
#aig
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
from ....legacy import printmeup as pm

#section: PubMed Search

def search_pubmed(query: str, max_results: int = settings.pubmed_max_results) -> list[dict]:
    """
    Search PubMed using NCBI E-utilities with score sorting.
    
    Uses esearch + efetch instead of pymed to get relevance-ranked results
    (PubMed's "Best Match" algorithm) rather than most-recent-first.
    """
    pm.deb(f"Searching PubMed for: '{query}' (max_results={max_results})")

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

        pm.deb(f"Found {len(pmids)} PMIDs, fetching details...")

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
    """
    Score from 0.0 to 1.0 based on how recent the article is.
    
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
    """
    Compute semantic relevance between query and article.
    
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
    """
    Compute a composite confidence score for each article.
    
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
    """
    Fetch citation counts for multiple PMIDs in parallel using ThreadPoolExecutor.
    
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
