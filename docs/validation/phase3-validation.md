# Phase 3 Validation Evidence

**Date:** 2026-09-29  
**Branch:** `codex/phase3-first-vertical-slice`  
**Base:** Phase 2 merge `ce437aae`

## Automated results

| Validation | Result |
|---|---|
| Ruff format/lint and strict mypy | Pass |
| OpenAPI reference validation | Pass — 10 paths, 10 operations, 118 references |
| Repository secret scan | Pass |
| PostgreSQL upgrade/down/base/forward and Alembic drift check | Pass — no new operations |
| Python tests | Pass — 39, including integration/recovery |
| Python measured coverage | Pass — 92.76% |
| Web component tests | Pass — 4 |
| Web coverage | Pass — 89.87% statements, 89.47% branches, 93.75% functions, 91.66% lines |
| ESLint, TypeScript and production build | Pass |
| Compose core build/start/health | Pass |
| Playwright Chromium critical flow | Pass — allow and block paths |

## Requirement evidence

- Canonicalization order independence and checksum reproduction: unit/property tests.
- Rounding boundaries, idempotence and money precision: exhaustive bounded property loops plus named boundary cases.
- Duplicate create, crash after claim and redelivery after result commit: PostgreSQL integration test.
- Incomplete, stale, substituted and self-approval rejection: PostgreSQL integration test.
- Exact risk/gate outcomes: policy unit test and Playwright allow/block workflows.
- Transition audit: persisted integration workflow and live API flow.

## External evidence still pending

GitHub Actions has not run because the user reserved all commit/push/PR operations. The CI workflow now includes the Playwright critical-flow job and must pass after the user's manual push.
