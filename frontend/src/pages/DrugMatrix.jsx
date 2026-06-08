import { useState, useEffect, useRef } from 'react';
import config from '../api/config';
import { useT } from '../i18n/lang';
import { DRUG_MATRIX_STRINGS } from '../i18n/strings/drugMatrix';
import './DrugMatrix.css';

// Score → severity bucket. The bucket name (e.g. "Major") is a stable
// key used to look up the localised label in DRUG_MATRIX_STRINGS.severities.
function severityBucket(score) {
  if (score == null) return { key: 'Unknown', color: '#9ca3af', bg: 'rgba(156,163,175,0.12)' };
  if (score >= 0.95) return { key: 'Contraindicated', color: '#dc2626', bg: 'rgba(220,38,38,0.18)' };
  if (score >= 0.85) return { key: 'Critical', color: '#ef4444', bg: 'rgba(239,68,68,0.18)' };
  if (score >= 0.75) return { key: 'Major', color: '#f97316', bg: 'rgba(249,115,22,0.18)' };
  if (score >= 0.6) return { key: 'Moderate-High', color: '#f59e0b', bg: 'rgba(245,158,11,0.18)' };
  if (score >= 0.4) return { key: 'Moderate', color: '#fbbf24', bg: 'rgba(251,191,36,0.18)' };
  if (score >= 0.2) return { key: 'Mild', color: '#a3e635', bg: 'rgba(163,230,53,0.18)' };
  return { key: 'Minimal', color: '#22c55e', bg: 'rgba(34,197,94,0.18)' };
}

/**
 * DrugMatrix — embeddable view for the Chat page.
 *
 * No layout chrome (no `.app`, no header, no theme toggle). The host page
 * is responsible for placement and theming. Pass `user` so the component
 * can decide whether to expose patient-load options (doctors only).
 */
