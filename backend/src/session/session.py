from __future__ import annotations
import time
import uuid
from typing import List, Dict, Any
import asyncio
from pydantic import BaseModel
import uuid as _uuid

from ..agent.agent import MedicalAgent
from ..auth.models import UserBase
from ..conversations import service as conv_service
from ..conversations.models import Conversation, Message
from ..agent.tools import get_last_search_sources, get_last_tool_debug, set_request_id, set_current_patient_id
from ..agent.langchain_agent import SYSTEM_PROMPT
from ..config import settings

from logging import getLogger
logger = getLogger(__name__)

# section: Models

class AgentResponse(BaseModel):
    # Messages to append to conversation, including final AI response and any intermediate tool calls
    messages: List[Message]
    success: bool
    conversation_id: str
    
    # number of messages (agent and user) in conversation after appending
    # not assigned until after messages are appended to conversation and saved to DB, so optional here
    total_message_count: int | None = None 
    
    debug: Dict[str, Any] = {}
    
    # Convenience accessors - computed from messages
    @property
    def tool_responses(self) -> List[dict]:
        """Get all tool executions from messages."""
        responses = []
        for msg in self.messages:
            if getattr(msg, "tools_used", None):
                for i in range(len(msg.tools_used)):
                    # handle possible length mismatch
                    t_res = msg.tool_results[i] if i < len(getattr(msg, "tool_results", [])) else ""
                    responses.append({
                        "tool_name": msg.tools_used[i],
                        "tool_result": t_res
                    })
        return responses
    
    @property
    def agent_sources(self) -> List[dict]:
        """Get all sources from messages."""
        sources = []
        for msg in self.messages:
            if getattr(msg, "sources", None):
                sources.extend(msg.sources)
        return sources

    @staticmethod
    def from_agent_result(result: dict, conversation_id: str, request_id: str) -> AgentResponse:
        # Extract AI response
        ai_response = (
            result["messages"][-1].content
            if result.get("messages")
            else "No response generated"
        )

        # Check for search sources (use request_id for cross-thread lookup)
        # Returns list of dicts with structured source information
        sources = get_last_search_sources(request_id=request_id)

        # Check for tool debug info
        tool_debug = get_last_tool_debug(request_id=request_id)

        # Determine which tools were used (collect all, not just the last)
        tools_used = []
        tool_results = []

        if result.get("messages"):
            messages = result["messages"]
            for i, msg in enumerate(messages):
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        t_name = tool_call.get("name")
                        t_id = tool_call.get("id")
                        if t_name:
                            tools_used.append(t_name)
                        # Find corresponding tool response
                        for j in range(i + 1, len(messages)):
                            next_msg = messages[j]
                            if hasattr(next_msg, "tool_call_id") and next_msg.tool_call_id == t_id:
                                tool_results.append(next_msg.content)
                                break

        # Create message with structured sources
        # Sources are now dicts with: ref, source, pmid, title, url, confidence_score, etc.
        assistant_message = Message(
            role="assistant",
            content=ai_response,
            tools_used=tools_used,
            tool_results=tool_results,
            sources=sources if sources else [],  # Keep full structured sources
        )

        return AgentResponse(
            messages=[assistant_message],
            success=True,
            conversation_id=conversation_id,
            debug={"tool_debug": tool_debug} if tool_debug else {},
        )
# section

