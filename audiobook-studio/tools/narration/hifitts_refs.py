#!/usr/bin/env python3
"""Build and score candidate narrator references from Hi-Fi TTS.

Why this dataset
----------------
Every reference tried so far failed on one of the two axes that matter. The locked
uk-s03 clip is clean but narrow (8.84 semitones). EMNS is wide (19.24) but the
listener hears "hiss and something else". The voice the listener then chose from the
remaining studio clips has only 1.4 seconds of speech, which is too thin to trust
over a book.

Hi-Fi TTS is the first source that can satisfy all three constraints at once:

  * 44.1 kHz, matching Fish's native rate, so no resampling of the identity source
  * selected for SNR >= 32 dB and signal bandwidth >= 13 kHz, with a `clean`
    subset held to SNR >= 40 dB
  * at least 17 hours per speaker, so a reference can be as long as the cloner wants
  * every clip carries a zero-WER verified transcript, which is exactly what
    `ref_text` needs, and removes the transcript-mismatch bug found in the QVoice
    path

It is also audiobook narration rather than read sentences, so the prosody is the
register this novel actually needs.

Two honest caveats, both from the dataset's own paper. The authors note LibriVox
audio still lags professional recordings, with hiss and metallic high frequencies
as the known residue -- the very defect that disqualified EMNS, so these candidates
must be judged by ear, not assumed clean. And they sought written consent from
speakers before using a voice for synthesis, and encourage others to do the same.

What this does
--------------
For each speaker, concatenate consecutive clips into a reference of about the
requested length, joining on the clip boundaries the dataset already provides and
carrying the concatenated transcript with it. Then score every candidate on
cleanliness and range so the shortlist is ordered before anyone listens.
"""

from __future__ import annotations

import argparse
import glob
import io
import json
import sys
from pathlib import Path

import numpy as np
import soundfile as sf


from prosody import dynamic_range_db, pitch_stats, speech_seconds  # noqa: E402

SNAPSHOT = "/Users/jessica/.cache/huggingface/hub/datasets--MikhailT--hifi-tts/snapshots"


def decode(audio_field) -> tuple[np.ndarray, int]:
    if isinstance(audio_field, dict):
        if audio_field.get("bytes"):
            data, rate = sf.read(io.BytesIO(audio_field["bytes"]), always_2d=False)
        else:
            data, rate = sf.read(audio_field["path"], always_2d=False)
    else:
        data, rate = sf.read(io.BytesIO(audio_field), always_2d=False)
    data = np.asarray(data, dtype=np.float32)
    if data.ndim > 1:
        data = data.mean(axis=1)
    return data, int(rate)


def snr_estimate(audio: np.ndarray, rate: int) -> float:
    """Crude SNR: voiced power against the power of the quietest frames, in dB."""
    frame = max(1, int(rate * 0.025))
    count = audio.size // frame
    if count < 16:
        return 0.0
    rms = np.sqrt(
        (audio[: count * frame].reshape(count, frame).astype(np.float64) ** 2).mean(
            axis=1
        )
        + 1e-12
    )
    speech = float(np.percentile(rms, 90))
    noise = float(np.percentile(rms, 5))
    if speech <= 0 or noise <= 0:
        return 0.0
    return float(20 * np.log10(speech / noise))


