"""
Ana Program - LangChain RAG ve Agent Sistemi
PDF dökümanlarınızla çalışan kapsamlı bir RAG ve Agent sistemi
"""

import os
from pdf_loader import PDFProcessor
from vector_store import VectorStoreManager
from rag_chain import RAGChain
from agent import PDFAgent

def print_banner():
    """Hoş geldin banner'ı"""
    print("\n" + "="*80)
    print(" "*20 + "🚀 LANGCHAIN RAG & AGENT SİSTEMİ 🚀")
    print("="*80)
    print("PDF dökümanlarınız: Attention, LLM Forgetting, Testing LLMs")
    print("Model: Ollama llama3:latest")
    print("="*80 + "\n")

def setup_rag_system(force_rebuild: bool = False):
    """RAG sistemini kur ve hazırla"""
    
    print("📋 ADIM 1: PDF İşleme")
    print("-" * 80)
    
    # Vector store manager oluştur
    vs_manager = VectorStoreManager(
        model_name="llama3:latest",
        store_type="chroma",
        persist_directory="./chroma_db"
    )
    
    # Mevcut database'i kontrol et
    if not force_rebuild and os.path.exists("./chroma_db"):
        print("📂 Mevcut vector database bulundu, yükleniyor...")
        vectorstore = vs_manager.load_vectorstore()
        
        if vectorstore:
            print("✅ Mevcut database yüklendi!\n")
            retriever = vs_manager.get_retriever(k=4)
            return vs_manager, retriever
    
    # Yeni database oluştur
    print("🆕 Yeni vector database oluşturuluyor...\n")
    
    # PDF'leri işle
    pdf_processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
    chunks = pdf_processor.process_pdfs(".")
    
    if not chunks:
        print("❌ Hiç döküman bulunamadı!")
        return None, None
    
    print(f"\n📋 ADIM 2: Vector Store Oluşturma")
    print("-" * 80)
    
    # Vector store oluştur
    vectorstore = vs_manager.create_vectorstore(chunks)
    retriever = vs_manager.get_retriever(k=4)
    
    print("✅ Vector store hazır!\n")
    return vs_manager, retriever

def demo_rag_chain(retriever):
    """RAG Chain demo"""
    print("\n" + "="*80)
    print("🔗 RAG CHAIN DEMO")
    print("="*80 + "\n")
    
    # RAG Chain oluştur
    rag = RAGChain(retriever, model_name="llama3:latest", temperature=0.7)
    
    # Demo sorular
    demo_questions = [
        "What is the attention mechanism in transformers?",
        "Tell me about LLM forgetting problem",
        "How can we test and evaluate large language models?"
    ]
    
    print("📝 Örnek sorular test ediliyor...\n")
    
    for i, question in enumerate(demo_questions, 1):
        print(f"\n{'='*80}")
        print(f"SORU {i}: {question}")
        print('='*80)
        
        # QA chain ile cevapla
        response = rag.query(question, chain_type="qa")
        print(f"\n🤖 CEVAP:\n{response['answer'][:500]}...")
        
        if response.get('source_documents'):
            print(f"\n📚 Kaynak sayısı: {len(response['source_documents'])}")
        
        print()
        input("⏎ Devam etmek için Enter'a basın...")

def demo_agent(retriever):
    """Agent demo"""
    print("\n" + "="*80)
    print("🤖 AGENT DEMO")
    print("="*80 + "\n")
    
    # Agent oluştur
    agent = PDFAgent(retriever, model_name="llama3:latest", temperature=0.7)
    
    # Demo görevler
    demo_tasks = [
        "Hangi PDF dökümanları mevcut?",
        "Attention mechanism hakkında bilgi ver",
        "LLM testing konusunu özetle"
    ]
    
    print("📝 Örnek görevler test ediliyor...\n")
    
    for i, task in enumerate(demo_tasks, 1):
        print(f"\n{'='*80}")
        print(f"GÖREV {i}: {task}")
        print('='*80 + "\n")
        
        result = agent.run(task)
        
        if "error" not in result:
            print(f"\n✅ Sonuç:\n{result.get('output', 'N/A')[:500]}...")
        else:
            print(f"\n❌ Hata: {result['error']}")
        
        print()
        input("⏎ Devam etmek için Enter'a basın...")

