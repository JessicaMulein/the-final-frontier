#!/usr/bin/env python3
"""Blind A/B: does Fish S2 Pro read this prose with more range than QVoice?

The premise behind replacing the engine is unverified, so this renders the exact
text QVoice already rendered and puts them side by side under opaque labels.

It also tests the likeliest cause of the flat affect, which is not the engine at
all. Measured in `dialect-reference-analysis.json`, the locked narrator reference
carries a pitch span of 8.84 semitones against the EMNS clip's 19.24, and a
dynamic range of 22.6 dB against 27.3. Every clone inherits the range of the clip
it is cloned from, so a 4.8 second reference with half the range is a plausible
ceiling no amount of sampling will lift.

Hence the conditions below vary the reference and the direction, not just the
engine. Each reference is paired with its OWN transcript: the QVoice logs show
uk-s03 audio conditioned with the EMNS transcript, which is a mismatch that can
only hurt a clone.

Loudness is matched across conditions before writing, because the louder take
wins a blind comparison for the wrong reason.
"""

from __future__ import annotations

import argparse
import json
import math
import time
from pathlib import Path

import mlx.core as mx
import numpy as np
import soundfile as sf

from audio_io import load_reference

REPO = Path(__file__).resolve().parents[3]
REFS = {
    "uk_s03": {
        "audio": REPO
        / "audiobook-studio/assets/voice-refs/common-voice-refs/uk-southern-female-03-tight.wav",
        # Its own transcript, from dialect-reference-analysis.json.
        "text": "She can scoop these things into three red bags and we'll go "
        "meet her on Thursday at the train station.",
        "pitch_span_semitones": 8.84,
    },
    "emns_599": {
        "audio": REPO / "audiobook-studio/assets/voice-refs/emns-refs/emns-neutral-l0-599.wav",
        "text": "The band enjoyed much regional and some national success and "
        "released three albums.",
        "pitch_span_semitones": 19.24,
    },
}

RESTRAINED = (
    "Read slowly, clearly, and naturally. Maintain a measured literary pace "
    "without sounding like an announcer."
)
INTERIOR = (
    "Read as a first-person memoir: dry, precise, quietly unsettled. Let meaning "
    "land through timing and emphasis rather than volume. Never announce."
)


