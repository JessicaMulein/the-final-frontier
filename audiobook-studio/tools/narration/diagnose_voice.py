#!/usr/bin/env python3
"""Find chapter boundaries where the apparent speaker changes.

The listener reports that the voice is recognisably the same but not *the same* from
file to file. That is a classic zero-shot-clone failure: the speaker prompt preserves
identity broadly, while stochastic generation moves age, resonance, breathiness or
placement enough that a hard chapter boundary exposes it.

This is a diagnostic, not an acceptance gate. Five earlier objective metrics failed
to predict this listener's preferences, so the numbers only order which transitions
to hear first.

The fingerprint deliberately excludes loudness and pitch range, which vary with the
text and performance. It averages low-order MFCCs over voiced frames across an entire
chapter: a coarse vocal-tract / spectral-envelope signature. If that moves, timbre
moved. Median F0 and active level are printed separately to explain a perceptual jump
that the MFCC distance alone cannot.

It also writes transition clips: twelve seconds from the end of one chapter, half a
second of silence, then twelve seconds from the next. Those are the actual production
files, unprocessed, because the defect only exists in comparison.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.fft import dct
from scipy.signal import resample_poly

from prosody import pitch_stats

TARGET_RATE = 16_000


def load(path: Path, rate: int = TARGET_RATE) -> tuple[np.ndarray, int]:
    audio, source_rate = sf.read(str(path), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if source_rate != rate:
        from fractions import Fraction

        ratio = Fraction(rate, int(source_rate)).limit_denominator(1000)
        audio = resample_poly(audio, ratio.numerator, ratio.denominator).astype(
            np.float32
        )
    return audio, rate


def hz_to_mel(value):
    return 2595.0 * np.log10(1.0 + value / 700.0)


def mel_to_hz(value):
    return 700.0 * (10 ** (value / 2595.0) - 1.0)


def mel_bank(rate: int, nfft: int, bands: int = 40) -> np.ndarray:
    points = mel_to_hz(
        np.linspace(hz_to_mel(60), hz_to_mel(rate / 2), bands + 2)
    )
    bins = np.floor((nfft + 1) * points / rate).astype(int)
    bank = np.zeros((bands, nfft // 2 + 1), dtype=np.float64)
    for index in range(1, bands + 1):
        left, centre, right = bins[index - 1 : index + 2]
        if centre > left:
            bank[index - 1, left:centre] = np.linspace(0, 1, centre - left, endpoint=False)
        if right > centre:
            bank[index - 1, centre:right] = np.linspace(1, 0, right - centre, endpoint=False)
    return bank


def fingerprint(audio: np.ndarray, rate: int) -> dict:
    frame = int(rate * 0.025)
    hop = int(rate * 0.010)
    nfft = 512
    starts = np.arange(0, max(0, audio.size - frame), hop)
    if starts.size == 0:
        raise ValueError("audio too short")
    frames = np.stack([audio[s : s + frame] for s in starts]).astype(np.float64)
    rms = np.sqrt((frames**2).mean(axis=1) + 1e-12)
    peak = float(np.percentile(rms, 98))
    voiced = rms >= peak * 10 ** (-30 / 20)
    frames = frames[voiced]
    rms = rms[voiced]
    window = np.hanning(frame)
    power = np.abs(np.fft.rfft(frames * window[None, :], n=nfft, axis=1)) ** 2
    mel = np.maximum(power @ mel_bank(rate, nfft).T, 1e-12)
    coeff = dct(np.log(mel), type=2, axis=1, norm="ortho")[:, 1:14]

    # Median, not mean: dialogue and unusual words should not move a chapter's
    # speaker fingerprint.
    centre = np.median(coeff, axis=0)
    spread = np.median(np.abs(coeff - centre), axis=0)
    active = float(np.sqrt(np.mean(rms**2)))
    return {
        "mfcc": centre,
        "spread": spread,
        "active_rms": active,
        "voiced_frames": int(frames.shape[0]),
    }


def chapter_number(path: Path) -> int:
    match = re.search(r"chapter-(\d{3})", path.name)
    return int(match.group(1)) if match else -1


def robust_distance(a: dict, b: dict) -> float:
    # Scale each coefficient by the typical within-chapter spread of the pair.
    scale = np.maximum((a["spread"] + b["spread"]) / 2, 0.1)
    return float(np.sqrt(np.mean(((a["mfcc"] - b["mfcc"]) / scale) ** 2)))


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("audio_dir", type=Path, nargs="?", default=Path("out/book"))
    p.add_argument("--out", type=Path, default=Path("out/voice-transitions"))
    p.add_argument("--seconds", type=float, default=12.0)
    args = p.parse_args()

    paths = sorted(args.audio_dir.glob("*-fish-clean92.wav"), key=chapter_number)
    entries = []
    source_audio = {}
    print(f"fingerprinting {len(paths)} chapters")
    for path in paths:
        audio, rate = load(path)
        source_audio[chapter_number(path)] = (audio, rate, path)
        fp = fingerprint(audio, rate)
        # pitch_stats assumes 24 kHz; resample for a comparable diagnostic.
        p24 = resample_poly(audio, 3, 2).astype(np.float32)
        median_f0, _, _ = pitch_stats(p24)
        entries.append(
            {
                "chapter": chapter_number(path),
                "file": path.name,
                "fingerprint": fp,
                "median_f0": median_f0,
            }
        )

    transitions = []
    for left, right in zip(entries, entries[1:]):
        if right["chapter"] != left["chapter"] + 1:
            continue
        distance = robust_distance(left["fingerprint"], right["fingerprint"])
        level_db = 20 * np.log10(
            right["fingerprint"]["active_rms"] / left["fingerprint"]["active_rms"]
        )
        f0_delta = right["median_f0"] - left["median_f0"]
        transitions.append(
            {
                "from": left["chapter"],
                "to": right["chapter"],
                "timbre_distance": round(distance, 3),
                "level_delta_db": round(float(level_db), 2),
                "f0_delta_hz": round(float(f0_delta), 1),
            }
        )

    args.out.mkdir(parents=True, exist_ok=True)
    for item in transitions:
        left, rate, _ = source_audio[item["from"]]
        right, _, _ = source_audio[item["to"]]
        span = int(rate * args.seconds)
        gap = np.zeros(int(rate * 0.5), dtype=np.float32)
        clip = np.concatenate([left[-span:], gap, right[:span]])
        path = args.out / f"ch{item['from']:03d}-to-{item['to']:03d}.wav"
        sf.write(str(path), clip, rate, subtype="PCM_16")
        item["clip"] = path.name

    print(f"\n{'transition':>10s} {'timbre':>7s} {'level':>8s} {'f0':>8s}")
    for item in sorted(transitions, key=lambda x: -x["timbre_distance"]):
        print(
            f"{item['from']:03d}->{item['to']:03d}  "
            f"{item['timbre_distance']:7.3f}  {item['level_delta_db']:+7.2f}dB  "
            f"{item['f0_delta_hz']:+7.1f}Hz"
        )

    serialised = []
    for entry in entries:
        serialised.append(
            {
                "chapter": entry["chapter"],
                "file": entry["file"],
                "median_f0": round(entry["median_f0"], 1),
                "active_rms": round(entry["fingerprint"]["active_rms"], 6),
                "mfcc": [round(float(x), 5) for x in entry["fingerprint"]["mfcc"]],
            }
        )
    (args.out / "report.json").write_text(
        json.dumps({"chapters": serialised, "transitions": transitions}, indent=2)
    )
    print(f"\nwrote {len(transitions)} transition clips and {args.out / 'report.json'}")
    print("numbers order the listen; they do not decide whether a voice changed")


if __name__ == "__main__":
    main()
