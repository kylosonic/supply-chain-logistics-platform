# BLUEPRINT: PHASE 1 — SECURITY HARDENING "STOP-THE-BLEED" (NB-63 / NB-65 / NB-66)

## Status

| Field | Value |
|---|---|
| Document | Phase 1 — Security Hardening stop-the-bleed (SEC-01, SEC-03, SEC-04) |
| Branch | `feat/security-hardening-v1` @ `17ab7c8` (verified: `.git/refs/heads/feat/security-hardening-v1`; `master` untouched at `4f57019` per `docs/swarm/STATE.md:25`) |
| Date | 2026-08-10 |
| Status | 🔒 PLANNED — @build executes exactly this; @qa audits against §QA-Audit-Against |
| Migrations | **NONE** (confirmed — no schema change; `feedback` table untouched) |
| Dispatch | `docs/swarm/STATE.md:12` — Phase 1 scope = NB-63, NB-65, NB-66 (audit C-1, H-5, H-3/H-2, "Do this week" items per `docs/security-audit-2026-08-10.md:156-160`) |

## 1. Objective

Close the three "stop-the-bleed" findings so that (a) no environment can boot with a publicly known signing key, (b) the only public write endpoint stops accepting anonymous writes, and (c) no deployed surface depends on a known-vulnerable dependency version — with regression guards so none of the fixes silently regress.

**Scope:** NB-63 (audit C-1), NB-65 (audit H-5), NB-66 (audit H-2/H-3/H-4 — with the Electron checklist split per §Adjudications).

**Non-scope (later phases of this batch):** NB-64 (tenant isolation, H-1), NB-67 (Supabase, H-6), NB-68 (bootstrap admin, M-1), NB-69 (account enumeration, M-2), NB-70 (CSP/CSV cap/dep-locking/Docker posture, M-3..M-6), NB-71 (low-severity tidy, L-1..L-9). Note NB-71.2 (`testserver` removal) stays deferred even though `docker-compose.yml:36` and `config.py:36` still list it — do not fold it into this phase (scope discipline; it is already ticketed).

## 2. Adjudications (locked decisions)

1. **NB-63 placeholder rejection is exact-match, non-dev only.** Only exact committed placeholder strings and length violations are rejected (`production-security-hardening.md:30` edge case). A one-character-different secret is a real secret decision.
2. **NB-63 startup abort requires a lifespan hook.** The guards are currently lazy — `settings.effective_jwt_secret_key` is only touched on first token encode/decode (`app/services/security.py:66,71`) and the Fernet seed (`security.py:79`). Without a startup touch, a placeholder environment boots and fails only on first auth. Add a FastAPI lifespan that touches every effective property; in dev/test envs all guards skip, so the test suite is unaffected.
3. **NB-65 chooses authenticated feedback (preferred option, `production-security-hardening.md:49`).** The public rate-limited alternative (3/hour per IP + honeypot) is **rejected**: the feedback form renders only inside the authenticated console (`apps/ops-console/src/pages/DashboardPage.tsx:389` via `FeedbackForm`), the console's axios client already attaches the Bearer token (`apps/ops-console/src/services/api.ts:91-101`), so auth costs zero product friction while killing anonymous abuse. The console API client already propagates 401 via the NB-59 soft-signout (`api.ts:103-112`).
4. **NB-66 Next.js target = 15.5.21 (conservative), not 16.2.11.** Next 16 requires React 19; product-web pins `react`/`react-dom` `^18.3.1` (`apps/product-web/package.json:20-21`). 15.5.x supports React 18 and is the patched line named by the audit (`security-audit-2026-08-10.md:84`). 16.2.11 stays recorded as an option if a later slice retires React 18.
5. **NB-66 Electron: version bump to `^43.0.2` in Phase 1; the official checklist is split to a later phase.** Rationale: (a) `apps/desktop/package.json` has no packager (no electron-builder/forge) — `@electron/fuses` and packaged-mode DevTools gating are packaging-time semantics, meaningless for the current `electron .` runtime (`package.json:9-11`); (b) `src/main.cjs` has no test harness — the checklist changes (navigation guard, permission handler) alter remote-URL loading behavior and need a dedicated QA slice with manual verification; (c) the audit's own roadmap sequenced the Electron checklist to "Next sprint" (`security-audit-2026-08-10.md:164`). NB-66.3 stays **OPEN** until that slice lands; this is recorded honestly in the acceptance mapping (§5) so the ticket is not falsely closed.
6. **The `change-me-in-production` compose fallback (23 chars) is added to the placeholder list even though the ≥32 length guard already catches it** — belt-and-braces, exact-match, and it keeps the failure message consistent ("known placeholder" instead of "too short").

