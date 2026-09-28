# Contributing to RuleTwin

RuleTwin uses short-lived branches, Conventional Commits and pull requests into protected `main`.

## Prerequisites

- Python 3.12
- Node.js 22 and pnpm 10
- Docker Engine/Desktop with Compose v2
- Git 2.4x or newer

## Local setup

1. Copy `.env.example` to `.env` and provide local-only values. Never commit `.env`.
2. Run `./scripts/dev.ps1 bootstrap` from PowerShell.
3. Run `./scripts/dev.ps1 up` to start PostgreSQL, API, worker and web services.
4. Run `./scripts/check.ps1` before requesting review.

See [`docs/operations/development.md`](docs/operations/development.md) for commands and troubleshooting.

## Change requirements

- Keep tenant boundaries explicit in every repository/query contract.
- Add tests for failure and abuse behavior, not only the happy path.
- Update OpenAPI and compatibility notes for public-contract changes.
- Include forward migration and recovery notes for schema changes.
- Do not claim implemented security, reliability or performance without executable evidence.
