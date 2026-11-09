from __future__ import annotations

from datetime import UTC, datetime


def build_live_snapshot(
    inventory_rows: list[dict],
    route_rows: list[dict],
    forecast_rows: list[dict],
    dispatch_overview: dict | None = None,
) -> dict:
    return {
        'type': 'live_update',
        'server_time': datetime.now(UTC).isoformat(),
        'inventory_overview': inventory_rows,
        'route_summaries': route_rows,
        'forecast_preview': forecast_rows,
        'dispatch_overview': dispatch_overview or {'updated_at': None, 'runs': []},
    }
