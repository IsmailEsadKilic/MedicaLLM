# Streaming Setup Guide

This guide walks you through setting up and verifying the streaming implementation in MedicaLLM.

## Quick Start

### Backend Setup

1. **Ensure streaming is enabled in the LLM configuration**:

```python
# backend/src/agent/agent.py
model = ChatOpenAI(
    model=settings.do_ai_model,
    api_key=settings.model_access_key,
    base_url="https://inference.do-ai.run/v1",
    temperature=0.3,
    max_tokens=2048,
    streaming=True,  # ✅ Must be True
)
```

2. **Start the backend**:

```bash
cd backend
python run.py
```

The backend should start on `http://localhost:8000`

### Frontend Setup

1. **Install dependencies**:

```bash
cd frontend
npm install
```

2. **Start the development server**:

```bash
npm run dev
```

The frontend should start on `http://localhost:5173`

## Verification

### Method 1: Browser Test

1. Open `http://localhost:5173` in your browser
2. Log in to the application
3. Send a message in the chat interface
4. Observe:
   - ✅ Thinking steps appear (e.g., "Searching medical documents...")
   - ✅ Text appears token-by-token (not all at once)
   - ✅ Cursor blinks during streaming
   - ✅ Sources appear after completion

### Method 2: curl Test

Test the streaming endpoint directly:

```bash
# Get a JWT token first by logging in
TOKEN="your-jwt-token-here"

# Test streaming endpoint
curl -X POST http://localhost:8000/api/drugs/query-stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "query": "Tell me about Aspirin",
    "conversation_id": "test-123"
  }' \
  --no-buffer
```

**Expected Output**:
```
data: {"type":"thinking","step":"Looking up drug information...","tool":"get_drug_info"}

data: {"type":"thinking","step":"Generating response...","tool":null}

data: {"type":"content","content":"Asp"}

data: {"type":"content","content":"irin"}

data: {"type":"content","content":" is"}

...

data: {"type":"done","sources":[],"tool_used":"get_drug_info"}
```

### Method 3: Python Test Script

```bash
cd backend
python test_streaming.py
```

This runs basic streaming tests without requiring authentication.

## Troubleshooting

### Problem: All text appears at once (no streaming)

**Diagnosis**:
```bash
# Check if streaming is enabled
grep "streaming=True" backend/src/agent/agent.py
```

**Solution**:
1. Ensure `streaming=True` in `ChatOpenAI` initialization
2. Verify you're using `astream_events()` not `astream()`
3. Check for Nginx buffering (see below)

### Problem: Connection drops mid-stream

**Diagnosis**:
- Check browser console for errors
- Check backend logs for exceptions

**Solution**:
1. Increase timeout in reverse proxy (if using one)
2. Add error handling in frontend
3. Check network stability

### Problem: Nginx buffering (production)

If deploying behind Nginx, add this to your config:

```nginx
location /api/drugs/query-stream {
    proxy_pass http://backend:8000;
    proxy_buffering off;
    proxy_cache off;
    proxy_read_timeout 300s;
    proxy_connect_timeout 75s;
    
    # Critical for SSE
    proxy_set_header Connection '';
    proxy_http_version 1.1;
    chunked_transfer_encoding off;
}
```

### Problem: CORS errors in browser

**Solution**:
Add CORS middleware in FastAPI:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Performance Tuning

### Backend

1. **Adjust token buffer size** (if needed):
```python
model = ChatOpenAI(
    ...,
    streaming=True,
    streaming_options={"chunk_size": 1}  # Stream every token
)
```

2. **Monitor memory usage**:
```bash
# Check memory usage during streaming
docker stats medicallm-backend
```

### Frontend

1. **Optimize React re-renders**:
```javascript
// Memoize message components
const Message = React.memo(({ message }) => {
  return <div>{message.content}</div>;
});
```

2. **Debounce state updates** (if streaming is too fast):
```javascript
import { debounce } from 'lodash';

const updateContent = debounce((content) => {
  setStreamingContent(content);
}, 50);
```

## Monitoring

### Backend Metrics

Monitor these metrics in production:

1. **Stream duration**: Time from first token to last token
2. **Token rate**: Tokens per second
3. **Error rate**: Failed streams / total streams
4. **Connection drops**: Streams interrupted before completion

### Frontend Metrics

1. **Time to first token**: User sends message → first token appears
2. **Perceived latency**: User experience of responsiveness
3. **Error rate**: Failed stream connections

## Advanced Configuration

### Custom Thinking Steps

Add custom thinking steps for new tools:

```python
# backend/src/agent/session.py
_TOOL_STEPS = {
    "your_custom_tool": [
        "Step 1: Initializing...",
        "Step 2: Processing...",
        "Step 3: Finalizing..."
    ],
}
```

### Custom SSE Message Types

Add new message types:

```python
# Backend
yield {"type": "custom", "data": "your data"}

# Frontend
if (chunk.type === 'custom') {
  handleCustomMessage(chunk.data);
}
```

## Production Checklist

Before deploying to production:

- [ ] `streaming=True` enabled in LLM config
- [ ] `X-Accel-Buffering: no` header set
- [ ] Error handling in place (backend and frontend)
- [ ] Timeout configured in reverse proxy
- [ ] CORS configured correctly
- [ ] Monitoring/logging in place
- [ ] Load testing completed
- [ ] Fallback to non-streaming if needed

## Resources

- [Main Streaming Documentation](../STREAMING.md)
- [LangChain Streaming Docs](https://python.langchain.com/docs/how_to/streaming/)
- [FastAPI SSE Tutorial](https://fastapi.tiangolo.com/tutorial/server-sent-events/)
- [MDN: Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events)

## Support

If you encounter issues:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review backend logs: `docker logs medicallm-backend`
3. Check browser console for frontend errors
4. Test with curl to isolate backend vs frontend issues

## Summary

✅ Streaming provides real-time, responsive user experience
✅ Requires `streaming=True` on LLM and proper SSE headers
✅ Use `astream_events()` for token-level streaming
✅ Test with curl before frontend integration
✅ Monitor performance and error rates in production
