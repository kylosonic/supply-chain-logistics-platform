# Pending Behaviors — Gap Ledger

> This file is the running ledger of behaviors that are locked-in (described in `docs/behaviors/*.md`) but not yet implemented. Each entry has a unique ID (`NB-XX`), a priority, the affected feature, and concrete user-acceptance criteria. The `@build` agent should not close these tickets without a corresponding `@qa` audit against the criteria.
>
> Conventions:
> - **Priority:** `P0` blocks launch of the feature. `P1` must ship in v1 but can ship after first paying customer. `P2` is desirable for v1 but not blocking.
> - **Acceptance criteria** are written from the user's perspective (state, action, observable consequence), not implementation mechanics.

---

## Feature: Cashflow & Bank-Transfer Receipt Verification

Source behavior doc: [`cashflow-bank-transfer-receipt-verification.md`](./cashflow-bank-transfer-receipt-verification.md)

### NB-01 — Tier pricing locked into the system — [IMPLEMENTED]
- **Priority:** P0
- **Feature area:** Subscription tiers, invoice generation
- **Acceptance criteria:**
  1. When an admin views the plan catalog, the flat prices displayed are Starter 4,500 ETB/month, Scale 10,000 ETB/quarter, Enterprise 45,000 ETB/quarter.
  2. When an invoice is issued for an upgraded Starter customer, the line items on the invoice show the flat amount as 4,500 ETB and any overage line as meter-rates from existing metering code (`delivery_tasks 0.20 ETB`, `route_optimizations 1.5 ETB`).
  3. When an invoice is issued for an upgraded Scale customer, the flat amount is 10,000 ETB billed quarterly with the billing period stated as the upcoming quarter (e.g., "Sep 1 – Nov 30").
  4. When an invoice is issued for an upgraded Enterprise customer, the flat amount is 45,000 ETB billed quarterly; no overage line items ever appear on Enterprise invoices regardless of usage recorded in the meter.
  5. Free tier customers never receive an invoice and never see a "Billing" or "Invoice" surface in the product.

### NB-02 — Two collection accounts (CBE + Dashen) surfaced on every invoice — [IMPLEMENTED]
- **Priority:** P0
- **Feature area:** Invoice rendering, payment instructions
- **Acceptance criteria:**
  1. Every invoice displays exactly one of: the CBE collection account string or the Dashen collection account string, alongside the bank name and account holder.
  2. The account is selected by the system at invoice issuance; the customer cannot switch the designated account after issuance.
  3. The two account strings are stored in a single configuration surface (no per-customer preference; all customers see one of these two accounts based on system policy).
  4. Accounts other than CBE and Dashen are never displayed on any invoice regardless of admin action.

### NB-03 — 7-day trial on first upgrade to any paid tier — [IMPLEMENTED]
- **Priority:** P0
- **Feature area:** Subscription lifecycle, workspace access
- **Acceptance criteria:**
  1. When a Free-tier customer clicks upgrade to Starter, Scale, or Enterprise, the trial starts immediately and lasts exactly 7 days (168 hours).
  2. During trial, the customer has read-write access to all features of the chosen tier.
  3. No invoice is issued and no payment surface appears during the 7-day trial.
  4. At the end of the 7-day trial, the workspace drops to read-only limbo (see NB-04).
  5. Trials do not stack — a customer cannot start a second trial of the same tier after a previous trial of that tier ended. Re-trials of the same tier are blocked silently.

### NB-04 — Read-only limbo between trial end and billing-period start — [IMPLEMENTED]
- **Priority:** P0
- **Feature area:** Workspace state, billing cadence
- **Acceptance criteria:**
  1. When a trial ends, the workspace enters read-only limbo until the start of the next billing period (the 1st of the following month for Starter, the 1st of the quarter for Scale/Enterprise).
  2. In limbo, the customer can log in, view all data, and export data. Write operations (route optimization runs, CSV uploads, mutations) are disabled.
  3. The customer sees an in-product banner: "Your trial has ended. Your first invoice is due on [billing-period start date] — once paid, your workspace resumes."
  4. At the moment the billing period starts, the first invoice is issued and the 3-day warning fires (NB-05). The limbo state continues until the invoice is paid or the lock is enforced.

### NB-05 — 3-day warning fires on every invoice at issuance — [IMPLEMENTED]
- **Priority:** P0
- **Feature area:** Invoice communication
- **Acceptance criteria:**
  1. The moment any invoice is issued to a customer (first invoice or any subsequent), a 3-day warning notification fires in-product.
  2. The notification displays: the invoice number, the flat amount expected, the designated bank account (CBE or Dashen), and the due date.
  3. The notification persists in the customer's notification surface for the full 3-day window.
  4. The notification is in-product only (no SMS, no email) — the only SMS in this feature fires on escalation (NB-09).

### NB-06 — Grace window: 3 days on first invoice, 0 days on subsequent — [IMPLEMENTED]
- **Priority:** P0
- **Feature area:** Lock enforcement, customer trust
- **Acceptance criteria:**
  1. On the customer's first invoice ever (post-trial), if no verified receipt reduces the invoice balance to zero by the due date, the workspace stays writable for an additional 3 calendar days before hard lock.
  2. On the customer's second invoice and every subsequent invoice, the grace window is 0 days. The moment the due date passes with a non-zero balance, the workspace hard-locks.
  3. During grace, write operations are disabled (same behavior as hard lock, but with a banner reading "Grace period: X days remaining").
  4. The customer cannot reset the first-invoice grace by upgrading tiers; only paying clears the lock.

