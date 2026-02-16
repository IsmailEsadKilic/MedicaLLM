from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from xsdata.models.datatype import XmlDate

__NAMESPACE__ = "http://www.drugbank.ca"


@dataclass
class ActionListType:
    class Meta:
        name = "action-list-type"

    action: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class AffectedOrganismListType:
    class Meta:
        name = "affected-organism-list-type"

    affected_organism: list[str] = field(
        default_factory=list,
        metadata={
            "name": "affected-organism",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class AhfsCodeListType:
    class Meta:
        name = "ahfs-code-list-type"

    ahfs_code: list[str] = field(
        default_factory=list,
        metadata={
            "name": "ahfs-code",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class ArticleType:
    class Meta:
        name = "article-type"

    ref_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ref-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    pubmed_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "pubmed-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    citation: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class AtcCodeLevelType:
    class Meta:
        name = "atc-code-level-type"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    code: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class AttachmentType:
    class Meta:
        name = "attachment-type"

    ref_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ref-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    title: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    url: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


class CalculatedPropertyKindType(Enum):
    LOG_P = "logP"
    LOG_S = "logS"
    WATER_SOLUBILITY = "Water Solubility"
    IUPAC_NAME = "IUPAC Name"
    TRADITIONAL_IUPAC_NAME = "Traditional IUPAC Name"
    MOLECULAR_WEIGHT = "Molecular Weight"
    MONOISOTOPIC_WEIGHT = "Monoisotopic Weight"
    SMILES = "SMILES"
    MOLECULAR_FORMULA = "Molecular Formula"
    IN_CH_I = "InChI"
    IN_CH_IKEY = "InChIKey"
    POLAR_SURFACE_AREA_PSA = "Polar Surface Area (PSA)"
    REFRACTIVITY = "Refractivity"
    POLARIZABILITY = "Polarizability"
    ROTATABLE_BOND_COUNT = "Rotatable Bond Count"
    H_BOND_ACCEPTOR_COUNT = "H Bond Acceptor Count"
    H_BOND_DONOR_COUNT = "H Bond Donor Count"
    P_KA_STRONGEST_ACIDIC = "pKa (strongest acidic)"
    P_KA_STRONGEST_BASIC = "pKa (strongest basic)"
    PHYSIOLOGICAL_CHARGE = "Physiological Charge"
    NUMBER_OF_RINGS = "Number of Rings"
    BIOAVAILABILITY = "Bioavailability"
    RULE_OF_FIVE = "Rule of Five"
    GHOSE_FILTER = "Ghose Filter"
    MDDR_LIKE_RULE = "MDDR-Like Rule"
    VEBER_S_RULE = "Veber's Rule"


class CalculatedPropertySourceType(Enum):
    CHEM_AXON = "ChemAxon"
    ALOGPS = "ALOGPS"


@dataclass
class CategoryType:
    class Meta:
        name = "category-type"

    category: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    mesh_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "mesh-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class ClassificationType:
    """Drug classification is obtained from ClassyFire (http://classyfire.wishartlab.com)."""

    class Meta:
        name = "classification-type"

    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    direct_parent: Optional[str] = field(
        default=None,
        metadata={
            "name": "direct-parent",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    kingdom: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    superclass: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    class_value: Optional[str] = field(
        default=None,
        metadata={
            "name": "class",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    subclass: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    alternative_parent: list[str] = field(
        default_factory=list,
        metadata={
            "name": "alternative-parent",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    substituent: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class DosageType:
    class Meta:
        name = "dosage-type"

    form: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    route: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    strength: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


class DrugTypeType(Enum):
    SMALL_MOLECULE = "small molecule"
    BIOTECH = "biotech"


@dataclass
class DrugbankDrugSaltIdType:
    """The DrugBank ID is used to uniquely identify a drug or salt entry.

    There is a primary ID and several secondary IDs that come from older
    ID formats or merged entries.
    """

    class Meta:
        name = "drugbank-drug-salt-id-type"

    value: str = field(
        default="",
        metadata={
            "required": True,
            "min_length": 1,
            "white_space": "collapse",
            "pattern": r"DB[0-9]{5}|DBSALT[0-9]{6}|APRD[0-9]{5}|BIOD[0-9]{5}|BTD[0-9]{5}|EXPT[0-9]{5}|NUTR[0-9]{5}",
        },
    )
    primary: bool = field(
        default=False,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class DrugbankMetaboliteIdType:
    """The metabolite DrugBank ID uniquely identifies a metabolite entry.

    Multiple IDs indicate a merged entry.
    """

    class Meta:
        name = "drugbank-metabolite-id-type"

    value: str = field(
        default="",
        metadata={
            "required": True,
            "min_length": 1,
            "white_space": "collapse",
            "pattern": r"DBMET[0-9]{5}",
        },
    )
    primary: bool = field(
        default=False,
        metadata={
            "type": "Attribute",
        },
    )


class ExperimentalPropertyKindType(Enum):
    WATER_SOLUBILITY = "Water Solubility"
    MELTING_POINT = "Melting Point"
    BOILING_POINT = "Boiling Point"
    LOG_P = "logP"
    LOG_S = "logS"
    HYDROPHOBICITY = "Hydrophobicity"
    ISOELECTRIC_POINT = "Isoelectric Point"
    CACO2_PERMEABILITY = "caco2 Permeability"
    P_KA = "pKa"
    MOLECULAR_WEIGHT = "Molecular Weight"
    MOLECULAR_FORMULA = "Molecular Formula"
    RADIOACTIVITY = "Radioactivity"


class ExternalIdentifierResourceType(Enum):
    UNI_PROT_KB = "UniProtKB"
    WIKIPEDIA = "Wikipedia"
    CH_EBI = "ChEBI"
    CH_EMBL = "ChEMBL"
    PUB_CHEM_COMPOUND = "PubChem Compound"
    PUB_CHEM_SUBSTANCE = "PubChem Substance"
    DRUGS_PRODUCT_DATABASE_DPD = "Drugs Product Database (DPD)"
    KEGG_COMPOUND = "KEGG Compound"
    KEGG_DRUG = "KEGG Drug"
    CHEM_SPIDER = "ChemSpider"
    BINDING_DB = "BindingDB"
    NATIONAL_DRUG_CODE_DIRECTORY = "National Drug Code Directory"
    GEN_BANK = "GenBank"
    THERAPEUTIC_TARGETS_DATABASE = "Therapeutic Targets Database"
    PHARM_GKB = "PharmGKB"
    PDB = "PDB"
    IUPHAR = "IUPHAR"
    GUIDE_TO_PHARMACOLOGY = "Guide to Pharmacology"
    ZINC = "ZINC"
    RX_CUI = "RxCUI"


class ExternalLinkResourceType(Enum):
    RX_LIST = "RxList"
    PDRHEALTH = "PDRhealth"
    DRUGS_COM = "Drugs.com"


@dataclass
class FoodInteractionListType:
    class Meta:
        name = "food-interaction-list-type"

    food_interaction: list[str] = field(
        default_factory=list,
        metadata={
            "name": "food-interaction",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class GoClassifierType:
    class Meta:
        name = "go-classifier-type"

    category: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


class GroupType(Enum):
    """
    Drugs are grouped into a category like approved, experimental, illicit.
    """

    APPROVED = "approved"
    ILLICIT = "illicit"
    EXPERIMENTAL = "experimental"
    WITHDRAWN = "withdrawn"
    NUTRACEUTICAL = "nutraceutical"
    INVESTIGATIONAL = "investigational"
    VET_APPROVED = "vet_approved"


@dataclass
class InternationalBrandType:
    class Meta:
        name = "international-brand-type"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    company: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


class KnownActionType(Enum):
    YES = "yes"
    NO = "no"
    UNKNOWN = "unknown"


@dataclass
class LinkType:
    class Meta:
        name = "link-type"

    ref_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ref-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    title: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    url: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class ManufacturerType:
    class Meta:
        name = "manufacturer-type"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    generic: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    url: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class MixtureType:
    class Meta:
        name = "mixture-type"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    ingredients: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    supplemental_ingredients: Optional[str] = field(
        default=None,
        metadata={
            "name": "supplemental-ingredients",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class PackagerType:
    class Meta:
        name = "packager-type"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    url: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class PatentType:
    class Meta:
        name = "patent-type"

    number: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    country: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    approved: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    expires: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    pediatric_extension: Optional[bool] = field(
        default=None,
        metadata={
            "name": "pediatric-extension",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class PathwayEnzymeListType:
    class Meta:
        name = "pathway-enzyme-list-type"

    uniprot_id: list[str] = field(
        default_factory=list,
        metadata={
            "name": "uniprot-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class PdbEntryListType:
    class Meta:
        name = "pdb-entry-list-type"

    pdb_entry: list[str] = field(
        default_factory=list,
        metadata={
            "name": "pdb-entry",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class PfamType:
    class Meta:
        name = "pfam-type"

    identifier: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


class PolypeptideExternalIdentifierResourceType(Enum):
    UNI_PROT_KB = "UniProtKB"
    UNI_PROT_ACCESSION = "UniProt Accession"
    HUGO_GENE_NOMENCLATURE_COMMITTEE_HGNC = (
        "HUGO Gene Nomenclature Committee (HGNC)"
    )
    HUMAN_PROTEIN_REFERENCE_DATABASE_HPRD = (
        "Human Protein Reference Database (HPRD)"
    )
    GEN_ATLAS = "GenAtlas"
    GENE_CARDS = "GeneCards"
    GEN_BANK_GENE_DATABASE = "GenBank Gene Database"
    GEN_BANK_PROTEIN_DATABASE = "GenBank Protein Database"
    CH_EMBL = "ChEMBL"
    IUPHAR = "IUPHAR"
    GUIDE_TO_PHARMACOLOGY = "Guide to Pharmacology"


@dataclass
class PolypeptideSynonymListType:
    class Meta:
        name = "polypeptide-synonym-list-type"

    synonym: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class PriceType:
    """
    The price for the given drug in US or Canadian currency.
    """

    class Meta:
        name = "price-type"

    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    cost: Optional["PriceType.Cost"] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    unit: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )

    @dataclass
    class Cost:
        value: str = field(
            default="",
            metadata={
                "required": True,
            },
        )
        currency: Optional[str] = field(
            default=None,
            metadata={
                "type": "Attribute",
                "required": True,
            },
        )


class ProductCountryType(Enum):
    """Drug products are currently only imported from the U.S.

    (FDA) and Canada (Canadian Drug Product Database, or DPD).
    """

    US = "US"
    CANADA = "Canada"
    EU = "EU"


class ProductSourceType(Enum):
    """
    Drug products are currently only imported from the FDA and the Canadian Drug
    Product Database, or DPD.
    """

    FDA_NDC = "FDA NDC"
    DPD = "DPD"
    EMA = "EMA"


@dataclass
class ReactionElementType:
    class Meta:
        name = "reaction-element-type"

    drugbank_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "drugbank-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class ReactionEnzymeType:
    class Meta:
        name = "reaction-enzyme-type"

    drugbank_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "drugbank-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    uniprot_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "uniprot-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class SequenceListType:
    class Meta:
        name = "sequence-list-type"

    sequence: list["SequenceListType.Sequence"] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )

    @dataclass
    class Sequence:
        value: str = field(
            default="",
            metadata={
                "required": True,
            },
        )
        format: str = field(
            init=False,
            default="FASTA",
            metadata={
                "type": "Attribute",
            },
        )


@dataclass
class SequenceType:
    class Meta:
        name = "sequence-type"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    format: str = field(
        init=False,
        default="FASTA",
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class SnpAdverseDrugReactionType:
    class Meta:
        name = "snp-adverse-drug-reaction-type"

    protein_name: list[str] = field(
        default_factory=list,
        metadata={
            "name": "protein-name",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "sequence": 1,
        },
    )
    gene_symbol: list[str] = field(
        default_factory=list,
        metadata={
            "name": "gene-symbol",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "sequence": 1,
        },
    )
    uniprot_id: list[str] = field(
        default_factory=list,
        metadata={
            "name": "uniprot-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "sequence": 1,
        },
    )
    rs_id: list[str] = field(
        default_factory=list,
        metadata={
            "name": "rs-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "sequence": 1,
        },
    )
    allele: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "sequence": 1,
        },
    )
    adverse_reaction: list[str] = field(
        default_factory=list,
        metadata={
            "name": "adverse-reaction",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "sequence": 1,
        },
    )
    description: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "sequence": 1,
        },
    )
    pubmed_id: list[str] = field(
        default_factory=list,
        metadata={
            "name": "pubmed-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "sequence": 1,
        },
    )


@dataclass
class SnpEffectType:
    class Meta:
        name = "snp-effect-type"

    protein_name: list[str] = field(
        default_factory=list,
        metadata={
            "name": "protein-name",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "sequence": 1,
        },
    )
    gene_symbol: list[str] = field(
        default_factory=list,
        metadata={
            "name": "gene-symbol",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "sequence": 1,
        },
    )
    uniprot_id: list[str] = field(
        default_factory=list,
        metadata={
            "name": "uniprot-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "sequence": 1,
        },
    )
    rs_id: list[str] = field(
        default_factory=list,
        metadata={
            "name": "rs-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "sequence": 1,
        },
    )
    allele: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "sequence": 1,
        },
    )
    defining_change: list[str] = field(
        default_factory=list,
        metadata={
            "name": "defining-change",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "sequence": 1,
        },
    )
    description: list[str] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "sequence": 1,
        },
    )
    pubmed_id: list[str] = field(
        default_factory=list,
        metadata={
            "name": "pubmed-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "sequence": 1,
        },
    )


class StateType(Enum):
    SOLID = "solid"
    LIQUID = "liquid"
    GAS = "gas"


@dataclass
class SynonymType:
    class Meta:
        name = "synonym-type"

    value: str = field(
        default="",
        metadata={
            "required": True,
        },
    )
    language: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )
    coder: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class TextbookType:
    class Meta:
        name = "textbook-type"

    ref_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ref-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    isbn: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    citation: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class ArticleListType:
    class Meta:
        name = "article-list-type"

    article: list[ArticleType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class AtcCodeType:
    class Meta:
        name = "atc-code-type"

    level: list[AtcCodeLevelType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "min_occurs": 4,
            "max_occurs": 4,
        },
    )
    code: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class AttachmentListType:
    class Meta:
        name = "attachment-list-type"

    attachment: list[AttachmentType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class CalculatedPropertyType:
    class Meta:
        name = "calculated-property-type"

    kind: Optional[CalculatedPropertyKindType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    value: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    source: Optional[CalculatedPropertySourceType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class CategoryListType:
    class Meta:
        name = "category-list-type"

    category: list[CategoryType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class DosageListType:
    class Meta:
        name = "dosage-list-type"

    dosage: list[DosageType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class DrugInteractionType:
    class Meta:
        name = "drug-interaction-type"

    drugbank_id: Optional[DrugbankDrugSaltIdType] = field(
        default=None,
        metadata={
            "name": "drugbank-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class ExperimentalPropertyType:
    class Meta:
        name = "experimental-property-type"

    kind: Optional[ExperimentalPropertyKindType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    value: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    source: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class ExternalIdentifierType:
    class Meta:
        name = "external-identifier-type"

    resource: Optional[ExternalIdentifierResourceType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    identifier: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class ExternalLinkType:
    class Meta:
        name = "external-link-type"

    resource: Optional[ExternalLinkResourceType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    url: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class GoClassifierListType:
    class Meta:
        name = "go-classifier-list-type"

    go_classifier: list[GoClassifierType] = field(
        default_factory=list,
        metadata={
            "name": "go-classifier",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class GroupListType:
    class Meta:
        name = "group-list-type"

    group: list[GroupType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "min_occurs": 1,
            "max_occurs": 6,
        },
    )


@dataclass
class InternationalBrandListType:
    class Meta:
        name = "international-brand-list-type"

    international_brand: list[InternationalBrandType] = field(
        default_factory=list,
        metadata={
            "name": "international-brand",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class LinkListType:
    class Meta:
        name = "link-list-type"

    link: list[LinkType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class ManufacturerListType:
    class Meta:
        name = "manufacturer-list-type"

    manufacturer: list[ManufacturerType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class MixtureListType:
    class Meta:
        name = "mixture-list-type"

    mixture: list[MixtureType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class PackagerListType:
    class Meta:
        name = "packager-list-type"

    packager: list[PackagerType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class PatentListType:
    class Meta:
        name = "patent-list-type"

    patent: list[PatentType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class PathwayDrugType:
    class Meta:
        name = "pathway-drug-type"

    drugbank_id: Optional[DrugbankDrugSaltIdType] = field(
        default=None,
        metadata={
            "name": "drugbank-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class PfamListType:
    class Meta:
        name = "pfam-list-type"

    pfam: list[PfamType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class PolypeptideExternalIdentifierType:
    class Meta:
        name = "polypeptide-external-identifier-type"

    resource: Optional[PolypeptideExternalIdentifierResourceType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    identifier: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class PriceListType:
    class Meta:
        name = "price-list-type"

    price: list[PriceType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class ProductType:
    """
    :ivar name:
    :ivar labeller:
    :ivar ndc_id:
    :ivar ndc_product_code:
    :ivar dpd_id: DPD ID from the Canadian Drug Product Database. Only
        present for drugs that are marketed in Canada.
    :ivar ema_product_code: EMA product code from the European Medicines
        Agency Database. Only present for products that are authorised
        by central procedure for marketing in the European Union.
    :ivar ema_ma_number: EMA marketing authorisation number from the
        European Medicines Agency Database. Only present for products
        that are authorised by central procedure for marketing in the
        European Union.
    :ivar started_marketing_on:
    :ivar ended_marketing_on:
    :ivar dosage_form:
    :ivar strength:
    :ivar route:
    :ivar fda_application_number:
    :ivar generic:
    :ivar over_the_counter:
    :ivar approved:
    :ivar country:
    :ivar source:
    """

    class Meta:
        name = "product-type"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    labeller: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    ndc_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "ndc-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    ndc_product_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "ndc-product-code",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    dpd_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "dpd-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "nillable": True,
        },
    )
    ema_product_code: Optional[str] = field(
        default=None,
        metadata={
            "name": "ema-product-code",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "nillable": True,
        },
    )
    ema_ma_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "ema-ma-number",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "nillable": True,
        },
    )
    started_marketing_on: Optional[str] = field(
        default=None,
        metadata={
            "name": "started-marketing-on",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    ended_marketing_on: Optional[str] = field(
        default=None,
        metadata={
            "name": "ended-marketing-on",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    dosage_form: Optional[str] = field(
        default=None,
        metadata={
            "name": "dosage-form",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    strength: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    route: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    fda_application_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "fda-application-number",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    generic: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    over_the_counter: Optional[bool] = field(
        default=None,
        metadata={
            "name": "over-the-counter",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    approved: Optional[bool] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    country: Optional[ProductCountryType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    source: Optional[ProductSourceType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class ReactionEnzymeListType:
    class Meta:
        name = "reaction-enzyme-list-type"

    enzyme: list[ReactionEnzymeType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class SaltType:
    class Meta:
        name = "salt-type"

    drugbank_id: list[DrugbankDrugSaltIdType] = field(
        default_factory=list,
        metadata={
            "name": "drugbank-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    unii: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    cas_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "cas-number",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    inchikey: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    average_mass: Optional[float] = field(
        default=None,
        metadata={
            "name": "average-mass",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    monoisotopic_mass: Optional[float] = field(
        default=None,
        metadata={
            "name": "monoisotopic-mass",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class SnpAdverseDrugReactionListType:
    class Meta:
        name = "snp-adverse-drug-reaction-list-type"

    reaction: list[SnpAdverseDrugReactionType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class SnpEffectListType:
    class Meta:
        name = "snp-effect-list-type"

    effect: list[SnpEffectType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class SynonymListType:
    class Meta:
        name = "synonym-list-type"

    synonym: list[SynonymType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class TextbookListType:
    class Meta:
        name = "textbook-list-type"

    textbook: list[TextbookType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class AtcCodeListType:
    class Meta:
        name = "atc-code-list-type"

    atc_code: list[AtcCodeType] = field(
        default_factory=list,
        metadata={
            "name": "atc-code",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class CalculatedPropertyListType:
    class Meta:
        name = "calculated-property-list-type"

    property: list[CalculatedPropertyType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class DrugInteractionListType:
    class Meta:
        name = "drug-interaction-list-type"

    drug_interaction: list[DrugInteractionType] = field(
        default_factory=list,
        metadata={
            "name": "drug-interaction",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class ExperimentalPropertyListType:
    class Meta:
        name = "experimental-property-list-type"

    property: list[ExperimentalPropertyType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class ExternalIdentifierListType:
    class Meta:
        name = "external-identifier-list-type"

    external_identifier: list[ExternalIdentifierType] = field(
        default_factory=list,
        metadata={
            "name": "external-identifier",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class ExternalLinkListType:
    class Meta:
        name = "external-link-list-type"

    external_link: list[ExternalLinkType] = field(
        default_factory=list,
        metadata={
            "name": "external-link",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class PathwayDrugListType:
    class Meta:
        name = "pathway-drug-list-type"

    drug: list[PathwayDrugType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "min_occurs": 1,
        },
    )


@dataclass
class PolypeptideExternalIdentifierListType:
    class Meta:
        name = "polypeptide-external-identifier-list-type"

    external_identifier: list[PolypeptideExternalIdentifierType] = field(
        default_factory=list,
        metadata={
            "name": "external-identifier",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class ProductListType:
    class Meta:
        name = "product-list-type"

    product: list[ProductType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class ReactionType:
    class Meta:
        name = "reaction-type"

    sequence: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    left_element: Optional[ReactionElementType] = field(
        default=None,
        metadata={
            "name": "left-element",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    right_element: Optional[ReactionElementType] = field(
        default=None,
        metadata={
            "name": "right-element",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    enzymes: Optional[ReactionEnzymeListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class ReferenceListType:
    """
    :ivar articles: Articles are typically PubMed references, although
        there are some references which do not have a PubMed ID.
    :ivar textbooks:
    :ivar links:
    :ivar attachments:
    """

    class Meta:
        name = "reference-list-type"

    articles: Optional[ArticleListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    textbooks: Optional[TextbookListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    links: Optional[LinkListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    attachments: Optional[AttachmentListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class SaltListType:
    class Meta:
        name = "salt-list-type"

    salt: list[SaltType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class PathwayType:
    class Meta:
        name = "pathway-type"

    smpdb_id: Optional[str] = field(
        default=None,
        metadata={
            "name": "smpdb-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    category: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    drugs: Optional[PathwayDrugListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    enzymes: Optional[PathwayEnzymeListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )


@dataclass
class PolypeptideType:
    class Meta:
        name = "polypeptide-type"

    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    general_function: Optional[str] = field(
        default=None,
        metadata={
            "name": "general-function",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    specific_function: Optional[str] = field(
        default=None,
        metadata={
            "name": "specific-function",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    gene_name: Optional[str] = field(
        default=None,
        metadata={
            "name": "gene-name",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    locus: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    cellular_location: Optional[str] = field(
        default=None,
        metadata={
            "name": "cellular-location",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    transmembrane_regions: Optional[str] = field(
        default=None,
        metadata={
            "name": "transmembrane-regions",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    signal_regions: Optional[str] = field(
        default=None,
        metadata={
            "name": "signal-regions",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    theoretical_pi: Optional[str] = field(
        default=None,
        metadata={
            "name": "theoretical-pi",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    molecular_weight: Optional[str] = field(
        default=None,
        metadata={
            "name": "molecular-weight",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    chromosome_location: Optional[str] = field(
        default=None,
        metadata={
            "name": "chromosome-location",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    organism: Optional["PolypeptideType.Organism"] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    external_identifiers: Optional[PolypeptideExternalIdentifierListType] = (
        field(
            default=None,
            metadata={
                "name": "external-identifiers",
                "type": "Element",
                "namespace": "http://www.drugbank.ca",
                "required": True,
            },
        )
    )
    synonyms: Optional[PolypeptideSynonymListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    amino_acid_sequence: Optional[SequenceType] = field(
        default=None,
        metadata={
            "name": "amino-acid-sequence",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    gene_sequence: Optional[SequenceType] = field(
        default=None,
        metadata={
            "name": "gene-sequence",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    pfams: Optional[PfamListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    go_classifiers: Optional[GoClassifierListType] = field(
        default=None,
        metadata={
            "name": "go-classifiers",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    source: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )

    @dataclass
    class Organism:
        value: str = field(
            default="",
            metadata={
                "required": True,
            },
        )
        ncbi_taxonomy_id: Optional[str] = field(
            default=None,
            metadata={
                "name": "ncbi-taxonomy-id",
                "type": "Attribute",
            },
        )


@dataclass
class ReactionListType:
    class Meta:
        name = "reaction-list-type"

    reaction: list[ReactionType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class CarrierType:
    class Meta:
        name = "carrier-type"

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    organism: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    actions: Optional[ActionListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    references: Optional[ReferenceListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    known_action: Optional[KnownActionType] = field(
        default=None,
        metadata={
            "name": "known-action",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    polypeptide: list[PolypeptideType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    position: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class EnzymeType:
    class Meta:
        name = "enzyme-type"

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    organism: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    actions: Optional[ActionListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    references: Optional[ReferenceListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    known_action: Optional[KnownActionType] = field(
        default=None,
        metadata={
            "name": "known-action",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    polypeptide: list[PolypeptideType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    inhibition_strength: Optional[str] = field(
        default=None,
        metadata={
            "name": "inhibition-strength",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    induction_strength: Optional[str] = field(
        default=None,
        metadata={
            "name": "induction-strength",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    position: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class PathwayListType:
    class Meta:
        name = "pathway-list-type"

    pathway: list[PathwayType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class PolypeptideListType:
    class Meta:
        name = "polypeptide-list-type"

    polypeptide: list[PolypeptideType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class TargetType:
    class Meta:
        name = "target-type"

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    organism: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    actions: Optional[ActionListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    references: Optional[ReferenceListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    known_action: Optional[KnownActionType] = field(
        default=None,
        metadata={
            "name": "known-action",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    polypeptide: list[PolypeptideType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    position: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class TransporterType:
    class Meta:
        name = "transporter-type"

    id: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    organism: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    actions: Optional[ActionListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    references: Optional[ReferenceListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    known_action: Optional[KnownActionType] = field(
        default=None,
        metadata={
            "name": "known-action",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    polypeptide: list[PolypeptideType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    position: Optional[int] = field(
        default=None,
        metadata={
            "type": "Attribute",
        },
    )


@dataclass
class CarrierListType:
    class Meta:
        name = "carrier-list-type"

    carrier: list[CarrierType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class EnzymeListType:
    class Meta:
        name = "enzyme-list-type"

    enzyme: list[EnzymeType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class TargetListType:
    class Meta:
        name = "target-list-type"

    target: list[TargetType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class TransporterListType:
    class Meta:
        name = "transporter-list-type"

    transporter: list[TransporterType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )


@dataclass
class DrugType:
    class Meta:
        name = "drug-type"

    drugbank_id: list[DrugbankDrugSaltIdType] = field(
        default_factory=list,
        metadata={
            "name": "drugbank-id",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "min_occurs": 1,
        },
    )
    name: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    description: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    cas_number: Optional[str] = field(
        default=None,
        metadata={
            "name": "cas-number",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    unii: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    average_mass: Optional[float] = field(
        default=None,
        metadata={
            "name": "average-mass",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    monoisotopic_mass: Optional[float] = field(
        default=None,
        metadata={
            "name": "monoisotopic-mass",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    state: Optional[StateType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    groups: Optional[GroupListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    general_references: Optional[ReferenceListType] = field(
        default=None,
        metadata={
            "name": "general-references",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    synthesis_reference: Optional[str] = field(
        default=None,
        metadata={
            "name": "synthesis-reference",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    indication: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    pharmacodynamics: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    mechanism_of_action: Optional[str] = field(
        default=None,
        metadata={
            "name": "mechanism-of-action",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    toxicity: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    metabolism: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    absorption: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    half_life: Optional[str] = field(
        default=None,
        metadata={
            "name": "half-life",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    protein_binding: Optional[str] = field(
        default=None,
        metadata={
            "name": "protein-binding",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    route_of_elimination: Optional[str] = field(
        default=None,
        metadata={
            "name": "route-of-elimination",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    volume_of_distribution: Optional[str] = field(
        default=None,
        metadata={
            "name": "volume-of-distribution",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    clearance: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    classification: Optional[ClassificationType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    salts: Optional[SaltListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    synonyms: Optional[SynonymListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    products: Optional[ProductListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    international_brands: Optional[InternationalBrandListType] = field(
        default=None,
        metadata={
            "name": "international-brands",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    mixtures: Optional[MixtureListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    packagers: Optional[PackagerListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    manufacturers: Optional[ManufacturerListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    prices: Optional[PriceListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    categories: Optional[CategoryListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    affected_organisms: Optional[AffectedOrganismListType] = field(
        default=None,
        metadata={
            "name": "affected-organisms",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    dosages: Optional[DosageListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    atc_codes: Optional[AtcCodeListType] = field(
        default=None,
        metadata={
            "name": "atc-codes",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    ahfs_codes: Optional[AhfsCodeListType] = field(
        default=None,
        metadata={
            "name": "ahfs-codes",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    pdb_entries: Optional[PdbEntryListType] = field(
        default=None,
        metadata={
            "name": "pdb-entries",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    fda_label: Optional[str] = field(
        default=None,
        metadata={
            "name": "fda-label",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    msds: Optional[str] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    patents: Optional[PatentListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    food_interactions: Optional[FoodInteractionListType] = field(
        default=None,
        metadata={
            "name": "food-interactions",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    drug_interactions: Optional[DrugInteractionListType] = field(
        default=None,
        metadata={
            "name": "drug-interactions",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    sequences: Optional[SequenceListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    calculated_properties: Optional[CalculatedPropertyListType] = field(
        default=None,
        metadata={
            "name": "calculated-properties",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
        },
    )
    experimental_properties: Optional[ExperimentalPropertyListType] = field(
        default=None,
        metadata={
            "name": "experimental-properties",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    external_identifiers: Optional[ExternalIdentifierListType] = field(
        default=None,
        metadata={
            "name": "external-identifiers",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    external_links: Optional[ExternalLinkListType] = field(
        default=None,
        metadata={
            "name": "external-links",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    pathways: Optional[PathwayListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    reactions: Optional[ReactionListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    snp_effects: Optional[SnpEffectListType] = field(
        default=None,
        metadata={
            "name": "snp-effects",
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    snp_adverse_drug_reactions: Optional[SnpAdverseDrugReactionListType] = (
        field(
            default=None,
            metadata={
                "name": "snp-adverse-drug-reactions",
                "type": "Element",
                "namespace": "http://www.drugbank.ca",
                "required": True,
            },
        )
    )
    targets: Optional[TargetListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    enzymes: Optional[EnzymeListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    carriers: Optional[CarrierListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    transporters: Optional[TransporterListType] = field(
        default=None,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "required": True,
        },
    )
    type_value: Optional[DrugTypeType] = field(
        default=None,
        metadata={
            "name": "type",
            "type": "Attribute",
            "required": True,
        },
    )
    created: Optional[XmlDate] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    updated: Optional[XmlDate] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class DrugbankType:
    """
    This is the root element type for the DrugBank database schema.

    :ivar drug:
    :ivar version: The DrugBank version for the exported XML file.
    :ivar exported_on: The date the XML file was exported.
    """

    class Meta:
        name = "drugbank-type"

    drug: list[DrugType] = field(
        default_factory=list,
        metadata={
            "type": "Element",
            "namespace": "http://www.drugbank.ca",
            "min_occurs": 1,
        },
    )
    version: Optional[str] = field(
        default=None,
        metadata={
            "type": "Attribute",
            "required": True,
        },
    )
    exported_on: Optional[XmlDate] = field(
        default=None,
        metadata={
            "name": "exported-on",
            "type": "Attribute",
            "required": True,
        },
    )


@dataclass
class Drugbank(DrugbankType):
    """This is the root element for the DrugBank database schema.

    DrugBank is a database on drug and drug-targets.
    """

    class Meta:
        name = "drugbank"
        namespace = "http://www.drugbank.ca"
