from __future__ import annotations
import json
from typing import List, Optional, Union
from sqlalchemy import or_, func
from sqlalchemy.orm import joinedload

from .calculate_severity import calculate_severity
from ..db.sql_client import get_session
from ..db.sql_models import (
    Drug as DrugORM,
    DrugSynonym,
    DrugGroup,
    DrugCategory,
    DrugProduct,
    DrugInternationalBrand,
    DrugMixture,
    DrugInteraction,
    DrugFoodInteraction,
    DrugDosage,
    DrugTarget,
    DrugEnzyme,
    DrugCarrier,
    DrugTransporter,
    DrugAtcCode,
    PatientRecord,
    UserRecord,
)
from .models import (
    Drug,
    DrugBase,
    DrugDescription,
    DrugSearchRequest,
    DrugSearchResponse,
    DrugSearchResult,
    CheckDrugInteractionRequest,
    CheckDrugInteractionResponse,
    DrugInteractionDetail,
    DrugFoodInteraction as DrugFoodInteractionModel,
    DrugSearchByIndicationRequest,
    DrugSearchByIndicationResponse,
    DrugSearchByCategoryRequest,
    DrugSearchByCategoryResponse,
    DrugAlternative,
    AnalyzePatientRequest,
    AnalyzePatientResponse,
    AnalyzePatientFoodInteractionsRequest,
    AnalyzePatientFoodInteractionsResponse,
    DrugDosage as DrugDosageModel,
    DrugTarget as DrugTargetModel,
    DrugEnzyme as DrugEnzymeModel,
    DrugCarrier as DrugCarrierModel,
    DrugTransporter as DrugTransporterModel,
    DrugInteraction as DrugInteractionModel,
    CheckOverdoseRiskResponse,
    OverdoseRiskDetail,
)

from logging import getLogger

logger = getLogger(__name__)

def _orm_to_drug_base(drug_orm: DrugORM) -> DrugBase:
    synonyms = [s.synonym for s in drug_orm.synonyms]
    
    return DrugBase(
        drug_id=drug_orm.drug_id, # type: ignore
        name=drug_orm.name, # type: ignore
        drug_type=drug_orm.drug_type, # type: ignore
        description=drug_orm.description, # type: ignore
        indication=drug_orm.indication, # type: ignore
        mechanism_of_action=drug_orm.mechanism_of_action, # type: ignore
        pharmacodynamics=drug_orm.pharmacodynamics, # type: ignore
        synonyms=synonyms,
    )


def _orm_to_drug_full(drug_orm: DrugORM) -> Drug:
    # Basic fields
    drug = Drug(
        drug_id=drug_orm.drug_id, # type: ignore
        name=drug_orm.name, # type: ignore
        drug_type=drug_orm.drug_type, # type: ignore
        description=drug_orm.description, # type: ignore
        indication=drug_orm.indication, # type: ignore
        mechanism_of_action=drug_orm.mechanism_of_action, # type: ignore
        pharmacodynamics=drug_orm.pharmacodynamics, # type: ignore
        toxicity=drug_orm.toxicity, # type: ignore
        metabolism=drug_orm.metabolism, # type: ignore
        absorption=drug_orm.absorption, # type: ignore
        half_life=drug_orm.half_life, # type: ignore
        protein_binding=drug_orm.protein_binding, # type: ignore
        route_of_elimination=drug_orm.route_of_elimination, # type: ignore
        volume_of_distribution=drug_orm.volume_of_distribution, # type: ignore
        clearance=drug_orm.clearance, # type: ignore
        created_date=drug_orm.created_date, # type: ignore
        updated_date=drug_orm.updated_date, # type: ignore
    )
    
    # Relationships
    drug.synonyms = [s.synonym for s in drug_orm.synonyms]
    drug.groups = [g.group_name for g in drug_orm.groups]
    drug.categories = [c.category for c in drug_orm.categories]
    drug.atc_codes = [a.code for a in drug_orm.atc_codes]
    drug.food_interactions = [f.interaction for f in drug_orm.food_interactions]
    
    # Complex relationships
    drug.products = [ # type: ignore
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
        for p in drug_orm.products
    ]
    
    drug.international_brands = [ # type: ignore
        {"brand_name": b.brand_name, "company": b.company}
        for b in drug_orm.international_brands
    ]
    
    drug.dosages = [ # type: ignore
        {"form": d.form, "route": d.route, "strength": d.strength}
        for d in drug_orm.dosages
    ]
    
    drug.mixtures = [ # type: ignore
        {
            "mixture_name": m.mixture_name,
            "ingredients": m.ingredients,
            "supplemental_ingredients": m.supplemental_ingredients,
        }
        for m in drug_orm.mixtures
    ]
    
    drug.targets = [ # type: ignore
        {
            "target_id": t.target_id,
            "name": t.name,
            "organism": t.organism,
            "known_action": t.known_action,
            "actions": t.actions,
        }
        for t in drug_orm.targets
    ]
    
    drug.enzymes = [ # type: ignore
        {
            "enzyme_id": e.enzyme_id,
            "name": e.name,
            "organism": e.organism,
            "known_action": e.known_action,
            "actions": e.actions,
            "inhibition_strength": e.inhibition_strength,
            "induction_strength": e.induction_strength,
        }
        for e in drug_orm.enzymes
    ]
    
    drug.carriers = [ # type: ignore
        {
            "carrier_id": c.carrier_id,
            "name": c.name,
            "organism": c.organism,
            "known_action": c.known_action,
            "actions": c.actions,
        }
        for c in drug_orm.carriers
    ]
    
    drug.transporters = [ # type: ignore
        {
            "transporter_id": t.transporter_id,
            "name": t.name,
            "organism": t.organism,
            "known_action": t.known_action,
            "actions": t.actions,
        }
        for t in drug_orm.transporters
    ]
    
    drug.interactions = [ # type: ignore
        {
            "drug2_drugbank_id": i.drug2_drugbank_id,
            "drug2_name": i.drug2_name,
            "description": i.description,
        }
        for i in drug_orm.interactions_as_drug1
    ]
    
    return drug


