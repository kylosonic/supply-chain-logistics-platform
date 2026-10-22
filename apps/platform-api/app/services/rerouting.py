from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.route import RouteSchedule, RouteStop
from app.models.shipment import Shipment


def generate_rerouting_plan(db: Session, alert_id: str, shipment_id: str) -> None:
    """Attach a reviewable saved-route candidate to an alert.

    This is deliberately not an autonomous rerouting engine. It never invents
    a carrier, cost, or recovery time. If no active saved schedule exists for
    the same origin/destination, the alert records that no candidate was found.
    """
    alert = db.get(Alert, alert_id)
    shipment = db.get(Shipment, shipment_id)

    if not alert or not shipment:
        return

    stmt = select(RouteSchedule).where(
        RouteSchedule.start_warehouse_id == shipment.origin_warehouse_id,
        RouteSchedule.status == 'active',
    ).join(
        RouteStop,
        RouteStop.route_schedule_id == RouteSchedule.id,
    ).where(
        RouteStop.warehouse_id == shipment.destination_warehouse_id,
    ).distinct()
    alternative_route = db.execute(stmt).scalars().first()

    if alternative_route is None:
        alert.payload = {
            'rerouting_status': 'no_saved_alternative',
            'rerouting_reason': (
                'No active saved schedule matches this shipment origin and destination. '
                'Create an alternative schedule before offering an auto-resolve action.'
            ),
        }
    else:
        alert.payload = {
            'rerouting_plan': {
                'proposed_route_id': str(alternative_route.id),
                'route_name': alternative_route.route_name,
                'estimated_duration_min': alternative_route.estimated_duration_min,
                'candidate_source': 'saved_active_schedule',
                'reasoning': (
                    'Matched an existing active schedule with the same origin and destination. '
                    'Operator review and confirmation are required before changing the shipment.'
                ),
            }
        }

    db.add(alert)
    db.commit()
