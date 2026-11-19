# Pilot Exposed-Surface Isolation Matrix

This is the complete network and operator surface inventory for the current rounding-rule pilot. Adding a route, export, artifact, metric label, service port, operator command, or webhook requires updating this matrix and its executable inventory test before merge.

## Edge and service boundaries

| Surface | Pilot exposure | Tenant-data rule | Evidence |
|---|---|---|---|
| HTTPS gateway | Only published pilot port | Routes web and `/api/*`; explicitly rejects metrics, framework docs, OpenAPI, and all development routes | `deploy/pilot/Caddyfile`; contract test |
| Web | Internal gateway target | Static application only; tenant data comes from authenticated API responses | Internal `frontend` network; no published port |
| API | Internal web/Prometheus target | Business routes require authenticated database-resolved membership; operations routes contain no tenant payload | Route inventory test and integration matrix |
| Worker | Internal process with database access | Claims one tenant-bearing outbox event and repeats tenant predicates for every object read/write | No HTTP listener or published port; worker recovery tests |
| PostgreSQL | Internal backend only | Composite tenant/object predicates, foreign keys, and application-role grants | Internal `backend` network; migration/integration tests |
| Prometheus | Internal frontend only | Scrapes aggregate, label-bounded metrics with no tenant, user, object, rule, or event identifier | Metric redaction test; no published port |

## HTTP surface inventory

| Method and path | Classification | Isolation decision |
|---|---|---|
| `GET /health/live` | Public operational | Static service/alive status only; no database or tenant data |
| `GET /health/ready` | Public operational | Boolean database reachability only; no tenant data |
| `GET /version` | Public operational | Service and immutable version only |
| `GET /metrics` | Internal operator | Aggregate counters/gauges only; blocked by the pilot gateway and scraped directly on the internal network |
| `/docs`, `/openapi.json` | Disabled in pilot | FastAPI disables framework docs outside dev/test; gateway also rejects them |
| `/v1/dev/*` | Disabled in pilot | Hidden from OpenAPI, rejected outside dev/test, and blocked by the pilot gateway |
| `GET /v1/session` | Authenticated identity | Returns only the caller's resolved user, tenant, and roles |
| `GET /v1/scenarios` | Tenant list | Synthesizes only the caller's assigned tenant scenario |
| `POST /v1/tenants/{tenant_id}/rule-versions` | Tenant mutation | Path tenant must equal identity tenant; author role required |
| `POST /v1/replay-datasets` | Tenant mutation | Body tenant must equal identity tenant; author/reviewer role required |
| `POST /v1/simulations` | Tenant mutation | Body tenant and every referenced object must belong to identity tenant |
| `GET /v1/simulations/{id}` | Tenant object | Tenant predicate; cross-tenant and absent objects share the same 404 response |
| `GET /v1/simulations/{id}/impact` | Tenant object | Parent simulation and impact are selected with tenant predicates |
| `GET /v1/simulations/{id}/evidence-export` | Tenant export/artifact | Parent authorization precedes checksum-bound content; cross-tenant returns non-enumerating 404 |
| `POST /v1/simulations/{id}/approvals` | Tenant mutation | Reviewer role, tenant predicate, self-approval denial, current exact evidence |
| `POST /v1/release-gates/evaluate` | Tenant mutation | Release-approver role; simulation, approval, policy, and checksum must share caller tenant |
| `GET /v1/audit-events` | Tenant list/cursor | Tenant predicate is fixed by identity; opaque cursor contains ordering boundary only and cannot select a tenant |

## Not exposed

- Evidence reproduction/import, standalone artifact reads, webhooks, public metrics, database administration, worker control, and general-purpose rule execution have no pilot HTTP route.
- Backup, restore, deployment-record, provisioning, and release-evidence commands are local operator actions. They are not served by the application and require host/provider access outside human tenant roles.
- Future routes are denied by the executable exact-route inventory until deliberately classified here.

## Exit rule

PILOT-02 repository scope passes only when the exact-route inventory, cross-tenant negative matrix, metric redaction checks, gateway/internal-network contract, and all protected checks pass. Any new exposed surface reopens this assessment.
