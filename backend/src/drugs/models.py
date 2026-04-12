from pydantic import BaseModel
from typing import List, Optional


class DrugInfo(BaseModel):
    success: bool
    drug_name: Optional[str] = None
    drug_id: Optional[str] = None
    is_synonym: Optional[bool] = None
    queried_name: Optional[str] = None
    actual_name: Optional[str] = None
    description: str = "N/A"
    indication: str = "N/A"
    mechanism_of_action: str = "N/A"
    pharmacodynamics: str = "N/A"
    toxicity: str = "N/A"
    metabolism: str = "N/A"
    absorption: str = "N/A"
    half_life: str = "N/A"
    protein_binding: str = "N/A"
    route_of_elimination: str = "N/A"
    groups: List[str] = []
    categories: List[str] = []
    cas_number: str = "N/A"
    unii: str = "N/A"
    state: str = "N/A"
    synonym_names: List[str] = []
    product_names: List[str] = []


class DrugSearchResult(BaseModel):
    name: str
    drug_id: Optional[str] = None


class DrugInteractionResult(BaseModel):
    success: bool
    interaction_found: bool = False
    drug1: Optional[str] = None
    drug2: Optional[str] = None
    drug1_id: Optional[str] = None
    drug2_id: Optional[str] = None
    description: Optional[str] = None
    message: Optional[str] = None


class AnalyzePatientRequest(BaseModel):
    chronic_conditions: List[str] = []
    allergies: List[str] = []
    current_medications: List[str] = []
