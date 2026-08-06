# Production-Readiness & Go-To-Market Plan (v1)

**Author:** @visionary (PM) · **Date:** Aug 6, 2026 · **Status:** PLAN — awaiting @architect execution
**Handoff target:** `@architect` → `@plan` → `@build`/`@fixer` → `@qa` → atomic commits on a new feature branch (e.g. `feat/production-readiness-v1`), then merge to `master` + deploy.

> This plan converts the shipped market-contender-v1 batch (TECH-01..50, all QA-approved) into a production-launchable system: real environment wiring (Supabase CLI + Vercel CLI), site/desktop/system market-readiness checklists, and a competitive grounding (FourKites/project44 — see `docs/competitor-research-fourkites-project44.md`).

---

## 0. Ground truth — what shipped vs what is NOT production-ready

### Shipped & QA-approved (master @ `34bf4a5`)
- **platform-api** (FastAPI + SQLAlchemy + Alembic): full cashflow (ETB tiers, trials, limbo/grace/lock, receipts, wallet credits, audit, reversals), activation (seeding, milestones, free-cap lock), metering, BYOK provider keys. **298+ backend tests green.**
- **ops-console** (Vite + React): dashboard, admin receipts queue, reversals panel, activation surfaces. **30 tests green.**
- **product-web** (Next.js 14): honest 5-section funnel, single "Start free" CTA, ETB pricing, weight gate (<720 KB/route). **57 tests green.**
- **desktop** (Electron shell): hosts ops-console login/dashboard, onboarding cockpit, connection test. **v0.1.0, dev-only — NOT packaged.**

### Known production blockers (from the batch ledger + this audit)
1. **PROD-A — API container lacks sample data.** `apps/platform-api/Dockerfile` copies `app`, `alembic`, `scripts` — but NOT `sample-data/`. The seeding service reads CSVs from `settings.sample_data_dir` ('sample-data') at signup → **in the Docker image, seeding crashes → signup fails in production.** Must bake `sample-data/` into the image (or make it a mounted volume + env path).
2. **PROD-B — Receipt extraction is mock-only.** `receipt_extraction_mode='mock'` default; only the deterministic mock adapter exists. Production needs either (a) a real HTTP provider adapter (BYOK plumbing already real), or (b) an explicit production decision to run the zero-confidence workflow (admin manually reads every receipt — viable for launch volume, but must be a deliberate setting, not the dev default).
3. **PROD-C — SMS gateway is an outbox stub.** `_dispatch_sms` raises NotImplementedError; `organizations.contact_phone` has no capture UI. Escalation SMS (NB-16) silently degrades to `failed/no_phone_on_file` rows. Production needs: a real gateway adapter (e.g., Ethiopian SMS providers) + a phone-capture field on the account page.
4. **PROD-D — CBE/Dashen collection accounts empty.** `cbe_account_number` / `dashen_account_number` / holders default to `''` — invoices would render blank account strings. Real values must be set in production env (admin-provided).
5. **PROD-E — Dev secrets in defaults.** `JWT_SECRET_KEY` defaults to `dev-secret-do-not-use-in-production-minimum-32`; `PROVIDER_KEY_ENCRYPTION_SECRET` empty; `APP_ENV` gates these — production must set real values and `APP_ENV=production`.
6. **PROD-F — Rate limits.** slowapi `200/min` per IP is active in production; signup is a 30/5min-limit in Supabase legacy config. Validate limits against the launch funnel (bursts of signups on the same NAT = false 429s for office networks).
7. **PROD-G — Allowed hosts & CORS need production domains** (currently localhost-only defaults — the CORS fix in `34bf4a5` is dev-oriented; production origins must be added).
8. **PROD-H — Human gap TECH-22 (NB-22):** CBE/Dashen fee-schedule verification vs ±1,000 ETB tolerance — **user action, blocks production launch** (documented procedure in `docs/plans/phase3-audit-reversibility.md` §12).
9. **PROD-I — Stale competitive doc.** `docs/competitive-landscape-2026.md` references pre-Phase-5 site components and suggests a "competitive evidence section with named benchmark signals" — **conflicts with NB-43 honesty rules.** Needs rewriting against the shipped site (research superseded by `docs/competitor-research-fourkites-project44.md`).
10. **PROD-J — Housekeeping:** dead `@supabase/supabase-js` dep + unused `.back-to-top` CSS in product-web; TECH-49 (`shipments.shipment_no` unique) parked.

