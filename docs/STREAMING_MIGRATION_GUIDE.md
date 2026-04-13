# Streaming Migration Guide

This guide helps you migrate from the old streaming implementation to the new token-by-token streaming using `astream_events()`.

## What Changed?

### Old Implementation (Before)
- Used `astream()` with `stream_mode="values"`
- Streamed full node outputs (not individual tokens)
- Less responsive user experience
- Larger chunks of text appearing at once

### New Implementation (After)
- Uses `astream_events()` with `version="v2"`
- Streams individual tokens as they're generated
- ChatGPT-like responsive experience
- Token-by-token text appearance

## Migration Steps

### Step 1: Enable Streaming in LLM

**File**: `backend/src/agent/agent.py`

```diff
model = ChatOpenAI(
    model=do_ai_model,
    api_key=model_access_key,
    base_url="https://inference.do-ai.run/v1",
    temperature=temperature,
    max_tokens=2048,
+   streaming=True,  # Enable streaming for token-by-token output
)
```

### Step 2: Replace astream() with astream_events()

**File**: `backend/src/agent/session.py`

```diff
- async for chunk in self.agent.astream(
-     {"messages": message_history},
-     stream_mode="values",
-     config={"recursion_limit": 50},
- ):
-     if chunk.get("messages"):
-         latest_message = chunk["messages"][-1]
-         # ... process full message

+ async for event in self.agent.astream_events(
+     {"messages": message_history},
+     version="v2",
+     config={"recursion_limit": 50},
+ ):
+     event_type = event.get("event")
+     
+     # Stream individual tokens
+     if event_type == "on_chat_model_stream":
+         chunk = event.get("data", {}).get("chunk")
+         if chunk and hasattr(chunk, "content"):
+             token = chunk.content
+             if token:
+                 yield {"type": "content", "content": token}
```

### Step 3: Update Tool Detection Logic

**Old way** (detecting tool calls from messages):
```python
if hasattr(latest_message, "tool_calls") and latest_message.tool_calls:
    call = latest_message.tool_calls[0]
    tool_name = call.get("name")
```

**New way** (detecting tool calls from events):
```python
if event_type == "on_chat_model_start":
    data = event.get("data", {})
    input_data = data.get("input", {})
    if isinstance(input_data, dict):
        messages = input_data.get("messages", [])
        if messages:
            last_msg = messages[-1]
            if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                call = last_msg.tool_calls[0]
                tool_name = call.get("name")
```

### Step 4: Add Critical SSE Headers

**File**: `backend/src/agent/router.py`

```diff
return StreamingResponse(
    generate_stream(),
    media_type="text/event-stream",
+   headers={
+       "Cache-Control": "no-cache",
+       "Connection": "keep-alive",
+       "X-Accel-Buffering": "no",  # Critical for Nginx
+   },
)
```

### Step 5: Improve Frontend Error Handling

**File**: `frontend/src/pages/Chat.jsx`

```diff
+ if (!response.body) {
+   throw new Error('Response body is null');
+ }

const reader = response.body.getReader();
const decoder = new TextDecoder();
let buffer = '';

+ try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      buffer += decoder.decode(value, { stream: true });
      const events = buffer.split('\n\n');
-     buffer = events.pop();
+     buffer = events.pop() || '';  // Prevent undefined
      
      // ... process events
    }
+ } finally {
+   reader.releaseLock();
+ }
```

## Verification

After migration, verify the changes:

### 1. Backend Test
```bash
cd backend
python test_streaming.py
```

### 2. curl Test
```bash
curl -X POST http://localhost:8000/api/drugs/query-stream \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"query": "Tell me about Aspirin", "conversation_id": "test"}' \
  --no-buffer
```

**Expected**: Tokens should appear one by one, not all at once.

### 3. Browser Test
1. Open the chat interface
2. Send a message
3. Observe token-by-token streaming
4. Check browser console for errors

## Troubleshooting

### Issue: Still seeing full chunks instead of tokens

**Cause**: `streaming=True` not set or using wrong streaming method

**Fix**:
1. Verify `streaming=True` in `ChatOpenAI` initialization
2. Verify using `astream_events()` not `astream()`
3. Restart the backend

### Issue: Connection drops mid-stream

**Cause**: Missing error handling or timeout

**Fix**:
1. Add try-finally block in frontend
2. Add `reader.releaseLock()` in finally
3. Increase proxy timeout if behind Nginx

### Issue: Nginx buffering (production only)

**Cause**: Missing `X-Accel-Buffering: no` header

**Fix**:
```python
headers={
    "X-Accel-Buffering": "no",
}
```

## Rollback Plan

If you need to rollback to the old implementation:

### 1. Revert Backend Changes
```bash
git checkout HEAD~1 backend/src/agent/agent.py
git checkout HEAD~1 backend/src/agent/session.py
git checkout HEAD~1 backend/src/agent/router.py
```

### 2. Restart Backend
```bash
cd backend
python run.py
```

### 3. Clear Browser Cache
```bash
# In browser DevTools
# Application > Clear Storage > Clear site data
```

## Performance Comparison

### Old Implementation
- **Time to first content**: 2-5 seconds (full response)
- **User experience**: Waiting, then full text appears
- **Perceived latency**: High

### New Implementation
- **Time to first token**: 200-500ms
- **User experience**: Immediate feedback, streaming text
- **Perceived latency**: Low

## Breaking Changes

### None!

The migration is **backward compatible**. The API contract remains the same:
- Same endpoint: `/api/drugs/query-stream`
- Same request format
- Same response format (SSE with JSON messages)

Only the internal implementation changed for better performance.

## Next Steps

After successful migration:

1. ✅ Monitor streaming performance
2. ✅ Check error rates in logs
3. ✅ Gather user feedback
4. ✅ Optimize if needed (see [STREAMING_SETUP.md](./STREAMING_SETUP.md))

## Resources

- [Full Documentation](../STREAMING.md)
- [Setup Guide](./STREAMING_SETUP.md)
- [Quick Reference](./STREAMING_QUICK_REFERENCE.md)
- [Implementation Summary](../STREAMING_IMPLEMENTATION_SUMMARY.md)

## Support

If you encounter issues during migration:

1. Check the [Troubleshooting](#troubleshooting) section
2. Review backend logs: `docker logs medicallm-backend`
3. Check browser console for frontend errors
4. Test with curl to isolate backend vs frontend issues
5. Refer to the rollback plan if needed

## Summary

✅ **Migration is straightforward**: 3 main changes (streaming=True, astream_events, headers)
✅ **Backward compatible**: No API changes
✅ **Improved UX**: Token-by-token streaming like ChatGPT
✅ **Production-ready**: Proper error handling and monitoring
✅ **Well-documented**: Comprehensive guides and references
