# Supply Chain Logistics Platform - Full Recreation Prompt

## How to use this file
- Copy everything between `BEGIN MASTER RECREATION PROMPT` and `END MASTER RECREATION PROMPT`.
- Paste it into your coding model/agent.
- The prompt is intentionally strict and fidelity-first.

---

## BEGIN MASTER RECREATION PROMPT

You are a principal full-stack engineer. Recreate a production-style monorepo called **Supply Chain Logistics Platform** with exact behavior fidelity to the specification below.

You must implement code, not stubs.

## 1) Non-negotiable constraints

1. Recreate architecture, behavior, and contracts exactly as specified.
2. Keep existing quirks unless explicitly told to improve them.
3. Do not invent files not listed in this spec.
4. Preserve API payload shapes, endpoint paths, status codes, auth gates, and role checks.
5. Preserve user-facing strings that are used by smoke tests.
6. Include tests and CI wiring exactly as described.
7. Preserve dark premium UI direction for web/ops/desktop surfaces.
8. Use the exact route prefixes and environment variable names.

## 2) Monorepo topology

Create this top-level layout:

```text
.
├── docker-compose.yml
├── package.json
├── README.md
├── .env.example
├── .github/
│   └── workflows/
│       └── ci.yml
├── apps/
│   ├── ops-console/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   ├── eslint.config.js
│   │   ├── index.html
│   │   ├── nginx.conf
│   │   ├── postcss.config.js
│   │   ├── tailwind.config.js
│   │   ├── tsconfig.json
│   │   ├── vite.config.ts
│   │   ├── vercel.json
│   │   ├── .env.example
│   │   └── src/
│   │       ├── main.tsx
│   │       ├── App.tsx
│   │       ├── index.css
│   │       ├── components/
│   │       ├── context/
│   │       ├── hooks/
│   │       ├── pages/
│   │       ├── services/
│   │       └── types/
│   ├── product-web/
│   │   ├── Dockerfile
│   │   ├── package.json
│   │   ├── next.config.mjs
│   │   ├── postcss.config.js
│   │   ├── tailwind.config.ts
│   │   ├── tsconfig.json
│   │   ├── vitest.config.ts
│   │   ├── next-env.d.ts
│   │   ├── .env.example
│   │   ├── public/
│   │   │   └── robots.txt
│   │   └── src/
│   │       ├── app/
│   │       ├── components/site/
│   │       └── lib/
│   ├── desktop/
│   │   ├── package.json
│   │   ├── README.md
│   │   ├── scripts/
│   │   │   └── ensure-electron-binary.cjs
│   │   └── src/
│   │       ├── main.cjs
│   │       ├── preload.cjs
│   │       ├── onboarding.html
│   │       └── onboarding.css
│   └── platform-api/
│       ├── Dockerfile
│       ├── pyproject.toml
│       ├── requirements.txt
│       ├── alembic.ini
│       ├── mypy.ini
│       ├── vercel.json
│       ├── api/
│       │   └── index.py
│       ├── alembic/
│       │   ├── env.py
│       │   ├── script.py.mako
│       │   └── versions/
│       ├── app/
│       │   ├── main.py
│       │   ├── api/
│       │   ├── core/
│       │   ├── db/
│       │   ├── models/
│       │   ├── repositories/
│       │   ├── schemas/
│       │   ├── services/
│       │   └── utils/
│       ├── scripts/
│       │   └── seed_data.py
│       ├── sample-data/
│       └── tests/
├── docs/
├── packages/
├── scripts/
└── supabase/
		├── config.toml
		└── migrations/
```

Important: there is no `apps/ops-console/README.md` and no `apps/platform-api/README.md` in this baseline.

## 3) Root workspace contracts

### Root `package.json`
Use npm workspaces:
- `apps/ops-console`
- `apps/product-web`
- `apps/desktop`

Include scripts:
- `dev:ops`, `dev:web`, `dev:desktop`
- `build:ops`, `build:web`, `build`
- `vercel:link`, `vercel:pull`, `vercel:pull:ops`, `vercel:pull:web`, `vercel:pull:api`
- `doctor:desktop`
- `test:ops`, `lint:ops`, `typecheck:ops`

