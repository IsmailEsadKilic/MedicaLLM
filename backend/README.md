# Backend - API Proxy Server

This backend now acts as a lightweight proxy that delegates all AI, conversation, and drug-related logic to the **Agent API Server** (agent-api).

## Architecture

```
Frontend → Backend (Auth + Proxy) → Agent API (AI + RAG + Data)
```

### Responsibilities

**Backend (this service):**
- User authentication (JWT)
- Request validation
- Proxying requests to Agent API
- User ownership verification

**Agent API:**
- LLM integration (Ollama)
- RAG (Vector Store)
- Drug information retrieval
- Conversation management in DynamoDB
- Message history

## Setup

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment:**
   Copy `.env.example` to `.env` and update:
   ```env
   PORT=3001
   AGENT_API_URL=http://localhost:2580
   JWT_SECRET=your-secret-key
   ```

3. **Start the server:**
   ```bash
   npm run dev
   ```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login user

### Conversations (Protected)
All conversation endpoints require JWT authentication.

- `GET /api/conversations` - Get all user conversations
- `POST /api/conversations` - Create new conversation
- `GET /api/conversations/:chatId` - Get specific conversation
- `PATCH /api/conversations/:chatId/title` - Update conversation title
- `DELETE /api/conversations/:chatId` - Delete conversation

### Drugs/Queries (Protected)
- `POST /api/drugs/query` - Query the medical agent
  ```json
  {
    "conversation_id": "uuid",
    "query": "What are the side effects of aspirin?"
  }
  ```
- `POST /api/drugs/generate-title` - Generate conversation title

### Health Check
- `GET /api/health` - Check server status

## Services

### Agent API Service (`src/services/agentApiService.ts`)
Handles all communication with the Agent API server:
- `createConversation(userId, title)` - Create conversation
- `getUserConversations(userId)` - Get user's conversations
- `getConversation(conversationId)` - Get single conversation
- `updateConversationTitle(conversationId, title)` - Update title
- `deleteConversation(conversationId)` - Delete conversation
- `queryAgent(conversationId, query)` - Query medical agent

## Development

```bash
# Development mode with auto-reload
npm run dev

# Build TypeScript
npm run build

# Production mode
npm start
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Backend server port | `3001` |
| `AGENT_API_URL` | Agent API server URL | `http://localhost:2580` |
| `JWT_SECRET` | Secret for JWT tokens | Required |
| `DYNAMODB_ENDPOINT` | DynamoDB endpoint (for auth) | `http://localhost:8000` |
| `AWS_REGION` | AWS region | `us-east-1` |

## Dependencies

- **express** - Web framework
- **axios** - HTTP client for Agent API
- **jsonwebtoken** - JWT authentication
- **bcrypt** - Password hashing
- **@aws-sdk/client-dynamodb** - DynamoDB client for user auth

## Removed Services

The following services are no longer needed as they're handled by the Agent API:
- ~~`aiService.ts`~~ - LLM integration
- ~~`drugService.ts`~~ - Drug information
- ~~`conversationService.ts`~~ - Conversation management
- ~~`titleService.ts`~~ - Title generation

## Testing

Ensure both services are running:

1. **Agent API** (port 2580):
   ```bash
   cd agent-api
   python api_server.py
   ```

2. **Backend** (port 3001):
   ```bash
   cd backend
   npm run dev
   ```

3. **Frontend** (port 3000):
   ```bash
   cd frontend
   npm run dev
   ```

Then test:
```bash
# Health check
curl http://localhost:3001/api/health

# Should show agent API URL
```
