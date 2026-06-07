import { useState, useEffect } from 'react';
import config from '../../api/config';
import { useDoctorPanel } from './panelContext';
import LoadingScreen from '../../components/LoadingScreen';
import { useT } from '../../i18n/lang';
import { DOCTOR_STRINGS } from '../../i18n/strings/doctor';

function DoctorPatients() {
  const t = useT(DOCTOR_STRINGS);
  const { patients: cachedPatients, setPatients: setCachedPatients, viewParams, navigateTo } = useDoctorPanel();
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
    if (viewParams?.addPatient) setShowAddModal(true);
  }, [viewParams?.addPatient]);

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
          throw new Error(data?.detail || t.patients.updateError);
        }
      } else {
        // Create new patient via doctor endpoint
        if (!form.name.trim() || !form.email.trim()) {
          throw new Error(t.patients.requiredFields);
        }
        const res = await fetch(`${config.API_URL}/api/users/doctors/patients`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
          body: JSON.stringify({ name: form.name.trim(), email: form.email.trim(), ...medicalBody }),
        });
        if (!res.ok) {
          const data = await res.json().catch(() => null);
          throw new Error(data?.detail || t.patients.createError);
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
    return <LoadingScreen variant="inline" message={t.loading.patients} />;
  }

  return (
    <div className="doctor-patients-page">
      {/* Header */}
      <div className="dashboard-header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div>
          <h1>{t.patients.title}</h1>
          <p>{t.patients.patientCount(patients.length)}</p>
        </div>
        <button className="quick-action-btn" onClick={() => { setSelectedPatient(null); setShowAddModal(true); }}>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/></svg>
          {t.patients.addNew}
        </button>
      </div>

      {/* Search */}
      <div style={{ marginBottom: '20px' }}>
        <input
          type="text"
          placeholder={t.patients.searchPatients}
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
          <h3>{searchQuery ? t.patients.noMatching : t.patients.noPatientsTitle}</h3>
          <p>{searchQuery ? t.patients.tryDifferent : t.patients.noPatientsDesc}</p>
        </div>
      ) : (
        <div className="patient-list-compact">
          {filteredPatients.map(patient => (
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
                  {patient.gender || t.patients.genderUnknown} • {patient.date_of_birth || t.patients.dobUnknown}
                </div>
              </div>
              <div className="patient-row-badges">
                {patient.chronic_conditions?.slice(0, 2).map((c, i) => (
                  <span key={i} className="badge badge-condition">{c}</span>
                ))}
                {patient.current_medications?.length > 0 && (
                  <span className="badge badge-med">{t.patients.medsCount(patient.current_medications.length)}</span>
                )}
                {patient.allergies?.length > 0 && (
                  <span className="badge badge-allergy">{t.patients.allergiesCount(patient.allergies.length)}</span>
                )}
              </div>
              <button
                className="patient-row-edit"
                onClick={(e) => { e.stopPropagation(); openEditModal(patient); }}
                title={t.patients.editPatient}
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
              <h2>{selectedPatient ? t.patients.editModalTitle : t.patients.addModalTitle}</h2>
              <button className="modal-close" onClick={closeModal}>×</button>
            </div>

            {/* Step indicator */}
            <div className="modal-steps">
              {[t.patients.step1, t.patients.step2, t.patients.step3].map((step, i) => (
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
                    <label>{t.patients.labelName} {!selectedPatient && <span style={{ color: '#f87171' }}>*</span>}</label>
                    <input
                      type="text"
                      value={form.name}
                      onChange={e => setForm({ ...form, name: e.target.value })}
                      placeholder={t.patients.placeholderName}
                      readOnly={!!selectedPatient}
                      style={selectedPatient ? { opacity: 0.6, cursor: 'not-allowed' } : {}}
                    />
                  </div>
                  <div className="form-group full-width">
                    <label>{t.patients.labelEmail} {!selectedPatient && <span style={{ color: '#f87171' }}>*</span>}</label>
                    <input
                      type="email"
                      value={form.email}
                      onChange={e => setForm({ ...form, email: e.target.value })}
                      placeholder={t.patients.placeholderEmail}
                      readOnly={!!selectedPatient}
                      style={selectedPatient ? { opacity: 0.6, cursor: 'not-allowed' } : {}}
                    />
                  </div>
                  <div className="form-group">
                    <label>{t.patients.labelDob}</label>
                    <input type="date" value={form.date_of_birth} onChange={e => setForm({ ...form, date_of_birth: e.target.value })} />
                  </div>
                  <div className="form-group">
                    <label>{t.patients.labelGender}</label>
                    <select value={form.gender} onChange={e => setForm({ ...form, gender: e.target.value })}>
                      <option value="male">{t.patients.genderMale}</option>
                      <option value="female">{t.patients.genderFemale}</option>
                      <option value="other">{t.patients.genderOther}</option>
                    </select>
                  </div>
                  <div className="form-group full-width">
                    <label>{t.patients.labelNotes}</label>
                    <textarea value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} placeholder={t.patients.placeholderNotes} rows={3} />
                  </div>
                </div>
              )}

              {modalStep === 2 && (
                <div>
                  <div className="form-group">
                    <label>{t.detail.labelConditions}</label>
                    <div className="tag-input-wrapper">
                      <input
                        type="text"
                        value={conditionInput}
                        onChange={e => setConditionInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addToList(setConditions, conditions, conditionInput, setConditionInput))}
                        placeholder={t.patients.typeConditionEnter}
                      />
                      <button onClick={() => addToList(setConditions, conditions, conditionInput, setConditionInput)}>{t.patients.addBtn}</button>
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
                    <label>{t.detail.labelAllergies}</label>
                    <div className="tag-input-wrapper">
                      <input
                        type="text"
                        value={allergyInput}
                        onChange={e => setAllergyInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addToList(setAllergies, allergies, allergyInput, setAllergyInput))}
                        placeholder={t.patients.typeAllergyEnter}
                      />
                      <button onClick={() => addToList(setAllergies, allergies, allergyInput, setAllergyInput)}>{t.patients.addBtn}</button>
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
                    <label>{t.detail.labelMedications}</label>
                    <div className="tag-input-wrapper">
                      <input
                        type="text"
                        value={medicationInput}
                        onChange={e => setMedicationInput(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && (e.preventDefault(), addToList(setMedications, medications, medicationInput, setMedicationInput))}
                        placeholder={t.patients.typeMedExample}
                      />
                      <button onClick={() => addToList(setMedications, medications, medicationInput, setMedicationInput)}>{t.patients.addBtn}</button>
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
                <button className="btn-secondary" onClick={() => setModalStep(s => s - 1)}>{t.patients.back}</button>
              )}
              <div style={{ flex: 1 }} />
              {modalStep < 3 ? (
                <button className="btn-primary" onClick={() => setModalStep(s => s + 1)}>{t.patients.next}</button>
              ) : (
                <button className="btn-primary" onClick={handleSavePatient} disabled={saving}>
                  {saving ? t.patients.saving : selectedPatient ? t.patients.update : t.patients.submit}
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
