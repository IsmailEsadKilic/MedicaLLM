from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import time

from ..auth.dependencies import get_current_user
from ..auth.models import UserBase
from ..users import service as user_service
from .session import Session
from .session_manager import SessionManager
from ..agent.langchain_agent import build_system_prompt
from ..agent.tools import set_current_user_id, set_current_patient_id
from ..middleware.rate_limiter import limiter, LLM_LIMIT, user_key
from ..config import settings

from logging import getLogger
logger = getLogger(__name__)

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
    logger.debug(f"[SESSION MANAGER] _get_or_create_session called for conversation {conversation_id}, user {current_user_id}")
    
    agent = getattr(request.app.state, "medical_agent", None)
    if not agent:
        logger.error("[SESSION MANAGER] Medical agent not found in app state. Cannot create session.")
        raise HTTPException(status_code=500, detail="Agent not available. Cannot create session.")
    
    logger.debug(f"[SESSION MANAGER] Agent found: {type(agent)}")
    
    session: Session = session_manager.get_or_create(conversation_id, agent)
    logger.debug(f"[SESSION MANAGER] Session obtained: {session.session_id}, user_id: {session.user_id}")
    
    # check ownership if session already exists
    if session.user_id != current_user_id:
        logger.warning(f"[SESSION MANAGER] Unauthorized session access attempt: user {current_user_id} trying to access session for user {session.user_id}")
        raise HTTPException(status_code=403, detail="Unauthorized access to session")
    
    logger.debug(f"[SESSION MANAGER] Session ownership verified")
    return session
                                            

# section: router and endpoints

router = APIRouter(prefix="/api/session", tags=["session"])

session_manager = SessionManager(
    max_sessions=settings.max_n_sessions, ttl_seconds=settings.session_ttl_seconds
)


@router.post("/query")
@limiter.limit(LLM_LIMIT, key_func=user_key)
async def endpoint_query(
    request: Request,
    body: QueryRequest,
    current_user: UserBase = Depends(get_current_user),
):
    """
    Process a user query with the agent. Returns full response.
    """
    logger.info(f"[SESSION QUERY] ========== NEW QUERY REQUEST ==========")
    logger.info(f"[SESSION QUERY] User: {current_user.user_id} ({current_user.email})")
    logger.info(f"[SESSION QUERY] Conversation: {body.conversation_id}")
    logger.info(f"[SESSION QUERY] Patient ID: {body.patient_id}")
    logger.info(f"[SESSION QUERY] Query: {body.query[:200]}...")
    logger.debug(f"[SESSION QUERY] Full query: {body.query}")
    logger.debug(f"[SESSION QUERY] Session ID from body: {body.session_id}")
    
    try:
        logger.debug(f"[SESSION QUERY] Getting or creating session")
        session = _get_or_create_session(request=request, conversation_id=body.conversation_id, current_user_id=current_user.user_id)
        logger.info(f"[SESSION QUERY] Session obtained: {session.session_id}")
        
        # Build dynamic system prompt with role context and optional patient data
        user_id = current_user.user_id
        is_doctor = current_user.is_doctor
        logger.debug(f"[SESSION QUERY] User role - is_doctor: {is_doctor}, is_patient: {current_user.is_patient}")
        
        patient = None
        if body.patient_id:
            logger.info(f"[SESSION QUERY] Loading patient {body.patient_id} for context")
            patient = user_service.get_patient_details(
                patient_id=body.patient_id,
                current_user_id=current_user.user_id,
            )
            if patient:
                logger.debug(f"[SESSION QUERY] Patient loaded: {patient.name}, medications: {len(patient.current_medications)}")
            else:
                logger.warning(f"[SESSION QUERY] Patient {body.patient_id} not found or not authorized")
        
        logger.debug(f"[SESSION QUERY] Building dynamic system prompt")
        dynamic_prompt = build_system_prompt(is_doctor=is_doctor, patient=patient)
        logger.debug(f"[SESSION QUERY] System prompt length: {len(dynamic_prompt)} chars")

        # Seed the user-ID context var so tools can perform user-scoped lookups
        set_current_user_id(user_id)
        logger.debug(f"[SESSION QUERY] Set current_user_id context var: {user_id}")
        
        # Seed the patient-ID context var if provided
        if body.patient_id:
            set_current_patient_id(body.patient_id)
            logger.debug(f"[SESSION QUERY] Set current_patient_id context var: {body.patient_id}")
        
        logger.info(f"[SESSION QUERY] Processing query: {body.query[:50]}...")
        query_start_time = time.time()
        
        result = await session.handle_user_query(
            body.query, system_prompt=dynamic_prompt, current_user=current_user
        )
        
        query_duration = (time.time() - query_start_time) * 1000
        logger.info(f"[SESSION QUERY] Query processed in {query_duration:.2f}ms")
        logger.debug(f"[SESSION QUERY] Result success: {result.success}")
        logger.debug(f"[SESSION QUERY] Result messages: {len(result.messages)}")
        logger.debug(f"[SESSION QUERY] Result sources: {len(result.agent_sources)}")
        logger.debug(f"[SESSION QUERY] Result tools used: {[t['tool_name'] for t in result.tool_responses]}")

        if not result.success:
            error_msg = result.debug.get("error") or "Unknown error"
            logger.error(f"[SESSION QUERY] Agent query failed: {error_msg}")
            logger.debug(f"[SESSION QUERY] Full debug info: {result.debug}")
            e = HTTPException(
                status_code=500, detail=error_msg
            )
            raise e
        
        response = {
            "success": True,
            "conversation_id": body.conversation_id,
            **result.model_dump(),
        }
        logger.info(f"[SESSION QUERY] ========== QUERY COMPLETED SUCCESSFULLY ==========")
        return response
        
    except HTTPException as e:
        logger.error(f"[SESSION QUERY] HTTP error during query processing: {e.status_code} - {e.detail}")
        raise e
    except Exception as e:
        logger.error(f"[SESSION QUERY] Failed to process query: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query-stream")
