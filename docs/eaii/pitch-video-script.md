# FreightPilot — Pitch Video Script & Storyboard

**For:** EAII (The AI Startup Center) second-round screening
**Requirement:** 3–5 minute pitch video, submitted as a shareable link
**Target runtime:** 4:10 (with a 3:45 fast cut and a 4:45 full cut noted)
**Format:** screen-share demo + talking head. Record at 1920×1080, 30 fps.

---

## How to use this script

1. **Before recording** — read section *Pre-flight checklist* below and do the run-through once. The demo is scripted against the live product; if a click path has moved, follow the on-screen labels (they are quoted verbatim in this script).
2. **Two presenter options** are written for every talking-head beat:
   - **[CAM]** — say it to camera (founder on screen).
   - **[VO]** — narrate over screen capture.
   Use whichever you are comfortable with; the timing assumes no gaps either way.
3. **Camera-off option:** if you would rather not appear on camera, use the **[VO]** lines throughout and start the video on the product. Nothing in the script requires your face — but the closing 20 seconds should include your face or at minimum your name and role spoken aloud.
4. Timings are *spoken* targets. If you run long, cut from §6 (Competition) and §8 (Financials) first — those are the sections a reader can absorb from the deck.

---

## Pre-flight checklist (10 minutes)

**Visual reference:** https://freightpilot-eaii.vercel.app/product/ — eight captures of the running
console, in the same order as the demo beats below. Look at these before recording so you know what
each screen should show. If you would rather not demo live, you can screen-record the product tour
page instead and the script still works.

| # | Check | Why |
|---|---|---|
| 1 | Close Slack, mail, and any tab with personal data. Notifications appear on camera. | Professionalism |
| 2 | Set the console to the demo workspace and confirm the dashboard shows numbers (not spinners). | Avoid dead air |
| 3 | Zoom the browser to ~110% so text is legible in the recording. | Readability |
| 4 | Hide the bookmarks bar (Ctrl+Shift+B in Chrome/Edge). | Clean frame |
| 5 | Test microphone for 15 seconds and listen back. | Audio matters more than video |
| 6 | Confirm screen resolution 1920×1080 and the recorder set to that output. | EAII review quality |
| 7 | Have the deck open in a second window for the slides you reference. | Section transitions |
| 8 | Rehearse the signup path once on a scratch email so the live demo flows. | The demo must not stall |

---

## Storyboard & script

### 0:00 – 0:15 · Cold open — the hook
**VISUAL:** Talking head, mid-shot. Plain background. Lower-third: *Name — Founder, FreightPilot*.
**AUDIO:**
> **[CAM]** "In Ethiopia, a logistics operator plans today's routes in Excel, finds out a truck is
> delayed when the driver calls, and discovers a stock-out when a customer complains. I built
> FreightPilot to replace that with one screen. Let me show you the product first, then the business."

**Why this works:** states a concrete, recognisable problem in the operator's own terms, promises a demo, and sets the agenda. No adjectives doing the work.

---

### 0:15 – 0:55 · The product, live — signup to a route plan
**VISUAL:** Switch to screen share. Browser at the product website.
**ON-SCREEN ACTION:**
1. Show the website hero. Point at the single call to action.
2. Fill the signup form with a business email and submit.
3. Land in the operations console. Do **not** narrate every click — narrate the meaning.

**AUDIO:**
> **[VO]** "A new company signs up with a business email. No sales call, no procurement, no install."
>
> "The workspace arrives already populated with sample operational data — three warehouses, an item
> catalogue, a fleet, inventory and order history. That is deliberate: an operator should see what
> the product does before they trust it with their own data."
>
> "Now the first route optimisation." *[click **Route Studio**, set the plan, run it]*
> "Two deliveries, weighted for distance, time, cost and vehicle capacity. Twenty-one kilometres,
> thirty-one birr sixty-one. That plan is persisted, and it is now in the run history."

**Why this works:** it is the product's core promise, demonstrated, not described. The numbers are real and specific.

---

