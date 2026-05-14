"""
PubMed PDF serving endpoints, search endpoint, and Scopus citation metrics.
"""
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Path as PathParam, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from ..auth.dependencies import get_current_user_id
from ..config import settings
from . import service as pubmed_service
from .pdf_downloader import (
    PDF_STORAGE_DIR as DOWNLOADS_DIR,
    download_pdf_async,
    get_pdf_path,
)
from .scopus_service import get_scopus_service

router = APIRouter(prefix="/api/pubmed", tags=["pubmed"])

# All persisted PDFs live under this resolved root. We compare resolved paths
# against this prefix on every read so that a malicious `pmid`/`doi` cannot
# escape the directory via path traversal (audit S4).
PDF_STORAGE_DIR = DOWNLOADS_DIR.resolve()

# PubMed IDs are positive integers, typically 1-9 digits. Reject anything else
# before passing the value to file-system code (audit S4, S5).
_PMID_RE = re.compile(r"^\d{1,12}$")
# DOIs are ASCII printable; reject any control / path characters explicitly so
# they can never end up in a constructed file path. We don't validate full DOI
# syntax — Crossref allows unicode in some cases — only that it's safe to log
# and to feed into a hash for the cache key.
_DOI_BLOCK_RE = re.compile(r"[\x00-\x1f\x7f/\\]")
# PMC IDs: optional "PMC" prefix + digits.
_PMC_RE = re.compile(r"^(?:PMC)?\d{1,12}$", re.IGNORECASE)


def _validate_pmid(pmid: str) -> str:
    if not _PMID_RE.match(pmid or ""):
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_pmid", "message": "PMID must be a positive integer"},
        )
    return pmid


def _validate_doi(doi: str) -> str:
    if not doi:
        return ""
    if _DOI_BLOCK_RE.search(doi) or len(doi) > 256:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_doi", "message": "DOI contains invalid characters"},
        )
    return doi


def _validate_pmc(pmc_id: str) -> str:
    if not pmc_id:
        return ""
    if not _PMC_RE.match(pmc_id) or len(pmc_id) > 32:
        raise HTTPException(
            status_code=400,
            detail={"error": "invalid_pmc_id", "message": "Invalid PMC identifier"},
        )
    return pmc_id


# ---------------------------------------------------------------------------
# REST search endpoint (audit P5) — lets the UI/tests exercise PubMed search
# without going through the LLM agent.
# ---------------------------------------------------------------------------


class PubMedSearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    max_results: int = Field(default=10, ge=1, le=20)
    min_confidence: float = Field(default=settings.pubmed_min_confidence, ge=0.0, le=100.0)


@router.post("/search")
async def endpoint_pubmed_search(
    body: PubMedSearchRequest,
    _user_id: str = Depends(get_current_user_id),
):
    """Run a PubMed search and return ranked articles. Auth-protected."""
    result = pubmed_service.search_pubmed(
        query=body.query,
        max_results=body.max_results,
        min_confidence=body.min_confidence,
    )
    return result.model_dump()


@router.get("/pdf/{pmid}")
async def serve_pubmed_pdf(
    pmid: str = PathParam(..., pattern=r"^\d{1,12}$"),
    doi: str = Query(default="", description="DOI for fallback download"),
    pmc_id: str = Query(default="", description="PubMed Central ID (e.g., PMC7234567)"),
    _user_id: str = Depends(get_current_user_id),
) -> FileResponse:
    """Serve a PubMed PDF. Downloads if not cached.

    Inputs are validated so a malicious PMID/DOI cannot traverse out of the
    downloads directory (audit S4, S5).
    """
    pmid = _validate_pmid(pmid)
    doi = _validate_doi(doi)
    pmc_id = _validate_pmc(pmc_id)

    # Check if already downloaded
    pdf_path = get_pdf_path(pmid, doi)

    # If not cached, download now
    if not pdf_path:
        pdf_path = await download_pdf_async(pmid, doi, pmc_id=pmc_id)

    if not pdf_path or not pdf_path.exists():
        raise HTTPException(
            status_code=404,
            detail={
                "error": "pdf_not_available",
                "message": (
                    f"PDF not available for PMID {pmid}. "
                    "This article may not have a free full-text version."
                ),
                "pmid": pmid,
                "suggestion": (
                    "Try articles from PubMed Central (PMC) or open-access journals. "
                    "You can view the abstract on PubMed."
                ),
            },
        )

    # Defence-in-depth: ensure the resolved path stays inside the downloads dir.
    resolved = pdf_path.resolve()
    try:
        resolved.relative_to(PDF_STORAGE_DIR)
    except ValueError:
        raise HTTPException(status_code=404, detail="PDF not found")

    return FileResponse(
        path=str(resolved),
        media_type="application/pdf",
        filename=f"pubmed_{pmid}.pdf",
        headers={"Content-Disposition": f'inline; filename="pubmed_{pmid}.pdf"'},
    )


