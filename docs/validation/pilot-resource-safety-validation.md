# Pilot Resource-Safety Validation

## Scope

This increment implements the PILOT-06 foundation without claiming the complete pilot gate. It adds configurable request-body and replay-dataset limits, atomic per-tenant simulation admission, bounded worker execution and retries, capped exponential retry delay, and explicit single-process worker concurrency.

## Implemented controls

- API requests larger than `RULETWIN_MAX_REQUEST_BODY_BYTES` fail with a non-successful `413` problem response.
- Replay datasets larger than `RULETWIN_MAX_DATASET_EVENTS` fail before event generation or database writes.
- Simulation admission uses a tenant-scoped PostgreSQL transaction advisory lock and rejects requests at `RULETWIN_MAX_PENDING_SIMULATIONS_PER_TENANT` with `429`.
- Idempotent retries are resolved before the queue-capacity check, so a safe replay does not consume another slot.
- Worker claims exclude events at the configured maximum attempt count.
- Each execution is bounded by `RULETWIN_WORKER_EXECUTION_TIMEOUT_SECONDS`.
- Recoverable failures use capped exponential delay; the final attempt marks the outbox event and simulation failed.
- Pilot worker concurrency is intentionally fixed at one per process. Horizontal multi-worker capacity is outside this increment.

## Executable evidence

- Configuration validation rejects unsafe ranges and retry-delay inversion.
- Middleware and endpoint tests cover request and dataset oversize responses.
- Integration coverage proves per-tenant queue saturation fails with `queue-capacity-exceeded`.
- Worker unit coverage verifies maximum-attempt claim binding and capped retry delay.
- OpenAPI describes `413` and `429` resource-limit responses.

## Local validation — 2026-10-28

- Ruff formatting and lint: passed.
- Mypy: passed for 27 source files.
- Python unit suite: 64 passed with 80.20% total coverage.
- OpenAPI validation: passed with 13 paths, 13 operations, and 136 resolved references.
- Repository secret scan: passed.
- `git diff --check`: passed.
- Compose configuration parse: passed.
- Database-backed integration and container saturation/recovery: not run locally because the Docker engine was unavailable; protected CI is required before merge.

## Remaining evidence

PILOT-06 is not closed by this document alone. A clean protected CI run, container-level timeout/retry recovery, sustained saturation behavior, and measured resource use on the named pilot reference profile remain required. General request-rate limiting is grouped with the next operations/edge-control increment rather than claimed here.
