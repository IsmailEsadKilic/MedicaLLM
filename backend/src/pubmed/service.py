import hashlib
import os
import time
import urllib.request
import urllib.parse
import urllib.error
import json
from datetime import datetime, timezone
from typing import Optional

from pymed import PubMed

from ..db.sql_client import get_session
from ..db.sql_models import PubmedCache, PubmedIndexed, PubmedCitation, PubmedPdfIndexed
from ..config import settings
from .. import printmeup as pm


def _normalize_query(query: str) -> str:
    return query.strip().lower()


def _query_hash(query: str) -> str:
    normalized = _normalize_query(query)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


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
            import xml.etree.ElementTree as ET
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

                if not pmid and not title:
                    continue

                articles.append({
                    "pmid": pmid, "title": title, "abstract": abstract,
                    "authors": authors, "journal": journal,
                    "publication_date": pub_date, "doi": doi,
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


def is_pmid_indexed(pmid: str) -> bool:
    session = get_session()
    try:
        return session.query(PubmedIndexed).filter(PubmedIndexed.pmid == pmid).first() is not None
    except Exception:
        return False
    finally:
        session.close()


def mark_pmid_indexed(pmid: str, title: str):
    session = get_session()
    try:
        rec = session.query(PubmedIndexed).filter(PubmedIndexed.pmid == pmid).first()
        if not rec:
            session.add(PubmedIndexed(pmid=pmid, title=title,
                                      indexed_at=datetime.now(timezone.utc).isoformat()))
            session.commit()
    except Exception as e:
        session.rollback()
        pm.war(f"Failed to mark PMID {pmid} as indexed: {e}")
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


# ========================================================================
# PMC Full-Text PDF Download
# ========================================================================

_ELINK_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
    "?dbfrom=pubmed&db=pmc&id={pmid}&retmode=json&tool={tool}&email={email}{api_key}"
)
_PMC_PDF_URL = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmcid}/pdf/"


def fetch_pmcid(pmid: str) -> Optional[str]:
    api_key_param = f"&api_key={settings.ncbi_api_key}" if settings.ncbi_api_key else ""
    url = _ELINK_URL.format(
        pmid=pmid, tool=urllib.parse.quote(settings.pubmed_tool_name),
        email=urllib.parse.quote(settings.pubmed_email), api_key=api_key_param,
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": f"{settings.pubmed_tool_name}/1.0 ({settings.pubmed_email})"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
        for link_set in data.get("linksets", []):
            for link_set_db in link_set.get("linksetdbs", []):
                if link_set_db.get("dbto") == "pmc":
                    ids = link_set_db.get("links", [])
                    if ids:
                        return str(ids[0])
        return None
    except Exception as e:
        pm.war(f"NCBI elink failed for PMID {pmid}: {e}")
        return None


def download_pmc_pdf(pmid: str, pmcid: str, output_dir: str) -> Optional[str]:
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"pmid_{pmid}.pdf")
    if os.path.exists(pdf_path):
        return pdf_path
    url = _PMC_PDF_URL.format(pmcid=pmcid)
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": f"{settings.pubmed_tool_name}/1.0 ({settings.pubmed_email})",
            "Accept": "application/pdf,*/*",
        })
        with urllib.request.urlopen(req, timeout=30) as resp:
            if "pdf" not in resp.headers.get("Content-Type", "").lower():
                return None
            with open(pdf_path, "wb") as f:
                f.write(resp.read())
        pm.suc(f"Downloaded PDF for PMID {pmid} → {pdf_path}")
        return pdf_path
    except urllib.error.HTTPError as e:
        if e.code not in (403, 404):
            pm.war(f"PDF download HTTP {e.code} for PMID {pmid}")
        return None
    except Exception as e:
        pm.war(f"PDF download failed for PMID {pmid}: {e}")
        return None


def is_pmid_pdf_indexed(pmid: str) -> bool:
    session = get_session()
    try:
        return session.query(PubmedPdfIndexed).filter(PubmedPdfIndexed.pmid == pmid).first() is not None
    except Exception:
        return False
    finally:
        session.close()


