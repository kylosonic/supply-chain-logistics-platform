# BLUEPRINT: PHASE 7 — Production-Readiness R0 (PROD-01..05)

## Status

| Field | Value |
|---|---|
| Document | Phase 7 — Production-Readiness R0 (PROD-01..05) |
| Branch | `feat/production-readiness-r0` (from `master` @ `34bf4a5`) |
| Base state | Uncommitted CORS hotfix (see §Commit Plan) + untracked `docs/production-readiness-plan.md`, `docs/competitor-research-fourkites-project44.md` |
| Date | 2026-08-06 |
| Status | 🔒 LOCKED — @build executes exactly this; @qa audits against §QA-Audit-Against |
| Migrations | **NONE** (confirmed, §Migrations) |

## Goal

Make the platform-api production-operable for R0: bake sample-data into the API image (PROD-01), wire a real OpenAI-compatible receipt-extraction adapter with a production mode guard (PROD-02), wire a provider-agnostic SMS gateway adapter plus contact-phone capture (PROD-03), and enforce production config guardrails for collection accounts and secrets (PROD-04/05) — all with hermetic regression tests and zero schema changes.

## Adjudications (locked decisions)

1. **PROD-01 test strategy:** BOTH (a) static packaging tests asserting the Dockerfile COPY lines + the 5 CSVs present in the build context, AND (b) one behavioral hermetic test that chdirs to a temp dir **outside the repo** and seeds purely from `settings.sample_data_dir`. (a) directly pins the regression that shipped; (b) proves the runtime path is settings-driven and cannot fall back to repo-root walk-up. The repo-root walk-up is a dev convenience; the container must resolve via the settings path alone.
2. **PROD-02 path:** **(a) — a generic OpenAI-compatible chat-completions adapter**, keyed on `provider_name == 'openai'` (the ops-console BYOK form already defaults to provider `openai`), reading `receipt_extraction_model` + `receipt_extraction_base_url`; `mock` remains dev/test-only; production config validation forces mode ∈ {`real`, `zero_confidence`}. Rationale: an OpenAI-compatible endpoint is the most portable wire contract (works with OpenAI, Groq, Together, local vLLM/Ollama-compatible gateways), the BYOK plumbing is already real (decrypt at dispatch), and the zero-confidence admin-queue workflow already exists as the deliberate fallback — so both halves of PROD-B become first-class.
3. **PROD-03 gateway:** **provider-agnostic generic REST SMS adapter** — POST JSON `{to, sender, text, brand}` to a configurable `sms_gateway_url` with `Authorization: Bearer <api_key>`. Rationale: Ethiopian providers (and global aggregators) universally expose a simple POST-JSON send API; hard-coding a single vendor couples us to an unverified provider; the adapter contract is documented so a vendor adapter can be dropped in later. Outbox semantics kept (row lifecycle queued → sent/failed), fail-soft preserved (never raises into the escalation decision path).
4. **CORS hotfix ordering:** commit the hotfix **FIRST as `fix(cors)`**, then PROD work on top — NOT folded into PROD-06. Rationale: (i) it is a standalone, already-tested fix (`test_cors_config.py`, 5 tests); (ii) PROD-05 config-guard tests construct `Settings(_env_file=None)` and depend on the corrected defaults — folding the default change into PROD-05 would blur config-change history; (iii) PROD-06 is out of R0 scope and deferring the fix risks it being forgotten.
5. **Contact-phone endpoint role guard:** `require_org_roles(OWNER, ADMIN)` **without** `require_writable_workspace` — the escalation phone must be settable while the workspace is in limbo/grace (that is exactly when escalation SMS matters). Documented in the endpoint docstring.

## Commit plan (atomic, @build only, after @qa approval of each batch)

