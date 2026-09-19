#!/usr/bin/env python3
"""Render a fixed passage through a palette of Qwen3-TTS VoiceDesign prompts.

Writes raw model output and a lightly mastered listening copy for each voice.
The raw copy makes every post-process auditable; the listening copy receives
only conservative full-scale click repair, level matching, and edge fades.
There are no joins because each passage is one generation.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))

from render_chapter_qwen3 import (  # noqa: E402
    SAMPLE_RATE,
    declick,
    match_level,
    soften_edges,
    suppress_onset_transient,
    trim_tail_artifact,
    verify_chunk,
)

MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--passage", type=Path, required=True)
    parser.add_argument("--voices", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--temperature", type=float, default=0.9)
    parser.add_argument("--top-k", type=int, default=50)
    parser.add_argument("--top-p", type=float, default=1.0)
    parser.add_argument("--repetition-penalty", type=float, default=1.1)
    parser.add_argument("--max-tokens", type=int, default=3000)
    parser.add_argument(
        "--verify-model", default="mlx-community/whisper-large-v3-turbo"
    )
    args = parser.parse_args()

    text = args.passage.read_text(encoding="utf-8").strip()
    voices = json.loads(args.voices.read_text(encoding="utf-8"))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    raw_dir = args.output_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)

    from mlx_audio.tts.utils import load_model
    import mlx.core as mx

    print(f"loading {args.model} once for {len(voices)} designed voices…", flush=True)
    model = load_model(args.model)
    reports = []

    for index, voice in enumerate(voices, start=1):
        seed = int(voice.get("seed", index))
        mx.random.seed(seed)
        np.random.seed(seed)
        print(
            f"=== [{index}/{len(voices)}] {voice['id']}: {voice['label']} "
            f"(seed {seed})",
            flush=True,
        )
        started = time.time()
        parts = []
        for result in model.generate(
            text=text,
            instruct=voice["instruction"],
            lang_code="English",
            temperature=args.temperature,
            top_k=args.top_k,
            top_p=args.top_p,
            repetition_penalty=args.repetition_penalty,
            max_tokens=args.max_tokens,
            split_pattern=None,
        ):
            parts.append(np.asarray(result.audio, dtype=np.float32).reshape(-1))
        if not parts:
            print("  NO AUDIO", flush=True)
            continue
        raw = np.concatenate(parts)
        raw_path = raw_dir / f"{index:02d}-{voice['id']}.wav"
        sf.write(str(raw_path), raw, SAMPLE_RATE)

        quality = verify_chunk(raw, text, model=args.verify_model, language="en")

        mastered, onset_ramp = suppress_onset_transient(raw)
        mastered, tail_cut = trim_tail_artifact(mastered)
        mastered, clicks = declick(mastered)
        raw_rms = float(np.sqrt((mastered.astype(np.float64) ** 2).mean()))
        mastered = soften_edges(match_level(mastered, -20.0), 25.0)
        output = args.output_dir / f"{index:02d}-{voice['id']}.wav"
        sf.write(str(output), mastered, SAMPLE_RATE)

        elapsed = time.time() - started
        report = {
            **voice,
            "seed": seed,
            "file": output.name,
            "raw_file": str(raw_path.relative_to(args.output_dir)),
            "seconds": round(mastered.size / SAMPLE_RATE, 3),
            "render_seconds": round(elapsed, 3),
            "realtime_factor": round(
                (mastered.size / SAMPLE_RATE) / max(elapsed, 1e-6), 3
            ),
            "raw_rms": round(raw_rms, 6),
            "onset_ramp_ms": round(onset_ramp * 1000, 1),
            "tail_trimmed_ms": round(tail_cut * 1000, 1),
            "clicks_repaired": clicks,
            "verification": {
                key: value
                for key, value in quality.items()
                if key != "transcript"
            },
            "transcript": quality["transcript"],
        }
        reports.append(report)
        print(
            f"  {report['seconds']:.1f}s audio in {elapsed:.1f}s "
            f"({report['realtime_factor']:.2f}x) · WER={quality['wer']:.3f} "
            f"cov={quality['coverage']:.3f} · gaps={quality['max_expected_gap']}/"
            f"{quality['max_added_span']} · clicks={clicks}",
            flush=True,
        )

    (args.output_dir / "report.json").write_text(json.dumps(reports, indent=2))
    print(f"\nwrote {len(reports)} auditions and report.json to {args.output_dir}")


if __name__ == "__main__":
    main()
