# BLUEPRINT: PHASE 1 — Cashflow Core (TECH-01..06 / NB-01..06)

Status: LOCKED for execution by @build on branch `feat/market-contender-v1`. Written by @plan, persisted by @architect. QA audits against this document AND the NB acceptance criteria.

## 0. Goal

Make the platform's subscription tier pricing (ETB), invoice generation, trial/limbo/grace/lock lifecycle, collection-account designation, and write-lock enforcement a real, tested backend surface — without breaking the existing select-tier flow, metering threshold events, or auth cookie/bearer flows.

## 1. Ground-truth decisions (locked for @build; deviations require @architect sign-off)

1. **Signup always creates a Free-tier org.** `CompanySignupRequest.subscription_tier` becomes a *preference only* — recorded in the audit payload, never applied to state. Three existing tests must be updated (§7.3).
2. **`billing_phase` is the authoritative workspace state** (`free | trial | limbo | active | grace | hard_locked`). Legacy `subscription_status` is derived for backward compatibility: free→`active`, trial→`trialing`, limbo→`trialing`, grace→`past_due`, hard_locked→`past_due`, active→`active`.
3. **Trials are per-tier, once per tier, startable only from phase `free`.** Mid-trial tier switch: current TrialRecord closed (ended_at=now); new tier never trialed → fresh 168h trial; already trialed → no new trial (org drops to limbo). From limbo/grace/hard_locked: tier switches allowed but NEVER start trials and NEVER reset grace/lock (NB-06.4).
4. **First invoice = trial-end anchor.** `next_period_start` from last `TrialRecord.ended_at`: Starter → next month 1st; Scale/Enterprise → next quarter 1st. First invoice issued lazily at that boundary, billed in advance, `due_date = period_start`.
5. **Grace adjudication (ARCHITECT DECISION):** NB-06.3 acceptance criteria (write-disabled during grace, banner "Grace period: X days remaining") is authoritative for QA. Behavior doc §5.6 wording is superseded. Implement write-disabled grace behind `GRACE_WRITES_ENABLED = False` constant in `locks.py`.
6. **Trial overage on first invoice:** per metric, `overage_units = max(0, Σ used over counters overlapping [trial_started_at, trial_ends_at] − tier_quota_for_billing_cycle)`. Starter vs monthly quota (2,500/50); Scale/Enterprise vs quarterly quota (5,000/250). Enterprise NEVER gets overage lines.
7. **Account designation policy (NB-02.3):** per-org rotation — org's Nth invoice → `collection_accounts[(N−1) % 2]` (first CBE, second Dashen). Only `bank_code ∈ {cbe, dashen}` and `is_active = true` eligible. No customer-facing switch endpoint; designation immutable at issuance.
8. **Money is `Numeric(14,2)` / `Decimal`** in all new models, schemas, service math. Flat prices whole ETB (4500/10000/45000); overage rates: Starter 0.20/1.50 ETB, Scale 0.16/1.00 ETB (existing values re-labeled ETB).
9. **No scheduler/cron exists.** Invoice issuance is **lazy**: every guard evaluation and billing-state read calls `refresh_workspace_state`, which issues invoices at boundary crossings. At-most-once via `UniqueConstraint(organization_id, billing_period_start)`; IntegrityError → rollback → return existing.
10. **Free tier cap enforcement (NB-31, Phase 4) NOT implemented here.** Free orgs writable in Phase 1. Free orgs DO get quota entries (2500/50, no overage) so metering keeps working.

## 2. Files to CREATE

### 2.1 Models (6 new files, all under `apps/platform-api/app/models/`)

