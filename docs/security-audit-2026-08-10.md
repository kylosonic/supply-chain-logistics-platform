# Security Audit — Supply Chain Logistics Platform

**Date:** 2026-08-10
**Auditor:** @vision (product/security review) + web research (verified 2026-08-10)
**Scope:** Entire monorepo — `apps/platform-api` (FastAPI), `apps/ops-console` (Vite/React), `apps/product-web` (Next.js 14), `apps/desktop` (Electron), `supabase/`, `docker-compose.yml`, git history (91 commits).
**Method:** Manual code review (secrets scan, auth/authorization tracing, injection & SSRF hunting, data-flow analysis), live `npm audit`, git-history secret scan, and verification of every dependency advisory against the GitHub Advisory Database + official docs.

---

## 1. Executive Summary

This codebase is **significantly above average** for a startup platform. The core auth (PBKDF2-600k, constant-time compare, HttpOnly/SameSite=strict cookies), the org-scoped surfaces (receipts, billing, providers), the RLS migration, and the Electron hardening are all done properly. No injection vulnerabilities, no SSRF, no leaked secrets in git history, `.env` files correctly ignored.

However, the audit found **1 critical, 6 high, 7 medium, and 8 low findings**. The two dominant themes:

1. **Authorization model split (HIGH):** Roughly half the endpoints enforce tenant isolation via organization membership; the other half (shipments, warehouses, items, alerts, routes, planning, invoices, forecast, ops, live websocket, telemetry ingestion) only require a *global* role and return **all tenants' data**. Any authenticated user with the lowest global role (VIEWER) can read every customer's shipments, alerts, and audit trail.
2. **Dependency staleness (HIGH):** `next@14.2.35` is the terminal release of a two-majors-old line that stopped receiving security patches in Dec 2025; `axios@1.16.1` is vulnerable to the 2026 prototype-pollution/Basic-auth-injection family (fixed in 1.18.0); `electron@31` is EOL (supported lines are ~41–43).

Plus a **critical operational trap**: the committed `.env.example` and `docker-compose.yml` ship placeholder secrets that are *long enough to pass the production length guards* — a deployment that copies them is running with a publicly known JWT signing key.

---

## 2. What Is Already Strong (do not regress these)

| Area | Evidence |
|---|---|
| Secret hygiene | Real `.env` files untracked; 91-commit history scanned — **zero secrets ever committed** |
| Password storage | PBKDF2-SHA256 @ 600k iterations, per-user random salt, `hmac.compare_digest` |
| Token handling | JWT with `iat`/`exp`; cookie set `HttpOnly` + `SameSite=strict` + `Secure` in prod |
| Rate limiting | Login 10/min, register 5/min, signup 3/min, global 200/min (slowapi) |
| Host/CORS | `TrustedHostMiddleware` wired; CORS explicit allowlist, credentials disciplined |
| Response headers | HSTS, `nosniff`, `X-Frame-Options: DENY`, Referrer-Policy, Permissions-Policy (middleware) |
| Provider keys at rest | Fernet-encrypted, org-scoped access, IDOR guards on read/revoke/test |
| Org-scoped surfaces | orders, receipts, wallet, billing, subscriptions, reversals, notifications, providers — all membership-gated |
| RLS migration | `company_profiles`: RLS enabled, all policies `auth.uid() = id` — textbook |
| Upload handling | Receipts: 5 MB cap, extension+content-type allowlist, magic-byte sniffing for extraction |
| Production guards | Mock extraction cannot leak to prod (`effective_receipt_extraction_mode`); JWT/encryption secrets min-length enforced |
| SSRF posture | All outbound HTTP (SMS, OpenAI-compatible) uses settings-driven URLs only, with timeouts |
| Electron | `sandbox: true`, `contextIsolation: true`, `nodeIntegration: false`, window-open denied |
| Frontend token storage | `sessionStorage` (not localStorage), org header, session-expiry interceptor |
| Audit | Sensitive operations write audit events; phones masked in audit payloads |

---

## 3. Findings

### 🔴 CRITICAL

#### C-1. Deployable placeholder secrets defeat the production guards
**Where:** `docker-compose.yml:31-34`, `apps/platform-api/.env.example:2-5` (both committed)
- `JWT_SECRET_KEY:-change-me-in-production` (22 chars) — would be caught by the ≥32-char guard, **but**
- the committed `.env.example` value `change-me-in-production-minimum-32-bytes` is **36 chars — long enough to pass every guard**, and
- `PROVIDER_KEY_ENCRYPTION_SECRET` placeholder is 42 chars — also passes.
- `POSTGRES_PASSWORD` defaults to `postgres`, and port **5432 is published to the host** (`docker-compose.yml:10-11`).

