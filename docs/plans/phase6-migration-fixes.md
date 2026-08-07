# Phase 6 — Migration-Fixes Batch (TECH-54, parent NB-51)

**Branch:** `feat/launch-readiness` (working tree after Phase 1 commit `0e28371`)
**Status:** Prepared by `@plan`; executed by `@build` (TDD), audited by `@qa`.

## Goal

Audit, minimally adjust, and atomically commit the TECH-54 hotfix batch (7 migration files + dependency manifests + product-web signup env guard) so the alembic chain runs green on both sqlite scratch chains and Postgres/Supabase, with regression tests for every fix that currently lacks coverage.

## Evidence anchors (verified)

- SQLAlchemy 2.0.51: `postgresql.UUID(as_uuid=True)` compiles on sqlite as `UUID` (accepted); `sa.Uuid()` → `CHAR(32)` on sqlite / `UUID` on PG; raw `uuid.UUID` bound through untyped `sa.text()` **fails on sqlite** (`sqlite3.ProgrammingError: type 'UUID' is not supported`).
- PostgreSQL has **no assignment/implicit cast text→uuid** (explicit-only) — a `str` UUID bound into a PG `uuid` column also fails. → the 0013 backfill bind must be **dialect-guarded**.
- `route_schedules.assigned_asset_id` / `route_history` table never exist in any migration (real table `route_optimization_runs` from 0007).
- Platform runs the full chain on PG: backend Dockerfile `CMD = alembic upgrade head && uvicorn ...`; dev `.env` → `postgresql+psycopg://...@localhost:5432/supply_chain`; sqlite is only the test path (`create_all`) and stamped scratch chains.
- 348 platform-api tests collect; **zero tests execute alembic** (no migration harness exists). product-web test script = `vitest run`.

## 1. File-by-file disposition table

| # | File | Root cause | Verdict | Test coverage |
|---|---|---|---|---|
| 1 | `apps/platform-api/alembic/versions/20260727_0005_fleet_assets.py` | Additive repair: `latitude`/`longitude`/`last_telemetry_at` added to `fleet_assets` create_table (model declares them; original 0005 never created them → fresh-DB drift). | **Keep as-is.** Additive; both-dialect safe. Pre-existing DBs reach parity via 0017. | Indirect via 0017 tests |
| 2 | `apps/platform-api/alembic/versions/20260803_0012_native_uuid_migration.py` | Phantom-artifact repair: removed `route_schedules_assigned_asset_id_fkey` + `assigned_asset_id` + `route_history` (never existed). Original 0012 was a guaranteed PG failure (`constraint ... does not exist`, `relation "route_history" does not exist`). | **Keep as-is.** 0012 remains PG-only raw SQL — sqlite scratch chains must be `create_all` + stamped. | Add chain-integrity test |
| 3 | `apps/platform-api/alembic/versions/20260805_0013_cashflow_phase1.py` | Type-consistency repair: `CHAR(36) → postgresql.UUID(as_uuid=True)` on new tables; `server_default=sa.text('1') → 'true'` (PG rejects DEFAULT 1 on boolean); seed `id` str→UUID in typed `bulk_insert` (OK both dialects). **BUT** `_backfill_organizations()` switched `'id': str(uuid.uuid4()) → uuid.uuid4()` in an **untyped** `sa.text()` INSERT → breaks sqlite-stamped chains with a `trialing` org. | **Needs adjustment (fix ①):** dialect-guard the new-id bind. | Add bind regression test (TDD red on current code) |
| 4 | `apps/platform-api/alembic/versions/20260806_0014_receipt_processing_phase2.py` | Same repairs as 0013: `CHAR(36) → postgresql.UUID` on 6 tables + `server_default=sa.text('0') → 'false'` (7 booleans). | **Keep as-is.** Verified sqlite-compilable. | Chain test only |
| 5 | `apps/platform-api/alembic/versions/20260806_0015_reversals_phase3.py` | PG branch: `reversed_by_user_id CHAR(36) → postgresql.UUID` (FK to users.id native uuid); `sender_fraud_flags` ids/org_id → uuid. sqlite branch keeps CHAR(36). | **Keep as-is.** Dialect branch preserved. | Chain test only |
| 6 | `apps/platform-api/alembic/versions/20260806_0016_activation_phase4.py` | `_UUID = sa.Uuid()` for `fleet_assets.organization_id` + new tables; keeps §0A composite-org-unique index replacement + sqlite guards. | **Keep as-is.** | Chain test only |
| 7 | `apps/platform-api/alembic/versions/20260806_0017_fleet_asset_telemetry_backfill.py` (new) | Idempotent forward repair: inspector-checked `add_column` for 3 telemetry columns; `down_revision='20260806_0016'` (head); downgrade documented no-op. | **Keep as-is.** | Add idempotency tests (primary gap) |
| 8 | `apps/platform-api/pyproject.toml` | `slowapi>=0.1.9` added (was requirements-only). | **Keep as-is.** | Manifest test covers |
| 9 | `apps/platform-api/requirements.txt` | `httpx>=0.27.0` added (was pyproject-only). | **Keep as-is.** | Manifest test covers |
| 10 | `apps/platform-api/tests/test_runtime_dependency_manifests.py` (new) | Regression guard: normalized-name set equality pyproject↔requirements. | **Keep as-is.** | N/A |
| 11 | `apps/product-web/src/lib/company-signup.ts` | Env-resolution guard: module-level silent fallback `… || 'http://localhost:8000/api/v1'` replaced with runtime `resolvePlatformApiBase()` — trimmed + trailing-slash stripped; non-production falls back to localhost; **production throws** `missingPlatformApiMessage`. Root cause: blank Vercel `NEXT_PUBLIC_PLATFORM_API_URL` → signup always failed deployed. | **Keep as-is.** | 3 resolver tests exist; 2 gaps below |
| 12 | `apps/product-web/src/lib/company-signup.test.ts` (new) | Resolver tests (configured+trailing slash; dev fallback; prod throw). | **Keep as-is, extend** (2 tests). | See §2 |
| 13 | `apps/product-web/.env.example` | Documentation: `NEXT_PUBLIC_APP_CONSOLE_URL` / `NEXT_PUBLIC_PLATFORM_API_URL` marked required in deployed envs. | **Keep as-is.** | None needed |
| — | `.opencode/agents/vision.md`, `docs/…` | Agent config / architect ledger — **NOT part of TECH-54**. | **Excluded** from commit. | — |

