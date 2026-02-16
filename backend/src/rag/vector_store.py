from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.vectorstores import VectorStoreRetriever
from typing import List
import os
from .. import printmeup as pm
from ..config import settings

VECTOR_STORE_PERSIST_DIR = "chromadb-data"

class VectorStoreManager:
    def __init__(
        self,
        persist_directory: str = VECTOR_STORE_PERSIST_DIR,
        embedding_model_id: str = settings.embedding_model_id
    ):
        """
        Args:
            persist_directory: Vector store directory
            embedding_model_id: Embedding model huggingface id
        """
        self.persist_directory = persist_directory
        self.embeddings = HuggingFaceEmbeddings(
            model_name=embedding_model_id, model_kwargs={"trust_remote_code": True}
        )
        self.vectorstore = None

    def load_vectorstore(self) -> Chroma | None:
        """Load existing vector store from persist directory."""
        try:
            if os.path.exists(self.persist_directory):
                pm.inf(
                    f"Loading existing Chroma database from {self.persist_directory}..."
                )
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings,
                )
                pm.suc("Existing vector store loaded")
                return self.vectorstore
            else:
                pm.war(f"No existing vector store found at {self.persist_directory}")
                return None
        except Exception as e:
            pm.err(e)
            return None

    def create_vectorstore(self, chunks: List[Document]) -> Chroma:
        """Create vector store from chunks."""

        if not chunks or len(chunks) == 0:
            raise pm.err(ValueError("Chunks list is empty, cannot create vector store"))

        pm.inf(f"Creating new vector store at {self.persist_directory}...")
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
        )
        pm.suc("New vector store created")
        return self.vectorstore

    def similarity_search(self, query: str, k: int = 4) -> List[Document] | None:
        """Perform a similarity search on the vector store.

        Args:
            query (str): The query string to search for.
            k (int, optional): The number of similar documents to return. Defaults to 4.
        Returns:
            List[Document] | None: List of similar documents or None if vector store is not loaded.
        """
        if not self.vectorstore:
            self.vectorstore = self.load_vectorstore()
        if not self.vectorstore:
            pm.err(m="Vector store could not be loaded for similarity search")
            return None

        return self.vectorstore.similarity_search(query, k=k)

    def get_retriever(self, k: int = 4) -> VectorStoreRetriever | None:
        if not self.vectorstore:
            return None

        return self.vectorstore.as_retriever(
            search_type="similarity", search_kwargs={"k": k}
            # * or search_type="mmr" for diverse results
        )