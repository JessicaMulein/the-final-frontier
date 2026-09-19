#!/usr/bin/env python3
"""Render a manuscript chapter with local Chatterbox TTS (mlx-audio).

Local audition tooling only — does not touch the Nova production path.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model

# Re-exported: `extract_body` is defined once in `spoken_text` so the digest the
# queue and packaging tooling computes cannot drift from the text a renderer
# actually feeds the model. Existing `from render_chapter_chatterbox import
# extract_body` callers keep working.
from spoken_text import FRONT_MATTER, extract_body  # noqa: F401

SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])(?:[\"'”’])?\s+|(?<=[\"'”’])\s+(?=[A-Z“\"])")
MODEL_ID = "mlx-community/chatterbox-fp16"
SAMPLE_RATE = 24_000
MAX_CHARS = 500

# Rough narration pace used only to bound plausible per-sentence duration.
# The EMNS neutral seed measures ~2.45 wps; uk-southern-female-03 ~3.3 wps.
# The lower value is the safer bound since it widens the allowed window.
WORDS_PER_SECOND_ESTIMATE = 2.5

# Variable join silence for sentence-mode stitching (Gemini "audiobook method").
PAUSE_AFTER_SENTENCE_MS = 550
PAUSE_AFTER_QUESTION_MS = 700
PAUSE_AFTER_EXCLAIM_MS = 650
PAUSE_AFTER_ELLIPSIS_MS = 900
PAUSE_PARAGRAPH_MS = 1200
PAUSE_FALLBACK_MS = 400


@dataclass(frozen=True)
class SpeechUnit:
    text: str
    pause_after_ms: int


def _split_oversized(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars:
        return [text]
    words = text.split()
    parts: list[str] = []
    buf = ""
    for word in words:
        candidate = f"{buf} {word}".strip() if buf else word
        if len(candidate) <= max_chars:
            buf = candidate
        else:
            if buf:
                parts.append(buf)
            buf = word
    if buf:
        parts.append(buf)
    return parts


def chunk_paragraphs(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= max_chars:
            chunks.append(paragraph)
            continue
        sentences = re.split(r"(?<=[.!?\"'])\s+", paragraph)
        buf = ""
        for sentence in sentences:
            candidate = f"{buf} {sentence}".strip() if buf else sentence
            if len(candidate) <= max_chars:
                buf = candidate
                continue
            if buf:
                chunks.append(buf)
            chunks.extend(_split_oversized(sentence, max_chars))
            buf = ""
        if buf:
            chunks.append(buf)
    return chunks


def _sentence_pause_ms(sentence: str, *, paragraph_break: bool) -> int:
    if paragraph_break:
        return PAUSE_PARAGRAPH_MS
    stripped = sentence.rstrip("\"'”’")
    if stripped.endswith("..."):
        return PAUSE_AFTER_ELLIPSIS_MS
    if stripped.endswith("…"):
        return PAUSE_AFTER_ELLIPSIS_MS
    if stripped.endswith("?"):
        return PAUSE_AFTER_QUESTION_MS
    if stripped.endswith("!"):
        return PAUSE_AFTER_EXCLAIM_MS
    if stripped.endswith((".", '"', "'", "”", "’")):
        return PAUSE_AFTER_SENTENCE_MS
    return PAUSE_FALLBACK_MS


def chunk_sentences(text: str, max_chars: int = MAX_CHARS) -> list[SpeechUnit]:
    """One speech unit per sentence, with variable silence after each."""
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    units: list[SpeechUnit] = []
    for paragraph_index, paragraph in enumerate(paragraphs):
        last_paragraph = paragraph_index == len(paragraphs) - 1
        raw_sentences = [s.strip() for s in SENTENCE_SPLIT.split(paragraph) if s.strip()]
        if not raw_sentences:
            continue
        expanded: list[str] = []
        for sentence in raw_sentences:
            expanded.extend(_split_oversized(sentence, max_chars))
        for sentence_index, sentence in enumerate(expanded):
            last_in_paragraph = sentence_index == len(expanded) - 1
            paragraph_break = last_in_paragraph and not last_paragraph
            units.append(
                SpeechUnit(
                    text=sentence,
                    pause_after_ms=_sentence_pause_ms(
                        sentence, paragraph_break=paragraph_break
                    ),
                )
            )
    return units


def units_from_paragraph_chunks(chunks: list[str], pause_ms: int) -> list[SpeechUnit]:
    if not chunks:
        return []
    units = [SpeechUnit(text=chunk, pause_after_ms=pause_ms) for chunk in chunks]
    # No trailing silence after the final unit.
    return [
        *units[:-1],
        SpeechUnit(text=units[-1].text, pause_after_ms=0),
    ]


def _raised_cosine_fade(length: int, *, fade_out: bool) -> np.ndarray:
    if length <= 0:
        return np.zeros(0, dtype=np.float32)
    # Equal-power-ish cosine ramp; smoother than a linear drop into silence.
    t = np.linspace(0.0, np.pi, length, dtype=np.float32)
    weights = 0.5 * (1.0 + np.cos(t))
    return weights if fade_out else weights[::-1]


def trim_trailing_breath(
    audio: np.ndarray,
    *,
    speech_threshold: float = 0.035,
    floor_threshold: float = 0.006,
    max_trim_ms: float = 500.0,
    hold_ms: float = 25.0,
    fade_ms: float = 50.0,
    fade_in_ms: float = 8.0,
) -> np.ndarray:
    """Cut end-of-chunk breath/fwip, then cosine-fade to true zero.

    The old gate kept a short pad *after* the last loud sample, which often
    preserved the model’s trailing click. We now cut near the last real speech
    peak and fade that edge closed before the join silence.
    """
    if audio.size == 0:
        return audio
    trimmed = audio.astype(np.float32, copy=True)
    abs_audio = np.abs(trimmed)
    max_trim = int(SAMPLE_RATE * max_trim_ms / 1000)
    search_start = max(0, trimmed.size - max_trim)
    window = abs_audio[search_start:]
    speech = np.flatnonzero(window >= speech_threshold)
    if speech.size == 0:
        # Mostly noise/breath — keep a tiny head then fade everything down.
        cut = min(trimmed.size, search_start + int(SAMPLE_RATE * 0.04))
    else:
        last_speech = search_start + int(speech[-1]) + 1
        hold = int(SAMPLE_RATE * hold_ms / 1000)
        cut = min(trimmed.size, last_speech + hold)
        # If the hold still sits on a noisy floor, back up to true quiet.
        floor_run = int(SAMPLE_RATE * 0.01)
        while cut > last_speech:
            probe = abs_audio[max(0, cut - floor_run) : cut]
            if probe.size and float(np.max(probe)) <= floor_threshold:
                break
            cut -= 1
    trimmed = trimmed[:cut]
    fade_out = min(int(SAMPLE_RATE * fade_ms / 1000), max(1, trimmed.size // 3))
    if fade_out > 0:
        trimmed[-fade_out:] *= _raised_cosine_fade(fade_out, fade_out=True)
        trimmed[-min(8, trimmed.size) :] = 0.0
    fade_in = min(int(SAMPLE_RATE * fade_in_ms / 1000), max(1, trimmed.size // 8))
    if fade_in > 0:
        trimmed[:fade_in] *= _raised_cosine_fade(fade_in, fade_out=False)
    return trimmed


def soften_stitched_joins(
    audio: np.ndarray,
    *,
    silence_threshold: float = 0.008,
    min_silence_ms: float = 200.0,
    fade_ms: float = 45.0,
) -> np.ndarray:
    """Repair already-stitched chapter WAVs: cosine-close speech tails into joins."""
    if audio.size == 0:
        return audio
    out = audio.astype(np.float32, copy=True)
    abs_audio = np.abs(out)
    min_silence = int(SAMPLE_RATE * min_silence_ms / 1000)
    fade = int(SAMPLE_RATE * fade_ms / 1000)
    silent = abs_audio < silence_threshold
    index = 0
    while index < silent.size:
        if not silent[index]:
            index += 1
            continue
        end = index
        while end < silent.size and silent[end]:
            end += 1
        if end - index >= min_silence and index > 0:
            start = max(0, index - fade)
            length = index - start
            if length > 0:
                out[start:index] *= _raised_cosine_fade(length, fade_out=True)
                out[max(0, index - 4) : index] = 0.0
            # Soften the landing of the next chunk too.
            land = min(out.size, end + min(fade // 3, int(SAMPLE_RATE * 0.01)))
            land_len = land - end
            if land_len > 0 and end < out.size:
                out[end:land] *= _raised_cosine_fade(land_len, fade_out=False)
        index = end
    return out


def synthesize(model, text: str, ref_audio: str | None, *, exaggeration: float, cfg_weight: float) -> np.ndarray:
    kwargs: dict = {
        "text": text,
        "exaggeration": exaggeration,
        "cfg_weight": cfg_weight,
    }
    if ref_audio:
        kwargs["ref_audio"] = ref_audio
    pieces: list[np.ndarray] = []
    for result in model.generate(**kwargs):
        audio = np.asarray(result.audio, dtype=np.float32).reshape(-1)
        if audio.size:
            pieces.append(audio)
    if not pieces:
        raise RuntimeError(f"No audio generated for chunk: {text[:80]!r}")
    return np.concatenate(pieces)


def duration_bounds(text: str, *, wps: float = WORDS_PER_SECOND_ESTIMATE) -> tuple[float, float, float]:
    """Plausible spoken-duration window for one sentence.

    Generous on purpose: this is a runaway/truncation detector, not a pace
    judge. A legitimate slow read must sit comfortably inside the window.
    """
    words = max(1, len(text.split()))
    expected = words / wps
    low = max(0.25, expected * 0.35)
    high = max(2.5, expected * 2.2 + 1.5)
    return expected, low, high


def synthesize_guarded(
    model,
    text: str,
    ref_audio: str | None,
    *,
    exaggeration: float,
    cfg_weight: float,
    retries: int = 2,
    wps: float = WORDS_PER_SECOND_ESTIMATE,
) -> tuple[np.ndarray, int, bool]:
    """Synthesize one sentence, re-rolling if the duration is implausible.

    Chatterbox fails per *sentence*, not per chapter: it either collapses into
    degenerate repetition (audio far longer than the text warrants) or drops the
    line (far shorter). Chapter 3 hit both — one attempt looped
    "he said yes before" ~18 times, another dropped 110 words.

    Re-rolling the whole chapter to fix one sentence re-rolls the dice on all of
    them, which is why chapter 3 failed twice with different defects. Retrying
    just the offending sentence is both far cheaper and far more likely to
    converge.

    Returns (audio, attempts_used, within_bounds).
    """
    expected, low, high = duration_bounds(text, wps=wps)
    best: np.ndarray | None = None
    best_error = float("inf")
    for attempt in range(1, retries + 2):
        chunk = synthesize(
            model,
            text,
            ref_audio,
            exaggeration=exaggeration,
            cfg_weight=cfg_weight,
        )
        seconds = chunk.size / SAMPLE_RATE
        if seconds > high:
            error = seconds - high
        elif seconds < low:
            error = low - seconds
        else:
            error = 0.0
        if error < best_error:
            best, best_error = chunk, error
        if error == 0.0:
            return chunk, attempt, True
        print(
            f"    guard: {seconds:.1f}s outside [{low:.1f}, {high:.1f}]s "
            f"(expected ~{expected:.1f}s) — re-rolling sentence "
            f"(attempt {attempt}/{retries + 1})"
        )
    assert best is not None
    print(
        f"    guard: kept closest attempt at {best.size / SAMPLE_RATE:.1f}s "
        f"after {retries + 1} tries"
    )
    return best, retries + 1, False


def _wps(text: str, audio: np.ndarray) -> float:
    seconds = audio.size / SAMPLE_RATE
    if seconds <= 0:
        return 0.0
    return len(text.split()) / seconds


def assemble_units(
    model,
    units: list[SpeechUnit],
    *,
    ref_audio: str | None,
    exaggeration: float,
    cfg_weight: float,
    gate_breaths: bool,
    sentence_retries: int = 2,
    wps: float = WORDS_PER_SECOND_ESTIMATE,
    pace_retries: int = 2,
    pace_low: float = 0.55,
    pace_high: float = 1.85,
    pace_min_words: int = 4,
) -> np.ndarray:
    """Render every unit, then repair the ones that drag or rush.

    Two layers, because they catch different things:

    1. Absolute duration guard (`synthesize_guarded`) — catches catastrophic
       collapse while the sentence is being generated: a 74-token babble loop
       runs ~37 s where ~9 s is due, a dropped line runs ~1 s.

    2. Pace-relative second pass (here) — catches the *moderate* failures the
       absolute bound is too loose to see. Chapter 3 produced "the sample
       landed where the pulse said it should" at 0.76 wps against a chapter
       median of 2.70; that is plainly broken but still inside any absolute
       window wide enough not to reject a legitimately slow read. Comparing
       each sentence to the chapter's own median is what makes it visible.

    Only outliers are re-rolled, so the second pass costs a few sentences rather
    than a whole chapter.
    """
    rendered: list[np.ndarray] = []
    guarded = 0
    unresolved: list[int] = []
    for index, unit in enumerate(units, start=1):
        preview = unit.text.replace("\n", " ")
        print(
            f"[{index}/{len(units)}] {len(unit.text)} chars · "
            f"pause={unit.pause_after_ms}ms · {preview[:72]}…"
        )
        chunk, attempts, ok = synthesize_guarded(
            model,
            unit.text,
            ref_audio,
            exaggeration=exaggeration,
            cfg_weight=cfg_weight,
            retries=sentence_retries,
            wps=wps,
        )
        if attempts > 1:
            guarded += 1
        if not ok:
            unresolved.append(index)
        rendered.append(chunk)

    # --- pace-relative repair pass -------------------------------------- #
    paces = [
        _wps(unit.text, audio)
        for unit, audio in zip(units, rendered)
        if len(unit.text.split()) >= pace_min_words
    ]
    repaired = 0
    still_off: list[tuple[int, float, float]] = []
    if len(paces) >= 5:
        median = float(np.median([p for p in paces if p > 0]))
        low, high = median * pace_low, median * pace_high
        for position, (unit, audio) in enumerate(zip(units, rendered)):
            words = len(unit.text.split())
            if words < pace_min_words:
                continue
            pace = _wps(unit.text, audio)
            if low <= pace <= high:
                continue
            best_audio, best_pace = audio, pace
            for _ in range(pace_retries):
                print(
                    f"    pace: unit {position + 1} at {best_pace:.2f} wps vs median "
                    f"{median:.2f} (allowed {low:.2f}-{high:.2f}) — re-rolling"
                )
                candidate = synthesize(
                    model,
                    unit.text,
                    ref_audio,
                    exaggeration=exaggeration,
                    cfg_weight=cfg_weight,
                )
                candidate_pace = _wps(unit.text, candidate)
                previous_pace = best_pace
                if abs(candidate_pace - median) < abs(best_pace - median):
                    best_audio, best_pace = candidate, candidate_pace
                if low <= best_pace <= high:
                    break
                # Some lines are simply slow to say — a short emphatic line, or
                # one dense with pauses. If a re-roll lands at essentially the
                # same pace, the cause is the text rather than the sampling, and
                # further attempts only burn render time. Chapter 5 unit 14 went
                # 1.00 -> 1.15 -> 1.21 -> 1.30 -> 1.32 wps and never converged.
                if abs(candidate_pace - previous_pace) / max(previous_pace, 1e-6) < 0.12:
                    print(
                        f"    pace: unit {position + 1} looks inherently slow "
                        f"({candidate_pace:.2f} wps repeatable) — accepting"
                    )
                    break
            if best_audio is not rendered[position]:
                rendered[position] = best_audio
                repaired += 1
            if not (low <= best_pace <= high):
                still_off.append((position + 1, best_pace, median))
        print(
            f"  pace pass: median {median:.2f} wps, repaired {repaired} unit(s)"
            + (
                "; still outside: "
                + ", ".join(f"unit {i} @ {p:.2f} wps" for i, p, _ in still_off)
                if still_off
                else "; all units within pace band"
            )
        )

    if guarded:
        print(
            f"  duration guard re-rolled {guarded}/{len(units)} sentence(s)"
            + (
                f"; still out of bounds at unit(s) {unresolved}"
                if unresolved
                else "; all within bounds"
            )
        )

    audio_parts: list[np.ndarray] = []
    for index, (unit, audio) in enumerate(zip(units, rendered), start=1):
        chunk = trim_trailing_breath(audio) if gate_breaths else audio
        audio_parts.append(chunk)
        if unit.pause_after_ms > 0 and index < len(units):
            audio_parts.append(
                np.zeros(int(SAMPLE_RATE * unit.pause_after_ms / 1000), dtype=np.float32)
            )
    if not audio_parts:
        return np.zeros(0, dtype=np.float32)
    joined = np.concatenate(audio_parts)
    # Second pass closes any residual join clicks the per-chunk gate missed.
    joined = soften_stitched_joins(joined)
    peak = float(np.max(np.abs(joined))) if joined.size else 0.0
    if peak > 1.0:
        joined = joined / peak * 0.98
    return joined


def render(
    chapter_path: Path,
    output_path: Path,
    *,
    ref_audio: str | None,
    exaggeration: float,
    cfg_weight: float,
    pause_ms: int,
    chunk_mode: str,
    gate_breaths: bool,
) -> None:
    body = extract_body(chapter_path)
    if chunk_mode == "sentences":
        units = chunk_sentences(body)
        # Zero the final pause so the file doesn't end on silence.
        if units:
            units = [
                *units[:-1],
                SpeechUnit(text=units[-1].text, pause_after_ms=0),
            ]
    else:
        units = units_from_paragraph_chunks(chunk_paragraphs(body), pause_ms)

    print(f"Loading {MODEL_ID} …")
    model = load_model(MODEL_ID)
    joined = assemble_units(
        model,
        units,
        ref_audio=ref_audio,
        exaggeration=exaggeration,
        cfg_weight=cfg_weight,
        gate_breaths=gate_breaths,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), joined, SAMPLE_RATE)
    seconds = joined.shape[0] / SAMPLE_RATE
    print(f"Wrote {output_path} ({seconds/60:.1f} min, {len(units)} chunks, mode={chunk_mode})")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chapter", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--ref-audio",
        type=Path,
        default=None,
        help="Optional reference WAV (accent/timbre). Omit for model default.",
    )
    parser.add_argument("--exaggeration", type=float, default=0.7)
    parser.add_argument("--cfg-weight", type=float, default=0.3)
    parser.add_argument(
        "--chunk-mode",
        choices=("sentences", "paragraphs"),
        default="sentences",
        help="sentences: variable pause stitch; paragraphs: fixed pause joins",
    )
    parser.add_argument(
        "--pause-ms",
        type=int,
        default=350,
        help="Fixed join pause for --chunk-mode paragraphs only",
    )
    parser.add_argument(
        "--gate-breaths",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Trim/fade trailing breath artifacts on each generated chunk",
    )
    args = parser.parse_args()
    ref = str(args.ref_audio) if args.ref_audio else None
    render(
        args.chapter,
        args.output,
        ref_audio=ref,
        exaggeration=args.exaggeration,
        cfg_weight=args.cfg_weight,
        pause_ms=args.pause_ms,
        chunk_mode=args.chunk_mode,
        gate_breaths=args.gate_breaths,
    )


if __name__ == "__main__":
    main()