## 3. File Inventory (change type / risk)

| # | File | Action | Risk | Notes |
|---|---|---|---|---|
| 1 | `apps/platform-api/app/core/config.py` | EDIT | **HIGH — startup guard change affects every environment** | Add `KNOWN_PLACEHOLDER_SECRETS`, placeholder checks in `effective_jwt_secret_key`/`effective_provider_key_encryption_secret`; existing length guards (config.py:74-82, 136-150) preserved; dev/test paths untouched |
| 2 | `apps/platform-api/app/main.py` | EDIT | **HIGH — new lifespan runs on every boot incl. TestClient** | Lifespan touches all effective properties; test env skips guards |
| 3 | `apps/platform-api/.env.example` | EDIT | LOW — docs/example only | Lines 2/5 → empty + instructions |
| 4 | `.env.example` (root) | EDIT | LOW — docs/example only | Lines 11/14 → empty + instructions |
| 5 | `docker-compose.yml` | EDIT | **HIGH — breaks `docker compose up` without env vars (intended fail-fast)** | Lines 9/31/34 required-var `:?`; line 11 loopback bind |
| 6 | `apps/platform-api/app/api/endpoints/feedback.py` | EDIT | MEDIUM — auth addition; console unaffected | Add `get_current_user`; stamp `user_email` |
| 7 | `apps/ops-console/package.json` | EDIT | LOW | Line 16 axios `^1.7.2` → `^1.18.0` |
| 8 | `apps/ops-console/package-lock.json` | EDIT (lockfile) | LOW | resolved 1.16.1 (lockfile:2030) → 1.18.x |
| 9 | `apps/product-web/package.json` | EDIT | **HIGH — major-adjacent runtime upgrade** | Line 19 next `^14.2.35` → `15.5.21`; lockfile too |
| 10 | `apps/product-web/package-lock.json` | EDIT (lockfile) | MEDIUM | resolved 14.2.35 (lockfile:2254) → 15.5.21 |
| 11 | `apps/desktop/package.json` | EDIT | LOW | Line 15 electron `^31.0.2` → `^43.0.2`; lockfile too |
| 12 | `apps/desktop/package-lock.json` | EDIT (lockfile) | LOW | resolved 31.0.2 (lockfile:289) → 43.x |
| 13 | `apps/platform-api/tests/test_config_guards.py` | EDIT (tests) | LOW | +6 guard tests (placeholders, preservation, dev edge) |
| 14 | `apps/platform-api/tests/test_secret_placeholder_hygiene.py` | NEW (tests) | LOW | Static scan of `.env.example` ×2 + compose (pins NB-63.3/63.4) |
| 15 | `apps/platform-api/tests/test_feedback_auth.py` | NEW (tests) | LOW | +5 tests (pins NB-65) |
| 16 | `apps/ops-console/src/services/api.test.ts` | TEST-ONLY (verify) | LOW | Must stay green — pins axios interceptor behavior |

**No overlapping files between tickets:** config.py/main.py/.env.example×2/compose (NB-63) ∥ feedback.py + test_feedback_auth.py (NB-65) ∥ three package.json/lockfile pairs (NB-66) are pairwise disjoint — verified by the inventory above. Parallel execution is legal per `AGENTS.md` §7 after NB-63's config change lands (feedback tests run against `app.main`, which NB-63 modifies — see §4 ordering).

