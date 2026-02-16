from fastapi import APIRouter, HTTPException, Depends, status

from ..auth.dependecies import get_current_user_id
from .. import printmeup as pm
from . import service

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("/")
async def endpoint_get_patients(user_id: str = Depends(get_current_user_id)):
    """Get all patients for the authenticated healthcare professional."""
    try:
        patients = service.get_patients(healthcare_professional_id=user_id)
        return patients
    except Exception as e:
        pm.err(e=e, m="Error getting patients")
        raise HTTPException(status_code=500, detail="Failed to get patients")


@router.post("/", status_code=status.HTTP_201_CREATED)
async def endpoint_create_patient(
    patient_data: dict,
    user_id: str = Depends(get_current_user_id),
):
    """Create a new patient."""
    try:
        patient = service.create_patient(
            healthcare_professional_id=user_id,
            patient_data=patient_data,
        )
        return patient
    except Exception as e:
        pm.err(e=e, m="Error adding patient")
        raise HTTPException(status_code=500, detail="Failed to add patient")


@router.get("/{patient_id}")
async def endpoint_get_patient(
    patient_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get a specific patient by ID."""
    try:
        patient = service.get_patient(
            healthcare_professional_id=user_id, patient_id=patient_id
        )
        if not patient:
            raise HTTPException(status_code=404, detail="Patient not found")
        return patient
    except HTTPException:
        raise
    except Exception as e:
        pm.err(e=e, m=f"Error getting patient {patient_id}")
        raise HTTPException(status_code=500, detail="Failed to get patient")


@router.put("/{patient_id}")
async def endpoint_update_patient(
    patient_id: str,
    patient_data: dict,
    user_id: str = Depends(get_current_user_id),
):
    """Update an existing patient."""
    try:
        patient = service.update_patient(
            healthcare_professional_id=user_id,
            patient_id=patient_id,
            patient_data=patient_data,
        )
        return patient
    except Exception as e:
        pm.err(e=e, m=f"Error updating patient {patient_id}")
        raise HTTPException(status_code=500, detail="Failed to update patient")


@router.delete("/{patient_id}")
async def endpoint_delete_patient(
    patient_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Delete a patient."""
    try:
        success = service.delete_patient(
            healthcare_professional_id=user_id, patient_id=patient_id
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete patient")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        pm.err(e=e, m=f"Error deleting patient {patient_id}")
        raise HTTPException(status_code=500, detail="Failed to delete patient")
