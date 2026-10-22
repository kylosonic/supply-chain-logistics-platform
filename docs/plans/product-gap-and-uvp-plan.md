# FreightPilot — Product Gap Assessment, Unique Value Proposition, and 12-Week Plan

**Date:** 2026-10-21  
**Status:** Strategy and execution plan — no implementation changes in this document  
**Companion research:** [Competitive Research — Ethiopia and Adjacent Logistics Platforms](../competitor-research-ethiopia-2026-10.md)

## 1. Executive decision

FreightPilot should not compete as another Ethiopian freight marketplace, and it should not position itself as a generic AI control tower.

The strongest defensible product is:

> **FreightPilot is the cash-aware dispatch system for Ethiopian private fleets. Plan the day's routes, prove every delivery, reconcile every driver's cash, and close the day with an auditable record—without joining a marketplace or changing how customers pay.**

Short form:

> **Know the route. Know the cash. Close the day.**

The product should serve distributors, wholesalers, manufacturers, and 3PLs that own or manage a private fleet. The first job is not matching strangers; it is helping an existing operation execute and account for its own deliveries.

This position is stronger than “AI logistics platform” because:

- it names a specific buyer and a recurring operational pain;
- it avoids the working-capital and liquidity burden of a marketplace;
- it uses capabilities FreightPilot already has or can build coherently: ETB operations, driver assignment, cash-on-delivery ledger, bank-transfer receipt verification, route explanations, forecasting, and audit;
- it is difficult for a global routing vendor to copy without local payment and cash workflows;
- it is difficult for a local custom-software shop to copy without productizing onboarding, workflow, and repeatable support.

AI is a supporting capability, not the category. The AI promise should be:

> **Grounded decisions, not autonomous theater.** Every recommendation is tied to a real record, explains its evidence, and waits for human approval before changing an operational or financial state.

## 2. What is actually built today

### Phase 0 progress — 2026-10-21

The first trust-reset slice is implemented locally on `codex/ai-decision-intelligence`:

- business roles now require an active organization membership;
- write guards no longer pass through for unaffiliated accounts;
- the websocket refuses an org-less subscriber;
- user registration attaches the new user to the actor's workspace instead of creating an
  unaffiliated global account;
- the users list is workspace-scoped;
- business scoping is defense-in-depth safe for an org-less actor (explicit legacy NULL rows only;
  single-record access is denied);
- route optimization and history use the member-selected workspace, including `X-Organization-Id`;
- the public product site now has a real `/docs` route and no longer links its footer to a 404;
- weather is explicitly labelled simulated and no mock storm is injected;
- rerouting no longer invents a carrier, recovery time, or cost; it uses only a saved active route
  candidate and fails closed otherwise.

Backend verification after these changes: **482 passed** (full suite). Product-web typecheck/build
and the eleven-route bundle gate pass with mocked Google Fonts because outbound font fetch is
blocked in this environment. Ops typecheck/lint pass, and **28 files / 174 tests** plus a real-config
production build pass. Independent security review cleared all previously reproduced critical/high
blockers; human UAT and final QA sign-off remain open. The P1 Cash-Aware Dispatch work is now
implemented locally on the same branch: customer
stops and windows, a deterministic time-window planner, signed driver manifests, an installable
driver PWA with queued status/cash actions and Amharic-first labels, tenant-scoped POD capture and
retrieval, admin-only day-end cash close, workflow-safe team invitations, and the grounded
Decision Brief / Cash Risk Radar / exception triage. The independent security review found several
pre-existing cross-tenant paths (freight invoices, selected-workspace writes, role-floor bypass,
quarantine slug takeover); those were remediated and now have regression tests. Human UAT,
production migration, merge, and deployment remain open.

The current repository is broader than the public site suggests, but several capabilities are partial or simulated. This distinction must drive both product and marketing.

