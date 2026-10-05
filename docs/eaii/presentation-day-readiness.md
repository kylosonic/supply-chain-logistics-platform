# Presentation-day readiness — FreightPilot at EAII

**Prepared:** 2026-10-05 · **For:** the session on 2026-10-06
**Method:** every claim below was checked against the live deployment, the running
console, or the repository source on 2026-10-05. Where something was *not* verified,
it says so. Nothing here is inferred from documentation alone.

---

## 1. The short version

**The platform is live and the core loop works.** An automated sweep of the real
production API passed **44 of 46 checks** (the two failures are one bug, fixed in
this batch but not yet deployed — §5).

So tomorrow's risk is **not** "will it fall over". It is three specific things:

| # | Risk | What to do |
|---|---|---|
| 1 | A **fresh workspace opens on a dashboard full of "Locked" tiles** | Warm the demo workspace tonight — §2.1 |
| 2 | Three surfaces show **data that isn't real**, and an AI institute is exactly the audience that asks | Know what to say — §4 |
| 3 | The **flagship Ethiopian-market feature has no screen** in the console | Now it does — §5.3 |

---

## 2. Do these before the audience arrives

### 2.1 Warm the demo workspace (most important item)

A brand-new signup lands on a dashboard where **Forecast demand** and **Weather
risk** read **"Locked — Unlocks after Milestone 5"**, and the inventory charts,
forecast chart, dock gantt and freight panels are replaced by dashed gate boxes.

This is by design (NB-29 progressive reveal), but it is not what you want on
screen. It happens because seeding marks sample rows `data_origin='sample'`, while
milestone progress counts only `real` rows — so a fresh workspace reports
`n_of_5 = 0`. **Verified live:** the signup response for a brand-new company
returns `"n_of_5": 0`.

**Fix:** in the workspace you will present, upload the five CSVs once (Data Intake
→ warehouses, items, fleet, inventory, orders), then run one route optimisation.
That completes all six milestones and unlocks every panel. Do this **tonight**, not
tomorrow.

### 2.2 Log in as **admin**, not operator

The sidebar shows all ten items to every role, but three routes are role-gated and
`ProtectedRoute` redirects a mismatch to `/unauthorized` — **a bare page with no
sidebar and no way back**. An `operator` who clicks *Verification Queue*, or a
`viewer` who clicks *Data Intake*, ends the demo until someone edits the URL.

**Log in as the workspace owner/admin.**

### 2.3 Do not sign up live on stage

`POST /auth/company-signup` is rate-limited to **3 per minute per IP** and rejects
public email domains (gmail, yahoo, outlook, icloud, proton…). A single fumble
plus a retry can produce a `429`, and a gmail address gets
*"Please use your company email domain"*. Have the workspace already created and
be logged in before you start.

### 2.4 Pre-warm the API

The first request after idle can take several seconds (serverless cold start) — one
`GET /billing/state` took **>60s** during today's sweep, then 1.0s on retry. Open
`https://platform-api-smoky.vercel.app/health` a couple of times before you present,
and click through the console once.

### 2.5 Have the fallback ready

All four URLs returned **200** today:

| Surface | URL | Status |
|---|---|---|
| Product website | https://product-web-chi.vercel.app | 200 |
| Operations console | https://ops-console-azure.vercel.app | 200 |
| API (`/health`) | https://platform-api-smoky.vercel.app/health | 200 — `{"status":"ok","db":"ok"}` |
| EAII submission page | https://freightpilot-eaii.vercel.app | 200 |

If the console misbehaves, the EAII submission page carries the pitch deck and a
4m34s narrated product video that needs no login.

---

## 3. What is genuinely working (so you can demo it with confidence)

Verified against production today, as a brand-new Ethiopian logistics company:

- **Signup → seeded workspace.** A new company immediately has 3 Addis warehouses
  (Addis Central/Bole Road, Arat Kilo, Kality), 3 items, 9 inventory rows, 12
  historical orders, 3 fleet assets. `n_of_5: 0` as designed.
- **Route optimisation — the centrepiece.** Real computation over the tenant's own
  warehouse coordinates: `21.07 km`, `31.61 ETB`, 2 stops, persisted to schedule
  and history. Haversine great-circle greedy nearest-neighbour; no external service.
