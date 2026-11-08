# Progress and Status

## Update — 2026-11-08, post-resource-safety baseline

PR #22 merged the provider-neutral OIDC verification foundation as `8c51d54`. PR #24 merged standards-based authorization-code/PKCE browser login, provider logout, session-scoped token storage, invited-subject provisioning, and Auth0 operations guidance as `e95e3ba`. PR #25 merged the resource-safety foundation as `d7365e6`. All three increments passed the five protected CI checks.

The resource-safety foundation adds request-body, replay-dataset, per-tenant queue, execution-time, retry-attempt, retry-delay, and worker-concurrency controls. It includes problem responses, OpenAPI declarations, configuration bounds, boundary tests, and clean-runner integration/container evidence. PILOT-06 remains partially satisfied because sustained saturation behavior, container timeout/recovery, and measured resource use on the named pilot reference profile are not yet recorded.

PILOT-01 also remains open: the Auth0 tenant/application/API and namespaced tenant claim require owner configuration, distinct invited subjects must be provisioned, and deployed login/logout, invalid-token, and provider key-rotation evidence must pass.

**As of:** 2026-11-08

**Baseline:** `main` at `d7365e6`

**Milestone:** Controlled-pilot readiness implementation

**Overall:** Tenant authorization, checksum-bound evidence export, OIDC verification, Auth0/PKCE browser integration, and the resource-safety foundation are merged with successful protected CI. RuleTwin is suitable for a synthetic local demonstration. It is not approved for an externally hosted pilot or real data.

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
- Hosted deployment, secret management, recovery, rollback, operational alerts, complete resource-safety evidence, SBOM/release artifacts, and measured reference-profile performance do not yet have pilot exit evidence.

## Next milestone

The approved implementation baseline is [`docs/pilot-readiness-plan.md`](pilot-readiness-plan.md). Work is ordered as:

1. Add structured operational telemetry, health signals, rate controls, actionable alerts, and an incident runbook.
2. Complete Auth0-hosted login/logout, invited identity, invalid-token, and rotation evidence.
3. Complete sustained saturation, timeout/recovery, and reference-profile evidence for PILOT-06.
4. Add reproducible deployment, external secret storage, backup/restore, and rollback.
5. Complete security, isolation, recovery, performance, and usability acceptance.
6. Publish immutable `v0.4.0-pilot.1` artifacts only after every gate passes.

## Owner decisions required

Hosting and budget, domain/TLS ownership, Auth0 tenant ownership, pilot identities and roles, backup retention and RPO/RTO, availability/support window, and hosted visibility remain required before deployment work can close.
