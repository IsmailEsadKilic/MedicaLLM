from pdb import pm

from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from typing import List

from ..config import settings

from logging import getLogger
logger = getLogger(__name__)

class PDFProcessor:
    """
    Loads and processes PDF documents into text chunks: List[Document]
    """

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
        logger.debug(f"Splitting {len(documents)} documents into chunks...")
        chunks = self.text_splitter.split_documents(documents)
        logger.debug(f"{len(chunks)} chunks created")
        return chunks

    def load_single_pdf(self, pdf_path: str) -> List[Document]:
        logger.debug(f"Loading PDF: {pdf_path}")
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        logger.debug(f"{len(documents)} pages loaded")
        return documents

    def load_all_pdfs(self, directory_path: str = settings.pdf_dir) -> List[Document]:
        """
        Load all PDFs from a directory.
        """
        logger.debug(f"Loading all PDFs in directory: {directory_path}")
        loader = DirectoryLoader(
            directory_path,
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,  # type: ignore
            show_progress=True,
        )
        documents = loader.load()
        logger.debug(f"{len(documents)} pages loaded")
        return documents

    def process_single_pdf(self, pdf_path: str) -> List[Document]:
        """
        Load and process a single PDF into text chunks.
        """
        logger.debug(f"Processing single PDF: {pdf_path}")
        documents = self.load_single_pdf(pdf_path)
        chunks = self.split_documents(documents)
        return chunks

    def process_pdfs(
        self, directory_path: str = settings.pdf_dir
    ) -> tuple[List[Document], int]:
        """
        oad and process all PDFs from a directory into text chunks.
        """
        logger.debug(f"Processing all PDFs in directory: {directory_path}")
        documents = self.load_all_pdfs(directory_path)
        chunks = self.split_documents(documents)
        return chunks, len(documents)
