import { useDoctorPanel } from './panelContext';

function Dashboard() {
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
    { label: 'Add Patient', icon: '➕', action: () => navigateTo('patients', { addPatient: true }) },
    { label: 'Interaction Matrix', icon: '⚠️', action: () => navigateTo('drug-matrix') },
    { label: 'AI Consultation', icon: '🤖', action: () => navigateTo('chat') },
    { label: 'Search Literature', icon: '📚', action: () => navigateTo('research') },
  ];

  if (loading) {
    return (
      <div className="empty-state">
        <p>Loading dashboard...</p>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>Welcome back, Dr. {user?.name?.split(' ').pop() || user?.name}</h1>
        <p>Here's an overview of your patients and recent activity.</p>
      </div>

      {/* Stats Cards */}
      <div className="dashboard-stats">
        <div className="stat-card-doc">
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.12)' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2"><path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/></svg>
          </div>
          <div className="stat-value">{stats.total}</div>
          <div className="stat-label">Total Patients</div>
        </div>

        <div className="stat-card-doc">
          <div className="stat-icon" style={{ background: 'rgba(251, 146, 60, 0.12)' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#fb923c" strokeWidth="2"><path d="M12 9v2m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          </div>
          <div className="stat-value">{stats.withConditions}</div>
          <div className="stat-label">With Chronic Conditions</div>
        </div>

        <div className="stat-card-doc">
          <div className="stat-icon" style={{ background: 'rgba(34, 197, 94, 0.12)' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="2"><polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/></svg>
          </div>
          <div className="stat-value">{stats.recentlyUpdated}</div>
          <div className="stat-label">Updated This Week</div>
        </div>

        <div className="stat-card-doc">
          <div className="stat-icon" style={{ background: 'rgba(59, 130, 246, 0.12)' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" strokeWidth="2"><rect x="3" y="3" width="18" height="18" rx="2"/><path d="M3 9h18M9 21V9"/></svg>
          </div>
          <div className="stat-value">{patients.reduce((sum, p) => sum + (p.current_medications?.length || 0), 0)}</div>
          <div className="stat-label">Active Medications</div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="dashboard-section">
        <div className="dashboard-section-header">
          <h2>Quick Actions</h2>
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
          <h2>Your Patients</h2>
          <button onClick={() => navigateTo('patients')}>View all →</button>
        </div>

        {patients.length === 0 ? (
          <div className="empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/>
              <line x1="19" y1="8" x2="19" y2="14"/><line x1="16" y1="11" x2="22" y2="11"/>
            </svg>
            <h3>No patients yet</h3>
            <p>Add your first patient to get started with medication safety analysis.</p>
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
                    {patient.gender || 'Unknown'} • {patient.chronic_conditions?.length || 0} conditions • {patient.current_medications?.length || 0} medications
                  </div>
                </div>
                <div className="patient-row-badges">
                  {patient.chronic_conditions?.slice(0, 2).map((c, i) => (
                    <span key={i} className="badge badge-condition">{c}</span>
                  ))}
                  {patient.allergies?.length > 0 && (
                    <span className="badge badge-allergy">{patient.allergies.length} allergies</span>
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
