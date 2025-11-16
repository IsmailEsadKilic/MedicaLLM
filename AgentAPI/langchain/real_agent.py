"""
Real LangChain Agent Module
LangChain Agent framework kullanarak gerçek bir agent oluşturur.
agent.py'deki fonksiyonları tool olarak kullanır.
"""

from langchain_ollama import ChatOllama
from langchain_core.tools import Tool
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from agent import PDFAgent
import os
import re

class RealPDFAgent:
    """
    Gerçek LangChain Agent - Tool seçimi yapan, reasoning gösteren agent
    
    Özellikler:
    - Otomatik tool seçimi (LLM karar verir)
    - Multi-step reasoning
    - Verbose mode ile düşünce sürecini gösterir
    - agent.py'deki fonksiyonları tool olarak kullanır
    """
    
    def __init__(self, 
                 retriever,
                 model_name: str = "llama2:latest",
                 temperature: float = 0.7,
                 verbose: bool = True):
        """
        Args:
            retriever: Vector store retriever
            model_name: Ollama model adı
            temperature: Model sıcaklığı
            verbose: True ise agent'ın düşünce sürecini gösterir
        """
        self.retriever = retriever
        self.model_name = model_name
        self.temperature = temperature
        self.verbose = verbose
        
        print(f"🤖 Real Agent başlatılıyor: {model_name}")
        
        # LLM oluştur
        self.llm = ChatOllama(
            model=model_name,
            temperature=temperature,
            base_url="http://localhost:11434"
        )
        
        # PDFAgent oluştur (tool'lar için)
        print("📦 Agent tool'ları hazırlanıyor...")
        self.pdf_agent = PDFAgent(retriever, model_name, temperature)
        
        # Tool'ları tanımla
        self.tools = self._create_tools()
        self.tool_dict = {tool.name: tool for tool in self.tools}
        
        # System prompt
        tool_descriptions = "\n".join([
            f"- {tool.name}: {tool.description}" 
            for tool in self.tools
        ])
        
        self.system_prompt = f"""You are a helpful AI assistant with access to tools. You must use tools to answer questions.

Available tools:
{tool_descriptions}

When you need to use a tool, respond EXACTLY in this format:
Action: tool_name
Action Input: input_text

After seeing the tool result (Observation), you can either:
1. Use another tool if needed
2. Provide the Final Answer

When you have the answer, respond with:
Final Answer: your answer here

Always think step by step."""
        
        print("✓ Real Agent hazır!\n")
        if self.verbose:
            print("💡 Verbose mode aktif - Agent'ın düşünce süreci gösterilecek\n")
    
    def _create_tools(self):
        """LangChain Tool'larını oluştur"""
        
        tools = [
            Tool(
                name="search_pdfs",
                func=self.pdf_agent.search_pdfs,
                description=(
                    "PDF dökümanlarında semantic arama yapar. "
                    "Kullanıcı bir konu hakkında detaylı bilgi istediğinde bu tool'u kullan. "
                    "Input: Arama sorgusu (string). "
                    "Output: İlgili PDF chunk'ları ve kaynak bilgileri."
                )
            ),
            Tool(
                name="list_pdfs",
                func=self.pdf_agent.get_document_info,
                description=(
                    "Sistemdeki tüm PDF dosyalarını listeler. "
                    "Kullanıcı 'hangi PDF'ler var', 'PDF listesi' gibi sorular sorduğunda kullan. "
                    "Input: Boş string ('') veya herhangi bir string. "
                    "Output: PDF dosya adları ve boyutları."
                )
            ),
            Tool(
                name="summarize_topic",
                func=self.pdf_agent.summarize_topic,
                description=(
                    "Bir konuyu kısaca özetler. "
                    "Kullanıcı 'özetle', 'summary', 'kısaca anlat' gibi isteklerde bulunduğunda kullan. "
                    "Input: Özetlenecek konu (string). "
                    "Output: Kısa özet."
                )
            )
        ]
        
        print(f"✓ {len(tools)} tool tanımlandı:")
        for tool in tools:
            print(f"  - {tool.name}")
        
        return tools
    
    def run(self, query: str):
        """
        Agent'ı çalıştır - ReAct loop
        
        Args:
            query: Kullanıcı sorusu
        
        Returns:
            Dict: {"output": str, "intermediate_steps": List}
        """
        print(f"\n{'='*70}")
        print(f"🎯 AGENT ÇALIŞTIRILIYOR")
        print(f"{'='*70}")
        print(f"💬 Soru: {query}\n")
        
        if self.verbose:
            print(f"{'='*70}")
            print("🧠 AGENT DÜŞÜNCE SÜRECİ:")
            print(f"{'='*70}\n")
        
        messages = [
            SystemMessage(content=self.system_prompt),
            HumanMessage(content=f"Question: {query}")
        ]
        
        intermediate_steps = []
        max_iterations = 5
        
        try:
            for iteration in range(max_iterations):
                if self.verbose:
                    print(f"\n🔄 Iteration {iteration + 1}/{max_iterations}")
                    print("-" * 70)
                
                # LLM'den cevap al
                response = self.llm.invoke(messages)
                response_text = response.content
                
                if self.verbose:
                    print(f"\n💭 Agent Response:\n{response_text}\n")
                
                # Final Answer kontrolü
                if "Final Answer:" in response_text:
                    final_answer = response_text.split("Final Answer:")[-1].strip()
                    if self.verbose:
                        print(f"✅ Final answer bulundu!")
                    
                    return {
                        "output": final_answer,
                        "intermediate_steps": intermediate_steps
                    }
                
                # Action parsing
                action_match = re.search(r'Action:\s*(\w+)', response_text)
                action_input_match = re.search(r'Action Input:\s*(.+?)(?=\n|$)', response_text, re.DOTALL)
                
                if action_match and action_input_match:
                    action = action_match.group(1).strip()
                    action_input = action_input_match.group(1).strip()
                    
                    if self.verbose:
                        print(f"🔧 Tool seçildi: {action}")
                        print(f"📝 Input: {action_input}")
                    
                    # Tool'u çalıştır
                    if action in self.tool_dict:
                        try:
                            observation = self.tool_dict[action].func(action_input)
                            intermediate_steps.append((action, action_input, observation))
                            
                            if self.verbose:
                                print(f"\n📊 Observation:")
                                print(f"{observation[:500]}..." if len(str(observation)) > 500 else observation)
                            
                            # Observation'ı mesajlara ekle
                            messages.append(AIMessage(content=response_text))
                            messages.append(HumanMessage(content=f"Observation: {observation}\n\nContinue thinking or provide Final Answer."))
                            
                        except Exception as e:
                            error_msg = f"Tool error: {e}"
                            if self.verbose:
                                print(f"\n❌ {error_msg}")
                            messages.append(AIMessage(content=response_text))
                            messages.append(HumanMessage(content=f"Observation: {error_msg}\n\nTry another approach."))
                    else:
                        if self.verbose:
                            print(f"⚠️  Tool '{action}' bulunamadı!")
                        messages.append(AIMessage(content=response_text))
                        messages.append(HumanMessage(content=f"Error: Tool '{action}' not found. Available tools: {list(self.tool_dict.keys())}"))
                else:
                    # Action parse edilemedi
                    if self.verbose:
                        print("⚠️  Action formatı hatalı, tekrar deneniyor...")
                    messages.append(AIMessage(content=response_text))
                    messages.append(HumanMessage(content="Please use the correct format:\nAction: tool_name\nAction Input: input"))
            
            # Max iteration ulaşıldı
            if self.verbose:
                print(f"\n⏰ Max iteration ({max_iterations}) ulaşıldı")
            
            return {
                "output": "Üzgünüm, cevabı bulmak için yeterli adım atamadım.",
                "intermediate_steps": intermediate_steps
            }
            
        except Exception as e:
            print(f"\n❌ Agent hatası: {e}")
            return {
                "output": f"Üzgünüm, bir hata oluştu: {e}",
                "intermediate_steps": intermediate_steps
            }
    
    def chat(self):
        """İnteraktif chat modu"""
        print(f"\n{'='*70}")
        print("🤖 REAL AGENT CHAT SİSTEMİ")
        print(f"{'='*70}")
        print("Bu agent otomatik olarak tool seçimi yapacak!")
        print("Çıkmak için: 'q', 'quit' veya 'exit'\n")
        
        while True:
            question = input("👤 Siz: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Görüşmek üzere!")
                break
            
            if not question:
                continue
            
            try:
                result = self.run(question)
                
                print(f"\n{'='*70}")
                print("💡 FINAL CEVAP:")
                print(f"{'='*70}")
                print(result["output"])
                print(f"{'='*70}\n")
                
            except KeyboardInterrupt:
                print("\n\n⏸️  İşlem durduruldu.")
                break
            except Exception as e:
                print(f"\n❌ Hata: {e}\n")


