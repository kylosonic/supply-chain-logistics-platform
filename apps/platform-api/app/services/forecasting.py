from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from functools import lru_cache
import hashlib
import json
from uuid import UUID

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.services.weather import simulated_weather_features
from app.utils.geo import haversine_km


@dataclass
class ForecastResult:
    model_name: str
    predictions: list[dict]


def build_training_frame(orders: list[dict]) -> pd.DataFrame:
    if not orders:
        raise ValueError('No historical orders available for forecasting.')

    df = pd.DataFrame(orders)
    df['order_date'] = pd.to_datetime(df['order_date'])
    df['week_start'] = df['order_date'].dt.to_period('W').apply(lambda r: r.start_time.date())

    group_cols = ['week_start', 'warehouse_code', 'sku']
    agg = df.groupby(group_cols, as_index=False).agg(
        quantity=('quantity', 'sum'),
        weather_avg_temp_c=('weather_avg_temp_c', 'mean'),
        weather_precip_mm=('weather_precip_mm', 'mean'),
        weather_disruption_index=('weather_disruption_index', 'mean'),
    )

    agg['weather_avg_temp_c'] = agg['weather_avg_temp_c'].fillna(20.0)
    agg['weather_precip_mm'] = agg['weather_precip_mm'].fillna(3.0)
    agg['weather_disruption_index'] = agg['weather_disruption_index'].fillna(0.2)
    agg['week_of_year'] = pd.to_datetime(agg['week_start']).dt.isocalendar().week.astype(int)
    agg['month'] = pd.to_datetime(agg['week_start']).dt.month
    return agg


def _training_frame_hash(training_df: pd.DataFrame) -> str:
    data_dict = {
        'warehouse_codes': sorted(training_df['warehouse_code'].unique().tolist()),
        'skus': sorted(training_df['sku'].unique().tolist()),
        'row_count': len(training_df),
        'quantity_sum': float(training_df['quantity'].sum()),
    }
    return hashlib.sha256(json.dumps(data_dict, sort_keys=True).encode()).hexdigest()[:16]


_trained_model_cache: dict[str, Pipeline] = {}


def _get_or_train_model(training_df: pd.DataFrame) -> Pipeline:
    cache_key = _training_frame_hash(training_df)
    if cache_key in _trained_model_cache:
        return _trained_model_cache[cache_key]

    categorical = ['warehouse_code', 'sku']
    numeric = ['week_of_year', 'month', 'weather_avg_temp_c', 'weather_precip_mm', 'weather_disruption_index']

    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical),
            ('num', 'passthrough', numeric),
        ]
    )

    model = RandomForestRegressor(n_estimators=250, random_state=42, n_jobs=-1)
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', model),
    ])

    x = training_df[categorical + numeric]
    y = training_df['quantity']
    pipeline.fit(x, y)

    if len(_trained_model_cache) > 10:
        _trained_model_cache.pop(next(iter(_trained_model_cache)))
    _trained_model_cache[cache_key] = pipeline

    return pipeline


def forecast_weekly_demand(
    orders: list[dict],
    warehouse_weather_lookup: dict[str, dict[str, float]],
    horizon_weeks: int = 4,
) -> ForecastResult:
    training_df = build_training_frame(orders)
    model = _get_or_train_model(training_df)

    latest_week = max(training_df['week_start'])
    combos = training_df[['warehouse_code', 'sku']].drop_duplicates()

    predictions: list[dict] = []
    for step in range(1, horizon_weeks + 1):
        future_week = latest_week + timedelta(days=7 * step)
        week_of_year = future_week.isocalendar()[1]
        month = future_week.month

        rows = []
        for _, combo in combos.iterrows():
            w_code = combo['warehouse_code']
            sku = combo['sku']
            weather = warehouse_weather_lookup.get(w_code, {
                'weather_avg_temp_c': 20.0,
                'weather_precip_mm': 3.0,
                'weather_disruption_index': 0.2,
            })
            rows.append({
                'warehouse_code': w_code,
                'sku': sku,
                'week_of_year': week_of_year,
                'month': month,
                'weather_avg_temp_c': weather['weather_avg_temp_c'],
                'weather_precip_mm': weather['weather_precip_mm'],
                'weather_disruption_index': weather['weather_disruption_index'],
            })

        future_df = pd.DataFrame(rows)
        y_pred = model.predict(future_df)
        y_pred = np.maximum(y_pred, 0)

        for i, row in future_df.iterrows():
            predictions.append({
                'week_start': future_week,
                'warehouse_code': row['warehouse_code'],
                'sku': row['sku'],
                'predicted_demand': float(round(y_pred[i], 2)),
            })

    return ForecastResult(model_name='RandomForestRegressor', predictions=predictions)