- **Demand forecasting is real ML.** `RandomForestRegressor` (250 trees,
  `OneHotEncoder` over warehouse×SKU + week/month/weather), trained on the tenant's
  own order history, cached by a training-frame hash. Live response:
  `model=RandomForestRegressor, points=12`.
- **Driver roster + cash-on-delivery, end to end.** Driver created (duplicate phone
  → clean `409`, not a 500) → COD shipment auto-assigned → delivery with a partial
  declaration → `2500.00 expected / 2000.00 collected / 500.00 shortfall` →
  settlement keeps the shortfall. **This whole loop is real and it is the most
  Ethiopia-specific thing in the product.**
- **Tenant isolation on the operational surfaces.** A second company sees **0**
  drivers and a cross-company driver read answers **404, never 403**.
- **Commercial surface.** Free tier 2,500 tasks/month; ETB ladder 4,500 / 10,000 /
  45,000; bank-transfer payment to CBE or Dashen with receipt verification — a
  genuinely local payment model, not a Stripe bolt-on.
- **90 API paths**, `APP_ENV=production`, Neon-backed Postgres.

---

## 4. What NOT to claim (and the exact reason)

An AI institute will ask harder questions than a general audience. Each of these is
a place where the product's own documentation or code contradicts a tempting claim.

| Don't say | Why | If asked, say |
|---|---|---|
| "AI weather risk" / "weather-aware routing" | The dashboard's **"Weather risk 8/10"** and the red polygon over the Addis map come from a **hardcoded fallback** in `weather.py:54-65`. The simulation gate requires disruption `> 0.5`, but the generator can only ever reach **0.298** anywhere on the grid — so the real branch is unreachable and the constant is returned every single time, for every tenant. | "Weather is a **simulated input layer** today; the routing and forecasting are real. Live weather feeds are integration work." |
| Weather improves the forecast | Forecast *features* include weather, but future weeks reuse the **last historical** weather vector, so weather carries no horizon signal. | "Weather is a feature in the model today; its lift isn't measured yet." |
| "The customer gets an SMS" | `SMS_GATEWAY_URL`/`API_KEY` are unset, and `_dispatch_sms` returns immediately when unconfigured — the message stays `queued` forever. | "SMS escalation is designed and wired; the gateway isn't connected yet." |
| "Autonomous exception resolution" / "Auto-Resolve" | `generate_rerouting_plan` queries `RouteSchedule.origin_warehouse_id`, `.destination_warehouse_id` and `.carrier` — **none of those columns exist** on that model — so it raises before doing anything. `/alerts/{id}/auto-resolve` always answers `400`. The **Auto-Resolve button never even renders**, because the console gates it on a plan payload that can never be written. | Don't demo it. It also *invents* a carrier ("Expedited Freight Inc") and a cost in **USD** in an otherwise ETB product. |
| "Carbon-footprint minimisation" | All three cost terms are linear in distance (`weighted = d × K`), so **every weight vector produces the identical tour**. The eco re-run cannot change the route, and `co2_saved_kg` is therefore always `0.0`. | "Carbon reporting is on the roadmap." |
| "Customers" / "ARR" / "traction" | Pre-revenue. Your own submission checklist says so explicitly. | Programme acceptance, verified funnel, working product. |
| "Signed desktop installer" | Electron runs from source; no code-signing certificate. | "Desktop shell is in the repo; signing is planned." |
| Receipts verified "within 24 hours" as a live guarantee | The receipt flow requires a **paid tier with an issued invoice**. On a free workspace `POST /receipts/upload` returns `400 — "You have no open invoice to apply this receipt to."` | Only demo receipts on a workspace that has an issued invoice. |

---

## 5. What changed in this batch

All changes are on the working tree, verified locally (typecheck, lint, **167 console
tests**, production build), and awaiting push.

### 5.1 `GET /api/v1/inventory` returned HTTP 500 for every tenant — **fixed**

