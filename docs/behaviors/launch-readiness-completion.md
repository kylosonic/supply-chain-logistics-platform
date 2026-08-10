# Launch Readiness Completion — Living Behaviors

> ⚠️ **NOT YET IMPLEMENTED** — This feature is locked but not yet built. It is tracked as tickets NB-72 through NB-79 in `docs/behaviors/pending-behaviors.md` (LCH-01..LCH-08 in the plan). Execution batch: `feat/launch-readiness-v1`, dispatched by @architect after the security-hardening batch. Every rule below is written from the user's perspective (state, actions, consequences), not implementation mechanics.

## 1. Why this feature exists

The platform's cashflow, activation, site, and live-launch features are shipped and QA-approved, and the production-readiness plan (`docs/production-readiness-plan.md`) closed its R0 environment-wiring tickets (PROD-01..05). What remains are the gaps between "works on Vercel previews" and "a real company can sign up, pay, and operate without a breakdown on launch day":

- the launch funnel is not verified end-to-end from the production domain;
- rate limits may false-429 office networks sharing one NAT on launch day;
- the site has no analytics and no error monitoring, so a broken launch form is invisible;
- the desktop shell is still dev-only — no signed installer, no update channel;
- production backups exist as a plan, not as a drilled procedure;
- CI gates are thinner than the release surface;
- stale documentation and legacy directories still contradict the shipped product;
- one human verification (CBE/Dashen fee schedules, TECH-22/NB-22) still blocks paid launch.

This feature turns the remaining checklist items into finished, verified behaviors.

## 2. The actors and their roles

- **Prospective customer:** lands on the real site, signs up, and reaches a working seeded workspace without a single security-blocked request, timeout, or false rate-limit error.
- **Operator:** opens the console from its real address, and the console and site can be monitored for health and errors without invasive tracking.
- **Desktop user:** downloads a signed installer, installs on a clean Windows machine, and reaches the real console.
- **Deployment operator (FreightPilot team):** can restore the production database from backup, is warned when CI is red, and reads only accurate, current documentation.
- **System:** refuses to deploy a red build, records privacy-light pageviews and signup clicks, and reports launch-form errors.

## 3. The launch funnel works end-to-end from the real domain (NB-72)

When a visitor starts from the production site address:

- the site loads, the "Start free" button submits the signup form to the production API with no browser security-blocked requests, no CORS errors, and no host-rejection errors;
- the visitor lands in the ops console with an authenticated session and a sample-data-seeded workspace;
- the first route optimization runs successfully on the sample data (activation milestone 6);
- the same flow is verified from both official web addresses;
- the CORS allowlist and allowed-hosts list used in production are the verified production values, and the regression tests pin them.

**Failure outcome:** any security-blocked request, CORS failure, or host rejection in the live flow blocks this ticket.

## 4. No false rate-limit errors on launch day (NB-73)

- A burst of signups from the same office network (shared NAT) does not produce 429 errors for legitimate users.
- The signup, login, and feedback limits are reviewed against the launch funnel and tuned per route where needed, with the final values documented in the ledger.
- Legitimate per-user abuse limits (login brute-force, signup spam) remain in force.

## 5. The funnel is observable — privacy-light (NB-74)

- The site records pageviews and "Start free" clicks with a privacy-light, no-fingerprinting analytics approach (e.g., Plausible/Umami), loaded `defer`/lazy, with no ad networks.
- Launch-form errors are observable (error monitoring on the site, at minimum for the signup form), so a broken funnel is visible within minutes, not discovered by a customer.
- Nothing about the site's honesty rules changes: no fabricated numbers are reported, and analytics never overrides copy.

## 6. The desktop installs and updates from the real product (NB-75)

- The desktop shell ships as a signed Windows installer (electron-builder, NSIS), pointing at the production console, signup, and docs URLs — no end-user environment variables required.
- An installer smoke test passes on a clean Windows VM: install → onboarding → connectivity test against production → launch console → login.
- Updates flow through a real channel (release feed), and the version is bumped to 1.0.0 with release notes.
- The packaged app re-verifies the Electron security posture (context isolation on, node integration off, external links open in the browser).

## 7. Production data can be restored (NB-76)

- The production Postgres backup strategy (Supabase PITR or scheduled dumps) is documented and **exercised**: a restore drill runs on a scratch database and proves the data comes back intact.
- The sample-data seeding path (workspace reset) works in production.
- The drill result is recorded in the ledger as evidence, not assumed.

## 8. CI gates the release (NB-77)

- The deploy pipeline runs the same gates a release depends on: full backend tests, console tests + typecheck + production build, site tests + `check:bundle` weight gate + production build, plus dependency vulnerability scans.
- A red gate blocks the Vercel deploy for the affected project (or is otherwise impossible to ignore).
- The gates are wired so they cannot be skipped silently.

## 9. Documentation and legacy artifacts match the shipped product (NB-78)

- The stale competitive-landscape document (`docs/competitive-landscape-2026.md`) is rewritten against the shipped site or deleted — it no longer contradicts the honesty rules.
- The legacy `supabase/` directory is retired or documented as history (per NB-67's decision).
- Housekeeping items (dead `@supabase/supabase-js` dependency, unused `.back-to-top` CSS) are removed.

## 10. The human verification gate is closed or explicitly recorded (NB-79)

- The CBE and Dashen fee schedules for transfers in the 5,000–50,000 ETB range are verified by a human against the ±1,000 ETB tolerance (NB-22 / TECH-22), and the finding is documented in `cashflow-bank-transfer-receipt-verification.md` §12 — or, if the gate cannot be closed, the production launch decision explicitly records the deferral with the risk stated.
- This is a human action, not a code ticket; the system's job is to make the decision visible and recorded.

## 11. Preservation rules

- All locked behaviors from the security-hardening batch (NB-63..71) and earlier batches remain untouched.
- The honesty rules (NB-43, NB-44) are preserved: analytics is privacy-light and never fabricates proof.
- The site's single-CTA rule, five-section structure, and page-weight budget are preserved.

## 12. Acceptance standard

This feature is complete when:

- the full launch flow is verified end-to-end from the production domain (signup → seeded workspace → first optimization) with zero security-blocked requests;
- rate limits are tuned and documented for the launch funnel;
- privacy-light analytics and error monitoring are live on the site, and a launch-form error is observable;
- the desktop ships as a signed, auto-updating Windows installer and passes the clean-VM smoke test;
- a restore drill proves production data can be restored;
- CI gates block red builds from reaching the deploy;
- stale docs and legacy artifacts no longer contradict the shipped product;
- the human fee-schedule gate is closed or explicitly recorded as a launch decision.

---

## Ticket map

| Ticket | Rule |
|---|---|
| NB-72 | §3 The launch funnel works end-to-end from the real domain (LCH-01) |
| NB-73 | §4 No false rate-limit errors on launch day (LCH-02) |
| NB-74 | §5 The funnel is observable — privacy-light (LCH-03) |
| NB-75 | §6 The desktop installs and updates from the real product (LCH-04) |
| NB-76 | §7 Production data can be restored (LCH-05) |
| NB-77 | §8 CI gates the release (LCH-06) |
| NB-78 | §9 Documentation and legacy artifacts match the shipped product (LCH-07) |
| NB-79 | §10 The human verification gate is closed or explicitly recorded (LCH-08) |

**Sources:** `docs/production-readiness-plan.md` §6/§8/§9 (PROD-06..PROD-13 → NB-72..78), `docs/behaviors/pending-behaviors.md` NB-22 (→ NB-79), `docs/security-audit-2026-08-10.md` (M-5/audit-tooling → NB-77).
