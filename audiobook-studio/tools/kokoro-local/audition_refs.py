#!/usr/bin/env python3
"""A/B a set of Chatterbox reference clips over a fixed test passage.

Local audition tooling only — does not touch the Nova production path.

Renders the same passage once per (reference x knob preset), then scores each
render two ways:

  fidelity  — mlx-whisper WER / insert / suspicious-replace, same gate family as
              `validate_stt.py`, but against an arbitrary passage rather than a
              whole chapter.
  prosody   — pitch range (semitone stdev over voiced frames) and dynamic range
              (dB, p95-p10 of frame RMS).

The prosody columns exist because WER alone cannot answer the question that
motivates a reference swap. A flat, evenly-paced render scores *well* on WER;
that is exactly the failure being chased away. Read the two together: prefer the
candidate that raises pitch/dynamic range without raising WER.

Neither number is an acceptance decision. Editorial voice acceptance is human —
these are a listen-list ordering and a regression guard.

Requires Metal, so run it in a normal Terminal rather than a sandbox.

Example
-------
  PY=.venv/bin/python
  $PY audition_refs.py \
      --ref-dir ../../../audiobook/kokoro-audition/emns-refs \
      --ref ../../../audiobook/kokoro-audition/common-voice-refs/uk-southern-female-03-tight.wav \
      --chapter-file "../../../The Final Frontier Novel/chapters/discovery-part/discovery-part-001-noise-floor.md" \
      --max-sentences 8 \
      --preset 0.7:0.3 --preset 0.5:0.5 \
      --out-dir ../../../audiobook/kokoro-audition/ref-audition
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))

from render_chapter_chatterbox import (  # noqa: E402
    MODEL_ID,
    SAMPLE_RATE,
    assemble_units,
    chunk_sentences,
    extract_body,
)
from validate_stt import (  # noqa: E402
    analyze_opcodes,
    normalized_tokens,
    token_wer,
    transcribe,
)
from prosody import dynamic_range_db, pitch_stats  # noqa: E402

WHISPER_MODEL = "mlx-community/whisper-large-v3-turbo"


# --------------------------------------------------------------------------- #
# passage handling
# --------------------------------------------------------------------------- #


def load_passage(
    *, passage_file: Path | None, chapter_file: Path | None, max_sentences: int
) -> str:
    if passage_file:
        text = passage_file.read_text(encoding="utf-8").strip()
        if not text:
            raise SystemExit(f"empty passage file: {passage_file}")
        return text
    if not chapter_file:
        raise SystemExit("provide --passage-file or --chapter-file")
    body = extract_body(chapter_file)
    units = chunk_sentences(body)
    if not units:
        raise SystemExit(f"no sentences found in {chapter_file}")
    picked = units[:max_sentences]
    return " ".join(u.text for u in picked)


# --------------------------------------------------------------------------- #
# audition
# --------------------------------------------------------------------------- #


@dataclass
class Result:
    ref: str
    ref_seconds: float
    exaggeration: float
    cfg_weight: float
    wav: str
    render_seconds: float
    wer: float
    insert_ops: int
    delete_ops: int
    replace_ops: int
    suspicious_replaces: int
    worst_insert_len: int
    pitch_median_hz: float
    pitch_stdev_semitones: float
    pitch_span_semitones: float
    dynamic_range_db: float
    transcript_preview: str


def parse_presets(raw: list[str]) -> list[tuple[float, float]]:
    presets: list[tuple[float, float]] = []
    for item in raw:
        try:
            exaggeration, cfg = item.split(":")
            presets.append((float(exaggeration), float(cfg)))
        except ValueError:
            raise SystemExit(f"bad --preset {item!r}; expected EXAG:CFG e.g. 0.5:0.5")
    return presets


def collect_refs(ref_dir: Path | None, refs: list[Path] | None) -> list[Path]:
    found: list[Path] = []
    if ref_dir:
        found.extend(sorted(p for p in ref_dir.glob("*.wav")))
    for ref in refs or []:
        if ref not in found:
            found.append(ref)
    missing = [p for p in found if not p.is_file()]
    if missing:
        raise SystemExit("missing ref(s): " + ", ".join(str(m) for m in missing))
    if not found:
        raise SystemExit("no reference WAVs given (--ref-dir and/or --ref)")
    return found


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--ref-dir", type=Path, default=None)
    parser.add_argument("--ref", type=Path, action="append", default=None)
    parser.add_argument("--passage-file", type=Path, default=None)
    parser.add_argument("--chapter-file", type=Path, default=None)
    parser.add_argument("--max-sentences", type=int, default=8)
    parser.add_argument(
        "--preset",
        action="append",
        default=None,
        help="EXAG:CFG pair; repeatable. Default: 0.7:0.3 (current) and 0.5:0.5",
    )
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--gate-breaths", action="store_true", default=True)
    parser.add_argument("--no-gate-breaths", dest="gate_breaths", action="store_false")
    parser.add_argument("--whisper-model", default=WHISPER_MODEL)
    parser.add_argument("--language", default="en")
    parser.add_argument("--skip-stt", action="store_true", help="Render + prosody only")
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()

    presets = parse_presets(args.preset or ["0.7:0.3", "0.5:0.5"])
    refs = collect_refs(args.ref_dir, args.ref)
    passage = load_passage(
        passage_file=args.passage_file,
        chapter_file=args.chapter_file,
        max_sentences=args.max_sentences,
    )
    units = chunk_sentences(passage)
    expected_toks = normalized_tokens(passage)

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "passage.txt").write_text(passage, encoding="utf-8")

    print(f"passage: {len(expected_toks)} tokens, {len(units)} sentence unit(s)")
    print(f"refs   : {len(refs)}")
    print(f"presets: {', '.join(f'{e}/{c}' for e, c in presets)}")
    print(f"renders: {len(refs) * len(presets)}\n")

    from mlx_audio.tts.utils import load_model

    print(f"Loading {MODEL_ID} once…")
    model = load_model(MODEL_ID)

    results: list[Result] = []
    for ref in refs:
        ref_audio, ref_sr = sf.read(str(ref), always_2d=False)
        ref_seconds = len(ref_audio) / ref_sr
        for exaggeration, cfg_weight in presets:
            tag = f"{ref.stem}__e{exaggeration:g}c{cfg_weight:g}".replace(".", "")
            dest = out_dir / f"audition-{tag}.wav"
            if args.skip_existing and dest.is_file():
                print(f"skip (exists) {dest.name}")
                audio, _ = sf.read(str(dest), always_2d=False)
                audio = np.asarray(audio, dtype=np.float32)
            else:
                print(f"render {ref.name}  e={exaggeration} cfg={cfg_weight} …")
                audio = assemble_units(
                    model,
                    units,
                    ref_audio=str(ref),
                    exaggeration=exaggeration,
                    cfg_weight=cfg_weight,
                    gate_breaths=args.gate_breaths,
                )
                sf.write(str(dest), audio, SAMPLE_RATE)

            audio = np.asarray(audio, dtype=np.float32)
            if audio.ndim > 1:
                audio = audio.mean(axis=1)

            median_hz, pitch_sd, pitch_span = pitch_stats(audio)
            dyn = dynamic_range_db(audio)

            wer = 0.0
            inserts = deletes = replaces = suspicious_n = worst_len = 0
            preview = ""
            if not args.skip_stt:
                transcript = transcribe(
                    dest, model=args.whisper_model, language=args.language
                )
                actual_toks = normalized_tokens(transcript)
                wer = token_wer(expected_toks, actual_toks)
                _, worst_insert, inserts, deletes, replaces, suspicious = analyze_opcodes(
                    expected_toks, actual_toks
                )
                suspicious_n = len(suspicious)
                worst_len = len(worst_insert["transcript"]) if worst_insert else 0
                preview = transcript[:200]

            results.append(
                Result(
                    ref=ref.name,
                    ref_seconds=round(ref_seconds, 2),
                    exaggeration=exaggeration,
                    cfg_weight=cfg_weight,
                    wav=dest.name,
                    render_seconds=round(audio.size / SAMPLE_RATE, 2),
                    wer=round(wer, 4),
                    insert_ops=inserts,
                    delete_ops=deletes,
                    replace_ops=replaces,
                    suspicious_replaces=suspicious_n,
                    worst_insert_len=worst_len,
                    pitch_median_hz=round(median_hz, 1),
                    pitch_stdev_semitones=round(pitch_sd, 2),
                    pitch_span_semitones=round(pitch_span, 2),
                    dynamic_range_db=round(dyn, 1),
                    transcript_preview=preview,
                )
            )

    # ------------------------------------------------------------------ #
    # table
    # ------------------------------------------------------------------ #
    print("\n" + "=" * 108)
    print("FIDELITY (lower better)          PROSODY (higher = more expressive)")
    print("=" * 108)
    header = (
        f"{'ref':30s} {'ref_s':>6s} {'knobs':>9s} {'WER':>7s} {'ins':>4s} "
        f"{'susp':>5s} {'pitchSD':>8s} {'span':>6s} {'dynDB':>6s}"
    )
    print(header)
    print("-" * 108)
    for r in sorted(results, key=lambda r: (r.ref, r.exaggeration)):
        print(
            f"{r.ref[:30]:30s} {r.ref_seconds:6.2f} "
            f"{f'{r.exaggeration:g}/{r.cfg_weight:g}':>9s} "
            f"{r.wer:7.4f} {r.insert_ops:4d} {r.suspicious_replaces:5d} "
            f"{r.pitch_stdev_semitones:8.2f} {r.pitch_span_semitones:6.2f} "
            f"{r.dynamic_range_db:6.1f}"
        )
    print("-" * 108)
    print(
        "pitchSD/span = semitone spread of the pitch track; dynDB = p95-p10 frame RMS.\n"
        "Look for a candidate that holds WER at or below the incumbent while\n"
        "raising pitch span and dynamic range. Then listen before deciding."
    )

    report = out_dir / "ref-audition.json"
    report.write_text(
        json.dumps(
            {
                "model": MODEL_ID,
                "whisper_model": args.whisper_model,
                "passage_tokens": len(expected_toks),
                "sentence_units": len(units),
                "gate_breaths": args.gate_breaths,
                "results": [asdict(r) for r in results],
            },
            indent=2,
        )
    )
    print(f"\nreport: {report}")


if __name__ == "__main__":
    main()
