"""
MedicaLLM API Server
Combines RAG system with Drug Database via LangChain Agent
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

# Project modules
from vector_store import VectorStoreManager
from rag_chain import RAGChain
from medica_agent import MedicaLLMAgent, set_rag_chain

# ============================================================
# Configuration
# ============================================================

MODEL_NAME = "llama2"
OLLAMA_URL = "http://localhost:11434"
# Use absolute path for vector store
import os
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
VECTOR_STORE_DIR = os.path.join(SCRIPT_DIR, "..", "chroma_db")

# ============================================================
# FastAPI App
# ============================================================

app = FastAPI(
    title="MedicaLLM API",
    description="Medical information assistant with RAG and Drug Database",
    version="2.0.0"
)

# CORS middleware for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================
# Global State
# ============================================================

agent: Optional[MedicaLLMAgent] = None
vector_store_manager: Optional[VectorStoreManager] = None
rag_chain: Optional[RAGChain] = None

# ============================================================
# Request/Response Models
# ============================================================

class QueryRequest(BaseModel):
    query: str
    
class QueryResponse(BaseModel):
    answer: str
    success: bool
    error: Optional[str] = None

class HealthResponse(BaseModel):
    status: str
    agent_ready: bool
    rag_ready: bool
    model: str

# ============================================================
# Startup Event
# ============================================================

@app.on_event("startup")
async def startup_event():
    """Initialize agent and RAG on startup."""
    global agent, vector_store_manager, rag_chain
    
    print("🚀 Starting MedicaLLM API Server...")
    
    # Initialize Vector Store
    try:
        vector_store_manager = VectorStoreManager(
            ollama_model_name=MODEL_NAME,
            persist_directory=VECTOR_STORE_DIR
        )
        
        vectorstore = vector_store_manager.load_vectorstore()
        
        if vectorstore:
            retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
            rag_chain = RAGChain(
                retriever=retriever,
                ollama_model_name=MODEL_NAME,
                ollama_base_url=OLLAMA_URL
            )
            print("✅ RAG system initialized")
        else:
            print("⚠️ No vector store found - RAG will be unavailable")
            rag_chain = None
            
    except Exception as e:
        print(f"⚠️ RAG initialization failed: {e}")
        rag_chain = None
    
    # Initialize Agent
    try:
        agent = MedicaLLMAgent(
            ollama_model_name=MODEL_NAME,
            ollama_base_url=OLLAMA_URL,
            temperature=0.3,
            rag_chain=rag_chain
        )
        print("✅ Agent initialized")
    except Exception as e:
        print(f"❌ Agent initialization failed: {e}")
        agent = None
    
    print("🏥 MedicaLLM API Server ready!")

# ============================================================
# API Endpoints
# ============================================================

@app.get("/api/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        agent_ready=agent is not None,
        rag_ready=rag_chain is not None,
        model=MODEL_NAME
    )


@app.post("/api/drugs/query", response_model=QueryResponse)
async def query_agent(request: QueryRequest):
    """
    Main query endpoint - processes questions through LangChain Agent.
    Supports:
    - Drug information queries
    - Drug interaction checks
    - Medical document searches (RAG)
    """
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        result = agent.query(request.query)
        return QueryResponse(
            answer=result["answer"],
            success=result.get("success", True),
            error=result.get("error")
        )
    except Exception as e:
        return QueryResponse(
            answer=f"Error: {str(e)}",
            success=False,
            error=str(e)
        )


@app.post("/api/rag/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest):
    """Direct RAG query endpoint (bypasses agent)."""
    if rag_chain is None:
        raise HTTPException(status_code=503, detail="RAG system not available")
    
    try:
        result = rag_chain.query(request.query, chain_type="qa")
        return QueryResponse(
            answer=result.get("answer", "No answer found"),
            success=True
        )
    except Exception as e:
        return QueryResponse(
            answer=f"Error: {str(e)}",
            success=False,
            error=str(e)
        )


@app.post("/api/clear-history")
async def clear_history():
    """Clear agent chat history."""
    if agent:
        agent.clear_history()
    return {"status": "ok", "message": "History cleared"}


# ============================================================
# Auth endpoints (for compatibility with React frontend)
# ============================================================

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    email: str
    password: str
    name: str

class AuthResponse(BaseModel):
    token: str
    user: dict

# Simple in-memory user store (for demo purposes)
users_db = {
    "demo@example.com": {
        "id": "user_1",
        "email": "demo@example.com",
        "name": "Demo User",
        "password": "demo123"
    }
}

@app.post("/api/auth/login", response_model=AuthResponse)
async def login(request: LoginRequest):
    """Simple login endpoint."""
    user = users_db.get(request.email)
    if user and user["password"] == request.password:
        return AuthResponse(
            token="demo_token_" + user["id"],
            user={"id": user["id"], "email": user["email"], "name": user["name"]}
        )
    raise HTTPException(status_code=401, detail="Invalid credentials")


@app.post("/api/auth/register", response_model=AuthResponse)
async def register(request: RegisterRequest):
    """Simple register endpoint."""
    if request.email in users_db:
        raise HTTPException(status_code=400, detail="User already exists")
    
    user_id = f"user_{len(users_db) + 1}"
    users_db[request.email] = {
        "id": user_id,
        "email": request.email,
        "name": request.name,
        "password": request.password
    }
    
    return AuthResponse(
        token="demo_token_" + user_id,
        user={"id": user_id, "email": request.email, "name": request.name}
    )


# ============================================================
# Conversations endpoints (simplified)
# ============================================================

conversations_db = {}

class Message(BaseModel):
    role: str
    content: str

class CreateConversationRequest(BaseModel):
    title: str = "New Chat"

@app.get("/api/conversations")
async def get_conversations():
    """Get all conversations."""
    return list(conversations_db.values())

@app.post("/api/conversations")
async def create_conversation(request: CreateConversationRequest):
    """Create new conversation."""
    import uuid
    chat_id = str(uuid.uuid4())
    conversations_db[chat_id] = {
        "chat_id": chat_id,
        "title": request.title,
        "messages": []
    }
    return {"chat_id": chat_id}

@app.post("/api/conversations/{chat_id}/messages")
async def add_message(chat_id: str, message: dict):
    """Add message to conversation."""
    if chat_id in conversations_db:
        conversations_db[chat_id]["messages"].append(message.get("message", {}))
    return {"status": "ok"}

@app.patch("/api/conversations/{chat_id}/title")
async def update_title(chat_id: str, data: dict):
    """Update conversation title."""
    if chat_id in conversations_db:
        conversations_db[chat_id]["title"] = data.get("title", "Untitled")
    return {"status": "ok"}

@app.delete("/api/conversations/{chat_id}")
async def delete_conversation(chat_id: str):
    """Delete conversation."""
    if chat_id in conversations_db:
        del conversations_db[chat_id]
    return {"status": "ok"}


# ============================================================
# Title generation endpoint
# ============================================================

@app.post("/api/drugs/generate-title")
async def generate_title(data: dict):
    """Generate title for conversation based on first message."""
    message = data.get("message", "")
    # Simple title generation - take first few words
    words = message.split()[:5]
    title = " ".join(words)
    if len(title) > 30:
        title = title[:27] + "..."
    return {"title": title}


# ============================================================
# Run Server
# ============================================================

if __name__ == "__main__":
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=3001,  # Same port as Node.js backend
        reload=False
    )