def calculate_arrival_probability(
    route_id: UUID,
    current_lat: float,
    current_lon: float,
    historical_runs: list[dict],
    route_destination: dict[str, float] | None = None,
) -> dict:
    now = datetime.now(tz=timezone.utc)

    min_history = 10
    if len(historical_runs) < min_history:
        fallback_minutes = 60
        if historical_runs:
            avg_duration = sum(
                float(run.get('estimated_duration_min', 60)) for run in historical_runs
            ) / len(historical_runs)
            fallback_minutes = avg_duration
        return {
            'predicted_eta': (now + timedelta(minutes=fallback_minutes)).isoformat(),
            'confidence_score': 0.1,
        }

    records: list[dict] = []
    for run in historical_runs:
        sched_date = run.get('schedule_date', now.date())
        if isinstance(sched_date, str):
            sched_date = datetime.fromisoformat(sched_date).date()
        weather = simulated_weather_features(sched_date, current_lat, current_lon)
        records.append({
            'total_distance_km': float(run.get('total_distance_km', 0)),
            'speed_kmh': float(run.get('speed_kmh', 50)),
            'stops_count': int(run.get('stops_count', 1)),
            'day_of_week': sched_date.weekday(),
            'weather_disruption_index': weather['weather_disruption_index'],
            'duration_min': float(run.get('estimated_duration_min', 60)),
        })

    train_df = pd.DataFrame(records)
    feature_cols = ['total_distance_km', 'speed_kmh', 'stops_count', 'day_of_week', 'weather_disruption_index']

    model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
    model.fit(train_df[feature_cols], train_df['duration_min'])

    remaining_distance_km: float
    if route_destination:
        remaining_distance_km = haversine_km(
            current_lat, current_lon,
            route_destination['latitude'], route_destination['longitude'],
        )
    else:
        remaining_distance_km = float(train_df['total_distance_km'].mean()) * 0.5

    live_weather = simulated_weather_features(now.date(), current_lat, current_lon)
    avg_speed = float(train_df['speed_kmh'].mean()) or 50.0
    avg_stops = int(train_df['stops_count'].mean()) or 1

    pred_input = pd.DataFrame([{
        'total_distance_km': remaining_distance_km,
        'speed_kmh': avg_speed,
        'stops_count': avg_stops,
        'day_of_week': now.weekday(),
        'weather_disruption_index': live_weather['weather_disruption_index'],
    }])

    predicted_minutes = float(model.predict(pred_input)[0])
    predicted_minutes = max(predicted_minutes, 0.0)

    tree_preds = np.array([t.predict(pred_input) for t in model.estimators_]).flatten()
    std_dev = float(np.std(tree_preds))
    mean_pred = float(np.mean(tree_preds)) or 1.0
    cv = std_dev / mean_pred
    confidence = round(max(0.0, min(1.0, 1.0 - cv)), 2)

    predicted_eta = now + timedelta(minutes=predicted_minutes)

    return {
        'predicted_eta': predicted_eta.isoformat(),
        'confidence_score': confidence,
    }
