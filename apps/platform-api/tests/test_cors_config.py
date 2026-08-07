"""CORS regression tests — product-web signup origins (TECH-51 / NB-46 hotfix).

Root cause fixed: the platform API's default CORS allow-list contained only the
ops-console dev origin (http://localhost:5173). The product-web signup form
(apps/product-web/src/lib/company-signup.ts) POSTs to
/api/v1/auth/company-signup from http://localhost:3000 (Next dev) or
http://localhost:8081 (docker compose) or the live
https://product-web-chi.vercel.app origin. A blank Vercel `CORS_ORIGINS`
override also used to collapse the allow-list to empty. Both paths surfaced as
the signup form's network-failure message.

These tests pin the default allow-list and the live preflight behavior.
"""
from fastapi.testclient import TestClient

from app.core.config import Settings, settings
from app.main import app

ALLOWED_ORIGINS = {
    'http://localhost',
    'http://localhost:5173',  # ops-console dev (must not regress)
    'http://localhost:3000',  # product-web dev (Next.js, default port)
    'http://localhost:5174',  # product-web dev (next dev -p 5174 — the real script port)
    'http://localhost:8081',  # product-web via docker compose
    'http://127.0.0.1:3000',
    'http://127.0.0.1:5174',
    'http://127.0.0.1:8081',
    'https://product-web-chi.vercel.app',
    'https://ops-console-azure.vercel.app',  # ops-console live (TECH-51)
}

DISALLOWED_ORIGIN = 'http://evil.example'


def test_default_cors_origins_include_product_web(monkeypatch):
    """The code default (no env, no .env file) must allow product-web origins."""
    monkeypatch.delenv('CORS_ORIGINS', raising=False)
    fresh = Settings(_env_file=None)
    assert ALLOWED_ORIGINS.issubset(set(fresh.cors_origins))


def test_blank_cors_origins_env_still_uses_safe_defaults(monkeypatch):
    """Vercel can materialize an unset variable as an empty string locally;
    that must not wipe the allow-list."""
    monkeypatch.setenv('CORS_ORIGINS', '')
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


def test_preflight_allows_product_web_vercel_origin():
    with TestClient(app) as client:
        resp = client.options(
            '/api/v1/auth/company-signup',
            headers={
                'Origin': 'https://product-web-chi.vercel.app',
                'Access-Control-Request-Method': 'POST',
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get('access-control-allow-origin') == 'https://product-web-chi.vercel.app'


def test_preflight_allows_product_web_local_dev_origin_5174():
    """Regression: product-web's real dev port is 5174 (package.json
    ``next dev -p 5174``), NOT Next's default 3000. The hotfix allowed
    :3000/:8081 but missed :5174, so local `npm run dev` signup kept
    hitting the network-failure fallback (preflight blocked -> fetch throws)."""
    with TestClient(app) as client:
        resp = client.options(
            '/api/v1/auth/company-signup',
            headers={
                'Origin': 'http://localhost:5174',
                'Access-Control-Request-Method': 'POST',
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get('access-control-allow-origin') == 'http://localhost:5174'


def test_preflight_allows_product_web_local_dev_origin_127_0_0_1_5174():
    with TestClient(app) as client:
        resp = client.options(
            '/api/v1/auth/company-signup',
            headers={
                'Origin': 'http://127.0.0.1:5174',
                'Access-Control-Request-Method': 'POST',
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get('access-control-allow-origin') == 'http://127.0.0.1:5174'


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


def test_default_cors_origins_include_both_live_origins(monkeypatch):
    """Code default (no env, no .env) must allow BOTH live web origins (TECH-51)."""
    monkeypatch.delenv('CORS_ORIGINS', raising=False)
    fresh = Settings(_env_file=None)
    assert 'https://product-web-chi.vercel.app' in set(fresh.cors_origins)
    assert 'https://ops-console-azure.vercel.app' in set(fresh.cors_origins)


def test_preflight_allows_ops_console_vercel_origin():
    """Live ops-console origin must pass preflight with its origin echoed (TECH-51)."""
    with TestClient(app) as client:
        resp = client.options(
            '/api/v1/auth/company-signup',
            headers={
                'Origin': 'https://ops-console-azure.vercel.app',
                'Access-Control-Request-Method': 'POST',
            },
        )
        assert resp.status_code == 200
        assert resp.headers.get('access-control-allow-origin') == 'https://ops-console-azure.vercel.app'


def test_default_allowed_hosts_include_live_platform_host(monkeypatch):
    """Code default (no env, no .env) must trust the live platform host (TECH-52)."""
    monkeypatch.delenv('ALLOWED_HOSTS', raising=False)
    fresh = Settings(_env_file=None)
    assert 'platform-api-smoky.vercel.app' in fresh.allowed_hosts
    assert {'localhost', '127.0.0.1', 'testserver'}.issubset(set(fresh.allowed_hosts))


def test_request_with_live_platform_host_succeeds():
    """Host: platform-api-smoky.vercel.app must pass TrustedHostMiddleware (TECH-52)."""
    with TestClient(app) as client:
        resp = client.get('/health', headers={'Host': 'platform-api-smoky.vercel.app'})
        assert resp.status_code == 200


def test_request_with_unlisted_host_is_rejected():
    """Hosts outside the allow-list must be rejected with 400 (closed allow-list)."""
    with TestClient(app) as client:
        resp = client.get('/health', headers={'Host': 'evil.example'})
        assert resp.status_code == 400
