"""CORS regression tests — product-web signup origins (TECH-51 / NB-46 hotfix).

Root cause fixed: the platform API's default CORS allow-list contained only the
ops-console dev origin (http://localhost:5173). The product-web signup form
(apps/product-web/src/lib/company-signup.ts) POSTs to
/api/v1/auth/company-signup from http://localhost:3000 (Next dev) or
http://localhost:8081 (docker compose) — both were CORS-blocked by the browser,
which surfaced as the signup form's network-failure message.

These tests pin the default allow-list and the live preflight behavior.
"""
from fastapi.testclient import TestClient

from app.core.config import Settings, settings
from app.main import app

ALLOWED_ORIGINS = {
    'http://localhost',
    'http://localhost:5173',  # ops-console dev (must not regress)
    'http://localhost:3000',  # product-web dev (Next.js)
    'http://localhost:8081',  # product-web via docker compose
    'http://127.0.0.1:3000',
    'http://127.0.0.1:8081',
}

DISALLOWED_ORIGIN = 'http://evil.example'


def test_default_cors_origins_include_product_web(monkeypatch):
    """The code default (no env, no .env file) must allow product-web origins."""
    monkeypatch.delenv('CORS_ORIGINS', raising=False)
    fresh = Settings(_env_file=None)
    assert ALLOWED_ORIGINS.issubset(set(fresh.cors_origins))


def test_runtime_settings_carry_product_web_origins():
    """The live settings singleton used by the app must include the origins."""
    assert ALLOWED_ORIGINS.issubset(set(settings.cors_origins))


def test_preflight_allows_product_web_dev_origin():
    with TestClient(app) as client:
        resp = client.options(
            '/api/v1/auth/company-signup',
            headers={
                'Origin': 'http://localhost:3000',
                'Access-Control-Request-Method': 'POST',
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get('access-control-allow-origin') == 'http://localhost:3000'


def test_preflight_allows_product_web_compose_origin():
    with TestClient(app) as client:
        resp = client.options(
            '/api/v1/auth/company-signup',
            headers={
                'Origin': 'http://localhost:8081',
                'Access-Control-Request-Method': 'POST',
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get('access-control-allow-origin') == 'http://localhost:8081'


def test_preflight_still_allows_ops_console_dev_origin():
    """Console regression: http://localhost:5173 must remain allowed."""
    with TestClient(app) as client:
        resp = client.options(
            '/api/v1/auth/company-signup',
            headers={
                'Origin': 'http://localhost:5173',
                'Access-Control-Request-Method': 'POST',
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get('access-control-allow-origin') == 'http://localhost:5173'


def test_preflight_rejects_disallowed_origin():
    """Unlisted origins must NOT be echoed (no wildcard behavior)."""
    with TestClient(app) as client:
        resp = client.options(
            '/api/v1/auth/company-signup',
            headers={
                'Origin': DISALLOWED_ORIGIN,
                'Access-Control-Request-Method': 'POST',
            },
        )
        assert 'access-control-allow-origin' not in resp.headers
