#!/usr/bin/env python3
"""Batch-render manuscript chapters with Chatterbox (model loaded once).

Local audition tooling only — does not touch the Nova production path.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

from mlx_audio.tts.utils import load_model

sys.path.insert(0, str(Path(__file__).resolve().parent))
from render_chapter_chatterbox import (  # noqa: E402
    MODEL_ID,
    SpeechUnit,
    assemble_units,
    chunk_paragraphs,
    chunk_sentences,
    extract_body,
    units_from_paragraph_chunks,
)
import soundfile as sf  # noqa: E402

CHAPTER_RE = re.compile(r"(?:^|/)(?:\w+-)*?(\d{3})-")


def discover_chapters(roots: list[Path], start: int, end: int) -> list[tuple[int, Path]]:
    found: dict[int, Path] = {}
    for root in roots:
        for path in sorted(root.rglob("*.md")):
            m = CHAPTER_RE.search(path.as_posix())
            if not m:
                continue
            n = int(m.group(1))
            if start <= n <= end:
                found.setdefault(n, path)
    missing = [n for n in range(start, end + 1) if n not in found]
    if missing:
        raise SystemExit(f"Missing chapter files for: {missing}")
    return [(n, found[n]) for n in range(start, end + 1)]


def render_one(
    model,
    chapter_path: Path,
    output_path: Path,
    *,
    ref_audio: str,
    exaggeration: float,
    cfg_weight: float,
    pause_ms: int,
    chunk_mode: str,
    gate_breaths: bool,
) -> float:
    body = extract_body(chapter_path)
    if chunk_mode == "sentences":
        units = chunk_sentences(body)
        if units:
            units = [
                *units[:-1],
                SpeechUnit(text=units[-1].text, pause_after_ms=0),
            ]
    else:
        units = units_from_paragraph_chunks(chunk_paragraphs(body), pause_ms)

    joined = assemble_units(
        model,
        units,
        ref_audio=ref_audio,
        exaggeration=exaggeration,
        cfg_weight=cfg_weight,
        gate_breaths=gate_breaths,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(output_path), joined, 24_000)
    return joined.shape[0] / 24_000


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--start", type=int, default=1)
    parser.add_argument("--end", type=int, default=30)
    parser.add_argument("--ref-audio", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument(
        "--manuscript-root",
        type=Path,
        default=Path("The Final Frontier Novel/chapters"),
    )
    parser.add_argument("--exaggeration", type=float, default=0.7)
    parser.add_argument("--cfg-weight", type=float, default=0.3)
    parser.add_argument("--chunk-mode", choices=("sentences", "paragraphs"), default="sentences")
    parser.add_argument("--pause-ms", type=int, default=350)
    parser.add_argument(
        "--gate-breaths",
        action=argparse.BooleanOptionalAction,
        default=True,
    )
    parser.add_argument("--voice-tag", default="chatterbox-uk-s03")
    parser.add_argument("--skip-existing", action="store_true")
    args = parser.parse_args()

    roots = [args.manuscript_root]
    chapters = discover_chapters(roots, args.start, args.end)
    ref = str(args.ref_audio.resolve())
    print(f"Loading {MODEL_ID} once for {len(chapters)} chapters…", flush=True)
    model = load_model(MODEL_ID)
    t0 = time.time()
    for chapter_num, path in chapters:
        sequence = 4 + chapter_num
        out = args.output_dir / f"{sequence:03d}-chapter-{chapter_num:03d}-{args.voice_tag}.wav"
        if args.skip_existing and out.exists():
            print(f"SKIP chapter {chapter_num} ({out.name})", flush=True)
            continue
        print(f"=== chapter {chapter_num}: {path.name} → {out.name}", flush=True)
        started = time.time()
        seconds = render_one(
            model,
            path,
            out,
            ref_audio=ref,
            exaggeration=args.exaggeration,
            cfg_weight=args.cfg_weight,
            pause_ms=args.pause_ms,
            chunk_mode=args.chunk_mode,
            gate_breaths=args.gate_breaths,
        )
        print(
            f"Wrote {out} ({seconds/60:.1f} min audio, {time.time()-started:.0f}s render)",
            flush=True,
        )
    print(f"Done chapters {args.start}-{args.end} in {(time.time()-t0)/60:.1f} min wall", flush=True)


if __name__ == "__main__":
    main()
