#!/usr/bin/env python3
"""Turn a failing Fish chapter into an actionable omission-repair report.

`scoring.assess_transcript` already *detects* omissions: it reports
`max_expected_gap`, the longest run of manuscript words with no match in the
whole-chapter ASR, and the chapter gate fails when that run reaches 8. What it
does not do is tell a human *which* words went missing, *where* in the prose they
belong, or *where in the audio* to cut to put them back. Reconstructing that by
hand -- diffing manuscript tokens against the ASR, then hunting the splice point
with an energy profile -- is exactly the manual work that repaired chapters 39,
49, 109 and 113. This module captures that work so the next omission is findable,
not just countable.

For a text-to-speech audiobook aimed at blind listeners this is not optional QA.
A dropped clause is invisible in every text metric that stays under threshold, and
a listener who cannot skim back to the page has no way to recover it. The whole
point of the gate is that every word the author wrote is spoken; this tool is how
you act on the gate when it fires.

Three things it does, all Fish-specific and all read-only unless asked to write:

  find    Diff manuscript against the manifest's whole-chapter ASR and, for every
          non-benign expected-gap, print the missing words, the surrounding prose,
          the containing assembly-map speech segment, and a suggested patch region.
          This is the report you feed into patch_verified_omission.py.

  seam    Re-transcribe a window of the delivered audio to confirm a splice reads
          the manuscript text with no stutter, drop or duplication. Uses a temp
          file and condition_on_previous_text=False -- the same robust settings as
          render_chapter_fish.verify -- because micro-slice and word-timestamp
          transcription drift badly and will lie to you about a boundary.

  formats Check that a chapter's delivered WAV, its MP3, and its slot in an M4B all
          agree on duration, so a repaired WAV that never got re-encoded cannot
          ship silently behind its own MP3.

Design choice: this informs a human, it does not repair. Choosing between a
re-render and a patch, and choosing the exact cut so a retained word is not left
fused to a dropped one, needed judgement every time. The suggested region is a
starting point for patch_verified_omission.py, not an automatic edit.
"""

from __future__ import annotations

import argparse
import json
from difflib import SequenceMatcher
from pathlib import Path

import numpy as np
import soundfile as sf

from manuscript import spoken_text
from scoring import is_benign_replace, normalized_tokens

REPO = Path(__file__).resolve().parents[3]

# The gate in scoring.assess_transcript fails a chapter at this run length; a
# report should surface anything at or approaching it, so it defaults one below.
DEFAULT_MIN_GAP = 5


def _load_manifest(manifest_path: Path) -> dict:
    return json.loads(manifest_path.read_text())


def _asr_text(manifest: dict) -> str:
    """The whole-chapter transcript the manifest already recorded.

    assess_transcript threw the transcript string away, but the per-segment ASR is
    kept under chapter_quality.asr_segments; joining it reconstructs the text the
    gate scored without re-running Whisper on ~7 minutes of audio.
    """
    quality = manifest.get("assembly", {}).get("chapter_quality", {})
    segments = quality.get("asr_segments") or []
    return " ".join(str(s.get("text", "")).strip() for s in segments)


def _containing_segment(manifest: dict, rate: int, start_sec: float, end_sec: float):
    """The single assembly-map speech_segment a patch region must live inside.

    patch_verified_omission.py refuses a duration-changing patch that is not wholly
    within one speech_segment, and a Fish tail-omission is dropped from the end of
    exactly such a segment, so the segment boundary is usually the right region end.
    """
    amap = manifest.get("assembly", {}).get("assembly_map") or []
    for entry in amap:
        if entry.get("kind") != "speech_segment":
            continue
        s = entry["start_sample"] / rate
        e = entry["end_sample"] / rate
        if s <= start_sec + 0.05 and e >= end_sec - 0.05:
            return entry
    return None