### Root `.env.example`
Include:
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT`
- `DATABASE_URL`
- `BACKEND_PORT`, `FRONTEND_PORT`, `PRODUCT_WEB_PORT`
- `JWT_SECRET_KEY`, `JWT_ALGORITHM`, `JWT_ACCESS_TOKEN_EXPIRE_MINUTES`
- `CORS_ORIGINS`, `ALLOWED_HOSTS`, `APP_ENV`, `LOG_LEVEL`

### Root `docker-compose.yml`
Services:
1. `postgres` using `postgres:16`
2. `backend` built from `apps/platform-api/Dockerfile`
3. `frontend` built from `apps/ops-console/Dockerfile`
4. `product-web` built from `apps/product-web/Dockerfile`

Required behavior:
- Health checks on all services.
- Backend depends on healthy postgres.
- Frontend depends on healthy backend.
- Volume `pgdata` for postgres persistence.

### Root `README.md`
Document:
- Monorepo layout.
- Local Docker startup.
- Optional local non-Docker startup commands per app.
- Vercel monorepo link/pull scripts.
- Supabase migration workflow.
- Company onboarding flow.
- API capability summary.
- Test commands.
- DB backup/restore scripts.

### CI workflow `.github/workflows/ci.yml`
Jobs:
1. `backend-tests` on ubuntu-latest, Python 3.12, `pip install -e ".[dev]"`, `pytest -q`.
2. `ops-console-tests` on ubuntu-latest, Node 20, install + test + build.
3. `product-web-tests` on ubuntu-latest, Node 20, install + test + build.

## 4) Backend (`apps/platform-api`) exact requirements

### 4.1 Runtime and dependencies

`pyproject.toml`:
- project name `supply-chain-backend`
- Python `>=3.11`
- FastAPI, Uvicorn, SQLAlchemy, Alembic, Psycopg, Pydantic, pydantic-settings, python-multipart, numpy, pandas, scikit-learn, PyJWT, cryptography
- dev extras: pytest, httpx, ruff, mypy

`requirements.txt` must include all above plus `slowapi>=0.1.9`.

Fidelity quirk to preserve:
- `slowapi` appears in `requirements.txt`, but not in `pyproject` dependency list.

### 4.2 Vercel backend entrypoint

`api/index.py` should:
- prepend project root to `sys.path`
- import `app.main:app`

`vercel.json` should route all requests to `api/index.py` using `@vercel/python`.

### 4.3 App bootstrap (`app/main.py`)

Must include:
- FastAPI app title `Supply Chain Logistics API`, version `1.0.0`
- SlowAPI limiter:
	- default `200/minute` only when env is not development/test
	- no default limits in development/test
- SlowAPI middleware + 429 handler returning `{ "detail": "Too many requests" }`
- CORS middleware:
	- `allow_origins=settings.cors_origins`
	- `allow_credentials='*' not in settings.cors_origins`
	- `allow_methods=['*']`, `allow_headers=['*']`
- TrustedHost middleware when `allowed_hosts` exists
- custom request context middleware that:
	- injects `X-Request-ID` (incoming header or generated UUID)
	- adds security headers:
		- `X-Content-Type-Options: nosniff`
		- `X-Frame-Options: DENY`
		- `Strict-Transport-Security: max-age=31536000; includeSubDomains`
		- `Referrer-Policy: strict-origin-when-cross-origin`
		- `Permissions-Policy: geolocation=(), microphone=(), camera=()`
	- records HTTP metrics
	- structured logs request completion with duration
- include API router under `/api/v1`
- `/health` endpoint probes DB with `SELECT 1` and returns:
	- `status`: `ok` or `degraded`
	- `db`: `ok` or `unavailable`
	- `env`: current app env

### 4.4 Core config (`app/core/config.py`)

Implement `Settings` via `BaseSettings`:
- parse comma-separated env vars for:
	- `cors_origins`
	- `allowed_hosts`
	- `blocked_public_email_domains`
- `effective_database_url`:
	- use `DATABASE_URL` when set
	- fallback sqlite in development/test
	- raise in non-dev without DATABASE_URL
- `effective_jwt_secret_key`:
	- use JWT secret when set
	- require length >= 32 in non-dev/test
	- fallback dev secret in development/test

### 4.5 DB layer

Implement:
- `app/db/base.py` DeclarativeBase class `Base`
- `app/db/custom_types.py` custom `UUIDType`:
	- postgres dialect uses native UUID
	- others use CHAR(36)
- `app/db/session.py`:
	- engine with pre_ping
	- postgres pool tuning when URL starts with postgres
	- sqlite foreign_keys pragma on connect
	- `SessionLocal`
	- `get_db` dependency

### 4.6 Model set (exact entities and key constraints)

Use `UUIDTimestampMixin` (`id`, `created_at`) from `app/models/common.py`.

Create these SQLAlchemy models:

1. `User`
- unique/indexed `username`
- unique/indexed nullable `email`
- `password_hash`, `role`, `is_active`

2. `Organization`
- `name`, unique/indexed `slug`, `primary_email_domain`
- `subscription_tier`, `subscription_status`
- `preferred_ai_provider`, `preferred_ai_key_id`
- `is_active`, `updated_at`

3. `OrganizationMembership`
- unique constraint on `(organization_id, user_id)`
- fields `role`, `is_active`, `updated_at`

4. `Warehouse`
- unique/indexed `code`
- address/location/capacity fields
- nullable `organization_id`
- relationships to inventory and orders

5. `Item`
- unique/indexed `sku`
- `name`, `category`, `unit_cost`, `reorder_level`, optional `temperature_threshold`
- nullable `organization_id`

6. `Inventory`
- unique constraint `uq_inventory_warehouse_item` on `(warehouse_id, item_id)`
- `quantity_on_hand`, `safety_stock`, `updated_at`
- nullable `organization_id`

7. `HistoricalOrder`
- `order_date` indexed
- foreign keys to warehouse/item
- optional `organization_id`
- `quantity`, `unit_price`, `customer_region`, optional weather features

8. `FleetAsset`
- unique/indexed `vehicle_code`
- driver info, capacity, status, last telemetry

9. `RouteSchedule`
- route metadata, objective/cost/distance/duration, status
- fk `start_warehouse_id`, optional assigned asset
- has `RouteStop` children

10. `RouteStop`
- fk to route schedule
- sequence, warehouse, arrival/departure, load, notes

11. `RouteOptimizationRun`
- stores scenario run summary + JSON snapshots
- fields for deliveries, weights, stops, unassigned deliveries
- optional `persisted_schedule_id`, `actor_user_id`, `organization_id`
- carbon fields: `minimize_carbon_footprint`, `co2_saved_kg`

12. `Shipment`
- unique/indexed `shipment_no`
- lifecycle timestamps, status, location, delay reason, POD ref
- optional route schedule association
- include `scope_3_emissions_kg`

Fidelity quirk to preserve:
- `destination_warehouse_id` is declared as string-mapped field with FK to warehouses, not with UUIDType.

13. `Alert`
- type/severity/status/title/message
- optional related entity references
- acknowledge/resolve metadata
- optional JSON payload

14. `ReplenishmentPlan`
- demand and suggestion fields
- pending/approved/rejected workflow fields

15. `ProviderApiKey`
- org/user refs
- `provider_name`, `key_name`, `masked_key`, `encrypted_key`, `status`, `revoked_at`

16. `OrganizationUsageCounter`
- `(organization_id, metric, period_start)` unique
- `period_end`, `used_units`, `updated_at`

17. `AuditEvent`
- event metadata + optional JSON payload

18. `MeteredEvent`
- organization-scoped usage event record

19. `DockAppointment`
- warehouse/truck scheduling fields

20. `FreightInvoice`
- order_id/carrier/rates/variance/status

21. `Feedback`
- category/message/user_email

Also export model imports in `app/models/__init__.py`.

### 4.7 Repositories

Implement repository classes for users, organizations, memberships, warehouses, items, inventory, orders, shipments, routes.

Important repository behavior:
- `InventoryRepository.upsert` uses postgres `insert ... on conflict do update` on `uq_inventory_warehouse_item`.
- `MembershipRepository.get_active_membership` should support optional org filter and newest-first lookup.
- `MembershipRepository.get_organization_id_for_user` should return earliest active membership org.

### 4.8 Security/auth services

Implement `app/services/security.py`:
- PBKDF2 SHA-256 password hashing format `pbkdf2_sha256$salt$hash`
- verify via constant-time compare
- JWT creation/decoding (`sub`, `role`, `iat`, `exp`)
- org-aware token function adding `org_id`
- provider-key encryption with Fernet key derived from SHA-256(seed)
	- seed is `PROVIDER_KEY_ENCRYPTION_SECRET` fallback to JWT secret
- `mask_provider_key` keeps first 4 and last 4 chars

Implement `app/services/authz.py`:
- `ensure_role(current_role, allowed_roles)` raising ValueError on failure.

Implement `app/api/security.py`:
- auth bearer optional + cookie fallback
- cookie name: `supply_chain_token`
- `get_current_user`
- `require_roles(...)`
- membership resolution via `X-Organization-Id` header
- org role gate helper

### 4.9 Audit and metering services

`app/services/audit.py`:
- `record_audit_event(...)`
- sanitize UUIDs inside payload recursively
- infer actor org via membership repository when possible

`app/services/metering.py`:
- monthly usage window helper (`period_start` = first day, `period_end` = last day)
- `record_usage_for_user_membership` increments org usage counter for metric `delivery_tasks` by default

### 4.10 Routing/forecast/weather/live helpers

`app/services/routing.py`:
- dataclasses `Node`, `Delivery`
- weighted leg cost based on distance/time/cost weights
- dijkstra utility
- greedy optimization honoring vehicle capacity and max stops
- return structure includes:
	- totals
	- stops with coordinates and ETA
	- unassigned deliveries

`app/services/forecasting.py`:
- build weekly training frame from order rows
- RandomForestRegressor pipeline with OneHotEncoder for categorical features
- hash-based model cache key from frame signature
- cap cache size at 10
- non-negative clipping on predictions
- expose:
	- `forecast_weekly_demand(...)`
	- `calculate_arrival_probability(...)`

`app/services/weather.py`:
- deterministic pseudo-weather based on date/lat/lon

`app/services/live_feed.py`:
- build payload shape:
	- `type: live_update`
	- `server_time`
	- `inventory_overview`
	- `route_summaries`
	- `forecast_preview`

Fidelity quirk to preserve:
- keep `app/services/rerouting.py` logic that references route fields not present in `RouteSchedule` (`destination_warehouse_id`, `carrier`).

### 4.11 API router registry

In `app/api/router.py`, mount these routers under `/api/v1`:
- auth, warehouses, items, inventory, orders, ingestion, forecast, routes, live, ops, shipments, alerts, planning, subscriptions, providers, weather, invoices, feedback

### 4.12 Endpoint contracts (must match)

#### Auth (`/auth`)

1. `POST /register`
- if users already exist:
	- requires admin auth
	- non-admin forbidden
- if no users exist:
	- first registered user is forced role `admin`
- unique username check

2. `POST /company-signup`
- request: company_name, company_email, password, optional full_name, subscription_tier
- reject public email domains from blocked list
- ensure unique email/username collision check
- create Organization + User(role=admin) + OrganizationMembership(role=owner)
- issue org-aware token
- set auth cookie (`supply_chain_token`, httponly, strict samesite, secure except dev/test)
- return user+organization+token payload

3. `POST /login`
- supports `identifier` or `username`
- case-normalizes identifier to lowercase
- issues token and sets cookie

4. `GET /me`

5. `GET /users` admin-only

6. `POST /logout` clears auth cookie

7. `GET /token` returns short-lived token for websocket auth bootstrap

Rate limits:
- login 10/min
- register 5/min
- company-signup 3/min
- in development/test all become 10000/min

#### Warehouses (`/warehouses`)
- `GET /`
- `POST /` operator/admin
- `GET /{warehouse_id}`
- `PATCH /{warehouse_id}` operator/admin

#### Items (`/items`)
- same CRUD-lite shape as warehouses

#### Inventory (`/inventory`)
- `GET /` by org membership
- `PUT /` upsert by warehouse code + sku
- `GET /overview` aggregated utilization by warehouse

#### Orders (`/orders`)
- `GET /` by org membership with pagination
- `POST /` operator/admin, resolves warehouse code + sku, writes org-scoped order

#### Ingestion (`/ingestion`)

CSV imports (operator/admin):
- `POST /warehouses-csv`
- `POST /items-csv`
- `POST /fleet-assets-csv`
- `POST /inventory-csv`
- `POST /orders-csv`

All CSV endpoints must:
- reject non-CSV files
- validate required columns
- process row-by-row
- accumulate row-level errors as `row {line}: ...`
- return counts: processed/created/updated/errors

Telemetry:
- `POST /telematics` updates fleet asset lat/lon/last_telemetry_at by `asset_id==vehicle_code`
- `POST /iot-telemetry` creates `temperature_excursion` alert when payload temp exceeds item threshold

#### Forecast (`/forecast`)
- `POST /weekly-demand`
- reads historical orders joined with warehouse/item
- fills missing weather via simulated weather service
- returns model name + forecast points

#### Routes (`/routes`)

1. `POST /optimize`
- requires operator/admin
- run greedy optimization
- optional carbon minimization path:
	- re-run with distance-only weights
	- compare emissions (`app/utils/emissions.py`)
	- choose eco route only if lower emissions
- record usage units equal to number of deliveries
- persist history run always
- optionally persist route schedule + route stops
- record audit event `route.optimized`

2. `GET /schedules`

3. `GET /schedules/{schedule_id}`

4. `GET /history`

5. `GET /history/{run_id}`

#### Live (`/live`)
- websocket `GET /updates`
- first client message must be JSON containing `token`
- invalid/missing auth closes with code 1008
- on success: emit live snapshot every 5 seconds

#### Ops (`/ops`)

1. `GET /ready` DB readiness
2. `GET /metrics` admin-only, returns in-memory app metrics snapshot
3. `GET /audit-timeline`
4. `GET /exception-feed`
	 - merge open/acknowledged alerts
	 - pending replenishment plans
	 - route optimization runs with unassigned deliveries
	 - include summary counts
5. `POST /live-eta`
	 - create/update dock appointment
	 - if ETA slip >45 minutes, status moves to `rescheduled`
6. `GET /dock-appointments`

#### Shipments (`/shipments`)

1. `GET /`
2. `POST /`
	 - unique shipment_no
	 - validates warehouse codes + sku
	 - optional route schedule check
	 - status starts `planned`
	 - audit event `shipment.created`
3. `GET /{shipment_id}`
4. `POST /{shipment_id}/status`
	 - delayed status requires `delay_reason`
	 - delayed status auto-creates delayed-shipment alert when no open/acknowledged alert exists
	 - delivered status auto-sets `actual_delivery` when omitted
	 - audit event `shipment.status_updated`

#### Alerts (`/alerts`)

1. `GET /`
2. `POST /` manual alert creation
3. `POST /scan`
	 - low stock alerts for quantity < safety stock
	 - delayed shipment alerts
	 - queue rerouting task for delayed >30 minutes
4. `POST /{alert_id}/acknowledge`
5. `POST /{alert_id}/resolve`
6. `POST /{alert_id}/auto-resolve`
	 - requires rerouting payload exists
	 - can update linked shipment route/status

#### Planning (`/planning`)

1. `GET /replenishment`
2. `POST /replenishment/generate`
	 - operator/admin
	 - derive avg weekly demand from historical orders window
	 - skip suggestions <= 0
	 - skip if pending plan already exists for same warehouse+item
	 - status `pending_approval`
3. `POST /replenishment/{plan_id}/approve` admin-only
4. `POST /replenishment/{plan_id}/reject` admin-only

#### Subscriptions (`/subscriptions`)

1. `GET /plans`
2. `GET /me`
3. `GET /usage/me`
4. `POST /usage/record`
5. `POST /select-tier`

Plan quotas to preserve:
- starter:
	- delivery_tasks: included 2500, overage 0.2
	- route_optimizations: included 50, overage 1.5
- scale:
	- delivery_tasks: included 5000, overage 0.16
	- route_optimizations: included 250, overage 1.0
- enterprise:
	- unlimited (None/None)

Threshold events when crossing:
- 80% (`approaching_limit`)
- 100% (`limit_reached`)
- first overage (`overage`)

#### Providers (`/providers`)

1. `GET /keys`
2. `POST /keys`
	 - reject duplicate active key by org+provider+key_name
	 - encrypt key and store masked version
3. `POST /keys/{key_id}/revoke`
4. `POST /keys/{key_id}/test`
	 - active required for success path
	 - simple shape check length >=12
5. `GET /preference`
6. `POST /preference`
	 - set preferred provider and key id on organization

#### Weather (`/weather`)
- `GET /risk-zones`
- generate simulated grid around Addis Ababa region (lat 8.0-10.0, lon 37.5-39.5 step 0.4)
- include disruption-driven severity and rectangles
- if no zones, return fallback mock zone

#### Invoices (`/invoices`)
- `GET /`
- `POST /upload` CSV:
	- required: `order_id`, `carrier_id`, `actual_rate`
	- compute `quoted_rate = order.quantity * order.unit_price`
	- `variance = actual_rate - quoted_rate`
	- status `mismatch_flagged` when variance != 0 else `matched`

#### Feedback (`/feedback`)
- `POST /` open endpoint for feedback creation

### 4.13 Schemas

Implement Pydantic schemas for:
- auth, subscription, provider, route, shipment, alert, planning, ops_insights, ingestion, forecast, invoice, feedback, dock_appointment, warehouse, item, inventory, order, common

Key enum values to preserve:
- user roles: `admin`, `operator`, `viewer`
- organization roles: `owner`, `admin`, `operator`, `viewer`
- shipment statuses: `planned`, `in_transit`, `delivered`, `delayed`, `cancelled`
- alert statuses: `open`, `acknowledged`, `resolved`

### 4.14 Alembic migrations

Provide migration chain equivalent to:
- `20260517_0001_initial.py`
- `20260518_0002_users_auth.py`
- `20260524_0003_mvp_features.py`
- `20260727_0004_multi_tenant_subscription_byok.py`
- `20260727_0005_fleet_assets.py`
- `20260727_0006_usage_metering.py`
- `20260729_0007_audit_and_route_history.py`
- `20260731_0008_carbon_footprint.py`
- `20260731_0009_add_phase_1_3_models.py`
- `20260731_0010_add_feedback_and_metered_events.py`
- `20260802_0011_add_org_id_to_core_models.py`
- `20260803_0012_native_uuid_migration.py`

## 5) Ops Console (`apps/ops-console`) exact requirements

### 5.1 Stack

Use React + TypeScript + Vite with:
- `@tanstack/react-query`
- `axios`
- `react-router-dom`
- `recharts`
- `leaflet` + `react-leaflet`

### 5.2 Env and API client

`.env.example`:
- `VITE_API_BASE_URL=/api/v1`
- `VITE_SIGNUP_URL=http://localhost:8081#signup`

