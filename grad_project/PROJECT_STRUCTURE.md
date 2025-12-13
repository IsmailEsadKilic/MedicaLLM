# Project Structure

```
grad_project/
├── backend/                           # Backend API (TypeScript + Express)
│   ├── src/
│   │   ├── services/
│   │   │   ├── drugService.ts         # Query Drugs & DrugInteractions
│   │   │   ├── aiService.ts           # Ollama AI integration
│   │   │   ├── titleService.ts        # Auto-generate chat titles
│   │   │   └── conversationService.ts # Conversation CRUD
│   │   ├── routes/
│   │   │   ├── drugs.ts               # Drug API endpoints
│   │   │   ├── conversations.ts       # Conversation API endpoints
│   │   │   └── auth.ts                # Authentication
│   │   ├── middleware/
│   │   │   └── auth.ts                # JWT auth middleware
│   │   └── index.ts                   # Express app entry
│   └── package.json
│
├── frontend/                          # Frontend (React + Vite)
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Chat.jsx               # Main chat interface
│   │   │   ├── Login.jsx              # Login page
│   │   │   └── Register.jsx           # Registration page
│   │   ├── App.jsx                    # (Not used)
│   │   ├── App.css                    # Styles
│   │   └── main.jsx                   # Entry point
│   ├── test.html                      # API test page
│   └── package.json
│
├── scripts/                           # Python scripts
│   ├── README.md                      # Scripts documentation
│   ├── create_conversations_table.py  # Create Conversations table
│   ├── load_drugs_table.py            # Load Drugs table
│   ├── load_to_dynamodb.py            # Load DrugInteractions table
│   ├── test_*.py                      # Testing scripts
│   ├── analyze_*.py                   # Analysis scripts
│   └── agent.py                       # Standalone Python agent
│
├── drugbank_data/                     # Source data
│   ├── full database 2.xml            # DrugBank XML (1.5GB)
│   └── drugbank.xsd                   # XML schema
│
├── dynamodb-data/                     # DynamoDB persistent data
│   └── (auto-generated)               # Created by Docker
│
├── documents/                         # Documentation
│   ├── PROJECT_OVERVIEW.md
│   ├── BACKEND.md
│   ├── FRONTEND.md
│   ├── DATABASE.md
│   ├── AUTHENTICATION.md
│   ├── INTEGRATION.md
│   └── CHANGELOG.md
│
├── docker-compose.yml                 # DynamoDB + Data loader
├── README.md                          # Main README
├── PROJECT_SUMMARY.md                 # Complete project summary
├── PROJECT_STRUCTURE.md               # This file
├── AGENT_SETUP.md                     # AI agent setup guide
├── CONVERSATIONS_DB_DESIGN.md         # Conversations table design
├── DOCKER_SETUP.md                    # Docker usage guide
├── drug_fields_summary.md             # Available drug fields
├── db_ai.md                           # Database setup log
└── .gitignore
```

## Key Directories

### `/backend` - Backend API
- **Port:** 3001
- **Tech:** TypeScript, Express, DynamoDB, Ollama
- **Run:** `cd backend && npm run dev`

### `/frontend` - Frontend UI
- **Port:** 3000
- **Tech:** React, Vite, react-markdown
- **Run:** `cd frontend && npm run dev`

### `/scripts` - Database & Testing
- **Purpose:** Setup tables, load data, testing
- **Tech:** Python, boto3
- **Run:** `python3 scripts/<script_name>.py`

### `/drugbank_data` - Source Data
- **Size:** 1.5GB XML file
- **Contains:** 17,430 drugs, 2.8M interactions

### `/dynamodb-data` - Database Storage
- **Auto-created:** By Docker
- **Persistent:** Data survives restarts
- **Backup:** Copy this folder

## Quick Start

```bash
# 1. Start DynamoDB and load data (first time only)
docker-compose --profile setup up

# 2. Start Ollama
ollama serve
ollama pull gemma2:27b

# 3. Start backend
cd backend && npm run dev

# 4. Start frontend
cd frontend && npm run dev

# 5. Open browser
http://localhost:3000/chat
```

## Data Flow

```
User Input
    ↓
Frontend (React)
    ↓
Backend API (Express)
    ↓
AI Service (Ollama) → Drug Service (DynamoDB)
    ↓
Response to User
```

## Database Tables

1. **Drugs** - 51,652 items (drugs + synonyms)
2. **DrugInteractions** - 2,855,848 items
3. **Conversations** - User chat history
4. **Users** - Authentication

## Ports

- **3000** - Frontend
- **3001** - Backend
- **8000** - DynamoDB Local
- **11434** - Ollama

## Environment

- **Node.js:** v18+
- **Python:** 3.11+
- **Docker:** Required for DynamoDB
- **Ollama:** Required for AI
