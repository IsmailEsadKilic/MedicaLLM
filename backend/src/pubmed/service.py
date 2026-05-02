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
    
    logger.info(f"PubMed search: '{query}' (max_results={max_results})")
    
    # Build API parameters
    api_key_param = f"&api_key={settings.ncbi_api_key}" if settings.ncbi_api_key else ""
    base_headers = {
        "User-Agent": f"{settings.pubmed_tool_name}/1.0 ({settings.pubmed_email})"
    }
    
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
        total_found = int(search_data.get("esearchresult", {}).get("count", 0))
        
        if not pmids:
            logger.info("No PubMed results found")
            return PubMedSearchResult(
                query=query,
                articles=[],
                total_found=0,
                search_time_ms=round((time.time() - start_time) * 1000, 2),
            )
        
        logger.debug(f"Found {len(pmids)} PMIDs, fetching details...")
        
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
        
        # Step 3: Parse articles
        articles = []
        for article_elem in root.findall(".//PubmedArticle"):
            try:
                article = _parse_article_xml(article_elem, query)
                if article:
                    articles.append(article)
            except Exception as e:
                logger.warning(f"Failed to parse article: {e}")
        
        # Step 4: Filter by confidence threshold
        filtered_articles = [a for a in articles if a.confidence_score >= min_confidence]
        filtered_count = len(articles) - len(filtered_articles)
        
        if filtered_count > 0:
            logger.info(f"Filtered {filtered_count} articles below {min_confidence} confidence")
        
        # Step 5: Sort by confidence (highest first)
        filtered_articles.sort(key=lambda a: a.confidence_score, reverse=True)
        
        # Calculate average confidence
        avg_confidence = (
            sum(a.confidence_score for a in filtered_articles) / len(filtered_articles)
            if filtered_articles else 0.0
        )
        
        search_time_ms = round((time.time() - start_time) * 1000, 2)
        
        logger.info(
            f"Retrieved {len(filtered_articles)} articles "
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
        logger.error(f"PubMed search failed for '{query}': {e}", exc_info=True)
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
    
    # Compute confidence score
    citation_count = 0  # TODO: Implement citation fetching if needed
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
