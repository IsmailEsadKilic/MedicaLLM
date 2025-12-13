# Drug Information AI Agent Setup

## 🎯 Overview
AI agent with 2 action groups that query DynamoDB tables:
1. **get_drug_info** - Query Drugs table (17,430 drugs + 34,222 synonyms)
2. **check_drug_interaction** - Query DrugInteractions table (2.8M interactions)

## 🗄️ Database Tables

### Table 1: Drugs
- **Items**: 51,652 (17,430 drugs + 34,222 synonyms)
- **Structure**: 
  - Main: `PK: DRUG#Warfarin, SK: META`
  - Synonym: `PK: DRUG#Coumadin, SK: SYNONYM, points_to: Warfarin`
- **Fields**: name, drug_id, indication, mechanism_of_action, pharmacodynamics, toxicity, metabolism, absorption, half_life, protein_binding, groups, categories

### Table 2: DrugInteractions
- **Items**: 2,855,848 interactions
- **Structure**: `PK: DRUG#Warfarin, SK: INTERACTS#Ibuprofen`
- **Fields**: drug1_name, drug2_name, description

## 🔧 Backend API

### Endpoints

#### 1. Get Drug Info
```
GET /api/drugs/info/:drugName
```
Example: `/api/drugs/info/Warfarin`

#### 2. Check Interaction
```
GET /api/drugs/interaction/:drug1/:drug2
```
Example: `/api/drugs/interaction/Warfarin/Ibuprofen`

#### 3. AI Agent Query
```
POST /api/drugs/query
Body: { "query": "What is Warfarin used for?" }
```

## 🤖 AI Agent Flow

1. **User Query** → Frontend sends to `/api/drugs/query`
2. **LLM Decision** → Ollama (gemma2:27b) decides which tool to use
3. **Tool Execution** → Query DynamoDB (Drugs or DrugInteractions table)
4. **LLM Response** → Generate natural language answer
5. **Return to User** → Display in chat interface

## 🚀 Running the System

### 1. Start DynamoDB Local
```bash
docker-compose up -d
```

### 2. Start Ollama
```bash
ollama serve
ollama pull gemma2:27b
```

### 3. Start Backend
```bash
cd backend
npm install
npm run dev
```

### 4. Start Frontend
```bash
cd frontend
npm install
npm run dev
```

## 📝 Example Queries

- "What is Warfarin used for?"
- "Do Warfarin and Ibuprofen interact?"
- "Tell me about Aspirin"
- "What are the side effects of Metformin?"
- "Can I take Lisinopril with Potassium?"

## 🔍 How It Works

### Query: "Do Warfarin and Ibuprofen interact?"

1. **LLM analyzes** → Decides to use `check_drug_interaction` tool
2. **Tool executes** → Queries DrugInteractions table
3. **Result**: 
```json
{
  "interaction_found": true,
  "drug1": "Warfarin",
  "drug2": "Ibuprofen",
  "description": "Ibuprofen may decrease the excretion rate of Warfarin..."
}
```
4. **LLM generates** → "Yes, Warfarin and Ibuprofen do interact. Ibuprofen may decrease the excretion rate of Warfarin, which could result in higher serum levels. This interaction could increase the risk of bleeding. Consult your doctor before taking these medications together."

## 📊 Performance

- **Drug lookup**: ~2-5ms
- **Interaction check**: ~2-5ms
- **LLM processing**: ~2-5 seconds (depends on model)
- **Total response time**: ~2-5 seconds

## 🔐 Authentication

All endpoints require JWT token in Authorization header:
```
Authorization: Bearer <token>
```

## 🎨 Frontend Features

- Real-time chat interface
- Multiple chat sessions
- Dark/Light theme
- Typing indicators
- Suggested queries
- User authentication
