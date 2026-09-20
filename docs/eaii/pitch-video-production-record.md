# Pitch Video — Production Record

**File:** `brag-output-2026-09-20-221936/brag.mp4`
**Live URL:** https://freightpilot-eaii.vercel.app/pitch-video.mp4
**Runtime:** 4 minutes 33.6 seconds (273.6s) — EAII window is 3–5 minutes ✅
**Format:** MP4 · H.264 · 1920×1080 · 30 fps · AAC 48 kHz stereo · 18.1 MB

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
- **Scene timing** — derived from the script's word counts against that measured total
  (`derive_timing.py` → `scene-timing.json`), because Whisper is not installed so word-level
  timestamps were unavailable. This is arithmetic on two measured quantities, not a pace estimate.
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

### Two defects found and fixed during production

1. **Duplicate audio track.** Overlapping two music `<audio>` elements on the same
   `data-track-index` tripled loudness in the overlap window. Caught by `hyperframes lint`
   (`duplicate_audio_track`), which was an **error**, not a warning. Fixed by pre-rendering one
   continuous bed so a single clip covers the whole piece.
2. **Dead video button.** The submission page's video button pointed at a literal
   `__VIDEO_URL__` placeholder — a reviewer clicking it would have hit a 404. It now embeds the
   real MP4 with a poster frame and a download link.

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
| `brag.mp4` | **The pitch video.** 4:33.6, 18.1 MB |
| `brag.jpg` | Poster frame — the route-plan proof moment (21.07 km / 31.61 ETB) |
| `brag-thumb.jpg` | 300×300 thumbnail for video listings |
| `brag-plan.md` | The `/brag` plan: angle, hook, storyboard, audio direction, readability ledger |
| `narration-script.txt` | The spoken script (748 words) |
| `narration.wav` | Generated narration, 12.5 MB |
| `scene-timing.json` · `derive_timing.py` | Scene boundaries and the arithmetic that produced them |
| `scene-map.json` | Scene → paragraph mapping with start times |
| `share-copy.txt` | Social copy for the post |
| `composition/` | The HyperFrames composition: `index.html`, assets, audio |
