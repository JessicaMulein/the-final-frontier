#!/usr/bin/env python3
"""Reference-audio loading for the narration engines.

Exists because two engines disagree about what a "reference" is and one of them
documents the wrong thing. Fish S2 Pro's README shows `ref_audio="sample.wav"`,
but `_prepare_reference_prompt` immediately calls `audio.ndim`, so a path raises
`AttributeError: 'str' object has no attribute 'ndim'`. It wants an `mx.array`.

Sample rate matters here too. Fish runs at 44.1 kHz while our reference clips and
the QVoice pipeline are 24 kHz, so a reference has to be resampled before it is
handed over. Resampling a voice reference with linear interpolation would alias,
and this clip is the sole source of the narrator's identity, so it uses
`resample_poly` (scipy is already a dependency of mlx-audio) rather than
`numpy.interp`.
"""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path

import mlx.core as mx
import numpy as np
import soundfile as sf


def load_reference(path: Path | str, target_rate: int) -> mx.array:
    """Mono float32 reference at `target_rate`, as an `mx.array`."""
    audio, rate = sf.read(str(path), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    if rate != target_rate:
        from scipy.signal import resample_poly

        ratio = Fraction(int(target_rate), int(rate)).limit_denominator(1000)
        audio = resample_poly(audio, ratio.numerator, ratio.denominator).astype(
            np.float32
        )

    peak = float(np.abs(audio).max()) if audio.size else 0.0
    if peak > 1.0:
        audio = audio / peak
    return mx.array(audio)


def reference_seconds(path: Path | str) -> float:
    info = sf.info(str(path))
    return float(info.frames) / float(info.samplerate)
