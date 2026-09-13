"""Restricted chapter parsing and deterministic excerpt preparation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .errors import InputError
from .util import normalize_lf_nfc, read_bytes_nofollow, sha256_text

HEADER_KEYS = frozenset(
    {"movement", "chapter", "pov_id", "timeline_id", "motif_events", "hook", "words", "length_class", "status"}
)
HEADER_LINE = re.compile(r"^([a-z_]+): (.+)$")
FILENAME_CHAPTER = re.compile(r"-(\d{3})-[a-z0-9]+(?:-[a-z0-9]+)*\.md$")
EMPHASIS = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
UNSUPPORTED_BLOCK = re.compile(r"(?m)^\s{0,3}(?:#{1,6}\s|>|```|~~~|(?:\*{3,}|-{3,})\s*$)")
UNSUPPORTED_LINK = re.compile(r"!?\[[^\]]*\]\([^)]*\)")


@dataclass(frozen=True)
class ChapterSource:
    path: Path
    chapter: int
    movement: str
    pov_id: str
    body: str
    body_sha256: str


def discover_chapter(manuscript_root: Path, chapter: int) -> Path:
    chapter_root = manuscript_root / "chapters"
    matches = sorted(chapter_root.glob(f"*/*-{chapter:03d}-*.md"))
    if len(matches) != 1:
        raise InputError(
            f"Chapter {chapter} must resolve to exactly one chapter file under {chapter_root}; found {len(matches)}"
        )
    return matches[0]


def read_chapter(path: Path, *, enforce_declared_words: bool = True) -> ChapterSource:
    try:
        decoded = read_bytes_nofollow(path).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError(f"Cannot decode chapter as strict UTF-8, {path}: {exc}") from exc
    text = normalize_lf_nfc(decoded)
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].removesuffix("\n") != "---":
        raise InputError(f"Chapter must begin with a restricted header delimiter: {path}")

    closing_index = None
    for index in range(1, len(lines)):
        if lines[index].removesuffix("\n") == "---":
            closing_index = index
            break
    if closing_index is None:
        raise InputError(f"Chapter header has no closing delimiter: {path}")

    header: dict[str, str] = {}
    for line_number, raw_line in enumerate(lines[1:closing_index], start=2):
        line = raw_line.removesuffix("\n")
        match = HEADER_LINE.fullmatch(line)
        if not match:
            raise InputError(f"Malformed restricted header line {line_number} in {path}")
        key, value = match.groups()
        if key in header:
            raise InputError(f"Duplicate chapter header key {key!r} in {path}")
        header[key] = value
    if set(header) != HEADER_KEYS:
        raise InputError(
            f"Chapter header keys are invalid in {path}; missing={sorted(HEADER_KEYS - set(header))}, "
            f"unknown={sorted(set(header) - HEADER_KEYS)}"
        )

    try:
        chapter_number = int(header["chapter"])
        declared_words = int(header["words"])
    except ValueError as exc:
        raise InputError(f"chapter and words header values must be integers in {path}") from exc
    filename_match = FILENAME_CHAPTER.search(path.name)
    if not filename_match or int(filename_match.group(1)) != chapter_number:
        raise InputError(f"Filename and chapter header disagree in {path}")

    body = "".join(lines[closing_index + 1 :])
    if not body.strip():
        raise InputError(f"Chapter Prose Body is empty: {path}")
    actual_words = len(body.split())
    if enforce_declared_words and declared_words != actual_words:
        raise InputError(
            f"Chapter {chapter_number} header words={declared_words} but normalized Prose Body has {actual_words}: {path}"
        )
    return ChapterSource(
        path=path.resolve(),
        chapter=chapter_number,
        movement=header["movement"],
        pov_id=header["pov_id"],
        body=body,
        body_sha256=sha256_text(body),
    )


def extract_anchored_excerpt(body: str, start_anchor: str, end_anchor: str, excerpt_id: str) -> str:
    if body.count(start_anchor) != 1:
        raise InputError(f"Excerpt {excerpt_id!r} start anchor must occur exactly once")
    if body.count(end_anchor) != 1:
        raise InputError(f"Excerpt {excerpt_id!r} end anchor must occur exactly once")
    start = body.index(start_anchor)
    end_start = body.index(end_anchor)
    if end_start < start:
        raise InputError(f"Excerpt {excerpt_id!r} end anchor occurs before its start anchor")
    end = end_start + len(end_anchor)
    return body[start:end]


def markdown_to_spoken(source: str, excerpt_id: str) -> str:
    """Remove only inline emphasis; fail closed on other Markdown constructs."""
    if UNSUPPORTED_BLOCK.search(source) or UNSUPPORTED_LINK.search(source) or "`" in source:
        raise InputError(f"Excerpt {excerpt_id!r} contains unsupported Markdown")
    spoken = EMPHASIS.sub(r"\1", source)
    if "*" in spoken:
        raise InputError(f"Excerpt {excerpt_id!r} contains unpaired or unsupported asterisks")
    if not spoken.strip():
        raise InputError(f"Excerpt {excerpt_id!r} becomes empty after spoken-text transformation")
    return spoken
