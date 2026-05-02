from __future__ import annotations
from typing import Literal, List
from datetime import datetime
import uuid
from pydantic import BaseModel, Field

from ..config import settings

class ToolExecution(BaseModel):
    """Detailed information about a single tool execution."""
    tool_name: str
    tool_args: dict = {}  # Input parameters passed to the tool
    tool_result: str = ""  # Raw output from the tool
    execution_time_ms: float | None = None  # Time taken to execute the tool
    error: str | None = None  # Error message if tool failed
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())


class Message(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    
    # Legacy fields (kept for backward compatibility)
    tools_used: List[str] = []  # Tool names: ["search_pubmed", "get_drug_info"]
    tool_results: List[str] = []  # Tool outputs (linked by index to tools_used)
    
    # New comprehensive tool execution tracking
    tool_executions: List[ToolExecution] = []  # Detailed tool execution info
    
    sources: List[dict] = []  # Structured sources with ref_id, title, url, confidence, etc.
    debug: dict = {}  # Additional debug information (execution time, etc.)
    
    @property
    def has_tools(self) -> bool:
        """Check if this message used any tools."""
        return len(self.tool_executions) > 0 or len(self.tools_used) > 0
    
    @property
    def has_sources(self) -> bool:
        """Check if this message has any sources."""
        return len(self.sources) > 0
    
    @property
    def has_debug_info(self) -> bool:
        """Check if this message has debug information."""
        return self.has_tools or self.has_sources or bool(self.debug)
    
    def get_source_by_ref(self, ref_id: str) -> dict | None:
        """Get a source by its reference ID (e.g., 'REF1')."""
        for source in self.sources:
            if source.get("ref") == ref_id:
                return source
        return None
    
    def get_tool_execution_summary(self) -> dict:
        """Get a summary of tool executions for this message."""
        if not self.tool_executions:
            return {}
        
        total_time = sum(
            t.execution_time_ms for t in self.tool_executions 
            if t.execution_time_ms is not None
        )
        
        return {
            "total_tools": len(self.tool_executions),
            "total_execution_time_ms": total_time,
            "tools": [t.tool_name for t in self.tool_executions],
            "errors": [t.error for t in self.tool_executions if t.error],
        }


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