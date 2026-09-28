# Phase 2 Operations Runbook

## Service boundaries

| Service | Responsibility | Readiness signal |
|---|---|---|
| PostgreSQL | Transactional state and outbox | `pg_isready` |
| Migration job | Forward schema application | Successful exit |
| API | Health, contract and future application boundary | `/health/ready` |
| Worker | Outbox lease and heartbeat skeleton | Structured heartbeat logs |
| Web | Static readiness and synthetic-session shell | HTTP 8080 |
| Prometheus | Optional local metrics inspection | HTTP 9090 |

## Expected startup order

PostgreSQL becomes healthy, migrations reach head, the API and worker start, the API becomes ready, and then the web container starts. A missing required setting causes configuration validation to stop the affected process.

## Basic diagnosis

1. Run `./scripts/dev.ps1 status`.
2. Check `./scripts/dev.ps1 logs` for structured API/worker events.
3. Compare liveness with readiness. Live plus not-ready indicates a dependency problem rather than a dead process.
4. Inspect PostgreSQL health and the migration job exit code.
5. Do not bypass a failed migration or readiness check by editing the database manually.

## Recovery boundaries

- Development data is synthetic and disposable, but normal shutdown preserves it.
- Schema recovery uses a reviewed forward migration by default.
- The downgrade path exists to verify reversibility in disposable test databases; it is not an automatic production rollback policy.
- Outbox rows remain pending when no handler exists. Phase 2 proves safe leasing only; Phase 3 owns product event handling.

## Known limitations

- Local synthetic identity is not production authentication.
- Product tenant authorization, rule execution, simulation and approvals are not implemented.
- No performance or production-readiness claim is supported by this phase.
- Local container, PostgreSQL integration and Prometheus evidence passed on 2026-09-27; clean-runner CI and scan evidence remains pending until the branch is pushed.
