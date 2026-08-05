# BLUEPRINT: PHASE 4 — Activation: Sample Seeding, Milestones, Progressive Reveal & Free-Cap Lock (TECH-25..35 / NB-25..35)

Status: LOCKED for execution by @build on branch `feat/market-contender-v1`. Written by @plan. QA audits against this document AND the NB acceptance criteria in `docs/behaviors/pending-behaviors.md` (lines 244-359) AND `docs/behaviors/operator-activation-and-milestone-tracking.md` (full). Builds ON TOP of Phase 1 (`6715f88`), Phase 2 (`179eeda`), Phase 3 (`fd5b69c`) outputs — no re-design of existing infrastructure; only the additive integration points listed below are touched. Migration head confirmed: `20260806_0015` → Phase 4 migration is `20260806_0016`. *Note: the graphify CLI is not installed in this environment (verified); the import map in §4 was grounded by direct module reads of every edge file (services/billing/*, services/metering.py, services/audit.py, api/security.py, api/endpoints/{auth,ingestion,routes,subscriptions,billing}.py, models/*, ops-console src).*

## 0. Goal

Turn the signup-to-value journey into a guided, metered loop: every new workspace is auto-seeded from `sample-data/` CSVs (per-workspace, audit-recorded), a persistent non-dismissible demo/onboarding banner drives the N-of-5 replacement flow, a six-milestone per-organization activation state gates progressive dashboard reveal (with hidden-or-placeholder panel modes), Free-tier writes hard-lock at 2,500 delivery_tasks OR 50 route_optimizations with an escalating 60/80/100% pitch ladder that never leaves the console, a one-time soft post-aha toast fires at milestone 6, every login lands on `/dashboard`, and an admin-gated typed-confirmation workspace reset restores the seeded state.

## 0A. @architect adjudication — 2026-08-05 (BLUEPRINT AMENDMENT, supersedes conflicting text)

**Context:** During TDD setup @build proved a schema-level blocker: `warehouses.code`, `items.sku`, `fleet_assets.vehicle_code` carry GLOBAL unique constraints (`unique=True` + DB unique indexes `ix_warehouses_code` / `ix_items_sku` from migration `0001`, `ix_fleet_assets_vehicle_code` from `0005`; migration `0011` added `organization_id` without dropping them). Decision #3 (identical per-workspace seeding) + decision #13 (org-scoped upsert by business key) are mutually contradictory with global uniqueness: the second org to sign up would IntegrityError on WH-001/SKU-001/TRUCK-1001, and org B's real upload of WH-001 would fail the same way. SIGNED OFF:

1. **Multi-tenant business-key uniqueness (APPROVED):** drop `unique=True` from `warehouses.code`, `items.sku`, `fleet_assets.vehicle_code` in the models; add composite `UniqueConstraint('organization_id','code')` / `('organization_id','sku')` / `('organization_id','vehicle_code')` via `__table_args__` (`UniqueConstraint` joins the existing sqlalchemy import line). NULL-org legacy rows remain allowed (NULLs are distinct under both Postgres and sqlite unique semantics). `fleet_assets.organization_id` is added by this phase's migration (already per decision #2) — the composite unique goes in the same migration. Migration `20260806_0016` in BOTH dialects: `op.drop_index('ix_warehouses_code')` + `op.create_index('ix_warehouses_org_code', 'warehouses', ['organization_id','code'], unique=True)` (same for `ix_items_sku`→`ix_items_org_sku`, `ix_fleet_assets_vehicle_code`→`ix_fleet_assets_org_vehicle_code`). Plain CREATE/DROP INDEX — no batch table-rebuild, so the sqlite-quirk precedent does NOT apply. Downgrade reverses.
2. **Observation (verify, extend if needed):** `shipments.shipment_no` is also global-unique (`ix_shipments_shipment_no`, migration `0003`). Shipments are NOT in the seeded set and NOT created by the 5 upload handlers today. If Phase 4's work proves any upload or seeding path creates Shipment rows from user-supplied `shipment_no`, apply the SAME composite-unique treatment in this migration. If not, record as a follow-up TECH ticket for a later batch (do not silently leave the hazard undocumented).
3. **TECH-48 (folded into Phase 4):** Two pre-existing Phase 1 tests are timezone-fragile and fail on machines where local date (UTC+3) is ahead of UTC date: `test_billing_api.py::test_state_grace_banner` and `test_billing_lock_guard.py::test_write_blocked_in_grace_with_days_remaining` (both inject `grace_ends_at = date.today() + timedelta(days=1)` with local `date.today()` while production derives days from UTC). Fix: change the two fixtures to use UTC dates (`datetime.now(UTC).date()`), restoring a deterministic green baseline. Production grace math is NOT touched (Phase 1 immutable). Documented in the Phase 4 commit message.

## 1. Ground-truth decisions (locked for @build; deviations require @architect sign-off)

1. **Activation state lives in a NEW 1:1 table `organization_activation_state`, NOT columns on `organizations`.** The `organizations` row is committed by `lifecycle.refresh_workspace_state` on every guard evaluation; activation state is a separately evolving aggregate (m6 timestamp, toast flag, seeded_at). Columns: `organization_id` (UNIQUE FK CASCADE), `m6_completed_at` DateTime(tz) NULL, `toast_fired_at` DateTime(tz) NULL, `seeded_at` DateTime(tz) NULL. **Milestones 1–5 are NOT stored — they are DERIVED** at read time: category C is complete iff ≥1 row exists with `organization_id = :org AND data_origin='real'` (indexed existence query per category). Only milestone 6 is stored (route optimization runs write no data table). Rationale: reset (NB-35) deletes real rows → milestones 1-5 reset automatically with zero drift; no stored flag can go stale. N-of-5 = length of the completed PREFIX [warehouses, items, fleet_assets, inventory, orders] — sequential rule (doc §4 "must complete milestone N before N+1 registers") means out-of-order uploads do not register (an org that uploads only orders is still 0 of 5).
2. **`data_origin` = a column on all 5 data tables, NOT a flag table.** `data_origin VARCHAR(8) NOT NULL DEFAULT 'real'` + CHECK `IN ('sample','real')` on `warehouses`, `items`, `fleet_assets`, `inventory`, `historical_orders` (Postgres-only CHECK per sqlite precedent). Seed rows are inserted with `data_origin='sample'` + `organization_id=org`; uploads insert/update with `data_origin='real'` + `organization_id=org`. **`fleet_assets` currently LACKS `organization_id`** — migration adds it (nullable, FK `organizations.id` ON DELETE SET NULL, indexed); pre-existing org-less fleet rows stay NULL and are invisible to activation counts (legacy rows; no backfill).
3. **Upload semantics: UPSERT-by-key, and sample rows are SUPERSEDED (deleted) on category upload — never "append both".** The existing endpoints upsert on business key (code/sku/vehicle_code/(warehouse,item)). Locked supersede rule, executed in the SAME transaction after the real upserts: delete org-scoped `data_origin='sample'` rows of the uploaded category EXCEPT sample rows still referenced by real rows of a downstream table (sample warehouses referenced by real `inventory`/`historical_orders` rows are kept — otherwise the real row dangles against a NOT NULL FK; they are deleted when that downstream category later turns real, at which point no real row references them). Sample `inventory`/`historical_orders` rows referencing a sample warehouse/item deleted in the same operation are explicitly deleted (org-scoped) in the same transaction. Deterministic, monotonic, no real-row loss, no FK violation. N-of-5 is unaffected by surviving sample rows (it counts real-presence only).
4. **Metering NEVER differentiates (NB-27.2/4) — `services/metering.py` is untouched.** Origin tagging is an AUDIT concern only: the `route.optimized` audit payload gains `data_origin` = `'real'` iff the start warehouse AND every delivery-target warehouse row used in the run exist with `data_origin='real'`, else `'sample'` (a run touching any sample warehouse is a sample-substrate run). Uploads gain a NEW audit event `workspace.csv_uploaded` with `{category, data_origin:'real', records_processed/created/updated, errors}` (uploads today write NO audit trail — gap-fill for NB-28 traceability).
5. **NB-31 free-cap lock COMPOSES with the Phase 1 phase lock inside the SAME `require_writable_workspace` dependency — one guard chain, zero per-endpoint edits.** `locks.assert_workspace_writable` keeps the phase check, then evaluates the new meter gate. `can_write = phase not in WRITE_DISABLED_PHASES AND NOT free_cap_locked`. The disabled-operation list (NB-31.2) is EXACTLY the 32 endpoints already declaring `require_writable_workspace` (route optimize, 5 CSV uploads, alert ack/resolve/manual-create, replenishment approve/reject, shipment create/update, provider key set/change, forecast). The available list (NB-31.3) is exactly the read endpoints without the guard. **Exempt carve-outs preserved**: `POST /subscriptions/select-tier` (upgrade is the ONLY way out of the cap — NB-31.4) and the Phase 2/3 receipt + reversal endpoints (cashflow servicing, already documented write-guard exempt) stay unguarded. `free_cap_locked = org.subscription_tier=='free' AND (delivery_tasks used_units ≥ pricing.included_units('free','delivery_tasks') OR route_optimizations used_units ≥ pricing.included_units('free','route_optimizations'))` where used_units is read from `organization_usage_counters` for the CURRENT month window (via `metering.current_usage_window(now.date())`). **Auto-lift at month rollover is FREE**: the window derives lazily from `now` exactly like Phase 1 phase derivation — no cron, no scheduler. The 423 detail gains `free_cap_locked` + `free_cap_message`; banner priority when BOTH locks hold: the Phase invoice banner (limbo/grace/hard_locked) wins — unpaid debt is the stronger commercial state; the free-cap banner re-surfaces when the phase resolves.
6. **Pitch thresholds (60/80/100%) persist in a NEW table `threshold_crossings`, fire-once-per-threshold-per-month.** Columns: `organization_id` FK CASCADE, `period_start` DATE, `threshold_level` VARCHAR(8) IN ('p60','p80'), `fired_at` TIMESTAMPTZ NOT NULL, `dismissed_at` TIMESTAMPTZ NULL; UNIQUE(organization_id, period_start, threshold_level). Utilization = `max(pct_delivery_tasks, pct_route_optimizations)` (the meter that locks first drives the pitch). At every activation-state read, the service crosses (INSERT) any threshold ≤ current utilization not yet crossed this period and includes `pitch_fired: [...]` in the payload; the console renders the banner from fired-crossings. **p100 is NOT a crossing row — it IS the free-cap lock state itself** (NB-32.3: the 100% banner supersedes 80%; NB-31.6 copy is the same banner). Banner stack: p100 > p80 > p60; p60 dismissible (`POST /activation/pitch-dismiss {level:'p60'}` sets dismissed_at; row is per-period so a new month re-fires); p80/p100 non-dismissible. Crossings are cleared by reset (NB-35).
7. **Milestone 6 = the org's FIRST route optimization run, any data substrate, no prefix requirement (NB-28.4 + NB-33.5 win over doc §4's "sequential" prose).** Registered in the optimize endpoint transaction: if `m6_completed_at IS NULL` → set it + `toast_fired_at` + audit `activation.milestone_6_completed` `{first_route_optimization_run_id, data_origin}`; the optimize RESPONSE gains `post_aha_toast: true` exactly on that first transition (console shows the one-time toast; NB-33.3 auto-dismiss). Subsequent runs: no re-fire (server truth).
8. **Banner visibility and copy — reconciled across NB-26.6 / NB-34 / doc §4:** the activation banner renders whenever `m6_completed_at IS NULL`; the COPY is state-driven: N<5 → demo copy ("Welcome back. You're {N*20}% through onboarding — {5-N} steps remaining ({next categories}). Continue setup." CTA `/upload`); N=5 → "Welcome back. You're 80% through onboarding — run your first route optimization to complete setup." CTA `/routes` (this is the NB-34.3 banner that keeps NB-26.6's "demo banner disappears at 5-of-5" true — the demo MESSAGING disappears, the onboarding banner persists until m6); m6 → no banner at all. NB-26's literal "You're viewing a demo workspace… N of 5 categories is yours" copy renders on the `/upload` full checklist (per-category sample/real/empty chips — NB-30.5). One component, one state source, two render densities (NB-30).
9. **`/dashboard` landing (NB-34.1) needs NO new guard** — `App.tsx` already routes `/` → `DashboardPage` under `ProtectedRoute` with `*` → `/` fallback, and no login path redirects to `/upload` or `/routes`. The blueprint adds a regression test asserting the route table + post-login redirect target stays `/`; no redirect logic changes.
10. **Workspace reset (NB-35) semantics:** `POST /activation/reset`, gated `require_org_roles(OWNER, ADMIN)`, body `{workspace_name: str}` — server compares against `org.name` EXACTLY (trimmed, case-sensitive) → 422 on mismatch. On match, one transaction: (a) delete ALL org-scoped rows of all 5 categories (orders → inventory → fleet → items → warehouses; CASCADE covers references), (b) re-seed sample rows from `sample-data/`, (c) reset activation state (`m6_completed_at=NULL`, `toast_fired_at=NULL`, `seeded_at=now`), (d) DELETE threshold_crossings for the org, (e) audit `workspace.reset_to_sample_data` `{workspace_name, categories, rows_reseeded}` with admin user + timestamp (NB-35.5, visible in audit timeline). Re-login flow (NB-35.7): the console, on 200, clears auth state + calls the existing `POST /auth/logout` cookie-clear, then redirects to `/login`; after re-login the default landing `/` renders the 0% banner. **No server-side token invalidation exists** (stateless JWTs, no blacklist — consistent with the existing auth design); document in the endpoint docstring. No keyboard shortcut, no light confirm — typed confirmation only (NB-35.6).
11. **`sample-data/` CSVs VERIFIED present** with exactly the 5 categories and headers matching the ingestion contract: `warehouses.csv` (code,name,address,city,state,country,latitude,longitude,capacity_units), `items.csv` (sku,name,category,unit_cost,reorder_level,temperature_threshold), `fleet_assets.csv` (vehicle_code,driver_name,driver_contact,capacity_units,status), `inventory.csv` (warehouse_code,sku,quantity_on_hand,safety_stock), `orders.csv` (order_date,warehouse_code,sku,quantity,unit_price,customer_region,weather_avg_temp_c,weather_precip_mm,weather_disruption_index). No fixture CSVs need to be shipped; the seeding service reads these files at runtime from `settings.sample_data_dir` (default `'sample-data'`, repo-root-relative).
12. **The `route_optimizations` meter is today NEVER recorded** — `routes.py` only records `delivery_tasks` (units = len(deliveries)). NB-31.1 requires BOTH meters to be able to hit the cap. Gap-fill locked: the optimize endpoint additionally records `record_usage_for_user_membership(db, user=actor, metric='route_optimizations', units=1)` per run.
13. **Ingestion endpoints must become org-scoped** — today lookups are global (`WHERE code == ...` with no `organization_id`), which would let org A's upload update org B's seeded WH-001. All 5 upload handlers scope lookups by `writable.organization_id` and stamp `organization_id` + `data_origin='real'` on every insert/update. This is a correctness prerequisite for per-workspace seeding (NB-25.3).

## 2. Files to CREATE

All paths relative to repo root. Backend under `apps/platform-api/app/`, tests under `apps/platform-api/tests/`, console under `apps/ops-console/src/`.

### 2.1 Model — `apps/platform-api/app/models/activation_state.py` (NEW, ~50 lines)

`OrganizationActivationState` (table `organization_activation_state`) — 1:1 with organizations (decision #1). Columns: `id` (UUIDTimestampMixin), `organization_id` UUIDType FK `organizations.id` CASCADE NOT NULL UNIQUE indexed, `m6_completed_at` DateTime(tz) NULL, `toast_fired_at` DateTime(tz) NULL, `seeded_at` DateTime(tz) NULL, `created_at`. Imports ONLY `app.db.base`, `app.db.custom_types`, `app.models.common`, sqlalchemy. NOTE: `UUIDTimestampMixin` provides `updated_at` with onupdate — verified pattern in `models/usage_meter.py`.

### 2.2 Model — `apps/platform-api/app/models/threshold_crossing.py` (NEW, ~45 lines)

`ThresholdCrossing` (table `threshold_crossings`) — decision #6. Columns: `id`, `organization_id` FK CASCADE NOT NULL indexed, `period_start` Date NOT NULL, `threshold_level` String(8) NOT NULL, `fired_at` DateTime(tz) NOT NULL, `dismissed_at` DateTime(tz) NULL, `created_at`; `UniqueConstraint('organization_id','period_start','threshold_level', name='uq_threshold_crossing_org_period_level')`; CheckConstraint `threshold_level IN ('p60','p80')` (model-level; Postgres-only in migration).

### 2.3 Service package — `apps/platform-api/app/services/activation/` (NEW; 6 modules, every module ≤200 lines — comfortably under the 400 hard cap; a SIBLING of `services/billing/`, NOT inside it: activation reads billing state but is the product-facing onboarding engine, and billing must never import activation — keeps the billing DAG acyclic)

**`__init__.py`** (~40 lines) — docstring stating the package contract (derived milestones 1-5, stored m6, lazy free-cap, pitch ladder, decisions #1/#5/#6/#7) + re-exports: `ActivationStateRead`, `activation_state_read`, `seed_workspace`, `supersede_sample_rows`, `record_csv_upload`, `record_route_optimization`, `reset_workspace`, `free_cap_state`, `pitch_state`, `dismiss_pitch`, `FreeCapLockedError`.

**`state.py`** (~190 lines; imports models, schemas.activation, services.audit, services.metering, services.billing.lifecycle) —
- `CATEGORIES: tuple[str, ...] = ('warehouses','items','fleet_assets','inventory','orders')` (ordered; the milestone order).
- `CATEGORY_META: dict[str, dict]` — label + model class + real-existence query per category (e.g. `warehouses → Warehouse`, predicate `Warehouse.organization_id==org.id, Warehouse.data_origin=='real'`).
- `_real_rows_exist(db, org_id, category) -> bool` — indexed `EXISTS` select, one per category.
- `completed_prefix(db, org_id) -> int` — longest prefix of CATEGORIES with `_real_rows_exist` True (decision #1).
- `next_step(prefix: int) -> dict | None` — `{category, label, cta: '/upload'}` for the first incomplete category; None at prefix 5.
- `_ensure_state_row(db, org_id) -> OrganizationActivationState` — get-or-create (defensive; seeding creates it, but guard reads before seeding in tests).
- `record_csv_upload(db, org_id, actor, *, category, counts: dict, now) -> None` — audit `workspace.csv_uploaded` `{category, data_origin:'real', records_processed, records_created, records_updated, errors}` (decision #4). NO milestone writes (derived).
- `record_route_optimization(db, org_id, run_id, *, data_origin, now) -> bool` — returns True iff this was the FIRST optimization (m6 transition): sets `m6_completed_at` + `toast_fired_at` on the state row, audit `activation.milestone_6_completed` `{first_route_optimization_run_id, data_origin}`; False if m6 already set. Commit-aware: caller commits.
- `activation_state_read(db, org, now) -> ActivationStateRead` — full composition: prefix/N-of-5, per-category `{real_rows, sample_rows, status: 'real'|'sample'|'empty'}`, `m6_completed`/`m6_completed_at`, `pct = min(prefix*20, 80)`, `next_step`, `free_cap = free_cap_state(...)`, `pitch = pitch_state(...)` (fires crossings), `toast_fired` flag.

**`seeding.py`** (~160 lines; imports models for all 5 tables, pandas, settings, services.audit, activation.state) —
- `_load_csv_rows(category) -> list[dict]` — `pd.read_csv(Path(settings.sample_data_dir) / f'{category}.csv')`, row→dict with the exact column mapping used by the ingestion handlers (verify against `sample-data/` headers, decision #11); `temperature_threshold`/`driver_contact`/`status`/weather columns optional-absent-safe.
- `seed_workspace(db, org, actor, *, force=False, now) -> SeedResult` — idempotent: if `force=False` and the org already has a state row with `seeded_at` set (or any sample row), return `{'skipped': True}`. Inserts in FK order warehouses → items → fleet_assets → inventory → orders, each row `organization_id=org.id, data_origin='sample'`; creates the activation state row (`seeded_at=now`); audit `workspace.seeded_sample_data` `{categories: [...], rows_per_category: {...}}` with actor=signup user (NB-25.4). Returns `{rows_per_category}`. `force=True` (reset path) skips the idempotency check — the caller has already wiped the org's rows.
- `supersede_sample_rows(db, org, category, now) -> int` — decision #3: delete org-scoped `data_origin='sample'` rows of `category` not referenced by real downstream rows; for warehouses/items additionally delete org-scoped sample `inventory`/`historical_orders` rows whose warehouse/item was deleted in this operation (explicit, org-scoped). Returns deleted count. Called by the upload endpoints in the SAME transaction as the upserts.

**`freecap.py`** (~120 lines; imports models.usage_meter, models.organization, services.metering, services.billing.pricing) —
- `class FreeCapLockedError(Exception)` — `(state: FreeCapState)` mirror of `WorkspaceLockedError`.
- `free_cap_state(db, org, now) -> FreeCapState` — pure lazy derivation (decision #5): `period_start/end = metering.current_usage_window(now.date())`; read both `OrganizationUsageCounter` rows; `included = pricing.included_units(tier, metric)`; `used = counter.used_units or 0`; `pct = round(used/included*100)` per metric (None when no cap); `utilization_pct = max(pcts)`; `locked = org.subscription_tier=='free' and (dt_used >= dt_included or ro_used >= ro_included)` — `included_units` from `pricing` (single source of truth; NOT `subscriptions.PLAN_QUOTAS`). NO writes.
- `assert_free_cap_writable(db, org, now) -> FreeCapState` — raise `FreeCapLockedError` when locked; return state otherwise.
- `pitch_state(db, org, now) -> PitchState` — decision #6: compute `utilization_pct`; cross (INSERT) `p60` when pct ≥ 60 and no row for (org, period_start, 'p60'), `p80` when pct ≥ 80 (audit `usage.pitch_fired` `{level, period_start, utilization_pct}` per crossing); `pitch_banner = 'p100' if locked else ('p80' if crossed-not-dismissed else ('p60' if crossed and dismissed_at IS NULL else None))` — p60 respects `dismissed_at`; p80/p100 never dismiss. Returns the payload fragment.
- `dismiss_pitch(db, org, level, now) -> None` — sets `dismissed_at` on the current-period row; 404 when no crossing row exists (p60 only from the console).

**`reset.py`** (~130 lines; imports models (all 5), activation.seeding + state, services.audit) —
- `reset_workspace(db, org, admin_user, workspace_name, now) -> ResetResult` — verify `workspace_name.strip() == org.name` else raise `ResetError(422, ...)`; one transaction: (1) delete org-scoped rows in reverse dependency order (`historical_orders`, `inventory`, `fleet_assets`, `items`, `warehouses` — order matters for CASCADE hygiene), (2) `seeding.seed_workspace(db, org, admin_user, force=True)`, (3) state row: `m6_completed_at=NULL, toast_fired_at=NULL, seeded_at=now`, (4) `DELETE FROM threshold_crossings WHERE organization_id=:org`, (5) audit `workspace.reset_to_sample_data` `{workspace_name, categories: [...], rows_reseeded}` (decision #10). Returns `{rows_reseeded}`.

**`banner.py`** (~90 lines; imports activation.state + freecap) —
- `activation_banner_payload(db, org, now) -> dict` — the single payload both console pages render (decision #8): `{visible, n_of_5, pct, next_step, cta, demo_mode (n_of_5 < 5), free_cap: {locked, utilization_pct, message}, pitch: {banner: 'p100'|'p80'|'p60'|None, fired: [...], dismissible: bool}, toast_fired}`. NB-30.1 single-source guarantee.

### 2.4 Schemas — `apps/platform-api/app/schemas/activation.py` (NEW, ~90 lines; pydantic only, standalone rule)

- `CategoryMilestoneRead` — `{category, label, status: 'real'|'sample'|'empty', real_rows: int, sample_rows: int, completed: bool}`.
- `ActivationStateRead` — `{organization_id, n_of_5: int, pct_complete: int, milestones: list[CategoryMilestoneRead], m6_completed: bool, m6_completed_at: datetime|None, next_step: {category,label,cta}|None, banner: dict, free_cap: dict, pitch: dict, toast_fired: bool}` (payload shapes in §6).
- `ResetWorkspaceRequest` — `{workspace_name: str = Field(min_length=1, max_length=128)}` + whitespace-only rejector.
- `ResetWorkspaceResult` — `{rows_reseeded: dict[str,int], activation_reset: bool}`.
- `PitchDismissRequest` — `{level: Literal['p60']}` (only p60 dismissible — server rejects anything else with 422).

### 2.5 Endpoints — `apps/platform-api/app/api/endpoints/activation.py` (NEW, ~150 lines; router prefix `/activation`)

- `GET /activation` — `get_current_membership` → `ActivationStateRead`: `activation_state_read(db, org, now)` (fires pitch crossings; NB-30.4 consumers poll via react-query invalidation).
- `POST /activation/reset` — `require_org_roles(OWNER, ADMIN)` + `ResetWorkspaceRequest` → `ResetWorkspaceResult`; `ResetError → 422`; success does NOT clear cookies server-side (decision #10 — console performs the logout).
- `POST /activation/pitch-dismiss` — `require_org_roles(OWNER, ADMIN, OPERATOR)` + `PitchDismissRequest` → `{dismissed: bool}`; non-'p60' level → 422.
- ALL THREE are write-guard EXEMPT by design: reads must work while locked, reset must work from a locked workspace, and pitch-dismiss is a read-adjacent UX action. Documented in the module docstring (receipts precedent).

### 2.6 Tests — 11 new backend files + console additions (§10 names every function)

`test_activation_models.py`, `test_activation_seeding.py`, `test_activation_milestones.py`, `test_activation_banner_state.py`, `test_activation_metering_origin.py`, `test_activation_panel_gating.py`, `test_activation_banner_shared.py`, `test_free_cap_lock.py`, `test_upgrade_pitch.py`, `test_activation_toast.py`, `test_activation_reset.py` + console `pages/ActivationBanner.test.tsx` (NEW) + `pages/workspaceSurfaces.smoke.test.tsx` (MODIFY).

## 3. Files to MODIFY

1. `apps/platform-api/app/models/fleet_asset.py` — add `organization_id` (UUIDType FK `organizations.id` ON DELETE SET NULL, nullable, indexed) + `data_origin` String(8) default 'real' + CheckConstraint. ~+8 lines.
2. `apps/platform-api/app/models/{warehouse,item,inventory,order}.py` — add `data_origin` String(8) NOT NULL default 'real' + CheckConstraint (`IN ('sample','real')`). No new imports.
3. `apps/platform-api/app/models/__init__.py` — export `OrganizationActivationState`, `ThresholdCrossing`.
4. `apps/platform-api/app/core/config.py` — add `sample_data_dir: str = 'sample-data'` (decision #11).
5. `apps/platform-api/app/services/billing/locks.py` — `assert_workspace_writable` composes the meter gate (decision #5): after the phase check passes, evaluate `activation.freecap.assert_free_cap_writable`; raise `FreeCapLockedError` → `WorkspaceLockedError`-shaped 423 with `free_cap_locked` + `free_cap_message` in the detail. Import `app.services.activation.freecap` (one-directional: billing.locks → activation.freecap → models/metering/pricing; activation NEVER imports billing.locks — acyclic by construction; note in docstring). ~+20 lines.
6. `apps/platform-api/app/api/security.py` — `require_writable_workspace` 423 detail dict gains `free_cap_locked` + `free_cap_message` when the raised error is `FreeCapLockedError` (catch both error types; `WorkspaceLockedError` path unchanged). ~+10 lines.
7. `apps/platform-api/app/api/endpoints/ingestion.py` — org-scope all 5 CSV handlers (decision #13): lookups filtered by `writable.organization_id`; inserts/updates stamped `organization_id` + `data_origin='real'`; after the upsert loop (before commit) call `activation.seeding.supersede_sample_rows(db, org, category)` + `activation.state.record_csv_upload(...)`. The per-handler upsert logic (row mapping + error capture) is extracted into `services/activation/ingest.py` helpers so this file stays ≤400 lines (357 + ~90 would exceed; extraction keeps it ~330). ~-80/+50 lines net.
8. `apps/platform-api/app/api/endpoints/routes.py` — optimize endpoint: (a) record the `route_optimizations` meter (decision #12), (b) compute `data_origin` for the run (decision #4: real iff start warehouse AND all stop warehouses real), add it to the `route.optimized` audit payload, (c) `record_route_optimization(db, org_id, run_id, data_origin=..., now)` and surface `post_aha_toast` in `RouteOptimizeResponse` (schema change, decision #7). ~+35 lines → ~330, stays under 400.
9. `apps/platform-api/app/schemas/route.py` — `RouteOptimizeResponse` gains `post_aha_toast: bool = False` + `data_origin: str | None = None`.
10. `apps/platform-api/app/schemas/ingestion.py` — `IngestionResult` unchanged (counts suffice); no change needed.
11. `apps/platform-api/app/api/router.py` — register `activation.router` with prefix `/activation`.
12. `apps/platform-api/app/services/metering.py` — UNTOUCHED (decision #4). The `route_optimizations` gap-fill is a CALL-SITE change in routes.py only.
13. `apps/platform-api/app/services/billing/lifecycle.py`, `invoices.py`, `pricing.py`, `subscriptions.py` — UNTOUCHED. `pricing.included_units` is the cap source of truth; `subscriptions.PLAN_QUOTAS` duplication is left as-is (Phase 1 surface, immutable).
14. Ops-console: `types/api.ts`, `services/activationApi.ts` (NEW), `hooks/queries.ts`, `components/ActivationBanner.tsx` (NEW), `components/PostAhaToast.tsx` (NEW), `components/Layout.tsx`, `pages/DashboardPage.tsx`, `pages/UploadPage.tsx`, `pages/AccountPage.tsx`, `pages/RoutesPage.tsx` (weather zones map gating), `App.tsx` (no logic change — landing verified, decision #9), `pages/ActivationBanner.test.tsx` (NEW), `pages/workspaceSurfaces.smoke.test.tsx` (§9).
15. `docs/plans/phase1-cashflow-core.md`, `phase2-receipt-processing.md`, `phase3-audit-reversibility.md` — UNTOUCHED (immutable).

## 4. Strict Import Map (DAG — models → schemas ↔ services → api; no cycles; services NEVER import `app.api`)

```
models.activation_state (NEW)          → db.base, db.custom_types, models.common, sqlalchemy
models.threshold_crossing (NEW)        → db.base, db.custom_types, models.common, sqlalchemy
models.fleet_asset (MOD)               → + organization_id + data_origin (no new imports)
models.{warehouse,item,inventory,order} (MOD) → + data_origin (no new imports)
models.__init__ (MOD)                  → + activation_state, threshold_crossing (top of DAG)
schemas.activation (NEW)               → pydantic + typing only (standalone rule)
schemas.route (MOD)                    → + post_aha_toast, data_origin (standalone)
services.metering                      → UNCHANGED (decision #4)
services.audit                         → UNCHANGED (record_audit_event reused)
services.billing.pricing               → UNCHANGED (cap source of truth)
services.billing.lifecycle             → UNCHANGED (Phase 1 engine untouched)
services.activation.state (NEW)        → models (5 data tables + ActivationState),
                                          schemas.activation, services.audit,
                                          services.metering (current_usage_window),
                                          activation.freecap
services.activation.freecap (NEW)      → models.usage_meter, models.organization,
                                          services.metering, services.billing.pricing
                                          (LEAF of billing: imports pricing only — acyclic)
services.activation.seeding (NEW)      → models (5 tables), core.config (sample_data_dir),
                                          pandas, services.audit, activation.state
services.activation.reset (NEW)        → models (5 tables + activation state + crossings),
                                          activation.seeding, activation.state, services.audit
services.activation.banner (NEW)       → activation.state, activation.freecap
services.activation.__init__ (NEW)     → re-exports (above modules)
services.billing.locks (MOD)           → + activation.freecap (assert_free_cap_writable)
                                          [billing.locks → activation.freecap → pricing;
                                           activation NEVER imports billing.locks — acyclic]
api.security (MOD)                     → + activation.freecap (FreeCapLockedError)
api.endpoints.activation (NEW)         → api.security (get_current_membership,
                                          require_org_roles), db.session, models.organization,
                                          schemas.activation, services.activation.*
api.endpoints.ingestion (MOD)          → + activation.seeding, activation.state
api.endpoints.routes (MOD)             → + activation.state, services.metering (route_optimizations)
api.router (MOD)                       → + api.endpoints.activation
core.config (MOD)                      → + sample_data_dir
tests → models + services + conftest (shared fixtures only; NO imports from other test files)
```

Cycle proof: `activation.* → billing.pricing` (leaf) and `activation.* → metering` (leaf); `billing.locks → activation.freecap → pricing` introduces no back-edge into billing (activation imports pricing/invoicing-adjacent reads only, never locks/lifecycle). `billing` NEVER imports `activation`. `activation.state → activation.freecap` (freecap imports nothing from state — pure counter math — acyclic). No service imports `app.api`. `api.endpoints.ingestion` stays ≤400 via the `services/activation/ingest.py` extraction (per-handler upsert helpers — add to §2.3: `ingest.py` ~200 lines holding `upsert_warehouses(db, org, df) -> counts`, `upsert_items(...)`, `upsert_fleet(...)`, `upsert_inventory(...)`, `upsert_orders(...)` — org-scoped row mapping mirroring today's handler bodies + `data_origin='real'` stamps; endpoints become thin callers).

## 5. Deterministic flows

**Signup (NB-25):** `POST /auth/company-signup` → org + user + membership created (existing) → `seeding.seed_workspace(db, org, user, now)` (inserts 5 categories sample rows + activation row `seeded_at`) → audit `workspace.created` (existing) + `workspace.seeded_sample_data` → single commit (existing line 203) → cookie set. The workspace is fully operational on sample data immediately (NB-25.2): route optimize, forecasts, alerts, replenishment, provider keys, tier switch all work — the only per-workspace gate is the new free-cap lock, applied uniformly.

**Upload (NB-26/28):** `POST /ingestion/{category}-csv` → write-guard (phase + free-cap) → org-scoped upsert with `data_origin='real'` → `supersede_sample_rows` (decision #3) → `record_csv_upload` audit → commit. Next `GET /activation` derives N-of-5 from real-presence; console invalidates `['activation']` on mutation success → banner + checklist update without reload (NB-30.4).

**Route optimization (NB-27/28/33):** `POST /routes/optimize` → write-guard → compute → record BOTH meters (`delivery_tasks` = len(deliveries) as today + `route_optimizations` = 1) → compute `data_origin` → audit `route.optimized` + `data_origin` → `record_route_optimization` (m6 transition + toast flag + audit) → response `post_aha_toast` when first-ever run → commit.

**Free-cap lock (NB-31):** `free_cap_state` derives lazily from the current month window at every guard evaluation and every `GET /activation`. Locked → 423 on the 32 guarded endpoints with `free_cap_locked: true`; console renders the NB-31.6 banner on EVERY page (Layout slot) with "Upgrade now" → `/account`. Month rollover: the window moves, counters read zero for the new period, lock lifts — zero code (lazy derivation, decision #5).

**Pitch ladder (NB-32):** `GET /activation` fires crossings p60/p80 as utilization crosses (insert + audit); console banner stack: p100 (locked) > p80 (persistent, "See pricing" → `/account`) > p60 (dismissible, no CTA, `POST /activation/pitch-dismiss`). Never leaves the console.

**Milestone-6 toast (NB-33):** first optimization response `post_aha_toast: true` → `PostAhaToast` renders the exact NB-33.1 copy, auto-dismisses (6s), no CTA; `toast_fired_at` prevents any re-fire (server truth).

**Login (NB-34):** any login → `/` → DashboardPage → activation banner by state matrix (decision #8); m6 → no banner.

**Reset (NB-35):** `/account` Danger zone (admin-visible) → modal requires typing `org.name` exactly → `POST /activation/reset` → wipes + re-seeds + resets state + clears crossings + audit → console logout + redirect `/login` → re-login lands `/` at 0%.

## 6. Endpoint + schema surface summary

| Method | Path | Auth | Body | Returns |
|---|---|---|---|---|
| GET | `/activation` | any membership | — | `ActivationStateRead` (§2.4; includes `banner`, `free_cap`, `pitch` payloads) |
| POST | `/activation/reset` | OWNER/ADMIN | `{workspace_name}` | `{rows_reseeded, activation_reset}`; 422 mismatch |
| POST | `/activation/pitch-dismiss` | OWNER/ADMIN/OPERATOR | `{level:'p60'}` | `{dismissed: bool}`; 422 other levels |

`ActivationStateRead.banner` shape: `{visible, n_of_5, pct_complete, cta ('/upload'|'/routes'|null), demo_mode: bool}`. `free_cap` shape: `{locked, utilization_pct, message: 'Free tier cap reached. Writes resume next month, or upgrade now to continue immediately.'|None}`. `pitch` shape: `{banner: 'p100'|'p80'|'p60'|None, dismissible: bool, fired: list[str]}`. `toast_fired: bool`.

## 7. Migration — `apps/platform-api/alembic/versions/20260806_0016_activation_phase4.py` (down_revision `'20260806_0015'`)

1. `ADD COLUMN data_origin VARCHAR(8) NOT NULL DEFAULT 'real'` on `warehouses`, `items`, `fleet_assets`, `inventory`, `historical_orders` (Postgres branch adds `CHECK (data_origin IN ('sample','real'))` per table; sqlite branch columns-only — Phase 3 quirk precedent, model CheckConstraints authoritative for `create_all` test DBs).
2. `fleet_assets`: `ADD COLUMN organization_id CHAR(36) NULL` + `ADD CONSTRAINT fk_fleet_assets_organization FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE SET NULL` (Postgres only) + `CREATE INDEX ix_fleet_assets_organization_id`.
3. `CREATE TABLE organization_activation_state` (id CHAR(36) PK, organization_id CHAR(36) NOT NULL UNIQUE, m6_completed_at TIMESTAMPTZ NULL, toast_fired_at TIMESTAMPTZ NULL, seeded_at TIMESTAMPTZ NULL, created_at TIMESTAMPTZ NOT NULL; FK organization_id → organizations(id) ON DELETE CASCADE; INDEX organization_id). Created in BOTH dialects (Phase 3 `_create_fraud_flags_table` pattern).
4. `CREATE TABLE threshold_crossings` (id CHAR(36) PK, organization_id CHAR(36) NOT NULL, period_start DATE NOT NULL, threshold_level VARCHAR(8) NOT NULL, fired_at TIMESTAMPTZ NOT NULL, dismissed_at TIMESTAMPTZ NULL, created_at TIMESTAMPTZ NOT NULL; FK organization_id CASCADE; UNIQUE(organization_id, period_start, threshold_level); INDEX organization_id). Both dialects.
5. No data backfill. Docstring flags the sqlite quirk exactly like `20260806_0015`.

## 8. Audit integration (Phase 1 `AuditEvent` pattern via `services.audit.record_audit_event`, reused unchanged)

New event types (all with actor + organization_id + stringified values):
- `workspace.seeded_sample_data` — `{categories: [...], rows_per_category: {...}}` (NB-25.4).
- `workspace.csv_uploaded` — `{category, data_origin:'real', records_processed, records_created, records_updated, errors: [...]}`.
- `workspace.reset_to_sample_data` — `{workspace_name, categories: [...], rows_reseeded: {...}}` (NB-35.5; visible in the dashboard/account audit timelines automatically).
- `activation.milestone_6_completed` — `{first_route_optimization_run_id, data_origin}`.
- `usage.pitch_fired` — `{level: 'p60'|'p80', period_start, utilization_pct}`.
- MODIFIED existing: `route.optimized` payload gains `data_origin` (NB-27.3). Existing payload fields untouched.

**Immutability discipline (Phase 3 rule) carries over:** no code path writes to an existing AuditEvent row; seeding/reset/upload/optimization write NEW records.

## 9. Ops-console map (Tailwind dark patterns; `apps/ops-console/src/`)

- **`types/api.ts` (MODIFY)** — `ActivationCategoryStatus = 'real'|'sample'|'empty'`; `CategoryMilestone`, `ActivationState` (per §2.4), `ResetWorkspaceResult`, `PitchDismissResult`; extend `RouteOptimizeResponse` with `post_aha_toast?: boolean` + `data_origin?: string | null`.
- **`services/activationApi.ts` (NEW)** — `getActivationState()`, `resetWorkspace(workspaceName)`, `dismissPitch(level)`.
- **`hooks/queries.ts` (MODIFY)** — `useActivationState()` (queryKey `['activation']`, staleTime 30s); `useResetWorkspace()` (mutation → on success call auth logout + redirect `/login`); `useDismissPitch()`; add `['activation']` to `useInvalidateDashboard()` and to the CSV-upload mutation invalidations (CsvUploadPanel gains an invalidation call after each successful upload — NB-30.4 live update) and the route-optimize mutation invalidation.
- **`components/ActivationBanner.tsx` (NEW, ~220 lines)** — THE single shared banner (NB-30): reads `useActivationState()`. Modes: `compact` (dashboard, NB-34 copy matrix incl. pct/N-of-5/next-step, CTA `/upload` or `/routes`) and `checklist` (upload page: NB-26 demo copy + 5 per-category chips `real`/`sample`/`empty` + next-step arrow + progress bar). Renders nothing when `m6_completed`. Free-cap + pitch banners render in BOTH modes (p100 supersedes p80 supersedes p60; p60 dismiss button calls `useDismissPitch`; p80/p100 CTA → `/account`).
- **`components/PostAhaToast.tsx` (NEW, ~60 lines)** — reads the optimize mutation response `post_aha_toast`; renders the EXACT NB-33.1 copy; no CTA; auto-dismiss 6s.
- **`components/Layout.tsx` (MODIFY)** — top-of-main banner slot rendering the FREE-CAP + pitch banners on EVERY page (NB-31.6, NB-32) from `useActivationState()`; the activation/demo banner itself stays page-level (dashboard + upload only, NB-30). Disable nothing globally.
- **`pages/DashboardPage.tsx` (MODIFY)** — render `<ActivationBanner mode="compact" />` under the header. Panel gating (NB-29): `milestone = state.m6 ? 6 : state.n_of_5`; ALWAYS-VISIBLE: exception feed, audit timeline, feedback form, usage posture tile, demo banner; `placeholder` mode: inventory charts + utilization tile (m4), forecast chart + forecast demand + weather risk tiles (m5) — render `<Panel>` with "Unlocks after Milestone N — [Continue onboarding]" + CTA; `hidden` mode: DockGantt + FreightReconciliation (m6) — render nothing until m6. Per-panel mode const (`{id, mode: 'hidden'|'placeholder', milestone}`) supporting both rendering modes (NB-29.3).
- **`pages/UploadPage.tsx` (MODIFY)** — render `<ActivationBanner mode="checklist" />`; disable upload buttons while `free_cap.locked` (server 423s anyway — UX mirror, NB-31.2).
- **`pages/RoutesPage.tsx` (MODIFY)** — weather risk zones map section gated: hidden until `n_of_5 >= 5` (NB-29.1); page itself remains routable (NB-28.5/RoutesPage unlock is a reveal concern; the route OPTIMIZE call 423s only on free-cap/phase locks — matching "Routes page unlocks at milestone 5" as a surface, with sample data making it functional from signup per NB-25.2).
- **`pages/AccountPage.tsx` (MODIFY)** — NEW "Danger zone" Panel (visible when `user.role === 'admin'`; server re-validates OWNER/ADMIN membership — decision #10): "Reset workspace to sample data" button → modal with a text input; the confirm button stays disabled until the typed value === `subscription.organization_name` exactly; on success → logout + redirect `/login`. The existing tier-picker cards remain the target of every "See pricing"/"Upgrade now" CTA (`/account` route is the in-product picker — NB-32.4 never leaves the console).
- **`pages/ReceiptsPage.tsx`, `App.tsx`** — NO logic change (App.tsx landing verified in §1 decision #9); smoke test asserts route table.
- **`pages/ActivationBanner.test.tsx` (NEW)** — renders compact/checklist modes, copy matrix rows, p60 dismiss, p100 CTA target.
- **`pages/workspaceSurfaces.smoke.test.tsx` (MODIFY)** — dashboard renders with activation banner in seeded state; danger zone visible for admin; panel gating placeholders render for a 0-of-5 state.

## 10. Sequencing (TDD order) and test map

### 10.1 `tests/conftest.py` (MODIFY — additive)

- `signup_workspace(client, name='Seed Co', email=None) -> (org_id, token)` — company-signup wrapper asserting 201.
- `sample_row_counts(db_session, org_id) -> dict[str, int]` — per-category `data_origin='sample'` counts (seed assertions).
- `upload_csv(client, token, category, filename, content: str) -> Response` — multipart helper for the 5 ingestion endpoints.
- `real_warehouse_csv(rows: list[tuple]) -> str` — CSV text builders per category (deterministic fixtures, NOT the shipped CSVs — same columns).
- `advance_usage(db_session, org_id, metric, units, period=None)` — direct `OrganizationUsageCounter` write to force thresholds/caps deterministically.
- `seed_csv_path(tmp_path, monkeypatch)` — fixture overriding `settings.sample_data_dir` to a tmp copy of `sample-data/` (keep repo files pristine in tests).

### 10.2 New test files (named functions)

**test_activation_models.py:** `test_activation_state_org_unique`; `test_activation_state_nullable_columns`; `test_threshold_crossing_unique_org_period_level`; `test_threshold_crossing_level_check`; `test_data_origin_default_real_and_check`; `test_fleet_asset_gains_organization_id`.

**test_activation_seeding.py (NB-25):** `test_signup_seeds_all_five_categories_per_workspace` (sample rows exist with org id, counts match CSVs); `test_seed_rows_origin_sample_and_org_scoped` (decision #2); `test_signup_seed_audit_event_recorded` (workspace.seeded_sample_data with user id + timestamp + payload — NB-25.4); `test_seed_idempotent_no_double_seed_on_second_org` (two signups → each org has own rows, no cross-contamination — NB-25.3); `test_seeded_workspace_runs_operations` (optimize + forecast + alert ack on sample data succeed — NB-25.2); `test_supersede_warehouses_deletes_sample_warehouses` (decision #3); `test_supersede_keeps_sample_warehouse_referenced_by_real_inventory`; `test_supersede_deletes_dangling_sample_inventory_orders`; `test_upload_scoped_to_own_org_does_not_touch_other_org_rows` (decision #13).

**test_activation_milestones.py (NB-28):** `test_fresh_signup_is_zero_of_five`; `test_upload_orders_only_registers_zero` (sequential prefix — decision #1); `test_upload_warehouses_then_items_advances_two`; `test_milestone_4_and_5_sequential_order`; `test_m6_on_sample_data_registers` (optimize at 0-of-5 → m6_completed, NB-28.4); `test_m6_first_run_any_substrate`; `test_m6_does_not_require_prefix` (NB-28.4 wins — decision #7); `test_state_per_organization_not_per_user` (two members see same state — NB-28.2); `test_second_user_inherits_state` (NB-9.2-style: joining user sees same checklist).

**test_activation_banner_state.py (NB-26 + NB-34):** `test_banner_visible_at_signup_not_dismissible` (no dismiss endpoint exists for the activation banner — NB-26.2); `test_banner_copy_zero_of_five` (NB-34.5 exact); `test_banner_copy_n_of_five_with_next_step` (NB-34.4, N=2 → 40% + "Fleet Assets" next); `test_banner_copy_five_of_five_pre_optimization` (80% + `/routes` CTA — NB-34.3); `test_banner_copy_disappears_at_m6` (NB-34.2); `test_demo_messaging_absent_at_five_of_five` (decision #8); `test_banner_state_matches_milestone_counts`.

**test_activation_metering_origin.py (NB-27):** `test_route_optimization_records_both_meters` (delivery_tasks = deliveries count + route_optimizations = 1 — decision #12); `test_sample_substrate_optimization_counts_identically` (same counters at same counts on sample warehouses — NB-27.1/2); `test_route_audit_data_origin_real` (all-real substrate); `test_route_audit_data_origin_sample` (any sample warehouse → 'sample' — decision #4); `test_metering_never_stores_origin` (no data_origin column on `organization_usage_counters`; counter rows identical for sample vs real runs — NB-27.4); `test_upload_audit_event_with_counts_and_origin`.

**test_activation_panel_gating.py (NB-29):** `test_panel_gate_payload_milestone_mapping` (activation state drives m4/m5/m6 thresholds — service-side assertion of the state the console gates on); `test_always_visible_surfaces_flagged` (banner/exception/audit/feedback flagged milestone 0); `test_gating_order_immutable` (no per-panel config path — const list, asserted stable).

**test_activation_banner_shared.py (NB-30):** `test_activation_payload_single_source` (dashboard + upload render from the same `GET /activation` — payload shape assertion); `test_state_change_reflects_without_reload` (upload → GET /activation returns updated n_of_5; console invalidation contract asserted via hook wiring in the console test); `test_upload_page_reports_per_category_origin_chips` (real/sample/empty per category — NB-30.5).

**test_free_cap_lock.py (NB-31):** `test_cap_hit_delivery_tasks_disables_writes` (2500 → 423 on optimize + upload + alert ack + replenishment approve + shipment create + provider set + manual alert — NB-31.2 full list); `test_cap_hit_route_optimizations_disables_writes` (50 runs → 423); `test_reads_remain_available` (dashboard reads, schedules, exports endpoints, /account, /subscriptions/me, audit timeline, exception feed all 200 while locked — NB-31.3); `test_free_cap_no_overage_path` (record past cap → still 423; no partial writes — NB-31.4); `test_sample_and_real_data_lock_identically` (50 sample-substrate optimizations → locked — NB-31.5); `test_lock_auto_lifts_at_month_rollover` (advance window → 200 again — lazy derivation, decision #5); `test_phase_lock_and_free_cap_compose` (both held → phase banner wins, still 423 — decision #5); `test_select_tier_available_while_free_cap_locked` (upgrade path open — NB-31.4 + decision #5); `test_receipts_exempt_from_free_cap` (upload/decision endpoints still 200 — carve-out); `test_423_detail_contains_free_cap_fields`.

**test_upgrade_pitch.py (NB-32):** `test_p60_fires_at_sixty_percent_once_per_month` (crossing row + audit; second read no re-fire — NB-32.5); `test_p60_dismissible_and_returns_next_month` (dismissed_at → banner hidden; new period → new crossing); `test_p80_fires_and_not_dismissible` (no dismiss path — 422 on dismiss of p80); `test_p100_supersedes_p80` (locked → pitch.banner='p100' regardless of p80 row); `test_banner_stack_order` (p100 > p80 > p60); `test_pitch_cta_targets_in_product_account` (payload cta contract — console-only CTA; server asserts nothing beyond payload shape); `test_crossings_cleared_on_upgrade_never_needed` (non-free tier → pitch payload null).

**test_activation_toast.py (NB-33):** `test_toast_fires_once_per_organization` (first optimize → response `post_aha_toast: true` + toast_fired_at set; second optimize → false — NB-33.4); `test_toast_fires_on_sample_data` (NB-33.5); `test_toast_no_cta_fields` (payload has no upgrade/price fields — NB-33.2, asserted at schema level); `test_toast_survives_second_user` (second user's first optimize → no re-fire).

**test_activation_reset.py (NB-35):** `test_reset_requires_admin_role` (operator 403); `test_reset_requires_exact_workspace_name` (mismatch 422; case/whitespace sensitivity locked); `test_reset_wipes_real_uploads_and_reseeds_sample` (real rows gone, sample rows back — counts equal CSVs); `test_reset_milestones_back_to_zero` (m6 cleared, n_of_5 = 0 — decision #1 derived semantics); `test_reset_clears_pitch_crossings`; `test_reset_audit_event_with_admin_and_timestamp` (workspace.reset_to_sample_data visible in audit timeline — NB-35.5); `test_reset_after_login_lands_on_dashboard_with_zero_banner` (console flow: logout → login → `/` shows 0% — NB-35.7, console test).

**test_activation_api.py:** `test_get_activation_membership_required` (401 without token); `test_get_activation_full_payload_shape`; `test_pitch_dismiss_unknown_level_422`; `test_reset_endpoint_route_registered`.

### 10.3 Sequencing

1. Models + migration + conftest → `test_activation_models.py` (`alembic upgrade head` verified on sqlite).
2. `seeding.py` (+ `settings.sample_data_dir`) + signup hook → `test_activation_seeding.py`.
3. `state.py` (derived milestones) → `test_activation_milestones.py`.
4. `freecap.py` + locks/security composition → `test_free_cap_lock.py`.
5. `pitch_state` + crossings → `test_upgrade_pitch.py`.
6. routes.py (meters + data_origin + m6 + toast) → `test_activation_metering_origin.py` + `test_activation_toast.py`.
7. ingestion org-scoping + supersede + `ingest.py` extraction → extend `test_activation_seeding.py` (supersede cases) + `test_activation_banner_shared.py`.
8. `reset.py` + endpoint → `test_activation_reset.py`.
9. Schemas + `/activation` endpoints + router → `test_activation_api.py` + `test_activation_banner_state.py` + `test_activation_panel_gating.py`.
10. Console: types → activationApi → hooks → ActivationBanner → PostAhaToast → DashboardPage gating → UploadPage checklist → AccountPage danger zone → RoutesPage gating → Layout banner slot → `ActivationBanner.test.tsx` + smoke test.
11. Full suite + `alembic upgrade head` + manual smoke: signup → seeded dashboard + banner → upload 1-5 CSVs (banner N-of-5 → 80% → optimize → toast → banner gone) → 60/80/100 pitch ladder via forced counters → reset flow with typed confirmation → re-login.

## 11. Explicit NON-GOALS (Phase 4 must NOT do)

- **NO Amharic / i18n** (scope lock; English-only console).
- **NO email drip** (DEFERRED-06 — activation pressure is in-product only).
- **NO feature-gated pitches** (DEFERRED-05 — quota-metering pitches only; no per-feature upgrade prompts).
- **NO A/B testing** (DEFERRED-08).
- **NO shared demo tenant** (seeding is per-workspace; no read-only demo toggle — doc §10).
- **NO per-user activation state** (org-scoped only — doc §10).
- **NO time-based onboarding deadlines** (banner is the only pressure — doc §10).
- **NO forced routing to `/upload`** (login lands `/` always — NB-34.1).
- **NO metering differentiation** (`services/metering.py` untouched; counters never store origin).
- **NO overage path on Free** (hard-lock only; no partial-write allowance — NB-31.4).
- **NO cron/scheduler** (month rollover + thresholds are lazy derivations; crossing INSERTs happen on reads).
- **NO server-side token blacklist/invalidation** (stateless JWTs; reset re-login is client logout — decision #10).
- **NO changes to `lifecycle.py`, `invoices.py`, `pricing.py`, `subscriptions.py`, `billing/__init__.py` surface, the Phase 1 banner/lock copy, or the Phase 2/3 receipt engine.**
- **NO new dashboard panels** — only gating of the 11 existing surfaces (NB-29 list is a gate map, not a build list).
- **NO deletion of the shipped `sample-data/` CSVs** — they become runtime inputs; tests copy them to tmp dirs.

## 12. Risks flagged against existing code (for @qa and @architect)

1. **Ingestion org-scoping changes multi-tenant behavior** (decision #13): lookups become org-filtered, so org-less legacy rows (organization_id NULL) are no longer updatable via CSV upload. Deterministic consequence; documented. The repositories (`get_by_code(code, organization_id)`) already support the filter — the endpoints just don't use it today.
2. **`record_usage_for_user_membership` resolves the org from the ACTOR's first active membership** — matches the existing optimize flow; the m6 hook must use the same `resolve_actor_organization_id` value to stay consistent when an admin (no membership) drives an optimization: `record_route_optimization` gets the org id explicitly from the endpoint, never from the actor.
3. **Supersede + CASCADE interplay** (decision #3): deleting sample warehouses CASCADE-deletes sample inventory/orders via the existing FKs — the explicit org-scoped cleanup is therefore belt-and-braces; the real risk is REAL downstream rows referencing deleted sample upstream rows — prevented by the "keep sample rows referenced by real rows" rule. The `test_supersede_keeps_sample_warehouse_referenced_by_real_inventory` test is the load-bearing guard.
4. **`require_writable_workspace` gains a new failure mode** — the 423 detail shape changes (additive fields only; existing fields unchanged). Phase 1 tests asserting the exact detail dict must be checked for strict equality (they assert fields, not full-dict equality — verify during build).
5. **`fleet_assets` gains `organization_id`** — the fleet read endpoints (`list_fleet_assets` in `ops.py`) query globally today; adding the column is additive and reads stay global (out of scope); activation counts filter by org.
6. **routes.py line budget** — +35 lines keeps it ~330, but the `data_origin` computation needs a single query for the warehouses used (start + stop codes); use one `IN (...)` select, not N queries.
7. **Crossing INSERTs on `GET /activation` are writes on a GET** — intentional (fire-once semantics need a durable mark; same lazy-issuance precedent as `lifecycle.try_issue_invoice`), documented in `freecap.pitch_state`; the endpoint is write-guard exempt and idempotent (UNIQUE constraint + upsert semantics).
8. **The `route_optimizations` meter is a behavior CHANGE to the optimize endpoint** (new counter row per run) — this is the NB-31.1 gap-fill, but it means existing orgs that ran optimizations before Phase 4 have uncounted history; acceptable (counters are forward-looking; no backfill — documented).
9. **Reset while Phase 1 locks are held**: `POST /activation/reset` is write-guard exempt and does NOT touch invoices/trials — the billing phase is preserved; only activation + data + crossings reset (NB-35 lists exactly those).
10. **Console role gate for the danger zone uses the global `user.role`** — server re-validates membership OWNER/ADMIN; a viewer with global admin role sees the button but gets 403 → the console surfaces the error; acceptable (server is authoritative).

## 13. QA audit notes

QA audits this phase against: this document (decisions #1-13 are binding), NB-25..35 acceptance criteria (pending-behaviors.md lines 244-359), and the behavior doc §1-10. Special attention: supersede semantics (decision #3), meter-lock composition + banner priority (decision #5), pitch fire-once + p60 dismiss (decision #6), milestone-6-on-sample-data + toast once (decision #7), banner copy matrix (decision #8), and reset re-login flow (decision #10). Ledger debit after QA APPROVED: TECH-25..35 removed from tech-backlog.md, `[IMPLEMENTED]` appended to NB-25..35, warning banner stripped from `operator-activation-and-milestone-tracking.md`.
