# Phase Console UI Website Language 02 — Dashboard Top + Activation, Route Studio, Account, Receipts, Admin Queue

**Status:** LOCKED for `@build` on branch `feat/console-website-language-batch`. Delta on top of TECH-60 (quiet pass) and TECH-62/63 (phase 01 shell + login, QA approved at `e70c939`). Source of truth: `docs/plans/console-ui-website-language-plan.md` sections 5, 6, 7, 8, 9, 10, 12, and 13. AST note: the `graphify` CLI is not available in this environment (confirmed again for this phase; same condition as phase 01), so the dependency maps below are grounded in direct source reads of every touched file and its current imports.

## Goal for this phase

Deliver the operator-density hierarchy pass for the five highest-traffic workspace surfaces — dashboard top + activation, Route Studio, Account, Receipts, and the admin verification queue — so each reads as a distinct, scannable workstation with a clear action hierarchy, while preserving every handler, state machine, locked string, role gate, and `data-testid` currently in place.

## Ground-truth decisions for this phase only

1. **Phase boundary:** this slice covers only source-plan sections 5–10. Do not pull section 11 (upload / shipments / alerts / planning / providers / unauthorized) or any other console work into this phase.
2. **Delta rule:** treat TECH-60 as the visual base and TECH-62/63 as the shell/login layer. Keep the deep slate canvas, cyan-only accent family, three-level surface model (canvas → `fp-shell-surface` primary → `fp-nested-surface` nested), mono numerals for all data metrics, border-first surfaces, and the no-gradient / no-glow / no-decorative-motion discipline. The existing `glow-ring` utility is the approved 2px cyan focus treatment, not a glow effect — it stays everywhere it currently appears.
3. **Surface order rule:** within each page, action surfaces outrank supporting data. On the dashboard the exception queue is the anchor; readiness and audit are support. On Account the plan/usage posture is dominant; provider control is a secondary work area; audit is a support stream; the danger zone is isolated last. On Route Studio the form is the primary modeling surface until results exist; the map is subordinate. On Receipts the intake is the confident action, wallet is a state block, history is a work queue. On the admin page the queue is the scanner and the detail pane is the decision surface.
4. **Shared-primitive rule:** all framing flows through the existing `PageHeader`, `Panel`, `MetricTile`, `StatusBadge`, `fp-shell-surface`, `fp-nested-surface`, and `fp-pill` primitives aligned in phase 01. No page forks the design language with bespoke surfaces, and no new runtime or test dependencies are allowed.
5. **CSS rule:** `apps/ops-console/src/index.css` requires no changes. If a shared density utility (for example a tighter nested-row class) proves necessary in two or more pages, it must be added once to the shared utilities layer in `index.css` under the existing motion/color discipline — never inlined per page.
6. **Component contract rule:** `ActivationBanner`, `CapPitchBanner`, `RouteMap`, `RouteSchedulesTable`, `WorkspaceResetDangerZone`, `PageHeader`, `Panel`, `MetricTile`, and `StatusBadge` keep their existing interfaces. This phase does not change their props or exports. `ActivationBanner.tsx` itself is not modified at all; its compact-mode behavior, state machine, copy, and testids are locked.
7. **Copy lock:** every string currently rendered by the touched pages is preserved verbatim. The only permitted text-level changes are structural reordering of already-existing labels, never new marketing copy or rewritten helper text.
8. **Workstation split rule (admin detail):** the reversal context required by source-plan section 10 stays in the full-width `Audit & reversibility` surface (the secure audit surface), not inside the detail pane. The detail pane is segmented into the four inspection segments: flags, extracted fields, preview, verdict controls.

## Ground-truth decisions per surface

### Surface 1 — Dashboard top + activation (source plan §5, §6)

- **Layer A — header surface:** keep the existing `PageHeader` with eyebrow `Control tower`, the current title, current description, and the current actions slot containing the live-sync chip and the refresh button. Copy and handlers (`handleRefresh`, `handleLiveMessage`, `lastLiveUpdate` chip) are unchanged.
- **Layer B — activation/readiness strip:** keep `<ActivationBanner mode="compact" />` mounted directly below the header. Its rendering contract, server-driven visibility, milestone gating (`n_of_5`, `pct_complete`, `m6_completed`), progress rail, and single CTA are locked — the page must not restyle or wrap it in new surfaces.
- **Layer C — metric hierarchy:** replace the current five-equal-tiles strip with the approved two-tier grouping while keeping `MetricTile` as the tile primitive and keeping every value, detail string, tone, and locked variant:
  - Primary metrics (dominant pair): `Open exceptions` and `In-transit`, rendered with visibly stronger presence than the secondary row (for example two larger primary-framed tiles spanning a shared strip).
  - Secondary metrics (quieter row): `Forecast demand` and `Weather risk` — including both unlocked and milestone-5 locked variants with their exact locked copy and `Continue onboarding` CTA to `/upload` — plus `Usage posture` with its `N/A` and 100/80 percentile tone thresholds.
  - The `summary` memo, `severityTone`, `PANEL_GATES` export, `gateMilestone`, and `GatePlaceholder` (copy `Unlocks after Milestone {n}` + `Continue onboarding →`) are preserved exactly.
