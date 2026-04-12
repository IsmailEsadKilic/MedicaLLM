import json
from datetime import datetime

from ..db.sql_client import get_session
from ..db.sql_models import ConversationRecord
from .. import printmeup as pm
from .models import Conversation, Message


def _record_to_conversation(rec: ConversationRecord) -> Conversation:
    messages_raw = json.loads(rec.messages) if rec.messages else []
    return Conversation(
        id=rec.conversation_id, user_id=rec.user_id, title=rec.title,
        messages=[Message(**m) for m in messages_raw],
        created_at=rec.created_at, updated_at=rec.updated_at,
    )


def get_conversation(conversation_id: str) -> Conversation | None:
    session = get_session()
    try:
        rec = session.query(ConversationRecord).filter(
            ConversationRecord.conversation_id == conversation_id
        ).first()
        return _record_to_conversation(rec) if rec else None
    except Exception as e:
        pm.err(e=e, m=f"Error getting conversation {conversation_id}")
        return None
    finally:
        session.close()


def get_conversations(user_id: str) -> list[Conversation]:
    session = get_session()
    try:
        recs = (session.query(ConversationRecord)
                .filter(ConversationRecord.user_id == user_id)
                .order_by(ConversationRecord.created_at.desc())
                .all())
        conversations = [_record_to_conversation(r) for r in recs]
        pm.inf(f"Found {len(conversations)} conversations for user {user_id}")
        return conversations
    except Exception as e:
        pm.err(e=e, m=f"Error getting conversations for user {user_id}")
        return []
    finally:
        session.close()


def create_conversation(user_id: str, title: str = "Untitled") -> Conversation:
    conversation = Conversation.create_new(user_id=user_id, title=title)
    session = get_session()
    try:
        session.add(ConversationRecord(
            conversation_id=conversation.id, user_id=user_id, title=title,
            messages="[]", created_at=conversation.created_at,
            updated_at=conversation.updated_at,
        ))
        session.commit()
        pm.suc(f"Created conversation {conversation.id} for user {user_id}")
    except Exception as e:
        session.rollback()
        pm.err(e=e, m="Error creating conversation")
        raise
    finally:
        session.close()
    return conversation


def save_conversation(conversation: Conversation) -> bool:
    session = get_session()
    try:
        rec = session.query(ConversationRecord).filter(
            ConversationRecord.conversation_id == conversation.id
        ).first()
        if not rec:
            return False
        rec.title = conversation.title
        rec.messages = json.dumps([m.model_dump() for m in conversation.messages])
        rec.updated_at = datetime.now().isoformat()
        session.commit()
        pm.inf(f"Saved conversation {conversation.id}")
        return True
    except Exception as e:
        session.rollback()
        pm.err(e=e, m=f"Error saving conversation {conversation.id}")
        return False
    finally:
        session.close()


def add_message(conversation_id: str, message: Message) -> bool:
    session = get_session()
    try:
        rec = session.query(ConversationRecord).filter(
            ConversationRecord.conversation_id == conversation_id
        ).first()
        if not rec:
            pm.war(f"Conversation {conversation_id} not found")
            return False
        messages = json.loads(rec.messages) if rec.messages else []
        messages.append(message.model_dump())
        rec.messages = json.dumps(messages)
        rec.updated_at = datetime.now().isoformat()
        session.commit()
        pm.inf(f"Appended message to conversation {conversation_id}")
        return True
    except Exception as e:
        session.rollback()
        pm.err(e=e, m=f"Error adding message to conversation {conversation_id}")
        return False
    finally:
        session.close()


def update_conversation_title(conversation_id: str, title: str) -> bool:
    session = get_session()
    try:
        rec = session.query(ConversationRecord).filter(
            ConversationRecord.conversation_id == conversation_id
        ).first()
        if not rec:
            return False
        rec.title = title
        rec.updated_at = datetime.now().isoformat()
        session.commit()
        pm.inf(f"Updated title for conversation {conversation_id}")
        return True
    except Exception as e:
        session.rollback()
        pm.err(e=e, m=f"Error updating title for conversation {conversation_id}")
        return False
    finally:
        session.close()


def delete_conversation(conversation_id: str) -> bool:
    session = get_session()
    try:
        result = session.query(ConversationRecord).filter(
            ConversationRecord.conversation_id == conversation_id
        ).delete()
        session.commit()
        if result == 0:
            return False
        pm.suc(f"Deleted conversation {conversation_id}")
        return True
    except Exception as e:
        session.rollback()
        pm.err(e=e, m=f"Error deleting conversation {conversation_id}")
        return False
    finally:
        session.close()
