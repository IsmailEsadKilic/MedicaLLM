from typing import List
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json

from ..auth.dependecies import get_current_user_id
from ..conversations import service as conv_service
from ..drugs.models import AnalyzePatientRequest
from .. import printmeup as pm
from .session import Session

router = APIRouter(prefix="/api/drugs", tags=["drugs/agent"])

# In-memory session store
active_sessions: dict[str, Session] = {}


class QueryRequest(BaseModel):
    conversation_id: str
    query: str


class GenerateTitleRequest(BaseModel):
    message: str


def _get_agent():
    """Get the global medical agent instance."""
    from ..main import medical_agent
    return medical_agent


def _get_or_create_session(conversation_id: str, agent) -> Session:
    """Get existing session or create a new one."""
    if conversation_id not in active_sessions:
        conversation = conv_service.get_conversation(conversation_id)
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
        active_sessions[conversation_id] = Session(
            conversation_id=conversation_id,
            user_id=conversation.user_id,
            agent=agent,
        )
    return active_sessions[conversation_id]


@router.post("/query")
async def endpoint_query(request: QueryRequest):
    """Process a user query with the medical agent. Returns full response."""
    try:
        agent = _get_agent()
        if not agent:
            raise HTTPException(status_code=503, detail="Medical agent not initialized")

        session = _get_or_create_session(request.conversation_id, agent)
        result = await session.handle_user_query(request.query)

        if not result.get("success"):
            raise HTTPException(
                status_code=500, detail=result.get("error", "Unknown error")
            )

        return {
            "success": True,
            "answer": result["answer"],
            "conversation_id": request.conversation_id,
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
async def endpoint_query_stream(request: QueryRequest):
    """Stream agent response for a user query."""

    async def generate_stream():
        try:
            agent = _get_agent()
            if not agent:
                yield f"data: {json.dumps({'error': 'Medical agent not initialized'})}\n\n"
                return

            session = _get_or_create_session(request.conversation_id, agent)
            async for chunk in session.stream_query(request.query):
                yield f"data: {json.dumps(chunk)}\n\n"
        except Exception as e:
            pm.err(e=e, m="Stream error")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"

    return StreamingResponse(generate_stream(), media_type="text/event-stream")


@router.post("/analyze-patient")
async def endpoint_analyze_patient(request: AnalyzePatientRequest):
    """Analyze patient medical profile using agent with database tools."""
    try:
        agent = _get_agent()
        if not agent:
            raise HTTPException(status_code=503, detail="Medical agent not initialized")

        prompt = f"""Create a medical analysis report for this patient. Use your database tools to gather information, then provide ONLY the final report without showing tool calls or intermediate steps.

Patient Profile:
- Chronic Conditions: {', '.join(request.chronic_conditions) if request.chronic_conditions else 'None'}
- Allergies: {', '.join(request.allergies) if request.allergies else 'None'}
- Current Medications: {', '.join(request.current_medications) if request.current_medications else 'None'}

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
                "chronic_conditions": request.chronic_conditions,
                "allergies": request.allergies,
                "current_medications": request.current_medications,
            },
        }
    except Exception as e:
        pm.err(e=e, m="Failed to analyze patient profile")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/generate-title")
async def endpoint_generate_title(request: GenerateTitleRequest):
    """Generate a concise title for a conversation from the first message."""
    try:
        # Simple fallback title generation
        words = request.message.split()
        title = " ".join(words[:5]) if len(words) > 5 else request.message
        if len(title) > 60:
            title = title[:57] + "..."
        return {"title": title}
    except Exception as e:
        pm.err(e=e, m="Title generation error")
        fallback = request.message[:30] + "..." if len(request.message) > 30 else request.message
        return {"title": fallback}
