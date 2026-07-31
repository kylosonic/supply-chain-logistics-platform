import time
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.alert import Alert
from app.models.shipment import Shipment
from app.models.route import RouteSchedule

def generate_rerouting_plan(db: Session, alert_id: str, shipment_id: str):
    # Simulate an expensive algorithm to generate a new route schedule
    time.sleep(2)
    
    alert = db.get(Alert, alert_id)
    shipment = db.get(Shipment, shipment_id)
    
    if not alert or not shipment:
        return

    # In a real scenario, this would query an optimization engine.
    # We will simulate finding a route schedule from the same origin to destination.
    # If one doesn't exist, we fallback to a mock schedule id.
    stmt = select(RouteSchedule).where(
        RouteSchedule.origin_warehouse_id == shipment.origin_warehouse_id,
        RouteSchedule.destination_warehouse_id == shipment.destination_warehouse_id,
        RouteSchedule.status == 'active'
    )
    alternative_route = db.execute(stmt).scalars().first()
    
    new_route_id = alternative_route.id if alternative_route else str(uuid.uuid4())
    new_carrier = alternative_route.carrier if alternative_route else "Expedited Freight Inc"
    
    # Update the alert with the generated rerouting plan
    plan = {
        "rerouting_plan": {
            "proposed_route_id": new_route_id,
            "carrier": new_carrier,
            "estimated_recovery_time_hrs": 12,
            "additional_cost_usd": 450.00,
            "reasoning": "Selected fastest alternative route with available capacity."
        }
    }
    
    alert.payload = plan
    db.add(alert)
    db.commit()
