from __future__ import annotations

import io
from datetime import UTC, datetime

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.security import require_roles, require_writable_workspace
from app.db.session import get_db
from app.models.alert import Alert
from app.models.fleet_asset import FleetAsset
from app.models.item import Item
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.user import User
from app.schemas.alert import AlertSeverity, AlertStatus, AlertType
from app.schemas.auth import UserRole
from app.schemas.ingestion import (
    IngestionResult,
    IoTColdChainPayload,
    IoTResult,
    TelematicsPayload,
    TelematicsResult,
)
from app.services.activation import ingest as activation_ingest
from app.services.activation import seeding
from app.services.activation import state as activation_state

router = APIRouter()


def _read_csv_to_df(file: UploadFile) -> pd.DataFrame:
    if not file.filename or not file.filename.lower().endswith('.csv'):
        raise HTTPException(status_code=400, detail='Only CSV files are accepted')
    content = file.file.read()
    try:
        return pd.read_csv(io.BytesIO(content))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f'Invalid CSV: {exc}') from exc


def _require_columns(df: pd.DataFrame, required: set[str]) -> None:
    missing = required.difference(df.columns)
    if missing:
        raise HTTPException(status_code=400, detail=f'Missing required columns: {sorted(missing)}')


def _finish_csv_upload(
    db: Session,
    actor: User,
    writable: OrganizationMembership | None,
    counts: dict,
    category: str,
) -> None:
    """Supersede sample rows + audit the upload in the SAME transaction
    (decision #3 keep-rule; decision #4 gap-fill audit). Org-less write
    contract (no membership) skips activation concerns."""
    if writable is None:
        return
    org = db.get(Organization, writable.organization_id)
    if org is None:
        return
    now = datetime.now(UTC)
    seeding.supersede_sample_rows(db, org, category, now)
    activation_state.record_csv_upload(
        db, org.id, actor, category=category, counts=counts, now=now
    )


@router.post('/warehouses-csv', response_model=IngestionResult)
def ingest_warehouses_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    df = _read_csv_to_df(file)
    _require_columns(
        df, {'code', 'name', 'address', 'city', 'state', 'country', 'latitude', 'longitude', 'capacity_units'}
    )
    org_id = writable.organization_id if writable else None
    counts = activation_ingest.upsert_warehouses(db, org_id, df)
    _finish_csv_upload(db, actor, writable, counts, 'warehouses')
    db.commit()
    return IngestionResult(**counts)


@router.post('/items-csv', response_model=IngestionResult)
def ingest_items_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    df = _read_csv_to_df(file)
    _require_columns(df, {'sku', 'name', 'category', 'unit_cost', 'reorder_level'})
    org_id = writable.organization_id if writable else None
    counts = activation_ingest.upsert_items(db, org_id, df)
    _finish_csv_upload(db, actor, writable, counts, 'items')
    db.commit()
    return IngestionResult(**counts)


@router.post('/fleet-assets-csv', response_model=IngestionResult)
def ingest_fleet_assets_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    df = _read_csv_to_df(file)
    _require_columns(df, {'vehicle_code', 'driver_name', 'capacity_units'})
    org_id = writable.organization_id if writable else None
    counts = activation_ingest.upsert_fleet(db, org_id, df)
    _finish_csv_upload(db, actor, writable, counts, 'fleet_assets')
    db.commit()
    return IngestionResult(**counts)


@router.post('/inventory-csv', response_model=IngestionResult)
def ingest_inventory_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    df = _read_csv_to_df(file)
    _require_columns(df, {'warehouse_code', 'sku', 'quantity_on_hand'})
    org_id = writable.organization_id if writable else None
    counts = activation_ingest.upsert_inventory(db, org_id, df)
    _finish_csv_upload(db, actor, writable, counts, 'inventory')
    db.commit()
    return IngestionResult(**counts)


@router.post('/orders-csv', response_model=IngestionResult)
def ingest_orders_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    df = _read_csv_to_df(file)
    _require_columns(df, {'order_date', 'warehouse_code', 'sku', 'quantity'})
    org_id = writable.organization_id if writable else None
    counts = activation_ingest.upsert_orders(db, org_id, df)
    _finish_csv_upload(db, actor, writable, counts, 'orders')
    db.commit()
    return IngestionResult(**counts)


@router.post('/telematics', response_model=TelematicsResult)
async def ingest_telematics(
    payload: TelematicsPayload,
    db: Session = Depends(get_db),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    """Ingest a real-time telematics data point for a fleet asset.

    Looks up the asset by its vehicle_code (asset_id), updates its GPS
    coordinates and telemetry timestamp.  Returns 404 if the asset is
    not registered.
    """
    asset = db.execute(
        select(FleetAsset).where(FleetAsset.vehicle_code == payload.asset_id)
    ).scalar_one_or_none()

    if asset is None:
        raise HTTPException(
            status_code=404,
            detail=f"Fleet asset with asset_id '{payload.asset_id}' not found",
        )

    asset.latitude = payload.latitude
    asset.longitude = payload.longitude
    asset.last_telemetry_at = payload.timestamp
    db.add(asset)
    db.commit()

    return TelematicsResult(
        asset_id=payload.asset_id,
        status="updated",
        updated_latitude=payload.latitude,
        updated_longitude=payload.longitude,
        telemetry_timestamp=payload.timestamp,
    )


@router.post('/iot-telemetry', response_model=IoTResult)
async def ingest_iot_telemetry(
    payload: IoTColdChainPayload,
    db: Session = Depends(get_db),
    writable: OrganizationMembership | None = Depends(require_writable_workspace),
):
    item = db.execute(select(Item).where(Item.sku == payload.sku)).scalar_one_or_none()

    if not item:
        raise HTTPException(
            status_code=404,
            detail=f"Item with SKU '{payload.sku}' not found",
        )

    alert_triggered = False
    if item.temperature_threshold is not None and payload.temperature_c > item.temperature_threshold:
        alert = Alert(
            alert_type=AlertType.TEMPERATURE_EXCURSION,
            severity=AlertSeverity.HIGH,
            status=AlertStatus.OPEN,
            title=f'Temperature threshold exceeded for {payload.sku}',
            message=f'Reported temperature {payload.temperature_c}°C exceeds threshold of {item.temperature_threshold}°C.',
            related_entity_type='item',
            related_entity_id=item.id,
        )
        db.add(alert)
        db.commit()
        alert_triggered = True

    return IoTResult(
        sku=payload.sku,
        status='processed',
        alert_triggered=alert_triggered,
    )
