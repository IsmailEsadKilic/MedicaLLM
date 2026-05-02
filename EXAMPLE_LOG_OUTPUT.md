# Example Log Output

This document shows what the comprehensive debug logging looks like for a typical user query.

## Example Query: "What is Aspirin?"

### Complete Log Trace

```
2026-05-02 14:23:45,123 - INFO - [SESSION QUERY] ========== NEW QUERY REQUEST ==========
2026-05-02 14:23:45,124 - INFO - [SESSION QUERY] User: user_1714665825000 (john.doe@example.com)
2026-05-02 14:23:45,124 - INFO - [SESSION QUERY] Conversation: conv_abc123def456
2026-05-02 14:23:45,124 - INFO - [SESSION QUERY] Patient ID: None
2026-05-02 14:23:45,124 - INFO - [SESSION QUERY] Query: What is Aspirin?
2026-05-02 14:23:45,125 - DEBUG - [SESSION QUERY] Full query: What is Aspirin?
2026-05-02 14:23:45,125 - DEBUG - [SESSION QUERY] Session ID from body: None
2026-05-02 14:23:45,126 - DEBUG - [SESSION QUERY] Getting or creating session
2026-05-02 14:23:45,127 - DEBUG - [SESSION MANAGER] _get_or_create_session called for conversation conv_abc123def456, user user_1714665825000
2026-05-02 14:23:45,128 - DEBUG - [SESSION MANAGER] Agent found: <class 'src.agent.agent.MedicalAgent'>
2026-05-02 14:23:45,129 - INFO - [SESSION MANAGER] Session cache hit: conv_abc123def456
2026-05-02 14:23:45,130 - DEBUG - [SESSION MANAGER] Session obtained: sess_xyz789, user_id: user_1714665825000
2026-05-02 14:23:45,131 - DEBUG - [SESSION MANAGER] Session ownership verified
2026-05-02 14:23:45,132 - INFO - [SESSION QUERY] Session obtained: sess_xyz789
2026-05-02 14:23:45,133 - DEBUG - [SESSION QUERY] User role - is_doctor: False, is_patient: False
2026-05-02 14:23:45,134 - DEBUG - [SESSION QUERY] Building dynamic system prompt
2026-05-02 14:23:45,135 - DEBUG - [SESSION QUERY] System prompt length: 3456 chars
2026-05-02 14:23:45,136 - DEBUG - [SESSION QUERY] Set current_user_id context var: user_1714665825000
2026-05-02 14:23:45,137 - INFO - [SESSION QUERY] Processing query: What is Aspirin?...
2026-05-02 14:23:45,138 - DEBUG - [SESSION] handle_user_query called for session sess_xyz789
2026-05-02 14:23:45,139 - DEBUG - [SESSION] Query length: 18 chars, first 100 chars: What is Aspirin?
2026-05-02 14:23:45,140 - DEBUG - [SESSION] Request ID: a1b2c3d4e5f6
2026-05-02 14:23:45,141 - DEBUG - [SESSION] Is first message: False, current message count: 4
2026-05-02 14:23:45,142 - DEBUG - [SESSION] Last message role: assistant
2026-05-02 14:23:45,143 - DEBUG - [SESSION] Appending user message to conversation
2026-05-02 14:23:45,144 - DEBUG - [CONVERSATION] add_message called for conversation conv_abc123def456, role: user
2026-05-02 14:23:45,145 - DEBUG - [CONVERSATION] Message added, total messages: 5
2026-05-02 14:23:45,146 - DEBUG - [SESSION] Message history length: 4 messages
2026-05-02 14:23:45,147 - DEBUG - [SESSION] System prompt length: 3456 chars
2026-05-02 14:23:45,148 - INFO - [SESSION] Starting agent invocation at 1714665825.148
2026-05-02 14:23:45,149 - INFO - [SESSION] Invoking agent with recursion_limit=50
2026-05-02 14:23:45,150 - DEBUG - [SESSION] Agent type: <class 'src.agent.agent.MedicalAgent'>

2026-05-02 14:23:45,200 - DEBUG - [TOOL] get_drug_info called with drug_name='Aspirin', detail='moderate'
2026-05-02 14:23:45,201 - INFO - [TOOL] get_drug_info: drug_name='Aspirin', detail='moderate'
2026-05-02 14:23:45,202 - DEBUG - [TOOL] Resolving drug name 'Aspirin' to drug_id
2026-05-02 14:23:45,203 - INFO - [TOOL] Resolved 'Aspirin' to drug_id: DB00945
2026-05-02 14:23:45,204 - DEBUG - [TOOL] Resolved 'Aspirin' to drug_id: DB00945
2026-05-02 14:23:45,205 - DEBUG - [TOOL] Fetching full drug information for DB00945
2026-05-02 14:23:45,206 - DEBUG - [DRUG SERVICE] get_drug called with drug_id: DB00945
2026-05-02 14:23:45,207 - DEBUG - [DRUG SERVICE] Querying database for drug DB00945
2026-05-02 14:23:45,250 - INFO - [DRUG SERVICE] Retrieved drug: Aspirin (DB00945)
2026-05-02 14:23:45,251 - DEBUG - [DRUG SERVICE] Drug has 15 synonyms, 234 interactions
2026-05-02 14:23:45,252 - DEBUG - [TOOL] Building response for Aspirin with detail level: moderate

2026-05-02 14:23:46,100 - INFO - [SESSION] Agent invocation completed in 952.34ms
2026-05-02 14:23:46,101 - DEBUG - [SESSION] Result keys: dict_keys(['messages'])
2026-05-02 14:23:46,102 - DEBUG - [SESSION] AgentResponse created with 1 messages
2026-05-02 14:23:46,103 - DEBUG - [SESSION] Tools used: [{'tool_name': 'get_drug_info', 'tool_result': '**Aspirin** (DB00945)...'}]
2026-05-02 14:23:46,104 - DEBUG - [SESSION] Sources count: 0
2026-05-02 14:23:46,105 - DEBUG - [SESSION] Extending conversation with 1 messages
2026-05-02 14:23:46,106 - DEBUG - [CONVERSATION] add_messages called for conversation conv_abc123def456, count: 1
2026-05-02 14:23:46,107 - INFO - [CONVERSATION] Added 1 messages, total: 6
2026-05-02 14:23:46,108 - INFO - [SESSION] Saved 1 messages, total count: 6
2026-05-02 14:23:46,109 - INFO - [SESSION] Query processing completed successfully
2026-05-02 14:23:46,110 - INFO - [SESSION QUERY] Query processed in 972.45ms
2026-05-02 14:23:46,111 - DEBUG - [SESSION QUERY] Result success: True
2026-05-02 14:23:46,112 - DEBUG - [SESSION QUERY] Result messages: 1
2026-05-02 14:23:46,113 - DEBUG - [SESSION QUERY] Result sources: 0
2026-05-02 14:23:46,114 - DEBUG - [SESSION QUERY] Result tools used: ['get_drug_info']
2026-05-02 14:23:46,115 - INFO - [SESSION QUERY] ========== QUERY COMPLETED SUCCESSFULLY ==========
```

