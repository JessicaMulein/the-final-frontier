"""Is the brightness decay caused by generation, or by the book?

Two explanations survive the measurement that brightness falls in 17 chapters out of
17:

  accumulation   Fish appends each rendered segment into a running Conversation and
                 conditions the next on its own output. Its output is slightly duller
                 than the reference, so dullness compounds. Under this explanation the
                 decay is a function of *elapsed generated time*, and every chapter
                 restarts the clock from its own fresh reference.
  the prose      chapters may simply end in quieter, more reflective writing, and a
                 narrator genuinely darkens when easing off. Under this explanation
                 the decay is a function of *fractional position* in the chapter, and
                 a short chapter should dull as much overall as a long one.

These predict different things, so they can be told apart with the audio already on
disk. Pool every window of every chapter and compare how well each variable explains
brightness:

  absolute minutes elapsed  ->  favours accumulation
  fraction through chapter   ->  favours the prose

A further discriminator: under accumulation, a long chapter keeps dulling and so ends
darker in absolute terms than a short one. Under the prose explanation, chapters end
at a similar place regardless of length.

Level is measured alongside, because if brightness and loudness fall together the
narrator is easing off and the decay should be left alone. Earlier measurement says
they do not: level rises slightly while brightness falls.

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
VOICED_DB = -36.0


def chapter_number(path: Path) -> int:
    match = re.search(r"-chapter-(\d{3})-", path.name)
    if not match:
        raise ValueError(path.name)
    return int(match.group(1))


def window_measures(audio: np.ndarray, rate: int, seconds: float):
    """Per-window centroid and voiced level, with window centre times."""
    freqs = np.fft.rfftfreq(NFFT, 1 / rate)
    span = int(seconds * rate)
    rows = []
    for start in range(0, max(1, audio.size - span // 2), span):
        piece = audio[start : start + span]
        if piece.size < span // 2:
            break
        if piece.size < NFFT:
            continue
        starts = np.arange(0, piece.size - NFFT + 1, NFFT // 2)
        frames = np.stack([piece[s : s + NFFT] for s in starts]).astype(np.float64)
        rms = np.sqrt((frames**2).mean(axis=1) + 1e-20)
        peak = float(rms.max())
        if peak <= 0:
            continue
        keep = rms >= peak * 10 ** (VOICED_DB / 20)
        if int(keep.sum()) < 8:
            continue
        power = np.abs(np.fft.rfft(frames[keep] * np.hanning(NFFT)[None, :], axis=1)) ** 2
        total = power.sum(axis=1) + 1e-20
        centroid = float(np.median((power * freqs[None, :]).sum(axis=1) / total))
        level = 20 * np.log10(float(np.sqrt(np.mean(rms[keep] ** 2))) + 1e-12)
        rows.append(
            {
                "minutes": (start + piece.size / 2) / rate / 60.0,
                "centroid": centroid,
                "level_db": level,
            }
        )
    return rows


def r_squared(x: np.ndarray, y: np.ndarray) -> tuple[float, float]:
    """(slope, R^2) of a straight-line fit."""
    if x.size < 4 or float(np.std(x)) == 0.0:
        return 0.0, 0.0
    slope, intercept = np.polyfit(x, y, 1)
    predicted = slope * x + intercept
    residual = float(((y - predicted) ** 2).sum())
    total = float(((y - y.mean()) ** 2).sum())
    return float(slope), (1.0 - residual / total if total > 0 else 0.0)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--book", type=Path, default=Path("out/book-repaired"))
    p.add_argument("--window", type=float, default=15.0)
    p.add_argument("--out", type=Path, default=Path("out/accumulation.json"))
    args = p.parse_args()

    files = sorted(args.book.glob("*-fish-clean92.wav"), key=chapter_number)
    if not files:
        raise SystemExit(f"no chapters in {args.book}")

    chapters = []
    for path in files:
        audio, rate = sf.read(str(path), always_2d=False)
        audio = np.asarray(audio, dtype=np.float32)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        rows = window_measures(audio, rate, args.window)
        if len(rows) < 4:
            continue
        total_minutes = audio.size / rate / 60.0
        for row in rows:
            row["fraction"] = row["minutes"] / total_minutes
        chapters.append(
            {
                "chapter": chapter_number(path),
                "minutes": total_minutes,
                "rows": rows,
            }
        )

    # Pooled comparison. Centre each chapter on its own mean so differences in
    # absolute brightness between chapters cannot flatter either variable.
    minutes, fraction, centred, raw, levels = [], [], [], [], []
    for item in chapters:
        values = np.array([r["centroid"] for r in item["rows"]])
        minutes.extend(r["minutes"] for r in item["rows"])
        fraction.extend(r["fraction"] for r in item["rows"])
        centred.extend(values - values.mean())
        raw.extend(values)
        levels.extend(r["level_db"] for r in item["rows"])
    minutes = np.array(minutes)
    fraction = np.array(fraction)
    centred = np.array(centred)
    raw = np.array(raw)
    levels = np.array(levels)

    print(f"{len(chapters)} chapters, {raw.size} windows of {args.window:.0f}s\n")
    slope_m, r2_m = r_squared(minutes, centred)
    slope_f, r2_f = r_squared(fraction, centred)
    print("explaining within-chapter brightness (chapter mean removed)")
    print(f"  absolute minutes elapsed   slope {slope_m:+8.2f} Hz/min   R2 {r2_m:.4f}")
    print(f"  fraction through chapter   slope {slope_f:+8.2f} Hz/unit  R2 {r2_f:.4f}")
    winner = "accumulation (elapsed time)" if r2_m > r2_f else "the prose (position)"
    print(f"  better explained by: {winner}")

    # Does a longer chapter end darker in absolute terms?
    ends = [(c["minutes"], c["rows"][-1]["centroid"]) for c in chapters]
    lengths = np.array([e[0] for e in ends])
    finals = np.array([e[1] for e in ends])
    slope_e, r2_e = r_squared(lengths, finals)
    print("\ndoes a longer chapter end darker?")
    print(f"  final centroid vs chapter length   slope {slope_e:+7.2f} Hz/min  R2 {r2_e:.4f}")
    print(
        "  accumulation predicts a negative slope here; the prose explanation "
        "predicts roughly zero"
    )

    # Brightness against loudness: if they fall together the narrator is easing off.
    slope_l, r2_l = r_squared(levels, raw)
    print("\nis brightness just following loudness?")
    print(f"  centroid vs voiced level   slope {slope_l:+7.2f} Hz/dB  R2 {r2_l:.4f}")

    args.out.write_text(
        json.dumps(
            {
                "window_seconds": args.window,
                "windows": int(raw.size),
                "pooled": {
                    "minutes": {"slope_hz_per_min": round(slope_m, 4), "r2": round(r2_m, 4)},
                    "fraction": {"slope_hz_per_unit": round(slope_f, 4), "r2": round(r2_f, 4)},
                    "length_vs_final": {
                        "slope_hz_per_min": round(slope_e, 4),
                        "r2": round(r2_e, 4),
                    },
                    "level_vs_centroid": {
                        "slope_hz_per_db": round(slope_l, 4),
                        "r2": round(r2_l, 4),
                    },
                },
                "chapters": [
                    {
                        "chapter": c["chapter"],
                        "minutes": round(c["minutes"], 3),
                        "first_centroid": round(c["rows"][0]["centroid"], 1),
                        "final_centroid": round(c["rows"][-1]["centroid"], 1),
                    }
                    for c in chapters
                ],
            },
            indent=2,
        )
    )
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
