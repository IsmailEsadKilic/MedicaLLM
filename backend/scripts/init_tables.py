import sys
from pathlib import Path
import logging
from sqlalchemy import text
from sqlalchemy import inspect

# Add project root to path so we can import from src
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from backend.src.db.sql_models import Base
from src.db.sql_client import get_engine
from src.db.sql_client import get_session

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

logger = logging.getLogger(__name__)



def init_database(drop_existing: bool = False):
    engine = get_engine()
    session = get_session()
    
    try:
        # Enable required PostgreSQL extensions
        logger.info("Enabling PostgreSQL extensions...")
        session.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
        session.commit()
        logger.info("✓ pg_trgm extension enabled")
        
        if drop_existing:
            logger.warning("⚠️  Dropping all existing tables and data...")
            Base.metadata.drop_all(engine)
            logger.info("✓ All tables dropped")
            logger.info("Creating all tables...")
            Base.metadata.create_all(engine)
            logger.info("✓ All tables created successfully")
        else:
            # Only create missing tables, preserve existing data
            logger.info("Checking existing tables...")
            inspector = inspect(engine)
            existing_tables = set(inspector.get_table_names())
            
            # Get tables defined in models
            model_tables = set(Base.metadata.tables.keys())
            
            missing_tables = model_tables - existing_tables
            
            if missing_tables:
                logger.info(f"Creating {len(missing_tables)} missing tables: {', '.join(missing_tables)}")
                Base.metadata.create_all(engine, checkfirst=True)
                logger.info("✓ Missing tables created")
            else:
                logger.info("✓ All tables already exist, no changes needed")
        
        # Log final table list
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"Database has {len(tables)} tables:")
        for table in sorted(tables):
            logger.info(f"  - {table}")
            
    except Exception as e:
        session.rollback()
        logger.error(f"Failed to initialize database: {e}", exc_info=True)
        raise
    finally:
        session.close()


def main():
    """Main entry point for table initialization."""
    import sys
    
    drop_existing = "--drop" in sys.argv or "-d" in sys.argv
    
    if drop_existing:
        logger.warning("⚠️  WARNING: This will DROP ALL EXISTING TABLES and data!")
        response = input("Are you sure you want to continue? (yes/no): ")
        if response.lower() != "yes":
            logger.info("Operation cancelled.")
            sys.exit(0)
    
    init_database(drop_existing=drop_existing)
    logger.info("✨ Database initialization complete!")


if __name__ == "__main__":
    main()