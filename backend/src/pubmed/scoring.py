"""
Article quality and relevance scoring for PubMed results.
"""
import math
from datetime import datetime
from typing import Optional, Dict

from logging import getLogger
logger = getLogger(__name__)


# ============================================================================
# Journal Quality Scoring (Scopus Metrics)
# ============================================================================

def get_journal_quality_score(
    cite_score: Optional[float] = None,
    sjr: Optional[float] = None,
    snip: Optional[float] = None,
    journal_percentile: Optional[float] = None,
) -> float:
    """
    Score journal quality based on Scopus metrics (0.0 - 1.0).
    
    Uses multiple metrics with fallbacks:
    - Journal percentile (most direct measure)
    - CiteScore (normalized)
    - SJR (normalized)
    - SNIP (normalized)
    
    Returns 0.5 if no metrics available (neutral score).
    """
    scores = []
    
    # Percentile is most direct (already 0-100 scale)
    if journal_percentile is not None:
        scores.append(journal_percentile / 100.0)
    
    # CiteScore: normalize (top journals ~20+, good journals ~5+)
    if cite_score is not None:
        normalized = min(cite_score / 20.0, 1.0)
        scores.append(normalized)
    
    # SJR: normalize (top journals ~10+, good journals ~2+)
    if sjr is not None:
        normalized = min(sjr / 10.0, 1.0)
        scores.append(normalized)
    
    # SNIP: normalize (top journals ~3+, good journals ~1.5+)
    if snip is not None:
        normalized = min(snip / 3.0, 1.0)
        scores.append(normalized)
    
    # Return average of available metrics, or 0.5 if none
    return sum(scores) / len(scores) if scores else 0.5


def get_fwci_score(
    fwci: Optional[float] = None,
    citation_normalized_percentile: Optional[float] = None,
) -> float:
    """
    Score based on Field-Weighted Citation Impact (0.0 - 1.0).

    Citation count distributions are heavily right-skewed (log-normal / power-law),
    so we combine two complementary field-normalized signals when available:

    1. **FWCI** (ratio scale) — preserves magnitude information ("10× field avg"
       vs "100× field avg"). We apply a log-tanh transform because:
         - FWCI distribution is log-normal in practice
         - Linear caps (old implementation used 3.0 → 1.0) erased distinctions
           between FWCI 3 and FWCI 100+ (top clinical reviews routinely hit 50+)
         - tanh(log10(x)) gives a smooth S-curve centered at FWCI=1.0 (=0.5),
           saturates gracefully at extremes, and keeps resolution at high values.

    2. **Citation-normalized percentile** (0-1, OpenAlex) — ordinal/rank-robust,
       directly interpretable ("top X% in field/year cohort"), resistant to
       outliers. Already fetched upstream but previously unused.

    Literature supports a hybrid rather than either signal alone: FWCI carries
    ratio information but is sensitive to extreme values; percentile is robust
    but loses magnitude. See Bornmann & Mutz (QSS 2020) and Leydesdorff on
    citing-side normalization + percentile hybrid approaches.

    Anchor points for the log-tanh transform:
        FWCI 0.1  → 0.12   (well below field average)
        FWCI 0.5  → 0.35
        FWCI 1.0  → 0.50   (field average — the natural midpoint)
        FWCI 2.0  → 0.65
        FWCI 5.0  → 0.80
        FWCI 10   → 0.88
        FWCI 50   → 0.97
        FWCI 100+ → 0.99   (smooth saturation, no hard cap)

    Returns 0.5 (neutral) if neither signal is available.
    """
    scores: list[float] = []

    # FWCI — log-tanh transform (symmetric around the field average)
    if fwci is not None and fwci > 0:
        scores.append(0.5 + 0.5 * math.tanh(math.log10(fwci)))
    elif fwci is not None and fwci <= 0:
        scores.append(0.0)

    # OpenAlex citation-normalized percentile is already a 0-1 field-normalized rank
    if citation_normalized_percentile is not None:
        try:
            pct = float(citation_normalized_percentile)
            # Clamp defensively — OpenAlex should return 0-1, but guard against
            # API drift or bad data
            scores.append(max(0.0, min(1.0, pct)))
        except (ValueError, TypeError):
            pass

    if not scores:
        return 0.5  # Neutral if neither metric is available

    # Average both signals when present — acts as cross-validation: a paper with
    # high FWCI AND high percentile is clearly impactful; a paper with high FWCI
    # but low percentile may have one anomalous citation spike
    return sum(scores) / len(scores)


