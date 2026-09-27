# RuleTwin Non-Functional Requirement Baseline

Targets are hypotheses until measured on a named local machine. Hard isolation and false-safe gates cannot be weakened to satisfy performance targets.

| ID | Concern | Phase 1 target/constraint | Planned evidence |
|---|---|---|---|
| RT-NFR-01 | Cost/deployment | ₹0 cash cost; local Docker Compose; no required managed service | Dependency/infrastructure inventory and clean-clone start |
| RT-NFR-02 | Tenant isolation | Zero cross-tenant disclosure/action across the complete matrix | RT-ISO test family, including filters, cursors, exports, artifacts, workers and telemetry |
| RT-NFR-03 | Determinism | Same engine/rule/dataset/policy tuple yields the same canonical outcome checksum | Repeated runs across process/worker restart |
| RT-NFR-04 | Scale hypothesis | Three tenants and up to 100,000 synthetic events on the reference laptop | Versioned load profile with hardware/resources recorded |
| RT-NFR-05 | API acknowledgement | Simulation acceptance P95 below 750 ms, measured separately from execution | Load test for request/transaction/outbox acknowledgement |
| RT-NFR-06 | Replay latency | Set the 10,000-event target only after a measured baseline | Reproducible benchmark; no invented threshold |
| RT-NFR-07 | Durability | Acknowledged simulation survives worker crash and duplicate delivery | Transaction/outbox/crash-point/restart suite |
| RT-NFR-08 | Idempotency | Same canonical request/key returns one logical simulation; conflicting reuse returns 409 | Concurrent duplicate and conflicting-payload tests |
| RT-NFR-09 | Audit completeness | 100% of protected mutations produce complete append-only audit evidence | Mutation-to-audit matrix and DB privilege tests |
| RT-NFR-10 | Safety | No arbitrary execution; zero dangerous false-safe results | Hostile rule corpus and fail-closed policy corpus |
| RT-NFR-11 | Operability | Health/readiness, structured redacted logs, correlation IDs and bounded metrics | Unhealthy dependency and telemetry smoke tests |
| RT-NFR-12 | Recovery | Initial RPO 24h/RTO 60m; design target RPO 15m subject to rehearsal | Timed backup/restore into a clean database |
| RT-NFR-13 | Accessibility | Keyboard, semantic form, focus, error and contrast fundamentals | Automated and manual checks in later UI phases |

## Measurement rule

Every result must record commit/version, dataset, machine profile, command, sample count and raw report. A plan or synthetic expectation is not a passing measurement.
