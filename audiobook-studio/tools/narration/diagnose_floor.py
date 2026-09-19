#!/usr/bin/env python3
"""Find where the noise floor rises, and whether the pipeline put it there.

The listener reports background that "opens up now and then". That phrasing points
at something periodic rather than constant, and this pipeline does exactly one
periodic thing to the background: `comfort_gap` synthesises 650 ms of room tone
between every paragraph, shaped from the render's own quiet frames. Chapter 5 has
about thirty of those.

Two other stages can also lift a floor. `flatten_slope` applies up to a 6 dB ramp
inside a segment to cancel a fade, and boosting the quiet end of a segment raises
its noise with the speech. `match_levels` adds up to 2 dB per segment.

So this compares three populations directly:

  INSERTED TONE   sustained low-level runs near 650 ms -- the synthesised gaps
  NATURAL PAUSE   short low-level runs inside a paragraph -- the model's own floor
  UNDER SPEECH    the quietest frames while speech is present

If the inserted tone sits above the natural pause floor, or is spectrally brighter,
that is the defect and it is mine, not the model's.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf

FRAME_MS = 20.0


def load(path: Path) -> tuple[np.ndarray, int]:
    audio, rate = sf.read(str(path), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return audio, int(rate)


def frames(audio: np.ndarray, rate: int) -> tuple[np.ndarray, float]:
    size = int(rate * FRAME_MS / 1000)
    count = audio.size // size
    block = audio[: count * size].reshape(count, size).astype(np.float64)
    return np.sqrt((block**2).mean(axis=1) + 1e-12), size / rate


def hf_ratio(audio: np.ndarray, rate: int, start: float, end: float) -> float:
    """Energy above 4 kHz. Hiss lives up there; a voice's floor is darker."""
    a, b = int(start * rate), int(end * rate)
    seg = audio[a:b].astype(np.float64)
    n = 1024
    if seg.size < n:
        return 0.0
    freqs = np.fft.rfftfreq(n, 1 / rate)
    window = np.hanning(n)
    ratios = []
    for offset in range(0, seg.size - n, n // 2):
        power = np.abs(np.fft.rfft(seg[offset : offset + n] * window)) ** 2
        total = power.sum()
        if total > 0:
            ratios.append(float(power[freqs > 4000].sum() / total))
    return float(np.mean(ratios)) if ratios else 0.0


def runs_below(level: np.ndarray, threshold: float, hop: float):
    out = []
    start = None
    for index, value in enumerate(level):
        if value < threshold and start is None:
            start = index
        elif value >= threshold and start is not None:
            out.append((start * hop, index * hop))
            start = None
    if start is not None:
        out.append((start * hop, len(level) * hop))
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("audio", type=Path)
    p.add_argument("--gap-ms", type=float, default=650.0)
    p.add_argument("--tolerance-ms", type=float, default=180.0)
    args = p.parse_args()

    audio, rate = load(args.audio)
    level, hop = frames(audio, rate)
    speech = float(np.percentile(level, 90))
    quiet_threshold = speech * 10 ** (-26 / 20)

    all_runs = runs_below(level, quiet_threshold, hop)
    target = args.gap_ms / 1000
    tolerance = args.tolerance_ms / 1000

    inserted, natural = [], []
    for start, end in all_runs:
        duration = end - start
        if duration < 0.08:
            continue
        (inserted if abs(duration - target) <= tolerance else natural).append(
            (start, end, duration)
        )

    def describe(name: str, group: list[tuple[float, float, float]]) -> dict:
        if not group:
            print(f"  {name:16s} none found")
            return {}
        levels, hfs = [], []
        for start, end, _ in group:
            a, b = int(start / hop), int(end / hop)
            core = level[a + 2 : max(a + 3, b - 2)]  # skip fades at the edges
            if core.size:
                levels.append(float(np.median(core)))
                hfs.append(hf_ratio(audio, rate, start + 0.05, end - 0.05))
        if not levels:
            print(f"  {name:16s} none measurable")
            return {}
        median = float(np.median(levels))
        db = 20 * np.log10(median / speech) if median > 0 else 0.0
        print(
            f"  {name:16s} n={len(levels):3d}  level {median:.6f} "
            f"({db:+6.1f} dB rel speech)  hf>4k {float(np.median(hfs)):.4f}"
        )
        return {"n": len(levels), "level": median, "db": db, "hf": float(np.median(hfs))}

    print(f"{args.audio.name}: {audio.size / rate / 60:.2f} min, speech ref {speech:.6f}")
    print(f"  quiet runs found: {len(all_runs)}")
    tone = describe("inserted tone", inserted)
    pause = describe("natural pause", natural)

    # Quietest frames while speech is present, i.e. the floor riding under the voice.
    voiced = level >= speech * 10 ** (-20 / 20)
    if voiced.any():
        under = float(np.percentile(level[voiced], 5))
        print(
            f"  {'under speech':16s}        level {under:.6f} "
            f"({20 * np.log10(under / speech):+6.1f} dB rel speech)"
        )

    if tone and pause:
        delta = tone["db"] - pause["db"]
        print(
            f"\ninserted tone sits {delta:+.1f} dB relative to the model's own pauses"
        )
        if delta > 1.5:
            print("  -> the synthesised gap is LOUDER than the voice's natural floor;")
            print("     that is the background opening up, and it is the assembler's")
            print("     doing rather than the model's")
        elif delta < -1.5:
            print("  -> gaps are quieter than natural pauses; the floor DROPPING out")
            print("     can also read as the background changing")
        else:
            print("  -> levels match; look at spectral character instead")
        if tone["hf"] > pause["hf"] * 1.4:
            print(
                f"  -> and it is brighter: hf {tone['hf']:.4f} vs {pause['hf']:.4f}, "
                "which reads as hiss rather than room"
            )

    if inserted:
        print("\nfirst inserted gaps (listen here):")
        for start, end, duration in inserted[:8]:
            print(f"  {start:7.2f}-{end:7.2f}s  ({duration * 1000:.0f} ms)")


if __name__ == "__main__":
    main()
