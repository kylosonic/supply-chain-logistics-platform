from app.services.routing import Delivery, Node, dijkstra_shortest_paths, haversine_km, optimize_route_greedy


def test_haversine_km_zero_distance_for_same_point():
    d = haversine_km(9.0, 38.0, 9.0, 38.0)
    assert round(d, 6) == 0.0


def test_dijkstra_shortest_paths_returns_all_nodes():
    nodes = {
        'WH-001': Node(code='WH-001', latitude=9.03, longitude=38.74),
        'WH-002': Node(code='WH-002', latitude=9.05, longitude=38.76),
        'WH-003': Node(code='WH-003', latitude=9.02, longitude=38.70),
    }

    dist = dijkstra_shortest_paths(
        nodes=nodes,
        start_code='WH-001',
        speed_kmh=45,
        cost_per_km=1.5,
        weights={'distance': 0.5, 'time': 0.3, 'cost': 0.2},
    )

    assert set(dist.keys()) == {'WH-001', 'WH-002', 'WH-003'}
    assert dist['WH-001'] == 0.0
    assert all(v >= 0 for v in dist.values())


def test_optimize_route_greedy_respects_vehicle_capacity():
    nodes = {
        'WH-001': Node(code='WH-001', latitude=9.03, longitude=38.74),
        'WH-002': Node(code='WH-002', latitude=9.04, longitude=38.75),
        'WH-003': Node(code='WH-003', latitude=9.08, longitude=38.79),
        'WH-004': Node(code='WH-004', latitude=9.12, longitude=38.83),
    }
    deliveries = [
        Delivery(warehouse_code='WH-002', demand_units=80),
        Delivery(warehouse_code='WH-003', demand_units=60),
        Delivery(warehouse_code='WH-004', demand_units=70),
    ]

    out = optimize_route_greedy(
        nodes=nodes,
        start_code='WH-001',
        deliveries=deliveries,
        vehicle_capacity_units=130,
        max_stops=10,
        speed_kmh=45,
        cost_per_km=1.5,
        weights={'distance': 0.5, 'time': 0.3, 'cost': 0.2},
    )

    assert out['capacity_used'] <= 130
    assert out['total_distance_km'] >= 0
    assert len(out['stops']) >= 1
    assert len(out['unassigned_deliveries']) >= 1
