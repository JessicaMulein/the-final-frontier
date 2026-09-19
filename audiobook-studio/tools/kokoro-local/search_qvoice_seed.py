#!/usr/bin/env python3
"""Search deterministic pure-C Qwen CustomVoice seeds until structural QA passes."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf

from render_chapter_qwen3 import verify_chunk


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--binary", type=Path, required=True)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--voice", type=Path, required=True)
    p.add_argument("--text-file", type=Path, required=True)
    p.add_argument("--instruction", required=True)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--start-seed", type=int, default=50)
    p.add_argument("--attempts", type=int, default=8)
    p.add_argument("--rate", type=float, default=0.92)
    p.add_argument("--verify-model", default="mlx-community/whisper-large-v3-turbo")
    args = p.parse_args()

    text = args.text_file.resolve().read_text(encoding="utf-8").strip()
    args.binary = args.binary.resolve()
    args.model = args.model.resolve()
    args.voice = args.voice.resolve()
    args.output = args.output.resolve()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["QWEN_METAL_FUSED_TALKER"] = "1"
    env.pop("QWEN_METAL_BATCH_MMA", None)
    attempts = []

    for seed in range(args.start_seed, args.start_seed + args.attempts):
        candidate = args.output.with_name(f"{args.output.stem}-seed{seed}.wav")
        log = candidate.with_suffix(".log")
        cmd = [
            str(args.binary), "--backend", "metal", "-d", str(args.model),
            "--load-voice", str(args.voice), "--icl-only", "-l", "English",
            "--seed", str(seed), "--temperature", "0.5", "--top-k", "50",
            "--top-p", "1.0", "--rep-penalty", "1.05", "--max-tokens", "1800",
            "--rate", str(args.rate), "--instruct", args.instruction,
            "--text", text, "-o", str(candidate),
        ]
        with log.open("w") as fh:
            result = subprocess.run(
                cmd, cwd=args.binary.parent, env=env, text=True,
                stdout=fh, stderr=subprocess.STDOUT,
            )
        record = {"seed": seed, "runtime_exit": result.returncode}
        if result.returncode == 0 and candidate.is_file():
            audio, sr = sf.read(str(candidate), always_2d=False)
            audio = np.asarray(audio, dtype=np.float32)
            if audio.ndim > 1:
                audio = audio.mean(axis=1)
            quality = verify_chunk(
                audio, text, model=args.verify_model, language="en"
            )
            record.update(
                {
                    "seconds": round(audio.size / sr, 3),
                    **{k: v for k, v in quality.items() if k != "transcript"},
                }
            )
            print(
                f"seed {seed}: {record['seconds']:.1f}s "
                f"wer={quality['wer']:.3f} cov={quality['coverage']:.3f} "
                f"gap={quality['max_expected_gap']} pass={quality['passed']}",
                flush=True,
            )
            if quality["passed"]:
                candidate.replace(args.output)
                record["selected"] = True
                attempts.append(record)
                args.output.with_suffix(".search.json").write_text(
                    json.dumps(attempts, indent=2)
                )
                print(f"selected seed {seed} -> {args.output}")
                return
        attempts.append(record)

    args.output.with_suffix(".search.json").write_text(json.dumps(attempts, indent=2))
    raise SystemExit(f"No passing seed in {args.attempts} attempts")


if __name__ == "__main__":
    main()
