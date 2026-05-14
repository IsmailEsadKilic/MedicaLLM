"""
Query type classification for adaptive PubMed search scoring.

Detects query intent and adjusts scoring weights accordingly.
"""
import re
from enum import Enum
from typing import Optional, Dict, TYPE_CHECKING
if TYPE_CHECKING:
    from langchain_core.language_models import BaseChatModel
    
from ..config import settings

from logging import getLogger

logger = getLogger(__name__)


class QueryType(str, Enum):
    """Types of PubMed queries with different scoring priorities."""
    
    AUTHOR_SPECIFIC = "author_specific"      # Searching for specific author's work
    DRUG_RESEARCH = "drug_research"          # Drug efficacy, safety, interactions
    DISEASE_RESEARCH = "disease_research"    # Disease mechanisms, treatments
    CLINICAL_GUIDELINE = "clinical_guideline" # Treatment guidelines, protocols
    REVIEW_META = "review_meta"              # Reviews and meta-analyses
    RECENT_ADVANCES = "recent_advances"      # Latest research in a field
    GENERAL_RESEARCH = "general_research"    # General medical research


class ScoringWeights:
    """Scoring weight configurations for different query types."""
    
    # Default weights (general research) — relevance is the most important gate
    DEFAULT = {
        "citations": 0.10,
        "fwci": 0.08,
        "journal": 0.12,
        "recency": 0.15,
        "evidence": 0.20,
        "relevance": 0.35,  # was 0.25
    }

    # Author-specific: Prioritize recency and relevance
    AUTHOR_SPECIFIC = {
        "citations": 0.08,
        "fwci": 0.04,
        "journal": 0.08,
        "recency": 0.25,
        "evidence": 0.10,
        "relevance": 0.45,  # was 0.30 — must match author name
    }

    # Drug research: Relevance + evidence level equally top; cut citation weight
    DRUG_RESEARCH = {
        "citations": 0.10,
        "fwci": 0.08,
        "journal": 0.12,
        "recency": 0.10,
        "evidence": 0.25,
        "relevance": 0.35,  # was 0.10 — critical fix
    }

    # Disease research: Balanced with strong relevance
    DISEASE_RESEARCH = {
        "citations": 0.10,
        "fwci": 0.10,
        "journal": 0.12,
        "recency": 0.13,
        "evidence": 0.20,
        "relevance": 0.35,  # was 0.15
    }

    # Clinical guidelines: Evidence + journal + relevance
    CLINICAL_GUIDELINE = {
        "citations": 0.08,
        "fwci": 0.08,
        "journal": 0.18,
        "recency": 0.12,
        "evidence": 0.24,
        "relevance": 0.30,  # was 0.10
    }

    # Reviews/Meta-analyses: Citations + relevance equally top
    REVIEW_META = {
        "citations": 0.15,
        "fwci": 0.10,
        "journal": 0.15,
        "recency": 0.08,
        "evidence": 0.17,
        "relevance": 0.35,  # was 0.10
    }

    # Recent advances: Recency first, relevance second
    RECENT_ADVANCES = {
        "citations": 0.05,
        "fwci": 0.08,
        "journal": 0.15,
        "recency": 0.37,
        "evidence": 0.10,
        "relevance": 0.25,  # was 0.10
    }


# ============================================================================
# Query Pattern Matching
# ============================================================================

# Author name patterns
AUTHOR_PATTERNS = [
    r'\b(?:by|author|authored by|written by)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
    r'\b([A-Z][a-z]+\s+[A-Z][a-z]+)\s+(?:research|work|studies|publications)',
    r'\b([A-Z][a-z]+\s+et\s+al)',
    r'\[AU\]',  # PubMed author tag
]

# Drug-related patterns. Avoid overly generic terms ("treatment", "therapy") that
# match almost every clinical query and bias classification toward DRUG_RESEARCH
# (audit P12). Drug queries are now characterised by *specific* drug-related
# vocabulary and clinical-trial design language.
DRUG_PATTERNS = [
    r'\b(?:drug|medication|pharmaceutical)\b',
    r'\b(?:efficacy|safety|adverse effects?|side effects?|toxicity)\b',
    r'\b(?:dosage|administration|pharmacokinetics?|pharmacodynamics?)\b',
    r'\b(?:clinical trial|randomi[sz]ed|placebo)\b',
    r'\b(?:drug interactions?|contraindications?)\b',
]