def _resolve_drug_id(session, drug_id: str) -> Optional[DrugORM]:
    return session.query(DrugORM).filter(DrugORM.drug_id == drug_id).first()


# ============================================================================
# 1. GET DRUG - Full drug information by ID
# ============================================================================

def get_drug(drug_id: str, detail: str = "moderate") -> Optional[Union[Drug, DrugBase, DrugDescription]]:
    """
    Get drug information by drug_id with configurable detail level.
    
    Args:
        drug_id: DrugBank ID (e.g., "DB00945")
        detail: Level of detail - "low", "moderate", or "high"
            - low: DrugDescription (drug_id, name, description)
            - moderate: DrugBase (+ drug_type, indication, mechanism, pharmacodynamics, synonyms)
            - high: Drug (full information including interactions, products, targets, etc.)
    
    Returns:
        DrugDescription | DrugBase | Drug: Drug information based on detail level
    """
    logger.debug(f"[DRUG SERVICE] get_drug called with drug_id: {drug_id}, detail: {detail}")
    session = get_session()
    try:
        logger.debug(f"[DRUG SERVICE] Querying database for drug {drug_id}")
        
        if detail == "low":
            # Low detail: Only basic fields, no relationships
            drug_orm = (
                session.query(DrugORM.drug_id, DrugORM.name, DrugORM.description)
                .filter(DrugORM.drug_id == drug_id)
                .first()
            )
            
            if not drug_orm:
                logger.warning(f"[DRUG SERVICE] Drug not found: {drug_id}")
                return None
            
            logger.info(f"[DRUG SERVICE] Retrieved drug (low detail): {drug_orm.name} ({drug_id})")
            return DrugDescription(
                drug_id=drug_orm.drug_id,
                name=drug_orm.name,
                description=drug_orm.description or "",
            )
        
        elif detail == "moderate":
            # Moderate detail: DrugBase fields + synonyms
            drug_orm = (
                session.query(DrugORM)
                .options(joinedload(DrugORM.synonyms))
                .filter(DrugORM.drug_id == drug_id)
                .first()
            )
            
            if not drug_orm:
                logger.warning(f"[DRUG SERVICE] Drug not found: {drug_id}")
                return None
            
            logger.info(f"[DRUG SERVICE] Retrieved drug (moderate detail): {drug_orm.name} ({drug_id})")
            
            synonyms = [s.synonym for s in drug_orm.synonyms]
            
            return DrugBase(
                drug_id=drug_orm.drug_id, # type: ignore
                name=drug_orm.name, # type: ignore
                description=drug_orm.description or "", # type: ignore
                drug_type=drug_orm.drug_type or "", # type: ignore
                indication=drug_orm.indication or "", # type: ignore
                mechanism_of_action=drug_orm.mechanism_of_action or "", # type: ignore
                pharmacodynamics=drug_orm.pharmacodynamics or "", # type: ignore
                synonyms=synonyms,
            )
        
        else:  # detail == "high"
            # High detail: Full Drug model with all relationships
            drug_orm = (
                session.query(DrugORM)
                .options(
                    joinedload(DrugORM.synonyms),
                    joinedload(DrugORM.groups),
                    joinedload(DrugORM.categories),
                    joinedload(DrugORM.atc_codes),
                    joinedload(DrugORM.food_interactions),
                    joinedload(DrugORM.dosages),
                )
                .filter(DrugORM.drug_id == drug_id)
                .first()
            )
            
            if not drug_orm:
                logger.warning(f"[DRUG SERVICE] Drug not found: {drug_id}")
                return None
            
            logger.info(f"[DRUG SERVICE] Retrieved drug (high detail): {drug_orm.name} ({drug_id})")
            
            # Load large relationships separately with limits to avoid memory issues
            drug_pk = drug_orm.id
            drug_orm.products = session.query(DrugProduct).filter(DrugProduct.drug_pk == drug_pk).limit(100).all()
            drug_orm.international_brands = session.query(DrugInternationalBrand).filter(DrugInternationalBrand.drug_pk == drug_pk).limit(100).all()
            drug_orm.mixtures = session.query(DrugMixture).filter(DrugMixture.drug_pk == drug_pk).limit(50).all()
            drug_orm.targets = session.query(DrugTarget).filter(DrugTarget.drug_pk == drug_pk).limit(50).all()
            drug_orm.enzymes = session.query(DrugEnzyme).filter(DrugEnzyme.drug_pk == drug_pk).limit(50).all()
            drug_orm.carriers = session.query(DrugCarrier).filter(DrugCarrier.drug_pk == drug_pk).limit(50).all()
            drug_orm.transporters = session.query(DrugTransporter).filter(DrugTransporter.drug_pk == drug_pk).limit(50).all()
            drug_orm.interactions_as_drug1 = session.query(DrugInteraction).filter(DrugInteraction.drug1_id == drug_pk).limit(500).all()
            
            logger.debug(f"[DRUG SERVICE] High detail - loaded {len(drug_orm.targets)} targets, {len(drug_orm.enzymes)} enzymes, {len(drug_orm.interactions_as_drug1)} interactions (limited)")
            
            return _orm_to_drug_full(drug_orm)
    
    except Exception as e:
        logger.error(f"[DRUG SERVICE] Error getting drug {drug_id}: {e}", exc_info=True)
        return None
    finally:
        session.close()

