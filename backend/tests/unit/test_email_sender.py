"""
Provider-selection logic for transactional email.

We don't actually send anything in tests — the goal is to verify that
the `_resolve_provider()` helper picks the right backend given different
env-var combinations. This guards against a regression where, say, an
empty SMTP_HOST silently re-enables log-only delivery in production.
"""
import importlib

import pytest


@pytest.fixture
def reload_settings(monkeypatch):
    """
    Force a fresh import of the settings + email_sender modules so each
    test sees the env vars it just set instead of values cached from a
    previous test run.
    """
    def _reload(env_overrides: dict[str, str]):
        for k, v in env_overrides.items():
            if v is None:
                monkeypatch.delenv(k, raising=False)
            else:
                monkeypatch.setenv(k, v)

        # Reimport settings so the new env is picked up.
        from src import config as cfg
        importlib.reload(cfg)

        # Then reimport email_sender so it grabs the fresh settings module.
        from src.auth import email_sender as es
        importlib.reload(es)
        return es

    return _reload


def test_auto_picks_resend_when_key_set(reload_settings):
    es = reload_settings({
        "EMAIL_PROVIDER": "auto",
        "RESEND_API_KEY": "re_test_key",
        "SMTP_HOST": "smtp.example.com",
        "SMTP_USERNAME": "user",
        "SMTP_PASSWORD": "pass",
    })
    assert es._resolve_provider() == "resend"


def test_auto_falls_back_to_smtp_without_resend(reload_settings):
    es = reload_settings({
        "EMAIL_PROVIDER": "auto",
        "RESEND_API_KEY": "",
        "SMTP_HOST": "smtp.example.com",
        "SMTP_USERNAME": "user",
        "SMTP_PASSWORD": "pass",
    })
    assert es._resolve_provider() == "smtp"


def test_auto_falls_back_to_log_only_when_nothing_configured(reload_settings):
    es = reload_settings({
        "EMAIL_PROVIDER": "auto",
        "RESEND_API_KEY": "",
        "SMTP_HOST": "",
    })
    assert es._resolve_provider() == "none"


def test_explicit_resend_requires_key(reload_settings):
    """If the operator explicitly asks for resend but forgets the key,
    we must NOT silently fall back to SMTP — that's the kind of accident
    the explicit setting is meant to prevent."""
    es = reload_settings({
        "EMAIL_PROVIDER": "resend",
        "RESEND_API_KEY": "",
        "SMTP_HOST": "smtp.example.com",
        "SMTP_USERNAME": "user",
        "SMTP_PASSWORD": "pass",
    })
    assert es._resolve_provider() == "none"


def test_explicit_smtp_ignores_resend_key(reload_settings):
    es = reload_settings({
        "EMAIL_PROVIDER": "smtp",
        "RESEND_API_KEY": "re_test_key",
        "SMTP_HOST": "smtp.example.com",
        "SMTP_USERNAME": "user",
        "SMTP_PASSWORD": "pass",
    })
    assert es._resolve_provider() == "smtp"