`InventoryRead` declared `id` / `warehouse_id` / `item_id` as `str` while the model
returns `UUID`. Pydantic does not coerce one to the other, so serialising a real row
raised `ResponseValidationError`. **This is the same defect class the repo already
fixed for `RouteScheduleSummary` in NB-64** — the comment in `schemas/route.py`
describes it exactly; `schemas/inventory.py` was missed.

It went unnoticed because the console reads `/inventory/overview` (a projection with
no ids, unaffected) and the endpoint had no test. **Verified live: HTTP 500 with 9
rows present.** Fixed with a field-level UUID→str coercion so the response shape is
unchanged, plus regression tests.

### 5.2 `GET /api/v1/invoices` leaked other tenants' freight invoices — **fixed**

**Verified live and reproduced twice:** a freshly created workspace that had never
uploaded anything returned **two freight invoices belonging to a different tenant**,
while `/notifications` correctly returned none for the same caller.

Three separate leaks in one endpoint:
- the **read** had no tenant scope at all;
- the **upload** never stamped `organization_id`, which is what left every historical
  row unattributed;
- the **order lookup** during upload was unscoped, so an operator could raise an
  invoice against another organisation's order and read its quantity and unit price
  back through the computed quoted rate.

Fixed with the repo's own shared scoping helpers. One deliberate judgement call,
documented in the code: the read passes `include_legacy_null=False`. The TECH-58
default exists so a *single-tenant* deployment keeps seeing rows written before org
scoping — but in a genuinely multi-tenant database it does the opposite of its
intent, and it is precisely why those two rows were world-readable. **Reverting one
keyword restores the old behaviour if the team disagrees.**

### 5.3 The Ethiopian-market feature now has a screen — **built**

`drivers` + `cash-collections` (NB-86) was **API-only**: twelve endpoints and zero
console surface. There was no Drivers page and no COD ledger page among the console's
twelve. The feature built specifically for this market could not be shown in the
product.

Added **Fleet & Cash** (`/drivers`), with:
- four end-of-day tiles — active drivers, cash with drivers, collected-not-banked,
  and **shortfall**;
- the roster, with phone as the identifying field, plus *Deactivate* (admin-only);
- **"What is on the van"** — what that driver is carrying right now;
- the cash position, with **Record cash** (declare, with the shortfall shown before
  you commit) and **Settle** (admin-only, because accepting a shortfall writes money
  off).

Also extended the Shipments board so the loop is reachable without leaving the UI:
**assign a driver and set a cash-on-delivery amount at creation**, and **confirm a
delivery with the cash figure in one call** — the shortfall is computed and shown in
the dialog before you confirm.

24 new tests (14 API-contract, 10 render). All 143 pre-existing tests still pass.

---

## 6. Known defects deliberately left alone tonight

Recorded so they are choices, not oversights.

### 6.1 The admin receipt surfaces are cross-tenant — **not fixed, and this is the most serious remaining finding**

`list_queue()` and `list_verified()` in `services/billing/receipts/queue.py` filter on
`status` **only** — no organisation filter — and `get_queue_item()` is a bare
primary-key lookup. Access is guarded by `require_org_roles(OWNER, ADMIN)`, which
checks the caller's role **inside their own organisation**, not ownership of the
receipt. The module docstring for the reversal endpoints acknowledges the queue is
"system-wide", and `delete_trusted_payer` takes `organization_id` as a **query
parameter**.

**Confirmed by reading the source**, not by live exploitation. It is not demo-visible
today because production currently holds **zero receipts** (`/receipts/queue` → `[]`,
verified). It becomes visible the moment two organisations both have receipts —
including if you demo the receipt flow on a workspace whose uploads are visible to
another tenant's Verification Queue.

I did not fix this because it needs a product decision about what a "platform admin"
is in a multi-tenant product, and because the queue is empty for tomorrow. It should
be the first thing fixed after the presentation.

### 6.2 The three fabricated surfaces

The weather zone and the rerouting plan are described in §4. You chose to be briefed
rather than have me change what is on screen, so the dashboard still shows
**Weather risk 8/10** in a danger tone and the route map still carries a red overlay
covering Addis Ababa. Both come from the same hardcoded rectangle. **Decide before you
present whether that tile helps or hurts you** — if it's on screen, expect the question.

### 6.3 Smaller items

