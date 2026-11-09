# Cashflow & Bank-Transfer Receipt Verification — Living Behaviors

> ✅ **IMPLEMENTED** — This feature shipped in Phases 1–3 of the market-contender-v1 batch (TECH-01..21; QA-approved commits `6715f88`, `179eeda`, `fd5b69c`). One open item remains: **NB-22/TECH-22** — a human verification of CBE/Dashen fee schedules vs the ±1,000 ETB tolerance is required before production launch (see §12). Every rule below is written from the user's perspective (state, actions, consequences), not implementation mechanics.

## 1. Why this feature exists

FreightPilot sells to Ethiopian logistics operators who cannot use card-based payment processors (Stripe, Razorpay, etc.). The dominant B2B payment method in this market is a direct bank transfer to a vendor-controlled collection account, with the customer uploading a transfer receipt as proof of payment and the vendor crediting the invoice after human verification.

This feature formalizes that loop into the product so the cashflow actually flows: freeloaders don't linger, paying customers get a real subscription rhythm, and a one-person admin queue can scale without collapsing into a manual spreadsheet.

## 2. The actors and their roles

- **Customer (the organization on a paid tier):** receives invoices, initiates bank transfers at CBE or Dashen, uploads receipts, waits for verification, experiences lock when invoices don't clear.
- **Admin (the human verifier):** reviews receipts in a verification queue, decides verify / reject / escalate, maintains each organization's trusted-payer list, owns mistake reversibility.
- **System (FreightPilot):** issues invoices on the locked cadence, accepts receipt uploads, runs AI-assisted extraction on each receipt, surfaces match verdicts to the admin queue, enforces locks and grace windows, issues automated warnings and the escalation SMS.

## 3. Payment collection surface

FreightPilot accepts payment at exactly two collection accounts, both controlled directly by the operator (no intermediary):

- A **CBE (Commercial Bank of Ethiopia)** business collection account.
- A **Dashen Bank** business collection account.

At invoice issuance, the customer is shown exactly one of these two accounts (the *designated account* for that invoice). The customer wires invoice payment to the designated account and uploads the resulting receipt.

Receipts from banks other than CBE or Dashen are not supported and will not appear in the admin verification queue (such a payment would have landed at a different recipient, not at FreightPilot).

## 4. Paid tiers and pricing

The subscription ladder is denominated in Ethiopian Birr (ETB). Flat tiers already exist as quotas and overage rates in the existing metering codebase; this feature adds the flat subscription price that has been missing.

| Tier | Flat subscription | Quotas (from existing metering) | Overage (already wired) | Billing cycle | Trial on first upgrade |
|---|---|---|---|---|---|
| Free | 0 ETB forever | 2,500 delivery_tasks / 50 route_optimizations (then hard cap, no overage) | — | Forever | None |
| Starter | 4,500 ETB / month | 2,500 delivery_tasks / 50 route_optimizations, then overage | delivery_tasks 0.20 ETB each, route_optimizations 1.5 ETB each | Monthly | 7 days |
| Scale | 10,000 ETB / quarter | 5,000 delivery_tasks / 250 route_optimizations, then overage | delivery_tasks 0.16 ETB each, route_optimizations 1.0 ETB each | Quarterly | 7 days |
| Enterprise | 45,000 ETB / quarter | Unlimited (no quota) | None (no overage calculation) | Quarterly | 7 days |

Quotas and overage rates come from the existing metering code and are not redefined by this feature. This feature defines the flat subscription price and the collection/lock workflow around it.

## 5. The full lifecycle from signup to first paid cycle

### 5.1 Signup and Free tier

When a customer signs up, they begin in the **Free tier** with no invoice, no trial, no payment obligation. They can stay in Free forever. Free caps usage at 2,500 delivery_tasks and 50 route_optimizations; crossing the cap does not generate overage charges or invoices — it hard-stops further write operations on those meters until the customer chooses to upgrade.

