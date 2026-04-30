"""
Drug catalog service — SQLite/SQLAlchemy implementation.

Replaces the DynamoDB-based service with proper relational queries:
- LIKE / contains for search (no more full-table scans)
- JOINs for synonym resolution, categories, products, references
- OR-based bidirectional interaction lookup
"""

from __future__ import annotations

import re
from typing import Optional

from sqlalchemy import or_, func
from sqlalchemy.orm import Session, joinedload

from ..db.sql_client import get_session
from ..db.sql_models import (
    Drug,
    DrugSynonym,
    DrugGroup,
    DrugCategory,
    DrugProduct,
    DrugReference,
    DrugInteraction,
    DrugFoodInteraction,
    DrugClassification,
    DrugInternationalBrand,
    DrugMixture,
    DrugDosage,
    DrugTarget,
    DrugEnzyme,
    DrugAtcCode,
)
from ....legacy import printmeup as pm


# ========================================================================
# INTERACTION SEVERITY CLASSIFICATION
# ========================================================================

_SEVERITY_CONTRAINDICATED = re.compile(
    r"contraindicated|do not use|must not|avoid concomitant|absolute.+prohibition",
    re.IGNORECASE,
)
_SEVERITY_MAJOR = re.compile(
    r"life.?threatening|fatal|death|serotonin syndrome|neuroleptic malignant"
    r"|hemorrhag|QT.?prolong|torsade|cardiac arrest|seizure|arrhythmi"
    r"|severe.+hypotension|severe.+bleeding|hypertensive crisis",
    re.IGNORECASE,
)
_SEVERITY_MODERATE = re.compile(
    r"increas.+risk|decreas.+effect|alter.+metabolism|may.+increase|may.+decrease"
    r"|monitor.+closely|adjust.+dose|enhance.+effect|reduce.+efficacy"
    r"|plasma.+concentration|auc.+increase|auc.+decrease|clearance.+decrease",
    re.IGNORECASE,
)

SEVERITY_ORDER = {"contraindicated": 0, "major": 1, "moderate": 2, "minor": 3}


def classify_interaction_severity(description: str) -> str:
    if not description:
        return "moderate"
    if _SEVERITY_CONTRAINDICATED.search(description):
        return "contraindicated"
    if _SEVERITY_MAJOR.search(description):
        return "major"
    if _SEVERITY_MODERATE.search(description):
        return "moderate"
    return "minor"


# ========================================================================
# INTERNAL HELPERS
# ========================================================================


def _resolve_drug(session: Session, name: str) -> Optional[Drug]:
    """Resolve a drug name (or synonym, product name, brand name) to a Drug ORM object."""
    name = name.strip()
    variants = [name, name.title(), name.upper(), name.lower()]

    for variant in variants:
        # Direct name match
        drug = session.query(Drug).filter(Drug.name == variant).first()
        if drug:
            return drug

        # Synonym match
        syn = session.query(DrugSynonym).filter(DrugSynonym.synonym == variant).first()
        if syn:
            return session.query(Drug).filter(Drug.id == syn.drug_pk).first()

    # Case-insensitive fallback
    drug = session.query(Drug).filter(Drug.name_lower == name.lower()).first()
    if drug:
        return drug

    syn = session.query(DrugSynonym).filter(DrugSynonym.synonym_lower == name.lower()).first()
    if syn:
        return session.query(Drug).filter(Drug.id == syn.drug_pk).first()

    # Product name → drug
    prod = session.query(DrugProduct).filter(DrugProduct.product_name_lower == name.lower()).first()
    if prod:
        return session.query(Drug).filter(Drug.id == prod.drug_pk).first()

    # International brand → drug
    brand = session.query(DrugInternationalBrand).filter(DrugInternationalBrand.brand_name_lower == name.lower()).first()
    if brand:
        return session.query(Drug).filter(Drug.id == brand.drug_pk).first()

    # Mixture name → drug
    mix = session.query(DrugMixture).filter(DrugMixture.mixture_name_lower == name.lower()).first()
    if mix:
        return session.query(Drug).filter(Drug.id == mix.drug_pk).first()

    return None


