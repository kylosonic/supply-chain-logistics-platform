# Phase 6 — Origin Trust (TECH-51 / TECH-52)

## Goal

Trust both live web origins (product-web + ops-console) for CORS and the platform's own public host for Host validation, via code defaults, pinned regression tests, explicit production env vars on the Vercel `platform-api` project, and a new production deployment.

## Files to Modify (exact paths)

1. `apps/platform-api/app/core/config.py` — extend `DEFAULT_CORS_ORIGINS` and the `allowed_hosts` default.
2. `apps/platform-api/tests/test_cors_config.py` — strengthen `ALLOWED_ORIGINS`; add 5 tests (2 CORS, 3 host).
3. `apps/platform-api/.env.example` — mirror the new production values in the documented `CORS_ORIGINS` / `ALLOWED_HOSTS` lines (documentation only; no behavior).

No new files are created. No new cross-file imports are required (see Strict Import Map).

## Strict Import Map

- `test_cors_config.py` already imports `TestClient` (fastapi.testclient), `Settings, settings` (app.core.config), and `app` (app.main) — the 5 new tests reuse these exact imports; **no import statement changes**.
- `config.py` — no import changes; both changes are in-place literal edits to existing module-level constants/defaults. `DEFAULT_CORS_ORIGINS` remains referenced by the `cors_origins` field default and the `parse_cors_origins` blank-string fallback (no signature changes). `allowed_hosts` default remains a plain list literal. `main.py` requires **zero changes** — `TrustedHostMiddleware` wiring (lines 43-44) already keys off `settings.allowed_hosts`, which becomes non-empty by default.

## Exact Values (data — apply verbatim)

- `DEFAULT_CORS_ORIGINS` gains one entry, inserted after `'https://product-web-chi.vercel.app',`: `'https://ops-console-azure.vercel.app',` (all 9 existing entries kept; new total = 10).
- `allowed_hosts` default becomes: `['localhost', '127.0.0.1', 'testserver', 'platform-api-smoky.vercel.app']`.
- Production `CORS_ORIGINS` value (mirror `.env.example` list + ops-console live origin):
  `http://localhost,http://localhost:5173,http://localhost:3000,http://localhost:5174,http://localhost:8081,http://127.0.0.1:3000,http://127.0.0.1:5174,http://127.0.0.1:8081,https://product-web-chi.vercel.app,https://ops-console-azure.vercel.app`
- Production `ALLOWED_HOSTS` value (locked behavior doc §3):
  `platform-api-smoky.vercel.app,product-web-chi.vercel.app,ops-console-azure.vercel.app,localhost,127.0.0.1,testserver`
- `.env.example` line 13 (`CORS_ORIGINS=`): append `,https://ops-console-azure.vercel.app` to the existing value; line 14 (`ALLOWED_HOSTS=`): replace with the production `ALLOWED_HOSTS` value above.

## New/Modified Test Names (precise)

In `apps/platform-api/tests/test_cors_config.py`:

1. Modify module-level `ALLOWED_ORIGINS` set: add `'https://ops-console-azure.vercel.app'` (comment: `# ops-console live (TECH-51)`). This automatically strengthens the three existing `issubset` tests (lines 34-51) to pin both live origins.
2. `test_default_cors_origins_include_both_live_origins(monkeypatch)` — monkeypatch-delenv `CORS_ORIGINS`, `Settings(_env_file=None)`, assert both `https://product-web-chi.vercel.app` and `https://ops-console-azure.vercel.app` are in `set(fresh.cors_origins)`.
3. `test_preflight_allows_ops_console_vercel_origin()` — preflight `OPTIONS /api/v1/auth/company-signup` with `Origin: https://ops-console-azure.vercel.app` + `Access-Control-Request-Method: POST`; assert 200 and echoed `access-control-allow-origin` equals the origin (mirror existing test at line 80).
4. `test_default_allowed_hosts_include_live_platform_host(monkeypatch)` — delenv `ALLOWED_HOSTS`, `Settings(_env_file=None)`, assert `'platform-api-smoky.vercel.app' in fresh.allowed_hosts` and `{'localhost','127.0.0.1','testserver'}` all present.
5. `test_request_with_live_platform_host_succeeds()` — `TestClient(app)` GET `/health` with header `Host: platform-api-smoky.vercel.app`; assert `resp.status_code == 200` (not 400). (TestClient/httpx honors an explicit `Host` header; TrustedHostMiddleware exact-matches it.)
6. `test_request_with_unlisted_host_is_rejected()` — `TestClient(app)` GET `/health` with header `Host: evil.example`; assert `resp.status_code == 400` (proves closed allow-list).

Existing tests that carry TECH-51 acceptance (must stay green, no edits): `test_preflight_allows_product_web_vercel_origin` (line 80), `test_preflight_rejects_disallowed_origin` (line 137), `test_preflight_still_allows_ops_console_dev_origin` (line 123 — guards `http://localhost:5173` regression).

## Step-by-Step Execution (TDD order)

