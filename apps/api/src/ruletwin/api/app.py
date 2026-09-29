import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.exceptions import HTTPException as StarletteHTTPException

from ruletwin.api.middleware import RequestContextMiddleware
from ruletwin.api.problems import ProblemError, problem_response
from ruletwin.api.vertical_slice import router as vertical_slice_router
from ruletwin.config import Settings
from ruletwin.db.database import Database
from ruletwin.logging import configure_logging

ReadinessProbe = Callable[[], Awaitable[bool]]


def create_app(settings: Settings, readiness_probe: ReadinessProbe | None = None) -> FastAPI:
    configure_logging(settings.log_level)
    database = Database(settings.database_url)
    probe = readiness_probe or database.ping

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        yield
        await database.dispose()

    app = FastAPI(
        title="RuleTwin",
        version=settings.version,
        docs_url="/docs" if settings.environment in {"dev", "test"} else None,
        redoc_url=None,
        lifespan=lifespan,
    )
    app.state.settings = settings
    app.state.database = database
    app.add_middleware(RequestContextMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.parsed_cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=[
            "Content-Type",
            "Idempotency-Key",
            "If-Match",
            "X-Actor-ID",
            "X-Correlation-ID",
        ],
    )

    @app.exception_handler(ProblemError)
    async def handle_problem(request: Request, exc: ProblemError) -> JSONResponse:
        return problem_response(
            request,
            status=exc.status,
            title=exc.title,
            detail=exc.detail,
            code=exc.code,
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation(request: Request, _: RequestValidationError) -> JSONResponse:
        return problem_response(
            request,
            status=422,
            title="Validation failed",
            detail="The request did not satisfy the endpoint contract.",
            code="validation-failed",
        )

    @app.exception_handler(StarletteHTTPException)
    async def handle_http(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        title = "Not found" if exc.status_code == 404 else "Request failed"
        code = "not-found" if exc.status_code == 404 else "http-error"
        return problem_response(
            request,
            status=exc.status_code,
            title=title,
            detail=str(exc.detail),
            code=code,
        )

    @app.get("/health/live", tags=["operations"])
    async def liveness() -> dict[str, str]:
        return {"status": "alive", "service": settings.service_name}

    @app.get("/health/ready", tags=["operations"])
    async def readiness() -> dict[str, str]:
        try:
            async with asyncio.timeout(settings.readiness_timeout_seconds):
                available = await probe()
        except TimeoutError:
            available = False
        if not available:
            raise ProblemError(503, "Not ready", "Database readiness check failed.", "not-ready")
        return {"status": "ready", "database": "reachable"}

    @app.get("/version", tags=["operations"])
    async def version() -> dict[str, str]:
        return {"service": settings.service_name, "version": settings.version}

    @app.get("/metrics", include_in_schema=False)
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.get("/v1/dev/session", tags=["development"], include_in_schema=False)
    async def development_session() -> dict[str, object]:
        if settings.environment not in {"dev", "test"}:
            raise ProblemError(404, "Not found", "Resource not found.", "not-found")
        return {
            "user": {
                "id": settings.synthetic_user_id,
                "email": settings.synthetic_user_email,
                "display_name": "NovaBill Analyst",
            },
            "tenant": {"slug": "novabill-sandbox", "display_name": "NovaBill Sandbox"},
            "roles": ["author", "reviewer"],
            "synthetic": True,
        }

    app.include_router(vertical_slice_router)

    return app
