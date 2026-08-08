# Phase Console UI Website Language 03 — Remaining Pages: Upload, Shipments, Alerts, Planning, Providers, Unauthorized/Fallbacks

**Status:** LOCKED for `@build` on branch `feat/console-website-language-batch`. Delta on top of TECH-60 (quiet pass), TECH-62/63 (phase 01 shell + login, QA approved at `e70c939`), and the phase 02 workstation hierarchy pass (QA approved at `790f853`). Source of truth: `docs/plans/console-ui-website-language-plan.md` sections 11, 12, and 13. AST note: `graphify query` and `graphify explain` were attempted for the seven target files, but the `graphify` CLI is not available in this environment (confirmed again for this phase; same condition as phases 01 and 02), so the dependency maps below are grounded in direct source reads of every touched file and its current imports.

## Goal for this phase

Close out the console website-language pass by aligning the six remaining surfaces — Upload, Shipments, Alerts, Planning, Providers, and Unauthorized/fallbacks — to the shared surface system: calmer step rails and intake framing on Upload, denser operational rows and shell-aligned dialogs on Shipments/Alerts/Planning, a governance-first key structure on Providers, and dark-system fallback surfaces instead of generic defaults — while preserving every handler, state machine, locked string, role gate, and test-pinned behavior currently in place.

## Ground-truth decisions for this phase only

1. **Phase boundary:** this slice covers only source-plan section 11 (upload / shipments / alerts / planning / providers / unauthorized / fallbacks), which is source-plan §13 execution step 8. Do not pull dashboard, route studio, account, receipts, or admin-queue work back into this phase, and do not modify the phase-01 shell modules or any phase-02 surface.
2. **Delta rule:** treat TECH-60 as the visual base, TECH-62/63 as the shell/login layer, and `790f853` as the workstation-hierarchy layer. Keep the deep slate canvas, cyan-only accent family, three-level surface model (canvas → `fp-shell-surface` primary → `fp-nested-surface` nested), mono numerals for all data metrics, border-first surfaces, and the no-gradient / no-glow / no-decorative-motion discipline. The existing `glow-ring` utility remains the approved 2px cyan focus treatment and stays everywhere it currently appears.
3. **Shared-primitive rule:** all framing flows through the existing `PageHeader`, `Panel`, `MetricTile`, `StatusBadge`, `fp-shell-surface`, `fp-nested-surface`, `fp-pill`, and `fp-input` primitives. The six pages are the last remaining consumers that hand-roll the same input class string (`glow-ring min-h-12 rounded-2xl border border-slate-700 bg-slate-900/80 ...`) — that fork is resolved in this phase by adopting the shared `fp-input` component class (available since phase 01, with its own focus-visible treatment) everywhere an input, textarea, or select appears on these six pages. File inputs keep their `file:`-modifier additions stacked on the `fp-input` base.
4. **Radius rule:** every hard-coded `rounded-[20px]`, `rounded-[22px]`, `rounded-[28px]`, and `rounded-xl` currently on these six pages is radius soup per source-plan §2.3 (20px is explicitly named in the soup list) and is replaced by a token-backed treatment: nested surfaces and queue rows use `fp-radius-panel` (16px), the page header stays `fp-shell-surface`, and dialog frames use `fp-radius-hero` (24px). No page gets a bespoke radius.
5. **Queue-row rule:** shipments, alerts, planning, and providers all render row cards with the same repeated `rounded-xl border border-slate-800/60 bg-slate-900/40 p-4` recipe. Because the same densified row treatment is needed on four pages, one shared `fp-row` component class is added to the shared layer in `index.css` (per the phase-02 CSS rule: a shared density utility required in two or more pages is added once, never inlined per page) and used by all four pages.
6. **Dialog normalization rule (flagged decisions):** all four modal surfaces in the console — `DelayReasonDialog` (Shipments), `ResolveDialog` (Alerts), `RejectDialog` (Planning), and the `WorkspaceResetDangerZone` typed-confirmation modal — currently drift from the shared system in three ways: an arbitrary `rounded-[28px]` frame radius (danger zone uses a different `rounded-2xl`), a `backdrop-blur-sm` overlay with two different backdrop colors (`bg-slate-950/70` and `bg-black/60`), and a heavy `shadow-[0_32px_100px_rgba(2,12,20,0.6)]`. This phase introduces one shared presentation-only `Dialog` primitive and moves all four modals onto it:
   - **Radius token:** the dialog frame uses `fp-radius-hero` (24px), the same token as the shell surface, because a modal is a top-level framing surface rather than a nested panel. The alternative (16px `fp-radius-panel`) was considered and rejected for that reason. **Flagged for QA:** verify all four dialogs render a single frame radius with no residual `rounded-[28px]` / `rounded-2xl` drift.
   - **Backdrop treatment:** one shared overlay (`bg-slate-950/80`) with **no `backdrop-blur`** — the blur is removed from all four dialogs. **Flagged for QA:** this is the blur-drift resolution; no dialog may keep a blur or a per-dialog backdrop color.
   - **Shadow treatment:** the heavy drop shadow is removed from the three inline dialogs; definition comes from the border-first frame only (matching the danger-zone modal, which already has no heavy shadow). **Flagged for QA:** no dialog reintroduces a large blur-shadow.
   - **Accessibility:** the primitive renders `role="dialog"` and `aria-modal="true"` on the frame. The danger zone already has both (smoke-pinned) and keeps them; the three inline dialogs gain them. The primitive adds **no focus trap, no Escape handling, and no backdrop-click close** — those would be new handlers, which are out of scope.
   - **Motion and layering:** the overlay keeps `animate-fade-in` and the frame keeps `animate-scale-in` (approved lightweight motion, source-plan §2.5); `fixed inset-0 z-50 grid place-items-center p-4` is preserved.
   - **Semantic tone:** the danger-zone modal keeps its rose danger framing (border + confirm button), `ResolveDialog` keeps its emerald confirm (success semantics), `RejectDialog` keeps its rose confirm (danger semantics), and `DelayReasonDialog` keeps its cyan confirm (primary action). Tone is passed through the primitive's className seam, not by forking the frame.