### 5.2 Upgrading into a paid tier

When a customer chooses to upgrade to Starter, Scale, or Enterprise, a **7-day trial** of that paid tier begins immediately.

During the trial, the customer gets full read-write access to all features of the chosen tier. No payment is required during the trial. No invoice is issued during the trial. No card, account, or pre-authorization is captured.

### 5.3 Trial end and read-only limbo

The trial ends exactly 7 days after it started.

From trial end until the next billing-period start, the workspace enters **read-only limbo**. The customer can still log in, view their routes and shipments, and export their data, but write operations are disabled. The customer sees an in-product message: "Your trial has ended. Your first invoice is due on [billing-period start date] — once paid, your workspace resumes."

This limbo is **not** an additional free trial. It is the customer's runway to arrange payment at the pace of Ethiopian bank transfers while the billing-period clock is not yet running.

### 5.4 First invoice issuance

At the start of the next billing period (the 1st of the following month for Starter monthly customers, the 1st of the quarter for Scale and Enterprise quarterly customers), the **first invoice is issued**.

The first invoice includes:
- The flat subscription price for the upcoming billing period (billed in advance)
- Any overage that accrued during the trial period (the only invoice in a customer's life that includes trial-period overage — subsequent invoices bill overage from the prior paid period)

### 5.5 The 3-day warning

The moment any invoice is issued, a **3-day warning notification** fires to the customer. The notification reads (paraphrased for the product copy team): "Invoice #X for Y ETB is due on [date]. Pay to [CBE or Dashen account string] and upload your receipt. If no verified receipt reaches us by [date + grace window], your workspace will enter read-only mode."

### 5.6 Grace windows and hard lock

| Invoice position | Grace window | Hard lock timing |
|---|---|---|
| **First invoice ever** (post-trial invoice for any tier) | 3 days from due date | Lock at the end of day 3 after due date if invoice balance remains above zero |
| **Second and every subsequent invoice** | 0 days | Lock at the moment the due date passes if invoice balance remains above zero |

Locking means the workspace drops to **read-only**. The customer can log in, view, and export. They cannot run route optimizations, upload new CSVs, or trigger any other write-metered action. The lock lifts the moment a verified receipt reduces the invoice balance to zero.

## 6. The receipt upload and verification loop

### 6.1 Upload action

The customer uploads a receipt as an image or PDF through the product surface. They do not need to specify which invoice the receipt is for — the system auto-routes the receipt to whichever open invoice belongs to that customer's organization. If the customer has multiple open invoices (rare but possible, e.g. an unpaid prior invoice plus a newly issued one), the system routes the receipt to the oldest open invoice with a non-zero balance, then any surplus flows to the next-oldest open invoice (see §6.4).

At upload, the customer sees real-time confirmation: "Receipt received — verification typically takes ≤24 hours." No further live status updates are pushed to the customer until the verification decision is made.

### 6.2 AI-assisted extraction

When a receipt is uploaded, the system runs AI-assisted extraction on the receipt file. The extractor reads the document and returns the following structured fields:

1. Sender name (the account holder paying)
2. Sender account number (if visible)
3. Receiver account number (must match either the CBE or Dashen collection account)
4. Receiver name (must match FreightPilot's registered business name)
5. Transfer amount in ETB
6. Transfer date
7. Reference number (the transaction ID — used as the dedup key across all invoices)
8. Bank identifier (CBE vs Dashen — inferred from receipt layout, customer does not tag this manually)

The extractor is expected to use the customer's BYOK provider key (the same key vault already wired into the product) per the existing provider-preference system. The extractor returns a confidence score alongside each field; low-confidence fields surface to the admin visually.

### 6.3 The admin verification verdicts

The admin queue shows each pending receipt alongside the invoice it was routed to and the extracted fields. The admin renders one of the following decisions:

| Decision | Effect |
|---|---|
| **Verified** | Credit the receipt amount against the invoice balance. If balance hits zero, unlock the workspace. Add sender to the organization's trusted-payer list if the admin authorizes it (default: yes if the sender is new). |
| **Rejected — wrong bank** | Money landed at a bank outside the CBE/Dashen portfolio (functionally rare). Rejection message to the customer: "Payment must land at CBE or Dashen. Please re-send to the account listed on your invoice." |
| **Rejected — duplicate submission** | The reference number on this receipt was already credited against any invoice in the system (current or prior). Hard reject. Flag the sender and reference in the audit log for fraud review. |
| **Rejected — illegible / unreadable** | AI extractor returned low confidence on sender, amount, or reference fields, and the admin cannot manually transcribe the receipt with confidence. Rejection message: "We couldn't read your receipt clearly. Please re-upload a clearer copy." |
| **Escalated** | Admin is not sure (e.g. ambiguous sender, suspicious surplus, partial payment received without explanation). The receipt is parked. An escalation SMS fires to the customer (see §8). Workspace remains locked if it was locked. The escalation stays open until the customer responds via the in-product banner, at which point the admin makes a final verify/reject decision. |

**Partial payments are never a rejection reason.** A receipt sent for less than the invoice balance is always accepted as partial credit (see §6.4).

**Wrong-bank-within-portfolio is auto-credited, not rejected.** A receipt that lands at the non-designated in-portfolio account (e.g. invoice said Dashen, receipt shows CBE) auto-flows through the verification queue with the admin's recommended verdict pre-filled as "Verify." The admin still clicks Verify (pessimistic unlock), but the receipt is not rejected for being on the "wrong" of the two accepted accounts.

### 6.4 Amount matching and tolerance

For any single receipt, the system compares the extracted receipt amount to the opened invoice's remaining balance. The matching behavior is deterministic and amount is never a rejection reason:

- **Receipt amount < remaining balance (partial payment):** Credit the full receipt amount against the balance. Remaining balance stays open. Invoice remains unpaid. Workspace remains locked (or read-only during grace). Customer can upload additional receipts until the cumulative credited amount reaches the invoice total.
- **Receipt amount = remaining balance (exact match):** Credit the full amount. Invoice marked paid. Workspace unlocks.
- **Receipt amount = remaining balance + surplus ≤ 1,000 ETB:** Credit the invoice total. The surplus (the difference) rolls forward as a **wallet credit** on the customer record. The wallet credit automatically reduces the next invoice's expected total. The invoice is marked paid, the workspace unlocks. The customer sees in-product: "Invoice paid. Wallet balance: +X ETB applies to next invoice."
- **Receipt amount > remaining balance + 1,000 ETB (large surplus):** Do not auto-credit. Flag the receipt for **admin manual decision**. The admin sees "Customer paid X against invoice balance of Y — surplus of Z ETB is larger than the auto-forward tolerance." The admin takes one of three actions:
  - Credit forward: invoice marked paid, surplus rolls forward as wallet credit. Workspace unlocks.
  - Credit backward: invoice marked paid, surplus is logged for manual refund offline (system does not perform the refund). Workspace unlocks.
  - Treat as legit partial with surplus: in rare cases admin may apply a partial credit only; balance remains open, workspace stays locked, customer is notified.

The tolerance of ±1,000 ETB exists to absorb routine variance (bank transfer fees, customer rounding, minor fat-finger) without generating admin bandwidth per receipt.

## 7. Sender identity and the trusted-payer list

### 7.1 First-time sender flow

When a receipt arrives, the system checks whether the extracted sender name is in the target organization's **trusted-payer list**.

- **Sender is on the trusted-payer list:** The receipt auto-flows through the admin queue with the recommended verdict pre-filled as "Verify." The admin still clicks Verify (pessimistic unlock requires the human action, per §6.3). This reduces admin decision-time on repeat payers to a single confirmation click.
- **Sender is new (not on the trusted-payer list):** The admin queue item is flagged "NEW SENDER." The visual flag is prominent. The admin makes one of three decisions:
  - **Verify + add to trusted-payer list:** sender is now trusted for this organization going forward. All future receipts from this sender auto-flow.
  - **Verify, do not add:** one-off approval. Future receipts from this sender will again trigger the "NEW SENDER" flag.
  - **Reject:** no credit issued, no list change.

### 7.2 The "Cash" sender

If the AI extractor returns sender = "CASH" (common on cash-deposit counter receipts), the receipt is always double-flagged in the admin queue — even if "Cash" was previously added to that organization's trusted-payer list. The flag reads "Cash deposit — confirm with customer that this was their intended transfer." This forces a deliberate human attention touch on the highest-fraud-risk sender value. The admin may still verify the receipt.

### 7.3 Properties of the trusted-payer list

- The trusted-payer list is **per organization**. A sender approved for Org A is not automatically approved for Org B. Every trusted-payer list is scoped to one organization.
- The trusted-payer list is **admin-only**. Customers cannot self-edit, pre-add payers, or request automated additions. Only admin verification actions add or remove senders. This forces a real human-review touch on every new payer and creates a compounding audit trail of who actually pays for each workspace.
- Each organization's trusted-payer list persists across invoices. Reusing a previously-approved sender is the fast path; introducing a new sender is the slow path.

## 8. Customer communication on verification outcomes

| Event | Customer notification | Channel |
|---|---|---|
| Receipt uploaded | "Receipt received — verification typically takes ≤24 hours." | In-product confirmation, no other channel |
| Receipt rejected (any reason other than illegible) | Banner on next console login: "Your receipt (ref X) was rejected. Reason: Y. Please upload a corrected receipt." Plus a re-upload button. | In-product only — no SMS, no email |
| Receipt rejected as illegible | Same banner + re-upload button | In-product only |
| Receipt escalated | Banner on next console login with the admin's escalation question + **a single SMS** to the customer's registered phone: "Hi [Customer], FreightPilot has a question about your recent receipt. Please log in to your workspace to respond." | In-product banner + SMS on this case only |
| Receipt verified, invoice paid | Banner: "Invoice #X paid. Your workspace is unlocked." Plus a re-upload button is NOT displayed. Wallet credit displayed if applicable. | In-product only |
| 3-day warning (every invoice) | Banner fires the moment the invoice is issued: "Invoice #X for Y ETB is due [date]." | In-product only |
| Hard lock enforced | Customer already received the 3-day warning. No additional comms at lock. Customer simply experiences the read-only state. | None — silent enforcement |

The escalation SMS is the only channel besides in-product, and it fires only on the escalation state. Routine rejections are the customer's responsibility to discover by logging in.

### 8.1 The dispute path

The rejection banner includes both a **Re-upload button** and a **Dispute this decision** text box. A customer who believes the rejection was wrong can submit a short written dispute. The dispute auto-converts the rejection into an escalation case: it appears in the admin queue as "Customer disputes rejection" with the dispute text attached. The admin reassesses and renders a final decision (verify or maintain rejection).

Disputes do not unlock the workspace in the meantime. The workspace stays read-only until the dispute is resolved in the customer's favor.

## 9. Reversibility and the audit trail

### 9.1 Every verification event creates a permanent audit record

Whether the action is verify, reject, escalate, partial-credit, or reversal (defined below), the system writes a permanent record with:

- Timestamp (Addis timezone)
- Admin who acted (admin user ID)
- Invoice number the receipt was attached to
- Receipt reference number (dedup key)
- Receipt sender name as extracted
- Receipt amount as extracted
- Expected invoice balance at the moment of verification
- Decision (verified / rejected with reason / escalated)
- Credit delta applied (positive number for credits, zero for rejects and escalations)
- Admin free-text note (optional on most decisions; mandatory on escalations and on "Verify, do not add to trusted-payer list" one-offs)

### 9.2 Reversibility — two distinct mechanisms

- **Silent undo within 24 hours of verification.** Admin realizes within 24h that they misread the receipt, mistyped the verdict, or approved the wrong invoice. Admin clicks "Undo" on the audit record of the original verification. System silently reverses the credit, restores the invoice balance, and re-locks the workspace if appropriate. Customer is not notified — often the customer has not yet noticed the unlock. Use case: "I just approved this but I misread the sender name — it's a different Mulugeta."
- **Reversal with customer notice, any time after 24 hours.** Admin can reverse any past verification at any later time. A mandatory reason note is required. The customer receives an auto-message: "Your payment of X ETB credited on (date) against Invoice #Y has been reversed. Reason: (admin note). Please contact us if you believe this is in error. Your workspace may be locked." Use case: "Fraud detection surfaced that this receipt was reused from another customer three days later."

### 9.3 What about the trusted-payer list when a verification is reversed?

When an admin reverses a verification that *also added the sender to the trusted-payer list (because the original verification was a "Verify + add to trusted-payer list" decision), the sender is **not hard-blocked** and **not silently retained**. Instead, the sender is **flagged as fraud-risk** on that organization's trusted-payer list.

Concretely:
- The sender remains on the trusted-payer list so the admin can still choose to verify future receipts from this sender.
- Every future receipt from this sender in this organization displays a permanent visual badge in the admin queue: "This sender has a reversed credit on file." The badge does not block verification. It demands admin attention.
- The admin retains discretion to either verify normally (ignoring the badge), remove the sender from the list entirely (clean removal), or escalates any future receipt from this flagged sender for greater scrutiny.

A single reversed verification never hard-blocks a sender permanently. Hard-block is a separate manual admin action reserved for confirmed duplicate-receipt brokers (a manual judgement, outside this feature's logic).

## 10. The notification tone rules

This section is non-binding guidance for the product copy team that implements the in-product banners and SMS. The implementation must not violate these principles:

- In-product banners are factual, short, and action-oriented. They describe what happened, what the customer must do next, and any amounts involved. No marketing language, no apologies, no fear.
- The escalation SMS is no more than 160 characters and contains the brand name, the request to log in, and nothing else. No specifics about the receipt in the SMS itself — the specifics belong in the in-product banner.
- The hard-lock state itself is not announced separately. The customer already received the 3-day warning; the lock is the consequence of inaction. Adding a separate "you are now locked" communication would be redundant theater.

## 11. What this feature does NOT do

To preserve scope and prevent feature creep, the following are explicitly out of scope and excluded from v1:

- No automatic reversal-on-bank-reversal hook. If a bank later reverses a transfer the customer sent, the system does not claw back. The admin handles that manually as a §9.2 reversal.
- No customer-facing trusted-payer list management UI. Customers cannot self-edit, pre-add, or remove payers.
- No real-time chat between admin and customer. Disputes are written-only and asynchronous.
- No auto-pricing of new tiers beyond the locked ladder (Starter 4,500 / Scale 10,000 / Enterprise 45,000 ETB). Creation of new tiers or new currencies is not in scope.
- No international / USD-denominated invoices. All invoices are in ETB to CBE or Dashen only.
- No card-on-file collection. There is no card capture surface anywhere in the product. Payment is bank-transfer + receipt only.
- No support for intermediary payment providers (Chapa, SantimPay, YenePay, etc.) in v1. The two collection accounts at CBE and Dashen each, locally controlled, are the entire payment surface.
- No automatic credit issuance on receipt upload. Pessimistic unlock is the rule — credit requires an explicit human admin verification action, even for fully-matched receipts from previously-trusted senders.

## 12. Open verification items flagged before launch

These items require a final operations review before a production launch:

- Direct verification of CBE and Dashen published fee schedules for transfers in the 5,000–50,000 ETB range. The ±1,000 ETB tolerance in §6.4 is reasoned from adjacent NBE regulation anchor but is not yet directly verified against the actual fee tables of the two banks in scope.
