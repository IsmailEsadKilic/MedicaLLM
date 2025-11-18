# 🏥 MedicaLLM

AI-powered chat application for medical questions.

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Requirements](#-requirements)
- [Installation](#-installation)
- [Usage](#-usage)
- [Troubleshooting](#-troubleshooting)
- [Documentation](#-documentation)

## ✨ Features

- 🤖 AI-powered medical Q&A
- 🔐 Secure user authentication
- 💬 Real-time chat interface
- 📱 Responsive design
- 🎨 Modern and user-friendly UI

## 🏗️ Architecture

MedicaLLM uses a microservices architecture:

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

## 📦 Requirements

- **Node.js** v18 or higher
- **npm** or **yarn**
- **Docker Desktop** (for DynamoDB)

## 🚀 Installation

### Step 1: Clone the Project

```bash
git clone <repo-url>
cd MedicaLLM
```

### Step 2: Backend Setup

```bash
cd medicallm-backend
npm install
```

**Create environment file** (`.env`):
```env
PORT=5000
NODE_ENV=development
FRONTEND_URL=http://localhost:3000
USE_LOCAL_DYNAMODB=true
DYNAMODB_LOCAL_ENDPOINT=http://localhost:8000
USERS_TABLE=medicallm-users
VERIFICATION_TABLE=medicallm-verifications
AWS_REGION=us-east-1
```

### Step 3: Frontend Setup

```bash
cd ../medicallm-frontend
npm install
```

**Create environment file** (`.env.local`):
```env
# OpenAI API Key (required for chat)
OPENAI_API_KEY=sk-your-openai-api-key

# Backend API URL
NEXT_PUBLIC_API_URL=http://localhost:5000

# NextAuth Secret (generate a secure secret)
AUTH_SECRET=your-secret-here
NEXTAUTH_URL=http://localhost:3000
```

**Generate AUTH_SECRET:**
```bash
# Linux/Mac
openssl rand -base64 32

# Windows PowerShell
[Convert]::ToBase64String((1..32 | ForEach-Object { Get-Random -Minimum 0 -Maximum 256 }))
```

### Step 4: Start the Database

**Method 1: Docker Compose (Recommended)**
```bash
# From project root directory
docker-compose -f docker-compose.dev.yml up -d
```

**Method 2: Manual Docker**
```bash
docker run -d -p 8000:8000 --name dynamodb-local amazon/dynamodb-local
```

### Step 5: Start Services

**Open 3 separate terminals:**

**Terminal 1 - Database (if you didn't use Docker Compose):**
```bash
# Skip if already running
docker ps | grep dynamodb
```

**Terminal 2 - Backend:**
```bash
cd medicallm-backend
npm run dev
```

**Terminal 3 - Frontend:**
```bash
cd medicallm-frontend
npm run dev
```

### Step 6: Test

1. Open in browser: http://localhost:3000
2. Go to sign up page
3. Create a new account
4. You will be automatically logged in

## 💻 Usage

### Development

**Start all services:**
```bash
# 1. Database
docker-compose -f docker-compose.dev.yml up -d

# 2. Backend (new terminal)
cd medicallm-backend
npm run dev

# 3. Frontend (new terminal)
cd medicallm-frontend
npm run dev
```

**Stop services:**
```bash
# Database
docker-compose -f docker-compose.dev.yml down

# Backend and Frontend: Stop with Ctrl+C
```

### Production

For production deployment, see `DEPLOYMENT.md` file.

## 🐛 Troubleshooting

### DynamoDB Connection Error

```bash
# Check if DynamoDB is running
docker ps | grep dynamodb

# If not running, start it
docker-compose -f docker-compose.dev.yml up -d
```

### Port Already in Use Error

```bash
# Windows
netstat -ano | findstr :8000
netstat -ano | findstr :5000
netstat -ano | findstr :3000

# Linux/Mac
lsof -i :8000
lsof -i :5000
lsof -i :3000
```

### Backend Connection Error

- Make sure `NEXT_PUBLIC_API_URL=http://localhost:5000` is set in frontend `.env.local`
- Check if backend is running: http://localhost:5000/health

### Module Not Found Error

```bash
# Clean node_modules in both directories
cd medicallm-backend
rm -rf node_modules package-lock.json
npm install

cd ../medicallm-frontend
rm -rf node_modules package-lock.json
npm install
```

## 📚 Documentation

- [Microservices Architecture](./MICROSERVICES_ARCHITECTURE.md) - Detailed architecture explanation
- [Quick Start](./README_MICROSERVICES.md) - Microservices quick start
- [Backend API](./medicallm-backend/README.md) - Backend API documentation
- [Frontend](./medicallm-frontend/README.md) - Frontend documentation

## 🔍 Checklist

- [ ] Node.js installed (`node --version`)
- [ ] Docker installed and running (`docker ps`)
- [ ] Backend `.env` file created
- [ ] Frontend `.env.local` file created
- [ ] DynamoDB running (port 8000)
- [ ] Backend running (port 5000)
- [ ] Frontend running (port 3000)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is under a private license.

## 📞 Contact

You can open an issue for questions.

---

**MedicaLLM** - AI-powered solution for your medical questions 🏥
