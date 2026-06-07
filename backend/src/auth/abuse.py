"""
Registration abuse controls.

* Per-IP daily registration cap — caps how many accounts a single IP
  can spin up in a UTC day. Atomic upsert against
  `registration_attempts(ip_hash, day, count)` so concurrent requests
  can't both squeeze through.

* IPs are stored hashed (SHA-256 of `ip || jwt_secret`) so a DB leak
  doesn't enumerate the source IPs of legitimate signups. The hash is
  also short enough to index.

* Counters auto-roll at midnight UTC, same as the message quota. We
  rely on the unique `(ip_hash, day)` index for the atomic
  `INSERT ... ON CONFLICT DO UPDATE RETURNING count` pattern.
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone

from fastapi import HTTPException, status
from sqlalchemy import text

from ..config import settings
from ..db.sql_client import get_session

logger = logging.getLogger(__name__)


def _today_utc_str() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _hash_ip(ip: str) -> str:
    """SHA-256(ip || jwt_secret). The secret is just a per-deploy salt — it
    keeps the hash space unpredictable to an attacker who can guess IPs."""
    salted = f"{ip or 'unknown'}|{settings.jwt_secret}".encode("utf-8")
    return hashlib.sha256(salted).hexdigest()


def consume_registration_attempt(ip: str) -> None:
    """
    Atomically register one account-creation attempt for the given IP.
    Raises HTTPException 429 when the IP has already exceeded the daily
    cap; otherwise returns silently.

    Successful or failed registration both consume one attempt — this is
    intentional, otherwise an attacker could brute-force email enumeration
    by watching which addresses are 'already registered'.
    """
    limit = settings.registration_daily_ip_cap
    if limit <= 0:
        # Cap of 0 disables the gate (useful for tests / dev).
        return

    db = get_session()
    try:
        ip_hash = _hash_ip(ip)
        day = _today_utc_str()
        row = db.execute(
            text(
                """
                INSERT INTO registration_attempts (ip_hash, day, count)
                VALUES (:ip_hash, :day, 1)
                ON CONFLICT (ip_hash, day)
                DO UPDATE SET count = registration_attempts.count + 1
                RETURNING count
                """
            ),
            {"ip_hash": ip_hash, "day": day},
        ).first()
        db.commit()
        new_count = int(row[0]) if row else 0

        if new_count > limit:
            # Don't roll back on this counter — the failed attempt should
            # also count, otherwise an attacker can keep retrying without
            # ever crossing the threshold.
            logger.warning(
                "[AUTH] Registration cap hit for ip_hash=%s (count=%d, limit=%d)",
                ip_hash[:12], new_count, limit,
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "REGISTRATION_RATE_LIMITED",
                    "message": (
                        "Too many accounts have been created from this "
                        "network today. Please try again tomorrow."
                    ),
                },
            )
    finally:
        db.close()