**Unchanged (verified compatible):** `app/api/security.py` (get_current_user stays as-is — `security.py:48-57`); `app/schemas/feedback.py`; `app/models/feedback.py` (no `user_id` column added — out of scope, noted in §Non-Goals); `app/services/security.py`; `tests/conftest.py` (token fixtures `conftest.py:119-137`, `_auth` helper `conftest.py:185-186` reused); `apps/ops-console/src/services/api.ts`, `logisticsApi.ts:264-265`, `components/FeedbackForm.tsx` (zero console production edits); `apps/product-web/src/**`, `scripts/check-bundle-budget.mjs`, `next.config.mjs`, `Dockerfile`; `apps/desktop/src/main.cjs`.

**Commit hygiene (STATE.md:102):** do NOT sweep `.opencode/agents/*`, `AGENTS.md`, `.gitignore`, `apps/platform-api/tests_full_run.log` (incomplete 3-line capture — not evidence of a green run) into batch commits.

## 4. Ticket-by-Ticket Blueprint

### 4.1 NB-63 — No environment can boot with a known placeholder secret (P0)

**Ground truth:** `apps/platform-api/.env.example:2` ships `JWT_SECRET_KEY=change-me-in-production-minimum-32-bytes` (**40 chars — passes the ≥32 guard** at `config.py:77`); `:5` ships `PROVIDER_KEY_ENCRYPTION_SECRET=change-me-provider-key-secret-min-32-chars!` (**43 chars — passes `config.py:145`**). Root `.env.example:11,14` carries the same values. `docker-compose.yml:31` falls back to `change-me-in-production` (23 chars), `:34` to the 43-char provider placeholder, `:9` defaults `POSTGRES_PASSWORD=postgres`, `:10-11` publishes `5432` to all host interfaces. Guards at `config.py:74-82` and `:136-150` are length-only; there is no placeholder rejection and no startup touch (verified: no lifespan in `main.py:30-73`).

**Implementation intent (@build):**

1. `config.py` — module-level `KNOWN_PLACEHOLDER_SECRETS: frozenset[str]` containing exactly (measured lengths):
   - `'change-me-in-production'` (23)
   - `'change-me-in-production-minimum-32-bytes'` (40)
   - `'change-me-provider-key-secret-min-32-chars!'` (43)
   - `'dev-secret-do-not-use-in-production-minimum-32'` (46 — the dev fallback at `config.py:81`, so a copy-paste of the dev default into prod is also rejected)
   
   In `effective_jwt_secret_key` (config.py:74-82): after the length check, when `app_env not in ('development','test')` and the raw value is in the set → `raise ValueError('JWT_SECRET_KEY must not be a known placeholder value')`. Mirror in `effective_provider_key_encryption_secret` (config.py:136-150) naming `PROVIDER_KEY_ENCRYPTION_SECRET`. Dev/test keep returning the raw value (permissive defaults preserved).
2. `main.py` — add `from contextlib import asynccontextmanager` + a lifespan that touches `settings.effective_database_url`, `settings.effective_jwt_secret_key`, `settings.effective_provider_key_encryption_secret`, `settings.effective_receipt_extraction_mode`, and the four collection-account properties; wire via `FastAPI(..., lifespan=lifespan)` (main.py:30). Any violation raises at boot with the variable-naming message (NB-63.1). Health endpoint untouched (main.py:76-84; `env` disclosure is NB-71.3, deferred).
3. `apps/platform-api/.env.example` — lines 2 and 5 become `JWT_SECRET_KEY=` / `PROVIDER_KEY_ENCRYPTION_SECRET=` (empty) with a comment: "REQUIRED in non-dev. Generate with: `python -c \"import secrets; print(secrets.token_urlsafe(48))\"`. Never commit a real value." Keep CBE/DASHEN lines 6-9 as-is — those are account metadata placeholders, not forgeable credentials; their guards already enforce non-empty in prod (config.py:104-134).
4. Root `.env.example` — lines 11/14 empty + same instruction. Root line 4 `POSTGRES_PASSWORD=postgres` → `POSTGRES_PASSWORD=` empty + instruction (NB-63.4 mirror; README copy flow `cp .env.example .env` at README.md:124/143/154/163 keeps working — user fills values).
5. `docker-compose.yml`:
   - Line 9: `POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}` (no default)
   - Line 11: `- "127.0.0.1:${POSTGRES_PORT:-5432}:5432"` (loopback bind)
   - Line 30: `DATABASE_URL: postgresql+psycopg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD}@postgres:5432/${POSTGRES_DB:-supply_chain}` (password fallback removed; `POSTGRES_DB/USER` non-secret fallbacks retained)
   - Line 31: `JWT_SECRET_KEY: ${JWT_SECRET_KEY:?JWT_SECRET_KEY must be set}`
   - Line 34: `PROVIDER_KEY_ENCRYPTION_SECRET: ${PROVIDER_KEY_ENCRYPTION_SECRET:?PROVIDER_KEY_ENCRYPTION_SECRET must be set}`
   - Line 36 `ALLOWED_HOSTS` `testserver` default: unchanged (NB-71.2, later phase)
   - `APP_ENV` default `production` (line 37): unchanged