def get_open_access_bonus(open_access: bool) -> float:
    """
    Small bonus for open access articles (0.0 - 0.1).
    
    Open access articles are more accessible and verifiable.
    """
    return 0.05 if open_access else 0.0


# ============================================================================
# Evidence Hierarchy
# ============================================================================

# Evidence levels based on publication type (higher = stronger evidence)
EVIDENCE_LEVELS = {
    "meta-analysis": 1.0,
    "systematic review": 0.9,
    "randomized controlled trial": 0.85,
    "clinical trial": 0.75,
    "controlled clinical trial": 0.75,
    "practice guideline": 0.7,
    "guideline": 0.7,
    "comparative study": 0.6,
    "multicenter study": 0.6,
    "cohort study": 0.55,
    "observational study": 0.5,
    "journal article": 0.5,
    "case-control study": 0.45,
    "review": 0.4,
    "case reports": 0.3,
    "editorial": 0.15,
    "comment": 0.1,
    "letter": 0.1,
    "preprint": 0.1,
}

def get_evidence_score(publication_types: list[str]) -> float:
    """
    Map publication types to an evidence level score (0.0 - 1.0).
    
    Returns the highest evidence level found among the publication types.
    """
    if not publication_types:
        return 0.3  # default for unknown
    
    best = 0.0
    for pt in publication_types:
        pt_lower = pt.lower()
        for key, score in EVIDENCE_LEVELS.items():
            if key in pt_lower:
                best = max(best, score)
                break
    
    return best if best > 0 else 0.3


# ============================================================================
# Recency Scoring
# ============================================================================

def get_recency_score(publication_date: str) -> float:
    """
    Score from 0.0 to 1.0 based on how recent the article is.
    
    - Last 2 years: 1.0
    - 2-20 years: linear decay from 1.0 to 0.1
    - 20+ years: 0.1
    """
    if not publication_date:
        return 0.3
    
    try:
        pub_dt = None
        for fmt in ("%Y-%m-%d", "%Y-%m", "%Y"):
            try:
                pub_dt = datetime.strptime(publication_date.strip()[:10], fmt)
                break
            except ValueError:
                continue
        
        if pub_dt is None:
            return 0.3
        
        years_ago = (datetime.now() - pub_dt).days / 365.25
        
        if years_ago <= 2:
            return 1.0
        elif years_ago >= 20:
            return 0.1
        else:
            # Linear decay from 1.0 to 0.1 over 18 years
            return 1.0 - (years_ago - 2) * (0.9 / 18)
    
    except Exception:
        return 0.3


# ============================================================================
# Citation Scoring
# ============================================================================

def normalize_citations(citation_count: int, max_citations: int = 1000) -> float:
    """
    Normalize citation count to 0-1 scale using log scaling.
    
    1000 citations = 1.0 (highly cited)
    100 citations = ~0.67
    10 citations = ~0.35
    0 citations = 0.0
    """
    if citation_count <= 0:
        return 0.0
    return min(math.log1p(citation_count) / math.log1p(max_citations), 1.0)


def compute_pubmed_rank_score(rank: int, total_fetched: int) -> float:
    """
    Convert PubMed's own sort=relevance position into a 0-1 score.

    PubMed's esearch returns articles already ranked by its own ML relevance
    model.  Rank 1 = most relevant.  We convert position to a score so it
    can be blended with keyword relevance:

      rank_score = 1 - (rank - 1) / max(total_fetched - 1, 1)

    This gives rank-1 a score of 1.0 and the last article a score of 0.0,
    with linear decay in between.
    """
    if rank <= 0 or total_fetched <= 0:
        return 0.5  # neutral when rank info is unavailable
    rank = max(1, min(rank, total_fetched))
    return 1.0 - (rank - 1) / max(total_fetched - 1, 1)


