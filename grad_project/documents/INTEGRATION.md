# Frontend-Backend Integration Documentation

## Overview
The frontend is now integrated with the backend authentication system. Users must register/login before accessing the chat interface.

## Changes Made

### New Files Created
1. **frontend/src/Auth.jsx** - Authentication component with login/register forms
2. **frontend/src/Auth.css** - Styling for authentication pages

### Modified Files
1. **frontend/src/App.jsx** - Added authentication state and conditional rendering

## Authentication Flow

### 1. Initial Load
```javascript
useEffect(() => {
  const token = localStorage.getItem('token');
  const savedUser = localStorage.getItem('user');
  if (token && savedUser) {
    setUser(JSON.parse(savedUser));
  }
}, []);
```
- Checks localStorage for existing token and user data
- Auto-logs in user if valid session exists

### 2. Login/Register
```javascript
const response = await fetch('http://localhost:3001/api/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ email, password })
});
```
- Sends credentials to backend
- Receives JWT token and user data
- Stores in localStorage
- Updates app state

### 3. Logout
```javascript
const handleLogout = () => {
  localStorage.removeItem('token');
  localStorage.removeItem('user');
  setUser(null);
  setChats([{ id: 1, title: 'New Chat', messages: [] }]);
  setCurrentChatId(1);
};
```
- Clears localStorage
- Resets app state
- Returns to login screen

## Component Structure

### Auth Component
```jsx
<Auth onLogin={handleLogin} />
```

**Props:**
- `onLogin(userData)` - Callback when authentication succeeds

**State:**
- `isLogin` - Toggle between login/register
- `formData` - Form inputs (email, password, name)
- `error` - Error message display
- `loading` - Loading state during API call

**Features:**
- Form validation (email format, password min 6 chars)
- Error handling and display
- Toggle between login/register
- Loading state during authentication

### App Component Updates

**New State:**
```javascript
const [user, setUser] = useState(null);
```

**Conditional Rendering:**
```javascript
if (!user) {
  return <Auth onLogin={handleLogin} />;
}
```

**User Display:**
- Shows user's name in sidebar footer
- Shows first letter of name in avatar
- Click to logout

## API Integration

### Register Endpoint
```javascript
POST http://localhost:3001/api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123",
  "name": "John Doe"
}

Response:
{
  "token": "jwt_token_here",
  "user": {
    "userId": "user_1234567890",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

### Login Endpoint
```javascript
POST http://localhost:3001/api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "token": "jwt_token_here",
  "user": {
    "userId": "user_1234567890",
    "email": "user@example.com",
    "name": "John Doe"
  }
}
```

## LocalStorage Structure

### Stored Data
```javascript
localStorage.setItem('token', 'jwt_token_here');
localStorage.setItem('user', JSON.stringify({
  userId: 'user_1234567890',
  email: 'user@example.com',
  name: 'John Doe'
}));
```

### Security Considerations
- JWT token stored in localStorage (XSS vulnerable)
- Consider httpOnly cookies for production
- Token expires after 7 days (backend configured)

## Error Handling

### Frontend Validation
- Email format validation (HTML5)
- Password minimum length (6 characters)
- Required field validation

### Backend Error Display
```javascript
catch (err) {
  setError(err.message);
}
```

**Error Types:**
- "User already exists" (400)
- "Invalid credentials" (401)
- "Authentication failed" (500)
- Validation errors from express-validator

## Testing the Integration

### 1. Start Backend
```bash
cd backend
docker-compose up -d  # Start DynamoDB
npm run db:setup-users  # Create Users table
npm run dev  # Start backend on port 3001
```

### 2. Start Frontend
```bash
cd frontend
npm run dev  # Start frontend on port 5173
```

### 3. Test Registration
1. Open http://localhost:5173
2. Click "Sign up"
3. Enter name, email, password
4. Click "Sign up" button
5. Should redirect to chat interface

### 4. Test Login
1. Logout (click user name in sidebar)
2. Enter registered email and password
3. Click "Sign in"
4. Should redirect to chat interface

### 5. Test Persistence
1. Refresh the page
2. Should remain logged in
3. User data persists across refreshes

## UI/UX Features

### Auth Page
- Gradient background (purple theme)
- Centered white card
- Smooth transitions
- Error message display
- Loading state on button
- Toggle between login/register

### User Display
- Avatar with first letter of name
- Full name in sidebar
- Click to logout
- Tooltip on hover

## Next Steps

### Immediate
- [ ] Add protected API calls with Authorization header
- [ ] Implement token refresh mechanism
- [ ] Add loading state on initial auth check
- [ ] Handle token expiration gracefully

### Future Enhancements
- [ ] Password strength indicator
- [ ] "Remember me" checkbox
- [ ] Forgot password flow
- [ ] Email verification
- [ ] Social login (Google, GitHub)
- [ ] User profile page
- [ ] Change password functionality
- [ ] Session timeout warning

## Known Issues

1. **CORS**: Backend must have CORS enabled (already configured)
2. **Token Expiration**: No automatic refresh, user must re-login after 7 days
3. **XSS Vulnerability**: Token in localStorage is vulnerable to XSS attacks
4. **No Loading State**: Initial auth check has no loading indicator

## Security Recommendations

### For Production
1. Use httpOnly cookies instead of localStorage
2. Implement CSRF protection
3. Add rate limiting on auth endpoints
4. Use HTTPS only
5. Implement refresh token rotation
6. Add account lockout after failed attempts
7. Log authentication events
8. Add 2FA support

## Troubleshooting

### "Failed to fetch" Error
- Check if backend is running on port 3001
- Verify CORS is enabled in backend
- Check browser console for details

### "Invalid credentials" Error
- Verify user exists in database
- Check password is correct
- Ensure DynamoDB is running

### Token Not Persisting
- Check localStorage in browser DevTools
- Verify token is being saved after login
- Check for localStorage quota issues

### User Not Auto-Logging In
- Check if token exists in localStorage
- Verify token format is correct
- Check browser console for errors
