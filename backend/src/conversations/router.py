from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel

from ..auth.dependencies import get_current_user_id
from .models import Message
from . import service
from ..config import settings

from logging import getLogger

logger = getLogger(__name__)

class CreateConversationRequest(BaseModel):
    title: str = settings.default_conversation_title

class UpdateTitleRequest(BaseModel):
    title: str

class AddMessageRequest(BaseModel):
    message: dict

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("/")
async def endpoint_get_conversations(user_id: str = Depends(get_current_user_id)):
    try:
        conversations = service.get_conversations(user_id=user_id)
        return {
            "success": True,
            "count": len(conversations),
            "conversations": [conv.model_dump() for conv in conversations],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversations for user {user_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", status_code=status.HTTP_201_CREATED)
async def endpoint_create_conversation(
    request: CreateConversationRequest,
    user_id: str = Depends(get_current_user_id),
):
    try:
        conversation = service.create_conversation(
            user_id=user_id, title=request.title
        )
        return {
            "success": True,
            "conversation_id": conversation.id,
            "conversation": conversation.model_dump(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to create conversation for user {user_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}")
async def endpoint_get_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        conversation = service.get_conversation(conversation_id=conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

        # Verify ownership
        if conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        return {
            "success": True,
            "conversation": conversation.model_dump(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get conversation {conversation_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{conversation_id}/title")
async def endpoint_update_title(
    conversation_id: str,
    request: UpdateTitleRequest,
    user_id: str = Depends(get_current_user_id),
):
    try:
        # Verify ownership
        conversation = service.get_conversation(conversation_id=conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        success = service.update_conversation_title(
            conversation_id=conversation_id, title=request.title
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update title")

        return {"success": True, "message": "Title updated", "title": conversation.title}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update title for conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{conversation_id}")
async def endpoint_delete_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        # Verify ownership
        conversation = service.get_conversation(conversation_id=conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        success = service.delete_conversation(conversation_id=conversation_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete conversation")

        return {"success": True, "message": "Conversation deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/messages")
async def endpoint_add_message(
    conversation_id: str,
    request: AddMessageRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Add a message to a conversation.
    Difference between this and user querying the agent is that this is a generic endpoint
    for adding any message (e.g. system messages, tool results) while the user query endpoint
    has additional logic for processing the query through the agent and generating a response.
    """
    try:
        # Verify ownership
        conversation = service.get_conversation(conversation_id=conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        msg = Message(**request.message)
        success = service.add_message(conversation_id=conversation_id, message=msg)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to add message")

        return {"success": True, "message": "Message added"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to add message to conversation {conversation_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
