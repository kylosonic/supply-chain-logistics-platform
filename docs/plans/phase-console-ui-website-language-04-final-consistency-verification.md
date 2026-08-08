# Phase Console UI Website Language 04 — Final Consistency Verification Sweep

**Status:** LOCKED for `@build` on branch `feat/console-website-language-batch`. This is source-plan step 9 (final consistency pass) plus a **UAT-adapted step 10** (verification only — no deploy before human approval). Delta on top of phases 01 (`e70c939`), 02 (`790f853`), and 03 (`78c2cfd`), all QA approved. Source of truth: `docs/plans/console-ui-website-language-plan.md` sections 12, 13 (steps 9–10), and 14. AST note: `graphify` is unavailable in this environment (same condition as phases 01–03); the sweep inventory below is grounded in direct source reads plus a PowerShell `Select-String` inventory of every class string in `apps/ops-console/src` performed for this blueprint.

## 1. Goal

Run the final whole-console consistency pass for the website-language batch: enforce the single cyan/sky accent family (semantic accents only for actual state), normalize every surface and radius onto the three-level token model, confirm mono numerals wherever data metrics render, and prove the branch green (`test`, `typecheck`, `build`) and merge-ready — without deploying or live-verifying before human UAT.

## 2. Files to modify or create

Sweep fixes only — token-based class-string swaps. **No new files, no new dependencies, no import changes.**

- `apps/ops-console/src/components/FeedbackForm.tsx` — the one component no phase touched: hand-rolled `rounded-[22px]` panel surface and input recipe drift from the system.
- `apps/ops-console/src/pages/ReceiptsPage.tsx` — hand-rolled input recipe (`rounded-2xl`) on the dispute textarea and upload input; hand-rolled row/card recipe (`rounded-xl … bg-slate-900/40`); literal `rounded-[16px]` amber note; wallet/ledger block surfaces.
- `apps/ops-console/src/pages/AccountPage.tsx` — duplicated hand-rolled `fieldClassName` input recipe; plan-card and panel-block row recipes; skeleton radii; non-mono data numerals in usage posture and plan limits.
- `apps/ops-console/src/pages/DashboardPage.tsx` — readiness/audit stat blocks and queue rows on the hand-rolled recipe; gate placeholder and skeleton radii.
- `apps/ops-console/src/pages/RoutesPage.tsx` — history rows, map placeholder, and empty-state surfaces on the hand-rolled recipe.
- `apps/ops-console/src/components/RouteOptimizerForm.tsx` — duplicated `fieldClassName` input recipe; checkbox cards, result block, stat cards, stop rows, and diff surface radii.
- `apps/ops-console/src/pages/AdminReceiptsPage.tsx` — queue-row button radius; teal non-token accents (Undo button, confidence bars, two captions); non-mono confidence percentage; literal `rounded-[16px]` preview frame and amber blocks. **Violet fraud chips are preserved (see Ground-truth decisions 2 and 3).**
- `apps/ops-console/src/components/DockGanttChart.tsx` — legacy milestone-6 chart: blue accents (outside the accent family), orange accents (warning semantics off-token), `backdrop-blur-sm`, neutral-hue surfaces, light-mode-only branches.
- `apps/ops-console/src/components/FreightReconciliationPanel.tsx` — legacy milestone-6 panel: blue upload button, orange mismatch accents, neutral-hue surfaces, light-mode-only branches, non-mono financial numerals.

**Expected to be untouched** (verified clean in the pre-sweep inventory): `AlertsPage`, `ShipmentsPage`, `PlanningPage`, `ProvidersPage`, `UploadPage`, `CsvUploadPanel`, `UnauthorizedPage`, `LoginPage`, `LoginFeedbackPanels`, `App.tsx`, `ErrorBoundary`, `WorkspaceResetDangerZone`, `ActivationBanner`, all `ui/*` primitives, all `shell/*` modules, `index.css`, `Layout.tsx`, `ProtectedRoute`, `AuthContext`, `services/*`, `hooks/*`, `types/*`, and all test files. If the build agent's own sweep run finds a residual site the pre-sweep inventory missed, it may fix it under the same rules; if it finds anything outside the rules below, it must stop and report rather than improvise.

