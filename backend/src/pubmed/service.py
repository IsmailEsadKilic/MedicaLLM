"""
PubMed search service using NCBI E-utilities API.

Provides relevance-ranked article search with confidence scoring.
"""
import time
import urllib.request
import urllib.parse
import urllib.error
import json
import xml.etree.ElementTree as ET
from typing import Optional
from logging import getLogger

from .models import PubMedArticle, PubMedSearchResult
from .scoring import compute_confidence_score, get_quality_warnings
from ..config import settings

logger = getLogger(__name__)


# ============================================================================
# PubMed Search
# ============================================================================

def search_pubmed(
    query: str,
    max_results: int = 10,
    min_confidence: float = 35.0,
) -> PubMedSearchResult:
    """
    Search PubMed using NCBI E-utilities with relevance ranking.
    
    Args:
        query: Search query string
        max_results: Maximum number of articles to retrieve (before filtering)
        min_confidence: Minimum confidence score to include (0-100)
    
    Returns:
        PubMedSearchResult with articles sorted by confidence score
    """
    start_time = time.time()
    
    logger.info(f"[PUBMED] PubMed search: '{query}' (max_results={max_results}, min_confidence={min_confidence})")
    logger.debug(f"[PUBMED] Query length: {len(query)} chars")
    
    # Build API parameters
    api_key_param = f"&api_key={settings.ncbi_api_key}" if settings.ncbi_api_key else ""
    base_headers = {
        "User-Agent": f"{settings.pubmed_tool_name}/1.0 ({settings.pubmed_email})"
    }
    logger.debug(f"[PUBMED] Using API key: {bool(settings.ncbi_api_key)}")
    
    try:
        # Step 1: esearch — get PMIDs sorted by relevance
        logger.debug(f"[PUBMED] Step 1: Executing esearch")
        esearch_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pubmed&term={urllib.parse.quote(query)}&retmax={max_results}"
            f"&sort=relevance&retmode=json"
            f"&tool={urllib.parse.quote(settings.pubmed_tool_name)}"
            f"&email={urllib.parse.quote(settings.pubmed_email)}{api_key_param}"
        )
        
        logger.debug(f"[PUBMED] esearch URL: {esearch_url[:200]}...")
        req = urllib.request.Request(esearch_url, headers=base_headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            search_data = json.loads(resp.read().decode())
        
        pmids = search_data.get("esearchresult", {}).get("idlist", [])
        total_found = int(search_data.get("esearchresult", {}).get("count", 0))
        
        logger.info(f"[PUBMED] esearch found {total_found} total articles, retrieved {len(pmids)} PMIDs")
        logger.debug(f"[PUBMED] PMIDs: {pmids}")
        
        if not pmids:
            logger.info("[PUBMED] No PubMed results found")
            return PubMedSearchResult(
                query=query,
                articles=[],
                total_found=0,
                search_time_ms=round((time.time() - start_time) * 1000, 2),
            )
        
        logger.debug(f"[PUBMED] Step 2: Fetching article details with efetch")
        
        # Step 2: efetch — get article details as XML
        efetch_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            f"?db=pubmed&id={','.join(pmids)}&retmode=xml"
            f"&tool={urllib.parse.quote(settings.pubmed_tool_name)}"
            f"&email={urllib.parse.quote(settings.pubmed_email)}{api_key_param}"
        )
        
        logger.debug(f"[PUBMED] efetch URL: {efetch_url[:200]}...")
        req = urllib.request.Request(efetch_url, headers=base_headers)
        with urllib.request.urlopen(req, timeout=20) as resp:
            root = ET.fromstring(resp.read().decode())
        
        logger.debug(f"[PUBMED] Step 3: Parsing XML articles")
        
        # Step 3: Parse articles
        articles = []
        for article_elem in root.findall(".//PubmedArticle"):
            try:
                article = _parse_article_xml(article_elem, query)
                if article:
                    articles.append(article)
                    logger.debug(f"[PUBMED] Parsed article: PMID {article.pmid}, confidence: {article.confidence_score:.1f}")
            except Exception as e:
                logger.warning(f"[PUBMED] Failed to parse article: {e}")
        
        logger.info(f"[PUBMED] Successfully parsed {len(articles)} articles")
        
        # Step 4: Filter by confidence threshold
        logger.debug(f"[PUBMED] Step 4: Filtering by confidence >= {min_confidence}")
        filtered_articles = [a for a in articles if a.confidence_score >= min_confidence]
        filtered_count = len(articles) - len(filtered_articles)
        
        if filtered_count > 0:
            logger.info(f"[PUBMED] Filtered {filtered_count} articles below {min_confidence} confidence")
        
        # Step 5: Sort by confidence (highest first)
        filtered_articles.sort(key=lambda a: a.confidence_score, reverse=True)
        logger.debug(f"[PUBMED] Sorted {len(filtered_articles)} articles by confidence")
        
        # Calculate average confidence
        avg_confidence = (
            sum(a.confidence_score for a in filtered_articles) / len(filtered_articles)
            if filtered_articles else 0.0
        )
        
        search_time_ms = round((time.time() - start_time) * 1000, 2)
        
        logger.info(
            f"[PUBMED] Retrieved {len(filtered_articles)} articles "
            f"(avg confidence: {avg_confidence:.1f}) in {search_time_ms}ms"
        )
        
        return PubMedSearchResult(
            query=query,
            articles=filtered_articles,
            total_found=total_found,
            search_time_ms=search_time_ms,
            avg_confidence=round(avg_confidence, 1),
            filtered_count=filtered_count,
        )
    
    except Exception as e:
        logger.error(f"[PUBMED] PubMed search failed for '{query}': {e}", exc_info=True)
        return PubMedSearchResult(
            query=query,
            articles=[],
            total_found=0,
            search_time_ms=round((time.time() - start_time) * 1000, 2),
        )