### 0:55 – 1:35 · The operational loop — what happens after the plan
**VISUAL:** Console. Navigate: **Dashboard** → **Shipments** → **Alerts** → **Upload**.
**ON-SCREEN ACTION:** Open the dashboard; hover the KPI tiles. Open the exception feed. Open the CSV upload surface and point at the per-category "sample vs your data" chips.

**AUDIO:**
> **[VO]** "Planning is only the first half. The dashboard is the operational picture: what is in
> stock, what is late, what is waiting on a decision."
>
> "A delayed shipment raises an exception. It lands in a queue where an operator acknowledges,
> resolves or escalates it — and every one of those actions is written to an audit trail."
>
> "And this is how a real team gets their data in: five CSVs — warehouses, items, fleet, inventory,
> orders. The product tells you exactly which categories are still sample data and which are yours."

**Why this works:** proves the product is an operating system for a day's work, not a one-trick optimiser.

---

### 1:35 – 2:05 · The cashflow layer — the wedge nobody else builds
**VISUAL:** Console. Navigate: **Receipts** → wallet / reconciliation view → audit timeline.
**ON-AUDIO:**
> **[VO]** "Here is the part that is specific to this market. Ethiopian operators settle by bank
> transfer. Receipts arrive as screenshots and PDFs, and someone matches them to invoices by hand."
>
> "FreightPilot ingests the receipt, matches it against the invoice, credits the wallet, and records
> the decision. If a decision is wrong, it can be reversed — and the reversal is itself an audited,
> undoable event. That matters because in cashflow operations, 'who changed this and when' is the
> question that ends arguments."

**Why this works:** it is the hardest thing in the product to copy, and it is a *business* problem, not a feature list.

---

### 2:05 – 2:40 · Built for trust — the multi-tenant and security story
**VISUAL:** Deck slides 1 and 3 side by side, or a static architecture graphic.
**ON-SCREEN ACTION:** If you have a second workspace handy, show that it sees none of the first workspace's shipments.

**AUDIO:**
> **[CAM]** "Two things I want an accelerator to check, because they are where logistics software
> usually fails."
>
> "First: isolation. Roughly half the platform's surfaces once returned every customer's data to any
> signed-in user. That is fixed, and it is now pinned by a two-organisation regression suite — a
> second company cannot list, read or change the first company's rows, and a cross-tenant read
> answers 'not found' rather than 'forbidden', so it does not even reveal that the record exists."
>
> "Second: I had an independent security audit done. It found one critical and six high findings —
> including a committed placeholder signing key. All of them are remediated, the dependencies are
> locked with hash verification, and CI now runs the tests, the linter, the type checks, the builds
> and dependency audits on every push."

**Why this works:** accelerators see a hundred demos. Almost nobody volunteers that their first
security audit found a critical issue and that they fixed it. This is the section that separates you.

---

### 2:40 – 3:20 · Market, business model, and traction
**VISUAL:** Deck slides 2 and 3.
**AUDIO:**
> **[CAM]** "The market is countable: Ethiopian freight forwarders, distributors and 3PL operators
> running five to fifty vehicles. Low thousands of serviceable firms, and the buyer is one person —
> the owner who feels route cost, stock-outs and reconciliation every week."
>
> "The model is B2B SaaS priced per company workspace, not per seat, because the value is
> operational. There is a free entry tier that onboards a real workspace; usage is metered
> server-side — delivery tasks and route optimisations — with threshold events at eighty percent,
> one hundred percent and overage. That is the upgrade moment, and it is backed by the customer's
> own operational record rather than a sales claim."
>
> "On traction, I will be straight with you: we are pre-revenue and post-product. What exists and is
> verified is the platform — six hundred and four automated tests, a signup-to-first-route-plan
> funnel verified end to end, and zero known critical or high advisories in anything we deploy."

**Why this works:** pre-revenue is stated plainly and immediately re-framed by what *is* proven. Reviewers trust the second sentence because of the first.

---

