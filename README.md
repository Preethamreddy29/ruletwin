# RuleTwin

RuleTwin is a deterministic, tenant-aware change-impact simulator for proposed business-rule changes. It replays synthetic events through baseline and candidate rule versions, compares outcomes, applies a versioned risk policy, and produces reproducible approval evidence.

> **Current state:** Phase 2 is merged. Phase 3 implements and locally validates the first deterministic rounding-rule vertical slice on `codex/phase3-first-vertical-slice`; clean-runner CI remains manual post-push evidence.

## Product boundary

RuleTwin is not a billing engine, no-code rules platform, payment system, feature-flag service, or AI rule generator. It uses fictional NovaBill scenarios and synthetic data only.

The portfolio index and governing sources are maintained in the sibling `enterprise-rule-intelligence` repository. This repository owns RuleTwin's product contracts, architecture decisions, security model, and eventual independently deployable runtime.

## Current milestone

Phase 3 provides one complete NovaBill Sandbox workflow: propose an immutable rounding rule, replay a versioned 100-event synthetic dataset against baseline and candidate rules, inspect deterministic financial impact and fail-closed risk, then bind a separate approver and release gate to the exact result checksum. PostgreSQL leases recover claimed work, duplicate requests are idempotent, protected transitions are audited, and Playwright verifies both allow and block paths.

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

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