7. **Alerts severity side-stripe rule (flagged violation, must be resolved):** the `severityBorderAccent` map in `AlertsPage` paints a 3px colored left border (`border-l-[3px] border-l-rose-500/60` etc.) onto alert rows. This side-stripe treatment violates the shared border-first, three-level surface rule (no stripe accents on nested surfaces — the same rule that drove the phase-02 dashboard exception-queue rows to plain dense rows). The map is deleted in this phase; severity is conveyed by the existing severity `StatusBadge` (label + tone) that already renders on each row. **Flagged for QA:** no `border-l-*` colored stripe may remain on any alert row, and the shared `fp-row` class carries no stripe variant.
8. **Alerts palette rule (additional violation found on the same page):** the `Auto-Resolve` action button is styled with violet (`border-violet-500/30 text-violet-200`), which violates source-plan §2.1 (no purple). It is restyled to the cyan accent outline used by the other alert actions. The `Scan for exceptions` header action is currently emerald and reads as a primary action; it becomes the cyan primary treatment (emerald is reserved for resolve/success semantics). Button labels (`Scan for exceptions`, `Scanning...`, `Auto-Resolve`) are preserved verbatim.
9. **Copy rule:** every string currently rendered by the touched pages is preserved verbatim. The only permitted text-level changes are structural reorderings of already-existing labels, and one flagged exception: the duplicated `Step {n}` eyebrows in `CsvUploadPanel` (which repeat the numbering already shown by the page-level import-sequence rail) are removed so a single calm step rail survives — this is the §11 "calmer step rail, clearer import sequence" intent. No new marketing copy or rewritten helper text.
10. **Sorting rule (Alerts triage rhythm):** alert rows are re-ordered in render by a stable presentation sort — severity rank (critical → high → medium → low), then `created_at` descending — so the highest-severity work is always visible first under the active status filter. This is render-time ordering only: `loadAlerts`, the `statusFilter` state, the filter select, and all mutation handlers are unchanged; server data is never mutated.
11. **Component contract rule:** `ActivationBanner` (including `mode="checklist"` on `/upload`), `PageHeader`, `Panel`, `MetricTile`, `StatusBadge`, and the phase-01 shell modules keep their existing interfaces and are not modified in this phase. `WorkspaceResetDangerZone` keeps its exact props (`organizationName`, `isAdmin`, `defaultOpen`) and its external behavior; only its internal modal frame moves to the shared `Dialog` primitive.
12. **Dependency rule:** no new runtime dependencies and no new test dependencies. Tests continue to use the existing Vitest server-render patterns in `workspaceSurfaces.smoke.test.tsx`; the existing `services/api` mock already covers the `logisticsApi` functions these pages call (confirmed: `logisticsApi` routes through the mocked `api` client), so new smoke blocks are feasible without new mocks.

## Ground-truth decisions per surface

### Surface 1 — Upload (source plan §11)

