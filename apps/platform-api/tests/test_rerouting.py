from __future__ import annotations

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.item import Item
from app.models.organization import Organization
from app.models.route import RouteSchedule, RouteStop
from app.models.shipment import Shipment
from app.models.warehouse import Warehouse
from app.services.rerouting import generate_rerouting_plan


def _fixture(db: Session):
    org = db.execute(select(Organization).where(Organization.slug == 'testco')).scalar_one()
    origin = Warehouse(
        organization_id=org.id,
        code='WH-ORIGIN',
        name='Origin',
        address='1',
        city='Addis Ababa',
        state='Addis Ababa',
        country='ET',
        latitude=9.0,
        longitude=38.7,
        capacity_units=100,
    )
    destination = Warehouse(
        organization_id=org.id,
        code='WH-DEST',
        name='Destination',
        address='2',
        city='Addis Ababa',
        state='Addis Ababa',
        country='ET',
        latitude=9.1,
        longitude=38.8,
        capacity_units=100,
    )
    item = Item(
        organization_id=org.id,
        sku='SKU-REROUTE',
        name='Reroute item',
        category='General',
        unit_cost=10,
        reorder_level=2,
    )
    db.add_all([origin, destination, item])
    db.flush()
    shipment = Shipment(
        organization_id=org.id,
        shipment_no='SHIP-REROUTE-1',
        origin_warehouse_id=origin.id,
        destination_warehouse_id=destination.id,
        item_id=item.id,
        quantity_units=1,
        status='delayed',
    )
    alert = Alert(
        organization_id=org.id,
        alert_type='shipment_delayed',
        severity='high',
        title='Delayed shipment',
        message='Delayed',
        related_entity_type='shipment',
        related_entity_id=str(shipment.id),
    )
    db.add_all([shipment, alert])
    db.commit()
    return org, origin, destination, shipment, alert


def test_rerouting_never_invents_a_candidate_or_cost(db_session: Session):
    _org, _origin, _destination, shipment, alert = _fixture(db_session)

    generate_rerouting_plan(db_session, alert.id, shipment.id)
    db_session.refresh(alert)

    assert alert.payload['rerouting_status'] == 'no_saved_alternative'
    assert 'rerouting_plan' not in alert.payload


def test_rerouting_uses_only_a_saved_active_route(db_session: Session):
    org, origin, destination, shipment, alert = _fixture(db_session)
    route = RouteSchedule(
        organization_id=org.id,
        route_name='Saved alternative',
        schedule_date=date(2026, 8, 10),
        start_warehouse_id=origin.id,
        vehicle_capacity_units=100,
        status='active',
        estimated_duration_min=90,
    )
    db_session.add(route)
    db_session.flush()
    db_session.add(
        RouteStop(
            route_schedule_id=route.id,
            sequence=1,
            warehouse_id=destination.id,
            load_units=1,
        )
    )
    db_session.commit()

    generate_rerouting_plan(db_session, alert.id, shipment.id)
    db_session.refresh(alert)

    plan = alert.payload['rerouting_plan']
    assert plan['proposed_route_id'] == str(route.id)
    assert plan['candidate_source'] == 'saved_active_schedule'
    assert plan['estimated_duration_min'] == 90
    assert 'additional_cost_usd' not in plan
    assert 'estimated_recovery_time_hrs' not in plan
