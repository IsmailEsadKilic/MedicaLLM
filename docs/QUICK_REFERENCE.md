# MedicaLLM Agent - Quick Reference Card

## 🛠️ Available Tools

| Tool | Purpose | Key Parameters |
|------|---------|----------------|
| `get_drug_info` | Get drug information | `drug_name`, `detail` (low/moderate/high) |
| `check_drug_interactions` | Check drug-drug interactions | `drug_names` (list of 2+) |
| `check_drug_food_interaction` | Check drug-food interactions | `drug_name`, `food_items` (optional) |
| `search_drugs_by_indication` | Find drugs for condition | `condition` |
| `search_drugs_by_category` | Find drugs in category | `category` |
| `recommend_alternative_drug` | Find safe alternatives | `current_drug_names`, `for_drug_name` |
| `analyze_patient_medications` | Analyze patient meds | `additional_drugs` (optional) |

## 🎯 Quick Usage Examples

### Get Drug Info
```python
# Basic info
get_drug_info.invoke({"drug_name": "Aspirin", "detail": "low"})

# Clinical info
get_drug_info.invoke({"drug_name": "Warfarin", "detail": "moderate"})

# Comprehensive
get_drug_info.invoke({"drug_name": "Metformin", "detail": "high"})
```

### Check Interactions
```python
check_drug_interactions.invoke({
    "drug_names": ["Warfarin", "Aspirin", "Ibuprofen"]
})
```

### Check Food Interactions
```python
check_drug_food_interaction.invoke({
    "drug_name": "Warfarin",
    "food_items": ["grapefruit"]
})
```

### Search by Indication
```python
search_drugs_by_indication.invoke({
    "condition": "hypertension"
})
```

### Search by Category
```python
search_drugs_by_category.invoke({
    "category": "antibiotic"
})
```

### Recommend Alternative
```python
recommend_alternative_drug.invoke({
    "current_drug_names": ["Aspirin", "Lisinopril"],
    "for_drug_name": "Warfarin"
})
```

### Analyze Patient
```python
# Set patient context first
set_current_patient_id("P-12345")

# Analyze
analyze_patient_medications.invoke({
    "additional_drugs": ["Aspirin"]
})
```

## 🎨 Severity Indicators

| Icon | Severity | Score Range |
|------|----------|-------------|
| 🔴 | MAJOR | ≥ 0.8 |
| 🟠 | MODERATE | 0.5 - 0.79 |
| 🟡 | MINOR | < 0.5 |
| ⚠️ | UNKNOWN | N/A |
| ✅ | SAFE | No interaction |

## 🔧 Context Variables

```python
# User context
set_current_user_id(user_id)
get_current_user_id()

# Patient context
set_current_patient_id(patient_id)
get_current_patient_id()

# Request context
set_request_id(request_id)
```

## 📝 Response Format

### Drug Information
```
**Drug Name** (DrugBank ID)
Also known as: synonym1, synonym2
Type: small molecule
Status: approved

Description: ...
Indication: ...
Mechanism of Action: ...
```

### Interactions
```
Found 2 interaction(s):

1. 🔴 **Warfarin** + **Aspirin** [MAJOR]
   Increased risk of bleeding...

2. 🟠 **Warfarin** + **Ibuprofen** [MODERATE]
   May increase anticoagulant effect...
```

### Patient Analysis
```
**Medication Safety Analysis for Patient P-12345**

Current Medications (3):
  - Warfarin (DB00682)
  - Aspirin (DB00945)
  - Lisinopril (DB00722)

⚠️ Found 1 interaction(s):

1. 🔴 **Warfarin** + **Aspirin** [MAJOR]
   Increased risk of bleeding...

**Safe Alternatives** (2):
  - Replace **Aspirin** with **Clopidogrel**
    Reason: Same therapeutic purpose, no interaction
```

## 🚀 System Prompt Structure

```
[CORE SYSTEM PROMPT]
├── Core Principles
├── Tool Documentation
├── Response Guidelines
├── Formatting Rules
├── Safety Reminders
└── Conversation Style

[ROLE-SPECIFIC PROMPT]
├── Healthcare Professional (if is_doctor=True)
└── General User (if is_doctor=False)

[PATIENT CONTEXT] (if patient provided)
├── Patient Demographics
├── Chronic Conditions
├── Current Medications
├── Known Allergies
└── Patient Context Rules
```

