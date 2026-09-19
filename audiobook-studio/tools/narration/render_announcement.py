"""Render spoken chapter announcements in the narrator's voice.

Why
---
The audiobook currently runs one chapter straight into the next. For a listener who
cannot see a player's chapter list, the spoken announcement *is* the navigation, so
this is an accessibility requirement before it is anything else.

It also addresses the measured boundary defect. Brightness falls across a chapter by
about 85 Hz of spectral centroid, and the decay tracks position in the chapter rather
than elapsed generation time -- consistent with the writing turning reflective at
chapter ends rather than with a model fault. Four blind boundary clips were all heard
as the voice getting "lighter, clearer" at the cut. Every attempt to flatten the decay
by equalisation made brightness *less* uniform across chapters and risks artefacts
that this audience would catch. An announcement fixes the join instead of the audio:
it separates the dark ending from the bright opening with a phrase of its own, in a
register that belongs to neither.

The announcement is generated with the same voice, reference, instruct and seed as the
chapters, and anchored the same way, so it is the same narrator rather than a second
voice spliced in.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import mlx.core as mx
import numpy as np
import soundfile as sf

from audio_io import load_reference
from manuscript import chapter_title
from render_chapter_fish import ANCHOR, active_rms

HIFI = Path("out/hifitts-refs")
REPO = Path(__file__).resolve().parents[3]
CHAPTER_ROOT = REPO / "The Final Frontier Novel/chapters"

ONES = [
    "Zero", "One", "Two", "Three", "Four", "Five", "Six", "Seven", "Eight", "Nine",
    "Ten", "Eleven", "Twelve", "Thirteen", "Fourteen", "Fifteen", "Sixteen",
    "Seventeen", "Eighteen", "Nineteen",
]
TENS = [
    "", "", "Twenty", "Thirty", "Forty", "Fifty", "Sixty", "Seventy", "Eighty", "Ninety",
]

# An announcement read in the chapter's own interior voice sounds like the story
# continuing, not like a signpost. It needs to read as structure: plainly, a beat
# slower, and without the reflective colour the prose carries.
ANNOUNCE_INSTRUCT = (
    "Read as a plain spoken heading, not as story: clear, even, unhurried, slightly "
    "formal. State it and stop. No emotion, no interpretation, no trailing off."
)


def spell(number: int) -> str:
    """Chapter numbers as words. The book runs to 128."""
    if number < 20:
        return ONES[number]
    if number < 100:
        tens, rest = divmod(number, 10)
        return TENS[tens] + (f"-{ONES[rest]}" if rest else "")
    hundreds, rest = divmod(number, 100)
    head = f"{ONES[hundreds]} Hundred"
    return f"{head} {spell(rest)}" if rest else head


def title_of(number: int) -> str:
    """Canonical chapter title from the required restricted header."""
    matches = list(CHAPTER_ROOT.glob(f"*/*-{number:03d}-*.md"))
    if len(matches) != 1:
        raise SystemExit(f"chapter {number}: expected one file, found {matches}")
    return chapter_title(matches[0])


def render_one(model, text: str, ref, ref_text: str, rate: int, seed: int) -> np.ndarray:
    mx.random.seed(seed)
    payload = f"<|speaker:0|>{ANCHOR}\n<|speaker:0|>{text}"
    pieces = []
    for result in model.generate(
        text=payload,
        ref_audio=ref,
        ref_text=ref_text,
        instruct=ANNOUNCE_INSTRUCT,
        chunk_length=300,
        max_tokens=1024,
        temperature=0.7,
        top_p=0.7,
        top_k=30,
        verbose=False,
    ):
        pieces.append(np.asarray(result.audio, dtype=np.float32))
    mx.clear_cache()
    if len(pieces) < 2:
        raise RuntimeError(f"anchor not isolated: {len(pieces)} segment(s)")
    return np.concatenate(pieces[1:])


def trim(audio: np.ndarray, rate: int, floor_db: float = -45.0) -> np.ndarray:
    win = max(1, int(0.02 * rate))
    frames = audio[: audio.size - audio.size % win].reshape(-1, win)
    rms = np.sqrt((frames.astype(np.float64) ** 2).mean(axis=1) + 1e-12)
    loud = np.flatnonzero(20 * np.log10(rms / (np.abs(audio).max() + 1e-12)) > floor_db)
    if loud.size == 0:
        return audio
    return audio[loud[0] * win : min(audio.size, (loud[-1] + 1) * win)]


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("chapters", type=int, nargs="+")
    p.add_argument("--out", type=Path, default=Path("out/announcements"))
    p.add_argument("--model", default="mlx-community/fish-audio-s2-pro")
    p.add_argument("--reference", default="hifitts-clean-92")
    p.add_argument("--seed", type=int, default=70)
    p.add_argument(
        "--style",
        choices=("number", "number-title"),
        default="number-title",
        help="'Chapter Eleven' or 'Chapter Eleven. The Mind as a Field.'",
    )
    args = p.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    ref_wav = HIFI / f"{args.reference}.wav"
    ref_text = (HIFI / f"{args.reference}.txt").read_text().strip()

    from mlx_audio.tts.utils import load_model

    print(f"loading {args.model}")
    model = load_model(args.model)
    rate = int(getattr(model, "sample_rate", 44100))
    ref = load_reference(ref_wav, rate)

    records = []
    for number in args.chapters:
        for style in ("number", "number-title") if args.style == "both" else (args.style,):
            text = f"Chapter {spell(number)}."
            if style == "number-title":
                text += f" {title_of(number)}."
            started = time.perf_counter()
            audio = trim(render_one(model, text, ref, ref_text, rate, args.seed), rate)
            path = args.out / f"chapter-{number:03d}-{style}.wav"
            sf.write(str(path), audio, rate, subtype="PCM_16")
            record = {
                "chapter": number,
                "style": style,
                "text": text,
                "seconds": round(audio.size / rate, 3),
                "active_rms": round(active_rms(audio, rate), 6),
                "wall_seconds": round(time.perf_counter() - started, 1),
                "output": str(path),
            }
            records.append(record)
            print(f"  {path.name}: {record['seconds']:.2f}s  \"{text}\"")

    (args.out / "announcements.json").write_text(json.dumps(records, indent=2))
    print(f"\nwrote {len(records)} announcements to {args.out}")


if __name__ == "__main__":
    main()
