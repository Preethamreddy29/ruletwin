# Tenant, RBAC and Separation of Duties

## Roles

| Capability | Analyst | QA reviewer | Release approver | Auditor | Operator |
|---|---:|---:|---:|---:|---:|
| Create candidate rule version | Yes | No | No | No | No |
| Create replay dataset/simulation | Yes | Yes | No | No | No |
| View tenant-scoped impact | Yes | Yes | Yes | Yes | Limited diagnostics |
| Submit review approval | No | Yes | No | No | No |
| Evaluate/record release gate | No | No | Yes | No | No |
| Reproduce/export evidence | Limited | Yes | Yes | Yes | No |
| View operational health | No | No | No | No | Yes |

## Enforcement rules

- Authentication establishes an actor; server-side authorization resolves roles and tenant memberships.
- Every lookup, list, filter, export, artifact download, metric label and worker job is tenant-scoped and object-authorized.
- Opaque UUIDs reduce enumeration value but never replace authorization.
- The candidate author cannot approve the same evidence. The release approver must act on a current reviewer approval bound to the exact checksum.
- Operators can diagnose execution state without reading rule/event/result payloads by default.
- Authorization denial is stable and non-enumerating; cross-tenant objects are not distinguishable from absent objects.

Phase 4A converts the implemented rounding workflow rows into executable same-tenant, wrong-role, absent-membership and cross-tenant tests. Export, artifact, webhook, metrics and operator-specific rows remain planned for later Phase 4/5 increments.
