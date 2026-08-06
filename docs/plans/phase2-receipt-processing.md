# BLUEPRINT: PHASE 2 — Receipt Processing: Upload, AI Extraction, Matching & Verification Queue (TECH-07..17 / NB-07..17)

Status: LOCKED for execution by @build on branch `feat/market-contender-v1`. Written by @plan. QA audits against this document AND the NB acceptance criteria in `docs/behaviors/pending-behaviors.md` (lines 71-175) AND `docs/behaviors/cashflow-bank-transfer-receipt-verification.md` (§6-10). Builds ON TOP of Phase 1 outputs (`services/billing/` package, models, migration `20260805_0013`). Phase 1 design is NOT re-opened; only the additive integration points listed in §4.6 are touched.

## 0. Goal

Make the bank-transfer receipt loop real: customers upload PNG/JPG/PDF receipts from any workspace state (including hard-locked), the system extracts 8 fields via the org's preferred BYOK key (or degrades to zero-confidence), dedups reference numbers system-wide, routes receipts to the oldest open invoice, and a human admin renders one of exactly five verdicts through a verification queue — with partials always crediting, ±1,000 ETB surplus rolling into a wallet ledger, escalations firing the only SMS (via a provider-agnostic outbox), and disputes converting rejections into escalation cases.

## 1. Ground-truth decisions (locked for @build; deviations require @architect sign-off)

1. **Write-guard exemption is a deliberate carve-out, not an omission.** Upload, dispute, queue-read, and verdict-render endpoints do NOT include `Depends(require_writable_workspace)`. They use `get_current_membership` (customer surfaces) or `require_org_roles(OWNER, ADMIN)` (admin surfaces) only. A hard-locked workspace MUST remain payable — that is the feature's purpose. Document this in the `receipts.py` endpoint module docstring.
2. **Uploads are accepted in ANY billing phase** (free/trial/limbo/grace/hard_locked/active). Routing to an open invoice is the only gate: no open invoice (no invoices, or all paid) → HTTP 400 `"You have no open invoice to apply this receipt to."` (Free orgs have no invoices → 400; acceptable and deterministic).
3. **"Open invoice" = `balance_remaining_etb > 0`** (Phase 1 uses `status='issued'` as the initial status; we do NOT add an 'open' status). Invoice `status` transitions `issued → paid` the moment balance reaches zero. `derive_phase` already keys off balance, so no Phase 1 change is needed for unlock evaluation — the unlock fires by running `lifecycle.refresh_workspace_state` inside the verify path (pessimistic: credits only happen on admin Verify).
4. **Pessimistic unlock everywhere.** No credit, no wallet movement, no phase change happens at upload. All of it happens in the admin verdict-render path (`render_verdict`).
5. **Dedup key = extracted reference number, matched against receipts with `status='verified'` SYSTEM-WIDE** (NB-14.2). Enforced twice: (a) at upload (hard-reject immediately when a verified receipt carries the same ref), and (b) as a database backstop — partial unique index on `payment_receipts(reference_number) WHERE status='verified'`; an IntegrityError on a second verify of the same ref → 409, admin forced to use `reject_duplicate`. Two pending receipts with the same ref are both visible in the queue; only one can ever verify.
6. **Receipt file bytes are stored in the database** (`file_data` LargeBinary, upload cap 5 MB). No object storage exists in the repo; DB blobs keep tests hermetic and let the admin queue re-display the receipt. Migration to object storage is out of scope.
7. **Extraction is provider-agnostic with a mock adapter in Phase 2.** The service resolves `org.preferred_ai_key_id` → active `ProviderApiKey` → decrypt via `security.decrypt_provider_key`, then dispatches to a provider adapter registry. Phase 2 ships ONE adapter: `mock` (deterministic, controlled by `settings.receipt_extraction_mode`, default `'mock'`). Real HTTP provider adapters are NON-GOAL (interface + key plumbing + fallback are real; the wire call is not). Missing key OR adapter error OR parse failure → zero-confidence `ExtractionResult` (all fields None, all confidence 0.0, `has_key=False`), which surfaces the NB-10.2 admin warning.
8. **Wallet credit reduces the NEXT invoice's `total_etb` (and `balance_remaining_etb`) at issuance, never `flat_amount_etb`.** The invoice carries a negative line item `kind='wallet_credit'` so the math stays legible: `total = flat + overage − applied_wallet`, floored at 0. Excess wallet (surplus credits exceeding the next total) stays `available` and rolls to the invoice after that (FIFO).
9. **`credit_backward` (NB-09.3b) records surplus for offline refund in the audit payload only.** No refund execution, no wallet row. `partial_ignore` (NB-09.3c) requires an explicit `partial_credit_amount_etb` ≤ min(receipt amount, invoice balance) supplied by the admin; surplus beyond it is ignored; balance stays open when the credited amount is below balance.
10. **CASH never auto-flows.** `is_cash_sender` overrides the trusted-payer pre-fill (NB-12.3) — pre-filled Verify is suppressed for CASH even when "cash" is on the trusted-payer list. Trusted-payer pre-fill and wrong-bank-within-portfolio pre-fill remain (NB-11.3, NB-13.1); the admin still clicks Verify (pessimistic).
11. **`reject_wrong_bank` is server-guarded to out-of-portfolio banks only.** Rendering `reject_wrong_bank` on a receipt whose bank is CBE or Dashen → 422 (NB-13.3/13.4). In practice such receipts cannot reach the queue (payments to a non-portfolio account would not land at FreightPilot), so the verdict is a safety valve, not a workflow.
12. **Escalation requires a mandatory admin note** — that note IS the escalation question shown in the customer banner (NB-16.2) and the only SMS-triggering state. SMS is never sent for any rejection or verification.
13. **SMS outbox only.** `enqueue_sms()` writes a `queued` row to `sms_messages`; a `_dispatch_sms()` stub raises `NotImplementedError` (gateway attaches later by polling `status='queued'`). Missing `organization.contact_phone` → row written with `status='failed'`, `error_message='no_phone_on_file'`; the in-product banner still fires (fail-soft). A new nullable `contact_phone` column on `organizations` is added by this phase's migration (no phone field exists today; no phone-capture UI in Phase 2 — flag for @architect).
14. **One dispute thread per receipt.** `dispute_threads.receipt_id` is UNIQUE. Repeat dispute cycles after a maintained rejection are a NON-GOAL.
15. **Money is `Decimal` / `Numeric(14,2)` end-to-end** with `ROUND_HALF_UP` quantization at every credit boundary, matching Phase 1 discipline.
16. **Customer notifications reuse the Phase 1 `Notification` model** (kind + payload + 3-day `expires_at`, dismiss-after-expiry semantics unchanged). New kinds: `receipt_verified`, `receipt_rejected`, `receipt_escalated`, `wallet_credit`, `dispute_resolved`. The upload confirmation (NB-07.4) is the HTTP response body text, not a notification row.

