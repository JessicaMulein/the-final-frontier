"""Cut listening clips for the tilt correction and verify it did nothing else.

The correction lifts high frequencies where a chapter has least of them, so the
plausible damage is raised breath and noise rather than restored clarity. That has
to be judged by ear, but three things can be checked by measurement first:

  head untouched   with --target head the correction is zero at the chapter start,
                   so the opening must be sample-identical to the input
  gaps untouched   repaired inter-paragraph gaps were rewritten to carry no energy
                   above 4 kHz; a tilt lift leaking into them would undo that
  duration exact   so existing manifests and timestamps stay valid
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import soundfile as sf

NFFT = 2048


def load(path: Path) -> tuple[np.ndarray, int]:
    audio, rate = sf.read(str(path), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return audio, int(rate)


def voiced_descriptors(audio: np.ndarray, rate: int) -> dict:
    """Centroid and >2 kHz ratio over speech-active frames only."""
    if audio.size < NFFT:
        return {}
    starts = np.arange(0, audio.size - NFFT + 1, NFFT // 2)
    frames = np.stack([audio[s : s + NFFT] for s in starts]).astype(np.float64)
    rms = np.sqrt((frames**2).mean(axis=1) + 1e-20)
    peak = float(rms.max())
    if peak <= 0:
        return {}
    keep = rms >= peak * 10 ** (-36 / 20)
    if not keep.any():
        return {}
    power = np.abs(np.fft.rfft(frames[keep] * np.hanning(NFFT)[None, :], axis=1)) ** 2
    freqs = np.fft.rfftfreq(NFFT, 1 / rate)
    total = power.sum(axis=1) + 1e-20
    return {
        "centroid_hz": round(float(np.median((power * freqs[None, :]).sum(axis=1) / total)), 1),
        "hf2k": round(float(np.median(power[:, freqs > 2000].sum(axis=1) / total)), 5),
    }


def quiet_hf(audio: np.ndarray, rate: int) -> float:
    """Median >4 kHz ratio in the quietest frames -- the repaired gap regions."""
    starts = np.arange(0, max(1, audio.size - NFFT + 1), NFFT // 2)
    frames = np.stack([audio[s : s + NFFT] for s in starts]).astype(np.float64)
    rms = np.sqrt((frames**2).mean(axis=1) + 1e-20)
    peak = float(rms.max())
    if peak <= 0:
        return 0.0
    quiet = rms <= peak * 10 ** (-50 / 20)
    if not quiet.any():
        return 0.0
    power = np.abs(np.fft.rfft(frames[quiet] * np.hanning(NFFT)[None, :], axis=1)) ** 2
    freqs = np.fft.rfftfreq(NFFT, 1 / rate)
    total = power.sum(axis=1) + 1e-20
    return round(float(np.median(power[:, freqs > 4000].sum(axis=1) / total)), 5)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--original", type=Path, required=True)
    p.add_argument("--variants", type=Path, nargs="+", required=True)
    p.add_argument("--out", type=Path, default=Path("out/tilt-test/clips"))
    p.add_argument("--seconds", type=float, default=20.0)
    p.add_argument("--seed", type=int, default=6120)
    args = p.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    original, rate = load(args.original)
    span = int(args.seconds * rate)

    print("verification against the original")
    print("name       samples  head identical  tail centroid  tail hf2k  quiet hf>4k")
    orig_tail = voiced_descriptors(original[-span:], rate)
    print(
        f"{'original':10s} {original.size:8d}  {'--':>14s}  "
        f"{orig_tail.get('centroid_hz', 0):13.1f}  {orig_tail.get('hf2k', 0):9.5f}  "
        f"{quiet_hf(original, rate):11.5f}"
    )

    checks = {}
    for path in args.variants:
        audio, r = load(path)
        if r != rate:
            raise SystemExit(f"{path.name}: sample rate {r} != {rate}")
        if audio.size != original.size:
            raise SystemExit(f"{path.name}: {audio.size} samples != {original.size}")
        head_span = min(span, audio.size)
        head_delta = float(np.abs(audio[:head_span] - original[:head_span]).max())
        tail = voiced_descriptors(audio[-span:], rate)
        checks[path.stem] = {
            "samples": int(audio.size),
            "head_max_abs_diff": round(head_delta, 6),
            "tail_centroid_hz": tail.get("centroid_hz"),
            "tail_hf2k": tail.get("hf2k"),
            "quiet_hf_above_4k": quiet_hf(audio, rate),
        }
        print(
            f"{path.stem:10s} {audio.size:8d}  {head_delta:14.6f}  "
            f"{tail.get('centroid_hz', 0):13.1f}  {tail.get('hf2k', 0):9.5f}  "
            f"{quiet_hf(audio, rate):11.5f}"
        )

    # Blind labels for the variants; the original is labelled so it can anchor.
    sf.write(str(args.out / "tail-orig.wav"), original[-span:], rate, subtype="PCM_16")
    labels = list("XYZWV")[: len(args.variants)]
    rng = random.Random(args.seed)
    rng.shuffle(labels)
    key = {}
    for label, path in zip(labels, args.variants):
        audio, _ = load(path)
        sf.write(str(args.out / f"tail-{label}.wav"), audio[-span:], rate, subtype="PCM_16")
        key[f"tail-{label}"] = path.stem

    (args.out / "blind_key.json").write_text(json.dumps(key, indent=2))
    (args.out / "checks.json").write_text(json.dumps(checks, indent=2))
    print(f"\nwrote tail-orig plus {len(labels)} blind variants to {args.out}")


if __name__ == "__main__":
    main()
