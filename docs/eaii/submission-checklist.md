# EAII Second-Round Submission — Link & Upload Checklist

**Form:** https://forms.gle/VCRWZkEQQniEo5UA7
**Deadline stated in the invitation:** September 20, 2026
**Hard requirement:** both the pitch deck link and the pitch video link must be set to
**"Anyone with the link can view."** Links that require an access request or permission approval
will not be reviewed.

> Do every check below in a **private/incognito window while signed out of all accounts**. If you
> can open the link without signing in, so can the reviewers — that is the only test that counts.

## The two links, ready to paste

| Form field | Paste this | Why it cannot fail the access check |
|---|---|---|
| **Pitch Deck URL** | `https://freightpilot-eaii.vercel.app/deck/` | Public static page on Vercel. No Google/Drive permission model exists, so there is no share setting that can be left on "Restricted". |
| **Pitch Video URL** | `https://freightpilot-eaii.vercel.app/watch/` | Same. Serves `video/mp4` with byte-range seeking; verified anonymously. |

Verified 2026-09-20 with an **anonymous HTTP client** (no cookies, no session): 13/13 routes returned
`200`. The deck page renders all 7 slides; the video responds `206 Partial Content` to a range
request; `/watch/` reports runtime `0:00 / 4:33` in the player.

Optional upgrade for the video field — a YouTube **Unlisted** upload (see §B2). Not required, and
only worth doing if you want a `youtu.be` link in the form.

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

### A3. The deck link — already hosted, nothing to upload

The deck is live at a public static URL. There is no permission dialog to get wrong, which is why
this is the safest possible answer to *"anyone with the link can view."*

```
https://freightpilot-eaii.vercel.app/deck/
```

Paste that into the form's **Pitch Deck URL** field. Verified signed-out: `200`, all 7 slides
render, and the page offers the deck inline as PDF plus an editable PPTX download.

**Record it here:**

```
Pitch deck link: https://freightpilot-eaii.vercel.app/deck/
Tested signed-out:  [x] yes   Date tested: 2026-09-20 (anonymous fetch, no cookies)
```

> **Fallback, only if the form rejects a folder-style URL:** a file-extension variant is also live
> and verified — `https://freightpilot-eaii.vercel.app/deck/deck.pdf`.
>
> **Optional, if you prefer Drive anyway:** steps A4–A6 below still work. Upload
> `FreightPilot-EAII-Pitch-Deck.pdf` to Drive, set **Anyone with the link → Viewer**, and paste that
> link instead. Nothing breaks if you do; it is simply more steps and one more thing to misconfigure.

---

## Part B — Pitch Video

### B1. The video is already produced and hosted

The pitch video exists: **4 m 34 s** (273.6 s — inside the 3–5 minute requirement), 1920×1080,
30 fps, H.264/AAC, narrated, 18.1 MB. It is live at a public static URL:

```
https://freightpilot-eaii.vercel.app/watch/
```

Paste that into the form's **Pitch Video URL** field. Verified signed-out: `200` with
`Content-Type: video/mp4` and `Accept-Ranges: bytes` (a byte-range request returns `206`, so it
seeks in the browser). The page shows the player, a poster frame, the duration badge, and the 11
chapter timestamps.

**Record it here:**

```
Pitch video link: https://freightpilot-eaii.vercel.app/watch/
Direct file:      https://freightpilot-eaii.vercel.app/watch/pitch-video.mp4
Runtime: 4 m 34 s   Tested signed-out:  [x] yes   Date tested: 2026-09-20
```

Source of truth for the recording: `brag-output-2026-09-20-221936/brag.mp4`, with
`docs/eaii/pitch-video-production-record.md` holding the full production evidence (scene plan,
narration script, timing map, and the `hyperframes check` result: 0 errors, 38/38 WCAG AA contrast).

### B2. Optional — also publish to YouTube (Unlisted)

Not required, because the Vercel link already satisfies *"shareable link, anyone with the link can
view."* But a `youtu.be` link is what reviewers expect for a video field, so if you want it:

1. Download the MP4 from `https://freightpilot-eaii.vercel.app/watch/`.
2. Go to <https://studio.youtube.com> → **Create** → **Upload videos**.
3. On the **Visibility** step choose **Unlisted**. **"Private" will fail the requirement** — a
   private video requires the viewer to be signed in and granted access.
4. You **must** also set **Audience → "No, it's not made for kids"**. If you skip this, the video
   stays in a draft state and the link will not work for anyone.
5. Publish → **Share** → **Copy link** (`https://youtu.be/XXXXXXXXXXX`).
6. Open it in a **private window signed out of Google**. It must play immediately.

Paste the YouTube URL into the form instead, and keep the `/watch/` link as the backup.

### B3. Optional — Google Drive instead

1. Upload the MP4 to Drive.
2. Right-click → **Share** → **General access** → **Anyone with the link** → role **Viewer**.
3. Test it signed out. Make sure it plays (Drive streams MP4 natively) rather than showing a
   download-only page.

### B4. Final video checks

| Check | Done |
|---|---|
| Runtime is between 3:00 and 5:00 | [x] 4 m 34 s |
| First 5 seconds play (not black/frozen) | [x] verified in the rendered file |
| Last 5 seconds play | [x] verified in the rendered file |
| Audio is audible and not clipping | [x] mean −23.6 dB, ~7 dB headroom |
| Link opens in a **signed-out private window** and plays | [x] anonymous fetch returns 200 / `video/mp4` |
| Visibility is public-link (Vercel) · **Unlisted** (YouTube) · **Anyone with the link** (Drive) | [x] public static URL |
| Not set to Private / Restricted | [x] no permission model exists on a static URL |

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

  One command closes it once you have the database password:

  ```powershell
  # Supabase Dashboard -> Settings -> Database -> Reset database password, then:
  ./scripts/rotate_and_deploy.ps1 -DryRun -DatabaseUrl 'postgresql+psycopg://postgres.huukqxpbwqcepnkrfhdw:<PASSWORD>@aws-0-us-east-1.pooler.supabase.com:6543/postgres?sslmode=require'
  # inspect the printed plan, then re-run without -DryRun to apply
  ```

  The script verifies the URL actually connects, rotates `JWT_SECRET_KEY` and
  `PROVIDER_KEY_ENCRYPTION_SECRET`, removes the dead `PASSWORD_SALT`, deploys all three Vercel
  projects, and then verifies `GET /health` reports `db:ok`. Use `-SkipConnectivityCheck` only if
  this machine is on a restricted network that cannot reach the database host.

- **No signed desktop installer yet.** The Electron shell runs from source; a signed, auto-updating
  installer is planned work.
- **The CBE/Dashen fee-schedule verification is still open.** It gates paid launch, not the product.
