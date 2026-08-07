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

## Closeout — Site Copy Closeout (NB-23 / NB-24) — ✅ COMPLETE

**Status:** Committed on `feat/tech-50-site-copy-closeout`, merged into `master` as part of the final closeout. QA APPROVED. Ledger debited 2026-08-05. **This closes the last open behaviors — the batch is fully complete.**

| TECH | Parent NB | Ticket summary |
|---|---|---|
| ~~TECH-50~~ | NB-23 / NB-24 | ✅ IMPLEMENTED — NB-23.5 read-only-limbo sales story line added to `/pricing` payment trust card verbatim: "Pay at your bank's pace — your first invoice isn't due until the start of the next billing period." (new `paymentPaceStory` export; rendered third paragraph of the SpotlightCard). All other NB-23/NB-24 criteria verified already satisfied by Phase 5 copy: ETB ladder + cycles, "Bank transfer to CBE or Dashen — receipt verified within 24 hours", trial substance ("first 7 days on that tier are a trial at no charge" + "No card required"), zero Stripe/credit-card/annual-billing mentions, partial-payment + wallet-credit story verbatim, no over-promising. Regression net: 4 new tests (57/57 product-web), trial-count invariant (2 / 1 in FAQ only), CTA count unchanged (4× "Start free"), check:bundle green (/pricing 690,976 raw bytes). |

**Closeout note:** NB-22 (CBE/Dashen fee-schedule verification) remains the sole open item — a HUMAN GAP (TECH-22) that blocks production launch only, not the codebase. Procedure in `docs/plans/phase3-audit-reversibility.md` §12.

## Phase 5 — Site Conversion: Hero, Sections, Pricing, Weight Budget & Honesty Rules (P0/P1) — ✅ COMPLETE

**Status:** Committed `9dc9b49` on `feat/market-contender-v1`. QA APPROVED. Ledger debited 2026-08-05. The site conversion feature is now FULLY SHIPPED; the `⚠️ NOT YET IMPLEMENTED` banner is stripped from `site-conversion-and-copy.md`. **This is the final phase of the batch — all TECH tickets are now closed and the branch awaits user UAT before merge to main.**

Source: `docs/behaviors/site-conversion-and-copy.md` (+ folded NB-23/NB-24 site-copy tickets — those were already covered by Phases 2/3 shipping the cashflow mechanic the copy describes)

| TECH | Parent NB | Ticket summary |
|---|---|---|
| ~~TECH-36~~ | NB-36 | ✅ IMPLEMENTED — Hero: exact H1 "Run your first optimized route in 5 minutes. Free." + verbatim supporting paragraph + single "Start free" CTA → `/launch`; no secondary CTAs, no urgency. |
| ~~TECH-37~~ | NB-37 | ✅ IMPLEMENTED — Exactly five sections in locked order (hero → how-it-works → pricing-summary → trust-strip → final-cta, `data-section` attrs); no testimonials/logos/case-studies/compare tables. |
| ~~TECH-38~~ | NB-38 | ✅ IMPLEMENTED — "How it works in 5 minutes" collapsed by default (CSS grid-rows transition, not framer-motion); exactly 3 text-only steps; Show/Hide affordance with aria state; no images. |
| ~~TECH-39~~ | NB-39 | ✅ IMPLEMENTED — Compact 4-column pricing table with the 3 locked ETB rows + Free line; no Most Popular badge; no Contact sales; partial-payment + wallet-credit story verbatim. |
| ~~TECH-40~~ | NB-40 | ✅ IMPLEMENTED — Trust strip line verbatim, text-only (zero anchors), ≤3 lines mobile via CSS. |
| ~~TECH-41~~ | NB-41 | ✅ IMPLEMENTED — Final CTA: single large "Start free" button, no companions; footer = existing chrome. |
| ~~TECH-42~~ | NB-42 | ✅ IMPLEMENTED — Weight gate `scripts/check-bundle-budget.mjs` (`check:bundle`, raw-byte sums from `.next/app-build-manifest.json` + CSS + fonts; all 6 routes 614–711 KB, ~500 KB under the 1.2 MB budget); no video; CSS-driven hero (hero-scene deleted); exactly ONE framer entrance on home (hero-entrance wrapper, test-asserted single `opacity:0`); Inter + Space Grotesk only (verified in built output); zero analytics (nothing to lazy-load); 3G devtools step documented in PR checklist. |
| ~~TECH-43~~ | NB-43 | ✅ IMPLEMENTED — All fabricated social proof deleted site-wide (testimonials, homeStats, USD pricing "Talk to sales", fake phone/HQ, "24 hours" reply promise); trust signals = the 4 verifiable stories only. |
| ~~TECH-44~~ | NB-44 | ✅ IMPLEMENTED — "free trial" absent from the Free signup path; "trial" occurs ONLY in the `/pricing` FAQ (7-day paid-tier mechanic, grep-verified); `/launch` honest ("Start free, no card required."). |
| ~~TECH-45~~ | NB-45 | ✅ IMPLEMENTED — Audit table (in blueprint §7): site-chrome **Slimmed** (scroll motion + back-to-top removed), site-content **Rewritten**, hero-scene **Deleted**, motion-section **Removed from home path** (kept for /platform+/technology), animated-counter **Deleted**, magnetic-link **OK**, motion-provider **OK**. |
| ~~TECH-46~~ | NB-46 | ✅ IMPLEMENTED — All 6 routes pass weight gate + honesty + single-CTA ("Start free"); `/pricing` full tier details from `pricing.TIER_SPECS` + trust story, CTA "Start free" everywhere (no Choose Starter/Scale); `/launch` platform-api-only signup (Supabase branch deleted — it silently broke NB-25 seeding), optional tier, public-email rejection surfaced verbatim, success redirect to console; `/contact` honest, no drip/CRM hooks, no fake details. |
| ~~TECH-47~~ | NB-47 | ✅ IMPLEMENTED — English-only v1, simple concrete English copy; metadata updated; no Amharic. |

