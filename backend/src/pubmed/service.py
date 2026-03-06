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

from ..db.client import dynamodb_client
from ..config import settings
from .. import printmeup as pm


PUBMED_CACHE_TABLE = "PubMedCache"


def _cache_table():
    return dynamodb_client.Table(PUBMED_CACHE_TABLE)  # type: ignore


def _normalize_query(query: str) -> str:
    """Normalize a query string for consistent cache keys."""
    return query.strip().lower()


def _query_hash(query: str) -> str:
    """Create a short hash of the normalized query for the PK."""
    normalized = _normalize_query(query)
    return hashlib.sha256(normalized.encode()).hexdigest()[:16]


# ========================================================================
# PubMed Search
# ========================================================================


def search_pubmed(query: str, max_results: int = settings.pubmed_max_results) -> list[dict]:
    """
    Search PubMed for articles matching the query using pymed.

    Returns a list of dicts with: pmid, title, abstract, authors, journal, publication_date, doi
    """
    pm.inf(f"Searching PubMed for: '{query}' (max_results={max_results})")

    pubmed = PubMed(tool=settings.pubmed_tool_name, email=settings.pubmed_email)

    try:
        results = pubmed.query(query, max_results=max_results)
        articles = []

        for article in results:
            try:
                # Extract PMID
                pmid = getattr(article, "pubmed_id", "") or ""
                # pymed sometimes returns multiple IDs separated by newline
                pmid = pmid.strip().split("\n")[0].strip()

                title = getattr(article, "title", "") or ""
                abstract = getattr(article, "abstract", "") or ""
                journal = getattr(article, "journal", "") or ""
                doi = getattr(article, "doi", "") or ""
                publication_date = getattr(article, "publication_date", None)

                # Format authors
                authors_raw = getattr(article, "authors", []) or []
                authors = []
                for a in authors_raw:
                    if isinstance(a, dict):
                        name = f"{a.get('firstname', '')} {a.get('lastname', '')}".strip()
                        if name:
                            authors.append(name)
                    elif isinstance(a, str):
                        authors.append(a)

                # Format date
                if publication_date:
                    if hasattr(publication_date, "strftime"):
                        publication_date = publication_date.strftime("%Y-%m-%d")
                    else:
                        publication_date = str(publication_date)

                if not pmid and not title:
                    continue

                articles.append({
                    "pmid": pmid,
                    "title": title,
                    "abstract": abstract,
                    "authors": authors,
                    "journal": journal,
                    "publication_date": publication_date or "",
                    "doi": doi,
                })
            except Exception as e:
                pm.war(f"Failed to parse a PubMed article: {e}")
                continue

        pm.suc(f"Found {len(articles)} PubMed articles")
        return articles

    except Exception as e:
        pm.err(e=e, m=f"PubMed search failed for '{query}'")
        return []


# ========================================================================
# DynamoDB Cache
# ========================================================================


def get_cached_results(query: str) -> Optional[list[dict]]:
    """
    Check DynamoDB cache for a previous search with the same query.
    Returns cached article list or None if not found / expired.
    """
    query_key = _query_hash(query)
    pk = f"QUERY#{query_key}"

    try:
        response = _cache_table().get_item(Key={"PK": pk, "SK": "META"})
        if "Item" not in response:
            return None

        meta = response["Item"]
        articles_data = meta.get("articles", [])

        if not articles_data:
            return None

        pm.inf(f"Cache hit for query '{query}' ({len(articles_data)} articles)")
        return articles_data

    except Exception as e:
        pm.war(f"Cache lookup failed: {e}")
        return None


def cache_results(query: str, articles: list[dict]):
    """Cache PubMed search results in DynamoDB."""
    query_key = _query_hash(query)
    pk = f"QUERY#{query_key}"

    try:
        _cache_table().put_item(Item={
            "PK": pk,
            "SK": "META",
            "query": _normalize_query(query),
            "articles": articles,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "result_count": len(articles),
        })
        pm.suc(f"Cached {len(articles)} articles for query '{query}'")
    except Exception as e:
        pm.war(f"Failed to cache results: {e}")


def is_pmid_indexed(pmid: str) -> bool:
    """Check if a PubMed article (by PMID) is already indexed in ChromaDB."""
    try:
        response = _cache_table().get_item(
            Key={"PK": f"PMID#{pmid}", "SK": "INDEXED"}
        )
        return "Item" in response
    except Exception:
        return False


