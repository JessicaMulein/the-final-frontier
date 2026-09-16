#!/usr/bin/env python3
"""In-place soften Chatterbox chapter joins (fwip repair without re-TTS)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_chapter_chatterbox import SAMPLE_RATE, soften_stitched_joins  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wavs", nargs="+", type=Path)
    parser.add_argument("--fade-ms", type=float, default=45.0)
    args = parser.parse_args()
    for path in args.wavs:
        audio, sr = sf.read(str(path), dtype="float32")
        if sr != SAMPLE_RATE:
            raise SystemExit(f"{path}: expected {SAMPLE_RATE} Hz, got {sr}")
        if audio.ndim > 1:
            audio = audio.mean(axis=1).astype("float32")
        fixed = soften_stitched_joins(audio, fade_ms=args.fade_ms)
        sf.write(str(path), fixed, SAMPLE_RATE)
        print(f"softened {path}")


if __name__ == "__main__":
    main()
