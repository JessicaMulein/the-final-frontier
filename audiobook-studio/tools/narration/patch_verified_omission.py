#!/usr/bin/env python3
"""Replace a verified omission or unintelligible span with separately generated speech.

This is not a general editing shortcut. It exists for a specific Fish failure mode:
the model silently omits an instruction-like phrase while leaving a long quiet region
where it belonged. Re-rendering with a fixed seed reproduces the omission exactly.

Safety invariants:

* the replacement region must be at least 20 dB quieter than chapter speech unless
  `--replace-unintelligible` explicitly records that whole-chapter ASR found
  unintelligible full-level audio there;
* the phrase must fit without time compression;
* output sample count and rate are exactly unchanged;
* the phrase is centered, leaving the existing silence around it;
* 30 ms equal-time fades prevent edge discontinuities;
* the final whole chapter is re-transcribed against the manuscript;
* the adjacent manifest is rebound to the final bytes and records the patch.

The explicit region is in delivered-file time, including the chapter announcement.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
import soundfile as sf

from manuscript import spoken_text
from render_chapter_fish import active_rms, comfort_gap, verify


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def mono(path: Path) -> tuple[np.ndarray, int]:
    audio, rate = sf.read(str(path), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return audio, int(rate)


def trim(audio: np.ndarray, rate: int, floor_db: float = -45.0) -> np.ndarray:
    frame = max(1, int(rate * 0.010))
    usable = audio[: audio.size - audio.size % frame]
    levels = np.sqrt((usable.reshape(-1, frame).astype(np.float64) ** 2).mean(axis=1) + 1e-20)
    peak = float(levels.max()) if levels.size else 0.0
    live = np.flatnonzero(levels >= peak * 10 ** (floor_db / 20)) if peak > 0 else np.zeros(0, int)
    if live.size == 0:
        raise SystemExit("patch phrase contains no speech")
    return audio[live[0] * frame : min(audio.size, (live[-1] + 1) * frame)]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("audio", type=Path)
    p.add_argument("phrase", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--chapter", type=Path, required=True)
    p.add_argument(
        "--announcement-text",
        default=None,
        help="when supplied, verify the complete delivered file against this spoken "
        "announcement plus manuscript prose. Useful when Whisper recognizes a patch "
        "with natural lead-in but drops it when transcription starts at a hard slice",
    )
    p.add_argument("--start", type=float, required=True)
    p.add_argument("--end", type=float, required=True)
    p.add_argument(
        "--replace-unintelligible",
        action="store_true",
        help="allow replacement of a full-level region that whole-chapter ASR proved "
        "does not contain the expected words; recorded as unintelligible replacement",
    )
    p.add_argument(
        "--allow-duration-change",
        action="store_true",
        help="allow a normally spoken phrase to exceed the unintelligible region. "
        "The exact assembly map and all later offsets are shifted by the sample delta",
    )
    p.add_argument("--verify-model", default="mlx-community/whisper-large-v3-turbo")
    args = p.parse_args()

    audio, rate = mono(args.audio)
    phrase, phrase_rate = mono(args.phrase)
    if phrase_rate != rate:
        raise SystemExit(f"phrase rate {phrase_rate} != chapter rate {rate}")
    phrase = trim(phrase, rate)

    start, end = int(round(args.start * rate)), int(round(args.end * rate))
    if not 0 <= start < end <= audio.size:
        raise SystemExit("patch region is outside the chapter")
    region = audio[start:end]
    chapter_level = active_rms(audio, rate)
    region_rms = float(np.sqrt(np.mean(region.astype(np.float64) ** 2) + 1e-20))
    relative_db = 20 * np.log10((region_rms + 1e-20) / (chapter_level + 1e-20))
    if relative_db > -20.0 and not args.replace_unintelligible:
        raise SystemExit(
            f"refusing to overwrite non-silent material: region is {relative_db:.1f} dB "
            "relative to chapter speech; use --replace-unintelligible only after "
            "whole-chapter ASR proves the expected words are absent"
        )
    if phrase.size > region.size and not args.allow_duration_change:
        raise SystemExit(
            f"phrase is {phrase.size / rate:.3f}s but region is {region.size / rate:.3f}s; "
            "use --allow-duration-change rather than time-compressing speech"
        )

    phrase_level = active_rms(phrase, rate)
    if phrase_level > 0 and chapter_level > 0:
        gain_db = float(np.clip(20 * np.log10(chapter_level / phrase_level), -3.0, 3.0))
        phrase = phrase * 10 ** (gain_db / 20)
    else:
        gain_db = 0.0
    peak = float(np.abs(phrase).max())
    if peak > 0.99:
        phrase *= 0.99 / peak

    fade = min(int(rate * 0.030), phrase.size // 4, region.size // 4)
    patch = phrase.copy()
    if fade:
        patch[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
        patch[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)

    if phrase.size > region.size:
        # Replace the compressed/unintelligible span with normally paced speech and
        # shift the rest of the chapter. Never time-compress a repair to preserve a
        # bad duration: intelligibility is the reason this patch exists.
        patched = np.concatenate([audio[:start], patch, audio[end:]]).astype(np.float32)
        position = start
    else:
        patched = audio.copy()
        if args.replace_unintelligible:
            # Remove the bad speech rather than mixing over it. Use production V6
            # floor from the rest of this chapter and preserve both edge waveforms.
            donors = [audio[:start], audio[end:]]
            replacement_region = comfort_gap(donors, region.size, rate, seed=15015)
            if fade:
                alpha = np.linspace(0, 1, fade, dtype=np.float32)
                replacement_region[:fade] = region[:fade] * (1 - alpha) + replacement_region[:fade] * alpha
                replacement_region[-fade:] = replacement_region[-fade:] * (1 - alpha) + region[-fade:] * alpha
            patched[start:end] = replacement_region
        position = start + (region.size - phrase.size) // 2
        patched[position : position + patch.size] += patch
    sample_delta = int(patched.size - audio.size)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(args.output), patched, rate, subtype="PCM_16")

    manifest = json.loads(args.manifest.read_text())
    expected = spoken_text(args.chapter)
    if args.announcement_text:
        quality = verify(patched, rate, args.announcement_text + " " + expected, args.verify_model)
        verification_scope = "full_with_announcement"
    else:
        prose_start = int(manifest["assembly"]["prose_start_sample"])
        quality = verify(patched[prose_start:], rate, expected, args.verify_model)
        offset = prose_start / rate
        for segment in quality.get("asr_segments", []):
            segment["start"] = round(segment["start"] + offset, 3)
            segment["end"] = round(segment["end"] + offset, 3)
        verification_scope = "prose_only"
    if not quality.get("passed"):
        raise SystemExit(
            f"patched chapter failed verification: WER {quality['wer']}, "
            f"gap {quality['max_expected_gap']}, added {quality['max_added_span']}"
        )

    if sample_delta:
        assembly = manifest["assembly"]
        assembly_map = assembly.get("assembly_map") or []
        containing = [
            entry
            for entry in assembly_map
            if entry["start_sample"] <= start and entry["end_sample"] >= end
        ]
        if len(containing) != 1 or containing[0].get("kind") != "speech_segment":
            raise SystemExit("duration-changing patch is not inside one speech segment")
        owner = containing[0]
        owner_index = assembly_map.index(owner)
        owner["end_sample"] += sample_delta
        owner["end_seconds"] = round(owner["end_sample"] / rate, 6)
        for entry in assembly_map[owner_index + 1 :]:
            entry["start_sample"] += sample_delta
            entry["end_sample"] += sample_delta
            entry["start_seconds"] = round(entry["start_sample"] / rate, 6)
            entry["end_seconds"] = round(entry["end_sample"] / rate, 6)
        speech_entries = [
            entry for entry in assembly_map if entry.get("kind") == "speech_segment"
        ]
        segments = manifest.get("segments", [])
        if len(speech_entries) != len(segments):
            raise SystemExit("speech record count changed while shifting assembly map")
        for segment, mapped in zip(segments, speech_entries):
            for field in ("start_sample", "end_sample", "start_seconds", "end_seconds"):
                segment[field] = mapped[field]
        assembly["sample_count"] = int(patched.size)
        assembly["seconds"] = round(patched.size / rate, 3)
        if assembly_map[-1]["end_sample"] != patched.size:
            raise SystemExit("shifted assembly map does not end at patched sample count")

    manifest["output"] = str(args.output.resolve())
    manifest["output_sha256"] = sha256(args.output)
    manifest["assembly"]["chapter_quality"] = {
        key: value for key, value in quality.items() if key != "transcript"
    }
    existing_patches = manifest["assembly"].get("production_patches") or []
    existing_patches.append(
        {
            "kind": (
                "verified_unintelligible_replacement"
                if args.replace_unintelligible
                else "verified_silent_omission"
            ),
            "phrase_path": str(args.phrase),
            "phrase_sha256": sha256(args.phrase),
            "region_start_sample": start,
            "region_end_sample": end,
            "phrase_start_sample": position,
            "phrase_end_sample": position + phrase.size,
            "sample_delta": sample_delta,
            "region_relative_db": round(float(relative_db), 2),
            "gain_db": round(gain_db, 3),
            "verification_scope": verification_scope,
            "announcement_text": args.announcement_text,
        }
    )
    manifest["assembly"]["production_patches"] = existing_patches
    destination_manifest = args.output.with_suffix(".manifest.json")
    staged = destination_manifest.with_suffix(".manifest.json.tmp")
    staged.write_text(json.dumps(manifest, indent=2))
    staged.replace(destination_manifest)

    print(f"patched {args.output}")
    print(
        f"  region {start / rate:.3f}-{end / rate:.3f}s "
        f"({relative_db:.1f} dB relative to speech)"
    )
    print(f"  phrase {phrase.size / rate:.3f}s at {position / rate:.3f}s, gain {gain_db:+.2f} dB")
    print(
        f"  samples {audio.size} -> {patched.size} (delta {sample_delta:+d}); "
        f"WER {quality['wer']:.4f}; coverage {quality['coverage']:.4f}; "
        f"pass {quality['passed']}"
    )
    print(f"  wrote {destination_manifest}")


if __name__ == "__main__":
    main()
