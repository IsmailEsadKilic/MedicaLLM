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
from typing import Optional, Dict, Callable
from logging import getLogger
from concurrent.futures import ThreadPoolExecutor

from .models import PubMedArticle, PubMedSearchResult
from .scoring import compute_confidence_score, get_quality_warnings
from .scopus_service import get_scopus_service
from .openalex_service import get_openalex_service
from .query_classifier import get_adaptive_weights, get_query_type_description
from ..config import settings

logger = getLogger(__name__)


# Shared, bounded thread pool for external-API enrichment fan-out. Reused across
# searches so concurrent multi-query searches don't multiply into 9+ threads
# (audit P20). 6 workers is enough for 2 concurrent searches × 3 services.
_ENRICHMENT_EXECUTOR: Optional[ThreadPoolExecutor] = None


def _get_enrichment_executor() -> ThreadPoolExecutor:
    global _ENRICHMENT_EXECUTOR
    if _ENRICHMENT_EXECUTOR is None:
        _ENRICHMENT_EXECUTOR = ThreadPoolExecutor(
            max_workers=6, thread_name_prefix="pubmed_enrich"
        )
    return _ENRICHMENT_EXECUTOR


def _http_get_with_retry(
    url: str,
    headers: dict,
    timeout: float = 8.0,
    max_attempts: int = 3,
    retry_on_empty: Optional[Callable[[bytes], bool]] = None,
) -> Optional[bytes]:
    """
    HTTP GET with retries for 429, 5xx, and transient network errors.
    
    Honours the `Retry-After` header when present. Falls back to linear backoff.
    Optionally retries when the response body is "empty" (caller-defined check).
    
    Returns the raw response body or None if all attempts fail.
    """
    last_err: Optional[Exception] = None
    for attempt in range(max_attempts):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                body = resp.read()
            # Caller-defined "empty" check (e.g., 0 results → maybe rate-limited)
            if retry_on_empty is not None and retry_on_empty(body):
                if attempt < max_attempts - 1:
                    sleep = 0.4 * (attempt + 1)
                    logger.debug(f"[HTTP] empty response, retry {attempt+1}/{max_attempts} in {sleep}s")
                    time.sleep(sleep)
                    continue
            return body
        except urllib.error.HTTPError as e:
            last_err = e
            # Honour Retry-After on 429/503
            if e.code in (429, 503):
                retry_after = e.headers.get("Retry-After", "")
                try:
                    sleep = float(retry_after) if retry_after else 1.0 * (attempt + 1)
                except ValueError:
                    sleep = 1.0 * (attempt + 1)
                sleep = min(sleep, 5.0)  # cap at 5s
                if attempt < max_attempts - 1:
                    logger.warning(f"[HTTP] {e.code} rate limited, retry {attempt+1}/{max_attempts} in {sleep:.1f}s")
                    time.sleep(sleep)
                    continue
            elif 500 <= e.code < 600 and attempt < max_attempts - 1:
                time.sleep(0.4 * (attempt + 1))
                continue
            else:
                # 4xx other than 429 → don't retry
                return None
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            if attempt < max_attempts - 1:
                time.sleep(0.4 * (attempt + 1))
                continue
    
    if last_err:
        logger.warning(f"[HTTP] all retries failed for {url[:80]}...: {last_err}")
    return None


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
    
    # Classify query and get adaptive weights (regex-based classification — no
    # LLM is ever passed here, so the LLM-classification fallback in
    # `classify_query` is unused; calling without `llm` makes that explicit).
    query_type, scoring_weights = get_adaptive_weights(query)
    query_type_desc = get_query_type_description(query_type)
    logger.info(f"[PUBMED] Query classified as: {query_type_desc}")
    logger.debug(f"[PUBMED] Using adaptive weights: {scoring_weights}")
    
    # Build API parameters
    api_key_param = f"&api_key={settings.ncbi_api_key}" if settings.ncbi_api_key else ""
    base_headers = {
        "User-Agent": f"{settings.pubmed_tool_name}/1.0 ({settings.pubmed_email})"
    }
    logger.debug(f"[PUBMED] Using API key: {bool(settings.ncbi_api_key)}")
    
    try:
        # Step 1: esearch — get PMIDs sorted by relevance (with retry for transient failures)
        logger.debug(f"[PUBMED] Step 1: Executing esearch")
        esearch_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            f"?db=pubmed&term={urllib.parse.quote(query)}&retmax={max_results}"
            f"&sort=relevance&retmode=json"
            f"&tool={urllib.parse.quote(settings.pubmed_tool_name)}"
            f"&email={urllib.parse.quote(settings.pubmed_email)}{api_key_param}"
        )
        
        logger.debug(f"[PUBMED] esearch URL: {esearch_url[:200]}...")
        pmids: list[str] = []
        total_found = 0
        
        # Don't treat "0 results" as a transient failure — it's a valid
        # response and retrying just adds ~1.2s of latency for nothing
        # (audit P9). We only retry on HTTP errors / network failures, which
        # `_http_get_with_retry` already handles.
        body = _http_get_with_retry(
            esearch_url, headers=base_headers, timeout=8.0,
            max_attempts=3,
        )
        if body:
            try:
                search_data = json.loads(body.decode())
                pmids = search_data.get("esearchresult", {}).get("idlist", [])
                total_found = int(search_data.get("esearchresult", {}).get("count", 0))
            except Exception as e:
                logger.warning(f"[PUBMED] Failed to parse esearch response: {e}")
        
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
        
        # Step 2: efetch — get article details as XML (with retry)
        efetch_url = (
            f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            f"?db=pubmed&id={','.join(pmids)}&retmode=xml"
            f"&tool={urllib.parse.quote(settings.pubmed_tool_name)}"
            f"&email={urllib.parse.quote(settings.pubmed_email)}{api_key_param}"
        )
        
        logger.debug(f"[PUBMED] efetch URL: {efetch_url[:200]}...")
        efetch_body = _http_get_with_retry(
            efetch_url, headers=base_headers, timeout=12.0, max_attempts=3,
        )
        if not efetch_body:
            logger.warning("[PUBMED] efetch failed after retries, returning empty result")
            return PubMedSearchResult(
                query=query,
                articles=[],
                total_found=total_found,
                search_time_ms=round((time.time() - start_time) * 1000, 2),
            )
        root = ET.fromstring(efetch_body.decode())
        
        logger.debug(f"[PUBMED] Step 3: Parsing XML articles")
        
        # Step 3: Parse articles (XML only — no external API calls here)
        articles = []
        article_dois: Dict[str, str] = {}  # pmid -> doi mapping for enrichment
        total_fetched_count = len(pmids)  # used for rank normalisation
        for article_elem in root.findall(".//PubmedArticle"):
            try:
                article = _parse_article_xml(
                    article_elem, query, scoring_weights, str(query_type),
                    pmids=pmids, total_fetched=total_fetched_count,
                )
                if article:
                    articles.append(article)
                    if article.doi:
                        article_dois[article.pmid] = article.doi
                    logger.debug(f"[PUBMED] Parsed article: PMID {article.pmid}, confidence: {article.confidence_score:.1f}")
            except Exception as e:
                logger.warning(f"[PUBMED] Failed to parse article: {e}")
        
        logger.info(f"[PUBMED] Successfully parsed {len(articles)} articles")
        
        # Step 3b: Batch-enrich with external metrics (Scopus + OpenAlex)
        articles = _batch_enrich_articles(articles, article_dois, query, scoring_weights)
        
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


