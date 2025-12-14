# Drug Information AI Agent - Project Summary

## 🎯 What We Built

A full-stack AI-powered drug information system with:
- **17,430 drugs** with detailed clinical information
- **34,222 drug synonyms** for flexible search
- **2,855,848 drug-drug interactions**
- AI agent with tool calling (Ollama + gemma2:27b)
- Real-time chat interface with conversation memory

---

## 📊 Database Architecture

### 1. Drugs Table (51,652 items)
**Structure:**
```
Main Drug:
  PK: DRUG#Warfarin
  SK: META
  
Synonym:
  PK: DRUG#Coumadin
  SK: SYNONYM
  points_to: Warfarin
```

**Fields Loaded (19/45):**
- Basic: drug_id, name, description, cas_number, unii, state
- Clinical: indication, pharmacodynamics, mechanism_of_action, toxicity, metabolism, absorption, half_life, protein_binding, route_of_elimination
- Classification: groups, categories
- Synonyms: 34,222 alternative names

**Query Performance:** 2-5ms

### 2. DrugInteractions Table (2,855,848 items)
**Structure:**
```
PK: DRUG#Warfarin
SK: INTERACTS#Ibuprofen
GSI_PK: DRUG#Ibuprofen (for reverse lookup)
GSI_SK: INTERACTS#Warfarin
```

**Fields:**
- drug1_id, drug1_name
- drug2_id, drug2_name
- description (interaction details)

**Query Performance:** 2-5ms

### 3. Conversations Table (Designed, not yet implemented)
**Structure:**
```
PK: USER#<user_id>
SK: CHAT#<timestamp>#<chat_id>
```

**Fields:**
- chat_id, user_id, title
- messages[] (array of user/assistant messages)
- created_at, updated_at

---

## 🤖 AI Agent Architecture

### Tools (2 Action Groups)

**1. get_drug_info**
- Queries: Drugs table
- Returns: Full drug information
- Use case: "What is Warfarin?"

**2. check_drug_interaction**
- Queries: DrugInteractions table
- Returns: Interaction details or "no interaction"
- Use case: "Do Warfarin and Ibuprofen interact?"

### Agent Flow
```
User Query
    ↓
LLM (gemma2:27b) - Decides which tool to use
    ↓
Tool Execution - Query DynamoDB
    ↓
LLM - Generate natural language response
    ↓
Return to User
```

### Features
- **Conversation Memory**: Sends full chat history for context
- **Tool Transparency**: Debug button shows which tool was used and raw data
- **Parallel Title Generation**: Auto-generates chat titles in background
- **Markdown Rendering**: Properly formatted responses with bold, bullets, etc.

---

## 🏗️ Tech Stack

### Backend (TypeScript + Express)
**Location:** `/backend/src/`

**Services:**
- `drugService.ts` - Query Drugs & DrugInteractions tables
- `aiService.ts` - Ollama integration with tool calling
- `titleService.ts` - Auto-generate conversation titles

**Routes:**
- `GET /api/drugs/info/:drugName` - Get drug info
- `GET /api/drugs/interaction/:drug1/:drug2` - Check interaction
- `POST /api/drugs/query` - AI agent query
- `POST /api/drugs/generate-title` - Generate chat title

**Dependencies:**
- `@aws-sdk/client-dynamodb` - DynamoDB client
- `axios` - HTTP requests to Ollama
- `express` - Web framework
- `cors` - CORS support

### Frontend (React + Vite)
**Location:** `/frontend/src/`

**Components:**
- `pages/Chat.jsx` - Main chat interface
- `pages/Login.jsx` - Authentication
- `pages/Register.jsx` - User registration

**Features:**
- Multiple chat sessions
- Dark/Light theme
- Markdown rendering (react-markdown)
- Debug info panel
- Conversation memory
- Auto-generated titles

**Port:** 3000 (configured in vite.config.js)

### Database (DynamoDB Local)
**Port:** 8000
**Tables:** Drugs, DrugInteractions, Users
**Docker:** `docker-compose.yml`

### AI Model (Ollama)
**Model:** gemma2:27b
**Port:** 11434
**Note:** Use 127.0.0.1 instead of localhost (IPv6 issue)

---

## 📁 Project Structure

```
grad_project/
├── backend/
│   ├── src/
│   │   ├── services/
│   │   │   ├── drugService.ts      # DynamoDB queries
│   │   │   ├── aiService.ts        # Ollama integration
│   │   │   └── titleService.ts     # Title generation
│   │   ├── routes/
│   │   │   ├── drugs.ts            # Drug API endpoints
│   │   │   └── auth.ts             # Authentication
│   │   └── index.ts                # Express app
│   └── package.json
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Chat.jsx            # Main chat UI
│   │   │   ├── Login.jsx
│   │   │   └── Register.jsx
│   │   ├── App.jsx                 # (not used, using pages/Chat.jsx)
│   │   └── main.jsx                # Entry point
│   └── package.json
├── drugbank_data/
│   └── full database 2.xml         # Source data (17,430 drugs)
├── load_drugs_table.py             # Load Drugs table
├── load_to_dynamodb.py             # Load DrugInteractions table
├── docker-compose.yml              # DynamoDB Local
├── CONVERSATIONS_DB_DESIGN.md      # Conversations table design
├── drug_fields_summary.md          # Available drug fields
└── AGENT_SETUP.md                  # Setup instructions
```

