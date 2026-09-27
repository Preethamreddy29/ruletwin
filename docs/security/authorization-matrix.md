# Authorization and Tenant-Isolation Matrix

Every row is a planned server-side decision and later requires same-tenant allow tests plus cross-tenant, wrong-role, absent-membership and stale-state denial tests.

| Resource/action | Analyst | QA reviewer | Release approver | Auditor | Operator | Object/state rule |
|---|---:|---:|---:|---:|---:|---|
| Create rule version | Allow | Deny | Deny | Deny | Deny | Tenant membership; validated scope; author recorded |
| Read rule version/diff | Allow | Allow | Allow | Allow | Deny | Both compared versions belong to actor tenant |
| Create dataset | Allow | Allow | Deny | Deny | Deny | Synthetic-only tenant dataset |
| Create simulation | Allow | Allow | Deny | Deny | Deny | All tuple objects belong to actor tenant and are compatible |
| Read simulation/impact | Allow | Allow | Allow | Allow | Metadata only | Tenant match; operator cannot read payload by default |
| Submit approval | Deny | Allow | Deny | Deny | Deny | Reviewer differs from candidate author; current exact evidence |
| Evaluate release gate | Deny | Deny | Allow | Deny | Deny | Current approval and policy/evidence tuple required |
| List audit events | Own actions only | Relevant tenant | Relevant tenant | Allow | Operational metadata | Tenant scope and cursor/filter authorization |
| Export/reproduce evidence | Deny | Allow | Allow | Allow | Deny | Tenant scope; immutable tuple; export audit required |
| Claim/complete worker job | Deny | Deny | Deny | Deny | Service identity only | Lease, tenant context and exact tuple propagated |
| Read artifact | Relevant tenant | Relevant tenant | Relevant tenant | Relevant tenant | Deny | Parent-object authorization precedes content access |
| Read metrics/logs | Deny | Deny | Deny | Deny | Allow redacted | No tenant payload or unbounded tenant identifier label |

## Mandatory denial behavior

- Cross-tenant and unauthorized-object requests return the same non-enumerating response as an absent object.
- List filters, pagination cursors and exports cannot broaden the actor's tenant scope.
- Artifact URLs are not authorization; every retrieval checks the parent object.
- Worker/service credentials cannot call human approval or release-gate operations.
- Role changes do not retroactively make stale approvals valid.
- Audit records include denied protected mutations where safe, without recording secrets or full payloads.
