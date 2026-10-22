# Signature Workflow Trace

The Phase 3 rounding slice implements steps 1–9 for one fixed development tenant and separate synthetic author/approver. Step 10's general auditor reproduction/export experience remains Phase 4; Phase 3 reproducibility is verified by immutable IDs and checksum tests.

| Step | Action | Contract/module | Planned evidence | Planned controls/tests |
|---:|---|---|---|---|
| 1 | Analyst creates candidate | Rule-version POST; rule domain | Immutable canonical version/checksum, author, audit | Tenant auth; schema, budget, dependency and date-overlap tests |
| 2 | Analyst creates fixed dataset | Dataset POST; dataset domain | Seed, generator/schema versions, checksum, audit | Deterministic regeneration and provenance tests |
| 3 | Analyst requests comparison | Simulation POST; application service | Immutable tuple, idempotency record, accepted state, outbox and audit in one transaction | Tuple compatibility and transaction rollback tests |
| 4 | Worker claims job | Outbox poll/lease | Attempt, lease and transition evidence | Duplicate delivery, lease expiry and crash-point tests |
| 5 | Worker runs both versions | Deterministic interpreter | Checksummed bounded outcomes/artifacts | No `eval`; resource budgets; repeat checksum tests |
| 6 | Comparator aggregates impact | Impact domain | Amount/state/error/event deltas and result checksum | Golden cases and boundary tests |
| 7 | Policy evaluates | Risk-policy domain | Version, normalized inputs, reasons, decision/checksum | Dangerous false-safe corpus; failures block |
| 8 | Reviewer decides | Impact GET; approval POST | Reviewer, exact result/policy, ETag and audit | Self/stale/replay/substitution rejection |
| 9 | Approver evaluates gate | Release-gate POST | Immutable allow/block and evidence checksum | Current approval/exact tuple required; all errors block |
| 10 | Auditor reproduces | Version resolution; audit GET | Reproduction record tied to original tuple | Pre-run checksum verification and tenant authorization |

## Boundary rules

- The web client never decides authorization, tenant scope, safety or gate outcome.
- API transactions own durable acceptance/outbox creation; workers own leased execution only.
- Interpreter and risk evaluator are deterministic domain components with no web/database dependency.
- Database and artifact access uses tenant-scoped interfaces.
- Protected mutations propagate actor and correlation identifiers into append-only audit evidence.