- Keep the `PageHeader` (eyebrow `Data intake`, current title and description) and keep `<ActivationBanner mode="checklist" />` mounted directly below it — the checklist state machine, chip rhythm, next-step emphasis, and `banner.visible` gating are locked; the page only frames it.
- **Calmer step rail:** the `Import sequence` / `Recommended onboarding order` panel keeps its exact header copy, but its five equal-weight card blocks (`rounded-[20px] ... px-4 py-4` in a five-column grid) become a quiet horizontal rail: five compact `fp-pill`-based items, each showing the existing `Step {n}` eyebrow and the existing step name (`Warehouses`, `Items`, `Fleet`, `Inventory`, `Orders`), with no card chrome, no grid-of-cards repetition, and no fourth surface treatment. The rail is the single source of step numbering on the page.
- **Intake panel:** `CsvUploadPanel` keeps its two-column grid, its five spec cards (titles, hints, action labels, key chips), and all upload behavior, but: each card moves to the shared `fp-row` treatment (or `fp-nested-surface` where the build agent prefers the panel frame) instead of `rounded-xl ... bg-slate-900/40`; the duplicated `Step {n}` eyebrow is removed from each card (decision 9), leaving the key chip (`WAREHOUSES`, `ITEMS`, `FLEET`, `INVENTORY`, `ORDERS`); the file input adopts the `fp-input` base with its existing `file:`-modifier styling preserved; and the upload button keeps the full disabled logic and all three labels (`Uploading...`, `Writes locked (Free cap)`, per-spec action label).
- **Free-cap lock:** the `freeCapLocked` derivation from `activationQ.data?.free_cap?.locked` and its effect on the upload button (disabled + `Writes locked (Free cap)` label) are preserved exactly.

### Surface 2 — Shipments (source plan §11)

- Keep the `PageHeader` (eyebrow `Shipment board`, current title/description), the four `MetricTile` values (`Planned`, `In transit`, `Delayed`, `Delivered`) with their detail strings and tone thresholds, and the loading/error/empty-state copy.
- **Dialog alignment:** `DelayReasonDialog` moves onto the shared `Dialog` primitive with its exact props (`shipmentNo`, `defaultReason`, `onConfirm`, `onCancel`), its `autoFocus` textarea, its placeholder `Describe the delay reason...`, the `Cancel` / `Confirm delay` buttons and the disabled-until-reason rule. Only the frame/overlay treatment changes.
- **Calmer manual-entry form:** the single crowded five-column row becomes a labeled field group — each of the five existing fields (`Shipment No`, `Origin Code`, `Destination Code`, `SKU`, `Quantity`) gets a label above the input using the existing placeholder strings as the label text (structural reorder of existing copy, per decision 9), all inputs adopt `fp-input`, the origin/destination/SKU uppercase transforms and the quantity `min={1}` constraint stay, and the submit action becomes a dominant cyan primary button with the existing spinner and `Creating...` / `Create` labels. `onCreate` and the form-reset after success are unchanged.
- **Denser shipment rows:** each shipment card becomes a dense `fp-row` queue row: line one = `StatusBadge` + created-at timestamp; line two = `shipment_no` in the existing Space Grotesk emphasis; right-aligned mono lane (`origin_warehouse_code → destination_warehouse_code`, `sku · quantity units`); one quiet delay-note line with the exact `Delay note: ...` / `No delay reason logged for this shipment.` copy; and the compact `Mark in transit / Mark delayed / Mark delivered / Mark cancelled` pill row with the existing disabled logic. `statusTransitions` and `statusTone` are unchanged; the `hover-lift` and `animate-fade-in` treatments stay.

### Surface 3 — Alerts (source plan §11)

- Keep the `PageHeader` (eyebrow `Exception center`, current title/description) and the four `MetricTile` values (`Open`, `Acknowledged`, `Critical`, `High severity`) with their detail strings and tone thresholds. The header action `Scan for exceptions` restyles to the cyan primary treatment (decision 8), keeping its `Scanning...` spinner state and handler.
- **Sharper queue rows:** alert cards become dense `fp-row` queue rows with no side-stripe (decision 7): line one = severity `StatusBadge` + status `StatusBadge` + `alert_type`; title; message; created-at timestamp; and the action pill row (`Acknowledge`, `Resolve`, `Auto-Resolve`) with the existing disabled logic and the `Auto-Resolve` violet → cyan restyle (decision 8). `severityBorderAccent` is deleted; `severityTone` and `statusTone` stay.
- **Triage rhythm:** rows render under the active `statusFilter` ordered by severity rank then `created_at` descending (decision 10). The filter select, `loadAlerts(filter)` flow, `open/acknowledged/resolved/all` options, and the `No alerts` / `No alerts for the selected filter.` empty states are unchanged.
- **Dialog alignment:** `ResolveDialog` moves onto the shared `Dialog` primitive with its exact props (`alertTitle`, `onConfirm`, `onCancel`), the optional-note textarea and placeholder, and the emerald `Resolve alert` confirm. The manual-entry panel keeps its title/description, moves its inputs to `fp-input`, and keeps `onCreate`, the severity select (low/medium/high/critical options), and the `Create alert` button.

### Surface 4 — Planning (source plan §11)

