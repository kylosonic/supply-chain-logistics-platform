"""Phase 4 model tests (blueprint §10.2 — test_activation_models.py).

Covers: 1:1 activation state row, threshold crossing uniqueness + level
check, data_origin column semantics on the 5 data tables, and the
fleet_assets organization_id addition (§0A composite unique amendments).
"""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.activation_state import OrganizationActivationState
from app.models.fleet_asset import FleetAsset
from app.models.inventory import Inventory
from app.models.item import Item
from app.models.organization import Organization
from app.models.threshold_crossing import ThresholdCrossing
from app.models.warehouse import Warehouse


def _make_org(db: Session, name: str = 'Model Co') -> Organization:
    org = Organization(
        name=name,
        slug=f'model-co-{uuid4().hex[:8]}',
        primary_email_domain='modelco.com',
        subscription_tier='free',
        subscription_status='active',
        billing_phase='free',
        is_active=True,
    )
    db.add(org)
    db.commit()
    db.refresh(org)
    return org


def test_activation_state_org_unique(db_session: Session):
    org = _make_org(db_session)
    db_session.add(OrganizationActivationState(organization_id=org.id))
    db_session.commit()

    db_session.add(OrganizationActivationState(organization_id=org.id))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_activation_state_nullable_columns(db_session: Session):
    org = _make_org(db_session)
    state = OrganizationActivationState(organization_id=org.id)
    db_session.add(state)
    db_session.commit()

    assert state.m6_completed_at is None
    assert state.toast_fired_at is None
    assert state.seeded_at is None
    assert state.created_at is not None

    now = datetime.now(UTC)
    state.m6_completed_at = now
    state.toast_fired_at = now
    state.seeded_at = now
    db_session.commit()
    assert state.m6_completed_at is not None


def test_threshold_crossing_unique_org_period_level(db_session: Session):
    org = _make_org(db_session)
    db_session.add(
        ThresholdCrossing(
            organization_id=org.id,
            period_start=datetime.now(UTC).date().replace(day=1),
            threshold_level='p60',
            fired_at=datetime.now(UTC),
        )
    )
    db_session.commit()

    db_session.add(
        ThresholdCrossing(
            organization_id=org.id,
            period_start=datetime.now(UTC).date().replace(day=1),
            threshold_level='p60',
            fired_at=datetime.now(UTC),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_threshold_crossing_level_check(db_session: Session):
    org = _make_org(db_session)
    db_session.add(
        ThresholdCrossing(
            organization_id=org.id,
            period_start=datetime.now(UTC).date().replace(day=1),
            threshold_level='p99',
            fired_at=datetime.now(UTC),
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_data_origin_default_real_and_check(db_session: Session):
    org = _make_org(db_session)
    wh = Warehouse(
        code='WH-MOD-1',
        name='Model WH',
        address='1 St',
        city='Addis',
        state='Addis Ababa',
        country='Ethiopia',
        latitude=8.98,
        longitude=38.75,
        capacity_units=100,
        organization_id=org.id,
    )
    db_session.add(wh)
    db_session.commit()

    assert wh.data_origin == 'real'

    item = Item(
        sku='SKU-MOD-1',
        name='Model Item',
        category='Mechanical',
        unit_cost=10.0,
        reorder_level=5,
        organization_id=org.id,
    )
    db_session.add(item)
    db_session.commit()
    assert item.data_origin == 'real'

    wh.data_origin = 'sample'
    db_session.commit()

    wh.data_origin = 'bogus'
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_data_origin_present_on_all_five_tables(db_session: Session):
    org = _make_org(db_session)
    wh = Warehouse(
        code='WH-MOD-2', name='WH', address='a', city='c', state='s', country='c',
        latitude=0.0, longitude=0.0, capacity_units=1, organization_id=org.id,
        data_origin='sample',
    )
    item = Item(
        sku='SKU-MOD-2', name='I', category='C', unit_cost=1.0, reorder_level=1,
        organization_id=org.id, data_origin='sample',
    )
    fleet = FleetAsset(
        vehicle_code='TRUCK-MOD-1', driver_name='D', capacity_units=10,
        organization_id=org.id, data_origin='sample',
    )
    db_session.add_all([wh, item, fleet])
    db_session.commit()

    inv = Inventory(
        warehouse_id=wh.id, item_id=item.id, organization_id=org.id,
        quantity_on_hand=5, safety_stock=1, data_origin='sample',
    )
    db_session.add(inv)
    db_session.commit()

    from app.models.order import HistoricalOrder

    order = HistoricalOrder(
        order_date=datetime.now(UTC).date(),
        warehouse_id=wh.id,
        item_id=item.id,
        organization_id=org.id,
        quantity=2,
        unit_price=1.0,
        data_origin='sample',
    )
    db_session.add(order)
    db_session.commit()

    for model, origin in [
        (Warehouse, 'sample'),
        (Item, 'sample'),
        (FleetAsset, 'sample'),
        (Inventory, 'sample'),
        (HistoricalOrder, 'sample'),
    ]:
        row = db_session.execute(select(model)).scalars().first()
        assert row is not None
        assert row.data_origin == origin


def test_fleet_asset_gains_organization_id(db_session: Session):
    org = _make_org(db_session)
    legacy = FleetAsset(vehicle_code='TRUCK-LEGACY-1', driver_name='Legacy', capacity_units=10)
    db_session.add(legacy)
    db_session.commit()
    assert legacy.organization_id is None

    scoped = FleetAsset(
        vehicle_code='TRUCK-ORG-1', driver_name='Scoped', capacity_units=10,
        organization_id=org.id,
    )
    db_session.add(scoped)
    db_session.commit()
    assert scoped.organization_id == org.id


def test_composite_unique_org_key_allows_same_code_across_orgs(db_session: Session):
    """§0A adjudication: two orgs may both hold WH-001/SKU-001/TRUCK-1001."""
    org_a = _make_org(db_session, 'Org A')
    org_b = _make_org(db_session, 'Org B')

    db_session.add_all([
        Warehouse(
            code='WH-001', name='A', address='a', city='c', state='s', country='c',
            latitude=0.0, longitude=0.0, capacity_units=1, organization_id=org_a.id,
        ),
        Warehouse(
            code='WH-001', name='B', address='a', city='c', state='s', country='c',
            latitude=0.0, longitude=0.0, capacity_units=1, organization_id=org_b.id,
        ),
    ])
    db_session.commit()

    rows = db_session.execute(
        select(Warehouse).where(Warehouse.code == 'WH-001')
    ).scalars().all()
    assert len(rows) == 2
    assert {r.organization_id for r in rows} == {org_a.id, org_b.id}


def test_composite_unique_rejects_duplicate_code_within_org(db_session: Session):
    org = _make_org(db_session)
    db_session.add(
        Warehouse(
            code='WH-001', name='A', address='a', city='c', state='s', country='c',
            latitude=0.0, longitude=0.0, capacity_units=1, organization_id=org.id,
        )
    )
    db_session.commit()
    db_session.add(
        Warehouse(
            code='WH-001', name='B', address='a', city='c', state='s', country='c',
            latitude=0.0, longitude=0.0, capacity_units=1, organization_id=org.id,
        )
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()