`src/services/api.ts`:
- axios baseURL from env fallback `/api/v1`
- `withCredentials: true`
- localStorage org key `supply_chain_org_id`
- inject header `X-Organization-Id` on requests when present
- on 401:
	- clear org storage
	- redirect to `/login` (unless already there)

### 5.3 Auth state

`AuthContext.tsx`:
- bootstrap via `/auth/me`
- then attempt `/subscriptions/me` to infer org id
- cache websocket token via `/auth/token` retrieval
- `login()` calls `/auth/login`, then `/auth/me`, then `/subscriptions/me`
- `logout()` posts `/auth/logout`, clears local state

### 5.4 Route map and protection

`App.tsx` should lazy-load pages and use `ProtectedRoute`.

Pages and route gates:
- `/` dashboard (authenticated)
- `/login`
- `/unauthorized`
- `/routes` roles `admin|operator|viewer`
- `/upload` roles `admin|operator`
- `/shipments` roles `admin|operator|viewer`
- `/alerts` roles `admin|operator|viewer`
- `/planning` roles `admin|operator|viewer`
- `/account` roles `admin|operator|viewer`
- `/providers` roles `admin|owner|operator`

Fidelity quirk:
- frontend includes `owner` role although backend user role enum does not include `owner` for `User.role`.

