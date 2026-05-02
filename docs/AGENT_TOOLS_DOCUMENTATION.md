# MedicaLLM Agent Tools Documentation

## Overview

The MedicaLLM agent has 7 specialized tools for drug information retrieval, interaction checking, and patient medication analysis. All tools automatically resolve drug names to DrugBank IDs and provide formatted, actionable responses.

## Tool Reference

### 1. get_drug_info

**Purpose:** Retrieve comprehensive drug information from the database.

**Signature:**
```python
get_drug_info(
    drug_name: str,
    detail: Literal["low", "moderate", "high"] = "moderate"
) -> str
```

**Parameters:**
- `drug_name`: Name of the drug (generic, brand, or synonym)
- `detail`: Level of detail to return
  - `"low"`: Basic information (description, indication)
  - `"moderate"`: Clinical information (mechanism, pharmacodynamics, toxicity, metabolism)
  - `"high"`: Comprehensive data (includes targets, enzymes, carriers, transporters)

**Example Usage:**
```python
# Basic info
result = get_drug_info.invoke({"drug_name": "Aspirin", "detail": "low"})

# Clinical info
result = get_drug_info.invoke({"drug_name": "Warfarin", "detail": "moderate"})

# Comprehensive info
result = get_drug_info.invoke({"drug_name": "Metformin", "detail": "high"})
```

**Use Cases:**
- "What is Warfarin?"
- "Tell me about Metformin"
- "What are the side effects of Aspirin?"
- "How does Lisinopril work?"

---

### 2. check_drug_interactions

**Purpose:** Check for interactions between multiple drugs.

**Signature:**
```python
check_drug_interactions(
    drug_names: list[str]
) -> str
```

**Parameters:**
- `drug_names`: List of 2 or more drug names to check

**Returns:**
- Formatted list of interactions with severity indicators:
  - 🔴 MAJOR (severity ≥ 0.8)
  - 🟠 MODERATE (severity ≥ 0.5)
  - 🟡 MINOR (severity < 0.5)
  - ⚠️ UNKNOWN (severity not available)

**Example Usage:**
```python
result = check_drug_interactions.invoke({
    "drug_names": ["Warfarin", "Aspirin", "Ibuprofen"]
})
```

**Use Cases:**
- "Do Warfarin and Ibuprofen interact?"
- "Check interactions between Lisinopril, Aspirin, and Metformin"
- "Are there any interactions in this drug list?"

---

### 3. check_drug_food_interaction

**Purpose:** Check for food interactions and dietary restrictions for a drug.

**Signature:**
```python
check_drug_food_interaction(
    drug_name: str,
    food_items: list[str] = []
) -> str
```

**Parameters:**
- `drug_name`: Name of the drug
- `food_items`: Optional list of specific food items to check (if empty, returns all food interactions)

**Example Usage:**
```python
# All food interactions
result = check_drug_food_interaction.invoke({
    "drug_name": "Warfarin"
})

# Specific food items
result = check_drug_food_interaction.invoke({
    "drug_name": "Warfarin",
    "food_items": ["grapefruit", "alcohol"]
})
```

**Use Cases:**
- "Can I eat grapefruit with Warfarin?"
- "Should I take Metformin with food?"
- "Are there any food restrictions for Lisinopril?"

---

### 4. search_drugs_by_indication

**Purpose:** Find drugs that treat a specific medical condition.

**Signature:**
```python
search_drugs_by_indication(
    condition: str
) -> str
```

**Parameters:**
- `condition`: Medical condition or indication (e.g., "diabetes", "hypertension", "pain")

**Returns:**
- List of up to 10 drugs with descriptions

**Example Usage:**
```python
result = search_drugs_by_indication.invoke({
    "condition": "hypertension"
})
```

**Use Cases:**
- "What drugs treat diabetes?"
- "Medications for hypertension"
- "What can be used for migraine?"

---

### 5. search_drugs_by_category

**Purpose:** Find drugs in a specific therapeutic category.

**Signature:**
```python
search_drugs_by_category(
    category: str
) -> str
```

**Parameters:**
- `category`: Therapeutic category (e.g., "antibiotic", "antidepressant", "analgesic")

**Returns:**
- List of up to 10 drugs with descriptions

**Example Usage:**
```python
result = search_drugs_by_category.invoke({
    "category": "antibiotic"
})
```

**Use Cases:**
- "List antibiotics"
- "What are some antidepressants?"
- "Show me antihypertensive drugs"

---

### 6. recommend_alternative_drug

**Purpose:** Find safe alternative drugs that don't interact with current medications.

**Signature:**
```python
recommend_alternative_drug(
    current_drug_names: list[str],
    for_drug_name: str
) -> str
```

**Parameters:**
- `current_drug_names`: List of drugs the patient is currently taking
- `for_drug_name`: The drug to find alternatives for

**Returns:**
- List of safe alternatives with reasons

**Example Usage:**
```python
result = recommend_alternative_drug.invoke({
    "current_drug_names": ["Aspirin", "Lisinopril"],
    "for_drug_name": "Warfarin"
})
```

**Use Cases:**
- "What can I use instead of Warfarin for a patient also on Aspirin?"
- "Suggest alternatives to Metformin"
- "Find a safer alternative for this patient"

---

### 7. analyze_patient_medications

