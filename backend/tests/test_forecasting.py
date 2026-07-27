from datetime import date, timedelta

import pandas as pd

from app.services.forecasting import build_training_frame, forecast_weekly_demand


def test_build_training_frame_aggregates_weekly_quantities():
    orders = [
        {
            'order_date': date(2026, 1, 5),
            'quantity': 10,
            'warehouse_code': 'WH-001',
            'sku': 'SKU-1',
            'weather_avg_temp_c': 20.0,
            'weather_precip_mm': 2.0,
            'weather_disruption_index': 0.1,
        },
        {
            'order_date': date(2026, 1, 6),
            'quantity': 15,
            'warehouse_code': 'WH-001',
            'sku': 'SKU-1',
            'weather_avg_temp_c': 21.0,
            'weather_precip_mm': 1.5,
            'weather_disruption_index': 0.1,
        },
    ]

    frame = build_training_frame(orders)

    assert len(frame) == 1
    assert int(frame.iloc[0]['quantity']) == 25
    assert 'week_of_year' in frame.columns


def test_forecast_weekly_demand_returns_positive_predictions_for_horizon():
    base_date = date(2026, 1, 1)
    orders = []
    for week in range(10):
        for wh in ('WH-001', 'WH-002'):
            for sku in ('SKU-1', 'SKU-2'):
                orders.append(
                    {
                        'order_date': base_date + timedelta(days=7 * week),
                        'quantity': 20 + week,
                        'warehouse_code': wh,
                        'sku': sku,
                        'weather_avg_temp_c': 18.0 + week * 0.2,
                        'weather_precip_mm': 2.0,
                        'weather_disruption_index': 0.15,
                    }
                )

    weather_lookup = {
        'WH-001': {'weather_avg_temp_c': 21.0, 'weather_precip_mm': 3.0, 'weather_disruption_index': 0.2},
        'WH-002': {'weather_avg_temp_c': 19.0, 'weather_precip_mm': 2.5, 'weather_disruption_index': 0.25},
    }

    out = forecast_weekly_demand(orders=orders, warehouse_weather_lookup=weather_lookup, horizon_weeks=4)

    assert out.model_name == 'RandomForestRegressor'
    assert len(out.predictions) == 16
    assert all(p['predicted_demand'] >= 0 for p in out.predictions)
