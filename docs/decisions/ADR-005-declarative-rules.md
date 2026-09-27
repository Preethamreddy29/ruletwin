# ADR-005: Declarative JSON Rules and Deterministic Interpreter

**Status:** Accepted for Phase 2 implementation (2026-09-27)
**Decision:** Represent rules as versioned schema-validated JSON executed only by an allowlisted deterministic interpreter. User code, `eval`, plugins and arbitrary expressions are prohibited in v1.
**Why:** Reproducibility, resource bounding and reviewability are hard release gates.
**Alternatives:** Executable scripts; general expression language; compiled plugins.
**Consequences:** The language is intentionally limited; canonicalization, schema versions, depth/operator budgets and golden semantics are required.
**Revisit when:** A documented user need cannot be expressed safely and a sandbox can be evidenced.
