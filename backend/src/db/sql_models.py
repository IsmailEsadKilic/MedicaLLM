"""
SQLAlchemy ORM models for the drug catalog.

Comprehensive relational schema capturing all valuable DrugBank XML data:
drugs, synonyms, groups, categories, products, references, interactions,
food interactions, classifications, dosages, international brands, mixtures,
ATC codes, external identifiers, pathways, targets, enzymes, carriers,
transporters, patents, and prices.
"""

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


class Base(DeclarativeBase):
    pass


# ── Drugs ─────────────────────────────────────────────────────────────────────


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
    cas_number = Column(String(50), default="")
    unii = Column(String(50), default="")
    state = Column(String(50), default="")
    average_mass = Column(Float, nullable=True)
    monoisotopic_mass = Column(Float, nullable=True)
    synthesis_reference = Column(Text, default="")
    fda_label = Column(String(500), default="")
    msds = Column(String(500), default="")
    created_date = Column(String(20), default="")
    updated_date = Column(String(20), default="")

    # Relationships
    synonyms = relationship("DrugSynonym", back_populates="drug", cascade="all, delete-orphan")
    products = relationship("DrugProduct", back_populates="drug", cascade="all, delete-orphan")
    references = relationship("DrugReference", back_populates="drug", cascade="all, delete-orphan")
    groups = relationship("DrugGroup", back_populates="drug", cascade="all, delete-orphan")
    categories = relationship("DrugCategory", back_populates="drug", cascade="all, delete-orphan")
    food_interactions = relationship("DrugFoodInteraction", back_populates="drug", cascade="all, delete-orphan")
    classification = relationship("DrugClassification", back_populates="drug", uselist=False, cascade="all, delete-orphan")
    dosages = relationship("DrugDosage", back_populates="drug", cascade="all, delete-orphan")
    international_brands = relationship("DrugInternationalBrand", back_populates="drug", cascade="all, delete-orphan")
    mixtures = relationship("DrugMixture", back_populates="drug", cascade="all, delete-orphan")
    prices = relationship("DrugPrice", back_populates="drug", cascade="all, delete-orphan")
    atc_codes = relationship("DrugAtcCode", back_populates="drug", cascade="all, delete-orphan")
    external_identifiers = relationship("DrugExternalIdentifier", back_populates="drug", cascade="all, delete-orphan")
    patents = relationship("DrugPatent", back_populates="drug", cascade="all, delete-orphan")
    targets = relationship("DrugTarget", back_populates="drug", cascade="all, delete-orphan")
    enzymes = relationship("DrugEnzyme", back_populates="drug", cascade="all, delete-orphan")
    carriers = relationship("DrugCarrier", back_populates="drug", cascade="all, delete-orphan")
    transporters = relationship("DrugTransporter", back_populates="drug", cascade="all, delete-orphan")
    affected_organisms = relationship("DrugAffectedOrganism", back_populates="drug", cascade="all, delete-orphan")
    pathways = relationship("DrugPathway", back_populates="drug", cascade="all, delete-orphan")
    interactions_as_drug1 = relationship(
        "DrugInteraction", foreign_keys="DrugInteraction.drug1_id",
        back_populates="drug1", cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_drugs_name_lower_trgm", "name_lower"),
    )


# ── Synonyms ──────────────────────────────────────────────────────────────────

class DrugSynonym(Base):
    __tablename__ = "drug_synonyms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    synonym = Column(String(500), nullable=False)
    synonym_lower = Column(String(500), nullable=False, index=True)
    drug = relationship("Drug", back_populates="synonyms")


# ── Groups ────────────────────────────────────────────────────────────────────

class DrugGroup(Base):
    __tablename__ = "drug_groups"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    group_name = Column(String(100), nullable=False)
    drug = relationship("Drug", back_populates="groups")


# ── Categories ────────────────────────────────────────────────────────────────

class DrugCategory(Base):
    __tablename__ = "drug_categories"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    category = Column(String(500), nullable=False)
    category_lower = Column(String(500), nullable=False, index=True)
    drug = relationship("Drug", back_populates="categories")


