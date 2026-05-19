from __future__ import annotations
import asyncio
from typing import List
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
import uvicorn
from fastapi import FastAPI, HTTPException, Request
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from contextlib import asynccontextmanager

import os
import logging
from logging import getLogger

from .colored_logging import setup_colored_logging
from .session.router import session_manager
from .config import settings
from .agent.agent import init_medical_agent

# Setup colored logging for both console and file
os.makedirs(settings.log_dir, exist_ok=True)
log_level = getattr(logging, settings.log_level, logging.DEBUG)

setup_colored_logging(
    log_level=log_level,
    log_file=f"{settings.log_dir}/{settings.app_name}.log",
    log_format="%(asctime)s - %(levelname)s - %(message)s",
)

# Suppress verbose debug logging from third-party libraries
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

logger = getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    periodic_tasks = None
    try:
        logger.info("=" * 80)
        logger.info("STARTING MEDICALLM BACKEND")
        logger.info("=" * 80)
        
        # Initialize PDF cache
        from .pubmed.pdf_downloader import initialize_cache
        initialize_cache()
        logger.info("PDF cache initialized")
        
        # Warm up the DB connection pool so the first user query doesn't
        # pay a 60s SSL/TCP handshake + auth on a managed Postgres (DO, RDS,
        # Neon, Supabase, etc.). We also implicitly verify the connection
        # string is good at startup instead of on the request path.
        try:
            from sqlalchemy import text
            from .db.sql_client import get_session
            def _ping():
                s = get_session()
                try:
                    s.execute(text("SELECT 1"))
                finally:
                    s.close()
            await asyncio.to_thread(_ping)
            logger.info("DB connection warmed up")
        except Exception as e:
            logger.error(f"DB warmup failed: {e}", exc_info=True)

        # Lightweight schema migration: add columns that may not exist yet
        try:
            def _migrate():
                s = get_session()
                try:
                    s.execute(text("""
                        ALTER TABLE conversations
                        ADD COLUMN IF NOT EXISTS patient_id VARCHAR(100)
                    """))
                    s.commit()
                finally:
                    s.close()
            await asyncio.to_thread(_migrate)
            logger.info("Schema migration check complete")
        except Exception as e:
            logger.warning(f"Schema migration skipped: {e}")

        await init_medical_agent(app)
        logger.info("Medical agent initialized")

        # Warm up the embedding model (optional - only if OPENAI_API_KEY is set)
        # Embeddings are only needed for semantic drug search.
        # Runs in a thread to avoid blocking the event loop during startup.
        if settings.openai_api_key and settings.openai_api_key.strip():
            try:
                from .drugs.embedding_service import get_embedding_service
                await asyncio.to_thread(get_embedding_service().warmup)
            except Exception as e:
                logger.warning(f"Embedding warmup skipped: {e}")
        else:
            logger.info("Embedding service disabled (OPENAI_API_KEY not set)")

        # Start periodic health-check / cleanup tasks
                
        async def periodic_tasks_func():
            while True:
                await asyncio.sleep(5 * 60) # 5 minutes
                await session_manager.cleanup()
                #todo: await health_check()
                
        periodic_tasks = asyncio.create_task(periodic_tasks_func())
        logger.info("Periodic tasks started")

        yield
        
        logger.info("Shutting down...")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}", exc_info=True)
        raise
    finally:
        if periodic_tasks is not None:
            periodic_tasks.cancel()
            try:
                await periodic_tasks
            except asyncio.CancelledError:
                pass

app = FastAPI(
    title="MedicaLLM Backend API",
    description="Backend API for MedicaLLM",
    version=settings.api_version,
    lifespan=lifespan
)

from .middleware.rate_limiter import limiter  # noqa: E402

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore


app.add_middleware(SlowAPIMiddleware)

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"[REQUEST] {request.method} {request.url.path}")
    try:
        response = await call_next(request)
        logger.info(f"[RESPONSE] {request.method} {request.url.path} - Status: {response.status_code}")
        return response
    except Exception as e:
        logger.error(f"[ERROR] {request.method} {request.url.path} - Error: {str(e)}", exc_info=True)
        raise

# CORS — allowed origins come from settings.cors_allowed_origins (CSV env var).
# Defaults are dev-only (localhost ports). Production deployments must set
# CORS_ALLOWED_ORIGINS to the real frontend URLs (audit I6).
_allowed_origins = [
    o.strip() for o in settings.cors_allowed_origins.split(",") if o.strip()
]
logger.info(f"[CORS] Allowed origins: {_allowed_origins}")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

#section: routers

from .auth.router import router as auth_router  # noqa: E402
from .conversations.router import router as conversations_router # noqa: E402
from .drugs.router import router as drug_search_router # noqa: E402
from .session.router import router as agent_router # noqa: E402
from .users.router import router as users_router # noqa: E402
from .admin.router import router as admin_router # noqa: E402
from .pubmed.router import router as pubmed_router # noqa: E402
from .pubmed.bookmarks_router import router as bookmarks_router # noqa: E402

# Register all routers
app.include_router(auth_router)
app.include_router(conversations_router)
app.include_router(drug_search_router)
app.include_router(agent_router)
app.include_router(users_router)
app.include_router(admin_router)
app.include_router(pubmed_router)
app.include_router(bookmarks_router)

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
    """
    Real health probe (audit I7).

    Returns 200 only when:
      - the medical agent finished startup, and
      - the database is reachable for a trivial `SELECT 1`.

    Anything else returns 503 with a structured `checks` payload so the
    Docker / load-balancer probes can distinguish "starting" from "broken".
    """
    checks: dict[str, str] = {}
    overall_ok = True

    # Agent
    medical_agent = getattr(app.state, "medical_agent", None)
    if medical_agent is None:
        checks["agent"] = "unavailable"
        overall_ok = False
    else:
        checks["agent"] = "ok"

    # DB
    try:
        from sqlalchemy import text
        from .db.sql_client import get_session
        def _ping():
            s = get_session()
            try:
                s.execute(text("SELECT 1"))
            finally:
                s.close()
        await asyncio.to_thread(_ping)
        checks["db"] = "ok"
    except Exception as exc:
        checks["db"] = f"error: {type(exc).__name__}"
        overall_ok = False

    if overall_ok:
        return {"status": "ok", "checks": checks}
    raise HTTPException(status_code=503, detail={"status": "degraded", "checks": checks})

# section: main

def main():
    try:
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except Exception as e:
        raise

if __name__ == "__main__":
    main()
