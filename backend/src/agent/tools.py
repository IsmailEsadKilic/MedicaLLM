import threading
from contextvars import ContextVar
from typing import Annotated, Literal, Optional
from langchain_core.tools import tool

from ..drugs import service as drug_service
from ..drugs.models import (
    DrugSearchRequest,
    CheckDrugInteractionRequest,
    DrugSearchByIndicationRequest,
    DrugSearchByCategoryRequest,
    AnalyzePatientRequest,
)
from ..pubmed import service as pubmed_service
from ..pubmed.models import PubMedSearchResult
from ..pubmed.service import extract_relevant_snippet
from ..pubmed.scoring import get_quality_warnings

from logging import getLogger

logger = getLogger(__name__)

# ============================================================================
# Cross-thread source & debug propagation
# ============================================================================

# ContextVar writes inside LangChain tool functions do NOT propagate back to
# the caller when LangChain runs synchronous tools in a thread-pool (which is
# the default for ``agent.astream()``).  The child thread receives a *copy* of
# the parent context, so reads work but writes are isolated.

# Fix: tools READ a ``_request_id_var`` (copied to the thread) and WRITE
# results into a plain thread-safe dict keyed by that request ID.  After the
# agent call the caller pops the results from the dict.

_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)

# Shared stores — dict operations are atomic under CPython's GIL; we add a
# lock for belt-and-suspenders safety on pop-with-default.
_store_lock = threading.Lock()
_source_store: dict[str, list] = {}
_debug_store: dict[str, dict] = {}

# Legacy ContextVar kept for backward-compatibility with ``handle_user_query``
# (non-streaming path) where tool and caller share the same context.
_last_search_sources_var: ContextVar[list | None] = ContextVar(
    "last_search_sources", default=None
)
_last_tool_debug_var: ContextVar[dict | None] = ContextVar(
    "last_tool_debug", default=None
)

# Stores the authenticated user's ID so agent tools can perform
# user-scoped lookups without exposing the ID to the LLM.
_current_user_id_var: ContextVar[str | None] = ContextVar(
    "current_user_id", default=None
)

# Stores the current patient ID for patient-scoped operations
_current_patient_id_var: ContextVar[str | None] = ContextVar(
    "current_patient_id", default=None
)


def set_request_id(request_id: str) -> None:
    """Set a unique request ID for the current coroutine.

    Must be called before each agent invocation so that tools (which may run in
    a thread-pool) can read it and write results into the shared stores.
    """
    _request_id_var.set(request_id)


def _store_sources(sources: Optional[list], tool_name: str = "unknown") -> None:
    """Append sources into both the shared dict (for streaming) and the
    ContextVar (for the non-streaming path).  Multiple tool calls in the
    same request accumulate sources instead of overwriting."""
    if sources is None:
        return
    # Tag each source with the originating tool
    for s in sources:
        s.setdefault("tool", tool_name)
    # ContextVar path (non-streaming)
    existing_cv = _last_search_sources_var.get()
    if existing_cv is None:
        _last_search_sources_var.set(list(sources))
    else:
        existing_cv.extend(sources)
    # Shared-dict path (streaming)
    rid = _request_id_var.get()
    if rid is not None:
        with _store_lock:
            existing = _source_store.get(rid)
            if existing is None:
                _source_store[rid] = list(sources)
            else:
                existing.extend(sources)


def _store_debug(debug: Optional[dict]) -> None:
    """Write debug info into both the shared dict and the ContextVar."""
    _last_tool_debug_var.set(debug)
    rid = _request_id_var.get()
    if rid is not None:
        with _store_lock:
            _debug_store[rid] = debug # type: ignore


def get_last_search_sources(request_id: Optional[str] = None):
    """
    Return and clear the search sources for the given request.

    When *request_id* is provided (streaming path) the shared dict is used,
    falling back to the ContextVar for the non-streaming path.
    """
    if request_id is not None:
        with _store_lock:
            sources = _source_store.pop(request_id, None)
        if sources is not None:
            return sources
    # Fallback: non-streaming path where tool and caller share context
    sources = _last_search_sources_var.get()
    _last_search_sources_var.set(None)
    return sources or []


def get_last_tool_debug(request_id: Optional[str] = None) -> Optional[dict]:
    """Return and clear debug info for the given request."""
    if request_id is not None:
        with _store_lock:
            debug = _debug_store.pop(request_id, None)
        if debug is not None:
            return debug
    debug = _last_tool_debug_var.get()
    _last_tool_debug_var.set(None)
    return debug


def set_current_user_id(user_id: str) -> None:
    """Store the authenticated user ID in the current coroutine context."""
    _current_user_id_var.set(user_id)


def get_current_user_id() -> Optional[str]:
    """Return the authenticated user ID stored for the current coroutine."""
    return _current_user_id_var.get()


def set_current_patient_id(patient_id: str | None) -> None:
    """Store the current patient ID in the current coroutine context."""
    _current_patient_id_var.set(patient_id)


def get_current_patient_id() -> Optional[str]:
    """Return the current patient ID stored for the current coroutine."""
    return _current_patient_id_var.get()


# ============================================================================
# Helper: Resolve drug name to drug_id
# ============================================================================

def _resolve_drug_name_to_id(drug_name: str, semantic_search: bool = False) -> Optional[str]:
    """
    Resolve a drug name (or synonym/brand) to a DrugBank ID using search.
    Returns the best match drug_id or None if not found.
    """
    try:
        request = DrugSearchRequest(
            query=drug_name,
            limit=1,
            min_similarity=0.3,
            include_synonyms=True,
            include_products=True,
            include_brands=True,
            include_semantic_search=semantic_search
        )
        response = drug_service.search_drugs(request)
        
        if response.success and response.results:
            drug_id = response.results[0].drug_id
            logger.info(f"Resolved '{drug_name}' to drug_id: {drug_id}")
            return drug_id
        else:
            logger.warning(f"Could not resolve drug name: {drug_name}")
            return None
    except Exception as e:
        logger.error(f"Error resolving drug name '{drug_name}': {e}")
        return None