---

## 🚀 How to Run

### 1. Start DynamoDB Local
```bash
docker-compose up -d
```

### 2. Load Data (One-time)
```bash
# Load drugs (17,430 drugs + 34,222 synonyms)
python3 load_drugs_table.py

# Load interactions (2,855,848 interactions)
python3 load_to_dynamodb.py
```

### 3. Start Ollama
```bash
ollama serve
ollama pull gemma2:27b
```

### 4. Start Backend
```bash
cd backend
npm install
npm run dev
```
**Runs on:** http://localhost:3001

### 5. Start Frontend
```bash
cd frontend
npm install
npm run dev
```
**Runs on:** http://localhost:3000

### 6. Access Application
- **Main App:** http://localhost:3000/chat
- **Login:** http://localhost:3000/login
- **Test Page:** http://localhost:3000/test.html

---

## 🎨 Features Implemented

### ✅ Database
- [x] Drugs table with 17,430 drugs
- [x] 34,222 synonyms for flexible search
- [x] 2,855,848 drug interactions
- [x] Fast queries (2-5ms)
- [x] Bidirectional interaction lookup

### ✅ AI Agent
- [x] Tool calling with 2 action groups
- [x] Ollama integration (gemma2:27b)
- [x] Conversation memory
- [x] Parallel title generation
- [x] Debug info panel

### ✅ Frontend
- [x] Real-time chat interface
- [x] Multiple chat sessions
- [x] Dark/Light theme
- [x] Markdown rendering
- [x] User authentication
- [x] Responsive design

### ✅ Backend
- [x] RESTful API
- [x] DynamoDB integration
- [x] JWT authentication
- [x] CORS support
- [x] Error handling

---

## 🐛 Issues Fixed

### 1. IPv6 Connection Issue
**Problem:** `ECONNREFUSED ::1:11434`
**Solution:** Changed `localhost` to `127.0.0.1` in aiService.ts

### 2. Browser Cache Issue
**Problem:** Frontend showing old demo code
**Solution:** 
- Cleared Vite cache
- Updated pages/Chat.jsx (not App.jsx)
- Hard refresh browser

### 3. Fetch Failed Error
**Problem:** Node.js fetch not working
**Solution:** Switched from fetch to axios

### 4. Duplicate Keys in Batch Write
**Problem:** Synonyms creating duplicate entries
**Solution:** Added deduplication logic before batch write

---

## 📈 Performance Metrics

- **Drug Lookup:** 2-5ms
- **Interaction Check:** 2-5ms
- **LLM Response:** 2-5 seconds
- **Total Response Time:** ~2-5 seconds
- **Database Size:** 
  - Drugs: 51,652 items
  - Interactions: 2,855,848 items

---

## 🔮 Future Enhancements

### Database
- [ ] Implement Conversations table
- [ ] Add remaining 26 drug fields (volume-of-distribution, clearance, etc.)
- [ ] Add food-interactions
- [ ] Add pharmacogenomics data

### Features
- [ ] Persist conversations to database
- [ ] Search/filter chat history
- [ ] Export chat as PDF
- [ ] Voice input
- [ ] Multi-drug interaction check (3+ drugs)
- [ ] Drug recommendations
- [ ] Dosage calculator

### AI Agent
- [ ] Add more tools (food interactions, dosage info)
- [ ] Improve context window management
- [ ] Add streaming responses
- [ ] Multi-language support

---

## 📝 API Endpoints

### Drug Information
```
GET  /api/drugs/info/:drugName
GET  /api/drugs/interaction/:drug1/:drug2
POST /api/drugs/query
POST /api/drugs/generate-title
```

### Authentication
```
POST /api/auth/register
POST /api/auth/login
```

---

## 🔑 Key Learnings

1. **DynamoDB Design:** PK/SK pattern enables flexible queries
2. **Synonym Handling:** Separate entries pointing to main drug
3. **Tool Calling:** LLM decides which tool to use based on query
4. **Conversation Memory:** Send full history for context
5. **Parallel Processing:** Generate title while processing main query
6. **IPv6 Issues:** Use 127.0.0.1 instead of localhost
7. **Browser Caching:** Clear Vite cache and use hard refresh

---

## 📚 Documentation Files

- `PROJECT_SUMMARY.md` - This file
- `AGENT_SETUP.md` - Setup instructions
- `CONVERSATIONS_DB_DESIGN.md` - Conversations table design
- `drug_fields_summary.md` - Available drug fields (45 total, 19 loaded)
- `README.md` - Project overview

---

## 🎯 Success Metrics

✅ **Database:** 3M+ items loaded successfully
✅ **Performance:** Sub-5ms queries
✅ **AI Agent:** Working with 2 tools
✅ **Frontend:** Full chat interface with memory
✅ **Backend:** RESTful API with authentication
✅ **Integration:** All components connected and working

---

**Project Status:** ✅ Fully Functional
**Last Updated:** December 2024
