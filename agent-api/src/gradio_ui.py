import gradio as gr
import requests
import asyncio
import websockets
import json
from typing import Generator
from datetime import datetime

# API Configuration
API_BASE_URL = "http://localhost:2580"
WS_URL = "ws://localhost:2580/ws/text-session"

# Global WebSocket connection
ws_connection = None

# Custom CSS for better styling
custom_css = """
.gradio-container {
    max-width: 1400px !important;
    margin: auto !important;
}
.header-section {
    text-align: center;
    padding: 20px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    border-radius: 10px;
    margin-bottom: 20px;
}
.header-section h1 {
    margin: 0;
    font-size: 2.5em;
    font-weight: bold;
}
.header-section p {
    margin: 10px 0 0 0;
    font-size: 1.2em;
    opacity: 0.9;
}
.status-card {
    padding: 15px;
    border-radius: 8px;
    background: #f8f9fa;
    border-left: 4px solid #667eea;
}
.tab-content {
    padding: 20px;
}
footer {
    text-align: center;
    padding: 20px;
    color: #666;
}
"""

async def connect_websocket():
    """Establish WebSocket connection"""
    global ws_connection
    try:
        ws_connection = await websockets.connect(WS_URL)
        return True
    except Exception as e:
        print(f"WebSocket connection error: {e}")
        return False

async def send_message_ws(message: str):
    """Send message via WebSocket and yield streaming responses"""
    global ws_connection
    
    if ws_connection is None or ws_connection.state.name != 'OPEN':
        await connect_websocket()
    
    if ws_connection is None:
        yield "Error: Could not connect to WebSocket"
        return
    
    try:
        # Send message
        await ws_connection.send(json.dumps({
            "type": "text",
            "data": message
        }))
        
        # Receive streaming response
        full_response = ""
        async for response in ws_connection:
            data = json.loads(response)
            if data.get("type") == "text_delta":
                delta = data.get("data", "")
                full_response += delta
                yield full_response
            elif data.get("type") == "text_final":
                break
            elif data.get("type") == "interrupt":
                yield full_response + "\n[Interrupted]"
                break
                
    except Exception as e:
        yield f"Error: {str(e)}"

def chat_with_llm(message: str, history: list) -> Generator[str, None, None]:
    """Chat interface for WebSocket session"""
    # Run async generator in event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        async def generate():
            async for response in send_message_ws(message):
                yield response
        
        gen = generate()
        while True:
            try:
                result = loop.run_until_complete(gen.__anext__())
                yield result
            except StopAsyncIteration:
                break
    finally:
        loop.close()

def invoke_llm_simple(prompt: str) -> str:
    """Simple LLM invocation via REST API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/invoke-llm",
            params={"prompt": prompt},
            timeout=60
        )
        if response.status_code == 200:
            return response.json().get("response", "No response")
        else:
            return f"Error: {response.status_code} - {response.text}"
    except Exception as e:
        return f"Error: {str(e)}"

def invoke_llm_rag(prompt: str) -> tuple[str, str]:
    """RAG-based LLM invocation via REST API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/invoke-llm/rag/qa",
            params={"prompt": prompt},
            timeout=120
        )
        if response.status_code == 200:
            data = response.json()
            answer = data.get("answer", "No answer")
            
            # Format source documents
            sources = data.get("source_documents", [])
            sources_text = "\n\n**Sources:**\n"
            for i, doc in enumerate(sources, 1):
                sources_text += f"\n**Source {i}:**\n"
                sources_text += f"- Content: {doc['page_content'][:200]}...\n"
                sources_text += f"- Metadata: {doc['metadata']}\n"
            
            return answer, sources_text
        else:
            return f"Error: {response.status_code}", response.text
    except Exception as e:
        return f"Error: {str(e)}", ""

def check_health() -> str:
    """Check API health"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            return "✅ API is healthy"
        else:
            return f"⚠️ API returned status {response.status_code}"
    except Exception as e:
        return f"❌ API is not reachable: {str(e)}"

# Create Gradio Interface
with gr.Blocks(title="MedicaLLM API Interface", theme="soft") as demo:
    gr.Markdown("# 🏥 MedicaLLM API Interface")
    gr.Markdown("Simple interface to interact with the MedicaLLM Agents API")
    
    # Health Check Section
    with gr.Row():
        health_btn = gr.Button("🔍 Check API Health", variant="secondary")
        health_output = gr.Textbox(label="Health Status", interactive=False)
    
    health_btn.click(check_health, outputs=health_output)
    
    gr.Markdown("---")
    
    # Chat Interface (WebSocket)
    with gr.Tab("💬 Chat Session (WebSocket)"):
        gr.Markdown("### Real-time chat with streaming responses")
        chatbot = gr.Chatbot(height=400)
        msg = gr.Textbox(
            label="Your Message",
            placeholder="Type your message here...",
            lines=2
        )
        chat_btn = gr.Button("Send", variant="primary")
        clear_btn = gr.Button("Clear Chat")
        
        def user_message(message, history):
            return "", history + [[message, None]]
        
        def bot_response(history):
            user_msg = history[-1][0]
            bot_msg = ""
            for response in chat_with_llm(user_msg, history):
                bot_msg = response
                history[-1][1] = bot_msg
                yield history
        
        msg.submit(user_message, [msg, chatbot], [msg, chatbot], queue=False).then(
            bot_response, chatbot, chatbot
        )
        chat_btn.click(user_message, [msg, chatbot], [msg, chatbot], queue=False).then(
            bot_response, chatbot, chatbot
        )
        clear_btn.click(lambda: None, None, chatbot, queue=False)
    
    # Simple LLM Invocation
    with gr.Tab("🤖 Simple LLM"):
        gr.Markdown("### Direct LLM invocation without RAG")
        simple_prompt = gr.Textbox(
            label="Prompt",
            placeholder="Enter your prompt...",
            lines=3
        )
        simple_btn = gr.Button("Generate", variant="primary")
        simple_output = gr.Textbox(
            label="Response",
            lines=10,
            interactive=False
        )
        
        simple_btn.click(invoke_llm_simple, inputs=simple_prompt, outputs=simple_output)
    
    # RAG-based LLM
    with gr.Tab("📚 RAG Query"):
        gr.Markdown("### Query with Retrieval-Augmented Generation")
        rag_prompt = gr.Textbox(
            label="Question",
            placeholder="Ask a question about the medical documents...",
            lines=3
        )
        rag_btn = gr.Button("Query RAG", variant="primary")
        rag_answer = gr.Textbox(
            label="Answer",
            lines=8,
            interactive=False
        )
        rag_sources = gr.Markdown(label="Source Documents")
        
        rag_btn.click(
            invoke_llm_rag,
            inputs=rag_prompt,
            outputs=[rag_answer, rag_sources]
        )
    
    gr.Markdown("---")
    gr.Markdown("*Make sure the FastAPI server is running on http://localhost:2580*")

# Launch the interface
if __name__ == "__main__":
    demo.queue()  # Enable queuing for streaming
    demo.launch(
        server_name="0.0.0.0",
        server_port=7860,
        share=False
    )
