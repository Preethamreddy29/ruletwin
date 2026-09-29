# ADR-009: Phase 3 Determinism, Evidence and Recovery Boundary

**Status:** Accepted  
**Date:** 2026-09-29

## Context

The first vertical slice must prove financial determinism, durable asynchronous work and evidence-bound approval without prematurely implementing the Phase 4 multi-tenant/RBAC breadth.

## Decision

1. Money is represented only as integer USD minor units. Phase 3 rounding uses allowlisted `half_up`, `up` and `down` modes; rule input is data and no dynamic code evaluation exists.
2. Canonical JSON is sorted, compact UTF-8 JSON and evidence identifiers use `sha256:` checksums. Latency is not part of deterministic evidence.
3. The scenario pack is generator `rounding-events-v1`, event schema `business-event-v1`, seed `314159`, count `100`. Its integer LCG avoids runtime-specific pseudo-random behavior.
4. Simulation acceptance writes `requested`, `queued`, audit records and the outbox item in one transaction. A worker claim is a lease; execution finalization, result records and outbox acknowledgement share one transaction. Redelivery sees completed evidence and acknowledges without rewriting it.
5. Risk policy `phase3-financial-threshold-v1` blocks when an event's absolute financial delta exceeds two minor units and fails closed for malformed impact.
6. Approval requires completed evidence, the current simulation ETag, exact result checksum, exact policy ID and an actor distinct from the requester. The release gate allows only an approving review plus an allow policy; every other state blocks.
7. The one-tenant UI uses fixed, separate synthetic development actor IDs passed in `X-Actor-ID`. This is deliberately not the Phase 4 authentication model.
8. Bounded Phase 3 outcomes remain relational. Artifact offload is deferred until larger measured result sets justify it.

Candidate versions are proposals rather than active effective schedules, so they may overlap the seeded baseline during comparison. Promotion/effective-range conflict enforcement belongs to the later release workflow.

## Consequences

- Identical engine/rule/dataset tuples reproduce the same result checksum across retries.
- A crash cannot lose an acknowledged simulation or create duplicate logical evidence.
- The Phase 3 security boundary is honest and narrow: separation of duties is enforced, but production authentication and general tenant isolation are not claimed.
- The approach is intentionally optimized for a small scenario pack; larger artifacts and throughput are measured before storage evolution.
