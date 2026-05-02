# Agent Tools & System Prompt Overhaul Summary

## Overview
Complete overhaul of LangChain agent tools to align with the updated drug service architecture and improved debug/source information handling.

## Changes Made

### 1. **backend/src/agent/tools.py** - Complete Rewrite

#### New Tool Structure

All tools now properly resolve drug names to DrugBank IDs using the search service before calling the drug service methods.

**Tool 1: get_drug_info**
- Signature: `get_drug_info(drug_name: str, detail: Literal["low", "moderate", "high"])`
- Resolves drug name to ID
- Calls `drug_service.get_drug(drug_id)`
- Returns formatted drug information based on detail level
- Low: Basic info (description, indication)
- Moderate: Clinical info (mechanism, pharmacodynamics, toxicity, metabolism)
- High: Comprehensive (includes targets, enzymes, carriers, transporters)

**Tool 2: check_drug_interactions**
- Signature: `check_drug_interactions(drug_names: list[str])`
- Resolves all drug names to IDs
- Calls `drug_service.check_drug_interactions(CheckDrugInteractionRequest)`
- Returns formatted interaction list with severity indicators (🔴 MAJOR, 🟠 MODERATE, 🟡 MINOR)
- Sorts by severity (highest first)

**Tool 3: check_drug_food_interaction**
- Signature: `check_drug_food_interaction(drug_name: str, food_items: list[str])`
- Resolves drug name to ID
- Calls `drug_service.check_drug_food_interactions(drug_id)`
- Highlights relevant food items if specified
- Returns all food interactions for the drug

**Tool 4: search_drugs_by_indication**
- Signature: `search_drugs_by_indication(condition: str)`
- Calls `drug_service.search_drugs_by_indication(DrugSearchByIndicationRequest)`
- Returns list of drugs that treat the specified condition
- Includes drug descriptions

**Tool 5: search_drugs_by_category**
- Signature: `search_drugs_by_category(category: str)`
- Calls `drug_service.search_drugs_by_category(DrugSearchByCategoryRequest)`
- Returns list of drugs in the therapeutic category
- Includes drug descriptions

**Tool 6: recommend_alternative_drug**
- Signature: `recommend_alternative_drug(current_drug_names: list[str], for_drug_name: str)`
- Resolves all drug names to IDs
- Calls `drug_service.get_alternative_drugs(current_drug_ids, for_drug_id)`
- Returns safe alternatives that don't interact with current medications
- Includes reason for each alternative

**Tool 7: analyze_patient_medications**
- Signature: `analyze_patient_medications(additional_drugs: list[str])`
- Uses context variable to get current patient ID
- Resolves additional drug names to IDs
- Calls `drug_service.analyze_patient(AnalyzePatientRequest)`
- Returns comprehensive analysis:
  - Current medications
  - All drug-drug interactions (sorted by severity)
  - Safe alternatives for problematic drugs

#### Helper Functions

**_resolve_drug_name_to_id(drug_name: str) -> Optional[str]**
- Uses `drug_service.search_drugs()` to find best match
- Returns DrugBank ID or None

**_resolve_drug_names_to_ids(drug_names: list[str]) -> list[str]**
- Batch resolves multiple drug names
- Skips unresolved names

#### Context Variables

Added new context variable:
- `_current_patient_id_var`: Stores patient ID for patient-scoped operations
- `set_current_patient_id(patient_id)`: Set patient context
- `get_current_patient_id()`: Get patient context

#### Debug & Source Information

Fixed the source and debug information storage:
- `_store_sources()`: Properly accumulates sources from multiple tool calls
- `_store_debug()`: Stores debug information per request
- `get_last_search_sources(request_id)`: Retrieves and clears sources
- `get_last_tool_debug(request_id)`: Retrieves and clears debug info

### 2. **backend/src/session/session.py** - Fixed Debug/Source Handling

#### AgentResponse Model
- Updated `from_agent_result()` to accept `request_id` parameter
- Properly extracts tools_used and tool_results from agent messages
- Creates Message objects with tools_used, tool_results, and sources
- Sources are extracted from the source store using request_id

#### Session.handle_user_query()
- Added `patient_id` parameter
- Calls `set_current_patient_id(patient_id)` to set patient context
- Passes `request_id` to `AgentResponse.from_agent_result()`
- Passes `patient_id` to session handler

