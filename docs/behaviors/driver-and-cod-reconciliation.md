# Driver roster and cash-on-delivery reconciliation (NB-86)

**Status:** deployed to production 2026-10-01 and smoke-tested live; awaiting human UAT
**Origin:** product evaluation from the buyer's side — what an Ethiopian freight
operator would need on day one, tested against what the API actually did.

## 1. What the evaluation found

The platform was strong where the pitch said it was: order intake, route
optimisation, exception handling, and **bank-transfer** reconciliation against
invoices. Three things an operator does *every single day* were missing entirely,
and each was verified by searching the codebase rather than assumed:

| Operational need | Evidence it was absent |
|---|---|
| Know **who** is carrying a load | zero occurrences of `driver` anywhere in `app/` |
| Know how much **cash** is coming back | `cod_amount`, `cash_collected`, `remittance` — no matches |
| Re-try a write safely on a bad connection | no `idempotency`, no `client_id` — every retry risked a duplicate |

The third one matters more here than in most markets. An Ethiopian operator's
confirmation traffic arrives over mobile data that drops mid-request. A dispatch
screen that retries a create, or a driver confirming a delivery twice, would
previously have produced two shipments and two financial records with no way to
tell which was real.

**The cash gap was the expensive one.** The product already reconciled bank
transfers — it understood that money arrives and must be matched. But in this
market the driver also collects cash at the door, and nothing in the software
recorded how much was expected, how much was handed in at the end of the day, or
what was missing. That is the largest unmonitored cash risk an operator carries,
and it was invisible.

## 2. What was built

### 2.1 Drivers (`/api/v1/drivers`)

A tenant-scoped roster. Phone is the natural key — it is how an operator actually
identifies a driver, and it is what a future driver-facing surface would
authenticate against.

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/drivers` | the roster, optional `?status=` filter |
| `POST` | `/drivers` | add a driver (409 on a duplicate phone in the same workspace) |
| `GET` | `/drivers/{id}` | one driver |
| `PATCH` | `/drivers/{id}` | correct details, change status |
| `DELETE` | `/drivers/{id}` | **deactivate**, not delete |
| `GET` | `/drivers/{id}/shipments` | what this driver is carrying right now |

Two deliberate choices:

- **Deactivation instead of deletion.** Shipments reference the driver, so a
  roster cleanup must never remove delivery history. The FK is `ON DELETE SET
  NULL` as a last resort, not as the normal path, and an inactive driver cannot
  be assigned new work (409).
- **`/drivers/{id}/shipments` exists as its own endpoint** because the operator's
  real question in the morning is "what has Yohannes got on the van?", not "show
  me all shipments and I will filter".

### 2.2 Shipment assignment (`POST /api/v1/shipments/{id}/driver`)

Assignment is separate from status because it happens at dispatch, before any
movement, and is the most frequent edit of a morning. Clearing a driver is
supported (cancelled or reassigned jobs).

### 2.3 Cash-on-delivery ledger (`/api/v1/cash-collections`)

One cash record per shipment that carries COD. The lifecycle mirrors the
receipt-reversal contract already used for bank transfers:

```
outstanding  ->  collected  ->  settled
                       \-->  voided (delivery reversed)
```

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/cash-collections` | filter by `status`, `driver_id` |
| `GET` | `/cash-collections/ledger` | **the end-of-day position** |
| `GET` | `/cash-collections/{id}` | one record |
| `POST` | `/cash-collections/{id}/declare` | record what the driver holds |
| `POST` | `/cash-collections/{id}/settle` | office received the cash (admin only) |

Three decisions worth stating:

- **The cash record opens at delivery, not in a second call.** `POST
  /shipments/{id}/status` accepts `cash_collected_etb` alongside the delivery, so
  the confirmation and the cash figure travel in one request over one connection
  attempt. A driver who never makes a second call still produces a complete
  record.
- **A shortfall is stored, not derived.** If `expected_etb` were later corrected,
  a historic shortfall must not silently change — the number that was acted on is
  the number that stays.
- **Settling does not erase the shortfall.** A written-off shortfall is exactly
  what an operator needs at month end, so settlement closes the record and leaves
  the figure intact. Settling is **admin-only**, matching receipt reversal:
  accepting a shortfall writes money off.
- **Over-collection is a surplus, not a negative shortfall.** `shortfall_etb` is
  floored at zero (and the DB check constraint enforces it); a driver who
  collected more is visible as `collected_etb > expected_etb`.

### 2.4 Idempotency (`shipments.client_ref`)

