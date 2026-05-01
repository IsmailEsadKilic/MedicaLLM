
# ok
from typing import Literal
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from ..auth.dependencies import get_current_user
from ..auth.models import UserDetails
from ..conversations import service as conversation_service
from ..drugs.models import AnalyzePatientRequest
from ..users import service as user_service
from ....legacy import printmeup as pm
from .session import Session
from .session_manager import SessionManager
from ..agent.langchain_agent import build_system_prompt
from ..agent.tools import set_current_user_id
from ..middleware.rate_limiter import limiter, LLM_LIMIT, user_key
from ..config import settings

# section: models

class QueryRequest(BaseModel):
    query: str
    session_id: str | None = None
    conversation_id: str
    patient_id: str | None = None


class GenerateTitleRequest(BaseModel):
    conversation_id: str

# section: dependencies and helpers

def _get_or_create_session(request: Request, conversation_id: str, current_user_id: str) -> Session:
    """
    Delegate to SessionManager — get an existing session or create one.
    """
    agent = getattr(request.app.state, "medical_agent", None)
    if not agent:
        pm.err(m="Medical agent not found in app state. Cannot create session.")
        raise HTTPException(status_code=500, detail="Agent not available. Cannot create session.")
    
    session: Session = session_manager.get_or_create(conversation_id, agent)
    
    # check ownership if session already exists
    if session.user_id != current_user_id:
        pm.war(f"Unauthorized session access attempt: user {current_user_id} trying to access session for user {session.user_id}")
        raise HTTPException(status_code=403, detail="Unauthorized access to session")
    
    return session
                                            

# section: router and endpoints

router = APIRouter(prefix="/api/drugs", tags=["drugs/agent"])

session_manager = SessionManager(
    max_sessions=settings.max_n_sessions, ttl_seconds=settings.session_ttl_seconds
)


@router.post("/query")
@limiter.limit(LLM_LIMIT, key_func=user_key)
async def endpoint_query(
    request: Request,
    body: QueryRequest,
    current_user: UserDetails = Depends(get_current_user),
):
    """
    Process a user query with the agent. Returns full response.
    """
    try:

        session = _get_or_create_session(request=request, conversation_id=body.conversation_id, current_user_id=current_user.user_id)
        
        # Build dynamic system prompt with role context and optional patient data
        user_id = current_user.user_id
        is_doctor = current_user.is_doctor
        patient = None
        if body.patient_id:
            patient = user_service.get_patient_details(
                patient_id=body.patient_id,
                current_user_id=current_user.user_id,
            )
        dynamic_prompt = build_system_prompt(is_doctor=is_doctor, patient=patient)

        # Seed the user-ID context var so tools can perform user-scoped lookups
        set_current_user_id(user_id)
        
        result = await session.handle_user_query(
            body.query, system_prompt=dynamic_prompt
        )

        if not result.success:
            e = HTTPException(
                status_code=500, detail=result.debug.get("error") or "Unknown error"
            )
            pm.err(e=e, m="Agent query failed")
            raise e
        
        response = {
            "success": True,
            "conversation_id": body.conversation_id,
            **result.model_dump(),
        }
        return response
        
    except HTTPException as e:
        pm.err(e=e, m="HTTP error during query processing")
        raise e
    except Exception as e:
        pm.err(e=e, m="Failed to process query")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query-stream")
@limiter.limit(LLM_LIMIT, key_func=user_key)
async def endpoint_query_stream(
    request: Request,
    body: QueryRequest,
    current_user: UserDetails = Depends(get_current_user),
):
    # todo:
    raise HTTPException(status_code=501, detail="Streaming endpoint not implemented yet")

@router.post("/generate-title")
async def endpoint_generate_title(
        request: Request,
        body: GenerateTitleRequest,
        current_user: UserDetails = Depends(get_current_user),
    ):
    """
    Generate a concise title for a conversation based on last user + agent messages.
    """
    try:
        session = session_manager.get(conversation_id=body.conversation_id) # no creation
        
        if not session:
            raise HTTPException(status_code=404, detail="Session not found for conversation")
    
        if not session.user_id == current_user.user_id:
            pm.war(f"Unauthorized title generation attempt: user {current_user.user_id} trying to access session for user {session.user_id}")
            raise HTTPException(status_code=403, detail="Unauthorized access to session")
        
        title = await session.generate_title(current_user)
        return {"success": True, "title": title}
    except HTTPException as e:
        pm.err(e=e, m="HTTP error during title generation")
        raise e
    except Exception as e:
        pm.err(e=e, m="Failed to generate title")
        raise HTTPException(status_code=500, detail=str(e))
