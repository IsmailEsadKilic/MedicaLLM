from __future__ import annotations
from sqlalchemy import (
    Column,
    ForeignKey, 
    Index,
    Integer,
    Float,
    String,
    Text,
    Boolean,
    Date,
)
from sqlalchemy.orm import DeclarativeBase, relationship
from pgvector.sqlalchemy import Vector


class Base(DeclarativeBase):
    pass


#section: Drugs

class Drug(Base):
    __tablename__ = "drugs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_id = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(500), nullable=False)
    name_lower = Column(String(500), nullable=False, index=True)
    drug_type = Column(String(50), default="")          # biotech | small molecule
    description = Column(Text, default="")
    indication = Column(Text, default="")
    mechanism_of_action = Column(Text, default="")
    pharmacodynamics = Column(Text, default="")
    toxicity = Column(Text, default="")
    metabolism = Column(Text, default="")
    absorption = Column(Text, default="")
    half_life = Column(String(1000), default="")
    protein_binding = Column(String(1000), default="")
    route_of_elimination = Column(Text, default="")
    volume_of_distribution = Column(Text, default="")
    clearance = Column(Text, default="")
    created_date = Column(String(20), default="")
    updated_date = Column(String(20), default="")

    # Relationships
    synonyms = relationship("DrugSynonym", back_populates="drug", cascade="all, delete-orphan")
    products = relationship("DrugProduct", back_populates="drug", cascade="all, delete-orphan")
    references = relationship("DrugReference", back_populates="drug", cascade="all, delete-orphan")
    groups = relationship("DrugGroup", back_populates="drug", cascade="all, delete-orphan")
    categories = relationship("DrugCategory", back_populates="drug", cascade="all, delete-orphan")
    food_interactions = relationship("DrugFoodInteraction", back_populates="drug", cascade="all, delete-orphan")
    dosages = relationship("DrugDosage", back_populates="drug", cascade="all, delete-orphan")
    international_brands = relationship("DrugInternationalBrand", back_populates="drug", cascade="all, delete-orphan")
    mixtures = relationship("DrugMixture", back_populates="drug", cascade="all, delete-orphan")
    atc_codes = relationship("DrugAtcCode", back_populates="drug", cascade="all, delete-orphan")
    external_identifiers = relationship("DrugExternalIdentifier", back_populates="drug", cascade="all, delete-orphan")
    targets = relationship("DrugTarget", back_populates="drug", cascade="all, delete-orphan")
    enzymes = relationship("DrugEnzyme", back_populates="drug", cascade="all, delete-orphan")
    carriers = relationship("DrugCarrier", back_populates="drug", cascade="all, delete-orphan")
    transporters = relationship("DrugTransporter", back_populates="drug", cascade="all, delete-orphan")
    interactions_as_drug1 = relationship(
        "DrugInteraction", foreign_keys="DrugInteraction.drug1_id",
        back_populates="drug1", cascade="all, delete-orphan",
    )
    embedding = relationship("DrugEmbedding", back_populates="drug", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_drugs_name_lower_trgm", "name_lower", postgresql_using="gin", postgresql_ops={"name_lower": "gin_trgm_ops"}),
    )

class DrugSynonym(Base):
    __tablename__ = "drug_synonyms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    synonym = Column(String(500), nullable=False)
    synonym_lower = Column(String(500), nullable=False, index=True)
    drug = relationship("Drug", back_populates="synonyms")
    __table_args__ = (
        Index("ix_synonym_lower_trgm", "synonym_lower", postgresql_using="gin", postgresql_ops={"synonym_lower": "gin_trgm_ops"}),
    )

class DrugGroup(Base):
    __tablename__ = "drug_groups"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    group_name = Column(String(100), nullable=False)
    drug = relationship("Drug", back_populates="groups")

class DrugCategory(Base):
    __tablename__ = "drug_categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    category = Column(String(500), nullable=False)
    category_lower = Column(String(500), nullable=False, index=True)
    drug = relationship("Drug", back_populates="categories")
    
    __table_args__ = (
        Index("ix_categories_lower_trgm", "category_lower", postgresql_using="gin", postgresql_ops={"category_lower": "gin_trgm_ops"}),
    )