**Adjudication notes:** (1) `hero-entrance.tsx` (25-line client wrapper) carries the single home entrance — Next 14.2.35's client-reference proxy crashes prerender when a server component renders `m` directly; QA adjudicated ACCEPTED (locked one-entrance semantics preserved, invariant strengthened). (2) Weight script reads `app-build-manifest.json` (App Router) not `build-manifest.json` (Pages router) — justified correction. (3) Housekeeping items recorded by QA (non-gating): `@supabase/supabase-js` dead dependency in product-web package.json, dead `.back-to-top` CSS, dead `iconLinks` export. (4) The 3G `LoadEventEnd < 3s` criterion remains a documented manual devtools PR-checklist item (unreachable in node).

## Deferred (explicitly NOT in this batch)

DEFERRED-01..DEFERRED-09 in `pending-behaviors.md` (refunds, third bank, intermediaries, USD, feature-gating, email drip, Amharic, A/B testing, desktop-primary-CTA) are out of scope for this batch.

## Acceptance gate

A phase is complete only when:
1. `@plan` blueprint exists in `docs/plans/` for the phase.
2. `@build` implemented TDD on `feat/market-contender-v1` and all tests pass.
3. `@qa` returns APPROVED against the blueprint AND the NB acceptance criteria.
4. Atomic commit executed on the feature branch.
5. Ledger debited: TECH tickets removed from this file, `[IMPLEMENTED]` appended to NB parents, warning banner stripped from the behavior doc (when its feature is fully shipped).

---

## Phase 6 — Live Launch: Origin Trust, Data Access Continuity & Deployment Hygiene (P0) — IN PROGRESS

**Status:** ✅ **COMPLETE 2026-08-07** — merged to `master` (`386a0f8..d68edf2`) and pushed. All Phase 6 tickets closed. Live verification: `/health` `db: ok`, preflights from both origins 200, route-optimize persist path 200 (P0 dead), prod schema at alembic head `20260808_0018` with drift closed, prod DB clean (0 test orgs).

Source: `docs/behaviors/live-launch-origin-trust-and-readiness.md` (parent tickets NB-48..NB-53)

