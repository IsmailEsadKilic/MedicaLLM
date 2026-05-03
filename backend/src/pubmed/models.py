"""
PubMed data models for articles, citations, and search results.
"""
from pydantic import BaseModel, Field
from typing import Optional


class PubMedArticle(BaseModel):
    """Structured PubMed article with metadata and confidence scoring."""
    
    pmid: str = Field(..., description="PubMed ID")
    title: str = Field(..., description="Article title")
    abstract: str = Field(default="", description="Article abstract")
    authors: list[str] = Field(default_factory=list, description="List of author names")
    journal: str = Field(default="", description="Journal name")
    publication_date: str = Field(default="", description="Publication date (YYYY-MM-DD or YYYY-MM or YYYY)")
    doi: str = Field(default="", description="Digital Object Identifier")
    pmc_id: str = Field(default="", description="PubMed Central ID (e.g., PMC7234567)")
    publication_types: list[str] = Field(default_factory=list, description="Publication type tags (e.g., 'Clinical Trial', 'Meta-Analysis')")
    
    # Citation and quality metrics
    citation_count: int = Field(default=0, description="Number of citations (if available)")
    confidence_score: float = Field(default=0.0, description="Composite confidence score (0-100)")
    confidence_breakdown: dict = Field(default_factory=dict, description="Breakdown of confidence score components")
    
    # Relevance to query
    relevance_score: float = Field(default=0.0, description="Keyword relevance to search query (0-1)")
    
    # Scopus metrics (optional, populated when Scopus API is available)
    scopus_id: str = Field(default="", description="Scopus article ID")
    scopus_eid: str = Field(default="", description="Scopus EID")
    cite_score: Optional[float] = Field(default=None, description="Journal CiteScore from Scopus")
    sjr: Optional[float] = Field(default=None, description="SCImago Journal Rank (SJR)")
    snip: Optional[float] = Field(default=None, description="Source Normalized Impact per Paper (SNIP)")
    fwci: Optional[float] = Field(default=None, description="Field-Weighted Citation Impact")
    journal_percentile: Optional[float] = Field(default=None, description="Journal percentile ranking in field (0-100)")
    subject_areas: list[str] = Field(default_factory=list, description="Scopus subject area classifications")
    open_access: bool = Field(default=False, description="Whether article is open access")
    author_count: int = Field(default=0, description="Number of authors")
    affiliation_count: int = Field(default=0, description="Number of institutional affiliations")
    citation_source: str = Field(default="", description="Source of citation data (scopus, semantic_scholar, none)")
    query_type: str = Field(default="", description="Detected query type for adaptive scoring")
    
    def get_citation_text(self) -> str:
        """Generate a formatted citation string."""
        authors_str = ", ".join(self.authors[:3])
        if len(self.authors) > 3:
            authors_str += " et al."
        
        parts = []
        if authors_str:
            parts.append(authors_str)
        if self.title:
            parts.append(f'"{self.title}"')
        if self.journal:
            parts.append(self.journal)
        if self.publication_date:
            parts.append(f"({self.publication_date[:4]})")
        
        return ". ".join(parts) + "."
    
    def get_url(self) -> str:
        """Get PubMed URL for this article."""
        if self.pmid:
            return f"https://pubmed.ncbi.nlm.nih.gov/{self.pmid}/"
        return ""
    
    def get_doi_url(self) -> str:
        """Get DOI URL if available."""
        if self.doi:
            return f"https://doi.org/{self.doi}"
        return ""


class PubMedSearchResult(BaseModel):
    """Search result container with articles and metadata."""
    
    query: str = Field(..., description="Original search query")
    articles: list[PubMedArticle] = Field(default_factory=list, description="Retrieved articles")
    total_found: int = Field(default=0, description="Total articles found (may be more than returned)")
    search_time_ms: float = Field(default=0.0, description="Search execution time in milliseconds")
    
    # Quality metrics
    avg_confidence: float = Field(default=0.0, description="Average confidence score of returned articles")
    filtered_count: int = Field(default=0, description="Number of articles filtered out due to low quality")
    
    def get_top_articles(self, n: int = 5) -> list[PubMedArticle]:
        """Get top N articles by confidence score."""
        return sorted(self.articles, key=lambda a: a.confidence_score, reverse=True)[:n]