def _energy_pauses(
    audio: np.ndarray,
    rate: int,
    lo_sec: float,
    hi_sec: float,
    floor_db: float = -42.0,
    min_ms: float = 60.0,
) -> list[tuple[float, float]]:
    """Quiet spans in a window, by short-frame RMS.

    The reliable way to place a splice: word-timestamp transcription drifts across
    windows (it put chapter 109's boundary a full segment away and sent the first
    patch to the wrong place), while the energy floor does not move. A real
    sentence boundary shows here as a contiguous span below the floor.
    """
    lo = max(0, int(lo_sec * rate))
    hi = min(audio.size, int(hi_sec * rate))
    segment = audio[lo:hi]
    frame = max(1, int(rate * 0.010))
    n = segment.size // frame
    if n == 0:
        return []
    levels = np.sqrt(
        (segment[: n * frame].reshape(-1, frame).astype(np.float64) ** 2).mean(axis=1)
        + 1e-12
    )
    db = 20 * np.log10(levels + 1e-9)
    pauses: list[tuple[float, float]] = []
    start = None
    for i in range(n):
        t = lo_sec + i * 0.010
        quiet = db[i] < floor_db
        if quiet and start is None:
            start = t
        elif not quiet and start is not None:
            if (t - start) * 1000 >= min_ms:
                pauses.append((round(start, 3), round(t, 3)))
            start = None
    if start is not None and (hi_sec - start) * 1000 >= min_ms:
        pauses.append((round(start, 3), round(hi_sec, 3)))
    return pauses


def _find_gaps(expected: tuple[str, ...], heard: tuple[str, ...], min_gap: int):
    """Non-benign delete/replace runs of expected words, in manuscript order.

    Mirrors assess_transcript's alignment (same tokenizer, same SequenceMatcher,
    autojunk off) so what this reports is exactly what the gate counted, then keeps
    only runs that is_benign_replace does not excuse -- the number/spelling/homophone
    flips that are ASR noise rather than audible loss.
    """
    matcher = SequenceMatcher(a=expected, b=heard, autojunk=False)
    opcodes = matcher.get_opcodes()
    gaps = []
    for idx, (tag, i1, i2, j1, j2) in enumerate(opcodes):
        if tag not in {"delete", "replace"}:
            continue
        gap = i2 - i1
        if gap < min_gap:
            continue
        exp_part = list(expected[i1:i2])
        heard_part = list(heard[j1:j2])
        if tag == "replace" and is_benign_replace(exp_part, heard_part):
            continue
        # Anchor for audio localization: the last word actually heard immediately
        # before this gap. For a pure deletion heard_part is empty, so fall back to
        # the tail of the preceding equal block -- that heard word is what sits right
        # before the silence/collapse in the audio.
        if heard_part:
            anchor = heard_part[-1]
        elif idx > 0 and opcodes[idx - 1][0] == "equal":
            prev = opcodes[idx - 1]
            anchor = heard[prev[4] - 1] if prev[4] > prev[3] else None
        else:
            anchor = None
        gaps.append(
            {
                "expected_index": i1,
                "expected": exp_part,
                "heard": heard_part,
                "gap": gap,
                "tag": tag,
                "anchor": anchor,
            }
        )
    return gaps


def _prose_context(prose: str, missing: list[str], width: int = 90) -> str:
    """Locate the missing run in the raw prose and show it with surrounding text.

    The tokenized run loses punctuation and casing; anchoring it back in the prose
    gives the human the sentence to re-render as the replacement phrase.
    """
    if not missing:
        return ""
    needle = " ".join(missing)
    hay = prose.lower()
    # Try progressively shorter heads of the run, since the ASR-tokenized words
    # may not match the prose spelling exactly (e.g. hyphenation).
    for length in range(len(missing), 0, -1):
        probe = " ".join(missing[:length]).lower()
        idx = hay.find(probe)
        if idx >= 0:
            start = max(0, idx - width)
            end = min(len(prose), idx + len(needle) + width)
            return ("…" if start else "") + prose[start:end].strip() + ("…" if end < len(prose) else "")
    return "(run not located verbatim in prose; check spelling/hyphenation)"