def search_drugs(request: DrugSearchRequest) -> DrugSearchResponse:
    """
    Hybrid search: combines TRGM fuzzy matching with semantic vector search.
    
    - TRGM: Good for typos, abbreviations, exact name matching
    - Semantic: Good for conceptual queries like "blood pressure medication"
    
    Args:
        request: Search parameters
    
    Returns:
        DrugSearchResponse: List of matching drugs with similarity scores
    """
    logger.debug(f"[DRUG SERVICE] search_drugs called with query: '{request.query}', limit: {request.limit}, semantic: {request.include_semantic_search}")
    logger.debug(f"[DRUG SERVICE] Search options - synonyms: {request.include_synonyms}, products: {request.include_products}, brands: {request.include_brands}")
    
    session = get_session()
    try:        
        search_term = request.query.lower().strip()
        if not search_term:
            logger.warning(f"[DRUG SERVICE] Empty search term provided")
            return DrugSearchResponse(
                success=True,
                query=request.query,
                results=[],
                count=0,
            )
        
        logger.debug(f"[DRUG SERVICE] Normalized search term: '{search_term}'")
        drug_map = {}  # drug_id -> {drug_orm, similarity_score, source}
        
        # ===== LEXICAL SEARCH (TRGM) =====
        
        # 1. Search by drug name (TRGM similarity)
        if True:  # Always search names
            logger.debug(f"[DRUG SERVICE] Searching by drug name (TRGM)")
            name_results = (
                session.query(
                    DrugORM.drug_id,
                    DrugORM.name,
                    DrugORM.description,
                    DrugORM.drug_type,
                    func.similarity(DrugORM.name_lower, search_term).label("similarity"),
                )
                .filter(func.similarity(DrugORM.name_lower, search_term) > request.min_similarity)
                .order_by(func.similarity(DrugORM.name_lower, search_term).desc())
                .limit(request.limit * 2)
                .all()
            )
            
            logger.debug(f"[DRUG SERVICE] Found {len(name_results)} name matches")
            
            for drug_id, name, desc, dtype, sim in name_results:
                if drug_id not in drug_map or drug_map[drug_id]["similarity"] < sim:
                    drug_map[drug_id] = {
                        "drug_id": drug_id,
                        "name": name,
                        "description": desc,
                        "drug_type": dtype,
                        "similarity": sim,
                        "source": "name",
                    }
        
        # 2. Search by synonym
        if request.include_synonyms:
            logger.debug(f"[DRUG SERVICE] Searching by synonyms (TRGM)")
            syn_results = (
                session.query(
                    DrugORM.drug_id,
                    DrugORM.name,
                    DrugORM.description,
                    DrugORM.drug_type,
                    func.similarity(DrugSynonym.synonym_lower, search_term).label("similarity"),
                )
                .join(DrugSynonym, DrugORM.id == DrugSynonym.drug_pk)
                .filter(func.similarity(DrugSynonym.synonym_lower, search_term) > request.min_similarity)
                .order_by(func.similarity(DrugSynonym.synonym_lower, search_term).desc())
                .limit(request.limit)
                .all()
            )
            
            logger.debug(f"[DRUG SERVICE] Found {len(syn_results)} synonym matches")
            
            for drug_id, name, desc, dtype, sim in syn_results:
                if drug_id not in drug_map or drug_map[drug_id]["similarity"] < sim:
                    drug_map[drug_id] = {
                        "drug_id": drug_id,
                        "name": name,
                        "description": desc,
                        "drug_type": dtype,
                        "similarity": sim,
                        "source": "synonym",
                    }
        
        # 3. Search by product name
        if request.include_products:
            logger.debug(f"[DRUG SERVICE] Searching by products (TRGM)")
            prod_results = (
                session.query(
                    DrugORM.drug_id,
                    DrugORM.name,
                    DrugORM.description,
                    DrugORM.drug_type,
                    func.similarity(DrugProduct.product_name_lower, search_term).label("similarity"),
                )
                .join(DrugProduct, DrugORM.id == DrugProduct.drug_pk)
                .filter(func.similarity(DrugProduct.product_name_lower, search_term) > request.min_similarity)
                .order_by(func.similarity(DrugProduct.product_name_lower, search_term).desc())
                .limit(request.limit)
                .all()
            )
            
            logger.debug(f"[DRUG SERVICE] Found {len(prod_results)} product matches")
            
            for drug_id, name, desc, dtype, sim in prod_results:
                if drug_id not in drug_map or drug_map[drug_id]["similarity"] < sim * 0.9:  # Slight penalty
                    drug_map[drug_id] = {
                        "drug_id": drug_id,
                        "name": name,
                        "description": desc,
                        "drug_type": dtype,
                        "similarity": sim * 0.9,
                        "source": "product",
                    }
        
        # 4. Search by international brand
        if request.include_brands:
            logger.debug(f"[DRUG SERVICE] Searching by brands (TRGM)")
            brand_results = (
                session.query(
                    DrugORM.drug_id,
                    DrugORM.name,
                    DrugORM.description,
                    DrugORM.drug_type,
                    func.similarity(DrugInternationalBrand.brand_name_lower, search_term).label("similarity"),
                )
                .join(DrugInternationalBrand, DrugORM.id == DrugInternationalBrand.drug_pk)
                .filter(func.similarity(DrugInternationalBrand.brand_name_lower, search_term) > request.min_similarity)
                .order_by(func.similarity(DrugInternationalBrand.brand_name_lower, search_term).desc())
                .limit(request.limit)
                .all()
            )
            
            logger.debug(f"[DRUG SERVICE] Found {len(brand_results)} brand matches")
            
            for drug_id, name, desc, dtype, sim in brand_results:
                if drug_id not in drug_map or drug_map[drug_id]["similarity"] < sim * 0.9:
                    drug_map[drug_id] = {
                        "drug_id": drug_id,
                        "name": name,
                        "description": desc,
                        "drug_type": dtype,
                        "similarity": sim * 0.9,
                        "source": "brand",
                    }
        
        # ===== SEMANTIC SEARCH (VECTOR) =====
        
        if request.include_semantic_search:
            logger.debug(f"[DRUG SERVICE] Performing semantic search")
            try:
                from .embedding_service import get_embedding_service
                embedding_service = get_embedding_service()
                
                # Semantic search with slightly lower threshold
                semantic_results = embedding_service.search_similar_drugs(
                    query=request.query,
                    limit=request.limit * 2,
                    min_similarity=max(0.3, request.min_similarity - 0.1)  # Slightly lower threshold
                )
                
                logger.debug(f"[DRUG SERVICE] Found {len(semantic_results)} semantic matches")
                
                # Merge semantic results with a weight factor
                # Semantic scores are typically lower, so we boost them slightly
                semantic_weight = 0.85  # Semantic results get 85% weight vs lexical
                
                for drug_id, name, desc, sim in semantic_results:
                    weighted_sim = sim * semantic_weight
                    
                    if drug_id not in drug_map:
                        # New result from semantic search only
                        drug_map[drug_id] = {
                            "drug_id": drug_id,
                            "name": name,
                            "description": desc,
                            "drug_type": "",  # Not available from semantic search
                            "similarity": weighted_sim,
                            "source": "semantic",
                        }
                    else:
                        # Drug found in both lexical and semantic search
                        # Boost the score (hybrid boost)
                        existing_sim = drug_map[drug_id]["similarity"]
                        # Take max of existing and semantic, then add small boost for appearing in both
                        boosted_sim = max(existing_sim, weighted_sim) + 0.05
                        drug_map[drug_id]["similarity"] = min(1.0, boosted_sim)  # Cap at 1.0
                        drug_map[drug_id]["source"] = "hybrid"
                
                logger.info(f"[DRUG SERVICE] Hybrid search: {len(drug_map)} total unique drugs after merging")
                
            except Exception as e:
                logger.error(f"[DRUG SERVICE] Semantic search failed: {e}", exc_info=True)
                # Continue with lexical results only
        
        # Sort by similarity and limit
        results = sorted(
            drug_map.values(),
            key=lambda x: x["similarity"],
            reverse=True,
        )[:request.limit]
        
        # Convert to response models
        search_results = [
            DrugSearchResult(
                drug_id=r["drug_id"],
                name=r["name"],
                description=r["description"],
                similarity_score=r["similarity"],
            )
            for r in results
        ]
        
        logger.info(f"[DRUG SERVICE] Search '{request.query}' found {len(search_results)} results (semantic: {request.include_semantic_search})")
        
        return DrugSearchResponse(
            success=True,
            query=request.query,
            results=search_results,
            count=len(search_results),
        )
    
    except Exception as e:
        logger.error(f"[DRUG SERVICE] Error searching drugs: {e}", exc_info=True)
        return DrugSearchResponse(
            success=False,
            query=request.query,
            results=[],
            count=0,
        )
    finally:
        session.close()

