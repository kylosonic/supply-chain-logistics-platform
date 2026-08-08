# Phase 01 — Token-true surfaces (TECH-77 / NB-60)

**Status:** LOCKED for execution on branch `feat/console-login-color-fidelity`. @plan blueprint, drafted 2026-08-08. Source of truth: `docs/behaviors/console-login-color-fidelity.md` (§3, §5, §7), `docs/behaviors/pending-behaviors.md` (NB-60), `docs/plans/console-login-color-fidelity-plan.md` (§2 evidence), `apps/ops-console/src/index.css` (tokens L169–201, classes L203–257).

## 1. Goal

Make the five shared console surface classes in `apps/ops-console/src/index.css` render the design system's declared tokens (instead of near-black translucent slate overlays) so the login page and every console surface that uses them render in one true color language — the root-cause fix for NB-60, as a single atomic workstream.

## 2. Ground-truth decisions

### 2.1 Exact token mappings (the five classes)

| Class (current lines) | Current declarations | New declarations | Radius (kept) |
|---|---|---|---|
| `.fp-shell-surface` (L204–207) | `@apply border border-slate-800/70 bg-slate-900/45;` | `@apply border;` + `border-color: var(--fp-border);` + `background-color: var(--fp-surface);` | `var(--fp-radius-hero)` |
| `.fp-nested-surface` (L209–212) | `@apply border border-slate-800/70 bg-slate-950/75;` | `@apply border;` + `border-color: var(--fp-border);` + `background-color: var(--fp-elevated);` | `var(--fp-radius-panel)` |
| `.fp-pill` (L214–217) | `@apply inline-flex items-center gap-2 border border-slate-700/70 bg-slate-950/75 px-2.5 py-1 text-xs;` | `@apply inline-flex items-center gap-2 border px-2.5 py-1 text-xs;` + `border-color: var(--fp-border);` + `background-color: var(--fp-elevated);` | `var(--fp-radius-pill)` |
| `.fp-input` (L219–222) | `@apply w-full border border-slate-700/70 bg-slate-950/80 px-3.5 py-2.5 text-sm text-slate-100 transition-colors;` | `@apply w-full border px-3.5 py-2.5 text-sm transition-colors;` + `border-color: var(--fp-border);` + `background-color: var(--fp-input);` + `color: var(--fp-primary);` | `var(--fp-radius-panel)` |
| `.fp-row` (L247–251) | `@apply border border-slate-800/60 bg-slate-950/75 p-4;` | `@apply border p-4;` + `border-color: var(--fp-border);` + `background-color: var(--fp-elevated);` (keep the `transition` line verbatim) | `var(--fp-radius-panel)` |

Constraint notes the builder must honor:
- Tailwind v3 preflight defaults `border-color` to `currentColor`; the border color MUST therefore be set explicitly via `var(--fp-border)` on every class that keeps the `border` utility.
- `.fp-input::placeholder` (L224–226): replace `color: rgba(143, 161, 179, 0.72);` with `color: var(--fp-placeholder);`.
- `.fp-input:focus-visible` (L228–232): keep the block **verbatim** — it already references `var(--fp-focus-ring)` and the accent family. No change.
- `.fp-row:hover` (L253–256): keep **verbatim** (state overlay, not resting-surface; deferred to TECH-79 sweep review).
- `.fp-dialog-overlay` / `.fp-dialog-surface` (L235–244): **out of scope this phase** (modal chrome; near-black dimming intentional; TECH-79 sweep note).
- Do not alter any existing token *values* in `:root` (L169–201). Only **add** one token (2.3).

### 2.2 Decision: `.fp-pill` and `.fp-row` are aligned to tokens IN THIS PHASE

**Decision: align both.** Justification: NB-60 AC4 ("The same rendered colors appear everywhere the shared surfaces are used") + behavior §3.3. Retokenizing three of five leaves the console speaking two color languages. TECH-77 is the root-cause ticket; same file, same substitution pattern, class names unchanged (zero TSX churn). The TECH-79 sweep then covers only the regression guard, verification, and state-color review.

### 2.3 Decision: placeholder contrast — new dedicated token `--fp-placeholder: #94a3b8` (slate-400)

Measured WCAG 2.1 contrast ratios (computed with the standard relative-luminance formula; verified 2026-08-08):

