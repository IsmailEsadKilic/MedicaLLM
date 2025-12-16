import uuid
from typing import Optional, Dict, Any
import printmeup as pm
import asyncio
from langchain_ollama import ChatOllama

from dynamodb_manager import DynamoDBManager
from models import Conversation, Message
from medical_agent import get_last_search_sources


class Session:
    """
    Session class for managing conversation state and agent interactions.
    Uses LangChain's message format and LangGraph state management.
    """
    
    def __init__(
        self,
        conversation_id: str,
        user_id: str,
        agent,  # LangGraph agent created by create_agent
        dynamodb_manager: DynamoDBManager
    ):
        """
        Initialize a session for a user conversation.
        
        Args:
            conversation_id: Unique identifier for the conversation
            user_id: User ID who owns the conversation
            agent: LangGraph agent instance
            dynamodb_manager: DynamoDB manager for persistence
        """
        self.session_id = str(uuid.uuid4())
        self.conversation_id = conversation_id
        self.user_id = user_id
        self.agent = agent
        self.dynamodb_manager = dynamodb_manager
        
        # Load conversation from database
        self.conversation: Optional[Conversation] = self.dynamodb_manager.get_conversation(conversation_id)
        
        if not self.conversation:
            pm.war(f"Conversation {conversation_id} not found, creating new one")
            self.conversation = self.dynamodb_manager.create_conversation(
                user_id=user_id,
                title="New Conversation"
            )
        
        pm.inf(f"✅ Session initialized: {self.session_id} for conversation {conversation_id}")
    
    def get_message_history(self) -> list:
        """
        Get conversation history in LangChain message format.
        
        Returns:
            List of LangChain message objects (HumanMessage, AIMessage)
        """
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
            pm.inf(f"💬 [SESSION] Processing query: {query[:100]}...")
            
            # Check if this is the first message
            is_first_message = len(self.conversation.messages) == 0 if self.conversation else False
            
            # Add user message to conversation history
            # Check if the last message is already this query (deduplication)
            should_append = True
            if self.conversation and self.conversation.messages:
                last_msg = self.conversation.messages[-1]
                if last_msg.role == "user" and last_msg.content == query:
                    pm.inf("🔄 [SESSION] Query already in history (skipping append)")
                    should_append = False
            
            if should_append:
                user_message = Message(role="user", content=query)
                if self.conversation:
                    self.conversation.messages.append(user_message)
                    self.dynamodb_manager.save_conversation(self.conversation)
            
            # Get existing message history
            message_history = self.get_message_history()
            pm.inf(f"📜 [SESSION] Message history length: {len(message_history)}")
            
            # Invoke the agent
            pm.inf(f"🤖 [SESSION] Invoking agent...")
            result = self.agent.invoke(
                {"messages": message_history},
                config={"recursion_limit": 50}
            )
            
            pm.inf(f"📊 [SESSION] Agent result keys: {list(result.keys())}")
            pm.inf(f"📊 [SESSION] Messages in result: {len(result.get('messages', []))}")
            
            # Extract AI response (the LLM's natural language response)
            ai_response = result["messages"][-1].content if result.get("messages") else "No response generated"
            pm.inf(f"💬 [SESSION] AI response length: {len(ai_response)} chars")
            pm.inf(f"💬 [SESSION] AI response preview: {ai_response[:200]}...")
            
            # Check if search_medical_documents was used and get sources
            sources = get_last_search_sources()
            
            # Determine which tool was used by checking the message history
            tool_used = None
            tool_result = None
            
            if result.get("messages"):
                messages = result["messages"]
                pm.inf(f"🔍 [DEBUG] Inspecting {len(messages)} messages for tool usage")
                
                # Iterate backwards to find the last tool call
                found_tool_call = False
                for i in range(len(messages) - 1, -1, -1):
                    msg = messages[i]
                    
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        tool_call = msg.tool_calls[0]
                        tool_used = tool_call.get('name')
                        tool_call_id = tool_call.get('id')
                        pm.inf(f"    Found tool call at index {i}: {tool_used} (ID: {tool_call_id})")
                        found_tool_call = True
                        
                        # Search forward for the corresponding ToolMessage
                        for j in range(i + 1, len(messages)):
                            next_msg = messages[j]
                            pm.inf(f"      Scanning index {j}: Type={next_msg.type}")
                            
                            # Check if matches tool_call_id
                            if hasattr(next_msg, 'tool_call_id') and next_msg.tool_call_id == tool_call_id:
                                tool_result = next_msg.content
                                pm.inf(f"      ✅ Matched ToolMessage! Content len: {len(str(tool_result))}")
                                break
                            # Fallback: if it's a ToolMessage (type='tool') and we haven't found a match yet
                            elif next_msg.type == 'tool' and not tool_result:
                                tool_result = next_msg.content
                                pm.inf(f"      ⚠️ Assumed match (type='tool'). Content len: {len(str(tool_result))}")
                                break
                                
                        break # Stop after finding the last tool call
                
                if not found_tool_call:
                     pm.inf("    No tool calls found in message history")

            # Fallback for debugging if still None but tool was used
            if tool_used and tool_result is None:
                pm.war(f"⚠️ Tool {tool_used} was used but no result was captured!")
                tool_result = "Debug: Tool was used but result could not be extracted from history."

            # Save AI response to conversation with sources if available
            ai_message = Message(
                role="assistant",
                content=ai_response,
                tool_used=tool_used,
                tool_result=tool_result,
                sources=sources if sources else None
            )
            if self.conversation:
                self.conversation.messages.append(ai_message)
                self.dynamodb_manager.save_conversation(self.conversation)
            
            # Generate title for first message
            if is_first_message and self.conversation:
                # Don't await - let it run in background
                asyncio.create_task(self._generate_and_update_title(query))
        
            pm.suc("✅ Query processed successfully")
            
            return {
                "success": True,
                "answer": ai_response,
                "conversation_id": self.conversation_id,
                "message_count": len(self.conversation.messages) if self.conversation else 0,
                "sources": sources if sources else [],
                "tool_used": tool_used,
                "tool_result": tool_result
            }
            
        except Exception as e:
            pm.err(e=e, m="Error processing query")
            return {
                "success": False,
                "error": str(e),
                "answer": f"❌ Error processing your query: {str(e)}",
                "sources": [],
                "tool_used": None,
                "tool_result": None
            }
    
    async def stream_query(self, query: str):
        """
        Stream agent response for a user query.
        Yields chunks as they become available.
        
        Args:
            query: User's question or message
            
        Yields:
            dict chunks containing response parts and metadata
        """
        try:
            pm.inf(f"💬 Streaming query: {query[:100]}...")
            
            # Add user message
            user_message = Message(role="user", content=query)
            if self.conversation:
                self.conversation.messages.append(user_message)
                self.dynamodb_manager.save_conversation(self.conversation)
            
            # Get message history
            message_history = self.get_message_history()
            
            # Stream from agent
            full_response = ""
            async for chunk in self.agent.astream({
                "messages": message_history
            }, stream_mode="values"):
                
                # Extract the latest message
                if chunk.get("messages"):
                    latest_message = chunk["messages"][-1]
                    
                    if hasattr(latest_message, 'content') and latest_message.content:
                        # Calculate the new content (diff from previous)
                        new_content = latest_message.content[len(full_response):]
                        full_response = latest_message.content
                        
                        if new_content:
                            yield {
                                "type": "content",
                                "content": new_content
                            }
            
            # Save final response
            ai_message = Message(role="assistant", content=full_response)
            if self.conversation:
                self.conversation.messages.append(ai_message)
                self.dynamodb_manager.save_conversation(self.conversation)
            
            yield {
                "type": "done",
                "conversation_id": self.conversation_id
            }
            
        except Exception as e:
            pm.err(e=e, m="Error streaming query")
            yield {
                "type": "error",
                "error": str(e)
            }
    
    def clear_history(self):
        """Clear conversation history."""
        if self.conversation:
            self.conversation.messages = []
            self.dynamodb_manager.save_conversation(self.conversation)
            pm.inf(f"🗑️ Conversation history cleared for {self.conversation_id}")
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation."""
        if not self.conversation:
            return {"error": "No conversation loaded"}
        
        return {
            "conversation_id": self.conversation.id,
            "user_id": self.conversation.user_id,
            "title": self.conversation.title,
            "message_count": len(self.conversation.messages),
            "created_at": self.conversation.created_at,
            "updated_at": self.conversation.updated_at
        }
    
    async def _generate_title(self, first_query: str) -> str:
        """
        Generate a concise conversation title based on the first query.
        
        Args:
            first_query: The first user message
            
        Returns:
            Generated title string
        """
        try:            
            llm = ChatOllama(
                model="llama2:latest",
                base_url="http://localhost:11434",
                temperature=0.7
            )
            
            prompt = f"""Generate a short, concise title (3-6 words) for a medical conversation that starts with this question:
            
    "{first_query}"
            
    Return ONLY the title, nothing else. Make it descriptive and professional.
            
    Examples:
    - "Warfarin Dosage Information"
    - "Type 2 Diabetes Management"
    - "Drug Interaction Check"
    - "Aspirin Side Effects"
            
    Title:"""
            
            response = llm.invoke(prompt)
            # Extract text content from response
            content = response.content if isinstance(response.content, str) else str(response.content)
            title = content.strip().strip('"').strip("'")
            
            # Limit length
            if len(title) > 60:
                title = title[:57] + "..."
            
            pm.inf(f"Generated title: {title}")
            return title
            
        except Exception as e:
            pm.err(e=e, m="Error generating title")
            # Fallback to truncated query
            return first_query[:50] + "..." if len(first_query) > 50 else first_query
    
    async def _generate_and_update_title(self, first_query: str):
        """
        Generate and update the conversation title in the background.
        
        Args:
            first_query: The first user message
        """
        try:
            title = await self._generate_title(first_query)
            
            if self.conversation:
                self.dynamodb_manager.update_conversation_title(
                    conversation_id=self.conversation_id,
                    title=title
                )
                self.conversation.title = title
                pm.inf(f"✅ Title updated: {title}")
        
        except Exception as e:
            pm.err(e=e, m="Error in title generation task")