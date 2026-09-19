#!/usr/bin/env python3
"""Render a chapter with Qwen3-TTS (MLX), cloning a reference voice.

Local audition tooling only — does not touch the Nova production path.

Differs from `render_chapter_chatterbox.py` in the two ways that matter:

  * Chunks by PARAGRAPH, not sentence. Chatterbox needed ~90 generations per
    chapter, each a cold start joined with inserted silence; that stitching
    layer is where the clipped endings and seam artefacts live. Qwen3-TTS
    accepts 4096 tokens at 12 Hz (~5.7 min of audio), so a paragraph fits
    comfortably and a chapter needs a handful of joins instead of ninety.

  * Normalises numerals first. Raw `19:52` is what produced the garbled
    mid-sentence audio that sounded like a dropped line.

Reference cloning uses `ref_audio` + `ref_text`; the transcript conditions the
clone far better than audio alone, which Chatterbox could not use.

Example
-------
  PY=.venv/bin/python
  $PY render_chapter_qwen3.py \
      "../../../The Final Frontier Novel/chapters/discovery-part/discovery-part-012-one-call-end-to-end.md" \
      --output "../../../audiobook/qwen3-audition/016-chapter-012-qwen3-emns.wav" \
      --ref-audio "../../../audiobook/kokoro-audition/emns-refs/emns-neutral-l0-599.wav" \
      --ref-text "The band enjoyed much regional and some national success, and released three albums."
"""

from __future__ import annotations

import argparse
import re
import sys
import tempfile
import time
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))

from normalize_speech_text import normalize  # noqa: E402
from render_chapter_chatterbox import extract_body  # noqa: E402
from validate_stt import (  # noqa: E402
    is_benign_replace,
    normalized_tokens,
    token_wer,
)


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


def verify_chunk(
    audio: np.ndarray, expected: str, *, model: str, language: str
) -> dict:
    """ASR-check one generation unit for omissions, additions and paraphrases."""
    import mlx_whisper

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
        temp = Path(handle.name)
    try:
        sf.write(str(temp), audio, SAMPLE_RATE)
        result = mlx_whisper.transcribe(
            str(temp),
            path_or_hf_repo=model,
            language=language,
            word_timestamps=False,
            verbose=False,
            condition_on_previous_text=False,
        )
    finally:
        temp.unlink(missing_ok=True)

    return assess_transcript(expected, (result.get("text") or "").strip())


def chunk_wer(audio: np.ndarray, expected: str, *, model: str, language: str) -> float:
    """Backward-compatible scalar wrapper around :func:`verify_chunk`."""
    return float(verify_chunk(audio, expected, model=model, language=language)["wer"])

MODEL_ID = "mlx-community/Qwen3-TTS-12Hz-1.7B-Base-bf16"
SAMPLE_RATE = 24_000
PARAGRAPH_PAUSE_MS = 900
# Qwen3-TTS allows 4096 codec tokens at 12.5 Hz (~5.5 minutes). Keep a
# conservative margin: 3,200 English prose characters is typically 500-600
# words / 3-4 minutes. A normal chapter then needs 2-3 generations instead of
# 28-34, removing roughly 90% of opportunities for startup transients, timbre
# drift, stochastic stumbles, and seams.
MAX_CHUNK_CHARS = 3_200

# Each generate() call re-conditions on the reference independently, so loudness
# drifts between chunks. Concatenating raw produced a -6.4 dB step at a
# paragraph seam in chapter 12 (peak 0.616 -> 0.296), audible as the presence
# suddenly dropping out. Matching every chunk to one RMS target removes it.
TARGET_RMS_DBFS = -20.0
EDGE_FADE_MS = 10.0


def _raised_cosine(length: int, *, fade_out: bool) -> np.ndarray:
    if length <= 0:
        return np.ones(0, dtype=np.float32)
    ramp = np.linspace(0.0, np.pi, length, dtype=np.float32)
    curve = ((1.0 - np.cos(ramp)) * 0.5).astype(np.float32)
    return curve[::-1] if fade_out else curve