### 5.5 Core pages and behavior

1. `LoginPage`
- supports standard login
- has "Create initial admin" action that calls `/auth/register` then logs in
- default demo values:
	- identifier `admin@testco.com`
	- password `admin12345`

2. `DashboardPage`
- shows KPI tiles and sections for:
	- exception feed
	- audit timeline
	- inventory/forecast charts
	- dock appointments gantt
	- freight reconciliation panel
	- feedback form
- subscribes to websocket live updates and invalidates query caches on messages

3. `RoutesPage`
- route optimizer form
- map with weather risk zones
- schedule table
- route optimization history cards

4. `ShipmentsPage`
- create shipment form
- status updates with modal for delayed reason

5. `AlertsPage`
- manual alert creation
- scan endpoint trigger
- acknowledge, resolve, auto-resolve actions

6. `PlanningPage`
- generate replenishment suggestions
- admin approve/reject workflow with rejection modal

7. `AccountPage`
- plan catalog and tier switching
- usage meter and utilization/overage visualization
- provider key create/test/revoke/preference
- audit timeline surface

8. `UploadPage`
- ordered import sequence cards:
	- Warehouses -> Items -> Fleet -> Inventory -> Orders
- mounts `CsvUploadPanel`

9. `ProvidersPage`
- provider key management with immediate post-create test