def check_drug_interactions(request: CheckDrugInteractionRequest) -> CheckDrugInteractionResponse:
    """
    Check for interactions between multiple drugs.
    
    Args:
        request: List of drug IDs to check
    
    Returns:
        CheckDrugInteractionResponse: All interactions found with severity scores
    """
    logger.debug(f"[DRUG SERVICE] check_drug_interactions called with {len(request.drug_ids)} drugs: {request.drug_ids}")
    
    session = get_session()
    try:
        drug_ids = request.drug_ids
        if len(drug_ids) < 2:
            logger.warning(f"[DRUG SERVICE] Insufficient drugs provided: {len(drug_ids)}")
            return CheckDrugInteractionResponse(interactions=[], count=0)
        
        # Get all drugs
        logger.debug(f"[DRUG SERVICE] Fetching drug records from database")
        drugs = session.query(DrugORM).filter(DrugORM.drug_id.in_(drug_ids)).all()
        drug_map = {d.drug_id: d for d in drugs}
        logger.debug(f"[DRUG SERVICE] Found {len(drugs)} drugs in database")
        
        interactions = []
        max_severity = 0.0
        
        # Check all pairs
        logger.debug(f"[DRUG SERVICE] Checking all drug pairs for interactions")
        for i, drug1_id in enumerate(drug_ids):
            for drug2_id in drug_ids[i + 1:]:
                drug1 = drug_map.get(drug1_id) # type: ignore
                drug2 = drug_map.get(drug2_id) # type: ignore
                
                if not drug1 or not drug2:
                    logger.warning(f"[DRUG SERVICE] Drug not found in map: {drug1_id if not drug1 else drug2_id}")
                    continue
                
                # Check both directions
                interaction = (
                    session.query(DrugInteraction)
                    .filter(
                        or_(
                            (DrugInteraction.drug1_id == drug1.id)
                            & (DrugInteraction.drug2_drugbank_id == drug2.drug_id),
                            (DrugInteraction.drug1_id == drug2.id)
                            & (DrugInteraction.drug2_drugbank_id == drug1.drug_id),
                        )
                    )
                    .first()
                )
                
                if interaction:
                    severity = calculate_severity(interaction.description) # type: ignore
                    max_severity = max(max_severity, severity)
                    logger.debug(f"[DRUG SERVICE] Interaction found: {drug1.name} + {drug2.name}, severity: {severity:.2f}")
                    
                    interactions.append(
                        DrugInteractionDetail(
                            drug1_id=drug1.drug_id, # type: ignore
                            drug1_name=drug1.name, # type: ignore
                            drug2_id=drug2.drug_id, # type: ignore
                            drug2_name=drug2.name, # type: ignore
                            description=interaction.description, # type: ignore
                            severity=severity,
                        )
                    )
        
        logger.info(f"[DRUG SERVICE] Found {len(interactions)} interactions among {len(drug_ids)} drugs, max severity: {max_severity:.2f}")
        
        return CheckDrugInteractionResponse(
            interactions=interactions,
            count=len(interactions),
            overall_severity=max_severity if interactions else None,
        )
    
    except Exception as e:
        logger.error(f"[DRUG SERVICE] Error checking drug interactions: {e}", exc_info=True)
        return CheckDrugInteractionResponse(interactions=[], count=0)
    finally:
        session.close()

