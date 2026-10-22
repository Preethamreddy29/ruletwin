# Phase 3 Validation Evidence

**Date:** 2026-10-21
**Branch:** `codex/phase3-first-vertical-slice`  
**Base:** Phase 2 merge `ce437aae`

## Automated results

| Validation | Result |
|---|---|
| Ruff format/lint and strict mypy | Pass |
| OpenAPI reference validation | Pass — 10 paths, 10 operations, 118 references |
| Repository secret scan | Pass |
| PostgreSQL upgrade/down/base/forward and Alembic drift check | Pass — no new operations |
| Python tests | Pass — 40, including integration/recovery and malformed engine-output fail-closed coverage |
| Python measured coverage | Pass — 92.88% |
| Web component tests | Pass — 4 |
| Web coverage | Pass — 89.87% statements, 89.47% branches, 93.75% functions, 91.66% lines |
| ESLint, TypeScript and production build | Pass |
| Compose clean reset/build/start/health | Pass — fresh volumes, migration, 100-event seed and idempotent reseed |
| Playwright Chromium critical flow | Pass — allow and block paths |

## Requirement evidence

- Canonicalization order independence and checksum reproduction: unit/property tests.
- Rounding boundaries, idempotence and money precision: exhaustive bounded property loops plus named boundary cases.
- Duplicate create, crash after claim and redelivery after result commit: PostgreSQL integration test.
- Incomplete, stale, substituted and self-approval rejection: PostgreSQL integration test.
- Exact risk/gate outcomes: policy unit test and Playwright allow/block workflows.
- Transition audit: persisted integration workflow and live API flow.
- Clean-reset workflow: only the two labeled RuleTwin volumes were removed; PostgreSQL/API became healthy and the seed restored exactly 100 events and one baseline rule.
- Post-Playwright persistence: 2 completed simulations, 2 impact records, 2 approvals, one allow gate, one block gate, 14 audit events and zero unprocessed outbox events.

## Clean-runner evidence

The pull-request workflow rerun for hardening commit `b498c48` completed successfully on 2026-10-21. All five jobs passed: backend/migrations/integration, web quality/build, contracts/repository security, Compose/container evidence and the Playwright critical flow. The earlier Bandit finding is closed by explicit fail-closed validation and its malformed-output regression test.
