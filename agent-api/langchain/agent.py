"""
LangChain Agent Module
Araçlar ile donatılmış basit agent oluşturur
"""

from langchain_ollama import ChatOllama
from typing import List
import os

class PDFAgent:
    """PDF'ler üzerinde çalışan basit Agent"""
    
    def __init__(self, 
                 retriever,
                 model_name: str = "llama2:latest",
                 temperature: float = 0.7):
        """
        Args:
            retriever: Vector store retriever
            model_name: Ollama model adı
            temperature: Model sıcaklığı
        """
        self.retriever = retriever
        self.model_name = model_name
        self.temperature = temperature
        
        print(f"🤖 Agent LLM başlatılıyor: {model_name}")
        self.llm = ChatOllama(
            model=model_name,
            temperature=temperature,
            base_url="http://10.91.136.163:11434"
        )
        
        print("✓ Agent oluşturuldu")
    
    def search_pdfs(self, query: str) -> str:
        """PDF dökümanlarında arama yap"""
        try:
            docs = self.retriever.get_relevant_documents(query)
            if not docs:
                return "İlgili bilgi bulunamadı."
            
            result = "Bulunan bilgiler:\n\n"
            for i, doc in enumerate(docs[:3]):
                source = doc.metadata.get("source", "Bilinmiyor")
                page = doc.metadata.get("page", "?")
                result += f"[{i+1}] Kaynak: {source} (Sayfa: {page})\n"
                result += f"{doc.page_content[:500]}...\n\n"
            
            return result
        except Exception as e:
            return f"Arama hatası: {str(e)}"
    
    def get_document_info(self, query: str = "") -> str:
        """Döküman bilgilerini getir"""
        try:
            data_dir = "./data"
            
            if not os.path.exists(data_dir):
                return "❌ 'data' klasörü bulunamadı!"
            
            # PDF dosyalarını listele
            pdf_files = [f for f in os.listdir(data_dir) if f.endswith('.pdf')]
            
            if not pdf_files:
                return "❌ data/ klasöründe hiç PDF bulunamadı!"
            
            info = f"📄 Mevcut PDF Dökümanlar ({len(pdf_files)} adet):\n\n"
            for i, pdf in enumerate(pdf_files, 1):
                pdf_path = os.path.join(data_dir, pdf)
                size = os.path.getsize(pdf_path) / 1024  # KB
                info += f"{i}. {pdf} (Boyut: {size:.2f} KB)\n"
            
            return info
        except Exception as e:
            return f"❌ Bilgi alma hatası: {str(e)}"
    
    def summarize_topic(self, topic: str) -> str:
        """Belirli bir konu hakkında özet çıkar"""
        try:
            docs = self.retriever.get_relevant_documents(topic)
            if not docs:
                return f"'{topic}' hakkında bilgi bulunamadı."
            
            # İlk birkaç dökümanı birleştir
            combined_text = "\n".join([doc.page_content for doc in docs[:3]])
            
            # LLM ile özetle
            prompt = f"""Aşağıdaki metni özetle. Kısa ve öz ol.

Metin:
{combined_text[:2000]}

Özet:"""
            
            response = self.llm.invoke(prompt)
            return response.content
            
        except Exception as e:
            return f"Özetleme hatası: {str(e)}"
    
    def run(self, query: str):
        """Agent'ı çalıştır - Basit soru-cevap"""
        print(f"\n🎯 Agent çalıştırılıyor...")
        print(f"💬 Query: {query}\n")
        
        try:
            # Önce ilgili dökümanları bul
            docs_info = self.search_pdfs(query)
            
            # Sonra LLM'e sor
            prompt = f"""Sen PDF dökümanları üzerinde çalışan bir asistansın.

Arama Sonuçları:
{docs_info}

Kullanıcı Sorusu: {query}

Lütfen yukarıdaki bilgileri kullanarak soruyu cevapla."""

            response = self.llm.invoke(prompt)
            
            return {"output": response.content}
            
        except Exception as e:
            return {"error": str(e)}
    
    def chat(self):
        """İnteraktif chat modu"""
        print("\n🤖 PDF Agent Chat Sistemi Başlatıldı!")
        print("Agent, PDF'lerden bilgi bulup sorularınızı cevaplayacak.")
        print("Çıkmak için 'quit', 'exit' veya 'q' yazın\n")
        
        while True:
            question = input("👤 Siz: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Görüşmek üzere!")
                break
            
            if not question:
                continue
            
            try:
                result = self.run(question)
                
                if "error" in result:
                    print(f"\n❌ Hata: {result['error']}\n")
                else:
                    print(f"\n🤖 Agent: {result.get('output', 'Cevap oluşturulamadı')}\n")
                    
            except Exception as e:
                print(f"❌ Hata: {e}\n")


if __name__ == "__main__":
    print("Agent modülü - main.py üzerinden kullanın")
