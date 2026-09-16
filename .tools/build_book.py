#!/usr/bin/env python3
"""Compile the novel manuscript and build EPUB / PDF editions.

Assembles ``front-matter.md`` → chapters (checker discovery order) →
``back-matter.md``, strips restricted Chapter_Headers, injects part breaks,
then shells out to Pandoc.

External dependencies (not Python packages):
  - pandoc (required for epub/pdf)
  - xelatex from MacTeX/TeX Live (required for pdf)

Examples (repo root)::

  python3 .tools/build_book.py compile
  python3 .tools/build_book.py epub
  python3 .tools/build_book.py pdf
  python3 .tools/build_book.py all
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent
sys.path.insert(0, str(TOOLS_DIR))

from check_novel import (  # noqa: E402
    DEFAULT_MANUSCRIPT_ROOT,
    discover_chapter_files,
    parse_chapter_filename,
    split_chapter_header,
)

BOOK_DIR = REPO_ROOT / "book"
BUILD_DIR = BOOK_DIR / "build"
DIST_DIR = BOOK_DIR / "dist"
STYLE_DIR = TOOLS_DIR / "book"
DEFAULT_COVER = REPO_ROOT / "cover.jpg"
DEFAULT_MANUSCRIPT = REPO_ROOT / DEFAULT_MANUSCRIPT_ROOT

MOVEMENT_TITLES = {
    "discovery_part": ("Part One", "Discovery"),
    "private_defense_part": ("Part Two", "Private Defense"),
    "mindwars_part": ("Part Three", "Mindwars"),
    "aftermath_coda": ("Coda", "Aftermath"),
}


def _slug_to_title(slug: str) -> str:
    return " ".join(part.capitalize() for part in slug.split("-") if part)


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").lstrip("\ufeff").strip() + "\n"


def compile_manuscript(
    manuscript_root: Path,
    *,
    include_part_breaks: bool = True,
) -> str:
    """Return the assembled Markdown document for Pandoc."""

    front = manuscript_root / "front-matter.md"
    back = manuscript_root / "back-matter.md"
    if not front.is_file():
        raise SystemExit(f"Missing front matter: {front}")
    if not back.is_file():
        raise SystemExit(f"Missing back matter: {back}")

    chapters = discover_chapter_files(manuscript_root)
    if not chapters:
        raise SystemExit(f"No chapter files under {manuscript_root / 'chapters'}")

    blocks: List[str] = []

    # Title page / rights / dedication — keep author headings; Pandoc will
    # still pick up the YAML metadata file for EPUB/PDF bibliographics.
    blocks.append(_read_text(front).rstrip())
    blocks.append("")

    previous_movement: Optional[str] = None
    for path in chapters:
        parsed = parse_chapter_filename(path.name)
        if parsed is None:
            raise SystemExit(f"Unexpected chapter filename: {path.name}")
        try:
            _header_lines, body = split_chapter_header(
                path.read_text(encoding="utf-8"),
                item=str(path.relative_to(REPO_ROOT)),
            )
        except Exception as exc:  # check_novel raises typed errors
            raise SystemExit(f"Failed to split header for {path.name}: {exc}") from exc

        body = body.strip()
        if not body:
            raise SystemExit(f"Empty prose body: {path.name}")

        if include_part_breaks and parsed.movement != previous_movement:
            label, subtitle = MOVEMENT_TITLES.get(
                parsed.movement,
                ("Part", parsed.movement.replace("_", " ").title()),
            )
            # Unnumbered part openers so EPUB TOC stays chapter-primary when
            # using --epub-chapter-level=1 with these as plain H1s before chapters.
            blocks.append(f"# {label}")
            blocks.append("")
            blocks.append(f"*{subtitle}*")
            blocks.append("")
            previous_movement = parsed.movement

        title = _slug_to_title(parsed.slug)
        blocks.append(f"# Chapter {parsed.sequence}")
        blocks.append("")
        blocks.append(f"## {title}")
        blocks.append("")
        blocks.append(body)
        blocks.append("")

    blocks.append(_read_text(back).rstrip())
    blocks.append("")
    return "\n".join(blocks)


def write_compiled(
    manuscript_root: Path,
    output_path: Path,
    *,
    include_part_breaks: bool = True,
) -> Path:
    text = compile_manuscript(
        manuscript_root, include_part_breaks=include_part_breaks
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(text, encoding="utf-8")
    return output_path


def _require_command(name: str) -> None:
    from shutil import which

    if which(name) is None:
        raise SystemExit(
            f"Required external command not found: {name}. "
            f"Install it and retry."
        )


def _pandoc_base_args(
    compiled: Path,
    *,
    cover: Optional[Path],
) -> List[str]:
    args = [
        "pandoc",
        str(compiled),
        "--from=markdown",
        f"--metadata-file={STYLE_DIR / 'metadata.yaml'}",
        "--standalone",
        "--toc",
        "--toc-depth=2",
    ]
    if cover is not None and cover.is_file():
        # EPUB uses this; PDF cover is handled separately via include.
        args.append(f"--epub-cover-image={cover}")
    return args


def build_epub(
    compiled: Path,
    output: Path,
    *,
    cover: Optional[Path],
) -> Path:
    _require_command("pandoc")
    output.parent.mkdir(parents=True, exist_ok=True)
    css = STYLE_DIR / "epub.css"
    args = _pandoc_base_args(compiled, cover=cover)
    args.extend(
        [
            "--to=epub3",
            f"--css={css}",
            "--split-level=1",
            "-o",
            str(output),
        ]
    )
    subprocess.run(args, check=True, cwd=str(REPO_ROOT))
    return output


def build_pdf(
    compiled: Path,
    output: Path,
    *,
    cover: Optional[Path],
    engine: str = "xelatex",
) -> Path:
    _require_command("pandoc")
    _require_command(engine)
    output.parent.mkdir(parents=True, exist_ok=True)
    preamble = STYLE_DIR / "pdf-preamble.tex"
    cover_def = BUILD_DIR / "cover-image.tex"
    if cover is not None and cover.is_file():
        # Paths with spaces must be brace-wrapped for \includegraphics.
        cover_def.write_text(
            "\\newcommand{\\coverimage}{"
            + cover.resolve().as_posix()
            + "}\n",
            encoding="utf-8",
        )
    else:
        cover_def.write_text(
            "\\newcommand{\\coverimage}{}\n",
            encoding="utf-8",
        )
    args = [
        "pandoc",
        str(compiled),
        "--from=markdown",
        f"--metadata-file={STYLE_DIR / 'metadata.yaml'}",
        "--standalone",
        "--toc",
        "--toc-depth=2",
        f"--pdf-engine={engine}",
        f"--include-in-header={cover_def}",
        f"--include-in-header={preamble}",
        "-V",
        "documentclass=book",
        "-V",
        "classoption=oneside",
        "-V",
        "geometry:margin=1in",
        "-V",
        "fontsize=11pt",
        "-V",
        "linestretch=1.25",
        "-V",
        "colorlinks=true",
        "-V",
        "linkcolor=black",
        "-V",
        "urlcolor=black",
        "-V",
        "toccolor=black",
        "-o",
        str(output),
    ]
    subprocess.run(args, check=True, cwd=str(REPO_ROOT))
    return output


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command",
        choices=("compile", "epub", "pdf", "all"),
        help="compile=Markdown only; epub/pdf=Pandoc; all=compile+epub+pdf",
    )
    parser.add_argument(
        "--manuscript-root",
        type=Path,
        default=DEFAULT_MANUSCRIPT,
        help="Novel root (default: The Final Frontier Novel)",
    )
    parser.add_argument(
        "--cover",
        type=Path,
        default=DEFAULT_COVER,
        help="Cover image for EPUB (and PDF title page when present)",
    )
    parser.add_argument(
        "--no-part-breaks",
        action="store_true",
        help="Do not inject Part/Coda openers between movements",
    )
    parser.add_argument(
        "--pdf-engine",
        default="xelatex",
        help="Pandoc PDF engine (default: xelatex)",
    )
    args = parser.parse_args(argv)

    manuscript_root = args.manuscript_root
    if not manuscript_root.is_absolute():
        manuscript_root = (REPO_ROOT / manuscript_root).resolve()

    compiled_path = BUILD_DIR / "the-final-frontier.md"
    epub_path = DIST_DIR / "the-final-frontier.epub"
    pdf_path = DIST_DIR / "the-final-frontier.pdf"
    cover = args.cover if args.cover.is_file() else None
    if args.cover and not args.cover.is_file():
        print(f"warning: cover not found at {args.cover}; continuing without it", file=sys.stderr)
        cover = None

    if args.command in ("compile", "epub", "pdf", "all"):
        write_compiled(
            manuscript_root,
            compiled_path,
            include_part_breaks=not args.no_part_breaks,
        )
        print(f"compiled {compiled_path}")

    if args.command in ("epub", "all"):
        build_epub(compiled_path, epub_path, cover=cover)
        print(f"wrote {epub_path} ({epub_path.stat().st_size} bytes)")

    if args.command in ("pdf", "all"):
        build_pdf(
            compiled_path,
            pdf_path,
            cover=cover,
            engine=args.pdf_engine,
        )
        print(f"wrote {pdf_path} ({pdf_path.stat().st_size} bytes)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
