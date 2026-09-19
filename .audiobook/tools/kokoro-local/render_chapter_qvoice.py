#!/usr/bin/env python3
"""Render a chapter with the pure-C Qwen CustomVoice runtime and strict QA.

Production pilot: persistent qvoice, seed-first deterministic candidate search,
large-Whisper structural verification, conservative declicking, gain matching,
and spectrally matched comfort noise between generation units.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import time
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))

from drift import profile as drift_profile  # noqa: E402
from normalize_speech_text import normalize  # noqa: E402
from render_chapter_chatterbox import extract_body  # noqa: E402
from render_chapter_qwen3 import (  # noqa: E402
    SAMPLE_RATE,
    assess_transcript,
    chunk_paragraphs,
    declick,
    verify_chunk,
)
from validate_stt import normalized_tokens  # noqa: E402


def active_rms(audio: np.ndarray) -> float:
    frame = max(1, int(SAMPLE_RATE * 0.020))
    usable = (audio.size // frame) * frame
    if usable == 0:
        return 0.0
    frames = audio[:usable].reshape(-1, frame).astype(np.float64)
    rms = np.sqrt((frames**2).mean(axis=1) + 1e-12)
    peak = float(rms.max())
    voiced = rms[rms >= peak * 10 ** (-36 / 20)]
    return float(np.sqrt(np.mean(voiced**2))) if voiced.size else 0.0


def match_chunk_levels(chunks: list[np.ndarray], limit_db: float = 2.0):
    levels = [active_rms(chunk) for chunk in chunks]
    target = float(np.median([x for x in levels if x > 0]))
    output, gains = [], []
    for chunk, level in zip(chunks, levels):
        if level <= 0 or target <= 0:
            gain_db = 0.0
        else:
            gain_db = 20 * math.log10(target / level)
            gain_db = max(-limit_db, min(limit_db, gain_db))
        gain = 10 ** (gain_db / 20)
        adjusted = chunk.astype(np.float32, copy=True) * gain
        peak = float(np.abs(adjusted).max())
        if peak > 0.99:
            adjusted *= 0.99 / peak
        output.append(adjusted)
        gains.append(round(gain_db, 3))
    return output, gains, target


def comfort_noise(chunks: list[np.ndarray], samples: int, seed: int) -> np.ndarray:
    """Stationary noise shaped to low-energy frames from accepted speech."""
    if samples <= 0:
        return np.zeros(0, dtype=np.float32)
    nfft = 1024
    window = np.hanning(nfft)
    spectra = []
    quiet_rms = []
    for audio in chunks:
        frames = []
        for start in range(0, max(0, audio.size - nfft), nfft // 2):
            frame = audio[start : start + nfft].astype(np.float64)
            frames.append((float(np.sqrt(np.mean(frame**2) + 1e-12)), frame))
        if not frames:
            continue
        values = np.array([r for r, _ in frames])
        lo, hi = np.percentile(values, [5, 18])
        for rms, frame in frames:
            if lo <= rms <= hi and rms > 1e-5:
                spectra.append(np.abs(np.fft.rfft(frame * window)))
                quiet_rms.append(rms)
    if not spectra:
        return np.zeros(samples, dtype=np.float32)

    shape = np.mean(spectra, axis=0)
    target = float(np.median(quiet_rms)) * 0.75
    rng = np.random.default_rng(seed)
    hop = nfft // 2
    blocks = math.ceil((samples + nfft) / hop)
    out = np.zeros(blocks * hop + nfft, dtype=np.float64)
    weight = np.zeros_like(out)
    for index in range(blocks):
        phase = rng.uniform(0, 2 * np.pi, shape.size)
        phase[0] = phase[-1] = 0
        frame = np.fft.irfft(shape * np.exp(1j * phase), n=nfft) * window
        start = index * hop
        out[start : start + nfft] += frame
        weight[start : start + nfft] += window**2
    valid = weight > 1e-8
    out[valid] /= np.sqrt(weight[valid])
    out = out[:samples]
    rms = float(np.sqrt(np.mean(out**2) + 1e-12))
    if rms > 0:
        out *= target / rms
    fade = min(int(SAMPLE_RATE * 0.040), samples // 4)
    if fade > 0:
        out[:fade] *= np.linspace(0, 1, fade)
        out[-fade:] *= np.linspace(1, 0, fade)
    return out.astype(np.float32)


# Same split the chunker uses, so a warm-up boundary always lands where the
# chunker would have put one.
SENTENCE_SPLIT = re.compile(r"(?<=[.!?…])\s+|(?<=[\"”’])\s+(?=[A-Z“\"])")

# The first unit of a chapter has no previous unit to warm up from, so it shipped
# the runtime's cold start raw. Measured on chapter 3: digital silence to 5.8x the
# chapter's median level inside one 20 ms frame, peaking at 8.2x, sample steps to
# 0.11, and zero energy above 6 kHz through the whole burst -- audible as a
# "digital sounding glitch" on the first two words. `declick` scored it 0 clicks
# because it is not a click; it is a spectrally degenerate onset.
#
# So give unit 1 something disposable to burn the cold start on, and trim it with
# the same ASR alignment every other unit uses. Requirements on this text: plain
# common vocabulary, so Whisper transcribes it reliably and the combined-text
# check passes; and a tail that will not collide with a chapter's opening words,
# so the boundary search cannot latch onto the wrong occurrence.
DEFAULT_LEAD_IN = (
    "Before the chapter begins, a short line to settle the voice, "
    "spoken at the same measured pace and then discarded."
)

# The runtime prints this once per generation; it is the only direct measure of
# how long a generation actually ran, which is what drives prosody drift.
GENERATED_RE = re.compile(r"Generated\s+(\d+)\s+frames\s+\(([\d.]+)s audio\)")


def build_warmup(previous_chunk: str, max_words: int) -> str:
    """Trailing sentences of the previous unit, capped to a word budget.

    The warm-up exists for exactly one reason: the runtime stretches and slurs
    the opening word or two of every generation, so something disposable has to
    absorb that. One sentence does it.

    Anything past that is expensive waste. It is generated, ASR-verified, then
    thrown away, and worse, it consumes the part of the generation where the
    model is still stable. The chapter-3 pilot prepended a whole paragraph
    unbounded; chunk 3 drew 76 warm-up words, so 27.4 s of audio was discarded
    and the real text was spoken between 27 s and 100 s of a single generation --
    entirely inside the region where delivery had already started to decay.
    """
    if max_words <= 0:
        return ""
    paragraph = previous_chunk.split("\n\n")[-1].strip()
    sentences = [s.strip() for s in SENTENCE_SPLIT.split(paragraph) if s.strip()]
    if not sentences:
        return ""

    picked: list[str] = []
    words = 0
    for sentence in reversed(sentences):
        count = len(sentence.split())
        if picked and words + count > max_words:
            break
        picked.insert(0, sentence)
        words += count
        if words >= max_words:
            break

    warmup = " ".join(picked)
    # A single runaway sentence would defeat the budget. Entering mid-sentence is
    # fine for warm-up: it is never heard, and the trim aligns on the first word
    # of the real text regardless.
    tokens = warmup.split()
    if len(tokens) > 2 * max_words:
        warmup = " ".join(tokens[-max_words:])
    return warmup


def quiet_cut(
    audio: np.ndarray,
    boundary: float,
    *,
    earliest: float = 0.0,
    back: float = 0.010,
    forward: float = 0.060,
    step_ms: float = 5.0,
    frame_ms: float = 10.0,
) -> float:
    """Cut point at a word boundary, biased forward so no warm-up audio survives.

    Cutting a flat 60 ms before the first kept word -- to protect that word's
    onset -- silently assumes there is 60 ms of silence to spend. When the
    warm-up's final word abuts the first kept word, and Whisper reports exactly
    that (chapter 3 chunk 11: "them" ending at 6.26 s, "I" starting at 6.26 s),
    the 60 ms comes out of the WARM-UP instead. A fragment of already-spoken
    audio at 1.3x the chapter's median level then survived into the delivered
    unit, landing just after a seam and just after the previous unit spoke those
    same words: audible as a stutter on the repeated phrase.

    Searching backward for an energy minimum does not fix it, because in
    continuous speech there is no minimum to find -- measured on that same case,
    the quietest point in the window sits 80 ms BEFORE the boundary and still
    carries 1.3x the median level. The nasal runs straight into the vowel.

    So the margin is spent forward instead. The two error directions are not
    equally bad: clipping a few ms off the onset of a word that is about to be
    spoken anyway is at worst a slight softening, while keeping a few ms of a word
    the listener just heard is a stutter. This searches [-10 ms, +60 ms] around
    the boundary for the least damaging point, which guarantees no residue as long
    as the reported boundary is not early by more than 10 ms, and pairs with a
    fade-in at the cut to hide the onset it does take.
    """
    frame = max(1, int(SAMPLE_RATE * frame_ms / 1000))
    step = max(1, int(SAMPLE_RATE * step_ms / 1000))
    lo = max(0, int(max(earliest, boundary - back) * SAMPLE_RATE))
    hi = min(audio.size - frame, int((boundary + forward) * SAMPLE_RATE))
    if hi <= lo:
        return max(0.0, min(boundary, audio.size / SAMPLE_RATE))
    best_at, best_rms = lo, None
    for start in range(lo, hi + 1, step):
        window = audio[start : start + frame].astype(np.float64)
        rms = float(np.sqrt(np.mean(window**2) + 1e-12))
        if best_rms is None or rms < best_rms:
            best_at, best_rms = start, rms
    return best_at / SAMPLE_RATE


def flatten_level(
    audio: np.ndarray, *, max_db: float = 7.0, window_ms: float = 200.0
) -> tuple[np.ndarray, float]:
    """Undo the within-unit level fade the runtime introduces.

    Delivery decays as a generation runs. Across chapter 3's 15 units the voiced
    level fell in 13, by 17% from start to end on average, which a listener hears
    as the narrator trailing off at the end of a unit -- reported independently at
    the end of unit 1 and at the end of the chapter.

    `match_chunk_levels` cannot touch this: it applies a single gain per unit, so
    it can align units to each other but not repair a slope inside one. This fits
    a line to the voiced level in dB and applies the inverse ramp, bounded and
    mean-preserving, so the unit ends where it started without changing how loud
    it sits relative to its neighbours.

    The bound has to be generous: measured across chapter 3 the fades run to
    -6.5 dB, so a 2.5 dB limit pinned on 10 of 15 units and left most of the
    problem in place. Spread over 25-40 s a 6 dB ramp is 0.2 dB/s, which is well
    under the threshold for hearing a level change as movement, while the fade it
    cancels is plainly audible.

    Returns the corrected audio and the correction applied across the unit in dB.
    """
    window = max(1, int(SAMPLE_RATE * window_ms / 1000))
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

    centres = (np.arange(count) + 0.5) * window / SAMPLE_RATE
    slope = float(np.polyfit(centres[voiced], 20 * np.log10(rms[voiced]), 1)[0])
    span = float(centres[voiced][-1] - centres[voiced][0])
    total = slope * span
    if span <= 0 or abs(total) < 0.5:
        return audio, 0.0

    total = float(np.clip(total, -max_db, max_db))
    midpoint = float(np.mean(centres[voiced]))
    times = np.arange(audio.size, dtype=np.float64) / SAMPLE_RATE
    gain_db = np.clip(-(total / span) * (times - midpoint), -max_db, max_db)
    out = (audio.astype(np.float64) * 10 ** (gain_db / 20)).astype(np.float32)
    loudest = float(np.abs(out).max())
    if loudest > 0.99:
        out *= 0.99 / loudest
    return out, round(-total, 3)


def generated_seconds(log: Path) -> float | None:
    """Seconds of audio the runtime reported generating, from its own log."""
    try:
        text = log.read_text(errors="replace")
    except OSError:
        return None
    matches = GENERATED_RE.findall(text)
    return float(matches[-1][1]) if matches else None


def render_candidate(args, text: str, seed: int, output: Path, log: Path) -> int:
    cmd = [
        str(args.binary),
        "--backend",
        "metal",
        "-d",
        str(args.model),
        "--load-voice",
        str(args.voice),
        "--icl-only",
        "-l",
        "English",
        "--seed",
        str(seed),
        "--temperature",
        str(args.temperature),
        "--top-k",
        "50",
        "--top-p",
        "1.0",
        "--rep-penalty",
        "1.05",
        "--max-tokens",
        str(args.max_tokens),
        "--rate",
        str(args.rate),
        "--instruct",
        args.instruction,
        "--text",
        text,
        "-o",
        str(output),
    ]
    env = os.environ.copy()
    env["QWEN_METAL_FUSED_TALKER"] = "1"
    env.pop("QWEN_METAL_BATCH_MMA", None)
    with log.open("w") as handle:
        return subprocess.run(
            cmd,
            cwd=args.binary.parent,
            env=env,
            text=True,
            stdout=handle,
            stderr=subprocess.STDOUT,
        ).returncode


def transcribe_timed(audio: np.ndarray, *, model: str):
    """Return transcript text and normalized word tokens with timestamps."""
    import mlx_whisper

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
        temp = Path(handle.name)
    try:
        sf.write(str(temp), audio, SAMPLE_RATE)
        result = mlx_whisper.transcribe(
            str(temp),
            path_or_hf_repo=model,
            language="en",
            word_timestamps=True,
            verbose=False,
            condition_on_previous_text=False,
        )
    finally:
        temp.unlink(missing_ok=True)

    words = []
    for segment in result.get("segments", []):
        for word in segment.get("words", []) or []:
            for token in normalized_tokens(word.get("word", "")):
                words.append(
                    {
                        "token": token,
                        "start": float(word["start"]),
                        "end": float(word["end"]),
                    }
                )
    return (result.get("text") or "").strip(), words


def align_new_text_boundary(
    warm_tokens: list[str], new_tokens: list[str], actual: list[str]
) -> int | None:
    """Map the expected warm-up/new-text boundary onto ASR word tokens.

    Prefer an exact opening-prefix match. If the opening is verbalized in a
    different form, map the expected boundary through SequenceMatcher opcodes,
    including ``replace`` spans. Numeric openings are the important case:
    chapter 1 expected ``two point one per second`` while Whisper emitted
    ``2 1 per second``. The old fallback ignored the replacement and chose the
    first later equal word (``per``), trimming away ``2.1`` even though chapter
    WER still passed. A replacement that starts at the boundary belongs to the
    new text, so its first actual token is the cut anchor.
    """
    if not new_tokens:
        return None

    prefix = new_tokens[: min(6, len(new_tokens))]
    search_from = max(0, len(warm_tokens) - 8)
    for index in range(search_from, len(actual) - len(prefix) + 1):
        if actual[index : index + len(prefix)] == prefix:
            return index

    expected = warm_tokens + new_tokens
    boundary = len(warm_tokens)
    opcodes = SequenceMatcher(a=expected, b=actual, autojunk=False).get_opcodes()
    for tag, i1, i2, j1, j2 in opcodes:
        # Most non-exact openings are a replacement beginning exactly here.
        if i1 == boundary:
            return j1 if j1 < len(actual) else None
        if i1 < boundary < i2:
            if tag == "equal":
                return j1 + (boundary - i1)
            if tag == "replace":
                # Preserve the actual side of a replacement that straddles the
                # boundary. Proportional mapping is only a fallback; normal
                # warm-ups end at a sentence boundary, so this is uncommon.
                expected_span = max(1, i2 - i1)
                actual_offset = int((boundary - i1) * (j2 - j1) / expected_span)
                return min(j2, j1 + actual_offset)
            if tag == "delete":
                return j1 if j1 < len(actual) else None

    # Last resort: retain the old behaviour, but only when no opcode maps the
    # boundary at all (malformed ASR alignment rather than a normal replacement).
    for tag, i1, i2, j1, _ in opcodes:
        if tag == "equal" and i2 > boundary:
            return j1 + max(0, boundary - i1)
    return None


def trim_warmup(
    audio: np.ndarray,
    *,
    warmup_text: str,
    new_text: str,
    verify_model: str,
) -> tuple[np.ndarray, dict, list[dict]]:
    """Locate the first new-text word and remove repeated warm-up audio.

    Also returns the delivered words with timestamps rebased onto the trimmed
    audio, so the drift profile can reuse this ASR pass instead of paying for a
    second one.
    """
    transcript, words = transcribe_timed(audio, model=verify_model)
    full_expected = f"{warmup_text}\n\n{new_text}"
    full_quality = assess_transcript(full_expected, transcript)
    if not full_quality["passed"]:
        raise ValueError(
            f"warm-up generation failed: wer={full_quality['wer']} "
            f"gap={full_quality['max_expected_gap']}"
        )

    warm_tokens = list(normalized_tokens(warmup_text))
    new_tokens = list(normalized_tokens(new_text))
    actual = [word["token"] for word in words]
    match_index = align_new_text_boundary(warm_tokens, new_tokens, actual)

    if match_index is None or match_index >= len(words):
        raise ValueError("could not align new-text boundary in warm-up generation")

    boundary = words[match_index]["start"]
    previous_end = words[match_index - 1]["end"] if match_index > 0 else 0.0
    cut_seconds = quiet_cut(audio, boundary, earliest=previous_end)
    cut_sample = min(audio.size, int(cut_seconds * SAMPLE_RATE))
    trimmed = audio[cut_sample:].copy()

    # Any cut leaves a step; ramp in so it cannot click.
    fade = min(int(SAMPLE_RATE * 0.015), trimmed.size)
    if fade > 1:
        ramp = 0.5 * (1 - np.cos(np.linspace(0.0, np.pi, fade)))
        trimmed[:fade] = trimmed[:fade] * ramp.astype(np.float32)

    # How much voiced audio survived ahead of the first kept word. Recorded so a
    # regression here is visible in the manifest instead of only audible.
    residue_frames = trimmed[: max(0, int((boundary - cut_seconds) * SAMPLE_RATE))]
    residue_peak = float(np.abs(residue_frames).max()) if residue_frames.size else 0.0
    delivered_quality = verify_chunk(
        trimmed, new_text, model=verify_model, language="en"
    )
    if not delivered_quality["passed"]:
        raise ValueError(
            f"trimmed delivery failed: wer={delivered_quality['wer']} "
            f"gap={delivered_quality['max_expected_gap']}"
        )
    delivered_words = [
        {
            "token": word["token"],
            "start": word["start"] - cut_seconds,
            "end": word["end"] - cut_seconds,
        }
        for word in words[match_index:]
        if word["end"] > cut_seconds
    ]
    return trimmed, {
        "warmup_words": len(warm_tokens),
        "trim_seconds": round(cut_seconds, 3),
        "boundary_seconds": round(boundary, 3),
        "cut_before_boundary_ms": round((boundary - cut_seconds) * 1000, 1),
        "residue_peak": round(residue_peak, 5),
        "matched_token": words[match_index]["token"],
        "full_quality": {
            key: value for key, value in full_quality.items() if key != "transcript"
        },
        "delivered_quality": {
            key: value
            for key, value in delivered_quality.items()
            if key != "transcript"
        },
    }, delivered_words


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("chapter", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--work-dir", type=Path, required=True)
    p.add_argument("--binary", type=Path, required=True)
    p.add_argument("--model", type=Path, required=True)
    p.add_argument("--voice", type=Path, required=True)
    p.add_argument("--instruction", required=True)
    # Delivery decays with generation length, not with text difficulty. In the
    # chapter-3 pilot every unit that generated 72-93 s of audio was flagged by
    # ear in its final quarter, and the one that generated 34 s was not. 1000
    # chars produced 75-93 s units; ~550 keeps warm-up plus text near 40 s, in
    # the region the model actually holds together. Cheaper units also make a
    # reroll cheap, which matters more than saving seams.
    p.add_argument("--chunk-chars", type=int, default=550)
    p.add_argument("--primary-seed", type=int, default=70)
    p.add_argument(
        "--seed-override",
        action="append",
        default=None,
        metavar="CHUNK:SEED",
        help="Use a different primary seed for one chunk; repeatable",
    )
    p.add_argument("--attempts", type=int, default=6)
    p.add_argument("--temperature", type=float, default=0.5)
    p.add_argument("--rate", type=float, default=0.92)
    p.add_argument("--max-tokens", type=int, default=1800)
    p.add_argument("--pause-ms", type=int, default=650)
    p.add_argument(
        "--overlap-warmup",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Prepend the previous unit's trailing sentences, then trim by ASR",
    )
    p.add_argument(
        "--warmup-max-words",
        type=int,
        default=24,
        help="Word budget for warm-up text (see build_warmup); 0 disables",
    )
    p.add_argument(
        "--lead-in",
        default=DEFAULT_LEAD_IN,
        help="Disposable text warming up chunk 1, trimmed like any warm-up; "
        "pass an empty string to ship the runtime's cold start",
    )
    p.add_argument(
        "--warn-generated-seconds",
        type=float,
        default=50.0,
        help="Warn when a generation exceeds this much audio (drift risk)",
    )
    p.add_argument("--verify-model", default="mlx-community/whisper-large-v3-turbo")
    args = p.parse_args()

    for name in ("binary", "model", "voice", "chapter", "output", "work_dir"):
        setattr(args, name, getattr(args, name).resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.work_dir.mkdir(parents=True, exist_ok=True)

    spoken = normalize(extract_body(args.chapter))
    chunks = chunk_paragraphs(spoken, args.chunk_chars)
    seed_overrides: dict[int, int] = {}
    for item in args.seed_override or []:
        try:
            chunk_index, seed = item.split(":", 1)
            seed_overrides[int(chunk_index)] = int(seed)
        except ValueError:
            raise SystemExit(f"bad --seed-override {item!r}; expected CHUNK:SEED")
    accepted_audio = []
    manifest = {
        "chapter": str(args.chapter),
        "output": str(args.output),
        "voice": str(args.voice),
        "instruction": args.instruction,
        "primary_seed": args.primary_seed,
        "seed_overrides": seed_overrides,
        "overlap_warmup": args.overlap_warmup,
        "warmup_max_words": args.warmup_max_words,
        "lead_in": args.lead_in,
        "chunk_chars": args.chunk_chars,
        "chunks": [],
    }
    started = time.time()

    for index, text in enumerate(chunks, start=1):
        chunk_dir = args.work_dir / f"chunk-{index:03d}"
        chunk_dir.mkdir(parents=True, exist_ok=True)
        warmup_text = ""
        if args.overlap_warmup:
            if index > 1:
                warmup_text = build_warmup(chunks[index - 2], args.warmup_max_words)
            else:
                warmup_text = " ".join(args.lead_in.split())
        generation_text = (
            f"{warmup_text}\n\n{text}" if warmup_text else text
        )
        selected = None
        attempts = []
        print(
            f"=== chunk {index}/{len(chunks)}: {len(text.split())} words"
            + (f" + {len(warmup_text.split())} warm-up" if warmup_text else ""),
            flush=True,
        )
        primary_seed = seed_overrides.get(index, args.primary_seed)
        for offset in range(args.attempts):
            seed = primary_seed + offset
            wav = chunk_dir / f"seed-{seed}.wav"
            log = chunk_dir / f"seed-{seed}.log"
            runtime_exit = render_candidate(args, generation_text, seed, wav, log)
            record = {"seed": seed, "runtime_exit": runtime_exit}
            grown = generated_seconds(log)
            if grown is not None:
                record["generated_seconds"] = grown
            delivered_words = None
            if runtime_exit == 0 and wav.is_file():
                audio, sr = sf.read(str(wav), always_2d=False)
                audio = np.asarray(audio, dtype=np.float32)
                if audio.ndim > 1:
                    audio = audio.mean(axis=1)
                try:
                    if warmup_text:
                        audio, overlap, delivered_words = trim_warmup(
                            audio,
                            warmup_text=warmup_text,
                            new_text=text,
                            verify_model=args.verify_model,
                        )
                        quality = overlap["delivered_quality"]
                        record["overlap"] = overlap
                    else:
                        quality = verify_chunk(
                            audio, text, model=args.verify_model, language="en"
                        )
                except ValueError as error:
                    record["overlap_error"] = str(error)
                    quality = {
                        "passed": False,
                        "wer": 1.0,
                        "coverage": 0.0,
                        "max_expected_gap": len(normalized_tokens(text)),
                        "max_added_span": 0,
                        "suspicious_spans": [],
                    }
                record.update(
                    {
                        "seconds": round(audio.size / sr, 3),
                        **{k: v for k, v in quality.items() if k != "transcript"},
                    }
                )
                print(
                    f"  seed {seed}: {record['seconds']:.1f}s "
                    f"wer={quality['wer']:.3f} cov={quality['coverage']:.3f} "
                    f"gap={quality['max_expected_gap']} pass={quality['passed']}"
                    + (
                        f" trim={record['overlap']['trim_seconds']:.2f}s"
                        if record.get("overlap")
                        else ""
                    )
                    + (f" gen={grown:.1f}s" if grown is not None else ""),
                    flush=True,
                )
                if grown is not None and grown > args.warn_generated_seconds:
                    print(
                        f"  WARNING chunk {index} generated {grown:.1f}s "
                        f"(> {args.warn_generated_seconds:.0f}s); delivery decays "
                        f"late in long generations -- lower --chunk-chars",
                        flush=True,
                    )
                if quality["passed"]:
                    selected = (seed, audio, record, delivered_words)
                    attempts.append(record)
                    break
            attempts.append(record)
        if selected is None:
            manifest["chunks"].append(
                {
                    "index": index,
                    "text": text,
                    "warmup_text": warmup_text,
                    "attempts": attempts,
                    "accepted": False,
                }
            )
            (args.work_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
            raise SystemExit(f"No passing candidate for chunk {index}")
        seed, audio, accepted, delivered_words = selected
        audio, clicks = declick(audio)

        # Report-only, and measured BEFORE the level correction below, so the
        # manifest keeps showing what the model actually did rather than what was
        # patched. Whisper reads slurred speech as correct, so WER and coverage
        # above say nothing about whether delivery held up; this does.
        reuse = delivered_words or None
        drift = drift_profile(
            audio,
            words=reuse,
            model=None if reuse else args.verify_model,
        )

        audio, level_correction_db = flatten_level(audio)
        accepted_audio.append(audio)
        if not drift["skipped"]:
            summary = drift["summary"]
            print(
                f"  drift: wps {summary['median_wps']:.2f}, slowest "
                f"{summary['slowest_vs_median']:.2f}x @{summary['slowest_window']['at']:.0f}s, "
                f"rate trend {summary['wps_trend']:+.2f}, level trend "
                f"{summary['rms_trend']:+.2f}, quietest "
                f"{summary['quietest_window_db']:+.1f}dB",
                flush=True,
            )
        manifest["chunks"].append(
            {
                "index": index,
                "text": text,
                "warmup_text": warmup_text,
                "words": len(text.split()),
                "attempts": attempts,
                "accepted": True,
                "seed": seed,
                "generated_seconds": accepted.get("generated_seconds"),
                "overlap": accepted.get("overlap"),
                "drift": drift,
                "level_correction_db": level_correction_db,
                "clicks_repaired": clicks,
                "raw_active_rms": round(active_rms(audio), 6),
            }
        )

    levelled, gains, target = match_chunk_levels(accepted_audio)
    gap_samples = int(SAMPLE_RATE * args.pause_ms / 1000)
    pieces = []
    cursor = 0
    for index, chunk in enumerate(levelled):
        start = cursor / SAMPLE_RATE
        pieces.append(chunk)
        cursor += chunk.size
        end = cursor / SAMPLE_RATE
        manifest["chunks"][index]["gain_db"] = gains[index]
        manifest["chunks"][index]["start_seconds"] = round(start, 3)
        manifest["chunks"][index]["end_seconds"] = round(end, 3)
        if index < len(levelled) - 1:
            tone = comfort_noise(levelled, gap_samples, seed=1000 + index)
            pieces.append(tone)
            cursor += tone.size
    joined = np.concatenate(pieces)
    peak = float(np.abs(joined).max())
    if peak > 0.99:
        joined *= 0.99 / peak
    sf.write(str(args.output), joined, SAMPLE_RATE, subtype="PCM_16")

    chapter_quality = verify_chunk(
        joined, spoken, model=args.verify_model, language="en"
    )
    manifest["assembly"] = {
        "seconds": round(joined.size / SAMPLE_RATE, 3),
        "level_target_active_rms": round(target, 6),
        "pause_ms": args.pause_ms,
        "comfort_noise": "spectrally shaped from low-energy accepted frames",
        "chapter_quality": {
            key: value for key, value in chapter_quality.items() if key != "transcript"
        },
        "render_wall_seconds": round(time.time() - started, 2),
    }
    (args.work_dir / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(
        f"Wrote {args.output} ({joined.size / SAMPLE_RATE / 60:.2f} min); "
        f"chapter WER={chapter_quality['wer']:.3f} "
        f"coverage={chapter_quality['coverage']:.3f} pass={chapter_quality['passed']}",
        flush=True,
    )
    if not chapter_quality["passed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
