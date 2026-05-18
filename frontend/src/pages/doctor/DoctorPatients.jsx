import { useState, useEffect } from 'react';
import { useNavigate, useOutletContext, useSearchParams } from 'react-router-dom';
import config from '../../api/config';

function DoctorPatients() {
  const { user, patients: cachedPatients, setPatients: setCachedPatients } = useOutletContext();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [localPatients, setLocalPatients] = useState(null);
  const patients = localPatients ?? cachedPatients ?? [];
  const loading = cachedPatients === null && localPatients === null;
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [showAddModal, setShowAddModal] = useState(false);
  const [modalStep, setModalStep] = useState(1);
  const [saving, setSaving] = useState(false);

  // Form state
  const [form, setForm] = useState({
    name: '',
    email: '',
    date_of_birth: '',
    gender: 'male',
    notes: '',
  });
  const [conditions, setConditions] = useState([]);
  const [allergies, setAllergies] = useState([]);
  const [medications, setMedications] = useState([]);
  const [conditionInput, setConditionInput] = useState('');
  const [allergyInput, setAllergyInput] = useState('');
  const [medicationInput, setMedicationInput] = useState('');

  useEffect(() => {
    if (searchParams.get('add') === 'true') setShowAddModal(true);
  }, []);

  const loadPatients = async () => {
    try {
      const token = localStorage.getItem('token');
      const res = await fetch(`${config.API_URL}/api/users/doctors/patients`, {
        headers: { 'Authorization': `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        const list = Array.isArray(data) ? data : [];
        setLocalPatients(list);
        setCachedPatients?.(list); // update layout cache too
      }
    } catch (err) {
      console.error('Failed to load patients:', err);
    }
  };

  const handleSavePatient = async () => {
    setSaving(true);
    try {
      const token = localStorage.getItem('token');
      const medicalBody = {
        date_of_birth: form.date_of_birth || null,
        gender: form.gender,
        chronic_conditions: conditions,
        allergies: allergies,
        current_medications: medications,
        notes: form.notes,
      };

      if (selectedPatient && selectedPatient.patient_id) {
        // Update existing patient
        const res = await fetch(`${config.API_URL}/api/users/profile/patient/${selectedPatient.patient_id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify(medicalBody),
        });
        if (!res.ok) {
          const data = await res.json().catch(() => null);
          throw new Error(data?.detail || 'Failed to update patient');
        }
      } else {
        // Create new patient via doctor endpoint
        if (!form.name.trim() || !form.email.trim()) {
          throw new Error('Patient name and email are required');
        }
        const res = await fetch(`${config.API_URL}/api/users/doctors/patients`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({ name: form.name.trim(), email: form.email.trim(), ...medicalBody }),
        });
        if (!res.ok) {
          const data = await res.json().catch(() => null);
          throw new Error(data?.detail || 'Failed to create patient');
        }
      }

      await loadPatients();
      closeModal();
    } catch (err) {
      alert(err.message);
    } finally {
      setSaving(false);
    }
  };

  const closeModal = () => {
    setShowAddModal(false);
    setModalStep(1);
    setForm({ name: '', email: '', date_of_birth: '', gender: 'male', notes: '' });
    setConditions([]);
    setAllergies([]);
    setMedications([]);
    setConditionInput('');
    setAllergyInput('');
    setMedicationInput('');
  };

  const openEditModal = (patient) => {
    setSelectedPatient(patient);
    setForm({
      name: patient.name || '',
      email: patient.email || '',
      date_of_birth: patient.date_of_birth || '',
      gender: patient.gender || 'male',
      notes: patient.notes || '',
    });
    setConditions(patient.chronic_conditions || []);
    setAllergies(patient.allergies || []);
    setMedications(patient.current_medications || []);
    setShowAddModal(true);
  };

  const addToList = (setter, list, inputValue, clearInput) => {
    if (inputValue.trim() && !list.includes(inputValue.trim())) {
      setter([...list, inputValue.trim()]);
      clearInput('');
    }
  };

  const removeFromList = (setter, list, index) => {
    setter(list.filter((_, i) => i !== index));
  };

  const filteredPatients = patients.filter(p => {
    const q = searchQuery.toLowerCase();
    return (
      p.name?.toLowerCase().includes(q) ||
      p.chronic_conditions?.some(c => c.toLowerCase().includes(q)) ||
      p.current_medications?.some(m => m.toLowerCase().includes(q))
    );
  });

  if (loading) {
    return <div className="empty-state"><p>Loading patients...</p></div>;
  }

  return (
    <div className="doctor-patients-page">
      {/* Header */}
      <div className="dashboard-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>Patients</h1>
          <p>{patients.length} patient{patients.length !== 1 ? 's' : ''} in your care</p>
        </div>
        <button className="quick-action-btn" onClick={() => { setSelectedPatient(null); setShowAddModal(true); }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          Add Patient
        </button>
      </div>

      {/* Search */}
      <div style={{ marginBottom: '20px' }}>
        <input
          type="text"
          placeholder="Search by name, condition, or medication..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="doctor-search-input"
        />
      </div>

      {/* Patient Grid */}
      {filteredPatients.length === 0 ? (
        <div className="empty-state">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M17 21v-2a4 4 0 00-4-4H5a4 4 0 00-4 4v2"/><circle cx="9" cy="7" r="4"/>
            <line x1="19" y1="8" x2="19" y2="14"/><line x1="16" y1="11" x2="22" y2="11"/>
          </svg>
          <h3>{searchQuery ? 'No matching patients' : 'No patients yet'}</h3>
          <p>{searchQuery ? 'Try a different search term' : 'Add your first patient to get started.'}</p>
        </div>
      ) : (
        <div className="patient-list-compact">
          {filteredPatients.map(patient => (
            <div
              key={patient.patient_id}
              className="patient-row"
              onClick={() => navigate(`/doctor/patients/${patient.patient_id}`)}
            >
              <div className="patient-row-avatar">
                {patient.name?.charAt(0).toUpperCase() || '?'}
              </div>
              <div className="patient-row-info">
                <div className="patient-row-name">{patient.name}</div>
                <div className="patient-row-meta">
                  {patient.gender || 'Unknown'} • {patient.date_of_birth || 'DOB unknown'}
                </div>
              </div>
              <div className="patient-row-badges">
                {patient.chronic_conditions?.slice(0, 2).map((c, i) => (
                  <span key={i} className="badge badge-condition">{c}</span>
                ))}
                {patient.current_medications?.length > 0 && (
                  <span className="badge badge-med">{patient.current_medications.length} meds</span>
                )}
                {patient.allergies?.length > 0 && (
                  <span className="badge badge-allergy">{patient.allergies.length} allergies</span>
                )}
              </div>
              <button
                className="patient-row-edit"
                onClick={(e) => { e.stopPropagation(); openEditModal(patient); }}
                title="Edit patient"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7"/>
                  <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z"/>
                </svg>
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Add/Edit Modal */}
      {showAddModal && (
        <div className="modal-overlay" onClick={closeModal}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div className="modal-header">
              <h2>{selectedPatient ? 'Edit Patient' : 'Add Patient'}</h2>
              <button className="modal-close" onClick={closeModal}>×</button>
            </div>

            {/* Step indicator */}
            <div className="modal-steps">
              {['Basic Info', 'Conditions & Allergies', 'Medications'].map((step, i) => (
                <div key={i} className={`modal-step ${modalStep === i + 1 ? 'active' : ''} ${modalStep > i + 1 ? 'done' : ''}`}>
                  <span className="step-num">{i + 1}</span>
                  <span className="step-label">{step}</span>
                </div>
              ))}
            </div>

            <div className="modal-body">
              {modalStep === 1 && (
                <div className="form-grid">
                  <div className="form-group full-width">
                    <label>Full Name {!selectedPatient && <span style={{ color: '#f87171' }}>*</span>}</label>
                    <input
                      type="text"
                      value={form.name}
                      onChange={e => setForm({ ...form, name: e.target.value })}
                      placeholder="Patient full name"
                      readOnly={!!selectedPatient}
                      style={selectedPatient ? { opacity: 0.6, cursor: 'not-allowed' } : {}}
                    />
                  </div>
                  <div className="form-group full-width">
                    <label>Email {!selectedPatient && <span style={{ color: '#f87171' }}>*</span>}</label>
                    <input
                      type="email"
                      value={form.email}
                      onChange={e => setForm({ ...form, email: e.target.value })}
                      placeholder="patient@email.com"
                      readOnly={!!selectedPatient}
                      style={selectedPatient ? { opacity: 0.6, cursor: 'not-allowed' } : {}}
                    />
                  </div>
                  <div className="form-group">
                    <label>Date of Birth</label>
                    <input type="date" value={form.date_of_birth} onChange={e => setForm({ ...form, date_of_birth: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>Gender</label>
                    <select value={form.gender} onChange={e => setForm({ ...form, gender: e.target.value })}>
                      <option value="male">Male</option>
                      <option value="female">Female</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                  <div className="form-group full-width">
                    <label>Notes</label>
                    <textarea value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} placeholder="Additional notes about the patient..." rows={3} />
                  </div>
                </div>
              )}

              {modalStep === 2 && (
                <div>
                  <div className="form-group">
                    <label>Chronic Conditions</label>
                    <div className="tag-input-wrapper">
                      <input
                        type="text"
                        value={conditionInput}
                        onChange={e => setConditionInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addToList(setConditions, conditions, conditionInput, setConditionInput))}
                        placeholder="Type condition and press Enter"
                      />
                      <button onClick={() => addToList(setConditions, conditions, conditionInput, setConditionInput)}>Add</button>
                    </div>
                    <div className="tag-list">
                      {conditions.map((c, i) => (
                        <span key={i} className="tag tag-condition">
                          {c} <button onClick={() => removeFromList(setConditions, conditions, i)}>×</button>
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className="form-group" style={{ marginTop: '16px' }}>
                    <label>Allergies</label>
                    <div className="tag-input-wrapper">
                      <input
                        type="text"
                        value={allergyInput}
                        onChange={e => setAllergyInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addToList(setAllergies, allergies, allergyInput, setAllergyInput))}
                        placeholder="Type allergy and press Enter"
                      />
                      <button onClick={() => addToList(setAllergies, allergies, allergyInput, setAllergyInput)}>Add</button>
                    </div>
                    <div className="tag-list">
                      {allergies.map((a, i) => (
                        <span key={i} className="tag tag-allergy">
                          {a} <button onClick={() => removeFromList(setAllergies, allergies, i)}>×</button>
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {modalStep === 3 && (
                <div>
                  <div className="form-group">
                    <label>Current Medications</label>
                    <div className="tag-input-wrapper">
                      <input
                        type="text"
                        value={medicationInput}
                        onChange={e => setMedicationInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addToList(setMedications, medications, medicationInput, setMedicationInput))}
                        placeholder="e.g. Metformin 500mg twice daily"
                      />
                      <button onClick={() => addToList(setMedications, medications, medicationInput, setMedicationInput)}>Add</button>
                    </div>
                    <div className="tag-list">
                      {medications.map((m, i) => (
                        <span key={i} className="tag tag-med">
                          {m} <button onClick={() => removeFromList(setMedications, medications, i)}>×</button>
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="modal-footer">
              {modalStep > 1 && (
                <button className="btn-secondary" onClick={() => setModalStep(s => s - 1)}>Back</button>
              )}
              <div style={{ flex: 1 }} />
              {modalStep < 3 ? (
                <button className="btn-primary" onClick={() => setModalStep(s => s + 1)}>Next</button>
              ) : (
                <button className="btn-primary" onClick={handleSavePatient} disabled={saving}>
                  {saving ? 'Saving...' : selectedPatient ? 'Update Patient' : 'Add Patient'}
                </button>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default DoctorPatients;