def declick(
    audio: np.ndarray,
    *,
    block_ms: float = 40.0,
    ratio: float = 600.0,
    min_jump: float = 0.30,
    abs_jump: float = 1.10,
    span: int = 5,
) -> tuple[np.ndarray, int]:
    """Repair impulsive discontinuities by interpolating across them.

    A click is a sample-to-sample jump far outside its *local* scale, not a
    large jump in absolute terms — ordinary loud speech at 24 kHz reaches 0.4
    between adjacent samples (file-wide p99 was 9.4x the local median). The
    click found at 349.478s in chapter 12 measured 0.2965 at **442x** local
    median, in otherwise quiet audio. Judging relative to a local baseline
    separates the two cleanly.

    Thresholds are deliberately conservative. Earlier settings still touched
    23 samples in chapter 1 and risked altering plosive consonants. At
    600x/0.30 or an absolute 1.10 jump, that falls to two unmistakable events
    while retaining the confirmed full-scale pop signature.

    Returns (audio, events_repaired).
    """
    if audio.size < 8:
        return audio, 0
    out = audio.astype(np.float32, copy=True)
    diff = np.abs(np.diff(out.astype(np.float64)))
    block = max(1, int(SAMPLE_RATE * block_ms / 1000))
    medians = np.array(
        [np.median(diff[i : i + block]) for i in range(0, diff.size, block)]
    )
    local = np.repeat(np.maximum(medians, 1e-6), block)[: diff.size]

    # Two rules, because one is blind where the other works.
    #
    # Relative catches clicks in quiet audio (the 349.478s click: 442x local).
    # It cannot see a click buried in loud speech, where the local median is
    # already high — the pop at 110.618s measured |jump| 1.1706 yet only 20x
    # local, and slipped straight through a ratio-only test.
    #
    # Absolute catches those. A bandlimited signal cannot step more than 2A
    # between samples, so a 1.17 jump is not speech. Chapter-wide p99.999 was
    # 0.5613, and jumps above 0.80 occurred exactly twice — the pop and its
    # immediate neighbour. Safe margin.
    flagged = np.flatnonzero(
        ((diff > local * ratio) & (diff > min_jump)) | (diff > abs_jump)
    )
    repaired = 0
    for index in flagged:
        lo = max(1, int(index) - span)
        hi = min(out.size - 1, int(index) + span + 1)
        if hi - lo < 2:
            continue
        # Linear bridge across the impulse from its clean neighbours.
        out[lo:hi] = np.linspace(out[lo - 1], out[hi], hi - lo, dtype=np.float32)
        repaired += 1
    return out, repaired


def match_level(audio: np.ndarray, target_dbfs: float = TARGET_RMS_DBFS) -> np.ndarray:
    """Scale a chunk to a common RMS so seams do not step in loudness."""
    if audio.size == 0:
        return audio
    rms = float(np.sqrt((audio.astype(np.float64) ** 2).mean()))
    if rms <= 1e-9:
        return audio
    out = (audio.astype(np.float32) * ((10.0 ** (target_dbfs / 20.0)) / rms)).astype(
        np.float32
    )
    peak = float(np.abs(out).max())
    if peak > 0.99:
        out *= 0.99 / peak
    return out


