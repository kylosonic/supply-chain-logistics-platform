# Console Navigation & Login Continuity — Implementation Plan

**Status:** LOCKED by the human (2026-08-08). PM plan artifact — no implementation authority. Hand off to `@architect` for execution. Tickets: NB-54..NB-59 (`pending-behaviors.md`), TECH-71..76 (`tech-backlog.md`), living behaviors in `console-navigation-persistence.md`.

**Scope:** `apps/ops-console` only. Fixes the perceived "the whole application loads over and over again when switching pages" plus the broken sign-in continuity behind it.

---

## 1. Problem statement (from the operator's seat)

Switching pages in the console currently feels like the application restarts:

- the shell (sidebar, top bar, banners) rebuilds on every switch;
- every panel replays its entrance animation as if loading for the first time;
- the dashboard re-fetches its data every time you come back, as if nothing was cached;
- occasionally the operator is hard-bounced back to the login screen mid-work;
- signing in can land the operator in a reload-into-login loop.

The login screen itself is **not** broken (verified: correct API base, correct signup address, new design deployed). The breakage is in the session-handling path that force-reloads the app and dumps the operator onto login.

## 2. Confirmed root causes (evidence for @plan/@build)

| # | Cause | Where |
|---|---|---|
| 1 | Any refused session (401) triggers `window.location.assign('/login')` — a full browser reload that boots the whole app from scratch | `src/services/api.ts` L71–76 |
| 2 | Right after sign-in, a follow-up request can fail and clear the token the operator just received — the next page then loads tokenless and every request is refused → reload-into-login loop | `src/services/api.ts` interceptor + `src/context/AuthContext.tsx` sign-in sequence |
| 3 | Raw `<a href>` anchors bypass the router → genuine full page loads | `DashboardPage` L67/L334, `MetricTile` L34, `RoutesPage` L110 (OSM attribution in `RouteMap` is external and stays) |
| 4 | The shell is mounted inside every route, so it unmounts/remounts on each navigation | `src/App.tsx` (every route wraps `<Layout>`) |
| 5 | The live data socket lives inside the dashboard page — leaving and returning reconnects it, and each message invalidates six data groups at once | `src/hooks/useLiveUpdates.ts` + `DashboardPage` + `hooks/queries.ts` L243–248 |
| 6 | Every panel replays staggered entrance animations per mount | `animate-fade-in`/`animate-scale-in`/`animate-slide-up` + per-item `animationDelay` across pages |
| 7 | The socket token fallback calls an address that is not part of the auth surface → live updates silently fail in production | `src/context/AuthContext.tsx` (`getToken`) |

## 3. The six workstreams (one ticket each)

| Workstream | Ticket | What the operator gets |
|---|---|---|
| A. No more full reloads | NB-54 / TECH-71 | Every internal link navigates in-app. No white flash, no re-verification, no login bounce when clicking around. |
| B. Persistent shell | NB-55 / TECH-72 | Sidebar, top bar, banners stay mounted. Page marker always correct. Drawer state preserved on mobile. |
| C. One live connection | NB-56 / TECH-73 | Data connection opens once per session. Background refresh is invisible. Graceful absence — no churn, no errors. |
| D. Calm transitions | NB-57 / TECH-74 | One subtle ~120–150ms fade per page switch. No staggered pop-in. Reduced-motion users see nothing. |
| E. Scroll + placeholders | NB-58 / TECH-75 | Back/forward restores scroll position; forward nav starts at top. First loads show a calm console-style placeholder, never bare text. |
| F. Auth continuity | NB-59 / TECH-76 | Refused sessions return softly to login (no reload, no loops). Sign-in never clears its own token. Signup link always real. Sign-out stays in-app. |

## 4. Hard rules

- Preserve all existing copy, handlers, page paths, role gates, and test markers.
- No new external libraries. CSS-only motion.
- Keep the console's visual language (one accent family, calm surfaces, mono numerals).
- The console keeps working when the live connection is unavailable — it is a freshness channel, not a dependency.
- The behavior doc (`console-navigation-persistence.md`) is the acceptance source of truth; each ticket's acceptance criteria in `pending-behaviors.md` are written from the operator's perspective and are what @qa audits against.

## 5. Execution order for @architect

1. F-first or A-first is a call for @architect; recommended order: **A (reloads) → F (auth continuity) → B (persistent shell) → C (live connection) → D (transitions) → E (scroll/placeholders)**, because A and F remove the worst defects (hard reloads, login loops), B and C remove the churn, and D/E are the polish layer. Each workstream is its own atomic commit on `feat/console-navigation-ux`.
2. After all workstreams: full verification (`npm run test`, `npm run typecheck`, `npm run build` from `apps/ops-console`), then halt for the human's hands-on UAT before any merge to `master`.

## 6. Acceptance standard

This plan is complete when the behavior doc's §10 standard holds: switching pages never reloads, flashes, rebuilds the shell, replays entrance animations, or returns the operator to login; dashboard data stays fresh invisibly; sign-in/expiry/sign-out never hard-reload or loop; the signup action always reaches the product site; scroll is preserved on back; reduced-motion users get no motion.

---

## Handoff note

Tickets are written and the ledger is updated. Ready for `@architect` to open the batch: branch `feat/console-navigation-ux`, blueprints per phase, TDD, @qa audit per ticket, atomic commits, then the human UAT gate before merge.
