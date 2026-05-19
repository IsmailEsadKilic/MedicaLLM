"""
OpenAlex integration — free, no-auth fallback for article-level metrics.

Provides FWCI (Field-Weighted Citation Impact) and citation percentile
when Scopus Abstract Retrieval API is not accessible with the current key.

Docs: https://docs.openalex.org/
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from logging import getLogger
from typing import Any, Dict, Optional

from ..config import settings

logger = getLogger(__name__)


class OpenAlexService:
    """Fetches article-level metrics from OpenAlex (free, no API key required)."""

    BASE_URL = "https://api.openalex.org"

    def __init__(self, email: Optional[str] = None, enabled: Optional[bool] = None):
        self.email = email or settings.openalex_email or settings.pubmed_email
        self.enabled = settings.openalex_enabled if enabled is None else enabled
        # Simple per-process cache keyed by (pmid|doi)
        self._cache: Dict[str, Optional[Dict[str, Any]]] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_article_metrics(
        self, pmid: Optional[str] = None, doi: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Fetch article-level metrics from OpenAlex.

        Returns a dict with these keys (any of which may be None):
            - fwci: float | None
            - citation_normalized_percentile: float | None  (0-1 scale)
            - cited_by_count: int | None
            - openalex_id: str

        Prefers PMID lookup (most precise), falls back to DOI.
        """
        if not self.enabled:
            return None
        if not pmid and not doi:
            return None

        cache_key = f"pmid:{pmid}" if pmid else f"doi:{doi}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        data = None
        if pmid:
            data = self._fetch(f"{self.BASE_URL}/works/pmid:{pmid}")
        if data is None and doi:
            # URL-encode DOI properly
            data = self._fetch(f"{self.BASE_URL}/works/doi:{urllib.parse.quote(doi, safe='')}")

        if data is None:
            self._cache[cache_key] = None
            return None

        parsed = self._parse(data)
        self._cache[cache_key] = parsed
        return parsed

    def get_batch_metrics(self, pmids: list[str]) -> Dict[str, Dict[str, Any]]:
        """
        Batch-fetch article metrics for multiple PMIDs in a single API call.
        
        Uses OpenAlex filter API: /works?filter=pmid:X|Y|Z
        Much faster than individual calls (1 request vs N requests).
        
        Args:
            pmids: List of PubMed IDs (max ~50 per call)
            
        Returns:
            Dict mapping PMID -> metrics dict
        """
        if not self.enabled or not pmids:
            return {}

        # Audit P16: OpenAlex's filter expects bare digits. Inputs like
        # "PMID:12345" or "  012345" silently return zero results. We
        # canonicalise here (strip leading zeros / non-digits) and keep a
        # mapping back to the original key so the result dict matches
        # whatever the caller provided.
        normalised: list[str] = []
        original_to_norm: Dict[str, str] = {}
        for raw in pmids:
            digits = "".join(ch for ch in str(raw) if ch.isdigit()).lstrip("0")
            if digits:
                normalised.append(digits)
                original_to_norm[raw] = digits

        if not normalised:
            return {}

        results: Dict[str, Dict[str, Any]] = {}
        uncached: list[str] = []

        # Check cache first (cache keys use the canonical form)
        for pmid in normalised:
            cache_key = f"pmid:{pmid}"
            if cache_key in self._cache and self._cache[cache_key] is not None:
                results[pmid] = self._cache[cache_key]
            else:
                uncached.append(pmid)
        
        if uncached:
            # OpenAlex filter supports pipe-separated PMIDs
            # Format: filter=ids.pmid:X|Y|Z (just numbers, pipe-separated)
            # Max ~50 per request (URL length)
            BATCH_SIZE = 50
            for i in range(0, len(uncached), BATCH_SIZE):
                batch = uncached[i:i + BATCH_SIZE]
                filter_str = "ids.pmid:" + "|".join(batch)
                url = f"{self.BASE_URL}/works?filter={filter_str}&per_page={len(batch)}"

                data = self._fetch(url)
                if data and "results" in data:
                    for work in data["results"]:
                        parsed = self._parse(work)
                        # Extract PMID from the work's ids
                        work_pmid = self._extract_pmid_from_work(work)
                        if work_pmid:
                            results[work_pmid] = parsed
                            self._cache[f"pmid:{work_pmid}"] = parsed

                # Mark unfound PMIDs as None in cache
                found_pmids = set(results.keys())
                for pmid in batch:
                    if pmid not in found_pmids:
                        self._cache[f"pmid:{pmid}"] = None

        # Map results back to whatever key the caller used.
        out: Dict[str, Dict[str, Any]] = {}
        for raw, norm in original_to_norm.items():
            if norm in results:
                out[raw] = results[norm]
        return out

    @staticmethod
    def _extract_pmid_from_work(work: Dict[str, Any]) -> Optional[str]:
        """Extract PMID from an OpenAlex work object."""
        ids = work.get("ids", {})
        pmid_url = ids.get("pmid", "")
        # Format: "https://pubmed.ncbi.nlm.nih.gov/36494145"
        if pmid_url:
            return pmid_url.rstrip("/").split("/")[-1]
        return None

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    def _fetch(self, url: str) -> Optional[Dict[str, Any]]:
        """GET a single OpenAlex work, with polite-pool email param and retries."""
        # OpenAlex recommends using ?mailto=<email> for the "polite pool"
        sep = "&" if "?" in url else "?"
        full_url = f"{url}{sep}mailto={urllib.parse.quote(self.email or '')}" if self.email else url

        headers = {"Accept": "application/json", "User-Agent": "MedicaLLM/1.0"}

        # Light rate limiting to stay well under OpenAlex's 10 req/sec polite cap
        time.sleep(0.1)

        for attempt in range(3):
            try:
                req = urllib.request.Request(full_url, headers=headers)
                # Reduced timeout from 3s to 2s for faster response
                with urllib.request.urlopen(req, timeout=2) as response:
                    return json.loads(response.read().decode())
            except urllib.error.HTTPError as e:
                if e.code == 429 and attempt < 2:
                    retry_after = e.headers.get("Retry-After", "")
                    try:
                        sleep = min(float(retry_after), 5.0) if retry_after else 1.0
                    except ValueError:
                        sleep = 1.0
                    logger.warning(f"[OPENALEX] Rate limit hit, retry {attempt+1}/3 in {sleep:.1f}s")
                    time.sleep(sleep)
                    continue
                if e.code == 404:
                    logger.debug(f"[OPENALEX] Not found: {url}")
                elif e.code >= 500 and attempt < 2:
                    time.sleep(0.1)
                    continue
                else:
                    logger.warning(f"[OPENALEX] HTTP {e.code} for {url}: {e.reason}")
                return None
            except Exception as e:
                # Don't retry on timeout - fail fast
                if attempt < 2 and "timed out" not in str(e).lower():
                    time.sleep(0.1)
                    continue
                logger.warning(f"[OPENALEX] Request failed for {url}: {e}")
                return None
        return None

    @staticmethod
    def _parse(work: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metrics from a `/works/{id}` payload."""
        percentile_obj = work.get("citation_normalized_percentile") or {}
        raw_percentile = percentile_obj.get("value")

        # Normalize percentile to None if missing, else to 0-1 float
        try:
            percentile = float(raw_percentile) if raw_percentile is not None else None
        except (ValueError, TypeError):
            percentile = None

        try:
            fwci = float(work["fwci"]) if work.get("fwci") is not None else None
        except (ValueError, TypeError):
            fwci = None

        return {
            "fwci": fwci,
            "citation_normalized_percentile": percentile,
            "cited_by_count": work.get("cited_by_count"),
            "openalex_id": (work.get("id") or "").replace("https://openalex.org/", ""),
        }


# Global instance
_openalex_service: Optional[OpenAlexService] = None


def get_openalex_service() -> OpenAlexService:
    """Get or create the global OpenAlex service instance."""
    global _openalex_service
    if _openalex_service is None:
        _openalex_service = OpenAlexService()
    return _openalex_service