def active_rms(audio: np.ndarray, rate: int) -> float:
    frame = max(1, int(rate * 0.020))
    usable = (audio.size // frame) * frame
    if usable == 0:
        return 0.0
    frames = audio[:usable].reshape(-1, frame).astype(np.float64)
    rms = np.sqrt((frames**2).mean(axis=1) + 1e-12)
    peak = float(rms.max())
    if peak <= 0:
        return 0.0
    voiced = rms[rms >= peak * 10 ** (-36 / 20)]
    return float(np.sqrt(np.mean(voiced**2))) if voiced.size else 0.0


def normalise(audio: np.ndarray, rate: int, target: float) -> np.ndarray:
    level = active_rms(audio, rate)
    if level <= 0 or target <= 0:
        return audio
    out = audio.astype(np.float32) * (target / level)
    peak = float(np.abs(out).max())
    if peak > 0.99:
        out *= 0.99 / peak
    return out


def prosody(audio: np.ndarray, rate: int) -> dict:
    """Pitch span and dynamic range, the two numbers that describe flatness."""
    frame = max(1, int(rate * 0.040))
    hop = frame // 2
    lo, hi = int(rate / 400), int(rate / 60)  # 60-400 Hz search range
    pitches = []
    for start in range(0, max(0, audio.size - frame), hop):
        window = audio[start : start + frame].astype(np.float64)
        if np.sqrt((window**2).mean() + 1e-12) < 1e-3:
            continue
        window = window - window.mean()
        corr = np.correlate(window, window, mode="full")[frame - 1 :]
        if corr[0] <= 0:
            continue
        segment = corr[lo:hi]
        if segment.size == 0:
            continue
        lag = int(np.argmax(segment)) + lo
        if corr[lag] / corr[0] < 0.3:
            continue
        pitches.append(rate / lag)

    frames = audio[: (audio.size // frame) * frame].reshape(-1, frame).astype(np.float64)
    rms = np.sqrt((frames**2).mean(axis=1) + 1e-12)
    voiced = rms[rms >= float(rms.max()) * 10 ** (-36 / 20)]

    span = 0.0
    if len(pitches) >= 8:
        p5, p95 = np.percentile(pitches, [5, 95])
        if p5 > 0:
            span = 12 * math.log2(p95 / p5)
    dynamic = 0.0
    if voiced.size >= 8:
        q5, q95 = np.percentile(voiced, [5, 95])
        if q5 > 0:
            dynamic = 20 * math.log10(q95 / q5)
    return {
        "pitch_span_semitones": round(float(span), 2),
        "dynamic_range_db": round(float(dynamic), 1),
        "voiced_frames": int(voiced.size),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--model", default="mlx-community/fish-audio-s2-pro")
    p.add_argument(
        "--qvoice-review",
        type=Path,
        default=REPO / "audiobook/qvoice-production/review/chapter3-v2",
        help="existing QVoice render supplying the control and the text",
    )
    p.add_argument("--unit", type=int, default=1, help="which unit's text to use")
    p.add_argument("--out", type=Path, default=Path("out/audition-ab"))
    args = p.parse_args()

    manifest = json.loads((args.qvoice_review / "work/manifest.json").read_text())
    chunk = manifest["chunks"][args.unit - 1]
    text = chunk["text"]
    print(f"text ({len(text.split())} words): {text[:90]}...")

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

    conditions = [
        ("fish_uks03_restrained", "uk_s03", RESTRAINED),
        ("fish_uks03_interior", "uk_s03", INTERIOR),
        ("fish_emns_restrained", "emns_599", RESTRAINED),
        ("fish_emns_interior", "emns_599", INTERIOR),
    ]

    arrays = {name: load_reference(REFS[name]["audio"], rate) for name in REFS}
    renders: dict[str, np.ndarray] = {}

    print(f"\nrendering {len(conditions)} conditions in one batch")
    start = time.perf_counter()
    pieces: dict[int, list[np.ndarray]] = {}
    for result in model.batch_generate(
        texts=[text] * len(conditions),
        ref_audios=[arrays[ref] for _, ref, _ in conditions],
        ref_texts=[REFS[ref]["text"] for _, ref, _ in conditions],
        instructs=[instruct for _, _, instruct in conditions],
        temperature=0.7,
        top_p=0.7,
        top_k=30,
        verbose=False,
    ):
        index = int(getattr(result, "sequence_idx", 0))
        pieces.setdefault(index, []).append(
            np.asarray(result.audio, dtype=np.float32)
        )
    print(f"  {time.perf_counter() - start:.1f}s, peak {mx.get_peak_memory() / 1e9:.1f} GB")

    for index, (name, _, _) in enumerate(conditions):
        if index in pieces:
            renders[name] = np.concatenate(pieces[index])

    # Match loudness to the control so the comparison is about delivery.
    target = active_rms(control, control_rate)

    args.out.mkdir(parents=True, exist_ok=True)
    labels = "ABCDEFGH"
    key, report = {}, []
    entries = [("qvoice_control", control, control_rate)] + [
        (name, audio, rate) for name, audio in renders.items()
    ]

    print("\n  label  condition                 secs   pitch_span  dyn_range")
    for label, (name, audio, audio_rate) in zip(labels, entries):
        levelled = normalise(audio, audio_rate, target)
        path = args.out / f"voice-{label}.wav"
        sf.write(str(path), levelled, audio_rate, subtype="PCM_16")
        metrics = prosody(levelled, audio_rate)
        key[label] = name
        report.append({"label": label, "condition": name, **metrics})
        print(
            f"  {label}      {name:24s} {levelled.size / audio_rate:5.1f}"
            f"      {metrics['pitch_span_semitones']:6.2f}"
            f"     {metrics['dynamic_range_db']:6.1f}"
        )

    (args.out / "blind-key.json").write_text(
        json.dumps(
            {
                "key": key,
                "text": text,
                "metrics": report,
                "reference_pitch_spans": {
                    name: REFS[name]["pitch_span_semitones"] for name in REFS
                },
            },
            indent=2,
        )
    )
    print(f"\nwrote {args.out}/voice-*.wav and blind-key.json")
    print("listen before reading the key")


if __name__ == "__main__":
    main()
