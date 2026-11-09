from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from threading import Lock


@dataclass
class AppMetrics:
    started_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    requests_total: int = 0
    requests_4xx: int = 0
    requests_5xx: int = 0
    unhandled_exceptions: int = 0
    websocket_connections: int = 0
    last_exception_at: datetime | None = None
    _lock: Lock = field(default_factory=Lock)

    def record_http(self, status_code: int) -> None:
        with self._lock:
            self.requests_total += 1
            if 400 <= status_code < 500:
                self.requests_4xx += 1
            elif status_code >= 500:
                self.requests_5xx += 1

    def record_ws_open(self) -> None:
        with self._lock:
            self.websocket_connections += 1

    def record_exception(self) -> None:
        with self._lock:
            self.unhandled_exceptions += 1
            self.last_exception_at = datetime.now(UTC)

    def snapshot(self) -> dict:
        with self._lock:
            uptime = int((datetime.now(UTC) - self.started_at).total_seconds())
            return {
                'started_at': self.started_at.isoformat(),
                'uptime_seconds': uptime,
                'requests_total': self.requests_total,
                'requests_4xx': self.requests_4xx,
                'requests_5xx': self.requests_5xx,
                'unhandled_exceptions': self.unhandled_exceptions,
                'last_exception_at': (
                    self.last_exception_at.isoformat()
                    if self.last_exception_at is not None
                    else None
                ),
                'websocket_connections': self.websocket_connections,
            }


app_metrics = AppMetrics()
