from __future__ import annotations
from typing import List
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
import uvicorn
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import os
from pydantic import BaseModel
from contextlib import asynccontextmanager

# * PROJECT MODULES
import printmeup as pm
from vector_store import VectorStoreManager
from pdf_processor import PDFProcessor
from medical_agent import create_medical_agent
from dynamodb_manager import DynamoDBManager
from session import Session

# section - CONSTANTS

load_dotenv(dotenv_path="../.env")

# * huggingface model IDs
# MODEL_ID = "google/gemma-3-4b-it" # * >8gb
# MODEL_ID = "google/gemma-3-1b-it" # * ~4gb
# MODEL_ID = "google/medgemma-4b-pt" # * >8gb

# * AWS Bedrock model
MODEL_NAME = os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")

# section - PUBLIC VARIABLES

vectorstore = None
medical_agent = None
dynamodb_manager = DynamoDBManager()
active_sessions = {}  # Store active sessions by conversation_id

# section - HELPERS

# section - CONVERSATION

# section - API MODELS

class CreateConversationRequest(BaseModel):
    user_id: str
    title: str = "Untitled"
    
class QueryRequest(BaseModel):
    conversation_id: str
    query: str

from models import Message

class AddMessageRequest(BaseModel):
    conversation_id: str
    message: dict # We will convert to Message model manually or let Pydantic handle it if we type it as Message, but keep it simple as dict first to debug

class UpdateTitleRequest(BaseModel):
    conversation_id: str
    title: str
    
class AnalyzePatientRequest(BaseModel):
    chronic_conditions: List[str]
    allergies: List[str]
    current_medications: List[str]

# section - APP

@asynccontextmanager
async def lifespan(app: FastAPI):
    # * Startup: Load VectorStore and Initialize Agent
    global vectorstore, medical_agent
    pm.inf("Loading Vector Store...")
    retriever = None
    try:
        vsm = VectorStoreManager()
        vectorstore = vsm.load_vectorstore()
        if not vectorstore:
            pm.inf("Vector store not found, processing PDFs...")
            pdf_processor = PDFProcessor()
            chunks = pdf_processor.process_pdfs()
            vectorstore = vsm.create_vectorstore(chunks)
        if vectorstore:
            retriever = vectorstore.as_retriever(search_kwargs={"k": 3})
        pm.suc("Vector store loaded successfully")
    except Exception as e:
        pm.err(e=e, m="Failed to load vector store")
    
    # Initialize Medical Agent using create_medical_agent
    try:
        pm.inf("Initializing Medical Agent...")
        
        medical_agent = create_medical_agent(
            bedrock_model_id=MODEL_NAME,
            temperature=0.3,
            retriever=retriever
        )
        pm.suc("Medical Agent initialized successfully")
    except Exception as e:
        pm.err(e=e, m="Failed to initialize Medical Agent")
        
    yield
    # * Shutdown
    pm.inf("Shutting down...")

app = FastAPI(title="MedicaLLM Agents API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    # * Production
    "https://yourdomain.com",
    # * EC2 IP
    "http://98.80.152.122",
    "http://98.80.152.122:3000",
    "http://98.80.152.122:3001",
    # * Frontend
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # * Backend
    "http://localhost:3001",
    "http://localhost:4000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/create-conversation")
async def endpoint_create_conversation(request: CreateConversationRequest):
    """
    Create a new conversation for a user.
    """
    try:
        conversation = dynamodb_manager.create_conversation(
            user_id=request.user_id,
            title=request.title
        )
        return {
            "success": True,
            "conversation_id": conversation.id,
            "conversation": conversation.model_dump()
        }
    except Exception as e:
        pm.err(e=e, m="Failed to create conversation")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversations")
async def endpoint_get_conversations(user_id: str):
    """
    Get all conversations for a user.
    """
    try:
        conversations = dynamodb_manager.get_conversations(user_id=user_id)
        if conversations is None:
            raise HTTPException(status_code=500, detail="Failed to fetch conversations")
        
        return {
            "success": True,
            "count": len(conversations),
            "conversations": [conv.model_dump() for conv in conversations]
        }
    except HTTPException:
        raise
    except Exception as e:
        pm.err(e=e, m=f"Failed to get conversations for user {user_id}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/conversation/{conversation_id}")
