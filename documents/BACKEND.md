# Backend Documentation

## Overview
Express.js backend with TypeScript, JWT authentication, and DynamoDB integration.

## Technology Stack
- **Language**: TypeScript 5.3.0
- **Framework**: Express.js 4.18.2
- **Database**: AWS DynamoDB (SDK v3)
- **Authentication**: JWT (jsonwebtoken 9.0.2) + bcrypt 5.1.1
- **Validation**: express-validator 7.0.1
- **Dev Tools**: ts-node-dev for hot reload

## Project Structure
```
backend/
├── src/
│   ├── db/
│   │   ├── dynamodb.ts       # DynamoDB client configuration
│   │   ├── setup.ts          # Items table setup
│   │   └── setupUsers.ts     # Users table setup
│   ├── middleware/
│   │   └── auth.ts           # JWT authentication middleware
│   ├── routes/
│   │   ├── auth.ts           # Authentication routes
│   │   └── items.ts          # Items CRUD routes
│   └── index.ts              # Express app entry point
├── package.json
├── tsconfig.json
├── .env
└── docker-compose.yml        # DynamoDB Local
```

## Environment Variables (.env)
```env
PORT=3001
NODE_ENV=development
DYNAMODB_ENDPOINT=http://localhost:8000
AWS_REGION=us-east-1
TABLE_NAME=Items
USERS_TABLE=Users
JWT_SECRET=your-secret-key-change-in-production
JWT_EXPIRES_IN=7d
```

## API Endpoints

### Health Check
- **GET** `/api/health`
  - Response: `{ status: 'ok', message: 'Backend is running' }`

### Authentication Routes (`/api/auth`)

#### Register User
- **POST** `/api/auth/register`
- **Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "password123",
    "name": "John Doe"
  }
  ```
- **Validation**:
  - Email must be valid
  - Password minimum 6 characters
  - Name is required
- **Response** (201):
  ```json
  {
    "token": "jwt_token_here",
    "user": {
      "userId": "user_1234567890",
      "email": "user@example.com",
      "name": "John Doe"
    }
  }
  ```
- **Errors**:
  - 400: Validation errors or user already exists
  - 500: Registration failed

#### Login User
- **POST** `/api/auth/login`
- **Body**:
  ```json
  {
    "email": "user@example.com",
    "password": "password123"
  }
  ```
- **Response** (200):
  ```json
  {
    "token": "jwt_token_here",
    "user": {
      "userId": "user_1234567890",
      "email": "user@example.com",
      "name": "John Doe"
    }
  }
  ```
- **Errors**:
  - 401: Invalid credentials
  - 500: Login failed

### Items Routes (`/api/items`)
- **GET** `/api/items` - Get all items
- **POST** `/api/items` - Create item
- **GET** `/api/items/:id` - Get item by ID
- **PUT** `/api/items/:id` - Update item
- **DELETE** `/api/items/:id` - Delete item

## Authentication Middleware

### Usage
```typescript
import { authMiddleware, AuthRequest } from './middleware/auth';

router.get('/protected', authMiddleware, (req: AuthRequest, res) => {
  const userId = req.userId; // Available after middleware
  // Your protected route logic
});
```

### How it works
1. Extracts JWT token from `Authorization: Bearer <token>` header
2. Verifies token using JWT_SECRET
3. Attaches `userId` to request object
4. Returns 401 if token is missing or invalid

## Database Setup

### DynamoDB Local (Development)
```bash
docker-compose up -d
```

### Create Tables
```bash
# Create Users table
npm run db:setup-users

# Create Items table
npm run db:setup
```

## Security Features
- ✅ Password hashing with bcrypt (10 salt rounds)
- ✅ JWT token-based authentication
- ✅ Token expiration (7 days default)
- ✅ Input validation with express-validator
- ✅ CORS enabled
- ✅ Environment variables for secrets
- ⚠️ SMTP email verification (skipped for now)

## NPM Scripts
```bash
npm run dev           # Start development server with hot reload
npm run build         # Compile TypeScript to JavaScript
npm start             # Run production build
npm run db:setup      # Create Items table
npm run db:setup-users # Create Users table
```

## Development Workflow
1. Start DynamoDB Local: `docker-compose up -d`
2. Create tables: `npm run db:setup-users`
3. Start dev server: `npm run dev`
4. Server runs on http://localhost:3001

## Next Steps
- [ ] Integrate with frontend
- [ ] Add chat/conversation endpoints
- [ ] Integrate LLM (AWS Bedrock/OpenAI)
- [ ] Add rate limiting
- [ ] Add request logging
- [ ] Add user profile endpoints
- [ ] Add password reset functionality
- [ ] Deploy to AWS with CDK