def _resolve_drug_names_to_ids(drug_names: list[str], semantic_search: bool = False) -> list[str]:
    """
    Resolve multiple drug names to drug IDs.
    Returns list of resolved drug_ids (skips unresolved names).
    """
    drug_ids = []
    for name in drug_names:
        drug_id = _resolve_drug_name_to_id(name, semantic_search=semantic_search)
        if drug_id:
            drug_ids.append(drug_id)
    return drug_ids

# ============================================================================
# TOOL 1: Get Drug Information
# ============================================================================

@tool
def get_drug_info(
    drug_name: Annotated[str, "Name of the drug (e.g., Warfarin, Metformin, Aspirin)"],
    detail: Annotated[
        Literal["low", "moderate", "high"],
        "Level of detail: 'low' for basic info, 'moderate' for standard clinical info, 'high' for comprehensive data including targets/enzymes/carriers"
    ] = "moderate",
    semantic_search: Annotated[bool, "Whether to use semantic search for drug name resolution. Use if the exact drug name is not given."] = False,
) -> str:
    """
    Get information about a specific drug from the database.

    Use this when the user asks about:
    - What a drug is or what it does
    - Drug indications (what it treats)
    - How a drug works (mechanism of action)
    - Side effects or toxicity
    - Pharmacokinetics (absorption, metabolism, half-life, etc.)
    - Drug properties and characteristics

    Examples:
    - "What is Warfarin?"
    - "Tell me about Metformin"
    - "What are the side effects of Aspirin?"
    - "How does Lisinopril work?"
    """
    try:
        logger.debug(f"[TOOL] get_drug_info called with drug_name='{drug_name}', detail='{detail}'")
        logger.info(f"get_drug_info: drug_name='{drug_name}', detail='{detail}'")
        
        # Resolve drug name to ID
        logger.debug(f"[TOOL] Resolving drug name '{drug_name}' to drug_id")
        drug_id = _resolve_drug_name_to_id(drug_name, semantic_search=semantic_search)
        if not drug_id:
            logger.warning(f"[TOOL] Drug not found: {drug_name}")
            return f"Drug not found: {drug_name}. Try a different name or spelling."
        
        logger.debug(f"[TOOL] Resolved '{drug_name}' to drug_id: {drug_id}")
        
        # Get drug information with specified detail level
        logger.debug(f"[TOOL] Fetching drug information for {drug_id} with detail level: {detail}")
        drug = drug_service.get_drug(drug_id, detail=detail)
        if not drug:
            logger.warning(f"[TOOL] Drug information not available for: {drug_name} ({drug_id})")
            return f"Drug information not available for: {drug_name}"
        
        # Build response based on detail level
        logger.debug(f"[TOOL] Building response for {drug.name} with detail level: {detail}")
        parts = [f"**{drug.name}** ({drug.drug_id})"]
        
        # Low detail: DrugDescription (drug_id, name, description)
        if detail == "low":
            if drug.description:
                desc = drug.description[:300]
                if len(drug.description) > 300:
                    desc += "..."
                parts.append(f"\nDescription: {desc}")
            return "\n".join(parts)
        
        # Moderate detail: DrugBase (+ drug_type, indication, mechanism, pharmacodynamics, synonyms)
        if detail == "moderate":
            #if hasattr(drug, 'synonyms') and drug.synonyms:
            synonyms = getattr(drug, 'synonyms', None)
            if synonyms:
                parts.append(f"Also known as: {', '.join(synonyms[:5])}")
            
            drug_type = getattr(drug, 'drug_type', None)
            if drug_type:
                parts.append(f"Type: {drug_type}")

            description = getattr(drug, 'description', None)
            if description:
                parts.append(f"\nDescription: {description}")
            
            indication = getattr(drug, 'indication', None)
            if indication:
                parts.append(f"\nIndication: {indication}")
            
            mechanism_of_action = getattr(drug, 'mechanism_of_action', None)
            if mechanism_of_action:
                parts.append(f"\nMechanism of Action: {mechanism_of_action}")
            
            pharmacodynamics = getattr(drug, 'pharmacodynamics', None)
            if pharmacodynamics:
                parts.append(f"\nPharmacodynamics: {pharmacodynamics}")
            
            return "\n".join(parts)
        
        # High detail: Full Drug model with all relationships
        synonyms = getattr(drug, 'synonyms', None)
        if synonyms:
            parts.append(f"Also known as: {', '.join(synonyms[:5])}")
        
        drug_type = getattr(drug, 'drug_type', None)
        if drug_type:
            parts.append(f"Type: {drug_type}")
        
        groups = getattr(drug, 'groups', None)
        if groups:
            parts.append(f"Status: {', '.join(groups)}")
        
        description = getattr(drug, 'description', None)
        if description:
            parts.append(f"\nDescription: {description}")
        
        indication = getattr(drug, 'indication', None)
        if indication:
            parts.append(f"\nIndication: {indication}")
        
        mechanism_of_action = getattr(drug, 'mechanism_of_action', None)
        if mechanism_of_action:
            parts.append(f"\nMechanism of Action: {mechanism_of_action}")
        
        pharmacodynamics = getattr(drug, 'pharmacodynamics', None)
        if pharmacodynamics:
            parts.append(f"\nPharmacodynamics: {pharmacodynamics}")
        
        toxicity = getattr(drug, 'toxicity', None)
        if toxicity:
            parts.append(f"\nToxicity/Side Effects: {toxicity}")
        
        metabolism = getattr(drug, 'metabolism', None)
        if metabolism:
            parts.append(f"\nMetabolism: {metabolism}")
        
        absorption = getattr(drug, 'absorption', None)
        if absorption:
            parts.append(f"\nAbsorption: {absorption}")
        
        half_life = getattr(drug, 'half_life', None)
        if half_life:
            parts.append(f"\nHalf-life: {half_life}")
        
        protein_binding = getattr(drug, 'protein_binding', None)
        if protein_binding:
            parts.append(f"\nProtein Binding: {protein_binding}")
        
        route_of_elimination = getattr(drug, 'route_of_elimination', None)
        if route_of_elimination:
            parts.append(f"\nRoute of Elimination: {route_of_elimination}")
        
        volume_of_distribution = getattr(drug, 'volume_of_distribution', None)
        if volume_of_distribution:
            parts.append(f"\nVolume of Distribution: {volume_of_distribution}")
        
        clearance = getattr(drug, 'clearance', None)
        if clearance:
            parts.append(f"\nClearance: {clearance}")
        
        categories = getattr(drug, 'categories', None)
        if categories:
            parts.append(f"\nCategories: {', '.join(categories[:10])}")
        
        food_interactions = getattr(drug, 'food_interactions', None)
        if food_interactions:
            parts.append(f"\nFood Interactions ({len(food_interactions)}): {'; '.join(food_interactions[:5])}")
        
        targets = getattr(drug, 'targets', None)
        if targets:
            parts.append(f"\nTargets ({len(targets)}): {', '.join([t.get('name', 'Unknown') for t in targets[:5]])}") # type: ignore
        
        enzymes = getattr(drug, 'enzymes', None)
        if enzymes:
            parts.append(f"\nEnzymes ({len(enzymes)}): {', '.join([e.get('name', 'Unknown') for e in enzymes[:5]])}") # type: ignore
        
        carriers = getattr(drug, 'carriers', None)
        if carriers:
            parts.append(f"\nCarriers ({len(carriers)}): {', '.join([c.get('name', 'Unknown') for c in carriers[:5]])}") # type: ignore
        
        transporters = getattr(drug, 'transporters', None)
        if transporters:
            parts.append(f"\nTransporters ({len(transporters)}): {', '.join([t.get('name', 'Unknown') for t in transporters[:5]])}") # type: ignore
        
        return "\n".join(parts)
        
    except Exception as e:
        logger.error(f"Error in get_drug_info for '{drug_name}': {e}", exc_info=True)
        return f"Error retrieving drug information: {str(e)}"