async def endpoint_get_conversation(conversation_id: str):
    """
    Get a conversation by ID
    """
    try:
        conversation = dynamodb_manager.get_conversation(conversation_id=conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {
            "success": True,
            "conversation": conversation.model_dump()
        }
    except HTTPException:
        raise
    except Exception as e:
        pm.err(e=e, m=f"Failed to get conversation {conversation_id}")
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/conversation/title")
async def endpoint_update_title(request: UpdateTitleRequest):
    """Update conversation title"""
    try:
        success = dynamodb_manager.update_conversation_title(
            conversation_id=request.conversation_id,
            title=request.title
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update title")
        
        return {"success": True, "message": "Title updated"}
    except HTTPException:
        raise
    except Exception as e:
        pm.err(e=e, m="Failed to update title")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/conversation/{conversation_id}")
async def endpoint_delete_conversation(conversation_id: str):
    """Delete a conversation"""
    try:
        success = dynamodb_manager.delete_conversation(conversation_id=conversation_id)
        
        if not success:
            raise HTTPException(status_code=404, detail="Conversation not found")
        
        return {"success": True, "message": "Conversation deleted"}
    except HTTPException as e:
        pm.err(e=e, m=f"Failed to delete conversation {conversation_id}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/conversation/add-message")
async def endpoint_add_message(request: AddMessageRequest):
    """Add a message to a conversation"""
    try:
        # validate message
        msg = Message(**request.message)
        
        success = dynamodb_manager.add_message(
            conversation_id=request.conversation_id,
            message=msg
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to add message")
        
        return {"success": True, "message": "Message added"}
    except HTTPException:
        raise
    except Exception as e:
        pm.err(e=e, m="Failed to add message")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/query")
async def endpoint_query(request: QueryRequest):
    """
    Process a user query with the medical agent.
    Returns full response.
    """
    try:
        # Get or create session for this conversation
        if request.conversation_id not in active_sessions:
            conversation = dynamodb_manager.get_conversation(request.conversation_id)
            if not conversation:
                raise HTTPException(status_code=404, detail="Conversation not found")
            
            active_sessions[request.conversation_id] = Session(
                conversation_id=request.conversation_id,
                user_id=conversation.user_id,
                agent=medical_agent,
                dynamodb_manager=dynamodb_manager
            )
        
        session = active_sessions[request.conversation_id]
        result = await session.handle_user_query(request.query)
        
        if not result.get("success"):
            raise HTTPException(status_code=500, detail=result.get("error", "Unknown error"))
        
        return {
            "success": True,
            "answer": result["answer"],
            "conversation_id": request.conversation_id,
            "sources": result.get("sources", []),
            "tool_used": result.get("tool_used"),
            "tool_result": result.get("tool_result")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        pm.err(e=e, m="Failed to process query")
        raise HTTPException(status_code=500, detail=str(e))

        
@app.post("/api/query-stream")
async def endpoint_query_stream(request: QueryRequest):
    """Stream agent response for a user query."""
    async def generate_stream():
        try:
            # Get or create session
            if request.conversation_id not in active_sessions:
                conversation = dynamodb_manager.get_conversation(request.conversation_id)
                if not conversation:
                    yield "data: {'error': 'Conversation not found'}\n\n"
                    return
                
                active_sessions[request.conversation_id] = Session(
                    conversation_id=request.conversation_id,
                    user_id=conversation.user_id,
                    agent=medical_agent,
                    dynamodb_manager=dynamodb_manager
                )
            
            session = active_sessions[request.conversation_id]
            
            async for chunk in session.stream_query(request.query):
                import json
                yield f"data: {json.dumps(chunk)}\n\n"
                
        except Exception as e:
            pm.err(e=e, m="Stream error")
            import json
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream"
    )
    
@app.post("/api/analyze-patient")
async def endpoint_analyze_patient(request: AnalyzePatientRequest):
    """Analyze patient medical profile using agent with database tools."""
    try:
        if not medical_agent:
            raise HTTPException(status_code=503, detail="Medical agent not initialized")
        
        prompt = f"""Create a medical analysis report for this patient. Use your database tools to gather information, then provide ONLY the final report without showing tool calls or intermediate steps.

Patient Profile:
- Chronic Conditions: {', '.join(request.chronic_conditions) if request.chronic_conditions else 'None'}
- Allergies: {', '.join(request.allergies) if request.allergies else 'None'}
- Current Medications: {', '.join(request.current_medications) if request.current_medications else 'None'}

Use your tools to check:
1. Drug information for each medication
2. Drug-drug interactions between medications
3. Drug-food interactions
4. Alternative medications for their conditions

Provide a professional medical report with sections:
## Medication Analysis
## Drug Interactions
## Food Interactions  
## Recommendations

Do NOT show tool calls or explain your process. Only provide the final formatted report."""

        result = medical_agent.invoke({"messages": [{"role": "user", "content": prompt}]})
        
        # Extract the final response
        messages = result.get("messages", [])
        analysis = messages[-1].content if messages else "No analysis generated"
        
        return {
            "success": True,
            "analysis": analysis,
            "patient_data": {
                "chronic_conditions": request.chronic_conditions,
                "allergies": request.allergies,
                "current_medications": request.current_medications
            }
        }
        
    except Exception as e:
        pm.err(e=e, m="Failed to analyze patient profile")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")

@app.get("/")
async def endpoint_root():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>MedicaLLM Agents API Health Check</title>
            <link rel="icon" type="image/x-icon" href="/favicon.ico">
        </head>
        <body>
            <h1>🏥 MedicaLLM Agents API is Running!</h1>
            <button onclick="location.href='/health'">Health Check</button>
            <script>
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/health")
async def endpoint_health():
    return {"status": "ok"}

# section - MAIN

def main():
    uvicorn.run(app, host="0.0.0.0", port=2580)


if __name__ == "__main__":
    main()
