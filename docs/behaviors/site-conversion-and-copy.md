# Site Conversion & Copy — Living Behaviors

> ✅ **IMPLEMENTED** — This feature shipped in Phase 5 of the market-contender-v1 batch (TECH-36..47; QA-approved commit `9dc9b49`). Every rule below is written from the user's perspective (state, actions, consequences), not implementation mechanics.

## 1. Why this feature exists

The public website (apps/product-web) currently leans toward a Western-premium B2B SaaS playbook: heavy framer-motion sections, long-scroll narratives, abstract "decision intelligence" framing. This conflicts with two realities that the cashflow and activation legs of this work surfaced:

1. **The actual buyer's connection reality.** Ethiopian mobile data on 3G is slow and metered. A long-scroll page with heavy animations loses visitors before the hero finishes rendering.
2. **The actual product reality.** FreightPilot's strongest promise is the activation flow we locked in: signup seeds sample data, the customer runs their first route optimization in 5 minutes, and the cashflow flow lets them pay by bank transfer to CBE or Dashen with no card ever required. None of those honest levers are currently surfaced in the site copy.

This feature rebuilds the site as an honest conversion funnel. Its single job is to move a visitor from "curious lander" to "clicked Start free and landed in the console with sample data loaded." Everything else — pricing information, partial-payment trust story, brief product explanation — exists to serve that one conversion.

## 2. The actors and their roles

- **Visitor:** an unauthenticated person landing on the site, typically an Ethiopian logistics operator (owner or dispatcher) on a slow mobile connection, evaluating whether FreightPilot is worth trying.
- **System (FreightPilot site):** serves a fast-loading, copy-honest, single-CTA-Conversion home page plus informational supporting routes (pricing, contact, platform, technology). Never asks the visitor for payment, never asks for a tier commitment before signup, never fabricates testimonials or metrics.

## 3. The site's single job

The site has one success metric: **the visitor clicked "Start free" and landed in the ops console with an authenticated session and a sample-data-seeded workspace.**

The site does NOT:
- Sell paid tiers directly (no on-site tier-pick transaction).
- Capture leads for sales-team follow-up (no "Book a demo" funnel).
- Drive desktop downloads as a primary action (the desktop shell is secondary; browser-based trial is primary).
- Promise outcomes that aren't yet verifiable (no fake metrics, no invented testimonials, no "trusted by N operators" claims).

The console sells the upgrade (per the activation behavior doc). The site sells the trial-start.

## 4. The home page hero

### 4.1 The primary headline

> **"Run your first optimized route in 5 minutes. Free."**

