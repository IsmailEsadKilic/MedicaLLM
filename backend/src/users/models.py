from __future__ import annotations
from pydantic import BaseModel
from typing import Literal, Optional, List
from datetime import date

class PatientDetails(BaseModel):
    """Patient profile information"""
    name: str
    date_of_birth: Optional[date] = None
    gender: Optional[Literal["male", "female", "other"]] = None
    chronic_conditions: List[str] = []
    allergies: List[str] = []
    current_medications: List[str] = []
    notes: Optional[str] = None

class Patient(BaseModel):
    """Full patient record with user info"""
    patient_id: str
    user_id: str
    name: str  # from user record
    email: str  # from user record
    date_of_birth: Optional[date] = None
    gender: Optional[Literal["male", "female", "other"]] = None
    chronic_conditions: List[str] = []
    allergies: List[str] = []
    current_medications: List[str] = []
    notes: Optional[str] = None
    created_at: str
    updated_at: str
    doctor_ids: List[str] = []  # List of doctor IDs treating this patient
    
    def to_patient_details(self) -> PatientDetails:
        return PatientDetails(
            name=self.name,
            date_of_birth=self.date_of_birth,
            gender=self.gender,
            chronic_conditions=self.chronic_conditions,
            allergies=self.allergies,
            current_medications=self.current_medications,
            notes=self.notes
        )

class DoctorDetails(BaseModel):
    """Doctor profile information"""
    specialty: Optional[str] = None

class Doctor(BaseModel):
    """Full doctor record with user info"""
    doctor_id: str
    user_id: str
    name: str  # from user record
    email: str  # from user record
    specialty: Optional[str] = None
    created_at: str
    updated_at: str
    patient_ids: List[str] = []  # List of patient IDs under this doctor's care
    
    def to_doctor_details(self) -> DoctorDetails:
        return DoctorDetails(
            specialty=self.specialty
        )

class CreatePatientProfileRequest(BaseModel):
    """Request to create a patient profile for a user"""
    date_of_birth: Optional[date] = None
    gender: Optional[Literal["male", "female", "other"]] = None
    chronic_conditions: List[str] = []
    allergies: List[str] = []
    current_medications: List[str] = []
    notes: Optional[str] = None

class CreateDoctorProfileRequest(BaseModel):
    """Request to create a doctor profile for a user"""
    specialty: Optional[str] = None

class AssignDoctorRequest(BaseModel):
    """Request to assign a doctor to a patient"""
    doctor_id: str
    patient_id: str