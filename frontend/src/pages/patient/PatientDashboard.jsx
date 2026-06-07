import { useNavigate, useOutletContext } from 'react-router-dom';
import LoadingScreen from '../../components/LoadingScreen';
import { useT } from '../../i18n/lang';
import { PATIENT_STRINGS } from '../../i18n/strings/patient';

function PatientDashboard() {
  const t = useT(PATIENT_STRINGS);
  const { user, profile, doctors } = useOutletContext();
  const navigate = useNavigate();
  const loading = profile === null;

  const stats = {
    medications: profile?.current_medications?.length || 0,
    conditions: profile?.chronic_conditions?.length || 0,
    allergies: profile?.allergies?.length || 0,
    doctors: doctors?.length || 0,
  };

  const quickActions = [
    { label: t.dashboard.qaCheckInteractions, icon: '⚠️', action: () => navigate('/patient/medications') },
    { label: t.dashboard.qaProfile, icon: '👤', action: () => navigate('/patient/profile') },
    { label: t.dashboard.qaDoctors, icon: '🏥', action: () => navigate('/patient/doctors') },
    { label: t.dashboard.qaChat, icon: '🤖', action: () => window.open('/chat', '_blank') },
  ];

  if (loading) {
    return <LoadingScreen variant="inline" message={t.loading.dashboard} className="patient-loading" />;
  }

  return (
    <div className="patient-dashboard">
      <div className="patient-dashboard-header">
        <h1>{t.dashboard.welcome(user?.name)}</h1>
        <p>{t.dashboard.subtitle}</p>
      </div>

      {/* Stats Cards */}
      <div className="patient-stats">
        <div className="patient-stat-card">
          <div className="stat-icon" style={{ background: 'rgba(16, 185, 129, 0.12)' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2">
              <path d="M10.5 1.5a4.5 4.5 0 00-4.5 4.5v12a4.5 4.5 0 009 0V6a4.5 4.5 0 00-4.5-4.5z"/><line x1="6" y1="12" x2="15" y2="12"/>
            </svg>
          </div>
          <div className="stat-value">{stats.medications}</div>
          <div className="stat-label">{t.dashboard.statMedications}</div>
        </div>

        <div className="patient-stat-card">
          <div className="stat-icon" style={{ background: 'rgba(251, 146, 60, 0.12)' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fb923c" strokeWidth="2">
              <path d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
          </div>
          <div className="stat-value">{stats.conditions}</div>
          <div className="stat-label">{t.dashboard.statConditions}</div>
        </div>

        <div className="patient-stat-card">
          <div className="stat-icon" style={{ background: 'rgba(239, 68, 68, 0.12)' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2">
              <path d="M18.364 5.636a9 9 0 11-12.728 0M12 9v4"/>
            </svg>
          </div>
          <div className="stat-value">{stats.allergies}</div>
          <div className="stat-label">{t.dashboard.statAllergies}</div>
        </div>

        <div className="patient-stat-card">
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.12)' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2">
              <path d="M3 21h18"/><rect x="5" y="2" width="14" height="20" rx="2"/><path d="M9 8h1M9 12h1M14 8h1M14 12h1"/>
            </svg>
          </div>
          <div className="stat-value">{stats.doctors}</div>
          <div className="stat-label">{t.dashboard.statDoctors}</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="patient-section">
        <div className="patient-section-header">
          <h2>{t.dashboard.quickHeading}</h2>
        </div>
        <div className="patient-quick-actions">
          {quickActions.map((action, i) => (
            <button key={i} className="patient-quick-action-btn" onClick={action.action}>
              <span style={{ fontSize: '18px' }}>{action.icon}</span>
              <span>{action.label}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Health Summary */}
      <div className="patient-section">
        <div className="patient-section-header">
          <h2>{t.dashboard.summaryHeading}</h2>
          <button onClick={() => navigate('/patient/profile')}>{t.dashboard.viewFullProfile}</button>
        </div>
        <div className="patient-card">
          {profile?.chronic_conditions?.length > 0 && (
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '6px' }}>{t.dashboard.labelConditions}</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {profile.chronic_conditions.map((c, i) => (
                  <span key={i} className="patient-badge condition">{c}</span>
                ))}
              </div>
            </div>
          )}
          {profile?.allergies?.length > 0 && (
            <div style={{ marginBottom: '12px' }}>
              <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '6px' }}>{t.dashboard.labelAllergies}</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {profile.allergies.map((a, i) => (
                  <span key={i} className="patient-badge allergy">{a}</span>
                ))}
              </div>
            </div>
          )}
          {profile?.current_medications?.length > 0 && (
            <div>
              <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '6px' }}>{t.dashboard.labelMedications}</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                {profile.current_medications.map((m, i) => (
                  <span key={i} className="patient-badge medication">{m}</span>
                ))}
              </div>
            </div>
          )}
          {!profile?.chronic_conditions?.length && !profile?.allergies?.length && !profile?.current_medications?.length && (
            <div className="patient-empty-state">
              <h3>{t.dashboard.emptyTitle}</h3>
              <p>{t.dashboard.emptyDesc}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PatientDashboard;