## 2. Missing tests to add (TDD)

### 2a. `apps/platform-api/tests/test_migration_0017_telemetry_backfill.py` (new)
Harness: throwaway `sqlite+pysqlite:///:memory:` engine (StaticPool), create `fleet_assets` with the **old-0005 shape** (no telemetry columns), execute `upgrade()` inside `MigrationContext.configure(conn)` + `Operations.context`, module loaded via `importlib.util.spec_from_file_location`.
- `test_0017_upgrade_adds_telemetry_columns_when_missing` — old shape → upgrade() → inspector shows the 3 columns; Float/DateTime round-trip insert succeeds.
- `test_0017_upgrade_is_idempotent_on_existing_columns` — fixed shape → upgrade() twice → no exception, no duplicate-column error.
- `test_0017_downgrade_is_noop_and_preserves_columns` — after upgrade, downgrade() → no error, columns remain.

### 2b. `apps/platform-api/tests/test_migration_chain_integrity.py` (new)
Regex-parse `revision`/`down_revision` from every `alembic/versions/*.py` (no module import):
- `test_migration_chain_is_linear_and_head_is_0017` — every down_revision resolves; no duplicates; exactly one head; `head == '20260806_0017'`; `0017.down_revision == '20260806_0016'`.

### 2c. `apps/platform-api/tests/test_migration_0013_backfill_dialect_bind.py` (new — TDD red on current tree)
Same harness; sqlite engine with `organizations` containing one `subscription_status='trialing'` row + 0013 tables schema context:
- `test_0013_backfill_binds_new_ids_on_sqlite` — call `_backfill_organizations()` → **no `ProgrammingError`**; a `trial_records` row exists whose `id` parses as UUID. **Red today**, green after fix ①.

### 2d. `apps/product-web/src/lib/company-signup.test.ts` (extend)
- `it('treats a whitespace-only configured URL as missing in production')` — `resolvePlatformApiBase('   ', 'production')` throws; `resolvePlatformApiBase('   ', 'development')` returns localhost fallback.
- `it('posts to the resolved API base URL and surfaces server errors')` — `vi.stubGlobal('fetch', …)`; `companySignup({...})` with `resolvePlatformApiBase('https://api.example.com/api/v1/', 'production')`; assert fetch called with exactly `https://api.example.com/api/v1/auth/company-signup`, POST, JSON content-type/body; non-ok response → thrown message equals parsed FastAPI `detail`. Add `afterEach(() => vi.unstubAllGlobals())`.

## 3. Strict Import Map

**Fix ① (0013 `_backfill_organizations`)** — no new imports. Localized: `new_id = str(uuid.uuid4()) if bind.dialect.name == 'sqlite' else uuid.uuid4()` bound as `'id': new_id`. (Do NOT bind `str()` globally — PG has no text→uuid assignment cast; do NOT bind raw `UUID` globally — sqlite driver rejects it.)

**New test files** — imports: `importlib.util`, `pathlib.Path`, `sqlalchemy` (`create_engine`, `inspect`, `text`), `alembic.migration.MigrationContext`, `alembic.operations.Operations`; `uuid`; `datetime.UTC`/`datetime` (2c). `test_migration_chain_integrity.py`: `pathlib.Path`, `re` only. company-signup.test.ts: `vi` from `'vitest'`, existing imports unchanged.

