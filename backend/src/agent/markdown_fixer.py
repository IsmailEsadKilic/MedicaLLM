"""
Markdown formatting utilities to fix common LLM markdown generation issues.
"""

import re


def fix_single_line_tables(text: str) -> str:
    """
    Fix markdown tables that are generated on a single line by adding proper line breaks.
    
    Converts:
        | Col1 | Col2 ||------|------|| Data1 | Data2 || Data3 | Data4 |
    
    To:
        | Col1 | Col2 |
        |------|------|
        | Data1 | Data2 |
        | Data3 | Data4 |
    
    Args:
        text: The markdown text potentially containing single-line tables
        
    Returns:
        The text with properly formatted tables
    """
    # Pattern to match single-line tables with double pipes ||
    # This pattern looks for sequences of | content | content || content | content ||
    pattern = r'\|([^|]+\|)+\|([^|]+\|)+'
    
    def fix_table_match(match):
        table_text = match.group(0)
        
        # Check if this is actually a compressed table (has || patterns)
        if '||' not in table_text:
            return table_text  # Already properly formatted
        
        # Split by || to get rows
        rows = table_text.split('||')
        
        # Clean up each row
        fixed_rows = []
        for row in rows:
            row = row.strip()
            if row:
                # Ensure row starts and ends with |
                if not row.startswith('|'):
                    row = '|' + row
                if not row.endswith('|'):
                    row = row + '|'
                fixed_rows.append(row)
        
        # Join rows with newlines
        return '\n'.join(fixed_rows)
    
    # Find and fix all single-line tables
    fixed_text = text
    
    # Look for patterns like || that indicate compressed tables
    if '||' in text:
        # Split by paragraphs to avoid breaking non-table content
        paragraphs = text.split('\n\n')
        fixed_paragraphs = []
        
        for para in paragraphs:
            # Check if this paragraph contains a compressed table
            if '||' in para and '|' in para:
                # Try to fix it
                lines = para.split('\n')
                fixed_lines = []
                
                for line in lines:
                    if '||' in line and line.count('|') > 4:  # Likely a compressed table
                        # Split by ||
                        rows = line.split('||')
                        for row in rows:
                            row = row.strip()
                            if row:
                                if not row.startswith('|'):
                                    row = '|' + row
                                if not row.endswith('|'):
                                    row = row + '|'
                                fixed_lines.append(row)
                    else:
                        fixed_lines.append(line)
                
                fixed_paragraphs.append('\n'.join(fixed_lines))
            else:
                fixed_paragraphs.append(para)
        
        fixed_text = '\n\n'.join(fixed_paragraphs)
    
    return fixed_text


def ensure_proper_markdown_spacing(text: str) -> str:
    """
    Ensure proper spacing around markdown elements.
    
    Args:
        text: The markdown text
        
    Returns:
        The text with proper spacing
    """
    # Ensure blank lines before and after tables
    text = re.sub(r'([^\n])\n(\|[^\n]+\|)\n', r'\1\n\n\2\n', text)
    text = re.sub(r'\n(\|[^\n]+\|)\n([^\n|])', r'\n\1\n\n\2', text)
    
    # Ensure blank lines before headings
    text = re.sub(r'([^\n])\n(#{1,6} )', r'\1\n\n\2', text)
    
    return text


def fix_markdown(text: str) -> str:
    """
    Apply all markdown fixes to the text.
    
    Args:
        text: The markdown text from the LLM
        
    Returns:
        The fixed markdown text
    """
    text = fix_single_line_tables(text)
    text = ensure_proper_markdown_spacing(text)
    return text


# ── Allowed heading patterns for PubMed responses ──────────────────────────
_ALLOWED_HEADINGS_RE = re.compile(
    r"^#{1,3}\s*(short\s*answer|evidence\s*summary|limitations)",
    re.IGNORECASE,
)