- **Exception queue (anchor):** keep the `Exception queue` / `What needs operator action` panel and its feed data, but render the feed items as denser operational rows rather than mini-cards: severity badge, source type, title, message, and timestamp in a tighter single-column scan pattern with reduced padding and no competing inner chrome. Keep the per-item stable keys, the `Queue clear` empty state, and the six-item slice.
- **Readiness and audit (support):** keep `Execution posture` / `Workspace readiness` with its four stat blocks (including the milestone-4 gated `Utilization` and its locked variant), and keep `Audit timeline` / `Latest workspace actions` with its four-item slice. Visually subordinate both to the queue: quieter framing, no equal-weight competition with the anchor.
- **Gated lower band:** keep the milestone-6 dock/freight pair, the `FeedbackForm`, and the milestone-gated `InventoryCharts` / `ForecastChart` placeholders exactly as wired; only ensure their `Panel` framing matches the aligned nested-surface treatment.

### Surface 2 — Route Studio workstation (source plan §7)

- **Page frame:** keep the `Route studio` header, its description, and the `Refresh schedules` action with `handleRefresh`, `loadSchedules`, the `useLiveUpdates` route-summaries handler, the error panel, and the `PostAhaToast` first-optimization flow (server-truth `post_aha_toast`). No state or handler changes.
- **Workstation layout:** the left column holds the route model form and is the dominant surface; the right column holds `RouteMap` (or the milestone-5 locked placeholder panel with its exact copy) and reads clearly subordinate until results exist. Below the pair, keep the `Schedule library` panel wrapping `RouteSchedulesTable`, then the `Scenario history` panel with its persisted/draft and unassigned badges, stats row, and empty state.
- **Form treatment:** within `RouteOptimizerForm`, group the existing fields by intent into four labeled groups — scenario identity (route name, schedule date, start warehouse code), route shape (deliveries, vehicle capacity, max stops), operating constraints (speed, cost per km), and persistence options (the two checkboxes). All fields, defaults, parsing of the deliveries string, submit mapping, submit labels, disabled/loading states, and the `queryClient` activation invalidation (NB-30.4) are preserved. The submit action becomes the dominant full-width primary action.
- **Result treatment:** keep the result block, and structure it as: summary badges at top (objective, assignment state, CO2), key stats in a structured mono-numeral row (distance, cost, duration, stops), the previous-result comparison isolated in one distinct diff surface with the existing emerald-versus-neutral delta coloring, and the stop sequence as dense readable rows keyed by sequence. Persisted-versus-draft distinction stays obvious via the existing badges in history.
- **No changes to `RouteSchedulesTable` or `RouteMap` internals:** both keep their props and behavior; only their surrounding placement and panel framing change.

### Surface 3 — Account governance surface (source plan §8)

- **Section boundaries:** structure the page into the five approved sections in order: plan + usage posture (dominant), escalation contact, provider control (secondary work area), audit stream (support), danger zone (isolated, unmistakable, last).
- **Posture strip:** keep the four `MetricTile` values (`Current plan`, `Usage`, `Preferred provider`, `Active keys`) with all current detail strings and tone thresholds (`progressPercent` 100 danger / 80 warning), but re-weight the strip into a dominant pair (plan, usage) and a quieter secondary pair (preferred provider, active keys) so billing posture is understood at a glance.
- **Plan cards:** keep the subscription panel and its plan cards — title, price text, `Current` badge, seats / vehicles / included tasks / overage rate rows, and the `Switch to plan` / `Current plan` toggle buttons with disabled logic — but present them as comparative operational controls: tighter density, muted chrome, consistent row rhythm, no mini-marketing-tile feel. All handlers (`onSelectTier`, `onRefreshUsage`), the usage meter block, and the `Usage endpoint unavailable` copy are unchanged.
- **Escalation contact:** keep the panel, the `contactPhone` input (id `contactPhone`, placeholder `Escalation phone`), `onSaveContactPhone`, and the current-phone caption.
- **Provider control:** keep the preferred-provider select + save, the add-key form fields and submit, and the key list with `Test` / `Revoke` actions and `keyTone` badges. Keep `onAddKey`, `onTestKey`, `onRevokeKey`, `onSetPreferredKey`, and the empty-key list copy.
- **Audit and danger zone:** keep the audit panel with its eight-item slice and the admin-only `WorkspaceResetDangerZone` mount (`user?.role === 'admin'`). The danger zone keeps its placement at the bottom, visually separated as an isolated governance boundary.
- All status-message channel copy (`statusMessage` strings) is preserved.

