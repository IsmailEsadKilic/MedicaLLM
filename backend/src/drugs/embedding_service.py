"""
Service for generating and managing drug embeddings for semantic search.
"""
from __future__ import annotations
import threading
import numpy as np
from typing import List, Optional
from sentence_transformers import SentenceTransformer

from ..config import settings
from ..db.sql_client import get_session
from ..db.sql_models import Drug as DrugORM, DrugEmbedding as DrugEmbeddingORM

from logging import getLogger

logger = getLogger(__name__)


class DrugEmbeddingService:
    """
    Manages drug embeddings for semantic search.
    Uses a local embedding model to generate vector representations of drugs.

    Thread safety:
        SentenceTransformer / PyTorch inference is CPU-bound and not safe to
        invoke concurrently from multiple threads on the same model instance
        (shared forward-pass state, memory allocator races on some backends).
        We serialize all ``encode()`` calls with ``_encode_lock``. This also
        protects the lazy-load path from a double-init race on startup.

        Query-embedding results are cached in an LRU so repeated lookups for
        the same drug name / indication / category skip the transformer call
        entirely (drug names repeat heavily across an agent's tool chain).
    """
    
    def __init__(self, model_name: Optional[str] = None):
        """
        Initialize the embedding service.
        
        Args:
            model_name: HuggingFace model name. Defaults to config setting.
        """
        self.model_name = model_name or settings.hgf_embedding_model_id
        self._model: Optional[SentenceTransformer] = None
        self._model_lock = threading.Lock()
        self._encode_lock = threading.Lock()
        logger.info(f"DrugEmbeddingService initialized with model: {self.model_name}")
    
    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load the embedding model with double-checked locking."""
        if self._model is None:
            with self._model_lock:
                if self._model is None:
                    logger.info(f"Loading embedding model: {self.model_name}")
                    self._model = SentenceTransformer(self.model_name, trust_remote_code=True)
                    logger.info("Embedding model loaded successfully")
        return self._model

    def warmup(self) -> None:
        """Force model load + a single dummy forward-pass.

        Run this at application startup so the first user query does not eat
        the 3-5 second one-off cost of loading weights and JIT-compiling the
        forward graph.
        """
        try:
            logger.info("[EMBEDDING] Warming up embedding model...")
            _ = self.model  # triggers lazy-load
            with self._encode_lock:
                self.model.encode("warmup", convert_to_numpy=True, normalize_embeddings=True)
            logger.info("[EMBEDDING] Warmup complete")
        except Exception as e:
            logger.error(f"[EMBEDDING] Warmup failed: {e}", exc_info=True)
    
    def create_embedding_text(self, drug_orm: DrugORM) -> str:
        """
        Create a text representation of a drug for embedding.
        Combines the most semantically relevant fields.
        
        Args:
            drug_orm: Drug ORM object
            
        Returns:
            str: Combined text for embedding
        """
        parts = []
        
        # Drug name (most important)
        if drug_orm.name:
            parts.append(f"Drug: {drug_orm.name}")
        
        # Indication (what it treats - very important for semantic search)
        if drug_orm.indication:
            parts.append(f"Indication: {drug_orm.indication}")
        
        # Categories (therapeutic class)
        if drug_orm.categories:
            categories = [c.category for c in drug_orm.categories[:5]]  # Top 5 categories
            if categories:
                parts.append(f"Categories: {', '.join(categories)}")
        
        # Mechanism of action
        if drug_orm.mechanism_of_action:
            parts.append(f"Mechanism: {drug_orm.mechanism_of_action}")
        
        # Description (truncated to avoid too much noise)
        if drug_orm.description:
            desc = drug_orm.description[:500]  # First 500 chars
            parts.append(f"Description: {desc}")
        
        # Pharmacodynamics
        if drug_orm.pharmacodynamics:
            pharma = drug_orm.pharmacodynamics[:300]  # First 300 chars
            parts.append(f"Pharmacodynamics: {pharma}")
        
        return " | ".join(parts)
    
    def generate_embedding(self, text: str) -> np.ndarray:
        """
        Generate an embedding vector for the given text.

        Serialized behind ``_encode_lock`` so concurrent tool calls don't race
        on the shared model. Short queries (drug names, indications) are
        cached so repeated lookups skip the transformer entirely.

        Args:
            text: Text to embed
            
        Returns:
            np.ndarray: Embedding vector
        """
        # Query cache — only for short strings (drug names, indications,
        # categories). We don't cache long document texts used in batch
        # embedding, which are one-shot and would bloat memory.
        if len(text) <= 256:
            cached = self._query_cache_get(text)
            if cached is not None:
                return cached

        with self._encode_lock:
            embedding = self.model.encode(
                text,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )

        if len(text) <= 256:
            self._query_cache_put(text, embedding)
        return embedding

    # --- query embedding cache --------------------------------------------
    # Small bounded cache for recent short-text embeddings (drug names,
    # indications, categories). Bounded to avoid unbounded memory growth.
    _QUERY_CACHE_MAX = 1024

    @property
    def _query_cache(self) -> dict[str, np.ndarray]:
        if not hasattr(self, "_query_cache_store"):
            self._query_cache_store: dict[str, np.ndarray] = {}
            self._query_cache_lock = threading.Lock()
        return self._query_cache_store

    def _query_cache_get(self, key: str) -> Optional[np.ndarray]:
        cache = self._query_cache  # ensures init
        with self._query_cache_lock:
            return cache.get(key)

    def _query_cache_put(self, key: str, value: np.ndarray) -> None:
        cache = self._query_cache
        with self._query_cache_lock:
            if len(cache) >= self._QUERY_CACHE_MAX:
                # Drop oldest (dict preserves insertion order)
                oldest = next(iter(cache))
                cache.pop(oldest, None)
            cache[key] = value
    
    def embed_drug(self, drug_orm: DrugORM) -> Optional[DrugEmbeddingORM]:
        """
        Generate and store embedding for a single drug.
        
        Args:
            drug_orm: Drug ORM object
            
        Returns:
            DrugEmbeddingORM: Created embedding record, or None if failed
        """
        try:
            # Create embedding text
            embedding_text = self.create_embedding_text(drug_orm)
            
            if not embedding_text.strip():
                logger.warning(f"No text to embed for drug {drug_orm.drug_id}")
                return None
            
            # Generate embedding — long document text, bypass query cache via
            # length check in generate_embedding; lock is still held.
            embedding_vector = self.generate_embedding(embedding_text)
            
            # Create embedding record
            from datetime import datetime
            embedding_record = DrugEmbeddingORM(
                drug_pk=drug_orm.id,
                embedding=embedding_vector.tolist(),
                embedding_text=embedding_text,
                created_at=datetime.utcnow().isoformat(),
            )
            
            logger.debug(f"Generated embedding for drug {drug_orm.drug_id} ({drug_orm.name})")
            return embedding_record
            
        except Exception as e:
            logger.error(f"Error embedding drug {drug_orm.drug_id}: {e}", exc_info=True)
            return None
    
    def embed_all_drugs(self, batch_size: int = 100) -> int:
        """
        Generate embeddings for all drugs that don't have them yet.
        
        Args:
            batch_size: Number of drugs to process in each batch
            
        Returns:
            int: Number of drugs embedded
        """
        session = get_session()
        try:
            # Get all drugs without embeddings
            drugs_without_embeddings = (
                session.query(DrugORM)
                .outerjoin(DrugEmbeddingORM, DrugORM.id == DrugEmbeddingORM.drug_pk)
                .filter(DrugEmbeddingORM.id == None)
                .all()
            )
            
            total_drugs = len(drugs_without_embeddings)
            if total_drugs == 0:
                logger.info("All drugs already have embeddings")
                return 0
            
            logger.info(f"Embedding {total_drugs} drugs in batches of {batch_size}")
            
            embedded_count = 0
            for i in range(0, total_drugs, batch_size):
                batch = drugs_without_embeddings[i:i + batch_size]
                
                for drug_orm in batch:
                    embedding_record = self.embed_drug(drug_orm)
                    if embedding_record:
                        session.add(embedding_record)
                        embedded_count += 1
                
                # Commit batch
                session.commit()
                logger.info(f"Embedded {min(i + batch_size, total_drugs)}/{total_drugs} drugs")
            
            logger.info(f"Successfully embedded {embedded_count} drugs")
            return embedded_count
            
        except Exception as e:
            logger.error(f"Error in embed_all_drugs: {e}", exc_info=True)
            session.rollback()
            return 0
        finally:
            session.close()
    
    def search_similar_drugs(
        self, 
        query: str, 
        limit: int = 10,
        min_similarity: float = 0.0
    ) -> List[tuple[str, str, str, float]]:
        """
        Search for drugs semantically similar to the query.
        
        Args:
            query: Search query text
            limit: Maximum number of results
            min_similarity: Minimum cosine similarity (0.0 to 1.0)
            
        Returns:
            List of tuples: (drug_id, name, description, similarity_score)
        """
        session = get_session()
        try:
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            
            # Search using cosine similarity
            # pgvector uses <=> operator for cosine distance (1 - cosine_similarity)
            from sqlalchemy import func, text
            
            results = (
                session.query(
                    DrugORM.drug_id,
                    DrugORM.name,
                    DrugORM.description,
                    # Convert cosine distance to similarity: similarity = 1 - distance
                    (1 - DrugEmbeddingORM.embedding.cosine_distance(query_embedding.tolist())).label("similarity")
                )
                .join(DrugEmbeddingORM, DrugORM.id == DrugEmbeddingORM.drug_pk)
                .filter((1 - DrugEmbeddingORM.embedding.cosine_distance(query_embedding.tolist())) >= min_similarity)
                .order_by(DrugEmbeddingORM.embedding.cosine_distance(query_embedding.tolist()))
                .limit(limit)
                .all()
            )
            
            logger.info(f"Semantic search for '{query}' found {len(results)} results")
            return results
            
        except Exception as e:
            logger.error(f"Error in semantic search: {e}", exc_info=True)
            return []
        finally:
            session.close()


# Global instance (lazy loaded)
_embedding_service: Optional[DrugEmbeddingService] = None

def get_embedding_service() -> DrugEmbeddingService:
    """Get or create the global embedding service instance."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = DrugEmbeddingService()
    return _embedding_service
