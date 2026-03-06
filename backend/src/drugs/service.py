from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
import re

from ..db.client import dynamodb_client
from .. import printmeup as pm


DRUGS_TABLE = "Drugs"
INTERACTIONS_TABLE = "DrugInteractions"
FOOD_INTERACTIONS_TABLE = "DrugFoodInteractions"


# ========================================================================
# INTERACTION SEVERITY CLASSIFICATION
# ========================================================================

# Keywords / phrases mapped to severity tiers.  The classifier iterates from
# the most severe tier downward and returns the first match.  This is a
# heuristic based on common DrugBank-style descriptions; it intentionally
# over-classifies rather than under-classifies to err on the side of caution.

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
    """Classify a drug-drug interaction description into a severity tier.

    Returns one of: ``"contraindicated"``, ``"major"``, ``"moderate"``, ``"minor"``.
    """
    if not description:
        return "moderate"  # default when no description available
    if _SEVERITY_CONTRAINDICATED.search(description):
        return "contraindicated"
    if _SEVERITY_MAJOR.search(description):
        return "major"
    if _SEVERITY_MODERATE.search(description):
        return "moderate"
    return "minor"


def _drugs_table():
    return dynamodb_client.Table(DRUGS_TABLE)  # type: ignore


def _interactions_table():
    return dynamodb_client.Table(INTERACTIONS_TABLE)  # type: ignore


def _food_table():
    return dynamodb_client.Table(FOOD_INTERACTIONS_TABLE)  # type: ignore


# ========================================================================
# DRUG INFORMATION
# ========================================================================


def resolve_drug_name(drug_name: str) -> str:
    """Resolve a drug name (synonym or actual) to its canonical name."""
    try:
        pm.inf(f"Resolving drug name: '{drug_name}'")
        for name_variant in [drug_name.title(), drug_name, drug_name.upper()]:
            # Check synonym
            syn_resp = _drugs_table().get_item(
                Key={"PK": f"DRUG#{name_variant}", "SK": "SYNONYM"}
            )
            if "Item" in syn_resp and "points_to" in syn_resp["Item"]:
                resolved = syn_resp["Item"]["points_to"]
                pm.suc(f"Synonym resolved: '{name_variant}' -> '{resolved}'")
                return resolved

            # Check direct drug
            meta_resp = _drugs_table().get_item(
                Key={"PK": f"DRUG#{name_variant}", "SK": "META"}
            )
            if "Item" in meta_resp:
                resolved = meta_resp["Item"].get("name", name_variant)
                pm.suc(f"Drug found: '{name_variant}' -> '{resolved}'")
                return resolved

        pm.war(f"Drug not found in DB, using title case: '{drug_name.title()}'")
        return drug_name.title()
    except Exception as e:
        pm.err(e=e, m=f"Error resolving drug name '{drug_name}'")
        return drug_name.title()


def get_drug_info(drug_name: str) -> dict:
    """Get detailed drug information. Supports synonym resolution."""
    try:
        drug_name = drug_name.strip()

        for name_variant in [drug_name, drug_name.title(), drug_name.upper(), drug_name.lower()]:
            # Direct lookup
            response = _drugs_table().get_item(
                Key={"PK": f"DRUG#{name_variant}", "SK": "META"}
            )
            if "Item" in response:
                drug = response["Item"]
                pm.inf(f"Found drug: {drug.get('name')}")
                return _format_drug_result(drug, drug_name)

            # Synonym lookup
            synonym_response = _drugs_table().get_item(
                Key={"PK": f"DRUG#{name_variant}", "SK": "SYNONYM"}
            )
            if "Item" in synonym_response and "points_to" in synonym_response["Item"]:
                actual_name = synonym_response["Item"]["points_to"]
                pm.inf(f"'{name_variant}' is a synonym for '{actual_name}'")
                response = _drugs_table().get_item(
                    Key={"PK": f"DRUG#{actual_name}", "SK": "META"}
                )
                if "Item" in response:
                    drug = response["Item"]
                    result = _format_drug_result(drug, drug_name)
                    result["is_synonym"] = True
                    result["queried_name"] = drug_name
                    result["actual_name"] = actual_name
                    return result

        pm.war(f"Drug '{drug_name}' not found")
        return {"success": False, "error": f"Drug '{drug_name}' not found in database"}
    except Exception as e:
        pm.err(e=e, m=f"Error getting drug info for '{drug_name}'")
        return {"success": False, "error": str(e)}


