# Phase Console UI Website Language 01 — Shell + Login (TECH-62 / TECH-63)

Status: LOCKED for `@build` on branch `feat/console-website-language-batch`. Delta on top of TECH-60 quiet pass. Source of truth: `docs/plans/console-ui-website-language-plan.md` sections 3, 4, 12, and 13. AST note: `graphify query` and `graphify explain` were attempted for `apps/ops-console/src/components/Layout.tsx`, `apps/ops-console/src/pages/LoginPage.tsx`, and `apps/ops-console/src/components/ui/PageHeader.tsx`, but the `graphify` CLI is not available in this environment, so the dependency map below is grounded in direct source reads.

## Goal for this phase

Deliver the shared shell alignment and login front-door pass so `apps/ops-console` reads like the same product as the website while preserving all existing auth behavior, route structure, and locked copy.

## Ground-truth decisions for this phase only

1. Phase boundary: this slice covers only TECH-62 and TECH-63. Do not pull dashboard hierarchy, route studio, receipts, admin verification, or unauthorized-page redesign work into this phase.
2. Delta rule: treat TECH-60 as the visual base layer. Keep the deep slate canvas, cyan-only accent family, border-first surfaces, mono numerals, and no-gradient/no-glow discipline.
3. Deepening decision: `apps/ops-console/src/components/Layout.tsx` is the shared shell module and currently holds sidebar data, mobile drawer control, brand block, top header, and utility footer in one implementation. Keep `Layout` as the external seam used by route modules, but move sidebar chrome and top-header chrome behind internal in-process modules so shell work stays localized.
4. Interface stability: `Layout`, `PageHeader`, and `Panel` must remain source-compatible for existing callers. Prefer zero page call-site edits; add only backward-compatible optional props if the build agent proves they are necessary.
5. Shell navigation invariants: preserve current group names, route paths, labels, route order, and short codes. Preserve the mobile drawer behavior and preserve the `CapPitchBanner` slot directly under the shared top shell.
6. Login behavior invariants: preserve `Navigate` redirect on authenticated load, preserve `login(identifier, password)`, preserve `registerApi(identifier, password, 'admin')`, preserve `signupUrl`, and preserve `bootstrapErrorMessage`. The change is hierarchy plus separated error presentation, not an auth-flow rewrite.
7. Copy lock: preserve every current shell and login string unless the approved source-of-truth plan explicitly requires reordering it. This phase should not invent new marketing copy, rename buttons, or change helper text.
8. Dependency rule: no new runtime dependencies and no new test dependencies. Use the existing Vite/Vitest and server-render test patterns already present in `apps/ops-console/src/pages/workspaceSurfaces.smoke.test.tsx`.

## Architecture context and phase seams

- `Layout` remains the deep module at the route seam. Deleting it would force every protected page to duplicate shell structure, so the seam stays and only its implementation deepens.
- `ShellSidebar` and `ShellHeader` become in-process adapters owned by `Layout`. They hide brand, navigation, identity, and mobile-shell presentation without changing route consumers.
- `PageHeader` and `Panel` remain the shared surface seam for page frames and nested work panels. This phase aligns their visual language so downstream pages keep leverage without page-by-page restyling.
- `LoginPage` remains the route seam. A small login feedback module is justified because deleting it would re-spread sign-in versus bootstrap error decisions back into the page implementation.

## Exact files to modify or create, with why each changes

