"""
Vector Store Module
Embedding'leri oluşturur ve vector store'da saklar
"""

from langchain_ollama import OllamaEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_chroma import Chroma
import os

class VectorStoreManager:
    """Vector store yönetimi için sınıf"""
    
    def __init__(self, 
                 model_name: str = "llama2:latest",
                 store_type: str = "chroma",
                 persist_directory: str = "./chroma_db"):
        """
        Args:
            model_name: Ollama model adı
            store_type: Vector store tipi ('chroma' veya 'faiss')
            persist_directory: Vector store'un kaydedileceği dizin
        """
        self.model_name = model_name
        self.store_type = store_type
        self.persist_directory = persist_directory        
        self.embeddings = OllamaEmbeddings(
            model=model_name,
            base_url="http://localhost:11434"
        )
        
        self.vectorstore = None
    
    def create_vectorstore(self, chunks):
        """Chunk'lardan vector store oluştur"""
        print(f"\n Vector store oluşturuluyor ({self.store_type})...")
        
        if self.store_type == "chroma":
            self.vectorstore = Chroma.from_documents(
                documents=chunks,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            print(f"Chroma vector store oluşturuldu: {self.persist_directory}")
            
        elif self.store_type == "faiss":
            self.vectorstore = FAISS.from_documents(
                documents=chunks,
                embedding=self.embeddings
            )
            print(f"✓ FAISS vector store oluşturuldu")
        
        return self.vectorstore
    
    def load_vectorstore(self):
        """Mevcut vector store'u yükle"""
        if self.store_type == "chroma":
            if os.path.exists(self.persist_directory):
                print(f"Mevcut Chroma database yükleniyor...")
                self.vectorstore = Chroma(
                    persist_directory=self.persist_directory,
                    embedding_function=self.embeddings
                )
                print("✓ Vector store yüklendi")
                return self.vectorstore
            else:
                print("Mevcut database bulunamadı")
                return None
        else:
            print("⚠️  FAISS için load işlemi desteklenmiyor. save/load_local kullanın.")
            return None
    
    def save_faiss(self, path: str = "./faiss_index"):
        """FAISS index'ini kaydet"""
        if self.vectorstore and self.store_type == "faiss":
            self.vectorstore.save_local(path)
            print(f"✓ FAISS index kaydedildi: {path}")
    
    def load_faiss(self, path: str = "./faiss_index"):
        """FAISS index'ini yükle"""
        if self.store_type == "faiss":
            self.vectorstore = FAISS.load_local(
                path,
                self.embeddings,
                allow_dangerous_deserialization=True
            )
            print(f"✓ FAISS index yüklendi: {path}")
            return self.vectorstore
    
    def similarity_search(self, query: str, k: int = 4):
        """Benzerlik araması yap"""
        if not self.vectorstore:
            print("⚠️  Vector store yüklenmemiş!")
            return []
        
        results = self.vectorstore.similarity_search(query, k=k)
        return results
    
    def get_retriever(self, k: int = 4):
        """Retriever objesi döndür"""
        if not self.vectorstore:
            print("⚠️  Vector store yüklenmemiş!")
            return None
        
        return self.vectorstore.as_retriever(
            search_type="similarity",
            search_kwargs={"k": k}
        )


if __name__ == "__main__":
    # Test
    print("Vector Store Manager testi")
    manager = VectorStoreManager(
        model_name="llama2:latest",
        store_type="chroma"
    )
    
    # Mevcut store'u yükle
    vectorstore = manager.load_vectorstore()
    
    if vectorstore:
        # Test araması
        results = manager.similarity_search("What is attention mechanism?", k=3)
        print(f"\n🔍 Test araması sonuçları ({len(results)} döküman):")
        for i, doc in enumerate(results):
            print(f"\n[{i+1}] {doc.page_content[:200]}...")