# ============================================================================
# TOOL 2: Check Drug Interactions
# ============================================================================

@tool
def check_drug_interactions(
    drug_names: Annotated[list[str], "List of drug names to check for interactions (minimum 2 drugs)"],
    semantic_search: Annotated[bool, "Whether to use semantic search for drug name resolution. Use if the exact drug name is not given."] = False
) -> str:
    """
    Check for interactions between multiple drugs.

    Use this when the user asks about:
    - Drug-drug interactions
    - Safety of combining medications
    - Whether multiple drugs can be taken together

    Examples:
    - "Do Warfarin and Ibuprofen interact?"
    - "Check interactions between Lisinopril, Aspirin, and Metformin"
    - "Are there any interactions in this drug list?"
    """
    try:
        logger.debug(f"[TOOL] check_drug_interactions called with {len(drug_names)} drugs: {drug_names}")
        logger.info(f"check_drug_interactions: drug_names={drug_names}")
        
        if len(drug_names) < 2:
            return "Please provide at least 2 drugs to check for interactions."
        
        # Resolve drug names to IDs
        logger.debug(f"[TOOL] Resolving {len(drug_names)} drug names to IDs")
        drug_ids = _resolve_drug_names_to_ids(drug_names, semantic_search=semantic_search)
        logger.debug(f"[TOOL] Resolved {len(drug_ids)} drug IDs: {drug_ids}")
        
        if len(drug_ids) < 2:
            logger.warning(f"[TOOL] Insufficient drugs resolved: {len(drug_ids)} out of {len(drug_names)}")
            return f"Could not resolve enough drug names. Found: {len(drug_ids)} out of {len(drug_names)} drugs."
        
        # Check interactions
        logger.debug(f"[TOOL] Checking interactions for drug_ids: {drug_ids}")
        request = CheckDrugInteractionRequest(drug_ids=drug_ids)
        response = drug_service.check_drug_interactions(request)
        logger.debug(f"[TOOL] Found {response.count} interactions")
        
        if response.count == 0:
            return (
                f"No documented interactions found between: {', '.join(drug_names)}. "
                "However, always inform your healthcare provider about all medications you're taking."
            )
        
        # Build response
        parts = [f"Found {response.count} interaction(s):\n"]
        
        # Sort by severity (highest first)
        sorted_interactions = sorted(
            response.interactions,
            key=lambda x: x.severity if x.severity else 0.5,
            reverse=True
        )
        
        for i, interaction in enumerate(sorted_interactions, 1):
            severity_label = "UNKNOWN"
            severity_icon = "⚠️"
            
            if interaction.severity is not None:
                if interaction.severity >= 0.8:
                    severity_label = "MAJOR"
                    severity_icon = "🔴"
                elif interaction.severity >= 0.5:
                    severity_label = "MODERATE"
                    severity_icon = "🟠"
                else:
                    severity_label = "MINOR"
                    severity_icon = "🟡"
            
            parts.append(
                f"{i}. {severity_icon} **{interaction.drug1_name}** + **{interaction.drug2_name}** "
                f"[{severity_label}]"
            )
            parts.append(f"   {interaction.description}")
            parts.append("")
        
        if response.overall_severity and response.overall_severity >= 0.6:
            parts.append(
                "⚠️ **IMPORTANT**: High-severity interactions detected. "
                "Consult with a healthcare provider before taking these medications together."
            )
        
        return "\n".join(parts)
        
    except Exception as e:
        logger.error(f"Error in check_drug_interactions: {e}", exc_info=True)
        return f"Error checking drug interactions: {str(e)}"


# ============================================================================
# TOOL 3: Check Drug-Food Interactions
# ============================================================================