def _parse_article_xml(
    article_elem: ET.Element,
    query: str,
    scoring_weights: dict,
    query_type: str,
    pmids: list[str] | None = None,
    total_fetched: int = 0,
) -> Optional[PubMedArticle]:
    """Parse a single PubmedArticle XML element into a PubMedArticle model."""
    
    # PMID
    pmid_elem = article_elem.find(".//PMID")
    pmid = pmid_elem.text.strip() if pmid_elem is not None and pmid_elem.text else ""

    # Positional rank from PubMed's sort=relevance result order (1-based)
    pubmed_rank = 0
    if pmids and pmid:
        try:
            pubmed_rank = pmids.index(pmid) + 1
        except ValueError:
            pubmed_rank = 0
    
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
    
    # DOI and PMC ID — must scan ALL <ArticleId> elements; the previous
    # implementation `break`-ed inside the PMC branch, which dropped the DOI
    # whenever PMC appeared first in the list (audit P2). DOI is required for
    # paywalled-PDF download fallback and for de-dup against OpenAlex.
    doi = ""
    pmc_id = ""
    for eid in article_elem.findall(".//ArticleId"):
        id_type = eid.get("IdType")
        if not (eid.text and id_type):
            continue
        if id_type == "doi" and not doi:
            doi = eid.text.strip()
        elif id_type == "pmc" and not pmc_id:
            pmc_id = eid.text.strip()  # e.g., "PMC7234567"
    
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
    
    # NOTE: External API calls (Scopus, OpenAlex, Semantic Scholar) are NOT made
    # here. They run in batch via _batch_enrich_articles() after all XML is parsed.
    # This keeps parsing fast and enables batch API optimizations.
    
    # Compute initial confidence score (without external metrics — will be re-scored)
    confidence, breakdown = compute_confidence_score(
        citation_count=0,
        publication_date=pub_date,
        publication_types=pub_types,
        query=query,
        title=title,
        abstract=abstract,
        pubmed_rank=pubmed_rank,
        total_fetched=total_fetched,
        custom_weights=scoring_weights,
    )
    # Store rank info for re-scoring after batch enrichment
    breakdown["_pubmed_rank"] = pubmed_rank
    
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
        citation_count=0,
        confidence_score=confidence,
        confidence_breakdown=breakdown,
        relevance_score=breakdown.get("relevance", 0.0) / 100.0,
        citation_source="none",
        query_type=query_type,
    )