def compute_blended_relevance(query: str, title: str, abstract: str, pubmed_rank: int = 0, total_fetched: int = 0) -> float:
    """
    Blend keyword relevance with PubMed's own positional rank signal.

    PubMed already runs a high-quality ML relevance model (sort=relevance).
    Using its rank position is zero-cost (no extra API calls or ML inference)
    and more reliable than re-running a general sentence-transformer.

    Blend: 50% keyword match + 50% PubMed rank score.
    Falls back to keyword-only when rank info is unavailable.
    """
    keyword_score = compute_keyword_relevance(query, title, abstract)
    if pubmed_rank <= 0 or total_fetched <= 0:
        return keyword_score
    rank_score = compute_pubmed_rank_score(pubmed_rank, total_fetched)
    return 0.5 * keyword_score + 0.5 * rank_score



STOPWORDS = {
    "the", "a", "an", "in", "on", "of", "for", "and", "or", "to",
    "with", "is", "are", "was", "were", "by", "from", "that", "this",
    "be", "at", "it", "as", "do", "does", "did", "not", "no", "but",
    "if", "its", "has", "have", "had", "may", "can", "will", "would",
    "should", "could", "about", "between", "among", "into", "through"
}


def compute_keyword_relevance(query: str, title: str, abstract: str) -> float:
    """
    Compute semantic relevance between query and article.
    
    - Title matches weighted 3x more than abstract matches
    - Bigrams (consecutive word pairs) checked in addition to unigrams
    - Returns score from 0.0 to 1.0
    """
    query_words = [w for w in query.lower().split() if w not in STOPWORDS]
    if not query_words:
        return 0.5
    
    title_lower = title.lower()
    abstract_lower = abstract.lower() if abstract else ""
    
    # Unigram scoring
    title_hits = sum(1 for t in query_words if t in title_lower)
    abstract_hits = sum(1 for t in query_words if t in abstract_lower)
    
    # Bigram scoring (consecutive word pairs from query)
    bigrams = [f"{query_words[i]} {query_words[i+1]}" for i in range(len(query_words) - 1)]
    bigram_title_hits = sum(1 for bg in bigrams if bg in title_lower) if bigrams else 0
    bigram_abstract_hits = sum(1 for bg in bigrams if bg in abstract_lower) if bigrams else 0
    
    n_terms = len(query_words)
    n_bigrams = max(len(bigrams), 1)
    
    # Title relevance (weighted 3x) + abstract relevance
    title_score = (title_hits / n_terms) * 0.7 + (bigram_title_hits / n_bigrams) * 0.3
    abstract_score = (abstract_hits / n_terms) * 0.7 + (bigram_abstract_hits / n_bigrams) * 0.3
    
    combined = title_score * 0.6 + abstract_score * 0.4
    return min(combined, 1.0)


# ============================================================================
# Composite Confidence Score
# ============================================================================

# Default weights for each signal (must sum to 1.0).
# These are the SCORING-LEVEL defaults; the adaptive query classifier in
# `query_classifier.py` may override them per query type. Both modules must
# stay in sync (audit P4) — this is the single source of truth and the
# classifier's `DEFAULT` mirrors these values.
DEFAULT_WEIGHTS = {
    "citations": 0.10,
    "fwci": 0.08,
    "journal": 0.12,
    "recency": 0.15,
    "evidence": 0.20,
    "relevance": 0.35,
}


