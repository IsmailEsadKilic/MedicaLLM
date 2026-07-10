from __future__ import annotations
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session

from ..config import settings
from .sql_models import Base

from logging import getLogger
logger = getLogger(__name__)

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        # Validate that we have a connection string before SQLAlchemy tries to
        # parse one. `create_engine("")` raises a confusing error several
        # frames deep; failing fast here gives operators a clear message
        # (audit I10).
        if not settings.postgres_url:
            raise RuntimeError(
                "Database is not configured: set DO_POSTGRES_URL (or POSTGRES_URL) "
                "in the environment to a valid postgresql:// connection string."
            )
        # Managed Postgres providers (DigitalOcean, Supabase, Neon, RDS) drop
        # idle TCP connections server-side after a few minutes. Without
        # pool_recycle, SQLAlchemy keeps handing out dead sockets; the next
        # query then stalls up to 60s on TCP/SSL re-handshake before failing
        # over. This manifested as "random 60s hangs" where a single query
        # would take ~60s while the DB itself answered in <200ms.
        #
        # Settings:
        #   pool_recycle=180      — close & reopen any connection older than
        #                           3 min; stays well under DO's ~600s idle
        #                           timeout.
        #   pool_pre_ping=True    — cheap SELECT 1 before handing out a
        #                           connection; catches any recycle we miss.
        #   pool_timeout=10       — don't queue indefinitely when the pool is
        #                           saturated; fail fast so the request can
        #                           surface a 500 instead of hanging forever.
        #   connect_timeout=10    — bound the TCP/SSL handshake; if the
        #                           server is unreachable we return in 10s,
        #                           not 60-120s.
        # SSL mode is configurable so local Postgres (which usually has no
        # SSL) works alongside managed cloud Postgres (which requires it).
        # Managed providers → "require"; a plain local/docker Postgres →
        # "disable" or "prefer". Controlled by the DB_SSLMODE env var,
        # defaulting to "require" to stay safe for cloud deployments.
        # If the connection URL already carries ?sslmode=..., libpq honours
        # that and we leave connect_args' sslmode out to avoid a conflict.
        sslmode = settings.db_sslmode
        connect_args = {
            "connect_timeout": 10,
            # Skip GSSAPI/Kerberos negotiation entirely. libpq tries GSSAPI
            # before SSL by default, and when the server has no Kerberos
            # (DigitalOcean, RDS, Supabase, most managed PGs) the client
            # still waits out the full GSSAPI timeout on every fresh
            # connection. Turning this off eliminates the dominant
            # cold-connect cost we observed (~60s/attempt).
            "gssencmode": "disable",
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 3,
        }
        # Only inject sslmode if the URL doesn't already specify one.
        if "sslmode=" not in (settings.postgres_url or ""):
            connect_args["sslmode"] = sslmode

        _engine = create_engine(
            settings.postgres_url,
            echo=False,
            pool_size=10,
            max_overflow=20,
            pool_recycle=180,
            pool_pre_ping=True,
            pool_timeout=10,
            connect_args=connect_args,
        )

        @event.listens_for(_engine, "connect")
        def _on_connect(dbapi_conn, conn_record):
            logger.debug("[DB] New connection established")

        @event.listens_for(_engine, "checkout")
        def _on_checkout(dbapi_conn, conn_record, conn_proxy):
            logger.debug("[DB] Connection checked out from pool")

    return _engine


def get_session_factory() -> sessionmaker:
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine(), expire_on_commit=False)
    return _SessionLocal


def get_session() -> Session:
    """
    Create a new SQLAlchemy session. Caller is responsible for closing it.
    """
    return get_session_factory()()