### 5.6 Data services/hook layer

Implement:
- `services/authApi.ts`
- `services/billingApi.ts`
- `services/logisticsApi.ts`
- `hooks/queries.ts`
- `hooks/useLiveUpdates.ts`

WebSocket URL behavior in `useLiveUpdates`:
- if API base is absolute http(s), derive ws(s) from it
- else derive from current browser origin

### 5.7 Styling direction

Use premium dark visual style with:
- CSS gradients + grid overlays
- fonts: IBM Plex Sans + Space Grotesk
- animated skeletons and subtle hover/entrance motion
- Tailwind + custom utility classes from `index.css`

`vite.config.ts`:
- enable proxy `/api` -> `http://localhost:8000` with `ws: true`
- manual chunk splitting for d3/recharts/leaflet bundles

### 5.8 Ops Docker + deployment

`apps/ops-console/Dockerfile`:
- multi-stage build (node build -> nginx runtime)
- healthcheck via `wget`

`apps/ops-console/vercel.json`:
- SPA rewrite to `/index.html`

## 6) Product Web (`apps/product-web`) exact requirements

### 6.1 Stack

Use Next.js 14 App Router + React 18 + Tailwind + framer-motion + zod + react-hook-form + optional Supabase.

### 6.2 Key config

`next.config.mjs`:
- `reactStrictMode: true`
- `output: 'standalone'`
- optimize package imports for `lucide-react`