| Role | Foreground | Background | Ratio | Verdict |
|---|---|---|---|---|
| Primary text | `--fp-primary` `#dbe4ee` | `--fp-elevated` `#111a26` | 13.62 : 1 | AA ✓ (also AAA) |
| Primary text | `--fp-primary` `#dbe4ee` | `--fp-input` `#233040` | 10.42 : 1 | AA ✓ |
| Secondary text | `--fp-secondary` `#8fa1b3` | `--fp-elevated` `#111a26` | 6.60 : 1 | AA ✓ |
| Secondary text | `--fp-secondary` `#8fa1b3` | `--fp-input` `#233040` | 5.05 : 1 | AA ✓ |
| Placeholder — current composite | `rgba(143,161,179,0.72)` ≈ `#708192` | `--fp-input` `#233040` | 3.34 : 1 | ✗ (exempt but illegible) |
| Placeholder — if `--fp-muted` used | `--fp-muted` `#5b6b7d` | `--fp-input` `#233040` | 2.45 : 1 | ✗ worse |
| **Placeholder — adopted** | **`#94a3b8` (slate-400)** | **`--fp-input` `#233040`** | **5.22 : 1** | **AA ✓** |
| Flag → TECH-78 (NB-61) | `--fp-muted` `#5b6b7d` | `--fp-elevated` `#111a26` | 3.20 : 1 | ✗ AA small text |
| Flag → TECH-78 (NB-61) | `--fp-muted` `#5b6b7d` | `--fp-surface` `#0d141d` | 3.39 : 1 | ✗ AA small text |

