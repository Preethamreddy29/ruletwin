# RuleTwin Implementation Plan

## Source precedence

1. Portfolio `docs/00_PORTFOLIO_ENGINEERING_HANDBOOK.md`
2. Portfolio `docs/01_RULETWIN_IMPLEMENTATION_RUNBOOK.md`
3. Portfolio `docs/04_RELEASE_EVIDENCE_MATRIX.md`
4. Portfolio `docs/Technical_Product_Portfolio_Project_Blueprint.md`
5. Approved Phase 0 evidence in the portfolio repository

The sibling portfolio repository is development provenance, not a RuleTwin runtime dependency.

## Phase status

| Phase | Status | Gate |
|---|---|---|
| 0 — Charter | Closed in the portfolio repository | Worth building as a documented hypothesis |
| 1 — Requirements and architecture | Complete; merged in PR #1 | Safe and feasible design |
| 2 — Engineering foundation | Complete; merged at `ce437aae` with clean-runner evidence | Repeatable engineering base |
| 3 — First vertical slice | Complete; merged in PR #13 | Core deterministic workflow is executable |
| 4A — Multi-tenant authorization | Complete; merged in PR #18 at `cffdb30`; protected CI passed | Tenant boundary is executable for implemented surfaces |
| Controlled-pilot readiness | In progress; evidence export merged, provider-neutral OIDC foundation awaits PR #22 merge, and dependent Auth0/PKCE browser integration is under validation | Invitation-only synthetic-data pilot gate |

## Delivered foundation

- Versioned domain, API, data, risk-policy, security, and decision records.
- Python/FastAPI API, React/TypeScript web application, PostgreSQL migrations, and a recoverable worker/outbox path.
- Deterministic rounding-rule simulation, impact comparison, fail-closed risk decision, checksum-bound approval, release gate, and append-only audit evidence.
- Two fictional tenants, database-resolved role memberships, object-level authorization, non-enumerating cross-tenant denial, and role-separated UI flows.
- Local and clean-runner validation across formatting, linting, typing, tests, coverage, OpenAPI, migrations, secret/dependency/container checks, Compose, and Playwright critical flows.

## Next implementation milestone

The controlling scope is [`pilot-readiness-plan.md`](pilot-readiness-plan.md). Delivery is ordered as:

1. Completed-simulation evidence export and authorization — merged through PR #21.
2. Merge the OIDC verification foundation and its dependent Auth0/PKCE browser integration; complete real-provider login/logout and invited-subject evidence.
3. Request, dataset, execution, queue, retry, and concurrency limits.
4. Structured operational telemetry and actionable alerts.
5. Reproducible HTTPS deployment, external secret management, automated migrations, backups, restore, and rollback.
6. Supply-chain artifacts, reference-profile performance evidence, accessibility, and operator acceptance.
7. Immutable `v0.4.0-pilot.1` release only after every pilot gate passes.

## Non-negotiable constraints

- Synthetic data only until separately approved.
- No billing execution or writes to external production systems.
- No claim of production readiness from development identity or partial-surface isolation evidence.
- Security, tenant isolation, determinism, immutability, and fail-closed behavior take precedence over feature breadth and latency.
- DecisionTrace and BoundaryOps remain separate repositories and are not pilot dependencies.

## Current decision boundary

RuleTwin can be demonstrated locally today. External hosting remains blocked on the owner decisions and executable evidence listed in [`pilot-readiness-plan.md`](pilot-readiness-plan.md).
