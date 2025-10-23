from __future__ import annotations
from typing import Any
from fastapi.responses import FileResponse, HTMLResponse
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import asyncio
import printmeup as pm

# section - CONSTANTS

DEFAULT_USER_GREETING = "Merhaba"

# section - HELPERS



# def get_vllm_client() -> AsyncOpenAI:
#     return AsyncOpenAI(
#         api_key="EMPTY",
#         base_url="http://localhost:8000/v1",
#     )


# def get_vllm_model() -> OpenAIChatCompletionsModel:
#     return OpenAIChatCompletionsModel(
#         # FIXME hardcoded for testing
#         model="google/gemma-3-27b-it",
#         # model="zai-org/GLM-4.6",
#         openai_client=get_vllm_client(),
#     )


# async def get_vllm_loaded_model_id() -> str:
#     client = get_vllm_client()
#     models = await client.models.list()
#     return models.data[0].id


# async def get_loaded_vllm_model() -> OpenAIChatCompletionsModel:
#     return OpenAIChatCompletionsModel(
#         model=await get_vllm_loaded_model_id(),
#         openai_client=get_vllm_client(),
    )

# section - SESSION

class TextSession():
    def __init__(self, ws: WebSocket):
        self.ws = ws
        self.llm = VllmLlm(session=self)

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

class VllmLlm():
    def __init__(self, session: TextSession):
        self.session = session
        self.interruptable = False
        self.interrupted = False
        
        self.new_message_queue: asyncio.Queue[str] = asyncio.Queue()
        self.process_message_queue_task: asyncio.Task | None = None
        
        self.llm_task: asyncio.Task | None = None

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
        await self.new_message_queue.put(message)

    async def process_message_queue_taskfunc(self):
        """
        Process messages from the queue and send to Ollama LLM.
        """
        try:
            while True:
                message = await self.new_message_queue.get()
                try:
                    await self.session.interrupt()  # * this is actually the earliest point we can interrupt
                    # * the previous in voice session, because we have to await
                    self.llm_task = asyncio.create_task(self.llm_taskfunc(message))
                finally:
                    self.new_message_queue.task_done()
        except asyncio.CancelledError:
            pm.inf("VLLM LLM message processor cancelled")
        except Exception as e:
            pm.err(
                e=e,
                a="VLLM LLM message processor",
            )
            raise e
        finally:
            if self.llm_task:
                await self.llm_task
            self.process_message_queue_task = None
        
    async def llm_taskfunc(self, message: str):
        try:
            self.session.accept_llm_text_delta = True
            self.interrupted = False
            self.interruptable = True
            pm.inf("generating llm response for:\n" + message)
            
            
            
            
        except asyncio.CancelledError:
            pm.inf("VLLM LLM task cancelled")
        except Exception as e:
            pm.err(e=e, m="Error in VLLM LLM task", a="VLLM LLM task")
        finally:
            
            
            
            pm.inf("handling final llm response")
            await self.session.handle_final_llm_response()
            self.interruptable = False
            self.llm_task = None

    
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
            pm.err(e=e, m="Error during LLM cleanup", a="LLM cleanup")
            raise e



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
            if data.get("type") == "disconnect":
                reason = data.get("data", "No reason provided")
                pm.inf(f"Client requested disconnect: {reason}")
                break
    except WebSocketDisconnect:
        pm.inf(
            f"WebSocket connection from {websocket.client} disconnected @/text-session"
        )
    except Exception as e:
        pm.err(
            e=e,
            m="Error in WebSocket connection",
            a="/text-session",
        )
        raise e
    finally:
        try:
            await session.cleanup()
            pm.inf(f"Cleaned up session for {websocket.client} @/console-session")
        except Exception as e:
            pm.err(
                e=e,
                m=f"Error cleaning up session for {websocket.client}",
                a="/console-session",
            )
            raise e

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
    