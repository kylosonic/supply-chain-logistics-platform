#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Rotate the FreightPilot production secrets and redeploy the three Vercel projects.

.DESCRIPTION
    One command to close the "production database unreachable + pre-guard secrets"
    gap. It:

      1. Verifies the supplied database URL actually connects (fails fast otherwise).
      2. Generates fresh JWT_SECRET_KEY and PROVIDER_KEY_ENCRYPTION_SECRET values.
      3. Writes DATABASE_URL / JWT_SECRET_KEY / PROVIDER_KEY_ENCRYPTION_SECRET to
         the platform-api Vercel project (production).
      4. Removes the dead PASSWORD_SALT variable if present.
      5. Deploys platform-api, ops-console and product-web to production.
      6. Verifies /health reports db:ok and runs the launch-funnel check.

    Nothing is written to disk except a local rotation record under .artifacts/.
    Secret values are never echoed.

.PARAMETER DatabaseUrl
    The full SQLAlchemy/psycopg URL, e.g.
    postgresql+psycopg://user:password@ep-example-pooler.eu-west-2.aws.neon.tech/neondb?sslmode=require

.PARAMETER DryRun
    Verify connectivity and print the exact plan without changing anything.

.PARAMETER SkipConnectivityCheck
    Skip the local connectivity probe. Use only when this machine cannot reach the
    database (restricted network) but the deployment host can — Vercel will surface
    the real failure via GET /health, which this script checks at the end.

.EXAMPLE
    ./scripts/rotate_and_deploy.ps1 -DatabaseUrl 'postgresql+psycopg://...' -DryRun
    ./scripts/rotate_and_deploy.ps1 -DatabaseUrl 'postgresql+psycopg://...'
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$DatabaseUrl,

    [switch]$DryRun,

    [switch]$SkipConnectivityCheck,

    [string]$PythonExe = ''
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$apiDir = Join-Path $repoRoot 'apps/platform-api'

function Write-Step([string]$Text) { Write-Host "`n=== $Text ===" -ForegroundColor Cyan }
function Write-Ok([string]$Text) { Write-Host "  [ok] $Text" -ForegroundColor Green }
function Write-Warn2([string]$Text) { Write-Host "  [!!] $Text" -ForegroundColor Yellow }
function Write-Fail([string]$Text) { Write-Host "  [xx] $Text" -ForegroundColor Red }

# 0. Resolve a Python interpreter
if (-not $PythonExe) {
    $candidates = @(
        (Join-Path $repoRoot '.venv/Scripts/python.exe'),
        (Join-Path $repoRoot 'apps/platform-api/.venv/Scripts/python.exe')
    )
    foreach ($c in $candidates) { if (Test-Path $c) { $PythonExe = $c; break } }
    if (-not $PythonExe) { $PythonExe = 'python' }
}
Write-Step 'Environment'
Write-Ok "python: $PythonExe"
Write-Ok "repo:   $repoRoot"

# 1. Validate the supplied URL connects before touching anything
Write-Step 'Verifying the database URL connects'
if ($DatabaseUrl -notmatch '://') {
    Write-Fail 'DatabaseUrl does not look like a connection URL.'
    exit 2
}
$maskedUrl = $DatabaseUrl -replace '(?<=://)[^@]*@', '***@'
Write-Ok "target: $maskedUrl"

$env:FP_PROBE_URL = $DatabaseUrl
if ($SkipConnectivityCheck) {
    Write-Warn2 'Connectivity probe skipped by request; the post-deploy /health check is now the only verification.'
    $probe = 'PROBE_SKIP requested'
} else {
    $probe = & $PythonExe -c @'
import os, sys
url = os.environ["FP_PROBE_URL"].replace("postgresql+psycopg://", "postgresql://")
try:
    import psycopg
except ImportError:
    print("PROBE_SKIP no-psycopg")
    sys.exit(0)
try:
    with psycopg.connect(url, connect_timeout=10) as conn:
        with conn.cursor() as cur:
            cur.execute("select count(*) from information_schema.tables where table_schema='public'")
            tables = cur.fetchone()[0]
            cur.execute("select version()")
            print(f"PROBE_OK tables={tables} server={(cur.fetchone()[0] or '')[:40]}")
except Exception as exc:
    print(f"PROBE_FAIL {type(exc).__name__}: {str(exc)[:200]}")
    sys.exit(1)
'@ 2>&1
}
Remove-Item Env:\FP_PROBE_URL -ErrorAction SilentlyContinue
$probe | ForEach-Object { Write-Host "  $_" }

if ($probe -match 'PROBE_FAIL') {
    Write-Fail 'The database URL did not connect. Fix it before deploying — the NB-63 boot guards will abort startup anyway.'
    exit 3
}
if ($probe -match 'PROBE_SKIP') {
    Write-Warn2 'psycopg not installed locally; could not pre-verify the connection. Continuing.'
} else {
    Write-Ok 'database reachable'
}

