# Phase 1 — Console Navigation & Login Continuity: Reloads + Auth (TECH-71/NB-54 + TECH-76/NB-59)

**Status:** LOCKED for `feat/console-navigation-ux` — Phase 1 of 6 in the Console Navigation & Login Continuity batch. Execution via `@build` (TDD), audit via `@qa` against the NB acceptance criteria, single atomic commit on QA APPROVED. Source of truth: `docs/behaviors/console-navigation-persistence.md` (§3, §8), `docs/behaviors/pending-behaviors.md` (NB-54, NB-59), `docs/plans/console-navigation-ux-plan.md` (§2 evidence), `docs/adr/tech-backlog.md` (TECH-71, TECH-76).

## 2. Goal

Make every in-app link inside `apps/ops-console` navigate via the router (never a browser reload) and make session refusal / sign-in / sign-out fully soft (no `window.location` bounce, no reload-into-login loops, no clearing of freshly issued tokens) — with zero new runtime dependencies.

## 3. Ground-truth decisions

1. **Soft-reset signal = module-level pub/sub in `src/services/api.ts`** — a module-scoped `Set` of listener callbacks with an exported `onAuthSessionExpired(listener)` register (returns an unsubscribe function). No `CustomEvent`, no new module, no dependency. Rationale: `api.ts` is already statically imported by `AuthContext.tsx` (no new cycle), and the node vitest environment (no jsdom) can exercise it with plain stubs.
2. **The 401 interceptor never touches `window`.** The `window.location.pathname !== '/login'` check and `window.location.assign('/login')` are deleted. Redirect happens exclusively through `ProtectedRoute`'s existing `<Navigate to="/login">` (react-router, in-app) once `AuthContext` state is nulled by the signal.
3. **Soft reset fires only when there is auth material to clear** (stored token OR stored org id), and **never while a session is being established**. A module-level `establishingSession` flag, toggled by exported `beginAuthSessionEstablishment()` / `endAuthSessionEstablishment()`, is set by `AuthContext.login()` around the whole sequence (login POST → me → subscription). This single rule covers: bad-credentials 401 (no material → error surfacing only, NB-59.2), follow-up 401 after a fresh login (guard → token survives, no signal, no bounce; error surfaces via the existing login catch), and mid-work 401 (material present, guard off → clear + signal → soft redirect, NB-59.3).
4. **Signal handler is state-only.** The interceptor clears storage; the `AuthProvider` listener only sets `user`/`orgId` to null (single responsibility, no double-clear).
5. **Internal-link rule:** any link whose href starts with `/` renders via react-router `Link`; anything else stays a plain `<a>` (external addresses — the OSM attribution and the signup URL — remain external per NB-54.3 / NB-59.5).
6. **`getToken()` becomes stored-token-only** — returns `getStoredToken()` or null; the `GET /auth/token` call and the `_cachedToken` module variable are deleted. `useLiveUpdates` already bails gracefully when the token is null (socket never opens — graceful absence).
7. **Signup fallback constant** in `LoginPage.tsx` changes from `http://localhost:8081#signup` to the real product site `https://product-web-chi.vercel.app/launch` (same value as `apps/ops-console/.env`; `VITE_*` values are public build-time constants, not secrets). `apps/ops-console/.env.example` is aligned to the same value so a prod build copied from the example can never ship a local address.
8. **`useResetWorkspace` (hooks/queries.ts L274 `window.location.assign('/login')`) is deliberately OUT of scope** — it is NB-35.7 reset behavior, asserted by `ActivationBanner.test.tsx`, not a 401 path and not an in-app link. Preserved untouched.
9. **Graphify note:** `graphify` is not installed in this environment and `graphify-out/` does not exist; AST mapping was performed by exhaustive file reads and greps (all edges verified against source). After `@build` completes edits, run `graphify update .` if the tool becomes available (per AGENTS.md §6).

## 4. Files to modify / create (with why)

