# TECH-57 + TECH-58 — Multi-Tenant Org-Scoping Fixes (Phase 6)

## 1. Goal

Eliminate cross-organization data leakage and the `MultipleResultsFound → 500` on route optimization (`TECH-57`, P0) and make warehouses/items CRUD org-scoped with org stamping on create (`TECH-58`, P1), preserving every response schema and the org-less pass-through contract established in Phase 4.

## 2. Verified Facts (evidence, read from source)

| Site | Current behavior | Verdict |
|---|---|---|
| `routes.py` L44 `select(Warehouse)` | Global — nodes include every org's warehouses | **Fix** (TECH-57) |
| `routes.py` L113 origin select | Global `Warehouse.code.in_(...)` — may pull rows from other orgs for the audit `data_origin` | **Fix** (TECH-57) |
| `routes.py` L151 `select(Warehouse).where(code==...).scalar_one()` | `MultipleResultsFound → 500` when 2+ orgs hold identical seeded codes (WH-001..003 per org, `data_origin='sample'`) and `persist_schedule=true` (schema default) | **Fix** (TECH-57) |
| `routes.py` L168 `scalar_one_or_none()` per stop | Same global collision; binds `RouteStop.warehouse_id` to a possibly-other-org row | **Fix** (TECH-57) |
| `routes.py` L106 `organization_id = resolve_actor_organization_id(db, actor)` | Already computed — but AFTER the global queries at L44/L113; must move up and be reused | **Fix** (TECH-57) |
| `warehouses.py` L23 list / L35 create pre-check / L52 get / L67 update; `items.py` identical | No org filter anywhere; create never stamps `organization_id`; pre-check is global (false 409 across orgs, or IntegrityError 500 on `uq_warehouses_org_code` / `uq_items_org_sku`) | **Fix** (TECH-58) |
| `inventory.py` (77 lines) | **Already scoped** (list_by_org / org-scoped upsert / stamps org) | **Exclude** |
| `orders.py` (64 lines) | **Already scoped** (list_by_org / org-scoped create) | **Exclude** |
| Fleet assets | **No CRUD endpoint exists** (no router mount) | **Exclude** |
| `resolve_actor_organization_id(db, user)` | Soft: first active membership's org or `None`; never raises | Reuse as-is |
| `require_writable_workspace` | Soft; `writable.organization_id` is the org on write endpoints | Reuse for stamping |
| Repos | `get_by_code(code, org=None)` / `get_by_sku(sku, org=None)` already org-conditional | Reuse pattern; no repo changes |
| Models | `organization_id` nullable UUID + org-scoped unique constraints | No model changes |
| Schemas | No `organization_id` in read responses | No schema changes; stamp assertions via DB |
| Phase 4 precedent | `org_id = writable.organization_id if writable else None`; conditional `.where(...)`; stamps org | Mirror exactly |
| Test infra | `tests/conftest.py`: `db_session`, `client`, `signup_workspace(name)` → `(org_id, token)` (auto-seeds WH-001..003 / SKU-001..003 per org), `seed_csv_path` fixture | Reuse; no conftest changes |
| Existing optimize tests | ALL use `persist_schedule: false` — why the P0 never fired in CI | Unchanged; new tests cover persist=true |

