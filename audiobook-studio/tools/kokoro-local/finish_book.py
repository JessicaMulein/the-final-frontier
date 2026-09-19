#!/usr/bin/env python3
"""Wait for a batch render to finish, then verify every chapter and encode MP3s.

Local audition tooling only — does not touch the Nova production path.

Polls the batch log for its completion line, then runs two steps that would
otherwise need babysitting:

  1. `detect_loops.py` over every chapter WAV — report only, nothing is moved or
     deleted. Failures are listed for a human to judge.
  2. `wav_to_mp3.py --skip-existing` to bring the MP3 set up to date.

Both steps are also safe to run mid-render (WAVs newer than the settle window
are skipped), so this can be started at any point.

Example
-------
  PY=.venv/bin/python
  $PY finish_book.py \
      --batch-log ../../../audiobook/kokoro-audition/chatterbox-emns-n599/batch-full-run-3.log \
      --audio-dir ../../../audiobook \
      --manuscript-root "../../../The Final Frontier Novel" \
      --voice-tag chatterbox-emns-n599
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PYTHON = sys.executable
DONE_MARKER = "Done chapters"


def wait_for_batch(log: Path, *, poll_seconds: float, timeout_hours: float) -> bool:
    """Return True once the log shows completion, False on timeout."""
    deadline = time.time() + timeout_hours * 3600
    last_seen = -1
    while time.time() < deadline:
        if log.is_file():
            text = log.read_text(errors="replace")
            if DONE_MARKER in text:
                for line in text.splitlines():
                    if DONE_MARKER in line:
                        print(f"batch finished: {line.strip()}", flush=True)
                return True
            rendered = text.count("Wrote ")
            if rendered != last_seen:
                print(f"  … {rendered} chapter render(s) written so far", flush=True)
                last_seen = rendered
        time.sleep(poll_seconds)
    print("timed out waiting for the batch to finish", flush=True)
    return False


def run(cmd: list[str], *, label: str) -> int:
    print(f"\n===== {label}\n$ {' '.join(cmd)}", flush=True)
    proc = subprocess.run(cmd, cwd=HERE)
    print(f"----- {label} exit={proc.returncode}", flush=True)
    return proc.returncode


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--batch-log", type=Path, required=True)
    parser.add_argument("--audio-dir", type=Path, required=True)
    parser.add_argument("--manuscript-root", type=Path, required=True)
    parser.add_argument("--voice-tag", required=True)
    parser.add_argument("--mp3-dir", type=Path, default=None)
    parser.add_argument("--report-dir", type=Path, default=None)
    parser.add_argument("--total-chapters", type=int, default=128)
    parser.add_argument("--poll-seconds", type=float, default=60.0)
    parser.add_argument("--timeout-hours", type=float, default=14.0)
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=300.0,
        help="Ignore WAVs newer than this, in case a render is still going",
    )
    parser.add_argument(
        "--skip-wait",
        action="store_true",
        help="Verify and encode immediately instead of waiting for the batch",
    )
    args = parser.parse_args()

    mp3_dir = args.mp3_dir or (args.audio_dir / "mp3")
    report_dir = args.report_dir or (
        args.audio_dir / "kokoro-audition" / args.voice_tag
    )

    if not args.skip_wait:
        print(f"waiting on {args.batch_log}", flush=True)
        if not wait_for_batch(
            args.batch_log,
            poll_seconds=args.poll_seconds,
            timeout_hours=args.timeout_hours,
        ):
            print("continuing anyway with whatever has settled", flush=True)
        # Let the final file settle before touching it.
        time.sleep(args.settle_seconds)

    wavs = sorted(
        p
        for p in args.audio_dir.glob(f"*-chapter-*-{args.voice_tag}.wav")
        if p.is_file()
    )
    print(f"\n{len(wavs)} chapter WAV(s) present", flush=True)

    verify_rc = 1
    if wavs:
        verify_rc = run(
            [
                PYTHON, "detect_loops.py", *[str(p) for p in wavs],
                "--manuscript-root", str(args.manuscript_root),
                "--settle-seconds", str(args.settle_seconds),
                "--report", str(report_dir / "final-verify.json"),
            ],
            label="verify all chapters (report only, nothing moved)",
        )

    encode_rc = run(
        [
            PYTHON, "wav_to_mp3.py",
            "--audio-dir", str(args.audio_dir),
            "--manuscript-root", str(args.manuscript_root / "chapters")
            if (args.manuscript_root / "chapters").is_dir()
            else str(args.manuscript_root),
            "--voice-tag", args.voice_tag,
            "--out-dir", str(mp3_dir),
            "--total-chapters", str(args.total_chapters),
            "--settle-seconds", str(args.settle_seconds),
            "--skip-existing",
        ],
        label="encode MP3s",
    )

    mp3s = sorted(mp3_dir.glob("*.mp3")) if mp3_dir.is_dir() else []
    print(
        f"\nsummary: {len(wavs)} wav(s), {len(mp3s)} mp3(s), "
        f"verify_exit={verify_rc} (0 = all chapters clean), encode_exit={encode_rc}"
    )
    missing = args.total_chapters - len(mp3s)
    if missing > 0:
        print(f"still to come: {missing} chapter(s)")


if __name__ == "__main__":
    main()