### NB-07 — Receipt upload surface with auto-routing to open invoices
- **Priority:** P0
- **Feature area:** Receipt management, customer upload
- **Acceptance criteria:**
  1. There is a single customer-facing upload surface for receipts; the customer does not specify which invoice the receipt is for.
  2. The system auto-routes receipts to the customer's oldest open invoice with a non-zero balance.
  3. If a customer has multiple open invoices and the receipt amount exceeds the oldest invoice's remaining balance, the surplus flows to the next-oldest open invoice, and so on, applying the tolerance rules from NB-08.
  4. At upload, the customer sees "Receipt received — verification typically takes ≤24 hours." No further live status updates push to the customer.
  5. Only image files (PNG, JPG) and PDF files are accepted. Other file types are rejected at upload with the message "Unsupported file format."

### NB-08 — Partial payments accepted, balance carried forward, unlock only at zero balance
- **Priority:** P0
- **Feature area:** Payment matching, lock enforcement
- **Acceptance criteria:**
  1. When a receipt amount is less than the invoice's remaining balance, the system credits the full receipt amount. Remaining balance is reduced by the credited amount.
  2. Invoice remains open while balance > 0.
  3. Workspace remains locked (or in grace, depending on grace window) while invoice balance > 0.
  4. The customer can upload additional receipts against the same invoice until cumulative credited amount ≥ invoice total.
  5. At the moment cumulative credited amount hits zero balance, the system unlocks the workspace (no optimistic unlock — unlock fires only on admin verification, per NB-09).
  6. Amount is never a rejection reason on partials. Partial payments always credit.

### NB-09 — ±1,000 ETB auto-forward tolerance, larger surplus flagged for admin
- **Priority:** P0
- **Feature area:** Payment matching, wallet credit, admin queue
- **Acceptance criteria:**
  1. When a receipt amount equals the remaining invoice balance exactly, the credit equals the receipt amount, the invoice is marked paid, the workspace unlocks on verification.
  2. When a receipt amount is between `balance` and `balance + 1,000 ETB` (inclusive), the system credits only the invoice balance to the invoice; the surplus rolls forward as a **wallet credit** on the customer record. The wallet credit automatically reduces the next invoice's expected total. The customer sees in-product: "Wallet balance: +X ETB applies to next invoice."
  3. When a receipt amount exceeds `balance + 1,000 ETB`, the receipt is flagged in the admin queue as "Large surplus — admin manual decision required." The admin takes one of three actions: (a) credit forward as wallet credit, (b) credit backward for manual offline refund, (c) treat as partial credit with surplus ignored. The system applies the chosen action on the admin's confirmation.
  4. The system never auto-rejects based on amount.

### NB-10 — AI-assisted receipt extraction via existing BYOK provider key
- **Priority:** P0
- **Feature area:** Receipt processing, BYOK integration
- **Acceptance criteria:**
  1. The system uses the customer's organization-preferred AI provider key (the existing BYOK preference surface) to perform extraction on uploaded receipts.
  2. If no provider key is set on the organization, the system surfaces a configuration warning in the admin queue: "No AI provider key set on this organization — extraction will be returned at zero confidence; admin must manually read the receipt."
  3. The extractor returns eight structured fields per receipt: sender name, sender account number, receiver account number, receiver name, transfer amount, transfer date, reference number, bank identifier.
  4. The extractor returns a confidence score per field. Fields below a low-confidence threshold (configurable, default 60%) are visually flagged in the admin queue as "low confidence — please manually verify."
  5. The extraction is logged in the audit trail alongside the verification decision (NB-12).

### NB-11 — Trusted-payer list per organization, admin-only
- **Priority:** P0
- **Feature area:** Sender identity, fraud prevention, admin workflow
- **Acceptance criteria:**
  1. Each organization has its own trusted-payer list scoped to that organization. Senders approved for Org A are not visible to or usable by Org B.
  2. Customers cannot view, edit, pre-add, or remove entries from their organization's trusted-payer list. The list is admin-only.
  3. When a receipt arrives and the sender matches an entry on the organization's trusted-payer list, the receipt auto-flows through the admin queue with the recommended verdict pre-filled as "Verify." The admin still clicks Verify (pessimistic unlock requires the human action).
  4. When the sender is not on the trusted-payer list, the admin queue item is flagged "NEW SENDER" with a prominent visual marker.
  5. The admin selects one of: "Verify + add to trusted-payer list," "Verify, do not add," or "Reject." Each selection produces a different persistence action on the trusted-payer list.

### NB-12 — "Cash" sender always double-flagged even if previously approved
- **Priority:** P0
- **Feature area:** Fraud prevention, high-risk sender handling
- **Acceptance criteria:**
  1. When the AI extractor returns sender = "CASH" (case-insensitive match), the receipt is double-flagged in the admin queue regardless of whether "CASH" is on the organization's trusted-payer list.
  2. The flag reads "Cash deposit — confirm with customer that this was their intended transfer."
  3. The flag persists and the admin must still click Verify (no auto-flow even with prior approval).
  4. The admin may verify the cash receipt normally.

### NB-13 — Wrong-bank-within-portfolio auto-credited, not rejected
- **Priority:** P0
- **Feature area:** Payment matching, customer friction reduction
- **Acceptance criteria:**
  1. When an invoice designated account X (CBE or Dashen) and the receipt shows the other in-portfolio account (Dashen or CBE), the receipt auto-flows through the admin queue with the recommended verdict pre-filled as "Verify."
  2. The admin still clicks Verify (pessimistic unlock).
  3. No "wrong-bank-within-portfolio" rejection message is shown to the customer for this case.
  4. "Wrong bank" rejection is reserved exclusively for receipts from banks outside the CBE/Dashen portfolio, which would not appear in the admin queue in practice (such a payment would have landed at a different recipient).

