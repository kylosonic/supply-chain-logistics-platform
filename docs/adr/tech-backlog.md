# Tech Backlog — Execution Tickets

> This file translates the locked behavioral requirements (`docs/behaviors/*.md` + `docs/behaviors/pending-behaviors.md`) into uniquely identified technical execution tickets (`TECH-XX`). Each ticket maps 1:1 to its parent `NB-XX` behavioral ticket and inherits its acceptance criteria.
>
> Execution protocol:
> - A SINGLE feature branch hosts the entire batch. Branch name: `feat/market-contender-v1` (created by @build).
> - Each phase below is a vertical slice: @plan writes the blueprint to `docs/plans/`, @build executes TDD, @qa audits, @build commits atomically on QA APPROVED.
> - The ledger is debited (tickets removed here, `[IMPLEMENTED]` appended to NB parents, warning banners stripped) by @architect only after QA sign-off per phase.

## Phase 1 — Cashflow Core: Invoicing, Trials, Limbo, Grace & Locks (P0) — ✅ COMPLETE

**Status:** Committed `6715f88` on `feat/market-contender-v1`. QA APPROVED. Ledger debited 2026-08-05.

Source: `docs/behaviors/cashflow-bank-transfer-receipt-verification.md`

| TECH | Parent NB | Ticket summary |
|---|---|---|
| ~~TECH-01~~ | NB-01 | ✅ IMPLEMENTED — Tier pricing locked: Starter 4,500/mo, Scale 10,000/qtr, Enterprise 45,000/qtr in plan catalog + invoice line items; Enterprise never shows overage; Free never invoices. |
| ~~TECH-02~~ | NB-02 | ✅ IMPLEMENTED — Two collection accounts (CBE + Dashen) in single config surface; each invoice designates exactly one; account locked at issuance. |
| ~~TECH-03~~ | NB-03 | ✅ IMPLEMENTED — 7-day (168h) trial on first paid-tier upgrade; full RW access; no invoice during trial; re-trials of same tier silently blocked. |
| ~~TECH-04~~ | NB-04 | ✅ IMPLEMENTED — Read-only limbo between trial end and next billing-period start; banner with due date; write ops disabled. |
| ~~TECH-05~~ | NB-05 | ✅ IMPLEMENTED — 3-day warning notification on every invoice at issuance (in-product only): invoice number, flat amount, designated bank, due date. |
| ~~TECH-06~~ | NB-06 | ✅ IMPLEMENTED — Grace windows: 3 days on first invoice ever, 0 days on subsequent; grace banner; hard lock with write-disabled state; only payment clears. |

**Adjudication note:** NB-06 grace write policy — acceptance criteria (write-disabled grace, "Grace period: X days remaining" banner) wins over behavior doc §5.6 wording. Toggle `GRACE_WRITES_ENABLED` in `app/services/billing/locks.py` flips behavior with one line if revisited.

## Phase 2 — Receipt Processing: Upload, AI Extraction, Matching & Verification Queue (P0) — ✅ COMPLETE

**Status:** Committed `179eeda` on `feat/market-contender-v1`. QA APPROVED. Ledger debited 2026-08-05.

Source: `docs/behaviors/cashflow-bank-transfer-receipt-verification.md`

