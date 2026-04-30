
# ok
from fastapi import APIRouter, HTTPException, Depends, status

from ..auth.dependencies import get_current_user_id
from ....legacy import printmeup as pm
from . import service

router = APIRouter(prefix="/api/patients", tags=["patients"])

@router.get("/")
async def endpoint_get_patients(user_id: str = Depends(get_current_user_id)):
    """Get all patients for the authenticated Doctor."""
    try:
        # Note: mapping user_id to doctor_id here as per service method
        patients = service.get_patients(doctor_id=user_id)
        return patients
    except Exception as e:
        pm.err(e=e, m="Error getting patients")
        raise HTTPException(status_code=500, detail="Failed to get patients")

@router.post("/", status_code=status.HTTP_201_CREATED)
async def endpoint_create_patient_for_user(
    patient_data: dict,
    user_id: str = Depends(get_current_user_id),
):
    """Create a new patient."""
    try:
        patient = service.create_patient(
            doctor_id=user_id,
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
            doctor_id=user_id, patient_id=patient_id
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
async def endpoint_update_patient_for_user(
    patient_id: str,
    patient_data: dict,
    user_id: str = Depends(get_current_user_id),
):
    """Update an existing patient."""
    try:
        patient = service.update_patient(
            doctor_id=user_id,
            patient_id=patient_id,
            patient_data=patient_data,
        )
        return patient
    except Exception as e:
        pm.err(e=e, m=f"Error updating patient {patient_id}")
        raise HTTPException(status_code=500, detail="Failed to update patient")

@router.delete("/{patient_id}")
async def endpoint_delete_patient_for_user(
    patient_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Delete a patient."""
    try:
        success = service.delete_patient(
            doctor_id=user_id, patient_id=patient_id
        )
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete patient")
        return {"success": True}
    except HTTPException:
        raise
    except Exception as e:
        pm.err(e=e, m=f"Error deleting patient {patient_id}")
        raise HTTPException(status_code=500, detail="Failed to delete patient")

@router.get("/doctors/")
async def endpoint_get_doctors(user_id: str = Depends(get_current_user_id)):
    """Get all doctors for the authenticated patient."""
    try:
        # Assuming service.get_doctors is implemented appropriately
        doctors = service.get_doctors(patient_id=user_id)
        return doctors
    except Exception as e:
        pm.err(e=e, m="Error getting doctors")
        raise HTTPException(status_code=500, detail="Failed to get doctors")

@router.post("/doctors/", status_code=status.HTTP_201_CREATED)
async def endpoint_create_doctor_for_user(
    doctor_data: dict,
    user_id: str = Depends(get_current_user_id),
):
    try:
        # Assuming service.create_doctor_for_user is implemented appropriately
        doctor = service.create_doctor_for_user(patient_id=user_id, doctor_data=doctor_data)
        return doctor
    except Exception as e:
        pm.err(e=e, m="Error creating doctor")
        raise HTTPException(status_code=500, detail="Failed to create doctor")

@router.put("/doctors/{doctor_id}")
async def endpoint_update_doctor_for_user(
    doctor_id: str,
    doctor_data: dict,
    user_id: str = Depends(get_current_user_id),
):
    try:
        # Assuming service.update_doctor_for_user is implemented appropriately
        doctor = service.update_doctor_for_user(patient_id=user_id, doctor_id=doctor_id, doctor_data=doctor_data)
        return doctor
    except Exception as e:
        pm.err(e=e, m=f"Error updating doctor {doctor_id}")
        raise HTTPException(status_code=500, detail="Failed to update doctor")

@router.delete("/doctors/{doctor_id}")
async def endpoint_delete_doctor_for_user(
    doctor_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        # Assuming service.delete_doctor_for_user is implemented appropriately
        success = service.delete_doctor_for_user(patient_id=user_id, doctor_id=doctor_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete doctor")
        return {"success": True}
    except Exception as e:
        pm.err(e=e, m=f"Error deleting doctor {doctor_id}")
        raise HTTPException(status_code=500, detail="Failed to delete doctor")

@router.post("/relationships/")
async def endpoint_create_patient_doctor(
    doctor_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new patient-doctor relationship."""
    try:
        # Assuming service.create_patient_doctor is implemented appropriately
        patient_doctor = service.create_patient_doctor(patient_id=user_id, doctor_id=doctor_id)
        return patient_doctor
    except Exception as e:
        pm.err(e=e, m="Error creating patient-doctor relationship")
        raise HTTPException(status_code=500, detail="Failed to create relationship")

@router.delete("/relationships/{doctor_id}")
async def endpoint_delete_patient_doctor(
    doctor_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a patient-doctor relationship."""
    try:
        # Assuming service.delete_patient_doctor is implemented appropriately
        service.delete_patient_doctor(patient_id=user_id, doctor_id=doctor_id)
        return {"detail": "Relationship deleted"}
    except Exception as e:
        pm.err(e=e, m="Error deleting patient-doctor relationship")
        raise HTTPException(status_code=500, detail="Failed to delete relationship")
