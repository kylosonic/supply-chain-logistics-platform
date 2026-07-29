# Market-Dominator Overhaul Implementation

## Intent

This repository was overhauled to follow the strongest public patterns used by leading logistics platforms while keeping FreightPilot's own product identity.

The goal was not to copy any one vendor. The goal was to combine the winning structural moves:

- project44-style enterprise decision-intelligence presentation
- FourKites-style autonomous resolution framing
- Onfleet-style pricing and ROI clarity
- Bringg-style platform plus services packaging
- Route4Me-style operational breadth and scenario orientation
- Shippeo-style rollout trust and implementation seriousness

## Business model decisions implemented

FreightPilot now presents as a tiered B2B SaaS product with:

- clear starter, scale, and enterprise packaging
- visible usage-aware economics via task metering and ROI modeling
- workspace governance as part of the core offer, not an afterthought
- BYOK provider control as a differentiation point against vendor lock-in
- desktop launch readiness as a first-class operator workflow

## Public website changes

Implemented in:

- `apps/product-web/src/App.tsx`
- `apps/product-web/src/index.css`

Key changes:

- Rebuilt the site around a decision-intelligence control-tower story instead of a generic feature list.
- Introduced platform-family framing: Control Tower, Decision Studio, Launch Cockpit, and Revenue Guard.
- Kept the signup flow and ROI calculator, but moved them into a more enterprise-grade narrative.
- Shifted the visual language to a darker, more executive interface inspired by category leaders.
- Kept copy grounded in existing FreightPilot capabilities instead of publishing unsupported market claims.

## Operations console changes

Implemented in:

- `apps/ops-console/src/components/Layout.tsx`
- `apps/ops-console/src/pages/DashboardPage.tsx`
- `apps/ops-console/src/pages/LoginPage.tsx`
- `apps/ops-console/src/pages/RoutesPage.tsx`
- `apps/ops-console/src/pages/AlertsPage.tsx`
- `apps/ops-console/src/pages/ShipmentsPage.tsx`
- `apps/ops-console/src/pages/PlanningPage.tsx`
- `apps/ops-console/src/pages/UploadPage.tsx`
- `apps/ops-console/src/pages/AccountPage.tsx`
- `apps/ops-console/src/components/CsvUploadPanel.tsx`
- `apps/ops-console/src/components/RouteOptimizerForm.tsx`
- `apps/ops-console/src/components/RouteMap.tsx`
- `apps/ops-console/src/components/RouteSchedulesTable.tsx`
- `apps/ops-console/src/components/ForecastChart.tsx`
- `apps/ops-console/src/components/InventoryCharts.tsx`
- `apps/ops-console/src/components/ui/*`
- `apps/ops-console/src/index.css`

Key changes:

- Replaced the utilitarian shell with a control-tower workspace frame.
- Elevated the dashboard into an exception-led operations surface.
- Added scenario-comparison feedback to route optimization.
- Restyled routes, alerts, shipments, planning, upload, and workspace pages into one coherent operator system.
- Brought subscription usage and provider-key governance into the same visual language as day-to-day operations.

## Backend insight layer changes

Implemented in:

- `apps/platform-api/app/models/audit_event.py`
- `apps/platform-api/app/models/route_history.py`
- `apps/platform-api/app/services/audit.py`
- `apps/platform-api/app/schemas/ops_insights.py`
- `apps/platform-api/app/schemas/route.py`
- `apps/platform-api/app/api/endpoints/auth.py`
- `apps/platform-api/app/api/endpoints/routes.py`
- `apps/platform-api/app/api/endpoints/alerts.py`
- `apps/platform-api/app/api/endpoints/shipments.py`
- `apps/platform-api/app/api/endpoints/planning.py`
- `apps/platform-api/app/api/endpoints/providers.py`
- `apps/platform-api/app/api/endpoints/subscriptions.py`
- `apps/platform-api/app/api/endpoints/ops.py`

Key changes:

- Added a reusable audit-event model and service for workspace and operational actions.
- Added route optimization run history so every scenario can be reviewed after execution.
- Added a unified exception-feed API that combines unresolved alerts, pending replenishment approvals, and route runs with unassigned deliveries.
- Extended existing mutation endpoints so route, alert, shipment, planning, provider, subscription, and workspace events are recorded consistently.

## Performance and test changes

Implemented in:

- `apps/ops-console/src/App.tsx`
- `apps/ops-console/vite.config.ts`
- `apps/ops-console/src/pages/workspaceSurfaces.smoke.test.tsx`
- `apps/product-web/src/App.smoke.test.tsx`
- `apps/platform-api/tests/test_operator_insights_api.py`

Key changes:

- Added lazy route loading in the ops console.
- Split chart and map libraries into dedicated bundles and removed stale compiled `.js` files that were shadowing TypeScript sources.
- Added backend tests for the new insight endpoints.
- Added lightweight render smoke tests for the redesigned ops-console and product-web surfaces.

## Desktop launch workstation changes

Implemented in:

- `apps/desktop/src/onboarding.html`
- `apps/desktop/src/onboarding.css`

Key changes:

- Reframed the desktop app as a rollout workstation instead of a plain setup form.
- Added stronger visual separation between connection setup, readiness state, sign-off, and launch flow.
- Preserved every existing script hook and button action while improving the workstation information hierarchy.

## Validation completed

- `npm --prefix apps/product-web run build`
- `npm --prefix apps/product-web run test`
- `npm --prefix apps/ops-console run build`
- `npm --prefix apps/ops-console run test`
- `npm --prefix apps/desktop run doctor`
- `python -m pytest tests/test_mvp_features_api.py tests/test_route_usage_metering_api.py tests/test_subscription_metering_api.py tests/test_operator_insights_api.py -q`

Desktop HTML and CSS were also checked through editor diagnostics after the redesign.

## Result

FreightPilot now reads and behaves much more like a serious logistics platform:

- stronger enterprise commercial posture
- clearer packaging and ROI story
- more credible operator-facing control surfaces
- better desktop rollout experience
- more cohesive design language across public site, console, and desktop shell