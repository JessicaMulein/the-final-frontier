#!/usr/bin/env python3
"""Detect a repeated acoustic span: the stutter class no transcript can see.

The defect this exists for
--------------------------
Chapter 2 rendered "six fifty-four" with the "four" audibly doubled. Whisper
normalised it to a single correct `.54` token, so chapter WER was 0.019, coverage
0.9964, seam residue 0.0, and the loop gate passed. Pace scoring actively preferred
that take over its rerolls because its overall rhythm was closest to the chapter
norm. Two rerolls were accepted by machine and rejected by ear.

Nothing that reads text can catch this. It has to be found in the waveform.

How
---
A stutter is a short span of audio that recurs almost immediately. So: frame the
audio, and for every lag in a plausible stutter range, ask whether a window here
looks like the window one lag later.

The hard part is not finding repeats, it is not drowning in them. Sustained vowels,
room tone and silence all self-match at nearly every lag, so naive self-similarity
flags everything. Three conditions separate a re-articulation from a steady sound:

  VOICED      both windows must carry speech energy, or silence matches silence.
  SIMILAR     the two windows must be close in spectral shape.
  CHANGING    the window must have internal spectral movement. A repeated
              onset-plus-vowel moves; a held vowel does not. This is the condition
              that does the real work, and without it the detector is useless.

Thresholds are fitted to the committed fixtures, and the test that matters is not
"does it flag the defect" but "does it flag the defect and leave its clean sibling
alone" -- the same words, the same voice, a different take.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf

FRAME_MS = 25.0
HOP_MS = 10.0
MIN_LAG_MS = 80.0
MAX_LAG_MS = 500.0
MIN_RUN_MS = 70.0
SIMILARITY = 0.93
MIN_NOVELTY = 0.12
VOICED_FLOOR_DB = -34.0


def load(path: Path) -> tuple[np.ndarray, int]:
    audio, rate = sf.read(str(path), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return audio, int(rate)


def features(audio: np.ndarray, rate: int) -> tuple[np.ndarray, np.ndarray, float]:
    """Log-compressed band energies per frame, L2-normalised, plus frame level."""
    frame = int(rate * FRAME_MS / 1000)
    hop = int(rate * HOP_MS / 1000)
    if audio.size < frame * 4:
        return np.zeros((0, 0)), np.zeros(0), hop / rate

    starts = np.arange(0, audio.size - frame + 1, hop)
    window = np.hanning(frame)
    frames = np.stack([audio[s : s + frame] for s in starts]).astype(np.float64)
    levels = np.sqrt((frames**2).mean(axis=1) + 1e-12)
    spectrum = np.abs(np.fft.rfft(frames * window[None, :], axis=1))

    # Coarse triangular-ish bands on a log frequency scale. Detail beyond this
    # does not help and makes steady sounds look artificially distinct.
    freqs = np.fft.rfftfreq(frame, 1 / rate)
    edges = np.geomspace(80, min(8000, rate / 2 - 1), 26)
    bands = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        mask = (freqs >= lo) & (freqs < hi)
        bands.append(spectrum[:, mask].sum(axis=1) if mask.any() else np.zeros(len(starts)))
    energy = np.log1p(np.stack(bands, axis=1) * 1000.0)

    norms = np.linalg.norm(energy, axis=1, keepdims=True)
    norms[norms <= 0] = 1.0
    return energy / norms, levels, hop / rate


def find_repeats(
    audio: np.ndarray,
    rate: int,
    *,
    similarity: float = SIMILARITY,
    min_novelty: float = MIN_NOVELTY,
    min_run_ms: float = MIN_RUN_MS,
) -> list[dict]:
    unit, levels, hop_seconds = features(audio, rate)
    if unit.shape[0] < 16:
        return []

    voiced = levels >= float(levels.max()) * 10 ** (VOICED_FLOOR_DB / 20)
    # Internal spectral movement: distance between consecutive frames.
    novelty = np.zeros(unit.shape[0])
    novelty[1:] = np.linalg.norm(np.diff(unit, axis=0), axis=1)

    min_lag = max(1, int((MIN_LAG_MS / 1000) / hop_seconds))
    max_lag = min(unit.shape[0] - 1, int((MAX_LAG_MS / 1000) / hop_seconds))
    min_run = max(2, int((min_run_ms / 1000) / hop_seconds))

    findings: list[dict] = []
    for lag in range(min_lag, max_lag + 1):
        left, right = unit[:-lag], unit[lag:]
        score = np.einsum("ij,ij->i", left, right)
        ok = (
            (score >= similarity)
            & voiced[:-lag]
            & voiced[lag:]
            # Require movement in BOTH copies, so a held vowel cannot qualify.
            & (novelty[:-lag] >= min_novelty)
            & (novelty[lag:] >= min_novelty)
        )
        if not ok.any():
            continue

        start = None
        for index, flag in enumerate(ok):
            if flag and start is None:
                start = index
            elif not flag and start is not None:
                if index - start >= min_run:
                    findings.append(
                        _finding(start, index, lag, score, hop_seconds)
                    )
                start = None
        if start is not None and len(ok) - start >= min_run:
            findings.append(_finding(start, len(ok), lag, score, hop_seconds))

    # One acoustic event produces hits at neighbouring lags; keep the strongest
    # per overlapping time region so a single stutter reports once.
    findings.sort(key=lambda f: (-f["score"], f["at"]))
    kept: list[dict] = []
    for candidate in findings:
        if any(
            abs(candidate["at"] - k["at"]) < 0.25 and abs(candidate["lag_ms"] - k["lag_ms"]) < 120
            for k in kept
        ):
            continue
        kept.append(candidate)
    kept.sort(key=lambda f: f["at"])
    return kept


def _finding(start: int, end: int, lag: int, score: np.ndarray, hop: float) -> dict:
    return {
        "at": round(start * hop, 3),
        "run_ms": round((end - start) * hop * 1000, 1),
        "lag_ms": round(lag * hop * 1000, 1),
        "score": round(float(score[start:end].mean()), 4),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("audio", type=Path, nargs="*")
    p.add_argument("--fixtures", action="store_true", help="validate against fixtures")
    p.add_argument("--similarity", type=float, default=SIMILARITY)
    p.add_argument("--min-novelty", type=float, default=MIN_NOVELTY)
    p.add_argument("--json", action="store_true")
    args = p.parse_args()

    if args.fixtures:
        _validate(args)
        return

    report = {}
    for path in args.audio:
        audio, rate = load(path)
        hits = find_repeats(
            audio, rate, similarity=args.similarity, min_novelty=args.min_novelty
        )
        report[str(path)] = hits
        if not args.json:
            print(f"{path.name}: {len(hits)} repeated span(s)")
            for hit in hits[:6]:
                print(
                    f"   {hit['at']:7.2f}s  lag {hit['lag_ms']:5.0f}ms  "
                    f"run {hit['run_ms']:5.0f}ms  score {hit['score']:.3f}"
                )
    if args.json:
        print(json.dumps(report, indent=2))


def _validate(args) -> None:
    """A gate is only useful if it separates a defect from its clean sibling."""
    index = json.loads(Path("fixtures/fixtures.json").read_text())
    print(
        f"similarity>={args.similarity} novelty>={args.min_novelty}\n"
        f"{'fixture':30s} {'defect':>8s} {'clean':>8s}  verdict"
    )
    passes = failures = 0
    for entry in index["fixtures"]:
        defect_path = Path("fixtures") / entry["file"]
        if not defect_path.is_file():
            continue
        audio, rate = load(defect_path)
        defect_hits = len(
            find_repeats(
                audio, rate, similarity=args.similarity, min_novelty=args.min_novelty
            )
        )
        sibling = entry.get("clean_sibling")
        clean_hits = None
        if sibling:
            clean_audio, clean_rate = load(Path("fixtures") / sibling["file"])
            clean_hits = len(
                find_repeats(
                    clean_audio,
                    clean_rate,
                    similarity=args.similarity,
                    min_novelty=args.min_novelty,
                )
            )

        # Only the stutter fixtures are this judge's job. For the others the
        # correct behaviour is silence on both sides.
        target = entry["id"] in {"intra_word_stutter", "warmup_residue_stutter"}
        if target:
            good = defect_hits > 0 and (clean_hits == 0 or clean_hits is None)
        else:
            good = defect_hits == 0
        passes += good
        failures += not good
        print(
            f"{entry['id']:30s} {defect_hits:8d} "
            f"{'-' if clean_hits is None else clean_hits:>8}  "
            f"{'ok' if good else 'MISS' if target else 'FALSE POSITIVE'}"
        )
    print(f"\n{passes} ok, {failures} not")


if __name__ == "__main__":
    main()