**Exploit:** Anyone who reads this repo (it's public-facing in your workflow) knows the signing key of any environment deployed from these defaults → forge a JWT with `role: ADMIN` → full platform takeover, decrypt all provider keys, read all tenants.

**Fix (immediate):**
1. Delete the placeholder values from `.env.example` (ship empty values + instructions), or better: make the deployment pipeline **fail at deploy time** if the secret equals any known placeholder.
2. Add a startup check in `config.py` that rejects a known-placeholder list, not just a length check.
3. Remove `ports: 5432` publication from docker-compose unless the DB is genuinely reachable by external consumers.
4. **Rotate** the JWT/encryption secrets of any environment that may have been deployed from defaults (Vercel envs, any VPS). Rotation = change value, redeploy; all sessions will invalidate — acceptable for a fix.

---

### 🟠 HIGH

#### H-1. Cross-tenant authorization gap on global-role-only endpoints
**Where:** `apps/platform-api/app/api/endpoints/{shipments,warehouses,items,alerts,routes,planning,invoices,forecast,ops,live,ingestion}.py`

These endpoints guard with `require_roles(VIEWER/OPERATOR/ADMIN)` (a **global** user role) and then query **without any organization filter**:
- `GET /api/v1/shipments` — every tenant's shipments (`shipments.py:50-56`)
- `GET /api/v1/ops/audit-timeline` — every tenant's audit events incl. emails and phone-masked data (`ops.py:43-50`)
- `GET /api/v1/ops/exception-feed`, `GET /api/v1/ops/dock-appointments` — cross-tenant
- `POST /api/v1/ops/live-eta`, `POST /api/v1/ingestion/telematics`, `POST /api/v1/ingestion/iot-telemetry` — **cross-tenant writes** (overwrite any fleet asset's GPS; inject high-severity alerts for any SKU)
- `/api/v1/live/updates` (WebSocket) — any authenticated user receives the **global** inventory/route/forecast snapshot

The platform already has the correct machinery (`get_current_membership`, `X-Organization-Id`, `require_org_roles`) — these endpoints simply predate it.

**Fix:** Convert every listed endpoint to membership-scoped queries (`OrganizationMembership` + `organization_id` filters on models). Decide explicitly: if the ops console is a single-tenant internal tool, it must be moved behind a distinct `SYSADMIN` role that no customer signup can reach — customers currently self-register as global ADMIN (see M-1).

#### H-2. Next.js 14.2.35 — terminal 14.x release, unpatched since Dec 2025
**Where:** `apps/product-web/package.json:19`
**Verified:** 14.2.35 was the final 14.x release (Dec 2025). All 2026 advisories — SSRF in Server Actions on custom servers (GHSA-89xv-2m56-2m9x), SSRF via dynamic rewrite hostnames (GHSA-p9j2-gv94-2wf4), stored XSS via CSP nonces (GHSA-ffhc-5mcf-pf4q), RSC cache-poisoning / cross-user cache confusion (GHSA-68g3-v927-f742), Server Action DoS (GHSA-m99w-x7hq-7vfj) — are fixed **only** in 15.5.21 / 16.2.11.
**Impact:** product-web is deployed on Vercel *and* self-hosted Docker — the self-hosted deployment is where the custom-server SSRF/cache-confusion class bites.
**Fix:** Upgrade to **16.2.11** (or conservative: 15.5.21) via `npx @next/codemod@canary upgrade latest`. Interim: if Server Actions are used, set `__NEXT_PRIVATE_ORIGIN` and pin Host at the edge.

#### H-3. axios 1.16.1 — 2026 prototype-pollution / auth-injection family
**Where:** `apps/ops-console/package.json:16` (resolved 1.16.1)
**Verified:** GHSA-xj6q-8x83-jv6g (polluted `Object.prototype` username/password → injected `Authorization: Basic`), GHSA-gcfj-64vw-6mp9 (interceptor config clone can route requests through an attacker proxy, CVSS 8.3), GHSA-hcpx-6fm6-wx23 / GHSA-7q8q-rj6j-mhjq (form-serializer DoS). **First patched: 1.18.0.**
**Fix:** `npm install axios@^1.18.0` in ops-console (package-lock bump only). Also fixes the NO_PROXY-bypass and maxBodyLength-bypass advisories.

#### H-4. Electron 31 — EOL, ~12 majors behind
**Where:** `apps/desktop/package.json:15`
**Verified:** Electron supports only the latest 3 stable majors (currently ~41–43, with v43 current). Electron 31 ships ~2 years of unpatched Chromium/Node vulnerabilities — and this app deliberately loads **remote URLs** (the riskiest documented pattern).
**Fix:** Upgrade to a supported major (`electron@^43`), then run the official checklist: navigation guard via `will-navigate` with exact-origin allowlist, `setPermissionRequestHandler` on the remote sessions (default auto-approves!), DevTools gated behind `!app.isPackaged`, and `@electron/fuses` to flip `runAsNode`/`nodeCliInspect`.

#### H-5. Unauthenticated feedback endpoint
**Where:** `apps/platform-api/app/api/endpoints/feedback.py:10-23`
`POST /api/v1/feedback` has **no authentication dependency**. Anyone can POST unlimited 2 KB messages → storage abuse, admin-queue pollution, and an email field used to harvest/fake identities. It is the only fully public write endpoint.
**Fix:** Require `get_current_user` (authenticated feedback) — or if public feedback is a product requirement, add a per-IP rate limit (e.g. 3/hour) and a honeypot/CAPTCHA.

#### H-6. Supabase auth configuration is a landmine
**Where:** `supabase/config.toml:182-229`
If the linked Supabase project (`huukqxpbwqcepnkrfhdw`) is ever wired to the product signup flow, it ships with: **email confirmations disabled** (`enable_confirmations = false` — anyone can register an account with a victim's email), **minimum password length 6**, no complexity requirements, `secure_password_change = false` (password change without re-auth), no CAPTCHA. The only migration (RLS) is correct, but the auth layer is not production-hardened.
**Fix:** `enable_confirmations = true`, `minimum_password_length = 8` + `lower_upper_letters_digits`, `secure_password_change = true`, enable Turnstile/hCaptcha, enable TOTP MFA for the console roles, and review the remote project's dashboard settings (rate limits, SMTP sender, session timebox) before go-live.

---

### 🟡 MEDIUM

#### M-1. Bootstrap admin backdoor — first user to register becomes global ADMIN
`auth.py:116-130` (`/register`): if the user table is empty, the first registration gets `role=ADMIN` with access to `/users`, `/ops/metrics`, and every global surface. Fine as a bootstrap convention — **catastrophic if the production DB is ever reset or a migration fails** and the first visitor becomes the platform admin.
**Fix:** Gate bootstrap behind a one-time env flag (`BOOTSTRAP_ADMIN_ALLOWED=1`) that must be explicitly removed after first boot, or require an admin-invite flow instead of open registration.

#### M-2. User enumeration via 409 responses
`auth.py:126-128,160-161` — "Username already exists" / "A user with this email already exists" disclose account existence. Combine with M-1/H-1 for targeted attacks.
**Fix:** Return a generic 409 message ("That username/email cannot be used"), and keep the timing uniform.

#### M-3. No CSP on the ops console (nginx + Vercel)
`apps/ops-console/nginx.conf` and `vercel.json` set good headers but **no Content-Security-Policy**. The console holds auth tokens in sessionStorage; CSP is the primary blast-radius control if any XSS slips through. The API sets no CSP either (fine for a JSON API, but the SPA needs one).
**Fix (nginx):** add header `Content-Security-Policy "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https://*.tile.openstreetmap.org; connect-src 'self'; font-src 'self' data:; object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"` (`style-src 'unsafe-inline'` is required by Leaflet; keep `script-src` strict). Mirror on Vercel via `vercel.json` `headers`.

#### M-4. CSV ingestion has no size cap
`ingestion.py:35-42` — `file.file.read()` with no limit (receipts get a 5 MB cap; CSVs get nothing). An authenticated operator can OOM the API process. Also: CSV cells starting with `=`, `+`, `-`, `@` can carry formula injection if data is ever exported to Excel.
**Fix:** Cap CSV uploads (e.g., 10 MB) before reading; if any Excel/CSV export exists, sanitize formula-leading cells on ingestion or export.

#### M-5. Python dependencies unpinned — no lockfile
`apps/platform-api/pyproject.toml:10-26` — all `>=` ranges, no lockfile. The local venv is healthy (starlette 1.3.1 — patched for the entire 2026 CVE wave incl. CVE-2026-48710 "BADHOST" and CVE-2026-54283 form-DoS), but a fresh install can resolve starlette 0.4x and silently re-open those vulnerabilities.
**Fix:** Adopt `uv` + commit `uv.lock` (or `pip-tools --generate-hashes`); declare `starlette>=1.3.1` explicitly; install in Docker with `uv sync --frozen`. Add `uv audit` / `pip-audit` to CI.

#### M-6. Docker deployment exposes Postgres with default credentials
`docker-compose.yml:10-11` — port 5432 published to the host with `postgres/postgres` fallback. On any internet-reachable VPS this is an open database (or at least a brute-force target) feeding the entire backend.
**Fix:** Bind to `127.0.0.1:5432:5432`, require `POSTGRES_PASSWORD` to be set (no default), and prefer a managed DB or internal Docker network only.

---

### 🔵 LOW / INFO

| # | Finding | Fix |
|---|---|---|
| L-1 | JWT logout is client-side only; tokens survive logout for 2 h | Add a token denylist/version claim for high-privilege roles; document the tradeoff |
| L-2 | `testserver` in default `ALLOWED_HOSTS` (`config.py:36`) | Remove; it's a Django test relic |
| L-3 | `/health` discloses `env` (`main.py:84`) | Drop the field on public deployments |
| L-4 | Receipt file replay serves client-supplied `content_type` (`receipts.py:236`) | Add `Content-Disposition: attachment` (nosniff already set) |
| L-5 | Dead env var `PASSWORD_SALT` in `apps/platform-api/.env` | Delete (Settings uses `extra='ignore'`) |
| L-6 | npm workspace install is broken (next extraneous/invalid at root) | `npm ci` from a clean state; fix hoisting |
| L-7 | `nanoid@3.3.12/3.3.16` (build-time via postcss) | Bump postcss; LOW because build-time only |
| L-8 | Electron IPC handlers don't validate `sender`/`senderFrame` | Add validation per the official checklist |
| L-9 | HSTS lacks `preload` | Leave it off — hstspreload.org now recommends against preload; keep `includeSubDomains` |

---

## 4. Priority Roadmap

### Do this week (stop-the-bleed)
1. **C-1:** Delete placeholder secrets from `.env.example`; add known-placeholder rejection to `config.py`; rotate JWT + provider-encryption secrets if any env may have used defaults.
2. **H-3:** Bump `axios` → `^1.18.0` (one-line lockfile change).
3. **H-2:** Kick off the Next.js upgrade to 15.5.21/16.2.11; until then set `__NEXT_PRIVATE_ORIGIN` + Host pinning on the self-hosted deployment.
4. **H-5:** Require auth on `/feedback` (or rate-limit it hard).

### Next sprint
5. **H-1:** Migrate all global-role endpoints to membership-scoped queries (or to a distinct SYSADMIN role). This is the highest-leverage code change; the tests in `test_tenant_isolation_endpoints.py` are a good harness to extend.
6. **H-4:** Electron → v43 + navigation guard + permission handler.
7. **H-6:** Harden Supabase auth settings before any product-web auth wiring.
8. **M-3:** Ship the CSP (nginx + Vercel).
9. **M-5:** uv lockfile + CI audit.

### Next month
10. **M-1/M-2:** Bootstrap flag + generic conflict messages.
11. **M-4/M-6:** CSV size cap; docker-compose hardening.
12. **L-1..L-9** tidy-up batch (30 min of work total).
13. Add `security.md` tooling: `npm audit` + `pip-audit` + `osv-scanner` in CI so this audit doesn't rot.

---

## 5. Research Sources (verified 2026-08-10)

- GitHub Advisory Database: GHSA-xj6q-8x83-jv6g (axios), GHSA-gcfj-64vw-6mp9, GHSA-hcpx-6fm6-wx23; Next.js 14.2.35 release notes; GHSA-89xv-2m56-2m9x, GHSA-p9j2-gv94-2wf4, GHSA-ffhc-5mcf-pf4q, GHSA-68g3-v927-f742, GHSA-m99w-x7hq-7vfj; Starlette GHSA-86qp-5c8j-p5mr (BADHOST), GHSA-82w8-qh3p-5jfq
- FastAPI security docs (OAuth2 JWT tutorial, Argon2id migration), Starlette middleware docs
- Supabase: going-into-prod checklist, auth email/sessions/MFA docs, RLS docs
- Electron: security checklist + timelines (supported majors ~41–43)
- MDN CSP + frame-ancestors; hstspreload.org (preload not recommended)
- PEP 751 (pylock.toml), uv docs (lockfile, audit, malware check)

*Nothing in this report has been changed in the codebase. All fixes are recommendations pending your review.*