| Area | Current truth | Evidence | Strategic status |
|---|---|---|---|
| Company onboarding | Business-email signup, workspace creation, initial admin, sample-data seeding | `apps/platform-api/app/api/endpoints/auth.py`; `apps/platform-api/app/services/activation/seeding.py` | **Real and strong** |
| Multi-tenant workspace | Organization and membership model; selected-workspace resolution is explicit on item, warehouse, invoice, receipt, shipment, planning, driver, cash, audit, and live-socket paths | `apps/platform-api/app/models/membership.py`; `apps/platform-api/app/core/tenant_scope.py`; `tests/test_workspace_boundary_and_role_floor.py`; `tests/test_receipt_tenant_boundary.py` | **Real; prior security blockers cleared** |
| Data intake | CSV import for warehouses, items, fleet, inventory, orders; sample data on signup | `apps/platform-api/app/api/endpoints/ingestion.py`; `apps/ops-console/src/pages/UploadPage.tsx` | **Real, narrow** |
| Route planning | Weighted greedy optimizer; warehouse-to-warehouse deliveries; capacity and max-stop limits; unassigned deliveries preserved; route decision trace | `apps/platform-api/app/services/routing.py`; `apps/ops-console/src/components/RouteOptimizerForm.tsx` | **Real, but not a true delivery VRP** |
| Route explanations | Deterministic explanation of selected stop, runner-up, weighted factors, capacity exclusions | `apps/platform-api/app/services/route_explanations.py`; `RouteDecisionBrief.tsx` | **Real and differentiated** |
| Demand forecasting | RandomForest weekly demand; planning intervals; aggregate backtest/WAPE caveat; model cache | `apps/platform-api/app/services/forecasting.py`; `ForecastChart.tsx` | **Real, but data and evaluation are limited** |
| Weather | Deterministic simulated weather features; simulated risk zones | `apps/platform-api/app/services/weather.py`; `apps/platform-api/app/api/endpoints/weather.py` | **Simulation — must not be sold as live weather** |
| Rerouting | Simulated delay, placeholder carrier, invented cost and reasoning | `apps/platform-api/app/services/rerouting.py` | **Demo only — must be removed, gated, or explicitly labeled** |
| Shipments | Manual status, location text, ETA fields, POD reference string, driver assignment, COD amount | `apps/platform-api/app/models/shipment.py`; `apps/platform-api/app/api/endpoints/shipments.py` | **Partial** |
| Delivery proof | Tenant-scoped photo proof with magic-byte validation, per-order cap, recipient/notes metadata, and operator retrieval; signature capture and object storage remain future work | `apps/platform-api/app/api/endpoints/dispatch.py`; `DispatchPage.tsx`; `DriverPage.tsx` | **Real locally; object storage/signature remain** |
| Live updates | WebSocket snapshot every five seconds; no native GPS or device feed | `apps/platform-api/app/api/endpoints/live.py`; `SessionLiveUpdates.tsx` | **Periodic snapshot, not live tracking** |
| Telematics | Ingest endpoint accepts telemetry and IoT payloads | `apps/platform-api/app/api/endpoints/ingestion.py` | **Integration seam, no device fleet management** |
| Driver roster | Driver records, phone, license, vehicle plate, status, shipments | `apps/platform-api/app/api/endpoints/drivers.py`; `CashLedger` surfaces | **Real and strategically important** |
| Cash-on-delivery | Expected cash, collected cash, shortfall, outstanding/collected/settled lifecycle | `apps/platform-api/app/api/endpoints/cash_collections.py`; `apps/platform-api/app/services/cash_ledger.py` | **Strong wedge, but no driver capture UX** |
| Subscription receipts | Bank-transfer receipt upload, OCR/zero-confidence fallback, verification queue, wallet, reversal, audit | `apps/platform-api/app/services/billing/`; `ReceiptsPage.tsx`; `AdminReceiptsPage.tsx` | **Real and locally differentiated** |
| Team collaboration | Invite/accept/revoke, role change, member removal, last-owner protection, and fragment-based invite links | `app/api/endpoints/team.py`; `TeamPanel.tsx`; `AcceptInvitePage.tsx` | **Real locally** |
| AI provider layer | Encrypted BYOK keys, provider test/revoke, preferred provider; real OpenAI-compatible adapter used for receipt extraction | `apps/platform-api/app/api/endpoints/providers.py`; `receipt_extraction.py` | **Useful infrastructure, underused** |
| AI decision layer | Grounded Decision Brief, Cash Risk Radar, and exception triage built from tenant records; optional LLM rewriting remains future work | `app/services/decision_intelligence.py`; `app/api/endpoints/insights.py`; `DecisionBriefPanel.tsx` | **Real locally; evaluation/UAT pending** |
| Public docs | Real `/docs`, `/privacy`, `/terms`, `/security`, and `/status` routes; footer/sitemap/bundle budget include them | `apps/product-web/src/app/`; Next build; bundle gate | **Real** |
| Desktop | Electron shell and onboarding cockpit; no packaged/signed installer or update feed | `apps/desktop/`; TECH-92 | **Not a launch dependency yet** |
| Release state | AI decision-intelligence work is uncommitted on `codex/ai-decision-intelligence`; focused tests pass, full suite and tenant test need fresh verification | current branch status and latest local evidence | **Do not market as shipped** |