def _drug_to_dict(drug: Drug, queried_name: str, is_synonym: bool = False) -> dict:
    """Convert a Drug ORM object to the API response dict."""
    groups = [g.group_name for g in drug.groups]
    categories = [c.category for c in drug.categories]
    synonym_names = [s.synonym for s in drug.synonyms]

    # Classification
    cls = drug.classification
    classification = None
    if cls:
        classification = {
            "description": cls.description or "",
            "direct_parent": cls.direct_parent or "",
            "kingdom": cls.kingdom or "",
            "superclass": cls.superclass or "",
            "class": cls.class_name or "",
            "subclass": cls.subclass or "",
        }

    # Targets
    targets = [{"name": t.name, "actions": t.actions, "known_action": t.known_action} for t in drug.targets]

    # Enzymes
    enzymes = [{"name": e.name, "actions": e.actions, "inhibition_strength": e.inhibition_strength,
                "induction_strength": e.induction_strength} for e in drug.enzymes]

    result = {
        "success": True,
        "drug_name": drug.name,
        "drug_id": drug.drug_id,
        "drug_type": drug.drug_type or "N/A",
        "description": drug.description or "N/A",
        "indication": drug.indication or "N/A",
        "mechanism_of_action": drug.mechanism_of_action or "N/A",
        "pharmacodynamics": drug.pharmacodynamics or "N/A",
        "toxicity": drug.toxicity or "N/A",
        "metabolism": drug.metabolism or "N/A",
        "absorption": drug.absorption or "N/A",
        "half_life": drug.half_life or "N/A",
        "protein_binding": drug.protein_binding or "N/A",
        "route_of_elimination": drug.route_of_elimination or "N/A",
        "volume_of_distribution": drug.volume_of_distribution or "N/A",
        "clearance": drug.clearance or "N/A",
        "average_mass": drug.average_mass,
        "monoisotopic_mass": drug.monoisotopic_mass,
        "groups": groups,
        "categories": categories,
        "classification": classification,
        "cas_number": drug.cas_number or "N/A",
        "unii": drug.unii or "N/A",
        "state": drug.state or "N/A",
        "fda_label": drug.fda_label or "",
        "synonym_names": synonym_names,
        "product_names": [],
        "targets": targets,
        "enzymes": enzymes,
    }
    if is_synonym:
        result["is_synonym"] = True
        result["queried_name"] = queried_name
        result["actual_name"] = drug.name
    return result


# ========================================================================
# PUBLIC API — same signatures as the old DynamoDB service
# ========================================================================


def resolve_drug_name(drug_name: str) -> str:
    """Resolve a drug name (synonym or actual) to its canonical name."""
    session = get_session()
    try:
        drug = _resolve_drug(session, drug_name)
        if drug:
            pm.suc(f"Resolved '{drug_name}' -> '{drug.name}'")
            return drug.name
        pm.war(f"Drug not found, using title case: '{drug_name.title()}'")
        return drug_name.title()
    finally:
        session.close()


def get_drug_info(drug_name: str) -> dict:
    """Get detailed drug information. Supports synonym resolution."""
    session = get_session()
    try:
        drug_name = drug_name.strip()
        drug = _resolve_drug(session, drug_name)
        if not drug:
            pm.war(f"Drug '{drug_name}' not found")
            return {"success": False, "error": f"Drug '{drug_name}' not found in database"}

        is_synonym = drug.name.lower() != drug_name.lower()
        pm.inf(f"Found drug: {drug.name}")
        return _drug_to_dict(drug, drug_name, is_synonym=is_synonym)
    except Exception as e:
        pm.err(e=e, m=f"Error getting drug info for '{drug_name}'")
        return {"success": False, "error": str(e)}
    finally:
        session.close()