@limiter.limit(LLM_LIMIT, key_func=user_key)
async def endpoint_query_stream(
    request: Request,
    body: QueryRequest,
    current_user: UserBase = Depends(get_current_user),
):
    """
    Process a user query with the agent. Returns SSE streaming response with real-time token streaming.
    """
    import json
    from fastapi.responses import StreamingResponse
    
    logger.info(f"[SESSION QUERY STREAM] ========== NEW STREAMING QUERY REQUEST ==========")
    logger.info(f"[SESSION QUERY STREAM] User: {current_user.user_id} ({current_user.email})")
    logger.info(f"[SESSION QUERY STREAM] Conversation: {body.conversation_id}")
    logger.info(f"[SESSION QUERY STREAM] Patient ID: {body.patient_id}")
    logger.info(f"[SESSION QUERY STREAM] Query: {body.query[:200]}...")
    
    async def generate():
        try:
            logger.debug(f"[SESSION QUERY STREAM] Getting or creating session")
            session = _get_or_create_session(request=request, conversation_id=body.conversation_id, current_user_id=current_user.user_id)
            logger.info(f"[SESSION QUERY STREAM] Session obtained: {session.session_id}")
            
            # Build dynamic system prompt with role context and optional patient data
            user_id = current_user.user_id
            is_doctor = current_user.is_doctor
            logger.debug(f"[SESSION QUERY STREAM] User role - is_doctor: {is_doctor}, is_patient: {current_user.is_patient}")
            
            patient = None
            if body.patient_id:
                logger.info(f"[SESSION QUERY STREAM] Loading patient {body.patient_id} for context")
                patient = user_service.get_patient_details(
                    patient_id=body.patient_id,
                    current_user_id=current_user.user_id,
                )
                if patient:
                    logger.debug(f"[SESSION QUERY STREAM] Patient loaded: {patient.name}, medications: {len(patient.current_medications)}")
                else:
                    logger.warning(f"[SESSION QUERY STREAM] Patient {body.patient_id} not found or not authorized")
            
            logger.debug(f"[SESSION QUERY STREAM] Building dynamic system prompt")
            dynamic_prompt = build_system_prompt(is_doctor=is_doctor, patient=patient)
            logger.debug(f"[SESSION QUERY STREAM] System prompt length: {len(dynamic_prompt)} chars")

            # Seed the user-ID context var so tools can perform user-scoped lookups
            set_current_user_id(user_id)
            logger.debug(f"[SESSION QUERY STREAM] Set current_user_id context var: {user_id}")
            
            # Seed the patient-ID context var if provided
            if body.patient_id:
                set_current_patient_id(body.patient_id)
                logger.debug(f"[SESSION QUERY STREAM] Set current_patient_id context var: {body.patient_id}")
            
            logger.info(f"[SESSION QUERY STREAM] Processing query with streaming...")
            
            # Send initial thinking step
            yield f"data: {json.dumps({'type': 'thinking', 'step': 'Processing your query...'})}\n\n"
            
            # Stream the response
            async for event in session.handle_user_query_streamed(
                body.query, 
                system_prompt=dynamic_prompt, 
                current_user=current_user
            ):
                event_type = event.get("type")
                
                if event_type == "content":
                    # Stream content tokens as they arrive
                    yield f"data: {json.dumps(event)}\n\n"
                
                elif event_type == "tool_start":
                    # Notify about tool usage with args
                    tool_name = event.get("tool_name", "unknown")
                    tool_args = event.get("tool_args", {})
                    yield f"data: {json.dumps({'type': 'thinking', 'step': f'Using {tool_name}...'})}\n\n"
                    yield f"data: {json.dumps({'type': 'tool_start', 'tool_name': tool_name, 'tool_args': tool_args})}\n\n"
                
                elif event_type == "tool_end":
                    # Tool completed with execution time
                    tool_name = event.get("tool_name", "unknown")
                    execution_time_ms = event.get("execution_time_ms")
                    logger.debug(f"[SESSION QUERY STREAM] Tool {tool_name} completed in {execution_time_ms}ms")
                    yield f"data: {json.dumps({'type': 'tool_end', 'tool_name': tool_name, 'execution_time_ms': execution_time_ms})}\n\n"
                
                elif event_type == "done":
                    # Send final metadata with comprehensive tool execution info
                    sources = event.get("sources", [])
                    tool_executions = event.get("tool_executions", [])
                    final_content = event.get("final_content", "")
                    execution_time = event.get("execution_time_ms", 0)
                    debug_info = event.get("debug", {})
                    
                    logger.info(f"[SESSION QUERY STREAM] Streaming completed in {execution_time:.2f}ms")
                    logger.debug(f"[SESSION QUERY STREAM] Tool executions: {len(tool_executions)}")
                    
                    yield f"data: {json.dumps({
                        'type': 'done', 
                        'sources': sources, 
                        'tool_executions': tool_executions,
                        'final_content': final_content,
                        'execution_time_ms': execution_time,
                        'debug': debug_info,
                    })}\n\n"
                
                elif event_type == "error":
                    # Handle errors
                    error_msg = event.get("error", "Unknown error")
                    logger.error(f"[SESSION QUERY STREAM] Stream error: {error_msg}")
                    yield f"data: {json.dumps({'type': 'error', 'error': error_msg})}\n\n"
                    return
            
            logger.info(f"[SESSION QUERY STREAM] ========== STREAMING QUERY COMPLETED SUCCESSFULLY ==========")
            
        except HTTPException as e:
            logger.error(f"[SESSION QUERY STREAM] HTTP error during query processing: {e.status_code} - {e.detail}")
            yield f"data: {json.dumps({'type': 'error', 'error': str(e.detail)})}\n\n"
        except Exception as e:
            logger.error(f"[SESSION QUERY STREAM] Failed to process query: {str(e)}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")

