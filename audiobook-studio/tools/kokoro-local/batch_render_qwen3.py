#!/usr/bin/env python3
"""Batch-render the book with Qwen3-TTS (MLX), model loaded once.

Local audition tooling only — does not touch the Nova production path.

Per chapter: normalise numerals -> paragraph chunks -> generate each chunk with
ASR verification and retry -> declick -> level-match -> edge fades -> join.

Everything it can check, it checks without a listener, and it records what it
could not. Per-chapter JSON captures chunk count, worst chunk WER, chunks that
stayed mismatched after retries, clicks repaired and loudness spread, so a
listening pass can be aimed rather than exhaustive.

Example
-------
  PY=.venv/bin/python
  $PY batch_render_qwen3.py --start 1 --end 128 \
      --manuscript-root "../../../The Final Frontier Novel/chapters" \
      --ref-audio "../../../audiobook/kokoro-audition/emns-refs/emns-neutral-l0-599.wav" \
      --ref-text "The band enjoyed much regional and some national success, and released three albums." \
      --output-dir "../../../audiobook" --voice-tag qwen3-emns --skip-existing
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))

from batch_render_chatterbox import discover_chapters  # noqa: E402
from normalize_speech_text import normalize  # noqa: E402
from render_chapter_chatterbox import extract_body  # noqa: E402
from render_chapter_qwen3 import (  # noqa: E402
    MODEL_ID,
    SAMPLE_RATE,
    chunk_paragraphs,
    declick,
    match_level,
    room_tone,
    soften_edges,
    suppress_onset_transient,
    trim_tail_artifact,
    verify_chunk,
)


def render_chapter(
    model,
    text: str,
    *,
    kwargs: dict,
    pause_ms: int,
    max_chunk_chars: int,
    verify_model: str | None,
    retries: int,
    target_rms_dbfs: float,
    fade_ms: float,
    label: str,
) -> tuple[np.ndarray, dict]:
    chunks = chunk_paragraphs(normalize(text), max_chunk_chars)
    pause = np.zeros(int(SAMPLE_RATE * pause_ms / 1000), dtype=np.float32)
    pieces: list[np.ndarray] = []
    levels: list[float] = []
    clicks = 0
    rerolls = 0
    tail_trimmed = 0.0
    cursor = 0
    boundaries: list[list[float]] = []
    unresolved: list[dict] = []
    worst_wer = 0.0

    for index, chunk in enumerate(chunks, start=1):
        piece = None
        best = None
        best_quality: dict | None = None
        attempts = (retries + 1) if verify_model else 1
        for attempt in range(1, attempts + 1):
            parts = []
            for result in model.generate(text=chunk, **kwargs):
                parts.append(np.asarray(result.audio, dtype=np.float32).reshape(-1))
            if not parts:
                break
            candidate = np.concatenate(parts)
            if not verify_model:
                piece = candidate
                break

            quality = verify_chunk(
                candidate, chunk, model=verify_model, language="en"
            )
            score = (
                quality["max_expected_gap"] * 10
                + quality["max_added_span"] * 10
                + quality["wer"]
            )
            best_score = (
                best_quality["max_expected_gap"] * 10
                + best_quality["max_added_span"] * 10
                + best_quality["wer"]
                if best_quality
                else float("inf")
            )
            if score < best_score:
                best_quality, best = quality, candidate
            if quality["passed"]:
                piece = candidate
                worst_wer = max(worst_wer, quality["wer"])
                break

            rerolls += 1
            print(
                f"    chunk {index} attempt {attempt}/{attempts} rejected: "
                f"wer={quality['wer']:.3f} cov={quality['coverage']:.3f} "
                f"gap={quality['max_expected_gap']} add={quality['max_added_span']}",
                flush=True,
            )
            if attempt == attempts:
                piece = best
                assert best_quality is not None
                worst_wer = max(worst_wer, best_quality["wer"])
                unresolved.append(
                    {
                        "chunk": index,
                        "wer": best_quality["wer"],
                        "coverage": best_quality["coverage"],
                        "max_expected_gap": best_quality["max_expected_gap"],
                        "max_added_span": best_quality["max_added_span"],
                        "suspicious_spans": best_quality["suspicious_spans"],
                        "text": chunk[:160],
                    }
                )
        if piece is None:
            unresolved.append({"chunk": index, "wer": None, "text": chunk[:120]})
            continue

        piece, _ = suppress_onset_transient(piece)
        piece, cut = trim_tail_artifact(piece)
        if cut > 0.02:
            tail_trimmed += cut
        piece, fixed = declick(piece)
        clicks += fixed
        levels.append(float(np.sqrt((piece.astype(np.float64) ** 2).mean())))
        piece = soften_edges(match_level(piece, target_rms_dbfs), fade_ms)
        boundaries.append(
            [round(cursor / SAMPLE_RATE, 3), round((cursor + piece.size) / SAMPLE_RATE, 3)]
        )
        cursor += piece.size
        pieces.append(piece)
        if index < len(chunks):
            # Room tone rather than digital zero: true silence between
            # paragraphs is itself audible as a dropout.
            gap = room_tone(piece, pause.size)
            pieces.append(gap)
            cursor += gap.size

    if not pieces:
        return np.zeros(0, dtype=np.float32), {"chunks": len(chunks), "failed": True}

    joined = np.concatenate(pieces)
    peak = float(np.abs(joined).max())
    if peak > 1.0:
        joined = joined / peak * 0.98
    spread = 0.0
    if levels and min(levels) > 0:
        spread = float(20 * np.log10(max(levels) / min(levels)))
    return joined, {
        "label": label,
        "chunks": len(chunks),
        "seconds": round(joined.size / SAMPLE_RATE, 2),
        "worst_chunk_wer": round(worst_wer, 4),
        "rerolls": rerolls,
        "clicks_repaired": clicks,
        "tail_trimmed_seconds": round(tail_trimmed, 3),
        "chunk_boundaries": boundaries,
        "loudness_spread_db": round(spread, 2),
        "unresolved_chunks": unresolved,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=128)
    parser.add_argument(
        "--chapter",
        type=int,
        action="append",
        default=None,
        help="Render only this chapter; repeatable. Overrides --start/--end.",
    )
    parser.add_argument("--manuscript-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--ref-audio", type=Path, required=True)
    parser.add_argument("--ref-text", required=True)
    parser.add_argument("--voice-tag", default="qwen3-emns")
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--temperature", type=float, default=0.7)
    parser.add_argument("--top-k", type=int, default=40)
    parser.add_argument("--top-p", type=float, default=0.95)
    parser.add_argument("--repetition-penalty", type=float, default=1.5)
    parser.add_argument("--max-chunk-chars", type=int, default=3_200)
    parser.add_argument("--pause-ms", type=int, default=900)
    parser.add_argument("--target-rms-dbfs", type=float, default=-20.0)
    parser.add_argument("--fade-ms", type=float, default=25.0)
    parser.add_argument(
        "--verify-model", default="mlx-community/whisper-large-v3-turbo"
    )
    parser.add_argument("--no-verify", dest="verify", action="store_false", default=True)
    parser.add_argument("--chunk-retries", type=int, default=2)
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument("--dedication", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()

    if args.chapter:
        chapters = [
            discover_chapters([args.manuscript_root], number, number)[0]
            for number in sorted(set(args.chapter))
        ]
    else:
        chapters = discover_chapters([args.manuscript_root], args.start, args.end)
    from mlx_audio.tts.utils import load_model

    print(f"loading {args.model} once for {len(chapters)} chapter(s)…", flush=True)
    model = load_model(args.model)
    verify_model = args.verify_model if args.verify else None

    kwargs = {
        "max_tokens": args.max_tokens,
        "temperature": args.temperature,
        "top_k": args.top_k,
        "top_p": args.top_p,
        "repetition_penalty": args.repetition_penalty,
        "split_pattern": None,
        "ref_audio": str(args.ref_audio),
        "ref_text": args.ref_text,
    }
    common = dict(
        kwargs=kwargs,
        pause_ms=args.pause_ms,
        max_chunk_chars=args.max_chunk_chars,
        verify_model=verify_model,
        retries=args.chunk_retries,
        target_rms_dbfs=args.target_rms_dbfs,
        fade_ms=args.fade_ms,
    )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    reports: list[dict] = []
    started = time.time()

    jobs: list[tuple[Path, Path, str]] = []
    if args.dedication and args.dedication.is_file():
        jobs.append(
            (
                args.dedication,
                args.output_dir / f"002-dedication-{args.voice_tag}.wav",
                "dedication",
            )
        )
    for number, path in chapters:
        jobs.append(
            (
                path,
                args.output_dir
                / f"{4 + number:03d}-chapter-{number:03d}-{args.voice_tag}.wav",
                f"chapter {number}",
            )
        )

    for source, out, label in jobs:
        if args.skip_existing and out.exists():
            print(f"SKIP {label} ({out.name})", flush=True)
            continue
        t0 = time.time()
        print(f"=== {label}: {source.name} -> {out.name}", flush=True)
        audio, info = render_chapter(model, extract_body(source), label=label, **common)
        if audio.size == 0:
            print(f"  FAILED {label}", flush=True)
            reports.append(info)
            continue
        sf.write(str(out), audio, SAMPLE_RATE)
        elapsed = time.time() - t0
        info["render_seconds"] = round(elapsed, 1)
        info["realtime_factor"] = round(info["seconds"] / max(elapsed, 1e-6), 2)
        reports.append(info)
        print(
            f"  {info['seconds']/60:5.2f} min in {elapsed/60:4.2f} min "
            f"({info['realtime_factor']:.2f}x) · {info['chunks']} chunks · "
            f"worst chunk wer={info['worst_chunk_wer']:.3f} · rerolls={info['rerolls']} · "
            f"clicks={info['clicks_repaired']} · tails={info['tail_trimmed_seconds']:.2f}s · "
            f"spread={info['loudness_spread_db']:.1f}dB",
            flush=True,
        )
        if info["unresolved_chunks"]:
            for item in info["unresolved_chunks"]:
                print(
                    f"  ! chunk {item['chunk']} wer={item['wer']} — LISTEN: "
                    f"{item['text'][:80]}",
                    flush=True,
                )
        if args.report:
            args.report.parent.mkdir(parents=True, exist_ok=True)
            args.report.write_text(json.dumps(reports, indent=2))

    total = time.time() - started
    audio_total = sum(r.get("seconds", 0) for r in reports)
    flagged = [r for r in reports if r.get("unresolved_chunks")]
    print(
        f"\nDone {len(reports)} item(s) in {total/60:.1f} min wall — "
        f"{audio_total/3600:.2f} h audio "
        f"({audio_total/max(total,1e-6):.2f}x realtime)"
    )
    print(f"items with an unresolved chunk (worth a listen): {len(flagged)}")
    for r in flagged:
        print(f"  {r['label']}: {[c['chunk'] for c in r['unresolved_chunks']]}")


if __name__ == "__main__":
    main()
