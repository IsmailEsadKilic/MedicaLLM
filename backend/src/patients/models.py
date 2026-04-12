from pydantic import BaseModel
from typing import Literal, Optional, List
from datetime import date


class Patient(BaseModel):
    id: str
    user_id: str
    name: str
    date_of_birth: Optional[date] = None
    gender: Literal["m", "f"]
    chronic_conditions: List[str] = []
    allergies: List[str] = []
    current_medications: List[str] = []
    notes: Optional[str] = None
    created_at: str
    updated_at: str
    
class HealthcareProfessional(BaseModel):
    id: str
    user_id: str
    name: str
    specialty: Optional[str] = None
    created_at: str
    updated_at: str

# * Patient user - HP user relationship is N:N
class PatientHP(BaseModel):
    user_id: str
    hp_id: str
    created_at: str