@router.post("/generate-title")
async def endpoint_generate_title(
        request: Request,
        body: GenerateTitleRequest,
        current_user: UserBase = Depends(get_current_user),
    ):
    """
    Generate a concise title for a conversation based on last user + agent messages.
    """
    logger.info(f"[GENERATE TITLE] Request for conversation {body.conversation_id} from user {current_user.user_id}")
    try:
        session = session_manager.get(conversation_id=body.conversation_id) # no creation
        
        if not session:
            logger.warning(f"[GENERATE TITLE] Session not found for conversation {body.conversation_id}")
            raise HTTPException(status_code=404, detail="Session not found for conversation")
    
        if not session.user_id == current_user.user_id:
            logger.warning(f"Unauthorized title generation attempt: user {current_user.user_id} trying to access session for user {session.user_id}")
            raise HTTPException(status_code=403, detail="Unauthorized access to session")
        
        logger.info(f"[GENERATE TITLE] Generating title for conversation {body.conversation_id}")
        title = await session.generate_title(current_user)
        logger.info(f"[GENERATE TITLE] Generated title: {title}")
        return {"success": True, "title": title}
    except HTTPException as e:
        logger.error(f"HTTP error during title generation: {str(e)}")
        raise e
    except Exception as e:
        logger.error(f"Failed to generate title: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
