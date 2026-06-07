import { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import config from '../api/config';
import '../App.css';

const API_URL = config.API_URL;

/* ------------------------------------------------------------------ */
/* Helpers                                                             */
/* ------------------------------------------------------------------ */

// Backend severity is a float in [0,1]. Map to a clinical label + color.
// Reference: backend/src/drugs/calculate_severity.py
function severityLabel(score) {
  if (score == null) return { label: 'Unknown', color: '#9ca3af', bg: 'rgba(156,163,175,0.15)', rank: 0 };
  if (score >= 0.95) return { label: 'Contraindicated', color: '#dc2626', bg: 'rgba(220,38,38,0.15)', rank: 6 };
  if (score >= 0.85) return { label: 'Critical',        color: '#ef4444', bg: 'rgba(239,68,68,0.15)',  rank: 5 };
  if (score >= 0.75) return { label: 'Major',           color: '#f97316', bg: 'rgba(249,115,22,0.15)', rank: 4 };
  if (score >= 0.6)  return { label: 'Moderate-High',   color: '#f59e0b', bg: 'rgba(245,158,11,0.15)', rank: 3 };
  if (score >= 0.4)  return { label: 'Moderate',        color: '#fbbf24', bg: 'rgba(251,191,36,0.15)', rank: 2 };
  if (score >= 0.2)  return { label: 'Mild',            color: '#a3e635', bg: 'rgba(163,230,53,0.15)', rank: 1 };
  return               { label: 'Minimal',         color: '#22c55e', bg: 'rgba(34,197,94,0.15)',  rank: 0 };
}

function authHeaders() {
  const token = localStorage.getItem('token');
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/* ------------------------------------------------------------------ */
/* Component                                                           */
/* ------------------------------------------------------------------ */

export default function DrugSearch() {
  const [user, setUser] = useState(null);
  const [theme, setTheme] = useState('dark');

  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searchError, setSearchError] = useState(null);
  const [includeSemantic, setIncludeSemantic] = useState(false);

  const [selectedDrugs, setSelectedDrugs] = useState([]);   // full Drug objects
  const [loadingDrug, setLoadingDrug] = useState(false);

  const [interaction, setInteraction] = useState(null);     // CheckDrugInteractionResponse
  const [checkingInteraction, setCheckingInteraction] = useState(false);
  const [interactionError, setInteractionError] = useState(null);

  const navigate = useNavigate();
  const searchAbortRef = useRef(null);

  /* ------------ auth / theme ------------ */
  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    if (!savedUser) {
      navigate('/login');
    } else {
      setUser(JSON.parse(savedUser));
    }
  }, [navigate]);

  useEffect(() => {
    document.body.className = theme;
  }, [theme]);

  /* ------------ search (debounced) ------------ */
  useEffect(() => {
    const q = searchQuery.trim();
    if (q.length < 2) {
      setSearchResults([]);
      setSearching(false);
      setSearchError(null);
      if (searchAbortRef.current) searchAbortRef.current.abort();
      return;
    }

    const timer = setTimeout(async () => {
      // Cancel any in-flight request
      if (searchAbortRef.current) searchAbortRef.current.abort();
      const controller = new AbortController();
      searchAbortRef.current = controller;

      setSearching(true);
      setSearchError(null);
      try {
        const url = `${API_URL}/api/drugs/search/${encodeURIComponent(q)}`
          + `?include_semantic_search=${includeSemantic}&min_similarity=0.3`;
        const res = await fetch(url, {
          headers: { ...authHeaders() },
          signal: controller.signal,
        });
        if (!res.ok) throw new Error(`Search failed (${res.status})`);
        const data = await res.json();
        // Backend shape: { success, query, results: [{drug_id, name, description, similarity_score}], count }
        setSearchResults(Array.isArray(data.results) ? data.results : []);
      } catch (err) {
        if (err.name !== 'AbortError') {
          console.error('Search error:', err);
          setSearchError(err.message || 'Search failed');
          setSearchResults([]);
        }
      } finally {
        setSearching(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery, includeSemantic]);

  /* ------------ interaction check when 2 drugs selected ------------ */
  useEffect(() => {
    let cancelled = false;
    const run = async () => {
      if (selectedDrugs.length !== 2) {
        setInteraction(null);
        setInteractionError(null);
        return;
      }
      setCheckingInteraction(true);
      setInteractionError(null);
      try {
        const [d1, d2] = selectedDrugs;
        const res = await fetch(
          `${API_URL}/api/drugs/interaction/${encodeURIComponent(d1.drug_id)}/${encodeURIComponent(d2.drug_id)}`,
          { headers: { ...authHeaders() } }
        );
        if (!res.ok) throw new Error(`Interaction check failed (${res.status})`);
        const data = await res.json();
        if (!cancelled) setInteraction(data);
      } catch (err) {
        if (!cancelled) {
          console.error('Interaction check error:', err);
          setInteractionError(err.message || 'Interaction check failed');
          setInteraction(null);
        }
      } finally {
        if (!cancelled) setCheckingInteraction(false);
      }
    };
    run();
    return () => { cancelled = true; };
  }, [selectedDrugs]);

  /* ------------ actions ------------ */
  const loadAndToggleDrug = useCallback(async (searchResult) => {
    // searchResult has { drug_id, name, description, similarity_score }
    const existingIdx = selectedDrugs.findIndex(d => d.drug_id === searchResult.drug_id);
    if (existingIdx !== -1) {
      setSelectedDrugs(selectedDrugs.filter(d => d.drug_id !== searchResult.drug_id));
      return;
    }

    setLoadingDrug(true);
    try {
      const res = await fetch(
        `${API_URL}/api/drugs/${encodeURIComponent(searchResult.drug_id)}?detail=high`,
        { headers: { ...authHeaders() } }
      );
      if (!res.ok) throw new Error(`Failed to load drug (${res.status})`);
      const drug = await res.json();
      setSelectedDrugs(prev => {
        const withoutDup = prev.filter(d => d.drug_id !== drug.drug_id);
        // Cap at 2 slots; drop the oldest to make room
        const next = withoutDup.length >= 2 ? [withoutDup[1], drug] : [...withoutDup, drug];
        return next;
      });
    } catch (err) {
      console.error('Load drug error:', err);
    } finally {
      setLoadingDrug(false);
    }
  }, [selectedDrugs]);

  const removeDrug = useCallback((drugId) => {
    setSelectedDrugs(prev => prev.filter(d => d.drug_id !== drugId));
  }, []);

  /* ------------ derived UI data ------------ */
  const filteredResults = useMemo(
    () => searchResults.filter(r => !selectedDrugs.some(d => d.drug_id === r.drug_id)),
    [searchResults, selectedDrugs]
  );

  const worstSeverity = useMemo(() => {
    if (!interaction) return null;
    return severityLabel(interaction.overall_severity);
  }, [interaction]);

  if (!user) return null;

  /* ------------ render ------------ */
  return (
    <div className={`app ${theme}`}>
      <div className="main" style={{ width: '100%' }}>
        <div className="header">
          <div className="header-left">
            <button className="menu-btn" onClick={() => navigate('/chat')} aria-label="Back">←</button>
            <h2>Drug Search & Interactions</h2>
          </div>
          <div className="header-right">
            <label className="theme-toggle">
              <input
                type="checkbox"
                checked={theme === 'dark'}
                onChange={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              />
              <span className="slider" />
            </label>
          </div>
        </div>

        <div style={{ display: 'flex', height: 'calc(100vh - 60px)' }}>
          {/* ── Sidebar ── */}
          <div className="patients-sidebar">
            <div
              style={{
                padding: '16px',
                borderBottom: theme === 'dark'
                  ? '1px solid rgba(59, 130, 246, 0.2)'
                  : '1px solid #e5e5e5',
                display: 'flex',
                flexDirection: 'column',
                gap: '10px',
              }}
            >
              <input
                type="text"
                placeholder="Search drugs, brands or synonyms…"
                className="search-input"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              <label
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  fontSize: '12px',
                  opacity: 0.8,
                  cursor: 'pointer',
                  userSelect: 'none',
                }}
              >
                <input
                  type="checkbox"
                  checked={includeSemantic}
                  onChange={(e) => setIncludeSemantic(e.target.checked)}
                />
                Semantic search (conditions, indications)
              </label>
              <div style={{ fontSize: '12px', opacity: 0.6 }}>
                Select up to <strong>2 drugs</strong> to check interactions.
              </div>
            </div>

            <div style={{ overflowY: 'auto', flex: 1 }}>
              {/* Selected drugs (pinned at top) */}
              {selectedDrugs.map((drug) => (
                <div
                  key={`sel-${drug.drug_id}`}
                  className="patient-item active"
                  onClick={() => removeDrug(drug.drug_id)}
                  title="Click to deselect"
                >
                  <div className="patient-avatar">💊</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        fontWeight: 600,
                        fontSize: 14,
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {drug.name}
                    </div>
                    <div style={{ fontSize: 12, opacity: 0.7, marginTop: 2 }}>
                      {drug.drug_id} · Selected
                    </div>
                  </div>
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="18" y1="6" x2="6" y2="18" />
                    <line x1="6" y1="6" x2="18" y2="18" />
                  </svg>
                </div>
              ))}

              {/* Search state messages */}
              {searching && (
                <div style={{ padding: '14px 16px', fontSize: 13, opacity: 0.7 }}>Searching…</div>
              )}
              {searchError && !searching && (
                <div style={{ padding: '14px 16px', fontSize: 13, color: '#ef4444' }}>
                  {searchError}
                </div>
              )}
              {!searching && !searchError && searchQuery.trim().length >= 2 && filteredResults.length === 0 && (
                <div style={{ padding: '14px 16px', fontSize: 13, opacity: 0.6 }}>
                  No drugs matched “{searchQuery}”.
                </div>
              )}
              {!searching && searchQuery.trim().length > 0 && searchQuery.trim().length < 2 && (
                <div style={{ padding: '14px 16px', fontSize: 13, opacity: 0.6 }}>
                  Type at least 2 characters.
                </div>
              )}

              {/* Results */}
              {filteredResults.map((drug) => (
                <div
                  key={drug.drug_id}
                  className="patient-item"
                  onClick={() => loadAndToggleDrug(drug)}
                >
                  <div className="patient-avatar">💊</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div
                      style={{
                        fontWeight: 600,
                        fontSize: 14,
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {drug.name}
                    </div>
                    <div
                      style={{
                        fontSize: 12,
                        opacity: 0.7,
                        marginTop: 2,
                        whiteSpace: 'nowrap',
                        overflow: 'hidden',
                        textOverflow: 'ellipsis',
                      }}
                    >
                      {drug.drug_id}
                      {typeof drug.similarity_score === 'number' && (
                        <> · match {Math.round(drug.similarity_score * 100)}%</>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* ── Main panel ── */}
          <div className="patient-details">
            {loadingDrug && selectedDrugs.length === 0 ? (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', opacity: 0.6 }}>
                Loading drug details…
              </div>
            ) : selectedDrugs.length > 0 ? (
              <div style={{ padding: 24, overflowY: 'auto', height: '100%' }}>
                {/* Interaction block */}
                {selectedDrugs.length === 2 && (
                  <InteractionBlock
                    theme={theme}
                    loading={checkingInteraction}
                    error={interactionError}
                    interaction={interaction}
                    worstSeverity={worstSeverity}
                    drugs={selectedDrugs}
                  />
                )}

                {/* Drug detail cards */}
                {selectedDrugs.map((drug) => (
                  <DrugDetailCard key={drug.drug_id} drug={drug} />
                ))}
              </div>
            ) : (
              <EmptyState />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ------------------------------------------------------------------ */
/* Subcomponents                                                       */
/* ------------------------------------------------------------------ */

function InteractionBlock({ theme, loading, error, interaction, worstSeverity, drugs }) {
  const [d1, d2] = drugs;
  const found = !loading && !error && interaction && interaction.count > 0;
  const clear = !loading && !error && interaction && interaction.count === 0;

  const sev = worstSeverity || severityLabel(null);

  const borderColor = loading
    ? '#3b82f6'
    : error
      ? '#ef4444'
      : found
        ? sev.color
        : '#10b981';

  return (
    <div className="detail-section">
      <h2 style={{ fontSize: 24, marginBottom: 16 }}>Drug Interaction Analysis</h2>
      <div
        style={{
          padding: 16,
          background: found
            ? (theme === 'dark' ? 'rgba(251, 191, 36, 0.08)' : '#fef9c3')
            : clear
              ? (theme === 'dark' ? 'rgba(16, 185, 129, 0.08)' : '#d1fae5')
              : (theme === 'dark' ? 'rgba(59, 130, 246, 0.08)' : '#ede9fe'),
          borderRadius: 8,
          borderLeft: `4px solid ${borderColor}`,
          marginBottom: 24,
        }}
      >
        <div style={{ fontWeight: 600, marginBottom: 8, fontSize: 16 }}>
          {loading && '⏳ Checking interactions…'}
          {error && `⚠️ ${error}`}
          {found && '⚠️ Interaction Found'}
          {clear && '✓ No Documented Interaction'}
        </div>

        {loading && (
          <div style={{ opacity: 0.75, fontSize: 14 }}>
            Looking up interactions for {d1.name} + {d2.name}…
          </div>
        )}

        {clear && (
          <div style={{ fontSize: 14, opacity: 0.85 }}>
            No documented interaction between <strong>{d1.name}</strong> and <strong>{d2.name}</strong> in DrugBank.
            This does not guarantee safety — always consult a clinician.
          </div>
        )}

        {found && (
          <>
            <div style={{ marginBottom: 8 }}>
              <strong>{d1.name}</strong> + <strong>{d2.name}</strong>
            </div>
            <div style={{ marginBottom: 12 }}>
              <span
                style={{
                  padding: '2px 10px',
                  borderRadius: 6,
                  fontSize: 12,
                  fontWeight: 700,
                  textTransform: 'uppercase',
                  background: sev.bg,
                  color: sev.color,
                  border: `1px solid ${sev.color}`,
                }}
              >
                Overall severity: {sev.label}
                {interaction.overall_severity != null
                  && ` (${interaction.overall_severity.toFixed(2)})`}
              </span>
            </div>

            {/* Each individual interaction row */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              {interaction.interactions.map((it, idx) => {
                const rowSev = severityLabel(it.severity);
                return (
                  <div
                    key={idx}
                    style={{
                      padding: '10px 12px',
                      borderRadius: 6,
                      background: theme === 'dark'
                        ? 'rgba(255,255,255,0.03)'
                        : 'rgba(0,0,0,0.02)',
                      borderLeft: `3px solid ${rowSev.color}`,
                    }}
                  >
                    <div style={{ fontSize: 12, opacity: 0.75, marginBottom: 4 }}>
                      <strong>{it.drug1_name}</strong> → <strong>{it.drug2_name}</strong>{' '}
                      <span
                        style={{
                          display: 'inline-block',
                          padding: '1px 6px',
                          borderRadius: 4,
                          fontSize: 10,
                          fontWeight: 700,
                          textTransform: 'uppercase',
                          background: rowSev.bg,
                          color: rowSev.color,
                          marginLeft: 6,
                        }}
                      >
                        {rowSev.label}
                      </span>
                    </div>
                    <div style={{ fontSize: 14, lineHeight: 1.5 }}>{it.description}</div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

function DrugDetailCard({ drug }) {
  const present = (v) => v && v !== 'N/A' && v !== '';

  return (
    <div style={{ marginBottom: 32 }}>
      <div className="detail-section">
        <h1 style={{ fontSize: 28, marginBottom: 8 }}>{drug.name}</h1>
        <div style={{ opacity: 0.7, marginBottom: 16, fontSize: 13 }}>
          {drug.drug_id}{drug.drug_type ? ` · ${drug.drug_type}` : ''}
        </div>
        <div className="info-grid">
          <div className="info-card">
            <div className="info-label">Drug ID</div>
            <div className="info-value">{drug.drug_id}</div>
          </div>
          <div className="info-card">
            <div className="info-label">Type</div>
            <div className="info-value">{drug.drug_type || 'N/A'}</div>
          </div>
          {Array.isArray(drug.groups) && drug.groups.length > 0 && (
            <div className="info-card">
              <div className="info-label">Status</div>
              <div className="info-value" style={{ fontSize: 15, textTransform: 'capitalize' }}>
                {drug.groups.join(', ')}
              </div>
            </div>
          )}
        </div>
      </div>

      {present(drug.description) && (
        <div className="detail-section">
          <h3 className="section-title">Description</h3>
          <div className="info-row">{drug.description}</div>
        </div>
      )}

      {present(drug.indication) && (
        <div className="detail-section">
          <h3 className="section-title">Indication</h3>
          <div className="info-row">{drug.indication}</div>
        </div>
      )}

      {present(drug.mechanism_of_action) && (
        <div className="detail-section">
          <h3 className="section-title">Mechanism of Action</h3>
          <div className="info-row">{drug.mechanism_of_action}</div>
        </div>
      )}

      {present(drug.pharmacodynamics) && (
        <div className="detail-section">
          <h3 className="section-title">Pharmacodynamics</h3>
          <div className="info-row">{drug.pharmacodynamics}</div>
        </div>
      )}

      {(present(drug.absorption) || present(drug.metabolism) || present(drug.half_life)
        || present(drug.protein_binding) || present(drug.route_of_elimination)
        || present(drug.volume_of_distribution) || present(drug.clearance)) && (
        <div className="detail-section">
          <h3 className="section-title">Pharmacokinetics</h3>
          {present(drug.absorption)            && <div className="info-row"><strong>Absorption:</strong> {drug.absorption}</div>}
          {present(drug.metabolism)            && <div className="info-row"><strong>Metabolism:</strong> {drug.metabolism}</div>}
          {present(drug.half_life)             && <div className="info-row"><strong>Half-life:</strong> {drug.half_life}</div>}
          {present(drug.protein_binding)       && <div className="info-row"><strong>Protein binding:</strong> {drug.protein_binding}</div>}
          {present(drug.route_of_elimination)  && <div className="info-row"><strong>Elimination:</strong> {drug.route_of_elimination}</div>}
          {present(drug.volume_of_distribution)&& <div className="info-row"><strong>Volume of distribution:</strong> {drug.volume_of_distribution}</div>}
          {present(drug.clearance)             && <div className="info-row"><strong>Clearance:</strong> {drug.clearance}</div>}
        </div>
      )}

      {present(drug.toxicity) && (
        <div className="detail-section">
          <h3 className="section-title">Toxicity</h3>
          <div className="info-row">{drug.toxicity}</div>
        </div>
      )}

      {Array.isArray(drug.synonyms) && drug.synonyms.length > 0 && (
        <div className="detail-section">
          <h3 className="section-title">Also known as</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
            {drug.synonyms.slice(0, 20).map((s, i) => (
              <span
                key={i}
                style={{
                  fontSize: 12,
                  padding: '3px 8px',
                  borderRadius: 12,
                  background: 'rgba(59, 130, 246,0.12)',
                  color: '#60a5fa',
                }}
              >
                {s}
              </span>
            ))}
          </div>
        </div>
      )}

      {Array.isArray(drug.categories) && drug.categories.length > 0 && (
        <div className="detail-section">
          <h3 className="section-title">Categories</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>
            {drug.categories.slice(0, 30).map((cat, i) => (
              <span key={i} className="badge badge-warning">{cat}</span>
            ))}
          </div>
        </div>
      )}

      {Array.isArray(drug.food_interactions) && drug.food_interactions.length > 0 && (
        <div className="detail-section">
          <h3 className="section-title">Food Interactions</h3>
          <ul style={{ paddingLeft: 20 }}>
            {drug.food_interactions.slice(0, 20).map((fi, i) => (
              <li key={i} style={{ marginBottom: 4 }}>{fi}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}

function EmptyState() {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        height: '100%',
        opacity: 0.55,
      }}
    >
      <div style={{ textAlign: 'center', maxWidth: 360 }}>
        <svg
          width="64" height="64" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="1.5"
          style={{ margin: '0 auto 16px' }}
        >
          <circle cx="11" cy="11" r="8" />
          <line x1="21" y1="21" x2="16.65" y2="16.65" />
        </svg>
        <div style={{ fontSize: 18, fontWeight: 600, marginBottom: 8 }}>
          Search for a drug
        </div>
        <div style={{ fontSize: 14, lineHeight: 1.5 }}>
          Start typing in the sidebar to look up drug details. Pick any two drugs to
          analyze their interactions with DrugBank data.
        </div>
      </div>
    </div>
  );
}
