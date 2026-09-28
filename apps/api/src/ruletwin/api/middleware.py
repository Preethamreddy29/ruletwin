import re
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware

REQUESTS = Counter(
    "ruletwin_http_requests_total",
    "HTTP requests processed",
    ("method", "route", "status"),
)
DURATION = Histogram(
    "ruletwin_http_request_duration_seconds",
    "HTTP request duration",
    ("method", "route"),
)
_UUID_PATTERN = re.compile(r"^[0-9a-fA-F-]{36}$")


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        supplied = request.headers.get("X-Correlation-ID", "")
        request_id = supplied if _UUID_PATTERN.fullmatch(supplied) else str(uuid.uuid4())
        trace_id = request.headers.get("traceparent", request_id)
        request.state.request_id = request_id
        request.state.trace_id = trace_id
        started = time.perf_counter()
        response = await call_next(request)
        route = getattr(request.scope.get("route"), "path", request.url.path)
        REQUESTS.labels(request.method, route, str(response.status_code)).inc()
        DURATION.labels(request.method, route).observe(time.perf_counter() - started)
        response.headers["X-Correlation-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        return response