def mark_pmid_indexed(pmid: str, title: str):
    """Mark a PMID as indexed in ChromaDB so we don't re-index it."""
    try:
        _cache_table().put_item(Item={
            "PK": f"PMID#{pmid}",
            "SK": "INDEXED",
            "title": title,
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        pm.war(f"Failed to mark PMID {pmid} as indexed: {e}")


# ========================================================================
# PubMed Citations Table  (O6 / O7)
# ========================================================================

PUBMED_CITATIONS_TABLE = "PubMedCitations"


def _citations_table():
    return dynamodb_client.Table(PUBMED_CITATIONS_TABLE)  # type: ignore


# ========================================================================
# Citation Count — Semantic Scholar API  (O7)
# ========================================================================

_SEMANTIC_SCHOLAR_URL = "https://api.semanticscholar.org/graph/v1/paper/PMID:{pmid}?fields=citationCount"


def get_cached_citation(pmid: str) -> Optional[int]:
    """Return a cached citation count for *pmid*, or None if not cached / expired."""
    try:
        response = _citations_table().get_item(
            Key={"PK": f"PMID#{pmid}", "SK": "CITATIONS"}
        )
        if "Item" not in response:
            return None
        item = response["Item"]
        # Honour DynamoDB TTL expiry as a server-side mechanism, but also check
        # a local `expires_at` unix timestamp so tests don't need DynamoDB TTL enabled.
        expires_at = item.get("expires_at")
        if expires_at and int(expires_at) < int(time.time()):
            return None
        count = item.get("citation_count")
        return int(count) if count is not None else None
    except Exception as e:
        pm.war(f"Citation cache lookup failed for PMID {pmid}: {e}")
        return None


def cache_citation(pmid: str, count: int, title: str = "") -> None:
    """Persist *count* citations for *pmid* into DynamoDB with a 30-day TTL."""
    expires_at = int(time.time()) + settings.pubmed_citation_ttl_seconds
    try:
        _citations_table().put_item(Item={
            "PK": f"PMID#{pmid}",
            "SK": "CITATIONS",
            "citation_count": count,
            "title": title,
            "cached_at": datetime.now(timezone.utc).isoformat(),
            "expires_at": expires_at,        # local TTL check
            "ttl": expires_at,               # native DynamoDB TTL attribute
        })
    except Exception as e:
        pm.war(f"Failed to cache citation count for PMID {pmid}: {e}")


def fetch_citation_count(pmid: str) -> Optional[int]:
    """
    Query the Semantic Scholar public API for the citation count of *pmid*.

    Returns None on any network/API error so the caller can degrade gracefully.
    The API is unauthenticated and allows 100 req/5 min without a key.
    """
    url = _SEMANTIC_SCHOLAR_URL.format(pmid=pmid)
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"{settings.pubmed_tool_name}/1.0 ({settings.pubmed_email})"},
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())
            count = data.get("citationCount")
            return int(count) if count is not None else None
    except urllib.error.HTTPError as e:
        # 404 = paper not in Semantic Scholar; silently return None
        if e.code != 404:
            pm.war(f"Semantic Scholar HTTP {e.code} for PMID {pmid}")
        return None
    except Exception as e:
        pm.war(f"Citation fetch failed for PMID {pmid}: {e}")
        return None


def get_or_fetch_citation_count(pmid: str, title: str = "") -> int:
    """
    Return the citation count for *pmid*, reading from the DynamoDB cache first
    and falling back to a live Semantic Scholar API call if not cached.

    Returns 0 when the count cannot be determined so sorting still works.
    """
    cached = get_cached_citation(pmid)
    if cached is not None:
        return cached

    count = fetch_citation_count(pmid)
    if count is None:
        count = 0

    cache_citation(pmid, count, title)
    return count


# ========================================================================
# PMC Full-Text PDF Download  (O6)
# ========================================================================

_ELINK_URL = (
    "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi"
    "?dbfrom=pubmed&db=pmc&id={pmid}&retmode=json&tool={tool}&email={email}{api_key}"
)
_PMC_PDF_URL = "https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmcid}/pdf/"


