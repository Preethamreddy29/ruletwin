import re
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request, Response
from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ruletwin.api.problems import problem_response

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
    def __init__(self, app: ASGIApp, *, max_request_body_bytes: int) -> None:
        super().__init__(app)
        self._max_request_body_bytes = max_request_body_bytes

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
        response: Response
        content_length = request.headers.get("content-length")
        if content_length is not None:
            try:
                declared_size = int(content_length)
            except ValueError:
                declared_size = self._max_request_body_bytes + 1
            if declared_size > self._max_request_body_bytes:
                response = problem_response(
                    request,
                    status=413,
                    title="Request too large",
                    detail="The request body exceeds the configured pilot limit.",
                    code="request-too-large",
                )
                response.headers["X-Correlation-ID"] = request_id
                response.headers["X-Trace-ID"] = trace_id
                return response
        if content_length is None and request.method in {"POST", "PUT", "PATCH"}:
            response = problem_response(
                request,
                status=411,
                title="Length required",
                detail="A Content-Length header is required for requests with a body.",
                code="length-required",
            )
            response.headers["X-Correlation-ID"] = request_id
            response.headers["X-Trace-ID"] = trace_id
            return response
        response = await call_next(request)
        route = getattr(request.scope.get("route"), "path", request.url.path)
        REQUESTS.labels(request.method, route, str(response.status_code)).inc()
        DURATION.labels(request.method, route).observe(time.perf_counter() - started)
        response.headers["X-Correlation-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        return response
