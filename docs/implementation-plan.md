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
| 1 — Requirements and architecture | **Complete locally; pending Git review/merge** | Safe and feasible design |
| 2 — Engineering foundation | Next; not started | Repeatable engineering base |

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
