# Supply Chain Logistics Platform Monorepo

Full-stack logistics platform with an operations console, API backend, and a product marketing website.

## What is included

- Operations console for logistics workflows (inventory, planning, routing, alerts)
- API backend for data, forecasting, and optimization endpoints
- Product website for company signup, desktop download CTAs, and product positioning
- Desktop shell for dispatch/operator teams (Electron)
- Dockerized local stack for backend, operations UI, and product website
- Company onboarding flow: business-email signup, subscription selection, data import, and preferred AI provider selection

## Monorepo layout

- `apps/platform-api` FastAPI + SQLAlchemy + Alembic backend
- `apps/ops-console` React + Tailwind operations frontend (Vite + TypeScript)
- `apps/product-web` Next.js + React + Tailwind product website
- `apps/desktop` Electron shell for desktop distribution
- `sample-data` CSV demo datasets for warehouses, items, inventory, and orders
- `scripts` backup and restore scripts for PostgreSQL
- `docs` architecture and roadmap documentation

## Tech stack

- Backend: FastAPI, SQLAlchemy, Alembic, Pydantic, psycopg
- Frontend (ops): React, Recharts, React Router, Tailwind
- Product web: Next.js, React, Tailwind
- Database: PostgreSQL
- Forecasting: scikit-learn and pandas

## Production endpoints

- Product website (Vercel): https://product-web-chi.vercel.app
- Operations console (Vercel): https://ops-console-azure.vercel.app
- Backend API (Vercel): https://platform-api-smoky.vercel.app
- Supabase project ref: `azljjrjatdpkcvjbpztn`
- Supabase API base: `https://azljjrjatdpkcvjbpztn.supabase.co`

## Vercel monorepo setup

This repository is linked to Vercel as a monorepo with one project per deployable app:

- `apps/product-web` -> `product-web` (Next.js preset, root directory `apps/product-web`)
- `apps/ops-console` -> `ops-console` (Vite preset, root directory `apps/ops-console`, SPA rewrite in `apps/ops-console/vercel.json`)
- `apps/platform-api` -> `platform-api` (Python serverless app, root directory `apps/platform-api`, request routing in `apps/platform-api/vercel.json`)

From repo root, relink the repository to the same Vercel projects:

```bash
npm run vercel:link
```

Pull production environment variables for all three Vercel projects:

```bash
npm run vercel:pull
```

Pull a single project only:

```bash
npm run vercel:pull:web
npm run vercel:pull:ops
npm run vercel:pull:api
```

Deploy each Vercel-backed section from the monorepo root:

```bash
npm run vercel:deploy:web
npm run vercel:deploy:ops
npm run vercel:deploy:api
```

Vercel CLI generates local environment files under `.vercel/.env.production.local` when you run `vercel pull`. Those files are machine-local deployment state and should stay uncommitted.

## Supabase CLI workflow (database + auth)

From repo root:

```bash
npx supabase link --project-ref azljjrjatdpkcvjbpztn --password <db-password>
npx supabase db push --linked --yes
```

Apply backend schema migrations to the same Supabase database:

```bash
cd apps/platform-api
set DATABASE_URL=postgresql+psycopg://postgres.azljjrjatdpkcvjbpztn:<db-password>@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require
python -m alembic upgrade head
```

Applied migration in this repo:

- `supabase/migrations/20260727153410_company_onboarding_and_profiles.sql`

This migration provisions:

- `public.company_profiles` table for company onboarding state
- Row-level security policies tied to `auth.uid()`
- Update timestamp trigger for profile mutations

## Root workspace scripts

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
```

## Local development

### 1) Configure environment

```bash
copy .env.example .env
```

### 2) Start full Docker stack

```bash
docker compose up -d --build
```

Services:
- Operations console: `http://localhost` (or `${FRONTEND_PORT}`)
- Product website: `http://localhost:8081` (or `${PRODUCT_WEB_PORT}`)
- API backend: `http://localhost:8000` (or `${BACKEND_PORT}`)
- PostgreSQL: `${POSTGRES_PORT}`

### 3) Run backend locally without Docker (optional)