def _parse_article_xml(article_elem: ET.Element, query: str) -> Optional[PubMedArticle]:
    """Parse a single PubmedArticle XML element into a PubMedArticle model."""
    
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
    
    # DOI and PMC ID
    doi = ""
    pmc_id = ""
    for eid in article_elem.findall(".//ArticleId"):
        id_type = eid.get("IdType")
        if id_type == "doi" and eid.text:
            doi = eid.text.strip()
        elif id_type == "pmc" and eid.text:
            pmc_id = eid.text.strip()  # e.g., "PMC7234567"
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
                month_map = {
                    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
                    "may": "05", "jun": "06", "jul": "07", "aug": "08",
                    "sep": "09", "oct": "10", "nov": "11", "dec": "12"
                }
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
    
    # Publication types
    pub_types = []
    for pt in article_elem.findall(".//PublicationType"):
        if pt.text:
            pub_types.append(pt.text.strip())
    
    # Skip if no essential data
    if not pmid and not title:
        return None
    
    # Compute confidence score - fetch citation count from Semantic Scholar
    citation_count = 0
    try:
        import urllib.request
        import json
        import time
        
        # Add small delay to avoid rate limiting (Semantic Scholar allows ~1 req/sec)
        time.sleep(0.15)  # 150ms delay between requests
        
        # Use the newer Semantic Scholar API endpoint with better reliability
        url = f"https://api.semanticscholar.org/graph/v1/paper/PMID:{pmid}?fields=citationCount"
        req = urllib.request.Request(
            url, 
            headers={
                "User-Agent": "MedicaLLM/1.0",
                "Accept": "application/json"
            }
        )
        with urllib.request.urlopen(req, timeout=5) as response:  # Increased from 3 to 5 seconds
            data = json.loads(response.read())
            citation_count = data.get("citationCount", 0) or 0
            logger.debug(f"[PUBMED] PMID {pmid} citation count: {citation_count}")
    except Exception as e:
        logger.warning(f"[PUBMED] Failed to fetch citation count for PMID {pmid}: {e}")
        pass  # Silently fail, use 0
    
    confidence, breakdown = compute_confidence_score(
        citation_count=citation_count,
        publication_date=pub_date,
        publication_types=pub_types,
        query=query,
        title=title,
        abstract=abstract,
    )
    
    return PubMedArticle(
        pmid=pmid,
        title=title,
        abstract=abstract,
        authors=authors,
        journal=journal,
        publication_date=pub_date,
        doi=doi,
        pmc_id=pmc_id,
        publication_types=pub_types,
        citation_count=citation_count,
        confidence_score=confidence,
        confidence_breakdown=breakdown,
        relevance_score=breakdown.get("relevance", 0.0) / 100.0,
    )


# ============================================================================
# Helper Functions
# ============================================================================

def extract_relevant_snippet(query: str, abstract: str, max_len: int = 400) -> str:
    """
    Extract the most query-relevant sentences from an abstract.
    
    Useful for creating concise source citations.
    """
    if not abstract:
        return ""
    
    sentences = abstract.replace(". ", ".\n").split("\n")
    query_terms = set(query.lower().split())
    
    # Remove stopwords
    stopwords = {"the", "a", "an", "in", "on", "of", "for", "and", "or", "to", "with"}
    query_terms -= stopwords
    
    # Score sentences by query term overlap
    scored = []
    for sent in sentences:
        overlap = sum(1 for t in query_terms if t in sent.lower())
        scored.append((overlap, sent.strip()))
    
    scored.sort(key=lambda x: x[0], reverse=True)
    
    # Build snippet up to max_len
    result = ""
    for _, sent in scored:
        if len(result) + len(sent) + 2 <= max_len:
            result += sent + " "
        else:
            break
    
    return result.strip() or abstract[:max_len]
