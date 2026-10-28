# RuleTwin

RuleTwin is a deterministic, tenant-aware change-impact simulator for proposed business-rule changes. It replays synthetic events through baseline and candidate rule versions, compares outcomes, applies a versioned risk policy, and produces reproducible approval evidence.

> **Current state:** Tenant authorization and deterministic evidence export are merged through PR #21 at `257e604`, with protected clean-runner CI passing. A provider-neutral OIDC verification foundation is awaiting merge in PR #22, and the dependent Auth0/PKCE browser integration is under validation. RuleTwin is a validated synthetic-data pilot candidate, not a production-ready service.

## Product boundary

RuleTwin is not a billing engine, no-code rules platform, payment system, feature-flag service, or AI rule generator. It uses fictional NovaBill and Brightline scenarios with synthetic data only.

The portfolio index and governing sources are maintained in the sibling `enterprise-rule-intelligence` repository. This repository owns RuleTwin's product contracts, architecture decisions, security model, and independently deployable runtime.

## Current milestone

The implemented workflow preserves deterministic simulation while adding two synthetic tenants, short-lived signed development identities, PostgreSQL-resolved memberships, role-separated analyst/reviewer/release-approver/auditor actions, object-level authorization, non-enumerating cross-tenant denial, and checksum-bound JSON evidence export.

The next milestone is controlled-pilot readiness. Its scope, exclusions, required evidence, and user decisions are defined in [`docs/pilot-readiness-plan.md`](docs/pilot-readiness-plan.md). The browser now has an authorization-code/PKCE implementation and tenant-scoped scenario discovery; actual Auth0 tenant configuration, invited-user provisioning evidence, full-surface isolation, recovery evidence, deployment automation, operational alerting, resource controls, and measured performance remain required before an externally hosted pilot.

## Run locally

Local setup and operation are documented in [`docs/operations/development.md`](docs/operations/development.md). After Docker Desktop and WSL are running:

```powershell
./scripts/dev.ps1 bootstrap
./scripts/dev.ps1 up
./scripts/check.ps1
```

The guided authorization demonstration is documented in [`docs/demo/phase4a-authorization-guide.md`](docs/demo/phase4a-authorization-guide.md).

## Evidence and design

Start with:

- [`docs/pilot-readiness-plan.md`](docs/pilot-readiness-plan.md)
- [`docs/implementation-plan.md`](docs/implementation-plan.md)
- [`docs/domain-model.md`](docs/domain-model.md)
- [`docs/product/requirements.md`](docs/product/requirements.md)
- [`docs/architecture/nfrs.md`](docs/architecture/nfrs.md)
- [`docs/data/data-model.md`](docs/data/data-model.md)
- [`docs/security/threat-model.md`](docs/security/threat-model.md)
- [`packages/contracts/openapi.json`](packages/contracts/openapi.json)
- [`docs/requirements-traceability.md`](docs/requirements-traceability.md)
- [`docs/progress.md`](docs/progress.md)
- [`docs/phase1-exit-audit.md`](docs/phase1-exit-audit.md)
- [`docs/validation/phase1-validation.md`](docs/validation/phase1-validation.md)
- [`docs/phase2-exit-audit.md`](docs/phase2-exit-audit.md)
- [`docs/validation/phase2-validation.md`](docs/validation/phase2-validation.md)
- [`docs/phase3-exit-audit.md`](docs/phase3-exit-audit.md)
- [`docs/validation/phase3-validation.md`](docs/validation/phase3-validation.md)
- [`docs/phase4a-exit-audit.md`](docs/phase4a-exit-audit.md)
- [`docs/validation/phase4a-validation.md`](docs/validation/phase4a-validation.md)
- [`docs/validation/pilot-oidc-foundation-validation.md`](docs/validation/pilot-oidc-foundation-validation.md)
- [`docs/operations/auth0-pilot.md`](docs/operations/auth0-pilot.md)
- [`docs/validation/pilot-auth0-integration-validation.md`](docs/validation/pilot-auth0-integration-validation.md)

## Security and limitations

RuleTwin remains pre-release. Development identities are local-only, the OIDC foundation is not a completed provider login integration, only implemented API/UI paths have executable tenant-isolation evidence, and only synthetic data is approved. See [`SECURITY.md`](SECURITY.md) and the pilot-readiness plan before deployment.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
