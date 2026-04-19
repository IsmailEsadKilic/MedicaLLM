# Streaming Implementation Guide

This document explains the real-time streaming implementation in MedicaLLM using LangChain, LangGraph, FastAPI, and React.

## Overview

MedicaLLM implements **token-by-token streaming** to provide a responsive, ChatGPT-like user experience. Instead of waiting for the complete response, users see:
- Real-time thinking steps (e.g., "Searching medical documents...")
- Token-by-token text generation as the LLM produces output
- Tool usage indicators
- Final sources and metadata

## Architecture

### Backend Stack
- **LangChain/LangGraph**: Agent framework with streaming support
- **FastAPI**: Web framework with Server-Sent Events (SSE)
- **Digital Ocean AI**: LLM provider (OpenAI-compatible API)

### Frontend Stack
- **React**: UI framework
- **Fetch API**: Native browser streaming with ReadableStream
- **Server-Sent Events (SSE)**: Unidirectional server-to-client streaming

## Backend Implementation

### 1. Enable Streaming in the LLM

**File**: `backend/src/agent/agent.py`

```python
model = ChatOpenAI(
    model=do_ai_model,
    api_key=model_access_key,
    base_url="https://inference.do-ai.run/v1",
    temperature=temperature,
    max_tokens=2048,
    streaming=True,  # ✅ CRITICAL: Enable streaming
)
```

**Why it matters**: Without `streaming=True`, the LLM will buffer the entire response before returning it, defeating the purpose of streaming.

### 2. Use `astream_events()` for Token-Level Streaming

**File**: `backend/src/agent/session.py`

LangGraph provides multiple streaming modes:
- `astream()`: Streams full node outputs after each node completes
- `astream_events()`: Streams token-level events from inside nodes ✅ **Best for real-time UX**
- `astream_log()`: Streams full execution logs (debugging)

```python
async for event in self.agent.astream_events(
    {"messages": message_history},
    version="v2",  # Required for LangGraph 0.2+
    config={"recursion_limit": 50},
):
    event_type = event.get("event")
    
    # Stream individual tokens from the LLM
    if event_type == "on_chat_model_stream":
        chunk = event.get("data", {}).get("chunk")
        if chunk and hasattr(chunk, "content"):
            token = chunk.content
            if token:
                yield {"type": "content", "content": token}
```

**Key Events**:
- `on_chat_model_start`: LLM invocation begins
- `on_chat_model_stream`: Individual token arrives ✅
- `on_tool_start`: Tool execution begins
- `on_tool_end`: Tool execution completes

### 3. FastAPI SSE Endpoint

**File**: `backend/src/agent/router.py`

```python
@router.post("/query-stream")
async def endpoint_query_stream(request: Request, body: QueryRequest):
    async def generate_stream():
        session = _get_or_create_session(body.conversation_id, agent)
        async for chunk in session.stream_query(body.query):
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # ✅ CRITICAL for Nginx
        },
    )
```

**Critical Headers**:
- `X-Accel-Buffering: no`: Disables Nginx buffering (most cloud platforms use Nginx). Without this, the entire response is buffered before being sent to the client.
- `Cache-Control: no-cache`: Prevents caching of streaming responses
- `Connection: keep-alive`: Keeps the connection open for streaming

### 4. SSE Message Format

Each SSE message follows this format:
```
data: {"type": "thinking", "step": "Searching medical documents...", "tool": "search_medical_documents"}

data: {"type": "content", "content": "Based"}

data: {"type": "content", "content": " on"}

data: {"type": "done", "sources": [...], "tool_used": "search_medical_documents"}

```

**Message Types**:
- `thinking`: Tool execution status (e.g., "Searching PubMed...")
- `content`: Individual token or text chunk
- `done`: Stream complete with metadata (sources, tool info)
- `error`: Error occurred during streaming

## Frontend Implementation

### 1. Fetch API with ReadableStream

**File**: `frontend/src/pages/Chat.jsx`

```javascript
const response = await fetch(`${config.API_URL}/api/drugs/query-stream`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    query: query,
    conversation_id: chatId,
    patient_id: selectedPatient?.id,
    account_type: user?.account_type,
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = '';
let accumulatedContent = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  buffer += decoder.decode(value, { stream: true });
  const events = buffer.split('\n\n');
  buffer = events.pop() || '';

  for (const event of events) {
    for (const line of event.split('\n')) {
      if (!line.startsWith('data: ')) continue;
      
      const chunk = JSON.parse(line.slice(6));
      
      if (chunk.type === 'content') {
        accumulatedContent += chunk.content;
        setStreamingContent(accumulatedContent);
      }
    }
  }
}
```