A caller-supplied reference makes create safe to retry. The guard is a **partial
unique index** on `(organization_id, client_ref)` — partial for the same reason
as `shipment_no`: NULLs are distinct, so shipments created without a reference
stay unconstrained, and two organisations may independently use the same
reference without colliding.

## 3. Acceptance criteria (what the tests pin)

`tests/test_driver_and_cash_reconciliation.py` — 24 tests. Each answers an
operational question rather than asserting an endpoint exists:

| Question the operator asks | Pinned by |
|---|---|
| Who is on the roster today? | `test_driver_can_be_added_and_appears_on_the_roster` |
| Can two drivers share a phone? | `test_duplicate_phone_in_one_workspace_is_a_conflict` |
| What if a driver leaves? | `test_driver_can_be_updated_and_deactivated`, `test_inactive_driver_cannot_be_assigned` |
| What is on that van? | `test_driver_shipment_list_answers_what_is_on_the_van` |
| How much cash is out right now? | `test_delivery_with_no_cash_declared_leaves_the_full_amount_outstanding` |
| The customer paid short — now what? | `test_cash_declared_with_delivery_records_the_shortfall` |
| The driver collected *more*? | `test_over_collection_is_a_surplus_not_a_negative_shortfall` |
| Can cash move before delivery? | `test_cash_declared_without_delivery_is_rejected` |
| How much is missing, total? | `test_ledger_summarises_what_is_out_and_what_is_missing` |
| Who may write off a shortfall? | `test_settling_requires_admin` |
| A retry arrived after banking — did it reopen the debt? | `test_settled_record_cannot_be_reopened_by_a_replayed_delivery` |
| The confirmation was sent three times? | `test_declaring_twice_is_idempotent` |
| The dispatch screen retried the create? | `test_repeated_create_with_the_same_client_ref_returns_one_shipment` |
| Whose cash is it after reassignment? | `test_reassignment_follows_the_cash` |

**Cross-tenant:** drivers and cash records are invisible across organisations and
cross-tenant access answers **404, never 403**, so record existence does not leak.
Pinned by `test_drivers_are_invisible_across_organisations`,
`test_cannot_assign_another_organisations_driver`,
`test_cash_records_are_invisible_across_organisations`,
`test_client_ref_is_scoped_per_organisation`, and
`test_driver_rows_carry_the_creating_organisation` (guards the scoping column
itself, since a NULL there would make the roster global).

## 3b. Production verification (2026-10-01)

Migration `20260812_0020` applied to production Neon, then platform-api deployed.
The full lifecycle was exercised against the live API, not just the test suite:

| # | Check | Live result |
|---|---|---|
| 1 | Driver created | `Yohannes Bekele / +251911000777 / active` |
| 2 | Duplicate phone in the same workspace | **409**, not 500 |
| 3 | COD shipment created and auto-assigned | `SHP-SMOKE-… cod=2500.00 driver=Yohannes Bekele` |
| 4 | Create replayed with the same `client_ref` | returned the **same shipment id** |
| 5 | Ledger before delivery | `outstanding=0 shortfall=0.00` |
| 6 | Delivery with a partial declaration | `collected=2000.00 shortfall=500.00`, `actual_delivery` set |
| 7 | Confirmation replayed after delivery | **one** cash record, shortfall still `500.00` — no double-count |
| 8 | Settle | `status=settled`, shortfall **kept** at `500.00`, `settled_at` set |
| 9 | Second organisation | `drivers=0 shortfall=0.00`; cross-tenant cash read → **404** |

Every one of the eight numbered assertions above came back as required on the
deployed build.

## 4. Not in this batch, and why

Recorded so the gaps are explicit rather than discovered later:

- **No driver-facing authentication or mobile app.** Drivers are records, not
  users. A driver cannot yet declare their own cash; an operator does it for
  them. This is the natural next slice, and the roster is the prerequisite for it.
- **No proof-of-delivery capture (photo/signature).** `shipments.proof_of_delivery_ref`
  already accepts a reference and is passed through the status endpoint, but
  nothing stores the artefact itself. Needs object storage, which is a
  different-sized decision.
- **No cash-to-bank-credit link.** Settling records that the office received the
  cash; it does not yet reconcile that cash against a bank deposit the way
  `payment_receipts` reconciles transfers. Closing that loop would let the ledger
  explain a bank shortfall end to end.
- **No offline queue in the clients.** The API is now safe to retry, but
  `apps/ops-console` does not yet persist a pending confirmation locally and
  replay it. The server contract is in place; the client work is not.
