# Progress and Status

**As of:** 2026-10-25

**Baseline:** `main` at `257e604`

**Milestone:** Controlled-pilot readiness implementation

**Overall:** Tenant authorization and checksum-bound evidence export are merged with successful protected CI. A provider-neutral OIDC verification foundation is implemented on branch `codex/pilot-oidc-foundation` and awaits review/merge. RuleTwin is suitable for a synthetic local demonstration. It is not approved for an externally hosted pilot or real data.

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

## Current limits

- Development identities remain local-only. OIDC provider selection, user provisioning, and browser login/logout are not complete.
- Isolation evidence covers implemented API/UI paths, including completed-simulation JSON export, only; every future reproduction, artifact, webhook, metrics, and operator path must be protected or disabled.
- Only the deterministic rounding-rule family and synthetic data packs are supported.
- Hosted deployment, secret management, recovery, rollback, operational alerts, resource limits, SBOM/release artifacts, and measured reference-profile performance do not yet have pilot exit evidence.

## Next milestone

The approved implementation baseline is [`docs/pilot-readiness-plan.md`](pilot-readiness-plan.md). Work is ordered as:

1. Review and merge the provider-neutral OIDC verification foundation.
2. Select the provider and implement authorization-code/PKCE login, logout, and deployed identity configuration evidence.
3. Resource limits, rate controls, observability, and alerting.
4. Reproducible deployment, external secret storage, backup/restore, and rollback.
5. Security, isolation, recovery, performance, and usability acceptance.
6. Immutable `v0.4.0-pilot.1` release after every gate passes.

## Owner decisions required

Hosting and budget, domain/TLS ownership, OIDC provider, pilot identities and roles, backup retention and RPO/RTO, availability/support window, and hosted visibility remain required before deployment work can close.
