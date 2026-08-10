# Production Security Hardening — Living Behaviors

> ⚠️ **NOT YET IMPLEMENTED** — This feature is locked but not yet built. It is tracked as tickets NB-63 through NB-71 in `docs/behaviors/pending-behaviors.md` (SEC-01..SEC-09 in the plan). Execution batch: `feat/security-hardening-v1`, dispatched by @architect. Every rule below is written from the user's perspective (state, actions, consequences), not implementation mechanics.

## 1. Why this feature exists

The 2026-08-10 security audit (`docs/security-audit-2026-08-10.md`) found one critical, six high, seven medium, and eight low findings — none of which are fixed yet. Two of them are direct user-facing product failures, not abstract hygiene:

1. **Any signed-in operator can see every customer's data.** Roughly half the platform's surfaces (shipments, alerts, ops feeds, forecast, planning, invoices, live updates, telemetry ingestion) return all tenants' rows to any authenticated user with the lowest role. For a multi-tenant B2B SaaS this is a customer-trust failure: Operator A of Company A can read Company B's shipments, alerts, and audit trail.
2. **Any deployment copied from the repo's defaults runs with a publicly known signing key.** The committed `.env.example` and `docker-compose.yml` contain placeholder secrets long enough to pass every production guard. Anyone who reads the repository can forge an admin token for such an environment.

The remaining findings are dependency staleness (Next.js, axios, Electron), an unauthenticated feedback write endpoint, an unsafe Supabase auth configuration, and a set of medium/low hardening items. This feature fixes all of them and keeps the fixes from silently regressing.

## 2. The actors and their roles

- **Operator / Owner / Admin (any company):** sees only their own company's operational data on every surface, and never another company's. Nothing about their login, navigation, or data changes except that foreign data stops appearing.
- **Visitor / prospective customer:** can submit feedback only at a bounded rate (or not at all without signing in) — the feedback surface cannot be used to flood the operator queue.
- **Deployment operator (the company running FreightPilot):** can boot an environment only with real secrets; a misconfigured deployment fails fast with a message naming the problem variable, instead of running with a known key.
- **System (FreightPilot API, console, site, desktop):** refuses insecure startup states, scopes every data query to the caller's organization, and ships no known-vulnerable dependency versions.

## 3. No environment can boot with a known placeholder secret (NB-63)

When the platform starts in any non-development environment:

- the startup guard checks every secret against a known-placeholder list, not just a length check — `JWT_SECRET_KEY` and `PROVIDER_KEY_ENCRYPTION_SECRET` values that match any committed placeholder value (or are shorter than the minimum) prevent startup with an error that names the offending variable;
- no committed file in the repository contains a placeholder value that could pass the guards (`.env.example` ships empty values plus instructions);
- the Postgres container is not reachable from outside its host by default — its port is bound to the host loopback only, and `POSTGRES_PASSWORD` has no default;
- any environment that may have been deployed from defaults has its JWT and provider-encryption secrets rotated, and the rotation is documented in the ledger.

**Failure outcome:** startup aborts with a precise message. **Edge cases:** development/test environments keep their permissive dev defaults; a placeholder that differs from the committed list by a single character is still a real secret decision — only exact committed placeholders and length violations are rejected.

## 4. Every operator sees only their own company's data — everywhere (NB-64)

This rule is the product decision locked for the platform: **the ops console is a true multi-tenant SaaS surface.** Every operator surface is scoped to the operator's organization. Concretely:

