"""
PDF Loader Module
PDF dosyalarını yükler ve işler
"""

from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from typing import List
import os

class PDFProcessor:
    """PDF dosyalarını yükleyen ve işleyen sınıf"""
    
    def __init__(self, chunk_size: int = 400, chunk_overlap: int = 100):
        """
        Args:
            chunk_size: Her bir text chunk'ının boyutu
            chunk_overlap: Chunk'lar arasındaki overlap miktarı
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )
    
    def load_single_pdf(self, pdf_path: str):
        """Tek bir PDF dosyasını yükle"""
        print(f"📄 PDF yükleniyor: {pdf_path}")
        loader = PyPDFLoader(pdf_path)
        documents = loader.load()
        print(f"✓ {len(documents)} sayfa yüklendi")
        return documents
    
    def load_all_pdfs(self, directory_path: str = "./data"):
        """Bir dizindeki tüm PDF dosyalarını yükle"""
        print(f"📁 Dizindeki tüm PDF'ler yükleniyor: {directory_path}")
        loader = DirectoryLoader(
            directory_path,
            glob="**/*.pdf",
            loader_cls=PyPDFLoader,
            show_progress=True
        )
        documents = loader.load()
        print(f"✓ Toplam {len(documents)} sayfa yüklendi")
        return documents
    
    def split_documents(self, documents):
        """Dökümanları chunk'lara böl"""
        print(f"✂️  Dökümanlar chunk'lara bölünüyor...")
        chunks = self.text_splitter.split_documents(documents)
        print(f"✓ {len(chunks)} chunk oluşturuldu")
        return chunks
    
    def process_pdfs(self, directory_path: str = "./data"):
        """PDF'leri yükle ve işle"""
        documents = self.load_all_pdfs(directory_path)
        chunks = self.split_documents(documents)
        return chunks


if __name__ == "__main__":
    # Test
    processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
    chunks = processor.process_pdfs()
    print(f"\n📊 İşlem tamamlandı!")
    print(f"Toplam chunk sayısı: {len(chunks)}")
    if chunks:
        print(f"\nÖrnek chunk (ilk 200 karakter):\n{chunks[0].page_content[:200]}...")