def interactive_mode(retriever):
    """İnteraktif mod - Kullanıcı seçimi"""
    
    while True:
        print("\n" + "="*80)
        print("📌 İNTERAKTİF MOD - MENÜ")
        print("="*80)
        print("\n1. 💬 RAG Chat (Basit Soru-Cevap)")
        print("2. 🗣️  Conversational RAG (Konuşma Geçmişi ile)")
        print("3. 🤖 Agent Chat (Araçlar ile)")
        print("4. 🔍 Test Araması")
        print("5. 🚪 Çıkış")
        
        choice = input("\nSeçiminiz (1-5): ").strip()
        
        if choice == "1":
            print("\n💬 RAG Chat Başlatılıyor (QA Chain)...")
            rag = RAGChain(retriever, model_name="llama3:latest")
            rag.chat(chain_type="qa")
            
        elif choice == "2":
            print("\n🗣️  Conversational RAG Başlatılıyor...")
            rag = RAGChain(retriever, model_name="llama3:latest")
            rag.chat(chain_type="conversational")
            
        elif choice == "3":
            print("\n🤖 Agent Chat Başlatılıyor...")
            agent = PDFAgent(retriever, model_name="llama3:latest")
            agent.chat()
            
        elif choice == "4":
            query = input("\n🔍 Arama sorgusu: ").strip()
            if query:
                vs_manager = VectorStoreManager()
                vs_manager.vectorstore = retriever.vectorstore
                results = vs_manager.similarity_search(query, k=3)
                
                print(f"\n📊 {len(results)} sonuç bulundu:\n")
                for i, doc in enumerate(results, 1):
                    print(f"[{i}] {doc.page_content[:200]}...")
                    print(f"    Kaynak: {doc.metadata.get('source', 'N/A')}\n")
            
        elif choice == "5":
            print("\n👋 Görüşmek üzere!")
            break
            
        else:
            print("\n⚠️  Geçersiz seçim!")

def main():
    """Ana program"""
    print_banner()
    
    # Ollama kontrol
    print("🔍 Ollama kontrol ediliyor...")
    try:
        import requests
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code == 200:
            print("✅ Ollama çalışıyor\n")
        else:
            print("⚠️  Ollama'ya erişilemiyor. Lütfen Ollama'nın çalıştığından emin olun.\n")
    except:
        print("⚠️  Ollama bağlantısı kontrol edilemedi. Devam ediyoruz...\n")
    
    # Kullanıcı tercihi
    print("Mevcut bir vector database'i yüklemek ister misiniz?")
    print("1. Evet, mevcut database'i yükle (hızlı)")
    print("2. Hayır, PDF'leri yeniden işle (yavaş ama güncel)")
    
    choice = input("\nSeçim (1/2) [Varsayılan: 1]: ").strip() or "1"
    force_rebuild = (choice == "2")
    
    # RAG sistemini kur
    vs_manager, retriever = setup_rag_system(force_rebuild=force_rebuild)
    
    if not retriever:
        print("❌ Sistem başlatılamadı!")
        return
    
    print("\n✨ Sistem hazır!\n")
    
    # Mod seçimi
    print("Hangi modda çalışmak istersiniz?")
    print("1. 🎬 Demo Mod (Otomatik örnekler)")
    print("2. 💬 İnteraktif Mod (Kendi sorularınızı sorun)")
    
    mode = input("\nSeçim (1/2) [Varsayılan: 2]: ").strip() or "2"
    
    if mode == "1":
        # Demo mod
        print("\n🎬 Demo Modu Başlatılıyor...\n")
        input("RAG Chain demo'sunu başlatmak için Enter'a basın...")
        demo_rag_chain(retriever)
        
        input("\nAgent demo'sunu başlatmak için Enter'a basın...")
        demo_agent(retriever)
        
        print("\n✨ Demo tamamlandı!")
        
    else:
        # İnteraktif mod
        interactive_mode(retriever)
    
    print("\n✅ Program sonlandı. İyi günler!")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Program kullanıcı tarafından durduruldu.")
    except Exception as e:
        print(f"\n❌ Beklenmeyen hata: {e}")
        import traceback
        traceback.print_exc()
