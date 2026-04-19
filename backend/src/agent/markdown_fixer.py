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
