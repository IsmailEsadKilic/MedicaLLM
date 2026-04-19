"""Test the markdown fixer utility"""

from src.agent.markdown_fixer import fix_markdown

# Test case: single-line table
test_input = """| # | Article (year) | Key take‑away ||---|----------------|---------------|| **1** | **The spectrum of clinical presentation** – *Pediatric Diabetes* (2015) | Highlights that mitochondrial DNA disorders can cause diabetes || **2** | **Nephrogenic diabetes insipidus** – *Journal* (2022) | Reviews the causes of NDI |"""

print("INPUT:")
print(test_input)
print("\n" + "="*80 + "\n")

fixed = fix_markdown(test_input)

print("OUTPUT:")
print(fixed)
print("\n" + "="*80 + "\n")

# Verify it has newlines
if '\n' in fixed and fixed.count('\n') > 2:
    print("✓ SUCCESS: Table has been split into multiple lines")
else:
    print("✗ FAILED: Table is still on one line")
