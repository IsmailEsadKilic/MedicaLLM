# Debugging Logs Added

## Summary
Added comprehensive logging throughout the backend to help diagnose routing and request issues.

## Bugs Fixed

### 1. Conversations Service Bug ✅
**File:** `backend/src/conversations/service.py`
**Issue:** `_record_to_conversation` was using `id=rec.conversation_id` instead of `conversation_id=rec.conversation_id`
**Impact:** This caused 500 errors when loading conversations because the Conversation model expects `conversation_id` field
**Fix:** Changed `id=` to `conversation_id=`

## Logging Added

### 1. Main Application (`backend/src/main.py`)

#### Startup Logging
- Application startup banner
- Medical agent initialization status
- Periodic tasks startup confirmation
- Shutdown logging

#### Router Registration Logging
- Logs each router as it's registered with its prefix
- Example output:
  ```
  ================================================================================
  REGISTERING ROUTERS
  ================================================================================
  Auth router prefix: /api/auth
  Conversations router prefix: /api/conversations
  Drugs router prefix: /api/drugs
  Session router prefix: /api/session
  Users router prefix: /api/users
  Admin router prefix: /api/admin
  ================================================================================
  ALL ROUTERS REGISTERED
  ================================================================================
  ```

#### Route Listing
- Lists all registered routes with their HTTP methods and paths
- Example output:
  ```
  Registered routes:
    GET        /
    GET        /health
    POST       /api/auth/login
    POST       /api/auth/send-code
    GET        /api/conversations/
    POST       /api/conversations/
    POST       /api/session/query
    POST       /api/session/generate-title
    GET        /api/drugs/search/{query}
    ...
  ```

#### Request/Response Middleware
- Logs every incoming request with method and path
- Logs response status code
- Logs errors with full stack trace
- Example output:
  ```
  [REQUEST] POST /api/session/query
  [RESPONSE] POST /api/session/query - Status: 200
  ```

### 2. Session Router (`backend/src/session/router.py`)

#### Query Endpoint
- Logs when query is received with user ID and conversation ID
- Logs when patient context is loaded
- Logs query preview (first 50 chars)
- Logs query processing status
- Example output:
  ```
  [SESSION QUERY] Received query from user abc123 for conversation xyz789
  [SESSION QUERY] Loading patient patient_456 for context
  [SESSION QUERY] Processing query: What are the side effects of aspirin?...
  ```

#### Generate Title Endpoint
- Logs title generation requests
- Logs session lookup status
- Logs authorization checks
- Logs generated title
- Example output:
  ```
  [GENERATE TITLE] Request for conversation xyz789 from user abc123
  [GENERATE TITLE] Generating title for conversation xyz789
  [GENERATE TITLE] Generated title: Aspirin Side Effects
  ```

### 3. Conversations Router (`backend/src/conversations/router.py`)

#### Get Conversations Endpoint
- Logs user ID requesting conversations
- Logs number of conversations found
- Logs errors with full stack trace
- Example output:
  ```
  [CONVERSATIONS] GET / - Loading conversations for user abc123
  [CONVERSATIONS] Found 5 conversations for user abc123
  ```

## Log Levels Used

- **INFO**: Normal operations, request/response tracking
- **WARNING**: Authorization failures, missing resources
- **ERROR**: Exceptions, failures with stack traces

## How to Use These Logs

### 1. Check Backend Startup
Look for the startup banner and router registration:
```bash
tail -f backend/logs/medicallm.log | grep "REGISTERING ROUTERS" -A 20
```

### 2. Monitor Incoming Requests
```bash
tail -f backend/logs/medicallm.log | grep "\[REQUEST\]"
```

### 3. Track Specific Endpoints
```bash
# Session queries
tail -f backend/logs/medicallm.log | grep "\[SESSION QUERY\]"

# Conversations
tail -f backend/logs/medicallm.log | grep "\[CONVERSATIONS\]"

# Title generation
tail -f backend/logs/medicallm.log | grep "\[GENERATE TITLE\]"
```

### 4. Debug 404 Errors
Check if routes are registered:
```bash
grep "Registered routes:" backend/logs/medicallm.log -A 50
```

### 5. Debug 500 Errors
Look for ERROR level logs with stack traces:
```bash
grep "ERROR" backend/logs/medicallm.log
```

## Expected Log Output on Startup

```
2024-01-15 10:30:00 - INFO - ================================================================================
2024-01-15 10:30:00 - INFO - STARTING MEDICALLM BACKEND
2024-01-15 10:30:00 - INFO - ================================================================================
2024-01-15 10:30:01 - INFO - Medical agent initialized
2024-01-15 10:30:01 - INFO - Periodic tasks started
2024-01-15 10:30:01 - INFO - ================================================================================
2024-01-15 10:30:01 - INFO - REGISTERING ROUTERS
2024-01-15 10:30:01 - INFO - ================================================================================
2024-01-15 10:30:01 - INFO - Auth router prefix: /api/auth
2024-01-15 10:30:01 - INFO - Conversations router prefix: /api/conversations
2024-01-15 10:30:01 - INFO - Drugs router prefix: /api/drugs
2024-01-15 10:30:01 - INFO - Session router prefix: /api/session
2024-01-15 10:30:01 - INFO - Users router prefix: /api/users
2024-01-15 10:30:01 - INFO - Admin router prefix: /api/admin
2024-01-15 10:30:01 - INFO - ================================================================================
2024-01-15 10:30:01 - INFO - ALL ROUTERS REGISTERED
2024-01-15 10:30:01 - INFO - ================================================================================
2024-01-15 10:30:01 - INFO - Registered routes:
2024-01-15 10:30:01 - INFO -   GET        /
2024-01-15 10:30:01 - INFO -   GET        /health
2024-01-15 10:30:01 - INFO -   POST       /api/auth/login
2024-01-15 10:30:01 - INFO -   POST       /api/auth/send-code
2024-01-15 10:30:01 - INFO -   POST       /api/auth/verification-code
...
```

## Files Modified

1. `backend/src/main.py` - Added startup, router registration, route listing, and request/response logging
2. `backend/src/session/router.py` - Added query and title generation logging
3. `backend/src/conversations/router.py` - Added conversation loading logging
4. `backend/src/conversations/service.py` - **FIXED BUG**: Changed `id=` to `conversation_id=`

## Next Steps

1. **Restart the backend server** to apply all changes
2. **Check the logs** at `backend/logs/medicallm.log`
3. **Verify routes are registered** correctly
4. **Test the frontend** and watch the logs in real-time
5. **Report any 404s** with the log output showing what routes are registered

## Troubleshooting

### If you still get 404s:
1. Check if the route is in the "Registered routes" list
2. Check if the request path matches exactly (case-sensitive)
3. Check if the HTTP method matches (GET vs POST)
4. Look for `[REQUEST]` logs to see what the backend is receiving

### If you get 500 errors:
1. Look for ERROR logs with stack traces
2. Check the specific endpoint logs (e.g., `[CONVERSATIONS]`)
3. Check database connection
4. Check if required services are initialized

---

**Status: ✅ COMPLETE**

Comprehensive logging added throughout the backend. The conversations bug has been fixed. Restart the backend to see detailed logs.
