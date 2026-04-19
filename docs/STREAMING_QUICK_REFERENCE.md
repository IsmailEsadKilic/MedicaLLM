# Streaming Quick Reference

## Backend (Python/FastAPI)

### Enable Streaming in LLM
```python
model = ChatOpenAI(
    model="gpt-4o-mini",
    streaming=True,  # ✅ Required
    temperature=0.3,
)
```

### Stream with astream_events()
```python
async for event in agent.astream_events(
    {"messages": message_history},
    version="v2",  # Required for LangGraph 0.2+
):
    if event["event"] == "on_chat_model_stream":
        token = event["data"]["chunk"].content
        yield {"type": "content", "content": token}
```

### FastAPI SSE Endpoint
```python
@router.post("/stream")
async def stream_endpoint():
    async def generate():
        async for chunk in stream_data():
            yield f"data: {json.dumps(chunk)}\n\n"
    
    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # ✅ Critical for Nginx
        },
    )
```

## Frontend (React/JavaScript)

### Fetch with ReadableStream
```javascript
const response = await fetch('/api/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ query: 'Hello' })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  
  buffer += decoder.decode(value, { stream: true });
  const events = buffer.split('\n\n');
  buffer = events.pop() || '';
  
  for (const event of events) {
    for (const line of event.split('\n')) {
      if (line.startsWith('data: ')) {
        const chunk = JSON.parse(line.slice(6));
        handleChunk(chunk);
      }
    }
  }
}
```

### React State
```javascript
const [content, setContent] = useState('');
const [isStreaming, setIsStreaming] = useState(false);

// Update on each token
if (chunk.type === 'content') {
  setContent(prev => prev + chunk.content);
}
```

## SSE Message Format

### Thinking Step
```json
data: {"type": "thinking", "step": "Searching...", "tool": "search"}
```

### Content Token
```json
data: {"type": "content", "content": "Hello"}
```

### Stream Complete
```json
data: {"type": "done", "sources": [], "tool_used": "search"}
```

### Error
```json
data: {"type": "error", "error": "Connection failed"}
```

## Testing

### curl Test
```bash
curl -X POST http://localhost:8000/api/stream \
  -H "Content-Type: application/json" \
  -d '{"query": "test"}' \
  --no-buffer
```

### Browser Test
```javascript
const eventSource = new EventSource('/api/stream');
eventSource.onmessage = (event) => {
  console.log(JSON.parse(event.data));
};
```

## Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| All tokens at once | `streaming=False` | Set `streaming=True` |
| Buffered response | Nginx buffering | Add `X-Accel-Buffering: no` |
| Connection drops | Timeout | Increase proxy timeout |
| Malformed JSON | Split messages | Use buffer for partial messages |

## Event Types (astream_events)

| Event | When | Use For |
|-------|------|---------|
| `on_chat_model_start` | LLM starts | Show "thinking" indicator |
| `on_chat_model_stream` | Token arrives | Stream text to UI |
| `on_chat_model_end` | LLM completes | Hide "thinking" indicator |
| `on_tool_start` | Tool starts | Show tool name |
| `on_tool_end` | Tool completes | Show tool result |

## Best Practices

✅ **DO**:
- Use `astream_events()` for token-level streaming
- Set `streaming=True` on the LLM
- Add `X-Accel-Buffering: no` header
- Handle errors gracefully
- Release reader in `finally` block
- Use buffer for partial SSE messages

❌ **DON'T**:
- Use `astream()` for token streaming (use `astream_events()`)
- Forget `version="v2"` parameter
- Block the event loop with sync code
- Parse JSON without try-catch
- Forget to handle connection drops

## Performance Tips

1. **Backend**: Use async generators, avoid blocking
2. **Frontend**: Memoize components, debounce if needed
3. **Network**: Use HTTP/2, enable compression
4. **Monitoring**: Track time-to-first-token, error rate

## Resources

- [Full Documentation](../STREAMING.md)
- [Setup Guide](./STREAMING_SETUP.md)
- [LangChain Docs](https://python.langchain.com/docs/how_to/streaming/)
- [FastAPI SSE](https://fastapi.tiangolo.com/tutorial/server-sent-events/)