def fetch_pmcid(pmid: str) -> Optional[str]:
    """
    Use the NCBI elink API to retrieve the PMC ID for *pmid*, if the article
    has an open-access full-text record in PubMed Central.

    Returns the raw PMCID string (digits only), or None if no PMC record exists.
    """
    api_key_param = f"&api_key={settings.ncbi_api_key}" if settings.ncbi_api_key else ""
    url = _ELINK_URL.format(
        pmid=pmid,
        tool=urllib.parse.quote(settings.pubmed_tool_name),
        email=urllib.parse.quote(settings.pubmed_email),
        api_key=api_key_param,
    )
    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": f"{settings.pubmed_tool_name}/1.0 ({settings.pubmed_email})"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        link_sets = data.get("linksets", [])
        if not link_sets:
            return None

        for link_set in link_sets:
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
    """
    Attempt to download the open-access PDF for a PMC article.

    Args:
        pmid:       PubMed ID (used only for naming the output file).
        pmcid:      PubMed Central ID returned by :func:`fetch_pmcid`.
        output_dir: Directory to save the downloaded PDF (created if absent).

    Returns:
        Absolute path to the saved PDF, or None on failure.
    """
    os.makedirs(output_dir, exist_ok=True)
    pdf_path = os.path.join(output_dir, f"pmid_{pmid}.pdf")

    if os.path.exists(pdf_path):
        pm.inf(f"PDF already exists for PMID {pmid}: {pdf_path}")
        return pdf_path

    url = _PMC_PDF_URL.format(pmcid=pmcid)
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": f"{settings.pubmed_tool_name}/1.0 ({settings.pubmed_email})",
                "Accept": "application/pdf,*/*",
            },
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            content_type = resp.headers.get("Content-Type", "")
            if "pdf" not in content_type.lower():
                pm.war(
                    f"PMC download for PMID {pmid} returned non-PDF content-type: {content_type}"
                )
                return None
            with open(pdf_path, "wb") as f:
                f.write(resp.read())

        pm.suc(f"Downloaded PDF for PMID {pmid} → {pdf_path}")
        return pdf_path
    except urllib.error.HTTPError as e:
        # 403/404 means no open-access PDF, not an error worth logging loudly.
        if e.code not in (403, 404):
            pm.war(f"PDF download HTTP {e.code} for PMID {pmid} (PMC{pmcid})")
        return None
    except Exception as e:
        pm.war(f"PDF download failed for PMID {pmid}: {e}")
        return None


# ========================================================================
# Full-Text PDF Indexing Tracking  (O6)
# ========================================================================

def is_pmid_pdf_indexed(pmid: str) -> bool:
    """Return True if a full-text PDF for *pmid* has already been indexed into ChromaDB."""
    try:
        response = _cache_table().get_item(
            Key={"PK": f"PMID#{pmid}", "SK": "PDF_INDEXED"}
        )
        return "Item" in response
    except Exception:
        return False


def mark_pmid_pdf_indexed(pmid: str, title: str, pdf_path: str) -> None:
    """Record that the full-text PDF for *pmid* has been indexed into ChromaDB."""
    try:
        _cache_table().put_item(Item={
            "PK": f"PMID#{pmid}",
            "SK": "PDF_INDEXED",
            "title": title,
            "pdf_path": pdf_path,
            "indexed_at": datetime.now(timezone.utc).isoformat(),
        })
    except Exception as e:
        pm.war(f"Failed to mark PDF indexed for PMID {pmid}: {e}")


# ========================================================================
# High-Level Enrichment Pipeline  (O6 / O7)
# ========================================================================

def enrich_articles_with_full_text(
    articles: list[dict],
    vector_store_manager,
    pdf_processor,
) -> list[dict]:
    """
    For each article in *articles*, attempt to download a full-text PDF from
    PubMed Central (if open-access) and index it into ChromaDB.

    Adds a ``has_full_text`` boolean key to each article dict indicating whether
    a full-text PDF was successfully downloaded and indexed.

    Args:
        articles:             List of article dicts as returned by :func:`search_pubmed`.
        vector_store_manager: :class:`~rag.vector_store.VectorStoreManager` instance.
        pdf_processor:        :class:`~rag.pdf_processor.PDFProcessor` instance.

    Returns:
        The same list with ``has_full_text`` keys populated (mutated in place
        and also returned for convenience).
    """
    output_dir = settings.pubmed_pdf_subdir

    for article in articles:
        pmid = article.get("pmid", "")
        title = article.get("title", "")
        article["has_full_text"] = False

        if not pmid:
            continue

        # Skip if already indexed
        if is_pmid_pdf_indexed(pmid):
            article["has_full_text"] = True
            pm.inf(f"Full-text PDF already indexed for PMID {pmid}")
            continue

        # Look up PMC ID
        pmcid = fetch_pmcid(pmid)
        if not pmcid:
            continue

        # Download PDF
        pdf_path = download_pmc_pdf(pmid, pmcid, output_dir)
        if not pdf_path:
            continue

        # Index through RAG pipeline
        try:
            pages = pdf_processor.load_single_pdf(pdf_path)
            # Attach source metadata so the retriever can surface filename/page
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
    """
    Add a ``citation_count`` key to each article dict, fetching from cache or
    the Semantic Scholar API.  Modifies *articles* in place and returns them.
    """
    for article in articles:
        pmid = article.get("pmid", "")
        title = article.get("title", "")
        if pmid:
            article["citation_count"] = get_or_fetch_citation_count(pmid, title)
        else:
            article["citation_count"] = 0
    return articles


def sort_articles_by_citations(articles: list[dict]) -> list[dict]:
    """Return *articles* sorted by ``citation_count`` descending (highest-impact first)."""
    return sorted(articles, key=lambda a: a.get("citation_count", 0), reverse=True)
