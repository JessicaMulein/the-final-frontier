"""Does the narrator's register walk *inside* a full-length chapter, or only sit
at a different level *between* chapters?

Why this exists
---------------
The listener's original complaint was "it goes deeper and then higher and back as
we go along", heard while playing full rendered chapters in sequence. Two very
different faults produce that description:

  a walk    register trends across a single chapter, so the voice sinks as the
            chapter proceeds. Fish appends each rendered segment into a running
            Conversation before generating the next, so the model conditions on
            its own output -- a plausible feedback path for exactly this.
  an offset register is stable within a chapter but each chapter sits at its own
            level, so the step is heard at chapter boundaries only.

The distinction decides the fix. A walk needs the feedback path broken. An offset
needs nothing but consistent starting conditions, which anchoring already gives.

The anchor experiment could not tell these apart: its excerpts are ~180 words,
where two 12 s windows differ by more than any trend does. This measures whole
chapters already on disk, in fixed windows, and fits a trend per chapter.

No generation, no GPU. Reads the rendered WAVs only.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from prosody import estimate_f0_track
from render_chapter_fish import active_rms


def chapter_number(path: Path) -> int:
    match = re.search(r"-chapter-(\d{3})-", path.name)
    if not match:
        raise ValueError(path.name)
    return int(match.group(1))


def windows(audio: np.ndarray, rate: int, seconds: float):
    win = int(seconds * rate)
    for start in range(0, max(1, audio.size - win // 2), win):
        piece = audio[start : start + win]
        if piece.size < win // 2:
            return
        yield start / rate, piece


def measure(piece: np.ndarray, rate: int) -> tuple[float, float, float]:
    s24 = resample_poly(piece, 80, 147).astype(np.float32) if rate == 44100 else piece
    track = estimate_f0_track(s24)
    if track.size < 12:
        return 0.0, 0.0, 0.0
    db = 20 * np.log10(active_rms(piece, rate) + 1e-12)
    return float(np.median(track)), float(np.percentile(track, 20)), float(db)


def trend(values: list[float], minutes: float) -> float:
    """Least-squares slope in Hz per minute. Sign is the direction of the walk."""
    if len(values) < 4 or minutes <= 0:
        return 0.0
    x = np.linspace(0.0, minutes, len(values))
    return float(np.polyfit(x, values, 1)[0])


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--book", type=Path, default=Path("out/book"))
    p.add_argument("--window", type=float, default=15.0)
    p.add_argument("--out", type=Path, default=Path("out/trajectory.json"))
    args = p.parse_args()

    files = sorted(args.book.glob("*-fish-clean92.wav"), key=chapter_number)
    if not files:
        raise SystemExit(f"no chapter wavs in {args.book}")

    print(f"{len(files)} chapters, {args.window:.0f}s windows\n")
    print("ch   mins  wins   p20 mean   p20 sd  p20 range   Hz/min   dB/min")
    records = []
    for path in files:
        audio, rate = sf.read(str(path), always_2d=False)
        audio = np.asarray(audio, dtype=np.float32)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        medians, p20s, dbs = [], [], []
        for _, piece in windows(audio, rate, args.window):
            median, p20, db = measure(piece, rate)
            if p20 <= 0:
                continue
            medians.append(median)
            p20s.append(p20)
            dbs.append(db)
        if len(p20s) < 4:
            continue
        minutes = audio.size / rate / 60.0
        record = {
            "chapter": chapter_number(path),
            "minutes": round(minutes, 2),
            "windows": len(p20s),
            "p20_mean": round(float(np.mean(p20s)), 2),
            "p20_sd": round(float(np.std(p20s)), 2),
            "p20_range": round(float(max(p20s) - min(p20s)), 2),
            "median_mean": round(float(np.mean(medians)), 2),
            "p20_slope_hz_per_min": round(trend(p20s, minutes), 2),
            "median_slope_hz_per_min": round(trend(medians, minutes), 2),
            "level_slope_db_per_min": round(trend(dbs, minutes), 3),
            "p20_first": round(p20s[0], 2),
            "p20_last": round(p20s[-1], 2),
        }
        records.append(record)
        print(
            f"{record['chapter']:3d} {minutes:6.2f} {len(p20s):5d} "
            f"{record['p20_mean']:10.2f} {record['p20_sd']:8.2f} "
            f"{record['p20_range']:10.2f} {record['p20_slope_hz_per_min']:+8.2f} "
            f"{record['level_slope_db_per_min']:+8.3f}"
        )

    slopes = [r["p20_slope_hz_per_min"] for r in records]
    means = [r["p20_mean"] for r in records]
    sds = [r["p20_sd"] for r in records]

    print("\nWITHIN chapters (is there a walk?)")
    print(f"  p20 slope           mean {np.mean(slopes):+.2f} Hz/min, "
          f"sd {np.std(slopes):.2f}, range {min(slopes):+.2f} to {max(slopes):+.2f}")
    print(f"  chapters trending down: {sum(1 for s in slopes if s < 0)}/{len(slopes)}")
    print(f"  typical window-to-window scatter (p20 sd): {np.mean(sds):.2f} Hz")

    print("\nBETWEEN chapters (is there an offset?)")
    print(f"  p20 chapter mean    {min(means):.2f} to {max(means):.2f} Hz, "
          f"spread {max(means) - min(means):.2f} Hz, sd {np.std(means):.2f}")

    print("\nadjacent-chapter steps in playback order")
    steps = []
    for a, b in zip(records, records[1:]):
        delta = round(b["p20_mean"] - a["p20_mean"], 2)
        steps.append({"from": a["chapter"], "to": b["chapter"], "p20_delta_hz": delta})
    for s in sorted(steps, key=lambda s: -abs(s["p20_delta_hz"]))[:8]:
        semis = 12 * np.log2(
            (next(r for r in records if r["chapter"] == s["to"])["p20_mean"])
            / (next(r for r in records if r["chapter"] == s["from"])["p20_mean"])
        )
        print(f"  {s['from']:3d} -> {s['to']:3d}  {s['p20_delta_hz']:+7.2f} Hz  "
              f"{semis:+.2f} st")

    # The comparison that matters: is a chapter's own internal spread bigger or
    # smaller than the step between chapters?
    print(
        f"\nwithin-chapter p20 range (mean {np.mean([r['p20_range'] for r in records]):.2f} Hz) "
        f"vs between-chapter spread ({max(means) - min(means):.2f} Hz)"
    )

    args.out.write_text(
        json.dumps(
            {
                "window_seconds": args.window,
                "chapters": records,
                "adjacent_steps": steps,
            },
            indent=2,
        )
    )
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
