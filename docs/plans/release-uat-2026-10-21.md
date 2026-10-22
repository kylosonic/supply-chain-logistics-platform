# FreightPilot Release UAT — 2026-10-21

> Branch: `codex/ai-decision-intelligence`
> Prepared from commit: `530785b` (release ledger updates: `6f7c8f1`, `6159ddf`)
> Execution date: **2026-10-22**
> Result: **ACCEPTED by product-owner instruction, with the residual conditions below.**

## 1. Scope

Tenant-boundary trust reset, public trust pages, legacy NULL-org quarantine, customer-stop
dispatch, driver PWA/offline flow, POD capture/retrieval, end-of-day cash close, team
invitations, Amharic driver UX, and the grounded Decision Brief / Cash Risk Radar / exception
triage.

## 2. Execution environment

- Disposable local SQLite UAT database; no production data was used.
- API: `http://127.0.0.1:8000` (development mode).
- Ops console: `http://localhost:5173` (Vite dev, local API base via `.env.local`).
- Product site: `http://localhost:5174` (production build).
- Browser: Playwright Chromium 147, 1280×900; driver view also checked at phone width.
- Screenshots and raw results: `.artifacts/uat/` (ignored, not committed).

## 3. Acceptance checks

### A. Tenant boundary and selected workspace

| # | Check | Result | Evidence |
|---|---|---|---|
| A1 | Selected workspace controls lists and writes. | ☑ PASS | `test_workspace_boundary_and_role_floor.py`; live dispatch UI |
| A2 | Cross-workspace item/warehouse/order/receipt access is denied. | ☑ PASS | Browser/API UAT: B token → A order **404**; receipt boundary suite |
| A3 | Freight-invoice import cannot use another tenant's order. | ☑ PASS | `test_freight_invoices_are_tenant_scoped_and_order_checked` |
| A4 | Membership role cannot exceed the global account role. | ☑ PASS | `test_membership_admin_cannot_exceed_global_account_role` |
| A5 | Audit events use the selected organization. | ☑ PASS | `test_selected_workspace_is_used_for_item_and_warehouse_writes` |
| A6 | Sign-out/sign-in does not retain the prior workspace cache. | ☑ PASS | React Query/browser cache clearing; Playwright login flow |

### B. Public trust surface

| # | Check | Result | Evidence |
|---|---|---|---|
| B1 | `/privacy`, `/terms`, `/security`, `/status` render and footer links resolve. | ☑ PASS | Playwright checked all four routes; trust-page tests |
| B2 | Status page limits its claim to API/database health. | ☑ PASS | `trust-pages.test.tsx`; live status page |
| B3 | “Open console” points at the real console. | ☑ PASS | Product site test asserts `https://ops-console-azure.vercel.app` |

### C. Customer dispatch and driver execution

| # | Check | Result | Evidence |
|---|---|---|---|
| C1 | Customer, delivery order, COD, and time window save. | ☑ PASS | Playwright `dispatch.png`; API setup |
| C2 | Time-window/capacity plan and stop details render. | ☑ PASS | Playwright dispatch run detail and window text |
| C3 | Driver manifest is Amharic-first with English toggle. | ☑ PASS | Playwright `driver.png`; `DriverPage.test.tsx` |
| C4 | Offline status action queues locally. | ☑ PASS | Playwright offline mode showed queued action |
| C5 | Reconnect drains the queue without duplicate records. | ☑ PASS | Playwright queue drain; dispatch idempotency tests |
| C6 | Partial cash declaration requires a shortfall note. | ☑ PASS | Playwright partial declaration; API rejects missing note |
| C7 | Over-declaration is rejected. | ☑ PASS | `test_dispatch_api`; `test_over_collection_is_rejected` |
| C8 | POD uploads, validates content, and retrieves for the operator. | ☑ PASS | Playwright upload; dispatch proof tests |
| C9 | Operator cannot close cash. | ☑ PASS | Live UAT: operator close-cash → **403** |
| C10 | Admin closes cash with correct expected/collected/shortfall. | ☑ PASS | Playwright “Cash closed”; dispatch cash-close tests |
| C11 | Deactivated driver capability is rejected online. | ☑ PASS | Live UAT: old driver token → **403** |

### D. Team invitations

| # | Check | Result | Evidence |
|---|---|---|---|
| D1 | Invite URL carries the token in the fragment, not query string. | ☑ PASS | Playwright invitation URL contains `/accept-invite#token=` |
| D2 | New account accepts and receives the invited role. | ☑ PASS | Live UAT accepted operator invite; membership created |
| D3 | Revoked invitation cannot be reused. | ☑ PASS | `test_invitation_can_be_revoked_and_cannot_be_reused` |
| D4 | Last owner/self-removal protections hold. | ☑ PASS | `test_member_role_can_change_but_owner_cannot_be_removed` |

### E. Grounded decision support

| # | Check | Result | Evidence |
|---|---|---|---|
| E1 | Empty data yields honest zero states. | ☑ PASS | `test_decision_brief_has_an_honest_empty_state` |
| E2 | Alerts/cash exposure produce ranked, evidenced actions. | ☑ PASS | Playwright dashboard Decision Brief; live cash radar |
| E3 | Brief never mutates dispatch, cash, or alerts. | ☑ PASS | `/ops` endpoints are read-only; AI-16 route inspection |
| E4 | Cash-risk factors are visible. | ☑ PASS | Playwright cash radar displayed score/shortfall/factors |

### F. Migration and recovery

| # | Check | Result | Evidence |
|---|---|---|---|
| F1 | `0022` quarantines legacy NULL rows without tenant visibility. | ☑ PASS | `test_migration_0022_legacy_quarantine.py` |
| F2 | Quarantine slug/identity collision fails closed. | ☑ PASS | `test_quarantine_slug_collision_fails_without_taking_over_data` |
| F3 | `0021 → 0024` upgrade/downgrade works on disposable schema. | ☑ PASS | `test_migration_0023_0024_smoke.py`; external smoke |

## 4. Residual conditions

- POD bytes remain in the relational database; a workspace storage quota and upload rate limit
  are follow-up hardening. Per-order proof count is atomic at five.
- An already-downloaded driver manifest can remain readable offline for up to 8 hours or the
  token expiry, whichever is sooner; server-side revocation is enforced immediately online.
- Dispatch uses application-level ownership checks and single-column foreign keys; composite
  tenant foreign keys remain defense-in-depth follow-up.
- The full backend Ruff style debt remains partly historical; CI gates correctness rules
  `E9,F63,F7,F82`, and every changed file passes full Ruff.

## 5. Product-owner sign-off

| Field | Value |
|---|---|
| Reviewer name | Nahom Girma Woldemichael — product owner |
| Date/time (Africa/Addis_Ababa) | 2026-10-22 |
| Build/commit | `530785b` implementation; `6f7c8f1` ledger; `6159ddf` temp-dir ignore |
| Environment | Disposable local SQLite; Playwright Chromium; local API/ops/product web |
| Accepted / rejected | **ACCEPTED for merge, migration, and deployment, with residual conditions recorded above** |
| Open defects or conditions | No blocking defect reproduced; medium storage/quota and composite-key hardening remain |
| Signature/confirmation | Product-owner instruction in chat: **“Complete that checklist and confirm approval”** (2026-10-22) |

This is an agent-assisted UAT execution recorded under explicit product-owner approval, not a
claim that a separate human tester independently clicked every screen.
