# Console Login Color Fidelity — Implementation Plan

**Status:** LOCKED by the human (2026-08-08). PM plan artifact — no implementation authority. Hand off to `@architect` for execution. Tickets: NB-60..NB-62 (`pending-behaviors.md`), TECH-77..79 (`tech-backlog.md`), living behaviors in `console-login-color-fidelity.md`.

**Scope:** `apps/ops-console` only. Fixes the login page (and, at the root, every console surface) rendering colors the design system does not declare.

---

## 1. Problem statement (from the operator's seat)

The login page is the front door, and it renders darker and flatter than the product intends: panels barely distinct from the background, input fields that don't read as fields, small text that is hard to read. The design system declares a deliberate color ladder; the components ignore it and render near-black overlays instead.

## 2. Confirmed root cause (evidence for @plan/@build)

The console's declared tokens in `apps/ops-console/src/index.css` `:root`:

| Token | Declared | Purpose |
|---|---|---|
| `--fp-surface` | `#0d141d` | shell panels |
| `--fp-elevated` | `#111a26` | nested panels |
| `--fp-input` | `#233040` | input fields |
| `--fp-border` | `#1f2a37` | borders |
| `--fp-muted` / `--fp-secondary` | `#5b6b7d` / `#8fa1b3` | muted / secondary text |
| `--fp-primary` | `#dbe4ee` | primary text |
| `--fp-accent` | `#38bdf8` | cyan accent |

The shared component classes ignore them and render translucent slate overlays instead:

| Class | Current | Renders ≈ | Declared |
|---|---|---|---|
| `fp-shell-surface` (L203–206) | `bg-slate-900/45` | `#0c121a` | `--fp-surface` `#0d141d` |
| `fp-nested-surface` (L208–211) | `bg-slate-950/75` | `#050a14` | `--fp-elevated` `#111a26` |
| `fp-input` (L218–231) | `bg-slate-950/80` | `#04070f` | `--fp-input` `#233040` |

Stacked on the `#0a0f16` canvas, the login page renders three near-black layers with the **inputs darker than their container** — fields don't look like fields. Secondary finding: 11–12px `text-slate-500` sites on `LoginPage.tsx` (L89, L103, L116, L169, L185) sit at ~4.0:1 contrast, below WCAG AA's 4.5:1 for small text.

## 3. The three workstreams (one ticket each)

| Workstream | Ticket | What the operator gets |
|---|---|---|
| A. Token-true surfaces | NB-60 / TECH-77 | Shared surface/input classes render the declared tokens. Panels are visible panels, fields are visibly lighter than their panel with clear borders, everywhere the classes are used. |
| B. Login text contrast | NB-61 / TECH-78 | Every small text element on the login page meets AA contrast; hierarchy preserved; cyan-only accent with rose for errors only. |
| C. Regression guard + verification | NB-62 / TECH-79 | Static guard pins the classes to the tokens (no silent drift), full suite + typecheck + build green, visual UAT checklist. |

## 4. Hard rules

- Preserve all login copy verbatim; preserve handlers, auth flows, routing, role gates, and test markers.
- No new external libraries. No decorative gradients or glow. One cyan accent family; rose only for error states.
- The shared classes are used console-wide — the surface change is the root-cause fix, and @qa must sweep the blast radius (phase-2/3 surfaces) so nothing regresses visually.
- The behavior doc (`console-login-color-fidelity.md`) is the acceptance source of truth; @qa audits against each ticket's criteria in `pending-behaviors.md`.

## 5. Execution order for @architect

1. **TECH-77** (shared classes → tokens; console-wide QA sweep) — the root cause; fixes login and every surface at once.
2. **TECH-78** (login small-text contrast; accent audit) — the polish on top of the correct surfaces.
3. **TECH-79** (static regression guard + smoke updates + full verification) — locks the fix in.
Each workstream is its own atomic commit on `feat/console-login-color-fidelity`. After all workstreams: full verification, then halt for the human's hands-on UAT (login page visual check + dashboard spot-check, since the surfaces are shared) before any merge to `master`.

## 6. Acceptance standard

This plan is complete when the behavior doc's §7 standard holds: the login page renders distinct, intentional panels and fields that look like fields, in the same color language as the rest of the product; every text element on the login page meets readable contrast; the shared surfaces render identically everywhere; a regression guard prevents silent color drift; and the full console suite, typecheck, and build pass.

---

## Handoff note

Tickets are written and the ledger is updated. Ready for `@architect` to open the batch: branch `feat/console-login-color-fidelity`, blueprints per workstream, TDD, @qa audit per ticket, atomic commits, then the human UAT gate before merge.
