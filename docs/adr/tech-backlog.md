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
| ~~TECH-49~~ | NB-64 | ✅ **IMPLEMENTED (2026-09-14)** — the global unique index `ix_shipments_shipment_no` (migration `0003`) was a multi-tenant hazard of the same class as §0A.1: two tenants could never use the same shipment number. Now reachable, because NB-64 made shipment creation accept a user-supplied number. Replaced with **two partial unique indexes** — `(organization_id, shipment_no)` where `organization_id IS NOT NULL`, and `(shipment_no)` where `organization_id IS NULL` — because SQL treats NULLs as distinct, so a single composite index would have stopped constraining unattributed legacy rows. Applied in `alembic/versions/20260811_0019_org_scoping_operations.py` (`_repair_shipment_number_uniqueness`) and mirrored in the model's `__table_args__`. Pinned by `tests/test_tenant_isolation_operations.py::test_shipment_duplicate_number_is_per_org`. |

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

## Follow-up Batch — Console UI: Website Language, Operator Density (P1) — IN PROGRESS

**Status:** Branch `feat/console-website-language-batch` created 2026-08-08 for a docs-plan-driven design hardening pass. Source-of-truth execution order lives in `docs/plans/console-ui-website-language-plan.md`. Phase 1 (TECH-62/63) QA APPROVED, committed `e70c939`, debited 2026-08-08. Phase 2 (TECH-64..68) QA APPROVED, committed `790f853`, debited 2026-08-08. Phase 3 (TECH-69) QA APPROVED, committed `78c2cfd`, debited 2026-08-08.

Source: `docs/plans/console-ui-website-language-plan.md`

| TECH | Parent | Ticket summary |
|---|---|---|
| ~~TECH-62~~ | — | ✅ IMPLEMENTED — Shared shell/tokens/page-header alignment: website-language dark field, restrained cyan accent, premium border-only surfaces, stronger workspace hierarchy, denser operator shell. |
| ~~TECH-63~~ | — | ✅ IMPLEMENTED — Login redesign: front-door trust framing, clearer primary/secondary actions, and visually separated sign-in vs bootstrap error states. |
| ~~TECH-64~~ | — | ✅ IMPLEMENTED — Dashboard top + activation hierarchy: 2-primary/3-secondary metric grouping, action-first focal point, stronger exception-queue anchor, supportive readiness/audit surfaces. |
| ~~TECH-65~~ | — | ✅ IMPLEMENTED — Route Studio workstation pass: intent-grouped form structure (scenario identity / route shape / operating constraints / persistence), dominant submit, result hierarchy with summary → mono stats → distinct diff → dense stop rows. |
| ~~TECH-66~~ | — | ✅ IMPLEMENTED — Account governance surface: five section boundaries, dominant plan/usage posture, secondary provider work area, supportive audit stream, isolated danger zone. |
| ~~TECH-67~~ | — | ✅ IMPLEMENTED — Receipts financial workflow pass: intake / wallet state / receipt history split, queue-like row scanning, structured dispute/rejection handling preserved. |
| ~~TECH-68~~ | — | ✅ IMPLEMENTED — Admin verification workstation pass: denser queue rows, segmented detail pane (flags → extracted fields → preview → verdict controls), verify primary / escalate warning-secondary / rejects muted-danger hierarchy. |
| ~~TECH-69~~ | — | ✅ IMPLEMENTED — Remaining console pages aligned: upload calm step rail + shared Dialog primitive (no blur/heavy shadow), denser shipment rows, alerts triage queue (side-stripes removed, violet→cyan), planning approval bands, providers governance rows, dark unauthorized fallback. |
| ~~TECH-70~~ | — | ✅ IMPLEMENTED — Final consistency pass: single accent family enforced (violet only in the preserved fraud-block exception), radius/input/mono normalization sweep (teal/blue/orange→0, backdrop-blur→0, token radius refs 9→31, mono sites 18→41), 55/55 tests + typecheck + build green. Committed `5029fda`. |

**Execution protocol for this batch:** Phase 1 = TECH-62/63 (commit `e70c939`). Phase 2 = TECH-64..68 (commit `790f853`). Phase 3 = TECH-69 (commit `78c2cfd`). Phase 4 = TECH-70 (commit `5029fda`). All QA APPROVED. Ledger debited per phase by @architect after QA sign-off.

**✅ SHIPPED 2026-08-08 — merged to `master` (`bb87988..389950c`, fast-forward) and pushed.** Docs commit `389950c` (ledger + PRODUCT.md + phase blueprints + source plan). Self-verification before merge: 55/55 tests, typecheck, production build, bundle markers, local preview 200. Live verification after Vercel deploy: `https://ops-console-azure.vercel.app` serves the new design language — live CSS hash-identical to local build with `fp-shell-surface`/`fp-row`/`fp-dialog-overlay`/`fp-input` tokens, shell descriptor in main chunk, and deployed LoginPage chunk carries `Enter control tower` / `Create initial admin` / `Create company account` / `first-time setup`. UAT residuals carried: 10 rounded-xl/2xl baseline sites in locked components (ActivationBanner ×6, MetricTile, PostAhaToast, RouteMap, RouteSchedulesTable) and AdminReceiptsPage L107 pre-existing `hover:bg-sky-400` on the undo-confirm button — documented, non-blocking. This closes the console website-language batch; the follow-up batch section is fully debited.

## Follow-up Batch — Console Navigation & Login Continuity (P1/P2) — TICKETS WRITTEN, AWAITING @ARCHITECT EXECUTION

