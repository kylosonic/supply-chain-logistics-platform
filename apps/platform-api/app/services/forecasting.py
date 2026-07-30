from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, datetime, timedelta, timezone
from uuid import UUID

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from app.services.weather import simulated_weather_features


@dataclass
class ForecastResult:
    model_name: str
    predictions: list[dict]


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


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


def train_weekly_demand_model(training_df: pd.DataFrame) -> Pipeline:
    categorical = ['warehouse_code', 'sku']
    numeric = ['week_of_year', 'month', 'weather_avg_temp_c', 'weather_precip_mm', 'weather_disruption_index']

    preprocessor = ColumnTransformer(
        transformers=[
            ('cat', OneHotEncoder(handle_unknown='ignore'), categorical),
            ('num', 'passthrough', numeric),
        ]
    )

    model = RandomForestRegressor(n_estimators=250, random_state=42)
    pipeline = Pipeline([
        ('preprocessor', preprocessor),
        ('model', model),
    ])

    x = training_df[categorical + numeric]
    y = training_df['quantity']
    pipeline.fit(x, y)
    return pipeline


def forecast_weekly_demand(
    orders: list[dict],
    warehouse_weather_lookup: dict[str, dict[str, float]],
    horizon_weeks: int = 4,
) -> ForecastResult:
    training_df = build_training_frame(orders)
    model = train_weekly_demand_model(training_df)

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

        for idx, row in future_df.iterrows():
            predictions.append({
                'week_start': future_week,
                'warehouse_code': row['warehouse_code'],
                'sku': row['sku'],
                'predicted_demand': float(round(y_pred[idx], 2)),
            })

    return ForecastResult(model_name='RandomForestRegressor', predictions=predictions)


# ---------------------------------------------------------------------------
# Predictive ETA Algorithm
# ---------------------------------------------------------------------------

def _haversine_miles(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points in miles."""
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def calculate_arrival_probability(
    route_id: UUID,
    current_lat: float,
    current_lon: float,
    historical_runs: list[dict],
    route_destination: dict[str, float] | None = None,
) -> dict:
    """Predict the remaining transit time using a RandomForestRegressor.

    Args:
        route_id: UUID of the route being tracked.
        current_lat: Current latitude of the vehicle.
        current_lon: Current longitude of the vehicle.
        historical_runs: List of dicts from RouteOptimizationRun rows,
            each containing at least ``total_distance_km``,
            ``estimated_duration_min``, ``speed_kmh``, ``stops_count``,
            and ``schedule_date``.
        route_destination: Optional dict with ``latitude`` and
            ``longitude`` of the route destination.  When provided the
            remaining distance is estimated via Haversine.

    Returns:
        A dict with ``predicted_eta`` (ISO datetime) and
        ``confidence_score`` (float 0-1).
    """
    now = datetime.now(tz=timezone.utc)

    # ---- Fallback when there is no history ----------------------------------
    if not historical_runs:
        return {
            'predicted_eta': (now + timedelta(minutes=60)).isoformat(),
            'confidence_score': 0.1,
        }

    # ---- Build training data from historical optimisation runs ---------------
    records: list[dict] = []
    for run in historical_runs:
        sched_date = run.get('schedule_date', now.date())
        if isinstance(sched_date, str):
            sched_date = datetime.fromisoformat(sched_date).date()
        weather = simulated_weather_features(
            sched_date,
            current_lat,
            current_lon,
        )
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

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(train_df[feature_cols], train_df['duration_min'])

    # ---- Build prediction row for current conditions -------------------------
    remaining_distance_km: float
    if route_destination:
        remaining_distance_km = _haversine_miles(
            current_lat, current_lon,
            route_destination['latitude'], route_destination['longitude'],
        ) * 1.60934  # miles → km
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

    # ---- Confidence from tree-level variance ---------------------------------
    tree_preds = np.array([t.predict(pred_input) for t in model.estimators_]).flatten()
    std_dev = float(np.std(tree_preds))
    mean_pred = float(np.mean(tree_preds)) or 1.0
    cv = std_dev / mean_pred  # coefficient of variation
    confidence = round(max(0.0, min(1.0, 1.0 - cv)), 2)

    predicted_eta = now + timedelta(minutes=predicted_minutes)

    return {
        'predicted_eta': predicted_eta.isoformat(),
        'confidence_score': confidence,
    }