# ========================================================================
# DRUG SEARCH
# ========================================================================


def search_drugs(query: str) -> dict:
    """Search drugs by name, synonym, product name, or brand name using SQL LIKE."""
    session = get_session()
    try:
        search_term = query.lower().strip()
        if not search_term:
            return {"drugs": [], "count": 0}

        drug_map: dict[str, dict] = {}

        # Search by drug name
        for name, drug_id, name_lower in (
            session.query(Drug.name, Drug.drug_id, Drug.name_lower)
            .filter(Drug.name_lower.contains(search_term))
            .limit(50)
            .all()
        ):
            drug_map[name] = {"name": name, "drug_id": drug_id, "name_lower": name_lower}

        # Search by synonym
        for syn_name, drug_pk in (
            session.query(DrugSynonym.synonym, DrugSynonym.drug_pk)
            .filter(DrugSynonym.synonym_lower.contains(search_term))
            .limit(50)
            .all()
        ):
            drug = session.query(Drug).filter(Drug.id == drug_pk).first()
            if drug and drug.name not in drug_map:
                drug_map[drug.name] = {"name": drug.name, "drug_id": drug.drug_id, "name_lower": drug.name_lower}

        # Search by product name
        for prod in (
            session.query(DrugProduct)
            .filter(DrugProduct.product_name_lower.contains(search_term))
            .limit(20)
            .all()
        ):
            drug = session.query(Drug).filter(Drug.id == prod.drug_pk).first()
            if drug and drug.name not in drug_map:
                drug_map[drug.name] = {"name": drug.name, "drug_id": drug.drug_id, "name_lower": drug.name_lower}

        # Search by international brand
        for brand in (
            session.query(DrugInternationalBrand)
            .filter(DrugInternationalBrand.brand_name_lower.contains(search_term))
            .limit(20)
            .all()
        ):
            drug = session.query(Drug).filter(Drug.id == brand.drug_pk).first()
            if drug and drug.name not in drug_map:
                drug_map[drug.name] = {"name": drug.name, "drug_id": drug.drug_id, "name_lower": drug.name_lower}

        # Sort: starts-with first, then alphabetical
        drugs = sorted(
            drug_map.values(),
            key=lambda d: (not d["name_lower"].startswith(search_term), d["name"]),
        )[:10]

        return {
            "drugs": [{"name": d["name"], "drug_id": d.get("drug_id")} for d in drugs],
            "count": len(drugs),
        }
    except Exception as e:
        pm.err(e=e, m=f"Error searching drugs for '{query}'")
        return {"drugs": [], "count": 0, "error": str(e)}
    finally:
        session.close()


# ========================================================================
# DRUG INTERACTIONS
# ========================================================================


