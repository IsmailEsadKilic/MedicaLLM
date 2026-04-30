
# ok
import asyncio
import threading
from cachetools import TTLCache
from fastapi import HTTPException

from ..agent.agent import MedicalAgent
from ....legacy import printmeup as pm
from ..conversations import service as conv_service
from .session import Session
from ..config import settings

class SessionManager:

    def __init__(
        self,
        max_sessions: int = settings.max_n_sessions,
        ttl_seconds: int = settings.session_ttl_seconds,
    ) -> None:
        self._cache: TTLCache = TTLCache(maxsize=max_sessions, ttl=ttl_seconds)
        self._lock = threading.Lock()
        self._max_sessions = max_sessions
        self._ttl_seconds = ttl_seconds

    def get(self, conversation_id: str) -> Session | None:
        with self._lock:
            session: Session | None = self._cache.get(conversation_id)
            if session is not None:
                pm.inf(f"Session cache hit: {conversation_id}")
            return session

    def create(self, conversation_id: str, agent: MedicalAgent) -> Session:
        conversation = conv_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")

        new_session = Session(
            conversation_id=conversation_id,
            user_id=conversation.user_id,
            agent=agent,
        )

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

    def get_or_create(self, conversation_id: str, agent: MedicalAgent) -> Session:
        """
        Retrieves an existing session or creates a new one.
        """
        session = self.get(conversation_id)
        if session is not None:
            return session
        
        return self.create(conversation_id, agent)

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
