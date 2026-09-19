"""Bring every chapter's average spectrum toward one book-wide reference.

Why this exists
---------------
Chapter-to-chapter brightness, not pitch, is what the listener hears at a chapter
boundary. Measured across three announcements generated with an identical anchor,
seed, reference and instruct -- differing only in their words -- spectral centroid
spanned 412 to 593 Hz. Generation-side control cannot fix that: anchoring stabilised
F0 (confirmed blind) but brightness is driven by the text being read.

What failed before, and why this differs
----------------------------------------
Two earlier attempts corrected spectral *tilt* with a *time-varying* ramp. Both made
brightness less uniform across chapters, once pushing a chapter's centroid to 901 Hz
against a natural range of 482-568, because holding a regression slope constant does
not hold centroid constant, and because a moving gain can pump.

This is the operation audiobook mastering actually performs:

  * one curve per chapter, constant for the whole chapter -- a static filter cannot
    pump, breathe, or drift;
  * the target is the book's own median spectrum, not a synthetic slope, so no
    chapter is pushed outside the range the narrator actually produced;
  * the curve is smoothed across a third of an octave, so it corrects broad
    character and cannot carve narrow resonances or chase formants;
  * it is bounded, and the bound is reported;
  * loudness is preserved exactly, so this changes colour and nothing else.

Within-chapter dynamics are deliberately untouched. The head-to-tail decay correlates
with the prose turning reflective at chapter ends, and flattening it removes
expression. Only the differences *between* chapters are corrected.

Never writes in place, and preserves duration exactly, so manifests, segment offsets,
and any read-along timings stay valid.
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


def load(path: Path) -> tuple[np.ndarray, int]:
    audio, rate = sf.read(str(path), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return audio, int(rate)


def active_rms(audio: np.ndarray, rate: int) -> float:
    frame = max(1, int(rate * 0.020))
    usable = (audio.size // frame) * frame
    if usable == 0:
        return 0.0
    frames = audio[:usable].reshape(-1, frame).astype(np.float64)
    rms = np.sqrt((frames**2).mean(axis=1) + 1e-20)
    peak = float(rms.max())
    if peak <= 0:
        return 0.0
    voiced = rms[rms >= peak * 10 ** (VOICED_DB / 20)]
    return float(np.sqrt(np.mean(voiced**2))) if voiced.size else 0.0


def frames_of(audio: np.ndarray) -> np.ndarray:
    if audio.size < NFFT:
        return np.zeros((0, NFFT))
    starts = np.arange(0, audio.size - NFFT + 1, HOP)
    return np.stack([audio[s : s + NFFT] for s in starts]).astype(np.float64)


def long_term_spectrum(audio: np.ndarray) -> np.ndarray:
    """Mean power spectrum over speech-active frames, normalised to unit power.

    Normalising removes loudness from the comparison, so a quiet chapter is not
    "corrected" by being brightened.
    """
    frames = frames_of(audio)
    if frames.shape[0] == 0:
        return np.zeros(NFFT // 2 + 1)
    rms = np.sqrt((frames**2).mean(axis=1) + 1e-20)
    peak = float(rms.max())
    if peak <= 0:
        return np.zeros(NFFT // 2 + 1)
    voiced = frames[rms >= peak * 10 ** (VOICED_DB / 20)]
    if voiced.shape[0] == 0:
        return np.zeros(NFFT // 2 + 1)
    power = (np.abs(np.fft.rfft(voiced * np.hanning(NFFT)[None, :], axis=1)) ** 2).mean(
        axis=0
    )
    total = float(power.sum())
    return power / total if total > 0 else power


def smooth_fractional_octave(curve_db: np.ndarray, freqs: np.ndarray, fraction: float):
    """Average the curve inside a fractional-octave window around each bin.

    Broad character only. A narrow correction would chase individual formants and
    resonances, which is how an EQ starts sounding like processing.
    """
    ratio = 2.0 ** (fraction / 2.0)
    out = np.empty_like(curve_db)
    for index, frequency in enumerate(freqs):
        if frequency <= 0:
            out[index] = curve_db[index]
            continue
        low, high = frequency / ratio, frequency * ratio
        window = (freqs >= low) & (freqs <= high)
        out[index] = curve_db[window].mean() if window.any() else curve_db[index]
    return out


def correction_curve(
    chapter: np.ndarray,
    reference: np.ndarray,
    freqs: np.ndarray,
    *,
    max_db: float,
    low_hz: float,
    high_hz: float,
    fraction: float,
) -> np.ndarray:
    """Static gain in dB per bin: reference minus chapter, smoothed and bounded."""
    floor = 1e-12
    delta = 10 * np.log10(np.maximum(reference, floor)) - 10 * np.log10(
        np.maximum(chapter, floor)
    )
    # Correct only where the voice carries information. Outside the band the curve is
    # held at the band edge rather than extrapolated into rumble or hiss.
    band = (freqs >= low_hz) & (freqs <= high_hz)
    if not band.any():
        return np.zeros_like(delta)
    delta = np.where(band, delta, 0.0)
    delta = smooth_fractional_octave(delta, freqs, fraction)
    low_edge = float(delta[band][0])
    high_edge = float(delta[band][-1])
    delta = np.where(freqs < low_hz, low_edge, delta)
    delta = np.where(freqs > high_hz, high_edge, delta)
    # Loudness-neutral: remove the reference-weighted average so the curve tilts
    # colour without adding level, then bound what remains.
    weight = np.maximum(reference, floor)
    delta = delta - float(np.average(delta, weights=weight))
    return np.clip(delta, -max_db, max_db)


def apply_static_curve(audio: np.ndarray, gain_db: np.ndarray) -> np.ndarray:
    """Zero-phase static filter via STFT, exact length preserved."""
    pad = NFFT
    padded = np.concatenate(
        [np.zeros(pad, dtype=np.float32), audio, np.zeros(pad * 2, dtype=np.float32)]
    )
    starts = np.arange(0, padded.size - NFFT + 1, HOP)
    window = np.hanning(NFFT)
    gain = 10 ** (gain_db / 20.0)
    out = np.zeros(starts[-1] + NFFT, dtype=np.float64)
    weight = np.zeros_like(out)
    for start in starts:
        block = padded[start : start + NFFT] * window
        rebuilt = np.fft.irfft(np.fft.rfft(block) * gain, n=NFFT) * window
        out[start : start + NFFT] += rebuilt
        weight[start : start + NFFT] += window**2
    valid = weight > 1e-8
    out[valid] /= weight[valid]
    return out[pad : pad + audio.size].astype(np.float32)


def centroid(audio: np.ndarray, rate: int) -> float:
    frames = frames_of(audio)
    if frames.shape[0] == 0:
        return 0.0
    rms = np.sqrt((frames**2).mean(axis=1) + 1e-20)
    peak = float(rms.max())
    if peak <= 0:
        return 0.0
    voiced = frames[rms >= peak * 10 ** (VOICED_DB / 20)]
    power = np.abs(np.fft.rfft(voiced * np.hanning(NFFT)[None, :], axis=1)) ** 2
    freqs = np.fft.rfftfreq(NFFT, 1 / rate)
    total = power.sum(axis=1) + 1e-20
    return float(np.median((power * freqs[None, :]).sum(axis=1) / total))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("inputs", type=Path, nargs="+", help="chapter WAVs to match")
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--max-db", type=float, default=3.0)
    p.add_argument("--low-hz", type=float, default=100.0)
    p.add_argument("--high-hz", type=float, default=10000.0)
    p.add_argument(
        "--octave-fraction",
        type=float,
        default=1 / 3,
        help="smoothing width; larger corrects broader character only",
    )
    p.add_argument(
        "--reference",
        type=Path,
        default=None,
        help="reuse a reference spectrum written by an earlier run, so a later batch "
        "is matched to the same target as the first",
    )
    p.add_argument("--report", type=Path, default=None)
    args = p.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    loaded = []
    for path in args.inputs:
        audio, rate = load(path)
        loaded.append((path, audio, rate))
    rates = {rate for _, _, rate in loaded}
    if len(rates) != 1:
        raise SystemExit(f"inputs must share one sample rate; found {sorted(rates)}")
    rate = rates.pop()
    freqs = np.fft.rfftfreq(NFFT, 1 / rate)

    spectra = {path.name: long_term_spectrum(audio) for path, audio, _ in loaded}

    if args.reference is not None and args.reference.is_file():
        stored = json.loads(args.reference.read_text())
        reference = np.array(stored["reference_power"], dtype=np.float64)
        if reference.size != freqs.size:
            raise SystemExit("stored reference does not match this FFT size")
        print(f"reference: reused from {args.reference}")
    else:
        # Median across chapters, so one unusually bright or dark chapter cannot
        # drag the target. This is the book's own centre, not an invented curve.
        reference = np.median(np.stack(list(spectra.values())), axis=0)
        reference = reference / max(float(reference.sum()), 1e-20)
        print(f"reference: median of {len(spectra)} chapters")

    print(f"\nbound +/-{args.max_db:.1f} dB, {args.octave_fraction:.3f}-octave smoothing, "
          f"{args.low_hz:.0f}-{args.high_hz:.0f} Hz\n")
    print("chapter                                 centroid      applied dB    level")
    records = []
    for path, audio, _ in loaded:
        gain_db = correction_curve(
            spectra[path.name],
            reference,
            freqs,
            max_db=args.max_db,
            low_hz=args.low_hz,
            high_hz=args.high_hz,
            fraction=args.octave_fraction,
        )
        before_level = active_rms(audio, rate)
        corrected = apply_static_curve(audio, gain_db)
        after_level = active_rms(corrected, rate)
        if after_level > 0 and before_level > 0:
            corrected = (corrected * (before_level / after_level)).astype(np.float32)
        peak = float(np.abs(corrected).max())
        if peak > 0.99:
            corrected = (corrected * (0.99 / peak)).astype(np.float32)

        if corrected.size != audio.size:
            raise SystemExit(f"{path.name}: length changed")

        destination = args.out / path.name
        sf.write(str(destination), corrected, rate, subtype="PCM_16")

        before_c = centroid(audio, rate)
        after_c = centroid(corrected, rate)
        level_delta = 20 * np.log10(
            (active_rms(corrected, rate) + 1e-20) / (before_level + 1e-20)
        )
        records.append(
            {
                "file": path.name,
                "centroid_before_hz": round(before_c, 1),
                "centroid_after_hz": round(after_c, 1),
                "max_abs_gain_db": round(float(np.abs(gain_db).max()), 2),
                "level_change_db": round(float(level_delta), 3),
            }
        )
        print(
            f"{path.name:38s} {before_c:6.1f} -> {after_c:6.1f}   "
            f"{float(np.abs(gain_db).max()):+6.2f} max   {float(level_delta):+.2f} dB"
        )

    before = [r["centroid_before_hz"] for r in records]
    after = [r["centroid_after_hz"] for r in records]
    print(
        f"\nbetween-chapter centroid spread: {max(before) - min(before):.1f} Hz -> "
        f"{max(after) - min(after):.1f} Hz"
    )

    if args.report:
        args.report.write_text(
            json.dumps(
                {
                    "settings": {
                        "max_db": args.max_db,
                        "low_hz": args.low_hz,
                        "high_hz": args.high_hz,
                        "octave_fraction": args.octave_fraction,
                        "nfft": NFFT,
                    },
                    "reference_power": [float(v) for v in reference],
                    "chapters": records,
                },
                indent=2,
            )
        )
        print(f"wrote {args.report}")


if __name__ == "__main__":
    main()
