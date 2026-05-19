import { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import config from '../../api/config';

function PatientMedications() {
  const { profile } = useOutletContext();
  const [analyzing, setAnalyzing] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState('');

  const loading = profile === null;
  const medications = profile?.current_medications || [];

  const checkInteractions = async () => {
    setAnalyzing(true);
    setError('');
    setResults(null);
    const token = localStorage.getItem('token');
    const savedUser = JSON.parse(localStorage.getItem('user') || '{}');
    const patientId = savedUser.patientId || profile?.patient_id;

    try {
      const res = await fetch(`${config.API_URL}/api/drugs/analyze-patient`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({ patient_id: patientId }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || 'Failed to analyze medications');
      }
      const data = await res.json();
      setResults(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setAnalyzing(false);
    }
  };

  const getSeverityClass = (severity) => {
    if (!severity) return 'low';
    const s = typeof severity === 'string' ? severity.toLowerCase() : '';
    if (s.includes('major') || s.includes('contraindicated') || s.includes('high')) return 'high';
    if (s.includes('moderate')) return 'moderate';
    return 'low';
  };

  if (loading) {
    return <div className="patient-loading">Loading medications...</div>;
  }

  return (
    <div className="patient-medications-page">
      <div className="patient-dashboard-header">
        <h1>My Medications</h1>
        <p>View your current medications and check for potential interactions.</p>
      </div>

      {/* Current Medications */}
      <div className="patient-section">
        <div className="patient-section-header">
          <h2>Current Medications ({medications.length})</h2>
          {medications.length > 1 && (
            <button onClick={checkInteractions} disabled={analyzing}>
              {analyzing ? 'Analyzing...' : 'Check Interactions →'}
            </button>
          )}
        </div>

        {medications.length === 0 ? (
          <div className="patient-empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M10.5 1.5a4.5 4.5 0 00-4.5 4.5v12a4.5 4.5 0 009 0V6a4.5 4.5 0 00-4.5-4.5z"/><line x1="6" y1="12" x2="15" y2="12"/>
            </svg>
            <h3>No medications listed</h3>
            <p>Update your profile to add your current medications.</p>
          </div>
        ) : (
          <div className="medication-list">
            {medications.map((med, i) => (
              <div key={i} className="medication-item">
                <div className="medication-icon">
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2">
                    <path d="M10.5 1.5a4.5 4.5 0 00-4.5 4.5v12a4.5 4.5 0 009 0V6a4.5 4.5 0 00-4.5-4.5z"/><line x1="6" y1="12" x2="15" y2="12"/>
                  </svg>
                </div>
                <span className="medication-name">{med}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Interaction Results */}
      {error && (
        <div className="patient-section">
          <div className="patient-card" style={{ borderColor: 'rgba(239, 68, 68, 0.3)' }}>
            <p style={{ color: '#f87171', margin: 0 }}>{error}</p>
          </div>
        </div>
      )}

      {results && (
        <div className="patient-section">
          <div className="patient-section-header">
            <h2>Interaction Analysis</h2>
            <span style={{ fontSize: '13px', color: '#64748b' }}>
              {results.count || results.interactions?.length || 0} interaction(s) found
            </span>
          </div>

          {results.interactions?.length === 0 ? (
            <div className="patient-card">
              <div className="patient-empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="1.5">
                  <path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="10"/>
                </svg>
                <h3>No interactions detected</h3>
                <p>Your current medications appear to be safe together.</p>
              </div>
            </div>
          ) : (
            <div>
              {results.interactions?.map((interaction, i) => {
                const severity = getSeverityClass(interaction.severity);
                return (
                  <div key={i} className={`interaction-card severity-${severity}`}>
                    <div className="interaction-content" style={{ flex: 1 }}>
                      <h4>
                        {interaction.drug1_name || interaction.drug1_id} ↔ {interaction.drug2_name || interaction.drug2_id}
                      </h4>
                      <p>{interaction.description || interaction.effect || 'Potential interaction detected.'}</p>
                    </div>
                    <span className={`interaction-severity-badge ${severity}`}>
                      {interaction.severity || 'Unknown'}
                    </span>
                  </div>
                );
              })}
            </div>
          )}

          {/* Safe Alternatives */}
          {results.safe_alternatives?.length > 0 && (
            <div style={{ marginTop: '20px' }}>
              <div className="patient-section-header">
                <h2>Suggested Alternatives</h2>
              </div>
              {results.safe_alternatives.map((alt, i) => (
                <div key={i} className="patient-card" style={{ marginBottom: '8px' }}>
                  <div style={{ fontSize: '14px', fontWeight: 600, color: '#e2e8f0', marginBottom: '4px' }}>
                    {alt.original_drug_name} → {alt.new_drug_name}
                  </div>
                  {alt.reason && (
                    <p style={{ fontSize: '13px', color: '#94a3b8', margin: 0 }}>{alt.reason}</p>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default PatientMedications;
