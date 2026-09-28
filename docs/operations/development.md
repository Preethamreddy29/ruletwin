# Local Development

## Prerequisites

- Python 3.12
- Node.js 22.20 and pnpm 10.18
- Docker Engine/Desktop with Compose v2
- Git 2.43 or newer

No real tenant, employer, credential or production data may be used.

## Bootstrap

From the repository root in PowerShell:

```powershell
./scripts/dev.ps1 bootstrap
```

This creates a repository-local `.venv`, installs Python and web dependencies, generates `.env` with local-only random credentials when absent, and preserves those credentials outside Git.

## Start and inspect

```powershell
./scripts/dev.ps1 up
./scripts/dev.ps1 status
./scripts/dev.ps1 logs
```

Endpoints:

- Web shell: `http://localhost:8080`
- API liveness: `http://localhost:8000/health/live`
- API readiness: `http://localhost:8000/health/ready`
- Version: `http://localhost:8000/version`
- Metrics: `http://localhost:8000/metrics`
- Development API documentation: `http://localhost:8000/docs`

Start Prometheus with the full profile when observability inspection is needed:

```powershell
docker compose --profile full up --build --detach
```

Prometheus is available at `http://localhost:9090`.

## Seed synthetic data

```powershell
./scripts/dev.ps1 seed
```

The command is deterministic and safe to rerun. It creates only the fictional NovaBill sandbox identity foundation.

## Checks

```powershell
./scripts/check.ps1
```

Integration and migration checks require PostgreSQL. With Docker running and the repository-local `.env` present, the command below starts PostgreSQL when necessary, creates only the isolated `ruletwin_test` database, runs the reversible migration cycle, and executes the full suite:

```powershell
./scripts/check.ps1 -Integration
```

CI supplies its own disposable PostgreSQL service. If `RULETWIN_TEST_DATABASE_URL` is already configured, the check script uses it instead of provisioning the local test database. The migration cycle refuses to operate on a database without `test` in its name.

## Stop

```powershell
./scripts/dev.ps1 down
```

Named volumes are retained. Deliberate volume deletion is a separate destructive action and is not part of normal shutdown.