1. `fix(cors): product-web signup origins in default CORS allow-list` — the uncommitted hotfix files: `apps/platform-api/app/core/config.py` (cors_origins defaults), `.env.example`, `apps/platform-api/.env.example`, `docker-compose.yml` (CORS_ORIGINS default), `apps/platform-api/tests/test_cors_config.py`.
2. `docs: add production-readiness plan and competitor research baseline` — untracked `docs/production-readiness-plan.md`, `docs/competitor-research-fourkites-project44.md`.
3. `feat(prod): PROD-01 — bake sample-data into API image` (git mv of the 5 CSVs; Dockerfile; compose env; doc path updates; packaging tests).
4. `feat(prod): PROD-02 — OpenAI-compatible extraction adapter + production mode guard` (config fields + property, adapter registry branch, pyproject httpx move, tests).
5. `feat(prod): PROD-03 — SMS gateway adapter + contact-phone capture` (config fields, sms.py dispatch, schema + endpoint + SubscriptionRead, ops-console UI, tests).
6. `feat(prod): PROD-04 — CBE/Dashen production config guardrails` (config properties + env examples + tests).
7. `feat(prod): PROD-05 — production secrets guardrails` (provider-key-encryption property, security.py binding, env examples, compose default, tests).

## Files to Modify / Create

| # | File | Action | Line budget | Reason |
|---|---|---|---|---|
| 1 | `sample-data/` (repo root, 5 CSVs) | MOVE → `apps/platform-api/sample-data/` via `git mv` | — | Build context is `./apps/platform-api`; root CSVs are unreachable by COPY |
| 2 | `apps/platform-api/Dockerfile` | MODIFY | ≤ 60 | COPY sample-data in builder + runtime stages |
| 3 | `docker-compose.yml` (repo root) | MODIFY | ≤ 85 | `SAMPLE_DATA_DIR` env default; hotfix already touched CORS default here |
| 4 | `apps/platform-api/app/core/config.py` | MODIFY | ≤ 135 | New fields + 6 `effective_*` guard properties |
| 5 | `apps/platform-api/app/services/billing/receipt_extraction.py` | MODIFY | ≤ 320 | Adapter registry branch + OpenAI-compatible adapter + zero-confidence mode |
| 6 | `apps/platform-api/app/services/billing/sms.py` | MODIFY | ≤ 195 | Real dispatch, fail-soft, `mask_phone` public, gateway seam |
| 7 | `apps/platform-api/app/services/security.py` | MODIFY | ≤ 105 | Fernet seed via `effective_provider_key_encryption_secret` |
| 8 | `apps/platform-api/app/services/billing/lifecycle.py` | MODIFY | ≤ 325 | `contact_phone` in `_subscription_read` |
| 9 | `apps/platform-api/app/schemas/subscription.py` | MODIFY | ≤ 115 | `UpdateContactPhoneRequest` + `SubscriptionRead.contact_phone` |
| 10 | `apps/platform-api/app/api/endpoints/subscriptions.py` | MODIFY | ≤ 395 | `POST /subscriptions/me/contact-phone` |
| 11 | `apps/platform-api/pyproject.toml` | MODIFY | ≤ 65 | Move `httpx` dev → core deps |
| 12 | `apps/platform-api/app/services/activation/seeding.py` | MODIFY | ≤ 370 | Docstring only (repo-root-relative wording) |
| 13 | `apps/ops-console/src/types/api.ts` | MODIFY | ≤ 215 | `CurrentSubscription.contact_phone` |
| 14 | `apps/ops-console/src/services/billingApi.ts` | MODIFY | ≤ 90 | `updateContactPhone()` |
| 15 | `apps/ops-console/src/pages/AccountPage.tsx` | MODIFY | ≤ 500 (existing 432; +≤60 additive) | Phone capture field + save |
| 16 | `apps/ops-console/src/pages/workspaceSurfaces.smoke.test.tsx` | MODIFY | ≤ existing +15 | Smoke assert phone field renders |
| 17 | `.env.example` (root) | MODIFY | ≤ 22 | New vars (PROD-04/05 placeholders) |
| 18 | `apps/platform-api/.env.example` | MODIFY | ≤ 16 | New vars; fix encryption-secret length |
| 19 | `README.md`, `PROJECT_RECREATION_PROMPT.md` | MODIFY | n/a | `sample-data` path references |
| 20 | `apps/platform-api/tests/test_prod_sample_data_packaging.py` | CREATE | ≤ 160 | PROD-01 |
| 21 | `apps/platform-api/tests/test_receipt_extraction_production.py` | CREATE | ≤ 200 | PROD-02 |
| 22 | `apps/platform-api/tests/test_sms_gateway.py` | CREATE | ≤ 140 | PROD-03 backend |
| 23 | `apps/platform-api/tests/test_contact_phone_api.py` | CREATE | ≤ 180 | PROD-03 API |
| 24 | `apps/platform-api/tests/test_config_guards.py` | CREATE | ≤ 200 | PROD-02/04/05 guards |