## 3. Ground-truth decisions (this phase only)

1. **Sweep boundary:** this phase is source-plan §13 step 9 plus a verification-only adaptation of step 10. No page restructures, no copy edits, no handler/state/route/role changes, no new primitives, no `index.css` edits (every token needed — `fp-row`, `fp-nested-surface`, `fp-input`, `fp-pill`, `fp-shell-surface`, `--fp-radius-panel`, `--fp-radius-hero` — already exists and is in use).
2. **Fraud-chip adjudication (AdminReceiptsPage violet):** the `REVERSED_CREDIT_CHIP` violet treatment (queue-row chip, flags-segment chip, and the informational fraud-badge block) is **PRESERVED** as a documented, single-purpose exception to the cyan-only rule. Rationale: it encodes actual state (fraud classification = danger semantics, exactly the "semantic accents for actual state" permission), it is inherited from the QA-approved phase-02 surface, it is copy-pinned by the smoke suite (`reversed credit on file` absence assertion), and recolor would blur the fraud signal against the rose `NEW SENDER` flag. Violet remains forbidden everywhere else; the sweep proves it occurs nowhere else. This exception is recorded for human UAT confirmation (see decision 6).
3. **Teal adjudication (AdminReceiptsPage):** teal is outside the palette and is not state-permitted. It resolves to token family: the `Undo (≤24h)` outline button and the ≥0.6 confidence bar become emerald (success semantics), the two informational captions (`Actions: …`, `Undo window closes …`) become slate neutral. No copy changes.
4. **Red/green adjudication (FreightReconciliationPanel only):** variance sign colors and the Matched/Mismatch status badge colors are actual state and are permitted per the user's standing rule (violet/green semantic accents permitted only for actual state). They stay. Orange (warning semantics) moves to the amber token family; blue (decorative/series color and a primary-action button, neither of which is state) moves to the sky accent family.
5. **Radius rule:** after the sweep the only radii rendered are: `--fp-radius-hero` (24px, shell/dialog frames), `--fp-radius-panel` (16px, nested surfaces, rows, inputs), `--fp-radius-pill` (pills/badges, 57 sites), the approved control radius `rounded-lg` (51 sites, buttons/fields/controls — consistent, documented baseline), chart-bar geometry `rounded-md` (DockGanttChart internals only), and the locked `ActivationBanner` 20px banner radius (one component, internally consistent, test-pinned — documented baseline). Zero `rounded-[arbitrary]` values and zero `rounded-xl`/`rounded-2xl`/`rounded-3xl` remain in `apps/ops-console/src` after the sweep (skeleton shimmer blocks included — they move to token variables with a visually imperceptible delta).
6. **UAT-before-deploy adaptation (records source-plan §13 step 10):** step 10 of the source plan ("tests + build + deploy + live verification") is **adapted by explicit decision**: this phase runs only `npm run test`, `npm run typecheck`, and `npm run build` from `apps/ops-console` and leaves the branch fully verified and merge-ready. **No deploy and no live verification execute before human UAT.** The deploy + live-verify sequence runs only AFTER the human approves the merge of this branch; the build agent must not run deploy scripts, docker builds, or live checks in this phase. The fraud-chip exception (decision 2) is part of the UAT checklist.
7. **Minimality rule:** every fix is a class-string swap on presentation markup only. No JSX reordering beyond the minimum needed to apply a token class; no copy edits; no `data-testid`/`aria-*`/`id` edits; no behavior deltas. If a swap would require touching a handler, state variable, or locked string, it is out of scope and must be reported instead.

## 4. Audit-table-driven sweep scope

The build agent must run these exact inventories from the repo root (PowerShell fallback noted; on this machine `rg` is absent so `Select-String` is the proven form), record the output, and reconcile every hit against the audit table below. Expected inventories per category:

1. **Accent colors** — command: `rg -n "(bg|text|border|ring)-(violet|purple|fuchsia|indigo|teal|pink|orange|lime|blue|cyan)-" apps/ops-console/src` (PowerShell: `Get-ChildItem apps/ops-console/src -Recurse -Include *.tsx,*.ts | Select-String -Pattern '(bg|text|border|ring)-(violet|purple|fuchsia|indigo|teal|pink|orange|lime|blue|cyan)-[0-9]+'`). Expected after sweep: **zero** hits outside the preserved violet fraud-chip block in `AdminReceiptsPage` (3 chip/block sites) — and zero `cyan-` hits anywhere (the accent family is sky). Baseline before sweep: violet×9 (all AdminReceiptsPage), teal×7 (all AdminReceiptsPage), blue×7 (DockGanttChart, FreightReconciliationPanel), orange×11 (DockGanttChart, FreightReconciliationPanel), no purple/fuchsia/indigo/pink/lime/cyan.
2. **Radius soup** — command: `rg -n "rounded-\[|rounded-xl|rounded-2xl|rounded-3xl" apps/ops-console/src` (PowerShell: `… | Select-String -Pattern 'rounded-\[|rounded-xl|rounded-2xl|rounded-3xl'`). Expected after sweep: only `rounded-[var(--fp-radius-panel)]` and `rounded-[var(--fp-radius-hero)]` token references (9+ sites pre-sweep, growing as literals convert). Baseline before sweep: `rounded-xl`×41, `rounded-2xl`×13, `rounded-[16px]`×4, `rounded-[22px]`×1, `rounded-[var(--fp-radius-panel)]`×9. `rounded-lg` (51), `rounded-full` (57), `rounded-md` (3) are approved baselines and must be excluded from the fix list.
3. **Shadows** — command: `rg -n "shadow-\[" apps/ops-console/src`. Expected: **zero**. Baseline: zero already (the pre-sweep inventory found no arbitrary shadows). `shadow-sm` (DockGanttChart bars) and `shadow-lg` (PostAhaToast floating layer) are approved elevation, not glow — excluded from the fix list and documented.
4. **Backdrop blur** — command: `rg -n "backdrop-blur" apps/ops-console/src`. Expected: **zero** after sweep. Baseline: exactly one — the DockGanttChart appointment track; removed per the phase-03 dialog blur precedent.
5. **Gradients** — command: `rg -n "bg-gradient|from-(sky|slate|cyan|emerald)|via-" apps/ops-console/src`. Expected: **zero** in TSX/TS (the `.skeleton` shimmer gradient in `index.css` is the approved utility and is not a finding).
6. **Side stripes** — command: `rg -n "border-l-(sky|cyan|emerald|amber|rose|violet|blue|red|green|teal|orange)" apps/ops-console/src`. Expected: **zero** (the phase-03 AlertsPage stripe map is gone). The single neutral structural hour-gridline `border-l` inside DockGanttChart is not a stripe accent and is preserved.
7. **Mono numerals** — command: `rg -n "font-mono|tabular-nums" apps/ops-console/src` to establish the baseline, then spot-verify each data-numeral render site listed in the audit table (section 5) for mono + tabular. Timestamps (rendered sans, consistently, across every page) and chart-axis/step indices (UploadPage rail, DockGanttChart hour labels) are deliberate and excluded.

### Audit table — file | finding | action

