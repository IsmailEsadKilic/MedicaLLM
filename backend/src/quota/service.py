"""
Daily-message quota for the free tier.

Design goals
------------
* Premium users (`UserRecord.is_premium = True`) bypass the quota entirely.
* Free users get `settings.free_daily_message_quota` messages per UTC day.
* Counter increments are race-free under concurrency: we use Postgres'
  `INSERT ... ON CONFLICT DO UPDATE ... RETURNING count` which is atomic
  on a unique `(user_pk, day)` index. Two concurrent requests for the same
  user on the same day will both observe distinct, monotonically increasing
  counts — neither can read the same value and both succeed.
* Failures bubble up as 429 with structured detail so the frontend can
  show a friendly upgrade prompt.

Why an upsert + conditional rollback (instead of a SELECT + UPDATE)?
SELECT-FOR-UPDATE on the daily row would also work but takes a row lock
for the whole request lifetime. The upsert is a single-statement,
short-lived transaction so it has zero impact on streaming latency.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import NamedTuple

from fastapi import HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session as OrmSession

from ..config import settings
from ..db.sql_client import get_session
from ..db.sql_models import UserRecord


class QuotaCheckResult(NamedTuple):
    """Returned by `consume_message`. `count` is the post-increment value."""
    is_premium: bool
    used_today: int
    daily_limit: int
    remaining: int


def _today_utc_str() -> str:
    """Use UTC so the rollover is consistent across users in any timezone."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


def _atomic_increment(db: OrmSession, user_pk: int, day: str) -> int:
    """
    Atomically increment the counter for (user_pk, day) and return the new
    value. Creates the row if it doesn't exist yet.

    Implemented as a Postgres-specific upsert because that's the runtime
    target. SQLite (used in some local dev setups) doesn't support
    `RETURNING` in upserts, but the rest of the app already requires
    Postgres for pgvector + pg_trgm so this is fine.
    """
    stmt = text(
        """
        INSERT INTO daily_message_usage (user_pk, day, count)
        VALUES (:user_pk, :day, 1)
        ON CONFLICT (user_pk, day)
        DO UPDATE SET count = daily_message_usage.count + 1
        RETURNING count
        """
    )
    row = db.execute(stmt, {"user_pk": user_pk, "day": day}).first()
    db.commit()
    return int(row[0]) if row else 0


def _decrement_on_rollback(db: OrmSession, user_pk: int, day: str) -> None:
    """Roll the counter back by one when the caller decided not to spend it.

    Used after we increment but discover the user has just exceeded the
    quota — we want the failed attempt NOT to count.
    """
    stmt = text(
        """
        UPDATE daily_message_usage
        SET count = GREATEST(count - 1, 0)
        WHERE user_pk = :user_pk AND day = :day
        """
    )
    db.execute(stmt, {"user_pk": user_pk, "day": day})
    db.commit()


def consume_message(user_id: str) -> QuotaCheckResult:
    """
    Atomically register one message against the user's daily quota.

    Raises:
        HTTPException 429 with structured body when the user is on the free
            tier and has already exhausted their daily messages.
    """
    db = get_session()
    try:
        user = (
            db.query(UserRecord)
            .filter(UserRecord.user_id == user_id)
            .one_or_none()
        )
        if user is None:
            # Treated as auth failure — this should have been caught upstream
            # but we don't want to silently grant unlimited usage to a ghost
            # user_id either.
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated user not found",
            )

        if user.is_premium:
            return QuotaCheckResult(
                is_premium=True,
                used_today=0,
                daily_limit=-1,  # sentinel: unlimited
                remaining=-1,
            )

        day = _today_utc_str()
        new_count = _atomic_increment(db, user.id, day)
        limit = settings.free_daily_message_quota

        if new_count > limit:
            # The increment was atomic so `new_count` is the user's true post-
            # increment value. Roll back the +1 we just took so the failed
            # attempt doesn't count against tomorrow either.
            _decrement_on_rollback(db, user.id, day)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "code": "DAILY_QUOTA_EXCEEDED",
                    "message": (
                        "You have reached the daily message limit for the "
                        "free tier. The counter resets at midnight UTC."
                    ),
                    "daily_limit": limit,
                    "used_today": limit,
                    "is_premium": False,
                },
            )

        return QuotaCheckResult(
            is_premium=False,
            used_today=new_count,
            daily_limit=limit,
            remaining=max(limit - new_count, 0),
        )
    finally:
        db.close()


def get_quota_status(user_id: str) -> QuotaCheckResult:
    """Read-only snapshot for the UI. Does NOT increment the counter."""
    db = get_session()
    try:
        user = (
            db.query(UserRecord)
            .filter(UserRecord.user_id == user_id)
            .one_or_none()
        )
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authenticated user not found",
            )

        if user.is_premium:
            return QuotaCheckResult(
                is_premium=True,
                used_today=0,
                daily_limit=-1,
                remaining=-1,
            )

        day = _today_utc_str()
        row = db.execute(
            text(
                "SELECT count FROM daily_message_usage "
                "WHERE user_pk = :user_pk AND day = :day"
            ),
            {"user_pk": user.id, "day": day},
        ).first()
        used = int(row[0]) if row else 0
        limit = settings.free_daily_message_quota
        return QuotaCheckResult(
            is_premium=False,
            used_today=used,
            daily_limit=limit,
            remaining=max(limit - used, 0),
        )
    finally:
        db.close()


def set_premium_by_email(email: str, premium: bool) -> bool:
    """Toggle premium status for the user with the given email.

    Returns True if a user row was updated, False if no match was found.
    Email is matched case-insensitively (stored values are normalised at
    registration but operators may type them in any case).
    """
    db = get_session()
    try:
        user = (
            db.query(UserRecord)
            .filter(UserRecord.email.ilike(email.strip()))
            .one_or_none()
        )
        if user is None:
            return False
        user.is_premium = bool(premium)
        db.commit()
        return True
    finally:
        db.close()


def list_premium_users() -> list[dict]:
    """Return all premium users for the admin panel."""
    db = get_session()
    try:
        rows = (
            db.query(UserRecord)
            .filter(UserRecord.is_premium.is_(True))
            .order_by(UserRecord.email)
            .all()
        )
        return [
            {"user_id": u.user_id, "email": u.email, "name": u.name}
            for u in rows
        ]
    finally:
        db.close()
