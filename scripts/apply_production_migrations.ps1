#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Apply pending Alembic migrations to the production Neon database.

.DESCRIPTION
    Needed because the Vercel project has no migration step: `vercel.json` only
    builds `api/index.py`, so a merged migration never reaches the database on its
    own. Every schema change must be applied here, BEFORE the code that depends on
    it is deployed — otherwise new columns are missing and the API 500s.

    This is deliberately narrow: it reads the connection string from Neon, checks
    the current revision, runs `alembic upgrade head`, and prints the resulting
    revision. It changes no Vercel configuration and deploys nothing.

.PARAMETER NeonApiKey
    Neon API key (https://console.neon.tech/app/settings/api-keys).
    Defaults to $env:NEON_API_KEY. Used only by neonctl; never written to disk.

.PARAMETER ProjectName
    Neon project name to migrate. Defaults to the production project.

.PARAMETER DryRun
    Report the current and target revision, then stop. Changes nothing.

.EXAMPLE
    ./scripts/apply_production_migrations.ps1 -DryRun
    ./scripts/apply_production_migrations.ps1
#>
[CmdletBinding()]
param(
    [string]$NeonApiKey = $env:NEON_API_KEY,
    [string]$ProjectName = 'freightpilot-prod',
    # neonctl prompts interactively when an account has more than one
    # organization, which hangs a non-interactive run. Passing the org explicitly
    # avoids the prompt; empty means "single-org account, no flag needed".
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

# neonctl writes spinners and ANSI colour codes around its output, so the raw
# stream is not valid JSON even with --output json. Strip the escapes and the
# leading banner, then hand the remainder to PowerShell's own parser -- which
# handles both a bare array and an object envelope correctly.
function ConvertFrom-NeonJson([object]$raw) {
    $text = ($raw | Out-String)
    $text = $text -replace "\x1B\[[0-9;?]*[ -/]*[@-~]", ''
    $text = $text -replace "\x1B[@-Z\\-_]", ''
    $start = -1
    foreach ($ch in @('[', '{')) {
        $i = $text.IndexOf($ch)
        if ($i -ge 0 -and ($start -lt 0 -or $i -lt $start)) { $start = $i }
    }
    if ($start -lt 0) { return $null }
    $json = $text.Substring($start).Trim()
    try { return ($json | ConvertFrom-Json) } catch { return $null }
}

Step 'Preflight'

if (-not $NeonApiKey) {
    Die @'
No Neon API key. Pass -NeonApiKey 'napi_...' or set $env:NEON_API_KEY.
Create one at https://console.neon.tech/app/settings/api-keys
The key is used only by neonctl and is never written to disk.
'@
}
Ok "Neon API key present ($($NeonApiKey.Substring(0, [Math]::Min(4, $NeonApiKey.Length)))..., $($NeonApiKey.Length) chars)"

if (-not $PythonExe) {
    foreach ($candidate in @(
        (Join-Path $apiDir '.venv-lockcheck/Scripts/python.exe'),
        (Join-Path $apiDir '.venv/Scripts/python.exe'),
        (Join-Path $repoRoot '.venv/Scripts/python.exe')
    )) {
        if (Test-Path $candidate) { $PythonExe = $candidate; break }
    }
}
if (-not $PythonExe -or -not (Test-Path $PythonExe)) {
    Die 'No Python interpreter with alembic found. Pass -PythonExe <path>.'
}
Ok "python: $PythonExe"

# 1. Isolate neonctl (installing it into the repo root has broken resolution
# before; setup_neon_production.ps1 uses the same isolated-dir pattern)
Step 'neonctl'
$neon = Join-Path $neonDir 'node_modules/.bin/neonctl.cmd'
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
Ok 'neonctl ready'

# 2. Locate the project and read its pooled connection string
Step "Neon project '$ProjectName'"
$orgArgs = @()
if ($OrgId) { $orgArgs = @('--org-id', $OrgId) }
$projectsRaw = & $neon projects list --api-key $NeonApiKey @orgArgs --output json 2>&1
if ($LASTEXITCODE -ne 0) { Die "projects list failed:`n$($projectsRaw | Select-Object -First 8)" }
$projects = ConvertFrom-NeonJson $projectsRaw
if (-not $projects) {
    # Most likely cause: neonctl asked which organization to use and got no
    # answer, so the account has several. Report that rather than a parse error.
    $peek = ($projectsRaw | Out-String)
    if ($peek -match 'organization would you like') {
        Die @'
neonctl prompted for an organization, which means this account has more than
one. Re-run with -OrgId, e.g.:

  Get the id from:  neonctl orgs list --api-key <key>
  ./scripts/apply_production_migrations.ps1 -OrgId org-xxxxx
'@
    }
    Die "could not parse the project list as JSON:`n$($peek.Substring(0, [Math]::Min(300, $peek.Length)))"
}
# neonctl has returned both a bare array and a {projects:[...]} envelope. The
# envelope test must be structural: on a bare array, `$projects.projects` uses
# PowerShell member enumeration and returns an array of nulls -- which is TRUTHY,
# so a naive `if ($projects.projects)` replaces good data with nulls.
if ($projects -isnot [System.Array] -and $projects.PSObject.Properties['projects']) {
    $projects = $projects.projects
}

if ($env:FP_MIGRATE_DEBUG) {
    Write-Host "  [dbg] parsed type : $($projects.GetType().FullName)"
    Write-Host "  [dbg] parsed count: $(@($projects).Count)"
    for ($i = 0; $i -lt @($projects).Count; $i++) {
        $item = @($projects)[$i]
        if ($null -eq $item) { Write-Host "  [dbg] item[$i] is NULL"; continue }
        Write-Host "  [dbg] item[$i] name: '$($item.name)' id: '$($item.id)'"
    }
}

# Match by explicit comparison rather than Where-Object on a property, which
# silently yields nothing here (returning an empty roster and a confusing
# "not found" message instead of a parse failure).
$project = $null
$seen = @()
foreach ($candidate in @($projects)) {
    if ($null -eq $candidate) { continue }
    $candidateName = [string]$candidate.name
    if (-not $candidateName -and $candidate.PSObject.Properties['name']) {
        $candidateName = [string]$candidate.PSObject.Properties['name'].Value
    }
    $seen += $candidateName
    if ($candidateName -eq $ProjectName) { $project = $candidate; break }
}
if (-not $project) {
    Die "project '$ProjectName' not found. Visible projects: $($seen -join ', ')"
}
Ok "project $($project.id) in $($project.region_id)"

$raw = & $neon connection-string --project-id $project.id --pooled --api-key $NeonApiKey @orgArgs 2>&1
if ($LASTEXITCODE -ne 0) { Die "connection-string failed:`n$raw" }
$pgUrl = ($raw | Where-Object { $_ -match '^postgres' } | Select-Object -First 1)
if (-not $pgUrl) { $pgUrl = ("$raw" -split "`n" | Where-Object { $_ -match 'postgres' } | Select-Object -First 1) }
if (-not $pgUrl) { Die 'could not read a postgres URL from neonctl output' }
$sqlalchemyUrl = $pgUrl.Trim() -replace '^postgres(ql)?://', 'postgresql+psycopg://'
Ok "pooled URL host: $((($sqlalchemyUrl -split '@')[-1] -split '/')[0])"

$env:DATABASE_URL = $sqlalchemyUrl

# 3. Current state
Step 'Current revision'
Push-Location $apiDir
try {
    $current = & $PythonExe -m alembic current 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) { Die "alembic current failed:`n$current" }
    $current = $current.Trim()
    Ok ($(if ($current) { $current } else { '<none — empty database>' }))

    $heads = & $PythonExe -m alembic heads 2>&1 | Out-String
    Ok "target: $($heads.Trim())"

    if ($DryRun) {
        Warn2 'DryRun: no migration applied.'
        exit 0
    }

    # 4. Apply
    Step 'Upgrade to head'
    $upgrade = & $PythonExe -m alembic upgrade head 2>&1 | Out-String
    if ($LASTEXITCODE -ne 0) { Die "alembic upgrade failed:`n$upgrade" }
    $upgrade.Trim() -split "`n" | Where-Object { $_.Trim() } | ForEach-Object { Write-Host "  $_" }

    Step 'Verified revision'
    $after = & $PythonExe -m alembic current 2>&1 | Out-String
    Ok ($after.Trim())
    Write-Host ''
    Ok 'Migration applied. Code that depends on it may now be deployed.'
} finally {
    Pop-Location
}
