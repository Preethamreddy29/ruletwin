# API Contract Examples

These examples illustrate the Phase 1 contract. They are not responses from a running service.

## Create a simulation

```http
POST /v1/simulations
Authorization: Bearer <redacted>
Idempotency-Key: 01HZX7N4Q8R8W7M2A1T9C6K5PB
X-Correlation-ID: 11111111-1111-4111-8111-111111111111
Content-Type: application/json
```

```json
{
  "tenant_id": "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  "baseline_rule_version_id": "bbbbbbbb-bbbb-4bbb-8bbb-bbbbbbbbbbbb",
  "candidate_rule_version_id": "cccccccc-cccc-4ccc-8ccc-cccccccccccc",
  "dataset_manifest_id": "dddddddd-dddd-4ddd-8ddd-dddddddddddd",
  "engine_version": "0.1.0",
  "risk_policy_version_id": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee"
}
```

```http
HTTP/1.1 202 Accepted
Location: /v1/simulations/ffffffff-ffff-4fff-8fff-ffffffffffff
ETag: "1"
```

The same actor, tenant and idempotency key with an identical canonical request returns the same logical simulation. Reuse with a different canonical request returns `409`.

## Submit an approval

```http
POST /v1/simulations/ffffffff-ffff-4fff-8fff-ffffffffffff/approvals
Authorization: Bearer <redacted>
Idempotency-Key: 01HZX8C76GZ7RZHPDT28HVB1ZK
X-Correlation-ID: 22222222-2222-4222-8222-222222222222
If-Match: "3"
Content-Type: application/json
```

```json
{
  "result_checksum": "sha256:0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef",
  "policy_version_id": "eeeeeeee-eeee-4eee-8eee-eeeeeeeeeeee",
  "decision": "approve",
  "rationale": "Reviewed the synthetic high-consequence scenarios."
}
```

Self-approval, stale ETag, changed evidence, replayed approval or a mismatched policy version returns `409` with a stable problem code.

## Stable problem response

```http
HTTP/1.1 409 Conflict
Content-Type: application/problem+json
```

```json
{
  "type": "/problems/stale-evidence",
  "title": "Referenced evidence is stale",
  "status": 409,
  "code": "RT_STALE_EVIDENCE",
  "detail": "Refresh the simulation result before approving.",
  "correlation_id": "22222222-2222-4222-8222-222222222222"
}
```

Errors must not reveal whether an object exists in another tenant.