@tool
def check_drug_food_interaction(
    drug_name: Annotated[str, "Name of the drug to check for food interactions"],
    food_items: Annotated[list[str], "List of food items to check (optional, if empty returns all food interactions)"] = [],
    semantic_search: Annotated[bool, "Whether to use semantic search for drug name resolution. Use if the exact drug name is not given."] = False
) -> str:
    """
    Check if a drug has any food interactions or dietary restrictions.

    Use this when the user asks about:
    - Food interactions with a drug
    - What to eat or avoid while taking a medication
    - Dietary restrictions for a drug
    - Whether to take a drug with or without food

    Examples:
    - "Can I eat grapefruit with Warfarin?"
    - "Should I take Metformin with food?"
    - "Are there any food restrictions for Lisinopril?"
    """
    try:
        logger.info(f"check_drug_food_interaction: drug_name='{drug_name}', food_items={food_items}")
        
        # Resolve drug name to ID
        drug_id = _resolve_drug_name_to_id(drug_name, semantic_search=semantic_search)
        if not drug_id:
            return f"Drug not found: {drug_name}. Try a different name or spelling."
        
        # Get food interactions
        interactions = drug_service.check_drug_food_interactions(drug_id)
        
        if not interactions:
            return (
                f"No specific food interactions are documented for {drug_name} in our database. "
                "This doesn't mean there are no interactions. Always consult your healthcare "
                "provider or pharmacist about dietary considerations."
            )
        
        # Build response
        parts = [f"Food Interactions for **{drug_name}**:\n"]
        parts.append(f"Found {len(interactions)} food interaction(s):\n")
        
        for i, interaction in enumerate(interactions, 1):
            interaction_text = interaction.interaction
            
            # If specific food items provided, highlight relevant ones
            if food_items:
                is_relevant = any(
                    food.lower() in interaction_text.lower()
                    for food in food_items
                )
                if is_relevant:
                    parts.append(f"{i}. ⚠️ **{interaction_text}**")
                else:
                    parts.append(f"{i}. {interaction_text}")
            else:
                parts.append(f"{i}. {interaction_text}")
        
        parts.append(
            "\nAlways follow your healthcare provider's instructions regarding food and medication timing."
        )
        
        return "\n".join(parts)
        
    except Exception as e:
        logger.error(f"Error in check_drug_food_interaction for '{drug_name}': {e}", exc_info=True)
        return f"Error checking food interactions: {str(e)}"


# ============================================================================
# TOOL 4: Search Drugs by Indication
# ============================================================================

@tool
def search_drugs_by_indication(
    condition: Annotated[str, "Medical condition or indication (e.g., diabetes, hypertension, pain)"],
    semantic_search: Annotated[bool, "Whether to use semantic search. Use True for conceptual queries like 'high blood pressure' to match 'hypertension'."] = False,
) -> str:
    """
    Search for drugs that treat a specific medical condition.

    Use this when the user asks about:
    - What drugs treat a condition
    - Medications for a specific disease
    - Treatment options for a medical condition

    Examples:
    - "What drugs treat diabetes?"
    - "Medications for hypertension"
    - "What can be used for migraine?"
    """
    try:
        logger.info(f"search_drugs_by_indication: condition='{condition}', semantic_search={semantic_search}")
        
        request = DrugSearchByIndicationRequest(
            indication=condition, 
            limit=20,
            include_semantic_search=semantic_search
        )
        response = drug_service.search_drugs_by_indication(request)
        
        if not response.success or response.count == 0:
            return (
                f"No drugs found for indication '{condition}'. "
                "Try different keywords or check the spelling."
            )
        
        parts = [f"Found {response.count} drug(s) for **{condition}**:\n"]
        
        for i, drug in enumerate(response.results[:10], 1):
            parts.append(f"{i}. **{drug.name}** ({drug.drug_id})")
            if drug.description:
                desc_snippet = drug.description[:150]
                if len(drug.description) > 150:
                    desc_snippet += "..."
                parts.append(f"   {desc_snippet}")
            parts.append("")
        
        if response.count > 10:
            parts.append(f"... and {response.count - 10} more drugs.")
        
        parts.append("Consult your healthcare provider before starting any medication.")
        
        return "\n".join(parts)
        
    except Exception as e:
        logger.error(f"Error in search_drugs_by_indication for '{condition}': {e}", exc_info=True)
        return f"Error searching drugs by indication: {str(e)}"


# ============================================================================
# TOOL 5: Search Drugs by Category
# ============================================================================

@tool
def search_drugs_by_category(
    category: Annotated[str, "Therapeutic category (e.g., antibiotic, antidepressant, antihypertensive)"],
    semantic_search: Annotated[bool, "Whether to use semantic search. Use True for conceptual queries to find related drug categories."] = False,
) -> str:
    """
    Search for drugs in a specific therapeutic category.

    Use this when the user asks about:
    - Drugs in a therapeutic class
    - Types of medications (e.g., antibiotics, antidepressants)
    - Drug categories

    Examples:
    - "List antibiotics"
    - "What are some antidepressants?"
    - "Show me antihypertensive drugs"
    """
    try:
        logger.info(f"search_drugs_by_category: category='{category}', semantic_search={semantic_search}")
        
        request = DrugSearchByCategoryRequest(
            category=category, 
            limit=20,
            include_semantic_search=semantic_search
        )
        response = drug_service.search_drugs_by_category(request)
        
        if not response.success or response.count == 0:
            return (
                f"No drugs found in category '{category}'. "
                "Try different keywords like 'antibiotic', 'antidepressant', or 'analgesic'."
            )
        
        parts = [f"Found {response.count} drug(s) in category **{category}**:\n"]
        
        for i, drug in enumerate(response.results[:10], 1):
            parts.append(f"{i}. **{drug.name}** ({drug.drug_id})")
            if drug.description:
                desc_snippet = drug.description[:150]
                if len(drug.description) > 150:
                    desc_snippet += "..."
                parts.append(f"   {desc_snippet}")
            parts.append("")
        
        if response.count > 10:
            parts.append(f"... and {response.count - 10} more drugs.")
        
        return "\n".join(parts)
        
    except Exception as e:
        logger.error(f"Error in search_drugs_by_category for '{category}': {e}", exc_info=True)
        return f"Error searching drugs by category: {str(e)}"


# ============================================================================
# TOOL 6: Recommend Alternative Drug
# ============================================================================