def check_drug_interaction(drug1: str, drug2: str) -> dict:
    """Check if two drugs interact. Resolves synonyms, queries both directions."""
    session = get_session()
    try:
        drug1 = drug1.strip()
        drug2 = drug2.strip()

        drug1_obj = _resolve_drug(session, drug1)
        drug2_obj = _resolve_drug(session, drug2)

        resolved1 = drug1_obj.name if drug1_obj else drug1.title()
        resolved2 = drug2_obj.name if drug2_obj else drug2.title()

        pm.inf(f"Checking interaction: '{resolved1}' + '{resolved2}'")

        if drug1_obj and drug2_obj:
            # Query both directions with a single OR
            interaction = (
                session.query(DrugInteraction)
                .filter(
                    or_(
                        (DrugInteraction.drug1_id == drug1_obj.id)
                        & (DrugInteraction.drug2_drugbank_id == drug2_obj.drug_id),
                        (DrugInteraction.drug1_id == drug2_obj.id)
                        & (DrugInteraction.drug2_drugbank_id == drug1_obj.drug_id),
                    )
                )
                .first()
            )

            if interaction:
                description = interaction.description or "No description available"
                severity = classify_interaction_severity(description)
                pm.suc(f"Interaction found: {resolved1} + {resolved2} (severity: {severity})")

                # Determine which direction matched for consistent naming
                if interaction.drug1_id == drug1_obj.id:
                    d1_name, d1_id = drug1_obj.name, drug1_obj.drug_id
                    d2_name, d2_id = interaction.drug2_name, interaction.drug2_drugbank_id
                else:
                    d1_name, d1_id = drug2_obj.name, drug2_obj.drug_id
                    d2_name, d2_id = interaction.drug2_name, interaction.drug2_drugbank_id

                return {
                    "success": True,
                    "interaction_found": True,
                    "drug1": d1_name,
                    "drug2": d2_name,
                    "drug1_id": d1_id,
                    "drug2_id": d2_id,
                    "description": description,
                    "severity": severity,
                }

        pm.war(f"No interaction found between {resolved1} and {resolved2}")
        return {
            "success": True,
            "interaction_found": False,
            "drug1": resolved1,
            "drug2": resolved2,
            "message": f"No known interaction found between {resolved1} and {resolved2}",
        }
    except Exception as e:
        pm.err(e=e, m=f"Error checking interaction between '{drug1}' and '{drug2}'")
        return {"success": False, "error": str(e)}
    finally:
        session.close()


# ========================================================================
# DRUG-FOOD INTERACTIONS
# ========================================================================


def get_drug_food_interactions(drug_name: str) -> dict:
    """Get food interactions for a specific drug."""
    session = get_session()
    try:
        drug_name = drug_name.strip()
        drug = _resolve_drug(session, drug_name)
        if not drug:
            return {
                "success": True,
                "drug_name": drug_name,
                "interactions": [],
                "count": 0,
                "message": f"Drug '{drug_name}' not found",
            }

        interactions = [fi.interaction for fi in drug.food_interactions]
        pm.suc(f"Found {len(interactions)} food interactions for {drug.name}")
        return {
            "success": True,
            "drug_name": drug.name,
            "interactions": interactions,
            "count": len(interactions),
        }
    except Exception as e:
        pm.err(e=e, m=f"Error getting food interactions for '{drug_name}'")
        return {"success": False, "error": str(e)}
    finally:
        session.close()


# ========================================================================
# SEARCH BY CATEGORY / INDICATION
# ========================================================================


def search_drugs_by_category(search_term: str, limit: int = 10) -> dict:
    """Search drugs by therapeutic category or indication using SQL LIKE."""
    session = get_session()
    try:
        term = search_term.lower().strip()
        pm.inf(f"Searching drugs by category/indication: {term}")

        # Search by category
        cat_drug_ids = (
            session.query(DrugCategory.drug_pk)
            .filter(DrugCategory.category_lower.contains(term))
            .distinct()
            .limit(limit)
            .all()
        )
        cat_ids = {row[0] for row in cat_drug_ids}

        # Search by indication
        ind_drugs = (
            session.query(Drug)
            .filter(func.lower(Drug.indication).contains(term))
            .limit(limit)
            .all()
        )
        ind_ids = {d.id for d in ind_drugs}

        all_ids = cat_ids | ind_ids
        if not all_ids:
            return {"success": True, "drugs": [], "count": 0}

        drugs = session.query(Drug).filter(Drug.id.in_(all_ids)).limit(limit).all()

        matches = []
        for d in drugs:
            cats = [c.category for c in d.categories][:3]
            matches.append({
                "name": d.name,
                "indication": (d.indication or "N/A")[:200],
                "categories": cats,
            })

        pm.suc(f"Found {len(matches)} drugs matching '{search_term}'")
        return {"success": True, "drugs": matches, "count": len(matches)}
    except Exception as e:
        pm.err(e=e, m=f"Error searching drugs by category '{search_term}'")
        return {"success": False, "error": str(e)}
    finally:
        session.close()


