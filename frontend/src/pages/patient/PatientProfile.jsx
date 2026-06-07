import { useState } from 'react';
import { useOutletContext } from 'react-router-dom';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import config from '../../api/config';
import LoadingScreen from '../../components/LoadingScreen';
import { useT } from '../../i18n/lang';
import { PATIENT_STRINGS } from '../../i18n/strings/patient';

function PatientProfile() {
  const t = useT(PATIENT_STRINGS);
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
    return <LoadingScreen variant="inline" message={t.loading.profile} className="patient-loading" />;
  }

  return (
    <div className="patient-profile-page">
      <div className="patient-dashboard-header">
        <h1>{t.profile.title}</h1>
        <p>{t.profile.subtitle}</p>
      </div>

      {/* Basic Info */}
      <div className="patient-section">
        <div className="patient-section-header">
          <h2>{t.profile.personalHeading}</h2>
          {!editingPersonal && (
            <button className="patient-btn secondary" onClick={startEditingPersonal}>{t.profile.edit}</button>
          )}
        </div>
        {editingPersonal ? (
          <div className="patient-card">
            <div className="patient-form-group">
              <label>{t.profile.labelFullName}</label>
              <input
                type="text"
                className="patient-form-input"
                value={personalForm.name}
                onChange={(e) => setPersonalForm({ ...personalForm, name: e.target.value })}
                placeholder={t.profile.placeholderFullName}
              />
            </div>
            <div className="patient-form-group">
              <label>{t.profile.labelGender}</label>
              <select
                className="patient-form-input"
                value={personalForm.gender}
                onChange={(e) => setPersonalForm({ ...personalForm, gender: e.target.value })}
              >
                <option value="">{t.profile.genderSelect}</option>
                <option value="male">{t.profile.genderMale}</option>
                <option value="female">{t.profile.genderFemale}</option>
                <option value="other">{t.profile.genderOther}</option>
              </select>
            </div>
            <div className="patient-form-group">
              <label>{t.profile.labelDob}</label>
              <input
                type="date"
                className="patient-form-input"
                value={personalForm.date_of_birth}
                onChange={(e) => setPersonalForm({ ...personalForm, date_of_birth: e.target.value })}
              />
            </div>
            <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
              <button className="patient-btn primary" onClick={savePersonal} disabled={saving}>
                {saving ? t.profile.saving : t.profile.saveChanges}
              </button>
              <button className="patient-btn secondary" onClick={cancelEditingPersonal}>{t.profile.cancel}</button>
            </div>
          </div>
        ) : (
          <div className="patient-card">
            <div className="profile-grid">
              <div className="profile-field">
                <span className="profile-field-label">{t.profile.labelFullName}</span>
                <span className="profile-field-value">{profile?.name || '—'}</span>
              </div>
              <div className="profile-field">
                <span className="profile-field-label">{t.profile.labelGender}</span>
                <span className="profile-field-value">{profile?.gender || '—'}</span>
              </div>
              <div className="profile-field">
                <span className="profile-field-label">{t.profile.labelDob}</span>
                <span className="profile-field-value">{profile?.date_of_birth || '—'}</span>
              </div>
              <div className="profile-field">
                <span className="profile-field-label">{t.profile.labelEmail}</span>
                <span className="profile-field-value">{profile?.email || '—'}</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Health Data (editable) */}
      <div className="patient-section">
        <div className="patient-section-header">
          <h2>{t.profile.healthHeading}</h2>
          {!editing && (
            <button onClick={startEditing}>{t.profile.edit}</button>
          )}
        </div>

        {editing ? (
          <div className="patient-card">
            <div className="patient-form-group">
              <label>{t.profile.labelChronicConditions}</label>
              <input
                type="text"
                className="patient-form-input"
                value={form.chronic_conditions}
                onChange={(e) => setForm({ ...form, chronic_conditions: e.target.value })}
                placeholder={t.profile.placeholderChronic}
              />
            </div>
            <div className="patient-form-group">
              <label>{t.profile.labelAllergies}</label>
              <input
                type="text"
                className="patient-form-input"
                value={form.allergies}
                onChange={(e) => setForm({ ...form, allergies: e.target.value })}
                placeholder={t.profile.placeholderAllergies}
              />
            </div>
            <div className="patient-form-group">
              <label>{t.profile.labelMedications}</label>
              <input
                type="text"
                className="patient-form-input"
                value={form.current_medications}
                onChange={(e) => setForm({ ...form, current_medications: e.target.value })}
                placeholder={t.profile.placeholderMedications}
              />
            </div>
            <div className="patient-form-group">
              <label>{t.profile.labelNotes}</label>
              <textarea
                className="patient-form-textarea"
                value={form.notes}
                onChange={(e) => setForm({ ...form, notes: e.target.value })}
                placeholder={t.profile.placeholderNotes}
              />
            </div>
            <div style={{ display: 'flex', gap: '12px', marginTop: '8px' }}>
              <button className="patient-btn primary" onClick={saveProfile} disabled={saving}>
                {saving ? t.profile.saving : t.profile.saveChanges}
              </button>
              <button className="patient-btn secondary" onClick={cancelEditing}>
                {t.profile.cancel}
              </button>
            </div>
          </div>
        ) : (
          <div className="patient-card">
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '6px' }}>{t.profile.sectionConditions}</div>
              {profile?.chronic_conditions?.length > 0 ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {profile.chronic_conditions.map((c, i) => (
                    <span key={i} className="patient-badge condition">{c}</span>
                  ))}
                </div>
              ) : (
                <span style={{ color: '#64748b', fontSize: '14px' }}>{t.profile.none}</span>
              )}
            </div>
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '6px' }}>{t.profile.sectionAllergies}</div>
              {profile?.allergies?.length > 0 ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {profile.allergies.map((a, i) => (
                    <span key={i} className="patient-badge allergy">{a}</span>
                  ))}
                </div>
              ) : (
                <span style={{ color: '#64748b', fontSize: '14px' }}>{t.profile.none}</span>
              )}
            </div>
            <div style={{ marginBottom: '16px' }}>
              <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '6px' }}>{t.profile.sectionMedications}</div>
              {profile?.current_medications?.length > 0 ? (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
                  {profile.current_medications.map((m, i) => (
                    <span key={i} className="patient-badge medication">{m}</span>
                  ))}
                </div>
              ) : (
                <span style={{ color: '#64748b', fontSize: '14px' }}>{t.profile.none}</span>
              )}
            </div>
            {profile?.notes && (
              <div>
                <div style={{ fontSize: '13px', color: '#64748b', marginBottom: '6px' }}>{t.profile.sectionNotes}</div>
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