| # | File | Finding | Action |
|---|------|---------|--------|
| 1 | `components/FeedbackForm.tsx` | Hand-rolled panel `rounded-[22px] … bg-slate-900/70` (22px named in the soup list) | FIX: adopt `fp-nested-surface` (16px token, nested surface); keep all copy, emerald feedback semantics, and handlers |
| 2 | `components/FeedbackForm.tsx` | Three hand-rolled textarea/input recipes (`bg-slate-950 … rounded-lg`, emerald focus) | FIX: adopt `fp-input` base with existing `min-h`/padding modifiers preserved; keep emerald `focus:border` only if it survives as a modifier — otherwise token focus (cyan) applies; copy/handlers untouched |
| 3 | `pages/ReceiptsPage.tsx` | Dispute textarea and upload input use hand-rolled recipe incl. `rounded-2xl` | FIX: adopt `fp-input` (keep `min-h-24` and any `file:`-style modifiers); `id="receipt-upload-input"` is load-bearing and untouched |
| 4 | `pages/ReceiptsPage.tsx` | ReceiptCard row, wallet block, ledger row use `rounded-xl border … bg-slate-900/40` recipe | FIX: receipt rows → `fp-row`; wallet/ledger blocks → `fp-nested-surface`; all dispute behaviors untouched |
| 5 | `pages/ReceiptsPage.tsx` | Literal `rounded-[16px]` amber note (line 109) | FIX: `rounded-[var(--fp-radius-panel)]` token reference |
| 6 | `pages/AccountPage.tsx` | Duplicated hand-rolled `fieldClassName` input recipe (contact phone, provider form) | FIX: replace the local string with `fp-input` (+ `min-h-12` modifier); the `id="contactPhone"` attribute and all handlers untouched |
| 7 | `pages/AccountPage.tsx` | Plan cards, escalation block, provider key cards, audit rows use `rounded-xl … bg-slate-900/40` recipe (6 sites) | FIX: plan cards and audit rows → `fp-nested-surface`; provider key cards → `fp-row` (governance row per phase-03 providers precedent); card selection/disabled logic untouched |
| 8 | `pages/AccountPage.tsx` | Skeleton blocks use `rounded-xl`/`rounded-2xl` (lines 201/204/208/209) | FIX: token radius variables (`--fp-radius-panel` for tiles, `--fp-radius-hero` for large blocks) |
| 9 | `pages/AccountPage.tsx` | Data numerals in sans: utilization %, overage units, overage cost, plan limits (seats/vehicles/tasks/overage rate), plan price text | FIX: wrap the numeric value spans in mono + tabular (`font-mono tabular-nums`); labels and `N/A`/`Unlimited` copy untouched |
| 10 | `pages/DashboardPage.tsx` | Readiness stat blocks, queue rows, audit rows use `rounded-xl … bg-slate-900/40` recipe (lines 319/325/331/339/344/355) | FIX: exception-queue rows → `fp-row`; readiness/audit stat blocks → `fp-nested-surface`; gate placeholder keeps its dashed border but moves to `fp-nested-surface` treatment with token radius; `PANEL_GATES`, gating, hooks untouched |
| 11 | `pages/DashboardPage.tsx` | `SkeletonBlock` base and dashboard skeleton blocks use `rounded-xl`/`rounded-2xl` | FIX: token radius variables (base block → `--fp-radius-panel`) |
| 12 | `pages/DashboardPage.tsx` | Queue-clear state block and gated placeholder use `rounded-xl` (lines 62/308) | FIX: token radius (`--fp-radius-panel`); emerald state tone preserved |
| 13 | `pages/RoutesPage.tsx` | Scenario-history rows, map placeholder, empty state use `rounded-xl …` recipe (lines 105/134/156) | FIX: history rows → `fp-row`; map placeholder and empty state → token radius on existing frame classes; `handleRefresh`/live-update wiring untouched |
| 14 | `components/RouteOptimizerForm.tsx` | Duplicated hand-rolled `fieldClassName` input recipe | FIX: adopt `fp-input` (+ `min-h-12`); field defaults, parsing, submit mapping untouched |
| 15 | `components/RouteOptimizerForm.tsx` | Result block `rounded-2xl`, checkbox cards and stat cards `rounded-xl`, stop rows `rounded-lg … bg-slate-900/40`, diff surface (lines 131/135/155/171/179/195) | FIX: result block → `fp-nested-surface`; checkbox/stat cards → `fp-nested-surface`; stop rows → `fp-row` (dense readable rows per §7); diff surface keeps emerald-versus-neutral delta colors with token radius |
| 16 | `pages/AdminReceiptsPage.tsx` | Queue-row selectable button `rounded-xl` (line 621) | FIX: `rounded-[var(--fp-radius-panel)]`; selected-state highlight classes and click handler untouched |
| 17 | `pages/AdminReceiptsPage.tsx` | Teal Undo button (line 62) and ≥0.6 confidence bar (line 403) | FIX: teal → emerald (success semantics); disabled logic, hover states, and `undo_available` gating untouched |
| 18 | `pages/AdminReceiptsPage.tsx` | Teal captions `Actions: …` (line 146) and `Undo window closes …` (line 194) | FIX: teal → slate neutral; copy untouched |
| 19 | `pages/AdminReceiptsPage.tsx` | Confidence percentage rendered in sans (line 398) | FIX: mono + tabular; bar width logic untouched |
| 20 | `pages/AdminReceiptsPage.tsx` | Literal `rounded-[16px]` preview frame (lines 423/425) and amber block (line 467) | FIX: `rounded-[var(--fp-radius-panel)]` token references; iframe/image branch logic untouched |
| 21 | `pages/AdminReceiptsPage.tsx` | Violet `REVERSED_CREDIT_CHIP` treatments (lines 328/370–371/631) | **PRESERVE** — documented fraud-state exception (decision 2); no change; UAT-confirmed |
| 22 | `components/DockGanttChart.tsx` | Blue legend dot + appointment bars (lines 37/61) — decorative/series color outside accent family | FIX: blue → sky (`bg-sky-500` legend; bars `bg-sky-500/80 border-sky-500`); appointment rendering math untouched |
| 23 | `components/DockGanttChart.tsx` | Orange rescheduled bars + legend (lines 38/61) — warning semantics off-token | FIX: orange → amber (token family); reschedule detection logic untouched |
| 24 | `components/DockGanttChart.tsx` | `backdrop-blur-sm` on appointment track (line 59) | FIX: remove blur; replace `bg-white/50 dark:bg-black/20` with a single dark track tone `bg-slate-950/30` (dark-only console) |
| 25 | `components/DockGanttChart.tsx` | Neutral-hue surfaces/text (lines 35/42/45–46/53) plus light-mode-only branches (`bg-neutral-100`, `text-neutral-900`, etc.) | FIX: single dark-system classes — track → `bg-slate-900/40` with token radius, text → slate tones, gridlines → `border-slate-800`; drop light branches (console is dark-only by hardcoded body background) |
| 26 | `components/DockGanttChart.tsx` | `rounded-md` bars, `border-l` hour gridlines, sans hour labels | PRESERVE — chart geometry/structure/axis, documented baseline |
| 27 | `components/FreightReconciliationPanel.tsx` | Blue upload button (lines 61/63) | FIX: blue → sky primary (`bg-sky-500 hover:bg-sky-400`); file-input click-through and disabled logic untouched |
| 28 | `components/FreightReconciliationPanel.tsx` | Orange mismatch count + badge (lines 73/117) | FIX: orange → amber (warning token family) |
| 29 | `components/FreightReconciliationPanel.tsx` | Neutral-hue stat blocks/table/badges + light-mode branches (lines 71–128) | FIX: single dark-system classes (stat blocks → nested surface tone, table text → slate tones, badges keep dark-branch amber/green); drop light branches |
| 30 | `components/FreightReconciliationPanel.tsx` | Financial numerals in sans: mismatch count, total variance, quoted/actual/variance cells (lines 73/77/106–111) | FIX: mono + tabular on the numeric spans; currency formatting, sign logic, and status logic untouched |
| 31 | `components/FreightReconciliationPanel.tsx` | Red/green variance and status colors (lines 109/117–118) | PRESERVE — actual state semantics per decision 4 |
| 32 | `pages/AlertsPage.tsx`, `ShipmentsPage.tsx`, `PlanningPage.tsx`, `ProvidersPage.tsx`, `UploadPage.tsx`, `CsvUploadPanel.tsx`, `UnauthorizedPage.tsx`, `App.tsx`, `ErrorBoundary.tsx` | Clean in pre-sweep inventory (rows on `fp-row`, inputs on `fp-input`, token radii) | NO ACTION — re-verify with the commands in section 4 and confirm zero hits |
| 33 | `ActivationBanner.tsx` | `rounded-xl`/`rounded-2xl` banner frames (lines 31/51/70/107/143) | PRESERVE — locked component, internally consistent 20px banner radius, test-pinned; documented baseline |

