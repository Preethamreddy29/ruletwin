[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('bootstrap', 'up', 'down', 'logs', 'seed', 'reset', 'status')]
    [string]$Command = 'status'
)

$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
$python = Join-Path $repo '.venv/Scripts/python.exe'
$envFile = Join-Path $repo '.env'

function New-LocalEnvironment {
    if (Test-Path -LiteralPath $envFile) {
        if (-not (Select-String -LiteralPath $envFile -Pattern '^RULETWIN_JWT_SECRET=' -Quiet)) {
            $jwt = ([Guid]::NewGuid().ToString('N') + [Guid]::NewGuid().ToString('N'))
            Add-Content -LiteralPath $envFile -Value "RULETWIN_JWT_SECRET=${jwt}" -Encoding utf8NoBOM
            Write-Host 'Added a generated development-only JWT signing secret to .env.'
        }
        return
    }
    $admin = [Guid]::NewGuid().ToString('N')
    $app = [Guid]::NewGuid().ToString('N')
    $test = [Guid]::NewGuid().ToString('N')
    $jwt = ([Guid]::NewGuid().ToString('N') + [Guid]::NewGuid().ToString('N'))
    @"
RULETWIN_ENVIRONMENT=dev
RULETWIN_DATABASE_URL=postgresql+psycopg://ruletwin_app:${app}@localhost:5432/ruletwin
RULETWIN_LOG_LEVEL=INFO
RULETWIN_CORS_ORIGINS=http://localhost:5173,http://localhost:8080
RULETWIN_JWT_SECRET=${jwt}
POSTGRES_DB=ruletwin
POSTGRES_USER=ruletwin_admin
POSTGRES_PASSWORD=${admin}
POSTGRES_APP_PASSWORD=${app}
POSTGRES_TEST_PASSWORD=${test}
"@ | Set-Content -LiteralPath $envFile -Encoding utf8NoBOM
    Write-Host 'Created local .env with generated development-only credentials.'
}

Push-Location $repo
try {
    switch ($Command) {
        'bootstrap' {
            New-LocalEnvironment
            if (-not (Test-Path -LiteralPath $python)) { py -3.12 -m venv .venv }
            & $python -m pip install --upgrade pip
            & $python -m pip install -e '.[dev]'
            pnpm install
        }
        'up' {
            if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
                throw 'Docker with Compose v2 is required. Install/start Docker Desktop, then retry.'
            }
            New-LocalEnvironment
            docker compose --profile core up --build --detach
            docker compose --profile core ps
        }
        'down' { docker compose --profile full down }
        'logs' { docker compose --profile core logs --follow --tail 100 }
        'seed' { docker compose --profile core run --rm api ruletwin-seed }
        'reset' {
            if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
                throw 'Docker with Compose v2 is required. Install/start Docker Desktop, then retry.'
            }
            New-LocalEnvironment
            Write-Host 'Resetting RuleTwin local synthetic data and rebuilding the core demo stack.'
            docker compose --profile full down --volumes --remove-orphans
            if ($LASTEXITCODE -ne 0) { throw 'RuleTwin stack reset failed.' }
            docker compose --profile core up --build --detach
            if ($LASTEXITCODE -ne 0) { throw 'RuleTwin stack startup failed after reset.' }
            docker compose --profile core ps
        }
        'status' {
            git status --short
            if (Get-Command docker -ErrorAction SilentlyContinue) {
                docker compose --profile full ps
            }
        }
    }
} finally {
    Pop-Location
}