## 3. Gaps, ranked by consequence

### P0 — Must fix before selling more broadly

#### P0.1 Tenant boundary escape (fixed locally)

This was the most serious issue in the product assessment. It is fixed and deployed on
`master` after the release gates passed.

The current path allows an organization admin to create a user through the global `/auth/register` endpoint without attaching that user to an organization. The created user can receive a global `ADMIN` role. With no membership:

- `actor_organization_id()` returns `None`;
- many read paths call `scoped_to_organization(..., include_legacy_null=True)`, which returns the unfiltered query for an org-less actor;
- global-role checks can therefore reach other tenants' data.

This was not a cosmetic tenant leak. It undermined the core promise of a multi-tenant operations system.

Required direction:

- make every business endpoint require an active organization membership, not only a global role;
- remove unaffiliated user creation or move platform administration to a separate, explicitly audited control plane;
- make `include_legacy_null=False` the default for business reads;
- prohibit org-less users on all operational surfaces;
- add a test that proves a tenant admin cannot create or promote a cross-tenant user;
- add a test that proves every operational endpoint returns 403/404 for an org-less actor;
- review all repositories and endpoints for default-unfiltered behavior.

The implementation now requires membership on business surfaces, denies org-less single-record
access, scopes the user list, and attaches new users to the actor's workspace. Do not describe the
product as tenant-safe in enterprise sales until the independent security review accepts it.

#### P0.2 Simulated capabilities (corrected locally)

The rerouting service:

- sleeps for two seconds to look expensive;
- invents a carrier if no route exists;
- returns a fixed recovery time and USD cost;
- includes a confidence-like sentence not derived from data;
- writes that invented plan to an alert.

The weather service is deterministic pseudo-weather.

The rerouting path now either attaches a real saved active route candidate or records
`no_saved_alternative`; it no longer invents a carrier, recovery time, or cost. Weather zones are
explicitly labelled `source: simulated` and the mock-storm fallback is removed. Both remain
simulated capabilities and must be presented that way until real providers are connected.

The general rule remains:

- removed;
- feature-gated behind an explicit “demo” environment;
- relabeled in UI and API as simulated;
- replaced with a real provider and an evidence trail.

Never ship invented reasoning or cost as an operational recommendation.

#### P0.3 Public trust surface (partially fixed)

The live site previously:

- links “Documentation” to the home page;
- links “API Reference” to `/api`, which renders the 404 page;
- links “Desktop App” to the home page;
- had no discoverable privacy, terms, security, or status page when this assessment was written;
- uses the generic page title “Supply Chain Logistics Platform” in the operations console rather than the FreightPilot brand.

The repository now has a real `/docs` route, footer/navigation links no longer point at the old 404,
and the console title is branded. The privacy, terms, security, and public status pages now exist
and are included in the sitemap/footer/bundle gate; they still need legal review before a paid
enterprise launch.

#### P0.4 Release evidence (backend and UI green; default Vite script environment-blocked)

The release is deployed. The backend full suite now passes at **482 tests**, including the
new tenant-scope, receipt, live-socket, rerouting, and multi-workspace regressions. Product-web
typecheck/build and the eleven-route bundle gate pass with mocked Google Fonts. The operations
console passes **28 files / 174 tests**, typecheck, lint, and the real-config production build.
The release decision should remain:

- no merge, migration, or deploy until human UAT signs the release checklist;
- no production claim for route explanations or forecast intervals until deployed;
- no “AI feature shipped” claim until the exact release diff is deployed and smoke-tested.

### P1 — Required to make the unique value proposition real

**Implementation update — 2026-10-21.** The gaps below describe the state when this plan was
written. They are now implemented locally on `codex/ai-decision-intelligence` as one vertical
slice: customer/delivery-order models, time-window planning, a signed driver manifest, an
installable offline-capable driver PWA with an Amharic-first UI, POD capture/retrieval, admin-only
cash close, team invitations, and a grounded decision layer. Migration chain head is
`20260823_0024`.

Remaining P1 hardening before a paid launch:

- move POD bytes from the relational database to object storage and add signature capture;
- add a true idempotency key and conflict policy to the offline queue (the current status/cash
  writes are effectively repeat-safe, but proof uploads require connectivity);
- run the five-to-eight-pilot evaluation and measure same-day cash-close and POD completion rates;
- complete per-series forecast evaluation and the optional LLM summarizer behind a measured
  fallback.

