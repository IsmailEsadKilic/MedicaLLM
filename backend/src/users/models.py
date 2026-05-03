from __future__ import annotations
from pydantic import BaseModel
from typing import Literal, List
from datetime import date

class PatientBase(BaseModel):
    patient_id: str
    user_id: str
    name: str
    date_of_birth: date | None = None
    gender: Literal["male", "female", "other"] | None = None
    chronic_conditions: List[str] = []
    allergies: List[str] = []
    current_medications: List[str] = []
    notes: str | None = None

class Patient(PatientBase):
    email: str  # from user record
    created_at: str
    updated_at: str
    doctor_ids: List[str] = []  # List of doctor IDs treating this patient

class DoctorBase(BaseModel):
    doctor_id: str 
    user_id: str 
    name: str  # from user record
    specialty: str | None = None

class Doctor(DoctorBase):
    email: str  # from user record
    created_at: str
    updated_at: str
    patient_ids: List[str] = []  # List of patient IDs under this doctor's care

class CreatePatientProfileRequest(BaseModel):
    """Request to create a patient profile for a user"""
    date_of_birth: date | None = None
    gender: Literal["male", "female", "other"] | None = None
    chronic_conditions: List[str] = []
    allergies: List[str] = []
    current_medications: List[str] = []
    notes: str | None = None

class CreateDoctorProfileRequest(BaseModel):
    """Request to create a doctor profile for a user"""
    specialty: str | None = None

class AssignDoctorRequest(BaseModel):
    """Request to assign a doctor to a patient"""
    doctor_id: str
    patient_id: str