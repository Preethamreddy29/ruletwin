# Deterministic Risk Policy Model

The risk policy is versioned data evaluated against canonical impact aggregates. It never calls a model or accepts free-form executable logic.

## Inputs

- Exact simulation result checksum and engine/rule/dataset tuple.
- Tenant and rule-family scope.
- Counts and rates for amount, state, error and emitted-event changes.
- Consequence classifications and affected-scenario coverage.
- Missing/invalid evidence indicators.

## Decision

The evaluator returns `allow`, `block`, or `error`. `error`, missing inputs, unknown consequence classes, stale checksums, invalid policy, or evaluator failure are treated as `block` by the release gate.

Rules are ordered, deterministic and explainable. Every result records policy version, matched rule identifiers, normalized inputs, decision, reasons and checksum. A policy version is immutable after first evaluation.

## Safety invariants

1. Dangerous false-safe count must remain zero in the versioned high-consequence corpus.
2. Threshold equality behavior is explicit and covered by boundary tests.
3. Tenant overrides can only tighten global safety unless an accepted ADR defines a governed exception.
4. An approval cannot override missing or invalid evidence.
5. Policy/evaluator version changes invalidate earlier approvals unless compatibility is explicitly proven.

## Policy v0.1 decision rules

The initial policy is deliberately conservative and uses categorical/zero-tolerance safety boundaries rather than invented performance measurements:

1. Block when any required version/checksum/scenario is missing, stale, unknown or invalid.
2. Block any change classified as high consequence.
3. Block any new error, unexpected error-code change or unexpected emitted-event change.
4. Block state transitions outside the rule-family allowlist.
5. Block monetary deltas unless the exact rule-family policy explicitly permits the direction, boundary and rounding result.
6. Block when required affected/control/effective-date scenarios are absent.
7. Allow only after all rules evaluate without error and the evidence tuple remains current; approval/gate separation still applies.

Policy thresholds can be refined only through a new immutable policy version with synthetic corpus evidence. Performance and product-value thresholds remain unmeasured and are not inferred from this design.