#### P1.1 No customer delivery stop model

The route optimizer accepts only warehouse codes (`Delivery.warehouse_code`). It does not model:

- customer locations;
- recipient names and phone numbers;
- delivery time windows;
- service durations;
- multiple vehicles and driver shifts;
- pickup/delivery pairs;
- failed-attempt or return-to-depot behavior.

That means the current product is primarily an inter-warehouse replenishment planner, while the cash-on-delivery ledger implies customer deliveries. The workflow is not yet closed.

#### P1.2 No driver execution surface

The console is a desktop-oriented operator product. There is no driver app, PWA, or Telegram workflow for:

- receiving today's manifest;
- seeing stop sequence and customer instructions;
- updating arrival/delivery/failure;
- capturing photo/signature proof;
- declaring cash collected;
- working through intermittent connectivity.

This is the difference between a planning tool and an operating system.

#### P1.3 Cash reconciliation is not yet an end-of-day workflow

The data model is strong, but the operator experience needs a dedicated daily close:

- expected cash by driver;
- cash collected vs declared;
- shortfall, overage, and unresolved handover;
- receipts attached to the relevant shipment or deposit;
- exception notes and approvals;
- a signed-off daily position.

Without this, the cash ledger is a useful report rather than a control loop.

#### P1.4 No team membership flow

The product is sold as a workspace for an operations team, but there is no invite, accept, role-change, or remove flow. A company admin can create users globally, which is both a product gap and the security problem above.

#### P1.5 AI is not grounded in the operator's daily decisions

The current AI-adjacent features are:

- a RandomForest forecast;
- a deterministic weighted route optimizer;
- deterministic route explanations;
- receipt extraction through a real provider adapter;
- simulated weather and saved-route-only rerouting.

There is no grounded decision layer that combines these into a daily explanation of what changed, what is at risk, and what to do next. A generic chatbot would not solve that; a structured decision brief can.

#### P1.6 Local-language and low-bandwidth experience is missing

Public competitor signals show the importance of Amharic and local-language driver workflows. FreightPilot is English-only, and the browser console assumes a reasonably stable desktop connection.

The first localization priority should be the driver/cash flow, not a full site translation.

### P2 — Valuable after the wedge is proven

- real GPS/telematics partner integration;
- real traffic and weather providers;
- multi-vehicle/time-window optimization with OR-Tools or an equivalent solver;
- customer tracking and notification links;
- route benchmarking and anonymous lane intelligence;
- payment-gateway integrations where merchant reconciliation is verifiable;
- signed desktop installer and auto-update;
- full per-series forecast evaluation;
- advanced analytics, error monitoring, and product instrumentation;
- additional languages beyond the driver-first Amharic experience.

## 4. Unique value proposition

### 4.1 Recommended ICP

**Primary ICP:** Ethiopian private-fleet operators with approximately 5–50 vehicles and 20–300 daily delivery or transfer tasks.

Best-fit segments:

- FMCG and consumer-goods distributors;
- wholesalers and retail suppliers;
- manufacturers with regional warehouses;
- 3PLs that operate dedicated fleets for enterprise clients;
- courier/fulfilment operators that collect cash or reconcile driver returns.

Qualification signals:

- owns or directly manages drivers;
- uses spreadsheets, WhatsApp, phone calls, and paper notes today;
- has recurring routes and repeat customers;
- collects some cash on delivery or requires driver cash reconciliation;
- has a dispatcher and a finance/office person;
- feels pain from unassigned deliveries, late customer calls, or cash shortfalls.

### 4.2 Anti-ICP

Do not target initially:

- pure load-matching brokerages looking for a marketplace;
- companies that want FreightPilot to take custody of freight or provide escrow;
- enterprises requiring global carrier-network integrations;
- one-truck owner-operators with no dispatcher or office reconciliation process;
- buyers who primarily want a custom ERP or HR/payroll system.

### 4.3 Positioning statement

For Ethiopian distributors, wholesalers, and 3PLs running private fleets, FreightPilot is the cash-aware dispatch system that turns a day of routes into a proved, reconciled, auditable operating record. Unlike freight marketplaces, it does not require joining a network or changing how customers pay. Unlike global routing tools, it treats cash, bank-transfer evidence, and local operating constraints as first-class parts of the workflow.

### 4.4 Message hierarchy

Headline:

> **Plan the route. Prove the delivery. Reconcile the cash. Close the day.**

Subhead:

> FreightPilot is the cash-aware dispatch system for Ethiopian private fleets. Run the day from one workspace, without a marketplace, card payment, or a new settlement system.

Proof points:

1. Plan routes with the actual capacity and delivery demand you have today.
2. Give drivers a phone-first manifest that works through unreliable connectivity.
3. Capture photo/signature delivery proof.
4. See exactly how much cash each driver should be holding.
5. Reconcile bank-transfer evidence and close the day with an audit trail.
6. Ask why a route or forecast was recommended; get an answer tied to the actual inputs.

### 4.5 Why this is defensible

| Alternative | Their strength | Why FreightPilot wins for this ICP |
|---|---|---|
| Gerad / TOLO / ChiNet | Network, matching, carrier discovery, local-language and mobile investment | FreightPilot does not require joining a network, does not take settlement risk, and focuses on the shipper's own fleet, customers, proof, and cash close. |
| OptimoRoute / Onfleet | Mature route optimization, driver app, POD, live tracking | FreightPilot is ETB-first, cash-aware, bank-transfer-aware, lower entry cost, and designed around Ethiopian operating constraints rather than card-first global workflows. |
| Mager / Kelel / DreamTech | Local presence and custom delivery | FreightPilot is a repeatable product with self-serve activation, transparent pricing, and one improving workflow rather than a new custom build per customer. |
| project44 / FourKites | Enterprise visibility and integrations | FreightPilot is not trying to be a global control tower. It owns the last operational mile that global tools do not reconcile: driver cash and local payment evidence. |

## 5. Product model: one daily loop

The product should be designed around one repeatable loop:

### Morning — plan

- Import or create delivery orders.
- Assign vehicles and drivers.
- Optimize stops with capacity, time, and priority constraints.
- Produce a driver manifest with expected cash per stop.
- Flag unassigned or high-risk deliveries before dispatch.

### During the day — execute

- Driver receives manifest and route.
- Driver updates arrival, delivery, failure, and return states.
- Driver captures proof: photo, signature, recipient name, notes.
- Driver declares cash collected and any shortfall reason.
- Dispatcher receives exceptions and can reassign or escalate.

### Evening — close

- Office reviews each driver's expected vs declared vs handed-over cash.
- Attach bank-transfer or deposit evidence where relevant.
- Record shortfall, overage, and approval notes.
- Close the day with a signed operating record.

### Next morning — learn

- Review yesterday's exceptions, route performance, cash shortfalls, and unassigned demand.
- Get a grounded decision brief: what changed, what is at risk today, and what to do next.

This loop is the product. Every feature should either strengthen it or be deferred.

## 6. AI strategy

### 6.1 Principles

1. **Grounded:** every output references specific records and input values.
2. **Auditable:** the user can inspect why the recommendation exists.
3. **Human-approved:** no automatic dispatch, settlement, reversal, or customer-facing action.
4. **Provider-optional:** BYOK and deterministic fallback; the product must remain useful without an LLM.
5. **Measured:** every AI feature has a baseline, an evaluation set, latency, cost, and acceptance criteria.
6. **Honest:** simulated data is labeled; uncertainty is displayed; no invented metrics or reasoning.

### 6.2 AI-1 — Daily Decision Brief

**User:** owner, operations manager, dispatcher lead.

**Output:** a short, structured brief with three sections:

- **What changed:** late shipments, new exceptions, stock pressure, unassigned deliveries, cash still outstanding.
- **What is at risk today:** routes likely to miss promised windows, drivers with abnormal cash exposure, SKU/warehouse stock risk, customers with repeat failures.
- **What to do next:** two or three ranked actions, each linked to the underlying record and expected effect.

Implementation:

- deterministic fact bundle generated from the database first;
- optional LLM only rewrites the fact bundle into concise language;
- if no provider is configured, render the deterministic brief;
- no free-form database queries from the model.

Acceptance:

- every claim links to a record or a calculated metric;
- the brief renders on a low-bandwidth connection within the existing dashboard budget;
- no recommendation can mutate state without an explicit user action;
- a fallback brief is always available.

Do not build a generic “chat with your logistics data” interface first.

### 6.3 AI-2 — Cash Risk Radar

**User:** owner/finance/operations.

**Output:** a ranked list of drivers and routes by likelihood and size of end-of-day cash shortfall.

Inputs:

- expected COD amount;
- historical declared vs expected cash;
- route duration and stop count;
- late/exception history;
- previous unresolved shortfalls;
- driver tenure/status and handover timing.

Start with a transparent rules/statistical model, not an LLM:

- high expected cash + high stop count + late route + prior shortfall = elevated risk;
- show the contributing factors;
- avoid using protected or irrelevant personal attributes.

Acceptance:

- the score is explainable at the factor level;
- finance can record an override reason;
- the model never blocks a driver or makes a fraud accusation automatically.

### 6.4 AI-3 — Exception Triage

**User:** dispatcher.

**Output:** a prioritized exception queue with a suggested next action.

Suggested actions:

- call driver;
- reassign stop;
- notify customer;
- split route;
- mark stock exception;
- open cash review.

Implementation:

- deterministic rules based on exception type, age, customer impact, and cash exposure;
- optional language model only for summarizing notes;
- operator confirms every action.

### 6.5 AI-4 — “Why this route?”

FreightPilot already has a strong foundation in `route_explanations.py`. Extend it to:

- explain the chosen sequence, runner-up, capacity and stop exclusions;
- compare two scenarios side by side;
- identify which assumption would change the decision;
- show whether the result depends on synthetic or real data.

This is a credible differentiator because it is deterministic and inspectable.

### 6.6 AI-5 — Forecast quality by series

The current aggregate WAPE caveat is honest but not sufficient for a dispatcher. Add:

- per-warehouse/SKU backtest error where enough history exists;
- explicit “not enough history” states;
- forecast ranges in the replenishment approval screen;
- a warning when the model is relying on synthetic weather;
- a simple baseline comparison (rolling average vs model).

### 6.7 AI-6 — Receipt and invoice evidence assistant

Already partially real:

- bank-transfer receipt extraction;
- confidence flags;
- duplicate/reference checks;
- verification queue.

Next steps:

- attach the original evidence to the audit timeline;
- surface ambiguous fields and require human verification;
- add clear provider/fallback status;
- never auto-verify money movement solely from an OCR result.

### 6.8 AI evaluation harness

Before shipping any recommendation feature, add:

- a golden set of synthetic and real pilot cases;
- expected facts and acceptable actions;
- hallucination checks;
- latency and cost measurements;
- provider outage/fallback tests;
- an explicit review of every AI-generated customer-facing string.

## 7. Competitive position

### 7.1 Where not to compete

- **Do not build a load marketplace.** Gerad, TOLO, and ChiNet are already building network liquidity. A new network is expensive, slow, and exposes FreightPilot to working-capital risk.
- **Do not build escrow.** The Kobo360/Lori/Sendy experience shows how payment timing can destroy an otherwise useful logistics platform.
- **Do not compete on enterprise control-tower breadth.** project44/FourKites have years of integration depth and enterprise sales.
- **Do not lead with “AI agents.”** The current data foundation does not support autonomous claims, and buyers in this segment need proof more than novelty.

### 7.2 Where to compete

FreightPilot should own the **private-fleet daily close**:

- plan the route;
- execute with a driver;
- prove the delivery;
- reconcile the cash;
- explain the decision;
- preserve the audit record.

This is a narrower product with a clearer buyer, measurable value, and a natural expansion path.

## 8. 12-week execution plan

### Phase 0 — Trust reset (weeks 1–2)

**Outcome:** the product and public surface tell the truth, and the tenant boundary is safe enough for pilots.

Tickets:

1. `SEC-01` — **DONE locally** — Close the org-less/global-admin tenant escape.
2. `SEC-02` — **PARTIAL** — Membership and org-less denial are fail-closed; the legacy NULL-row read cleanup and explicit data backfill remain.
3. `REL-01` — **DONE** — Full backend suite, tenant-scope tests, migration smoke, ruff, mypy, and console gates.
4. `TRUTH-01` — **DONE** — Remove or explicitly label simulated weather, rerouting, and any invented carrier/cost output.
5. `WEB-01` — **DONE locally** — Docs/API/Desktop links, `/docs`, and the privacy, terms, security, and status routes are present; legal review remains a launch task.
6. `BRAND-01` — **DONE** — Console title and user-facing wording are branded.
7. `DOC-01` — **PARTIAL** — The state file records the retired swarm process; older plan documents still contain stale references.

Exit criteria:

- a tenant admin cannot create or reach an unaffiliated cross-tenant user;
- no public surface links to a 404;
- no simulated feature is presented as live intelligence;
- all release gates have fresh evidence.

### Phase 1 — Cash-Aware Dispatch MVP (weeks 2–6)

**Outcome:** a private fleet can run one real day from order intake to cash close.

Tickets:

1. `DISP-01` — Customer, delivery order, delivery stop, recipient, and address model.
2. `DISP-02` — Multi-stop route input from delivery orders, including capacity, time windows, service time, and priority.
3. `DISP-03` — Driver manifest and assignment.
4. `DISP-04` — Offline-first driver PWA with idempotent sync and a conflict policy.
5. `DISP-05` — Photo/signature/recipient proof of delivery, stored outside the relational database in object storage.
6. `DISP-06` — Cash collected/deposited declaration from the driver flow.
7. `DISP-07` — End-of-day reconciliation board: expected, declared, handed over, shortfall, overage, approval, and audit.
8. `DISP-08` — Exception states for failed delivery, partial delivery, return to depot, and unassigned stop.
9. `DISP-09` — Amharic-first driver labels and low-bandwidth UX.
10. `DISP-10` — Customer tracking link with status and proof visibility, permission-scoped.

Exit criteria:

- one pilot can plan a real multi-stop day from customer orders;
- a driver can complete the day on a phone with intermittent connectivity;
- every completed COD stop has a proof record and a cash declaration;
- the office can close the day and see every shortfall;
- no cash figure depends on a free-text field alone.

### Phase 2 — Grounded Decision Brief (weeks 5–9)

**Outcome:** the product proactively tells the operator what matters, with evidence.

Tickets:

1. `AI-01` — Fact-bundle service for yesterday/today/tomorrow.
2. `AI-02` — Deterministic Daily Decision Brief.
3. `AI-03` — Optional BYOK LLM summarization with structured schema and fallback.
4. `AI-04` — Cash Risk Radar with factor explanations.
5. `AI-05` — Exception triage and suggested action queue.
6. `AI-06` — Route scenario comparison and “what would change this decision?” explanation.
7. `AI-07` — Per-series forecast quality and baseline comparison.
8. `AI-08` — Evaluation harness and monitoring.

Exit criteria:

- every statement links to a record or a calculated fact;
- every suggestion is advisory and requires human confirmation;
- the brief remains useful with no LLM provider configured;
- the evaluation set shows no unsupported factual claim;
- operators can dismiss or correct the recommendation and the reason is recorded.

### Phase 3 — Pilot hardening (weeks 8–11)

**Outcome:** five to eight design partners run real workflows and produce evidence.

Tickets:

1. `PILOT-01` — Recruit five to eight qualified private fleets.
2. `PILOT-02` — Baseline and instrument dispatch time, unassigned deliveries, POD completion, cash close time, shortfall, and route distance/time.
3. `PILOT-03` — Onboarding templates for CSV, customer locations, drivers, and opening cash.
4. `PILOT-04` — Support runbook and weekly operating review.
5. `PILOT-05` — Privacy, driver consent, data retention, and export policy.
6. `PILOT-06` — Real case study only after measured results exist.

Exit criteria:

- at least three pilots complete four consecutive weeks;
- at least 70% of completed routes have same-day POD and cash close;
- dispatch planning time is materially lower than baseline;
- customers can articulate the cash/proof value in their own words;
- at least three pilot customers are willing to pay or sign a paid pilot.

### Phase 4 — Packaging and launch decision (weeks 11–12)

**Outcome:** decide whether to scale, narrow, or reposition based on evidence.

Deliverables:

- updated pricing and packaging;
- sales narrative and demo script;
- documented pilot ROI;
- support and onboarding model;
- go/no-go decision for paid launch;
- refreshed competitive research.

## 9. Pricing and packaging

The current ladder has two strategic problems:

1. **It is usage-only.** Free and Starter share the same included units; paid tiers mostly differ by cycle and overage treatment. The buyer cannot see why the product is worth more as the fleet grows.
2. **The quarterly prices create a confusing effective rate.** Scale at 10,000 ETB per quarter is roughly 3,333 ETB/month, below Starter at 4,500 ETB/month, while including more tasks. That can cannibalize Starter and invite negotiation.

Recommended packaging hypothesis to test with pilots:

| Tier | Audience | Value anchor |
|---|---|---|
| **Free** | One dispatcher proving the workflow | First route, sample data, limited records |
| **Starter** | Small private fleet | Up to 10 drivers, COD close, route planning, basic proof |
| **Growth** | Multi-route distributor/3PL | Up to 30 drivers, multi-warehouse, Decision Brief, exports, proof retention |
| **Enterprise** | Larger operator or group | SSO, SLA, custom onboarding, audit/data controls, dedicated support |

Price on a mix of:

- active drivers;
- delivery tasks;
- enabled control features (cash close, proof, AI brief);
- support tier.

