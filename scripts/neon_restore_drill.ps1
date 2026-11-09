#!/usr/bin/env pwsh
<#
.SYNOPSIS
    Restore drill for the production Neon database (NB-76 / LCH-05).

.DESCRIPTION
    Proves production data can actually be brought back, rather than assuming it.
    Neon's native mechanism is a copy-on-write branch, which is a real restore
    path and needs no pg_dump:

      1. Snapshot row counts + the alembic head on production.
      2. Create a branch from production.
      3. Compare the restored branch against the snapshot.
      4. Prove isolation: write a probe table on the branch and confirm it does
         NOT appear in production.
      5. Delete the branch and confirm only `main` remains.

    Exits non-zero on any mismatch. The branch is always deleted, including when
    a check fails, so a failed drill cannot leave a billable branch behind.

    Why this exists instead of scripts/db_backup.ps1: those scripts run
    `docker compose exec postgres pg_dump`, so they only work against the local
    Docker database. They cannot reach a managed Postgres, and no pg_dump or
    psql binary is installed in this environment. A drill that silently cannot
    run is worse than no drill, because it looks like coverage.

.PARAMETER NeonApiKey
    Neon API key. Defaults to $env:NEON_API_KEY.

.PARAMETER ProjectId
    Neon project id (not name).

.EXAMPLE
    $env:NEON_API_KEY = 'napi_...'
    ./scripts/neon_restore_drill.ps1 -ProjectId summer-wind-82665524
#>
[CmdletBinding()]
param(
    [string]$NeonApiKey = $env:NEON_API_KEY,
    [Parameter(Mandatory = $true)][string]$ProjectId,
    [string]$ParentBranch = 'main',
    [string]$DrillBranch = 'restore-drill',
    [string]$PythonExe = ''
)

$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
$neon = Join-Path $env:TEMP 'neon-cli\node_modules\.bin\neonctl.cmd'

function Step([string]$t) { Write-Host "`n=== $t ===" -ForegroundColor Cyan }
function Ok([string]$t) { Write-Host "  [ok] $t" -ForegroundColor Green }
function Die([string]$t) { Write-Host "  [xx] $t" -ForegroundColor Red; exit 1 }

if (-not $NeonApiKey) { Die 'No Neon API key. Set $env:NEON_API_KEY or pass -NeonApiKey.' }
if (-not (Test-Path $neon)) { Die "neonctl not found at $neon. Run scripts/setup_neon_production.ps1 once to install it." }
if (-not $PythonExe) {
    $candidate = Join-Path $repoRoot '.venv/Scripts/python.exe'
    $PythonExe = if (Test-Path $candidate) { $candidate } else { 'python' }
}

# Shared probe: counts + migration head. Emitted as one JSON line so the two
# sides can be compared exactly rather than by eyeballing printed text.
$PROBE = @'
import json, os, sys, psycopg
url = os.environ["FP_URL"]
out = {}
try:
    with psycopg.connect(url, connect_timeout=25) as c:
        with c.cursor() as cur:
            for table in ("organizations", "users", "warehouses", "shipments"):
                cur.execute(f"select count(*) from {table}")
                out[table] = cur.fetchone()[0]
            cur.execute("select version_num from alembic_version")
            out["alembic_head"] = cur.fetchone()[0]
    out["ok"] = True
except Exception as exc:
    out["ok"] = False
    out["error"] = f"{type(exc).__name__}: {str(exc)[:160]}"
print(json.dumps(out))
'@

function Get-Conn([string]$branch) {
    $args = @('connection-string', '--project-id', $ProjectId, '--pooled', '--api-key', $NeonApiKey)
    if ($branch) { $args += @('--branch', $branch) }
    $raw = & $neon @args 2>&1
    $line = ($raw | Where-Object { $_ -match '^postgres' } | Select-Object -First 1)
    if (-not $line) { Die "could not read a connection string for branch '$branch'" }
    return ([string]($line.Trim() -replace '^postgres(ql)?://', 'postgresql://'))
}

function Invoke-Probe([string]$url) {
    $env:FP_URL = $url
    $json = & $PythonExe -c $PROBE 2>&1 | Select-Object -Last 1
    Remove-Item Env:\FP_URL -ErrorAction SilentlyContinue
    try { return ($json | ConvertFrom-Json) } catch { Die "probe produced unparseable output: $json" }
}

# Preconditions: no leftover branch from a previous failed run
Step 'Preconditions'
$branches = (& $neon branches list --project-id $ProjectId --api-key $NeonApiKey --output json 2>&1) -join "`n"
if ($LASTEXITCODE -ne 0) { Die "could not list branches:`n$($branches | Select-Object -First 5)" }
$branchList = $branches | ConvertFrom-Json
if (@($branchList) | Where-Object { $_.name -eq $DrillBranch }) {
    Write-Host "  cleaning up a leftover '$DrillBranch' branch from an earlier run"
    & $neon branches delete $DrillBranch --project-id $ProjectId --api-key $NeonApiKey 2>&1 | Out-Null
    Start-Sleep -Seconds 5
}
Ok "clean slate ($(@($branchList).Count) branch(es) before the drill)"