# Disease-related patterns
DISEASE_PATTERNS = [
    r'\b(?:disease|disorder|syndrome|condition|illness)\b',
    r'\b(?:pathogenesis|etiology|mechanism|pathophysiology)\b',
    r'\b(?:diagnosis|diagnostic|screening)\b',
    r'\b(?:prognosis|outcome|mortality|morbidity)\b',
    r'\b(?:risk factors|epidemiology|prevalence|incidence)\b',
    r'\b(?:diabetes|cancer|alzheimer|parkinson|hypertension|asthma|copd|heart failure)\b',  # Common diseases
]

# Guideline patterns
GUIDELINE_PATTERNS = [
    r'\b(?:guideline|protocol|recommendation|consensus)\b',
    r'\b(?:best practice|standard of care|clinical practice)\b',
    r'\b(?:management|approach|strategy)\b',
    r'\b(?:treatment|therapy)\s+(?:guideline|protocol|recommendation)\b',
]

# Review/Meta-analysis patterns
REVIEW_PATTERNS = [
    r'\b(?:review|meta-analysis|systematic review)\b',
    r'\b(?:literature review|overview|summary)\b',
]

# Recent advances patterns
RECENT_PATTERNS = [
    r'\b(?:recent|latest|new|novel|emerging|current)\b',
    r'\b(?:advances|developments|progress|breakthrough)\b',
    r'\b(?:2024|2025|2026|last year|past year)\b',
]


def classify_query(query: str, llm: Optional['BaseChatModel'] = None) -> QueryType:
    """
    Classify a PubMed query into the *single* most likely type.

    This is the fixed-priority path used when callers want a stable label
    (e.g. for logging or query analytics). For scoring weights, prefer
    `get_adaptive_weights`, which can blend signals from multiple matching
    types (audit P13).
    """
    types, _scores = _score_query_types(query, llm)
    if types:
        return types[0]
    return QueryType.GENERAL_RESEARCH


def _score_query_types(
    query: str, llm: Optional['BaseChatModel'] = None
) -> tuple[list[QueryType], dict[QueryType, float]]:
    """
    Return query types ordered by confidence and a score map.

    Each type gets a score 0.0-1.0 based on how many of its patterns matched.
    The previous implementation returned the FIRST matching type by a fixed
    priority, so a "recent systematic review of diabetes drug therapy" was
    classified as REVIEW_META and lost the recency / drug signals (audit P13).

    The returned list is sorted by descending score; the map is exposed so
    callers can blend weights in proportion to confidence.
    """
    query_lower = query.lower()
    scores: dict[QueryType, float] = {}

    # Author signal — strong and exclusive when present
    for pattern in AUTHOR_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            scores[QueryType.AUTHOR_SPECIFIC] = 1.0
            break

    review_hits = sum(1 for p in REVIEW_PATTERNS if re.search(p, query_lower))
    if review_hits:
        scores[QueryType.REVIEW_META] = min(1.0, 0.5 + 0.25 * review_hits)

    guideline_hits = sum(1 for p in GUIDELINE_PATTERNS if re.search(p, query_lower))
    if guideline_hits:
        scores[QueryType.CLINICAL_GUIDELINE] = min(1.0, 0.5 + 0.25 * guideline_hits)

    recent_hits = sum(1 for p in RECENT_PATTERNS if re.search(p, query_lower))
    if recent_hits >= 2:
        scores[QueryType.RECENT_ADVANCES] = min(1.0, 0.4 + 0.2 * recent_hits)

    drug_hits = sum(1 for p in DRUG_PATTERNS if re.search(p, query_lower))
    if drug_hits >= 2:
        scores[QueryType.DRUG_RESEARCH] = min(1.0, 0.4 + 0.15 * drug_hits)

    disease_hits = sum(1 for p in DISEASE_PATTERNS if re.search(p, query_lower))
    if disease_hits >= 1:
        scores[QueryType.DISEASE_RESEARCH] = min(1.0, 0.4 + 0.15 * disease_hits)

    # Optional LLM disambiguation when nothing matched and an LLM is given
    if not scores and llm is not None:
        llm_label = _classify_with_llm(query, llm)
        if llm_label is not None:
            scores[llm_label] = 0.7

    # Always keep GENERAL_RESEARCH as a low-weight fallback so blending has
    # something sensible to fall back on.
    scores.setdefault(QueryType.GENERAL_RESEARCH, 0.3)

    ordered = sorted(scores.keys(), key=lambda t: scores[t], reverse=True)
    logger.debug(f"[QUERY_CLASSIFIER] '{query[:60]}...' scores: { {k.value: round(v, 2) for k, v in scores.items()} }")
    return ordered, scores


