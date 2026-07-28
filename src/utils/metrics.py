from __future__ import annotations
import time
from collections import deque
from dataclasses import dataclass
from prometheus_client import Counter, Histogram, Gauge, generate_latest
from fastapi.responses import Response


REQ_COUNT = Counter("cognita_http_requests_total", "requests", ["method", "path", "status"])
REQ_LAT = Histogram("cognita_http_request_latency_seconds", "latency", ["method", "path"])
ACTIVE = Gauge("cognita_active_sessions", "active sessions")


@dataclass
class _Rec:
    ts: float
    latency_ms: float
    is_error: bool


class MetricsCollector:
    def __init__(self, window_seconds: int = 3600):
        self.window = window_seconds
        self._reqs: deque[_Rec] = deque()
        self.active_sessions = 0

    def _prune(self) -> None:
        cutoff = time.time() - self.window
        while self._reqs and self._reqs[0].ts < cutoff:
            self._reqs.popleft()

    def record_request(self, method: str, path: str, status: int, latency_ms: float) -> None:
        REQ_COUNT.labels(method, path, status).inc()
        REQ_LAT.labels(method, path).observe(latency_ms / 1000.0)
        self._reqs.append(_Rec(time.time(), latency_ms, status >= 500))

    def record_message(self, status: str, source: str) -> None:  # noqa: ARG002
        pass

    def update_active_sessions(self, n: int) -> None:
        self.active_sessions = n
        ACTIVE.set(n)

    def snapshot(self, window_minutes: int = 60) -> dict:
        self.window = window_minutes * 60
        self._prune()
        n = len(self._reqs)
        errs = sum(1 for r in self._reqs if r.is_error)
        avg = (sum(r.latency_ms for r in self._reqs) / n) if n else 0.0
        return {"active_sessions": self.active_sessions, "avg_latency_ms": round(avg, 2),
                "error_rate": round(errs / n, 4) if n else 0.0, "requests_in_window": n}


def metrics_response() -> Response:
    return Response(generate_latest(), media_type="text/plain")