Unchanged (verified compatible): `tests/conftest.py` (seed_csv_path walk-up finds `apps/platform-api/sample-data` one level up; CSV_HEADERS/helpers untouched), `apps/platform-api/scripts/seed_data.py` (walk-up still resolves), `.dockerignore` (does not exclude `sample-data`), `app/models/sms_message.py` (has `status` incl. `sent`, `provider_name`, `gateway_message_id`, `error_message`, `sent_at`), `app/models/organization.py` (`contact_phone` exists).

## Strict Import Map

- **config.py (leaf — pydantic only):** adds `receipt_extraction_base_url: str = 'https://api.openai.com/v1'`, `receipt_extraction_model: str = 'gpt-4o-mini'`, `sms_gateway_url: str = ''`, `sms_gateway_api_key: str = ''`, `sms_sender_name: str = 'FreightPilot'`; adds properties `effective_receipt_extraction_mode`, `effective_cbe_account_holder`, `effective_cbe_account_number`, `effective_dashen_account_holder`, `effective_dashen_account_number`, `effective_provider_key_encryption_secret`. Existing fields/validators/effective_database_url/effective_jwt_secret_key preserved verbatim.
- **receipt_extraction.py (MODIFY):** adds stdlib `base64` and `httpx` imports only. New module-level: `_openai_compatible_adapter(content_bytes, api_key) -> dict`, `_post_chat_completion(url, api_key, payload) -> dict` (test seam), `_sniff_mime(content_bytes) -> str`. `_extract_with_provider` gains `provider_name == 'openai'` branch. `extract_receipt` reads `settings.effective_receipt_extraction_mode`. `_mock_adapter` untouched. DAG: `services.billing.receipt_extraction → models(4), core.config, services.audit, services.security` (acyclic, no `app.api`).
- **sms.py (MODIFY):** adds `from datetime import UTC, datetime` and `import httpx`; renames `_mask_phone` → public `mask_phone` (one call-site update at the `sms.enqueued` audit payload). New module-level seam `_post_to_gateway(payload) -> None`. `enqueue_sms` drops the `try/except NotImplementedError` and calls `_dispatch_sms(row)` directly (new contract: `_dispatch_sms` NEVER raises). DAG: `services.billing.sms → models(3), core.config, services.audit`.
- **security.py (MODIFY):** `_provider_key_fernet` seed line changes from `settings.provider_key_encryption_secret` to `settings.effective_provider_key_encryption_secret` (binds the PROD-05 guard; dev/test fallback to JWT secret preserved). No new imports.
- **schemas/subscription.py (MODIFY):** `UpdateContactPhoneRequest(contact_phone: str)` with `field_validator` (strip; remove spaces/dashes/parens; must match `^\+?\d{9,15}$` else `ValueError`; return normalized digits with optional leading `+`); `contact_phone: str | None = None` added to `SubscriptionRead`. Pydantic only.
- **lifecycle.py (MODIFY):** `_subscription_read` adds `contact_phone=org.contact_phone`. No new imports.
- **subscriptions.py (MODIFY):** imports `UpdateContactPhoneRequest` + `from app.services.billing.sms import mask_phone`. Endpoint `POST /me/contact-phone` mirrors `select_tier` dependency stack: `require_org_roles(OWNER, ADMIN)`; loads org via `db.get`; persists `org.contact_phone`; `record_audit_event(event_type='organization.contact_phone_updated', payload={'contact_phone': mask_phone(phone)})`; returns `lifecycle.subscription_read(db, organization)`. DAG: endpoints→services only; acyclic.
- **ops-console:** `types/api.ts` — `CurrentSubscription` gains `contact_phone: string | null`. `billingApi.ts` — `updateContactPhone(contact_phone): Promise<CurrentSubscription>` POSTs `/subscriptions/me/contact-phone`. `AccountPage.tsx` — `useState<string>('')` for `contactPhone`, initialized from `subscription.contact_phone ?? ''`; handler `onSaveContactPhone` calls `updateContactPhone` then `refresh()`; UI: one Panel section ("Escalation contact") with existing `fieldClassName` input + gradient save button + `statusMessage` feedback, placed above the AI provider panel. No new components/routes.

