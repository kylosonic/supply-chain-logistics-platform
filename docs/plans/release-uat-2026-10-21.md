# FreightPilot Release UAT — 2026-10-21

> Branch: `codex/ai-decision-intelligence`
> Scope: tenant-boundary trust reset, public trust pages, legacy data quarantine, customer-stop
> dispatch, driver PWA/POD/cash close, team invitations, Amharic driver UX, and the grounded
> Decision Brief / Cash Risk Radar / exception triage.
> Status: **automated gates under verification; human sign-off not yet recorded.**

## 1. Purpose

This checklist is the human acceptance gate for the branch. It is not a substitute for the
automated QA/security evidence; it verifies that the actual console and driver workflow make sense
to an operator. No production migration, merge, or deployment should be claimed complete until the
sign-off block at the end is filled.

## 2. Preconditions

- Use a **non-production** database or a disposable preview workspace.
- Take a database backup/snapshot before applying migrations `20260821_0022` through
  `20260823_0024`.
- Use two test workspaces (`Workspace A`, `Workspace B`) and one user who belongs to both.
- Use a phone-sized viewport (360–430px wide) for the driver checks.
- Keep browser devtools available to switch offline mode and inspect queued actions.

## 3. Acceptance checks

### A. Tenant boundary and selected workspace

| # | Check | Expected | Result |
|---|---|---|---|
| A1 | Sign in as a user in A and B; select A with `X-Organization-Id` through the console session. | Lists and writes reflect A only. | ☐ |
| A2 | From A, request a B item or warehouse by ID. | 404; B record is unchanged. | ☐ |
| A3 | From A, upload a freight-invoice CSV referencing a B order. | The B order is skipped; no B rate or carrier is returned. | ☐ |
| A4 | Give a global viewer an admin membership in B. Open team and receipt-queue surfaces. | Denied; membership cannot exceed the account role floor. | ☐ |
| A5 | Create an A shipment while B is the user's newest membership. | Audit event is stored under A. | ☐ |
| A6 | Sign out and sign in as another workspace in the same tab. | No prior workspace query data remains visible. | ☐ |

### B. Public trust surface

| # | Check | Expected | Result |
|---|---|---|---|
| B1 | Open `/privacy`, `/terms`, `/security`, and `/status`. | Pages render, footer links resolve, no 404. | ☐ |
| B2 | On `/status`, confirm the probe names the API/database limit and does not claim full-system health. | Copy is explicit about what is not checked. | ☐ |
| B3 | Check the footer “Open console” link. | Points at the real console, not localhost. | ☐ |

### C. Customer dispatch and driver execution

| # | Check | Expected | Result |
|---|---|---|---|
| C1 | Create two customers with different coordinates and time windows; create delivery orders. | Both orders are saved with COD and window values. | ☐ |
| C2 | Plan one run with a driver and capacity limit. | Stops are sequenced, windows/capacity are visible, and no global-optimality claim is shown. | ☐ |
| C3 | Open the signed driver link on a phone-sized viewport. | Amharic is the default; English toggle works; manifest shows stop order and amounts. | ☐ |
| C4 | Put the device offline and mark a stop in transit, delivered, and/or failed. | Changes queue locally and show queued count. | ☐ |
| C5 | Restore connectivity. | Queue syncs; manifest reloads; no duplicate stop or cash record appears. | ☐ |
| C6 | Declare less cash than expected without a note. | Rejected with an explanatory error. | ☐ |
| C7 | Declare more cash than COD. | Rejected. | ☐ |
| C8 | Upload a valid PNG proof; then upload a non-image renamed `.png`. | Valid proof saves and opens for the operator; spoofed content is rejected. | ☐ |
| C9 | Close cash as an operator. | Denied. | ☐ |
| C10 | Close cash as an admin after all stops are terminal. | Expected/collected/shortfall totals are correct; failed stops do not create a cash obligation. | ☐ |
| C11 | Deactivate a driver while an old link exists, then reload online. | Server rejects the old capability immediately. An already-downloaded offline manifest is capped at 8 hours and cannot observe a server-side revocation before expiry; confirm that residual is acceptable for the pilot. | ☐ |

### D. Team invitations

| # | Check | Expected | Result |
|---|---|---|---|
| D1 | Invite an operator by email. | Invite URL carries the token in the URL fragment, not the query string. | ☐ |
| D2 | Accept as a new account. | Membership is created with the invited role; login succeeds. | ☐ |
| D3 | Revoke a pending invite and retry acceptance. | 410/invalid; no membership is created. | ☐ |
| D4 | Try to remove the last owner or change your own role. | Denied with a clear reason. | ☐ |

### E. Grounded decision support

| # | Check | Expected | Result |
|---|---|---|---|
| E1 | Open the dashboard with no open alerts or cash exposure. | Brief shows honest zero states, not invented recommendations. | ☐ |
| E2 | Create an open alert and an open COD run. | Brief shows the alert, cash exposure, ranked actions, and evidence. | ☐ |
| E3 | Confirm the brief never mutates dispatch, cash, or alert state. | Recommendations are links only. | ☐ |
| E4 | Confirm cash-risk factors are visible. | Score, shortfall, count, and factors are shown. | ☐ |

### F. Migration and recovery

| # | Check | Expected | Result |
|---|---|---|---|
| F1 | Apply `0022 → 0023 → 0024` on a copy with legacy NULL rows. | Rows move to the inactive memberless quarantine; no tenant can read them. | ☐ |
| F2 | Pre-create a workspace using the reserved quarantine slug, then run `0022`. | Migration fails closed; no tenant data is reassigned or deleted. | ☐ |
| F3 | Downgrade the disposable copy from `0024` to `0021`. | New tables are removed; prior data remains. | ☐ |

## 4. Automated evidence to attach

- full backend suite output;
- scoped Ruff and mypy output;
- ops-console test, typecheck, lint, and real-config build output;
- product-web test, typecheck/build, and bundle-budget output;
- migration `0021 → 0024` upgrade/downgrade smoke output;
- independent QA and security review findings and dispositions;
- production `/health`, signup, dispatch, and cross-tenant smoke checks after deployment.

## 5. Human sign-off

| Field | Value |
|---|---|
| Reviewer name | |
| Date/time (Africa/Addis_Ababa) | |
| Build/commit | |
| Environment | |
| Accepted / rejected | |
| Open defects or conditions | |
| Signature/confirmation | |

**Not signed:** the automated test results in this repository do not constitute human UAT.
