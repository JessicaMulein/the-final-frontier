#!/usr/bin/env python3
"""Detect loop / babble collapse in a rendered chapter WAV.

Local audition tooling only — does not touch the Nova production path.

Why this exists
---------------
`validate_stt.py` gates on WER, longest insert span and suspicious replaces.
That combination has a blind spot: when Chatterbox collapses into degenerate
repetition, whisper often transcribes the run as many *tiny or empty* segments.
No single insert span gets long, WER barely moves, and the chapter can PASS with
30 seconds of garbage in it.

Observed on chapter 1 with a 0.5/0.5 render: a 29.5 s stretch transcribed as
"2.1" roughly 25 times, plus a 30 s stretch that collapsed to "No fit.", and the
gate still returned PASS.

Signals used here, all duration-aware rather than token-aware:

  stall     — a segment whose words-per-second is far below natural speech.
              30 s of audio carrying two words is the signature of a collapse.
  repeat    — the same short segment text recurring back to back.
  empty     — whisper emitting zero-word segments.
  bloat     — total audio far longer than the manuscript word count implies.

None of these replace listening; they turn a silent false PASS into a loud
failure with timestamps to jump to.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from pathlib import Path

import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))

# A stall is judged against the render's *own* median pace, not an absolute
# words/sec constant. Different reference clips legitimately differ in tempo:
# the EMNS neutral seed narrates at ~2.4 wps where uk-southern-female-03 runs
# ~3.3 wps. An absolute threshold mistakes a slow voice for a broken one.
STALL_PACE_FRACTION = 0.30
STALL_MIN_SECONDS = 4.0
REPEAT_MIN_RUN = 4

# Consecutive self-repetition. Prose does not say the same multi-word phrase
# three times in a row; a collapsed decoder does. Requiring a minimum total span
# as well keeps incidental doubling ("that that", "had had") from tripping it.
REPEAT_MIN_CONSECUTIVE = 3
REPEAT_MAX_PHRASE_WORDS = 12
REPEAT_MIN_TOKENS = 12

# Pace-independent completeness check: did the render actually say the words.
# Bounded on BOTH sides. Under-coverage means dropped content; over-coverage
# means the model added words, which is what babble does. Clean chapters measure
# 0.985-1.012; chapter 5's two babbling attempts measured 1.132 and 1.127.
WORD_COVERAGE_FAIL = 0.97
WORD_COVERAGE_HIGH = 1.07

WORD = re.compile(r"[^\W_]+", re.UNICODE)


@dataclass
class Finding:
    kind: str
    start: float
    end: float
    detail: str

    @property
    def seconds(self) -> float:
        return self.end - self.start


@dataclass
class LoopReport:
    wav: str
    audio_seconds: float
    expected_words: int
    transcript_words: int
    word_coverage: float
    words_per_second: float
    median_segment_wps: float
    stalled_seconds: float
    repeated_seconds: float
    empty_segments: int
    segments_past_eof: int
    passed: bool
    findings: list[dict] = field(default_factory=list)


def normalize(text: str) -> str:
    return " ".join(WORD.findall(text.lower()))


def transcribe_full(wav: Path, *, model: str, language: str) -> tuple[str, list[dict]]:
    """Transcribe once, returning both the flat text and the segment list.

    Lets a caller feed the STT gate and this loop gate from a single whisper
    pass — worth roughly a minute per chapter, which matters across a full book.
    """
    import mlx_whisper

    result = mlx_whisper.transcribe(
        str(wav),
        path_or_hf_repo=model,
        language=language,
        word_timestamps=False,
        verbose=False,
        # See the note in validate_stt.transcribe: leaving context conditioning
        # on makes whisper invent repetition loops, which this module would then
        # report as `babble` in a perfectly good render.
        condition_on_previous_text=False,
    )
    return (result.get("text") or "").strip(), list(result.get("segments") or [])


def analyse(
    wav: Path,
    expected_text: str,
    *,
    whisper_model: str,
    language: str,
    segments: list[dict] | None = None,
    transcript_text: str | None = None,
    stall_pace_fraction: float = STALL_PACE_FRACTION,
    stall_min_seconds: float = STALL_MIN_SECONDS,
    coverage_fail: float = WORD_COVERAGE_FAIL,
    coverage_high: float = WORD_COVERAGE_HIGH,
) -> LoopReport:
    import statistics

    audio, sr = sf.read(str(wav), always_2d=False)
    audio_seconds = len(audio) / sr
    expected_words = len(WORD.findall(expected_text))

    if segments is None:
        transcript_from_call, segments = transcribe_full(
            wav, model=whisper_model, language=language
        )
        if transcript_text is None:
            transcript_text = transcript_from_call
    raw_segments = segments

    # Whisper can emit segments that start beyond the end of the audio, and it
    # tends to hallucinate repetition when it does. Those are artefacts of the
    # transcriber, not defects in the render, so drop them before judging.
    segments = []
    past_eof = 0
    for seg in raw_segments:
        start = float(seg.get("start", 0.0))
        if start >= audio_seconds:
            past_eof += 1
            continue
        end = min(float(seg.get("end", 0.0)), audio_seconds)
        segments.append({"start": start, "end": end, "text": seg.get("text", "")})

    findings: list[Finding] = []
    transcript_words = 0
    empty = 0

    # Establish this render's own pace from segments long enough to be reliable.
    paces = []
    for seg in segments:
        words = len(normalize(seg["text"]).split())
        span = seg["end"] - seg["start"]
        if words >= 3 and span >= 1.0:
            paces.append(words / span)
    median_wps = statistics.median(paces) if paces else 0.0
    stall_wps = median_wps * stall_pace_fraction if median_wps else 0.0

    # --- stalls: long spans well below this render's own pace ------------ #
    for seg in segments:
        text = normalize(seg["text"])
        words = len(text.split())
        transcript_words += words
        start, end = seg["start"], seg["end"]
        span = end - start
        if words == 0:
            empty += 1
            continue
        if stall_wps and span >= stall_min_seconds and (words / span) < stall_wps:
            findings.append(
                Finding(
                    kind="stall",
                    start=start,
                    end=end,
                    detail=f"{words} word(s) in {span:.1f}s "
                    f"({words / span:.2f} wps vs median {median_wps:.2f}): {text[:56]!r}",
                )
            )

    # --- repeats: same short text back to back -------------------------- #
    run_text: str | None = None
    run_start = 0.0
    run_end = 0.0
    run_len = 0

    def flush_run() -> None:
        nonlocal run_len
        if run_text and run_len >= REPEAT_MIN_RUN:
            findings.append(
                Finding(
                    kind="repeat",
                    start=run_start,
                    end=run_end,
                    detail=f"{run_len}x {run_text[:40]!r}",
                )
            )
        run_len = 0

    for seg in segments:
        text = normalize(seg["text"])
        start, end = seg["start"], seg["end"]
        if text and text == run_text and len(text.split()) <= 4:
            run_len += 1
            run_end = end
            continue
        flush_run()
        run_text, run_start, run_end, run_len = text, start, end, 1
    flush_run()

    # --- degenerate repetition ------------------------------------------ #
    # A collapse does not have to be slow, and it does not have to add words.
    # Chapter 18 substituted babble for real content, so coverage stayed at
    # ~1.00 and the stall check saw healthy pace. Counting how often a phrase
    # occurs anywhere is also wrong: the repeated unit is often long and recurs
    # only 4-6 times ("you had to wait for me to turn up on me" x4), which no
    # frequency threshold catches without also flagging ordinary prose.
    #
    # What actually identifies a loop is *consecutive* self-repetition. Prose
    # effectively never says the same multi-word phrase back to back three
    # times; a collapsed decoder does nothing else.
    #
    # Checked against the flat text as well as the segments, because whisper's
    # `text` and `segments` can disagree on this material.
    seg_tokens = normalize(" ".join(seg["text"] for seg in segments)).split()
    candidates = [("segments", seg_tokens)]
    if transcript_text is not None:
        flat_tokens = normalize(transcript_text).split()
        if flat_tokens != seg_tokens:
            candidates.append(("transcript", flat_tokens))

    worst: tuple[int, str, int, str] | None = None  # (span, phrase, reps, source)
    for source, tokens in candidates:
        index = 0
        while index < len(tokens):
            best_here: tuple[int, str, int] | None = None
            for width in range(2, REPEAT_MAX_PHRASE_WORDS + 1):
                if index + width * REPEAT_MIN_CONSECUTIVE > len(tokens):
                    break
                phrase = tokens[index : index + width]
                reps = 1
                probe = index + width
                while (
                    probe + width <= len(tokens)
                    and tokens[probe : probe + width] == phrase
                ):
                    reps += 1
                    probe += width
                if reps >= REPEAT_MIN_CONSECUTIVE:
                    span = reps * width
                    if best_here is None or span > best_here[0]:
                        best_here = (span, " ".join(phrase), reps)
            if best_here:
                if worst is None or best_here[0] > worst[0]:
                    worst = (*best_here, source)
                index += best_here[0]
            else:
                index += 1

    if worst and worst[0] >= REPEAT_MIN_TOKENS:
        span, phrase, reps, source = worst
        findings.append(
            Finding(
                kind="babble",
                start=0.0,
                end=audio_seconds,
                detail=f"{phrase!r} repeats {reps}x back to back "
                f"({span} tokens, via {source}) — degenerate repetition",
            )
        )

    stalled = sum(f.seconds for f in findings if f.kind == "stall")
    repeated = sum(f.seconds for f in findings if f.kind == "repeat")

    coverage = transcript_words / expected_words if expected_words else 0.0
    if coverage < coverage_fail:
        findings.append(
            Finding(
                kind="missing",
                start=0.0,
                end=audio_seconds,
                detail=f"said {transcript_words} of {expected_words} words "
                f"(coverage {coverage:.3f}) — content not delivered",
            )
        )
    elif coverage > coverage_high:
        findings.append(
            Finding(
                kind="surplus",
                start=0.0,
                end=audio_seconds,
                detail=f"said {transcript_words} of {expected_words} words "
                f"(coverage {coverage:.3f}) — model added content",
            )
        )

    passed = not findings
    findings.sort(key=lambda f: f.start)
    return LoopReport(
        wav=str(wav),
        audio_seconds=round(audio_seconds, 2),
        expected_words=expected_words,
        transcript_words=transcript_words,
        word_coverage=round(coverage, 4),
        words_per_second=round(transcript_words / audio_seconds if audio_seconds else 0.0, 2),
        median_segment_wps=round(median_wps, 2),
        stalled_seconds=round(stalled, 2),
        repeated_seconds=round(repeated, 2),
        empty_segments=empty,
        segments_past_eof=past_eof,
        passed=passed,
        findings=[asdict(f) for f in findings],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("wav", type=Path, nargs="+")
    parser.add_argument(
        "--manuscript-root",
        type=Path,
        required=True,
        help="Passed to validate_stt's chapter lookup for the expected text",
    )
    parser.add_argument("--whisper-model", default="mlx-community/whisper-large-v3-turbo")
    parser.add_argument("--language", default="en")
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument(
        "--settle-seconds",
        type=float,
        default=0.0,
        help="Skip WAVs modified more recently than this — set when sweeping "
        "while a batch render is still running",
    )
    parser.add_argument(
        "--quarantine",
        type=Path,
        default=None,
        help="Move failing WAVs here so a --skip-existing batch re-renders them",
    )
    args = parser.parse_args()

    import time

    from validate_stt import WAV_CHAPTER_RE, expected_text_for_chapter

    reports: list[LoopReport] = []
    failures: list[Path] = []
    now = time.time()
    for wav in args.wav:
        match = WAV_CHAPTER_RE.match(wav.name)
        if not match:
            raise SystemExit(f"unrecognized chapter WAV name: {wav.name}")
        if args.settle_seconds > 0:
            age = now - wav.stat().st_mtime
            if age < args.settle_seconds:
                print(
                    f"\n=== SKIP  {wav.name} — modified {age:.0f}s ago, "
                    f"still rendering"
                )
                continue
        chapter = int(match.group("num"))
        expected_raw, _ = expected_text_for_chapter(args.manuscript_root, chapter)
        report = analyse(
            wav,
            expected_raw,
            whisper_model=args.whisper_model,
            language=args.language,
        )
        reports.append(report)
        if not report.passed:
            failures.append(wav)

        verdict = "PASS" if report.passed else "FAIL"
        print(f"\n=== {verdict}  {wav.name}")
        print(
            f"  audio={report.audio_seconds:.1f}s  pace={report.words_per_second:.2f} wps "
            f"(median segment {report.median_segment_wps:.2f})"
        )
        print(
            f"  words said={report.transcript_words}/{report.expected_words} "
            f"coverage={report.word_coverage:.3f}"
        )
        print(
            f"  stalled={report.stalled_seconds:.1f}s  repeated={report.repeated_seconds:.1f}s "
            f"  empty={report.empty_segments}  past_eof_dropped={report.segments_past_eof}"
        )
        kinds = Counter(f["kind"] for f in report.findings)
        if kinds:
            print(f"  findings: {dict(kinds)}")
        for f in report.findings:
            print(f"    [{f['kind']:6s}] {f['start']:7.2f}-{f['end']:7.2f}s  {f['detail']}")

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(
            json.dumps([asdict(r) for r in reports], indent=2)
        )
        print(f"\nreport: {args.report}")

    print(
        f"\nswept {len(reports)} chapter(s): "
        f"{sum(1 for r in reports if r.passed)} pass, {len(failures)} fail"
    )
    if failures:
        print("failing:")
        for wav in failures:
            kinds = ", ".join(
                sorted(
                    {
                        f["kind"]
                        for r in reports
                        if r.wav == str(wav)
                        for f in r.findings
                    }
                )
            )
            print(f"  {wav.name}  ({kinds})")

    if args.quarantine and failures:
        args.quarantine.mkdir(parents=True, exist_ok=True)
        for wav in failures:
            wav.rename(args.quarantine / wav.name)
        print(
            f"\nmoved {len(failures)} failing WAV(s) to {args.quarantine} — "
            f"re-run the batch with --skip-existing to regenerate them"
        )

    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