- `apps/ops-console/src/index.css` — adjust shared shell and surface tokens/utilities so the shell, page headers, and login front door all use the same three-level surface model, radius discipline, and focus treatment defined by the source-of-truth plan.
- `apps/ops-console/src/components/Layout.tsx` — reduce the file to a shell orchestrator that owns drawer state, auth context access, `CapPitchBanner` placement, and the `children` seam while delegating sidebar and top-header presentation.
- `apps/ops-console/src/components/shell/ShellSidebar.tsx` — new module for the brand block, grouped navigation, active-route emphasis, utility footer, identity text, and logout affordance.
- `apps/ops-console/src/components/shell/ShellHeader.tsx` — new module for the shared top shell framing: context label, descriptor, role chip, user chip, and mobile-navigation trigger presentation.
- `apps/ops-console/src/components/ui/PageHeader.tsx` — align shared page-header spacing, action rhythm, and typography with the website-language frame without changing existing page imports.
- `apps/ops-console/src/components/ui/Panel.tsx` — align nested work-surface defaults so Phase 1 shell changes flow through a common primitive instead of page-level one-offs.
- `apps/ops-console/src/components/shell/ShellChrome.test.tsx` — new seam-level test file that pins shell grouping, branding, and identity framing directly against the new shell modules.
- `apps/ops-console/src/pages/LoginPage.tsx` — preserve handlers and copy while restructuring the front-door layout, CTA hierarchy, and separate sign-in versus bootstrap feedback channels.
- `apps/ops-console/src/components/login/LoginFeedbackPanels.tsx` — new pure presentation module that renders distinct sign-in and first-time-setup error surfaces from simple props so the separation is testable without a browser-only library.
- `apps/ops-console/src/components/login/LoginFeedbackPanels.test.tsx` — new test file for the feedback module’s empty state, single-error states, and dual-error state.
- `apps/ops-console/src/pages/workspaceSurfaces.smoke.test.tsx` — strengthen the locked login smoke assertions so the redesign proves the preserved primary action, signup action, and first-time bootstrap control remain visible.

## Strict import and dependency map for touched files

### `apps/ops-console/src/components/Layout.tsx`

- Keep the React imports for `useState` and `PropsWithChildren`.
- Keep `useAuth` from `../context/AuthContext`.
- Keep `CapPitchBanner` from `./ActivationBanner`.
- Remove the direct `react-router-dom` imports from this file after the sidebar split.
- Add a named import of `ShellSidebar` from `./shell/ShellSidebar`.
- Add a named import of `ShellHeader` from `./shell/ShellHeader`.
- `Layout` must continue exporting the same `Layout({ children })` interface so `App.tsx` stays untouched.

### `apps/ops-console/src/components/shell/ShellSidebar.tsx`

- Import `Link` and `NavLink` from `react-router-dom`.
- Import the `UserRead` type from `../../types/auth`.
- Export a single `ShellSidebar` module.
- Keep route metadata private to the module unless a second real consumer appears.
- Preserve the current route inventory exactly: `/`, `/routes`, `/shipments`, `/alerts`, `/planning`, `/upload`, `/receipts`, `/admin/receipts`, `/account`, `/providers`.
- Preserve the current group labels and codes exactly: `Operations` with `CT`, `RT`, `SH`, `EX`, `PL`; `Workspace` with `DI`, `PY`, `VQ`, `WS`, `IN`.

### `apps/ops-console/src/components/shell/ShellHeader.tsx`

- Import the `UserRead` type from `../../types/auth`.
- Accept user identity data and the mobile-open callback as props from `Layout`; do not re-read auth context inside this presentation module.
- Keep the shell descriptor text owned by the `Layout` seam unless the build agent extracts it as a private constant shared only by `Layout` and `ShellHeader`.

### `apps/ops-console/src/components/ui/PageHeader.tsx`

- Keep the React import for `ReactNode`.
- Keep the current prop names `eyebrow`, `title`, `description`, and `actions`.
- If an extra prop becomes necessary for spacing or framing, it must be optional and default-safe so all current caller files compile without changes.
- Current caller imports that must remain unchanged: `DashboardPage`, `RoutesPage`, `UploadPage`, `ShipmentsPage`, `AlertsPage`, `PlanningPage`, `AccountPage`, `ProvidersPage`, `ReceiptsPage`, and `AdminReceiptsPage`.

### `apps/ops-console/src/components/ui/Panel.tsx`

- Keep the existing prop contract and keep the local `joinClasses` helper unless the build agent centralizes class joining without changing caller imports.
- Current caller imports across page modules and shared modules should require no path changes in this phase.

### `apps/ops-console/src/pages/LoginPage.tsx`