| TECH | Parent NB | Ticket summary |
|---|---|---|
| ~~TECH-07~~ | NB-07 | ✅ IMPLEMENTED — Receipt upload surface (PNG/JPG/PDF only, "Unsupported file format" rejection); auto-routing to oldest open invoice; surplus cascades to next-open; "≤24h" confirmation; unrouteable uploads never pollute the queue (rollback → 400). |
| ~~TECH-08~~ | NB-08 | ✅ IMPLEMENTED — Partial payments credit as received, balance carried forward, multiple receipts per invoice, unlock only at zero balance (pessimistic, on admin Verify), amount never rejects. |
| ~~TECH-09~~ | NB-09 | ✅ IMPLEMENTED — ±1,000 ETB auto-forward tolerance → wallet credit (FIFO, reduces next invoice total via negative `wallet_credit` line item); surplus >1,000 ETB → 3-way admin decision (credit_forward / credit_backward / partial_ignore); never auto-reject on amount. |
| ~~TECH-10~~ | NB-10 | ✅ IMPLEMENTED — Extraction via org-preferred BYOK key; 8 fields + per-field confidence; zero-confidence fallback with admin warning when no key; low-confidence (<60%) visual flags; mock adapter in Phase 2 (provider-agnostic registry, real HTTP adapters are a later phase). |
| ~~TECH-11~~ | NB-11 | ✅ IMPLEMENTED — Per-org trusted-payer list, admin-only, no customer surface; "NEW SENDER" flag; verify+add / verify-once / reject decisions with distinct persistence. |
| ~~TECH-12~~ | NB-12 | ✅ IMPLEMENTED — "CASH" sender always double-flagged with "Cash deposit — confirm" note; pre-fill suppressed even when trusted. |
| ~~TECH-13~~ | NB-13 | ✅ IMPLEMENTED — Wrong-bank-within-portfolio (CBE↔Dashen) auto-flows with pre-filled Verify; `reject_wrong_bank` 422-guarded for in-portfolio banks. |
| ~~TECH-14~~ | NB-14 | ✅ IMPLEMENTED — System-wide dedup on reference number against verified receipts: hard reject at upload + partial unique index backstop (IntegrityError → 409); fraud-flag audit pair; NB-14.3 rejection banner. |
| ~~TECH-15~~ | NB-15 | ✅ IMPLEMENTED — Exact 5-verdict enum (Verify / reject_wrong_bank / reject_duplicate / reject_illegible / Escalate); no amount-mismatch verdict; rejections → in-product banner + re-upload, no SMS. |
| ~~TECH-16~~ | NB-16 | ✅ IMPLEMENTED — Escalation = only SMS-triggering state; exact ≤160-char template; outbox-only (`sms_messages` queue, provider-agnostic, fail-soft `no_phone_on_file`); banner with admin's escalation question; workspace stays locked. |
| ~~TECH-17~~ | NB-17 | ✅ IMPLEMENTED — Dispute path: rejection banner has Re-upload + Dispute textbox; dispute converts rejection → escalation case ("Customer disputes rejection" label); read-only until resolution; one thread per receipt. |

**Adjudication notes:** (1) `contact_phone` added to `organizations` (nullable) with no capture UI yet — escalation SMS degrades to `failed/no_phone_on_file` until a phone field ships (candidate Phase 3 work). (2) Extraction is wired with key plumbing + zero-confidence fallback; only the deterministic mock adapter ships (real HTTP adapters later). (3) `services/billing/receipts/` package split per QA blocker: intake.py (309), queue.py (125), verdicts.py (237), disputes.py (121), `__init__.py` (55).

## Phase 3 — Cashflow: Audit Trail, Reversibility & Fraud Controls (P0/P1) — ✅ COMPLETE

**Status:** Committed `fd5b69c` on `feat/market-contender-v1`. QA APPROVED. Ledger debited 2026-08-05. The cashflow feature is now FULLY SHIPPED (Phases 1–3); the `⚠️ NOT YET IMPLEMENTED` banner is stripped from the behavior doc.

Source: `docs/behaviors/cashflow-bank-transfer-receipt-verification.md`

