# 🏗️ Microservices Architecture - Database Strategy

## 📊 Current Architecture

```
┌─────────────────┐
│   Frontend      │
│   Next.js       │
│   Port: 3000    │
└────────┬────────┘
         │ HTTP
         │
┌────────▼────────┐
│   Backend API   │
│   Express.js    │
│   Port: 5000    │
└────────┬────────┘
         │ AWS SDK
         │
┌────────▼────────┐
│   DynamoDB      │
│   Local/Cloud   │
│   Port: 8000    │
└─────────────────┘
```

## 🎯 Microservices Principles

### ✅ Correct Approach: Database per Service

**Each service should have its own database:**

```
┌─────────────────┐
│   Frontend      │
│   (Next.js)     │
└────────┬────────┘
         │
         │ API Calls
         │
┌────────▼────────┐      ┌─────────────────┐
│   Backend API   │──────▶│   DynamoDB      │
│   (Express.js)  │      │   (Owned by      │
│                 │      │    Backend)      │
└─────────────────┘      └─────────────────┘
```

**Advantages:**
- ✅ Services are independent (loose coupling)
- ✅ Each service manages its own database
- ✅ Scalability
- ✅ Technology independence

### ❌ Wrong Approach: Shared Database

**All services should not use the same database:**

```
┌─────────┐  ┌─────────┐  ┌─────────┐
│Service1│  │Service2│  │Service3│
└───┬─────┘  └───┬─────┘  └───┬─────┘
    │           │           │
    └───────────┼───────────┘
                │
         ┌──────▼──────┐
         │  Database  │  ❌ Anti-pattern!
         └────────────┘
```

**Disadvantages:**
- ❌ Services are dependent on each other
- ❌ Scaling difficulties
- ❌ Technology lock-in

## 🐳 Management with Docker Compose

### Development Environment

Start all services with a single command:

```bash
docker-compose up
```

**Services:**
1. **DynamoDB Local** - Database (Port 8000)
2. **Backend API** - Express.js (Port 5000)
3. **Frontend** - Next.js (Port 3000) - Optional

### Running Services Separately

**Database only:**
```bash
docker-compose up dynamodb
```

**Backend + Database:**
```bash
docker-compose up dynamodb backend
```

**All services:**
```bash
docker-compose up
```

## 📦 Database Location

### Development (Local)

**Docker Container:**
```yaml
dynamodb:
  image: amazon/dynamodb-local
  ports:
    - "8000:8000"
```

**Backend connection:**
```env
DYNAMODB_LOCAL_ENDPOINT=http://dynamodb:8000
```

### Production (Cloud)

**AWS DynamoDB (Managed Service):**
```env
AWS_REGION=us-east-1
# AWS credentials via IAM role
```

**Advantages:**
- ✅ Automatic scaling
- ✅ High availability
- ✅ Backup
- ✅ Security

## 🔄 Database Access Strategy

### Backend Service Manages the Database

```
Frontend → Backend API → DynamoDB
```

**Why?**
- ✅ Security (database not exposed to frontend)
- ✅ Business logic in backend
- ✅ Data validation in backend
- ✅ API layer (RESTful)

### Frontend Does Not Directly Access Database

```
Frontend → DynamoDB  ❌ WRONG!
```

**Why is it wrong?**
- ❌ Security risk (credentials in frontend)
- ❌ CORS issues
- ❌ Scattered business logic

## 🎯 Recommended Architecture

### Development

```bash
# Terminal 1: Database
docker-compose up dynamodb

# Terminal 2: Backend
cd medicallm-backend
npm run dev

# Terminal 3: Frontend
cd medicallm-frontend
npm run dev
```

### Production

```
┌─────────────────┐
│   Vercel/       │
│   Frontend      │
└────────┬────────┘
         │ HTTPS
         │
┌────────▼────────┐
│   AWS/          │
│   Backend API   │
└────────┬────────┘
         │ AWS SDK
         │
┌────────▼────────┐
│   AWS DynamoDB  │
│   (Managed)     │
└─────────────────┘
```

## 📝 Environment Variables

### Backend (.env)
```env
# Development
DYNAMODB_LOCAL_ENDPOINT=http://dynamodb:8000
USE_LOCAL_DYNAMODB=true

# Production
AWS_REGION=us-east-1
# Use IAM role (no credentials needed)
```

### Frontend (.env.local)
```env
NEXT_PUBLIC_API_URL=http://localhost:5000
```

## 🚀 Quick Start

### With Docker Compose (Recommended)

```bash
# Start all services
docker-compose up

# Database only
docker-compose up dynamodb

# Run in background
docker-compose up -d

# Stop
docker-compose down
```

### Manual (Development)

```bash
# 1. Database
docker run -d -p 8000:8000 --name dynamodb-local amazon/dynamodb-local

# 2. Backend
cd medicallm-backend
npm run dev

# 3. Frontend
cd medicallm-frontend
npm run dev
```

## ✅ Best Practices

1. **Database per Service** - Each service has its own database
2. **Backend owns Database** - Frontend does not directly access database
3. **Docker Compose** - Manage all services for development
4. **Managed Services** - Use managed services like AWS DynamoDB in production
5. **Environment Variables** - Separate config for each environment
6. **Health Checks** - Monitor service health

## 📚 Resources

- [Microservices Patterns](https://microservices.io/patterns/data/database-per-service.html)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [AWS DynamoDB Best Practices](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/best-practices.html)