# ── Classification (ClassyFire) ───────────────────────────────────────────────

class DrugClassification(Base):
    __tablename__ = "drug_classifications"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, unique=True)
    description = Column(Text, default="")
    direct_parent = Column(String(500), default="")
    kingdom = Column(String(200), default="")
    superclass = Column(String(200), default="")
    class_name = Column(String(200), default="")
    subclass = Column(String(200), default="")
    drug = relationship("Drug", back_populates="classification")


# ── Products ──────────────────────────────────────────────────────────────────

class DrugProduct(Base):
    __tablename__ = "drug_products"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
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


# ── Dosages ───────────────────────────────────────────────────────────────────

class DrugDosage(Base):
    __tablename__ = "drug_dosages"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    form = Column(String(200), default="")
    route = Column(String(200), default="")
    strength = Column(String(200), default="")
    drug = relationship("Drug", back_populates="dosages")


# ── International Brands ──────────────────────────────────────────────────────

class DrugInternationalBrand(Base):
    __tablename__ = "drug_international_brands"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    brand_name = Column(String(500), nullable=False)
    brand_name_lower = Column(String(500), nullable=False, index=True)
    company = Column(String(500), default="")
    drug = relationship("Drug", back_populates="international_brands")


# ── Mixtures ──────────────────────────────────────────────────────────────────

class DrugMixture(Base):
    __tablename__ = "drug_mixtures"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    mixture_name = Column(String(500), nullable=False)
    mixture_name_lower = Column(String(500), nullable=False, index=True)
    ingredients = Column(Text, default="")
    supplemental_ingredients = Column(Text, default="")
    drug = relationship("Drug", back_populates="mixtures")


# ── Prices ────────────────────────────────────────────────────────────────────

class DrugPrice(Base):
    __tablename__ = "drug_prices"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    description = Column(String(500), default="")
    cost = Column(String(50), default="")
    currency = Column(String(10), default="")
    unit = Column(String(50), default="")
    drug = relationship("Drug", back_populates="prices")


# ── ATC Codes ─────────────────────────────────────────────────────────────────

class DrugAtcCode(Base):
    __tablename__ = "drug_atc_codes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    code = Column(String(20), nullable=False, index=True)
    drug = relationship("Drug", back_populates="atc_codes")


# ── External Identifiers ─────────────────────────────────────────────────────

class DrugExternalIdentifier(Base):
    __tablename__ = "drug_external_identifiers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    resource = Column(String(200), nullable=False)
    identifier = Column(String(200), nullable=False)
    drug = relationship("Drug", back_populates="external_identifiers")


# ── Patents ───────────────────────────────────────────────────────────────────

class DrugPatent(Base):
    __tablename__ = "drug_patents"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    number = Column(String(100), default="")
    country = Column(String(100), default="")
    approved = Column(String(20), default="")
    expires = Column(String(20), default="")
    pediatric_extension = Column(Boolean, default=False)
    drug = relationship("Drug", back_populates="patents")


# ── References ────────────────────────────────────────────────────────────────

class DrugReference(Base):
    __tablename__ = "drug_references"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    ref_type = Column(String(50), nullable=False)
    pubmed_id = Column(String(50), default="")
    isbn = Column(String(50), default="")
    citation = Column(Text, default="")
    title = Column(Text, default="")
    url = Column(String(500), default="")
    ref_id = Column(String(50), default="")
    drug = relationship("Drug", back_populates="references")


# ── Pharmacological Targets ───────────────────────────────────────────────────

class DrugTarget(Base):
    __tablename__ = "drug_targets"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    target_id = Column(String(50), default="")
    name = Column(String(500), default="")
    organism = Column(String(200), default="")
    known_action = Column(String(20), default="")
    actions = Column(Text, default="")       # comma-separated
    drug = relationship("Drug", back_populates="targets")


