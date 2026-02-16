from __future__ import annotations
import asyncio
from typing import List
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
import uvicorn
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import os
from pydantic import BaseModel
from contextlib import asynccontextmanager

from .config import settings
from . import printmeup as pm


# section - PUBLIC VARIABLES

medical_agent = None


# SECTION - FASTAPI

async def wait_for_dynamodb_ready(max_retries: int = 5, delay: float = 2.0):
    """Wait for DynamoDB to be ready with retry logic."""
    from .db.client import dynamodb_client
    
    pm.inf(f"Waiting for DynamoDB at {settings.dynamodb_endpoint}...")
    
    for attempt in range(max_retries):
        try:
            dynamodb_client.meta.client.list_tables()  # type: ignore
            pm.suc("DynamoDB connection successful")
            return
        except Exception as e:
            if attempt < max_retries - 1:
                pm.inf(f"Waiting for DynamoDB... ({attempt + 1}/{max_retries})")
                await asyncio.sleep(delay)
            else:
                pm.err(e=e, m=f"Failed to connect to DynamoDB after {max_retries} attempts")
                raise
            
async def init_tables():
    """Initialize all DynamoDB tables (idempotent - creates only if not exist)."""
    from .db.tables import (
        create_conversations_table,
        create_drugs_table,
        create_drug_interactions_table,
        create_drug_food_interactions_table,
        create_users_table,
        create_patients_table,
    )
    
    pm.inf("Initializing DynamoDB tables...")
    
    try:
        create_users_table()
        create_conversations_table()
        create_drugs_table()
        create_drug_interactions_table()
        create_drug_food_interactions_table()
        create_patients_table()
        
        pm.suc("All tables initialized")
    except Exception as e:
        pm.err(e=e, m="Failed to initialize tables")
        raise

async def seed_chromadb():
    """Load PDF documents into ChromaDB for RAG (if not already loaded)."""
    from .rag.vector_store import VectorStoreManager
    from .rag.pdf_processor import PDFProcessor
    
    pm.inf("Checking ChromaDB vector store...")
    
    try:
        vsm = VectorStoreManager()
        vectorstore = vsm.load_vectorstore()
        
        if vectorstore:
            pm.suc("Vector store already exists, skipping PDF processing")
            return vsm
        
        pm.inf("Vector store not found, processing PDFs...")
        pdf_processor = PDFProcessor()
        chunks = pdf_processor.process_pdfs()
        
        if not chunks:
            pm.war("No PDF chunks found, skipping vector store creation")
            return vsm
        
        vectorstore = vsm.create_vectorstore(chunks)
        pm.suc(f"Vector store created with {len(chunks)} chunks")
        return vsm
        
    except Exception as e:
        pm.err(e=e, m="Failed to initialize vector store")
        pm.war("App will start without RAG functionality")
        return None

async def init_medical_agent():
    """Initialize the medical agent with vector store retriever."""
    global medical_agent
    from .agent.agent import create_medical_agent
    
    try:
        pm.inf("Initializing Medical Agent...")
        
        # Try to get retriever from vector store
        retriever = None
        vsm = await seed_chromadb()
        if vsm:
            retriever = vsm.get_retriever(k=3)
        
        medical_agent = create_medical_agent(
            bedrock_model_id=settings.bedrock_llm_id,
            temperature=0.3,
            retriever=retriever,
        )
        pm.suc("Medical Agent initialized successfully")
    except Exception as e:
        pm.err(e=e, m="Failed to initialize Medical Agent")
        pm.war("App will start without agent functionality")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await wait_for_dynamodb_ready()
        await init_tables()
        await init_medical_agent()
        yield
    except Exception as e:
        pm.err(e)
        raise
    finally:
        pm.inf("Shutting down...")

app = FastAPI(
    title="MedicaLLM Agents API",
    description="API for MedicaLLM Agents",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:4000",
        "http://localhost:5173",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)  

# section - ROUTERS

from .auth.router import router as auth_router
from .conversations.router import router as conversations_router
from .drugs.router import router as drug_search_router
from .agent.router import router as agent_router
from .patients.router import router as patients_router

app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(drug_search_router)
app.include_router(agent_router)
app.include_router(patients_router)

# section - HEALTH

@app.get("/")
async def endpoint_root():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>MedicaLLM Agents API Health Check</title>
        </head>
        <body>
            <h1>🏥 MedicaLLM Agents API is Running!</h1>
            <button onclick="location.href='/health'">Health Check</button>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/health")
async def endpoint_health():
    return {"status": "ok"}

# section - MAIN

def main():
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        pm.err(e)
        raise

if __name__ == "__main__":
    main()
