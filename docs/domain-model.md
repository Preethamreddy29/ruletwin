# RuleTwin Domain Model

## Vocabulary

- **Tenant:** an isolated fictional customer configuration and authorization boundary.
- **Rule definition:** stable identity and rule family; contains no mutable executable code.
- **Rule version:** immutable, schema-validated declarative JSON plus scope, effective dates, dependencies, author, canonical form and checksum.
- **Replay dataset:** immutable manifest identifying a fixed seed, generator version, event schema version and checksum.
- **Simulation:** tenant-scoped request comparing one baseline tuple with one candidate tuple.
- **Simulation run:** one leased worker attempt; retries cannot change the logical result.
- **Outcome:** canonical result for one event and rule tuple: amount, workflow state, error, emitted events and measured latency metadata.
- **Impact delta:** normalized difference between baseline and candidate outcomes.
- **Risk policy:** immutable versioned rules that classify aggregated deltas and fail closed when evidence is missing or invalid.
- **Approval:** reviewer decision bound to an exact result checksum, policy version and concurrency version.
- **Release gate:** immutable allow/block outcome with its complete evidence tuple.
- **Audit event:** append-only record of a protected action and its actor, tenant, correlation and causation identifiers.

## Required rule families

Rounding, tiered rate, late fee, effective-date eligibility and exception routing. Rules are interpreted by an allowlisted deterministic interpreter; user-supplied executable code is prohibited.

## Core invariants

1. Every owned object is tenant-scoped; a client-supplied tenant identifier never establishes authorization.
2. Rule, dataset, policy, result, approval, gate and audit versions are immutable.
3. Canonical serialization and checksum algorithms are versioned.
4. A candidate cannot depend on a missing, cyclic or incompatible rule version.
5. Effective-date ranges for the same tenant and rule cannot overlap unless the rule-family contract explicitly permits it.
6. Identical engine/rule/dataset/policy tuples produce identical canonical outcome checksums; latency observations are excluded from the deterministic checksum.
7. Approval cannot be performed by the candidate author and is stale when referenced evidence changes.
8. A release gate fails closed for missing, stale, invalid or unavailable evidence or policy.
9. Audit events cannot be updated or deleted by the application role.
10. Reproduction resolves only immutable version identifiers and verifies all checksums before evaluation.

## Money and time decisions

- Monetary values use ISO-4217 currency plus integer minor units. Unsupported minor-unit precision is rejected; no binary floating point participates in financial comparison.
- Percentage/rate inputs use bounded exact decimal strings with schema-defined scale and explicit rounding at named calculation boundaries.
- Timestamps use UTC ISO-8601 instants. Business effective dates are calendar dates evaluated in a tenant-configured IANA timezone captured in the rule version.
- Effective ranges are start-inclusive and end-exclusive. Missing timezone or ambiguous/nonexistent local time fails validation.

These semantics are design decisions pending review; they are not implemented or empirically validated.
