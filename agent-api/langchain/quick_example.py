"""
Hızlı Başlangıç Örneği
En basit kullanım için
"""

from pdf_loader import PDFProcessor
from vector_store import VectorStoreManager
from rag_chain import RAGChain

print("="*80)
print("🚀 LangChain RAG - Hızlı Örnek")
print("="*80 + "\n")

# 1. PDF'leri yükle
print("📄 ADIM 1: PDF'ler yükleniyor...")
processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
chunks = processor.process_pdfs("./data")

# 2. Vector store oluştur
print("\n🗄️  ADIM 2: Vector store oluşturuluyor...")
vs_manager = VectorStoreManager(
    model_name="llama2:latest",
    store_type="chroma",
    persist_directory="./chroma_db"
)
vectorstore = vs_manager.create_vectorstore(chunks)
retriever = vs_manager.get_retriever(k=3)

# 3. RAG Chain oluştur
print("\n🔗 ADIM 3: RAG Chain oluşturuluyor...")
rag = RAGChain(retriever, model_name="llama2:latest", temperature=0.7)

# 4. Örnek soru
print("\n💬 ADIM 4: Örnek soru soruluyor...")
question = "What is the attention mechanism in neural networks?"
print(f"Soru: {question}\n")

response = rag.query(question, chain_type="qa")

print("\n" + "="*80)
print("🎯 CEVAP:")
print("="*80)
print(response["answer"])

if response.get("source_documents"):
    print("\n" + "="*80)
    print("📚 KAYNAK DÖKÜMANLAR:")
    print("="*80)
    for i, doc in enumerate(response["source_documents"][:2]):
        source = doc.metadata.get("source", "Bilinmiyor")
        page = doc.metadata.get("page", "?")
        print(f"\n[{i+1}] Kaynak: {source} (Sayfa: {page})")
        print(f"İçerik: {doc.page_content[:200]}...")

print("\n" + "="*80)
print("✅ Örnek tamamlandı!")
print("Daha fazlası için: python main.py")
print("="*80)
