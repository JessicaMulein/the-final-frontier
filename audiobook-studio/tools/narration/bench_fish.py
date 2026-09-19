#!/usr/bin/env python3
"""Measure whether candidate generation is affordable on this machine.

The whole generate-many-and-judge approach rests on one number: what a candidate
costs in wall time relative to the audio it produces. If a candidate costs about
real time, eight candidates per unit turns an eight-minute chapter into roughly an
hour, and adaptive budgeting stops being an optimization and becomes a precondition.

So this measures three things and reports them plainly:

  1. real-time factor for a single `generate`, warm (excluding model load)
  2. real-time factor for `batch_generate` at N candidates, which is the number that
     actually decides the design, because batching is the only way several candidates
     cost less than several generations
  3. peak memory, to confirm an 8-bit 4B model plus codec and caches fits with room
     for a batch

It deliberately does not judge quality. Nothing here listens to the audio; it only
establishes the budget that later stages have to live inside.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import mlx.core as mx
import numpy as np
import soundfile as sf

SAMPLE_RATE = 24_000


from audio_io import load_reference


def summarise(label: str, seconds: float, audio_seconds: float, candidates: int) -> dict:
    per_candidate = seconds / max(1, candidates)
    rtf = seconds / audio_seconds if audio_seconds > 0 else float("nan")
    record = {
        "label": label,
        "candidates": candidates,
        "wall_seconds": round(seconds, 2),
        "audio_seconds_each": round(audio_seconds, 2),
        "wall_per_candidate": round(per_candidate, 2),
        "rtf_total": round(rtf, 3),
        "rtf_per_candidate": round(per_candidate / audio_seconds, 3)
        if audio_seconds > 0
        else None,
        "peak_memory_gb": round(float(mx.get_peak_memory() / 1e9), 2),
    }
    print(
        f"  {label:28s} {candidates:2d} cand  wall {seconds:7.1f}s  "
        f"audio {audio_seconds:5.1f}s  per-cand {per_candidate:6.1f}s  "
        f"RTF/cand {record['rtf_per_candidate']}  peak {record['peak_memory_gb']}GB",
        flush=True,
    )
    return record


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    # The checkpoint the implementation is written against, per
    # mlx_audio/tts/models/fish_qwen3_omni/README.md. A community 8-bit
    # conversion was tried first and failed to load: 358 missing parameters
    # including codebook_embeddings.weight, embeddings.weight and every
    # layers.N.*, because its key layout does not match what sanitize() and
    # load_weights() expect. Quantizing is a later optimization, not a
    # prerequisite; 4B at bf16 is comfortable in 64 GB.
    p.add_argument("--model", default="mlx-community/fish-audio-s2-pro")
    p.add_argument(
        "--ref-audio",
        type=Path,
        default=Path(
            "../../../audiobook-studio/assets/voice-refs/common-voice-refs/"
            "uk-southern-female-03-tight.wav"
        ),
    )
    p.add_argument(
        "--ref-text",
        default="The band enjoyed much regional and some national success, "
        "and released three albums.",
        help="transcript of the reference clip; conditions the clone far better "
        "than audio alone",
    )
    p.add_argument(
        "--instruct",
        default="Read slowly, clearly, and naturally. Maintain a measured "
        "literary pace without sounding like an announcer.",
    )
    p.add_argument("--batch", type=int, action="append", default=None)
    p.add_argument("--report", type=Path, default=Path("out/bench-fish.json"))
    args = p.parse_args()

    batches = args.batch or [4, 8]
    ref = args.ref_audio.resolve()
    if not ref.is_file():
        raise SystemExit(f"reference audio not found: {ref}")

    # One paragraph of the real manuscript, so the measurement reflects the
    # prose that will actually be rendered rather than a short benchmark phrase.
    text = (
        "The matched load was a brass slug the size of my thumb with a fifty-ohm "
        "resistor buried in it, and it had spent two nights in a cold cabinet, so "
        "the first thing I did on the eleventh of December was close my hand around "
        "it until it came up to room temperature."
    )

    from mlx_audio.tts.utils import load_model

    print(f"loading {args.model}", flush=True)
    load_start = time.perf_counter()
    # load_model already invokes Model.post_load_hook(model, model_path), which is
    # what attaches the tokenizer and the codec. Calling it again here is wrong.
    model = load_model(args.model)
    load_seconds = time.perf_counter() - load_start
    print(f"  loaded in {load_seconds:.1f}s", flush=True)

    # Must be an mx.array at the model's rate. The model README documents passing a
    # path, but `_prepare_reference_prompt` calls `audio.ndim`, so a str raises.
    ref_audio = load_reference(ref, int(getattr(model, "sample_rate", 44100)))
    results = {
        "model": args.model,
        "load_seconds": round(load_seconds, 2),
        "reference": str(ref),
        "words": len(text.split()),
        "runs": [],
    }

    common = dict(
        ref_audio=ref_audio,
        ref_text=args.ref_text,
        instruct=args.instruct,
        temperature=0.7,
        top_p=0.7,
        top_k=30,
        verbose=False,
    )

    print("\nsingle generate (warm-up pass first, not timed)", flush=True)
    for segment in model.generate(text=text, **common):
        _ = segment.audio
        break

    mx.reset_peak_memory()
    start = time.perf_counter()
    audio_seconds = 0.0
    for segment in model.generate(text=text, **common):
        audio_seconds += int(segment.samples) / float(segment.sample_rate)
    results["runs"].append(
        summarise("generate", time.perf_counter() - start, audio_seconds, 1)
    )

    if not hasattr(model, "batch_generate"):
        print("\n  model has no batch_generate; candidates would cost N generations")
    else:
        print("\nbatch_generate", flush=True)
        for n in batches:
            mx.reset_peak_memory()
            start = time.perf_counter()
            per_sequence: dict[int, float] = {}
            for result in model.batch_generate(
                texts=[text] * n,
                ref_audios=[ref_audio] * n,
                ref_texts=[args.ref_text] * n,
                instructs=[args.instruct] * n,
                temperature=0.7,
                top_p=0.7,
                top_k=30,
                verbose=False,
            ):
                index = int(getattr(result, "sequence_idx", 0))
                per_sequence[index] = per_sequence.get(index, 0.0) + int(
                    result.samples
                ) / float(result.sample_rate)
            elapsed = time.perf_counter() - start
            mean_audio = (
                sum(per_sequence.values()) / len(per_sequence) if per_sequence else 0.0
            )
            results["runs"].append(
                summarise(f"batch_generate x{n}", elapsed, mean_audio, n)
            )

    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(results, indent=2))

    single = next((r for r in results["runs"] if r["label"] == "generate"), None)
    batched = [r for r in results["runs"] if r["label"].startswith("batch")]
    if single and batched:
        best = min(batched, key=lambda r: r["wall_per_candidate"])
        speedup = single["wall_per_candidate"] / max(1e-9, best["wall_per_candidate"])
        print(
            f"\nbatching gives {speedup:.2f}x per candidate at "
            f"{best['candidates']} candidates"
        )
        print(
            "adaptive budgeting is "
            + (
                "an optimization"
                if best["rtf_per_candidate"] and best["rtf_per_candidate"] < 0.35
                else "a precondition"
            )
        )
    print(f"wrote {args.report}")


if __name__ == "__main__":
    main()
