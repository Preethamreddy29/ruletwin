from dataclasses import dataclass

from fastapi import Request
from fastapi.responses import JSONResponse


@dataclass(slots=True)
class ProblemError(Exception):
    status: int
    title: str
    detail: str
    code: str


def problem_response(
    request: Request,
    *,
    status: int,
    title: str,
    detail: str,
    code: str,
) -> JSONResponse:
    body = {
        "type": f"https://ruletwin.local/problems/{code}",
        "title": title,
        "status": status,
        "detail": detail,
        "instance": request.url.path,
        "code": code,
        "correlation_id": getattr(request.state, "request_id", None),
    }
    return JSONResponse(body, status_code=status, media_type="application/problem+json")
