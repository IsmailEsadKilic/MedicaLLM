import threading
from contextvars import ContextVar
from typing import Annotated, Optional
from langchain_core.tools import tool

from ..drugs import service as drug_service
from ..pubmed import service as pubmed_service
from .. import printmeup as pm

# ---------------------------------------------------------------------------
# Cross-thread source & debug propagation
# ---------------------------------------------------------------------------
# ContextVar writes inside LangChain tool functions do NOT propagate back to
# the caller when LangChain runs synchronous tools in a thread-pool (which is
# the default for ``agent.astream()``).  The child thread receives a *copy* of
# the parent context, so reads work but writes are isolated.
#
# Fix: tools READ a ``_request_id_var`` (copied to the thread) and WRITE
# results into a plain thread-safe dict keyed by that request ID.  After the
# agent call the caller pops the results from the dict.
# ---------------------------------------------------------------------------

_request_id_var: ContextVar[Optional[str]] = ContextVar(
    "request_id", default=None
)

# Shared stores — dict operations are atomic under CPython's GIL; we add a
# lock for belt-and-suspenders safety on pop-with-default.
_store_lock = threading.Lock()
_source_store: dict[str, Optional[list]] = {}
_debug_store: dict[str, Optional[dict]] = {}

# Legacy ContextVar kept for backward-compatibility with ``handle_user_query``
# (non-streaming path) where tool and caller share the same context.
_last_search_sources_var: ContextVar[Optional[list]] = ContextVar(
    "last_search_sources", default=None
)
_last_tool_debug_var: ContextVar[Optional[dict]] = ContextVar(
    "last_tool_debug", default=None
)
# O10: stores the authenticated user's ID so agent tools can perform
# user-scoped DynamoDB lookups without exposing the ID to the LLM.
_current_user_id_var: ContextVar[Optional[str]] = ContextVar(
    "current_user_id", default=None
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
            _debug_store[rid] = debug


def get_last_search_sources(request_id: Optional[str] = None):
    """Return and clear the search sources for the given request.

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
    return sources


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
    """Store the authenticated user ID in the current coroutine context (O10)."""
    _current_user_id_var.set(user_id)


def get_current_user_id_ctx() -> Optional[str]:
    """Return the authenticated user ID stored for the current coroutine (O10)."""
    return _current_user_id_var.get()


# ============================================================
# TOOL 1: Drug Information Lookup
# ============================================================

@tool
def get_drug_info(
    drug_name: Annotated[str, "Name of the drug (e.g., Warfarin, Metformin, Aspirin)"],
) -> str:
    """
    Get comprehensive information about a specific drug from the database.

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
        pm.inf(f"Looking up drug: {drug_name}")
        result = drug_service.get_drug_info(drug_name)

        if not result.get("success"):
            return f"Drug not found: {drug_name}"

        parts = []
        drug_name_display = result["drug_name"]
        if result.get("is_synonym"):
            parts.append(f"{result['queried_name']} (also known as {result['actual_name']})")
        else:
            parts.append(drug_name_display)

        for field, label in [
            ("indication", "Indication"),
            ("mechanism_of_action", "Mechanism"),
            ("toxicity", "Side effects/toxicity"),
            ("metabolism", "Metabolism"),
            ("half_life", "Half-life"),
        ]:
            val = result.get(field, "N/A")
            if val != "N/A":
                parts.append(f"{label}: {val}")

        return " | ".join(parts)
    except Exception as e:
        pm.err(e=e, m=f"Error in get_drug_info for '{drug_name}'")
        return f"Error retrieving drug information: {str(e)}"


# ============================================================
# TOOL 2: Drug Interaction Check
# ============================================================

@tool
def check_drug_interaction(
    drug1: Annotated[str, "First drug name"],
    drug2: Annotated[str, "Second drug name"],
) -> str:
    """
    Check if two drugs have a known interaction.

    Use this when the user asks about:
    - Drug-drug interactions
    - Safety of combining medications
    - Whether two drugs can be taken together

    Examples:
    - "Does Warfarin interact with Ibuprofen?"
    - "Can I take Lisinopril with Aspirin?"
    - "Are there any interactions between Metformin and Glipizide?"
    """
    try:
        pm.inf(f"check_drug_interaction: drug1='{drug1}', drug2='{drug2}'")
        result = drug_service.check_drug_interaction(drug1, drug2)

        if not result.get("success"):
            return f"Error checking interaction: {result.get('error', 'Unknown error')}"

        if result.get("interaction_found"):
            severity = result.get("severity", "moderate")
            return (
                f"Yes, {result['drug1']} and {result['drug2']} do interact. "
                f"Severity: {severity.upper()}. "
                f"{result['description']} It's important to consult with a healthcare "
                f"provider before taking these medications together."
            )
        else:
            return (
                f"No documented interaction found between {result['drug1']} and "
                f"{result['drug2']}. However, always inform your healthcare provider "
                f"about all medications you're taking."
            )
    except Exception as e:
        pm.err(e=e, m=f"Error checking interaction between '{drug1}' and '{drug2}'")
        return f"Error checking interaction: {str(e)}"


# ============================================================
# TOOL 3: Drug-Food Interaction Check
# ============================================================

@tool
def check_drug_food_interaction(
    drug_name: Annotated[str, "Name of the drug"],
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
        pm.inf(f"Checking food interactions for: {drug_name}")
        result = drug_service.get_drug_food_interactions(drug_name)

        if not result.get("success"):
            return f"Error checking food interactions: {result.get('error', 'Unknown error')}"

        if result.get("count", 0) > 0:
            interactions = result["interactions"]
            response = [f"Food Interactions for {result['drug_name']}:", f"Found {result['count']} food interaction(s):\n"]
            for i, interaction in enumerate(interactions, 1):
                response.append(f"{i}. {interaction}")
            response.append("\nAlways follow your healthcare provider's instructions regarding food and medication timing.")
            return "\n".join(response)
        else:
            return (
                f"No specific food interactions are documented for {result['drug_name']} "
                f"in our database. This doesn't mean there are no interactions. Always "
                f"consult your healthcare provider or pharmacist about dietary considerations."
            )
    except Exception as e:
        pm.err(e=e, m=f"Error checking food interactions for '{drug_name}'")
        return f"Error checking food interactions: {str(e)}"


# ============================================================
# TOOL 4: Search Drugs by Category/Indication
# ============================================================

@tool
def search_drugs_by_indication(
    condition: Annotated[str, "Medical condition or therapeutic category (e.g., diabetes, hypertension, pain)"],
) -> str:
    """
    Search for drugs that treat a specific condition or belong to a therapeutic category.

    Use this when the user asks about:
    - What drugs treat a condition
    - Alternative medications for a condition
    - Drug recommendations for a specific disease

    Examples:
    - "What drugs treat diabetes?"
    - "Recommend alternatives for hypertension"
    - "What medications are available for pain?"
    """
    try:
        pm.inf(f"Searching drugs for condition: {condition}")
        result = drug_service.search_drugs_by_category(condition, limit=10)

        if not result.get("success"):
            return f"Error searching drugs: {result.get('error', 'Unknown error')}"

        if result.get("count", 0) == 0:
            return f"No drugs found for '{condition}'. Try different keywords like 'diabetes', 'hypertension', or 'pain'."

        drugs = result["drugs"]
        response = [f"Found {result['count']} drug(s) for {condition}:\n"]
        for i, drug in enumerate(drugs, 1):
            response.append(f"{i}. {drug['name']}")
            if drug.get("categories"):
                response.append(f"   Categories: {', '.join(drug['categories'])}")
            if drug.get("indication") and drug["indication"] != "N/A":
                indication = drug["indication"][:150]
                if len(drug["indication"]) > 150:
                    indication += "..."
                response.append(f"   Indication: {indication}")
            response.append("")

        response.append("Consult your healthcare provider before starting any medication.")
        return "\n".join(response)
    except Exception as e:
        pm.err(e=e, m=f"Error searching drugs for '{condition}'")
        return f"Error searching drugs: {str(e)}"


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


# ============================================================
# TOOL 5: PubMed Literature Search
# ============================================================

@tool
def search_pubmed(
    query: Annotated[str, "Medical research query for PubMed. MUST be in English. Use MeSH terms when possible (e.g., 'heart failure' not 'kalp yetmezliği'). Combine terms with AND/OR for precision."],
    num_articles: Annotated[int, "Number of articles to retrieve (default: 5, max: 20)"] = 5,
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

    # Reject non-English queries (Turkish character check)
    turkish_chars = set("çğıöşüÇĞİÖŞÜ")
    if any(c in turkish_chars for c in query):
        return "ERROR: PubMed query must be in English. Please rephrase your search in English using medical terminology."
    
    debug_info = {
        "cache_hit": False,
        "articles_fetched": 0,
        "num_articles_requested": num_articles,
    }

    try:
        pm.inf(f"PubMed search for: {query}")

        # Cache disabled — always fetch fresh results from NCBI E-utilities
        # to ensure latest scoring/filtering logic is applied.
        articles = pubmed_service.search_pubmed(query, max_results=num_articles)
        debug_info["articles_fetched"] = len(articles)

        if not articles:
            _store_sources(None)
            _store_debug(debug_info)
            return "No PubMed articles found for your query. Try different or broader search terms."

        # Step 4: Enrich with citation counts and compute confidence scores
        pubmed_service.enrich_articles_with_citations(articles)
        articles = pubmed_service.compute_confidence_scores(articles, query=query)
        articles = pubmed_service.sort_articles_by_confidence(articles)
        debug_info["confidence_scoring"] = True

        # Filter out very low-confidence articles (keep at least 2)
        _CONFIDENCE_THRESHOLD = 35.0
        if len(articles) > 2:
            above = [a for a in articles if a.get("confidence_score", 0) >= _CONFIDENCE_THRESHOLD]
            if len(above) >= 2:
                dropped = len(articles) - len(above)
                if dropped:
                    pm.inf(f"Filtered {dropped} articles below {_CONFIDENCE_THRESHOLD} confidence")
                articles = above
            # else keep all — not enough quality articles to filter

        # Hard cap: never send more than 5 articles to the LLM
        articles = articles[:5]
        pm.inf(f"Sending {len(articles)} articles to LLM (scores: {[a.get('confidence_score', 0) for a in articles]})")

        # Return raw structured articles for the agent's LLM to synthesize (O1: single LLM call)
        search_sources: list = []
        result_parts = [
            "RETRIEVED PUBMED ARTICLES (sorted by confidence score, highest first):",
            "IMPORTANT: Only cite articles that DIRECTLY address the user's question.",
            "If an article is tangentially related but does not address the core question, note it as 'not directly relevant' and do NOT use its data in your answer.",
            "Do NOT add any clinical claims, guideline recommendations, or statistics that are not explicitly stated in these abstracts.",
            "",
        ]

        for i, article in enumerate(articles, 1):
            title = article.get("title", "Untitled")
            abstract = article.get("abstract", "No abstract available.")
            journal = article.get("journal", "")
            date = article.get("publication_date", "")
            pmid = article.get("pmid", "")
            doi = article.get("doi", "")
            citations = article.get("citation_count", 0)
            confidence = article.get("confidence_score", 0)
            breakdown = article.get("confidence_breakdown", {})
            pub_types = breakdown.get("publication_types", [])

            result_parts.append(f"[Article {i} — REF{i}]")
            result_parts.append(f"Title: {title}")
            if journal:
                result_parts.append(f"Journal: {journal}")
            if date:
                result_parts.append(f"Published: {date}")
            if pmid:
                result_parts.append(f"PMID: {pmid}")
            if doi:
                result_parts.append(f"DOI: https://doi.org/{doi}")
            result_parts.append(f"Citations: {citations}")
            result_parts.append(f"Confidence Score: {confidence}/100")
            if pub_types:
                result_parts.append(f"Study Type: {', '.join(pub_types)}")
            result_parts.append(f"Score Breakdown — Citations: {breakdown.get('citations', 0)}, Recency: {breakdown.get('recency', 0)}, Evidence Level: {breakdown.get('evidence_level', 0)}, Relevance: {breakdown.get('relevance', 0)}")

            # Data fidelity warnings
            warnings = []
            relevance_score = breakdown.get("relevance", 50)
            if relevance_score < 40:
                warnings.append(f"⚠ LOW RELEVANCE ({relevance_score}/100) — this article may not directly address the user's query. Only cite if truly relevant.")
            if date:
                try:
                    pub_year = int(date[:4])
                    from datetime import datetime as _dt
                    article_age = _dt.now().year - pub_year
                    if article_age > 20:
                        warnings.append(f"⚠ OLD ARTICLE ({pub_year}, {article_age} years ago) — cite with caution, note age limitation")
                    elif article_age > 10:
                        warnings.append(f"⚠ Article is {article_age} years old — check for more recent evidence")
                except (ValueError, IndexError):
                    pass
            if confidence < 35:
                warnings.append(f"⚠ LOW CONFIDENCE ({confidence}/100) — weak evidence")
            if not abstract or abstract == "No abstract available.":
                warnings.append("⚠ NO ABSTRACT — cannot verify content, do not cite")
            if warnings:
                result_parts.append("WARNINGS: " + "; ".join(warnings))

            result_parts.append(f"Abstract: {abstract}")
            result_parts.append("")

            source_entry = {
                "ref": f"REF{i}",
                "source": f"PubMed — {journal}" if journal else "PubMed",
                "pmid": pmid,
                "title": title,
                "citations": citations,
                "confidence_score": confidence,
                "study_type": ", ".join(pub_types) if pub_types else "Unknown",
                "content": _extract_relevant_snippet(query, abstract),
                "tool": "search_pubmed",
            }
            search_sources.append(source_entry)

        # Post-article instruction block — positioned LAST so the LLM sees it
        # immediately before generating its response (recency bias).
        result_parts.append("=" * 60)
        result_parts.append("YOUR RESPONSE MUST FOLLOW THIS EXACT TEMPLATE:")
        result_parts.append("")
        result_parts.append("## Short Answer")
        result_parts.append("[Write 2-3 sentences directly answering the question. Cite with [REF1], [REF2] etc.]")
        result_parts.append("")
        result_parts.append("## Evidence Summary")
        result_parts.append("[For each relevant article above, summarize its KEY FINDING in 2-3 sentences.")
        result_parts.append("Every sentence MUST include a [REF] number. Use a markdown table if citing 3+ articles.]")
        result_parts.append("")
        result_parts.append("## Limitations")
        result_parts.append("[State what the retrieved sources do NOT cover. Example: 'The retrieved literature does not address specific dosing recommendations, BRCA mutation carriers, or non-hormonal alternatives.']")
        result_parts.append("")
        result_parts.append("STOP AFTER THE LIMITATIONS SECTION. DO NOT WRITE ANYTHING ELSE.")
        result_parts.append("DO NOT add: clinical recommendations, decision frameworks, practical guidance,")
        result_parts.append("drug dosages, screening protocols, alternative therapy lists, bottom line sections,")
        result_parts.append("key references sections, or any content not from the abstracts above.")
        result_parts.append("Any sentence without a [REF] number (except in Limitations) will be deleted.")
        result_parts.append("=" * 60)

        _store_sources(search_sources, tool_name="search_pubmed")
        _store_debug(debug_info)
        return "\n".join(result_parts)

    except Exception as e:
        pm.err(e=e, m=f"Error searching PubMed for '{query}'")
        _store_debug(debug_info)
        return f"Error searching PubMed: {str(e)}"


# ============================================================
# TOOL 7: Alternative Drug Recommendation (O9)
# ============================================================

@tool
def recommend_alternative_drug(
    drug_name: Annotated[str, "Name of the drug to find alternatives for"],
    reason: Annotated[str, "Why an alternative is needed (e.g., interaction, allergy, contraindication)"],
    patient_medications: Annotated[list[str], "List of other drugs the patient is currently taking, to filter out alternatives that interact with them"] = [],
) -> str:
    """
    Recommend safer alternative drugs when a medication causes an interaction,
    allergy, or contraindication.

    Use this when:
    - An interaction or contraindication is found and a safer substitute is needed
    - The user asks for alternatives to a drug
    - A patient is allergic to a drug and needs a replacement
    - You need to suggest drugs in the same therapeutic class

    Examples:
    - "What can I use instead of Warfarin for a patient also on Aspirin?"
    - "My patient is allergic to Penicillin, suggest alternatives"
    - "Are there safer alternatives to Metformin for this patient?"
    """
    try:
        pm.inf(f"recommend_alternative_drug: drug='{drug_name}', reason='{reason}', patient_meds={patient_medications}")
        result = drug_service.get_alternative_drugs(drug_name, patient_medications)

        if not result.get("success"):
            return f"Could not find alternatives for {drug_name}: {result.get('error', 'Unknown error')}"

        original = result["original_drug"]
        alternatives = result.get("alternatives", [])
        original_indication = result.get("original_indication", "N/A")
        original_categories = result.get("original_categories", [])
        patient_meds_checked = result.get("patient_medications_checked", [])

        if not alternatives:
            return (
                f"No safe alternatives found for {original}. "
                f"The search checked {result.get('total_candidates_checked', 0)} candidates "
                f"from the same therapeutic category but all had interactions with the patient's "
                f"current medications ({', '.join(patient_meds_checked) if patient_meds_checked else 'none provided'})."
            )

        parts = [
            f"ALTERNATIVE DRUG RECOMMENDATIONS FOR: {original}",
            f"Reason for replacement: {reason}",
            f"Original indication: {original_indication[:200] if original_indication and original_indication != 'N/A' else 'N/A'}",
            f"Original categories: {', '.join(original_categories[:5]) if original_categories else 'N/A'}",
        ]
        if patient_meds_checked:
            parts.append(f"Patient medications checked for interactions: {', '.join(patient_meds_checked)}")
        parts.append(f"\nFound {len(alternatives)} safe alternative(s):\n")

        for i, alt in enumerate(alternatives, 1):
            parts.append(f"{i}. {alt['name']}")
            if alt.get("categories"):
                parts.append(f"   Categories: {', '.join(alt['categories'][:3])}")
            if alt.get("indication") and alt["indication"] != "N/A":
                indication_snippet = alt["indication"][:160]
                if len(alt["indication"]) > 160:
                    indication_snippet += "..."
                parts.append(f"   Indication: {indication_snippet}")
            if alt.get("groups"):
                parts.append(f"   Status: {', '.join(alt['groups'][:3])}")
            parts.append("")

        parts.append(
            "NOTE: These alternatives share the same therapeutic purpose and have no documented "
            "interactions with the patient's listed medications. Always confirm with a "
            "healthcare provider before switching medications."
        )
        return "\n".join(parts)
    except Exception as e:
        pm.err(e=e, m=f"Error in recommend_alternative_drug for '{drug_name}'")
        return f"Error finding alternative drugs: {str(e)}"


# ============================================================
# TOOL 8: Analyze Patient Medications (O10)
# ============================================================

@tool
def analyze_patient_medications(
    patient_id: Annotated[str, "The patient's unique ID to retrieve their full medication profile"],
) -> str:
    """
    Perform a comprehensive medication safety analysis for a specific patient.

    This tool:
    1. Loads the patient's full profile from the database (medications, allergies, conditions).
    2. Checks every pairwise drug-drug interaction among the patient's current medications.
    3. Cross-references each medication against the patient's known allergies.
    4. Returns a structured safety report sorted by severity.

    Use this when the user asks to:
    - Analyse a patient's medications
    - Check if a patient's drug regimen is safe
    - Find potential conflicts in a patient's medication list
    - Review all interactions for a patient

    Examples:
    - "Analyse the medications for patient P-123"
    - "Are there any drug interactions for this patient?"
    - "Check the medication safety profile for my patient"
    """
    from ..users import service as patient_service
    from itertools import combinations

    try:
        pm.inf(f"Analysing medications for patient {patient_id}")
        healthcare_professional_id = get_current_user_id_ctx()
        if not healthcare_professional_id:
            return "Unable to perform analysis: user context not available."

        patient = patient_service.get_patient(
            healthcare_professional_id=healthcare_professional_id,
            patient_id=patient_id,
        )
        if not patient:
            return f"Patient not found: {patient_id}"

        name = patient.get("name", "Unknown")
        medications: list = patient.get("current_medications", [])
        allergies: list = patient.get("allergies", [])
        conditions: list = patient.get("chronic_conditions", [])

        if not medications:
            return (
                f"Patient {name} has no current medications recorded. "
                "No interaction analysis is possible."
            )

        lines: list[str] = [
            f"MEDICATION SAFETY REPORT — {name}",
            f"Chronic Conditions: {', '.join(conditions) if conditions else 'None'}",
            f"Known Allergies: {', '.join(allergies) if allergies else 'None'}",
            f"Current Medications ({len(medications)}): {', '.join(medications)}",
            "",
        ]

        # ── Pairwise drug-drug interactions ───────────────────────────────
        pairs = list(combinations(medications, 2))
        interaction_lines: list[tuple[int, str]] = []  # (severity_order, line)
        for drug1, drug2 in pairs:
            try:
                result = drug_service.check_drug_interaction(drug1, drug2)
                if result.get("interaction_found"):
                    severity = result.get("severity", "moderate")
                    sev_label = severity.upper()
                    sev_icon = {
                        "contraindicated": "🚫",
                        "major": "🔴",
                        "moderate": "🟠",
                        "minor": "🟡",
                    }.get(severity, "⚠")
                    line = (
                        f"  {sev_icon} [{sev_label}] {drug1} + {drug2}: "
                        f"{result.get('description', 'Interaction detected')}"
                    )
                    order = drug_service.SEVERITY_ORDER.get(severity, 3)
                    interaction_lines.append((order, line))
            except Exception:
                pass  # skip individual pair errors

        # Sort by severity: contraindicated first, then major, moderate, minor
        interaction_lines.sort(key=lambda x: x[0])

        if interaction_lines:
            lines.append(f"DRUG-DRUG INTERACTIONS ({len(interaction_lines)} found, sorted by severity):")
            lines.extend(line for _, line in interaction_lines)
        else:
            lines.append("DRUG-DRUG INTERACTIONS: None detected among current medications.")
        lines.append("")

        # ── Allergy cross-reference ────────────────────────────────────────
        allergy_flags: list[str] = []
        if allergies:
            for med in medications:
                med_lower = med.lower()
                for allergy in allergies:
                    if allergy.lower() in med_lower or med_lower in allergy.lower():
                        allergy_flags.append(
                            f"  🚨 {med} may be related to documented allergy: {allergy}"
                        )

        if allergy_flags:
            lines.append(f"ALLERGY CONFLICTS ({len(allergy_flags)} flagged):")
            lines.extend(allergy_flags)
        else:
            lines.append("ALLERGY CONFLICTS: No direct conflicts detected.")
        lines.append("")

        # ── Summary ────────────────────────────────────────────────────────
        total_issues = len(interaction_lines) + len(allergy_flags)
        if total_issues == 0:
            lines.append("SUMMARY: No immediate safety concerns detected. Continued monitoring is advised.")
        else:
            lines.append(
                f"SUMMARY: {total_issues} potential safety concern(s) identified. "
                "Review with the prescribing physician before continuing the current regimen."
            )

        return "\n".join(lines)
    except Exception as e:
        pm.err(e=e, m=f"Error in analyze_patient_medications for patient '{patient_id}'")
        return f"Error analysing patient medications: {str(e)}"


# ============================================================
# All tools list for agent creation
# ============================================================

ALL_TOOLS = [
    get_drug_info,
    check_drug_interaction,
    check_drug_food_interaction,
    search_drugs_by_indication,
    search_pubmed,
    recommend_alternative_drug,
    analyze_patient_medications,
]
