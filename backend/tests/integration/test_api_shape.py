"""
Endpoint shape & validation tests.

Goal: catch breakages in the request/response contract without spinning
up Postgres. If a route is renamed, a status code changes, or required
fields disappear from a response, these tests fail before deploy.

Real data flow (does my registered user get persisted?) is covered by
the production smoke layer that hits the live droplet after deploy.
"""
import pytest


# Every public route the frontend depends on. If one of these flips its
# status code or path, frontend will break — and we want to know first.
_HEALTH_ROUTES = ["/health", "/api/version"]


@pytest.mark.parametrize("path", _HEALTH_ROUTES)
def test_health_routes_return_200(app_with_stubs, path):
    res = app_with_stubs.get(path)
    assert res.status_code == 200, f"{path} returned {res.status_code}"


def test_health_payload_shape(app_with_stubs):
    res = app_with_stubs.get("/health")
    body = res.json()
    assert body["status"] in {"ok", "degraded"}
    assert "checks" in body
    # The checks block must at least surface the agent and DB probes
    # — the GitHub Actions monitor relies on this shape.
    assert "agent" in body["checks"]
    assert "db" in body["checks"]


def test_version_payload_shape(app_with_stubs):
    res = app_with_stubs.get("/api/version")
    body = res.json()
    # Falls back to "dev" when env vars aren't set — that's fine in tests.
    assert "commit" in body
    assert "branch" in body
    assert "version" in body


def test_login_rejects_missing_fields(app_with_stubs):
    """422 (validation), not 500 — the model is doing its job."""
    res = app_with_stubs.post("/api/auth/login", json={})
    assert res.status_code == 422


def test_login_rejects_bad_email_format(app_with_stubs):
    res = app_with_stubs.post(
        "/api/auth/login",
        json={"email": "not-an-email", "password": "Whatever1!"},
    )
    assert res.status_code == 422


def test_register_rejects_disposable_email(app_with_stubs):
    """The disposable-domain block must run BEFORE we touch the database."""
    res = app_with_stubs.post(
        "/api/auth/send-code",
        json={
            "email": "abuser@mailinator.com",
            "password": "StrongPass1!",
            "name": "Test",
            "account_type": "user",
        },
    )
    # Some setups return 400, some 422 — we just want it to be rejected.
    assert res.status_code in (400, 422), (
        f"Disposable email leaked through: {res.status_code} {res.text}"
    )


def test_register_rejects_weak_password(app_with_stubs):
    res = app_with_stubs.post(
        "/api/auth/send-code",
        json={
            "email": "user@gmail.com",
            "password": "weak",
            "name": "Test",
            "account_type": "user",
        },
    )
    assert res.status_code == 422


def test_change_password_requires_auth(app_with_stubs):
    """Without a Bearer token, the endpoint must say 'no'."""
    res = app_with_stubs.post(
        "/api/auth/change-password",
        json={"current_password": "x", "new_password": "Whatever1!"},
    )
    assert res.status_code == 401


def test_admin_endpoints_require_auth(app_with_stubs):
    """Admin endpoints all sit behind a bearer token. A regression where
    one accidentally becomes public is the kind of thing this catches."""
    for path in [
        "/api/admin/stats",
        "/api/admin/users",
        "/api/admin/premium",
    ]:
        res = app_with_stubs.get(path)
        assert res.status_code in (401, 403), (
            f"{path} returned {res.status_code}, expected 401/403"
        )


def test_unknown_route_returns_404(app_with_stubs):
    res = app_with_stubs.get("/api/totally-fake-route-12345")
    assert res.status_code == 404