def cmd_find(args: argparse.Namespace) -> int:
    manifest = _load_manifest(args.manifest)
    chapter_path = Path(manifest["chapter"])
    prose = spoken_text(chapter_path)
    expected = normalized_tokens(prose)
    heard = normalized_tokens(_asr_text(manifest))

    quality = manifest.get("assembly", {}).get("chapter_quality", {})
    rate = manifest.get("assembly", {}).get("sample_rate", 44100)
    print(f"chapter {manifest.get('chapter')}")
    print(f"  title: {manifest.get('canonical_title')}")
    print(
        f"  gate: passed={quality.get('passed')} wer={quality.get('wer')} "
        f"coverage={quality.get('coverage')} "
        f"max_expected_gap={quality.get('max_expected_gap')}"
    )

    gaps = _find_gaps(expected, heard, args.min_gap)
    if not gaps:
        print(f"  no non-benign expected-gaps >= {args.min_gap} tokens; "
              "any failure is benign ASR drift, not audible omission")
        return 0

    audio = None
    if args.audio and Path(manifest["output"]).is_file():
        data, _ = sf.read(manifest["output"], always_2d=False)
        audio = data.mean(axis=1) if data.ndim > 1 else data

    print(f"  {len(gaps)} real omission(s):\n")
    for n, g in enumerate(gaps, 1):
        print(f"  [{n}] {g['tag']} of {g['gap']} expected token(s):")
        print(f"      missing : {' '.join(g['expected'])}")
        if g["heard"]:
            print(f"      heard   : {' '.join(g['heard'])}")
        print(f"      prose   : {_prose_context(prose, g['expected'])}")

        # Locate the seam in audio: the heard fragment before the gap tells us where
        # the drop sits, so the containing speech_segment's end is the natural region
        # end and its pauses give the region start.
        if audio is not None:
            # Anchor by searching the ASR segments for the last heard word before the gap.
            seg = _locate_seam_segment(manifest, rate, g.get("anchor"))
            if seg is not None:
                seg_end = seg["end_sample"] / rate
                pauses = _energy_pauses(audio, rate, max(0, seg_end - 3.0), seg_end)
                region_start = pauses[-1][0] if pauses else round(seg_end - 0.5, 3)
                print(
                    f"      segment : speech_segment {seg['start_sample']/rate:.3f}"
                    f"-{seg_end:.3f}s"
                )
                print(
                    f"      suggest : --start {region_start:.3f} --end {seg_end:.3f} "
                    "--replace-unintelligible --allow-duration-change"
                )
                print(
                    f"      phrase  : re-render the missing run (prefixed with the "
                    "last retained word so the join is not fused), verify in isolation"
                )
        print()
    return 1


def _locate_seam_segment(manifest: dict, rate: int, anchor_word: str | None):
    """Best-guess speech_segment holding the drop, via the ASR segment carrying anchor.

    We match the anchor word (last word heard before the gap) to an ASR segment,
    then return the assembly-map speech_segment whose time range contains that ASR
    segment's end. Tail omissions land at that segment's end boundary.
    """
    quality = manifest.get("assembly", {}).get("chapter_quality", {})
    asr = quality.get("asr_segments") or []
    amap = manifest.get("assembly", {}).get("assembly_map") or []
    target_time = None
    if anchor_word:
        for s in asr:
            if anchor_word.lower() in str(s.get("text", "")).lower():
                target_time = float(s.get("end", 0.0))
    if target_time is None:
        return None
    best = None
    for entry in amap:
        if entry.get("kind") != "speech_segment":
            continue
        s = entry["start_sample"] / rate
        e = entry["end_sample"] / rate
        if s <= target_time <= e + 1.0:
            best = entry
    return best


