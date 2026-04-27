from typing import Literal
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from ..auth.dependencies import get_current_user
from ..auth.models import CurrentUserDetails
from ..conversations import service as conversation_service
from ..drugs.models import AnalyzePatientRequest
from ..users import service as user_service
from .. import printmeup as pm
from .session import Session
from .session_manager import SessionManager
from .langchain_agent import build_system_prompt
from .tools import set_current_user_id
from ..middleware.rate_limiter import limiter, LLM_LIMIT, user_key
from ..config import settings

# section: models


class QueryRequest(BaseModel):
    conversation_id: str
    query: str
    patient_id: str | None = None


class GenerateTitleRequest(BaseModel):
    conversation_id: str


# section

router = APIRouter(prefix="/api/drugs", tags=["drugs/agent"])

session_manager = SessionManager(
    max_sessions=settings.max_n_sessions, ttl_seconds=settings.session_ttl_seconds
)


def _get_agent(request: Request, agent_type: str = "medical_agent"):
    """FastAPI dependency — retrieves the medical agent from app.state."""
    return getattr(request.app.state, agent_type, None)


def _get_or_create_session(conversation_id: str, agent) -> Session:
    """Delegate to SessionManager — get an existing session or create one."""
    return session_manager.get_or_create(conversation_id, agent)


@router.post("/query")
@limiter.limit(LLM_LIMIT, key_func=user_key)
async def endpoint_query(
    request: Request,
    body: QueryRequest,
    current_user: CurrentUserDetails = Depends(get_current_user),
):
    """Process a user query with the agent. Returns full response."""
    try:
        agent = _get_agent(request)
        if not agent:
            raise HTTPException(status_code=503, detail="Medical agent not initialized")

        # Build dynamic system prompt with role context and optional patient data
        user_id = current_user.id
        account_type = current_user.account_type
        patient = None
        if body.patient_id:
            patient = user_service.get_patient_dto(
                healthcare_professional_id=user_id,
                patient_id=body.patient_id,
            )
        dynamic_prompt = build_system_prompt(account_type=account_type, patient=patient)

        # Seed the user-ID context var so tools can perform user-scoped lookups
        # ?: why?
        set_current_user_id(user_id)

        session = _get_or_create_session(body.conversation_id, agent)
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
        e = HTTPException(status_code=500, detail=str(e))
        pm.err(e=e, m="Failed to process query")
        raise e


@router.post("/query-stream")
@limiter.limit(LLM_LIMIT, key_func=user_key)
async def endpoint_query_stream(
    request: Request,
    body: QueryRequest,
    current_user: CurrentUserDetails = Depends(get_current_user),
):
    """
    Stream agent response for a user query using Server-Sent Events (SSE).

    This endpoint provides real-time token-by-token streaming of the agent's response,
    including thinking steps, tool usage, and final content.
    """

    async def generate_stream():
        try:
            agent = _get_agent(request)
            if not agent:
                pm.war("Medical agent not initialized for streaming endpoint")
                raise HTTPException(status_code=503, detail="Medical agent not initialized")
            
            # Build dynamic system prompt with role context and optional patient data
            user_id = current_user.id
            account_type = current_user.account_type
            patient = None
            if body.patient_id:
                patient = user_service.get_patient_dto(
                    healthcare_professional_id=user_id,
                    patient_id=body.patient_id,
                )
            dynamic_prompt = build_system_prompt(account_type=account_type, patient=patient)
            
            #?: again why?
            set_current_user_id(user_id)
            
            session = _get_or_create_session(body.conversation_id, agent)
            
            async for event in session.handle_user_query_streamed(body.query, system_prompt=dynamic_prompt):
                yield "agent_event\n" #debug:

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable Nginx buffering for real-time streaming
        },
    )


@router.post("/analyze-patient")
@limiter.limit(LLM_LIMIT, key_func=user_key)
async def endpoint_analyze_patient(request: Request, body: AnalyzePatientRequest):
    """Analyze patient medical profile using agent with database tools."""
    try:
        agent = _get_agent(request)
        if not agent:
            raise HTTPException(status_code=503, detail="Medical agent not initialized")

        prompt = f"""Create a medical analysis report for this patient. Use your database tools to gather information, then provide ONLY the final report without showing tool calls or intermediate steps.

Patient Profile:
- Chronic Conditions: {", ".join(body.chronic_conditions) if body.chronic_conditions else "None"}
- Allergies: {", ".join(body.allergies) if body.allergies else "None"}
- Current Medications: {", ".join(body.current_medications) if body.current_medications else "None"}

Use your tools to check:
1. Drug information for each medication
2. Drug-drug interactions between medications
3. Drug-food interactions
4. Alternative medications for their conditions

Provide a professional medical report with sections:
## Medication Analysis
## Drug Interactions
## Food Interactions  
## Recommendations

Do NOT show tool calls or explain your process. Only provide the final formatted report."""

        result = agent.invoke({"messages": [{"role": "user", "content": prompt}]})
        messages = result.get("messages", [])
        analysis = messages[-1].content if messages else "No analysis generated"

        return {
            "success": True,
            "analysis": analysis,
            "patient_data": {
                "chronic_conditions": body.chronic_conditions,
                "allergies": body.allergies,
                "current_medications": body.current_medications,
            },
        }
    except Exception as e:
        pm.err(e=e, m="Failed to analyze patient profile")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-title")
async def endpoint_generate_title(request: GenerateTitleRequest):
    """Generate a concise title for a conversation from the first message using the LLM."""

    def create_fallback_title(message: str) -> str:
        """Create a fallback title from the message."""
        words = message.split()
        fallback = " ".join(words[:6]) if len(words) > 6 else message
        if len(fallback) > 60:
            fallback = fallback[:57] + "..."
        return fallback if fallback else "New Conversation"

    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage
        from ..config import settings

        # Validate input
        if not request.message or not request.message.strip():
            return {"title": "New Conversation"}

        model = ChatOpenAI(
            model=settings.do_ai_model,
            api_key=settings.model_access_key,
            base_url="https://inference.do-ai.run/v1",
            temperature=0.3,
            max_tokens=50,
        )

        messages = [
            HumanMessage(
                content=(
                    "Create a short title (4-6 words) for this message. "
                    "Return only the title, no quotes or extra punctuation.\n\n"
                    f"Message: {request.message[:200]}"  # Limit input length
                )
            )
        ]

        response = model.invoke(messages)

        # Handle different response types
        raw = response.content
        if isinstance(raw, list):
            raw = " ".join(str(part) for part in raw if part)

        # Clean up the title
        title = str(raw).strip().strip('"').strip("'").strip(".").strip()

        # Validate title
        if not title or len(title) < 3:
            pm.war(f"LLM returned invalid title: '{title}', using fallback")
            return {"title": create_fallback_title(request.message)}

        # Truncate if too long
        if len(title) > 60:
            title = title[:57] + "..."

        pm.inf(f"Generated title: {title}")
        return {"title": title}

    except Exception as e:
        pm.err(e=e, m="Title generation error, using fallback")
        return {"title": create_fallback_title(request.message)}
