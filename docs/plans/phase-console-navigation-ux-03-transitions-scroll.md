# Blueprint: Phase 3 — Calm Page Transitions & Scroll Restoration (NB-57 / NB-58)

**Status:** LOCKED execution blueprint for `@build`. Branch: `feat/console-navigation-ux`. Batch: TECH-74 / NB-57 + TECH-75 / NB-58. Source of truth: `docs/behaviors/console-navigation-persistence.md` (§6, §7), `docs/behaviors/pending-behaviors.md` (NB-57, NB-58), `docs/plans/console-navigation-ux-plan.md` (§2 evidence rows 6; §5 workstreams D/E). No new external libraries. CSS-only motion.

**Graphify note:** the `graphify` CLI is not installed on this machine and `graphify-out/` does not exist; AST/edge mapping was performed via direct file reads of every file listed below. If `graphify` becomes available, run `graphify update .` after the batch; do not block execution on it.

## 1. Title + Status

- **Feature:** Console navigation UX — Phase 3: calm page transitions (TECH-74 / NB-57) + scroll restoration & first-load placeholders (TECH-75 / NB-58)
- **Branch:** `feat/console-navigation-ux`
- **Scope:** `apps/ops-console` only. Builds on Phase 2 (layout-route shell, nested Suspense, RouteFallback).

## 2. Goal

Make page switching in the console feel like a single calm session: one subtle ~140ms content fade on in-app navigation (nothing per-element, nothing on reduced motion), window scroll position restored on back navigation (forward starts at top), and first loads show a calm console-language skeleton instead of a bare text line — with the shell staying mounted and zero new dependencies.

## 3. Ground-truth decisions

### 3.1 Transition mechanism — ONE wrapper fade, CSS-only (TECH-74)

- **Decision:** Option (a) — a new `PageTransition` module (component) mounted ONCE inside `Layout.tsx`, wrapping `<Outlet/>` **inside the existing nested `<Suspense>`**. It renders a plain `<div>` keyed by `location.pathname`; the key change remounts only the div + outlet content and re-triggers a pure CSS animation class (`fp-page-fade`, 140ms `fadeIn` ease-out, `both` fill). The shell (`Layout`, sidebar, header, banners, mobile drawer) never remounts; `Layout` itself is never keyed. React-router already swaps route elements, so the remount is free.
- **Placement rationale (inside Suspense, not outside):** the animation class lives on the keyed div, which is the suspended tree — the fade starts when the page content actually commits. Consequence: on a lazy chunk's first visit (skeleton → content), content fades in after the skeleton; on cached-chunk navigation (the common case), content fades in immediately. RouteFallback stays OUTSIDE the animated subtree, so the skeleton never fades in or out.
- **First-login-load decision:** NO fade on the very first layout mount. The `PageTransition` module suppresses the animation class on initial mount via a `useRef` flag flipped in a mount-only effect (StrictMode-safe). Justification: the login→dashboard landing is an auth flow completion, not a page switch. Subsequent pathname changes (in-app navigation) always fade. The top-level `/login` and `/unauthorized` routes are outside `Layout` and never receive the wrapper fade — acceptable, documented edge.
- **CSS:** add one utility `.fp-page-fade { animation: fadeIn 0.14s ease-out both; }` reusing the existing `fadeIn` keyframes. `both` fill + the existing `prefers-reduced-motion` block (index.css) zeroes the duration → no fade for reduced-motion users (NB-57.3) with zero extra code.

### 3.2 Animation inventory — per-site decision (exact)

Grep basis: `animate-fade-in|animate-scale-in|animate-slide-up|stagger-|animationDelay` across `apps/ops-console/src` (31 hits). Classification rule: remove every page-mount entrance (class and/or inline `animationDelay`); keep ONLY genuine state changes. Recorded corrections: `.fp-nested-surface`, `.fp-shell-surface`, `.fp-pill`, `.fp-input` have NO baked animation — only `.fp-row` does; `.stagger-1..6` utilities are defined but have ZERO usages (dead code).

