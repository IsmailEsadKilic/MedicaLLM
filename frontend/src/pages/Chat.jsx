import { useState, useRef, useEffect, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import config from '../api/config';
import PdfPanel from './PdfPanel';
import DrugMatrix from './DrugMatrix';
import Dashboard from './doctor/Dashboard';
import DoctorPatients from './doctor/DoctorPatients';
import PatientDetail from './doctor/PatientDetail';
import Research from './doctor/Research';
import { DoctorPanelContext } from './doctor/panelContext';
import MarkdownWithReferences from '../components/MarkdownWithReferences';
import ConfidenceBreakdown from '../components/ConfidenceBreakdown';
import LoadingScreen from '../components/LoadingScreen';
import '../App.css';
import './doctor/DoctorPanel.css';
import './doctor/DoctorPages.css';
import './doctor/Research.css';

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
  // Developer mode — when off, the per-message Debug Info button is hidden.
  // Persisted to localStorage so power users don't have to re-enable on every
  // tab. Defaults to false (most users never need the raw tool dumps).
  const [developerMode, setDeveloperMode] = useState(() => {
    try {
      return localStorage.getItem('medicallm.developerMode') === 'true';
    } catch {
      return false;
    }
  });
  const toggleDeveloperMode = () => {
    setDeveloperMode((prev) => {
      const next = !prev;
      try {
        localStorage.setItem('medicallm.developerMode', next ? 'true' : 'false');
      } catch {
        // localStorage may be unavailable (private mode quotas, etc.) —
        // the in-memory state still flips for the current session.
      }
      return next;
    });
  };
  const [showSources, setShowSources] = useState({});
  const [isListening, setIsListening] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [thinkingStep, setThinkingStep] = useState('');
  // O8: PDF preview side panel — { source: string, page: number } | null
  const [pdfPanel, setPdfPanel] = useState(null);
  // O11: In-page views — embed the entire doctor panel inside /chat.
  // 'chat' is the messaging view; everything else swaps the main area.
  const [activeView, setActiveView] = useState('chat'); // 'chat' | 'dashboard' | 'patients' | 'patient-detail' | 'drug-matrix' | 'research'
  const [viewParams, setViewParams] = useState({});     // { patientId?, addPatient? }
  // Cache of all the doctor's patients (used by Dashboard / Patients pages
  // and the in-chat patient selector). Lazy-loaded once per session.
  const [doctorPatients, setDoctorPatients] = useState(null);
  // O10: Patient-aware responses — patient list and the currently selected patient
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const messagesEndRef = useRef(null);
  const messagesContainerRef = useRef(null);
  const recognitionRef = useRef(null);
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();

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
    if (!user || !user.isDoctor) return;
    const fetchPatients = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${config.API_URL}/api/users/doctors/patients`, {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          const list = Array.isArray(data) ? data : [];
          setPatients(list);
          setDoctorPatients(list); // shared with embedded doctor panel
          // Auto-select patient from URL param (e.g. /doctor/chat?patient=xyz)
          const patientParam = searchParams.get('patient');
          if (patientParam && list.length > 0) {
            const match = list.find(p => p.patient_id === patientParam || p.user_id === patientParam);
            if (match) setSelectedPatient(match);
          }
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

      // Audit F10: previously a 401 would still try to parse the JSON body
      // and silently leave the user on a broken Chat screen. Forward to the
      // login page when the token is rejected.
      if (response.status === 401) {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        navigate('/login');
        return;
      }
      if (!response.ok) {
        // Non-fatal — just leave the conversations list empty and let the
        // user retry. Avoids dumping internal server errors into the UI.
        setChats([]);
        return;
      }

      const data = await response.json();
      const conversations = data.conversations || [];

      setChats(conversations.map(c => ({
        id: c.conversation_id,
        title: c.title,
        messages: c.messages || []
      })));
    } catch {
      // Network failure — leave the chat list empty rather than crashing.
      setChats([]);
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

  // Smart auto-scroll: only scroll to bottom if user is already near the bottom
  useEffect(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    // Check if user is near the bottom (within 100px threshold)
    const isNearBottom = container.scrollHeight - container.scrollTop - container.clientHeight < 100;
    
    // Only auto-scroll if user hasn't manually scrolled up
    if (isNearBottom) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
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
      
      // Send query to agent via SSE streaming endpoint
      const response = await fetch(`${config.API_URL}/api/session/query-stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          query: query,
          conversation_id: chatId,
          // O10: pass patient context for dynamic system prompt
          patient_id: selectedPatient ? selectedPatient.patient_id : null,
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
      let toolExecutions = [];  // Comprehensive tool execution data
      let debugInfo = {};

      setIsStreaming(true);
      setStreamingContent('');
      setThinkingStep('');

      // Parse the SSE stream with improved error handling.
      //
      // Audit F3: when the backend ends the stream without a trailing "\n\n"
      // (e.g. it flushed the final `done` event right before closing the
      // socket), the previous loop kept the last event in `buffer` and never
      // processed it. We now drain `buffer` once the reader signals end-of-
      // stream by appending a synthetic terminator and reusing the same
      // parsing block.
      //
      // We also extract the per-line parser into a single closure so the
      // EOF flush path executes the *same* code as the streaming path —
      // there's no second copy to drift out of sync.

      const handleChunk = (chunk) => {
        if (chunk.type === 'thinking') {
          setThinkingStep(chunk.step || '');
        } else if (chunk.type === 'content') {
          setThinkingStep('');
          accumulatedContent += chunk.content;
          setStreamingContent(accumulatedContent);
        } else if (chunk.type === 'tool_start') {
          const toolName = chunk.tool_name || 'unknown';
          setThinkingStep(`Using ${toolName}...`);
        } else if (chunk.type === 'tool_end') {
          setThinkingStep('');
        } else if (chunk.type === 'done') {
          sources = chunk.sources || [];
          toolExecutions = chunk.tool_executions || [];
          debugInfo = {
            execution_time_ms: chunk.execution_time_ms,
            debug: chunk.debug,
          };
          if (chunk.final_content) {
            accumulatedContent = chunk.final_content;
            setStreamingContent(accumulatedContent);
          }
        } else if (chunk.type === 'error') {
          throw new Error(chunk.error || 'Streaming error');
        }
      };

      const drainEvents = (chunks) => {
        for (const event of chunks) {
          if (!event.trim()) continue;
          for (const line of event.split('\n')) {
            if (!line.startsWith('data: ')) continue;
            try {
              const parsed = JSON.parse(line.slice(6));
              handleChunk(parsed);
            } catch (parseErr) {
              // Continue processing other chunks; an early-truncated chunk
              // shouldn't block the rest of the stream.
              // eslint-disable-next-line no-console
              console.warn('Failed to parse SSE chunk:', line, parseErr);
            }
          }
        }
      };

      try {
        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          buffer += decoder.decode(value, { stream: true });
          const events = buffer.split('\n\n');
          buffer = events.pop() || '';

          drainEvents(events);
        }

        // Flush any tail event that wasn't terminated with "\n\n".
        if (buffer.trim()) {
          drainEvents([buffer]);
          buffer = '';
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
        tool_executions: toolExecutions,  // Comprehensive tool execution data
        sources: sources,
        debug: debugInfo,
      };

      // Debug logging removed for production (audit F8). Re-enable behind
      // a feature flag if needed during local debugging.
      setChats(prev => prev.map(c =>
        c.id === chatId ? { ...c, messages: [...c.messages, botMessage] } : c
      ));
      setStreamingContent('');
      setIsStreaming(false);
      setThinkingStep('');

      // Generate title using LLM AFTER the response is complete
      if (isFirstMessage && accumulatedContent) {
        fetch(`${config.API_URL}/api/session/generate-title`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          },
          body: JSON.stringify({ conversation_id: chatId })
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
  if (loadingChats) return <LoadingScreen message="Preparing your workspace" />;

  // In-page navigation for the embedded doctor panel views.
  const navigateTo = (view, params = {}) => {
    if (view === 'chat') {
      // Honor an incoming patient context from the doctor panel.
      if (params.patientId) {
        const match = (doctorPatients || []).find(p => p.patient_id === params.patientId);
        if (match) setSelectedPatient(match);
        setCurrentChatId(null); // start a fresh chat for this consult
      }
      setActiveView('chat');
      setViewParams(params);
      return;
    }
    setActiveView(view);
    setViewParams(params);
  };

  const panelValue = {
    user,
    patients: doctorPatients,
    setPatients: setDoctorPatients,
    viewParams,
    navigateTo,
  };

  return (
    <DoctorPanelContext.Provider value={panelValue}>
    <div className={`doctor-panel ${theme}`}>
      <aside className={`doctor-sidebar ${sidebarOpen ? '' : 'collapsed'}`}>
        <div className="doctor-sidebar-header">
          <button className="sidebar-toggle" onClick={() => setSidebarOpen(!sidebarOpen)} aria-label="Toggle sidebar">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              {sidebarOpen ? (
                <><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></>
              ) : (
                <><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></>
              )}
            </svg>
          </button>
        </div>

        <nav className="doctor-nav">
          {user.isDoctor && (
            <button
              className={`doctor-nav-item ${activeView === 'dashboard' ? 'active' : ''}`}
              onClick={() => navigateTo('dashboard')}
              title={!sidebarOpen ? 'Dashboard' : undefined}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
                <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
              </svg>
              {sidebarOpen && <span>Dashboard</span>}
            </button>
          )}
          {user.isDoctor && (
            <button
              className={`doctor-nav-item ${(activeView === 'patients' || activeView === 'patient-detail') ? 'active' : ''}`}
              onClick={() => navigateTo('patients')}
              title={!sidebarOpen ? 'Patients' : undefined}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/>
                <path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/>
              </svg>
              {sidebarOpen && <span>Patients</span>}
            </button>
          )}
          <button
            className={`doctor-nav-item ${activeView === 'chat' ? 'active' : ''}`}
            onClick={() => navigateTo('chat')}
            title={!sidebarOpen ? 'AI Chat' : undefined}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
            </svg>
            {sidebarOpen && <span>AI Chat</span>}
          </button>
          <button
            className={`doctor-nav-item ${activeView === 'drug-matrix' ? 'active' : ''}`}
            onClick={() => navigateTo('drug-matrix')}
            title={!sidebarOpen ? 'Drug Matrix' : undefined}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
              <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
            </svg>
            {sidebarOpen && <span>Drug Matrix</span>}
          </button>
          {user.isDoctor && (
            <button
              className={`doctor-nav-item ${activeView === 'research' ? 'active' : ''}`}
              onClick={() => navigateTo('research')}
              title={!sidebarOpen ? 'Research' : undefined}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
              </svg>
              {sidebarOpen && <span>Research</span>}
            </button>
          )}

          {/* Conversation history lives directly in the sidebar, below Research. */}
          {sidebarOpen && (
            <div className="sidebar-chat-list">
              <button
                className="new-chat sidebar-new-chat"
                onClick={() => { navigateTo('chat'); createNewChat(); }}
              >
                <span>+</span> New chat
              </button>
              <div className="chat-history">
                {chats.map(chat => (
                  <div
                    key={chat.id}
                    className={`chat-item ${activeView === 'chat' && chat.id === currentChatId ? 'active' : ''}`}
                    onClick={() => { setCurrentChatId(chat.id); navigateTo('chat'); }}
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
            </div>
          )}
        </nav>

        <div className="doctor-sidebar-footer">
          <div className="doctor-footer-row">
            <div
              className={`doctor-user-info clickable ${sidebarOpen ? '' : 'collapsed'} ${profileMenuOpen ? 'active' : ''}`}
              onClick={() => setProfileMenuOpen(!profileMenuOpen)}
              role="button"
              tabIndex={0}
              title={!sidebarOpen ? user.name : undefined}
            >
              <div className="doctor-avatar">{user.name?.charAt(0).toUpperCase()}</div>
              {sidebarOpen && (
                <div className="doctor-user-details">
                  <span className="doctor-user-name">{user.name}</span>
                  <span className="doctor-user-role">{user.isDoctor ? 'Doctor' : 'User'}</span>
                </div>
              )}
              {sidebarOpen && (
                <svg
                  className="user-info-chevron"
                  width="14" height="14" viewBox="0 0 24 24"
                  fill="none" stroke="currentColor" strokeWidth="2"
                  strokeLinecap="round" strokeLinejoin="round"
                >
                  <polyline points="6 9 12 15 18 9" />
                </svg>
              )}
            </div>
            {sidebarOpen && (
              <label className="theme-toggle-mini" title="Toggle theme">
                <input
                  type="checkbox"
                  checked={theme === 'dark'}
                  onChange={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                />
                <span className="slider-mini"></span>
              </label>
            )}
          </div>
          {profileMenuOpen && (
            <div className="profile-dropdown sidebar-profile-dropdown">
              <div className="dropdown-user-info">
                <div className="dropdown-avatar">{user.name.charAt(0).toUpperCase()}</div>
                <div>
                  <div className="dropdown-name">{user.name}</div>
                  <div className="dropdown-email">{user.email}</div>
                  <div className="dropdown-role">{user.isDoctor ? 'Healthcare Professional' : 'General User'}</div>
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
      </aside>

      <div className={`chat-content-area${pdfPanel ? ' pdf-panel-open' : ''}`} style={{ flex: 1, display: 'flex', minWidth: 0 }}>
      <div className="main">
        <div className="header">
          <div className="header-left">
            <h2 className="chat-header-title">MedicaLLM</h2>
          </div>
          {/* O10: Patient context selector — visible only for healthcare professionals */}
          {user && user.isDoctor && (
            <div className="patient-selector">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ flexShrink: 0 }}>
                <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2" />
                <circle cx="9" cy="7" r="4" />
              </svg>
              <select
                className="patient-select"
                value={selectedPatient ? selectedPatient.patient_id : ''}
                onChange={(e) => {
                  const pid = e.target.value;
                  setSelectedPatient(pid ? patients.find(p => p.patient_id === pid) || null : null);
                }}
                title="Select an active patient for context-aware responses"
              >
                <option value="">No patient selected</option>
                {patients.map(p => (
                  <option key={p.patient_id} value={p.patient_id}>{p.name}</option>
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
          </div>
        </div>
        {activeView !== 'chat' ? (
          activeView === 'drug-matrix' ? (
            <DrugMatrix
              user={user}
              initialPatientId={selectedPatient ? selectedPatient.patient_id : null}
            />
          ) : (
            <div className="doctor-main" style={{ flex: 1, overflowY: 'auto', padding: '24px 32px', minWidth: 0 }}>
              {activeView === 'dashboard' && <Dashboard />}
              {activeView === 'patients' && <DoctorPatients />}
              {activeView === 'patient-detail' && <PatientDetail />}
              {activeView === 'research' && <Research />}
            </div>
          )
        ) : (
          <>
        <div className="messages" ref={messagesContainerRef}>
          {!currentChatId || currentChat?.messages.length === 0 ? (
            <div className="empty-state">
              <h1>{selectedPatient ? `Consulting for ${selectedPatient.name}` : 'How can I help you today?'}</h1>
              <div className="suggestions">
                {selectedPatient ? (
                  <>
                    <button className="suggestion" onClick={() => setInput(`Summarize ${selectedPatient.name}'s medication profile and flag any concerns`)}>
                      📋 Summarize medication profile
                    </button>
                    <button className="suggestion" onClick={() => setInput(`Check all drug interactions for this patient's current medications`)}>
                      ⚠️ Check all interactions
                    </button>
                    <button className="suggestion" onClick={() => setInput(`Are there any safer alternatives for this patient's medications?`)}>
                      💊 Suggest alternatives
                    </button>
                    <button className="suggestion" onClick={() => setInput(`What should I monitor given this patient's conditions and medications?`)}>
                      🔍 Monitoring recommendations
                    </button>
                    <button className="suggestion" onClick={() => setInput(`Are any of this patient's medications contraindicated with their conditions or allergies?`)}>
                      🚫 Check contraindications
                    </button>
                    <button className="suggestion" onClick={() => setInput(`Recommend lifestyle and dietary advice tailored to this patient`)}>
                      🥗 Lifestyle recommendations
                    </button>
                  </>
                ) : (
                  <>
                    <button className="suggestion" onClick={() => setInput('What can I do during a hypertension episode?')}>
                      What can I do during a hypertension episode?
                    </button>
                    <button className="suggestion" onClick={() => setInput('Do Warfarin and Ibuprofen interact?')}>
                      Do Warfarin and Ibuprofen interact?
                    </button>
                    <button className="suggestion" onClick={() => setInput('Tell me about Aspirin')}>
                      Tell me about Aspirin
                    </button>
                    <button className="suggestion" onClick={() => setInput('Search PubMed for SGLT2 inhibitors in heart failure')}>
                      Search PubMed for SGLT2 inhibitors
                    </button>
                    <button className="suggestion" onClick={() => setInput('What are common side effects of Metformin?')}>
                      Side effects of Metformin?
                    </button>
                    <button className="suggestion" onClick={() => setInput('Compare ACE inhibitors vs ARBs for hypertension')}>
                      ACE inhibitors vs ARBs?
                    </button>
                  </>
                )}
              </div>
            </div>
          ) : (
            currentChat?.messages.map((msg, i) => (
              <div key={`${msg.timestamp}-${i}`} className={`message ${msg.role}`}>
                <div className="message-inner">
                  <div className="avatar">{msg.role === 'user' ? 'U' : 'AI'}</div>
                  <div className="content">
                    {msg.role === 'assistant' ? (
                      <>
                        {(() => {
                          // ── Reference numbering (display-only) ─────────────
                          // The agent allocates a per-request monotonic REF
                          // counter across every tool call, so a response
                          // that ends up citing only the last tool's outputs
                          // can legitimately use [22], [23], [24]. We compute
                          // a 1-based display map here so the inline badges
                          // and the source cards both show [1], [2], [3] in
                          // the order they first appear in the response.
                          // The original REF ids stay intact in `source.ref`
                          // (used for backend correlation and debug logs).
                          const sources = Array.isArray(msg.sources) ? msg.sources : [];
                          const citationPattern = /[\[【](?:REF)?\s*(\d+(?:\s*,\s*(?:REF)?\s*\d+)*)\s*[\]】]/gi;
                          // First-occurrence order of every original REF the
                          // model actually cited, so [22, 23, 7] becomes
                          // {22→1, 23→2, 7→3}.
                          const firstOrderRefs = [];
                          const seen = new Set();
                          let citationMatch;
                          while ((citationMatch = citationPattern.exec(msg.content || '')) !== null) {
                            citationMatch[1].split(',').forEach((s) => {
                              const n = parseInt(s.replace(/REF/gi, '').trim(), 10);
                              if (!Number.isNaN(n) && !seen.has(n)) {
                                seen.add(n);
                                firstOrderRefs.push(n);
                              }
                            });
                          }
                          const displayMap = {};
                          firstOrderRefs.forEach((origNum, idx) => {
                            displayMap[origNum] = idx + 1;
                          });
                          // Filter sources to only those actually cited and
                          // sort by their display order so card #N matches
                          // citation [N] in the text.
                          const filteredSources = seen.size > 0
                            ? sources
                                .filter((s) => {
                                  if (s.ref) {
                                    const m = String(s.ref).match(/(\d+)/);
                                    const refNum = m ? parseInt(m[1], 10) : null;
                                    return refNum !== null && seen.has(refNum);
                                  }
                                  return true; // non-PubMed sources always shown
                                })
                                .sort((a, b) => {
                                  const na = parseInt(String(a.ref || '').match(/(\d+)/)?.[1] ?? '0', 10);
                                  const nb = parseInt(String(b.ref || '').match(/(\d+)/)?.[1] ?? '0', 10);
                                  return (displayMap[na] ?? 9999) - (displayMap[nb] ?? 9999);
                                })
                            : sources;

                          return (
                            <>
                              <MarkdownWithReferences
                                content={msg.content}
                                sources={filteredSources}
                                displayMap={displayMap}
                                onSourceClick={(source, index) => {
                            const sourceElement = document.getElementById(`source-${i}-${index}`);
                            
                            // For DrugBank/database sources, scroll to and highlight the source card
                            // For PubMed sources, just highlight without scrolling (PDF opens in place)
                            const isDatabaseSource = source.source_type === 'database' || 
                                                    source.source === 'DrugBank' || 
                                                    source.source === 'DrugBank Interaction' ||
                                                    !source.pmid;
                            
                            if (isDatabaseSource) {
                              // Expand the sources section if not already expanded
                              if (!showSources[i]) {
                                setShowSources({ ...showSources, [i]: true });
                              }
                              
                              // Scroll after a brief delay to allow the section to expand
                              setTimeout(() => {
                                const elem = document.getElementById(`source-${i}-${index}`);
                                if (elem) {
                                  elem.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                                  elem.classList.add('highlighted');
                                  setTimeout(() => elem.classList.remove('highlighted'), 1000);
                                }
                              }, 100);
                            } else if (sourceElement) {
                              // For PubMed sources, just highlight without scrolling
                              sourceElement.classList.add('highlighted');
                              setTimeout(() => sourceElement.classList.remove('highlighted'), 1000);
                            }
                            
                            // Open PDF if available
                            if (source.pmid) {
                              const doi = source.doi || '';
                              const pmcId = source.pmc_id || '';
                              let pdfUrl = `${config.API_URL}/api/pubmed/pdf/${source.pmid}`;
                              const params = [];
                              if (doi) params.push(`doi=${encodeURIComponent(doi)}`);
                              if (pmcId) params.push(`pmc_id=${encodeURIComponent(pmcId)}`);
                              if (params.length > 0) pdfUrl += `?${params.join('&')}`;
                              
                              // Pass article data if available to avoid redundant API call
                              const articleData = source.abstract ? {
                                pmid: source.pmid,
                                title: source.title,
                                abstract: source.abstract,
                                authors: source.authors || [],
                                journal: source.journal || '',
                                publication_date: source.publication_date || '',
                                doi: source.doi || '',
                                pmc_id: source.pmc_id || '',
                                citation_count: source.citation_count || 0,
                                confidence_score: source.confidence_score || 0,
                                pubmed_url: source.pubmed_url || `https://pubmed.ncbi.nlm.nih.gov/${source.pmid}/`,
                                doi_url: source.doi_url || (source.doi ? `https://doi.org/${source.doi}` : ''),
                              } : null;
                              
                              setPdfPanel({
                                source: pdfUrl,
                                page: 1,
                                articleData: articleData
                              });
                            }
                          }}
                              />
                              {filteredSources.length > 0 && (
                          <div className="sources-section">
                            <button
                              className="sources-toggle"
                              onClick={() => setShowSources({ ...showSources, [i]: !showSources[i] })}
                            >
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"
                                style={{ transform: showSources[i] ? 'rotate(90deg)' : 'rotate(0deg)', transition: 'transform 0.2s' }}>
                                <polyline points="9 18 15 12 9 6" />
                              </svg>
                              Sources ({filteredSources.length})
                            </button>
                            {showSources[i] && (
                            <div className="sources-list-rich">
                              {filteredSources.map((source, idx) => {
                                // Use the 1-based display number we computed
                                // earlier so the card label matches the [N]
                                // the user sees inline in the text. Falls
                                // back to the original ref number, then to
                                // position (handles non-PubMed sources that
                                // don't carry a ref id).
                                const refMatch = String(source.ref || '').match(/(\d+)/);
                                const origRefNum = refMatch ? parseInt(refMatch[1], 10) : null;
                                const displayRefNum =
                                  origRefNum !== null && displayMap[origRefNum] !== undefined
                                    ? displayMap[origRefNum]
                                    : (origRefNum ?? idx + 1);
                                const isPdf = (source.source &&
                                  source.source.toLowerCase().endsWith('.pdf')) ||
                                  !!source.pdf_path;
                                const pdfSource = source.pdf_path || source.source;
                                const pageNum = source.page ? parseInt(source.page, 10) : 1;
                                const isActive = pdfPanel &&
                                  pdfPanel.source === pdfSource &&
                                  pdfPanel.page === pageNum;
                                const hasPubMedLink = !!source.pmid;
                                const hasConfidence = source.confidence_score !== undefined;
                                return (
                                  <div key={idx} className="source-card" id={`source-${i}-${idx}`}>
                                    <div className="source-card-header">
                                      <span className="source-card-num">{displayRefNum}</span>
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
                                      {source.citation_count !== undefined && source.citation_count > 0 && (
                                        <span className="source-citations">{source.citation_count} citations</span>
                                      )}
                                      {source.page && (
                                        <span className="source-page">Page {source.page}</span>
                                      )}
                                    </div>
                                    {source.content && (
                                      <div className="source-card-snippet">{source.content}</div>
                                    )}
                                    <div className="source-card-actions">
                                      {source.pmid && (
                                        <button
                                          className={`view-source-btn${isActive ? ' active' : ''}`}
                                          onClick={() => {
                                            if (isActive) {
                                              setPdfPanel(null);
                                            } else {
                                              const doi = source.doi || '';
                                              const pmcId = source.pmc_id || '';
                                              let pdfUrl = `${config.API_URL}/api/pubmed/pdf/${source.pmid}`;
                                              const params = [];
                                              if (doi) params.push(`doi=${encodeURIComponent(doi)}`);
                                              if (pmcId) params.push(`pmc_id=${encodeURIComponent(pmcId)}`);
                                              if (params.length > 0) pdfUrl += `?${params.join('&')}`;
                                              
                                              // Pass article data if available to avoid redundant API call
                                              const articleData = source.abstract ? {
                                                pmid: source.pmid,
                                                title: source.title,
                                                abstract: source.abstract,
                                                authors: source.authors || [],
                                                journal: source.journal || '',
                                                publication_date: source.publication_date || '',
                                                doi: source.doi || '',
                                                pmc_id: source.pmc_id || '',
                                                citation_count: source.citation_count || 0,
                                                confidence_score: source.confidence_score || 0,
                                                pubmed_url: source.pubmed_url || `https://pubmed.ncbi.nlm.nih.gov/${source.pmid}/`,
                                                doi_url: source.doi_url || (source.doi ? `https://doi.org/${source.doi}` : ''),
                                              } : null;
                                              
                                              // Open PDF panel - it will handle fallback to abstract if PDF not available
                                              setPdfPanel({ source: pdfUrl, page: 1, articleData: articleData });
                                            }
                                          }}
                                        >
                                          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                            <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                                            <polyline points="14 2 14 8 20 8" />
                                          </svg>
                                          {isActive ? 'Close' : 'View Article'}
                                        </button>
                                      )}
                                      {hasPubMedLink && (
                                        <a
                                          className="view-source-btn"
                                          href={`https://pubmed.ncbi.nlm.nih.gov/${source.pmid}/`}
                                          target="_blank"
                                          rel="noopener noreferrer"
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
                                    
                                    {/* Confidence Score Breakdown */}
                                    {source.confidence_breakdown && (
                                      <ConfidenceBreakdown 
                                        breakdown={source.confidence_breakdown}
                                        overallScore={source.confidence_score || 0}
                                        article={source}
                                      />
                                    )}
                                  </div>
                                );
                              })}
                            </div>
                            )}
                          </div>
                          )}
                            </>
                          );
                        })()}
                        {/* Debug Info Section — only visible when the user
                            opted into developer mode in Settings (audit F8:
                            console logging is off; the panel itself still
                            surfaces the same data for power users). */}
                        {msg.role === 'assistant' && developerMode && (() => {
                          const hasDebugInfo = (
                            (msg.tool_executions && msg.tool_executions.length > 0) || 
                            (msg.tools_used && msg.tools_used.length > 0) ||  // Legacy support
                            (msg.sources && msg.sources.length > 0) ||
                            msg.debug
                          );
                          
                          if (!hasDebugInfo) return null;
                          
                          return (
                          <div style={{ marginTop: '10px' }}>
                            <button
                              onClick={() => setShowDebug({ ...showDebug, [i]: !showDebug[i] })}
                              style={{
                                background: 'rgba(255,255,255,0.1)',
                                border: '1px solid rgba(255,255,255,0.2)',
                                borderRadius: '4px',
                                padding: '6px 12px',
                                fontSize: '12px',
                                cursor: 'pointer',
                                color: 'inherit',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '6px',
                                fontWeight: '500',
                              }}
                            >
                              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                <circle cx="12" cy="12" r="10" />
                                <line x1="12" y1="16" x2="12" y2="12" />
                                <line x1="12" y1="8" x2="12.01" y2="8" />
                              </svg>
                              {showDebug[i] ? 'Hide' : 'Show'} Debug Info
                              {msg.tool_executions && msg.tool_executions.length > 0 && (
                                <span style={{
                                  background: 'rgba(96,165,250,0.2)',
                                  padding: '2px 6px',
                                  borderRadius: '3px',
                                  fontSize: '11px',
                                  fontWeight: 'bold',
                                }}>
                                  {msg.tool_executions.length} tool{msg.tool_executions.length !== 1 ? 's' : ''}
                                </span>
                              )}
                            </button>
                            {showDebug[i] && (
                              <div style={{
                                marginTop: '10px',
                                padding: '16px',
                                background: 'rgba(0,0,0,0.3)',
                                borderRadius: '8px',
                                fontSize: '13px',
                                fontFamily: 'monospace',
                                border: '1px solid rgba(255,255,255,0.15)',
                              }}>
                                {/* Comprehensive Tool Executions Section */}
                                {msg.tool_executions && msg.tool_executions.length > 0 && (
                                  <div style={{ marginBottom: '16px' }}>
                                    <div style={{ 
                                      fontWeight: 'bold', 
                                      marginBottom: '12px',
                                      color: '#60a5fa',
                                      fontSize: '15px',
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: '8px',
                                    }}>
                                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z" />
                                      </svg>
                                      Tool Executions ({msg.tool_executions.length})
                                    </div>
                                    {msg.tool_executions.map((toolExec, toolIdx) => (
                                      <div key={toolIdx} style={{
                                        marginBottom: '12px',
                                        padding: '12px',
                                        background: 'rgba(255,255,255,0.05)',
                                        borderRadius: '6px',
                                        borderLeft: '4px solid #60a5fa',
                                      }}>
                                        {/* Tool Header */}
                                        <div style={{ 
                                          display: 'flex',
                                          justifyContent: 'space-between',
                                          alignItems: 'center',
                                          marginBottom: '8px',
                                        }}>
                                          <div style={{ 
                                            fontWeight: 'bold',
                                            color: '#93c5fd',
                                            fontSize: '14px',
                                          }}>
                                            {toolIdx + 1}. {toolExec.tool_name}
                                          </div>
                                          {toolExec.execution_time_ms && (
                                            <div style={{
                                              fontSize: '11px',
                                              color: '#fcd34d',
                                              background: 'rgba(251,191,36,0.15)',
                                              padding: '3px 8px',
                                              borderRadius: '4px',
                                              fontWeight: 'bold',
                                            }}>
                                              ⚡ {toolExec.execution_time_ms.toFixed(0)}ms
                                            </div>
                                          )}
                                        </div>
                                        
                                        {/* Tool Arguments */}
                                        {toolExec.tool_args && Object.keys(toolExec.tool_args).length > 0 && (
                                          <div style={{ marginBottom: '8px' }}>
                                            <div style={{ 
                                              fontSize: '11px', 
                                              color: '#9ca3af',
                                              marginBottom: '4px',
                                              fontWeight: 'bold',
                                            }}>
                                              📥 Input Parameters:
                                            </div>
                                            <pre style={{ 
                                              margin: 0,
                                              whiteSpace: 'pre-wrap',
                                              wordBreak: 'break-word',
                                              fontSize: '11px',
                                              color: '#d1d5db',
                                              padding: '8px',
                                              background: 'rgba(0,0,0,0.4)',
                                              borderRadius: '4px',
                                              maxHeight: '150px',
                                              overflow: 'auto',
                                            }}>
                                              {JSON.stringify(toolExec.tool_args, null, 2)}
                                            </pre>
                                          </div>
                                        )}
                                        
                                        {/* Tool Result */}
                                        {toolExec.tool_result && (
                                          <div style={{ marginBottom: '8px' }}>
                                            <div style={{ 
                                              fontSize: '11px', 
                                              color: '#9ca3af',
                                              marginBottom: '4px',
                                              fontWeight: 'bold',
                                            }}>
                                              📤 Output:
                                            </div>
                                            <pre style={{ 
                                              margin: 0,
                                              whiteSpace: 'pre-wrap',
                                              wordBreak: 'break-word',
                                              fontSize: '11px',
                                              color: '#d1d5db',
                                              maxHeight: '500px',
                                              overflow: 'auto',
                                              padding: '8px',
                                              background: 'rgba(0,0,0,0.4)',
                                              borderRadius: '4px',
                                            }}>
                                              {typeof toolExec.tool_result === 'string' 
                                                ? toolExec.tool_result
                                                : JSON.stringify(toolExec.tool_result, null, 2)
                                              }
                                            </pre>
                                          </div>
                                        )}
                                        
                                        {/* Error Display */}
                                        {toolExec.error && (
                                          <div style={{
                                            marginTop: '8px',
                                            padding: '8px',
                                            background: 'rgba(239,68,68,0.15)',
                                            borderRadius: '4px',
                                            borderLeft: '3px solid #ef4444',
                                          }}>
                                            <div style={{ 
                                              fontSize: '11px', 
                                              color: '#fca5a5',
                                              fontWeight: 'bold',
                                              marginBottom: '4px',
                                            }}>
                                              ⚠️ Error:
                                            </div>
                                            <div style={{ 
                                              fontSize: '11px',
                                              color: '#fecaca',
                                            }}>
                                              {toolExec.error}
                                            </div>
                                          </div>
                                        )}
                                        
                                        {/* Timestamp */}
                                        {toolExec.timestamp && (
                                          <div style={{
                                            marginTop: '8px',
                                            fontSize: '10px',
                                            color: '#6b7280',
                                          }}>
                                            🕐 {new Date(toolExec.timestamp).toLocaleString()}
                                          </div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                )}
                                
                                {/* Legacy tools_used support */}
                                {(!msg.tool_executions || msg.tool_executions.length === 0) && msg.tools_used && msg.tools_used.length > 0 && (
                                  <div style={{ marginBottom: '12px' }}>
                                    <div style={{ 
                                      fontWeight: 'bold', 
                                      marginBottom: '8px',
                                      color: '#60a5fa',
                                      fontSize: '14px'
                                    }}>
                                      🔧 Tools Used (Legacy) ({msg.tools_used.length})
                                    </div>
                                    {msg.tools_used.map((tool, toolIdx) => (
                                      <div key={toolIdx} style={{
                                        marginBottom: '8px',
                                        padding: '8px',
                                        background: 'rgba(255,255,255,0.05)',
                                        borderRadius: '4px',
                                        borderLeft: '3px solid #60a5fa'
                                      }}>
                                        <div style={{ 
                                          fontWeight: 'bold',
                                          color: '#93c5fd',
                                          marginBottom: '4px'
                                        }}>
                                          {toolIdx + 1}. {tool}
                                        </div>
                                        {msg.tool_results && msg.tool_results[toolIdx] && (
                                          <div style={{ marginTop: '6px' }}>
                                            <div style={{ 
                                              fontSize: '11px', 
                                              color: '#9ca3af',
                                              marginBottom: '4px'
                                            }}>
                                              Result:
                                            </div>
                                            <pre style={{ 
                                              margin: 0,
                                              whiteSpace: 'pre-wrap',
                                              wordBreak: 'break-word',
                                              fontSize: '12px',
                                              color: '#d1d5db',
                                              maxHeight: '400px',
                                              overflow: 'auto',
                                              padding: '6px',
                                              background: 'rgba(0,0,0,0.3)',
                                              borderRadius: '3px'
                                            }}>
                                              {typeof msg.tool_results[toolIdx] === 'string' 
                                                ? msg.tool_results[toolIdx]
                                                : JSON.stringify(msg.tool_results[toolIdx], null, 2)
                                              }
                                            </pre>
                                          </div>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                )}

                                {/* Sources Summary */}
                                {msg.sources && msg.sources.length > 0 && (
                                  <div style={{ marginBottom: '12px' }}>
                                    <div style={{ 
                                      fontWeight: 'bold',
                                      color: '#34d399',
                                      marginBottom: '8px',
                                      fontSize: '15px',
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: '8px',
                                    }}>
                                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20" />
                                        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z" />
                                      </svg>
                                      Sources Summary
                                    </div>
                                    <div style={{
                                      padding: '10px',
                                      background: 'rgba(52,211,153,0.1)',
                                      borderRadius: '6px',
                                      borderLeft: '4px solid #34d399'
                                    }}>
                                      <div style={{ color: '#6ee7b7', marginBottom: '6px' }}>
                                        📊 Total: {msg.sources.length} source{msg.sources.length !== 1 ? 's' : ''}
                                      </div>
                                      {msg.sources.filter(s => s.pmid).length > 0 && (
                                        <div style={{ color: '#6ee7b7', fontSize: '12px', marginBottom: '4px' }}>
                                          📄 PubMed Articles: {msg.sources.filter(s => s.pmid).length}
                                        </div>
                                      )}
                                      {msg.sources.filter(s => s.pdf_path || (s.source && s.source.endsWith('.pdf'))).length > 0 && (
                                        <div style={{ color: '#6ee7b7', fontSize: '12px', marginBottom: '4px' }}>
                                          📑 PDF Documents: {msg.sources.filter(s => s.pdf_path || (s.source && s.source.endsWith('.pdf'))).length}
                                        </div>
                                      )}
                                      {msg.sources.some(s => s.confidence_score !== undefined) && (
                                        <div style={{ color: '#6ee7b7', fontSize: '12px', marginBottom: '4px' }}>
                                          ⭐ Avg Confidence: {Math.round(
                                            msg.sources
                                              .filter(s => s.confidence_score !== undefined)
                                              .reduce((sum, s) => sum + s.confidence_score, 0) / 
                                            msg.sources.filter(s => s.confidence_score !== undefined).length
                                          )}/100
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                )}

                                {/* Detailed Sources Debug - Raw Data */}
                                {msg.sources && msg.sources.length > 0 && (
                                  <div style={{ marginBottom: '12px' }}>
                                    <div style={{ 
                                      fontWeight: 'bold',
                                      color: '#60a5fa',
                                      marginBottom: '8px',
                                      fontSize: '15px',
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: '8px',
                                    }}>
                                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <polyline points="16 18 22 12 16 6" />
                                        <polyline points="8 6 2 12 8 18" />
                                      </svg>
                                      Sources Debug Data
                                    </div>
                                    {msg.sources.map((source, srcIdx) => (
                                      <div key={srcIdx} style={{
                                        marginBottom: '12px',
                                        padding: '12px',
                                        background: 'rgba(96, 165, 250,0.1)',
                                        borderRadius: '6px',
                                        borderLeft: '4px solid #60a5fa',
                                      }}>
                                        <div style={{ 
                                          fontWeight: 'bold',
                                          color: '#93c5fd',
                                          marginBottom: '8px',
                                          fontSize: '13px',
                                        }}>
                                          Source {srcIdx + 1}: {source.ref || `#${srcIdx + 1}`}
                                        </div>
                                        
                                        {/* Key Fields */}
                                        <div style={{ fontSize: '11px', color: '#d1d5db', marginBottom: '8px' }}>
                                          {source.pmid && (
                                            <div style={{ marginBottom: '4px' }}>
                                              <strong style={{ color: '#93c5fd' }}>PMID:</strong> {source.pmid}
                                            </div>
                                          )}
                                          {source.title && (
                                            <div style={{ marginBottom: '4px' }}>
                                              <strong style={{ color: '#93c5fd' }}>Title:</strong> {source.title}
                                            </div>
                                          )}
                                          {source.journal && (
                                            <div style={{ marginBottom: '4px' }}>
                                              <strong style={{ color: '#93c5fd' }}>Journal:</strong> {source.journal}
                                            </div>
                                          )}
                                          {source.publication_date && (
                                            <div style={{ marginBottom: '4px' }}>
                                              <strong style={{ color: '#93c5fd' }}>Published:</strong> {source.publication_date}
                                            </div>
                                          )}
                                          {source.citation_count !== undefined && (
                                            <div style={{ marginBottom: '4px' }}>
                                              <strong style={{ color: '#93c5fd' }}>Citations:</strong> {source.citation_count}
                                            </div>
                                          )}
                                          {source.confidence_score !== undefined && (
                                            <div style={{ marginBottom: '4px' }}>
                                              <strong style={{ color: '#93c5fd' }}>Confidence:</strong> {source.confidence_score}/100
                                            </div>
                                          )}
                                          {source.authors && source.authors.length > 0 && (
                                            <div style={{ marginBottom: '4px' }}>
                                              <strong style={{ color: '#93c5fd' }}>Authors:</strong> {source.authors.slice(0, 3).join(', ')}{source.authors.length > 3 ? ' et al.' : ''}
                                            </div>
                                          )}
                                        </div>

                                        {/* Abstract Preview */}
                                        {source.abstract && (
                                          <div style={{ marginBottom: '8px' }}>
                                            <details>
                                              <summary style={{ 
                                                cursor: 'pointer', 
                                                color: '#93c5fd', 
                                                fontWeight: 'bold',
                                                fontSize: '11px',
                                                marginBottom: '4px'
                                              }}>
                                                📄 Abstract ({source.abstract.length} chars)
                                              </summary>
                                              <div style={{
                                                marginTop: '6px',
                                                padding: '8px',
                                                background: 'rgba(0,0,0,0.4)',
                                                borderRadius: '4px',
                                                fontSize: '11px',
                                                color: '#d1d5db',
                                                maxHeight: '200px',
                                                overflow: 'auto',
                                                whiteSpace: 'pre-wrap',
                                                wordBreak: 'break-word'
                                              }}>
                                                {source.abstract}
                                              </div>
                                            </details>
                                          </div>
                                        )}

                                        {/* Full Raw JSON */}
                                        <details>
                                          <summary style={{ 
                                            cursor: 'pointer', 
                                            color: '#93c5fd', 
                                            fontWeight: 'bold',
                                            fontSize: '11px'
                                          }}>
                                            🔍 Full Source Object (JSON)
                                          </summary>
                                          <pre style={{
                                            marginTop: '6px',
                                            padding: '8px',
                                            background: 'rgba(0,0,0,0.4)',
                                            borderRadius: '4px',
                                            fontSize: '10px',
                                            color: '#d1d5db',
                                            maxHeight: '300px',
                                            overflow: 'auto',
                                            whiteSpace: 'pre-wrap',
                                            wordBreak: 'break-word'
                                          }}>
                                            {JSON.stringify(source, null, 2)}
                                          </pre>
                                        </details>
                                      </div>
                                    ))}
                                  </div>
                                )}

                                {/* Performance Metrics */}
                                {msg.debug && Object.keys(msg.debug).length > 0 && (
                                  <div>
                                    <div style={{ 
                                      fontWeight: 'bold',
                                      color: '#fbbf24',
                                      marginBottom: '8px',
                                      fontSize: '15px',
                                      display: 'flex',
                                      alignItems: 'center',
                                      gap: '8px',
                                    }}>
                                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                                        <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
                                      </svg>
                                      Performance Metrics
                                    </div>
                                    <div style={{
                                      padding: '10px',
                                      background: 'rgba(251,191,36,0.1)',
                                      borderRadius: '6px',
                                      borderLeft: '4px solid #fbbf24'
                                    }}>
                                      {msg.debug.execution_time_ms && (
                                        <div style={{ color: '#fcd34d', marginBottom: '6px', fontSize: '13px' }}>
                                          ⏱️ Total Execution Time: <strong>{msg.debug.execution_time_ms.toFixed(0)}ms</strong>
                                        </div>
                                      )}
                                      {msg.tool_executions && msg.tool_executions.length > 0 && (
                                        <div style={{ color: '#fcd34d', marginBottom: '6px', fontSize: '12px' }}>
                                          🔧 Tool Execution Time: {
                                            msg.tool_executions
                                              .filter(t => t.execution_time_ms)
                                              .reduce((sum, t) => sum + t.execution_time_ms, 0)
                                              .toFixed(0)
                                          }ms
                                        </div>
                                      )}
                                      {msg.debug.tool_debug && (
                                        <div style={{ 
                                          marginTop: '8px',
                                          fontSize: '12px',
                                          color: '#d1d5db'
                                        }}>
                                          <details>
                                            <summary style={{ cursor: 'pointer', color: '#fcd34d', fontWeight: 'bold' }}>
                                              Additional Debug Info
                                            </summary>
                                            <pre style={{
                                              marginTop: '6px',
                                              padding: '8px',
                                              background: 'rgba(0,0,0,0.4)',
                                              borderRadius: '4px',
                                              fontSize: '11px',
                                              maxHeight: '150px',
                                              overflow: 'auto'
                                            }}>
                                              {JSON.stringify(msg.debug.tool_debug, null, 2)}
                                            </pre>
                                          </details>
                                        </div>
                                      )}
                                    </div>
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                          );
                        })()}
                        {/* Save to patient notes button */}
                        {selectedPatient && msg.content && (
                          <button
                            className="save-to-notes-btn"
                            onClick={async () => {
                              try {
                                const token = localStorage.getItem('token');
                                const res = await fetch(`${config.API_URL}/api/users/profile/patient/${selectedPatient.patient_id}/notes`, {
                                  method: 'POST',
                                  headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
                                  body: JSON.stringify({ note: msg.content.slice(0, 2000) }),
                                });
                                if (res.ok) {
                                  alert('Saved to patient notes');
                                } else {
                                  alert('Failed to save note');
                                }
                              } catch (err) {
                                console.error('Save note error:', err);
                              }
                            }}
                          >
                            📝 Save to patient notes
                          </button>
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
                  <MarkdownWithReferences
                    content={streamingContent}
                    sources={[]}
                    onSourceClick={() => {}}
                  />
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
          </>
        )}
      </div>
      {/* O8: PDF preview side panel */}
      {pdfPanel && (
        <PdfPanel
          source={pdfPanel.source}
          page={pdfPanel.page}
          onClose={() => setPdfPanel(null)}
          apiUrl={config.API_URL}
          articleData={pdfPanel.articleData}
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
                  <div className="settings-value">{user.isDoctor ? 'Healthcare Professional' : 'General User'}</div>
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
                <h3>Developer</h3>
                <div className="settings-field">
                  <label>Developer mode</label>
                  <div className="settings-value" style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <button
                      type="button"
                      onClick={toggleDeveloperMode}
                      aria-pressed={developerMode}
                      className={`settings-theme-btn${developerMode ? ' active' : ''}`}
                    >
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                        <polyline points="16 18 22 12 16 6" />
                        <polyline points="8 6 2 12 8 18" />
                      </svg>
                      {developerMode ? 'Enabled' : 'Disabled'}
                    </button>
                    <span style={{ fontSize: '11px', opacity: 0.7 }}>
                      Shows the per-message Debug Info button with tool execution data.
                    </span>
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
    </DoctorPanelContext.Provider>
  );
}

export default Chat;
