from __future__ import annotations
from pydantic import BaseModel, Field
from typing import List

class DrugDescription(BaseModel):
    drug_id: str
    name: str
    description: str = ""

class DrugBase(DrugDescription):
    drug_type: str = ""  # eg "biotech" | "small molecule"
    indication: str = "" # eg "non-small cell lung cancer", "hypertension", "depression"
    mechanism_of_action: str = "" # eg "kinase inhibitor"
    pharmacodynamics: str = "" # eg "inhibits EGFR phosphorylation"
    synonyms: List[str] = [] # eg for "Tylenol": ["Acetaminophen", "Paracetamol"]

class Drug(DrugBase):
    toxicity: str = ""
    metabolism: str = ""
    absorption: str = ""
    half_life: str = ""
    protein_binding: str = ""
    route_of_elimination: str = ""
    volume_of_distribution: str = ""
    clearance: str = "" # eg "renal", "hepatic", "other"
    created_date: str = ""
    updated_date: str = ""

    # these lists might be too large
    interactions: List[DrugInteraction] = []
    food_interactions: List[str] = []
    products: List[DrugProduct] = []
    international_brands: List[DrugInternationalBrand] = []
    
    groups: List[str] = []
    categories: List[str] = []
    dosages: List[DrugDosage] = []
    mixtures: List[DrugMixture] = []
    atc_codes: List[str] = []
    targets: List[DrugTarget] = []
    enzymes: List[DrugEnzyme] = []
    carriers: List[DrugCarrier] = []
    transporters: List[DrugTransporter] = []
    
#section: Drug related models

class DrugSynonym(BaseModel):
    synonym: str

class DrugGroup(BaseModel):
    group_name: str # eg "approved", "investigational", "withdrawn", "illicit", "nutraceutical"

class DrugCategory(BaseModel):
    category: str # eg "antibiotic", "antidepressant", "antihypertensive", "analgesic", "antiviral", etc.

class DrugProduct(BaseModel):
    product_name: str # eg "Tylenol Extra Strength"
    labeller: str = ""
    ndc_id: str = ""
    ndc_product_code: str = ""
    dpd_id: str = ""
    ema_product_code: str = ""
    ema_ma_number: str = ""
    fda_application_number: str = ""
    dosage_form: str = ""
    strength: str = ""
    route: str = ""
    country: str = ""
    source: str = ""
    generic: bool = False
    over_the_counter: bool = False
    approved: bool = False
    started_marketing_on: str = ""
    ended_marketing_on: str = ""

class DrugDosage(BaseModel):
    form: str = ""
    route: str = ""
    strength: str = ""

class DrugInternationalBrand(BaseModel):
    brand_name: str # eg "Tylenol"
    company: str = "" # eg "Johnson & Johnson"

class DrugMixture(BaseModel):
    mixture_name: str # eg "Tylenol Extra Strength"
    ingredients: str = ""
    supplemental_ingredients: str = ""

class DrugAtcCode(BaseModel):
    code: str

class DrugExternalIdentifier(BaseModel):
    resource: str
    identifier: str

class DrugReference(BaseModel):
    ref_type: str  # eg "article", "textbook", "link"
    pubmed_id: str = "" # for articles
    isbn: str = ""
    citation: str = ""
    title: str = ""
    url: str = ""
    ref_id: str = "" # unique identifier for this reference

class DrugTarget(BaseModel):
    target_id: str = ""
    name: str = "" # eg "EGFR" | "Epidermal Growth Factor Receptor"
    organism: str = ""
    known_action: str = ""
    actions: str = ""


class DrugEnzyme(BaseModel):
    enzyme_id: str = ""
    name: str = "" # eg "CYP3A4" | "Cytochrome P450 3A4"
    organism: str = ""
    known_action: str = ""
    actions: str = ""
    inhibition_strength: str = ""
    induction_strength: str = ""


class DrugCarrier(BaseModel):
    carrier_id: str = ""
    name: str = "" # eg "P-glycoprotein" | "P-gp" | "ABCB1"
    organism: str = ""
    known_action: str = ""
    actions: str = ""


