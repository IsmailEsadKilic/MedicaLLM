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

# Drug-related patterns
DRUG_PATTERNS = [
    r'\b(?:drug|medication|pharmaceutical|therapy|treatment)\b',
    r'\b(?:efficacy|safety|adverse effects|side effects|toxicity)\b',
    r'\b(?:dosage|administration|pharmacokinetics|pharmacodynamics)\b',
    r'\b(?:clinical trial|randomized|placebo)\b',
    r'\b(?:drug interaction|contraindication)\b',
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
    Classify a PubMed query into a specific type.
    
    Args:
        query: Search query string
        llm: Optional LLM for ambiguous query classification
        
    Returns:
        QueryType enum value
    """
    query_lower = query.lower()
    
    # Check for author-specific queries
    for pattern in AUTHOR_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            logger.debug(f"[QUERY_CLASSIFIER] Detected AUTHOR_SPECIFIC query: {query}")
            return QueryType.AUTHOR_SPECIFIC
    
    # Check for review/meta-analysis queries
    review_matches = sum(1 for p in REVIEW_PATTERNS if re.search(p, query_lower))
    if review_matches > 0:
        logger.debug(f"[QUERY_CLASSIFIER] Detected REVIEW_META query: {query}")
        return QueryType.REVIEW_META
    
    # Check for guideline queries
    guideline_matches = sum(1 for p in GUIDELINE_PATTERNS if re.search(p, query_lower))
    if guideline_matches >= 1:  # Even one match is strong signal for guidelines
        logger.debug(f"[QUERY_CLASSIFIER] Detected CLINICAL_GUIDELINE query: {query}")
        return QueryType.CLINICAL_GUIDELINE
    
    # Check for recent advances queries
    recent_matches = sum(1 for p in RECENT_PATTERNS if re.search(p, query_lower))
    if recent_matches >= 2:  # Need at least 2 matches to be confident
        logger.debug(f"[QUERY_CLASSIFIER] Detected RECENT_ADVANCES query: {query}")
        return QueryType.RECENT_ADVANCES
    
    # Check for drug research queries
    drug_matches = sum(1 for p in DRUG_PATTERNS if re.search(p, query_lower))
    if drug_matches >= 2:
        logger.debug(f"[QUERY_CLASSIFIER] Detected DRUG_RESEARCH query: {query}")
        return QueryType.DRUG_RESEARCH
    
    # Check for disease research queries
    disease_matches = sum(1 for p in DISEASE_PATTERNS if re.search(p, query_lower))
    if disease_matches >= 1:  # Even one strong disease indicator is enough
        logger.debug(f"[QUERY_CLASSIFIER] Detected DISEASE_RESEARCH query: {query}")
        return QueryType.DISEASE_RESEARCH
    
    # If no clear pattern match and LLM is available, use LLM classification
    if llm is not None:
        logger.debug(f"[QUERY_CLASSIFIER] No regex match, using LLM classification for: {query}")
        llm_classification = _classify_with_llm(query, llm)
        if llm_classification:
            logger.info(f"[QUERY_CLASSIFIER] LLM classified as: {llm_classification}")
            return llm_classification
    
    # Default to general research
    logger.debug(f"[QUERY_CLASSIFIER] Detected GENERAL_RESEARCH query: {query}")
    return QueryType.GENERAL_RESEARCH


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
    Classify query and return appropriate scoring weights.
    
    Args:
        query: Search query string
        llm: Optional LLM for ambiguous query classification
        boost_impact_score_weights: If True, adjust impact metrics (citations, FWCI, journal)
        is_very_recent: If True, decrease impact metrics for recent articles (< 1 year old)
        
    Returns:
        Tuple of (query_type, weights_dict)
    """
    query_type = classify_query(query, llm)
    weights = get_scoring_weights(query_type)
    
    if is_very_recent:
        # For very recent articles, decrease impact weights (they haven't had time to accumulate citations)
        weights = _boost_impact_weights(weights, boost_factor=0.5)
        logger.debug(f"[QUERY_CLASSIFIER] Decreased impact weights for recent article: {weights}")
    
    else:
        # For non-recent articles, boost impact weights if enabled
        if boost_impact_score_weights:
            weights = _boost_impact_weights(weights, boost_factor=1.5)
            logger.debug(f"[QUERY_CLASSIFIER] Boosted impact weights: {weights}")
    
    return query_type, weights


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
