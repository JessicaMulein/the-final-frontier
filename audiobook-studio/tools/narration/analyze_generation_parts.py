#!/usr/bin/env python3
"""Spectral and pace analysis of multi-call Fish generation parts.

Given a chapter render that used --max-words-per-call, extract each generation
part's audio from the joined WAV (via the manifest segment spans), write
standalone WAVs for listening, and compare brightness / articulation across
the re-anchor boundary.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf

import match_spectra
import pace


def _to24k(audio: np.ndarray, rate: int) -> np.ndarray:
    if rate == 24000:
        return audio.astype(np.float32)
    from fractions import Fraction

    from scipy.signal import resample_poly

    ratio = Fraction(24000, rate).limit_denominator()
    return resample_poly(audio, ratio.numerator, ratio.denominator).astype(np.float32)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("manifest", type=Path)
    p.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="defaults to the joined WAV's directory",
    )
    args = p.parse_args()

    manifest = json.loads(args.manifest.read_text())
    wav_path = Path(manifest["output"])
    if not wav_path.is_file():
        raise SystemExit(f"joined WAV missing: {wav_path}")
    out_dir = args.out_dir or wav_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    audio, rate = sf.read(str(wav_path), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)

    segments = manifest["segments"]
    parts: dict[int, list[dict]] = {}
    for seg in segments:
        parts.setdefault(int(seg["generation_part"]), []).append(seg)

    part_reports = []
    part_paths: list[Path] = []
    for part_index in sorted(parts):
        segs = parts[part_index]
        start = int(segs[0]["start_sample"])
        end = int(segs[-1]["end_sample"])
        piece = audio[start:end]
        path = out_dir / f"{wav_path.stem}.part{part_index:02d}.wav"
        sf.write(str(path), piece, rate, subtype="PCM_16")
        part_paths.append(path)

        paced = []
        for seg in segs:
            clip = audio[int(seg["start_sample"]) : int(seg["end_sample"])]
            paced.append(pace.measure(clip if rate == 24000 else _to24k(clip, rate)))
        live = [m for m in paced if m]
        artic = [m["articulation"] for m in live]
        pause = [m["pause_fraction"] for m in live]
        centroid_hz = match_spectra.centroid(piece, rate)
        report = {
            "generation_part": part_index,
            "path": str(path.resolve()),
            "seconds": round(piece.size / rate, 3),
            "segments": len(segs),
            "start_seconds": segs[0]["start_seconds"],
            "end_seconds": segs[-1]["end_seconds"],
            "centroid_hz": round(centroid_hz, 1),
            "articulation_mean": round(float(np.mean(artic)), 3) if artic else None,
            "articulation_first_third": (
                round(float(np.mean(artic[: max(1, len(artic) // 3)])), 3)
                if artic
                else None
            ),
            "articulation_last_third": (
                round(float(np.mean(artic[-max(1, len(artic) // 3) :])), 3)
                if artic
                else None
            ),
            "pause_fraction_mean": round(float(np.mean(pause)), 3) if pause else None,
        }
        part_reports.append(report)
        print(
            f"part {part_index}: {report['seconds']:.1f}s  "
            f"centroid {report['centroid_hz']:.0f} Hz  "
            f"artic {report['articulation_mean']}  "
            f"({report['articulation_first_third']} -> {report['articulation_last_third']})  "
            f"-> {path.name}"
        )

    boundary = None
    if len(part_reports) >= 2:
        left = sf.read(str(part_paths[-2]), always_2d=False)[0]
        right = sf.read(str(part_paths[-1]), always_2d=False)[0]
        left = np.asarray(left, dtype=np.float32)
        right = np.asarray(right, dtype=np.float32)
        window = int(rate * 30)
        left_tail = left[-window:] if left.size > window else left
        right_head = right[:window] if right.size > window else right
        c_left = match_spectra.centroid(left_tail, rate)
        c_right = match_spectra.centroid(right_head, rate)
        a_left = pace.measure(
            left_tail if rate == 24000 else _to24k(left_tail, rate)
        )
        a_right = pace.measure(
            right_head if rate == 24000 else _to24k(right_head, rate)
        )
        boundary = {
            "window_seconds": 30.0,
            "left_part": part_reports[-2]["generation_part"],
            "right_part": part_reports[-1]["generation_part"],
            "left_tail_centroid_hz": round(c_left, 1),
            "right_head_centroid_hz": round(c_right, 1),
            "centroid_delta_hz": round(c_right - c_left, 1),
            "left_tail_articulation": a_left["articulation"] if a_left else None,
            "right_head_articulation": a_right["articulation"] if a_right else None,
        }
        print(
            f"\nre-anchor boundary (30s tail/head): "
            f"centroid {boundary['left_tail_centroid_hz']:.0f} -> "
            f"{boundary['right_head_centroid_hz']:.0f} Hz "
            f"(delta {boundary['centroid_delta_hz']:+.0f})  "
            f"artic {boundary['left_tail_articulation']} -> "
            f"{boundary['right_head_articulation']}"
        )

    listen = out_dir / f"{wav_path.stem}.LISTEN.wav"
    if not listen.exists() or listen.resolve() != wav_path.resolve():
        if listen.resolve() != wav_path.resolve():
            listen.write_bytes(wav_path.read_bytes())
    report_path = out_dir / f"{wav_path.stem}.parts-spectral.json"
    payload = {
        "joined": str(wav_path.resolve()),
        "listen": str(listen.resolve()),
        "generation_calls": manifest.get("generation", {}).get("generation_calls"),
        "max_words_per_call": manifest.get("generation", {}).get("max_words_per_call"),
        "parts": part_reports,
        "boundary": boundary,
        "chapter_articulation": {
            "first_third": manifest.get("assembly", {}).get("articulation_first_third"),
            "last_third": manifest.get("assembly", {}).get("articulation_last_third"),
        },
        "verification": manifest.get("verification"),
    }
    report_path.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"\nwrote {report_path}")
    print(f"listen: {listen}")


if __name__ == "__main__":
    main()