## Example Query: "Check interactions between Aspirin and Warfarin"

### Complete Log Trace

```
2026-05-02 14:25:30,123 - INFO - [SESSION QUERY] ========== NEW QUERY REQUEST ==========
2026-05-02 14:25:30,124 - INFO - [SESSION QUERY] User: user_1714665825000 (john.doe@example.com)
2026-05-02 14:25:30,125 - INFO - [SESSION QUERY] Conversation: conv_abc123def456
2026-05-02 14:25:30,126 - INFO - [SESSION QUERY] Query: Check interactions between Aspirin and Warfarin
2026-05-02 14:25:30,127 - DEBUG - [SESSION QUERY] Full query: Check interactions between Aspirin and Warfarin
2026-05-02 14:25:30,128 - INFO - [SESSION QUERY] Processing query: Check interactions between Aspirin and...

2026-05-02 14:25:30,200 - DEBUG - [TOOL] check_drug_interactions called with 2 drugs: ['Aspirin', 'Warfarin']
2026-05-02 14:25:30,201 - INFO - [TOOL] check_drug_interactions: drug_names=['Aspirin', 'Warfarin']
2026-05-02 14:25:30,202 - DEBUG - [TOOL] Resolving 2 drug names to IDs
2026-05-02 14:25:30,203 - INFO - [TOOL] Resolved 'Aspirin' to drug_id: DB00945
2026-05-02 14:25:30,204 - INFO - [TOOL] Resolved 'Warfarin' to drug_id: DB00682
2026-05-02 14:25:30,205 - DEBUG - [TOOL] Resolved 2 drug IDs: ['DB00945', 'DB00682']
2026-05-02 14:25:30,206 - DEBUG - [TOOL] Checking interactions for drug_ids: ['DB00945', 'DB00682']
2026-05-02 14:25:30,207 - DEBUG - [DRUG SERVICE] check_drug_interactions called with 2 drugs: ['DB00945', 'DB00682']
2026-05-02 14:25:30,208 - DEBUG - [DRUG SERVICE] Fetching drug records from database
2026-05-02 14:25:30,250 - DEBUG - [DRUG SERVICE] Found 2 drugs in database
2026-05-02 14:25:30,251 - DEBUG - [DRUG SERVICE] Checking all drug pairs for interactions
2026-05-02 14:25:30,300 - DEBUG - [DRUG SERVICE] Interaction found: Aspirin + Warfarin, severity: 0.85
2026-05-02 14:25:30,301 - INFO - [DRUG SERVICE] Found 1 interactions among 2 drugs, max severity: 0.85
2026-05-02 14:25:30,302 - DEBUG - [TOOL] Found 1 interactions

2026-05-02 14:25:31,100 - INFO - [SESSION] Agent invocation completed in 900.12ms
2026-05-02 14:25:31,101 - DEBUG - [SESSION] Tools used: [{'tool_name': 'check_drug_interactions', 'tool_result': 'Found 1 interaction(s)...'}]
2026-05-02 14:25:31,102 - INFO - [SESSION QUERY] Query processed in 977.89ms
2026-05-02 14:25:31,103 - INFO - [SESSION QUERY] ========== QUERY COMPLETED SUCCESSFULLY ==========
```

