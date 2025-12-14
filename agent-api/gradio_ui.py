"""
MedicaLLM Gradio UI - Simple Interface for Testing the API
"""

import gradio as gr
import requests
import json
from typing import List, Tuple
import uuid

# API Configuration
API_BASE_URL = "http://localhost:2580"
USER_ID = "test_user_" + str(uuid.uuid4())[:8]  # Generate a test user ID
current_conversation_id = None

def create_new_conversation():
    """Create a new conversation and return its ID."""
    global current_conversation_id
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/api/create-conversation",
            json={
                "user_id": USER_ID,
                "title": "New Conversation"
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            current_conversation_id = data["conversation_id"]
            return current_conversation_id
        else:
            return None
    except Exception as e:
        print(f"Error creating conversation: {e}")
        return None


def send_message(message: str, history: List[Tuple[str, str]]) -> Tuple[List[Tuple[str, str]], str]:
    """
    Send a message to the API and get the response.
    
    Args:
        message: User's message
        history: Chat history
        
    Returns:
        Updated history and empty string for input box
    """
    global current_conversation_id
    
    if not message.strip():
        return history, ""
    
    # Create conversation if needed
    if current_conversation_id is None:
        current_conversation_id = create_new_conversation()
        if current_conversation_id is None:
            history.append((message, "❌ Error: Could not create conversation"))
            return history, ""
    
    # Add user message to history immediately
    history.append((message, "🤔 Thinking..."))
    
    try:
        # Send query to API
        response = requests.post(
            f"{API_BASE_URL}/api/query",
            json={
                "conversation_id": current_conversation_id,
                "query": message
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "No response")
            # Update the last message with actual response
            history[-1] = (message, answer)
        else:
            error_msg = f"❌ Error {response.status_code}: {response.text}"
            history[-1] = (message, error_msg)
            
    except Exception as e:
        history[-1] = (message, f"❌ Error: {str(e)}")
    
    return history, ""


def send_message_stream(message: str, history: List[Tuple[str, str]]):
    """
    Send a message and stream the response.
    
    Args:
        message: User's message
        history: Chat history
        
    Yields:
        Updated history
    """
    global current_conversation_id
    
    if not message.strip():
        yield history
        return
    
    # Create conversation if needed
    if current_conversation_id is None:
        current_conversation_id = create_new_conversation()
        if current_conversation_id is None:
            history.append((message, "❌ Error: Could not create conversation"))
            yield history
            return
    
    # Add user message to history
    history.append((message, ""))
    yield history
    
    try:
        # Stream response from API
        response = requests.post(
            f"{API_BASE_URL}/api/query-stream",
            json={
                "conversation_id": current_conversation_id,
                "query": message
            },
            stream=True
        )
        
        full_response = ""
        
        if response.status_code == 200:
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]  # Remove 'data: ' prefix
                        try:
                            data = json.loads(data_str)
                            if data.get("type") == "content":
                                full_response += data.get("content", "")
                                history[-1] = (message, full_response)
                                yield history
                            elif data.get("type") == "error":
                                history[-1] = (message, f"❌ Error: {data.get('error')}")
                                yield history
                                return
                        except json.JSONDecodeError:
                            continue
        else:
            history[-1] = (message, f"❌ Error {response.status_code}: {response.text}")
            yield history
            
    except Exception as e:
        history[-1] = (message, f"❌ Error: {str(e)}")
        yield history


def clear_conversation():
    """Clear the current conversation and start fresh."""
    global current_conversation_id
    current_conversation_id = None
    return [], ""


def get_example_queries():
    """Return example queries for quick testing."""
    return [
        "What is Warfarin?",
        "Does Aspirin interact with Warfarin?",
        "What are the side effects of Metformin?",
        "How to manage type 2 diabetes?",
        "Tell me about Lisinopril",
    ]


# Create Gradio Interface
with gr.Blocks(title="MedicaLLM - Medical AI Assistant") as demo:
    gr.Markdown(
        """
        # 🏥 MedicaLLM - Medical AI Assistant
        
        Ask questions about drugs, drug interactions, or general medical information.
        
        **Features:**
        - 💊 Drug information lookup
        - ⚠️ Drug interaction checking
        - 📚 Medical document search with sources
        
        ⚕️ **Disclaimer:** This is for informational purposes only. Always consult healthcare professionals.
        """
    )
    
    with gr.Row():
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                label="Chat History",
                height=500,
                bubble_full_width=False,
                avatar_images=(None, "🤖")
            )
            
            with gr.Row():
                msg_input = gr.Textbox(
                    label="Your Message",
                    placeholder="Ask about drugs, interactions, or medical conditions...",
                    scale=4,
                    lines=2
                )
                send_btn = gr.Button("Send 📤", variant="primary", scale=1)
            
            with gr.Row():
                clear_btn = gr.Button("New Conversation 🔄", variant="secondary")
                stream_toggle = gr.Checkbox(label="Stream Response", value=True)
        
        with gr.Column(scale=1):
            gr.Markdown("### 📋 Example Queries")
            examples = gr.Examples(
                examples=get_example_queries(),
                inputs=msg_input,
                label=None
            )
            
            gr.Markdown(
                """
                ### 🔧 Status
                
                **API URL:** `http://localhost:2580`
                
                **User ID:** `{}`
                
                **Conversation ID:** Will be created on first message
                
                ### 💡 Tips
                
                - Use **streaming** for real-time responses
                - Click **New Conversation** to start fresh
                - Try the example queries to get started
                """.format(USER_ID)
            )
    
    # Event handlers
    def submit_message(message, history, use_stream):
        """Handle message submission with or without streaming."""
        if use_stream:
            return send_message_stream(message, history)
        else:
            return send_message(message, history)
    
    # Non-streaming submission
    msg_input.submit(
        lambda msg, hist, stream: send_message_stream(msg, hist) if stream else send_message(msg, hist),
        inputs=[msg_input, chatbot, stream_toggle],
        outputs=[chatbot, msg_input]
    )
    
    send_btn.click(
        lambda msg, hist, stream: send_message_stream(msg, hist) if stream else send_message(msg, hist),
        inputs=[msg_input, chatbot, stream_toggle],
        outputs=[chatbot, msg_input]
    )
    
    clear_btn.click(
        clear_conversation,
        inputs=[],
        outputs=[chatbot, msg_input]
    )


if __name__ == "__main__":
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                 🏥 MedicaLLM Gradio UI                      ║
    ╚══════════════════════════════════════════════════════════════╝
    
    Starting Gradio interface...
    
    Make sure the API server is running at: http://localhost:2580
    
    User ID: {}
    
    """.format(USER_ID))
    
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