This single sentence carries the conversion work. It promises a specific, verifiable outcome (first optimized route), in a specific timeframe (5 minutes, the activation flow's design target), at a specific price (free, the Free-tier-forever signup path).

### 4.2 The hero supporting paragraph

> *Sign up and your workspace loads with sample data — warehouses, fleet, inventory, orders, all ready. Optimize your first route immediately. Upload your real CSVs when you're ready. Pay by bank transfer to CBE or Dashen when you outgrow the free tier. No card, no commitment.*

This paragraph pays off every promise made in the primary headline and names the two banks (CBE, Dashen) the cashflow leg locked in. Each claim is verifiable against a behavior in the cashflow or activation docs:

- "sample data — warehouses, fleet, inventory, orders, all ready" → NB-25 (sample data seeds workspace on signup)
- "Optimize your first route immediately" → NB-28 (milestone 6 reachable on sample data)
- "Upload your real CSVs when you're ready" → NB-28 (milestones 1-5 require real uploads)
- "Pay by bank transfer to CBE or Dashen when you outgrow the free tier" → NB-02 (CBE + Dashen only) + NB-31 (Free hard-locks at cap) + NB-32 (upgrade pitch fires from the console, not the site)
- "No card, no commitment" → §6.1 of cashflow behavior doc (no card-on-file anywhere in v1)

### 4.3 The hero CTA

The hero contains exactly one primary CTA: a button reading **"Start free"** (not "Start free trial" — see §6.2 below for the language rule).

The hero does NOT contain:
- A secondary "See pricing" button (split CTA = split attention; the single CTA is the only path).
- A secondary "Book a demo" or "Contact sales" button (no sales-team motion in v1).
- A "Download desktop" button (desktop is secondary; browser trial is primary).
- Any fabricated urgency ("Limited spots available", "Offer ends soon").

## 5. Home page section structure

The home page has exactly five sections, in order, between the site chrome (nav + footer) and the page boundaries:

1. **Hero** (per §4).
2. **"How it works" expandable section** (per §7). Collapsed by default.
3. **Pricing summary** (per §8). Compact, 3 paid-tier rows + Free-tier line below.
4. **Trust strip** (per §9). One line restating the bank-transfer + no-card + partial-payment story.
5. **Final CTA** (per §10). One button: "Start free."

That's it. No testimonials section. No customer-logo bar. No long-scroll narrative. No animated case-study cards. No "compare us to competitors" table.

The sections are sequential, vertical, and not behind any tab or carousel. The visitor scrolls once from top to bottom and either clicks "Start free" or leaves.

The site's other routes (`/platform`, `/technology`, `/pricing`, `/launch`, `/contact`) remain accessible from the top nav, but nothing on the home page *forces* the visitor to navigate to them. The home page is a complete pitch by itself.

## 6. Copy honesty rules

### 6.1 No unsupported claims

The site copy must not contain:
- Specific numeric outcome claims not verifiable by product behavior (e.g., "Cut dispatch time by 40%", "Save 30% on fuel", "Reduce delays by 80%"). The product team does not yet have the data to support these claims.
- Vague "AI-powered" or "decision intelligence" framing that does not correspond to a specific product behavior the visitor can verify after signup. The existing `services/forecasting.py` and `services/routing.py` produce real outputs the customer sees; copy may reference "demand forecasting" and "route optimization" by name because those are real surfaces. The site must not promise "autonomous dispatch" (the system is human-in-the-loop, per the system-purpose doc).
- Fabricated social proof. No "Trusted by 50+ operators", no invented customer logos, no fake five-star reviews, no fake case-study quotes.

This rule implements the honesty principle from the market-dominator overhaul doc: "Kept copy grounded in existing FreightPilot capabilities instead of publishing unsupported market claims."

### 6.2 Language precision around "trial" and "free"

The signup path is Free-tier-forever, NOT a time-limited free trial. The site copy must not use the phrase "free trial" to describe signup.

- The hero button reads **"Start free"** (Free tier, forever).
- The hero supporting paragraph reads **"Pay by bank transfer to CBE or Dashen when you outgrow the free tier"** (the upgrade path).
- The phrase "trial" is reserved exclusively for the **7-day paid-tier trial** that fires when a Free-tier customer chooses to upgrade to Starter, Scale, or Enterprise (per the cashflow behavior doc §5.2). The site does not surface the trial mechanic prominently because the trial fires inside the console, not on the site.

If a visitor reads only the site and never signs up, they come away understanding: "Free forever, pay by bank transfer later, no card required." That is the honest mental model.

### 6.3 Pricing precision

All pricing copy uses the tier ladder locked in the cashflow behavior doc:
- Starter: 4,500 ETB / month
- Scale: 10,000 ETB / quarter
- Enterprise: 45,000 ETB / quarter
- Free: 0 ETB / forever, capped

The site must not misrepresent any of these (no "Starter 4,500/mo" displayed as "from 4,500" with the cycle hidden; no "Save 20% with annual billing" because no annual billing exists in v1).

## 7. "How it works" expandable section

### 7.1 Default state

The "How it works" section is collapsed by default on home page load. It displays a single visible heading: "How it works in 5 minutes" with a "Show" affordance (chevron, plus icon, or equivalent).

The collapsed state keeps the home page fast to absorb: the visitor reads the hero, sees the "How it works" prompt, and chooses whether to expand it. Visitors who just want the CTA do not have to scroll past a wall of step descriptions.

### 7.2 Expanded state — exactly three steps

When expanded, the section shows exactly three steps. There is no fourth step. No "and then join other operators like you" closing flourish. No fake "trusted by N operators" tagline.

The three steps are:

1. **"Sign up free — your workspace loads with sample data in under a minute."**
2. **"Run your first route optimization on the sample data — see the map, the stops, the schedule."**
3. **"Upload your real CSVs (warehouses, items, fleet, inventory, orders) when you're ready. Pay by bank transfer to CBE or Dashen when you outgrow the free tier."**

### 7.3 No images, no videos, no GIFs in this section

To honor the page weight budget (§11), the three steps are text-only with simple icons (line icons, not photos). No video walkthroughs. No animated GIFs. No product-screenshot carousels.

A prospective customer who wants to see the product in action must sign up and try it. The site does not front-load the product experience; the console does.

## 8. The pricing summary

### 8.1 Layout

The pricing summary is a compact table with 3 rows, one per paid tier (Starter, Scale, Enterprise). The columns are:

| Tier | Flat price | Billing cycle | What's included (≤5 words) |
|---|---|---|---|
| Starter | 4,500 ETB | per month | First lift off Free tier |
| Scale | 10,000 ETB | per quarter | Mid-size dispatch shop |
| Enterprise | 45,000 ETB | per quarter | Unlimited usage, dedicated support |

The "What's included" column is intentionally vague in this v1 — because the codebase does not yet differentiate tiers by features, only by quotas and overage rates. A more detailed differentiation will become possible after the deferred feature-gating work (DEFERRED-05) is done.

Below the table, a single line reads:

> **Free forever — 2,500 delivery tasks / month, no payment ever. Start here.**

### 8.2 No "Most Popular" badge

The pricing summary table must not display a "Most Popular" badge on any tier. The product team has no data on which tier is most popular, and inventing the badge to bias the visitor toward Scale or Enterprise is dishonest.

### 8.3 No "Contact sales" tier

Enterprise is priced at 45,000 ETB / quarter publicly. There is no "Contact sales for Enterprise" CTA on the pricing summary. The price is the price. If a visitor wants Enterprise, they sign up Free first and upgrade inside the console (per the activation flow), or they can use the `/contact` route for a one-off inquiry — but the pricing page does not push them to contact sales.

### 8.4 Partial-payment and wallet-credit story placement

Below the pricing table and the Free-tier line, the partial-payment + wallet-credit story surfaces (from NB-24 in the cashflow ledger). Specifically:

> **Partial payments welcome.** Pay what your cash flow allows — send the receipt for each transfer, and your workspace unlocks when the full balance clears. If you overpay within 1,000 ETB, the surplus applies as credit to your next invoice.

This is the trust strip's content (§9 below) repeated in slightly more detail, anchored to the pricing surface where the visitor is most likely to be thinking about payment mechanics.

## 9. The trust strip

Between the pricing summary and the final CTA, a single line restates the trust story:

> **Bank transfer to CBE or Dashen. No card required. Partial payments welcome. No hidden fees, no annual lock-in.**

The trust strip does not link anywhere. It is a closing reassurance, not a navigation surface. It exists to bridge the pricing information the visitor just absorbed to the final CTA they're about to see.

## 10. The final CTA

The final section of the home page contains exactly one button: **"Start free."**

The button:
- Is large, visually prominent, and on its own line (no companion CTAs).
- On click, navigates the visitor to the company signup flow (the existing signup form on `/launch` per the existing site routing).
- Does not display any secondary CTA (no "See pricing" — pricing was already shown; no "Book a demo" — no sales motion in v1).
- Does not display any urgency / scarcity language ("Limited spots", "Offer ends soon").

## 11. Page weight and load budget

### 11.1 The hard constraint

The home page must finish loading in **under 3 seconds on a 3G connection** (approximated as 400 kbps network, ~1.2 MB total page weight including JavaScript bundles, CSS, fonts, images).

This is the single most important UX constraint on the site. A visitor on 3G who waits 5+ seconds for the hero to render will leave. Conversion optimization starts with load time, not with copy.

### 11.2 What "page weight" includes

The 1.2 MB budget includes:
- HTML document
- All CSS
- All JavaScript (including framer-motion, react, next.js runtime)
- All web fonts (Inter and Space Grotesk only — no additional font families)
- All images, icons, and any media

### 11.3 Hard rules to hit the weight budget

To hit the budget, the implementation must:
- **No video assets** on the home page or anywhere surfaced from the home page.
- **No hero background images larger than 100 KB.** The hero should be CSS-driven (gradients, the existing layered background from the market-dominator work) rather than image-driven.
- **Framer-motion usage is limited to one entrance animation on the hero.** No scroll-triggered motion sections. No staggered card entrance animations on the pricing table. No animated counters on the home page (the existing `animated-counter.tsx` component may be used on `/platform` or `/technology` but not on `/`).
- **No additional web font families** beyond Inter and Space Grotesk already in the codebase.
- **No third-party analytics scripts** loaded synchronously on the home page (analytics must load with `defer` or be wired through next/script with `strategy="lazyOnload"`).
- **The expanded "How it works" section contains no images.** Per §7.3, it is text + line icons only.

### 11.4 TheChrome (nav + footer) is included in the budget

The sticky glass nav and the footer sections (from `site-chrome.tsx`) are part of the home page's total weight. They must be reviewed and slimmed if they push the home page over budget. The product-web's existing `site-content.ts` may surface nav configuration that pulls in additional assets — audit before launch.

## 12. The other site routes

This behavior doc focuses on the home page because it is the conversion surface. The other routes (`/platform`, `/technology`, `/pricing`, `/launch`, `/contact`) remain accessible from the top nav and must continue to render correctly against their existing component wiring. But they are not the primary conversion surface.

Three rules apply to all routes, not just the home page:

1. **Page weight budget applies site-wide.** Every route must load in under 3 seconds on 3G. Routes that exceed this must be reviewed and slimmed.
2. **Honesty rules apply site-wide.** No unsupported numeric claims, no fake testimonials, no fabricated social proof, no "free trial" language for the Free-tier-forever signup path.
3. **Single CTA per page, with the CTA being "Start free."** No Routte has multiple CTAs competing for the visitor's attention. Pricing detail belongs on `/pricing`; contact intake belongs on `/contact`; but every route funnels to "Start free" as the primary action.

### 12.1 The /pricing route

`/pricing` is the full-display pricing page. It expands on the home page's pricing summary by including:
- Full tier details (quotas, overage rates, billing cycle) for each paid tier.
- The full partial-payment + wallet-credit + verification-within-24h trust story.
- Any tier-specific FAQ entries (per NB-24).

The CTA on `/pricing` is the same as the home page: **"Start free."** Not "Choose Starter." Not "Choose Scale." Not "Contact sales."

### 12.2 The /launch route

`/launch` is the existing company-signup form surface. This is where the "Start free" CTA navigates to. The signup form must:
- Accept business email + password + company name + optional tier preference (the existing signup-form component per the codebase).
- Reject public email domains (per existing `blocked_public_email_domains` in backend config).
- On submit, fire the company-signup API call that provisions the workspace with sample data seeding (per NB-25 activation behavior).
- On success, redirect to the ops console (`https://ops-console-azure.vercel.app` or local equivalent per the existing env config).

The signup form does NOT ask for payment at signup. Payment enters the customer's experience only after they upgrade inside the console (per the cashflow behavior).

### 12.3 The /contact route

`/contact` is the existing contact form. It remains available for visitors who want to send a message. It is not a primary CTA surface — the contact link lives in the footer, not in the home page's body CTAs.

The contact form must not become a hidden "lead capture for sales follow-up" funnel. Visitors who fill it out are acknowledged but not entered into an automated sales drip. Any follow-up is manual and human.

## 13. What this feature does NOT do

To preserve scope:

- **No on-site tier-selection transaction.** Visitors do not pick a tier on the site. They pick a tier inside the console after signup (per Question 2 lock-in of the Site leg).
- **No sales-team motion.** No "Book a demo" CTA, no automated sales drip, no CRM integration for site form submissions. v1 is a self-serve product-led funnel.
- **No desktop-download as primary CTA.** The desktop shell remains available via its existing download center URL (`NEXT_PUBLIC_DESKTOP_DOWNLOAD_URL` per the env config), but the home page does not feature it as a primary action. Browser-based trial is the v1 funnel.
- **No A/B testing framework shipped with v1.** The site will be instrumented for basic analytics (pageview + "Start free" click) but no experiment framework is shipped. The locked copy is the v1 launch copy.
- **No localization (Amharic) in v1.** The site renders in English only. Amharic localization is a separate work item and not yet scoped.

## 14. Open verification items flagged before launch

These open items are tracked in `docs/behaviors/pending-behaviors.md` and must be cleared before this feature launches to production:

- An audit of the existing `site-chrome.tsx`, `site-content.ts`, `hero-scene.tsx`, `motion-section.tsx`, and `animated-counter.tsx` components must confirm that no current asset or motion pattern violates the page weight budget (§11). Components that violate the budget must be slimmed or removed from the home page render path specifically.
- The pricing summary table's "What's included" column is intentionally vague in v1 (§8.1). When the deferred feature-gating work item (DEFERRED-05) lands, the column copy must be updated to reflect actual tier-level feature differences.
- The copy in §4.1, §4.2, §7.2, §8.1, §8.4, and §9 is_locked-in_product copy direction, not final-shipped marketing language. A copy-review pass before launch must confirm the tone is consistent across the home page and the supporting routes.
