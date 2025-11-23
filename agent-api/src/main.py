from __future__ import annotations
from typing import Any, Literal
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
from dotenv import load_dotenv
import uuid

# * PROJECT MODULES
import printmeup as pm
from vector_store import VectorStoreManager
from pdf_processor import PDFProcessor
from rag_chain import RAGChain

# * LANGCHAIN
from langchain.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain.agents import create_agent
from langchain_ollama import OllamaLLM

# section - CONSTANTS

load_dotenv()

DEFAULT_USER_GREETING = "Merhaba"

# * huggingface model IDs
# MODEL_ID = "google/gemma-3-4b-it" # * >8gb
# MODEL_ID = "google/gemma-3-1b-it" # * ~4gb
# MODEL_ID = "google/medgemma-4b-pt" # * >8gb

# * ollama model names
# MODEL_NAME = "gemma3:latest"
MODEL_NAME = "llama3:latest"

# * ollama server URL
# OLLAMA_URL = "http://10.91.136.163:11434" # * over zerotier network
OLLAMA_URL = "http://localhost:11434"

# section - PUBLIC VARIABLES

sessions: dict[str, BaseSession] = dict()

# section - HELPERS


# section - SESSION

class BaseSession:
    def __init__(self):
        self.id = self.set_id()
        
    def set_id(self) -> str:
        return str(uuid.uuid4())

class TextSession(BaseSession):
    def __init__(self):
        super().__init__()
        self.sek = SekLangchain(session=self)
        self.accept_sek_text_delta = False

    def handle_text_message_sync(self, text_input: str):
        self.sek.handle_message_sync(text_input)

    async def handle_text_message_async(self, text_input: str):
        await self.sek.handle_message_async(text_input)

    async def handle_sek_text_delta(self, delta: str):
        if delta == "" or not self.accept_sek_text_delta:
            # * if "" but not final response, ignore
            return
        print(delta, end="", flush=True if delta != "" else False)

    async def handle_final_sek_response(self):
        if not self.accept_sek_text_delta:
            return
        print("")
        self.accept_sek_text_delta = False
        
    async def handle_full_sek_response(self, response: str):
        print(response)

    async def interrupt(self):
        await self.sek.interrupt()

    async def start_background_tasks(self):
        self.sek.start_background_tasks()

    async def cleanup(self):
        await self.sek.cleanup()

class TextSessionWS(TextSession):
    def __init__(self, ws: WebSocket):
        super().__init__()
        self.ws = ws

    async def handle_sek_text_delta(self, delta: str):
        if delta == "" or not self.accept_sek_text_delta:
            # * if "" but not final response, ignore
            return
        await self.ws.send_json({"type": "text_delta", "data": delta})
        print(delta, end="", flush=True if delta != "" else False)

    async def handle_final_sek_response(self):
        if not self.accept_sek_text_delta:
            return
        await self.ws.send_json({"type": "text_final"})
        print("")
        self.accept_sek_text_delta = False

    async def interrupt(self):
        await self.ws.send_json({"type": "interrupt"})
        await self.sek.interrupt()

# section - SEK

class BaseSek():
    def __init__(self):
        pass

class SekLangchain(BaseSek):
    def __init__(self, session: TextSession):
        self.session = session
        self.pdf_processor: PDFProcessor | None = None
        self.vsm = VectorStoreManager(
            ollama_model_name=MODEL_NAME,
        )
        self.vectorstore = self.vsm.load_vectorstore()
        if not self.vectorstore:
            self.pdf_processor = PDFProcessor()
            chunks = self.pdf_processor.process_pdfs()
            self.vectorstore = self.vsm.create_vectorstore(chunks)
            
        self.rag_chain = RAGChain(
            retriever=self.vectorstore.as_retriever(search_kwargs={"k": 5}),
            ollama_model_name=MODEL_NAME,
            ollama_base_url=OLLAMA_URL,
            temperature=0.7,
        )
    
    def start_background_tasks(self):
        pass
    
    def handle_message_sync(self, message: str):
        pass
    
    async def handle_message_async(self, message: str):
        pass
    
    async def interrupt(self):
        pass
    
    async def cleanup(self):
        pass            

