from langchain.agents import AgentState, create_agent
from langgraph.graph.state import CompiledStateGraph
from langchain.agents.middleware.types import (
    ContextT,
    ResponseT,
    _InputAgentState,
    _OutputAgentState,
)

from ..agent.langchain_agent import create_medical_agent
from ..config import settings

from logging import getLogger

logger = getLogger(__name__)


class MedicalAgent:
    invoke = CompiledStateGraph[
        AgentState[ResponseT], ContextT, _InputAgentState, _OutputAgentState[ResponseT] # type: ignore
    ].invoke
    ainvoke = CompiledStateGraph[
        AgentState[ResponseT], ContextT, _InputAgentState, _OutputAgentState[ResponseT] # type: ignore
    ].ainvoke

    def __init__(self, langchain_agent):
        self.langchain_agent: CompiledStateGraph[
            AgentState[ResponseT], # type: ignore
            ContextT, # type: ignore
            _InputAgentState,
            _OutputAgentState[ResponseT], # type: ignore
        ] = langchain_agent
        self.invoke = langchain_agent.invoke
        self.ainvoke = langchain_agent.ainvoke


async def init_medical_agent(app):
    try:
        logger.info("[AGENT INIT] Initializing medical agent...")
        logger.debug(f"[AGENT INIT] LLM model: {settings.llm_model_id}")
        logger.debug(f"[AGENT INIT] Temperature: {settings.llm_temperature}")
        logger.debug(f"[AGENT INIT] Max iterations: {settings.llm_max_iterations}")
        
        agent = create_medical_agent(
            llm_model_id=settings.llm_model_id,
            temperature=settings.llm_temperature,
            max_iterations=settings.llm_max_iterations,
        )
        app.state.medical_agent = MedicalAgent(agent)
        logger.info("[AGENT INIT] Medical agent initialized successfully")
        logger.debug(f"[AGENT INIT] Agent type: {type(agent)}")
    except Exception as e:
        app.state.medical_agent = None
        logger.error(f"[AGENT INIT] Failed to initialize medical agent: {str(e)}", exc_info=True)
        logger.warning(f"[AGENT INIT] No medical agent available: {str(e)}")