### 3:20 – 3:45 · Team and the honest gap
**VISUAL:** Deck slide 5.
**AUDIO:**
> **[CAM]** "I am the founder, and I built this: the API, the console, the website, the desktop shell
> — about twenty thousand lines across four deployable surfaces, with the engineering discipline to
> keep it standing."
>
> "What I do not have is an advisor who has run logistics operations in this market, and someone who
> has taken B2B SaaS into owner-operated firms. That is a real gap, and it is one of the main reasons
> I am applying rather than just building."

**Why this works:** naming the gap you want filled is what an accelerator is for. Pretending it does not exist reads as inexperience.

---

### 3:45 – 4:10 · The ask and the close
**VISUAL:** Deck slide 7. Cut back to talking head for the last two lines.
**AUDIO:**
> **[CAM]** "So the ask has four parts: domain mentorship in Ethiopian logistics operations;
> go-to-market help converting founder-led onboarding into a repeatable motion; support closing one
> remaining human verification — confirming the CBE and Dashen transfer fee schedules in the five to
> fifty thousand birr band, which blocks paid launch rather than the product; and preparation for a
> seed round."
>
> "In return you get a founder who is available five days a week — above your three-day requirement —
> and a platform you can audit line by line. Every number in this video is reproducible from the
> repository."
>
> "Thank you. I am [Name], founder of FreightPilot."

**Why this works:** a specific four-part ask, a concrete commitment that exceeds the stated requirement, and a final line that a reviewer can write down.

---

## Timing table

| Section | Start | Duration | Cut priority |
|---|---|---|---|
| Cold open | 0:00 | 0:15 | Keep |
| Product demo: signup → route plan | 0:15 | 0:40 | Keep — this is the video |
| Operational loop | 0:55 | 0:40 | Trim to 0:25 if long |
| Cashflow layer | 1:35 | 0:30 | Keep — differentiator |
| Trust: isolation + security audit | 2:05 | 0:35 | Keep — your edge |
| Market / model / traction | 2:40 | 0:40 | Trim to 0:30 |
| Team + honest gap | 3:20 | 0:25 | Trim to 0:15 |
| Ask + close | 3:45 | 0:25 | Keep |
| **Total** | | **4:10** | |

**Fast cut (3:45):** trim operational loop to 0:25 and market/model to 0:30.
**Full cut (4:45):** add a 0:35 beat after §3 showing the planning approval flow (generate replenishment plan → approve → audit entry).

---

## Delivery notes

- **Pace:** roughly 145 words per minute. The script above is ~600 spoken words; that is 4:05 at
  that pace. Do not rush the product demo — silence while a screen loads is fine and reads as real.
- **Sentences to slow down for:** the 404-not-403 line, the "one critical and six high findings"
  line, and the five-days-per-week commitment. These are the three things a reviewer should retain.
- **Do not** read the deck aloud. The video should add what the deck cannot: a working product, a
  live number, and a founder's voice.
- **Numbers to have ready if asked (put them in the video description):**
  - Backend tests: 399 passing on the locked dependency set
  - Console + website tests: 143 + 62 passing
  - Live API endpoints: 81
  - Schema migrations: 19
  - First route plan produced: 21.07 km, 31.61 ETB
  - Launch funnel: 22 of 22 verification steps passing

---

## Alternative: narrated screen-only cut

If you prefer not to be on camera at all, the cut is identical except:

- Replace every **[CAM]** beat with the visual from the *next* section and read the line as **[VO]**.
- Open on the product website instead of a talking head, and put the cold-open line as a caption
  over the hero for the first 8 seconds.
- End on slide 7 with your name and role as a lower-third while you speak the final line.

The result is a 4:10 screen-led pitch that still satisfies "record a 3–5-minute pitch video".

---

## After recording — submission checklist

1. Export at 1080p, H.264 MP4, and keep it under 500 MB.
2. Check the first 5 seconds and the last 5 seconds play correctly (most common upload failure).
3. Upload to **YouTube (Unlisted)** or **Google Drive**, then follow
   `docs/eaii/submission-checklist.md` to confirm the link is set to "Anyone with the link can view".
4. Test the link in a private/incognito window while signed out of every account. If you can watch
   it without signing in, so can the reviewers.
5. Paste the tested URL into the submission form.
