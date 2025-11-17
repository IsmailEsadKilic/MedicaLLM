from __future__ import annotations
from typing import Any
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import printmeup as pm

from langchain.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.prompts.chat import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    SystemMessagePromptTemplate,
)
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent


from dotenv import load_dotenv
load_dotenv()

# section - CONSTANTS


DEFAULT_USER_GREETING = "Merhaba"

# TODO
# MODEL_ID = "google/gemma-3-4b-it" # * >8gb
MODEL_ID = "google/gemma-3-1b-it" # * ~4gb
# MODEL_ID = "google/medgemma-4b-pt" # * >8gb

# section - HELPERS


# section - SESSION

class TextSession():
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
            
            self.messages.append(HumanMessage(content=message))
            
            response = self.agent.astream(
                [self.messages]
            )
            async for chunk in response:
                if self.interrupted:
                    pm.inf("LLM response generation interrupted")
                    break
                pm.ins(chunk)
                o += str(chunk.content)
            
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
    session = TextSession(
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


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("static/favicon.ico")


@app.get("/health")
async def endpoint_health():
    return {"status": "ok"}

# section - MAIN

def main():
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

if __name__ == "__main__":
    main()
    