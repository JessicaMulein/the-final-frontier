#!/usr/bin/env python3
"""PostFileSave hook: run the chapter-scope objective check on a saved chapter.

Why
---
Chapter metadata drifts behind prose the moment the two are maintained by hand as
separate steps. Chapter 3 carried `words: 1191` against an observed 1186 because a
line edit shortened a sentence and the header stayed put; nothing noticed until a
whole-manuscript scan days later. The chapter-scope check costs 0.1s and would
have caught it on save.

Behaviour
---------
Reads the hook payload from stdin, finds the saved chapter path, runs the checker
against that one file, and appends any diagnostic to `.build/pending-defects.txt`.
`report_pending.py` surfaces that on the next prompt, because PostFileSave stdout
is not forwarded into the session.

Always exits 0. A save is never blocked and a hook failure never interrupts
writing; the worst case is a missed check, not a lost edit.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / ".tools" / "check_novel.py"
CHAPTERS = "The Final Frontier Novel/chapters/"
PENDING = REPO_ROOT / ".build" / "pending-defects.txt"


def iter_strings(value: object):
    """Walk an arbitrary JSON structure yielding every string leaf.

    The hook payload's key names are not depended on: any string that resolves to
    a chapter file is accepted. That keeps this working if the payload shape
    changes.
    """
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in value.values():
            yield from iter_strings(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            yield from iter_strings(item)


def find_chapter(payload: object) -> Path | None:
    for candidate in iter_strings(payload):
        if not candidate.endswith(".md") or CHAPTERS not in candidate:
            continue
        path = Path(candidate)
        if not path.is_absolute():
            path = REPO_ROOT / candidate
        if path.is_file():
            return path
    return None


def main() -> int:
    try:
        raw = sys.stdin.read()
    except Exception:
        raw = ""

    payload: object = None
    if raw.strip():
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = raw

    chapter = find_chapter(payload) if payload is not None else None
    if chapter is None and len(sys.argv) > 1:
        chapter = find_chapter(sys.argv[1:])
    if chapter is None:
        return 0

    try:
        result = subprocess.run(
            [
                sys.executable,
                str(CHECKER),
                "--scope",
                "chapter",
                "--chapter",
                str(chapter),
            ],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
    except Exception:
        return 0

    if result.returncode == 0:
        return 0

    lines = [
        line
        for line in (result.stdout + result.stderr).splitlines()
        if line.startswith(("ERROR", "WARN"))
    ] or ["exit %d with no parsed diagnostic" % result.returncode]

    try:
        PENDING.parent.mkdir(parents=True, exist_ok=True)
        with PENDING.open("a", encoding="utf-8") as handle:
            handle.write(f"{chapter.name}\n")
            for line in lines:
                handle.write(f"  {line}\n")
    except Exception:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