def _format_drug_result(drug: dict, queried_name: str) -> dict:
    return {
        "success": True,
        "drug_name": drug.get("name"),
        "drug_id": drug.get("drug_id"),
        "description": drug.get("description", "N/A"),
        "indication": drug.get("indication", "N/A"),
        "mechanism_of_action": drug.get("mechanism_of_action", "N/A"),
        "pharmacodynamics": drug.get("pharmacodynamics", "N/A"),
        "toxicity": drug.get("toxicity", "N/A"),
        "metabolism": drug.get("metabolism", "N/A"),
        "absorption": drug.get("absorption", "N/A"),
        "half_life": drug.get("half_life", "N/A"),
        "protein_binding": drug.get("protein_binding", "N/A"),
        "route_of_elimination": drug.get("route_of_elimination", "N/A"),
        "groups": drug.get("groups", []),
        "categories": drug.get("categories", []),
        "cas_number": drug.get("cas_number", "N/A"),
        "unii": drug.get("unii", "N/A"),
        "state": drug.get("state", "N/A"),
        "synonym_names": drug.get("synonym_names", []),
        # product_names is not stored on META to stay within DynamoDB's 400 KB
        # item limit — call get_drug_products() for the full product list.
        "product_names": [],
    }


# ========================================================================
# DRUG SEARCH
# ========================================================================


def search_drugs(query: str) -> dict:
    """Search drugs by name or synonym (scan-based search)."""
    try:
        search_term = query.lower().strip()

        main_result = _drugs_table().scan(
            FilterExpression="SK = :meta AND (begins_with(name_lower, :search) OR contains(name_lower, :search))",
            ExpressionAttributeValues={":meta": "META", ":search": search_term},
            Limit=50,
        )

        drug_map = {}
        for item in main_result.get("Items", []):
            drug_map[item["name"]] = {
                "name": item["name"],
                "drug_id": item.get("drug_id"),
                "name_lower": item.get("name_lower", item["name"].lower()),
            }

        # Also search synonyms
        syn_result = _drugs_table().scan(
            FilterExpression="SK = :syn AND contains(PK, :search_upper)",
            ExpressionAttributeValues={":syn": "SYNONYM", ":search_upper": query.strip()},
            Limit=50,
        )
        for item in syn_result.get("Items", []):
            points_to = item.get("points_to")
            if points_to and points_to not in drug_map:
                drug_map[points_to] = {
                    "name": points_to,
                    "drug_id": item.get("drug_id"),
                    "name_lower": points_to.lower(),
                }

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


# ========================================================================
# DRUG INTERACTIONS
# ========================================================================