# ============================================================================
# Batch Enrichment (Scopus + OpenAlex — concurrent)
# ============================================================================


def _batch_enrich_articles(
    articles: list[PubMedArticle],
    article_dois: Dict[str, str],
    query: str,
    scoring_weights: dict,
) -> list[PubMedArticle]:
    """
    Enrich a list of PubMedArticles with external metrics in batch.
    
    Uses batch APIs (Scopus batch search + OpenAlex filter) and concurrent
    execution to minimize total latency. Replaces the old per-article sequential
    approach which caused timeouts.
    
    Performance: ~2-3 API calls total instead of 4N sequential calls.
    Typical time: 1-3 seconds for 15 articles (was 20-60+ seconds).
    """
    if not articles:
        return articles
    
    pmids = [a.pmid for a in articles if a.pmid]
    
    # --- Concurrent batch fetches ---
    scopus_results: Dict[str, Dict] = {}
    openalex_results: Dict[str, Dict] = {}
    fulltext_results: Dict[str, Dict[str, str]] = {}
    
    def _fetch_scopus():
        if not settings.scopus_api_key or not settings.scopus_use_for_citations:
            return {}
        try:
            return get_scopus_service().enrich_batch(pmids, dois=article_dois)
        except Exception as e:
            logger.warning(f"[PUBMED] Batch Scopus enrichment failed: {e}")
            return {}
    
    def _fetch_openalex():
        if not settings.openalex_enabled:
            return {}
        try:
            return get_openalex_service().get_batch_metrics(pmids)
        except Exception as e:
            logger.warning(f"[PUBMED] Batch OpenAlex enrichment failed: {e}")
            return {}
    
    def _fetch_fulltext():
        if not settings.fulltext_enabled:
            return {}
        try:
            # Fetch full text for ALL articles by default.
            # settings.fulltext_max_articles > 0 caps to top-N if you need to
            # bound latency (e.g., for very large result sets).
            target_articles = articles
            if settings.fulltext_max_articles > 0:
                target_articles = articles[: settings.fulltext_max_articles]
            request = [
                {"pmid": a.pmid, "pmc_id": a.pmc_id}
                for a in target_articles
                if a.pmid
            ]
            from .fulltext_service import get_fulltext_service
            return get_fulltext_service().get_batch_full_texts(request)
        except Exception as e:
            logger.warning(f"[PUBMED] Batch full-text fetch failed: {e}")
            return {}
    
    # Run Scopus, OpenAlex, and Europe PMC full-text in parallel. We use a
    # bounded executor (max 3 workers — one per service) so callers running
    # multiple searches concurrently (e.g. `search_pubmed_multi` fans out 3
    # sub-queries) don't multiply this footprint into 9+ threads. Each task
    # is itself I/O-bound and yields the GIL while waiting on HTTP.
    #
    # Audit P19: the previous code declared per-future "timings" but they
    # were just `future.result()` wait-times measured serially, which made
    # them meaningless — once `result()` returns the future is already done
    # and we're not waiting on the others. We now only report the wall-clock
    # for the whole enrichment block, which is what actually matters for
    # latency budgets.
    t0 = time.time()
    enrich_pool = _get_enrichment_executor()
    future_scopus = enrich_pool.submit(_fetch_scopus)
    future_openalex = enrich_pool.submit(_fetch_openalex)
    future_fulltext = enrich_pool.submit(_fetch_fulltext)
    scopus_results = future_scopus.result()
    openalex_results = future_openalex.result()
    fulltext_results = future_fulltext.result()
    t_total = (time.time() - t0) * 1000
    
    logger.info(
        f"[PUBMED] Enrichment timing: total={t_total:.0f}ms "
        f"(Scopus={len(scopus_results)}/{len(pmids)}, "
        f"OpenAlex={len(openalex_results)}/{len(pmids)}, "
        f"FullText={len(fulltext_results)}/{len(pmids)})"
    )
    
    # --- Merge metrics into each article and re-score ---
    enriched_articles = []
    for article in articles:
        pmid = article.pmid
        scopus_data = scopus_results.get(pmid, {})
        openalex_data = openalex_results.get(pmid, {})
        
        # Determine citation count and source
        citation_count = 0
        citation_source = "none"
        
        if scopus_data.get("citation_count"):
            citation_count = int(scopus_data["citation_count"])
            citation_source = "scopus"
        elif openalex_data and openalex_data.get("cited_by_count"):
            citation_count = int(openalex_data["cited_by_count"])
            citation_source = "openalex"
        
        # FWCI: prefer Scopus (if institutional key), fallback OpenAlex
        fwci = scopus_data.get("fwci")
        fwci_source = "scopus" if fwci is not None else ""
        if fwci is None and openalex_data:
            fwci = openalex_data.get("fwci")
            fwci_source = "openalex" if fwci is not None else ""
        
        # Journal metrics from Scopus Serial Title
        cite_score = scopus_data.get("cite_score")
        sjr = scopus_data.get("sjr")
        snip = scopus_data.get("snip")
        journal_percentile = scopus_data.get("journal_percentile")
        open_access = scopus_data.get("open_access", False)
        subject_areas = scopus_data.get("subject_areas", [])
        
        # OpenAlex extras
        citation_normalized_percentile = (
            openalex_data.get("citation_normalized_percentile") if openalex_data else None
        )
        openalex_id = openalex_data.get("openalex_id", "") if openalex_data else ""
        
        # Re-compute confidence score with full metrics
        confidence, breakdown = compute_confidence_score(
            citation_count=citation_count,
            publication_date=article.publication_date,
            publication_types=article.publication_types,
            query=query,
            title=article.title,
            abstract=article.abstract,
            cite_score=cite_score,
            sjr=sjr,
            snip=snip,
            journal_percentile=journal_percentile,
            fwci=fwci,
            citation_normalized_percentile=citation_normalized_percentile,
            open_access=open_access,
            pubmed_rank=(article.confidence_breakdown.get("_pubmed_rank", 0)),
            total_fetched=len(articles),
            custom_weights=scoring_weights,
        )
        
        # Create enriched article (Pydantic model is immutable-ish, so rebuild)
        fulltext_sections = fulltext_results.get(pmid, {})
        # Truncate long sections to keep LLM context manageable
        if fulltext_sections:
            max_chars = settings.fulltext_max_chars_per_section
            fulltext_sections = {
                k: (v[:max_chars] + "…") if len(v) > max_chars else v
                for k, v in fulltext_sections.items()
            }
        
        enriched = article.model_copy(update={
            "citation_count": citation_count,
            "citation_source": citation_source,
            "confidence_score": confidence,
            "confidence_breakdown": breakdown,
            "relevance_score": breakdown.get("relevance", 0.0) / 100.0,
            "scopus_id": scopus_data.get("scopus_id", ""),
            "scopus_eid": scopus_data.get("eid", ""),
            "cite_score": cite_score,
            "sjr": sjr,
            "snip": snip,
            "fwci": fwci,
            "fwci_source": fwci_source,
            "citation_normalized_percentile": citation_normalized_percentile,
            "openalex_id": openalex_id,
            "journal_percentile": journal_percentile,
            "subject_areas": subject_areas,
            "open_access": open_access,
            "author_count": scopus_data.get("author_count", len(article.authors)),
            "affiliation_count": scopus_data.get("affiliation_count", 0),
            "full_text_available": bool(fulltext_sections),
            "full_text_sections": fulltext_sections,
        })
        enriched_articles.append(enriched)
    
    return enriched_articles


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