- Keep the `PageHeader` (eyebrow `Planning`, current title/description), the four `MetricTile` values (`Horizon`, `Pending`, `Approved`, `Rejected`) with detail strings and tone thresholds, the generate panel (`Run replenishment planning` + `Horizon (weeks)` labeled input with `id="horizon"` + `Generate replenishment suggestions` / `Generating...` button), the error panel, and the skeleton loading state.
- **Dialog alignment:** `RejectDialog` moves onto the shared `Dialog` primitive with its exact props (`sku`, `onConfirm`, `onCancel`), the `Need manual review` default, the placeholder `Reason for rejection...`, and the rose `Reject plan` confirm with its disabled rule.
- **Stronger approval-board hierarchy, less repeated-card feeling:** the `Approval board` / `Current replenishment plans` panel keeps its header copy but splits its content into two bands: an **action band** for `pending_approval` plans (dominant presence, dense `fp-row` rows showing the status badge, warehouse code, SKU, the mono stats row `Avg demand: x / Suggested: x / Horizon: xw`, the rationale line, and the admin-only `Approve` / `Reject` pills), followed by a quieter **history band** for `approved` and `rejected` plans (same `fp-row` structure, muted chrome, rejection-reason line). The admin role gate (`user?.role === 'admin'` gating both actions on pending plans only) and the non-admin fallback line (`rejection_reason` / `No rejection reason recorded.`) are preserved. Numeric values in the stats row render mono per source-plan §2.4.
- Keep `onGenerate`, `onApprove`, `onRejectConfirm`, `loadPlans`, the horizon input handler, and the `No plans yet` / `Generate replenishment suggestions using the form above.` empty state.

### Surface 5 — Providers (source plan §11)

- Keep the `PageHeader` (`Carrier Integrations` title and description — no eyebrow is added, per copy lock) and the two-column layout with the `Active Connections` / `Provider Keys` panel on the left and the `New Integration` / `Add Credentials` panel on the right.
- **Governance-first key structure:** the key list moves from mini-cards (`rounded-[20px]`) to a clean governance row structure on the shared `fp-row` class: each row shows `provider_name` + `key_name` with the status `StatusBadge` on one line, the `masked_key` in mono on the next, and the `REVOKE` pill for active keys when `isAdminOrOwner`. The `Loading keys...`, error surface, and `No provider keys configured. Add one to get started.` states are preserved.
- **Form:** the three labeled fields (`Provider Code`, `Key Name / Alias`, `API Key / Secret` with the password input and masked placeholder) adopt `fp-input`, keeping their labels, required attributes, and placeholders; the `testError` channel, the `Validating connection...` / `Securely Save Key` button labels, and the submit disabled logic are unchanged.
- Keep `fetchKeys`, `onSubmit` (create → immediate test → clear form → refresh), `onRevoke` with its `window.confirm`, the `alert` error channel, and the `isAdminOrOwner` role gate.

### Surface 6 — Unauthorized and fallbacks (source plan §11)

- **`UnauthorizedPage`:** currently a light-theme white card (`bg-white ... ring-slate-200` with dark text) — the one surface completely outside the design system. It is rebuilt as a centered `fp-shell-surface` frame on the dark canvas with the exact existing copy (`Unauthorized`, `You do not have permission to access this page.`) in the standard slate text treatments. The `/unauthorized` route stays standalone (no `Layout` wrapper) and the page supplies its own framing.
- **`RouteFallback` in `App.tsx`:** the Suspense fallback (`Loading workspace surface...`) swaps its hand-rolled `rounded-2xl border border-slate-800/60 bg-slate-900/40` surface for the `fp-nested-surface` class. Copy, the lazy route table, `allowedRoles`, and all route elements are untouched.
- **`ErrorBoundary` and `PageErrorBoundary`:** the two fallback branches swap their hard-coded `rounded-2xl` radii for the `fp-radius-panel` token (keeping the semantic red/danger borders, the icon blocks, all copy, and the `Try again` / crash-copy handlers). These are the last generic-default fallback surfaces in the console.

## Exact files to modify or create, with why each changes