### NB-14 — Hard reject on duplicate reference number across the entire system
- **Priority:** P0
- **Feature area:** Fraud prevention, deduplication
- **Acceptance criteria:**
  1. The reference number is the dedup key for receipts across the entire system, not just within a single organization.
  2. When a receipt is uploaded whose extracted reference number already exists on any previously-verified receipt (current customer, different customer, current invoice, prior invoice, etc.), the system hard-rejects the receipt with the verdict "Duplicate submission."
  3. The rejection banner reads: "Your receipt (ref X) was rejected. Reason: This reference number has already been credited. Please upload a new receipt for your current invoice."
  4. The duplicate-event pair is flagged in the audit trail for fraud review (the original receipt that used this reference, plus the duplicate attempt).

### NB-15 — Rejection codes enumerated, amount never a rejection reason
- **Priority:** P0
- **Feature area:** Verification verdicts, customer communication
- **Acceptance criteria:**
  1. The admin's available verdicts are exactly: Verify, Reject — wrong bank (outside portfolio), Reject — duplicate submission, Reject — illegible / unreadable, Escalate.
  2. There is no "Reject — amount mismatch" verdict in the admin's available actions.
  3. Partial receipts never produce a rejection of any kind.
  4. Each rejection produces an in-product banner to the customer with the specific rejection reason and a re-upload button. No rejection produces an SMS.

### NB-16 — Escalation is the only state that triggers customer SMS
- **Priority:** P0
- **Feature area:** Customer communication, escalation workflow
- **Acceptance criteria:**
  1. The escalation state is reserved for ambiguous cases the admin cannot verify or reject outright (ambiguous sender, suspicious surplus, partial payment without explanation, etc.).
  2. On escalation, the customer receives both (a) an in-product banner with the admin's escalation question and (b) a single SMS to the customer's registered phone reading: "Hi [Customer], FreightPilot has a question about your recent receipt. Please log in to your workspace to respond."
  3. The SMS is ≤160 characters, includes only the brand name and the request to log in, and contains no specifics about the receipt.
  4. The escalation SMS fires only on escalation. All other rejection or verification outcomes are communicated in-product only.
  5. The workspace stays locked (or in grace, depending on grace window) while escalation is unresolved.

### NB-17 — Dispute path converts rejections to escalations
- **Priority:** P1
- **Feature area:** Customer voice, admin queue
- **Acceptance criteria:**
  1. Every rejection banner includes both a "Re-upload" button and a "Dispute this decision" text box.
  2. When the customer submits a dispute, the disputed rejection converts into an escalation case in the admin queue with label "Customer disputes rejection" and the dispute text attached.
  3. The workspace remains read-only until the dispute is resolved in the customer's favor.
  4. The admin renders a final decision on the dispute (verify or maintain rejection); the customer is notified in-product of the decision.

### NB-18 — Every verification action creates a permanent audit record
- **Priority:** P0
- **Feature area:** Audit trail, accountability
- **Acceptance criteria:**
  1. Every verification action (verify, reject, escalate, partial-credit, reversal) creates exactly one audit record.
  2. The record contains: timestamp (Addis timezone), admin user ID, invoice number, receipt reference number, sender name as extracted, amount as extracted, expected invoice balance at moment of action, decision, credit delta applied, admin free-text note (mandatory on escalations and on "Verify, do not add to trusted-payer list" one-offs; optional elsewhere).
  3. The audit record is immutable post-write. Reversals (NB-19) create their own audit records rather than mutating original records.

### NB-19 — Silent undo of verifications within 24 hours
- **Priority:** P1
- **Feature area:** Admin workflow, mistake recovery
- **Acceptance criteria:**
  1. Within 24 hours of having verified a receipt, the admin sees an "Undo" action on that verification's audit record.
  2. On click of Undo, the system silently reverses the credit, restores the invoice balance, and re-locks the workspace if appropriate.
  3. No customer notification is sent for an Undo within 24 hours.
  4. After 24 hours pass, the Undo action is no longer visible on the verification record. Only the explicit reversal (NB-20) is available.

### NB-20 — Verified reversal with customer notice after 24 hours
- **Priority:** P1
- **Feature area:** Audit integrity, fraud recovery, customer communication
- **Acceptance criteria:**
  1. At any time more than 24 hours after a verification, the admin can reverse the verification via an explicit "Reverse" action on the verification's audit record.
  2. The reversal action requires a mandatory reason note from the admin (free text).
  3. On reversal, the customer receives an auto-message: "Your payment of X ETB credited on (date) against Invoice #Y has been reversed. Reason: (admin note). Please contact us if you believe this is in error. Your workspace may be locked."
  4. The reversal creates its own audit record, distinct from the original verification (NB-18).
  5. The reversal does not perform a manual bank refund — the refund is handled offline as a separate manual action; the system only adjusts the invoice balance and lock state.

### NB-21 — Fraud-risk sender flag when reversal targets a previously-added trusted sender
- **Priority:** P1
- **Feature area:** Trusted-payer list, fraud detection
- **Acceptance criteria:**
  1. When an admin reverses a verification whose original action had added the sender to that organization's trusted-payer list, the sender is not hard-blocked and not silently retained unmodified.
  2. The sender is flagged with a "fraud-risk" badge on that organization's trusted-payer list — every future receipt from this sender in that organization displays a "This sender has a reversed credit on file" badge in the admin queue.
  3. The badge persists indefinitely and is visible to the admin on every future verification involving this sender.
  4. The badge does not block verification — the admin retains discretion to verify, escalate, or reject.
  5. The admin also retains the option to manually remove the sender from the trusted-payer list entirely or to escalate any future receipt from this sender.
  6. Hard-block of a sender is a separate manual action (outside the scope of automatic reversal logic); a single reversed verification never hard-blocks a sender.

