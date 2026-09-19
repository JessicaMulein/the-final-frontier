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
import json
import sys
import time
from pathlib import Path

import mlx.core as mx
import numpy as np
import soundfile as sf

import pace
from audio_io import load_reference
from manuscript import spoken_text

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
    """Room tone for the gap between paragraphs, shaped from this render's own floor.

    Two lessons from the QVoice path are folded in here. Digital silence between
    paragraphs is itself audible -- the noise floor dropping to true zero reads as a
    dropout, and it makes any imperfect edge land harder. And the tone has to be
    shaped from the voice's own quiet frames, not white noise, or it reads as hiss.

    The first Fish render had no gap at all: paragraphs were concatenated directly,
    which the listener described as rambling even though the reading was clear.
    """
    if samples <= 0:
        return np.zeros(0, dtype=np.float32)
    nfft = 1024
    window = np.hanning(nfft)
    spectra, quiet = [], []
    for audio in segments:
        levels, frames = [], []
        for start in range(0, max(0, audio.size - nfft), nfft // 2):
            frame = audio[start : start + nfft].astype(np.float64)
            levels.append(float(np.sqrt(np.mean(frame**2) + 1e-12)))
            frames.append(frame)
        if not frames:
            continue
        values = np.array(levels)
        lo, hi = np.percentile(values, [5, 18])
        for level, frame in zip(levels, frames):
            if lo <= level <= hi and level > 1e-5:
                spectra.append(np.abs(np.fft.rfft(frame * window)))
                quiet.append(level)
    if not spectra:
        return np.zeros(samples, dtype=np.float32)

    shape = np.mean(spectra, axis=0)
    target = float(np.median(quiet)) * 0.75
    rng = np.random.default_rng(seed)
    hop = nfft // 2
    blocks = int(np.ceil((samples + nfft) / hop))
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
    level = float(np.sqrt(np.mean(out**2) + 1e-12))
    if level > 0:
        out *= target / level
    fade = min(int(rate * 0.040), samples // 4)
    if fade > 0:
        out[:fade] *= np.linspace(0, 1, fade)
        out[-fade:] *= np.linspace(1, 0, fade)
    return out.astype(np.float32)


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
    """Whole-chapter ASR check, reusing the existing scoring."""
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
    return assess_transcript(expected, (result.get("text") or "").strip())


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
    args = p.parse_args()

    ref_wav = HIFI / f"{args.reference}.wav"
    ref_txt = HIFI / f"{args.reference}.txt"
    if not ref_wav.is_file() or not ref_txt.is_file():
        raise SystemExit(f"reference not found: {ref_wav}")

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
    paragraphs = [p.strip() for p in spoken.split("\n\n") if p.strip()]

    if args.sentence_pause != "none":
        tag = "[short pause]" if args.sentence_pause == "short" else "[pause]"
        paragraphs = [_pause_between_sentences(p, tag) for p in paragraphs]

    units = (
        [s for p in paragraphs for s in _sentences(p)]
        if args.sentence_turns
        else paragraphs
    )
    tagged = "\n".join(f"<|speaker:0|>{u}" for u in units)
    print(
        f"  {len(paragraphs)} paragraphs -> {len(units)} turns"
        f"{' (sentence-level)' if args.sentence_turns else ''}, "
        f"pause tags: {args.sentence_pause}, gap {args.paragraph_gap_ms:.0f}ms"
    )

    payload = f"<|speaker:0|>{ANCHOR}\n{tagged}" if args.anchor else tagged
    if args.anchor:
        if len(ANCHOR.encode("utf-8")) <= args.chunk_length:
            raise SystemExit(
                f"anchor is {len(ANCHOR.encode())} bytes but chunk_length is "
                f"{args.chunk_length}: it would be batched together with the "
                f"chapter's first paragraph and could not be discarded cleanly"
            )
        print(f"  anchor: {len(ANCHOR.split())} words, discarded after generation")
    if args.seed is not None:
        mx.random.seed(args.seed)
        print(f"  seed: {args.seed}")

    print(f"\nrendering (chunk_length={args.chunk_length})", flush=True)
    started = time.perf_counter()
    segments: list[np.ndarray] = []
    records = []
    anchor_audio: np.ndarray | None = None
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
        # Drop the anchor here, before any post-processing, so it cannot influence
        # slope removal, the level target, the room-tone spectrum or the pace profile.
        if args.anchor and anchor_audio is None and not segments:
            anchor_audio = audio
            print(
                f"  anchor  : {audio.size / rate:6.2f}s discarded "
                f"({time.perf_counter() - started:6.1f}s wall)",
                flush=True,
            )
            continue
        segments.append(audio)
        records.append(
            {
                "index": int(getattr(segment, "segment_idx", len(segments) - 1)),
                "seconds": round(audio.size / rate, 3),
                "tokens": int(getattr(segment, "token_count", 0)),
            }
        )
        print(
            f"  segment {len(segments):2d}: {audio.size / rate:6.2f}s "
            f"(total {sum(s.size for s in segments) / rate / 60:5.2f} min, "
            f"{time.perf_counter() - started:6.1f}s wall)",
            flush=True,
        )
    render_seconds = time.perf_counter() - started

    if not segments:
        raise SystemExit("no audio generated")
    anchor_sha256 = None
    if args.anchor:
        if anchor_audio is None:
            raise SystemExit("anchor requested but no segment was yielded for it")
        import hashlib

        anchor_sha256 = hashlib.sha256(anchor_audio.tobytes()).hexdigest()
        print(f"  anchor sha256 {anchor_sha256[:16]} ({anchor_audio.size / rate:.2f}s)")
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
    pieces: list[np.ndarray] = []
    for index, segment in enumerate(levelled):
        pieces.append(segment)
        if index < len(levelled) - 1 and gap_samples > 0:
            pieces.append(comfort_gap(levelled, gap_samples, rate, seed=1000 + index))
    joined = np.concatenate(pieces)
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
    # These offsets are the exact paragraph boundaries for read-along alignment.
    # They come from assembly arithmetic rather than recognition, so they carry no
    # ASR error and bound any later sentence-level alignment inside a known window.
    gap_seconds = gap_samples / rate
    cursor = 0.0
    for index, segment in enumerate(levelled):
        measured = pace.measure(segment if rate == 24000 else _to24k(segment, rate))
        records[index].update(
            {
                "gain_db": gains[index],
                "slope_correction_db": corrections[index],
                "start_seconds": round(cursor, 3),
                "end_seconds": round(cursor + segment.size / rate, 3),
                "pace": measured,
            }
        )
        cursor += segment.size / rate
        if index < len(levelled) - 1:
            cursor += gap_seconds
        if measured:
            print(
                f"  {index:3d} {measured['seconds']:5.1f}   "
                f"{measured['articulation']:12.3f}  "
                f"{measured['pause_fraction'] * 100:5.1f}   "
                f"{measured['longest_gap']:6.2f}"
            )

    live = [r["pace"] for r in records if r.get("pace")]
    manifest = {
        "chapter": str(args.chapter),
        "output": str(args.output.resolve()),
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
            "level_target_active_rms": round(target, 6),
            "render_seconds": round(render_seconds, 1),
            "paragraph_gap_seconds": round(gap_seconds, 6),
            "segment_offsets_include_gaps": True,
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
        quality = verify(joined, rate, spoken, args.verify_model)
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
    expected_seconds = round(joined.size / rate, 3)
    final_end = records[-1]["end_seconds"] if records else 0.0
    if abs(final_end - expected_seconds) > 0.05:
        raise SystemExit(
            f"segment offsets do not describe the written audio: last segment ends at "
            f"{final_end:.3f}s but the file is {expected_seconds:.3f}s long"
        )

    manifest_path = args.output.with_suffix(".manifest.json")
    manifest_path.write_text(json.dumps(manifest, indent=2))
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