## Example Query: "Find research on metformin and longevity"

### Complete Log Trace

```
2026-05-02 14:30:15,123 - INFO - [SESSION QUERY] ========== NEW QUERY REQUEST ==========
2026-05-02 14:30:15,124 - INFO - [SESSION QUERY] User: user_1714665825000 (john.doe@example.com)
2026-05-02 14:30:15,125 - INFO - [SESSION QUERY] Query: Find research on metformin and longevity

2026-05-02 14:30:15,200 - DEBUG - [TOOL] search_pubmed called with query='metformin longevity', num_articles=5
2026-05-02 14:30:15,201 - INFO - [TOOL] PubMed search for: metformin longevity
2026-05-02 14:30:15,202 - DEBUG - [TOOL] Calling pubmed_service.search_pubmed with max_results=5
2026-05-02 14:30:15,203 - INFO - [PUBMED] PubMed search: 'metformin longevity' (max_results=5, min_confidence=35.0)
2026-05-02 14:30:15,204 - DEBUG - [PUBMED] Query length: 19 chars
2026-05-02 14:30:15,205 - DEBUG - [PUBMED] Using API key: True
2026-05-02 14:30:15,206 - DEBUG - [PUBMED] Step 1: Executing esearch
2026-05-02 14:30:15,207 - DEBUG - [PUBMED] esearch URL: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=metformin%20longevity...
2026-05-02 14:30:15,800 - INFO - [PUBMED] esearch found 234 total articles, retrieved 5 PMIDs
2026-05-02 14:30:15,801 - DEBUG - [PUBMED] PMIDs: ['38123456', '38123457', '38123458', '38123459', '38123460']
2026-05-02 14:30:15,802 - DEBUG - [PUBMED] Step 2: Fetching article details with efetch
2026-05-02 14:30:15,803 - DEBUG - [PUBMED] efetch URL: https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=pubmed&id=38123456,38123457...
2026-05-02 14:30:16,500 - DEBUG - [PUBMED] Step 3: Parsing XML articles
2026-05-02 14:30:16,501 - DEBUG - [PUBMED] Parsed article: PMID 38123456, confidence: 82.5
2026-05-02 14:30:16,502 - DEBUG - [PUBMED] Parsed article: PMID 38123457, confidence: 78.3
2026-05-02 14:30:16,503 - DEBUG - [PUBMED] Parsed article: PMID 38123458, confidence: 75.1
2026-05-02 14:30:16,504 - DEBUG - [PUBMED] Parsed article: PMID 38123459, confidence: 71.8
2026-05-02 14:30:16,505 - DEBUG - [PUBMED] Parsed article: PMID 38123460, confidence: 68.2
2026-05-02 14:30:16,506 - INFO - [PUBMED] Successfully parsed 5 articles
2026-05-02 14:30:16,507 - DEBUG - [PUBMED] Step 4: Filtering by confidence >= 35.0
2026-05-02 14:30:16,508 - DEBUG - [PUBMED] Sorted 5 articles by confidence
2026-05-02 14:30:16,509 - INFO - [PUBMED] Retrieved 5 articles (avg confidence: 75.2) in 1306.45ms
2026-05-02 14:30:16,510 - DEBUG - [TOOL] PubMed search completed: 5 articles, search_time=1306.45ms
2026-05-02 14:30:16,511 - DEBUG - [TOOL] Article PMIDs: ['38123456', '38123457', '38123458', '38123459', '38123460']

2026-05-02 14:30:17,800 - INFO - [SESSION] Agent invocation completed in 2600.34ms
2026-05-02 14:30:17,801 - DEBUG - [SESSION] Tools used: [{'tool_name': 'search_pubmed', 'tool_result': 'RETRIEVED PUBMED ARTICLES...'}]
2026-05-02 14:30:17,802 - DEBUG - [SESSION] Sources count: 5
2026-05-02 14:30:17,803 - INFO - [SESSION QUERY] Query processed in 2677.89ms
2026-05-02 14:30:17,804 - INFO - [SESSION QUERY] ========== QUERY COMPLETED SUCCESSFULLY ==========
```

