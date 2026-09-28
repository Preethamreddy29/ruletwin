# RuleTwin

RuleTwin is a deterministic, tenant-aware change-impact simulator for proposed business-rule changes. It replays synthetic events through baseline and candidate rule versions, compares outcomes, applies a versioned risk policy, and produces reproducible approval evidence.

> **Current state:** Phase 1 is merged. Phase 2 engineering-foundation implementation and local Docker/PostgreSQL validation pass on `codex/phase2-engineering-foundation`; formal Phase 2 closure is waiting for a clean GitHub Actions run after commit and push.

## Product boundary

RuleTwin is not a billing engine, no-code rules platform, payment system, feature-flag service, or AI rule generator. It uses fictional NovaBill scenarios and synthetic data only.

The portfolio index and governing sources are maintained in the sibling `enterprise-rule-intelligence` repository. This repository owns RuleTwin's product contracts, architecture decisions, security model, and eventual independently deployable runtime.

## Current milestone

Phase 2 establishes the FastAPI service boundary, React/Vite readiness shell, PostgreSQL migrations, transaction and outbox-worker scaffolding, structured health/metrics signals, non-root containers, deterministic synthetic seed, quality tooling and CI. Product rule execution and simulation remain Phase 3 scope.

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

## License

Apache License 2.0. See [`LICENSE`](LICENSE).