# ========================================================================
# ALTERNATIVE DRUG RECOMMENDATIONS
# ========================================================================


def get_alternative_drugs(drug_name: str, patient_medications: list[str] | None = None) -> dict:
    """Find alternative drugs by matching indication/categories, filtering out
    candidates that interact with the patient's current medications.
    """
    session = get_session()
    try:
        if patient_medications is None:
            patient_medications = []

        drug = _resolve_drug(session, drug_name)
        if not drug:
            return {"success": False, "error": f"Drug '{drug_name}' not found in database"}

        original_name = drug.name
        original_indication = drug.indication or ""
        original_categories = [c.category for c in drug.categories]

        pm.inf(f"Finding alternatives for '{original_name}'")

        # Collect candidate drug IDs from matching categories
        candidate_ids: set[int] = set()
        for cat in original_categories[:5]:
            cat_matches = (
                session.query(DrugCategory.drug_pk)
                .filter(DrugCategory.category_lower == cat.lower())
                .limit(20)
                .all()
            )
            for (pk,) in cat_matches:
                if pk != drug.id:
                    candidate_ids.add(pk)

        # Also search by indication keywords
        if original_indication and original_indication != "N/A":
            keywords = [w for w in original_indication.split() if len(w) > 4][:3]
            for kw in keywords:
                ind_matches = (
                    session.query(Drug.id)
                    .filter(func.lower(Drug.indication).contains(kw.lower()))
                    .limit(10)
                    .all()
                )
                for (pk,) in ind_matches:
                    if pk != drug.id:
                        candidate_ids.add(pk)

        if not candidate_ids:
            return {
                "success": True,
                "original_drug": original_name,
                "alternatives": [],
                "count": 0,
                "message": "No alternative drugs found in the same therapeutic category.",
            }

        # Load candidate drugs
        candidates = session.query(Drug).filter(Drug.id.in_(list(candidate_ids)[:30])).all()
        patient_meds = [m.strip() for m in patient_medications if m.strip()]

        safe_alternatives: list[dict] = []
        for candidate in candidates:
            has_conflict = False
            for patient_med in patient_meds:
                # Use the public function (opens its own session)
                interaction = check_drug_interaction(candidate.name, patient_med)
                if interaction.get("success") and interaction.get("interaction_found"):
                    has_conflict = True
                    pm.inf(f"Filtered out '{candidate.name}': interacts with {patient_med}")
                    break

            if not has_conflict:
                cand_groups = [g.group_name for g in candidate.groups]
                cand_cats = [c.category for c in candidate.categories]
                safe_alternatives.append({
                    "name": candidate.name,
                    "indication": candidate.indication or "N/A",
                    "categories": cand_cats,
                    "mechanism_of_action": candidate.mechanism_of_action or "N/A",
                    "groups": cand_groups,
                })

        # Sort: approved drugs first, then alphabetically
        safe_alternatives.sort(
            key=lambda d: (
                "approved" not in [g.lower() for g in d.get("groups", [])],
                d["name"],
            )
        )

        pm.suc(f"Found {len(safe_alternatives)} safe alternatives for '{original_name}'")
        return {
            "success": True,
            "original_drug": original_name,
            "original_indication": original_indication,
            "original_categories": original_categories,
            "alternatives": safe_alternatives[:10],
            "count": len(safe_alternatives[:10]),
            "total_candidates_checked": len(candidate_ids),
            "patient_medications_checked": patient_meds,
        }
    except Exception as e:
        pm.err(e=e, m=f"Error finding alternatives for '{drug_name}'")
        return {"success": False, "error": str(e)}
    finally:
        session.close()


# ========================================================================
# PRODUCT & REFERENCE QUERIES
# ========================================================================


