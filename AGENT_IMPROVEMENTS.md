# Agent Behavior Improvements

## Summary
Updated the MedicaLLM agent system prompt to improve intelligent handling of PubMed searches and patient-aware drug analysis.

## Changes Made

### 1. Smart PubMed Article Count Handling

**Location**: `backend/src/agent/langchain_agent.py`

**Behavior**:
- **Ask for count**: When user says generic phrases like "search pubmed" or "find articles" WITHOUT specifying a number
  - Agent asks: "How many articles would you like? (I can retrieve up to 20, default is 5)"
  
- **Use specified count**: When user specifies a number (e.g., "give me 3 articles on diabetes")
  - Agent uses that exact number without asking
  
- **Multiple searches with count limit**: Agent can perform multiple searches but respects user's total article count
  - Example: User asks for 3 articles → Agent searches "diabetes type 1" (3 articles) + "diabetes type 2" (3 articles) → Agent cites only the 3 MOST RELEVANT articles total

**Updated Sections**:
1. Tool description for `search_pubmed` - Added `num_articles` parameter documentation
2. "Tool Usage Efficiency" section - Added PubMed-specific guidance
3. "For PubMed Research Queries" section - Added detailed examples and rules

### 2. Patient-Aware Drug Analysis

**Location**: `backend/src/agent/langchain_agent.py`

**Behavior**:
- **Automatic patient analysis**: When a patient profile is active and user mentions ANY drug names, agent automatically calls `analyze_patient_medications` with those drugs as `additional_drugs`
  
**Examples**:
- User: "What about Aspirin?" → `analyze_patient_medications(additional_drugs=["Aspirin"])`
- User: "Can they take Ibuprofen and Warfarin?" → `analyze_patient_medications(additional_drugs=["Ibuprofen", "Warfarin"])`
- User: "Tell me about Metformin" → `analyze_patient_medications(additional_drugs=["Metformin"])` THEN `get_drug_info("Metformin")`

**Updated Sections**:
1. Tool description for `analyze_patient_medications` - Added critical rule about automatic invocation
2. "For Patient Medication Analysis" section - Added detailed examples
3. "IMPORTANT PATIENT CONTEXT RULES" section - Added explicit examples of when to trigger analysis

## Benefits

### PubMed Improvements:
- ✅ Reduces unnecessary back-and-forth when user specifies article count
- ✅ Prevents over-retrieval while allowing comprehensive searches
- ✅ Ensures final response matches user's requested article count
- ✅ Maintains conversational flow for vague requests

### Patient Analysis Improvements:
- ✅ Proactive safety checking when drugs are mentioned
- ✅ Automatic interaction detection with patient's current medications
- ✅ Seamless integration of patient context into all drug queries
- ✅ Reduces risk of missing critical drug interactions

## Testing Scenarios

### PubMed:
1. "search pubmed for diabetes" → Should ask for article count
2. "give me 5 articles on hypertension" → Should search with num_articles=5
3. "find 3 articles on diabetes" → Should cite exactly 3 articles even if multiple searches performed

### Patient Analysis:
1. Patient on [Warfarin, Metformin], user asks "what about Aspirin?" → Should analyze patient + Aspirin
2. Patient on [Lisinopril], user asks "tell me about Ibuprofen" → Should analyze patient + Ibuprofen, then provide drug info
3. No patient context, user asks "what about Aspirin?" → Should provide general drug info (no patient analysis)

## Files Modified
- `backend/src/agent/langchain_agent.py` - System prompt updates
- `backend/src/agent/tools.py` - No changes needed (already supports the required functionality)
- `backend/src/agent/agent.py` - No changes needed

## Notes
- The `analyze_patient_medications` tool already accepts `additional_drugs` parameter and properly resolves drug names
- The `search_pubmed` tool already accepts `num_articles` parameter (default: 5, max: 20)
- All changes are prompt-based; no code logic changes required