### Surface 4 — Receipts financial workflow (source plan §9)

- **Three-part split:** the page is presented as intake (upload surface), wallet state block, and receipt history work queue. Keep the header copy and the status/error message panels.
- **Intake:** keep the upload panel with the file input (id `receipt-upload-input` — this id is load-bearing because the re-upload action programmatically clicks it), the accept pattern, the selected-file caption, the submit disabled/uploading logic, and the `Upload receipt` / `Uploading…` labels. The dynamic import of `uploadReceipt`, `refetchReceipts`, and the `UPLOAD_CONFIRMATION` constant are unchanged.
- **Wallet:** keep the wallet panel rendered as a financial state block: `Available balance` with the mono-numeral `available_etb`, the applies-to-next-invoice caption, the credits ledger rows with `applied_to_invoice_number`, and the `No surplus credits yet.` / `Wallet unavailable.` states.
- **Receipt history:** keep the history panel, but render receipt entries as a dense work queue where status, amount, invoice, sender, and actionability are the emphasized columns. Preserve every interactive behavior inside `ReceiptCard`: the dispute toggle, dispute textarea (max length 1000 and exact placeholder), `Submit dispute` disabled logic, `Re-upload` (via the programmatic input click), the verified / reversed / rejected / escalated copy blocks, and `onDispute` wiring through `useSubmitDispute`.
- All empty states (`No receipts uploaded yet.`) are preserved.

### Surface 5 — Admin queue / verification workstation (source plan §10)

- **Queue column:** keep the `Queue` / `Pending and escalated` panel, the row buttons with `selectedId` highlight, and each row's encoding of organization, reference, amount, invoice, sender, state badge, age timestamp, and flag chips (`REVERSED_CREDIT_CHIP`, `NEW SENDER`, `CASH`). Densify the rows for faster scanning without touching the selection/click handlers or the dispute-text line.
- **Detail column:** segment the `AdminDetail` pane into the four inspection segments in order: flags (all flag chips plus the fraud-badge admin controls block), extracted fields (the eight-field grid with confidence percentages, mono values, and confidence bars), preview (`Preview receipt file` with the PDF iframe / image branch), and verdict controls. Keep verdict pre-fill suppression (only pre-fill when the service recommends verify — NB-12.3), the five-verdict set, the large-surplus decision block with `partial_ignore` amount input, the trusted-payer select, the required escalation note, the optional admin note (max length 512), and the `Render decision` submit with its disabled logic. `onRendered` refetching and the `renderDecision` payload mapping are unchanged.
- **Verdict hierarchy:** restyle the verdict actions to a three-tier hierarchy: `Verify` as the dominant primary action (solid cyan), `Escalate` as a warning secondary (amber outline), and the three reject verdicts as a controlled muted-danger group (rose outline). Selection state must remain obvious in all cases; the current verdict state variable and the active styling logic are preserved.
- **Reversal surface:** keep the full-width `Audit & reversibility` panel (source-plan §10 reversal panel) as a secure audit surface: `ReversalActionButtons` with the undo (≤24h, optional note) and reverse (mandatory reason) modes, the window captions, `AuditEventsDrawer`, the `Refresh audit` action, and the empty state `No verified receipts.`. `onUndo` / `onReverse` mutation flows and their server message strings are unchanged.
- The page-level message and error channels, the queue/detail two-column grid, and the empty detail state (`Select a receipt`) are preserved.

## Exact files to modify or create, with why each changes

