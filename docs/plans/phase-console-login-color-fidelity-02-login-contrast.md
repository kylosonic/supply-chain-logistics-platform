# Phase 02 — Login small-text contrast (TECH-78 / NB-61)

**Status:** LOCKED for execution on branch `feat/console-login-color-fidelity`. @plan blueprint, 2026-08-08. Source of truth: `docs/behaviors/console-login-color-fidelity.md` (§4, §5, §7), `docs/behaviors/pending-behaviors.md` (NB-61), `docs/plans/console-login-color-fidelity-plan.md` (§2 secondary finding), `docs/plans/phase-console-login-color-fidelity-01-token-surfaces.md` (§2.3 flagged pairs), `apps/ops-console/src/index.css` (tokens L169–203), `apps/ops-console/src/services/contrastRatio.ts`.

## 1. Goal

Raise the five 11–12px `text-slate-500` sites on `apps/ops-console/src/pages/LoginPage.tsx` to the slate-400 step so every small text element on the login page meets WCAG AA (≥ 4.5:1) on the Phase 01 token surfaces, with the slate ladder and the rose-for-errors-only discipline preserved — one atomic workstream, no copy or behavior changes.

## 2. Ground-truth decisions

### 2.1 Token-vs-utility decision: use the plain Tailwind utility `text-slate-400`