@tool
def recommend_alternative_drug(
    current_drug_names: Annotated[list[str], "List of current drugs the patient is taking"],
    for_drug_name: Annotated[str, "The drug to find alternatives for"],
    semantic_search: Annotated[bool, "Whether to use semantic search for drug name resolution. Use if the exact drug name is not given."] = False,
) -> str:
    """
    Find alternative drugs that don't interact with current medications.

    Use this when:
    - An interaction is found and a safer substitute is needed
    - The user asks for alternatives to a drug
    - A patient needs a replacement medication

    Examples:
    - "What can I use instead of Warfarin for a patient also on Aspirin?"
    - "Suggest alternatives to Metformin"
    - "Find a safer alternative for this patient"
    """
    try:
        logger.info(f"recommend_alternative_drug: current_drugs={current_drug_names}, for_drug='{for_drug_name}', semantic_search={semantic_search}")
        
        # Resolve drug names to IDs
        current_drug_ids = _resolve_drug_names_to_ids(current_drug_names, semantic_search=semantic_search)
        for_drug_id = _resolve_drug_name_to_id(for_drug_name, semantic_search=semantic_search)
        
        if not for_drug_id:
            return f"Could not find drug: {for_drug_name}"
        
        # Get alternatives
        alternatives = drug_service.get_alternative_drugs(current_drug_ids, for_drug_id)
        
        if not alternatives:
            return (
                f"No safe alternatives found for {for_drug_name} that don't interact with "
                f"the current medications: {', '.join(current_drug_names)}."
            )
        
        parts = [f"Alternative drugs for **{for_drug_name}**:\n"]
        parts.append(f"Found {len(alternatives)} safe alternative(s):\n")
        
        for i, alt in enumerate(alternatives, 1):
            parts.append(f"{i}. **{alt.new_drug_name}** ({alt.new_drug_id})")
            parts.append(f"   Reason: {alt.reason}")
            parts.append("")
        
        parts.append(
            "NOTE: These alternatives have no documented interactions with the listed medications. "
            "Always confirm with a healthcare provider before switching medications."
        )
        
        return "\n".join(parts)
        
    except Exception as e:
        logger.error(f"Error in recommend_alternative_drug: {e}", exc_info=True)
        return f"Error finding alternative drugs: {str(e)}"


# ============================================================================
# TOOL 7: Check for Overdose Risk (Same Active Ingredient)
# ============================================================================

@tool
def check_for_overdose_interaction(
    drug_names: Annotated[list[str], "List of drug names to check for overdose risk (minimum 2 drugs)"],
    semantic_search: Annotated[bool, "Whether to use semantic search for drug name resolution. Use if the exact drug name is not given."] = False
) -> str:
    """
    Check if multiple drugs contain the same active ingredient, which could lead to overdose.

    Use this when the user asks about:
    - Risk of taking multiple medications together
    - Whether drugs contain the same ingredient
    - Overdose risk from drug combinations
    - Duplicate therapy concerns

    Examples:
    - "Can I take Tylenol and Paracetamol together?"
    - "Do these medications have the same active ingredient?"
    - "Is there an overdose risk with these drugs?"
    """
    try:
        logger.debug(f"[TOOL] check_for_overdose_interaction called with {len(drug_names)} drugs: {drug_names}")
        logger.info(f"check_for_overdose_interaction: drug_names={drug_names}")
        
        if len(drug_names) < 2:
            return "Please provide at least 2 drugs to check for overdose risk."
        
        # Resolve drug names to IDs
        logger.debug(f"[TOOL] Resolving {len(drug_names)} drug names to IDs")
        drug_ids = _resolve_drug_names_to_ids(drug_names, semantic_search=semantic_search)
        logger.debug(f"[TOOL] Resolved {len(drug_ids)} drug IDs: {drug_ids}")
        
        if len(drug_ids) < 2:
            logger.warning(f"[TOOL] Insufficient drugs resolved: {len(drug_ids)} out of {len(drug_names)}")
            return f"Could not resolve enough drug names. Found: {len(drug_ids)} out of {len(drug_names)} drugs."
        
        # Check for overdose risks
        logger.debug(f"[TOOL] Checking for overdose risks among drug_ids: {drug_ids}")
        from ..drugs import service as drug_service
        response = drug_service.check_overdose_risk(drug_ids)
        
        if not response.has_risk:
            return (
                f"No overdose risk detected among: {', '.join(drug_names)}. "
                "These drugs do not appear to contain the same active ingredients. "
                "However, always inform your healthcare provider about all medications you're taking."
            )
        
        # Build response
        parts = [f"⚠️ **OVERDOSE RISK DETECTED** ⚠️\n"]
        parts.append(f"Found {len(response.risks)} potential overdose risk(s):\n")
        
        for i, risk in enumerate(response.risks, 1):
            parts.append(f"{i}. 🔴 **{risk.drug1_name}** and **{risk.drug2_name}**")
            parts.append(f"   Reason: {risk.reason}")
            if risk.shared_ingredients:
                parts.append(f"   Shared ingredients: {', '.join(risk.shared_ingredients)}")
            parts.append("")
        
        parts.append(
            "⚠️ **CRITICAL WARNING**: Taking these medications together may result in "
            "an overdose due to duplicate active ingredients. Consult with a healthcare "
            "provider immediately before taking these medications together."
        )
        
        return "\n".join(parts)
        
    except Exception as e:
        logger.error(f"Error in check_for_overdose_interaction: {e}", exc_info=True)
        return f"Error checking overdose risk: {str(e)}"


# ============================================================================
# TOOL 8: Analyze Patient Medications
# ============================================================================