- `apps/ops-console/src/pages/DashboardPage.tsx` — restructure the top of the dashboard into the three-layer hierarchy (header / activation / two-tier metrics) and densify the exception queue rows into the anchor surface. All hooks, state, gating, and copy stay in place.
- `apps/ops-console/src/pages/RoutesPage.tsx` — rebalance the workstation columns (form-dominant left, map-subordinate right, library and history below) so the page reads as a modeling environment. Handlers and live-update wiring unchanged.
- `apps/ops-console/src/components/RouteOptimizerForm.tsx` — group the form fields by intent into four labeled groups and restructure the result block (summary, structured stats, distinct diff surface, dense stop rows) with a dominant submit action.
- `apps/ops-console/src/pages/AccountPage.tsx` — impose the five-section governance boundaries, re-weight the posture strip, and tighten the plan cards into comparative operational controls without touching any handler.
- `apps/ops-console/src/pages/ReceiptsPage.tsx` — present intake / wallet / history as a financial workflow with denser work-queue rows, preserving the load-bearing upload input id and all dispute behaviors.
- `apps/ops-console/src/pages/AdminReceiptsPage.tsx` — densify the queue rows, segment the detail pane, apply the three-tier verdict hierarchy, and treat the reversals surface as a secure audit block.
- `apps/ops-console/src/pages/workspaceSurfaces.smoke.test.tsx` — strengthen the dashboard, receipts, and admin assertions against the restructured hierarchy and add a Route Studio smoke block (feasible with the existing service mocks). All existing assertions remain intact.
- **No new files are created in this phase.** No changes to `index.css`, `App.tsx`, `Layout.tsx`, the shell modules, `ActivationBanner.tsx`, `RouteMap.tsx`, `RouteSchedulesTable.tsx`, `WorkspaceResetDangerZone.tsx`, or the UI primitives.

## Strict import and dependency map for touched files

### `apps/ops-console/src/pages/DashboardPage.tsx`

- Keep all current imports unchanged: `useCallback`, `useMemo`, `useState` from React; `ActivationBanner`, `DockGanttChart`, `FeedbackForm`, `FreightReconciliationPanel`, `ForecastChart`, `InventoryCharts` from `../components`; `MetricTile`, `PageHeader`, `Panel`, `StatusBadge` from `../components/ui`; `useAuth` from `../context/AuthContext`; the eleven query hooks from `../hooks/queries`; `useLiveUpdates` and its `LiveUpdatePayload` type from `../hooks/useLiveUpdates`.
- Keep the `PANEL_GATES` export, `gateMilestone`, `severityTone`, `GatePlaceholder`, `SkeletonBlock`, `DashboardSkeleton`, and the `summary` memo exactly as-is; the build agent reorders and re-frames markup only.

### `apps/ops-console/src/pages/RoutesPage.tsx`

- Keep all current imports: `useEffect`, `useState` from React; `PostAhaToast`, `RouteMap`, `RouteOptimizerForm`, `RouteSchedulesTable` from `../components`; `PageHeader`, `Panel`, `StatusBadge` from `../components/ui`; `useAuth`; `useActivationState` from `../hooks/queries`; `useLiveUpdates`; the three service functions from `../services/logisticsApi`; and the four API types from `../types/api`.
- The `RouteOptimizeResponse`, `RouteStop`, `RouteScheduleSummary`, and `WeatherRiskZone` types continue to flow through the same call sites; no type moves.

### `apps/ops-console/src/components/RouteOptimizerForm.tsx`

- Keep all current imports: `useState` from React; `useQueryClient` from `@tanstack/react-query`; `Panel`, `StatusBadge` from `./ui`; `optimizeRoute` from `../services/logisticsApi`; `RouteOptimizeResponse` from `../types/api`.
- Keep the `onOptimized` prop contract, the `payload` defaults, `previousResult` / `result` state, both delta variables, and the `queryClient.invalidateQueries` activation refresh.

### `apps/ops-console/src/pages/AccountPage.tsx`

- Keep all current imports: `useEffect`, `useMemo`, `useState`, `FormEvent` type from React; `MetricTile`, `PageHeader`, `Panel`, `StatusBadge` from `../components/ui`; `WorkspaceResetDangerZone` from `../components/WorkspaceResetDangerZone`; `useAuth`; the nine functions from `../services/billingApi`; `getAuditTimeline` from `../services/logisticsApi`; the four helpers from `./accountUsageUtils`; and the five API types from `../types/api`.
- Keep the local helpers `priceText` and `keyTone`, the `fieldClassName` string, and all eight handlers verbatim.

### `apps/ops-console/src/pages/ReceiptsPage.tsx`

