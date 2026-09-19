#!/usr/bin/env python3
"""Replace synthesised room tone with the model's own pause audio, non-destructively.

The defect
----------
`comfort_gap` builds inter-paragraph tone by averaging the spectrum of frames between
the 5th and 18th percentile of level. At those levels a Fish render is essentially
silent below 4 kHz, so the averaged spectrum is dominated by sparse high-frequency
content, and renormalising it to floor loudness manufactures hiss. Measured on
chapter 5: the inserted tone matches the natural floor in level (-36.8 dB against
-36.7 dB) but carries 29% of its energy above 4 kHz where the model's own pauses
carry none. Inserted twelve to thirty times per chapter, that is a background that
opens and closes.

The repair
----------
Stop synthesising. The model already produces a correct floor during its own pauses,
so use that: harvest real low-level audio from the same render and crossfade it in to
fill each gap. Same file, same voice, same room, correct spectrum.

Safety
------
Never writes in place. Reads one file, writes another, and reports what it changed so
the result can be compared before anything is accepted. Total duration is preserved
exactly, so existing manifests and timestamps stay valid.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf

FRAME_MS = 20.0
HF_SPLIT_HZ = 4000.0
# A synthesised gap is quiet AND bright. Natural pauses are quiet and dark.
QUIET_DB = -26.0
HF_SUSPECT = 0.12
MIN_GAP_MS = 250.0
EDGE_FADE_MS = 30.0


def load(path: Path) -> tuple[np.ndarray, int]:
    audio, rate = sf.read(str(path), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return audio, int(rate)


def frame_stats(audio: np.ndarray, rate: int):
    """Per-frame level and high-frequency ratio."""
    size = int(rate * FRAME_MS / 1000)
    count = audio.size // size
    block = audio[: count * size].reshape(count, size).astype(np.float64)
    level = np.sqrt((block**2).mean(axis=1) + 1e-12)

    window = np.hanning(size)
    freqs = np.fft.rfftfreq(size, 1 / rate)
    high = freqs > HF_SPLIT_HZ
    power = np.abs(np.fft.rfft(block * window[None, :], axis=1)) ** 2
    total = power.sum(axis=1) + 1e-20
    return level, (power[:, high].sum(axis=1) / total), size


def find_runs(mask: np.ndarray) -> list[tuple[int, int]]:
    runs, start = [], None
    for index, flag in enumerate(mask):
        if flag and start is None:
            start = index
        elif not flag and start is not None:
            runs.append((start, index))
            start = None
    if start is not None:
        runs.append((start, len(mask)))
    return runs


def harvest_floor(
    audio: np.ndarray, level: np.ndarray, hf: np.ndarray, size: int, speech: float
) -> np.ndarray:
    """Longest stretches of the model's own quiet, dark pause audio."""
    quiet = level < speech * 10 ** (QUIET_DB / 20)
    dark = hf < HF_SUSPECT * 0.5
    runs = [(a, b) for a, b in find_runs(quiet & dark) if (b - a) * size >= size * 4]
    runs.sort(key=lambda r: r[1] - r[0], reverse=True)
    if not runs:
        return np.zeros(0, dtype=np.float32)
    donor = [audio[a * size : b * size] for a, b in runs[:12]]
    return np.concatenate(donor).astype(np.float32)


