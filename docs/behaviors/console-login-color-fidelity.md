# Console Login Color Fidelity — Living Behaviors

> ⚠️ **NOT YET IMPLEMENTED** — This feature is locked but not built. Tickets: NB-60..NB-62 in `pending-behaviors.md`. Handoff prepared for `@architect`; blueprint + TDD execution pending. Every rule below is written from the user's perspective (state, actions, consequences), not implementation mechanics.

## 1. Why this feature exists

The login page is the front door of the product, and it currently renders darker and flatter than the design system intends: the panels are barely visible against the background, the input fields don't read as fields, and some small text is hard to read. The colors the design system declares are not the colors that render. This feature makes the login page render in the product's true colors — and keeps it that way.

## 2. The actors and their roles

- **Operator / Owner / Admin:** opens the login page and immediately perceives it as the same product as the website and the rest of the console — visible panels, fields that look like fields, readable text.
- **System (FreightPilot console):** renders every surface in the color values the design system declares, across the login page and everywhere the shared surfaces appear.

## 3. The login page renders in the product's declared colors

### 3.1 Panels are visible panels

When the operator opens the login page:

- the page background, the main panels, and the nested panels inside them are each visibly distinct — no near-black stacking where one surface disappears into another;
- panel borders are clearly visible;
- the layout reads as deliberate surfaces on a dark canvas, matching the same visual language as the rest of the console and the product website.

### 3.2 Fields read as fields

- Input fields on the login page are visibly lighter than the panel they sit in, with a clear border and a readable placeholder — the operator can tell at a glance where to type.
- Focused fields show the product's cyan focus treatment.

### 3.3 One color language everywhere

- The same rendered colors apply wherever the shared surfaces appear across the whole console — the login page and the rest of the application must never disagree about what a panel or a field looks like.

## 4. Small text on the login page is readable

- Every text element on the login page — eyebrows, helper copy, secondary actions — is readable against its background (WCAG AA contrast for small text).
- Hierarchy is preserved: labels read as labels, body text as body text, titles as titles — nothing flattens into one gray mass.

## 5. Accent discipline

- The login page uses one cyan accent family for the brand mark, the primary action, links, and focus treatment.
- Rose is used only for error states. No new hues are introduced anywhere on the page.

## 6. Preservation rules

- All existing copy on the login page is preserved verbatim.
- All handlers, authentication flows, page paths, role gates, and test markers are preserved.
- No new external libraries.
- The console keeps its existing visual rules (one accent family, calm surfaces, no decorative gradients or glow).

## 7. Acceptance standard

This feature is complete when:

- an operator opening the login page sees distinct, intentional panels and fields that look like fields, in the same color language as the rest of the product;
- every text element on the login page meets readable contrast;
- the shared surfaces render identically everywhere they appear;
- a regression guard exists so color drift of the shared surfaces cannot silently return;
- the full console test suite, typecheck, and build pass.

---

## Ticket map

| Ticket | Rule |
|---|---|
| NB-60 | §3 The login page renders in the product's declared colors |
| NB-61 | §4 Small text on the login page is readable |
| NB-62 | §7 Acceptance standard — regression guard + full verification |
