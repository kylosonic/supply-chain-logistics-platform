# BLUEPRINT: PHASE 3 — Audit Trail, Reversibility & Fraud Controls (TECH-18..22 / NB-18..22)

Status: LOCKED for execution by @build on branch `feat/market-contender-v1`. Written by @plan. QA audits against this document AND the NB acceptance criteria in `docs/behaviors/pending-behaviors.md` (lines 176-221) AND `docs/behaviors/cashflow-bank-transfer-receipt-verification.md` (§9-12). Builds ON TOP of Phase 1 (`6715f88`) and Phase 2 (`179eeda`) outputs — no re-design of existing infrastructure; only the additive integration points listed below are touched. Migration head confirmed: `20260806_0014` → Phase 3 migration is `20260806_0015`. *Note: the graphify CLI is not installed in this environment; the import map in §4 was grounded by direct module reads of every edge file (services/audit.py, billing/*, receipts/*, models, endpoints, schemas).*

## 0. Goal

Make every verification action permanently auditable and reversible: a full NB-18 field-set audit record per action (immutable, append-only), a silent **Undo** within 24 hours (credit reversed, balance restored, workspace re-locked, no customer notice), an explicit **Reverse** after 24 hours (mandatory reason note, exact auto-message to the customer via in-product Notification, distinct audit record, no automatic refund), and a persistent **fraud-risk badge** on senders whose reversed verification had added them to the trusted-payer list — the badge never hard-blocks. TECH-22 (CBE/Dashen fee-schedule verification) is a documented HUMAN acceptance-gate with NO code.

## 1. Ground-truth decisions (locked for @build; deviations require @architect sign-off)

1. **One reversal mechanism, two eligibility windows — NOT two state machines.** Undo and Reverse share one core (`reversals/core.py`): same balance restoration, same wallet-void rule, same fraud-flag trigger, same NB-18-complete audit payload. They differ only in (a) window: Undo eligible while `now <= decided_at + 24h`, Reverse eligible while `now > decided_at + 24h`; (b) Undo has no customer notification (NB-19.3), Reverse writes the exact NB-20.3 Notification row; (c) Reverse requires a mandatory reason note (NB-20.2), Undo's note is optional (NB-18.2: note optional on most decisions, mandatory on escalations and one-offs — not on undo).
2. **The receipt NEVER leaves `status='verified'`; reversal state lives on separate columns** (`reversal_status`, `reversal_note`, `reversed_by_user_id`, `reversed_at`). Rationale: the partial unique index `uq_payment_receipt_verified_ref WHERE status='verified'` is the NB-14 dedup backstop — moving a reversed receipt off `verified` would let a duplicate reference be re-credited. Keeping `verified` preserves "one credited reference forever" while the reversal becomes a correction *layer*. The queue filter (`status IN pending/escalated`) is unaffected.
3. **The original `receipts.verified` audit record is the reversal's source of truth — and is NEVER mutated.** The reversal core loads the AuditEvent with `event_type='receipts.verified'` and `entity_id=<receipt_id>`, reads `credit_delta_etb` and `balance_before_etb` from its payload, restores `new_balance = current_balance + credit_delta` (quantized `ROUND_HALF_UP`), and sets `status='issued'` when the restored balance > 0 (stays `paid` at zero — deterministic even when other receipts covered the same invoice, NB-08 multi-receipt case). The reversal writes its OWN audit record with the mirror field set (decision `undo`/`reversed`, negative credit delta). Immutability is structural: no code path ever writes to an existing AuditEvent row; the test map proves it.
4. **Re-lock = `lifecycle.refresh_workspace_state` after restoration, nothing else.** NB-19.2 "re-locks the workspace if appropriate" / NB-20.5 "workspace may be locked" are satisfied by the existing Phase 1 engine: `derive_phase` keys off `balance_remaining_etb > 0` → GRACE (if inside the original grace window) or HARD_LOCKED — both read-only. No new grace math, no lock overrides. (Consequence: an undo within 24h of a verify that paid a first-invoice with a 3-day grace may land in GRACE rather than HARD_LOCKED — still write-disabled; acceptable and documented. The refresh may also lazily issue a next-period invoice — intended, same as Phase 2 upload behavior.)
5. **Wallet interplay — void un-applied, never claw back applied.** On undo/reverse: every `WalletCredit` row with `receipt_id = <receipt>` and `status='available'` flips to a NEW `'voided'` status (constraint widened) with `voided_at`; the available pool recomputes correctly. Wallet rows already `'applied'` to a later invoice are LEFT UNTOUCHED — NB-20.5 limits the reversal's system effects to "the invoice balance and lock state", and unwinding a consumed credit would mutate a different invoice than the reversed one. This asymmetry is deliberate, documented in the `wallet.py` docstring, and covered by tests.
6. **Fraud-risk badge lives in a NEW `sender_fraud_flags` table, NOT a column on `trusted_payers`.** NB-21.2 ("every future receipt from this sender in that organization displays the badge") + NB-21.5 (admin may "remove the sender from the trusted-payer list entirely") are only jointly satisfiable if the flag survives list removal. `sender_fraud_flags` is keyed `(organization_id, normalized_sender_name)` UNIQUE with `fraud_risk_since` + `reversal_count`, rows are never auto-deleted → "persists indefinitely" (NB-21.3). The badge is display-only: no verification gating anywhere (NB-21.4, NB-21.6 — a single reversal never hard-blocks). The flag fires when the ORIGINAL verified audit payload has `trusted_payer_action == 'added'` — on BOTH undo and reverse (NB-21 draws no window distinction, and a silent clawback is the stronger fraud signal; the badge is non-punitive so early triggering is safe). Admin discretion retained: normal verify, escalate, or manual list removal via a new `DELETE /receipts/trusted-payers/{sender_name}` (list removal does NOT clear the flag — documented).
7. **The ≤24h window is evaluated SERVER-SIDE against `receipt.decided_at` (UTC), at every undo/reverse call and in every availability payload.** `undo_available = status=='verified' AND reversal_status IS NULL AND now <= decided_at + 24h`. The boundary at exactly `now == decided_at + 24h` is Undo-eligible (`<=`). Client-side hiding of the Undo button (NB-19.4) is UX only — the server 409s Undo past the window and 409s Reverse inside it. `settings.reversal_undo_window_hours: int = 24` is the single knob.
8. **Reverse customer message = in-product Notification row, EXACT NB-20.3 copy, no SMS.** Kind `receipt_reversed`, `expires_at` = now + 3 days (`NOTIFICATION_EXPIRY_DAYS` from intake). Message: `"Your payment of {amount} ETB credited on {date} against Invoice #{invoice} has been reversed. Reason: {reason}. Please contact us if you believe this is in error. Your workspace may be locked."` — amount = original `amount_etb` from the verified audit payload; date = `decided_at` rendered in Africa/Addis_Ababa (`ZoneInfo`), `%d %b %Y`; reason = the mandatory note. SMS is NOT used (NB-16: escalation is the only SMS state). Undo writes NO notification (NB-19.3).
9. **One reversal per receipt, ever.** `reversal_status IS NULL` is a hard pre-condition for both undo and reverse (else 409). After a reversal the receipt remains `verified` + `reversal_status` set; re-verifying the same receipt is impossible (status not pending/escalated → 409). The recovery path for a "wrong sender" undo is the admin re-rendering nothing on this receipt but the customer re-uploading a corrected receipt. Deterministic; re-reversal is a NON-GOAL.
10. **Cross-org admin pattern inherited from Phase 2.** Undo/reverse endpoints are gated `require_org_roles(OWNER, ADMIN)` only — same as `render_decision_endpoint`, no cross-org ownership check (the admin queue is system-wide). The reversal service acts on the RECEIPT's `organization_id` (recipient org), never the admin's membership org. Flagged for @architect if cross-org admin isolation is ever wanted.
11. **Timestamps stay UTC in storage; "Addis timezone" is a rendering concern.** NB-18.2's "timestamp (Addis timezone)" is honored in display layers (ops-console `toLocaleString`, reversal message date via Africa/Addis_Ababa). Storage convention (`DateTime(timezone=True)`, UTC) is NOT re-opened — Phase 1/2 precedent.
12. **TECH-22 = HUMAN GAP, zero code.** See §12. It is an acceptance-gate checklist item, not a ticket for @build.

## 2. Files to CREATE

All paths relative to repo root unless noted. Backend under `apps/platform-api/app/`, tests under `apps/platform-api/tests/`, console under `apps/ops-console/src/`.

### 2.1 Model — `apps/platform-api/app/models/sender_fraud_flag.py` (NEW, ~35 lines)

`SenderFraudFlag` (table `sender_fraud_flags`) — the persistent per-org fraud-risk marker (decision #6). Columns: `id` (UUIDTimestampMixin), `organization_id` FK `organizations.id` CASCADE indexed NOT NULL, `sender_name` String(128) NOT NULL (stored normalized via `trusted_payers.normalize_sender`), `fraud_risk_since` DateTime(timezone=True) NOT NULL, `reversal_count` Integer NOT NULL default 1, `created_at`. `UniqueConstraint('organization_id','sender_name')`. Imports ONLY `app.db.base`, `app.db.custom_types`, `app.models.common`, sqlalchemy.

### 2.2 Services — `apps/platform-api/app/services/billing/reversals/` package (NEW; 4 modules, every module ≤300 lines — under the 400 hard cap, split from the start per the Phase 2 precedent)

**`__init__.py`** (~30 lines) — docstring stating the package contract (one mechanism, two windows, decision #1) + re-exports: `ReversalError`, `reversal_availability`, `undo_verification`, `reverse_verification`, `is_fraud_flagged`, `flag_sender_fraud`.

**`core.py`** (~140 lines) — the shared reversal core (imports models, `services.audit`, `services.billing.wallet`, `services.billing.lifecycle`, `services.billing.receipts.intake.NOTIFICATION_EXPIRY_DAYS`, `reversals.fraud_flags`):
- `class ReversalError(Exception)` — `(status_code, message)`, mirror of `ReceiptVerdictError`.
- `UNDO_WINDOW_HOURS` reference → `settings.reversal_undo_window_hours`.
- `reversal_availability(db, receipt, now) -> dict` — `{undo_available: bool, undo_available_until: datetime|None, reverse_available: bool}` per decision #7 (also used by the audit-read surface).
- `_load_verified_audit(db, receipt) -> AuditEvent | None` — the ORIGINAL `receipts.verified` event for `entity_id=<receipt.id>` (read-only; the reversal's source of truth, decision #3). Raises `ReversalError(409, ...)` when missing (defensive; should not exist for verified receipts).
- `_restore_balance(db, org, invoice, verified_event) -> Decimal` — `new = q(balance_now + delta)`; `status='issued'` when `new > 0`; quantize `ROUND_HALF_UP`; returns restored balance.
- `_void_available_wallet(db, org, receipt) -> Decimal` — delegate to `wallet.void_wallet_credits_for_receipt`; returns voided amount (decision #5).
- `_apply_fraud_flag_if_added(db, org, receipt, verified_event, reversal_kind, admin_user)` — when `verified_event.payload['trusted_payer_action']=='added'` and receipt has a sender: `fraud_flags.flag_sender_fraud(...)` + audit `receipts.fraud_flagged` (decision #6).
- `_record_reversal_audit(db, *, org, receipt, verified_event, admin_user, reversal_kind, note, restored_balance, wallet_voided)` — writes `receipts.undo` or `receipts.reversed` with the FULL NB-18 field set: `invoice_number`, `reference_number`, `sender_name`, `amount_etb` (original), `balance_before_etb` (balance at moment of reversal = pre-restoration balance), `decision` ('undo'|'reversed'), `credit_delta_etb` (negative, stringified), `note`, `reversal_status`, `restored_balance_etb`, `wallet_voided_etb`, `original_verified_event_id`.
- `_mark_receipt(db, receipt, kind, note, admin_user)` — set the four reversal columns.
- `_relock(db, org)` — `lifecycle.refresh_workspace_state(db, org, now)` (decision #4).

**`undo.py`** (~110 lines; imports `core` + models): `undo_verification(db, admin_user, receipt_id, note=None) -> PaymentReceipt` — guards: receipt exists (404), `status=='verified'` (409 otherwise), `reversal_status IS NULL` (409, one reversal per receipt), `now <= decided_at + 24h` (409 "Undo window closed — use Reverse" — SERVER guard, decision #7); then `_load_verified_audit` → `_restore_balance` → `_void_available_wallet` → `_apply_fraud_flag_if_added` → `_mark_receipt('undo', note, admin_user)` → `_record_reversal_audit` → `_relock`. NO Notification row, NO SMS (NB-19.3).

**`reverse.py`** (~170 lines; imports `core` + models + `Notification`): `reverse_verification(db, admin_user, receipt_id, reason) -> PaymentReceipt` — guards: receipt exists (404), `status=='verified'` (409), `reversal_status IS NULL` (409), `now > decided_at + 24h` (409 "Use Undo within 24 hours" — Reverse is the after-24h path), **`reason` stripped non-empty else 422** (NB-20.2); then restore/void/flag/mark/reverse-audit exactly as undo, then write the Notification row with the EXACT NB-20.3 copy (decision #8; amount/date/invoice from the verified audit payload + reason). NO SMS, NO refund execution (NB-20.5).

**`fraud_flags.py`** (~70 lines; imports models + audit): `normalize` reused from `services.billing.trusted_payers.normalize_sender`; `is_fraud_flagged(db, org_id, sender_name) -> bool`; `flag_sender_fraud(db, org, sender_name, admin_user) -> SenderFraudFlag` (upsert: exists → `reversal_count += 1`; else insert with `fraud_risk_since = now`; audit `receipts.fraud_flagged` with `{sender_name, reversal_count}`); `fraud_flag_read(db, org_id, sender_name) -> SenderFraudFlag | None` (for queue payload `fraud_risk_since`).

### 2.3 Endpoints — `apps/platform-api/app/api/endpoints/receipt_reversals.py` (NEW; router prefix `/receipts`; module docstring cites decisions #7/#9/#10)

Kept OUT of `receipts.py` to hold that file under the 400-line cap (260 existing + ~150 new would exceed). Route-order note: no conflicts — the existing receipts router has no `GET /{receipt_id}` route and no `/audit` or `/trusted-payers` static suffixes; still, register this router AFTER `receipts.router` in `router.py` and verify with the API tests.

- `GET /receipts/audit` — admin `require_org_roles(OWNER, ADMIN)` → `list[VerifiedReceiptAuditRead]`: all `status=='verified'` receipts ordered `decided_at DESC`, each with `reversal_availability` (decision #7). Backed by a new `list_verified` read in `receipts/queue.py`.
- `GET /receipts/{receipt_id}/audit-events` — admin gate → `list[ReceiptAuditEventRead]`: AuditEvent rows for `entity_type='payment_receipt', entity_id=<id>` (newest first), each with `available_actions: ['undo'] | ['reverse'] | []` computed server-side ONLY for the `receipts.verified` event when `reversal_status IS NULL` (NB-19.1: the Undo/Reverse actions live ON the verification's audit record).
- `POST /receipts/{receipt_id}/undo` — admin gate; `UndoRequest {note: str | None (max 512)}` → `ReversalRead`. All guards in `undo.undo_verification`; `ReversalError → HTTPException`.
- `POST /receipts/{receipt_id}/reverse` — admin gate; `ReverseRequest {reason: str (1..512, non-blank)}` → `ReversalRead`. Guards in `reverse.reverse_verification`.
- `DELETE /receipts/trusted-payers/{sender_name}` — admin gate → `{removed: bool}`. Calls `trusted_payers.remove_trusted_payer(db, org, sender_name, admin_user)` — org resolved from the RECEIPT context is not available here, so: org = admin membership org is WRONG (trusted payer lists are per-org of the RECEIPT's workspace). Decision: the removal endpoint requires the org context — use `GET /receipts/audit` rows (which carry `organization_id`) and accept `organization_id` as a query param on the DELETE (admin-visible, system-wide admin surface — consistent with the system-wide queue). Missing row → 404. Audit `receipts.trusted_payer_removed`. **Fraud flag NOT cleared** (decision #6).

### 2.4 Schemas — `apps/platform-api/app/schemas/receipts.py` (MODIFY — additive)

- `ReversalStatus(StrEnum)` — `UNDO='undo'`, `REVERSED='reversed'`.
- `UndoRequest` — `{note: str | None = Field(default=None, max_length=512)}`.
- `ReverseRequest` — `{reason: str = Field(min_length=1, max_length=512)}` + whitespace-only rejector (mirror `DisputeRequest`).
- `ReversalRead` — `{receipt_id, invoice_number, reference_number, amount_etb, reversal_status, reversal_note, reversed_at, restored_balance_etb, wallet_voided_etb, message: str | None}` (message populated on reverse with the NB-20.3 copy).
- `VerifiedReceiptAuditRead` — `{id, organization_id, organization_name, invoice_number, reference_number, amount_etb, sender_name, decided_at, reversal_status, undo_available, undo_available_until, reverse_available}`.
- `ReceiptAuditEventRead` — `{id, event_type, description, created_at, payload: dict|list|None, available_actions: list[str]}`.
- `ReceiptRead` (MODIFY) — add `reversal_status: ReversalStatus | None = None` (customer surface shows the reversed state; the banner carries the detail).
- `ReceiptQueueItemRead` (MODIFY) — add `sender_has_reversed_credit: bool = False` and `fraud_risk_since: datetime | None = None` (decision #6; surfaced on EVERY future queue item for that sender).

### 2.5 Tests — 5 new files + conftest additions (§10 names every function)

`test_reversal_models.py`, `test_reversal_undo.py`, `test_reversal_reverse.py`, `test_reversal_wallet_interplay.py`, `test_reversal_fraud_badge.py` (+ API-level coverage inside the topic files; smoke-test extension for the console).

## 3. Files to MODIFY

1. `apps/platform-api/app/models/__init__.py` — export `SenderFraudFlag`.
2. `apps/platform-api/app/models/payment_receipt.py` — 4 reversal columns + CheckConstraint (`reversal_status IN ('undo','reversed') OR reversal_status IS NULL`).
3. `apps/platform-api/app/models/wallet_credit.py` — widen status CheckConstraint to `IN ('available','applied','voided')`; add `voided_at` DateTime(tz) nullable.
4. `apps/platform-api/app/services/billing/wallet.py` — add `void_wallet_credits_for_receipt(db, org, receipt) -> Decimal` (available rows for the receipt → `'voided'` + `voided_at`; audit `wallet.voided` with `{receipt_id, amount_etb}`; returns voided total). No new imports (models only — cycle discipline preserved).
5. `apps/platform-api/app/services/billing/trusted_payers.py` — add `remove_trusted_payer(db, org, sender_name, admin_user) -> bool` (404 via `ReversalError`? NO — this module has no error type; return None for missing, the endpoint 404s; audit `receipts.trusted_payer_removed`). No new imports.
6. `apps/platform-api/app/services/billing/receipts/queue.py` — `list_verified(db) -> list[PaymentReceipt]` (verified, decided_at DESC); `queue_item_payload` gains `sender_has_reversed_credit` + `fraud_risk_since` via `reversals.fraud_flags` (one-directional: queue → fraud_flags; fraud_flags imports nothing from receipts — acyclic).
7. `apps/platform-api/app/services/billing/__init__.py` — re-export the `reversals` package.
8. `apps/platform-api/app/api/router.py` — register `receipt_reversals.router` AFTER `receipts.router`.
9. `apps/platform-api/app/core/config.py` — add `reversal_undo_window_hours: int = 24`.
10. `apps/platform-api/app/schemas/receipts.py` — §2.4.
11. Ops-console: `types/api.ts`, `services/receiptsApi.ts`, `hooks/queries.ts`, `pages/AdminReceiptsPage.tsx`, `pages/ReceiptsPage.tsx` (customer reversed-state display), `pages/workspaceSurfaces.smoke.test.tsx` (§9).
12. `docs/plans/phase1-cashflow-core.md`, `phase2-receipt-processing.md` — UNTOUCHED (immutable).
13. `apps/platform-api/app/services/billing/receipts/verdicts.py`, `intake.py`, `disputes.py`, `credits.py`, `sms.py`, `lifecycle.py`, `invoices.py` — UNTOUCHED (reversal runs on the existing verify artifacts; `render_verdict` already 409s non-pending/escalated receipts, which is the re-verification blocker).

## 4. Strict Import Map (DAG — models → schemas ↔ services → api; no cycles; services NEVER import `app.api`)

```
models.sender_fraud_flag                 → db.base, db.custom_types, models.common, sqlalchemy (no cross-model imports)
models.payment_receipt (MOD)             → + 4 columns (no new imports)
models.wallet_credit (MOD)               → + voided_at + widened CHECK (no new imports)
models.__init__ (MOD)                    → + sender_fraud_flag (top of DAG)
schemas.receipts (MOD)                   → pydantic only (standalone, unchanged rule)
services.billing.wallet (MOD)            → models + audit  (+void_wallet_credits_for_receipt)
services.billing.trusted_payers (MOD)    → models + audit  (+remove_trusted_payer)
services.billing.receipts.intake         → UNCHANGED (reversals imports ITS constants — one-way)
services.billing.reversals.fraud_flags   → models + audit + services.billing.trusted_payers.normalize_sender
services.billing.reversals.core          → models (PaymentReceipt, SubscriptionInvoice, WalletCredit, Notification, AuditEvent)
                                           + services.audit + services.billing.wallet
                                           + services.billing.lifecycle
                                           + services.billing.receipts.intake (NOTIFICATION_EXPIRY_DAYS)
                                           + reversals.fraud_flags
services.billing.reversals.undo          → reversals.core + models
services.billing.reversals.reverse       → reversals.core + models + models.notification
services.billing.receipts.queue (MOD)    → + reversals.fraud_flags (fraud_flags imports nothing from receipts → acyclic)
services.billing.__init__ (MOD)          → + reversals
api.endpoints.receipt_reversals (NEW)    → api.security.require_org_roles, db.session, models,
                                           schemas.receipts, services.billing.receipts.queue (list_verified),
                                           services.billing.reversals (undo/reverse/fraud_flags/availability),
                                           services.billing.trusted_payers (remove)
api.endpoints.receipts (MOD)             → UNCHANGED imports (no reversal imports — file stays under 400 lines)
api.router (MOD)                         → + api.endpoints.receipt_reversals
core.config (MOD)                        → + reversal_undo_window_hours
tests → models + services + conftest (shared fixtures only; NO imports from other test files)
```

Cycle proof: `reversals.* → intake` but `intake` imports nothing from `reversals`; `queue → fraud_flags → trusted_payers/audit` (leaf); `reversals.core → wallet/lifecycle` where `wallet` imports nothing billing-internal and `lifecycle → invoices → pricing/wallet` (Phase 1 chain unchanged). No new edge points back into `receipts/*` except the two constant imports from `intake` (leaf-imports, acyclic).

## 5. The reversal state machine (deterministic flow)

```
VERIFIED receipt (status='verified', reversal_status IS NULL, decided_at = T0)
│
├─ ADMIN reads GET /receipts/audit  → availability computed SERVER-side:
│    now <= T0 + 24h  → undo_available=True, reverse_available=False
│    now >  T0 + 24h  → undo_available=False, reverse_available=True
│    (exactly now == T0 + 24h  → undo (≤ boundary))
│    reversal_status set → neither (409 at the service, UI hides both)
│
├─ POST /receipts/{id}/undo   (admin OWNER/ADMIN; optional note)
│    guards: 404 receipt · 409 not verified · 409 already reversed · 409 past window (SERVER)
│    → load original receipts.verified audit (READ-ONLY source of truth)
│    → restored = q(balance_now + credit_delta); balance>0 → invoice status='issued'
│    → wallet: available rows for this receipt → 'voided' (+audit wallet.voided)
│    → if verified payload trusted_payer_action=='added': fraud_flags.flag_sender_fraud
│         (+audit receipts.fraud_flagged)
│    → receipt.reversal_status='undo', reversal_note, reversed_by, reversed_at
│    → audit receipts.undo (full NB-18 field set, credit_delta negative)
│    → NO Notification, NO SMS (NB-19.3)
│    → lifecycle.refresh_workspace_state → GRACE|HARD_LOCKED (read-only) (NB-19.2)
│
└─ POST /receipts/{id}/reverse (admin OWNER/ADMIN; MANDATORY reason)
    guards: 404 receipt · 409 not verified · 409 already reversed · 409 inside window
            · 422 blank reason (NB-20.2)
    → identical core steps with kind='reversed'
    → Notification kind='receipt_reversed', EXACT NB-20.3 copy, expires +3d (NB-20.3)
    → audit receipts.reversed (distinct record — NB-18.3/NB-20.4)
    → NO refund execution, NO wallet creation (NB-20.5); applied wallet rows untouched (decision #5)
    → lifecycle.refresh_workspace_state (NB-20.5 "workspace may be locked")

FRAUD BADGE (NB-21) — display-only, never gates:
  queue_item_payload → sender_has_reversed_credit = is_fraud_flagged(org, sender)
  rendered: "This sender has a reversed credit on file" chip on EVERY future queue item
  admin retains: verify normally / escalate / DELETE /receipts/trusted-payers/{sender}
  (list removal ≠ flag removal; flag persists indefinitely — decision #6)
```

## 6. Endpoint + schema surface summary

| Method | Path | Auth | Body | Returns |
|---|---|---|---|---|
| GET | `/receipts/audit` | OWNER/ADMIN | — | `list[VerifiedReceiptAuditRead]` |
| GET | `/receipts/{id}/audit-events` | OWNER/ADMIN | — | `list[ReceiptAuditEventRead]` (+ per-event `available_actions`) |
| POST | `/receipts/{id}/undo` | OWNER/ADMIN | `UndoRequest {note?}` | `ReversalRead` |
| POST | `/receipts/{id}/reverse` | OWNER/ADMIN | `ReverseRequest {reason}` | `ReversalRead` |
| DELETE | `/receipts/trusted-payers/{sender}` | OWNER/ADMIN | query `organization_id` | `{removed: bool}` |

All reversal endpoints are write-guard EXEMPT (same carve-out rationale as Phase 2 — servicing locked workspaces is the feature's purpose; documented in the module docstring).

## 7. Migration — `apps/platform-api/alembic/versions/20260806_0015_reversals_phase3.py` (down_revision `'20260806_0014'`)

1. `ALTER TABLE payment_receipts ADD COLUMN reversal_status VARCHAR(16) NULL`, `reversal_note VARCHAR(512) NULL`, `reversed_by_user_id UUID NULL` (FK `users.id` ON DELETE SET NULL), `reversed_at TIMESTAMP WITH TIME ZONE NULL`; `ADD CONSTRAINT ck_payment_receipt_reversal_status CHECK (reversal_status IN ('undo','reversed') OR reversal_status IS NULL)`.
2. `wallet_credits`: drop `ck_wallet_credit_status`, re-add `CHECK (status IN ('available','applied','voided'))`; `ADD COLUMN voided_at TIMESTAMP WITH TIME ZONE NULL`.
3. `CREATE TABLE sender_fraud_flags` (id UUID PK, organization_id UUID NOT NULL FK CASCADE, sender_name VARCHAR(128) NOT NULL, fraud_risk_since TIMESTAMPTZ NOT NULL, reversal_count INTEGER NOT NULL DEFAULT 1, created_at TIMESTAMPTZ NOT NULL; UNIQUE(organization_id, sender_name); INDEX(organization_id)).
4. No data backfill. Docstring must flag the sqlite quirk (constraint drop/add on sqlite may require batch mode; tests build via `Base.metadata.create_all` so the model CheckConstraints are authoritative — Phase 2 precedent).

## 8. Audit integration (Phase 1 `AuditEvent` pattern via `services.audit.record_audit_event`, reused unchanged)

New event types (all with actor, organization_id = RECEIPT's org, stringified Decimals):
- `receipts.undo` — FULL NB-18 field set (decision #3/#8): `{invoice_number, reference_number, sender_name, amount_etb, balance_before_etb (pre-restoration), decision: 'undo', credit_delta_etb (negative), note, reversal_status: 'undo', restored_balance_etb, wallet_voided_etb, original_verified_event_id}`.
- `receipts.reversed` — same field set, `decision: 'reversed'`, note = mandatory reason, `+ notification_sent: true`.
- `wallet.voided` — `{receipt_id, amount_etb, reversal_kind}`.
- `receipts.fraud_flagged` — `{sender_name, reversal_count, original_verified_event_id}`.
- `receipts.trusted_payer_removed` — `{sender_name}`.

**Immutability:** no new or existing code path writes to an existing AuditEvent row. The original `receipts.verified` event is read-only; the test map asserts its payload is byte-identical after undo/reverse and that a second event (not an update) was created.

## 9. Ops-console (Tailwind dark patterns; `apps/ops-console/src/`)

- **`types/api.ts` (MODIFY)** — `ReversalStatus = 'undo' | 'reversed'`; `UndoPayload`/`ReversePayload`; `VerifiedReceiptAudit` (with `undo_available`, `undo_available_until`, `reverse_available`); `ReceiptAuditEvent` (with `available_actions`); extend `Receipt` (+`reversal_status`), `ReceiptQueueItem` (+`sender_has_reversed_credit`, `fraud_risk_since`).
- **`services/receiptsApi.ts` (MODIFY)** — `listVerifiedAudit()`, `getReceiptAuditEvents(id)`, `undoReceipt(id, note?)`, `reverseReceipt(id, reason)`, `removeTrustedPayer(senderName, organizationId)`.
- **`hooks/queries.ts` (MODIFY)** — `useVerifiedAudit()`, `useReceiptAuditEvents(id)`, `useUndoReceipt()` / `useReverseReceipt()` mutations (invalidate `['receipts']`, `['receipts','queue']`, `['ops','audit-timeline']`).
- **`pages/AdminReceiptsPage.tsx` (MODIFY)** — (a) NEW "Verified & reversible" panel listing `useVerifiedAudit()` rows: per row, an "Undo" action button rendered ONLY when `undo_available` (hidden after 24h — NB-19.4, with the server as the real control) and a "Reverse" action when `reverse_available`; Reverse opens a modal with a mandatory reason textarea (submit disabled until non-blank); Undo opens a light confirm with optional note. (b) NEW queue-item chip: when `sender_has_reversed_credit` render `"This sender has a reversed credit on file"` (rose/violet, non-blocking, alongside NEW SENDER/CASH chips — NB-21.2/21.4). (c) In the detail panel, when the badge is present, a "Remove sender from trusted-payer list" button (calls `removeTrustedPayer`, confirms, refetches queue + audit). (d) Per-receipt audit-events drawer: `GET /receipts/{id}/audit-events` rendering each event with its `available_actions` as the Undo/Reverse affordance anchored ON the verification's audit record (NB-19.1/20.1).
- **`pages/ReceiptsPage.tsx` (MODIFY)** — receipt history cards render a "reversed" StatusBadge + the NB-20.3 message line when `reversal_status='reversed'` (the Notification row already delivers the banner copy on next login; the card is the persistent record).
- **`pages/workspaceSurfaces.smoke.test.tsx` (MODIFY)** — assert the admin reversals panel renders ("Verified & reversible") and the queue renders without the badge chip when no fraud flag is present.
- **`pages/DashboardPage.tsx` / `pages/AccountPage.tsx`** — NO code change required: the audit timelines automatically surface `receipts.undo`/`receipts.reversed` events (they are AuditEvents). Verified in smoke tests.

## 10. Sequencing (TDD order) and testing requirements

### 10.1 `tests/conftest.py` (MODIFY — additive)

- `verify_receipt(client, token, ref, *, amount='4520.00', sender='Mulugeta Tesfaye', trusted_payer_action='verified_once') -> (receipt_id, invoice)` helper composing upload → queue lookup → decision (mirrors the existing per-file helpers without importing them).
- `force_window(client, db_session, receipt_id, hours)` — rewind/advance `decided_at` directly on the row (and the verified audit event `created_at` where the payload copy is read) for deterministic window tests.
- `make_verified_with_surplus(...)` — verify with `amount > balance` (auto-forward) to produce an `available` WalletCredit row for wallet-interplay tests.

### 10.2 New test files (named functions)

**test_reversal_models.py:** `test_reversal_status_check_constraint`; `test_wallet_voided_status_allowed_and_voided_at`; `test_sender_fraud_flag_org_sender_unique`; `test_reversal_columns_nullable_by_default`.

**test_reversal_undo.py (NB-19):** `test_undo_within_24h_restores_balance_and_reopens_invoice` (status back to `issued`, balance = original `balance_before_etb`); `test_undo_no_customer_notification` (zero Notification rows for org — NB-19.3); `test_undo_creates_own_audit_record_and_leaves_original_untouched` (receipts.undo exists; original receipts.verified payload byte-identical — NB-18.3); `test_undo_at_exactly_24h_boundary_eligible` (now == decided_at + 24h → 200); `test_undo_after_24h_server_guarded_409` (now + 1s → 409 even if UI hid the button — decision #7); `test_undo_availability_flags_in_audit_payload` (undo_available False, reverse_available True past window); `test_undo_re_locks_workspace` (phase → hard_locked/grace after refresh — NB-19.2); `test_undo_on_non_verified_409`; `test_undo_twice_409` (one reversal per receipt); `test_undo_optional_note_persisted_in_audit`.

**test_reversal_reverse.py (NB-20):** `test_reverse_requires_reason_422_when_blank`; `test_reverse_after_24h_restores_balance_and_reopens`; `test_reverse_writes_exact_customer_message` (Notification row kind `receipt_reversed`, message equals the EXACT NB-20.3 copy with amount/date/invoice/reason interpolated — decision #8); `test_reverse_creates_distinct_audit_record` (receipts.reversed with decision 'reversed', mandatory note — NB-20.4); `test_reverse_no_automatic_refund` (no wallet row created, no SmsMessage row — NB-20.5); `test_reverse_inside_24h_409_forces_undo`; `test_reverse_twice_409`; `test_reverse_re_locks_workspace`.

**test_reversal_wallet_interplay.py (decision #5):** `test_undo_voids_available_wallet_credit` (row status 'voided', `voided_at` set, `available_wallet_credit` recomputes to 0, audit `wallet.voided`); `test_undo_does_not_claw_back_applied_wallet_credit` (applied row untouched, later invoice balance unchanged); `test_reverse_voids_available_wallet_credit`; `test_wallet_list_surfaces_voided_rows` (customer wallet view includes voided entries with status).

**test_reversal_fraud_badge.py (NB-21):** `test_reverse_of_verify_added_flags_sender`; `test_undo_of_verify_added_also_flags_sender` (decision #6 — badge on both mechanisms); `test_verify_without_added_never_flags`; `test_badge_surfaces_on_future_queue_item` (new upload same sender → `sender_has_reversed_credit=True`, `fraud_risk_since` set — NB-21.2); `test_badge_persists_across_uploads_and_orgs` (flag scoped per org; another org's identical sender unflagged); `test_badge_does_not_block_verification` (verify still 200 with badge — NB-21.4); `test_badge_survives_trusted_payer_removal` (DELETE trusted-payer → flag still surfaces on next receipt — NB-21.3/21.5); `test_remove_trusted_payer_endpoint_audits_and_404s_unknown`; `test_single_reversal_never_hard_blocks` (no status change, no gating).

**test_reversal_api.py:** `test_audit_list_admin_only_403_for_operator_viewer`; `test_audit_list_returns_availability`; `test_audit_events_per_receipt_with_actions`; `test_undo_endpoint_happy_path_and_commit`; `test_reverse_endpoint_happy_path_and_message`; `test_customer_receipt_shows_reversal_status` (ReceiptRead); `test_route_registration_no_conflicts` (both routers respond).

### 10.3 Sequencing

1. Models + migration + conftest → `test_reversal_models.py` (`alembic upgrade head` verified).
2. `fraud_flags.py` → `wallet.void_wallet_credits_for_receipt` → `core.py` (restore/void/flag/audit primitives).
3. `undo.py` + availability → `test_reversal_undo.py` (window boundary first).
4. `reverse.py` + notification → `test_reversal_reverse.py`.
5. Wallet interplay → `test_reversal_wallet_interplay.py`.
6. `trusted_payers.remove_trusted_payer` + badge wiring into `queue.queue_item_payload` → `test_reversal_fraud_badge.py`.
7. Schemas + endpoints + router → `test_reversal_api.py`.
8. Console: types → receiptsApi → hooks → AdminReceiptsPage panels/chips → ReceiptsPage reversed card → smoke test.
9. Full suite + `alembic upgrade head` + manual smoke: verify → undo (balance restored, locked, no banner) → verify again → reverse (banner with exact copy, badge on re-upload).

## 11. Explicit NON-GOALS (Phase 3 must NOT do)

- **NO SMS on undo or reverse** (NB-16: escalation is the only SMS state; decision #8).
- **NO automatic refund** (NB-20.5; DEFERRED-01 stays deferred — `credit_backward`/reversal record offline-refund intent in audit only).
- **NO hard-block from reversal** (NB-21.6 — badge is display-only, always).
- **NO mutation of original audit records** (NB-18.3 — reversals write new records; test-enforced).
- **NO re-reversal** (one reversal per receipt; no un-undo).
- **NO claw-back of applied wallet credits** (decision #5 — documented asymmetry).
- **NO change to the five-verdict enum, dedup index, queue filter, or grace/lock math.**
- **NO re-verification of a reversed receipt** (status stays `verified`; new upload is the recovery path).
- **NO customer-facing trusted-payer management** (NB-11 unchanged; the new DELETE is admin-only).
- **NO TECH-22 code** — human acceptance-gate only (§12).
- **NO new tables beyond `sender_fraud_flags`**; no object storage; no scheduler; no metering changes.

## 12. TECH-22 — HUMAN GAP: CBE + Dashen fee-schedule verification (NO CODE — acceptance-gate checklist)

TECH-22 (NB-22) is **not a build ticket**. It blocks **production launch** (not this branch's merge). Recorded here so @qa audits it as a gate and @scribe persists it in the ledger. Procedure (executed by @architect/user, documented by @scribe):

1. Fetch the CURRENT published fee schedules of Commercial Bank of Ethiopia (CBE) and Dashen Bank for transfers in the **5,000–50,000 ETB range**.
2. Coverage required (NB-22.2): same-bank intra-bank transfer fees; inter-bank RTGS transfer fees; flat fees AND percent fees on both the customer-side and receiver-side of the transfer.
3. Compute the verified fee upper bound per bank/type. Compare against the `±1,000 ETB` tolerance (`settings.wallet_auto_forward_tolerance_etb`):
   - Materially below 1,000 ETB → tighten the tolerance (reduces fraud surface; one-line setting change + NB-09 test updates, tracked as a follow-up ticket).
   - Exceeds 1,000 ETB → widen the tolerance (one-line setting change; otherwise legitimate payments are flagged for admin manual decision too often).
4. Document the findings in `docs/behaviors/cashflow-bank-transfer-receipt-verification.md` **§12 (Open verification items)** — replace the open item with the verified table + conclusion (NB-22.4).
5. QA sign-off on this checklist is a precondition for production launch; the phase's code work proceeds regardless.

## 13. Risks flagged against existing code (for @qa and @architect)

1. **`lifecycle.refresh_workspace_state` commits internally** (Phase 2 risk #1, same shape): undo/reverse must complete restore + void + flag + audit + notification FIRST, then call refresh so the single commit persists everything together. If any guard fails mid-flight, raise BEFORE touching balances. `undo_verification`/`reverse_verification` must be written commit-aware exactly like `render_verdict`.
2. **Restored-balance arithmetic must use the audit payload, not receipt fields**: `payment_receipt` does not store `balance_before`/`credit_delta` — only the `receipts.verified` event does. Reversal reads that event; if it is missing (defensive 409), a silent inconsistency exists and must NOT be papered over.
3. **Route ordering in `router.py`**: register `receipt_reversals` after `receipts`; the API tests include a no-conflict assertion (`/receipts/audit` must not be swallowed by any `{receipt_id}` pattern).
4. **`decided_at` tz-naive risk** (sqlite round-trips): normalize with the Phase 1 `_as_utc` pattern before window arithmetic; boundary test at exactly 24h protects this.
5. **Wallet `'voided'` affects `available_wallet_credit` and the customer wallet list** — verify `apply_available_wallet_credits` FIFO ignores voided rows (it filters `status=='available'`, so it does — test proves it).
6. **Fraud flag lookup cost**: `queue_item_payload` gains one indexed lookup per item (`sender_fraud_flags(organization_id, sender_name)`) — negligible at queue scale; no join needed.
7. **`DELETE /receipts/trusted-payers/{sender}` needs `organization_id`** — the queue is system-wide; never fall back to the admin's membership org (that would delete a row from the wrong org). 400 when the query param is absent.
8. **No `ReceiptVerdictError` reuse in `trusted_payers.py`** — keep that module's error surface unchanged (it returns None/raises nothing today); the endpoint maps missing-row → 404.
