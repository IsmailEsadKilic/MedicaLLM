"""
Email canonicalisation + disposable-domain rejection.

These functions guard the registration endpoint against duplicate-account
abuse and throwaway providers, so they get a focused unit suite. The tests
use only stdlib + the function under test — no DB, no network, no agent.
"""
from src.auth.email_utils import (
    canonicalize_email,
    email_domain,
    is_disposable_domain,
    normalize_email,
)


class TestNormalizeEmail:
    def test_basic_lowercase(self):
        assert normalize_email("Foo@BAR.com") == "foo@bar.com"

    def test_strips_whitespace(self):
        assert normalize_email("  user@example.com\n") == "user@example.com"

    def test_unicode_full_width_at_sign(self):
        # Some attackers use ＠ (full-width @) to evade naive matching;
        # NFKC normalises it to ASCII '@'.
        assert normalize_email("user\uff20gmail.com") == "user@gmail.com"

    def test_empty_string(self):
        assert normalize_email("") == ""


class TestCanonicalizeEmail:
    def test_gmail_dot_trick(self):
        # Gmail ignores dots in the local part — every variant goes to
        # the same inbox.
        assert canonicalize_email("john.doe@gmail.com") == "johndoe@gmail.com"
        assert canonicalize_email("j.o.h.n.d.o.e@gmail.com") == "johndoe@gmail.com"

    def test_gmail_plus_alias(self):
        assert canonicalize_email("johndoe+anything@gmail.com") == "johndoe@gmail.com"

    def test_gmail_combined_dot_and_plus(self):
        assert canonicalize_email("John.Doe+spam@Gmail.com") == "johndoe@gmail.com"

    def test_googlemail_collapses_to_gmail(self):
        # googlemail.com is the same Google inbox space as gmail.com.
        assert canonicalize_email("user@googlemail.com") == "user@gmail.com"

    def test_outlook_plus_alias(self):
        assert canonicalize_email("jane+work@outlook.com") == "jane@outlook.com"

    def test_outlook_does_not_strip_dots(self):
        # Outlook treats dots as significant; we must NOT normalise them.
        assert canonicalize_email("jane.doe@outlook.com") == "jane.doe@outlook.com"

    def test_unknown_domain_is_left_alone(self):
        # Custom / corporate domains keep their literal local part.
        assert canonicalize_email("ali@medicallm.com.tr") == "ali@medicallm.com.tr"

    def test_domain_without_at_sign(self):
        # Garbage in, garbage out — we don't crash.
        assert canonicalize_email("not-an-email") == "not-an-email"

    def test_empty_string(self):
        assert canonicalize_email("") == ""


class TestEmailDomain:
    def test_basic(self):
        assert email_domain("user@gmail.com") == "gmail.com"

    def test_uppercase(self):
        assert email_domain("USER@GMAIL.COM") == "gmail.com"

    def test_no_at_sign(self):
        assert email_domain("invalid") == ""


class TestDisposableDomain:
    def test_known_disposable_rejected(self):
        # 'mailinator.com' is one of the highest-traffic disposable
        # providers and must be in the shipped list. Any failure here
        # likely means the disposable_domains.txt file moved.
        assert is_disposable_domain("anyone@mailinator.com") is True

    def test_real_provider_allowed(self):
        assert is_disposable_domain("real@gmail.com") is False
        assert is_disposable_domain("user@medicallm.com.tr") is False

    def test_case_insensitive(self):
        assert is_disposable_domain("USER@MAILINATOR.COM") is True

    def test_invalid_input_safe(self):
        # Garbage shouldn't crash the registration handler.
        assert is_disposable_domain("") is False
        assert is_disposable_domain("not-an-email") is False
