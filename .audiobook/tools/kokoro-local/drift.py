#!/usr/bin/env python3
"""Profile progressive prosody drift inside a generation unit.

Why this exists
---------------
The qvoice runtime degrades as an autoregressive generation gets longer: the
voice slows, words smear, and active level decays. In the chapter-3 pilot a
listener flagged three separate stretches as the narrator "drifting off like she
is on drugs", and all three sat in the last quarter of a 72-93 s generation. The
one chunk that generated only 34 s was not flagged.

Every text-based gate missed it. `verify_chunk` and `validate_stt` ask whether
the right words are present, and Whisper reconstructs slurred speech happily, so
a chunk whose tail sat 4.6 dB down with a word smeared to 1.68 s still scored
wer=0.066 / coverage=0.988 and shipped.

Scope, deliberately limited
---------------------------
This module REPORTS, it does not judge. An earlier version of it tried to be an
accept/reject gate on a first-third versus last-third comparison; validated
against the listener's own calls it flagged 1 of 3 bad chunks and rated the
best-sounding chunk worst of all, because thirds-medians average away the local
degradation that is audible and because sentence-final words absorb trailing
pauses. Those statistics are not a reliable perceptual proxy at this sample size.

So the fix for drift belongs upstream, in keeping generation units short enough
that the model stays in its stable region. This module's job is to make the
effect visible and to let a before/after comparison be quantitative rather than
anecdotal. Use `--windows` to see where inside a unit delivery falls apart.
"""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

SAMPLE_RATE = 24_000
WINDOW_SECONDS = 8.0
WINDOW_HOP = 4.0
MIN_SECONDS = 12.0
MIN_WORDS = 16


