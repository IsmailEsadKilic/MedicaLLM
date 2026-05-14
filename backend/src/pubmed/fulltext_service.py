"""
Europe PMC full-text service.

Fetches and parses full-text JATS XML for open-access PubMed articles.
Much faster than PDF downloading + parsing, and returns structured sections
(Methods, Results, Discussion, etc.) directly.

Free, no API key required. Only works for articles with open-access full text
in Europe PMC (a significant subset of PubMed).
"""
from __future__ import annotations

import re
import time
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from logging import getLogger
from typing import Dict, List, Optional

logger = getLogger(__name__)


class FullTextService:
    """Fetches open-access full text from Europe PMC."""

    BASE_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest"

    # Sections we care about for clinical reasoning, in priority order.
    # Keys are lowercase section titles; we match partial names.
    SECTION_PRIORITIES = [
        "abstract",
        "introduction",
        "background",
        "methods",
        "materials and methods",
        "results",
        "discussion",
        "conclusion",
        "conclusions",
    ]

    def __init__(self):
        # Per-process cache keyed by pmid-or-pmc-id → parsed sections dict
        self._cache: Dict[str, Optional[Dict[str, str]]] = {}

    def get_full_text(
        self,
        pmid: Optional[str] = None,
        pmc_id: Optional[str] = None,
    ) -> Optional[Dict[str, str]]:
        """
        Fetch full-text sections for an article.

        Args:
            pmid: PubMed ID (preferred when no pmc_id is known)
            pmc_id: PubMed Central ID (e.g., "PMC7234567" or "7234567")

        Returns:
            Dict of section_name → text (lowercase keys), or None if
            full text is not available.
        """
        key = pmc_id or pmid
        if not key:
            return None
        if key in self._cache:
            return self._cache[key]

        # Try PMC ID first (more reliable), fall back to PMID lookup
        pmc_clean = self._normalize_pmc(pmc_id) if pmc_id else None
        if not pmc_clean and pmid:
            # Convert PMID → PMC ID via Europe PMC
            pmc_clean = self._resolve_pmid_to_pmc(pmid)

        if not pmc_clean:
            self._cache[key] = None
            return None

        xml_body = self._fetch_fulltext_xml(pmc_clean)
        if not xml_body:
            self._cache[key] = None
            return None

        sections = self._parse_jats_sections(xml_body)
        self._cache[key] = sections if sections else None
        return self._cache[key]

    def get_batch_full_texts(
        self, articles: List[Dict[str, str]]
    ) -> Dict[str, Dict[str, str]]:
        """
        Batch fetch full texts for multiple articles.

        Args:
            articles: List of {"pmid": str, "pmc_id": str} dicts

        Returns:
            Dict mapping pmid → section dict (only for articles with full text)
        """
        from concurrent.futures import ThreadPoolExecutor

        results: Dict[str, Dict[str, str]] = {}

        def _fetch_one(a):
            pmid = a.get("pmid", "")
            pmc_id = a.get("pmc_id", "")
            if not pmid:
                return None
            sections = self.get_full_text(pmid=pmid, pmc_id=pmc_id)
            return (pmid, sections)

        # Europe PMC allows ~10 req/s; 8 workers keeps us safely under that
        # even when fetching 15+ articles concurrently.
        with ThreadPoolExecutor(max_workers=8) as executor:
            for result in executor.map(_fetch_one, articles):
                if result is None:
                    continue
                pmid, sections = result
                if sections:
                    results[pmid] = sections

        return results

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_pmc(pmc_id: Optional[str]) -> Optional[str]:
        """Return PMC ID in canonical form (e.g., 'PMC7234567')."""
        if not pmc_id:
            return None
        pmc_id = pmc_id.strip()
        if not pmc_id:
            return None
        if not pmc_id.upper().startswith("PMC"):
            pmc_id = f"PMC{pmc_id}"
        return pmc_id.upper()

    def _resolve_pmid_to_pmc(self, pmid: str) -> Optional[str]:
        """
        Use Europe PMC's search API to find the PMC ID for a PubMed article.
        """
        url = (
            f"{self.BASE_URL}/search?query=EXT_ID:{pmid}%20AND%20SRC:MED"
            f"&resultType=lite&format=json"
        )
        body = self._http_get(url, timeout=3.0)
        if not body:
            return None
        try:
            import json

            data = json.loads(body.decode())
            results = data.get("resultList", {}).get("result", [])
            if results:
                pmcid = results[0].get("pmcid")
                if pmcid:
                    return self._normalize_pmc(pmcid)
        except Exception as e:
            logger.debug(f"[EUROPE_PMC] Failed to parse PMID→PMC response: {e}")
        return None

    def _fetch_fulltext_xml(self, pmc_id: str) -> Optional[bytes]:
        """Fetch JATS XML for a PMC article. Returns None on 404 or paywall.

        Audit P18: enforce a hard upper bound on the response body so that
        a malformed / pathological article cannot consume tens of MB of
        memory per request. 8 MB covers even the longest open-access
        articles we've seen (typically <1 MB).
        """
        url = f"{self.BASE_URL}/{pmc_id}/fullTextXML"
        # Shorter timeout per article: full-text XMLs are small (usually <1MB)
        # and we can't afford to block the whole batch on one slow article.
        body = self._http_get(url, timeout=4.0, max_bytes=8 * 1024 * 1024)
        if not body:
            return None
        # Europe PMC sometimes returns an empty body for unavailable articles
        if len(body) < 200:
            return None
        # Check it's actually XML (not an HTML error page)
        if not body.lstrip().startswith(b"<"):
            return None
        return body

    @staticmethod
    def _http_get(url: str, timeout: float = 5.0, max_bytes: int = 8 * 1024 * 1024) -> Optional[bytes]:
        """Simple HTTP GET with retry on 429/5xx only. Timeouts are NOT retried
        (they would double the worst-case latency for a single slow article).

        `max_bytes` (audit P18) caps the in-memory response body. We read in
        chunks and abort once the cap is reached so a malicious or malformed
        upstream response cannot exhaust process memory.
        """
        headers = {"User-Agent": "MedicaLLM/1.0", "Accept": "application/xml"}
        for attempt in range(2):
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=timeout) as response:
                    # Pre-flight: reject responses that announce themselves
                    # as larger than max_bytes. Some servers omit this header
                    # so we still cap the read loop below.
                    declared = response.headers.get("Content-Length")
                    if declared and declared.isdigit() and int(declared) > max_bytes:
                        logger.debug(
                            f"[EUROPE_PMC] Rejecting oversized response "
                            f"({declared} > {max_bytes}) for {url}"
                        )
                        return None
                    chunks: list[bytes] = []
                    read_so_far = 0
                    while True:
                        chunk = response.read(64 * 1024)
                        if not chunk:
                            break
                        read_so_far += len(chunk)
                        if read_so_far > max_bytes:
                            logger.debug(
                                f"[EUROPE_PMC] Truncated streaming download "
                                f"at {max_bytes} bytes for {url}"
                            )
                            return None
                        chunks.append(chunk)
                    return b"".join(chunks)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    return None
                if e.code in (429, 503) and attempt == 0:
                    retry_after = e.headers.get("Retry-After", "")
                    try:
                        sleep = min(float(retry_after), 3.0) if retry_after else 0.8
                    except ValueError:
                        sleep = 0.8
                    logger.debug(f"[EUROPE_PMC] {e.code}, retry in {sleep:.1f}s")
                    time.sleep(sleep)
                    continue
                logger.debug(f"[EUROPE_PMC] HTTP {e.code} for {url}")
                return None
            except (TimeoutError, urllib.error.URLError) as e:
                # Don't retry on timeout — it likely indicates a slow/unavailable
                # article and would just double the worst-case latency.
                logger.debug(f"[EUROPE_PMC] Request timeout/failure for {url}: {e}")
                return None
            except Exception as e:
                logger.debug(f"[EUROPE_PMC] Unexpected error for {url}: {e}")
                return None
        return None

    # ------------------------------------------------------------------
    # JATS XML parsing
    # ------------------------------------------------------------------

    @classmethod
    def _parse_jats_sections(cls, xml_body: bytes) -> Optional[Dict[str, str]]:
        """
        Parse Europe PMC JATS XML and extract named sections.

        Returns a dict like:
            {
                "abstract": "...",
                "introduction": "...",
                "methods": "...",
                "results": "...",
                "discussion": "...",
                "conclusion": "...",
            }
        Only sections actually present are returned.
        """
        try:
            root = ET.fromstring(xml_body)
        except ET.ParseError as e:
            logger.debug(f"[EUROPE_PMC] JATS parse error: {e}")
            return None

        sections: Dict[str, List[str]] = {}

        # Abstract lives under <front><article-meta><abstract>
        for abs_elem in root.iter("abstract"):
            text = cls._extract_text(abs_elem)
            if text:
                sections.setdefault("abstract", []).append(text)

        # Body sections under <body><sec>
        body = root.find("body")
        if body is not None:
            for sec in body.iter("sec"):
                title_elem = sec.find("title")
                title = (
                    cls._extract_text(title_elem).strip().lower()
                    if title_elem is not None
                    else ""
                )
                if not title:
                    continue

                # Match against known section priorities (partial)
                matched_key = None
                for key in cls.SECTION_PRIORITIES:
                    if key in title:
                        matched_key = key
                        break

                # Normalize common aliases
                if matched_key == "materials and methods":
                    matched_key = "methods"
                elif matched_key == "conclusions":
                    matched_key = "conclusion"
                elif matched_key == "background":
                    matched_key = "introduction"

                if matched_key is None:
                    continue

                text = cls._extract_section_text(sec)
                if text:
                    sections.setdefault(matched_key, []).append(text)

        if not sections:
            return None

        # Join repeated section chunks and clean up whitespace
        return {k: cls._clean_whitespace(" ".join(v)) for k, v in sections.items()}

    @staticmethod
    def _extract_text(elem: Optional[ET.Element]) -> str:
        """Get concatenated text content from an element tree, skipping tags."""
        if elem is None:
            return ""
        return " ".join(elem.itertext())

    @classmethod
    def _extract_section_text(cls, sec_elem: ET.Element) -> str:
        """
        Extract the paragraph text from a <sec>, excluding the <title>
        and any nested <table>, <fig>, <xref>, <sec> children
        (nested sections are collected separately at the top level).
        """
        parts: List[str] = []
        for p in sec_elem.findall(".//p"):
            # Skip paragraphs inside captions/tables
            parent_map_tags = {x.tag for x in sec_elem.iter() if p in list(x)}
            if parent_map_tags & {"table", "fig", "caption"}:
                continue
            text = cls._extract_text(p).strip()
            if text:
                parts.append(text)
        return " ".join(parts)

    @staticmethod
    def _clean_whitespace(text: str) -> str:
        """Collapse all whitespace runs to single spaces and trim."""
        return re.sub(r"\s+", " ", text).strip()


# ------------------------------------------------------------------
# Module-level singleton
# ------------------------------------------------------------------

_fulltext_service: Optional[FullTextService] = None


def get_fulltext_service() -> FullTextService:
    global _fulltext_service
    if _fulltext_service is None:
        _fulltext_service = FullTextService()
    return _fulltext_service
