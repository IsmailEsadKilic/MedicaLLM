# Debug Logging Implementation Summary

## Overview
Comprehensive debug logging has been added throughout the entire MedicaLLM backend to provide detailed visibility into all operations, with special focus on agent querying and tool execution.

## Files Modified

### Core Configuration
1. **`backend/src/config.py`**
   - Changed default `log_level` from `"INFO"` to `"DEBUG"`

### Agent Components
2. **`backend/src/agent/tools.py`**
   - Added DEBUG logs to all 8 agent tools
   - Logs tool invocation, parameters, resolution steps, and results
   - Tags: `[TOOL]`

3. **`backend/src/agent/agent.py`**
   - Added initialization logging
   - Logs agent creation success/failure
   - Tags: `[AGENT INIT]`

4. **`backend/src/agent/langchain_agent.py`**
   - Added logger import (was missing)
   - Added detailed agent creation logging
   - Logs model configuration, tools, and settings
   - Tags: `[AGENT CREATE]`

### Session Management
5. **`backend/src/session/session.py`**
   - Added comprehensive query handling logs
   - Logs request ID, query details, message history
   - Logs agent invocation timing and results
   - Logs message saving and title generation
   - Tags: `[SESSION]`

6. **`backend/src/session/router.py`**
   - Added detailed endpoint logging with separators
   - Logs user info, conversation ID, patient context
   - Logs query processing duration and results
   - Added `import time` for timing measurements
   - Tags: `[SESSION QUERY]`, `[SESSION MANAGER]`

### Services
7. **`backend/src/drugs/service.py`**
   - Added database operation logging
   - Logs drug lookups, searches, and interaction checks
   - Logs query parameters and result counts
   - Tags: `[DRUG SERVICE]`

8. **`backend/src/pubmed/service.py`**
   - Added comprehensive API call logging
   - Logs esearch/efetch operations
   - Logs article parsing and confidence scoring
   - Tags: `[PUBMED]`

9. **`backend/src/conversations/service.py`**
   - Added message handling logs
   - Logs message additions and counts
   - Tags: `[CONVERSATION]`

10. **`backend/src/auth/service.py`**
    - Added authentication logging
    - Logs registration, login, and token verification
    - Tags: `[AUTH]`

## Log Structure

### Log Levels
- **DEBUG**: Detailed internal operations, variable values, step-by-step execution
- **INFO**: High-level summaries, successful operations, milestones
- **WARNING**: Non-critical issues, missing data, authorization failures
- **ERROR**: Critical failures with full stack traces

### Log Tags
Each component uses consistent tags for easy filtering:
- `[SESSION QUERY]` - HTTP endpoint operations
- `[SESSION]` - Session class operations
- `[SESSION MANAGER]` - Session manager operations
- `[TOOL]` - Agent tool executions
- `[DRUG SERVICE]` - Drug database operations
- `[PUBMED]` - PubMed API operations
- `[AGENT INIT]` - Agent initialization
- `[AGENT CREATE]` - Agent creation
- `[CONVERSATION]` - Conversation operations
- `[AUTH]` - Authentication operations

## Key Features

### 1. Complete Request Tracing
Every user query is logged from start to finish:
```
[SESSION QUERY] ========== NEW QUERY REQUEST ==========
[SESSION QUERY] User: user_123 (user@example.com)
[SESSION QUERY] Conversation: conv_456
[SESSION QUERY] Query: What is aspirin?
[SESSION] handle_user_query called for session sess_789
[SESSION] Request ID: abc123def456
[TOOL] get_drug_info called with drug_name='aspirin'
[DRUG SERVICE] get_drug called with drug_id: DB00945
[SESSION] Agent invocation completed in 1234.56ms
[SESSION QUERY] ========== QUERY COMPLETED SUCCESSFULLY ==========
```

### 2. Tool Execution Tracking
Every tool call is logged with parameters and results:
```
[TOOL] get_drug_info: drug_name='Aspirin', detail='moderate'
[TOOL] Resolving drug name 'Aspirin' to drug_id
[TOOL] Resolved 'Aspirin' to drug_id: DB00945
[TOOL] Fetching full drug information for DB00945
[TOOL] Building response for Aspirin with detail level: moderate
```

### 3. Performance Monitoring
Execution times are logged for all major operations:
```
[SESSION] Agent invocation completed in 1234.56ms
[PUBMED] Retrieved 5 articles (avg confidence: 78.5) in 2345.67ms
[SESSION QUERY] Query processed in 3456.78ms
```

### 4. Error Diagnosis
Comprehensive error logging with context:
```
[DRUG SERVICE] Error getting drug DB00945: Connection timeout
Traceback (most recent call last):
  File "...", line 123, in get_drug
    ...
```

## Usage Examples

### View all logs in real-time:
```bash
tail -f backend/logs/MedicaLLM.log
```

### Filter by component:
```bash
grep "\[SESSION QUERY\]" backend/logs/MedicaLLM.log
grep "\[TOOL\]" backend/logs/MedicaLLM.log
grep "\[PUBMED\]" backend/logs/MedicaLLM.log
```

### View only errors:
```bash
grep "ERROR" backend/logs/MedicaLLM.log
```

### Track a specific query:
```bash
grep "Request ID: abc123" backend/logs/MedicaLLM.log
```

## Benefits

1. **Complete Visibility**: Every operation logged with context
2. **Performance Tracking**: Timing data for optimization
3. **Debugging**: Detailed stack traces and variable states
4. **Audit Trail**: Complete record of all operations
5. **Tool Usage Analytics**: Track which tools are used and how often
6. **API Monitoring**: Track external API calls and performance
7. **Error Diagnosis**: Comprehensive error information

## Configuration

### Change log level via environment variable:
```bash
export LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR
```

### Or modify `backend/src/config.py`:
```python
log_level: str = "DEBUG"  # Change to INFO for production
```

## Production Recommendations

1. **Use INFO level in production** to reduce log volume
2. **Set up log rotation** to manage disk space
3. **Use DEBUG level** for troubleshooting specific issues
4. **Monitor log file size** and implement rotation policies
5. **Consider structured logging (JSON)** for easier parsing
6. **Integrate with monitoring tools** (ELK, Datadog, etc.)

## Testing

To test the logging:
1. Start the backend: `cd backend && python run.py`
2. Make a query through the frontend or API
3. View logs: `tail -f backend/logs/MedicaLLM.log`
4. You should see detailed logs for every step of the query processing

## Next Steps

1. Monitor logs during normal operation
2. Identify performance bottlenecks from timing data
3. Set up automated log analysis
4. Configure log rotation for production
5. Integrate with monitoring/alerting systems
