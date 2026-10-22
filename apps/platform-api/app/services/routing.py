from __future__ import annotations

import heapq
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.utils.geo import haversine_km  # noqa: F401 - re-exported for tests


@dataclass
class Node:
    code: str
    latitude: float
    longitude: float


@dataclass
class Delivery:
    warehouse_code: str
    demand_units: int


def weighted_leg_cost(
    distance_km: float,
    speed_kmh: float,
    cost_per_km: float,
    weights: dict[str, float],
) -> tuple[float, float, float]:
    if speed_kmh <= 0:
        raise ValueError('speed_kmh must be positive')
    time_min = (distance_km / speed_kmh) * 60
    monetary_cost = distance_km * cost_per_km
    weighted = (
        weights.get('distance', 0.5) * distance_km
        + weights.get('time', 0.3) * time_min
        + weights.get('cost', 0.2) * monetary_cost
    )
    return weighted, time_min, monetary_cost


def _weighted_components(
    distance_km: float,
    speed_kmh: float,
    cost_per_km: float,
    weights: dict[str, float],
) -> dict[str, float]:
    """Return the contribution of each factor to this leg's weighted score.

    The components are in the same units the optimizer already uses; they are
    not cross-metric normalisations. They are used only to explain which
    configured factor dominated a decision.
    """
    time_min = (distance_km / speed_kmh) * 60
    monetary_cost = distance_km * cost_per_km
    return {
        'distance': weights.get('distance', 0.5) * distance_km,
        'time': weights.get('time', 0.3) * time_min,
        'cost': weights.get('cost', 0.2) * monetary_cost,
    }


def _dominant_factor(components: dict[str, float]) -> str:
    if not components or max(components.values(), default=0.0) <= 0:
        return 'none'
    return max(components, key=lambda key: components[key])


def dijkstra_shortest_paths(
    nodes: dict[str, Node],
    start_code: str,
    speed_kmh: float,
    cost_per_km: float,
    weights: dict[str, float],
) -> dict[str, float]:
    dist: dict[str, float] = {code: float('inf') for code in nodes}
    dist[start_code] = 0.0
    pq: list[tuple[float, str]] = [(0.0, start_code)]

    while pq:
        current_cost, u = heapq.heappop(pq)
        if current_cost > dist[u]:
            continue

        for v, n in nodes.items():
            if v == u:
                continue
            d = haversine_km(nodes[u].latitude, nodes[u].longitude, n.latitude, n.longitude)
            edge_cost, _, _ = weighted_leg_cost(
                d,
                speed_kmh=speed_kmh,
                cost_per_km=cost_per_km,
                weights=weights,
            )
            cand = current_cost + edge_cost
            if cand < dist[v]:
                dist[v] = cand
                heapq.heappush(pq, (cand, v))

    return dist


