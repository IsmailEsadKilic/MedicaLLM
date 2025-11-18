from __future__ import annotations
from typing import Any
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
from dotenv import load_dotenv

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
from langchain_openai import ChatOpenAI
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
MODEL_NAME = "gemma3:latest"
# MODEL_NAME = "llama3:latest"

OLLAMA_URL = "http://10.91.136.163:11434"

load_dotenv()

# section - PUBLIC VARIABLES

# section - HELPERS


# section - SESSION

class TextSession:
    def __init__(self):
        self.llm = LangchainLLM(session=self)
        self.accept_llm_text_delta = False

    def handle_text_message_sync(self, text_input: str):
        self.llm.handle_message_sync(text_input)

    async def handle_text_message_async(self, text_input: str):
        await self.llm.handle_message_async(text_input)

    async def handle_llm_text_delta(self, delta: str):
        if delta == "" or not self.accept_llm_text_delta:
            # * if "" but not final response, ignore
            return
        print(delta, end="", flush=True if delta != "" else False)

    async def handle_final_llm_response(self):
        if not self.accept_llm_text_delta:
            return
        print("")
        self.accept_llm_text_delta = False

    async def interrupt(self):
        await self.llm.interrupt()

    async def start_background_tasks(self):
        self.llm.start_background_tasks()

    async def cleanup(self):
        await self.llm.cleanup()

class TextSessionWS(TextSession):
    def __init__(self, ws: WebSocket):
        self.ws = ws
        self.llm = LangchainLLM(session=self)

        self.accept_llm_text_delta = False

    def handle_text_message_sync(self, text_input: str):
        self.llm.handle_message_sync(text_input)

    async def handle_text_message_async(self, text_input: str):
        await self.llm.handle_message_async(text_input)


    async def handle_llm_text_delta(self, delta: str):
        if delta == "" or not self.accept_llm_text_delta:
            # * if "" but not final response, ignore
            return
        await self.ws.send_json({"type": "text_delta", "data": delta})
        print(delta, end="", flush=True if delta != "" else False)

    async def handle_final_llm_response(self):
        if not self.accept_llm_text_delta:
            return
        await self.ws.send_json({"type": "text_final"})
        print("")
        self.accept_llm_text_delta = False

    async def interrupt(self):
        await self.ws.send_json({"type": "interrupt"})
        await self.llm.interrupt()

    async def start_background_tasks(self):
        self.llm.start_background_tasks()

    async def cleanup(self):
        await self.llm.cleanup()

# section - LLM

class LangchainLLM():
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
            self.session.accept_llm_text_delta = True
            self.interrupted = False
            self.interruptable = True
            pm.inf("generating llm response for:\n" + message)
            
            
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
    pm.ins(f"Invoking Ollama LLM with prompt: {prompt}")
    return {"response": OllamaLLM(model=MODEL_NAME, base_url=OLLAMA_URL).invoke(prompt)}

@app.get("/invoke-llm/rag/qa")
async def endpoint_invoke_llm_rag(prompt: str):    
    pm.ins(f"Invoking Ollama LLM RAG chain with prompt: {prompt}")
    # * Load vector store
    vsm = VectorStoreManager(
        ollama_model_name=MODEL_NAME,
    )
    vectorstore = vsm.load_vectorstore()
    if not vectorstore:
        pdf_processor = PDFProcessor()
        chunks = pdf_processor.process_pdfs()
        vectorstore = vsm.create_vectorstore(chunks)
            
    # * Create RAG chain
    rag_chain = RAGChain(
        retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
        ollama_model_name=MODEL_NAME,
        ollama_base_url=OLLAMA_URL,
        temperature=0.7,
    )
    
    # * Query RAG chain
    result = rag_chain.query(question=prompt, chain_type="qa")
    
    return {
        "answer": result["answer"],
        "source_documents": [
            {
                "page_content": doc.page_content,
                "metadata": doc.metadata
            } for doc in result["source_documents"]
        ]
    }
    
@app.get("/invoke-llm/rag/conversational")
async def endpoint_invoke_llm_rag_conversational():
    pass

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
    uvicorn.run("main:app", host="0.0.0.0", port=2580, reload=True)

if __name__ == "__main__":
    main()
    