"""Hold the narrator's brightness steady across a chapter, non-destructively.

The defect
----------
Measured over 17 rendered chapters, the voice dulls from start to finish without a
single exception: spectral centroid falls 84.8 Hz on average (about 16%), energy
above 2 kHz roughly halves, and spectral tilt drops 3.02 dB/octave. Gradual over six
minutes, so a chapter played alone sounds fine. But cut a dull ending 1.2 s from a
fresh start and the listener hears the voice "get lighter, clearer" at every chapter
boundary -- which is what four blind boundary clips reported, in all four cases,
including two boundaries whose F0 moves the other way.

Nothing in the pipeline addresses it. `flatten_slope` removes a level slope inside a
segment and `match_levels` matches level between segments. Both are level-only and
blind to spectrum.

The correction
--------------
A slowly varying tilt filter, fitted the same way `flatten_slope` fits level: measure
tilt per window across the whole chapter, fit one straight line, and apply its
inverse as a smooth ramp. Using the fitted line rather than per-frame measurements
keeps the correction predictable and stops it chasing normal speech variation.

  --target head   the chapter keeps the brightness it starts with; only the later
                  part is lifted. Nothing is darkened.
  --target mean   pivots about the chapter's mean: the opening is darkened slightly
                  and the ending lifted slightly, so average character is preserved
                  and the maximum correction at either end is halved.

Safety
------
Never writes in place. Duration and sample rate are preserved exactly, so existing
manifests and timestamps stay valid.

Three bounds, because the risk here is real: at a chapter's end there is very little
energy above 2 kHz, so an aggressive lift raises breath and noise rather than
restoring clarity.

  --max-db-per-oct  caps the tilt change itself
  --cap-db          caps the gain at any single frequency
  --only-boost      never attenuate; high frequencies are lifted, low left alone

Quiet frames are left untouched. Repaired inter-paragraph gaps were deliberately
rewritten to carry no energy above 4 kHz, and a tilt lift applied to them would
start undoing that.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf

NFFT = 2048
HOP = NFFT // 4
VOICED_DB = -36.0
FIT_LOW_HZ = 200.0
FIT_HIGH_HZ = 8000.0


def load(path: Path) -> tuple[np.ndarray, int]:
    audio, rate = sf.read(str(path), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return audio, int(rate)


def frame(audio: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    pad = NFFT
    padded = np.concatenate(
        [np.zeros(pad, dtype=np.float32), audio, np.zeros(pad * 2, dtype=np.float32)]
    )
    starts = np.arange(0, padded.size - NFFT + 1, HOP)
    frames = np.stack([padded[s : s + NFFT] for s in starts]).astype(np.float64)
    return frames, starts


def tilt_of(power: np.ndarray, octaves: np.ndarray, band: np.ndarray) -> np.ndarray:
    """dB/octave regression of the log spectrum over the voice band, per frame."""
    db = 10 * np.log10(power[:, band] + 1e-20)
    centred = octaves - octaves.mean()
    denom = float((centred**2).sum())
    if denom <= 0:
        return np.zeros(db.shape[0])
    return (db - db.mean(axis=1, keepdims=True)) @ centred / denom


def measure_trend(
    audio: np.ndarray, rate: int, window: float
) -> tuple[float, float, list[dict]]:
    """Fit tilt against time over the chapter. Returns (intercept, slope/min, rows)."""
    freqs = np.fft.rfftfreq(NFFT, 1 / rate)
    band = (freqs >= FIT_LOW_HZ) & (freqs <= FIT_HIGH_HZ)
    octaves = np.log2(freqs[band] / FIT_LOW_HZ)
    span = int(window * rate)
    times, tilts, rows = [], [], []
    for start in range(0, max(1, audio.size - span // 2), span):
        piece = audio[start : start + span]
        if piece.size < span // 2:
            break
        frames, _ = frame(piece)
        rms = np.sqrt((frames**2).mean(axis=1) + 1e-20)
        peak = float(rms.max())
        if peak <= 0:
            continue
        keep = rms >= peak * 10 ** (VOICED_DB / 20)
        if int(keep.sum()) < 8:
            continue
        power = np.abs(np.fft.rfft(frames[keep] * np.hanning(NFFT)[None, :], axis=1)) ** 2
        value = float(np.median(tilt_of(power, octaves, band)))
        centre = (start + piece.size / 2) / rate / 60.0
        times.append(centre)
        tilts.append(value)
        rows.append({"minutes": round(centre, 3), "tilt_db_per_oct": round(value, 4)})
    if len(tilts) < 4:
        return 0.0, 0.0, rows
    slope, intercept = np.polyfit(times, tilts, 1)
    return float(intercept), float(slope), rows


def gain_curve(
    delta_per_oct: np.ndarray,
    freqs: np.ndarray,
    pivot: float,
    cap_db: float,
    only_boost: bool,
) -> np.ndarray:
    """Per-frame, per-bin gain in dB for a tilt change of delta_per_oct."""
    with np.errstate(divide="ignore"):
        octaves = np.log2(np.maximum(freqs, 1.0) / pivot)
    # Hold the curve constant outside the band that carries voice information, so a
    # tilt change cannot produce a large gain at 20 Hz or at Nyquist.
    octaves = np.clip(octaves, np.log2(250.0 / pivot), np.log2(8000.0 / pivot))
    db = delta_per_oct[:, None] * octaves[None, :]
    if only_boost:
        db = np.maximum(db, 0.0)
    return np.clip(db, -cap_db, cap_db)


def apply(
    audio: np.ndarray,
    rate: int,
    intercept: float,
    slope: float,
    target: str,
    max_per_oct: float,
    cap_db: float,
    pivot: float,
    only_boost: bool,
    target_tilt: float | None = None,
) -> tuple[np.ndarray, dict]:
    minutes_total = audio.size / rate / 60.0
    frames, starts = frame(audio)
    window = np.hanning(NFFT)
    rms = np.sqrt((frames**2).mean(axis=1) + 1e-20)
    peak = float(rms.max())
    voiced = rms >= peak * 10 ** (VOICED_DB / 20) if peak > 0 else np.zeros(rms.shape, bool)

    # Frame centre in minutes, measured on the original timeline.
    centres = (starts + NFFT / 2 - NFFT) / rate / 60.0
    fitted = intercept + slope * centres
    if target_tilt is not None:
        reference = float(target_tilt)
    elif target == "head":
        reference = intercept
    else:
        reference = intercept + slope * minutes_total / 2.0
    delta = np.clip(reference - fitted, -max_per_oct, max_per_oct)
    # Only correct where there is voice. Quiet frames keep unity gain so repaired
    # gaps and true silence are not touched.
    delta = np.where(voiced, delta, 0.0)

    freqs = np.fft.rfftfreq(NFFT, 1 / rate)
    gain = 10 ** (gain_curve(delta, freqs, pivot, cap_db, only_boost) / 20.0)

    spectra = np.fft.rfft(frames * window[None, :], axis=1) * gain
    rebuilt = np.fft.irfft(spectra, n=NFFT, axis=1) * window[None, :]

    out = np.zeros(starts[-1] + NFFT, dtype=np.float64)
    weight = np.zeros_like(out)
    for index, start in enumerate(starts):
        out[start : start + NFFT] += rebuilt[index]
        weight[start : start + NFFT] += window**2
    valid = weight > 1e-8
    out[valid] /= weight[valid]
    out = out[NFFT : NFFT + audio.size]

    loudest = float(np.abs(out).max())
    trimmed = 0.0
    if loudest > 0.99:
        trimmed = loudest
        out *= 0.99 / loudest
    stats = {
        "target": "absolute" if target_tilt is not None else target,
        "reference_tilt_db_per_oct": round(reference, 4),
        "clipped_by_max_per_oct": bool(
            np.any(np.abs(reference - fitted)[voiced] > max_per_oct + 1e-9)
        )
        if voiced.any()
        else False,
        "delta_at_head_db_per_oct": round(float(delta[voiced][0]) if voiced.any() else 0.0, 4),
        "delta_at_tail_db_per_oct": round(float(delta[voiced][-1]) if voiced.any() else 0.0, 4),
        "max_abs_delta_db_per_oct": round(float(np.abs(delta).max()), 4),
        "voiced_frames": int(voiced.sum()),
        "total_frames": int(rms.size),
        "peak_before_limit": round(trimmed, 4) if trimmed else None,
    }
    return out.astype(np.float32), stats


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("audio", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--target", choices=("head", "mean"), default="head")
    p.add_argument(
        "--target-tilt",
        type=float,
        default=None,
        metavar="DB_PER_OCT",
        help="absolute book-wide tilt to hold, e.g. -6.6, overriding --target. "
        "Per-chapter targets flatten each chapter to its own opening, which leaves "
        "chapter openings unequal (measured head centroids run 482-568 Hz) and can "
        "turn a step up at a boundary into a step down. An absolute target puts every "
        "chapter at the same brightness throughout, so no chapter's ending is brighter "
        "or duller than another chapter's opening.",
    )
    p.add_argument("--max-db-per-oct", type=float, default=3.0)
    p.add_argument("--cap-db", type=float, default=6.0)
    p.add_argument("--pivot-hz", type=float, default=500.0)
    p.add_argument("--only-boost", action="store_true")
    p.add_argument("--window", type=float, default=15.0)
    p.add_argument("--report", type=Path, default=None)
    args = p.parse_args()

    audio, rate = load(args.audio)
    print(f"{args.audio.name}: {audio.size / rate / 60:.2f} min")

    intercept, slope, rows = measure_trend(audio, rate, args.window)
    if not rows:
        raise SystemExit("not enough voiced material to fit a tilt trend")
    minutes = audio.size / rate / 60.0
    print(
        f"  tilt fit: {intercept:+.2f} dB/oct at the start, "
        f"{slope:+.3f} dB/oct per minute -> {intercept + slope * minutes:+.2f} at the end"
    )

    corrected, stats = apply(
        audio,
        rate,
        intercept,
        slope,
        args.target,
        args.max_db_per_oct,
        args.cap_db,
        args.pivot_hz,
        args.only_boost,
        args.target_tilt,
    )
    if stats["clipped_by_max_per_oct"]:
        print(
            f"  WARNING: correction clipped by --max-db-per-oct "
            f"{args.max_db_per_oct:.1f}; target {stats['reference_tilt_db_per_oct']:+.2f} "
            f"not fully reached"
        )
    print(
        f"  correction: {stats['delta_at_head_db_per_oct']:+.2f} dB/oct at the head, "
        f"{stats['delta_at_tail_db_per_oct']:+.2f} at the tail "
        f"(cap {args.max_db_per_oct:.1f}/oct, {args.cap_db:.1f} dB, "
        f"{'boost only' if args.only_boost else 'symmetric'})"
    )

    after_intercept, after_slope, _ = measure_trend(corrected, rate, args.window)
    print(
        f"  after: {after_intercept:+.2f} dB/oct at the start, "
        f"{after_slope:+.3f} per minute -> "
        f"{after_intercept + after_slope * minutes:+.2f} at the end"
    )

    if corrected.size != audio.size:
        raise SystemExit(f"length changed: {audio.size} -> {corrected.size}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(args.output), corrected, rate, subtype="PCM_16")
    print(f"  wrote {args.output}")

    if args.report:
        args.report.write_text(
            json.dumps(
                {
                    "input": str(args.audio),
                    "output": str(args.output),
                    "settings": {
                        "target": args.target,
                        "target_tilt": args.target_tilt,
                        "max_db_per_oct": args.max_db_per_oct,
                        "cap_db": args.cap_db,
                        "pivot_hz": args.pivot_hz,
                        "only_boost": args.only_boost,
                        "window_seconds": args.window,
                    },
                    "before": {
                        "tilt_intercept": round(intercept, 4),
                        "tilt_slope_per_min": round(slope, 4),
                        "windows": rows,
                    },
                    "after": {
                        "tilt_intercept": round(after_intercept, 4),
                        "tilt_slope_per_min": round(after_slope, 4),
                    },
                    "applied": stats,
                },
                indent=2,
            )
        )
        print(f"  wrote {args.report}")


if __name__ == "__main__":
    main()