## 5. Strict import map

**No imports change in this phase.** No module moves, no type moves, no new exports. Every fix consumes classes that already exist in the current `index.css` component layer (`fp-row`, `fp-nested-surface`, `fp-input`, `fp-pill`, `fp-shell-surface`, `fp-dialog-overlay`, `fp-dialog-surface`) and the existing CSS variables (`--fp-radius-panel`, `--fp-radius-hero`). Files keep their exact current import statements; the only diff is inside JSX `className` strings. `index.css` is not modified.

## 6. Step-by-step execution for `@build`

1. Start from the current branch state; do not touch any unrelated dirty or untracked file (see preservation notes). Scope the change set to the nine files named in section 2.
2. Run the seven inventory commands from section 4 and save the raw output; reconcile every hit against the audit table. If a hit has no table row and does not fit a listed baseline, stop and report — do not improvise.
3. Apply the fixes in this order, smallest blast radius first: (a) token-radius swaps and mono-numeral wraps in phase-02 pages (`AdminReceiptsPage`, `AccountPage`, `DashboardPage`, `RoutesPage`, `RouteOptimizerForm`, `ReceiptsPage`); (b) `fp-input` adoption in the three files that still duplicate the hand-rolled recipe (`AccountPage`, `RouteOptimizerForm`, `ReceiptsPage`); (c) the `FeedbackForm` surface/input alignment; (d) the two milestone-6 components (`DockGanttChart`, `FreightReconciliationPanel`) last, since they carry the largest single-file deltas.
4. Re-run the seven inventory commands and confirm the post-sweep expectations from section 4: zero arbitrary radii, zero `rounded-xl`/`rounded-2xl`/`rounded-3xl`, zero `shadow-[`, zero `backdrop-blur`, zero gradients, zero colored side stripes, zero teal/blue/orange/cyan, and violet only in the three preserved fraud-chip sites.
5. Do not touch the fraud chips (decision 2), the banner component, the primitives, `index.css`, any test file, or any handler/state/route.
6. Run the verification commands below from `apps/ops-console`. Fix nothing outside the sweep rules to make them pass — if a test fails, report it.

