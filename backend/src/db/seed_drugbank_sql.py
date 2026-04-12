"""
Seed the PostgreSQL drug catalog from DrugBank XML — comprehensive extraction.

Captures ALL valuable data from the XML: drugs, synonyms, groups, categories,
products, references, interactions, food interactions, classifications, dosages,
international brands, mixtures, prices, ATC codes, external identifiers,
patents, targets, enzymes, carriers, transporters, affected organisms, pathways.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

from tqdm import tqdm
from xsdata.formats.dataclass.parsers import XmlParser

from drugbank_schema.drugbank import (
    Drugbank, DrugType, GroupType, KnownActionType,
)
from src.db.sql_client import get_engine, get_session, init_sql_db
from src.db.sql_models import (
    Base, Drug, DrugSynonym, DrugGroup, DrugCategory, DrugProduct,
    DrugReference, DrugInteraction, DrugFoodInteraction,
    DrugClassification, DrugDosage, DrugInternationalBrand, DrugMixture,
    DrugPrice, DrugAtcCode, DrugExternalIdentifier, DrugPatent,
    DrugTarget, DrugEnzyme, DrugCarrier, DrugTransporter,
    DrugAffectedOrganism, DrugPathway,
)
from src import printmeup as pm

_BAR_FMT = "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
_MAX_LONG_TEXT = 10_000
_MAX_SHORT_TEXT = 1_000
_MAX_SYNONYMS = 200


def _get_primary_id(drug: DrugType) -> str:
    for dbid in drug.drugbank_id:
        if dbid.primary:
            return dbid.value
    return drug.drugbank_id[0].value if drug.drugbank_id else "UNKNOWN"


def _safe_str(value, max_len: int = 0) -> str:
    if value is None:
        return ""
    s = str(value).strip()
    if max_len and len(s) > max_len:
        return s[:max_len]
    return s


def _actions_str(actions_list) -> str:
    """Extract action strings from an ActionListType."""
    if actions_list is None:
        return ""
    return ", ".join(a for a in actions_list.action if a)


def _known_action_str(ka) -> str:
    if ka is None:
        return ""
    return ka.value if isinstance(ka, KnownActionType) else str(ka)


def seed_all(drugs: list[DrugType]) -> dict[str, int]:
    """Seed all drug data into SQLite. Returns counts per entity type."""
    session = get_session()
    counts = {
        "drugs": 0, "synonyms": 0, "groups": 0, "categories": 0,
        "products": 0, "references": 0, "interactions": 0,
        "food_interactions": 0, "classifications": 0, "dosages": 0,
        "international_brands": 0, "mixtures": 0, "prices": 0,
        "atc_codes": 0, "external_ids": 0, "patents": 0,
        "targets": 0, "enzymes": 0, "carriers": 0, "transporters": 0,
        "affected_organisms": 0, "pathways": 0,
    }

    drug_map: dict[str, Drug] = {}

    try:
        # ── Phase 1: drugs + all related entities ─────────────────────────
        for dx in tqdm(drugs, desc="Drugs", unit="drug", bar_format=_BAR_FMT):
            if not dx.name:
                continue

            drug_name = dx.name.strip()
            drug_id = _get_primary_id(dx)

            drug_obj = Drug(
                drug_id=drug_id,
                name=drug_name,
                name_lower=drug_name.lower(),
                drug_type=dx.type_value.value if dx.type_value else "",
                description=_safe_str(dx.description, _MAX_LONG_TEXT),
                indication=_safe_str(dx.indication, _MAX_LONG_TEXT),
                mechanism_of_action=_safe_str(dx.mechanism_of_action, _MAX_LONG_TEXT),
                pharmacodynamics=_safe_str(dx.pharmacodynamics, _MAX_LONG_TEXT),
                toxicity=_safe_str(dx.toxicity, _MAX_LONG_TEXT),
                metabolism=_safe_str(dx.metabolism, _MAX_LONG_TEXT),
                absorption=_safe_str(dx.absorption, _MAX_LONG_TEXT),
                half_life=_safe_str(dx.half_life, _MAX_SHORT_TEXT),
                protein_binding=_safe_str(dx.protein_binding, _MAX_SHORT_TEXT),
                route_of_elimination=_safe_str(dx.route_of_elimination, _MAX_LONG_TEXT),
                volume_of_distribution=_safe_str(dx.volume_of_distribution, _MAX_SHORT_TEXT),
                clearance=_safe_str(dx.clearance, _MAX_SHORT_TEXT),
                cas_number=_safe_str(dx.cas_number),
                unii=_safe_str(dx.unii),
                state=dx.state.value if dx.state else "",
                average_mass=dx.average_mass,
                monoisotopic_mass=dx.monoisotopic_mass,
                synthesis_reference=_safe_str(dx.synthesis_reference, _MAX_SHORT_TEXT),
                fda_label=_safe_str(dx.fda_label, 500),
                msds=_safe_str(dx.msds, 500),
                created_date=str(dx.created) if dx.created else "",
                updated_date=str(dx.updated) if dx.updated else "",
            )
            session.add(drug_obj)
            drug_map[drug_name] = drug_obj
            counts["drugs"] += 1

            # ── Synonyms ──────────────────────────────────────────────────
            if dx.synonyms:
                seen_syn: set[str] = set()
                for syn in dx.synonyms.synonym:
                    val = syn.value.strip()
                    if val and val not in seen_syn and val != drug_name:
                        seen_syn.add(val)
                        session.add(DrugSynonym(drug=drug_obj, synonym=val, synonym_lower=val.lower()))
                        counts["synonyms"] += 1
                        if len(seen_syn) >= _MAX_SYNONYMS:
                            break

            # ── Groups ────────────────────────────────────────────────────
            if dx.groups:
                for g in dx.groups.group:
                    if isinstance(g, GroupType):
                        session.add(DrugGroup(drug=drug_obj, group_name=g.value))
                        counts["groups"] += 1

            # ── Categories ────────────────────────────────────────────────
            if dx.categories:
                for cat in dx.categories.category:
                    if cat.category:
                        session.add(DrugCategory(drug=drug_obj, category=cat.category, category_lower=cat.category.lower()))
                        counts["categories"] += 1

            # ── Classification ────────────────────────────────────────────
            if dx.classification:
                c = dx.classification
                session.add(DrugClassification(
                    drug=drug_obj,
                    description=_safe_str(c.description, 500),
                    direct_parent=_safe_str(c.direct_parent, 500),
                    kingdom=_safe_str(c.kingdom, 200),
                    superclass=_safe_str(c.superclass, 200),
                    class_name=_safe_str(c.class_value, 200),
                    subclass=_safe_str(c.subclass, 200),
                ))
                counts["classifications"] += 1

            # ── Products ──────────────────────────────────────────────────
            if dx.products:
                seen_prod: set[str] = set()
                for prod in dx.products.product:
                    pname = _safe_str(prod.name, 500)
                    if not pname or pname in seen_prod:
                        continue
                    seen_prod.add(pname)
                    session.add(DrugProduct(
                        drug=drug_obj,
                        product_name=pname,
                        product_name_lower=pname.lower(),
                        labeller=_safe_str(prod.labeller, 500),
                        ndc_id=_safe_str(prod.ndc_id, 100),
                        ndc_product_code=_safe_str(prod.ndc_product_code, 100),
                        dpd_id=_safe_str(prod.dpd_id, 100),
                        ema_product_code=_safe_str(prod.ema_product_code, 100),
                        ema_ma_number=_safe_str(prod.ema_ma_number, 100),
                        fda_application_number=_safe_str(prod.fda_application_number, 100),
                        dosage_form=_safe_str(prod.dosage_form, 200),
                        strength=_safe_str(prod.strength, 200),
                        route=_safe_str(prod.route, 200),
                        country=prod.country.value if prod.country else "",
                        source=prod.source.value if prod.source else "",
                        generic=prod.generic if prod.generic is not None else False,
                        over_the_counter=prod.over_the_counter if prod.over_the_counter is not None else False,
                        approved=prod.approved if prod.approved is not None else False,
                        started_marketing_on=_safe_str(prod.started_marketing_on, 20),
                        ended_marketing_on=_safe_str(prod.ended_marketing_on, 20),
                    ))
                    counts["products"] += 1

            # ── Dosages ───────────────────────────────────────────────────
            if dx.dosages:
                for dos in dx.dosages.dosage:
                    session.add(DrugDosage(
                        drug=drug_obj,
                        form=_safe_str(dos.form, 200),
                        route=_safe_str(dos.route, 200),
                        strength=_safe_str(dos.strength, 200),
                    ))
                    counts["dosages"] += 1

            # ── International Brands ──────────────────────────────────────
            if dx.international_brands:
                for ib in dx.international_brands.international_brand:
                    bname = _safe_str(ib.name, 500)
                    if bname:
                        session.add(DrugInternationalBrand(
                            drug=drug_obj,
                            brand_name=bname,
                            brand_name_lower=bname.lower(),
                            company=_safe_str(ib.company, 500),
                        ))
                        counts["international_brands"] += 1

            # ── Mixtures ──────────────────────────────────────────────────
            if dx.mixtures:
                for mx in dx.mixtures.mixture:
                    mname = _safe_str(mx.name, 500)
                    if mname:
                        session.add(DrugMixture(
                            drug=drug_obj,
                            mixture_name=mname,
                            mixture_name_lower=mname.lower(),
                            ingredients=_safe_str(mx.ingredients, _MAX_LONG_TEXT),
                            supplemental_ingredients=_safe_str(mx.supplemental_ingredients, _MAX_LONG_TEXT),
                        ))
                        counts["mixtures"] += 1

            # ── Prices ────────────────────────────────────────────────────
            if dx.prices:
                for pr in dx.prices.price:
                    session.add(DrugPrice(
                        drug=drug_obj,
                        description=_safe_str(pr.description, 500),
                        cost=pr.cost.value if pr.cost else "",
                        currency=pr.cost.currency if pr.cost and pr.cost.currency else "",
                        unit=_safe_str(pr.unit, 50),
                    ))
                    counts["prices"] += 1

            # ── ATC Codes ─────────────────────────────────────────────────
            if dx.atc_codes:
                for atc in dx.atc_codes.atc_code:
                    if atc.code:
                        session.add(DrugAtcCode(drug=drug_obj, code=atc.code))
                        counts["atc_codes"] += 1

            # ── External Identifiers ──────────────────────────────────────
            if dx.external_identifiers:
                for ei in dx.external_identifiers.external_identifier:
                    res = ei.resource.value if ei.resource else ""
                    ident = _safe_str(ei.identifier, 200)
                    if res and ident:
                        session.add(DrugExternalIdentifier(drug=drug_obj, resource=res, identifier=ident))
                        counts["external_ids"] += 1

            # ── Patents ───────────────────────────────────────────────────
            if dx.patents:
                for pat in dx.patents.patent:
                    session.add(DrugPatent(
                        drug=drug_obj,
                        number=_safe_str(pat.number, 100),
                        country=_safe_str(pat.country, 100),
                        approved=_safe_str(pat.approved, 20),
                        expires=_safe_str(pat.expires, 20),
                        pediatric_extension=pat.pediatric_extension if pat.pediatric_extension is not None else False,
                    ))
                    counts["patents"] += 1

            # ── References ────────────────────────────────────────────────
            gr = dx.general_references
            if gr:
                if gr.articles:
                    for art in gr.articles.article:
                        item = {"ref_type": "article", "pubmed_id": _safe_str(art.pubmed_id, 50),
                                "citation": _safe_str(art.citation, _MAX_SHORT_TEXT), "ref_id": _safe_str(art.ref_id, 50)}
                        if item["pubmed_id"] or item["citation"]:
                            session.add(DrugReference(drug=drug_obj, **item))
                            counts["references"] += 1
                if gr.textbooks:
                    for tb in gr.textbooks.textbook:
                        item = {"ref_type": "textbook", "isbn": _safe_str(tb.isbn, 50),
                                "citation": _safe_str(tb.citation, _MAX_SHORT_TEXT), "ref_id": _safe_str(tb.ref_id, 50)}
                        if item["isbn"] or item["citation"]:
                            session.add(DrugReference(drug=drug_obj, **item))
                            counts["references"] += 1
                if gr.links:
                    for lnk in gr.links.link:
                        item = {"ref_type": "link", "title": _safe_str(lnk.title, _MAX_SHORT_TEXT),
                                "url": _safe_str(lnk.url, 500), "ref_id": _safe_str(lnk.ref_id, 50)}
                        if item["title"] or item["url"]:
                            session.add(DrugReference(drug=drug_obj, **item))
                            counts["references"] += 1

            # ── Targets ───────────────────────────────────────────────────
            if dx.targets:
                for t in dx.targets.target:
                    session.add(DrugTarget(
                        drug=drug_obj, target_id=_safe_str(t.id, 50),
                        name=_safe_str(t.name, 500), organism=_safe_str(t.organism, 200),
                        known_action=_known_action_str(t.known_action),
                        actions=_actions_str(t.actions),
                    ))
                    counts["targets"] += 1

            # ── Enzymes ───────────────────────────────────────────────────
            if dx.enzymes:
                for e in dx.enzymes.enzyme:
                    session.add(DrugEnzyme(
                        drug=drug_obj, enzyme_id=_safe_str(e.id, 50),
                        name=_safe_str(e.name, 500), organism=_safe_str(e.organism, 200),
                        known_action=_known_action_str(e.known_action),
                        actions=_actions_str(e.actions),
                        inhibition_strength=_safe_str(e.inhibition_strength, 50),
                        induction_strength=_safe_str(e.induction_strength, 50),
                    ))
                    counts["enzymes"] += 1

            # ── Carriers ──────────────────────────────────────────────────
            if dx.carriers:
                for c in dx.carriers.carrier:
                    session.add(DrugCarrier(
                        drug=drug_obj, carrier_id=_safe_str(c.id, 50),
                        name=_safe_str(c.name, 500), organism=_safe_str(c.organism, 200),
                        known_action=_known_action_str(c.known_action),
                        actions=_actions_str(c.actions),
                    ))
                    counts["carriers"] += 1

            # ── Transporters ──────────────────────────────────────────────
            if dx.transporters:
                for tr in dx.transporters.transporter:
                    session.add(DrugTransporter(
                        drug=drug_obj, transporter_id=_safe_str(tr.id, 50),
                        name=_safe_str(tr.name, 500), organism=_safe_str(tr.organism, 200),
                        known_action=_known_action_str(tr.known_action),
                        actions=_actions_str(tr.actions),
                    ))
                    counts["transporters"] += 1

            # ── Affected Organisms ────────────────────────────────────────
            if dx.affected_organisms:
                for org in dx.affected_organisms.affected_organism:
                    if org and org.strip():
                        session.add(DrugAffectedOrganism(drug=drug_obj, organism=org.strip()))
                        counts["affected_organisms"] += 1

            # ── Pathways ──────────────────────────────────────────────────
            if dx.pathways:
                for pw in dx.pathways.pathway:
                    session.add(DrugPathway(
                        drug=drug_obj,
                        smpdb_id=_safe_str(pw.smpdb_id, 50),
                        pathway_name=_safe_str(pw.name, 500),
                        category=_safe_str(pw.category, 200),
                    ))
                    counts["pathways"] += 1

            # ── Food Interactions ─────────────────────────────────────────
            if dx.food_interactions:
                for food_text in dx.food_interactions.food_interaction:
                    if food_text and food_text.strip():
                        session.add(DrugFoodInteraction(drug=drug_obj, interaction=food_text.strip()))
                        counts["food_interactions"] += 1

        # Flush to assign PKs before interaction phase
        session.flush()

        # ── Phase 2: drug-drug interactions ───────────────────────────────
        for dx in tqdm(drugs, desc="Interactions", unit="drug", bar_format=_BAR_FMT):
            if not dx.name or dx.drug_interactions is None:
                continue
            drug_name = dx.name.strip()
            drug_obj = drug_map.get(drug_name)
            if drug_obj is None:
                continue
            for interaction in dx.drug_interactions.drug_interaction:
                other_name = interaction.name.strip() if interaction.name else ""
                other_id = interaction.drugbank_id.value if interaction.drugbank_id else ""
                description = _safe_str(interaction.description)
                if not other_name:
                    continue
                session.add(DrugInteraction(
                    drug1_id=drug_obj.id, drug2_drugbank_id=other_id,
                    drug2_name=other_name, description=description,
                ))
                counts["interactions"] += 1

        session.commit()
        pm.suc(f"SQL seed complete: {counts}")
    except Exception as e:
        session.rollback()
        pm.err(e=e, m="SQL seed failed")
        raise
    finally:
        session.close()

    return counts


def is_db_seeded() -> bool:
    session = get_session()
    try:
        return session.query(Drug.id).limit(1).count() > 0
    finally:
        session.close()


def main(argv: list[str] | None = None) -> None:
    xml_path = Path("data/xml/drugbank.xml").resolve()
    if not xml_path.exists():
        pm.err(m=f"XML file not found: {xml_path}")
        sys.exit(1)

    pm.inf(f"DrugBank XML path: {xml_path}")
    init_sql_db()

    if is_db_seeded():
        pm.suc("Drug catalog already seeded — skipping.")
        return

    pm.inf("Parsing DrugBank XML …")
    t0 = time.time()
    xml_parser = XmlParser()
    drugbank: Drugbank = xml_parser.parse(str(xml_path), Drugbank)
    num_drugs = len(drugbank.drug)
    pm.suc(f"Parsed {num_drugs} drugs in {time.time() - t0:.1f}s")

    if num_drugs == 0:
        pm.war("No drugs found in XML — nothing to seed.")
        return

    t1 = time.time()
    counts = seed_all(drugbank.drug)
    pm.suc(f"Seeding complete in {time.time() - t1:.1f}s — {counts}")


if __name__ == "__main__":
    main()
