# ADR-003: Shared-Schema Multitenancy

**Status:** Accepted for Phase 2 implementation (2026-09-27)
**Decision:** Use one PostgreSQL database/schema with mandatory tenant keys, composite constraints and tenant-scoped repository interfaces. Evaluate row-level security as defense in depth before implementation.
**Why:** Three synthetic tenants do not justify database-per-tenant operations, while explicit scoping remains testable.
**Alternatives:** Schema-per-tenant; database-per-tenant.
**Consequences:** Every path, join, filter, export, job and artifact requires tenant tests; one missed predicate is high severity.
**Revisit when:** Regulatory isolation, per-tenant restore or scale requirements demand a stronger physical boundary.
