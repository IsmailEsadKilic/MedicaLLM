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
            pm.inf(f"💬 Processing query: {query[:100]}...")
            
            # Check if this is the first message
            is_first_message = len(self.conversation.messages) == 0 if self.conversation else False
            
            # Add user message to conversation history
            user_message = Message(role="user", content=query)
            if self.conversation:
                self.conversation.messages.append(user_message)
                self.dynamodb_manager.save_conversation(self.conversation)
            
            # Get existing message history
            message_history = self.get_message_history()
            
            # Invoke the agent
            result = self.agent.invoke({
                "messages": message_history
            })
            
            # Extract AI response
            ai_response = result["messages"][-1].content if result.get("messages") else "No response generated"
            
            # Check if search_medical_documents was used and get sources
            sources = get_last_search_sources()
            
            # Determine which tool was used by checking the message history
            tool_used = None
            if result.get("messages"):
                for msg in reversed(result["messages"]):
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        tool_used = msg.tool_calls[0].get('name') if msg.tool_calls else None
                        break
            
            # Save AI response to conversation with sources if available
            ai_message = Message(
                role="assistant",
                content=ai_response,
                tool_used=tool_used,
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
                "sources": sources if sources else None,
                "tool_used": tool_used
            }
            
        except Exception as e:
            pm.err(e=e, m="Error processing query")
            return {
                "success": False,
                "error": str(e),
                "answer": f"❌ Error processing your query: {str(e)}"
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