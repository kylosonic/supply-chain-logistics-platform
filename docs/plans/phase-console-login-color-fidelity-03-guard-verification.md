# Phase 03 — Regression-guard consolidation & verification (TECH-79 / NB-62)

**Status:** LOCKED for @build execution on branch `feat/console-login-color-fidelity`. @plan blueprint, 2026-08-08. Source of truth: `docs/behaviors/console-login-color-fidelity.md` (§7), `docs/behaviors/pending-behaviors.md` (NB-62), `docs/plans/console-login-color-fidelity-plan.md` (§3 workstream C, §5, §6), `docs/adr/tech-backlog.md` (TECH-79). Phases 1–2 committed and QA-approved (`2550841`, `daaeac2`).

## 1. Goal

Close the final workstream of the console login color fidelity batch: consolidate and complete the regression-guard coverage seeded in phases 1–2 (test-only), prove no smoke assertions are affected, run the full verification gate, and deliver the human UAT checklist — with **zero production code changes**.

## 2. Ground-truth decisions (verified against the working tree)

### 2.1 Guard gap analysis — one residual gap, one test-only fix

**Already covered (verified, `surfaceTokens.guard.test.ts`, 7 test blocks):**
- The five shared classes each reference their mandated `background-color: var(--fp-*)` and `border-color: var(--fp-border)` tokens; none contains `bg-slate-950/900/800/700`.
- `.fp-input` contains `color: var(--fp-primary);` and `.fp-input::placeholder` contains `color: var(--fp-placeholder);`.
- The token block declares `--fp-placeholder: #94a3b8;`.

**Residual gap (verified): token-block integrity is NOT guarded.** The `tokenBlock()` helper slices `:root`, but the only declaration-side assertion is `--fp-placeholder`. The other five load-bearing tokens (`--fp-surface: #0d141d`, `--fp-elevated: #111a26`, `--fp-input: #233040`, `--fp-border: #1f2a37`, `--fp-primary: #dbe4ee` — all present at `index.css` L171–182) are only asserted on the *reference* side. If a future commit deleted one of them, every existing assertion would still pass while the class silently resolves to nothing — precisely the "color drift silently returns" failure NB-62 is named for.

**Decision:** add **one** new test block to `surfaceTokens.guard.test.ts` asserting the five token declarations appear verbatim in the token block with their phase-1 values (reuse the existing `tokenBlock()` helper; exact-match style of the existing placeholder assertion). Exactly five contains checks in one `it` block. No other guard changes. `loginContrast.guard.test.ts` is complete — no changes. Adjacent guards untouched.

### 2.2 Smoke verification — NO smoke test edits needed

- `workspaceSurfaces.smoke.test.tsx` L310 asserts `bg-emerald-400` (live-sync dot, `DashboardPage.tsx` literal untouched) — unaffected; smoke renders class strings, not computed styles.
- L482 asserts `not bg-white` (Unauthorized fallback) — `fp-shell-surface` class name intact — unaffected.
- `Layout.smoke.test.tsx` L144 asserts `fp-nested-surface` presence — class name intact — unaffected.
- `motion.guard.test.ts` L62–66 `.fp-row` slice — no `animation:`, hover block present — unaffected.
- `services/internalNavGuard.test.ts` — TS/TSX nav patterns only — unaffected.

**Explicit statement:** zero smoke test edits.

### 2.3 Zero-production-change decision + adjudication flags

**Decision: this phase touches NO production code.** The only code change is the single test-block addition to `surfaceTokens.guard.test.ts`.

**Flagged for @architect adjudication (recommended: no action, do NOT expand scope):**
1. `.fp-row:hover` uses hardcoded rgba state-overlay values — state treatment, consistent with existing raw-rgba state patterns (focus ring, scrollbar thumb); outside NB-62 AC1 (resting classes all reference tokens).
2. `.fp-dialog-overlay` / `.fp-dialog-surface` still use `bg-slate-950/80` / `bg-slate-950` — documented intentional exclusion (modal chrome, near-black dimming).
3. Token *values* pinned by this phase's new assertion — any future deliberate token retune must update the guard in the same commit. Intended friction.

## 3. Files to modify / create (test-only)

- **Modify:** `apps/ops-console/src/surfaceTokens.guard.test.ts` — add one new `it` block asserting the token block declares `--fp-surface: #0d141d;`, `--fp-elevated: #111a26;`, `--fp-input: #233040;`, `--fp-border: #1f2a37;`, `--fp-primary: #dbe4ee;` (exact-match contains checks via `tokenBlock()`). Update the file header comment's blueprint reference. **No import changes.**
- **Create:** this blueprint (persisted by the orchestrator).
- **Explicitly NOT modified:** `index.css`, `LoginPage.tsx`, `LoginFeedbackPanels.tsx`, `loginContrast.guard.test.ts`, `motion.guard.test.ts`, `services/internalNavGuard.test.ts`, `services/contrastRatio.ts`, `services/contrastRatio.test.ts`, all smoke tests, all other console pages/components, `product-web`.

