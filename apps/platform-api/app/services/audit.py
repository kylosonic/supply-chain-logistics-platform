from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.audit_event import AuditEvent
from app.models.fleet_asset import FleetAsset
from app.models.route import RouteSchedule
from app.models.user import User
from app.utils.geo import haversine_miles


def resolve_actor_organization_id(db: Session, user: User | None) -> str | None:
    if user is None:
        return None

    from app.repositories import MembershipRepository
    return MembershipRepository(db).get_organization_id_for_user(user.id)


def _sanitize_payload(value: Any) -> Any:
    if isinstance(value, dict):
        return {k: str(v) if isinstance(v, UUID) else _sanitize_payload(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_sanitize_payload(item) for item in value]
    if isinstance(value, UUID):
        return str(value)
    return value


def record_audit_event(
    db: Session,
    *,
    event_type: str,
    entity_type: str,
    description: str,
    actor: User | None = None,
    entity_id: str | None = None,
    organization_id: str | None = None,
    payload: dict[str, Any] | list[Any] | None = None,
) -> AuditEvent:
    event = AuditEvent(
        event_type=event_type,
        entity_type=entity_type,
        entity_id=entity_id,
        actor_user_id=actor.id if actor else None,
        organization_id=organization_id or resolve_actor_organization_id(db, actor),
        description=description,
        payload=_sanitize_payload(payload),
    )
    db.add(event)
    return event


# ---------------------------------------------------------------------------
# Autonomous Exception Management
# ---------------------------------------------------------------------------

_MAX_RADIUS_MILES = 50.0


def auto_resolve_late_pickup(alert_id: UUID, db: Session) -> dict[str, Any]:
    """Automatically resolve a LATE_PICKUP alert by reassigning the
    closest IDLE fleet asset within 50 miles.

    Steps:
        1. Verify the alert exists and is of type ``LATE_PICKUP``.
        2. Look up the associated ``RouteSchedule`` to get origin coords.
        3. Query all ``FleetAsset`` rows with ``status='IDLE'`` that have
           known coordinates.
        4. Filter to those within 50 miles using the Haversine formula.
        5. Pick the closest one and assign it to the route.
        6. Mark the alert as ``AUTO_RESOLVED`` and commit.

    Args:
        alert_id: UUID of the alert to resolve.
        db: Active SQLAlchemy session.

    Returns:
        A dict summarising the resolution outcome.

    Raises:
        ValueError: If the alert is not found, is not a LATE_PICKUP type,
            has no associated route, or no eligible asset is available.
    """
    # 1. Fetch and validate the alert
    alert = db.execute(
        select(Alert).where(Alert.id == alert_id)
    ).scalar_one_or_none()

    if alert is None:
        raise ValueError(f"Alert '{alert_id}' not found")

    if alert.alert_type != 'LATE_PICKUP':
        raise ValueError(
            f"Alert '{alert_id}' is type '{alert.alert_type}', expected 'LATE_PICKUP'"
        )

    # 2. Extract origin coordinates from the associated route
    route_id = alert.related_entity_id
    if not route_id:
        raise ValueError(f"Alert '{alert_id}' has no related route entity")

    route = db.execute(
        select(RouteSchedule).where(RouteSchedule.id == route_id)
    ).scalar_one_or_none()

    if route is None:
        raise ValueError(f"RouteSchedule '{route_id}' not found")

    origin_lat = route.origin_latitude
    origin_lon = route.origin_longitude
    if origin_lat is None or origin_lon is None:
        raise ValueError(
            f"RouteSchedule '{route_id}' has no origin coordinates"
        )

    # 3. Query all IDLE assets with known positions
    idle_assets = db.execute(
        select(FleetAsset).where(
            FleetAsset.status == 'IDLE',
            FleetAsset.latitude.isnot(None),
            FleetAsset.longitude.isnot(None),
        )
    ).scalars().all()

    # 4. Filter within 50-mile radius using Haversine
    candidates: list[tuple[FleetAsset, float]] = []
    for asset in idle_assets:
        dist = haversine_miles(origin_lat, origin_lon, asset.latitude, asset.longitude)
        if dist <= _MAX_RADIUS_MILES:
            candidates.append((asset, dist))

    if not candidates:
        raise ValueError(
            f"No IDLE assets within {_MAX_RADIUS_MILES} miles of origin "
            f"({origin_lat}, {origin_lon})"
        )

    # 5. Select the closest asset
    candidates.sort(key=lambda pair: pair[1])
    closest_asset, closest_distance = candidates[0]

    # 6. Assign the asset to the route and resolve the alert
    route.assigned_asset_id = closest_asset.id
    closest_asset.status = 'ASSIGNED'

    alert.status = 'AUTO_RESOLVED'
    alert.resolved_at = datetime.now(tz=timezone.utc)
    alert.resolution_note = (
        f"Auto-resolved: assigned asset '{closest_asset.vehicle_code}' "
        f"({closest_distance:.1f} mi away)"
    )

    db.add(route)
    db.add(closest_asset)
    db.add(alert)
    db.commit()

    return {
        'alert_id': str(alert_id),
        'status': 'AUTO_RESOLVED',
        'assigned_asset_id': closest_asset.id,
        'assigned_vehicle_code': closest_asset.vehicle_code,
        'distance_miles': round(closest_distance, 2),
        'route_id': route_id,
    }