def get_drug_products(drug_name: str) -> dict:
    """Return brand-name products for a drug."""
    session = get_session()
    try:
        drug = _resolve_drug(session, drug_name.strip())
        if not drug:
            return {"success": False, "error": f"Drug '{drug_name}' not found"}

        products = [
            {
                "product_name": p.product_name,
                "labeller": p.labeller,
                "dosage_form": p.dosage_form,
                "strength": p.strength,
                "route": p.route,
                "country": p.country,
                "generic": p.generic,
                "over_the_counter": p.over_the_counter,
                "approved": p.approved,
            }
            for p in drug.products
        ]
        return {"success": True, "drug_name": drug.name, "products": products, "count": len(products)}
    except Exception as e:
        pm.err(e=e, m=f"Error getting products for '{drug_name}'")
        return {"success": False, "error": str(e)}
    finally:
        session.close()


def get_drug_references(drug_name: str) -> dict:
    """Return general references (articles, textbooks, links) for a drug."""
    session = get_session()
    try:
        drug = _resolve_drug(session, drug_name.strip())
        if not drug:
            return {"success": False, "error": f"Drug '{drug_name}' not found"}

        refs = [
            {
                "ref_type": r.ref_type,
                "pubmed_id": r.pubmed_id,
                "isbn": r.isbn,
                "citation": r.citation,
                "title": r.title,
                "url": r.url,
                "ref_id": r.ref_id,
            }
            for r in drug.references
        ]
        return {"success": True, "drug_name": drug.name, "references": refs, "count": len(refs)}
    except Exception as e:
        pm.err(e=e, m=f"Error getting references for '{drug_name}'")
        return {"success": False, "error": str(e)}
    finally:
        session.close()


def search_by_product_name(product_name: str) -> dict:
    """Look up which drug(s) a commercial product/brand/mixture name belongs to.

    Searches across: products (FDA/DPD/EMA), international brands, and mixtures.
    """
    session = get_session()
    try:
        product_name = product_name.strip()
        term = product_name.lower()
        results: list[dict] = []
        seen_drugs: set[int] = set()

        def _add_drug(drug_pk: int):
            if drug_pk in seen_drugs:
                return
            seen_drugs.add(drug_pk)
            drug = session.query(Drug).filter(Drug.id == drug_pk).first()
            if drug:
                results.append({"drug_name": drug.name, "drug_id": drug.drug_id, "source": source})

        # 1. Products (exact then contains)
        source = "product"
        for prod in session.query(DrugProduct).filter(DrugProduct.product_name_lower == term).all():
            _add_drug(prod.drug_pk)
        if not results:
            for prod in session.query(DrugProduct).filter(DrugProduct.product_name_lower.contains(term)).limit(10).all():
                _add_drug(prod.drug_pk)

        # 2. International brands
        source = "international_brand"
        for brand in session.query(DrugInternationalBrand).filter(DrugInternationalBrand.brand_name_lower == term).all():
            _add_drug(brand.drug_pk)
        if not any(r["source"] == "international_brand" for r in results):
            for brand in session.query(DrugInternationalBrand).filter(DrugInternationalBrand.brand_name_lower.contains(term)).limit(10).all():
                _add_drug(brand.drug_pk)

        # 3. Mixtures
        source = "mixture"
        for mix in session.query(DrugMixture).filter(DrugMixture.mixture_name_lower == term).all():
            _add_drug(mix.drug_pk)
        if not any(r["source"] == "mixture" for r in results):
            for mix in session.query(DrugMixture).filter(DrugMixture.mixture_name_lower.contains(term)).limit(10).all():
                _add_drug(mix.drug_pk)

        if results:
            pm.suc(f"'{product_name}' maps to {len(results)} drug(s)")
        else:
            pm.inf(f"'{product_name}' not found in products/brands/mixtures")

        return {"success": True, "product_name": product_name, "drugs": results, "count": len(results)}
    except Exception as e:
        pm.err(e=e, m=f"Error searching by product name '{product_name}'")
        return {"success": False, "error": str(e)}
    finally:
        session.close()
