import { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import config from '../../api/config';
import LoadingScreen from '../../components/LoadingScreen';
import { useT } from '../../i18n/lang';
import { PATIENT_STRINGS } from '../../i18n/strings/patient';

function PatientMedications() {
  const t = useT(PATIENT_STRINGS);
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
        throw new Error(data.detail || t.medications.analysisError);
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
    return <LoadingScreen variant="inline" message={t.loading.medications} className="patient-loading" />;
  }

  return (
    <div className="patient-medications-page">
      <div className="patient-dashboard-header">
        <h1>{t.medications.title}</h1>
        <p>{t.medications.subtitle}</p>
      </div>

      {/* Current Medications */}
      <div className="patient-section">
        <div className="patient-section-header">
          <h2>{t.medications.sectionHeading(medications.length)}</h2>
          {medications.length > 1 && (
            <button onClick={checkInteractions} disabled={analyzing}>
              {analyzing ? t.medications.analysing : t.medications.checkButton}
            </button>
          )}
        </div>

        {medications.length === 0 ? (
          <div className="patient-empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M10.5 1.5a4.5 4.5 0 00-4.5 4.5v12a4.5 4.5 0 009 0V6a4.5 4.5 0 00-4.5-4.5z"/><line x1="6" y1="12" x2="15" y2="12"/>
            </svg>
            <h3>{t.medications.emptyTitle}</h3>
            <p>{t.medications.emptyDesc}</p>
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
            <h2>{t.medications.analysisHeading}</h2>
            <span style={{ fontSize: '13px', color: '#64748b' }}>
              {t.medications.analysisCount(results.count || results.interactions?.length || 0)}
            </span>
          </div>

          {results.interactions?.length === 0 ? (
            <div className="patient-card">
              <div className="patient-empty-state">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#22c55e" strokeWidth="1.5">
                  <path d="M9 12l2 2 4-4"/><circle cx="12" cy="12" r="10"/>
                </svg>
                <h3>{t.medications.noInteractionsTitle}</h3>
                <p>{t.medications.noInteractionsDesc}</p>
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
                      <p>{interaction.description || interaction.effect || t.medications.potentialInteraction}</p>
                    </div>
                    <span className={`interaction-severity-badge ${severity}`}>
                      {interaction.severity || t.medications.severityUnknown}
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
                <h2>{t.medications.alternativesHeading}</h2>
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
