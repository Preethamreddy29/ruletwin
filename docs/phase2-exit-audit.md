# RuleTwin Phase 2 Exit Audit

**Audit date:** 2026-09-27
**Gate:** repeatable engineering base
**Scope:** Phase 2 foundation only; no Phase 3 product-capability claim.

| Exit criterion | Classification | Evidence |
|---|---|---|
| One command starts core services | Satisfied with local evidence | `./scripts/dev.ps1 up` built and started PostgreSQL, the migration job, API, worker and web from a stopped state. PostgreSQL and API became healthy, the migration exited `0`, and the web returned HTTP `200`. Warm-cache startup with a retained database volume was 26.14 seconds. |
| One command runs checks | Satisfied with local evidence | `./scripts/check.ps1 -Integration` provisioned the isolated `ruletwin_test` database, ran the reversible migration cycle, then passed Python and web formatting, lint, types, tests, coverage, contract, secret, build and Compose checks. |
| CI builds from a clean runner | Missing external evidence | `.github/workflows/ci.yml` defines backend/PostgreSQL, web, contract/security and container jobs. The workflow cannot run until this branch is committed and pushed. |
| Health and telemetry are visible | Satisfied with local evidence | Live liveness, readiness, version, metrics and web requests returned HTTP `200`. Prometheus reported target `http://api:8000/metrics` healthy with `up{job="ruletwin-api"}=1`. |

## Required test classification

| Required evidence | Classification |
|---|---|
| Clean database migration up/down/forward policy | Satisfied — isolated `ruletwin_test` upgrade, downgrade to base, forward upgrade and `alembic check` passed |
| Readiness with healthy/unhealthy database | Satisfied — live PostgreSQL readiness passed; controlled unavailable-probe behavior passes component tests |
| API error mapping | Satisfied with executable component tests |
| Worker claims one outbox item safely | Satisfied — PostgreSQL integration test exercised the `FOR UPDATE SKIP LOCKED` claim and lease update |
| Container runs as non-root | Satisfied — runtime inspection found API/worker `10001:10001` and web `101:101`; all three root filesystems are read-only |
| Secret scanner rejects a planted controlled fixture | Satisfied with executable test |

## Deployment evidence

- Deployment identifier: `v0.1.0-dev-foundation` (development claim only; no release tag created).
- Local reference system: HP Pavilion Laptop 14-dv2xxx; Intel Core i5-1235U (10 cores, 12 logical processors); 15.7 GiB RAM; Windows 11 build 26200; Docker Desktop 4.91.0 with WSL 2.7.14.
- Measured warm-cache core startup: 26.14 seconds from stopped containers with retained volumes.
- A true clean-clone/clean-runner measurement remains external evidence and must not be inferred from the warm-cache result.

## Decision

**Phase 2 implementation and all locally executable gate evidence are complete. Phase 2 is not formally closed until the clean GitHub Actions run passes.** The same run will provide the remaining clean-runner and security-scan evidence. Any CI failure reopens the affected criterion.

Phase 3 remains deferred until the Phase 2 pull request passes CI and is merged.