def spectral_fill(
    length: int,
    donor: np.ndarray,
    rate: int,
    target_level: float,
    rng,
    cutoff_hz: float,
    nfft: int = 2048,
) -> np.ndarray:
    """Stationary room tone from the robust PSD of real natural pauses.

    This is the FFT/IFFT donor approach suggested after the waveform donor created
    pops. It differs from the original `comfort_gap` in the two ways that matter:

    * DONOR POPULATION: only confirmed natural, dark pauses reach this function;
      the old synthesiser sampled percentile frames that included the artificial
      bright gaps it was trying to imitate.
    * ROBUST PSD: median power, not mean magnitude. A sparse high-frequency event
      cannot dominate the shape after level normalisation.

    Random complex coefficients drawn against sqrt(PSD), followed by IFFT and Hann
    overlap-add, preserve spectral character while discarding every donor transient.
    """
    if donor.size < nfft or length <= 0:
        return np.zeros(length, dtype=np.float32)

    hop = nfft // 2
    window = np.hanning(nfft)
    spectra = []
    for start in range(0, donor.size - nfft + 1, hop):
        frame = donor[start : start + nfft].astype(np.float64)
        level = float(np.sqrt(np.mean(frame**2) + 1e-20))
        if level < 1e-6:
            continue
        spectra.append(np.abs(np.fft.rfft(frame * window)) ** 2)
    if not spectra:
        return np.zeros(length, dtype=np.float32)

    psd = np.median(np.stack(spectra), axis=0)
    freqs = np.fft.rfftfreq(nfft, 1 / rate)

    # Natural pauses measured zero meaningful energy above 4 kHz. A soft transition
    # avoids the ringing a brick-wall mask would introduce.
    lo = max(200.0, cutoff_hz - 500.0)
    hi = cutoff_hz + 500.0
    mask = np.ones_like(freqs)
    transition = (freqs > lo) & (freqs < hi)
    mask[freqs >= hi] = 0.0
    mask[transition] = 0.5 * (
        1.0 + np.cos(np.pi * (freqs[transition] - lo) / (hi - lo))
    )
    psd *= mask**2

    blocks = int(np.ceil((length + nfft) / hop))
    out = np.zeros(blocks * hop + nfft, dtype=np.float64)
    weight = np.zeros_like(out)
    scale = np.sqrt(np.maximum(psd, 0.0))
    for index in range(blocks):
        # Complex Gaussian coefficients produce a stationary random process with
        # the target power spectrum. DC and Nyquist must be real for irfft.
        coeff = (rng.standard_normal(scale.size) + 1j * rng.standard_normal(scale.size))
        coeff *= scale / np.sqrt(2.0)
        coeff[0] = rng.standard_normal() * scale[0]
        coeff[-1] = rng.standard_normal() * scale[-1]
        frame = np.fft.irfft(coeff, n=nfft) * window
        start = index * hop
        out[start : start + nfft] += frame
        weight[start : start + nfft] += window**2

    valid = weight > 1e-8
    out[valid] /= np.sqrt(weight[valid])
    # Skip the first overlap-add transient and take a settled region.
    out = out[nfft : nfft + length]
    current = float(np.sqrt(np.mean(out**2) + 1e-20))
    if current > 0 and target_level > 0:
        out *= target_level / current
    return out.astype(np.float32)


