#!/usr/bin/env python3
"""Re-render selected units of an already-rendered chapter and re-assemble.

Why this exists
---------------
After the generation-length fixes, remaining defects are a per-unit lottery
rather than a systematic decay: in chapter 3's 15 units, 14 were accepted by ear
and one was an outlier against its own chapter -- lowest articulation rate,
highest pause load. Fixing that one unit through the chapter renderer costs a
full re-render, roughly ten minutes of compute to replace twenty-four seconds of
audio, which makes spot-fixing a 130-chapter book impractical.

Everything needed is already on disk. Unpatched units are lifted verbatim from
the assembled chapter using the boundaries the manifest recorded, so they arrive
already declicked, level-flattened and level-matched, with no Whisper pass and no
generation. Only the named units are regenerated.

Levels stay consistent because the manifest records the level target the original
assembly matched to; a patched unit is matched to that same target rather than
re-deriving a new one, so reusing neighbours cannot double-normalise them.

Selection differs from the chapter renderer on purpose. The renderer accepts the
first seed that passes ASR, which is how an outlier ships in the first place. Here
every candidate that passes ASR is also scored on pace against the median of the
units being kept, and the closest to that norm wins. The goal of a patch is not a
different unit, it is an unremarkable one.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))

import pace  # noqa: E402
from drift import profile as drift_profile  # noqa: E402
from normalize_speech_text import normalize  # noqa: E402
from render_chapter_chatterbox import extract_body  # noqa: E402
from render_chapter_qvoice import (  # noqa: E402
    active_rms,
    build_warmup,
    comfort_noise,
    flatten_level,
    generated_seconds,
    render_candidate,
    trim_warmup,
)
from render_chapter_qwen3 import (  # noqa: E402
    SAMPLE_RATE,
    chunk_paragraphs,
    declick,
    verify_chunk,
)

LEVEL_LIMIT_DB = 2.0


def load_mono(path: Path) -> np.ndarray:
    audio, _ = sf.read(str(path), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return audio


def match_to_target(audio: np.ndarray, target: float) -> tuple[np.ndarray, float]:
    """Gain-match one unit to the level target the original assembly used."""
    level = active_rms(audio)
    if level <= 0 or target <= 0:
        return audio, 0.0
    gain_db = max(-LEVEL_LIMIT_DB, min(LEVEL_LIMIT_DB, 20 * math.log10(target / level)))
    out = audio.astype(np.float32, copy=True) * (10 ** (gain_db / 20))
    peak = float(np.abs(out).max())
    if peak > 0.99:
        out *= 0.99 / peak
    return out, round(gain_db, 3)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--work-dir", type=Path, required=True, help="existing work dir")
    p.add_argument("--output", type=Path, required=True, help="new chapter wav")
    p.add_argument(
        "--chunk",
        type=int,
        action="append",
        required=True,
        metavar="INDEX",
        help="1-based unit index to re-render; repeatable",
    )
    p.add_argument("--binary", type=Path, required=True)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument(
        "--candidate-seeds",
        type=int,
        default=4,
        help="how many seeds to try per patched unit, scored on pace",
    )
    p.add_argument(
        "--first-seed",
        type=int,
        default=None,
        help="first seed to try (default: one past the seed already accepted)",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="replace the unit with the best passing candidate even when pace "
        "is not closer to the chapter norm (for explicit acoustic defects)",
    )
    p.add_argument("--temperature", type=float, default=0.5)
    p.add_argument("--rate", type=float, default=0.92)
    p.add_argument("--max-tokens", type=int, default=1800)
    p.add_argument("--verify-model", default="mlx-community/whisper-large-v3-turbo")
    args = p.parse_args()

    work = args.work_dir.resolve()
    manifest = json.loads((work / "manifest.json").read_text())
    previous = Path(manifest["output"])
    assembled = previous if previous.is_file() else work.parent / previous.name
    if not assembled.is_file():
        raise SystemExit(f"cannot find the assembled chapter: {previous}")

    chapter = Path(manifest["chapter"])
    spoken = normalize(extract_body(chapter))
    chunks = chunk_paragraphs(spoken, manifest["chunk_chars"])
    recorded = [c["text"] for c in manifest["chunks"]]
    if chunks != recorded:
        raise SystemExit(
            "chapter text no longer matches the manifest "
            f"({len(chunks)} units now vs {len(recorded)} recorded); "
            "patching would misalign, run a full render instead"
        )

    patch_set = sorted(set(args.chunk))
    for index in patch_set:
        if not 1 <= index <= len(recorded):
            raise SystemExit(f"unit {index} out of range 1..{len(recorded)}")

    audio_in = load_mono(assembled)
    target = manifest["assembly"]["level_target_active_rms"]
    pause_ms = manifest["assembly"]["pause_ms"]

    # Existing units, verbatim, plus the pace norm of the ones being kept.
    units: dict[int, np.ndarray] = {}
    kept_measures = []
    for chunk in manifest["chunks"]:
        start = int(chunk["start_seconds"] * SAMPLE_RATE)
        end = int(chunk["end_seconds"] * SAMPLE_RATE)
        segment = audio_in[start:end].copy()
        units[chunk["index"]] = segment
        if chunk["index"] not in patch_set:
            measured = pace.measure(segment)
            if measured:
                kept_measures.append(measured)
    norm = pace.norm_of(kept_measures)
    print(
        f"chapter norm from {norm.get('units', 0)} kept units: "
        f"articulation {norm.get('articulation', 0):.3f}, "
        f"pause {norm.get('pause_fraction', 0) * 100:.1f}%",
        flush=True,
    )

    runtime = SimpleNamespace(
        binary=args.binary.resolve(),
        model=args.model.resolve(),
        voice=Path(manifest["voice"]),
        instruction=manifest["instruction"],
        temperature=args.temperature,
        rate=args.rate,
        max_tokens=args.max_tokens,
    )

    report = []
    for index in patch_set:
        record = manifest["chunks"][index - 1]
        text = record["text"]
        before = pace.measure(units[index])
        print(
            f"\n=== unit {index}: {len(text.split())} words, "
            f"was seed {record['seed']} "
            f"(articulation {before['articulation']:.3f}, "
            f"pause {before['pause_fraction'] * 100:.1f}%, "
            f"deviation {pace.deviation(before, norm):.3f})",
            flush=True,
        )

        warmup_text = ""
        if manifest.get("overlap_warmup", True):
            if index > 1:
                warmup_text = build_warmup(
                    chunks[index - 2], manifest.get("warmup_max_words", 24)
                )
            else:
                warmup_text = " ".join((manifest.get("lead_in") or "").split())
        generation_text = f"{warmup_text}\n\n{text}" if warmup_text else text

        chunk_dir = work / f"chunk-{index:03d}"
        chunk_dir.mkdir(parents=True, exist_ok=True)
        first = args.first_seed if args.first_seed is not None else record["seed"] + 1
        candidates = []
        for offset in range(args.candidate_seeds):
            seed = first + offset
            wav = chunk_dir / f"patch-seed-{seed}.wav"
            log = chunk_dir / f"patch-seed-{seed}.log"
            exit_code = render_candidate(runtime, generation_text, seed, wav, log)
            if exit_code != 0 or not wav.is_file():
                print(f"  seed {seed}: runtime exit {exit_code}", flush=True)
                continue
            grown = generated_seconds(log)
            candidate = load_mono(wav)
            try:
                if warmup_text:
                    candidate, overlap, words = trim_warmup(
                        candidate,
                        warmup_text=warmup_text,
                        new_text=text,
                        verify_model=args.verify_model,
                    )
                    quality = overlap["delivered_quality"]
                else:
                    overlap, words = None, None
                    quality = verify_chunk(
                        candidate, text, model=args.verify_model, language="en"
                    )
            except ValueError as error:
                print(f"  seed {seed}: rejected ({error})", flush=True)
                continue
            if not quality["passed"]:
                print(
                    f"  seed {seed}: failed ASR wer={quality['wer']:.3f} "
                    f"cov={quality['coverage']:.3f}",
                    flush=True,
                )
                continue

            candidate, clicks = declick(candidate)
            candidate, correction = flatten_level(candidate)
            measured = pace.measure(candidate)
            score = pace.deviation(measured, norm)
            print(
                f"  seed {seed}: {candidate.size / SAMPLE_RATE:.1f}s "
                f"wer={quality['wer']:.3f} gen={grown if grown else float('nan'):.1f}s "
                f"articulation {measured['articulation']:.3f} "
                f"pause {measured['pause_fraction'] * 100:.1f}% "
                f"deviation {score:.3f}",
                flush=True,
            )
            candidates.append(
                {
                    "seed": seed,
                    "audio": candidate,
                    "quality": {k: v for k, v in quality.items() if k != "transcript"},
                    "overlap": overlap,
                    "words": words,
                    "clicks": clicks,
                    "level_correction_db": correction,
                    "generated_seconds": grown,
                    "pace": measured,
                    "deviation": score,
                }
            )

        if not candidates:
            print(f"  no usable candidate for unit {index}; keeping the original")
            report.append({"index": index, "patched": False})
            continue

        best = min(candidates, key=lambda c: c["deviation"])
        if not args.force and best["deviation"] >= pace.deviation(before, norm):
            print(
                f"  best candidate (seed {best['seed']}, deviation "
                f"{best['deviation']:.3f}) is no closer to the norm than the "
                f"original ({pace.deviation(before, norm):.3f}); keeping the original"
            )
            report.append(
                {
                    "index": index,
                    "patched": False,
                    "reason": "no candidate improved on the original",
                    "candidates": [
                        {"seed": c["seed"], "deviation": c["deviation"]} for c in candidates
                    ],
                }
            )
            continue

        levelled, gain_db = match_to_target(best["audio"], target)
        units[index] = levelled
        after = pace.measure(levelled)
        print(
            f"  -> seed {best['seed']}: articulation "
            f"{before['articulation']:.3f} -> {after['articulation']:.3f}, "
            f"pause {before['pause_fraction'] * 100:.1f}% -> "
            f"{after['pause_fraction'] * 100:.1f}%, gain {gain_db:+.2f}dB"
        )
        record.update(
            {
                "seed": best["seed"],
                "patched_from_seed": manifest["chunks"][index - 1]["seed"],
                "generated_seconds": best["generated_seconds"],
                "overlap": best["overlap"],
                "clicks_repaired": best["clicks"],
                "level_correction_db": best["level_correction_db"],
                "gain_db": gain_db,
                "drift": drift_profile(
                    best["audio"],
                    words=best["words"] or None,
                    model=None if best["words"] else args.verify_model,
                ),
                "pace": after,
                "attempts": [
                    {"seed": c["seed"], "deviation": c["deviation"], "pace": c["pace"]}
                    for c in candidates
                ],
            }
        )
        report.append(
            {
                "index": index,
                "patched": True,
                "seed": best["seed"],
                "articulation_before": before["articulation"],
                "articulation_after": after["articulation"],
            }
        )

    # Re-assemble in order, with the same seam treatment as the original.
    ordered = [units[c["index"]] for c in manifest["chunks"]]
    gap = int(SAMPLE_RATE * pause_ms / 1000)
    pieces, cursor = [], 0
    for position, unit in enumerate(ordered):
        start = cursor / SAMPLE_RATE
        pieces.append(unit)
        cursor += unit.size
        manifest["chunks"][position]["start_seconds"] = round(start, 3)
        manifest["chunks"][position]["end_seconds"] = round(cursor / SAMPLE_RATE, 3)
        if position < len(ordered) - 1:
            tone = comfort_noise(ordered, gap, seed=1000 + position)
            pieces.append(tone)
            cursor += tone.size
    joined = np.concatenate(pieces)
    peak = float(np.abs(joined).max())
    if peak > 0.99:
        joined *= 0.99 / peak

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(args.output), joined, SAMPLE_RATE, subtype="PCM_16")

    quality = verify_chunk(joined, spoken, model=args.verify_model, language="en")
    manifest["output"] = str(args.output.resolve())
    manifest["assembly"]["seconds"] = round(joined.size / SAMPLE_RATE, 3)
    manifest["assembly"]["chapter_quality"] = {
        k: v for k, v in quality.items() if k != "transcript"
    }
    manifest["patches"] = manifest.get("patches", []) + [
        {"units": patch_set, "result": report}
    ]
    (work / "manifest.json").write_text(json.dumps(manifest, indent=2))

    print(
        f"\nWrote {args.output} ({joined.size / SAMPLE_RATE / 60:.2f} min); "
        f"chapter WER={quality['wer']:.3f} coverage={quality['coverage']:.3f} "
        f"pass={quality['passed']}",
        flush=True,
    )
    if not quality["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
