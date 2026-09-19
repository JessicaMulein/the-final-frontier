#!/usr/bin/env python3
"""Verbalise numerals before synthesis so a TTS model never sees raw digits.

Local audition tooling only — does not touch the Nova production path.

Why this exists
---------------
Chatterbox read `19:52` as "nineteen five two" and `14:08:17` one digit at a
time, producing 2-3 seconds of garbled audio mid-sentence that a listener hears
as a dropped sentence. Every transcript-based gate missed it twice over: whisper
reads the digits back correctly as numerals, and `validate_stt.py` explicitly
filters number/ordinal differences as benign noise.

The manuscript is instrument logs, so this is not incidental: 310 clock times
across 48 of 128 chapters, 69 of them H:MM:SS.

This module rewrites *only the synthesis input*. The manuscript is never
touched, and neither is the text the STT gate compares against — the existing
number/word filters in `validate_stt.py` already treat "19:52" and "nineteen
fifty-two" as equivalent.

Reading style follows how a narrator reads a 24-hour log aloud:

    19:52     -> nineteen fifty-two
    06:43     -> oh six forty-three
    07:02     -> seven oh two
    14:00     -> fourteen hundred
    14:08:17  -> fourteen oh eight and seventeen seconds
    9:06      -> nine oh six

Pass `--style plain` for "nineteen fifty-two" with no "oh" prefix on the hour.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

ONES = (
    "zero one two three four five six seven eight nine ten eleven twelve "
    "thirteen fourteen fifteen sixteen seventeen eighteen nineteen"
).split()
TENS = {2: "twenty", 3: "thirty", 4: "forty", 5: "fifty", 6: "sixty"}

TIME_RE = re.compile(r"(?<![\d:])(\d{1,2}):(\d{2})(?::(\d{2}))?(?![\d:])")
EQUATION_RE = re.compile(r"\b([a-zA-Z])\s*=\s*(\d+)\b")
DECIMAL_RE = re.compile(r"(?<![\d.])(\d+)\.(\d+)(?![\d.])")


def say_two_digit(value: int) -> str:
    """0-69 as words. 'zero' is caller's problem; minutes use say_minute."""
    if value < 20:
        return ONES[value]
    tens, units = divmod(value, 10)
    word = TENS.get(tens, "")
    return f"{word}-{ONES[units]}" if units else word


def say_hour(hour: int, *, style: str = "plain") -> str:
    """Hour as words.

    `plain` says the hour straight ("six forty-three", "seven oh two"), which is
    how a narrator reads a timestamp in prose. `radio` prefixes single-digit
    hours with "oh", which is how a dispatcher reads it aloud but which doubles
    awkwardly on times like 07:02 -> "oh seven oh two".
    """
    if style == "radio" and hour < 10:
        return f"oh {ONES[hour]}"
    return say_two_digit(hour)


def say_minute(minute: int) -> str:
    if minute == 0:
        return "hundred"
    if minute < 10:
        return f"oh {ONES[minute]}"
    return say_two_digit(minute)


def say_time(match: re.Match, *, style: str = "plain") -> str:
    hour = int(match.group(1))
    minute = int(match.group(2))
    seconds = match.group(3)
    if hour > 23 or minute > 59:
        return match.group(0)  # not a time; leave it alone
    spoken = f"{say_hour(hour, style=style)} {say_minute(minute)}"
    if seconds is not None:
        value = int(seconds)
        if value > 59:
            return match.group(0)
        unit = "second" if value == 1 else "seconds"
        spoken += f" and {say_two_digit(value)} {unit}"
    return spoken


def say_decimal(match: re.Match) -> str:
    whole, frac = match.group(1), match.group(2)
    digits = " ".join(ONES[int(d)] for d in frac)
    return f"{whole} point {digits}"


def normalize(text: str, *, style: str = "plain") -> str:
    """Rewrite forms that a TTS front end predictably mis-verbalises.

    Deliberately conservative: only patterns with observed failures are
    touched. Bare integers are left alone because the model reads them
    correctly and rewriting them risks changing the prose rhythm. Homograph
    rules are exact phrases confirmed in this manuscript; `red` is synthesis
    spelling only and the source text remains `read`.
    """
    out = TIME_RE.sub(lambda m: say_time(m, style=style), text)
    out = EQUATION_RE.sub(
        lambda m: f"{m.group(1)} equals {say_two_digit(int(m.group(2)))}"
        if int(m.group(2)) <= 69
        else f"{m.group(1)} equals {m.group(2)}",
        out,
    )
    out = DECIMAL_RE.sub(say_decimal, out)
    out = re.sub(
        r"\bthis time he read the dates\b",
        "this time he red the dates",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r"\bwhile Ravi read them out\b",
        "while Ravi red them out",
        out,
        flags=re.IGNORECASE,
    )
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manuscript-root", type=Path, default=None)
    parser.add_argument("--style", choices=("plain", "radio"), default="plain")
    parser.add_argument(
        "--preview",
        type=int,
        default=24,
        help="Show this many distinct rewrites and exit",
    )
    args = parser.parse_args()

    if not args.manuscript_root:
        samples = [
            "The request went into the queue at 19:52, and in the morning I would know.",
            "The call clock said 14:08:17.",
            "At 06:43 the filter found no candidate. At 07:02 the confidence crossed.",
            "Six hours put 3:06 at the bottom.",
            "At 14:00 the council accepted the withdrawal.",
            "Tested set: n=4, all Northline-adjacent adults.",
            "Two point one per second, near enough.",
        ]
        for s in samples:
            print(f"  before: {s}")
            print(f"  after : {normalize(s, style=args.style)}\n")
        return

    seen: dict[str, str] = {}
    files = 0
    for path in sorted(args.manuscript_root.rglob("*.md")):
        body = path.read_text(encoding="utf-8")
        hits = TIME_RE.findall(body)
        if hits:
            files += 1
        for match in TIME_RE.finditer(body):
            raw = match.group(0)
            if raw not in seen:
                seen[raw] = say_time(match, style=args.style)
    print(f"{len(seen)} distinct time strings across {files} chapter file(s)\n")
    for raw in sorted(seen, key=lambda s: (s.count(":"), s))[: args.preview]:
        print(f"  {raw:>10s}  ->  {seen[raw]}")
    if len(seen) > args.preview:
        print(f"  … {len(seen) - args.preview} more")


if __name__ == "__main__":
    main()