- Keep all current imports: `useState` from React; `ChangeEvent`, `FormEvent` types from React; `PageHeader`, `Panel`, `StatusBadge` from `../components/ui`; `useReceipts`, `useSubmitDispute`, `useWallet` from `../hooks/queries`; `Receipt` from `../types/api`.
- Keep `UPLOAD_CONFIRMATION`, `statusTone`, and the internal `ReceiptCard` component (moved or not, its props and behaviors stay identical).

### `apps/ops-console/src/pages/AdminReceiptsPage.tsx`

- Keep all current imports: `useState` from React; `PageHeader`, `Panel`, `StatusBadge` from `../components/ui`; the six hooks from `../hooks/queries`; `getReceiptFileUrl`, `renderDecision` from `../services/receiptsApi`; and the five types from `../types/api`.
- Keep the four flag-copy constants, `verdictTone`, and the internal modules `ReversalActionButtons`, `AuditEventsDrawer`, `ReversalsPanel`, and `AdminDetail` with their exact prop contracts; only their internal markup and the verdict action styling change.

### `apps/ops-console/src/pages/workspaceSurfaces.smoke.test.tsx`

- Keep all existing mocks (auth context, receiptsApi, api) and the `seededActivationState` / `preloadedDashboardClient` fixtures intact.
- Add a named import of `RoutesPage` from `./RoutesPage` for the new Route Studio smoke block; the existing `services/api` mock already resolves `get` to empty arrays, which the page's `Promise.all` tolerates.
- Do not weaken or remove any current assertion.

### Dependencies that must remain untouched in this phase

- `apps/ops-console/src/App.tsx` — route table, `allowedRoles` map, and lazy imports stay unchanged (`/account` admin|operator|viewer, `/receipts` admin|owner|operator|viewer, `/admin/receipts` admin|owner).
- `apps/ops-console/src/components/ProtectedRoute.tsx`, `context/AuthContext.tsx`, `services/*` — auth gate, provider contract, and transport layers stay unchanged.
- `apps/ops-console/src/components/ActivationBanner.tsx` — banner state machine, cap-pitch hierarchy (p60 reminder / p80 concern / p100 stop), milestone chip rendering, and all testids stay unchanged.
- `apps/ops-console/src/components/Layout.tsx`, `components/shell/*` — phase-01 shell modules stay unchanged.

## Step-by-step execution for `@build`

1. Start from the current branch state without touching any unrelated dirty or untracked file; scope the change set to the seven files listed above.
2. **Surface 1 — dashboard:** restructure `DashboardPage.tsx` into the three-layer top (header, activation strip slot, two-tier metric groups), then densify the exception queue rows and subordinate the readiness/audit panels. Preserve all gating, hooks, and copy; do not edit `ActivationBanner.tsx`.
3. **Surface 2 — Route Studio:** rebalance `RoutesPage.tsx` columns and panel order, then group the `RouteOptimizerForm` fields by intent and rebuild the result block hierarchy with the dominant submit action.
4. **Surface 3 — Account:** reorder and re-weight the `AccountPage` sections into the five governance boundaries, tighten the plan cards, and keep the danger zone isolated last.
5. **Surface 4 — Receipts:** restructure `ReceiptsPage.tsx` into intake / wallet / history with dense work-queue rows, preserving the upload input id and every dispute interaction.
6. **Surface 5 — Admin queue:** densify the queue rows, segment the detail pane into the four inspection segments, apply the three-tier verdict hierarchy, and confirm the reversals surface reads as the secure audit block.
7. Strengthen the smoke assertions in `workspaceSurfaces.smoke.test.tsx` and add the Route Studio smoke block; do not weaken existing expectations.
8. Run the verification commands below from `apps/ops-console` and resolve any alignment drift through the shared primitives or the shared utilities layer in `index.css` — never through per-page visual one-offs outside the design language.

## Acceptance checkpoints tied to the source-of-truth plan

