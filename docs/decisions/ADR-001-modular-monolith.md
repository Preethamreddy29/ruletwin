# ADR-001: Modular Monolith

**Status:** Accepted for Phase 2 implementation (2026-09-27)
**Decision:** Use one FastAPI modular-monolith API with explicit module boundaries and a separate worker process sharing application/domain packages.
**Why:** The v1 workflow is transactionally cohesive and does not justify distributed ownership or operational cost.
**Alternatives:** Microservices; single undifferentiated application.
**Consequences:** Module dependency rules and tests are required; deployment remains simple; later extraction must occur through versioned contracts.
**Revisit when:** Independent scaling, ownership or release cadence is proven by measurements rather than anticipated.
