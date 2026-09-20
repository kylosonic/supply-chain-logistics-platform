# EAII Second-Round Submission — Structure & What Goes Where

**Form:** https://forms.gle/VCRWZkEQQniEo5UA7
**Deadline stated in the invitation:** September 20, 2026

---

## 1. The one thing to understand first

The email asks for **three separate inputs**, not one package:

| # | What EAII asks for | Where it goes | Status |
|---|---|---|---|
| 1 | Pitch Deck, as a **"shareable link"** | A field in the Google Form | ✅ Link ready |
| 2 | Pitch Video (3–5 min), as a **"shareable link"** | A **separate** field in the Google Form | ⬜ You record it |
| 3 | Weekly Availability | A field (or an upload) in the Google Form | ✅ Text ready |

The page at **https://freightpilot-eaii.vercel.app** is a *supporting* artefact. It holds the deck, the product tour and the availability statement behind one link — useful context, and it satisfies "shareable link" on its own. But **the video needs its own link**, because it lives on YouTube or Drive, not on that page.

So: **two links go into the form, and one of them (the deck) can be the page URL.**

---

## 2. Field-by-field: what to paste

### Field: Pitch Deck link
Paste exactly this:

```
https://freightpilot-eaii.vercel.app
```

Why the page rather than a direct PDF link: a reviewer lands on a page that opens with the deck (inline PDF viewer), and the deck is downloadable as PDF *and* as editable PowerPoint. If the form demands a file-type link, use the direct one instead:

```
https://freightpilot-eaii.vercel.app/deck.pdf
```

Both are verified to open **signed out, with no access request**.

### Field: Pitch Video link
⬜ **You supply this — it is the only thing not yet done.**

1. Record from `docs/eaii/pitch-video-script.md` (4:10 target; 3:45 and 4:45 cuts included).
2. Upload to **YouTube → Visibility: Unlisted** (not Private) *or* **Google Drive → General access: Anyone with the link → Viewer**.
3. On YouTube you **must** also set **Audience → "No, it's not made for kids"**, or the video stays a draft and the link fails for everyone.
4. Open the link in a **private window signed out of all accounts**. If it plays, it will play for EAII.
5. Paste that URL into the form.

If you also want it on the submission page, send me the URL and I will embed it and redeploy — one command.

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
| **Submission page** | `/` | The single link. Sections: 01 Pitch Deck · 02 Pitch Video · 03 Product Tour · 04 Weekly Availability · 05 Product status ("what is built, and what is not") |
| **Pitch deck (PDF)** | `/deck.pdf` | The 7-slide deck. Print-ready, exactly 7 pages |
| **Pitch deck (PPTX)** | `/deck.pptx` | Same deck, native editable PowerPoint — for a reviewer who wants to reuse slides |
| **Product tour** | `/product/` | 8 screenshots of the running console on a real workspace. Also your visual reference while recording |
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
| `docs/eaii/pitch-page/index.html` | the submission page. Replace `__VIDEO_URL__` to embed the video |
| `docs/eaii/submission-checklist.md` | the detailed Play-Drive/YouTube walkthrough with screenshots-level steps |

After editing the page, redeploy it:

```powershell
cd docs/eaii/pitch-page
npx vercel deploy --yes --prod
```

---

## 7. Summary — the shortest version

1. **Deck link:** `https://freightpilot-eaii.vercel.app` → into the form
2. **Video:** record → YouTube Unlisted → test signed out → link into the form
3. **Availability:** paste the paragraph in §2, or upload the signed PDF
4. Submit before **September 20, 2026**

That is the whole submission. Everything except the recording is already live and verified.