- Keep `useState` from React and `Navigate` from `react-router-dom`.
- Keep `useAuth` from `../context/AuthContext`.
- Keep the `register` alias import from `../services/authApi`.
- Keep `bootstrapErrorMessage` from `../services/authErrors`.
- Add a named import of `LoginFeedbackPanels` from `../components/login/LoginFeedbackPanels`.
- Keep the local `getErrorMessage` helper unless the build agent moves it to a pure in-process helper with equivalent coverage. Do not change `bootstrapErrorMessage` behavior.

### `apps/ops-console/src/components/login/LoginFeedbackPanels.tsx`

- No data hooks, no router hooks, and no API imports.
- Export a single pure presentation module driven only by nullable sign-in and bootstrap error props.

### `apps/ops-console/src/components/shell/ShellChrome.test.tsx`

- Use `renderToString` from `react-dom/server`, `StaticRouter` from `react-router-dom/server`, and Vitest imports only.
- Import `ShellSidebar` from `./ShellSidebar`.
- Import `ShellHeader` from `./ShellHeader`.
- Import the `UserRead` type from `../../types/auth` for typed fixture data.
- Do not pull `QueryClientProvider`, auth context, or API mocks into this test unless the build agent expands the shell interfaces and can justify the extra seam complexity.

### `apps/ops-console/src/components/login/LoginFeedbackPanels.test.tsx`

- Use `renderToString` from `react-dom/server`, Vitest imports, and `LoginFeedbackPanels` from `./LoginFeedbackPanels`.

### `apps/ops-console/src/pages/workspaceSurfaces.smoke.test.tsx`

- Keep all existing mocks for auth, API, and receipt services intact.
- Keep current imports of `LoginPage`, `DashboardPage`, `ReceiptsPage`, `AdminReceiptsPage`, `AccountPage`, and `WorkspaceResetDangerZone`.
- Strengthen only the login assertion block; do not weaken or rewrite the activation, receipts, admin queue, or reset-flow assertions.

### Dependencies that must remain untouched in this phase

- `apps/ops-console/src/App.tsx` — route table and `allowedRoles` map stay unchanged.
- `apps/ops-console/src/components/ProtectedRoute.tsx` — auth gate behavior stays unchanged.
- `apps/ops-console/src/context/AuthContext.tsx` — auth provider contract stays unchanged.
- `apps/ops-console/src/services/authApi.ts` and `apps/ops-console/src/services/authErrors.ts` — transport and bootstrap-message behavior stay unchanged.

## Step-by-step execution for `@build`

1. Start from the current branch state without touching unrelated dirty or untracked files; keep the change set limited to the files listed above.
2. Split `Layout.tsx` first. Introduce `ShellSidebar.tsx` and `ShellHeader.tsx`, move the current sidebar and top-shell presentation into them, and keep `Layout` focused on auth access, drawer state, shell composition, and the `children` seam.
3. While moving shell markup, preserve the current navigation inventory, link destinations, group names, short codes, logout label, and identity text. Do not add or remove routes.
4. Update `index.css`, `PageHeader.tsx`, and `Panel.tsx` together so the shared shell, page-header frame, and nested work surfaces all inherit the same restrained website-language surface model. Keep the TECH-60 palette and do not reintroduce glow or gradient effects.
5. Add `ShellChrome.test.tsx` immediately after the shell split so the new seam is pinned before broader style tuning continues.
6. Add `LoginFeedbackPanels.tsx` as a pure presentation module for separate sign-in and bootstrap feedback surfaces.
7. Refactor `LoginPage.tsx` to track sign-in feedback and bootstrap feedback separately, clearing only the relevant channel per action, while preserving `onSubmit`, `onBootstrapInitialAdmin`, redirect behavior, and all current copy.
8. Rework the login composition into the approved front-door hierarchy: left promise rail and right sign-in surface on larger screens, single stacked flow on smaller screens, dominant sign-in action, clearly secondary product-site signup, and quieter first-time bootstrap control.
9. Add `LoginFeedbackPanels.test.tsx`, then strengthen the login assertions in `workspaceSurfaces.smoke.test.tsx`. Keep all existing smoke coverage for other surfaces intact.
10. Run the verification commands listed below from `apps/ops-console`. If downstream protected pages need alignment after the shared-surface changes, solve it through `PageHeader` or `Panel`, not by ad hoc page-specific restyling in this phase.

