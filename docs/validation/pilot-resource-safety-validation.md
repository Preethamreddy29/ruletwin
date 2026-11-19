# Pilot Resource-Safety Validation

## Scope

The merged foundation plus the `codex/pilot-resource-safety-evidence` increment implement the repository-controlled PILOT-06 gate: configurable request-body and replay-dataset limits, atomic per-tenant simulation admission, bounded worker execution and retries, capped exponential retry delay, explicit single-process worker concurrency, and retained saturation/recovery evidence.

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
- `scripts/resource_safety.py` stops the worker, fills the configured queue, proves fail-closed rejection and idempotent replay, drains the queue, forces a worker execution timeout with a database row lock, and proves retry recovery.
- The evidence record includes the commit, named machine profile, timings, deterministic result checksums, attempt/final-state data, and measured API/worker container statistics.

## Local validation — 2026-10-28

- Ruff formatting and lint: passed.
- Mypy: passed for 27 source files.
- Python unit suite after the CI configuration correction: 65 passed with 80.20% total coverage.
- OpenAPI validation: passed with 13 paths, 13 operations, and 136 resolved references.
- Repository secret scan: passed.
- `git diff --check`: passed.
- Compose configuration parse: passed.
- Database-backed integration and container checks were not run in the initial local validation because the Docker engine was unavailable.

## Merge and clean-runner evidence

- PR #25 merged to `main` as `d7365e6`.
- All five required protected checks passed: backend/migrations/integration, contracts/repository security, web quality/build, Playwright critical flow, and Compose/container evidence.
- The merge establishes the resource-safety implementation foundation.

## Local saturation and recovery evidence — 2026-11-19

- Profile: `sunny-windows-docker-resource-v1`, Windows 11, 12 logical CPUs.
- Queue limit: 5; accepted: 5; next request rejected with `queue-capacity-exceeded`.
- Idempotent retry returned the original simulation identifier while saturated.
- All 5 admitted simulations completed in 6.614 seconds with one deterministic result checksum.
- A forced one-second worker timeout was stored as `TimeoutError`; the same outbox item completed on attempt 2 after the lock was released.
- API snapshot: 0.18% CPU and 71.82 MiB memory. Worker snapshot: 4.23% CPU and 60.95 MiB memory. These are observed evidence, not capacity guarantees.

## Exit assessment

PR #36 passed all five protected checks in run `44546320237` and was squash-merged as `db4e3dd`. Main-only run `44547402942` passed on the merged commit and retained artifact `14540613851`, named `ruletwin-resource-safety-db4e3dd210e6402579782b67bfa567c1531f8c97`, until 2027-02-17. PILOT-06 is closed. General edge request-rate limiting remains an operational defense in depth and is not represented as a replacement for the queue and execution limits proven here.
