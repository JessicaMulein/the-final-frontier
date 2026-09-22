#!/usr/bin/env python3
"""Write a V6 comfort-tone pad WAV, shaped from a donor chapter's own room tone.

Why this exists: the M4B concatenates 128 chapter WAVs end to end. With nothing
between them, the last sentence of a chapter runs straight into the next chapter's
spoken announcement — a run-on with no pause. The obvious fix, a digital-silence
pad, is wrong for the same reason the V6 gap synthesizer exists: pure zeros drop
the background out entirely, so the room tone the listener has been hearing
vanishes for the length of the pad and returns with the next chapter. That is the
"background opens up" defect, moved to the chapter seam.

So the inter-chapter pad is the same V6 stationary room tone the renderer uses
for intra-chapter gaps: `comfort_gap` shaped from real chapter audio, at 44.1 kHz.
The donor is the preceding chapter, so the pad matches the tone the listener was
just in. This imports `comfort_gap` from the renderer rather than reimplementing
it, so the seam pad and the in-chapter gaps can never drift apart.

Usage:
  make_comfort_pad.py --donor CHAPTER.wav --seconds 1.2 --output pad.wav [--seed N]
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import soundfile as sf

from render_chapter_fish import GAP_ALGORITHM, comfort_gap


def _mono(path: Path) -> tuple[np.ndarray, int]:
    audio, rate = sf.read(str(path), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return audio, int(rate)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--donor", type=Path, required=True,
                   help="chapter WAV whose room tone shapes the pad")
    p.add_argument("--seconds", type=float, required=True,
                   help="pad length in seconds")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--seed", type=int, default=9021,
                   help="RNG seed for the V6 spectral fill; fixed for reproducibility")
    args = p.parse_args()

    donor, rate = _mono(args.donor)
    samples = int(round(args.seconds * rate))
    if samples <= 0:
        raise SystemExit("pad length must be positive")

    # comfort_gap harvests confirmed dark-pause donors from the audio it is given,
    # builds the median power spectrum, and synthesises stationary tone at the
    # natural floor level. Feeding it the whole donor chapter gives it ample dark
    # pauses to shape from.
    pad = comfort_gap([donor], samples, rate, seed=args.seed)
    if pad.size != samples:
        raise SystemExit(
            f"pad length mismatch: got {pad.size}, wanted {samples}"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(args.output), pad, rate, subtype="PCM_16")
    print(f"wrote {args.output} ({args.seconds:.3f}s, {GAP_ALGORITHM}, seed {args.seed})")


if __name__ == "__main__":
    main()