| TECH | Parent NB | Ticket summary |
|---|---|---|
| ~~TECH-51~~ | NB-48 | ✅ IMPLEMENTED — Origin trust for BOTH official web addresses: `https://ops-console-azure.vercel.app` added to `DEFAULT_CORS_ORIGINS` (10 total) + 5 new preflight/host regression tests (test_cors_config.py 10→15); production `CORS_ORIGINS` env set (10-origin value) on platform-api Vercel project; redeployed; live preflight from both origins returns echoed `access-control-allow-origin`, unlisted origin → 400 no echo. |
| ~~TECH-52~~ | NB-49 | ✅ IMPLEMENTED — `platform-api-smoky.vercel.app` added to `allowed_hosts` code defaults; production `ALLOWED_HOSTS` env set (6-host value incl. both web origins); redeployed; live `GET /health` → 200 (host accepted, was 400-rejected); unlisted host → 400 (closed list). `main.py` untouched (TrustedHostMiddleware already keyed off settings). |
| ~~TECH-53~~ | NB-50 | ✅ IMPLEMENTED — Credential rotation continuity: consumer inventory (exactly ONE prod consumer: Vercel `DATABASE_URL`), corrected pooler URL (`postgres.<ref>` tenant-qualified username), Vercel env swapped (byte-exact, no newline), redeployed, `/health` `db: ok` within 60s; prod verified at alembic head `20260806_0017` (migrations already applied — no chain run needed); full-table JSONL backup taken pre-cleanup. Rollback path: backup + re-rotation (old password unrecoverable by Supabase design — documented). |
| ~~TECH-54~~ | NB-51 | ✅ IMPLEMENTED — Migration-fixes batch: dialect-safe uuid/boolean DDL (fix ①: 0013 backfill bind dialect-guarded), phantom-artifact removal in 0012, idempotent 0017 telemetry backfill (+3-test harness), chain-integrity regression test (head pinned 0017), dep-manifest alignment + test, product-web signup env guard (resolvePlatformApiBase) + tests; QA-approved atomic commit `5b9607a`; full chain proven on scratch PG16. Post-publication regression verification folds into TECH-56/Final UAT. |
| ~~TECH-56~~ | NB-53 | ✅ IMPLEMENTED — Live e2e verified: signup→login→activation (sample-seeded, banner "0 of 5")→warehouses (org-scoped 3/3)→optimize persist=true **200** (was 500) → m6 + toast fired. Browser-visual pass of criterion 4 deferred to human UAT (headless env; HTTP-level + baked-URL wiring verified). NB-50/52 closed before final verification per NB-53.5. |
| ~~TECH-57~~ | NB-53.3 | ✅ IMPLEMENTED — P0 org-scoping of `routes/optimize` persist path (4 query sites org-filtered via `resolve_actor_organization_id`; `or_(org == X, org IS NULL)` semantics for legacy rows); 16 new regression tests; live re-verified 200. Committed `157cbb5`. |
| ~~TECH-58~~ | — | ✅ IMPLEMENTED — Tenant isolation: warehouses/items list/get/create/update org-scoped (conditional reads, equality-only create pre-checks, org stamping, 404 guards). Live re-verified: new org sees exactly its own 3 rows. Committed `157cbb5`. |
| ~~TECH-59~~ | — | ✅ IMPLEMENTED — **Schema drift repair `20260808_0018`** (found via model-vs-prod audit after live 500): `route_schedules.assigned_asset_id/origin_latitude/origin_longitude` (+PG FK), `alerts.payload`, `shipments.scope_3_emissions_kg` were declared in models but never created by any migration (sqlite `create_all` tests masked it). Applied to prod, head pinned in chain test, 3 new migration tests. Committed `d68edf2`. |
| ~~TECH-60~~ | — | ✅ IMPLEMENTED — **Console visual overhaul ("Quiet Control Tower")**: flat deep-slate base `#0a0f16`, single accent (solid sky-500, no gradients), mono numerals (JetBrains Mono), color-only hovers, clean 2px focus rings, focused single-column login, flat sidebar/panels/headers/banners across all 20 files. 41/41 tests green, typecheck + build green, live-verified in deployed bundle (flat bg + JetBrains Mono present, no glow shadows). Committed `00e2b15`, deployed `ops-console-azure.vercel.app`. Copy, handlers, and `data-testid`s unchanged. |
| ~~TECH-61~~ | — | ✅ IMPLEMENTED — **product-web quiet pass** (same design language as TECH-60): flat `#0a0f16` base, single cyan accent (violet/amber/emerald accents removed), solid sky-500 CTAs (MagneticLink primary + signup submit), no glass blur / glow shadows / 3D-tilt spotlight cards, radii normalized (38/34/32px → rounded-2xl), calm kickers. LOCKED BEHAVIORS PRESERVED: copy, five-section structure, single-CTA rule (test constant updated to new primary class), Inter + Space Grotesk fonts, one hero entrance. 62/62 tests green, `check:bundle` weight budget PASSED (all routes ≤711KB). Committed `62146e5` (+68/−138 lines), deployed `product-web-chi.vercel.app`, live-verified (flat bg, no blur, hero copy intact, gradients absent). |
| TECH-55 | NB-52 | Smoke-test workspace removal: produce a dry-run listing of every record belonging to the smoke-test workspace; listing reviewed (must contain ONLY smoke-test data, zero customer data) before any deletion; workspace + orphaned records removed; verified absent from the ops-console data and all searches; no other workspace affected. |
| TECH-56 | NB-53 | E2E launch verification: preflight + signup flow verified against the LIVE API from both official origins; `/health` reports `db: ok`; newly created workspace visible post-signup; runs only after TECH-51..TECH-55 are verified. |

**Execution protocol for this phase:** Phase 1 = TECH-51/52 (code → QA → commit → Vercel env → redeploy → live preflight). Phase 2 = TECH-54 (QA audit of hotfix tree → atomic commit). Phase 3 = TECH-53 (inventory → dashboard rotation [human] → Vercel DATABASE_URL → redeploy → health → prod migrations). Phase 4 = TECH-55 (dry-run → review → delete → verify). Phase 5 = TECH-56 (live e2e). Ledger debits per phase by @architect only after QA sign-off. UAT halt + user-approved merge to main after ALL phases.
