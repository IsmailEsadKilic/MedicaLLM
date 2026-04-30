import json
import uuid
from datetime import datetime
from typing import cast

from ..auth.models import CurrentUserDetails
from ..auth.service import get_user_by_id
from ..db.sql_client import get_session
from ..db.sql_models import PatientRecord
from ....legacy import printmeup as pm
from .models import PatientDetails


def _record_to_dict(rec: PatientRecord) -> dict:
    data = json.loads(str(rec.data)) if rec.data else {}  # type: ignore
    return {
        "id": rec.patient_id,  # type: ignore
        "doctor_id": rec.doctor_id,  # type: ignore
        **data,
        "created_at": rec.created_at,  # type: ignore
        "updated_at": rec.updated_at,  # type: ignore
    }


def get_patients(doctor_id: str) -> list[dict]:
    session = get_session()
    try:
        recs = session.query(PatientRecord).filter(
            PatientRecord.doctor_id == doctor_id
        ).all()
        return [_record_to_dict(r) for r in recs]
    except Exception as e:
        pm.err(e=e, m="Error getting patients")
        return []
    finally:
        session.close()


def get_patient_details(patient_id: str, current_user_id: str) -> PatientDetails | None:
    session = get_session()
    try:
        current_user = get_user_by_id(current_user_id)
        if not current_user:
            pm.err(m=f"User not found for ID {current_user_id}")
            return None
        # check if current user is authorized to access this patient
        if current_user.get("account_type") == "doctor":
            # doctors can only access patients they are assigned to
            rec = session.query(PatientRecord).filter(
                PatientRecord.patient_id == patient_id,
                PatientRecord.doctor_id == current_user.get("user_id"),
            ).first()
        elif current_user.get("account_type") == "patient":
            # patients can only access their own record
            rec = session.query(PatientRecord).filter(
                PatientRecord.patient_id == patient_id,
                PatientRecord.doctor_id == current_user.get("user_id"),
            ).first()
        else:
            pm.err(m=f"Unauthorized access attempt by user {current_user.get('user_id')} with account type {current_user.get('account_type')}")
            return None
        
        return cast(PatientDetails, _record_to_dict(rec)) if rec else None
    except Exception as e:
        pm.err(e=e, m=f"Error getting patient {patient_id}")
        return None
    finally:
        session.close()


def create_patient(doctor_id: str, patient_data: dict) -> dict:
    now = datetime.now().isoformat()
    patient_id = str(uuid.uuid4())
    session = get_session()
    try:
        session.add(PatientRecord(
            patient_id=patient_id,
            doctor_id=doctor_id,
            data=json.dumps(patient_data),
            created_at=now, updated_at=now,
        ))
        session.commit()
        pm.suc(f"Patient created: {patient_id}")
    except Exception as e:
        session.rollback()
        pm.err(e=e, m="Error creating patient")
        raise
    finally:
        session.close()
    return {"id": patient_id, "doctor_id": doctor_id,
            **patient_data, "created_at": now, "updated_at": now}


def update_patient(doctor_id: str, patient_id: str, patient_data: dict) -> dict:
    now = datetime.now().isoformat()
    session = get_session()
    try:
        rec = session.query(PatientRecord).filter(
            PatientRecord.doctor_id == doctor_id,
            PatientRecord.patient_id == patient_id,
        ).first()
        if not rec:
            raise ValueError(f"Patient {patient_id} not found")
        setattr(rec, "data", json.dumps(patient_data))
        setattr(rec, "updated_at", now)
        session.commit()
        pm.inf(f"Patient updated: {patient_id}")
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
    return {"id": patient_id, "doctor_id": doctor_id,
            **patient_data, "updated_at": now}


def delete_patient(doctor_id: str, patient_id: str) -> bool:
    session = get_session()
    try:
        result = session.query(PatientRecord).filter(
            PatientRecord.doctor_id == doctor_id,
            PatientRecord.patient_id == patient_id,
        ).delete()
        session.commit()
        if result == 0:
            return False
        pm.suc(f"Patient deleted: {patient_id}")
        return True
    except Exception as e:
        session.rollback()
        pm.err(e=e, m=f"Error deleting patient {patient_id}")
        return False
    finally:
        session.close()

def get_doctors(patient_id: str) -> list[dict]:
    session = get_session()
    try:
        recs = session.query(PatientRecord).filter(
            PatientRecord.patient_id == patient_id
        ).all()
        return [_record_to_dict(r) for r in recs]
    except Exception as e:
        pm.err(e=e, m="Error getting doctors")
        return []
    finally:
        session.close()

def create_doctor_for_user(patient_id: str, doctor_data: dict) -> dict:
    now = datetime.now().isoformat()
    doctor_id = doctor_data.get("id", str(uuid.uuid4()))
    session = get_session()
    try:
        session.add(PatientRecord(
            patient_id=patient_id,
            doctor_id=doctor_id,
            data=json.dumps(doctor_data),
            created_at=now, updated_at=now,
        ))
        session.commit()
    except Exception as e:
        session.rollback()
        pm.err(e=e, m="Error creating doctor")
        raise
    finally:
        session.close()
    return {"id": doctor_id, "patient_id": patient_id, **doctor_data, "created_at": now, "updated_at": now}

def update_doctor_for_user(patient_id: str, doctor_id: str, doctor_data: dict) -> dict:
    now = datetime.now().isoformat()
    session = get_session()
    try:
        rec = session.query(PatientRecord).filter(
            PatientRecord.patient_id == patient_id,
            PatientRecord.doctor_id == doctor_id,
        ).first()
        if not rec:
            raise ValueError(f"doctor {doctor_id} not found")
        setattr(rec, "data", json.dumps(doctor_data))
        setattr(rec, "updated_at", now)
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    return {"id": doctor_id, "patient_id": patient_id, **doctor_data, "updated_at": now}

def delete_doctor_for_user(patient_id: str, doctor_id: str) -> bool:
    session = get_session()
    try:
        result = session.query(PatientRecord).filter(
            PatientRecord.patient_id == patient_id,
            PatientRecord.doctor_id == doctor_id,
        ).delete()
        session.commit()
        return result > 0
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()

def create_patient_doctor(patient_id: str, doctor_id: str) -> dict:
    now = datetime.now().isoformat()
    session = get_session()
    try:
        session.add(PatientRecord(
            patient_id=patient_id,
            doctor_id=doctor_id,
            data="{}",
            created_at=now, updated_at=now,
        ))
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    return {"patient_id": patient_id, "doctor_id": doctor_id, "created_at": now, "updated_at": now}

def delete_patient_doctor(patient_id: str, doctor_id: str) -> bool:
    session = get_session()
    try:
        result = session.query(PatientRecord).filter(
            PatientRecord.patient_id == patient_id,
            PatientRecord.doctor_id == doctor_id,
        ).delete()
        session.commit()
        return result > 0
    except Exception:
        session.rollback()
        return False
    finally:
        session.close()