## Acceptance checkpoints tied to the source-of-truth plan

- TECH-62 / source plan section 3.1: the shared shell shows a distinct brand block, the `Operations` and `Workspace` navigation groups, and a utility footer with role, identity, and logout.
- TECH-62 / source plan section 3.1: active navigation is obviously emphasized and inactive navigation stays quiet but readable.
- TECH-62 / source plan section 3.2: the top shell reads as a framing device with context label, page descriptor, and role/user chips; the mobile navigation trigger still works.
- TECH-62 / source plan section 12 and section 13 step 1: the shell and page-header alignment flows through common primitives and shared tokens, not route-by-route experiments.
- TECH-63 / source plan section 4 desktop/mobile: login presents a split front door on desktop and a clean single-stack flow on mobile.
- TECH-63 / source plan section 4 form behavior: labels stay above inputs, the sign-in action remains dominant, the product-site account-creation path stays secondary, and the bootstrap control remains visibly first-time-only.
- TECH-63 / source plan section 4 error handling: sign-in failures and bootstrap failures render in distinct feedback surfaces instead of a single shared error box.
- Source plan section 12 hard rules: copy, handlers, auth flows, routing, role gates, and existing `data-testid` values remain preserved.

## Testing requirements

1. `apps/ops-console/src/components/shell/ShellChrome.test.tsx` must assert that the shell still renders `FreightPilot`, `Operations workspace`, both navigation group labels, the current route labels and short codes, the logout affordance, the `Control tower` context label, the shared descriptor text, and user identity chips when fixture user data is passed in.
2. `apps/ops-console/src/components/login/LoginFeedbackPanels.test.tsx` must cover the empty state, sign-in-only error state, bootstrap-only error state, and dual-error state, and must prove the two channels render as separate surfaces instead of one merged notice.
3. `apps/ops-console/src/pages/workspaceSurfaces.smoke.test.tsx` must strengthen the login smoke assertion block so it continues to find `Enter control tower`, the product-site `Create company account` path, and `Create initial admin (first-time setup)` after the redesign.
4. Existing activation-banner, receipts, admin-queue, account, and reset-flow smoke assertions must remain green without weakening any expectation tied to preserved surfaces outside this phase.
5. If the build agent moves the local `getErrorMessage` helper out of `LoginPage.tsx`, add a pure unit-test seam for it instead of deleting the current bootstrap-message coverage in `apps/ops-console/src/services/authErrors.test.ts`.

## Verification commands for `apps/ops-console`

Run these commands from `apps/ops-console`:

- `npm run test`
- `npm run typecheck`
- `npm run build`

## Notes on preserving copy, handlers, auth flows, routing, role gates, and `data-testid` values

- Preserve current shell and login copy, including product name, descriptor, promise text, button labels, signup text, bootstrap text, and all current error message strings produced by the auth helpers.
- Preserve all handlers: `login`, `logout`, `registerApi`, `onSubmit`, `onBootstrapInitialAdmin`, the mobile drawer open/close callbacks, and `CapPitchBanner` mount behavior.
- Preserve auth flows and redirects: authenticated users still leave `/login`, protected routes still rely on `ProtectedRoute`, and the login page still enters the workspace via the same cookie-backed auth path.
- Preserve routing and role gates: do not edit `App.tsx` paths, do not edit `allowedRoles`, and do not change any sidebar destination.
- Preserve the existing activation-related `data-testid` values. This phase must not rename or remove `activation-banner`, `activation-checklist`, `cap-pitch-banner`, or any `milestone-chip-*` identifier.
- Do not touch unrelated dirty or untracked files. Keep the implementation scoped to the files named in this blueprint.