def demo():
    """Demo: Agent'ı test et"""
    print("\n🎬 REAL AGENT DEMO\n")
    print("="*70)
    
    # Database yükle
    from vector_store import VectorStoreManager
    
    print("📂 Database yükleniyor...")
    vs_manager = VectorStoreManager(model_name="llama2:latest")
    
    if not os.path.exists("./chroma_db"):
        print("❌ Database bulunamadı!")
        print("   Önce database oluşturun: python main.py")
        return
    
    vectorstore = vs_manager.load_vectorstore()
    if not vectorstore:
        print("❌ Database yüklenemedi!")
        return
    
    print("✓ Database yüklendi\n")
    
    retriever = vs_manager.get_retriever(k=2)
    
    # Real Agent oluştur
    agent = RealPDFAgent(
        retriever=retriever,
        model_name="llama2:latest",
        temperature=0.7,
        verbose=True  # ← Düşünce sürecini göster
    )
    
    # Test soruları
    test_questions = [
        "Hangi PDF dosyaları var sistemde?",
        "Attention mechanism nedir?",
        # "Attention konusunu özetle"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{'='*70}")
        print(f"TEST {i}/{len(test_questions)}")
        print(f"{'='*70}\n")
        
        result = agent.run(question)
        
        print(f"\n{'='*70}")
        print("✅ Test tamamlandı!")
        print(f"{'='*70}\n")
        
        if i < len(test_questions):
            input("⏎ Devam etmek için Enter'a basın...\n")
    
    print("\n✅ Tüm testler tamamlandı!")


if __name__ == "__main__":
    demo()
