import json
import uuid
from datetime import datetime
from typing import List

from ..auth.service import get_user_by_id
from ..db.sql_client import get_session
from ..db.sql_models import PatientRecord, DoctorRecord, DoctorPatientAssociation, UserRecord
from ....legacy import printmeup as pm
from .models import PatientDetails, Patient, Doctor, DoctorDetails


def get_patient_details(patient_id: str, current_user_id: str) -> PatientDetails | None:
    """Get patient details if current user is authorized."""
    session = get_session()
    try:
        current_user = get_user_by_id(current_user_id)
        if not current_user:
            pm.err(m=f"User not found for ID {current_user_id}")
            return None
        
        # Get patient record
        patient_rec = session.query(PatientRecord).filter(
            PatientRecord.patient_id == patient_id
        ).first()
        
        if not patient_rec:
            return None
        
        # Authorization check
        if current_user.is_doctor:
            # Doctors can only access patients assigned to them
            association = session.query(DoctorPatientAssociation).join(
                DoctorRecord
            ).filter(
                DoctorRecord.user_pk == session.query(UserRecord).filter(
                    UserRecord.user_id == current_user_id
                ).first().id,
                DoctorPatientAssociation.patient_pk == patient_rec.id
            ).first()
            
            if not association:
                pm.err(m=f"Doctor {current_user_id} not authorized to access patient {patient_id}")
                return None
        
        elif current_user.is_patient:
            # Patients can only access their own record
            user_rec = session.query(UserRecord).filter(
                UserRecord.user_id == current_user_id
            ).first()
            
            if patient_rec.user_pk != user_rec.id:
                pm.err(m=f"Patient {current_user_id} not authorized to access patient {patient_id}")
                return None
        else:
            # Regular users cannot access patient records
            pm.err(m=f"Unauthorized access attempt by user {current_user_id}")
            return None
        
        # Return patient details
        return PatientDetails(
            date_of_birth=patient_rec.date_of_birth if patient_rec.date_of_birth else None,
            gender=patient_rec.gender if patient_rec.gender else None,
            chronic_conditions=json.loads(patient_rec.chronic_conditions) if patient_rec.chronic_conditions else [],
            allergies=json.loads(patient_rec.allergies) if patient_rec.allergies else [],
            current_medications=json.loads(patient_rec.current_medications) if patient_rec.current_medications else [],
            notes=patient_rec.notes if patient_rec.notes else None,
        )
    except Exception as e:
        pm.err(e=e, m=f"Error getting patient {patient_id}")
        return None
    finally:
        session.close()


def get_patients_for_doctor(doctor_id: str) -> List[Patient]:
    """Get all patients for a doctor."""
    session = get_session()
    try:
        doctor_rec = session.query(DoctorRecord).filter(
            DoctorRecord.doctor_id == doctor_id
        ).first()
        
        if not doctor_rec:
            return []
        
        patients = []
        for assoc in doctor_rec.patients:
            patient_rec = assoc.patient
            user_rec = patient_rec.user
            
            patients.append(Patient(
                patient_id=patient_rec.patient_id,
                user_id=user_rec.user_id,
                name=user_rec.name,
                email=user_rec.email,
                date_of_birth=patient_rec.date_of_birth if patient_rec.date_of_birth else None,
                gender=patient_rec.gender if patient_rec.gender else None,
                chronic_conditions=json.loads(patient_rec.chronic_conditions) if patient_rec.chronic_conditions else [],
                allergies=json.loads(patient_rec.allergies) if patient_rec.allergies else [],
                current_medications=json.loads(patient_rec.current_medications) if patient_rec.current_medications else [],
                notes=patient_rec.notes if patient_rec.notes else None,
                created_at=patient_rec.created_at,
                updated_at=patient_rec.updated_at,
                doctor_ids=[],  # Can be populated if needed
            ))
        
        return patients
    except Exception as e:
        pm.err(e=e, m="Error getting patients for doctor")
        return []
    finally:
        session.close()


def get_doctors_for_patient(patient_id: str) -> List[Doctor]:
    """Get all doctors for a patient."""
    session = get_session()
    try:
        patient_rec = session.query(PatientRecord).filter(
            PatientRecord.patient_id == patient_id
        ).first()
        
        if not patient_rec:
            return []
        
        doctors = []
        for assoc in patient_rec.doctors:
            doctor_rec = assoc.doctor
            user_rec = doctor_rec.user
            
            doctors.append(Doctor(
                doctor_id=doctor_rec.doctor_id,
                user_id=user_rec.user_id,
                name=user_rec.name,
                email=user_rec.email,
                specialty=doctor_rec.specialty if doctor_rec.specialty else None,
                created_at=doctor_rec.created_at,
                updated_at=doctor_rec.updated_at,
                patient_ids=[],  # Can be populated if needed
            ))
        
        return doctors
    except Exception as e:
        pm.err(e=e, m="Error getting doctors for patient")
        return []
    finally:
        session.close()