## Env / Settings additions (with defaults)

| Var (Settings field) | Default | Notes |
|---|---|---|
| `RECEIPT_EXTRACTION_BASE_URL` (`receipt_extraction_base_url`) | `https://api.openai.com/v1` | chat-completions base; adapter appends `/chat/completions` |
| `RECEIPT_EXTRACTION_MODEL` (`receipt_extraction_model`) | `gpt-4o-mini` | configurable per deployment/provider |
| `SMS_GATEWAY_URL` (`sms_gateway_url`) | `''` (empty) | empty = gateway not configured → row stays `queued` (dev/test parity) |
| `SMS_GATEWAY_API_KEY` (`sms_gateway_api_key`) | `''` | empty → not configured |
| `SMS_SENDER_NAME` (`sms_sender_name`) | `FreightPilot` | gateway "sender" field; `sms_brand_name` retained for audit payload |
| `SAMPLE_DATA_DIR` (`sample_data_dir`) | `sample-data` | unchanged; now resolves to `/app/sample-data` in the image; compose default `${SAMPLE_DATA_DIR:-sample-data}` |
| `CBE_ACCOUNT_HOLDER` / `CBE_ACCOUNT_NUMBER` / `DASHEN_ACCOUNT_HOLDER` / `DASHEN_ACCOUNT_NUMBER` | `''` (dev) | new guard properties; env.example placeholders added |
| `PROVIDER_KEY_ENCRYPTION_SECRET` | `''` (dev) | new guard ≥32 chars in production; both `.env.example` files + compose default updated to ≥32-char placeholders |

## Step-by-Step Execution (for @build)

**PROD-01 — sample-data baked into the image**
1. `git mv` the five CSVs (warehouses.csv, items.csv, fleet_assets.csv, inventory.csv, orders.csv) from repo-root `sample-data/` to `apps/platform-api/sample-data/`. Do NOT alter CSV contents or headers (phase-4 header contract is load-bearing).
2. Dockerfile builder stage: after `COPY scripts ./scripts`, add `COPY sample-data ./sample-data`. Runtime stage: after `COPY --from=builder /app/pyproject.toml ./`, add `COPY --from=builder /app/sample-data ./sample-data`. Runtime CWD is `/app`, so `Path('sample-data')` resolves directly.
3. Repo-root `docker-compose.yml`: add `SAMPLE_DATA_DIR: ${SAMPLE_DATA_DIR:-sample-data}` to the backend service environment.
4. Update path references: root `README.md` (three `sample-data` mentions), `PROJECT_RECREATION_PROMPT.md` (tree entry), seeding.py module docstring ("repo-root-relative" → "build-image-relative via settings.sample_data_dir").
5. Verify by reading: `scripts/seed_data.py` walk-up and `tests/conftest.py::seed_csv_path` walk-up both still resolve one level up.
6. Create `tests/test_prod_sample_data_packaging.py`.

