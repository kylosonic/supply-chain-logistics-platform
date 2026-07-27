from __future__ import annotations

import io

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.security import require_roles
from app.db.session import get_db
from app.models.fleet_asset import FleetAsset
from app.models.inventory import Inventory
from app.models.item import Item
from app.models.order import HistoricalOrder
from app.models.user import User
from app.models.warehouse import Warehouse
from app.schemas.auth import UserRole
from app.schemas.ingestion import IngestionResult

router = APIRouter()


def _read_csv_to_df(file: UploadFile) -> pd.DataFrame:
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail='Only CSV files are accepted')
    content = file.file.read()
    try:
        return pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'Invalid CSV: {exc}') from exc


@router.post('/warehouses-csv', response_model=IngestionResult)
def ingest_warehouses_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    df = _read_csv_to_df(file)
    required = {'code', 'name', 'address', 'city', 'state', 'country', 'latitude', 'longitude', 'capacity_units'}
    missing = required.difference(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f'Missing required columns: {sorted(missing)}')

    processed = created = updated = 0
    errors: list[str] = []

    for idx, row in df.iterrows():
        processed += 1
        try:
            code = str(row['code']).strip()
            existing = db.execute(select(Warehouse).where(Warehouse.code == code)).scalar_one_or_none()
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
                existing.name = payload['name']
                existing.address = payload['address']
                existing.city = payload['city']
                existing.state = payload['state']
                existing.country = payload['country']
                existing.latitude = payload['latitude']
                existing.longitude = payload['longitude']
                existing.capacity_units = payload['capacity_units']
                db.add(existing)
                updated += 1
            else:
                db.add(Warehouse(code=code, **payload))
                created += 1
        except Exception as exc:
            errors.append(f'row {idx + 2}: {exc}')

    db.commit()
    return IngestionResult(records_processed=processed, records_created=created, records_updated=updated, errors=errors)


@router.post('/items-csv', response_model=IngestionResult)
def ingest_items_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    df = _read_csv_to_df(file)
    required = {'sku', 'name', 'category', 'unit_cost', 'reorder_level'}
    missing = required.difference(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f'Missing required columns: {sorted(missing)}')

    processed = created = updated = 0
    errors: list[str] = []

    for idx, row in df.iterrows():
        processed += 1
        try:
            sku = str(row['sku']).strip()
            existing = db.execute(select(Item).where(Item.sku == sku)).scalar_one_or_none()
            payload = {
                'name': str(row['name']),
                'category': str(row['category']),
                'unit_cost': float(row['unit_cost']),
                'reorder_level': int(row['reorder_level']),
            }

            if existing:
                existing.name = payload['name']
                existing.category = payload['category']
                existing.unit_cost = payload['unit_cost']
                existing.reorder_level = payload['reorder_level']
                db.add(existing)
                updated += 1
            else:
                db.add(Item(sku=sku, **payload))
                created += 1
        except Exception as exc:
            errors.append(f'row {idx + 2}: {exc}')

    db.commit()
    return IngestionResult(records_processed=processed, records_created=created, records_updated=updated, errors=errors)


@router.post('/fleet-assets-csv', response_model=IngestionResult)
def ingest_fleet_assets_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    df = _read_csv_to_df(file)
    required = {'vehicle_code', 'driver_name', 'capacity_units'}
    missing = required.difference(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f'Missing required columns: {sorted(missing)}')

    processed = created = updated = 0
    errors: list[str] = []

    for idx, row in df.iterrows():
        processed += 1
        try:
            vehicle_code = str(row['vehicle_code']).strip()
            existing = db.execute(select(FleetAsset).where(FleetAsset.vehicle_code == vehicle_code)).scalar_one_or_none()
            payload = {
                'driver_name': str(row['driver_name']),
                'driver_contact': str(row['driver_contact']) if 'driver_contact' in df.columns and pd.notna(row['driver_contact']) else None,
                'capacity_units': int(row['capacity_units']),
                'status': str(row['status']) if 'status' in df.columns and pd.notna(row['status']) else 'active',
            }

            if existing:
                existing.driver_name = payload['driver_name']
                existing.driver_contact = payload['driver_contact']
                existing.capacity_units = payload['capacity_units']
                existing.status = payload['status']
                db.add(existing)
                updated += 1
            else:
                db.add(FleetAsset(vehicle_code=vehicle_code, **payload))
                created += 1
        except Exception as exc:
            errors.append(f'row {idx + 2}: {exc}')

    db.commit()
    return IngestionResult(records_processed=processed, records_created=created, records_updated=updated, errors=errors)


