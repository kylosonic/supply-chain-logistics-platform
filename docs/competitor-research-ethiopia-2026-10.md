# Competitive Research — Ethiopia and Adjacent Logistics Platforms

**Research date:** 2026-10-21  
**Method:** direct review of public product websites, pricing pages, and 2026 Ethiopian market reporting.  
**Important limitation:** company capability, scale, coverage, and outcome figures are public marketing or interview claims unless explicitly described as audited evidence. They are useful for positioning and feature comparison, not as verified market facts.

## 1. Why this research exists

The prior competitive notes focused mostly on global enterprise control towers: project44 and FourKites. That is useful for understanding category language, but it is not FreightPilot's actual competitive set.

FreightPilot's real competition in Ethiopia is:

1. spreadsheets, phone calls, paper delivery notes, WhatsApp/Telegram coordination, and cash;
2. Ethiopian freight marketplaces and load boards;
3. local custom-software companies that build fleet systems project by project;
4. global SMB route-planning tools sold in USD with card billing and no local cash/bank workflows;
5. global enterprise visibility platforms with long implementations and opaque pricing.

The key strategic question is therefore not “how do we look like project44?” It is:

> Which operational job is still badly served by all of the above, and where can FreightPilot build a repeatable product rather than a custom project?

## 2. Market context: the payment rail is moving faster than the trust layer

### 2.1 Digital payments are growing, but logistics and proof remain the bottleneck

Ethiopian Business Review reported in May 2026 that Ethiopia has made significant progress in digital payments, but e-commerce and distribution are still constrained by:

- fragmented fulfilment and last-mile delivery;
- weak address systems;
- consumer trust and dispute-resolution gaps;
- a strong preference for cash;
- low digital literacy in parts of the market;
- the need to prove delivery, not merely accept payment.

The same report cited approximately:

- 57 million telebirr subscribers;
- 34.2 million CBE Birr users;
- 10,000+ Chapa merchants;
- 358,000 telebirr agents;
- 344,000 telebirr merchants.

The strategic implication is direct: **payments are no longer the only scarce layer. Delivery proof, cash custody, reconciliation, and operational trust are.**

