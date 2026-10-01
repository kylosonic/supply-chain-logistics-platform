# EAII Second-Round Submission — Structure & What Goes Where

**Form:** https://forms.gle/VCRWZkEQQniEo5UA7
**Deadline stated in the invitation:** September 20, 2026

---

## 1. The one thing to understand first

The email asks for **three separate inputs**, not one package:

| # | What EAII asks for | Where it goes | Status |
|---|---|---|---|
| 1 | Pitch Deck, as a **"shareable link"** | A field in the Google Form | ✅ Hosted |
| 2 | Pitch Video (3–5 min), as a **"shareable link"** | A **separate** field in the Google Form | ✅ Hosted |
| 3 | Weekly Availability | A field (or an upload) in the Google Form | ✅ Text ready |

Both required links are now **live pages on one Vercel project**, verified to open in a signed-out
browser with no access request. That satisfies *"Anyone with the link can view"* by construction —
a public static page has no permission model to misconfigure.

## 2. Field-by-field: what to paste

### Field: Pitch Deck link
Paste exactly this:

```
https://freightpilot-eaii.vercel.app/deck/
```

That page shows all 7 slides, maps each of the 10 required EAII sections to its slide, and offers
the deck inline as PDF plus a downloadable editable PPTX. If the form insists on a file-extension
link, either of these is also verified signed-out:

```
https://freightpilot-eaii.vercel.app/deck/deck.pdf
https://freightpilot-eaii.vercel.app/deck/deck.pptx
```

### Field: Pitch Video link
Paste exactly this:

```
https://freightpilot-eaii.vercel.app/watch/
```

A 4 m 34 s narrated pitch (273.6 s — inside the 3–5 minute requirement), playing from an HTML5
player on a page that also lists the 11 chapters with timestamps. The underlying file is
`https://freightpilot-eaii.vercel.app/watch/pitch-video.mp4` — `video/mp4`, byte-range enabled
(returns `206`), so it seeks in-browser.

> **Optional upgrade.** A YouTube or Drive link carries more reviewer trust than a raw file, and
> YouTube is what most reviewers expect for a video field. If you want that, upload
> `pitch-video.mp4` (download it from the `/watch/` page) to **YouTube → Unlisted**, then set
> **Audience → "No, it's not made for kids"** — without that, the video stays a draft and the link
> fails for everyone. Paste the YouTube URL instead; the Vercel link stays as a backup. The
> `/watch/` link already works today, so this is a nice-to-have, not a blocker.

### Field: Weekly Availability
Paste this text:

```
Available five days per week (Monday-Friday, 09:00-17:00 EAT) for the full 4-6 month
program duration - above the three-day minimum. Core hours are flexible to suit program
sessions and mentor time zones; 48 hours' notice for any unavoidable change. Full
availability statement: https://freightpilot-eaii.vercel.app/weekly-availability.pdf
```

If the form has a file upload instead, download `weekly-availability.pdf` from that URL, fill in your **name, date and signature** (section 6 of the document), then upload it.

---

## 3. What each artefact is, and why it exists

| Artefact | Live URL | Purpose |
|---|---|---|
| **Submission page** | `/` | Hub page. Sections: 01 Pitch Deck · 02 Pitch Video · 03 Product Tour · 04 Weekly Availability · 05 Product status ("what is built, and what is not") |
| **Pitch deck (hosted)** | `/deck/` | **← deck link for the form.** All 7 slides, 10 required sections mapped |
| **Pitch video (hosted)** | `/watch/` | **← video link for the form.** Player, poster, 11 chapters |
| **Pitch deck (PDF)** | `/deck/deck.pdf` | The 7-slide deck. Print-ready, exactly 7 pages |
| **Pitch deck (PPTX)** | `/deck/deck.pptx` | Same deck, native editable PowerPoint — for a reviewer who wants to reuse slides |
| **Pitch video (MP4)** | `/watch/pitch-video.mp4` | The 4 m 34 s file itself. `video/mp4`, range-enabled |
| **Product tour** | `/product/` | 8 screenshots of the running console on a real workspace |
| **Availability (PDF)** | `/weekly-availability.pdf` | The 5-day commitment, working grid, and time-allocation plan |
| **Live product** | product-web-chi.vercel.app · ops-console-azure.vercel.app · platform-api-smoky.vercel.app | The actual platform. Signup works end to end |

