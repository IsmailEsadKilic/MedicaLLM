"""
Transactional email delivery.

Two provider backends, selected at runtime by `settings.email_provider`:

* ``smtp`` (default) — sends via aiosmtplib over the configured SMTP
  server. Reliable when the host network allows outbound 465/587, but
  many cloud providers (DigitalOcean, GCP free tier, etc.) filter
  outbound SMTP by default to deter spam.

* ``resend`` — sends via Resend's HTTPS API
  (https://resend.com/docs/send-with-rest-api). Works on any host that
  can reach the public internet over port 443. Recommended fallback
  when SMTP is blocked.

Either provider falls back to a log-only mode when its credentials
aren't configured so dev workflows keep working without a real mail
server.

Configuration
-------------
Common to both providers:
    EMAIL_PROVIDER=smtp | resend
    PUBLIC_APP_URL=https://medicallm.com.tr
    SMTP_FROM_ADDRESS=noreply@medicallm.com.tr      # used for both
    SMTP_FROM_NAME=MedicaLLM                        # used for both

SMTP-specific:
    SMTP_HOST=smtp.hostinger.com
    SMTP_PORT=465
    SMTP_USERNAME=noreply@medicallm.com.tr
    SMTP_PASSWORD=<account password>
    SMTP_USE_SSL=true            # 465 SSL (Hostinger default)
    SMTP_USE_STARTTLS=false      # 587 STARTTLS — set true if using port 587

Resend-specific:
    RESEND_API_KEY=re_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
    RESEND_FROM_ADDRESS=noreply@medicallm.com.tr   # must be a verified
                                                    # domain in Resend

Security notes
--------------
* Credentials come from env, never from the codebase.
* Both code paths use a per-message timeout so a hung dependency can't
  pin a worker.
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
import httpx

from ..config import settings

logger = logging.getLogger(__name__)


# Hard upper bound so a misconfigured / unreachable mail backend never
# blocks an auth handler indefinitely. Kept tight (8s) because both
# providers respond well under a second when reachable; anything longer
# is almost always a network-level block.
_SMTP_TIMEOUT_SECONDS = 8
_RESEND_TIMEOUT_SECONDS = 8

# Resend REST endpoint. Hard-coded to the public production host —
# their docs explicitly recommend not making this configurable.
_RESEND_ENDPOINT = "https://api.resend.com/emails"


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


async def _send_via_resend(
    *, to: str, subject: str, text_body: str, html_body: str
) -> None:
    """Send via the Resend HTTPS API. Falls back when the API key isn't
    configured — caller treats RuntimeError as 'provider unavailable'."""
    api_key = settings.resend_api_key
    if not api_key:
        raise RuntimeError("Resend not configured (missing RESEND_API_KEY)")

    # Resolve the from address. Prefer explicit Resend setting, then the
    # generic SMTP_FROM_ADDRESS so a single env var works for both
    # providers, then fall back to the SMTP username.
    from_address = (
        settings.resend_from_address
        or settings.smtp_from_address
        or settings.smtp_username
    )
    if not from_address:
        raise RuntimeError(
            "Resend has no usable 'from' address — set RESEND_FROM_ADDRESS "
            "or SMTP_FROM_ADDRESS"
        )

    from_field = formataddr((settings.smtp_from_name or "MedicaLLM", from_address))
    payload = {
        "from": from_field,
        "to": [to],
        "subject": subject,
        "text": text_body,
        "html": html_body,
    }

    async with httpx.AsyncClient(timeout=_RESEND_TIMEOUT_SECONDS) as client:
        response = await client.post(
            _RESEND_ENDPOINT,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
        )

    if response.status_code >= 300:
        # Resend returns useful structured error bodies — surface them so
        # operators can spot misconfiguration (e.g. unverified domain).
        raise RuntimeError(
            f"Resend API rejected message with HTTP {response.status_code}: "
            f"{response.text[:500]}"
        )


async def send_verification_code(to_email: str, code: str) -> None:
    """Deliver a verification code. Routes to the configured provider
    (SMTP or Resend) and falls back to a warning log when no provider is
    configured — dev still works without a mail server.

    Never raises into the auth handler — a transient SMTP failure must not
    leak a 500 to the registration form. The code is also logged at
    WARNING level so an operator can manually deliver during an outage.
    """
    subject, text_body, html_body = _render_verification_email(code)
    provider = (settings.email_provider or "smtp").lower()

    # Treat the provider as unconfigured when its required credential is
    # missing — that way a typo in EMAIL_PROVIDER doesn't break sends, it
    # just falls back to log-only and prints the code.
    if provider == "resend" and not settings.resend_api_key:
        logger.warning(
            "[AUTH] EMAIL_PROVIDER=resend but RESEND_API_KEY is empty; "
            "falling back to log-only delivery."
        )
        provider = "noop"
    elif provider == "smtp" and not settings.smtp_host:
        logger.warning(
            "[AUTH] EMAIL_PROVIDER=smtp but SMTP_HOST is empty; falling "
            "back to log-only delivery."
        )
        provider = "noop"

    if provider == "noop":
        logger.warning(
            f"[AUTH] No mail provider configured — verification code "
            f"for {to_email}: {code}"
        )
        return

    try:
        if provider == "resend":
            await _send_via_resend(
                to=to_email, subject=subject,
                text_body=text_body, html_body=html_body,
            )
        else:
            message = _build_message(
                to=to_email, subject=subject,
                text_body=text_body, html_body=html_body,
            )
            await _send_via_smtp(message)
        logger.info(
            f"[AUTH] Verification email sent to {to_email} via {provider}"
        )
    except Exception as exc:
        logger.error(
            f"[AUTH] {provider} delivery failed for {to_email}: {exc}",
            exc_info=True,
        )
        # Last-ditch fallback: log the code so the operator can hand-deliver.
        logger.warning(
            f"[AUTH] Manual delivery hint — code for {to_email}: {code}"
        )
