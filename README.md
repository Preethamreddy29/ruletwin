# RuleTwin

RuleTwin is a deterministic, tenant-aware change-impact simulator for proposed business-rule changes. It replays synthetic events through baseline and candidate rule versions, compares outcomes, applies a versioned risk policy, and produces reproducible approval evidence.

> **Current state:** Phase 3 is merged at `5a13a3e`. Phase 4A adds a locally validated multi-tenant authorization slice on `codex/phase4a-multitenant-authorization`; clean-runner CI remains pending until the branch is pushed and reviewed.

## Product boundary

RuleTwin is not a billing engine, no-code rules platform, payment system, feature-flag service, or AI rule generator. It uses fictional NovaBill scenarios and synthetic data only.

The portfolio index and governing sources are maintained in the sibling `enterprise-rule-intelligence` repository. This repository owns RuleTwin's product contracts, architecture decisions, security model, and eventual independently deployable runtime.

## Current milestone

Phase 4A preserves the deterministic rounding workflow while adding two synthetic tenants, short-lived signed development identities, PostgreSQL-resolved memberships, role-separated analyst/reviewer/release-approver/auditor actions, object-level authorization, and non-enumerating cross-tenant denial. The UI makes the identity and tenant boundary directly demonstrable while Playwright retains both allow and block release paths.

Local setup and operation are documented in [`docs/operations/development.md`](docs/operations/development.md). After Docker Desktop and WSL are running:

```powershell
./scripts/dev.ps1 bootstrap
./scripts/dev.ps1 up
./scripts/check.ps1
```

Start with:

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
- [`docs/demo/phase3-demo-guide.md`](docs/demo/phase3-demo-guide.md)
- [`docs/phase4a-exit-audit.md`](docs/phase4a-exit-audit.md)
- [`docs/validation/phase4a-validation.md`](docs/validation/phase4a-validation.md)
- [`docs/demo/phase4a-authorization-guide.md`](docs/demo/phase4a-authorization-guide.md)

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
