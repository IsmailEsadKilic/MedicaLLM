# Changelog

All notable changes and development progress for the MedicaLLM project.

## [Unreleased]

### Frontend
- [ ] Integrate with backend API
- [ ] Add authentication pages (Login/Register)
- [ ] Implement persistent chat storage
- [ ] Add voice input functionality
- [ ] Add file upload support

### Backend
- [ ] Add chat/conversation endpoints
- [ ] Integrate LLM (AWS Bedrock or OpenAI)
- [ ] Add rate limiting
- [ ] Add request logging middleware
- [ ] Add user profile endpoints
- [ ] Implement password reset functionality

### Infrastructure
- [ ] Create AWS CDK stack
- [ ] Deploy to AWS
- [ ] Set up CI/CD pipeline
- [ ] Configure production environment

---

## [Current] - 2024

### ✅ Frontend - Completed

#### Chat Interface
- Created React application with Vite
- Implemented multi-chat support with sidebar
- Added message history per chat
- Created empty state with suggestion prompts
- Added real-time message display
- Implemented auto-scroll to latest message

#### Chat Management
- Create new chat functionality
- Switch between multiple chats
- Rename chat with inline editing
- Delete chat (with minimum 1 chat protection)
- Auto-generate chat title from first message
- Chat dropdown menu with options

#### UI/UX Features
- Dark/Light theme toggle with smooth transitions
- Collapsible sidebar
- Smooth animations (fadeIn, pulse)
- Loading state with typing indicator (●●●)
- Responsive design
- Custom scrollbar styling

#### Components
- User avatar placeholder
- Theme toggle switch (moon/sun icons)
- Voice input button (UI only)
- Send button with disabled state
- Chat item with hover effects
- Message bubbles (user/assistant)

### ✅ Backend - Completed

#### Core Setup
- Initialized Express.js server with TypeScript
- Configured CORS for cross-origin requests
- Set up environment variables with dotenv
- Created health check endpoint (`/api/health`)
- Configured hot reload with ts-node-dev

#### Database Integration
- Integrated AWS DynamoDB SDK v3
- Set up DynamoDB Local with Docker Compose
- Created DynamoDB client configuration
- Implemented Document Client for simplified operations

#### Authentication System
- **User Registration**
  - Email validation
  - Password validation (min 6 characters)
  - Name validation
  - Duplicate user check
  - Password hashing with bcrypt (10 salt rounds)
  - Unique userId generation (timestamp-based)
  - JWT token generation
  - User data storage in DynamoDB

- **User Login**
  - Email/password validation
  - User lookup by email
  - Password verification with bcrypt
  - JWT token generation
  - User info return (without password)

- **JWT Middleware**
  - Token extraction from Authorization header
  - Token verification
  - UserId attachment to request object
  - Error handling for invalid/missing tokens

#### Database Tables
- **Users Table**
  - Partition key: email
  - Attributes: userId, password, name, createdAt
  - Billing mode: PAY_PER_REQUEST
  - Setup script: `npm run db:setup-users`

- **Items Table**
  - Partition key: id
  - Basic CRUD operations
  - Setup script: `npm run db:setup`

#### Security Features
- Password hashing with bcrypt
- JWT token-based authentication
- Token expiration (7 days)
- Input validation with express-validator
- Environment variables for secrets
- CORS configuration

#### API Endpoints
- `GET /api/health` - Health check
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `GET /api/items` - Get all items
- `POST /api/items` - Create item
- `GET /api/items/:id` - Get item by ID
- `PUT /api/items/:id` - Update item
- `DELETE /api/items/:id` - Delete item

#### NPM Scripts
- `npm run dev` - Development server with hot reload
- `npm run build` - TypeScript compilation
- `npm start` - Production server
- `npm run db:setup` - Create Items table
- `npm run db:setup-users` - Create Users table

### ✅ Documentation - Completed
- Created `documents/` folder for project documentation
- **PROJECT_OVERVIEW.md** - Project description, tech stack, structure
- **BACKEND.md** - Backend architecture, API endpoints, setup
- **AUTHENTICATION.md** - Auth flow, JWT structure, security
- **DATABASE.md** - DynamoDB schema, operations, setup
- **FRONTEND.md** - Component structure, state management, styling
- **CHANGELOG.md** - Development progress tracking

### ✅ Project Structure
```
grad_project/
├── frontend/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── App.css
│   │   └── main.jsx
│   ├── package.json
│   └── vite.config.js
├── backend/
│   ├── src/
│   │   ├── db/
│   │   │   ├── dynamodb.ts
│   │   │   ├── setup.ts
│   │   │   └── setupUsers.ts
│   │   ├── middleware/
│   │   │   └── auth.ts
│   │   ├── routes/
│   │   │   ├── auth.ts
│   │   │   └── items.ts
│   │   └── index.ts
│   ├── package.json
│   ├── tsconfig.json
│   ├── .env
│   └── docker-compose.yml
├── documents/
│   ├── PROJECT_OVERVIEW.md
│   ├── BACKEND.md
│   ├── AUTHENTICATION.md
│   ├── DATABASE.md
│   ├── FRONTEND.md
│   └── CHANGELOG.md
└── README.md
```

---

## Development Notes

### Decisions Made
1. **JWT over Sessions**: Stateless authentication for scalability
2. **DynamoDB over SQL**: NoSQL for flexibility and AWS integration
3. **TypeScript for Backend**: Type safety and better developer experience
4. **Vite over CRA**: Faster build times and better DX
5. **Custom CSS over Library**: Full control and lightweight
6. **Email as Primary Key**: Natural unique identifier for users
7. **PAY_PER_REQUEST Billing**: Better for development and variable loads

### Skipped Features (Intentional)
- ❌ SMTP email verification (will add later)
- ❌ Password reset functionality (will add later)
- ❌ Frontend-backend integration (next step)
- ❌ LLM integration (next step)
- ❌ AWS deployment (next step)

### Known Issues
- Frontend uses mock responses (not connected to backend)
- No persistent storage for frontend chats
- No rate limiting on API endpoints
- No request logging
- No error boundaries in React
- No loading states for API calls
- No form validation in frontend

### Performance Considerations
- DynamoDB Local for development (fast)
- Hot reload enabled for both frontend and backend
- Minimal dependencies
- No unnecessary re-renders in React

---

## Version History

### v0.2.0 - Current
- Backend authentication system
- DynamoDB integration
- Comprehensive documentation

### v0.1.0 - Initial
- Frontend chat interface
- Basic project structure
- README setup

---

## Contributors
- Development Team

## License
Not specified yet
