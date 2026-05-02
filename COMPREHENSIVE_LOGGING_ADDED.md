# Comprehensive Debug Logging Added to MedicaLLM Backend

## Summary

Extensive debug logging has been added throughout the entire MedicaLLM backend to provide detailed visibility into all operations, especially agent querying and tool execution.

## Changes Made

### 1. Configuration (`backend/src/config.py`)
- **Changed default log level from INFO to DEBUG** for comprehensive logging
- All logs are written to `logs/MedicaLLM.log`

### 2. Agent Tools (`backend/src/agent/tools.py`)
Added detailed logging to all 8 agent tools:

#### `get_drug_info`
- Logs drug name resolution process
- Logs drug_id resolution
- Logs detail level and response building
- Logs errors with full stack traces

#### `check_drug_interactions`
- Logs number of drugs being checked
- Logs drug name to ID resolution process
- Logs interaction checking process
- Logs number of interactions found with severity levels

#### `check_drug_food_interaction`
- Logs drug resolution
- Logs food interaction queries

#### `search_drugs_by_indication`
- Logs indication search queries
- Logs results count

#### `search_drugs_by_category`
- Logs category search queries
- Logs results count

#### `recommend_alternative_drug`
- Logs alternative drug search process
- Logs filtering logic

#### `analyze_patient_medications`
- Logs patient ID and medication analysis
- Logs interaction detection
- Logs alternative recommendations

#### `search_pubmed`
- Logs query validation (English check)
- Logs PubMed API calls
- Logs article retrieval and parsing
- Logs confidence scoring
- Logs article PMIDs and metadata

### 3. Session Management (`backend/src/session/session.py`)
Added comprehensive logging to query handling:

- **`handle_user_query`**:
  - Logs session ID and request ID
  - Logs query length and preview
  - Logs message history length
  - Logs system prompt length
  - Logs agent invocation start/completion
  - Logs execution time in milliseconds
  - Logs result structure (messages, tools, sources)
  - Logs message saving process
  - Logs title generation scheduling

- **Message deduplication**:
  - Logs duplicate detection
  - Logs message append decisions

- **Agent invocation**:
  - Logs agent type
  - Logs recursion limit
  - Logs result keys and structure
  - Logs tools used and sources count

### 4. Session Router (`backend/src/session/router.py`)
Added detailed endpoint logging:

- **`endpoint_query`**:
  - Logs request start with separator line
  - Logs user information (ID, email)
  - Logs conversation ID and patient ID
  - Logs query preview and full query
  - Logs session creation/retrieval
  - Logs user role (doctor/patient)
  - Logs patient loading process
  - Logs system prompt building
  - Logs context variable setting
  - Logs query processing duration
  - Logs result structure and success
  - Logs tools used and sources
  - Logs completion with separator line

- **`_get_or_create_session`**:
  - Logs session manager operations
  - Logs agent availability
  - Logs session ownership verification

### 5. Drug Service (`backend/src/drugs/service.py`)
Added detailed database operation logging:

- **`get_drug`**:
  - Logs drug_id lookup
  - Logs database query execution
  - Logs drug retrieval with metadata (synonyms, interactions)

- **`search_drugs`**:
  - Logs search query and parameters
  - Logs search options (synonyms, products, brands)
  - Logs normalized search term
  - Logs name search results count
  - Logs synonym/product/brand searches

- **`check_drug_interactions`**:
  - Logs number of drugs being checked
  - Logs database fetching
  - Logs pair-wise interaction checking
  - Logs each interaction found with severity
  - Logs overall interaction summary

### 6. PubMed Service (`backend/src/pubmed/service.py`)
Added comprehensive API call logging:

- **`search_pubmed`**:
  - Logs query details and parameters
  - Logs API key usage
  - Logs esearch execution and URL
  - Logs PMIDs retrieved
  - Logs efetch execution
  - Logs XML parsing process
  - Logs each article parsed with PMID and confidence
  - Logs filtering by confidence threshold
  - Logs sorting and final results
  - Logs search timing

### 7. Agent Initialization (`backend/src/agent/agent.py`, `backend/src/agent/langchain_agent.py`)
Added initialization logging:

- **`init_medical_agent`**:
  - Logs initialization start
  - Logs LLM configuration (model, temperature, iterations)
  - Logs success/failure with agent type

