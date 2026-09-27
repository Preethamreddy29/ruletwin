# Threat-to-Test Traceability

These are planned test identifiers. They are not implemented or passing-test evidence.

| Threat | Severity | Planned test IDs | Required assertion |
|---|---|---|---|
| RT-T01 forged identity/tenant | High | RT-SEC-001–004 | Invalid issuer/audience/signature/expiry and client tenant claims never establish access. |
| RT-T02 cross-tenant leakage | Critical | RT-ISO-001–012 | Every get/list/filter/cursor/export/artifact/worker/metric path denies cross-tenant access without enumeration. |
| RT-T03 evidence tampering | High | RT-INT-001–006 | Immutable writes reject mutation; substituted content/checksum or cross-tenant FK fails. |
| RT-T04 approval abuse | Critical | RT-APR-001–008 | Self, stale, replayed, expired, wrong-policy and substituted-result approvals cannot produce allow. |
| RT-T05 policy false-safe | Critical | RT-POL-001–010 | Missing, malformed, unknown, unavailable or error policy state blocks; dangerous false-safe count is zero. |
| RT-T06 rule injection/exhaustion | Critical | RT-RUL-001–012 | Unknown operators, executable strings, excessive depth/size/fan-out/time and cycles reject or terminate safely. |
| RT-T07 simulation DoS | High | RT-RES-001–007 | Oversize/rate/queue limits, cancellation and backpressure preserve bounded availability and visible failure. |
| RT-T08 audit loss/forgery | High | RT-AUD-001–006 | Application update/delete is denied and every protected mutation yields one complete audit event. |
| RT-T09 log/metric leakage | High | RT-LOG-001–005 | Planted secrets and tenant payloads do not appear in errors, logs, metrics or traces. |
| RT-T10 duplicate/crash inconsistency | High | RT-WRK-001–010 | Crash points, lease expiry, duplicate delivery and restart preserve acknowledged work and one logical result. |

## Phase 1 review result

Every high/critical threat has prevention/detection controls in the threat model and at least one explicit negative-test family. Test implementation and evidence remain mandatory in later phases; this mapping alone does not mitigate a threat.
