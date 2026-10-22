from __future__ import annotations

from datetime import UTC, datetime, time, timedelta
from typing import Any

from app.utils.geo import haversine_km


def _as_utc(value: datetime | None, fallback: datetime) -> datetime:
    if value is None:
        return fallback
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def _optional_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)


def plan_time_window_route(
    *,
    start_label: str,
    start_latitude: float,
    start_longitude: float,
    start_time: datetime | None,
    orders: list[dict[str, Any]],
    vehicle_capacity_units: int,
    max_stops: int,
    average_speed_kmh: float,
) -> dict[str, Any]:
    """Deterministic time-window-aware greedy planner.

    This is intentionally a transparent heuristic, not a global VRP solver.
    Capacity, stop count, travel time, service time, windows, and priority
    penalties are visible in the resulting stop evidence.
    """
    if average_speed_kmh <= 0:
        raise ValueError('average_speed_kmh must be positive')

    pending = list(orders)
    current_lat = start_latitude
    current_lng = start_longitude
    current_time = _as_utc(
        start_time,
        datetime.combine(datetime.now(UTC).date(), time(8, 0), tzinfo=UTC),
    )
    capacity_left = vehicle_capacity_units
    stops: list[dict[str, Any]] = []
    total_distance = 0.0
    total_minutes = 0

    for sequence in range(1, max_stops + 1):
        feasible = [order for order in pending if order['quantity_units'] <= capacity_left]
        if not feasible:
            break

        scored: list[tuple[float, dict[str, Any], float, int, datetime]] = []
        for order in feasible:
            distance = haversine_km(
                current_lat,
                current_lng,
                order['latitude'],
                order['longitude'],
            )
            travel_minutes = int(round((distance / average_speed_kmh) * 60))
            arrival = current_time + timedelta(minutes=travel_minutes)
            window_start = _optional_utc(order.get('window_start'))
            window_end = _optional_utc(order.get('window_end'))
            if window_start is not None and arrival < window_start:
                arrival = window_start
            lateness_minutes = 0
            if window_end is not None and arrival > window_end:
                lateness_minutes = int((arrival - window_end).total_seconds() // 60)

            # Distance is the base cost. Lateness is deliberately expensive,
            # and higher-priority orders receive a small, bounded preference.
            score = distance + (lateness_minutes * 2.0) + ((5 - int(order.get('priority', 3))) * 0.25)
            scored.append((score, order, distance, travel_minutes, arrival))

        scored.sort(key=lambda item: (item[0], item[1]['order_no']))
        _score, chosen, distance, travel_minutes, arrival = scored[0]
        window_end = _optional_utc(chosen.get('window_end'))
        stops.append(
            {
                'order_id': str(chosen['id']),
                'order_no': chosen['order_no'],
                'sequence': sequence,
                'planned_arrival': arrival.isoformat(),
                'travel_minutes': travel_minutes,
                'leg_distance_km': round(distance, 2),
                'late_minutes': (
                    int((arrival - window_end).total_seconds() // 60)
                    if window_end is not None and arrival > window_end
                    else 0
                ),
            }
        )
        total_distance += distance
        total_minutes += travel_minutes + int(chosen.get('service_minutes', 0))
        current_time = arrival + timedelta(minutes=int(chosen.get('service_minutes', 0)))
        current_lat = chosen['latitude']
        current_lng = chosen['longitude']
        capacity_left -= int(chosen['quantity_units'])
        pending = [order for order in pending if order['id'] != chosen['id']]

    selected_ids = {stop['order_id'] for stop in stops}
    unassigned = [
        {
            'order_id': str(order['id']),
            'order_no': order['order_no'],
            'reason': (
                'exceeds_remaining_capacity'
                if int(order['quantity_units']) > capacity_left
                else 'max_stops_reached'
            ),
        }
        for order in pending
        if str(order['id']) not in selected_ids
    ]
    return {
        'start_label': start_label,
        'start_latitude': start_latitude,
        'start_longitude': start_longitude,
        'stops': stops,
        'unassigned': unassigned,
        'capacity_used': vehicle_capacity_units - capacity_left,
        'total_distance_km': round(total_distance, 2),
        'estimated_duration_min': total_minutes,
        'start_time': current_time,
    }
