from http.client import HTTPException
import json
from datetime import datetime

from ..db.sql_client import get_session
from ..db.sql_models import ConversationRecord
from .models import Conversation, Message
from ..config import settings

from logging import getLogger

logger = getLogger(__name__)


def _record_to_conversation(rec: ConversationRecord) -> Conversation:
    messages_raw = json.loads(rec.messages) if rec.messages else []  # type: ignore
    # Get user_id from the relationship
    user_id = rec.user.user_id if rec.user else ""
    return Conversation(
        id=rec.conversation_id, # type: ignore
        user_id=user_id,
        title=rec.title,  # type: ignore
        messages=[Message(**m) for m in messages_raw],
        created_at=rec.created_at, # type: ignore
        updated_at=rec.updated_at,  # type: ignore
    )


def get_conversation(conversation_id: str) -> Conversation | None:
    session = get_session()
    try:
        rec = (
            session.query(ConversationRecord)
            .filter(ConversationRecord.conversation_id == conversation_id)
            .first()
        )
        return _record_to_conversation(rec) if rec else None
    except Exception as e:
        logger.error(f"Error getting conversation {conversation_id}: {str(e)}")
        return None
    finally:
        session.close()


def get_conversations(user_id: str) -> list[Conversation]:
    session = get_session()
    try:
        # Get user's internal PK first
        from ..db.sql_models import UserRecord
        user_rec = session.query(UserRecord).filter(UserRecord.user_id == user_id).first()
        if not user_rec:
            logger.warning(f"User not found: {user_id}")
            return []
        
        recs = (
            session.query(ConversationRecord)
            .filter(ConversationRecord.user_pk == user_rec.id)
            .order_by(ConversationRecord.created_at.desc())
            .all()
        )
        conversations = [_record_to_conversation(r) for r in recs]
        return conversations
    except Exception as e:
        logger.error(f"Error getting conversations for user {user_id}: {str(e)}")
        return []
    finally:
        session.close()


def create_conversation(
    user_id: str, title: str = settings.default_conversation_title
) -> Conversation:
    conversation = Conversation.create_new(user_id=user_id, title=title)
    session = get_session()
    try:
        # Get user's internal PK
        from ..db.sql_models import UserRecord
        user_rec = session.query(UserRecord).filter(UserRecord.user_id == user_id).first()
        if not user_rec:
            raise ValueError(f"User not found: {user_id}")
        
        session.add(
            ConversationRecord(
                conversation_id=conversation.conversation_id,
                user_pk=user_rec.id,
                title=title,
                messages="[]",
                created_at=conversation.created_at,
                updated_at=conversation.updated_at,
            )
        )
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating conversation for user {user_id}: {str(e)}")
        raise
    finally:
        session.close()
    return conversation


def save_conversation(conversation: Conversation) -> bool:
    session = get_session()
    try:
        rec = (
            session.query(ConversationRecord)
            .filter(ConversationRecord.conversation_id == conversation.conversation_id)
            .first()
        )
        if not rec:
            return False
        rec.title = conversation.title  # type: ignore
        rec.messages = json.dumps([m.model_dump() for m in conversation.messages])  # type: ignore
        rec.updated_at = datetime.now().isoformat()  # type: ignore
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error saving conversation {conversation.conversation_id}: {str(e)}")
        return False
    finally:
        session.close()


def add_message(conversation_id: str, message: Message) -> tuple[bool, int]:
    session = get_session()
    try:
        rec = (
            session.query(ConversationRecord)
            .filter(ConversationRecord.conversation_id == conversation_id)
            .first()
        )
        if not rec:
            logger.warning(f"Conversation {conversation_id} not found")
            return False, 0
        messages = json.loads(rec.messages) if rec.messages else []  # type: ignore
        messages.append(message.model_dump())
        rec.messages = json.dumps(messages)  # type: ignore
        rec.updated_at = datetime.now().isoformat()  # type: ignore
        session.commit()
        return True, len(messages)
    except Exception as e:
        session.rollback()
        logger.error(f"Error adding message to conversation {conversation_id}: {str(e)}")
        return False, 0
    finally:
        session.close()


def add_messages(conversation_id: str, messages: list[Message]) -> tuple[bool, int]:
    session = get_session()
    try:
        rec = (
            session.query(ConversationRecord)
            .filter(ConversationRecord.conversation_id == conversation_id)
            .first()
        )
        if not rec:
            logger.warning(f"Conversation {conversation_id} not found")
            return False, 0
        existing_messages = json.loads(rec.messages) if rec.messages else []  # type: ignore
        existing_messages.extend([m.model_dump() for m in messages])
        rec.messages = json.dumps(existing_messages)  # type: ignore
        rec.updated_at = datetime.now().isoformat()  # type: ignore
        session.commit()
        return True, len(existing_messages)
    except Exception as e:
        session.rollback()
        logger.error(f"Error adding messages to conversation {conversation_id}: {str(e)}")
        return False, 0
    finally:
        session.close()


def update_conversation_title(conversation_id: str, title: str) -> bool:
    session = get_session()
    try:
        rec = (
            session.query(ConversationRecord)
            .filter(ConversationRecord.conversation_id == conversation_id)
            .first()
        )
        if not rec:
            return False
        rec.title = title  # type: ignore
        rec.updated_at = datetime.now().isoformat()  # type: ignore
        session.commit()
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error updating title for conversation {conversation_id}: {str(e)}")
        return False
    finally:
        session.close()


def delete_conversation(conversation_id: str) -> bool:
    session = get_session()
    try:
        result = (
            session.query(ConversationRecord)
            .filter(ConversationRecord.conversation_id == conversation_id)
            .delete()
        )
        session.commit()
        if result == 0:
            return False
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error deleting conversation {conversation_id}: {str(e)}")
        return False
    finally:
        session.close()