| TECH | Parent NB | Ticket summary |
|---|---|---|
| ~~TECH-18~~ | NB-18 | ✅ IMPLEMENTED — Every verification action writes exactly one immutable audit record with the full field set (Addis-time rendering, admin user, invoice no., ref no., sender, amount, balance-before, decision, credit delta, mandatory note on escalations/one-offs). Reversals create new records; original records are structurally never mutated (insert-only audit writer). |
| ~~TECH-19~~ | NB-19 | ✅ IMPLEMENTED — Silent Undo within 24h (server-enforced, exactly-24h boundary eligible): credit reversed, balance restored, invoice re-opened, workspace re-locked via lifecycle refresh; zero customer notifications; Undo hidden past 24h and 409-guarded server-side. |
| ~~TECH-20~~ | NB-20 | ✅ IMPLEMENTED — Reverse after 24h: mandatory non-blank reason (422); exact NB-20.3 auto-message as in-product Notification (kind `receipt_reversed`, expires +3d, NO SMS); distinct audit record; balance + lock adjusted only — no automatic refund (DEFERRED-01). |
| ~~TECH-21~~ | NB-21 | ✅ IMPLEMENTED — Fraud-risk badge in new `sender_fraud_flags` table (per-org, normalized sender, UNIQUE); fires on undo AND reverse when the verified audit payload shows `trusted_payer_action='added'`; surfaces on EVERY future queue item for that sender; persists indefinitely incl. after trusted-payer list removal; display-only, never hard-blocks; admin retains verify/escalate/remove discretion. |
| TECH-22 | NB-22 | ⏳ **HUMAN GAP — OPEN, BLOCKS PRODUCTION LAUNCH ONLY.** Verify CBE + Dashen published fee schedules (5,000–50,000 ETB range) against the ±1,000 ETB tolerance before production; document findings in `cashflow-bank-transfer-receipt-verification.md` §12. Procedure in `docs/plans/phase3-audit-reversibility.md` §12. No code required. |

**Adjudication notes:** (1) Reversed receipts stay `status='verified'` — reversal state lives on `reversal_status`/`reversed_at` columns so the NB-14 partial-unique dedup invariant is never weakened. (2) Wallet interplay is asymmetric by design: `available` wallet rows for the reversed receipt are voided (new `'voided'` status); `applied` rows are never clawed back (NB-20.5 limits system effects to balance + lock). (3) Migration `20260806_0015` branches by dialect (sqlite skips CHECK/FK DDL — SQLAlchemy batch mode emits malformed SQL; models authoritative via `create_all`; Postgres has full DDL). (4) Cross-org admin isolation NOT enforced (inherited Phase 2 pattern; flag for @architect if ever wanted).

## Phase 4 — Activation: Sample Seeding, Milestones, Progressive Reveal & Free-Cap Lock (P0/P1) — ✅ COMPLETE

**Status:** Committed `138d38e` on `feat/market-contender-v1`. QA APPROVED (after one FAIL round — banner checklist copy + placeholder CTAs + reset-flow coverage fixed). Ledger debited 2026-08-05. The activation feature is now FULLY SHIPPED; the `⚠️ NOT YET IMPLEMENTED` banner is stripped from `operator-activation-and-milestone-tracking.md`.

Source: `docs/behaviors/operator-activation-and-milestone-tracking.md`

