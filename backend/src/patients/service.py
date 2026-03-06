import uuid
from datetime import datetime
from botocore.exceptions import ClientError

from ..db.client import dynamodb_client
from .. import printmeup as pm
from ..db.tables import PATIENTS_TABLE

def _table():
    return dynamodb_client.Table(PATIENTS_TABLE)  # type: ignore


def get_patients(healthcare_professional_id: str) -> list[dict]:
    """Get all patients for a healthcare professional."""
    try:
        response = _table().query(
            KeyConditionExpression="healthcare_professional_id = :hpId",
            ExpressionAttributeValues={":hpId": healthcare_professional_id},
        )
        return response.get("Items", [])
    except ClientError as e:
        pm.err(e=e, m="Error getting patients")
        return []


def get_patient(healthcare_professional_id: str, patient_id: str) -> dict | None:
    """Get a specific patient by ID."""
    try:
        response = _table().get_item(
            Key={"healthcare_professional_id": healthcare_professional_id, "id": patient_id}
        )
        return response.get("Item")
    except ClientError as e:
        pm.err(e=e, m=f"Error getting patient {patient_id}")
        return None


def create_patient(healthcare_professional_id: str, patient_data: dict) -> dict:
    """Create a new patient."""
    now = datetime.now().isoformat()
    patient = {
        "id": str(uuid.uuid4()),
        "healthcare_professional_id": healthcare_professional_id,
        **patient_data,
        "created_at": now,
        "updated_at": now,
    }
    _table().put_item(Item=patient)
    pm.suc(f"Patient created: {patient['id']}")
    return patient


def update_patient(healthcare_professional_id: str, patient_id: str, patient_data: dict) -> dict:
    """Update an existing patient."""
    patient = {
        "id": patient_id,
        "healthcare_professional_id": healthcare_professional_id,
        **patient_data,
        "updated_at": datetime.now().isoformat(),
    }
    _table().put_item(Item=patient)
    pm.inf(f"Patient updated: {patient_id}")
    return patient


def delete_patient(healthcare_professional_id: str, patient_id: str) -> bool:
    """Delete a patient."""
    try:
        _table().delete_item(
            Key={"healthcare_professional_id": healthcare_professional_id, "id": patient_id}
        )
        pm.suc(f"Patient deleted: {patient_id}")
        return True
    except ClientError as e:
        pm.err(e=e, m=f"Error deleting patient {patient_id}")
        return False
