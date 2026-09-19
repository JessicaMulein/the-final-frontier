#!/usr/bin/env python3
"""Render the whole book with Fish S2 Pro, resumably, and report what to listen to.

Settings are the ones the listener approved on chapter 3: the `hifitts-clean-92`
reference, the interior-memoir direction, 650 ms of shaped room tone between
paragraphs, and `[short pause]` between sentences. They are not exposed as knobs
here on purpose — a book should be one voice, and a flag that drifts mid-run is how
chapter 60 stops matching chapter 3.

Resumability is the point. At the measured RTF of 1.33 this is roughly a 20-hour
job, so it must survive being interrupted, and it must never silently redo work.
A chapter is skipped only if its audio exists AND its manifest records a pass, so a
half-written file from a kill is regenerated rather than trusted.

What this does NOT do is certify the output. A passing chapter here means no
text-level problem was found. The defect class that cost this project a session --
an intra-word stutter that Whisper normalises into the correct token -- is not
detectable by anything in this script, and the acoustic judges are not built yet.
The listen list it emits is therefore a triage aid, not a guarantee.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CHAPTERS = REPO / "The Final Frontier Novel/chapters"
HERE = Path(__file__).resolve().parent

# Delivery naming already established in audiobook/: sequence = 4 + chapter.
SEQUENCE_OFFSET = 4
VOICE_TAG = "fish-clean92"


def inventory() -> list[tuple[int, Path]]:
    """(chapter number, path) for every chapter, ordered by the front matter."""
    found: dict[int, Path] = {}
    for path in sorted(CHAPTERS.glob("*/*.md")):
        head = path.read_text(errors="replace")[:800]
        match = re.search(r"^chapter:\s*(\d+)", head, re.M)
        if not match:
            continue
        number = int(match.group(1))
        if number in found:
            raise SystemExit(f"duplicate chapter {number}: {path} and {found[number]}")
        found[number] = path
    return sorted(found.items())


def output_for(out_dir: Path, number: int) -> Path:
    return out_dir / f"{SEQUENCE_OFFSET + number:03d}-chapter-{number:03d}-{VOICE_TAG}.wav"


def already_done(wav: Path) -> dict | None:
    """Manifest of a previous successful render, or None if it must be redone."""
    manifest = wav.with_suffix(".manifest.json")
    if not wav.is_file() or not manifest.is_file():
        return None
    try:
        data = json.loads(manifest.read_text())
    except json.JSONDecodeError:
        return None
    quality = data.get("assembly", {}).get("chapter_quality")
    if not quality or not quality.get("passed"):
        return None
    if wav.stat().st_size < 1_000_000:
        return None
    return data


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    # Deliverables belong in the repo's `audiobook/` directory, which is reserved
    # for final output only: the WAVs, the MP3s derived from them, and the M4B.
    # Tooling inputs, provenance and superseded renders live under `audiobook-studio/`.
    p.add_argument("--out-dir", type=Path, default=REPO / "audiobook")
    p.add_argument("--first", type=int, default=1)
    p.add_argument("--last", type=int, default=128)
    p.add_argument("--reference", default="hifitts-clean-92")
    p.add_argument(
        "--retries",
        type=int,
        default=1,
        help="re-render a chapter this many extra times if QA fails",
    )
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    chapters = [(n, path) for n, path in inventory() if args.first <= n <= args.last]
    print(f"{len(chapters)} chapters in range {args.first}-{args.last}")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    pending, skipped = [], []
    for number, path in chapters:
        if already_done(output_for(args.out_dir, number)):
            skipped.append(number)
        else:
            pending.append((number, path))
    print(f"  {len(skipped)} already rendered and passing, {len(pending)} to do")
    if skipped:
        print(f"  skipping: {_ranges(skipped)}")

    if args.dry_run:
        for number, path in pending[:10]:
            print(f"  would render {number:3d}  {path.name}")
        if len(pending) > 10:
            print(f"  ... and {len(pending) - 10} more")
        return

    report_path = args.out_dir / "book-report.json"
    report = json.loads(report_path.read_text()) if report_path.is_file() else {}

    started = time.perf_counter()
    failures = []
    for index, (number, path) in enumerate(pending, start=1):
        wav = output_for(args.out_dir, number)
        elapsed = time.perf_counter() - started
        rate = elapsed / max(1, index - 1) if index > 1 else 0.0
        eta = rate * (len(pending) - index + 1) / 3600 if rate else 0.0
        print(
            f"\n=== [{index}/{len(pending)}] chapter {number} {path.name}"
            + (f"  (eta {eta:.1f} h)" if eta else ""),
            flush=True,
        )

        outcome = None
        for attempt in range(args.retries + 1):
            result = subprocess.run(
                [
                    sys.executable,
                    str(HERE / "render_chapter_fish.py"),
                    str(path),
                    "--output",
                    str(wav),
                    "--reference",
                    args.reference,
                ],
                cwd=HERE,
                capture_output=True,
                text=True,
            )
            tail = [
                line
                for line in result.stdout.splitlines()
                if line.startswith(("wrote", "  WER", "  articulation"))
            ]
            for line in tail:
                print("   ", line.strip(), flush=True)
            if result.returncode != 0:
                print(f"    render exit {result.returncode}", flush=True)
                snippet = (result.stderr or "").strip().splitlines()[-3:]
                for line in snippet:
                    print(f"    {line}", flush=True)

            outcome = already_done(wav)
            if outcome:
                break
            if attempt < args.retries:
                print("    QA did not pass; retrying", flush=True)

        if not outcome:
            failures.append(number)
            report[str(number)] = {"chapter": number, "file": wav.name, "passed": False}
        else:
            assembly = outcome["assembly"]
            quality = assembly["chapter_quality"]
            report[str(number)] = {
                "chapter": number,
                "file": wav.name,
                "passed": True,
                "minutes": round(assembly["seconds"] / 60, 2),
                "wer": quality["wer"],
                "coverage": quality["coverage"],
                "articulation_first_third": assembly.get("articulation_first_third"),
                "articulation_last_third": assembly.get("articulation_last_third"),
                "suspicious_spans": quality.get("suspicious_spans", []),
            }
        report_path.write_text(json.dumps(report, indent=2))

    _summarise(report, args.out_dir, failures)


def _ranges(numbers: list[int]) -> str:
    numbers = sorted(numbers)
    out, start, previous = [], numbers[0], numbers[0]
    for n in numbers[1:]:
        if n == previous + 1:
            previous = n
            continue
        out.append(f"{start}" if start == previous else f"{start}-{previous}")
        start = previous = n
    out.append(f"{start}" if start == previous else f"{start}-{previous}")
    return ", ".join(out)


def _summarise(report: dict, out_dir: Path, failures: list[int]) -> None:
    passing = [r for r in report.values() if r.get("passed")]
    minutes = sum(r.get("minutes", 0.0) for r in passing)
    print(
        f"\n{len(passing)} chapters passing, {len(failures)} failed, "
        f"{minutes / 60:.1f} h of audio"
    )

    # Triage, ordered by how much attention each chapter probably needs.
    listen = []
    for r in passing:
        reasons = []
        first = r.get("articulation_first_third")
        last = r.get("articulation_last_third")
        if first and last and first > 0:
            drop = (first - last) / first
            if drop > 0.10:
                reasons.append(f"articulation -{drop * 100:.0f}% across chapter")
        if r.get("wer", 0) > 0.05:
            reasons.append(f"WER {r['wer']:.3f}")
        if r.get("coverage", 1.0) < 0.99:
            reasons.append(f"coverage {r['coverage']:.3f}")
        spans = r.get("suspicious_spans") or []
        if len(spans) > 4:
            reasons.append(f"{len(spans)} suspicious spans")
        if reasons:
            listen.append({"chapter": r["chapter"], "file": r["file"], "reasons": reasons})

    listen.sort(key=lambda x: -len(x["reasons"]))
    path = out_dir / "listen-list.json"
    path.write_text(
        json.dumps(
            {
                "note": "Triage only. Text metrics cannot see intra-word stutters; "
                "the acoustic judges are not built yet.",
                "failed_chapters": failures,
                "listen": listen,
            },
            indent=2,
        )
    )
    print(f"listen list: {len(listen)} chapters flagged -> {path}")
    if failures:
        print(f"FAILED (no passing render): {_ranges(failures)}")
    for item in listen[:10]:
        print(f"  ch {item['chapter']:3d}  {'; '.join(item['reasons'])}")


if __name__ == "__main__":
    main()