- **`collection_account.py`** — `CollectionAccount` (table `collection_accounts`): id UUID PK; bank_code String(16) UNIQUE NOT NULL; bank_name String(64); account_holder String(128); account_number String(64); is_active Boolean default True; created_at. CheckConstraint `bank_code IN ('cbe','dashen')`.
- **`subscription_invoice.py`** — `SubscriptionInvoice` (table `subscription_invoices`): id; organization_id UUID FK organizations.id CASCADE indexed NOT NULL; invoice_number String(32) UNIQUE indexed NOT NULL; tier String(24); billing_period_start Date; billing_period_end Date; flat_amount_etb Numeric(14,2); total_etb Numeric(14,2); balance_remaining_etb Numeric(14,2) (init = total); due_date Date; grace_days Integer (3 first-ever / 0 subsequent); grace_ends_at Date; designated_account_id FK collection_accounts.id RESTRICT NOT NULL; status String(24) default 'issued' (`issued|open|paid|void`); created_at. UniqueConstraint(organization_id, billing_period_start) name `uq_subscription_invoice_org_period`. Relationships: `lines`, `designated_account`.
- **`invoice_line_item.py`** — `InvoiceLineItem` (table `invoice_line_items`): id; invoice_id FK subscription_invoices.id CASCADE indexed NOT NULL; kind String(16) (`flat` | `overage_delivery_tasks` | `overage_route_optimizations`); description String(128); quantity Integer nullable; unit_price_etb Numeric(14,2) nullable; amount_etb Numeric(14,2).
- **`trial_record.py`** — `TrialRecord` (table `trial_records`): id; organization_id FK CASCADE indexed NOT NULL; tier String(24); started_at timestamptz; ended_at timestamptz; created_at. UniqueConstraint(organization_id, tier) name `uq_trial_record_org_tier`.
- **`notification.py`** — `Notification` (table `notifications`): id; organization_id FK CASCADE indexed NOT NULL; kind String(32) (`invoice_warning` in Phase 1); title String(128); message String(512); payload JSON nullable (invoice_number, amount_etb, bank_name, bank_account, due_date, grace_ends_at); expires_at timestamptz (issuance + 3 days); dismissed_at timestamptz nullable; created_at. Index (organization_id, kind, expires_at).
- **`billing_counter.py`** — `BillingCounter` (table `billing_counters`): id Integer PK (fixed 1); last_value Integer NOT NULL default 0. Invoice numbers render `INV-{last_value:06d}`.

### 2.2 Modified model file

- **`organization.py`** — add: `billing_phase` String(24) NOT NULL server_default 'free'; `trial_started_at` timestamptz nullable; `trial_ends_at` timestamptz nullable.
- **`__init__.py`** — import and export the 6 new models.

### 2.3 Services — new package `apps/platform-api/app/services/billing/` (4 modules + `__init__.py`)

- **`pricing.py`** (pure, no DB): `TIER_SPECS` dict (flat_price_etb: starter 4500, scale 10000, enterprise 45000; billing_cycle monthly/quarterly; included_units per metric; overage_rate_etb per metric; trial_duration_hours=168); `flat_price_etb(tier)`, `billing_cycle_for(tier)`, `included_units(tier, metric)`, `overage_rate_etb(tier, metric)`, `period_for_tier(tier, anchor) -> (start, end)`, `next_period_start_after(anchor, cycle)`, `trial_period(start, 168)`, `grace_days_for(invoice_ordinal) -> 3|0`.
- **`invoices.py`** (imports models, pricing, audit): `issue_first_invoice(db, org, now)`, `issue_next_invoice(db, org, now)`, `try_issue_invoice(db, org, now) -> Invoice|None` (IntegrityError → rollback → re-read), `next_invoice_number(db)`, `designate_account(db, org, ordinal)`, `list_invoices(db, org)`, `get_invoice(db, org, invoice_number)`, `_trial_overage(db, org, tier, start, end)`, `_build_warning_notification(db, invoice, now)` (NB-05.2 fields; expires_at = now+3d).
- **`lifecycle.py`** (imports models, pricing, invoices): `derive_phase(db, org, now)` — PURE derivation, no side effects; `refresh_workspace_state(db, org, now)` — try_issue_invoice + derive + persist org.billing_phase; `start_trial(db, org, tier, now) -> TrialRecord|None`; `end_current_trial(db, org, now)`; `apply_tier_selection(db, org, tier, now) -> SubscriptionRead` (audit `subscription.tier_selected` with payload {from_tier, to_tier, trial_started, trial_ends_at, billing_phase}); `banner_for(state) -> dict` (single source of copy: limbo → "Your trial has ended. Your first invoice is due on {period_start} — once paid, your workspace resumes."; grace → "Grace period: {days} days remaining"; hard_locked → None; else None); `next_billing_period_start(org, now)`.
- **`locks.py`** (imports lifecycle): `WRITE_DISABLED_PHASES = frozenset({LIMBO, GRACE, HARD_LOCKED})`; `GRACE_WRITES_ENABLED = False`; `assert_workspace_writable(db, membership, now)` raises `WorkspaceLockedError`; `class WorkspaceLockedError(Exception)` carrying WorkspaceState.
- **`__init__.py`** — re-export public functions.

