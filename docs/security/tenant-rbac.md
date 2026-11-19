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

The current pilot converts every exposed rounding-workflow row into executable same-tenant, wrong-role, absent-membership and cross-tenant tests. Completed-simulation export is parent-authorized. Metrics are aggregate-only and internal at the pilot gateway; standalone artifacts, webhooks, reproduction, and worker/operator APIs have no exposed route. See [`pilot-surface-isolation-matrix.md`](pilot-surface-isolation-matrix.md).