## 7. Acceptance checkpoints tied to source plan §12/§14

- **§12 (one accent family):** after the sweep, the only hues rendered are sky (accent), emerald/amber/rose (semantic state), violet (documented fraud-chip exception only), and red/green (documented freight-panel state semantics only). No decorative multi-accent composition remains anywhere in `apps/ops-console/src`.
- **§12 (mono numerals):** every data metric — dashboard stats, metric tiles, receipt amounts, shipment lane data, planning stats, admin confidence/amounts, account usage/plan figures, freight variance figures — renders mono + tabular; timestamps and axis/step indices remain the deliberate sans baseline.
- **§12 (shared primitives, no forks):** the hand-rolled input recipe is gone from `AccountPage`, `RouteOptimizerForm`, and `ReceiptsPage`; the hand-rolled row/card recipe is gone everywhere; all nested surfaces flow through `Panel`, `fp-row`, `fp-nested-surface`, or `fp-input`.
- **§13 step 9 complete:** sweep commands return the expected post-sweep inventories (section 4), documented in this blueprint's audit table (section 4, rows 1–33).
- **§13 step 10 adapted:** `npm run test`, `npm run typecheck`, and `npm run build` are green from `apps/ops-console`; the branch is merge-ready; **no deploy and no live verification ran and none may run before human UAT** (decision 6).
- **§12 hard rules:** copy, handlers, auth flows, routing, role gates, `data-testid` values, `aria-*` attributes, and load-bearing ids (`receipt-upload-input`, `contactPhone`, `horizon`) are untouched — the sweep is class-string-only.
- **§14 acceptance standard:** no page or component feels like it belongs to another design system; the console reads as one surface system end to end; operators scan faster, not slower.

