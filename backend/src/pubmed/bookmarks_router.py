"""Saved articles / bookmarks endpoints."""
from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from ..auth.dependencies import get_current_user_id
from ..db.sql_client import get_session
from ..db.sql_models import SavedArticle, UserRecord

router = APIRouter(prefix="/api/bookmarks", tags=["bookmarks"])


class BookmarkRequest(BaseModel):
    pmid: str
    title: str = ""
    authors: str = ""
    journal: str = ""
    publication_date: str = ""
    doi: str = ""
    abstract: str = ""


class BookmarkResponse(BaseModel):
    id: int
    pmid: str
    title: str
    authors: str
    journal: str
    publication_date: str
    doi: str
    abstract: str
    saved_at: str


@router.post("", response_model=BookmarkResponse)
def save_article(req: BookmarkRequest, user_id: str = Depends(get_current_user_id)):
    session = get_session()
    try:
        user = session.query(UserRecord).filter(UserRecord.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        # Check if already saved
        existing = session.query(SavedArticle).filter(
            SavedArticle.user_pk == user.id,
            SavedArticle.pmid == req.pmid
        ).first()
        if existing:
            raise HTTPException(status_code=409, detail="Article already bookmarked")

        article = SavedArticle(
            user_pk=user.id,
            pmid=req.pmid,
            title=req.title,
            authors=req.authors,
            journal=req.journal,
            publication_date=req.publication_date,
            doi=req.doi,
            abstract=req.abstract,
            saved_at=datetime.now().isoformat(),
        )
        session.add(article)
        session.commit()
        session.refresh(article)
        return BookmarkResponse(
            id=article.id, pmid=article.pmid, title=article.title,
            authors=article.authors, journal=article.journal,
            publication_date=article.publication_date, doi=article.doi,
            abstract=article.abstract, saved_at=article.saved_at,
        )
    finally:
        session.close()


@router.get("", response_model=List[BookmarkResponse])
def list_bookmarks(user_id: str = Depends(get_current_user_id)):
    session = get_session()
    try:
        user = session.query(UserRecord).filter(UserRecord.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        articles = session.query(SavedArticle).filter(
            SavedArticle.user_pk == user.id
        ).order_by(SavedArticle.id.desc()).all()
        return [
            BookmarkResponse(
                id=a.id, pmid=a.pmid, title=a.title,
                authors=a.authors, journal=a.journal,
                publication_date=a.publication_date, doi=a.doi,
                abstract=a.abstract, saved_at=a.saved_at,
            ) for a in articles
        ]
    finally:
        session.close()


@router.delete("/{pmid}")
def remove_bookmark(pmid: str, user_id: str = Depends(get_current_user_id)):
    session = get_session()
    try:
        user = session.query(UserRecord).filter(UserRecord.user_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        article = session.query(SavedArticle).filter(
            SavedArticle.user_pk == user.id,
            SavedArticle.pmid == pmid
        ).first()
        if not article:
            raise HTTPException(status_code=404, detail="Bookmark not found")
        session.delete(article)
        session.commit()
        return {"detail": "Bookmark removed"}
    finally:
        session.close()
