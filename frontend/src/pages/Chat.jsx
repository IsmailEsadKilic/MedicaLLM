import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import config from '../api/config';
import '../App.css';

function Chat() {
  const [user, setUser] = useState(null);
  const [chats, setChats] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [loadingChats, setLoadingChats] = useState(true);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [theme, setTheme] = useState('dark');
  const [editingId, setEditingId] = useState(null);
  const [editTitle, setEditTitle] = useState('');
  const [menuOpen, setMenuOpen] = useState(null);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const [showDebug, setShowDebug] = useState({});
  const [isListening, setIsListening] = useState(false);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (!token || !savedUser) {
      navigate('/login');
    } else {
      setUser(JSON.parse(savedUser));
      loadConversations();
    }
  }, [navigate]);

  const loadConversations = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/api/conversations`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      setChats(data.map(c => ({
        id: c.id,
        title: c.title,
        messages: c.messages
      })));
      // Don't auto-create, just load existing chats
    } catch (error) {
      console.error('Failed to load conversations:', error);
    } finally {
      setLoadingChats(false);
    }
  };

  useEffect(() => {
    document.body.className = theme;
  }, [theme]);

  useEffect(() => {
    // Initialize speech recognition
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInput(transcript);
        setIsListening(false);
      };

      recognitionRef.current.onerror = () => {
        setIsListening(false);
      };

      recognitionRef.current.onend = () => {
        setIsListening(false);
      };
    }
  }, []);

  const toggleVoiceInput = () => {
    if (!recognitionRef.current) {
      alert('Voice input not supported in this browser. Try Chrome or Edge.');
      return;
    }

    if (isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    } else {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const currentChat = chats.find(c => c.id === currentChatId);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentChat?.messages]);

  const createNewChat = async () => {
    // Don't create new chat if current chat is empty
    if (currentChat && currentChat.messages.length === 0) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/api/conversations`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ title: 'New Chat' })
      });
      const data = await response.json();
      const newChat = { id: data.chat_id, title: 'New Chat', messages: [] };
      setChats([newChat, ...chats]);
      setCurrentChatId(data.chat_id);
    } catch (error) {
      console.error('Failed to create chat:', error);
    }
  };

  const deleteChat = async (id) => {
    if (chats.length === 1) return;
    try {
      const token = localStorage.getItem('token');
      await fetch(`${config.API_URL}/api/conversations/${id}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const filtered = chats.filter(c => c.id !== id);
      setChats(filtered);
      if (currentChatId === id && filtered.length > 0) {
        setCurrentChatId(filtered[0].id);
      }
    } catch (error) {
      console.error('Failed to delete chat:', error);
    }
  };

  const startEdit = (id, title) => {
    setEditingId(id);
    setEditTitle(title);
  };

  const saveEdit = async () => {
    try {
      const token = localStorage.getItem('token');
      await fetch(`${config.API_URL}/api/conversations/${editingId}/title`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ title: editTitle })
      });
      setChats(chats.map(c => c.id === editingId ? { ...c, title: editTitle } : c));
      setEditingId(null);
    } catch (error) {
      console.error('Failed to update title:', error);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    setChats([{ id: 1, title: 'New Chat', messages: [] }]);
    setCurrentChatId(1);
    navigate('/login');
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || loading) return;

    // Create new chat if none exists
    let chatId = currentChatId;
    if (!chatId) {
      try {
        const token = localStorage.getItem('token');
        const response = await fetch(`${config.API_URL}/api/conversations`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ title: 'New Chat' })
        });
        const data = await response.json();
        chatId = data.chat_id;
        const newChat = { id: chatId, title: 'New Chat', messages: [] };
        setChats(prev => [newChat, ...prev]);
        setCurrentChatId(chatId);
      } catch (error) {
        console.error('Failed to create chat:', error);
        return;
      }
    }

    const userMessage = { role: 'user', content: input, timestamp: new Date().toISOString() };
    const currentChatData = chats.find(c => c.id === chatId);
    const isFirstMessage = !currentChatData || currentChatData.messages.length === 0;

    // Save user message to database
    try {
      const token = localStorage.getItem('token');
      await fetch(`${config.API_URL}/api/conversations/${chatId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: userMessage })
      });
    } catch (error) {
      console.error('Failed to save message:', error);
    }

    setChats(prev => prev.map(c =>
      c.id === chatId
        ? { ...c, messages: [...c.messages, userMessage] }
        : c
    ));
    const query = input;
    setInput('');
    setLoading(true);

    try {
      const token = localStorage.getItem('token');

      // Generate title using LLM
      if (isFirstMessage) {
        fetch(`${config.API_URL}/api/drugs/generate-title`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ message: input })
        })
          .then(res => res.json())
          .then(data => {
            if (data.title) {
              setChats(prev => prev.map(c =>
                c.id === chatId ? { ...c, title: data.title } : c
              ));
              fetch(`${config.API_URL}/api/conversations/${chatId}/title`, {
                method: 'PATCH',
                headers: {
                  'Content-Type': 'application/json',
                  'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ title: data.title })
              }).catch(() => { });
            }
          })
          .catch(() => { });
      }
      // Build conversation history for context
      const conversationHistory = (currentChatData?.messages || []).map(m =>
        `${m.role === 'user' ? 'User' : 'Assistant'}: ${m.content}`
      ).join('\n');

      const fullQuery = conversationHistory ?
        `Previous conversation:\n${conversationHistory}\n\nCurrent question: ${query}` :
        query;

      const response = await fetch(`${config.API_URL}/api/drugs/query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ query: fullQuery, conversation_id: chatId })
      });

      const data = await response.json();

      const botMessage = {
        role: 'assistant',
        content: data.answer || data.error || 'No response received',
        timestamp: new Date().toISOString(),
        tool_used: data.tool_used,
        tool_result: data.tool_result,
        sources: data.sources
      };

      // Save message to database
      await fetch(`${config.API_URL}/api/conversations/${chatId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ message: botMessage })
      });

      setChats(prev => prev.map(c =>
        c.id === chatId ? { ...c, messages: [...c.messages, botMessage] } : c
      ));
    } catch (error) {
      const errorMessage = {
        role: 'assistant',
        content: 'Error: Could not connect to the server. Make sure the backend is running.'
      };
      setChats(prev => prev.map(c =>
        c.id === chatId ? { ...c, messages: [...c.messages, errorMessage] } : c
      ));
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;
  if (loadingChats) return <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>Loading...</div>;

  return (
    <div className={`app ${theme}`}>
      {sidebarOpen && (
        <div className="sidebar">
          <div className="sidebar-header">
            <button className="new-chat" onClick={createNewChat}>
              <span>+</span> New chat
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
                          <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                          <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                        </svg>
                        Rename
                      </div>
                      {chats.length > 1 && (
                        <div className="menu-item" onClick={(e) => { e.stopPropagation(); deleteChat(chat.id); setMenuOpen(null); }}>
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                            <polyline points="3 6 5 6 21 6" />
                            <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
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
          <div className="sidebar-footer" style={{ flexDirection: 'column' }}>
            <button
              className="patients-btn"
              onClick={() => navigate('/drug-search')}
              style={{ marginBottom: '10px' }}
            >
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8" />
                <path d="m21 21-4.35-4.35" />
              </svg>
              Drug Search
            </button>
            {user.accountType === 'healthcare_professional' && (
              <button
                className="patients-btn"
                onClick={() => navigate('/patients')}
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                  <circle cx="9" cy="7" r="4" />
                  <path d="M23 21v-2a4 4 0 0 0-3-3.87" />
                  <path d="M16 3.13a4 4 0 0 1 0 7.75" />
                </svg>
                My Patients
              </button>
            )}
          </div>
        </div>
      )}
      <div className="main">
        <div className="header">
          <div className="header-left">
            <button className="menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>☰</button>
            <h2>MedicaLLM</h2>
          </div>
          <div className="header-right">
            <label className="theme-toggle">
              <input type="checkbox" checked={theme === 'dark'} onChange={() => setTheme(theme === 'dark' ? 'light' : 'dark')} />
              <span className="slider"></span>
            </label>
            <div className="user-menu">
              <div className="user-info" onClick={() => setProfileMenuOpen(!profileMenuOpen)}>
                <div className="user-avatar">{user.name.charAt(0).toUpperCase()}</div>
                <span>{user.name}</span>
              </div>
              {profileMenuOpen && (
                <div className="profile-dropdown">
                  <div className="menu-item" onClick={() => { setProfileMenuOpen(false); }}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="3" />
                      <path d="M12 1v6m0 6v6M5.6 5.6l4.2 4.2m4.2 4.2l4.2 4.2M1 12h6m6 0h6M5.6 18.4l4.2-4.2m4.2-4.2l4.2-4.2" />
                    </svg>
                    Settings
                  </div>
                  <div className="menu-item" onClick={handleLogout}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                      <polyline points="16 17 21 12 16 7" />
                      <line x1="21" y1="12" x2="9" y2="12" />
                    </svg>
                    Logout
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
        <div className="messages">
          {!currentChatId || currentChat?.messages.length === 0 ? (
            <div className="empty-state">
              <h1>How can I help you today?</h1>
              <div className="suggestions">
                <button className="suggestion" onClick={() => setInput('What is Warfarin used for?')}>
                  What is Warfarin used for?
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
                  <div className="content">
                    {msg.role === 'assistant' ? (
                      <>
                        <ReactMarkdown>{msg.content}</ReactMarkdown>
                        {msg.sources && Array.isArray(msg.sources) && msg.sources.length > 0 && (
                          <div className="sources-section">
                            <div className="sources-title">Sources:</div>
                            <ul className="sources-list">
                              {msg.sources.map((source, idx) => (
                                <li key={idx} className="source-item">
                                  <span className="source-name">{source.source}</span>
                                  {source.page && <span className="source-page"> (Page {source.page})</span>}
                                </li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {msg.tool_used && (
                          <div style={{ marginTop: '10px' }}>
                            <button
                              onClick={() => setShowDebug({ ...showDebug, [i]: !showDebug[i] })}
                              style={{
                                background: 'rgba(255,255,255,0.1)',
                                border: '1px solid rgba(255,255,255,0.2)',
                                borderRadius: '4px',
                                padding: '4px 8px',
                                fontSize: '12px',
                                cursor: 'pointer',
                                color: 'inherit',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '4px'
                              }}
                            >
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <circle cx="12" cy="12" r="10" />
                                <line x1="12" y1="16" x2="12" y2="12" />
                                <line x1="12" y1="8" x2="12.01" y2="8" />
                              </svg>
                              {showDebug[i] ? 'Hide' : 'Show'} Debug Info
                            </button>
                            {showDebug[i] && (
                              <div style={{
                                marginTop: '8px',
                                padding: '10px',
                                background: 'rgba(0,0,0,0.2)',
                                borderRadius: '4px',
                                fontSize: '13px',
                                fontFamily: 'monospace'
                              }}>
                                <div><strong>Tool Used:</strong> {msg.tool_used}</div>
                                {/* <div style={{ marginTop: '8px' }}><strong>Result:</strong></div>
                                <pre style={{ margin: '4px 0 0 0', whiteSpace: 'pre-wrap' }}>
                                  {msg.tool_result ? (
                                    typeof msg.tool_result === 'string' ? msg.tool_result : JSON.stringify(msg.tool_result, null, 2)
                                  ) : (
                                    <span style={{ color: '#aaa', fontStyle: 'italic' }}>No result output available</span>
                                  )}
                                </pre> */}
                              </div>
                            )}
                          </div>
                        )}
                      </>
                    ) : (
                      msg.content
                    )}
                  </div>
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
            <button
              type="button"
              className="voice-btn"
              disabled={loading}
              onClick={toggleVoiceInput}
              style={{ color: isListening ? '#ef4444' : 'inherit' }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 1a3 3 0 0 0-3 3v8a3 3 0 0 0 6 0V4a3 3 0 0 0-3-3z" />
                <path d="M19 10v2a7 7 0 0 1-14 0v-2" />
                <line x1="12" y1="19" x2="12" y2="23" />
                <line x1="8" y1="23" x2="16" y2="23" />
              </svg>
            </button>
            <button type="submit" className="send-btn" disabled={loading || !input.trim()}>↑</button>
          </div>
        </form>
      </div>
    </div>
  );
}

export default Chat;