- No list, detail, feed, timeline, forecast, route plan, invoice, alert, shipment, dock appointment, or ingestion response ever contains another organization's rows — on any page, any endpoint, any WebSocket message.
- Live updates (the live feed and WebSocket snapshot) deliver only the subscriber's own organization's data.
- Cross-tenant access attempts (e.g., guessing another org's record id) return **404 Not Found** — not 403 — so the existence of the record is never leaked.
- Write endpoints that mutate operational data (telematics, IoT telemetry, alert creation, shipment creation/updates, route persistence) stamp and enforce the caller's organization, and refuse rows that belong to another org.
- Regression coverage proves isolation with two organizations: two orgs with overlapping identifiers never see each other's rows, and the existing global-role endpoints (`/ops/audit-timeline`, `/ops/exception-feed`, `/ops/metrics`, `/shipments`, `/alerts`, `/forecast`, `/planning`, `/invoices`, `/live`, `/ingestion`, `/weather`) are all converted to membership-scoped queries.
- Any internal tool surface that must remain global is moved behind a distinct role that no customer signup can ever reach.

**Expected outcome:** a customer's data is invisible to every other customer, and an operator's daily workflow is unchanged except that foreign data is gone. **Failure outcome:** any endpoint still returning another org's rows is a release blocker.

## 5. The feedback surface cannot be abused (NB-65)

The feedback form is the only public write surface in the product. Either:

- only signed-in users can submit feedback (preferred — feedback then carries a real identity), **or**
- if public feedback is kept as a product requirement, a single visitor can submit at most 3 messages per hour (per IP), and the form includes a honeypot/captcha-style control.

In both cases the operator's feedback queue contains only real, bounded input. **Edge case:** an existing visitor who submits one message and returns later the same day is not blocked from their next legitimate submission.

## 6. The product ships no known-vulnerable dependency versions (NB-66)

- The product website runs on a Next.js major that still receives security patches (upgrade from 14.2.35 to ≥15.5.21, or 16.2.11), with the upgrade completed before any further self-hosted deployment.
- The ops console uses axios ≥1.18.0 (resolves the prototype-pollution, auth-injection, and proxy-routing advisories).
- The desktop shell runs on a supported Electron major (upgrade from 31), with the official Electron security checklist applied to the packaged app: exact-origin navigation guard on `will-navigate`, `setPermissionRequestHandler` on remote sessions, DevTools gated behind `!app.isPackaged`, and `@electron/fuses` flipping `runAsNode`/`nodeCliInspect`.
- After each upgrade: the full test suites, typecheck, and production builds pass; the live surfaces (site, console, desktop) still behave identically for operators.

**Failure outcome:** a dependency with a known critical/high advisory in a deployed surface blocks release.

## 7. Supabase auth can never be wired up unsafe (NB-67)

If the Supabase project is ever connected to any signup flow again, its auth configuration must be production-hardened first: email confirmations enabled, minimum password length 8 with complexity requirements, secure password change enabled, CAPTCHA enabled, and the remote project's dashboard settings (rate limits, SMTP sender, session timebox) reviewed. If the legacy Supabase auth path is permanently retired instead, the `supabase/` directory is removed or marked retired in the ledger so the landmine cannot be re-armed by accident.

## 8. The first visitor can never become the platform admin (NB-68)

Open registration can never produce a global admin. The bootstrap admin convention (first user in an empty database becomes ADMIN) is gated behind an explicit one-time environment flag that must be removed after first boot, or replaced by an admin-invite flow. **Failure outcome:** a database reset or failed migration cannot turn the next visitor into the platform administrator.

## 9. No account enumeration (NB-69)

Signup and login responses are uniform: a username/email that already exists returns the same generic conflict message as any other conflict, with the same timing, so a visitor cannot probe which accounts exist.

## 10. Console and upload hardening (NB-70)

- The ops console serves a Content-Security-Policy (nginx and Vercel) that keeps the token-bearing surface locked down: `default-src 'self'`, strict `script-src`, `object-src 'none'`, `frame-ancestors 'none'`, with `style-src 'unsafe-inline'` only because the map library requires it.
- CSV uploads are size-capped (e.g., 10 MB) with a clear in-product error message — an oversized file is rejected politely, and the API process never reads unbounded uploads.
- Python dependencies are locked (committed lockfile) and installed frozen in CI/images; a dependency vulnerability scan runs in CI.
- Docker deployment: Postgres binds to loopback only, no default password, and the backend requires explicit production secrets.

## 11. Low-severity tidy (NB-71)

The remaining low-severity items are fixed in one small pass: token revocation documented for high-privilege roles, `testserver` removed from default allowed hosts, `env` dropped from the public health endpoint, `Content-Disposition` on receipt file responses, the dead `PASSWORD_SALT` env var removed, npm workspace hoisting repaired, postcss bumped, and Electron IPC handlers validating their sender frame.

## 12. Preservation rules

- Existing locked behaviors are untouched: cashflow rules (NB-01..22), activation (NB-25..35), site copy (NB-36..47), live-launch trust (NB-48..53), console navigation (NB-54..59), and login color fidelity (NB-60..62) keep their acceptance criteria.
- Copy, handlers, page paths, and test markers are unchanged except where a rule above requires it (e.g., generic conflict messages).
- Nothing in this feature changes what a legitimate operator can do with their own company's data.

## 13. Acceptance standard

This feature is complete when:

- no environment can boot with a known placeholder secret, and the startup failure names the variable;
- two organizations with overlapping data can be operated side by side and neither can see or mutate the other's data on any surface, verified by the two-org regression suite;
- the feedback surface is bounded (authenticated or rate-limited) and the operator queue cannot be flooded anonymously;
- no deployed surface depends on a version with a known critical/high advisory (site, console, desktop all verified);
- the Supabase auth landmine is either hardened or retired;
- the bootstrap-admin backdoor is closed;
- signup/login no longer enumerates accounts;
- the console has a CSP, CSV uploads are capped, Python deps are locked and scanned in CI, and Docker exposes nothing unintended;
- the low-severity tidy items are closed;
- the full test suites (backend, console, site) are green and the new isolation guards are pinned by tests so they cannot silently regress.

---

## Ticket map

| Ticket | Rule |
|---|---|
| NB-63 | §3 No environment can boot with a known placeholder secret (SEC-01) |
| NB-64 | §4 Every operator sees only their own company's data — everywhere (SEC-02) |
| NB-65 | §5 The feedback surface cannot be abused (SEC-03) |
| NB-66 | §6 The product ships no known-vulnerable dependency versions (SEC-04) |
| NB-67 | §7 Supabase auth can never be wired up unsafe (SEC-05) |
| NB-68 | §8 The first visitor can never become the platform admin (SEC-06) |
| NB-69 | §9 No account enumeration (SEC-07) |
| NB-70 | §10 Console and upload hardening (SEC-08) |
| NB-71 | §11 Low-severity tidy (SEC-09) |

**Sources:** `docs/security-audit-2026-08-10.md` (C-1 → NB-63; H-1 → NB-64; H-5 → NB-65; H-2/H-3/H-4 → NB-66; H-6 → NB-67; M-1 → NB-68; M-2 → NB-69; M-3/M-4/M-5/M-6 → NB-70; L-1..L-9 → NB-71). Product decision D1 (multi-tenant org-scoping) is locked in §4.