def mark_pmid_pdf_indexed(pmid: str, title: str, pdf_path: str) -> None:
    session = get_session()
    try:
        rec = session.query(PubmedPdfIndexed).filter(PubmedPdfIndexed.pmid == pmid).first()
        if not rec:
            session.add(PubmedPdfIndexed(pmid=pmid, title=title, pdf_path=pdf_path,
                                         indexed_at=datetime.now(timezone.utc).isoformat()))
            session.commit()
    except Exception as e:
        session.rollback()
        pm.war(f"Failed to mark PDF indexed for PMID {pmid}: {e}")
    finally:
        session.close()


def enrich_articles_with_full_text(articles: list[dict], vector_store_manager, pdf_processor) -> list[dict]:
    output_dir = settings.pubmed_pdf_subdir
    for article in articles:
        pmid = article.get("pmid", "")
        title = article.get("title", "")
        article["has_full_text"] = False
        if not pmid:
            continue
        if is_pmid_pdf_indexed(pmid):
            article["has_full_text"] = True
            continue
        pmcid = fetch_pmcid(pmid)
        if not pmcid:
            continue
        pdf_path = download_pmc_pdf(pmid, pmcid, output_dir)
        if not pdf_path:
            continue
        try:
            pages = pdf_processor.load_single_pdf(pdf_path)
            for page in pages:
                page.metadata.setdefault("source", f"PubMed:{pmid}")
                page.metadata.setdefault("pmid", pmid)
                page.metadata.setdefault("title", title)
                page.metadata.setdefault("file_name", os.path.basename(pdf_path))
            chunks = pdf_processor.split_documents(pages)
            if vector_store_manager.add_documents(chunks):
                mark_pmid_pdf_indexed(pmid, title, pdf_path)
                article["has_full_text"] = True
                pm.suc(f"Full-text PDF indexed for PMID {pmid} ({len(chunks)} chunks)")
        except Exception as e:
            pm.war(f"Failed to index PDF for PMID {pmid}: {e}")
    return articles


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
# Publication Type / Evidence Level (via NCBI E-utilities)
# ========================================================================

_EFETCH_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
    "?db=pubmed&id={pmid}&retmode=xml&tool={tool}&email={email}{api_key}"
)

# Evidence hierarchy — higher = stronger evidence
_EVIDENCE_LEVELS = {
    "meta-analysis": 1.0,
    "systematic review": 0.9,
    "randomized controlled trial": 0.85,
    "clinical trial": 0.75,
    "controlled clinical trial": 0.75,
    "comparative study": 0.6,
    "multicenter study": 0.6,
    "cohort study": 0.55,
    "observational study": 0.5,
    "case-control study": 0.45,
    "case reports": 0.3,
    "review": 0.4,
    "editorial": 0.15,
    "comment": 0.1,
    "letter": 0.1,
}


def fetch_publication_types(pmid: str) -> list[str]:
    """Fetch publication types for a PMID from NCBI E-utilities."""
    api_key_param = f"&api_key={settings.ncbi_api_key}" if settings.ncbi_api_key else ""
    url = _EFETCH_URL.format(
        pmid=pmid, tool=urllib.parse.quote(settings.pubmed_tool_name),
        email=urllib.parse.quote(settings.pubmed_email), api_key=api_key_param,
    )
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": f"{settings.pubmed_tool_name}/1.0 ({settings.pubmed_email})"
        })
        with urllib.request.urlopen(req, timeout=10) as resp:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(resp.read().decode())
            pub_types = []
            for pt in root.iter("PublicationType"):
                if pt.text:
                    pub_types.append(pt.text.strip())
            return pub_types
    except Exception as e:
        pm.war(f"Failed to fetch publication types for PMID {pmid}: {e}")
        return []
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
_W_CITATIONS = 0.35
_W_RECENCY = 0.25
_W_EVIDENCE = 0.30
_W_RELEVANCE = 0.10


def _normalize_citations(citation_count: int, max_citations: int) -> float:
    """Normalize citation count to 0.0 - 1.0 using log scale."""
    if max_citations <= 0 or citation_count <= 0:
        return 0.0
    import math
    return min(math.log1p(citation_count) / math.log1p(max_citations), 1.0)


