"""Separate within-chapter drift from between-chapter drift in the anchor experiment.

The problem this resolves
------------------------
The listener reports that the four standalone anchored excerpts sound consistent
with one another, but the blind *pair* clips built from those same four files do
not. Both cannot be true of the same audio unless the pair construction itself
introduces the difference.

anchor_experiment.write_transition builds a pair as:

    left[-12s:]  +  0.5s silence  +  right[:12s]

That is a *tail* against a *head*. Measured on the anchored files, tails sit
0.8-6.2 Hz lower in median F0 and roughly 1.5-2 dB quieter than the heads of the
same generation. So the pair clip is not isolating the chapter boundary: it adds
one generation's internal decay to whatever between-chapter step exists.

This script rebuilds the comparison with the confound removed, using only the
already-rendered waveforms -- no generation, no GPU.

  within   head of chapter N  vs  tail of chapter N   (same generation, same
           chapter, same seed: any audible step here is drift *inside* one
           render and has nothing to do with chapter boundaries)
  across   head of chapter N  vs  head of chapter N+1 (the boundary question,
           asked fairly: same position in each generation)
  legacy   tail of chapter N  vs  head of chapter N+1 (the original
           construction, kept so the three can be compared directly)

Both sides of every clip are normalised to one fixed active-RMS target, so
loudness is constant across every clip in the set and register is the only
variable left. Clips are blind-labelled; the key is written to a separate file.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from diagnose_voice import fingerprint, robust_distance
from prosody import estimate_f0_track
from render_chapter_fish import active_rms

TARGET_RMS = 0.075


def read_mono(path: Path) -> tuple[np.ndarray, int]:
    audio, rate = sf.read(str(path), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return audio, int(rate)


def trim_silence(audio: np.ndarray, rate: int, floor_db: float = -45.0) -> np.ndarray:
    """Drop leading and trailing near-silence so 'tail' means final speech."""
    win = max(1, int(0.02 * rate))
    frames = audio[: audio.size - audio.size % win].reshape(-1, win)
    rms = np.sqrt((frames.astype(np.float64) ** 2).mean(axis=1) + 1e-12)
    loud = np.flatnonzero(20 * np.log10(rms / (np.abs(audio).max() + 1e-12)) > floor_db)
    if loud.size == 0:
        return audio
    return audio[loud[0] * win : min(audio.size, (loud[-1] + 1) * win)]


def at_level(audio: np.ndarray, rate: int) -> np.ndarray:
    level = active_rms(audio, rate)
    if level <= 0:
        return audio
    scaled = audio * (TARGET_RMS / level)
    peak = np.abs(scaled).max()
    return scaled / peak * 0.97 if peak > 0.97 else scaled


def register(audio: np.ndarray, rate: int) -> dict:
    """Median F0 plus a p20 'baseline' that is less swayed by prosodic reach.

    Median F0 over 12 s of *different* text mixes register with what the
    sentences happen to be doing. The low percentile of the F0 distribution is a
    closer proxy for the floor a speaker keeps returning to, which is what
    'the voice went deeper' actually refers to.
    """
    a24 = resample_poly(audio, 80, 147).astype(np.float32) if rate == 44100 else audio
    track = estimate_f0_track(a24)
    if track.size < 12:
        return {"median": 0.0, "p20": 0.0, "frames": int(track.size)}
    return {
        "median": round(float(np.median(track)), 2),
        "p20": round(float(np.percentile(track, 20)), 2),
        "frames": int(track.size),
    }


def timbre(audio: np.ndarray, rate: int) -> dict:
    a16 = resample_poly(audio, 160, 441).astype(np.float32) if rate == 44100 else audio
    return fingerprint(a16, 16000 if rate == 44100 else rate)


def side(audio: np.ndarray, rate: int, where: str, seconds: float) -> np.ndarray:
    span = int(seconds * rate)
    return audio[:span] if where == "head" else audio[-span:]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, default=Path("out/anchor-experiment"))
    p.add_argument("--out", type=Path, default=Path("out/anchor-pairs"))
    p.add_argument("--condition", default="anchored", choices=["anchored", "fixed"])
    p.add_argument("--pairs", type=int, nargs="+", default=[1, 2, 11, 12])
    p.add_argument("--seconds", type=float, default=12.0)
    p.add_argument("--seed", type=int, default=911)
    args = p.parse_args()

    if len(args.pairs) % 2:
        raise SystemExit("--pairs must be an even number of chapters")
    pairs = list(zip(args.pairs[0::2], args.pairs[1::2]))
    chapters = sorted(set(args.pairs))

    args.out.mkdir(parents=True, exist_ok=True)

    loaded: dict[int, tuple[np.ndarray, int]] = {}
    for number in chapters:
        path = args.source / f"ch{number:03d}-{args.condition}.wav"
        if not path.exists():
            raise SystemExit(f"missing {path}")
        audio, rate = read_mono(path)
        loaded[number] = (trim_silence(audio, rate), rate)

    # Measure every side once.
    sides: dict[tuple[int, str], dict] = {}
    for number in chapters:
        audio, rate = loaded[number]
        for where in ("head", "tail"):
            piece = side(audio, rate, where, args.seconds)
            sides[(number, where)] = {
                "audio": piece,
                "register": register(piece, rate),
                "timbre": timbre(piece, rate),
                "dbfs": round(float(20 * np.log10(active_rms(piece, rate) + 1e-12)), 2),
            }

    def step(a: tuple[int, str], b: tuple[int, str]) -> dict:
        x, y = sides[a], sides[b]
        return {
            "median_delta_hz": round(y["register"]["median"] - x["register"]["median"], 2),
            "p20_delta_hz": round(y["register"]["p20"] - x["register"]["p20"], 2),
            "level_delta_db": round(y["dbfs"] - x["dbfs"], 2),
            "timbre_distance": round(robust_distance(x["timbre"], y["timbre"]), 3),
        }

    print(f"condition: {args.condition}   window: {args.seconds:.0f}s\n")
    print("WITHIN one generation (head -> tail of the same chapter)")
    print("chapter   median dHz   p20 dHz   level dB   timbre")
    internal = []
    for number in chapters:
        s = step((number, "head"), (number, "tail"))
        s["chapter"] = number
        internal.append(s)
        print(
            f"  {number:03d}   {s['median_delta_hz']:+10.2f} {s['p20_delta_hz']:+9.2f} "
            f"{s['level_delta_db']:+10.2f} {s['timbre_distance']:8.3f}"
        )

    print("\nBETWEEN chapters, same position in each generation (head -> head)")
    print("pair        median dHz   p20 dHz   level dB   timbre")
    boundary = []
    for left, right in pairs:
        fair = step((left, "head"), (right, "head"))
        legacy = step((left, "tail"), (right, "head"))
        boundary.append(
            {"pair": f"{left:03d}-{right:03d}", "head_vs_head": fair, "tail_vs_head": legacy}
        )
        print(
            f"{left:03d}-{right:03d}   {fair['median_delta_hz']:+10.2f} "
            f"{fair['p20_delta_hz']:+9.2f} {fair['level_delta_db']:+10.2f} "
            f"{fair['timbre_distance']:8.3f}"
        )
    print("\nsame pairs as the original clips built them (tail -> head)")
    for record in boundary:
        legacy = record["tail_vs_head"]
        print(
            f"{record['pair']}   {legacy['median_delta_hz']:+10.2f} "
            f"{legacy['p20_delta_hz']:+9.2f} {legacy['level_delta_db']:+10.2f} "
            f"{legacy['timbre_distance']:8.3f}"
        )

    # Blind clips. Every clip is two 12s sides at one fixed level, 0.5s apart.
    # 'null' is the same audio on both sides: a listener who hears a step there
    # invalidates the protocol, so it is worth the 25 seconds it costs.
    plans = [("null", chapters[0], "head", chapters[0], "head")]
    for left, right in pairs:
        plans.append(("within", left, "head", left, "tail"))
        plans.append(("within", right, "head", right, "tail"))
        plans.append(("across", left, "head", right, "head"))
        plans.append(("legacy", left, "tail", right, "head"))

    rng = random.Random(args.seed)
    labels = [f"clip-{i + 1:02d}" for i in range(len(plans))]
    rng.shuffle(labels)

    key = {}
    for label, (kind, la, lw, ra, rw) in zip(labels, plans):
        rate = loaded[la][1]
        left_side = at_level(sides[(la, lw)]["audio"], rate)
        right_side = at_level(sides[(ra, rw)]["audio"], rate)
        clip = np.concatenate(
            [left_side, np.zeros(int(0.5 * rate), dtype=np.float32), right_side]
        )
        sf.write(str(args.out / f"{label}.wav"), clip, rate, subtype="PCM_16")
        key[label] = {
            "kind": kind,
            "left": f"ch{la:03d} {lw}",
            "right": f"ch{ra:03d} {rw}",
        }

    (args.out / "measurements.json").write_text(
        json.dumps(
            {
                "condition": args.condition,
                "seconds": args.seconds,
                "target_rms": TARGET_RMS,
                "within_chapter": internal,
                "between_chapter": boundary,
            },
            indent=2,
        )
    )
    (args.out / "blind_key.json").write_text(json.dumps(key, indent=2))
    print(f"\nwrote {len(plans)} blind clips to {args.out}")
    print("measurements.json is safe to read; blind_key.json is the answer")


if __name__ == "__main__":
    main()
