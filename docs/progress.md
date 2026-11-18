# Progress and Status

## Update — 2026-11-10, supply-chain preflight foundation

Branch `codex/pilot-supply-chain-release` starts from the deployment/recovery foundation merged through PR #30 at `a8a8ad9`. It adds API and web SPDX SBOM generation, JSON high/critical vulnerability reports, fail-closed image gates, immutable local image metadata, checksum-bound evidence manifests, retained pull-request artifacts, and a main-only manual preflight workflow. The workflow deliberately rejects the official pilot version form while other controlled-pilot gates remain open.

Local validation passed: reversible migrations and zero drift; 83 Python tests at 89.01% coverage; web lint, typing, 8 tests, and production build; workflow/OpenAPI/secret validation; both image builds; both SPDX SBOMs; zero unfixed high/critical findings after replacing the unsupported web runtime base; and checksum-bound manifest verification. PILOT-08 is not closed until the protected pull-request workflow and the main preflight workflow both pass and their evidence artifacts are retained.

## Update — 2026-11-10, deployment and recovery foundation

Branch `codex/pilot-deployment-recovery-foundation` starts from the operations baseline merged through PR #28 at `b88aa21`. It adds an HTTPS-only standalone pilot topology, immutable image-digest enforcement, internal service networks, mounted database-secret support, automated migration/seed ordering, release-record capture, checksum-bound PostgreSQL backups, isolated restore fingerprinting, and worker-restart evidence capture.

The complete database-backed Python suite passes with 75 tests and 89.01% coverage, plus clean formatting/lint and successful typing across 28 source files. Web lint, typing, 8 component tests, and the production build pass. The pilot Compose contract renders successfully. A live local rehearsal created a 110,494-byte checksum-bound backup in 0.816 seconds, restored it into an isolated database in 6.564 seconds, matched the migration/table/evidence fingerprint, restarted the worker, and removed the temporary database. Hosted image, TLS, secret-store, scheduled-backup, log-redaction, approved RPO/RTO, and release-specific rollback evidence remain required.

## Update — 2026-11-08, pilot operations baseline in progress

Development branch `codex/pilot-operations-baseline` starts from the refreshed protected `main` baseline at `381febd`. The increment adds aggregate database/queue/worker health metrics, eight actionable Prometheus rules, deterministic alert simulations, automated rule/configuration validation, and an incident runbook. Local validation passed across the database-backed Python suite, web quality/build, Prometheus configuration/rule tests, and the live full stack. It deliberately does not claim centralized hosted logs, notification delivery, operator rehearsal, protected branch evidence, or PILOT-07 closure.

## Update — 2026-11-08, post-resource-safety baseline

PR #22 merged the provider-neutral OIDC verification foundation as `8c51d54`. PR #24 merged standards-based authorization-code/PKCE browser login, provider logout, session-scoped token storage, invited-subject provisioning, and Auth0 operations guidance as `e95e3ba`. PR #25 merged the resource-safety foundation as `d7365e6`. All three increments passed the five protected CI checks.

The resource-safety foundation adds request-body, replay-dataset, per-tenant queue, execution-time, retry-attempt, retry-delay, and worker-concurrency controls. It includes problem responses, OpenAPI declarations, configuration bounds, boundary tests, and clean-runner integration/container evidence. PILOT-06 remains partially satisfied because sustained saturation behavior, container timeout/recovery, and measured resource use on the named pilot reference profile are not yet recorded.

PILOT-01 also remains open: the Auth0 tenant/application/API and namespaced tenant claim require owner configuration, distinct invited subjects must be provisioned, and deployed login/logout, invalid-token, and provider key-rotation evidence must pass.

**As of:** 2026-11-08

**Baseline:** `main` at `b88aa21`; deployment/recovery work on `codex/pilot-deployment-recovery-foundation`

**Milestone:** Controlled-pilot readiness implementation