| TECH | Parent NB | Ticket summary |
|---|---|---|
| ~~TECH-25~~ | NB-25 | ✅ IMPLEMENTED — Per-workspace seeding from `sample-data/` CSVs at company-signup (idempotent, FK-ordered, `data_origin='sample'`); audit `workspace.seeded_sample_data`. |
| ~~TECH-26~~ | NB-26 | ✅ IMPLEMENTED — Persistent non-dismissible demo banner, one component/state source, compact (`/dashboard`) + checklist (`/upload`) densities; N-of-5 copy; disappears at 5-of-5 per decision #8 matrix (demo messaging ends, onboarding banner persists until m6). |
| ~~TECH-27~~ | NB-27 | ✅ IMPLEMENTED — Metering never differentiates (`services/metering.py` untouched); `route.optimized` audit gains `data_origin` ("sample" if any touched warehouse is sample, else "real"); uploads audit `workspace.csv_uploaded`. |
| ~~TECH-28~~ | NB-28 | ✅ IMPLEMENTED — Six-milestone state: milestones 1–5 DERIVED (≥1 real row per category, sequential prefix), m6 stored (`m6_completed_at`); first optimization on ANY substrate completes m6 (no prefix requirement); out-of-order uploads don't register. |
| ~~TECH-29~~ | NB-29 | ✅ IMPLEMENTED — Progressive panel reveal by milestone with hidden-or-placeholder modes; gated panels get prerequisite text + "Continue onboarding" CTA; always-visible surfaces (banner, exception feed, audit timeline, feedback) never hidden. |
| ~~TECH-30~~ | NB-30 | ✅ IMPLEMENTED — Shared activation state via `GET /activation`; `/dashboard` compact + `/upload` full checklist; live updates without reload (query invalidation). |
| ~~TECH-31~~ | NB-31 | ✅ IMPLEMENTED — Free-cap lock composes INSIDE `require_writable_workspace` (zero endpoint edits); 2,500 delivery_tasks OR 50 route_optimizations from `pricing.included_units`; exact disabled/available op lists (guarded/unguarded endpoint sets); `route_optimizations` meter gap-filled (was never recorded); no overage; month-rollover auto-lift via lazy derivation; 423 detail carries free_cap fields; phase banner wins when both locks hold; `select-tier` + receipt/reversal endpoints exempt. |
| ~~TECH-32~~ | NB-32 | ✅ IMPLEMENTED — Pitch ladder: `threshold_crossings` table, fire-once-per-threshold-per-month (lazy insert on activation read), utilization = max of both meter pcts; p60 dismissible/no CTA, p80 persistent "See pricing" → in-product `/account`, p100 = the lock banner itself ("Upgrade now"); never leaves console. |
| ~~TECH-33~~ | NB-33 | ✅ IMPLEMENTED — Milestone-6 toast exactly once per org (server truth via `toast_fired_at`), exact NB-33.1 copy, no CTA, auto-dismisses (6s), fires on any substrate. |
| ~~TECH-34~~ | NB-34 | ✅ IMPLEMENTED — Every login lands on `/dashboard` (`/` → DashboardPage, regression-tested); banner copy matrix: 0 of 5 / N of 5 / 80% pre-optimization / none after m6. |
| ~~TECH-35~~ | NB-35 | ✅ IMPLEMENTED — Admin workspace reset: `POST /activation/reset` with exact typed workspace-name confirmation (422 mismatch); one transaction wipes real rows + re-seeds + resets m6/toast + deletes crossings + audit `workspace.reset_to_sample_data`; console clears cache + logs out + redirects to `/login` (re-login lands on `/` with 0% banner); no server token invalidation (stateless JWTs — documented). |

**Adjudication notes:** (1) **@architect amendment §0A** (in `docs/plans/phase4-activation-milestones.md`): global unique constraints on `warehouses.code` / `items.sku` / `fleet_assets.vehicle_code` were a pre-existing multi-tenant defect (migration `0011` added org_id without dropping them) — replaced with composite `(organization_id, key)` unique indexes in migration `20260806_0016` (both dialects). Two-org identical seeding proven by test. (2) **TECH-48 (folded)**: two Phase 1 tests were tz-fragile (`date.today()` local vs UTC) — fixtures now UTC-anchored; production untouched. (3) **Ingestion org-scoping (decision #13)**: the 5 CSV handlers now scope by `writable.organization_id` and stamp org + `data_origin='real'` — the one place Phase 4 altered existing multi-tenant behavior. (4) `fleet_assets` gained `organization_id` (was missing). (5) QA round 1 found: checklist density not state-driven at 5-of-5, missing placeholder CTAs, missing reset-flow console test — all fixed, console 30/30.

## Follow-up ticket (deferred to a later batch)

| TECH | Parent | Ticket summary |
|---|---|---|
| TECH-49 | — | Global unique index `ix_shipments_shipment_no` (migration `0003`) is a multi-tenant hazard of the same class as §0A.1. No current code path creates Shipment rows from user input, so NOT urgent — apply the same composite `(organization_id, shipment_no)` treatment when shipment creation lands. Recorded per `docs/plans/phase4-activation-milestones.md` §0A.2. |

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