**PROD-02 — OpenAI-compatible extraction adapter**
7. config.py: two new fields + `effective_receipt_extraction_mode` property: in non-dev environments raw mode must be one of `real` or `zero_confidence` (anything else — including `mock` — raises `ValueError`); in dev/test returns the raw value (default `mock`). When mode is `real`, the base URL must start with `http://` or `https://`.
8. receipt_extraction.py: registry branch for `openai`; adapter builds a chat-completions payload with model from settings, a system prompt demanding strict JSON of exactly the 8 `EXTRACTION_FIELDS` plus per-field confidence 0..1, and a user message containing the receipt as a base64 data URI (MIME sniffed from magic bytes: PNG/JPEG/PDF magic, else `application/octet-stream`); POST through `_post_chat_completion` seam with Bearer auth and 30s timeout; parse `choices[0].message.content` as JSON; take `model_name` from response `model`; any HTTP error, non-2xx, malformed JSON, or missing keys raises `ProviderAdapterError` (upstream zero-confidence fallback handles it). Never require `response_format` — tolerate endpoints without JSON-mode support.
9. `extract_receipt`: when `effective_receipt_extraction_mode == 'zero_confidence'`, still resolve the org key (for audit `has_key` truth) but skip the provider call entirely and produce `_empty_result(has_key=key is not None, error='zero_confidence_mode')`.
10. pyproject.toml: move `httpx>=0.27.0` from `[project.optional-dependencies].dev` to core `dependencies` (both adapters need it in the production image, which installs only core deps).