- **Forecast weeks land in the past.** The horizon anchors to the last order week, and
  the shipped orders end **2026-01-28**, so the chart plots February 2026. Upload
  recent order dates in the warm-up to fix this.
- **Cash exposure is invisible until delivery.** A COD shipment still `in_transit` is
  not counted in "cash with drivers" — the cash record opens at the delivery event. The
  ledger answers *"what came back short"*, not *"what is out on the road"*.
- **`POST /providers/keys/{id}/test` fakes verification.** It makes no network call;
  the verdict is `len(key) >= 12` and the message reads "Key format looks valid". A
  12-character nonsense key shows a green badge.
- **`/billing/state` reported `phase: free`, `can_write: true`** on a free workspace —
  correct, but note the free tier hard-locks writes at 2,500 tasks/50 optimisations.
- **A fleet CSV upload does not create drivers.** `fleet-assets-csv` writes
  `driver_name`/`driver_contact` into `fleet_assets`; the new `drivers` roster is a
  separate table populated only through `/drivers`. An operator who uploads their fleet
  file still sees an empty roster. The new page says this plainly on screen.

---

## 7. The target customer's view — what an Ethiopian operator would try to do

Read as the buyer, not the builder. These are the tasks someone running a real
Ethiopian logistics operation would attempt, and where the product meets or misses them.

### What lands well

- **Cash on delivery.** In this market the driver collects cash at the door, and it is
  the largest unmonitored cash risk an operator carries. The product now tracks
  expected → collected → shortfall per delivery, and *keeps the shortfall on the books
  at settlement* — which is exactly what month-end needs.
- **Bank transfer with receipt verification to CBE / Dashen.** No card rails, no Stripe.
  A ±1,000 ETB auto-forward tolerance and a trusted-payer list. This is the most
  locally-grounded part of the whole product and it is worth showing.
- **Retry-safe writes.** `client_ref` idempotency on shipment creation is not a
  checkbox here — a dropped connection mid-dispatch is the normal case, and the server
  contract is built for it.
- **Additive-only price ladder in ETB**, and `total_cost` displayed in ETB throughout.
- **Addis-real seed data.** Bole Road, Arat Kilo, Kality (the dry port), Ethiopian
  driver names, `+251` phone numbers. It reads as a local product, not a reskin.

### Where the operator hits a wall

1. **No customs, no clearance, no corridor.** This is the big one. Ethiopian logistics
   is largely **import freight**: ERCA clearance, the Ethiopian Single Window, ASYCUDA
   declarations, the Djibouti corridor, transit to Modjo dry port, then inland
   distribution. The product models **warehouse-to-warehouse distribution** — consignment
   tracking, HS codes, duty, bonds, container and transit-document state do not exist.
   Worth being honest about: FreightPilot is a **distribution and dispatch** product, not
   a freight-forwarding system. If a reviewer from the sector asks "does it do customs?",
   the answer is no, and it is better said first.
