# Tech Backlog — Execution Tickets

> This file translates the locked behavioral requirements (`docs/behaviors/*.md` + `docs/behaviors/pending-behaviors.md`) into uniquely identified technical execution tickets (`TECH-XX`). Each ticket maps 1:1 to its parent `NB-XX` behavioral ticket and inherits its acceptance criteria.
>
> Execution protocol:
> - A SINGLE feature branch hosts the entire batch. Branch name: `feat/market-contender-v1` (created by @build).
> - Each phase below is a vertical slice: @plan writes the blueprint to `docs/plans/`, @build executes TDD, @qa audits, @build commits atomically on QA APPROVED.
> - The ledger is debited (tickets removed here, `[IMPLEMENTED]` appended to NB parents, warning banners stripped) by @architect only after QA sign-off per phase.

## Phase 1 — Cashflow Core: Invoicing, Trials, Limbo, Grace & Locks (P0)

Source: `docs/behaviors/cashflow-bank-transfer-receipt-verification.md`

| TECH | Parent NB | Ticket summary |
|---|---|---|
| TECH-01 | NB-01 | Tier pricing locked: Starter 4,500/mo, Scale 10,000/qtr, Enterprise 45,000/qtr in plan catalog + invoice line items; Enterprise never shows overage; Free never invoices. |
| TECH-02 | NB-02 | Two collection accounts (CBE + Dashen) in single config surface; each invoice designates exactly one; account locked at issuance. |
| TECH-03 | NB-03 | 7-day (168h) trial on first paid-tier upgrade; full RW access; no invoice during trial; re-trials of same tier silently blocked. |
| TECH-04 | NB-04 | Read-only limbo between trial end and next billing-period start; banner with due date; write ops disabled. |
| TECH-05 | NB-05 | 3-day warning notification on every invoice at issuance (in-product only): invoice number, flat amount, designated bank, due date. |
| TECH-06 | NB-06 | Grace windows: 3 days on first invoice ever, 0 days on subsequent; grace banner; hard lock with write-disabled state; only payment clears. |

## Phase 2 — Receipt Processing: Upload, AI Extraction, Matching & Verification Queue (P0)

Source: `docs/behaviors/cashflow-bank-transfer-receipt-verification.md`

| TECH | Parent NB | Ticket summary |
|---|---|---|
| TECH-07 | NB-07 | Receipt upload surface (PNG/JPG/PDF only); auto-routing to oldest open invoice; surplus cascades to next invoices; "≤24h" confirmation. |
| TECH-08 | NB-08 | Partial payments: credit as received, balance carried forward, multiple receipts per invoice, unlock only at zero balance, amount never rejects. |
| TECH-09 | NB-09 | ±1,000 ETB auto-forward tolerance → wallet credit on next invoice; surplus >1,000 ETB flagged for admin 3-way decision; never auto-reject on amount. |
| TECH-10 | NB-10 | AI-assisted extraction via org-preferred BYOK key; 8 fields + per-field confidence; zero-confidence warning when no key; low-confidence visual flags. |
| TECH-11 | NB-11 | Per-org trusted-payer list, admin-only; "NEW SENDER" flag; verify+add / verify-once / reject decisions. |
| TECH-12 | NB-12 | "CASH" sender always double-flagged with "Cash deposit — confirm" note, even if previously approved. |
| TECH-13 | NB-13 | Wrong-bank-within-portfolio (CBE↔Dashen) auto-flows with pre-filled Verify; wrong-bank rejection reserved for out-of-portfolio only. |
| TECH-14 | NB-14 | Hard reject on duplicate reference number across the entire system; fraud-flag pair in audit trail. |
| TECH-15 | NB-15 | Exact verdict enum: Verify / Reject-wrong-bank / Reject-duplicate / Reject-illegible / Escalate; no amount-mismatch verdict; rejections → in-product banner + re-upload, no SMS. |
| TECH-16 | NB-16 | Escalation = only SMS-triggering state; ≤160-char SMS to registered phone; banner with escalation question; workspace stays locked. |
| TECH-17 | NB-17 | Dispute path: rejection banner has Re-upload + Dispute textbox; dispute converts to escalation case; read-only until resolved. |

## Phase 3 — Cashflow: Audit Trail, Reversibility & Fraud Controls (P0/P1)

Source: `docs/behaviors/cashflow-bank-transfer-receipt-verification.md`

| TECH | Parent NB | Ticket summary |
|---|---|---|
| TECH-18 | NB-18 | Immutable audit record per verification action with full field set; reversals create new records, never mutate originals. |
| TECH-19 | NB-19 | Silent Undo within 24h: reverses credit, restores balance, re-locks; no customer notice; Undo hidden after 24h. |
| TECH-20 | NB-20 | Reverse with notice after 24h: mandatory reason note; auto-message to customer; creates distinct audit record; no automatic refund. |
| TECH-21 | NB-21 | Fraud-risk sender badge on trusted-payer list when reversal targets a previously-added sender; badge persists; never auto-hard-blocks. |
| TECH-22 | NB-22 | **HUMAN GAP — NOT CODE.** Verify CBE + Dashen published fee schedules (5,000–50,000 ETB range) and confirm the ±1,000 ETB tolerance before production launch. Requires user action; do not build. |

