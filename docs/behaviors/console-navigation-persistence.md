# Console Navigation & Login Continuity — Living Behaviors

> ✅ **IMPLEMENTED** — This feature shipped in the console navigation & login continuity batch (NB-54..NB-59; QA-approved commits `01808ae`, `ab9262a`, `a7da5c4` on `feat/console-navigation-ux`, 2026-08-08). Every rule below is written from the user's perspective (state, actions, consequences), not implementation mechanics.

## 1. Why this feature exists

Switching pages in the console currently feels like the whole application restarts: the shell rebuilds, panels replay entrance choreography, the dashboard refetches its data as if visited for the first time, and occasionally the operator is bounced back to the login screen mid-work. Signing in can also land the operator in a forced reload loop. This feature makes page switching and login continuity feel like they happen inside a single, stable application session.

## 2. The actors and their roles

- **Operator (any workspace role):** moves between console pages all day; expects the shell to stay put, data to stay fresh quietly, and the app to never restart itself.
- **Owner / Admin:** same expectations, plus reliable sign-in and never being kicked to a broken login flow.
- **System (FreightPilot console):** owns the single session shell, the one live data connection, the calm page change, and the soft sign-in/sign-out continuity.

## 3. Page switching never restarts the app

### 3.1 Navigation is always in-app

When the operator clicks any navigation item or any in-app link that leads to another console page, the application must not perform a full browser reload. The surrounding shell — sidebar with brand block and navigation groups, top shell with context label and identity chips, persistent banners — stays on screen unchanged; only the page content area changes.

Observable consequences the operator must never see while switching pages:

- a white flash or blank frame
- the app re-verifying the session from scratch
- being returned to the login screen
- the sidebar, header, or banners rebuilding or flickering
- the mobile navigation drawer closing or resetting unexpectedly

### 3.2 Every link that looks internal behaves internal

Any text or button on a console page that reads as a link to another console page (for example "Continue onboarding", "Continue setup", "Run your first route") navigates inside the application. External addresses (for example map attributions) remain external.

## 4. The workspace shell persists across pages

When the operator moves between pages:

- the sidebar (brand block, both navigation groups, identity footer with role and sign-out) stays mounted and unchanged;
- the top shell (context label, page descriptor, role and user chips) stays mounted;
- any persistent banner (usage cap, upgrade pitch, activation state) stays mounted and does not refetch or flash;
- the active page marker in the sidebar is always correct after the switch;
- on mobile, the drawer state the operator left is preserved where sensible.

## 5. Live data updates connect once per session

### 5.1 One connection, one session

The live data connection opens once per workspace session and remains open while the operator works. Leaving the dashboard and returning to it does not reopen or replay the connection.

### 5.2 Background refresh is invisible

When live data arrives, dashboard surfaces update quietly in the background. The operator must never see the dashboard blank out, replay its loading placeholders, or rebuild its panels because of a background refresh.

### 5.3 Graceful absence

If the live connection is unavailable, the operator still sees the last known data and the application keeps working normally. The console does not show errors, does not retry aggressively on every page visit, and does not hint that anything is broken.

## 6. Page changes are calm

When the operator switches pages:

- the new page content fades in once, briefly (roughly a tenth of a second) and subtly;
- panels, cards, and rows never replay individual entrance animations during the switch;
- nothing pops, staggers, or slides per element;
- if the operator has reduced motion enabled at the operating-system level, no fade is shown at all.

## 7. Scroll position and first-load placeholders

- When the operator returns to a page with the browser's back action, the page opens at the scroll position they left, not at the top.
- Moving forward to a new page starts at the top of that page.
- The first time a page loads, the operator sees a calm placeholder built from the same visual language as the console — never a bare text line.

## 8. Signing in and out never restarts the app; expired sessions never bounce

### 8.1 Sign-in lands softly

When the operator signs in successfully, they land on the dashboard inside the same application session. No full reload happens between the login screen and the dashboard. A failed sign-in shows a clear error on the login screen and nothing else happens.

### 8.2 Expired or refused sessions return softly

If the session expires or a data request is refused while the operator is working, the operator is returned to the login screen without a page reload, and the next successful sign-in works normally. The operator is never stuck in a loop where the app reloads into login repeatedly.

### 8.3 Sign-out returns softly

Signing out returns the operator to the login screen without a full reload.

### 8.4 The signup path is always reachable

The "Create company account" action on the login screen always opens the product website's signup page at its real address — never a placeholder, a local address, or a dead link.

## 9. Preservation rules

- All existing copy on every surface is preserved.
- All handlers, authentication flows, page paths, role gates, and test markers are preserved.
- No new external libraries are introduced.
- The console keeps the same visual language (one accent family, calm surfaces, mono numerals, no decorative motion).

## 10. Acceptance standard

This feature is complete when:

- switching between any two console pages never reloads, flashes, rebuilds the shell, replays entrance animations, or returns the operator to login;
- the dashboard shows fresh data without ever appearing to reload;
- sign-in, session expiry, and sign-out never trigger a full reload or a bounce loop;
- the login screen's signup action always reaches the product site;
- scroll position is preserved on back navigation;
- every rule above holds for operators using reduced motion.

---

## Ticket map

| Ticket | Rule |
|---|---|
| NB-54 | §3 Page switching never restarts the app |
| NB-55 | §4 The workspace shell persists across pages |
| NB-56 | §5 Live data updates connect once per session |
| NB-57 | §6 Page changes are calm |
| NB-58 | §7 Scroll position and first-load placeholders |
| NB-59 | §8 Signing in and out never restarts the app; expired sessions never bounce |
