"""End-to-end smoke test for the daily message quota.

What it does (idempotent — safe to re-run):

1. Creates a throwaway user in the live DB if one doesn't exist
   (email = `quota-test+{epoch}@example.com`)
2. Calls `consume_message(user_id)` 21 times in sequence
3. Asserts:
     - Calls 1..20 succeed and `remaining` decreases monotonically
     - Call 21 raises HTTPException(429) with code DAILY_QUOTA_EXCEEDED
     - The DB row for today shows count == 20 (rolled back from 21)
4. Sets the user as premium and calls `consume_message` once more —
   should succeed regardless of the previous 20.
5. Cleans up: deletes the throwaway user (cascades to daily_message_usage).

Usage on the droplet:
    docker compose -f compose.yml -f compose.prod.yml exec backend \\
        python -m scripts.test_quota
"""
from __future__ import annotations

import sys
import time
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import text

from src.db.sql_client import get_session
from src.db.sql_models import UserRecord
from src.quota.service import consume_message, get_quota_status


GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
RESET = "\033[0m"


def ok(msg: str) -> None:
    print(f"{GREEN}✓{RESET} {msg}")


def fail(msg: str) -> None:
    print(f"{RED}✗{RESET} {msg}")


def info(msg: str) -> None:
    print(f"{YELLOW}…{RESET} {msg}")


def make_test_user() -> tuple[str, int]:
    """Create a fresh user row, return (user_id, user_pk)."""
    db = get_session()
    try:
        epoch = int(time.time())
        email = f"quota-test+{epoch}@example.com"
        user_id = f"user_{uuid.uuid4().hex}"
        now = datetime.now(timezone.utc).isoformat()
        rec = UserRecord(
            user_id=user_id,
            email=email,
            email_canonical=email,
            password="$2b$12$dummy.hash.value.never.matched.for.login",
            name="Quota Test",
            is_premium=False,
            created_at=now,
            updated_at=now,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)
        return user_id, rec.id
    finally:
        db.close()


def cleanup_user(user_pk: int) -> None:
    db = get_session()
    try:
        db.execute(text("DELETE FROM users WHERE id = :pk"), {"pk": user_pk})
        db.commit()
    finally:
        db.close()


def main() -> int:
    info("Creating throwaway user...")
    user_id, user_pk = make_test_user()
    ok(f"User created: user_id={user_id} pk={user_pk}")

    failures = 0
    try:
        info("Calling consume_message 20 times (each must succeed)...")
        for i in range(1, 21):
            try:
                result = consume_message(user_id)
            except Exception as e:
                fail(f"Call #{i} unexpectedly raised: {e}")
                failures += 1
                continue
            expected_remaining = 20 - i
            if result.used_today != i:
                fail(
                    f"Call #{i}: used_today={result.used_today}, expected {i}"
                )
                failures += 1
            elif result.remaining != expected_remaining:
                fail(
                    f"Call #{i}: remaining={result.remaining}, "
                    f"expected {expected_remaining}"
                )
                failures += 1
        if failures == 0:
            ok("All 20 calls accepted; counter monotonic.")

        info("21st call must raise HTTPException(429)...")
        raised = False
        try:
            consume_message(user_id)
        except HTTPException as e:
            if e.status_code == 429:
                detail = e.detail or {}
                if isinstance(detail, dict) and detail.get("code") == "DAILY_QUOTA_EXCEEDED":
                    ok(
                        f"21st call raised 429 with structured detail "
                        f"(daily_limit={detail.get('daily_limit')})"
                    )
                    raised = True
                else:
                    fail(f"21st raised 429 but detail not structured: {detail}")
                    failures += 1
            else:
                fail(f"21st raised HTTPException with status {e.status_code}")
                failures += 1
        except Exception as e:
            fail(f"21st raised wrong exception type: {type(e).__name__}: {e}")
            failures += 1
        if not raised and failures == 0:
            fail("21st call did NOT raise — quota guard is broken")
            failures += 1

        info("Verifying counter was rolled back to 20 in DB...")
        snapshot = get_quota_status(user_id)
        if snapshot.used_today == 20:
            ok(f"DB counter == 20 (failed attempt did not bleed into tomorrow)")
        else:
            fail(
                f"DB counter == {snapshot.used_today} (expected 20). "
                f"Counter rollback may be broken."
            )
            failures += 1

        info("Flipping is_premium=True and calling consume_message...")
        db = get_session()
        try:
            db.execute(
                text("UPDATE users SET is_premium = TRUE WHERE user_id = :uid"),
                {"uid": user_id},
            )
            db.commit()
        finally:
            db.close()

        try:
            result = consume_message(user_id)
            if result.is_premium and result.daily_limit == -1:
                ok("Premium user bypasses quota (daily_limit=-1, unlimited)")
            else:
                fail(
                    f"Premium call returned wrong shape: "
                    f"is_premium={result.is_premium}, daily_limit={result.daily_limit}"
                )
                failures += 1
        except Exception as e:
            fail(f"Premium call unexpectedly raised: {e}")
            failures += 1

    finally:
        info("Cleaning up throwaway user...")
        cleanup_user(user_pk)
        ok(f"Deleted user_pk={user_pk}")

    print()
    if failures:
        print(f"{RED}❌ {failures} check(s) failed{RESET}")
        return 1
    print(f"{GREEN}✅ All quota checks passed{RESET}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
