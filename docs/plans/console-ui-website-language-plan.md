# Console UI Plan — Website Language, Operator Density

**Status:** APPROVED by the human. Planning artifact only — no implementation authority. Hand off to `@architect` for execution with the `impeccable` skill.

**Scope:** `apps/ops-console` only. This plan replaces ad-hoc visual tweaking with a full operator-journey design pass.

---

## 1. Core direction

### The design thesis

**Website language, operator density.**

The console must inherit the same visual language as the product website:
- same dark field
- same restrained cyan accent
- same premium border-only surfaces
- same typographic calm
- same spacing discipline

Then it must be hardened for daily operational use:
- denser layouts
- stronger scanability
- mono numbers
- clearer action hierarchy
- less visual repetition

### What we are NOT doing

- Not adding decorative gradients back
- Not adding glow shadows
- Not reintroducing random premium effects just because the previous pass became too flat
- Not diverging from the website’s language again

The fix is **coherence + hierarchy**, not “make it louder.”

---

## 2. Global visual rules

### 2.1 Color
- Base canvas remains the same deep slate-black as the website.
- Use **one accent family only**: cyan/sky.
- Use semantic accents only for actual state:
  - success = emerald
  - warning = amber
  - danger = rose
- No purple.
- No decorative multi-accent compositions.

### 2.2 Surface model
Use exactly three surface levels:
1. **Canvas** — page background
2. **Primary surface** — main work panel / page frame
3. **Nested surface** — cards, form groups, queue rows, detail sections

No random fourth/fifth surface treatments.

### 2.3 Radius
- Large surfaces: one consistent “hero panel” radius
- Standard nested panels: one consistent smaller radius
- Pills/badges: one consistent pill radius

No 34/30/28/26/22/20 radius soup.

### 2.4 Typography
- Display/headings: premium and restrained
- Body: neutral, quiet, easy to scan
- Data numerals: mono
- Eyebrows: calm, low-volume, only where structurally useful
- Avoid over-tracked uppercase labels unless they encode actual section hierarchy

### 2.5 Motion
Keep only useful motion:
- lightweight page/load fades
- button state transitions
- semantic pulses for alerts/warnings
- progress transitions where meaningful

No decorative hover theatrics.
No motion that competes with data.

---

## 3. Shared shell plan

### 3.1 Sidebar
#### Problem
The sidebar currently feels thin and under-designed. It lacks the premium structure of the website and doesn’t establish strong workspace hierarchy.

#### Goal
Create a shell that feels branded, stable, and premium enough to live in for hours.

#### Planned structure
1. **Brand block**
   - compact mark
   - product name
   - short descriptor
2. **Navigation groups**
   - Operations
   - Workspace
3. **Utility footer**
   - role
   - identity
   - logout

#### Planned behavior
- active item = clearly emphasized, not just barely highlighted
- inactive item = quiet but readable
- groups = visible enough to organize, quiet enough not to decorate

#### Acceptance
- user can scan the whole nav in 1 second
- active route is instantly obvious
- shell feels like the same company as the website

### 3.2 Top shell / header
#### Problem
The header feels too generic and too thin.

#### Goal
Make it a framing device, not a strip of text.

#### Planned structure
- context label
- page descriptor
- role + user chips
- page actions when needed

#### Acceptance
- every page opens with context
- the shell looks intentional, not skeletal

---

## 4. Login plan

### Problem
The current login is cleaner than before but still too generic and emotionally underweighted.

### Goal
Make login feel like the front door to the product, not a fallback screen.

### Layout
#### Desktop
Two-column split:
- left = compact brand/value framing
- right = sign-in surface

#### Mobile
Single stack:
- brand
- sign-in surface
- secondary actions

### Left column content
Not fluffy marketing.
Just 3 anchored promises:
- route decisions
- exception handling
- workspace controls

### Form behavior
- labels above inputs
- one clear primary action
- bootstrap action clearly secondary
- “new workspace?” flow clear but non-competing

### Error handling
Visually separate:
- normal sign-in errors
- bootstrap / first-time-setup errors

### Acceptance
- new admin immediately knows where to sign in
- returning user sees trust and clarity
- bootstrap is obviously first-time-only

---

## 5. Dashboard top plan

### Problem
The top of the dashboard is calmer than before but still too equal-weight and repetitive.

### Goal
The top of the dashboard should answer:
1. what matters now
2. what is blocked
3. what needs action
4. how healthy the workspace is

### Planned structure
#### Layer A — header surface
- title
- descriptor
- refresh / live-state actions

#### Layer B — activation / readiness strip
- onboarding state
- next action
- progress
- single CTA

#### Layer C — metric hierarchy
Not five equal cards.

Planned grouping:
- **Primary metrics** (2)
  - open exceptions
  - in-transit / active movement
- **Secondary metrics** (3)
  - forecast
  - weather risk
  - usage posture

### Exception queue
Must feel like the anchor surface.
- stronger row hierarchy
- better severity emphasis
- denser scan pattern
- less “mini-card gallery”

### Workspace readiness
Supportive, not equal to the queue.

### Audit stream
Supportive stream, not a competing headline section.

### Acceptance
- action items visually outrank supporting data
- queue becomes the natural focal point
- readiness/audit read as secondary support surfaces

---

## 6. Activation banner plan