## Example Error Log

### Drug Not Found

```
2026-05-02 14:35:20,123 - INFO - [SESSION QUERY] ========== NEW QUERY REQUEST ==========
2026-05-02 14:35:20,124 - INFO - [SESSION QUERY] Query: What is XYZ123?
2026-05-02 14:35:20,200 - DEBUG - [TOOL] get_drug_info called with drug_name='XYZ123', detail='moderate'
2026-05-02 14:35:20,201 - INFO - [TOOL] get_drug_info: drug_name='XYZ123', detail='moderate'
2026-05-02 14:35:20,202 - DEBUG - [TOOL] Resolving drug name 'XYZ123' to drug_id
2026-05-02 14:35:20,250 - WARNING - [TOOL] Could not resolve drug name: XYZ123
2026-05-02 14:35:20,251 - WARNING - [TOOL] Drug not found: XYZ123
```

### Database Connection Error

```
2026-05-02 14:40:10,123 - DEBUG - [DRUG SERVICE] get_drug called with drug_id: DB00945
2026-05-02 14:40:10,124 - DEBUG - [DRUG SERVICE] Querying database for drug DB00945
2026-05-02 14:40:15,125 - ERROR - [DRUG SERVICE] Error getting drug DB00945: (psycopg2.OperationalError) could not connect to server: Connection timed out
Traceback (most recent call last):
  File "C:\Ismail Projects\MedicaLLM\backend\src\drugs\service.py", line 123, in get_drug
    drug_orm = session.query(DrugORM).filter(DrugORM.drug_id == drug_id).first()
  File "...", line 456, in first
    ...
psycopg2.OperationalError: could not connect to server: Connection timed out
2026-05-02 14:40:15,126 - ERROR - [SESSION] Error processing query: Error retrieving drug information
```

## Log Filtering Examples

### View only session queries:
```bash
grep "\[SESSION QUERY\]" backend/logs/MedicaLLM.log
```

### View only tool executions:
```bash
grep "\[TOOL\]" backend/logs/MedicaLLM.log
```

### View only errors and warnings:
```bash
grep -E "(ERROR|WARNING)" backend/logs/MedicaLLM.log
```

### View timing information:
```bash
grep "completed in" backend/logs/MedicaLLM.log
```

### Track a specific request:
```bash
grep "Request ID: a1b2c3d4e5f6" backend/logs/MedicaLLM.log
```

### View PubMed operations:
```bash
grep "\[PUBMED\]" backend/logs/MedicaLLM.log
```

### View database operations:
```bash
grep "\[DRUG SERVICE\]" backend/logs/MedicaLLM.log
```