@tool
def analyze_patient_medications(
    additional_drugs: Annotated[list[str], "Additional drug names to analyze along with patient's current medications"] = [],
    semantic_search: Annotated[bool, "Whether to use semantic search for drug name resolution. Use if the exact drug name is not given."] = False,
) -> str:
    """
    Perform a comprehensive medication safety analysis for the current patient.

    This tool:
    1. Loads the patient's full profile (medications, allergies, conditions)
    2. Checks all drug-drug interactions
    3. Checks drug-food interactions
    4. Provides safe alternatives if needed

    Use this when the user asks to:
    - Analyze a patient's medications
    - Check if a patient's drug regimen is safe
    - Review all interactions for a patient
    - Add new medications to a patient's regimen

    Examples:
    - "Analyze this patient's medications"
    - "Check for interactions in the patient's drug list"
    - "Can I add Aspirin to this patient's medications?"
    """
    try:
        # Get patient ID from context
        patient_id = get_current_patient_id()
        if not patient_id:
            return (
                "No patient context available. Please select a patient first or provide a patient ID."
            )
        
        logger.info(f"analyze_patient_medications: patient_id='{patient_id}', additional_drugs={additional_drugs}, semantic_search={semantic_search}")
        
        # Resolve additional drug names to IDs
        additional_drug_ids = _resolve_drug_names_to_ids(additional_drugs, semantic_search=semantic_search) if additional_drugs else []
        
        # Analyze patient
        request = AnalyzePatientRequest(
            patient_id=patient_id,
            additional_drug_ids=additional_drug_ids
        )
        response = drug_service.analyze_patient(request)
        
        # Build response
        parts = [f"**Medication Safety Analysis for Patient {response.patient_id}**\n"]
        
        if response.current_drugs:
            parts.append(f"Current Medications ({len(response.current_drugs)}):")
            for drug in response.current_drugs:
                parts.append(f"  - {drug.name} ({drug.drug_id})")
            parts.append("")
        
        if response.count == 0:
            parts.append("✅ No drug-drug interactions detected.")
        else:
            parts.append(f"⚠️ Found {response.count} interaction(s):\n")
            
            # Sort by severity
            sorted_interactions = sorted(
                response.interactions,
                key=lambda x: x.severity if x.severity else 0.5,
                reverse=True
            )
            
            for i, interaction in enumerate(sorted_interactions, 1):
                severity_label = "UNKNOWN"
                severity_icon = "⚠️"
                
                if interaction.severity is not None:
                    if interaction.severity >= 0.8:
                        severity_label = "MAJOR"
                        severity_icon = "🔴"
                    elif interaction.severity >= 0.5:
                        severity_label = "MODERATE"
                        severity_icon = "🟠"
                    else:
                        severity_label = "MINOR"
                        severity_icon = "🟡"
                
                parts.append(
                    f"{i}. {severity_icon} **{interaction.drug1_name}** + **{interaction.drug2_name}** "
                    f"[{severity_label}]"
                )
                parts.append(f"   {interaction.description}")
                parts.append("")
        
        if response.safe_alternatives:
            parts.append(f"\n**Safe Alternatives** ({len(response.safe_alternatives)}):\n")
            for alt in response.safe_alternatives:
                parts.append(f"  - Replace **{alt.old_drug_name}** with **{alt.new_drug_name}**")
                parts.append(f"    Reason: {alt.reason}")
                parts.append("")
        
        return "\n".join(parts)
        
    except Exception as e:
        logger.error(f"Error in analyze_patient_medications: {e}", exc_info=True)
        return f"Error analyzing patient medications: {str(e)}"


def _extract_relevant_snippet(query: str, abstract: str, max_len: int = 400) -> str:
    """Extract the most query-relevant sentences from an abstract."""
    if not abstract:
        return ""
    sentences = abstract.replace(". ", ".\n").split("\n")
    query_terms = set(query.lower().split())
    stopwords = {"the", "a", "an", "in", "on", "of", "for", "and", "or", "to", "with"}
    query_terms -= stopwords

    scored = []
    for sent in sentences:
        overlap = sum(1 for t in query_terms if t in sent.lower())
        scored.append((overlap, sent.strip()))

    scored.sort(key=lambda x: x[0], reverse=True)

    result = ""
    for _, sent in scored:
        if len(result) + len(sent) + 2 <= max_len:
            result += sent + " "
        else:
            break
    return result.strip() or abstract[:max_len]


