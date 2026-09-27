# ADR-004: Relational Rule Dependencies

**Status:** Accepted for Phase 2 implementation (2026-09-27)
**Decision:** Store versioned dependency edges in PostgreSQL and perform bounded cycle/compatibility validation in the domain layer.
**Why:** The graph is small, transactional and queried with known traversals; a graph database adds unjustified operations.
**Alternatives:** Graph database; dependency arrays embedded only in JSON.
**Consequences:** Recursive queries and traversal budgets are explicit; edges remain constrained and auditable.
**Revisit when:** Measured graph size or traversal patterns exceed relational safety/performance targets.