6. **Rotation task (NB-63.5) — HUMAN/OPS, not code:** verify the Vercel `platform-api` production env holds real (non-placeholder) `JWT_SECRET_KEY`/`PROVIDER_KEY_ENCRYPTION_SECRET` (they were set in prior phases per `tech-backlog.md:149-151`/PROD-05); rotate if any env may have been deployed from defaults; document the rotation in `docs/swarm/STATE.md` §7 and the ledger before Batch 1 completion (STATE.md:131). Owner: @devops/@architect.

**Tests (TDD, red first — extend `tests/test_config_guards.py`, reusing `_prod_settings` at :15-28):**
- `test_production_rejects_known_jwt_placeholder` — 40-char committed placeholder → `ValueError` matching `JWT_SECRET_KEY` (NB-63.1)
- `test_production_rejects_known_provider_placeholder` — 43-char committed placeholder → `ValueError` matching `PROVIDER_KEY_ENCRYPTION_SECRET` (NB-63.1)
- `test_production_rejects_compose_jwt_fallback` — 23-char `change-me-in-production` → `ValueError` (adjudication 6)
- `test_production_rejects_dev_fallback_default` — 46-char dev default → `ValueError` (adjudication 6)
- `test_production_accepts_novel_long_secret` — 40 random chars not in the set → passes (edge case §2.1: single-char difference is a real secret)
- `test_development_placeholder_values_allowed` — dev env with exact placeholder strings → no raise (edge case: dev defaults permissive, `production-security-hardening.md:30`)
- Existing: `test_production_jwt_secret_min_length` (:98-102) and `test_production_provider_key_encryption_secret_min_length` (:78-81) must stay green — pins NB-63.2 (length guard preserved)

**New `tests/test_secret_placeholder_hygiene.py` (static, pins NB-63.3/63.4; precedent: `test_prod_sample_data_packaging.py` reads repo files):**
- `test_platform_api_env_example_ships_empty_secrets` — parse `apps/platform-api/.env.example`; `JWT_SECRET_KEY=`/`PROVIDER_KEY_ENCRYPTION_SECRET=` values empty; no line matches any string in `KNOWN_PLACEHOLDER_SECRETS`
- `test_root_env_example_ships_empty_secrets` — same for root `.env.example` incl. `POSTGRES_PASSWORD=` empty
- `test_compose_has_no_secret_defaults_and_binds_loopback` — `docker-compose.yml` text: no `:-change-me` / `:-postgres` password fallback on lines 9/30/31/34; `127.0.0.1:` prefix on the postgres port line; `:?` error interpolations present

**Risk callout (affects every environment):** a local `apps/platform-api/.env` with `APP_ENV=production` + the old placeholder now aborts boot with the naming error — that is the intended fail-fast; remediation is real values or `APP_ENV=development` for local dev. The pytest suite runs in dev/test env so guards skip; `conftest.py:114` TestClient `with` context will exercise the new lifespan in test env (guards skip → no breakage).

### 4.2 NB-65 — The feedback surface cannot be abused (P1)

