#!/usr/bin/env python3
"""Locate probable glitches in rendered chapters and emit a timestamped listen list.

Local audition tooling only — does not touch the Nova production path.

Why this exists
---------------
Every other gate in this directory reads a whisper transcript, and that is the
wrong instrument for the defects that actually reach a listener:

  * Whisper is a language model. It reconstructs a half-dropped word from
    context and reports the correct text, so word-level "accuracy" measured
    against a transcript is biased toward passing.
  * `validate_stt.py` explicitly treats number and ordinal differences as benign
    noise — which is exactly the class that fails audibly. `19:52` came out as
    "19-5-2" and no gate objected.

This module never asks whether the right words appear. It asks two questions
that a transcript cannot answer:

  1. TEXT RISK — which sentences contain tokens the model reliably stumbles on
     (clock times, bare numerals, symbols). Derived from the manuscript, so it
     is exact and costs nothing.
  2. SEAM DAMAGE — at each join, was the chunk cut while still sounding? A
     clipped final consonant, a click, or a truncated tail is audible and
     invisible to ASR.

Chunk boundaries are recoverable because `assemble_units` joins chunks with
runs of *exact* zeros. Matching those runs against the same `chunk_sentences`
split the renderer used gives per-sentence timestamps.

Output is a listen list, not a verdict. A green run here does not mean the
audio is good; it means these two specific failure modes were not found.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))

from render_chapter_chatterbox import SAMPLE_RATE, chunk_sentences, extract_body  # noqa: E402

WAV_CHAPTER_RE = re.compile(
    r"^(?P<seq>\d{3})-chapter-(?P<num>\d{3})-(?P<voice>.+)\.wav$", re.IGNORECASE
)

# Tokens Chatterbox mis-verbalises. Clock times are the worst: it reads the
# colon as a break and emits digits separately ("nineteen five two").
RISK = {
    "clock-time": re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b"),
    "decimal": re.compile(r"\b\d+\.\d+\b"),
    "equation": re.compile(r"\b[a-zA-Z]\s*=\s*\d+"),
    "long-number": re.compile(r"(?<![\d:.])\d{3,}(?![\d:.])"),
    "short-number": re.compile(r"(?<![\d:.])\d{1,2}(?![\d:.])"),
}

# A join that still has this much energy in its final moments was cut mid-sound.
CUT_RMS = 0.015
CUT_WINDOW_MS = 12.0
MIN_PAUSE_MS = 90.0

# Click detection has to be *relative*. Speech at 24 kHz routinely has
# sample-to-sample deltas above 0.15 on plosives, so an absolute threshold
# reports every consonant in the book — a first attempt flagged 263,000 "clicks"
# across two chapters. A click is a delta far outside the local scale AND
# isolated, so the surrounding samples look nothing like it.
CLICK_SCALE = 14.0
CLICK_WINDOW_MS = 20.0
CLICK_MIN_ABS = 0.05

# A dropout is a brief near-silent hole with speech on both sides, short enough
# that it cannot be an intended pause.
DROPOUT_MIN_MS = 12.0
DROPOUT_MAX_MS = 120.0
DROPOUT_RATIO = 0.08

MAX_HITS_PER_KIND = 40


@dataclass
class Hit:
    chapter: int
    kind: str
    detail: str
    unit: int | None = None
    start_seconds: float | None = None
    exact: bool = True

    @property
    def stamp(self) -> str:
        if self.start_seconds is None:
            return "--:--"
        m, s = divmod(int(self.start_seconds), 60)
        return f"{m:d}:{s:02d}"


@dataclass
class ChapterReport:
    chapter: int
    wav: str
    seconds: float
    units_expected: int
    boundaries_found: int
    aligned: bool
    hits: list[dict] = field(default_factory=list)


def load_mono(path: Path) -> np.ndarray:
    audio, sr = sf.read(str(path), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    if sr != SAMPLE_RATE:
        raise SystemExit(f"{path.name}: expected {SAMPLE_RATE} Hz, got {sr}")
    return audio


def zero_runs(audio: np.ndarray, *, min_ms: float = MIN_PAUSE_MS) -> list[tuple[int, int]]:
    """Start index and length of every run of exact zeros — the inserted pauses."""
    quiet = audio == 0.0
    if not quiet.any():
        return []
    edges = np.flatnonzero(np.diff(quiet.astype(np.int8)))
    bounds = np.concatenate(([0] if quiet[0] else [], edges + 1, [quiet.size]))
    runs: list[tuple[int, int]] = []
    minimum = int(SAMPLE_RATE * min_ms / 1000)
    for start, end in zip(bounds[:-1], bounds[1:]):
        start, end = int(start), int(end)
        if end > start and quiet[start] and (end - start) >= minimum:
            runs.append((start, end - start))
    return runs


def unit_starts(audio: np.ndarray, expected_units: int) -> tuple[list[float], bool]:
    """Start time of each rendered chunk, and whether alignment looks trustworthy."""
    runs = zero_runs(audio)
    starts = [0.0] + [(start + length) / SAMPLE_RATE for start, length in runs]
    aligned = len(starts) == expected_units
    if not aligned and expected_units > 0:
        # Fall back to proportional placement so timestamps stay useful.
        total = audio.size / SAMPLE_RATE
        starts = [total * i / expected_units for i in range(expected_units)]
    return starts, aligned


def text_risks(units, starts: list[float], chapter: int, aligned: bool) -> list[Hit]:
    hits: list[Hit] = []
    for index, unit in enumerate(units):
        for kind, rx in RISK.items():
            found = rx.findall(unit.text)
            if not found:
                continue
            # Report the strongest risk per sentence only.
            hits.append(
                Hit(
                    chapter=chapter,
                    kind=f"text:{kind}",
                    detail=f"{found[:4]} in: {unit.text[:88]}",
                    unit=index + 1,
                    start_seconds=starts[index] if index < len(starts) else None,
                    exact=aligned,
                )
            )
            break
    return hits


def unit_spans(audio: np.ndarray, expected_units: int) -> list[tuple[float, float]] | None:
    """(start, end) seconds for each rendered chunk, or None if unrecoverable.

    Chunks are the audio between the inserted exact-zero pauses.
    """
    runs = zero_runs(audio)
    if len(runs) + 1 != expected_units:
        return None
    spans: list[tuple[float, float]] = []
    cursor = 0
    for start, length in runs:
        spans.append((cursor / SAMPLE_RATE, start / SAMPLE_RATE))
        cursor = start + length
    spans.append((cursor / SAMPLE_RATE, audio.size / SAMPLE_RATE))
    return spans


def dropped_sentences(
    audio: np.ndarray,
    units,
    chapter: int,
    *,
    short_ratio: float = 2.2,
    silent_ratio: float = 0.12,
    min_words: int = 4,
) -> list[Hit]:
    """Sentences whose chunk is too short, or too quiet, to contain their words.

    This is the one check that can see a *dropped sentence*, which is what a
    listener notices most and what every transcript-based gate misses: whisper
    reconstructs the missing line's neighbours and reports fluent text.

    A chunk is judged against the chapter's own median words/sec, so a slow
    narrator is not mistaken for a broken one.
    """
    spans = unit_spans(audio, len(units))
    if spans is None:
        return [
            Hit(
                chapter=chapter,
                kind="audio:unalignable",
                detail=f"{len(zero_runs(audio)) + 1} chunks recovered vs "
                f"{len(units)} sentences — cannot check for dropped sentences",
                exact=False,
            )
        ]

    paces: list[float] = []
    for unit, (start, end) in zip(units, spans):
        words = len(unit.text.split())
        seconds = end - start
        if words >= min_words and seconds > 0.05:
            paces.append(words / seconds)
    if len(paces) < 5:
        return []
    median = float(np.median(paces))

    hits: list[Hit] = []
    for index, (unit, (start, end)) in enumerate(zip(units, spans), start=1):
        words = len(unit.text.split())
        seconds = end - start
        if words < min_words or seconds <= 0:
            continue
        chunk = audio[int(start * SAMPLE_RATE) : int(end * SAMPLE_RATE)]
        voiced = speech_fraction(chunk)
        pace = words / seconds
        if pace > median * short_ratio:
            hits.append(
                Hit(
                    chapter=chapter,
                    kind="audio:sentence-truncated",
                    detail=f"{words} words in {seconds:.2f}s ({pace:.1f} wps vs median "
                    f"{median:.1f}) — audio too short for the line: {unit.text[:72]}",
                    unit=index,
                    start_seconds=start,
                )
            )
        elif voiced < silent_ratio:
            hits.append(
                Hit(
                    chapter=chapter,
                    kind="audio:sentence-silent",
                    detail=f"only {voiced*100:.0f}% of {seconds:.2f}s is voiced — "
                    f"line may be missing: {unit.text[:72]}",
                    unit=index,
                    start_seconds=start,
                )
            )
    return hits


def speech_fraction(chunk: np.ndarray, *, floor_db: float = -40.0) -> float:
    if chunk.size == 0:
        return 0.0
    frame = max(1, int(SAMPLE_RATE * 0.010))
    trimmed = chunk[: (chunk.size // frame) * frame]
    if trimmed.size == 0:
        return 0.0
    rms = np.sqrt((trimmed.reshape(-1, frame).astype(np.float64) ** 2).mean(axis=1) + 1e-12)
    peak = float(rms.max())
    if peak <= 0:
        return 0.0
    return float((rms >= peak * 10 ** (floor_db / 20.0)).mean())


def seam_damage(audio: np.ndarray, chapter: int, aligned: bool) -> list[Hit]:
    hits: list[Hit] = []
    window = int(SAMPLE_RATE * CUT_WINDOW_MS / 1000)
    for start, _ in zero_runs(audio):
        pre = audio[max(0, start - window) : start]
        if pre.size == 0:
            continue
        level = float(np.sqrt((pre.astype(np.float64) ** 2).mean()))
        if level > CUT_RMS:
            hits.append(
                Hit(
                    chapter=chapter,
                    kind="audio:cut-while-voiced",
                    detail=f"{level:.3f} RMS in final {CUT_WINDOW_MS:.0f}ms before pause "
                    f"(clipped word ending)",
                    start_seconds=start / SAMPLE_RATE,
                    exact=True,
                )
            )
    hits = hits[:MAX_HITS_PER_KIND]
    hits += find_clicks(audio, chapter)
    hits += find_dropouts(audio, chapter)
    return hits


def _block_reduce(values: np.ndarray, block: int, fn) -> np.ndarray:
    trimmed = values[: (values.size // block) * block]
    if trimmed.size == 0:
        return np.zeros(0)
    return fn(trimmed.reshape(-1, block), axis=1)


def find_clicks(audio: np.ndarray, chapter: int) -> list[Hit]:
    """Sample deltas that are large *relative to their neighbourhood* and isolated."""
    if audio.size < 3:
        return []
    delta = np.abs(np.diff(audio))
    block = max(1, int(SAMPLE_RATE * CLICK_WINDOW_MS / 1000))
    local = _block_reduce(delta, block, np.median)
    if local.size == 0:
        return []
    scale = np.repeat(local, block)
    if scale.size < delta.size:
        scale = np.concatenate([scale, np.full(delta.size - scale.size, local[-1])])
    scale = np.maximum(scale[: delta.size], 1e-6)

    candidate = (delta > scale * CLICK_SCALE) & (delta > CLICK_MIN_ABS)
    hits: list[Hit] = []
    for idx in np.flatnonzero(candidate):
        lo = max(0, idx - 3)
        hi = min(delta.size, idx + 4)
        neighbourhood = np.concatenate([delta[lo:idx], delta[idx + 1 : hi]])
        if neighbourhood.size and delta[idx] > neighbourhood.max() * 3.0:
            hits.append(
                Hit(
                    chapter=chapter,
                    kind="audio:click",
                    detail=f"isolated discontinuity {float(delta[idx]):.3f} "
                    f"vs local median {float(scale[idx]):.4f}",
                    start_seconds=int(idx) / SAMPLE_RATE,
                    exact=True,
                )
            )
    return hits[:MAX_HITS_PER_KIND]


def find_dropouts(audio: np.ndarray, chapter: int) -> list[Hit]:
    """Brief near-silent holes bracketed by speech — too short to be a pause."""
    frame = max(1, int(SAMPLE_RATE * 0.005))
    rms = np.sqrt(
        _block_reduce(audio.astype(np.float64) ** 2, frame, np.mean) + 1e-12
    )
    if rms.size < 8:
        return []
    speech_level = float(np.percentile(rms, 75))
    if speech_level <= 0:
        return []
    quiet = rms < speech_level * DROPOUT_RATIO
    min_frames = max(1, int(DROPOUT_MIN_MS / 5))
    max_frames = max(min_frames, int(DROPOUT_MAX_MS / 5))

    hits: list[Hit] = []
    index = 0
    while index < quiet.size:
        if not quiet[index]:
            index += 1
            continue
        start = index
        while index < quiet.size and quiet[index]:
            index += 1
        length = index - start
        if not (min_frames <= length <= max_frames):
            continue
        if start == 0 or index >= quiet.size:
            continue
        before = rms[max(0, start - 6) : start]
        after = rms[index : index + 6]
        if before.size == 0 or after.size == 0:
            continue
        # Speech on both sides, and the hole is far quieter than either.
        if before.mean() > speech_level * 0.4 and after.mean() > speech_level * 0.4:
            hits.append(
                Hit(
                    chapter=chapter,
                    kind="audio:dropout",
                    detail=f"{length * 5}ms hole at {rms[start:index].mean():.4f} RMS "
                    f"between speech at {before.mean():.3f}/{after.mean():.3f}",
                    start_seconds=start * frame / SAMPLE_RATE,
                    exact=True,
                )
            )
    return hits[:MAX_HITS_PER_KIND]


def analyse_chapter(
    wav: Path, chapter_file: Path, chapter: int, *, do_text: bool, do_audio: bool
) -> ChapterReport:
    audio = load_mono(wav)
    units = chunk_sentences(extract_body(chapter_file))
    starts, aligned = unit_starts(audio, len(units))
    hits: list[Hit] = []
    if do_text:
        hits += text_risks(units, starts, chapter, aligned)
    if do_audio:
        hits += dropped_sentences(audio, units, chapter)
        hits += seam_damage(audio, chapter, aligned)
    hits.sort(key=lambda h: (h.start_seconds if h.start_seconds is not None else 0.0))
    return ChapterReport(
        chapter=chapter,
        wav=wav.name,
        seconds=round(audio.size / SAMPLE_RATE, 2),
        units_expected=len(units),
        boundaries_found=len(zero_runs(audio)) + 1,
        aligned=aligned,
        hits=[{**asdict(h), "stamp": h.stamp} for h in hits],
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio-dir", type=Path, required=True)
    parser.add_argument("--manuscript-root", type=Path, required=True)
    parser.add_argument("--voice-tag", required=True)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--chapter", type=int, action="append", default=None)
    parser.add_argument("--no-text", dest="do_text", action="store_false", default=True)
    parser.add_argument("--no-audio", dest="do_audio", action="store_false", default=True)
    parser.add_argument(
        "--max-listed",
        type=int,
        default=6,
        help="Hits printed per chapter (the report keeps all)",
    )
    parser.add_argument(
        "--extract-clips",
        type=Path,
        default=None,
        help="Write a short excerpt around each hit here, for a listening check",
    )
    parser.add_argument("--clip-seconds", type=float, default=3.0)
    parser.add_argument("--clips-per-chapter", type=int, default=8)
    args = parser.parse_args()

    chapter_files: dict[int, Path] = {}
    for path in sorted(args.manuscript_root.rglob("*.md")):
        match = re.match(r"^(?:[a-z]+-)*?(\d{3})-", path.stem)
        if match:
            chapter_files[int(match.group(1))] = path

    wanted = set(args.chapter) if args.chapter else None
    reports: list[ChapterReport] = []
    for wav in sorted(args.audio_dir.glob(f"*-chapter-*-{args.voice_tag}.wav")):
        match = WAV_CHAPTER_RE.match(wav.name)
        if not match:
            continue
        chapter = int(match.group("num"))
        if wanted and chapter not in wanted:
            continue
        if chapter not in chapter_files:
            print(f"ch{chapter:03d}: no manuscript file, skipped", file=sys.stderr)
            continue
        reports.append(
            analyse_chapter(
                wav,
                chapter_files[chapter],
                chapter,
                do_text=args.do_text,
                do_audio=args.do_audio,
            )
        )

    total = sum(len(r.hits) for r in reports)
    by_kind: dict[str, int] = {}
    for r in reports:
        for h in r.hits:
            by_kind[h["kind"]] = by_kind.get(h["kind"], 0) + 1
    misaligned = [r.chapter for r in reports if not r.aligned]

    print(f"scanned {len(reports)} chapter(s), {total} hit(s)")
    for kind, count in sorted(by_kind.items(), key=lambda kv: -kv[1]):
        print(f"  {kind:26s} {count}")
    if misaligned:
        print(
            f"\ntimestamps approximate for {len(misaligned)} chapter(s) where chunk "
            f"boundaries did not match the sentence split: {misaligned[:12]}"
        )

    flagged = [r for r in reports if r.hits]
    print(f"\n{len(flagged)} chapter(s) with at least one hit\n")
    for r in sorted(flagged, key=lambda r: -len(r.hits)):
        print(f"=== ch{r.chapter:03d}  {r.seconds/60:5.1f} min  {len(r.hits)} hit(s)"
              f"{'' if r.aligned else '  [approx timestamps]'}")
        for h in r.hits[: args.max_listed]:
            print(f"    {h['stamp']:>7s}  {h['kind']:26s} {h['detail'][:96]}")
        if len(r.hits) > args.max_listed:
            print(f"    … {len(r.hits) - args.max_listed} more")

    if args.extract_clips:
        out = args.extract_clips
        out.mkdir(parents=True, exist_ok=True)
        written = 0
        for r in reports:
            audio = load_mono(args.audio_dir / r.wav)
            picked = [h for h in r.hits if h["start_seconds"] is not None][
                : args.clips_per_chapter
            ]
            for h in picked:
                centre = float(h["start_seconds"])
                half = args.clip_seconds / 2
                lo = max(0, int((centre - half) * SAMPLE_RATE))
                hi = min(audio.size, int((centre + half) * SAMPLE_RATE))
                if hi <= lo:
                    continue
                stamp = h["stamp"].replace(":", "m")
                kind = h["kind"].replace(":", "-")
                name = f"ch{r.chapter:03d}-{stamp}-{kind}.wav"
                sf.write(str(out / name), audio[lo:hi], SAMPLE_RATE)
                written += 1
        print(f"\nwrote {written} clip(s) to {out} ({args.clip_seconds:g}s each)")

    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps([asdict(r) for r in reports], indent=2))
        print(f"\nreport: {args.report}")


if __name__ == "__main__":
    main()