1. **Red:** Add the 5 new tests + `ALLOWED_ORIGINS` edit to `test_cors_config.py`. Run from `apps/platform-api`:
   `.venv\Scripts\python.exe -m pytest tests/test_cors_config.py -k "live_origins or ops_console_vercel or allowed_hosts or live_platform_host or unlisted_host"` — expect **5 failures** (no config change yet). Existing 10 tests must still pass.
2. **Green:** Edit `config.py` — insert the ops-console live origin into `DEFAULT_CORS_ORIGINS` and add `'platform-api-smoky.vercel.app'` to the `allowed_hosts` default (exact values above). No other code changes.
3. **Suite:** Record the baseline pass count first (`pytest` before any change, expected green), then run the full suite from `apps/platform-api`:
   `.venv\Scripts\python.exe -m pytest`
   Expected: all existing tests still pass; the 5 new tests now pass (test_cors_config.py goes 10 → 15 tests).
4. **Ops — CORS (TECH-51):** cwd `apps/platform-api`. Discover current state with `vercel env ls production` (if "not linked" error, retry with `vercel env ls production --project platform-api`). Set the var (pwsh pipe; non-interactive):
   `echo "http://localhost,http://localhost:5173,http://localhost:3000,http://localhost:5174,http://localhost:8081,http://127.0.0.1:3000,http://127.0.0.1:5174,http://127.0.0.1:8081,https://product-web-chi.vercel.app,https://ops-console-azure.vercel.app" | vercel env add CORS_ORIGINS production`
5. **Ops — Hosts (TECH-52):** same cwd:
   `echo "platform-api-smoky.vercel.app,product-web-chi.vercel.app,ops-console-azure.vercel.app,localhost,127.0.0.1,testserver" | vercel env add ALLOWED_HOSTS production`
6. **Deploy (both):** `vercel deploy --prod` from `apps/platform-api` — a new production deployment is mandatory for env changes to take effect.

## Verification Checklist (mapped to acceptance criteria)

- **TECH-51-1** (defaults include both live origins): `test_default_cors_origins_include_both_live_origins` + strengthened `issubset` tests green.
- **TECH-51-2** (ops-console preflight echo): `test_preflight_allows_ops_console_vercel_origin` green.
- **TECH-51-3** (product-web preflight echo): `test_preflight_allows_product_web_vercel_origin` green (unchanged).
- **TECH-51-4** (disallowed origin not echoed): `test_preflight_rejects_disallowed_origin` green (unchanged).
- **TECH-51 live:** `curl.exe -i -s -X OPTIONS "https://platform-api-smoky.vercel.app/api/v1/auth/company-signup" -H "Origin: https://product-web-chi.vercel.app" -H "Access-Control-Request-Method: POST"` → HTTP 200 + `access-control-allow-origin: https://product-web-chi.vercel.app`; repeat with `-H "Origin: https://ops-console-azure.vercel.app"` → echoed ops-console origin; negative: `-H "Origin: http://evil.example"` → **no** `access-control-allow-origin` header in response (assert header absence, not status).
- **TECH-52-1/2/3:** the three host tests green (default contains live host; `Host: platform-api-smoky.vercel.app` → 200; `Host: evil.example` → 400).
- **TECH-52 live:** `curl.exe -s -o NUL -w "%{http_code}" "https://platform-api-smoky.vercel.app/health"` → expect `200` (NOT 400); composed check: `curl.exe -i -s -X OPTIONS "https://platform-api-smoky.vercel.app/api/v1/auth/company-signup" -H "Origin: https://ops-console-azure.vercel.app" -H "Access-Control-Request-Method: POST"` → 200 + echoed origin (proves Host + CORS composition).

## Risks

- **`vercel env add` interactivity/existence:** may prompt for confirmation or fail if the var already exists — on failure run `vercel env rm CORS_ORIGINS production --yes` (or `ALLOWED_HOSTS`), then re-add with the same piped command. Do not leave a stale value in place.
- **Env vars require a new deployment:** changing env on Vercel does not affect the running instance; `vercel deploy --prod` is mandatory and is the last ops step.
- **Project linkage:** env commands must run from `apps/platform-api`; if Vercel reports the directory unlinked, fall back to `--project platform-api` flags (or `vercel link --yes` once) before env operations.
- **Local `.env` trap:** `test_runtime_settings_carry_product_web_origins` asserts against the module-level `settings` singleton, which reads a local `.env` if present — if `apps/platform-api/.env` exists with an explicit `CORS_ORIGINS` lacking the ops-console origin, that strengthened test will fail. Fix by updating the local `.env` (dev-only, not committed) to the new 10-origin value.
- **Blank-string collapse:** a materialized-but-empty `ALLOWED_HOSTS` yields `[]` and disables `TrustedHostMiddleware` entirely (dev behavior); the live value above must remain non-empty. `CORS_ORIGINS` blank-safe via defaults (existing behavior, still pinned by tests).
- **pwsh specifics:** use `curl.exe` (never the `curl` alias) with `-i -s -X OPTIONS`; `-o NUL` and `%{http_code}` are curl.exe-native and safe in pwsh.
