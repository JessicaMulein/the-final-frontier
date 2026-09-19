#!/usr/bin/env python3
"""Does a deterministic discarded lead-in stabilise Fish's voice between chapters?

The failure under test
----------------------
Each chapter is an independent zero-shot clone. The same reference keeps it broadly
"the same speaker", but stochastic generation moves the baseline register: measured
chapter transitions shift median F0 by up to +/-11.5 Hz, and the listener hears the
voice go deeper, then higher, then back.

Three conditions, with the engine, voice, direction and chapter text held constant:

  existing   the already-rendered stochastic production excerpt
  fixed      reset MLX to the same seed before each chapter
  anchored   same seed, but generate one identical lead-in first, retain its audio
             tokens in Fish's running Conversation, and discard only its whole
             yielded segment from the delivered waveform

This is NOT QVoice's dangerous warm-up technique. There is no ASR boundary search,
no cut inside a waveform and no possibility of deleting a chapter's first word. The
anchor is an entire Fish turn and an entire yielded segment. Its codes stay in
conversation context; its waveform does not ship.

A critical invariant is checked rather than assumed: the discarded anchor waveform
must be byte-identical across chapters. If its hash changes, the model did not start
from one deterministic voice state and the experiment is invalid.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import time
from itertools import combinations
from pathlib import Path

import mlx.core as mx
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

from audio_io import load_reference
from diagnose_voice import fingerprint, robust_distance
from manuscript import paragraphs, sentences, spoken_text
from prosody import pitch_stats
from render_chapter_fish import ANCHOR, INTERIOR, active_rms

REPO = Path(__file__).resolve().parents[3]
CHAPTER_ROOT = REPO / "The Final Frontier Novel/chapters"
HIFI = Path("out/hifitts-refs")

# ANCHOR now lives in render_chapter_fish so the experiment and the renderer cannot
# drift apart: a different anchor is a different voice state, which would silently
# invalidate any comparison between this experiment and a production render.
CHUNK_LENGTH = 300
assert len(ANCHOR.encode("utf-8")) > CHUNK_LENGTH


def chapter_path(number: int) -> Path:
    matches = list(CHAPTER_ROOT.glob(f"*/*-{number:03d}-*.md"))
    if len(matches) != 1:
        raise SystemExit(f"chapter {number}: expected one file, found {matches}")
    return matches[0]


def pause_between_sentences(paragraph: str) -> str:
    parts = sentences(paragraph)
    if len(parts) < 2:
        return paragraph
    return parts[0] + " " + " ".join(f"[short pause] {s}" for s in parts[1:])


def excerpt(number: int, target_words: int) -> tuple[str, str]:
    text = spoken_text(chapter_path(number))
    chosen, words = [], 0
    for paragraph in paragraphs(text):
        prepared = pause_between_sentences(paragraph)
        chosen.append(prepared)
        words += len(paragraph.split())
        if words >= target_words:
            break
    tagged = "\n".join(f"<|speaker:0|>{p}" for p in chosen)
    return tagged, "\n\n".join(chosen)


def render(model, text: str, ref, ref_text: str, seed: int, anchored: bool):
    mx.random.seed(seed)
    payload = (
        f"<|speaker:0|>{ANCHOR}\n{text}"
        if anchored
        else text
    )
    pieces = []
    started = time.perf_counter()
    for result in model.generate(
        text=payload,
        ref_audio=ref,
        ref_text=ref_text,
        instruct=INTERIOR,
        chunk_length=CHUNK_LENGTH,
        max_tokens=1024,
        temperature=0.7,
        top_p=0.7,
        top_k=30,
        verbose=False,
    ):
        pieces.append(np.asarray(result.audio, dtype=np.float32))
    wall = time.perf_counter() - started
    if not pieces:
        raise RuntimeError("no audio generated")
    if anchored and len(pieces) < 2:
        raise RuntimeError(
            f"anchor was not isolated: only {len(pieces)} segment(s); "
            f"anchor bytes={len(ANCHOR.encode())}, chunk_length={CHUNK_LENGTH}"
        )
    anchor = pieces[0] if anchored else None
    delivered = np.concatenate(pieces[1:] if anchored else pieces)
    mx.clear_cache()
    return delivered, anchor, wall, len(pieces)


def metrics(audio: np.ndarray, rate: int) -> dict:
    a16 = resample_poly(audio, 160, 441).astype(np.float32) if rate == 44100 else audio
    fp = fingerprint(a16, 16000 if rate == 44100 else rate)
    a24 = resample_poly(audio, 80, 147).astype(np.float32) if rate == 44100 else audio
    median_f0, _, span = pitch_stats(a24)
    return {
        "median_f0": round(median_f0, 2),
        "pitch_span": round(span, 2),
        "active_rms": round(active_rms(audio, rate), 6),
        "fingerprint": fp,
    }


def serialise_metrics(value: dict) -> dict:
    return {
        "median_f0": value["median_f0"],
        "pitch_span": value["pitch_span"],
        "active_rms": value["active_rms"],
        "mfcc": [round(float(x), 6) for x in value["fingerprint"]["mfcc"]],
        "spread": [round(float(x), 6) for x in value["fingerprint"]["spread"]],
    }


def load_existing(number: int, seconds: float) -> tuple[np.ndarray, int]:
    matches = list(Path("out/book").glob(f"*-chapter-{number:03d}-fish-clean92.wav"))
    if len(matches) != 1:
        raise SystemExit(f"existing chapter {number} not found")
    audio, rate = sf.read(str(matches[0]), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return audio[: int(seconds * rate)], int(rate)


def pair_summary(chapters: list[int], values: dict[int, dict]) -> dict:
    f0 = [values[ch]["median_f0"] for ch in chapters]
    distances = [
        robust_distance(values[a]["fingerprint"], values[b]["fingerprint"])
        for a, b in combinations(chapters, 2)
    ]
    return {
        "f0_min": round(min(f0), 2),
        "f0_max": round(max(f0), 2),
        "f0_range_hz": round(max(f0) - min(f0), 2),
        "f0_std_hz": round(float(np.std(f0)), 2),
        "mean_pairwise_timbre_distance": round(float(np.mean(distances)), 3),
        "max_pairwise_timbre_distance": round(max(distances), 3),
    }


def write_transition(
    path: Path,
    left: np.ndarray,
    right: np.ndarray,
    rate: int,
    seconds: float = 12.0,
):
    """Level-match both sides; register, not loudness, is the variable."""
    target = min(active_rms(left, rate), active_rms(right, rate))
    def match(audio):
        level = active_rms(audio, rate)
        return audio * (target / level) if level > 0 else audio
    span = int(seconds * rate)
    clip = np.concatenate(
        [match(left)[-span:], np.zeros(int(rate * 0.5), dtype=np.float32), match(right)[:span]]
    )
    sf.write(str(path), clip, rate, subtype="PCM_16")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--chapters", type=int, nargs="+", default=[1, 2, 11, 12])
    p.add_argument("--words", type=int, default=180)
    p.add_argument("--seed", type=int, default=70)
    p.add_argument("--model", default="mlx-community/fish-audio-s2-pro")
    p.add_argument("--reference", default="hifitts-clean-92")
    p.add_argument("--out", type=Path, default=Path("out/anchor-experiment"))
    args = p.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    ref_wav = HIFI / f"{args.reference}.wav"
    ref_text = (HIFI / f"{args.reference}.txt").read_text().strip()

    from mlx_audio.tts.utils import load_model
    print(f"loading {args.model}")
    model = load_model(args.model)
    rate = int(getattr(model, "sample_rate", 44100))
    ref = load_reference(ref_wav, rate)

    audio: dict[str, dict[int, np.ndarray]] = {
        "existing": {}, "fixed": {}, "anchored": {}
    }
    measured: dict[str, dict[int, dict]] = {
        "existing": {}, "fixed": {}, "anchored": {}
    }
    anchor_hashes = {}
    records = []

    for number in args.chapters:
        text, _ = excerpt(number, args.words)
        print(f"\nchapter {number}: {len(re.sub(r'<[^>]+>|\[[^]]+\]', '', text).split())} words")
        for condition, anchored in (("fixed", False), ("anchored", True)):
            delivered, anchor, wall, segments = render(
                model, text, ref, ref_text, args.seed, anchored
            )
            path = args.out / f"ch{number:03d}-{condition}.wav"
            sf.write(str(path), delivered, rate, subtype="PCM_16")
            audio[condition][number] = delivered
            measured[condition][number] = metrics(delivered, rate)
            anchor_hash = None
            if anchor is not None:
                anchor_hash = hashlib.sha256(anchor.tobytes()).hexdigest()
                anchor_hashes[number] = anchor_hash
                sf.write(
                    str(args.out / f"ch{number:03d}-discarded-anchor.wav"),
                    anchor,
                    rate,
                    subtype="PCM_16",
                )
            records.append(
                {
                    "chapter": number,
                    "condition": condition,
                    "seconds": round(delivered.size / rate, 2),
                    "wall_seconds": round(wall, 1),
                    "segments": segments,
                    "anchor_sha256": anchor_hash,
                    "metrics": serialise_metrics(measured[condition][number]),
                }
            )
            print(
                f"  {condition:8s} {delivered.size / rate:5.1f}s, "
                f"F0 {measured[condition][number]['median_f0']:6.1f}Hz, "
                f"{wall:5.1f}s wall, {segments} segment(s)"
            )

        seconds = min(
            audio["fixed"][number].size, audio["anchored"][number].size
        ) / rate
        existing, existing_rate = load_existing(number, seconds)
        if existing_rate != rate:
            existing = resample_poly(existing, rate, existing_rate).astype(np.float32)
        audio["existing"][number] = existing
        measured["existing"][number] = metrics(existing, rate)

    unique_anchors = set(anchor_hashes.values())
    identical = len(unique_anchors) == 1
    print(f"\nanchor hashes identical: {identical} ({len(unique_anchors)} unique)")
    if not identical:
        raise SystemExit("experiment invalid: deterministic anchor changed across chapters")

    summary = {
        condition: pair_summary(args.chapters, values)
        for condition, values in measured.items()
    }
    print("\ncondition    F0 range  F0 std  mean timbre  max timbre")
    for condition in ("existing", "fixed", "anchored"):
        s = summary[condition]
        print(
            f"{condition:10s} {s['f0_range_hz']:8.2f} {s['f0_std_hz']:7.2f} "
            f"{s['mean_pairwise_timbre_distance']:12.3f} "
            f"{s['max_pairwise_timbre_distance']:11.3f}"
        )

    # Blind transitions for the two chapter pairs that originally moved most.
    conditions = ["existing", "fixed", "anchored"]
    rng = random.Random(238)
    key = {}
    for left, right in ((1, 2), (11, 12)):
        order = conditions.copy()
        rng.shuffle(order)
        for label, condition in zip("ABC", order):
            filename = f"pair-{left:03d}-{right:03d}-{label}.wav"
            write_transition(
                args.out / filename,
                audio[condition][left],
                audio[condition][right],
                rate,
            )
            key[f"{left:03d}-{right:03d}-{label}"] = condition

    (args.out / "report.json").write_text(
        json.dumps(
            {
                "chapters": args.chapters,
                "seed": args.seed,
                "anchor": ANCHOR,
                "anchor_bytes": len(ANCHOR.encode()),
                "anchor_hashes_identical": identical,
                "anchor_sha256": next(iter(unique_anchors)),
                "summary": summary,
                "records": records,
                "blind_key": key,
            },
            indent=2,
        )
    )
    print(f"\nwrote experiment and blind transition clips to {args.out}")
    print("listen before opening report.json")


if __name__ == "__main__":
    main()
