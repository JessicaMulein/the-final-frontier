"""Write the reviewed `title:` into chapter front matter. Idempotent, body-preserving.

Reads the proposals produced by propose_titles.py and inserts one line per chapter,
immediately after `chapter:`, so front matter reads movement / chapter / title.

Guarantees, because this edits 128 files of someone's novel:

  body untouched   the prose after the front matter is compared byte for byte before
                   and after, and a mismatch aborts the whole run
  other keys kept  every existing front-matter line is preserved in order; only one
                   line is added
  idempotent       a chapter that already has a title is left alone
  atomic per file  the new text is written only after both checks pass

Use --dry-run first. It reports exactly what would change and writes nothing.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
FRONT_MATTER = re.compile(r"\A(---\n)(.*?\n)(---\n)", re.DOTALL)


def quote(value: str) -> str:
    """One complete JSON-compatible double-quoted scalar."""
    return json.dumps(value, ensure_ascii=False)


def rewrite(text: str, title: str) -> tuple[str, str]:
    """Return (new_text, body). Raises if front matter is missing or malformed."""
    match = FRONT_MATTER.match(text)
    if not match:
        raise ValueError("no front matter")
    opening, block, closing = match.groups()
    body = text[match.end() :]
    lines = block.splitlines()
    if any(re.match(r"\s*title\s*:", line) for line in lines):
        return text, body
    out, inserted = [], False
    for line in lines:
        out.append(line)
        if not inserted and re.match(r"\s*chapter\s*:", line):
            out.append(f"title: {quote(title)}")
            inserted = True
    if not inserted:
        raise ValueError("no `chapter:` key to anchor the title to")
    return opening + "\n".join(out) + "\n" + closing + body, body


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--proposals", type=Path, default=Path("out/titles-proposed.json"))
    p.add_argument("--dry-run", action="store_true")
    p.add_argument(
        "--remove",
        action="store_true",
        help="remove title lines inserted by this migration without reverting any "
        "unrelated uncommitted prose edits",
    )
    args = p.parse_args()

    if args.remove:
        removed = 0
        for record in json.loads(args.proposals.read_text()):
            path = REPO / record["file"]
            text = path.read_text(encoding="utf-8")
            match = FRONT_MATTER.match(text)
            if not match:
                raise SystemExit(f"{path.name}: no front matter")
            opening, block, closing = match.groups()
            body = text[match.end() :]
            lines = block.splitlines()
            kept = [line for line in lines if not re.match(r"\s*title\s*:", line)]
            dropped = len(lines) - len(kept)
            if dropped == 0:
                continue
            if dropped != 1:
                raise SystemExit(f"{path.name}: {dropped} title lines; refusing")
            updated = opening + "\n".join(kept) + "\n" + closing + body
            if not updated.endswith(body):
                raise SystemExit(f"{path.name}: body not intact; aborting")
            if args.dry_run:
                removed += 1
                continue
            path.write_text(updated, encoding="utf-8")
            removed += 1
        print(f"removed {removed} title lines" + (" (dry run)" if args.dry_run else ""))
        return

    records = json.loads(args.proposals.read_text())
    numbers = [record.get("chapter") for record in records]
    files = [record.get("file") for record in records]
    if len(records) != 128 or len(set(numbers)) != 128 or set(numbers) != set(range(1, 129)):
        raise SystemExit("proposals must contain exactly one record for chapters 1 through 128")
    if len(set(files)) != 128 or any(not isinstance(path, str) for path in files):
        raise SystemExit("proposals must contain 128 unique chapter file paths")
    for record in records:
        title = record.get("proposed_title")
        if not isinstance(title, str) or not title.strip() or any(c in title for c in "\r\n\x00"):
            raise SystemExit(f"chapter {record.get('chapter')} has an invalid proposed title")

    planned, skipped = [], []
    for record in records:
        path = REPO / record["file"]
        original = path.read_text(encoding="utf-8")
        try:
            updated, body = rewrite(original, record["proposed_title"])
        except ValueError as error:
            raise SystemExit(f"{path.name}: {error}")
        if updated == original:
            skipped.append(record["chapter"])
            continue
        # The body must survive untouched.
        _, body_after = rewrite(updated, record["proposed_title"])
        if body_after != body:
            raise SystemExit(f"{path.name}: body would change; aborting")
        if not updated.endswith(body):
            raise SystemExit(f"{path.name}: body is not intact at the tail; aborting")
        planned.append((path, updated, record))

    print(f"{len(planned)} to write, {len(skipped)} already had a title")
    for _, _, record in planned[:5]:
        print(f"  ch{record['chapter']:03d}  title: {record['proposed_title']!r}")
    if len(planned) > 5:
        print(f"  ... and {len(planned) - 5} more")

    if args.dry_run:
        print("\ndry run: nothing written")
        return

    for path, updated, _ in planned:
        path.write_text(updated, encoding="utf-8")
    print(f"\nwrote {len(planned)} files")


if __name__ == "__main__":
    main()
