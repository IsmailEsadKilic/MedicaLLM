from langchain.agents import AgentState, create_agent
from langgraph.graph.state import CompiledStateGraph
from langchain.agents.middleware.types import (
    ContextT,
    ResponseT,
    _InputAgentState,
    _OutputAgentState,
)

from ..agent.langchain_agent import create_medical_agent
from ..conversations.models import Message
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
        agent = create_medical_agent(
            llm_model_id=settings.llm_model_id,
            temperature=settings.llm_temperature,
            max_iterations=settings.llm_max_iterations,
        )
        app.state.medical_agent = MedicalAgent(agent)
    except Exception as e:
        app.state.medical_agent = None
        logger.warning(f"No medical agent available: {str(e)}")
