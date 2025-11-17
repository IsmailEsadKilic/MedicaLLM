# MedicaLLM Backend API

Backend API service built with Express.js.

## Installation

```bash
npm install
```

## Environment Variables

Create a `.env` file (refer to `.env.example` file):

```env
PORT=5000
NODE_ENV=development
FRONTEND_URL=http://localhost:3000
USE_LOCAL_DYNAMODB=true
DYNAMODB_LOCAL_ENDPOINT=http://localhost:8000
USERS_TABLE=medicallm-users
VERIFICATION_TABLE=medicallm-verifications
```

## Running

### Development
```bash
npm run dev
```

### Production
```bash
npm run build
npm start
```

## API Endpoints

### Health Check
- `GET /health` - Checks API status

### Authentication
- `POST /api/auth/register` - New user registration
- `POST /api/auth/send-verification` - Send email verification code
- `POST /api/auth/verify-email` - Verify email verification code

## Port

Default port: `5000`

To access from frontend, add `NEXT_PUBLIC_API_URL=http://localhost:5000` environment variable to the frontend project.
