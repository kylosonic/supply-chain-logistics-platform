from __future__ import annotations

from datetime import date


def simulated_weather_features(target_date: date, latitude: float, longitude: float) -> dict[str, float]:
    """Deterministic pseudo-weather for reproducible local development."""
    day_of_year = target_date.timetuple().tm_yday
    seasonal = 15 + 10 * __import__('math').sin((2 * __import__('math').pi * day_of_year) / 365)
    geo_adjust = (abs(latitude) * 0.05) + (abs(longitude) * 0.01)

    avg_temp_c = round(seasonal - geo_adjust, 2)
    precip_mm = round(max(0.0, 3 + 2 * __import__('math').cos((2 * __import__('math').pi * day_of_year) / 30)), 2)
    disruption = min(1.0, max(0.0, round((precip_mm / 20) + (abs(latitude) / 200), 3)))

    return {
        'weather_avg_temp_c': avg_temp_c,
        'weather_precip_mm': precip_mm,
        'weather_disruption_index': disruption,
    }