@tool
def search_pubmed(
    query: Annotated[
        str,
        "Medical research query for PubMed. MUST be in English. Use MeSH terms when possible (e.g., 'heart failure' not 'kalp yetmezliği'). Combine terms with AND/OR for precision.",
    ],
    num_articles: Annotated[
        int, "Number of articles to retrieve (default: 5, max: 20)"
    ] = 5,
) -> str:
    """
    Search PubMed for published medical research articles and clinical studies.

    Use this when the user asks about:
    - Recent medical research or clinical studies
    - Evidence-based medicine or scientific evidence
    - Published papers on a medical topic
    - "What does the research say about..."
    - Literature review or scientific findings
    - Clinical trials or study results

    Examples:
    - "What research exists on metformin and longevity?"
    - "Find studies about SGLT2 inhibitors in heart failure"
    - "What does the literature say about statin side effects?"
    - "Recent research on mRNA vaccines"
    - "Give me 20 articles about COVID-19 vaccines" (uses num_articles=20)
    """
    # Validate and cap num_articles
    num_articles = max(1, min(num_articles, 20))
    logger.debug(f"[TOOL] search_pubmed called with query='{query}', num_articles={num_articles}")

    # Reject non-English queries (Turkish character check)
    turkish_chars = set("çğıöşüÇĞİÖŞÜ")
    if any(c in turkish_chars for c in query):
        logger.warning(f"[TOOL] Non-English query rejected: {query}")
        return "ERROR: PubMed query must be in English. Please rephrase your search in English using medical terminology."

    debug_info = {
        "cache_hit": False,
        "articles_fetched": 0,
        "num_articles_requested": num_articles,
    }

    try:
        logger.info(f"PubMed search for: {query}")
        logger.debug(f"[TOOL] Calling pubmed_service.search_pubmed with max_results={num_articles}")

        # Use new PubMed service that returns PubMedSearchResult
        # Fetch extra articles upstream so the relevance gate has candidates to pick from
        fetch_count = max(num_articles, 15)
        result: PubMedSearchResult = pubmed_service.search_pubmed(
            query=query,
            max_results=fetch_count,
            min_confidence=45.0,  # raised from 35 → 45
        )
        
        logger.debug(f"[TOOL] PubMed search completed: {len(result.articles)} articles, search_time={result.search_time_ms}ms")
        
        debug_info["articles_fetched"] = len(result.articles)
        debug_info["avg_confidence"] = result.avg_confidence
        debug_info["filtered_count"] = result.filtered_count
        debug_info["search_time_ms"] = result.search_time_ms

        if not result.articles:
            logger.warning(f"[TOOL] No PubMed articles found for query: {query}")
            _store_sources(None, tool_name="search_pubmed")
            _store_debug(debug_info)
            return "No PubMed articles found for your query. Try different or broader search terms."

        # Hard relevance gate: drop articles whose relevance_score < 0.45
        # (relevance_score is stored as 0-1 float derived from the 0-100 breakdown)
        MIN_RELEVANCE = 0.45
        high_relevance = [a for a in result.articles if a.relevance_score >= MIN_RELEVANCE]
        if not high_relevance:
            # Fall back to top article by confidence when nothing clears the gate
            high_relevance = result.articles[:1]
            logger.warning(
                f"[TOOL] No articles cleared relevance gate ({MIN_RELEVANCE}) for '{query}'; "
                f"using top confidence article as fallback"
            )

        # Cap the number of articles passed to the LLM context at 3
        MAX_CONTEXT_ARTICLES = min(num_articles, 3)
        context_articles = high_relevance[:MAX_CONTEXT_ARTICLES]

        # If the only surviving article is weak, tell the LLM explicitly
        all_weak = all(a.relevance_score < MIN_RELEVANCE for a in context_articles)
        if all_weak:
            logger.warning(f"[TOOL] All surviving articles have low relevance for query: {query}")
            _store_sources(None, tool_name="search_pubmed")
            _store_debug(debug_info)
            return (
                "No high-quality directly relevant evidence was found on PubMed for this specific query. "
                "The available articles address adjacent topics but do not directly answer the question. "
                "Please acknowledge this limitation in your response and avoid making claims from "
                "non-specific sources."
            )

        # Articles are already scored and sorted by the service
        logger.info(
            f"Retrieved {len(result.articles)} articles, {len(high_relevance)} passed relevance gate, "
            f"using {len(context_articles)} in context (avg confidence: {result.avg_confidence:.1f})"
        )
        logger.debug(f"[TOOL] Context article PMIDs: {[a.pmid for a in context_articles]}")

        # Build response for LLM
        search_sources: list = []
        result_parts = [
            "RETRIEVED PUBMED ARTICLES (sorted by confidence score, highest first):",
            "IMPORTANT: Only cite articles that DIRECTLY address the user's question.",
            "Every factual claim MUST include a [REF#] citation.",
            "",
        ]

        for i, article in enumerate(context_articles, 1):
            # Get quality warnings using new scoring module
            warnings = get_quality_warnings(
                confidence_score=article.confidence_score,
                relevance_score=article.relevance_score,
                publication_date=article.publication_date,
                abstract=article.abstract
            )
            
            result_parts.append(f"[Article {i} — REF{i}]")
            result_parts.append(f"Title: {article.title}")
            if article.journal:
                result_parts.append(f"Journal: {article.journal}")
            if article.publication_date:
                result_parts.append(f"Published: {article.publication_date}")
            if article.pmid:
                result_parts.append(f"PMID: {article.pmid}")
            if article.doi:
                result_parts.append(f"DOI: https://doi.org/{article.doi}")
            result_parts.append(f"Confidence Score: {article.confidence_score}/100")
            if article.publication_types:
                result_parts.append(f"Study Type: {', '.join(article.publication_types)}")
            
            breakdown = article.confidence_breakdown
            result_parts.append(
                f"Score Breakdown — Citations: {breakdown.get('citations', 0)}, "
                f"Recency: {breakdown.get('recency', 0)}, "
                f"Evidence Level: {breakdown.get('evidence_level', 0)}, "
                f"Relevance: {breakdown.get('relevance', 0)}"
            )

            if warnings:
                result_parts.append("WARNINGS: " + "; ".join(warnings))

            result_parts.append(f"Abstract: {article.abstract}")
            result_parts.append("")

            source_entry = {
                "ref": f"REF{i}",
                "source": f"PubMed — {article.journal}" if article.journal else "PubMed",
                "pmid": article.pmid,
                "pmc_id": article.pmc_id,
                "title": article.title,
                "url": article.get_url(),
                "citations": article.citation_count,
                "citation_count": article.citation_count,  # Add both for compatibility
                "confidence_score": article.confidence_score,
                "confidence_breakdown": article.confidence_breakdown,
                "study_type": ", ".join(article.publication_types) if article.publication_types else "Unknown",
                "content": extract_relevant_snippet(query, article.abstract),
                "tool": "search_pubmed",
                "warnings": warnings,
                "doi": article.doi,
                # Add full article data for abstract viewer fallback
                "abstract": article.abstract,
                "authors": article.authors,
                "journal": article.journal,
                "publication_date": article.publication_date,
                "pubmed_url": article.get_url(),
                "doi_url": article.get_doi_url() if article.doi else "",
            }
            search_sources.append(source_entry)

        # Add citation instructions
        result_parts.extend([
            "=" * 60,
            "RESPONSE FORMAT:",
            "- Provide a structured answer; do NOT flatten all evidence into a single sentence.",
            "- Cite EVERY factual claim with [REF#].",
            "- Example: 'Estrogen-alone therapy is associated with LOWER breast cancer risk [REF1],'",
            "  'whereas combined estrogen+progestin therapy raises it [REF2].'",
            "- If articles study different populations or therapy subtypes, present each strand separately.",
            "- If an article's scope does not match the user's specific subgroup (e.g., general population",
            "  vs. women with family history), note that gap explicitly.",
            "- End with a 'Limitations' section noting what the sources don't cover.",
            "=" * 60,
        ])

        _store_sources(search_sources, tool_name="search_pubmed")
        _store_debug(debug_info)
        return "\n".join(result_parts)

    except Exception as e:
        logger.error(f"Error searching PubMed for '{query}': {str(e)}")
        _store_debug(debug_info)
        return f"Error searching PubMed: {str(e)}"


# ============================================================================
# TOOL 9: Multi-Query PubMed Search
# ============================================================================