class DrugEnzyme(Base):
    __tablename__ = "drug_enzymes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    enzyme_id = Column(String(50), default="")
    name = Column(String(500), default="")
    organism = Column(String(200), default="")
    known_action = Column(String(20), default="")
    actions = Column(Text, default="")
    inhibition_strength = Column(String(50), default="")
    induction_strength = Column(String(50), default="")
    drug = relationship("Drug", back_populates="enzymes")


class DrugCarrier(Base):
    __tablename__ = "drug_carriers"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    carrier_id = Column(String(50), default="")
    name = Column(String(500), default="")
    organism = Column(String(200), default="")
    known_action = Column(String(20), default="")
    actions = Column(Text, default="")
    drug = relationship("Drug", back_populates="carriers")


class DrugTransporter(Base):
    __tablename__ = "drug_transporters"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    transporter_id = Column(String(50), default="")
    name = Column(String(500), default="")
    organism = Column(String(200), default="")
    known_action = Column(String(20), default="")
    actions = Column(Text, default="")
    drug = relationship("Drug", back_populates="transporters")


# ── Affected Organisms ────────────────────────────────────────────────────────

class DrugAffectedOrganism(Base):
    __tablename__ = "drug_affected_organisms"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    organism = Column(String(500), nullable=False)
    drug = relationship("Drug", back_populates="affected_organisms")


# ── Pathways ──────────────────────────────────────────────────────────────────

class DrugPathway(Base):
    __tablename__ = "drug_pathways"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False)
    smpdb_id = Column(String(50), default="")
    pathway_name = Column(String(500), default="")
    category = Column(String(200), default="")
    drug = relationship("Drug", back_populates="pathways")


# ── Drug-Drug Interactions ────────────────────────────────────────────────────

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
    )


# ── Drug-Food Interactions ────────────────────────────────────────────────────

class DrugFoodInteraction(Base):
    __tablename__ = "drug_food_interactions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    drug_pk = Column(Integer, ForeignKey("drugs.id", ondelete="CASCADE"), nullable=False, index=True)
    interaction = Column(Text, nullable=False)
    drug = relationship("Drug", back_populates="food_interactions")


# ══════════════════════════════════════════════════════════════════════════════
# APP-STATE MODELS (users, conversations, patients, pubmed caches)
# ══════════════════════════════════════════════════════════════════════════════


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(100), unique=True, nullable=False, index=True)
    email = Column(String(320), unique=True, nullable=False, index=True)
    password = Column(String(200), nullable=False)
    name = Column(String(200), nullable=False)
    account_type = Column(String(50), nullable=False, default="general_user")
    created_at = Column(String(50), default="")


class ConversationRecord(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    conversation_id = Column(String(100), unique=True, nullable=False, index=True)
    user_id = Column(String(100), nullable=False, index=True)
    title = Column(String(200), default="Untitled")
    messages = Column(Text, default="[]")  # JSON-serialized list
    created_at = Column(String(50), default="")
    updated_at = Column(String(50), default="")


class PatientRecord(Base):
    __tablename__ = "patients"
    id = Column(Integer, primary_key=True, autoincrement=True)
    patient_id = Column(String(100), unique=True, nullable=False, index=True)
    healthcare_professional_id = Column(String(100), nullable=False, index=True)
    data = Column(Text, default="{}")  # JSON-serialized patient data
    created_at = Column(String(50), default="")
    updated_at = Column(String(50), default="")


class PubmedCache(Base):
    __tablename__ = "pubmed_cache"
    id = Column(Integer, primary_key=True, autoincrement=True)
    query_hash = Column(String(32), unique=True, nullable=False, index=True)
    query = Column(String(500), default="")
    articles = Column(Text, default="[]")  # JSON-serialized
    cached_at = Column(String(50), default="")


class PubmedCitation(Base):
    __tablename__ = "pubmed_citations"
    id = Column(Integer, primary_key=True, autoincrement=True)
    pmid = Column(String(50), unique=True, nullable=False, index=True)
    citation_count = Column(Integer, default=0)
    title = Column(Text, default="")
    cached_at = Column(String(50), default="")
    expires_at = Column(Integer, default=0)
