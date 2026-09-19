#!/usr/bin/env python3
"""Manuscript text handling for the Fish pipeline.

Forked deliberately from `kokoro-local`. The two pipelines target different
engines with different failure modes, and the old one is frozen: reaching back
into it meant a change made for Fish could alter Chatterbox or QVoice behaviour,
and that the old pipeline could never be archived while the new one depended on it.

`extract_body` is a straight port, and `normalize_speech_text` now sits alongside
this module rather than being reached for across the boundary. Nothing here imports
from the old pipeline.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

# Front matter is a leading `---` block. Same contract as the old pipeline, so a
# chapter file renders identically under either.
FRONT_MATTER = re.compile(r"^---\n.*?\n---\n+", re.DOTALL)
HEADER_LINE = re.compile(r"^(?P<key>[a-z_]+): (?P<value>.+)$")
HEADER_KEYS = frozenset(
    {
        "movement",
        "chapter",
        "title",
        "pov_id",
        "timeline_id",
        "motif_events",
        "hook",
        "words",
        "length_class",
        "status",
    }
)


def restricted_header(path: Path) -> dict[str, str]:
    """Read the complete closed ChapterHeader contract, failing on divergence."""
    text = Path(path).read_text(encoding="utf-8")
    match = FRONT_MATTER.match(text)
    if match is None:
        raise SystemExit(f"No restricted chapter header in {path}")
    values: dict[str, str] = {}
    for line in match.group(0).splitlines()[1:-1]:
        parsed = HEADER_LINE.fullmatch(line)
        if parsed is None:
            raise SystemExit(f"Malformed restricted chapter header line in {path}: {line!r}")
        key, value = parsed.group("key"), parsed.group("value")
        if key in values:
            raise SystemExit(f"Duplicate restricted chapter header key {key!r} in {path}")
        values[key] = value
    if set(values) != HEADER_KEYS:
        raise SystemExit(
            f"Invalid restricted chapter header keys in {path}; "
            f"missing={sorted(HEADER_KEYS - set(values))}, "
            f"unknown={sorted(set(values) - HEADER_KEYS)}"
        )
    return values


def chapter_title(path: Path) -> str:
    """Canonical reader-facing title from the required restricted header."""
    raw = restricted_header(path)["title"]
    try:
        title = json.loads(raw)
    except (json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"Malformed quoted chapter title in {path}: {exc}") from exc
    if not isinstance(title, str) or not title.strip() or any(c in title for c in "\r\n\x00"):
        raise SystemExit(f"Chapter title must be nonblank single-line text in {path}")
    return title


def extract_body(path: Path) -> str:
    """Prose body of a chapter, with the restricted front matter removed."""
    text = Path(path).read_text(encoding="utf-8")
    body = FRONT_MATTER.sub("", text, count=1).strip()
    if not body:
        raise SystemExit(f"No body text in {path}")
    return body


def paragraphs(body: str) -> list[str]:
    """Paragraphs, blank-line separated, whitespace collapsed within each."""
    return [
        " ".join(block.split())
        for block in re.split(r"\n\s*\n", body)
        if block.strip()
    ]


SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+|(?<=[\"”’])\s+(?=[A-Z“\"])")


def sentences(text: str) -> list[str]:
    return [s.strip() for s in SENTENCE_SPLIT.split(text) if s.strip()]


def spoken_text(path: Path) -> str:
    """The exact text handed to the engine: body, front matter gone, numerals spoken.

    Numeral verbalisation is not optional. Raw `19:52` was read aloud as
    "nineteen-five-two" by an earlier engine, and a transcript check cannot catch it
    because the digits round-trip correctly.
    """
    from normalize_speech_text import normalize  # noqa: PLC0415

    return normalize(extract_body(path))