**Ground truth:** `apps/platform-api/app/api/endpoints/feedback.py:10-23` — `POST /api/v1/feedback` (mounted at `router.py:49` + `main.py:73`) has no auth dependency; unlimited anonymous 2 KB writes (schema cap at `schemas/feedback.py:6-9`). Console caller: `logisticsApi.ts:264-265` → axios instance `api.ts:85-101` which always attaches `Authorization: Bearer` + `X-Organization-Id`; form renders only inside the protected dashboard (`DashboardPage.tsx:389`). No existing feedback tests in `tests/` (verified by grep).

**Implementation intent (@build):**
- `feedback.py`: import `User` + `get_current_user` from `app.api.security`; add `user: User = Depends(get_current_user)` to `submit_feedback`; stamp `user_email=payload.user_email or user.email` (identity-bearing record without a schema change — `feedback.user_email` exists at `models/feedback.py:12`). Response model/status unchanged. Anonymous POST → FastAPI's 401 `'Missing authentication token'` (`security.py:55`) — the "clear message" (NB-65.1).
- **Console: zero production edits.** Verified: no console change is required for the signed-in path; the 401 path soft-signs out via the NB-59 interceptor (`api.ts:103-112`), which is the documented session-expiry behavior, not a regression.
- The public rate-limited alternative is not implemented (adjudication 3) — NB-65.2's "if" branch is intentionally unmet and recorded as a rejected decision, satisfying NB-65.3 (no endpoint accepts unlimited anonymous writes).

**New `tests/test_feedback_auth.py` (reuses `client`/`admin_token`/`viewer_token` fixtures, `conftest.py:108-137`):**
- `test_anonymous_feedback_rejected` — no headers → 401, detail contains `authentication` (NB-65.1)
- `test_authenticated_feedback_creates_row` — `admin_token` POST → 200 `FeedbackRead`; row persisted in `feedback` (NB-65.3: bounded by identity)
- `test_feedback_stamps_authenticated_user_email` — payload without `user_email` → stored `user_email == 'admin@testco.com'`
- `test_feedback_preserves_provided_email` — payload with `user_email` → stored value preserved
- `test_feedback_message_validation_preserved` — 2001-char message → 422 (pins schema cap, NB-65.3 bounded input)
- `test_authenticated_repeat_submissions_allowed` — two sequential authed POSTs → both 200 (edge case `production-security-hardening.md:52`: a returning signed-in user is never blocked)

### 4.3 NB-66 — No known-vulnerable dependency versions (P1)

**Ground truth:** `apps/ops-console/package.json:16` axios `^1.7.2`, lockfile resolved `1.16.1` (lockfile:2030). `apps/product-web/package.json:19` next `^14.2.35`, lockfile resolved `14.2.35` (lockfile:2254). `apps/desktop/package.json:15` electron `^31.0.2`, lockfile resolved `31.0.2` (lockfile:289).

**4.3.1 axios (console) — H-3:**
- Edit `apps/ops-console/package.json:16` → `"axios": "^1.18.0"`; run `npm --prefix apps/ops-console install` (lockfile-only effect; resolves the prototype-pollution/auth-injection/proxy-routing/form-DoS families per `security-audit-2026-08-10.md:88-91`).
- Verify lockfile `node_modules/axios` version ≥ 1.18.0; run `npm --prefix apps/ops-console run test` (143/143 at last ledger record, `tech-backlog.md:219`), `typecheck`, `build`.

