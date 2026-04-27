# PubMed Tool Yeniden Tasarımı — Implementation Plan

## Amaç

1. Yerel doküman altyapısını (ChromaDB, PDF indirme, `search_medical_documents`) tamamen kaldır
2. `search_pubmed` tool'unu gelişmiş, doğru sonuç veren bir araştırma aracına dönüştür
3. Kaynak-cevap uyumsuzluğunu çöz

---

## Sorun → Çözüm Eşleştirme Tablosu

| Sorun # | Sorun Açıklaması | Çözüm Yeri | Çözüm |
|---------|-----------------|------------|-------|
| 1.1 | Tüm kaynaklar gönderilir, LLM sadece bazılarını kullanır | Faz 2.4 + Faz 3.2 | REF numarası sistemi + frontend filtreleme |
| 1.2 | Çoklu tool kaynaklar karışıyor | Faz 2.6 | `_store_sources` tool bazlı gruplama |
| 1.3 | Source snippet çok kısa (200 char) | Faz 2.5 | Akıllı snippet çıkarma (400 char) |
| 2.1 | Türkçe sorgu PubMed'e gidiyor | Faz 2.1 | Tool annotation + Türkçe karakter kontrolü |
| 2.2 | Cache key hassasiyeti | Faz 2.7 | Kelime sıralama normalizasyonu |
| 2.3 | Yinelenen efetch (dead code) | Faz 2.8 | Dead code temizliği |
| 2.4 | Abstract gereksiz chunk'lanıyor | Faz 1 | ChromaDB indeksleme tamamen kaldırılıyor |
| 3.1 | Relevance her zaman 0.5 | Faz 2.3b | Keyword overlap ile hesaplama |
| 3.2 | Set-bağımlı citation normalize | Faz 2.3c | Global log-scale (referans: 1000 cite) |
| 3.3 | "Journal Article" evidence tanımsız | Faz 2.3a | `_EVIDENCE_LEVELS`'a ekleme |
| 4.1 | ChromaDB filtre çelişkisi | Faz 1 | ChromaDB tamamen kaldırılıyor |
| 4.2 | Streaming'de tool_result eziliyor | Faz 2.9 | Tüm tool sonuçlarını biriktir |
| 4.3 | System prompt source talimatı çelişkili | Faz 3.1 | REF sistemi ile netleştirme |
| 5.1 | Context window aşılabiliyor | Faz 2.2 | Default 5, max 20 makale |
| 5.2 | 20B model yetersiz | Faz 3.4 | Model önerisi |

---

## Faz 1 — Kaldırılacaklar

