"""Org-scoped CSV upsert helpers (blueprint decision #13).

Per-handler row mapping extracted from ``api/endpoints/ingestion.py`` so
the endpoint module stays under the 400-line cap. Lookups are scoped by
``organization_id``; every insert/update is stamped
``organization_id`` + ``data_origin='real'``. When ``org_id`` is None
(org-less legacy write contract) the lookup falls back to the global
namespace and no org stamp is applied — pre-existing behavior preserved.

Import map: models (5 tables), pandas only. Never imports app.api.
"""

from __future__ import annotations

import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.fleet_asset import FleetAsset
from app.models.inventory import Inventory
from app.models.item import Item
from app.models.order import HistoricalOrder
from app.models.warehouse import Warehouse


def _org_filter(column, org_id):
    return column == org_id if org_id is not None else None


def upsert_warehouses(db: Session, org_id, df: pd.DataFrame) -> dict:
    processed = created = updated = 0
    errors: list[str] = []
    for idx, row in df.iterrows():
        processed += 1
        try:
            code = str(row['code']).strip()
            query = select(Warehouse).where(Warehouse.code == code)
            if org_id is not None:
                query = query.where(Warehouse.organization_id == org_id)
            existing = db.execute(query).scalar_one_or_none()
            payload = {
                'name': str(row['name']),
                'address': str(row['address']),
                'city': str(row['city']),
                'state': str(row['state']),
                'country': str(row['country']),
                'latitude': float(row['latitude']),
                'longitude': float(row['longitude']),
                'capacity_units': int(row['capacity_units']),
            }
            if existing:
                for key, value in payload.items():
                    setattr(existing, key, value)
                existing.data_origin = 'real'
                existing.organization_id = org_id
                db.add(existing)
                updated += 1
            else:
                db.add(Warehouse(code=code, organization_id=org_id, data_origin='real', **payload))
                created += 1
        except Exception as exc:
            errors.append(f'row {idx + 2}: {exc}')
    return {
        'records_processed': processed,
        'records_created': created,
        'records_updated': updated,
        'errors': errors,
    }


def upsert_items(db: Session, org_id, df: pd.DataFrame) -> dict:
    processed = created = updated = 0
    errors: list[str] = []
    for idx, row in df.iterrows():
        processed += 1
        try:
            sku = str(row['sku']).strip()
            query = select(Item).where(Item.sku == sku)
            if org_id is not None:
                query = query.where(Item.organization_id == org_id)
            existing = db.execute(query).scalar_one_or_none()
            payload = {
                'name': str(row['name']),
                'category': str(row['category']),
                'unit_cost': float(row['unit_cost']),
                'reorder_level': int(row['reorder_level']),
            }
            if 'temperature_threshold' in df.columns and pd.notna(row['temperature_threshold']):
                payload['temperature_threshold'] = float(row['temperature_threshold'])
            if existing:
                for key, value in payload.items():
                    setattr(existing, key, value)
                existing.data_origin = 'real'
                existing.organization_id = org_id
                db.add(existing)
                updated += 1
            else:
                db.add(Item(sku=sku, organization_id=org_id, data_origin='real', **payload))
                created += 1
        except Exception as exc:
            errors.append(f'row {idx + 2}: {exc}')
    return {
        'records_processed': processed,
        'records_created': created,
        'records_updated': updated,
        'errors': errors,
    }


def upsert_fleet(db: Session, org_id, df: pd.DataFrame) -> dict:
    processed = created = updated = 0
    errors: list[str] = []
    for idx, row in df.iterrows():
        processed += 1
        try:
            vehicle_code = str(row['vehicle_code']).strip()
            query = select(FleetAsset).where(FleetAsset.vehicle_code == vehicle_code)
            if org_id is not None:
                query = query.where(FleetAsset.organization_id == org_id)
            existing = db.execute(query).scalar_one_or_none()
            payload = {
                'driver_name': str(row['driver_name']),
                'driver_contact': (
                    str(row['driver_contact'])
                    if 'driver_contact' in df.columns and pd.notna(row['driver_contact'])
                    else None
                ),
                'capacity_units': int(row['capacity_units']),
                'status': (
                    str(row['status'])
                    if 'status' in df.columns and pd.notna(row['status'])
                    else 'active'
                ),
            }
            if existing:
                for key, value in payload.items():
                    setattr(existing, key, value)
                existing.data_origin = 'real'
                existing.organization_id = org_id
                db.add(existing)
                updated += 1
            else:
                db.add(
                    FleetAsset(
                        vehicle_code=vehicle_code,
                        organization_id=org_id,
                        data_origin='real',
                        **payload,
                    )
                )
                created += 1
        except Exception as exc:
            errors.append(f'row {idx + 2}: {exc}')
    return {
        'records_processed': processed,
        'records_created': created,
        'records_updated': updated,
        'errors': errors,
    }