def fill(length: int, donor: np.ndarray, target_level: float, rng) -> np.ndarray:
    """Build `length` samples of floor from donor material, level-matched."""
    if donor.size < 64:
        return np.zeros(length, dtype=np.float32)
    out = np.zeros(length, dtype=np.float32)
    cursor = 0
    crossfade = min(int(len(donor) // 8), 512)
    while cursor < length:
        take = min(len(donor), length - cursor + crossfade)
        start = int(rng.integers(0, max(1, len(donor) - take)))
        piece = donor[start : start + take].copy()
        if cursor > 0 and crossfade > 0 and cursor - crossfade >= 0:
            ramp = np.linspace(0, 1, crossfade, dtype=np.float32)
            overlap = min(crossfade, length - (cursor - crossfade), piece.size)
            if overlap > 0:
                region = slice(cursor - crossfade, cursor - crossfade + overlap)
                out[region] = out[region] * (1 - ramp[:overlap]) + piece[:overlap] * ramp[:overlap]
                piece = piece[overlap:]
        end = min(length, cursor + piece.size)
        if end > cursor:
            out[cursor:end] = piece[: end - cursor]
        cursor = end
    current = float(np.sqrt(np.mean(out.astype(np.float64) ** 2) + 1e-12))
    if current > 0 and target_level > 0:
        out *= target_level / current
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("audio", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument(
        "--method",
        choices=("spectral", "lowpass", "donor"),
        default="spectral",
        help="spectral synthesises stationary floor from the robust PSD of natural "
        "pauses (recommended); lowpass filters the existing gap; donor copies real "
        "pause audio and is retained only as a rejected comparison",
    )
    p.add_argument(
        "--cutoff-hz",
        type=float,
        default=3500.0,
        help="low-pass cutoff for synthetic gaps; natural pauses had zero measured "
        "energy above 4 kHz",
    )
    p.add_argument(
        "--fft-size",
        type=int,
        choices=(2048, 4096, 8192),
        default=2048,
        help="spectral method FFT size: 2048=46ms/21.5Hz, 4096=93ms/10.8Hz, "
        "8192=186ms/5.4Hz at 44.1kHz; larger resolves room modes better but has "
        "less temporal resolution",
    )
    p.add_argument("--report", type=Path, default=None)
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    if args.output.resolve() == args.audio.resolve():
        raise SystemExit("refusing to write over the input")

    audio, rate = load(args.audio)
    level, hf, size = frame_stats(audio, rate)
    speech = float(np.percentile(level, 90))

    quiet = level < speech * 10 ** (QUIET_DB / 20)
    bright = hf > HF_SUSPECT
    candidates = [
        (a, b)
        for a, b in find_runs(quiet & bright)
        if (b - a) * size / rate * 1000 >= MIN_GAP_MS
    ]

    donor = harvest_floor(audio, level, hf, size, speech)

    # Level is matched per gap against the gap's own existing RMS, not against a
    # global figure. Only the spectrum is wrong, so only the spectrum should change.
    # A global target taken as the median over all quiet frames is biased low by the
    # deep interior of long pauses: it measured 0.002007 where the gaps themselves
    # sit at 0.003568, and using it left every gap 5.1 dB down -- trading audible
    # hiss for an audible dropout.
    natural_runs = [
        float(np.median(level[a:b]))
        for a, b in find_runs(quiet & (hf < HF_SUSPECT * 0.5))
        if b - a >= 4
    ]
    target = float(np.median(natural_runs)) if natural_runs else 0.0

    print(f"{args.audio.name}: {audio.size / rate / 60:.2f} min")
    print(f"  synthetic-tone regions found: {len(candidates)}")
    print(f"  donor floor harvested: {donor.size / rate:.2f}s")
    print(f"  target floor level: {target:.6f}")
    if not candidates:
        print("  nothing to repair")
        return
    if donor.size < rate // 4:
        raise SystemExit("not enough natural pause audio to harvest; aborting")

    repaired = audio.copy()
    rng = np.random.default_rng(0)
    fade = int(rate * EDGE_FADE_MS / 1000)
    changed = []
    for a, b in candidates:
        start, end = a * size, min(b * size, repaired.size)
        span = end - start
        if span <= 2 * fade:
            continue
        before_hf = float(np.median(hf[a:b]))
        # Match this gap's own level, so the repair is spectral only. Measure the
        # interior, not the whole detected region: the region includes the fade
        # skirts either side, and averaging those in under-levelled the audible
        # middle by up to 7 dB.
        margin = min(int(rate * 0.05), span // 4)
        core = audio[start + margin : end - margin]
        existing = float(
            np.sqrt(np.mean((core if core.size else audio[start:end]).astype(np.float64) ** 2) + 1e-20)
        )
        if args.method == "spectral":
            patch = spectral_fill(
                span,
                donor,
                rate,
                existing if existing > 0 else target,
                rng,
                args.cutoff_hz,
                args.fft_size,
            )
        elif args.method == "lowpass":
            # Preserve this gap's exact waveform, timing and amplitude envelope;
            # remove only the spectral band that is absent from natural pauses.
            # Zero-phase filtering avoids shifting the envelope. The result is
            # rescaled to the original core RMS so this is a timbre change, not a
            # level change.
            from scipy.signal import butter, sosfiltfilt

            source = audio[start:end].astype(np.float64)
            sos = butter(6, args.cutoff_hz, btype="lowpass", fs=rate, output="sos")
            filtered = sosfiltfilt(sos, source).astype(np.float32)
            core_filtered = filtered[margin:-margin] if margin and filtered.size > 2 * margin else filtered
            current = float(np.sqrt(np.mean(core_filtered.astype(np.float64) ** 2) + 1e-20))
            if current > 0 and existing > 0:
                filtered *= existing / current
            patch = filtered
        else:
            patch = fill(span, donor, existing if existing > 0 else target, rng)

        # Proper equal-time crossfades. Start: original -> patch. End: patch ->
        # original. At alpha endpoints the result equals the untouched waveform,
        # so filtering cannot create a sample discontinuity at either boundary.
        alpha = np.linspace(0, 1, fade, dtype=np.float32)
        repaired[start : start + fade] = (
            repaired[start : start + fade] * (1 - alpha)
            + patch[:fade] * alpha
        )
        repaired[start + fade : end - fade] = patch[fade:-fade]
        repaired[end - fade : end] = (
            patch[-fade:] * (1 - alpha)
            + repaired[end - fade : end] * alpha
        )
        changed.append(
            {
                "start": round(start / rate, 3),
                "end": round(end / rate, 3),
                "ms": round(span / rate * 1000, 1),
                "hf_before": round(before_hf, 4),
                "method": args.method,
                "cutoff_hz": args.cutoff_hz if args.method in {"lowpass", "spectral"} else None,
                "fft_size": args.fft_size if args.method == "spectral" else None,
            }
        )

    if args.dry_run:
        print(f"  would repair {len(changed)} regions (dry run, nothing written)")
        for item in changed[:8]:
            print(f"    {item['start']:7.2f}-{item['end']:7.2f}s  hf {item['hf_before']:.3f}")
        return

    assert repaired.size == audio.size, "duration must not change"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(args.output), repaired, rate, subtype="PCM_16")

    after_level, after_hf, _ = frame_stats(repaired, rate)
    print(f"  repaired {len(changed)} regions")
    print(f"  wrote {args.output}")
    print(
        f"  duration unchanged: {audio.size / rate:.3f}s -> {repaired.size / rate:.3f}s"
    )
    checked = []
    for item in changed:
        a = int(item["start"] * rate / size)
        b = int(item["end"] * rate / size)
        checked.append(float(np.median(after_hf[a:b])))
    if checked:
        print(
            f"  hf above 4 kHz in those regions: "
            f"{np.median([c['hf_before'] for c in changed]):.4f} -> "
            f"{float(np.median(checked)):.4f}"
        )

    if args.report:
        args.report.write_text(
            json.dumps({"input": str(args.audio), "output": str(args.output),
                        "regions": changed}, indent=2)
        )
        print(f"  report -> {args.report}")


if __name__ == "__main__":
    main()
