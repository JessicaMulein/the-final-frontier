#!/usr/bin/env python3
"""Make chapter-to-chapter presence consistent without changing speech.

The apparent voice varies between files. Before blaming zero-shot cloning, remove the
much larger measurable confound: each chapter is level-matched to its OWN segment
median, and those chapter targets span 4.91 dB peak-to-peak. A five-decibel change in
presence makes the same voice sound closer, fuller, older, or simply different.

This uses only attenuation for the diagnostic: every chapter is brought to the
quietest completed chapter's active-RMS target. No limiter, no clipping, no dynamics
processing and no amplification. The waveform shape is identical, just scaled. If
the normalised transition sounds like one speaker where the original does not, the
problem is mastering rather than the clone.

Never writes in place. For `--transitions`, it writes the same tail/head clips as
`diagnose_voice.py`, with the gain values embedded in the report.
"""

from __future__ import annotations

import argparse
import glob
import json
import re
from pathlib import Path

import numpy as np
import soundfile as sf


def chapter(path: Path) -> int:
    match = re.search(r"chapter-(\d{3})", path.name)
    return int(match.group(1)) if match else -1


def inventory(audio_dir: Path):
    rows = []
    for manifest_path in sorted(audio_dir.glob("*.manifest.json"), key=chapter):
        manifest = json.loads(manifest_path.read_text())
        wav = Path(manifest["output"])
        # Manifests from the running render store out/book paths relative to the
        # narration directory. The sibling file is authoritative if that path does
        # not resolve from the caller's cwd.
        if not wav.is_file():
            wav = audio_dir / manifest_path.name.replace(".manifest.json", ".wav")
        if not wav.is_file():
            continue
        target = float(manifest["assembly"].get("level_target_active_rms") or 0)
        if target <= 0:
            continue
        rows.append((chapter(wav), wav, target))
    return rows


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("audio_dir", type=Path, nargs="?", default=Path("out/book"))
    p.add_argument("--out", type=Path, default=Path("out/voice-transitions-normalised"))
    p.add_argument("--seconds", type=float, default=12.0)
    p.add_argument("--write-chapters", action="store_true")
    args = p.parse_args()

    rows = inventory(args.audio_dir)
    if not rows:
        raise SystemExit("no passing chapter manifests found")
    target = min(r[2] for r in rows)
    print(f"{len(rows)} chapters; diagnostic target {target:.6f} (quietest chapter)")

    loaded = {}
    report = {"target_active_rms": target, "chapters": [], "transitions": []}
    args.out.mkdir(parents=True, exist_ok=True)
    for number, path, original_target in rows:
        audio, rate = sf.read(str(path), always_2d=False)
        audio = np.asarray(audio, dtype=np.float32)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        gain = target / original_target
        gain_db = 20 * np.log10(gain)
        adjusted = audio * gain
        loaded[number] = (adjusted, int(rate), path)
        report["chapters"].append(
            {
                "chapter": number,
                "file": path.name,
                "original_target": original_target,
                "gain_db": round(float(gain_db), 3),
            }
        )
        if args.write_chapters:
            sf.write(
                str(args.out / path.name), adjusted, rate, subtype="PCM_16"
            )

    for left in sorted(loaded):
        right = left + 1
        if right not in loaded:
            continue
        a, rate, _ = loaded[left]
        b, b_rate, _ = loaded[right]
        if b_rate != rate:
            continue
        span = int(rate * args.seconds)
        gap = np.zeros(int(rate * 0.5), dtype=np.float32)
        clip = np.concatenate([a[-span:], gap, b[:span]])
        filename = f"ch{left:03d}-to-{right:03d}.wav"
        sf.write(str(args.out / filename), clip, rate, subtype="PCM_16")
        report["transitions"].append(
            {"from": left, "to": right, "file": filename}
        )

    (args.out / "report.json").write_text(json.dumps(report, indent=2))
    print(f"wrote {len(report['transitions'])} transition clips to {args.out}")
    print("all gains <= 0 dB; no limiter or amplification used")
    print("compare against out/voice-transitions/chNNN-to-NNN.wav")


if __name__ == "__main__":
    main()