**PROD-03 — SMS gateway adapter + contact-phone capture**
11. config.py: three SMS fields.
12. sms.py: rename `_mask_phone` → `mask_phone` (public; one call site); rewrite `_dispatch_sms(row)`: unconfigured (no URL or no key) → return immediately, row stays `queued`; configured → build payload `{to: row.to_phone, sender: settings.sms_sender_name, text: row.body, brand: settings.sms_brand_name}`, call `_post_to_gateway`; on success set `status='sent'`, `provider_name='generic_http'`, `sent_at=now(UTC)`; if the gateway JSON response contains an `id`, store it in `gateway_message_id`; on ANY exception set `status='failed'`, `error_message` (truncated ≤ 200 chars) — never re-raise. Implement `_post_to_gateway` with httpx POST, Bearer auth, 15s timeout, raise on non-2xx. Flush the row so `enqueue_sms` callers observe the final status.
13. schemas/subscription.py: `UpdateContactPhoneRequest` with the normalization validator; `contact_phone` on `SubscriptionRead`.
14. lifecycle.py: include `contact_phone` in `_subscription_read`.
15. subscriptions.py: `POST /me/contact-phone` per §Import Map (roles OWNER/ADMIN only — adjudication #5; document "escalation contact must be settable while locked" in the docstring). Return the refreshed `SubscriptionRead`.
16. ops-console: types/api.ts field, billingApi.ts function, AccountPage.tsx field + save handler + status feedback, smoke-test assertion.

**PROD-04 — CBE/Dashen guardrails**
17. config.py: four `effective_*` properties — in non-dev, empty holder/number raises `ValueError` (`'CBE_ACCOUNT_HOLDER is required in non-dev environments'` etc.); dev/test return the raw value. Mirror the JWT guard message style. (The invoice rendering source is the DB `collection_accounts` rows seeded by migration 20260805_0013 — which reads these settings at seed time; the guard makes blank account numbers impossible in production config.)
18. Add placeholder rows to both `.env.example` files.

**PROD-05 — secrets guardrails**
19. config.py: `effective_provider_key_encryption_secret` — in non-dev, empty or `< 32` chars raises `ValueError`; dev/test return raw (empty allowed — legacy Fernet fallback).
20. security.py: bind the guard — `_provider_key_fernet` seeds from the effective property.
21. Update `.env.example` files (root + platform-api) and the compose default so all secret placeholders are ≥32 chars.
22. Create `tests/test_config_guards.py`.

## Migrations

**NONE.** Confirmed: `organizations.contact_phone` added in Phase 2 (`20260806_0014_receipt_processing_phase2.py`); `sms_messages` already has `status` (check constraint includes `'sent'`), `provider_name`, `gateway_message_id`, `error_message`, `sent_at`; no new columns, tables, or constraints. Alembic dir untouched.

## Testing Requirements (every test named + acceptance criterion)

**tests/test_prod_sample_data_packaging.py (PROD-01, 5 tests):**
1. `test_dockerfile_builder_stage_copies_sample_data` — Dockerfile text contains a builder-stage `COPY sample-data` line.
2. `test_dockerfile_runtime_stage_copies_sample_data` — runtime stage contains `COPY --from=builder /app/sample-data`.
3. `test_build_context_contains_all_five_sample_csvs` — all 5 CSVs exist at `apps/platform-api/sample-data/` with the phase-4 header contract (parse each header line).
4. `test_seed_resolves_from_settings_dir_in_pristine_cwd` — monkeypatch CWD to an empty temp dir outside the repo; point `settings.sample_data_dir` at an absolute temp copy of the 5 CSVs; run `seed_workspace`; assert per-category rows > 0 AND the `workspace.seeded_sample_data` audit event fires (proves container-like resolution path — settings-only, no repo fallback).
5. `test_seed_raises_when_sample_dir_unresolvable` — chdir to an empty temp dir, leave `settings.sample_data_dir='sample-data'`; `seed_workspace` raises `FileNotFoundError` (negative control: the repo-root walk-up must NOT rescue a container-like environment).

**tests/test_receipt_extraction_production.py (PROD-02, 6 tests):**
1. `test_openai_adapter_normalizes_chat_completion_response` — monkeypatched `_post_chat_completion` returns a canned chat-completions response; dispatch with provider `openai` yields exactly the 8 fields, numeric confidence, and `model_name` from the response.
2. `test_openai_adapter_posts_to_configured_base_url` — recorded URL ends with `/chat/completions` and starts with `settings.receipt_extraction_base_url`.
3. `test_openai_adapter_error_degrades_to_zero_confidence` — seam raises; `extract_receipt` returns `_empty_result(has_key=True, error set)`, upload path still 200 (fail-soft preserved).
4. `test_real_mode_disables_mock_adapter` — mode `real`, provider `mock` → `ProviderAdapterError` (mock cannot leak into production mode).
5. `test_zero_confidence_mode_never_calls_provider` — mode `zero_confidence` with an active key; extraction returns empty fields and the seam is never invoked.
6. `test_mock_adapter_still_works_in_test_mode` — regression pin: default mode `mock` + sidecar returns the canonical 8 fields.

**tests/test_sms_gateway.py (PROD-03, 4 tests):**
1. `test_unconfigured_gateway_keeps_row_queued` — no URL/key; `enqueue_sms` leaves `status='queued'` (regression pin for the 9 existing escalation tests).
2. `test_configured_gateway_marks_row_sent` — monkeypatched `_post_to_gateway` records the payload; row becomes `sent` with `provider_name='generic_http'`, `sent_at` set.
3. `test_gateway_failure_fails_soft` — seam raises; row `failed` with `error_message`; `send_escalation_sms` does not raise and the in-product banner still fires.
4. `test_gateway_payload_uses_sender_name_and_phone` — captured payload `to` equals `org.contact_phone` and `sender` equals `settings.sms_sender_name`.

**tests/test_contact_phone_api.py (PROD-03, 6 tests):**
1. `test_update_contact_phone_round_trip` — owner POST returns 200, `org.contact_phone` persisted, `SubscriptionRead.contact_phone` echoes it.
2. `test_update_contact_phone_normalizes_input` — `'+251 91 123 4567'` stored as `'+251911123456'`.
3. `test_update_contact_phone_rejects_invalid` — `'not-a-phone'` → 422.
4. `test_update_contact_phone_requires_owner_or_admin` — viewer token → 403.
5. `test_update_contact_phone_audit_event` — `organization.contact_phone_updated` recorded with masked phone payload.
6. `test_escalation_uses_captured_phone` — capture via the API, then escalate a receipt → `SmsMessage.to_phone` equals the captured value (end-to-end).

**tests/test_config_guards.py (PROD-02/04/05, 12 tests + 1 Fernet pin — all construct `Settings(_env_file=None, ...)` with the other required prod fields set, isolating the guard under test):**
1. `test_production_extraction_mode_rejects_mock` — `receipt_extraction_mode='mock'` in production → `ValueError` on `effective_receipt_extraction_mode`.
2. `test_production_extraction_mode_accepts_real` — `real` passes (positive pin).
3. `test_production_cbe_holder_required` — empty `cbe_account_holder` → `ValueError`.
4. `test_production_cbe_number_required` — empty `cbe_account_number` → `ValueError`.
5. `test_production_dashen_holder_required` — empty `dashen_account_holder` → `ValueError`.
6. `test_production_dashen_number_required` — empty `dashen_account_number` → `ValueError`.
7. `test_production_requires_provider_key_encryption_secret` — empty → `ValueError`.
8. `test_production_provider_key_encryption_secret_min_length` — 8-char secret → `ValueError`.
9. `test_production_database_url_required` — empty `database_url` → `ValueError` via `effective_database_url` (pins pre-existing guard).
10. `test_production_jwt_secret_required` — empty `jwt_secret_key` → `ValueError` (pins existing).
11. `test_production_jwt_secret_min_length` — 8-char secret → `ValueError` (pins existing).
12. `test_development_defaults_skip_guards` — dev/test defaults (empty accounts, empty secrets, mode `mock`) raise nothing.
13. `test_fernet_binding_uses_effective_encryption_secret` — production Settings with a 32+ char secret: `encrypt_provider_key`/`decrypt_provider_key` round-trip; production with empty secret: calling `encrypt_provider_key` raises `ValueError`.

**ops-console (1 smoke test):** extend `workspaceSurfaces.smoke.test.tsx` — `test_account_page_renders_escalation_phone_field` asserts the phone input and save button render on the Account route.

**Existing suites must stay green (no regressions):** `test_receipt_escalation_sms.py` (9), `test_receipt_extraction.py` (9), `test_activation_seeding.py` (11), `test_cors_config.py` (5), plus the full 298-test backend suite and 30-test ops-console suite.

**Planned test counts:** PROD-01: 5 · PROD-02: 7 (6 + 1 config guard) · PROD-03: 10 (4 + 6) · PROD-04: 4 · PROD-05: 6 (5 guards + 1 Fernet) · frontend: 1 → **33 new backend tests + 1 new frontend smoke test = 34 planned.**

## Non-Goals (R0)

- No new routes/pages beyond `POST /api/v1/subscriptions/me/contact-phone` and the AccountPage phone field.
- No SMS scheduler/poller — dispatch stays inline at enqueue; outbox polling for unconfigured deployments remains documented semantics.
- No backup/restore infra (PROD-08, later), no analytics (PROD-10, later), no rate-limit review (PROD-11, later), no CI gates (PROD-13, later), no CORS prod-domain wiring (PROD-06, later — but the dev hotfix is committed first per adjudication #4).
- No vendor-specific SMS adapter beyond the generic REST contract; no extraction provider beyond the single OpenAI-compatible adapter.
- Honesty rules preserved: zero-confidence warnings, admin-queue manual review, and the escalation in-product banner are unchanged; no invented success metrics anywhere.

## QA-Audit-Against

QA audits this batch against: `docs/production-readiness-plan.md` §9 rows **PROD-01..05** (acceptance criteria verbatim), §6 checklist items **PROD-A..E**, §2 platform-api env matrix, and this document (adjudications #1–5 are binding). Special attention: PROD-01 hermetic seeding from a pristine CWD; PROD-02 mock-unusable-in-production guard + zero-confidence short-circuit; PROD-03 fail-soft dispatch + phone validation/RBAC; PROD-04 blank-account impossibility; PROD-05 Fernet seam binding. Ledger debit after QA APPROVED: PROD-A..E checked in §6, PROD-01..05 marked in §9.
