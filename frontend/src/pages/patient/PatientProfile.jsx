import { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import config from '../../api/config';
import LoadingScreen from '../../components/LoadingScreen';

function PatientProfile() {
  const { profile, setProfile } = useOutletContext();
  const [editing, setEditing] = useState(false);
  const [editingPersonal, setEditingPersonal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState(null);
  const [personalForm, setPersonalForm] = useState(null);

  const loading = profile === null;

  const startEditing = () => {
    setForm({
      chronic_conditions: (profile?.chronic_conditions || []).join(', '),
      allergies: (profile?.allergies || []).join(', '),
      current_medications: (profile?.current_medications || []).join(', '),
      notes: profile?.notes || '',
    });
    setEditing(true);
  };

  const cancelEditing = () => {
    setEditing(false);
    setForm(null);
  };

  const startEditingPersonal = () => {
    setPersonalForm({
      name: profile?.name || '',
      gender: profile?.gender || '',
      date_of_birth: profile?.date_of_birth || '',
    });
    setEditingPersonal(true);
  };

  const cancelEditingPersonal = () => {
    setEditingPersonal(false);
    setPersonalForm(null);
  };

  const savePersonal = async () => {
    setSaving(true);
    const token = localStorage.getItem('token');
    const savedUser = JSON.parse(localStorage.getItem('user') || '{}');
    const patientId = savedUser.patientId || profile?.patient_id;

    const payload = {};
    if (personalForm.name) payload.name = personalForm.name;
    if (personalForm.gender) payload.gender = personalForm.gender;
    if (personalForm.date_of_birth) payload.date_of_birth = personalForm.date_of_birth;

    try {
      const res = await fetch(`${config.API_URL}/api/users/profile/patient/${patientId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const updated = await res.json();
        setProfile(updated);
        // Also update name in localStorage so navbar reflects it
        const user = JSON.parse(localStorage.getItem('user') || '{}');
        if (personalForm.name) user.name = personalForm.name;
        localStorage.setItem('user', JSON.stringify(user));
        setEditingPersonal(false);
        setPersonalForm(null);
      }
    } catch (err) {
      console.error('Failed to save personal info:', err);
    } finally {
      setSaving(false);
    }
  };

  const saveProfile = async () => {
    setSaving(true);
    const token = localStorage.getItem('token');
    const savedUser = JSON.parse(localStorage.getItem('user') || '{}');
    const patientId = savedUser.patientId || profile?.patient_id;

    const payload = {
      chronic_conditions: form.chronic_conditions
        ? form.chronic_conditions.split(',').map(s => s.trim()).filter(Boolean)
        : [],
      allergies: form.allergies
        ? form.allergies.split(',').map(s => s.trim()).filter(Boolean)
        : [],
      current_medications: form.current_medications
        ? form.current_medications.split(',').map(s => s.trim()).filter(Boolean)
        : [],
      notes: form.notes || '',
    };

    try {
      const res = await fetch(`${config.API_URL}/api/users/profile/patient/${patientId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });
      if (res.ok) {
        const updated = await res.json();
        setProfile(updated);
        setEditing(false);
        setForm(null);
      }
    } catch (err) {
      console.error('Failed to save profile:', err);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return <LoadingScreen variant="inline" message="Loading profile" className="patient-loading" />;
  }

  return (
    <div className="patient-profile-page">
      <div className="patient-dashboard-header">
        <h1>My Health Profile</h1>
        <p>View and manage your personal health information.</p>
      </div>

      {/* Basic Info */}
      <div className="patient-section">
        <div className="patient-section-header">
          <h2>Personal Information</h2>
          {!editingPersonal && (
            <button className="patient-btn secondary" onClick={startEditingPersonal}>Edit</button>
          )}
        </div>
        {editingPersonal ? (
          <div className="patient-card">
            <div className="patient-form-group">
              <label>Full Name</label>
              <input
                type="text"
                className="patient-form-input"
                value={personalForm.name}
                onChange={(e) => setPersonalForm({ ...personalForm, name: e.target.value })}
                placeholder="Your full name"
              />
            </div>
            <div className="patient-form-group">
              <label>Gender</label>
              <select
                className="patient-form-input"
                value={personalForm.gender}
                onChange={(e) => setPersonalForm({ ...personalForm, gender: e.target.value })}
              >
                <option value="">Select gender</option>
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
            <div className="patient-form-group">
              <label>Date of Birth</label>
              <input
                type="date"
                className="patient-form-input"
                value={personalForm.date_of_birth}
                onChange={(e) => setPersonalForm({ ...personalForm, date_of_birth: e.target.value })}
              />
            </div>
            <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
              <button className="patient-btn primary" onClick={savePersonal} disabled={saving}>
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
              <button className="patient-btn secondary" onClick={cancelEditingPersonal}>Cancel</button>
            </div>
          </div>
        ) : (
          <div className="patient-card">
            <div className="profile-grid">
              <div className="profile-field">
                <span className="profile-field-label">Full Name</span>
                <span className="profile-field-value">{profile?.name || '—'}</span>
              </div>
              <div className="profile-field">
                <span className="profile-field-label">Gender</span>
                <span className="profile-field-value">{profile?.gender || '—'}</span>
              </div>
              <div className="profile-field">
                <span className="profile-field-label">Date of Birth</span>
                <span className="profile-field-value">{profile?.date_of_birth || '—'}</span>
              </div>
              <div className="profile-field">
                <span className="profile-field-label">Email</span>
                <span className="profile-field-value">{profile?.email || '—'}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Health Data (editable) */}
      <div className="patient-section">
        <div className="patient-section-header">
          <h2>Health Data</h2>
          {!editing && (
            <button onClick={startEditing}>Edit</button>
          )}
        </div>

        {editing ? (
          <div className="patient-card">
            <div className="patient-form-group">
              <label>Chronic Conditions (comma-separated)</label>
              <input
                type="text"
                className="patient-form-input"
                value={form.chronic_conditions}
                onChange={(e) => setForm({ ...form, chronic_conditions: e.target.value })}
                placeholder="e.g. Diabetes Type 2, Hypertension"
              />
            </div>
            <div className="patient-form-group">
              <label>Allergies (comma-separated)</label>
              <input
                type="text"
                className="patient-form-input"
                value={form.allergies}
                onChange={(e) => setForm({ ...form, allergies: e.target.value })}
                placeholder="e.g. Penicillin, Aspirin"
              />
            </div>
            <div className="patient-form-group">
              <label>Current Medications (comma-separated)</label>
              <input
                type="text"
                className="patient-form-input"
                value={form.current_medications}
                onChange={(e) => setForm({ ...form, current_medications: e.target.value })}
                placeholder="e.g. Metformin 1000mg, Lisinopril 10mg"
              />
            </div>
            <div className="patient-form-group">
              <label>Notes</label>
              <textarea
                className="patient-form-textarea"
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                placeholder="Any additional health notes..."
              />
            </div>
            <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
              <button className="patient-btn primary" onClick={saveProfile} disabled={saving}>
                {saving ? 'Saving...' : 'Save Changes'}
              </button>
              <button className="patient-btn secondary" onClick={cancelEditing}>
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <div className="patient-card">
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '6px' }}>Chronic Conditions</div>
              {profile?.chronic_conditions?.length > 0 ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {profile.chronic_conditions.map((c, i) => (
                    <span key={i} className="patient-badge condition">{c}</span>
                  ))}
                </div>
              ) : (
                <span style={{ color: '#64748b', fontSize: '14px' }}>None listed</span>
              )}
            </div>
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '6px' }}>Allergies</div>
              {profile?.allergies?.length > 0 ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {profile.allergies.map((a, i) => (
                    <span key={i} className="patient-badge allergy">{a}</span>
                  ))}
                </div>
              ) : (
                <span style={{ color: '#64748b', fontSize: '14px' }}>None listed</span>
              )}
            </div>
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '6px' }}>Current Medications</div>
              {profile?.current_medications?.length > 0 ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {profile.current_medications.map((m, i) => (
                    <span key={i} className="patient-badge medication">{m}</span>
                  ))}
                </div>
              ) : (
                <span style={{ color: '#64748b', fontSize: '14px' }}>None listed</span>
              )}
            </div>
            {profile?.notes && (
              <div>
                <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '6px' }}>Notes</div>
                <div className="patient-notes-markdown">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {profile.notes}
                  </ReactMarkdown>
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

export default PatientProfile;
