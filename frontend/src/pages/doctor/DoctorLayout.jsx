import { useState, useEffect, useMemo } from 'react';
import { useNavigate, useLocation, Outlet, useParams, useSearchParams } from 'react-router-dom';
import config from '../../api/config';
import { useT } from '../../i18n/lang';
import { DOCTOR_STRINGS } from '../../i18n/strings/doctor';
import { DoctorPanelContext } from './panelContext';
import './DoctorPanel.css';
import './DoctorPages.css';
import '../DrugMatrix.css';

function DoctorLayout() {
  const t = useT(DOCTOR_STRINGS);
  const [user, setUser] = useState(null);
  const [collapsed, setCollapsed] = useState(false);
  const [theme, setTheme] = useState('dark');
  // Shared cache — survives navigation between doctor pages
  const [patients, setPatients] = useState(null);
  const navigate = useNavigate();
  const location = useLocation();
  const params = useParams();
  const [searchParams] = useSearchParams();

  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    const savedTheme = localStorage.getItem('theme') || 'dark';
    if (!savedUser) {
      navigate('/login');
      return;
    }
    const userData = JSON.parse(savedUser);
    if (!userData.isDoctor) {
      navigate('/chat');
      return;
    }
    setUser(userData);
    setTheme(savedTheme);
  }, [navigate]);

  // Fetch patients once when the layout mounts (not on every tab switch)
  useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) return;

    fetch(`${config.API_URL}/api/users/doctors/patients`, {
      headers: { 'Authorization': `Bearer ${token}` },
    }).then(r => r.ok ? r.json() : []).then(data => {
      setPatients(Array.isArray(data) ? data : []);
    }).catch(() => setPatients([]));
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
    { path: '/doctor', icon: 'dashboard', label: t.nav.dashboard },
    { path: '/doctor/patients', icon: 'patients', label: t.nav.patients },
    { path: '/chat', icon: 'chat', label: t.nav.aiChat, external: true },
    { path: '/doctor/research', icon: 'research', label: t.nav.research },
  ];

  const isActive = (path) => {
    if (path === '/doctor') return location.pathname === '/doctor';
    return location.pathname.startsWith(path);
  };

  // Bridge the panel context to react-router. Legacy URLs keep working.
  const panelValue = useMemo(() => ({
    user,
    patients,
    setPatients,
    viewParams: {
      patientId: params.patientId,
      addPatient: searchParams.get('add') === 'true',
    },
    navigateTo: (view, viewParams = {}) => {
      switch (view) {
        case 'dashboard':       return navigate('/doctor');
        case 'patients':        return navigate(viewParams.addPatient ? '/doctor/patients?add=true' : '/doctor/patients');
        case 'patient-detail':  return navigate(`/doctor/patients/${viewParams.patientId}`);
        case 'drug-matrix':     return navigate('/chat');
        case 'research':        return navigate('/doctor/research');
        case 'chat': {
          const url = viewParams.patientId ? `/chat?patient=${viewParams.patientId}` : '/chat';
          return window.open(url, '_blank');
        }
        default:                return;
      }
    },
  }), [user, patients, params.patientId, searchParams, navigate]);

  if (!user) return null;

  return (
    <DoctorPanelContext.Provider value={panelValue}>
      <div className={`doctor-panel ${theme}`}>
        <aside className={`doctor-sidebar ${collapsed ? 'collapsed' : ''}`}>
          <div className="doctor-sidebar-header">
            {!collapsed && <h2 className="doctor-sidebar-title">MedicaLLM</h2>}
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

          <nav className="doctor-nav">
            {navItems.map(item => (
              <button
                key={item.path}
                className={`doctor-nav-item ${isActive(item.path) ? 'active' : ''}`}
                onClick={() => item.external ? window.open(item.path, '_blank') : navigate(item.path)}
                title={collapsed ? item.label : undefined}
              >
                <NavIcon name={item.icon} />
                {!collapsed && <span>{item.label}</span>}
              </button>
            ))}
          </nav>

          <div className="doctor-sidebar-footer">
            <div className={`doctor-user-info ${collapsed ? 'collapsed' : ''}`}>
              <div className="doctor-avatar">{user.name?.charAt(0).toUpperCase()}</div>
              {!collapsed && (
                <div className="doctor-user-details">
                  <span className="doctor-user-name">{user.name}</span>
                  <span className="doctor-user-role">{t.nav.role}</span>
                </div>
              )}
            </div>
            <div className="doctor-sidebar-actions">
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

        <main className="doctor-main">
          <Outlet />
        </main>
      </div>
    </DoctorPanelContext.Provider>
  );
}

function NavIcon({ name }) {
  const icons = {
    dashboard: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
      </svg>
    ),
    patients: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 00-3-3.87"/><path d="M16 3.13a4 4 0 010 7.75"/>
      </svg>
    ),
    chat: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
      </svg>
    ),
    drugs: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M10.5 1.5H8.25A2.25 2.25 0 006 3.75v16.5a2.25 2.25 0 002.25 2.25h7.5A2.25 2.25 0 0018 20.25V3.75a2.25 2.25 0 00-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3m-3 18.75h3"/>
      </svg>
    ),
    research: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
    ),
  };
  return icons[name] || null;
}

export default DoctorLayout;
