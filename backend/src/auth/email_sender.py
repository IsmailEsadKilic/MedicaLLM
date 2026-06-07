"""
Transactional email delivery — supports two backends:

* **Resend** (HTTPS API, recommended on cloud hosts that block outbound
  SMTP — DigitalOcean blocks ports 25/465/587 by default).
* **SMTP** (Hostinger or any generic SMTP server) — kept as a fallback so
  on-prem / unblocked deployments can use direct mail.

Selection logic
---------------
`settings.email_provider` controls which backend is used:

* ``"resend"`` — always Resend; raises if no API key is set.
* ``"smtp"``   — always SMTP.
* ``"auto"`` (default) — Resend when ``RESEND_API_KEY`` is set, else SMTP
  when ``SMTP_HOST`` is set, else log-only (dev fallback).

The public entrypoint is `send_verification_code(to, code)` — same
signature as before so callers (`auth.service`, `scripts.send_test_email`)
don't change.

Security notes
--------------
* Credentials come from env, never the codebase.
* Each send is wrapped in a tight timeout so a misbehaving provider
  cannot pin a FastAPI worker.
* Failures never bubble into the auth handler — they're logged and the
  code is recorded so an operator can hand-deliver during an outage.
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


# Hard upper bound so a misconfigured / unreachable provider never
# blocks an auth handler indefinitely. Resend's API typically responds
# in 200-400ms; SMTP under a second when the network path is open.
_SEND_TIMEOUT_SECONDS = 8

_RESEND_API_URL = "https://api.resend.com/emails"


# ──────────────────────────────────────────────────────────────────────
# Template — shared by both backends
# ──────────────────────────────────────────────────────────────────────


def _render_verification_email(code: str) -> tuple[str, str, str]:
    """Return (subject, plain_text_body, html_body) for the verification mail.

    The code is interpolated as plain digits — but we still HTML-escape the
    template variables defensively in case future content includes
    user-typed strings.
    """
    safe_code = html.escape(code)
    safe_app_url = html.escape(settings.public_app_url or "https://medicallm.com.tr")
    subject = "MedicaLLM doğrulama kodunuz"
    text = (
        f"MedicaLLM'e hoş geldiniz!\n\n"
        f"Doğrulama kodunuz: {code}\n\n"
        f"Kaydınızı tamamlamak için bu kodu kayıt sayfasına girin.\n"
        f"Kodun süresi 10 dakika sonra dolar.\n\n"
        f"Bu e-postayı talep etmediyseniz dikkate almayabilirsiniz.\n\n"
        f"— MedicaLLM ekibi\n"
        f"{settings.public_app_url}\n"
    )
    html_body = f"""\
<!DOCTYPE html>
<html lang="tr">
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
                E-postanızı doğrulayın
            </h1>
            <p style="font-size:14px;line-height:1.55;color:#334155;margin:0 0 24px;">
                MedicaLLM hesabınızı tamamlamak için aşağıdaki kodu kullanın.
                Kodun süresi 10&nbsp;dakika sonra dolar.
            </p>
            <div style="font-family:ui-monospace,Menlo,Consolas,monospace;font-size:32px;font-weight:700;letter-spacing:0.5em;text-align:center;padding:18px 0;background:#eff6ff;border:1px solid #bfdbfe;border-radius:10px;color:#1d4ed8;margin-bottom:24px;">
                {safe_code}
            </div>
            <p style="font-size:13px;line-height:1.5;color:#64748b;margin:0 0 0;">
                Bu işlemi siz başlatmadıysanız bu e-postayı yok sayabilirsiniz —
                hesap oluşturulmaz.
            </p>
        </div>
        <div style="text-align:center;color:#94a3b8;font-size:11px;margin-top:18px;">
            <a href="{safe_app_url}" style="color:#94a3b8;text-decoration:none;">{safe_app_url}</a>
        </div>
    </div>
