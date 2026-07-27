param(
  [string]$OutputFile = "backup.sql"
)

$ErrorActionPreference = "Stop"
$pgUser = if ($env:POSTGRES_USER) { $env:POSTGRES_USER } else { "postgres" }
$pgDb = if ($env:POSTGRES_DB) { $env:POSTGRES_DB } else { "supply_chain" }

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
  throw "docker is not installed or not in PATH."
}

Write-Host "Creating PostgreSQL backup to $OutputFile ..."
docker compose exec -T postgres pg_dump -U $pgUser -d $pgDb > $OutputFile
Write-Host "Backup completed: $OutputFile"
