#!/usr/bin/env python3
"""Render a manuscript chapter with local Kokoro TTS (mlx-audio)."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import soundfile as sf
from mlx_audio.tts.utils import load_model

FRONT_MATTER = re.compile(r"^---\n.*?\n---\n+", re.DOTALL)
MODEL_ID = "mlx-community/Kokoro-82M-bf16"
SAMPLE_RATE = 24_000
# Kokoro is happiest around 100–200 tokens; keep chunks short for narration.
MAX_CHARS = 420


def extract_body(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    body = FRONT_MATTER.sub("", text, count=1).strip()
    if not body:
        raise SystemExit(f"No body text in {path}")
    return body


def chunk_paragraphs(text: str, max_chars: int = MAX_CHARS) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
    chunks: list[str] = []
    for paragraph in paragraphs:
        if len(paragraph) <= max_chars:
            chunks.append(paragraph)
            continue
        # Split long paragraphs on sentence boundaries.
        sentences = re.split(r"(?<=[.!?\"'])\s+", paragraph)
        buf = ""
        for sentence in sentences:
            candidate = f"{buf} {sentence}".strip() if buf else sentence
            if len(candidate) <= max_chars:
                buf = candidate
                continue
            if buf:
                chunks.append(buf)
            if len(sentence) <= max_chars:
                buf = sentence
            else:
                # Hard-wrap very long sentences on commas / spaces.
                words = sentence.split()
                buf = ""
                for word in words:
                    candidate = f"{buf} {word}".strip() if buf else word
                    if len(candidate) <= max_chars:
                        buf = candidate
                    else:
                        if buf:
                            chunks.append(buf)
                        buf = word
        if buf:
            chunks.append(buf)
    return chunks


def synthesize(model, text: str, voice: str, lang_code: str, speed: float) -> np.ndarray:
    pieces: list[np.ndarray] = []
    for result in model.generate(
        text=text,
        voice=voice,
        speed=speed,
        lang_code=lang_code,
    ):
        audio = np.asarray(result.audio, dtype=np.float32).reshape(-1)
        if audio.size:
            pieces.append(audio)
    if not pieces:
        raise RuntimeError(f"No audio generated for chunk: {text[:80]!r}")
    return np.concatenate(pieces)


def render(
    chapter_path: Path,
    voice: str,
    output_path: Path,
    *,
    lang_code: str,
    speed: float,
    pause_ms: int,
) -> None:
    body = extract_body(chapter_path)
    chunks = chunk_paragraphs(body)
    print(f"Loading {MODEL_ID} …")
    model = load_model(MODEL_ID)
    pause = np.zeros(int(SAMPLE_RATE * pause_ms / 1000), dtype=np.float32)
    audio_parts: list[np.ndarray] = []
    for index, chunk in enumerate(chunks, start=1):
        preview = chunk.replace("\n", " ")
        print(f"[{index}/{len(chunks)}] {len(chunk)} chars · {preview[:72]}…")
        audio_parts.append(synthesize(model, chunk, voice, lang_code, speed))
        audio_parts.append(pause)
    if audio_parts:
        audio_parts.pop()  # drop trailing pause
    joined = np.concatenate(audio_parts)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), joined, SAMPLE_RATE)
    seconds = joined.shape[0] / SAMPLE_RATE
    print(f"Wrote {output_path} ({seconds/60:.1f} min, {len(chunks)} chunks)")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("chapter", type=Path)
    parser.add_argument("--voice", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--lang-code", default="b")
    parser.add_argument("--speed", type=float, default=1.0)
    parser.add_argument("--pause-ms", type=int, default=350)
    args = parser.parse_args()
    render(
        args.chapter,
        args.voice,
        args.output,
        lang_code=args.lang_code,
        speed=args.speed,
        pause_ms=args.pause_ms,
    )


if __name__ == "__main__":
    main()