class DrugProduct(Base):
    __tablename__ = "drug_products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    product_name = Column(String(500), nullable=False)
    product_name_lower = Column(String(500), nullable=False, index=True)
    labeller = Column(String(500), default="")
    ndc_id = Column(String(100), default="")
    ndc_product_code = Column(String(100), default="")
    dpd_id = Column(String(100), default="")
    ema_product_code = Column(String(100), default="")
    ema_ma_number = Column(String(100), default="")
    fda_application_number = Column(String(100), default="")
    dosage_form = Column(String(200), default="")
    strength = Column(String(200), default="")
    route = Column(String(200), default="")
    country = Column(String(100), default="")
    source = Column(String(50), default="")
    generic = Column(Boolean, default=False)
    over_the_counter = Column(Boolean, default=False)
    approved = Column(Boolean, default=False)
    started_marketing_on = Column(String(20), default="")
    ended_marketing_on = Column(String(20), default="")
    drug = relationship("Drug", back_populates="products")
    
    __table_args__ = (
        Index("ix_products_name_trgm", "product_name_lower", postgresql_using="gin", postgresql_ops={"product_name_lower": "gin_trgm_ops"}),
    )

class DrugDosage(Base):
    __tablename__ = "drug_dosages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    form = Column(String(200), default="")
    route = Column(String(200), default="")
    strength = Column(String(200), default="")
    drug = relationship("Drug", back_populates="dosages")

class DrugInternationalBrand(Base):
    __tablename__ = "drug_international_brands"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    brand_name = Column(String(500), nullable=False)
    brand_name_lower = Column(String(500), nullable=False, index=True)
    company = Column(String(500), default="")
    drug = relationship("Drug", back_populates="international_brands")
    
    __table_args__ = (
        Index("ix_brands_name_trgm", "brand_name_lower", postgresql_using="gin", postgresql_ops={"brand_name_lower": "gin_trgm_ops"}),
    )

class DrugMixture(Base):
    __tablename__ = "drug_mixtures"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    mixture_name = Column(String(500), nullable=False)
    mixture_name_lower = Column(String(500), nullable=False, index=True)
    ingredients = Column(Text, default="")
    supplemental_ingredients = Column(Text, default="")
    drug = relationship("Drug", back_populates="mixtures")
    
    __table_args__ = (
        Index("ix_mixtures_name_trgm", "mixture_name_lower", postgresql_using="gin", postgresql_ops={"mixture_name_lower": "gin_trgm_ops"}),
    )



class DrugAtcCode(Base):
    __tablename__ = "drug_atc_codes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    code = Column(String(20), nullable=False, index=True)
    drug = relationship("Drug", back_populates="atc_codes")

class DrugExternalIdentifier(Base):
    __tablename__ = "drug_external_identifiers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    resource = Column(String(200), nullable=False)
    identifier = Column(String(200), nullable=False)
    drug = relationship("Drug", back_populates="external_identifiers")



class DrugReference(Base):
    __tablename__ = "drug_references"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    ref_type = Column(String(50), nullable=False)
    pubmed_id = Column(String(50), default="")
    isbn = Column(String(50), default="")
    citation = Column(Text, default="")
    title = Column(Text, default="")
    url = Column(String(500), default="")
    ref_id = Column(String(50), default="")
    drug = relationship("Drug", back_populates="references")

class DrugTarget(Base):
    __tablename__ = "drug_targets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    target_id = Column(String(50), default="")
    name = Column(String(500), default="", index=True)
    organism = Column(String(200), default="")
    known_action = Column(String(20), default="")
    actions = Column(Text, default="")       # comma-separated
    drug = relationship("Drug", back_populates="targets")

class DrugEnzyme(Base):
    __tablename__ = "drug_enzymes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    enzyme_id = Column(String(50), default="")
    name = Column(String(500), default="", index=True)
    organism = Column(String(200), default="")
    known_action = Column(String(20), default="")
    actions = Column(Text, default="")
    inhibition_strength = Column(String(50), default="")
    induction_strength = Column(String(50), default="")
    drug = relationship("Drug", back_populates="enzymes")

class DrugCarrier(Base):
    __tablename__ = "drug_carriers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    carrier_id = Column(String(50), default="")
    name = Column(String(500), default="", index=True)
    organism = Column(String(200), default="")
    known_action = Column(String(20), default="")
    actions = Column(Text, default="")
    drug = relationship("Drug", back_populates="carriers")

class DrugTransporter(Base):
    __tablename__ = "drug_transporters"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    transporter_id = Column(String(50), default="")
    name = Column(String(500), default="", index=True)
    organism = Column(String(200), default="")
    known_action = Column(String(20), default="")
    actions = Column(Text, default="")
    drug = relationship("Drug", back_populates="transporters")