## 2. Files to CREATE

All paths relative to repo root unless noted. Backend under `apps/platform-api/app/`, tests under `apps/platform-api/tests/`, console under `apps/ops-console/src/`.

### 2.1 Models (6 new files under `apps/platform-api/app/models/`)

**`payment_receipt.py`** — `PaymentReceipt` (table `payment_receipts`). One row per uploaded file. Columns:
- `id` (UUIDTimestampMixin), `organization_id` FK `organizations.id` CASCADE, indexed, NOT NULL
- `invoice_id` FK `subscription_invoices.id` SET NULL, indexed, nullable — the primary routing target (oldest open invoice at upload); NULL for hard-rejected duplicates and unrouteable uploads (none reach the queue, so NULL is rare)
- `file_name` String(255), `content_type` String(64), `file_size_bytes` Integer, `file_data` LargeBinary NOT NULL, `file_sha256` String(64) NOT NULL
- `reference_number` String(64), indexed, nullable — dedup key (extracted)
- `amount_etb` Numeric(14,2) nullable, `sender_name` String(128) nullable, `sender_account_number` String(64) nullable, `receiver_account_number` String(64) nullable, `receiver_name` String(128) nullable, `transfer_date` Date nullable, `bank_code` String(16) nullable
- `status` String(24) NOT NULL default `'pending'` — CheckConstraint `status IN ('pending','verified','rejected','escalated')`
- `verdict` String(24) nullable — CheckConstraint `verdict IN ('verify','reject_wrong_bank','reject_duplicate','reject_illegible','escalate')`
- `rejection_reason` String(512) nullable, `admin_note` String(512) nullable
- `decision_made_by_user_id` FK `users.id` SET NULL nullable, `decided_at` DateTime(tz) nullable
- `trusted_payer_action` String(24) nullable — CheckConstraint `trusted_payer_action IN ('added','verified_once') OR trusted_payer_action IS NULL` (NB-11.5 persistence)
- `large_surplus_decision` String(24) nullable — CheckConstraint `large_surplus_decision IN ('credit_forward','credit_backward','partial_ignore') OR large_surplus_decision IS NULL`
- `partial_credit_amount_etb` Numeric(14,2) nullable (only for `partial_ignore`)
- `surplus_etb` Numeric(14,2) nullable — computed at queue-item build time
- Flags (all Boolean NOT NULL default False): `is_new_sender`, `is_cash_sender`, `is_wrong_bank_within_portfolio`, `is_large_surplus`, `is_duplicate`, `has_zero_confidence`; `low_confidence_fields` JSON nullable (list of field names)
- Indexes: `(organization_id, status)`; `(status, created_at)` for the queue; partial UNIQUE index `uq_payment_receipt_verified_ref` on `reference_number` WHERE `status='verified'` (postgresql_where + sqlite_where so `Base.metadata.create_all` in tests builds it)

**`receipt_extraction.py`** — `ReceiptExtraction` (table `receipt_extractions`), 1:1 with receipts (TECH-10). Columns: `id`, `receipt_id` FK `payment_receipts.id` CASCADE NOT NULL UNIQUE, `provider_name` String(64) nullable (None = zero-confidence fallback), `key_id` String(64) nullable, `model_name` String(64) nullable, `fields` JSON NOT NULL (8 keys), `confidence` JSON NOT NULL (same 8 keys, floats 0..1), `raw_response` JSON nullable, `error_message` String(512) nullable, `created_at`.

**`wallet_credit.py`** — `WalletCredit` (table `wallet_credits`) — the surplus ledger (TECH-09). Columns: `id`, `organization_id` FK CASCADE indexed NOT NULL, `receipt_id` FK `payment_receipts.id` RESTRICT NOT NULL (every credit traces to a verified receipt), `amount_etb` Numeric(14,2) NOT NULL CheckConstraint `amount_etb > 0`, `status` String(16) default `'available'` CheckConstraint `status IN ('available','applied')`, `applied_to_invoice_id` FK `subscription_invoices.id` SET NULL nullable, `applied_at` DateTime(tz) nullable, `created_at`. Index `(organization_id, status)`.

**`sms_message.py`** — `SmsMessage` (table `sms_messages`) — the outbox (TECH-16). Columns: `id`, `organization_id` FK CASCADE indexed NOT NULL, `receipt_id` FK `payment_receipts.id` SET NULL nullable (context), `to_phone` String(24) NOT NULL (snapshot), `body` String(200) NOT NULL (service enforces ≤160; column headroom), `status` String(16) default `'queued'` CheckConstraint `status IN ('queued','sent','failed')`, `provider_name` String(64) nullable, `gateway_message_id` String(128) nullable, `error_message` String(255) nullable, `created_at`, `sent_at` DateTime(tz) nullable.

**`trusted_payer.py`** — `TrustedPayer` (table `trusted_payers`) — per-org admin-only list (NB-11). Columns: `id`, `organization_id` FK CASCADE indexed NOT NULL, `sender_name` String(128) NOT NULL (stored normalized: casefold + strip + collapse whitespace), `added_by_user_id` FK `users.id` SET NULL nullable, `created_at`. UniqueConstraint `(organization_id, sender_name)`.

**`dispute_thread.py`** — `DisputeThread` (table `dispute_threads`) — rejection→escalation conversion (NB-17). Columns: `id`, `receipt_id` FK `payment_receipts.id` CASCADE NOT NULL UNIQUE, `organization_id` FK CASCADE indexed NOT NULL, `dispute_text` String(1000) NOT NULL, `submitted_by_user_id` FK `users.id` SET NULL nullable, `status` String(16) default `'open'` CheckConstraint `status IN ('open','resolved')`, `resolution` String(24) nullable CheckConstraint `resolution IN ('verify','maintain_rejection')`, `resolved_by_user_id` FK `users.id` SET NULL nullable, `created_at`, `resolved_at` DateTime(tz) nullable.

**`app/models/__init__.py` (MODIFY)** — import/export the 6 new models (top of DAG preserved).

**`app/models/organization.py` (MODIFY)** — add `contact_phone` String(24) nullable.

### 2.2 Services — extend `apps/platform-api/app/services/billing/` (5 new modules + `__init__.py`; every module stays ≤400 lines)

**`wallet.py`** (~110 lines; imports models + audit only — NO lifecycle/invoices import, breaking the potential import cycle): `create_wallet_credit(db, org, receipt, amount_etb) -> WalletCredit`; `available_wallet_credit(db, org) -> Decimal`; `apply_available_wallet_credits(db, org, invoice, total_etb) -> tuple[Decimal, Decimal]` (returns applied amount and remaining available; marks rows `applied`/`applied_at` FIFO by created_at; floors at total); `_wallet_notification(db, org, amount_etb)` builder (kind `wallet_credit`, message "Wallet balance: +X ETB applies to next invoice.").