@router.get("/pdf/check/{pmid}")
async def check_pdf_availability(
    pmid: str = PathParam(..., pattern=r"^\d{1,12}$"),
    doi: str = Query(default="", description="DOI for identification"),
    _user_id: str = Depends(get_current_user_id),
) -> dict:
    """
    Check if a PDF is available *for sure*.

    Returns `available: True` only when the PDF is already cached on disk.
    The previous version returned `True` unconditionally (audit P6) which
    misled the frontend. For uncached articles, return `available: False`
    with a hint that the caller can attempt a download via `/pdf/{pmid}`.
    """
    pmid = _validate_pmid(pmid)
    doi = _validate_doi(doi)

    pdf_path = get_pdf_path(pmid, doi)
    pdf_url = f"/api/pubmed/pdf/{pmid}" + (f"?doi={doi}" if doi else "")

    if pdf_path and pdf_path.exists():
        return {"available": True, "cached": True, "url": pdf_url}

    return {
        "available": False,
        "cached": False,
        "url": pdf_url,
        "note": "PDF is not cached locally. Calling the URL will trigger an on-demand download attempt.",
    }


@router.get("/scopus/citation/{pmid}")
async def get_scopus_citation_count(
    pmid: str = PathParam(..., pattern=r"^\d{1,12}$"),
    doi: str = Query(default="", description="DOI for fallback lookup"),
    _user_id: str = Depends(get_current_user_id),
) -> dict:
    """Get citation count from Scopus API for a PubMed article."""
    pmid = _validate_pmid(pmid)
    doi = _validate_doi(doi)

    scopus_service = get_scopus_service()

    if not scopus_service.enabled:
        return {
            "pmid": pmid,
            "citation_count": 0,
            "source": "unavailable",
            "enabled": False,
            "message": "Scopus API key not configured",
        }

    citation_count = scopus_service.get_citation_count_by_pmid(pmid)

    if citation_count is None and doi:
        citation_count = scopus_service.get_citation_count_by_doi(doi)

    if citation_count is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "article_not_found",
                "message": f"Article not found in Scopus database for PMID {pmid}",
                "pmid": pmid,
            },
        )

    return {
        "pmid": pmid,
        "citation_count": citation_count,
        "source": "scopus",
        "enabled": True,
    }


@router.get("/scopus/metrics/{pmid}")
async def get_scopus_article_metrics(
    pmid: str = PathParam(..., pattern=r"^\d{1,12}$"),
    doi: str = Query(default="", description="DOI for fallback lookup"),
    _user_id: str = Depends(get_current_user_id),
) -> dict:
    """Get comprehensive article metrics from Scopus API."""
    pmid = _validate_pmid(pmid)
    doi = _validate_doi(doi)

    scopus_service = get_scopus_service()

    if not scopus_service.enabled:
        raise HTTPException(
            status_code=503,
            detail={"error": "service_unavailable", "message": "Scopus API key not configured"},
        )

    metrics = scopus_service.get_article_metrics(pmid=pmid, doi=doi or None)

    if not metrics:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "article_not_found",
                "message": f"Article not found in Scopus database for PMID {pmid}",
                "pmid": pmid,
            },
        )

    return {**metrics, "source": "scopus"}


@router.get("/scopus/status")
async def get_scopus_status(
    _user_id: str = Depends(get_current_user_id),
) -> dict:
    """Check Scopus API configuration status."""
    scopus_service = get_scopus_service()
    return {
        "enabled": scopus_service.enabled,
        "configured": bool(settings.scopus_api_key),
        "use_for_citations": settings.scopus_use_for_citations,
    }
