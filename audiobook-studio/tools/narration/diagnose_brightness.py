"""Does the voice get duller across a chapter?

Why this exists
---------------
Four blind chapter-boundary clips -- two boundaries, production and anchored -- were
all heard the same way: at the cut the voice gets "lighter, clearer". Two of those
four boundaries step *downward* in F0 (-0.81 and -1.17 semitones), so pitch has the
direction wrong on half the set and cannot be what is being heard.

Every clip was a chapter tail followed by a chapter head. If chapter endings are
duller than chapter beginnings, all four clips brighten at the cut regardless of
which chapters they join or how the chapters were generated. That is a within-chapter
trajectory, and nothing in the pipeline looks at it: `flatten_slope` corrects a level
slope inside a segment and `match_levels` matches level between segments, both
level-only, both blind to spectrum.

What is measured
----------------
Per window, over speech-active frames only:

  centroid   spectral centroid in Hz -- the standard correlate of brightness
  hf2k       fraction of energy above 2 kHz
  tilt       dB/octave regression of the log spectrum, a direct measure of how
             much high frequency is present relative to low

Silence is excluded deliberately. Repaired gaps were rewritten to carry zero energy
above 4 kHz, so including them would manufacture exactly the trend being looked for.

No generation. Reads rendered WAVs.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import soundfile as sf

NFFT = 2048
HOP = 1024
VOICED_DB = -36.0


def chapter_number(path: Path) -> int:
    match = re.search(r"-chapter-(\d{3})-", path.name)
    if not match:
        raise ValueError(path.name)
    return int(match.group(1))


def spectra(audio: np.ndarray, rate: int):
    """Voiced-frame power spectra and their frame times."""
    if audio.size < NFFT:
        return np.zeros((0, NFFT // 2 + 1)), np.zeros(0)
    starts = np.arange(0, audio.size - NFFT + 1, HOP)
    frames = np.stack([audio[s : s + NFFT] for s in starts]).astype(np.float64)
    rms = np.sqrt((frames**2).mean(axis=1) + 1e-20)
    peak = float(rms.max())
    if peak <= 0:
        return np.zeros((0, NFFT // 2 + 1)), np.zeros(0)
    keep = rms >= peak * 10 ** (VOICED_DB / 20)
    if not keep.any():
        return np.zeros((0, NFFT // 2 + 1)), np.zeros(0)
    frames = frames[keep] * np.hanning(NFFT)[None, :]
    power = np.abs(np.fft.rfft(frames, axis=1)) ** 2
    times = (starts[keep] + NFFT / 2) / rate
    return power, times


def descriptors(power: np.ndarray, freqs: np.ndarray) -> dict:
    total = power.sum(axis=1) + 1e-20
    centroid = (power * freqs[None, :]).sum(axis=1) / total
    hf2k = power[:, freqs > 2000].sum(axis=1) / total
    # Spectral tilt: least-squares dB/octave over the band that carries voice
    # information. Fit per frame, then take the median.
    band = (freqs >= 200) & (freqs <= 8000)
    octaves = np.log2(freqs[band] / 200.0)
    db = 10 * np.log10(power[:, band] + 1e-20)
    centred = octaves - octaves.mean()
    denom = float((centred**2).sum())
    tilt = (db - db.mean(axis=1, keepdims=True)) @ centred / denom if denom > 0 else np.zeros(db.shape[0])
    return {
        "centroid": float(np.median(centroid)),
        "hf2k": float(np.median(hf2k)),
        "tilt": float(np.median(tilt)),
    }


def trend(values: list[float], minutes: float) -> float:
    if len(values) < 4 or minutes <= 0:
        return 0.0
    return float(np.polyfit(np.linspace(0.0, minutes, len(values)), values, 1)[0])


def analyse(path: Path, window: float) -> dict | None:
    audio, rate = sf.read(str(path), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    freqs = np.fft.rfftfreq(NFFT, 1 / rate)
    span = int(window * rate)
    rows = []
    for start in range(0, max(1, audio.size - span // 2), span):
        piece = audio[start : start + span]
        if piece.size < span // 2:
            break
        power, _ = spectra(piece, rate)
        if power.shape[0] < 8:
            continue
        rows.append(descriptors(power, freqs))
    if len(rows) < 4:
        return None
    minutes = audio.size / rate / 60.0
    out = {"chapter": chapter_number(path), "minutes": round(minutes, 2), "windows": len(rows)}
    for field, unit in (("centroid", "hz"), ("hf2k", "ratio"), ("tilt", "db_oct")):
        series = [r[field] for r in rows]
        out[f"{field}_head"] = round(series[0], 4)
        out[f"{field}_tail"] = round(series[-1], 4)
        out[f"{field}_delta"] = round(series[-1] - series[0], 4)
        out[f"{field}_slope_per_min"] = round(trend(series, minutes), 4)
        out[f"{field}_mean"] = round(float(np.mean(series)), 4)
    return out


def report(name: str, records: list[dict]) -> None:
    print(f"\n=== {name} ({len(records)} chapters) ===")
    print("ch   mins   centroid head->tail    Hz/min    hf2k h->t     tilt h->t")
    for r in records:
        print(
            f"{r['chapter']:3d} {r['minutes']:6.2f}   "
            f"{r['centroid_head']:7.1f}->{r['centroid_tail']:7.1f} "
            f"{r['centroid_delta']:+8.1f} {r['centroid_slope_per_min']:+9.2f}  "
            f"{r['hf2k_head']:.4f}->{r['hf2k_tail']:.4f}  "
            f"{r['tilt_head']:+6.2f}->{r['tilt_tail']:+6.2f}"
        )
    for field, label in (
        ("centroid", "centroid Hz"),
        ("hf2k", "energy >2kHz"),
        ("tilt", "tilt dB/oct"),
    ):
        slopes = [r[f"{field}_slope_per_min"] for r in records]
        deltas = [r[f"{field}_delta"] for r in records]
        down = sum(1 for d in deltas if d < 0)
        print(
            f"  {label:14s} head->tail mean {np.mean(deltas):+9.4f} "
            f"(sd {np.std(deltas):.4f}), falling in {down}/{len(deltas)}, "
            f"slope mean {np.mean(slopes):+.4f}/min"
        )


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--books",
        type=Path,
        nargs="+",
        default=[Path("out/book-repaired"), Path("out/anchor-full-repaired")],
    )
    p.add_argument("--window", type=float, default=15.0)
    p.add_argument("--out", type=Path, default=Path("out/brightness.json"))
    args = p.parse_args()

    everything = {}
    for book in args.books:
        files = sorted(book.glob("*-fish-clean92.wav"), key=chapter_number)
        records = [r for r in (analyse(f, args.window) for f in files) if r]
        if not records:
            print(f"no usable chapters in {book}")
            continue
        everything[str(book)] = records
        report(str(book), records)

    args.out.write_text(json.dumps(everything, indent=2))
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
