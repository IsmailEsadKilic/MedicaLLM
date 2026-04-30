"""
SQLAlchemy engine and session factory for the drug catalog database (PostgreSQL).
"""

from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from ..config import settings
from ....legacy import printmeup as pm
from .sql_models import Base

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        _engine = create_engine(
            settings.postgres_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
        )
    return _engine


def get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionLocal


def get_session() -> Session:
    """Create a new SQLAlchemy session. Caller is responsible for closing it."""
    return get_session_factory()()


def init_sql_db() -> None:
    """Create all SQL tables if they don't exist yet."""
    engine = get_engine()
    Base.metadata.create_all(engine)
    pm.suc("PostgreSQL drug catalog tables initialized")