- **Modify `apps/ops-console/src/services/api.ts`** — add pub/sub + establishment guard + rewrite the response interceptor error branch (delete L71–76 window logic). Storage helpers (`getStoredToken`/`setStoredToken`/`getStoredOrgId`/`setStoredOrgId`/`clearAuthStorage`) keep exact semantics.
- **Modify `apps/ops-console/src/context/AuthContext.tsx`** — subscribe to the session-expired signal (effect declared before the bootstrap effect so the listener exists before any bootstrap 401); wrap `login()` in the establishment guard with a `finally`; rewrite `getToken()` to stored-token-only; delete `_cachedToken` and the dynamic import.
- **Modify `apps/ops-console/src/pages/DashboardPage.tsx`** — replace the two raw anchors (GatePlaceholder L67, utilization locked variant L334) with router links; copy, classes, and structure unchanged.
- **Modify `apps/ops-console/src/pages/RoutesPage.tsx`** — replace the locked-map placeholder anchor (L110) with a router link; copy unchanged.
- **Modify `apps/ops-console/src/components/ui/MetricTile.tsx`** — render `Link` for internal `cta.href` (leading `/`), plain anchor otherwise; prop contract (`cta?: { label; href }`) unchanged so callers (DashboardPage L248/L264) need no edits.
- **Modify `apps/ops-console/src/pages/LoginPage.tsx`** — change the `VITE_SIGNUP_URL` fallback constant only (L39); keep `target="_blank" rel="noreferrer"` and all copy; external anchor stays (NB-54 applies to in-app links only).
- **Modify `apps/ops-console/.env.example`** — align `VITE_SIGNUP_URL` to the real product address.
- **Create `apps/ops-console/src/services/internalNavGuard.test.ts`** — static regression guard (see §7).
- **Modify `apps/ops-console/src/services/api.test.ts`** — add response-interceptor test suite (see §7).
- **Modify `apps/ops-console/src/pages/workspaceSurfaces.smoke.test.tsx`** — add one signup-URL assertion to the existing login smoke test; all existing `href="/upload"` assertions remain valid because SSR output of `Link` still renders the `href`.

Not modified (verified ineligible): `src/components/RouteMap.tsx` (external attribution, keep), `src/components/ActivationBanner.tsx` + `src/components/shell/*` (already `Link`/`NavLink`-based — confirmed by grep), `src/components/ProtectedRoute.tsx`, `src/App.tsx` (role gates/routes), `src/hooks/queries.ts` (reset flow), `src/services/authApi.ts`, `src/services/authErrors.ts`, `src/pages/ActivationBanner.test.tsx`, `src/services/authErrors.test.ts`, `apps/product-web/**` (skip-link `href="#main-content"` is an in-page hash outside ops-console scope).

## 5. Strict import / dependency map

All imports absolute, relative to `apps/ops-console/src`:

| File | Imports ADDED | Imports REMOVED / CHANGED | Notes |
|---|---|---|---|
| `services/api.ts` | none (pub/sub uses module-scope `Set`) | delete all `window.location` usage; delete nothing else | new exports: `onAuthSessionExpired(listener): () => void`, `beginAuthSessionEstablishment(): void`, `endAuthSessionEstablishment(): void`; existing exports unchanged |
| `context/AuthContext.tsx` | from `'../services/api'`: add `onAuthSessionExpired`, `beginAuthSessionEstablishment`, `endAuthSessionEstablishment` to the existing static import block (already imports `clearAuthStorage`, `getStoredOrgId`, `getStoredToken`, `setStoredOrgId`) | delete the dynamic `import('../services/api')` inside `getToken` and the `_cachedToken` module variable | react/react-hooks imports unchanged; `UserRead` import unchanged |
| `pages/DashboardPage.tsx` | `import { Link } from 'react-router-dom';` (new import line) | none | react-router-dom v6.23.1 already a dependency |
| `pages/RoutesPage.tsx` | `import { Link } from 'react-router-dom';` | none | |
| `components/ui/MetricTile.tsx` | `import { Link } from 'react-router-dom';` (file currently has zero imports) | none | |
| `pages/LoginPage.tsx` | none | none (constant value change only) | |
| `.env.example` | — | — | value change only |
| `services/internalNavGuard.test.ts` (new) | `node:fs` and `node:path` (dev-only builtins, not runtime deps) | — | |
| `services/api.test.ts` | none new (existing `vi`, stubs pattern reused) | — | add rejecting-adapter harness |
| `pages/workspaceSurfaces.smoke.test.tsx` | none | none | one new assertion |

Dependency constraint: **no new runtime dependency is allowed** (behavior doc §9.3). `Link`/`Navigate` come from the already-installed `react-router-dom`.