**company-signup.ts** — no import changes; exports unchanged (`missingPlatformApiMessage`, `resolvePlatformApiBase`).

## 4. Migration-run verification (Postgres-shaped proof)

docker-compose provides `postgres` (postgres:16) — scratch proof (pre-flight for TECH-53):
1. `docker compose up -d postgres` → wait healthy (`pg_isready`).
2. `docker compose exec postgres createdb -U postgres supply_chain_scratch`.
3. From `apps/platform-api` (repo venv): `DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/supply_chain_scratch`, `APP_ENV=development`; run `..\..\.venv\Scripts\alembic.exe upgrade head` → **full corrected chain (0001→0017) green**.
4. **0013 backfill on PG:** `alembic upgrade 0012`, INSERT one `organizations` row with `subscription_status='trialing'` via `docker compose exec postgres psql -U postgres -d supply_chain_scratch -c "INSERT …"`, then `alembic upgrade head` → verify a `trial_records` row created.
5. **0017 add-path on PG-shaped schema:** `alembic upgrade 0016`, `ALTER TABLE fleet_assets DROP COLUMN latitude, DROP COLUMN longitude, DROP COLUMN last_telemetry_at`, `alembic upgrade head` → columns re-added; then `alembic downgrade -1 && alembic upgrade head` → no-op downgrade + idempotent re-run on PG.
6. Drop the scratch DB. If docker is unavailable, record as TECH-53 pre-flight step; sqlite tests + chain test remain the automated gate.

## 5. Atomic commit staging set

```
apps/platform-api/alembic/versions/20260727_0005_fleet_assets.py
apps/platform-api/alembic/versions/20260803_0012_native_uuid_migration.py
apps/platform-api/alembic/versions/20260805_0013_cashflow_phase1.py
apps/platform-api/alembic/versions/20260806_0014_receipt_processing_phase2.py
apps/platform-api/alembic/versions/20260806_0015_reversals_phase3.py
apps/platform-api/alembic/versions/20260806_0016_activation_phase4.py
apps/platform-api/alembic/versions/20260806_0017_fleet_asset_telemetry_backfill.py
apps/platform-api/pyproject.toml
apps/platform-api/requirements.txt
apps/platform-api/tests/test_runtime_dependency_manifests.py
apps/platform-api/tests/test_migration_0017_telemetry_backfill.py        (new)
apps/platform-api/tests/test_migration_chain_integrity.py                (new)
apps/platform-api/tests/test_migration_0013_backfill_dialect_bind.py     (new)
apps/product-web/.env.example
apps/product-web/src/lib/company-signup.ts
apps/product-web/src/lib/company-signup.test.ts
```

**NOT staged:** `.opencode/agents/vision.md`, `docs/`. Suggested message: `fix(migrations): TECH-54 — dialect-safe uuid/boolean DDL, phantom-artifact removal in 0012, idempotent 0017 telemetry backfill, dep-manifest alignment, product-web signup env guard (+ tests)`.

## 6. Verification commands

- platform-api: `..\..\.venv\Scripts\python.exe -m pytest` from `apps/platform-api` (expect 348 + new tests green; 0013 bind test red before fix ①, green after).
- product-web: `npm test` from `apps/product-web` (vitest run; existing 3 + new 2 green).

## 7. Risks

1. **Chain ordering:** 0017 is head; chain-integrity test hard-gates future revisions.
2. **sqlite vs Postgres:** 0012 remains PG-only raw SQL — sqlite scratch chains must be `create_all` + stamped, never migrated from empty. 0013/0014 `postgresql.UUID` compiles on sqlite as `UUID` (verified).
3. **Historical-edit safety:** pre-fix versions could not have run on any Postgres DB (guaranteed failures), stamped sqlite DBs never re-run edited revisions, 0005 edit is additive with 0017 parity, Supabase prod not past 0012. No data-loss path identified.
4. **0013 backfill bind (fix ①):** red on sqlite-with-data chains until guarded.
5. **Residual drift (OUT of scope, follow-up flag):** `route_schedules.assigned_asset_id` / `origin_latitude` / `origin_longitude` declared in `app/models/route.py` L18–20 but created by NO migration — exist only on `create_all` schemas, never on alembic-built PG. Open a follow-up ticket later.
6. **Deployment hygiene (ops):** Vercel must set `NEXT_PUBLIC_PLATFORM_API_URL` + `NEXT_PUBLIC_APP_CONSOLE_URL`; blank → production signup throws clear message (intended); verify on live launch (TECH-56).
7. **Manifest test granularity:** names only, not version specifiers — adequate; note for hardening.
