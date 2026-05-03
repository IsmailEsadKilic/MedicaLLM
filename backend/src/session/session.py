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
from ..conversations.models import Conversation, Message, ToolExecution
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

        # Collect comprehensive tool execution information
        tool_executions = []
        tools_used = []  # Legacy support
        tool_results = []  # Legacy support

        if result.get("messages"):
            messages = result["messages"]
            for i, msg in enumerate(messages):
                if hasattr(msg, "tool_calls") and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        t_name = tool_call.get("name")
                        t_id = tool_call.get("id")
                        t_args = tool_call.get("args", {})
                        
                        if t_name:
                            tools_used.append(t_name)  # Legacy
                            
                            # Find corresponding tool response
                            tool_result_content = ""
                            tool_error = None
                            for j in range(i + 1, len(messages)):
                                next_msg = messages[j]
                                if hasattr(next_msg, "tool_call_id") and next_msg.tool_call_id == t_id:
                                    tool_result_content = next_msg.content
                                    tool_results.append(tool_result_content)  # Legacy
                                    
                                    # Check if result indicates an error
                                    if "error" in tool_result_content.lower()[:100]:
                                        tool_error = tool_result_content[:500]
                                    break
                            
                            # Create detailed tool execution record
                            tool_exec = ToolExecution(
                                tool_name=t_name,
                                tool_args=t_args,
                                tool_result=tool_result_content,
                                error=tool_error,
                            )
                            tool_executions.append(tool_exec)

        # Create message with structured sources and comprehensive tool info
        assistant_message = Message(
            role="assistant",
            content=ai_response,
            tools_used=tools_used,  # Legacy
            tool_results=tool_results,  # Legacy
            tool_executions=tool_executions,  # New comprehensive tracking
            sources=sources if sources else [],
            debug={"tool_debug": tool_debug} if tool_debug else {},
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
        """
        Process a user query through the agent with streaming support.
        Yields chunks of the response as they are generated.
        
        Yields:
            dict: Streaming events with type and content
        """
        try:
            logger.debug(f"[SESSION STREAM] handle_user_query_streamed called for session {self.session_id}")
            logger.debug(f"[SESSION STREAM] Query length: {len(query)} chars")

            # Generate a unique request ID for cross-thread source/debug propagation
            request_id = _uuid.uuid4().hex
            set_request_id(request_id)
            logger.debug(f"[SESSION STREAM] Request ID: {request_id}")

            if not self.conversation:
                m = f"No conversation found for session {self.session_id} with conversation ID {self.conversation_id}"
                logger.error(m)
                raise ValueError(m)

            is_first_message = len(self.conversation.messages) == 0 if self.conversation else False
            logger.debug(f"[SESSION STREAM] Is first message: {is_first_message}, current message count: {len(self.conversation.messages)}")

            # Deduplication check
            should_append = True
            if self.conversation.messages:
                last_msg = self.conversation.messages[-1]
                if last_msg.role == "user" and last_msg.content == query:
                    should_append = False
                    logger.warning(f"[SESSION STREAM] Duplicate query detected, skipping append")

            if should_append:
                logger.debug(f"[SESSION STREAM] Appending user message to conversation")
                user_message = Message(role="user", content=query)
                self.conversation.messages.append(user_message)
                conv_service.add_message(self.conversation.conversation_id, user_message)

            message_history = self.get_message_history()
            logger.debug(f"[SESSION STREAM] Message history length: {len(message_history)} messages")
            message_history = [{"role": "system", "content": system_prompt}] + message_history

            # Track execution time
            start_time = time.time()
            logger.info(f"[SESSION STREAM] Starting agent streaming invocation")
            
            # Track tool executions
            tool_executions = []
            current_tool_call = {}  # Track current tool being executed
            
            # Stream from agent
            full_response = ""
            async for event in self.agent.langchain_agent.astream_events(
                {"messages": message_history},
                config={"recursion_limit": 50},
                version="v2"
            ):
                kind = event.get("event")
                
                # Stream token-by-token from the LLM
                if kind == "on_chat_model_stream":
                    content = event.get("data", {}).get("chunk", {})
                    if hasattr(content, "content") and content.content:
                        chunk_text = content.content
                        full_response += chunk_text
                        yield {"type": "content", "content": chunk_text}
                
                # Log tool calls
                elif kind == "on_tool_start":
                    tool_name = event.get("name", "unknown")
                    tool_input = event.get("data", {}).get("input", {})
                    tool_start_time = time.time()
                    
                    logger.debug(f"[SESSION STREAM] Tool started: {tool_name} with args: {tool_input}")
                    
                    # Store current tool call info
                    current_tool_call = {
                        "tool_name": tool_name,
                        "tool_args": tool_input,
                        "start_time": tool_start_time,
                    }
                    
                    yield {
                        "type": "tool_start", 
                        "tool_name": tool_name,
                        "tool_args": tool_input,
                    }
                
                elif kind == "on_tool_end":
                    tool_name = event.get("name", "unknown")
                    tool_output = event.get("data", {}).get("output", "")
                    tool_end_time = time.time()
                    
                    # Calculate execution time
                    execution_time_ms = None
                    if current_tool_call.get("start_time"):
                        execution_time_ms = (tool_end_time - current_tool_call["start_time"]) * 1000
                    
                    logger.debug(f"[SESSION STREAM] Tool completed: {tool_name} in {execution_time_ms:.2f}ms")
                    
                    # Check for errors in output
                    tool_error = None
                    if isinstance(tool_output, str) and "error" in tool_output.lower()[:100]:
                        tool_error = tool_output[:500]
                    
                    # Create tool execution record
                    tool_exec = ToolExecution(
                        tool_name=tool_name,
                        tool_args=current_tool_call.get("tool_args", {}),
                        tool_result=str(tool_output),
                        execution_time_ms=execution_time_ms,
                        error=tool_error,
                    )
                    tool_executions.append(tool_exec)
                    
                    yield {
                        "type": "tool_end", 
                        "tool_name": tool_name,
                        "execution_time_ms": execution_time_ms,
                    }
                    
                    # Reset current tool call
                    current_tool_call = {}
            
            execution_time_ms = (time.time() - start_time) * 1000
            logger.info(f"[SESSION STREAM] Agent streaming completed in {execution_time_ms:.2f}ms")
            
            # Get sources and tool debug info
            sources = get_last_search_sources(request_id=request_id)
            tool_debug = get_last_tool_debug(request_id=request_id)
            
            # Create assistant message with comprehensive tool execution data
            assistant_message = Message(
                role="assistant",
                content=full_response,
                tool_executions=tool_executions,
                sources=sources if sources else [],
                debug={
                    "execution_time_ms": execution_time_ms,
                    "tool_debug": tool_debug,
                } if tool_debug else {"execution_time_ms": execution_time_ms},
            )
            
            # Save to conversation
            self.conversation.messages.append(assistant_message)
            conv_service.add_message(self.conversation.conversation_id, assistant_message)
            logger.info(f"[SESSION STREAM] Saved assistant message to conversation")
            
            # Generate title for first message
            if is_first_message:
                logger.debug(f"[SESSION STREAM] Scheduling title generation for first message")
                asyncio.create_task(self.generate_title(current_user=current_user, save=True))
            
            # Yield final metadata with comprehensive tool execution info
            yield {
                "type": "done",
                "sources": sources,
                "tool_executions": [t.model_dump() for t in tool_executions],
                "final_content": full_response,
                "execution_time_ms": execution_time_ms,
                "debug": tool_debug,
            }
            
        except Exception as e:
            logger.error(f"[SESSION STREAM] Error processing streamed query: {str(e)}", exc_info=True)
            yield {"type": "error", "error": str(e)}
            raise e
        
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