class SekLangchainAsync(BaseSek):
    def __init__(self, session: TextSession):
        self.session = session
        self.interruptable = False
        self.interrupted = False
        self.new_message_queue = asyncio.Queue(maxsize=100)
        self.llm_task = None
        self.process_message_queue_task: asyncio.Task | None = None
        
        self.llm_task: asyncio.Task | None = None
        
        # TODO
        # self.agent
        # self.messages

    def handle_message_sync(self, message: str):
        """
        Add message to the processing queue.
        A thread calls this method.
        """
        self.new_message_queue.put_nowait(message)
        
    async def handle_message_async(self, message: str):
        """
        Add message to the processing queue.
        An async context calls this method.
        """
        await self.session.interrupt() 
        self.new_message_queue.put_nowait(message)

    async def process_message_queue_taskfunc(self):
        try:
            while True:
                message = await self.new_message_queue.get()
                try:
                    await self.session.interrupt() # * if handled message sync. else, will be already interrupted
                    self.llm_task = asyncio.create_task(self.llm_taskfunc(message))
                finally:
                    self.new_message_queue.task_done()
        except asyncio.CancelledError:
            pm.inf("LLM message processor cancelled")
        except Exception as e:
            pm.err(e)
        finally:
            if self.llm_task:
                await self.llm_task
            self.process_message_queue_task = None

    async def llm_taskfunc(self, message: str):
        o = ""
        try:
            self.session.accept_sek_text_delta = True
            self.interrupted = False
            self.interruptable = True
            pm.inf("generating llm response for:\n" + message)
            
            # TODO: handle streaming response from langchain LLM
            
        except asyncio.CancelledError:
            pm.inf("LLM task cancelled")
        except Exception as e:
            pm.err(e)
        finally:
            
            # TODO handle
            pass

    def start_background_tasks(self):
        if not self.process_message_queue_task:
            self.process_message_queue_task = asyncio.create_task(
                self.process_message_queue_taskfunc()
            )

    async def interrupt(self):
        """
        Interrupt current LLM response generation.
        """
        pm.inf("Interrupting LLM response generation")
        if self.interruptable and not self.interrupted:
            self.interrupted = True
            pm.inf("LLM is interruptable, interrupting")
            if self.llm_task:
                await self.llm_task

    async def cleanup(self):
        try:
            if self.process_message_queue_task:
                self.process_message_queue_task.cancel()
                try:
                    await self.process_message_queue_task
                except asyncio.CancelledError:
                    pass
        except Exception as e:
            pm.err(e)

# section - APP

app = FastAPI(title="MedicaLLM Agents API", version="0.1.0")

@app.websocket("/ws/text-session")
async def websocket_endpoint_text_session(
    websocket: WebSocket,
):
    await websocket.accept()
    pm.suc(f"WebSocket connection from {websocket.client} accepted @/text-session")
    session = TextSessionWS(
        ws=websocket,
    )
    try:
        await session.start_background_tasks()
        await session.handle_text_message_async(DEFAULT_USER_GREETING)
        while True:
            data = await websocket.receive_json()
            if data.get("type") == "text":
                text = data.get("data")
                await session.handle_text_message_async(text)
    except WebSocketDisconnect:
        pm.inf(
            f"WebSocket connection from {websocket.client} disconnected @/text-session"
        )
    except Exception as e:
        pm.err(e)
    finally:
        try:
            await session.cleanup()
            pm.inf(f"Cleaned up session for {websocket.client} @/text-session")
        except Exception as e:
            pm.err(e)

@app.get("/")
async def endpoint_root():
    html_content = """
    <!DOCTYPE html>
    <html>
        <head>
            <title>MedicaLLM Agents API Health Check</title>
            <link rel="icon" type="image/x-icon" href="/favicon.ico">
        </head>
        <body>
            <button onclick="location.href='/health'">Health Check</button>
            <script>
            </script>
        </body>
    </html>
    """
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/invoke-llm")
async def endpoint_invoke_llm(prompt: str):
    pm.inf(f"Invoking Ollama LLM with prompt: {prompt}")
    return {"response": OllamaLLM(model=MODEL_NAME, base_url=OLLAMA_URL).invoke(prompt)}

# http://localhost:2580/invoke-llm/rag/qa?prompt=What%20is%20MedicaLLM%3F
@app.get("/invoke-llm/rag/{chain_type}")
async def endpoint_invoke_llm_rag(chain_type: str, prompt: str):    
    pm.inf(f"Invoking Ollama LLM RAG chain with prompt: {prompt}")
    
    global sessions
    session = sessions.get("default", None)
    if not isinstance(session, TextSession):
        return {"error": "No valid default session found."}
    
    # * Load vector store
    vsm = VectorStoreManager(
        ollama_model_name=MODEL_NAME,
    )
    vectorstore = vsm.load_vectorstore()
    if not vectorstore:
        pdf_processor = PDFProcessor()
        chunks = pdf_processor.process_pdfs()
        vectorstore = vsm.create_vectorstore(chunks)
            
    if chain_type != "qa" and chain_type != "conversational":
        chain_type = "qa"
    
    # * Query RAG chain
    result = session.sek.rag_chain.query(question=prompt, chain_type=chain_type)
    
    response = {
        "answer": result["answer"],
        "source_documents": [
            {
                "page_content": doc.page_content,
                "metadata": doc.metadata
            } for doc in result["source_documents"]
        ]
    }
    if result.get("chat_history", None):
        response["chat_history"] = result["chat_history"]
        
    return response

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("../static/favicon.ico")

@app.get("/test-system")
async def endpoint_test_system():
    pass

@app.get("/health")
async def endpoint_health():
    return {"status": "ok"}

# section - MAIN

def main():
    global sessions
    default_session = TextSession()
    default_session.id = "default"
    sessions[default_session.id] = default_session
    pm.suc("Created default session for MedicaLLM Agents API")
    
    uvicorn.run(app, host="0.0.0.0", port=2580)

if __name__ == "__main__":
    main()
    