"""Rebuild the scene map and the composition's clip timings from measured audio.

Input : scene-timing.measured.json  (produced by measure_timing.py via ASR)
Output: scene-map.json              (scene boundaries, paragraphs grouped)
        composition/index.html      (data-start / data-duration rewritten)

The paragraph->scene grouping is unchanged from the original scene-map.json; only
the *numbers* are replaced, and they now come from measuring narration.wav rather
than from proportional word counts.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

OUT = Path(__file__).resolve().parent
COMP = OUT / "composition" / "index.html"
TOTAL = 273.6

# paragraph -> scene.
#
# Re-derived against the MEASURED timeline. The original grouping was fitted to the
# derived word-count timeline and, once the real onsets were known, put each scene's
# visuals in front of the wrong paragraphs -- e.g. the bank-transfer visual (s5) was
# aligned with paragraph 6 ("Then the first route optimization"), and the isolation
# visual with paragraph 5.
#
# The boundaries below are the chapter boundaries that were published on the video
# page, which the audio independently confirms (each one coincides with a measured
# paragraph onset within 0.45s).
SCENES = [
    ("s1", "The driver calls", [1, 2, 3]),
    ("s2", "One surface", [4, 5]),
    ("s3", "The first route plan", [6]),
    ("s4", "After the plan", [7]),
    ("s5", "The cashflow wedge", [8, 9]),
    ("s6", "Isolation", [10]),
    ("s7", "The audit", [11, 12]),
    ("s8", "Model and traction", [13, 14]),
    ("s9", "Team and the honest gap", [15]),
    ("s10", "The ask", [16, 17]),
    ("s11", "Close", [18, 19]),
]


def main() -> int:
    measured = json.loads((OUT / "scene-timing.measured.json").read_text(encoding="utf-8"))
    by_index = {r["index"]: r for r in measured}
    old_map = json.loads((OUT / "scene-map.json").read_text(encoding="utf-8"))
    old_by_id = {s["id"]: s for s in old_map["scenes"]}

    starts = [by_index[g[0]]["start"] for _, _, g in SCENES]
    for a, b in zip(starts, starts[1:]):
        if b <= a:
            raise SystemExit(f"non-monotonic scene starts: {starts}")

    scenes = []
    for i, (sid, name, paras) in enumerate(SCENES):
        start = by_index[paras[0]]["start"]
        end = by_index[paras[-1]]["end"]
        if i + 1 < len(SCENES):
            end = by_index[SCENES[i + 1][2][0]]["start"]
        else:
            end = TOTAL
        # Paragraph 3 starts exactly where paragraph 2 ends, so scene 1 absorbs it.
        if i == 0:
            start = 0.0
        scenes.append({
            "id": sid,
            "start": round(start, 2),
            "duration": round(end - start, 2),
            "name": name,
            "paras": paras,
        })

    total = sum(s["duration"] for s in scenes)
    print(f"{'scene':<5} {'name':<26} {'derived':>9} {'measured':>9} {'dur':>7}  shift")
    print("-" * 78)
    for s in scenes:
        o = old_by_id[s["id"]]
        print(f"{s['id']:<5} {s['name']:<26} {o['start']:>8.1f}s {s['start']:>8.2f}s "
              f"{s['duration']:>6.2f}s  {s['start'] - o['start']:>+6.2f}s")
    print("-" * 78)
    print(f"sum of durations: {total:.2f}s (target {TOTAL}s)")
    if abs(total - TOTAL) > 0.05:
        print(f"WARNING: durations do not sum to {TOTAL}s "
              f"(diff {total - TOTAL:+.2f}s)")
    worst = max(abs(s["start"] - old_by_id[s["id"]]["start"]) for s in scenes)
    print(f"largest correction applied: {worst:.2f}s")

    out = {
        "total_duration": TOTAL,
        "narration": "narration.wav",
        "source": ("narration.wav measured by ASR word alignment "
                   "(measure_timing.py); scene boundaries are measured paragraph "
                   "onsets, not proportional word counts."),
        "music_volume": old_map["music_volume"],
        "note_music": old_map["note_music"],
        "scenes": scenes,
    }
    (OUT / "scene-map.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print("\nwrote scene-map.json")

    html = COMP.read_text(encoding="utf-8")

    # --- 1. the clip elements -------------------------------------------------
    applied = 0
    for s in scenes:
        pat = re.compile(
            r'(<div class="scene clip" id="' + s["id"] + r'"\s+data-start=")[\d.]+'
            r'("\s+data-duration=")[\d.]+(")'
        )
        html, n = pat.subn(
            lambda m: f'{m.group(1)}{s["start"]}{m.group(2)}{s["duration"]}{m.group(3)}',
            html,
        )
        if n != 1:
            raise SystemExit(f"expected 1 substitution for {s['id']}, made {n}")
        applied += n

    # --- 2. the gsap timeline's own copy of the same numbers ------------------
    # These were duplicated by hand and drifted from the clip attributes; they are
    # now regenerated from the same measured source so the entrance animations
    # cannot fire at a different time from the cut.
    # 'in' is the entrance duration: eased crossfade length per scene.
    in_dur = {"s1": 0.70, "s11": 0.90}
    rows = ",\n".join(
        "      {{ id: '{id}',{pad}start: {start},{pad2}dur: {dur}, in: {inn} }}".format(
            id=s["id"],
            pad=" " * (4 - len(s["id"])),
            pad2=" " * (5 - len(s["id"])),
            start=s["start"],
            dur=s["duration"],
            inn=in_dur.get(s["id"], 0.70),
        )
        for s in scenes
    )
    js_pat = re.compile(r"(    const SCENES = \[\n)(.*?)(\n    \];)", re.S)
    html, n = js_pat.subn(lambda m: m.group(1) + rows + m.group(3), html, count=1)
    if n != 1:
        raise SystemExit(f"expected to rewrite the SCENES array once, made {n}")

    # --- 3. the final fade, which must start at the last scene's fade-in ------
    end_fade = round(max(0.0, TOTAL - 1.2), 2)
    fade_pat = re.compile(r"(tl\.to\('#s11', \{ opacity: 0, duration: 1\.1, ease: 'power2\.inOut' \}, )[\d.]+(\);)")
    html, n = fade_pat.subn(lambda m: f"{m.group(1)}{end_fade}{m.group(2)}", html, count=1)
    if n != 1:
        raise SystemExit(f"expected to rewrite the closing fade once, made {n}")

    COMP.write_text(html, encoding="utf-8")
    print(f"rewrote composition/index.html: {applied} scene clips, "
          f"SCENES array, closing fade at {end_fade}s")

    print("\nverifying written values:")
    for line in COMP.read_text(encoding="utf-8").splitlines():
        if 'class="scene clip"' in line or "id: 's" in line or "tl.to('#s11'" in line:
            print("  " + line.strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
