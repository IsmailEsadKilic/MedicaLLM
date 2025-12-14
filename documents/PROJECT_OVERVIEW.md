# MedicaLLM - Full Stack AWS CDK Project

## Project Description
MedicaLLM is a full-stack medical chatbot application built with React frontend, Express.js backend, and AWS infrastructure using CDK.

## Tech Stack

### Frontend
- **Framework**: React 18.2.0
- **Build Tool**: Vite 5.0.0
- **Styling**: Custom CSS with dark/light theme support
- **Port**: 5173 (default Vite dev server)

### Backend
- **Runtime**: Node.js with TypeScript
- **Framework**: Express.js 4.18.2
- **Database**: AWS DynamoDB (Local for development)
- **Authentication**: JWT + bcrypt
- **Port**: 3001

### Infrastructure (Planned)
- **IaC**: AWS CDK
- **Cloud Provider**: AWS

## Project Structure
```
grad_project/
├── frontend/          # React application
├── backend/           # Express.js API
├── cdk/              # AWS CDK infrastructure (coming next)
└── documents/        # Project documentation
```

## Current Status
✅ Frontend UI completed with chat interface
✅ Backend API with authentication system
✅ DynamoDB integration (local)
⏳ Frontend-Backend integration (pending)
⏳ AWS CDK deployment (pending)
⏳ LLM integration (pending)

## Quick Start

### Prerequisites
- Node.js 18+
- Docker (for DynamoDB Local)
- npm or yarn

### Setup Instructions

1. **Backend Setup**
```bash
cd backend
npm install
docker-compose up -d  # Start DynamoDB Local
npm run db:setup-users  # Create Users table
npm run dev
```

2. **Frontend Setup**
```bash
cd frontend
npm install
npm run dev
```

## Documentation Files
- [BACKEND.md](./BACKEND.md) - Backend architecture and API documentation
- [FRONTEND.md](./FRONTEND.md) - Frontend structure and components
- [AUTHENTICATION.md](./AUTHENTICATION.md) - Authentication system details
- [DATABASE.md](./DATABASE.md) - Database schema and setup
