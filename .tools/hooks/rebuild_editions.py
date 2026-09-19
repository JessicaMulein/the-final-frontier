#!/usr/bin/env python3
"""Stop hook: rebuild the EPUB and PDF when the prose has moved past them.

Why not on save
---------------
The whole text build is about 13 seconds — 0.1s to compile, 2.1s for EPUB, 11.1s
for the PDF through XeLaTeX. That is fine once at the end of a turn and wrong on
every keystroke, and nobody needs a typeset PDF mid-sentence.

Rebuilds only when something actually changed: the newest chapter, front-matter or
back-matter mtime against the built EPUB. Planning documents are excluded because
they do not appear in the editions.

Always exits 0. A build failure here is reported into `.build/pending-defects.txt`
for the next prompt rather than interrupting the session.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
BUILDER = REPO_ROOT / ".tools" / "build_book.py"
EPUB = REPO_ROOT / "book" / "dist" / "the-final-frontier.epub"
PDF = REPO_ROOT / "book" / "dist" / "the-final-frontier.pdf"
MANUSCRIPT = REPO_ROOT / "The Final Frontier Novel"
PENDING = REPO_ROOT / ".build" / "pending-defects.txt"


def newest_prose_mtime() -> float:
    newest = 0.0
    for path in MANUSCRIPT.rglob("*.md"):
        if "/planning/" in path.as_posix():
            continue
        newest = max(newest, path.stat().st_mtime)
    return newest


def note(message: str) -> None:
    try:
        PENDING.parent.mkdir(parents=True, exist_ok=True)
        with PENDING.open("a", encoding="utf-8") as handle:
            handle.write(message.rstrip() + "\n")
    except Exception:
        pass


def main() -> int:
    try:
        prose = newest_prose_mtime()
        if prose == 0.0:
            return 0
        built = min(
            (path.stat().st_mtime for path in (EPUB, PDF) if path.is_file()),
            default=0.0,
        )
        if built and prose <= built:
            return 0
    except Exception:
        return 0

    try:
        result = subprocess.run(
            [sys.executable, str(BUILDER), "all"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=900,
        )
    except Exception as exc:
        note(f"Edition rebuild could not start: {exc}")
        return 0

    if result.returncode != 0:
        tail = (result.stdout + result.stderr).strip().splitlines()[-6:]
        note(
            "Edition rebuild failed:\n"
            + "\n".join(f"  {line}" for line in tail)
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
