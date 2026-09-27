# ADR-006: Database Metadata with Content-Addressed Artifacts

**Status:** Accepted for Phase 2 implementation (2026-09-27)
**Decision:** Keep decision-critical metadata, aggregates and checksums in PostgreSQL; store large bounded detailed results in local content-addressed artifact storage referenced by immutable metadata.
**Why:** This preserves transactional discovery and authorization without forcing unbounded payloads into transactional rows.
**Alternatives:** All results in PostgreSQL; all results in object storage.
**Consequences:** Authorization applies to artifacts; checksum, lifecycle, tombstone and backup behavior must be tested. Retention durations remain open.
**Revisit when:** Measured result sizes and database behavior support a simpler single-store design.
