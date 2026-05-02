
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List

from ..db.sql_client import get_session
from ..db.sql_models import UserRecord
from ..auth.dependencies import get_current_user_id
from ..auth.service import get_user_by_id
from . import service
from .models import (
    Patient,
    PatientBase,
    Doctor,
    DoctorBase,
    CreatePatientProfileRequest,
    CreateDoctorProfileRequest,
    AssignDoctorRequest,
)

router = APIRouter(prefix="/api/users", tags=["users"])

# Patient Profile Endpoints
@router.post("/profile/patient", status_code=status.HTTP_201_CREATED, response_model=Patient)
async def create_patient_profile(
    request: CreatePatientProfileRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Create a patient profile for the authenticated user."""
    patient_data = PatientBase(
        patient_id="",  # Will be generated
        user_id=user_id,
        name="",  # Will be filled from user record
        date_of_birth=request.date_of_birth,
        gender=request.gender,
        chronic_conditions=request.chronic_conditions,
        allergies=request.allergies,
        current_medications=request.current_medications,
        notes=request.notes,
    )
    
    patient = service.create_patient_profile(user_id, patient_data)
    if not patient:
        raise HTTPException(
            status_code=400,
            detail="Failed to create patient profile. Profile may already exist."
        )
    return patient

@router.get("/profile/patient/{patient_id}", response_model=PatientBase)
async def get_patient_details(
    patient_id: str,
    user_id: str = Depends(get_current_user_id),
):
    """Get patient details. Accessible by the patient themselves or their assigned doctors."""
    details = service.get_patient_details(patient_id, user_id)
    if not details:
        raise HTTPException(
            status_code=404,
            detail="Patient not found or access denied"
        )
    return details

# Doctor Profile Endpoints
@router.post("/profile/doctor", status_code=status.HTTP_201_CREATED, response_model=Doctor)
async def create_doctor_profile(
    request: CreateDoctorProfileRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Create a doctor profile for the authenticated user."""
    doctor_data = DoctorBase(
        doctor_id="",  # Will be generated
        user_id=user_id,
        name="",  # Will be filled from user record
        specialty=request.specialty
    )

    doctor = service.create_doctor_profile(user_id, doctor_data)
    if not doctor:
        raise HTTPException(
            status_code=400,
            detail="Failed to create doctor profile. Profile may already exist."
        )
    return doctor

# Doctor-Patient Relationship Endpoints
@router.get("/doctors/patients", response_model=List[Patient])
async def get_patients_for_doctor(user_id: str = Depends(get_current_user_id)):
    """Get all patients assigned to the authenticated doctor."""
    user = get_user_by_id(user_id)
    if not user or not user.is_doctor:
        raise HTTPException(
            status_code=403,
            detail="Only doctors can access this endpoint"
        )

    
    session = get_session()
    try:
        user_rec = session.query(UserRecord).filter(UserRecord.user_id == user_id).first()
        if not user_rec or not user_rec.doctor_profile:
            raise HTTPException(status_code=404, detail="Doctor profile not found")
        
        doctor_id = user_rec.doctor_profile.doctor_id
        patients = service.get_patients_for_doctor(doctor_id)
        return patients
    finally:
        session.close()

@router.get("/patients/doctors", response_model=List[Doctor])
async def get_doctors_for_patient(user_id: str = Depends(get_current_user_id)):
    """Get all doctors assigned to the authenticated patient."""
    user = get_user_by_id(user_id)
    if not user or not user.is_patient:
        raise HTTPException(
            status_code=403,
            detail="Only patients can access this endpoint"
        )
    
    # Get patient_id from user
    session = get_session()
    try:
        user_rec = session.query(UserRecord).filter(UserRecord.user_id == user_id).first()
        if not user_rec or not user_rec.patient_profile:
            raise HTTPException(status_code=404, detail="Patient profile not found")
        
        patient_id = user_rec.patient_profile.patient_id
        doctors = service.get_doctors_for_patient(patient_id)
        return doctors
    finally:
        session.close()

@router.post("/relationships/assign", status_code=status.HTTP_201_CREATED)
async def assign_doctor_to_patient(
    request: AssignDoctorRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Assign a doctor to a patient. Admin only endpoint."""
    # TODO: Add admin authorization check
    success = service.assign_doctor_to_patient(request.doctor_id, request.patient_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to assign doctor to patient"
        )
    return {"success": True, "message": "Doctor assigned to patient successfully"}

@router.delete("/relationships/remove")
async def remove_doctor_from_patient(
    request: AssignDoctorRequest,
    user_id: str = Depends(get_current_user_id),
):
    """Remove a doctor from a patient. Admin only endpoint."""
    # TODO: Add admin authorization check
    success = service.remove_doctor_from_patient(request.doctor_id, request.patient_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail="Failed to remove doctor from patient"
        )
    return {"success": True, "message": "Doctor removed from patient successfully"}
