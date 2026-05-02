from __future__ import annotations
from typing import Literal, Any, List
from datetime import datetime
import uuid
from pydantic import BaseModel, Field

from ..config import settings

class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    tools_used: List[str] = [] # linked by index to tool_results
    tool_results: List[str] = []
    sources: List[str] = []


class Conversation(BaseModel):
    conversation_id: str
    user_id: str
    title: str = settings.default_conversation_title
    messages: List[Message] = []
    created_at: str
    updated_at: str

    @classmethod
    def create_new(cls, user_id: str, title: str = settings.default_conversation_title):
        now = datetime.now().isoformat()
        return cls(
            conversation_id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            messages=[],
            created_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, d: dict) -> Conversation:
        return cls.model_validate(d)

    @property
    def last_message(self) -> Message | None:
        return self.messages[-1] if self.messages else None
    
    def get_last_messages(self, n: int = 2) -> List[Message]:
        return self.messages[-n:] if self.messages else []

    @property
    def message_count(self) -> int:
        return len(self.messages)
    
class CreateConversationRequest(BaseModel):
    title: str = settings.default_conversation_title

class UpdateTitleRequest(BaseModel):
    title: str

class AddMessageRequest(BaseModel):
    message: dict