### NB-22 — Verify CBE and Dashen fee schedules before launch (verification gap)
- **Priority:** P0
- **Feature area:** Tolerance calibration, collections accuracy
- **Acceptance criteria:**
  1. Before this feature reaches production, the ±1,000 ETB tolerance defined in NB-09 must be verified against the actual published fee schedules of CBE and Dashen Bank for transfers in the 5,000–50,000 ETB range.
  2. The verification covers: same-bank intra-bank transfer fees, inter-bank RTGS transfer fees, and any flat fees or percent fees on the customer-side and receiver-side of the transfer.
  3. If the verified fee upper bound is materially below 1,000 ETB, the NB-09 tolerance window can be tightened (reduces fraud surface). If the verified fee upper bound exceeds 1,000 ETB, the NB-09 tolerance window must be widened (otherwise legitimate payments will be flagged for admin manual decision too often).
  4. The verification is documented in `docs/behaviors/cashflow-bank-transfer-receipt-verification.md` §12 (Open verification items) before this gap is closed.

### NB-23 — Site copy must reflect bank-transfer-only payment model
- **Priority:** P1
- **Feature area:** Public website (apps/product-web)
- **Acceptance criteria:**
  1. The pricing page communicates the tier ladder in ETB (Starter 4,500 / Scale 10,000 / Enterprise 45,000) with billing cycles (monthly for Starter, quarterly for Scale/Enterprise).
  2. The pricing page communicates the payment method as "Bank transfer to CBE or Dashen — receipt verified within 24 hours."
  3. The trial offer is communicated as "7-day free trial, no payment during trial, no card on file."
  4. There is no mention of Stripe, cards, "credit card on file," "annual billing discount," or any payment method not supported in v1.
  5. The "Read-only limbo" concept is communicated as a sales story: "Pay at your bank's pace — your first invoice isn't due until the start of the next billing period."

### NB-24 — Site copy must reflect the partial-payment welcome story
- **Priority:** P1
- **Feature area:** Public website (apps/product-web)
- **Acceptance criteria:**
  1. The pricing page or FAQ includes a line communicating: "Partial payments welcome. Pay what your cash flow allows, send the receipt for each transfer, and your workspace unlocks when the full balance clears."
  2. The FAQ includes a line on the wallet-credit forward mechanic: "If you overpay within 1,000 ETB, the surplus applies as credit to your next invoice."
  3. These stories must not over-promise — there is no automated refund flow on minor surpluses; only admin manual decision handles surpluses >1,000 ETB.

---

## Feature: Operator Activation & Milestone Tracking

Source behavior doc: [`operator-activation-and-milestone-tracking.md`](./operator-activation-and-milestone-tracking.md)

### NB-25 — New workspace auto-seeded with sample data on signup
- **Priority:** P0
- **Feature area:** Workspace initialization, activation flow
- **Acceptance criteria:**
  1. When a new customer signs up (via company-signup or external signup surface), the system seeds their workspace with the sample CSVs from `sample-data/` (warehouses, items, fleet assets, inventory, orders) before the customer has performed any upload.
  2. The seeded workspace supports all read and write operations on the sample data — the customer can run forecasts, run route optimizations, acknowledge alerts, approve replenishment plans, set provider keys, and change subscription tier without uploading any real CSV.
  3. Sample data seeding is per-workspace; there is no shared "demo tenant" surfaced to the customer.
  4. The audit trail records "workspace.seeded_sample_data" at signup time, with the user ID and timestamp.

