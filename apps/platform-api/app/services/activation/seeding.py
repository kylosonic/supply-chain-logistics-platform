"""Per-workspace sample seeding + supersede semantics (decisions #2/#3/#11).

Seed rows are inserted with ``data_origin='sample'`` + the org id from
the shipped ``sample-data/`` CSVs (build-image-relative via
``settings.sample_data_dir``). Uploads supersede sample rows of the
uploaded category in the SAME transaction — except sample rows still
referenced by real rows of a downstream table (decision #3 keep rule).

Import map: models (5 tables), core.config, pandas, services.audit,
activation.state. Never imports app.api.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.fleet_asset import FleetAsset
from app.models.inventory import Inventory
from app.models.item import Item
from app.models.order import HistoricalOrder
from app.models.organization import Organization
from app.models.user import User
from app.models.warehouse import Warehouse
from app.services.activation.state import CATEGORIES, CATEGORY_META, _ensure_state_row
from app.services.audit import record_audit_event


def _sample_data_dir() -> Path:
    """Resolve the sample-data dir: settings path relative to CWD first,
    then walk up to the repo root (tests run from apps/platform-api)."""
    direct = Path(settings.sample_data_dir)
    if direct.is_dir():
        return direct
    current = Path.cwd()
    while current != current.parent:
        candidate = current / settings.sample_data_dir
        if candidate.is_dir():
            return candidate
        current = current.parent
    raise FileNotFoundError(
        f"sample-data directory '{settings.sample_data_dir}' not found"
    )


def _opt(row, df: pd.DataFrame, column: str, default: Any = None) -> Any:
    if column in df.columns and pd.notna(row[column]):
        return row[column]
    return default


def _load_csv_rows(category: str) -> list[dict]:
    """CSV rows -> row dicts matching the ingestion handler column mapping
    (decision #11 — headers verified against the shipped files)."""
    path = _sample_data_dir() / f'{category}.csv'
    df = pd.read_csv(path)
    rows: list[dict] = []
    for _idx, row in df.iterrows():
        if category == 'warehouses':
            rows.append({
                'code': str(row['code']).strip(),
                'name': str(row['name']),
                'address': str(row['address']),
                'city': str(row['city']),
                'state': str(row['state']),
                'country': str(row['country']),
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude']),
                'capacity_units': int(row['capacity_units']),
            })
        elif category == 'items':
            payload = {
                'sku': str(row['sku']).strip(),
                'name': str(row['name']),
                'category': str(row['category']),
                'unit_cost': float(row['unit_cost']),
                'reorder_level': int(row['reorder_level']),
            }
            threshold = _opt(row, df, 'temperature_threshold')
            if threshold is not None:
                payload['temperature_threshold'] = float(threshold)
            rows.append(payload)
        elif category == 'fleet_assets':
            payload = {
                'vehicle_code': str(row['vehicle_code']).strip(),
                'driver_name': str(row['driver_name']),
                'capacity_units': int(row['capacity_units']),
            }
            contact = _opt(row, df, 'driver_contact')
            if contact is not None:
                payload['driver_contact'] = str(contact)
            status = _opt(row, df, 'status')
            payload['status'] = str(status) if status is not None else 'active'
            rows.append(payload)
        elif category == 'inventory':
            rows.append({
                'warehouse_code': str(row['warehouse_code']).strip(),
                'sku': str(row['sku']).strip(),
                'quantity_on_hand': int(row['quantity_on_hand']),
                'safety_stock': int(_opt(row, df, 'safety_stock', 0)),
            })
        elif category == 'orders':
            rows.append({
                'order_date': pd.to_datetime(row['order_date']).date(),
                'warehouse_code': str(row['warehouse_code']).strip(),
                'sku': str(row['sku']).strip(),
                'quantity': int(row['quantity']),
                'unit_price': float(_opt(row, df, 'unit_price', 0.0)),
                'customer_region': str(_opt(row, df, 'customer_region', 'unknown')),
                'weather_avg_temp_c': (
                    float(_opt(row, df, 'weather_avg_temp_c'))
                    if _opt(row, df, 'weather_avg_temp_c') is not None else None
                ),
                'weather_precip_mm': (
                    float(_opt(row, df, 'weather_precip_mm'))
                    if _opt(row, df, 'weather_precip_mm') is not None else None
                ),
                'weather_disruption_index': (
                    float(_opt(row, df, 'weather_disruption_index'))
                    if _opt(row, df, 'weather_disruption_index') is not None else None
                ),
            })
        else:  # pragma: no cover — CATEGORIES is locked
            raise ValueError(f'Unknown category {category}')
    return rows


def _any_sample_row(db: Session, org_id) -> bool:
    for category in CATEGORIES:
        model = CATEGORY_META[category]['model']
        row = db.execute(
            select(model.id).where(
                model.organization_id == org_id, model.data_origin == 'sample'
            ).limit(1)
        ).first()
        if row is not None:
            return True
    return False


def seed_workspace(
    db: Session,
    org: Organization,
    actor: User | None,
    *,
    force: bool = False,
    now: datetime,
) -> dict:
    """Idempotently seed the org from the shipped CSVs (decision #11).

    ``force=True`` (reset path) skips the idempotency check — the caller
    has already wiped the org's rows. Returns ``{'skipped': True}`` or
    ``{'rows_per_category': {...}}``. Commit-aware: the caller commits.
    """
    state = _ensure_state_row(db, org.id)
    if not force and (state.seeded_at is not None or _any_sample_row(db, org.id)):
        return {'skipped': True}

    rows_per_category: dict[str, int] = {}
    warehouse_rows: dict[str, Warehouse] = {}
    item_rows: dict[str, Item] = {}

    for row in _load_csv_rows('warehouses'):
        wh = Warehouse(organization_id=org.id, data_origin='sample', **row)
        db.add(wh)
        warehouse_rows[row['code']] = wh
    rows_per_category['warehouses'] = len(warehouse_rows)

    for row in _load_csv_rows('items'):
        item = Item(organization_id=org.id, data_origin='sample', **row)
        db.add(item)
        item_rows[row['sku']] = item
    rows_per_category['items'] = len(item_rows)

    fleet_rows = _load_csv_rows('fleet_assets')
    for row in fleet_rows:
        db.add(FleetAsset(organization_id=org.id, data_origin='sample', **row))
    rows_per_category['fleet_assets'] = len(fleet_rows)

    db.flush()

    inventory_rows = _load_csv_rows('inventory')
    for row in inventory_rows:
        warehouse = db.execute(
            select(Warehouse).where(
                Warehouse.organization_id == org.id,
                Warehouse.code == row['warehouse_code'],
            )
        ).scalar_one_or_none()
        item = db.execute(
            select(Item).where(Item.organization_id == org.id, Item.sku == row['sku'])
        ).scalar_one_or_none()
        if warehouse is None or item is None:
            continue
        db.add(
            Inventory(
                warehouse_id=warehouse.id,
                item_id=item.id,
                organization_id=org.id,
                data_origin='sample',
                quantity_on_hand=row['quantity_on_hand'],
                safety_stock=row['safety_stock'],
            )
        )
    rows_per_category['inventory'] = len(inventory_rows)

    orders_rows = _load_csv_rows('orders')
    for row in orders_rows:
        warehouse = db.execute(
            select(Warehouse).where(
                Warehouse.organization_id == org.id,
                Warehouse.code == row['warehouse_code'],
            )
        ).scalar_one_or_none()
        item = db.execute(
            select(Item).where(Item.organization_id == org.id, Item.sku == row['sku'])
        ).scalar_one_or_none()
        if warehouse is None or item is None:
            continue
        db.add(
            HistoricalOrder(
                order_date=row['order_date'],
                warehouse_id=warehouse.id,
                item_id=item.id,
                organization_id=org.id,
                data_origin='sample',
                quantity=row['quantity'],
                unit_price=row['unit_price'],
                customer_region=row['customer_region'],
                weather_avg_temp_c=row['weather_avg_temp_c'],
                weather_precip_mm=row['weather_precip_mm'],
                weather_disruption_index=row['weather_disruption_index'],
            )
        )
    rows_per_category['orders'] = len(orders_rows)

    state.seeded_at = now
    db.add(state)

    record_audit_event(
        db,
        event_type='workspace.seeded_sample_data',
        entity_type='organization',
        entity_id=org.id,
        actor=actor,
        organization_id=org.id,
        description=f'Seeded workspace {org.name} with sample data',
        payload={
            'categories': list(CATEGORIES),
            'rows_per_category': rows_per_category,
        },
    )
    return {'rows_per_category': rows_per_category}


def supersede_sample_rows(db: Session, org: Organization, category: str, now: datetime) -> int:
    """Decision #3: delete org-scoped sample rows of ``category`` except
    sample rows still referenced by real downstream rows; also explicitly
    delete dangling org-scoped sample inventory/orders referencing deleted
    sample warehouses/items. Returns the deleted category-row count.
    """
    org_id = org.id

    # Push pending upserts (data_origin flips) to the DB first so the
    # keep-rule queries and core-level deletes see the post-upload state
    # (the ingestion session runs with autoflush=False).
    db.flush()

    if category in ('warehouses', 'items'):
        model = Warehouse if category == 'warehouses' else Item
        sample_rows = db.execute(
            select(model).where(model.organization_id == org_id, model.data_origin == 'sample')
        ).scalars().all()
        if not sample_rows:
            return 0

        referenced: set = set()
        for downstream, fk_col in (
            (Inventory, Inventory.warehouse_id if category == 'warehouses' else Inventory.item_id),
            (
                HistoricalOrder,
                HistoricalOrder.warehouse_id if category == 'warehouses' else HistoricalOrder.item_id,
            ),
        ):
            refs = db.execute(
                select(fk_col).where(
                    downstream.organization_id == org_id,
                    downstream.data_origin == 'real',
                    fk_col.in_([row.id for row in sample_rows]),
                )
            ).scalars().all()
            referenced.update(refs)

        to_delete = [row for row in sample_rows if row.id not in referenced]
        if not to_delete:
            return 0
        deleted_ids = {row.id for row in to_delete}
        for row in to_delete:
            db.delete(row)

        if category == 'warehouses':
            db.execute(
                delete(Inventory).where(
                    Inventory.organization_id == org_id,
                    Inventory.data_origin == 'sample',
                    Inventory.warehouse_id.in_(deleted_ids),
                )
            )
            db.execute(
                delete(HistoricalOrder).where(
                    HistoricalOrder.organization_id == org_id,
                    HistoricalOrder.data_origin == 'sample',
                    HistoricalOrder.warehouse_id.in_(deleted_ids),
                )
            )
        else:
            db.execute(
                delete(Inventory).where(
                    Inventory.organization_id == org_id,
                    Inventory.data_origin == 'sample',
                    Inventory.item_id.in_(deleted_ids),
                )
            )
            db.execute(
                delete(HistoricalOrder).where(
                    HistoricalOrder.organization_id == org_id,
                    HistoricalOrder.data_origin == 'sample',
                    HistoricalOrder.item_id.in_(deleted_ids),
                )
            )
        return len(to_delete)

    if category == 'fleet_assets':
        result = db.execute(
            delete(FleetAsset).where(
                FleetAsset.organization_id == org_id, FleetAsset.data_origin == 'sample'
            )
        )
        return result.rowcount or 0

    if category == 'inventory':
        result = db.execute(
            delete(Inventory).where(
                Inventory.organization_id == org_id, Inventory.data_origin == 'sample'
            )
        )
        return result.rowcount or 0

    if category == 'orders':
        result = db.execute(
            delete(HistoricalOrder).where(
                HistoricalOrder.organization_id == org_id, HistoricalOrder.data_origin == 'sample'
            )
        )
        return result.rowcount or 0

    return 0  # pragma: no cover — CATEGORIES is locked