Do not finalize pricing until pilots reveal the real willingness to pay and the support cost per account.

## 10. Metrics

### North Star

**Verified delivery-and-cash cycles closed per week.**

This measures the actual value loop, not logins or messages.

### Activation

- first optimized route within 10 minutes;
- first real data import within 7 days;
- first driver manifest sent within 14 days;
- first same-day cash close within 21 days.

### Operational value

- delivery tasks with proof of delivery;
- same-day cash-close rate;
- shortfall ETB per 1,000 ETB collected;
- unassigned delivery rate;
- dispatch planning minutes per route;
- route distance/time vs baseline;
- exception resolution time;
- customer notification/ETA accuracy (only when real tracking exists).

### AI value and safety

- Decision Brief open rate;
- recommendation acceptance/dismissal rate;
- route explanation usage;
- forecast error by series, not only aggregate;
- cash-risk precision/recall in pilot;
- provider outage fallback success;
- unsupported-claim rate in evaluation;
- latency and cost per brief.

### Commercial

- pilot-to-paid conversion;
- gross margin per account;
- onboarding days to first value;
- weekly active dispatchers;
- team seats per workspace;
- retention by tier.

## 11. Risks and mitigations

| Risk | Severity | Mitigation |
|---|---|---|
| Cross-tenant access through org-less users | Critical | Membership-required business endpoints; fail-closed scoping; separate platform-admin plane; regression tests. |
| Marketplace temptation dilutes focus | High | Explicit anti-ICP; no load matching, carrier network, escrow, or guaranteed payouts in the first year. |
| AI claims outrun evidence | High | Grounded facts, audit links, human approval, evaluation harness, simulated-data labels. |
| Driver adoption fails | High | Amharic-first, extremely simple PWA/Telegram flow, offline sync, pilot with real drivers before building more manager features. |
| Address/customer data is incomplete | High | Support landmark/phone/region addresses; allow manual pin + notes; do not require a perfect national address system. |
| Cash handling creates fraud/dispute risk | High | Keep custody with the operator; record evidence and approvals; never accuse or auto-block; separate roles for declare vs settle. |
| Payment integrations expand scope | Medium | Treat telebirr/Chapa as optional evidence sources, not a settlement business, until merchant reconciliation is proven. |
| Custom requests pull the product toward services | Medium | Productize only recurring requests; maintain a clear anti-ICP and change-control gate. |
| Support economics are poor for small fleets | Medium | Self-serve onboarding, templates, partner-assisted setup, and a minimum viable paid tier. |
| Public site and docs undermine credibility | Medium | Fix docs/API/legal/status links before outbound sales. |
| Current branch and deployment state are unclear to buyers | Medium | Separate “shipped” and “planned” claims; release only with evidence. |

## 12. Decisions required from the founder

1. **Confirm the ICP:** private fleets first, not marketplaces.
2. **Choose the first operating corridor:** Addis same-day distribution versus Addis–Djibouti/inter-city replenishment.
3. **Confirm the cash boundary:** FreightPilot records and reconciles cash; it does not hold, lend, or guarantee funds.
4. **Choose the driver surface:** offline-first PWA first, Telegram bot as an additional notification/entry channel, native app later.
5. **Choose the language wedge:** Amharic driver UX first; full console localization later.
6. **Confirm the AI promise:** grounded decision support, not autonomous dispatch.
7. **Choose the first paid package:** pilot pricing before locking a public ladder.

## 13. Immediate next actions

1. Fix the tenant boundary and add regression tests.
2. Run the full release gates and do not merge the current AI branch until they are green.
3. Keep weather explicitly labelled simulated and rerouting limited to saved-route candidates.
4. Fix the public docs/API/footer links and brand title.
5. Approve the “cash-aware dispatch for private fleets” position.
6. Recruit five to eight design partners in the target ICP.
7. Model customer, delivery order, stop, proof, and cash handover as first-class entities.
8. Build the end-of-day reconciliation board before adding more dashboards.
9. Define the pilot baseline and the North Star metric.
10. Delay load matching, escrow, and enterprise control-tower claims.

## 14. Bottom line

FreightPilot does not need to become a bigger version of every competitor. It needs to become unmistakably better at one recurring Ethiopian operating problem:

> **A private fleet finishes the day knowing every route was executed, every delivery was proved, and every driver's cash was reconciled.**

That is a product with a real buyer, a measurable outcome, a defensible local data advantage, and a credible AI story. It is also a product that can be built from the current codebase without taking on marketplace liquidity or working-capital risk.
