#!/usr/bin/env python3
"""Encode finished chapter WAVs to tagged MP3s.

Local audition tooling only — does not touch the Nova production path.

Safe to run while a batch render is still going: any WAV touched within
`--settle-seconds` is assumed to be mid-write and skipped, so a partially
written chapter never gets encoded.

Chapter titles come from the manuscript filename slug (the front matter carries
no title field), so `discovery-part-001-noise-floor.md` becomes "Noise Floor".

Example
-------
  PY=.venv/bin/python
  $PY wav_to_mp3.py \
      --audio-dir ../../../audiobook \
      --manuscript-root "../../../The Final Frontier Novel/chapters" \
      --voice-tag chatterbox-emns-n599 \
      --out-dir ../../../audiobook/mp3
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

WAV_CHAPTER_RE = re.compile(
    r"^(?P<seq>\d{3})-chapter-(?P<num>\d{3})-(?P<voice>.+)\.wav$", re.IGNORECASE
)
SLUG_RE = re.compile(r"^(?:[a-z]+-)*?(?P<num>\d{3})-(?P<slug>.+)$")

# Words that should stay lowercase in a title, unless they lead it.
MINOR = {
    "a", "an", "and", "as", "at", "before", "but", "by", "for", "from", "in",
    "into", "nor", "of", "on", "onto", "or", "over", "the", "to", "up", "with",
}


def title_from_slug(slug: str) -> str:
    words = slug.replace("_", "-").split("-")
    out: list[str] = []
    for index, word in enumerate(words):
        if not word:
            continue
        lower = word.lower()
        if index > 0 and lower in MINOR:
            out.append(lower)
        else:
            out.append(lower[:1].upper() + lower[1:])
    return " ".join(out)


def chapter_titles(manuscript_root: Path) -> dict[int, str]:
    titles: dict[int, str] = {}
    for path in sorted(manuscript_root.rglob("*.md")):
        m = SLUG_RE.match(path.stem)
        if not m:
            continue
        titles[int(m.group("num"))] = title_from_slug(m.group("slug"))
    return titles


def probe_seconds(path: Path) -> float:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=nw=1:nk=1", str(path)],
        capture_output=True, text=True,
    )
    try:
        return float(proc.stdout.strip())
    except ValueError:
        return 0.0


def encode(
    wav: Path,
    dest: Path,
    *,
    bitrate: str,
    sample_rate: int,
    album: str,
    artist: str,
    title: str,
    track: int,
    total: int,
) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-i", str(wav),
        "-c:a", "libmp3lame",
        "-ac", "1",
        "-ar", str(sample_rate),
        "-b:a", bitrate,
        "-metadata", f"album={album}",
        "-metadata", f"artist={artist}",
        "-metadata", f"album_artist={artist}",
        "-metadata", f"title={title}",
        "-metadata", f"track={track}/{total}",
        "-metadata", "genre=Audiobook",
        "-id3v2_version", "3",
        str(dest),
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise SystemExit(f"ffmpeg failed on {wav.name}:\n{proc.stderr[:600]}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio-dir", type=Path, required=True)
    parser.add_argument("--manuscript-root", type=Path, required=True)
    parser.add_argument("--voice-tag", required=True)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--album", default="The Final Frontier")
    # Matches build_m4b.py's --author so MP3 and M4B metadata agree.
    parser.add_argument("--artist", default="Jessica Mulein")
    parser.add_argument("--bitrate", default="96k")
    parser.add_argument("--sample-rate", type=int, default=44100)
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=120.0,
        help="Skip WAVs modified more recently than this (likely mid-write)",
    )
    parser.add_argument(
        "--total-chapters",
        type=int,
        default=None,
        help="Track total for ID3; defaults to the highest chapter found",
    )
    parser.add_argument("--skip-existing", action="store_true")
    parser.add_argument(
        "--exclude-chapter",
        action="append",
        type=int,
        default=None,
        help="Chapter number to leave out; repeatable",
    )
    args = parser.parse_args()

    if shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None:
        raise SystemExit("ffmpeg/ffprobe not found on PATH")

    titles = chapter_titles(args.manuscript_root)
    excluded = set(args.exclude_chapter or [])

    candidates: list[tuple[int, int, Path]] = []
    for wav in sorted(args.audio_dir.glob("*.wav")):
        m = WAV_CHAPTER_RE.match(wav.name)
        if not m or m.group("voice").lower() != args.voice_tag.lower():
            continue
        candidates.append((int(m.group("num")), int(m.group("seq")), wav))

    if not candidates:
        raise SystemExit(f"no chapter WAVs found for voice tag {args.voice_tag!r}")

    total = args.total_chapters or max(n for n, _, _ in candidates)
    now = time.time()
    encoded = skipped_recent = skipped_existing = 0
    total_seconds = 0.0

    for chapter, sequence, wav in candidates:
        if chapter in excluded:
            print(f"  exclude ch{chapter:03d} (requested)")
            continue
        age = now - wav.stat().st_mtime
        if age < args.settle_seconds:
            print(f"  skip    ch{chapter:03d} — modified {age:.0f}s ago, still rendering")
            skipped_recent += 1
            continue
        title = titles.get(chapter, f"Chapter {chapter}")
        dest = args.out_dir / f"{sequence:03d}-chapter-{chapter:03d}-{args.voice_tag}.mp3"
        if args.skip_existing and dest.is_file():
            skipped_existing += 1
            continue
        encode(
            wav, dest,
            bitrate=args.bitrate,
            sample_rate=args.sample_rate,
            album=args.album,
            artist=args.artist,
            title=f"{chapter:03d} — {title}",
            track=chapter,
            total=total,
        )
        seconds = probe_seconds(dest)
        total_seconds += seconds
        wav_mb = wav.stat().st_size / 1e6
        mp3_mb = dest.stat().st_size / 1e6
        print(
            f"  ok      ch{chapter:03d} {seconds/60:5.1f} min  "
            f"{wav_mb:6.1f}MB wav -> {mp3_mb:5.1f}MB mp3   {title}"
        )
        encoded += 1

    print(
        f"\nencoded {encoded} file(s) into {args.out_dir}"
        + (f", {skipped_recent} still rendering" if skipped_recent else "")
        + (f", {skipped_existing} already present" if skipped_existing else "")
    )
    if total_seconds:
        print(f"total encoded runtime: {total_seconds/3600:.2f} h")


if __name__ == "__main__":
    main()
