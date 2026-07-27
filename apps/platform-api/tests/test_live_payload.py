from app.services.live_feed import build_live_snapshot


def test_build_live_snapshot_shape():
    payload = build_live_snapshot(
        inventory_rows=[
            {'warehouse_code': 'WH-001', 'warehouse_name': 'Main', 'total_quantity_on_hand': 500, 'total_safety_stock': 120, 'utilization_percent': 45.5}
        ],
        route_rows=[
            {'id': 'r1', 'route_name': 'Route A', 'schedule_date': '2026-05-18', 'total_distance_km': 100.0, 'total_cost': 150.0, 'estimated_duration_min': 180, 'status': 'planned'}
        ],
        forecast_rows=[
            {'week_start': '2026-05-18', 'warehouse_code': 'WH-001', 'sku': 'SKU-001', 'predicted_demand': 82.0}
        ],
    )

    assert payload['type'] == 'live_update'
    assert 'server_time' in payload
    assert len(payload['inventory_overview']) == 1
    assert len(payload['route_summaries']) == 1
    assert len(payload['forecast_preview']) == 1
