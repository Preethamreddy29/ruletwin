# ADR-002: PostgreSQL Transactional Outbox

**Status:** Accepted for Phase 2 implementation (2026-09-27)
**Decision:** Persist simulation state and an outbox record in one PostgreSQL transaction; a separate worker polls and leases events. No broker is used in v1.
**Why:** This avoids dual-write loss while meeting the zero-cash local deployment constraint.
**Alternatives:** Managed/self-hosted broker; synchronous execution; database notifications alone.
**Consequences:** At-least-once delivery requires idempotent handlers, leases, retry state and backlog metrics.
**Revisit when:** Measured throughput, latency or fan-out cannot be met safely with polling.
