# Logging Setup Complete ✅

## Summary

Comprehensive debug logging has been successfully added to the MedicaLLM backend and is now configured to output to **both console and file**.

## Configuration Changes

### 1. Environment Variable (`.env`)
Changed:
```bash
LOG_LEVEL=DEBUG  # Was: INFO
```

### 2. Main Application (`backend/src/main.py`)
Updated logging configuration to include **both file and console handlers**:
- **File Handler**: Writes to `backend/logs/MedicaLLM.log`
- **Console Handler**: Writes to stdout (visible in terminal)

## How to Use

### Start the Backend
```bash
cd backend
python run.py
```

You will now see detailed logs in the console like:
```
2026-05-02 16:17:47 - INFO - [SESSION QUERY] ========== NEW QUERY REQUEST ==========
2026-05-02 16:17:47 - INFO - [SESSION QUERY] User: user_123 (user@example.com)
2026-05-02 16:17:47 - INFO - [SESSION QUERY] Query: Do Warfarin and Ibuprofen interact?...
2026-05-02 16:17:47 - DEBUG - [SESSION QUERY] Full query: Do Warfarin and Ibuprofen interact?
2026-05-02 16:17:48 - DEBUG - [TOOL] check_drug_interactions called with 2 drugs
2026-05-02 16:17:48 - DEBUG - [DRUG SERVICE] Fetching drug records from database
2026-05-02 16:17:54 - INFO - [DRUG SERVICE] Found 1 interactions among 2 drugs
2026-05-02 16:17:56 - INFO - [SESSION] Agent invocation completed in 8630.43ms
2026-05-02 16:17:57 - INFO - [SESSION QUERY] ========== QUERY COMPLETED SUCCESSFULLY ==========
```

### View Logs

#### Console (Real-time)
Logs automatically appear in the terminal where you run `python run.py`

#### File (Persistent)
```bash
# View all logs
cat backend/logs/MedicaLLM.log

# Follow logs in real-time
tail -f backend/logs/MedicaLLM.log

# View last 50 lines
tail -n 50 backend/logs/MedicaLLM.log
```

### Filter Logs

#### By Component
```bash
# Session queries
grep "\[SESSION QUERY\]" backend/logs/MedicaLLM.log

# Tool executions
grep "\[TOOL\]" backend/logs/MedicaLLM.log

# Database operations
grep "\[DRUG SERVICE\]" backend/logs/MedicaLLM.log

# PubMed API calls
grep "\[PUBMED\]" backend/logs/MedicaLLM.log

# Agent operations
grep "\[AGENT" backend/logs/MedicaLLM.log
```

#### By Log Level
```bash
# Debug logs only
grep "DEBUG" backend/logs/MedicaLLM.log

# Info logs only
grep "INFO" backend/logs/MedicaLLM.log

# Errors and warnings
grep -E "(ERROR|WARNING)" backend/logs/MedicaLLM.log
```

#### By Time Range
```bash
# Logs from specific date/time
grep "2026-05-02 16:17" backend/logs/MedicaLLM.log
```

## Log Levels

### DEBUG (Most Verbose)
- Detailed internal operations
- Variable values and data structures
- Step-by-step execution
- Database query details
- API call parameters

**Example:**
```
2026-05-02 16:17:47 - DEBUG - [SESSION] Query length: 42 chars, first 100 chars: Do Warfarin and Ibuprofen interact?
2026-05-02 16:17:47 - DEBUG - [SESSION] Request ID: a1b2c3d4e5f6
2026-05-02 16:17:47 - DEBUG - [TOOL] Resolving drug name 'Warfarin' to drug_id
```

### INFO (Default)
- High-level operation summaries
- Successful completions
- Important state changes
- Query processing milestones

**Example:**
```
2026-05-02 16:17:47 - INFO - [SESSION QUERY] User: user_123 (user@example.com)
2026-05-02 16:17:54 - INFO - [DRUG SERVICE] Found 1 interactions among 2 drugs
2026-05-02 16:17:56 - INFO - [SESSION] Agent invocation completed in 8630.43ms
```

### WARNING
- Non-critical issues
- Missing data
- Authorization failures
- Invalid inputs

**Example:**
```
2026-05-02 16:17:47 - WARNING - [TOOL] Drug not found: XYZ123
2026-05-02 16:17:47 - WARNING - [SESSION MANAGER] Unauthorized session access attempt
```

### ERROR
- Critical failures
- Database errors
- API failures
- Exception stack traces

**Example:**
```
2026-05-02 16:17:47 - ERROR - [DRUG SERVICE] Error getting drug DB00945: Connection timeout
Traceback (most recent call last):
  File "...", line 123, in get_drug
    ...
```

## Log Components

Each log entry is tagged with a component identifier:

| Tag | Component | Description |
|-----|-----------|-------------|
| `[SESSION QUERY]` | Session Router | HTTP endpoint operations |
| `[SESSION]` | Session Class | Session management and query handling |
| `[SESSION MANAGER]` | Session Manager | Session lifecycle management |
| `[TOOL]` | Agent Tools | All 8 agent tool executions |
| `[DRUG SERVICE]` | Drug Service | Database operations for drugs |
| `[PUBMED]` | PubMed Service | PubMed API operations |
| `[AGENT INIT]` | Agent Init | Agent initialization |
| `[AGENT CREATE]` | Agent Create | Agent creation and configuration |
| `[CONVERSATION]` | Conversation Service | Message and conversation management |
| `[AUTH]` | Auth Service | Authentication operations |

## What Gets Logged

### Every User Query
1. ✅ User information (ID, email)
2. ✅ Conversation ID
3. ✅ Patient context (if applicable)
4. ✅ Full query text
5. ✅ Session creation/retrieval
6. ✅ System prompt building
7. ✅ Agent invocation
8. ✅ Tool executions with parameters
9. ✅ Database queries
10. ✅ API calls (PubMed, LLM)
11. ✅ Execution timing
12. ✅ Results and sources
13. ✅ Message saving
14. ✅ Success/failure status

### Tool Executions
- Tool name and parameters
- Drug name resolution
- Database lookups
- Interaction checks
- PubMed searches
- Results and errors

### Performance Metrics
- Agent invocation time (ms)
- Database query time
- API call time
- Total query processing time

### Errors
- Full stack traces
- Error context
- Failed operations
- Recovery attempts

## Changing Log Level

### Temporarily (Current Session)
Edit `.env`:
```bash
LOG_LEVEL=INFO    # Less verbose
LOG_LEVEL=DEBUG   # Most verbose
LOG_LEVEL=WARNING # Only warnings and errors
LOG_LEVEL=ERROR   # Only errors
```

Then restart the backend.

### Permanently
Update `backend/src/config.py`:
```python
log_level: str = "INFO"  # Change default
```

## Production Recommendations

### For Development
```bash
LOG_LEVEL=DEBUG  # See everything
```

### For Production
```bash
LOG_LEVEL=INFO   # Balanced logging
```

### For Troubleshooting
```bash
LOG_LEVEL=DEBUG  # Temporarily enable for debugging
```

### Log Rotation
Set up log rotation to prevent disk space issues:

**Linux/Mac (`logrotate`):**
```
/path/to/backend/logs/MedicaLLM.log {
    daily
    rotate 7
    compress
    delaycompress
    missingok
    notifempty
}
```

**Windows (PowerShell script):**
```powershell
# Rotate logs older than 7 days
Get-ChildItem "backend/logs" -Filter "*.log" | 
    Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-7)} | 
    Remove-Item
```

## Troubleshooting

### No Logs Appearing in Console
1. Check `.env` file has `LOG_LEVEL=DEBUG`
2. Restart the backend
3. Check `backend/logs/MedicaLLM.log` exists

### Too Many Logs
1. Change `LOG_LEVEL=INFO` in `.env`
2. Restart the backend

### Logs Not Updating
1. Make sure you restarted the backend after changing `.env`
2. Check file permissions on `backend/logs/` directory

### Missing DEBUG Logs
1. Verify `.env` has `LOG_LEVEL=DEBUG` (not INFO)
2. Restart backend completely
3. Check console output

## Example: Debugging a Query

1. **Start backend with DEBUG logging:**
   ```bash
   cd backend
   python run.py
   ```

2. **Make a query from frontend**

3. **Watch console output in real-time** - you'll see:
   - Request received
   - User authentication
   - Session creation
   - Query processing
   - Tool executions
   - Database queries
   - API calls
   - Results
   - Response sent

4. **Review file logs for details:**
   ```bash
   tail -f backend/logs/MedicaLLM.log
   ```

## Success Indicators

When logging is working correctly, you should see:

✅ Console shows logs in real-time
✅ File `backend/logs/MedicaLLM.log` is being updated
✅ Both DEBUG and INFO logs appear
✅ Component tags like `[SESSION QUERY]`, `[TOOL]` are visible
✅ Timing information shows execution duration
✅ Tool executions are logged with parameters
✅ Database operations are logged
✅ Errors show full stack traces

## Next Steps

1. ✅ Logging is configured and working
2. ✅ Both console and file output enabled
3. ✅ DEBUG level active for comprehensive logging
4. 📝 Monitor logs during normal operation
5. 📝 Identify performance bottlenecks from timing data
6. 📝 Set up log rotation for production
7. 📝 Consider structured logging (JSON) for parsing
8. 📝 Integrate with monitoring tools if needed

## Support

If you encounter issues:
1. Check `.env` has `LOG_LEVEL=DEBUG`
2. Restart backend completely
3. Verify `backend/logs/` directory exists and is writable
4. Check console for any startup errors
5. Review `backend/logs/MedicaLLM.log` for error messages
