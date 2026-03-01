import hashlib
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