### 2.4 Schemas

- **`app/schemas/billing.py`** (new): `WorkspacePhase(StrEnum)` FREE/TRIAL/LIMBO/ACTIVE/GRACE/HARD_LOCKED; `BillingCycle(StrEnum)` MONTHLY/QUARTERLY; `DesignatedAccountRead` (bank_name, bank_code, account_holder, account_number); `InvoiceLineRead` (kind, description, quantity, unit_price_etb, amount_etb); `SubscriptionInvoiceRead` (invoice_number, tier, period_start, period_end, flat_amount_etb, total_etb, balance_remaining_etb, due_date, grace_days, grace_ends_at, status, lines, designated_account); `WorkspaceStateRead` (phase, can_write, billing_visible, banner_message, due_date, days_remaining, trial_ends_at, next_billing_period_start) — `billing_visible = (org invoice count > 0)`; `NotificationRead` (id, kind, title, message, payload, expires_at, dismissed_at).
- **`app/schemas/subscription.py`** (extend additive): `PlanRead` + flat_price_etb, billing_cycle, overage_unit_price_etb; `SubscriptionRead` + billing_phase, trial_ends_at, next_billing_period_start.
- **`app/schemas/auth.py`** (extend): `SubscriptionTier` + FREE='free'.

### 2.5 Endpoints