## 6. Acceptance checkpoints (verbatim NB rules from pending-behaviors.md)

**NB-54** (TECH-71): (1) clicking any navigation item or in-app link never performs a full browser reload — no white flash, no session re-verification, no return to login; (2) every link that reads as a link to another console page navigates inside the application; (3) external addresses (map attributions) remain external and unaffected; (4) sidebar, top shell, persistent banners stay on screen unchanged.

**NB-59** (TECH-76): (1) successful sign-in lands on the dashboard in the same application session, no reload between login and dashboard; (2) failed sign-in shows a clear error on the login screen and nothing else happens; (3) expired/refused sessions return to login without a page reload and the next sign-in works normally — never a reload-into-login loop; (4) sign-out returns to login without a full reload; (5) "Create company account" always opens the real product signup address — never a placeholder, local address, or dead link.

## 7. Test plan

Existing tests that touch the affected area (all must stay green, untouched unless listed): `src/services/api.test.ts` (extend), `src/services/authErrors.test.ts` (no change), `src/pages/workspaceSurfaces.smoke.test.tsx` (extend), `src/pages/ActivationBanner.test.tsx` (no change).

New test seams:
1. **`api.test.ts` — response-interceptor suite** (node env; reuse the existing `sessionMock`/`localMock` stubs; add a rejecting adapter that throws `{ response: { status: 401 } }`):
   - 401 with stored token → `clearAuthStorage` effect observed (token null), subscribed listener called, and a stubbed `window` records **no** `location.assign` call (vi.stubGlobal).
   - 401 during establishment (guard active) → token retained, listener not called, no assign.
   - 401 with no token and no org id (login-POST failure path) → storage untouched, no signal, no assign.
   - Listener unsubscribe → no call after 401.
   - Existing request-interceptor and storage round-trip tests unchanged.
2. **`internalNavGuard.test.ts` (new)** — reads `apps/ops-console/src` recursively; asserts no raw `<a href="/` pattern exists in any `.ts`/`.tsx` file (regression guard for NB-54.1/.2); asserts `RouteMap.tsx` still contains the OpenStreetMap attribution anchor (NB-54.3 preserved); asserts `LoginPage.tsx` contains the real product signup URL (NB-59.5). `href="https://…"` and `href="#…"` do not match the guard pattern.
3. **`workspaceSurfaces.smoke.test.tsx`** — extend the login test with `expect(html).toContain('https://product-web-chi.vercel.app/launch')`; existing dashboard/routes assertions (`href="/upload"`, `Continue onboarding`, `Unlocks after Milestone`) stay valid since `Link` SSR output retains the `href`.
4. **Documented limitation:** `AuthProvider` bootstrap/redirect is not unit-testable in the node environment (no jsdom; `renderToString` does not flush `useEffect`, and the codebase mocks `AuthContext` everywhere). The soft-redirect correctness is covered compositionally: interceptor tests prove "no reload + clear + signal", `ProtectedRoute` already navigates via `<Navigate>` when `isAuthenticated` is false, and the sign-in redirect (`<Navigate to="/" replace />` on `isAuthenticated`) is pre-existing. Final proof is the human UAT pass after all phases (PM plan §5.2).

## 8. Verification commands (from `apps/ops-console`)

- `npm run test` (vitest --run — full suite, expect 55 existing + new)
- `npm run typecheck` (tsc --noEmit)
- `npm run build` (tsc --noEmit && vite build — production build must inline the real `VITE_SIGNUP_URL`)
- Optionally `npm run lint`; then `graphify update .` if available

## 9. Preservation notes

- Preserve verbatim: all copy ("Continue onboarding →", "Unlocks after Milestone {n}", "Create company account →"), handlers, routing paths, `ProtectedRoute` role gates (`admin/operator/viewer/owner` per route in `App.tsx`), and all `data-testid` markers (none exist on the four anchor sites; do not add any).
- Keep `RouteMap.tsx` attribution, `useResetWorkspace` + its `assign('/login')` and its test, `authErrors.ts`, storage key names, and `useLiveUpdates` behavior untouched.
- Do NOT touch or stage the three unrelated dirty files: `.gitignore`, `.opencode/agents/vision.md`, `apps/platform-api/tests_full_run.log`.
- No commits until `@qa` APPROVED; single atomic commit for the phase.
