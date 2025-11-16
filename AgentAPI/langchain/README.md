# LangChain RAG ve Agent Sistemi 🚀

Ollama llama2:latest modeli ile PDF dökümanları üzerinde çalışan kapsamlı bir RAG (Retrieval-Augmented Generation) ve Agent sistemi.

## 📋 Özellikler

### 🔍 RAG (Retrieval-Augmented Generation)
- PDF dökümanlarını otomatik yükleme ve işleme
- Chroma/FAISS vector store desteği
- Semantic search ile ilgili bilgileri bulma
- Farklı chain tipleri:
  - Basit QA Chain
  - Conversational Chain (konuşma geçmişi ile)
  - Custom prompt'lu chain

### 🤖 LangChain Agent
- ReAct pattern ile çalışan agent
- Özelleştirilmiş araçlar:
  - PDF döküman arama
  - Döküman bilgileri getirme
  - Konu özetleme
- Multi-step reasoning
- Tool kullanım izleme

### 📚 Dökümanlar
- `attention.pdf` - Attention mechanism
- `LLMForgetting.pdf` - LLM forgetting problemi
- `TestingAndEvaluatingLLM.pdf` - LLM test ve değerlendirme

## 🚀 Kurulum

### 1. Gereksinimler
```bash
# Python 3.12+ gerekli
# Ollama kurulu ve çalışıyor olmalı
```

### 2. Paketler (Otomatik yüklendi)
- langchain
- langchain-community
- langchain-ollama
- chromadb
- pypdf
- tiktoken
- faiss-cpu
- python-dotenv

### 3. Ollama Modeli
```bash
# llama2:latest modelini indirin
ollama pull llama2:latest

# Ollama'yı başlatın
ollama serve
```

## 💻 Kullanım

### Ana Program
```bash
python main.py
```

Program başladığında:
1. **Database seçimi**: Mevcut database'i yükle veya yeniden oluştur
2. **Mod seçimi**: Demo mod veya İnteraktif mod
3. **İnteraktif modda**:
   - RAG Chat (basit QA)
   - Conversational RAG (konuşma geçmişi)
   - Agent Chat (araçlar ile)
   - Test araması

### Modüller Ayrı Kullanım

#### PDF Yükleme
```python
from pdf_loader import PDFProcessor

processor = PDFProcessor(chunk_size=1000, chunk_overlap=200)
chunks = processor.process_pdfs(".")
```

#### Vector Store
```python
from vector_store import VectorStoreManager

vs_manager = VectorStoreManager(
    model_name="llama2:latest",
    store_type="chroma"
)
vectorstore = vs_manager.create_vectorstore(chunks)
retriever = vs_manager.get_retriever(k=4)
```

#### RAG Chain
```python
from rag_chain import RAGChain

rag = RAGChain(retriever, model_name="llama2:latest")

# Soru sor
response = rag.query("What is attention mechanism?", chain_type="qa")
print(response["answer"])

# Chat modu
rag.chat()
```

#### Agent
```python
from agent import PDFAgent

agent = PDFAgent(retriever, model_name="llama2:latest")

# Görev çalıştır
result = agent.run("PDF dökümanları hakkında bilgi ver")
print(result["output"])

# Chat modu
agent.chat()
```

## 📁 Dosya Yapısı

```
langchain/
├── main.py              # Ana program
├── pdf_loader.py        # PDF yükleme ve işleme
├── vector_store.py      # Vector store yönetimi
├── rag_chain.py         # RAG chain'leri
├── agent.py             # LangChain agent
├── chroma_db/           # Chroma database (otomatik oluşur)
├── attention.pdf        # PDF dökümanlar
├── LLMForgetting.pdf
├── TestingAndEvaluatingLLM.pdf
└── README.md
```

## 🎯 Örnek Kullanım Senaryoları

### 1. Basit Soru-Cevap
```
Soru: "What is the attention mechanism?"
Sistem: PDF'lerden ilgili bilgileri bulur ve cevaplar
```

### 2. Konuşmalı Etkileşim
```
Siz: "Tell me about attention"
AI: [Cevap]
Siz: "Can you explain it more simply?"
AI: [Önceki konuşmayı hatırlayarak cevap]
```

### 3. Agent ile Araç Kullanımı
```
Siz: "Hangi dökümanlar var ve attention hakkında ne söylüyorlar?"
Agent: 
1. get_document_info aracını kullanır
2. search_pdfs aracını kullanır
3. Sonuçları birleştirir ve sunar
```

## 🔧 Konfigürasyon

### Vector Store Ayarları
```python
VectorStoreManager(
    model_name="llama2:latest",  # Ollama model
    store_type="chroma",          # veya "faiss"
    persist_directory="./chroma_db"
)
```

### RAG Chain Ayarları
```python
RAGChain(
    retriever=retriever,
    model_name="llama2:latest",
    temperature=0.7  # 0-1 arası (düşük: tutarlı, yüksek: yaratıcı)
)
```

### PDF İşleme Ayarları
```python
PDFProcessor(
    chunk_size=1000,      # Her chunk'ın boyutu
    chunk_overlap=200     # Chunk'lar arası overlap
)
```

## 🐛 Sorun Giderme

### Ollama Bağlantı Hatası
```bash
# Ollama'nın çalıştığını kontrol edin
curl http://localhost:11434/api/tags

# Ollama'yı yeniden başlatın
ollama serve
```

### Model Bulunamadı
```bash
# Modeli indirin
ollama pull llama2:latest

# Mevcut modelleri listeleyin
ollama list
```

### Import Hatası
```bash
# Sanal ortamı aktif edin
.venv\Scripts\activate

# Paketleri yeniden yükleyin
pip install langchain langchain-community langchain-ollama chromadb pypdf tiktoken faiss-cpu
```

## 📊 Performans İpuçları

1. **İlk çalıştırma yavaş**: PDF'ler işlenip vector store oluşturuluyor
2. **Sonraki çalıştırmalar hızlı**: Mevcut database yükleniyor
3. **Chunk boyutu**: Daha küçük chunk = daha hassas ama daha yavaş
4. **k parametresi**: Daha fazla döküman = daha fazla context ama daha yavaş

## 🎓 Gelişmiş Kullanım

### Custom Prompt
```python
from langchain_core.prompts import ChatPromptTemplate

custom_prompt = ChatPromptTemplate.from_messages([
    ("system", "Sen bir AI asistanısın..."),
    ("human", "{input}")
])
```

### Yeni Araç Ekleme
```python
def custom_tool(query: str) -> str:
    # Özel işlem
    return result

new_tool = Tool(
    name="custom_tool",
    func=custom_tool,
    description="Ne yaptığını açıkla"
)
```

## 📝 Notlar

- Türkçe ve İngilizce sorular destekleniyor
- Sistem kaynak dökümanları gösterir
- Agent verbose mode ile adım adım düşünmeyi gösterir
- Konuşma geçmişi conversational chain'de saklanır

## 🆘 Yardım

Sorunlarla karşılaşırsanız:
1. README'yi dikkatlice okuyun
2. Ollama'nın çalıştığından emin olun
3. Model'in indirilmiş olduğunu kontrol edin
4. Hata mesajlarını dikkatlice inceleyin

## 🚀 Sonraki Adımlar

- [ ] Web UI ekle (Gradio/Streamlit)
- [ ] Daha fazla araç ekle
- [ ] Multi-modal destek (görsel)
- [ ] Farklı embedding modelleri test et
- [ ] Çoklu dil desteği geliştir

---
**Not**: Bu sistem eğitim ve araştırma amaçlıdır. Production kullanımı için ek güvenlik ve optimizasyon gerekebilir.