2. **The default cost model is not credible to the person you're selling to.** The
   console ships `cost_per_km = 1.5` and `speed_kmh = 45`. Diesel in Ethiopia was
   **180.46 ETB/litre** on 28 September 2026
   ([GlobalPetrolPrices](https://www.globalpetrolprices.com/Ethiopia/diesel_prices/)).
   A loaded medium truck burns roughly 20–30 L/100 km, so **fuel alone is 36–54 ETB/km** —
   the default understates it by more than 20×. That is why the demo shows
   *"21.07 km → 31.61 ETB"*, and a real operator will say out loud that you cannot run a
   truck for 31 birr. Both fields are editable in the Route Studio form, so set them to
   a defensible figure before you present, or be ready to explain what the number means.
3. **45 km/h through Addis is optimistic.** The ETA is `distance ÷ speed`. Midday Addis
   traffic is far slower; expect a dispatcher to challenge the arrival times. Also note
   distances are **straight-line haversine between warehouse coordinates**, not road
   distance, so the 21.07 km is a floor, not a route length.
4. **The fleet CSV and the driver roster are not connected** (§6.3) — the file an
   operator already has will not populate the list the operator needs.
5. **No Amharic, no Ethiopian calendar.** Deliberately out of scope for v1 (NB-47), and
   defensible — but to an Ethiopian audience it is the first thing noticed. Dates render
   Gregorian throughout.
6. **Capacity is unit-less.** "180 units" and "40 capacity" mean nothing against
   quintals, kilograms or cubic metres. Vehicle classes (Isuzu FSR/NPR, Sino trucks,
   bajaj for last mile) are absent.
7. **No driver-side surface.** Drivers are records, not users: a driver cannot confirm
   their own delivery or declare their own cash. The office does it for them. That is
   the natural next slice, and the roster is now its prerequisite.
8. **No proof-of-delivery artefact.** `proof_of_delivery_ref` accepts a reference but
   nothing stores a photo or signature.
9. **Notifications are in-product only.** Where SMS exists it is unconfigured (§4), and
   there is no email. In practice the office will still phone the driver.

### What I'd expect them to ask that the deck may not answer

- *Who pays, and how?* — answered well: ETB, bank transfer, receipt verified.
- *What happens when the connection drops?* — answered well: idempotent writes.
- *Where does the AI actually sit?* — answer honestly: a RandomForest demand model and
  a greedy optimiser; the weather layer is simulated (§4). At an AI institute this
  question is close to certain, and a precise answer will land better than a broad one.
- *Can it talk to ERCA / the Single Window?* — no. Say so, and frame it as the roadmap.
- *Is my data separate from my competitor's?* — yes on the operational surfaces
  (verified: drivers 404 across tenants), but see §6.1 for the receipts caveat. Do not
  volunteer "yes" without that qualification if a technical reviewer is present.

---

## 8. Suggested demo order

1. Product website briefly — positioning in ETB, bank transfer, no card.
2. Log into the **warmed** workspace as admin. Dashboard unlocked, real numbers.
3. **Route Studio** — run an optimisation. Map, stops, distance, cost. *(Set
   `cost_per_km` to a credible figure first — §7.2.)*
4. **Shipments** — create a COD shipment, assign a driver.
5. **Fleet & Cash** *(new)* — the roster, "what is on the van", then mark the delivery
   with a partial cash figure. Watch the **500 ETB shortfall** appear.
6. Close the loop — **settle** it and show the shortfall is *kept*, not erased.
7. **Payments** — the CBE/Dashen receipt story. Only if the workspace has an issued
   invoice (§4).
8. Finish on the ETB price ladder and the free tier.

Skip **Exceptions** (auto-resolve is dead — §4) and don't linger on the **Weather risk**
tile unless you're ready for the question.

---

## 9. Verification evidence

| Check | Result |
|---|---|
| Console typecheck (`tsc --noEmit`) | clean |
| Console lint (`eslint --max-warnings=0`) | clean |
| Console tests | **167 passed / 21 files** (143 pre-existing + 24 new) |
| Console production build | succeeds; `DriversPage` = 14.32 kB (4.05 kB gzip) lazy chunk |
| Production funnel sweep | **44/46** — `scripts/verify_production_funnel.py` |
| Failing checks | `GET /api/v1/inventory` → 500 (fixed in this batch, **not yet deployed**) |
| Backend tests | **NOT RUN LOCALLY** — see §10 |
| Backend syntax check (`py_compile`) | clean on all three changed/added files |

## 10. One thing I could not verify

**I could not run the backend test suite on this machine.** `pypi.org` is unreachable
from here — DNS resolves it to IPv6-only addresses and HTTPS requests hang
indefinitely, while npm, GitHub and the Vercel endpoints all work fine. I created a
Python 3.11 venv, but `pip install` could not fetch a single package in ~50 minutes, so
I killed it rather than let it spin.

What that means: my two backend fixes are verified by **reading the code, matching the
pattern already used and tested elsewhere in the repo (`drivers.py`, `tenant_scope.py`),
a `py_compile` pass, and live reproduction of the original defects against production**
— but **not** by a local `pytest` run. They are covered by
`tests/test_inventory_and_invoice_tenant_scope.py`, which will run in GitHub Actions on
push. **Check that CI run before relying on them tomorrow.**

I did not fake this result. If you have a machine with PyPI access, running
`cd apps/platform-api && pytest -q` is the one piece of evidence still missing.
