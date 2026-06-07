"""
SMTP-based transactional email delivery.

Sends a single, branded HTML+text message via the configured SMTP
provider (Hostinger out of the box, but any host that takes SMTP works).

Falls back to log-only delivery when `settings.smtp_host` is empty so the
local dev environment never tries to connect to a real mail server.

Configuration
-------------
Set these in `.env` to enable real delivery:

    SMTP_HOST=smtp.hostinger.com
    SMTP_PORT=465
    SMTP_USERNAME=noreply@medicallm.com.tr
    SMTP_PASSWORD=<account password>
    SMTP_USE_SSL=true            # 465 SSL (Hostinger default)
    SMTP_USE_STARTTLS=false      # 587 STARTTLS — set true if using port 587
    SMTP_FROM_ADDRESS=noreply@medicallm.com.tr
    SMTP_FROM_NAME=MedicaLLM
    PUBLIC_APP_URL=https://medicallm.com.tr

Security notes
--------------
* Passwords come from env, never from the codebase.
* `aiosmtplib` is async-native so calling this from a FastAPI handler
  doesn't block the event loop. We wrap each send in a per-message
  timeout so a hung mail server can't pin a worker.
* The SUBJECT/BODY is always rendered server-side from the template
  below; user-controlled content is escaped before interpolation.
"""
from __future__ import annotations

import asyncio
import html
import logging
import ssl
from email.message import EmailMessage
from email.utils import formataddr

import aiosmtplib

from ..config import settings

logger = logging.getLogger(__name__)


# Hard upper bound so a misconfigured / unreachable SMTP server never
# blocks an auth handler indefinitely. Kept tight (8s) because Hostinger
# and most consumer SMTPs respond well under a second when reachable;
# anything longer is almost always a network-level block (cloud hosts
# often filter outbound 25/465 by default).
_SMTP_TIMEOUT_SECONDS = 8


def _from_header() -> str:
    """Build a 'Name <addr>' From header from the configured fields."""
    address = settings.smtp_from_address or settings.smtp_username
    if not address:
        return ""
    name = settings.smtp_from_name or "MedicaLLM"
    return formataddr((name, address))


def _render_verification_email(code: str) -> tuple[str, str, str]:
    """Return (subject, plain_text_body, html_body) for the verification mail.

    The code is interpolated as plain digits — but we still HTML-escape the
    template variables defensively in case future content includes
    user-typed strings.
    """
    safe_code = html.escape(code)
    safe_app_url = html.escape(settings.public_app_url or "https://medicallm.com.tr")
    subject = "Your MedicaLLM verification code"
    text = (
        f"Welcome to MedicaLLM!\n\n"
        f"Your verification code is: {code}\n\n"
        f"Enter this code on the registration page to complete your sign-up.\n"
        f"The code expires in 10 minutes.\n\n"
        f"If you didn't request this email, you can safely ignore it.\n\n"
        f"— The MedicaLLM team\n"
        f"{settings.public_app_url}\n"
    )
    html_body = f"""\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>{subject}</title>
</head>
<body style="margin:0;padding:0;background:#f4f6fb;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Inter',sans-serif;color:#0f172a;">
    <div style="max-width:520px;margin:0 auto;padding:32px 16px;">
        <div style="background:#ffffff;border-radius:14px;padding:32px;box-shadow:0 12px 28px rgba(15,23,42,0.06);">
            <div style="font-size:18px;font-weight:700;color:#1d4ed8;margin-bottom:16px;letter-spacing:0.02em;">
                MedicaLLM
            </div>
            <h1 style="font-size:22px;margin:0 0 12px;color:#0f172a;font-weight:700;">
                Verify your email
            </h1>
            <p style="font-size:14px;line-height:1.55;color:#334155;margin:0 0 24px;">
                Use the code below to finish setting up your MedicaLLM account.
                The code expires in 10&nbsp;minutes.
            </p>
            <div style="font-family:ui-monospace,Menlo,Consolas,monospace;font-size:32px;font-weight:700;letter-spacing:0.5em;text-align:center;padding:18px 0;background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;color:#1d4ed8;margin-bottom:24px;">
                {safe_code}
            </div>
            <p style="font-size:13px;line-height:1.5;color:#64748b;margin:0 0 0;">
                Didn&apos;t request this? You can safely ignore this email — no
                account will be created.
            </p>
        </div>
        <div style="text-align:center;color:#94a3b8;font-size:11px;margin-top:18px;">
            <a href="{safe_app_url}" style="color:#94a3b8;text-decoration:none;">{safe_app_url}</a>
        </div>
    </div>
</body>
</html>"""
    return subject, text, html_body


def _build_message(
    *, to: str, subject: str, text_body: str, html_body: str
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = _from_header()
    msg["To"] = to
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")
    return msg


async def _send_via_smtp(message: EmailMessage) -> None:
    """Open one short-lived TLS connection per message — Hostinger and most
    consumer SMTP servers don't allow long-lived clients anyway."""
    host = settings.smtp_host
    port = settings.smtp_port
    username = settings.smtp_username
    password = settings.smtp_password
    use_ssl = settings.smtp_use_ssl
    use_starttls = settings.smtp_use_starttls and not use_ssl

    if not host or not username or not password:
        raise RuntimeError(
            "SMTP not configured (missing host / username / password)"
        )

    tls_context = ssl.create_default_context()
    await asyncio.wait_for(
        aiosmtplib.send(
            message,
            hostname=host,
            port=port,
            username=username,
            password=password,
            use_tls=use_ssl,         # 465 = SSL/TLS from connect
            start_tls=use_starttls,  # 587 = STARTTLS upgrade
            tls_context=tls_context,
            timeout=_SMTP_TIMEOUT_SECONDS,
        ),
        timeout=_SMTP_TIMEOUT_SECONDS + 5,  # outer guard
    )


async def send_verification_code(to_email: str, code: str) -> None:
    """Deliver a verification code. Falls back to a warning log when SMTP
    isn't configured so dev still works without a mail server.

    Never raises into the auth handler — a transient SMTP failure must not
    leak a 500 to the registration form. The code is also logged at INFO
    level so an operator can manually deliver during an outage.
    """
    subject, text_body, html_body = _render_verification_email(code)

    if not settings.smtp_host:
        # Dev / unconfigured deployment — keep the legacy log-only behaviour
        # so the developer can copy the code from the server log.
        logger.warning(
            f"[AUTH] SMTP unconfigured — verification code for {to_email}: {code}"
        )
        return

    try:
        message = _build_message(
            to=to_email, subject=subject,
            text_body=text_body, html_body=html_body,
        )
        await _send_via_smtp(message)
        logger.info(f"[AUTH] Verification email sent to {to_email}")
    except Exception as exc:
        logger.error(
            f"[AUTH] SMTP delivery failed for {to_email}: {exc}", exc_info=True
        )
        # Last-ditch fallback: log the code so the operator can hand-deliver.
        logger.warning(
            f"[AUTH] Manual delivery hint — code for {to_email}: {code}"
        )