**Status:** Behavior doc + gap tickets locked by the human (2026-08-08). Tickets NB-54..NB-59 in `docs/behaviors/pending-behaviors.md`, living behaviors in `docs/behaviors/console-navigation-persistence.md`, PM plan in `docs/plans/console-navigation-ux-plan.md`. A SINGLE feature branch (`feat/console-navigation-ux`) hosts the batch. **Phase 1 (TECH-71, TECH-76) QA APPROVED, committed `01808ae`. Phase 2 (TECH-72, TECH-73) QA APPROVED, committed `ab9262a`. Phase 3 (TECH-74, TECH-75) QA APPROVED, committed `a7da5c4`. All debited 2026-08-08 — batch code-complete, awaits human UAT before merge to master.**

Source: `docs/behaviors/console-navigation-persistence.md` (parent tickets NB-54..NB-59)

| TECH | Parent NB | Ticket summary |
|---|---|---|
| ~~TECH-71~~ | NB-54 | ✅ IMPLEMENTED — Eliminate full page reloads: every in-app link that leads to another console page becomes in-app navigation (dashboard gate placeholders ×2, metric-tile CTAs, route-studio placeholder ×1). External addresses stay external (OSM attribution + signup link verified). Static regression guard `internalNavGuard.test.ts` pins zero raw `<a href="/` in src. |
| ~~TECH-72~~ | NB-55 | ✅ IMPLEMENTED — Persistent shell: layout-route restructure (single auth-only ProtectedRoute wraps Layout at `/`; dashboard = index; 9 child routes keep byte-exact `allowedRoles`); Suspense nested inside Layout around `<Outlet/>` so lazy chunk loads never unmount the shell; RouteFallback relocated to Layout and exported; shell markup/drawer/banner unchanged; live payloads never invalidate `['activation']` → no banner refetch on navigation. |
| ~~TECH-73~~ | NB-56 | ✅ IMPLEMENTED — Live updates connect once per session: single `SessionLiveUpdates` socket owner in Layout (RoutesPage's hidden second socket consolidated); module-level payload store (`useLivePayload` SSR-safe, `useLivePayloadStream` new-publish-only); payload-scoped invalidation (inventory/routes/forecast only) via trailing-edge 15s coalescer (`createCoalescedInvalidator`, latest wins, dispose); connect-once-and-stop reconnect policy (graceful absence, no churn); "Live sync" chip reads shared store, copy verbatim. |
| ~~TECH-74~~ | NB-57 | ✅ IMPLEMENTED — Calm page transitions: single ~140ms `fp-page-fade` via `PageTransition` (keyed by pathname, first-mount suppressed, StrictMode-safe); 27-row animation inventory executed — all page-mount entrance classes/delays stripped (`.fp-row` baked animation removed, dead `.stagger-*` deleted), only state-change animations kept (dialogs, pulseRing, error blocks, results container); reduced-motion block untouched; `motion.guard.test.ts` pins the allowlist. |
| ~~TECH-75~~ | NB-58 | ✅ IMPLEMENTED — Scroll restoration: `ScrollManager` (window-only, passive 100ms-debounced save per pathname, POP → restore saved ?? 0, PUSH/REPLACE → top, SSR-safe) + pure `createScrollPositions()` Map factory; RouteFallback upgraded to `fp-nested-surface` skeleton surface with `role="status"` and sr-only "Loading workspace surface..." (copy preserved). |
| ~~TECH-76~~ | NB-59 | ✅ IMPLEMENTED — Auth continuity: 401 handling is fully soft (module-level `onAuthSessionExpired` pub/sub + establishment guard in `api.ts`; interceptor never touches `window`; redirect via ProtectedRoute only — no reload-into-login loops), token never cleared by follow-up calls after sign-in, `getToken()` stored-token-only (dead `/auth/token` fallback removed), signup link resolves to the real product site (`https://product-web-chi.vercel.app/launch` fallback + `.env.example` aligned), sign-out stays in-app. 4 new interceptor tests + 1 signup-URL smoke assertion. |

**Execution protocol for this batch:** single branch `feat/console-navigation-ux`; Phase 1 = TECH-71/76 (`01808ae`), Phase 2 = TECH-72/73 (`ab9262a`), Phase 3 = TECH-74/75 (`a7da5c4`); each phase: @plan blueprint → @build TDD → @qa audit → atomic commit on QA APPROVED → ledger debit by @architect.

**✅ SHIPPED 2026-08-08 — merged to `master` (fast-forward `3164b45..d52da1d`) and pushed.** Ledger closeout `d52da1d` (NB-54..59 `[IMPLEMENTED]`, TECH-71..76 debited, banner stripped, 3 phase blueprints). Self-verification before merge: 109/109 tests, typecheck, production build, bundle markers (fp-page-fade present, skeleton fallback copy present, zero stagger/animationDelay in JS chunks, only preserved reset-flow `location.assign`), local preview 200. Live verification after Vercel deploy: `https://ops-console-azure.vercel.app` serves the new build — CSS `index-rq-2eo1f.css` (hash-identical to local) with `fp-page-fade`, main chunk with skeleton fallback copy, zero `animationDelay`. UAT residuals documented at phase closeout: 34 pre-existing lint findings at HEAD (zero new from this batch — sweep in a separate tech-debt batch); in-memory scroll map (native browser restore on hard reload); `/login` + `/unauthorized` have no wrapper fade (entry/edge pages by design). This closes the console navigation & login continuity batch — the follow-up batch section is fully debited.

**Diagnosis evidence (from PM investigation, for @plan/@build):** hard-reload sources — `src/services/api.ts` 401 interceptor (`window.location.assign('/login')`) + raw `<a href>` anchors (`DashboardPage` L67/L334, `MetricTile` L34, `RoutesPage` L110; OSM attribution in `RouteMap` stays external); shell remount — every route element wraps `<Layout>` in `src/App.tsx`; socket churn — `useLiveUpdates` lives in `DashboardPage` and `handleLiveMessage` invalidates six query groups (`inventory`, `forecast`, `routes`, `shipments`, `subscriptions`, `activation` in `hooks/queries.ts` L243-248); entrance choreography — `animate-fade-in`/`animate-scale-in`/`animate-slide-up` + per-item `animationDelay` stagger across pages; `AuthContext.getToken()` fallback hits `GET /auth/token` (not part of the auth surface — live socket auth silently fails in production).

**Execution protocol for this batch (per PM plan §9):** single branch; @plan blueprint per phase in `docs/plans/`; @build TDD; @qa audit against NB acceptance criteria; atomic commit per phase on QA APPROVED; ledger debits by @architect only after QA sign-off; UAT halt + user-approved merge to `master` after ALL phases.

## Follow-up Batch — Console Login Color Fidelity (P1/P2) — IN PROGRESS

**Status:** Behavior doc + gap tickets locked by the human (2026-08-08). Tickets NB-60..NB-62 in `docs/behaviors/pending-behaviors.md`, living behaviors in `docs/behaviors/console-login-color-fidelity.md`, PM plan in `docs/plans/console-login-color-fidelity-plan.md`. A SINGLE feature branch (`feat/console-login-color-fidelity`) hosts the batch. **Phase 1 (TECH-77) QA APPROVED, committed `2550841`. Phase 2 (TECH-78) QA APPROVED, committed `daaeac2`. Phase 3 (TECH-79) QA APPROVED, committed `0a68046`. All debited 2026-08-08 — batch code-complete, awaits human UAT (NB-62 AC3) before merge to `master`.**

Source: `docs/behaviors/console-login-color-fidelity.md` (parent tickets NB-60..NB-62)

| TECH | Parent NB | Ticket summary |
|---|---|---|
| ~~TECH-77~~ | NB-60 | ✅ IMPLEMENTED — Token-true surfaces: the five shared classes (`.fp-shell-surface`→`var(--fp-surface)`, `.fp-nested-surface`/`.fp-pill`/`.fp-row`→`var(--fp-elevated)`, `.fp-input`→`var(--fp-input)` bg + `var(--fp-primary)` text + `var(--fp-placeholder)` placeholder) now render the declared tokens instead of near-black slate overlays; explicit `border-color: var(--fp-border)` everywhere (Tailwind preflight currentColor trap honored); new `--fp-placeholder: #94a3b8` (5.22:1 on inputs, `--fp-muted` left untouched for product-web parity); `:focus-visible`/`.fp-row:hover`/`.fp-dialog-*`/reduced-motion/keyframes untouched; zero TSX churn (22 consumer files swept clean); `surfaceTokens.guard.test.ts` (7 assertions, red-first proven) + pure `contrastRatio.ts` module (6 pinned pairs: 13.62/10.42/6.60/5.05/2.45/5.22). 129/129 tests green. |
| ~~TECH-78~~ | NB-61 | ✅ IMPLEMENTED — Login small-text contrast: five `text-slate-500`→`text-slate-400` sites on `LoginPage.tsx` (L89/L103/L116/L169/L185) raise every login text element to AA (slate-400 = 7.22:1 on shell, 6.83:1 on elevated; full 16-site sweep tabled in blueprint §2.3; rose panels 9.30:1 pass untouched); slate ladder 400<300<200<100 preserved; hover slate-300 kept; `--fp-muted` flag noted (used nowhere on login — token frozen for product-web parity); `loginContrast.guard.test.ts` bans text-slate-500/600 in login files + pins rose/hover hierarchy. 142/142 tests green. |
| ~~TECH-79~~ | NB-62 | ✅ IMPLEMENTED (code + guards) — Regression-guard consolidation: `surfaceTokens.guard.test.ts` now proves BOTH sides (7 reference blocks + new token-block integrity block pinning `--fp-surface/--fp-elevated/--fp-input/--fp-border/--fp-primary` declarations verbatim in `:root`); `loginContrast.guard.test.ts` pins the login text side; smoke tests verified unaffected (zero edits); zero production changes this phase. 143/143 tests, typecheck + build green. **Human UAT (NB-62 AC3 — login visual + dashboard spot-check) remains the only open gate before merge.** |

**Diagnosis evidence (from PM investigation, for @plan/@build):** declared tokens in `apps/ops-console/src/index.css` `:root` (`--fp-surface` #0d141d, `--fp-elevated` #111a26, `--fp-input` #233040, `--fp-border` #1f2a37, `--fp-muted` #5b6b7d, `--fp-secondary` #8fa1b3, `--fp-primary` #dbe4ee, `--fp-accent` #38bdf8) were IGNORED by the shared component classes (L203-211 `fp-shell-surface`, L208-211 `fp-nested-surface`, L218-231 `fp-input`) — they rendered translucent slate overlays instead, stacking to near-black (`~#0c121a` shell → `~#050a14` nested → `~#04070f` input) on the `#0a0f16` canvas, with inputs darker than their container. Login page contrast: 11-12px `text-slate-500` text at ~4.0:1 (below WCAG AA 4.5:1). Phase 1 closed the surface half; Phase 2 closed the contrast half; Phase 3 locked both with guards.

**Execution protocol for this batch (per PM plan §8):** single branch `feat/console-login-color-fidelity`; Phase 1 = TECH-77 (`2550841`); Phase 2 = TECH-78 (`daaeac2`); Phase 3 = TECH-79 (`0a68046`); each phase: @plan blueprint → @build TDD → @qa audit → atomic commit on QA APPROVED → ledger debit by @architect.

**✅ SHIPPED 2026-08-08 — merged to `master` (fast-forward `0b2036b..0a68046`) and pushed.** Self-verification before merge: 143/143 tests, typecheck, production build, bundle markers (built CSS carries token values `#0d141d`/`#233040`/`#94a3b8`, `.fp-input::placeholder` → `var(--fp-placeholder)`; LoginPage chunk has `text-slate-400`, zero `text-slate-500`). Live verification after Vercel deploy: `https://ops-console-azure.vercel.app` serves the new build — CSS `index-DjxQiVWk.css` (hash-identical to local) with all token colors + `var(--fp-surface)` references. NB-62 `[IMPLEMENTED]` flipped, behavior-doc banner stripped. Batch fully debited; residual notes carried: 34 pre-existing lint findings at HEAD (zero new — tech-debt sweep owed separately); `.fp-dialog-*` modal chrome and `.fp-row:hover` state overlay deliberately token-exempt (documented in phase-03 blueprint §2.3); token values now guard-pinned — any future retune must update `surfaceTokens.guard.test.ts` in the same commit.

---

## Security Hardening + Launch Readiness Batch (NB-63..NB-79) — CODE COMPLETE, AWAITS HUMAN UAT

**Status:** Behaviour contracts locked by the human 2026-08-10 (`17ab7c8`). Implemented 2026-09-14 on the single branch `feat/security-hardening-v1` (5 commits, `6c2029f` latest, `master` untouched at `4f57019`). Behaviour docs: `docs/behaviors/production-security-hardening.md` (NB-63..71), `docs/behaviors/launch-readiness-completion.md` (NB-72..79). Source audit: `docs/security-audit-2026-08-10.md`. State: `docs/swarm/STATE.md`.

**Ledger numbering note:** this batch was scoped as SEC-01..09 / LCH-01..08 in the behaviour docs and maps to NB-63..NB-79. Execution tickets are recorded below as **TECH-80..TECH-96** — the next free numbers after TECH-79. No TECH ids were previously assigned to this batch, so nothing is renumbered.

**Verification evidence (locked dependency set):** 399 backend tests passing in a venv built from `requirements.lock` with `--require-hashes`; 143 ops-console tests + typecheck + `eslint --max-warnings=0` + production build; 62 product-web tests + Next 15 build; launch funnel 22/22 against a real HTTP server. Logs under `.artifacts/`.

| TECH | Parent NB | Ticket summary |
|---|---|---|
| ~~TECH-80~~ | NB-63 | ✅ IMPLEMENTED — Known-placeholder secrets rejected at boot by exact match against `KNOWN_PLACEHOLDER_SECRETS` (not length alone), error naming the offending variable; boot-time guard touches every `effective_*` property in `app/main.py` lifespan so a misconfigured non-dev environment aborts at startup; `.env.example` (root + app) ships empty values + generation instructions; `docker-compose.yml` requires `POSTGRES_PASSWORD`/`JWT_SECRET_KEY`/`PROVIDER_KEY_ENCRYPTION_SECRET` and binds Postgres to `127.0.0.1`. 8 tests in `tests/test_config_guards.py`. |
| ~~TECH-81~~ | NB-64 | ✅ IMPLEMENTED — Tenant scoping across every flagged surface. New `app/core/tenant_scope.py` (no upstream imports, so repositories can use it without a cycle); `organization_id` added to `shipments`, `alerts`, `replenishment_plans`, `route_schedules`, `dock_appointments`, `freight_invoices` (model + migration `20260811_0019`, dialect-correct backfill from the parent chain); 11 endpoint modules converted; cross-tenant reads answer 404 never 403; `order_by_organization_first` makes an own-org row win a code tie against a legacy NULL-org row. 12 tests in `tests/test_tenant_isolation_operations.py`. |
| ~~TECH-82~~ | NB-65 | ✅ IMPLEMENTED — `POST /api/v1/feedback` requires an authenticated user and stamps the caller's identity instead of trusting a client-supplied email. `tests/test_feedback_auth.py`. |
| ~~TECH-83~~ | NB-66 | ✅ IMPLEMENTED — `next` 14.2.35→16.3.5 (via 15.5.21; see TECH-97 for the second hop), `axios`→1.20.0, `electron` 31→43, `react-router-dom` 6→7.18.3 (production open-redirect advisory; 6 test files updated from the removed `react-router-dom/server` deep import to `react-router`). Each upgrade verified by that surface's tests + production build. |
| ~~TECH-84~~ | NB-67 | ✅ IMPLEMENTED — Supabase auth **retired, not hardened**: `supabase/RETIRED.md` records the H-6 preconditions to re-arm; unused `@supabase/supabase-js` removed from `apps/product-web`; decision recorded in `docs/adr/0001-production-database-topology.md`. |
| ~~TECH-85~~ | NB-68 | ✅ IMPLEMENTED — Open registration can no longer mint a global admin: `POST /auth/register` requires an authenticated ADMIN once any user exists; first-user bootstrap remains legal only on an empty database. |
| ~~TECH-86~~ | NB-69 | ✅ IMPLEMENTED — Generic conflict messages on register/login (no "username already exists"), uniform timing. |
| ~~TECH-87~~ | NB-70 | ✅ IMPLEMENTED — CSP for ops-console in both `nginx.conf` and `vercel.json`, tuned to the real dependencies (CARTO basemap in `img-src`, `wss` live socket in `connect-src`, `'unsafe-inline'` styles for Leaflet); CSV uploads capped (`csv_max_size_bytes`, 413 + plain-language error, read bounded at cap+1 bytes so an oversized body is never buffered); `requirements.lock` generated with `--generate-hashes`, installed `--require-hashes` in Docker and CI. |
| ~~TECH-88~~ | NB-71 | ✅ IMPLEMENTED — `testserver` dropped from allowed hosts outside dev/test via `effective_allowed_hosts`; `env` removed from `/health`; `Content-Disposition: attachment` on receipt file responses; dead `PASSWORD_SALT` removed; npm non-breaking audit fixes applied; JWT logout tradeoff documented in `STATE.md` §7 (no denylist — accepted at current scale). |
| ~~TECH-89~~ | NB-72 | ✅ IMPLEMENTED (local) / ⏳ **PRODUCTION HALF BLOCKED** — Launch funnel verified end to end against a real HTTP server: 22/22 steps covering signup → seeded workspace → first route optimisation (21.07 km, 31.61 ETB) → run history → billing state → cross-tenant 404. Evidence: `.artifacts/nb72-funnel-verification.log`. Hosted verification blocked: the production `DATABASE_URL` is a Vercel *sensitive* variable, unreadable by CLI, and `/health` reports `db: unavailable`. Single-command recovery: `scripts/rotate_and_deploy.ps1`. |
| ~~TECH-90~~ | NB-73 | ✅ IMPLEMENTED — No false rate-limit errors on the funnel path (no 429 at any of the 22 steps); per-user abuse limits (login 10/min, register 5/min, signup 3/min) unchanged and still enforced. |
| ~~TECH-91~~ | NB-74 | ✅ IMPLEMENTED (analytics half; error monitoring still open) — `apps/product-web/src/components/site/site-analytics.tsx` renders a privacy-light, cookieless provider (Plausible/Umami) **only** when both `NEXT_PUBLIC_ANALYTICS_DOMAIN` and `NEXT_PUBLIC_ANALYTICS_SRC` are set; otherwise it renders nothing at all — verified by building twice, with and without the env vars: unconfigured output contains no third-party analytics reference and the only external host is the site's own, configured output carries `<link rel="preload" href="…/script.js" as="script">` (the `afterInteractive` strategy's defer behaviour). Funnel events wired at the conversion point: `start_free_click` on submit, `signup_success` on 201, `signup_error` on failure, all routed through a `trackEvent` that is typed to a closed event union, restricted to string props, and cannot throw into the signup flow. `NEXT_PUBLIC_ANALYTICS_*` documented in `.env.example`. 7 new guards in `site-analytics.test.tsx`. **Still open:** a provider account must be created and the two env vars set in Vercel; error monitoring (Sentry-equivalent) is not wired. |
| TECH-92 | NB-75 | ⏳ OPEN (P1, **requires a code-signing certificate**) — Electron upgraded to a supported major (TECH-83) and the shell still runs from source; `electron-builder` NSIS packaging, signing, and an update feed are outstanding. Not code-blocked; externally blocked. |
| ~~TECH-93~~ | NB-76 | ✅ IMPLEMENTED (2026-09-16) — Restore drill **executed and passing** against the production Neon database via `scripts/neon_restore_drill.ps1`: snapshots production counts + alembic head, creates a copy-on-write branch, asserts all five fields match the snapshot, writes a probe table on the branch and asserts it is ABSENT in production (isolation), re-checks production is unchanged by the drill, then deletes the branch and asserts only `main` remains. Verified output: orgs=5 users=5 warehouses=15 shipments=2 head=20260811_0019, restored identical, isolation proven, branch deleted. Record at `.artifacts/neon-restore-drill-*.md`. **Note:** the pre-existing `scripts/db_backup.*` / `db_restore.*` only run `docker compose exec postgres pg_dump`, so they cannot reach a managed Postgres, and no `pg_dump`/`psql` binary exists in this environment — the Neon-native branch path is used instead. A drill that silently cannot run is worse than none, because it looks like coverage. |
| ~~TECH-94~~ | NB-77 | ✅ IMPLEMENTED (with one configuration step outstanding) — `.github/workflows/ci.yml` runs the gates a release depends on: backend tests + ruff, `pip-audit --strict` on `requirements.lock`, ops-console typecheck/lint/test/build/`npm audit --audit-level=high`, product-web test/build/`check:bundle`/audit. `docs/release-gates.md` documents how a red run blocks deploy. **Outstanding:** the GitHub branch-protection rule that makes the block authoritative is not confirmed enabled. |
| ~~TECH-95~~ | NB-78 | ✅ IMPLEMENTED — ADR-0001 records the production database topology; `supabase/RETIRED.md`; dead `@supabase/supabase-js` dependency removed; README production/schema sections rewritten against the shipped topology (stale `azljjrjatdpkcvjbpztn` ref corrected to the actually-linked project). |
| TECH-96 | NB-79 | ⏳ **HUMAN GAP — OPEN, BLOCKS PAID LAUNCH ONLY.** Same gate as TECH-22: verify CBE + Dashen published fee schedules (5,000–50,000 ETB) against the ±1,000 ETB tolerance. Recorded as an explicit launch decision rather than silently deferred. |

**Defects found and fixed while verifying this batch** (not in the original audit — recorded because the audit's scope did not include them):
| Defect | Impact | Fix |
|---|---|---|
| `/health` opened a Postgres connect with no timeout | The readiness probe hung for the OS TCP timeout (~2 min) and looked *up* while the database was down | `connect_timeout: 5` in `app/db/session.py`; `/health` now fails fast and reports `degraded` |
| `RouteScheduleSummary` extended plain `BaseModel` while declaring `id: str` | `GET /routes/schedules` raised `ResponseValidationError` → HTTP 500 once any org had a persisted schedule (masked until NB-64 made schedules listable) | Now extends `ORMBase`, matching its sibling `RouteOptimizationRunSummary` |
| `apiDetail()` returned FastAPI's array-form 422 `detail` as an object | Any validation error made React render a raw object → "Objects are not valid as a React child", i.e. a blank page instead of an error message | Both `detail` shapes flattened to a string in `apps/ops-console/src/services/authErrors.ts` |
| `scalar_one_or_none()` on an org-scoped query that also permits legacy NULL-org rows | Could raise `MultipleResultsFound` (HTTP 500) or silently return *another tenant's* row on a code tie (seed data repeats `WH-001`/`SKU-001`/`TRUCK-1001` per org) | `order_by_organization_first()` helper; `.first()` at every single-row lookup. Found by a failing cross-tenant test, not by inspection |

**Execution protocol deviation (recorded honestly, per `AGENTS.md` §6):** this batch was implemented and verified by a single agent rather than dispatched through the `@plan → @build → @qa → @security` topology in `AGENTS.md` §2, and the commits carry no `QA approved` / `@security` sign-off trailer. The verification that *was* performed is itemised in `docs/swarm/STATE.md` §4/§9 with runnable commands and saved logs, so it is auditable — but it is self-verification, not independent QA. **Human UAT (NB-81) and an independent @qa/@security pass remain open gates before merge to `master`.**

**Graphify limitation (recorded, not pretended — `AGENTS.md` §9):** `graphify` is not installed in this environment, so the mandatory pre/post graph sync was **not** performed for this batch. No `graphify update .` result is claimed.

---

## Security verification pass + dependency closure (2026-09-14, second session)

### TECH-97 — Next 16 upgrade to clear a build-chain advisory — ✅ IMPLEMENTED

A full `npm audit` run during the security pass found the earlier claim of "zero critical/high advisories in deployed dependencies" was **wrong**: `postcss <= 8.5.22` carries two HIGH and two MODERATE advisories (arbitrary `.map` file disclosure via attacker-controlled `sourceMappingURL`; XSS via unescaped `</style>`), and `next@15.5.21` pinned postcss to **exactly** `8.4.31`, so no patch-level bump could reach it and an `overrides` entry could not override an exact pin.

Investigated whether it was actually exploitable before spending the upgrade:

| Check | Result |
|---|---|
| postcss in the client bundle browsers download | **No** — 0 client chunks reference it |
| `require('postcss')` anywhere in `.next/server` at runtime | **No** |
| postcss vendored into `.next/standalone` (what the Docker image runs) | **No** |
| Attacker-controllable CSS reaching the build | **No** — CSS is repo-authored and static |

So the real deployed risk was nil, but it was still a production dependency with a HIGH advisory, which the release contract (`production-security-hardening.md` §6) treats as a release blocker. Resolved properly by upgrading to `next@16.3.5`, which ships `postcss@8.5.23`.

**Cascade fixed as part of the upgrade (each verified):**

1. **Turbopack became the default builder** and could not resolve the hoisted `next` in this npm workspace: *"Could not find the Next.js package (next/package.json)"*. Investigated overriding `turbopack.root`, but Next reads `outputFileTracingRoot` as the filesystem root and would not honour a separate Turbopack root. Since `outputFileTracingRoot` is required for the Docker standalone path (which **cannot be verified here — no Docker daemon**), the build script now pins the builder explicitly: `next build --webpack`. Reverting that pin trades a verifiable build for an unverifiable one.
2. **`app-build-manifest.json` is no longer emitted**, so `check:bundle` failed outright. Rewritten to extract the `/_next/...` asset URLs from the prerendered HTML in `.next/server/app/**`. This is a *better* measurement than the old manifest walk: it is exactly the set of files the browser loads for that route. Verified PASSED — `/launch` is the heaviest route at 1,081,474 bytes against the 1,200,000 budget.
3. `next-env.d.ts` and `tsconfig.json` were updated by the Next 16 CLI.

**Verification after the upgrade:** 62/62 site tests, production build green, standalone `server.js` present at top level (Docker `CMD node server.js` still valid), `npm audit --omit=dev` → **found 0 vulnerabilities**, `check:bundle` PASSED. 143/143 console tests + typecheck + `--max-warnings=0` lint + build unchanged; backend 398/399 with one pre-existing flaky test (`test_0013_backfill_binds_new_ids_on_sqlite`, passes in isolation, unrelated to this change).

### TECH-98 — Dev-only advisories scoped out of the release gate — ✅ IMPLEMENTED

`vitest` (critical) and `vite` (high) remain in both apps, but both are **devDependencies** — a test runner and a dev server, neither shipped to users. Their fixes require major migrations (`vitest@5`, `vite@8`) that were not attempted in this pass. CI's audit steps now run `audit --omit=dev --audit-level=high` (the deployed set, which is the contract's actual scope) plus a non-blocking full `audit` for visibility. Rationale recorded in the workflow comments.

### TECH-99 — Independent security verification pass — ✅ IMPLEMENTED (as a verification pass, not an independent auditor)

Run by the same agent that wrote the code, so this is **verification, not independent assurance** — the §2 topology deviation still stands. What was actually checked:

| Check | Command / method | Result |
|---|---|---|
| Python dependency vulnerabilities | `pip-audit -r requirements.lock --strict` | No known vulnerabilities |
| Site deployed dependency vulnerabilities | `npm audit --omit=dev` (product-web) | **0 vulnerabilities** |
| Console deployed dependency vulnerabilities | `npm audit --omit=dev` (ops-console) | **0 vulnerabilities** |
| Client bundle exposure of postcss | grep client chunks | Not present |
| Runtime exposure of postcss | grep `.next/server` + `.next/standalone` | Not present |
| Dev-only advisories | `npm audit` (full) | vitest/vite only — see TECH-98 |
| Production DB reachability | psycopg probe + TCP | Pooler reachable; **both project refs report `FATAL: (ENOTFOUND) tenant/user ... not found` across 8 pooler regions** — see TECH-89 |

**Supabase finding (corrects TECH-89's diagnosis):** the production database is not failing on a wrong password. The pooler cannot find the *project*: both `huukqxpbwqcepnkrfhdw` (current, per `supabase/.temp/linked-project.json`) and `azljjrjatdpkcvjbpztn` (legacy, per README) return `ENOTFOUND`, and neither is recognised in any of the eight standard pooler regions. Both Supabase projects are therefore deleted or long-paused. **Recovering production requires creating a new Supabase project (or another managed Postgres) and re-running migrations — not merely re-entering a password.** `scripts/rotate_and_deploy.ps1` becomes usable once a reachable URL exists.

### TECH-100 — Branch protection — ❌ BLOCKED BY PLAN, NOT SKIPPED

Attempting to enable it returns `403: Upgrade to GitHub Pro or make this repository public to enable this feature`. The repository is **private on a free plan**, and GitHub restricts branch protection on private repos to paid plans. No client-side workaround exists: the setting is server-side. Options are (a) upgrade to GitHub Pro, (b) make the repo public, or (c) accept CI as a strong signal rather than a hard block — which is the current state and is documented as such in `docs/release-gates.md` §3.





---

## Production recovery on Neon (2026-09-16) — TECH-101

**Context.** TECH-89 recorded the production database as unreachable. The security pass (TECH-99) then
established the real cause: the Supabase pooler answered `FATAL: (ENOTFOUND) tenant/user ... not
found` for **both** known project refs (`huukqxpbwqcepnkrfhdw` per `supabase/.temp/linked-project.json`
and the legacy README ref) and neither was recognised in any of 8 standard pooler regions — so both
projects were deleted or long-paused, and no credential-recovery path existed.

**Action.** Production was re-provisioned on Neon through `scripts/setup_neon_production.ps1`, fully
CLI-driven (no dashboard): Neon project `summer-wind-82665524` in `aws-eu-west-2` (PG 18.6, pooled
endpoint), 19 migrations applied, `DATABASE_URL` + `JWT_SECRET_KEY` +
`PROVIDER_KEY_ENCRYPTION_SECRET` rotated, dead `PASSWORD_SALT` removed, all three Vercel projects
deployed.

**Verified.** `GET /health` → `{"status":"ok","db":"ok"}`; launch funnel **22/22 against production**
(signup, seeded workspace, first route optimisation at 21.07 km / 31.61 ETB, billing state,
cross-tenant read → 404). All three web surfaces return 200.

**Two non-obvious failures found and fixed during the cutover**, both recorded because each cost real
diagnostic time and neither was visible from the outside:

1. **`$value | vercel env add NAME production` silently truncates the value.** The CLI reads stdin as
   "value, then optional description", and a piped string can be split — for a connection string this
   produced `invalid channel_binding value: "require` (an unterminated quote) at runtime. The write
   *appears* to succeed. Fixed by writing through a file with a byte-exact redirect; verified 157
   bytes written for a 157-character URL. The same bug would silently corrupt JWT secrets.
2. **`vercel deploy --cwd apps/<name>` double-nests the path.** Each Vercel project already has
   `rootDirectory = apps/<name>`, which Vercel applies relative to the deploy cwd, so the deploy fails
   with "The provided path .../apps/<name>/apps/<name> does not exist" — a message that misleadingly
   points at project settings. Resolved by deploying via git push to `master`, which is also the
   documented production path for this repo.

**Permanent improvement kept from this work:** `/health` now emits a structured single line
(`health_db_unavailable type=... detail=...`, DSN password redacted) on database failure. Previously a
`db: unavailable` result carried no reason at all, which is why this outage was expensive to
diagnose. A temporary response-body diagnostic was used to find the truncation and has been removed;
`/health` returns exactly `{status, db}`.

**Follow-up opened:** NB-76 (restore drill) is now unblocked and has not been run; NB-75 still needs a
code-signing certificate; NB-79 remains a human verification gate.

---

## EAII submission links hosted (2026-09-20) — TECH-102

The EAII form takes two URL fields — **Pitch Deck URL** and **Pitch Video URL** — and states that
links requiring an access request "will not be reviewed." Both are now public static pages on the
existing `freightpilot-eaii` Vercel project, chosen specifically because a static page has **no
permission model to misconfigure**: there is no "Restricted" default that can be left on, which is
the single most common way a Drive/YouTube link fails this requirement.

| Route | Serves | Link role |
|---|---|---|
| `/deck/` | 7 slide images, the 10 EAII sections mapped to slides, inline PDF + PPTX download | **Pitch Deck URL** |
| `/watch/` | HTML5 player, poster, 11 chapter timestamps | **Pitch Video URL** |
| `/deck/deck.pdf`, `/deck/deck.pptx` | file-extension fallbacks if a form validates on extension | fallback |
| `/watch/pitch-video.mp4` | the 273.6 s file itself, `video/mp4`, range-enabled | direct |

**Verification (anonymous client, no cookies):** 13/13 routes `200`; range request on the video
returned `206 bytes 0-1023/19010967`; the player reported `0:00 / 4:33`; the deck page contained all
7 slide references and all 10 required section names. Screenshots in `.artifacts/url-proof/`.

**Two things worth recording:**

1. **The MP4 is duplicated on purpose.** `/watch/pitch-video.mp4` and `/pitch-video.mp4` are the same
   18.1 MB file. The form may be filled with either link, so each page must work when opened *alone*
   — a shared parent-relative path would break if only one route were ever visited. 36 MB of static
   asset on Vercel's CDN is cheaper than a link that renders a broken player.
2. **The MP4 is gitignored, and the ignore had to become recursive.** The original pattern
   `docs/eaii/pitch-page/*.mp4` did not match the new `watch/` subdirectory, so an 18 MB binary
   silently entered the staging area on the first `git add -A`. Changed to `**/*.mp4` and the file
   was unstaged before committing; staged payload went from 24.4 MB to 3.62 MB.

### TECH-103 — Slide rasters are a manual export step

`docs/eaii/pitch-page/deck-slides/*.png` (7 files, 1920×1080) were rendered from
`FreightPilot-EAII-Pitch-Deck.pdf` with PyMuPDF and committed as binaries. There is **no script** that
regenerates them, so editing the deck and rebuilding the PDF leaves the hosted slides showing the old
content with no failure signal — the page still renders, just stale. The deck already changed once
during this work ("Core Team and Advisors" → "Core Team and Advisor"), which is exactly the kind of
edit that would desynchronise them. **Debit:** add a `scripts/build_deck_slides.py` and chain it after
PDF generation, or have `/deck/` render the PDF directly and delete the rasters.

---

## Pitch video audio was ahead of the picture (2026-09-20) — TECH-104

**Reported by the user after the first delivery:** "the audio and video arent synced the audio is
ahead." Confirmed, and worse than a tuning issue — the visual scene cues were up to **19.5s early**.

### Root cause: an estimate presented as a measurement

`derive_timing.py` computed each paragraph's duration as
`words(paragraph) / words(total) * 273.6` and documented itself as *"arithmetic on two measured
quantities, not an estimate of pace."* Both halves of that claim were wrong:

| Claim | Reality |
|---|---|
| `words(total)` is measured | it was a hardcoded `856`, from a draft with more text. The script has **748** words |
| proportional word counts are not a pace estimate | they *are* one — they assume a perfectly constant speaking rate |

The stale divisor scaled every cue by 748/856 = **87.4%**, so each cue fired earlier than the voice,
compounding along the timeline: scene 2 only 9.8s early, the close **19.5s** early. A constant rate
would still have left 1–3s of residual drift, because Kokoro does not hold one pace across paragraph
breaks.

### Why it survived the original QA

The verification at the time checked the *properties of the timeline*, not its correspondence to the
audio: 11 scene midpoints were inspected as frames, the durations summed to 273.6s, and the audio
levels were clean. Every one of those passes whether or not the cues line up with the voice. The
self-consistent number (`scene-map.json` summed to exactly 273.6s) was taken as evidence of
correctness when it was only evidence of internal consistency — a timeline can be perfectly
self-consistent and still wrong, because the error was in the input constant.

### Fix

1. **Measure, don't estimate.** `measure_timing.py` transcribes `narration.wav` with
   `faster-whisper` (small.en, int8) and aligns the recognised words to the *known* script with
   `difflib` (94.8% of tokens matched, 0.955 similarity). Because alignment is against known text,
   ASR mis-spellings cannot corrupt the result — only each word's timestamp is used.
2. **Cross-check independently.** All 19 derived onsets coincide with a silence-gap midpoint in the
   raw audio envelope within **±0.50s**. Two unrelated methods agreeing is what makes the numbers
   trustworthy; the original method had no second source at all.
3. **One generator for three copies.** The timings lived in the clip `data-start`/`data-duration`
   attributes, the `gsap` `SCENES` array, and the closing fade. `apply_measured_timing.py` now
   rewrites all three from the single measured file, so they cannot drift apart.
4. **Re-derive the scene grouping.** The paragraph→scene mapping had been fitted to the wrong
   timeline, so scenes displayed the wrong visuals for their audio (the bank-transfer visual covered
   the route-optimisation narration). Regrouped onto the chapter boundaries already published on the
   video page, which the measured onsets confirm.
5. **Fix the copies of the numbers.** The same bad figures had been pasted into `/watch/`'s chapter
   list and into the composition's HTML comments.

### Verification (two independent tests, both required)

| Test | Result |
|---|---|
| Cut placement — frame-to-frame luma change across all 8208 frames, strongest peak within ±2.5s of each intended boundary | all 10 boundaries found, worst error **0.29s** |
| Global audio offset — onset-envelope cross-correlation of the MP4's audio vs `narration.wav` | **+0.0 ms** |

Confirmed live: the deployed `/watch/pitch-video.mp4` is byte-identical (sha256) to the verified local
render.

### Lesson recorded

Two failure modes worth naming, because both are easy to repeat:

- **A constant baked into a script is invisible.** Nothing in the output looked wrong; the timings
  were plausible, monotonic, and summed correctly. Any number that describes a property of an input
  artifact (word counts, durations, file sizes) should be read from that artifact at runtime.
- **The first verifier written for this fix was itself wrong** and reported FAIL on a correct video:
  it classified frames by nearest scene signature, which breaks during crossfades where every frame
  is near-black, and its global strongest-peak-first rule let one high-contrast cut mask weaker ones.
  A verification that fails should first be suspected of being a bad test. The replacement measures
  the property directly (where does the picture change?) rather than inferring it.

**Debit:** `derive_timing.py` and `scene-timing.json` are retained only as the record of the defect and
must not be reused; the production record marks them superseded.

