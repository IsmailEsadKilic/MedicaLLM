from __future__ import annotations
import asyncio
from typing import List
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
import uvicorn
from fastapi import FastAPI, HTTPException
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from contextlib import asynccontextmanager

from . import printmeup as pm
from .db.client import wait_for_dynamodb_ready
from .db.tables import init_tables
from .agent.agent import init_medical_agent

# SECTION - FASTAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    periodic_tasks = None
    try:
        
        #* init sequence: wait for DynamoDB, init tables, seed vector store, init agent
        await wait_for_dynamodb_ready()
        await init_tables()
        await init_medical_agent(app)

        #* Start periodic health-check / cleanup tasks
        from .agent.router import session_manager
                
        async def periodic_tasks_func():
            while True:
                await asyncio.sleep(300) #* 5-minute interval
                await session_manager.periodic_cleanup()
                
        periodic_tasks = asyncio.create_task(periodic_tasks_func())
        
        pm.inf("Cleanup task started")

        yield
    except Exception as e:
        pm.err(e)
        raise
    finally:
        if periodic_tasks is not None:
            periodic_tasks.cancel()
            try:
                await periodic_tasks
            except asyncio.CancelledError:
                pass
        pm.inf("Shutting down...")

app = FastAPI(
    title="MedicaLLM Backend API",
    description="Backend API for MedicaLLM application",
    version="1.0.0",
    lifespan=lifespan
)

from .middleware.rate_limiter import limiter  # noqa: E402

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore


app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      #* frontend (Docker / npm preview on port 3000)
        "http://127.0.0.1:3000",      #* same, but via loopback IP instead of hostname
        "http://localhost:4000",      #* alternative local port (e.g. second compose profile)
        "http://localhost:5173",      #* Vite dev server default port
    ],
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)  

# section - ROUTERS

from .auth.router import router as auth_router  # noqa: E402
from .conversations.router import router as conversations_router # noqa: E402
from .drugs.router import router as drug_search_router # noqa: E402
from .agent.router import router as agent_router # noqa: E402
from .patients.router import router as patients_router # noqa: E402
from .rag.router import router as rag_router # noqa: E402

app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(drug_search_router)
app.include_router(agent_router)
app.include_router(patients_router)
app.include_router(rag_router)

# section - HEALTH

@app.get("/")
async def endpoint_root():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>MedicaLLM backend</title>
        </head>
        <body>
            <h1>🏥 MedicaLLM backend is Running!</h1>
            <p>Try the <a href="/health">/health</a> endpoint for a JSON health check response.</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/health")
async def endpoint_health():
    if True:  #HACK Placeholder for real health checks (DB, agent, etc.)
        return {"status": "ok"}
    else:
        raise HTTPException(status_code=503, detail="")

# section - MAIN

def main():
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        pm.err(e)
        raise

if __name__ == "__main__":
    main()
