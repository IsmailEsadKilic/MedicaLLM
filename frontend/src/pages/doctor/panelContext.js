import { createContext, useContext } from 'react';

/**
 * DoctorPanelContext — shared access for the doctor panel pages
 * (Dashboard, Patients, PatientDetail, Research, DrugMatrix).
 *
 * Supplies whatever the pages need without binding them to a specific
 * router layout, so the same components can render either inside the
 * legacy `/doctor/*` routes (provided by DoctorLayout) or embedded
 * inside `/chat` (provided by Chat).
 *
 * Shape:
 *   {
 *     user: { user_id, name, email, isDoctor },
 *     patients: PatientSummary[] | null,
 *     setPatients: (next) => void,
 *     viewParams: { patientId?: string, addPatient?: boolean },
 *     navigateTo: (view, params?) => void,
 *   }
 *
 * `view` accepts: 'dashboard' | 'patients' | 'patient-detail' |
 *                 'drug-matrix' | 'research' | 'chat'
 */
export const DoctorPanelContext = createContext(null);

export function useDoctorPanel() {
  const ctx = useContext(DoctorPanelContext);
  if (!ctx) {
    throw new Error('useDoctorPanel must be used inside <DoctorPanelContext.Provider>');
  }
  return ctx;
}
