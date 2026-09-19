#!/usr/bin/env python3
"""Measure delivery pace from the waveform alone, with no ASR.

Two quantities, kept separate because they have different remedies:

  ARTICULATION RATE -- amplitude-envelope peaks per second of *voiced* time, a
    proxy for syllable rate that ignores pauses entirely. If this falls, the voice
    is genuinely speaking more slowly, and only a different take or time-scaling
    changes it.
  PAUSE LOAD -- what fraction of a unit is silence, and how long the individual
    gaps run. If this rises, the speech itself is intact and only the gaps are
    stretched, which can be shortened without touching voiced audio.

Both are cheap (numpy, CPU) so they can score render candidates inside the
render loop without adding a Whisper pass, and they are robust to the thing that
made ASR word timings misleading here: Whisper attributes trailing silence to the
preceding word, so a word "lasting" 1.2 s may be 0.3 s of speech and 0.9 s of
pause. These metrics never confuse the two.

Measured on chapter 3 (15 units, listener-approved apart from its final unit),
articulation ran 7.20-8.52 peaks per voiced second with a median of 8.06, and
pause fraction 27-39% with a median of 33%. The unit the listener flagged was the
minimum on articulation and the maximum on pause load, which is what makes these
usable as a selection signal.
"""

from __future__ import annotations

import numpy as np

SAMPLE_RATE = 24_000
FRAME_MS = 10.0
# Voiced threshold, relative to the unit's own 90th-percentile frame level, so it
# does not depend on absolute gain.
VOICED_FLOOR_DB = -26.0
MIN_GAP_SECONDS = 0.150
# Gap time beyond this is what a pause trim could reclaim.
NATURAL_GAP_SECONDS = 0.300
PEAK_MIN_SPACING_MS = 80.0


def _envelope(audio: np.ndarray) -> tuple[np.ndarray, float]:
    frame = max(1, int(SAMPLE_RATE * FRAME_MS / 1000))
    count = audio.size // frame
    if count == 0:
        return np.zeros(0), FRAME_MS / 1000.0
    frames = audio[: count * frame].reshape(count, frame).astype(np.float64)
    return np.sqrt((frames**2).mean(axis=1) + 1e-12), FRAME_MS / 1000.0


def measure(audio: np.ndarray) -> dict | None:
    """Pace statistics for one generation unit, or None if it is too short."""
    env, hop = _envelope(audio)
    if env.size < 20:
        return None
    reference = float(np.percentile(env, 90))
    if reference <= 0:
        return None
    threshold = reference * 10 ** (VOICED_FLOOR_DB / 20)
    voiced = env >= threshold

    gaps: list[float] = []
    run = 0
    for flag in voiced:
        if flag:
            if run:
                gaps.append(run * hop)
            run = 0
        else:
            run += 1
    if run:
        gaps.append(run * hop)

    smooth = np.convolve(env, np.ones(3) / 3, mode="same")
    spacing = max(1, int((PEAK_MIN_SPACING_MS / 1000) / hop))
    peaks = 0
    last = -spacing
    for i in range(1, smooth.size - 1):
        if (
            voiced[i]
            and smooth[i] > smooth[i - 1]
            and smooth[i] >= smooth[i + 1]
            and smooth[i] > threshold * 1.6
            and i - last >= spacing
        ):
            peaks += 1
            last = i

    voiced_seconds = float(voiced.sum()) * hop
    total = env.size * hop
    if voiced_seconds <= 0:
        return None
    long_gaps = [g for g in gaps if g >= MIN_GAP_SECONDS]
    return {
        "seconds": round(total, 3),
        "voiced_seconds": round(voiced_seconds, 3),
        "voiced_fraction": round(voiced_seconds / total, 4),
        "pause_fraction": round(1 - voiced_seconds / total, 4),
        "articulation": round(peaks / voiced_seconds, 4),
        "long_gaps": len(long_gaps),
        "longest_gap": round(max(long_gaps), 3) if long_gaps else 0.0,
        "reclaimable_seconds": round(
            sum(g - NATURAL_GAP_SECONDS for g in gaps if g > NATURAL_GAP_SECONDS), 3
        ),
    }


def norm_of(measures: list[dict]) -> dict:
    """Median pace of a set of units, used as the target a patch should match."""
    usable = [m for m in measures if m]
    if not usable:
        return {}
    return {
        "articulation": float(np.median([m["articulation"] for m in usable])),
        "pause_fraction": float(np.median([m["pause_fraction"] for m in usable])),
        "units": len(usable),
    }


def deviation(measure_one: dict, norm: dict) -> float:
    """How far a unit sits from a chapter norm, as a single comparable score.

    Articulation is weighted above pause load: a unit that articulates slowly
    sounds like the narrator flagging, whereas extra pause time reads as
    punctuation and is partly driven by the sentence lengths in the text.
    """
    if not measure_one or not norm:
        return float("inf")
    articulation = abs(measure_one["articulation"] - norm["articulation"]) / max(
        1e-6, norm["articulation"]
    )
    pause = abs(measure_one["pause_fraction"] - norm["pause_fraction"]) / max(
        1e-6, norm["pause_fraction"]
    )
    return round(articulation + 0.5 * pause, 5)
