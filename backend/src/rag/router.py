from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse

from ..auth.dependencies import get_current_user_id
from ..config import settings

ABS_PDF_DIR = Path(settings.pdf_dir).resolve()

router = APIRouter(prefix="/api/pdf", tags=["pdf"])


def _resolve_pdf_path(source: str) -> Path:
    """
    Given an arbitrary source string (which may be an absolute path, a relative
    path, or just a bare filename), locate the actual PDF file inside
    ABS_PDF_DIR and return its resolved Path.

    Raises HTTPException 404 when the file cannot be found.
    """
    #* Normalise Windows-style backslashes so that Path.name works on Linux.
    source = source.replace("\\", "/")
    #* Strip any directory components the caller may have included.
    bare_name = Path(source).name

    if not bare_name or bare_name in (".", ".."):
        raise HTTPException(status_code=400, detail="Invalid source filename")

    #* Walk to find the first matching filename.
    for dirpath, _dirs, filenames in os.walk(ABS_PDF_DIR):
        if bare_name in filenames:
            candidate = (Path(dirpath) / bare_name).resolve()
            #* Confirm it is still inside ABS_PDF_DIR (prevents symlink escapes).
            try:
                candidate.relative_to(ABS_PDF_DIR)
            except ValueError:
                raise HTTPException(status_code=403, detail="Access denied")
            return candidate

    raise HTTPException(
        status_code=404,
        detail=f"PDF file '{bare_name}' not found in the document store",
    )


@router.get("/serve")
async def serve_pdf(
    source: str = Query(..., description="Source path or filename of the PDF to serve"),
    _user_id: str = Depends(get_current_user_id),
) -> FileResponse:
    pdf_path = _resolve_pdf_path(source)

    return FileResponse(
        path=str(pdf_path),
        media_type="application/pdf",
        filename=pdf_path.name,
        headers={"Content-Disposition": f"inline; filename=\"{pdf_path.name}\""},
    )
