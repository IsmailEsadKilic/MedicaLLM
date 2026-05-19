import sys
import time
from pathlib import Path
from tqdm import tqdm
from xsdata.formats.dataclass.parsers import XmlParser
import logging
from sqlalchemy import text

# Add project root to path so we can import from src
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.db.sql_client import get_session
from src.db.sql_models import (
    Drug, DrugSynonym, DrugGroup, DrugCategory, DrugProduct,
    DrugReference, DrugInteraction, DrugFoodInteraction, DrugDosage, 
    DrugInternationalBrand, DrugMixture, DrugAtcCode, DrugExternalIdentifier,
    DrugTarget, DrugEnzyme, DrugCarrier, DrugTransporter
)
from scripts.init_tables import init_database
from drugbank import Drugbank, DrugType, GroupType, KnownActionType

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

logger = logging.getLogger(__name__)

#aig: file

_BAR_FMT = "{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"


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
    if actions_list is None:
        return ""
    return ", ".join(a for a in actions_list.action if a)


def _known_action_str(ka) -> str:
    if ka is None:
        return ""
    return ka.value if isinstance(ka, KnownActionType) else str(ka)


def seed_database(drugs: list[DrugType]):
    """Seed drug data into database."""
    session = get_session()

    drug_map = {}
    counts = {k: 0 for k in [
        "drugs", "synonyms", "groups", "categories", "products", 
        "references", "interactions", "food_interactions", "dosages", 
        "international_brands", "mixtures", "atc_codes", "external_ids", 
        "targets", "enzymes", "carriers", "transporters"
    ]}

    try:
        # ── Phase 1: Drugs & Entities ──
        for dx in tqdm(drugs, desc="Parsing Drugs", unit="drug", bar_format=_BAR_FMT):
            if not dx.name:
                continue

            drug_name = dx.name.strip()
            
            # Form drug object
            drug_obj = Drug(
                drug_id=_get_primary_id(dx),
                name=drug_name,
                name_lower=drug_name.lower(),
                drug_type=dx.type_value.value if dx.type_value else "",
                description=_safe_str(dx.description),
                indication=_safe_str(dx.indication),
                mechanism_of_action=_safe_str(dx.mechanism_of_action),
                pharmacodynamics=_safe_str(dx.pharmacodynamics),
                toxicity=_safe_str(dx.toxicity),
                metabolism=_safe_str(dx.metabolism),
                absorption=_safe_str(dx.absorption),
                half_life=_safe_str(dx.half_life, 1000),
                protein_binding=_safe_str(dx.protein_binding, 1000),
                route_of_elimination=_safe_str(dx.route_of_elimination),
                volume_of_distribution=_safe_str(dx.volume_of_distribution),
                clearance=_safe_str(dx.clearance),
                created_date=str(dx.created) if dx.created else "",
                updated_date=str(dx.updated) if dx.updated else "",
            )
            
            session.add(drug_obj)
            drug_map[drug_name] = drug_obj
            counts["drugs"] += 1

            # Synonyms
            if dx.synonyms:
                seen = set()
                for syn in dx.synonyms.synonym:
                    v = syn.value.strip()
                    if v and v not in seen and v != drug_name:
                        seen.add(v)
                        drug_obj.synonyms.append(DrugSynonym(synonym=v, synonym_lower=v.lower()))
                        counts["synonyms"] += 1
                        if len(seen) > 50: break # Skip absurd amounts of synonyms

            # Groups
            if dx.groups:
                for g in dx.groups.group:
                    drug_obj.groups.append(DrugGroup(group_name=g.value))
                    counts["groups"] += 1

            # Categories
            if dx.categories:
                for c in dx.categories.category:
                    if c.category:
                        drug_obj.categories.append(DrugCategory(category=c.category, category_lower=c.category.lower()))
                        counts["categories"] += 1

            # Products (Brands / Physical packages)
            if dx.products:
                seen_prod = set()
                for p in dx.products.product:
                    pname = _safe_str(p.name, 500)
                    if pname and pname not in seen_prod:
                        seen_prod.add(pname)
                        drug_obj.products.append(DrugProduct(
                            product_name=pname, product_name_lower=pname.lower(),
                            labeller=_safe_str(p.labeller, 500), ndc_id=_safe_str(p.ndc_id, 100),
                            ndc_product_code=_safe_str(p.ndc_product_code, 100), dpd_id=_safe_str(p.dpd_id, 100),
                            ema_product_code=_safe_str(p.ema_product_code, 100), ema_ma_number=_safe_str(p.ema_ma_number, 100),
                            fda_application_number=_safe_str(p.fda_application_number, 100),
                            dosage_form=_safe_str(p.dosage_form, 200), strength=_safe_str(p.strength, 200), route=_safe_str(p.route, 200),
                            country=p.country.value if getattr(p, "country", None) else "", # type: ignore
                            source=p.source.value if getattr(p, "source", None) else "", # type: ignore
                            generic=p.generic if getattr(p, "generic", None) is not None else False,
                            over_the_counter=p.over_the_counter if getattr(p, "over_the_counter", None) is not None else False,
                            approved=p.approved if getattr(p, "approved", None) is not None else False,
                            started_marketing_on=_safe_str(p.started_marketing_on, 20),
                            ended_marketing_on=_safe_str(p.ended_marketing_on, 20),
                        ))
                        counts["products"] += 1
            
            # International Brands
            if dx.international_brands:
                for ib in dx.international_brands.international_brand:
                    if ib.name:
                        drug_obj.international_brands.append(DrugInternationalBrand(brand_name=_safe_str(ib.name, 500), brand_name_lower=_safe_str(ib.name.lower(), 500), company=_safe_str(ib.company, 500)))
                        counts["international_brands"] += 1
                        
            # Mixtures
            if dx.mixtures:
                for mx in dx.mixtures.mixture:
                    mname = _safe_str(mx.name, 500)
                    if mname:
                        drug_obj.mixtures.append(DrugMixture(
                            mixture_name=mname,
                            mixture_name_lower=mname.lower(),
                            ingredients=_safe_str(mx.ingredients),
                            supplemental_ingredients=_safe_str(mx.supplemental_ingredients),
                        ))
                        counts["mixtures"] += 1

            # Dosages
            if dx.dosages:
                for dos in dx.dosages.dosage:
                    drug_obj.dosages.append(DrugDosage(
                        form=_safe_str(dos.form, 200),
                        route=_safe_str(dos.route, 200),
                        strength=_safe_str(dos.strength, 200),
                    ))
                    counts["dosages"] += 1

            # Atc Codes
            if dx.atc_codes:
                for atc in dx.atc_codes.atc_code:
                    if atc.code:
                        drug_obj.atc_codes.append(DrugAtcCode(code=atc.code))
                        counts["atc_codes"] += 1

            # Food Interactions
            if dx.food_interactions:
                for food_text in dx.food_interactions.food_interaction:
                    if food_text and food_text.strip():
                        drug_obj.food_interactions.append(DrugFoodInteraction(interaction=food_text.strip()))
                        counts["food_interactions"] += 1
                        
            # External Identifiers
            if dx.external_identifiers:
                for ei in dx.external_identifiers.external_identifier:
                    res = ei.resource.value if ei.resource else ""
                    ident = _safe_str(ei.identifier, 200)
                    if res and ident:
                        drug_obj.external_identifiers.append(DrugExternalIdentifier(resource=res, identifier=ident))
                        counts["external_ids"] += 1
                        
            # References
            gr = dx.general_references
            if gr:
                if gr.articles:
                    for art in gr.articles.article:
                        if art.pubmed_id or art.citation:
                            drug_obj.references.append(DrugReference(ref_type="article", pubmed_id=_safe_str(art.pubmed_id, 50), citation=_safe_str(art.citation, 1000), ref_id=_safe_str(art.ref_id, 50)))
                            counts["references"] += 1
                if gr.textbooks:
                    for tb in gr.textbooks.textbook:
                        if tb.isbn or tb.citation:
                            drug_obj.references.append(DrugReference(ref_type="textbook", isbn=_safe_str(tb.isbn, 50), citation=_safe_str(tb.citation, 1000), ref_id=_safe_str(tb.ref_id, 50)))
                            counts["references"] += 1
                if gr.links:
                    for lnk in gr.links.link:
                        if lnk.title or lnk.url:
                            drug_obj.references.append(DrugReference(ref_type="link", title=_safe_str(lnk.title, 1000), url=_safe_str(lnk.url, 500), ref_id=_safe_str(lnk.ref_id, 50)))
                            counts["references"] += 1

            # Biological macromolecule targets
            if dx.targets:
                for t in dx.targets.target:
                    drug_obj.targets.append(DrugTarget(
                        target_id=_safe_str(t.id, 50),
                        name=_safe_str(t.name, 500), organism=_safe_str(t.organism, 200),
                        known_action=_known_action_str(t.known_action), actions=_actions_str(t.actions)
                    ))
                    counts["targets"] += 1

            # Enzymes
            if dx.enzymes:
                for e in dx.enzymes.enzyme:
                    drug_obj.enzymes.append(DrugEnzyme(
                        enzyme_id=_safe_str(e.id, 50),
                        name=_safe_str(e.name, 500), organism=_safe_str(e.organism, 200),
                        known_action=_known_action_str(e.known_action), actions=_actions_str(e.actions),
                        inhibition_strength=_safe_str(e.inhibition_strength, 50),
                        induction_strength=_safe_str(e.induction_strength, 50)
                    ))
                    counts["enzymes"] += 1
                    
            # Carriers
            if dx.carriers:
                for c in dx.carriers.carrier:
                    drug_obj.carriers.append(DrugCarrier(
                        carrier_id=_safe_str(c.id, 50),
                        name=_safe_str(c.name, 500), organism=_safe_str(c.organism, 200),
                        known_action=_known_action_str(c.known_action), actions=_actions_str(c.actions)
                    ))
                    counts["carriers"] += 1

            # Transporters
            if dx.transporters:
                for tr in dx.transporters.transporter:
                    drug_obj.transporters.append(DrugTransporter(
                        transporter_id=_safe_str(tr.id, 50),
                        name=_safe_str(tr.name, 500), organism=_safe_str(tr.organism, 200),
                        known_action=_known_action_str(tr.known_action), actions=_actions_str(tr.actions)
                    ))
                    counts["transporters"] += 1

        # ── Phase 2: Interactions ──
        logger.info("Parsing Drug Interactions...")
        for dx in tqdm(drugs, desc="Interactions", unit="drug", bar_format=_BAR_FMT):
            drug_name = dx.name.strip() if dx.name else ""
            if not drug_name or not dx.drug_interactions: 
                continue
            
            drug_obj = drug_map.get(drug_name)
            if not drug_obj: 
                continue
            
            for interact in dx.drug_interactions.drug_interaction:
                db_id = interact.drugbank_id.value if interact.drugbank_id else ""
                int_name = interact.name.strip() if interact.name else ""
                if db_id and int_name:
                    drug_obj.interactions_as_drug1.append(DrugInteraction(
                        drug2_drugbank_id=db_id, 
                        drug2_name=int_name, description=_safe_str(interact.description)
                    ))
                    counts["interactions"] += 1

        logger.info("Committing all data to database (this may take a moment)...")
        session.commit()
        
        logger.info(f"✨ Seeding Complete! Inserted Entities: {counts}")

    except Exception as e:
        session.rollback()
        logger.error(f"Seeding failed: {e}", exc_info=True)
        raise
    finally:
        session.close()


def main():
    """Main entry point for seeding DrugBank data."""
    xml_path = Path(__file__).parent.parent / "data" / "drugbank.xml"
    if not xml_path.exists():
        logger.error(f"Required XML file missing: {xml_path}")
        sys.exit(1)

    # 1. Initialize Database (drop and recreate tables)
    logger.info("Initializing database tables...")
    init_database(drop_existing=True)
    
    # 2. Parse XML
    logger.info("Parsing DrugBank XML from disk into memory...")
    t0 = time.time()
    xml_parser = XmlParser()
    drugbank = xml_parser.parse(str(xml_path), Drugbank)
    logger.info(f"Successfully loaded {len(drugbank.drug)} drugs into memory. ({time.time() - t0:.2f}s)")
    
    # 3. Seed Data
    seed_database(drugbank.drug)


if __name__ == "__main__":
    main()
