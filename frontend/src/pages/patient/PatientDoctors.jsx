import { useOutletContext } from 'react-router-dom';
import LoadingScreen from '../../components/LoadingScreen';
import { useT } from '../../i18n/lang';
import { PATIENT_STRINGS } from '../../i18n/strings/patient';

function PatientDoctors() {
  const t = useT(PATIENT_STRINGS);
  const { doctors } = useOutletContext();
  const loading = doctors === null;

  if (loading) {
    return <LoadingScreen variant="inline" message={t.loading.doctors} className="patient-loading" />;
  }

  return (
    <div className="patient-doctors-page">
      <div className="patient-dashboard-header">
        <h1>{t.doctors.title}</h1>
        <p>{t.doctors.subtitle}</p>
      </div>

      <div className="patient-section">
        <div className="patient-section-header">
          <h2>{t.doctors.sectionHeading(doctors.length)}</h2>
        </div>

        {doctors.length === 0 ? (
          <div className="patient-empty-state">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M3 21h18"/><rect x="5" y="2" width="14" height="20" rx="2"/>
              <path d="M9 8h1M9 12h1M14 8h1M14 12h1"/>
            </svg>
            <h3>{t.doctors.emptyTitle}</h3>
            <p>{t.doctors.emptyDesc}</p>
          </div>
        ) : (
          <div className="doctor-card-grid">
            {doctors.map((doctor, i) => (
              <div key={doctor.doctor_id || i} className="doctor-card-item">
                <div className="doctor-card-avatar">
                  {doctor.name?.charAt(0).toUpperCase() || 'D'}
                </div>
                <div className="doctor-card-info">
                  <div className="doctor-card-name">{doctor.name || t.doctors.labelDoctorFallback}</div>
                  {doctor.specialty && (
                    <div className="doctor-card-specialty">{doctor.specialty}</div>
                  )}
                  {doctor.email && (
                    <div className="doctor-card-email">{doctor.email}</div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default PatientDoctors;
