"""Measure real narration timings by ASR, then rebuild the scene map from them.

Why this exists
---------------
`derive_timing.py` computed paragraph durations as
`words(paragraph) / words(total) * 273.6` -- proportional word counts, which
assume a perfectly constant speaking rate. It also hardcoded `total_words`
implicitly via a stale constant: the script contains 748 words but the timing
run divided by 856 (a number from an earlier draft of the script). Both defects
push every scene cue earlier than the voice, which is what "the audio is ahead
of the video" means in practice.

This script replaces the estimate with a measurement:
  1. transcribe narration.wav with faster-whisper -> word-level timestamps
  2. align the recognised words to the known script text (difflib)
  3. read off the true start/end of each paragraph
  4. regroup paragraphs into scenes and emit scene-map.json + scene-timing.json

Alignment is on the *known* script, so ASR spelling errors correct themselves:
we only need the ASR to tell us *when* each word was spoken, not what it was.
"""
from __future__ import annotations

import difflib
import json
import re
import sys
from pathlib import Path

OUT = Path(__file__).resolve().parent
AUDIO = OUT / "narration.wav"
VIDEO_DURATION = 273.6
WORD_RE = re.compile(r"[a-z0-9]+")


def norm(text: str) -> str:
    return " ".join(WORD_RE.findall(text.lower()))


def words_of(text: str) -> list[str]:
    return WORD_RE.findall(text.lower())


def main() -> int:
    script = (OUT / "narration-script.txt").read_text(encoding="utf-8").strip()
    paragraphs = [p.strip() for p in script.split("\n\n") if p.strip()]
    para_words = [words_of(p) for p in paragraphs]

    print(f"script: {len(paragraphs)} paragraphs, "
          f"{sum(len(w) for w in para_words)} words")

    from faster_whisper import WhisperModel

    print("loading model small.en (int8)...", flush=True)
    model = WhisperModel("small.en", device="cpu", compute_type="int8")
    segments, info = model.transcribe(
        str(AUDIO),
        language="en",
        word_timestamps=True,
        vad_filter=False,
        beam_size=5,
        condition_on_previous_text=False,
    )
    print(f"detected language={info.language} "
          f"prob={info.language_probability:.3f} duration={info.duration:.2f}s",
          flush=True)

    asr: list[dict] = []
    for seg in segments:
        for w in (seg.words or []):
            tok = norm(w.word)
            if tok:
                asr.append({"t": tok, "start": float(w.start), "end": float(w.end)})
    print(f"ASR produced {len(asr)} timed words", flush=True)
    if len(asr) < 100:
        print("ERROR: too few recognised words; ASR did not work", file=sys.stderr)
        return 1

    # Flatten the script to a single token stream, remembering which paragraph
    # each token belongs to.
    script_tokens: list[str] = []
    owner: list[int] = []
    for pi, ws in enumerate(para_words, start=1):
        for w in ws:
            script_tokens.append(w)
            owner.append(pi)

    asr_tokens = [a["t"] for a in asr]
    print(f"aligning {len(script_tokens)} script tokens "
          f"to {len(asr_tokens)} ASR tokens...", flush=True)

    sm = difflib.SequenceMatcher(a=script_tokens, b=asr_tokens, autojunk=False)
    # script index -> (start, end) of the matching ASR word
    timing: dict[int, tuple[float, float]] = {}
    for a0, b0, size in sm.get_matching_blocks():
        for k in range(size):
            src = asr[b0 + k]
            timing[a0 + k] = (src["start"], src["end"])

    coverage = len(timing) / len(script_tokens)
    ratio = sm.ratio()
    print(f"matched {len(timing)}/{len(script_tokens)} script tokens "
          f"({coverage:.1%}), similarity={ratio:.3f}")
    if coverage < 0.80:
        print("ERROR: alignment coverage too low to trust", file=sys.stderr)
        return 1

    # Paragraph boundaries from matched words. Unmatched words are interpolated
    # between their nearest matched neighbours.
    para_start: list[float] = []
    para_end: list[float] = []
    for pi in range(1, len(paragraphs) + 1):
        idxs = [i for i, o in enumerate(owner) if o == pi]
        hits = [i for i in idxs if i in timing]
        if not hits:
            print(f"ERROR: paragraph {pi} has no aligned words", file=sys.stderr)
            return 1
        # Interpolate any leading/trailing unmatched words using local pace.
        first, last = hits[0], hits[-1]
        if len(hits) >= 2:
            span = timing[last][1] - timing[first][0]
            per = span / (last - first + 1)
        else:
            per = 0.3
        start = timing[first][0] - per * (first - idxs[0])
        end = timing[last][1] + per * (idxs[-1] - last)
        para_start.append(max(0.0, start))
        para_end.append(end)

    rows = []
    for i, p in enumerate(paragraphs):
        rows.append({
            "index": i + 1,
            "words": len(para_words[i]),
            "start": round(para_start[i], 2),
            "duration": round(para_end[i] - para_start[i], 2),
            "end": round(para_end[i], 2),
            "head": " ".join(p.split()[:10]),
        })

    print()
    print(f"{'#':>3}  {'words':>5}  {'start':>8}  {'end':>8}  {'vs derived':>11}  opening words")
    print("-" * 100)
    old = json.loads((OUT / "scene-timing.json").read_text(encoding="utf-8"))
    old_start = {r["index"]: r["start"] for r in old}
    for r in rows:
        delta = r["start"] - old_start.get(r["index"], r["start"])
        print(f"{r['index']:>3}  {r['words']:>5}  {r['start']:>8.2f}  {r['end']:>8.2f}  "
              f"{delta:>+10.2f}s  {r['head']}")

    # Sanity: monotonic and inside the file.
    for a, b in zip(rows, rows[1:]):
        if b["start"] < a["start"]:
            print(f"ERROR: non-monotonic at paragraph {b['index']}", file=sys.stderr)
            return 1
    if rows[-1]["end"] > VIDEO_DURATION + 0.5:
        print(f"WARNING: last paragraph ends at {rows[-1]['end']}s, "
              f"beyond video duration {VIDEO_DURATION}s")

    (OUT / "scene-timing.measured.json").write_text(
        json.dumps(rows, indent=2), encoding="utf-8")
    print(f"\nwrote scene-timing.measured.json ({len(rows)} paragraphs)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
