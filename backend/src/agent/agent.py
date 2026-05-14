"""
Medical agent wrapper.

Wraps the LangGraph compiled state graph produced by `create_medical_agent`
in a thin facade that exposes `invoke` / `ainvoke`. The previous version
imported private internal types from `langchain.agents.middleware.types`
(`_InputAgentState`, `_OutputAgentState`, etc.) — those are private and may
disappear or move between langchain releases (audit A2). We keep the typing
loose here so the wrapper survives langchain upgrades.
"""
from typing import Any

from ..agent.langchain_agent import create_medical_agent
from ..config import settings

from logging import getLogger

logger = getLogger(__name__)


class MedicalAgent:
    """
    Thin wrapper around a LangGraph compiled state graph.

    Exposes both `invoke` (sync) and `ainvoke` (async). Callers should prefer
    `ainvoke` when running inside an event loop; the sync `invoke` is kept for
    background tasks (e.g., title generation) that aren't on the request hot
    path.
    """

    def __init__(self, langchain_agent: Any):
        self.langchain_agent = langchain_agent
        # Bind the methods directly so callers can keep calling
        # `medical_agent.invoke(...)` / `await medical_agent.ainvoke(...)`.
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