def _classify_with_llm(query: str, llm: 'BaseChatModel') -> Optional[QueryType]:
    """
    Use LLM to classify ambiguous queries.
    
    Args:
        query: Search query string
        llm: Language model for classification
        
    Returns:
        QueryType or None if classification fails
    """
    try:
        classification_prompt = f"""Classify the following PubMed search query into ONE of these categories:

1. author_specific - Searching for a specific author's publications
2. drug_research - Research about drugs, medications, treatments, clinical trials
3. disease_research - Research about diseases, conditions, pathophysiology
4. clinical_guideline - Clinical guidelines, protocols, best practices
5. review_meta - Systematic reviews or meta-analyses
6. recent_advances - Latest/recent research or advances in a field
7. general_research - General medical research query

Query: "{query}"

Respond with ONLY the category name (e.g., "drug_research"), nothing else."""

        from langchain_core.messages import HumanMessage
        
        response = llm.invoke([HumanMessage(content=classification_prompt)])
        classification_str = response.content.strip().lower()
        
        # Map response to QueryType
        type_mapping = {
            "author_specific": QueryType.AUTHOR_SPECIFIC,
            "drug_research": QueryType.DRUG_RESEARCH,
            "disease_research": QueryType.DISEASE_RESEARCH,
            "clinical_guideline": QueryType.CLINICAL_GUIDELINE,
            "review_meta": QueryType.REVIEW_META,
            "recent_advances": QueryType.RECENT_ADVANCES,
            "general_research": QueryType.GENERAL_RESEARCH,
        }
        
        result = type_mapping.get(classification_str)
        if result:
            logger.debug(f"[QUERY_CLASSIFIER] LLM classified '{query}' as {result}")
            return result
        else:
            logger.warning(f"[QUERY_CLASSIFIER] LLM returned unexpected classification: {classification_str}")
            return None
            
    except Exception as e:
        logger.warning(f"[QUERY_CLASSIFIER] LLM classification failed: {e}")
        return None


def get_scoring_weights(query_type: QueryType) -> Dict[str, float]:
    """
    Get scoring weights for a specific query type.
    
    Args:
        query_type: Type of query
        
    Returns:
        Dictionary of scoring weights
    """
    weights_map = {
        QueryType.AUTHOR_SPECIFIC: ScoringWeights.AUTHOR_SPECIFIC,
        QueryType.DRUG_RESEARCH: ScoringWeights.DRUG_RESEARCH,
        QueryType.DISEASE_RESEARCH: ScoringWeights.DISEASE_RESEARCH,
        QueryType.CLINICAL_GUIDELINE: ScoringWeights.CLINICAL_GUIDELINE,
        QueryType.REVIEW_META: ScoringWeights.REVIEW_META,
        QueryType.RECENT_ADVANCES: ScoringWeights.RECENT_ADVANCES,
        QueryType.GENERAL_RESEARCH: ScoringWeights.DEFAULT,
    }
    
    weights = weights_map.get(query_type, ScoringWeights.DEFAULT)
    logger.debug(f"[QUERY_CLASSIFIER] Using weights for {query_type}: {weights}")
    return weights


