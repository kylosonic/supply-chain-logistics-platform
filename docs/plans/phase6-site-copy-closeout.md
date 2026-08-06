# BLUEPRINT: PHASE 6 — Site Copy Closeout (TECH-50 / NB-23.5)

Status: LOCKED for execution by @build on a new feature branch `feat/tech-50-site-copy-closeout` cut from `master` (`5d014a1`, working tree clean). Written by @plan. QA audits against THIS document AND the NB-23/NB-24 acceptance criteria in `docs/behaviors/pending-behaviors.md` (NB-23 lines 224–232, NB-24 lines 234–240) AND the phase-5 locked-copy conventions in `docs/plans/phase5-site-conversion.md` §1.1, §5, §8, §9. This is the FINAL closeout slice of the market-contender-v1 batch: 45/47 behaviors shipped; the single remaining gap is NB-23.5. One-line text slice — `apps/product-web` only, zero backend changes. *Note: the graphify CLI is not installed in this environment (verified); the placement decision below was grounded by direct reads of `site-content.ts`, `pricing/page.tsx`, `pricing.phase5.test.tsx`, and `pending-behaviors.md`.*

## 0. Goal

Close NB-23.5 by rendering the read-only-limbo sales story — **[EXACT]** "Pay at your bank's pace — your first invoice isn't due until the start of the next billing period." — in the `/pricing` payment trust section, with zero other copy changes, and prove via tests that NB-23.3 substance, NB-24, NB-44, and NB-46 remain satisfied.

## 1. Ground-truth decisions (locked for @build; deviations require @architect sign-off)

1. **Copy lock:** the NB-23.5 line is **[EXACT]** — it is quoted verbatim in `pending-behaviors.md` line 232 and is the sole missing criterion, so no paraphrase latitude. Subject only to HTML entity encoding for the apostrophes ("bank's", "isn't" → `&#x27;` in SSR output) — tests assert the decoded text (phase-5 convention §1.1). The string contains no "trial" and no "free trial" substring — NB-44 safe by construction.
2. **Placement:** `/pricing` payment trust section ONLY (the `SpotlightCard` block in `src/app/pricing/page.tsx`, lines 118–128). Adjudication vs. the home page: NB-23.5's criterion does not name a page, but NB-23 criterion 1 targets the pricing page, NB-24.1/2 already live on `/pricing`, and the home page carries the NB-42-sensitive 1.2 MB / 3s budget with a lean locked hero — adding the line there is not required and not free. **Home page: NOT touched.**
3. **Ordering within the section:** the new line renders as a third paragraph in the payment trust card — after the `partialPaymentStory` paragraph, before the `verificationLine` paragraph. Narrative flow: welcome story → payment-pace (limbo) story → verification anchor. Reuse the existing paragraph styling class `text-sm leading-8 text-white/72` with `mt-4` (the story paragraph above it already carries `mt-8`).
4. **Export naming/location:** new export `paymentPaceStory` in `src/lib/site-content.ts`, placed immediately after `partialPaymentStory` (line 106) and before `trustStripLine` — keeps the three payment-story exports adjacent. Existing exports `partialPaymentStory`, `verificationLine`, `faqItems` are NOT modified (byte-identity regression is tested).
5. **Test file:** NEW `src/app/pricing.phase6.test.tsx` rather than extending `pricing.phase5.test.tsx`. Rationale: the phase-5 file was QA-audited and merged at `5d014a1`; mutating a merged audit artifact muddies the trail, and phase 6 is its own audit unit (same page, new criterion). The phase-5 file's existing assertions double as the regression net and must remain green untouched — the new line adds no "trial" occurrence and no CTA, so they will.
6. **Weight budget:** the added line is ~125 bytes of text on `/pricing`, which has its own 1.2 MB raw-byte budget via `check-bundle-budget.mjs` — negligible, no bundle change expected (same chunks; no new imports beyond one string export). NB-42 unaffected.

## 2. Files to MODIFY (all under `apps/product-web/`)

1. `src/lib/site-content.ts` — ADD one export after `partialPaymentStory` (line 106):
   - `paymentPaceStory` **[EXACT]** = `Pay at your bank's pace — your first invoice isn't due until the start of the next billing period.`
   - Single-quoted string with escaped apostrophes, matching module convention (e.g. `you\'re`). DO NOT touch `partialPaymentStory` (lines 105–106), `verificationLine` (line 111), or the FAQ block (lines 140–166).
2. `src/app/pricing/page.tsx` — ADD `paymentPaceStory` to the existing `@/lib/site-content` import (lines 9–15); render one new `<p className="mt-4 text-sm leading-8 text-white/72">{paymentPaceStory}</p>` between the `partialPaymentStory` paragraph (line 125) and the `verificationLine` paragraph (line 126). No other changes — metadata, hero, tier cards, FAQ, and JSON-LD all stay byte-identical.

## 3. Files to CREATE

