"""
Enhanced source and debug tracking for agent tool calls.

Provides Gemini-style inline citation tracking with structured metadata.
Handles cross-thread propagation for LangChain's thread-pool execution.
"""
import threading
from contextvars import ContextVar
from dataclasses import dataclass, field, asdict
from enum import Enum


# ============================================================================
# Source Models
# ============================================================================

class SourceType(str, Enum):
    """Type of information source."""
    PUBMED = "pubmed"
    DATABASE = "database"
    TOOL = "tool"
    EXTERNAL = "external"


@dataclass
class Source:
    """
    Structured source citation with inline reference support.
    
    Designed to support Gemini-style inline citations where each factoid
    in the AI response can link to a specific source.
    """
    # Core identification
    ref_id: str  # e.g., "REF1", "REF2" for inline citations
    source_type: SourceType
    tool_name: str  # Which tool generated this source
    
    # Display information
    title: str
    url: str | None = None
    
    # Content
    content: str = ""  # Snippet or summary of source content
    
    # Metadata
    metadata: dict = field(default_factory=dict)
    
    # Quality indicators
    confidence_score: float | None = None  # 0-100 scale
    warnings: list[str] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    def get_display_text(self) -> str:
        """Get formatted display text for UI."""
        parts = [self.title]
        if self.metadata.get("journal"):
            parts.append(f"({self.metadata['journal']})")
        if self.metadata.get("publication_date"):
            parts.append(f"[{self.metadata['publication_date'][:4]}]")
        return " ".join(parts)


@dataclass
class ToolExecution:
    """Record of a single tool execution with timing and results."""
    tool_name: str
    arguments: dict
    result: str
    execution_time_ms: float
    success: bool
    error: str | None = None
    sources_generated: int = 0
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)


# ============================================================================
# Cross-Thread Propagation
# ============================================================================

# LangChain runs tools in a thread-pool, so ContextVar writes don't propagate
# back to the caller. Solution: tools read a request_id (copied to thread) and
# write results to a shared thread-safe dict keyed by request_id.

_request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)
_current_user_id_var: ContextVar[str | None] = ContextVar("current_user_id", default=None)
_current_patient_id_var: ContextVar[str | None] = ContextVar("current_patient_id", default=None)

# Thread-safe stores
_store_lock = threading.Lock()
_source_store: dict[str, list[Source]] = {}
_tool_execution_store: dict[str, list[ToolExecution]] = {}


# ============================================================================
# Context Management
# ============================================================================

def set_request_id(request_id: str) -> None:
    """
    Set unique request ID for current coroutine.
    
    Must be called before each agent invocation so tools can write results
    to the shared stores.
    """
    _request_id_var.set(request_id)


def get_request_id() -> str | None:
    """Get current request ID."""
    return _request_id_var.get()


def set_current_user_id(user_id: str) -> None:
    """Store authenticated user ID in current coroutine context."""
    _current_user_id_var.set(user_id)


def get_current_user_id() -> str | None:
    """Get authenticated user ID for current coroutine."""
    return _current_user_id_var.get()


def set_current_patient_id(patient_id: str | None) -> None:
    """Store current patient ID in current coroutine context."""
    _current_patient_id_var.set(patient_id)


def get_current_patient_id() -> str | None:
    """Get current patient ID for current coroutine."""
    return _current_patient_id_var.get()


# ============================================================================
# Source Tracking
# ============================================================================

def add_source(source: Source) -> None:
    """
    Add a source to the current request's source list.
    
    Thread-safe: works from tool execution threads.
    """
    request_id = _request_id_var.get()
    if request_id is None:
        # Fallback: no request context (shouldn't happen in production)
        return
    
    with _store_lock:
        if request_id not in _source_store:
            _source_store[request_id] = []
        _source_store[request_id].append(source)


def add_sources(sources: list[Source]) -> None:
    """Add multiple sources at once."""
    for source in sources:
        add_source(source)


def get_sources(request_id: str) -> list[Source]:
    """
    Retrieve and clear sources for a request.
    
    Call this after agent execution completes.
    """
    with _store_lock:
        sources = _source_store.pop(request_id, [])
    return sources