`.env.example` must include:
- `NEXT_PUBLIC_SITE_URL`
- `NEXT_PUBLIC_CONTACT_FORM_ENDPOINT`
- `NEXT_PUBLIC_DESKTOP_DOWNLOAD_URL`
- `NEXT_PUBLIC_DOCS_URL`
- `NEXT_PUBLIC_APP_CONSOLE_URL`
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `NEXT_PUBLIC_PLATFORM_API_URL`

### 6.3 Layout and metadata

`src/app/layout.tsx`:
- use `Inter` and `Space_Grotesk` from `next/font/google`
- site metadata for SEO/OpenGraph/Twitter
- `metadataBase` from env site URL fallback `https://freightpilot.com`
- include `MotionProvider` and `SiteChrome`

### 6.4 Global visual system

`src/app/globals.css`:
- dark theme (`color-scheme: dark`)
- layered backgrounds, glass components, focus styles, skip-link

`src/components/site/site-chrome.tsx`:
- sticky glass nav
- desktop + mobile nav handling
- animated mobile menu
- back-to-top button
- footer sections

### 6.5 Required routes/pages

Create routes:
- `/` home
- `/platform`
- `/technology`
- `/pricing`
- `/launch`
- `/contact`
- `loading.tsx`
- `not-found.tsx`
- `sitemap.ts`