def check_drug_food_interactions(drug_id: str) -> List[DrugFoodInteractionModel]:
    """
    Get all food interactions for a specific drug.
    
    Args:
        drug_id: DrugBank ID
    
    Returns:
        List[DrugFoodInteractionModel]: All food interactions
    """
    session = get_session()
    try:
        drug = _resolve_drug_id(session, drug_id)
        if not drug:
            logger.warning(f"Drug not found: {drug_id}")
            return []
        
        interactions = [
            DrugFoodInteractionModel(interaction=fi.interaction)
            for fi in drug.food_interactions
        ]
        
        logger.info(f"Found {len(interactions)} food interactions for {drug.name}")
        return interactions
    
    except Exception as e:
        logger.error(f"Error getting food interactions: {e}", exc_info=True)
        return []
    finally:
        session.close()

def search_drugs_by_indication(request: DrugSearchByIndicationRequest) -> DrugSearchByIndicationResponse:
    """
    Search drugs by medical indication/condition.
    Supports both lexical (TRGM) and semantic (vector) search.
    
    Args:
        request: Indication search parameters
    
    Returns:
        DrugSearchByIndicationResponse: Drugs matching the indication
    """
    session = get_session()
    try:
        search_term = request.indication.lower().strip()
        drug_map = {}  # drug_id -> {drug_id, name, description, similarity}
        
        # ===== LEXICAL SEARCH (TRGM) =====
        logger.debug(f"[DRUG SERVICE] Searching by indication (TRGM): '{search_term}'")
        
        # Search in indication field using TRGM similarity
        results = (
            session.query(
                DrugORM.drug_id,
                DrugORM.name,
                DrugORM.description,
                func.similarity(func.lower(DrugORM.indication), search_term).label("similarity"),
            )
            .filter(func.similarity(func.lower(DrugORM.indication), search_term) > 0.2)
            .order_by(func.similarity(func.lower(DrugORM.indication), search_term).desc())
            .limit(request.limit * 2)
            .all()
        )
        
        logger.debug(f"[DRUG SERVICE] Found {len(results)} TRGM matches for indication")
        
        for drug_id, name, description, sim in results:
            drug_map[drug_id] = {
                "drug_id": drug_id,
                "name": name,
                "description": description,
                "similarity": sim,
            }
        
        # ===== SEMANTIC SEARCH (VECTOR) =====
        if request.include_semantic_search:
            logger.debug(f"[DRUG SERVICE] Performing semantic search for indication")
            try:
                from .embedding_service import get_embedding_service
                embedding_service = get_embedding_service()
                
                # Semantic search on indication field
                semantic_results = embedding_service.search_similar_drugs(
                    query=request.indication,
                    limit=request.limit * 2,
                    min_similarity=0.3
                )
                
                logger.debug(f"[DRUG SERVICE] Found {len(semantic_results)} semantic matches")
                
                semantic_weight = 0.85
                
                for drug_id, name, desc, sim in semantic_results:
                    weighted_sim = sim * semantic_weight
                    
                    if drug_id not in drug_map:
                        drug_map[drug_id] = {
                            "drug_id": drug_id,
                            "name": name,
                            "description": desc,
                            "similarity": weighted_sim,
                        }
                    else:
                        # Hybrid boost
                        existing_sim = drug_map[drug_id]["similarity"]
                        boosted_sim = max(existing_sim, weighted_sim) + 0.05
                        drug_map[drug_id]["similarity"] = min(1.0, boosted_sim)
                
                logger.info(f"[DRUG SERVICE] Hybrid indication search: {len(drug_map)} total unique drugs")
                
            except Exception as e:
                logger.error(f"[DRUG SERVICE] Semantic search failed: {e}", exc_info=True)
        
        # Sort by similarity and limit
        sorted_results = sorted(
            drug_map.values(),
            key=lambda x: x["similarity"],
            reverse=True,
        )[:request.limit]
        
        drug_results = [
            DrugDescription(
                drug_id=r["drug_id"],
                name=r["name"],
                description=r["description"],
            )
            for r in sorted_results
        ]
        
        logger.info(f"Found {len(drug_results)} drugs for indication '{request.indication}' (semantic: {request.include_semantic_search})")
        
        return DrugSearchByIndicationResponse(
            success=True,
            indication=request.indication,
            results=drug_results,
            count=len(drug_results),
        )
    
    except Exception as e:
        logger.error(f"Error searching by indication: {e}", exc_info=True)
        return DrugSearchByIndicationResponse(
            success=False,
            indication=request.indication,
            results=[],
            count=0,
        )
    finally:
        session.close()