**4.3.2 Next.js (site) — H-2:**
- Target `next@15.5.21` (adjudication 4). Execute `npm --prefix apps/product-web install next@15.5.21`; run `npx --prefix apps/product-web @next/codemod@canary upgrade 15` **only if** the build reports API changes (ground truth: no `use server`, `cookies()`, `headers()`, `searchParams`, `params`, `generateMetadata`, or server `fetch` in `apps/product-web/src` — grep verified zero matches — so the 15.x async-request codemods are expected to be no-ops; do not run codemods pre-emptively).
- **Locked-behavior risk assessment (must all pass, `production-security-hardening.md:59`):**
  - Five-section home structure + single-CTA + pricing copy: pinned by `site-content.phase5.test.tsx`, `routes-single-cta.phase5.test.tsx`, `home.phase5.test.tsx` etc. (62/62 at last ledger record `tech-backlog.md:158`) — component code untouched; the upgrade is runtime-only.
  - Hero-entrance client wrapper (`hero-entrance.tsx:1-25`): Next 14.2.35's client-reference proxy crash that motivated the wrapper (`tech-backlog.md:124` adjudication note) is fixed upstream in 15.x; the wrapper stays byte-identical (zero churn minimizes risk); `home.smoke.test.tsx` pins the single `data-hero-entrance` animation.
  - Weight gate: `check:bundle` reads `.next/app-build-manifest.json` (`check-bundle-budget.mjs:39-41`) — still emitted by Next 15 App Router builds; last recorded totals 614–711 KB vs 1.2 MB budget (`tech-backlog.md:117`) ≈ 500 KB headroom. If the manifest path changes, update the script (justified correction, precedent `tech-backlog.md:124` note 2).
  - Self-hosted Docker path: `next.config.mjs:4` `output: 'standalone'` must persist — `Dockerfile:20` copies `.next/standalone`; `Dockerfile:5` uses `npm ci` which consumes the lockfile.
- Verify: `npm --prefix apps/product-web run build`, `npm --prefix apps/product-web run check:bundle` (expect PASS, all routes < 1,200,000 bytes), `npm --prefix apps/product-web run test`, `npm --prefix apps/product-web run start` local 200 smoke on `/`, `/pricing`, `/launch`.
- **Interim mitigation (only if the upgrade must be split — contingency, not the plan):** pin `next@14.2.35` (no drift), add Host pinning at the self-hosted edge (product-web service `docker-compose.yml:65-77`), and record that no Server Actions exist so the custom-server SSRF class (GHSA-89xv-2m56-2m9x) is not reachable; the RSC cache-poisoning class (GHSA-68g3-v927-f742) is the residual exposure until the upgrade lands. `__NEXT_PRIVATE_ORIGIN` is **not** applicable (no Server Actions).

**4.3.3 Electron (desktop) — H-4 (version half only, adjudication 5):**
- Edit `apps/desktop/package.json:15` → `"electron": "^43.0.2"`; run `npm --prefix apps/desktop install` (postinstall `ensure-electron-binary.cjs` downloads the v43 binary; `scripts/ensure-electron-binary.cjs:65-121` handles the swap; on Windows uses `tar -xf` at :103).
- Verify: `npm --prefix apps/desktop run doctor` → "[desktop] Electron 43.x binary is ready"; lockfile `node_modules/electron` version ≥ 43.0.0.
- **Deferred (Phase 2 slice, tracked — NB-66.3 stays OPEN):** exact-origin `will-navigate` guard, `setPermissionRequestHandler`, DevTools gating `!app.isPackaged`, `@electron/fuses` `runAsNode`/`nodeCliInspect` (audit H-4 fix list, `security-audit-2026-08-10.md:96`; current `main.cjs` has no navigation guard — remote URLs loaded at `main.cjs:271,310` — and a `toggleDevTools` menu role at :203). IPC `sender` validation is NB-71.8 and stays out of this phase.

## 5. Dependency Graph / Execution Order

```
NB-63 config.py + main.py (lifespan) ──┐
                                        ├─► shared TestClient surface (conftest.py:114) — must be green after BOTH land
NB-65 feedback.py + test_feedback_auth.py ┘

NB-66: 3 fully independent lockfile/package bumps (ops-console ∥ product-web ∥ desktop) — parallel-safe, disjoint files
```