def voiced_rms(audio: np.ndarray, *, floor_db: float = -36.0) -> float:
    """RMS over voiced 20 ms frames only, so pauses do not dilute the level."""
    frame = max(1, int(SAMPLE_RATE * 0.020))
    usable = (audio.size // frame) * frame
    if usable == 0:
        return 0.0
    frames = audio[:usable].reshape(-1, frame).astype(np.float64)
    rms = np.sqrt((frames**2).mean(axis=1) + 1e-12)
    peak = float(rms.max())
    if peak <= 0:
        return 0.0
    voiced = rms[rms >= peak * 10 ** (floor_db / 20)]
    return float(np.sqrt(np.mean(voiced**2))) if voiced.size else 0.0


def word_timings(audio: np.ndarray, *, model: str, language: str = "en") -> list[dict]:
    """Word-level timings for one generation unit."""
    import mlx_whisper

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
        temp = Path(handle.name)
    try:
        sf.write(str(temp), audio, SAMPLE_RATE)
        result = mlx_whisper.transcribe(
            str(temp),
            path_or_hf_repo=model,
            language=language,
            word_timestamps=True,
            verbose=False,
            condition_on_previous_text=False,
        )
    finally:
        temp.unlink(missing_ok=True)

    words = []
    for segment in result.get("segments", []):
        for word in segment.get("words", []) or []:
            start, end = float(word["start"]), float(word["end"])
            token = (word.get("word") or "").strip()
            if end > start and token:
                words.append({"token": token, "start": start, "end": end})
    return words


def profile(
    audio: np.ndarray,
    *,
    words: list[dict] | None = None,
    model: str | None = None,
    window: float = WINDOW_SECONDS,
    hop: float = WINDOW_HOP,
) -> dict:
    """Sliding-window delivery profile for one generation unit.

    Reports, per window, words per second, median word duration and voiced level
    relative to the unit's own median, plus the worst window on each axis. All
    figures are relative to the unit itself, so they do not depend on how fast or
    loud the voice is overall.
    """
    seconds = audio.size / SAMPLE_RATE
    if words is None:
        if model is None:
            raise ValueError("profile() needs either words= or model=")
        words = word_timings(audio, model=model)

    report: dict = {"seconds": round(seconds, 3), "words": len(words), "windows": []}
    if seconds < MIN_SECONDS or len(words) < MIN_WORDS:
        report["skipped"] = True
        report["reason"] = "too short to profile"
        return report
    report["skipped"] = False

    start = 0.0
    while start + window <= seconds + 1e-9:
        inside = [w for w in words if w["start"] >= start and w["end"] <= start + window]
        if len(inside) >= 3:
            durs = np.array([w["end"] - w["start"] for w in inside])
            clip = audio[int(start * SAMPLE_RATE) : int((start + window) * SAMPLE_RATE)]
            report["windows"].append(
                {
                    "at": round(start, 2),
                    "wps": round(len(inside) / window, 3),
                    "median_word_ms": round(float(np.median(durs)) * 1000, 1),
                    "p90_word_ms": round(float(np.percentile(durs, 90)) * 1000, 1),
                    "rms": round(voiced_rms(clip), 6),
                }
            )
        start += hop

    if not report["windows"]:
        report["skipped"] = True
        report["reason"] = "no usable windows"
        return report

    wps = np.array([w["wps"] for w in report["windows"]])
    rms = np.array([w["rms"] for w in report["windows"]])
    med_wps = float(np.median(wps))
    med_rms = float(np.median(rms[rms > 0])) if (rms > 0).any() else 0.0
    slowest = report["windows"][int(np.argmin(wps))]
    quietest = report["windows"][int(np.argmin(np.where(rms > 0, rms, np.inf)))]

    # Trend across the unit: least-squares slope, normalised to the median, so
    # "loses 30% of its level over the unit" reads as -0.30.
    t = np.array([w["at"] for w in report["windows"]], dtype=float)
    span = max(1e-9, t[-1] - t[0]) if t.size > 1 else 1.0

    def trend(values: np.ndarray, median: float) -> float:
        if t.size < 2 or median <= 0:
            return 0.0
        slope = float(np.polyfit(t, values, 1)[0])
        return round(slope * span / median, 4)

    longest = max(words, key=lambda w: w["end"] - w["start"])
    report["summary"] = {
        "median_wps": round(med_wps, 3),
        "slowest_window": {"at": slowest["at"], "wps": slowest["wps"]},
        "slowest_vs_median": round(slowest["wps"] / med_wps, 3) if med_wps else 0.0,
        "wps_trend": trend(wps, med_wps),
        "median_rms": round(med_rms, 6),
        "quietest_window_db": (
            round(20 * float(np.log10(quietest["rms"] / med_rms)), 2)
            if med_rms > 0 and quietest["rms"] > 0
            else 0.0
        ),
        "quietest_at": quietest["at"],
        "rms_trend": trend(rms, med_rms),
        "longest_word": {
            "token": longest["token"],
            "ms": round((longest["end"] - longest["start"]) * 1000, 1),
            "at": round(longest["start"], 2),
        },
    }
    return report


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("wav", type=Path, nargs="+")
    p.add_argument("--model", default="mlx-community/whisper-large-v3-turbo")
    p.add_argument("--windows", action="store_true", help="print every window")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    report = {}
    for path in args.wav:
        audio, sr = sf.read(str(path), always_2d=False)
        audio = np.asarray(audio, dtype=np.float32)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        result = profile(audio, model=args.model)
        report[str(path)] = result
        if args.json:
            continue
        if result["skipped"]:
            print(f"{path.name}: skipped ({result['reason']})")
            continue
        s = result["summary"]
        print(
            f"{path.name:34s} {result['seconds']:6.1f}s  "
            f"wps {s['median_wps']:.2f} (slowest {s['slowest_window']['wps']:.2f} "
            f"@{s['slowest_window']['at']:.0f}s = {s['slowest_vs_median']:.2f}x, "
            f"trend {s['wps_trend']:+.2f})  "
            f"level (quietest {s['quietest_window_db']:+.1f}dB @{s['quietest_at']:.0f}s, "
            f"trend {s['rms_trend']:+.2f})  "
            f"longest {s['longest_word']['token']!r} {s['longest_word']['ms']:.0f}ms"
        )
        if args.windows:
            print("      at    wps  med_ms  p90_ms     rms")
            for w in result["windows"]:
                print(
                    f"  {w['at']:6.1f} {w['wps']:6.2f} {w['median_word_ms']:7.0f}"
                    f" {w['p90_word_ms']:7.0f} {w['rms']:.4f}"
                )
    if args.json:
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
