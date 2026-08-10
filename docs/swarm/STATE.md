# Swarm State — Authoritative Workflow Record

> Maintained by @scribe per `AGENTS.md` §3. Updated at every gate transition by @architect (stale state is a defect, NB-80).
> Last updated: 2026-08-10. All facts below verified against repository files and git refs at write time.

## 1. Current Phase

**Phase: `PLANNED`**

- Behavior sets NB-63..85 are **locked** (human confirmed 2026-08-10; docs commit `17ab7c8`).
- Implementation blueprint is **in progress** for Batch 1 (`feat/security-hardening-v1`).
- **Phase 1 scope = stop-the-bleed tickets: NB-63, NB-65, NB-66** (maps to audit C-1, H-5, H-3/H-2 — the audit's "Do this week" items).
- No implementation code exists on the active branch yet; `IMPLEMENTING` must not be entered until the Phase 1 blueprint is committed and @architect dispatches @plan → @build.

## 2. Active Feature Branch & Batch Definition

| Item | Value |
|---|---|
| Active branch | `feat/security-hardening-v1` (created 2026-08-10; `.git/HEAD` verified) |
| Branch head | `17ab7c88cb60c5a41d9846e1c41ff933d96af1e5` (`17ab7c8` — docs-only commit) |
| Batch | Security hardening batch: **SEC-01..SEC-09 → NB-63..NB-71** (per `docs/behaviors/production-security-hardening.md`) |
| Batch 1 | Stop-the-bleed: NB-63 (SEC-01), NB-65 (SEC-03), NB-66 (SEC-04) |
| Queued batches (locked, NOT yet branched/dispatched) | `feat/launch-readiness-v1` — LCH-01..08 → NB-72..79; `feat/swarm-health-growth-v1` — OPS-01..03 + GR-01..03 → NB-80..85 |
| Branch ownership | Single branch for the whole batch; no second branch permitted (`AGENTS.md` §4) |
| `master` | Untouched at `4f57019871af2f3debb575eee6420f98720a38af` (`4f57019`) — verified via `.git/refs/heads/master` |

## 3. Active Tickets

All tickets below are **NOT IMPLEMENTED** (locked by human confirmation 2026-08-10). Acceptance criteria live in `docs/behaviors/pending-behaviors.md`.

### 3.1 Security hardening batch (branch `feat/security-hardening-v1`) — NB-63..71

| NB | SEC | Priority | Status | Ticket summary |
|---|---|---|---|---|
| NB-63 | SEC-01 | P0 | NOT IMPLEMENTED | No environment can boot with a known placeholder secret (audit C-1) |
| NB-64 | SEC-02 | P0 | NOT IMPLEMENTED | Every operator sees only their own company's data — everywhere (audit H-1; product decision D1 locked) |
| NB-65 | SEC-03 | P1 | NOT IMPLEMENTED | The feedback surface cannot be abused (audit H-5) |
| NB-66 | SEC-04 | P1 | NOT IMPLEMENTED | No known-vulnerable dependency versions (audit H-2/H-3/H-4) |
| NB-67 | SEC-05 | P1 | NOT IMPLEMENTED | Supabase auth can never be wired up unsafe (audit H-6) |
| NB-68 | SEC-06 | P1 | NOT IMPLEMENTED | First visitor can never become the platform admin (audit M-1) |
| NB-69 | SEC-07 | P2 | NOT IMPLEMENTED | No account enumeration (audit M-2) |
| NB-70 | SEC-08 | P1 | NOT IMPLEMENTED | Console and upload hardening: CSP, CSV cap, dep locking, Docker posture (audit M-3/M-4/M-5/M-6) |
| NB-71 | SEC-09 | P2 | NOT IMPLEMENTED | Low-severity tidy (audit L-1..L-9) |

### 3.2 Launch-readiness batch (branch NOT yet created) — NB-72..79

| NB | LCH | Priority | Status |
|---|---|---|---|
| NB-72 | LCH-01 | P0 | NOT IMPLEMENTED — launch funnel end-to-end from real domain (PROD-06) |
| NB-73 | LCH-02 | P1 | NOT IMPLEMENTED — no false rate-limit errors (PROD-11) |
| NB-74 | LCH-03 | P1 | NOT IMPLEMENTED — funnel observable, privacy-light (PROD-10) |
| NB-75 | LCH-04 | P1 | NOT IMPLEMENTED — desktop installs/updates from real product (PROD-07) |
| NB-76 | LCH-05 | P1 | NOT IMPLEMENTED — production data can be restored (PROD-08) |
| NB-77 | LCH-06 | P1 | NOT IMPLEMENTED — CI gates the release (PROD-13) |
| NB-78 | LCH-07 | P2 | NOT IMPLEMENTED — docs/legacy artifacts match shipped product (PROD-09, PROD-12) |
| NB-79 | LCH-08 | P0 (human gate) | NOT IMPLEMENTED — fee-schedule verification closed or explicitly recorded (TECH-22/NB-22) |

### 3.3 Swarm-health & growth batch (branch NOT yet created) — NB-80..85

| NB | ID | Priority | Status |
|---|---|---|---|
| NB-80 | OPS-01 | P1 | NOT IMPLEMENTED — state file exists and is current. *Note: this file partially fulfills AC1; ticket stays open pending batch execution and @architect gate-update ownership.* |
| NB-81 | OPS-02 | P1 | NOT IMPLEMENTED — no merge without recorded human UAT |
| NB-82 | OPS-03 | P2 | NOT IMPLEMENTED — deployment topology recorded as ADR |
| NB-83 | GR-01 | P2 (v1.1) | NOT IMPLEMENTED — owners can invite teammates |
| NB-84 | GR-02 | P2 (v1.1) | NOT IMPLEMENTED — phone-on-file state visible |
| NB-85 | GR-03 | P2 (v1.1) | NOT IMPLEMENTED — route decisions explainable |

### 3.4 Previously shipped (for reference, NOT active)

- TECH-01..21, TECH-25..54, TECH-56..79 debited; NB-01..21, NB-23..62 `[IMPLEMENTED]` per `docs/adr/tech-backlog.md`. TECH-49 parked (shipments `shipment_no` global unique index — deferred multi-tenant hazard).

## 4. Completed Gates

| Gate | Status | Evidence |
|---|---|---|
| Security audit produced | ✅ PASS | `docs/security-audit-2026-08-10.md` (2026-08-10; 1 critical, 6 high, 7 medium, 8 low; auditor @vision + web research) |
| Audit verified in code | ✅ PASS | @vision manual code review + live `npm audit` + git-history secret scan (91 commits, zero secrets ever committed) |
| Behavior sets locked (NB-63..85) | ✅ PASS | Human confirmed behavior set and approved Batch 1 first (2026-08-10) |
| Docs committed | ✅ PASS | Commit `17ab7c8` on `feat/security-hardening-v1` (behavior docs + ledger) |
| Branch created | ✅ PASS | `feat/security-hardening-v1` created 2026-08-10; `.git/HEAD` verified |

## 5. Failed Gates

**None.** (Recorded explicitly: zero failed gates to date on this batch.)

## 6. Retry Count

**0** — no implementation correction, QA, or security retry loops have occurred on this batch (no code exists yet).

## 7. Unresolved Risks

| Risk | Detail | Blocker level |
|---|---|---|
| TECH-22 / NB-22 — CBE/Dashen fee-schedule human gate | ±1,000 ETB tolerance (NB-09) must be verified against published CBE/Dashen fees (5,000–50,000 ETB) before production; procedure in `docs/plans/phase3-audit-reversibility.md` §12, findings to `cashflow-bank-transfer-receipt-verification.md` §12 | Blocks **production launch (R2) only** — not code |
| C-1 — deployable placeholder secrets | `.env.example` values (36/42 chars) pass length guards; `docker-compose.yml` publishes 5432 + default Postgres password | → NB-63 |
| H-1 — cross-tenant authorization gap | ~half of endpoints guard only by global role and return all tenants' rows (shipments, alerts, ops feed, forecast, planning, invoices, live WebSocket, telemetry ingestion); includes cross-tenant writes | → NB-64 (release blocker per behavior doc) |
| H-2/H-3/H-4 — dependency staleness | `next@14.2.35` (terminal 14.x, unpatched since Dec 2025); axios declared `^1.7.2` (resolved 1.16.1; patched only ≥1.18.0); `electron@^31` EOL (~12 majors behind) | → NB-66 |
| H-5 — unauthenticated `/feedback` | Only fully public write endpoint; unlimited 2 KB anonymous POSTs | → NB-65 |
| H-6 — Supabase auth landmine | Email confirmations disabled, min password 6, no CAPTCHA if ever wired to signup | → NB-67 |
| PROD-06..13 — production-readiness tickets | PROD-06 (P0) + PROD-07..11 (P1) + PROD-12/13 (P2) open in `docs/production-readiness-plan.md` §9; PROD-01..05 ✅ DONE (R0) | Maps to NB-72..78 |
| Local-only working tree changes | Pre-existing uncommitted files NOT part of this batch: `.opencode/agents/*` (11 agent files), `AGENTS.md`, `.gitignore`, `apps/platform-api/tests_full_run.log` | Must NOT be swept into batch commits |

## 8. Artifact Paths

- `docs/swarm/STATE.md` — this file (created 2026-08-10)
- `docs/behaviors/pending-behaviors.md` — gap ledger (NB-01..85 + DEFERRED-01..09)
- `docs/behaviors/production-security-hardening.md` — living behaviors NB-63..71 (SEC-01..09)
- `docs/behaviors/launch-readiness-completion.md` — living behaviors NB-72..79 (LCH-01..08)
- `docs/behaviors/swarm-health-and-growth-candidates.md` — living behaviors NB-80..85 (OPS/GR)
- `docs/security-audit-2026-08-10.md` — audit findings (C-1, H-1..6, M-1..6, L-1..9)
- `docs/adr/tech-backlog.md` — TECH execution ledger (TECH-22 open)
- `docs/production-readiness-plan.md` — PROD tickets + env matrices + rollout phases (R0..R3)
- `docs/plans/phase3-audit-reversibility.md` — TECH-22 human-gate procedure (§12)
- Behavior docs for shipped features: `docs/behaviors/cashflow-bank-transfer-receipt-verification.md`, `operator-activation-and-milestone-tracking.md`, `site-conversion-and-copy.md`, `live-launch-origin-trust-and-readiness.md`, `console-navigation-persistence.md`, `console-login-color-fidelity.md`

## 9. Last Verification Evidence

| Evidence | Value |
|---|---|
| Docs lock commit | `17ab7c88cb60c5a41d9846e1c41ff933d96af1e5` (`17ab7c8`) on `feat/security-hardening-v1` — verified in `.git/refs/heads/feat/security-hardening-v1` |
| Security audit date | 2026-08-10 |
| Audit verification | Verified in code by @vision (manual review + npm audit + git-history scan); report states "Nothing in this report has been changed in the codebase" — fixes are pending, none applied |
| `master` ref | `4f57019871af2f3debb575eee6420f98720a38af` (`4f57019`) — verified in `.git/refs/heads/master` |
| Test evidence on branch | None yet — no implementation code exists on `feat/security-hardening-v1` |

## 10. Rollout / Rollback Note

- The branch is **safe to abandon**: `feat/security-hardening-v1` contains only the docs commit `17ab7c8`; deleting it loses no code (behavior sets remain in `docs/behaviors/*`).
- `master` is **untouched at `4f57019`** — no deployment, no environment change, no rollback path needed.
- Any environment previously deployed from repo defaults must have JWT + provider-encryption secrets **rotated** before Batch 1 completion (NB-63 AC5; audit C-1 fix item 4).
