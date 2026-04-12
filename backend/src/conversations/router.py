from fastapi import APIRouter, HTTPException, Depends, status

from ..auth.dependencies import get_current_user_id
from .. import printmeup as pm
from .models import (
    CreateConversationRequest,
    UpdateTitleRequest,
    AddMessageRequest,
    Message,
)
from . import service

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


@router.get("/")
async def endpoint_get_conversations(user_id: str = Depends(get_current_user_id)):
    """Get all conversations for the authenticated user."""
    try:
        conversations = service.get_conversations(user_id=user_id)
        return {
            "success": True,
            "count": len(conversations),
            "conversations": [conv.model_dump() for conv in conversations],
        }
    except Exception as e:
        pm.err(e=e, m=f"Failed to get conversations for user {user_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", status_code=status.HTTP_201_CREATED)
async def endpoint_create_conversation(
    request: CreateConversationRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Create a new conversation for the authenticated user."""
    try:
        conversation = service.create_conversation(
            user_id=user_id, title=request.title
        )
        return {
            "success": True,
            "conversation_id": conversation.id,
            "conversation": conversation.model_dump(),
        }
    except Exception as e:
        pm.err(e=e, m="Failed to create conversation")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{chat_id}")
async def endpoint_get_conversation(
    chat_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get a specific conversation by ID."""
    try:
        conversation = service.get_conversation(conversation_id=chat_id)
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
        pm.err(e=e, m=f"Failed to get conversation {chat_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{chat_id}/title")
async def endpoint_update_title(
    chat_id: str,
    request: UpdateTitleRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Update conversation title."""
    try:
        # Verify ownership
        conversation = service.get_conversation(conversation_id=chat_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        success = service.update_conversation_title(
            conversation_id=chat_id, title=request.title
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to update title")

        return {"success": True, "message": "Title updated"}
    except HTTPException:
        raise
    except Exception as e:
        pm.err(e=e, m="Failed to update title")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{chat_id}")
async def endpoint_delete_conversation(
    chat_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Delete a conversation."""
    try:
        # Verify ownership
        conversation = service.get_conversation(conversation_id=chat_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        success = service.delete_conversation(conversation_id=chat_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete conversation")

        return {"success": True, "message": "Conversation deleted"}
    except HTTPException:
        raise
    except Exception as e:
        pm.err(e=e, m=f"Failed to delete conversation {chat_id}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{chat_id}/messages")
async def endpoint_add_message(
    chat_id: str,
    request: AddMessageRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Add a message to a conversation."""
    try:
        # Verify ownership
        conversation = service.get_conversation(conversation_id=chat_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        msg = Message(**request.message)
        success = service.add_message(conversation_id=chat_id, message=msg)

        if not success:
            raise HTTPException(status_code=500, detail="Failed to add message")

        return {"success": True, "message": "Message added"}
    except HTTPException:
        raise
    except Exception as e:
        pm.err(e=e, m="Failed to add message")
        raise HTTPException(status_code=500, detail=str(e))
