# Requirements Traceability

The authoritative requirements remain in [`product/requirements.md`](product/requirements.md) and [`architecture/nfrs.md`](architecture/nfrs.md). “Slice” means the Phase 3 one-tenant rounding scope is implemented; broader v1 coverage remains later-phase work.

| Requirement | Implementation evidence | Verification | Status |
|---|---|---|---|
| Immutable tenant-scoped rule versions | `domain/canonical.py`, `domain/rounding.py`, migration `0002`, rule API | Canonical order/checksum unit test; migration constraints | Phase 3 slice complete |
| Deterministic replay tuple | `domain/datasets.py`, `domain/simulation.py`, seeded scenario pack | Repeated dataset/result checksum test; integration replay | Phase 3 slice complete |
| Baseline/candidate comparison | Worker application service, relational outcomes/impact | Rounding boundary/property tests; Playwright impact view | Financial Phase 3 dimension complete |
| Versioned fail-closed risk policy | Seeded immutable policy and pure evaluator | Allow/block/error unit test; Playwright both outcomes | Phase 3 slice complete |
| Separation of duties | Approval service validates author, checksum, policy and ETag | Incomplete, stale/substituted and self-approval integration cases | Phase 3 slice complete; full RBAC Phase 4 |
| Durable asynchronous simulation | Transactional simulation/outbox plus lease worker | Duplicate request, crash-after-claim and post-result redelivery | Phase 3 slice complete |
| Stable versioned API behavior | `packages/contracts/openapi.json`, problem responses and ETags | OpenAPI reference validation; live UI/API path | Phase 3 operations implemented |
| Protected mutation audit | Append-only `audit_events`; application role cannot update/delete | Migration grant/revoke and integration/live workflow | Phase 3 transitions complete |
| Signature workflow UI-to-data | `App.tsx`, API/application/domain/worker/database path | Chromium allow/block critical flows | Phase 3 complete |
| High threats and full tenant isolation | Phase 1 threat/control plans | Full negative authorization matrix | Deferred to Phase 4/5 |

## Current gate

Phase 3 passes all locally executable evidence. See [`phase3-exit-audit.md`](phase3-exit-audit.md) and [`validation/phase3-validation.md`](validation/phase3-validation.md). Clean-runner GitHub Actions remains pending the user's manual commit and push.
