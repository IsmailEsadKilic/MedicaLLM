from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader

from typing import List
from .. import printmeup as pm

PDF_DATA_DIR = "data/pdf"

class PDFProcessor:
    """Loads and processes PDF documents into text chunks: List[Document]"""
    # * This module is responsible for loading all medical PDFs into chunks.
    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 100):
        """
        Args:
            chunk_size: Size of each text chunk
            chunk_overlap: Amount of overlap between chunks
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

    def split_documents(self, documents: List[Document]) -> List[Document]:
        pm.inf("Splitting documents into chunks...")
        chunks = self.text_splitter.split_documents(documents)
        pm.suc(f"{len(chunks)} chunks created")
        return chunks

    def load_single_pdf(self, pdf_path: str) -> List[Document]:
        pm.inf(f"Loading PDF: {pdf_path}")
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        pm.suc(f"{len(documents)} pages loaded")
        return documents

    def load_all_pdfs(self, directory_path: str = PDF_DATA_DIR) -> List[Document]:
        """Load all PDFs from a directory."""
        pm.inf(f"Loading all PDFs in directory: {directory_path}")
        loader = DirectoryLoader(
            directory_path,
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,  # type: ignore
            show_progress=True,
        )
        documents = loader.load()
        pm.suc(f"{len(documents)} pages loaded")
        return documents

    def process_pdfs(self, directory_path: str = PDF_DATA_DIR) -> List[Document]:
        """Load and process all PDFs from a directory into text chunks."""
        documents = self.load_all_pdfs(directory_path)
        chunks = self.split_documents(documents)
        return chunks
    
if __name__ == "__main__":
    pm.inf("Starting PDF processing test...")
    processor = PDFProcessor()
    chunks = processor.process_pdfs()
    pm.suc("PDF processing complete.")
    pm.inf(f"Total Chunks: {len(chunks)}")
    if chunks:
        pm.inf(f"First Chunk Content:\n{chunks[0].page_content[:500]}...")
    # * These chunks are then stored in the vector store and used by the retriever to provide accurate, context-grounded answers.”