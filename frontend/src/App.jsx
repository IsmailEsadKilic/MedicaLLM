import { useState, useRef, useEffect } from 'react';
import './App.css';
import config from './api/config';
import Auth from './Auth';
import DrugSearch from './pages/DrugSearch';
import PatientAnalysis from './pages/PatientAnalysis';

function App() {
  console.log('App loaded at:', new Date().toISOString());
  const [user, setUser] = useState(null);
  const [chats, setChats] = useState([{ id: 1, title: 'New Chat', messages: [] }]);
  const [currentChatId, setCurrentChatId] = useState(1);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [theme, setTheme] = useState('dark');
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [menuOpen, setMenuOpen] = useState(null);
  const [currentView, setCurrentView] = useState('chat'); // 'chat', 'drug-search', or 'patient-analysis'
  const messagesEndRef = useRef(null);

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (token && savedUser) {
      setUser(JSON.parse(savedUser));
    }
  }, []);

  useEffect(() => {
    document.body.className = theme;
  }, [theme]);

  const handleLogin = (userData) => {
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setUser(null);
    setChats([{ id: 1, title: 'New Chat', messages: [] }]);
    setCurrentChatId(1);
  };

  if (!user) {
    return <Auth onLogin={handleLogin} />;
  }

  const currentChat = chats.find(c => c.id === currentChatId);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentChat?.messages]);

  const createNewChat = () => {
    const newId = Math.max(...chats.map(c => c.id)) + 1;
    setChats([...chats, { id: newId, title: 'New Chat', messages: [] }]);
    setCurrentChatId(newId);
  };

  const deleteChat = (id) => {
    if (chats.length === 1) return;
    const filtered = chats.filter(c => c.id !== id);
    setChats(filtered);
    if (currentChatId === id) setCurrentChatId(filtered[0].id);
  };

  const startEdit = (id, title) => {
    setEditingId(id);
    setEditTitle(title);
  };

  const saveEdit = () => {
    setChats(chats.map(c => c.id === editingId ? { ...c, title: editTitle } : c));
    setEditingId(null);
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    const userMessage = { role: 'user', content: input };
    const updatedChats = chats.map(c => 
      c.id === currentChatId 
        ? { ...c, messages: [...c.messages, userMessage], title: c.messages.length === 0 ? input.slice(0, 30) : c.title }
        : c
    );
    setChats(updatedChats);
    const query = input;
    setInput('');
    setLoading(true);

    try {
      const token = localStorage.getItem('token');
      console.log('Sending query to backend:', query);
      
      const response = await fetch(`${config.API_URL}/api/drugs/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ query })
      });

      console.log('Response status:', response.status);
      const data = await response.json();
      console.log('Response data:', data);
      
      const botMessage = { 
        role: 'assistant', 
        content: data.answer || data.error || 'No response received'
      };
      
      setChats(prev => prev.map(c => 
        c.id === currentChatId ? { ...c, messages: [...c.messages, botMessage] } : c
      ));
    } catch (error) {
      const errorMessage = { 
        role: 'assistant', 
        content: 'Error: Could not connect to the server. Make sure the backend is running.'
      };
      setChats(prev => prev.map(c => 
        c.id === currentChatId ? { ...c, messages: [...c.messages, errorMessage] } : c
      ));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className={`app ${theme}`}>
      {sidebarOpen && (
        <div className="sidebar">
          <div className="sidebar-header">
            <button className="new-chat" onClick={createNewChat}>
              <span>+</span> New chat
            </button>
            <button className="new-chat" onClick={() => setCurrentView('drug-search')} style={{ marginTop: '10px' }}>
              🔍 Drug Search
            </button>
            <button className="new-chat" onClick={() => setCurrentView('patient-analysis')} style={{ marginTop: '10px' }}>
              🏥 Patient Analysis
            </button>
            <button className="new-chat" onClick={() => setCurrentView('chat')} style={{ marginTop: '10px' }}>
              💬 Chat
            </button>
          </div>
          <div className="chat-history">
            {chats.map(chat => (
              <div 
                key={chat.id} 
                className={`chat-item ${chat.id === currentChatId ? 'active' : ''}`}
                onClick={() => setCurrentChatId(chat.id)}
              >
                {editingId === chat.id ? (
                  <input 
                    className="chat-title-input"
                    value={editTitle}
                    onChange={(e) => setEditTitle(e.target.value)}
                    onBlur={saveEdit}
                    onKeyDown={(e) => e.key === 'Enter' && saveEdit()}
                    onClick={(e) => e.stopPropagation()}
                    autoFocus
                  />
                ) : (
                  <div className="chat-title">{chat.title}</div>
                )}
                <div className="chat-menu">
                  <button className="menu-btn-chat" onClick={(e) => { e.stopPropagation(); setMenuOpen(menuOpen === chat.id ? null : chat.id); }}>⋯</button>
                  {menuOpen === chat.id && (
                    <div className="chat-dropdown">
                      <div className="menu-item" onClick={(e) => { e.stopPropagation(); startEdit(chat.id, chat.title); setMenuOpen(null); }}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                        Rename
                      </div>
                      {chats.length > 1 && (
                        <div className="menu-item" onClick={(e) => { e.stopPropagation(); deleteChat(chat.id); setMenuOpen(null); }}>
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <polyline points="3 6 5 6 21 6"/>
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                          </svg>
                          Delete
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
          <div className="sidebar-footer">
            <div className="user-info" onClick={handleLogout} title="Click to logout">
              <div className="user-avatar">{user.name.charAt(0).toUpperCase()}</div>
              <span>{user.name}</span>
            </div>
            <label className="theme-toggle">
              <input type="checkbox" checked={theme === 'dark'} onChange={() => setTheme(theme === 'dark' ? 'light' : 'dark')} />
              <span className="slider"></span>
            </label>
          </div>
        </div>
      )}
      <div className="main">
        {currentView === 'drug-search' ? (
          <DrugSearch />
        ) : currentView === 'patient-analysis' ? (
          <PatientAnalysis />
        ) : (
        <>
        <div className="header">
          <button className="menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>☰</button>
          <h2>MedicaLLM - Drug Info AI</h2>
          <div className="spacer"></div>
        </div>
        <div className="messages">
          {currentChat?.messages.length === 0 ? (
            <div className="empty-state">
              <h1>How can I help you today?</h1>
              <div className="suggestions">
                <button className="suggestion" onClick={() => setInput('What can I do during a hypertension episode?')}>
                  What can I do during a hypertension episode?
                </button>
                <button className="suggestion" onClick={() => setInput('Do Warfarin and Ibuprofen interact?')}>
                  Do Warfarin and Ibuprofen interact?
                </button>
                <button className="suggestion" onClick={() => setInput('Tell me about Aspirin')}>
                  Tell me about Aspirin
                </button>
              </div>
            </div>
          ) : (
            currentChat?.messages.map((msg, i) => (
              <div key={i} className={`message ${msg.role}`}>
                <div className="message-inner">
                  <div className="avatar">{msg.role === 'user' ? 'U' : 'AI'}</div>
                  <div className="content">{msg.content}</div>
                </div>
              </div>
            ))
          )}
          {loading && <div className="message assistant"><div className="message-inner"><div className="avatar">AI</div><div className="content"><div className="typing">●●●</div></div></div></div>}
          <div ref={messagesEndRef} />
        </div>
        <form onSubmit={sendMessage} className="input-form">
          <div className="input-wrapper">
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Message MedicaLLM..."
              disabled={loading}
            />
            <button type="button" className="voice-btn" disabled={loading}>
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z"/>
                <path d="M19 10v2a7 7 0 0 1-14 0v-2"/>
                <line x1="12" y1="19" x2="12" y2="23"/>
                <line x1="8" y1="23" x2="16" y2="23"/>
              </svg>
            </button>
            <button type="submit" className="send-btn" disabled={loading || !input.trim()}>↑</button>
          </div>
        </form>
        </>
        )}
      </div>
    </div>
  );
}

export default App;
