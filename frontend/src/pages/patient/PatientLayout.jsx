import { useState, useEffect } from 'react';
import { useNavigate, useLocation, Outlet } from 'react-router-dom';
import config from '../../api/config';
import { useT } from '../../i18n/lang';
import { PATIENT_STRINGS } from '../../i18n/strings/patient';
import './PatientPanel.css';
import './PatientPages.css';

function PatientLayout() {
  const t = useT(PATIENT_STRINGS);
  const [user, setUser] = useState(null);
  const [collapsed, setCollapsed] = useState(false);
  const [theme, setTheme] = useState('dark');
  const [profile, setProfile] = useState(null);
  const [doctors, setDoctors] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();

  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (!savedUser) {
      navigate('/login');
      return;
    }
    const userData = JSON.parse(savedUser);
    if (!userData.isPatient) {
      navigate('/chat');
      return;
    }
    setUser(userData);
    setTheme(savedTheme);
  }, [navigate]);

  // Fetch patient profile once
  useEffect(() => {
    const token = localStorage.getItem('token');
    const savedUser = localStorage.getItem('user');
    if (!token || !savedUser) return;
    const userData = JSON.parse(savedUser);
    if (!userData.patientId) return;

    fetch(`${config.API_URL}/api/users/profile/patient/${userData.patientId}`, {
      headers: { 'Authorization': `Bearer ${token}` },
    }).then(r => r.ok ? r.json() : null).then(data => {
      if (data) setProfile(data);
    }).catch(() => {});
  }, []);

  // Fetch assigned doctors once
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;

    fetch(`${config.API_URL}/api/users/patients/doctors`, {
      headers: { 'Authorization': `Bearer ${token}` },
    }).then(r => r.ok ? r.json() : []).then(data => {
      setDoctors(Array.isArray(data) ? data : []);
    }).catch(() => setDoctors([]));
  }, []);

  useEffect(() => {
    document.body.className = theme;
    localStorage.setItem('theme', theme);
  }, [theme]);

  const handleLogout = () => {
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    navigate('/login');
  };

  const navItems = [
    { path: '/patient', icon: 'dashboard', label: t.nav.dashboard },
    { path: '/patient/profile', icon: 'profile', label: t.nav.profile },
    { path: '/patient/medications', icon: 'medications', label: t.nav.medications },
    { path: '/patient/doctors', icon: 'doctors', label: t.nav.doctors },
    { path: '/chat', icon: 'chat', label: t.nav.aiChat, external: true },
  ];

  const isActive = (path) => {
    if (path === '/patient') return location.pathname === '/patient';
    return location.pathname.startsWith(path);
  };

  if (!user) return null;

  return (
    <div className={`patient-panel ${theme}`}>
      <aside className={`patient-sidebar ${collapsed ? 'collapsed' : ''}`}>
        <div className="patient-sidebar-header">
          {!collapsed && <h2 className="patient-sidebar-title">MedicaLLM</h2>}
          <button className="sidebar-toggle" onClick={() => setCollapsed(!collapsed)}>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              {collapsed ? (
                <><line x1="3" y1="12" x2="21" y2="12"/><line x1="3" y1="6" x2="21" y2="6"/><line x1="3" y1="18" x2="21" y2="18"/></>
              ) : (
                <><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></>
              )}
            </svg>
          </button>
        </div>

        <nav className="patient-nav">
          {navItems.map(item => (
            <button
              key={item.path}
              className={`patient-nav-item ${isActive(item.path) ? 'active' : ''}`}
              onClick={() => item.external ? window.open(item.path, '_blank') : navigate(item.path)}
              title={collapsed ? item.label : undefined}
            >
              <PatientNavIcon name={item.icon} />
              {!collapsed && <span>{item.label}</span>}
            </button>
          ))}
        </nav>

        <div className="patient-sidebar-footer">
          <div className={`patient-user-info ${collapsed ? 'collapsed' : ''}`}>
            <div className="patient-avatar">{user.name?.charAt(0).toUpperCase()}</div>
            {!collapsed && (
              <div className="patient-user-details">
                <span className="patient-user-name">{user.name}</span>
                <span className="patient-user-role">{t.nav.role}</span>
              </div>
            )}
          </div>
          <div className="patient-sidebar-actions">
            {!collapsed && (
              <label className="theme-toggle-mini">
                <input type="checkbox" checked={theme === 'dark'} onChange={() => setTheme(t => t === 'dark' ? 'light' : 'dark')} />
                <span className="slider-mini"></span>
              </label>
            )}
            <button className="logout-btn" onClick={handleLogout} title={t.nav.logout}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/>
              </svg>
            </button>
          </div>
        </div>
      </aside>

      <main className="patient-main">
        <Outlet context={{ user, theme, setTheme, profile, setProfile, doctors, setDoctors }} />
      </main>
    </div>
  );
}

function PatientNavIcon({ name }) {
  const icons = {
    dashboard: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
      </svg>
    ),
    profile: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2"/><circle cx="12" cy="7" r="4"/>
      </svg>
    ),
    medications: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M10.5 1.5a4.5 4.5 0 00-4.5 4.5v12a4.5 4.5 0 009 0V6a4.5 4.5 0 00-4.5-4.5z"/><line x1="6" y1="12" x2="15" y2="12"/>
      </svg>
    ),
    doctors: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 21h18"/><path d="M9 8h1"/><path d="M9 12h1"/><path d="M9 16h1"/><path d="M14 8h1"/><path d="M14 12h1"/><path d="M14 16h1"/><rect x="5" y="2" width="14" height="20" rx="2"/>
      </svg>
    ),
    chat: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
      </svg>
    ),
  };
  return icons[name] || null;
}

export default PatientLayout;