## Phase 4 — Activation: Sample Seeding, Milestones, Progressive Reveal & Free-Cap Lock (P0/P1)

Source: `docs/behaviors/operator-activation-and-milestone-tracking.md`

| TECH | Parent NB | Ticket summary |
|---|---|---|
| TECH-25 | NB-25 | New workspace auto-seeded from `sample-data/` CSVs on signup; all ops runnable on seed; per-workspace; audit event `workspace.seeded_sample_data`. |
| TECH-26 | NB-26 | Persistent non-dismissible "demo workspace" banner; N-of-5 progress text; disappears only at milestone 5; CTA to `/upload`. |
| TECH-27 | NB-27 | Sample-data operations consume meters identically to real; `data_origin` ("sample"/"real") on route audit events; metering never differentiates. |
| TECH-28 | NB-28 | Six-milestone activation state per organization; milestones 1-5 require ≥1 real row; milestone 6 reachable on sample data. |
| TECH-29 | NB-29 | Progressive dashboard panel reveal by milestone; always-visible surfaces (banner, exception feed, audit timeline, feedback); hidden-or-placeholder mode support. |
| TECH-30 | NB-30 | Activation banner on both `/dashboard` (compact) and `/upload` (full checklist) from shared state; live updates without reload. |
| TECH-31 | NB-31 | Free tier hard-lock at 2,500 delivery_tasks OR 50 route_optimizations; exact disabled/available operation lists; no Free overage; banner on every page; auto-lift at month rollover. |
| TECH-32 | NB-32 | Escalating upgrade pitch at 60% (dismissible, no CTA) / 80% (persistent, "See pricing" → in-product `/account`) / 100% (hard-lock banner, "Upgrade now"); never leaves console; fires once per threshold per month. |
| TECH-33 | NB-33 | Soft post-aha toast at milestone 6, exactly once per org; informational only; auto-dismisses. |
| TECH-34 | NB-34 | Returning users always land on `/dashboard`; banner text varies by activation state (0 of 5 / N of 5 / 5 of 5 pre-optimization / none). |
| TECH-35 | NB-35 | Admin-gated workspace reset with typed workspace-name confirmation; wipes real uploads, re-seeds sample, resets milestones, audit event, re-login flow. |

## Phase 5 — Site Conversion: Hero, Sections, Pricing, Weight Budget & Honesty Rules (P0/P1)

Source: `docs/behaviors/site-conversion-and-copy.md` (+ folds in NB-23/NB-24 site-copy tickets)

| TECH | Parent NB | Ticket summary |
|---|---|---|
| TECH-36 | NB-36 | Home hero: exact headline + supporting paragraph + single "Start free" CTA → `/launch`; no secondary CTAs, no urgency. |
| TECH-37 | NB-37 | Home page exactly five sections in order; no testimonials/logos/case-studies/compare tables. |
| TECH-38 | NB-38 | "How it works" collapsed by default; exactly 3 text-only steps; expand/collapse affordance. |
| TECH-39 | NB-39 | Pricing summary: 3 paid-tier rows + Free line; no Most Popular badge; no Contact sales; partial-payment + wallet-credit story verbatim. |
| TECH-40 | NB-40 | Trust strip line between pricing and final CTA; text-only, no links; wraps ≤3 lines mobile. |
| TECH-41 | NB-41 | Final CTA: single large "Start free" button, no companions. |
| TECH-42 | NB-42 | Page weight budget: <1.2 MB total, <3s on 3G; no video; CSS hero ≤100 KB image; framer-motion limited to one hero entrance; Inter + Space Grotesk only; analytics deferred. |
| TECH-43 | NB-43 | No fabricated social proof anywhere (no "Trusted by N", no fake logos/reviews/case studies, no invented comparison table). |
| TECH-44 | NB-44 | No "free trial" language for signup path; "trial" only in paid-tier-trial contexts on `/pricing` FAQ; signup form honest. |
| TECH-45 | NB-45 | Audit existing `apps/product-web/src/components/site/` components against weight budget; document OK/Slimmed/Removed checklist in PR; `animated-counter.tsx` excluded from home page. |
| TECH-46 | NB-46 | All site routes pass weight + honesty + single-CTA rules; `/pricing` full details + trust story; `/launch` signup wiring incl. sample seeding trigger; `/contact` not a lead-capture funnel. |
| TECH-47 | NB-47 | Scope lock: English-only v1; simple clear English copy. |

## Deferred (explicitly NOT in this batch)

DEFERRED-01..DEFERRED-09 in `pending-behaviors.md` (refunds, third bank, intermediaries, USD, feature-gating, email drip, Amharic, A/B testing, desktop-primary-CTA) are out of scope for this batch.

## Acceptance gate

A phase is complete only when:
1. `@plan` blueprint exists in `docs/plans/` for the phase.
2. `@build` implemented TDD on `feat/market-contender-v1` and all tests pass.
3. `@qa` returns APPROVED against the blueprint AND the NB acceptance criteria.
4. Atomic commit executed on the feature branch.
5. Ledger debited: TECH tickets removed from this file, `[IMPLEMENTED]` appended to NB parents, warning banner stripped from the behavior doc (when its feature is fully shipped).
