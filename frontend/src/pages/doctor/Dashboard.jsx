import { useDoctorPanel } from './panelContext';
import { useT } from '../../i18n/lang';
import { DOCTOR_STRINGS } from '../../i18n/strings/doctor';

function Dashboard() {
  const t = useT(DOCTOR_STRINGS);
  const { user, patients: cachedPatients, navigateTo } = useDoctorPanel();
  const patients = cachedPatients || [];
  const loading = cachedPatients === null;

  const stats = {
    total: patients.length,
    withConditions: patients.filter(p => p.chronic_conditions?.length > 0).length,
    recentlyUpdated: patients.filter(p => {
      if (!p.updated_at) return false;
      const updated = new Date(p.updated_at);
      const weekAgo = new Date(Date.now() - 7 * 24 * 60 * 60 * 1000);
      return updated > weekAgo;
    }).length,
  };

  const quickActions = [
    { label: t.dashboard.qaAddPatient, icon: '➕', action: () => navigateTo('patients', { addPatient: true }) },
    { label: t.dashboard.qaInteractions, icon: '⚠️', action: () => navigateTo('drug-matrix') },
    { label: t.dashboard.qaConsult, icon: '🤖', action: () => navigateTo('chat') },
    { label: t.dashboard.qaResearch, icon: '📚', action: () => navigateTo('research') },
  ];

  if (loading) {
    return (
      <div className="empty-state">
        <p>{t.loading.dashboard}</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>{t.dashboard.welcome(user?.name)}</h1>
        <p>{t.dashboard.subtitle}</p>
      </div>

      {/* Stats Cards */}
      <div className="dashboard-stats">
        <div className="stat-card-doc">
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.12)' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
          </div>
          <div className="stat-value">{stats.total}</div>
          <div className="stat-label">{t.dashboard.statTotal}</div>
        </div>

        <div className="stat-card-doc">
          <div className="stat-icon" style={{ background: 'rgba(251, 146, 60, 0.12)' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fb923c" strokeWidth="2"><path d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          </div>
          <div className="stat-value">{stats.withConditions}</div>
          <div className="stat-label">{t.dashboard.statConditions}</div>
        </div>

        <div className="stat-card-doc">
          <div className="stat-icon" style={{ background: 'rgba(34, 197, 94, 0.12)' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          </div>
          <div className="stat-value">{stats.recentlyUpdated}</div>
          <div className="stat-label">{t.dashboard.statRecent}</div>
        </div>

        <div className="stat-card-doc">
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.12)' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
          </div>
          <div className="stat-value">{patients.reduce((sum, p) => sum + (p.current_medications?.length || 0), 0)}</div>
          <div className="stat-label">{t.dashboard.statMeds}</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="dashboard-section">
        <div className="dashboard-section-header">
          <h2>{t.dashboard.qaHeading}</h2>
        </div>
        <div className="quick-actions">
          {quickActions.map((action, i) => (
            <button key={i} className="quick-action-btn" onClick={action.action}>
              <span style={{ fontSize: '18px' }}>{action.icon}</span>
              <span>{action.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Recent Patients */}
      <div className="dashboard-section">
        <div className="dashboard-section-header">
          <h2>{t.dashboard.yourPatients}</h2>
          <button onClick={() => navigateTo('patients')}>{t.dashboard.viewAll}</button>
        </div>

        {patients.length === 0 ? (
          <div className="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/>
              <line x1="19" y1="8" x2="19" y2="14"/><line x1="16" y1="11" x2="22" y2="11"/>
            </svg>
            <h3>{t.dashboard.emptyTitle}</h3>
            <p>{t.dashboard.emptyDesc}</p>
          </div>
        ) : (
          <div className="patient-list-compact">
            {patients.slice(0, 5).map(patient => (
              <div
                key={patient.patient_id}
                className="patient-row"
                onClick={() => navigateTo('patient-detail', { patientId: patient.patient_id })}
              >
                <div className="patient-row-avatar">
                  {patient.name?.charAt(0).toUpperCase() || '?'}
                </div>
                <div className="patient-row-info">
                  <div className="patient-row-name">{patient.name}</div>
                  <div className="patient-row-meta">
                    {t.dashboard.meta(patient.gender, patient.chronic_conditions?.length || 0, patient.current_medications?.length || 0)}
                  </div>
                </div>
                <div className="patient-row-badges">
                  {patient.chronic_conditions?.slice(0, 2).map((c, i) => (
                    <span key={i} className="badge badge-condition">{c}</span>
                  ))}
                  {patient.allergies?.length > 0 && (
                    <span className="badge badge-allergy">{t.dashboard.allergies(patient.allergies.length)}</span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default Dashboard;