- `apps/ops-console/src/components/ui/Dialog.tsx` — **new** shared presentation-only modal primitive (overlay + border-first frame + optional eyebrow/title/description + children + footer/actions + className tone seam), carrying `role="dialog"` and `aria-modal="true"`. Exists so all four dialogs align to one surface treatment instead of four drifted implementations.
- `apps/ops-console/src/index.css` — add three shared component-layer classes once: `fp-dialog-overlay` (fixed inset-0 z-50 grid place-items-center p-4, `bg-slate-950/80`, no blur, fade-in), `fp-dialog-surface` (border-first frame, `fp-radius-hero`, scale-in), and `fp-row` (dense nested row: border, `fp-radius-panel`, quiet background, hover transition). No palette, motion, or focus changes.
- `apps/ops-console/src/pages/UploadPage.tsx` — reframe the import-sequence panel as a calm five-item rail so the page opens with one quiet step strip; banner mount and header stay.
- `apps/ops-console/src/components/CsvUploadPanel.tsx` — align spec cards to `fp-row`, drop the duplicated per-card `Step {n}` eyebrow, adopt `fp-input` for the file inputs; upload logic, free-cap lock, and all labels preserved.
- `apps/ops-console/src/pages/ShipmentsPage.tsx` — move `DelayReasonDialog` to the `Dialog` primitive, densify rows onto `fp-row`, and rebuild the manual-entry form as a calm labeled group with a dominant primary action.
- `apps/ops-console/src/pages/AlertsPage.tsx` — delete the severity side-stripe map, densify rows onto `fp-row`, add the render-time severity/recency sort, restyle `Auto-Resolve` (violet → cyan) and the header scan action (emerald → cyan), and move `ResolveDialog` to the `Dialog` primitive.
- `apps/ops-console/src/pages/PlanningPage.tsx` — move `RejectDialog` to the `Dialog` primitive and split the approval board into a dominant pending action band plus a quieter history band with mono stats.
- `apps/ops-console/src/pages/ProvidersPage.tsx` — rebuild the key list as governance rows on `fp-row` with mono masked keys and adopt `fp-input` for the credential form.
- `apps/ops-console/src/pages/UnauthorizedPage.tsx` — rebuild the light-theme card as a centered dark `fp-shell-surface` frame with the existing copy.
- `apps/ops-console/src/App.tsx` — only the `RouteFallback` surface class swap (copy, routes, roles untouched).
- `apps/ops-console/src/components/ErrorBoundary.tsx` — radius-token swaps in both fallback branches only.
- `apps/ops-console/src/components/WorkspaceResetDangerZone.tsx` — migrate only the internal typed-confirmation modal frame onto the `Dialog` primitive (rose tone seam); props, copy, typed-input behavior, aria attributes, and the `useResetWorkspace` flow are unchanged.
- `apps/ops-console/src/pages/workspaceSurfaces.smoke.test.tsx` — add smoke blocks for Upload, Shipments, Alerts, Planning, Providers, and Unauthorized against the existing mocks; all existing assertions remain intact.

## Strict import and dependency map for touched files

### `apps/ops-console/src/components/ui/Dialog.tsx` (new)

- Import only `type { PropsWithChildren, ReactNode }` from `react`.
- Export a single named `Dialog` module. No hooks, no router, no API imports, no data fetching.
- Contract: optional `eyebrow`, `title`, `description`, `children`, optional `actions`/`footer` node, optional `className` for tone seams (rose danger frame), optional `bodyClassName`. Defaults must make a bare `<Dialog>` render a valid overlay + frame.

### `apps/ops-console/src/index.css`

- No new imports. Add the three classes to the existing `@layer components` block (`fp-dialog-overlay`, `fp-dialog-surface`, `fp-row`) using the existing `--fp-*` tokens only.

### `apps/ops-console/src/pages/UploadPage.tsx`

- Keep the current imports exactly: `ActivationBanner` from `../components/ActivationBanner`, `CsvUploadPanel` from `../components/CsvUploadPanel`, `PageHeader` from `../components/ui/PageHeader`, `Panel` from `../components/ui/Panel`. No new imports; markup re-framing only.

### `apps/ops-console/src/components/CsvUploadPanel.tsx`

- Keep the current imports exactly: `useState` from `react`; `useQueryClient` from `@tanstack/react-query`; `useActivationState` from `../hooks/queries`; `uploadFleetAssetsCsv`, `uploadInventoryCsv`, `uploadItemsCsv`, `uploadOrdersCsv`, `uploadWarehousesCsv` from `../services/logisticsApi`.
- Keep `UploadKind`, `UploadSpec`, and the `uploadSpecs` array verbatim (titles, hints, action labels, keys). Keep `files`, `results`, `activeKind`, `queryClient`, and the `freeCapLocked` derivation. Keep `submit(kind)` including the per-kind dispatch, the result-string format (`{kind} import: processed=..., created=..., updated=..., errors=...`), the failure format, the `queryClient.invalidateQueries({ queryKey: ['activation'] })` NB-30.4 refresh, and the `finally` clear.

### `apps/ops-console/src/pages/ShipmentsPage.tsx`

- Keep the current imports exactly: `FormEvent`, `useEffect`, `useState` from `react`; `MetricTile`, `PageHeader`, `Panel`, `StatusBadge` from `../components/ui`; `createShipment`, `listShipments`, `updateShipmentStatus` from `../services/logisticsApi`; `Shipment`, `ShipmentStatus` from `../types/api`.
- Add a named import of `Dialog` from `../components/ui/Dialog` for the local `DelayReasonDialog`.
- Keep `statusTransitions`, `statusTone`, the local `SkeletonBlock`, and the page state (`shipments`, `error`, `loading`, `creating`, `delayDialog`, `form`) and all handlers (`loadShipments`, `onCreate`, `onStatusUpdate` with the delayed branch, `onDelayConfirm`) verbatim.

### `apps/ops-console/src/pages/AlertsPage.tsx`