1. `src/app/pricing.phase6.test.tsx` (~70 lines, SSR `renderToString`, node test env like `pricing.phase5.test.tsx`) — imports `PricingPage` from `./pricing/page` and `{ partialPaymentStory, paymentPaceStory, faqItems }` from `@/lib/site-content`; copies the `count` and `decodeHtml` helpers from `pricing.phase5.test.tsx` (they are tiny; do not import from the phase-5 test file). Test map in §5.

## 4. Strict Import Map

- `src/lib/site-content.ts` → (unchanged deps: `lucide-react` icon types only) — leaf data module; new export adds no imports.
- `src/app/pricing/page.tsx` → `@/lib/site-content` already imported; the named-import list gains `paymentPaceStory`. All other imports (`next`, `lucide-react`, `@/components/site/*`) unchanged.
- `src/app/pricing.phase6.test.tsx` → `react`, `react-dom/server` (`renderToString`), `vitest`, `./pricing/page` (default `PricingPage`), `@/lib/site-content` (three named exports).
- No cross-app imports; no new dependencies; no `src/test/setup.ts` need (SSR render only, same as phase-5 pricing test).

## 5. Step-by-step execution (for @build)

1. Create branch `feat/tech-50-site-copy-closeout` from `master` (`5d014a1`). Run the existing `product-web` test suite — green baseline.
2. Add the `paymentPaceStory` export to `src/lib/site-content.ts` (§2.1). Verify `partialPaymentStory`/`verificationLine`/`faqItems` are untouched (git diff must show one added export only).
3. Create `src/app/pricing.phase6.test.tsx` with the four tests in §5a–d (write BEFORE wiring the page, so test (a) fails — TDD).
4. Wire the paragraph into `src/app/pricing/page.tsx` (§2.2). Run the full `product-web` suite — all phase-5 pricing tests AND the new phase-6 tests green.
5. Run `npm run build` + `npm run check:bundle` and confirm the `/pricing` route total is unchanged or trivially higher (well under 1.2 MB) — record the number in the PR description as the NB-42 evidence.

## 5a. Test map (`pricing.phase6.test.tsx`, one `describe` block "pricing page phase 6 (NB-23.5, NB-24, NB-44, NB-46)")

- **(a) NB-23.5 line renders:** after `decodeHtml(renderToString(<PricingPage />))`, `html.toContain(paymentPaceStory)` — asserts the exact locked line, byte-identical.
- **(b) "trial" still ONLY in the FAQ block (NB-23.3 + NB-44):** strip the JSON-LD `<script>` (same pattern as phase-5 test line 88); `count(withoutJsonLd, 'trial')` = 2, both inside the locked trial FAQ Q/A; and `count(withoutJsonLd, 'free trial')` = 1 (only the locked FAQ question "Do you offer a free trial?" — the new line introduces zero new occurrences). FAQ answer still contains "the first 7 days on that tier are a trial at no charge".
- **(c) NB-24 partial-payment story byte-identical regression:** `html.toContain(partialPaymentStory)` (asserted against the imported export — guards against any edit to that string); also `html.toContain(verificationLine)`.
- **(d) NB-46 single-CTA regression:** `count(html, '>Start free<')` = 4 (hero + 3 tier cards) and `count(html, 'href="/launch"')` = 4 — unchanged from phase 5; the new paragraph contributes zero CTAs.

## 6. Explicit NON-GOALS (locked)

No new routes, no new pages. No copy changes anywhere except the single added line on `/pricing` — specifically NOT the home page, `/launch`, `/platform`, `/technology`, `/contact`, metadata, or JSON-LD. No changes to `partialPaymentStory`, `verificationLine`, `trustStripLine`, or any `faqItems` entry. No literal "free trial" / new "trial" occurrences (NB-44). No platform-api changes, no ops-console changes, no migrations, no new dependencies, no new components, no new icons. No weight-budget impact beyond the ~125-byte text line (no new JS chunks expected). No changes to phase-5 test files — they stay exactly as merged.

## 7. QA-audit-against note

@qa verifies TECH-50 against THIS document AND `docs/behaviors/pending-behaviors.md` NB-23 (lines 224–232) + NB-24 (lines 234–240), specifically: **NB-23.5** (line renders on `/pricing`, verbatim), **NB-23.3** (trial substance intact: 7-day + no payment during trial + no card on file — FAQ + "No card required" lines unchanged), **NB-24** (partial-payment + wallet-credit story byte-identical, no over-promising), **NB-44** (no new "trial"/"free trial" occurrences), **NB-46** (single CTA posture unchanged: exactly the four locked "Start free" labels → `/launch`), **NB-47** (line is simple English), and **NB-42** (`check:bundle` /pricing total recorded, under 1.2 MB). PR description must include: (a) the locked line verbatim, (b) git diff confirmation that only `site-content.ts` (one added export) + `pricing/page.tsx` (import + one `<p>`) changed, (c) `check:bundle` /pricing total, (d) full test suite output.