Source: [Ethiopian Business Review — Ethiopia's E-Commerce Expansion Held Back by Logistics, Trust Gaps](https://ethiopianbusinessreview.net/ethiopias-e-commerce-expansion-held-back-by-logistics-trust-gaps-despite-digital-payment-growth-experts-say/)

### 2.2 The trucking market still runs on informal coordination

A January 2026 Capital interview with TOLO Freight described the Ethiopian trucking market as follows:

- the market is still largely coordinated through phone calls, paper documents, and cash deals at truck stations;
- trucks reportedly run empty 30–40% of the time;
- roughly 95% of international trade moves through the Ethiopia–Djibouti corridor;
- small shippers often cannot discover fair market prices;
- forcing digital settlement onto a cash-based market has been a failure mode for African logistics platforms.

TOLO's response is a multilingual marketplace with offline settlement, reputation, documentation, and proof of delivery. Those are public interview claims and should be validated independently before being used as market sizing.

Strategic implication: **cash and offline settlement are not temporary bugs to eliminate. They are operating constraints the product must model.**

Source: [Capital — Digital logistics disruptor rewires Ethiopia's trucking chain](https://capitalethiopia.com/2026/01/11/digital-logistics-disruptor-rewires-ethiopias-trucking-chain/)

### 2.3 The African freight-marketplace model has a working-capital trap

An April 2026 All Business Africa report examined the first wave of venture-backed African digital freight platforms, including Kobo360, Lori Systems, and Sendy. The central finding:

- the platforms improved discovery and utilization in theory;
- many were caught between paying drivers quickly and collecting from shippers 30–90 days later;
- that working-capital gap required continuous financing;
- when financing tightened, driver payments, supply, and customer service deteriorated together;
- Sendy shut down in 2023, and Kobo360 was later bought back at a severely reduced outcome.

The report's conclusion is important for FreightPilot: software can improve coordination, but a business that takes custody of freight, guarantees driver payment, or runs an escrow network also takes on a finance company's balance-sheet risk.

Strategic implication: **FreightPilot should be an asset-light operations and reconciliation layer, not a freight marketplace or escrow provider in its first phase.**

Source: [All Business Africa — African Road Freight and Trucking 2026](https://allbusiness.africa/insights/african-road-freight-trucking-2026)

## 3. Competitive map

### 3.1 Direct local freight marketplaces

| Platform | Public positioning | Publicly visible capabilities | Gap / opening for FreightPilot |
|---|---|---|---|
| **Gerad Logistics** | “Ethiopia's Future Digital Freight Network”; nationwide shipper/driver/fleet matching | Shipper and driver Apps, verified drivers, load posting, bids/matching, live tracking claims, Chapa/Addis Pay/bank transfer, escrow language, Telegram bot, fleet portal, driver/team management, load approvals, earnings/payout tracking | Network marketplace first. Public claims emphasize escrow and “no cash accepted,” while much of Ethiopian freight still settles offline. FreightPilot can serve private fleets that do not want to join a marketplace or move settlement to escrow. |
| **TOLO Freight** | Homegrown digital freight marketplace; “separate matching from settlement” | Load posting, algorithm pricing and bids, carrier verification/deposits, multilingual UI (Amharic, Oromiffa, Tigrinya, English), ratings, digital contracts, checkpoint tracking, document capture, POD, offline settlement | Strong local-language and corridor thinking. Marketplace and deposit model still require network density, trust, and carrier supply. FreightPilot can focus on the shipper's own fleet and existing customer relationships. |
| **ChiNet** | “Modern transport and logistics solutions”; all-in-one platform for shippers, carriers, brokers | Load/truck search, bidding, TMS, shipment/order management, live tracking claims, role-based operations, web/mobile apps, public Starter load-board price starting at $19/month | Marketplace/TMS breadth but public site contains broad, sometimes generic claims. FreightPilot can differentiate through cash evidence, auditability, and private-fleet workflow depth rather than load-board breadth. |

Public links:

- [Gerad Logistics](https://gerad.app/)
- [TOLO Freight interview](https://capitalethiopia.com/2026/01/11/digital-logistics-disruptor-rewires-ethiopias-trucking-chain/)
- [ChiNet](https://chinetlink.et/)

### 3.2 Local custom-software companies

| Company | Public positioning | Relevance | Gap / opening |
|---|---|---|---|
| **Mager Software** | Addis Ababa enterprise software company; healthcare flagship plus custom enterprise systems | Logistics page advertises fleet dispatch, route optimization, warehouse management, delivery tracking, and driver mobile apps | Project-led custom delivery, not a self-serve product with transparent pricing, sample-data onboarding, or a repeatable cash-reconciliation workflow. |
| **Kelel IT Solutions** | Remote-first IT solutions; custom software, banking, insurance, fleet systems | Fleet page advertises vehicles, drivers, dispatch, trips, maintenance, fuel, tires, service reminders, customer tracking, dashboards, HR/finance | Broad custom-system promise; no visible product pricing, trial, activation path, or local bank-receipt reconciliation as a packaged capability. |
| **DreamTech** | Ethiopian software and AI project company | Public search results advertise logistics and transport software including route optimization and fleet management | Service-led model; productization and repeatable onboarding remain the opening. |

Public links:

- [Mager logistics software](https://magersoftware.com/logistics-transport-software-ethiopia)
- [Kelel fleet management](https://kelelitsolution.com/solutions/fleet-management-system-ethiopia)
- [DreamTech](https://dreamtech.et/)

### 3.3 Global SMB route and last-mile tools

| Platform | Public pricing observed | Visible capabilities | Gap / opening |
|---|---|---|---|
| **OptimoRoute** | Lite $35.10/driver/month billed annually; Pro $44.10/driver/month billed annually; 30-day trial | 700–1,000 orders per plan, route history, driver app, live tracking, ETA/breadcrumbs, POD, customer feedback, analytics | Strong route engine and self-serve trial, but no ETB pricing, CBE/Dashen receipt reconciliation, COD driver-cash custody, or Ethiopian operating model. |
| **Onfleet** | Launch from $619/month for 2,500 tasks; Scale from $1,349/month for 5,000; Enterprise from $3,099/month | Unlimited users, driver app, POD, chat, route optimization, auto-dispatch, notifications, command center, integrations | Excellent last-mile orchestration, but high fixed cost and card/cloud-first assumptions. Ethiopian SMB fleets need a lower entry point and cash/receipt truth. |

Public links:

- [OptimoRoute pricing](https://optimoroute.com/pricing/)
- [Onfleet pricing](https://onfleet.com/pricing)

### 3.4 Global enterprise visibility and control towers

The existing FreightPilot research already covers project44 and FourKites:

- enterprise-only pricing;
- long integration and onboarding projects;
- global carrier/telematics networks;
- enterprise visibility, ETA, yard, ocean, air, and exception narratives;
- no meaningful Ethiopia-first payment, cash, or bank-transfer workflow.

They validate the category language around exceptions and decision intelligence, but they are not the right product template for a 5–50 vehicle Ethiopian private fleet.

Source: [existing FourKites/project44 research](./competitor-research-fourkites-project44.md)

## 4. Capability comparison

Legend: **●** strong public capability, **◐** partial or claim-dependent, **○** absent / unclear, **—** not core.

| Capability | Gerad | TOLO | ChiNet | OptimoRoute | Onfleet | Mager/Kelel | FreightPilot today |
|---|---:|---:|---:|---:|---:|---:|---:|
| Freight marketplace / load board | ● | ● | ● | ○ | ○ | ○ | ○ |
| Private-fleet workspace | ◐ | ◐ | ◐ | ● | ● | ● | ● |
| Route optimization | ○ | ◐ | ◐ | ● | ● | ◐ | ◐ (warehouse-to-warehouse greedy optimizer) |
| Customer stop / time-window routing | ○ | ◐ | ○ | ● | ● | ◐ | ○ |
| Driver mobile experience | ● | ● | ● | ● | ● | ◐ | ○ |
| Live GPS / telematics | ● (claimed) | ◐ (checkpoint updates) | ● (claimed) | ● | ● | ◐ | ◐ (ingest endpoint; no native device integration) |
| Proof of delivery / photo / signature | ◐ | ● | ○ | ● | ● | ◐ | ○ (reference field only) |
| COD / driver cash custody | ○ | ◐ (offline settlement) | ○ | ○ | ○ | ○ | ● (ledger exists; no mobile capture flow) |
| Bank-transfer receipt verification | ○ | ○ | ○ | ○ | ○ | ○ | ● |
| ETB pricing / local billing | ○ | ○ | — | ○ | ○ | ○ | ● |
| Multi-tenant audit and governance | ◐ | ○ | ◐ | ○ | ◐ | ◐ | ● |
| AI decision support | ○ | ○ | ○ | ◐ | ◐ | ○ | ◐ (forecasting + receipt extraction; no grounded copilot) |
| Local-language driver UX | ◐ (EN/Amharic) | ● (four languages claimed) | ○ | ○ | ○ | ◐ | ○ |
| Offline / low-bandwidth operation | ○ | ◐ | ○ | ◐ | ○ | ○ | ○ |
| Public docs / API reference | ○ | ○ | ○ | ● | ● | ○ | ○ (live site links are broken) |

The table is intentionally conservative. “Claimed” means the vendor advertises the capability publicly but this research did not verify production behavior, coverage, or outcome quality.

## 5. What the market is telling us

### 5.1 The marketplace lane is crowded and capital-intensive

Gerad, TOLO, and ChiNet are all building networks of shippers, carriers, and brokers. Competing there requires:

- carrier supply density;
- verified identity and documents;
- pricing/bidding liquidity;
- dispute handling;
- payment/escrow trust;
- working-capital discipline.

That is a different company from a SaaS operations platform. It also carries the exact working-capital risk documented in the Kobo360/Lori/Sendy cases.

### 5.2 Global tools solve routing, not the Ethiopian cash close

OptimoRoute and Onfleet are credible routing products. They do not solve:

- a driver collecting cash and handing it back to the office;
- an office reconciling a CBE or Dashen bank transfer against a subscription invoice;
- a dispatcher working with Ethiopian addresses, phone-first coordination, and intermittent connectivity;
- a manager who needs an auditable explanation of why a route, forecast, or exception action was chosen.

FreightPilot should not try to beat them at generic route optimization breadth. It should beat them at the **cash-and-proof loop around the route**.

### 5.3 Local custom vendors prove demand but not productization

Mager, Kelel, and DreamTech advertise many of the same modules. Their model is project discovery, custom scope, integration, and support. FreightPilot's opening is:

- self-serve activation with sample data;
- a repeatable operating workflow;
- transparent ETB pricing;
- a product that can be improved for every customer at once;
- auditable controls rather than a one-off admin console.

### 5.4 The strongest gap is not “AI.” It is trustworthy closure

The market already has dashboards and AI claims. What it lacks is a simple answer to the end-of-day operator question:

> Which routes were completed, which deliveries are proved, which drivers are still holding cash, and what is the shortfall?

That question connects dispatch, field execution, finance, and audit. It is a better foundation for AI than a generic chatbot.

## 6. Implications for FreightPilot

### Recommended position

**FreightPilot is the cash-aware dispatch system for Ethiopian private fleets.**

It helps distributors, wholesalers, and 3PLs:

1. plan the day's routes;
2. give drivers a phone-first manifest;
3. capture delivery proof;
4. record cash collected and returned;
5. reconcile bank-transfer evidence; and
6. close the day with an auditable operating record.

### What not to become

- not a load marketplace;
- not an escrow or lending business;
- not a generic ERP replacement;
- not an “autonomous dispatch” product;
- not a dashboard that claims live GPS, weather, or AI capability it cannot substantiate.

### Defensible advantage

The durable advantage is not the route algorithm alone. It is the combination of:

- a private-fleet workflow;
- local payment evidence;
- driver cash custody;
- proof-of-delivery records;
- exception history;
- route/forecast/decision explanations;
- an auditable operating dataset that improves recommendations over time.

That dataset is difficult for a horizontal global routing vendor to replicate and does not require FreightPilot to carry marketplace working capital.

## 7. Research caveats

- Public vendor claims are not audited. Treat coverage, scale, savings, and automation percentages as marketing until independently validated.
- Pricing changes frequently; the figures above are the public prices visible on 2026-10-21.
- The TOLO interview is a founder interview, not an independent market study.
- The Ethiopian Business Review figures are reported speech from a symposium, not a primary statistical release.
- The existing project44/FourKites research is dated August 2026 and should be refreshed before enterprise sales.
