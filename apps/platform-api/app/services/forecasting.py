from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


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