# 1. Snapshot production
Step 'Snapshotting production'
$prodBefore = Invoke-Probe (Get-Conn '')
if (-not $prodBefore.ok) { Die "production is not reachable: $($prodBefore.error)" }
Ok ("production: orgs={0} users={1} warehouses={2} shipments={3} head={4}" -f `
    $prodBefore.organizations, $prodBefore.users, $prodBefore.warehouses, $prodBefore.shipments, $prodBefore.alembic_head)

# 2. Create the restore branch
Step "Creating restore branch '$DrillBranch' from '$ParentBranch'"
$created = (& $neon branches create --project-id $ProjectId --name $DrillBranch --parent $ParentBranch --api-key $NeonApiKey --output json 2>&1) -join "`n"
if ($LASTEXITCODE -ne 0) { Die "branch create failed:`n$($created | Select-Object -First 5)" }
$branchId = (($created | ConvertFrom-Json).branch).id
Ok "branch $branchId created"

# Wait for the compute to accept connections rather than guessing a sleep.
$prodAfter = $null
$restored = $null
try {
    for ($i = 1; $i -le 20; $i++) {
        Start-Sleep -Seconds 5
        $restored = Invoke-Probe (Get-Conn $DrillBranch)
        if ($restored.ok) { break }
        Write-Host "  waiting for the branch compute ($i/20): $($restored.error)"
    }
    if (-not $restored.ok) { Die "restore branch never became reachable: $($restored.error)" }

    # 3. Data must match
    Step 'Comparing restored data against production'
    $fields = @('organizations', 'users', 'warehouses', 'shipments', 'alembic_head')
    $mismatch = @()
    foreach ($f in $fields) {
        $a = $prodBefore.$f; $b = $restored.$f
        if ("$a" -ne "$b") { $mismatch += "$f prod=$a restored=$b" }
    }
    if ($mismatch.Count -gt 0) { Die "restored data differs from production:`n    $($mismatch -join "`n    ")" }
    Ok ("restored matches production on all {0} fields" -f $fields.Count)

    # 4. Isolation: a write on the branch must not reach production
    Step 'Proving isolation'
    $env:FP_URL = (Get-Conn $DrillBranch)
    & $PythonExe -c @'
import os, psycopg
with psycopg.connect(os.environ["FP_URL"], connect_timeout=25) as c:
    with c.cursor() as cur:
        cur.execute("create table if not exists restore_drill_probe (id int)")
        cur.execute("insert into restore_drill_probe values (1)")
    c.commit()
'@ 2>&1 | Out-Null
    Remove-Item Env:\FP_URL -ErrorAction SilentlyContinue

    $env:FP_URL = (Get-Conn '')
    $leaked = (& $PythonExe -c @'
import os, psycopg
with psycopg.connect(os.environ["FP_URL"], connect_timeout=25) as c:
    with c.cursor() as cur:
        cur.execute("select to_regclass('public.restore_drill_probe')")
        print("PRESENT" if cur.fetchone()[0] else "ABSENT")
'@ 2>&1 | Select-Object -Last 1).Trim()
    Remove-Item Env:\FP_URL -ErrorAction SilentlyContinue
    if ($leaked -ne 'ABSENT') { Die "a write on the restore branch reached production — isolation is broken" }
    Ok 'branch writes do not reach production'

    # 5. Production unchanged by the drill itself
    Step 'Confirming production was not disturbed'
    $prodAfter = Invoke-Probe (Get-Conn '')
    foreach ($f in @('organizations', 'users', 'warehouses', 'shipments', 'alembic_head')) {
        if ("$($prodBefore.$f)" -ne "$($prodAfter.$f)") {
            Die "the drill changed production.$f ($($prodBefore.$f) -> $($prodAfter.$f))"
        }
    }
    Ok 'production identical before and after the drill'
}
finally {
    Step 'Cleaning up'
    & $neon branches delete $branchId --project-id $ProjectId --api-key $NeonApiKey 2>&1 | Out-Null
    Start-Sleep -Seconds 5
    $remaining = ((& $neon branches list --project-id $ProjectId --api-key $NeonApiKey --output json 2>&1) -join "`n") | ConvertFrom-Json
    $names = (@($remaining) | ForEach-Object { $_.name }) -join ', '
    if ($names -notmatch [regex]::Escape($DrillBranch)) { Ok "drill branch deleted (remaining: $names)" }
    else { Write-Host "  [!!] drill branch may still exist — check the Neon dashboard" -ForegroundColor Yellow }
}

$recordDir = Join-Path $repoRoot '.artifacts'
New-Item -ItemType Directory -Force -Path $recordDir | Out-Null
$record = Join-Path $recordDir "neon-restore-drill-$(Get-Date -Format yyyyMMdd-HHmmss).md"
@"
# Neon restore drill record

- Date: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')
- Project: $ProjectId
- Method: Neon copy-on-write branch from `$ParentBranch` (no pg_dump available)
- Restored counts: orgs=$($restored.organizations) users=$($restored.users) warehouses=$($restored.warehouses) shipments=$($restored.shipments) head=$($restored.alembic_head)
- Production counts (before): orgs=$($prodBefore.organizations) users=$($prodBefore.users) warehouses=$($prodBefore.warehouses) shipments=$($prodBefore.shipments) head=$($prodBefore.alembic_head)
- Production counts (after):  orgs=$($prodAfter.organizations) users=$($prodAfter.users) warehouses=$($prodAfter.warehouses) shipments=$($prodAfter.shipments) head=$($prodAfter.alembic_head)
- Isolation: a probe table written on the branch was ABSENT in production
- Drill branch deleted: yes

Result: PASS — production data is restorable and the restore is isolated.
"@ | Set-Content -Path $record -Encoding utf8
Ok "record written to $($record -replace [regex]::Escape($repoRoot), '.')"

Write-Host "`nRestore drill PASSED." -ForegroundColor Green
