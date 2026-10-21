# Progress and Status

**As of:** 2026-10-21

**Branch:** `codex/phase3-first-vertical-slice` (hardening commit `b498c48` pushed)

**Milestone:** RuleTwin Phase 3 — first vertical slice

**Overall:** Phase 3 implementation and exit evidence pass. The production assertion identified by the first clean-runner attempt was replaced by explicit fail-closed validation; the rerun succeeded across all five pull-request jobs.

## Implemented

- One tenant, separate synthetic author/approver, one declarative rounding family and integer-minor-unit execution.
- Canonical JSON/checksums, immutable rule/dataset/policy/evidence records and deterministic 100-event scenario pack.
- Baseline-versus-candidate replay, relational outcomes/impact, versioned financial-threshold risk evaluation and immutable release gate.
- Transactional simulation plus outbox creation, lease reclaim, idempotent completion and recovery after claim or result commit.
- Incomplete, stale, substituted and self-authored approval controls bound to result checksum, policy ID and simulation ETag.
- Append-only audit records for rule, dataset, simulation, approval and gate mutations/state transitions.
- Guided responsive UI for propose, dataset selection, polling, impact review and decision.
- Playwright Chromium coverage for both allow and block critical paths.
- Predictable `dev.ps1 reset` workflow recreates local volumes, migrations and deterministic seed without manual database edits; repository attributes preserve executable LF line endings on Windows.

## Verified locally

- `./scripts/check.ps1 -Integration`: formatting, lint, mypy, OpenAPI, secret scan, reversible migrations, zero schema drift, 40 Python tests, 4 web tests, type check and production build all passed.
- Python measured scope: 92.88%; web: 89.87% statements, 89.47% branches, 93.75% functions and 91.66% lines.
- Worker recovery suite passes for crash after claim and redelivery after committed result; duplicate simulation remains one logical job/result.
- `./scripts/dev.ps1 up` rebuilt and started the core stack; PostgreSQL/API were healthy and API/worker/web were running.
- `./scripts/dev.ps1 reset` was exercised from deleted RuleTwin volumes; it rebuilt the stack, applied migrations, seeded exactly 100 events and one baseline rule, and an immediate reseed preserved both counts.
- `pnpm e2e`: 2 Chromium tests exercised the safe `5`-minor-unit rule and blocked `10`-minor-unit rule through release-gate decision.

## Evidence limits and next work

- GitHub Actions clean-runner evidence passes at hardening commit `b498c48` across backend/integration, web/build, contracts/security, Compose and Playwright jobs.
- Phase 3 uses explicit fixed development actor IDs; authenticated multi-tenant RBAC is Phase 4.
- Phase 3 stores bounded 100-event outcomes relationally; artifact offload/retention expansion is later scope.
- Full five-family rules, dependency graph, multiple tenants, richer impact dimensions and auditor reproduction UI remain Phase 4.
