import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import config from '../api/config';
import '../App.css';

const API_URL = config.API_URL;

export default function DrugSearch() {
  const [user, setUser] = useState(null);
  const [theme, setTheme] = useState('dark');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [selectedDrugs, setSelectedDrugs] = useState([]);
  const [interaction, setInteraction] = useState(null);
  const [checkingInteraction, setCheckingInteraction] = useState(false);
  const navigate = useNavigate();

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


  useEffect(() => {
    const search = async () => {
      if (searchQuery.length < 2) {
        setSearchResults([]);
        return;
      }
      try {
        const res = await fetch(`${API_URL}/api/drug-search/search/${searchQuery}`);
        const data = await res.json();
        setSearchResults(data.drugs || []);
      } catch (err) {
        console.error('Search error:', err);
      }
    };
    const timer = setTimeout(search, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

  useEffect(() => {
    const checkInteractions = async () => {
      if (selectedDrugs.length === 2) {
        setCheckingInteraction(true);
        try {
          const res = await fetch(`${API_URL}/api/drug-search/interaction/${selectedDrugs[0].drug_name}/${selectedDrugs[1].drug_name}`);
          const data = await res.json();
          if (res.ok) setInteraction(data);
        } catch (err) {
          console.error('Interaction check error:', err);
        } finally {
          setCheckingInteraction(false);
        }
      } else {
        setInteraction(null);
      }
    };
    checkInteractions();
  }, [selectedDrugs]);

  const toggleDrugSelection = async (drugName) => {
    const existing = selectedDrugs.find(d => d.drug_name === drugName);
    if (existing) {
      setSelectedDrugs(selectedDrugs.filter(d => d.drug_name !== drugName));
    } else {
      if (selectedDrugs.length >= 2) {
        setSelectedDrugs([selectedDrugs[1]]);
      }
      try {
        const res = await fetch(`${API_URL}/api/drug-search/${drugName}`);
        const data = await res.json();
        if (res.ok) setSelectedDrugs([...selectedDrugs.filter(d => d.drug_name !== drugName), data]);
      } catch (err) {
        console.error('Load drug error:', err);
      }
    }
  };

  if (!user) return null;

  return (
    <div className={`app ${theme}`}>
      <div className="main" style={{ width: '100%' }}>
        <div className="header">
          <div className="header-left">
            <button className="menu-btn" onClick={() => navigate('/')}>←</button>
            <h2>Drug Search & Interactions</h2>
          </div>
          <div className="header-right">
            <label className="theme-toggle">
              <input type="checkbox" checked={theme === 'dark'} onChange={() => setTheme(theme === 'dark' ? 'light' : 'dark')} />
              <span className="slider"></span>
            </label>
          </div>
        </div>
        
        <div style={{ display: 'flex', height: 'calc(100vh - 60px)' }}>
          <div className="patients-sidebar">
            <div style={{ padding: '16px', borderBottom: theme === 'dark' ? '1px solid rgba(139, 92, 246, 0.2)' : '1px solid #e5e5e5' }}>
              <input 
                type="text" 
                placeholder="Search drugs..."
                className="search-input"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div style={{ overflowY: 'auto', flex: 1 }}>
              {selectedDrugs.map((drug, idx) => (
                <div 
                  key={`selected-${idx}`}
                  className="patient-item active"
                  onClick={() => toggleDrugSelection(drug.drug_name)}
                >
                  <div className="patient-avatar">💊</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: '600', fontSize: '14px' }}>{drug.drug_name}</div>
                    <div style={{ fontSize: '12px', opacity: 0.7, marginTop: '2px' }}>Selected</div>
                  </div>
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polyline points="20 6 9 17 4 12"/>
                  </svg>
                </div>
              ))}
              {searchResults
                .filter(drug => !selectedDrugs.some(d => d.drug_name === drug.name))
                .map((drug, idx) => (
                  <div 
                    key={idx}
                    className="patient-item"
                    onClick={() => toggleDrugSelection(drug.name)}
                  >
                    <div className="patient-avatar">💊</div>
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: '600', fontSize: '14px' }}>{drug.name}</div>
                      <div style={{ fontSize: '12px', opacity: 0.7, marginTop: '2px' }}>Click to select</div>
                    </div>
                  </div>
                ))}
            </div>
          </div>

          <div className="patient-details">
            {selectedDrugs.length > 0 ? (
              <div style={{ padding: '24px', overflowY: 'auto', height: '100%' }}>
                {selectedDrugs.length === 2 && interaction && (
                  <div className="detail-section">
                    <h2 style={{ fontSize: '24px', marginBottom: '16px' }}>Drug Interaction Analysis</h2>
                    <div style={{
                      padding: '16px',
                      background: interaction.interaction_found ? (theme === 'dark' ? 'rgba(251, 191, 36, 0.1)' : '#fef3c7') : (theme === 'dark' ? 'rgba(16, 185, 129, 0.1)' : '#d1fae5'),
                      borderRadius: '8px',
                      borderLeft: `4px solid ${interaction.interaction_found ? '#fbbf24' : '#10b981'}`,
                      marginBottom: '24px'
                    }}>
                      <div style={{ fontWeight: '600', marginBottom: '8px', fontSize: '16px' }}>
                        {interaction.interaction_found ? '⚠️ Interaction Found' : '✓ No Interaction Found'}
                      </div>
                      {interaction.interaction_found ? (
                        <>
                          <div style={{ marginBottom: '8px' }}><strong>{interaction.drug1}</strong> + <strong>{interaction.drug2}</strong></div>
                          <div>{interaction.description}</div>
                        </>
                      ) : (
                        <div>{interaction.message}</div>
                      )}
                    </div>
                  </div>
                )}

                {selectedDrugs.map((selectedDrug, idx) => (
                  <div key={idx}>
                    <div className="detail-section">
                      <h1 style={{ fontSize: '28px', marginBottom: '8px' }}>{selectedDrug.drug_name}</h1>
                      {selectedDrug.is_synonym && <div style={{ opacity: 0.7, marginBottom: '16px' }}>Also known as: {selectedDrug.queried_name}</div>}
                      <div className="info-grid">
                        <div className="info-card">
                          <div className="info-label">Drug ID</div>
                          <div className="info-value">{selectedDrug.drug_id}</div>
                        </div>
                        <div className="info-card">
                          <div className="info-label">State</div>
                          <div className="info-value">{selectedDrug.state || 'N/A'}</div>
                        </div>
                      </div>
                    </div>

                    {selectedDrug.description && selectedDrug.description !== 'N/A' && (
                      <div className="detail-section">
                        <h3 className="section-title">Description</h3>
                        <div className="info-row">{selectedDrug.description}</div>
                      </div>
                    )}

                    {selectedDrug.indication && selectedDrug.indication !== 'N/A' && (
                      <div className="detail-section">
                        <h3 className="section-title">Indication</h3>
                        <div className="info-row">{selectedDrug.indication}</div>
                      </div>
                    )}

                    {selectedDrug.mechanism_of_action && selectedDrug.mechanism_of_action !== 'N/A' && (
                      <div className="detail-section">
                        <h3 className="section-title">Mechanism of Action</h3>
                        <div className="info-row">{selectedDrug.mechanism_of_action}</div>
                      </div>
                    )}

                    {selectedDrug.pharmacodynamics && selectedDrug.pharmacodynamics !== 'N/A' && (
                      <div className="detail-section">
                        <h3 className="section-title">Pharmacodynamics</h3>
                        <div className="info-row">{selectedDrug.pharmacodynamics}</div>
                      </div>
                    )}

                    <div className="detail-section">
                      <h3 className="section-title">Pharmacokinetics</h3>
                      {selectedDrug.absorption && selectedDrug.absorption !== 'N/A' && <div className="info-row"><strong>Absorption:</strong> {selectedDrug.absorption}</div>}
                      {selectedDrug.metabolism && selectedDrug.metabolism !== 'N/A' && <div className="info-row"><strong>Metabolism:</strong> {selectedDrug.metabolism}</div>}
                      {selectedDrug.half_life && selectedDrug.half_life !== 'N/A' && <div className="info-row"><strong>Half Life:</strong> {selectedDrug.half_life}</div>}
                      {selectedDrug.protein_binding && selectedDrug.protein_binding !== 'N/A' && <div className="info-row"><strong>Protein Binding:</strong> {selectedDrug.protein_binding}</div>}
                      {selectedDrug.route_of_elimination && selectedDrug.route_of_elimination !== 'N/A' && <div className="info-row"><strong>Route of Elimination:</strong> {selectedDrug.route_of_elimination}</div>}
                    </div>

                    {selectedDrug.toxicity && selectedDrug.toxicity !== 'N/A' && (
                      <div className="detail-section">
                        <h3 className="section-title">Toxicity</h3>
                        <div className="info-row">{selectedDrug.toxicity}</div>
                      </div>
                    )}

                    {selectedDrug.groups && selectedDrug.groups.length > 0 && (
                      <div className="detail-section">
                        <h3 className="section-title">Groups</h3>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                          {selectedDrug.groups.map((group, i) => (
                            <span key={i} className="badge badge-success">{group}</span>
                          ))}
                        </div>
                      </div>
                    )}

                    {selectedDrug.categories && selectedDrug.categories.length > 0 && (
                      <div className="detail-section">
                        <h3 className="section-title">Categories</h3>
                        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                          {selectedDrug.categories.map((cat, i) => (
                            <span key={i} className="badge badge-warning">{cat}</span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', opacity: 0.5 }}>
                <div style={{ textAlign: 'center' }}>
                  <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: '0 auto 16px' }}>
                    <circle cx="12" cy="12" r="10"/>
                    <line x1="12" y1="8" x2="12" y2="12"/>
                    <line x1="12" y1="16" x2="12.01" y2="16"/>
                  </svg>
                  <div style={{ fontSize: '18px' }}>Select drugs to view details</div>
                  <div style={{ fontSize: '14px', marginTop: '8px' }}>Select 2 drugs to check interactions</div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