### 3. **backend/src/session/router.py** - Patient Context Support

#### endpoint_query
- Imports `set_current_patient_id` from tools
- Calls `set_current_patient_id(body.patient_id)` if patient_id provided
- Passes `patient_id` to `session.handle_user_query()`

### 4. **backend/src/agent/langchain_agent.py** - Improved System Prompt

#### New SYSTEM_PROMPT Structure

**Core Principles:**
1. Evidence-based responses
2. Conversational for greetings
3. Multi-tool chaining
4. Clear & structured formatting

**Tool Documentation:**
- Clear descriptions of all 7 tools
- Parameter explanations
- Usage examples

**Response Guidelines:**
- Specific guidance for each query type
- Drug information queries
- Interaction queries
- Patient medication analysis
- Treatment recommendations
- Alternative drug requests

**Formatting Rules:**
- Bold for drug names
- Emoji severity indicators
- Table formatting guidelines
- Bullet points for lists

**Safety Reminders:**
- Disclaimers about consulting healthcare providers
- Flag high-severity interactions
- Note limitations

**Conversation Style:**
- Professional but approachable
- Natural greetings
- Clarifying questions
- Acknowledge uncertainty

#### Role-Specific Prompts

**_ROLE_HEALTHCARE:**
- Clinical terminology
- Mechanism of action details
- Pharmacokinetic considerations
- Evidence-based citations
- Dosing considerations

**_ROLE_GENERAL:**
- Plain language
- Avoid jargon
- Practical safety advice
- Recommend consulting providers
- Educational information disclaimer

#### Patient Context Block

**build_system_prompt():**
- Improved formatting with markdown
- Clear patient profile section
- Explicit rules for patient context:
  - Consider profile in every answer
  - Proactively flag allergy conflicts
  - Proactively flag medication conflicts
  - Use analyze_patient_medications tool
  - Tool automatically accesses patient data

### 5. **backend/src/conversations/models.py** - Message Model

The Message model already supports:
- `tools_used: List[str]` - List of tool names used
- `tool_results: List[str]` - List of tool results (linked by index)
- `sources: List[str]` - List of sources cited

## Key Improvements

### 1. Drug Name Resolution
- All tools now properly resolve drug names to IDs before calling service
- Handles synonyms, brands, and product names
- Graceful error handling for unresolved names

### 2. Consistent Response Formatting
- All tools return well-formatted, structured responses
- Severity indicators with emojis
- Clear sections and headers
- Appropriate disclaimers

### 3. Patient Context Support
- Patient ID stored in context variable
- analyze_patient_medications automatically uses patient context
- Patient profile included in system prompt
- Proactive conflict detection

### 4. Debug & Source Tracking
- Fixed cross-thread propagation issues
- Sources properly accumulated from multiple tool calls
- Debug information properly stored and retrieved
- Request ID used for cross-thread lookup

### 5. Improved System Prompt
- Clear tool documentation
- Specific response guidelines for each query type
- Role-appropriate language (healthcare vs. general)
- Patient context rules
- Safety reminders and disclaimers

## Testing Recommendations

1. **Test Drug Name Resolution:**
   - Try various drug names (generic, brand, synonyms)
   - Test with misspellings
   - Verify error handling

2. **Test Tool Chaining:**
   - Query that requires multiple tools
   - e.g., "Check if Warfarin interacts with Aspirin and suggest alternatives"

3. **Test Patient Context:**
   - Set patient context
   - Ask to analyze patient medications
   - Verify patient data is used correctly

4. **Test Debug/Source Information:**
   - Verify sources are captured from tool calls
   - Check debug information is available
   - Test with multiple tool calls in one query

5. **Test Response Formatting:**
   - Verify severity indicators display correctly
   - Check table formatting
   - Verify markdown rendering

## Migration Notes

- No database schema changes required
- No API contract changes
- Backward compatible with existing conversations
- All existing endpoints continue to work

## Next Steps

1. Add PubMed tool back (search_pubmed) when ready
2. Consider adding more detail levels for other tools
3. Add caching for drug name resolution
4. Add metrics/logging for tool usage
5. Consider adding tool-specific rate limiting
