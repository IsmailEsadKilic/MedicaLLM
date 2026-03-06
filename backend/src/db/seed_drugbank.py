
#AIG
"""
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

from tqdm import tqdm
from xsdata.formats.dataclass.parsers import XmlParser



from drugbank_schema.drugbank import (  # noqa: E402
    Drugbank,
    DrugType,
    GroupType,
)
from src.db.client import dynamodb_client  # noqa: E402
from src import printmeup as pm  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

XML_DATA_PATH = os.path.join(Path(__file__).resolve().parent.parent, "data", "xml", "drugbank.xml")

DRUGS_TABLE = "Drugs"
INTERACTIONS_TABLE = "DrugInteractions"
FOOD_INTERACTIONS_TABLE = "DrugFoodInteractions"

# tqdm bar format shared by all seed stages
_BAR_FMT = "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_primary_id(drug: DrugType) -> str:
    """Return the primary DrugBank ID (e.g. DB00001) for a drug."""
    for dbid in drug.drugbank_id:
        if dbid.primary:
            return dbid.value
    # Fallback: first id in the list
    return drug.drugbank_id[0].value if drug.drugbank_id else "UNKNOWN"


def _safe_str(value: str | None, max_len: int = 0) -> str:
    """Return a non-None, optionally-truncated string safe for DynamoDB."""
    if value is None:
        return ""
    s = str(value).strip()
    if max_len and len(s) > max_len:
        return s[:max_len]
    return s


def _groups_list(drug: DrugType) -> list[str]:
    """Extract the list of group strings (approved, experimental …)."""
    if drug.groups is None:
        return []
    return [g.value for g in drug.groups.group if isinstance(g, GroupType)]


def _categories_list(drug: DrugType) -> list[str]:
    """Extract the list of therapeutic category names."""
    if drug.categories is None:
        return []
    return [
        c.category
        for c in drug.categories.category
        if c.category
    ]


def _synonyms_list(drug: DrugType) -> list[str]:
    """Extract unique synonym values."""
    if drug.synonyms is None:
        return []
    seen: set[str] = set()
    result: list[str] = []
    for syn in drug.synonyms.synonym:
        val = syn.value.strip()
        if val and val not in seen:
            seen.add(val)
            result.append(val)
    return result


def _product_names_list(drug: DrugType) -> list[dict]:
    """Extract unique product dicts (name, labeller, dosage_form, strength,
    route, country, generic, otc, approved) from a drug's products list.

    Only the *unique product names* are kept (de-duplicated by name).
    """
    if drug.products is None:
        return []
    seen: set[str] = set()
    result: list[dict] = []
    for prod in drug.products.product:
        name = _safe_str(prod.name)
        if not name or name in seen:
            continue
        seen.add(name)
        item: dict = {
            "product_name": name[:500],
            "labeller": _safe_str(prod.labeller, max_len=500),
            "dosage_form": _safe_str(prod.dosage_form, max_len=200),
            "strength": _safe_str(prod.strength, max_len=200),
            "route": _safe_str(prod.route, max_len=200),
            "country": prod.country.value if prod.country else "",
            "generic": prod.generic if prod.generic is not None else False,
            "over_the_counter": prod.over_the_counter if prod.over_the_counter is not None else False,
            "approved": prod.approved if prod.approved is not None else False,
        }
        # Strip empty strings
        item = {k: v for k, v in item.items() if v != ""}
        item["product_name"] = name  # always keep
        result.append(item)
    return result


# Maximum field lengths to stay well within DynamoDB's 400 KB item limit.
_MAX_LONG_TEXT  = 10_000   # description, indication, mechanism, etc.
_MAX_SHORT_TEXT = 1_000    # labeller, dosage_form, strength, route, citation …
_MAX_SYNONYMS   = 200      # synonym_names list on META


def _references_list(drug: DrugType) -> list[dict]:
    """Extract general references (articles, textbooks, links) as flat dicts.

    Each dict has at minimum ``ref_type`` and one of ``pubmed_id``/``isbn``/``url``
    plus ``citation``/``title``.
    """
    refs: list[dict] = []
    gr = drug.general_references
    if gr is None:
        return refs

    # --- Articles (PubMed) ------------------------------------------------
    if gr.articles:
        for art in gr.articles.article:
            item: dict = {"ref_type": "article"}
            if art.pubmed_id:
                item["pubmed_id"] = art.pubmed_id.strip()[:50]
            if art.citation:
                item["citation"] = art.citation.strip()[:_MAX_SHORT_TEXT]
            if art.ref_id:
                item["ref_id"] = art.ref_id.strip()[:50]
            # Only keep if we have *something* useful
            if "pubmed_id" in item or "citation" in item:
                refs.append(item)

    # --- Textbooks --------------------------------------------------------
    if gr.textbooks:
        for tb in gr.textbooks.textbook:
            item = {"ref_type": "textbook"}
            if tb.isbn:
                item["isbn"] = tb.isbn.strip()[:50]
            if tb.citation:
                item["citation"] = tb.citation.strip()[:_MAX_SHORT_TEXT]
            if tb.ref_id:
                item["ref_id"] = tb.ref_id.strip()[:50]
            if "isbn" in item or "citation" in item:
                refs.append(item)

    # --- Links ------------------------------------------------------------
    if gr.links:
        for lnk in gr.links.link:
            item = {"ref_type": "link"}
            if lnk.title:
                item["title"] = lnk.title.strip()[:_MAX_SHORT_TEXT]
            if lnk.url:
                item["url"] = lnk.url.strip()[:500]
            if lnk.ref_id:
                item["ref_id"] = lnk.ref_id.strip()[:50]
            if "title" in item or "url" in item:
                refs.append(item)

    return refs


# ---------------------------------------------------------------------------
# Table empty check
# ---------------------------------------------------------------------------

def _table_is_empty(table_name: str) -> bool:
    """Return True if the given DynamoDB table has zero items."""
    table = dynamodb_client.Table(table_name)  # type: ignore
    # Scan with Limit=1 is the cheapest way to check for any items.
    resp = table.scan(Limit=1, Select="COUNT")
    return resp.get("Count", 0) == 0


# ---------------------------------------------------------------------------
# Seed functions
# ---------------------------------------------------------------------------

def seed_drugs(drugs: list[DrugType]) -> dict[str, int]:
    """Write drug META, SYNONYM, PRODUCT and REF items to the Drugs table.

    Returns a dict with counts: ``meta``, ``synonyms``, ``products``, ``refs``.
    """
    table = dynamodb_client.Table(DRUGS_TABLE)  # type: ignore
    counts = {"meta": 0, "synonyms": 0, "products": 0, "product_lookups": 0, "refs": 0}

    with table.batch_writer() as batch:
        for drug in tqdm(drugs, desc="Drugs (meta+syn+prod+ref)", unit="drug",
                         bar_format=_BAR_FMT):
            if not drug.name:
                continue

            drug_name = drug.name.strip()
            drug_id = _get_primary_id(drug)
            groups = _groups_list(drug)
            categories = _categories_list(drug)
            synonyms = _synonyms_list(drug)
            products = _product_names_list(drug)
            references = _references_list(drug)

            # -- META item --------------------------------------------------
            item: dict = {
                "PK": f"DRUG#{drug_name}",
                "SK": "META",
                "name": drug_name,
                "name_lower": drug_name.lower(),
                "drug_id": drug_id,
                "description": _safe_str(drug.description, max_len=_MAX_LONG_TEXT),
                "indication": _safe_str(drug.indication, max_len=_MAX_LONG_TEXT),
                "mechanism_of_action": _safe_str(drug.mechanism_of_action, max_len=_MAX_LONG_TEXT),
                "pharmacodynamics": _safe_str(drug.pharmacodynamics, max_len=_MAX_LONG_TEXT),
                "toxicity": _safe_str(drug.toxicity, max_len=_MAX_LONG_TEXT),
                "metabolism": _safe_str(drug.metabolism, max_len=_MAX_LONG_TEXT),
                "absorption": _safe_str(drug.absorption, max_len=_MAX_LONG_TEXT),
                "half_life": _safe_str(drug.half_life, max_len=_MAX_SHORT_TEXT),
                "protein_binding": _safe_str(drug.protein_binding, max_len=_MAX_SHORT_TEXT),
                "route_of_elimination": _safe_str(drug.route_of_elimination, max_len=_MAX_LONG_TEXT),
                "cas_number": _safe_str(drug.cas_number),
                "unii": _safe_str(drug.unii),
                "state": drug.state.value if drug.state else "",
                "groups": groups,
                "categories": categories,
                # Denormalized synonym list capped to avoid hitting 400 KB item limit.
                # product_names is intentionally omitted — use PRODUCT# items instead.
                "synonym_names": synonyms[:_MAX_SYNONYMS] if synonyms else [],
            }

            # DynamoDB does not allow empty string values in non-key attributes
            # when using the resource API; strip them out.
            item = {k: v for k, v in item.items() if v != "" and v != []}
            # Re-add keys (they are always required)
            item.setdefault("PK", f"DRUG#{drug_name}")
            item.setdefault("SK", "META")

            batch.put_item(Item=item)
            counts["meta"] += 1

            # -- SYNONYM items (lookup by synonym name → canonical name) ----
            for synonym in synonyms:
                if synonym == drug_name:
                    continue  # skip self
                syn_item = {
                    "PK": f"DRUG#{synonym}",
                    "SK": "SYNONYM",
                    "points_to": drug_name,
                    "drug_id": drug_id,
                }
                batch.put_item(Item=syn_item)
                counts["synonyms"] += 1

            # -- PRODUCT items (per-drug detail rows) -----------------------
            for idx, prod in enumerate(products):
                prod_item = {
                    "PK": f"DRUG#{drug_name}",
                    "SK": f"PRODUCT#{idx}",
                    **prod,
                }
                batch.put_item(Item=prod_item)
                counts["products"] += 1

                # Reverse-lookup: product name → drug name
                lookup_item = {
                    "PK": f"PRODUCT#{prod['product_name']}",
                    "SK": f"DRUG#{drug_name}",
                    "drug_name": drug_name,
                    "drug_id": drug_id,
                }
                batch.put_item(Item=lookup_item)
                counts["product_lookups"] += 1

            # -- REFERENCE items (articles, textbooks, links) ---------------
            for idx, ref in enumerate(references):
                ref_item = {
                    "PK": f"DRUG#{drug_name}",
                    "SK": f"REF#{idx}",
                    **ref,
                }
                batch.put_item(Item=ref_item)
                counts["refs"] += 1

    return counts


def seed_drug_interactions(drugs: list[DrugType]) -> int:
    """Write drug-drug interaction items to the DrugInteractions table.

    Each interaction is stored once per direction discovered in the XML
    (DrugBank already lists A→B only; we store with GSI for reverse lookup).

    Returns the number of interaction items written.
    """
    table = dynamodb_client.Table(INTERACTIONS_TABLE)  # type: ignore
    written = 0

    with table.batch_writer() as batch:
        for drug in tqdm(drugs, desc="Drug-drug interactions", unit="drug",
                         bar_format=_BAR_FMT):
            if not drug.name or drug.drug_interactions is None:
                continue

            drug_name = drug.name.strip()
            drug_id = _get_primary_id(drug)

            for interaction in drug.drug_interactions.drug_interaction:
                other_name = interaction.name.strip() if interaction.name else ""
                other_id = interaction.drugbank_id.value if interaction.drugbank_id else ""
                description = _safe_str(interaction.description)

                if not other_name:
                    continue

                item = {
                    "PK": f"DRUG#{drug_name}",
                    "SK": f"INTERACTS#{other_name}",
                    "drug1_name": drug_name,
                    "drug1_id": drug_id,
                    "drug2_name": other_name,
                    "drug2_id": other_id,
                    "description": description,
                    # GSI keys for reverse lookup
                    "GSI_PK": f"DRUG#{other_name}",
                    "GSI_SK": f"INTERACTS#{drug_name}",
                }
                item = {k: v for k, v in item.items() if v != ""}
                item.setdefault("PK", f"DRUG#{drug_name}")
                item.setdefault("SK", f"INTERACTS#{other_name}")

                batch.put_item(Item=item)
                written += 1

    return written


def seed_food_interactions(drugs: list[DrugType]) -> int:
    """Write drug-food interaction items to the DrugFoodInteractions table.

    Returns the number of food interaction items written.
    """
    table = dynamodb_client.Table(FOOD_INTERACTIONS_TABLE)  # type: ignore
    written = 0

    with table.batch_writer() as batch:
        for drug in tqdm(drugs, desc="Drug-food interactions", unit="drug",
                         bar_format=_BAR_FMT):
            if not drug.name or drug.food_interactions is None:
                continue

            drug_name = drug.name.strip()

            for idx, food_text in enumerate(drug.food_interactions.food_interaction):
                if not food_text or not food_text.strip():
                    continue

                item = {
                    "PK": f"DRUG#{drug_name}",
                    "SK": f"FOOD#{idx}",
                    "interaction": food_text.strip(),
                }
                batch.put_item(Item=item)
                written += 1

    return written


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> None:

    xml_path = Path("data/xml/drugbank.xml").resolve()
    if not xml_path.exists():
        pm.err(m=f"XML file not found: {xml_path}")
        sys.exit(1)

    pm.inf(f"DrugBank XML path: {xml_path}")

    # ---- Check if already seeded ----------------------------------------
    try:
        if not _table_is_empty(DRUGS_TABLE):
            pm.suc("Drugs table already contains data — skipping seed. Use --force to re-seed.")
            return
            # pm.deb("Continuing with seeding anyway for testing purposes TODO: (comment out this line to enable early return).")
    except Exception as e:
        pm.war(f"Could not check Drugs table (will attempt seed anyway): {e}")

    # ---- Parse XML using xsdata -----------------------------------------
    pm.inf("Parsing DrugBank XML (this may take a while for large files) …")
    t0 = time.time()

    xml_parser = XmlParser()
    drugbank: Drugbank = xml_parser.parse(str(xml_path), Drugbank)

    num_drugs = len(drugbank.drug)
    elapsed = time.time() - t0
    pm.suc(f"Parsed {num_drugs} drugs in {elapsed:.1f}s")

    if num_drugs == 0:
        pm.war("No drugs found in XML — nothing to seed.")
        return

    # ---- Seed tables -----------------------------------------------------
    pm.inf(f"Seeding {DRUGS_TABLE} table (meta + synonyms + products + references) …")
    t1 = time.time()
    drug_counts = seed_drugs(drugbank.drug)
    pm.suc(
        f"  Wrote {drug_counts['meta']} META, {drug_counts['synonyms']} synonyms, "
        f"{drug_counts['products']} products, {drug_counts['product_lookups']} product lookups, "
        f"{drug_counts['refs']} references in {time.time() - t1:.1f}s"
    )

    pm.inf(f"Seeding {INTERACTIONS_TABLE} table …")
    t2 = time.time()
    n_interactions = seed_drug_interactions(drugbank.drug)
    pm.suc(f"  Wrote {n_interactions} drug-drug interaction items in {time.time() - t2:.1f}s")

    pm.inf(f"Seeding {FOOD_INTERACTIONS_TABLE} table …")
    t3 = time.time()
    n_food = seed_food_interactions(drugbank.drug)
    pm.suc(f"  Wrote {n_food} drug-food interaction items in {time.time() - t3:.1f}s")

    total_elapsed = time.time() - t0
    pm.suc(
        f"Seeding complete in {total_elapsed:.1f}s — "
        f"{drug_counts['meta']} drugs, {drug_counts['synonyms']} synonyms, "
        f"{drug_counts['products']} products, {drug_counts['refs']} references, "
        f"{n_interactions} drug interactions, {n_food} food interactions"
    )


if __name__ == "__main__":
    main()