# Forbidden section markers — matches both markdown headings and plain text
_FORBIDDEN_SECTION_RE = re.compile(
    r"^(?:#{1,3}\s*|(?:\*\*))?"  # optional ## or **
    r"("
    r"clinical\s*(implications|recommendations|decision|guidance)"
    r"|practical\s*(guidance|recommendations|approach)"
    r"|decision[\s\-]*making"
    r"|bottom\s*line"
    r"|take[\s\-]*away"
    r"|alternative\s*(therap|options|symptom)"
    r"|key\s*references"
    r"|references\s*$"
    r"|sources\s*$"
    r"|what\s+(this|it)\s+means"
    r"|consider\s+surveillance"
    r"|re[\-\s]*evaluate"
    r"|treat\s+with\s+a\s+multi"
    r"|individuali[sz]e"
    r"|discuss\s+the\s+incremental"
    r"|evidence[\s\-]*based\s+alternatives"
    r"|why\s+the\s+concern"
    r"|important\s*:"
    r"|risk\s+stratification"
    r"|assess\s+benefits"
    r"|weigh\s+risks"
    r"|shared\s+decision"
    r"|if\s+you\s+decide"
    r")",
    re.IGNORECASE,
)

# Numbered top-level section heading: "1. Some Title" (at least 2 words after number)
# This catches hallucinated elaboration sections like "1. Why the concern?"
_NUMBERED_HEADING_RE = re.compile(
    r"^\d+\.\s+[A-Z][a-z]+(?:\s+\w+)+",  # e.g. "1. Why the concern?"
)


def strip_hallucinated_sections(text: str, has_pubmed_sources: bool = False) -> str:
    """Remove hallucinated content beyond the allowed 3-section structure.

    Only applies when PubMed sources were retrieved.

    Strategy (cascading):
    1. If ``## Limitations`` heading exists, keep everything up to the end of
       that section and truncate the rest.
    2. Otherwise, if ``## Short Answer`` or ``## Evidence Summary`` exist,
       strip everything before the first allowed heading AND strip forbidden
       sections after.
    3. Otherwise, do best-effort forbidden-pattern stripping on the raw text.
    """
    if not has_pubmed_sources:
        return text

    lines = text.split("\n")

    # ── Strategy 1: truncate after ## Limitations ────────────────────────
    limitations_start = None
    next_heading_after_limitations = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("#") and re.match(r"^#{1,3}\s*limitations", stripped, re.IGNORECASE):
            limitations_start = i
        elif limitations_start is not None and stripped.startswith("#") and i > limitations_start:
            next_heading_after_limitations = i
            break

    if limitations_start is not None:
        # Find first allowed heading to strip preamble
        first_allowed = None
        for i, line in enumerate(lines):
            if line.strip().startswith("#") and _ALLOWED_HEADINGS_RE.match(line.strip()):
                first_allowed = i
                break
        start = first_allowed if first_allowed is not None else 0
        end = next_heading_after_limitations if next_heading_after_limitations is not None else len(lines)
        return "\n".join(lines[start:end]).rstrip()

    # ── Strategy 2: allowed headings exist but no ## Limitations ─────────
    first_allowed = None
    for i, line in enumerate(lines):
        if line.strip().startswith("#") and _ALLOWED_HEADINGS_RE.match(line.strip()):
            first_allowed = i
            break

    if first_allowed is not None:
        lines = lines[first_allowed:]
        # Strip forbidden heading sections
        result = []
        in_forbidden = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith("#"):
                if _FORBIDDEN_SECTION_RE.search(stripped):
                    in_forbidden = True
                    continue
                else:
                    in_forbidden = False
            if not in_forbidden:
                result.append(line)
        return "\n".join(result).rstrip()

    # ── Strategy 3: no markdown headings at all — aggressive truncation ───
    # The model writes "Short answer:\n...\n\n1. Why the concern?\n..."
    # Everything from the first numbered section heading onwards is hallucinated.
    # Also catch plain-text forbidden markers.
    truncate_at = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        # Numbered section heading: "1. Some Title With Multiple Words"
        if _NUMBERED_HEADING_RE.match(stripped):
            truncate_at = i
            break
        # Plain-text forbidden markers
        if _FORBIDDEN_SECTION_RE.search(stripped):
            truncate_at = i
            break

    if truncate_at is not None and truncate_at > 0:
        return "\n".join(lines[:truncate_at]).rstrip()

    return text.rstrip()
