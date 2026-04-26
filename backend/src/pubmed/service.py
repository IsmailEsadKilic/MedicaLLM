import hashlib
import math
import time
import urllib.request
import urllib.parse
import urllib.error
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from typing import Optional

from ..db.sql_client import get_session
from ..db.sql_models import PubmedCache, PubmedCitation
from ..config import settings
from .. import printmeup as pm


def _normalize_query(query: str) -> str:
    """Order-independent query normalization for cache key generation."""
    words = query.strip().lower().split()
    stopwords = {"the", "a", "an", "in", "on", "of", "for", "and", "or", "to", "with"}
    words = [w for w in words if w not in stopwords]
    words.sort()
    return " ".join(words)


# Bump this version whenever scoring/filtering logic changes to invalidate
# stale cached results that were scored with a previous algorithm.
_CACHE_VERSION = "v2"


def _query_hash(query: str) -> str:
    normalized = _normalize_query(query)
    raw = f"{_CACHE_VERSION}:{normalized}"
    return hashlib.sha256(raw.encode()).hexdigest()[:16]


# ========================================================================
# PubMed Search
# ========================================================================

def search_pubmed(query: str, max_results: int = settings.pubmed_max_results) -> list[dict]:
    """Search PubMed using NCBI E-utilities with relevance sorting.
    
    Uses esearch + efetch instead of pymed to get relevance-ranked results
    (PubMed's "Best Match" algorithm) rather than most-recent-first.
    """
    pm.inf(f"Searching PubMed for: '{query}' (max_results={max_results})")

    api_key_param = f"&api_key={settings.ncbi_api_key}" if settings.ncbi_api_key else ""
    base_headers = {"User-Agent": f"{settings.pubmed_tool_name}/1.0 ({settings.pubmed_email})"}

    try:
        # Step 1: esearch — get PMIDs sorted by relevance
        esearch_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pubmed&term={urllib.parse.quote(query)}&retmax={max_results}"
            f"&sort=relevance&retmode=json"
            f"&tool={urllib.parse.quote(settings.pubmed_tool_name)}"
            f"&email={urllib.parse.quote(settings.pubmed_email)}{api_key_param}"
        )
        req = urllib.request.Request(esearch_url, headers=base_headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            search_data = json.loads(resp.read().decode())

        pmids = search_data.get("esearchresult", {}).get("idlist", [])
        if not pmids:
            pm.inf("No PubMed results found")
            return []

        pm.inf(f"Found {len(pmids)} PMIDs, fetching details...")

        # Step 2: efetch — get article details as XML
        efetch_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            f"?db=pubmed&id={','.join(pmids)}&retmode=xml"
            f"&tool={urllib.parse.quote(settings.pubmed_tool_name)}"
            f"&email={urllib.parse.quote(settings.pubmed_email)}{api_key_param}"
        )
        req = urllib.request.Request(efetch_url, headers=base_headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            root = ET.fromstring(resp.read().decode())

        articles = []
        for article_elem in root.findall(".//PubmedArticle"):
            try:
                # PMID
                pmid_elem = article_elem.find(".//PMID")
                pmid = pmid_elem.text.strip() if pmid_elem is not None and pmid_elem.text else ""

                # Title
                title_elem = article_elem.find(".//ArticleTitle")
                title = title_elem.text.strip() if title_elem is not None and title_elem.text else ""

                # Abstract
                abstract_parts = []
                for abs_text in article_elem.findall(".//AbstractText"):
                    label = abs_text.get("Label", "")
                    text = "".join(abs_text.itertext()).strip()
                    if label and text:
                        abstract_parts.append(f"{label}: {text}")
                    elif text:
                        abstract_parts.append(text)
                abstract = "\n".join(abstract_parts)

                # Journal
                journal_elem = article_elem.find(".//Journal/Title")
                journal = journal_elem.text.strip() if journal_elem is not None and journal_elem.text else ""

                # DOI
                doi = ""
                for eid in article_elem.findall(".//ArticleId"):
                    if eid.get("IdType") == "doi" and eid.text:
                        doi = eid.text.strip()
                        break

                # Publication date
                pub_date = ""
                date_elem = article_elem.find(".//PubDate")
                if date_elem is not None:
                    y = date_elem.findtext("Year", "")
                    m = date_elem.findtext("Month", "")
                    d = date_elem.findtext("Day", "")
                    if y:
                        pub_date = y
                        if m:
                            # Convert month name to number if needed
                            month_map = {"jan":"01","feb":"02","mar":"03","apr":"04","may":"05","jun":"06",
                                         "jul":"07","aug":"08","sep":"09","oct":"10","nov":"11","dec":"12"}
                            m_num = month_map.get(m.lower()[:3], m.zfill(2))
                            pub_date = f"{y}-{m_num}"
                            if d:
                                pub_date = f"{y}-{m_num}-{d.zfill(2)}"

                # Authors
                authors = []
                for author in article_elem.findall(".//Author"):
                    last = author.findtext("LastName", "")
                    first = author.findtext("ForeName", "")
                    name = f"{first} {last}".strip()
                    if name:
                        authors.append(name)

                # Publication types (extract here to avoid redundant efetch later)
                pub_types = []
                for pt in article_elem.findall(".//PublicationType"):
                    if pt.text:
                        pub_types.append(pt.text.strip())

                if not pmid and not title:
                    continue

                articles.append({
                    "pmid": pmid, "title": title, "abstract": abstract,
                    "authors": authors, "journal": journal,
                    "publication_date": pub_date, "doi": doi,
                    "publication_types": pub_types,
                })
            except Exception as e:
                pm.war(f"Failed to parse article: {e}")

        pm.suc(f"Found {len(articles)} PubMed articles (relevance-sorted)")
        return articles

    except Exception as e:
        pm.err(e=e, m=f"PubMed search failed for '{query}'")
        return []


# ========================================================================
# PostgreSQL Cache
# ========================================================================

def get_cached_results(query: str) -> Optional[list[dict]]:
    query_key = _query_hash(query)
    session = get_session()
    try:
        rec = session.query(PubmedCache).filter(PubmedCache.query_hash == query_key).first()
        if not rec:
            return None
        # Check TTL — expire stale search results so newer research surfaces
        if rec.cached_at:
            try:
                cached_dt = datetime.fromisoformat(rec.cached_at)
                age_seconds = (datetime.now(timezone.utc) - cached_dt).total_seconds()
                if age_seconds > settings.pubmed_search_cache_ttl_seconds:
                    pm.inf(f"Cache expired for query '{query}' (age={age_seconds/3600:.0f}h)")
                    return None
            except (ValueError, TypeError):
                pass  # If cached_at is unparseable, use the cached data
        articles = json.loads(rec.articles) if rec.articles else []
        if not articles:
            return None
        pm.inf(f"Cache hit for query '{query}' ({len(articles)} articles)")
        return articles
    except Exception as e:
        pm.war(f"Cache lookup failed: {e}")
        return None
    finally:
        session.close()


def cache_results(query: str, articles: list[dict]):
    query_key = _query_hash(query)
    session = get_session()
    try:
        rec = session.query(PubmedCache).filter(PubmedCache.query_hash == query_key).first()
        if rec:
            rec.articles = json.dumps(articles)
            rec.cached_at = datetime.now(timezone.utc).isoformat()
        else:
            session.add(PubmedCache(
                query_hash=query_key, query=_normalize_query(query),
                articles=json.dumps(articles),
                cached_at=datetime.now(timezone.utc).isoformat(),
            ))
        session.commit()
        pm.suc(f"Cached {len(articles)} articles for query '{query}'")
    except Exception as e:
        session.rollback()
        pm.war(f"Failed to cache results: {e}")
    finally:
        session.close()


# ========================================================================
# Citation Count — Semantic Scholar API
# ========================================================================

_SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/PMID:{pmid}?fields=citationCount"


def get_cached_citation(pmid: str) -> Optional[int]:
    session = get_session()
    try:
        rec = session.query(PubmedCitation).filter(PubmedCitation.pmid == pmid).first()
        if not rec:
            return None
        if rec.expires_at and rec.expires_at < int(time.time()):
            return None
        return rec.citation_count
    except Exception as e:
        pm.war(f"Citation cache lookup failed for PMID {pmid}: {e}")
        return None
    finally:
        session.close()


def cache_citation(pmid: str, count: int, title: str = "") -> None:
    expires_at = int(time.time()) + settings.pubmed_citation_ttl_seconds
    session = get_session()
    try:
        rec = session.query(PubmedCitation).filter(PubmedCitation.pmid == pmid).first()
        if rec:
            rec.citation_count = count
            rec.cached_at = datetime.now(timezone.utc).isoformat()
            rec.expires_at = expires_at
        else:
            session.add(PubmedCitation(
                pmid=pmid, citation_count=count, title=title,
                cached_at=datetime.now(timezone.utc).isoformat(), expires_at=expires_at,
            ))
        session.commit()
    except Exception as e:
        session.rollback()
        pm.war(f"Failed to cache citation count for PMID {pmid}: {e}")
    finally:
        session.close()


def fetch_citation_count(pmid: str) -> Optional[int]:
    url = _SEMANTIC_SCHOLAR_URL.format(pmid=pmid)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f"{settings.pubmed_tool_name}/1.0 ({settings.pubmed_email})"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            count = data.get("citationCount")
            return int(count) if count is not None else None
    except urllib.error.HTTPError as e:
        if e.code != 404:
            pm.war(f"Semantic Scholar HTTP {e.code} for PMID {pmid}")
        return None
    except Exception as e:
        pm.war(f"Citation fetch failed for PMID {pmid}: {e}")
        return None


def get_or_fetch_citation_count(pmid: str, title: str = "") -> int:
    cached = get_cached_citation(pmid)
    if cached is not None:
        return cached
    count = fetch_citation_count(pmid) or 0
    cache_citation(pmid, count, title)
    return count


def enrich_articles_with_citations(articles: list[dict]) -> list[dict]:
    """Enrich articles with citation counts using parallel fetching."""
    pmids = [a.get("pmid", "") for a in articles if a.get("pmid")]
    counts = fetch_citation_counts_parallel(pmids)
    for article in articles:
        pmid = article.get("pmid", "")
        article["citation_count"] = counts.get(pmid, 0) if pmid else 0
    return articles


def sort_articles_by_citations(articles: list[dict]) -> list[dict]:
    return sorted(articles, key=lambda a: a.get("citation_count", 0), reverse=True)


# ========================================================================
# Publication Type / Evidence Level
# ========================================================================

# Evidence hierarchy — higher = stronger evidence
_EVIDENCE_LEVELS = {
    "meta-analysis": 1.0,
    "systematic review": 0.9,
    "randomized controlled trial": 0.85,
    "clinical trial": 0.75,
    "controlled clinical trial": 0.75,
    "practice guideline": 0.7,
    "guideline": 0.7,
    "comparative study": 0.6,
    "multicenter study": 0.6,
    "cohort study": 0.55,
    "observational study": 0.5,
    "journal article": 0.5,
    "case-control study": 0.45,
    "review": 0.4,
    "case reports": 0.3,
    "editorial": 0.15,
    "comment": 0.1,
    "letter": 0.1,
    "preprint": 0.1,
}


# ========================================================================
# Recency Score
# ========================================================================

def get_recency_score(publication_date: str) -> float:
    """Score from 0.0 to 1.0 based on how recent the article is.
    
    Last 2 years = 1.0, decays linearly to 0.1 at 20+ years old.
    """
    if not publication_date:
        return 0.3
    try:
        from datetime import datetime
        pub_dt = None
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                pub_dt = datetime.strptime(publication_date.strip()[:10], fmt)
                break
            except ValueError:
                continue
        
        if pub_dt is None:
            return 0.3
        
        years_ago = (datetime.now() - pub_dt).days / 365.25
        if years_ago <= 2:
            return 1.0
        elif years_ago >= 20:
            return 0.1
        else:
            return 1.0 - (years_ago - 2) * (0.9 / 18)
    except Exception:
        return 0.3


# ========================================================================
# Composite Confidence Score
# ========================================================================

# Weights for each signal (must sum to 1.0)
_W_CITATIONS = 0.20
_W_RECENCY   = 0.20
_W_EVIDENCE  = 0.25
_W_RELEVANCE = 0.35


def _normalize_citations(citation_count: int, max_citations: int = 1000) -> float:
    """Global log-scale citation normalization. 1000 citations = 1.0."""
    if citation_count <= 0:
        return 0.0
    return min(math.log1p(citation_count) / math.log1p(max_citations), 1.0)


def _compute_keyword_relevance(query: str, title: str, abstract: str) -> float:
    """Compute semantic relevance between query and article.
    
    Title matches are weighted 3x more than abstract matches.
    Bigrams (consecutive word pairs) are checked in addition to unigrams.
    """
    stopwords = {"the", "a", "an", "in", "on", "of", "for", "and", "or", "to",
                 "with", "is", "are", "was", "were", "by", "from", "that", "this",
                 "be", "at", "it", "as", "do", "does", "did", "not", "no", "but",
                 "if", "its", "has", "have", "had", "may", "can", "will", "would",
                 "should", "could", "about", "between", "among", "into", "through"}
    
    query_words = [w for w in query.lower().split() if w not in stopwords]
    if not query_words:
        return 0.5
    
    title_lower = title.lower()
    abstract_lower = abstract.lower() if abstract else ""
    
    # Unigram scoring
    title_hits = sum(1 for t in query_words if t in title_lower)
    abstract_hits = sum(1 for t in query_words if t in abstract_lower)
    
    # Bigram scoring (consecutive word pairs from query)
    bigrams = [f"{query_words[i]} {query_words[i+1]}" for i in range(len(query_words) - 1)]
    bigram_title_hits = sum(1 for bg in bigrams if bg in title_lower) if bigrams else 0
    bigram_abstract_hits = sum(1 for bg in bigrams if bg in abstract_lower) if bigrams else 0
    
    n_terms = len(query_words)
    n_bigrams = max(len(bigrams), 1)
    
    # Title relevance (weighted 3x) + abstract relevance
    title_score = (title_hits / n_terms) * 0.7 + (bigram_title_hits / n_bigrams) * 0.3
    abstract_score = (abstract_hits / n_terms) * 0.7 + (bigram_abstract_hits / n_bigrams) * 0.3
    
    combined = title_score * 0.6 + abstract_score * 0.4
    return min(combined, 1.0)


def compute_confidence_scores(articles: list[dict], query: str = "") -> list[dict]:
    """Compute a composite confidence score for each article.
    
    Score = weighted combination of:
      - Normalized citation count (global log-scale, ref: 1000 citations)
      - Recency score (linear decay over 20 years)
      - Evidence level (publication type hierarchy)
      - Relevance score (keyword overlap with query)
    
    Each article gets a 'confidence_score' (0-100) and 'confidence_breakdown' dict.
    """
    if not articles:
        return articles

    for article in articles:
        pmid = article.get("pmid", "")
        title = article.get("title", "")
        abstract = article.get("abstract", "")
        
        # Citation score (global normalization)
        cite_score = _normalize_citations(article.get("citation_count", 0))
        
        # Recency score
        recency = get_recency_score(article.get("publication_date", ""))
        
        # Evidence level
        pub_types = article.get("publication_types") or []
        evidence = get_evidence_score(pub_types)
        
        # Relevance score (keyword overlap)
        relevance = _compute_keyword_relevance(query, title, abstract) if query else 0.5
        
        # Composite score
        raw_score = (
            _W_CITATIONS * cite_score +
            _W_RECENCY * recency +
            _W_EVIDENCE * evidence +
            _W_RELEVANCE * relevance
        )
        
        confidence = round(raw_score * 100, 1)
        
        article["confidence_score"] = confidence
        article["confidence_breakdown"] = {
            "citations": round(cite_score * 100, 1),
            "recency": round(recency * 100, 1),
            "evidence_level": round(evidence * 100, 1),
            "relevance": round(relevance * 100, 1),
            "publication_types": pub_types,
        }
    
    return articles


def sort_articles_by_confidence(articles: list[dict]) -> list[dict]:
    """Sort articles by composite confidence score (highest first)."""
    return sorted(articles, key=lambda a: a.get("confidence_score", 0), reverse=True)


def fetch_citation_counts_parallel(pmids: list[str]) -> dict[str, int]:
    """Fetch citation counts for multiple PMIDs in parallel using ThreadPoolExecutor.
    
    Returns a dict mapping PMID → citation count.
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    results: dict[str, int] = {}
    
    # Check cache first
    uncached: list[str] = []
    for pmid in pmids:
        cached = get_cached_citation(pmid)
        if cached is not None:
            results[pmid] = cached
        else:
            uncached.append(pmid)
    
    if not uncached:
        return results
    
    # Fetch uncached in parallel (max 5 concurrent to respect rate limits)
    def _fetch_one(pmid: str) -> tuple[str, int]:
        count = fetch_citation_count(pmid) or 0
        return pmid, count
    
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(_fetch_one, pmid): pmid for pmid in uncached}
        for future in as_completed(futures):
            try:
                pmid, count = future.result(timeout=10)
                results[pmid] = count
                # Cache for next time
                title = ""
                cache_citation(pmid, count, title)
            except Exception as e:
                pmid = futures[future]
                pm.war(f"Parallel citation fetch failed for {pmid}: {e}")
                results[pmid] = 0
    
    pm.inf(f"Fetched citation counts for {len(uncached)} articles in parallel")
    return results


def get_evidence_score(publication_types: list[str]) -> float:
    """Map publication types to an evidence level score (0.0 - 1.0)."""
    if not publication_types:
        return 0.3  # default for unknown
    best = 0.0
    for pt in publication_types:
        pt_lower = pt.lower()
        for key, score in _EVIDENCE_LEVELS.items():
            if key in pt_lower:
                best = max(best, score)
                break
    return best if best > 0 else 0.3