def compute_confidence_scores(articles: list[dict], query: str = "", vector_store_manager=None) -> list[dict]:
    """Compute a composite confidence score for each article.
    
    Score = weighted combination of:
      - Normalized citation count (log-scaled)
      - Recency score (linear decay over 20 years)
      - Evidence level (publication type hierarchy)
      - Relevance score (Chroma similarity when available, 0.5 default)
    
    Each article gets a 'confidence_score' (0-100) and 'confidence_breakdown' dict.
    """
    if not articles:
        return articles

    # Compute relevance scores via Chroma similarity if available
    relevance_map: dict[str, float] = {}
    if query and vector_store_manager:
        try:
            results = vector_store_manager.vectorstore.similarity_search_with_relevance_scores(query, k=20)
            for doc, score in results:
                pmid = doc.metadata.get("pmid", "")
                if pmid and pmid not in relevance_map:
                    # Chroma scores can vary; normalize to 0-1
                    relevance_map[pmid] = max(0.0, min(1.0, score))
        except Exception as e:
            pm.war(f"Relevance scoring failed: {e}")

    # Find max citations for normalization
    max_cites = max((a.get("citation_count", 0) for a in articles), default=1)

    # Batch-fetch publication types for all articles in one call
    pmids_needing_types = [a.get("pmid", "") for a in articles 
                           if a.get("pmid") and a.get("publication_types") is None]
    pub_types_map = fetch_publication_types_batch(pmids_needing_types) if pmids_needing_types else {}

    for article in articles:
        pmid = article.get("pmid", "")
        
        # Citation score (normalized)
        cite_score = _normalize_citations(article.get("citation_count", 0), max_cites)
        
        # Recency score
        recency = get_recency_score(article.get("publication_date", ""))
        
        # Evidence level (use batch-fetched types)
        pub_types = article.get("publication_types")
        if pub_types is None and pmid:
            pub_types = pub_types_map.get(pmid, [])
            article["publication_types"] = pub_types
        evidence = get_evidence_score(pub_types or [])
        
        # Relevance score (from Chroma similarity if available)
        pmid = article.get("pmid", "")
        relevance = relevance_map.get(pmid, 0.5)
        
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
            "publication_types": pub_types or [],
        }
    
    return articles


def sort_articles_by_confidence(articles: list[dict]) -> list[dict]:
    """Sort articles by composite confidence score (highest first)."""
    return sorted(articles, key=lambda a: a.get("confidence_score", 0), reverse=True)


def fetch_publication_types_batch(pmids: list[str]) -> dict[str, list[str]]:
    """Fetch publication types for multiple PMIDs in a single NCBI efetch call.
    
    Returns a dict mapping PMID → list of publication type strings.
    """
    if not pmids:
        return {}
    
    import xml.etree.ElementTree as ET
    api_key_param = f"&api_key={settings.ncbi_api_key}" if settings.ncbi_api_key else ""
    url = (
        f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        f"?db=pubmed&id={','.join(pmids)}&retmode=xml"
        f"&tool={urllib.parse.quote(settings.pubmed_tool_name)}"
        f"&email={urllib.parse.quote(settings.pubmed_email)}{api_key_param}"
    )
    try:
        req = urllib.request.Request(url, headers={
            "User-Agent": f"{settings.pubmed_tool_name}/1.0 ({settings.pubmed_email})"
        })
        with urllib.request.urlopen(req, timeout=15) as resp:
            root = ET.fromstring(resp.read().decode())
        
        result: dict[str, list[str]] = {}
        for article_elem in root.findall(".//PubmedArticle"):
            pmid_elem = article_elem.find(".//PMID")
            if pmid_elem is None or not pmid_elem.text:
                continue
            pmid = pmid_elem.text.strip()
            pub_types = []
            for pt in article_elem.findall(".//PublicationType"):
                if pt.text:
                    pub_types.append(pt.text.strip())
            result[pmid] = pub_types
        
        pm.inf(f"Batch-fetched publication types for {len(result)} articles")
        return result
    except Exception as e:
        pm.war(f"Batch publication type fetch failed: {e}")
        return {}


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
