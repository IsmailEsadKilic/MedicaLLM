# Available Drug Fields in DrugBank XML

## ✅ Currently Loaded in Drugs Table

### Basic Information (6/8 fields)
- ✅ `drugbank-id` - Unique identifier (e.g., DB00001)
- ✅ `name` - Drug name
- ✅ `description` - Full description
- ✅ `cas-number` - Chemical Abstracts Service number
- ✅ `unii` - Unique Ingredient Identifier
- ✅ `state` - Solid/liquid/gas
- ❌ `average-mass` - Molecular weight
- ❌ `monoisotopic-mass` - Exact mass

### Clinical Information (9/11 fields)
- ✅ `indication` - What the drug treats
- ✅ `pharmacodynamics` - How the drug works
- ✅ `mechanism-of-action` - Detailed mechanism
- ✅ `toxicity` - Side effects and toxicity info
- ✅ `metabolism` - How body processes it
- ✅ `absorption` - How it's absorbed
- ✅ `half-life` - Duration in body
- ✅ `protein-binding` - Protein binding percentage
- ✅ `route-of-elimination` - How it's excreted
- ❌ `volume-of-distribution` - Distribution in body
- ❌ `clearance` - Clearance rate

### Classification (2/5 fields)
- ✅ `groups` - approved/experimental/withdrawn/investigational
- ✅ `categories` - Drug categories
- ❌ `atc-codes` - Anatomical Therapeutic Chemical codes
- ❌ `ahfs-codes` - American Hospital Formulary Service codes
- ❌ `classification` - Drug classification

### Interactions & Effects (1/3 fields)
- ✅ `drug-interactions` - Drug-drug interactions (in DrugInteractions table)
- ❌ `food-interactions` - Food interactions
- ❌ `affected-organisms` - Which organisms affected

### Chemical & Molecular (1/8 fields)
- ✅ `synonyms` - Alternative names (34,222 synonym entries)
- ❌ `salts` - Salt forms
- ❌ `calculated-properties` - Chemical properties
- ❌ `experimental-properties` - Lab-measured properties
- ❌ `external-identifiers` - IDs in other databases
- ❌ `external-links` - External resources
- ❌ `sequences` - Protein/DNA sequences
- ❌ `pdb-entries` - Protein Data Bank entries

### Products & Brands (0/7 fields)
- ❌ `products` - Commercial products
- ❌ `international-brands` - Brand names worldwide
- ❌ `mixtures` - Drug mixtures
- ❌ `manufacturers` - Manufacturers
- ❌ `packagers` - Packaging companies
- ❌ `prices` - Pricing information
- ❌ `dosages` - Dosage forms

### Pharmacogenomics (0/2 fields)
- ❌ `snp-effects` - SNP effects
- ❌ `snp-adverse-drug-reactions` - Genetic adverse reactions

### Protein Interactions (0/4 fields)
- ❌ `targets` - Drug targets (proteins)
- ❌ `enzymes` - Metabolizing enzymes
- ❌ `carriers` - Carrier proteins
- ❌ `transporters` - Transport proteins

### References & Documentation (0/7 fields)
- ❌ `general-references` - Scientific references
- ❌ `patents` - Patent information
- ❌ `pathways` - Metabolic pathways
- ❌ `reactions` - Chemical reactions
- ❌ `fda-label` - FDA label information
- ❌ `msds` - Material Safety Data Sheet
- ❌ `synthesis-reference` - Synthesis information

---

## 📊 Summary
- **Loaded**: 19/45 fields (42%)
- **Core fields for AI agent**: ✅ Complete
- **Future enhancements**: 26 fields available to add

---

## 📋 Complete List of Fields (45 fields)

### Basic Information (8 fields)
- `drugbank-id`, `name`, `description`, `cas-number`, `unii`, `state`, `average-mass`, `monoisotopic-mass`

### Clinical Information (11 fields)
- `indication`, `pharmacodynamics`, `mechanism-of-action`, `toxicity`, `metabolism`, `absorption`, `half-life`, `protein-binding`, `route-of-elimination`, `volume-of-distribution`, `clearance`

### Classification (5 fields)
- `groups`, `categories`, `atc-codes`, `ahfs-codes`, `classification`

### Interactions & Effects (3 fields)
- `drug-interactions`, `food-interactions`, `affected-organisms`

### Products & Brands (7 fields)
- `products`, `international-brands`, `mixtures`, `manufacturers`, `packagers`, `prices`, `dosages`

### Chemical & Molecular (8 fields)
- `synonyms`, `salts`, `calculated-properties`, `experimental-properties`, `external-identifiers`, `external-links`, `sequences`, `pdb-entries`

### Pharmacogenomics (2 fields)
- `snp-effects`, `snp-adverse-drug-reactions`

### Protein Interactions (4 fields)
- `targets`, `enzymes`, `carriers`, `transporters`

### References & Documentation (7 fields)
- `general-references`, `patents`, `pathways`, `reactions`, `fda-label`, `msds`, `synthesis-reference`

## 💡 Recommended Fields for Drugs Table

For your AI agent, include these essential fields:

```json
{
  "PK": "DRUG#DB00001",
  "drug_id": "DB00001",
  "name": "Lepirudin",
  "name_lower": "lepirudin",
  "description": "Full description...",
  "indication": "What it treats...",
  "groups": ["approved"],
  "categories": ["Anticoagulants", ...],
  "synonyms": ["Alternative names"],
  "mechanism_of_action": "How it works...",
  "toxicity": "Side effects..."
}
```

### Why these fields?
- `name` + `name_lower` - For search/autocomplete
- `description` - For AI context
- `indication` - What it treats
- `groups` - Is it approved?
- `categories` - Drug type
- `synonyms` - Handle alternative names
- `mechanism_of_action` - How it works
- `toxicity` - Safety info
