from __future__ import annotations
from pydantic import BaseModel
from typing import Literal, Optional, List
from datetime import date

from ..auth.models import User

class Patient(BaseModel):
    id: str
    user_id: str
    name: str
    date_of_birth: Optional[date] = None
    gender: Optional[Literal["male", "female"]] = None
    chronic_conditions: List[str] = []
    allergies: List[str] = []
    current_medications: List[str] = []
    notes: Optional[str] = None
    created_at: str
    updated_at: str
    doctors: List[Doctor] = []
    
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

class PatientDetails(BaseModel):
    name: str
    date_of_birth: Optional[date] = None
    gender: Optional[Literal["male", "female"]] = None
    chronic_conditions: List[str] = []
    allergies: List[str] = []
    current_medications: List[str] = []
    notes: Optional[str] = None
    
class Doctor(BaseModel):
    id: str
    user_id: str
    name: str
    specialty: Optional[str] = None
    created_at: str
    updated_at: str
    patients: List[Patient] = []