```bash
cd apps/platform-api
copy .env.example .env
python -m pip install -e ".[dev]"
alembic upgrade head
python scripts/seed_data.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4) Run operations console locally without Docker (optional)

```bash
cd apps/ops-console
copy .env.example .env
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

### 5) Run product website locally without Docker (optional)

```bash
cd apps/product-web
copy .env.example .env
npm install
npm run dev
```

### 6) Run desktop shell locally (optional)

```bash
cd apps/desktop
npm install
npm run start
```

The desktop package now validates and repairs Electron runtime artifacts during install and before startup.

You can run a standalone runtime health check with:

```bash
npm --prefix apps/desktop run doctor
```

If your machine still reports an Electron install failure, run a clean reinstall:

```bash
npm --prefix apps/desktop remove electron
npm --prefix apps/desktop install electron@31.0.2
```

## Product website environment variables

`apps/product-web/.env.example` contains:

- `NEXT_PUBLIC_DESKTOP_DOWNLOAD_URL`: desktop installer/download center URL
- `NEXT_PUBLIC_DOCS_URL`: docs portal URL
- `NEXT_PUBLIC_APP_CONSOLE_URL`: operations console URL
- `NEXT_PUBLIC_PLATFORM_API_URL`: backend API base URL used by inline company signup form
- `NEXT_PUBLIC_SUPABASE_URL`: optional Supabase project URL for auth-backed signup
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`: optional Supabase publishable key

## Company onboarding flow

1. Open product site and use the company signup form with a business email domain.
2. Download and launch desktop app (or open ops console directly).
3. Sign in with company credentials.
4. Go to Account page to choose subscription tier.
5. Add provider API keys and set the preferred provider for dashboard AI workflows.
6. Go to CSV Upload and import, in order: warehouses, items, fleet assets (cars + drivers), inventory, orders.

## API capabilities (current)

Base API prefix: `/api/v1`

- Auth: register/login/me/users
- Company onboarding: `POST /auth/company-signup` (company email + workspace bootstrap)
- Warehouses, items, inventory CRUD and overview
- Orders ingestion and CSV uploads
- Forecasting endpoints
- Routing optimization and schedule views
- Live feed, shipment lifecycle, alerts, replenishment planning
- Operations readiness and metrics endpoints
- Subscription management: plans listing, select tier, tenant subscription state
- Usage metering: monthly task counters with threshold events at 80%, 100%, and overage, automatically recorded from route optimization delivery tasks and available via `POST /subscriptions/usage/record` and `GET /subscriptions/usage/me`
- Provider key management: BYOK create/list/test/revoke with encrypted storage
- Provider preference: set/get organization preferred AI provider key used by dashboard workflows
- Expanded onboarding ingestion endpoints: warehouses, items, fleet assets, inventory, and orders CSV imports

## Testing

### Backend

```bash
cd apps/platform-api
pytest -q
```

### Operations console

```bash
cd apps/ops-console
npm run test
```

## Operations scripts

- PowerShell backup: `./scripts/db_backup.ps1 -OutputFile backup.sql`
- PowerShell restore: `./scripts/db_restore.ps1 -InputFile backup.sql`
- Bash backup: `./scripts/db_backup.sh backup.sql`
- Bash restore: `./scripts/db_restore.sh backup.sql`

## Seed and demo data

CSV examples live in `sample-data`.

```bash
cd apps/platform-api
python scripts/seed_data.py
```

Default seeded users:
- `admin/admin12345`
- `operator/operator12345`
- `viewer/viewer12345`

Default seeded user emails:
- `admin@testco.com`
- `operator@testco.com`
- `viewer@testco.com`

Extra onboarding sample:
- `sample-data/fleet_assets.csv`

## Roadmap for desktop B2B SaaS

See `docs/desktop-b2b-roadmap.md` for recommended next additions:

- Multi-tenant organization model
- BYOK API key vault and provider adapter layer
- Desktop shell packaging and secure updates
- Audit trails, metering, and enterprise governance

## Research artifacts

- `docs/competitive-landscape-2026.md`: evidence-based benchmark of comparable logistics platforms and the rationale behind the latest product-web and desktop onboarding overhaul.
- `docs/market-dominator-overhaul-implementation.md`: implemented business-model, website, ops-console, and desktop changes derived from the market-dominator benchmark.
