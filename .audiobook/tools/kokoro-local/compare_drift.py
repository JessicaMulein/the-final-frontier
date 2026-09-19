#!/usr/bin/env python3
"""Compare intra-unit delivery decay between two qvoice renders of one chapter.

Both renders are measured the same way -- profiling each accepted unit as it sits
in the assembled chapter -- so the comparison does not depend on what either run
happened to record in its own manifest.

Usage:
    compare_drift.py OLD_REVIEW_DIR NEW_REVIEW_DIR
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import soundfile as sf

from drift import profile

MODEL = "mlx-community/whisper-large-v3-turbo"


def load_mono(path: Path):
    audio, sr = sf.read(str(path), always_2d=False)
    audio = np.asarray(audio, dtype=np.float32)
    if audio.ndim > 1:
        audio = audio.mean(axis=1)
    return audio, sr


def measure(review: Path, model: str) -> dict:
    manifest = json.load(open(review / "work" / "manifest.json"))
    wav = review / Path(manifest["output"]).name
    audio, sr = load_mono(wav)
    rows = []
    for chunk in manifest["chunks"]:
        if not chunk.get("accepted"):
            continue
        seg = audio[int(chunk["start_seconds"] * sr) : int(chunk["end_seconds"] * sr)]
        result = profile(seg, model=model)
        rows.append(
            {
                "index": chunk["index"],
                "generated_seconds": chunk.get("generated_seconds"),
                "delivered_seconds": result["seconds"],
                "warmup_words": len((chunk.get("warmup_text") or "").split()),
                "profile": result,
            }
        )
    return {"name": wav.name, "manifest": manifest, "rows": rows}


def report(run: dict) -> None:
    m = run["manifest"]
    print(f"\n=== {run['name']}")
    print(
        f"    chunk_chars={m.get('chunk_chars')} "
        f"warmup_max_words={m.get('warmup_max_words', 'unbounded')} "
        f"chunks={len(run['rows'])} "
        f"total={m['assembly']['seconds']:.1f}s "
        f"wall={m['assembly']['render_wall_seconds']:.0f}s"
    )
    print(
        "  ch  gen_s  del_s  wu  med_wps  slowest  rate_trend  "
        "quietest_dB  lvl_trend  longest_word"
    )
    for row in run["rows"]:
        p = row["profile"]
        gen = row["generated_seconds"]
        gen_s = f"{gen:5.1f}" if isinstance(gen, (int, float)) else "    -"
        if p["skipped"]:
            print(
                f"  {row['index']:2d}  {gen_s} {p['seconds']:6.1f}"
                f" {row['warmup_words']:3d}   (skipped: {p['reason']})"
            )
            continue
        s = p["summary"]
        print(
            f"  {row['index']:2d}  {gen_s} {p['seconds']:6.1f} {row['warmup_words']:3d}"
            f"   {s['median_wps']:6.2f}   {s['slowest_vs_median']:6.2f}"
            f"      {s['wps_trend']:+6.2f}"
            f"      {s['quietest_window_db']:+6.1f}     {s['rms_trend']:+6.2f}"
            f"   {s['longest_word']['token']!r} {s['longest_word']['ms']:.0f}ms"
        )


def aggregate(run: dict) -> dict:
    live = [r for r in run["rows"] if not r["profile"]["skipped"]]
    gens = [
        r["generated_seconds"]
        for r in run["rows"]
        if isinstance(r["generated_seconds"], (int, float))
    ]
    if not live:
        return {}
    slowest = [r["profile"]["summary"]["slowest_vs_median"] for r in live]
    rate_trend = [r["profile"]["summary"]["wps_trend"] for r in live]
    lvl_trend = [r["profile"]["summary"]["rms_trend"] for r in live]
    quiet = [r["profile"]["summary"]["quietest_window_db"] for r in live]
    longest = [r["profile"]["summary"]["longest_word"]["ms"] for r in live]
    return {
        "units": len(run["rows"]),
        "max_generated": max(gens) if gens else None,
        "mean_generated": float(np.mean(gens)) if gens else None,
        "worst_slowest_vs_median": min(slowest),
        "mean_rate_trend": float(np.mean(rate_trend)),
        "mean_level_trend": float(np.mean(lvl_trend)),
        "worst_quietest_db": min(quiet),
        "max_longest_word_ms": max(longest),
    }


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("old", type=Path)
    p.add_argument("new", type=Path)
    p.add_argument("--model", default=MODEL)
    args = p.parse_args()

    runs = []
    for review in (args.old, args.new):
        run = measure(review, args.model)
        report(run)
        runs.append(run)

    print("\n=== summary (negative trend = slowing / fading across a unit)")
    a, b = aggregate(runs[0]), aggregate(runs[1])
    labels = [
        ("units", "generation units", "{:.0f}"),
        ("max_generated", "longest generation (s)", "{:.1f}"),
        ("mean_generated", "mean generation (s)", "{:.1f}"),
        ("worst_slowest_vs_median", "worst window vs own median", "{:.2f}"),
        ("mean_rate_trend", "mean rate trend", "{:+.3f}"),
        ("mean_level_trend", "mean level trend", "{:+.3f}"),
        ("worst_quietest_db", "worst quiet window (dB)", "{:+.1f}"),
        ("max_longest_word_ms", "longest single word (ms)", "{:.0f}"),
    ]
    print(f"  {'metric':30s} {'old':>10s} {'new':>10s}")
    for key, label, fmt in labels:
        if a.get(key) is None or b.get(key) is None:
            continue
        print(f"  {label:30s} {fmt.format(a[key]):>10s} {fmt.format(b[key]):>10s}")


if __name__ == "__main__":
    main()