def hf_metallic(audio: np.ndarray, rate: int) -> float:
    """Energy fraction above 10 kHz during voiced frames.

    The paper names "hissing and metallic sound in samples with boosted high
    frequencies" as the residual defect. Unlike the gap-based measure tried
    earlier -- which rated EMNS cleaner than the reference the listener preferred,
    because EMNS's gaps are digitally zeroed -- this looks inside voiced audio,
    where that kind of boost actually lives.
    """
    n = 2048
    freqs = np.fft.rfftfreq(n, 1 / rate)
    window = np.hanning(n)
    frame_rms = []
    frames = []
    for start in range(0, max(0, audio.size - n), n):
        segment = audio[start : start + n].astype(np.float64)
        level = float(np.sqrt((segment**2).mean() + 1e-12))
        frame_rms.append(level)
        frames.append(segment)
    if not frames:
        return 0.0
    threshold = float(np.percentile(frame_rms, 70))
    ratios = []
    for level, segment in zip(frame_rms, frames):
        if level < threshold:
            continue
        power = np.abs(np.fft.rfft(segment * window)) ** 2
        total = power.sum()
        if total > 0:
            ratios.append(float(power[freqs > 10000].sum() / total))
    return float(np.mean(ratios)) if ratios else 0.0


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seconds", type=float, default=25.0, help="target reference length")
    p.add_argument("--out", type=Path, default=Path("out/hifitts-refs"))
    args = p.parse_args()

    import pyarrow.parquet as pq

    files = sorted(glob.glob(f"{SNAPSHOT}/*/data/dev.*.parquet"))
    if not files:
        raise SystemExit("dev parquet shards not found; download them first")

    args.out.mkdir(parents=True, exist_ok=True)
    rows = []

    for path in files:
        subset = Path(path).name.split("-")[0]  # dev.clean / dev.other
        table = pq.read_table(path)
        speakers = table.column("speaker").to_pylist()
        texts = table.column("text_normalized").to_pylist()
        durations = table.column("duration").to_pylist()
        audio_col = table.column("audio").to_pylist()

        for speaker in sorted(set(speakers)):
            indices = [i for i, s in enumerate(speakers) if s == speaker]
            # Prefer mid-length clips: very short ones carry little prosody, very
            # long ones risk a chapter break or a breath in the middle.
            indices.sort(key=lambda i: abs(float(durations[i]) - 8.0))

            pieces, transcript, total, rate = [], [], 0.0, None
            for i in indices:
                audio, clip_rate = decode(audio_col[i])
                if rate is None:
                    rate = clip_rate
                elif clip_rate != rate:
                    continue
                pieces.append(audio)
                transcript.append(str(texts[i]).strip())
                total += audio.size / clip_rate
                if total >= args.seconds:
                    break
            if not pieces or rate is None:
                continue

            joined = np.concatenate(pieces)
            peak = float(np.abs(joined).max())
            if peak > 0:
                joined = joined / peak * 0.95

            name = f"hifitts-{subset.split('.')[1]}-{speaker}"
            wav_path = args.out / f"{name}.wav"
            sf.write(str(wav_path), joined, rate, subtype="PCM_16")
            text = " ".join(transcript)
            (args.out / f"{name}.txt").write_text(text + "\n")

            _, _, span = pitch_stats(
                joined if rate == 24000 else _to24k(joined, rate)
            )
            rows.append(
                {
                    "name": name,
                    "speaker": speaker,
                    "subset": subset,
                    "rate": rate,
                    "seconds": round(joined.size / rate, 2),
                    "clips": len(pieces),
                    "pitch_span_semitones": round(span, 2),
                    "dynamic_range_db": round(
                        dynamic_range_db(
                            joined if rate == 24000 else _to24k(joined, rate)
                        ),
                        1,
                    ),
                    "snr_db": round(snr_estimate(joined, rate), 1),
                    "hf_above_10k": round(hf_metallic(joined, rate), 4),
                    "words": len(text.split()),
                }
            )

    rows.sort(key=lambda r: -r["pitch_span_semitones"])
    print(
        f"{'name':28s} {'set':6s} {'secs':>5s} {'span':>6s} {'dyn':>6s} "
        f"{'snr':>6s} {'>10k':>7s}"
    )
    for row in rows:
        print(
            f"{row['name']:28s} {row['subset'].split('.')[1]:6s} {row['seconds']:5.1f} "
            f"{row['pitch_span_semitones']:6.2f} {row['dynamic_range_db']:6.1f} "
            f"{row['snr_db']:6.1f} {row['hf_above_10k']:7.4f}"
        )

    (args.out / "scores.json").write_text(json.dumps(rows, indent=2))
    print(f"\nwrote {len(rows)} references to {args.out}")
    print("reference for comparison: uk-s03 span 8.84, EMNS span 19.24 (rejected: hiss)")


def _to24k(audio: np.ndarray, rate: int) -> np.ndarray:
    from fractions import Fraction

    from scipy.signal import resample_poly

    ratio = Fraction(24000, int(rate)).limit_denominator(1000)
    return resample_poly(audio, ratio.numerator, ratio.denominator).astype(np.float32)


if __name__ == "__main__":
    main()
