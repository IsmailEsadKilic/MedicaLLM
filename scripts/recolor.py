"""One-off color migration: violet/purple -> navy/blue across the frontend.

Replaces every mapped color in every .css/.jsx/.js file under frontend/src.
Whitespace inside rgba() is normalised to a single canonical form so we
catch both `139,92,246` and `139, 92, 246` etc.

Usage:
    python3 scripts/recolor.py frontend/src
"""
import re
import sys
from pathlib import Path

ROOT = Path(sys.argv[1])

# (pattern, replacement) — order matters: do the longer/more specific
# substitutions first so a shorter HEX doesn't accidentally swallow part of
# another color.
HEX_MAP = [
    # Violet (Tailwind violet-* family)
    ("#8b5cf6", "#3b82f6"),  # violet-500 -> blue-500   (primary accent)
    ("#a78bfa", "#60a5fa"),  # violet-400 -> blue-400
    ("#c4b5fd", "#93c5fd"),  # violet-300 -> blue-300
    ("#ddd6fe", "#bfdbfe"),  # violet-200 -> blue-200   (rare)
    ("#7c3aed", "#2563eb"),  # violet-600 -> blue-600
    ("#6d28d9", "#1d4ed8"),  # violet-700 -> blue-700
    ("#5b21b6", "#1e40af"),  # violet-800 -> blue-800   (rare)
    # Purple (Tailwind purple-*)
    ("#a855f7", "#3b82f6"),  # purple-500 -> blue-500
    ("#9333ea", "#1d4ed8"),  # purple-600 -> blue-700
    ("#c084fc", "#60a5fa"),  # purple-400 -> blue-400
    ("#d8b4fe", "#93c5fd"),  # purple-300 -> blue-300
    ("#7e22ce", "#1e40af"),  # purple-700 -> blue-800
    # Indigo (Tailwind indigo-*) — reads as "purple" in light mode against
    # white surfaces. Map to the same blue tones so the brand stays navy.
    ("#6366f1", "#3b82f6"),  # indigo-500 -> blue-500
    ("#4f46e5", "#2563eb"),  # indigo-600 -> blue-600
    ("#4338ca", "#1d4ed8"),  # indigo-700 -> blue-700
    ("#3730a3", "#1e40af"),  # indigo-800 -> blue-800
    ("#312e81", "#1e3a8a"),  # indigo-900 -> blue-900
    ("#818cf6", "#60a5fa"),  # indigo-400 -> blue-400
    ("#a5b4fc", "#93c5fd"),  # indigo-300 -> blue-300
    ("#c7d2fe", "#bfdbfe"),  # indigo-200 -> blue-200
]

# RGB triplets in the same order. We canonicalise spacing afterwards.
RGB_MAP = [
    ((139, 92, 246), (59, 130, 246)),    # violet-500 -> blue-500
    ((167, 139, 250), (96, 165, 250)),   # violet-400 -> blue-400
    ((196, 181, 253), (147, 197, 253)),  # violet-300 -> blue-300
    ((124, 58, 237), (37, 99, 235)),     # violet-600 -> blue-600
    ((109, 40, 217), (29, 78, 216)),     # violet-700 -> blue-700
    ((168, 85, 247), (59, 130, 246)),    # purple-500 -> blue-500
    ((147, 51, 234), (29, 78, 216)),     # purple-600 -> blue-700
    ((192, 132, 252), (96, 165, 250)),   # purple-400 -> blue-400
    # Indigo family (these read as purple in light mode)
    ((99, 102, 241), (59, 130, 246)),    # indigo-500 -> blue-500
    ((79, 70, 229), (37, 99, 235)),      # indigo-600 -> blue-600
    ((67, 56, 202), (29, 78, 216)),      # indigo-700 -> blue-700
    ((55, 48, 163), (30, 64, 175)),      # indigo-800 -> blue-800
    ((49, 46, 129), (30, 58, 138)),      # indigo-900 -> blue-900
    ((129, 140, 248), (96, 165, 250)),   # indigo-400 -> blue-400
    ((165, 180, 252), (147, 197, 253)),  # indigo-300 -> blue-300
    ((199, 210, 254), (191, 219, 254)),  # indigo-200 -> blue-200
]


def replace_hex(text: str) -> str:
    # Case-insensitive: hex colors can appear as #8B5CF6 too.
    for old, new in HEX_MAP:
        text = re.sub(re.escape(old), new, text, flags=re.IGNORECASE)
    return text


def replace_rgb(text: str) -> str:
    # Match rgba(R, G, B[, A]) and rgb(R, G, B) with arbitrary whitespace.
    triplet_re = re.compile(
        r"\b(rgba?)\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*"
        r"(,\s*[0-9.]+\s*)?\)",
    )

    rgb_lookup = {old: new for old, new in RGB_MAP}

    def sub(m: re.Match) -> str:
        fn = m.group(1)
        r, g, b = int(m.group(2)), int(m.group(3)), int(m.group(4))
        alpha_part = m.group(5) or ""
        new_rgb = rgb_lookup.get((r, g, b))
        if new_rgb is None:
            return m.group(0)
        nr, ng, nb = new_rgb
        if fn == "rgb":
            return f"rgb({nr}, {ng}, {nb})"
        return f"rgba({nr}, {ng}, {nb}{alpha_part})"

    return triplet_re.sub(sub, text)


def process_file(path: Path) -> bool:
    """Returns True when the file was modified."""
    original = path.read_text(encoding="utf-8")
    out = replace_hex(original)
    out = replace_rgb(out)
    if out != original:
        path.write_text(out, encoding="utf-8")
        return True
    return False


changed = []
for ext in ("css", "jsx", "js"):
    for p in ROOT.rglob(f"*.{ext}"):
        # Skip generated / vendored bundles
        if "node_modules" in p.parts or "dist" in p.parts:
            continue
        if process_file(p):
            changed.append(p)

print(f"Modified {len(changed)} files:")
for p in changed:
    print(f"  {p.relative_to(ROOT)}")
