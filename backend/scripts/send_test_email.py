"""Quick SMTP smoke test.

Reads the SMTP_* env vars (or .env), sends a single verification email,
and exits 0 on success. Useful as the first thing you run after setting
up the Hostinger mailbox to confirm credentials + DNS are working.

Usage (from /opt/medicallm on the droplet):
    docker compose -f compose.yml -f compose.prod.yml exec backend \\
        python -m scripts.send_test_email you@example.com

Or locally:
    cd backend && uv run scripts/send_test_email.py you@example.com
"""
import asyncio
import sys
from pathlib import Path

# Allow `python scripts/send_test_email.py` from the backend root.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.auth.email_sender import send_verification_code


async def main() -> int:
    if len(sys.argv) < 2:
        print("Usage: send_test_email.py <recipient@example.com>", file=sys.stderr)
        return 2
    recipient = sys.argv[1]
    code = "123456"
    print(f"Sending test verification email to {recipient}...")
    await send_verification_code(recipient, code)
    print("Done. Check the inbox (and spam folder).")
    return 0


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
