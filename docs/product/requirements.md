# RuleTwin Phase 1 Requirements

These requirements define v1 intent and acceptance design. “Must” does not imply implementation exists.

| ID | Requirement | Phase 1 acceptance design |
|---|---|---|
| RT-F01 | Create immutable tenant-scoped rule versions from validated declarative JSON. | Rule schema version, author, effective range, dependencies, canonical checksum and audit fields are required. |
| RT-F02 | Support rounding, tiered rate, late fee, effective-date eligibility and exception-routing families. | Every family has a bounded allowlisted representation; executable user code is prohibited. |
| RT-F03 | Create deterministic synthetic replay datasets. | Manifest records tenant, fixed seed, generator/event-schema versions, count and checksum. |
| RT-F04 | Run baseline and candidate versions in isolated bounded evaluation contexts. | Exact version tuple and resource budgets are recorded; no tenant state crosses the evaluation boundary. |
| RT-F05 | Compare money, workflow state, errors, emitted events and latency metadata. | Canonical safety-relevant values determine result checksum; nondeterministic latency observation is reported but excluded from it. |
| RT-F06 | Aggregate deltas by tenant, rule, scenario and consequence. | Impact contract exposes bounded aggregates and evidence checksum. |
| RT-F07 | Apply an immutable deterministic risk-policy version. | Missing, invalid, stale or errored policy/evidence fails closed. |
| RT-F08 | Enforce author, reviewer and release-approver separation. | Self/stale/replayed/substituted approval cannot produce an allow gate. |
| RT-F09 | Emit an immutable release-gate result and auditable evidence tuple. | Gate binds simulation result, policy and current approval checksums with reasons and actor/correlation data. |
| RT-F10 | Reproduce a previous decision. | Reproduction resolves only exact immutable engine/rule/dataset/policy versions and verifies checksums first. |
| RT-F11 | Expose stable versioned HTTP contracts and errors. | OpenAPI 3.1 defines all ten required operations, idempotency, correlation, concurrency and problem responses. |
| RT-F12 | Protect every object, list, export, artifact and worker path by tenant and role. | Authorization matrix and non-enumerating denial behavior are mandatory. |

## Explicit non-goals

- Billing execution, production data writes or payment processing.
- General-purpose no-code rule authoring or arbitrary scripts.
- AI-generated rules or probabilistic safety decisions.
- Cross-repository database access or shared runtime libraries.
- DecisionTrace or BoundaryOps implementation during RuleTwin v1.
