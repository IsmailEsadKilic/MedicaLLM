"""
Scopus API integration for citation metrics.

Provides citation counts and additional metrics from Scopus database.
"""
import urllib.request
import urllib.parse
import urllib.error
import json
import time
from typing import Optional, Dict, Any
from logging import getLogger

from ..config import settings

logger = getLogger(__name__)


class ScopusCitationService:
    """Service for fetching citation data from Scopus API."""
    
    BASE_URL = "https://api.elsevier.com/content"
    _abstract_api_warning_shown = False  # Class variable to track if warning was shown
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Scopus service.
        
        Args:
            api_key: Scopus API key (defaults to settings.scopus_api_key)
        """
        self.api_key = api_key or settings.scopus_api_key
        self.enabled = bool(self.api_key)
        # Per-instance ISSN -> journal metrics cache to avoid repeat Serial API calls
        self._serial_cache: Dict[str, Dict[str, Any]] = {}
        
        if not self.enabled:
            logger.debug("[SCOPUS] Scopus API key not configured, service disabled")
    
    def get_citation_count_by_pmid(self, pmid: str) -> Optional[int]:
        """
        Get citation count for a PubMed article using PMID.
        
        Args:
            pmid: PubMed ID
            
        Returns:
            Citation count or None if not found/error
        """
        if not self.enabled:
            return None
        
        try:
            # Search for article by PMID
            article_data = self._search_by_pmid(pmid)
            
            if article_data:
                citation_count = article_data.get("citedby-count", 0)
                logger.debug(f"[SCOPUS] PMID {pmid} citation count: {citation_count}")
                return int(citation_count) if citation_count else 0
            
            return None
            
        except Exception as e:
            logger.warning(f"[SCOPUS] Failed to fetch citation count for PMID {pmid}: {e}")
            return None
    
    def get_citation_count_by_doi(self, doi: str) -> Optional[int]:
        """
        Get citation count for an article using DOI.
        
        Args:
            doi: Digital Object Identifier
            
        Returns:
            Citation count or None if not found/error
        """
        if not self.enabled:
            return None
        
        try:
            # Search for article by DOI
            article_data = self._search_by_doi(doi)
            
            if article_data:
                citation_count = article_data.get("citedby-count", 0)
                logger.debug(f"[SCOPUS] DOI {doi} citation count: {citation_count}")
                return int(citation_count) if citation_count else 0
            
            return None
            
        except Exception as e:
            logger.warning(f"[SCOPUS] Failed to fetch citation count for DOI {doi}: {e}")
            return None
    
    def get_article_metrics(self, pmid: Optional[str] = None, doi: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get comprehensive article metrics from Scopus.
        
        Args:
            pmid: PubMed ID (optional)
            doi: Digital Object Identifier (optional)
            
        Returns:
            Dictionary with metrics or None if not found
            {
                "citation_count": int,
                "scopus_id": str,
                "eid": str,
                "title": str,
                "publication_name": str,
                "cover_date": str,
                "doi": str,
                "pmid": str,
                "author_count": int,
                "affiliation_count": int,
                "subject_areas": list[str],
                "open_access": bool,
                "fwci": float,  # Field-Weighted Citation Impact
                "cite_score": float,  # Journal CiteScore
                "sjr": float,  # SCImago Journal Rank
                "snip": float,  # Source Normalized Impact per Paper
                "journal_percentile": float  # Percentile ranking
            }
        """
        if not self.enabled:
            return None
        
        try:
            # Try PMID first, then DOI
            article_data = None
            if pmid:
                article_data = self._search_by_pmid(pmid)
            if not article_data and doi:
                article_data = self._search_by_doi(doi)
            
            if not article_data:
                return None
            
            # Extract comprehensive metrics
            metrics = {
                "citation_count": int(article_data.get("citedby-count", 0)),
                "scopus_id": article_data.get("dc:identifier", "").replace("SCOPUS_ID:", ""),
                "eid": article_data.get("eid", ""),
                "title": article_data.get("dc:title", ""),
                "publication_name": article_data.get("prism:publicationName", ""),
                "cover_date": article_data.get("prism:coverDate", ""),
                "doi": article_data.get("prism:doi", ""),
                "pmid": article_data.get("pubmed-id", ""),
                "author_count": len(article_data.get("author", [])) if "author" in article_data else 0,
                "affiliation_count": int(article_data.get("affiliation-count", 0)),
                "subject_areas": self._extract_subject_areas(article_data),
                "open_access": self._is_open_access(article_data),
                # Journal/article metrics — populated below
                "cite_score": None,
                "sjr": None,
                "snip": None,
                "journal_percentile": None,
                "fwci": None,
                "fwci_source": None,
                "citation_normalized_percentile": None,
                "openalex_id": None,
            }

            # 1) Journal-level metrics via Serial Title API (ISSN-based, works with
            #    basic API keys). This is the primary source for CiteScore/SJR/SNIP/
            #    percentile.
            issn = self._extract_issn(article_data)
            if issn:
                serial_metrics = self._get_serial_metrics(issn)
                if serial_metrics:
                    # Only overwrite when we actually have a value
                    for key, value in serial_metrics.items():
                        if value is not None:
                            metrics[key] = value
                    # Enrich subject areas if Serial Title returned richer list
                    if not metrics["subject_areas"] and serial_metrics.get("subject_areas"):
                        metrics["subject_areas"] = serial_metrics["subject_areas"]

            # 2) Article-level metrics via Abstract Retrieval (FWCI). Requires
            #    institutional access; degrades silently on 401.
            #    OpenAlex is used as a fallback further up the pipeline in
            #    `service.py` so it also runs when Scopus fails completely.
            #    SKIP if we already know the key doesn't have access (after first 401).
            scopus_id = metrics["scopus_id"]
            if scopus_id and not ScopusCitationService._abstract_api_warning_shown:
                detailed_data = self._get_abstract_details(scopus_id)
                if detailed_data:
                    for key, value in self._extract_detailed_metrics(detailed_data).items():
                        if value is not None:
                            metrics[key] = value
                    if metrics.get("fwci") is not None and not metrics.get("fwci_source"):
                        metrics["fwci_source"] = "scopus"
                else:
                    ScopusCitationService._abstract_api_warning_shown = True
                    logger.info(
                        "[SCOPUS] Abstract Retrieval API not accessible with current API key. "
                        "FWCI will be supplied by OpenAlex fallback (journal-level metrics still work via Serial Title API)."
                    )

            # 3) Last-resort fallbacks straight off the search entry (rarely populated)
            for key, value in self._get_journal_metrics(article_data).items():
                if metrics.get(key) is None and value is not None:
                    metrics[key] = value
            for key, value in self._get_article_level_metrics(article_data).items():
                if metrics.get(key) is None and value is not None:
                    metrics[key] = value
            
            logger.debug(f"[SCOPUS] Retrieved metrics for article: {metrics['title'][:50]}...")
            return metrics
            
        except Exception as e:
            logger.warning(f"[SCOPUS] Failed to fetch article metrics: {e}")
            return None
    
    def search_batch(self, pmids: list[str]) -> Dict[str, Dict[str, Any]]:
        """
        Batch search Scopus for multiple PMIDs in a single API call.
        
        Scopus Search API supports OR queries: PMID(X) OR PMID(Y) OR ...
        Max ~25 PMIDs per call (URL length limit).
        
        Args:
            pmids: List of PubMed IDs
            
        Returns:
            Dict mapping PMID -> article data (only found articles)
        """
        if not self.enabled or not pmids:
            return {}
        
        results: Dict[str, Dict[str, Any]] = {}
        
        # Scopus URL limit ~4000 chars; each PMID(XXXXXXXX) is ~15 chars + " OR "
        # Safe batch size: 25
        BATCH_SIZE = 25
        for i in range(0, len(pmids), BATCH_SIZE):
            # Small delay between consecutive batches (Scopus ~9 req/s limit)
            if i > 0:
                time.sleep(0.2)
            batch = pmids[i:i + BATCH_SIZE]
            query = " OR ".join(f"PMID({p})" for p in batch)
            entries = self._search_articles_batch(query, count=len(batch))
            for entry in entries:
                found_pmid = entry.get("pubmed-id", "")
                if found_pmid:
                    results[found_pmid] = entry
        
        return results
    
    def _search_articles_batch(self, query: str, count: int = 25) -> list[Dict[str, Any]]:
        """
        Execute a Scopus search query returning multiple results.
        
        Args:
            query: Scopus search query (e.g., "PMID(X) OR PMID(Y)")
            count: Max results to return
            
        Returns:
            List of article data dicts
        """
        if not self.enabled:
            return []
        
        url = f"{self.BASE_URL}/search/scopus"
        params = {
            "query": query,
            "httpAccept": "application/json",
            "count": count,
        }
        
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        
        logger.debug(f"[SCOPUS] Batch searching {count} articles")
        
        headers = {"Accept": "application/json", "User-Agent": "MedicaLLM/1.0", "X-ELS-APIKey": self.api_key}
        
        for attempt in range(3):
            try:
                req = urllib.request.Request(full_url, headers=headers)
                with urllib.request.urlopen(req, timeout=5) as response:
                    data = json.loads(response.read().decode())
                    entries = data.get("search-results", {}).get("entry", [])
                    return [e for e in entries if "error" not in e and "dc:title" in e]
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 2:
                    retry_after = e.headers.get("Retry-After", "")
                    try:
                        sleep = min(float(retry_after), 5.0) if retry_after else 1.0
                    except ValueError:
                        sleep = 1.0
                    logger.warning(f"[SCOPUS] Rate limit hit on batch, retry {attempt+1}/3 in {sleep:.1f}s")
                    time.sleep(sleep)
                    continue
                logger.warning(f"[SCOPUS] Batch search HTTP error {e.code}: {e.reason}")
                return []
            except Exception as e:
                if attempt < 2:
                    time.sleep(0.3)
                    continue
                logger.warning(f"[SCOPUS] Batch search failed: {e}")
                return []
        return []
    
    def enrich_batch(self, pmids: list[str], dois: Optional[Dict[str, str]] = None) -> Dict[str, Dict[str, Any]]:
        """
        Batch-enrich multiple articles with Scopus metrics.
        
        Single API call for search + per-unique-ISSN serial lookups (cached).
        Much faster than per-article get_article_metrics calls.
        
        Args:
            pmids: List of PubMed IDs
            dois: Optional mapping of PMID -> DOI for fallback
            
        Returns:
            Dict mapping PMID -> metrics dict (same structure as get_article_metrics)
        """
        if not self.enabled or not pmids:
            return {}
        
        # 1) Batch search
        search_results = self.search_batch(pmids)
        logger.debug(f"[SCOPUS] Batch search found {len(search_results)}/{len(pmids)} articles")
        
        # 2) Parallel Serial Title lookups for all unique ISSNs
        #    (cache ensures each ISSN is fetched only once even under concurrency)
        unique_issns = set()
        pmid_to_issn: Dict[str, str] = {}
        for found_pmid, article_data in search_results.items():
            issn = self._extract_issn(article_data)
            if issn:
                unique_issns.add(issn)
                pmid_to_issn[found_pmid] = issn
        
        uncached_issns = [i for i in unique_issns if i not in self._serial_cache]
        if uncached_issns:
            from concurrent.futures import ThreadPoolExecutor
            # Scopus Serial API is stricter than Search; 3 workers is safe.
            max_workers = min(3, len(uncached_issns))
            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                list(executor.map(self._get_serial_metrics, uncached_issns))
        
        # 3) Extract metrics per article (serial data now cached)
        enriched: Dict[str, Dict[str, Any]] = {}
        for found_pmid, article_data in search_results.items():
            metrics = {
                "citation_count": int(article_data.get("citedby-count", 0)),
                "scopus_id": article_data.get("dc:identifier", "").replace("SCOPUS_ID:", ""),
                "eid": article_data.get("eid", ""),
                "title": article_data.get("dc:title", ""),
                "publication_name": article_data.get("prism:publicationName", ""),
                "cover_date": article_data.get("prism:coverDate", ""),
                "doi": article_data.get("prism:doi", ""),
                "pmid": found_pmid,
                "author_count": len(article_data.get("author", [])) if "author" in article_data else 0,
                "affiliation_count": int(article_data.get("affiliation-count", 0)),
                "subject_areas": self._extract_subject_areas(article_data),
                "open_access": self._is_open_access(article_data),
                "cite_score": None,
                "sjr": None,
                "snip": None,
                "journal_percentile": None,
                "fwci": None,
                "fwci_source": None,
                "citation_normalized_percentile": None,
                "openalex_id": None,
            }
            
            issn = pmid_to_issn.get(found_pmid)
            if issn:
                serial_metrics = self._serial_cache.get(issn)
                if serial_metrics:
                    for key, value in serial_metrics.items():
                        if value is not None:
                            metrics[key] = value
                    if not metrics["subject_areas"] and serial_metrics.get("subject_areas"):
                        metrics["subject_areas"] = serial_metrics["subject_areas"]
            
            # Last-resort fallbacks from search entry
            for key, value in self._get_journal_metrics(article_data).items():
                if metrics.get(key) is None and value is not None:
                    metrics[key] = value
            
            enriched[found_pmid] = metrics
        
        return enriched

    def _search_by_pmid(self, pmid: str) -> Optional[Dict[str, Any]]:
        """
        Search Scopus for an article by PMID.
        
        Args:
            pmid: PubMed ID
            
        Returns:
            Article data dictionary or None
        """
        query = f"PMID({pmid})"
        return self._search_article(query)
    
    def _search_by_doi(self, doi: str) -> Optional[Dict[str, Any]]:
        """
        Search Scopus for an article by DOI.
        
        Args:
            doi: Digital Object Identifier
            
        Returns:
            Article data dictionary or None
        """
        query = f"DOI({doi})"
        return self._search_article(query)
    
    def _search_article(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Execute a Scopus search query.
        
        Args:
            query: Scopus search query
            
        Returns:
            First article result or None
        """
        if not self.enabled:
            return None
        
        # Minimal rate limiting for single-article lookups (batch uses its own pacing)
        time.sleep(0.1)
        
        url = f"{self.BASE_URL}/search/scopus"
        params = {
            "query": query,
            "httpAccept": "application/json",
            "count": 1,  # We only need the first result
        }
        
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        
        logger.debug(f"[SCOPUS] Searching: {query}")
        
        req = urllib.request.Request(
            full_url,
            headers={
                "Accept": "application/json",
                "User-Agent": "MedicaLLM/1.0",
                "X-ELS-APIKey": self.api_key
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=5) as response:
                data = json.loads(response.read().decode())
                
                # Extract first entry from search results
                entries = data.get("search-results", {}).get("entry", [])
                if entries and len(entries) > 0:
                    entry = entries[0]
                    # Check if it's a valid result (not an error entry)
                    if "error" not in entry and "dc:title" in entry:
                        return entry
                
                logger.debug(f"[SCOPUS] No results found for query: {query}")
                return None
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.debug(f"[SCOPUS] Article not found: {query}")
            elif e.code == 429:
                logger.warning("[SCOPUS] Rate limit exceeded")
            else:
                logger.warning(f"[SCOPUS] HTTP error {e.code}: {e.reason}")
            return None
        except Exception as e:
            logger.warning(f"[SCOPUS] Search failed: {e}")
            return None
    
    def _get_abstract_details(self, scopus_id: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed article information from Abstract Retrieval API.
        This API includes FWCI and other detailed metrics not in search results.
        
        Note: This endpoint may require institutional access or higher-tier API keys.
        If you get 401 errors, your API key may not have access to this endpoint.
        
        Args:
            scopus_id: Scopus article ID (numeric part only)
            
        Returns:
            Detailed article data or None
        """
        if not self.enabled or not scopus_id:
            return None
        
        # Minimal delay
        time.sleep(0.1)
        
        url = f"{self.BASE_URL}/abstract/scopus_id/{scopus_id}"
        params = {
            "httpAccept": "application/json",
            "view": "FULL",  # Get full details including metrics
        }
        
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        
        logger.debug(f"[SCOPUS] Fetching abstract details for Scopus ID: {scopus_id}")
        
        req = urllib.request.Request(
            full_url,
            headers={
                "Accept": "application/json",
                "User-Agent": "MedicaLLM/1.0",
                "X-ELS-APIKey": self.api_key
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=3) as response:
                data = json.loads(response.read().decode())
                
                # The response is wrapped in "abstracts-retrieval-response"
                abstract_data = data.get("abstracts-retrieval-response")
                if abstract_data:
                    return abstract_data
                
                logger.debug(f"[SCOPUS] No abstract details found for Scopus ID: {scopus_id}")
                return None
                
        except urllib.error.HTTPError as e:
            if e.code == 404:
                logger.debug(f"[SCOPUS] Abstract not found for Scopus ID: {scopus_id}")
            elif e.code == 401:
                # Log once at debug level to avoid spam, this is expected for some API keys
                logger.debug(f"[SCOPUS] Abstract Retrieval API requires institutional access (401 Unauthorized). "
                           "FWCI and detailed metrics will not be available. Consider upgrading your API key.")
            elif e.code == 429:
                logger.warning("[SCOPUS] Rate limit exceeded")
            else:
                logger.warning(f"[SCOPUS] HTTP error {e.code}: {e.reason}")
            return None
        except Exception as e:
            logger.debug(f"[SCOPUS] Failed to fetch abstract details: {e}")
            return None
    
    def _extract_detailed_metrics(self, abstract_data: Dict[str, Any]) -> Dict[str, Optional[float]]:
        """
        Extract detailed metrics from Abstract Retrieval API response.
        
        Args:
            abstract_data: Response from Abstract Retrieval API
            
        Returns:
            Dictionary with detailed metrics (FWCI, CiteScore, etc.)
        """
        metrics = {
            "fwci": None,
            "cite_score": None,
            "sjr": None,
            "snip": None,
        }
        
        # FWCI is in the coredata section
        coredata = abstract_data.get("coredata", {})
        
        # Field-Weighted Citation Impact
        if "fwci" in coredata:
            try:
                metrics["fwci"] = float(coredata["fwci"])
                logger.debug(f"[SCOPUS] Found FWCI: {metrics['fwci']}")
            except (ValueError, TypeError):
                pass
        
        # Journal metrics are in subject-areas or item section
        # CiteScore
        item = abstract_data.get("item", {})
        if "citescore-currentmetric" in item:
            try:
                metrics["cite_score"] = float(item["citescore-currentmetric"])
                logger.debug(f"[SCOPUS] Found CiteScore: {metrics['cite_score']}")
            except (ValueError, TypeError):
                pass
        
        # SJR (SCImago Journal Rank)
        if "sjr-currentmetric" in item:
            try:
                metrics["sjr"] = float(item["sjr-currentmetric"])
                logger.debug(f"[SCOPUS] Found SJR: {metrics['sjr']}")
            except (ValueError, TypeError):
                pass
        
        # SNIP (Source Normalized Impact per Paper)
        if "snip-currentmetric" in item:
            try:
                metrics["snip"] = float(item["snip-currentmetric"])
                logger.debug(f"[SCOPUS] Found SNIP: {metrics['snip']}")
            except (ValueError, TypeError):
                pass
        
        return metrics
    
    def _extract_subject_areas(self, article_data: Dict[str, Any]) -> list[str]:
        """
        Extract subject area names from article data.
        
        Args:
            article_data: Scopus article data
            
        Returns:
            List of subject area names
        """
        subject_areas = []
        
        # Subject areas can be in different formats
        if "subject-area" in article_data:
            areas = article_data["subject-area"]
            if isinstance(areas, list):
                subject_areas = [area.get("$", "") for area in areas if "$" in area]
            elif isinstance(areas, dict):
                subject_areas = [areas.get("$", "")]
        
        return [area for area in subject_areas if area]
    
    def _is_open_access(self, article_data: Dict[str, Any]) -> bool:
        """
        Determine if article is open access.
        
        Args:
            article_data: Scopus article data
            
        Returns:
            True if open access, False otherwise
        """
        # Check openaccess flag
        oa_flag = article_data.get("openaccess")
        if oa_flag is not None:
            # Can be string "1"/"0" or int 1/0 or bool
            if isinstance(oa_flag, str):
                return oa_flag == "1"
            return bool(oa_flag)
        
        return False
    
    def _get_journal_metrics(self, article_data: Dict[str, Any]) -> Dict[str, Optional[float]]:
        """
        Extract journal-level metrics from article data.
        
        Note: Basic search API doesn't include all journal metrics.
        For full metrics, would need separate Serial Title API calls.
        
        Args:
            article_data: Scopus article data
            
        Returns:
            Dictionary with journal metrics
        """
        metrics = {
            "cite_score": None,
            "sjr": None,
            "snip": None,
            "journal_percentile": None,
        }
        
        # Try to extract from aggregation-metrics if available
        # Note: These are often not in basic search results
        agg_metrics = article_data.get("aggregation-metrics", {})
        
        # CiteScore
        if "citescore" in agg_metrics:
            try:
                metrics["cite_score"] = float(agg_metrics["citescore"])
            except (ValueError, TypeError):
                pass
        
        # SJR (SCImago Journal Rank)
        if "sjr" in agg_metrics:
            try:
                metrics["sjr"] = float(agg_metrics["sjr"])
            except (ValueError, TypeError):
                pass
        
        # SNIP (Source Normalized Impact per Paper)
        if "snip" in agg_metrics:
            try:
                metrics["snip"] = float(agg_metrics["snip"])
            except (ValueError, TypeError):
                pass
        
        # Percentile
        if "percentile" in agg_metrics:
            try:
                metrics["journal_percentile"] = float(agg_metrics["percentile"])
            except (ValueError, TypeError):
                pass
        
        return metrics
    
    def _get_article_level_metrics(self, article_data: Dict[str, Any]) -> Dict[str, Optional[float]]:
        """
        Extract article-level metrics from article data.
        
        Args:
            article_data: Scopus article data
            
        Returns:
            Dictionary with article-level metrics
        """
        metrics = {
            "fwci": None,  # Field-Weighted Citation Impact
        }
        
        # FWCI (Field-Weighted Citation Impact)
        # Compares citations to field average (1.0 = average, >1.0 = above average)
        if "fwci" in article_data:
            try:
                metrics["fwci"] = float(article_data["fwci"])
            except (ValueError, TypeError):
                pass
        
        return metrics

    # ------------------------------------------------------------------
    # Serial Title API (journal-level metrics)
    # ------------------------------------------------------------------

    def _extract_issn(self, article_data: Dict[str, Any]) -> Optional[str]:
        """Pick the best ISSN from a search entry. Prefers print ISSN, falls back to eISSN."""
        for key in ("prism:issn", "prism:eIssn"):
            raw = article_data.get(key)
            if not raw:
                continue
            # prism:issn may contain space-separated print+electronic pairs
            first = str(raw).split()[0].strip().replace("-", "")
            if first:
                return first
        return None

    def _get_serial_metrics(self, issn: str) -> Optional[Dict[str, Any]]:
        """
        Fetch journal-level metrics (CiteScore, SJR, SNIP, percentile) from the
        Scopus Serial Title API. Results are cached per-instance by ISSN.

        Args:
            issn: Journal ISSN (digits only, hyphens stripped)

        Returns:
            Dict with cite_score / sjr / snip / journal_percentile / subject_areas
            or None on error.
        """
        if not self.enabled or not issn:
            return None

        if issn in self._serial_cache:
            return self._serial_cache[issn]

        # Minimal delay (serial lookups are ISSN-cached, rarely repeated)
        time.sleep(0.1)

        url = f"{self.BASE_URL}/serial/title/issn/{issn}"
        params = {
            "httpAccept": "application/json",
            "view": "CITESCORE",  # Returns CiteScore history incl. percentile
        }
        full_url = f"{url}?{urllib.parse.urlencode(params)}"

        logger.debug(f"[SCOPUS] Fetching serial metrics for ISSN {issn}")

        headers = {"Accept": "application/json", "User-Agent": "MedicaLLM/1.0", "X-ELS-APIKey": self.api_key}
        data = None
        for attempt in range(3):
            try:
                req = urllib.request.Request(full_url, headers=headers)
                with urllib.request.urlopen(req, timeout=3) as response:
                    data = json.loads(response.read().decode())
                break
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 2:
                    retry_after = e.headers.get("Retry-After", "")
                    try:
                        sleep = min(float(retry_after), 5.0) if retry_after else 1.0
                    except ValueError:
                        sleep = 1.0
                    logger.warning(f"[SCOPUS] Serial API rate limit, retry {attempt+1}/3 in {sleep:.1f}s")
                    time.sleep(sleep)
                    continue
                if e.code == 404:
                    logger.debug(f"[SCOPUS] Serial not found for ISSN {issn}")
                else:
                    logger.warning(f"[SCOPUS] Serial API HTTP error {e.code}: {e.reason}")
                self._serial_cache[issn] = {}
                return None
            except Exception as e:
                if attempt < 2:
                    time.sleep(0.3)
                    continue
                logger.warning(f"[SCOPUS] Serial API request failed for ISSN {issn}: {e}")
                self._serial_cache[issn] = {}
                return None
        
        if data is None:
            self._serial_cache[issn] = {}
            return None

        entries = data.get("serial-metadata-response", {}).get("entry", [])
        if not entries:
            self._serial_cache[issn] = {}
            return None
        entry = entries[0]

        parsed = self._parse_serial_entry(entry)
        self._serial_cache[issn] = parsed
        return parsed

    @staticmethod
    def _latest_from_list(entries: list, value_key: str = "$") -> Optional[float]:
        """Pick the most recent entry (by @year) from a Scopus metric list."""
        if not entries:
            return None
        try:
            latest = max(entries, key=lambda e: int(e.get("@year", 0)))
            raw = latest.get(value_key)
            return float(raw) if raw is not None else None
        except (ValueError, TypeError):
            return None

    def _parse_serial_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """Extract CiteScore, SJR, SNIP, percentile and subject areas from a Serial Title entry."""
        result: Dict[str, Any] = {
            "cite_score": None,
            "sjr": None,
            "snip": None,
            "journal_percentile": None,
            "subject_areas": [],
        }

        # SJR — latest year in SJRList
        sjr_list = entry.get("SJRList", {}).get("SJR", []) if entry.get("SJRList") else []
        result["sjr"] = self._latest_from_list(sjr_list)

        # SNIP — latest year in SNIPList
        snip_list = entry.get("SNIPList", {}).get("SNIP", []) if entry.get("SNIPList") else []
        result["snip"] = self._latest_from_list(snip_list)

        # CiteScore + percentile from citeScoreYearInfoList
        cs_info = entry.get("citeScoreYearInfoList", {})
        current_cs = cs_info.get("citeScoreCurrentMetric")
        if current_cs:
            try:
                result["cite_score"] = float(current_cs)
            except (ValueError, TypeError):
                pass

        # Percentile: pick highest percentile from the latest *complete* year
        year_entries = cs_info.get("citeScoreYearInfo", [])
        complete_years = [y for y in year_entries if y.get("@status") == "Complete"] or year_entries
        if complete_years:
            try:
                latest_year = max(complete_years, key=lambda y: int(y.get("@year", 0)))
                infos = (
                    latest_year.get("citeScoreInformationList", [{}])[0].get("citeScoreInfo", [])
                )
                if infos:
                    ranks = infos[0].get("citeScoreSubjectRank", [])
                    percentiles = [
                        int(r["percentile"]) for r in ranks if "percentile" in r and str(r["percentile"]).isdigit()
                    ]
                    if percentiles:
                        result["journal_percentile"] = float(max(percentiles))
                    # If the current-year metric was missing, fall back to the latest complete CiteScore
                    if result["cite_score"] is None:
                        cs_val = infos[0].get("citeScore")
                        if cs_val is not None:
                            try:
                                result["cite_score"] = float(cs_val)
                            except (ValueError, TypeError):
                                pass
            except (ValueError, TypeError, KeyError, IndexError):
                pass

        # Subject areas
        subject_areas = entry.get("subject-area", [])
        if isinstance(subject_areas, list):
            result["subject_areas"] = [a.get("$", "") for a in subject_areas if a.get("$")]
        elif isinstance(subject_areas, dict) and subject_areas.get("$"):
            result["subject_areas"] = [subject_areas["$"]]

        return result


# Global instance
_scopus_service: Optional[ScopusCitationService] = None


def get_scopus_service() -> ScopusCitationService:
    """Get or create the global Scopus service instance."""
    global _scopus_service
    if _scopus_service is None:
        _scopus_service = ScopusCitationService()
    return _scopus_service


def get_citation_count(pmid: Optional[str] = None, doi: Optional[str] = None) -> int:
    """
    Convenience function to get citation count from Scopus.
    
    Args:
        pmid: PubMed ID (optional)
        doi: Digital Object Identifier (optional)
        
    Returns:
        Citation count (0 if not found or error)
    """
    service = get_scopus_service()
    
    if not service.enabled:
        return 0
    
    # Try PMID first
    if pmid:
        count = service.get_citation_count_by_pmid(pmid)
        if count is not None:
            return count
    
    # Fallback to DOI
    if doi:
        count = service.get_citation_count_by_doi(doi)
        if count is not None:
            return count
    
    return 0
