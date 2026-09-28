[CmdletBinding()]
param([switch]$Integration)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo '.venv/Scripts/python.exe'
$envFile = Join-Path $repo '.env'
if (-not (Test-Path -LiteralPath $python)) {
    throw 'Missing .venv. Run ./scripts/dev.ps1 bootstrap first.'
}

function Invoke-Checked {
    param([scriptblock]$Action, [string]$Label)
    & $Action
    if ($LASTEXITCODE -ne 0) { throw "$Label failed with exit code $LASTEXITCODE." }
}

function Initialize-LocalIntegrationDatabase {
    if ($env:RULETWIN_TEST_DATABASE_URL) {
        if (-not $env:RULETWIN_DATABASE_URL) {
            $env:RULETWIN_DATABASE_URL = $env:RULETWIN_TEST_DATABASE_URL
        }
        return
    }
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw 'Docker is required when RULETWIN_TEST_DATABASE_URL is not configured.'
    }
    if (-not (Test-Path -LiteralPath $envFile)) {
        throw 'Missing .env. Run ./scripts/dev.ps1 up before integration checks.'
    }

    $settings = @{}
    Get-Content -LiteralPath $envFile | ForEach-Object {
        if ($_ -match '^([^#=]+)=(.*)$') {
            $settings[$matches[1].Trim()] = $matches[2].Trim()
        }
    }
    if (-not $settings['POSTGRES_TEST_PASSWORD']) {
        throw 'POSTGRES_TEST_PASSWORD is missing from .env.'
    }

    Invoke-Checked { docker compose --profile core up --detach postgres } 'Test PostgreSQL startup'
    $exists = docker compose exec -T postgres psql -U ruletwin_admin -d postgres -Atc `
        "select 1 from pg_database where datname='ruletwin_test';"
    if ($LASTEXITCODE -ne 0) { throw 'Test database inspection failed.' }
    if ($exists -ne '1') {
        Invoke-Checked {
            docker compose exec -T postgres createdb -U ruletwin_admin -O ruletwin_test ruletwin_test
        } 'Test database creation'
    }

    $password = [uri]::EscapeDataString($settings['POSTGRES_TEST_PASSWORD'])
    $testUrl = "postgresql+psycopg://ruletwin_test:${password}@127.0.0.1:5432/ruletwin_test"
    $env:RULETWIN_DATABASE_URL = $testUrl
    $env:RULETWIN_TEST_DATABASE_URL = $testUrl
}

Push-Location $repo
try {
    Invoke-Checked { & $python -m ruff format --check . } 'Python format'
    Invoke-Checked { & $python -m ruff check . } 'Python lint'
    Invoke-Checked { & $python -m mypy } 'Python type check'
    Invoke-Checked { & $python scripts/validate_openapi.py } 'OpenAPI validation'
    Invoke-Checked { & $python scripts/secret_scan.py . } 'Secret scan'
    if ($Integration) {
        Initialize-LocalIntegrationDatabase
        Invoke-Checked { & $python scripts/test_migrations.py } 'Migration cycle'
        Invoke-Checked { & $python -m pytest } 'Python tests'
    } else {
        Invoke-Checked { & $python -m pytest -m 'not integration' } 'Python tests'
    }
    Invoke-Checked { pnpm format:check } 'Web format'
    Invoke-Checked { pnpm lint } 'Web lint'
    Invoke-Checked { pnpm typecheck } 'Web type check'
    Invoke-Checked { pnpm test } 'Web tests'
    Invoke-Checked { pnpm build } 'Web build'
    if (Get-Command docker -ErrorAction SilentlyContinue) {
        docker compose --profile full config --quiet
    } else {
        Write-Warning 'Docker is unavailable; Compose and container checks were not run locally.'
    }
} finally {
    Pop-Location
}