- Keep the current imports exactly: `FormEvent`, `useEffect`, `useState` from `react`; `MetricTile`, `PageHeader`, `Panel`, `StatusBadge` from `../components/ui`; `acknowledgeAlert`, `autoResolveAlert`, `createAlert`, `listAlerts`, `resolveAlert`, `scanAlerts` from `../services/logisticsApi`; `Alert`, `AlertStatus`, `AlertSeverity` from `../types/api`.
- Add a named import of `Dialog` from `../components/ui/Dialog` for the local `ResolveDialog`.
- Delete the local `severityBorderAccent` map (decision 7). Keep `severityTone` and `statusTone`, the `statusFilter` state and its select handler, and all handlers (`loadAlerts`, `onCreate`, `onScan`, `onAcknowledge`, `onResolveConfirm`, `onAutoResolve`) verbatim.

### `apps/ops-console/src/pages/PlanningPage.tsx`

- Keep the current imports exactly: `useEffect`, `useState` from `react`; `MetricTile`, `PageHeader`, `Panel`, `StatusBadge` from `../components/ui`; `useAuth` from `../context/AuthContext`; `approveReplenishmentPlan`, `generateReplenishmentPlans`, `listReplenishmentPlans`, `rejectReplenishmentPlan` from `../services/logisticsApi`; `ReplenishmentPlan` from `../types/api`.
- Add a named import of `Dialog` from `../components/ui/Dialog` for the local `RejectDialog`.
- Keep `statusTone`, the page state (`plans`, `horizon`, `error`, `loading`, `isGenerating`, `rejectDialog`), and all handlers (`loadPlans`, `onGenerate`, `onApprove`, `onRejectConfirm`) verbatim, including the `useAuth` admin gate.

### `apps/ops-console/src/pages/ProvidersPage.tsx`

- Keep the current imports exactly: `useEffect`, `useState` from `react`; `PageHeader`, `Panel`, `StatusBadge` from `../components/ui`; `listProviderKeys`, `createProviderKey`, `testProviderKey`, `revokeProviderKey` from `../services/logisticsApi`; `ProviderKey` from `../types/api`; `useAuth` from `../context/AuthContext`.
- Keep all state and handlers (`fetchKeys`, `onSubmit`, `onRevoke` with `window.confirm`) and the `isAdminOrOwner` derivation verbatim. No new imports.

### `apps/ops-console/src/pages/UnauthorizedPage.tsx`

- No imports today and none are required for the restyle (plain markup on the shared classes). Copy stays exactly `Unauthorized` and `You do not have permission to access this page.`

### `apps/ops-console/src/App.tsx`

- Keep every import, the lazy route table, the `allowedRoles` map, and every route element. Only the `RouteFallback` function body's surface classes change.

### `apps/ops-console/src/components/ErrorBoundary.tsx`

- Keep the `Component` import, the `Props`/`State` interfaces, both fallback branches' copy, the icon SVGs, and the `setState` retry handler. Only radius classes change (token swap).

### `apps/ops-console/src/components/WorkspaceResetDangerZone.tsx`

- Keep the current imports: `useState` from `react`; `Panel` from `./ui/Panel`; `useResetWorkspace` from `../hooks/queries`. Add a named import of `Dialog` from `./ui/Dialog` for the internal modal.
- Keep the component signature and the `resetMutation`, `resetModalOpen`, `typedWorkspaceName` state, the `!isAdmin` early return, and the full `resetMutation.mutate(typedWorkspaceName)` flow.

### `apps/ops-console/src/pages/workspaceSurfaces.smoke.test.tsx`

- Keep all existing mocks (`authUserState`, `AuthContext`, `receiptsApi`, `api`, `leaflet`, `react-leaflet`), the `seededActivationState` / `preloadedDashboardClient` fixtures, and every existing `it` block untouched.
- Add named imports of `UploadPage`, `ShipmentsPage`, `AlertsPage`, `PlanningPage`, `ProvidersPage`, and `UnauthorizedPage` from `./` for the new blocks. The existing `services/api` mock already resolves `get` to `{ data: [] }`, which the `logisticsApi`-based pages tolerate in SSR (initial render shows the loading skeleton plus header/panel copy).

### Dependencies that must remain untouched in this phase

- `apps/ops-console/src/App.tsx` — route table, `allowedRoles` map, lazy imports, and all route elements stay unchanged (only `RouteFallback` surface classes change).
- `apps/ops-console/src/components/ProtectedRoute.tsx`, `context/AuthContext.tsx`, `services/*` — auth gate, provider contract, and transport layers stay unchanged.
- `apps/ops-console/src/components/ActivationBanner.tsx` — banner state machine, checklist mode, milestone chips, cap-pitch hierarchy, and all testids stay unchanged; the page-level mount on `/upload` stays between header and import rail.
- `apps/ops-console/src/components/Layout.tsx`, `components/shell/*` — phase-01 shell modules stay unchanged.
- `apps/ops-console/src/components/ui/PageHeader.tsx`, `Panel.tsx`, `MetricTile.tsx`, `StatusBadge.tsx` — phase-01/02 primitives stay unchanged.
- Phase-02 surfaces — `DashboardPage`, `RoutesPage`, `RouteOptimizerForm`, `AccountPage`, `ReceiptsPage`, `AdminReceiptsPage` stay unchanged.

