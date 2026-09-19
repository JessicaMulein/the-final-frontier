#!/usr/bin/env python3
"""UserPromptSubmit hook: surface objective defects and stale editions.

Why this trigger
----------------
PostFileSave and Stop stdout are not forwarded into the session, so a check that
runs there is recorded but unseen. UserPromptSubmit stdout *is* forwarded, which
makes it the one reliable place to report. Save-time checks accumulate into
`.build/pending-defects.txt`; this drains that file at the top of the next turn.

Also reports real manuscript defects independent of the save hook, filtered so the
expected noise does not drown the signal: the global gate reports 128
`CHAPTER_STATUS_NOT_FINAL` and one `FINALIZATION_GATE_MISSING` by design, because
nothing is finalised. Those are the gate working, not defects. Anything else is.

Always exits 0. A reporting hook must never block a prompt.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKER = REPO_ROOT / ".tools" / "check_novel.py"
PENDING = REPO_ROOT / ".build" / "pending-defects.txt"
EPUB = REPO_ROOT / "book" / "dist" / "the-final-frontier.epub"
MANUSCRIPT = REPO_ROOT / "The Final Frontier Novel"

# Reported by design while the manuscript is unfinished. Not defects.
EXPECTED_CODES = {"CHAPTER_STATUS_NOT_FINAL", "FINALIZATION_GATE_MISSING"}


def drain_pending() -> list[str]:
    try:
        if not PENDING.is_file():
            return []
        text = PENDING.read_text(encoding="utf-8").strip()
        PENDING.write_text("", encoding="utf-8")
        return text.splitlines() if text else []
    except Exception:
        return []


def real_defects() -> list[str]:
    try:
        result = subprocess.run(
            [sys.executable, str(CHECKER), "--scope", "global"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=120,
        )
    except Exception:
        return []

    found = []
    for line in (result.stdout + result.stderr).splitlines():
        if not line.startswith(("ERROR", "WARN")):
            continue
        parts = line.split(None, 2)
        if len(parts) > 1 and parts[1] in EXPECTED_CODES:
            continue
        found.append(line)
    return found


def newest_prose_mtime() -> float:
    newest = 0.0
    try:
        for path in MANUSCRIPT.rglob("*.md"):
            if "/planning/" in path.as_posix():
                continue
            newest = max(newest, path.stat().st_mtime)
    except Exception:
        return 0.0
    return newest


def editions_stale() -> bool:
    try:
        if not EPUB.is_file():
            return True
        return newest_prose_mtime() > EPUB.stat().st_mtime
    except Exception:
        return False


def main() -> int:
    blocks: list[str] = []

    saved = drain_pending()
    if saved:
        blocks.append(
            "Chapter checks failed on save since the last turn:\n"
            + "\n".join(saved)
        )

    defects = real_defects()
    if defects:
        blocks.append(
            "Objective manuscript defects outstanding "
            "(excluding the expected not-final reports):\n"
            + "\n".join(f"  {line}" for line in defects)
        )

    if editions_stale():
        blocks.append(
            "EPUB/PDF are older than the prose. "
            "`python3 .tools/build_book.py all` rebuilds them in ~13s."
        )

    if blocks:
        print("\n\n".join(blocks))
    return 0


if __name__ == "__main__":
    sys.exit(main())