def search_drugs_by_category(request: DrugSearchByCategoryRequest) -> DrugSearchByCategoryResponse:
    """
    Search drugs by therapeutic category.
    Supports both lexical (TRGM) and semantic (vector) search.
    
    Args:
        request: Category search parameters
    
    Returns:
        DrugSearchByCategoryResponse: Drugs in the category
    """
    session = get_session()
    try:
        search_term = request.category.lower().strip()
        drug_map = {}  # drug_id -> {drug_id, name, description, similarity}
        
        # ===== LEXICAL SEARCH (TRGM) =====
        logger.debug(f"[DRUG SERVICE] Searching by category (TRGM): '{search_term}'")
        
        # Search categories using TRGM similarity
        category_matches = (
            session.query(
                DrugCategory.drug_pk,
                func.similarity(DrugCategory.category_lower, search_term).label("similarity")
            )
            .filter(func.similarity(DrugCategory.category_lower, search_term) > 0.3)
            .order_by(func.similarity(DrugCategory.category_lower, search_term).desc())
            .limit(request.limit * 2)
            .all()
        )
        
        logger.debug(f"[DRUG SERVICE] Found {len(category_matches)} TRGM category matches")
        
        if category_matches:
            drug_pks_with_sim = {pk: sim for pk, sim in category_matches}
            drug_pks = list(drug_pks_with_sim.keys())
            
            # Get drugs
            drugs = (
                session.query(DrugORM.drug_id, DrugORM.name, DrugORM.description)
                .filter(DrugORM.id.in_(drug_pks))
                .all()
            )
            
            for drug_id, name, description in drugs:
                # Find the drug_pk to get similarity score
                drug_pk = session.query(DrugORM.id).filter(DrugORM.drug_id == drug_id).scalar()
                similarity = drug_pks_with_sim.get(drug_pk, 0.5)
                
                drug_map[drug_id] = {
                    "drug_id": drug_id,
                    "name": name,
                    "description": description,
                    "similarity": similarity,
                }
        
        # ===== SEMANTIC SEARCH (VECTOR) =====
        if request.include_semantic_search:
            logger.debug(f"[DRUG SERVICE] Performing semantic search for category")
            try:
                from .embedding_service import get_embedding_service
                embedding_service = get_embedding_service()
                
                # Semantic search
                semantic_results = embedding_service.search_similar_drugs(
                    query=request.category,
                    limit=request.limit * 2,
                    min_similarity=0.3
                )
                
                logger.debug(f"[DRUG SERVICE] Found {len(semantic_results)} semantic matches")
                
                semantic_weight = 0.85
                
                for drug_id, name, desc, sim in semantic_results:
                    weighted_sim = sim * semantic_weight
                    
                    if drug_id not in drug_map:
                        drug_map[drug_id] = {
                            "drug_id": drug_id,
                            "name": name,
                            "description": desc,
                            "similarity": weighted_sim,
                        }
                    else:
                        # Hybrid boost
                        existing_sim = drug_map[drug_id]["similarity"]
                        boosted_sim = max(existing_sim, weighted_sim) + 0.05
                        drug_map[drug_id]["similarity"] = min(1.0, boosted_sim)
                
                logger.info(f"[DRUG SERVICE] Hybrid category search: {len(drug_map)} total unique drugs")
                
            except Exception as e:
                logger.error(f"[DRUG SERVICE] Semantic search failed: {e}", exc_info=True)
        
        # Sort by similarity and limit
        sorted_results = sorted(
            drug_map.values(),
            key=lambda x: x["similarity"],
            reverse=True,
        )[:request.limit]
        
        drug_results = [
            DrugDescription(drug_id=r["drug_id"], name=r["name"], description=r["description"])
            for r in sorted_results
        ]
        
        logger.info(f"Found {len(drug_results)} drugs in category '{request.category}' (semantic: {request.include_semantic_search})")
        
        return DrugSearchByCategoryResponse(
            success=True,
            category=request.category,
            results=drug_results,
            count=len(drug_results),
        )
    
    except Exception as e:
        logger.error(f"Error searching by category: {e}", exc_info=True)
        return DrugSearchByCategoryResponse(
            success=False,
            category=request.category,
            results=[],
            count=0,
        )
    finally:
        session.close()

def get_alternative_drugs(current_drugs: List[str], for_drug_id: str) -> List[DrugAlternative]:
    """
    Find alternative drugs that don't interact with current medications.
    
    Args:
        current_drugs: List of current drug IDs
        for_drug_id: Drug ID to find alternatives for
    
    Returns:
        List[DrugAlternative]: Safe alternative drugs
    """
    session = get_session()
    try:
        # Get the drug to replace
        target_drug = _resolve_drug_id(session, for_drug_id)
        if not target_drug:
            logger.warning(f"Target drug not found: {for_drug_id}")
            return []
        
        # Get categories and indication
        categories = [c.category for c in target_drug.categories]
        indication = target_drug.indication
        
        # Find candidate drugs in same categories
        candidate_pks = set()
        for category in categories[:5]:  # Limit to top 5 categories
            cat_drugs = (
                session.query(DrugCategory.drug_pk)
                .filter(DrugCategory.category == category)
                .filter(DrugCategory.drug_pk != target_drug.id)
                .limit(20)
                .all()
            )
            candidate_pks.update(pk for (pk,) in cat_drugs)
        
        if not candidate_pks:
            return []
        
        # Get candidate drugs
        candidates = session.query(DrugORM).filter(DrugORM.id.in_(candidate_pks)).all()
        
        # Filter out drugs that interact with current medications
        alternatives = []
        for candidate in candidates:
            has_interaction = False
            
            for current_drug_id in current_drugs:
                current_drug = _resolve_drug_id(session, current_drug_id)
                if not current_drug:
                    continue
                
                # Check interaction
                interaction = (
                    session.query(DrugInteraction)
                    .filter(
                        or_(
                            (DrugInteraction.drug1_id == candidate.id)
                            & (DrugInteraction.drug2_drugbank_id == current_drug.drug_id),
                            (DrugInteraction.drug1_id == current_drug.id)
                            & (DrugInteraction.drug2_drugbank_id == candidate.drug_id),
                        )
                    )
                    .first()
                )
                
                if interaction:
                    severity = calculate_severity(interaction.description) # type: ignore
                    if severity > 0.5:  # Only filter out moderate+ interactions
                        has_interaction = True
                        break
            
            if not has_interaction:
                alternatives.append(
                    DrugAlternative(
                        old_drug_id=for_drug_id,
                        old_drug_name=target_drug.name, # type: ignore
                        new_drug_id=candidate.drug_id, # type: ignore
                        new_drug_name=candidate.name, # type: ignore
                        reason=f"Same therapeutic category, no significant interactions with current medications",
                    )
                )
        
        # Sort by approved status
        alternatives.sort(
            key=lambda a: (
                "approved" not in [g.group_name.lower() for g in session.query(DrugORM).filter(DrugORM.drug_id == a.new_drug_id).first().groups], # type: ignore
                a.new_drug_name,
            )
        )
        
        logger.info(f"Found {len(alternatives)} alternatives for {target_drug.name}")
        return alternatives[:10]  # Return top 10
    
    except Exception as e:
        logger.error(f"Error finding alternatives: {e}", exc_info=True)
        return []
    finally:
        session.close()


