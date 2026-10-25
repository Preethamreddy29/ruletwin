# Progress and Status

**As of:** 2026-10-25

**Baseline:** `main` at `bf90277`

**Milestone:** Controlled-pilot readiness implementation

**Overall:** Phase 4A and the controlled-pilot plan are merged. A tenant-authorized, checksum-bound JSON evidence export is implemented on branch `codex/pilot-evidence-export` and awaits review/merge. RuleTwin is suitable for a synthetic local demonstration. It is not approved for an externally hosted pilot or real data.

## Completed evidence

- Phase 3 first vertical slice merged through PR #13.
- Phase 4A multi-tenant authorization merged through PR #18 as `cffdb30`.
- Phase 4A pull-request and post-merge workflows passed all five protected CI checks.
- Main CI passed again at `d64275f` after the Gitleaks action upgrade.
- Two fictional tenants and four role-separated development personas per tenant are implemented.
- PostgreSQL-resolved membership, tenant/object authorization, non-enumerating cross-tenant denial, deterministic replay, fail-closed risk decisions, checksum-bound approval, release gates, outbox recovery, and audit evidence have executable coverage.
- Local Phase 4A validation recorded 46 Python tests, 93.56% Python coverage, 88.14% web statement coverage, Playwright critical-flow coverage, reversible migrations, zero schema drift, and no API/worker errors in the validated run.
- The evidence-export branch adds a deterministic JSON bundle for completed simulations, including immutable input/result/impact/risk checksums, latest approval, release-gate result, an export checksum, attachment metadata, and an `evidence.exported` audit event.
- Export authorization is enforced for same-tenant reviewers, release approvers, and auditors; analysts are denied and cross-tenant simulation identifiers remain non-enumerating.
- Branch validation currently records 46 passing Python tests with 93.56% coverage, 3 passing web component tests, 2 passing Chromium workflows with real JSON downloads, valid 11-operation OpenAPI, and successful web lint, type checking, and production build.

## Current limits

- The development identity endpoint is not production authentication or OIDC.
- Isolation evidence covers implemented API/UI paths, including completed-simulation JSON export, only; every future reproduction, artifact, webhook, metrics, and operator path must be protected or disabled.
- Only the deterministic rounding-rule family and synthetic data packs are supported.
- Hosted deployment, secret management, recovery, rollback, operational alerts, resource limits, SBOM/release artifacts, and measured reference-profile performance do not yet have pilot exit evidence.

## Next milestone

The approved implementation baseline is [`docs/pilot-readiness-plan.md`](pilot-readiness-plan.md). Work is ordered as:

1. Review and merge the completed-simulation evidence export, then keep unfinished pilot surfaces disabled.
2. Production OIDC with development identities disabled outside local mode.
3. Resource limits, rate controls, observability, and alerting.
4. Reproducible deployment, external secret storage, backup/restore, and rollback.
5. Security, isolation, recovery, performance, and usability acceptance.
6. Immutable `v0.4.0-pilot.1` release after every gate passes.

## Owner decisions required

Hosting and budget, domain/TLS ownership, OIDC provider, pilot identities and roles, backup retention and RPO/RTO, availability/support window, and hosted visibility remain required before deployment work can close.
