# Scripts Directory

## Database Setup Scripts

### Core Setup (Required)
- `create_conversations_table.py` - Creates Conversations table
- `load_drugs_table.py` - Loads 17,430 drugs + 34,222 synonyms (~10 min)
- `load_to_dynamodb.py` - Loads 2,855,848 drug interactions (~5 min)

**Usage:**
```bash
# Run all at once with Docker
docker-compose --profile setup up

# Or manually
python3 scripts/create_conversations_table.py
python3 scripts/load_drugs_table.py
python3 scripts/load_to_dynamodb.py
```

---

## Testing Scripts

### Query Testing
- `test_query.py` - Test basic drug queries
- `test_common_drugs.py` - Test common drug interactions
- `test_drug_query.py` - Test drug info retrieval

**Usage:**
```bash
python3 scripts/test_query.py
python3 scripts/test_common_drugs.py
```

---

## Analysis Scripts

### Data Analysis
- `analyze_interactions.py` - Analyze interaction patterns
- `interaction_summary.py` - Generate interaction statistics
- `check_drug_fields.py` - Check available drug fields in XML
- `check_synonyms.py` - Check drug synonyms
- `fetch_single_drug.py` - Fetch detailed drug information

**Usage:**
```bash
python3 scripts/analyze_interactions.py
python3 scripts/check_synonyms.py
```

---

## AI Agent

### Standalone Agent
- `agent.py` - Standalone Python AI agent (not used in production)

**Note:** The production agent is in `backend/src/services/aiService.ts`

---

## Requirements

All scripts require:
```bash
pip install boto3
```

For AI agent:
```bash
pip install boto3 requests
```

---

## Data Source

Scripts expect:
- DynamoDB Local running on `http://localhost:8000`
- XML file at `drugbank_data/full database 2.xml`

---

## Script Organization

```
scripts/
├── README.md                          # This file
├── create_conversations_table.py      # Setup
├── load_drugs_table.py                # Setup
├── load_to_dynamodb.py                # Setup
├── test_*.py                          # Testing
├── analyze_*.py                       # Analysis
├── check_*.py                         # Analysis
├── fetch_*.py                         # Analysis
└── agent.py                           # Standalone agent
```
