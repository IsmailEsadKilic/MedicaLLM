# MedicaLLM Agent API

A conversational medical AI agent powered by LangChain with drug information tools and RAG capabilities.

## Features

✅ **LangChain Agent** - Automatic tool calling and conversation management  
✅ **Drug Database** - 17,430 drugs with 34,222 synonyms and 2.8M interactions  
✅ **RAG Integration** - Search medical PDF documents  
✅ **Conversation Memory** - Maintains context across messages  
✅ **Streaming Support** - Real-time response generation  
✅ **FastAPI Backend** - RESTful API with WebSocket support  

---

## Quick Start

### 1. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -r requirements.txt
```

### 2. Setup Database

```bash
# One-time setup (creates tables and loads ~3M records)
python setup_database.py

# This takes ~15 minutes and loads:
# - Conversations table
# - Drugs table (17,430 drugs + 34,222 synonyms)
# - DrugInteractions table (2,855,848 interactions)
```

### 3. Start Ollama

```bash
ollama serve
ollama pull llama2
```

### 4. Run API Server

```bash
python api_server.py
# Server starts at http://localhost:2580
```

### 5. Test It

```bash
# Health check
curl http://localhost:2580/health

# Or run the example script
python example_agent.py
```

---

## Architecture

```
┌─────────────┐
│   Frontend  │
└──────┬──────┘
       │
       ↓
┌─────────────────────────────────────┐
│     FastAPI Server (api_server.py)  │
└──────────────┬──────────────────────┘
               │
               ↓
┌──────────────────────────────────────┐
│  MedicalAgent (medical_agent.py)     │
│  - LangChain Agent                   │
│  - Tool Calling                      │
│  - Conversation Memory               │
└───┬──────────────────────────────┬───┘
    │                              │
    ↓                              ↓
┌───────────────┐          ┌──────────────┐
│   DynamoDB    │          │    Ollama    │
│  - Drugs      │          │   (LLM)      │
│  - Interacts  │          └──────────────┘
│  - Convos     │
└───────────────┘
```

---

## Available Tools

The agent has access to these tools:

### 1. `get_drug_info`
Get detailed drug information (indication, mechanism, toxicity, metabolism, etc.)

**Example:**
```
User: "What is Warfarin used for?"
Agent: [Uses get_drug_info tool]
```

### 2. `check_drug_interaction`
Check if two drugs interact with each other

**Example:**
```
User: "Can I take Warfarin with Aspirin?"
Agent: [Uses check_drug_interaction tool]
```

### 3. `search_medical_documents` (optional)
Search medical PDF documents using RAG

**Example:**
```
User: "What are the symptoms of diabetes?"
Agent: [Uses search_medical_documents tool]
```

---

## API Endpoints

### Conversations

```bash
# Create conversation
POST /api/create-conversation
{
  "user_id": "user123",
  "title": "Drug Consultation"
}

# Get all conversations
GET /api/conversations?user_id=user123

# Get single conversation
GET /api/conversation/{conversation_id}

# Update title
PATCH /api/conversation/title
{
  "conversation_id": "uuid",
  "title": "New Title"
}

# Delete conversation
DELETE /api/conversation/{conversation_id}
```

### Queries

```bash
# Query agent
POST /api/query
{
  "conversation_id": "uuid",
  "query": "What is Warfarin?"
}

# Stream query
POST /api/query-stream
{
  "conversation_id": "uuid",
  "query": "Tell me about aspirin"
}
```

---

## Project Structure

```
agent-api/
├── api_server.py           # FastAPI application
├── medical_agent.py        # LangChain agent (NEW ✨)
├── dynamodb_manager.py     # Database operations
├── models.py               # Pydantic models
├── setup_database.py       # Database setup (NEW ✨)
├── vector_store.py         # RAG/embeddings
├── pdf_processor.py        # PDF processing
├── example_agent.py        # Usage examples (NEW ✨)
├── AGENT_USAGE.md          # Detailed usage guide (NEW ✨)
├── rag_chain.py            # [DEPRECATED]
├── data/
│   ├── pdf/                # Medical PDFs for RAG
│   └── xml/
│       └── drugbank/       # DrugBank XML data
└── scripts/
    └── _DEPRECATED.md      # Old scripts (retired)
```

---

## Configuration

### Environment Variables

Create a `.env` file:

```bash
DYNAMODB_ENDPOINT=http://localhost:8000
OLLAMA_URL=http://localhost:11434
DRUGBANK_XML_PATH=data/xml/drugbank/full database 2.xml
```

### Model Selection

Edit `api_server.py`:

```python
MODEL_NAME = "llama2"  # or "gemma2", "mistral", etc.
```

---

## Python Usage

```python
from medical_agent import MedicalAgent
from dynamodb_manager import DynamoDBManager

# Initialize
db_manager = DynamoDBManager()
agent = MedicalAgent(
    db_manager=db_manager,
    ollama_model_name="llama2"
)

# Create conversation
conversation = db_manager.create_conversation(
    user_id="user123",
    title="Medical Consultation"
)

# Query
result = agent.query(
    user_input="What is Warfarin?",
    conversation=conversation
)

print(result["answer"])
print(result["tool_used"])
```

See [AGENT_USAGE.md](AGENT_USAGE.md) for detailed examples.

---

## Migration from Old Architecture

### What Changed?

❌ **Retired:**
- TypeScript backend (`backend/src/services/aiService.ts`)
- Separate database scripts (`scripts/create_conversations_table.py`, etc.)
- Old agent implementations (`scripts/agent.py`, `scripts/langchain_agent.py`)
- Manual tool calling logic

✅ **New:**
- Unified Python stack
- LangChain-based agent with automatic tool calling
- Single setup script (`setup_database.py`)
- Built-in conversation memory
- Streaming support
- Better error handling

See [scripts/_DEPRECATED.md](scripts/_DEPRECATED.md) for migration details.

---

## Development

### Run Tests

```bash
# Test database setup
python setup_database.py --check

# Test agent
python example_agent.py
```

### Add New Tools

Edit `medical_agent.py`:

```python
@tool
def my_new_tool(param: str) -> str:
    """Tool description for the LLM"""
    # Your tool logic
    return result
```

The agent will automatically discover and use your tool!

---

## Troubleshooting

### Agent not calling tools?

Some models don't support tool calling well. Try:
- `llama2` ✅
- `llama3` ✅
- `mistral` ✅
- `gemma2` ✅

### Database empty?

```bash
# Check tables
python setup_database.py --check

# Reload data
python setup_database.py --data-only
```

### Ollama not responding?

```bash
# Check Ollama
curl http://localhost:11434/api/tags

# Restart if needed
pkill ollama && ollama serve
```

---

## Documentation

- [AGENT_USAGE.md](AGENT_USAGE.md) - Comprehensive usage guide
- [scripts/_DEPRECATED.md](scripts/_DEPRECATED.md) - Migration guide
- [example_agent.py](example_agent.py) - Working examples

---

## License

MIT

---

## Credits

- **DrugBank** - Drug information database
- **LangChain** - Agent framework
- **Ollama** - Local LLM inference
- **FastAPI** - Web framework