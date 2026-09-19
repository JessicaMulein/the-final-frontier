#!/usr/bin/env python3
"""Per-chapter audio state, the listen queue, and the approval ledger.

Local audition tooling only — does not touch the Nova production path.

The rule this enforces
---------------------
A changed chapter must be re-rendered, must pass its automated gates, and must
then be *listened to by a human* before it can enter a packaged M4B. Machine
gates measure content fidelity. They are blind to delivery — the renderer's own
comment says so: whisper reads slurred speech as correct. So a passing gate is a
precondition for a listen, never a substitute for one.

Approval is bound to the text, not to the chapter number
-------------------------------------------------------
Every ledger entry records the `spoken_sha256` it approved. Nothing ever has to
remember to un-approve a chapter: edit the prose and the digest changes, so the
old approval simply stops matching and the chapter reappears in the queue. There
is no revocation step to forget.

States
------
    missing      no render on disk
    stale        a render exists, but of superseded prose
    failed       rendered, automated gates did not pass
    unlistened   rendered, gates passed, awaiting a human listen  <- the queue
    rejected     a human listened to this exact text and rejected it
    accepted     a human listened to this exact text and accepted it

Only `accepted` chapters may be packaged.

Runs on plain python3 — no mlx, no Metal, no venv — so it is usable from a hook,
from CI, or while a render is occupying the GPU.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from spoken_text import discover_chapters, spoken_sha256, text_version  # noqa: E402

LEDGER_SCHEMA_VERSION = 1
BOOK_ID = "the-final-frontier"

MISSING = "missing"
STALE = "stale"
FAILED = "failed"
UNLISTENED = "unlistened"
REJECTED = "rejected"
ACCEPTED = "accepted"

# Report order: worst first, so the top of the table is the work.
STATE_ORDER = (MISSING, STALE, FAILED, REJECTED, UNLISTENED, ACCEPTED)

PACKAGEABLE = (ACCEPTED,)
NEEDS_RENDER = (MISSING, STALE, FAILED, REJECTED)
NEEDS_LISTEN = (UNLISTENED,)


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


@dataclass(frozen=True)
class ChapterState:
    chapter: int
    source: Path
    spoken_sha256: str
    state: str
    wav: Path
    wav_exists: bool
    manifest_sha256: str | None
    gates_passed: bool | None
    wer: float | None
    coverage: float | None
    audio_seconds: float | None
    fallback_chunks: tuple[int, ...]
    listened_at: str | None
    note: str | None

    @property
    def packageable(self) -> bool:
        return self.state in PACKAGEABLE


# --------------------------------------------------------------------------- #
# ledger
# --------------------------------------------------------------------------- #


def load_ledger(path: Path) -> list[dict]:
    """Read the append-only listen ledger. A missing ledger is an empty one."""
    if not path.is_file():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Ledger unreadable: {path}: {exc}")
    if not isinstance(data, dict) or data.get("schema_version") != LEDGER_SCHEMA_VERSION:
        raise SystemExit(
            f"Ledger schema mismatch in {path}: "
            f"expected schema_version {LEDGER_SCHEMA_VERSION}"
        )
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise SystemExit(f"Ledger {path} has no entries list")
    return entries


def save_ledger(path: Path, entries: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": LEDGER_SCHEMA_VERSION,
                "book_id": BOOK_ID,
                "entries": entries,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def latest_verdict(
    entries: list[dict], *, chapter: int, voice_tag: str, digest: str
) -> dict | None:
    """Most recent verdict for this exact (chapter, voice, text) triple.

    Earlier entries are never rewritten or removed; a later entry for the same
    triple supersedes an earlier one, and both stay in the record.
    """
    matches = [
        entry
        for entry in entries
        if entry.get("chapter") == chapter
        and entry.get("voice_tag") == voice_tag
        and entry.get("spoken_sha256") == digest
    ]
    if not matches:
        return None
    return max(matches, key=lambda entry: entry.get("at", ""))


# --------------------------------------------------------------------------- #
# state resolution
# --------------------------------------------------------------------------- #


def read_manifest(path: Path) -> dict | None:
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def resolve_chapter(
    chapter: int,
    source: Path,
    *,
    output_dir: Path,
    work_root: Path,
    voice_tag: str,
    ledger: list[dict],
) -> ChapterState:
    digest = spoken_sha256(source)
    wav = output_dir / f"{4 + chapter:03d}-chapter-{chapter:03d}-{voice_tag}.wav"
    manifest = read_manifest(work_root / f"chapter-{chapter:03d}" / "manifest.json")

    quality = (manifest or {}).get("assembly", {}).get("chapter_quality", {}) or {}
    chunks = (manifest or {}).get("chunks", []) or []
    primary = (manifest or {}).get("primary_seed")
    fallback = tuple(
        chunk["index"]
        for chunk in chunks
        if isinstance(chunk, dict)
        and chunk.get("accepted")
        and chunk.get("seed") is not None
        and chunk.get("seed") != primary
    )
    recorded = (manifest or {}).get("spoken_sha256")
    gates_passed = bool(quality.get("passed")) if quality else None

    verdict = latest_verdict(
        ledger, chapter=chapter, voice_tag=voice_tag, digest=digest
    )

    if manifest is None or not wav.is_file():
        state = MISSING
    elif recorded != digest:
        # Includes manifests written before spoken_sha256 existed: unprovable is
        # treated as stale rather than assumed current.
        state = STALE
    elif not gates_passed:
        state = FAILED
    elif verdict is None:
        state = UNLISTENED
    elif verdict.get("verdict") == ACCEPTED:
        state = ACCEPTED
    else:
        state = REJECTED

    return ChapterState(
        chapter=chapter,
        source=source,
        spoken_sha256=digest,
        state=state,
        wav=wav,
        wav_exists=wav.is_file(),
        manifest_sha256=recorded if isinstance(recorded, str) else None,
        gates_passed=gates_passed,
        wer=quality.get("wer"),
        coverage=quality.get("coverage"),
        audio_seconds=(manifest or {}).get("assembly", {}).get("seconds"),
        fallback_chunks=fallback,
        listened_at=(verdict or {}).get("at"),
        note=(verdict or {}).get("note"),
    )


def resolve_all(
    chapters_root: Path,
    *,
    output_dir: Path,
    work_root: Path,
    voice_tag: str,
    ledger_path: Path,
    start: int = 1,
    end: int = 128,
) -> list[ChapterState]:
    ledger = load_ledger(ledger_path)
    return [
        resolve_chapter(
            number,
            source,
            output_dir=output_dir,
            work_root=work_root,
            voice_tag=voice_tag,
            ledger=ledger,
        )
        for number, source in discover_chapters(chapters_root, start, end)
    ]


# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #


def print_report(states: list[ChapterState], *, chapters_root: Path) -> None:
    counts = {state: 0 for state in STATE_ORDER}
    for item in states:
        counts[item.state] += 1

    total_fallback = sum(len(item.fallback_chunks) for item in states)
    rendered = [item for item in states if item.gates_passed]

    print(f"{'ch':>4}  {'state':<11} {'wer':>6} {'cov':>6} {'min':>6}  fallback  note")
    print("-" * 78)
    for item in sorted(states, key=lambda s: (STATE_ORDER.index(s.state), s.chapter)):
        if item.state == ACCEPTED:
            continue
        wer = f"{item.wer:.3f}" if item.wer is not None else "-"
        cov = f"{item.coverage:.3f}" if item.coverage is not None else "-"
        minutes = (
            f"{item.audio_seconds / 60:.1f}" if item.audio_seconds is not None else "-"
        )
        fallback = (
            ",".join(str(index) for index in item.fallback_chunks)
            if item.fallback_chunks
            else "-"
        )
        note = (item.note or "")[:24]
        print(
            f"{item.chapter:>4}  {item.state:<11} {wer:>6} {cov:>6} {minutes:>6}  "
            f"{fallback:>8}  {note}"
        )
    if counts[ACCEPTED]:
        print(f"\n({counts[ACCEPTED]} accepted chapters omitted)")

    print("\nsummary")
    for state in STATE_ORDER:
        print(f"  {state:<11} {counts[state]:>4}")

    if rendered:
        print(
            f"\nfallback chunks across {len(rendered)} rendered chapter(s): "
            f"{total_fallback}"
        )
        print(
            "  A non-primary seed means the first candidate failed its gate. "
            "This is the\n  honest reliability signal; a clean pass rate with "
            "many fallbacks is a healthy\n  retry budget rather than a "
            "dependable first attempt."
        )

    chapters = discover_chapters(chapters_root)
    print(f"\ntext_version {text_version(chapters)}")
    packageable = all(item.packageable for item in states)
    print(
        f"packageable  {'yes' if packageable else 'no'} "
        f"({counts[ACCEPTED]}/{len(states)} accepted)"
    )


def states_to_json(states: list[ChapterState], *, chapters_root: Path) -> dict:
    return {
        "schema_version": 1,
        "book_id": BOOK_ID,
        "generated_at": utc_now(),
        "text_version_sha256": text_version(discover_chapters(chapters_root)),
        "packageable": all(item.packageable for item in states),
        "counts": {
            state: sum(1 for item in states if item.state == state)
            for state in STATE_ORDER
        },
        "chapters": [
            {
                "chapter": item.chapter,
                "state": item.state,
                "source": str(item.source),
                "spoken_sha256": item.spoken_sha256,
                "manifest_sha256": item.manifest_sha256,
                "wav": str(item.wav),
                "wav_exists": item.wav_exists,
                "gates_passed": item.gates_passed,
                "wer": item.wer,
                "coverage": item.coverage,
                "audio_seconds": item.audio_seconds,
                "fallback_chunks": list(item.fallback_chunks),
                "listened_at": item.listened_at,
                "note": item.note,
            }
            for item in states
        ],
    }


# --------------------------------------------------------------------------- #
# cli
# --------------------------------------------------------------------------- #


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--chapters-root", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--voice-tag", default="qvoice-uks03")
    parser.add_argument(
        "--ledger",
        type=Path,
        default=None,
        help="Listen ledger JSON (default: <output-dir>/listen-ledger.json)",
    )
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=128)

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--report", action="store_true", help="human-readable table")
    mode.add_argument("--json", action="store_true", help="full state as JSON")
    mode.add_argument(
        "--queue",
        action="store_true",
        help="chapter numbers awaiting a human listen, one per line",
    )
    mode.add_argument(
        "--stale",
        action="store_true",
        help="chapter numbers needing a re-render, one per line",
    )
    mode.add_argument(
        "--text-version", action="store_true", help="print the text version digest"
    )
    mode.add_argument(
        "--accept", type=int, metavar="N", help="record a human accept for chapter N"
    )
    mode.add_argument(
        "--reject", type=int, metavar="N", help="record a human reject for chapter N"
    )
    parser.add_argument("--note", default=None, help="note stored with the verdict")
    parser.add_argument(
        "--listener", default="author", help="who listened; stored with the verdict"
    )
    args = parser.parse_args()

    for name in ("chapters_root", "output_dir", "work_root"):
        setattr(args, name, getattr(args, name).resolve())
    ledger_path = (args.ledger or args.output_dir / "listen-ledger.json").resolve()

    if args.text_version:
        print(text_version(discover_chapters(args.chapters_root, args.start, args.end)))
        return

    if args.accept is not None or args.reject is not None:
        chapter = args.accept if args.accept is not None else args.reject
        verdict = ACCEPTED if args.accept is not None else REJECTED
        if verdict == REJECTED and not args.note:
            raise SystemExit("--reject requires --note saying what was wrong")

        matches = [
            (number, source)
            for number, source in discover_chapters(args.chapters_root)
            if number == chapter
        ]
        if not matches:
            raise SystemExit(f"No chapter {chapter} under {args.chapters_root}")
        number, source = matches[0]

        entries = load_ledger(ledger_path)
        state = resolve_chapter(
            number,
            source,
            output_dir=args.output_dir,
            work_root=args.work_root,
            voice_tag=args.voice_tag,
            ledger=entries,
        )
        if verdict == ACCEPTED and state.state not in (UNLISTENED, REJECTED, ACCEPTED):
            raise SystemExit(
                f"Chapter {number} is {state.state}; only a rendered chapter that "
                "passed its gates can be accepted. Re-render first."
            )

        entries.append(
            {
                "chapter": number,
                "voice_tag": args.voice_tag,
                "spoken_sha256": state.spoken_sha256,
                "verdict": verdict,
                "at": utc_now(),
                "listener": args.listener,
                "note": args.note,
            }
        )
        save_ledger(ledger_path, entries)
        print(
            f"{verdict} chapter {number} "
            f"({state.spoken_sha256[:16]}, {args.voice_tag}) → {ledger_path}"
        )
        return

    states = resolve_all(
        args.chapters_root,
        output_dir=args.output_dir,
        work_root=args.work_root,
        voice_tag=args.voice_tag,
        ledger_path=ledger_path,
        start=args.start,
        end=args.end,
    )

    if args.json:
        print(json.dumps(states_to_json(states, chapters_root=args.chapters_root), indent=2))
        return
    if args.queue:
        for item in states:
            if item.state in NEEDS_LISTEN:
                print(item.chapter)
        return
    if args.stale:
        for item in states:
            if item.state in NEEDS_RENDER:
                print(item.chapter)
        return

    print_report(states, chapters_root=args.chapters_root)


if __name__ == "__main__":
    main()
