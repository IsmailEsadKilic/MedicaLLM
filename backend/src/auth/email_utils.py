"""
Email canonicalisation + disposable-provider detection.

The free-tier daily quota is per-user. Without normalisation, a single
abuser can generate dozens of distinct UserRecord rows for the same
real mailbox (`john.doe@gmail.com`, `john.doe+1@gmail.com`,
`johndoe@gmail.com` are all the same Gmail inbox).

`canonicalize_email` collapses these into a single comparable form, and
`is_disposable_domain` rejects throwaway providers entirely. Both are
cheap, pure-Python, and run at registration time.
"""
from __future__ import annotations

import logging
import unicodedata
from pathlib import Path

logger = logging.getLogger(__name__)


# Domains where Gmail-style dot/+plus aliasing applies. Outlook / iCloud do
# NOT use the dot trick (they treat dots as significant), so we narrow the
# aggressive normalisation to the Google-hosted domains.
_GMAIL_LIKE_DOMAINS = frozenset({
    "gmail.com",
    "googlemail.com",
})

# Domains where the `+suffix` form is a recipient extension and can be
# stripped for de-duplication. Most major providers honour this, so we
# strip it broadly. Stripping here is conservative — it never changes
# what the user typed in the database, only what we hash for dupe checks.
_PLUS_ALIAS_DOMAINS = frozenset({
    "gmail.com",
    "googlemail.com",
    "outlook.com",
    "hotmail.com",
    "live.com",
    "icloud.com",
    "me.com",
    "yahoo.com",
    "ymail.com",
    "fastmail.com",
    "fastmail.fm",
    "protonmail.com",
    "proton.me",
})


def _load_disposable_domains() -> frozenset[str]:
    """Read the disposable-domain list shipped alongside this module."""
    path = Path(__file__).with_name("disposable_domains.txt")
    if not path.exists():
        logger.warning(
            "[AUTH] disposable_domains.txt not found at %s — disposable "
            "email rejection will be a no-op.",
            path,
        )
        return frozenset()
    domains: set[str] = set()
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip().lower()
        if not line or line.startswith("#"):
            continue
        domains.add(line)
    logger.info(f"[AUTH] Loaded {len(domains)} disposable email domains")
    return frozenset(domains)


# Loaded once per process. Tests can monkeypatch by importing this module
# and reassigning the attribute if needed.
DISPOSABLE_DOMAINS: frozenset[str] = _load_disposable_domains()


def normalize_email(email: str) -> str:
    """
    Casefold + strip Unicode noise. Used as the bare-minimum canonicalisation
    even when we don't want to be too aggressive (e.g. for the form field).
    """
    if not email:
        return ""
    # NFKC handles confusables like full-width '＠' or composed accents.
    return unicodedata.normalize("NFKC", email).strip().casefold()


def canonicalize_email(email: str) -> str:
    """
    Aggressive canonicalisation used for **dupe detection** only.

    Returns a stable string per real mailbox:
      - Lowercase + Unicode-normalised
      - Plus aliases stripped on providers that honour them
      - Dots removed from the local part on Gmail-family domains
      - The original local-part case is preserved in the stored `email`
        field; we only mutate this canonical copy

    Examples:
      'John.Doe+spam@Gmail.com'  → 'johndoe@gmail.com'
      'jane+work@outlook.com'    → 'jane@outlook.com'
      'sezer@medicallm.com.tr'   → 'sezer@medicallm.com.tr'   (untouched)
    """
    norm = normalize_email(email)
    if "@" not in norm:
        return norm

    local, _, domain = norm.rpartition("@")
    if not local or not domain:
        return norm

    if domain in _PLUS_ALIAS_DOMAINS and "+" in local:
        local = local.split("+", 1)[0]

    if domain in _GMAIL_LIKE_DOMAINS:
        local = local.replace(".", "")
        # Treat googlemail.com as gmail.com so `a@googlemail.com` and
        # `a@gmail.com` collapse to the same canonical form.
        domain = "gmail.com"

    return f"{local}@{domain}"


def email_domain(email: str) -> str:
    """Return the lowercase domain part of an email, or empty string."""
    norm = normalize_email(email)
    if "@" not in norm:
        return ""
    return norm.rpartition("@")[2]


def is_disposable_domain(email: str) -> bool:
    """True when the email's domain is on the disposable-providers list."""
    domain = email_domain(email)
    if not domain:
        return False
    return domain in DISPOSABLE_DOMAINS
