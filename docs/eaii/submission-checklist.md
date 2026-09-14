# EAII Second-Round Submission — Link & Upload Checklist

**Form:** https://forms.gle/VCRWZkEQQniEo5UA7
**Deadline stated in the invitation:** September 20, 2026
**Hard requirement:** both the pitch deck link and the pitch video link must be set to
**"Anyone with the link can view."** Links that require an access request or permission approval
will not be reviewed.

> Do every check below in a **private/incognito window while signed out of all accounts**. If you
> can open the link without signing in, so can the reviewers — that is the only test that counts.

---

## Part A — Pitch Deck

### A1. Files in this repository

| File | Use |
|---|---|
| `docs/eaii/pitch-deck.html` | Source. 7 slides, 16:9 (13.333in × 7.5in). Open in Chrome and use **Print → Save as PDF** to regenerate the PDF if you edit it. |
| `docs/eaii/FreightPilot-EAII-Pitch-Deck.pdf` | **Upload this to Drive.** Print-ready, exactly 7 pages. |
| `docs/eaii/FreightPilot-EAII-Pitch-Deck.pptx` | **Optional backup.** 7 native, editable PowerPoint slides if a reviewer asks for an editable copy. |

### A2. Cover all 10 required sections

The deck is 7 slides and maps to the required content as follows. Verify this mapping is still intact
if you edit anything:

| EAII required content | Where it lives |
|---|---|
| 1 Problem | Slide 1 — "1 · The problem" |
| 2 Solution | Slide 1 — "2 · The solution" |
| 3 Market Opportunity | Slide 2 (whole slide) |
| 4 Traction | Slide 3 — "Traction" card + the four metric tiles |
| 5 Business Model | Slide 3 — "Business model" card |
| 6 Go-to-Market | Slide 4 — "Go-to-market" card |
| 7 Competition | Slide 4 — "Competition" card |
| 8 Core Team and Advisors | Slide 5 (whole slide) |
| 9 Financial Projection | Slide 6 (whole slide) |
| 10 The Ask | Slide 7 (whole slide) |

Slide count: **7** (the limit is "no more than 7 slides"). ✅

### A3. Upload to Google Drive (recommended — most reliable "anyone with the link" link)

1. Go to <https://drive.google.com> and sign in with the account you want associated with the
   submission.
2. Create a folder, e.g. `EAII Submission — FreightPilot`.
3. Upload `FreightPilot-EAII-Pitch-Deck.pdf`.
4. Right-click the file → **Share** → **Share** again (the dialog).
5. Under **General access**, change *Restricted* to **Anyone with the link**.
6. Confirm the role dropdown next to it says **Viewer** — not Editor, not Commenter.
7. Click **Copy link** → **Done**.
8. Open the link in a **private window signed out of Google**. You should see the 7-page deck
   rendered. If you see a sign-in page or "You need access", step 5 did not apply — repeat it.

**Link to record here:**

```
Pitch deck link: ________________________________________________
Tested signed-out:  [ ] yes   Date tested: ____________
```

---

## Part B — Pitch Video

### B1. Record from `pitch-video-script.md`

The script is written for **4:10** (requirement is 3–5 minutes) with a fast 3:45 cut and a full 4:45
cut. Do the pre-flight checklist in that file before you hit record.

**Export settings:** 1080p, H.264 MP4, under 500 MB.

### B2. Option 1 — YouTube (Unlisted)

"Unlisted" is the correct choice: it is link-viewable but not searchable. **"Private" will fail the
requirement** — a private video requires the viewer to be signed in and granted access.

1. Go to <https://studio.youtube.com> → **Create** → **Upload videos**.
2. Select your MP4. Fill in a title and description (put the numbers list from the script into the
   description — it helps reviewers).
3. On the **Visibility** step, choose **Unlisted**. Do **not** choose Private.
4. Also set: **Audience → "No, it's not made for kids"**. If you skip this, the video stays in a
   draft state and the link will not work for anyone.
5. Publish, then click the video → **Share** → **Copy link**. It looks like
   `https://youtu.be/XXXXXXXXXXX`.
6. Open that link in a **private window signed out of Google**. It must play immediately.

### B3. Option 2 — Google Drive

1. Upload the MP4 to the same Drive folder as the deck.
2. Right-click → **Share** → **General access** → **Anyone with the link** → role **Viewer**.
3. Copy the link and test it signed out, exactly as in A3 step 8. Make sure it plays (Drive streams
   MP4 natively) rather than showing a download-only page.

### B4. Final video checks

| Check | Done |
|---|---|
| Runtime is between 3:00 and 5:00 | [ ] |
| First 5 seconds play (not black/frozen) | [ ] |
| Last 5 seconds play | [ ] |
| Audio is audible and not clipping | [ ] |
| Link opens in a **signed-out private window** and plays | [ ] |
| Visibility is **Unlisted** (YouTube) or **Anyone with the link** (Drive) | [ ] |
| Not set to Private / Restricted | [ ] |

**Link to record here:**

```
Pitch video link: _______________________________________________
Runtime: ______   Tested signed-out:  [ ] yes   Date tested: ____________
```

---

## Part C — Weekly Availability

`docs/eaii/weekly-availability.md` contains the availability declaration. It states a commitment of
**five days per week (Monday–Friday)** against a required minimum of three.

Two ways to submit it:

- **Paste the key line into the form's availability field:**
  > Available five days per week (Monday–Friday, 09:00–17:00 EAT) for the full 4–6 month program
  > duration — above the three-day minimum. Flexible on hours to suit program sessions and mentor
  > time zones; 48 hours' notice for any unavoidable change.
- **Or upload the full document** as a PDF: open `weekly-availability.md`, print to PDF, and upload
  it to the same Drive folder with the same "Anyone with the link" sharing.

Fill in your name, date, and signature in §6 of that document before submitting.

---

## Part D — Before you press Submit on the form

- [ ] Pitch deck link added, tested signed out, shows **7 pages**
- [ ] Pitch video link added, tested signed out, plays, runtime 3–5 minutes
- [ ] Weekly availability answered (minimum three days; ours states five)
- [ ] Company name, founder name, and contact email match across the deck, the video, and the form
- [ ] Both links open **without an access request** — this is the single most common rejection reason
- [ ] You have kept a copy of exactly what you submitted (screenshot the completed form)

---

## Part E — What is true in this submission (do not overstate)

So that nothing in the form contradicts the product, here is the accurate status. Use these figures
if the form asks for traction:

**Working and verified**
- Live product website, operations console, and API; Electron desktop shell in the repository.
- 81 API endpoints; 19 database migrations.
- 399 backend tests, 143 console tests, 62 website tests — all passing.
- Launch funnel verified end to end: 22 of 22 steps, including signup → seeded workspace → first
  route optimisation producing a real plan (21.07 km, 31.61 ETB) → billing state → cross-tenant
  isolation returning 404.
- Zero known critical or high dependency advisories in deployed surfaces; dependencies are locked
  with hash verification and CI gates run on every push.

**Not yet true — do not claim it**
- **Pre-revenue.** There are no paying customers yet. Do not write "customers" or "ARR".
- **The hosted production database needs its credentials reissued** before the public site can
  complete signups again. The code and schema are verified; this is an access/credential task.
  If a reviewer clicks through to the live site and signup fails, that is why — mention it if asked
  rather than letting it be discovered.
- **No signed desktop installer yet.** The Electron shell runs from source; a signed, auto-updating
  installer is planned work.
- **The CBE/Dashen fee-schedule verification is still open.** It gates paid launch, not the product.
