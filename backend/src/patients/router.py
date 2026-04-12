from fastapi import APIRouter, HTTPException, Depends, status

from ..auth.dependencies import get_current_user_id
from .. import printmeup as pm
from . import service

router = APIRouter(prefix="/api/patients", tags=["patients"])

@router.get("/")
async def endpoint_get_patients(user_id: str = Depends(get_current_user_id)):
    """Get all patients for the authenticated healthcare professional."""
    try:
        # Note: mapping user_id to healthcare_professional_id here as per service method
        patients = service.get_patients(healthcare_professional_id=user_id)
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
async def endpoint_update_patient_for_user(
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
async def endpoint_delete_patient_for_user(
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

@router.get("/hps/")
async def endpoint_get_hps(user_id: str = Depends(get_current_user_id)):
    """Get all healthcare professionals for the authenticated patient."""
    try:
        # Assuming service.get_hps is implemented appropriately
        hps = service.get_hps(patient_id=user_id)
        return hps
    except Exception as e:
        pm.err(e=e, m="Error getting healthcare professionals")
        raise HTTPException(status_code=500, detail="Failed to get healthcare professionals")

@router.post("/hps/", status_code=status.HTTP_201_CREATED)
async def endpoint_create_hp_for_user(
    hp_data: dict,
    user_id: str = Depends(get_current_user_id),
):
    try:
        # Assuming service.create_hp_for_user is implemented appropriately
        hp = service.create_hp_for_user(patient_id=user_id, hp_data=hp_data)
        return hp
    except Exception as e:
        pm.err(e=e, m="Error creating healthcare professional")
        raise HTTPException(status_code=500, detail="Failed to create healthcare professional")

@router.put("/hps/{hp_id}")
async def endpoint_update_hp_for_user(
    hp_id: str,
    hp_data: dict,
    user_id: str = Depends(get_current_user_id),
):
    try:
        # Assuming service.update_hp_for_user is implemented appropriately
        hp = service.update_hp_for_user(patient_id=user_id, hp_id=hp_id, hp_data=hp_data)
        return hp
    except Exception as e:
        pm.err(e=e, m=f"Error updating healthcare professional {hp_id}")
        raise HTTPException(status_code=500, detail="Failed to update healthcare professional")

@router.delete("/hps/{hp_id}")
async def endpoint_delete_hp_for_user(
    hp_id: str,
    user_id: str = Depends(get_current_user_id),
):
    try:
        # Assuming service.delete_hp_for_user is implemented appropriately
        success = service.delete_hp_for_user(patient_id=user_id, hp_id=hp_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete healthcare professional")
        return {"success": True}
    except Exception as e:
        pm.err(e=e, m=f"Error deleting healthcare professional {hp_id}")
        raise HTTPException(status_code=500, detail="Failed to delete healthcare professional")

@router.post("/relationships/")
async def endpoint_create_patient_hp(
    hp_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Create a new patient-healthcare professional relationship."""
    try:
        # Assuming service.create_patient_hp is implemented appropriately
        patient_hp = service.create_patient_hp(patient_id=user_id, hp_id=hp_id)
        return patient_hp
    except Exception as e:
        pm.err(e=e, m="Error creating patient-healthcare professional relationship")
        raise HTTPException(status_code=500, detail="Failed to create relationship")

@router.delete("/relationships/{hp_id}")
async def endpoint_delete_patient_hp(
    hp_id: str,
    user_id: str = Depends(get_current_user_id)
):
    """Delete a patient-healthcare professional relationship."""
    try:
        # Assuming service.delete_patient_hp is implemented appropriately
        service.delete_patient_hp(patient_id=user_id, hp_id=hp_id)
        return {"detail": "Relationship deleted"}
    except Exception as e:
        pm.err(e=e, m="Error deleting patient-healthcare professional relationship")
        raise HTTPException(status_code=500, detail="Failed to delete relationship")
