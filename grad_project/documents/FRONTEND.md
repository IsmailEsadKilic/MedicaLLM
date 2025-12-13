# Frontend Documentation

## Overview
React-based chat interface with dark/light theme support, built with Vite.

## Technology Stack
- **Framework**: React 18.2.0
- **Build Tool**: Vite 5.0.0
- **Language**: JavaScript (JSX)
- **Styling**: Custom CSS
- **State Management**: React Hooks (useState, useEffect, useRef)

## Project Structure
```
frontend/
├── src/
│   ├── App.jsx          # Main application component
│   ├── App.css          # Application styles
│   └── main.jsx         # React entry point
├── index.html
├── package.json
└── vite.config.js
```

## Features

### ✅ Implemented Features
1. **Chat Interface**
   - Multi-chat support with sidebar
   - Message history per chat
   - Real-time message display
   - Empty state with suggestions

2. **Chat Management**
   - Create new chat
   - Switch between chats
   - Rename chat
   - Delete chat (minimum 1 chat required)
   - Auto-title from first message

3. **UI/UX**
   - Dark/Light theme toggle
   - Responsive sidebar (collapsible)
   - Smooth animations
   - Auto-scroll to latest message
   - Loading state with typing indicator

4. **User Interface Elements**
   - User avatar placeholder
   - Theme toggle switch
   - Voice input button (UI only)
   - Send button with disabled state
   - Chat dropdown menu

### ⏳ Pending Features
- Backend API integration
- Real authentication
- Persistent chat storage
- Voice input functionality
- File upload
- Message editing
- Message search

## Component Structure

### Main App Component
```jsx
function App() {
  // State Management
  const [chats, setChats] = useState([...]);
  const [currentChatId, setCurrentChatId] = useState(1);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [theme, setTheme] = useState('dark');
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [menuOpen, setMenuOpen] = useState(null);
  
  // Refs
  const messagesEndRef = useRef(null);
}
```

## State Management

### Chat State
```javascript
{
  id: number,              // Unique chat identifier
  title: string,           // Chat title (auto-generated or custom)
  messages: Array<{
    role: 'user' | 'assistant',
    content: string
  }>
}
```

### Example Chat Object
```javascript
{
  id: 1,
  title: "New Chat",
  messages: [
    { role: 'user', content: 'Hello' },
    { role: 'assistant', content: 'Hi! How can I help?' }
  ]
}
```

## Key Functions

### createNewChat()
Creates a new chat and switches to it
```javascript
const createNewChat = () => {
  const newId = Math.max(...chats.map(c => c.id)) + 1;
  setChats([...chats, { id: newId, title: 'New Chat', messages: [] }]);
  setCurrentChatId(newId);
};
```

### deleteChat(id)
Deletes a chat (prevents deleting last chat)
```javascript
const deleteChat = (id) => {
  if (chats.length === 1) return;
  const filtered = chats.filter(c => c.id !== id);
  setChats(filtered);
  if (currentChatId === id) setCurrentChatId(filtered[0].id);
};
```

### sendMessage(e)
Handles message submission (currently mock response)
```javascript
const sendMessage = async (e) => {
  e.preventDefault();
  if (!input.trim() || loading) return;

  // Add user message
  const userMessage = { role: 'user', content: input };
  // Update chats with user message
  // Set loading state
  // Mock API call (setTimeout)
  // Add assistant response
};
```

## Styling System

### Theme Classes
- `.app.dark` - Dark theme styles
- `.app.light` - Light theme styles

### Color Scheme

**Dark Theme**
- Background: #212121
- Sidebar: #171717
- Text: #ececec
- Borders: #2f2f2f
- Accent: #8b5cf6 (purple)

**Light Theme**
- Background: #ffffff
- Sidebar: #f7f7f8
- Text: #1f1f1f
- Borders: #e5e5e5
- Accent: #8b5cf6 (purple)

### Key CSS Classes
```css
.sidebar              /* Chat history sidebar */
.chat-item            /* Individual chat in sidebar */
.messages             /* Message container */
.message.user         /* User message */
.message.assistant    /* Assistant message */
.input-wrapper        /* Message input container */
.theme-toggle         /* Theme switch */
```

## User Interactions

### Keyboard Shortcuts
- **Enter**: Send message
- **Enter** (while editing title): Save title

### Mouse Interactions
- Click chat item: Switch to chat
- Click new chat button: Create new chat
- Click menu button: Open chat options
- Click suggestion: Fill input with suggestion
- Click send button: Send message

## Auto-scroll Behavior
```javascript
useEffect(() => {
  messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
}, [currentChat?.messages]);
```

## Theme Persistence
```javascript
useEffect(() => {
  document.body.className = theme;
}, [theme]);
```

## Mock Data & Responses

### Initial State
```javascript
const [chats, setChats] = useState([
  { id: 1, title: 'New Chat', messages: [] }
]);
```

### Mock Response
```javascript
const botMessage = { 
  role: 'assistant', 
  content: 'This is a demo response. Connect to your backend API to get real responses.' 
};
```

### Suggestion Prompts
- "Explain quantum computing"
- "Write a Python function"
- "Plan a trip to Japan"

## Integration Points (TODO)

### API Integration Needed
```javascript
// Replace mock response with actual API call
const response = await fetch('http://localhost:3001/api/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    message: input,
    conversationId: currentChatId
  })
});
```

### Authentication Integration
```javascript
// Add login/register pages
// Store JWT token in localStorage
// Add protected route wrapper
// Handle token expiration
```

### Persistent Storage
```javascript
// Save chats to backend
// Load chats on mount
// Sync chat state with server
```

## Development

### Start Dev Server
```bash
npm run dev
```
Runs on http://localhost:5173

### Build for Production
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

## Responsive Design
- Sidebar: 260px fixed width
- Main content: Flexible
- Max content width: 800px (centered)
- Mobile: Sidebar can be toggled

## Accessibility Considerations (TODO)
- [ ] Add ARIA labels
- [ ] Keyboard navigation
- [ ] Screen reader support
- [ ] Focus management
- [ ] Color contrast validation

## Performance Optimizations (TODO)
- [ ] Lazy load messages
- [ ] Virtual scrolling for long chats
- [ ] Debounce input
- [ ] Memoize expensive computations
- [ ] Code splitting

## Browser Support
- Modern browsers (Chrome, Firefox, Safari, Edge)
- ES6+ features required
- CSS Grid and Flexbox support needed

## Next Steps
1. Integrate with backend API
2. Add authentication pages (Login/Register)
3. Implement real chat functionality
4. Add persistent storage
5. Implement voice input
6. Add file upload support
7. Improve accessibility
8. Add error handling
9. Add loading states
10. Optimize performance
