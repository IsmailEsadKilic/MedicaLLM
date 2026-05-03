import json
import uuid
from datetime import datetime
from typing import List, Optional
import logging

from ..auth.service import get_user_by_id
from ..db.sql_client import get_session
from ..db.sql_models import PatientRecord, DoctorRecord, DoctorPatientAssociation, UserRecord
from .models import PatientBase, Patient, Doctor, DoctorBase

logger = logging.getLogger(__name__)


def get_patient_details(patient_id: str, current_user_id: str) -> Optional[PatientBase]:
    """Get patient details if current user is authorized."""
    session = get_session()
    try:
        current_user = get_user_by_id(current_user_id)
        if not current_user:
            logger.error(f"User not found for ID {current_user_id}")
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
            user_rec = session.query(UserRecord).filter(
                UserRecord.user_id == current_user_id
            ).first()
            
            if not user_rec or not user_rec.doctor_profile:
                logger.error(f"Doctor profile not found for user {current_user_id}")
                return None
            
            association = session.query(DoctorPatientAssociation).filter(
                DoctorPatientAssociation.doctor_pk == user_rec.doctor_profile.id,
                DoctorPatientAssociation.patient_pk == patient_rec.id
            ).first()
            
            if not association:
                logger.error(f"Doctor {current_user_id} not authorized to access patient {patient_id}")
                return None
        
        elif current_user.is_patient:
            # Patients can only access their own record
            user_rec = session.query(UserRecord).filter(
                UserRecord.user_id == current_user_id
            ).first()
            
            if user_rec is None or patient_rec.user_pk != user_rec.id:  # type: ignore
                logger.error(f"Patient {current_user_id} not authorized to access patient {patient_id}")
                return None
        else:
            # Regular users cannot access patient records
            logger.error(f"Unauthorized access attempt by user {current_user_id}")
            return None
        
        # Get user name for PatientDetails
        user_rec = patient_rec.user
        
        # Return patient details
        return PatientBase(
            patient_id=patient_rec.patient_id, # type: ignore
            user_id=user_rec.user_id,
            name=user_rec.name,
            date_of_birth=patient_rec.date_of_birth if patient_rec.date_of_birth else None, # type: ignore
            gender=patient_rec.gender if patient_rec.gender else None, # type: ignore
            chronic_conditions=json.loads(patient_rec.chronic_conditions) if patient_rec.chronic_conditions else [], # type: ignore
            allergies=json.loads(patient_rec.allergies) if patient_rec.allergies else [], # type: ignore
            current_medications=json.loads(patient_rec.current_medications) if patient_rec.current_medications else [], # type: ignore
            notes=patient_rec.notes if patient_rec.notes else None, # type: ignore
        )
    except Exception as e:
        logger.error(f"Error getting patient {patient_id}: {e}", exc_info=True)
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
        logger.error(f"Error getting patients for doctor: {e}", exc_info=True)
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
        logger.error(f"Error getting doctors for patient: {e}", exc_info=True)
        return []
    finally:
        session.close()


def create_patient_profile(user_id: str, patient_data: PatientBase) -> Optional[Patient]:
    """Create a patient profile for a user."""
    session = get_session()
    try:
        user_rec = session.query(UserRecord).filter(
            UserRecord.user_id == user_id
        ).first()
        
        if not user_rec:
            logger.error(f"User not found: {user_id}")
            return None
        
        # Check if patient profile already exists
        if user_rec.patient_profile:
            logger.error(f"Patient profile already exists for user {user_id}")
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
        
        logger.info(f"Patient profile created: {patient_id}")
        
        return Patient(
            patient_id=patient_id,
            user_id=user_id,
            name=user_rec.name, # type: ignore
            email=user_rec.email, # type: ignore
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
        logger.error(f"Error creating patient profile: {e}", exc_info=True)
        return None
    finally:
        session.close()


def create_doctor_profile(user_id: str, doctor_data: DoctorBase) -> Optional[Doctor]:
    """Create a doctor profile for a user."""
    session = get_session()
    try:
        user_rec = session.query(UserRecord).filter(
            UserRecord.user_id == user_id
        ).first()
        
        if not user_rec:
            logger.error(f"User not found: {user_id}")
            return None
        
        # Check if doctor profile already exists
        if user_rec.doctor_profile:
            logger.error(f"Doctor profile already exists for user {user_id}")
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
        
        logger.info(f"Doctor profile created: {doctor_id}")
        
        return Doctor(
            doctor_id=doctor_id,
            user_id=user_id,
            name=user_rec.name, # type: ignore
            email=user_rec.email, # type: ignore
            specialty=doctor_data.specialty,
            created_at=now,
            updated_at=now,
            patient_ids=[],
        )
    except Exception as e:
        session.rollback()
        logger.error(f"Error creating doctor profile: {e}", exc_info=True)
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
            logger.error(f"Doctor or patient not found: {doctor_id}, {patient_id}")
            return False
        
        # Check if association already exists
        existing = session.query(DoctorPatientAssociation).filter(
            DoctorPatientAssociation.doctor_pk == doctor_rec.id,
            DoctorPatientAssociation.patient_pk == patient_rec.id,
        ).first()
        
        if existing:
            logger.warning(f"Doctor {doctor_id} already assigned to patient {patient_id}")
            return True
        
        association = DoctorPatientAssociation(
            doctor_pk=doctor_rec.id,
            patient_pk=patient_rec.id,
            created_at=datetime.now().isoformat(),
        )
        
        session.add(association)
        session.commit()
        
        logger.info(f"Doctor {doctor_id} assigned to patient {patient_id}")
        return True
    except Exception as e:
        session.rollback()
        logger.error(f"Error assigning doctor to patient: {e}", exc_info=True)
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
            logger.info(f"Doctor {doctor_id} removed from patient {patient_id}")
            return True
        return False
    except Exception as e:
        session.rollback()
        logger.error(f"Error removing doctor from patient: {e}", exc_info=True)
        return False
    finally:
        session.close()
