import uuid
from typing import Optional, Dict, Any
import asyncio

from .. import printmeup as pm
from ..conversations import service as conv_service
from ..conversations.models import Conversation, Message
from .tools import get_last_search_sources


class Session:
    """
    Session class for managing conversation state and agent interactions.
    Uses LangChain's message format and LangGraph state management.
    """

    def __init__(
        self,
        conversation_id: str,
        user_id: str,
        agent,  # LangGraph agent
    ):
        self.session_id = str(uuid.uuid4())
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.agent = agent

        # Load conversation from database
        self.conversation: Optional[Conversation] = conv_service.get_conversation(conversation_id)

        if not self.conversation:
            pm.war(f"Conversation {conversation_id} not found, creating new one")
            self.conversation = conv_service.create_conversation(
                user_id=user_id, title="New Conversation"
            )

        pm.inf(f"Session initialized: {self.session_id} for conversation {conversation_id}")

    def get_message_history(self) -> list:
        """Get conversation history in LangChain message format."""
        if not self.conversation:
            return []

        messages = []
        for msg in self.conversation.messages:
            if msg.role == "user":
                messages.append({"role": "user", "content": msg.content})
            elif msg.role == "assistant":
                messages.append({"role": "assistant", "content": msg.content})
        return messages

    async def handle_user_query(self, query: str) -> Dict[str, Any]:
        """Process a user query through the agent."""
        try:
            pm.inf(f"Processing query: {query[:100]}...")

            is_first_message = len(self.conversation.messages) == 0 if self.conversation else False

            # Deduplication check
            should_append = True
            if self.conversation and self.conversation.messages:
                last_msg = self.conversation.messages[-1]
                if last_msg.role == "user" and last_msg.content == query:
                    pm.inf("Query already in history (skipping append)")
                    should_append = False

            if should_append:
                user_message = Message(role="user", content=query)
                if self.conversation:
                    self.conversation.messages.append(user_message)
                    conv_service.save_conversation(self.conversation)

            message_history = self.get_message_history()
            pm.inf(f"Message history length: {len(message_history)}")

            # Invoke agent
            pm.inf("Invoking agent...")
            result = self.agent.invoke(
                {"messages": message_history},
                config={"recursion_limit": 50},
            )

            # Extract AI response
            ai_response = (
                result["messages"][-1].content
                if result.get("messages")
                else "No response generated"
            )
            pm.inf(f"AI response length: {len(ai_response)} chars")

            # Check for search sources
            sources = get_last_search_sources()

            # Determine which tool was used
            tool_used = None
            tool_result = None

            if result.get("messages"):
                messages = result["messages"]
                for i in range(len(messages) - 1, -1, -1):
                    msg = messages[i]
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        tool_call = msg.tool_calls[0]
                        tool_used = tool_call.get("name")
                        tool_call_id = tool_call.get("id")

                        for j in range(i + 1, len(messages)):
                            next_msg = messages[j]
                            if hasattr(next_msg, "tool_call_id") and next_msg.tool_call_id == tool_call_id:
                                tool_result = next_msg.content
                                break
                            elif next_msg.type == "tool" and not tool_result:
                                tool_result = next_msg.content
                                break
                        break

            # Save AI response
            ai_message = Message(
                role="assistant",
                content=ai_response,
                tool_used=tool_used,
                tool_result=tool_result,
                sources=sources if sources else None,
            )
            if self.conversation:
                self.conversation.messages.append(ai_message)
                conv_service.save_conversation(self.conversation)

            # Generate title for first message
            if is_first_message and self.conversation:
                asyncio.create_task(self._generate_and_update_title(query))

            pm.suc("Query processed successfully")

            return {
                "success": True,
                "answer": ai_response,
                "conversation_id": self.conversation_id,
                "message_count": len(self.conversation.messages) if self.conversation else 0,
                "sources": sources if sources else [],
                "tool_used": tool_used,
                "tool_result": tool_result,
            }

        except Exception as e:
            pm.err(e=e, m="Error processing query")
            return {
                "success": False,
                "error": str(e),
                "answer": f"Error processing your query: {str(e)}",
                "sources": [],
                "tool_used": None,
                "tool_result": None,
            }

    async def stream_query(self, query: str):
        """Stream agent response for a user query."""
        try:
            pm.inf(f"Streaming query: {query[:100]}...")

            user_message = Message(role="user", content=query)
            if self.conversation:
                self.conversation.messages.append(user_message)
                conv_service.save_conversation(self.conversation)

            message_history = self.get_message_history()

            full_response = ""
            async for chunk in self.agent.astream(
                {"messages": message_history}, stream_mode="values"
            ):
                if chunk.get("messages"):
                    latest_message = chunk["messages"][-1]
                    if hasattr(latest_message, "content") and latest_message.content:
                        new_content = latest_message.content[len(full_response):]
                        full_response = latest_message.content
                        if new_content:
                            yield {"type": "content", "content": new_content}

            # Save final response
            ai_message = Message(role="assistant", content=full_response)
            if self.conversation:
                self.conversation.messages.append(ai_message)
                conv_service.save_conversation(self.conversation)

            yield {"type": "done", "conversation_id": self.conversation_id}

        except Exception as e:
            pm.err(e=e, m="Error streaming query")
            yield {"type": "error", "error": str(e)}

    def clear_history(self):
        """Clear conversation history."""
        if self.conversation:
            self.conversation.messages = []
            conv_service.save_conversation(self.conversation)
            pm.inf(f"Conversation history cleared for {self.conversation_id}")

    async def _generate_title(self, first_query: str) -> str:
        """Generate a concise conversation title based on the first query."""
        try:
            # Fallback to truncated query
            title = first_query[:50] + "..." if len(first_query) > 50 else first_query
            return title
        except Exception as e:
            pm.err(e=e, m="Error generating title")
            return first_query[:50] + "..." if len(first_query) > 50 else first_query

    async def _generate_and_update_title(self, first_query: str):
        """Generate and update the conversation title in the background."""
        try:
            title = await self._generate_title(first_query)
            if self.conversation:
                conv_service.update_conversation_title(
                    conversation_id=self.conversation_id, title=title
                )
                self.conversation.title = title
                pm.inf(f"Title updated: {title}")
        except Exception as e:
            pm.err(e=e, m="Error in title generation task")
