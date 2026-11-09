from __future__ import annotations

import hashlib
from datetime import UTC, datetime, time, timedelta
from decimal import Decimal
from uuid import UUID, uuid4

import jwt
from fastapi import APIRouter, Depends, File, Form, Header, HTTPException, Response, UploadFile
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.security import (
    get_current_membership,
    organization_scoped_get,
    require_roles,
    require_writable_workspace,
    resolve_scoped_organization,
    scoped_to_organization,
)
from app.core.config import settings
from app.db.session import get_db
from app.models.dispatch import (
    Customer,
    DeliveryOrder,
    DeliveryProof,
    DispatchRun,
)
from app.models.driver import Driver
from app.models.item import Item
from app.models.membership import OrganizationMembership
from app.models.organization import Organization
from app.models.user import User
from app.schemas.auth import UserRole
from app.schemas.dispatch import (
    CashCloseRequest,
    CashCloseSummary,
    CustomerCreate,
    CustomerRead,
    CustomerTrackingLinkResponse,
    CustomerTrackingRead,
    DeliveryOrderCreate,
    DeliveryOrderRead,
    DeliveryProofRead,
    DispatchPlanRequest,
    DispatchRunDetail,
    DispatchRunRead,
    DispatchStopRead,
    DriverCashDeclare,
    DriverLinkResponse,
    DriverManifest,
    DriverStatusUpdate,
    FleetDispatchPlanRequest,
    FleetDispatchPlanResponse,
)
from app.services.audit import record_audit_event
from app.services.dispatch import plan_fleet_time_window_routes, plan_time_window_route
from app.services.security import decode_access_token

router = APIRouter()

_PROOF_MAX_BYTES = 4 * 1024 * 1024
_PROOF_TYPES = {'image/jpeg', 'image/png', 'image/webp'}
_TERMINAL_ORDER_STATUSES = {'delivered', 'failed', 'cancelled'}
_CUSTOMER_TRACKING_HOURS = 72


def _has_expected_image_signature(content: bytes, content_type: str) -> bool:
    if content_type == 'image/jpeg':
        return content.startswith(b'\xff\xd8\xff')
    if content_type == 'image/png':
        return content.startswith(b'\x89PNG\r\n\x1a\n')
    if content_type == 'image/webp':
        return (
            len(content) >= 12
            and content.startswith(b'RIFF')
            and content[8:12] == b'WEBP'
        )
    return False


def _org(actor: User, writable: OrganizationMembership | None) -> UUID:
    return resolve_scoped_organization(actor, writable)


def _customer_read(customer: Customer) -> CustomerRead:
    return CustomerRead.model_validate(customer)


def _order_read(order: DeliveryOrder, customer: Customer | None) -> DeliveryOrderRead:
    return DeliveryOrderRead(
        id=str(order.id),
        created_at=order.created_at,
        order_no=order.order_no,
        customer_id=str(order.customer_id),
        customer_code=customer.code if customer else None,
        customer_name=customer.name if customer else None,
        item_id=str(order.item_id) if order.item_id else None,
        dispatch_run_id=str(order.dispatch_run_id) if order.dispatch_run_id else None,
        driver_id=str(order.driver_id) if order.driver_id else None,
        quantity_units=order.quantity_units,
        cod_amount_etb=order.cod_amount_etb,
        window_start=order.window_start,
        window_end=order.window_end,
        service_minutes=order.service_minutes,
        priority=order.priority,
        stop_sequence=order.stop_sequence,
        status=order.status,
        completed_at=order.completed_at,
        collected_cash_etb=order.collected_cash_etb,
        cash_declared_at=order.cash_declared_at,
        cash_settled_at=order.cash_settled_at,
        cash_note=order.cash_note,
        notes=order.notes,
    )


def _run_read(run: DispatchRun) -> DispatchRunRead:
    return DispatchRunRead.model_validate(run)


def _stops_for_run(db: Session, run: DispatchRun) -> list[DispatchStopRead]:
    stop_data = run.stops_json or []
    order_ids = [UUID(str(item['order_id'])) for item in stop_data]
    if not order_ids:
        return []
    rows = db.execute(
        select(DeliveryOrder, Customer)
        .join(
            Customer,
            (Customer.id == DeliveryOrder.customer_id)
            & (Customer.organization_id == run.organization_id),
        )
        .where(
            DeliveryOrder.organization_id == run.organization_id,
            DeliveryOrder.id.in_(order_ids),
        )
    ).all()
    by_id = {str(order.id): (order, customer) for order, customer in rows}
    proofs = (
        db.execute(
            select(DeliveryProof)
            .where(
                DeliveryProof.organization_id == run.organization_id,
                DeliveryProof.delivery_order_id.in_(order_ids),
            )
            .order_by(DeliveryProof.captured_at.desc())
        )
        .scalars()
        .all()
    )
    proof_by_order: dict[str, str] = {}
    for proof in proofs:
        proof_by_order.setdefault(str(proof.delivery_order_id), str(proof.id))

    stops: list[DispatchStopRead] = []
    for item in stop_data:
        found = by_id.get(str(item['order_id']))
        if found is None:
            continue
        order, customer = found
        stops.append(
            DispatchStopRead(
                order_id=str(order.id),
                order_no=order.order_no,
                customer_code=customer.code,
                customer_name=customer.name,
                address=customer.address,
                phone=customer.phone,
                latitude=customer.latitude,
                longitude=customer.longitude,
                sequence=item['sequence'],
                planned_arrival=datetime.fromisoformat(item['planned_arrival']),
                window_start=order.window_start,
                window_end=order.window_end,
                demand_units=order.quantity_units,
                cod_amount_etb=order.cod_amount_etb,
                status=order.status,
                completed_at=order.completed_at,
                collected_cash_etb=order.collected_cash_etb,
                proof_id=proof_by_order.get(str(order.id)),
            )
        )
    return sorted(stops, key=lambda stop: stop.sequence)


