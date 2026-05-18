from fastapi import APIRouter, Depends, HTTPException, Query, Request, status

from ..auth.dependencies import get_current_user_id
from .models import (
    AddMessageRequest,
    CreateConversationRequest,
    Message,
    UpdateTitleRequest,
)
from . import service

from logging import getLogger

logger = getLogger(__name__)

router = APIRouter(prefix="/api/conversations", tags=["conversations"])


def _safe_500(action: str) -> HTTPException:
    """Return a generic 500 without leaking the underlying exception (audit S11)."""
    return HTTPException(status_code=500, detail=f"Failed to {action}")


@router.get("/")
async def endpoint_get_conversations(
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
):
    """
    List a user's conversations, paginated.

    Audit I16: defaults to 50 results so we don't dump the user's entire
    history into one response.
    """
    logger.info(
        f"[CONVERSATIONS] GET / user={user_id} limit={limit} offset={offset}"
    )
    try:
        conversations = service.get_conversations(
            user_id=user_id, limit=limit, offset=offset
        )
        logger.info(f"[CONVERSATIONS] Found {len(conversations)} conversations")
        return {
            "success": True,
            "count": len(conversations),
            "limit": limit,
            "offset": offset,
            "conversations": [conv.model_dump() for conv in conversations],
        }
    except HTTPException:
        raise
    except Exception:
        logger.error(
            f"Failed to get conversations for user {user_id}", exc_info=True
        )
        raise _safe_500("list conversations")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def endpoint_create_conversation(
    request: Request,
    body: CreateConversationRequest,
    user_id: str = Depends(get_current_user_id),
):
    try:
        conversation = service.create_conversation(user_id=user_id, title=body.title)
        return {
            "success": True,
            "conversation_id": conversation.conversation_id,
            "conversation": conversation.model_dump(),
        }
    except HTTPException:
        raise
    except Exception:
        logger.error(f"Failed to create conversation for user {user_id}", exc_info=True)
        raise _safe_500("create conversation")


@router.get("/patient/{patient_id}")
async def endpoint_get_patient_conversations(
    patient_id: str,
    user_id: str = Depends(get_current_user_id),
    limit: int = Query(default=20, ge=1, le=100),
):
    """Get conversations linked to a specific patient (for consultation history)."""
    try:
        conversations = service.get_patient_conversations(
            user_id=user_id, patient_id=patient_id, limit=limit
        )
        return {
            "success": True,
            "count": len(conversations),
            "conversations": [conv.model_dump() for conv in conversations],
        }
    except Exception:
        logger.error(
            f"Failed to get patient conversations for {patient_id}",
            exc_info=True,
        )
        raise _safe_500("list patient conversations")


@router.get("/{conversation_id}")
async def endpoint_get_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        conversation = service.get_conversation(conversation_id=conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")
        return {"success": True, "conversation": conversation.model_dump()}
    except HTTPException:
        raise
    except Exception:
        logger.error(f"Failed to get conversation {conversation_id}", exc_info=True)
        raise _safe_500("load conversation")


@router.patch("/{conversation_id}/title")
async def endpoint_update_title(
    conversation_id: str,
    request: Request,
    body: UpdateTitleRequest,
    user_id: str = Depends(get_current_user_id),
):
    try:
        conversation = service.get_conversation(conversation_id=conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        success = service.update_conversation_title(
            conversation_id=conversation_id, title=body.title
        )
        if not success:
            raise _safe_500("update title")

        # Return the title we just persisted, not the in-memory copy that
        # was loaded *before* the update. Audit I19: the previous response
        # echoed the stale `conversation.title` instead of `body.title`.
        return {"success": True, "message": "Title updated", "title": body.title}
    except HTTPException:
        raise
    except Exception:
        logger.error(
            f"Failed to update title for conversation {conversation_id}",
            exc_info=True,
        )
        raise _safe_500("update title")


@router.delete("/{conversation_id}")
async def endpoint_delete_conversation(
    conversation_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        conversation = service.get_conversation(conversation_id=conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        success = service.delete_conversation(conversation_id=conversation_id)
        if not success:
            raise _safe_500("delete conversation")

        return {"success": True, "message": "Conversation deleted"}
    except HTTPException:
        raise
    except Exception:
        logger.error(
            f"Failed to delete conversation {conversation_id}", exc_info=True
        )
        raise _safe_500("delete conversation")


@router.post("/{conversation_id}/messages")
async def endpoint_add_message(
    conversation_id: str,
    request: Request,
    body: AddMessageRequest,
    user_id: str = Depends(get_current_user_id),
):
    """
    Add a message to a conversation. Distinct from the agent-query endpoint:
    this is a generic insert (e.g., system messages, tool results).
    """
    try:
        conversation = service.get_conversation(conversation_id=conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        if conversation.user_id != user_id:
            raise HTTPException(status_code=403, detail="Forbidden")

        msg = Message(**body.message)
        success, _count = service.add_message(
            conversation_id=conversation_id, message=msg
        )
        if not success:
            raise _safe_500("add message")

        return {"success": True, "message": "Message added"}
    except HTTPException:
        raise
    except Exception:
        logger.error(
            f"Failed to add message to conversation {conversation_id}",
            exc_info=True,
        )
        raise _safe_500("add message")