### Problem
It is readable, but it still feels stapled on instead of guided.

### Goal
Make onboarding feel like an intentional journey rail.

### Compact mode (/dashboard)
- one state sentence
- one CTA
- one progress rail
- no extra noise

### Checklist mode (/upload)
- clearer chip rhythm
- stronger “next step” emphasis
- quieter surrounding chrome
- better contrast between empty / sample / real

### Cap banners
- p60 = reminder
- p80 = rising concern
- p100 = unmistakable stop state

### Acceptance
- onboarding teaches instead of nags
- next action becomes obvious

---

## 7. Route Studio plan

### Problem
Still reads as a technical form plus support panels, not a workstation.

### Goal
Make it feel like the console’s primary modeling environment.

### Planned structure
#### Left column
- route model form
- grouped by intent:
  - scenario identity
  - route shape
  - operating constraints
  - persistence options

#### Right column
- route map / weather context
- clearly subordinate to the form until results exist

#### Below
- saved schedules
- scenario history

### Form treatment
- stronger field grouping
- better checkbox/toggle treatment
- submit action dominant
- helper copy calm but useful

### Result treatment
- summary block at top
- key stats in structured row
- previous result comparison in one distinct diff surface
- stop sequence as dense, readable rows

### Acceptance
- page feels like a tool, not a demo
- result hierarchy is immediate
- persisted vs draft state is obvious

---

## 8. Account page plan

### Problem
The page feels long and too uniformly weighted.

### Goal
Turn it into a governance surface with clear section boundaries.

### Planned structure
1. plan + usage posture
2. escalation contact
3. provider control
4. audit stream
5. danger zone

### Section rules
- plan/usage = dominant
- provider control = secondary work area
- audit = support stream
- danger zone = isolated and unmistakable

### Plan cards
Must stop feeling like mini marketing tiles.
They should read like comparative operational controls.

### Acceptance
- billing posture is understood at a glance
- provider work feels controlled
- dangerous actions are clearly isolated

---

## 9. Receipts page plan

### Problem
It still reads like stacked cards instead of a financial workflow.

### Goal
Split it clearly into:
- intake
- wallet state
- receipt history

### Upload
Should feel like a confident intake surface.

### Wallet
Should read as a financial state block, not a generic card.

### Receipt history
Each row should emphasize:
- status
- amount
- invoice
- sender
- actionability

### Dispute / rejection handling
Should feel structured and intentional, not tacked underneath the card.

### Acceptance
- upload confidence increases
- wallet is scannable
- receipt rows read like a real work queue

---

## 10. Admin queue / verification workstation plan

### Problem
This is the highest-stakes page but still feels like stacked cards.

### Goal
Make it feel like a verification workstation with clear queue/detail modes.

### Queue column
Each row must clearly encode:
- organization
- amount
- reference
- sender
- state
- age
- flags

Rows should feel denser and more operational.

### Detail column
Must be segmented into:
1. flags
2. extracted fields
3. preview
4. verdict controls
5. reversal context

### Verdict actions
Need stronger hierarchy:
- verify = primary
- escalate = warning secondary
- reject = controlled muted-danger

### Reversal panel
Should read like a secure audit surface, not another generic content block.

### Acceptance
- queue scanning becomes faster
- decision confidence increases
- detail pane feels like a workstation, not card soup

---

## 11. Remaining pages (to complete the console)

### Upload
- calmer step rail
- clearer import sequence
- intake panel aligned to the same surface system

### Shipments
- dialog surface aligned to shell
- denser shipment rows
- calmer manual-entry form

### Alerts
- sharper queue rows
- dialog treatment aligned
- better triage rhythm

### Planning
- same dialog alignment
- stronger approval-board hierarchy
- less repeated-card feeling

### Providers
- governance-first, not mini-card-first
- cleaner row structure for keys

### Unauthorized / fallbacks
- inherit the same system, not generic defaults

---

## 12. Shared implementation rules for `@architect` + `impeccable`

### Hard rules
- preserve all existing copy unless a human explicitly approves copy edits
- preserve all handlers
- preserve all `data-testid`s used by tests
- preserve all auth flows
- preserve page routing and role gates
- no decorative gradients
- no glow shadows
- no random visual experiments outside the design system

### Visual rules
- one accent family only
- mono numerals everywhere metrics matter
- large surfaces = premium, quiet
- nested surfaces = dense, work-oriented
- active state > passive state contrast must be obvious

### Technical rules
- shared surfaces must flow through common primitives where possible
- page-specific polish must not fork the design language
- every page should pass tests, typecheck, build
- no new dependencies unless explicitly justified and approved

---

## 13. Execution order for `@architect`

1. shared tokens / shell / page header
2. login
3. dashboard top + activation
4. route studio
5. account
6. receipts
7. admin queue
8. upload / shipments / alerts / planning / providers / unauthorized
9. final consistency pass
10. tests + build + deploy + live verification

---

## 14. Acceptance standard

This pass is complete when:
- the console clearly feels like the same product as the website
- the listed surfaces no longer feel “AI slop” or generic
- hierarchy is stronger than flatness
- operators can scan faster, not slower
- no page feels like it belongs to another design system

---

## 15. Recommendation

Approved direction: **yes**.

Pass this document to `@architect` and explicitly ask for execution with the **impeccable** skill.