**Overall:** Tenant authorization, evidence export, OIDC/Auth0 integration, resource safety, and operations are merged with successful protected CI. Deployment/secrets/recovery automation is implemented on the current branch but still needs live and hosted evidence. RuleTwin is suitable for a synthetic local demonstration. It is not approved for an externally hosted pilot or real data.

## Completed evidence

- Phase 3 first vertical slice merged through PR #13.
- Phase 4A multi-tenant authorization merged through PR #18 as `cffdb30`.
- Phase 4A pull-request and post-merge workflows passed all five protected CI checks.
- Main CI passed again at `d64275f` after the Gitleaks action upgrade.
- Two fictional tenants and four role-separated development personas per tenant are implemented.
- PostgreSQL-resolved membership, tenant/object authorization, non-enumerating cross-tenant denial, deterministic replay, fail-closed risk decisions, checksum-bound approval, release gates, outbox recovery, and audit evidence have executable coverage.
- Local Phase 4A validation recorded 46 Python tests, 93.56% Python coverage, 88.14% web statement coverage, Playwright critical-flow coverage, reversible migrations, zero schema drift, and no API/worker errors in the validated run.
- PR #21 adds a deterministic JSON bundle for completed simulations, including immutable input/result/impact/risk checksums, latest approval, release-gate result, an export checksum, attachment metadata, and an `evidence.exported` audit event.
- Export authorization is enforced for same-tenant reviewers, release approvers, and auditors; analysts are denied and cross-tenant simulation identifiers remain non-enumerating.
- Branch validation currently records 46 passing Python tests with 93.56% coverage, 3 passing web component tests, 2 passing Chromium workflows with real JSON downloads, valid 11-operation OpenAPI, and successful web lint, type checking, and production build.
- The OIDC foundation enforces RS256, exact issuer/audience, required subject and tenant claims, expiry, maximum token lifetime, bounded JWKS caching, controlled rotation refresh, stable external-subject mapping, database-resolved roles, and non-enumerating membership denial.
- OIDC branch validation currently records a reversible three-migration cycle, zero schema drift, 58 passing Python tests with 90.46% coverage, 3 passing web component tests with 88.31% statement coverage, 2 passing Chromium workflows, a production web build, and a valid 12-operation OpenAPI contract.
- PR #25 adds bounded request bodies and replay datasets, atomic per-tenant queue admission, bounded worker execution/retries, capped retry delay, and explicit single-process pilot worker concurrency. Its merge head passed backend/integration, contracts/security, web, Playwright, and Compose/container checks.

## Current limits

- Auth0-hosted configuration, invited-user provisioning, login/logout, invalid-token, and key-rotation evidence require owner/provider access and are not complete.
- Isolation evidence covers implemented API/UI paths, including completed-simulation JSON export, only; every future reproduction, artifact, webhook, metrics, and operator path must be protected or disabled.
- Only the deterministic rounding-rule family and synthetic data packs are supported.
- Hosted deployment, secret management, recovery, rollback, centralized log/notification delivery, complete resource-safety evidence, SBOM/release artifacts, and measured reference-profile performance do not yet have pilot exit evidence.

## Next milestone

The approved implementation baseline is [`docs/pilot-readiness-plan.md`](pilot-readiness-plan.md). Work is ordered as:

1. Complete Auth0-hosted login/logout, invited identity, invalid-token, and rotation evidence.
2. Complete sustained saturation, timeout/recovery, and reference-profile evidence for PILOT-06.
3. Deploy the reviewed immutable pilot topology and capture provider secret-store, HTTPS, log-redaction, scheduled-backup, restore, rollback, log, and alert-delivery evidence.
4. Complete supply-chain, security, isolation, performance, accessibility, and operator acceptance.
5. Publish immutable `v0.4.0-pilot.1` artifacts only after every gate passes.

## Owner decisions required

Hosting and budget, domain/TLS ownership, Auth0 tenant ownership, pilot identities and roles, backup retention and RPO/RTO, availability/support window, and hosted visibility remain required before deployment work can close.