# ============================================================================
# Multi-Query Search (deduplicates by PMID across parallel queries)
# ============================================================================

def search_pubmed_multi(
    queries: list[str],
    max_per_query: int = 5,
    min_confidence: float = 45.0,
) -> PubMedSearchResult:
    """
    Run up to 3 targeted PubMed sub-queries, merge results, and deduplicate by PMID.

    Used when a complex clinical question has multiple distinct facets that a
    single broad query cannot capture (e.g., estrogen-only HRT vs. combined HRT).

    Args:
        queries: List of focused sub-query strings (max 3 used).
        max_per_query: Articles to fetch per sub-query before filtering.
        min_confidence: Minimum confidence score to include (0-100).

    Returns:
        Merged, deduplicated PubMedSearchResult sorted by confidence.
    """
    start_time = time.time()
    seen_pmids: set[str] = set()
    all_articles = []
    combined_total_found = 0

    # Run sub-queries in parallel (each makes its own esearch+efetch+enrich roundtrip)
    sub_queries = queries[:3]  # cap at 3 to limit latency
    
    def _run_query(q: str):
        try:
            return search_pubmed(
                query=q,
                max_results=max(max_per_query, 10),
                min_confidence=min_confidence,
            )
        except Exception as exc:
            logger.warning(f"[PUBMED] sub-query failed ('{q}'): {exc}")
            return None
    
    with ThreadPoolExecutor(max_workers=len(sub_queries)) as executor:
        results = list(executor.map(_run_query, sub_queries))
    
    for result in results:
        if result is None:
            continue
        combined_total_found += result.total_found
        for article in result.articles:
            if article.pmid and article.pmid not in seen_pmids:
                seen_pmids.add(article.pmid)
                all_articles.append(article)
            elif not article.pmid:
                all_articles.append(article)

    # Sort merged pool by confidence
    all_articles.sort(key=lambda a: a.confidence_score, reverse=True)

    avg_confidence = (
        sum(a.confidence_score for a in all_articles) / len(all_articles)
        if all_articles else 0.0
    )
    search_time_ms = round((time.time() - start_time) * 1000, 2)

    logger.info(
        f"[PUBMED] Multi-query ({len(queries)} queries): "
        f"{len(all_articles)} unique articles in {search_time_ms}ms"
    )

    return PubMedSearchResult(
        query=" | ".join(queries),
        articles=all_articles,
        total_found=combined_total_found,
        search_time_ms=search_time_ms,
        avg_confidence=round(avg_confidence, 1),
        filtered_count=0,
    )
