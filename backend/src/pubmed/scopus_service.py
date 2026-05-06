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
            }
            
            # Get detailed metrics from Abstract Retrieval API if we have a Scopus ID
            scopus_id = metrics["scopus_id"]
            if scopus_id:
                detailed_data = self._get_abstract_details(scopus_id)
                if detailed_data:
                    # Update with detailed metrics
                    detailed_metrics = self._extract_detailed_metrics(detailed_data)
                    metrics.update(detailed_metrics)
                elif not ScopusCitationService._abstract_api_warning_shown:
                    # Show warning once if Abstract API is not accessible
                    logger.info("[SCOPUS] Abstract Retrieval API not accessible with current API key. "
                              "FWCI and detailed journal metrics will not be available. "
                              "This is normal for basic Scopus API keys.")
                    ScopusCitationService._abstract_api_warning_shown = True
            
            # Get journal metrics (CiteScore, SJR, SNIP) from search data
            journal_metrics = self._get_journal_metrics(article_data)
            metrics.update(journal_metrics)
            
            # Get article-level metrics (FWCI) from search data (usually not present)
            article_level_metrics = self._get_article_level_metrics(article_data)
            metrics.update(article_level_metrics)
            
            logger.debug(f"[SCOPUS] Retrieved metrics for article: {metrics['title'][:50]}...")
            return metrics
            
        except Exception as e:
            logger.warning(f"[SCOPUS] Failed to fetch article metrics: {e}")
            return None
    
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
        
        # Rate limiting - Scopus allows different rates based on subscription
        # Standard rate: 2 requests per second
        time.sleep(0.5)
        
        url = f"{self.BASE_URL}/search/scopus"
        params = {
            "query": query,
            "apiKey": self.api_key,
            "httpAccept": "application/json",
            "count": 1,  # We only need the first result
        }
        
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        
        logger.debug(f"[SCOPUS] Searching: {query}")
        
        req = urllib.request.Request(
            full_url,
            headers={
                "Accept": "application/json",
                "User-Agent": "MedicaLLM/1.0"
            }
        )
        
        try:
            with urllib.request.urlopen(req, timeout=2) as response:
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
        
        # Rate limiting
        time.sleep(0.5)
        
        url = f"{self.BASE_URL}/abstract/scopus_id/{scopus_id}"
        params = {
            "apiKey": self.api_key,
            "httpAccept": "application/json",
            "view": "FULL",  # Get full details including metrics
        }
        
        full_url = f"{url}?{urllib.parse.urlencode(params)}"
        
        logger.debug(f"[SCOPUS] Fetching abstract details for Scopus ID: {scopus_id}")
        
        req = urllib.request.Request(
            full_url,
            headers={
                "Accept": "application/json",
                "User-Agent": "MedicaLLM/1.0"
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
