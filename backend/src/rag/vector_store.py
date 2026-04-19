import asyncio

from langchain_core.documents import Document
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
from langchain_core.vectorstores import VectorStoreRetriever
from typing import List
import os

from ..rag.pdf_processor import PDFProcessor
from .. import printmeup as pm
from ..config import settings

class VectorStoreManager:
    def __init__(
        self,
        persist_directory: str = settings.vector_store_persist_dir,
        hgf_embedding_model_id: str = settings.hgf_embedding_model_id
    ):
        self.persist_directory = persist_directory
        
        # Configure HuggingFace embeddings with optional token
        model_kwargs = {"trust_remote_code": True}
        encode_kwargs = {}
        
        # If HF_TOKEN is set, pass it to the embeddings
        if settings.hf_token:
            model_kwargs["token"] = settings.hf_token
            pm.deb("Using HuggingFace token for embeddings")
        
        self.embeddings = HuggingFaceEmbeddings(
            model_name=hgf_embedding_model_id,
            model_kwargs=model_kwargs,
            encode_kwargs=encode_kwargs,
        )
        self.pdf_processor = PDFProcessor()
        
        self.vectorstore = self.get_vector_store()
        
    def load_vectorstore(self) -> Chroma | None:
        """Load existing vector store from persist directory."""
        try:
            if os.path.exists(self.persist_directory):
                pm.deb(
                    f"Loading existing Chroma database from {self.persist_directory}..."
                )
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings,
                )
                pm.inf("Existing vector store loaded")
                return self.vectorstore
            else:
                pm.deb(f"No existing vector store found at {self.persist_directory}")
                return None
        except Exception as e:
            pm.err(e)
            return None
        
    def create_vectorstore(self, chunks: List[Document] | None = None) -> Chroma:
        """Create vector store from chunks."""
        doc_count = None
        if not chunks or len(chunks) == 0:
            chunks, doc_count = self.pdf_processor.process_pdfs()

        if not chunks or len(chunks) == 0:
            pm.inf(f"No documents to index — creating empty vector store at {self.persist_directory}")
            self.vectorstore = Chroma(
                persist_directory=self.persist_directory,
                embedding_function=self.embeddings,
            )
            pm.suc("Empty vector store created (will be populated as documents are added)")
            return self.vectorstore

        pm.inf(f"Creating new vector store at {self.persist_directory}, with {len(chunks)} chunks"
            + (f" from {doc_count} documents." if doc_count else ""))
        self.vectorstore = Chroma.from_documents(
            documents=chunks,
            embedding=self.embeddings,
            persist_directory=self.persist_directory,
        )
        pm.suc("New vector store created")
        return self.vectorstore    
    
    def get_vector_store(self) -> Chroma:
        """Get vector store, loading existing or creating new if needed."""
        vectorstore = self.load_vectorstore()
        if vectorstore:
            return vectorstore
        else:
            return self.create_vectorstore()
        
    def add_chunks(self, chunks: List[Document]) -> bool:
        """Add new chunks to the existing vector store (incremental).
        
        Args:
            chunks: List of chunk objects to add.
        Returns:
            True if successful, False otherwise.
        """
        if not chunks:
            pm.war("No chunks to add to vector store")
            return False

        try:
            pm.deb(f"Adding {len(chunks)} new chunks to existing vector store...")
            self.vectorstore.add_documents(chunks)
            pm.deb(f"{len(chunks)} chunks added to vector store")
            return True
        except Exception as e:
            pm.err(e=e, m="Failed to add documents to vector store")
            return False
        
    def add_documents(self, documents: List[Document]) -> bool:
        pm.deb(f"Adding {len(documents)} new documents to vector store...")
        return self.add_chunks(self.pdf_processor.split_documents(documents))
    
    def similarity_search(self, query: str, k: int = 4) -> List[Document] | None:
        """Perform a similarity search on the vector store.

        Args:
            query (str): The query string to search for.
            k (int, optional): The number of similar documents to return. Defaults to 4.
        Returns:
            List[Document] | None: List of similar documents or None if vector store is not loaded.
        """

        return self.vectorstore.similarity_search(query, k=k)
        
    def get_retriever(self, k: int = 4) -> VectorStoreRetriever:
        return self.vectorstore.as_retriever(
            search_type="similarity", search_kwargs={"k": k}
        )

async def init_vector_store_manager(app):
    loop = asyncio.get_event_loop()
    vsm = await loop.run_in_executor(None, VectorStoreManager, settings.vector_store_persist_dir, settings.hgf_embedding_model_id)
    app.state.vsm = vsm
    app.state.retriever = vsm.get_retriever(k=3)
    pm.suc("Vector store initialized")