#!/usr/bin/env python3
"""Score candidate voice references on cleanliness AND expressiveness together.

Why this exists
---------------
Every previous reference selection in this project optimised one axis at a time,
and that is why neither candidate is satisfactory:

  uk-southern-female-03  clean, "voice and voice only", pitch span 8.84 st
  emns-neutral-l0-599    pitch span 19.24 st, but audibly "hiss and something else"

The listener rejected EMNS on recording quality and rejected the current voice's
flatness. Nobody had scored both properties jointly, so no candidate was ever
judged on the thing that actually matters: a clean recording that is also
expressive.

This measures four things per candidate and prints them side by side:

  NOISE FLOOR   level of the quietest frames against voiced level, in dB. This is
                what "hiss" is. A studio clip has a deep floor; a browser-recorded
                one does not.
  HISS          fraction of energy above 8 kHz measured in NON-voiced frames only.
                Separates genuine high-frequency detail in speech from broadband
                noise in the gaps, which a plain spectrum cannot do -- EMNS reads
                as brighter than the clean reference precisely because its noise
                lives up there.
  PITCH SPAN    10-90 percentile F0 spread in semitones.
  DYNAMIC RANGE p95-p10 of frame RMS in dB.

Prosody functions are imported from the existing `prosody.py` rather than
reimplemented, so the numbers are directly comparable to the recorded 8.84 and
19.24 figures instead of being a new scale nobody can compare against.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(
    0, str(Path(__file__).resolve().parents[1] / "kokoro-local")
)

from prosody import (  # noqa: E402
    dynamic_range_db,
    frame_rms,
    pitch_stats,
    speech_seconds,
)

TARGET_RATE = 24_000


def load(path: Path) -> np.ndarray:
    audio, rate = sf.read(str(path), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if rate != TARGET_RATE:
        from fractions import Fraction

        from scipy.signal import resample_poly

        ratio = Fraction(TARGET_RATE, int(rate)).limit_denominator(1000)
        audio = resample_poly(audio, ratio.numerator, ratio.denominator).astype(
            np.float32
        )
    return audio


def noise_metrics(audio: np.ndarray) -> dict:
    """Noise floor depth and high-frequency noise measured in the gaps."""
    rms = frame_rms(audio)
    if rms.size < 16:
        return {"floor_db": 0.0, "hiss": 0.0}

    voiced_level = float(np.percentile(rms, 90))
    floor_level = float(np.percentile(rms, 5))
    floor_db = (
        20 * float(np.log10(floor_level / voiced_level))
        if voiced_level > 0 and floor_level > 0
        else 0.0
    )

    # High-frequency content of the quiet frames only. In speech, HF energy in the
    # gaps is noise by definition; in voiced frames it could be fricatives.
    n = 1024
    window = np.hanning(n)
    freqs = np.fft.rfftfreq(n, 1 / TARGET_RATE)
    quiet_threshold = voiced_level * 10 ** (-30 / 20)
    ratios = []
    for start in range(0, max(0, audio.size - n), n // 2):
        segment = audio[start : start + n].astype(np.float64)
        level = np.sqrt((segment**2).mean() + 1e-12)
        if level > quiet_threshold or level < 1e-6:
            continue
        power = np.abs(np.fft.rfft(segment * window)) ** 2
        total = power.sum()
        if total <= 0:
            continue
        ratios.append(float(power[freqs > 8000].sum() / total))
    return {
        "floor_db": round(floor_db, 1),
        "hiss": round(float(np.mean(ratios)) if ratios else 0.0, 4),
        "quiet_frames": len(ratios),
    }


def score(path: Path) -> dict:
    audio = load(path)
    peak = float(np.abs(audio).max()) if audio.size else 0.0
    _, _, span = pitch_stats(audio)
    noise = noise_metrics(audio)
    return {
        "file": path.name,
        "seconds": round(audio.size / TARGET_RATE, 2),
        "speech_seconds": round(speech_seconds(audio), 2),
        "peak": round(peak, 3),
        "pitch_span_semitones": round(span, 2),
        "dynamic_range_db": round(dynamic_range_db(audio), 1),
        **noise,
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("audio", type=Path, nargs="+")
    p.add_argument("--report", type=Path, default=None)
    args = p.parse_args()

    rows = []
    for path in args.audio:
        if not path.is_file():
            print(f"  (missing) {path}")
            continue
        rows.append(score(path))

    print(
        f"{'file':34s} {'secs':>5s} {'speech':>6s} {'span':>6s} "
        f"{'dyn_dB':>7s} {'floor_dB':>8s} {'hiss':>7s}"
    )
    for row in rows:
        print(
            f"{row['file']:34s} {row['seconds']:5.1f} {row['speech_seconds']:6.1f} "
            f"{row['pitch_span_semitones']:6.2f} {row['dynamic_range_db']:7.1f} "
            f"{row['floor_db']:8.1f} {row['hiss']:7.4f}"
        )

    if rows:
        print(
            "\nwant: high span, high dyn_dB, DEEP (very negative) floor_dB, low hiss"
        )
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(rows, indent=2))
        print(f"wrote {args.report}")


if __name__ == "__main__":
    main()