# ============================================================================
# Tool Execution Tracking
# ============================================================================

def record_tool_execution(execution: ToolExecution) -> None:
    """
    Record a tool execution for debugging.
    
    Thread-safe: works from tool execution threads.
    """
    request_id = _request_id_var.get()
    if request_id is None:
        return
    
    with _store_lock:
        if request_id not in _tool_execution_store:
            _tool_execution_store[request_id] = []
        _tool_execution_store[request_id].append(execution)


def get_tool_executions(request_id: str) -> list[ToolExecution]:
    """
    Retrieve and clear tool executions for a request.
    
    Call this after agent execution completes.
    """
    with _store_lock:
        executions = _tool_execution_store.pop(request_id, [])
    return executions


# ============================================================================
# Helper Functions
# ============================================================================

def create_pubmed_source(
    ref_id: str,
    tool_name: str,
    article: dict,
    snippet: str = "",
) -> Source:
    """
    Create a Source from a PubMed article.
    
    Args:
        ref_id: Reference ID (e.g., "REF1")
        tool_name: Name of tool that generated this source
        article: PubMed article dict with pmid, title, etc.
        snippet: Relevant content snippet
    """
    pmid = article.get("pmid", "")
    url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None
    
    return Source(
        ref_id=ref_id,
        source_type=SourceType.PUBMED,
        tool_name=tool_name,
        title=article.get("title", "Untitled"),
        url=url,
        content=snippet,
        metadata={
            "pmid": pmid,
            "journal": article.get("journal", ""),
            "publication_date": article.get("publication_date", ""),
            "doi": article.get("doi", ""),
            "authors": article.get("authors", []),
            "citation_count": article.get("citation_count", 0),
            "study_type": ", ".join(article.get("publication_types", [])),
        },
        confidence_score=article.get("confidence_score"),
        warnings=article.get("warnings", []),
    )


def create_database_source(
    ref_id: str,
    tool_name: str,
    title: str,
    content: str,
    metadata: dict | None = None,
) -> Source:
    """Create a Source from database information."""
    return Source(
        ref_id=ref_id,
        source_type=SourceType.DATABASE,
        tool_name=tool_name,
        title=title,
        url=None,
        content=content,
        metadata=metadata or {},
    )


def generate_ref_id(index: int) -> str:
    """Generate a reference ID from an index (1-based)."""
    return f"REF{index}"


# ============================================================================
# Debug Summary
# ============================================================================

def create_debug_summary(
    request_id: str,
    agent_execution_time_ms: float,
) -> dict:
    """
    Create a comprehensive debug summary for a request.
    
    Includes:
    - Tool execution details
    - Source generation stats
    - Timing information
    - Error tracking
    """
    executions = get_tool_executions(request_id)
    sources = get_sources(request_id)
    
    # Calculate stats
    total_tool_time = sum(e.execution_time_ms for e in executions)
    failed_tools = [e for e in executions if not e.success]
    
    # Group sources by tool
    sources_by_tool = {}
    for source in sources:
        tool = source.tool_name
        if tool not in sources_by_tool:
            sources_by_tool[tool] = []
        sources_by_tool[tool].append(source)
    
    return {
        "request_id": request_id,
        "timing": {
            "total_agent_time_ms": agent_execution_time_ms,
            "total_tool_time_ms": total_tool_time,
            "overhead_ms": agent_execution_time_ms - total_tool_time,
        },
        "tools": {
            "total_executions": len(executions),
            "failed_executions": len(failed_tools),
            "executions": [e.to_dict() for e in executions],
        },
        "sources": {
            "total_sources": len(sources),
            "by_tool": {
                tool: len(srcs) for tool, srcs in sources_by_tool.items()
            },
            "by_type": {
                source_type: len([s for s in sources if s.source_type == source_type])
                for source_type in SourceType
            },
        },
        "errors": [
            {"tool": e.tool_name, "error": e.error}
            for e in failed_tools
        ] if failed_tools else None,
    }
