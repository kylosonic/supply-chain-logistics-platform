import uuid
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.security import get_current_membership
from app.models.membership import OrganizationMembership
from app.services.weather import simulated_weather_features

router = APIRouter()

class WeatherRiskZone(BaseModel):
    id: str
    severity_score: int
    polygon: list[list[float]]
    source: str = 'simulated'

@router.get('/risk-zones', response_model=list[WeatherRiskZone])
def get_weather_risk_zones(
    _membership: OrganizationMembership = Depends(get_current_membership),
):
    """
    Returns explicitly simulated weather risk zones based on a deterministic
    disruption model. Do not present these as live weather observations.
    """
    zones = []
    target_date = date.today()
    
    # Grid around Addis Ababa region
    lat_start, lat_end, lat_step = 8.0, 10.0, 0.4
    lng_start, lng_end, lng_step = 37.5, 39.5, 0.4
    
    lat = lat_start
    while lat <= lat_end:
        lng = lng_start
        while lng <= lng_end:
            features = simulated_weather_features(target_date, lat, lng)
            disruption = features.get('weather_disruption_index', 0)
            
            if disruption > 0.5:
                # Severity scale 1 to 10
                severity = min(10, max(1, int(disruption * 10)))
                # Create a rectangle polygon around this point
                polygon = [
                    [lat - 0.2, lng - 0.2],
                    [lat - 0.2, lng + 0.2],
                    [lat + 0.2, lng + 0.2],
                    [lat + 0.2, lng - 0.2]
                ]
                zones.append(WeatherRiskZone(
                    id=f"zone-{uuid.uuid4().hex[:8]}",
                    severity_score=severity,
                    polygon=polygon,
                    source='simulated',
                ))
            lng += lng_step
        lat += lat_step
        
    return zones
