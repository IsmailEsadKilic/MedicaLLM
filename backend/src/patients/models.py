from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class PatientBase(BaseModel):
    name: str
    date_of_birth: Optional[str] = None
    gender: Optional[str] = None
    chronic_conditions: List[str] = []
    allergies: List[str] = []
    current_medications: List[str] = []
    notes: Optional[str] = None


class PatientCreate(PatientBase):
    pass


class PatientUpdate(PatientBase):
    name: Optional[str] = None  # type: ignore


class Patient(PatientBase):
    id: str
    healthcare_professional_id: str
    created_at: str
    updated_at: str