- Source plan §5, Layer B: the dashboard top answers what matters now, what is blocked, and what needs action; the activation strip keeps one state sentence, one CTA, and one progress rail.
- Source plan §5, Layer C: primary metrics (open exceptions, in-transit) visually outrank the secondary metrics (forecast, weather risk, usage posture); no five-equal-tile repetition remains.
- Source plan §5, exception queue / readiness / audit: the queue is the natural focal point; readiness and audit read as secondary support surfaces; gated milestone placeholders still render with locked copy.
- Source plan §6, compact mode: `/dashboard` banner behavior, copy, and milestone gating are unchanged; onboarding reads as a journey rail, not a stapled notice.
- Source plan §7: Route Studio reads as a workstation — form grouped by intent, map clearly subordinate until results exist, saved schedules and scenario history below, result hierarchy immediate (summary block, structured stats, distinct diff surface, dense stop rows), persisted vs draft obvious, submit action dominant.
- Source plan §8: Account has clear section boundaries — plan/usage dominant, escalation contact and provider control as secondary work areas, audit as support, danger zone isolated and unmistakable; plan cards read as comparative operational controls.
- Source plan §9: Receipts splits into intake, wallet state, and receipt history; upload feels confident, wallet is scannable with mono numerals, rows emphasize status, amount, invoice, sender, and actionability; dispute/rejection handling stays structured.
- Source plan §10: the admin page reads as a verification workstation — queue rows encode organization, amount, reference, sender, state, age, and flags; the detail pane is segmented (flags, extracted fields, preview, verdict controls); verdict hierarchy is verify-primary / escalate-warning / reject-muted-danger; the reversal panel reads as a secure audit surface.
- Source plan §12 hard rules: copy, handlers, auth flows, routing, role gates, and existing `data-testid` values are preserved; no decorative gradients, no glow shadows, no new dependencies.
- Source plan §14 acceptance standard: all five surfaces feel like the same product as the website and operators can scan faster, not slower.

## Testing requirements

1. `apps/ops-console/src/pages/workspaceSurfaces.smoke.test.tsx` must keep every existing assertion green, including the activation banner, receipts, admin queue, reversals, account escalation-contact, and danger-zone blocks.
2. Strengthen the dashboard smoke block so it still proves the metric hierarchy copy renders: `Open exceptions`, `In-transit`, `Forecast demand`, `Weather risk`, and `Usage posture` (including the milestone-5 locked variants under the seeded 0-of-5 state).
3. Add a Route Studio smoke block rendering `RoutesPage` with the existing mocks and asserting the workstation copy: `Route studio`, the page title, `Optimize route`, `Schedule library`, `Scenario history`, and the milestone-5 map placeholder text.
4. Existing `ActivationBanner.test.tsx` and `ShellChrome.test.tsx` suites must remain green with no edits.
5. If the build agent introduces a shared density utility in `index.css`, it must be covered by the existing suites rendering those rows; no new test files are required otherwise.

## Verification commands for `apps/ops-console`

Run these commands from `apps/ops-console`:

- `npm run test`
- `npm run typecheck`
- `npm run build`

## Notes on preserving copy, handlers, auth flows, routing, role gates, and `data-testid` values

- **Copy:** preserve every string in the five pages and the form, including dashboard tile details, gate placeholders, queue empty states, plan card labels and price text, provider key copy, escalation captions, upload/wallet/history copy, dispute and rejection blocks, admin flag constants, verdict labels, undo/reverse prompts, and all status-message strings.
- **Handlers:** preserve `handleRefresh`, `handleLiveMessage`, `onSubmit` (form), `onOptimized`, `onUpload`, `onFileSelected`, `onDispute`, `onSelectTier`, `onAddKey`, `onTestKey`, `onRevokeKey`, `onSetPreferredKey`, `onRefreshUsage`, `onSaveContactPhone`, `onRendered`, `onUndo`, `onReverse`, `onRemoveTrustedPayer` (including its `window.confirm`), and all local toggle/state handlers.
- **Auth flows and routing:** do not edit `App.tsx` paths or the `allowedRoles` map; do not change `ProtectedRoute`, `AuthContext`, or any sidebar destination. `/login` redirect and cookie-backed auth behavior are untouched.
- **Role gates:** keep the admin-only `WorkspaceResetDangerZone` mount on `/account` and the admin/owner gate on `/admin/receipts` behavior as-is.
- **`data-testid` values:** do not rename or remove `activation-banner`, `activation-checklist`, `cap-pitch-banner`, or any `milestone-chip-*` identifier. The upload input id `receipt-upload-input` is load-bearing (programmatic click from the re-upload action) and must not change.
- **Banner state machines:** the activation banner (compact/checklist modes, `m6_completed` short-circuit, `banner.visible` gate) and the cap-pitch hierarchy (p100 > p80 > p60 with the `Dismiss` action) remain untouched.
- **Unrelated files:** do not touch `.gitignore`, `.opencode/agents/vision.md`, `apps/platform-api/tests_full_run.log`, `docs/adr/tech-backlog.md`, or `docs/plans/console-ui-website-language-plan.md`. Keep the change set scoped to the seven files named in this blueprint.