function DrugMatrix({ user, initialPatientId = null }) {
  const t = useT(DRUG_MATRIX_STRINGS);
  const sevLabel = (key) => t.severities[key] || key;

  const [drugs, setDrugs] = useState([]); // [{drug_id, name}]
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [interactions, setInteractions] = useState([]);
  const [checking, setChecking] = useState(false);
  const [selectedCell, setSelectedCell] = useState(null);
  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState('');
  const searchTimer = useRef(null);

  // Load patients for quick-load feature (doctors only) and optionally
  // hydrate the matrix from a patient passed in by the host.
  useEffect(() => {
    if (!user) return;
    if (user.isDoctor) loadPatients();
    if (initialPatientId) loadPatientMeds(initialPatientId);
  }, [user, initialPatientId]);

  const loadPatients = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${config.API_URL}/api/users/doctors/patients`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setPatients(Array.isArray(data) ? data : []);
      }
    } catch (err) {
      console.error('Failed to load patients:', err);
    }
  };

  const loadPatientMeds = async (patientId) => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${config.API_URL}/api/users/profile/patient/${patientId}`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setSelectedPatient(patientId);
        if (data.current_medications?.length > 0) {
          // Resolve medication names → drug IDs
          const resolved = [];
          for (const medName of data.current_medications) {
            const searchRes = await fetch(`${config.API_URL}/api/drugs/search/${encodeURIComponent(medName)}?limit=1`, {
              headers: { 'Authorization': `Bearer ${token}` },
            });
            if (searchRes.ok) {
              const data = await searchRes.json();
              const results = data.results || data;
              if (results.length > 0) {
                resolved.push({ drug_id: results[0].drug_id, name: results[0].name });
              }
            }
          }
          setDrugs(resolved);
        }
      }
    } catch (err) {
      console.error('Failed to load patient medications:', err);
    }
  };

  // Debounced drug search
  useEffect(() => {
    if (searchTimer.current) clearTimeout(searchTimer.current);
    const q = searchQuery.trim();
    if (q.length < 2) {
      setSearchResults([]);
      return;
    }
    setSearching(true);
    searchTimer.current = setTimeout(async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await fetch(`${config.API_URL}/api/drugs/search/${encodeURIComponent(q)}?limit=8`, {
          headers: { 'Authorization': `Bearer ${token}` },
        });
        if (res.ok) {
          const data = await res.json();
          const results = data.results || data;
          setSearchResults(results.filter(d => !drugs.some(existing => existing.drug_id === d.drug_id)));
        }
      } catch (err) {
        console.error('Search failed:', err);
      } finally {
        setSearching(false);
      }
    }, 300);
  }, [searchQuery, drugs]);

  // Re-check interactions whenever the drug list changes
  useEffect(() => {
    if (drugs.length >= 2) {
      checkInteractions();
    } else {
      setInteractions([]);
    }
  }, [drugs]);

  const checkInteractions = async () => {
    setChecking(true);
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${config.API_URL}/api/drugs/interactions`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify({ drug_ids: drugs.map(d => d.drug_id) }),
      });
      if (res.ok) {
        const data = await res.json();
        setInteractions(data.interactions || []);
      }
    } catch (err) {
      console.error('Interaction check failed:', err);
    } finally {
      setChecking(false);
    }
  };

  const addDrug = (drug) => {
    if (!drugs.some(d => d.drug_id === drug.drug_id)) {
      setDrugs([...drugs, { drug_id: drug.drug_id, name: drug.name }]);
    }
    setSearchQuery('');
    setSearchResults([]);
  };

  const removeDrug = (drugId) => {
    setDrugs(drugs.filter(d => d.drug_id !== drugId));
    setSelectedCell(null);
  };

  const getInteraction = (drug1Id, drug2Id) => {
    return interactions.find(
      i => (i.drug1_id === drug1Id && i.drug2_id === drug2Id) ||
           (i.drug1_id === drug2Id && i.drug2_id === drug1Id)
    );
  };

  return (
    <div className="drug-matrix-page" style={{ padding: '24px 32px', overflowY: 'auto', height: '100%' }}>
      <div className="page-header">
        <h1>{t.title}</h1>
        <p>{t.subtitle}</p>
      </div>

      {/* Drug Input Section */}
      <div className="matrix-controls">
        <div className="matrix-search-section">
          <div className="matrix-search-box">
            <input
              type="text"
              placeholder={t.searchPlaceholder}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="matrix-search-input"
            />
            {searching && <span className="search-spinner" />}
            {searchResults.length > 0 && (
              <div className="matrix-search-dropdown">
                {searchResults.map(drug => (
                  <button
                    key={drug.drug_id}
                    className="matrix-search-result"
                    onClick={() => addDrug(drug)}
                  >
                    <span className="drug-result-name">{drug.name}</span>
                    <span className="drug-result-id">{drug.drug_id}</span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {patients.length > 0 && (
            <div className="matrix-patient-select">
              <select
                value={selectedPatient}
                onChange={(e) => {
                  if (e.target.value) loadPatientMeds(e.target.value);
                }}
              >
                <option value="">{t.loadFromPatient}</option>
                {patients.map(p => (
                  <option key={p.patient_id} value={p.patient_id}>
                    {p.name} ({t.patientMedsHint(p.current_medications?.length || 0)})
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {drugs.length > 0 && (
          <div className="matrix-drug-chips">
            {drugs.map(drug => (
              <span key={drug.drug_id} className="drug-chip">
                {drug.name}
                <button onClick={() => removeDrug(drug.drug_id)} className="chip-remove">×</button>
              </span>
            ))}
            {drugs.length > 0 && (
              <button className="chip-clear-all" onClick={() => { setDrugs([]); setSelectedCell(null); }}>
                {t.clearAll}
              </button>
            )}
          </div>
        )}
      </div>

      {/* Interaction Matrix */}
      {drugs.length >= 2 && (
        <div className="matrix-container">
          {checking && <div className="matrix-loading">{t.checking}</div>}
          <div className="matrix-grid-wrapper">
            <table className="interaction-matrix">
              <thead>
                <tr>
                  <th className="matrix-corner"></th>
                  {drugs.map(drug => (
                    <th key={drug.drug_id} className="matrix-header-cell">
                      <span className="matrix-header-label">{drug.name}</span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {drugs.map((rowDrug, rowIdx) => (
                  <tr key={rowDrug.drug_id}>
                    <td className="matrix-row-header">{rowDrug.name}</td>
                    {drugs.map((colDrug, colIdx) => {
                      if (rowIdx === colIdx) {
                        return <td key={colDrug.drug_id} className="matrix-cell diagonal">—</td>;
                      }
                      if (colIdx < rowIdx) {
                        return <td key={colDrug.drug_id} className="matrix-cell mirror"></td>;
                      }
                      const inter = getInteraction(rowDrug.drug_id, colDrug.drug_id);
                      const sev = inter ? severityBucket(inter.severity) : null;
                      const isSelected = selectedCell?.drug1 === rowDrug.drug_id && selectedCell?.drug2 === colDrug.drug_id;
                      return (
                        <td
                          key={colDrug.drug_id}
                          className={`matrix-cell ${inter ? 'has-interaction' : 'no-interaction'} ${isSelected ? 'selected' : ''}`}
                          style={inter ? { backgroundColor: sev.bg, borderColor: sev.color } : {}}
                          onClick={() => inter && setSelectedCell({ drug1: rowDrug.drug_id, drug2: colDrug.drug_id, interaction: inter })}
                        >
                          {inter ? (
                            <span className="cell-severity" style={{ color: sev.color }}>{sevLabel(sev.key)}</span>
                          ) : (
                            <span className="cell-safe">✓</span>
                          )}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          <div className="matrix-summary">
            <div className="summary-stat">
              <span className="summary-value">{drugs.length}</span>
              <span className="summary-label">{t.summaryDrugs}</span>
            </div>
            <div className="summary-stat">
              <span className="summary-value">{interactions.length}</span>
              <span className="summary-label">{t.summaryFound}</span>
            </div>
            <div className="summary-stat">
              <span className="summary-value" style={{ color: interactions.filter(i => i.severity >= 0.75).length > 0 ? '#ef4444' : '#22c55e' }}>
                {interactions.filter(i => i.severity >= 0.75).length}
              </span>
              <span className="summary-label">{t.summaryCritical}</span>
            </div>
          </div>
        </div>
      )}

      {drugs.length < 2 && (
        <div className="matrix-empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
            <rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/>
          </svg>
          <h3>{t.emptyTitle}</h3>
          <p>{user?.isDoctor ? t.emptyDescDoctor : t.emptyDescGeneric}</p>
        </div>
      )}

      {selectedCell && (
        <div className="interaction-detail-panel">
          <div className="detail-panel-header">
            <h3>
              <span className="badge badge-med">{selectedCell.interaction.drug1_name}</span>
              <span className="interaction-arrow">↔</span>
              <span className="badge badge-med">{selectedCell.interaction.drug2_name}</span>
            </h3>
            <button className="detail-close" onClick={() => setSelectedCell(null)}>×</button>
          </div>
          <div className="detail-panel-body">
            <div className="detail-severity-badge" style={{
              color: severityBucket(selectedCell.interaction.severity).color,
              background: severityBucket(selectedCell.interaction.severity).bg,
            }}>
              {sevLabel(severityBucket(selectedCell.interaction.severity).key)}
              {selectedCell.interaction.severity != null && (
                <span> ({(selectedCell.interaction.severity * 100).toFixed(0)}%)</span>
              )}
            </div>
            <p className="detail-description">{selectedCell.interaction.description}</p>
          </div>
        </div>
      )}

      {/* Severity legend lives at the bottom of the page so it doesn't
          intercept the eye on first load — users only need it when
          interpreting cell colours, which they do AFTER scanning the
          matrix or sample data. Keeping it last also means the legend
          appears under the empty-state hero, not above it. */}
      <div className="matrix-legend matrix-legend-footer">
        <span className="legend-title">{t.legendHeading}:</span>
        {[
          { key: 'Minimal', color: '#22c55e' },
          { key: 'Mild', color: '#a3e635' },
          { key: 'Moderate', color: '#fbbf24' },
          { key: 'Major', color: '#f97316' },
          { key: 'Critical', color: '#ef4444' },
          { key: 'Contraindicated', color: '#dc2626' },
        ].map(item => (
          <span key={item.key} className="legend-item">
            <span className="legend-dot" style={{ background: item.color }}></span>
            {sevLabel(item.key)}
          </span>
        ))}
      </div>
    </div>
  );
}

export default DrugMatrix;