def _build_pubmed_response(
    queries: list[str],
    articles,
    avg_confidence: float,
    sources_tool_name: str = "search_pubmed_multi",
) -> str:
    """Shared helper to format a list of PubMedArticle objects into LLM context."""
    MIN_RELEVANCE = 0.45
    high_relevance = [a for a in articles if a.relevance_score >= MIN_RELEVANCE]
    if not high_relevance:
        high_relevance = articles[:1] if articles else []

    MAX_CONTEXT = 5  # multi-query allows up to 5 across all sub-queries
    context_articles = high_relevance[:MAX_CONTEXT]

    if not context_articles:
        return (
            "No high-quality directly relevant evidence was found on PubMed for these queries. "
            "Please acknowledge this limitation in your response."
        )

    search_sources: list = []
    result_parts = [
        f"RETRIEVED PUBMED ARTICLES for queries: {' | '.join(queries)}",
        "IMPORTANT: Only cite articles that DIRECTLY address the user's question.",
        "Every factual claim MUST include a [REF#] citation.",
        "",
    ]

    combined_query = " ".join(queries)
    for i, article in enumerate(context_articles, 1):
        warnings = get_quality_warnings(
            confidence_score=article.confidence_score,
            relevance_score=article.relevance_score,
            publication_date=article.publication_date,
            abstract=article.abstract,
        )
        result_parts.append(f"[Article {i} — REF{i}]")
        result_parts.append(f"Title: {article.title}")
        if article.journal:
            result_parts.append(f"Journal: {article.journal}")
        if article.publication_date:
            result_parts.append(f"Published: {article.publication_date}")
        if article.pmid:
            result_parts.append(f"PMID: {article.pmid}")
        if article.doi:
            result_parts.append(f"DOI: https://doi.org/{article.doi}")
        result_parts.append(f"Confidence Score: {article.confidence_score}/100")
        if article.publication_types:
            result_parts.append(f"Study Type: {', '.join(article.publication_types)}")
        breakdown = article.confidence_breakdown
        result_parts.append(
            f"Score Breakdown — Citations: {breakdown.get('citations', 0)}, "
            f"Recency: {breakdown.get('recency', 0)}, "
            f"Evidence Level: {breakdown.get('evidence_level', 0)}, "
            f"Relevance: {breakdown.get('relevance', 0)}"
        )
        if warnings:
            result_parts.append("WARNINGS: " + "; ".join(warnings))
        result_parts.append(f"Abstract: {article.abstract}")
        result_parts.append("")

        search_sources.append({
            "ref": f"REF{i}",
            "source": f"PubMed — {article.journal}" if article.journal else "PubMed",
            "pmid": article.pmid,
            "pmc_id": article.pmc_id,
            "title": article.title,
            "url": article.get_url(),
            "citations": article.citation_count,
            "citation_count": article.citation_count,
            "confidence_score": article.confidence_score,
            "confidence_breakdown": article.confidence_breakdown,
            "study_type": ", ".join(article.publication_types) if article.publication_types else "Unknown",
            "content": extract_relevant_snippet(combined_query, article.abstract),
            "tool": sources_tool_name,
            "warnings": warnings,
            "doi": article.doi,
            "abstract": article.abstract,
            "authors": article.authors,
            "journal": article.journal,
            "publication_date": article.publication_date,
            "pubmed_url": article.get_url(),
            "doi_url": article.get_doi_url() if article.doi else "",
        })

    result_parts.extend([
        "=" * 60,
        "RESPONSE FORMAT:",
        "- Present each evidence strand separately when sub-queries produced different findings.",
        "- Cite EVERY factual claim with [REF#].",
        "- If studies differ by therapy subtype, population, or follow-up duration, state each separately.",
        "- End with a 'Limitations' section noting scope gaps.",
        "=" * 60,
    ])

    _store_sources(search_sources, tool_name=sources_tool_name)
    return "\n".join(result_parts)


@tool
def search_pubmed_multi(
    queries: Annotated[
        list[str],
        (
            "List of 2–3 focused English PubMed sub-queries targeting different facets of the same "
            "clinical question. Each query should be specific (e.g., 'estrogen-only HRT breast cancer risk' "
            "and 'combined estrogen progestin HRT breast cancer risk family history'). Max 3 queries."
        ),
    ],
) -> str:
    """
    Search PubMed with multiple targeted sub-queries and return merged, deduplicated results.

    Use this tool instead of search_pubmed when:
    - The question involves multiple distinct clinical facets (e.g., two different therapy types,
      two different patient populations, or conflicting evidence streams)
    - A single broad query would return low-relevance articles
    - You need to distinguish between treatment subtypes (e.g., estrogen-alone vs. combined HRT)
    - The user asks about risk/safety where evidence differs by subgroup

    Examples:
    - Query: "Is HRT safe after breast cancer?"
      sub-queries: ["estrogen-only HRT breast cancer recurrence risk", "combined HRT breast cancer recurrence risk"]
    - Query: "Does aspirin prevent heart attacks?"
      sub-queries: ["aspirin primary prevention cardiovascular events", "aspirin secondary prevention myocardial infarction"]
    """
    if not queries or len(queries) < 2:
        return "Please provide at least 2 sub-queries for multi-query search."

    # Enforce English (Turkish char check on all queries)
    turkish_chars = set("çğıöşüÇĞİÖŞÜ")
    for q in queries:
        if any(c in turkish_chars for c in q):
            return "ERROR: All PubMed queries must be in English."

    queries = queries[:3]
    logger.info(f"[TOOL] search_pubmed_multi: {len(queries)} sub-queries: {queries}")

    debug_info = {"sub_queries": queries, "cache_hit": False}

    try:
        result = pubmed_service.search_pubmed_multi(
            queries=queries,
            max_per_query=8,
            min_confidence=45.0,
        )

        debug_info["articles_fetched"] = len(result.articles)
        debug_info["avg_confidence"] = result.avg_confidence
        _store_debug(debug_info)

        if not result.articles:
            _store_sources(None, tool_name="search_pubmed_multi")
            return (
                "No PubMed articles found across all sub-queries. "
                "Try broader or different search terms."
            )

        return _build_pubmed_response(
            queries=queries,
            articles=result.articles,
            avg_confidence=result.avg_confidence,
            sources_tool_name="search_pubmed_multi",
        )

    except Exception as exc:
        logger.error(f"[TOOL] search_pubmed_multi failed: {exc}", exc_info=True)
        _store_debug(debug_info)
        return f"Error in multi-query PubMed search: {str(exc)}"


ALL_TOOLS = [
    get_drug_info,
    check_drug_interactions,
    check_drug_food_interaction,
    search_drugs_by_indication,
    search_drugs_by_category,
    recommend_alternative_drug,
    check_for_overdose_interaction,
    analyze_patient_medications,
    search_pubmed,
    search_pubmed_multi,
]
