# Pilot Full-Surface Isolation Validation

**Date:** 2026-11-19

**Scope:** PILOT-02 repository and current pilot surface

**Branch:** `codex/pilot-isolation-closeout`

## Implemented evidence

- An exact executable inventory fails when a new business route appears without classification.
- Every current business route is proven to depend on authenticated identity; development routes remain out of the contract.
- The integration matrix covers cross-tenant rule/dataset/simulation creation, simulation/impact/export reads, approval, release gate, scenario list, and paginated audit list.
- Cross-tenant object reads use the same non-enumerating response as an absent object.
- Metrics contain aggregate bounded labels only and are checked for absence of known tenant identifiers, slugs, and tenant labels.
- The pilot gateway rejects metrics, framework docs/OpenAPI, and development routes. API, worker, database, web, and Prometheus remain on internal networks with only the HTTPS gateway published.
- Unimplemented reproduction, standalone artifact, webhook, public metric, and worker-control surfaces have no route.
- `security/pilot-surface-isolation-matrix.md` records every current surface and reopening rule.

## Local result

| Check | Result |
|---|---|
| Clean Linux non-integration suite | 91 passed, 4 deselected, 81.13% coverage |
| Expanded cross-tenant integration matrix | Passed against isolated PostgreSQL test database |
| Exact business-route authentication inventory | Passed for all 11 current business operations |
| Metric redaction | Passed for tenant labels, slugs, and both known tenant identifiers |
| Pilot gateway syntax | Caddy 2.10.2 adapted the configuration successfully and preserved the internal-only matcher |
| Static safety | Ruff format/lint, mypy, OpenAPI, secret scan, and diff hygiene passed |

## Exit assessment

PILOT-02 remains open until local integration/container validation and all five protected pull-request checks pass. The assessment applies to the exact current pilot surface only; any added route, artifact, label, port, operator API, or webhook reopens the gate.
