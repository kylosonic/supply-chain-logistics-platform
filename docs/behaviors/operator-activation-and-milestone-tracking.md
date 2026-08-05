# Operator Activation & Milestone Tracking — Living Behaviors

> ⚠️ **NOT YET IMPLEMENTED** — This document describes locked-in product behaviors that are not yet built. Engineering work must be triggered by `@architect` after reviewing the gap tickets in `docs/behaviors/pending-behaviors.md`. Every rule below is written from the user's perspective (state, actions, consequences), not implementation mechanics.

## 1. Why this feature exists

FreightPilot's current dashboard shows 11 panels of empty KPIs to a brand-new operator. The five upload steps required before any panel produces value are presented as a 5-card sequence on a separate page. There is no guided onboarding path, no progressive disclosure, no first-aha moment marker, and no upgrade-intention signal tied to usage.

This feature transforms the signup-to-value journey from "wall of zeros" into a guided milestone loop. It is the activation half of the cashflow engine: a customer who never reaches their first route optimization never feels the value; a customer who never feels the value never upgrades; a customer who never upgrades never pays.

The cashflow behavior (see [`cashflow-bank-transfer-receipt-verification.md`](./cashflow-bank-transfer-receipt-verification.md)) and this behavior are mutually reinforcing — activation drives the usage that triggers the hard-lock, the hard-lock drives the upgrade pitch, and the upgrade pitch opens the trial-to-invoice flow.

## 2. The actors and their roles

- **Customer (any role within the organization):** signs up, sees the activation surface, optionally runs first actions on sample data, uploads real CSVs progressively, runs their first real route optimization, graduates when the activation checklist completes.
- **Admin (organization-level admin role):** can reset the workspace back to sample-data-seeded state if a teammate uploaded garbage CSVs. Cannot bypass the activation flow for any user in their org.
- **System (FreightPilot):** seeds the new workspace with sample data, tracks per-organization milestone state, reveals dashboard panels progressively, surfaces the activation banner persistently, hard-locks Free-tier writes at the cap, fires the soft and hard upgrade pitches at the locked-in trigger states.

## 3. Sample data seeding on signup

### 3.1 What "sample data" means

Every new customer workspace is seeded with sample data sourced from the existing `sample-data/` directory shipped with the product (the CSV files already present in the repository root: warehouses, items, fleet assets, inventory, orders). The seed is per-workspace, not a shared demo tenant.

After seeding, the new customer can immediately see populated dashboards, run forecasts, run route optimizations, and acknowledge alerts — every operational surface works against sample data without the customer having to upload anything.

### 3.2 The "demo data" banner

A persistent banner appears on the dashboard the moment the customer signs up, and remains visible until every sample-data row has been replaced by a real upload.

The banner communicates three things:
- "You're viewing a demo workspace with sample data."
- "Upload your real CSVs to start replacing the demo with your operation."
- A one-click call to action → the `/upload` page.

The banner never hides itself, never minimizes, and cannot be dismissed by the user. It stays present on every dashboard view until the workspace is fully the customer's own data.

### 3.3 Sample data is operationally usable, not gated

The customer can perform every write operation on sample data — run route optimizations, acknowledge alerts, approve replenishment plans, set provider keys, change subscription tier, run forecasts. All these operations consume the same meters as real data and write the same audit trail.

There is no "demo mode" distinction anywhere in the system — sample data is just data the system seeded rather than data the customer uploaded. Meters, locks, and audit log treat all data the same.

### 3.4 What happens when real uploads begin

When the customer uploads their first real CSV (e.g., warehouses), the system replaces the seeded sample warehouses with the uploaded rows. The other data categories (items, fleet, inventory, orders) remain sample data until the customer uploads those too. The customer's workspace is now in a "partial sample" state.

The dashboard banner updates to communicate: "You're viewing a partial demo workspace — 1 of 5 data categories is yours. Upload more to complete your real operation."

As more CSVs upload, more sample categories are replaced. The dashboard banner updates to "2 of 5", "3 of 5", and so on. When all five categories have real data uploaded, the banner disappears entirely.

### 3.5 No lock for staying on sample data

The customer can stay on full-sample data forever. There is no enforced time limit and no lockout. The persistent banner is the only social-pressure mechanism.

