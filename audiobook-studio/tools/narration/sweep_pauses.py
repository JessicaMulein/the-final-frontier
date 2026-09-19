#!/usr/bin/env python3
"""Isolate what fixes "it rambles": gaps, inline pause tags, or sentence turns.

The listener's verdict on the stamina render was specific: perfectly clear, but it
rambles and wants more natural pauses between sentences. Three separate levers could
produce that, and they should not be changed together:

  PARAGRAPH GAP    room tone between paragraphs at assembly. The first Fish render
                   had none at all -- a bare concatenate -- which is almost certainly
                   the dominant cause. QVoice used 650 ms of shaped tone.
  INLINE TAGS      Fish's documented `[pause]` / `[short pause]`, inside a paragraph,
                   where a gap at assembly cannot reach.
  SENTENCE TURNS   each sentence as its own generation, so every sentence boundary
                   becomes an assembly-level gap. Most control, most cold starts.

Run on a short excerpt so iteration costs a minute, not eight.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import mlx.core as mx
import numpy as np
import soundfile as sf



from audio_io import load_reference  # noqa: E402
from manuscript import spoken_text

from render_chapter_fish import (  # noqa: E402
    INTERIOR,
    _pause_between_sentences,
    _sentences,
    active_rms,
    comfort_gap,
    flatten_slope,
    match_levels,
)

REPO = Path(__file__).resolve().parents[3]
HIFI = Path("out/hifitts-refs")

# (name, paragraph_gap_ms, pause tag or None, sentence_turns)
VARIANTS = [
    ("v0_as_shipped_no_gap", 0.0, None, False),
    ("v1_gap650", 650.0, None, False),
    ("v2_gap650_short_pause", 650.0, "[short pause]", False),
    ("v3_gap900_pause", 900.0, "[pause]", False),
    ("v4_sentence_turns_gap350", 350.0, None, True),
]


def build_text(paragraphs: list[str], tag: str | None, sentence_turns: bool) -> str:
    prepared = [
        _pause_between_sentences(p, tag) if tag else p for p in paragraphs
    ]
    units = (
        [s for p in prepared for s in _sentences(p)] if sentence_turns else prepared
    )
    return "\n".join(f"<|speaker:0|>{u}" for u in units)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="mlx-community/fish-audio-s2-pro")
    p.add_argument("--reference", default="hifitts-clean-92")
    p.add_argument(
        "--chapter",
        type=Path,
        default=REPO
        / "The Final Frontier Novel/chapters/discovery-part/discovery-part-003-the-failed-check.md",
    )
    p.add_argument("--paragraphs", type=int, default=4, help="excerpt length")
    p.add_argument("--out", type=Path, default=Path("out/sweep-pauses"))
    args = p.parse_args()

    spoken = normalize(extract_body(args.chapter))
    paragraphs = [x.strip() for x in spoken.split("\n\n") if x.strip()][
        : args.paragraphs
    ]
    words = sum(len(x.split()) for x in paragraphs)
    print(f"excerpt: {len(paragraphs)} paragraphs, {words} words")

    ref_wav = HIFI / f"{args.reference}.wav"
    ref_text = (HIFI / f"{args.reference}.txt").read_text().strip()

    from mlx_audio.tts.utils import load_model

    print(f"loading {args.model}")
    model = load_model(args.model)
    rate = int(getattr(model, "sample_rate", 44100))
    reference = load_reference(ref_wav, rate)

    args.out.mkdir(parents=True, exist_ok=True)
    labels = "ABCDEFGH"
    key, report = {}, []

    print("\n  label  variant                    secs   gaps  wall")
    for label, (name, gap_ms, tag, sentence_turns) in zip(labels, VARIANTS):
        text = build_text(paragraphs, tag, sentence_turns)
        started = time.perf_counter()
        segments = [
            np.asarray(segment.audio, dtype=np.float32)
            for segment in model.generate(
                text=text,
                ref_audio=reference,
                ref_text=ref_text,
                instruct=INTERIOR,
                chunk_length=300,
                max_tokens=1024,
                temperature=0.7,
                top_p=0.7,
                top_k=30,
                verbose=False,
            )
        ]
        elapsed = time.perf_counter() - started
        if not segments:
            print(f"  {label}      {name:24s}  (no audio)")
            continue

        segments = [flatten_slope(s, rate)[0] for s in segments]
        levelled, _, _ = match_levels(segments, rate)
        gap_samples = int(rate * gap_ms / 1000)
        pieces: list[np.ndarray] = []
        for index, segment in enumerate(levelled):
            pieces.append(segment)
            if index < len(levelled) - 1 and gap_samples > 0:
                pieces.append(
                    comfort_gap(levelled, gap_samples, rate, seed=1000 + index)
                )
        joined = np.concatenate(pieces)
        peak = float(np.abs(joined).max())
        if peak > 0.99:
            joined *= 0.99 / peak

        sf.write(
            str(args.out / f"take-{label}.wav"), joined, rate, subtype="PCM_16"
        )
        key[label] = name
        report.append(
            {
                "label": label,
                "variant": name,
                "paragraph_gap_ms": gap_ms,
                "pause_tag": tag,
                "sentence_turns": sentence_turns,
                "segments": len(levelled),
                "seconds": round(joined.size / rate, 2),
                "wall_seconds": round(elapsed, 1),
            }
        )
        print(
            f"  {label}      {name:24s} {joined.size / rate:6.1f} "
            f"{len(levelled):5d} {elapsed:6.1f}s"
        )
        mx.clear_cache()

    (args.out / "blind-key.json").write_text(
        json.dumps({"key": key, "variants": report}, indent=2)
    )
    print(f"\nwrote {args.out}/take-*.wav and blind-key.json")
    print("A is the current behaviour; listen for pacing, not clarity")


if __name__ == "__main__":
    main()