def _lookup_warehouse(db: Session, org_id, code: str) -> Warehouse | None:
    query = select(Warehouse).where(Warehouse.code == code)
    if org_id is not None:
        query = query.where(Warehouse.organization_id == org_id)
    return db.execute(query).scalar_one_or_none()


def _lookup_item(db: Session, org_id, sku: str) -> Item | None:
    query = select(Item).where(Item.sku == sku)
    if org_id is not None:
        query = query.where(Item.organization_id == org_id)
    return db.execute(query).scalar_one_or_none()


def upsert_inventory(db: Session, org_id, df: pd.DataFrame) -> dict:
    processed = created = updated = 0
    errors: list[str] = []
    for idx, row in df.iterrows():
        processed += 1
        try:
            warehouse = _lookup_warehouse(db, org_id, str(row['warehouse_code']))
            item = _lookup_item(db, org_id, str(row['sku']))
            if not warehouse or not item:
                raise ValueError('warehouse_code or sku not found')

            existing = db.execute(
                select(Inventory).where(
                    Inventory.warehouse_id == warehouse.id, Inventory.item_id == item.id
                )
            ).scalar_one_or_none()

            safety_stock = (
                int(row['safety_stock'])
                if 'safety_stock' in df.columns and pd.notna(row['safety_stock'])
                else 0
            )
            quantity_on_hand = int(row['quantity_on_hand'])

            if existing:
                existing.quantity_on_hand = quantity_on_hand
                existing.safety_stock = safety_stock
                existing.data_origin = 'real'
                existing.organization_id = org_id
                db.add(existing)
                updated += 1
            else:
                db.add(
                    Inventory(
                        warehouse_id=warehouse.id,
                        item_id=item.id,
                        organization_id=org_id,
                        data_origin='real',
                        quantity_on_hand=quantity_on_hand,
                        safety_stock=safety_stock,
                    )
                )
                created += 1
        except Exception as exc:
            errors.append(f'row {idx + 2}: {exc}')
    return {
        'records_processed': processed,
        'records_created': created,
        'records_updated': updated,
        'errors': errors,
    }


def upsert_orders(db: Session, org_id, df: pd.DataFrame) -> dict:
    processed = created = updated = 0
    errors: list[str] = []
    for idx, row in df.iterrows():
        processed += 1
        try:
            warehouse = _lookup_warehouse(db, org_id, str(row['warehouse_code']))
            item = _lookup_item(db, org_id, str(row['sku']))
            if not warehouse or not item:
                raise ValueError('warehouse_code or sku not found')

            db.add(
                HistoricalOrder(
                    order_date=pd.to_datetime(row['order_date']).date(),
                    warehouse_id=warehouse.id,
                    item_id=item.id,
                    organization_id=org_id,
                    data_origin='real',
                    quantity=int(row['quantity']),
                    unit_price=(
                        float(row['unit_price'])
                        if 'unit_price' in df.columns and pd.notna(row['unit_price'])
                        else 0.0
                    ),
                    customer_region=(
                        str(row['customer_region'])
                        if 'customer_region' in df.columns and pd.notna(row['customer_region'])
                        else 'unknown'
                    ),
                    weather_avg_temp_c=(
                        float(row['weather_avg_temp_c'])
                        if 'weather_avg_temp_c' in df.columns and pd.notna(row['weather_avg_temp_c'])
                        else None
                    ),
                    weather_precip_mm=(
                        float(row['weather_precip_mm'])
                        if 'weather_precip_mm' in df.columns and pd.notna(row['weather_precip_mm'])
                        else None
                    ),
                    weather_disruption_index=(
                        float(row['weather_disruption_index'])
                        if 'weather_disruption_index' in df.columns
                        and pd.notna(row['weather_disruption_index'])
                        else None
                    ),
                )
            )
            created += 1
        except Exception as exc:
            errors.append(f'row {idx + 2}: {exc}')
    return {
        'records_processed': processed,
        'records_created': created,
        'records_updated': updated,
        'errors': errors,
    }
