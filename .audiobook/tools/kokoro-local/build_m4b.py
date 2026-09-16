#!/usr/bin/env python3
"""Build a chaptered M4B from ordered audiobook WAVs + cover art.

Local packaging only — does not touch the Nova production path.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import tempfile
from pathlib import Path

import soundfile as sf

WAV_RE = re.compile(
    r"^(?P<seq>\d{3})-(?P<kind>dedication|chapter)-(?P<num>\d{3})-(?P<voice>.+)\.wav$",
    re.IGNORECASE,
)


def discover_wavs(audio_dir: Path, voice_tag: str) -> list[tuple[int, str, Path]]:
    """Return (sort_key, chapter_title, path) in playback order."""
    items: list[tuple[int, str, Path]] = []
    for path in sorted(audio_dir.glob(f"*-{voice_tag}.wav")):
        match = WAV_RE.match(path.name)
        if not match:
            continue
        seq = int(match.group("seq"))
        kind = match.group("kind").lower()
        num = int(match.group("num"))
        if kind == "dedication":
            title = "Dedication"
        else:
            title = f"Chapter {num}"
        items.append((seq, title, path))
    items.sort(key=lambda row: row[0])
    if not items:
        raise SystemExit(f"No WAVs matching *-{voice_tag}.wav in {audio_dir}")
    return items


def duration_ms(path: Path) -> int:
    info = sf.info(str(path))
    return int(round(info.duration * 1000))


def write_ffmetadata(
    path: Path,
    *,
    title: str,
    author: str,
    album: str,
    chapters: list[tuple[str, int, int]],
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
    wavs: list[tuple[int, str, Path]],
    *,
    cover: Path,
    output: Path,
    title: str,
    author: str,
    album: str,
    aac_bitrate: str,
) -> None:
    if not cover.is_file():
        raise SystemExit(f"Cover not found: {cover}")

    chapters: list[tuple[str, int, int]] = []
    cursor = 0
    for _, name, path in wavs:
        length = duration_ms(path)
        chapters.append((name, cursor, cursor + length))
        cursor += length

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="frontier-m4b-") as tmp:
        tmp_dir = Path(tmp)
        list_path = tmp_dir / "concat.txt"
        meta_path = tmp_dir / "ffmetadata.txt"
        concat_audio = tmp_dir / "audio.m4a"

        list_path.write_text(
            "".join(f"file '{path.resolve().as_posix()}'\n" for _, _, path in wavs),
            encoding="utf-8",
        )
        write_ffmetadata(
            meta_path,
            title=title,
            author=author,
            album=album,
            chapters=chapters,
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
        "--require-chapters",
        type=int,
        default=0,
        help="Fail unless at least this many chapter WAVs are present (dedication optional)",
    )
    args = parser.parse_args()

    wavs = discover_wavs(args.audio_dir, args.voice_tag)
    chapter_count = sum(1 for _, title, _ in wavs if title.startswith("Chapter "))
    if args.require_chapters and chapter_count < args.require_chapters:
        raise SystemExit(
            f"Expected at least {args.require_chapters} chapter WAVs, found {chapter_count}"
        )

    output = args.output
    if output is None:
        slug = re.sub(r"[^a-z0-9]+", "-", args.title.lower()).strip("-")
        output = args.audio_dir / f"{slug}-{args.voice_tag}.m4b"

    print(f"Packaging {len(wavs)} tracks → {output}")
    for _, title, path in wavs:
        print(f"  {path.name} · {title}")
    build_m4b(
        wavs,
        cover=args.cover,
        output=output,
        title=args.title,
        author=args.author,
        album=args.album,
        aac_bitrate=args.aac_bitrate,
    )


if __name__ == "__main__":
    main()