# 2. Generate rotated secrets
Write-Step 'Generating rotated secrets'
$jwt = & $PythonExe -c "import secrets; print(secrets.token_urlsafe(48))"
$enc = & $PythonExe -c "import secrets; print(secrets.token_urlsafe(48))"
if ($jwt.Length -lt 32 -or $enc.Length -lt 32) { Write-Fail 'secret generation produced a short value'; exit 4 }
Write-Ok ("JWT_SECRET_KEY: {0} chars" -f $jwt.Length)
Write-Ok ("PROVIDER_KEY_ENCRYPTION_SECRET: {0} chars" -f $enc.Length)
Write-Warn2 'Rotating JWT invalidates all existing console sessions (expected, and acceptable for a fix).'

# 3. Apply to Vercel
Write-Step 'Vercel environment (platform-api / production)'
Push-Location $apiDir
try {
    $existing = (& npx --no-install vercel env ls production 2>&1) -join "`n"

    foreach ($entry in @(
            @{ Name = 'DATABASE_URL'; Value = $DatabaseUrl },
            @{ Name = 'JWT_SECRET_KEY'; Value = $jwt },
            @{ Name = 'PROVIDER_KEY_ENCRYPTION_SECRET'; Value = $enc }
        )) {
        if ($DryRun) {
            Write-Ok "would set $($entry.Name) (removing any existing value first)"
            continue
        }
        # Remove then re-add: `vercel env add` on an existing key is interactive.
        if ($existing -match "(?m)^\s*$($entry.Name)\s") {
            $entry.Value | npx --no-install vercel env rm $entry.Name production --yes 2>&1 | Out-Null
            Write-Ok "removed previous $($entry.Name)"
        }
        $entry.Value | npx --no-install vercel env add $entry.Name production 2>&1 | Out-Null
        if ($LASTEXITCODE -ne 0) { Write-Fail "failed to set $($entry.Name)"; exit 5 }
        Write-Ok "set $($entry.Name)"
    }

    if ($existing -match '(?m)^\s*PASSWORD_SALT\s') {
        if ($DryRun) { Write-Ok 'would remove dead PASSWORD_SALT' }
        else {
            npx --no-install vercel env rm PASSWORD_SALT production --yes 2>&1 | Out-Null
            Write-Ok 'removed dead PASSWORD_SALT'
        }
    }

    if ($DryRun) {
        Write-Step 'Dry run complete'
        Write-Host '  Nothing was changed. Re-run without -DryRun to apply.' -ForegroundColor Yellow
        Pop-Location
        exit 0
    }
}
finally { Pop-Location }

# 4. Deploy the three projects
Write-Step 'Deploying to production'
foreach ($app in @('platform-api', 'ops-console', 'product-web')) {
    Write-Host "  -> $app" -ForegroundColor Cyan
    $dir = Join-Path $repoRoot "apps/$app"
    Push-Location $dir
    try {
        $output = & npx --no-install vercel deploy --prod --yes 2>&1
        $output | Select-Object -Last 3 | ForEach-Object { Write-Host "     $_" }
        if ($LASTEXITCODE -ne 0) { Write-Warn2 "$app deploy returned a non-zero exit; inspect the output above" }
    }
    finally { Pop-Location }
}

# 5. Verify
Write-Step 'Verifying production'
$health = $null
for ($attempt = 1; $attempt -le 12; $attempt++) {
    Start-Sleep -Seconds 10
    try {
        $health = (Invoke-WebRequest -Uri 'https://platform-api-smoky.vercel.app/health' -TimeoutSec 45 -UseBasicParsing).Content
        Write-Host "  attempt ${attempt}: $health"
        if ($health -match '"db"\s*:\s*"ok"') { break }
    } catch {
        Write-Host "  attempt ${attempt}: $($_.Exception.Message)"
    }
}

if ($health -match '"db"\s*:\s*"ok"') {
    Write-Ok 'API health reports the database reachable'
    Write-Step 'Running the launch-funnel verification'
    & $PythonExe (Join-Path $repoRoot '.artifacts/verify_funnel.py') 'https://platform-api-smoky.vercel.app' 2>&1 |
        Select-Object -Last 12
} else {
    Write-Fail 'API still reports the database unavailable. Check the platform-api deployment logs.'
    exit 6
}

# 6. Rotation record
$record = Join-Path $repoRoot ".artifacts/secret-rotation-$(Get-Date -Format yyyyMMdd-HHmmss).md"
@"
# Secret rotation record

- Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')
- Rotated in: Vercel project ``platform-api``, environment ``production``
- Variables rotated: DATABASE_URL, JWT_SECRET_KEY, PROVIDER_KEY_ENCRYPTION_SECRET
- Removed: PASSWORD_SALT (dead variable, audit L-5)
- Verification: GET /health returned db:ok; launch-funnel verification executed
- Effect: all previously issued console sessions are invalidated (expected)

Values are deliberately not recorded here. Retrieve them from the Vercel dashboard
if needed, or rotate again with this script.
"@ | Set-Content -Path $record -Encoding utf8
Write-Ok "rotation record written to $($record -replace [regex]::Escape($repoRoot), '.')"
Write-Host "`nDone." -ForegroundColor Green
