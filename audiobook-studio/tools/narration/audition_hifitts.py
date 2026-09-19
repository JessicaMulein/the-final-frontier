#!/usr/bin/env python3
"""Blind audition: Hi-Fi TTS narrator candidates against the incumbent choices.

Renders sequentially rather than batched. A four-way batch of this passage peaked
at 62.4 GB against a 55.7 GB recommended working set; it completed, but the book
pipeline should cap batch size by unit length, and an audition is not where to
gamble on that.

Candidates are the female Hi-Fi TTS speakers that scored best on range and noise,
plus the studio clip the listener picked (1.4 s of speech, the thinness this whole
exercise is meant to fix) and the current QVoice render as an unlabeled control.

Gender came from median F0, not metadata: the dataset parquet carries no gender
column, and the highest-range candidate overall turned out to be male.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import mlx.core as mx
import numpy as np
import soundfile as sf

from audio_io import load_reference
from audition_ab import active_rms, normalise, prosody

REPO = Path(__file__).resolve().parents[3]
COMMON = REPO / "audiobook-studio/assets/voice-refs/common-voice-refs"
HIFI = Path("out/hifitts-refs")

INTERIOR = (
    "Read as a first-person memoir: dry, precise, quietly unsettled. Let meaning "
    "land through timing and emphasis rather than volume. Never announce."
)


def candidates() -> list[tuple[str, Path, str]]:
    """(name, audio, transcript) triples. Transcripts must match the audio."""
    out: list[tuple[str, Path, str]] = []
    for speaker in ("other-11614", "clean-92", "other-12787"):
        wav = HIFI / f"hifitts-{speaker}.wav"
        txt = HIFI / f"hifitts-{speaker}.txt"
        if wav.is_file() and txt.is_file():
            out.append((f"hifitts_{speaker.replace('-', '_')}", wav, txt.read_text().strip()))
    # The listener's pick from the studio clips, for direct comparison.
    out.append(
        (
            "uks02_listener_pick",
            COMMON / "uk-southern-female-02.wav",
            "Making a phone call to Courtney.",
        )
    )
    return out


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="mlx-community/fish-audio-s2-pro")
    p.add_argument(
        "--qvoice-review",
        type=Path,
        default=REPO / "audiobook/qvoice-production/review/chapter3-v2",
    )
    p.add_argument("--unit", type=int, default=8)
    p.add_argument("--out", type=Path, default=Path("out/audition-hifitts"))
    args = p.parse_args()

    manifest = json.loads((args.qvoice_review / "work/manifest.json").read_text())
    chunk = manifest["chunks"][args.unit - 1]
    text = chunk["text"]
    print(f"unit {args.unit}: {len(text.split())} words")

    control_path = args.qvoice_review / Path(manifest["output"]).name
    control_audio, control_rate = sf.read(str(control_path), always_2d=False)
    control_audio = np.asarray(control_audio, dtype=np.float32)
    if control_audio.ndim > 1:
        control_audio = control_audio.mean(axis=1)
    control = control_audio[
        int(chunk["start_seconds"] * control_rate) : int(
            chunk["end_seconds"] * control_rate
        )
    ].copy()

    picks = candidates()
    if not picks:
        raise SystemExit("no candidate references found; run hifitts_refs.py first")

    from mlx_audio.tts.utils import load_model

    print(f"loading {args.model}")
    model = load_model(args.model)
    rate = int(getattr(model, "sample_rate", 44100))

    renders = []
    for name, wav, ref_text in picks:
        print(f"  rendering {name} (ref {ref_text[:50]}...)", flush=True)
        start = time.perf_counter()
        pieces = [
            np.asarray(segment.audio, dtype=np.float32)
            for segment in model.generate(
                text=text,
                ref_audio=load_reference(wav, rate),
                ref_text=ref_text,
                instruct=INTERIOR,
                temperature=0.7,
                top_p=0.7,
                top_k=30,
                verbose=False,
            )
        ]
        audio = np.concatenate(pieces)
        print(
            f"    {time.perf_counter() - start:.1f}s wall, "
            f"{audio.size / rate:.1f}s audio, peak {mx.get_peak_memory() / 1e9:.1f} GB"
        )
        renders.append((name, audio, rate))
        mx.clear_cache()

    target = active_rms(control, control_rate)
    args.out.mkdir(parents=True, exist_ok=True)
    entries = [("qvoice_control", control, control_rate)] + renders

    labels = "ABCDEFGH"
    key, report = {}, []
    print("\n  label  condition                  secs    wps   span    dyn")
    for label, (name, audio, audio_rate) in zip(labels, entries):
        levelled = normalise(audio, audio_rate, target)
        sf.write(
            str(args.out / f"voice-{label}.wav"), levelled, audio_rate, subtype="PCM_16"
        )
        metrics = prosody(levelled, audio_rate)
        seconds = levelled.size / audio_rate
        key[label] = name
        report.append(
            {"label": label, "condition": name, "seconds": round(seconds, 1), **metrics}
        )
        print(
            f"  {label}      {name:25s} {seconds:5.1f}  "
            f"{len(text.split()) / seconds:5.2f}  "
            f"{metrics['pitch_span_semitones']:6.2f} {metrics['dynamic_range_db']:6.1f}"
        )

    (args.out / "blind-key.json").write_text(
        json.dumps({"key": key, "unit": args.unit, "text": text, "metrics": report}, indent=2)
    )
    print(f"\nwrote {args.out}/voice-*.wav and blind-key.json")
    print("judge accent, clarity, then range; these are LibriVox readers so accent varies")


if __name__ == "__main__":
    main()
