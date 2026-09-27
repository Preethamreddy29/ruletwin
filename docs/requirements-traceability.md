# Phase 1 Requirements Traceability

`Planned` means no implementation or passing test exists.

The authoritative functional requirements and NFR identifiers are defined in [`product/requirements.md`](product/requirements.md) and [`architecture/nfrs.md`](architecture/nfrs.md).

| Requirement | Design artifact | Planned verification | Status |
|---|---|---|---|
| Immutable tenant-scoped rule versions | `domain-model.md`, `data/data-model.md`, `data/schema-review.md` | Schema, immutability, overlap and tenant tests | Phase 1 design complete; not implemented |
| Deterministic replay tuple | `domain-model.md`, ADR-005 | Repeated canonical checksum across restart | Phase 1 design complete; not implemented |
| Baseline/candidate comparison dimensions | `domain-model.md`, `../packages/contracts/openapi.json` | Golden amount/state/error/event cases | Phase 1 design complete; tests deferred |
| Versioned fail-closed risk policy | `risk-policy.md`, ADR-007 | Dangerous/safe/missing/invalid policy corpus | Phase 1 policy complete; not implemented |
| Separation of duties and tenant isolation | `security/tenant-rbac.md`, `security/authorization-matrix.md`, ADR-003/008 | Complete role/action/object/path matrix | Phase 1 matrix complete; tests deferred |
| Durable asynchronous simulation | ADR-002, data model, signature workflow | Crash-point/outbox/duplicate-delivery tests | Phase 1 design complete; not implemented |
| Stable versioned API behavior | `../packages/contracts/openapi.json`, `api/examples.md` | JSON/OpenAPI structure/reference validation and contract examples | Phase 1 contract complete and structurally validated |
| High threats mapped to controls/tests | `security/threat-model.md`, `security/threat-to-test.md` | Threat review and later negative tests | Phase 1 mapping reviewed; tests deferred |
| Eight required architecture decisions | `decisions/ADR-001` through `ADR-008` | Review status and revisit triggers | Eight accepted ADRs |
| Signature workflow UI-to-data traceability | `architecture/signature-workflow.md` | Walkthrough of every boundary and stored tuple | Phase 1 trace reviewed |

## Gate status

Phase 1 **passes locally as a design gate**. See [`phase1-exit-audit.md`](phase1-exit-audit.md). All executable controls and tests remain future evidence and must not be represented as implemented.
