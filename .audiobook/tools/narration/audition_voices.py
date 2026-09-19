#!/usr/bin/env python3
"""Blind audition of the clean studio references that were never evaluated.

The listener asked whether another voice is available. Three candidates were
already in the repository and had never been auditioned:

  uk-southern-female-01.wav   never evaluated
  uk-southern-female-02.wav   never evaluated, only 1.4 s of speech
  uk-southern-female-03.wav   the UNTRIMMED original of the locked reference

That last one matters most. The locked reference is the tight-cropped, faded
derivative of it, and the crop measures 8.84 semitones of pitch span against the
original's 12.91 for the same 4.5 s of speech. If that difference survives
cloning, roughly four semitones of range were given away by a preprocessing step,
on the voice the listener already likes.

All conditions use the direction the listener preferred in the previous audition,
so the reference is the only variable. Loudness is matched to the QVoice control
so the louder take cannot win for the wrong reason.
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
COMMON = REPO / ".audiobook/assets/voice-refs/common-voice-refs"

# Each reference paired with its own transcript. The locked pipeline conditioned
# uk-s03 audio with EMNS's transcript, a mismatch that can only hurt a clone.
UKS03_TEXT = (
    "She can scoop these things into three red bags and we'll go meet her on "
    "Thursday at the train station."
)

CANDIDATES = [
    ("uks03_tight_current", COMMON / "uk-southern-female-03-tight.wav", UKS03_TEXT),
    ("uks03_untrimmed", COMMON / "uk-southern-female-03.wav", UKS03_TEXT),
    ("uks01", COMMON / "uk-southern-female-01.wav", None),
    ("uks02", COMMON / "uk-southern-female-02.wav", None),
]

# The direction the listener chose in the previous round.
INTERIOR = (
    "Read as a first-person memoir: dry, precise, quietly unsettled. Let meaning "
    "land through timing and emphasis rather than volume. Never announce."
)


def transcribe(path: Path, model: str = "mlx-community/whisper-large-v3-turbo") -> str:
    """Transcribe a reference whose text is not recorded.

    ref_text conditions the clone, so guessing it is worse than reading it off the
    audio. Whisper is reliable on a few seconds of clean studio speech.
    """
    import mlx_whisper

    result = mlx_whisper.transcribe(
        str(path), path_or_hf_repo=model, language="en", verbose=False
    )
    return (result.get("text") or "").strip()


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="mlx-community/fish-audio-s2-pro")
    p.add_argument(
        "--qvoice-review",
        type=Path,
        default=REPO / "audiobook/qvoice-production/review/chapter3-v2",
    )
    p.add_argument("--unit", type=int, default=8, help="unit 8 contains dialogue")
    p.add_argument("--out", type=Path, default=Path("out/audition-voices"))
    args = p.parse_args()

    manifest = json.loads((args.qvoice_review / "work/manifest.json").read_text())
    chunk = manifest["chunks"][args.unit - 1]
    text = chunk["text"]
    print(f"unit {args.unit}: {len(text.split())} words")
    print(f"  {text[:100]}...")

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

    print("\nresolving reference transcripts")
    resolved = []
    for name, path, ref_text in CANDIDATES:
        if not path.is_file():
            print(f"  (missing) {path.name}")
            continue
        if ref_text is None:
            ref_text = transcribe(path)
            print(f"  {name}: transcribed -> {ref_text[:70]}")
        else:
            print(f"  {name}: known transcript")
        resolved.append((name, path, ref_text))

    from mlx_audio.tts.utils import load_model

    print(f"\nloading {args.model}")
    model = load_model(args.model)
    rate = int(getattr(model, "sample_rate", 44100))

    print(f"rendering {len(resolved)} references in one batch")
    start = time.perf_counter()
    pieces: dict[int, list[np.ndarray]] = {}
    for result in model.batch_generate(
        texts=[text] * len(resolved),
        ref_audios=[load_reference(path, rate) for _, path, _ in resolved],
        ref_texts=[ref_text for _, _, ref_text in resolved],
        instructs=[INTERIOR] * len(resolved),
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
    for index, (name, _, _) in enumerate(resolved):
        if index in pieces:
            entries.append((name, np.concatenate(pieces[index]), rate))

    labels = "ABCDEFGH"
    key, report = {}, []
    print("\n  label  condition               secs    wps   pitch_span  dyn_range")
    for label, (name, audio, audio_rate) in zip(labels, entries):
        levelled = normalise(audio, audio_rate, target)
        sf.write(
            str(args.out / f"voice-{label}.wav"), levelled, audio_rate, subtype="PCM_16"
        )
        metrics = prosody(levelled, audio_rate)
        seconds = levelled.size / audio_rate
        wps = len(text.split()) / seconds if seconds else 0.0
        key[label] = name
        report.append(
            {
                "label": label,
                "condition": name,
                "seconds": round(seconds, 1),
                "wps": round(wps, 2),
                **metrics,
            }
        )
        print(
            f"  {label}      {name:22s} {seconds:5.1f}  {wps:5.2f}"
            f"      {metrics['pitch_span_semitones']:6.2f}     "
            f"{metrics['dynamic_range_db']:6.1f}"
        )

    (args.out / "blind-key.json").write_text(
        json.dumps(
            {"key": key, "unit": args.unit, "instruct": INTERIOR, "text": text,
             "metrics": report},
            indent=2,
        )
    )
    print(f"\nwrote {args.out}/voice-*.wav and blind-key.json")
    print("judge identity and clarity first, range second; key afterwards")


if __name__ == "__main__":
    main()
