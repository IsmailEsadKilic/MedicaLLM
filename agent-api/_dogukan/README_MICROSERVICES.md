# 🏗️ Microservices Architecture - Quick Start

## 📊 Architecture Overview

```
┌─────────────────┐
│   Frontend      │  Port 3000
│   (Next.js)     │
└────────┬────────┘
         │ HTTP API
         │
┌────────▼────────┐
│   Backend API   │  Port 5000
│   (Express.js)  │
└────────┬────────┘
         │ AWS SDK
         │
┌────────▼────────┐
│   DynamoDB      │  Port 8000
│   (Docker)      │
└─────────────────┘
```

## 🚀 Quick Start

### Method 1: Docker Compose (Recommended)

**Start only the database:**
```bash
docker-compose -f docker-compose.dev.yml up -d
```

**Start Backend and Frontend manually:**
```bash
# Terminal 1: Backend
cd medicallm-backend
npm run dev

# Terminal 2: Frontend
cd medicallm-frontend
npm run dev
```

### Method 2: Manual (Development)

**1. Database:**
```bash
docker run -d -p 8000:8000 --name dynamodb-local amazon/dynamodb-local
```

**2. Backend:**
```bash
cd medicallm-backend
npm run dev
```

**3. Frontend:**
```bash
cd medicallm-frontend
npm run dev
```

## 🎯 Microservices Principles

### ✅ Correct: Database per Service

- Each service has its own database
- Backend manages the database
- Frontend does not directly access the database

### ❌ Wrong: Shared Database

- All services should not use the same database
- This is an anti-pattern

## 📝 Environment Variables

### Backend (`medicallm-backend/.env`)
```env
PORT=5000
NODE_ENV=development
FRONTEND_URL=http://localhost:3000
USE_LOCAL_DYNAMODB=true
DYNAMODB_LOCAL_ENDPOINT=http://localhost:8000
USERS_TABLE=medicallm-users
```

### Frontend (`medicallm-frontend/.env.local`)
```env
NEXT_PUBLIC_API_URL=http://localhost:5000
AUTH_SECRET=your-secret
```

## 🔄 In Production

**Use AWS DynamoDB:**
```env
AWS_REGION=us-east-1
# Automatic authentication via IAM role
```

## 📚 More Information

See `MICROSERVICES_ARCHITECTURE.md` file.
