"""
IP hashing + day-bucket helpers from `auth.abuse`.

We don't go near the database here — those branches are exercised in
the integration suite where a real Postgres is available. The hash and
date-bucket helpers are pure and worth covering in isolation because a
typo in either silently breaks the whole rate-limiter.
"""
from datetime import datetime, timezone

from src.auth import abuse


def test_hash_ip_is_deterministic():
    """Same input + same secret → same digest. Otherwise the per-day
    counter would never increment for repeat offenders."""
    a = abuse._hash_ip("203.0.113.5")
    b = abuse._hash_ip("203.0.113.5")
    assert a == b


def test_hash_ip_distinguishes_inputs():
    a = abuse._hash_ip("203.0.113.5")
    b = abuse._hash_ip("203.0.113.6")
    assert a != b


def test_hash_ip_handles_blank():
    """Blank input shouldn't crash — proxy header could be missing."""
    digest = abuse._hash_ip("")
    assert isinstance(digest, str)
    assert len(digest) == 64  # sha256 hex


def test_today_utc_str_format():
    """The day-bucket key must be a YYYY-MM-DD string in UTC, since the
    Postgres column is a string column. Any drift to local time would
    let abusers cross UTC midnight on their local clock and get a fresh
    counter."""
    val = abuse._today_utc_str()
    # Must round-trip through datetime.strptime
    parsed = datetime.strptime(val, "%Y-%m-%d")
    assert parsed.year >= 2024  # sanity check, not future-proof beyond 2099
    # Must equal today in UTC.
    today_utc = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert val == today_utc
