"""Blind A/B of real chapter boundaries: production versus anchored.

This is the product, not a diagnostic. Each clip is the end of one chapter, a
chapter break, and the start of the next -- exactly what a listener meets when the
book plays through. The two boundaries chosen are the worst measured in the book:
10 -> 11 and 11 -> 12, which in production step +0.84 and -1.17 semitones.

Each chapter is normalised to one common active-RMS target first, because the
finished book gets a loudness pass anyway and chapter level spread (4.91 dB across
the book) would otherwise mask the thing under test. What is left is register.

Both sides come from gap-repaired audio, so the synthesised-hiss defect is not in
the way of the judgement.
"""

from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path

import numpy as np
import soundfile as sf

from render_chapter_fish import active_rms

TARGET_RMS = 0.075


def find(book: Path, number: int) -> Path:
    matches = sorted(book.glob(f"*-chapter-{number:03d}-fish-clean92.wav"))
    if len(matches) != 1:
        raise SystemExit(f"chapter {number} in {book}: found {matches}")
    return matches[0]


def read_normalised(path: Path) -> tuple[np.ndarray, int]:
    audio, rate = sf.read(str(path), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    level = active_rms(audio, rate)
    if level > 0:
        audio = audio * (TARGET_RMS / level)
        peak = float(np.abs(audio).max())
        if peak > 0.97:
            audio = audio / peak * 0.97
    return audio, int(rate)


def centroid(audio: np.ndarray, rate: int, nfft: int = 2048) -> float:
    """Median spectral centroid over speech-active frames."""
    if audio.size < nfft:
        return 0.0
    starts = np.arange(0, audio.size - nfft + 1, nfft // 2)
    frames = np.stack([audio[s : s + nfft] for s in starts]).astype(np.float64)
    rms = np.sqrt((frames**2).mean(axis=1) + 1e-20)
    peak = float(rms.max())
    if peak <= 0:
        return 0.0
    keep = rms >= peak * 10 ** (-36 / 20)
    if not keep.any():
        return 0.0
    power = np.abs(np.fft.rfft(frames[keep] * np.hanning(nfft)[None, :], axis=1)) ** 2
    freqs = np.fft.rfftfreq(nfft, 1 / rate)
    total = power.sum(axis=1) + 1e-20
    return float(np.median((power * freqs[None, :]).sum(axis=1) / total))


def trim_edges(audio: np.ndarray, rate: int, floor_db: float = -45.0) -> np.ndarray:
    win = max(1, int(0.02 * rate))
    frames = audio[: audio.size - audio.size % win].reshape(-1, win)
    rms = np.sqrt((frames.astype(np.float64) ** 2).mean(axis=1) + 1e-12)
    loud = np.flatnonzero(20 * np.log10(rms / (np.abs(audio).max() + 1e-12)) > floor_db)
    if loud.size == 0:
        return audio
    return audio[loud[0] * win : min(audio.size, (loud[-1] + 1) * win)]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--book",
        action="append",
        default=None,
        metavar="NAME=PATH",
        help="a condition to compare, e.g. production=out/book-repaired; repeatable",
    )
    p.add_argument("--out", type=Path, default=Path("out/boundary-ab"))
    p.add_argument("--boundaries", type=int, nargs="+", default=[10, 11, 11, 12])
    p.add_argument("--seconds", type=float, default=15.0)
    p.add_argument("--break-ms", type=float, default=1200.0)
    p.add_argument("--seed", type=int, default=4477)
    p.add_argument(
        "--announce-dir",
        type=Path,
        default=None,
        help="directory of rendered chapter announcements; when given, each boundary "
        "is built twice -- bare, and with the incoming chapter announced -- so the "
        "two can be compared blind",
    )
    p.add_argument(
        "--announce-lead-ms",
        type=float,
        default=1000.0,
        help="silence between the outgoing chapter and the announcement",
    )
    p.add_argument(
        "--announce-tail-ms",
        type=float,
        default=900.0,
        help="silence between the announcement and the incoming chapter",
    )
    args = p.parse_args()

    boundaries = list(zip(args.boundaries[0::2], args.boundaries[1::2]))
    args.out.mkdir(parents=True, exist_ok=True)

    specs = args.book or [
        "production=out/book-repaired",
        "anchored=out/anchor-full-repaired",
    ]
    sources: dict[str, Path] = {}
    for spec in specs:
        if "=" not in spec:
            raise SystemExit(f"--book expects NAME=PATH, got {spec!r}")
        name, path = spec.split("=", 1)
        sources[name] = Path(path)
    cache: dict[tuple[str, int], tuple[np.ndarray, int]] = {}
    for name, book in sources.items():
        for number in sorted({n for pair in boundaries for n in pair}):
            audio, rate = read_normalised(find(book, number))
            cache[(name, number)] = (trim_edges(audio, rate), rate)

    # Announcements are normalised to the same target as the chapters so the
    # narrator's level does not jump at the signpost, which would be heard as a
    # step in its own right and confound the thing under test.
    announcements: dict[int, np.ndarray] = {}
    if args.announce_dir is not None:
        for number in sorted({n for pair in boundaries for n in pair}):
            matches = sorted(args.announce_dir.glob(f"chapter-{number:03d}-*.wav"))
            if not matches:
                continue
            audio, rate = read_normalised(matches[0])
            announcements[number] = trim_edges(audio, rate)

    plans = [
        (name, a, b, announce)
        for a, b in boundaries
        for name in sources
        for announce in ((False, True) if announcements else (False,))
    ]
    rng = random.Random(args.seed)
    labels = [f"boundary-{i + 1:02d}" for i in range(len(plans))]
    rng.shuffle(labels)

    key = {}
    print("clip             condition   boundary  announced   out -> in centroid   jump")
    for label, (name, a, b, announce) in zip(labels, plans):
        left, rate = cache[(name, a)]
        right, _ = cache[(name, b)]
        span = int(args.seconds * rate)

        def silence(milliseconds: float) -> np.ndarray:
            return np.zeros(int(rate * milliseconds / 1000), dtype=np.float32)

        middle: list[np.ndarray]
        if announce and b in announcements:
            middle = [
                silence(args.announce_lead_ms),
                announcements[b],
                silence(args.announce_tail_ms),
            ]
        else:
            middle = [silence(args.break_ms)]
        clip = np.concatenate([left[-span:], *middle, right[:span]])
        sf.write(str(args.out / f"{label}.wav"), clip, rate, subtype="PCM_16")
        # Spectral centroid is the one measure that has ordered this listener's
        # judgements correctly, so record the step it predicts for each clip.
        out_c = centroid(left[-span:], rate)
        in_c = centroid(right[:span], rate)
        key[label] = {
            "condition": name,
            "boundary": f"{a:03d} -> {b:03d}",
            "announced": bool(announce and b in announcements),
            "centroid_out_hz": round(out_c, 1),
            "centroid_in_hz": round(in_c, 1),
            "centroid_jump_hz": round(in_c - out_c, 1),
        }
        print(
            f"{label}.wav  {name:>12s}  {a:03d} -> {b:03d}  "
            f"{'yes' if key[label]['announced'] else ' no':>9s}   "
            f"{out_c:7.1f} -> {in_c:7.1f}  {in_c - out_c:+7.1f}"
        )

    (args.out / "blind_key.json").write_text(json.dumps(key, indent=2))
    print(f"\n{len(plans)} clips in {args.out}; key in blind_key.json")


if __name__ == "__main__":
    main()
