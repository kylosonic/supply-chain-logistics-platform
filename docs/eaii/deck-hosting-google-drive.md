# Hosting the Pitch Deck on Google Drive (alternative to the live page)

EAII accepts **Google Drive, Canva, or a similar platform**, with sharing set to
**"Anyone with the link can view."**

The submission page (**https://freightpilot-eaii.vercel.app**) already satisfies this — it is a public
host, it needs no account, and it serves the deck inline as a 7-page PDF plus a downloadable editable
PPTX. Verified: `HTTP/1.1 200 OK` with no redirect, no `set-cookie`, no `WWW-Authenticate`.

This document is the **Google Drive** path, in case you prefer a Drive link (some reviewers find
Drive familiar, and it keeps the deck in your own Drive).

---

## Which link to use

| Option | Link | When to prefer it |
|---|---|---|
| **Live submission page** (current) | `https://freightpilot-eaii.vercel.app` | Default. One link opens the deck, the product tour and the availability statement. Reviewer sees it instantly. |
| **Direct deck PDF** | `https://freightpilot-eaii.vercel.app/deck.pdf` | If the form demands a file-type link. |
| **Google Drive** (below) | your Drive share URL | If you want the deck in your own Drive, or a reviewer specifically asks for Drive. |
| **Canva** | — | Only if you want to restyle the deck. The `.pptx` imports into Canva if needed. |

You do not need both. Pick one and put it in the form.

---

## Uploading to Google Drive

1. Download **`FreightPilot-EAII-Pitch-Deck.pdf`** from
   `https://freightpilot-eaii.vercel.app/deck.pdf`
   (or open it from `docs/eaii/FreightPilot-EAII-Pitch-Deck.pdf` in the repository).
2. Go to <https://drive.google.com> and sign in with the account you want associated with the
   submission.
3. Create a folder, e.g. `EAII Submission — FreightPilot`.
4. Upload the PDF. Optionally also upload the PPTX (editable) and the weekly-availability PDF.
5. Right-click the PDF → **Share** → **Share** again to open the full dialog.
6. Under **General access**, change **Restricted** → **Anyone with the link**.
7. Confirm the role dropdown next to it reads **Viewer** — not Editor, not Commenter.
8. Click **Copy link** → **Done**.

### The test that matters

Open the copied link in a **private/incognito window while signed out of every Google account**.

- You should see the 7-page deck rendered in Drive's viewer.
- If you see a sign-in page, or "You need access", or a **Request access** button — step 6 did not
  apply. Repeat it.

EAII's stated rule: *"Links requiring access requests will not be reviewed."* The signed-out test is
the only check that proves compliance.

---

## Record it here

```
Pitch deck link: ______________________________________________
Platform:        [ ] Vercel page   [ ] Google Drive   [ ] Canva   [ ] other ______
Tested signed out: [ ] yes        Date tested: ____________
Page/slide count seen: ______     (must be 7)
```

---

## Note on the deck file

- The PDF is **exactly 7 pages**, which is EAII's stated maximum ("no more than 7 slides").
- It covers all 10 required sections, in order, as:
  - **Slide 1** — Problem · Solution
  - **Slide 2** — Market Opportunity
  - **Slide 3** — Traction · Business Model
  - **Slide 4** — Go To Market · Competition
  - **Slide 5** — Core Team and Advisor
  - **Slide 6** — Financial Projection
  - **Slide 7** — The Ask
- The **PPTX** is the same 7 slides as native, editable PowerPoint, in case a reviewer asks for an
  editable copy or you want to restyle it in Canva.
