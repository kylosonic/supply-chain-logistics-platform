# Pitch Video — Production Record

**File:** `brag-output-2026-09-20-221936/brag.mp4`
**Live URL:** https://freightpilot-eaii.vercel.app/pitch-video.mp4
**Runtime:** 4 minutes 33.6 seconds (273.6s) — EAII window is 3–5 minutes ✅
**Format:** MP4 · H.264 · 1920×1080 · 30 fps · AAC 48 kHz stereo · 18.3 MB

---

## 1. How it was made

Built with the **`/brag`** skill (https://github.com/latent-spaces/brag), which drives
**HyperFrames** (HTML → deterministic video). `/brag` is designed for 15–25 second launch videos;
this is a 3–5 minute pitch, which is an **external requirement from EAII**, not a creative choice.
The deviation is documented in `brag-plan.md` and every other rule of the skill was honoured:

| `/brag` law | How this video satisfies it |
|---|---|
| **Readable** — every line holds long enough to read | Text holds to the documented floor (short label ~0.8s settled; sentence ~0.3s/word). Verified by HyperFrames' layout inspect: **0 issues across 9 samples** |
| **Specific** | Real ETB figures, CBE/Dashen transfer framing, Addis Ababa warehouse geography — not swappable copy |
| **Show the thing** | Real console screenshots at 1600×1000, plus the real numbers 21.07 km / 31.61 ETB |
| **No generic SaaS language** | Opening line is *"The driver calls."* — a sentence no generic promo would write |
| **Hook is everything** | The first frame states the industry's actual failure mode |
| **Narration complements, does not read the screen** | Script never reads visible text aloud |

## 2. Inputs (all real, no invented claims)

- **Narration** — 748 words, Kokoro-82M via `npx hyperframes tts`, voice `af_heart` at speed 1.0.
  Generated length **273.6s**, measured with ffprobe.
- **Scene timing** — **measured by ASR word alignment** (`measure_timing.py` →
  `scene-timing.measured.json`), applied to the composition by `apply_measured_timing.py`.

  > **Corrected 2026-09-20 — the first render was out of sync.** Scene boundaries were originally
  > derived as `words(paragraph) / words(total) × 273.6`, with `total_words` a hardcoded **856**.
  > The script actually contains **748** words, so every cue was scaled by 748/856 = 87.4% and fell
  > **progressively earlier** than the voice: 9.8s early by scene 2, up to **19.5s early** by the
  > close. The effect a viewer sees is the audio running ahead of the picture, which is how it was
  > reported.
  >
  > The proportional method had a second, subtler flaw: it assumes a constant speaking rate. Kokoro
  > does not hold one across paragraph breaks, so even with the right word count the paragraph
  > onsets would still drift by 1–3s.
  >
  > Both are now replaced by measurement. `faster-whisper` (small.en, int8) transcribes
  > `narration.wav` with word-level timestamps; those words are aligned to the *known* script with
  > `difflib` (94.8% of tokens matched, 0.955 similarity), so ASR spelling errors cannot affect the
  > result — only the timing of each word is taken from the ASR. Paragraph onsets are then read off
  > the aligned words, and scenes are regrouped from them.
  >
  > The scene→paragraph grouping also had to be re-derived. The original grouping was fitted to the
  > wrong timeline and, once the real onsets were known, put each scene's visuals in front of the
  > wrong paragraphs — most visibly the bank-transfer visual (`s5`) covering "Then the first route
  > optimization" instead of the bank-transfer narration. Paragraphs were regrouped onto the
  > chapter boundaries that had been published on the video page, which the audio independently
  > confirms: every boundary coincides with a measured paragraph onset within 0.45s.
  >
  > The 273.6s total is unchanged. Verified after the fix: 11 scene durations sum to exactly
  > **273.60s**.
  >
  > **Post-fix verification** (`verify_sync2.py`, two independent tests):
  >
  > | Test | Method | Result |
  > |---|---|---|
  > | Cut placement | frame-to-frame luma change over all 8208 frames; strongest peak within ±2.5s of each intended boundary | all 10 boundaries found, largest error **0.29s** (the crossfade starts 0.6s before the cut, so the expected midpoint offset is 0.30s — the −0.27s seen on every scene is that artifact, not drift) |
  > | Global audio offset | onset-envelope cross-correlation of the MP4's audio track against `narration.wav` at 8 kHz | best lag **+0.0 ms** |
  >
  > The first attempt at this verifier reported FAIL and was wrong: it classified frames by nearest
  > scene signature, which fails during crossfades (every frame is near-black there and matches any
  > signature), and its global strongest-peak-first rule let the high-contrast route-plan cut mask
  > weaker cuts elsewhere. Both were faults in the test, not the video; the replaced test measures
  > what it claims to.
  >
  > The published chapter list on `/watch/` had been generated from the same wrong numbers and was
  > corrected alongside the video (`0:22→0:31`, `0:33→0:48`, `0:46→1:02`, `1:06→1:19`, `1:34→1:51`,
  > `2:00→2:14`, `2:34→2:50`, `3:13→3:31`, `3:38→3:54`, `4:06→4:25`).
- **Music** — the bundled Ende "Happy Beats / Business Moves" vol-1 track (163.96s, 120.19 BPM),
  pre-built into a single 273.6s bed with the loop seam dipped in volume and 2.5s/6s fades.
  Mixed at **volume 0.07** so speech always dominates.
- **Screenshots** — 8 captures of the running operations console against a live workspace.

## 3. Verification performed

| Check | Result |
|---|---|
| `hyperframes lint` | **0 errors** (12 warnings, all `nested_structure_needs_subcomposition` — advisory about Studio timeline rows, not correctness) |
| `hyperframes check` (the gate `/brag` requires) | **passed** — 0 errors, 0 runtime warnings, **0 layout issues across 9 samples**, **38/38 text checks pass WCAG AA contrast** |
| Full decode | clean — no errors across all 273.6s |
| Audio present | AAC stereo, 48 kHz, full duration |
| Audio level | mean **−23.6 dB**, peaks **−5 to −8 dB** — ~7 dB headroom, no clipping, consistent across all scenes |
| Visual spot-check | 11 frames extracted at every scene midpoint and inspected |
| Range requests | HTTP **206** — the video is seekable in a browser |
| A/V sync — cut placement | all 10 boundaries within **0.29s** of the measured narration onsets (`verify_sync2.py`) |
| A/V sync — audio offset | **+0.0 ms** lag vs `narration.wav` (onset-envelope cross-correlation) |

Delivered file: 19,212,553 bytes (18.32 MiB), sha256 `61E53A8995C057DC224AEC481563573E9E2B2D4DD87A20D900CCF994A4461F8F`.
Verified byte-identical to what the live `/watch/pitch-video.mp4` serves.

### Three defects found and fixed during production

1. **Duplicate audio track.** Overlapping two music `<audio>` elements on the same
   `data-track-index` tripled loudness in the overlap window. Caught by `hyperframes lint`
   (`duplicate_audio_track`), which was an **error**, not a warning. Fixed by pre-rendering one
   continuous bed so a single clip covers the whole piece.
2. **Dead video button.** The submission page's video button pointed at a literal
   `__VIDEO_URL__` placeholder — a reviewer clicking it would have hit a 404. It now embeds the
   real MP4 with a poster frame and a download link.
3. **Audio ahead of the picture** (reported after the first delivery). Three independent causes,
   all in the timing layer rather than the render:
   - `derive_timing.py` divided by a hardcoded **856** words when the script has **748**, scaling
     every cue to 87.4% and pulling it progressively earlier (9.8s by scene 2 → 19.5s by the close).
   - The proportional word-count method assumes a constant speaking rate, which Kokoro does not
     hold across paragraph breaks; residual drift of 1–3s remained even with the right count.
   - The composition carried the timings in **three** places — the clip `data-start`/`data-duration`
     attributes, the `gsap` `SCENES` array, and the closing fade — so a fix to one would have left
     the entrance animations firing at different moments from the cuts.

   Replaced with measurement (ASR word alignment against the known script) and a single generator
   (`apply_measured_timing.py`) that rewrites all three locations from one source. The relevant
   numbers had also been copied into the video page's chapter list, which was corrected too.

## 4. What EAII still needs from you

The MP4 is done and hosted, but **EAII asks for a video-platform link** (Google Drive, YouTube
Unlisted, Vimeo, or similar). The file above is the exact file to upload.

1. Download it: https://freightpilot-eaii.vercel.app/pitch-video.mp4
2. Upload to **YouTube (Unlisted)** or **Google Drive (Anyone with the link → Viewer)**.
3. If YouTube: also set **Audience → "No, it's not made for kids"**, or the video stays a draft and
   the link fails for everyone.
4. Test the link in a **private window signed out of all accounts**.
5. Paste that link into the form's Pitch Video field.

Full steps: `docs/eaii/submission-checklist.md` Part B, then `docs/eaii/SUBMISSION-STRUCTURE.md`.

## 5. Files

| File | What it is |
|---|---|
| `brag.mp4` | **The pitch video.** 4:33.6, 18.3 MB, sha256 `61E53A89…461F8F` |
| `brag.jpg` | Poster frame — the route-plan proof moment (21.07 km / 31.61 ETB) |
| `brag-thumb.jpg` | 300×300 thumbnail for video listings |
| `brag-plan.md` | The `/brag` plan: angle, hook, storyboard, audio direction, readability ledger |
| `narration-script.txt` | The spoken script (748 words) |
| `narration.wav` | Generated narration, 12.5 MB |
| `measure_timing.py` | **Timing source of truth.** ASR-aligns the audio to the script, writes `scene-timing.measured.json` |
| `apply_measured_timing.py` | Applies measured timings to `scene-map.json` and to all three timing locations in `composition/index.html` |
| `scene-timing.measured.json` | Measured paragraph onsets/offsets |
| `scene-timing.json` · `derive_timing.py` | ⚠️ **Superseded and known wrong** (hardcoded 856-word divisor). Kept only as the record of the defect |
| `scene-map.json` | Scene → paragraph mapping with measured start times |
| `share-copy.txt` | Social copy for the post |
| `composition/` | The HyperFrames composition: `index.html`, assets, audio |