**`receipt_extraction.py`** (~160 lines; imports models, security, audit): `EXTRACTION_FIELDS` tuple of the exact 8 keys (`sender_name`, `sender_account_number`, `receiver_account_number`, `receiver_name`, `transfer_amount`, `transfer_date`, `reference_number`, `bank_identifier`); `LOW_CONFIDENCE_THRESHOLD = 0.60`; `ExtractionResult` dataclass (fields dict, confidence dict, provider_name, key_id, model_name, has_key bool, error str|None); `resolve_extraction_key(db, org) -> ProviderApiKey | None` (preferred_ai_key_id → active, decrypt-on-use); `extract_receipt(db, org, receipt, content_bytes, user) -> ExtractionResult` — orchestrates key resolution, adapter dispatch, zero-confidence fallback, `ReceiptExtraction` row persistence, audit `receipts.extraction_completed`; `_extract_with_provider(provider_name, api_key, content_bytes) -> dict` — adapter registry dispatch, raises `ProviderAdapterError` for unknown providers; `_MOCK_ADAPTER` — deterministic extraction controlled by `settings.receipt_extraction_mode` (mock mode parses a JSON sidecar in the upload form field `mock_extraction` when present, else returns empty → zero confidence; used ONLY in dev/test).

**`credits.py`** (~200 lines; imports models, wallet, lifecycle, audit): `classify_surplus(amount_etb, balance_etb) -> str` — pure: `'exact'` (equal), `'partial'` (less), `'auto_forward'` (balance < amount ≤ balance + 1,000), `'large_surplus'` (amount > balance + 1,000); `apply_credit(db, org, receipt, decision, *, partial_amount, admin_user) -> CreditOutcome` — the credit-application core (§5); `_credit_invoice(db, org, invoice, amount_etb)` — mutate `balance_remaining_etb` (quantize ROUND_HALF_UP), set `status='paid'` at zero; `_cascade_surplus(db, org, amount_etb, first_invoice)` — deterministic cascade across next-oldest open invoices (NB-07.3); `unlock_evaluation(db, org, now)` — calls `lifecycle.refresh_workspace_state` after credits (decision #4).

**`trusted_payers.py`** (~60 lines; imports model + audit): `normalize_sender(name) -> str`; `is_trusted(db, org_id, sender_name) -> bool`; `add_trusted_payer(db, org, sender_name, admin_user)` (Idempotent; audit `receipts.trusted_payer_added`).

**`sms.py`** (~80 lines; imports models + audit): `ESCALATION_SMS_TEMPLATE = 'Hi {name}, FreightPilot has a question about your recent receipt. Please log in to your workspace to respond.'` (assert ≤160 chars at call time; name fallback → org name); `enqueue_sms(db, *, organization_id, to_phone, body, receipt_id=None) -> SmsMessage` (writes `queued`; calls `_dispatch_sms` which raises `NotImplementedError` and is swallowed — row stays `queued`); `send_escalation_sms(db, org, receipt) -> SmsMessage | None` (resolves `org.contact_phone`; missing → `failed` row with `no_phone_on_file`; audit `sms.enqueued` with status + phone).

**`receipts.py`** (~350 lines; imports models, schemas.receipts, audit, and the billing submodules above — NEVER app.api): the orchestrator. Public functions: `upload_receipt(db, org, *, file_name, content_type, file_bytes, user, mock_extraction=None) -> PaymentReceipt` (format/size validation, sha256, persist, run extraction via `receipt_extraction.extract_receipt`, then `_dedup_and_route`); `_dedup_and_route(db, org, receipt, extraction)` — system-wide dedup against `status='verified'` references → hard reject (status `rejected`, verdict `reject_duplicate`, `is_duplicate=True`, fraud-flag audit pair, `receipt_rejected` notification with NB-14.3 copy, NO queue item), else route via `_oldest_open_invoice` (missing → 400 at the endpoint layer) and set `invoice_id`; `_compute_flags(db, receipt, invoice)` — sets the 6 booleans + `low_confidence_fields` + `surplus_etb`; `recommended_verdict(db, receipt, invoice) -> str | None` (trusted payer OR wrong-bank-within-portfolio → `'verify'`; CASH → None per decision #10); `list_customer_receipts(db, org)`; `list_queue(db) -> list[PaymentReceipt]` (status IN pending/escalated, oldest first, join org); `get_queue_item(db, receipt_id)`; `render_verdict(db, admin_user, receipt_id, verdict_request) -> PaymentReceipt` — the state machine (§5): validations (escalate→note required, reject_wrong_bank→422 in-portfolio, large surplus→3-way required, partial_ignore→amount required), then dispatch to `credits.apply_credit` on verify, or rejection/escalation handling, audit record per §8, notifications, SMS on escalate only; `submit_dispute(db, user, receipt_id, text) -> DisputeThread` (receipt must be org's + `rejected`; converts to `escalated`; audit `receipts.dispute_submitted`); `resolve_dispute(db, admin_user, receipt_id, decision) -> PaymentReceipt` (verify → credit path + thread `verify`/resolved + `receipt_verified` banner; maintain → thread `maintain_rejection`/resolved + `dispute_resolved` banner); `list_wallet(db, org)`.

**`services/billing/__init__.py` (MODIFY)** — re-export the 5 new modules' public functions.

### 2.3 Schemas — `apps/platform-api/app/schemas/receipts.py` (new)

- `ReceiptStatus(StrEnum)` pending/verified/rejected/escalated; `Verdict(StrEnum)` verify/reject_wrong_bank/reject_duplicate/reject_illegible/escalate; `TrustedPayerAction(StrEnum)` added/verified_once; `LargeSurplusDecision(StrEnum)` credit_forward/credit_backward/partial_ignore
- `ReceiptUploadResponse` — `{message: str, receipt_id: str}` (message exactly: "Receipt received — verification typically takes ≤24 hours.")
- `ReceiptRead` (customer surface — NO admin internals): id, status, verdict, invoice_number, reference_number, amount_etb, sender_name, bank_code, rejection_reason, created_at, decided_at
- `ReceiptQueueItemRead` (admin surface): id, organization_id, organization_name, invoice_number, designated_bank_code, status, verdict, extracted fields (8 key/value pairs), per-field confidence, low_confidence_fields, all 6 flags, has_zero_confidence warning text, recommended_verdict, surplus_etb, large_surplus_decision, partial_credit_amount_etb, trusted_payer_action, admin_note, dispute_text, dispute_status, file meta (file_name/content_type/file_size_bytes), created_at
- `VerdictRequest` — `{verdict: Verdict, note: str | None, admin_note: str | None, trusted_payer_action: TrustedPayerAction | None, large_surplus_decision: LargeSurplusDecision | None, partial_credit_amount_etb: Decimal | None}` with server-side cross-field validation per decision #12/#9
- `DisputeRequest` — `{text: str}` (1..1000 chars)
- `WalletCreditRead` — `{amount_etb, status, applied_to_invoice_number, created_at}`; `WalletRead` — `{available_etb: Decimal, credits: list[WalletCreditRead]}`

### 2.4 Endpoints — `apps/platform-api/app/api/endpoints/receipts.py` (new; prefix `/receipts`; module docstring states the write-guard exemption rationale)

- `POST /receipts/upload` — customer, `Depends(get_current_membership)`, multipart `file` (UploadFile) + optional `mock_extraction` form field (dev/test only, gated by `settings.receipt_extraction_mode == 'mock'`). Validates: extension ∈ {png,jpg,jpeg,pdf} AND content-type image/png|image/jpeg|application/pdf → else 400 `"Unsupported file format."`; size ≤ `settings.receipt_max_size_bytes` → else 400 `"Receipt too large — maximum 5 MB."`; calls `lifecycle.refresh_workspace_state` FIRST (materializes any lazily-issued invoice so routing sees it), then `receipts.upload_receipt`; open-invoice missing → 400. Response `ReceiptUploadResponse`. EXEMPT from write guard. No `require_roles` (any membership may pay).
- `GET /receipts` — customer; list own receipts newest-first; EXEMPT from write guard (must be viewable while locked). → `list[ReceiptRead]`
- `GET /receipts/wallet` — customer; available balance + credit history; EXEMPT. → `WalletRead`
- `POST /receipts/{receipt_id}/dispute` — customer; `DisputeRequest`; EXEMPT. 404 if not org's; 409 if not `rejected` or a thread exists. → `ReceiptRead`
- `GET /receipts/queue` — admin, `Depends(require_org_roles(OrganizationRole.OWNER, OrganizationRole.ADMIN))`; EXEMPT from write guard. → `list[ReceiptQueueItemRead]`
- `GET /receipts/queue/{receipt_id}` — admin gate; → `ReceiptQueueItemRead`
- `POST /receipts/{receipt_id}/decision` — admin gate; `VerdictRequest`; EXEMPT. Applies `receipts.render_verdict` (or `resolve_dispute` when an open thread exists). → `ReceiptRead` (customer view is fine for the console refresh)
- `POST /receipts/{receipt_id}/decision` with `verdict=verify` when the receipt is a resolved-dispute target routes through `resolve_dispute` semantics — same endpoint, one entry point.

**`apps/platform-api/app/api/router.py` (MODIFY)** — register `receipts.router` at prefix `/receipts`.

### 2.5 Migration — `apps/platform-api/alembic/versions/20260806_0014_receipt_processing_phase2.py` (down_revision `'20260805_0013'`)

- Create `payment_receipts`, `receipt_extractions`, `wallet_credits`, `trusted_payers`, `sms_messages`, `dispute_threads` with columns/constraints/indexes per §2.1 (partial unique index with both `postgresql_where` and `sqlite_where`; if the bundled sqlite version rejects partial indexes during `alembic upgrade head` on sqlite, keep the index Postgres-only and rely on the service-layer backstop — flag in the migration docstring).
- `ALTER TABLE organizations ADD contact_phone VARCHAR(24) NULL`.
- No data backfill.

### 2.6 Ops-console (minimal-but-real; Tailwind dark patterns; `apps/ops-console/src/`)

- **`services/receiptsApi.ts` (CREATE)** — `uploadReceipt(file: File, mockExtraction?: object)`, `listReceipts()`, `getWallet()`, `listReceiptQueue()`, `getReceiptQueueItem(id)`, `renderDecision(id, payload)`, `submitDispute(id, text)` against `/receipts/*`.
- **`types/api.ts` (MODIFY)** — add `ReceiptStatus`, `Verdict`, `TrustedPayerAction`, `LargeSurplusDecision`, `Receipt`, `ReceiptQueueItem`, `ExtractedField`, `WalletCredit`, `WalletSummary` types.
- **`pages/ReceiptsPage.tsx` (CREATE)** — customer surface: PageHeader + upload Panel (file input `accept=".png,.jpg,.jpeg,.pdf"`, submit → status message "Receipt received — verification typically takes ≤24 hours."), wallet Panel ("Wallet balance: +X ETB applies to next invoice."), receipt history list with StatusBadge; rejection cards render the rejection banner copy + "Re-upload" button (re-opens upload) + "Dispute this decision" textarea + submit (NB-17.1); verified cards show invoice paid + wallet line; escalated cards show the escalation question banner (no response box in Phase 2 — decision #14 note). Accessible to all roles incl. locked workspaces.
- **`pages/AdminReceiptsPage.tsx` (CREATE)** — queue list (pending + escalated, oldest first) with flag chips: `NEW SENDER` (prominent, rose), `Cash deposit — confirm with customer that this was their intended transfer.` (double-flag styling), `Wrong-bank-within-portfolio` (info, pre-fill note), `Large surplus — admin manual decision required` (+ surplus ETB), `No AI provider key set on this organization — extraction will be returned at zero confidence; admin must manually read the receipt.`, per-field `low confidence — please manually verify` chips, `Customer disputes rejection` + dispute text when a thread exists. Detail panel: extracted 8 fields w/ confidence bars, file preview (blob URL from `file_data` — endpoint must return file bytes: add `GET /receipts/queue/{receipt_id}/file` returning `Response` with media type, admin-gated; add this endpoint to §2.4), verdict action row (Verify + add to trusted-payer list / Verify, do not add / Reject — wrong bank / Reject — duplicate / Reject — illegible / Escalate with mandatory note), large-surplus 3-way select + partial amount input, optional admin note. Pre-filled Verify rendered when `recommended_verdict='verify'`.
- **`pages/AdminReceiptsPage.tsx` → verdict buttons map 1:1 to the `Verdict` enum** (NB-15.1); no amount-mismatch button exists.
- **`hooks/queries.ts` (MODIFY)** — `useReceipts()`, `useReceiptQueue()`, `useWallet()`, `useRenderDecision()` mutation, `useSubmitDispute()` mutation.
- **`components/Layout.tsx` (MODIFY)** — add nav entries: `{ to: '/receipts', label: 'Payments', code: 'PY', hint: 'Receipts and wallet' }` and `{ to: '/admin/receipts', label: 'Verification Queue', code: 'VQ', hint: 'Receipt verdicts' }`.
- **`App.tsx` (MODIFY)** — routes: `/receipts` (all roles), `/admin/receipts` (`allowedRoles={['admin','owner']}`).

### 2.7 Tests (10 new files + conftest additions; named functions in §9)

`test_receipt_models.py`, `test_receipt_extraction.py`, `test_receipt_upload_api.py`, `test_receipt_routing.py`, `test_receipt_credit_apply.py`, `test_receipt_admin_queue.py`, `test_receipt_dedup_fraud.py`, `test_receipt_escalation_sms.py`, `test_receipt_dispute.py`, `test_receipt_audit.py`.

## 3. Strict Import Map (models → schemas ↔ services → api; no cycles)

- New model files import ONLY `app.db.base`, `app.db.custom_types`, `app.models.common`, sqlalchemy (FKs by string). No cross-model imports.
- `app.models.__init__` imports all models (top of DAG).
- `schemas.receipts` imports only pydantic (+ `schemas.auth` if a role enum is needed — it is not; keep it standalone).
- `services.billing.wallet` → models + `services.audit`. (No lifecycle/invoices import — cycle-breaker.)
- `services.billing.receipt_extraction` → models + `services.audit` + `services.security.decrypt_provider_key`. NO billing-internal imports.
- `services.billing.trusted_payers` → models + `services.audit`.
- `services.billing.sms` → models + `services.audit`.
- `services.billing.credits` → models + `services.billing.wallet` + `services.billing.lifecycle` + `services.audit`. (Credits → lifecycle → invoices → wallet: acyclic.)
- `services.billing.receipts` → models + `schemas.receipts` + `services.audit` + all four billing modules above (`receipt_extraction`, `credits`, `trusted_payers`, `sms`) + `services.billing.lifecycle` (for the pre-routing refresh). **services.billing never imports app.api** (Phase 1 rule preserved).
- `services.billing.__init__` → the 9 modules (4 Phase 1 + 5 Phase 2).
- `api.endpoints.receipts` → `api.security.get_current_membership` + `require_org_roles`, `db.session`, models, `schemas.receipts`, `services.billing.receipts` + `lifecycle`. Deliberately NOT importing `require_writable_workspace`.
- `api.router` → + `api.endpoints.receipts`.
- `core.config` → + `receipt_extraction_mode: str = 'mock'`, `receipt_max_size_bytes: int = 5 * 1024 * 1024`, `wallet_auto_forward_tolerance_etb: Decimal = Decimal('1000.00')`, `sms_brand_name: str = 'FreightPilot'`.
- `billing/invoices.py` (MODIFY) → + `services.billing.wallet` (for `apply_available_wallet_credits`). Wallet imports nothing from invoices — cycle broken at `wallet`.
- Tests → models + services + `conftest`; new shared fixtures in `conftest.py` (§9.1) — do NOT import helpers from `test_billing_api.py`.

## 4. Files to MODIFY (summary)

1. `app/models/__init__.py` — export 6 new models.
2. `app/models/organization.py` — `contact_phone` column.
3. `app/services/billing/__init__.py` — export new modules.
4. `app/services/billing/invoices.py` — wallet-credit integration (§4.6).
5. `app/schemas/billing.py` — UNTOUCHED (receipt schemas are standalone).
6. `app/api/router.py` — register receipts router.
7. `app/core/config.py` — 4 new settings (above).
8. `tests/conftest.py` — new fixtures (§9.1).
9. Ops-console: `types/api.ts`, `hooks/queries.ts`, `components/Layout.tsx`, `App.tsx`.
10. `docs/plans/phase1-cashflow-core.md` — UNTOUCHED (immutable).

### 4.1-4.5 (inline above in §2)

### 4.6 The wallet-credit integration point into Phase 1 (`invoices.py` — the ONLY Phase 1 service touched)

- `_issue_invoice(db, org, tier, period_start, period_end, overage, ordinal, now, wallet_credit_etb: Decimal = Decimal('0.00'))` — new keyword param, default 0 (backward compatible; `issue_first_invoice` never passes it). After composing flat + overage lines: `total = flat + overage − wallet_credit_etb` (floored at 0 via `max(Decimal('0.00'), ...)`); when `wallet_credit_etb > 0`, append line item `kind='wallet_credit'`, description `'Wallet credit applied'`, quantity None, `unit_price_etb=None`, `amount_etb=-wallet_credit_etb`; set `total_etb` and `balance_remaining_etb` from the floored total. The `billing.invoice_issued` audit payload gains `wallet_credit_etb`.
- `issue_next_invoice(db, org, now)` — before calling `_issue_invoice`, compute `available = wallet.available_wallet_credit(db, org)`; pass `min(available, flat + overage)` as `wallet_credit_etb`; call `wallet.apply_available_wallet_credits(db, org, invoice, total)` AFTER the invoice flush (marks rows applied FIFO, sets `applied_to_invoice_id`/`applied_at`; returns remaining for the audit payload).
- `lifecycle.py`, `locks.py`, `pricing.py`, `try_issue_invoice`, `issue_first_invoice` — UNTOUCHED. Unlock evaluation reuses `lifecycle.refresh_workspace_state` unchanged (it already derives ACTIVE from `balance_remaining_etb == 0`).

## 5. The credit-application state machine (deterministic flow)

```
UPLOAD (POST /receipts/upload, any phase, write-guard-exempt)
 ├─ format ∈ {png,jpg,jpeg,pdf} + content-type + ≤5MB          else 400 (NB-07.5)
 ├─ lifecycle.refresh_workspace_state(db, org, now)            (materialize lazy invoices)
 ├─ persist PaymentReceipt(status='pending', file_data, sha256)
 ├─ EXTRACTION (receipt_extraction.extract_receipt)
 │    ├─ key = resolve(org.preferred_ai_key_id) → active ProviderApiKey → decrypt
 │    ├─ key missing / adapter error / parse fail → zero-confidence result
 │    │    └─ flags.has_zero_confidence = True (NB-10.2 warning text)
 │    └─ mock/provider adapter → 8 fields + per-field confidence
 │         └─ confidence < 0.60 → low_confidence_fields += field (NB-10.4)
 ├─ DEDUP (NB-14): ref non-empty AND ref ∈ verified receipts SYSTEM-WIDE
 │    ├─ YES → status='rejected', verdict='reject_duplicate', is_duplicate=True
 │    │     ├─ audit pair: receipts.duplicate_attempt (new) + receipts.duplicate_flagged (original)
 │    │     └─ Notification kind='receipt_rejected', payload ref+reason (NB-14.3 copy)
 │    │     └─ NO queue item, NO SMS, NO routing. End.
 │    └─ NO  → continue
 ├─ ROUTING (NB-07.2): oldest open invoice (balance>0, period_start asc) → invoice_id
 │    ├─ none → 400 "You have no open invoice to apply this receipt to."
 │    └─ set invoice_id (primary target); cascade computed at verify time
 └─ FLAGS (computed, persisted): is_new_sender (not in trusted_payers), is_cash_sender
      (sender casefold == 'cash'), is_wrong_bank_within_portfolio (bank ∈ {cbe,dashen}
      AND ≠ designated), is_large_surplus (amount > balance + 1000), surplus_etb,
      low_confidence_fields, has_zero_confidence
      └─ recommended_verdict: trusted payer OR wrong-bank-within-portfolio → 'verify';
         CASH → None (NB-12.3 overrides even if trusted)
      └─ → QUEUE (status='pending')

ADMIN VERDICT (POST /receipts/{id}/decision — owner/admin, write-guard-exempt)
 ├─ open dispute thread exists? → resolve_dispute path (verify | maintain_rejection) ↓
 ├─ verdict = escalate → REQUIRE note (422 if absent) (NB-16.1, decision #12)
 │    ├─ status='escalated'; audit receipts.escalated (note = question)
 │    ├─ Notification kind='receipt_escalated' (question) (NB-16.2a)
 │    ├─ send_escalation_sms → sms_messages 'queued' (NB-16.2b; ≤160 chars; only SMS state)
 │    │    └─ no contact_phone → row 'failed' no_phone_on_file; banner still fires
 │    └─ no credit; phase unchanged (locked stays locked) (NB-16.5). End.
 ├─ verdict = reject_wrong_bank → bank must be OUT of portfolio else 422 (NB-13.3/4)
 ├─ verdict = reject_duplicate → fraud-flag audit pair; banner (NB-14.3 copy)
 ├─ verdict = reject_illegible → banner "We couldn't read your receipt clearly.
 │    Please re-upload a clearer copy."
 ├─ (all rejects) → status='rejected', rejection_reason; Notification kind='receipt_rejected'
 │    (+ re-upload button data in payload); NO SMS (NB-15.4). End.
 └─ verdict = verify → CREDIT APPLICATION (credits.apply_credit) — the only credit path:
      invoice = receipt.invoice_id; balance = invoice.balance_remaining_etb
      A) amount ≤ balance                      (partial | exact — NB-08.1)
           credit = amount; balance -= credit; 0 → status='paid'
           surplus = 0; no wallet row
      B) balance < amount ≤ balance + 1,000    (auto-forward — NB-09.2)
           credit = balance → paid; surplus = amount − balance
           → WalletCredit(available) + Notification 'wallet_credit' (NB-09.2 copy)
      C) amount > balance + 1,000              (large surplus — NB-09.3) → NO auto-credit
           REQUIRED large_surplus_decision (422 if missing):
           C1 credit_forward : full credit → paid; WalletCredit(surplus) + wallet banner
           C2 credit_backward: full credit → paid; surplus in AUDIT payload only
                              (offline refund; no wallet row) (decision #9)
           C3 partial_ignore : REQUIRED partial_credit_amount_etb
                               (0 < amt ≤ min(amount, balance)); credit amt;
                               surplus ignored; balance>0 → stays open (NB-09.3c)
      (wrong-bank-within-portfolio → same math; the pre-fill is UX only — NB-13.1)
      SURPLUS CASCADE (NB-07.3): if the receipt amount exceeded the primary invoice
      balance and any credit remains unapplied after B/C (only reachable via C3 with
      amt==balance... none; cascade is structural for MULTI-RECEIPT/multi-invoice
      scenarios — defined as: after crediting the primary invoice, remaining credited
      excess flows to next-oldest open invoice, same tolerance rules, recursively).
      → trusted_payer_action: 'added' → TrustedPayer row + audit; 'verified_once' → none
      → audit receipts.verified with §9.1 field set (balance_before, credit_delta, ...)
      → Notification 'receipt_verified' (+ wallet line when applicable)
      → unlock_evaluation: lifecycle.refresh_workspace_state (balance==0 → ACTIVE) (NB-08.5)

DISPUTE (POST /receipts/{id}/dispute — customer, write-guard-exempt)
 └─ receipt.status == 'rejected' AND no existing thread       else 404/409
      → DisputeThread(open, text); receipt.status='escalated'
      → queue shows "Customer disputes rejection" + text (NB-17.2)
      → workspace unchanged (read-only until resolved) (NB-17.3)
      → admin renders final decision via /decision:
           verify            → credit path A/B/C + thread(resolution='verify', resolved)
                               + 'receipt_verified' banner (NB-17.4)
           any rejection     → thread(resolution='maintain_rejection', resolved)
                               + 'dispute_resolved' banner; stays rejected
```

## 6. The admin verification queue API (surface summary)

| Method | Path | Auth gate | Write guard | Body | Returns |
|---|---|---|---|---|---|
| POST | `/receipts/upload` | membership | EXEMPT | multipart file (+ mock_extraction in mock mode) | `ReceiptUploadResponse` |
| GET | `/receipts` | membership | EXEMPT | — | `list[ReceiptRead]` |
| GET | `/receipts/wallet` | membership | EXEMPT | — | `WalletRead` |
| POST | `/receipts/{id}/dispute` | membership | EXEMPT | `DisputeRequest` | `ReceiptRead` |
| GET | `/receipts/queue` | OWNER/ADMIN | EXEMPT | — | `list[ReceiptQueueItemRead]` |
| GET | `/receipts/queue/{id}` | OWNER/ADMIN | EXEMPT | — | `ReceiptQueueItemRead` |
| GET | `/receipts/queue/{id}/file` | OWNER/ADMIN | EXEMPT | — | raw file bytes (media type) |
| POST | `/receipts/{id}/decision` | OWNER/ADMIN | EXEMPT | `VerdictRequest` | `ReceiptRead` |

Queue content: `status IN ('pending','escalated')`, oldest first, org name joined. Pre-filled Verify (`recommended_verdict='verify'`) for trusted payers (NB-11.3) and wrong-bank-within-portfolio (NB-13.1); suppressed for CASH (NB-12.3). Flags rendered per §2.6. The 3-way large-surplus decision (C1/C2/C3) is a required field on the verify request when `is_large_surplus` (NB-09.3).

## 7. Extraction service design (TECH-10)

- Interface: `extract_receipt(db, org, receipt, content_bytes, user) -> ExtractionResult` where `ExtractionResult` carries `fields` (exactly the 8 keys from `EXTRACTION_FIELDS`), `confidence` (same keys, float 0..1), provider/key/model metadata, `has_key`, `error`.
- BYOK resolution: `org.preferred_ai_key_id` → `ProviderApiKey` (must be org's + `status='active'`) → decrypt via `security.decrypt_provider_key` at dispatch time only; key material never persisted outside the existing `encrypted_key` column.
- Provider-agnostic dispatch: adapter registry keyed by `provider_name`; `_extract_with_provider` raises `ProviderAdapterError` for unregistered providers → zero-confidence fallback. Phase 2 ships only the `mock` adapter (deterministic; `settings.receipt_extraction_mode`). Real adapters = NON-GOAL.
- Zero-confidence fallback: no key / adapter failure / malformed output → all fields None, all confidence 0.0, `has_key=False`, `error_message` set; queue flag `has_zero_confidence` + NB-10.2 warning string; admin reads the receipt image manually (the file is served by `/receipts/queue/{id}/file`).
- Persistence + audit: one `ReceiptExtraction` row per upload (1:1); audit `receipts.extraction_completed` with provider, key_id, per-field confidence summary, error (NB-10.5).
- Threshold: `LOW_CONFIDENCE_THRESHOLD = 0.60` module constant (configurable per NB-10.4); fields below it land in `low_confidence_fields` and render "low confidence — please manually verify."

## 8. Audit integration (Phase 1 `AuditEvent` pattern — `services.audit.record_audit_event`, reused unchanged)

Event types written by Phase 2 (all with `actor` = acting user, `organization_id`, structured payload):
- `receipts.uploaded` — file meta, sha256, routed invoice number (or none)
- `receipts.extraction_completed` — provider, key_id, confidence summary, error
- `receipts.duplicate_attempt` + `receipts.duplicate_flagged` — the NB-14.4 fraud-flag PAIR (attempt carries original receipt id; flagged event attaches to the original receipt's entity_id)
- `receipts.verified` — full §9.1 field set: invoice number, reference number, sender name, amount, balance BEFORE, decision, credit delta, note, trusted_payer_action, wallet_credit amount, large_surplus_decision
- `receipts.rejected` — verdict, reference, reason
- `receipts.escalated` — escalation note (the question)
- `receipts.dispute_submitted` — text
- `receipts.dispute_resolved` — resolution (verify / maintain_rejection)
- `receipts.trusted_payer_added` — normalized sender name
- `sms.enqueued` — to_phone (masked), status (queued/failed), receipt context
- `billing.invoice_issued` (Phase 1, MODIFIED payload) — gains `wallet_credit_etb` (decision #8)

Reversals/undo (TECH-19/20) are Phase 3 — Phase 2 writes append-only records only.

## 9. Sequencing (TDD order) and testing requirements

### 9.1 `tests/conftest.py` (MODIFY — additive only, no Phase 1 fixture changes)

- `sample_receipt_bytes()` — small valid PNG bytes constant; `bad_format_bytes()` (e.g. `.txt`); `pdf_bytes()` minimal.
- `make_paid_org_with_open_invoice(db, *, tier='starter', balance_etb=4520, invoice_number='INV-000100')` — reuses the `_signup/_upgrade/_force_trial_ended/_inject_invoice` recipe currently local to `test_billing_api.py` (replicated, NOT imported) → returns (org, invoice).
- `upload_receipt(client, token, *, filename='receipt.png', content=..., mock_extraction=None)` helper hitting the upload endpoint with multipart.
- `mock_extraction_payload(**overrides)` — canonical 8-field extraction dict for mock-mode tests.
- `make_admin_membership(db, org)` — owner-role membership for admin queue tests (the admin user fixture from Phase 1 conftest has no org membership by default).

### 9.2 New test files (named functions)

**test_receipt_models.py:** `test_payment_receipt_status_check_constraint`; `test_payment_receipt_verdict_check_constraint`; `test_verified_reference_partial_unique` (two verified rows same ref → IntegrityError; verified+pending coexist); `test_wallet_credit_positive_amount_check`; `test_trusted_payer_org_sender_unique`; `test_dispute_thread_one_per_receipt`; `test_sms_status_check_constraint`; `test_org_contact_phone_column`.

**test_receipt_extraction.py:** `test_no_key_returns_zero_confidence_and_flag`; `test_resolve_key_prefers_active_preferred_key`; `test_revoked_preferred_key_falls_back`; `test_mock_adapter_returns_eight_fields`; `test_extraction_persists_row_and_audits`; `test_low_confidence_fields_flagged_below_threshold`; `test_adapter_error_degrades_to_zero_confidence`; `test_extraction_never_fails_upload`.

**test_receipt_upload_api.py:** `test_upload_accepts_png_jpg_pdf`; `test_upload_rejects_txt_with_unsupported_format`; `test_upload_rejects_oversized_file`; `test_upload_confirmation_message_exact_copy`; `test_upload_ok_while_hard_locked` (exemption proof: org in hard_locked → 200, no 423); `test_upload_ok_during_grace`; `test_upload_no_open_invoice_returns_400`; `test_upload_free_org_returns_400`; `test_upload_routes_to_oldest_open_invoice` (two invoices, receipt routes to older); `test_upload_unauthenticated_401`.

**test_receipt_routing.py:** `test_surplus_cascade_computes_secondary_targets` (unit-level on `credits._cascade_surplus`); `test_multiple_receipts_per_invoice_accumulate`; `test_partial_receipt_never_routed_away`; `test_duplicate_upload_skips_routing_and_queue`.

**test_receipt_credit_apply.py:** `test_partial_credit_reduces_balance_invoice_stays_open`; `test_exact_credit_marks_invoice_paid`; `test_small_surplus_credits_balance_and_creates_wallet_credit`; `test_small_surplus_wallet_notification_copy`; `test_large_surplus_requires_admin_decision_422_without`; `test_large_surplus_credit_forward_closes_invoice_and_wallets`; `test_large_surplus_credit_backward_audits_no_wallet`; `test_large_surplus_partial_ignore_keeps_balance_open_when_under`; `test_verify_unlocks_workspace_via_refresh` (phase → ACTIVE after verify); `test_partial_verify_keeps_workspace_locked`; `test_wallet_credit_applied_to_next_invoice_at_issuance` (available 250 → next invoice total = flat − 250, negative wallet line, rows marked applied); `test_wallet_credit_exceeding_next_total_rolls_remainder`; `test_credit_amount_never_rejection_reason` (partial of any size verifies).

**test_receipt_admin_queue.py:** `test_queue_lists_pending_and_escalated_only`; `test_queue_gate_denies_operator_and_viewer` (403); `test_queue_item_renders_flags`; `test_new_sender_flag_when_not_trusted`; `test_trusted_payer_prefills_verify`; `test_cash_sender_double_flagged_even_when_trusted_and_no_prefill`; `test_wrong_bank_within_portfolio_prefills_verify`; `test_zero_confidence_warning_text`; `test_low_confidence_visual_flags_present`; `test_verify_add_trusted_payer_persists_and_audits`; `test_verify_do_not_add_leaves_list_unchanged`; `test_reject_wrong_bank_in_portfolio_422`; `test_reject_wrong_bank_out_of_portfolio_allowed`; `test_escalate_requires_note_422`; `test_verdict_enum_has_no_amount_mismatch`.

**test_receipt_dedup_fraud.py:** `test_duplicate_reference_across_organizations_hard_rejects`; `test_duplicate_reference_across_invoices_hard_rejects`; `test_duplicate_rejection_banner_copy_exact` (NB-14.3); `test_duplicate_fraud_flag_pair_in_audit`; `test_second_verify_same_ref_409_and_forced_duplicate_reject`; `test_duplicate_attempt_does_not_create_queue_item`.

**test_receipt_escalation_sms.py:** `test_escalate_enqueues_sms_row_queued`; `test_escalation_sms_body_under_160_chars`; `test_escalation_sms_no_receipt_specifics`; `test_rejection_never_enqueues_sms`; `test_verification_never_enqueues_sms`; `test_escalation_banner_with_question`; `test_missing_phone_fails_soft_queued_failed_row`; `test_escalation_keeps_workspace_locked`; `test_escalated_receipt_back_in_queue_for_final_decision`.

**test_receipt_dispute.py:** `test_dispute_only_on_rejected_receipt_409_otherwise`; `test_dispute_converts_rejection_to_escalation_with_label`; `test_dispute_thread_persists_text`; `test_workspace_stays_locked_during_dispute`; `test_dispute_resolution_verify_credits_and_unlocks`; `test_dispute_resolution_maintain_rejection_banner`; `test_second_dispute_on_same_receipt_409`.

**test_receipt_audit.py:** `test_verified_audit_carries_full_field_set` (§9.1 set); `test_rejected_audit_reason`; `test_escalation_audit_note`; `test_wallet_credit_audit_chain`; `test_audit_actor_is_admin_user`.

### 9.3 Sequencing

1. Models + migration + conftest additions → `test_receipt_models.py` (alembic upgrade head verified).
2. `wallet.py` → `credits.py` pure math → `test_receipt_credit_apply.py` (core cases first).
3. `receipt_extraction.py` → `test_receipt_extraction.py`.
4. `invoices.py` wallet integration → wallet-at-issuance tests in `test_receipt_credit_apply.py`.
5. `receipts.py` intake: upload → extraction wiring → dedup → routing → flags → `test_receipt_upload_api.py`, `test_receipt_routing.py`, `test_receipt_dedup_fraud.py`.
6. `trusted_payers.py` + queue orchestration + `render_verdict` credit paths → `test_receipt_admin_queue.py` (flags/prefill/verdict validation).
7. API surface: `schemas/receipts.py`, `endpoints/receipts.py`, router → API-level tests across the files above (endpoint assertions live in their topic files).
8. `sms.py` + escalation → `test_receipt_escalation_sms.py`.
9. Disputes → `test_receipt_dispute.py`.
10. Audit coverage → `test_receipt_audit.py`.
11. Console: types → receiptsApi → hooks → ReceiptsPage → AdminReceiptsPage → Layout nav → App routes → extend `workspaceSurfaces.smoke.test.tsx` (new surfaces render) + a small ReceiptsPage test if the file pattern supports it.
12. Full suite + `alembic upgrade head` + manual smoke (upload → queue → verify → unlock; upload while locked).

## 10. Explicit NON-GOALS (Phase 2 must NOT do)

- No undo / reverse / fraud-risk badge (TECH-18..21 — Phase 3). Audit records are append-only.
- No free-tier cap hard lock (TECH-31 — Phase 4).
- No real SMS gateway call — outbox only (`sms_messages` + `enqueue_sms`; dispatch stub raises).
- No real AI provider HTTP adapter — `mock` adapter + provider-agnostic interface + BYOK resolution + zero-confidence fallback only. Flagged for @architect (NB-10 extraction is "wired, not live").
- No escalation-response endpoint — escalated receipts stay in the queue until the admin re-renders a verdict (simplification of NB-16.2's "log in to respond").
- No repeat dispute cycles (one thread per receipt).
- No customer-visible trusted-payer management; no phone-capture UI (`contact_phone` is a data column only).
- No refund execution (credit_backward = audit-logged intent).
- No amount-mismatch verdict, ever.
- No object storage / file scanning / OCR choice — bytes live in the DB.
- No changes to product-web or desktop. No changes to Phase 1 lock semantics beyond the documented exemption. No scheduler. No changes to metering.

## 11. Risks flagged against Phase 1 code (for @qa and @architect)

1. **`lifecycle.refresh_workspace_state` commits internally.** The verify path must apply credits + wallet + audit + notifications + SMS FIRST, then call refresh (single transaction; refresh's commit persists everything together). If the partial-unique IntegrityError fires during credit application, roll back before refresh — otherwise a partially-credited state could commit. `render_verdict` must be written commit-aware.
2. **`derive_phase` keys off `balance_remaining_etb` only** — invoice `status` ('issued'/'paid') is cosmetic to the phase. Credits MUST set `status='paid'` for the admin/customer surfaces, but unlock correctness depends on balance; both must be updated atomically.
3. **`_issue_invoice` computes `total_etb` from lines** — adding a negative `wallet_credit` line changes the total; keep the floor at 0 and quantize; verify no assertion elsewhere assumes `total_etb ≥ flat_amount_etb`.
4. **Lazy issuance during uploads:** the upload handler calling `refresh_workspace_state` can newly ISSUE an invoice mid-flow (boundary crossing). That is intended (routing must see it) but means an upload can change billing phase before routing — order the calls deliberately (refresh → route).
5. **Partial unique index portability** — sqlite partial indexes depend on the bundled SQLite build. If `create_all`/`alembic` fails on sqlite, drop the index to Postgres-only and rely on the service-layer dedup + IntegrityError backstop (tests must then assert the service behavior, not the index).
6. **`audit.record_audit_event` sanitizes UUIDs in payloads** — receipt/payment amounts must be stringified (`str(Decimal)`) in payloads (Phase 1 convention) to keep JSON clean.
7. **Uploads must never 423.** Do not add `require_writable_workspace` to any receipts endpoint, and verify no router-level default dependency introduces it. Explicit regression test: `test_upload_ok_while_hard_locked`.
8. **Org-less / free-org edge:** upload on a free org returns 400 (no open invoice). The console should surface the 400 copy gracefully; no queue pollution.
9. **`contact_phone` absent everywhere in existing data** — escalation SMS rows will be `failed` until phones exist; the banner is the primary channel. Decide with @architect whether a phone-capture admin field ships in Phase 3.
10. **Two pending receipts, same ref:** both queue; the second verify hits the unique index → 409 → admin must reject_duplicate. The queue UI must surface the 409 gracefully (button disabled state + message).
11. **Phase 1 test helpers are file-local** (`test_billing_api.py`) — Phase 2 conftest replicates the recipe rather than importing across test modules (test isolation); flag to @qa that duplicate helper code is deliberate.
12. **`invoices.py` grows** with the wallet param — keep the change additive (default-arg) so `issue_first_invoice` and `try_issue_invoice` behavior is bit-identical for Phase 1 tests.
13. **`settings` defaults:** `receipt_extraction_mode='mock'` must be overridable per environment; never default to live provider calls.
14. **graphify is not installed** (Phase 1 risk #1 still open) — AST mapping in this blueprint was done via Read/Grep; install graphify before Phase 3 and run `graphify update .` after Phase 2 merges.
