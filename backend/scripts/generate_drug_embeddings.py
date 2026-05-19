"""
Script to generate embeddings for all drugs in the database.
Run this after seeding the database with drug data.

Usage:
    python -m backend.scripts.generate_drug_embeddings
"""
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from backend.src.drugs.embedding_service import get_embedding_service
from backend.src.config import settings

from logging import getLogger, basicConfig, INFO

basicConfig(level=INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = getLogger(__name__)


def main():
    """Generate embeddings for all drugs."""
    logger.info("=" * 60)
    logger.info("Drug Embedding Generation Script")
    logger.info("=" * 60)
    logger.info(f"Database: {settings.postgres_url[:50]}...")
    logger.info(f"Embedding model: {settings.hgf_embedding_model_id}")
    logger.info("")
    
    try:
        # Get embedding service
        embedding_service = get_embedding_service()
        
        # Generate embeddings
        logger.info("Starting embedding generation...")
        logger.info("This may take several minutes depending on the number of drugs.")
        logger.info("")
        
        count = embedding_service.embed_all_drugs(batch_size=100)
        
        logger.info("")
        logger.info("=" * 60)
        logger.info(f"✓ Successfully generated embeddings for {count} drugs")
        logger.info("=" * 60)
        
        if count == 0:
            logger.info("All drugs already have embeddings. Nothing to do.")
        
        return 0
        
    except KeyboardInterrupt:
        logger.warning("\n\nInterrupted by user. Partial embeddings may have been saved.")
        return 1
    except Exception as e:
        logger.error(f"\n\n✗ Error generating embeddings: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