| # | Site | Current | Classification | Decision |
|---|---|---|---|---|
| 1 | `components/ui/Panel.tsx` L22 | `animate-fade-in` on shared page panel | Page-mount entrance | REMOVE class |
| 2 | `components/ui/PageHeader.tsx` L12 | `animate-slide-up` on every page header | Page-mount entrance | REMOVE class |
| 3 | `components/ui/MetricTile.tsx` L25 | `animate-scale-in` on tile | Page-mount entrance | REMOVE class; **KEEP** L29 inline `pulseRing` style (state-driven) |
| 4 | `pages/DashboardPage.tsx` L295–296 | `animate-fade-in` + `animationDelay` on exception-queue rows | Page-mount list | REMOVE class + style |
| 5 | `pages/DashboardPage.tsx` L310 | `animate-fade-in` on "Queue clear" empty state | Mount-rendered | REMOVE class |
| 6 | `pages/DashboardPage.tsx` L357 | `animate-fade-in` + delay on audit timeline items | Page-mount list | REMOVE class + style |
| 7 | `pages/AccountPage.tsx` L461 | `animate-fade-in` on audit event articles | Page-mount list | REMOVE class |
| 8 | `pages/AlertsPage.tsx` L281 | `animationDelay` stagger on alert rows | Page-mount list | REMOVE style |
| 9 | `pages/AlertsPage.tsx` L324 | `animate-fade-in` on "No alerts" empty state | Mount-rendered | REMOVE class |
| 10 | `pages/PlanningPage.tsx` L235 | `animate-fade-in` on empty state | Mount-rendered | REMOVE class |
| 11 | `pages/PlanningPage.tsx` L261 | `animationDelay` on plan rows | Page-mount list | REMOVE style |
| 12 | `pages/ProvidersPage.tsx` L87 | `animate-fade-in` on page wrapper | Page-mount entrance | REMOVE class |
| 13 | `pages/ProvidersPage.tsx` L179 | `animate-fade-in` on `{testError && …}` block | **STATE CHANGE** | **KEEP** |
| 14 | `pages/RoutesPage.tsx` L136 | `animationDelay` on run rows | Page-mount list | REMOVE style |
| 15 | `pages/RoutesPage.tsx` L158 | `animate-fade-in` on empty state | Mount-rendered | REMOVE class |
| 16 | `pages/ShipmentsPage.tsx` L242 | `animationDelay` on shipment rows | Page-mount list | REMOVE style |
| 17 | `pages/ShipmentsPage.tsx` L277 | `animate-fade-in` on empty state | Mount-rendered | REMOVE class |
| 18 | `pages/UnauthorizedPage.tsx` L4 | `animate-fade-in` on standalone page | Page-mount entrance (outside Layout) | REMOVE class |
| 19 | `components/CsvUploadPanel.tsx` L108 | `animationDelay` on `uploadSpecs` cards | Static mount-rendered config list | REMOVE style (keep `fp-row`) |
| 20 | `components/RouteOptimizerForm.tsx` L154 | `animate-slide-up` on `{result ? …}` container | **STATE CHANGE** (results after submit) | **KEEP** |
| 21 | `components/RouteOptimizerForm.tsx` L194 | `animationDelay` stagger on stop rows | Per-item stagger inside state-change block | REMOVE style (keep `fp-row`) |
| 22 | `index.css` `.fp-row` (L249) | `animation: fadeIn 0.3s ease-out both;` baked into shared class | Replays on every row mount | **STRIP** the animation line; keep `transition` + hover |
| 23 | `index.css` `.stagger-1..6` (L127–132) | Dead utilities, zero usages | Dead code | REMOVE block |
| 24 | `index.css` `.fp-dialog-overlay` (L236) + `.fp-dialog-surface` (L242) | `fadeIn 0.3s` / `scaleIn 0.28s` | **STATE CHANGE** (dialog open) | **KEEP untouched** |
| 25 | `index.css` keyframes `fadeIn`/`slideUp`/`scaleIn`/`shimmer`/`pulseRing`/`spin` | Keyframe defs | All still referenced after edits | KEEP all |
| 26 | `index.css` L259–264 `prefers-reduced-motion` block | Zeroes animation/transition duration globally | NB-57.3 mechanism | **KEEP untouched** |
| 27 | `components/ui/StatusBadge.tsx` L33 | inline `pulseRing` | **STATE CHANGE** | **KEEP** |

