# Progress and Status

**As of:** 2026-10-24  
**Baseline:** `main` at `d64275f`  
**Milestone:** Controlled-pilot readiness baseline  
**Overall:** Phase 4A is merged and its protected clean-runner CI passed. RuleTwin is suitable for a synthetic local demonstration. It is not approved for an externally hosted pilot or real data.

## Completed evidence

- Phase 3 first vertical slice merged through PR #13.
- Phase 4A multi-tenant authorization merged through PR #18 as `cffdb30`.
- Phase 4A pull-request and post-merge workflows passed all five protected CI checks.
- Main CI passed again at `d64275f` after the Gitleaks action upgrade.
- Two fictional tenants and four role-separated development personas per tenant are implemented.
- PostgreSQL-resolved membership, tenant/object authorization, non-enumerating cross-tenant denial, deterministic replay, fail-closed risk decisions, checksum-bound approval, release gates, outbox recovery, and audit evidence have executable coverage.
- Local Phase 4A validation recorded 46 Python tests, 93.56% Python coverage, 88.14% web statement coverage, Playwright critical-flow coverage, reversible migrations, zero schema drift, and no API/worker errors in the validated run.

## Current limits

- The development identity endpoint is not production authentication or OIDC.
- Isolation evidence covers implemented API/UI paths only; every future export, artifact, webhook, metrics, and operator path must be protected or disabled.
- Only the deterministic rounding-rule family and synthetic data packs are supported.
- Hosted deployment, secret management, recovery, rollback, operational alerts, resource limits, SBOM/release artifacts, and measured reference-profile performance do not yet have pilot exit evidence.

## Next milestone

The approved implementation baseline is [`docs/pilot-readiness-plan.md`](pilot-readiness-plan.md). Work is ordered as:

1. Evidence export and complete authorization of every pilot-visible surface.
2. Production OIDC with development identities disabled outside local mode.
3. Resource limits, rate controls, observability, and alerting.
4. Reproducible deployment, external secret storage, backup/restore, and rollback.
5. Security, isolation, recovery, performance, and usability acceptance.
6. Immutable `v0.4.0-pilot.1` release after every gate passes.

## Owner decisions required

Hosting and budget, domain/TLS ownership, OIDC provider, pilot identities and roles, backup retention and RPO/RTO, availability/support window, and hosted visibility remain required before deployment work can close.
