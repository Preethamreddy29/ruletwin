# RuleTwin

RuleTwin is a deterministic, tenant-aware change-impact simulator for proposed business-rule changes. It replays synthetic events through baseline and candidate rule versions, compares outcomes, applies a versioned risk policy, and produces reproducible approval evidence.

> **Current state:** The controlled-pilot foundation includes deterministic simulation and evidence export, tenant-aware authorization, OIDC verification, Auth0-compatible authorization-code/PKCE browser flows, bounded resource controls, operations/alerting, deployment/recovery automation, and supply-chain evidence generation. RuleTwin is suitable for synthetic local demonstrations; it is not yet approved for an externally hosted pilot or production use.

## Product boundary

RuleTwin is not a billing engine, no-code rules platform, payment system, feature-flag service, or AI rule generator. It uses fictional NovaBill and Brightline scenarios with synthetic data only.

The portfolio index and governing sources are maintained in the sibling `enterprise-rule-intelligence` repository. This repository owns RuleTwin's product contracts, architecture decisions, security model, and independently deployable runtime.

## What works now

- Deterministic baseline-versus-candidate replay for a versioned rounding-rule family.
- Two fictional tenants with PostgreSQL-resolved memberships and role-separated analyst, reviewer, release-approver, and auditor actions.
- Non-enumerating tenant/object authorization, fail-closed risk decisions, checksum-bound approval and release gates.
- Recoverable worker/outbox execution, append-only audit evidence, and deterministic JSON evidence export.
- Provider-neutral OIDC token verification plus an Auth0-compatible browser PKCE/login/logout implementation.
- Request, replay-dataset, per-tenant queue, worker timeout/retry, and pilot worker-concurrency controls.
- Aggregate database/queue/worker health metrics, eight actionable Prometheus alerts, deterministic alert tests, and an incident runbook.
- An HTTPS-only pilot topology with immutable-image enforcement, mounted secrets, automated migrations, deployment records, checksum-bound backups, and isolated restore verification.
- API/web SPDX SBOMs, high/critical vulnerability gates, checksum-bound evidence manifests, and retained preflight workflow artifacts.
- FastAPI, React/TypeScript, PostgreSQL, Docker Compose, OpenAPI, migrations, and protected CI validation.

## Current milestone

The next milestone is controlled-pilot readiness. Its scope, exclusions, required evidence, and user decisions are defined in [`docs/pilot-readiness-plan.md`](docs/pilot-readiness-plan.md). Actual Auth0 tenant configuration and invited-user evidence, complete exposed-surface isolation, hosted deployment/log/notification evidence, provider secret-store evidence, hosted recovery drills, protected preflight artifacts, and measured performance/accessibility evidence remain required before an externally hosted pilot.

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
- [`docs/validation/pilot-resource-safety-validation.md`](docs/validation/pilot-resource-safety-validation.md)
- [`docs/operations/pilot-incident-runbook.md`](docs/operations/pilot-incident-runbook.md)
- [`docs/validation/pilot-operations-validation.md`](docs/validation/pilot-operations-validation.md)
- [`docs/operations/pilot-deployment-recovery.md`](docs/operations/pilot-deployment-recovery.md)
- [`docs/validation/pilot-deployment-recovery-validation.md`](docs/validation/pilot-deployment-recovery-validation.md)
- [`docs/operations/pilot-release-evidence.md`](docs/operations/pilot-release-evidence.md)
- [`docs/validation/pilot-supply-chain-validation.md`](docs/validation/pilot-supply-chain-validation.md)

## Security and limitations

RuleTwin remains pre-release. The OIDC and browser integration code has not yet been validated against a configured hosted provider, development identities are permitted only in local mode, only implemented API/UI paths have executable tenant-isolation evidence, and only synthetic data is approved. See [`SECURITY.md`](SECURITY.md) and the pilot-readiness plan before deployment.

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
