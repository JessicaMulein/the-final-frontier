#!/usr/bin/env python3
"""Prove MLX is actually computing on the GPU, then generate once.

Written because four earlier attempts died before inference and the only evidence
of "is this running" was whether the fans spun up. Fan noise is not a measurement.
This reports the MLX device, the Metal device info, and GPU buffer memory before
and after a real generation, so "did it use the GPU" has a numeric answer.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import mlx.core as mx


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="mlx-community/fish-audio-s2-pro")
    p.add_argument(
        "--ref-audio",
        type=Path,
        default=Path(
            "../../../.audiobook/assets/voice-refs/common-voice-refs/"
            "uk-southern-female-03-tight.wav"
        ),
    )
    p.add_argument(
        "--ref-text",
        default="The band enjoyed much regional and some national success, "
        "and released three albums.",
    )
    p.add_argument("--out", type=Path, default=Path("out/gpu-check.wav"))
    args = p.parse_args()

    print("=== MLX device")
    print("  default_device:", mx.default_device())
    try:
        info = mx.metal.device_info()
        for key in (
            "device_name",
            "architecture",
            "max_recommended_working_set_size",
            "memory_size",
        ):
            if key in info:
                value = info[key]
                if isinstance(value, int) and value > 1 << 20:
                    print(f"  {key}: {value / 1e9:.1f} GB")
                else:
                    print(f"  {key}: {value}")
    except Exception as error:  # noqa: BLE001
        print("  metal.device_info unavailable:", error)

    # A trivial GPU op, to separate "MLX can reach the GPU" from "the model loads".
    mx.reset_peak_memory()
    probe = (mx.random.normal((4096, 4096)) @ mx.random.normal((4096, 4096))).sum()
    mx.eval(probe)
    print(f"  probe matmul ok, peak GPU memory {mx.get_peak_memory() / 1e9:.2f} GB")

    ref = args.ref_audio.resolve()
    if not ref.is_file():
        raise SystemExit(f"reference audio not found: {ref}")

    from mlx_audio.tts.utils import load_model

    print(f"\n=== loading {args.model}")
    start = time.perf_counter()
    model = load_model(args.model)
    print(f"  loaded in {time.perf_counter() - start:.1f}s")
    print(f"  peak GPU memory after load {mx.get_peak_memory() / 1e9:.2f} GB")
    model_rate = int(getattr(model, "sample_rate", 44100))
    print(f"  sample_rate {model_rate}")

    from audio_io import load_reference, reference_seconds

    print(
        f"  reference {ref.name}: {reference_seconds(ref):.2f}s, "
        f"resampled to {model_rate} Hz"
    )
    ref_array = load_reference(ref, model_rate)

    text = (
        "The matched load was a brass slug the size of my thumb with a fifty-ohm "
        "resistor buried in it."
    )
    print("\n=== generating")
    mx.reset_peak_memory()
    start = time.perf_counter()
    segments = list(
        model.generate(
            text=text,
            ref_audio=ref_array,
            ref_text=args.ref_text,
            instruct="Read slowly, clearly, and naturally.",
            temperature=0.7,
            top_p=0.7,
            top_k=30,
            verbose=False,
        )
    )
    elapsed = time.perf_counter() - start

    total_samples = sum(int(s.samples) for s in segments)
    rate = int(segments[0].sample_rate)
    seconds = total_samples / rate
    print(f"  segments {len(segments)}")
    print(f"  audio {seconds:.2f}s at {rate} Hz")
    print(f"  wall {elapsed:.1f}s  RTF {elapsed / max(seconds, 1e-9):.2f}")
    print(f"  peak GPU memory during generation {mx.get_peak_memory() / 1e9:.2f} GB")

    import numpy as np
    import soundfile as sf

    audio = np.concatenate([np.asarray(s.audio, dtype=np.float32) for s in segments])
    args.out.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(args.out), audio, rate, subtype="PCM_16")
    print(f"  wrote {args.out} (peak {float(np.abs(audio).max()):.3f})")


if __name__ == "__main__":
    main()
