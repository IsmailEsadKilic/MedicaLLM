from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from ..auth.dependencies import get_current_user
from ..conversations import service as conv_service
from ..drugs.models import AnalyzePatientRequest
from ..patients import service as patient_service
from .. import printmeup as pm
from .session import Session
from .session_manager import SessionManager
from .agent import build_system_prompt
from .tools import set_current_user_id
from ..middleware.rate_limiter import limiter, LLM_LIMIT, user_key

router = APIRouter(prefix="/api/drugs", tags=["drugs/agent"])

# Bounded, TTL-evicting session store (O3).
# Max 100 concurrent sessions; each session expires after 30 minutes of idle.
session_manager = SessionManager(max_sessions=100, ttl_seconds=1800)


class QueryRequest(BaseModel):
    conversation_id: str
    query: str
    # O10: optional patient context and role awareness
    patient_id: Optional[str] = None
    account_type: Optional[str] = None


class GenerateTitleRequest(BaseModel):
    message: str


def _get_agent(request: Request):
    """FastAPI dependency — retrieves the medical agent from app.state."""
    return getattr(request.app.state, "medical_agent", None)


def _get_or_create_session(conversation_id: str, agent) -> Session:
    """Delegate to SessionManager — get an existing session or create one."""
    return session_manager.get_or_create(conversation_id, agent)


@router.post("/query")
@limiter.limit(LLM_LIMIT, key_func=user_key)
async def endpoint_query(request: Request, body: QueryRequest, current_user: dict = Depends(get_current_user)):
    """Process a user query with the medical agent. Returns full response."""
    try:
        agent = _get_agent(request)
        if not agent:
            raise HTTPException(status_code=503, detail="Medical agent not initialized")

        # O10: Build dynamic system prompt with role context and optional patient data
        user_id = current_user["user_id"]
        account_type = body.account_type or current_user.get("account_type", "general_user")
        patient = None
        if body.patient_id:
            patient = patient_service.get_patient(
                healthcare_professional_id=user_id,
                patient_id=body.patient_id,
            )
        dynamic_prompt = build_system_prompt(account_type=account_type, patient=patient)

        # Seed the user-ID context var so tools can perform user-scoped lookups
        set_current_user_id(user_id)

        session = _get_or_create_session(body.conversation_id, agent)
        result = await session.handle_user_query(body.query, system_prompt=dynamic_prompt)

        if not result.get("success"):
            raise HTTPException(
                status_code=500, detail=result.get("error", "Unknown error")
            )

        return {
            "success": True,
            "answer": result["answer"],
            "conversation_id": body.conversation_id,
            "sources": result.get("sources", []),
            "tool_used": result.get("tool_used"),
            "tool_result": result.get("tool_result"),
            "debug": result.get("debug"),
        }
    except HTTPException:
        raise
    except Exception as e:
        pm.err(e=e, m="Failed to process query")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query-stream")
@limiter.limit(LLM_LIMIT, key_func=user_key)
async def endpoint_query_stream(request: Request, body: QueryRequest, current_user: dict = Depends(get_current_user)):
    """Stream agent response for a user query."""

    async def generate_stream():
        try:
            agent = _get_agent(request)
            if not agent:
                yield f"data: {json.dumps({'error': 'Medical agent not initialized'})}\n\n"
                return

            # O10: Build dynamic system prompt with role context and optional patient data
            user_id = current_user["user_id"]
            account_type = body.account_type or current_user.get("account_type", "general_user")
            patient = None
            if body.patient_id:
                patient = patient_service.get_patient(
                    healthcare_professional_id=user_id,
                    patient_id=body.patient_id,
                )
            dynamic_prompt = build_system_prompt(account_type=account_type, patient=patient)

            # Seed the user-ID context var so tools can perform user-scoped lookups
            set_current_user_id(user_id)

            session = _get_or_create_session(body.conversation_id, agent)
            async for chunk in session.stream_query(body.query, system_prompt=dynamic_prompt):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            pm.err(e=e, m="Stream error")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(generate_stream(), media_type="text/event-stream")


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
- Chronic Conditions: {', '.join(body.chronic_conditions) if body.chronic_conditions else 'None'}
- Allergies: {', '.join(body.allergies) if body.allergies else 'None'}
- Current Medications: {', '.join(body.current_medications) if body.current_medications else 'None'}

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
    try:
        from langchain_aws import ChatBedrock
        from ..config import settings

        model = ChatBedrock(
            model=settings.bedrock_llm_id,
            model_kwargs={"temperature": 0.3, "max_tokens": 30},
        )
        prompt = (
            "Generate a very short title (max 6 words) summarizing this user message. "
            "Return ONLY the title text, no quotes, no punctuation at the end, no explanation.\n\n"
            f"User message: {request.message}"
        )
        response = model.invoke(prompt)
        raw = response.content
        if isinstance(raw, list):
            raw = " ".join(str(part) for part in raw)
        title = raw.strip().strip('"').strip("'").strip(".")
        # Enforce length limits
        if len(title) > 60:
            title = title[:57] + "..."
        if not title:
            raise ValueError("Empty title from LLM")
        return {"title": title}
    except Exception as e:
        pm.err(e=e, m="Title generation error")
        # Fallback: first 5 words
        words = request.message.split()
        fallback = " ".join(words[:5]) if len(words) > 5 else request.message
        if len(fallback) > 60:
            fallback = fallback[:57] + "..."
        return {"title": fallback}