def _run_detail(db: Session, run: DispatchRun) -> DispatchRunDetail:
    return DispatchRunDetail(
        **_run_read(run).model_dump(),
        stops=_stops_for_run(db, run),
        unassigned=run.unassigned_json or [],
    )


def _fleet_route_name(base_name: str, driver_name: str, multiple_vehicles: bool) -> str:
    if not multiple_vehicles:
        return base_name
    suffix = f' - {driver_name}'
    return f'{base_name[: max(1, 128 - len(suffix))]}{suffix}'[:128]


def _customer_in_org(db: Session, organization_id: UUID, customer_id: str) -> Customer:
    return organization_scoped_get(
        db,
        Customer,
        customer_id,
        organization_id,
        not_found_detail='Customer not found',
        include_legacy_null=False,
    )


def _order_in_org(db: Session, organization_id: UUID, order_id: str) -> DeliveryOrder:
    return organization_scoped_get(
        db,
        DeliveryOrder,
        order_id,
        organization_id,
        not_found_detail='Delivery order not found',
        include_legacy_null=False,
    )


@router.get('/customers', response_model=list[CustomerRead])
def list_customers(
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    return (
        db.execute(
            scoped_to_organization(select(Customer), Customer, membership.organization_id).order_by(
                Customer.name
            )
        )
        .scalars()
        .all()
    )


@router.post('/customers', response_model=CustomerRead, status_code=201)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership = Depends(require_writable_workspace),
):
    organization_id = _org(actor, writable)
    duplicate = db.execute(
        select(Customer.id).where(
            Customer.organization_id == organization_id,
            Customer.code == payload.code.strip().upper(),
        )
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail='Customer code already exists')
    customer = Customer(
        organization_id=organization_id,
        code=payload.code.strip().upper(),
        name=payload.name.strip(),
        phone=payload.phone,
        address=payload.address.strip(),
        latitude=payload.latitude,
        longitude=payload.longitude,
        notes=payload.notes,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return _customer_read(customer)


@router.get('/orders', response_model=list[DeliveryOrderRead])
def list_delivery_orders(
    run_id: str | None = None,
    status_filter: str | None = None,
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    stmt = select(DeliveryOrder).where(DeliveryOrder.organization_id == membership.organization_id)
    if run_id:
        stmt = stmt.where(DeliveryOrder.dispatch_run_id == run_id)
    if status_filter:
        stmt = stmt.where(DeliveryOrder.status == status_filter)
    orders = db.execute(stmt.order_by(DeliveryOrder.created_at.desc())).scalars().all()
    customer_ids = {order.customer_id for order in orders}
    customers = (
        db.execute(select(Customer).where(Customer.id.in_(customer_ids))).scalars().all()
        if customer_ids
        else []
    )
    customer_by_id = {customer.id: customer for customer in customers}
    return [_order_read(order, customer_by_id.get(order.customer_id)) for order in orders]


@router.post('/orders', response_model=DeliveryOrderRead, status_code=201)
def create_delivery_order(
    payload: DeliveryOrderCreate,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership = Depends(require_writable_workspace),
):
    organization_id = _org(actor, writable)
    customer = _customer_in_org(db, organization_id, payload.customer_id)
    if payload.item_id:
        organization_scoped_get(
            db,
            Item,
            payload.item_id,
            organization_id,
            not_found_detail='Item not found',
            include_legacy_null=False,
        )
    if (
        payload.window_start is not None
        and payload.window_end is not None
        and payload.window_start > payload.window_end
    ):
        raise HTTPException(status_code=422, detail='window_start must be before window_end')
    duplicate = db.execute(
        select(DeliveryOrder.id).where(
            DeliveryOrder.organization_id == organization_id,
            DeliveryOrder.order_no == payload.order_no.strip(),
        )
    ).first()
    if duplicate:
        raise HTTPException(status_code=409, detail='Delivery order number already exists')
    order = DeliveryOrder(
        organization_id=organization_id,
        customer_id=customer.id,
        item_id=payload.item_id,
        order_no=payload.order_no.strip(),
        quantity_units=payload.quantity_units,
        cod_amount_etb=payload.cod_amount_etb,
        window_start=payload.window_start,
        window_end=payload.window_end,
        service_minutes=payload.service_minutes,
        priority=payload.priority,
        notes=payload.notes,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return _order_read(order, customer)


@router.get('/orders/{order_id}', response_model=DeliveryOrderRead)
def get_delivery_order(
    order_id: str,
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    order = _order_in_org(db, membership.organization_id, order_id)
    customer = _customer_in_org(db, membership.organization_id, str(order.customer_id))
    return _order_read(order, customer)


@router.post(
    '/orders/{order_id}/tracking-link',
    response_model=CustomerTrackingLinkResponse,
)
def create_customer_tracking_link(
    order_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership = Depends(require_writable_workspace),
):
    organization_id = _org(actor, writable)
    order = _order_in_org(db, organization_id, order_id)
    expires_at = datetime.now(UTC) + timedelta(hours=_CUSTOMER_TRACKING_HOURS)
    token = jwt.encode(
        {
            'sub': str(order.id),
            'org_id': str(organization_id),
            'scope': 'customer_tracking',
            'iat': int(datetime.now(UTC).timestamp()),
            'exp': int(expires_at.timestamp()),
            'jti': uuid4().hex,
        },
        settings.effective_jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return CustomerTrackingLinkResponse(
        token=token,
        tracking_url=f'{settings.console_url.rstrip("/")}/track#token={token}',
        expires_at=expires_at,
    )


@router.get('/tracking', response_model=CustomerTrackingRead)
def get_customer_tracking(
    x_tracking_token: str = Header(default='', alias='X-Tracking-Token'),
    db: Session = Depends(get_db),
):
    if not x_tracking_token:
        raise HTTPException(status_code=401, detail='Tracking token required')
    try:
        token_payload = decode_access_token(x_tracking_token)
        if token_payload.get('scope') != 'customer_tracking':
            raise ValueError('wrong scope')
        organization_id = UUID(str(token_payload['org_id']))
        order_id = UUID(str(token_payload['sub']))
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail='Invalid or expired tracking token') from None

    organization = db.get(Organization, organization_id)
    order = db.get(DeliveryOrder, order_id)
    if (
        organization is None
        or not organization.is_active
        or order is None
        or order.organization_id != organization_id
    ):
        raise HTTPException(status_code=404, detail='Tracking link not found')
    customer = db.get(Customer, order.customer_id)
    if customer is None or customer.organization_id != organization_id:
        raise HTTPException(status_code=404, detail='Tracking link not found')

    run = db.get(DispatchRun, order.dispatch_run_id) if order.dispatch_run_id else None
    driver = db.get(Driver, run.driver_id) if run and run.driver_id else None
    planned_arrival = None
    if run is not None:
        for stop in run.stops_json or []:
            if str(stop.get('order_id')) == str(order.id):
                raw_arrival = stop.get('planned_arrival')
                if raw_arrival:
                    planned_arrival = datetime.fromisoformat(str(raw_arrival))
                break
    proof_count = db.execute(
        select(func.count(DeliveryProof.id)).where(
            DeliveryProof.organization_id == organization_id,
            DeliveryProof.delivery_order_id == order.id,
        )
    ).scalar_one()
    return CustomerTrackingRead(
        order_no=order.order_no,
        customer_name=customer.name,
        status=order.status,
        route_name=run.route_name if run else None,
        driver_name=driver.full_name if driver else None,
        planned_arrival=planned_arrival,
        window_start=order.window_start,
        window_end=order.window_end,
        proof_available=proof_count > 0,
        updated_at=order.updated_at,
    )


@router.post('/runs', response_model=DispatchRunDetail, status_code=201)
def plan_dispatch_run(
    payload: DispatchPlanRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership = Depends(require_writable_workspace),
):
    organization_id = _org(actor, writable)
    order_ids = list(dict.fromkeys(payload.order_ids))
    orders = (
        db.execute(
            select(DeliveryOrder).where(
                DeliveryOrder.organization_id == organization_id,
                DeliveryOrder.id.in_([UUID(str(order_id)) for order_id in order_ids]),
                DeliveryOrder.status == 'planned',
            )
            .with_for_update()
        )
        .scalars()
        .all()
    )
    by_id = {str(order.id): order for order in orders}
    if len(by_id) != len(order_ids):
        raise HTTPException(status_code=422, detail='One or more orders are not plannable')

    customer_ids = {order.customer_id for order in orders}
    customers = (
        db.execute(
            select(Customer).where(
                Customer.organization_id == organization_id,
                Customer.id.in_(customer_ids),
            )
        )
        .scalars()
        .all()
    )
    customer_by_id = {customer.id: customer for customer in customers}
    if any(order.customer_id not in customer_by_id for order in orders):
        raise HTTPException(status_code=422, detail='A delivery order has no customer')

    driver = None
    if payload.driver_id:
        driver = organization_scoped_get(
            db,
            Driver,
            payload.driver_id,
            organization_id,
            not_found_detail='Driver not found',
            include_legacy_null=False,
        )
        if driver.status != 'active':
            raise HTTPException(status_code=422, detail='Driver is not active')

    start_time = payload.start_time or datetime.combine(payload.plan_date, time(8, 0), tzinfo=UTC)
    planned = plan_time_window_route(
        start_label=payload.start_label,
        start_latitude=payload.start_latitude,
        start_longitude=payload.start_longitude,
        start_time=start_time,
        orders=[
            {
                'id': order.id,
                'order_no': order.order_no,
                'quantity_units': order.quantity_units,
                'priority': order.priority,
                'service_minutes': order.service_minutes,
                'window_start': order.window_start,
                'window_end': order.window_end,
                'latitude': customer_by_id[order.customer_id].latitude,
                'longitude': customer_by_id[order.customer_id].longitude,
            }
            for order in orders
        ],
        vehicle_capacity_units=payload.vehicle_capacity_units,
        max_stops=payload.max_stops,
        average_speed_kmh=payload.average_speed_kmh,
    )
    if not planned['stops']:
        raise HTTPException(status_code=422, detail='No delivery orders fit this vehicle')

    run = DispatchRun(
        organization_id=organization_id,
        route_name=payload.route_name.strip(),
        plan_date=payload.plan_date,
        start_label=payload.start_label,
        start_latitude=payload.start_latitude,
        start_longitude=payload.start_longitude,
        vehicle_capacity_units=payload.vehicle_capacity_units,
        max_stops=payload.max_stops,
        total_distance_km=planned['total_distance_km'],
        estimated_duration_min=planned['estimated_duration_min'],
        expected_cash_etb=sum(
            (
                by_id[stop['order_id']].cod_amount_etb
                for stop in planned['stops']
            ),
            Decimal('0.00'),
        ),
        status='planned',
        driver_id=driver.id if driver else None,
        created_by_user_id=actor.id,
        stops_json=planned['stops'],
        unassigned_json=planned['unassigned'],
    )
    db.add(run)
    db.flush()
    for stop in planned['stops']:
        order = by_id[stop['order_id']]
        order.dispatch_run_id = run.id
        order.driver_id = driver.id if driver else None
        order.stop_sequence = stop['sequence']
        order.status = 'assigned'
    record_audit_event(
        db,
        event_type='dispatch.run_planned',
        entity_type='dispatch_run',
        entity_id=str(run.id),
        actor=actor,
        organization_id=str(organization_id),
        description=f'Planned {len(planned["stops"])} customer stops',
        payload={'order_count': len(planned['stops']), 'driver_id': driver.id if driver else None},
    )
    db.commit()
    db.refresh(run)
    return _run_detail(db, run)


@router.post('/plan-fleet', response_model=FleetDispatchPlanResponse, status_code=201)
def plan_fleet_dispatch(
    payload: FleetDispatchPlanRequest,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership = Depends(require_writable_workspace),
):
    organization_id = _org(actor, writable)
    order_ids = list(dict.fromkeys(payload.order_ids))
    try:
        order_uuids = [UUID(str(order_id)) for order_id in order_ids]
    except ValueError:
        raise HTTPException(status_code=422, detail='One or more order ids are invalid') from None
    orders = (
        db.execute(
            select(DeliveryOrder)
            .where(
                DeliveryOrder.organization_id == organization_id,
                DeliveryOrder.id.in_(order_uuids),
                DeliveryOrder.status == 'planned',
            )
            .with_for_update()
        )
        .scalars()
        .all()
    )
    by_id = {str(order.id): order for order in orders}
    if len(by_id) != len(order_ids):
        raise HTTPException(status_code=422, detail='One or more orders are not plannable')

    driver_ids = list(dict.fromkeys(vehicle.driver_id for vehicle in payload.vehicles))
    if len(driver_ids) != len(payload.vehicles):
        raise HTTPException(status_code=422, detail='Each vehicle must use a different driver')
    try:
        driver_uuids = [UUID(str(driver_id)) for driver_id in driver_ids]
    except ValueError:
        raise HTTPException(status_code=422, detail='One or more driver ids are invalid') from None
    drivers = (
        db.execute(
            select(Driver).where(
                Driver.organization_id == organization_id,
                Driver.id.in_(driver_uuids),
                Driver.status == 'active',
            )
        )
        .scalars()
        .all()
    )
    driver_by_id = {str(driver.id): driver for driver in drivers}
    if len(driver_by_id) != len(driver_ids):
        raise HTTPException(
            status_code=422,
            detail='One or more drivers are missing or inactive in this workspace',
        )

    customer_ids = {order.customer_id for order in orders}
    customers = (
        db.execute(
            select(Customer).where(
                Customer.organization_id == organization_id,
                Customer.id.in_(customer_ids),
            )
        )
        .scalars()
        .all()
    )
    customer_by_id = {customer.id: customer for customer in customers}
    if any(order.customer_id not in customer_by_id for order in orders):
        raise HTTPException(status_code=422, detail='A delivery order has no customer')

    start_time = payload.start_time or datetime.combine(
        payload.plan_date, time(8, 0), tzinfo=UTC
    )
    planned = plan_fleet_time_window_routes(
        start_label=payload.start_label,
        start_latitude=payload.start_latitude,
        start_longitude=payload.start_longitude,
        start_time=start_time,
        orders=[
            {
                'id': order.id,
                'order_no': order.order_no,
                'quantity_units': order.quantity_units,
                'priority': order.priority,
                'service_minutes': order.service_minutes,
                'window_start': order.window_start,
                'window_end': order.window_end,
                'latitude': customer_by_id[order.customer_id].latitude,
                'longitude': customer_by_id[order.customer_id].longitude,
            }
            for order in orders
        ],
        vehicles=[
            {
                'id': vehicle.driver_id,
                'driver_id': vehicle.driver_id,
                'vehicle_capacity_units': vehicle.vehicle_capacity_units,
                'max_stops': vehicle.max_stops,
                'average_speed_kmh': vehicle.average_speed_kmh,
            }
            for vehicle in payload.vehicles
        ],
    )
    if not planned['vehicles']:
        raise HTTPException(status_code=422, detail='No delivery orders fit this fleet')

    created_runs: list[DispatchRun] = []
    multiple_vehicles = len(planned['vehicles']) > 1
    for vehicle_plan in planned['vehicles']:
        driver_id = vehicle_plan['driver_id']
        driver = driver_by_id[driver_id]
        vehicle_plan_data = vehicle_plan['plan']
        vehicle = next(
            item for item in payload.vehicles if item.driver_id == driver_id
        )
        run = DispatchRun(
            organization_id=organization_id,
            route_name=_fleet_route_name(
                payload.route_name.strip(), driver.full_name, multiple_vehicles
            ),
            plan_date=payload.plan_date,
            start_label=payload.start_label,
            start_latitude=payload.start_latitude,
            start_longitude=payload.start_longitude,
            vehicle_capacity_units=vehicle.vehicle_capacity_units,
            max_stops=vehicle.max_stops,
            total_distance_km=vehicle_plan_data['total_distance_km'],
            estimated_duration_min=vehicle_plan_data['estimated_duration_min'],
            expected_cash_etb=sum(
                (by_id[stop['order_id']].cod_amount_etb for stop in vehicle_plan_data['stops']),
                Decimal('0.00'),
            ),
            status='planned',
            driver_id=driver.id,
            created_by_user_id=actor.id,
            stops_json=vehicle_plan_data['stops'],
            unassigned_json=[],
        )
        db.add(run)
        db.flush()
        for stop in vehicle_plan_data['stops']:
            order = by_id[stop['order_id']]
            order.dispatch_run_id = run.id
            order.driver_id = driver.id
            order.stop_sequence = stop['sequence']
            order.status = 'assigned'
        created_runs.append(run)

    record_audit_event(
        db,
        event_type='dispatch.fleet_planned',
        entity_type='dispatch_run',
        entity_id=str(created_runs[0].id),
        actor=actor,
        organization_id=str(organization_id),
        description=f'Planned {len(created_runs)} vehicle runs',
        payload={
            'run_ids': [str(run.id) for run in created_runs],
            'vehicle_count': len(created_runs),
            'order_count': sum(len(run.stops_json or []) for run in created_runs),
            'unassigned_count': len(planned['unassigned']),
        },
    )
    db.commit()
    for run in created_runs:
        db.refresh(run)
    return FleetDispatchPlanResponse(
        runs=[_run_detail(db, run) for run in created_runs],
        unassigned=planned['unassigned'],
    )


@router.get('/runs', response_model=list[DispatchRunRead])
def list_dispatch_runs(
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    return (
        db.execute(
            select(DispatchRun)
            .where(DispatchRun.organization_id == membership.organization_id)
            .order_by(DispatchRun.created_at.desc())
            .limit(100)
        )
        .scalars()
        .all()
    )


@router.get('/runs/{run_id}', response_model=DispatchRunDetail)
def get_dispatch_run(
    run_id: str,
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    run = organization_scoped_get(
        db,
        DispatchRun,
        run_id,
        membership.organization_id,
        not_found_detail='Dispatch run not found',
        include_legacy_null=False,
    )
    return _run_detail(db, run)


@router.post('/runs/{run_id}/driver-link', response_model=DriverLinkResponse)
def create_driver_link(
    run_id: str,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.OPERATOR, UserRole.ADMIN)),
    writable: OrganizationMembership = Depends(require_writable_workspace),
):
    organization_id = _org(actor, writable)
    run = organization_scoped_get(
        db,
        DispatchRun,
        run_id,
        organization_id,
        not_found_detail='Dispatch run not found',
        include_legacy_null=False,
    )
    if run.driver_id is None:
        raise HTTPException(status_code=409, detail='Assign a driver before creating a driver link')
    driver = organization_scoped_get(
        db,
        Driver,
        run.driver_id,
        organization_id,
        not_found_detail='Driver not found',
        include_legacy_null=False,
    )
    if driver.status != 'active':
        raise HTTPException(status_code=409, detail='Driver is not active')
    expires_at = datetime.now(UTC) + timedelta(hours=12)
    token = jwt.encode(
        {
            'sub': str(driver.id),
            'org_id': str(organization_id),
            'run_id': str(run.id),
            'scope': 'driver_run',
            'iat': int(datetime.now(UTC).timestamp()),
            'exp': int(expires_at.timestamp()),
            'jti': uuid4().hex,
        },
        settings.effective_jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )
    return DriverLinkResponse(
        token=token,
        # Keep the capability in the fragment so it is not sent to the web
        # server, access logs, or third-party referrers during page load.
        driver_url=f'{settings.console_url.rstrip("/")}/driver#token={token}',
        expires_at=expires_at,
    )


@router.post('/runs/{run_id}/close-cash', response_model=CashCloseSummary)
def close_dispatch_cash(
    run_id: str,
    payload: CashCloseRequest | None = None,
    db: Session = Depends(get_db),
    actor: User = Depends(require_roles(UserRole.ADMIN)),
    writable: OrganizationMembership = Depends(require_writable_workspace),
):
    organization_id = _org(actor, writable)
    run = organization_scoped_get(
        db,
        DispatchRun,
        run_id,
        organization_id,
        not_found_detail='Dispatch run not found',
        include_legacy_null=False,
    )
    if run.status == 'closed' or run.cash_closed_at is not None:
        raise HTTPException(status_code=409, detail='Cash is already closed for this run')
    orders = (
        db.execute(
            select(DeliveryOrder).where(
                DeliveryOrder.organization_id == organization_id,
                DeliveryOrder.dispatch_run_id == run.id,
            )
            .with_for_update()
        )
        .scalars()
        .all()
    )
    if not orders:
        raise HTTPException(status_code=409, detail='Dispatch run has no delivery orders')
    if any(order.status not in _TERMINAL_ORDER_STATUSES for order in orders):
        raise HTTPException(status_code=409, detail='All delivery orders must be terminal before cash close')
    # A failed or cancelled stop never creates a cash obligation. Only a
    # delivered stop contributes to the expected day-end cash position.
    expected = sum(
        (order.cod_amount_etb for order in orders if order.status == 'delivered'),
        Decimal('0.00'),
    )
    declared = sum(
        (order.collected_cash_etb or Decimal('0.00') for order in orders),
        Decimal('0.00'),
    )
    handed_over = (
        payload.handed_over_etb
        if payload is not None and payload.handed_over_etb is not None
        else declared
    )
    note = payload.note if payload is not None else None
    if (handed_over != expected or handed_over != declared) and not (note or '').strip():
        raise HTTPException(
            status_code=422,
            detail=(
                'A note is required when handed-over cash differs from '
                'expected or declared cash'
            ),
        )
    shortfall = max(expected - handed_over, Decimal('0.00'))
    overage = max(handed_over - expected, Decimal('0.00'))
    now = datetime.now(UTC)
    for order in orders:
        order.cash_settled_at = now
    run.status = 'closed'
    run.cash_closed_at = now
    run.cash_closed_by_user_id = actor.id
    run.cash_declared_etb = declared
    run.cash_handed_over_etb = handed_over
    run.cash_shortfall_etb = shortfall
    run.cash_overage_etb = overage
    run.cash_deposit_bank = payload.deposit_bank if payload is not None else None
    run.cash_deposit_reference = payload.deposit_reference if payload is not None else None
    run.cash_close_note = note
    record_audit_event(
        db,
        event_type='dispatch.cash_closed',
        entity_type='dispatch_run',
        entity_id=str(run.id),
        actor=actor,
        organization_id=str(organization_id),
        description=(
            f'Closed cash with {shortfall} ETB shortfall and {overage} ETB overage'
        ),
        payload={
            'expected_etb': str(expected),
            'collected_etb': str(declared),
            'declared_etb': str(declared),
            'handed_over_etb': str(handed_over),
            'shortfall_etb': str(shortfall),
            'overage_etb': str(overage),
            'deposit_bank': payload.deposit_bank if payload is not None else None,
            'deposit_reference': (
                payload.deposit_reference if payload is not None else None
            ),
            'note': note,
        },
    )
    db.commit()
    return CashCloseSummary(
        run_id=str(run.id),
        expected_etb=expected,
        collected_etb=declared,
        declared_etb=declared,
        handed_over_etb=handed_over,
        shortfall_etb=shortfall,
        overage_etb=overage,
        deposit_bank=payload.deposit_bank if payload is not None else None,
        deposit_reference=payload.deposit_reference if payload is not None else None,
        note=note,
        terminal_stops=len(orders),
        total_stops=len(orders),
        closed_at=now,
    )


def _driver_context(
    x_driver_token: str = Header(default='', alias='X-Driver-Token'),
    db: Session = Depends(get_db),
) -> tuple[DispatchRun, Driver]:
    if not x_driver_token:
        raise HTTPException(status_code=401, detail='Driver token required')
    try:
        payload = decode_access_token(x_driver_token)
        if payload.get('scope') != 'driver_run':
            raise ValueError('wrong scope')
        organization_id = UUID(str(payload['org_id']))
        run_id = UUID(str(payload['run_id']))
        driver_id = UUID(str(payload['sub']))
    except (KeyError, TypeError, ValueError):
        raise HTTPException(status_code=401, detail='Invalid driver token') from None
    run = db.get(DispatchRun, run_id)
    driver = db.get(Driver, driver_id)
    if (
        run is None
        or driver is None
        or run.organization_id != organization_id
        or driver.organization_id != organization_id
        or run.driver_id != driver.id
        or driver.status != 'active'
        or run.status == 'closed'
    ):
        raise HTTPException(status_code=403, detail='Driver access is not valid for this run')
    return run, driver


@router.get('/driver/manifest', response_model=DriverManifest)
def driver_manifest(
    context: tuple[DispatchRun, Driver] = Depends(_driver_context),
    db: Session = Depends(get_db),
):
    run, driver = context
    return DriverManifest(
        run_id=str(run.id),
        route_name=run.route_name,
        plan_date=run.plan_date,
        driver_id=str(driver.id),
        driver_name=driver.full_name,
        start_label=run.start_label,
        stops=_stops_for_run(db, run),
    )


@router.post('/driver/orders/{order_id}/status', response_model=DispatchStopRead)
def driver_update_status(
    order_id: str,
    payload: DriverStatusUpdate,
    context: tuple[DispatchRun, Driver] = Depends(_driver_context),
    db: Session = Depends(get_db),
):
    run, driver = context
    order = _order_in_org(db, run.organization_id, order_id)
    if order.dispatch_run_id != run.id or order.driver_id != driver.id:
        raise HTTPException(status_code=404, detail='Delivery order not found')
    if order.status in {'cancelled', 'delivered'}:
        raise HTTPException(status_code=409, detail='This delivery is already terminal')
    order.status = payload.status
    order.completed_at = datetime.now(UTC) if payload.status in _TERMINAL_ORDER_STATUSES else None
    if payload.note:
        order.notes = payload.note
    record_audit_event(
        db,
        event_type='dispatch.driver_status',
        entity_type='delivery_order',
        entity_id=str(order.id),
        organization_id=str(run.organization_id),
        description=f'Driver marked delivery {order.order_no} as {payload.status}',
        payload={'status': payload.status, 'driver_id': str(driver.id), 'note': payload.note},
    )
    db.commit()
    db.refresh(order)
    customer = db.get(Customer, order.customer_id)
    assert customer is not None
    stops = _stops_for_run(db, run)
    return next(stop for stop in stops if stop.order_id == str(order.id))


@router.post('/driver/orders/{order_id}/cash', response_model=DispatchStopRead)
def driver_declare_cash(
    order_id: str,
    payload: DriverCashDeclare,
    context: tuple[DispatchRun, Driver] = Depends(_driver_context),
    db: Session = Depends(get_db),
):
    run, driver = context
    order = _order_in_org(db, run.organization_id, order_id)
    if order.dispatch_run_id != run.id or order.driver_id != driver.id:
        raise HTTPException(status_code=404, detail='Delivery order not found')
    if order.status not in {'in_transit', 'delivered'}:
        raise HTTPException(status_code=409, detail='Cash is declared at delivery or in transit')
    if payload.collected_etb > order.cod_amount_etb:
        raise HTTPException(
            status_code=422,
            detail='Collected cash cannot exceed the cash-on-delivery amount',
        )
    if payload.collected_etb < order.cod_amount_etb and not (payload.note or '').strip():
        raise HTTPException(
            status_code=422,
            detail='A note is required when declaring less than the expected cash',
        )
    order.collected_cash_etb = payload.collected_etb
    order.cash_declared_at = datetime.now(UTC)
    order.cash_note = payload.note
    record_audit_event(
        db,
        event_type='dispatch.cash_declared',
        entity_type='delivery_order',
        entity_id=str(order.id),
        organization_id=str(run.organization_id),
        description=f'Driver declared {payload.collected_etb} ETB for {order.order_no}',
        payload={'collected_etb': str(payload.collected_etb), 'note': payload.note},
    )
    db.commit()
    db.refresh(order)
    stops = _stops_for_run(db, run)
    return next(stop for stop in stops if stop.order_id == str(order.id))


@router.post('/driver/orders/{order_id}/proof', response_model=DeliveryProofRead, status_code=201)
def driver_upload_proof(
    order_id: str,
    file: UploadFile = File(...),
    recipient_name: str | None = Form(default=None),
    notes: str | None = Form(default=None),
    proof_kind: str = Form(default='photo'),
    context: tuple[DispatchRun, Driver] = Depends(_driver_context),
    db: Session = Depends(get_db),
):
    run, driver = context
    order = _order_in_org(db, run.organization_id, order_id)
    if order.dispatch_run_id != run.id or order.driver_id != driver.id:
        raise HTTPException(status_code=404, detail='Delivery order not found')
    if file.content_type not in _PROOF_TYPES:
        raise HTTPException(status_code=415, detail='Proof must be a JPEG, PNG, or WebP image')
    content = file.file.read(_PROOF_MAX_BYTES + 1)
    if not content or len(content) > _PROOF_MAX_BYTES:
        raise HTTPException(status_code=413, detail='Proof image is too large')
    if not _has_expected_image_signature(content, file.content_type or ''):
        raise HTTPException(status_code=415, detail='Proof content does not match the declared image type')
    db.execute(
        select(Organization)
        .where(Organization.id == run.organization_id)
        .with_for_update()
    ).scalar_one()
    used_bytes = db.execute(
        select(
            func.coalesce(func.sum(func.length(DeliveryProof.file_data)), 0)
        ).where(DeliveryProof.organization_id == run.organization_id)
    ).scalar_one()
    if used_bytes + len(content) > settings.proof_org_quota_bytes:
        raise HTTPException(
            status_code=413,
            detail='Workspace proof storage is full',
        )
    existing_proofs = db.execute(
        select(func.count(DeliveryProof.id)).where(
            DeliveryProof.organization_id == run.organization_id,
            DeliveryProof.delivery_order_id == order.id,
        )
    ).scalar_one()
    if existing_proofs >= 5:
        raise HTTPException(
            status_code=409,
            detail='This delivery already has the maximum number of proofs',
        )
    proof = DeliveryProof(
        organization_id=run.organization_id,
        delivery_order_id=order.id,
        proof_sequence=existing_proofs + 1,
        proof_kind=proof_kind.strip()[:16] or 'photo',
        content_type=file.content_type,
        file_data=content,
        file_sha256=hashlib.sha256(content).hexdigest(),
        recipient_name=recipient_name,
        notes=notes,
        captured_at=datetime.now(UTC),
    )
    db.add(proof)
    try:
        db.flush()
        record_audit_event(
            db,
            event_type='dispatch.proof_uploaded',
            entity_type='delivery_order',
            entity_id=str(order.id),
            organization_id=str(run.organization_id),
            description=f'Proof uploaded for {order.order_no}',
            payload={'proof_kind': proof.proof_kind, 'content_type': proof.content_type},
        )
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail='This delivery already has the maximum number of proofs',
        ) from None
    db.refresh(proof)
    return DeliveryProofRead.model_validate(proof)


@router.get('/orders/{order_id}/proofs', response_model=list[DeliveryProofRead])
def list_order_proofs(
    order_id: str,
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    order = _order_in_org(db, membership.organization_id, order_id)
    return (
        db.execute(
            select(DeliveryProof)
            .where(
                DeliveryProof.organization_id == membership.organization_id,
                DeliveryProof.delivery_order_id == order.id,
            )
            .order_by(DeliveryProof.captured_at.desc())
        )
        .scalars()
        .all()
    )


@router.get('/orders/{order_id}/proofs/{proof_id}/file')
def get_order_proof_file(
    order_id: str,
    proof_id: str,
    db: Session = Depends(get_db),
    membership: OrganizationMembership = Depends(get_current_membership),
    _: User = Depends(require_roles(UserRole.VIEWER, UserRole.OPERATOR, UserRole.ADMIN)),
):
    order = _order_in_org(db, membership.organization_id, order_id)
    proof = organization_scoped_get(
        db,
        DeliveryProof,
        proof_id,
        membership.organization_id,
        not_found_detail='Delivery proof not found',
        include_legacy_null=False,
    )
    if proof.delivery_order_id != order.id:
        raise HTTPException(status_code=404, detail='Delivery proof not found')
    extension = {
        'image/jpeg': 'jpg',
        'image/png': 'png',
        'image/webp': 'webp',
    }.get(proof.content_type, 'bin')
    return Response(
        content=proof.file_data,
        media_type=proof.content_type,
        headers={
            'Content-Disposition': f'inline; filename="proof-{proof.id}.{extension}"',
            'Cache-Control': 'private, no-store',
            'X-Content-Type-Options': 'nosniff',
        },
    )
