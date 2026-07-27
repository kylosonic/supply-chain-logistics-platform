from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from math import asin, cos, radians, sin, sqrt
import heapq


@dataclass
class Node:
    code: str
    latitude: float
    longitude: float


@dataclass
class Delivery:
    warehouse_code: str
    demand_units: int


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    c = 2 * asin(sqrt(a))
    return r * c


def weighted_leg_cost(distance_km: float, speed_kmh: float, cost_per_km: float, weights: dict[str, float]) -> tuple[float, float, float]:
    time_min = (distance_km / speed_kmh) * 60
    monetary_cost = distance_km * cost_per_km
    weighted = (
        weights.get('distance', 0.5) * distance_km
        + weights.get('time', 0.3) * time_min
        + weights.get('cost', 0.2) * monetary_cost
    )
    return weighted, time_min, monetary_cost


def dijkstra_shortest_paths(nodes: dict[str, Node], start_code: str, speed_kmh: float, cost_per_km: float, weights: dict[str, float]) -> dict[str, float]:
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
            edge_cost, _, _ = weighted_leg_cost(d, speed_kmh=speed_kmh, cost_per_km=cost_per_km, weights=weights)
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
) -> dict:
    if start_code not in nodes:
        raise ValueError('start warehouse not found in node map')

    pending = [d for d in deliveries if d.warehouse_code in nodes and d.warehouse_code != start_code]
    capacity_left = vehicle_capacity_units
    current_code = start_code
    current_time = datetime.now(UTC)

    stops = []
    total_distance = 0.0
    total_cost = 0.0
    total_minutes = 0.0
    cumulative_load = 0

    for sequence in range(1, max_stops + 1):
        feasible = [d for d in pending if d.demand_units <= capacity_left]
        if not feasible:
            break

        scored = []
        for demand in feasible:
            src = nodes[current_code]
            dst = nodes[demand.warehouse_code]
            distance = haversine_km(src.latitude, src.longitude, dst.latitude, dst.longitude)
            weighted, minutes, cost = weighted_leg_cost(distance, speed_kmh=speed_kmh, cost_per_km=cost_per_km, weights=weights)
            scored.append((weighted, demand, distance, minutes, cost))

        scored.sort(key=lambda x: x[0])
        _, chosen, leg_distance, leg_minutes, leg_cost = scored[0]

        total_distance += leg_distance
        total_cost += leg_cost
        total_minutes += leg_minutes
        capacity_left -= chosen.demand_units
        cumulative_load += chosen.demand_units
        current_time = current_time + timedelta(minutes=leg_minutes)

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

    return {
        'objective': 'weighted_cost',
        'total_distance_km': round(total_distance, 2),
        'total_cost': round(total_cost, 2),
        'estimated_duration_min': int(round(total_minutes)),
        'capacity_used': cumulative_load,
        'stops': stops,
        'unassigned_deliveries': [
            {'warehouse_code': d.warehouse_code, 'demand_units': d.demand_units} for d in pending
        ],
    }