After the batch, the only remaining `animate-*`/`animationDelay` occurrences in src are: `index.css` (utility definitions + dialog classes + `.fp-page-fade`) and `RouteOptimizerForm.tsx` (`animate-slide-up` container only — no `animationDelay`).

### 3.3 Scroll restoration — mechanism (TECH-75)

- **Which element scrolls (confirmed):** the window/document. `Layout`'s root is `min-h-screen` with a `px-4 py-4` flex container — no overflow container on the main column. The desktop sidebar is `sticky top-4 h-[calc(100vh-2rem)]` with its own internal scroll (preserved automatically because `ShellSidebar` stays mounted, Phase 2). **ScrollManager restores the WINDOW scroll only.**
- **Mechanism:** a `ScrollManager` module (component, renders `null`) mounted once in `Layout` next to `SessionLiveUpdates`, using `useLocation()` + `useNavigationType()` (react-router-dom 6.23.1 built-in export; no new deps):
  - **Save:** passive `window` `scroll` listener, debounced ~100ms, writing `scrollPositions.save(pathname, window.scrollY)` for the CURRENT pathname.
  - **Restore semantics:** on `navigationType === 'POP'` (back/forward) → `window.scrollTo(0, saved ?? 0)`; on `PUSH`/`REPLACE` → `window.scrollTo(0, 0)` (NB-58.2). The catch-all `<Navigate to="/" replace />` is `REPLACE` → top.
  - **Store decision:** plain in-memory `Map<string, number>` behind a pure factory `createScrollPositions()` held in a `useRef` (app-lifetime; per-tab; SSR-safe). **Not** sessionStorage: hard reloads are handled by the browser's native `history.scrollRestoration`; sessionStorage risks stale positions across token re-entry. Documented limitations: positions lost on hard reload (native takes over); a page whose height changed clamps at the browser's max; positions keyed by pathname only (no console page varies scroll by search params — acceptable).
  - **Timing note:** on POP the restore fires immediately; if the chunk is uncached the skeleton renders first and the browser clamps the restore when content commits (rare — back targets are typically cached chunks). Do not add delay hacks.
  - `typeof window !== 'undefined'` guards inside effects for SSR robustness. No interaction with `history.scrollRestoration` (leave default).

### 3.4 First-load placeholder — RouteFallback upgrade (TECH-75)

- **Decision:** replace the bare text div with a calm, console-language skeleton surface, keeping the copy "Loading workspace surface..." as `sr-only` text (preserves the verbatim string for screen readers AND the existing Phase-2 guard assertions). Structure: an outer `fp-nested-surface` container with `role="status"`, containing: one header-width skeleton bar, two to three panel-shaped skeleton blocks, and a row of smaller bars — all using the existing `.skeleton` utility (shimmer keyframes; first real consumer). Neutral shape works for both the nested console fallback and the top-level `/login`/`/unauthorized` chunk fallback (`App.tsx` reuses the same `RouteFallback`). Keep it cheap — lazy chunks suspend once per session.
- `RouteFallback` stays exported from `Layout.tsx`; `App.tsx` is untouched.

## 4. Exact files to modify/create (with why)

**Create:**
1. `apps/ops-console/src/components/PageTransition.tsx` — the single-fade wrapper module.
2. `apps/ops-console/src/services/scrollPositions.ts` — pure `createScrollPositions()` store (testable in node).
3. `apps/ops-console/src/components/ScrollManager.tsx` — window-scroll save/restore component (renders `null`).
4. `apps/ops-console/src/motion.guard.test.ts` — static fs guard for the animation inventory.
5. `apps/ops-console/src/services/scrollPositions.test.ts` — pure store tests.
6. `apps/ops-console/src/components/ScrollManager.test.tsx` — SSR + source-string guards.
7. `apps/ops-console/src/components/PageTransition.test.tsx` — SSR + source-string guards.

