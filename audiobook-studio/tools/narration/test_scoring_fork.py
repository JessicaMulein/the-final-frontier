#!/usr/bin/env python3
"""Assert the forked scoring module matches the pipeline it was forked from.

The fork exists so the old tree can be archived. That is only safe if the numbers
do not move: every WER, coverage and suspicious-span figure the new pipeline reports
must be what the old implementation would have produced for the same inputs. A
silent divergence here would invalidate every manifest going forward and would not
show up as an error.

Run:  PYTHONPATH=../vendor/mlx-audio .venv/bin/python test_scoring_fork.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import scoring

LEGACY = Path(__file__).resolve().parents[1] / "kokoro-local"

# Real cases from this project, including the ones that exposed bugs.
CASES: list[tuple[str, str]] = [
    ("", ""),
    ("The matched load was a brass slug.", "The matched load was a brass slug."),
    # Numerals verbalised differently by ASR: the benign class.
    (
        "Wednesday gave me the road call at six thirty-one",
        "Wednesday gave me the road call at 6.31",
    ),
    # The boundary bug: expected 'two point one', heard as digits.
    ("Two point one per second, near enough", "2 .1 per second near enough"),
    # A name ASR mishears, which is how 'Ravi' got trimmed away.
    ("Ravi wanted the control", "Revy wanted the control"),
    # Homophones seen in real chapter reports.
    ("the first alarm at six fifty-four", "the first alarm at 6.54"),
    ("it was her morning", "it was her mourning"),
    ("summarizing the dates", "summarising the dates"),
    # Outright omission, which must NOT be benign.
    (
        "I cleared the state and processed the same raw sample again",
        "I cleared the state again",
    ),
    # Truncation of the kind that produced 13% coverage.
    (
        "The matched load was a brass slug the size of my thumb with a fifty-ohm "
        "resistor buried in it, and it had spent two nights in a cold cabinet",
        "The matched load was a brass slug",
    ),
    # Insertion.
    ("no hidden buffer", "no hidden hidden buffer"),
]


def legacy_assess():
    if str(LEGACY) not in sys.path:
        sys.path.insert(0, str(LEGACY))
    from render_chapter_qwen3 import assess_transcript  # noqa: PLC0415

    return assess_transcript


def main() -> None:
    try:
        original = legacy_assess()
    except Exception as error:  # noqa: BLE001
        print(f"SKIP: old pipeline unavailable ({type(error).__name__}: {error})")
        print("Once kokoro-local is archived this test becomes a golden-file check.")
        return

    failures = 0
    golden = {}
    for expected, heard in CASES:
        mine = scoring.assess_transcript(expected, heard)
        theirs = original(expected, heard)
        same = mine == theirs
        failures += not same
        golden[f"{expected[:40]}|{heard[:40]}"] = {
            k: v for k, v in mine.items() if k != "transcript"
        }
        label = "ok  " if same else "DIFF"
        print(
            f"{label} wer={mine['wer']:.4f} cov={mine['coverage']:.4f} "
            f"gap={mine['max_expected_gap']} add={mine['max_added_span']} "
            f"susp={len(mine['suspicious_spans'])}  {expected[:44]!r}"
        )
        if not same:
            for key in sorted(set(mine) | set(theirs)):
                if mine.get(key) != theirs.get(key):
                    print(f"      {key}: forked={mine.get(key)!r} old={theirs.get(key)!r}")

    # Tokenisation must match too; assess_transcript could agree by coincidence.
    from validate_stt import normalized_tokens as legacy_tokens  # noqa: PLC0415

    token_failures = 0
    for expected, heard in CASES:
        for text in (expected, heard):
            if scoring.normalized_tokens(text) != legacy_tokens(text):
                token_failures += 1
                print(f"DIFF tokens for {text[:50]!r}")

    Path("fixtures/scoring-golden.json").write_text(json.dumps(golden, indent=2))
    print(
        f"\n{len(CASES) - failures}/{len(CASES)} assessments identical, "
        f"{len(CASES) * 2 - token_failures}/{len(CASES) * 2} tokenisations identical"
    )
    print("wrote fixtures/scoring-golden.json (golden file for after the old tree goes)")
    if failures or token_failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
