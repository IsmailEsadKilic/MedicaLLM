from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

from ..db.client import dynamodb_client
from .. import printmeup as pm


DRUGS_TABLE = "Drugs"
INTERACTIONS_TABLE = "DrugInteractions"
FOOD_INTERACTIONS_TABLE = "DrugFoodInteractions"


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
                pm.suc(f"Interaction found: {d1} + {d2}")
                return {
                    "success": True,
                    "interaction_found": True,
                    "drug1": interaction.get("drug1_name"),
                    "drug2": interaction.get("drug2_name"),
                    "drug1_id": interaction.get("drug1_id"),
                    "drug2_id": interaction.get("drug2_id"),
                    "description": interaction.get("description", "No description available"),
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