Page-level behavior:
- heavy marketing narrative for logistics operations
- premium card layout and animated sections
- CTA links to launch, docs, console, desktop as appropriate

### 6.6 Company signup logic

Implement `src/lib/company-signup.ts`:
- if Supabase env vars are configured:
	- use Supabase auth signUp
	- optionally upsert `company_profiles`
- else fallback to platform API:
	- `POST {NEXT_PUBLIC_PLATFORM_API_URL}/auth/company-signup`
- normalize API error body text (including JSON-like strings)

Implement `src/components/site/signup-form.tsx`:
- schema validated launch form
- tier choices starter/scale/enterprise
- success/error banner behavior

### 6.7 Contact form

`src/components/site/contact-form.tsx`:
- submit to env endpoint or fallback formsubmit URL
- append `_subject` and `_captcha=false`
- render success state card after submit

### 6.8 Site content module

Implement a centralized `site-content.ts` exporting:
- nav config
- pricing tiers
- FAQ
- testimonials
- trust signals
- feature cards
- deep links from env defaults

### 6.9 Product web tests

Implement `src/app/home.smoke.test.tsx` (Vitest server rendering) with assertions:
- home contains:
	- `Plan routes, manage exceptions, and launch operations from one control layer.`
	- `Launch your workspace`
	- `Explore the platform`
- platform/technology/pricing contain `FreightPilot` and html length > 500
- launch contains `Set up the workspace and launch operations in stages` and html length > 500
- contact contains `Send a message` and html length > 500

### 6.10 Product web Docker

`apps/product-web/Dockerfile`:
- deps stage
- build stage
- runtime stage serving Next standalone `server.js` on port 80
- healthcheck via `wget`

Fidelity note:
- there is no `apps/product-web/vercel.json` in this baseline.

## 7) Desktop (`apps/desktop`) exact requirements

### 7.1 Package and scripts

`package.json`:
- main `src/main.cjs`
- dev dependency `electron@^31.0.2`
- scripts:
	- `postinstall`, `predev`, `prestart` run `scripts/ensure-electron-binary.cjs`
	- `dev`, `start` run `electron .`
	- `doctor` runs `node scripts/ensure-electron-binary.cjs --check`

### 7.2 Electron binary repair script

`scripts/ensure-electron-binary.cjs` behavior:
- verify electron package and runtime dist state (`dist/version`, `path.txt`, executable presence)
- if broken:
	- download artifact with `@electron/get`
	- extract
	- Windows branch uses native `tar -xf` fallback (Node24/extract-zip reliability issue)
- support `--check` mode and fail if invalid

### 7.3 Desktop main process

`src/main.cjs`:
- persists config at userData:
	- `freightpilot-desktop-config.json`
- persists setup window bounds:
	- `freightpilot-window-state.json`
- default config urls:
	- ops console default `https://ops-console-azure.vercel.app/login`
	- product signup default `https://product-web-chi.vercel.app#signup`
	- docs default `https://product-web-chi.vercel.app`
- URL sanitization must only permit http/https
- reachability test via fetch with 8s timeout
- setup window and console window creation
- application menu entries:
	- open control tower
	- open docs
	- setup window
- IPC channels:
	- `desktop:get-config`
	- `desktop:save-config`
	- `desktop:test-console`
	- `desktop:open-external`
	- `desktop:launch-console`

### 7.4 Preload bridge

`src/preload.cjs` exposes `window.freightPilotDesktop` methods matching IPC handlers.

### 7.5 Onboarding UI contracts

`src/onboarding.html` + `onboarding.css` must implement:
- premium launch cockpit interface
- step machine with these milestone keys:
	- `createdAccount`
	- `connectedConsole`
	- `invitedTeam`
	- `importedData`
	- `launchedLive`
- role checkboxes:
	- dispatcher/data/security ownership
- readiness score formula:
	- completed steps weighted 70
	- role signoff weighted 20
	- URL validity weighted 10
- risk list output and celebration banner on completion
- save/test/launch actions integrated with preload bridge