## 🎭 Role Modes

### Healthcare Professional
- Clinical terminology
- Detailed pharmacology
- Evidence-based approach
- Assumes medical knowledge

### General User
- Plain language
- Explain technical terms
- Safety-focused
- Clear disclaimers

## 🔍 Drug Name Resolution

Automatically resolves:
- ✅ Generic names (Aspirin, Warfarin)
- ✅ Brand names (Tylenol, Coumadin)
- ✅ Synonyms (Acetaminophen, Paracetamol)
- ✅ Product names (Various commercial names)

Uses fuzzy matching with similarity > 0.3

## ⚠️ Error Handling

| Error Type | Response |
|------------|----------|
| Drug not found | "Drug not found: [name]. Try different spelling." |
| Insufficient data | "No data available for [query]." |
| Service error | "Error: [generic message]" + log details |
| Missing context | "No patient context available." |

## 📊 Debug & Source Info

```python
# Get sources
sources = get_last_search_sources(request_id="...")
# Returns: [{"ref": "REF1", "title": "...", "pmid": "...", ...}]

# Get debug info
debug = get_last_tool_debug(request_id="...")
# Returns: {"cache_hit": False, "articles_fetched": 5, ...}
```

## 🧪 Testing

```bash
# Run test script
python -m backend.test_agent_tools

# Test specific tool
python -c "from backend.src.agent.tools import get_drug_info; print(get_drug_info.invoke({'drug_name': 'Aspirin', 'detail': 'low'}))"
```

## 📚 Documentation Files

| File | Purpose |
|------|---------|
| `AGENT_OVERHAUL_SUMMARY.md` | Complete overview of changes |
| `AGENT_TOOLS_DOCUMENTATION.md` | Comprehensive tool reference |
| `SYSTEM_PROMPT_GUIDE.md` | System prompt documentation |
| `CHANGES_SUMMARY.md` | Quick changes summary |
| `QUICK_REFERENCE.md` | This file |

## 🔗 Key Files

| File | Purpose |
|------|---------|
| `backend/src/agent/tools.py` | Tool implementations |
| `backend/src/agent/langchain_agent.py` | System prompt & agent creation |
| `backend/src/agent/agent.py` | Agent wrapper |
| `backend/src/session/session.py` | Session management |
| `backend/src/session/router.py` | API endpoints |

## 💡 Best Practices

1. **Always resolve drug names** before calling service methods
2. **Set patient context** before using analyze_patient_medications
3. **Use appropriate detail level** for get_drug_info
4. **Chain tools** when needed (interaction → alternative)
5. **Include disclaimers** in responses
6. **Format responses** with headers and indicators
7. **Handle errors gracefully** with user-friendly messages
8. **Log errors** for debugging

## 🎯 Common Patterns

### Check Interaction → Recommend Alternative
```python
# 1. Check interaction
interactions = check_drug_interactions.invoke({
    "drug_names": ["Warfarin", "Aspirin"]
})

# 2. If high severity, recommend alternative
if "MAJOR" in interactions:
    alternatives = recommend_alternative_drug.invoke({
        "current_drug_names": ["Warfarin"],
        "for_drug_name": "Aspirin"
    })
```

### Get Drug Info → Check Food Interactions
```python
# 1. Get drug info
info = get_drug_info.invoke({
    "drug_name": "Warfarin",
    "detail": "moderate"
})

# 2. Check food interactions
food_interactions = check_drug_food_interaction.invoke({
    "drug_name": "Warfarin"
})
```

### Search → Get Details
```python
# 1. Search by indication
drugs = search_drugs_by_indication.invoke({
    "condition": "hypertension"
})

# 2. Get details for specific drug
details = get_drug_info.invoke({
    "drug_name": "Lisinopril",
    "detail": "high"
})
```

## 🚨 Important Notes

- ⚠️ Patient context required for `analyze_patient_medications`
- ⚠️ Drug name resolution may fail for very obscure drugs
- ⚠️ Severity scores are estimates, not definitive
- ⚠️ Always include healthcare provider disclaimer
- ⚠️ Never provide specific dosing recommendations

## 📞 Support

- Check documentation in `backend/` directory
- Review test script: `backend/test_agent_tools.py`
- Check logs for error details
- Verify drug service is working

---

**Last Updated:** 2026-05-02
**Version:** 2.0.0
**Status:** ✅ Production Ready
