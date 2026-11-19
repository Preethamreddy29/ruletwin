from pathlib import Path

from fastapi.routing import APIRoute

from ruletwin.api.vertical_slice import router

BUSINESS_SURFACES = {
    ("GET", "/v1/session"),
    ("GET", "/v1/scenarios"),
    ("POST", "/v1/tenants/{tenant_id}/rule-versions"),
    ("POST", "/v1/replay-datasets"),
    ("POST", "/v1/simulations"),
    ("GET", "/v1/simulations/{simulation_id}"),
    ("GET", "/v1/simulations/{simulation_id}/impact"),
    ("GET", "/v1/simulations/{simulation_id}/evidence-export"),
    ("POST", "/v1/simulations/{simulation_id}/approvals"),
    ("POST", "/v1/release-gates/evaluate"),
    ("GET", "/v1/audit-events"),
}


def _dependency_names(route: APIRoute) -> set[str]:
    names: set[str] = set()
    pending = list(route.dependant.dependencies)
    while pending:
        dependency = pending.pop()
        name = getattr(dependency.call, "__name__", None)
        if name:
            names.add(name)
        pending.extend(dependency.dependencies)
    return names


def test_every_business_surface_requires_authenticated_identity() -> None:
    actual: set[tuple[str, str]] = set()
    for route in router.routes:
        assert isinstance(route, APIRoute)
        if route.path.startswith("/v1/dev/"):
            assert route.include_in_schema is False
            continue
        for method in route.methods:
            actual.add((method, route.path))
        assert "authenticated_identity" in _dependency_names(route), route.path

    assert actual == BUSINESS_SURFACES


def test_pilot_gateway_keeps_operator_and_development_surfaces_internal() -> None:
    root = Path(__file__).resolve().parents[4]
    caddy = (root / "deploy/pilot/Caddyfile").read_text(encoding="utf-8")
    compose = (root / "deploy/pilot/compose.yaml").read_text(encoding="utf-8")

    assert "@internalOnly path /api/metrics /api/openapi.json /api/docs* /api/v1/dev/*" in caddy
    assert "respond @internalOnly 404" in caddy
    assert 'ports: ["${RULETWIN_HTTPS_PORT:-8443}:8443"]' in compose
    assert "backend:\n    internal: true" in compose
    assert "frontend:\n    internal: true" in compose
