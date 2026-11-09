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


def plan_fleet_time_window_routes(
    *,
    start_label: str,
    start_latitude: float,
    start_longitude: float,
    start_time: datetime | None,
    orders: list[dict[str, Any]],
    vehicles: list[dict[str, Any]],
) -> dict[str, Any]:
    """Assign orders across vehicles, then plan each vehicle's stop sequence.

    This is a deterministic capacity- and window-aware heuristic. It assigns
    each order to the vehicle with the lowest immediate distance/lateness
    penalty, then runs the existing single-vehicle planner over that allocation.
    It is intentionally transparent rather than claiming global optimality.
    """
    if not vehicles:
        raise ValueError('At least one vehicle is required')
    if len({str(vehicle['id']) for vehicle in vehicles}) != len(vehicles):
        raise ValueError('Vehicle ids must be unique')
    if any(float(vehicle['average_speed_kmh']) <= 0 for vehicle in vehicles):
        raise ValueError('average_speed_kmh must be positive')

    base_time = _as_utc(
        start_time,
        datetime.combine(datetime.now(UTC).date(), time(8, 0), tzinfo=UTC),
    )
    states: dict[str, dict[str, Any]] = {}
    for vehicle in vehicles:
        vehicle_id = str(vehicle['id'])
        states[vehicle_id] = {
            'vehicle_id': vehicle_id,
            'capacity_left': int(vehicle['vehicle_capacity_units']),
            'max_stops': int(vehicle['max_stops']),
            'average_speed_kmh': float(vehicle['average_speed_kmh']),
            'current_lat': start_latitude,
            'current_lng': start_longitude,
            'current_time': base_time,
            'orders': [],
        }

    def deadline(order: dict[str, Any]) -> datetime:
        window_end = _optional_utc(order.get('window_end'))
        return window_end or datetime.max.replace(tzinfo=UTC)

    pending = sorted(
        orders,
        key=lambda order: (
            deadline(order),
            -int(order.get('priority', 3)),
            str(order['order_no']),
        ),
    )
    unassigned: list[dict[str, str]] = []

    for order in pending:
        quantity = int(order['quantity_units'])
        candidates: list[tuple[float, str, float, int, datetime]] = []
        for state in states.values():
            if (
                quantity > state['capacity_left']
                or len(state['orders']) >= state['max_stops']
            ):
                continue
            distance = haversine_km(
                state['current_lat'],
                state['current_lng'],
                order['latitude'],
                order['longitude'],
            )
            travel_minutes = int(round((distance / state['average_speed_kmh']) * 60))
            arrival = state['current_time'] + timedelta(minutes=travel_minutes)
            window_start = _optional_utc(order.get('window_start'))
            window_end = _optional_utc(order.get('window_end'))
            if window_start is not None and arrival < window_start:
                arrival = window_start
            lateness_minutes = (
                int((arrival - window_end).total_seconds() // 60)
                if window_end is not None and arrival > window_end
                else 0
            )
            priority_penalty = (5 - int(order.get('priority', 3))) * 0.25
            load_balance_penalty = len(state['orders']) * 0.05
            score = distance + (lateness_minutes * 2.0) + priority_penalty + load_balance_penalty
            candidates.append(
                (score, state['vehicle_id'], distance, travel_minutes, arrival)
            )

        if not candidates:
            max_capacity = max(
                int(vehicle['vehicle_capacity_units']) for vehicle in vehicles
            )
            unassigned.append(
                {
                    'order_id': str(order['id']),
                    'order_no': str(order['order_no']),
                    'reason': (
                        'exceeds_vehicle_capacity'
                        if quantity > max_capacity
                        else 'vehicle_capacity_or_stop_limit_reached'
                    ),
                }
            )
            continue

        _score, vehicle_id, distance, travel_minutes, arrival = min(
            candidates,
            key=lambda item: (item[0], item[1]),
        )
        state = states[vehicle_id]
        state['orders'].append(order)
        state['capacity_left'] -= quantity
        state['current_lat'] = order['latitude']
        state['current_lng'] = order['longitude']
        state['current_time'] = arrival + timedelta(
            minutes=int(order.get('service_minutes', 0))
        )

    planned_vehicles = []
    for vehicle in vehicles:
        state = states[str(vehicle['id'])]
        if not state['orders']:
            continue
        plan = plan_time_window_route(
            start_label=start_label,
            start_latitude=start_latitude,
            start_longitude=start_longitude,
            start_time=base_time,
            orders=state['orders'],
            vehicle_capacity_units=int(vehicle['vehicle_capacity_units']),
            max_stops=int(vehicle['max_stops']),
            average_speed_kmh=float(vehicle['average_speed_kmh']),
        )
        planned_vehicles.append(
            {
                'vehicle_id': str(vehicle['id']),
                'driver_id': str(vehicle['driver_id']),
                'plan': plan,
            }
        )

    return {
        'vehicles': planned_vehicles,
        'unassigned': unassigned,
    }