**Modify:**
8. `apps/ops-console/src/components/Layout.tsx` — mount `<PageTransition>` inside the nested `<Suspense>` around `<Outlet/>`; mount `<ScrollManager />` beside `<SessionLiveUpdates />`; upgrade `RouteFallback` to the skeleton + sr-only copy. (`Layout` keeps `min-h-screen` root, `space-y-5` main, sidebar/drawer structure, all props and handlers.)
9. `apps/ops-console/src/index.css` — strip `.fp-row` animation line (L249); delete `.stagger-1..6` (L127–132); add `.fp-page-fade` utility. Touch nothing else.
10. `apps/ops-console/src/components/ui/Panel.tsx` — remove `animate-fade-in` (row 1).
11. `apps/ops-console/src/components/ui/PageHeader.tsx` — remove `animate-slide-up` (row 2).
12. `apps/ops-console/src/components/ui/MetricTile.tsx` — remove `animate-scale-in`; keep `hover-lift`, keep `pulseRing` style (row 3).
13. `apps/ops-console/src/pages/DashboardPage.tsx` — rows 4–6.
14. `apps/ops-console/src/pages/AccountPage.tsx` — row 7.
15. `apps/ops-console/src/pages/AlertsPage.tsx` — rows 8–9.
16. `apps/ops-console/src/pages/PlanningPage.tsx` — rows 10–11.
17. `apps/ops-console/src/pages/ProvidersPage.tsx` — row 12 only (row 13 stays).
18. `apps/ops-console/src/pages/RoutesPage.tsx` — rows 14–15.
19. `apps/ops-console/src/pages/ShipmentsPage.tsx` — rows 16–17.
20. `apps/ops-console/src/pages/UnauthorizedPage.tsx` — row 18.
21. `apps/ops-console/src/components/CsvUploadPanel.tsx` — row 19.
22. `apps/ops-console/src/components/RouteOptimizerForm.tsx` — row 21 only (row 20 stays).
23. `apps/ops-console/src/components/Layout.smoke.test.tsx` — ADDITIVE cases only (RouteFallback skeleton output, PageTransition presence); no existing assertion touched.

**Explicitly NOT modified:** `App.tsx`, `main.tsx`, `components/ui/Dialog.tsx`, `components/ui/StatusBadge.tsx`, all `shell/*` components, `ActivationBanner.tsx`, `ProtectedRoute.tsx`, `ErrorBoundary.tsx`, `context/AuthContext.tsx`, `services/api.ts`, `hooks/useLiveUpdates.ts`, `hooks/queries.ts`, `App.composition.guard.test.ts`.

## 5. Strict import / dependency map

### 5.1 Existing files — required new imports
- `Layout.tsx` adds exactly two imports: `PageTransition` from `./PageTransition` and `ScrollManager` from `./ScrollManager`. All existing imports unchanged. `RouteFallback` export signature unchanged. **The exact opening tag `<Suspense fallback={<RouteFallback />}>` must be preserved verbatim** — `App.composition.guard.test.ts` asserts it; `PageTransition` slots between that tag and `<Outlet />`.
- `App.tsx`: no changes, no new imports (`RouteFallback` import line must stay `import { Layout, RouteFallback } from './components/Layout';`).