def create_patient_profile(user_id: str, patient_data: PatientDetails) -> Patient | None:
    """Create a patient profile for a user."""
    session = get_session()
    try:
        user_rec = session.query(UserRecord).filter(
            UserRecord.user_id == user_id
        ).first()
        
        if not user_rec:
            pm.err(m=f"User not found: {user_id}")
            return None
        
        # Check if patient profile already exists
        if user_rec.patient_profile:
            pm.err(m=f"Patient profile already exists for user {user_id}")
            return None
        
        now = datetime.now().isoformat()
        patient_id = str(uuid.uuid4())
        
        patient_rec = PatientRecord(
            patient_id=patient_id,
            user_pk=user_rec.id,
            date_of_birth=str(patient_data.date_of_birth) if patient_data.date_of_birth else "",
            gender=patient_data.gender if patient_data.gender else "",
            chronic_conditions=json.dumps(patient_data.chronic_conditions),
            allergies=json.dumps(patient_data.allergies),
            current_medications=json.dumps(patient_data.current_medications),
            notes=patient_data.notes if patient_data.notes else "",
            created_at=now,
            updated_at=now,
        )
        
        session.add(patient_rec)
        session.commit()
        
        pm.suc(f"Patient profile created: {patient_id}")
        
        return Patient(
            patient_id=patient_id,
            user_id=user_id,
            name=user_rec.name,
            email=user_rec.email,
            date_of_birth=patient_data.date_of_birth,
            gender=patient_data.gender,
            chronic_conditions=patient_data.chronic_conditions,
            allergies=patient_data.allergies,
            current_medications=patient_data.current_medications,
            notes=patient_data.notes,
            created_at=now,
            updated_at=now,
            doctor_ids=[],
        )
    except Exception as e:
        session.rollback()
        pm.err(e=e, m="Error creating patient profile")
        return None
    finally:
        session.close()


def create_doctor_profile(user_id: str, doctor_data: DoctorDetails) -> Doctor | None:
    """Create a doctor profile for a user."""
    session = get_session()
    try:
        user_rec = session.query(UserRecord).filter(
            UserRecord.user_id == user_id
        ).first()
        
        if not user_rec:
            pm.err(m=f"User not found: {user_id}")
            return None
        
        # Check if doctor profile already exists
        if user_rec.doctor_profile:
            pm.err(m=f"Doctor profile already exists for user {user_id}")
            return None
        
        now = datetime.now().isoformat()
        doctor_id = str(uuid.uuid4())
        
        doctor_rec = DoctorRecord(
            doctor_id=doctor_id,
            user_pk=user_rec.id,
            specialty=doctor_data.specialty if doctor_data.specialty else "",
            created_at=now,
            updated_at=now,
        )
        
        session.add(doctor_rec)
        session.commit()
        
        pm.suc(f"Doctor profile created: {doctor_id}")
        
        return Doctor(
            doctor_id=doctor_id,
            user_id=user_id,
            name=user_rec.name,
            email=user_rec.email,
            specialty=doctor_data.specialty,
            created_at=now,
            updated_at=now,
            patient_ids=[],
        )
    except Exception as e:
        session.rollback()
        pm.err(e=e, m="Error creating doctor profile")
        return None
    finally:
        session.close()


def assign_doctor_to_patient(doctor_id: str, patient_id: str) -> bool:
    """Assign a doctor to a patient."""
    session = get_session()
    try:
        doctor_rec = session.query(DoctorRecord).filter(
            DoctorRecord.doctor_id == doctor_id
        ).first()
        
        patient_rec = session.query(PatientRecord).filter(
            PatientRecord.patient_id == patient_id
        ).first()
        
        if not doctor_rec or not patient_rec:
            pm.err(m=f"Doctor or patient not found: {doctor_id}, {patient_id}")
            return False
        
        # Check if association already exists
        existing = session.query(DoctorPatientAssociation).filter(
            DoctorPatientAssociation.doctor_pk == doctor_rec.id,
            DoctorPatientAssociation.patient_pk == patient_rec.id,
        ).first()
        
        if existing:
            pm.war(f"Doctor {doctor_id} already assigned to patient {patient_id}")
            return True
        
        association = DoctorPatientAssociation(
            doctor_pk=doctor_rec.id,
            patient_pk=patient_rec.id,
            created_at=datetime.now().isoformat(),
        )
        
        session.add(association)
        session.commit()
        
        pm.suc(f"Doctor {doctor_id} assigned to patient {patient_id}")
        return True
    except Exception as e:
        session.rollback()
        pm.err(e=e, m="Error assigning doctor to patient")
        return False
    finally:
        session.close()


def remove_doctor_from_patient(doctor_id: str, patient_id: str) -> bool:
    """Remove a doctor from a patient."""
    session = get_session()
    try:
        doctor_rec = session.query(DoctorRecord).filter(
            DoctorRecord.doctor_id == doctor_id
        ).first()
        
        patient_rec = session.query(PatientRecord).filter(
            PatientRecord.patient_id == patient_id
        ).first()
        
        if not doctor_rec or not patient_rec:
            return False
        
        result = session.query(DoctorPatientAssociation).filter(
            DoctorPatientAssociation.doctor_pk == doctor_rec.id,
            DoctorPatientAssociation.patient_pk == patient_rec.id,
        ).delete()
        
        session.commit()
        
        if result > 0:
            pm.suc(f"Doctor {doctor_id} removed from patient {patient_id}")
            return True
        return False
    except Exception as e:
        session.rollback()
        pm.err(e=e, m="Error removing doctor from patient")
        return False
    finally:
        session.close()