Fidelity quirk:
- desktop README may describe localhost default OPS_CONSOLE_URL, but main runtime defaults point to hosted Vercel URL.

## 8) Infrastructure and deployment wiring

### 8.1 Backend Dockerfile

Multi-stage python 3.12-slim build/runtime:
- install deps with editable install
- copy app/alembic files
- runtime command:
	- `alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000`

### 8.2 Vercel model

Root scripts for monorepo link/pull should target:
- ops-console
- product-web
- platform-api

Ops has `vercel.json` rewrite.
Platform-api has `vercel.json` with python build and catch-all route.

### 8.3 Supabase

Include `supabase/migrations/20260727153410_company_onboarding_and_profiles.sql` (company onboarding/profile storage and RLS setup).

## 9) Tests that must exist and pass

### 9.1 Backend test suite includes

- `test_auth.py`
	- password hash roundtrip
	- token encode/decode
	- expired token rejection

- `test_auth_api.py`
	- register/login/me flow
	- admin-only users endpoint checks
	- first-user bootstrap admin behavior

- `test_company_onboarding_api.py`
	- full company-signup -> subscription -> provider key lifecycle
	- reject public email domains
	- login by email identifier

- `test_forecasting.py`
	- training frame aggregation
	- positive horizon predictions

- `test_live_payload.py`
	- live payload shape

- `test_routes_authz.py`
	- role guard checks

- `test_routing.py`
	- distance function and capacity constraints

- `test_websocket_live.py`
	- websocket closes on missing token
	- websocket emits `live_update`

- `test_ops.py`
	- `/ops/ready` success
	- `/ops/metrics` authz

- `test_rbac_endpoints.py`
	- viewer cannot create warehouse
	- operator can create warehouse
	- token required

- `test_route_usage_metering_api.py`
	- route optimization auto-records usage count by deliveries
	- no membership path does not crash

- `test_subscription_metering_api.py`
	- threshold events at 80/100/overage
	- enterprise unlimited behavior
	- active org membership required

- `test_mvp_features_api.py`
	- shipment delay reason validation
	- delayed alert creation
	- alert scan+ack+resolve
	- replenishment generation and approval flow

- `test_operator_insights_api.py`
	- route history + audit timeline
	- exception feed merges multiple sources

### 9.2 Product web tests

`home.smoke.test.tsx` as described above.

### 9.3 Ops tests

Use Vitest command wiring from package scripts.

## 10) Known quirks to preserve for exact parity

1. `requirements.txt` includes `slowapi`; `pyproject.toml` does not explicitly include it.
2. `Shipment.destination_warehouse_id` typing is inconsistent (string mapped with warehouse FK).
3. `services/rerouting.py` references route fields not present on `RouteSchedule` (`destination_warehouse_id`, `carrier`).
4. `services/audit.py` includes an autonomous late-pickup resolver path not aligned with main alert enums (`LATE_PICKUP`, `AUTO_RESOLVED`).
5. Frontend providers route allows `owner` role though backend user role enum is `admin|operator|viewer`.

Do not silently "clean these up" unless explicitly asked for an improved version.

## 11) Exact command surface to support

From repo root:

```bash
npm run dev:ops
npm run dev:web
npm run dev:desktop
npm run build:ops
npm run build:web
npm run build
npm run test:ops
npm run lint:ops
npm run typecheck:ops
npm run vercel:link
npm run vercel:pull
npm run doctor:desktop
```

Backend local:

```bash
cd apps/platform-api
python -m pip install -e ".[dev]"
alembic upgrade head
python scripts/seed_data.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
pytest -q
```

Docker local:

```bash
docker compose up -d --build
```

## 12) Acceptance checklist (must all pass)

1. Backend starts, migrations apply, `/health` returns ok/degraded shape.
2. Auth cookie + bearer flows both work.
3. Company signup creates org+owner membership and returns token payload.
4. Ops console login works and persists org id in localStorage.
5. Websocket live updates stream every 5s and frontend receives them.
6. Route optimization persists history and usage metering increments by delivery count.
7. Alert scan generates low-stock and delayed shipment alerts as applicable.
8. Planning generate/approve/reject works with role gates.
9. Provider key create/test/revoke/preference flows work.
10. Product-web smoke tests pass with required copy strings.
11. Desktop onboarding saves config, tests console URL, and launches control tower.
12. CI jobs succeed for backend, ops-console, and product-web.

## 13) Output format expected from the coding agent

When implementing this prompt, return:
1. A complete repository tree with all files.
2. Full source code (no placeholders).
3. Commands run and test outputs.
4. Any fidelity deviations explicitly listed.

Do not return conceptual plans only. Return implementation.

## END MASTER RECREATION PROMPT

