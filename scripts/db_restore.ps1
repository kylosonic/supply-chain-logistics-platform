param(
  [Parameter(Mandatory = $true)]
  [string]$InputFile
)

$ErrorActionPreference = "Stop"
$pgUser = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "postgres" }
$pgDb = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "supply_chain" }

if (-not (Test-Path $InputFile)) {
  throw "Input file not found: $InputFile"
}

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw "docker is not installed or not in PATH."
}

Write-Host "Restoring PostgreSQL backup from $InputFile ..."
Get-Content $InputFile | docker compose exec -T postgres psql -U $pgUser -d $pgDb
Write-Host "Restore completed."
