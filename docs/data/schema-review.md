# Phase 1 Schema and Lifecycle Review

**Review date:** 2026-09-27
**Scope:** conceptual PostgreSQL design only; no migrations or database exist.
**Outcome:** accepted for Phase 2 implementation, subject to migration-level verification.

## Key and constraint decisions

| Area | Required design |
|---|---|
| Tenant ownership | Every tenant-owned table carries `tenant_id`; identifiers remain opaque UUIDs; foreign keys include tenant scope where the referenced object is tenant-owned. |
| Immutability | Rule versions, dataset manifests, business events, outcomes, impact deltas, risk-policy versions, evaluations, approvals, gates and audit events have no application update path. Corrections create linked replacements. |
| Rule dates | Exclusion constraint prevents overlapping `[effective_from, effective_until)` ranges for the same tenant/definition where the rule family disallows overlap. Open end represents infinity. |
| Dependencies | Unique `(tenant_id, from_version_id, to_version_id)` edge; self-edge rejected; both ends share tenant; bounded domain traversal rejects cycles and incompatible schemas. |
| Simulations | Unique idempotency record by tenant, actor, operation and key; canonical request hash detects conflicting key reuse. The simulation stores the exact engine, baseline, candidate, dataset and policy versions. |
| Worker leasing | One active lease per runnable simulation attempt; state/version compare-and-swap prevents stale completion; attempts are retained. |
| Evidence binding | Approval references exact simulation result checksum and policy version. Gate references current approval, result and policy checksums. |
| Audit | Insert-only application permission; actor, tenant, action, object, correlation, causation, timestamp and optional evidence checksum required. |
| Artifacts | Content-addressed checksum plus tenant/parent authorization metadata; a locator alone never grants access. |

## Initial indexes

- Tenant plus stable object ID on every tenant-owned table.
- Rule definition by tenant/name and versions by tenant/definition/effective range.
- Simulation by tenant/status/created time; outbox by availability/status/lease expiry.
- Impact deltas by tenant/simulation/consequence and rule/scenario dimensions.
- Audit events by tenant/time, tenant/object/time and correlation ID.
- Unique checksums only where canonical content is intentionally de-duplicated within the same tenant.

Indexes will be verified with representative synthetic query plans in later phases; no performance claim is made here.

## Retention policy v0.1

| Data | Design retention |
|---|---|
| Rule, dataset and risk-policy versions | Indefinite for the local v1 portfolio unless explicitly superseded and unreferenced; metadata remains immutable. |
| Approvals, release gates and audit events | Indefinite; application cannot delete them. |
| Decision-critical aggregates/checksums | At least as long as any approval/gate references them; local v1 default indefinite. |
| Detailed outcome artifacts | 90 days after an ungated simulation completes; indefinitely while referenced by an approval/gate. Expiry creates an audit event and tombstone. |
| Idempotency records | 24 hours minimum, then only when no active operation depends on them. |
| Completed outbox delivery records | 30 days; business/audit evidence is retained separately. |
| Redacted operational logs | 14 days by default; never a substitute for audit evidence. |

## Review checklist

- Tenant keys and cross-tenant foreign-key prevention: accepted.
- Immutable evidence chain and stale-approval behavior: accepted.
- Date-range and dependency constraints: accepted.
- Durable outbox/lease model: accepted via ADR-002.
- Artifact split and retention: accepted via ADR-006 and this policy.
- Migration types, privileges and actual query plans: deferred correctly to Phase 2 implementation evidence.