def check_drug_interaction(drug1: str, drug2: str) -> dict:
    """Check if two drugs interact. Resolves synonyms and tries both directions."""
    try:
        drug1 = drug1.strip()
        drug2 = drug2.strip()

        resolved1 = resolve_drug_name(drug1)
        resolved2 = resolve_drug_name(drug2)

        pm.inf(f"Checking interaction: '{resolved1}' + '{resolved2}'")

        for d1, d2 in [(resolved1, resolved2), (resolved2, resolved1)]:
            response = _interactions_table().get_item(
                Key={"PK": f"DRUG#{d1}", "SK": f"INTERACTS#{d2}"}
            )
            if "Item" in response:
                interaction = response["Item"]
                description = interaction.get("description", "No description available")
                severity = classify_interaction_severity(description)
                pm.suc(f"Interaction found: {d1} + {d2} (severity: {severity})")
                return {
                    "success": True,
                    "interaction_found": True,
                    "drug1": interaction.get("drug1_name"),
                    "drug2": interaction.get("drug2_name"),
                    "drug1_id": interaction.get("drug1_id"),
                    "drug2_id": interaction.get("drug2_id"),
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


# ========================================================================
# DRUG-FOOD INTERACTIONS
# ========================================================================


def get_drug_food_interactions(drug_name: str) -> dict:
    """Get food interactions for a specific drug."""
    try:
        drug_name = drug_name.strip()
        resolved_name = resolve_drug_name(drug_name)

        pm.inf(f"Getting food interactions for: {resolved_name}")

        for name_variant in [resolved_name, resolved_name.title()]:
            response = _food_table().query(
                KeyConditionExpression=Key("PK").eq(f"DRUG#{name_variant}")
            )
            if response["Items"]:
                interactions = [item["interaction"] for item in response["Items"]]
                pm.suc(f"Found {len(interactions)} food interactions for {name_variant}")
                return {
                    "success": True,
                    "drug_name": name_variant,
                    "interactions": interactions,
                    "count": len(interactions),
                }

        pm.inf(f"No food interactions found for {resolved_name}")
        return {
            "success": True,
            "drug_name": resolved_name,
            "interactions": [],
            "count": 0,
            "message": f"No food interactions documented for {resolved_name}",
        }
    except Exception as e:
        pm.err(e=e, m=f"Error getting food interactions for '{drug_name}'")
        return {"success": False, "error": str(e)}


# ========================================================================
# SEARCH BY CATEGORY / INDICATION
# ========================================================================


def search_drugs_by_category(search_term: str, limit: int = 10) -> dict:
    """Search drugs by therapeutic category or indication."""
    try:
        search_term_lower = search_term.lower()
        pm.inf(f"Searching drugs by category/indication: {search_term_lower}")

        response = _drugs_table().scan(
            FilterExpression="attribute_exists(categories) OR attribute_exists(indication)"
        )

        matches = []
        for item in response["Items"]:
            if item.get("SK") != "META":
                continue

            categories = [c.lower() for c in item.get("categories", [])]
            indication = item.get("indication", "").lower()

            if any(search_term_lower in cat for cat in categories) or search_term_lower in indication:
                matches.append(
                    {
                        "name": item.get("name"),
                        "indication": item.get("indication", "N/A")[:200],
                        "categories": item.get("categories", [])[:3],
                    }
                )
                if len(matches) >= limit:
                    break

        pm.suc(f"Found {len(matches)} drugs matching '{search_term}'")
        return {"success": True, "drugs": matches, "count": len(matches)}
    except Exception as e:
        pm.err(e=e, m=f"Error searching drugs by category '{search_term}'")
        return {"success": False, "error": str(e)}


# ========================================================================
# ALTERNATIVE DRUG RECOMMENDATIONS (O9)
# ========================================================================


def get_alternative_drugs(drug_name: str, patient_medications: list[str] | None = None) -> dict:
    """
    Find alternative drugs for a given drug by matching its indication/categories,
    then filtering out candidates that interact with the patient's current medications.

    Returns a ranked list of safe alternatives with their indications.
    """
    try:
        if patient_medications is None:
            patient_medications = []

        # Step 1: Look up the original drug's indication and categories
        drug_info = get_drug_info(drug_name)
        if not drug_info.get("success"):
            return {
                "success": False,
                "error": f"Drug '{drug_name}' not found in database",
            }

        original_name = drug_info["drug_name"]
        original_indication = drug_info.get("indication", "")
        original_categories = drug_info.get("categories", [])

        pm.inf(
            f"Finding alternatives for '{original_name}' "
            f"(indication: {original_indication[:80] if original_indication else 'N/A'}, "
            f"categories: {original_categories[:3]})"
        )
        
        pm.deb("this feature times out the database scan. skipping actual search and returning empty list for now.")
        return {
            "success": False,
            "original_drug": original_name,
            "original_indication": original_indication,
            "original_categories": original_categories,
            "alternatives": [],
            "count": 0,
            "total_candidates_checked": 0,
            "patient_medications_checked": patient_medications,
            "message": "Alternative search is currently disabled to avoid timeouts.",
        }

        # Step 2: Collect candidate drugs from matching categories and indications
        candidate_names: set[str] = set()

        for cat in original_categories[:5]:
            result = search_drugs_by_category(cat, limit=20)
            for d in result.get("drugs", []):
                name = d.get("name")
                if name and name.lower() != original_name.lower():
                    candidate_names.add(name)

        # Also search by the first meaningful words of the indication
        if original_indication and original_indication != "N/A":
            keywords = [w for w in original_indication.split() if len(w) > 4][:3]
            for kw in keywords:
                result = search_drugs_by_category(kw, limit=10)
                for d in result.get("drugs", []):
                    name = d.get("name")
                    if name and name.lower() != original_name.lower():
                        candidate_names.add(name)

        if not candidate_names:
            return {
                "success": True,
                "original_drug": original_name,
                "alternatives": [],
                "count": 0,
                "message": "No alternative drugs found in the same therapeutic category.",
            }

        # Step 3: Filter candidates that interact with any of the patient's medications
        safe_alternatives: list[dict] = []
        patient_meds = [m.strip() for m in patient_medications if m.strip()]

        for candidate in list(candidate_names)[:30]:
            has_conflict = False
            conflict_description = ""

            for patient_med in patient_meds:
                interaction = check_drug_interaction(candidate, patient_med)
                if interaction.get("success") and interaction.get("interaction_found"):
                    has_conflict = True
                    conflict_description = (
                        f"Interacts with {patient_med}: "
                        f"{interaction.get('description', '')[:120]}"
                    )
                    break

            if not has_conflict:
                # Fetch full info for display
                info = get_drug_info(candidate)
                if info.get("success"):
                    safe_alternatives.append(
                        {
                            "name": info["drug_name"],
                            "indication": info.get("indication", "N/A"),
                            "categories": info.get("categories", []),
                            "mechanism_of_action": info.get("mechanism_of_action", "N/A"),
                            "groups": info.get("groups", []),
                        }
                    )
            else:
                pm.inf(f"Filtered out '{candidate}': {conflict_description}")

        # Sort: approved drugs first, then alphabetically
        safe_alternatives.sort(
            key=lambda d: (
                "approved" not in [g.lower() for g in d.get("groups", [])],
                d["name"],
            )
        )

        pm.suc(
            f"Found {len(safe_alternatives)} safe alternatives for '{original_name}' "
            f"(checked {len(candidate_names)} candidates, {len(patient_meds)} patient meds)"
        )

        return {
            "success": True,
            "original_drug": original_name,
            "original_indication": original_indication,
            "original_categories": original_categories,
            "alternatives": safe_alternatives[:10],
            "count": len(safe_alternatives[:10]),
            "total_candidates_checked": len(candidate_names),
            "patient_medications_checked": patient_meds,
        }

    except Exception as e:
        pm.err(e=e, m=f"Error finding alternatives for '{drug_name}'")
        return {"success": False, "error": str(e)}


# ========================================================================
# PRODUCT & REFERENCE QUERIES
# ========================================================================


def get_drug_products(drug_name: str) -> dict:
    """Return the product (brand-name) items for a drug."""
    try:
        drug_name = drug_name.strip()
        resolved = resolve_drug_name(drug_name)

        response = _drugs_table().query(
            KeyConditionExpression=Key("PK").eq(f"DRUG#{resolved}")
            & Key("SK").begins_with("PRODUCT#"),
        )
        products = [
            {k: v for k, v in item.items() if k not in ("PK", "SK")}
            for item in response.get("Items", [])
        ]
        return {"success": True, "drug_name": resolved, "products": products, "count": len(products)}
    except Exception as e:
        pm.err(e=e, m=f"Error getting products for '{drug_name}'")
        return {"success": False, "error": str(e)}


def get_drug_references(drug_name: str) -> dict:
    """Return general-reference items (articles, textbooks, links) for a drug."""
    try:
        drug_name = drug_name.strip()
        resolved = resolve_drug_name(drug_name)

        response = _drugs_table().query(
            KeyConditionExpression=Key("PK").eq(f"DRUG#{resolved}")
            & Key("SK").begins_with("REF#"),
        )
        refs = [
            {k: v for k, v in item.items() if k not in ("PK", "SK")}
            for item in response.get("Items", [])
        ]
        return {"success": True, "drug_name": resolved, "references": refs, "count": len(refs)}
    except Exception as e:
        pm.err(e=e, m=f"Error getting references for '{drug_name}'")
        return {"success": False, "error": str(e)}


def search_by_product_name(product_name: str) -> dict:
    """Look up which drug(s) a commercial product name belongs to.

    Uses the ``PRODUCT#<product_name>`` → ``DRUG#<drug_name>`` reverse-lookup
    items written by the seed script.
    """
    try:
        product_name = product_name.strip()
        results: list[dict] = []

        for variant in [product_name, product_name.title(), product_name.upper()]:
            response = _drugs_table().query(
                KeyConditionExpression=Key("PK").eq(f"PRODUCT#{variant}"),
            )
            for item in response.get("Items", []):
                results.append({
                    "drug_name": item.get("drug_name"),
                    "drug_id": item.get("drug_id"),
                })
            if results:
                break

        if results:
            pm.suc(f"Product '{product_name}' maps to {len(results)} drug(s)")
        else:
            pm.inf(f"Product '{product_name}' not found in reverse-lookup")

        return {"success": True, "product_name": product_name, "drugs": results, "count": len(results)}
    except Exception as e:
        pm.err(e=e, m=f"Error searching by product name '{product_name}'")
        return {"success": False, "error": str(e)}