However — and this is the load-bearing rule that connects to the cashflow leg — **the customer can't operate on full-sample data without consuming their Free tier meters**. Every route optimization run on sample warehouses still counts toward the 2,500 delivery_tasks Free cap. The hard-lock on Free writes (see §6) fires on full-sample data work just as it fires on real-data work.

Sample data is *training wheels*, not a free infinite plan.

## 4. The six-milestone activation checklist

Activation state is tracked as a six-milestone checklist. The milestones are sequential; the customer must complete milestone N before milestone N+1 registers as complete.

| Milestone | Trigger | What unlocks / changes |
|---|---|---|
| **Milestone 1** | Customer uploads a Warehouses CSV (any row count, real uploads only — sample-seed state doesn't count). | Dashboard displays the activation banner with "1 of 5 — Items next." No other dashboard panels unlock yet. |
| **Milestone 2** | Customer uploads an Items CSV. | Dashboard banner updates to "2 of 5 — Fleet next." |
| **Milestone 3** | Customer uploads a Fleet Assets CSV. | Dashboard banner updates to "3 of 5 — Inventory next." |
| **Milestone 4** | Customer uploads an Inventory CSV. | Dashboard partially reveals: inventory overview panel + utilization metric appear. Forecast still disabled (requires orders). Routes page still disabled (requires orders). |
| **Milestone 5** | Customer uploads an Orders CSV. | Forecasts become runnable. The Routes page unlocks. The activation banner updates to "5 of 5 — Run your first route optimization." |
| **Milestone 6** | Customer completes their first real route optimization run. | The full dashboard reveals. The activation banner disappears entirely. The soft post-aha toast fires (see §7.1). The customer has graduated. |

Only milestone 6 can be reached on sample data. Milestones 1-5 require the customer to upload at least one row of real data in the specified CSV category (because milestones 1-5 are about *replacing* sample data, not running on it).

Milestone 6, by contrast, can be reached on either full-sample data or real data — the first route optimization is the aha moment, and we do not require it to be on real data. The aha is the customer feeling the product's core value; the data substrate doesn't matter.

## 5. The progressive dashboard reveal

Dashboard panels are gated by activation milestone status. A customer who hasn't reached the milestone for a panel sees either nothing (the panel is hidden) or an empty placeholder with the message "Unlocks after Milestone N — [Click here to continue onboarding]".

| Dashboard surface | Visible from milestone… | Notes |
|---|---|---|
| Activation banner | 0 (always visible from signup until milestone 6) | Disappears only when milestone 6 completes. |
| Exception feed panel | 0 | Always visible. Empty state reads "No open alerts yet — upload inventory and orders to surface exceptions." |
| Audit timeline panel | 0 | Always visible. Initially seeded with the "Workspace created" audit event. |
| Inventory charts panel | Milestone 4 (inventory uploaded) | Hidden until milestone 4. |
| Utilization metric tile | Milestone 4 | Hidden until milestone 4. |
| Forecast chart panel | Milestone 5 (orders uploaded) | Hidden until milestone 5. |
| Forecast demand metric tile | Milestone 5 | Hidden until milestone 5. |
| Weather risk metric tile | Milestone 5 | Hidden until milestone 5. |
| Weather risk zones map (Routes page) | Milestone 5 | Routes page itself unlocks at milestone 5. |
| Route schedules panel | Milestone 6 (first optimization completed) | Hidden until milestone 6. |
| Route optimization history panel | Milestone 6 | Hidden until milestone 6. |
| Dock appointment gantt | Milestone 6 | Hidden until milestone 6. |
| Freight reconciliation panel | Milestone 6 | Hidden until milestone 6. |
| Feedback form | 0 | Always visible. |

Sample data populates the unlocked panels with realistic numbers — but the panels themselves remain hidden until the prerequisite milestone is reached. The customer sees value reveal as a *reward* for completing onboarding steps.

## 6. Free tier hard-lock on writes

### 6.1 The cap

When a Free-tier customer's monthly metered usage reaches the included quota (2,500 delivery_tasks OR 50 route_optimizations, whichever comes first), the system hard-locks further write operations on those meters.

### 6.2 What "hard-lock" disables

The following write operations are disabled when the Free cap is hit:
- Running a new route optimization
- Uploading a new CSV (any of the 5 categories — uploads are metered write operations)
- Acknowledging or resolving an alert (these consume audit trail writes)
- Approving or rejecting a replenishment plan
- Creating or updating a shipment
- Setting or changing a provider key preference
- Creating a manual alert

The following operations remain available regardless of cap state:
- Reading dashboard data
- Viewing schedule history
- Exporting any data
- Logging in, viewing account / subscription / provider pages
- Reading audit timeline and exception feed

### 6.3 The hard-lock banner

When the cap is hit, every page in the console displays a top banner: "Free tier cap reached. Writes resume on the first of next month, or upgrade now to continue immediately." The banner contains an "Upgrade now" button that opens the in-product subscription tier picker.

The banner persists on every page view until either the customer upgrades OR the next billing month begins and the meter resets.

### 6.4 No overage on Free

Free tier has no overage rate. The hard-lock is the entire mechanism. A Free customer cannot exceed the cap by paying more — there is no overage path on Free. The only way to lift the cap is to upgrade to Starter, Scale, or Enterprise.

### 6.5 The hard-lock respects sample data

Sample-data operations count toward the cap, just like real-data operations. A customer who runs 2,500 route optimizations on sample data hits the cap and is hard-locked. They cannot escape the cap by staying on demo data.

## 7. The upgrade pitch surfaces

### 7.1 The soft post-aha moment (milestone 6, one-time)

The first time the customer completes a milestone 6 (first route optimization, real or sample-data), a one-time toast notification fires:

"First optimization complete. Free tier covers 2,500 delivery_tasks per month — when you outgrow that, Starter lifts the cap."

The toast:
- Has no "Upgrade" button.
- Has no link to a pricing page.
- Has no commercial call to action at all.
- Is purely informational.
- Disappears after a few seconds.
- Fires exactly once per customer, never again.

This is a *kindness* moment, not a sales moment. The customer just felt the aha; we acknowledge it and inform them about the future ceiling, without pressuring them.

### 7.2 The hard usage-upgrade pitch (60% / 80% / 100% of Free quota)

Three escalating banners fire as the customer approaches and hits the Free cap.

| Threshold | Banner content | CTA | Behavior |
|---|---|---|---|
| 60% of cap | "You've used 60% of your Free tier tasks this month." | None | Informational banner only, dismissible until next threshold. |
| 80% of cap | "You've used 80% of your Free tier tasks. Consider upgrading before writes lock." | "See pricing" button → opens in-product subscription tier picker | Persists until next threshold or upgrade. |
| 100% of cap | "Free tier cap reached. Writes resume next month, or upgrade now to continue immediately." | "Upgrade now" button → opens in-product subscription tier picker | Persists on every page view until either upgrade or month rollover. |

The in-product tier picker is the existing `/account` subscription surface already in the codebase. The customer never bounces to the public marketing website to upgrade — they stay inside the console through the entire upgrade flow.

### 7.3 No feature-gating pitches in v1

The codebase currently differentiates Free / Starter / Scale / Enterprise tiers by quota caps and overage rates only. There is no starter-only or scale-only feature that a user can attempt to access and be prompted to upgrade.

Feature-gated pitches (e.g., "Multi-warehouse schedules require Scale — upgrade to unlock") are deferred to v2 as a separate feature-differentiation work item. Until that work is done, quota-metering pitches are the only upgrade lever the system uses.

### 7.4 No signup-time pitch

There is no upgrade pitch shown at signup, in the welcome email, or on the first-login screen. The customer sees the activation banner and the dashboard. The first commercial touchpoint is the milestone-6 soft toast.

## 8. Returning users and login routing

### 8.1 Login always lands on the dashboard

Every login — regardless of activation state — lands on the dashboard page (`/`). The system never auto-routes a returning user to `/upload` directly. The user's intent on returning is respected; they may want to view a route schedule or check an audit event before they continue onboarding.

### 8.2 The dashboard banner surfaces activation state

If the customer has not yet completed milestone 6, the dashboard banner communicates their state explicitly:

- A customer who hasn't uploaded any real CSVs sees: "Welcome back. You're 0% through onboarding — 5 steps remaining. Continue setup." → one-click to `/upload`.
- A customer who has uploaded 2 of 5 CSVs sees: "Welcome back. You're 40% through onboarding — 3 steps remaining (Fleet, Inventory, Orders). Continue setup." → one-click to `/upload`.
- A customer who has uploaded 5 of 5 CSVs but hasn't run a route optimization sees: "Welcome back. You're 80% through onboarding — run your first route optimization to complete setup." → one-click to `/routes`.
- A customer who completed milestone 6 sees no activation banner at all.

### 8.3 The banner is the same surface across pages

The activation banner is a single component that reads the same per-organization activation state. On the dashboard, it renders as a compact top banner with the "continue setup" CTA. On the `/upload` page, it renders as the full milestone checklist with per-step descriptions and progress visualization.

The state is shared; only the rendering detail varies by page context.

## 9. Per-organization activation state

### 9.1 State is organization-scoped, not user-scoped

Activation milestone state is tracked per organization, not per user. If user A (admin) logs in and uploads warehouses on Tuesday, then user B (operator) logs in on Wednesday with the same org, B sees the activation checklist at "1 of 5 — items next."

The reason: freightPilot activation is a team process. In Ethiopian logistics operators, sometimes the dispatcher uploads the warehouses CSV, but the warehouse manager uploads the inventory CSV, and the fleet manager uploads the fleet assets CSV. The activation state reflects the *organization's* progress, not any one person's.

### 9.2 New users joining an activated org inherit the activated state

A user who joins an organization that has already completed milestone 6 logs in to a dashboard with no activation banner. The activation flow is invisible to them. They see the full product immediately.

A user who joins an organization that hasn't completed activation logs in and sees the same banner as their teammates — "you're 2 of 5 — fleet next." They can individually help complete the checklist by uploading the missing CSVs.

### 9.3 The admin-gated "Reset workspace to sample data" action

If a teammate uploaded bad CSVs and the admin wants to start over, the admin can reset the workspace to the original sample-data-seeded state. This action:

- Is admin-gated (requires the admin role on the organization).
- Appears on the `/account` page under a "Danger zone" section.
- Requires a typed confirmation: the admin must type the workspace name into a confirmation modal before the reset executes.
- On confirmation, deletes all real CSV-uploaded data across warehouses, items, fleet assets, inventory, and orders.
- Re-seeds the sample data from the `sample-data/` directory.
- Resets the activation state back to "0 of 5."
- Issues an audit trail event recorded as "workspace.reset_to_sample_data" with the admin user ID and timestamp.

The reset is intentionally nuclear and unambiguous. It cannot be performed accidentally. Sample data and the audit trail of the reset action itself are the only artifacts that survive.

### 9.4 No "skip onboarding" or "dismiss the banner" path

The activation banner cannot be dismissed by any user action other than completing milestone 6 (which removes it permanently). There is no "I'll do this later" or "I already know the product" skip button. The banner is persistent social pressure, exactly the same way the cashflow "Invoice Due" banner is persistent — a real operational state needs a real action to clear it.

## 10. What this feature does NOT do

To preserve scope:

- **No per-user activation state.** State is per-organization (§9.1). Individual user progress within the org is not tracked separately.
- **No time-based onboarding deadlines.** A customer can stay at "0 of 5" for 6 months without penalty. The banner is the only reminder.
- **No email-based activation sequences.** No "you haven't uploaded warehouses yet — here's how" email drip. All activation pressure is in-product. (An email-based drip is a separate work item and can be added later, but is out of scope for v1.)
- **No forced routing to `/upload`.** Login always lands on the dashboard (§8.1). The banner is the routing mechanism.
- **No feature-gating pitches.** Tier differentiation is quota-based only in v1. A separate feature-differentiation work item is required before feature-gated pitches become possible (§7.3).
- **No shared demo tenant.** Sample data lives in each user's own workspace (§3.1, decision C-iii). A shared read-only demo toggle is not provided.
- **No "Lock for using sample data too long."** Sample data is usable indefinitely (§3.5). The metering cap is the only enforcement mechanism. The activation banner is the only visual reminder.

## 11. Open verification items flagged before launch

These open items are tracked in `docs/behaviors/pending-behaviors.md` and must be cleared before this feature launches to production:

- The audit-trail schema for "workspace.reset_to_sample_data" events must be coordinated with the existing `AuditEvent` model in the codebase. The shape must be documented before implementation.
- The 5-milestone gating logic must be coordinated against the existing `UploadPage` and `CsvUploadPanel` components. The system must distinguish "sample-data-seeded state" from "real-upload state" — a clarification of what "row counts as sample" means at the data layer must be locked before build.
