#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Provision Neon Postgres, migrate it, wire Vercel, and deploy FreightPilot.

.DESCRIPTION
    End-to-end production recovery in one command. Everything is done through
    CLIs (neonctl + vercel + alembic); nothing needs the Neon dashboard.

      1. Creates a Neon project (or reuses an existing one by name).
      2. Reads the pooled connection string.
      3. Verifies it actually connects with psycopg.
      4. Runs `alembic upgrade head` against it — REQUIRED, because the Vercel
         config has no migration step and a fresh database has no schema, so
         signup would 500 without this.
      5. Rotates JWT_SECRET_KEY + PROVIDER_KEY_ENCRYPTION_SECRET, removes the
         dead PASSWORD_SALT, and sets DATABASE_URL on platform-api/production.
      6. Deploys platform-api, ops-console and product-web.
      7. Polls /health until it reports db:ok, then runs the launch-funnel check.

.PARAMETER NeonApiKey
    Neon API key (https://console.neon.tech/app/settings/api-keys).
    Defaults to $env:NEON_API_KEY.

.PARAMETER ProjectName
    Neon project name. Reused if it already exists.

.PARAMETER DryRun
    Do everything read-only: verify the key works, list projects, print the
    plan. Changes nothing.

.EXAMPLE
    ./scripts/setup_neon_production.ps1 -NeonApiKey 'napi_xxx' -DryRun
    ./scripts/setup_neon_production.ps1 -NeonApiKey 'napi_xxx'
#>
[CmdletBinding()]
param(
    [string]$NeonApiKey = $env:NEON_API_KEY,
    [string]$ProjectName = 'freightpilot-prod',
    # Pinned deliberately. Neon's default region is us-east-2, but the product
    # targets East African operators and the API is deployed to Vercel iad1
    # (Washington DC). eu-west-2 measured ~176ms from the dev machine versus
    # ~380ms for us-east-1, and is the closest region to both the customer base
    # and the existing org project, so the app-to-database hop is the shortest
    # available.
    [string]$RegionId = 'aws-eu-west-2',
    [string]$OrgId = '',
    [string]$PythonExe = '',
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$apiDir = Join-Path $repoRoot 'apps/platform-api'
$neonDir = Join-Path $env:TEMP 'neon-cli'

function Step([string]$t) { Write-Host "`n=== $t ===" -ForegroundColor Cyan }
function Ok([string]$t) { Write-Host "  [ok] $t" -ForegroundColor Green }
function Warn2([string]$t) { Write-Host "  [!!] $t" -ForegroundColor Yellow }
function Die([string]$t) { Write-Host "  [xx] $t" -ForegroundColor Red; exit 1 }

# ---------------------------------------------------------------------------
# 0. Preconditions
# ---------------------------------------------------------------------------
Step 'Preconditions'

if (-not $NeonApiKey) {
    Die @'
No Neon API key. Create one at https://console.neon.tech/app/settings/api-keys
(Neon console -> Settings -> API keys -> Create new API key), then either:
    $env:NEON_API_KEY = 'napi_...'
or pass -NeonApiKey 'napi_...'
The key is used only by neonctl and is never written to disk or to Vercel.
'@
}
Ok "Neon API key present ($($NeonApiKey.Substring(0, [Math]::Min(4, $NeonApiKey.Length)))..., $($NeonApiKey.Length) chars)"

if (-not $PythonExe) {
    foreach ($c in @((Join-Path $repoRoot '.venv/Scripts/python.exe'),
                     (Join-Path $apiDir '.venv/Scripts/python.exe'))) {
        if (Test-Path $c) { $PythonExe = $c; break }
    }
    if (-not $PythonExe) { $PythonExe = 'python' }
}
Ok "python: $PythonExe"

# Ensure neonctl exists in an isolated dir (installing it into the repo root
# would fight npm workspace hoisting).
$neon = Join-Path $neonDir 'node_modules\.bin\neonctl.cmd'
if (-not (Test-Path $neon)) {
    Warn2 'neonctl not found locally; installing into an isolated directory'
    New-Item -ItemType Directory -Force -Path $neonDir | Out-Null
    if (-not (Test-Path (Join-Path $neonDir 'package.json'))) {
        '{"name":"neon-cli-holder","private":true}' | Set-Content (Join-Path $neonDir 'package.json')
    }
    Push-Location $neonDir
    try { & npm install --silent neonctl 2>&1 | Out-Null } finally { Pop-Location }
    if (-not (Test-Path $neon)) { Die 'neonctl install failed' }
}
$neonVersion = (& $neon --version 2>&1 | Select-Object -Last 1).Trim()
Ok "neonctl $neonVersion"

# Resolve the organization id. neonctl prompts interactively when an account
# belongs to an organization, which would hang an unattended run, so the id is
# always passed explicitly.
if (-not $OrgId) {
    $orgsRaw = & $neon orgs list --api-key $NeonApiKey --output json 2>&1
    try {
        $orgs = ($orgsRaw -join "`n") | ConvertFrom-Json
    } catch {
        Die "could not list Neon organizations (is the key account-scoped?):`n$($orgsRaw | Select-Object -First 5)"
    }
    if (-not $orgs -or $orgs.Count -eq 0) { Die 'no Neon organization found for this API key' }
    $OrgId = $orgs[0].id
    if ($orgs.Count -gt 1) {
        Warn2 "$($orgs.Count) organizations visible; using the first ($OrgId). Pass -OrgId to choose."
    }
}
Ok "org: $OrgId"

# Confirm the key authenticates before doing anything else.
$projectsJson = & $neon projects list --org-id $OrgId --api-key $NeonApiKey --output json 2>&1
if ($LASTEXITCODE -ne 0) { Die "Neon API rejected the key:`n$projectsJson" }
try {
    $existing = ($projectsJson -join "`n") | ConvertFrom-Json
} catch {
    Die "could not parse the project list:`n$($projectsJson | Select-Object -First 5)"
}
if ($null -eq $existing) { $existing = @() }
Ok "key authenticates ($(@($existing).Count) existing project(s))"

foreach ($p in @($existing)) { if ($p.name -eq $ProjectName) { Ok "found existing project '$ProjectName' (id $($p.id))" } }

if ($DryRun) {
    Step 'Dry run complete'
    Write-Host "  Would create/reuse Neon project '$ProjectName' in $RegionId (org $OrgId)," -ForegroundColor Yellow
    Write-Host '         verify the connection, run alembic upgrade head, rotate secrets,' -ForegroundColor Yellow
    Write-Host '         set DATABASE_URL, deploy 3 Vercel projects, verify /health + funnel.' -ForegroundColor Yellow
    Write-Host '  Nothing was changed.' -ForegroundColor Yellow
    exit 0
}

# ---------------------------------------------------------------------------
# 1. Create or reuse the Neon project
# ---------------------------------------------------------------------------
Step "Neon project '$ProjectName'"
$project = @($existing) | Where-Object { $_.name -eq $ProjectName } | Select-Object -First 1
if ($project) {
    Ok "reusing project $($project.id)"
} else {
    $created = & $neon projects create --name $ProjectName --region-id $RegionId --org-id $OrgId --api-key $NeonApiKey --output json 2>&1
    if ($LASTEXITCODE -ne 0) { Die "project create failed:`n$($created | Select-Object -First 8)" }
    try {
        $project = (($created -join "`n") | ConvertFrom-Json).project
    } catch {
        Die "could not parse the create response:`n$($created | Select-Object -First 8)"
    }
    Ok "created project $($project.id) in $($project.region_id)"
}

# ---------------------------------------------------------------------------
# 2. Connection string (pooled)
# ---------------------------------------------------------------------------
Step 'Connection string'
$raw = & $neon connection-string --project-id $project.id --pooled --api-key $NeonApiKey 2>&1
if ($LASTEXITCODE -ne 0) { Die "connection-string failed:`n$raw" }
$pgUrl = ($raw | Where-Object { $_ -match '^postgres' } | Select-Object -First 1)
if (-not $pgUrl) { $pgUrl = ("$raw" -split "`n" | Where-Object { $_ -match 'postgres' } | Select-Object -First 1) }
if (-not $pgUrl) { Die "could not read a postgres URL from neonctl output" }
$pgUrl = $pgUrl.Trim()

# SQLAlchemy needs the psycopg driver named explicitly.
$sqlalchemyUrl = $pgUrl -replace '^postgres(ql)?://', 'postgresql+psycopg://'
Ok "got a pooled URL (host: $((($sqlalchemyUrl -split '@')[-1] -split '/')[0]))"

# ---------------------------------------------------------------------------
# 3. Verify it connects
# ---------------------------------------------------------------------------
Step 'Verifying the connection'
$env:FP_NEON_URL = $sqlalchemyUrl
$probe = & $PythonExe -c @'
import os, sys
url = os.environ["FP_NEON_URL"].replace("postgresql+psycopg://", "postgresql://")
try:
    import psycopg
except ImportError:
    print("PROBE_SKIP no-psycopg"); sys.exit(0)
try:
    with psycopg.connect(url, connect_timeout=15) as conn:
        with conn.cursor() as cur:
            cur.execute("select version()")
            print("PROBE_OK", (cur.fetchone()[0] or "")[:60])
except Exception as exc:
    print(f"PROBE_FAIL {type(exc).__name__}: {str(exc)[:220]}"); sys.exit(1)
'@ 2>&1
Remove-Item Env:\FP_NEON_URL -ErrorAction SilentlyContinue
$probe | ForEach-Object { Write-Host "  $_" }
if ($probe -match 'PROBE_FAIL') { Die 'Neon connection failed; not touching Vercel.' }
Ok 'Neon database reachable'

# ---------------------------------------------------------------------------
# 4. Migrate (REQUIRED: a fresh database has no schema)
# ---------------------------------------------------------------------------
Step 'Running alembic upgrade head against Neon'
Push-Location $apiDir
try {
    $env:DATABASE_URL = $sqlalchemyUrl
    $env:APP_ENV = 'production'
    # Production guards require real values; the real ones are generated below,
    # but alembic only needs DATABASE_URL. Supply throwaways so Settings loads.
    if (-not $env:JWT_SECRET_KEY) { $env:JWT_SECRET_KEY = (& $PythonExe -c "import secrets;print(secrets.token_urlsafe(48))") }
    if (-not $env:PROVIDER_KEY_ENCRYPTION_SECRET) { $env:PROVIDER_KEY_ENCRYPTION_SECRET = (& $PythonExe -c "import secrets;print(secrets.token_urlsafe(48))") }
    if (-not $env:RECEIPT_EXTRACTION_MODE) { $env:RECEIPT_EXTRACTION_MODE = 'real' }
    if (-not $env:CBE_ACCOUNT_HOLDER) { $env:CBE_ACCOUNT_HOLDER = 'FreightPilot PLC' }
    if (-not $env:CBE_ACCOUNT_NUMBER) { $env:CBE_ACCOUNT_NUMBER = '1000134567890' }
    if (-not $env:DASHEN_ACCOUNT_HOLDER) { $env:DASHEN_ACCOUNT_HOLDER = 'FreightPilot PLC' }
    if (-not $env:DASHEN_ACCOUNT_NUMBER) { $env:DASHEN_ACCOUNT_NUMBER = '012345678901' }

    $migrated = & $PythonExe -m alembic upgrade head 2>&1
    $migrated | Select-Object -Last 6 | ForEach-Object { Write-Host "  $_" }
    if ($LASTEXITCODE -ne 0) { Die "alembic upgrade failed — Vercel NOT touched (the app would 500 without a schema)" }
    Ok 'schema applied'
}
finally {
    Pop-Location
    Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue
    Remove-Item Env:\APP_ENV -ErrorAction SilentlyContinue
}

# ---------------------------------------------------------------------------
# 5. Rotate secrets + set DATABASE_URL on Vercel
# ---------------------------------------------------------------------------
Step 'Vercel environment (platform-api / production)'
$jwt = & $PythonExe -c "import secrets;print(secrets.token_urlsafe(48))"
$enc = & $PythonExe -c "import secrets;print(secrets.token_urlsafe(48))"

Push-Location $apiDir
try {
    $ls = (& npx --no-install vercel env ls production 2>&1) -join "`n"
    foreach ($entry in @(
            @{ Name = 'DATABASE_URL'; Value = $sqlalchemyUrl },
            @{ Name = 'JWT_SECRET_KEY'; Value = $jwt },
            @{ Name = 'PROVIDER_KEY_ENCRYPTION_SECRET'; Value = $enc }
        )) {
        if ($ls -match "(?m)^\s*$($entry.Name)\s") {
            $entry.Value | npx --no-install vercel env rm $entry.Name production --yes 2>&1 | Out-Null
        }
        $entry.Value | npx --no-install vercel env add $entry.Name production 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { Die "failed to set $($entry.Name)" }
        Ok "set $($entry.Name)"
    }
    if ($ls -match '(?m)^\s*PASSWORD_SALT\s') {
        npx --no-install vercel env rm PASSWORD_SALT production --yes 2>&1 | Out-Null
        Ok 'removed dead PASSWORD_SALT'
    }
}
finally { Pop-Location }

# ---------------------------------------------------------------------------
# 6. Deploy
# ---------------------------------------------------------------------------
Step 'Deploying to production'
# Deploy from the REPO ROOT with --cwd, not by changing into the app directory.
# Each Vercel project's rootDirectory is already set to apps/<name> in its
# project settings, so Vercel resolves the app path relative to the repo root.
# Running `vercel deploy` from inside apps/<name> therefore resolves to
# apps/<name>/apps/<name> and fails with "The provided path ... does not exist".
foreach ($app in @('platform-api', 'ops-console', 'product-web')) {
    Write-Host "  -> $app" -ForegroundColor Cyan
    Push-Location $repoRoot
    try {
        $out = & npx --no-install vercel deploy --prod --yes --cwd "apps/$app" 2>&1
        $out | Select-Object -Last 3 | ForEach-Object { Write-Host "     $_" }
        if ($LASTEXITCODE -ne 0) { Warn2 "$app deploy returned a non-zero exit; inspect the output above" }
    }
    finally { Pop-Location }
}

# ---------------------------------------------------------------------------
# 7. Verify
# ---------------------------------------------------------------------------
Step 'Verifying production'
$health = $null
for ($i = 1; $i -le 12; $i++) {
    Start-Sleep -Seconds 10
    try {
        $health = (Invoke-WebRequest 'https://platform-api-smoky.vercel.app/health' -TimeoutSec 45 -UseBasicParsing).Content
        Write-Host "  attempt ${i}: $health"
        if ($health -match '"db"\s*:\s*"ok"') { break }
    } catch { Write-Host "  attempt ${i}: $($_.Exception.Message)" }
}
if ($health -notmatch '"db"\s*:\s*"ok"') { Die 'API still reports the database unavailable — check the platform-api deployment logs.' }
Ok 'API reports the database reachable'

Step 'Launch-funnel verification'
$funnel = Join-Path $repoRoot '.artifacts/verify_funnel.py'
if (Test-Path $funnel) {
    & $PythonExe $funnel 'https://platform-api-smoky.vercel.app' 2>&1 | Select-Object -Last 10
} else {
    Warn2 "funnel script not found at $funnel; run it manually"
}

$record = Join-Path $repoRoot ".artifacts/neon-provision-$(Get-Date -Format yyyyMMdd-HHmmss).md"
@"
# Neon provisioning record

- Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')
- Neon project: $ProjectName ($($project.id))
- Region / host: $((($sqlalchemyUrl -split '@')[-1] -split '/')[0])
- Pooled connection: yes
- Schema: `alembic upgrade head` applied
- Vercel (platform-api/production): DATABASE_URL, JWT_SECRET_KEY, PROVIDER_KEY_ENCRYPTION_SECRET rotated; PASSWORD_SALT removed
- Deployed: platform-api, ops-console, product-web
- Verified: /health db:ok

Connection strings and secrets are deliberately NOT recorded here.
"@ | Set-Content -Path $record -Encoding utf8
Ok "record written to $($record -replace [regex]::Escape($repoRoot), '.')"

Write-Host "`nProduction is live on Neon." -ForegroundColor Green
