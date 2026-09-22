#!/usr/bin/env python3
"""Build a chaptered M4B from ordered audiobook WAVs + cover art.

Local packaging only — does not touch the Nova production path.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))

# audiobook-studio/tools/kokoro-local/build_m4b.py -> repo root is four up.
REPO_ROOT = Path(__file__).resolve().parents[3]

from audio_state import ACCEPTED, resolve_all, utc_now  # noqa: E402
from spoken_text import discover_chapters, text_version  # noqa: E402
from wav_to_mp3 import chapter_titles  # noqa: E402

# The numeric segment is optional: front matter is named `002-dedication-<voice>.wav`
# with no number, so requiring one silently dropped the dedication from the book.
WAV_RE = re.compile(
    r"^(?P<seq>\d{3})-(?P<kind>dedication|chapter)(?:-(?P<num>\d{3}))?-(?P<voice>.+)\.wav$",
    re.IGNORECASE,
)


def discover_wavs(
    audio_dir: Path, voice_tag: str, *, manuscript_root: Path | None = None
) -> list[tuple[int, str, str, Path]]:
    """Return (sort_key, kind, title, path) in playback order.

    When `manuscript_root` is given, chapter names come from the manuscript's
    canonical restricted-header titles ("1. Noise Floor"). Missing titles fail
    closed instead of silently producing inconsistent player metadata.
    """
    titles = chapter_titles(manuscript_root) if manuscript_root else {}
    items: list[tuple[int, str, str, Path]] = []
    for path in sorted(audio_dir.glob(f"*-{voice_tag}.wav")):
        match = WAV_RE.match(path.name)
        if not match:
            continue
        seq = int(match.group("seq"))
        kind = match.group("kind").lower()
        raw_num = match.group("num")
        if kind == "dedication":
            title = "Dedication"
        else:
            num = int(raw_num) if raw_num else seq
            if manuscript_root is not None and num not in titles:
                raise SystemExit(f"No canonical manuscript title for chapter {num}")
            canonical_title = titles.get(num)
            title = f"{num}. {canonical_title}" if canonical_title else f"Chapter {num}"
        items.append((seq, kind, title, path))
    items.sort(key=lambda row: row[0])
    if not items:
        raise SystemExit(f"No WAVs matching *-{voice_tag}.wav in {audio_dir}")
    return items


def duration_ms(path: Path) -> int:
    info = sf.info(str(path))
    return int(round(info.duration * 1000))


def verify_listened(
    *,
    chapters_root: Path,
    output_dir: Path,
    work_root: Path,
    voice_tag: str,
    ledger: Path | None,
    chapter_numbers: set[int],
) -> list:
    """Refuse to package unless every included chapter is an accepted current render.

    This is the gate the whole queue exists to serve. Automated gates decide
    whether a render is faithful to the text; only a person decides whether the
    delivery is acceptable, and only accepted renders of the *current* prose may
    ship. Failing here is the correct outcome, not an obstacle.

    Scope follows the WAVs being packaged, so a 30-chapter preview is judged on
    its 30 chapters while a full book is judged on all 128. Chapters absent from
    the audio set are outside this build and are not evaluated.
    """
    states = [
        item
        for item in resolve_all(
            chapters_root,
            output_dir=output_dir,
            work_root=work_root,
            voice_tag=voice_tag,
            ledger_path=(ledger or output_dir / "listen-ledger.json"),
            start=min(chapter_numbers),
            end=max(chapter_numbers),
        )
        if item.chapter in chapter_numbers
    ]
    blocked = [item for item in states if item.state != ACCEPTED]
    if blocked:
        by_state: dict[str, list[int]] = {}
        for item in blocked:
            by_state.setdefault(item.state, []).append(item.chapter)
        lines = [
            f"Refusing to package: {len(blocked)} of {len(states)} chapters are not "
            "accepted.",
            "",
        ]
        for state, numbers in sorted(by_state.items()):
            shown = ", ".join(str(number) for number in numbers[:14])
            if len(numbers) > 14:
                shown += f", … (+{len(numbers) - 14})"
            lines.append(f"  {state:<11} {len(numbers):>4}   {shown}")
        lines += [
            "",
            "  audio_state.py --stale   → chapters needing a re-render",
            "  audio_state.py --queue   → chapters awaiting a listen",
            "  audio_state.py --accept N --note '…'",
            "",
            "Override with --no-verify-text only to build a private proof copy.",
        ]
        raise SystemExit("\n".join(lines))
    return states


def write_sidecar(
    path: Path,
    *,
    output: Path,
    voice_tag: str,
    release_version: str,
    version: str,
    states: list | None,
    tracks: list[tuple[int, str, str, Path]],
    total_ms: int,
) -> None:
    """Record which text this audiobook contains, beside the audiobook.

    An M4B is opaque: nothing in the audio says which draft it was made from. The
    sidecar makes the question answerable without listening — compare
    `text_version_sha256` against `spoken_text.py --chapters-root … ` and a
    mismatch tells you the audiobook is behind, while the per-chapter digests
    tell you exactly which chapters moved.
    """
    by_chapter = {item.chapter: item for item in (states or [])}
    payload = {
        "schema_version": 1,
        "book_id": "the-final-frontier",
        "m4b": output.name,
        "built_at": utc_now(),
        "voice_tag": voice_tag,
        "release_version": release_version,
        "text_version_sha256": version,
        "text_verified": states is not None,
        "duration_seconds": round(total_ms / 1000, 3),
        "track_count": len(tracks),
        "chapters": [
            {
                "chapter": number,
                "spoken_sha256": item.spoken_sha256,
                "wer": item.wer,
                "coverage": item.coverage,
                "fallback_chunks": list(item.fallback_chunks),
                "listened_at": item.listened_at,
                "note": item.note,
            }
            for number, item in sorted(by_chapter.items())
        ],
        "non_chapter_tracks": [
            {"sequence": seq, "kind": kind, "title": title, "wav": wav.name}
            for seq, kind, title, wav in tracks
            if kind != "chapter"
        ],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def write_ffmetadata(
    path: Path,
    *,
    title: str,
    author: str,
    album: str,
    chapters: list[tuple[str, int, int]],
    comment: str | None = None,
) -> None:
    lines = [
        ";FFMETADATA1",
        f"title={_escape(title)}",
        f"artist={_escape(author)}",
        f"album={_escape(album)}",
        f"album_artist={_escape(author)}",
        "genre=Audiobook",
        "media_type=2",
    ]
    if comment:
        # Carried inside the file so a stray copy with no sidecar can still say
        # which text it contains.
        lines.append(f"comment={_escape(comment)}")
    for name, start_ms, end_ms in chapters:
        lines.extend(
            [
                "",
                "[CHAPTER]",
                "TIMEBASE=1/1000",
                f"START={start_ms}",
                f"END={end_ms}",
                f"title={_escape(name)}",
            ]
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("=", "\\=").replace(";", "\\;").replace("#", "\\#").replace("\n", " ")


def build_m4b(
    wavs: list[tuple[int, str, str, Path]],
    *,
    cover: Path,
    output: Path,
    title: str,
    author: str,
    album: str,
    aac_bitrate: str,
    comment: str | None = None,
    chapter_gap_ms: int = 2500,
    pad_python: str | None = None,
    pad_script: Path | None = None,
) -> int:
    if not cover.is_file():
        raise SystemExit(f"Cover not found: {cover}")

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="frontier-m4b-") as tmp:
        tmp_dir = Path(tmp)
        list_path = tmp_dir / "concat.txt"
        meta_path = tmp_dir / "ffmetadata.txt"
        concat_audio = tmp_dir / "audio.m4a"

        # A V6 comfort-tone pad between chapters, so the last sentence of one
        # chapter does not run straight into the next chapter's announcement.
        # Pure silence would drop the room tone out at every seam (the "background
        # opens up" defect), so each pad is synthesised by make_comfort_pad.py from
        # the PRECEDING chapter's own tone. The pad belongs to the preceding
        # chapter's running time, so the next chapter's marker lands on its
        # announcement rather than inside dead-sounding tone.
        can_pad = (
            chapter_gap_ms > 0
            and pad_python is not None
            and pad_script is not None
            and pad_script.is_file()
        )
        if chapter_gap_ms > 0 and not can_pad:
            raise SystemExit(
                "chapter gap requested but the V6 pad generator is unavailable; "
                "pass --pad-python and ensure make_comfort_pad.py exists, or set "
                "--chapter-gap-ms 0 to concatenate with no pause (not recommended)."
            )

        concat_lines: list[str] = []
        chapters: list[tuple[str, int, int]] = []
        cursor = 0
        last_index = len(wavs) - 1
        for i, (_, _, name, path) in enumerate(wavs):
            length = duration_ms(path)
            concat_lines.append(f"file '{path.resolve().as_posix()}'")
            chapter_end = cursor + length
            # Append a pad after every chapter except the last, and fold its
            # duration into this chapter's end so markers stay exact.
            if can_pad and i != last_index:
                pad_path = tmp_dir / f"pad-{i:03d}.wav"
                subprocess.run(
                    [
                        pad_python,
                        str(pad_script),
                        "--donor", str(path.resolve()),
                        "--seconds", f"{chapter_gap_ms / 1000:.3f}",
                        "--output", str(pad_path),
                        "--seed", str(9021 + i),
                    ],
                    check=True,
                )
                pad_ms = duration_ms(pad_path)
                concat_lines.append(f"file '{pad_path.resolve().as_posix()}'")
                chapter_end += pad_ms
            chapters.append((name, cursor, chapter_end))
            cursor = chapter_end

        list_path.write_text("\n".join(concat_lines) + "\n", encoding="utf-8")
        write_ffmetadata(
            meta_path,
            title=title,
            author=author,
            album=album,
            chapters=chapters,
            comment=comment,
        )

        # Single AAC encode from the WAV concat (preserves chapter timing).
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-f",
                "concat",
                "-safe",
                "0",
                "-i",
                str(list_path),
                "-c:a",
                "aac",
                "-b:a",
                aac_bitrate,
                "-ar",
                "24000",
                "-ac",
                "1",
                "-movflags",
                "+faststart",
                str(concat_audio),
            ],
            check=True,
        )

        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i",
                str(concat_audio),
                "-i",
                str(cover.resolve()),
                "-i",
                str(meta_path),
                "-map",
                "0:a",
                "-map",
                "1:v",
                "-map_metadata",
                "2",
                "-c:a",
                "copy",
                "-c:v",
                "mjpeg",
                "-disposition:v:0",
                "attached_pic",
                "-f",
                "mp4",
                str(output.resolve()),
            ],
            check=True,
        )

    total_min = cursor / 60000
    print(f"Wrote {output} ({len(wavs)} chapters, {total_min:.1f} min)")
    return cursor


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--audio-dir",
        type=Path,
        default=Path("audiobook"),
        help="Directory containing ordered WAV files",
    )
    parser.add_argument("--voice-tag", default="chatterbox-uk-s03")
    parser.add_argument("--cover", type=Path, default=Path("cover.jpg"))
    parser.add_argument(
        "--manuscript-root",
        type=Path,
        default=None,
        help="Chapters dir; canonical restricted-header titles are used in chapter metadata",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Output .m4b path (default: audiobook/<title-slug>-<voice>.m4b)",
    )
    parser.add_argument("--title", default="The Final Frontier")
    parser.add_argument("--author", default="Jessica Mulein")
    parser.add_argument("--album", default="The Final Frontier")
    parser.add_argument("--aac-bitrate", default="64k")
    parser.add_argument(
        "--chapter-gap-ms",
        type=int,
        default=2500,
        help="V6 comfort-tone pause inserted between chapters so one does not run "
        "into the next announcement. 2.5s was chosen by ear as a clear chapter "
        "break for a listener who cannot see one. 0 concatenates with no pause "
        "(not recommended).",
    )
    parser.add_argument(
        "--pad-python",
        default=None,
        help="Python interpreter that can run make_comfort_pad.py (the narration "
        "venv, which has the V6 synthesis deps). Defaults to the narration venv "
        "beside this repo if present, else the current interpreter.",
    )
    parser.add_argument(
        "--require-chapters",
        type=int,
        default=0,
        help="Fail unless at least this many chapter WAVs are present (dedication optional)",
    )
    parser.add_argument(
        "--chapters-root",
        type=Path,
        default=None,
        help="Manuscript chapters dir, for the listen gate and text version "
        "(default: --manuscript-root)",
    )
    parser.add_argument(
        "--work-root",
        type=Path,
        default=None,
        help="qvoice work root holding per-chapter manifest.json",
    )
    parser.add_argument(
        "--ledger",
        type=Path,
        default=None,
        help="Listen ledger (default: <audio-dir>/listen-ledger.json)",
    )
    parser.add_argument(
        "--release-version",
        default="v0.9.0",
        help="Human-readable release label carried in the M4B and sidecar",
    )
    parser.add_argument(
        "--no-verify-text",
        action="store_true",
        help="Skip the listen gate and the text-version stamp. Private proof "
        "copies only — the output cannot state which text it contains.",
    )
    args = parser.parse_args()

    chapters_root = args.chapters_root or args.manuscript_root
    if not args.no_verify_text and (chapters_root is None or args.work_root is None):
        raise SystemExit(
            "Packaging requires --chapters-root and --work-root so every chapter can "
            "be checked against the listen ledger and the text version recorded.\n"
            "Pass --no-verify-text to build an unverifiable proof copy instead."
        )

    wavs = discover_wavs(
        args.audio_dir, args.voice_tag, manuscript_root=chapters_root
    )
    # Count by kind, not by title text — titles come from canonical chapter metadata.
    chapter_count = sum(1 for _, kind, _, _ in wavs if kind == "chapter")
    if args.require_chapters and chapter_count < args.require_chapters:
        raise SystemExit(
            f"Expected at least {args.require_chapters} chapter WAVs, found {chapter_count}"
        )

    output = args.output
    if output is None:
        slug = re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-")
        output = args.audio_dir / f"{slug}-{args.voice_tag}.m4b"

    states = None
    version = "unverified"
    comment = None
    if not args.no_verify_text:
        numbers = {
            int(match.group("num") or match.group("seq"))
            for _, kind, _, path in wavs
            if kind == "chapter" and (match := WAV_RE.match(path.name))
        }
        if not numbers:
            raise SystemExit("No chapter WAVs to verify; nothing to package.")
        root = chapters_root.resolve()
        states = verify_listened(
            chapters_root=root,
            output_dir=args.audio_dir.resolve(),
            work_root=args.work_root.resolve(),
            voice_tag=args.voice_tag,
            ledger=args.ledger,
            chapter_numbers=numbers,
        )
        # Version covers exactly the chapters in this build, so a preview and a
        # full book never share a digest.
        version = text_version(
            [
                (number, path)
                for number, path in discover_chapters(
                    root, min(numbers), max(numbers)
                )
                if number in numbers
            ]
        )
        comment = (
            f"{args.release_version} · text_version {version} · voice {args.voice_tag}"
        )
        print(
            f"Listen gate: {len(states)}/{len(states)} chapters accepted\n"
            f"Text version: {version}"
        )

    print(f"Packaging {len(wavs)} tracks ({chapter_count} chapters) → {output}")
    for _, _, title, path in wavs:
        print(f"  {path.name} · {title}")

    # Resolve the interpreter and script for the V6 inter-chapter pad. The pad
    # synthesis lives in the narration subproject (it imports the renderer's
    # comfort_gap so the seam tone and the in-chapter gaps can never drift), which
    # has its own venv with the numeric deps.
    pad_script = (
        REPO_ROOT / "audiobook-studio/tools/narration/make_comfort_pad.py"
    )
    if args.pad_python:
        pad_python = args.pad_python
    else:
        venv_python = (
            REPO_ROOT / "audiobook-studio/tools/narration/.venv/bin/python"
        )
        pad_python = str(venv_python) if venv_python.exists() else sys.executable

    total_ms = build_m4b(
        wavs,
        cover=args.cover,
        output=output,
        title=args.title,
        author=args.author,
        album=args.album,
        aac_bitrate=args.aac_bitrate,
        comment=comment,
        chapter_gap_ms=args.chapter_gap_ms,
        pad_python=pad_python,
        pad_script=pad_script,
    )

    sidecar = output.with_suffix(".json")
    write_sidecar(
        sidecar,
        output=output,
        voice_tag=args.voice_tag,
        release_version=args.release_version,
        version=version,
        states=states,
        tracks=wavs,
        total_ms=total_ms,
    )
    print(f"Wrote {sidecar}")


if __name__ == "__main__":
    main()