def _robust_transcribe(audio: np.ndarray, rate: int, a: float, b: float, model: str) -> str:
    """Windowed ASR via temp file, the only settings that read a seam honestly."""
    import tempfile

    import mlx_whisper

    seg = audio[int(a * rate) : int(b * rate)].astype(np.float32)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as handle:
        temp = Path(handle.name)
    try:
        sf.write(str(temp), seg, rate)
        result = mlx_whisper.transcribe(
            str(temp),
            path_or_hf_repo=model,
            language="en",
            condition_on_previous_text=False,
            verbose=False,
        )
    finally:
        temp.unlink(missing_ok=True)
    return (result.get("text") or "").strip()


def cmd_seam(args: argparse.Namespace) -> int:
    data, rate = sf.read(str(args.audio), always_2d=False)
    audio = data.mean(axis=1) if data.ndim > 1 else data
    text = _robust_transcribe(audio, rate, args.start, args.end, args.model)
    print(f"seam [{args.start:.2f}-{args.end:.2f}s]:")
    print(f"  {text}")
    return 0


def _duration(path: Path) -> float:
    return float(sf.info(str(path)).duration)


def cmd_formats(args: argparse.Namespace) -> int:
    """Confirm delivered WAV, its MP3, and an M4B chapter slot agree on duration."""
    import subprocess

    wav_dur = _duration(args.wav)
    print(f"wav : {args.wav.name}  {wav_dur:.2f}s")
    ok = True
    if args.mp3:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_entries", "format=duration",
             "-of", "json", str(args.mp3)],
            capture_output=True, text=True,
        )
        mp3_dur = float(json.loads(out.stdout)["format"]["duration"])
        diff = abs(mp3_dur - wav_dur)
        status = "OK" if diff < 0.5 else "MISMATCH"
        ok = ok and diff < 0.5
        print(f"mp3 : {args.mp3.name}  {mp3_dur:.2f}s  diff {diff:.2f}s  {status}")
    if args.m4b and args.chapter_title:
        out = subprocess.run(
            ["ffprobe", "-v", "quiet", "-show_chapters", "-of", "json", str(args.m4b)],
            capture_output=True, text=True,
        )
        chapters = json.loads(out.stdout).get("chapters", [])
        match = next(
            (c for c in chapters if str(c.get("tags", {}).get("title", "")).startswith(args.chapter_title)),
            None,
        )
        if match is None:
            print(f"m4b : no chapter titled {args.chapter_title!r}  MISMATCH")
            ok = False
        else:
            cdur = float(match["end_time"]) - float(match["start_time"])
            diff = abs(cdur - wav_dur)
            status = "OK" if diff < 0.5 else "MISMATCH"
            ok = ok and diff < 0.5
            print(f"m4b : '{match['tags']['title']}'  {cdur:.2f}s  diff {diff:.2f}s  {status}")
    return 0 if ok else 1


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_find = sub.add_parser("find", help="report real omissions in a chapter manifest")
    p_find.add_argument("manifest", type=Path, help="delivered chapter .manifest.json")
    p_find.add_argument("--min-gap", type=int, default=DEFAULT_MIN_GAP,
                        help=f"minimum expected-token run to report (default {DEFAULT_MIN_GAP})")
    p_find.add_argument("--no-audio", dest="audio", action="store_false",
                        help="skip audio-based region suggestion (report words only)")
    p_find.set_defaults(audio=True, func=cmd_find)

    p_seam = sub.add_parser("seam", help="re-transcribe a splice window to confirm it reads clean")
    p_seam.add_argument("audio", type=Path)
    p_seam.add_argument("--start", type=float, required=True)
    p_seam.add_argument("--end", type=float, required=True)
    p_seam.add_argument("--model", default="mlx-community/whisper-large-v3-turbo")
    p_seam.set_defaults(func=cmd_seam)

    p_fmt = sub.add_parser("formats", help="check WAV/MP3/M4B durations agree for a chapter")
    p_fmt.add_argument("--wav", type=Path, required=True)
    p_fmt.add_argument("--mp3", type=Path, default=None)
    p_fmt.add_argument("--m4b", type=Path, default=None)
    p_fmt.add_argument("--chapter-title", default=None,
                       help="M4B chapter title prefix, e.g. '39.'")
    p_fmt.set_defaults(func=cmd_formats)

    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
