import { useState, useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import config from '../api/config';
import LoadingScreen from '../components/LoadingScreen';
import './Admin.css';

function Admin() {
  const [authenticated, setAuthenticated] = useState(false);
  const [loginData, setLoginData] = useState({ username: '', password: '' });
  const [loginError, setLoginError] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  const [systemStats, setSystemStats] = useState(null);
  const [users, setUsers] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [patients, setPatients] = useState([]);
  const [relationships, setRelationships] = useState([]);
  const [premiumUsers, setPremiumUsers] = useState([]);
  const [premiumEmail, setPremiumEmail] = useState('');
  const [premiumMsg, setPremiumMsg] = useState('');
  const [premiumBusy, setPremiumBusy] = useState(false);
  // Users-table search + paging. Page is 1-based.
  const [userSearch, setUserSearch] = useState('');
  const [userRoleFilter, setUserRoleFilter] = useState('all');
  const [userPage, setUserPage] = useState(1);
  const USER_PAGE_SIZE = 20;

  // Same shape, scoped to the doctor-patient assignments table.
  const [assignSearch, setAssignSearch] = useState('');
  const [assignPage, setAssignPage] = useState(1);
  const ASSIGN_PAGE_SIZE = 20;
  const [assignForm, setAssignForm] = useState({ doctor_id: '', patient_id: '' });
  const [assignMsg, setAssignMsg] = useState('');
  const [loading, setLoading] = useState(false);
  const [expandedUser, setExpandedUser] = useState(null);
  const navigate = useNavigate();

  useEffect(() => {
    const adminToken = localStorage.getItem('admin_token');
    if (adminToken) {
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
      const data = await res.json();
      localStorage.setItem('admin_token', data.token);
      setAuthenticated(true);
    } catch (err) {
      setLoginError(err.message);
    } finally {
      setLoginLoading(false);
    }
  };

  const handleLogout = () => {
    localStorage.removeItem('admin_token');
    setAuthenticated(false);
  };

  const fetchData = async () => {
    setLoading(true);
    const token = localStorage.getItem('admin_token');
    const headers = { 'Authorization': `Bearer ${token}` };
    try {
      const [statsRes, usersRes, doctorsRes, patientsRes, relsRes, premiumRes] = await Promise.all([
        fetch(`${config.API_URL}/api/admin/stats`, { headers }),
        fetch(`${config.API_URL}/api/admin/users`, { headers }),
        fetch(`${config.API_URL}/api/admin/doctors`, { headers }),
        fetch(`${config.API_URL}/api/admin/patients`, { headers }),
        fetch(`${config.API_URL}/api/admin/relationships`, { headers }),
        fetch(`${config.API_URL}/api/admin/premium`, { headers }),
      ]);
      const allRes = [statsRes, usersRes, doctorsRes, patientsRes, relsRes, premiumRes];
      if (allRes.some(r => r.status === 401)) {
        localStorage.removeItem('admin_token');
        setAuthenticated(false);
        return;
      }
      setSystemStats(await statsRes.json());
      const usersData = await usersRes.json();
      setUsers(usersData.users || []);
      const doctorsData = await doctorsRes.json();
      setDoctors(doctorsData.doctors || []);
      const patientsData = await patientsRes.json();
      setPatients(patientsData.patients || []);
      const relsData = await relsRes.json();
      setRelationships(relsData.relationships || []);
      const premiumData = await premiumRes.json();
      setPremiumUsers(premiumData.users || []);
    } catch (err) {
      console.error('Failed to load admin data:', err);
    } finally {
      setLoading(false);
    }
  };

  // Fast email lookup so the row badge can show 'Premium' without a per-row
  // .find() over premiumUsers.
  const premiumEmails = useMemo(
    () => new Set(premiumUsers.map((u) => u.email.toLowerCase())),
    [premiumUsers],
  );

  // Filter + paginate the users list. Search matches name, email, user_id.
  const filteredUsers = useMemo(() => {
    const q = userSearch.trim().toLowerCase();
    return users.filter((u) => {
      if (q) {
        const haystack = `${u.name} ${u.email} ${u.user_id}`.toLowerCase();
        if (!haystack.includes(q)) return false;
      }
      if (userRoleFilter === 'all') return true;
      if (userRoleFilter === 'premium') return premiumEmails.has((u.email || '').toLowerCase());
      return u.account_type === userRoleFilter;
    });
  }, [users, userSearch, userRoleFilter, premiumEmails]);

  const totalPages = Math.max(1, Math.ceil(filteredUsers.length / USER_PAGE_SIZE));
  const safePage = Math.min(userPage, totalPages);
  const pagedUsers = filteredUsers.slice(
    (safePage - 1) * USER_PAGE_SIZE,
    safePage * USER_PAGE_SIZE,
  );

  // Reset page back to 1 whenever the filter changes so the user doesn't
  // get stuck on an empty trailing page.
  useEffect(() => {
    setUserPage(1);
  }, [userSearch, userRoleFilter]);

  // Same paging math for the assignments table.
  const filteredAssignments = useMemo(() => {
    const q = assignSearch.trim().toLowerCase();
    if (!q) return relationships;
    return relationships.filter((r) => {
      const haystack = `${r.doctor_name} ${r.patient_name} ${r.doctor_id} ${r.patient_id}`.toLowerCase();
      return haystack.includes(q);
    });
  }, [relationships, assignSearch]);

  const assignTotalPages = Math.max(1, Math.ceil(filteredAssignments.length / ASSIGN_PAGE_SIZE));
  const assignSafePage = Math.min(assignPage, assignTotalPages);
  const pagedAssignments = filteredAssignments.slice(
    (assignSafePage - 1) * ASSIGN_PAGE_SIZE,
    assignSafePage * ASSIGN_PAGE_SIZE,
  );

  useEffect(() => {
    setAssignPage(1);
  }, [assignSearch]);

  const handleAssign = async () => {
    if (!assignForm.doctor_id || !assignForm.patient_id) {
      setAssignMsg('Select both a doctor and a patient');
      return;
    }
    const token = localStorage.getItem('admin_token');
    try {
      const res = await fetch(`${config.API_URL}/api/users/relationships/assign`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(assignForm),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to assign');
      setAssignMsg('Assigned successfully!');
      setAssignForm({ doctor_id: '', patient_id: '' });
      fetchData();
    } catch (err) {
      setAssignMsg(err.message);
    }
  };

  const handleRemove = async (doctor_id, patient_id) => {
    const token = localStorage.getItem('admin_token');
    try {
      const res = await fetch(`${config.API_URL}/api/users/relationships/remove`, {
        method: 'DELETE',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ doctor_id, patient_id }),
      });
      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || 'Failed to remove');
      }
      fetchData();
    } catch (err) {
      setAssignMsg(err.message);
    }
  };

  const handleAddPremium = async (e) => {
    e?.preventDefault?.();
    const email = premiumEmail.trim();
    if (!email) {
      setPremiumMsg('Enter an email');
      return;
    }
    setPremiumBusy(true);
    setPremiumMsg('');
    const token = localStorage.getItem('admin_token');
    try {
      const res = await fetch(`${config.API_URL}/api/admin/premium/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to add premium user');
      setPremiumMsg(data.message || 'Granted');
      setPremiumEmail('');
      // Refresh the premium list only — full fetchData would be wasteful here.
      const listRes = await fetch(`${config.API_URL}/api/admin/premium`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      const listData = await listRes.json();
      setPremiumUsers(listData.users || []);
    } catch (err) {
      setPremiumMsg(err.message);
    } finally {
      setPremiumBusy(false);
    }
  };

  const handleRemovePremium = async (email) => {
    if (!window.confirm(`Revoke premium for ${email}?`)) return;
    setPremiumBusy(true);
    const token = localStorage.getItem('admin_token');
    try {
      const res = await fetch(`${config.API_URL}/api/admin/premium/remove`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || 'Failed to revoke premium');
      setPremiumMsg(data.message || 'Revoked');
      setPremiumUsers((prev) => prev.filter((u) => u.email.toLowerCase() !== email.toLowerCase()));
    } catch (err) {
      setPremiumMsg(err.message);
    } finally {
      setPremiumBusy(false);
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
  if (loading && !systemStats) return <LoadingScreen message="Loading admin panel" />;

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
        <div className="admin-section-header-row">
          <h2>Users ({filteredUsers.length}{filteredUsers.length !== users.length ? ` / ${users.length}` : ''})</h2>
          <div className="users-toolbar">
            <input
              type="search"
              placeholder="Search by name, email, or ID…"
              value={userSearch}
              onChange={(e) => setUserSearch(e.target.value)}
              className="users-search-input"
            />
            <select
              value={userRoleFilter}
              onChange={(e) => setUserRoleFilter(e.target.value)}
              className="users-role-select"
            >
              <option value="all">All roles</option>
              <option value="user">User</option>
              <option value="patient">Patient</option>
              <option value="doctor">Doctor</option>
              <option value="premium">Premium only</option>
            </select>
          </div>
        </div>
        <div className="users-table-wrap">
          <table className="users-table">
            <thead>
              <tr>
                <th>Name</th><th>Email</th><th>Type</th><th>Chats</th>
                <th>Messages</th><th>Tool Calls</th><th>Patients</th><th>Joined</th>
              </tr>
            </thead>
            <tbody>
              {pagedUsers.map((u) => {
                const isPremium = premiumEmails.has((u.email || '').toLowerCase());
                return (
                <>{/* Fragment needed for adjacent rows */}
                  <tr key={u.user_id} className="user-row" onClick={() => setExpandedUser(expandedUser === u.user_id ? null : u.user_id)}>
                    <td>
                      <div className="user-cell">
                        <div className="user-cell-avatar">{u.name.charAt(0).toUpperCase()}</div>
                        <span>{u.name}</span>
                        {isPremium && <span className="role-badge premium" title="Premium — bypasses daily quota">★ Premium</span>}
                      </div>
                    </td>
                    <td className="email-cell">{u.email}</td>
                    <td><span className={`role-badge ${u.account_type}`}>{u.account_type === 'doctor' ? 'Pro' : u.account_type === 'patient' ? 'Patient' : 'User'}</span></td>
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
                          <div className="detail-actions">
                            {isPremium ? (
                              <button
                                className="admin-refresh"
                                disabled={premiumBusy}
                                onClick={(e) => { e.stopPropagation(); handleRemovePremium(u.email); }}
                              >Revoke premium</button>
                            ) : (
                              <button
                                className="admin-refresh"
                                disabled={premiumBusy}
                                onClick={async (e) => {
                                  e.stopPropagation();
                                  setPremiumEmail(u.email);
                                  await handleAddPremium();
                                }}
                              >Grant premium</button>
                            )}
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
                );
              })}
            </tbody>
          </table>
          {filteredUsers.length === 0 && (
            <div className="users-empty">No users match your filters.</div>
          )}
        </div>
        {totalPages > 1 && (
          <div className="users-pagination">
            <button
              className="admin-refresh"
              disabled={safePage === 1}
              onClick={() => setUserPage((p) => Math.max(1, p - 1))}
            >← Prev</button>
            <span className="users-pagination-info">
              Page {safePage} of {totalPages}
            </span>
            <button
              className="admin-refresh"
              disabled={safePage >= totalPages}
              onClick={() => setUserPage((p) => Math.min(totalPages, p + 1))}
            >Next →</button>
          </div>
        )}
      </div>

      {/* Doctor-Patient Relationships Management */}
      <div className="admin-section">
        <div className="admin-section-header-row">
          <h2>Doctor-Patient Assignments ({filteredAssignments.length}{filteredAssignments.length !== relationships.length ? ` / ${relationships.length}` : ''})</h2>
          <div className="users-toolbar">
            <input
              type="search"
              placeholder="Search by doctor or patient name…"
              value={assignSearch}
              onChange={(e) => setAssignSearch(e.target.value)}
              className="users-search-input"
            />
          </div>
        </div>

        <div className="assign-form">
          <select
            value={assignForm.doctor_id}
            onChange={(e) => setAssignForm({ ...assignForm, doctor_id: e.target.value })}
          >
            <option value="">— Select Doctor —</option>
            {doctors.map(d => (
              <option key={d.doctor_id} value={d.doctor_id}>
                {d.name} ({d.specialty || 'General'})
              </option>
            ))}
          </select>
          <select
            value={assignForm.patient_id}
            onChange={(e) => setAssignForm({ ...assignForm, patient_id: e.target.value })}
          >
            <option value="">— Select Patient —</option>
            {patients.map(p => (
              <option key={p.patient_id} value={p.patient_id}>
                {p.name} ({p.email})
              </option>
            ))}
          </select>
          <button className="admin-refresh" onClick={handleAssign}>Assign</button>
        </div>
        {assignMsg && <div className="assign-msg">{assignMsg}</div>}

        {filteredAssignments.length > 0 ? (
          <>
            <div className="users-table-wrap" style={{ marginTop: '16px' }}>
              <table className="users-table">
                <thead>
                  <tr><th>Doctor</th><th>Patient</th><th>Assigned</th><th>Action</th></tr>
                </thead>
                <tbody>
                  {pagedAssignments.map((r, i) => (
                    <tr key={`${r.doctor_id}-${r.patient_id}-${i}`} className="user-row">
                      <td>{r.doctor_name}</td>
                      <td>{r.patient_name}</td>
                      <td className="date-cell">{r.created_at ? new Date(r.created_at).toLocaleDateString() : '—'}</td>
                      <td>
                        <button
                          className="admin-refresh"
                          style={{ color: '#f87171', borderColor: 'rgba(239,68,68,0.3)', padding: '4px 10px', fontSize: '12px' }}
                          onClick={() => handleRemove(r.doctor_id, r.patient_id)}
                        >Remove</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {assignTotalPages > 1 && (
              <div className="users-pagination">
                <button
                  className="admin-refresh"
                  disabled={assignSafePage === 1}
                  onClick={() => setAssignPage((p) => Math.max(1, p - 1))}
                >← Prev</button>
                <span className="users-pagination-info">
                  Page {assignSafePage} of {assignTotalPages}
                </span>
                <button
                  className="admin-refresh"
                  disabled={assignSafePage >= assignTotalPages}
                  onClick={() => setAssignPage((p) => Math.min(assignTotalPages, p + 1))}
                >Next →</button>
              </div>
            )}
          </>
        ) : (
          <p style={{ color: '#64748b', fontSize: '14px', marginTop: '12px' }}>
            {relationships.length === 0
              ? 'No assignments yet.'
              : 'No assignments match your search.'}
          </p>
        )}
      </div>

      {/* Premium Users — bypass the daily message quota */}
      <div className="admin-section">
        <div className="admin-section-header-row">
          <h2>
            <span className="premium-star" aria-hidden="true">★</span> Premium Users ({premiumUsers.length})
          </h2>
          <p className="premium-subtle">
            Bypasses the {systemStats?.free_daily_message_quota ?? 20}-message daily limit. Match by registered email.
          </p>
        </div>
        <form className="premium-add-form" onSubmit={handleAddPremium}>
          <input
            type="email"
            placeholder="user@example.com"
            value={premiumEmail}
            onChange={(e) => setPremiumEmail(e.target.value)}
            disabled={premiumBusy}
            required
          />
          <button className="premium-add-btn" type="submit" disabled={premiumBusy}>
            {premiumBusy ? 'Working…' : 'Grant premium'}
          </button>
        </form>
        {premiumMsg && <div className="assign-msg">{premiumMsg}</div>}

        {premiumUsers.length > 0 ? (
          <div className="premium-grid">
            {premiumUsers.map((u) => (
              <div key={u.user_id} className="premium-card">
                <div className="premium-card-avatar">
                  {(u.name || u.email).charAt(0).toUpperCase()}
                </div>
                <div className="premium-card-body">
                  <div className="premium-card-name">{u.name || '—'}</div>
                  <div className="premium-card-email" title={u.email}>{u.email}</div>
                </div>
                <button
                  className="premium-card-revoke"
                  onClick={() => handleRemovePremium(u.email)}
                  disabled={premiumBusy}
                  aria-label={`Revoke premium for ${u.email}`}
                  title="Revoke premium"
                >
                  Revoke
                </button>
              </div>
            ))}
          </div>
        ) : (
          <p className="premium-empty">No premium users yet. Grant access by entering an email above.</p>
        )}
      </div>
    </div>
  );
}

export default Admin;