### [DELETE] `search_medical_documents` tool'u
**Dosya:** [tools.py](file:///c:/Users/unala/projects/MedicaLLM/backend/src/agent/tools.py)
- L371-449 arası `search_medical_documents` fonksiyonu silinecek
- L850 `ALL_TOOLS` listesinden çıkarılacak
- `_retriever`, `set_retriever`, `get_retriever` fonksiyonları silinecek (L17, L58-62, L81-82)

### [DELETE] ChromaDB indeksleme (`search_pubmed` içinden)
**Dosya:** [tools.py](file:///c:/Users/unala/projects/MedicaLLM/backend/src/agent/tools.py)
- L514-559 arası ChromaDB indeksleme bloğu silinecek
- `_vector_store_manager`, `set_vector_store_manager`, `_pdf_processor`, `set_pdf_processor` silinecek (L18, L64-78)
- `Document` import'u silinecek (L5)
- `VectorStoreRetriever` import'u silinecek (L6)

### [DELETE] ChromaDB Relevance Scoring (`compute_confidence_scores` içinden)
**Dosya:** [service.py](file:///c:/Users/unala/projects/MedicaLLM/backend/src/pubmed/service.py)
- L566-576 arası `vector_store_manager.similarity_search_with_relevance_scores` bloğu silinecek
- `compute_confidence_scores` fonksiyonundan `vector_store_manager` parametresi kaldırılacak

### [DELETE] PDF İndirme ve İndeksleme Altyapısı
**Dosya:** [service.py](file:///c:/Users/unala/projects/MedicaLLM/backend/src/pubmed/service.py)
- L316-429 arası tüm PMC PDF fonksiyonları silinecek:
  - `fetch_pmcid()`, `download_pmc_pdf()`, `is_pmid_pdf_indexed()`, `mark_pmid_pdf_indexed()`, `enrich_articles_with_full_text()`

### [MODIFY] Agent oluşturma — ChromaDB bağımlılığı kaldır
**Dosya:** [agent.py](file:///c:/Users/unala/projects/MedicaLLM/backend/src/agent/agent.py)
- `create_medical_agent()` fonksiyonundan `retriever` ve `vector_store_manager` parametreleri kaldırılacak
- `init_medical_agent()` fonksiyonundan `vsm`, `retriever`, `PDFProcessor` referansları kaldırılacak

### [MODIFY] App başlatma — VectorStore init kaldır
**Dosya:** [main.py](file:///c:/Users/unala/projects/MedicaLLM/backend/src/main.py)
- `init_vector_store_manager` çağrısı kaldırılacak
- `app.state.vsm` ve `app.state.retriever` referansları kaldırılacak

### [DELETE] RAG modülü (isteğe bağlı)
- `backend/src/rag/` klasörü tamamen kaldırılabilir (artık hiçbir yerde kullanılmayacak)
- Veya ileride kullanılabilir diye saklanabilir

### [DELETE] PubMed PDF veritabanı tabloları
**Dosya:** [sql_models.py](file:///c:/Users/unala/projects/MedicaLLM/backend/src/db/sql_models.py) (varsa)
- `PubmedPdfIndexed` modeli kaldırılabilir
- `PubmedIndexed` modeli kaldırılabilir (abstract indeksleme takibi artık gereksiz)

---

## Faz 2 — `search_pubmed` Tool'unu Geliştir

### 2.1 — Sorgu İyileştirme (Query Enhancement)

> [!IMPORTANT]
> En kritik iyileştirme. Kullanıcı Türkçe sorduğunda veya belirsiz sorduğunda PubMed'den doğru sonuç gelmesi gerekiyor.

**Dosya:** [tools.py](file:///c:/Users/unala/projects/MedicaLLM/backend/src/agent/tools.py) — `search_pubmed` fonksiyonu

Yapılacak değişiklik: Tool tanımını güncelleyerek LLM'in **sorguyu İngilizce ve PubMed-optimized formatta** oluşturmasını sağla.

```python
@tool
def search_pubmed(
    query: Annotated[str, "Medical research query for PubMed. MUST be in English. Use MeSH terms when possible (e.g., 'heart failure' not 'kalp yetmezliği'). Combine terms with AND/OR for precision."],
    num_articles: Annotated[int, "Number of articles to retrieve (default: 5, max: 20)"] = 5,
) -> str:
```

Ek olarak, tool içinde basit bir query validation eklenebilir:

```python
# Basit Türkçe karakter kontrolü
turkish_chars = set("çğıöşüÇĞİÖŞÜ")
if any(c in turkish_chars for c in query):
    return "ERROR: PubMed query must be in English. Please rephrase your search in English using medical terminology."
```

### 2.2 — Makale Sayısını Düşür, Kaliteyi Artır

Mevcut default: 10 makale, max 50. Bu çok fazla — LLM hepsini sentezleyemiyor.

```python
num_articles: ... = 5,  # Default 10 → 5
# max: 20 (50 yerine)
num_articles = max(1, min(num_articles, 20))
```

### 2.3 — Confidence Score'u Düzelt

**Dosya:** [service.py](file:///c:/Users/unala/projects/MedicaLLM/backend/src/pubmed/service.py)

#### a) "Journal Article" evidence level ekle
```python
_EVIDENCE_LEVELS = {
    "meta-analysis": 1.0,
    "systematic review": 0.9,
    "randomized controlled trial": 0.85,
    "clinical trial": 0.75,
    "controlled clinical trial": 0.75,
    "practice guideline": 0.7,        # YENİ
    "guideline": 0.7,                  # YENİ
    "comparative study": 0.6,
    "multicenter study": 0.6,
    "cohort study": 0.55,
    "observational study": 0.5,
    "journal article": 0.5,            # YENİ — en yaygın tip
    "case-control study": 0.45,
    "review": 0.4,
    "case reports": 0.3,
    "editorial": 0.15,
    "comment": 0.1,
    "letter": 0.1,
    "preprint": 0.1,                    # YENİ
}
```

#### b) Relevance score'u ChromaDB yerine keyword overlap ile hesapla

ChromaDB kaldırıldığı için yeni bir relevance hesaplama:

```python
def _compute_keyword_relevance(query: str, title: str, abstract: str) -> float:
    """Sorgu terimleri ile makale arasındaki keyword overlap skoru."""
    query_terms = set(query.lower().split())
    # Stopword'leri çıkar
    stopwords = {"the", "a", "an", "in", "on", "of", "for", "and", "or", "to", "with", "is", "are", "was", "were"}
    query_terms -= stopwords
    
    if not query_terms:
        return 0.5
    
    text = f"{title} {abstract}".lower()
    matches = sum(1 for term in query_terms if term in text)
    return min(matches / len(query_terms), 1.0)
```

#### c) Citation normalizasyonunu global yap

```python
def _normalize_citations(citation_count: int, max_citations: int) -> float:
    """Global log-scale normalizasyon."""
    if citation_count <= 0:
        return 0.0
    # Global referans: 1000 citation = 1.0 (çok iyi çalışma)
    return min(math.log1p(citation_count) / math.log1p(1000), 1.0)
```

#### d) Ağırlıkları güncelle (relevance artık keyword-based)

```python
_W_CITATIONS = 0.30
_W_RECENCY   = 0.25
_W_EVIDENCE  = 0.30
_W_RELEVANCE = 0.15  # keyword overlap
```

### 2.4 — Kaynak-Cevap Bağlantısını Kur

**Dosya:** [tools.py](file:///c:/Users/unala/projects/MedicaLLM/backend/src/agent/tools.py) — `search_pubmed` fonksiyonu

LLM'e verilen makale listesine **referans numarası** ekle ve system prompt'ta "bu numaraları kullan" de:

```python
result_parts.append(f"[Article {i} — REF{i}]")
result_parts.append(f"Title: {title}")
# ...
```

Ardından sources listesine de aynı referans numarasını ekle:

```python
source_entry = {
    "ref": f"REF{i}",  # Frontend'de eşleştirme için
    "source": f"PubMed — {journal}" if journal else "PubMed",
    "pmid": pmid,
    "title": title,
    # ...
    "content": abstract[:400],  # 200 → 400 karaktere çıkar
}
```

### 2.5 — Source Snippet'i Zenginleştir

Abstract'ın ilk 200 karakteri yerine, sorgu ile en alakalı cümleyi bul:

```python
def _extract_relevant_snippet(query: str, abstract: str, max_len: int = 400) -> str:
    """Abstract'tan sorguyla en alakalı cümleyi çıkar."""
    if not abstract:
        return ""
    sentences = abstract.replace(". ", ".\n").split("\n")
    query_terms = set(query.lower().split())
    
    scored = []
    for sent in sentences:
        overlap = sum(1 for t in query_terms if t in sent.lower())
        scored.append((overlap, sent.strip()))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    
    result = ""
    for _, sent in scored:
        if len(result) + len(sent) + 2 <= max_len:
            result += sent + " "
        else:
            break
    return result.strip() or abstract[:max_len]
```

### 2.6 — Çoklu Tool Kaynak Karışmasını Önle (Sorun 1.2)

**Dosya:** [tools.py](file:///c:/Users/unala/projects/MedicaLLM/backend/src/agent/tools.py)

`_store_sources` fonksiyonunu güncelleyerek her kaynağa `tool_name` alanı ekle:

```python
def _store_sources(sources: Optional[list], tool_name: str = "unknown") -> None:
    if sources is None:
        return
    # Her kaynağa tool bilgisi ekle
    for s in sources:
        s["tool"] = tool_name
    # ... (geri kalan aynı)
```

Her tool çağrısında:
```python
# search_pubmed içinde:
_store_sources(search_sources, tool_name="search_pubmed")
```

### 2.7 — Cache Key Normalizasyonunu İyileştir (Sorun 2.2)

**Dosya:** [service.py](file:///c:/Users/unala/projects/MedicaLLM/backend/src/pubmed/service.py)

```python
def _normalize_query(query: str) -> str:
    """Kelime sırasından bağımsız normalizasyon."""
    words = query.strip().lower().split()
    # Stopword'leri çıkar
    stopwords = {"the", "a", "an", "in", "on", "of", "for", "and", "or", "to", "with"}
    words = [w for w in words if w not in stopwords]
    words.sort()  # Sıralayarak aynı terimlerin aynı hash'i üretmesini sağla
    return " ".join(words)
```

### 2.8 — Dead Code Temizliği (Sorun 2.3)

**Dosya:** [service.py](file:///c:/Users/unala/projects/MedicaLLM/backend/src/pubmed/service.py)

`compute_confidence_scores()` içindeki batch efetch bloğunu kaldır (L582-584). `search_pubmed()` zaten `publication_types` döndürüyor, tekrar çekmek gereksiz.

Ayrıca `fetch_publication_types()` tek-PMID fonksiyonu da kaldırılabilir (artık batch ile çekiliyor).

### 2.9 — Streaming'de Tool Result Biriktirme (Sorun 4.2)

**Dosya:** [session.py](file:///c:/Users/unala/projects/MedicaLLM/backend/src/agent/session.py)

Mevcut kod sadece ilk tool sonucunu kaydediyor. Tüm tool sonuçlarını biriktir:

```python
# Mevcut (hatalı):
tool_result = None
# ...
if not tool_result:
    tool_result = data.get("output")

# Yeni (düzeltilmiş):
tool_results = []  # Liste olarak biriktir
tool_names = []    # Hangi tool'lar çağrıldı
# ...
elif event_type == "on_tool_end":
    data = event.get("data", {})
    output = data.get("output")
    if output:
        tool_results.append(output)
```

---

## Faz 3 — System Prompt & Frontend Temizliği

### 3.1 — System Prompt Güncelle
**Dosya:** [agent.py](file:///c:/Users/unala/projects/MedicaLLM/backend/src/agent/agent.py)

- `search_medical_documents` referanslarını kaldır
- Tool listesinden 5 numarayı çıkar (7 tool kalacak)
- PubMed tool talimatını güçlendir:

```
6. **search_pubmed** - Search PubMed for medical research. 
   CRITICAL: Always convert the user's query to English medical terminology before calling this tool.
   Use MeSH terms when possible. Default: 5 articles.
   In your response, cite articles by their REF number (e.g., "According to REF1...").
   Only cite articles you actually used in your answer.
```

- Multi-tool flow örneklerinden `search_medical_documents` olanları güncelle
- Source talimatını netleştir:

```
When citing PubMed articles, use the REF numbers provided (e.g., "A meta-analysis [REF1] found that...").
Only articles you explicitly reference will be shown as sources to the user.
```

### 3.2 — Frontend: Sadece Kullanılan Kaynakları Göster
**Dosya:** [Chat.jsx](file:///c:/Users/unala/projects/MedicaLLM/frontend/src/pages/Chat.jsx)

LLM cevabında geçen REF numaralarını parse ederek yalnızca kullanılan kaynakları göster:

```javascript
// Cevaptaki REF numaralarını bul
const usedRefs = new Set();
const refPattern = /REF(\d+)/g;
let match;
while ((match = refPattern.exec(msg.content)) !== null) {
  usedRefs.add(parseInt(match[1]));
}

// Sadece kullanılan kaynakları filtrele
const filteredSources = msg.sources?.filter((_, idx) => usedRefs.has(idx + 1)) || msg.sources;
```

### 3.3 — Kullanılmayan Dosyaları Temizle

| Dosya | Eylem |
|-------|-------|
| `backend/src/rag/vector_store.py` | Sil |
| `backend/src/rag/pdf_processor.py` | Sil |
| `backend/src/rag/router.py` | Sil |
| `backend/chromadb-data/` | Sil + `.gitignore`'a ekle |
| `backend/src/db/sql_models.py` → `PubmedIndexed`, `PubmedPdfIndexed` | Kaldır |
| `backend/src/pubmed/service.py` → PDF fonksiyonları | Sil |
| `backend/src/pubmed/service.py` → `fetch_publication_types()` tek-PMID | Sil (dead code) |

### 3.4 — Model Kapasitesi Önerisi (Sorun 5.2)

> [!IMPORTANT]
> `.env` dosyasında `DO_AI_MODEL=openai-gpt-oss-20b` kullanılıyor. Tıbbi sentezleme ve çoklu kaynak karşılaştırması için daha güçlü model önerilir.

**Önerilen değişiklik:**
```env
# .env
DO_AI_MODEL=openai-gpt-oss-120b  # 20b → 120b
```

Bu değişiklik:
- Daha iyi Türkçe→İngilizce çeviri
- Daha doğru kaynak sentezleme
- Daha az halüsinasyon
- REF numaralarını daha tutarlı kullanma

---

## Verification Plan

### Otomatik Test
```bash
# Backend'in hatasız başladığını doğrula
cd backend && python -c "from src.agent.tools import ALL_TOOLS; print(f'{len(ALL_TOOLS)} tools loaded')"

# PubMed aramasının çalıştığını doğrula  
cd backend && python -c "from src.pubmed.service import search_pubmed; r = search_pubmed('SGLT2 inhibitors heart failure', 3); print(f'{len(r)} articles found')"
```

### Manuel Test (Browser)
1. **Türkçe sorgu testi:** "Kalp yetmezliğinde SGLT2 inhibitörleri"
   - ✅ LLM'in İngilizce PubMed sorgusu oluşturduğunu doğrula (Sorun 2.1)
   - ✅ Dönen makalelerin alakalı olduğunu kontrol et
   - ✅ Source listesinin cevapla uyumlu olduğunu kontrol et (Sorun 1.1)

2. **Confidence score testi:** "Recent studies on metformin and longevity"
   - ✅ "Journal Article" → 0.5 aldığını kontrol et (Sorun 3.3)
   - ✅ Citation normalizasyonunun global olduğunu doğrula (Sorun 3.2)
   - ✅ Relevance'ın keyword overlap ile hesaplandığını doğrula (Sorun 3.1)

3. **Çoklu tool testi:** "Warfarin ile ibuprofen etkileşir mi?"
   - ✅ Kaynaklar tool bazında ayrışmalı (Sorun 1.2)
   - ✅ Streaming'de tüm tool sonuçları biriktirilmeli (Sorun 4.2)

4. **Context window testi:** 20 makale isteyen sorgu
   - ✅ Max 20 ile sınırlı (Sorun 5.1)
   - ✅ REF numaralarıyla sadece kullanılan kaynaklar gösterilmeli (Sorun 1.1)

5. **Cache testi:** Aynı konuyu farklı kelime sıralamasıyla sor
   - ✅ Aynı cache'e hit etmeli (Sorun 2.2)

---

## Özet: Yeni Tool Listesi (7 tool)

| # | Tool | Kaynak |
|---|------|--------|
| 1 | `get_drug_info` | PostgreSQL (DrugBank) |
| 2 | `check_drug_interaction` | PostgreSQL (DrugBank) |
| 3 | `check_drug_food_interaction` | PostgreSQL (DrugBank) |
| 4 | `search_drugs_by_indication` | PostgreSQL (DrugBank) |
| 5 | **`search_pubmed`** ← geliştirilmiş | PubMed API (canlı) |
| 6 | `recommend_alternative_drug` | PostgreSQL (DrugBank) |
| 7 | `analyze_patient_medications` | DynamoDB + PostgreSQL |

> [!IMPORTANT]
> `search_medical_documents` kaldırılıyor. Tüm araştırma sorguları doğrudan PubMed API üzerinden cevaplanacak.