- **`app/api/endpoints/billing.py`** (new, prefix `/billing`, behind `get_current_membership`): `GET /billing/invoices`; `GET /billing/invoices/{invoice_number}` (404 if not found/not org's; free org → []/404); `GET /billing/state` (calls `lifecycle.refresh_workspace_state`).
- **`app/api/endpoints/notifications.py`** (new, prefix `/notifications`, behind `get_current_membership`): `GET /notifications`; `POST /notifications/{id}/dismiss` (sets dismissed_at; **409 while now < expires_at** per NB-05.3). Exempt from write guard.
- **`app/api/endpoints/subscriptions.py`** (modified): `GET /plans` rebuild from `pricing.TIER_SPECS` + keep USD fields + add Free row (tier='free', flat 0, quotas 2500/50, overage None); keep module-level `PLAN_QUOTAS` and ADD 'free' entry; `GET /me` extended via refresh_workspace_state; `POST /select-tier` → `lifecycle.apply_tier_selection`, same gate, EXEMPT from write guard; `POST /usage/record` + write guard.
- **`app/api/security.py`** (modified): add `require_writable_workspace` dependency (see §5).
- **`app/api/router.py`** (modified): register billing + notifications routers.
- **14 guarded endpoint files** add `Depends(require_writable_workspace)` to write endpoints: routes (POST /optimize), ingestion (5 CSVs + telematics + iot-telemetry), alerts (POST, scan, ack, resolve, auto-resolve), planning (generate, approve, reject), shipments (POST, status), warehouses (POST, PATCH), items (POST, PATCH), inventory (PUT), orders (POST), providers (POST keys, revoke, test, preference), forecast (POST weekly-demand), ops (POST live-eta), invoices (POST upload), subscriptions (usage/record). EXEMPT: all auth, select-tier, notifications, feedback POST, all GETs.

### 2.6 Migration

**`alembic/versions/20260805_0013_cashflow_phase1.py`** (down_revision '20260803_0012'):
- Create 6 tables with constraints per §2.1; seed `billing_counters` (id=1, last_value=0).
- `ALTER TABLE organizations` add billing_phase + trial_started_at + trial_ends_at.
- Seed CBE + Dashen collection accounts (values from `app/core/config.py` env fields if present, else placeholder constants — flag in docstring).
- Backfill existing orgs: 'trialing' → trial + TrialRecord(now, now+168h); 'active' → active; 'past_due' → hard_locked; 'canceled' → free. No fabricated invoices.

### 2.7 Tests — 6 new files + conftest + 3 updated (see §7)

## 3. Strict Import Map (models → schemas ↔ services → api; no cycles)

- New model files import only: `app.db.base`, `app.models.common`, `app.db.custom_types`, sqlalchemy (FKs by string reference).
- `app.models.__init__` imports all models (top of DAG).
- `schemas.billing` → `schemas.auth`; `schemas.subscription` → `schemas.billing` + `schemas.auth`; `schemas.auth` → nothing app-internal.
- `services.billing.pricing` → no app imports. `invoices` → models + pricing + audit. `lifecycle` → models + pricing + invoices + schemas.billing. `locks` → lifecycle + schemas.billing. `__init__` → 4 modules.
- `api.security` → + `from app.services.billing import locks` (+ WorkspacePhase). **services.billing never imports app.api.** 
- `api.endpoints.subscriptions` → + lifecycle, locks, pricing, BillingCycle. `billing.py` → security.get_current_membership, models, schemas.billing, lifecycle. `notifications.py` → security, models, schemas.
- Guarded endpoint files → + `require_writable_workspace` from security.
- `core/config.py` → optional env: cbe_account_holder, cbe_account_number, dashen_account_holder, dashen_account_number (defaults empty).
- Tests → billing services/models + conftest; `conftest.py` adds `import app.models  # noqa: F401` and autouse `seed_collection_accounts` fixture.

## 4. Module-boundary justification

`pricing.py` (pure constants/math, zero DB) → `invoices.py` (persistence + composition) → `lifecycle.py` (state engine, all phase-transition rules) → `locks.py` (enforcement policy + exception). One-directional chain; HTTP stays out of the state engine; pricing stays DB-free. Phase 4 free-cap lock will reuse `locks.assert_workspace_writable`.

## 5. Lock enforcement strategy (TECH-06)

`require_writable_workspace(membership = Depends(get_current_membership), db = Depends(get_db)) -> OrganizationMembership`:
1. Membership None → pass through (preserves org-less write contract: test_rbac_endpoints, test_route_optimization_without_membership).
2. Else load org, `locks.assert_workspace_writable` (runs refresh_workspace_state incl. lazy issuance); raise on phase ∈ {limbo, grace, hard_locked}.
3. Convert to `HTTPException(423 Locked)` with `detail = {"state": phase.value, "message": banner_message, "days_remaining": days_remaining, "can_write": False}`.
4. Phases free/trial/active → return membership unchanged (existing behavior preserved).

## 6. Sequencing (TDD order)

1. Models + migration + conftest (test_billing_models.py). `alembic upgrade head` verified.
2. `pricing.py` + test_billing_pricing.py.
3. `lifecycle.py` derivation half + test_billing_lifecycle.py (pure parts first).
4. `invoices.py` + test_billing_invoices.py.
5. `locks.py` + guard in security.py + test_billing_lock_guard.py; wire 32 endpoints one file at a time, run each file's existing tests after wiring.
6. API surface: billing.py, notifications.py, subscriptions.py, router.py, schemas; test_billing_api.py.
7. Repair existing tests (§7.3); full suite.
8. Full-suite + alembic upgrade head + manual smoke.

## 7. Testing requirements (named test functions)

### 7.1 conftest.py (modify)
`import app.models  # noqa: F401`; autouse `seed_collection_accounts(db_session)` inserting CBE + Dashen rows.

### 7.2 New test files

**test_billing_models.py:** `test_collection_accounts_check_constraint_rejects_unknown_bank`; `test_subscription_invoice_org_period_unique`; `test_trial_record_org_tier_unique`; `test_seed_collection_accounts_present`.

**test_billing_pricing.py:** `test_flat_prices_locked` (4500/10000/45000); `test_billing_cycles`; `test_monthly_period_math` (2026-08-05 → 08-01..08-31); `test_quarterly_period_math` (2026-08-05 → 07-01..09-30); `test_next_period_start_monthly` (08-05 → 09-01; 08-01 → 09-01); `test_next_period_start_quarterly` (08-05 → 10-01; 06-30 → 07-01); `test_grace_days_first_vs_subsequent`; `test_free_tier_quotas_no_overage`.

**test_billing_lifecycle.py:** `test_signup_org_starts_free_phase`; `test_first_upgrade_starts_168h_trial` (routes/optimize 200 during trial); `test_no_invoice_during_trial`; `test_retrial_same_tier_silently_blocked`; `test_second_tier_gets_own_trial`; `test_midtrial_switch_ends_previous_trial`; `test_limbo_after_trial_end` (423, banner contains "Your trial has ended. Your first invoice is due on"); `test_limbo_next_period_start_monthly` (08-15 → 09-01); `test_limbo_next_period_start_quarterly` (08-15 → 10-01); `test_refresh_issues_first_invoice_at_boundary` (phase grace, 3-day warning created); `test_grace_then_hard_lock`; `test_upgrade_during_grace_does_not_reset_grace`; `test_tier_switch_from_hard_lock_no_trial`.

**test_billing_invoices.py:** `test_first_invoice_starter_line_items` (flat 4500 + overage_delivery_tasks at 0.20); `test_first_invoice_scale_quarterly_period` (period upcoming quarter, flat 10000); `test_enterprise_invoice_never_has_overage_lines`; `test_invoice_designates_exactly_one_account`; `test_designation_rotates_per_org` (inv1 CBE, inv2 Dashen); `test_invoice_number_format_and_uniqueness` (INV-000001); `test_at_most_one_invoice_per_period`; `test_first_invoice_grace_3_subsequent_0`; `test_warning_notification_fields` (expires = issuance + 3d); `test_issue_records_audit_event` (`billing.invoice_issued`).

**test_billing_lock_guard.py:** `test_write_blocked_in_limbo` (423, state limbo, limbo banner); `test_write_blocked_in_grace_with_days_remaining`; `test_write_blocked_in_hard_lock`; `test_reads_always_available` (GETs 200 during hard_locked); `test_auth_endpoints_exempt`; `test_select_tier_exempt_and_non_resetting`; `test_usage_record_guarded`; `test_no_membership_passthrough` (201 preserved); `test_trial_and_free_phases_unaffected`.

**test_billing_api.py:** `test_plan_catalog_etb_prices` (incl. free row); `test_me_returns_billing_phase_and_trial`; `test_state_free_org_no_billing_surface`; `test_state_grace_banner`; `test_invoice_list_and_detail_include_designated_account`; `test_notifications_list_and_dismiss_window` (dismiss before expiry → 409; after → 200).

### 7.3 Updated existing tests (flagged breakage)
- `test_subscription_metering_api.py`: `_signup_company` helper — after signup (free), call select-tier before recording usage; assertions unchanged.
- `test_route_usage_metering_api.py`: `_company_signup_token` — same select-tier step; `test_route_optimization_without_membership_does_not_fail` untouched.
- `test_company_onboarding_api.py`: signup asserts `subscription_tier == 'free'`; select-tier asserts tier + `status == 'trialing'` + `billing_phase == 'trial'`; provider-key steps remain green (trial = full write).

## 8. Explicit NON-GOALS (Phase 1 must NOT do)

No receipt upload/extraction/verification queue (Phase 2). No wallet credit / tolerance (TECH-09). No audit-verification records / undo / reverse (TECH-18..21). No SMS / escalation / disputes (TECH-16,17). No balance_remaining mutation path (Phase 2 credits). No free-tier cap hard lock (Phase 4). No ops-console banner rendering (API contract only). No collection-account admin CRUD UI. No scheduler. No changes to metering.current_usage_window or PLAN_QUOTAS semantics for existing paid tiers. No removal of USD fields from PlanRead. No changes to SubscriptionStatus enum.

## 9. Risks flagged on the existing code

1. graphify not installed / GRAPH_REPORT.md absent — mapping via Read/Grep. Install before Phase 2.
2. Signup-tier echo tested today — 3 existing tests MUST be updated or CI fails (deliberate behavior change per behavior doc).
3. Org-less write calls are a tested contract — guard must pass through when membership None (fail-open safe: no org → no workspace state).
4. `Organization` defaults are starter/trialing — signup endpoint is only live creator today; every new org must be explicitly free/active.
5. No scheduler — lazy issuance is only viable Phase-1 mechanism; at-most-once via unique constraint.
6. NB-06 §5.6 vs NB-06.3 grace contradiction — ADJUDICATED: acceptance criteria wins (write-disabled grace), toggle `GRACE_WRITES_ENABLED`.
7. Metering windows are calendar-month; Scale/Enterprise bill quarterly — invoice overage uses decision-#6 aggregation; do NOT fix metering in this phase.
8. `select_tier` semantic change (`active` → `trialing` during 7-day trial) — extended SubscriptionRead (billing_phase, trial_ends_at) is the console migration contract.
9. Money float discipline — Decimal/Numeric(14,2) end-to-end or ETB rounding errors surface in invoices.
