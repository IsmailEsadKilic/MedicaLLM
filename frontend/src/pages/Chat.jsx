import { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import config from '../api/config';
import PdfPanel from './PdfPanel';
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
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [showDebug, setShowDebug] = useState({});
  const [showSources, setShowSources] = useState({});
  const [isListening, setIsListening] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [thinkingStep, setThinkingStep] = useState('');
  // O8: PDF preview side panel — { source: string, page: number } | null
  const [pdfPanel, setPdfPanel] = useState(null);
  // O10: Patient-aware responses — patient list and the currently selected patient
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
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

  // O10: Load patient list for healthcare professionals so they can select
  // an active patient context from the chat header.
  useEffect(() => {
    if (!user || user.account_type !== 'healthcare_professional') return;
    const fetchPatients = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${config.API_URL}/api/patients/`, {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          setPatients(Array.isArray(data) ? data : []);
        }
      } catch {
        // non-fatal — patient selector simply stays empty
      }
    };
    fetchPatients();
  }, [user]);

  const loadConversations = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/api/conversations/`, {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      const data = await response.json();
      const conversations = data.conversations || data;
      setChats(conversations.map(c => ({
        id: c.id,
        title: c.title,
        messages: c.messages || []
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
  }, [currentChat?.messages, streamingContent]);

  const createNewChat = async () => {
    // Don't create new chat if current chat is empty or no chat is selected
    if (!currentChatId || (currentChat && currentChat.messages.length === 0)) {
      return;
    }

    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${config.API_URL}/api/conversations/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ title: 'New Chat' })
      });
      const data = await response.json();
      const newChat = { id: data.conversation_id, title: 'New Chat', messages: [] };
      setChats([newChat, ...chats]);
      setCurrentChatId(data.conversation_id);
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
        const response = await fetch(`${config.API_URL}/api/conversations/`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ title: 'New Chat' })
        });
        const data = await response.json();
        chatId = data.conversation_id;
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

    // Update local state immediately (session saves to DB)
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
      
      // Send query to agent via SSE streaming endpoint
      const response = await fetch(`${config.API_URL}/api/drugs/query-stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          query: query,
          conversation_id: chatId,
          // O10: pass patient context and role for dynamic system prompt
          patient_id: selectedPatient ? selectedPatient.id : null,
          account_type: user ? user.account_type : null,
        })
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      if (!response.body) {
        throw new Error('Response body is null');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let accumulatedContent = '';
      let sources = [];
      let toolUsed = null;

      setIsStreaming(true);
      setStreamingContent('');
      setThinkingStep('');

      // Parse the SSE stream with improved error handling
      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const events = buffer.split('\n\n');
          buffer = events.pop() || '';

          for (const event of events) {
            if (!event.trim()) continue;
            
            for (const line of event.split('\n')) {
              if (!line.startsWith('data: ')) continue;
              
              try {
                const chunk = JSON.parse(line.slice(6));
                
                if (chunk.type === 'thinking') {
                  setThinkingStep(chunk.step || '');
                } else if (chunk.type === 'content') {
                  setThinkingStep('');
                  accumulatedContent += chunk.content;
                  setStreamingContent(accumulatedContent);
                } else if (chunk.type === 'done') {
                  sources = chunk.sources || [];
                  toolUsed = chunk.tool_used || null;
                } else if (chunk.type === 'error') {
                  throw new Error(chunk.error || 'Streaming error');
                }
              } catch (parseErr) {
                console.warn('Failed to parse SSE chunk:', line, parseErr);
                // Continue processing other chunks
              }
            }
          }
        }
      } finally {
        // Ensure reader is released
        reader.releaseLock();
      }

      // Finalize: commit the completed message to chat state
      const botMessage = {
        role: 'assistant',
        content: accumulatedContent || 'No response received',
        timestamp: new Date().toISOString(),
        tool_used: toolUsed,
        sources: sources,
      };

      setChats(prev => prev.map(c =>
        c.id === chatId ? { ...c, messages: [...c.messages, botMessage] } : c
      ));
      setStreamingContent('');
      setIsStreaming(false);
      setThinkingStep('');
    } catch (error) {
      console.error('Streaming error:', error);
      setStreamingContent('');
      setIsStreaming(false);
      setThinkingStep('');
      const errorMessage = {
        role: 'assistant',
        content: `Error: ${error.message || 'Could not connect to the server. Make sure the backend is running.'}`,
        timestamp: new Date().toISOString(),
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
            {user.account_type === 'healthcare_professional' && (
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
      <div className={`chat-content-area${pdfPanel ? ' pdf-panel-open' : ''}`}>
      <div className="main">
        <div className="header">
          <div className="header-left">
            <button className="menu-btn" onClick={() => setSidebarOpen(!sidebarOpen)}>☰</button>
            <h2>MedicaLLM</h2>
          </div>
          {/* O10: Patient context selector — visible only for healthcare professionals */}
          {user && user.account_type === 'healthcare_professional' && (
            <div className="patient-selector">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
              </svg>
              <select
                className="patient-select"
                value={selectedPatient ? selectedPatient.id : ''}
                onChange={(e) => {
                  const pid = e.target.value;
                  setSelectedPatient(pid ? patients.find(p => p.id === pid) || null : null);
                }}
                title="Select an active patient for context-aware responses"
              >
                <option value="">No patient selected</option>
                {patients.map(p => (
                  <option key={p.id} value={p.id}>{p.name}</option>
                ))}
              </select>
              {selectedPatient && (
                <button
                  className="clear-patient-btn"
                  onClick={() => setSelectedPatient(null)}
                  title="Clear patient context"
                >✕</button>
              )}
            </div>
          )}
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
                  <div className="dropdown-user-info">
                    <div className="dropdown-avatar">{user.name.charAt(0).toUpperCase()}</div>
                    <div>
                      <div className="dropdown-name">{user.name}</div>
                      <div className="dropdown-email">{user.email}</div>
                      <div className="dropdown-role">{user.account_type === 'healthcare_professional' ? 'Healthcare Professional' : 'General User'}</div>
                    </div>
                  </div>
                  <div className="dropdown-divider" />
                  <div className="menu-item" onClick={() => { setProfileMenuOpen(false); setSettingsOpen(true); }}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="12" cy="12" r="3" />
                      <path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" />
                    </svg>
                    Settings
                  </div>
                  <div className="menu-item" onClick={() => { setProfileMenuOpen(false); navigate('/drug-search'); }}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <circle cx="11" cy="11" r="8" /><path d="m21 21-4.35-4.35" />
                    </svg>
                    Drug Search
                  </div>
                  {user.account_type === 'healthcare_professional' && (
                    <div className="menu-item" onClick={() => { setProfileMenuOpen(false); navigate('/patients'); }}>
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" /><circle cx="9" cy="7" r="4" />
                        <path d="M23 21v-2a4 4 0 0 0-3-3.87" /><path d="M16 3.13a4 4 0 0 1 0 7.75" />
                      </svg>
                      My Patients
                    </div>
                  )}
                  <div className="menu-item" onClick={() => { setProfileMenuOpen(false); navigate('/'); }}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                      <polyline points="9 22 9 12 15 12 15 22" />
                    </svg>
                    Home Page
                  </div>
                  <div className="dropdown-divider" />
                  <div className="menu-item danger" onClick={handleLogout}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
                      <polyline points="16 17 21 12 16 7" />
                      <line x1="21" y1="12" x2="9" y2="12" />
                    </svg>
                    Sign Out
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
                  <div className="content">
                    {msg.role === 'assistant' ? (
                      <>
                        <ReactMarkdown remarkPlugins={[remarkGfm]}>{msg.content}</ReactMarkdown>
                        {msg.sources && Array.isArray(msg.sources) && msg.sources.length > 0 && (
                          <div className="sources-section">
                            <button
                              className="sources-toggle"
                              onClick={() => setShowSources({ ...showSources, [i]: !showSources[i] })}
                            >
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                                style={{ transform: showSources[i] ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}>
                                <polyline points="9 18 15 12 9 6" />
                              </svg>
                              Sources ({msg.sources.length})
                            </button>
                            {showSources[i] && (
                            <div className="sources-list-rich">
                              {msg.sources.map((source, idx) => {
                                const isPdf = (source.source &&
                                  source.source.toLowerCase().endsWith('.pdf')) ||
                                  !!source.pdf_path;
                                const pdfSource = source.pdf_path || source.source;
                                const pageNum = source.page ? parseInt(source.page, 10) : 1;
                                const isActive = pdfPanel &&
                                  pdfPanel.source === pdfSource &&
                                  pdfPanel.page === pageNum;
                                const hasPubMedLink = source.pmid && !source.pdf_path;
                                const hasConfidence = source.confidence_score !== undefined;
                                return (
                                  <div key={idx} className="source-card">
                                    <div className="source-card-header">
                                      <span className="source-card-num">{idx + 1}</span>
                                      <div className="source-card-title">
                                        {source.title || source.source}
                                      </div>
                                      {hasConfidence && (
                                        <span className={`confidence-badge ${
                                          source.confidence_score >= 70 ? 'high' :
                                          source.confidence_score >= 40 ? 'medium' : 'low'
                                        }`}>
                                          {source.confidence_score}/100
                                        </span>
                                      )}
                                    </div>
                                    <div className="source-card-meta">
                                      {source.source && <span className="source-journal">{source.source}</span>}
                                      {source.study_type && source.study_type !== 'Unknown' && (
                                        <span className="source-study-type">{source.study_type}</span>
                                      )}
                                      {source.citations !== undefined && source.citations > 0 && (
                                        <span className="source-citations">{source.citations} citations</span>
                                      )}
                                      {source.page && (
                                        <span className="source-page">Page {source.page}</span>
                                      )}
                                    </div>
                                    {source.content && (
                                      <div className="source-card-snippet">{source.content}</div>
                                    )}
                                    <div className="source-card-actions">
                                      {isPdf && (
                                        <button
                                          className={`view-source-btn${isActive ? ' active' : ''}`}
                                          onClick={() =>
                                            isActive
                                              ? setPdfPanel(null)
                                              : setPdfPanel({ source: pdfSource, page: pageNum })
                                          }
                                        >
                                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                            <polyline points="14 2 14 8 20 8" />
                                          </svg>
                                          {isActive ? 'Close PDF' : 'View PDF'}
                                        </button>
                                      )}
                                      {hasPubMedLink && (
                                        <a
                                          className="view-source-btn"
                                          href={`https://pubmed.ncbi.nlm.nih.gov/${source.pmid}/`}
                                          target="_blank"
                                          rel="noopener noreferrer"
                                          style={{ textDecoration: 'none' }}
                                        >
                                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
                                            <polyline points="15 3 21 3 21 9" />
                                            <line x1="10" y1="14" x2="21" y2="3" />
                                          </svg>
                                          View on PubMed
                                        </a>
                                      )}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                            )}
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
                      <span style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</span>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
          {/* Show thinking steps while agent is working */}
          {loading && !isStreaming && !thinkingStep && (
            <div className="message assistant">
              <div className="message-inner">
                <div className="avatar">AI</div>
                <div className="content">
                  <div className="typing">●●●</div>
                </div>
              </div>
            </div>
          )}
          {thinkingStep && !streamingContent && (
            <div className="message assistant">
              <div className="message-inner">
                <div className="avatar">AI</div>
                <div className="content">
                  <div className="thinking-step">{thinkingStep}</div>
                </div>
              </div>
            </div>
          )}
          {/* Render live streaming content token-by-token */}
          {isStreaming && streamingContent && (
            <div className="message assistant">
              <div className="message-inner">
                <div className="avatar">AI</div>
                <div className="content">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>{streamingContent}</ReactMarkdown>
                  <span className="streaming-cursor" />
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
        <form onSubmit={sendMessage} className="input-form">
          <div className="input-wrapper">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  if (input.trim() && !loading) {
                    sendMessage(e);
                  }
                }
              }}
              placeholder="Message MedicaLLM..."
              disabled={loading}
              rows={1}
              onInput={(e) => {
                e.target.style.height = 'auto';
                e.target.style.height = Math.min(e.target.scrollHeight, 150) + 'px';
              }}
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
      {/* O8: PDF preview side panel */}
      {pdfPanel && (
        <PdfPanel
          source={pdfPanel.source}
          page={pdfPanel.page}
          onClose={() => setPdfPanel(null)}
          apiUrl={config.API_URL}
        />
      )}
      </div>

      {/* Settings Modal */}
      {settingsOpen && (
        <div className="settings-overlay" onClick={() => setSettingsOpen(false)}>
          <div className="settings-modal" onClick={(e) => e.stopPropagation()}>
            <div className="settings-header">
              <h2>Settings</h2>
              <button className="settings-close" onClick={() => setSettingsOpen(false)}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M18 6 6 18" /><path d="m6 6 12 12" />
                </svg>
              </button>
            </div>
            <div className="settings-body">
              <div className="settings-section">
                <h3>Account</h3>
                <div className="settings-field">
                  <label>Name</label>
                  <div className="settings-value">{user.name}</div>
                </div>
                <div className="settings-field">
                  <label>Email</label>
                  <div className="settings-value">{user.email}</div>
                </div>
                <div className="settings-field">
                  <label>Account Type</label>
                  <div className="settings-value">{user.account_type === 'healthcare_professional' ? 'Healthcare Professional' : 'General User'}</div>
                </div>
              </div>
              <div className="settings-section">
                <h3>Appearance</h3>
                <div className="settings-field">
                  <label>Theme</label>
                  <div className="settings-toggle-row">
                    <button
                      className={`settings-theme-btn${theme === 'dark' ? ' active' : ''}`}
                      onClick={() => setTheme('dark')}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" />
                      </svg>
                      Dark
                    </button>
                    <button
                      className={`settings-theme-btn${theme === 'light' ? ' active' : ''}`}
                      onClick={() => setTheme('light')}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <circle cx="12" cy="12" r="5" />
                        <line x1="12" y1="1" x2="12" y2="3" /><line x1="12" y1="21" x2="12" y2="23" />
                        <line x1="4.22" y1="4.22" x2="5.64" y2="5.64" /><line x1="18.36" y1="18.36" x2="19.78" y2="19.78" />
                        <line x1="1" y1="12" x2="3" y2="12" /><line x1="21" y1="12" x2="23" y2="12" />
                        <line x1="4.22" y1="19.78" x2="5.64" y2="18.36" /><line x1="18.36" y1="5.64" x2="19.78" y2="4.22" />
                      </svg>
                      Light
                    </button>
                  </div>
                </div>
              </div>
              <div className="settings-section">
                <h3>About</h3>
                <div className="settings-field">
                  <label>Version</label>
                  <div className="settings-value">MedicaLLM v1.0.0</div>
                </div>
                <div className="settings-field">
                  <label>Drug Database</label>
                  <div className="settings-value">DrugBank 5.1 — 17,430 drugs</div>
                </div>
                <div className="settings-field">
                  <label>Research</label>
                  <div className="settings-value">PubMed with confidence scoring</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default Chat;
