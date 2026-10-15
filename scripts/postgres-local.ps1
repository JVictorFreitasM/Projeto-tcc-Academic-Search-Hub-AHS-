param(
    [ValidateSet("init", "start", "stop", "status")]
    [string]$Action = "start"
)

$ErrorActionPreference = "Stop"
$projectRoot = [System.IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
$postgresRoot = [System.IO.Path]::GetFullPath((Join-Path $projectRoot ".postgres"))
$dataDirectory = [System.IO.Path]::GetFullPath((Join-Path $postgresRoot "data"))
$logFile = Join-Path $postgresRoot "postgres.log"
$postgresBin = "C:\Program Files\PostgreSQL\18\bin"
$port = 5434

if (-not $postgresRoot.StartsWith($projectRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Diretório PostgreSQL fora do projeto: $postgresRoot"
}

foreach ($program in @("initdb.exe", "pg_ctl.exe", "pg_isready.exe", "psql.exe", "createdb.exe")) {
    if (-not (Test-Path -LiteralPath (Join-Path $postgresBin $program))) {
        throw "PostgreSQL 18 não encontrado em $postgresBin"
    }
}

function Test-LocalPostgres {
    & (Join-Path $postgresBin "pg_isready.exe") -h 127.0.0.1 -p $port -U postgres -d postgres *> $null
    return $LASTEXITCODE -eq 0
}

function Start-LocalPostgres {
    if (Test-LocalPostgres) {
        return
    }
    if (-not (Test-Path -LiteralPath (Join-Path $dataDirectory "PG_VERSION"))) {
        throw "Instância ainda não inicializada. Rode: scripts/postgres-local.ps1 init"
    }
    & (Join-Path $postgresBin "pg_ctl.exe") start -D $dataDirectory -o "-p $port -h 127.0.0.1" -l $logFile -w
    if ($LASTEXITCODE -ne 0) {
        throw "Não foi possível iniciar o PostgreSQL local"
    }
}

function Initialize-LocalPostgres {
    New-Item -ItemType Directory -Force -Path $postgresRoot | Out-Null
    if (-not (Test-Path -LiteralPath (Join-Path $dataDirectory "PG_VERSION"))) {
        & (Join-Path $postgresBin "initdb.exe") -D $dataDirectory --encoding=UTF8 --locale=C --username=postgres --auth-local=trust --auth-host=trust
        if ($LASTEXITCODE -ne 0) {
            throw "Falha ao inicializar a instância PostgreSQL"
        }
    }
    Start-LocalPostgres

    $roleExists = & (Join-Path $postgresBin "psql.exe") -h 127.0.0.1 -p $port -U postgres -d postgres -tAc "SELECT 1 FROM pg_roles WHERE rolname='app_user'"
    if (("$roleExists").Trim() -ne "1") {
        & (Join-Path $postgresBin "psql.exe") -h 127.0.0.1 -p $port -U postgres -d postgres -v ON_ERROR_STOP=1 -c "CREATE ROLE app_user LOGIN CREATEDB"
    }
    foreach ($database in @("academic_search", "academic_search_test")) {
        $databaseExists = & (Join-Path $postgresBin "psql.exe") -h 127.0.0.1 -p $port -U postgres -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='$database'"
        if (("$databaseExists").Trim() -ne "1") {
            & (Join-Path $postgresBin "createdb.exe") -h 127.0.0.1 -p $port -U postgres -O app_user $database
        }
    }
    Write-Host "PostgreSQL local pronto em 127.0.0.1:$port"
}

switch ($Action) {
    "init" { Initialize-LocalPostgres }
    "start" { Start-LocalPostgres; Write-Host "PostgreSQL local em execução em 127.0.0.1:$port" }
    "stop" {
        if (Test-LocalPostgres) {
            & (Join-Path $postgresBin "pg_ctl.exe") stop -D $dataDirectory -m fast -w
        }
    }
    "status" {
        if (Test-LocalPostgres) { Write-Host "ready"; exit 0 }
        Write-Host "stopped"; exit 1
    }
}