**Purpose:** Perform comprehensive medication safety analysis for the current patient.

**Signature:**
```python
analyze_patient_medications(
    additional_drugs: list[str] = []
) -> str
```

**Parameters:**
- `additional_drugs`: Optional list of additional drug names to analyze along with patient's current medications

**Returns:**
- Comprehensive analysis including:
  - Current medications list
  - All drug-drug interactions (sorted by severity)
  - Safe alternatives for problematic drugs

**Context Required:**
- Patient ID must be set in context using `set_current_patient_id(patient_id)`
- Patient must exist in database with medication data

**Example Usage:**
```python
# Set patient context first
set_current_patient_id("P-12345")

# Analyze current medications
result = analyze_patient_medications.invoke({})

# Analyze with additional drugs
result = analyze_patient_medications.invoke({
    "additional_drugs": ["Aspirin", "Ibuprofen"]
})
```

**Use Cases:**
- "Analyze this patient's medications"
- "Check for interactions in the patient's drug list"
- "Can I add Aspirin to this patient's medications?"

---

## Drug Name Resolution

All tools automatically resolve drug names to DrugBank IDs using fuzzy matching. This means you can use:

- **Generic names:** "Aspirin", "Warfarin", "Metformin"
- **Brand names:** "Tylenol", "Coumadin", "Glucophage"
- **Synonyms:** "Acetaminophen", "Paracetamol"
- **Product names:** Various commercial product names

The resolution process:
1. Searches drug names, synonyms, products, and brands
2. Uses TRGM similarity matching (fuzzy search)
3. Returns best match with similarity > 0.3
4. Gracefully handles unresolved names

---

## Context Variables

### User Context
```python
set_current_user_id(user_id: str)
get_current_user_id() -> Optional[str]
```

Used for user-scoped database operations.

### Patient Context
```python
set_current_patient_id(patient_id: str | None)
get_current_patient_id() -> Optional[str]
```

Used for patient-scoped operations (required for `analyze_patient_medications`).

### Request Context
```python
set_request_id(request_id: str)
```

Used for cross-thread source and debug information propagation.

---

## Debug & Source Information

### Source Tracking

Sources are automatically tracked for tools that retrieve external data:
- PubMed searches (when implemented)
- Drug database queries

Sources are stored per request and can be retrieved:
```python
sources = get_last_search_sources(request_id="...")
```

### Debug Information

Debug information is stored for troubleshooting:
```python
debug = get_last_tool_debug(request_id="...")
```

---

## Error Handling

All tools include comprehensive error handling:

1. **Drug Not Found:**
   - Returns user-friendly message
   - Suggests trying different spelling or name

2. **Insufficient Data:**
   - Returns message indicating no data available
   - Provides context about what was searched

3. **Service Errors:**
   - Logs error details
   - Returns generic error message to user
   - Includes exception information in logs

---

## Response Formatting

All tools return well-formatted responses:

### Headers
- Use `**bold**` for drug names and important terms
- Use markdown headers for sections

### Lists
- Numbered lists for sequential items
- Bullet points for non-sequential items

### Severity Indicators
- 🔴 MAJOR - High severity interactions
- 🟠 MODERATE - Moderate severity interactions
- 🟡 MINOR - Minor severity interactions
- ✅ SAFE - No interactions detected
- ⚠️ UNKNOWN - Severity not available

### Tables
- Each row on separate line
- Clear column headers
- Aligned for readability

---

## Best Practices

### 1. Tool Selection
- Use `get_drug_info` for general drug information
- Use `check_drug_interactions` for multiple drug interaction checks
- Use `analyze_patient_medications` when patient context is available
- Chain tools when needed (e.g., check interaction → recommend alternative)

### 2. Detail Levels
- Use `"low"` for quick overviews
- Use `"moderate"` for clinical decision support
- Use `"high"` for comprehensive research

### 3. Patient Context
- Always set patient context before using `analyze_patient_medications`
- Clear patient context when switching patients
- Verify patient exists before analysis

### 4. Error Recovery
- Handle drug name resolution failures gracefully
- Provide alternative suggestions when tools fail
- Log errors for debugging

### 5. Response Interpretation
- Pay attention to severity indicators
- Note disclaimers and limitations
- Always recommend consulting healthcare providers

---

## Integration with LangChain Agent

Tools are registered with the LangChain agent in `ALL_TOOLS`:

```python
ALL_TOOLS = [
    get_drug_info,
    check_drug_interactions,
    check_drug_food_interaction,
    search_drugs_by_indication,
    search_drugs_by_category,
    recommend_alternative_drug,
    analyze_patient_medications,
]
```

The agent automatically:
- Selects appropriate tools based on user query
- Chains multiple tools when needed
- Formats responses according to system prompt
- Handles errors and retries

---

## Testing

Use the test script to verify tools work correctly:

```bash
python -m backend.test_agent_tools
```

This tests:
- Drug name resolution
- All tool functions
- Response formatting
- Error handling

---

## Future Enhancements

1. **PubMed Integration:** Add back `search_pubmed` tool for literature search
2. **Caching:** Cache drug name resolution results
3. **Metrics:** Add tool usage metrics and logging
4. **Rate Limiting:** Add tool-specific rate limiting
5. **Batch Operations:** Support batch drug lookups
6. **Advanced Filtering:** Add more filtering options for search tools
