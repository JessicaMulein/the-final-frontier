#!/usr/bin/env python3
"""Tight-crop a Chatterbox reference WAV and apply a micro fade-out.

Local audition tooling only — does not touch the Nova production path.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import soundfile as sf


def prepare_ref(
    source: Path,
    destination: Path,
    *,
    threshold: float = 0.01,
    pad_ms: float = 25.0,
    fade_ms: float = 15.0,
    fade_in_ms: float = 8.0,
) -> dict:
    audio, sample_rate = sf.read(str(source), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1).astype(np.float32)

    abs_audio = np.abs(audio)
    active = np.flatnonzero(abs_audio >= threshold)
    if active.size == 0:
        raise SystemExit(f"No samples above threshold {threshold} in {source}")

    pad = int(sample_rate * pad_ms / 1000)
    start = max(0, int(active[0]) - pad)
    end = min(audio.size, int(active[-1]) + 1 + pad)
    cropped = audio[start:end].copy()

    fade_in = min(int(sample_rate * fade_in_ms / 1000), cropped.size // 4)
    fade_out = min(int(sample_rate * fade_ms / 1000), cropped.size // 4)
    if fade_in > 0:
        cropped[:fade_in] *= np.linspace(0.0, 1.0, fade_in, dtype=np.float32)
    if fade_out > 0:
        cropped[-fade_out:] *= np.linspace(1.0, 0.0, fade_out, dtype=np.float32)

    destination.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(destination), cropped, sample_rate)

    original_s = audio.size / sample_rate
    cropped_s = cropped.size / sample_rate
    lead_ms = start * 1000 / sample_rate
    trail_ms = (audio.size - end) * 1000 / sample_rate
    return {
        "source": str(source),
        "destination": str(destination),
        "sample_rate": sample_rate,
        "original_seconds": round(original_s, 3),
        "cropped_seconds": round(cropped_s, 3),
        "removed_lead_ms": round(lead_ms, 1),
        "removed_trail_ms": round(trail_ms, 1),
        "fade_in_ms": fade_in_ms,
        "fade_out_ms": fade_ms,
        "threshold": threshold,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--threshold", type=float, default=0.01)
    parser.add_argument("--pad-ms", type=float, default=25.0)
    parser.add_argument("--fade-ms", type=float, default=15.0)
    parser.add_argument("--fade-in-ms", type=float, default=8.0)
    args = parser.parse_args()
    info = prepare_ref(
        args.source,
        args.output,
        threshold=args.threshold,
        pad_ms=args.pad_ms,
        fade_ms=args.fade_ms,
        fade_in_ms=args.fade_in_ms,
    )
    for key, value in info.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