def optimize_route_greedy(
    nodes: dict[str, Node],
    start_code: str,
    deliveries: list[Delivery],
    vehicle_capacity_units: int,
    max_stops: int,
    speed_kmh: float,
    cost_per_km: float,
    weights: dict[str, float],
    forced_first_code: str | None = None,
) -> dict:
    if start_code not in nodes:
        raise ValueError('start warehouse not found in node map')

    if not deliveries:
        raise ValueError('at least one delivery is required')

    unknown_codes = sorted({d.warehouse_code for d in deliveries if d.warehouse_code not in nodes})
    if unknown_codes:
        raise ValueError(
            f'delivery warehouse not found in node map: {", ".join(unknown_codes)}'
        )
    if any(d.warehouse_code == start_code for d in deliveries):
        raise ValueError('start warehouse cannot also be a delivery target')

    # Assign every demand row for a destination together so a later duplicate
    # is never silently discarded when that warehouse is selected.
    demand_by_code: dict[str, int] = {}
    for delivery in deliveries:
        demand_by_code[delivery.warehouse_code] = (
            demand_by_code.get(delivery.warehouse_code, 0) + delivery.demand_units
        )
    pending = [
        Delivery(warehouse_code=code, demand_units=demand)
        for code, demand in demand_by_code.items()
    ]
    capacity_left = vehicle_capacity_units
    current_code = start_code
    current_time = datetime.now(UTC)

    stops = []
    total_distance = 0.0
    total_cost = 0.0
    total_minutes = 0.0
    cumulative_load = 0
    factor_totals = {'distance': 0.0, 'time': 0.0, 'cost': 0.0}
    decision_trace: list[dict] = []
    capacity_excluded_codes: set[str] = set()

    for sequence in range(1, max_stops + 1):
        excluded_now = {
            delivery.warehouse_code
            for delivery in pending
            if delivery.demand_units > capacity_left
        }
        capacity_excluded_codes.update(excluded_now)
        feasible = [d for d in pending if d.demand_units <= capacity_left]
        if not feasible:
            break

        capacity_excluded_count = len(excluded_now)

        scored = []
        for demand in feasible:
            src = nodes[current_code]
            dst = nodes[demand.warehouse_code]
            distance = haversine_km(src.latitude, src.longitude, dst.latitude, dst.longitude)
            weighted, minutes, cost = weighted_leg_cost(
                distance,
                speed_kmh=speed_kmh,
                cost_per_km=cost_per_km,
                weights=weights,
            )
            components = _weighted_components(distance, speed_kmh, cost_per_km, weights)
            scored.append((weighted, demand, distance, minutes, cost, components))

        # Deterministic tie-break: identical scores resolve by warehouse code,
        # never by the incoming delivery order.
        scored.sort(key=lambda item: (item[0], item[1].warehouse_code))
        selected = scored[0]
        if forced_first_code and sequence == 1:
            selected = next(
                (item for item in scored if item[1].warehouse_code == forced_first_code),
                scored[0],
            )
        _, chosen, leg_distance, leg_minutes, leg_cost, components = selected
        runner_up = next(
            (item for item in scored if item[1].warehouse_code != chosen.warehouse_code),
            None,
        )

        total_distance += leg_distance
        total_cost += leg_cost
        total_minutes += leg_minutes
        for factor, value in components.items():
            factor_totals[factor] += value
        capacity_left -= chosen.demand_units
        cumulative_load += chosen.demand_units
        current_time = current_time + timedelta(minutes=leg_minutes)

        decision_trace.append({
            'sequence': sequence,
            'chosen_warehouse_code': chosen.warehouse_code,
            'chosen_weighted_cost': round(selected[0], 2),
            'runner_up_warehouse_code': runner_up[1].warehouse_code if runner_up else None,
            'runner_up_weighted_cost': round(runner_up[0], 2) if runner_up else None,
            'margin': round(runner_up[0] - selected[0], 2) if runner_up else None,
            'dominant_factor': _dominant_factor(components),
            'factor_components': {key: round(value, 2) for key, value in components.items()},
            'capacity_excluded_count': capacity_excluded_count,
        })

        stops.append({
            'sequence': sequence,
            'warehouse_code': chosen.warehouse_code,
            'demand_units': chosen.demand_units,
            'leg_distance_km': round(leg_distance, 2),
            'cumulative_distance_km': round(total_distance, 2),
            'latitude': nodes[chosen.warehouse_code].latitude,
            'longitude': nodes[chosen.warehouse_code].longitude,
            'estimated_arrival': current_time,
        })

        current_code = chosen.warehouse_code
        pending = [d for d in pending if d.warehouse_code != chosen.warehouse_code]

    selected_codes = {stop['warehouse_code'] for stop in stops}
    unassigned = [
        {'warehouse_code': d.warehouse_code, 'demand_units': d.demand_units}
        for d in deliveries
        if d.warehouse_code not in selected_codes
    ]

    return {
        'objective': 'weighted_cost',
        'total_distance_km': round(total_distance, 2),
        'total_cost': round(total_cost, 2),
        'estimated_duration_min': int(round(total_minutes)),
        'capacity_used': cumulative_load,
        'stops': stops,
        'decision_trace': decision_trace,
        'factor_totals': {key: round(value, 2) for key, value in factor_totals.items()},
        'capacity_excluded_count': len(capacity_excluded_codes),
        'unassigned_deliveries': unassigned,
    }