**Decision: `text-slate-400` (#94a3b8), not `text-[color:var(--fp-secondary)]`.** Justification:
1. **Codebase convention:** every TSX file uses raw Tailwind utilities for text color; zero usage of `var(--fp-secondary)`/`var(--fp-muted)` in TSX. Tokens are consumed only inside `index.css` component classes.
2. **Already-adopted color:** Phase 01 chose `--fp-placeholder: #94a3b8` (slate-400). Using `text-slate-400` in TSX makes login small text and input placeholders the same declared color — one color language (behavior §3.3).
3. **AA compliance proven:** slate-400 = **7.22:1 on `--fp-surface`**, **6.83:1 on `--fp-elevated`** (exact `contrastRatio` math; verified against all seven Phase 01 pins). The token alternative `--fp-secondary` #8fa1b3 (6.98:1 / 6.60:1) also passes but introduces a novel class pattern for zero extra margin.
4. **Slate-family constraint:** slate-400 is a slate; NB-61 AC3 "no new hues" holds.

### 2.2 Per-site changes (exact, with computed ratios)

| Site | Current class | Change | FG → BG | Ratio before → after | Verdict |
|---|---|---|---|---|---|
| L89 eyebrow "FreightPilot workspace" (12px, uppercase) | `text-slate-500` | → `text-slate-400` | `#64748b` → `#94a3b8` on `--fp-surface` `#0d141d` | 3.89 → 7.22 | FAIL → PASS |
| L103 value-point labels (11px, uppercase) | `text-slate-500` | → `text-slate-400` | on `--fp-elevated` `#111a26` | 3.68 → 6.83 | FAIL → PASS |
| L116 eyebrow "Control tower login" (12px, uppercase) | `text-slate-500` | → `text-slate-400` | on `--fp-surface` | 3.89 → 7.22 | FAIL → PASS |
| L169 helper copy "New workspace? …" (12px) | `text-slate-500` | → `text-slate-400` | on `--fp-elevated` | 3.68 → 6.83 | FAIL → PASS |
| L185 bootstrap link "Create initial admin (first-time setup)" (12px, secondary action) | `text-slate-500` + `hover:text-slate-300` | → `text-slate-400`; **hover stays `text-slate-300`** | on `--fp-surface` | 3.89 → 7.22 | FAIL → PASS |

Only the `text-slate-500` token inside each of the five `className` strings changes. Copy, element type, surrounding utilities, hover/disabled states, and line structure stay byte-identical otherwise.

### 2.3 Full login-page color/contrast sweep (every text color, on the NEW surfaces)

| # | Site | Color | Background | Ratio | Verdict |
|---|---|---|---|---|---|
| 1 | L89 eyebrow | slate-500 → slate-400 | shell `#0d141d` | 3.89 → **7.22** | **FAIL → FIX** |
| 2 | L93 body helper (14px) | slate-400 `#94a3b8` | shell `#0d141d` | 7.22 | PASS (stays) |
| 3 | L103 value-point labels | slate-500 → slate-400 | elevated `#111a26` | 3.68 → **6.83** | **FAIL → FIX** |
| 4 | L104 value-point titles | slate-200 `#e2e8f0` | elevated `#111a26` | 14.20 | PASS (stays) |
| 5 | L116 eyebrow | slate-500 → slate-400 | shell `#0d141d` | 3.89 → **7.22** | **FAIL → FIX** |
| 6 | L120 body helper (14px) | slate-400 `#94a3b8` | shell `#0d141d` | 7.22 | PASS (stays) |
| 7 | L127 / L141 field labels | slate-300 `#cbd5e1` | elevated `#111a26` | 11.79 | PASS (stays) |
| 8 | Input value text | `--fp-primary` `#dbe4ee` via `.fp-input` | input `#233040` | 10.42 | PASS (Phase 01) |
| 9 | Input placeholders | `--fp-placeholder` `#94a3b8` via `.fp-input::placeholder` | input `#233040` | 5.22 | PASS (Phase 01) |
| 10 | L85 / L157 "FP" badge + primary button text | slate-950 `#020617` | accent sky-500 `#0ea5e9` | 7.28 | PASS (accent, stays) |
| 11 | L172 link "Create company account →" | sky-400 `#38bdf8` | elevated `#111a26` | 8.17 | PASS (accent, stays) |
| 12 | L169 helper copy | slate-500 → slate-400 | elevated `#111a26` | 3.68 → **6.83** | **FAIL → FIX** |
| 13 | L185 bootstrap link | slate-500 → slate-400 (hover slate-300 stays) | shell `#0d141d` | 3.89 → **7.22** | **FAIL → FIX** |
| 14 | L90 h1 | slate-100 `#f1f5f9` | shell `#0d141d` | 16.89 | PASS (stays) |
| 15 | L117 h2 | slate-100 `#f1f5f9` | elevated `#111a26` | 15.98 | PASS (stays) |
| 16 | Feedback panels (rose text) | rose-300 `#fda4af` on rose-950/30 over elevated = composite `#231422` | `#231422` | 9.30 | PASS — `LoginFeedbackPanels.tsx` **NOT modified** |

**Flags from Phase 01 §2.3 — disposition:**
- `--fp-muted` `#5b6b7d` (3.20:1 elevated, 3.39:1 surface, 2.45:1 input): **FAIL for small text but used NOWHERE on the login page** — note only, no fix (token frozen in parity with product-web).
- `slate-500` on canvas `#0a0f16` (4.04:1): **not applicable** — no login text sits directly on the canvas.
- `slate-500` on input `#233040` (2.81:1): **not applicable** — input text/placeholder are token-driven.

**Post-fix hierarchy (NB-61 AC2):** slate ladder intact — eyebrows/helper/bootstrap (slate-400) < labels (slate-300) < value-point titles (slate-200) < titles (slate-100). Eyebrows stay distinct via uppercase + weight + tracking; bootstrap link stays subordinate to the sky-400 primary link via size/weight, slate-300 hover preserved.

## 3. Files to modify / create (exact)

**Modify**
- `apps/ops-console/src/pages/LoginPage.tsx` — the only production file touched. Five `className` strings (L89, L103, L116, L169, L185): `text-slate-500` → `text-slate-400`. Nothing else changes.
- `apps/ops-console/src/services/contrastRatio.test.ts` — extend `PINNED_PAIRS` and the AA-helper block with the new pairs from §2.3 (±0.05 tolerance). Module untouched; test data only.

**Create**
- `apps/ops-console/src/loginContrast.guard.test.ts` — static TSX-content guard (node env, pattern after `surfaceTokens.guard.test.ts`): reads `LoginPage.tsx` and `LoginFeedbackPanels.tsx`; asserts banned low-contrast text utilities `text-slate-500` and `text-slate-600` appear nowhere in either; asserts `LoginPage.tsx` still contains `text-slate-400` and `hover:text-slate-300`; asserts `LoginFeedbackPanels.tsx` still contains `text-rose-300`. NB-62 guard's text-side seed.

**Explicitly NOT modified:** `index.css` (frozen from Phase 01), `LoginFeedbackPanels.tsx` (rose-300 at 9.30:1 passes), `contrastRatio.ts`, all smoke tests, all other console pages, `product-web`.

## 4. Strict import / dependency map

- `pages/LoginPage.tsx`: **zero import changes** — five string literals inside `className` only.
- `services/contrastRatio.test.ts`: imports unchanged; new data only.
- `loginContrast.guard.test.ts` (new): `node:fs`/`node:path`/`node:url`/vitest — identical set to `surfaceTokens.guard.test.ts`; resolves paths from `import.meta.url`.
- No new external libraries (behavior §6).

## 5. Step-by-step execution (for @build; TDD order)

1. Extend `services/contrastRatio.test.ts` first: pinned pairs `#94a3b8/#0d141d = 7.22`, `#94a3b8/#111a26 = 6.83`, `#64748b/#0d141d = 3.89` (documents fixed FAIL), `#64748b/#111a26 = 3.68` (documents fixed FAIL), `#8fa1b3/#0d141d = 6.98` (documents rejected token alternative), `#fda4af/#231422 = 9.30` (rose panel PASS; `#231422` = alpha-composite `0.3 × #4c0519 + 0.7 × #111a26`, comment it), plus `wcagAAContrast` assertions (true for 7.22/6.83/9.30, false for 3.89/3.68). Run — green.
2. Write `loginContrast.guard.test.ts`. Run — **must fail red** against current `LoginPage.tsx` (5 × `text-slate-500` present).
3. Edit `LoginPage.tsx` L89, L103, L116, L169, L185: `text-slate-500` → `text-slate-400`. No other token changes.
4. Run the guard — green. Run full suite, typecheck, build, lint.
5. Verify `git diff --stat` shows exactly `LoginPage.tsx` (5 one-token diffs), `contrastRatio.test.ts`, and the new guard file; `git diff` on `index.css`, `LoginFeedbackPanels.tsx`, and smoke tests empty.
6. Do NOT commit. Hand to @qa; commit only after approval.

## 6. Acceptance checkpoints (tied to NB-61 verbatim)

| NB-61 AC (verbatim) | Evidence artifact this phase |
|---|---|
| 1. "Every text element on the login page — eyebrows, helper copy, secondary actions — meets WCAG AA contrast for small text against its background." | §2.3 sweep: all 16 sites PASS after the five edits; contrast unit test pins every pair; static guard bans `text-slate-500`/`text-slate-600` from both login files. |
| 2. "Hierarchy is preserved: labels read as labels, body text as body text, titles as titles — nothing flattens into one gray mass." | Slate ladder preserved (400 < 300 < 200 < 100); eyebrows keep uppercase/weight/tracking; bootstrap `hover:text-slate-300` untouched; guard asserts it. |
| 3. "The login page uses one cyan accent family … rose appears only for error states; no new hues are introduced." | slate-400 is slate-family; sky-400 link, sky-500 badge/button, rose-300 error panels untouched (9.30:1 pinned); guard asserts `text-rose-300` remains. |

## 7. Test plan (node env)

1. **Contrast unit additions** — six new pinned pairs; same `it.each` + ±0.05 style; `wcagAAContrast` boundary assertions.
2. **Static TSX guard** (`loginContrast.guard.test.ts`) — absence of the only failing utilities + pinned ratio tests is the invariant. Deliberately does not assert copy.
3. **Existing tests must stay green — no edits:** `LoginFeedbackPanels.test.tsx`, `workspaceSurfaces.smoke.test.tsx`, `Layout.smoke.test.tsx`, `surfaceTokens.guard.test.ts`, `motion.guard.test.ts`. No LoginPage smoke test exists today; none proposed.
4. **@qa audit:** diff review of the five one-token changes against §2.2 + visual login-page check in the NB-62 UAT gate.

## 8. Verification commands (run from `apps/ops-console`)

- `npm test`, `npm run typecheck`, `npm run build`, `npm run lint` (zero warnings on new files; pre-existing baseline untouched).
- `git diff --stat` — exactly the three files; `git diff -- apps/ops-console/src/index.css apps/ops-console/src/components/login/LoginFeedbackPanels.tsx` empty.

## 9. Preservation notes

- **Copy verbatim:** every string byte-identical — only five `className` tokens change.
- **Handlers & flows:** `onSubmit`, `onBootstrapInitialAdmin`, `getErrorMessage`, `login`, `registerApi`, `bootstrapErrorMessage`, signup-URL fallback, `isAuthenticated` redirect untouched.
- **Routes / role gates / test markers:** none on login page; `data-testid="login-signin-error"`/`"login-bootstrap-error"` live in unmodified `LoginFeedbackPanels.tsx`.
- **Hover/disabled states:** bootstrap link keeps `hover:text-slate-300` + underline; button keeps `disabled:opacity-60`.
- **Tokens & surfaces:** `index.css` frozen — no token value or class changes.
- **Unrelated dirty files (do NOT touch or stage):** `.gitignore`, `.opencode/agents/vision.md`, `docs/adr/tech-backlog.md`, `docs/behaviors/pending-behaviors.md`; untracked `apps/platform-api/tests_full_run.log`, `docs/plans/phase-console-login-color-fidelity-01-token-surfaces.md`.
- **Git discipline:** no intermediate commits; atomic commit after @qa approval; no push; UAT gate before merge.