</body>
</html>"""
    return subject, text, html_body


# ──────────────────────────────────────────────────────────────────────
# Backend: Resend
# ──────────────────────────────────────────────────────────────────────


async def _send_via_resend(*, to: str, subject: str, text_body: str, html_body: str) -> None:
    """POST to the Resend API. Raises on non-2xx so the caller can log/fall back."""
    api_key = settings.resend_api_key
    if not api_key:
        raise RuntimeError("Resend selected but RESEND_API_KEY is not set")

    payload: dict = {
        "from": settings.resend_from_address,
        "to": [to],
        "subject": subject,
        "html": html_body,
        "text": text_body,
    }
    if settings.resend_reply_to:
        payload["reply_to"] = settings.resend_reply_to

    timeout = httpx.Timeout(_SEND_TIMEOUT_SECONDS, connect=5.0)
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(_RESEND_API_URL, json=payload, headers=headers)
        body = resp.text
        if resp.status_code >= 400:
            # Resend returns JSON like {"statusCode":422,"message":"..."}.
            # Don't log the API key — only echo response body.
            raise RuntimeError(f"Resend API {resp.status_code}: {body[:500]}")
        logger.debug(f"[AUTH] Resend accepted message: {body[:200]}")


# ──────────────────────────────────────────────────────────────────────
# Backend: SMTP (Hostinger / generic)
# ──────────────────────────────────────────────────────────────────────


def _smtp_from_header() -> str:
    address = settings.smtp_from_address or settings.smtp_username
    if not address:
        return ""
    name = settings.smtp_from_name or "MedicaLLM"
    return formataddr((name, address))


def _build_smtp_message(*, to: str, subject: str, text_body: str, html_body: str) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = _smtp_from_header()
    msg["To"] = to
    msg.set_content(text_body)
    msg.add_alternative(html_body, subtype="html")
    return msg


async def _send_via_smtp(*, to: str, subject: str, text_body: str, html_body: str) -> None:
    host = settings.smtp_host
    port = settings.smtp_port
    username = settings.smtp_username
    password = settings.smtp_password
    use_ssl = settings.smtp_use_ssl
    use_starttls = settings.smtp_use_starttls and not use_ssl

    if not host or not username or not password:
        raise RuntimeError("SMTP not configured (missing host / username / password)")

    message = _build_smtp_message(
        to=to, subject=subject, text_body=text_body, html_body=html_body
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
            timeout=_SEND_TIMEOUT_SECONDS,
        ),
        timeout=_SEND_TIMEOUT_SECONDS + 5,  # outer guard
    )


# ──────────────────────────────────────────────────────────────────────
# Provider selection
# ──────────────────────────────────────────────────────────────────────


def _resolve_provider() -> str:
    """Return the active backend name: 'resend', 'smtp', or 'none'.

    'none' means we should log the code and return — no real delivery.
    """
    explicit = (settings.email_provider or "auto").strip().lower()
    has_resend = bool(settings.resend_api_key)
    has_smtp = bool(settings.smtp_host)

    if explicit == "resend":
        return "resend" if has_resend else "none"
    if explicit == "smtp":
        return "smtp" if has_smtp else "none"
    # auto
    if has_resend:
        return "resend"
    if has_smtp:
        return "smtp"
    return "none"


# ──────────────────────────────────────────────────────────────────────
# Public entrypoint
# ──────────────────────────────────────────────────────────────────────


async def send_verification_code(to_email: str, code: str) -> None:
    """Deliver a verification code via the configured backend.

    Never raises into the auth handler — a transient delivery failure
    must not surface a 500 to the user. The code is logged at INFO
    level on failure so an operator can hand-deliver during an outage.
    """
    subject, text_body, html_body = _render_verification_email(code)
    provider = _resolve_provider()

    if provider == "none":
        logger.warning(
            f"[AUTH] No email backend configured — verification code for {to_email}: {code}"
        )
        return

    try:
        if provider == "resend":
            await _send_via_resend(
                to=to_email, subject=subject,
                text_body=text_body, html_body=html_body,
            )
        else:
            await _send_via_smtp(
                to=to_email, subject=subject,
                text_body=text_body, html_body=html_body,
            )
        logger.info(f"[AUTH] Verification email sent to {to_email} via {provider}")
    except Exception as exc:
        logger.error(
            f"[AUTH] {provider} delivery failed for {to_email}: {exc}",
            exc_info=True,
        )
        # Last-ditch fallback: log the code so the operator can hand-deliver.
        logger.warning(
            f"[AUTH] Manual delivery hint — code for {to_email}: {code}"
        )
