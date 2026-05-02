"""Initialize all PostgreSQL tables."""
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import logging
from sqlalchemy import text, inspect

from backend.src.db.sql_client import get_engine, get_session
from backend.src.db.sql_models import Base

from logging import getLogger, basicConfig, INFO

basicConfig(level=INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = getLogger(__name__)

def init_extensions():
    """Initialize required PostgreSQL extensions."""
    logger.info("Initializing PostgreSQL extensions...")
    engine = get_engine()
    with engine.connect() as conn:
        # Enable pg_trgm for fuzzy text search (already in use)
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        logger.info("✓ pg_trgm extension enabled")
        
        # Enable pgvector for semantic search
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
        logger.info("✓ pgvector extension enabled")
        
        conn.commit()

def init_tables():
    """Create all tables defined in sql_models.py"""
    logger.info("=" * 60)
    logger.info("Database Initialization")
    logger.info("=" * 60)
    
    engine = get_engine()
    
    # First, ensure extensions are installed
    try:
        init_extensions()
    except Exception as e:
        logger.error(f"✗ Failed to initialize extensions: {e}")
        logger.error("Make sure pgvector is installed in PostgreSQL")
        return False
    
    # Create all tables
    try:
        logger.info("Creating tables...")
        Base.metadata.create_all(engine)
        logger.info("✓ All tables created successfully")
    except Exception as e:
        logger.error(f"✗ Failed to create tables: {e}")
        return False
    
    # Verify tables were created
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"✓ Verified {len(tables)} tables exist")
        logger.info("=" * 60)
        logger.info("Database initialization complete!")
        logger.info("=" * 60)
        return True
    except Exception as e:
        logger.error(f"✗ Failed to verify tables: {e}")
        return False

if __name__ == "__main__":
    success = init_tables()
    sys.exit(0 if success else 1)