class DrugTransporter(BaseModel):
    transporter_id: str = ""
    name: str = "" # eg "P-glycoprotein" | "P-gp" | "ABCB1"
    organism: str = ""
    known_action: str = ""
    actions: str = ""


class DrugInteraction(BaseModel):
    drug2_drugbank_id: str
    drug2_name: str
    description: str = ""


class DrugFoodInteraction(BaseModel):
    interaction: str # eg "Avoid grapefruit juice"

#section: app models
class DrugSearchRequest(BaseModel):
    """
    Search drugs by name, synonym, product name, or brand name.
    """
    query: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=10, ge=1, le=100)
    include_synonyms: bool = True
    include_products: bool = True
    include_brands: bool = True
    
    # whether to include results that match semantically but not lexically
    # (eg "high blood pressure" should match drugs indicated for "hypertension")
    include_semantic_search: bool = False 
    
    min_similarity: float = Field(default=0.3, ge=0.0, le=1.0)

class DrugSearchResponse(BaseModel):
    success: bool = True
    query: str
    results: List[DrugSearchResult]
    count: int
    search_time_ms: float | None = None

class DrugSearchResult(DrugDescription):
    similarity_score: float | None = None  # For fuzzy search, range from 0.0 to 1.0

class CheckDrugInteractionRequest(BaseModel):
    drug_ids: List[str] = Field(..., min_length=2, max_length=10)

class CheckDrugInteractionResponse(BaseModel):
    interactions: List[DrugInteractionDetail] = []
    count: int = 0
    
    # severity of the worst interaction, range from 0.0 (minor) to 1.0 (major).
    # if none, severity is unknown or not provided for all interactions.
    overall_severity: float | None = None 

class DrugInteractionDetail(BaseModel):
    drug1_id: str
    drug1_name: str
    drug2_id: str
    drug2_name: str
    description: str
    
    # range from 0.0 (minor) to 1.0 (major). if none, severity is unknown or not provided.
    severity: float | None = None

class DrugSearchByIndicationRequest(BaseModel):
    indication: str = Field(..., min_length=1, max_length=500)
    limit: int = Field(default=20, ge=1, le=100)
    include_semantic_search: bool = False

class DrugSearchByIndicationResponse(BaseModel):
    success: bool = True
    indication: str
    results: List[DrugDescription]
    count: int
    search_time_ms: float | None = None
    
class DrugSearchByCategoryRequest(BaseModel):
    category: str = Field(..., min_length=1, max_length=100)
    limit: int = Field(default=20, ge=1, le=100)
    include_semantic_search: bool = False
    
class DrugSearchByCategoryResponse(BaseModel):
    success: bool = True
    category: str
    results: List[DrugDescription]
    count: int
    search_time_ms: float | None = None

class DrugAlternative(BaseModel):
    old_drug_id: str
    old_drug_name: str
    new_drug_id: str
    new_drug_name: str
    reason: str = "" # eg "safer for patients with renal impairment"

class AnalyzePatientRequest(BaseModel):
    """
    Analyze a patient's current + additional medications for interactions, and Patient Profile details.
    """
    patient_id: str
    
    # proposed additional medications to analyze along with the patient's current medications.
    additional_drug_ids: List[str] = []

class AnalyzePatientResponse(BaseModel):
    patient_id: str
    current_drugs: List[DrugBase] = []
    interactions: List[DrugInteractionDetail] = []
    count: int = 0
    safe_alternatives: List[DrugAlternative] = []
    
class AnalyzePatientFoodInteractionsRequest(BaseModel):
    patient_id: str
    food_items: List[str] = []
    
    # current and proposed medications to check for interactions with the food items.
    additional_drug_ids: List[str] = []

class AnalyzePatientFoodInteractionsResponse(BaseModel):
    patient_id: str
    current_drugs: List[DrugBase] = []
    interactions: List[DrugFoodInteraction] = []
    count: int = 0
    
    # drugs that may not interact, or have very low severity interactions
    safe_alternatives: List[DrugAlternative] = []

# do this at the end to avoid circular imports
Drug.model_rebuild()