def _boost_impact_weights(weights: Dict[str, float], boost_factor: float = 1.5) -> Dict[str, float]:
    """
    Adjust impact-related scoring weights (citations, FWCI, journal quality).
    
    Impact metrics are multiplied by boost_factor, then all weights are
    normalized to sum to 1.0.
    
    Args:
        weights: Original scoring weights
        boost_factor: Multiplier for impact metrics
                     - > 1.0: Boost impact metrics (e.g., 1.5 for older articles)
                     - < 1.0: Decrease impact metrics (e.g., 0.5 for very recent articles)
        
    Returns:
        Normalized weights with adjusted impact metrics
    """
    # Define impact metrics to adjust
    impact_metrics = {"citations", "fwci", "journal"}
    
    # Create a copy to avoid modifying original
    adjusted = weights.copy()
    
    # Adjust impact metrics
    for metric in impact_metrics:
        if metric in adjusted:
            adjusted[metric] *= boost_factor
    
    # Normalize to sum to 1.0
    total = sum(adjusted.values())
    if total > 0:
        adjusted = {k: v / total for k, v in adjusted.items()}
    
    return adjusted


def get_adaptive_weights(
    query: str, 
    llm: Optional['BaseChatModel'] = None, 
    boost_impact_score_weights: bool = settings.boost_impact_score_weights,
    is_very_recent: bool = False
) -> tuple[QueryType, Dict[str, float]]:
    """
    Classify query and return blended scoring weights.

    Audit P13: previously this took the single highest-priority match and
    used its weight profile, which was fragile for multi-faceted queries
    like "recent systematic review of diabetes drug therapy" that should
    inherit signal from REVIEW + RECENT + DRUG simultaneously.

    Behaviour:
      - We score every type that has at least one matching pattern.
      - Final weights are a confidence-weighted average of each matched
        type's profile, falling back to GENERAL_RESEARCH at low weight.
      - The "primary" type (returned to callers for logging) is the one
        with the highest score.
    """
    ordered_types, type_scores = _score_query_types(query, llm)
    primary = ordered_types[0] if ordered_types else QueryType.GENERAL_RESEARCH

    # Blend weight profiles in proportion to confidence
    weight_keys = list(ScoringWeights.DEFAULT.keys())
    blended: Dict[str, float] = {k: 0.0 for k in weight_keys}
    total_score = sum(type_scores.values())
    if total_score > 0:
        for qtype, score in type_scores.items():
            profile = get_scoring_weights(qtype)
            share = score / total_score
            for k in weight_keys:
                blended[k] += profile.get(k, 0.0) * share
    else:
        # No matches at all — fall through to defaults (shouldn't happen
        # because GENERAL_RESEARCH always gets a small share).
        blended = dict(ScoringWeights.DEFAULT)

    # Re-normalise to 1.0 in case rounding drifted us off
    total = sum(blended.values())
    if total > 0:
        blended = {k: v / total for k, v in blended.items()}

    if is_very_recent:
        # For very recent articles, decrease impact weights (they haven't had time to accumulate citations)
        blended = _boost_impact_weights(blended, boost_factor=0.5)
        logger.debug(f"[QUERY_CLASSIFIER] Decreased impact weights for recent article: {blended}")
    elif boost_impact_score_weights:
        blended = _boost_impact_weights(blended, boost_factor=1.5)
        logger.debug(f"[QUERY_CLASSIFIER] Boosted impact weights: {blended}")

    return primary, blended


def get_query_type_description(query_type: QueryType) -> str:
    """
    Get human-readable description of query type.
    
    Args:
        query_type: Type of query
        
    Returns:
        Description string
    """
    descriptions = {
        QueryType.AUTHOR_SPECIFIC: "Author-specific search (prioritizing recent work)",
        QueryType.DRUG_RESEARCH: "Drug research (prioritizing clinical trials and evidence)",
        QueryType.DISEASE_RESEARCH: "Disease research (balanced approach)",
        QueryType.CLINICAL_GUIDELINE: "Clinical guidelines (prioritizing authoritative sources)",
        QueryType.REVIEW_META: "Review/Meta-analysis (prioritizing well-cited reviews)",
        QueryType.RECENT_ADVANCES: "Recent advances (prioritizing newest research)",
        QueryType.GENERAL_RESEARCH: "General medical research (balanced approach)",
    }
    return descriptions.get(query_type, "General research")
