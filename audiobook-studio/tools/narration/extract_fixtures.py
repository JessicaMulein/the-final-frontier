#!/usr/bin/env python3
"""Preserve the defects confirmed by ear as small regression fixtures.

Why this runs before any cleanup
--------------------------------
The QVoice review directories are about 350 MB and are superseded as audio. But
they are also the only recordings of the defects a listener actually caught, and
every one of them passed the automated gates in place at the time. Delete them and
the evidence that motivates the acoustic judges is gone; there is no way to
regenerate a specific stochastic stutter.

So each defect is cut to a few seconds, paired with what the listener heard and
which gates wrongly passed it, and kept. The bulk audio then becomes disposable.

Each fixture also carries a `clean_sibling` where one exists: a gate that flags the
defect is worthless if it also flags the good take of the same words.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf

REPO = Path(__file__).resolve().parents[3]
REVIEW = REPO / "audiobook/qvoice-production/review"

# Coordinates come from the session where each defect was diagnosed. Absolute
# times are used where a manifest boundary is not the thing of interest.
FIXTURES = [
    {
        "id": "intra_word_stutter",
        "source": "chapter2-v2/006-chapter-002-v2.wav",
        "start": 205.0,
        "end": 211.5,
        "heard": "audible doubling on the 'four' of 'six fifty-four'",
        "reported_at": "3:29-3:30",
        "passed_gates": [
            "chapter WER 0.019",
            "coverage 0.9964",
            "unit boundary residue_peak 0.0",
            "loop/stall gate",
            "pace scoring preferred this take over its rerolls",
        ],
        "why_invisible": "Whisper normalises the stutter into a single correct "
        "'.54' token, so no text metric can see it",
        "clean_sibling": {
            "source": "chapter2-v4/006-chapter-002-v4.wav",
            "start": 205.0,
            "end": 211.5,
            "note": "seed 71 reroll of the same words",
        },
    },
    {
        "id": "truncated_opening_numeric",
        "source": "chapter1-v2/005-chapter-001-v2.wav",
        "start": 201.0,
        "end": 214.0,
        "heard": "unit begins at 'per second'; 'Two point one' is missing",
        "reported_at": "3:25-3:28",
        "passed_gates": ["chapter WER 0.023", "coverage 0.994", "residue_peak 0.0"],
        "why_invisible": "the boundary search took the next exact ASR word match; "
        "expected 'two point one' was heard as '2 1', a replace opcode the aligner "
        "skipped over",
        "clean_sibling": {
            "source": "chapter1-v3/005-chapter-001-v3.wav",
            "start": 201.0,
            "end": 214.0,
            "note": "after the align_new_text_boundary fix",
        },
    },
    {
        "id": "truncated_opening_name",
        "source": "chapter1-v2/005-chapter-001-v2.wav",
        "start": 322.0,
        "end": 334.0,
        "heard": "unit begins at 'wanted'; the name 'Ravi' is missing",
        "reported_at": "found by manifest scan, not by ear",
        "passed_gates": ["chapter WER 0.023", "unit WER 0.027", "coverage 0.9865"],
        "why_invisible": "ASR heard 'Ravi' as 'Revy', so the aligner anchored on the "
        "following exact word",
        "clean_sibling": {
            "source": "chapter1-v3/005-chapter-001-v3.wav",
            "start": 322.0,
            "end": 334.0,
            "note": "seed 73 after the fix",
        },
    },
    {
        "id": "cold_start_burst",
        "source": "chapter3-short/007-chapter-003-short.wav",
        "start": 0.0,
        "end": 3.0,
        "heard": "digital glitch on the first two words, 'the matched load'",
        "reported_at": "0:00",
        "passed_gates": ["declick reported 0 clicks", "chapter WER 0.024"],
        "why_invisible": "it is not a click but a spectrally degenerate onset: "
        "digital silence to 5.8x the chapter median level inside one 20 ms frame, "
        "peaking at 8.2x, with sample steps to 0.11",
        "clean_sibling": {
            "source": "chapter3-v2/007-chapter-003-v2.wav",
            "start": 0.0,
            "end": 3.0,
            "note": "after adding the disposable lead-in",
        },
    },
    {
        "id": "warmup_residue_stutter",
        "source": "chapter3-short/007-chapter-003-short.wav",
        "start": 330.5,
        "end": 337.0,
        "heard": "stutter just after the seam, on words the previous unit had just "
        "spoken ('...had not tested them')",
        "reported_at": "5:33",
        "passed_gates": [
            "chapter WER 0.019",
            "residue below every threshold then in place",
        ],
        "why_invisible": "a flat 60 ms back-off was carved out of the warm-up when "
        "Whisper reported the two words as contiguous, leaving voiced audio at 1.3x "
        "the median level",
        "clean_sibling": {
            "source": "chapter3-v2/007-chapter-003-v2.wav",
            "start": 325.0,
            "end": 331.5,
            "note": "after the forward-biased quiet_cut",
        },
    },
    {
        "id": "within_unit_level_fade",
        "source": "chapter3-short/007-chapter-003-short.wav",
        "start": 298.4,
        "end": 333.3,
        "heard": "narrator trailing off toward the end of the unit",
        "reported_at": "end of unit 1 and end of chapter",
        "passed_gates": ["per-unit gain matching", "chapter WER 0.019"],
        "why_invisible": "gain matching applies one gain per unit, so it cannot see "
        "a slope inside a unit; this unit fell 6.46 dB start to end",
        "clean_sibling": {
            "source": "chapter3-v2/007-chapter-003-v2.wav",
            "start": 298.0,
            "end": 333.0,
            "note": "after flatten_level; same unit measured -0.27 dB",
        },
    },
    {
        "id": "articulation_outlier",
        "source": "chapter3-v2/007-chapter-003-v2.wav",
        "start": 453.5,
        "end": 477.7,
        "heard": "still drifting at the end of the chapter",
        "reported_at": "end of chapter 3",
        "passed_gates": [
            "chapter WER 0.0185",
            "drift profile (relative to the unit's own median, so a uniformly slow "
            "unit reads as flat)",
        ],
        "why_invisible": "articulation 7.196 against a chapter median of 8.059, and "
        "the highest pause load of any unit, but normalising to the unit's own "
        "median hides it",
        "clean_sibling": None,
    },
]


def cut(source: Path, start: float, end: float) -> tuple[np.ndarray, int] | None:
    if not source.is_file():
        return None
    info = sf.info(str(source))
    rate = info.samplerate
    begin = max(0, int(start * rate))
    finish = min(info.frames, int(end * rate))
    if finish <= begin:
        return None
    audio, _ = sf.read(str(source), start=begin, stop=finish, always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return audio, rate


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, default=Path("fixtures"))
    args = p.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    index = []
    missing = []

    for spec in FIXTURES:
        record = {k: v for k, v in spec.items() if k != "clean_sibling"}
        source = REVIEW / spec["source"]
        result = cut(source, spec["start"], spec["end"])
        if result is None:
            missing.append(spec["source"])
            print(f"  MISSING {spec['id']}: {spec['source']}")
            continue
        audio, rate = result
        defect_path = args.out / f"{spec['id']}.wav"
        sf.write(str(defect_path), audio, rate, subtype="PCM_16")
        record["file"] = defect_path.name
        record["seconds"] = round(audio.size / rate, 2)
        record["sample_rate"] = rate

        sibling = spec.get("clean_sibling")
        if sibling:
            sib = cut(REVIEW / sibling["source"], sibling["start"], sibling["end"])
            if sib:
                sib_audio, sib_rate = sib
                sib_path = args.out / f"{spec['id']}__clean.wav"
                sf.write(str(sib_path), sib_audio, sib_rate, subtype="PCM_16")
                record["clean_sibling"] = {
                    "file": sib_path.name,
                    "seconds": round(sib_audio.size / sib_rate, 2),
                    "note": sibling["note"],
                    "source": sibling["source"],
                }
            else:
                missing.append(sibling["source"])
        index.append(record)
        print(
            f"  {spec['id']:28s} {record['seconds']:5.2f}s"
            + ("  +clean" if record.get("clean_sibling") else "")
        )

    (args.out / "fixtures.json").write_text(
        json.dumps(
            {
                "note": "Each entry is a defect a listener confirmed that every "
                "automated gate of the time passed. A new gate must flag the defect "
                "and must not flag its clean sibling.",
                "fixtures": index,
                "missing_sources": sorted(set(missing)),
            },
            indent=2,
        )
    )
    print(f"\n{len(index)} fixtures -> {args.out}/fixtures.json")
    if missing:
        print(f"missing sources ({len(set(missing))}): {sorted(set(missing))}")


if __name__ == "__main__":
    main()