## Step-by-step execution for `@build`

1. Start from the current branch state without touching any unrelated dirty or untracked file; scope the change set to the twelve files listed above.
2. Add the three shared classes (`fp-dialog-overlay`, `fp-dialog-surface`, `fp-row`) to `index.css` first, then create `Dialog.tsx`, so the pages and modals can adopt them in one pass.
3. **Dialogs:** migrate `DelayReasonDialog`, `ResolveDialog`, `RejectDialog`, and the danger-zone modal onto `Dialog` in one coordinated change; verify the four dialogs share the frame radius, the single non-blurred overlay, and the border-first frame, and that the three inline dialogs now emit `role="dialog"` + `aria-modal="true"`.
4. **Surface 1 — Upload:** reframe the import-sequence rail, then align `CsvUploadPanel` cards/inputs; confirm the activation checklist banner mount position and the free-cap disabled label are untouched.
5. **Surface 2 — Shipments:** dialog migration, dense `fp-row` queue rows, and the calm labeled entry form with the dominant primary submit.
6. **Surface 3 — Alerts:** delete the side-stripe map, restyle the two flagged buttons, add the render-time sort, densify rows, migrate the dialog, and align the form inputs.
7. **Surface 4 — Planning:** dialog migration, then the two-band approval board (pending action band dominant, history band quiet) with mono stats; confirm the admin-only action gating still applies to pending plans only.
8. **Surface 5 — Providers:** governance row structure for keys and `fp-input` adoption on the credential form; confirm the `REVOKE` gate (active keys only, admin/owner only) and the `window.confirm` flow.
9. **Surface 6 — Fallbacks:** rebuild `UnauthorizedPage` on the dark system, swap the `RouteFallback` surface class, and apply the radius-token swaps in `ErrorBoundary`.
10. Extend `workspaceSurfaces.smoke.test.tsx` with the six new blocks; do not weaken any existing expectation.
11. Run the verification commands below from `apps/ops-console` and resolve any alignment drift through the shared classes or primitives — never through per-page visual one-offs outside the design language.

## Acceptance checkpoints tied to the source-of-truth plan

- Source plan §11 Upload: the page opens with one calm step rail; the import sequence reads in a single clear order; the intake panel sits on the same surface system as every other nested surface; the activation checklist behavior on `/upload` (position, mode, milestone chips, next-step emphasis) is unchanged; the free-cap lock still disables uploads with the `Writes locked (Free cap)` label.
- Source plan §11 Shipments: the delay dialog matches the shared dialog treatment (hero radius, single non-blurred overlay, border-first frame, `role="dialog"`/`aria-modal="true"`); shipment rows are denser and scannable with mono lane data; the manual-entry form is calm with labels above inputs and one dominant primary action.
- Source plan §11 Alerts: queue rows are sharper with no side-stripe accents; severity reads from the severity badge; the queue is triaged (highest severity first under the active filter); the resolve dialog matches the shared treatment; no violet remains anywhere on the page.
- Source plan §11 Planning: the reject dialog matches the shared treatment; the approval board has a clear hierarchy (pending action band outranks the approved/rejected history band); the repeated-card feeling is gone; admin-only approval actions are preserved.
- Source plan §11 Providers: the page is governance-first — keys read as a clean row structure with mono masked keys and status badges; the credential form adopts the shared input treatment; the revoke flow and role gate are intact.
- Source plan §11 Unauthorized/fallbacks: the unauthorized page and the loading/error fallbacks inherit the same dark border-first system — no light-theme card, no generic defaults.
- Source plan §12 hard rules: copy (including every string on the six pages and the four dialogs), handlers, auth flows, routing, role gates, and all test-pinned attributes (`role="dialog"`, `aria-modal="true"`, `aria-label="Workspace name confirmation"`, `disabled` on the typed-confirmation input, `id="horizon"`) are preserved; no decorative gradients, no glow shadows, no new dependencies; shared surfaces flow through the common primitives/classes.
- Source plan §14 acceptance standard: the six surfaces feel like the same product as the website and operators can scan faster, not slower; no page feels like it belongs to another design system.

## Testing requirements