class Session:
    """
    Session class for managing conversation state and agent interactions.
    Uses LangChain's message format and LangGraph state management.
    """
    def __init__(
        self,
        conversation_id: str,
        user_id: str,
        agent: MedicalAgent,
    ):
        self.session_id = str(uuid.uuid4())
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.agent: MedicalAgent = agent

        # Load conversation from database
        self.conversation: Conversation | None = conv_service.get_conversation(conversation_id)

        if not self.conversation:
            self.conversation = conv_service.create_conversation(
                user_id=user_id, title=settings.default_conversation_title
            )

    def get_message_history(self) -> list:
        """
        Get conversation history in LangChain message format.

        Applies a sliding window of the most recent max_history_turns
        user+assistant pairs to bound context size and control token usage.
        """
        if not self.conversation:
            return []

        messages = []
        for msg in self.conversation.messages:
            if msg.role == "user":
                messages.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                messages.append({"role": "assistant", "content": msg.content})

        # Sliding window: keep only the most recent turns
        max_messages = settings.max_history_turns * 2
        if len(messages) > max_messages:
            messages = messages[-max_messages:]

        return messages

    async def handle_user_query(self, query: str, system_prompt: str = SYSTEM_PROMPT, current_user: UserBase | None = None) -> AgentResponse:
        """
        Process a user query through the agent.

        Args:
            query: The user's question.
            system_prompt: Optional dynamic system prompt. When supplied it
                replaces the default SYSTEM_PROMPT for this single invocation,
                enabling role-aware and patient-context responses.
            patient_id: Optional patient ID for patient-scoped operations.
        """
        try:
            logger.debug(f"[SESSION] handle_user_query called for session {self.session_id}")
            logger.debug(f"[SESSION] Query length: {len(query)} chars, first 100 chars: {query[:100]}")

            # Generate a unique request ID for cross-thread source/debug propagation
            request_id = _uuid.uuid4().hex
            set_request_id(request_id)
            logger.debug(f"[SESSION] Request ID: {request_id}")
    

            if not self.conversation:
                m = f"No conversation found for session {self.session_id} with conversation ID {self.conversation_id}"
                logger.error(m)
                raise ValueError(m)

            is_first_message = len(self.conversation.messages) == 0 if self.conversation else False
            logger.debug(f"[SESSION] Is first message: {is_first_message}, current message count: {len(self.conversation.messages)}")

            # Deduplication check
            should_append = True
            if self.conversation.messages:
                last_msg = self.conversation.messages[-1]
                logger.debug(f"[SESSION] Last message role: {last_msg.role}")
                if last_msg.role == "user":
                    if last_msg.content == query:
                        # exact same query already in history
                        should_append = False
                        logger.warning(f"[SESSION] Duplicate query detected, skipping append")
                    else:
                        logger.warning("Last user message differs from current query. Possible out-of-order messages or conversation state mismatch.")
                        self.conversation.messages.append(Message(role="system",
                            content="Last conversation message was from user but no agent response was generated. answer previous query also if necessary."
                        ))

            if should_append:
                logger.debug(f"[SESSION] Appending user message to conversation")
                user_message = Message(role="user", content=query)
                self.conversation.messages.append(user_message)
                conv_service.add_message(self.conversation.conversation_id, user_message)
            else:
                logger.debug(f"[SESSION] Skipping message append (duplicate)")

            message_history = self.get_message_history()
            logger.debug(f"[SESSION] Message history length: {len(message_history)} messages")
            message_history = [{"role": "system", "content": system_prompt}] + message_history
            logger.debug(f"[SESSION] System prompt length: {len(system_prompt)} chars")

            # Track execution time for debugging
            start_time = time.time()
            logger.info(f"[SESSION] Starting agent invocation at {start_time}")
            
            # Invoke agent with multi-tool reasoning enabled
            # The recursion_limit allows the agent to chain multiple tools together
            # Example: get_drug_info → check_interaction → search_pubmed → recommend_alternative
            logger.info(f"[SESSION] Invoking agent with recursion_limit=50")
            logger.debug(f"[SESSION] Agent type: {type(self.agent)}")
            
            result = self.agent.invoke(
                {"messages": message_history}, # type: ignore
                config={"recursion_limit": 50},
            )
            
            execution_time_ms = (time.time() - start_time) * 1000
            logger.info(f"[SESSION] Agent invocation completed in {execution_time_ms:.2f}ms")
            logger.debug(f"[SESSION] Result keys: {result.keys() if isinstance(result, dict) else 'not a dict'}")
            
            agent_response = AgentResponse.from_agent_result(
                result,
                conversation_id=self.conversation_id,
                request_id=request_id,
            )
            logger.debug(f"[SESSION] AgentResponse created with {len(agent_response.messages)} messages")
            logger.debug(f"[SESSION] Tools used: {agent_response.tool_responses}")
            logger.debug(f"[SESSION] Sources count: {len(agent_response.agent_sources)}")
            
            # Add execution timing to debug info
            if agent_response.debug:
                agent_response.debug["execution_time_ms"] = execution_time_ms
            else:
                agent_response.debug = {"execution_time_ms": execution_time_ms}
            
            logger.debug(f"[SESSION] Extending conversation with {len(agent_response.messages)} messages")
            self.conversation.messages.extend(agent_response.messages)
            s, count = conv_service.add_messages(self.conversation.conversation_id, agent_response.messages)
            if not s:
                m = f"Failed to save agent response messages to conversation {self.conversation_id}"
                logger.error(m)
                raise ValueError(m)

            logger.info(f"[SESSION] Saved {len(agent_response.messages)} messages, total count: {count}")
            agent_response.total_message_count = count

            # Generate title for first message
            if is_first_message:
                logger.debug(f"[SESSION] Scheduling title generation for first message")
                asyncio.create_task(self.generate_title(current_user=current_user, save=True))

            logger.info(f"[SESSION] Query processing completed successfully")
            return agent_response

        except Exception as e:
            logger.error(f"[SESSION] Error processing query: {str(e)}", exc_info=True)
            raise e


    async def handle_user_query_streamed(self, query: str, system_prompt: str = SYSTEM_PROMPT, current_user: UserBase | None = None):
        # todo:
        raise NotImplementedError("Streaming not implemented yet")
        
    async def generate_title(self, current_user: UserBase | None, save: bool = True) -> str:
        """
        Generate a concise title for a conversation based on last user + agent messages.
        """
        if not self.conversation:
            return settings.default_conversation_title

        recent_messages = self.conversation.messages[-2:]  # Last user+assistant pair
        content_for_title = "\n".join(
            f"{msg.role}: {msg.content}" for msg in recent_messages
        )

        # Prompt for title generation
        user_role = "doctor" if (current_user and current_user.is_doctor) else "user"
        title_prompt = (
            f"Based on the following conversation between a {user_role} and an AI assistant, "
            "generate a concise and descriptive title (3-5 words) that captures the main topic or question being discussed.\n\n"
            f"{content_for_title}\n\n"
            "Title:"
        )

        # Call the agent with the title generation prompt
        result = self.agent.invoke(
            {"messages": [{"role": "system", "content": title_prompt}]},
            config={"recursion_limit": 10},
        ) # type: ignore

        generated_title = (
            result["messages"][-1].content.strip() if result.get("messages") else "Conversation"
        )
        logger.info(f"Generated title: {generated_title}")
        if save:
            self.conversation.title = generated_title
            conv_service.update_conversation_title(self.conversation.conversation_id, generated_title)
        return generated_title