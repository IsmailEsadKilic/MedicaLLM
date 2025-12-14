import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import '../App.css';

const mockPatients = [
  {
    id: 1,
    name: 'Sarah',
    surname: 'Johnson',
    identityNumber: '12345678901',
    age: 45,
    bloodType: 'A+',
    gender: 'Female',
    phone: '+1 (555) 123-4567',
    email: 'sarah.j@email.com',
    address: '123 Oak Street, Boston, MA 02108',
    lastVisit: '2024-01-15',
    nextAppointment: '2024-02-20',
    chronicConditions: ['Type 2 Diabetes', 'Hypertension'],
    allergies: ['Penicillin', 'Peanuts'],
    currentMedications: [
      { name: 'Metformin', dosage: '500mg', frequency: 'Twice daily' },
      { name: 'Lisinopril', dosage: '10mg', frequency: 'Once daily' }
    ],
    recentVisits: [
      { date: '2024-01-15', reason: 'Routine checkup', doctor: 'Dr. Smith', notes: 'Blood pressure stable, A1C at 6.8%' },
      { date: '2023-12-10', reason: 'Follow-up', doctor: 'Dr. Smith', notes: 'Adjusted medication dosage' },
      { date: '2023-11-05', reason: 'Annual physical', doctor: 'Dr. Smith', notes: 'Overall health good' }
    ],
    labResults: [
      { date: '2024-01-15', test: 'HbA1c', result: '6.8%', range: '4.0-5.6%', status: 'High' },
      { date: '2024-01-15', test: 'Blood Pressure', result: '128/82', range: '<120/80', status: 'Elevated' },
      { date: '2024-01-15', test: 'Cholesterol', result: '195 mg/dL', range: '<200', status: 'Normal' },
      { date: '2024-01-15', test: 'Glucose', result: '142 mg/dL', range: '70-100', status: 'High' }
    ],
    vitals: { height: '165 cm', weight: '72 kg', bmi: '26.4' }
  },
  {
    id: 2,
    name: 'Michael',
    surname: 'Chen',
    identityNumber: '98765432109',
    age: 62,
    bloodType: 'O-',
    gender: 'Male',
    phone: '+1 (555) 234-5678',
    email: 'mchen@email.com',
    address: '456 Maple Ave, Cambridge, MA 02139',
    lastVisit: '2024-01-18',
    nextAppointment: '2024-03-15',
    chronicConditions: ['Coronary Artery Disease', 'High Cholesterol'],
    allergies: ['Sulfa drugs'],
    currentMedications: [
      { name: 'Atorvastatin', dosage: '40mg', frequency: 'Once daily' },
      { name: 'Aspirin', dosage: '81mg', frequency: 'Once daily' },
      { name: 'Metoprolol', dosage: '50mg', frequency: 'Twice daily' }
    ],
    recentVisits: [
      { date: '2024-01-18', reason: 'Cardiology follow-up', doctor: 'Dr. Smith', notes: 'EKG normal, continue current regimen' },
      { date: '2023-12-20', reason: 'Chest pain evaluation', doctor: 'Dr. Smith', notes: 'Stress test scheduled' },
      { date: '2023-11-15', reason: 'Routine checkup', doctor: 'Dr. Smith', notes: 'Cholesterol improving' }
    ],
    labResults: [
      { date: '2024-01-18', test: 'LDL Cholesterol', result: '98 mg/dL', range: '<100', status: 'Normal' },
      { date: '2024-01-18', test: 'HDL Cholesterol', result: '52 mg/dL', range: '>40', status: 'Normal' },
      { date: '2024-01-18', test: 'Triglycerides', result: '145 mg/dL', range: '<150', status: 'Normal' },
      { date: '2024-01-18', test: 'Blood Pressure', result: '118/76', range: '<120/80', status: 'Normal' }
    ],
    vitals: { height: '178 cm', weight: '85 kg', bmi: '26.8' }
  },
  {
    id: 3,
    name: 'Emily',
    surname: 'Rodriguez',
    identityNumber: '55566677788',
    age: 28,
    bloodType: 'B+',
    gender: 'Female',
    phone: '+1 (555) 345-6789',
    email: 'emily.r@email.com',
    address: '789 Pine Road, Somerville, MA 02144',
    lastVisit: '2024-01-22',
    nextAppointment: '2024-04-22',
    chronicConditions: ['Asthma'],
    allergies: ['Latex', 'Shellfish'],
    currentMedications: [
      { name: 'Albuterol Inhaler', dosage: '90mcg', frequency: 'As needed' },
      { name: 'Fluticasone', dosage: '110mcg', frequency: 'Twice daily' }
    ],
    recentVisits: [
      { date: '2024-01-22', reason: 'Asthma management', doctor: 'Dr. Smith', notes: 'Symptoms well controlled' },
      { date: '2023-10-15', reason: 'Annual checkup', doctor: 'Dr. Smith', notes: 'Healthy, continue current treatment' },
      { date: '2023-07-08', reason: 'Asthma exacerbation', doctor: 'Dr. Smith', notes: 'Prescribed prednisone course' }
    ],
    labResults: [
      { date: '2024-01-22', test: 'Peak Flow', result: '420 L/min', range: '380-550', status: 'Normal' },
      { date: '2024-01-22', test: 'SpO2', result: '98%', range: '>95%', status: 'Normal' },
      { date: '2023-10-15', test: 'Complete Blood Count', result: 'Normal', range: 'Normal', status: 'Normal' }
    ],
    vitals: { height: '162 cm', weight: '58 kg', bmi: '22.1' }
  }
];

