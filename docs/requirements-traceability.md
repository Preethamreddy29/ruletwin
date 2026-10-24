# Requirements Traceability

The authoritative requirements remain in [`product/requirements.md`](product/requirements.md) and [`architecture/nfrs.md`](architecture/nfrs.md). “Slice” means the Phase 3 one-tenant rounding scope is implemented; broader v1 coverage remains later-phase work.

| Requirement | Implementation evidence | Verification | Status |
|---|---|---|---|
| Immutable tenant-scoped rule versions | `domain/canonical.py`, `domain/rounding.py`, migration `0002`, rule API | Canonical order/checksum unit test; migration constraints | Phase 3 slice complete |
| Deterministic replay tuple | `domain/datasets.py`, `domain/simulation.py`, seeded scenario pack | Repeated dataset/result checksum test; integration replay | Phase 3 slice complete |
| Baseline/candidate comparison | Worker application service, relational outcomes/impact | Rounding boundary/property tests; Playwright impact view | Financial Phase 3 dimension complete |
| Versioned fail-closed risk policy | Seeded immutable policy and pure evaluator | Allow/block/error unit test; Playwright both outcomes | Phase 3 slice complete |
| Separation of duties | JWT identity dependency, PostgreSQL memberships, approval/gate services | Wrong-role, self-approval, stale/substituted evidence and Playwright persona transitions | Phase 4A implemented actions complete |
| Durable asynchronous simulation | Transactional simulation/outbox plus lease worker | Duplicate request, crash-after-claim and post-result redelivery | Phase 3 slice complete |
| Stable versioned API behavior | `packages/contracts/openapi.json`, problem responses and ETags | OpenAPI reference validation; live UI/API path | Phase 3 operations implemented |
| Protected mutation audit | Append-only `audit_events`; application role cannot update/delete | Migration grant/revoke and integration/live workflow | Phase 3 transitions complete |
| Signature workflow UI-to-data | `App.tsx`, API/application/domain/worker/database path | Chromium allow/block critical flows | Phase 3 complete |
| Implemented-path tenant isolation | Auth dependency plus tenant-scoped application queries | Same-tenant allow; cross-tenant and absent-object equivalent 404; isolated audit lists | Phase 4A slice complete |
| High threats and full-surface isolation | Phase 1 threat/control plans | Export/artifact/webhook/metrics/operator negative matrix | Remaining Phase 4/5 scope |


## Current gate

Phase 3 and Phase 4A pass their local and protected clean-runner gates. Phase 4A merged through PR #18 at `cffdb30`, and main CI passed again at `d64275f`. Controlled-pilot hardening is planned and not yet satisfied; see [`phase4a-exit-audit.md`](phase4a-exit-audit.md), [`validation/phase4a-validation.md`](validation/phase4a-validation.md), and [`pilot-readiness-plan.md`](pilot-readiness-plan.md).
