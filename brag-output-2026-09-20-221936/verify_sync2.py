"""Verify A/V sync of the rendered video against the measured narration timeline.

Two independent tests, neither of which depends on classifying a frame as a
particular scene (that fails during crossfades, where every frame is near-black
and matches any signature):

TEST 1 -- do the picture cuts happen when they should?
    Compute a frame-to-frame change signal over the whole video, find its peaks
    (the cuts/crossfades), and compare each peak with the intended scene start.
    A crossfade has a duration, so the expected peak is the midpoint of the
    transition, not its first frame.

TEST 2 -- is the audio globally time-aligned with the video?
    Extract the narration track from the rendered MP4 and cross-correlate its
    onset-strength envelope against the original narration.wav. If the muxer
    shifted the audio, the best lag is non-zero. This catches a whole-file
    offset, which TEST 1 cannot see.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import numpy as np

OUT = Path(__file__).resolve().parent
VIDEO = OUT / "brag-mg.mp4"  # the delivered cut (motion-graphics pass)
NARRATION = OUT / "narration.wav"
FPS = 30
XF = 0.6  # crossfade length used by the composition


def extract_raw(path: str, args: list[str], sr: int | None = None) -> np.ndarray:
    cmd = ["ffmpeg", "-hide_banner", "-loglevel", "error"]
    if sr:
        cmd += ["-i", path, "-ac", "1", "-ar", str(sr), "-f", "f32le", "-"]
    else:
        cmd += args + ["-"]
    p = subprocess.run(cmd, capture_output=True, check=True)
    return np.frombuffer(p.stdout, dtype=np.float32)


def main() -> int:
    scene_map = json.loads((OUT / "scene-map.json").read_text(encoding="utf-8"))
    scenes = scene_map["scenes"]

    # ---------------- TEST 1: cut placement ----------------
    # 1x1 luma per frame via ffmpeg's signalstats on a tiny scale: cheap and enough
    # to see change, but too lossy. Use 64x36 luma frames instead.
    raw = subprocess.run(
        ["ffmpeg", "-hide_banner", "-loglevel", "error", "-i", str(VIDEO),
         "-vf", "scale=64:36,format=gray", "-f", "rawvideo", "-"],
        capture_output=True, check=True,
    ).stdout
    frames = np.frombuffer(raw, dtype=np.uint8)
    n = frames.size // (64 * 36)
    frames = frames[: n * 64 * 36].reshape(n, 36, 64).astype(np.float32)
    print(f"decoded {n} frames for cut detection")

    diff = np.mean(np.abs(np.diff(frames, axis=0)), axis=(1, 2))  # len n-1
    # Smooth over the crossfade window so a transition reads as one hump.
    win = max(1, int(XF * FPS))
    kernel = np.ones(win) / win
    smooth = np.convolve(diff, kernel, mode="same")

    # Each intended boundary is scored in its OWN window. A global strongest-first
    # pick is wrong here: a high-contrast cut (e.g. into the route-plan slide) scores
    # far higher than a low-contrast one, and a global "keep strongest, suppress
    # neighbours" rule can let one boundary's peak mask a weaker boundary elsewhere.
    # The question per scene is only "is there a cut near here?", which is local.
    SEARCH = 2.5  # seconds either side

    print()
    print("TEST 1 -- picture cut vs intended scene start")
    print(f"{'scene':<6}{'intended':>11}{'peak t':>10}{'peak val':>10}{'delta':>9}  note")
    print("-" * 66)
    worst1 = 0.0
    for s in scenes[1:]:
        start = s["start"]
        lo = max(1, int((start - SEARCH) * FPS))
        hi = min(smooth.size, int((start + SEARCH) * FPS))
        if hi <= lo:
            print(f"{s['id']:<6}{start:>10.2f}s{'':>10}{'':>10}{'no window':>9}")
            worst1 = 99.0
            continue
        seg = smooth[lo:hi]
        best = lo + int(np.argmax(seg))
        cut_t = (best + 1) / FPS
        d = cut_t - start
        worst1 = max(worst1, abs(d))
        # A cut whose local peak is buried in noise means the two scenes look alike;
        # report it rather than silently claiming a pass.
        base = float(np.median(seg))
        note = "" if smooth[best] > base * 1.5 else "low contrast (scenes similar)"
        print(f"{s['id']:<6}{start:>10.2f}s{cut_t:>9.2f}s{smooth[best]:>10.2f}{d:>+8.2f}s  {note}")
    print("-" * 66)
    print(f"largest cut error: {worst1:.2f}s "
          f"(a crossfade of {XF}s means |delta| up to ~{XF/2 + 1/FPS:.2f}s is expected)")

    # ---------------- TEST 2: global audio alignment ----------------
    SR = 8000
    a_vid = extract_raw(str(VIDEO), [], sr=SR)
    a_ref = extract_raw(str(NARRATION), [], sr=SR)
    m = min(a_vid.size, a_ref.size)
    a_vid, a_ref = a_vid[:m], a_ref[:m]
    print(f"\nTEST 2 -- global audio alignment ({m/SR:.1f}s compared at {SR} Hz)")

    # Onset strength: half-wave-rectified difference of a short-window RMS.
    def envelope(x: np.ndarray, w: int = 400) -> np.ndarray:
        k = np.ones(w) / w
        rms = np.sqrt(np.convolve(x * x, k, mode="same"))
        d = np.diff(rms, prepend=rms[0])
        return np.maximum(d, 0.0)

    e_vid, e_ref = envelope(a_vid), envelope(a_ref)
    e_vid -= e_vid.mean()
    e_ref -= e_ref.mean()
    nfft = 1 << int(np.ceil(np.log2(e_vid.size + e_ref.size)))
    corr = np.fft.irfft(np.fft.rfft(e_vid, nfft) * np.conj(np.fft.rfft(e_ref, nfft)), nfft)
    corr = np.concatenate((corr[-SR * 5:], corr[: SR * 5 + 1]))
    lags = np.arange(-SR * 5, SR * 5 + 1)
    best = int(lags[int(np.argmax(corr))])
    print(f"best lag: {best / SR * 1000:+.1f} ms "
          f"(positive = video audio later than reference)")

    ok1 = worst1 <= (XF / 2 + 1.5)
    ok2 = abs(best) <= SR * 0.05  # within 50 ms
    print()
    print(f"TEST 1 cut placement : {'PASS' if ok1 else 'FAIL'} (worst {worst1:.2f}s)")
    print(f"TEST 2 audio offset  : {'PASS' if ok2 else 'FAIL'} ({best / SR * 1000:+.1f} ms)")
    print(f"\nRESULT: {'PASS' if (ok1 and ok2) else 'FAIL'}")
    return 0 if (ok1 and ok2) else 1


if __name__ == "__main__":
    raise SystemExit(main())
