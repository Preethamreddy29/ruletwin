# RuleTwin Implementation Plan

## Source precedence

1. Portfolio `docs/00_PORTFOLIO_ENGINEERING_HANDBOOK.md`
2. Portfolio `docs/01_RULETWIN_IMPLEMENTATION_RUNBOOK.md`
3. Portfolio `docs/04_RELEASE_EVIDENCE_MATRIX.md`
4. Portfolio `docs/Technical_Product_Portfolio_Project_Blueprint.md`
5. Approved Phase 0 evidence in the portfolio repository

The sibling portfolio checkout used for this phase is `D:\sunny\Profile\projects\enterprise-rule-intelligence`. References to it are development provenance, not runtime dependencies.

## Phase status

| Phase | Status | Gate |
|---|---|---|
| 0 — Charter | Closed in portfolio repository | Worth building as a documented hypothesis |
| 1 — Requirements and architecture | Complete and merged in PR #1 | Safe and feasible design |
| 2 — Engineering foundation | Merged at `ce437aae` | Repeatable engineering base |
| 3 — First vertical slice | Implementation and local validation complete; clean CI evidence pending | Core workflow is real |

## Phase 1 deliverables

- Domain vocabulary, invariants, lifecycle and money/effective-date semantics.
- Reviewed ERD and retention/immutability model.
- Versioned OpenAPI with stable errors, idempotency and concurrency behavior.
- Eight accepted ADRs with alternatives and revisit triggers.
- Complete STRIDE threat-to-planned-test mapping for high risks.
- Deterministic fail-closed risk-policy model.
- Tenant/RBAC and separation-of-duties model.
- Requirements-to-contract/control/test traceability.

## Exit gate

Phase 1 closes only when:

1. OpenAPI validates.
2. The schema diagram and invariants are reviewed.
3. All eight required ADRs exist and have explicit status.
4. Every high threat has a planned control and negative test.
5. The signature workflow is traceable from user action through API, domain, storage, worker, policy, approval, gate, and audit.

No runtime code, dependency installation, CI claims, measurements, or production-readiness claims belong to Phase 1. The evidence and decision are recorded in [`phase1-exit-audit.md`](phase1-exit-audit.md).

## Phase 2 deliverables

- Repository contribution, security, ownership and pull-request governance.
- Python 3.12/FastAPI service foundation with validated fail-closed configuration.
- React/TypeScript/Vite readiness shell for a synthetic development identity.
- PostgreSQL 16 migration baseline, application/test roles and deterministic seed.
- Transaction boundary and PostgreSQL outbox lease-worker skeleton.
- Liveness, readiness, version, problem-details, correlation/trace and metrics contracts.
- Non-root read-only API, worker and web containers plus Compose profiles.
- Ruff, mypy, pytest, ESLint, Prettier, Vitest and coverage gates.
- GitHub CI for unit, integration, migration, contract, dependency, secret and container checks.
- Development and Phase 2 operations runbooks.

## Phase 2 exit gate

Phase 2 closes only when one command starts all core services, one command runs the checks, CI succeeds from a clean runner, migrations are verified against PostgreSQL, and health/telemetry are visible. All locally executable evidence now passes; formal closure is waiting only for the clean GitHub Actions run after commit and push. Current classification is recorded in [`phase2-exit-audit.md`](phase2-exit-audit.md).

## Phase 3 deliverables and gate

- Immutable canonical rounding-rule versions and versioned 100-event scenario pack.
- Integer-minor-unit deterministic interpreter, comparator, impact checksum and threshold policy.
- Transactional idempotent simulation/outbox acceptance and lease-recoverable worker execution.
- Checksum/policy/version-bound approval with incomplete, stale and self-approval rejection.
- Append-only transition audit and immutable allow/block release gate.
- Guided React workflow and Chromium validation of both risk outcomes.

Phase 3 passes locally when the migration drift gate, full checks, crash recovery integration suite,
live Compose workflow, and Playwright allow/block paths pass. Clean-runner CI after the user's manual
commit/push remains external evidence; see [`phase3-exit-audit.md`](phase3-exit-audit.md).