## 8. Testing requirements

1. Run `npm run test` from `apps/ops-console` — all suites must stay green with **zero test-file edits** (including `workspaceSurfaces.smoke.test.tsx`, `ActivationBanner.test.tsx`, `ShellChrome.test.tsx`, `LoginFeedbackPanels.test.tsx`, `accountUsageUtils.test.ts`, `authErrors.test.ts`, `api.test.ts`).
2. Confirm the smoke suite still proves: fraud-chip copy absent when no flag is present (proving the preserved chips remain copy-identical), `activation-banner`/`milestone-chip-*`/`cap-pitch-banner` testids, the login channels, the dashboard metric hierarchy copy, and every phase-03 surface block.
3. Run `npm run typecheck` and `npm run build` from `apps/ops-console`; both must pass with no warnings introduced by the sweep.
4. **Explicitly not executed in this phase:** deploy, docker build/start, live URL checks, or any production verification — these run only after human-approved merge (decision 6).

## 9. Preservation notes (copy, handlers, auth, routing, gates, testids)

- **Copy:** zero copy edits in this phase — including chip labels, captions, empty states, placeholders, button labels, and error strings in every touched file.
- **Handlers/state:** no handler, state variable, effect, query, or mutation is touched; the diff is confined to JSX class strings.
- **Auth flows, routing, role gates:** `App.tsx`, `ProtectedRoute`, `AuthContext`, `allowedRoles`, all route paths, sidebar destinations, and page-level role gates (`admin` planning actions, `isAdminOrOwner` providers revoke, admin/owner `/admin/receipts`, admin-only danger zone) are untouched.
- **Pinned attributes:** `data-testid="activation-banner"`, `"activation-checklist"`, `"cap-pitch-banner"`, `milestone-chip-*`, `"login-signin-error"`, `"login-bootstrap-error"`, `"post-aha-toast"`; ids `receipt-upload-input`, `contactPhone`, `horizon`; `role="dialog"`/`aria-modal="true"` on the four dialogs; the typed-confirmation input's `aria-label` and disabled-until-match behavior — all unchanged.
- **Locked components:** `ActivationBanner` (both modes, cap-pitch hierarchy), all `ui/*` primitives, all `shell/*` modules, `index.css`, `Layout.tsx`, `ErrorBoundary`, `WorkspaceResetDangerZone`, `Dialog` — no edits.
- **Documented exceptions carried into UAT:** violet fraud chips (decision 2); red/green freight state colors (decision 4); `shadow-lg` on the floating `PostAhaToast` and `shadow-sm` on chart bars (approved elevation); `rounded-lg` control radius, `rounded-full` pill radius, `rounded-md` chart geometry, banner 20px radius, sans timestamps, chart axis labels (approved baselines).
- **Unrelated files:** do not touch `.gitignore`, `.opencode/agents/vision.md`, `apps/platform-api/tests_full_run.log`, `docs/adr/tech-backlog.md`, `docs/plans/console-ui-website-language-plan.md`, `PRODUCT.md`, or any other dirty/untracked file not named in section 2. The change set is the nine files in section 2 and nothing else.

## 10. Verification commands

Run from `apps/ops-console`:

- `npm run test`
- `npm run typecheck`
- `npm run build`

Then re-run the seven inventory commands from section 4 and confirm the expected post-sweep inventories. Deploy and live verification are deferred until after human-approved merge (decision 6).