### 5.2 New modules — interfaces and imports
- `PageTransition.tsx`: imports `useLocation` from `react-router-dom`, `useEffect`/`useRef` from `react`, `type ReactNode` from `react`. Props: `{ children: ReactNode }`. Contract:
  - Renders `<div key={pathname} className={animate ? 'fp-page-fade' : undefined}>{children}</div>`.
  - `animate` derived from a `useRef` flag initialized `true`, set to `false` in a mount-only `useEffect`. Initial render emits the div WITHOUT `fp-page-fade`; the flag flips after the first commit, so every subsequent pathname change re-mounts the keyed div WITH the class while same-pathname renders re-use the mounted div (no replay). StrictMode-safe: the ref is only written in the effect (never during render).
  - The wrapper div carries no layout classes (`main`'s `space-y-5` keeps one child → no visual change).
- `scrollPositions.ts`: zero imports. Exports `createScrollPositions(): ScrollPositions` — factory returning `{ save(path: string, y: number): void; get(path: string): number | undefined; clear(): void }` backed by a fresh `Map<string, number>` per call (no module-level mutable state → SSR- and test-safe).
- `ScrollManager.tsx`: imports `useEffect`/`useRef` from `react`, `useLocation`/`useNavigationType` from `react-router-dom`, `createScrollPositions` from `../services/scrollPositions`. Renders `null`. Behavior contract:
  - `const store = useRef<ScrollPositions>` lazy-initialized once (created exactly once per app lifetime).
  - Effect A (mount, deps `[]`): if `typeof window === 'undefined'` return; attach passive `scroll` listener; debounce ~100ms; save under the CURRENT pathname; remove listener on cleanup.
  - Effect B (deps `[pathname, navigationType]`): `POP` → `window.scrollTo(0, store.get(pathname) ?? 0)`; otherwise → `window.scrollTo(0, 0)`.
  - No other global writes; no `history.scrollRestoration` mutation.

### 5.3 Removed/moved symbols
Nothing is moved across files; the batch only removes CSS classes/inline styles (inventory §3.2) and adds the two new modules. All class-string edits are local; no type, field, or handler is relocated, renamed, or dropped. `PageHeader`, `Panel`, `MetricTile` keep their full existing prop interfaces and all other classes.

## 6. Acceptance checkpoints (NB-57 / NB-58 verbatim → evidence)

| Ticket | Verbatim criterion | Implementation evidence | Test evidence |
|---|---|---|---|
| NB-57.1 | "When the operator switches pages, the new page content fades in once, briefly (roughly a tenth of a second) and subtly." | `PageTransition` keyed div + `.fp-page-fade` (140ms `fadeIn` ease-out `both`); one fade per pathname change | `PageTransition.test.tsx` (class present on nav, absent on first render); `motion.guard.test.ts` |
| NB-57.2 | "Panels, cards, and rows never replay individual entrance animations during a page switch." | Inventory §3.2: all mount-entrance classes/delays removed; `.fp-row` baked animation stripped; only state-change animations remain | `motion.guard.test.ts` scans every src file with allowlist = `index.css` + `RouteOptimizerForm.tsx` (container only) |
| NB-57.3 | "If the operator has reduced motion enabled at the operating-system level, no fade is shown at all." | Existing `prefers-reduced-motion` block zeroes `animation-duration` for `.fp-page-fade` | `motion.guard.test.ts` asserts block present and `.fp-page-fade` animated via `fadeIn` |
| NB-58.1 | "When the operator returns to a page with the browser's back action, the page opens at the scroll position they left, not at the top." | `ScrollManager` Effect B on `POP` → `scrollTo(0, saved ?? 0)`; save-on-scroll keeps positions fresh | `scrollPositions.test.ts` (store roundtrip); `ScrollManager.test.tsx` source guards (POP branch) |
| NB-58.2 | "Moving forward to a new page starts at the top of that page." | `PUSH`/`REPLACE` → `scrollTo(0, 0)` (incl. catch-all `<Navigate replace />`) | `ScrollManager.test.tsx` source guards (non-POP branch → 0) |
| NB-58.3 | "The first time a page loads, the operator sees a calm placeholder built from the console's visual language — never a bare text line." | `RouteFallback` = `fp-nested-surface` + `.skeleton` blocks + `role="status"` + sr-only copy | `Layout.smoke.test.tsx` additive case: SSR HTML contains `skeleton` classes and sr-only "Loading workspace surface..." |

## 7. Test plan (node env — `renderToString` cannot run effects; window absent)

1. `motion.guard.test.ts` (new, mirrors `App.composition.guard.test.ts` — `SRC_DIR` via `import.meta.url`, SELF-excluded, recursion over `src`):
   - `animationDelay` and `stagger-` appear in ZERO files under `src` (excluding the guard file itself).
   - `animate-fade-in|animate-scale-in|animate-slide-up` appear ONLY in `index.css` (utility definitions + dialog classes) and `components/RouteOptimizerForm.tsx` (exactly the `animate-slide-up` container; file must NOT contain `animationDelay`).
   - `index.css` content guards: `.fp-row` block does NOT contain `animation:`; `.stagger-1` absent; `.fp-page-fade` present with `0.14s` and `fadeIn`; `.fp-dialog-surface` still references `scaleIn`; `.fp-dialog-overlay` still references `fadeIn`; `prefers-reduced-motion` block still present.
2. `scrollPositions.test.ts` (new): save/get roundtrip; `get` of unknown path → `undefined`; `clear` empties; two factory instances independent.
3. `ScrollManager.test.tsx` (new): `renderToString(<StaticRouter location="/"><ScrollManager/></StaticRouter>)` → renders empty, no crash; source-string guards: imports `useNavigationType`/`useLocation`, contains `'POP'` comparison, contains `scrollTo` with `0` fallback, imports `createScrollPositions` from `../services/scrollPositions`.
4. `PageTransition.test.tsx` (new): `renderToString` with `StaticRouter` → initial output contains the wrapper `<div>` WITHOUT `fp-page-fade` and WITH rendered children; source guards: contains `key={pathname}`, `fp-page-fade`, mount-only effect flipping the suppression flag.
5. `Layout.smoke.test.tsx` (additive): (a) nested-fallback SSR output contains `skeleton` class(es) and `role="status"` and the sr-only `Loading workspace surface...` span (existing assertion must remain green — copy preserved as sr-only text); (b) Layout SSR contains the `PageTransition` wrapper div; (c) `ScrollManager` presence — assert existing shell markers still present (`FreightPilot`, `data-testid="cap-pitch-banner"`, `<main`).
6. `App.composition.guard.test.ts`: MUST remain untouched and green.

## 8. Verification commands

From `apps/ops-console` (run all four):
- `npm run test` — vitest (all existing + new guards)
- `npm run typecheck` — `tsc --noEmit`
- `npm run lint` — eslint, zero warnings
- `npm run build` — `tsc --noEmit && vite build`

Repo hygiene: `git branch --show-current` must print `feat/console-navigation-ux`; `git status` should show only the §4 files staged by `@build` after `@qa` approval (single atomic commit; no intermediate commits).

Manual UAT checklist (human, after build passes): switch between /dashboard ↔ /alerts ↔ /shipments → exactly one subtle ~140ms fade of the whole content area, no per-row stagger, no shell flicker; scroll deep into /alerts → back → position restored; forward → top; reload mid-page → browser native restore; OS-level reduce-motion → no fade at all; first visit to a never-loaded page → skeleton surface, not bare text; login → dashboard landing → no fade.

## 9. Preservation notes

- **Copy:** every string on every surface preserved; `SHELL_CONTEXT_LABEL`/`SHELL_DESCRIPTOR` untouched; "Loading workspace surface..." retained verbatim (now sr-only).
- **Handlers/routes/role gates:** all page handlers, route elements, `allowedRoles` arrays, `<Navigate to="/" replace />` catch-all, `ProtectedRoute` composition — untouched (guarded by the untouched `App.composition.guard.test.ts`).
- **Data-testids:** none added or removed.
- **State animations kept:** `.fp-dialog-overlay`/`.fp-dialog-surface` (dialog open), `pulseRing` (MetricTile L29, StatusBadge L33), ProvidersPage error block, RouteOptimizerForm results container, `.animate-spin-slow` spinner, `.skeleton` shimmer.
- **Reduced-motion block** (index.css): byte-for-byte untouched.
- **Unrelated dirty files:** do not touch Phase-1/2 files (`api.ts`, `AuthContext`, `useLiveUpdates`, `internalNavGuard`, `shell/*`, `ActivationBanner`, `ProtectedRoute`, `ErrorBoundary`, `LoginPage`, `App.tsx`, `main.tsx`) or any surfaces outside `apps/ops-console`.
- **No new dependencies** (react-router-dom 6.23.1 already provides `useNavigationType`).
- **Known limitations (documented, accepted):** scroll map is in-memory (lost on hard reload → native browser restore); pathname-keyed only; POP restore can be clamped if page height shrank; `/login` and `/unauthorized` have no wrapper fade.