---

## 1. Target deployment topology

| Surface | Where it runs | How it's reached |
|---|---|---|
| **product-web** (site) | **Vercel** (managed Next.js) | `https://freightpilot.com` (or chosen domain) |
| **platform-api** (API) | **Docker on VPS** (existing docker-compose) or managed host | `https://api.freightpilot.com` — CORS/ALLOWED_HOSTS updated |
| **ops-console** | Docker/VPS (nginx :80) or Vercel | `https://app.freightpilot.com` (console) |
| **Postgres** | **Supabase hosted project** (already linked: `freightpilot-prod`, ref `azljjrjatdpkcvjbpztn`) OR docker Postgres | `DATABASE_URL` via Supabase pooler (port 5432/6543) |
| **desktop** | Windows installers (electron-builder) | download center + auto-update |

**Key decision for @architect:** Supabase's role. Recommended: **Supabase = hosted Postgres only** (the platform-api already does its own auth/JWT/Alembic migrations; the legacy Supabase auth migration `20260727153410_company_onboarding_and_profiles.sql` is vestigial after Phase 5 removed the Supabase signup path). Options: (a) run Alembic migrations against the Supabase Postgres and retire the supabase/ legacy dir, or (b) keep docker Postgres on the VPS and drop Supabase entirely. Both work — the plan below documents the Supabase-Postgres path since the project is already linked, with the retirement note for (b).

---

## 2. Environment wiring — Supabase CLI

```bash
# 0) Prereqs: supabase CLI installed, logged in (access token), project linked (already done: freightpilot-prod)
supabase login
supabase link --project-ref azljjrjatdpkcvjbpztn

# 1) Get the real connection strings
supabase projects list                 # confirm ref
# DATABASE_URL (direct)   : postgresql+psycopg://postgres.<ref>:<DB_PASSWORD>@aws-0-<region>.pooler.supabase.com:5432/postgres
# DATABASE_URL (pooler)   : postgresql+psycopg://postgres.<ref>:<DB_PASSWORD>@aws-0-<region>.pooler.supabase.com:6543/postgres
# (Use the transaction pooler port 6543 for the API; SSL required)

# 2) Run platform-api Alembic migrations against it (from apps/platform-api)
set DATABASE_URL=<pooler-url>& python -m alembic upgrade head

# 3) Legacy supabase auth migration: apply ONLY if the legacy onboarding flow is kept.
#    Recommendation: do NOT apply — Phase 5 removed the Supabase signup path; keep
#    supabase/migrations as history, delete the dir after sign-off (PROD-09).
```

