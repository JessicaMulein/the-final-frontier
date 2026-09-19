#!/usr/bin/env python3
"""Objective prosody metrics for voice references and renders (numpy only).

Local audition tooling only — does not touch the Nova production path.

Why these exist
---------------
`validate_stt.py` measures *fidelity*: did the model say the right words. It
cannot answer the question that motivates swapping a voice reference, because a
flat, evenly-paced read scores well on WER — and flatness is the defect being
chased away.

Two cheap, label-free measures that do move with perceived expressiveness:

  pitch span / stdev  — spread of the F0 distribution in semitones. An engaged
                        narrator moves through pitch; a monotone one does not.
  dynamic range       — p95-p10 of frame RMS in dB. Leaning in and backing off.

Caveat worth remembering: low-arousal emotions (sadness in particular) *reduce*
pitch variability. So a clip labelled "very sad" is typically flatter than a
neutral one. Measure, do not infer from emotion labels.

Deliberately dependency-free (numpy only) so corpus-wide profiling does not
have to import the TTS stack.
"""

from __future__ import annotations

import numpy as np

SAMPLE_RATE = 24_000


# --------------------------------------------------------------------------- #
# energy
# --------------------------------------------------------------------------- #


def frame_rms(audio: np.ndarray, *, frame_ms: float = 25.0) -> np.ndarray:
    win = max(1, int(SAMPLE_RATE * frame_ms / 1000))
    if audio.size < win:
        return np.zeros(0, dtype=np.float64)
    frames = np.pad(audio, (0, (-audio.size) % win)).reshape(-1, win)
    return np.sqrt((frames.astype(np.float64) ** 2).mean(axis=1) + 1e-12)


def speech_seconds(audio: np.ndarray, *, rms_floor_db: float = -42.0) -> float:
    """Seconds of non-quiet audio — the part that actually conditions a model."""
    if audio.size == 0:
        return 0.0
    win = max(1, int(SAMPLE_RATE * 0.010))
    frames = np.pad(audio, (0, (-audio.size) % win)).reshape(-1, win)
    rms = np.sqrt((frames.astype(np.float64) ** 2).mean(axis=1) + 1e-12)
    peak = float(rms.max())
    if peak <= 0.0:
        return 0.0
    return float((rms >= peak * (10.0 ** (rms_floor_db / 20.0))).sum()) * win / SAMPLE_RATE


def dynamic_range_db(audio: np.ndarray) -> float:
    """p95 - p10 of frame RMS in dB, over non-silent frames."""
    rms = frame_rms(audio)
    if rms.size == 0:
        return 0.0
    peak = rms.max()
    if peak <= 0:
        return 0.0
    voiced = rms[rms >= peak * 10 ** (-40.0 / 20.0)]
    if voiced.size < 8:
        return 0.0
    lo, hi = np.percentile(voiced, 10), np.percentile(voiced, 95)
    if lo <= 0:
        return 0.0
    return float(20 * np.log10(hi / lo))


# --------------------------------------------------------------------------- #
# pitch
# --------------------------------------------------------------------------- #


def estimate_f0_track(
    audio: np.ndarray,
    *,
    frame_ms: float = 40.0,
    hop_ms: float = 20.0,
    f_min: float = 60.0,
    f_max: float = 400.0,
    voiced_threshold: float = 0.35,
) -> np.ndarray:
    """Vectorised autocorrelation pitch track. Returns F0 (Hz) for voiced frames.

    Autocorrelation is computed for every frame at once via rFFT, which makes
    corpus-wide profiling practical. Deliberately simple: only the *spread* of
    the distribution is used downstream, so occasional octave errors wash out.
    """
    win = int(SAMPLE_RATE * frame_ms / 1000)
    hop = int(SAMPLE_RATE * hop_ms / 1000)
    if audio.size < win:
        return np.zeros(0, dtype=np.float64)
    lag_min = max(2, int(SAMPLE_RATE / f_max))
    lag_max = min(win - 1, int(SAMPLE_RATE / f_min))
    if lag_max <= lag_min:
        return np.zeros(0, dtype=np.float64)

    starts = np.arange(0, audio.size - win + 1, hop)
    if starts.size == 0:
        return np.zeros(0, dtype=np.float64)
    frames = np.stack([audio[s : s + win] for s in starts]).astype(np.float64)
    frames = frames * np.hanning(win)[None, :]

    # Drop near-silent frames before the transform.
    energy = np.sqrt((frames**2).mean(axis=1))
    frames = frames[energy >= 1e-4]
    if frames.shape[0] == 0:
        return np.zeros(0, dtype=np.float64)

    frames = frames - frames.mean(axis=1, keepdims=True)

    size = 1 << (2 * win - 1).bit_length()
    spectrum = np.fft.rfft(frames, n=size, axis=1)
    corr = np.fft.irfft(spectrum * np.conj(spectrum), n=size, axis=1)[:, :win]

    zero_lag = corr[:, :1]
    valid = zero_lag[:, 0] > 0
    corr = corr[valid] / zero_lag[valid]
    if corr.shape[0] == 0:
        return np.zeros(0, dtype=np.float64)

    segment = corr[:, lag_min : lag_max + 1]
    best = np.argmax(segment, axis=1)
    rows = np.arange(segment.shape[0])
    strength = segment[rows, best]
    voiced = strength >= voiced_threshold
    if not voiced.any():
        return np.zeros(0, dtype=np.float64)

    segment = segment[voiced]
    best = best[voiced]
    rows = np.arange(segment.shape[0])
    lags = best.astype(np.float64)

    # Parabolic refinement, skipping peaks that sit on a boundary.
    inner = (best > 0) & (best < segment.shape[1] - 1)
    if inner.any():
        ri = rows[inner]
        bi = best[inner]
        a = segment[ri, bi - 1]
        b = segment[ri, bi]
        c = segment[ri, bi + 1]
        denom = a - 2 * b + c
        safe = np.abs(denom) > 1e-12
        adjust = np.zeros_like(denom)
        adjust[safe] = 0.5 * (a[safe] - c[safe]) / denom[safe]
        lags[inner] = bi + adjust

    lags = lags + lag_min
    lags = lags[lags > 0]
    if lags.size == 0:
        return np.zeros(0, dtype=np.float64)
    return SAMPLE_RATE / lags


def pitch_stats(audio: np.ndarray) -> tuple[float, float, float]:
    """(median Hz, stdev in semitones, 10-90 percentile span in semitones)."""
    track = estimate_f0_track(audio)
    if track.size < 12:
        return 0.0, 0.0, 0.0
    median = float(np.median(track))
    if median <= 0:
        return 0.0, 0.0, 0.0
    semis = 12.0 * np.log2(track / median)
    # Clip gross octave errors so they do not dominate the spread.
    semis = semis[np.abs(semis) <= 14.0]
    if semis.size < 12:
        return median, 0.0, 0.0
    span = float(np.percentile(semis, 90) - np.percentile(semis, 10))
    return median, float(semis.std()), span