### How the 10 required deck sections map to the 7 slides

| EAII requirement | Slide |
|---|---|
| 1 Problem | 1 |
| 2 Solution | 1 |
| 3 Market Opportunity | 2 |
| 4 Traction | 3 |
| 5 Business Model | 3 |
| 6 Go-to-Market | 4 |
| 7 Competition | 4 |
| 8 Core Team and Advisors | 5 |
| 9 Financial Projection | 6 |
| 10 The Ask | 7 |

Slide limit is "no more than 7" — we use exactly 7. ✅

---

## 4. Before you press Submit

Run this checklist in a **private window, signed out of everything**:

- [ ] Deck link opens and shows **7 pages**
- [ ] Video link **plays** (not "request access", not "sign in to confirm")
- [ ] Video runtime is between **3:00 and 5:00**
- [ ] Availability answered (ours states 5 days, minimum is 3)
- [ ] Company name, founder name and email are **consistent** across deck, video and form
- [ ] Neither link requires an access request — this is the most common rejection reason
- [ ] Screenshot the completed form for your records

---

## 5. If a reviewer clicks through to the product

Production is live and verified — signup genuinely works. But two honest notes, so nothing surprises you:

1. **There are no paying customers.** Do not claim revenue.
2. **The hosted database was re-provisioned recently.** It is a fresh Neon instance with a handful of test workspaces. If asked, the accurate answer is: the original Supabase projects were deleted, production was rebuilt on Neon, and the full launch funnel now passes 22/22 end to end.

Everything else you can state as fact, because it is verifiable:

- 7-slide deck covering all 10 required sections
- 399 backend + 143 console + 68 website tests passing
- Launch funnel verified 22/22 **in production**: signup → seeded workspace → first route plan at 21.07 km / 31.61 ETB → billing → cross-tenant read returns 404
- Every deployed dependency audit clean (0 known vulnerabilities)
- Security audit findings remediated, with a restore drill executed against production

---

## 6. Files in this repository (if you need to edit anything)

| File | Edit it to change… |
|---|---|
| `docs/eaii/pitch-deck.html` | the deck. Print to PDF in Chrome to regenerate; then rebuild the PPTX with `python scripts/build_pitch_deck_pptx.py` |
| `docs/eaii/pitch-video-script.md` | the video script and timings |
| `docs/eaii/weekly-availability.md` | the availability statement |
| `docs/eaii/pitch-page/index.html` | the submission hub page |
| `docs/eaii/pitch-page/deck/index.html` | the hosted deck page that the **deck link** points at |
| `docs/eaii/pitch-page/watch/index.html` | the hosted video page that the **video link** points at |
| `docs/eaii/pitch-page/vercel.json` | headers (content types, range support, noindex) |
| `docs/eaii/submission-checklist.md` | the detailed Drive/YouTube walkthrough with screenshots-level steps |

After editing any page, redeploy:

```powershell
npx vercel deploy --yes --prod --cwd docs/eaii/pitch-page
```

---

## 7. Summary — the shortest version

1. **Deck link:** `https://freightpilot-eaii.vercel.app/deck/` → into the form
2. **Video link:** `https://freightpilot-eaii.vercel.app/watch/` → into the form
3. **Availability:** paste the paragraph in §2, or upload the signed PDF
4. Submit before **September 20, 2026**

Both required links are live and were verified anonymously: 13/13 routes return `200`, the deck
renders all 7 slides, and the video serves `video/mp4` with working byte-range seeking.
Optional polish only: re-upload the MP4 to YouTube Unlisted if you want a familiar video host.
