from datetime import date
from fastapi import APIRouter, Depends
import uuid

from app.api.security import get_current_user
from app.models.user import User
from app.services.weather import simulated_weather_features
from pydantic import BaseModel

router = APIRouter()

class WeatherRiskZone(BaseModel):
    id: str
    severity_score: int
    polygon: list[list[float]]

@router.get('/risk-zones', response_model=list[WeatherRiskZone])
def get_weather_risk_zones(user: User = Depends(get_current_user)):
    """
    Returns simulated weather risk zones based on the disruption index.
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
                    polygon=polygon
                ))
            lng += lng_step
        lat += lat_step
        
    # If the simulated logic yields no zones, inject a mock one for demonstration
    if not zones:
        zones.append(WeatherRiskZone(
            id="mock-storm-alpha",
            severity_score=8,
            polygon=[
                [8.8, 38.6],
                [8.8, 38.9],
                [9.1, 38.9],
                [9.1, 38.6]
            ]
        ))
        
    return zones