**Supabase CLI does not manage app env vars** (it manages the project's own secrets). So the "real env variables" for our apps are stored in each app's deployment host:
- platform-api env → VPS `.env` / docker-compose `environment:` (or a secrets manager)
- product-web env → **Vercel** (`vercel env add`)
- ops-console env → build-time `.env.production` on VPS

---

## 3. Environment wiring — Vercel CLI (product-web)

```bash
# 0) Prereqs: vercel CLI, logged in, project created
vercel login
cd apps/product-web
vercel link --yes            # link to the freightpilot site project

# 1) Add production env vars (values per matrix below)
vercel env add NEXT_PUBLIC_SITE_URL production
vercel env add NEXT_PUBLIC_PLATFORM_API_URL production   # https://api.freightpilot.com/api/v1
vercel env add NEXT_PUBLIC_APP_CONSOLE_URL production    # https://app.freightpilot.com
vercel env add NEXT_PUBLIC_CONTACT_FORM_ENDPOINT production  # real formsubmit.co address
vercel env add NEXT_PUBLIC_DOCS_URL production
vercel env add NEXT_PUBLIC_DESKTOP_DOWNLOAD_URL production

# 2) Deploy
vercel --prod

# 3) Domains/TLS (managed by Vercel)
vercel domains add freightpilot.com      # or use Vercel dashboard
```

**Env var matrix (product-web → Vercel):**

| Var | Production value | Notes |
|---|---|---|
| `NEXT_PUBLIC_SITE_URL` | `https://freightpilot.com` | metadata/OG |
| `NEXT_PUBLIC_PLATFORM_API_URL` | `https://api.freightpilot.com/api/v1` | the ONLY signup path |
| `NEXT_PUBLIC_APP_CONSOLE_URL` | `https://app.freightpilot.com` | post-signup redirect |
| `NEXT_PUBLIC_CONTACT_FORM_ENDPOINT` | real formsubmit.co email relay | not a CRM/drip |
| `NEXT_PUBLIC_DOCS_URL` | real docs URL | footer link |
| `NEXT_PUBLIC_DESKTOP_DOWNLOAD_URL` | real download center | footer link only (DEFERRED-09) |

**Env var matrix (platform-api → VPS):**

| Var | Production value | Notes |
|---|---|---|
| `DATABASE_URL` | Supabase pooler URL (or VPS Postgres) | `postgresql+psycopg://…:6543/postgres` |
| `JWT_SECRET_KEY` | ≥32-char random | generate + store in secrets manager |
| `PROVIDER_KEY_ENCRYPTION_SECRET` | random 32+ bytes | decrypts org BYOK keys |
| `CBE_ACCOUNT_HOLDER` / `CBE_ACCOUNT_NUMBER` | real CBE account | PROD-D — required before invoices |
| `DASHEN_ACCOUNT_HOLDER` / `DASHEN_ACCOUNT_NUMBER` | real Dashen account | PROD-D |
| `CORS_ORIGINS` | `https://freightpilot.com,https://app.freightpilot.com,https://www.freightpilot.com` | PROD-G |
| `ALLOWED_HOSTS` | `api.freightpilot.com,freightpilot.com,app.freightpilot.com,localhost` | PROD-G |
| `APP_ENV` | `production` | enables production guardrails |
| `RECEIPT_EXTRACTION_MODE` | `real` (after PROD-B) or explicit `zero-confidence` decision | |
| `SMS_*` | real gateway creds (after PROD-C) | |
| `SAMPLE_DATA_DIR` | `/app/sample-data` (after PROD-A) | |
| `BLOCKED_PUBLIC_EMAIL_DOMAINS` | keep current list | |

**Env var matrix (desktop):**

| Var | Production value | Notes |
|---|---|---|
| `OPS_CONSOLE_URL` | `https://app.freightpilot.com/login` | default is localhost:5173 — must ship prod value |
| `PRODUCT_SIGNUP_URL` | `https://freightpilot.com/launch` | |
| `DOCS_URL` | real docs URL | |

---

## 4. Site market-readiness checklist (product-web)

- [ ] Domains + TLS live (Vercel-managed), `www` + apex redirects
- [ ] `NEXT_PUBLIC_*` all set via `vercel env add` (matrix above) — no hardcoded localhost anywhere (grep `localhost` in `apps/product-web/src` must return only comments/tests)
- [ ] Manual 3G devtools pass on production build: every route `LoadEventEnd < 3s` at 400 kbps; trust strip ≤3 lines at 360px (NB-42 checklist item — now that it's the REAL environment, do the manual pass once and record it)
- [ ] `check:bundle` gate runs in CI (add to a GitHub Action or the deploy pipeline)
- [ ] Real contact form endpoint (formsubmit.co with a real inbox; test one submission end-to-end)
- [ ] Post-signup redirect verified against the real console domain + cookie path (same-site cookie flow)
- [ ] Analytics: **decision required** — none ships today (DEFERRED-08). Minimum for market-readiness: privacy-light pageview + "Start free" click instrumentation (e.g., Plausible/Umami, `defer`/lazyOnload per NB-42.7). No fingerprinting, no ad networks.
- [ ] Error monitoring for the site (e.g., Sentry with `lazyOnload`) — at minimum the launch form errors must be observable
- [ ] `robots.txt` + `sitemap.xml` + sensible `404` page
- [ ] OG/social metadata verified (layout.tsx title/description already honest — verify rendered tags)
- [ ] Honesty re-audit post-deploy: grep production HTML for "free trial" (only /pricing FAQ), "Trusted by", "Most Popular", fake contacts
- [ ] The stale `docs/competitive-landscape-2026.md` rewritten or deleted (PROD-I)

## 5. Desktop market-readiness checklist (apps/desktop)

- [ ] **Package with electron-builder** (add `electron-builder` + `electron-builder.yml`): Windows NSIS installer (and optionally portable). No packaging exists today — this is the main gap.
- [ ] **Code signing** (Windows): sign the installer (self-signed acceptable for internal pilots; real cert for public launch — SmartScreen friction otherwise)
- [ ] **Auto-update** (electron-updater + a release feed — GitHub Releases or a VPS endpoint)
- [ ] Prod URLs baked/configured: `OPS_CONSOLE_URL=https://app.freightpilot.com/login`, `PRODUCT_SIGNUP_URL=https://freightpilot.com/launch`, `DOCS_URL=…` — via a packaged config file (not requiring env vars on end-user machines)
- [ ] Onboarding cockpit's "connectivity test" must point at the **production** console + API health endpoints, not localhost
- [ ] Electron security posture re-verified post-packaging: context isolation ON, nodeIntegration OFF, `setWindowOpenHandler` external-browser behavior (already per README — re-verify in the packaged build)
- [ ] Installer smoke test on a clean Windows VM: install → onboarding → connect → launch console → login
- [ ] Version bump to 1.0.0 + release notes

## 6. System market-readiness checklist (platform-api + ops-console)

- [x] **PROD-A** sample-data baked into the API image (+ a test that runs seeding from a pristine container filesystem — the current tests run from the repo root where CSVs exist, masking the bug)
- [x] **PROD-B** extraction mode decision: wire one real provider adapter (BYOK provider key flow already exists) OR explicitly set zero-confidence workflow + admin training note
- [x] **PROD-C** SMS gateway adapter + `contact_phone` capture (account page) + escalation end-to-end test with the real gateway sandbox
- [x] **PROD-D** real CBE/Dashen account values in prod env; invoice rendering test with real values (no blank accounts)
- [x] **PROD-E** real secrets; `APP_ENV=production`; verify prod config guardrails (JWT length check, DB required)
- [ ] **PROD-F** rate-limit review: slowapi 200/min default — verify signup/login bursts; per-route tuning if needed
- [ ] **PROD-G** CORS + ALLOWED_HOSTS with production domains (extend the `test_cors_config.py` list with the prod origins)
- [ ] **PROD-H** TECH-22 human verification (user action) — document findings in `cashflow-bank-transfer-receipt-verification.md` §12
- [ ] **PROD-J** housekeeping: remove dead `@supabase/supabase-js` dep, unused `.back-to-top` CSS; TECH-49 filed (parked)
- [ ] DB: Alembic migrations applied to the production Postgres; **backup strategy** (Supabase PITR or pg_dump cron) + restore drill
- [ ] Health endpoint + uptime monitoring (the `/health` endpoint exists — wire an uptime check + alert)
- [ ] Logging/observability: structured logs already exist (request_completed); add error-rate alerting; crash reporting for the API
- [ ] Ops-console production build env: `VITE_API_BASE_URL=https://api.freightpilot.com/api/v1` (or nginx proxy), cookie `Secure` + `SameSite` correctness across app./api. domains
- [ ] Free-cap + billing clock sanity in production timezone (Addis UTC+3) — the tz-sensitive tests were fixed (TECH-48); verify banner day-counts against the real clock
- [ ] Backup + restore drill for the sample-data seeding path (workspace.reset must work in prod)
- [ ] Load smoke: N concurrent signups → seeding → first optimization (the free-cap meters and pitch crossings are lazy — confirm no hot-path regressions)

## 7. Competitive positioning — market-ready message (from research)

See `docs/competitor-research-fourkites-project44.md` for full evidence. The one-line GTM thesis:

> **"The only Ethiopian supply-chain platform with published ETB pricing, a real Free tier, and bank-transfer payments — built for operators who FourKites and project44 don't serve."**

- **Match (table stakes):** real-time tracking + predictive ETA; exception management as the core workflow; low-friction data onboarding (sample data = our version of their "any document" promise).
- **Don't copy:** unverifiable marketing stats (our honesty rules are the differentiator), opaque enterprise pricing, analyst theater, agent mythology.
- **Anchor pricing against local substitutes** (spreadsheets + WhatsApp + telebirr), not the giants — Free→Starter conversion is the funnel that matters.
- **Collect real local proof early** (ETB saved, hours saved per operator) — the giants set the expectation that buyers ask for proof; we must publish real numbers, not invented ones.

## 8. Phased rollout

| Phase | Gate | Content |
|---|---|---|
| **R0 — Environment wiring** | PROD-A..G resolved + deployed | Supabase Postgres + Alembic; Vercel site with real env; API on VPS with prod CORS/hosts; secrets |
| **R1 — Private beta (10–20 operators)** | Site + console + cashflow verified by real users | Recruit operators; collect real case data; fix extraction/SMS gaps with real traffic |
| **R2 — Paid pilot** | First paying customer; TECH-22 human gate CLOSED | First invoices + receipts + wallet credits in production; partial payments |
| **R3 — Public launch** | Site honesty re-audit + analytics live + desktop installer public | marketing push; desktop download center live |

## 9. Handoff to @architect — execution tickets

Create branch `feat/production-readiness-v1`. Suggested tickets (priority: P0 = blocks R0, P1 = R1/R2, P2 = nice-to-have):

| Ticket | Priority | Status | Acceptance criterion (user-visible) |
|---|---|---|---|
| PROD-01 | P0 | ✅ DONE (R0) | Signup succeeds in the production API container — sample-data CSV present in image; seeding audit event fires |
| PROD-02 | P0 | ✅ DONE (R0) | Receipt extraction runs in production mode (real OpenAI-compatible adapter OR explicit zero-confidence mode; mock impossible in prod) |
| PROD-03 | P0 | ✅ DONE (R0) | Escalation SMS sends via a configurable REST gateway to the customer's registered phone; phone capture UI on account page |
| PROD-04 | P0 | ✅ DONE (R0) | Every invoice displays the real CBE or Dashen collection account (never blank — production config guard) |
| PROD-05 | P0 | ✅ DONE (R0) | Production secrets set; APP_ENV=production; prod config guardrails verified (JWT, DB, provider-key-encryption ≥32 chars) |
| PROD-06 | P0 | ⏳ NEXT (R1) | Site signup works end-to-end from Vercel to the production API (CORS + hosts + cookies) — dev CORS hotfix already merged (`1a3875d`) |
| PROD-07 | P1 | ⏳ | Desktop ships as a signed, auto-updating Windows installer pointing at production URLs |
| PROD-08 | P1 | ⏳ | Production Postgres backup + restore drill documented and exercised |
| PROD-09 | P1 | ⏳ | Stale `competitive-landscape-2026.md` rewritten/deleted; supabase legacy dir retired or documented |
| PROD-10 | P1 | ⏳ | Analytics (privacy-light) + error monitoring live on the site |
| PROD-11 | P1 | ⏳ | Rate-limit review pass on the launch funnel |
| PROD-12 | P2 | ⏳ | Housekeeping: dead supabase-js dep + `.back-to-top` CSS removed; TECH-49 parked note |
| PROD-13 | P2 | ⏳ | CI gates: check:bundle + full test suites wired into deploy pipeline |

**R0 status:** PROD-01..05 shipped on `feat/production-readiness-r0` (commits `cef9de2`..`2868370`, QA APPROVED, merged to master). PROD-A..E resolved. R0 verification note: PROD-04's guard makes blank accounts impossible in production config, but the REAL account values still must be supplied by the operator in the production env (TECH-22 human gate remains, blocks R2).

**Human-gate (not code, before R2):** TECH-22 fee-schedule verification — user action.

---

*This plan is the PM handoff. @architect: sanity-check the Supabase-as-Postgres decision (§1), the env matrices (§2–3), and the ticket priorities (§9), then dispatch @plan for PROD-01..05 (R0) blueprints.*
