"""The single definition of *what text gets narrated*, and its digest.

Local audition tooling only — does not touch the Nova production path.

Why this exists
---------------
Every derived audio artifact needs to answer one question: which version of the
prose am I? Without that, a render, a listen approval, and a packaged M4B all
silently outlive the text they were made from. A WAV on disk looks identical
whether or not the chapter changed under it.

So the narrated string is defined in exactly one place — here — and everything
that renders, gates, approves, or packages derives its identity from it:

    extract_body()   strip the Chapter_Header, keep the Prose Body
    spoken_text()    + normalize() so digits are verbalised as they are spoken
    spoken_sha256()  the per-chapter identity
    text_version()   the whole-book identity, over the ordered chapter digests

`render_chapter_chatterbox` and `render_chapter_qvoice` import `extract_body`
from here rather than defining it, so a hash can never drift from the text that
was actually fed to the model.

Deliberately dependency-free: `re`, `hashlib`, `pathlib`, and the pure
`normalize_speech_text` module. Importing this must never require mlx-audio,
Metal, or the local venv, because the state and queue tooling has to run
anywhere — including from a hook or CI — without a GPU.

The digest covers the *spoken* text, not the raw Markdown. Editing a `hook:`
line, correcting a `words:` count, or promoting a `status:` does not invalidate
eight minutes of audio. Only a change to what is read aloud does.
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from normalize_speech_text import normalize

FRONT_MATTER = re.compile(r"^---\n.*?\n---\n+", re.DOTALL)

# chapters/<movement>/<movement>-<NNN>-<slug>.md, per the manuscript's
# file-conventions.md four-way agreement rule.
CHAPTER_FILENAME = re.compile(
    r"^(?P<movement>[a-z][a-z-]*)-(?P<number>\d{3})-(?P<slug>[a-z0-9][a-z0-9-]*)\.md$"
)


def extract_body(path: Path) -> str:
    """Return the Prose Body: the chapter file with its Chapter_Header removed."""
    text = path.read_text(encoding="utf-8")
    body = FRONT_MATTER.sub("", text, count=1).strip()
    if not body:
        raise SystemExit(f"No body text in {path}")
    return body


def spoken_text(path: Path, *, style: str = "plain") -> str:
    """Return the exact string a renderer feeds to the model for this chapter.

    Must stay identical to what `render_chapter_qvoice.main` computes, which is
    `normalize(extract_body(chapter))`. Both call into this module so the two
    cannot diverge.
    """
    return normalize(extract_body(path), style=style)


def spoken_sha256(path: Path, *, style: str = "plain") -> str:
    """Digest of the narrated text of one chapter."""
    return hashlib.sha256(spoken_text(path, style=style).encode("utf-8")).hexdigest()


def discover_chapters(
    chapters_root: Path, start: int = 1, end: int = 128
) -> list[tuple[int, Path]]:
    """Return sorted (chapter_number, path) for chapters in [start, end].

    Walks the movement directories under `chapters_root` and reads the number
    from the filename rather than from the header, so this stays usable when a
    header is mid-edit. Duplicate numbers are an error: the manuscript checker
    guarantees a bijection, and quietly picking one would hide a real break.
    """
    found: dict[int, Path] = {}
    for path in sorted(chapters_root.rglob("*.md")):
        match = CHAPTER_FILENAME.match(path.name)
        if not match:
            continue
        number = int(match.group("number"))
        if not start <= number <= end:
            continue
        if number in found:
            raise SystemExit(
                f"Duplicate chapter {number}: {found[number].name} and {path.name}"
            )
        found[number] = path
    if not found:
        raise SystemExit(f"No chapter files found under {chapters_root}")
    return [(number, found[number]) for number in sorted(found)]


def text_version(chapters: list[tuple[int, Path]], *, style: str = "plain") -> str:
    """Digest identifying the whole text a packaged audiobook corresponds to.

    Computed over the ordered `NNN:<spoken_sha256>` lines so it changes when any
    chapter's narrated text changes, when a chapter is added or removed, and
    when the order changes — and not otherwise. Independent of git, so it is
    stable across uncommitted work and meaningful in a released file.
    """
    lines = "\n".join(
        f"{number:03d}:{spoken_sha256(path, style=style)}" for number, path in chapters
    )
    return hashlib.sha256(lines.encode("utf-8")).hexdigest()


def main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Print spoken-text digests.")
    parser.add_argument("--chapters-root", type=Path, required=True)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=128)
    parser.add_argument("--style", default="plain")
    parser.add_argument(
        "--json", action="store_true", help="emit per-chapter digests as JSON"
    )
    args = parser.parse_args()

    chapters = discover_chapters(args.chapters_root, args.start, args.end)
    version = text_version(chapters, style=args.style)
    if args.json:
        print(
            json.dumps(
                {
                    "text_version_sha256": version,
                    "chapter_count": len(chapters),
                    "chapters": [
                        {
                            "chapter": number,
                            "path": str(path),
                            "spoken_sha256": spoken_sha256(path, style=args.style),
                        }
                        for number, path in chapters
                    ],
                },
                indent=2,
            )
        )
        return
    for number, path in chapters:
        print(f"{number:03d}  {spoken_sha256(path, style=args.style)[:16]}  {path.name}")
    print(f"\ntext_version {version}")
    print(f"chapters     {len(chapters)}")


if __name__ == "__main__":
    main()
