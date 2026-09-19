#!/usr/bin/env python3
"""How much delivery range can direction alone buy, holding identity fixed?

The listener settled the identity question: uk-s03 over EMNS, for clarity. The
measurements support the reason — EMNS carries more high-frequency energy but it
reads as noise, not detail, and this project has already rejected EMNS grafts for
background EQ and failed to denoise them without spectral damage.

So the reference is fixed at uk-s03 and only the direction varies. This answers a
cheap question before an expensive one: if instruct and inline tags can widen the
delivery on a clean reference, no port is needed. If they cannot, the flat affect
is a property of the reference, and separating timbre from style (IndexTTS2) is the
structural fix rather than a speculative one.

Prosody numbers are reported but explicitly not used to rank. Pitch span and
dynamic range already anti-predicted this listener's choice once: the take they
preferred scored lowest on both. They are recorded to characterise conditions, not
to pick a winner.
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
from audition_ab import REFS, active_rms, normalise, prosody

# Fixed: the identity the listener chose.
REFERENCE = "uk_s03"

DIRECTIONS: list[tuple[str, str, bool]] = [
    (
        "baseline_restrained",
        "Read slowly, clearly, and naturally. Maintain a measured literary pace "
        "without sounding like an announcer.",
        False,
    ),
    (
        "interior",
        "Read as a first-person memoir: dry, precise, quietly unsettled. Let "
        "meaning land through timing and emphasis rather than volume. Never "
        "announce.",
        False,
    ),
    (
        "interior_slower",
        "Read as a first-person memoir, unhurried and deliberate: dry, precise, "
        "quietly unsettled. Leave room after each sentence. Let meaning land "
        "through timing and emphasis rather than volume. Never announce.",
        False,
    ),
    (
        "engineer_testimony",
        "Read like a careful engineer giving testimony about something that "
        "frightened her. Factual on the surface, with the tension underneath. "
        "Vary the phrasing so it never becomes a list. Do not perform.",
        False,
    ),
    (
        "interior_tagged",
        "Read as a first-person memoir: dry, precise, quietly unsettled. Let "
        "meaning land through timing and emphasis rather than volume.",
        True,
    ),
    (
        "audiobook_professional",
        "Narrate as a professional audiobook reader for literary fiction: warm, "
        "intelligent, unhurried, with natural variation in pitch and pace between "
        "sentences. Avoid a flat, even delivery.",
        True,
    ),
]


def add_tags(text: str) -> str:
    """Sparse inline tags at sentence boundaries.

    Tags live in the spoken transform only; the manuscript is never touched. Kept
    deliberately thin because this novel needs restrained implication, and the
    obvious failure mode of a tag vocabulary is overacting.
    """
    import re

    sentences = [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]
    out = []
    for index, sentence in enumerate(sentences):
        if index and index % 2 == 0:
            out.append("[short pause] " + sentence)
        else:
            out.append(sentence)
    return " ".join(out)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="mlx-community/fish-audio-s2-pro")
    p.add_argument(
        "--qvoice-review",
        type=Path,
        default=Path(__file__).resolve().parents[3]
        / "audiobook/qvoice-production/review/chapter3-v2",
    )
    p.add_argument(
        "--unit",
        type=int,
        default=4,
        help="unit index; default picks a passage containing dialogue",
    )
    p.add_argument("--out", type=Path, default=Path("out/sweep-instruct"))
    args = p.parse_args()

    manifest = json.loads((args.qvoice_review / "work/manifest.json").read_text())
    chunk = manifest["chunks"][args.unit - 1]
    text = chunk["text"]
    has_dialogue = '"' in text or "\u201c" in text
    print(f"unit {args.unit}: {len(text.split())} words, dialogue={has_dialogue}")
    print(f"  {text[:110]}...")

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

    from mlx_audio.tts.utils import load_model

    print(f"loading {args.model}")
    model = load_model(args.model)
    rate = int(getattr(model, "sample_rate", 44100))
    ref = load_reference(REFS[REFERENCE]["audio"], rate)
    ref_text = REFS[REFERENCE]["text"]

    texts = [add_tags(text) if tagged else text for _, _, tagged in DIRECTIONS]

    print(f"\nrendering {len(DIRECTIONS)} directions in one batch")
    start = time.perf_counter()
    pieces: dict[int, list[np.ndarray]] = {}
    for result in model.batch_generate(
        texts=texts,
        ref_audios=[ref] * len(DIRECTIONS),
        ref_texts=[ref_text] * len(DIRECTIONS),
        instructs=[instruct for _, instruct, _ in DIRECTIONS],
        temperature=0.7,
        top_p=0.7,
        top_k=30,
        verbose=False,
    ):
        index = int(getattr(result, "sequence_idx", 0))
        pieces.setdefault(index, []).append(np.asarray(result.audio, dtype=np.float32))
    print(
        f"  {time.perf_counter() - start:.1f}s, peak {mx.get_peak_memory() / 1e9:.1f} GB"
    )

    target = active_rms(control, control_rate)
    args.out.mkdir(parents=True, exist_ok=True)

    entries = [("qvoice_control", control, control_rate)]
    for index, (name, _, _) in enumerate(DIRECTIONS):
        if index in pieces:
            entries.append((name, np.concatenate(pieces[index]), rate))

    labels = "ABCDEFGHIJ"
    key, report = {}, []
    print("\n  label  condition                secs    wps   pitch_span  dyn_range")
    for label, (name, audio, audio_rate) in zip(labels, entries):
        levelled = normalise(audio, audio_rate, target)
        sf.write(str(args.out / f"take-{label}.wav"), levelled, audio_rate, subtype="PCM_16")
        metrics = prosody(levelled, audio_rate)
        seconds = levelled.size / audio_rate
        wps = len(text.split()) / seconds if seconds else 0.0
        key[label] = name
        report.append({"label": label, "condition": name, "seconds": round(seconds, 1),
                       "wps": round(wps, 2), **metrics})
        print(
            f"  {label}      {name:23s} {seconds:5.1f}  {wps:5.2f}"
            f"      {metrics['pitch_span_semitones']:6.2f}     {metrics['dynamic_range_db']:6.1f}"
        )

    (args.out / "blind-key.json").write_text(
        json.dumps({"key": key, "reference": REFERENCE, "unit": args.unit,
                    "text": text, "metrics": report}, indent=2)
    )
    print(f"\nwrote {args.out}/take-*.wav and blind-key.json")
    print("one of these is the current QVoice render; listen before reading the key")


if __name__ == "__main__":
    main()