def analyze_patient(request: AnalyzePatientRequest) -> AnalyzePatientResponse:
    """
    Analyze patient's medications for interactions and provide recommendations.
    
    Args:
        request: Patient analysis request
    
    Returns:
        AnalyzePatientResponse: Complete analysis with interactions and alternatives
    """
    session = get_session()
    try:
        # Get patient
        patient = session.query(PatientRecord).filter(
            PatientRecord.patient_id == request.patient_id
        ).first()
        
        if not patient:
            logger.warning(f"Patient not found: {request.patient_id}")
            return AnalyzePatientResponse(
                patient_id=request.patient_id,
                current_drugs=[],
                interactions=[],
                count=0,
                safe_alternatives=[],
            )
        
        # Parse current medications
        current_meds = json.loads(patient.current_medications) if patient.current_medications else [] # type: ignore
        all_drug_ids = current_meds + request.additional_drug_ids
        
        if not all_drug_ids:
            return AnalyzePatientResponse(
                patient_id=request.patient_id,
                current_drugs=[],
                interactions=[],
                count=0,
                safe_alternatives=[],
            )
        
        # Get drug details
        drugs = session.query(DrugORM).filter(DrugORM.drug_id.in_(all_drug_ids)).all()
        drug_map = {d.drug_id: d for d in drugs}
        
        current_drug_bases = [
            _orm_to_drug_base(drug_map[drug_id])
            for drug_id in all_drug_ids
            if drug_id in drug_map
        ]
        
        # Check interactions
        interaction_request = CheckDrugInteractionRequest(drug_ids=all_drug_ids)
        interaction_response = check_drug_interactions(interaction_request)
        
        # Find alternatives for problematic drugs
        alternatives = []
        if interaction_response.interactions:
            # Find drugs involved in high-severity interactions
            problem_drugs = set()
            for interaction in interaction_response.interactions:
                if interaction.severity and interaction.severity > 0.6:
                    problem_drugs.add(interaction.drug1_id)
                    problem_drugs.add(interaction.drug2_id)
            
            # Get alternatives for each problem drug
            for problem_drug_id in problem_drugs:
                other_drugs = [d for d in all_drug_ids if d != problem_drug_id]
                drug_alternatives = get_alternative_drugs(other_drugs, problem_drug_id)
                alternatives.extend(drug_alternatives[:3])  # Top 3 per drug
        
        logger.info(f"Analyzed patient {request.patient_id}: {len(interaction_response.interactions)} interactions, {len(alternatives)} alternatives")
        
        return AnalyzePatientResponse(
            patient_id=request.patient_id,
            current_drugs=current_drug_bases,
            interactions=interaction_response.interactions,
            count=len(interaction_response.interactions),
            safe_alternatives=alternatives,
        )
    
    except Exception as e:
        logger.error(f"Error analyzing patient: {e}", exc_info=True)
        return AnalyzePatientResponse(
            patient_id=request.patient_id,
            current_drugs=[],
            interactions=[],
            count=0,
            safe_alternatives=[],
        )
    finally:
        session.close()


# ============================================================================
# 10. ANALYZE PATIENT FOOD INTERACTIONS
# ============================================================================

def analyze_patient_food_interactions(
    request: AnalyzePatientFoodInteractionsRequest
) -> AnalyzePatientFoodInteractionsResponse:
    """
    Analyze patient's medications for food interactions.
    
    Args:
        request: Patient food interaction analysis request
    
    Returns:
        AnalyzePatientFoodInteractionsResponse: Food interactions and recommendations
    """
    session = get_session()
    try:
        # Get patient
        patient = session.query(PatientRecord).filter(
            PatientRecord.patient_id == request.patient_id
        ).first()
        
        if not patient:
            logger.warning(f"Patient not found: {request.patient_id}")
            return AnalyzePatientFoodInteractionsResponse(
                patient_id=request.patient_id,
                current_drugs=[],
                interactions=[],
                count=0,
                safe_alternatives=[],
            )
        
        # Parse current medications
        current_meds = json.loads(patient.current_medications) if patient.current_medications else [] # type: ignore
        all_drug_ids = current_meds + request.additional_drug_ids
        
        if not all_drug_ids:
            return AnalyzePatientFoodInteractionsResponse(
                patient_id=request.patient_id,
                current_drugs=[],
                interactions=[],
                count=0,
                safe_alternatives=[],
            )
        
        # Get drug details
        drugs = session.query(DrugORM).filter(DrugORM.drug_id.in_(all_drug_ids)).all()
        drug_map = {d.drug_id: d for d in drugs}
        
        current_drug_bases = [
            _orm_to_drug_base(drug_map[drug_id])
            for drug_id in all_drug_ids
            if drug_id in drug_map
        ]
        
        # Get all food interactions
        all_food_interactions = []
        for drug_id in all_drug_ids:
            if drug_id in drug_map:
                drug = drug_map[drug_id]
                for fi in drug.food_interactions:
                    all_food_interactions.append(
                        DrugFoodInteractionModel(interaction=fi.interaction)
                    )
        
        logger.info(f"Found {len(all_food_interactions)} food interactions for patient {request.patient_id}")
        
        return AnalyzePatientFoodInteractionsResponse(
            patient_id=request.patient_id,
            current_drugs=current_drug_bases,
            interactions=all_food_interactions,
            count=len(all_food_interactions),
            safe_alternatives=[],  # Could implement alternative suggestions
        )
    
    except Exception as e:
        logger.error(f"Error analyzing patient food interactions: {e}", exc_info=True)
        return AnalyzePatientFoodInteractionsResponse(
            patient_id=request.patient_id,
            current_drugs=[],
            interactions=[],
            count=0,
            safe_alternatives=[],
        )
    finally:
        session.close()