class DrugInteraction(Base):
    __tablename__ = "drug_interactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug1_id = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    drug2_drugbank_id = Column(String(20), nullable=False, index=True)
    drug2_name = Column(String(500), nullable=False)
    description = Column(Text, default="")
    drug1 = relationship("Drug", foreign_keys=[drug1_id], back_populates="interactions_as_drug1")
    __table_args__ = (
        Index("ix_interaction_pair", "drug1_id", "drug2_drugbank_id", unique=True),
        Index("ix_interaction_name_trgm", "drug2_name", postgresql_using="gin", postgresql_ops={"drug2_name": "gin_trgm_ops"}),
    )

class DrugFoodInteraction(Base):
    __tablename__ = "drug_food_interactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    interaction = Column(Text, nullable=False)
    drug = relationship("Drug", back_populates="food_interactions")

class DrugEmbedding(Base):
    """
    Stores vector embeddings for semantic drug search.
    Embeddings are generated from drug name, description, indication, mechanism of action, and categories.
    """
    __tablename__ = "drug_embeddings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    embedding = Column(Vector(768), nullable=False)  # nomic-embed-text-v1 uses 768 dimensions
    embedding_text = Column(Text, default="")  # The text that was embedded (for debugging/reprocessing)
    created_at = Column(String(50), default="")
    
    # Relationships
    drug = relationship("Drug", back_populates="embedding")
    
    __table_args__ = (
        # HNSW index for fast approximate nearest neighbor search
        Index("ix_drug_embeddings_hnsw", "embedding", postgresql_using="hnsw", postgresql_with={"m": 16, "ef_construction": 64}, postgresql_ops={"embedding": "vector_cosine_ops"}),
    )

#section: App State

class UserRecord(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(320), unique=True, nullable=False, index=True)
    password = Column(String(200), nullable=False)
    name = Column(String(200), nullable=False)
    created_at = Column(String(50), default="")
    updated_at = Column(String(50), default="")
    
    # Relationships
    conversations = relationship("ConversationRecord", back_populates="user", cascade="all, delete-orphan")
    patient_profile = relationship("PatientRecord", back_populates="user", uselist=False, cascade="all, delete-orphan")
    doctor_profile = relationship("DoctorRecord", back_populates="user", uselist=False, cascade="all, delete-orphan")

class ConversationRecord(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(100), unique=True, nullable=False, index=True)
    user_pk = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), default="Untitled")
    messages = Column(Text, default="[]")  # JSON-serialized list
    created_at = Column(String(50), default="")
    updated_at = Column(String(50), default="")
    
    # Relationships
    user = relationship("UserRecord", back_populates="conversations")

class PatientRecord(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(100), unique=True, nullable=False, index=True)
    user_pk = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    date_of_birth = Column(String(20), default="")
    gender = Column(String(20), default="")
    chronic_conditions = Column(Text, default="[]")  # JSON-serialized list
    allergies = Column(Text, default="[]")  # JSON-serialized list
    current_medications = Column(Text, default="[]")  # JSON-serialized list
    notes = Column(Text, default="")
    created_at = Column(String(50), default="")
    updated_at = Column(String(50), default="")
    
    # Relationships
    user = relationship("UserRecord", back_populates="patient_profile")
    doctors = relationship("DoctorPatientAssociation", back_populates="patient", cascade="all, delete-orphan")

class DoctorRecord(Base):
    __tablename__ = "doctors"
    id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_id = Column(String(100), unique=True, nullable=False, index=True)
    user_pk = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    specialty = Column(String(200), default="")
    created_at = Column(String(50), default="")
    updated_at = Column(String(50), default="")
    
    # Relationships
    user = relationship("UserRecord", back_populates="doctor_profile")
    patients = relationship("DoctorPatientAssociation", back_populates="doctor", cascade="all, delete-orphan")

class DoctorPatientAssociation(Base):
    __tablename__ = "doctor_patient_associations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    doctor_pk = Column(Integer, ForeignKey("doctors.id", ondelete="CASCADE"), nullable=False, index=True)
    patient_pk = Column(Integer, ForeignKey("patients.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(String(50), default="")
    
    # Relationships
    doctor = relationship("DoctorRecord", back_populates="patients")
    patient = relationship("PatientRecord", back_populates="doctors")
    
    __table_args__ = (
        Index("ix_doctor_patient_unique", "doctor_pk", "patient_pk", unique=True),
    )