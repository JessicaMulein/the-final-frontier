#!/usr/bin/env python3
"""Resumable full-book wrapper for the validated pure-C qvoice renderer."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from batch_render_chatterbox import discover_chapters  # noqa: E402
from spoken_text import spoken_sha256  # noqa: E402


def manifest_passed(path: Path) -> bool:
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text())
        return bool(data.get("assembly", {}).get("chapter_quality", {}).get("passed"))
    except (OSError, json.JSONDecodeError):
        return False


def manifest_current(path: Path, source: Path) -> bool:
    """Whether a passing manifest narrates the text `source` holds *now*.

    A manifest written before `spoken_sha256` existed cannot answer this, so it
    is treated as not current and the chapter re-renders once. That is the safe
    direction: the cost is one render, and the alternative is shipping audio of
    superseded prose.
    """
    if not path.is_file():
        return False
    try:
        recorded = json.loads(path.read_text()).get("spoken_sha256")
    except (OSError, json.JSONDecodeError):
        return False
    if not isinstance(recorded, str) or not recorded:
        return False
    return recorded == spoken_sha256(source)


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--start", type=int, default=1)
    p.add_argument("--end", type=int, default=128)
    p.add_argument("--chapter", type=int, action="append", default=None)
    p.add_argument("--manuscript-root", type=Path, required=True)
    p.add_argument("--output-dir", type=Path, required=True)
    p.add_argument("--work-root", type=Path, required=True)
    p.add_argument("--binary", type=Path, required=True)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--voice", type=Path, required=True)
    p.add_argument("--dedication", type=Path, default=None)
    p.add_argument("--voice-tag", default="qvoice-uks03")
    p.add_argument("--skip-existing", action="store_true")
    p.add_argument("--continue-on-error", action="store_true", default=True)
    p.add_argument(
        "--instruction",
        default=(
            "Read slowly, clearly, and naturally. Maintain a measured literary "
            "pace without sounding like an announcer."
        ),
    )
    p.add_argument(
        "--dedication-instruction",
        default=(
            "Read this dedication warmly, directly, and with quiet gratitude. "
            "Address Hannah and Dan with confidence and affection. Keep the tone "
            "sincere and grounded, not mournful, uncertain, dramatic, or confused."
        ),
    )
    args = p.parse_args()

    for name in (
        "manuscript_root",
        "output_dir",
        "work_root",
        "binary",
        "model",
        "voice",
    ):
        setattr(args, name, getattr(args, name).resolve())
    if args.dedication:
        args.dedication = args.dedication.resolve()

    if args.chapter:
        chapters = [
            discover_chapters([args.manuscript_root], number, number)[0]
            for number in sorted(set(args.chapter))
        ]
    else:
        chapters = discover_chapters(
            [args.manuscript_root], args.start, args.end
        )

    args.output_dir.mkdir(parents=True, exist_ok=True)
    args.work_root.mkdir(parents=True, exist_ok=True)
    log_dir = args.work_root / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    jobs: list[tuple[str, Path, Path, Path]] = []
    if args.dedication and args.dedication.is_file():
        jobs.append(
            (
                "dedication",
                args.dedication,
                args.output_dir / f"002-dedication-{args.voice_tag}.wav",
                args.work_root / "dedication",
            )
        )
    for number, source in chapters:
        jobs.append(
            (
                f"chapter {number}",
                source,
                args.output_dir
                / f"{4 + number:03d}-chapter-{number:03d}-{args.voice_tag}.wav",
                args.work_root / f"chapter-{number:03d}",
            )
        )

    renderer = Path(__file__).resolve().parent / "render_chapter_qvoice.py"
    records = []
    started = time.time()
    failures = []

    for index, (label, source, output, work) in enumerate(jobs, start=1):
        manifest = work / "manifest.json"
        if args.skip_existing and output.is_file() and manifest_passed(manifest):
            # Skipping requires a passing render *of the current text*. The
            # dedication is sourced from front matter rather than a chapter file,
            # so it is exempt from the chapter-text check.
            if label == "dedication" or manifest_current(manifest, source):
                print(
                    f"SKIP [{index}/{len(jobs)}] {label}: passing current output exists",
                    flush=True,
                )
                records.append(
                    {"label": label, "status": "skipped", "output": str(output)}
                )
                continue
            print(
                f"STALE [{index}/{len(jobs)}] {label}: prose changed since render",
                flush=True,
            )

        print(f"=== [{index}/{len(jobs)}] {label}: {source.name}", flush=True)
        log = log_dir / f"{work.name}.log"
        command = [
            sys.executable,
            str(renderer),
            str(source),
            "--output",
            str(output),
            "--work-dir",
            str(work),
            "--binary",
            str(args.binary),
            "--model",
            str(args.model),
            "--voice",
            str(args.voice),
            "--instruction",
            args.dedication_instruction if label == "dedication" else args.instruction,
            "--chunk-chars",
            "1000",
            "--primary-seed",
            "70",
            "--attempts",
            "6",
            "--temperature",
            "0.5",
            "--rate",
            "0.92",
            "--pause-ms",
            "650",
        ]
        t0 = time.time()
        with log.open("w") as handle:
            result = subprocess.run(
                command,
                text=True,
                stdout=handle,
                stderr=subprocess.STDOUT,
            )
        elapsed = time.time() - t0
        passed = result.returncode == 0 and output.is_file() and manifest_passed(manifest)
        record = {
            "label": label,
            "status": "passed" if passed else "failed",
            "exit": result.returncode,
            "seconds_wall": round(elapsed, 1),
            "output": str(output),
            "manifest": str(manifest),
            "log": str(log),
        }
        if manifest.is_file():
            try:
                data = json.loads(manifest.read_text())
                record["audio_seconds"] = data.get("assembly", {}).get("seconds")
                record["chapter_quality"] = data.get("assembly", {}).get(
                    "chapter_quality"
                )
                record["chunk_count"] = len(data.get("chunks", []))
                record["fallback_chunks"] = [
                    chunk["index"]
                    for chunk in data.get("chunks", [])
                    if chunk.get("seed") != 70
                ]
            except (OSError, json.JSONDecodeError):
                pass
        records.append(record)
        (args.work_root / "batch-report.json").write_text(json.dumps(records, indent=2))
        print(
            f"  {'PASS' if passed else 'FAIL'} in {elapsed / 60:.1f} min"
            + (
                f" · {record.get('audio_seconds', 0) / 60:.1f} min audio"
                f" · {record.get('chunk_count', '?')} chunks"
                f" · fallback {record.get('fallback_chunks', [])}"
                if passed
                else f" · see {log}"
            ),
            flush=True,
        )
        if not passed:
            failures.append(label)
            if not args.continue_on_error:
                break

    total = time.time() - started
    print(
        f"\nDone: {len(records)} job(s), {len(failures)} failure(s), "
        f"{total / 60:.1f} min wall",
        flush=True,
    )
    if failures:
        print("Failures: " + ", ".join(failures), flush=True)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
