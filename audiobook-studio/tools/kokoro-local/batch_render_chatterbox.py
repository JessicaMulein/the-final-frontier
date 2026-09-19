#!/usr/bin/env python3
"""Batch-render manuscript chapters with Chatterbox (model loaded once).

Local audition tooling only — does not touch the Nova production path.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import asdict
from pathlib import Path

from mlx_audio.tts.utils import load_model

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_chapter_chatterbox import (  # noqa: E402
    MODEL_ID,
    SpeechUnit,
    assemble_units,
    chunk_paragraphs,
    chunk_sentences,
    extract_body,
    units_from_paragraph_chunks,
)
from validate_stt import (  # noqa: E402
    REPO_ROOT,
    expected_text_for_chapter,
    validate_one,
)
from detect_loops import analyse as analyse_loops  # noqa: E402
from detect_loops import transcribe_full  # noqa: E402
import soundfile as sf  # noqa: E402

CHAPTER_RE = re.compile(r"(?:^|/)(?:\w+-)*?(\d{3})-")


def discover_chapters(roots: list[Path], start: int, end: int) -> list[tuple[int, Path]]:
    found: dict[int, Path] = {}
    for root in roots:
        for path in sorted(root.rglob("*.md")):
            m = CHAPTER_RE.search(path.as_posix())
            if not m:
                continue
            n = int(m.group(1))
            if start <= n <= end:
                found.setdefault(n, path)
    missing = [n for n in range(start, end + 1) if n not in found]
    if missing:
        raise SystemExit(f"Missing chapter files for: {missing}")
    return [(n, found[n]) for n in range(start, end + 1)]


def render_one(
    model,
    chapter_path: Path,
    output_path: Path,
    *,
    ref_audio: str,
    exaggeration: float,
    cfg_weight: float,
    pause_ms: int,
    chunk_mode: str,
    gate_breaths: bool,
) -> float:
    body = extract_body(chapter_path)
    if chunk_mode == "sentences":
        units = chunk_sentences(body)
        if units:
            units = [
                *units[:-1],
                SpeechUnit(text=units[-1].text, pause_after_ms=0),
            ]
    else:
        units = units_from_paragraph_chunks(chunk_paragraphs(body), pause_ms)

    joined = assemble_units(
        model,
        units,
        ref_audio=ref_audio,
        exaggeration=exaggeration,
        cfg_weight=cfg_weight,
        gate_breaths=gate_breaths,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), joined, 24_000)
    return joined.shape[0] / 24_000


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=30)
    parser.add_argument("--ref-audio", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--manuscript-root",
        type=Path,
        default=Path("The Final Frontier Novel/chapters"),
    )
    parser.add_argument("--exaggeration", type=float, default=0.7)
    parser.add_argument("--cfg-weight", type=float, default=0.3)
    parser.add_argument("--chunk-mode", choices=("sentences", "paragraphs"), default="sentences")
    parser.add_argument("--pause-ms", type=int, default=350)
    parser.add_argument(
        "--gate-breaths",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--voice-tag", default="chatterbox-uk-s03")
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument(
        "--stt-recheck",
        action=argparse.BooleanOptionalAction,
        default=False,
        help="After each chapter, STT-validate and optionally re-render on FAIL",
    )
    parser.add_argument(
        "--stt-retries",
        type=int,
        default=1,
        help="Extra full re-renders after an STT FAIL (default 1)",
    )
    parser.add_argument("--stt-wer-fail", type=float, default=0.12)
    parser.add_argument("--stt-insert-fail", type=int, default=12)
    parser.add_argument("--stt-suspicious-fail", type=int, default=15)
    parser.add_argument(
        "--stt-model",
        default="mlx-community/whisper-large-v3-turbo",
    )
    parser.add_argument("--stt-language", default="en")
    parser.add_argument(
        "--stt-report",
        type=Path,
        default=None,
        help="JSONL append path for per-chapter STT results",
    )
    parser.add_argument(
        "--loop-check",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Also gate on loop/babble/dropped-content (detect_loops). The WER "
        "gate alone passes renders containing 30s of babble, so keep this on.",
    )
    args = parser.parse_args()

    roots = [args.manuscript_root]
    chapters = discover_chapters(roots, args.start, args.end)
    ref = str(args.ref_audio.resolve())
    manuscript_root = args.manuscript_root
    # validate_stt expects novel root (parent of chapters/) when given the chapters dir
    if manuscript_root.name == "chapters":
        manuscript_root = manuscript_root.parent
    stt_report = args.stt_report
    if args.stt_recheck and stt_report is None:
        stt_report = (
            REPO_ROOT
            / "audiobook/kokoro-audition/chatterbox-v2"
            / f"stt-batch-{args.start:03d}-{args.end:03d}.jsonl"
        )
    print(f"Loading {MODEL_ID} once for {len(chapters)} chapters…", flush=True)
    model = load_model(MODEL_ID)
    t0 = time.time()
    stt_failures = 0
    for chapter_num, path in chapters:
        sequence = 4 + chapter_num
        out = args.output_dir / f"{sequence:03d}-chapter-{chapter_num:03d}-{args.voice_tag}.wav"
        if args.skip_existing and out.exists():
            print(f"SKIP chapter {chapter_num} ({out.name})", flush=True)
            continue
        attempts = 1 + (args.stt_retries if args.stt_recheck else 0)
        passed = not args.stt_recheck
        for attempt in range(1, attempts + 1):
            print(
                f"=== chapter {chapter_num}: {path.name} → {out.name}"
                + (f" (attempt {attempt}/{attempts})" if attempts > 1 else ""),
                flush=True,
            )
            started = time.time()
            seconds = render_one(
                model,
                path,
                out,
                ref_audio=ref,
                exaggeration=args.exaggeration,
                cfg_weight=args.cfg_weight,
                pause_ms=args.pause_ms,
                chunk_mode=args.chunk_mode,
                gate_breaths=args.gate_breaths,
            )
            print(
                f"Wrote {out} ({seconds/60:.1f} min audio, {time.time()-started:.0f}s render)",
                flush=True,
            )
            if not args.stt_recheck:
                break

            # One whisper pass feeds both gates.
            transcript, segments = transcribe_full(
                out, model=args.stt_model, language=args.stt_language
            )
            report = validate_one(
                out,
                manuscript_root=manuscript_root,
                model=args.stt_model,
                language=args.stt_language,
                wer_fail=args.stt_wer_fail,
                insert_fail=args.stt_insert_fail,
                suspicious_fail=args.stt_suspicious_fail,
                transcript=transcript,
            )
            status = "PASS" if report.passed else "FAIL"
            print(
                f"  STT {status} wer={report.wer:.3f} suspicious={report.suspicious_replaces} "
                f"ins={report.insert_ops} del={report.delete_ops} repl={report.replace_ops}",
                flush=True,
            )
            for ex in report.suspicious_examples[:5]:
                print(f"  ~ {ex['expected']!r} → {ex['transcript']!r}", flush=True)

            loop_report = None
            loop_ok = True
            if args.loop_check:
                expected_raw, _ = expected_text_for_chapter(
                    manuscript_root, chapter_num
                )
                loop_report = analyse_loops(
                    out,
                    expected_raw,
                    whisper_model=args.stt_model,
                    language=args.stt_language,
                    segments=segments,
                    transcript_text=transcript,
                )
                loop_ok = loop_report.passed
                print(
                    f"  LOOP {'PASS' if loop_ok else 'FAIL'} "
                    f"pace={loop_report.words_per_second:.2f}wps "
                    f"coverage={loop_report.word_coverage:.3f} "
                    f"stalled={loop_report.stalled_seconds:.1f}s "
                    f"repeated={loop_report.repeated_seconds:.1f}s",
                    flush=True,
                )
                for finding in loop_report.findings[:5]:
                    print(
                        f"  ! [{finding['kind']}] "
                        f"{finding['start']:.1f}-{finding['end']:.1f}s "
                        f"{finding['detail']}",
                        flush=True,
                    )

            if stt_report is not None:
                stt_report.parent.mkdir(parents=True, exist_ok=True)
                with stt_report.open("a", encoding="utf-8") as fh:
                    fh.write(
                        json.dumps(
                            {
                                "attempt": attempt,
                                "attempts": attempts,
                                **asdict(report),
                                "loop": asdict(loop_report) if loop_report else None,
                            }
                        )
                        + "\n"
                    )

            if report.passed and loop_ok:
                passed = True
                break
            if attempt < attempts:
                out.unlink(missing_ok=True)
                reason = []
                if not report.passed:
                    reason.append("STT")
                if not loop_ok:
                    reason.append("LOOP")
                print(
                    f"  {'+'.join(reason)} FAIL — re-rendering chapter {chapter_num}",
                    flush=True,
                )
        if args.stt_recheck and not passed:
            stt_failures += 1
            print(
                f"  still FAIL after {attempts} attempt(s); keeping last render",
                flush=True,
            )
    print(
        f"Done chapters {args.start}-{args.end} in {(time.time()-t0)/60:.1f} min wall"
        + (f" (stt_failures={stt_failures})" if args.stt_recheck else ""),
        flush=True,
    )


if __name__ == "__main__":
    main()