**Filter semantics decision (evidence-driven):** org-present reads/optimize use `OR(model.organization_id == org, model.organization_id IS NULL)` so legacy null-org rows remain visible (required by `test_route_usage_metering_api.py` L92-116); org-less actors keep fully unfiltered queries (org-less operator tests + Phase 4 decision #5). The create duplicate pre-check uses **equality-only** to mirror NULL-distinct unique-constraint semantics (a legacy null row with the same code must NOT false-409). Cross-org identical codes remain legal; the eliminated leak is org-vs-org.

## 3. Files to Modify / Create

- `apps/platform-api/app/api/endpoints/routes.py` (modify — 4 query sites + 1 resolution move)
- `apps/platform-api/app/api/endpoints/warehouses.py` (modify — all 4 endpoints)
- `apps/platform-api/app/api/endpoints/items.py` (modify — all 4 endpoints)
- `apps/platform-api/tests/test_route_optimize_org_scoping.py` (create — TECH-57)
- `apps/platform-api/tests/test_tenant_isolation_endpoints.py` (create — TECH-58)

No model, schema, repository, security, router, or conftest changes.

## 4. Strict Import Map

- `routes.py`: `from sqlalchemy import asc, select` → `from sqlalchemy import asc, or_, select`. `resolve_actor_organization_id` already imported (L30).
- `warehouses.py`: `from sqlalchemy import select` → `from sqlalchemy import or_, select`; add `from app.services.audit import resolve_actor_organization_id`.
- `items.py`: same as warehouses.py (Item).

## 5. Step-by-Step Execution

### 5.1 `routes.py` — `optimize_routes()` (TECH-57)

1. **Move org resolution to the top** — `organization_id = resolve_actor_organization_id(db, actor)` immediately after the dependency block, before the L44 query. Remove the duplicate assignment at L106.
2. **L44 nodes query:** when `organization_id` non-`None` → `.where(or_(Warehouse.organization_id == organization_id, Warehouse.organization_id.is_(None)))`; when `None` → unfiltered. Keep the "No warehouses available" 400.
3. **L113 origin audit select:** identical conditional org filter on the `code.in_(used_codes)` query.
4. **L151 persisted start warehouse:** identical conditional org filter; keep `.scalar_one()`.
5. **L168 persisted stop warehouses:** identical conditional org filter inside the loop; keep `scalar_one_or_none()` + `continue` skip.
6. Nothing else changes (payload, metering, run record, audit, commit all untouched).

### 5.2 `warehouses.py` — all four endpoints (TECH-58)

1. **list_warehouses:** rename `_` → `actor`; resolve org; conditional `or_(...)` filter; keep skip/limit.
2. **create_warehouse:** org-scoped pre-check — `select(Warehouse).where(Warehouse.code == payload.code)` + `.where(Warehouse.organization_id == writable.organization_id)` when `writable` non-`None` (equality-only); stamp `warehouse = Warehouse(**payload.model_dump(), organization_id=writable.organization_id if writable else None)`. Keep 409/201.
3. **get_warehouse:** rename `_` → `actor`; resolve org; guard: `if not row or (organization_id is not None and row.organization_id is not None and row.organization_id != organization_id)` → 404.
4. **update_warehouse:** same guard as get; setattr loop unchanged (WarehouseUpdate has no org field).

### 5.3 `items.py` — all four endpoints (TECH-58)

Mirror warehouses.py with `Item`, `Item.sku`, `uq_items_org_sku`, `'SKU already exists'`.

## 6. Exclusions (with evidence)

inventory.py / orders.py already scoped; fleet assets have no endpoint surface; no repo/schema/model/conftest changes.

## 7. Testing Requirements (TDD — tests first)

### 7.1 `tests/test_route_optimize_org_scoping.py` (TECH-57)
Fixtures: `client`, `db_session`, `signup_workspace`, `seed_csv_path`. Helper `_optimize_payload(**overrides)` modeled on `test_activation_metering_origin.py::_OPTIMIZE_TWO` (WH-001 start; WH-002/WH-003 deliveries) with `'persist_schedule': True`.
1. `test_optimize_persist_true_org_a_returns_200_and_schedule_under_org_a` — 200; exactly one RouteSchedule; start_warehouse_id = org A's WH-001 id; all RouteStops reference org A ids.
2. `test_optimize_persist_true_org_b_returns_200_and_schedule_under_org_b` — orgs A+B (identical codes); B optimize persist → 200; two schedules total, one per org, each pointing at its own WH-001.
3. `test_optimize_start_warehouse_from_other_org_returns_404` — B creates B-only WH-X1 (201 — doubles as TECH-58 stamping check); A optimizes with start WH-X1 → 404 'start_warehouse_code not found'; no RouteSchedule created.
4. `test_single_org_optimize_persist_true_unchanged` — fresh org C only → 200 + one schedule under C.

### 7.2 `tests/test_tenant_isolation_endpoints.py` (TECH-58)
Org A + org B (identical seeded codes, distinct ids). Warehouses:
1. `test_list_warehouses_org_a_sees_only_own_rows` — 200, exactly 3, codes {WH-001,WH-002,WH-003}, ids in A's set, `organization_id == org_a` in DB; repeat for B (distinct ids).
2. `test_get_warehouse_from_other_org_returns_404` — B's id from A → 404; A's own → 200.
3. `test_create_warehouse_stamps_organization_id` — A creates WH-Z9 → 201; DB row org == org_a, data_origin == 'real'.
4. `test_create_warehouse_duplicate_code_same_org_returns_409` — WH-Z9 twice → 409; seeded WH-001 → 409.
5. `test_create_warehouse_duplicate_code_other_org_returns_201` — B creates WH-Z9 → 201, org == org_b.
6. `test_update_warehouse_other_org_returns_404_and_own_200` — PATCH B's row from A → 404; own row → 200 + DB reflects change.

Items — mirror all six with SKU-Z9, `/api/v1/items`, `'SKU already exists'`.

### 7.3 Regression guarantees (no edits to existing tests)
org-less operator create → still 201; org-less warehouses visible to member + org-less actors via `is_(None)`/unfiltered; reads with member tokens → 200; all 11 existing optimize sites use persist=false → L151/L168 untouched.

## 8. Suite + Verification Commands

- Targeted: `..\..\.venv\Scripts\python.exe -m pytest tests/test_route_optimize_org_scoping.py tests/test_tenant_isolation_endpoints.py -q` (workdir apps/platform-api)
- Full suite: `..\..\.venv\Scripts\python.exe -m pytest tests -q` (workdir apps/platform-api)
- Expected: 353 existing green + 16 new (4 TECH-57 + 12 TECH-58) = **369 passing**.

## 9. Risks & Mitigations

1. FK SET NULL orphans become globally visible under `is_(None)` — follow-up purge/tombstone; documented.
2. `resolve_actor_organization_id` returns None for org-less users (org-less pass-through preserved; Phase 4 decision #5).
3. Legacy null-org rows: reads include them (`is_(None)`); create pre-check excludes them (equality-only) — deliberate, mirrors NULL-distinct unique constraints.
4. Residual 500 edge: persist=true with BOTH an org row AND a legacy null row sharing a code → still MultipleResultsFound. Org-vs-org (the P0) eliminated; null-collision edge pre-existing — follow-up ticket, out of TECH-57 scope.
5. No response-schema implications; `organization_id` absent from read schemas (assert via DB).
6. Create race TOCTOU pre-existing (IntegrityError → 500) — not worsened; optional follow-up.

## 10. Commit Staging Set + Message

Single atomic commit (after `@qa` approval):
- `apps/platform-api/app/api/endpoints/routes.py`
- `apps/platform-api/app/api/endpoints/warehouses.py`
- `apps/platform-api/app/api/endpoints/items.py`
- `apps/platform-api/tests/test_route_optimize_org_scoping.py`
- `apps/platform-api/tests/test_tenant_isolation_endpoints.py`

Message: `fix(tenant-isolation): TECH-57/58 — org-scope route optimization and warehouse/item CRUD`