**Key Points**:
- `{ stream: true }` in `TextDecoder.decode()`: Handles multi-byte UTF-8 characters split across chunks
- Buffer management: SSE messages may arrive in partial chunks, so we maintain a buffer
- `reader.releaseLock()`: Always release the reader in a `finally` block

### 2. React State Management

```javascript
const [streamingContent, setStreamingContent] = useState('');
const [isStreaming, setIsStreaming] = useState(false);
const [thinkingStep, setThinkingStep] = useState('');
```

**Rendering**:
```jsx
{isStreaming && streamingContent && (
  <div className="message assistant">
    <div className="message-inner">
      <div className="avatar">AI</div>
      <div className="content">
        <ReactMarkdown>{streamingContent}</ReactMarkdown>
        <span className="streaming-cursor" />
      </div>
    </div>
  </div>
)}
```

## Testing

### Backend Test (curl)

```bash
curl -X POST http://localhost:8000/api/drugs/query-stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{"query": "Tell me about Aspirin", "conversation_id": "test-123"}' \
  --no-buffer
```

**Expected Output**: Tokens should appear one by one, not all at once.

### Frontend Test

1. Start the backend: `cd backend && python run.py`
2. Start the frontend: `cd frontend && npm run dev`
3. Open the chat interface
4. Send a message
5. Observe:
   - Thinking steps appear (e.g., "Searching medical documents...")
   - Text streams token-by-token
   - Cursor blinks during streaming
   - Sources appear after completion

## Common Issues

### Issue 1: All Tokens Arrive at Once

**Symptoms**: No real-time streaming, entire response appears after a delay

**Causes**:
1. `streaming=True` not set on the LLM
2. Nginx buffering enabled (missing `X-Accel-Buffering: no`)
3. Using `astream()` instead of `astream_events()`

**Fix**:
```python
# ✅ Correct
model = ChatOpenAI(..., streaming=True)
async for event in agent.astream_events(..., version="v2"):
    ...

# ❌ Wrong
model = ChatOpenAI(..., streaming=False)
async for chunk in agent.astream(...):
    ...
```

### Issue 2: Connection Drops Mid-Stream

**Symptoms**: Streaming stops before completion, no error message

**Causes**:
1. Timeout on reverse proxy (Nginx, CloudFlare)
2. Network interruption
3. Backend exception not caught

**Fix**:
- Increase proxy timeout: `proxy_read_timeout 300s;` (Nginx)
- Add error handling in frontend:
```javascript
try {
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    // ... process chunk
  }
} catch (error) {
  console.error('Stream interrupted:', error);
  // Show error to user
} finally {
  reader.releaseLock();
}
```

### Issue 3: Malformed JSON in SSE

**Symptoms**: `JSON.parse()` errors in browser console

**Causes**:
1. SSE message split across multiple chunks
2. Invalid JSON in backend response

**Fix**:
- Use buffer to accumulate partial messages:
```javascript
buffer += decoder.decode(value, { stream: true });
const events = buffer.split('\n\n');
buffer = events.pop() || '';  // Keep incomplete message in buffer
```

## Performance Considerations

### Backend
- **Token Buffering**: LangChain may buffer tokens internally. Use `streaming=True` to minimize this.
- **Async Generators**: Use `async for` to avoid blocking the event loop
- **Connection Pooling**: FastAPI handles this automatically

### Frontend
- **React Re-renders**: Use `React.memo()` for message components to avoid re-rendering all messages on each token
- **Debouncing**: Consider debouncing state updates if streaming is too fast (rare with LLMs)

## References

- [LangChain Streaming Documentation](https://python.langchain.com/docs/how_to/streaming/)
- [LangGraph Streaming Modes](https://langchain-ai.github.io/langgraph/concepts/streaming/)
- [FastAPI Server-Sent Events](https://fastapi.tiangolo.com/tutorial/server-sent-events/)
- [MDN: Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)
- [Digital Ocean AI Documentation](https://docs.digitalocean.com/products/ai/)

## Summary

✅ **Backend**: Use `astream_events()` with `streaming=True` on the LLM
✅ **FastAPI**: Return `StreamingResponse` with proper SSE headers
✅ **Frontend**: Use Fetch API with `ReadableStream` and buffer management
✅ **Testing**: Verify token-by-token streaming with curl before frontend integration

The implementation provides a responsive, real-time user experience that matches modern AI chat interfaces like ChatGPT.
