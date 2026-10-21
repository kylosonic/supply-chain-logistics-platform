from datetime import date, timedelta

from app.services import forecasting
from app.services.forecasting import (
    _MODEL_CACHE_LIMIT,
    _remember_model,
    _training_frame_hash,
    build_training_frame,
    forecast_weekly_demand,
)


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
    assert out.quality['status'] == 'validated'
    assert out.quality['history_weeks'] == 10
    assert out.quality['holdout_weeks'] == 2
    assert out.quality['wape_percent'] is not None
    assert 'aggregated across all warehouse/SKU rows' in out.quality['caveat']
    assert all(
        p['planning_low'] <= p['predicted_demand'] <= p['planning_high']
        for p in out.predictions
    )


def test_forecast_quality_is_honest_when_history_is_too_short():
    orders = []
    for week in range(2):
        orders.append(
            {
                'order_date': date(2026, 2, 2) + timedelta(days=7 * week),
                'quantity': 12,
                'warehouse_code': 'WH-001',
                'sku': 'SKU-1',
                'weather_avg_temp_c': 20.0,
                'weather_precip_mm': 2.0,
                'weather_disruption_index': 0.1,
            }
        )

    out = forecast_weekly_demand(
        orders=orders,
        warehouse_weather_lookup={
            'WH-001': {
                'weather_avg_temp_c': 20.0,
                'weather_precip_mm': 2.0,
                'weather_disruption_index': 0.1,
            }
        },
        horizon_weeks=1,
    )

    assert out.quality['status'] == 'insufficient_history'
    assert out.quality['history_weeks'] == 2
    assert out.quality['holdout_weeks'] == 0
    assert out.quality['wape_percent'] is None
    assert 'No held-out backtest' in out.quality['caveat']
    assert len(out.predictions) == 1
    assert out.predictions[0]['planning_low'] <= out.predictions[0]['predicted_demand']
    assert out.predictions[0]['predicted_demand'] <= out.predictions[0]['planning_high']


def test_training_hash_changes_when_distribution_changes_with_same_totals():
    base = {
        'order_date': date(2026, 3, 2),
        'warehouse_code': 'WH-001',
        'sku': 'SKU-1',
        'weather_avg_temp_c': 20.0,
        'weather_precip_mm': 2.0,
        'weather_disruption_index': 0.1,
    }
    next_week = {**base, 'order_date': date(2026, 3, 9)}
    first = build_training_frame([{**base, 'quantity': 10}, {**next_week, 'quantity': 10}])
    second = build_training_frame([{**base, 'quantity': 5}, {**next_week, 'quantity': 15}])

    assert int(first['quantity'].sum()) == int(second['quantity'].sum())
    assert _training_frame_hash(first) != _training_frame_hash(second)


def test_zero_actual_holdout_does_not_claim_an_error_widened_range():
    orders = [
        {
            'order_date': date(2026, 4, 6) + timedelta(days=7 * week),
            'quantity': 0,
            'warehouse_code': 'WH-001',
            'sku': 'SKU-1',
            'weather_avg_temp_c': 20.0,
            'weather_precip_mm': 2.0,
            'weather_disruption_index': 0.1,
        }
        for week in range(4)
    ]

    out = forecast_weekly_demand(
        orders=orders,
        warehouse_weather_lookup={
            'WH-001': {
                'weather_avg_temp_c': 20.0,
                'weather_precip_mm': 2.0,
                'weather_disruption_index': 0.1,
            }
        },
        horizon_weeks=1,
    )

    assert out.quality['wape_percent'] is None
    assert out.quality['status'] == 'limited'
    assert out.quality['range_basis'] == 'ensemble_p10_p90'
    assert out.predictions[0]['planning_low'] == 0
    assert out.predictions[0]['planning_high'] == 0


def test_trained_model_cache_never_exceeds_the_documented_limit():
    forecasting._trained_model_cache.clear()
    try:
        for index in range(_MODEL_CACHE_LIMIT + 1):
            _remember_model(f'frame-{index}', object())  # type: ignore[arg-type]

        assert len(forecasting._trained_model_cache) == _MODEL_CACHE_LIMIT
        assert 'frame-0' not in forecasting._trained_model_cache
        assert f'frame-{_MODEL_CACHE_LIMIT}' in forecasting._trained_model_cache
    finally:
        forecasting._trained_model_cache.clear()
