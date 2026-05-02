"""
Article quality and relevance scoring for PubMed results.
"""
import math
from datetime import datetime
from typing import Optional


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


# ============================================================================
# Relevance Scoring
# ============================================================================

# Common stopwords to exclude from relevance matching
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

# Weights for each signal (must sum to 1.0)
W_CITATIONS = 0.20
W_RECENCY = 0.20
W_EVIDENCE = 0.25
W_RELEVANCE = 0.35


def compute_confidence_score(
    citation_count: int,
    publication_date: str,
    publication_types: list[str],
    query: str,
    title: str,
    abstract: str,
) -> tuple[float, dict]:
    """
    Compute composite confidence score for an article.
    
    Returns:
        - confidence_score: 0-100 scale
        - breakdown: dict with individual component scores
    """
    # Individual scores (0-1 scale)
    cite_score = normalize_citations(citation_count)
    recency = get_recency_score(publication_date)
    evidence = get_evidence_score(publication_types)
    relevance = compute_keyword_relevance(query, title, abstract)
    
    # Weighted composite
    raw_score = (
        W_CITATIONS * cite_score +
        W_RECENCY * recency +
        W_EVIDENCE * evidence +
        W_RELEVANCE * relevance
    )
    
    confidence = round(raw_score * 100, 1)
    
    breakdown = {
        "citations": round(cite_score * 100, 1),
        "recency": round(recency * 100, 1),
        "evidence_level": round(evidence * 100, 1),
        "relevance": round(relevance * 100, 1),
        "publication_types": publication_types,
    }
    
    return confidence, breakdown


def get_quality_warnings(
    confidence_score: float,
    relevance_score: float,
    publication_date: str,
    abstract: str,
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
    
    # No abstract
    if not abstract or abstract == "No abstract available.":
        warnings.append("⚠ NO ABSTRACT — cannot verify content, do not cite")
    
    return warnings