1. `apps/ops-console/src/pages/workspaceSurfaces.smoke.test.tsx` must keep every existing assertion green, including login, dashboard skeleton, receipts, admin queue, reversals, fraud-chip absence, seeded dashboard/activation, Route Studio, account escalation contact, and both danger-zone blocks.
2. Add a smoke block for `UploadPage` asserting the page title, `Recommended onboarding order`, and the `Upload Warehouses` / `Upload Items` / `Upload Fleet Assets` / `Upload Inventory` / `Upload Orders` action labels (the unseeded activation query resolves to an unlocked free cap, so the action labels render).
3. Add a smoke block for `ShipmentsPage` asserting `Track movement health across every lane`, `Create a shipment`, `Shipment lifecycle`, and the `Mark ` action labels.
4. Add a smoke block for `AlertsPage` asserting `Triage, assign, and close operational risk quickly`, `Create a manual operator alert`, `Alert queue`, and `Scan for exceptions`.
5. Add a smoke block for `PlanningPage` asserting `Generate and approve replenishment actions`, `Run replenishment planning`, `Horizon (weeks)`, and the `Approval board` eyebrow (visible in the loading skeleton).
6. Add a smoke block for `ProvidersPage` asserting `Carrier Integrations`, `Provider Keys`, `Loading keys...`, and `Securely Save Key`.
7. Add a smoke block for `UnauthorizedPage` asserting `Unauthorized` and `You do not have permission to access this page.` and asserting the light-theme fragment is gone (for example, the rendered HTML no longer contains the `bg-white` surface class).
8. Existing `ShellChrome.test.tsx`, `ActivationBanner.test.tsx`, `accountUsageUtils.test.ts`, `authErrors.test.ts`, and `api.test.ts` suites must remain green with no edits.

## Verification commands for `apps/ops-console`

Run these commands from `apps/ops-console`:

- `npm run test`
- `npm run typecheck`
- `npm run build`

## Notes on preserving copy, handlers, auth flows, routing, role gates, and `data-testid` values

- **Copy:** preserve every string on the six pages and in the four dialogs, including the upload spec titles/hints/action labels, the import-rail step names, the free-cap label, shipment form placeholders and status-action labels, alert severity/status option text and action labels, planning horizon label, generate/approve/reject labels and the `Need manual review` default, the rejection-reason empty line, provider form labels, `Securely Save Key` / `Validating connection...`, `REVOKE`, all empty/error/loading states (`No shipments yet`, `No alerts`, `No plans yet`, `No provider keys configured. Add one to get started.`, `Loading keys...`), the unauthorized page copy, `Loading workspace surface...`, and every dialog string (headings, body copy, placeholders, `Cancel`, `Confirm delay`, `Resolve alert`, `Reject plan`, danger-zone copy).
- **Handlers:** preserve `submit(kind)` with the per-kind upload dispatch and activation invalidation; `loadShipments`, `onCreate`, `onStatusUpdate` (delayed branch), `onDelayConfirm`; `loadAlerts`, `onCreate`, `onScan`, `onAcknowledge`, `onResolveConfirm`, `onAutoResolve`; `loadPlans`, `onGenerate`, `onApprove`, `onRejectConfirm`; `fetchKeys`, `onSubmit` (create → test → clear → refresh), `onRevoke` (including its `window.confirm`) and its `alert` error channel; the `ErrorBoundary` `Try again` reset; and every local toggle/state handler.
- **Auth flows and routing:** do not edit `App.tsx` paths or the `allowedRoles` map; do not change `ProtectedRoute`, `AuthContext`, or any sidebar destination. `/unauthorized` remains a standalone route without `Layout`; `/upload` keeps its admin|operator gate, `/providers` its admin|owner|operator gate, and `/shipments`, `/alerts`, `/planning` their admin|operator|viewer gates.
- **Role gates:** keep the providers `isAdminOrOwner` gate (form panel and `REVOKE` actions) and the planning admin-only `Approve` / `Reject` gating on pending plans.
- **`data-testid` and pinned attributes:** none of the six pages currently carries `data-testid` values, but the danger-zone modal keeps `role="dialog"`, `aria-modal="true"`, the typed-confirmation input with `aria-label="Workspace name confirmation"` and its disabled-until-match behavior (all smoke-pinned), and the planning horizon input keeps `id="horizon"`. The activation banner keeps `activation-banner`, `activation-checklist`, `cap-pitch-banner`, and every `milestone-chip-*` identifier — `ActivationBanner.tsx` is not edited.
- **Activation checklist behavior on `/upload`:** the `<ActivationBanner mode="checklist" />` mount stays between the page header and the import rail; its server-driven visibility, milestone gating, and next-step emphasis are untouched.
- **Free-cap lock:** the `freeCapLocked` derivation and its upload-disabling behavior (button disabled + `Writes locked (Free cap)` label) are preserved exactly.
- **Dialog behavior:** the four dialogs gain no new interactions — no focus trap, no Escape handling, no backdrop-click close; only presentation and the aria attributes change.
- **Unrelated files:** do not touch `.gitignore`, `.opencode/agents/vision.md`, `apps/platform-api/tests_full_run.log`, `docs/adr/tech-backlog.md`, or `docs/plans/console-ui-website-language-plan.md`. Keep the change set scoped to the twelve files named in this blueprint.