@router.post('/inventory-csv', response_model=IngestionResult)
def ingest_inventory_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    df = _read_csv_to_df(file)
    required = {'warehouse_code', 'sku', 'quantity_on_hand'}
    missing = required.difference(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f'Missing required columns: {sorted(missing)}')

    processed = created = updated = 0
    errors: list[str] = []

    for idx, row in df.iterrows():
        processed += 1
        try:
            warehouse = db.execute(select(Warehouse).where(Warehouse.code == str(row['warehouse_code']))).scalar_one_or_none()
            item = db.execute(select(Item).where(Item.sku == str(row['sku']))).scalar_one_or_none()
            if not warehouse or not item:
                raise ValueError('warehouse_code or sku not found')

            existing = db.execute(
                select(Inventory).where(Inventory.warehouse_id == warehouse.id, Inventory.item_id == item.id)
            ).scalar_one_or_none()

            safety_stock = int(row['safety_stock']) if 'safety_stock' in df.columns and pd.notna(row['safety_stock']) else 0
            quantity_on_hand = int(row['quantity_on_hand'])

            if existing:
                existing.quantity_on_hand = quantity_on_hand
                existing.safety_stock = safety_stock
                updated += 1
                db.add(existing)
            else:
                inv = Inventory(
                    warehouse_id=warehouse.id,
                    item_id=item.id,
                    quantity_on_hand=quantity_on_hand,
                    safety_stock=safety_stock,
                )
                created += 1
                db.add(inv)
        except Exception as exc:
            errors.append(f'row {idx + 2}: {exc}')

    db.commit()
    return IngestionResult(records_processed=processed, records_created=created, records_updated=updated, errors=errors)


@router.post('/orders-csv', response_model=IngestionResult)
def ingest_orders_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
):
    df = _read_csv_to_df(file)
    required = {'order_date', 'warehouse_code', 'sku', 'quantity'}
    missing = required.difference(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f'Missing required columns: {sorted(missing)}')

    processed = created = updated = 0
    errors: list[str] = []

    for idx, row in df.iterrows():
        processed += 1
        try:
            warehouse = db.execute(select(Warehouse).where(Warehouse.code == str(row['warehouse_code']))).scalar_one_or_none()
            item = db.execute(select(Item).where(Item.sku == str(row['sku']))).scalar_one_or_none()
            if not warehouse or not item:
                raise ValueError('warehouse_code or sku not found')

            order = HistoricalOrder(
                order_date=pd.to_datetime(row['order_date']).date(),
                warehouse_id=warehouse.id,
                item_id=item.id,
                quantity=int(row['quantity']),
                unit_price=float(row['unit_price']) if 'unit_price' in df.columns and pd.notna(row['unit_price']) else 0.0,
                customer_region=str(row['customer_region']) if 'customer_region' in df.columns and pd.notna(row['customer_region']) else 'unknown',
                weather_avg_temp_c=float(row['weather_avg_temp_c']) if 'weather_avg_temp_c' in df.columns and pd.notna(row['weather_avg_temp_c']) else None,
                weather_precip_mm=float(row['weather_precip_mm']) if 'weather_precip_mm' in df.columns and pd.notna(row['weather_precip_mm']) else None,
                weather_disruption_index=float(row['weather_disruption_index']) if 'weather_disruption_index' in df.columns and pd.notna(row['weather_disruption_index']) else None,
            )
            db.add(order)
            created += 1
        except Exception as exc:
            errors.append(f'row {idx + 2}: {exc}')

    db.commit()
    return IngestionResult(records_processed=processed, records_created=created, records_updated=updated, errors=errors)