def suppress_onset_transient(
    audio: np.ndarray,
    *,
    silence_floor: float = 0.004,
    max_ramp_ms: float = 120.0,
    tail_fade_ms: float = 60.0,
) -> tuple[np.ndarray, float]:
    """Flatten the decoder's startup attack without cutting any speech.

    Qwen3-TTS opens each generation with an impulsive burst. Measured on chapter
    12 at the 107.58s join: a 0.296-peak attack reaching full amplitude within
    40ms of digital silence, ringing for ~80ms, against speech that sits at
    ~0.15. Straight after an inserted pause it reads as a loud "bwang" with a
    tail.

    Only the first ~40ms is pure artefact — it carries no voicing at all
    (f0_frames=0, spectral centroid 2794Hz, high zero-crossing rate). Speech
    begins *underneath* the ring, so trimming to the first sustained speech
    would clip the opening word. Instead we ramp gain across just the burst,
    which removes the attack and leaves the utterance intact.

    Returns (audio, ramp_seconds_applied).
    """
    if audio.size == 0:
        return audio, 0.0

    # Detection was tried and abandoned. Two attempts failed for the same
    # reason: any threshold needs a clean baseline, and the burst contaminates
    # whatever window the baseline is measured over. A search window ending at
    # 150ms with the reference starting at 150ms let every later burst hide
    # inside its own reference, catching 9 of 34 chunks while onset peaks still
    # reached 0.97.
    #
    # An unconditional ramp from the chunk's first audible sample cannot miss.
    # A ~120ms rise at a paragraph opening, after a 900ms pause, is inaudible as
    # a defect — it reads as a natural breath onset — and it guarantees no step
    # out of digital silence regardless of what the decoder emitted.
    onset = 0
    audible = np.flatnonzero(np.abs(audio) > silence_floor)
    if audible.size:
        onset = int(audible[0])

    out = audio[onset:].astype(np.float32, copy=True)
    if out.size == 0:
        return audio, 0.0
    ramp = min(int(SAMPLE_RATE * max_ramp_ms / 1000), max(1, out.size // 4))
    out[:ramp] *= _raised_cosine(ramp, fade_out=False)
    fade_out = min(int(SAMPLE_RATE * tail_fade_ms / 1000), max(1, out.size // 4))
    out[-fade_out:] *= _raised_cosine(fade_out, fade_out=True)
    return out, ramp / SAMPLE_RATE


def trim_tail_artifact(
    audio: np.ndarray,
    *,
    frame_ms: float = 20.0,
    quiet_run_ms: float = 120.0,
    floor_ratio: float = 0.06,
    search_ms: float = 900.0,
    max_trailing_ms: float = 320.0,
) -> tuple[np.ndarray, float]:
    """Cut trailing audio the model emits after the text is finished.

    Mirror image of the onset transient. In chapter 1 the chunk ending
    "...rather than decaying" finished at 358.49s, went quiet, then *restarted*
    at 358.67s and climbed to peak 0.209 — a word or breath that never
    completes, chopped off by the edge fade. Perceived as a garbled sound
    followed by a cut.

    A WER check cannot see this: every expected word is present and the defect
    is *surplus* audio, so the chunk scored 0.0000.

    Unlike the head, the tail is safe to cut decisively — there is no speech
    after the final word to protect. That asymmetry is why trimming the onset
    was dangerous and trimming here is not.

    Strategy: walk back from the end, find the last sustained quiet gap, and if
    real energy resumes after it, end the chunk at that gap.

    Returns (audio, seconds_removed).
    """
    if audio.size == 0:
        return audio, 0.0
    frame = max(1, int(SAMPLE_RATE * frame_ms / 1000))
    usable = (audio.size // frame) * frame
    if usable < frame * 6:
        return audio, 0.0
    rms = np.sqrt(
        (audio[:usable].astype(np.float64).reshape(-1, frame) ** 2).mean(axis=1) + 1e-12
    )
    speech = float(np.percentile(rms, 85))
    if speech <= 1e-6:
        return audio, 0.0
    threshold = speech * floor_ratio
    need = max(1, int(quiet_run_ms / frame_ms))
    horizon = max(0, len(rms) - int(search_ms / frame_ms))

    # Scan backwards for a quiet run that has audible content after it.
    index = len(rms) - 1
    run = 0
    while index >= horizon:
        if rms[index] < threshold:
            run += 1
            if run >= need:
                after = rms[index + run :]
                trailing_ms = after.size * frame_ms
                # Only a SHORT fragment after the gap is an artefact. A longer
                # one is a real final sentence following an internal pause —
                # cutting at the first qualifying gap removed up to 1400ms and
                # would have deleted whole closing lines.
                if (
                    after.size
                    and trailing_ms <= max_trailing_ms
                    and float(after.max()) > threshold * 3
                ):
                    cut = (index + run) * frame
                    if cut < audio.size:
                        return audio[:cut].copy(), (audio.size - cut) / SAMPLE_RATE
                run = 0  # keep looking further back
        else:
            run = 0
        index -= 1
    return audio, 0.0


def room_tone(
    reference: np.ndarray, samples: int, *, level_scale: float = 0.7
) -> np.ndarray:
    """Low-level tone for inter-chunk pauses, matched to the voice's own floor.

    Absolute digital silence between paragraphs is itself audible: the noise
    floor vanishing to true zero reads as a dropout, and it makes any imperfect
    edge land harder. Real narration keeps a floor. We synthesise one at the
    level the model's own quiet frames sit at, so seams stop announcing
    themselves.
    """
    if samples <= 0:
        return np.zeros(0, dtype=np.float32)
    frame = max(1, int(SAMPLE_RATE * 0.020))
    usable = (reference.size // frame) * frame
    if usable < frame * 4:
        return np.zeros(samples, dtype=np.float32)
    rms = np.sqrt(
        (reference[:usable].astype(np.float64).reshape(-1, frame) ** 2).mean(axis=1)
        + 1e-12
    )
    floor = float(np.percentile(rms, 10)) * level_scale
    if floor <= 1e-6:
        return np.zeros(samples, dtype=np.float32)
    rng = np.random.default_rng(0)
    noise = rng.standard_normal(samples).astype(np.float32)
    # Gently low-pass so it reads as room rather than hiss.
    kernel = np.ones(8, dtype=np.float32) / 8.0
    noise = np.convolve(noise, kernel, mode="same")
    current = float(np.sqrt((noise.astype(np.float64) ** 2).mean()))
    if current <= 1e-9:
        return np.zeros(samples, dtype=np.float32)
    return (noise * (floor / current)).astype(np.float32)


def soften_edges(audio: np.ndarray, fade_ms: float = EDGE_FADE_MS) -> np.ndarray:
    """Short fades so a level-matched chunk cannot click at its boundaries."""
    if audio.size == 0:
        return audio
    out = audio.astype(np.float32, copy=True)
    span = min(int(SAMPLE_RATE * fade_ms / 1000), max(1, out.size // 8))
    out[:span] *= _raised_cosine(span, fade_out=False)
    out[-span:] *= _raised_cosine(span, fade_out=True)
    return out


def chunk_paragraphs(text: str, max_chars: int = MAX_CHUNK_CHARS) -> list[str]:
    """Pack complete paragraphs into long, model-native narrative spans.

    Qwen3 can synthesize ~5.5 minutes per generation. Treating every paragraph
    as a separate call recreated Chatterbox's core defect: dozens of cold starts
    and seams per chapter. This packs adjacent paragraphs up to `max_chars`,
    retaining blank-line boundaries so the model controls its own paragraph
    timing and prosody.

    An individual oversized paragraph is split on sentence boundaries only as a
    last resort. A sentence longer than the limit is split on words so this
    function can never return an over-limit chunk.
    """
    raw_paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    paragraphs: list[str] = []

    for raw in raw_paragraphs:
        para = " ".join(raw.split())
        if len(para) <= max_chars:
            paragraphs.append(para)
            continue

        sentences = [
            part.strip()
            for part in re.split(
                r"(?<=[.!?…])\s+|(?<=[\"”’])\s+(?=[A-Z“\"])", para
            )
            if part.strip()
        ]
        buffer = ""
        for sentence in sentences:
            if len(sentence) > max_chars:
                if buffer:
                    paragraphs.append(buffer)
                    buffer = ""
                words = sentence.split()
                word_buffer = ""
                for word in words:
                    candidate = f"{word_buffer} {word}".strip()
                    if len(candidate) <= max_chars:
                        word_buffer = candidate
                    else:
                        if word_buffer:
                            paragraphs.append(word_buffer)
                        word_buffer = word
                if word_buffer:
                    paragraphs.append(word_buffer)
                continue
            candidate = f"{buffer} {sentence}".strip()
            if len(candidate) <= max_chars:
                buffer = candidate
            else:
                if buffer:
                    paragraphs.append(buffer)
                buffer = sentence
        if buffer:
            paragraphs.append(buffer)

    chunks: list[str] = []
    buffer = ""
    for para in paragraphs:
        candidate = f"{buffer}\n\n{para}".strip() if buffer else para
        if len(candidate) <= max_chars:
            buffer = candidate
        else:
            if buffer:
                chunks.append(buffer)
            buffer = para
    if buffer:
        chunks.append(buffer)

    # Keep short dialogue exchanges inside one generation. A boundary between
    # `"Yours or mine?"` and `"Both. You ran the pulse."` caused the first word
    # of the reply to arrive in a visibly different voice. Prefer moving the
    # final dialogue paragraph from the left chunk into the right; if that would
    # overflow, move the first right paragraph left instead. Never alter text.
    def is_dialogue(paragraph: str) -> bool:
        return paragraph.lstrip().startswith(('"', '“', "'", '‘'))

    for index in range(len(chunks) - 1):
        left = chunks[index].split("\n\n")
        right = chunks[index + 1].split("\n\n")
        if not left or not right or not (is_dialogue(left[-1]) and is_dialogue(right[0])):
            continue
        moved_left = "\n\n".join([left[-1], *right])
        if len(left) > 1 and len(moved_left) <= max_chars:
            chunks[index] = "\n\n".join(left[:-1])
            chunks[index + 1] = moved_left
            continue
        moved_right = "\n\n".join([*left, right[0]])
        if len(right) > 1 and len(moved_right) <= max_chars:
            chunks[index] = moved_right
            chunks[index + 1] = "\n\n".join(right[1:])

    assert all(chunk and len(chunk) <= max_chars for chunk in chunks)
    return chunks


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chapter", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ref-audio", type=Path, default=None)
    parser.add_argument("--ref-text", default=None)
    parser.add_argument("--model", default=MODEL_ID)
    parser.add_argument("--max-tokens", type=int, default=4096)
    parser.add_argument("--max-chunk-chars", type=int, default=MAX_CHUNK_CHARS)
    parser.add_argument("--pause-ms", type=int, default=PARAGRAPH_PAUSE_MS)
    parser.add_argument(
        "--no-normalize",
        dest="do_normalize",
        action="store_false",
        default=True,
        help="Feed raw manuscript text (to reproduce the numeral defect)",
    )
    parser.add_argument("--limit-chunks", type=int, default=None)
    parser.add_argument(
        "--match-levels",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Normalise each chunk to a common RMS so seams do not step in loudness",
    )
    parser.add_argument("--target-rms-dbfs", type=float, default=TARGET_RMS_DBFS)
    parser.add_argument(
        "--trim-artifacts",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Strip the decoder startup transient from each chunk (the 'bwang')",
    )
    parser.add_argument("--fade-ms", type=float, default=25.0)
    parser.add_argument("--declick", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--verify-chunks", action=argparse.BooleanOptionalAction, default=True,
        help="ASR-check every chunk against its text and re-roll on mismatch")
    parser.add_argument("--verify-model", default="mlx-community/whisper-small-mlx-q4")
    parser.add_argument("--chunk-wer-fail", type=float, default=0.25)
    parser.add_argument("--chunk-retries", type=int, default=2)
    args = parser.parse_args()

    body = extract_body(args.chapter)
    if args.do_normalize:
        body = normalize(body)
    chunks = chunk_paragraphs(body, args.max_chunk_chars)
    if args.limit_chunks:
        chunks = chunks[: args.limit_chunks]

    print(f"{len(chunks)} paragraph chunk(s), {sum(len(c) for c in chunks)} chars")
    print(f"normalize={args.do_normalize}  model={args.model}")

    from mlx_audio.tts.utils import load_model

    print("loading model…", flush=True)
    model = load_model(args.model)

    verifier = None
    if args.verify_chunks:
        import mlx_whisper  # noqa: F401

        verifier = args.verify_model
        print(f"per-chunk verification via {verifier}", flush=True)

    kwargs: dict = {"max_tokens": args.max_tokens}
    if args.ref_audio:
        kwargs["ref_audio"] = str(args.ref_audio)
        if not args.ref_text:
            raise SystemExit("--ref-audio requires --ref-text (the exact transcript)")
        kwargs["ref_text"] = args.ref_text

    pause = np.zeros(int(SAMPLE_RATE * args.pause_ms / 1000), dtype=np.float32)
    pieces: list[np.ndarray] = []
    levels: list[float] = []
    trimmed_total = 0.0
    suppressed = 0
    declicked = 0
    best_wer: dict[int, float] = {}
    rejected: list[tuple[int, float]] = []
    started = time.time()
    for index, chunk in enumerate(chunks, start=1):
        t0 = time.time()
        piece = None
        attempts = args.chunk_retries + 1 if verifier else 1
        for attempt in range(1, attempts + 1):
            audio_parts = []
            for result in model.generate(text=chunk, **kwargs):
                audio_parts.append(
                    np.asarray(result.audio, dtype=np.float32).reshape(-1)
                )
            if not audio_parts:
                print(f"  [{index}/{len(chunks)}] NO AUDIO for: {chunk[:60]!r}")
                break
            candidate = np.concatenate(audio_parts)
            if not verifier:
                piece = candidate
                break
            wer = chunk_wer(candidate, chunk, model=verifier, language="en")
            if wer <= args.chunk_wer_fail:
                piece = candidate
                if attempt > 1:
                    print(f"       recovered on attempt {attempt} (wer={wer:.3f})")
                break
            print(
                f"       attempt {attempt}/{attempts} wer={wer:.3f} > "
                f"{args.chunk_wer_fail:.2f} — model altered the text, re-rolling"
            )
            if piece is None or wer < best_wer.get(index, 1e9):
                best_wer[index] = wer
                piece = candidate
            if attempt == attempts:
                rejected.append((index, wer))
        if piece is None:
            continue
        raw_rms = float(np.sqrt((piece.astype(np.float64) ** 2).mean()))
        if args.trim_artifacts:
            piece, ramp = suppress_onset_transient(piece)
            if ramp > 0:
                trimmed_total += ramp
                suppressed += 1
                print(f"       suppressed onset transient over {ramp*1000:.0f}ms")
        if args.declick:
            piece, fixed = declick(piece)
            if fixed:
                declicked += fixed
                print(f'       repaired {fixed} click(s)')
        if args.match_levels:
            piece = match_level(piece, args.target_rms_dbfs)
        piece = soften_edges(piece, args.fade_ms)
        pieces.append(piece)
        if index < len(chunks):
            pieces.append(pause)
        levels.append(raw_rms)
        print(
            f"  [{index}/{len(chunks)}] {len(chunk):4d} chars -> "
            f"{piece.size / SAMPLE_RATE:6.2f}s in {time.time()-t0:5.1f}s "
            f"({(piece.size / SAMPLE_RATE) / max(time.time()-t0, 1e-6):4.2f}x realtime)",
            flush=True,
        )

    if not pieces:
        raise SystemExit("no audio generated")
    joined = np.concatenate(pieces)
    peak = float(np.abs(joined).max())
    if peak > 1.0:
        joined = joined / peak * 0.98
    args.output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(args.output), joined, SAMPLE_RATE)
    total = time.time() - started
    seconds = joined.size / SAMPLE_RATE
    print(
        f"\nwrote {args.output} — {seconds/60:.2f} min audio in {total/60:.2f} min "
        f"({seconds/max(total,1e-6):.2f}x realtime), {len(chunks)} chunk(s)"
    )
    if declicked:
        print(f"repaired {declicked} click(s)")
    if rejected:
        print(f"{len(rejected)} chunk(s) still mismatched after retries: "
              + ", ".join(f"#{i} wer={w:.2f}" for i, w in rejected))
    if levels:
        quiet, loud = min(levels), max(levels)
        spread = 20 * np.log10(loud / quiet) if quiet > 0 else float("inf")
        print(
            f"pre-normalisation chunk loudness spread: {spread:.1f} dB "
            f"(quietest {quiet:.4f}, loudest {loud:.4f} RMS)"
            + ("  — levelled" if args.match_levels else "  — NOT levelled")
        )


if __name__ == "__main__":
    main()
