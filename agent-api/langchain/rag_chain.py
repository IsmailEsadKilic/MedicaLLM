"""
RAG Chain Module
RAG (Retrieval-Augmented Generation) zinciri oluşturur
Modern LangChain LCEL API kullanır
"""

from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

class RAGChain:
    """RAG zinciri yönetimi için sınıf"""
    
    def __init__(self, 
                 retriever,
                 model_name: str = "llama2:latest",
                 temperature: float = 0.7):
        """
        Args:
            retriever: Vector store'dan elde edilen retriever
            model_name: Ollama model adı
            temperature: Model sıcaklığı (0-1 arası)
        """
        self.retriever = retriever
        self.model_name = model_name
        self.temperature = temperature
        self.chat_history = []
        
        # LLM oluştur
        print(f"LLM başlatılıyor: {model_name}")
        self.llm = ChatOllama(
            model=model_name,
            temperature=temperature,
            base_url="http://10.91.136.163:11434"
        )
        
        # Chain'leri oluştur
        self._create_chains()
    
    def _create_chains(self):
        """Farklı chain tipleri oluştur"""
        
        # Basit QA prompt
        self.qa_prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen yardımsever bir AI asistanısın. Aşağıdaki bağlam bilgilerini kullanarak soruyu cevapla.

Bağlam:
{context}

Önemli kurallar:
- Sadece verilen bağlam bilgilerini kullan
- Eğer cevabı bağlamda bulamıyorsan, bilmiyorum de
- Cevapları detaylı ve açıklayıcı ver
- Türkçe veya İngilizce cevap verebilirsin"""),
            ("human", "{question}")
        ])
        
        # Conversational prompt (konuşma geçmişi ile)
        self.conversational_prompt = ChatPromptTemplate.from_messages([
            ("system", """Sen yardımsever bir AI asistanısın. Önceki konuşma geçmişini ve bağlam bilgilerini kullanarak soruyu cevapla.

Konuşma Geçmişi:
{chat_history}

Bağlam:
{context}

Önemli kurallar:
- Önceki konuşmaları hatırla ve tutarlı ol
- Verilen bağlam bilgilerini kullan
- Detaylı ve açıklayıcı cevaplar ver"""),
            ("human", "{question}")
        ])
        
        # QA Chain (LCEL)
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)
        
        self.qa_chain = (
            {"context": self.retriever | format_docs, "question": RunnablePassthrough()}
            | self.qa_prompt
            | self.llm
            | StrOutputParser()
        )
        
        print("✓ RAG chain'leri oluşturuldu")
    
    def query(self, question: str, chain_type: str = "qa"):
        """
        Soru sor ve cevap al
        
        Args:
            question: Sorulacak soru
            chain_type: Chain tipi ('qa', 'conversational')
        """
        print(f"\n💬 Soru: {question}")
        print(f"🔗 Chain tipi: {chain_type}\n")
        
        try:
            # İlgili dökümanları al
            source_docs = self.retriever.invoke(question)
            
            if chain_type == "qa":
                # Basit QA
                answer = self.qa_chain.invoke(question)
                
            elif chain_type == "conversational":
                # Konuşma geçmişi ile
                history_text = "\n".join([f"Human: {h[0]}\nAI: {h[1]}" for h in self.chat_history[-3:]])
                context = "\n\n".join([doc.page_content for doc in source_docs])
                
                messages = self.conversational_prompt.format_messages(
                    chat_history=history_text,
                    context=context,
                    question=question
                )
                
                response = self.llm.invoke(messages)
                answer = response.content
                
                # Konuşma geçmişine ekle
                self.chat_history.append((question, answer))
                
            else:
                raise ValueError(f"Geçersiz chain tipi: {chain_type}")
            
            return {
                "answer": answer,
                "source_documents": source_docs
            }
            
        except Exception as e:
            print(f"❌ Hata: {e}")
            return {
                "answer": f"Üzgünüm, bir hata oluştu: {e}",
                "source_documents": []
            }
    
    def print_response(self, response):
        """Response'u güzel bir formatta yazdır"""
        print("\n" + "="*80)
        print("CEVAP:")
        print("="*80)
        print(response["answer"])
        
        if response.get("source_documents"):
            print("\n" + "="*80)
            print("KAYNAK DÖKÜMANLAR:")
            print("="*80)
            for i, doc in enumerate(response["source_documents"][:3]):
                source = doc.metadata.get("source", "Bilinmiyor")
                page = doc.metadata.get("page", "?")
                print(f"\n[{i+1}] Kaynak: {source} (Sayfa: {page})")
                print(f"İçerik: {doc.page_content[:300]}...")
        
        print("\n" + "="*80)
    
    def chat(self, chain_type: str = "conversational"):
        """İnteraktif chat modu"""
        print("\n RAG Chat Sistemi Başlatıldı!")
        print("Çıkmak için 'quit', 'exit' veya 'q' yazın\n")
        
        while True:
            question = input("Siz: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Görüşmek üzere!")
                break
            
            if not question:
                continue
            
            try:
                response = self.query(question, chain_type=chain_type)
                print(f"\n AI: {response['answer']}\n")
                
            except Exception as e:
                print(f"Hata: {e}\n")


if __name__ == "__main__":
    print("RAG Chain modülü - main.py üzerinden kullanın")
