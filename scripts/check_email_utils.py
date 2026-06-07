"""Smoke test for src.auth.email_utils."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from src.auth.email_utils import canonicalize_email, is_disposable_domain  # noqa: E402

cases = [
    ("John.Doe+spam@Gmail.com", "johndoe@gmail.com"),
    ("john.doe@googlemail.com", "johndoe@gmail.com"),
    ("jane+work@outlook.com", "jane@outlook.com"),
    ("user@yahoo.com", "user@yahoo.com"),
    ("Sezer@MedicaLLM.com.tr", "sezer@medicallm.com.tr"),
    ("USER@PROTONMAIL.COM", "user@protonmail.com"),
    ("plain@example.com", "plain@example.com"),
]
ok = True
for inp, expected in cases:
    out = canonicalize_email(inp)
    mark = "✓" if out == expected else "✗"
    if out != expected:
        ok = False
    print(f"{mark} {inp!r:50s} -> {out!r}  (expected {expected!r})")

print()
disp_cases = [
    ("user@gmail.com", False),
    ("attacker@mailinator.com", True),
    ("a@10minutemail.com", True),
    ("foo@temp-mail.org", True),
    ("admin@medicallm.com.tr", False),
]
for email, expected in disp_cases:
    out = is_disposable_domain(email)
    mark = "✓" if out == expected else "✗"
    if out != expected:
        ok = False
    print(f"{mark} disposable {email!r:40s} = {out} (expected {expected})")

sys.exit(0 if ok else 1)
