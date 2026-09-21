#!/usr/bin/env python3
"""Render a whole chapter with Fish S2 Pro, then gate it.

This is the stamina test, and the seed of the production pipeline. A good thirty
second take proves nothing about the failure mode that actually cost this project a
session: QVoice was fine in 30-second pieces and drifted, stuttered, and truncated
words over eight minutes.

Structurally simpler than the QVoice path on purpose. Fish's `generate` splits long
text internally at `chunk_length` and appends each rendered segment back into a
running `Conversation` before the next, so prosody context carries forward natively.
The QVoice pipeline approximated that by prepending the previous paragraph and then
trimming it back off by ASR timestamp, and two of this session's bugs lived in that
machinery: a warm-up residue that read as a stutter, and a boundary misalignment
that deleted "Two point one" and "Ravi" while chapter WER stayed at 0.023.

So there is no warm-up, no trim, and no seam alignment here. If Fish holds together,
an entire class of defect simply does not exist.

What is kept from the QVoice path is the assembly and the QA, because those were
sound: level matching across segments, slope removal inside a segment, and a
whole-chapter ASR check. Plus the pace profile, which is the one measurement that
tracked the listener's drift reports.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

import mlx.core as mx
import numpy as np
import soundfile as sf

import pace
from audio_io import load_reference
from manuscript import chapter_title, spoken_text
from repair_gaps import HF_SUSPECT, QUIET_DB, frame_stats, harvest_floor, spectral_fill

REPO = Path(__file__).resolve().parents[3]
# The narrator's identity is committed, not regenerated. `out/` is ignored, so reading
# the reference from there made the book's voice depend on an untracked file that a
# clean checkout would not have and a cache clear could not rebuild. See
# assets/voice-refs/hifitts/PROVENANCE.md, which also carries its sha256.
HIFI = REPO / "audiobook-studio/assets/voice-refs/hifitts"

INTERIOR = (
    "Read as a first-person memoir: dry, precise, quietly unsettled. Let meaning "
    "land through timing and emphasis rather than volume. Never announce."
)

MANIFEST_SCHEMA = 2
GAP_ALGORITHM = "spectral-v6"
GAP_FFT_SIZE = 2048
GAP_CUTOFF_HZ = 3500.0
REFERENCE_WAV_SHA256 = "2718268846e7b02b15b130c499711ae4730f8041307f49d39e1e08678a8ec762"
REFERENCE_TEXT_SHA256 = "9fb56fcb1bd465b15398174da692c8b18fc468bcac9764a09b21580f6245d4aa"

# A deterministic lead-in turn, generated and then discarded, used to pin the voice
# state before a chapter begins. Measured across 21 rendered chapters, each chapter's
# register is stable within itself but sits at its own level: p20 F0 chapter means
# span 172.4-188.1 Hz, and chapters 10 -> 11 -> 12 step +0.84 then -1.17 semitones.
# That is the fault the listener described as the voice going deeper, then higher,
# then back. Register is set at generation start, so the lever is generation start.
#
# 79 words / >300 bytes, deliberately larger than the default chunk_length. In
# group_turns_into_batches an oversized first turn becomes the current batch and the
# next turn flushes it before appending, so the anchor is guaranteed to arrive as one
# whole yielded segment. That matters: it is discarded as a complete segment, so
# unlike the QVoice warm-up there is no ASR boundary search, no cut inside a
# waveform, and no way to delete a chapter's first word.
ANCHOR = (
    "Before the chapter begins, I settle into the same chair and place the notebook "
    "squarely on the desk. I take one ordinary breath and read this line in the "
    "voice I use for facts that matter: calm, exact, unhurried, and close enough to "
    "hear the thought behind the words. I do not announce, perform, or hurry. I let "
    "each sentence finish, leave the silence where it belongs, and begin the next "
    "one only when it is ready."
)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def production_identity(
    chapter: Path,
    *,
    announcement: Path | None,
    reference_name: str,
    seed: int | None,
    anchored: bool,
    model: str = "mlx-community/fish-audio-s2-pro",
    instruct: str = INTERIOR,
    chunk_length: int = 300,
    max_tokens: int = 1024,
    temperature: float = 0.7,
    top_p: float = 0.7,
    top_k: int = 30,
    sentence_pause: str = "short",
    sentence_turns: bool = False,
    segment_gap_ms: float = 650.0,
    announcement_gap_ms: float = 900.0,
    spoken_replacements: tuple[str, ...] = (),
    max_words_per_call: int = 0,
) -> dict:
    """Every input and fixed setting that determines a production chapter.

    `book_fish.already_done` recomputes this object before skipping. This is the
    difference between resumable and stale: a passing manifest beside a large WAV is
    not evidence that the WAV speaks the current prose with the current narrator.
    """
    ref_wav = HIFI / f"{reference_name}.wav"
    ref_txt = HIFI / f"{reference_name}.txt"
    if not ref_wav.is_file() or not ref_txt.is_file():
        raise RuntimeError(f"reference not found: {ref_wav}")
    ref_wav_sha = _sha256_file(ref_wav)
    ref_txt_sha = _sha256_file(ref_txt)
    if reference_name == "hifitts-clean-92":
        if ref_wav_sha != REFERENCE_WAV_SHA256 or ref_txt_sha != REFERENCE_TEXT_SHA256:
            raise RuntimeError(
                "committed narrator reference does not match PROVENANCE.md; refusing "
                "to render a different voice under the same name"
            )

    spoken = spoken_text(chapter)
    generated_spoken = spoken
    for replacement in spoken_replacements:
        if "=" not in replacement:
            raise RuntimeError(f"spoken replacement expects OLD=NEW: {replacement!r}")
        old, new = replacement.split("=", 1)
        count = generated_spoken.count(old)
        if not old or count != 1:
            raise RuntimeError(
                f"spoken replacement OLD must occur exactly once; {old!r} occurs {count} times"
            )
        generated_spoken = generated_spoken.replace(old, new, 1)
    title = chapter_title(chapter)
    payload = {
        "schema": "frontier-fish-production/v2",
        "chapter_source_sha256": _sha256_file(chapter),
        "spoken_sha256": _sha256_text(spoken),
        "generation_spoken_sha256": _sha256_text(generated_spoken),
        "canonical_title": title,
        "announcement_sha256": (
            _sha256_file(announcement) if announcement is not None else None
        ),
        "announcement_name": announcement.name if announcement is not None else None,
        "reference_name": reference_name,
        "reference_wav_sha256": ref_wav_sha,
        "reference_text_sha256": ref_txt_sha,
        "model": model,
        "instruct": instruct,
        "seed": seed,
        "anchored": anchored,
        "anchor_text": ANCHOR if anchored else None,
        "chunk_length": chunk_length,
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "top_k": top_k,
        "sentence_pause": sentence_pause,
        "sentence_turns": sentence_turns,
        "segment_gap_ms": segment_gap_ms,
        "announcement_gap_ms": announcement_gap_ms,
        "spoken_replacements": list(spoken_replacements),
        "max_words_per_call": max_words_per_call,
        "gap_algorithm": GAP_ALGORITHM,
        "gap_fft_size": GAP_FFT_SIZE,
        "gap_cutoff_hz": GAP_CUTOFF_HZ,
    }
    payload["identity_sha256"] = _sha256_text(
        json.dumps(payload, sort_keys=True, separators=(",", ":"))
    )
    return payload


def active_rms(audio: np.ndarray, rate: int) -> float:
    frame = max(1, int(rate * 0.020))
    usable = (audio.size // frame) * frame
    if usable == 0:
        return 0.0
    frames = audio[:usable].reshape(-1, frame).astype(np.float64)
    rms = np.sqrt((frames**2).mean(axis=1) + 1e-12)
    peak = float(rms.max())
    if peak <= 0:
        return 0.0
    voiced = rms[rms >= peak * 10 ** (-36 / 20)]
    return float(np.sqrt(np.mean(voiced**2))) if voiced.size else 0.0


def flatten_slope(audio: np.ndarray, rate: int, max_db: float = 6.0) -> tuple[np.ndarray, float]:
    """Remove a within-segment level slope, bounded and mean-preserving.

    Ported from the QVoice path, where segments faded 3-6.5 dB start to end and the
    listener heard it as the narrator trailing off. Per-segment gain matching cannot
    see a slope inside a segment.
    """
    window = max(1, int(rate * 0.200))
    count = audio.size // window
    if count < 4:
        return audio, 0.0
    frames = audio[: count * window].reshape(count, window).astype(np.float64)
    rms = np.sqrt((frames**2).mean(axis=1) + 1e-12)
    peak = float(rms.max())
    if peak <= 0:
        return audio, 0.0
    voiced = rms >= peak * 10 ** (-36 / 20)
    if int(voiced.sum()) < 4:
        return audio, 0.0
    centres = (np.arange(count) + 0.5) * window / rate
    slope = float(np.polyfit(centres[voiced], 20 * np.log10(rms[voiced]), 1)[0])
    span = float(centres[voiced][-1] - centres[voiced][0])
    total = slope * span
    if span <= 0 or abs(total) < 0.5:
        return audio, 0.0
    total = float(np.clip(total, -max_db, max_db))
    midpoint = float(np.mean(centres[voiced]))
    times = np.arange(audio.size, dtype=np.float64) / rate
    gain_db = np.clip(-(total / span) * (times - midpoint), -max_db, max_db)
    out = (audio.astype(np.float64) * 10 ** (gain_db / 20)).astype(np.float32)
    loudest = float(np.abs(out).max())
    if loudest > 0.99:
        out *= 0.99 / loudest
    return out, round(-total, 3)


def comfort_gap(
    segments: list[np.ndarray], samples: int, rate: int, seed: int
) -> np.ndarray:
    """V6 stationary room tone shaped only from confirmed natural dark pauses.

    The original gap synthesizer used mean magnitude over percentile-selected quiet
    frames. Sparse high-frequency events dominated after normalization, manufacturing
    audible hiss: 29–39% of gap energy above 4 kHz against effectively zero in Fish's
    natural pauses. This is the chapter-5 "background opens up" defect.

    V6, chosen by ear over donor-waveform repair, low-pass filtering, and FFT sizes
    4096/8192, uses the same implementation as `repair_gaps.py`: confirmed dark pause
    donors, median power spectrum, random complex coefficients, IFFT and Hann
    overlap-add, FFT 2048, and a soft 3.5 kHz cutoff. At render time `segments` contain
    only model output -- no previously synthesized gaps -- so the donor population
    cannot be contaminated by the defect it is replacing.
    """
    if samples <= 0:
        return np.zeros(0, dtype=np.float32)
    if not segments:
        return np.zeros(samples, dtype=np.float32)

    source = np.concatenate(segments)
    level, hf, size = frame_stats(source, rate)
    speech = float(np.percentile(level, 90)) if level.size else 0.0
    donor = harvest_floor(source, level, hf, size, speech)
    if donor.size < GAP_FFT_SIZE:
        raise RuntimeError(
            f"not enough natural dark pause audio for {GAP_ALGORITHM}: "
            f"{donor.size} samples"
        )

    quiet = level < speech * 10 ** (QUIET_DB / 20)
    natural_runs = [
        float(np.median(level[a:b]))
        for a, b in _runs(quiet & (hf < HF_SUSPECT * 0.5))
        if b - a >= 4
    ]
    if not natural_runs:
        raise RuntimeError(f"no natural floor level available for {GAP_ALGORITHM}")
    target = float(np.median(natural_runs))

    gap = spectral_fill(
        samples,
        donor,
        rate,
        target,
        np.random.default_rng(seed),
        GAP_CUTOFF_HZ,
        GAP_FFT_SIZE,
    )
    fade = min(int(rate * 0.040), samples // 4)
    if fade > 0:
        gap[:fade] *= np.linspace(0, 1, fade, dtype=np.float32)
        gap[-fade:] *= np.linspace(1, 0, fade, dtype=np.float32)
    return gap.astype(np.float32)


def _runs(mask: np.ndarray) -> list[tuple[int, int]]:
    """Contiguous true ranges, kept local so gap generation has no CLI coupling."""
    runs: list[tuple[int, int]] = []
    start: int | None = None
    for index, flag in enumerate(mask):
        if flag and start is None:
            start = index
        elif not flag and start is not None:
            runs.append((start, index))
            start = None
    if start is not None:
        runs.append((start, len(mask)))
    return runs


def match_levels(segments: list[np.ndarray], rate: int, limit_db: float = 2.0):
    levels = [active_rms(s, rate) for s in segments]
    usable = [x for x in levels if x > 0]
    if not usable:
        return segments, [0.0] * len(segments), 0.0
    target = float(np.median(usable))
    out, gains = [], []
    for segment, level in zip(segments, levels):
        if level <= 0:
            out.append(segment)
            gains.append(0.0)
            continue
        gain_db = float(
            np.clip(20 * np.log10(target / level), -limit_db, limit_db)
        )
        adjusted = segment.astype(np.float32) * (10 ** (gain_db / 20))
        peak = float(np.abs(adjusted).max())
        if peak > 0.99:
            adjusted *= 0.99 / peak
        out.append(adjusted)
        gains.append(round(gain_db, 3))
    return out, gains, target


def verify(audio: np.ndarray, rate: int, expected: str, model: str) -> dict:
    """Whole-chapter ASR check, reusing the existing scoring.

    Also returns the transcriber's timestamped segments under `asr_segments`.

    Those timings were being computed and thrown away on every chapter. They are the
    raw material for synchronised read-along, and recomputing them later would mean
    re-transcribing roughly fourteen hours of audio for data this pass already has.
    They are recorded as *evidence*, not as authority: the renderer knows where each
    paragraph sits to the sample, so assembly arithmetic remains the source of truth
    for structure and these bound any later sentence-level alignment inside a
    paragraph window.

    They describe the waveform handed to this function, which is the delivered file
    including the announcement and every inter-paragraph gap.
    """
    import tempfile

    import mlx_whisper

    from scoring import assess_transcript

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
        temp = Path(handle.name)
    try:
        sf.write(str(temp), audio, rate)
        result = mlx_whisper.transcribe(
            str(temp),
            path_or_hf_repo=model,
            language="en",
            verbose=False,
            condition_on_previous_text=False,
        )
    finally:
        temp.unlink(missing_ok=True)
    assessment = assess_transcript(expected, (result.get("text") or "").strip())
    assessment["asr_segments"] = [
        {
            "start": round(float(segment.get("start", 0.0)), 3),
            "end": round(float(segment.get("end", 0.0)), 3),
            "text": str(segment.get("text", "")).strip(),
        }
        for segment in (result.get("segments") or [])
    ]
    return assessment


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("chapter", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--model", default="mlx-community/fish-audio-s2-pro")
    p.add_argument("--reference", default="hifitts-clean-92", help="stem under out/hifitts-refs")
    p.add_argument("--instruct", default=INTERIOR)
    p.add_argument(
        "--paragraph-gap-ms",
        type=float,
        default=650.0,
        help="room tone inserted between paragraphs; 0 concatenates directly, which "
        "the listener heard as rambling",
    )
    # Chosen by ear over four alternatives: no gap (the original bug), gap only,
    # this, 900 ms with a full [pause], and sentence-level turns. The listener's
    # complaint was that sentences ran together and the reading rambled despite
    # being perfectly clear; a gap at assembly cannot reach inside a paragraph, so
    # the inline tag is doing work the gap cannot.
    p.add_argument(
        "--sentence-pause",
        choices=("none", "short", "full"),
        default="short",
        help="insert Fish inline pause tags between sentences within a paragraph",
    )
    p.add_argument(
        "--sentence-turns",
        action="store_true",
        help="tag each sentence as its own turn rather than each paragraph, giving "
        "assembly-level control of inter-sentence gaps at the cost of more generations",
    )
    p.add_argument("--chunk-length", type=int, default=300)
    p.add_argument("--max-tokens", type=int, default=1024)
    p.add_argument("--temperature", type=float, default=0.7)
    p.add_argument("--top-p", type=float, default=0.7)
    p.add_argument("--top-k", type=int, default=30)
    p.add_argument("--verify-model", default="mlx-community/whisper-large-v3-turbo")
    p.add_argument("--no-verify", action="store_true")
    # Both default to off, so the production path is unchanged unless asked.
    p.add_argument(
        "--seed",
        type=int,
        default=None,
        help="reset MLX's RNG before generating; Fish's generate() exposes no seed "
        "parameter, so this is the only handle on reproducibility",
    )
    p.add_argument(
        "--anchor",
        action="store_true",
        help="generate one identical discarded lead-in turn first, so every chapter "
        "starts from the same voice state; its codes stay in Fish's running "
        "Conversation but its waveform never ships",
    )
    p.add_argument(
        "--keep-anchor-audio",
        action="store_true",
        help="also write the discarded anchor waveform, for checking that it is "
        "byte-identical across chapters",
    )
    p.add_argument(
        "--announcement",
        type=Path,
        default=None,
        help="spoken chapter announcement to place at the head of this chapter's "
        "audio. For a listener who cannot see a player's chapter list, this is the "
        "navigation: it states where they are without them touching the device. It "
        "goes inside the chapter rather than becoming its own track, so a player's "
        "chapter list stays one meaningful entry per chapter instead of 256 "
        "alternating ones, which is slower to move through with a screen reader.",
    )
    p.add_argument(
        "--announcement-gap-ms",
        type=float,
        default=900.0,
        help="silence between the announcement and the first paragraph",
    )
    p.add_argument(
        "--spoken-replace",
        action="append",
        default=[],
        metavar="OLD=NEW",
        help="replace one exact string in generation input without changing the "
        "manuscript or expected ASR text. For non-spoken markup that Fish treats as "
        "an instruction; repeatable and recorded in production identity",
    )
    p.add_argument(
        "--max-words-per-call",
        type=int,
        default=0,
        help="split an unusually long chapter into separate deterministic generate() "
        "calls at paragraph boundaries, each re-anchored with the same seed; 0 keeps "
        "the approved one-call behavior",
    )
    args = p.parse_args()

    ref_wav = HIFI / f"{args.reference}.wav"
    ref_txt = HIFI / f"{args.reference}.txt"
    if not ref_wav.is_file() or not ref_txt.is_file():
        raise SystemExit(f"reference not found: {ref_wav}")
    if args.announcement is not None and not args.announcement.is_file():
        raise SystemExit(f"announcement not found: {args.announcement}")

    try:
        identity = production_identity(
            args.chapter,
            announcement=args.announcement,
            reference_name=args.reference,
            seed=args.seed,
            anchored=args.anchor,
            model=args.model,
            instruct=args.instruct,
            chunk_length=args.chunk_length,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            top_k=args.top_k,
            sentence_pause=args.sentence_pause,
            sentence_turns=args.sentence_turns,
            segment_gap_ms=args.paragraph_gap_ms,
            announcement_gap_ms=args.announcement_gap_ms,
            spoken_replacements=tuple(args.spoken_replace),
            max_words_per_call=args.max_words_per_call,
        )
    except RuntimeError as exc:
        raise SystemExit(str(exc)) from exc

    spoken = spoken_text(args.chapter)
    words = len(spoken.split())
    print(f"{args.chapter.name}: {words} spoken words")
    print(f"reference: {args.reference}")

    from mlx_audio.tts.utils import load_model

    print(f"loading {args.model}")
    model = load_model(args.model)
    rate = int(getattr(model, "sample_rate", 44100))
    reference = load_reference(ref_wav, rate)
    ref_text = ref_txt.read_text().strip()

    # Fish only chunks long text when it can find speaker turns:
    #
    #   turns = split_text_by_speaker(text)
    #   return group_turns_into_batches(...) if turns else [text]
    #
    # `split_text_by_speaker` matches <|speaker:N|> and nothing else, so plain
    # narration falls through as a single batch, `chunk_length` is ignored, and
    # `max_tokens` truncates the result. The first attempt at this chapter produced
    # 47.55 s for 1186 words -- 13% of the text, WER 0.87, coverage 0.13.
    #
    # Tagging each paragraph as one speaker turn engages the existing batching and,
    # more importantly, keeps the running Conversation across batches, which is the
    # continuity the QVoice path had to fake with warm-up and trimming.
    generation_spoken = spoken
    for replacement in args.spoken_replace:
        if "=" not in replacement:
            raise SystemExit(f"--spoken-replace expects OLD=NEW, got {replacement!r}")
        old, new = replacement.split("=", 1)
        count = generation_spoken.count(old)
        if not old or count != 1:
            raise SystemExit(
                f"--spoken-replace OLD must occur exactly once; {old!r} occurs {count} times"
            )
        generation_spoken = generation_spoken.replace(old, new, 1)
        print(f"  generation-only replacement: {old!r} -> {new!r}")
    paragraphs = [p.strip() for p in generation_spoken.split("\n\n") if p.strip()]

    if args.sentence_pause != "none":
        tag = "[short pause]" if args.sentence_pause == "short" else "[pause]"
        paragraphs = [_pause_between_sentences(p, tag) for p in paragraphs]

    units = (
        [s for p in paragraphs for s in _sentences(p)]
        if args.sentence_turns
        else paragraphs
    )
    if args.max_words_per_call > 0 and args.sentence_turns:
        raise SystemExit("--max-words-per-call is supported only with paragraph turns")
    unit_parts: list[list[str]] = [[]]
    part_words = 0
    for unit in units:
        unit_words = len(re.sub(r"\[[^]]+\]", "", unit).split())
        if (
            args.max_words_per_call > 0
            and unit_parts[-1]
            and part_words + unit_words > args.max_words_per_call
        ):
            unit_parts.append([])
            part_words = 0
        unit_parts[-1].append(unit)
        part_words += unit_words
    tagged_parts = [
        "\n".join(f"<|speaker:0|>{unit}" for unit in part) for part in unit_parts
    ]
    print(
        f"  {len(paragraphs)} paragraphs -> {len(units)} turns -> "
        f"{len(tagged_parts)} generate call(s)"
        f"{' (sentence-level)' if args.sentence_turns else ''}, "
        f"pause tags: {args.sentence_pause}, gap {args.paragraph_gap_ms:.0f}ms"
    )

    if args.anchor:
        if len(ANCHOR.encode("utf-8")) <= args.chunk_length:
            raise SystemExit(
                f"anchor is {len(ANCHOR.encode())} bytes but chunk_length is "
                f"{args.chunk_length}: it would be batched together with the "
                f"chapter's first paragraph and could not be discarded cleanly"
            )
        print(f"  anchor: {len(ANCHOR.split())} words, discarded from every call")
    if args.seed is not None:
        print(f"  seed: {args.seed}, reset before every generate call")

    print(f"\nrendering (chunk_length={args.chunk_length})", flush=True)
    started = time.perf_counter()
    segments: list[np.ndarray] = []
    records = []
    anchor_audios: list[np.ndarray] = []
    for part_index, tagged in enumerate(tagged_parts):
        if args.seed is not None:
            mx.random.seed(args.seed)
        payload = f"<|speaker:0|>{ANCHOR}\n{tagged}" if args.anchor else tagged
        first_yield = True
        speech_before = len(segments)
        for segment in model.generate(
            text=payload,
            ref_audio=reference,
            ref_text=ref_text,
            instruct=args.instruct,
            chunk_length=args.chunk_length,
            max_tokens=args.max_tokens,
            temperature=args.temperature,
            top_p=args.top_p,
            top_k=args.top_k,
            verbose=False,
        ):
            audio = np.asarray(segment.audio, dtype=np.float32)
            if args.anchor and first_yield:
                anchor_audios.append(audio)
                print(
                    f"  part {part_index + 1} anchor: {audio.size / rate:6.2f}s "
                    f"discarded ({time.perf_counter() - started:6.1f}s wall)",
                    flush=True,
                )
                first_yield = False
                continue
            first_yield = False
            global_index = len(segments)
            segments.append(audio)
            records.append(
                {
                    "index": global_index,
                    "generation_part": part_index,
                    "part_segment_index": int(
                        getattr(segment, "segment_idx", global_index)
                    ),
                    "seconds": round(audio.size / rate, 3),
                    "tokens": int(getattr(segment, "token_count", 0)),
                }
            )
            print(
                f"  segment {len(segments):2d} [part {part_index + 1}]: "
                f"{audio.size / rate:6.2f}s "
                f"(total {sum(s.size for s in segments) / rate / 60:5.2f} min, "
                f"{time.perf_counter() - started:6.1f}s wall)",
                flush=True,
            )
        if len(segments) == speech_before:
            raise RuntimeError(f"generate call {part_index + 1} yielded no speech")
    render_seconds = time.perf_counter() - started

    if not segments:
        raise SystemExit("no audio generated")
    anchor_sha256 = None
    anchor_audio: np.ndarray | None = None
    if args.anchor:
        if len(anchor_audios) != len(tagged_parts):
            raise SystemExit(
                f"expected {len(tagged_parts)} anchor segments, got {len(anchor_audios)}"
            )
        anchor_hashes = [hashlib.sha256(audio.tobytes()).hexdigest() for audio in anchor_audios]
        if len(set(anchor_hashes)) != 1:
            raise SystemExit("deterministic anchor changed between generation parts")
        anchor_audio = anchor_audios[0]
        anchor_sha256 = anchor_hashes[0]
        print(
            f"  anchor sha256 {anchor_sha256[:16]} ({anchor_audio.size / rate:.2f}s, "
            f"identical across {len(anchor_audios)} call(s))"
        )
        if args.keep_anchor_audio:
            anchor_path = args.output.with_name(args.output.stem + ".anchor.wav")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            sf.write(str(anchor_path), anchor_audio, rate, subtype="PCM_16")
            print(f"  wrote {anchor_path}")

    # Slope removal per segment, then level matching across segments.
    corrections = []
    for index, segment in enumerate(segments):
        segments[index], applied = flatten_slope(segment, rate)
        corrections.append(applied)
    levelled, gains, target = match_levels(segments, rate)

    gap_samples = int(rate * args.paragraph_gap_ms / 1000)

    # Build the delivered waveform and its exact sample-domain map together. The map
    # is the read-along source of truth; seconds are derived presentation values.
    pieces: list[np.ndarray] = []
    assembly_map: list[dict] = []
    assembly_cursor = 0

    def append_piece(kind: str, audio: np.ndarray, **metadata) -> None:
        nonlocal assembly_cursor
        start = assembly_cursor
        end = start + int(audio.size)
        pieces.append(audio)
        assembly_map.append(
            {
                "kind": kind,
                "start_sample": start,
                "end_sample": end,
                "start_seconds": round(start / rate, 6),
                "end_seconds": round(end / rate, 6),
                **metadata,
            }
        )
        assembly_cursor = end

    announcement_samples = 0
    if args.announcement is not None:
        intro, intro_rate = sf.read(str(args.announcement), always_2d=False)
        intro = np.asarray(intro, dtype=np.float32)
        if intro.ndim > 1:
            intro = intro.mean(axis=1)
        if int(intro_rate) != rate:
            raise SystemExit(
                f"announcement is {intro_rate} Hz but the chapter is {rate} Hz; "
                "resampling the narrator's own voice is not acceptable here"
            )
        intro_level = active_rms(intro, rate)
        if intro_level > 0 and target > 0:
            intro = intro * (target / intro_level)
            intro_peak = float(np.abs(intro).max())
            if intro_peak > 0.99:
                intro = intro * (0.99 / intro_peak)
        append_piece("announcement", intro.astype(np.float32))
        intro_gap = int(rate * args.announcement_gap_ms / 1000)
        if intro_gap > 0:
            append_piece(
                "announcement_gap",
                comfort_gap(levelled, intro_gap, rate, seed=999),
                algorithm=GAP_ALGORITHM,
            )
        announcement_samples = assembly_cursor
        print(
            f"  announcement {intro.size / rate:.2f}s + "
            f"{args.announcement_gap_ms:.0f}ms gap; prose starts at "
            f"{announcement_samples / rate:.2f}s"
        )

    for index, segment in enumerate(levelled):
        append_piece("speech_segment", segment, segment_index=index)
        if index < len(levelled) - 1 and gap_samples > 0:
            append_piece(
                "segment_gap",
                comfort_gap(levelled, gap_samples, rate, seed=1000 + index),
                after_segment=index,
                algorithm=GAP_ALGORITHM,
            )
    joined = np.concatenate(pieces)
    if assembly_cursor != joined.size:
        raise SystemExit(
            f"assembly map ends at sample {assembly_cursor} but waveform has "
            f"{joined.size} samples"
        )
    peak = float(np.abs(joined).max())
    if peak > 0.99:
        joined *= 0.99 / peak

    args.output.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(args.output), joined, rate, subtype="PCM_16")
    minutes = joined.size / rate / 60
    print(
        f"\nwrote {args.output} ({minutes:.2f} min) in {render_seconds:.0f}s "
        f"(RTF {render_seconds / (joined.size / rate):.2f}), peak "
        f"{mx.get_peak_memory() / 1e9:.1f} GB"
    )

    # Pace profile per segment: the one measurement that tracked the listener's
    # drift reports on the QVoice renders.
    print("\n  seg  secs  artic/voiced_s  pause%  longest_gap")
    # Segment offsets must describe the delivered waveform, which interleaves a
    # `comfort_gap` between every pair of segments. Advancing this cursor by segment
    # duration alone silently under-reported every offset by the accumulated gap
    # time -- 650 ms per preceding gap, about 21 s by the end of a 33-paragraph
    # chapter -- so the recorded spans did not point at the audio they named.
    #
    # These offsets are exact yielded-speech-segment boundaries for read-along
    # alignment. Fish may group multiple paragraph turns into one yielded segment, so
    # they are not claimed as paragraph boundaries. They come from assembly arithmetic
    # rather than recognition and bound later sentence alignment inside a known window.
    gap_seconds = gap_samples / rate
    speech_spans = {
        entry["segment_index"]: entry
        for entry in assembly_map
        if entry["kind"] == "speech_segment"
    }
    for index, segment in enumerate(levelled):
        measured = pace.measure(segment if rate == 24000 else _to24k(segment, rate))
        span = speech_spans[index]
        records[index].update(
            {
                "gain_db": gains[index],
                "slope_correction_db": corrections[index],
                "start_sample": span["start_sample"],
                "end_sample": span["end_sample"],
                "start_seconds": span["start_seconds"],
                "end_seconds": span["end_seconds"],
                "pace": measured,
            }
        )
        if measured:
            print(
                f"  {index:3d} {measured['seconds']:5.1f}   "
                f"{measured['articulation']:12.3f}  "
                f"{measured['pause_fraction'] * 100:5.1f}   "
                f"{measured['longest_gap']:6.2f}"
            )

    live = [r["pace"] for r in records if r.get("pace")]
    manifest = {
        "schema_version": MANIFEST_SCHEMA,
        "production_identity": identity,
        "chapter": str(args.chapter),
        "canonical_title": identity["canonical_title"],
        "output": str(args.output.resolve()),
        "output_sha256": _sha256_file(args.output),
        "engine": "fish_s2_pro",
        "model": args.model,
        "reference": {"name": args.reference, "text": ref_text},
        "instruct": args.instruct,
        "generation": {
            "chunk_length": args.chunk_length,
            "max_tokens": args.max_tokens,
            "temperature": args.temperature,
            "top_p": args.top_p,
            "top_k": args.top_k,
            "max_words_per_call": args.max_words_per_call,
            "generation_calls": len(tagged_parts),
            "spoken_replacements": list(args.spoken_replace),
            "seed": args.seed,
            "anchored": bool(args.anchor),
            "anchor_text": ANCHOR if args.anchor else None,
            "anchor_sha256": anchor_sha256,
            "anchor_seconds": (
                round(anchor_audio.size / rate, 3) if anchor_audio is not None else None
            ),
        },
        "segments": records,
        "assembly": {
            "seconds": round(joined.size / rate, 3),
            "sample_rate": rate,
            "sample_count": int(joined.size),
            "level_target_active_rms": round(target, 6),
            "render_seconds": round(render_seconds, 1),
            "paragraph_gap_seconds": round(gap_seconds, 6),
            "gap_algorithm": GAP_ALGORITHM,
            "gap_fft_size": GAP_FFT_SIZE,
            "gap_cutoff_hz": GAP_CUTOFF_HZ,
            "segment_offsets_include_gaps": True,
            "announcement_path": (
                str(args.announcement) if args.announcement is not None else None
            ),
            # Where the manuscript actually begins. Read-along alignment must start
            # here: everything before it is navigation, not prose, and syncing it
            # against chapter text would put the highlight a sentence ahead.
            "prose_start_sample": int(announcement_samples),
            "prose_starts_at_seconds": round(announcement_samples / rate, 6),
            "assembly_map": assembly_map,
        },
    }
    if live:
        articulation = [m["articulation"] for m in live]
        manifest["assembly"]["articulation_first_third"] = round(
            float(np.mean(articulation[: max(1, len(articulation) // 3)])), 3
        )
        manifest["assembly"]["articulation_last_third"] = round(
            float(np.mean(articulation[-max(1, len(articulation) // 3) :])), 3
        )
        print(
            f"\n  articulation first third "
            f"{manifest['assembly']['articulation_first_third']:.3f} -> last third "
            f"{manifest['assembly']['articulation_last_third']:.3f}"
        )

    if not args.no_verify:
        print("\nverifying whole chapter against the manuscript", flush=True)
        # Verify the prose region only. The announcement speaks words that are not in
        # the manuscript, so transcribing it would charge the chapter WER for a
        # signpost and report an added span that is working as intended. Segment
        # timings are shifted back afterwards so they stay relative to the delivered
        # file rather than to the slice that was transcribed.
        prose_offset_samples = int(announcement_samples)
        quality = verify(joined[prose_offset_samples:], rate, spoken, args.verify_model)
        announcement_seconds = announcement_samples / rate
        if announcement_samples > 0:
            for segment in quality.get("asr_segments", []):
                segment["start"] = round(segment["start"] + announcement_seconds, 3)
                segment["end"] = round(segment["end"] + announcement_seconds, 3)
        manifest["assembly"]["chapter_quality"] = {
            k: v for k, v in quality.items() if k != "transcript"
        }
        print(
            f"  WER {quality['wer']:.4f}  coverage {quality['coverage']:.4f}  "
            f"gap {quality['max_expected_gap']}  added {quality['max_added_span']}  "
            f"pass {quality['passed']}"
        )
        for span in quality.get("suspicious_spans", [])[:8]:
            print(f"    expected {span['expected']} heard {span['heard']}")

    # Fail loudly if the recorded spans stop describing the delivered file. Read-along
    # alignment trusts these offsets, and a silent drift is exactly the defect above.
    expected_samples = int(joined.size)
    final_end_sample = records[-1]["end_sample"] if records else 0
    if final_end_sample != expected_samples:
        raise SystemExit(
            f"segment offsets do not describe the written audio: last segment ends at "
            f"sample {final_end_sample} but the file has {expected_samples} samples"
        )

    manifest_path = args.output.with_suffix(".manifest.json")
    staged_manifest = manifest_path.with_suffix(manifest_path.suffix + ".tmp")
    staged_manifest.write_text(json.dumps(manifest, indent=2))
    staged_manifest.replace(manifest_path)
    print(f"wrote {manifest_path}")


def _sentences(text: str) -> list[str]:
    """Same split the chunker uses elsewhere in this project."""
    import re

    parts = re.split(r"(?<=[.!?…])\s+|(?<=[\"”’])\s+(?=[A-Z“\"])", text)
    return [s.strip() for s in parts if s.strip()]


def _pause_between_sentences(paragraph: str, tag: str) -> str:
    """Insert an inline pause tag between sentences, never before the first.

    Tags live only in the spoken transform; the manuscript is untouched. Fish
    documents `[pause]` and `[short pause]` among its inline controls. Applied to
    every sentence boundary rather than sampled, because the listener's complaint
    was that sentences run together, not that some do.
    """
    sentences = _sentences(paragraph)
    if len(sentences) < 2:
        return paragraph
    return sentences[0] + " " + " ".join(f"{tag} {s}" for s in sentences[1:])


def _to24k(audio: np.ndarray, rate: int) -> np.ndarray:
    from fractions import Fraction

    from scipy.signal import resample_poly

    ratio = Fraction(24000, int(rate)).limit_denominator(1000)
    return resample_poly(audio, ratio.numerator, ratio.denominator).astype(np.float32)


if __name__ == "__main__":
    main()