- **`create_medical_agent`**:
  - Logs model configuration details
  - Logs LLM base URL and settings
  - Logs number of tools and tool names
  - Logs ChatOpenAI model creation
  - Logs agent creation success

### 8. Conversation Service (`backend/src/conversations/service.py`)
Added message handling logging:

- **`add_message`**:
  - Logs conversation ID and message role
  - Logs total message count after addition

- **`add_messages`**:
  - Logs batch message addition
  - Logs count of messages added
  - Logs total message count

### 9. Auth Service (`backend/src/auth/service.py`)
Added authentication logging:

- **`register_user`**:
  - Logs registration attempts
  - Logs user_id generation
  - Logs registration success/failure

- **`login_user`**:
  - Logs login attempts
  - Logs authentication success/failure
  - Logs invalid credentials warnings

- **`verify_token`**:
  - Logs token verification
  - Logs token expiration/invalidity

## Log Levels Used

### DEBUG
- Detailed internal state information
- Function entry/exit points
- Variable values and data structures
- Step-by-step process execution
- Database query details
- API call details

### INFO
- High-level operation summaries
- Successful completions
- Important state changes
- Query processing milestones
- Search results summaries

### WARNING
- Non-critical issues
- Missing data
- Authorization failures
- Duplicate operations
- Invalid inputs

### ERROR
- Critical failures
- Database errors
- API failures
- Exception stack traces

## Log Format

All logs follow the format:
```
YYYY-MM-DD HH:MM:SS - LEVEL - [COMPONENT] Message
```

Examples:
```
2026-05-02 14:23:45 - DEBUG - [SESSION QUERY] User: user_123 (user@example.com)
2026-05-02 14:23:45 - INFO - [TOOL] get_drug_info: drug_name='Aspirin', detail='moderate'
2026-05-02 14:23:46 - DEBUG - [DRUG SERVICE] Found 1 drugs in database
2026-05-02 14:23:47 - INFO - [SESSION] Agent invocation completed in 1234.56ms
```

## Log Tags by Component

- `[SESSION QUERY]` - Session router endpoint operations
- `[SESSION]` - Session class operations
- `[SESSION MANAGER]` - Session manager operations
- `[TOOL]` - Agent tool executions
- `[DRUG SERVICE]` - Drug database service operations
- `[PUBMED]` - PubMed API operations
- `[AGENT INIT]` - Agent initialization
- `[AGENT CREATE]` - Agent creation
- `[CONVERSATION]` - Conversation service operations
- `[AUTH]` - Authentication operations

## Viewing Logs

### Real-time monitoring:
```bash
tail -f backend/logs/MedicaLLM.log
```

### Filter by component:
```bash
grep "\[SESSION QUERY\]" backend/logs/MedicaLLM.log
grep "\[TOOL\]" backend/logs/MedicaLLM.log
grep "\[PUBMED\]" backend/logs/MedicaLLM.log
```

### Filter by log level:
```bash
grep "DEBUG" backend/logs/MedicaLLM.log
grep "ERROR" backend/logs/MedicaLLM.log
```

### View errors only:
```bash
grep -E "(ERROR|WARNING)" backend/logs/MedicaLLM.log
```

## Benefits

1. **Complete Visibility**: Every operation is logged with context
2. **Performance Tracking**: Execution times logged for all major operations
3. **Debugging**: Detailed stack traces and variable states
4. **Audit Trail**: Complete record of all user queries and agent responses
5. **Tool Usage**: Track which tools are called and their results
6. **API Monitoring**: Track external API calls (PubMed, LLM)
7. **Error Diagnosis**: Comprehensive error information with context

## Performance Impact

- Log level can be changed to INFO or WARNING in production to reduce log volume
- DEBUG level is recommended for development and troubleshooting
- Logs are written asynchronously to minimize performance impact

## Configuration

To change log level, update `backend/src/config.py` or set environment variable:
```bash
export LOG_LEVEL=INFO  # or DEBUG, WARNING, ERROR
```

## Next Steps

1. Monitor logs during agent queries to identify bottlenecks
2. Use log analysis tools to track patterns
3. Set up log rotation for production environments
4. Consider structured logging (JSON) for easier parsing
5. Integrate with monitoring tools (ELK stack, Datadog, etc.)