function Patients() {
  const [user, setUser] = useState(null);
  const [theme, setTheme] = useState('dark');
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [patients, setPatients] = useState(mockPatients);
  const [searchQuery, setSearchQuery] = useState('');
  const [showAddModal, setShowAddModal] = useState(false);
  const [modalStep, setModalStep] = useState(1);
  const [newPatient, setNewPatient] = useState({
    name: '', surname: '', identityNumber: '', age: '', bloodType: 'A+', gender: 'Male',
    phone: '', email: '', address: '',
    height: '', weight: '', bmi: '',
    chronicConditions: '', allergies: '',
    labFile: null, notes: ''
  });
  const [medications, setMedications] = useState([]);
  const [currentMed, setCurrentMed] = useState({ name: '', dosage: '', frequency: '' });
  const navigate = useNavigate();

  useEffect(() => {
    const savedUser = localStorage.getItem('user');
    if (!savedUser) {
      navigate('/login');
    } else {
      const userData = JSON.parse(savedUser);
      if (userData.accountType !== 'healthcare_professional') {
        navigate('/');
      }
      setUser(userData);
    }
  }, [navigate]);

  useEffect(() => {
    document.body.className = theme;
  }, [theme]);

  useEffect(() => {
    if (newPatient.height && newPatient.weight) {
      const heightNum = parseFloat(newPatient.height);
      const weightNum = parseFloat(newPatient.weight);
      if (heightNum > 0 && weightNum > 0) {
        const heightM = heightNum / 100;
        const bmi = (weightNum / (heightM * heightM)).toFixed(1);
        setNewPatient(prev => ({ ...prev, bmi }));
      }
    }
  }, [newPatient.height, newPatient.weight]);

  const capitalizeWords = (str) => {
    return str.split(',').map(item => {
      const trimmed = item.trim();
      return trimmed.charAt(0).toUpperCase() + trimmed.slice(1).toLowerCase();
    }).join(', ');
  };

  const handleAddPatient = () => {
    const patient = {
      id: patients.length + 1,
      name: newPatient.name,
      surname: newPatient.surname,
      identityNumber: newPatient.identityNumber,
      age: parseInt(newPatient.age),
      bloodType: newPatient.bloodType,
      gender: newPatient.gender,
      phone: newPatient.phone,
      email: newPatient.email,
      address: newPatient.address,
      lastVisit: '-',
      nextAppointment: '-',
      labFile: newPatient.labFile ? newPatient.labFile.name : null,
      chronicConditions: newPatient.chronicConditions ? newPatient.chronicConditions.split(',').map(c => c.trim()) : [],
      allergies: newPatient.allergies ? newPatient.allergies.split(',').map(a => a.trim()) : [],
      currentMedications: medications,
      recentVisits: newPatient.notes ? [{ date: new Date().toISOString().split('T')[0], reason: 'Initial visit', doctor: user.name, notes: newPatient.notes }] : [],
      labResults: [],
      vitals: { 
        height: newPatient.height || '-', 
        weight: newPatient.weight || '-', 
        bmi: newPatient.bmi || '-' 
      }
    };
    setPatients([...patients, patient]);
    setShowAddModal(false);
    setModalStep(1);
    setNewPatient({ name: '', surname: '', identityNumber: '', age: '', bloodType: 'A+', gender: 'Male', phone: '', email: '', address: '', height: '', weight: '', bmi: '', chronicConditions: '', allergies: '', labFile: null, notes: '' });
    setMedications([]);
    setCurrentMed({ name: '', dosage: '', frequency: '' });
    setSelectedPatient(patient);
  };

  if (!user) return null;

  return (
    <div className={`app ${theme}`}>
      <div className="main" style={{ width: '100%' }}>
        <div className="header">
          <div className="header-left">
            <button className="menu-btn" onClick={() => navigate('/')}>←</button>
            <h2>My Patients</h2>
            <button 
              className="add-patient-btn"
              onClick={() => setShowAddModal(true)}
            >
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="12" y1="5" x2="12" y2="19"/>
                <line x1="5" y1="12" x2="19" y2="12"/>
              </svg>
              Add Patient
            </button>
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
                placeholder="Search patients..."
                className="search-input"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
            </div>
            <div style={{ overflowY: 'auto', flex: 1 }}>
              {patients.filter(patient => {
                const query = searchQuery.toLowerCase();
                return patient.name.toLowerCase().includes(query) ||
                       patient.surname.toLowerCase().includes(query) ||
                       patient.identityNumber.includes(query);
              }).map(patient => (
                <div 
                  key={patient.id}
                  className={`patient-item ${selectedPatient?.id === patient.id ? 'active' : ''}`}
                  onClick={() => setSelectedPatient(patient)}
                >
                  <div className="patient-avatar">{patient.name.charAt(0)}{patient.surname.charAt(0)}</div>
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: '600', fontSize: '14px' }}>{patient.name} {patient.surname}</div>
                    <div style={{ fontSize: '12px', opacity: 0.7, marginTop: '2px' }}>{patient.age} years • {patient.bloodType}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="patient-details">
            {selectedPatient ? (
              <div style={{ padding: '24px', overflowY: 'auto', height: '100%' }}>
                <div className="detail-section">
                  <div style={{ display: 'flex', alignItems: 'center', gap: '16px', marginBottom: '24px' }}>
                    <div className="patient-avatar-large">{selectedPatient.name.charAt(0)}{selectedPatient.surname.charAt(0)}</div>
                    <div>
                      <h1 style={{ fontSize: '28px', marginBottom: '4px' }}>{selectedPatient.name} {selectedPatient.surname}</h1>
                      <div style={{ opacity: 0.7 }}>{selectedPatient.age} years old • {selectedPatient.gender}</div>
                    </div>
                  </div>

                  <div className="info-grid">
                    <div className="info-card">
                      <div className="info-label">Identity Number</div>
                      <div className="info-value">{selectedPatient.identityNumber}</div>
                    </div>
                    <div className="info-card">
                      <div className="info-label">Blood Type</div>
                      <div className="info-value">{selectedPatient.bloodType}</div>
                    </div>
                    <div className="info-card">
                      <div className="info-label">BMI</div>
                      <div className="info-value">{selectedPatient.vitals.bmi}</div>
                    </div>
                  </div>
                </div>

                <div className="detail-section">
                  <h3 className="section-title">Contact Information</h3>
                  <div className="info-row"><strong>Phone:</strong> {selectedPatient.phone}</div>
                  <div className="info-row"><strong>Email:</strong> {selectedPatient.email}</div>
                  <div className="info-row"><strong>Address:</strong> {selectedPatient.address}</div>
                </div>

                <div className="detail-section">
                  <h3 className="section-title">Vitals</h3>
                  <div className="info-row"><strong>Height:</strong> {selectedPatient.vitals.height}</div>
                  <div className="info-row"><strong>Weight:</strong> {selectedPatient.vitals.weight}</div>
                  <div className="info-row"><strong>BMI:</strong> {selectedPatient.vitals.bmi}</div>
                </div>

                <div className="detail-section">
                  <h3 className="section-title">Chronic Conditions</h3>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {selectedPatient.chronicConditions.map((condition, i) => (
                      <span key={i} className="badge badge-warning">{condition}</span>
                    ))}
                  </div>
                </div>

                <div className="detail-section">
                  <h3 className="section-title">Allergies</h3>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                    {selectedPatient.allergies.map((allergy, i) => (
                      <span key={i} className="badge badge-danger">{allergy}</span>
                    ))}
                  </div>
                </div>

                <div className="detail-section">
                  <h3 className="section-title">Current Medications</h3>
                  {selectedPatient.currentMedications.map((med, i) => (
                    <div key={i} className="medication-item">
                      <div style={{ fontWeight: '600' }}>{med.name}</div>
                      <div style={{ fontSize: '14px', opacity: 0.7 }}>{med.dosage} - {med.frequency}</div>
                    </div>
                  ))}
                </div>

                <div className="detail-section">
                  <h3 className="section-title">Recent Lab Results</h3>
                  <div className="table-container">
                    <table className="results-table">
                      <thead>
                        <tr>
                          <th>Date</th>
                          <th>Test</th>
                          <th>Result</th>
                          <th>Reference Range</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedPatient.labResults.map((result, i) => (
                          <tr key={i}>
                            <td>{new Date(result.date).toLocaleDateString()}</td>
                            <td>{result.test}</td>
                            <td>{result.result}</td>
                            <td>{result.range}</td>
                            <td>
                              <span className={`badge badge-${result.status === 'Normal' ? 'success' : result.status === 'High' ? 'danger' : 'warning'}`}>
                                {result.status}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>

                <div className="detail-section">
                  <h3 className="section-title">Recent Visits</h3>
                  {selectedPatient.recentVisits.map((visit, i) => (
                    <div key={i} className="visit-item">
                      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
                        <div style={{ fontWeight: '600' }}>{visit.reason}</div>
                        <div style={{ opacity: 0.7, fontSize: '14px' }}>{new Date(visit.date).toLocaleDateString()}</div>
                      </div>
                      <div style={{ fontSize: '14px', opacity: 0.7, marginBottom: '4px' }}>{visit.doctor}</div>
                      <div style={{ fontSize: '14px' }}>{visit.notes}</div>
                    </div>
                  ))}
                </div>
              </div>
            ) : (
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%', opacity: 0.5 }}>
                <div style={{ textAlign: 'center' }}>
                  <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: '0 auto 16px' }}>
                    <path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/>
                    <circle cx="9" cy="7" r="4"/>
                    <path d="M23 21v-2a4 4 0 0 0-3-3.87"/>
                    <path d="M16 3.13a4 4 0 0 1 0 7.75"/>
                  </svg>
                  <div style={{ fontSize: '18px' }}>Select a patient to view details</div>
                </div>
              </div>
            )}
          </div>
        </div>

        {showAddModal && (
          <div className="modal-overlay" onClick={() => { setShowAddModal(false); setModalStep(1); }}>
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
                <div>
                  <h2 style={{ margin: 0 }}>Add New Patient</h2>
                  <div style={{ fontSize: '14px', opacity: 0.7, marginTop: '4px' }}>Step {modalStep} of 3</div>
                </div>
                <button className="close-btn" onClick={() => { setShowAddModal(false); setModalStep(1); }}>×</button>
              </div>

              {modalStep === 1 && (
                <div className="form-grid">
                  <div className="form-group">
                    <label>First Name *</label>
                    <input value={newPatient.name} onChange={(e) => setNewPatient({...newPatient, name: e.target.value})} />
                  </div>
                  <div className="form-group">
                    <label>Last Name *</label>
                    <input value={newPatient.surname} onChange={(e) => setNewPatient({...newPatient, surname: e.target.value})} />
                  </div>
                  <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                    <label>Identity Number *</label>
                    <input value={newPatient.identityNumber} onChange={(e) => setNewPatient({...newPatient, identityNumber: e.target.value})} placeholder="11 digits" maxLength="11" />
                  </div>
                  <div className="form-group">
                    <label>Age *</label>
                    <input type="number" value={newPatient.age} onChange={(e) => setNewPatient({...newPatient, age: e.target.value})} />
                  </div>
                  <div className="form-group">
                    <label>Gender *</label>
                    <select value={newPatient.gender} onChange={(e) => setNewPatient({...newPatient, gender: e.target.value})}>
                      <option>Male</option>
                      <option>Female</option>
                      <option>Other</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Blood Type *</label>
                    <select value={newPatient.bloodType} onChange={(e) => setNewPatient({...newPatient, bloodType: e.target.value})}>
                      <option>A+</option>
                      <option>A-</option>
                      <option>B+</option>
                      <option>B-</option>
                      <option>AB+</option>
                      <option>AB-</option>
                      <option>O+</option>
                      <option>O-</option>
                    </select>
                  </div>
                  <div className="form-group">
                    <label>Phone</label>
                    <input value={newPatient.phone} onChange={(e) => setNewPatient({...newPatient, phone: e.target.value})} />
                  </div>
                  <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                    <label>Email</label>
                    <input type="email" value={newPatient.email} onChange={(e) => setNewPatient({...newPatient, email: e.target.value})} />
                  </div>
                  <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                    <label>Address</label>
                    <input value={newPatient.address} onChange={(e) => setNewPatient({...newPatient, address: e.target.value})} />
                  </div>
                </div>
              )}

              {modalStep === 2 && (
                <div className="form-grid">
                  <div className="form-group">
                    <label>Height (cm)</label>
                    <input 
                      type="number" 
                      min="50" 
                      max="250" 
                      value={newPatient.height} 
                      onChange={(e) => setNewPatient({...newPatient, height: e.target.value})} 
                      placeholder="50-250" 
                    />
                  </div>
                  <div className="form-group">
                    <label>Weight (kg)</label>
                    <input 
                      type="number" 
                      min="0" 
                      max="400" 
                      value={newPatient.weight} 
                      onChange={(e) => setNewPatient({...newPatient, weight: e.target.value})} 
                      placeholder="0-400" 
                    />
                  </div>
                  <div className="form-group">
                    <label>BMI (Auto-calculated)</label>
                    <input value={newPatient.bmi} readOnly placeholder="Auto-calculated" style={{ opacity: 0.7 }} />
                  </div>
                  <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                    <label>Chronic Conditions</label>
                    <input 
                      value={newPatient.chronicConditions} 
                      onChange={(e) => setNewPatient({...newPatient, chronicConditions: e.target.value})} 
                      onBlur={(e) => setNewPatient({...newPatient, chronicConditions: capitalizeWords(e.target.value)})}
                      placeholder="Separate with commas (e.g., Diabetes, Hypertension)" 
                    />
                  </div>
                  <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                    <label>Allergies</label>
                    <input 
                      value={newPatient.allergies} 
                      onChange={(e) => setNewPatient({...newPatient, allergies: e.target.value})} 
                      onBlur={(e) => setNewPatient({...newPatient, allergies: capitalizeWords(e.target.value)})}
                      placeholder="Separate with commas (e.g., Penicillin, Peanuts)" 
                    />
                  </div>
                  <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                    <label>Current Medications</label>
                    <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
                      <input 
                        value={currentMed.name} 
                        onChange={(e) => setCurrentMed({...currentMed, name: e.target.value})} 
                        placeholder="Medication name"
                        style={{ flex: 2 }}
                      />
                      <input 
                        value={currentMed.dosage} 
                        onChange={(e) => setCurrentMed({...currentMed, dosage: e.target.value})} 
                        placeholder="Dosage (e.g., 500mg)"
                        style={{ flex: 1 }}
                      />
                      <input 
                        value={currentMed.frequency} 
                        onChange={(e) => setCurrentMed({...currentMed, frequency: e.target.value})} 
                        placeholder="Frequency"
                        style={{ flex: 1 }}
                      />
                      <button 
                        type="button"
                        onClick={() => {
                          if (currentMed.name) {
                            setMedications([...medications, currentMed]);
                            setCurrentMed({ name: '', dosage: '', frequency: '' });
                          }
                        }}
                        style={{
                          padding: '10px 16px',
                          background: '#8b5cf6',
                          color: 'white',
                          border: 'none',
                          borderRadius: '8px',
                          cursor: 'pointer',
                          fontSize: '14px'
                        }}
                      >
                        Add
                      </button>
                    </div>
                    {medications.length > 0 && (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {medications.map((med, i) => (
                          <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 12px', background: theme === 'dark' ? 'rgba(30, 41, 59, 0.4)' : '#f0f0f0', borderRadius: '6px' }}>
                            <span style={{ fontSize: '14px' }}>
                              <strong>{med.name}</strong> - {med.dosage} - {med.frequency}
                            </span>
                            <button 
                              type="button"
                              onClick={() => setMedications(medications.filter((_, idx) => idx !== i))}
                              style={{ background: 'none', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '18px', padding: '0 4px' }}
                            >
                              ×
                            </button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )}

              {modalStep === 3 && (
                <div className="form-grid">
                  <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                    <label>Recent Lab Results (PDF)</label>
                    <input 
                      type="file" 
                      accept=".pdf"
                      onChange={(e) => setNewPatient({...newPatient, labFile: e.target.files[0]})} 
                      style={{ padding: '8px' }}
                    />
                    {newPatient.labFile && (
                      <div style={{ marginTop: '8px', fontSize: '13px', opacity: 0.8 }}>
                        📄 {newPatient.labFile.name}
                      </div>
                    )}
                  </div>
                  <div className="form-group" style={{ gridColumn: '1 / -1' }}>
                    <label>Additional Notes</label>
                    <textarea 
                      value={newPatient.notes} 
                      onChange={(e) => setNewPatient({...newPatient, notes: e.target.value})} 
                      placeholder="Any additional notes about the patient..."
                      rows="6"
                      style={{ resize: 'vertical' }}
                    />
                  </div>
                </div>
              )}

              <div style={{ display: 'flex', gap: '12px', justifyContent: 'space-between', marginTop: '24px' }}>
                <div>
                  {modalStep > 1 && (
                    <button className="cancel-btn" onClick={() => setModalStep(modalStep - 1)}>← Back</button>
                  )}
                </div>
                <div style={{ display: 'flex', gap: '12px' }}>
                  <button className="cancel-btn" onClick={() => { setShowAddModal(false); setModalStep(1); }}>Cancel</button>
                  {modalStep < 3 ? (
                    <button 
                      className="submit-btn" 
                      onClick={() => setModalStep(modalStep + 1)}
                      disabled={modalStep === 1 && (!newPatient.name || !newPatient.surname || !newPatient.identityNumber || !newPatient.age)}
                    >
                      Next →
                    </button>
                  ) : (
                    <button 
                      className="submit-btn" 
                      onClick={handleAddPatient}
                    >
                      Add Patient
                    </button>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default Patients;
