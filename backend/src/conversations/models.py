from __future__ import annotations
from typing import Literal, Any, List, Optional
from datetime import datetime
import uuid
from pydantic import BaseModel, Field


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    tool_used: Optional[str] = None
    tool_result: Optional[Any] = None
    sources: Optional[Any] = None


class Conversation(BaseModel):
    id: str
    user_id: str
    title: str = "Untitled"
    messages: List[Message] = []
    created_at: str
    updated_at: str

    @classmethod
    def create_new(cls, user_id: str, title: str = "Untitled"):
        now = datetime.now().isoformat()
        return cls(
            id=str(uuid.uuid4()),
            user_id=user_id,
            title=title,
            messages=[],
            created_at=now,
            updated_at=now,
        )

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_dict(cls, doc: dict) -> "Conversation":
        doc.pop("_id", None)
        return cls(**doc)

    @property
    def last_message(self) -> Optional[Message]:
        return self.messages[-1] if self.messages else None

    @property
    def message_count(self) -> int:
        return len(self.messages)


class CreateConversationRequest(BaseModel):
    title: str = "New Chat"


class UpdateTitleRequest(BaseModel):
    title: str


class AddMessageRequest(BaseModel):
    message: dict
