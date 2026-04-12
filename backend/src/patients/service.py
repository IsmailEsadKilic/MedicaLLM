import json
import uuid
from datetime import datetime

from ..db.sql_client import get_session
from ..db.sql_models import PatientRecord
from .. import printmeup as pm


def _record_to_dict(rec: PatientRecord) -> dict:
    data = json.loads(rec.data) if rec.data else {}
    return {
        "id": rec.patient_id,
        "healthcare_professional_id": rec.healthcare_professional_id,
        **data,
        "created_at": rec.created_at,
        "updated_at": rec.updated_at,
    }


def get_patients(healthcare_professional_id: str) -> list[dict]:
    session = get_session()
    try:
        recs = session.query(PatientRecord).filter(
            PatientRecord.healthcare_professional_id == healthcare_professional_id
        ).all()
        return [_record_to_dict(r) for r in recs]
    except Exception as e:
        pm.err(e=e, m="Error getting patients")
        return []
    finally:
        session.close()


def get_patient(healthcare_professional_id: str, patient_id: str) -> dict | None:
    session = get_session()
    try:
        rec = session.query(PatientRecord).filter(
            PatientRecord.healthcare_professional_id == healthcare_professional_id,
            PatientRecord.patient_id == patient_id,
        ).first()
        return _record_to_dict(rec) if rec else None
    except Exception as e:
        pm.err(e=e, m=f"Error getting patient {patient_id}")
        return None
    finally:
        session.close()


def create_patient(healthcare_professional_id: str, patient_data: dict) -> dict:
    now = datetime.now().isoformat()
    patient_id = str(uuid.uuid4())
    session = get_session()
    try:
        session.add(PatientRecord(
            patient_id=patient_id,
            healthcare_professional_id=healthcare_professional_id,
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
    return {"id": patient_id, "healthcare_professional_id": healthcare_professional_id,
            **patient_data, "created_at": now, "updated_at": now}


def update_patient(healthcare_professional_id: str, patient_id: str, patient_data: dict) -> dict:
    now = datetime.now().isoformat()
    session = get_session()
    try:
        rec = session.query(PatientRecord).filter(
            PatientRecord.healthcare_professional_id == healthcare_professional_id,
            PatientRecord.patient_id == patient_id,
        ).first()
        if not rec:
            raise ValueError(f"Patient {patient_id} not found")
        rec.data = json.dumps(patient_data)
        rec.updated_at = now
        session.commit()
        pm.inf(f"Patient updated: {patient_id}")
    except Exception as e:
        session.rollback()
        raise
    finally:
        session.close()
    return {"id": patient_id, "healthcare_professional_id": healthcare_professional_id,
            **patient_data, "updated_at": now}


def delete_patient(healthcare_professional_id: str, patient_id: str) -> bool:
    session = get_session()
    try:
        result = session.query(PatientRecord).filter(
            PatientRecord.healthcare_professional_id == healthcare_professional_id,
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
