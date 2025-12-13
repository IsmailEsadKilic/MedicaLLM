# Authentication System Documentation

## Overview
JWT-based authentication system with bcrypt password hashing and DynamoDB user storage.

## Authentication Flow

### Registration Flow
```
1. User submits email, password, name
2. Validate input (email format, password length, name presence)
3. Check if user already exists in DynamoDB
4. Hash password with bcrypt (10 salt rounds)
5. Generate unique userId (user_timestamp)
6. Store user in DynamoDB Users table
7. Generate JWT token with userId
8. Return token + user info (without password)
```

### Login Flow
```
1. User submits email, password
2. Validate input
3. Fetch user from DynamoDB by email
4. Compare submitted password with hashed password using bcrypt
5. Generate JWT token with userId
6. Return token + user info (without password)
```

### Protected Route Access
```
1. Client sends request with Authorization header: "Bearer <token>"
2. Middleware extracts token from header
3. Verify token signature and expiration
4. Extract userId from token payload
5. Attach userId to request object
6. Continue to route handler
```

## JWT Token Structure

### Payload
```json
{
  "userId": "user_1234567890",
  "iat": 1234567890,
  "exp": 1234567890
}
```

### Configuration
- **Secret**: Stored in `JWT_SECRET` environment variable
- **Expiration**: 7 days (configurable via `JWT_EXPIRES_IN`)
- **Algorithm**: HS256 (default)

## Password Security

### Hashing
- **Algorithm**: bcrypt
- **Salt Rounds**: 10
- **Process**: 
  ```typescript
  const hashedPassword = await bcrypt.hash(password, 10);
  ```

### Verification
```typescript
const isValid = await bcrypt.compare(plainPassword, hashedPassword);
```

## User Model (DynamoDB)

### Table: Users
- **Partition Key**: email (String)
- **Billing Mode**: PAY_PER_REQUEST

### Attributes
```typescript
{
  email: string;          // Primary key
  userId: string;         // Unique identifier (user_timestamp)
  password: string;       // Bcrypt hashed password
  name: string;           // User's display name
  createdAt: string;      // ISO timestamp
}
```

## Input Validation

### Registration
- **email**: Must be valid email format
- **password**: Minimum 6 characters
- **name**: Cannot be empty

### Login
- **email**: Must be valid email format
- **password**: Cannot be empty

### Validation Library
Using `express-validator` for server-side validation.

## Error Responses

### 400 Bad Request
```json
{
  "errors": [
    {
      "msg": "Invalid value",
      "param": "email",
      "location": "body"
    }
  ]
}
```

### 401 Unauthorized
```json
{
  "error": "Invalid credentials"
}
```
or
```json
{
  "error": "No token provided"
}
```
or
```json
{
  "error": "Invalid token"
}
```

### 500 Internal Server Error
```json
{
  "error": "Registration failed"
}
```
or
```json
{
  "error": "Login failed"
}
```

## Middleware Usage Example

```typescript
import { authMiddleware, AuthRequest } from './middleware/auth';

// Protected route
router.get('/profile', authMiddleware, async (req: AuthRequest, res) => {
  const userId = req.userId; // Available after auth middleware
  
  // Fetch user data using userId
  const user = await getUserById(userId);
  res.json(user);
});
```

## Security Best Practices Implemented

✅ **Password Hashing**: Never store plain text passwords
✅ **JWT Tokens**: Stateless authentication
✅ **Token Expiration**: Tokens expire after 7 days
✅ **Input Validation**: Server-side validation for all inputs
✅ **Environment Variables**: Secrets stored in .env file
✅ **CORS**: Cross-origin requests handled properly
✅ **Unique User IDs**: Timestamp-based unique identifiers

## Security Considerations (TODO)

⚠️ **Email Verification**: Not implemented (skipped SMTP)
⚠️ **Password Reset**: Not implemented yet
⚠️ **Rate Limiting**: Should add to prevent brute force
⚠️ **Refresh Tokens**: Consider implementing for better security
⚠️ **Password Strength**: Could enforce stronger password requirements
⚠️ **Account Lockout**: After multiple failed login attempts
⚠️ **2FA**: Two-factor authentication for enhanced security

## Testing Authentication

### Register a User
```bash
curl -X POST http://localhost:3001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "name": "Test User"
  }'
```

### Login
```bash
curl -X POST http://localhost:3001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123"
  }'
```

### Access Protected Route
```bash
curl -X GET http://localhost:3001/api/protected \
  -H "Authorization: Bearer YOUR_JWT_TOKEN_HERE"
```

## Frontend Integration (Pending)

### Store Token
```javascript
localStorage.setItem('token', response.token);
```

### Send Token with Requests
```javascript
fetch('http://localhost:3001/api/protected', {
  headers: {
    'Authorization': `Bearer ${localStorage.getItem('token')}`
  }
});
```

### Handle Token Expiration
```javascript
if (response.status === 401) {
  // Token expired or invalid
  localStorage.removeItem('token');
  // Redirect to login
}
```