Decisions recorded:
1. **Placeholder token value:** `#94a3b8` (slate-400) — the lightest member of the slate family that is still a *slate*, clearing AA at 5.22:1 on `#233040` (slate-300 `#cbd5e1` at 9.02:1 would over-brighten the field).
2. **Do NOT retune `--fp-muted` (#5b6b7d).** It is declared verbatim in both the console (`index.css` L178) and the product site (`apps/product-web/src/app/globals.css` L18) — mutating it risks silent drift. Add dedicated token `--fp-placeholder: #94a3b8` with a one-line comment recording the contrast rationale.
3. **Flag for TECH-78 / NB-61:** `--fp-muted` on `--fp-elevated` (3.20:1) and on `--fp-surface` (3.39:1) fails AA for small text. TECH-78 must audit the login page's muted/helper text (LoginPage.tsx L89/L103/L116/L169/L185). NOT this phase.

## 3. Files to modify / create (exact, with why)

**Modify**
- `apps/ops-console/src/index.css` — the only production file touched in this phase.
  - In `:root` (tokens, L169–201): add `--fp-placeholder: #94a3b8;` with a comment recording the 5.22:1 decision. Do not reformat pre-existing indentation; minimize the diff.
  - In `@layer components` (L203–257): retokenize `.fp-shell-surface`, `.fp-nested-surface`, `.fp-pill`, `.fp-input` (incl. `::placeholder`), `.fp-row` per §2.1. Keep `.fp-dialog-overlay`, `.fp-dialog-surface`, `.fp-row:hover`, and all radius/transition lines.

**Create**
- `apps/ops-console/src/services/contrastRatio.ts` — pure WCAG relative-luminance + contrast-ratio module (no DOM, no framework). Reused by TECH-78.
- `apps/ops-console/src/services/contrastRatio.test.ts` — unit test pinning the hardcoded hex pairs from §2.3 with tolerance.
- `apps/ops-console/src/surfaceTokens.guard.test.ts` — static CSS-content guard (node env, pattern after `motion.guard.test.ts`): asserts the five classes reference `var(--fp-*)` tokens and no longer contain `bg-slate-*` overlays; asserts `--fp-placeholder` exists and `.fp-input::placeholder` uses it. This is the NB-62 regression-guard *seed* (TECH-79 extends it later).

**Explicitly NOT modified:** every `.tsx` consumer (zero churn — class names unchanged), `motion.guard.test.ts`, `workspaceSurfaces.smoke.test.tsx`, `Layout.smoke.test.tsx`, `product-web`.

## 4. Strict import / dependency map (CSS-only phase — no cross-file imports)

- `index.css`: zero imports change; consumes only its own `:root` custom properties. New dependency: `--fp-placeholder` → `.fp-input::placeholder`. Google Fonts `@import` (L1) and Tailwind directives (L3–5) untouched.
- `services/contrastRatio.ts`: zero imports — pure functions over hex strings using only `Math`. Type surface: `contrastRatio(hexA: string, hexB: string): number` (throws on malformed hex) and `wcagAAContrast(hexFg: string, hexBg: string): boolean` (≥ 4.5:1). No new dependencies.
- `services/contrastRatio.test.ts`: imports `{ describe, expect, it }` from `'vitest'` and `{ contrastRatio }` from `'./contrastRatio'`.
- `surfaceTokens.guard.test.ts`: imports `{ describe, expect, it }` from `'vitest'`, `{ readFileSync }` from `'node:fs'`, `{ join }` from `'node:path'`, `{ fileURLToPath }` from `'node:url'` — identical to `motion.guard.test.ts`. Reads `index.css` via a path resolved from `import.meta.url`.

## 5. Step-by-step execution (for @build; TDD order)

1. Write `services/contrastRatio.ts` and `services/contrastRatio.test.ts` first (hardcoded pairs from §2.3, tolerance ±0.05). Run the test — green.
2. Write `surfaceTokens.guard.test.ts` asserting: each of the five class blocks contains its mandated `background-color: var(--fp-*)` / `border-color: var(--fp-border)` reference; `.fp-input` block contains `color: var(--fp-primary)` and its `::placeholder` block contains `var(--fp-placeholder)`; the token block declares `--fp-placeholder: #94a3b8`; none of the five class blocks contains `bg-slate-950`, `bg-slate-900`, `bg-slate-800`, or `bg-slate-700`. Run it — **must fail red** against current CSS.
3. In `index.css` `:root`, add `--fp-placeholder: #94a3b8;` (comment: contrast 5.22:1 on `--fp-input`). No other token changes.
4–8. Retokenize `.fp-shell-surface`, `.fp-nested-surface`, `.fp-pill`, `.fp-input` (keep radius, `transition-colors`, `:focus-visible` verbatim; retokenize `::placeholder`), `.fp-row` (keep `transition` + `.fp-row:hover` verbatim).
9. Run the guard test — green. Run full suite, typecheck, build, lint (commands §7).
10. Verify `git diff --stat` shows only `index.css` plus the three new files; `git diff apps/ops-console/src/pages apps/ops-console/src/components` empty.
11. Do NOT commit. Hand the diff to @qa for audit; commit only after @qa approval.

## 6. Acceptance checkpoints (tied to NB-60 verbatim)

| NB-60 AC (verbatim) | Evidence artifact this phase |
|---|---|
| 1. "…the page background, main panels, and nested panels are each visibly distinct — no near-black stacking…" | `.fp-shell-surface`→`#0d141d` (vs canvas `#0a0f16`), `.fp-nested-surface`→`#111a26`; luminance ordering `#0a0f16 < #0d141d < #111a26 < #233040`; guard test pins tokens; @qa visual sweep of login page. |
| 2. "Input fields … visibly lighter than the panel they sit in, with a clear border and a readable placeholder; focused fields show the cyan focus treatment." | `.fp-input`→`#233040` (lighter than `#111a26`), border `var(--fp-border)`, placeholder `--fp-placeholder` at 5.22:1, `:focus-visible` unchanged (`var(--fp-focus-ring)`). |
| 3. "The rendered colors match the color values the design system declares…" | Guard test asserts the exact `var(--fp-*)` references; no `bg-slate-*` overlays remain in the five classes. |
| 4. "The same rendered colors appear everywhere the shared surfaces are used across the console…" | All five shared classes retokenized (incl. `.fp-row`/`.fp-pill`); @qa blast-radius sweep of the 22 consumer files (§8); all render-path smoke tests green. |

## 7. Test plan (node env — what CAN be tested)

1. **Static CSS-content guard** (`src/surfaceTokens.guard.test.ts`) — content-level proof; NB-62 regression-guard seed.
2. **Contrast unit test** (`src/services/contrastRatio.test.ts`) — hardcoded hex pairs: 13.62 primary/elevated; 10.42 primary/input; 6.60 secondary/elevated; 5.05 secondary/input; 2.45 muted/input (documents exemption); 5.22 placeholder/input; AA-boolean helper on the boundary.
3. **Consumer render-path smoke (existing, must stay green — no edits):** `src/pages/workspaceSurfaces.smoke.test.tsx`, `src/components/Layout.smoke.test.tsx` (asserts `fp-nested-surface` presence L144), `src/motion.guard.test.ts` (slices `.fp-row {`…`.fp-row:hover` L62–66 — no `animation:` in block; hover block still present).
4. **QA human visual sweep:** login page panel/field distinction + dashboard spot-check (NB-62 AC3), scheduled after this workstream's verification, before merge.

## 8. Console-wide blast radius — every consumer of the five classes (for @qa)

Source definitions: `src/index.css` L204 (shell), L209 (nested), L214 (pill), L219 (input + placeholder L224 + focus L228), L247 (row + hover L253).

**Components (10 files):** `components/CsvUploadPanel.tsx` (fp-input L103; fp-row L108), `components/FreightReconciliationPanel.tsx` (fp-nested-surface L71/L75/L81), `components/WorkspaceResetDangerZone.tsx` (fp-input L69), `components/Layout.tsx` (fp-nested-surface L22), `components/FeedbackForm.tsx` (fp-nested-surface L23; fp-input L36/L52/L62), `components/RouteOptimizerForm.tsx` (fp-input L73; fp-nested-surface L130/L134/L154/L170; fp-row L194), `components/ui/PageHeader.tsx` (fp-shell-surface L12), `components/ui/Panel.tsx` (fp-nested-surface L22), `components/shell/ShellSidebar.tsx` (fp-shell-surface L79/L93/L108), `components/shell/ShellHeader.tsx` (fp-shell-surface L12; fp-pill L34/L35).

**Pages (12 files):** `pages/LoginPage.tsx` (fp-shell-surface L82/L111; fp-nested-surface L102/L113/L168; fp-input L132/L146), `pages/DashboardPage.tsx` (fp-shell-surface L221; fp-nested-surface L320/L326/L340/L345/L356), `pages/AccountPage.tsx` (fp-input L195; fp-shell-surface L224; fp-nested-surface L255/L260/L316/L351/L382/L461; fp-row L417), `pages/AdminReceiptsPage.tsx` (fp-input L100/L490/L502/L515/L524), `pages/ReceiptsPage.tsx` (fp-row L24/L229; fp-input L90/L193; fp-nested-surface L215), `pages/ShipmentsPage.tsx` (fp-input L62/L193/L197/L201/L205/L209; fp-row L242; fp-nested-surface L277), `pages/AlertsPage.tsx` (fp-input L63/L215/L222/L230/L252; fp-row L278; fp-nested-surface L320), `pages/PlanningPage.tsx` (fp-input L63/L175; fp-nested-surface L235; fp-row L259), `pages/RoutesPage.tsx` (fp-row L136), `pages/ProvidersPage.tsx` (fp-row L111; fp-input L148/L159/L171), `pages/UploadPage.tsx` (fp-pill L24), `pages/UnauthorizedPage.tsx` (fp-shell-surface L4).

**Tests touching these classes (must remain green; do not edit):** `components/Layout.smoke.test.tsx` L144; `motion.guard.test.ts` L62–66; `pages/workspaceSurfaces.smoke.test.tsx` (indirect).

Expected visual deltas @qa must verify per surface: panels/rows/pills lift from ≈`#050a14` to `#111a26`, shell surfaces to `#0d141d`, inputs from ≈`#04070f` to `#233040` (visibly lighter than containers), borders to `#1f2a37`, input text to `--fp-primary`, placeholders brighten to slate-400.

## 9. Verification commands (run from `apps/ops-console`)

- `npm test` — full vitest suite incl. new guard + contrast tests (green).
- `npm run typecheck` — `tsc --noEmit`.
- `npm run build` — `tsc --noEmit && vite build`.
- `npm run lint` — `--max-warnings=0`; CSS invisible to eslint; new TS files must be lint-clean.

## 10. Preservation notes

- **Copy, handlers, routes, role gates, data-testids:** zero `.tsx` files change — class names untouched, preserved by construction.
- **Existing tokens:** no existing token *value* changes — console `:root` stays in verbatim parity with `apps/product-web/src/app/globals.css` (L14–22). Only `--fp-placeholder` added.
- **`.fp-row:hover` and `.hover-lift`:** preserved verbatim (state overlays; TECH-79 sweep review).
- **`.fp-dialog-overlay` / `.fp-dialog-surface`:** untouched (modal chrome; near-black dimming intentional).
- **Motion block:** `prefers-reduced-motion` (L259–264) and all keyframes untouched.
- **Unrelated files:** do not reformat the token block's irregular indentation; do not touch scrollbar/selection/focus/skip-to-content/responsive-grid sections.
- **Git discipline:** no intermediate commits; atomic commit only after @qa approval; no push; halt for human UAT gate (login visual + dashboard spot-check) before merge.
