# Supply Chain Logistics Platform (Monorepo)

Full-stack platform for inventory visibility, demand forecasting, and delivery route optimization.

Project path:
`/mnt/c/Users/nahom/Downloads/Projects/supply-chain-logistics-platform`

## Tech stack
- Frontend: React + Tailwind + Recharts (Vite + TypeScript)
- Backend: FastAPI + SQLAlchemy + Alembic
- Database: PostgreSQL
- ML: Scikit-learn (weekly demand forecasting)
- Routing: Greedy weighted heuristic + Dijkstra utility

## Monorepo structure
- `frontend/` React app
- `backend/` FastAPI app
- `sample-data/` example CSV files

## Industry-standard defaults used
Because precise domain schema/constraints were not provided, this implementation uses common logistics defaults:
1. Forecast target: weekly demand quantity per SKU per warehouse
2. Forecast horizon default: 4 weeks
3. Weather: deterministic simulated features (temperature, precipitation, disruption index)
4. Routing objective: weighted total cost (distance/time/monetary cost)
5. Route UI: list view + route optimizer form
6. API versioning: `/api/v1`
7. Auth: JWT bearer auth + role-based access control (admin/operator/viewer)
8. Local run model: native backend/frontend + PostgreSQL (Docker or native)

## Data model (implemented)
- Warehouses: code, name, address, city, state, country, latitude, longitude, capacity_units
- Items: sku, name, category, unit_cost, reorder_level
- Inventory: warehouse_id, item_id, quantity_on_hand, safety_stock
- Historical orders: order_date, warehouse_id, item_id, quantity, unit_price, customer_region, weather_* fields
- Route schedules: route_name, schedule_date, start_warehouse_id, objective, total_distance_km, total_cost, estimated_duration_min, status
- Route stops: sequence, warehouse_id, planned_arrival/departure, load_units
- Shipments: shipment_no, origin/destination warehouse, sku, quantity_units, lifecycle status, delivery proof reference
- Alerts: low-stock, delayed-shipment, and manual exception alerts with acknowledge/resolve workflow
- Replenishment plans: generated suggestions with pending approval, approve/reject decision tracking

## CSV upload formats

### Orders CSV (`POST /api/v1/ingestion/orders-csv`)
Required columns:
- `order_date` (YYYY-MM-DD)
- `warehouse_code` (string)
- `sku` (string)
- `quantity` (int)
Optional:
- `unit_price` (float)
- `customer_region` (string)
- `weather_avg_temp_c` (float)
- `weather_precip_mm` (float)
- `weather_disruption_index` (float 0..1)

### Inventory CSV (`POST /api/v1/ingestion/inventory-csv`)
Required columns:
- `warehouse_code` (string)
- `sku` (string)
- `quantity_on_hand` (int)
Optional:
- `safety_stock` (int)

## API highlights
- Warehouses CRUD: `/api/v1/warehouses`
- Items CRUD: `/api/v1/items`
- Inventory management + overview: `/api/v1/inventory`, `/api/v1/inventory/overview`
- Orders ingest/create/list: `/api/v1/orders`, CSV endpoints under `/api/v1/ingestion/*`
- Forecast: `POST /api/v1/forecast/weekly-demand`
- Route optimize + schedules: `POST /api/v1/routes/optimize`, `GET /api/v1/routes/schedules`
- Shipment lifecycle: `GET/POST /api/v1/shipments`, `POST /api/v1/shipments/{shipment_id}/status`
- Exception management: `GET/POST /api/v1/alerts`, `POST /api/v1/alerts/scan`, `POST /api/v1/alerts/{alert_id}/acknowledge`, `POST /api/v1/alerts/{alert_id}/resolve`
- Planning approvals: `GET /api/v1/planning/replenishment`, `POST /api/v1/planning/replenishment/generate`, `POST /api/v1/planning/replenishment/{plan_id}/approve`, `POST /api/v1/planning/replenishment/{plan_id}/reject`
- Health: `GET /health`
- Readiness: `GET /api/v1/ops/ready`
- Runtime metrics (admin-only): `GET /api/v1/ops/metrics`

## Quick start (Windows + WSL)

### Option A: Full Docker stack (production-style local run)
Prerequisite: Docker Desktop with WSL integration enabled.

From repo root:
```bash
copy .env.example .env
docker compose up -d
```

Services:
- Frontend + reverse proxy: `http://localhost` (or `${FRONTEND_PORT}`)
- Backend API (direct): `http://localhost:8000` (or `${BACKEND_PORT}`)
- PostgreSQL: `${POSTGRES_PORT}`

### Option B: Native PostgreSQL on Windows/WSL
Create database `supply_chain` and set `DATABASE_URL` accordingly.

### Backend run
```bash
cd backend
copy .env.example .env
python -m pip install -e ".[dev]"
alembic upgrade head
python scripts/seed_data.py
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend run
In another terminal:
```bash
cd frontend
copy .env.example .env
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Open: `http://localhost:5173`

## Testing
Backend unit tests for core modules:
```bash
cd backend
pytest -q
```

Authentication notes:
- `/api/v1/auth/register` is public only for the first user (bootstraps the first admin).
- After the first user exists, only an authenticated admin can register additional users.
- Seeded default users are created by `python scripts/seed_data.py`:
  - `admin/admin12345`
  - `operator/operator12345`
  - `viewer/viewer12345`

## Operations
- DB backup (PowerShell): `.\scripts\db_backup.ps1 -OutputFile backup.sql`
- DB restore (PowerShell): `.\scripts\db_restore.ps1 -InputFile backup.sql`
- DB backup (bash): `./scripts/db_backup.sh backup.sql`
- DB restore (bash): `./scripts/db_restore.sh backup.sql`

## Seed/demo data
Sample CSVs are in `sample-data/`:
- `warehouses.csv`
- `items.csv`
- `inventory.csv`
- `orders.csv`

Seed script:
```bash
cd backend
python3 scripts/seed_data.py
```
