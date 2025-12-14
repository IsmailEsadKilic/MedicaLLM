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
            updated_at=now
        )

    def to_dynamo_item(self) -> dict:
        """Convert Pydantic model to DynamoDB item format"""
        # Convert model to dict, serialize messages properly
        item = self.model_dump()
        
        # Add PK and SK for Single Table Design
        # PK: USER#<user_id>
        # SK: CHAT#<timestamp>#<chat_id>
        item['PK'] = f"USER#{self.user_id}"
        item['SK'] = f"CHAT#{self.created_at}#{self.id}"
        
        # GSI Keys for ChatIdIndex
        item['GSI_PK'] = f"CHAT#{self.id}"
        item['GSI_SK'] = f"USER#{self.user_id}"
        
        return item

    @classmethod
    def from_dynamo_item(cls, item: dict) -> 'Conversation':
        """Create Conversation instance from DynamoDB item"""
        # Remove DB keys before creating model
        clean_item = {k: v for k, v in item.items() if k not in ['PK', 'SK', 'GSI_PK', 'GSI_SK']}
        return cls(**clean_item)