- **Order:** Step 1 = NB-63 (config + main.py + guards + hygiene tests; red → green → full backend suite). Step 2 = NB-65 (feedback + tests). Step 3 = NB-66 (three bumps; console suite, site build+bundle+tests, desktop doctor). Steps 1 and 3 can run in parallel with NB-65 after Step 1 lands; within Step 3 all three bumps run in parallel.
- **Shared-file conflicts:** none — config.py vs feedback.py vs the three package.json files are disjoint (inventory §3). The only coupling is behavioral: NB-65's tests run against `app.main`, which NB-63 modifies (lifespan) — so NB-63 lands first.
- **Commits (atomic, @build only, after @qa approval of each):** `fix(sec): NB-63 known-placeholder rejection + compose/.env.example hardening` → `fix(sec): NB-65 authenticated feedback` → `fix(sec): NB-66 axios@^1.18, next@15.5.21, electron@^43` (three atomic commits, matching phase7's one-commit-per-ticket protocol, `phase7-production-r0.md:26-34`).

## 6. Acceptance Mapping (test → NB criterion)

| Ticket | Criterion | Proving test / evidence |
|---|---|---|
| NB-63.1 | startup aborts naming variable | `test_production_rejects_known_jwt_placeholder`, `test_production_rejects_known_provider_placeholder` + lifespan wiring (raise at boot) |
| NB-63.2 | length guard preserved | existing `test_production_jwt_secret_min_length`, `test_production_provider_key_encryption_secret_min_length` green |
| NB-63.3 | no committed placeholder passes guards | `test_platform_api_env_example_ships_empty_secrets`, `test_root_env_example_ships_empty_secrets`, + compose scan |
| NB-63.4 | loopback bind + no DB password default | `test_compose_has_no_secret_defaults_and_binds_loopback` |
| NB-63.5 | rotation documented | STATE.md §7 + ledger entry (human/ops task — QA verifies the record exists) |
| NB-65.1 | signed-in required, clear rejection | `test_anonymous_feedback_rejected` (401) |
| NB-65.2 | rate-limit alternative | **Rejected** (adjudication 3) — recorded in blueprint; not applicable |
| NB-65.3 | bounded queue, no unlimited anonymous writes | `test_authenticated_feedback_creates_row` + `test_feedback_message_validation_preserved` + 401 test |
| NB-66.1 | Next ≥15.5.21 before further self-hosted deploys | lockfile check (15.5.21) + build/check:bundle/tests green |
| NB-66.2 | axios ≥1.18.0 | lockfile check + console suite/typecheck/build green |
| NB-66.3 | supported Electron + checklist | Version half: lockfile + doctor green. **Checklist: OPEN — tracked to Phase 2 slice (adjudication 5)** |
| NB-66.4 | suites/typecheck/builds pass, surfaces identical | full suite runs + bundle budget + route smoke (§7) |

## 7. Integration Risks

1. **Next 15 vs weight gate:** `check:bundle` depends on `.next/app-build-manifest.json` (script :39-41); Next 15 still emits it. Headroom ~500 KB. If totals shift, gate fails loudly → investigate before merging; do not raise the budget.
2. **Next 15 vs locked site behaviors:** runtime-only upgrade; hero-entrance wrapper (React 18 + framer-motion 12.43) untouched; 62/62 site tests + single-CTA/five-section guards are the tripwire.
3. **axios bump vs console tests:** `api.test.ts` drives the real axios instance with a custom adapter (`api.test.ts:65-77`); 1.16→1.18 is semver-minor, but the interceptor/clone changes in the patched family are exactly what these tests pin — run the full console suite, not a subset.
4. **Config guard vs local dev flows:** any local `.env` with `APP_ENV=production` + old placeholder values now fails boot with a naming error (intended). Devs with `APP_ENV=development` unaffected. pytest unaffected (test env skips guards).
5. **docker-compose default removal vs local docker dev:** `docker compose up` now requires `JWT_SECRET_KEY`, `PROVIDER_KEY_ENCRYPTION_SECRET`, `POSTGRES_PASSWORD` (compose `:?` errors list the variable). README copy-flow still works — root `.env.example` ships empty + instructions. Document the new requirement in the PR description.
6. **Lifespan vs existing deployments:** any boot from defaults now crashes at startup instead of at first auth — deployment must carry real secrets (Vercel already does).
7. **Feedback 401 vs console UX:** an expired session submitting feedback triggers the NB-59 soft-signout (storage cleared, ProtectedRoute redirect) — documented behavior, not a regression; no console code change.
8. **Electron bump:** binary download (~100 MB) at install; `doctor` validates. `ensure-electron-binary.cjs` handles the swap; no runtime code change in Phase 1.

## 8. QA Checklist (@qa)

Run in order; record every command + result (`AGENTS.md` §6 evidence rule):

1. `git status --short --branch` → only batch files + pre-existing untracked (STATE.md:102 list), branch `feat/security-hardening-v1`
2. Backend (cwd `apps/platform-api`): `.venv\Scripts\python.exe -m pytest tests/test_config_guards.py tests/test_secret_placeholder_hygiene.py tests/test_feedback_auth.py -q` → new tests green, red-first proof captured in PR notes; then full `.venv\Scripts\python.exe -m pytest -q` → all green (372 `def test_` functions across 61 modules per static scan; last recorded full-suite count 298+, `phase7-production-r0.md:177`)
3. NB-63 behavior: construct `Settings(_env_file=None, app_env='production', jwt_secret_key='change-me-in-production-minimum-32-bytes', ...)` → `effective_jwt_secret_key` raises naming `JWT_SECRET_KEY` (QA may run this as a one-liner against the venv)
4. NB-65 behavior: curl anonymous POST `/api/v1/feedback` → 401; with a real token → 200 (via test suite)
5. Console: `npm --prefix apps/ops-console run test` (143/143 last record), `npm --prefix apps/ops-console run typecheck`, `npm --prefix apps/ops-console run build`
6. Site: `npm --prefix apps/product-web run build`, `npm --prefix apps/product-web run check:bundle` (PASS, all routes < 1,200,000 bytes), `npm --prefix apps/product-web run test` (62/62 last record)
7. Desktop: `npm --prefix apps/desktop run doctor` → Electron 43.x ready
8. Static: `Select-String` on `apps/platform-api/.env.example`, root `.env.example`, `docker-compose.yml` → zero placeholder secrets, empty values + instructions, `127.0.0.1:` postgres bind
9. Audit against `pending-behaviors.md:648-685` acceptance criteria verbatim (mapping §6), and `docs/swarm/STATE.md` updated (NB-63.5 rotation record)

## 9. Evidence Format (commands + expected results)

```
# NB-63 (cwd apps/platform-api)
.venv\Scripts\python.exe -m pytest tests/test_config_guards.py tests/test_secret_placeholder_hygiene.py -q
  → 9 passed (6 placeholder + 3 hygiene; existing 14 guard tests stay green)

# NB-65 (cwd apps/platform-api)
.venv\Scripts\python.exe -m pytest tests/test_feedback_auth.py -q
  → 6 passed

# NB-66 console
npm --prefix apps/ops-console install && (Select-String -Path apps/ops-console/package-lock.json -Pattern '"node_modules/axios"' -Context 0,1)  → version ≥ 1.18.0
npm --prefix apps/ops-console run test && npm --prefix apps/ops-console run build → all pass

# NB-66 site
npm --prefix apps/product-web install next@15.5.21
npm --prefix apps/product-web run build && npm --prefix apps/product-web run check:bundle → build ok; "check:bundle PASSED — all six routes under the 1.2 MB budget."
npm --prefix apps/product-web run test → all pass

# NB-66 desktop
npm --prefix apps/desktop install && npm --prefix apps/desktop run doctor → "[desktop] Electron 43.x binary is ready"
```

## 10. Non-Goals (Phase 1)

- No schema changes/migrations (feedback table untouched; `user_id` column deliberately not added).
- No console/site/desktop runtime code changes (zero production edits outside the three package.json files; feedback.py is the only endpoint edit).
- No NB-64/67/68/69/70/71 work (ticketed later phases); no `testserver` default removal; no `/health` env drop; no CSP; no CSV cap; no Python lockfile; no Electron checklist.
- No rate-limiting/honeypot machinery for feedback (rejected alternative, adjudication 3).
- No Next 16 / React 19 migration (recorded option, adjudication 4).

## 11. QA-Audit-Against

QA audits against: `docs/behaviors/pending-behaviors.md:648-685` (NB-63/65/66 verbatim), `docs/behaviors/production-security-hardening.md` §3/§5/§6, `docs/security-audit-2026-08-10.md` C-1/H-5/H-3/H-2, and this document (adjudications 1-6 binding). Ledger debit after QA APPROVED per ticket; NB-66.3 flagged OPEN with the Phase 2 checklist slice.
