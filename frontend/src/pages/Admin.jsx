import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import config from '../api/config';
import './Admin.css';

function Admin() {
  const [authenticated, setAuthenticated] = useState(false);
  const [loginData, setLoginData] = useState({ username: '', password: '' });
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  const [systemStats, setSystemStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(false);
  const [expandedUser, setExpandedUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const adminAuth = sessionStorage.getItem('admin_auth');
    if (adminAuth === 'true') {
      setAuthenticated(true);
    }
  }, []);

  useEffect(() => {
    if (authenticated) fetchData();
  }, [authenticated]);

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoginError('');
    setLoginLoading(true);
    try {
      const res = await fetch(`${config.API_URL}/api/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginData),
      });
      if (!res.ok) throw new Error('Invalid credentials');
      sessionStorage.setItem('admin_auth', 'true');
      setAuthenticated(true);
    } catch (err) {
      setLoginError(err.message);
    } finally {
      setLoginLoading(false);
    }
  };

  const handleLogout = () => {
    sessionStorage.removeItem('admin_auth');
    setAuthenticated(false);
  };

  const fetchData = async () => {
    setLoading(true);
    try {
      const [statsRes, usersRes] = await Promise.all([
        fetch(`${config.API_URL}/api/admin/stats`),
        fetch(`${config.API_URL}/api/admin/users`),
      ]);
      setSystemStats(await statsRes.json());
      const usersData = await usersRes.json();
      setUsers(usersData.users || []);
    } catch (err) {
      console.error('Failed to load admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  // ── Login Gate ──
  if (!authenticated) {
    return (
      <div className="admin-login-container">
        <div className="admin-login-box">
          <div className="admin-login-icon">
            <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2" />
              <path d="M7 11V7a5 5 0 0 1 10 0v4" />
            </svg>
          </div>
          <h2>Admin Access</h2>
          <p>Enter admin credentials to continue</p>
          {loginError && <div className="admin-login-error">{loginError}</div>}
          <form onSubmit={handleLogin}>
            <input
              type="text" placeholder="Username" value={loginData.username}
              onChange={(e) => setLoginData({ ...loginData, username: e.target.value })}
              required autoFocus
            />
            <input
              type="password" placeholder="Password" value={loginData.password}
              onChange={(e) => setLoginData({ ...loginData, password: e.target.value })}
              required
            />
            <button type="submit" disabled={loginLoading}>
              {loginLoading ? 'Verifying...' : 'Access Panel'}
            </button>
          </form>
          <button className="admin-login-back" onClick={() => navigate('/chat')}>Back to Chat</button>
        </div>
      </div>
    );
  }

  // ── Admin Panel ──
  if (loading && !systemStats) return <div className="admin-loading">Loading admin panel...</div>;

  return (
    <div className="admin">
      <div className="admin-header">
        <div className="admin-header-left">
          <button className="admin-back" onClick={() => navigate('/chat')}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M19 12H5" /><polyline points="12 19 5 12 12 5" />
            </svg>
          </button>
          <h1>Admin Panel</h1>
        </div>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button className="admin-refresh" onClick={fetchData}>Refresh</button>
          <button className="admin-refresh" style={{ color: '#f87171', borderColor: 'rgba(239,68,68,0.3)' }} onClick={handleLogout}>Sign Out</button>
        </div>
      </div>

      {systemStats && (
        <div className="stats-grid">
          <div className="stat-card"><div className="stat-value">{systemStats.users}</div><div className="stat-label">Total Users</div></div>
          <div className="stat-card"><div className="stat-value">{systemStats.conversations}</div><div className="stat-label">Conversations</div></div>
          <div className="stat-card"><div className="stat-value">{systemStats.messages}</div><div className="stat-label">Messages</div></div>
          <div className="stat-card"><div className="stat-value">{systemStats.total_tool_calls}</div><div className="stat-label">Tool Calls</div></div>
          <div className="stat-card"><div className="stat-value">{systemStats.patients}</div><div className="stat-label">Patients</div></div>
          <div className="stat-card"><div className="stat-value">{(systemStats.drugs_in_database || 0).toLocaleString()}</div><div className="stat-label">Drugs in DB</div></div>
          <div className="stat-card"><div className="stat-value">{(systemStats.drug_interactions || 0).toLocaleString()}</div><div className="stat-label">Interactions</div></div>
          <div className="stat-card"><div className="stat-value">{systemStats.pubmed_articles_indexed}</div><div className="stat-label">PubMed Indexed</div></div>
        </div>
      )}

      {systemStats && systemStats.tool_breakdown && Object.keys(systemStats.tool_breakdown).length > 0 && (
        <div className="admin-section">
          <h2>Tool Usage</h2>
          <div className="tool-bars">
            {Object.entries(systemStats.tool_breakdown).sort(([,a], [,b]) => b - a).map(([tool, count]) => {
              const max = Math.max(...Object.values(systemStats.tool_breakdown));
              return (
                <div key={tool} className="tool-bar-row">
                  <div className="tool-bar-name">{tool}</div>
                  <div className="tool-bar-track"><div className="tool-bar-fill" style={{ width: `${(count / max) * 100}%` }} /></div>
                  <div className="tool-bar-count">{count}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      <div className="admin-section">
        <h2>Users ({users.length})</h2>
        <div className="users-table-wrap">
          <table className="users-table">
            <thead>
              <tr>
                <th>Name</th><th>Email</th><th>Type</th><th>Chats</th>
                <th>Messages</th><th>Tool Calls</th><th>Patients</th><th>Joined</th>
              </tr>
            </thead>
            <tbody>
              {users.map((u) => (
                <>{/* Fragment needed for adjacent rows */}
                  <tr key={u.user_id} className="user-row" onClick={() => setExpandedUser(expandedUser === u.user_id ? null : u.user_id)}>
                    <td><div className="user-cell"><div className="user-cell-avatar">{u.name.charAt(0).toUpperCase()}</div>{u.name}</div></td>
                    <td className="email-cell">{u.email}</td>
                    <td><span className={`role-badge ${u.account_type}`}>{u.account_type === 'doctor' ? 'Pro' : 'User'}</span></td>
                    <td>{u.stats.total_conversations}</td>
                    <td>{u.stats.total_messages}</td>
                    <td>{u.stats.total_tool_calls}</td>
                    <td>{u.stats.patient_count}</td>
                    <td className="date-cell">{u.created_at ? new Date(u.created_at).toLocaleDateString() : '—'}</td>
                  </tr>
                  {expandedUser === u.user_id && (
                    <tr key={`${u.user_id}-detail`} className="user-detail-row">
                      <td colSpan="8">
                        <div className="user-detail">
                          <div className="detail-grid">
                            <div className="detail-item"><span className="detail-label">User ID</span><span className="detail-value">{u.user_id}</span></div>
                            <div className="detail-item"><span className="detail-label">User Messages</span><span className="detail-value">{u.stats.user_messages}</span></div>
                            <div className="detail-item"><span className="detail-label">AI Responses</span><span className="detail-value">{u.stats.assistant_messages}</span></div>
                          </div>
                          {Object.keys(u.stats.tools_used).length > 0 && (
                            <div className="detail-tools">
                              <span className="detail-label">Tools Used:</span>
                              <div className="detail-tool-tags">
                                {Object.entries(u.stats.tools_used).sort(([,a],[,b]) => b - a).map(([tool, count]) => (
                                  <span key={tool} className="tool-tag">{tool} ({count})</span>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default Admin;