### NB-26 — "Demo workspace" banner persistent until data is fully replaced
- **Priority:** P0
- **Feature area:** Activation social pressure, dashboard UX
- **Acceptance criteria:**
  1. After signup, every dashboard view displays a banner reading (paraphrased for the copy team): "You're viewing a demo workspace with sample data. Upload your real CSVs to start replacing the demo with your operation."
  2. The banner cannot be dismissed, minimized, or hidden by the customer.
  3. The banner contains a one-click CTA that navigates to `/upload`.
  4. The banner remains visible on every dashboard view until all 5 data categories (warehouses, items, fleet assets, inventory, orders) have been replaced by real uploads.
  5. When the customer has replaced N of 5 categories with real uploads (1 ≤ N < 5), the banner updates to communicate: "You're viewing a partial demo workspace — N of 5 categories is yours. Upload more to complete your real operation."
  6. When all 5 categories are fully replaced by real uploads, the banner disappears entirely (this coincides with milestone 5 of the activation checklist; the banner's disappearance is not a separate signal from milestone 5).

### NB-27 — Sample-data operations consume Free tier meters identically to real-data operations
- **Priority:** P0
- **Feature area:** Metering integrity, no "demo loophole"
- **Acceptance criteria:**
  1. Every write operation (route optimization run, CSV upload, alert acknowledgment, replenishment approval, shipment creation or update, provider preference change, manual alert creation) consumes the same meters regardless of whether the data substrate is sample or real.
  2. A Free-tier customer running 2,500 route optimization runs on full-sample data hits the Free cap and is hard-locked identically to a customer running 2,500 optimizations on real data.
  3. The audit trail of write operations identifies the data substrate where operationally relevant — route optimization audit events include a `data_origin` field that is "sample" or "real" — but the metering does not differentiate.
  4. The hard-lock (NB-31) fires uniformly on sample and real data.

### NB-28 — Six-milestone activation checklist tracked per organization
- **Priority:** P0
- **Feature area:** Activation state, cooperative onboarding
- **Acceptance criteria:**
  1. The system tracks exactly six milestones, in sequence: (1) Warehouses CSV uploaded, (2) Items CSV uploaded, (3) Fleet Assets CSV uploaded, (4) Inventory CSV uploaded, (5) Orders CSV uploaded, (6) First route optimization completed.
  2. State is per-organization, not per-user. Multiple users within the same org share a single activation state.
  3. Milestone N is registered complete only when at least one real row is uploaded for the corresponding CSV category. The seed sample-data state at signup does not register as completing milestones 1-5.
  4. Milestone 6 can be reached on either full-sample data or partial-sample data or full-real data — the first route optimization is the aha, and the data substrate doesn't gate the milestone.
  5. The activation state is reflected in the dashboard banner (NB-26) and on the `/upload` page (NB-30).

### NB-29 — Progressive dashboard panel reveal by milestone
- **Priority:** P0
- **Feature area:** Dashboard UX, value reveal as reward
- **Acceptance criteria:**
  1. Dashboard panels are hidden until their milestone prerequisite is met. Specifically: inventory charts and utilization metric tile appear only after milestone 4; forecast chart, forecast demand metric, weather risk metric, and the weather risk zones map (Routes page) appear only after milestone 5; route schedules, route optimization history, dock appointment gantt, and freight reconciliation panel appear only after milestone 6.
  2. The activation banner, exception feed panel, audit timeline panel, and feedback form are visible from signup (milestone 0) and never hidden.
  3. Panels gated by milestone display either nothing (hidden) or an empty placeholder describing their prerequisite milestone with a CTA back to `/upload` or `/routes`. The product team chooses between hidden vs placeholder per panel — the system must support both rendering modes.
  4. Panels unlock in the same order for every customer. There is no panel-specific configuration that allows skipping the reveal sequence.

### NB-30 — Activation banner surfaces on both `/dashboard` and `/upload` from shared state
- **Priority:** P0
- **Feature area:** Consistent activation UX across pages
- **Acceptance criteria:**
  1. The activation banner is rendered on both `/dashboard` and `/upload` and reads from the same per-organization activation state.
  2. On `/dashboard`, the banner renders in compact form with the "Continue setup" CTA navigates to `/upload`.
  3. On `/upload`, the banner renders as the full milestone checklist with per-step descriptions, current-step indicator, and recommended-next-step arrow.
  4. State changes (milestone completion) immediately reflect in both renderings without page reload — the customer should not have to refresh to see progress update.
  5. The banner's `data_origin` ("sample or real") state is also reflected on the `/upload` page so the customer understands which CSVs they've uploaded vs which still carry sample data.

### NB-31 — Free tier hard-locks writes when monthly cap is reached
- **Priority:** P0
- **Feature area:** Cashflow funnel, mandatory upgrade pressure
- **Acceptance criteria:**
  1. When a Free-tier customer's monthly metered usage reaches 2,500 delivery_tasks OR 50 route_optimizations (whichever comes first), the system disables further write operations on those meters.
  2. Disabled operations include: running new route optimizations, uploading new CSVs, acknowledging or resolving alerts, approving or rejecting replenishment plans, creating or updating shipments, setting or changing provider key preferences, creating manual alerts.
  3. Available operations remain: reading dashboard data, viewing schedule history, exporting any data, logging in, viewing account / subscription / provider pages, reading audit timeline and exception feed.
  4. There is no overage rate on Free tier. Hard-lock is the only mechanism. A Free customer cannot pay to lift the cap — the only way forward is upgrade.
  5. The hard-lock applies identically on sample-data operations and real-data operations (per NB-27).
  6. The hard-lock banner appears on every page in the console reading: "Free tier cap reached. Writes resume next month, or upgrade now to continue immediately." The banner contains an "Upgrade now" button that opens the in-product subscription tier picker.
  7. The hard-lock lifts automatically on the first day of the next billing month when the meter resets to zero.

### NB-32 — Escalating upgrade pitch at 60% / 80% / 100% of Free quota
- **Priority:** P0
- **Feature area:** Upgrade intent surfacing, in-product conversion
- **Acceptance criteria:**
  1. When a Free-tier customer's metered usage crosses 60% of the cap, an in-product banner fires: "You've used 60% of your Free tier tasks this month." No CTA button. Banner is dismissible until the next threshold.
  2. When the customer crosses 80%, a non-dismissible banner fires: "You've used 80% of your Free tier tasks. Consider upgrading before writes lock." With a "See pricing" button that opens the in-product subscription tier picker (`/account`).
  3. When the customer crosses 100%, the hard-lock banner fires (NB-31) with the "Upgrade now" CTA — the 100% banner supersedes the 80% banner.
  4. The upgrade CTA on both the 80% and 100% banners must never navigate the customer away from the console. The customer remains in-product through the entire upgrade flow.
  5. The banners fire once per threshold crossing per billing month — repeating the same page view does not re-fire banners that have already fired.

### NB-33 — Soft post-aha toast at milestone 6 (first route optimization)
- **Priority:** P1
- **Feature area:** Customer emotional bridge to commercial surface
- **Acceptance criteria:**
  1. Exactly once per customer (per organization, not per user), when milestone 6 is completed (first real route optimization run), a toast notification fires: "First optimization complete. Free tier covers 2,500 delivery_tasks per month — when you outgrow that, Starter lifts the cap."
  2. The toast has no upgrade button, no link to the pricing page, no commercial CTA at all. It is informational only.
  3. The toast auto-dismisses after a few seconds.
  4. The toast fires exactly once per organization, never again. Subsequent milestone 6 completions (e.g., a second user running their first optimization, or the same user running another optimization) do not re-fire it.
  5. The toast fires regardless of whether milestone 6 was reached on full-sample data, partial-sample data, or full-real data.

### NB-34 — Returning user lands on `/dashboard` with activation state surfaced in banner
- **Priority:** P0
- **Feature area:** Returning user UX, low-friction re-entry
- **Acceptance criteria:**
  1. Every login — regardless of activation state — lands on `/dashboard` (URL `/`). The system never auto-routes a returning user directly to `/upload` or `/routes`.
  2. If the customer has completed milestone 6, no activation banner is displayed. They see the full dashboard.
  3. If the customer has completed milestones 1-5 but not 6, the dashboard banner reads: "Welcome back. You're 80% through onboarding — run your first route optimization to complete setup." CTA navigates to `/routes`.
  4. If the customer has completed N of 5 CSV milestones (0 ≤ N < 5), the banner reads: "Welcome back. You're N of 5 through onboarding — next step is [next CSV category]. Continue setup." CTA navigates to `/upload`.
  5. If the customer has not completed any milestones and is still on full-sample data, the banner reads: "Welcome back. You're 0% through onboarding — 5 steps remaining. Continue setup." CTA navigates to `/upload`.

### NB-35 — Workspace reset to sample data (admin-gated, typed confirmation)
- **Priority:** P1
- **Feature area:** Catastrophic recovery, admin escape hatch
- **Acceptance criteria:**
  1. An admin user can navigate to `/account` and find a "Danger zone" section containing "Reset workspace to sample data."
  2. Clicking it opens a confirmation modal. The action cannot be performed without typing the workspace name correctly in a text field of the modal.
  3. On typed confirmation, the system deletes all real CSV-uploaded data across warehouses, items, fleet assets, inventory, and orders. Sample-data-seeded warehouses, items, fleet, inventory, and orders are re-seeded from `sample-data/`.
  4. Activation milestone state resets to "0 of 5."
  5. The action issues an audit event recorded as "workspace.reset_to_sample_data" with the admin user ID and timestamp. The event is visible in the audit timeline.
  6. The reset cannot be performed accidentally. There is no keyboard shortcut and no "are you sure" without typed confirmation. The action is intentionally nuclear.
  7. After reset, the customer is logged out and re-landed on `/dashboard` with activation banner reading "0% through onboarding."

---

## Feature: Site Conversion & Copy

Source behavior doc: [`site-conversion-and-copy.md`](./site-conversion-and-copy.md)

### NB-36 — Home page hero copy and single "Start free" CTA
- **Priority:** P0
- **Feature area:** Home page conversion, primary CTA
- **Acceptance criteria:**
  1. The home page hero displays the primary headline: "Run your first optimized route in 5 minutes. Free."
  2. The hero supporting paragraph reads (paraphrased for the copy team, exact words pending final polish): "Sign up and your workspace loads with sample data — warehouses, fleet, inventory, orders, all ready. Optimize your first route immediately. Upload your real CSVs when you're ready. Pay by bank transfer to CBE or Dashen when you outgrow the free tier. No card, no commitment."
  3. The hero contains exactly one primary CTA button reading "Start free" (not "Start free trial", not "Try FreightPilot", not "Get started").
  4. The hero does not display a secondary CTA, a "See pricing" button, a "Book a demo" button, a "Download desktop" button, or any urgency / scarcity language.
  5. The "Start free" button navigates to the existing company-signup form on `/launch`.

### NB-37 — Home page section structure (exactly five sections)
- **Priority:** P0
- **Feature area:** Home page layout
- **Acceptance criteria:**
  1. The home page body contains exactly five sections in this order: (1) Hero, (2) "How it works" expandable section (collapsed by default), (3) Pricing summary, (4) Trust strip, (5) Final CTA.
  2. No testimonials section, no customer-logo bar, no animated case-study cards, no "compare us to competitors" table.
  3. The sections are sequential, vertical, not behind tabs or carousels.
  4. The home page does not force the visitor to navigate to other routes (`/platform`, `/technology`, `/pricing`, `/launch`, `/contact`) — those remain accessible only from the top nav.
  5. All five sections are reachable by single vertical scroll from top to bottom.

### NB-38 — "How it works" section collapsed by default with exactly three steps
- **Priority:** P0
- **Feature area:** Home page "how it works" expansion behavior
- **Acceptance criteria:**
  1. The "How it works" section is collapsed by default on home page load. It displays a single visible heading "How it works in 5 minutes" with a "Show" affordance (chevron, plus icon, or equivalent).
  2. On expansion, the section reveals exactly three steps in this order:
     - Step 1: "Sign up free — your workspace loads with sample data in under a minute."
     - Step 2: "Run your first route optimization on the sample data — see the map, the stops, the schedule."
     - Step 3: "Upload your real CSVs (warehouses, items, fleet, inventory, orders) when you're ready. Pay by bank transfer to CBE or Dashen when you outgrow the free tier."
  3. There is no fourth step.
  4. The section contains no images, videos, GIFs, or product-screenshot carousels. Text and line icons only.
  5. The expanded state can be collapsed back to the default state by the same affordance used to expand it.

### NB-39 — Pricing summary: 3 paid tiers + Free line below, no "Most Popular" badge, no "Contact sales"
- **Priority:** P0
- **Feature area:** Home page pricing surface
- **Acceptance criteria:**
  1. The home page pricing summary displays a compact table with 3 rows, one per paid tier (Starter, Scale, Enterprise).
  2. The columns are: Tier | Flat price | Billing cycle | What's included (≤5 words).
  3. The rows display: Starter / 4,500 ETB / per month / First lift off Free tier; Scale / 10,000 ETB / per quarter / Mid-size dispatch shop; Enterprise / 45,000 ETB / per quarter / Unlimited usage, dedicated support.
  4. Below the table, a single line reads: "Free forever — 2,500 delivery tasks / month, no payment ever. Start here."
  5. No tier row displays a "Most Popular" or "Recommended" badge.
  6. The Enterprise row does not display a "Contact sales" CTA — the price is shown directly.
  7. Below the table and the Free line, the partial-payment + wallet-credit story surfaces verbatim: "Partial payments welcome. Pay what your cash flow allows — send the receipt for each transfer, and your workspace unlocks when the full balance clears. If you overpay within 1,000 ETB, the surplus applies as credit to your next invoice."

### NB-40 — Trust strip between pricing and final CTA
- **Priority:** P0
- **Feature area:** Home page conversion reassurance
- **Acceptance criteria:**
  1. Between the pricing summary and the final CTA, a single-line trust strip displays: "Bank transfer to CBE or Dashen. No card required. Partial payments welcome. No hidden fees, no annual lock-in."
  2. The trust strip does not link anywhere — it is text only, no anchor tags, no buttons.
  3. The trust strip is single-line on desktop and wraps cleanly on mobile to no more than 3 lines.

### NB-41 — Final CTA: single "Start free" button
- **Priority:** P0
- **Feature area:** Home page closing CTA
- **Acceptance criteria:**
  1. The final CTA section of the home page contains exactly one button reading "Start free."
  2. The button is large, visually prominent, on its own line.
  3. The button does not display any companion CTAs (no "See pricing" companion, no "Book a demo").
  4. The footer below the final CTA is the site chrome footer (existing component), not an additional CTA surface.
  5. On click, the button navigates to the existing `/launch` signup form.

### NB-42 — Page weight budget: under 1.2 MB total, under 3 seconds on 3G
- **Priority:** P0
- **Feature area:** Site performance, Ethiopian mobile connection reality
- **Acceptance criteria:**
  1. The home page total page weight (HTML + CSS + JS + fonts + images + media + chrome) is under 1.2 MB when measured with browser devtools network panel under a 3G profile.
  2. The home page finishes loading (LoadEventEnd or equivalent) in under 3 seconds on a 3G connection profile (400 kbps).
  3. No video assets load on the home page (no `<video>`, no YouTube embed, no background mp4).
  4. Hero background is CSS-driven (gradients, layered backgrounds) — no hero background image larger than 100 KB.
  5. Framer-motion usage on the home page is limited to exactly one entrance animation on the hero. No scroll-triggered motion sections, no staggered card entrance animations on the pricing table, no animated counters.
  6. The web font families loaded on the home page are Inter and Space Grotesk only — no additional font families.
  7. Third-party analytics scripts load with `defer` or via next/script `strategy="lazyOnload"`. No synchronous third-party scripts in `<head>`.
  8. The expanded "How it works" section contains no images (per NB-38 criterion 4).

### NB-43 — No fabricated social proof anywhere on the site
- **Priority:** P0
- **Feature area:** Honesty in marketing copy
- **Acceptance criteria:**
  1. No page on the site displays "Trusted by N operators" or any specific numeric customer count claim.
  2. No page on the site displays invented customer logos (e.g., placeholder brand logos implying customer relationships that don't exist).
  3. No page on the site displays fake five-star reviews, fake testimonial quotes, or fabricated case-study cards with invented customer names.
  4. No page displays a "Compare us to competitors" style table that invents competitor weaknesses or invents FreightPilot advantages not backed by real product behavior.
  5. The trust signals the site uses are limited to: (a) the bank-transfer-to-CBE/Dashen story (verifiable, per cashflow NB-02), (b) the sample-data-seeded-on-signup story (verifiable, per activation NB-25), (c) the no-card-required story (verifiable, per cashflow §6.1), and (d) the partial-payment-welcome story (verifiable, per cashflow NB-08 / NB-24).

### NB-44 — No "free trial" language for signup path
- **Priority:** P0
- **Feature area:** Copy precision, expectation honesty
- **Acceptance criteria:**
  1. The phrase "free trial" does not appear in the hero, the "How it works" section, the pricing summary, the trust strip, or the final CTA on the home page.
  2. The hero button reads "Start free" — not "Start free trial," not "Try FreightPilot free trial," not "Free trial access."
  3. The phrase "trial" appears on the site ONLY in contexts that describe the 7-day paid-tier-trial mechanic — and only on the `/pricing` route's FAQ or in deeper documentation, not on the home page.
  4. The signup form on `/launch` does not promise a "free trial" — it communicates "Start free, no card required" or equivalent honest language.
  5. No email confirmation or post-signup in-product copy (in the ops console) references "free trial" for the Free tier signup path. The 7-day trial language is reserved exclusively for the in-console upgrade pitch (per activation NB-32 / NB-33).

### NB-45 — Existing site components audited against page weight budget
- **Priority:** P0
- **Feature area:** Codebase audit, v1 launch readiness
- **Acceptance criteria:**
  1. Before this feature reaches production, the implementation must audit the existing `apps/product-web/src/components/site/` components — specifically `site-chrome.tsx`, `site-content.ts`, `hero-scene.tsx`, `motion-section.tsx`, `animated-counter.tsx`, `magnetic-link.tsx`, `motion-provider.tsx` — for assets, motion patterns, or dependencies that violate NB-42's page weight budget.
  2. Any component that violates the budget on the home page render path must be slimmed or removed from the home page specifically (not necessarily removed from other routes — `/platform` and `/technology` can use heavier components as long as they themselves also pass the page weight budget for their route).
  3. The audit findings are documented as a checklist in the implementation PR description, with each home page render-path component marked "OK" or "Slimmed/Removed" before the PR is merged.
  4. The audit explicitly verifies that the existing `animated-counter.tsx` component is NOT used on the home page (it may be used on `/platform` or `/technology` if those routes pass the budget).

### NB-46 — Other site routes (pricing, platform, technology, launch, contact) pass the same weight and honesty rules
- **Priority:** P1
- **Feature area:** Site-wide rules
- **Acceptance criteria:**
  1. Every site route (`/`, `/platform`, `/technology`, `/pricing`, `/launch`, `/contact`) loads in under 3 seconds on 3G with total page weight under 1.2 MB.
  2. Every site route complies with NB-43 (no fabricated social proof) and NB-44 (no "free trial" language for the Free signup path).
  3. Every site route has exactly one primary CTA, and that CTA reads "Start free" (per §13 of the behavior doc).
  4. The `/pricing` route expands on the home page's pricing summary with full tier details (quotas, overage rates, billing cycle) and the full partial-payment + wallet-credit + verification-within-24h trust story. The CTA on `/pricing` is "Start free," not "Choose Starter" / "Choose Scale" / "Contact sales."
  5. The `/launch` route is the existing company-signup form. It accepts business email + password + company name + optional tier preference. It rejects public email domains. On submit it fires the company-signup API call and on success redirects to the ops console. On success it triggers sample-data seeding per activation NB-25.
  6. The `/contact` route remains available for visitors who want to send a message. The contact form is not a hidden "lead capture for sales follow-up" funnel — visitors who fill it out are acknowledged but not entered into an automated sales drip.

### NB-47 — No Amharic localization in v1 (scope lock)
- **Priority:** P2
- **Feature area:** Localization scope
- **Acceptance criteria:**
  1. The site renders in English only for v1.
  2. Amharic localization is not implemented in v1 — it is a separate work item to scope later.
  3. The site copy must be written in clear, simple English that is accessible to a non-native English speaker operating a logistics business in Ethiopia (avoid American-idiomatic marketing phrases; prefer concrete subject-verb-object constructions).

---

## Open items deferred to later features

These are explicitly out of scope of v1 but noted here so they are not lost:

- **DEFERRED-01 — Refund flow for verified reversals.** When an admin reverses a verified credit (NB-20), the system adjusts the invoice balance but does not perform an actual refund of the money back to the customer. Refunds must be handled offline until a separate refund-flow feature is scoped.
- **DEFERRED-02 — Third collection account.** Adding a third bank beyond CBE and Dashen (e.g., Awash Bank or Abyssinia Bank) requires re-validating NB-02 (collection surface), NB-10 (AI extraction against a new receipt format), NB-13 (wrong-bank-within-portfolio logic), and site copy in NB-23. Do not add a third bank without re-running the design fork in Question 3 of the original conversation.
- **DEFERRED-03 — Intermediary payment support (Chapa, SantimPay, YenePay).** Rejected for v1 because intermediary receipts prove "I paid Chapa" not "Chapa sent to FreightPilot's account," which would require a second manual reconciliation hop. If scoped later, it requires a separate reconciliation queue on the vendor side.
- **DEFERRED-04 — USD-denominated invoices for international customers.** Out of scope. v1 serves Ethiopian operators paying in ETB to local bank accounts.
- **DEFERRED-05 — Feature-gated upgrade pitches.** When the tier differentiation extends beyond quotas to actual surface-level feature differences (e.g., preferred-AI-provider unlock at Scale, multi-warehouse schedule at Enterprise, enhanced SMS / Slack alert routing at Scale), a separate "feature-gating pitch" work item must produce those pitch surfaces. Until then, the system uses only the metering-based pitches defined in NB-32 / NB-33. The behavior in §7 of the activation doc must be revised when this work is done.
- **DEFERRED-06 — Email-based activation drip.** The current activation behavior is purely in-product. A separate email-onboarding-drip workitem can later add reminders for users who log in but don't progress milestones (e.g., a Day-3 "still stuck? here's how to format your warehouses CSV" email). Out of scope for v1; the in-product persistent banner is the v1 mechanism.
- **DEFERRED-07 — Amharic localization of the site.** v1 ships English-only. Amharic localization requires a separate copy-translation workstream, font validation for Ethiopic characters, and a bilingual navigation model. Not scoped for v1.
- **DEFERRED-08 — A/B testing framework for site copy.** v1 ships a single locked-copy variant per page. Conversion-rate experimentation infrastructure is a separate work item; v1 instruments only basic pageview + "Start free" click analytics.
- **DEFERRED-09 — Desktop-download as a primary site CTA.** The desktop shell remains available via its existing download center URL, but the v1 home page does not feature desktop download as a primary action. Browser-based trial via the ops console is the v1 funnel. Lift this restriction only after desktop distribution can validate conversion uplift vs the browser funnel.

---

## Acceptance gate before feature is marked "Implemented"

All `NB-01` through `NB-22` (cashflow), `NB-25` through `NB-35` (activation), and `NB-36` through `NB-46` (site) tickets above (`P0` and `P1`) must be `@qa`-verified against the user-acceptance criteria. `P2` tickets (`NB-23`, `NB-24`, `NB-47`) can ship later but must ship before public launch.