# ============================================================================
# 11. CHECK OVERDOSE RISK (SAME ACTIVE INGREDIENT)
# ============================================================================

def check_overdose_risk(drug_ids: List[str]) -> CheckOverdoseRiskResponse:
    """
    Check if multiple drugs contain the same active ingredient, which could lead to overdose.
    
    This function checks for:
    1. Drugs that are actually the same drug (same drug_id)
    2. Drugs that share the same name or synonyms (e.g., Tylenol and Acetaminophen)
    3. Combination drugs that share common ingredients
    
    Args:
        drug_ids: List of drug IDs to check
    
    Returns:
        CheckOverdoseRiskResponse: Overdose risks found
    """
    logger.debug(f"[DRUG SERVICE] check_overdose_risk called with {len(drug_ids)} drugs: {drug_ids}")
    
    session = get_session()
    try:
        if len(drug_ids) < 2:
            logger.warning(f"[DRUG SERVICE] Insufficient drugs provided: {len(drug_ids)}")
            return CheckOverdoseRiskResponse(has_risk=False, risks=[], count=0)
        
        # Get all drugs with their synonyms and mixtures
        logger.debug(f"[DRUG SERVICE] Fetching drug records with synonyms and mixtures")
        drugs = (
            session.query(DrugORM)
            .options(
                joinedload(DrugORM.synonyms),
                joinedload(DrugORM.mixtures)
            )
            .filter(DrugORM.drug_id.in_(drug_ids))
            .all()
        )
        
        if len(drugs) < 2:
            logger.warning(f"[DRUG SERVICE] Only found {len(drugs)} drugs in database")
            return CheckOverdoseRiskResponse(has_risk=False, risks=[], count=0)
        
        logger.debug(f"[DRUG SERVICE] Found {len(drugs)} drugs in database")
        
        risks = []
        
        # Check all pairs
        for i, drug1 in enumerate(drugs):
            for drug2 in drugs[i + 1:]:
                # Build sets of all names/synonyms for each drug
                drug1_names = {drug1.name.lower()}
                drug1_names.update(s.synonym.lower() for s in drug1.synonyms)
                
                drug2_names = {drug2.name.lower()}
                drug2_names.update(s.synonym.lower() for s in drug2.synonyms)
                
                # Check if they share any names (indicating same active ingredient)
                shared_names = drug1_names & drug2_names
                
                if shared_names:
                    logger.info(f"[DRUG SERVICE] Overdose risk: {drug1.name} and {drug2.name} share names: {shared_names}")
                    risks.append(
                        OverdoseRiskDetail(
                            drug1_id=drug1.drug_id, # type: ignore
                            drug1_name=drug1.name, # type: ignore
                            drug2_id=drug2.drug_id, # type: ignore
                            drug2_name=drug2.name, # type: ignore
                            reason=f"These are the same medication under different names. Taking both could result in an overdose.",
                            shared_ingredients=list(shared_names),
                        )
                    )
                    continue
                
                # Check if combination drugs share ingredients
                if drug1.mixtures and drug2.mixtures:
                    for mix1 in drug1.mixtures:
                        for mix2 in drug2.mixtures:
                            if mix1.ingredients and mix2.ingredients:
                                # Parse ingredients (comma-separated)
                                ingredients1 = {ing.strip().lower() for ing in mix1.ingredients.split(',')}
                                ingredients2 = {ing.strip().lower() for ing in mix2.ingredients.split(',')}
                                
                                shared_ingredients = ingredients1 & ingredients2
                                
                                if shared_ingredients:
                                    logger.info(f"[DRUG SERVICE] Overdose risk: {drug1.name} and {drug2.name} share ingredients: {shared_ingredients}")
                                    risks.append(
                                        OverdoseRiskDetail(
                                            drug1_id=drug1.drug_id, # type: ignore
                                            drug1_name=drug1.name, # type: ignore
                                            drug2_id=drug2.drug_id, # type: ignore
                                            drug2_name=drug2.name, # type: ignore
                                            reason=f"These combination medications contain the same active ingredient(s). Taking both could result in an overdose.",
                                            shared_ingredients=list(shared_ingredients),
                                        )
                                    )
                                    break
        
        logger.info(f"[DRUG SERVICE] Found {len(risks)} overdose risks among {len(drug_ids)} drugs")
        
        return CheckOverdoseRiskResponse(
            has_risk=len(risks) > 0,
            risks=risks,
            count=len(risks),
        )
    
    except Exception as e:
        logger.error(f"[DRUG SERVICE] Error checking overdose risk: {e}", exc_info=True)
        return CheckOverdoseRiskResponse(has_risk=False, risks=[], count=0)
    finally:
        session.close()
