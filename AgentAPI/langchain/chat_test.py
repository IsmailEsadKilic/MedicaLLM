"""
Konuşmalı Test - Geçmiş Tutuyor!
"""
import os
print("\n💬 Konuşmalı PDF Q&A Testi\n" + "="*60 + "\n")

# Database kontrol
if not os.path.exists("./chroma_db"):
    print("❌ Database bulunamadı! Önce: python main.py\n")
    exit(1)

from vector_store import VectorStoreManager
from rag_chain import RAGChain

# Setup
print("📂 Database yükleniyor...")
vs_manager = VectorStoreManager(model_name="llama2:latest")
vectorstore = vs_manager.load_vectorstore()

if not vectorstore:
    print("❌ Database yüklenemedi!")
    exit(1)

print("✓ Database yüklendi\n")

retriever = vs_manager.get_retriever(k=5)

print("🔗 RAG Chain oluşturuluyor (QA mode)...")
rag = RAGChain(retriever, model_name="llama3.2:3b")
print("✓ Hazır!\n")

print("="*60)
print("İNTERAKTİF SOHBET (QA Mode + Kaynaklar)")
print("="*60)
print("Çıkmak için: 'q' veya 'quit'\n")

# Özel chat döngüsü - Kaynakları gösterir
while True:
    question = input("Siz: ").strip()
    
    if question.lower() in ['quit', 'exit', 'q']:
        print("Görüşmek üzere!")
        break
    
    if not question:
        continue
    
    try:
        response = rag.query(question, chain_type="qa")
        
        print(f"\n AI: {response['answer']}")
        
        # KAYNAKLAR GÖSTER
        if response.get('source_documents'):
            print(f"\n KAYNAK DÖKÜMANLAR:")
            print("-"*60)
            for i, doc in enumerate(response['source_documents'], 1):
                source = doc.metadata.get('source', 'Bilinmiyor')
                page = doc.metadata.get('page', '?')
                print(f"  [{i}] {source} (Sayfa: {page})")
                print(f"      İçerik: {doc.page_content[:150]}...")
            print("-"*60)
        
        print()
        
    except Exception as e:
        print(f"Hata: {e}\n")

print("\n Sohbet sona erdi!\n")
