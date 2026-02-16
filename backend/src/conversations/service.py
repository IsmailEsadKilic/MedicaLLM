from datetime import datetime
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from ..db.client import dynamodb_client
from .. import printmeup as pm
from .models import Conversation, Message


CONVERSATIONS_TABLE = "Conversations"


def _table():
    return dynamodb_client.Table(CONVERSATIONS_TABLE)  # type: ignore


def get_conversation(conversation_id: str) -> Conversation | None:
    """Get a conversation by chat_id using GSI."""
    try:
        response = _table().query(
            IndexName="ChatIdIndex",
            KeyConditionExpression=Key("GSI_PK").eq(f"CHAT#{conversation_id}"),
        )
        if response["Items"]:
            return Conversation.from_dynamo_item(response["Items"][0])
        return None
    except ClientError as e:
        pm.err(e=e, m=f"Error getting conversation {conversation_id}")
        return None


def get_conversations(user_id: str) -> list[Conversation]:
    """Get all conversations for a user, sorted by newest first."""
    try:
        response = _table().query(
            KeyConditionExpression=Key("PK").eq(f"USER#{user_id}")
            & Key("SK").begins_with("CHAT#"),
            ScanIndexForward=False,
        )
        conversations = [Conversation.from_dynamo_item(item) for item in response["Items"]]
        pm.inf(f"Found {len(conversations)} conversations for user {user_id}")
        return conversations
    except ClientError as e:
        pm.err(e=e, m=f"Error getting conversations for user {user_id}")
        return []


def create_conversation(user_id: str, title: str = "Untitled") -> Conversation:
    """Create a new conversation for a user."""
    conversation = Conversation.create_new(user_id=user_id, title=title)
    item = conversation.to_dynamo_item()
    _table().put_item(Item=item)
    pm.suc(f"Created conversation {conversation.id} for user {user_id}")
    return conversation


def save_conversation(conversation: Conversation) -> bool:
    """Save/update an existing conversation."""
    try:
        item = conversation.to_dynamo_item()
        item["updated_at"] = datetime.now().isoformat()
        _table().put_item(Item=item)
        pm.inf(f"Saved conversation {conversation.id}")
        return True
    except ClientError as e:
        pm.err(e=e, m=f"Error saving conversation {conversation.id}")
        return False


def add_message(conversation_id: str, message: Message) -> bool:
    """Add a message to a conversation."""
    try:
        conversation = get_conversation(conversation_id)
        if not conversation:
            pm.war(f"Conversation {conversation_id} not found")
            return False

        conversation.messages.append(message)
        conversation.updated_at = datetime.now().isoformat()
        return save_conversation(conversation)
    except Exception as e:
        pm.err(e=e, m=f"Error adding message to conversation {conversation_id}")
        return False


def update_conversation_title(conversation_id: str, title: str) -> bool:
    """Update the title of a conversation."""
    try:
        conversation = get_conversation(conversation_id)
        if not conversation:
            pm.war(f"Conversation {conversation_id} not found")
            return False

        conversation.title = title
        conversation.updated_at = datetime.now().isoformat()
        return save_conversation(conversation)
    except Exception as e:
        pm.err(e=e, m=f"Error updating title for conversation {conversation_id}")
        return False


def delete_conversation(conversation_id: str) -> bool:
    """Delete a conversation."""
    try:
        conversation = get_conversation(conversation_id)
        if not conversation:
            pm.war(f"Conversation {conversation_id} not found")
            return False

        _table().delete_item(
            Key={
                "PK": f"USER#{conversation.user_id}",
                "SK": f"CHAT#{conversation.created_at}#{conversation.id}",
            }
        )
        pm.suc(f"Deleted conversation {conversation_id}")
        return True
    except ClientError as e:
        pm.err(e=e, m=f"Error deleting conversation {conversation_id}")
        return False
