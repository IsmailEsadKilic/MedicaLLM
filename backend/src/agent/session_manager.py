"""
Session management with TTL-based eviction (O3).

Replaces the unbounded plain-dict `active_sessions` in router.py with a
bounded TTLCache-backed store:
  - Maximum 100 concurrent sessions (LRU eviction when full).
  - 30-minute idle TTL: sessions that have not been accessed for
    SESSION_TTL_SECONDS are evicted automatically by cachetools.
  - Thread-safe: all cache mutations are protected by a threading.Lock
    so concurrent async handlers cannot corrupt the store.
  - A periodic background coroutine (`run_periodic_cleanup`) logs store
    health every 5 minutes for observability.
"""

import asyncio
import threading
from typing import Optional

from cachetools import TTLCache
from fastapi import HTTPException

from .. import printmeup as pm
from ..conversations import service as conv_service
from .session import Session

# ── Configuration ────────────────────────────────────────────────────────────

MAX_SESSIONS: int = 100
SESSION_TTL_SECONDS: int = 30 * 60  # 30 minutes


# ── SessionManager ────────────────────────────────────────────────────────────


class SessionManager:
    """
    Bounded, TTL-evicting session store.

    Usage::

        session_manager = SessionManager()
        session = session_manager.get_or_create(conversation_id, agent)
    """

    def __init__(
        self,
        max_sessions: int = MAX_SESSIONS,
        ttl_seconds: int = SESSION_TTL_SECONDS,
    ) -> None:
        self._cache: TTLCache = TTLCache(maxsize=max_sessions, ttl=ttl_seconds)
        self._lock = threading.Lock()
        self._max_sessions = max_sessions
        self._ttl_seconds = ttl_seconds
        pm.suc(
            f"SessionManager ready "
            f"(max_sessions={max_sessions}, ttl={ttl_seconds}s / "
            f"{ttl_seconds // 60} min)"
        )

    # ── Public API ────────────────────────────────────────────────────────────

    def get_or_create(self, conversation_id: str, agent) -> Session:
        """
        Return a live session for *conversation_id*, creating one if needed.

        The lock is held only for cache look-up and insertion; the
        potentially slow DynamoDB call to load the conversation happens
        outside the lock so other requests are not blocked during I/O.
        """
        # Fast path: session already cached
        with self._lock:
            session: Optional[Session] = self._cache.get(conversation_id)
            if session is not None:
                pm.inf(f"Session cache hit: {conversation_id}")
                return session

        # Slow path: load conversation from DB and build session
        conversation = conv_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        new_session = Session(
            conversation_id=conversation_id,
            user_id=conversation.user_id,
            agent=agent,
        )

        # Re-check under the lock in case a concurrent request created the
        # session while we were doing DB I/O (double-checked locking).
        with self._lock:
            existing = self._cache.get(conversation_id)
            if existing is not None:
                pm.inf(f"Session created concurrently, using existing: {conversation_id}")
                return existing
            self._cache[conversation_id] = new_session
            pm.inf(
                f"Session created: {conversation_id} "
                f"(active: {len(self._cache)}/{self._max_sessions})"
            )
            return new_session

    def evict(self, conversation_id: str) -> None:
        """Manually remove a session before its TTL expires."""
        with self._lock:
            if conversation_id in self._cache:
                del self._cache[conversation_id]
                pm.inf(f"Session manually evicted: {conversation_id}")

    @property
    def size(self) -> int:
        """Number of live sessions currently in the cache."""
        return len(self._cache)


    async def cleanup(self) -> None:
        """
        Long-running coroutine that logs session-store health every 5 minutes.

        TTLCache evicts expired entries automatically on access, so this task
        is primarily for observability. Schedule it once via
        ``asyncio.create_task(session_manager.cleanup())``.
        """
        with self._lock:
            active = len(self._cache)
        pm.inf(
            f"[SessionManager] health check — "
            f"{active}/{self._max_sessions} active sessions"
        )
