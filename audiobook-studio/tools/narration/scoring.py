#!/usr/bin/env python3
"""Text scoring for the Fish pipeline: tokenisation, WER, and transcript assessment.

Forked from the old pipeline so that `kokoro-local` can be frozen and eventually
archived without stranding this one. The two pipelines keep separate gates on
purpose -- their engines fail differently, and a threshold tuned for Fish has no
business changing how Chatterbox or QVoice is judged.

These particular functions were transferred programmatically rather than retyped,
because a slip in the WER or tokenisation definition would silently shift every
quality number the pipeline reports. Equivalence against the original is asserted
in `test_scoring_fork.py`.

What is deliberately NOT here: anything that reads audio. Transcription lives with
the caller, so this module stays importable without `mlx_whisper` and can be tested
on strings alone.
"""

from __future__ import annotations

import re
import unicodedata
from difflib import SequenceMatcher

TOKEN = re.compile(r"[^\W_]+(?:'[^\W_]+)*", re.UNICODE)


APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'", "＇": "'"})


_NUMBER_WORDS = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
    "eleven": "11",
    "twelve": "12",
    "thirteen": "13",
    "fourteen": "14",
    "fifteen": "15",
    "sixteen": "16",
    "seventeen": "17",
    "eighteen": "18",
    "nineteen": "19",
    "twenty": "20",
    "thirty": "30",
    "forty": "40",
    "fifty": "50",
    "sixty": "60",
    "seventy": "70",
    "eighty": "80",
    "ninety": "90",
    "hundred": "100",
}


def _numberish(tokens: list[str]) -> str:
    if not tokens:
        return ""
    if all(t.isdigit() for t in tokens):
        return "".join(tokens)
    out: list[str] = []
    ordinals = {
        "first": "1",
        "second": "2",
        "third": "3",
        "fourth": "4",
        "fifth": "5",
        "sixth": "6",
        "seventh": "7",
        "eighth": "8",
        "ninth": "9",
        "tenth": "10",
        "eleventh": "11",
        "twelfth": "12",
    }
    for t in tokens:
        if t in ordinals:
            out.append(ordinals[t])
        elif t.endswith(("st", "nd", "rd", "th")) and t[:-2].isdigit():
            out.append(t[:-2])
        elif t.endswith(("st", "nd", "rd", "th")) and t[:-2] in _NUMBER_WORDS:
            out.append(_NUMBER_WORDS[t[:-2]])
        elif t in _NUMBER_WORDS:
            out.append(_NUMBER_WORDS[t])
        elif t in {"point", "oh"}:
            continue
        elif t.isdigit():
            out.append(t)
        else:
            return ""
    return "".join(out)


def _normalize_spelling(token: str) -> str:
    token = token.replace("'", "")
    pairs = (
        ("neighbour", "neighbor"),
        ("neighbours", "neighbors"),
        ("digitiser", "digitizer"),
        ("travelling", "traveling"),
        ("travelled", "traveled"),
        ("organised", "organized"),
        ("recognised", "recognized"),
    )
    for uk, us in pairs:
        if token in {uk, us}:
            return us
    return token


def normalized_tokens(value: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFC", value).translate(APOSTROPHES).casefold()
    return tuple(TOKEN.findall(normalized))


def token_wer(expected: tuple[str, ...], actual: tuple[str, ...]) -> float:
    if not expected:
        return 0.0 if not actual else 1.0
    matcher = SequenceMatcher(a=expected, b=actual, autojunk=False)
    edits = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace":
            edits += max(i2 - i1, j2 - j1)
        elif tag == "delete":
            edits += i2 - i1
        elif tag == "insert":
            edits += j2 - j1
    return edits / len(expected)


def is_benign_replace(expected: list[str], actual: list[str]) -> bool:
    if not expected and not actual:
        return True
    e_num = _numberish(expected)
    a_num = _numberish(actual)
    if e_num and a_num and e_num == a_num:
        return True
    if len(expected) == 1 and len(actual) == 1:
        e = _normalize_spelling(expected[0])
        a = _normalize_spelling(actual[0])
        if e == a:
            return True
        # Weak function-word flips are usually ASR, not audible TTS failure.
        weak = {
            "a",
            "an",
            "the",
            "and",
            "in",
            "on",
            "at",
            "as",
            "to",
            "of",
            "i",
            "it",
            "that",
            "this",
            "than",
            "then",
            "with",
            "for",
            "from",
            "by",
            "or",
            "but",
        }
        if e in weak and a in weak:
            return True
        # Tense / plural micro-flips Whisper often invents.
        if e.rstrip("ds") == a.rstrip("ds") and min(len(e), len(a)) >= 4:
            return True
    # Spoken number phrases vs digits ("hundred and nine" ↔ "109").
    e_num2 = _numberish([t for t in expected if t not in {"and", "a", "the"}])
    a_num2 = _numberish([t for t in actual if t not in {"and", "a", "the"}])
    if e_num2 and a_num2 and e_num2 == a_num2:
        return True
    e_join = "".join(expected).replace("-", "")
    a_join = "".join(actual).replace("-", "")
    if e_join and e_join == a_join:
        return True
    return False


def assess_transcript(expected: str, heard_text: str) -> dict:
    """Assess an existing ASR transcript against expected synthesis text."""
    wanted = normalized_tokens(expected)
    heard = normalized_tokens(heard_text)
    if not wanted:
        return {
            "passed": not heard,
            "wer": 0.0 if not heard else 1.0,
            "coverage": 0.0,
            "max_expected_gap": 0,
            "max_added_span": len(heard),
            "suspicious_spans": [],
            "transcript": heard_text,
        }

    matcher = SequenceMatcher(a=wanted, b=heard, autojunk=False)
    max_expected_gap = 0
    max_added_span = 0
    suspicious: list[dict] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        expected_part = list(wanted[i1:i2])
        heard_part = list(heard[j1:j2])
        if tag in {"delete", "replace"}:
            max_expected_gap = max(max_expected_gap, i2 - i1)
        if tag in {"insert", "replace"}:
            max_added_span = max(max_added_span, j2 - j1)
        if tag == "replace" and not is_benign_replace(expected_part, heard_part):
            suspicious.append(
                {
                    "expected": expected_part,
                    "heard": heard_part,
                    "expected_len": i2 - i1,
                    "heard_len": j2 - j1,
                }
            )

    wer = token_wer(wanted, heard)
    coverage = len(heard) / len(wanted)
    passed = (
        wer <= 0.12
        and 0.94 <= coverage <= 1.06
        and max_expected_gap < 8
        and max_added_span < 8
    )
    return {
        "passed": passed,
        "wer": round(wer, 4),
        "coverage": round(coverage, 4),
        "max_expected_gap": max_expected_gap,
        "max_added_span": max_added_span,
        "suspicious_spans": suspicious[:8],
        "transcript": heard_text,
    }