def compute_confidence_score(
    citation_count: int,
    publication_date: str,
    publication_types: list[str],
    query: str,
    title: str,
    abstract: str,
    # Scopus metrics (optional)
    cite_score: Optional[float] = None,
    sjr: Optional[float] = None,
    snip: Optional[float] = None,
    journal_percentile: Optional[float] = None,
    fwci: Optional[float] = None,
    citation_normalized_percentile: Optional[float] = None,
    open_access: bool = False,
    # PubMed positional rank (from sort=relevance esearch result, 1-based)
    pubmed_rank: int = 0,
    total_fetched: int = 0,
    # Custom weights (optional)
    custom_weights: Optional[Dict[str, float]] = None,
) -> tuple[float, dict]:
    """
    Compute composite confidence score for an article.
    
    Args:
        citation_count: Number of citations
        publication_date: Publication date string
        publication_types: List of publication type tags
        query: Search query
        title: Article title
        abstract: Article abstract
        cite_score: Journal CiteScore (optional)
        sjr: SCImago Journal Rank (optional)
        snip: Source Normalized Impact per Paper (optional)
        journal_percentile: Journal percentile ranking (optional)
        fwci: Field-Weighted Citation Impact (optional)
        citation_normalized_percentile: OpenAlex citation percentile, 0-1 (optional).
            Rank-based complement to FWCI, used jointly for a robust field-impact signal.
        open_access: Whether article is open access
        custom_weights: Custom scoring weights (optional, overrides defaults)
    
    Returns:
        - confidence_score: 0-100 scale
        - breakdown: dict with individual component scores
    """
    # Use custom weights if provided, otherwise use defaults
    weights = custom_weights if custom_weights else DEFAULT_WEIGHTS
    
    # Individual scores (0-1 scale)
    cite_score_val = normalize_citations(citation_count)
    fwci_score = get_fwci_score(fwci, citation_normalized_percentile)
    journal_score = get_journal_quality_score(cite_score, sjr, snip, journal_percentile)
    recency = get_recency_score(publication_date)
    evidence = get_evidence_score(publication_types)
    # Blend keyword relevance with PubMed's own positional rank (zero extra latency)
    relevance = compute_blended_relevance(query, title, abstract, pubmed_rank=pubmed_rank, total_fetched=total_fetched)
    oa_bonus = get_open_access_bonus(open_access)
    
    # Weighted composite using provided or default weights
    raw_score = (
        weights["citations"] * cite_score_val +
        weights["fwci"] * fwci_score +
        weights["journal"] * journal_score +
        weights["recency"] * recency +
        weights["evidence"] * evidence +
        weights["relevance"] * relevance
    )
    
    # Add small open access bonus (max 5 points)
    raw_score = min(raw_score + oa_bonus, 1.0)
    
    confidence = round(raw_score * 100, 1)
    
    breakdown = {
        "citations": round(cite_score_val * 100, 1),
        "fwci": round(fwci_score * 100, 1),
        # Keep the same keys as DEFAULT_WEIGHTS so external consumers can map
        # a weight to its score directly (audit P11). We also keep the legacy
        # `journal_quality` / `evidence_level` aliases for any downstream code
        # already reading them (e.g. tools.py result formatting).
        "journal": round(journal_score * 100, 1),
        "journal_quality": round(journal_score * 100, 1),
        "recency": round(recency * 100, 1),
        "evidence": round(evidence * 100, 1),
        "evidence_level": round(evidence * 100, 1),
        "relevance": round(relevance * 100, 1),
        "open_access_bonus": round(oa_bonus * 100, 1),
        "publication_types": publication_types,
        # Include raw Scopus metrics for reference
        "scopus_metrics": {
            "cite_score": cite_score,
            "sjr": sjr,
            "snip": snip,
            "journal_percentile": journal_percentile,
            "fwci": fwci,
            "citation_normalized_percentile": citation_normalized_percentile,
        },
        # Include weights used for transparency
        "weights_used": weights,
    }
    
    return confidence, breakdown


def get_quality_warnings(
    confidence_score: float,
    relevance_score: float,
    publication_date: str,
    abstract: str,
    fwci: Optional[float] = None,
) -> list[str]:
    """
    Generate quality warnings for an article based on various criteria.
    
    Returns list of warning strings to display to user/LLM.
    """
    warnings = []
    
    # Low relevance
    if relevance_score < 0.4:
        warnings.append(
            f"⚠ LOW RELEVANCE ({round(relevance_score * 100)}/100) — "
            "this article may not directly address the query. Only cite if truly relevant."
        )
    
    # Old article
    if publication_date:
        try:
            pub_year = int(publication_date[:4])
            article_age = datetime.now().year - pub_year
            if article_age > 20:
                warnings.append(
                    f"⚠ OLD ARTICLE ({pub_year}, {article_age} years ago) — "
                    "cite with caution, note age limitation"
                )
            elif article_age > 10:
                warnings.append(
                    f"⚠ Article is {article_age} years old — check for more recent evidence"
                )
        except (ValueError, IndexError):
            pass
    
    # Low confidence
    if confidence_score < 35:
        warnings.append(f"⚠ LOW CONFIDENCE ({confidence_score}/100) — weak evidence")

    # Below field-average impact
    if fwci is not None and fwci < 0.5:
        warnings.append(
            f"⚠ LOW FIELD IMPACT (FWCI {fwci:.2f}) — cited much less than similar articles in its field"
        )

    # No abstract
    if not abstract or abstract == "No abstract available.":
        warnings.append("⚠ NO ABSTRACT — cannot verify content, do not cite")
    
    return warnings
