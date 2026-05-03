"""
PubMed PDF serving endpoints and Scopus citation metrics.
"""
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from ..auth.dependencies import get_current_user_id
from ..config import settings
from .pdf_downloader import get_pdf_path, download_pdf_async
from .scopus_service import get_scopus_service

router = APIRouter(prefix="/api/pubmed", tags=["pubmed"])

PDF_STORAGE_DIR = Path(settings.pdf_dir) / "pubmed_downloads"


@router.get("/pdf/{pmid}")
async def serve_pubmed_pdf(
    pmid: str,
    doi: str = Query(default="", description="DOI for fallback download"),
    pmc_id: str = Query(default="", description="PubMed Central ID (e.g., PMC7234567)"),
    _user_id: str = Depends(get_current_user_id),
) -> FileResponse:
    """
    Serve a PubMed PDF. Downloads if not cached.
    
    Args:
        pmid: PubMed ID
        doi: Optional DOI for download fallback
        pmc_id: Optional PubMed Central ID (e.g., PMC7234567)
    
    Returns:
        PDF file response
    
    Note:
        Not all PubMed articles have free full-text PDFs available.
        Articles behind paywalls or without open access will fail to download.
        Articles with PMC IDs have higher success rates.
    """
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
                "message": f"PDF not available for PMID {pmid}. This article may not have a free full-text version.",
                "pmid": pmid,
                "suggestion": "Try articles from PubMed Central (PMC) or open access journals. You can view the abstract on PubMed."
            }
        )
    
    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=f"pubmed_{pmid}.pdf",
        headers={"Content-Disposition": f'inline; filename="pubmed_{pmid}.pdf"'},
    )


@router.get("/pdf/check/{pmid}")
async def check_pdf_availability(
    pmid: str,
    doi: str = Query(default="", description="DOI for identification"),
    _user_id: str = Depends(get_current_user_id),
) -> dict:
    """
    Check if a PDF is available (cached or downloadable).
    
    Returns:
        {
            "available": bool,
            "cached": bool,
            "url": str (if available)
        }
    """
    pdf_path = get_pdf_path(pmid, doi)
    
    if pdf_path and pdf_path.exists():
        return {
            "available": True,
            "cached": True,
            "url": f"/api/pubmed/pdf/{pmid}{'?doi=' + doi if doi else ''}"
        }
    
    # Could add logic here to check if PDF is downloadable
    # For now, assume it might be available
    return {
        "available": True,  # Optimistic - will try to download on request
        "cached": False,
        "url": f"/api/pubmed/pdf/{pmid}{'?doi=' + doi if doi else ''}"
    }



@router.get("/scopus/citation/{pmid}")
async def get_scopus_citation_count(
    pmid: str,
    doi: str = Query(default="", description="DOI for fallback lookup"),
    _user_id: str = Depends(get_current_user_id),
) -> dict:
    """
    Get citation count from Scopus API for a PubMed article.
    
    Args:
        pmid: PubMed ID
        doi: Optional DOI for fallback lookup
    
    Returns:
        {
            "pmid": str,
            "citation_count": int,
            "source": "scopus" | "unavailable",
            "enabled": bool
        }
    """
    scopus_service = get_scopus_service()
    
    if not scopus_service.enabled:
        return {
            "pmid": pmid,
            "citation_count": 0,
            "source": "unavailable",
            "enabled": False,
            "message": "Scopus API key not configured"
        }
    
    # Try PMID first
    citation_count = scopus_service.get_citation_count_by_pmid(pmid)
    
    # Fallback to DOI if provided and PMID lookup failed
    if citation_count is None and doi:
        citation_count = scopus_service.get_citation_count_by_doi(doi)
    
    if citation_count is None:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "article_not_found",
                "message": f"Article not found in Scopus database for PMID {pmid}",
                "pmid": pmid
            }
        )
    
    return {
        "pmid": pmid,
        "citation_count": citation_count,
        "source": "scopus",
        "enabled": True
    }


@router.get("/scopus/metrics/{pmid}")
async def get_scopus_article_metrics(
    pmid: str,
    doi: str = Query(default="", description="DOI for fallback lookup"),
    _user_id: str = Depends(get_current_user_id),
) -> dict:
    """
    Get comprehensive article metrics from Scopus API.
    
    Args:
        pmid: PubMed ID
        doi: Optional DOI for fallback lookup
    
    Returns:
        {
            "pmid": str,
            "citation_count": int,
            "scopus_id": str,
            "eid": str,
            "title": str,
            "publication_name": str,
            "cover_date": str,
            "doi": str,
            "author_count": int,
            "affiliation_count": int,
            "subject_areas": list[str],
            "source": "scopus"
        }
    """
    scopus_service = get_scopus_service()
    
    if not scopus_service.enabled:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "service_unavailable",
                "message": "Scopus API key not configured"
            }
        )
    
    # Get comprehensive metrics
    metrics = scopus_service.get_article_metrics(pmid=pmid, doi=doi or None)
    
    if not metrics:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "article_not_found",
                "message": f"Article not found in Scopus database for PMID {pmid}",
                "pmid": pmid
            }
        )
    
    return {
        **metrics,
        "source": "scopus"
    }


@router.get("/scopus/status")
async def get_scopus_status(
    _user_id: str = Depends(get_current_user_id),
) -> dict:
    """
    Check Scopus API configuration status.
    
    Returns:
        {
            "enabled": bool,
            "configured": bool,
            "use_for_citations": bool
        }
    """
    scopus_service = get_scopus_service()
    
    return {
        "enabled": scopus_service.enabled,
        "configured": bool(settings.scopus_api_key),
        "use_for_citations": settings.scopus_use_for_citations
    }
