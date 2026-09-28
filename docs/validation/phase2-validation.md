# Phase 2 Validation Record

**Validation date:** 2026-09-27
**Branch:** `codex/phase2-engineering-foundation`
**Local environment:** Windows 11 build 26200, Python 3.12.1, Docker Desktop 4.91.0 / Engine 29.8.0, WSL 2.7.14

## Passing evidence

| Check | Result |
|---|---|
| One-command core startup | Pass — `./scripts/dev.ps1 up`; 26.14 seconds with warm Docker cache and retained volume |
| Compose configuration | Pass — full profile parsed successfully |
| API/worker/web image builds | Pass |
| Core runtime | Pass — PostgreSQL and API healthy; migration exit `0`; worker and web running |
| HTTP smoke | Pass — liveness, readiness, version, metrics and web returned `200` |
| Deterministic seed | Pass — rerunnable result contained 1 tenant, 1 user, 4 roles and 2 assignments |
| Database revision | Pass — `20260927_0001` |
| Migration policy | Pass — upgrade, downgrade to base, forward upgrade and drift check against isolated `ruletwin_test` |
| Python formatting and Ruff lint | Pass |
| Python strict mypy check | Pass — 16 source files |
| Python unit/component/integration tests | Pass — 20 passed against live PostgreSQL |
| Python covered scope | Pass — 95.81% total |
| Web Prettier and ESLint | Pass |
| Web TypeScript check | Pass |
| Web component tests | Pass — 3 passed |
| Web covered scope | Pass — 100% statements/lines/functions; 95.23% branches |
| Production web build | Pass |
| OpenAPI structure/references | Pass — 10 paths, 10 operations, 111 references |
| Repository secret scan | Pass, including controlled planted-secret rejection test |
| Package lock reproducibility | Pass — frozen offline install |
| JSON/YAML and local Markdown-link validation | Pass |
| Runtime container identity | Pass — API/worker `10001:10001`, web `101:101` |
| Runtime read-only root filesystems | Pass — API, worker and web |
| Prometheus scrape | Pass — RuleTwin API target health `up`, query value `1` |

## Defects found and resolved during live validation

1. Added `/tmp` as an in-memory filesystem for the read-only Nginx container.
2. Added a dedicated host-bridge network so PostgreSQL remains isolated while local tests can use the loopback-only `127.0.0.1:5432` binding.
3. Made the migration-cycle script invoke Alembic through the active Python interpreter on Windows.
4. Selected the Windows-compatible async event loop for Alembic and pytest PostgreSQL execution.
5. Excluded generated web coverage/build output from repeatable Prettier checks.
6. Made `./scripts/check.ps1 -Integration` safely provision and migrate only `ruletwin_test` when no external test URL is supplied.

## Pending external evidence

| Check | Reason |
|---|---|
| Clean GitHub Actions run | Branch is local and uncommitted; workflow requires commit and push |
| Dependency/static/container vulnerability jobs | Configured in GitHub Actions; results cannot be claimed before the workflow runs |
| Clean-clone startup measurement | The measured local result used cached images and a retained volume |

This record distinguishes local development evidence from clean-runner and production evidence. It makes no production-readiness claim.