**Strict import map:** zero import changes; path resolution via `import.meta.url` unchanged.

## 4. Step-by-step execution (for @build)

1. Read `surfaceTokens.guard.test.ts`; add the single new `it` block per §3. Do NOT touch the other six blocks.
2. Run only the guard file: `npx vitest run src/surfaceTokens.guard.test.ts` — green on first run (verification-phase guard against already-correct state; no red-green cycle, no production change follows).
3. Run the full verification gate (§6) from `apps/ops-console`.
4. Run the scope checks (§6).
5. Do NOT commit. Hand the diff to @qa; commit atomically only after approval.

## 5. Acceptance checkpoints (tied to NB-62 verbatim)

| NB-62 AC (verbatim) | Evidence artifact this phase |
|---|---|
| 1. "A regression guard exists that fails the build if the shared surface or input classes stop referencing the declared color tokens." | `surfaceTokens.guard.test.ts` proves both sides: reference side (7 blocks) + declaration side (new block pinning the five tokens in `:root`). `loginContrast.guard.test.ts` pins the login text side. |
| 2. "The full console test suite, typecheck, and build pass with the color changes in place." | `npm test`, `npm run typecheck`, `npm run build`, `npm run lint` (zero warnings) green from `apps/ops-console`. |
| 3. "A human visual check of the login page (and a spot-check of the dashboard, which shares the surfaces) confirms the rendered colors match the declared system." | UAT checklist (§7) documented in this plan + commit docs note + closeout ledger entry; **hard halt for human UAT before any merge to `master`**. NB-62 is not marked IMPLEMENTED until UAT passes. |

## 6. Verification commands (run from `apps/ops-console`)

- `npm test`, `npm run typecheck`, `npm run build`, `npm run lint` (`--max-warnings=0`).
- **Scope check 1:** `git diff --stat master...HEAD -- apps/ops-console/src` lists exactly: `index.css`, `pages/LoginPage.tsx`, `surfaceTokens.guard.test.ts`, `loginContrast.guard.test.ts`, `services/contrastRatio.ts`, `services/contrastRatio.test.ts`. Phase 3's own delta is `surfaceTokens.guard.test.ts` only.
- **Scope check 2:** `git status --short` shows no new churn under `apps/ops-console` beyond the guard file; pre-existing unrelated dirty files must NOT be staged.

## 7. UAT checklist (verbatim, ready to paste into the commit docs note and closeout ledger entry)

**Console Login Color Fidelity — Final UAT Checklist (TECH-79 / NB-62)**

*Login page — visual check:*
1. Panels are visibly distinct: page background, main panels, and nested panels each read as deliberate, separate surfaces — no near-black stacking; panel borders are clearly visible.
2. Input fields are visibly lighter than the panel they sit in, with a clear border; placeholders are readable at a glance.
3. All small text — eyebrows, helper copy, secondary actions — is readable against its background (no hard-to-read gray text).
4. Focusing a field shows the cyan focus treatment; the primary action and links use the cyan accent family.
5. Rose/red appears only on the error panels — nowhere else on the page.
6. One cyan accent family throughout; no new hues anywhere.

*Dashboard spot-check (shared surfaces):*
7. Panels, rows, pills, and inputs render the same token colors as the login page — the console never disagrees about what a panel or a field looks like.
8. Contrast spot-check: any helper/secondary text visible during the spot-check is readable against its surface.

*Reference values (declared system):* canvas `#0a0f16`; surface `#0d141d`; elevated `#111a26`; input `#233040`; border `#1f2a37`; primary text `#dbe4ee`; placeholder `#94a3b8`; accent `#38bdf8`.

## 8. Preservation notes

- **Zero production churn:** no `.tsx`, no CSS, no services touched; `index.css` frozen from Phase 01; `LoginPage.tsx` frozen from Phase 02.
- **Adjacent guards untouched:** `loginContrast.guard.test.ts`, `motion.guard.test.ts`, `services/internalNavGuard.test.ts`.
- **Smoke tests untouched:** byte-identical.
- **Copy, handlers, routes, role gates, test markers:** preserved by construction.
- **Deliberate exclusions documented (do not "fix"):** `.fp-dialog-overlay`/`.fp-dialog-surface`, `.fp-row:hover` — if @architect rules otherwise, new ticket.
- **Documentation hygiene:** the behavior doc's `NOT YET IMPLEMENTED` banner and the NB-62 `[IMPLEMENTED]` flip are ledger duties post-UAT.
- **Git discipline:** no intermediate commits; atomic commit after @qa approval; no push; hard halt for human UAT before merge.
