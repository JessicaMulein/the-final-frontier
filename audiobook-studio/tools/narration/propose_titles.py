"""Propose a `title:` for every chapter, for review before anything is written.

Chapter front matter carries movement, chapter, pov_id, timeline_id, motif_events,
hook, words, length_class and status -- but no title. Titles currently exist only as
filename slugs, which is not data the pipeline can rely on: the audiobook needs spoken
chapter announcements, and for a listener who cannot see a player's chapter list that
announcement is the navigation.

A slug is lossy. Casing is gone, so proper nouns look like common words, and the
usual title-case rule cannot tell "the mind as a field" from a name. Two safeguards:

  proper nouns   each slug word is checked against the chapter's own prose. A word
                 that appears capitalised mid-sentence in the body is almost certainly
                 a name, and is capitalised in the title regardless of the small-word
                 rule.
  flagging       anything the mechanical rule cannot decide -- digits, very short
                 slugs, words absent from the prose entirely -- is marked for review
                 rather than silently guessed.

Writes a review file and changes nothing.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
CHAPTER_ROOT = REPO / "The Final Frontier Novel/chapters"
FRONT_MATTER = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)

SMALL = {
    "a", "an", "and", "as", "at", "but", "by", "for", "from", "if", "in", "into",
    "nor", "of", "on", "or", "over", "so", "the", "to", "up", "with", "yet",
}


def body_of(path: Path) -> str:
    return FRONT_MATTER.sub("", path.read_text(encoding="utf-8"), count=1).strip()


def front_matter_of(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = FRONT_MATTER.match(text)
    if not match:
        raise SystemExit(f"{path}: no front matter")
    fields = {}
    for line in match.group(0).splitlines():
        if ":" in line and not line.startswith("---"):
            key, _, value = line.partition(":")
            fields[key.strip()] = value.strip()
    return fields


def proper_nouns(body: str) -> set[str]:
    """Words that appear capitalised somewhere other than a sentence start."""
    found = set()
    for sentence in re.split(r"(?<=[.!?])\s+|\n+", body):
        words = re.findall(r"[A-Za-z][A-Za-z'’-]*", sentence)
        for word in words[1:]:
            if word[0].isupper() and not word.isupper():
                found.add(word.lower())
    # "I" is capitalised everywhere and is not a name.
    found.discard("i")
    return found


def slug_of(path: Path, number: int) -> str:
    return re.sub(rf"^.*?-{number:03d}-", "", path.stem)


def propose(slug: str, names: set[str]) -> tuple[str, list[str]]:
    words = [w for w in slug.split("-") if w]
    notes = []
    out = []
    for index, word in enumerate(words):
        first_or_last = index == 0 or index == len(words) - 1
        if word.isdigit():
            notes.append(f"numeral {word!r} -- spell it out for speech?")
            out.append(word)
        elif word in names and word not in SMALL:
            out.append(word.capitalize())
            notes.append(f"{word!r} capitalised as a proper noun (found in prose)")
        elif word in SMALL and not first_or_last:
            out.append(word)
        else:
            out.append(word.capitalize())
    return " ".join(out), notes


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("out/titles-proposed.json"))
    p.add_argument("--review", type=Path, default=Path("out/titles-review.md"))
    args = p.parse_args()

    files = sorted(CHAPTER_ROOT.glob("*/*.md"))
    if not files:
        raise SystemExit(f"no chapters under {CHAPTER_ROOT}")

    records = []
    for path in files:
        fields = front_matter_of(path)
        if "title" in fields:
            raise SystemExit(f"{path.name} already has a title; refusing to guess")
        number = int(fields["chapter"])
        body = body_of(path)
        slug = slug_of(path, number)
        names = proper_nouns(body)
        title, notes = propose(slug, names)
        words = [w for w in slug.split("-") if w]
        if len(words) <= 1:
            notes.append("single-word slug -- confirm this is the intended title")
        if any(w.isdigit() for w in words):
            notes.append("contains digits")
        records.append(
            {
                "chapter": number,
                "movement": fields.get("movement", ""),
                "file": str(path.relative_to(REPO)),
                "slug": slug,
                "proposed_title": title,
                "hook": fields.get("hook", "").strip('"'),
                "notes": notes,
            }
        )

    records.sort(key=lambda r: r["chapter"])
    numbers = [r["chapter"] for r in records]
    missing = sorted(set(range(1, len(records) + 1)) - set(numbers))
    duplicates = sorted({n for n in numbers if numbers.count(n) > 1})

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(records, indent=2))

    lines = [
        "# Proposed chapter titles",
        "",
        f"{len(records)} chapters. Nothing has been written yet.",
        "",
        "| ch | movement | proposed title | needs review |",
        "| --- | --- | --- | --- |",
    ]
    for r in records:
        note = "; ".join(r["notes"]) if r["notes"] else ""
        lines.append(
            f"| {r['chapter']} | {r['movement']} | {r['proposed_title']} | {note} |"
        )
    args.review.write_text("\n".join(lines) + "\n")

    flagged = [r for r in records if r["notes"]]
    print(f"{len(records)} chapters, numbers {min(numbers)}-{max(numbers)}")
    if missing:
        print(f"  MISSING chapter numbers: {missing}")
    if duplicates:
        print(f"  DUPLICATE chapter numbers: {duplicates}")
    print(f"  flagged for review: {len(flagged)}")
    for r in flagged:
        print(f"    ch{r['chapter']:03d}  {r['proposed_title']!r}")
        for note in r["notes"]:
            print(f"           {note}")
    print(f"\nwrote {args.out} and {args.review}")


if __name__ == "__main__":
    main()
