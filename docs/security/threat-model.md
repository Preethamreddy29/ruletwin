# RuleTwin Phase 1 Threat Model

Status: design hypothesis. Planned controls and tests are not implemented evidence.

## Assets and boundaries

Assets include tenant data, rule and dataset versions, simulation results, policy decisions, approvals, gates, audit history, credentials and service availability. Trust boundaries exist at browser/API, API/database, outbox/worker, worker/artifact store and export surfaces.

| ID | STRIDE | Threat | Impact | Planned controls | Planned verification |
|---|---|---|---|---|---|
| RT-T01 | Spoofing/Elevation | Forged identity or tenant context | Cross-tenant action | Signed short-lived token, server-resolved membership, object authorization | Invalid/expired token and tenant-confusion matrix |
| RT-T02 | Information disclosure | Cross-tenant lookup, list, export, artifact or metric leakage | Critical confidentiality breach | Tenant-scoped repositories, composite keys, non-enumerating denial, redacted telemetry | Complete cross-tenant path/filter/export/artifact/worker/metric suite |
| RT-T03 | Tampering | Rule or dataset altered after submission | False simulation evidence | Immutable versions, canonical checksums, FK constraints | Mutation rejection and checksum-substitution tests |
| RT-T04 | Tampering/Elevation | Self-approval, replayed approval or evidence substitution | Unsafe release allowed | Separation of duties, nonce/version, expiry, exact checksum binding | Self/stale/replay/substitution negative tests |
| RT-T05 | Tampering | Risk policy unavailable or malformed but reports safe | Dangerous false-safe | Versioned schema, deterministic evaluator, fail closed | Missing/invalid/unavailable policy corpus; false-safe must be zero |
| RT-T06 | DoS/Elevation | Pathological rule or arbitrary-code injection | Resource exhaustion or execution | Declarative schema, allowlisted interpreter, depth/size/operator/time budgets; no eval/exec | Hostile input and budget boundary tests |
| RT-T07 | DoS | Oversized simulation exhausts API/worker/storage | Availability loss | Request limits, quotas, async queue, leases, cancellation and backpressure | Oversize/rate/queue saturation and crash tests |
| RT-T08 | Repudiation/Tampering | Audit deletion, forgery or missing protected mutation | Decision cannot be defended | Append-only DB privileges, correlation/actor/checksum fields | Privilege tests and 100% mutation-to-audit matrix |
| RT-T09 | Information disclosure | Secrets or tenant values enter logs/errors | Credential/data leakage | Structured allowlisted logs, redaction, generic errors | Planted-secret and tenant-payload scanning |
| RT-T10 | Tampering/Repudiation | Worker duplicate or crash changes outcome | Lost or inconsistent acknowledged work | Transactional outbox, leases, idempotent transitions, deterministic tuple | Crash-point, duplicate-delivery and restart replay tests |

## High-risk gate

RT-T01 through RT-T06 and RT-T08 are release-blocking high threats. Phase 1 requires reviewed planned controls and tests; later phases require executable evidence before any claim of mitigation.

The planned test families and required assertions are reviewed in [`threat-to-test.md`](threat-to-test.md).
