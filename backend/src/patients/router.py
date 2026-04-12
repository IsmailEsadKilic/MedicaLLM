from fastapi import APIRouter, HTTPException, Depends, status

from ..auth.dependencies import get_current_user_id
from .. import printmeup as pm
from . import service

router = APIRouter(prefix="/api/patients", tags=["patients"])


@router.get("/")
async def endpoint_get_patients(user_id: str = Depends(get_current_user_id)):
    """Get all patients for the authenticated healthcare professional."""
    try:
        patients = service.get_patients(hp_id=user_id)
        return patients
    except Exception as e:
        pm.err(e=e, m="Error getting patients")
        raise HTTPException(status_code=500, detail="Failed to get patients")
    
async def endpoint_create_patient_for_user():
    try:
        patient = service.create_patient_for_user(
    except Exception as e:
        pm.err(e=e, )
        raise HTTPException(

async def endpoint_update_patient_for_user():
    try:
        patient = service.update_patient_for_user(
    except Exception as e:
        pm.err(e=e, )
        raise HTTPException(

async def endpoint_delete_patient_for_user():
    try:
        return service.delete_patient_for_user(
    except Exception as e:
        pm.err(e=e, )
        raise HTTPException(

async def endpoint_get_hps(user_id: str = Depends(get_current_user_id)):
    """Get all healthcare professionals for the authenticated patient."""
    try:
        hps = service.get_hps(patient_id=user_id)
        return hps
    except Exception as e:
        pm.err(e=e, m="Error getting healthcare professionals")
        raise HTTPException(status_code=500, detail="Failed to get healthcare professionals")
    
async def endpoint_create_hp_for_user():
    try:
        patient = service.create_hp_for_user(
    except Exception as e:
        pm.err(e=e, )
        raise HTTPException(

async def endpoint_update_hp_for_user():
    try:
        patient = service.update_hp_for_user(
    except Exception as e:
        pm.err(e=e, )
        raise HTTPException(

async def endpoint_delete_hp_for_user():
    try:
        return service.delete_hp_for_user(
    except Exception as e:
        pm.err(e=e, )
        raise HTTPException(
    
async def endpoint_create_patient_hp(user_id: str = Depends(get_current_user_id)):
    """Create a new patient-healthcare professional relationship."""
    try:
        patient_hp = service.create_patient_hp(patient_id=user_id)
        return patient_hp
    except Exception as e:
        pm.err(e=e, m="Error creating patient-healthcare professional relationship")
        raise HTTPException(status_code=500, detail="Failed to create relationship")

async def endpoint_delete_patient_hp(user_id: str = Depends(get_current_user_id)):
    """Delete a patient-healthcare professional relationship."""
    try:
        service.delete_patient_hp(patient_id=user_id)
        return {"detail": "Relationship deleted"}
    except Exception as e:
        pm.err(e=e, m="Error deleting patient-healthcare professional relationship")
        raise HTTPException(status_code=500, detail="Failed to delete relationship")