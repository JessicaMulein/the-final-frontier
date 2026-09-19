#!/usr/bin/env python3
"""Select and build Chatterbox reference clips from the EMNS corpus (OpenSLR SLR136).

Local audition tooling only — does not touch the Nova production path.

EMNS is a single-speaker British English emotive corpus (Apache 2.0). Its
utterances are short (mean ~60 chars, ~4-8 s), so a single clip lands in the
same length band as the current `uk-southern-female-03-tight.wav` seed (4.81 s).
To reach the 10-15 s band that zero-shot cloning prefers, this script can splice
several same-emotion clips recorded close together in time into one continuous
reference.

Source audio is Opus-in-WebM at 48 kHz mono. We decode to 24 kHz mono PCM to
match `render_chapter_chatterbox.SAMPLE_RATE`.

Modes
-----
  --report   Duration/level/emotion survey of the corpus. No files written.
  --build    Write reference WAVs for the selected recipe(s).

Example
-------
  PY=.venv/bin/python
  $PY emns_select_refs.py --report --corpus ~/.cache/emns-slr136

  $PY emns_select_refs.py --build \
      --corpus ~/.cache/emns-slr136 \
      --emotion Sad --level 6 --level 7 \
      --target-seconds 13 \
      --out-dir ../../../audiobook/kokoro-audition/emns-refs
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import statistics
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import soundfile as sf

sys.path.insert(0, str(Path(__file__).resolve().parent))

from prosody import dynamic_range_db, pitch_stats, speech_seconds  # noqa: E402

SAMPLE_RATE = 24_000
AUDIO_SUBDIR = "cleaned_webm"
METADATA_NAME = "metadata.csv"

# Gap inserted between spliced utterances. Long enough to read as a sentence
# boundary, short enough that the speaker encoder still sees continuous speech.
SPLICE_GAP_MS = 320.0
EDGE_FADE_MS = 12.0
FINAL_FADE_OUT_MS = 15.0
FINAL_FADE_IN_MS = 8.0


# --------------------------------------------------------------------------- #
# metadata
# --------------------------------------------------------------------------- #


@dataclass
class Utterance:
    uid: str
    text: str
    emotion: str
    level: int
    created: str
    path: Path
    seconds: float = 0.0

    @property
    def stem(self) -> str:
        return self.path.stem


def load_metadata(corpus: Path, *, complete_only: bool = True) -> list[Utterance]:
    meta_path = corpus / METADATA_NAME
    audio_dir = corpus / AUDIO_SUBDIR
    if not meta_path.is_file():
        raise SystemExit(f"metadata not found: {meta_path}")
    if not audio_dir.is_dir():
        raise SystemExit(f"audio dir not found: {audio_dir}")

    out: list[Utterance] = []
    missing = 0
    with meta_path.open(newline="", encoding="utf-8") as handle:
        for row in csv.DictReader(handle, delimiter="|"):
            if complete_only and row.get("status") != "Complete":
                continue
            # metadata stores `wavs/<name>.webm`; extracted tree is cleaned_webm/
            name = Path(row["audio_recording"]).name
            wav = audio_dir / name
            if not wav.is_file():
                missing += 1
                continue
            try:
                level = int(row["level"])
            except (KeyError, ValueError):
                continue
            out.append(
                Utterance(
                    uid=row["id"],
                    text=row["utterance"],
                    emotion=row["emotion"],
                    level=level,
                    created=row.get("date_created", ""),
                    path=wav,
                )
            )
    if missing:
        print(f"note: {missing} metadata rows had no matching audio file", file=sys.stderr)
    return out


# --------------------------------------------------------------------------- #
# audio helpers
# --------------------------------------------------------------------------- #


def require_ffmpeg() -> None:
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise SystemExit(f"{tool} not found on PATH (brew install ffmpeg)")


def probe_seconds(path: Path) -> float:
    """Exact decoded duration.

    Do NOT trust the WebM container's `format=duration` here. These clips came
    from a browser MediaRecorder, whose containers routinely carry absent or
    inflated duration metadata: id=241 advertises 15.28 s and decodes to 8.87 s.
    Counting decoded samples is slower but is the only honest number.
    """
    proc = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-ac",
            "1",
            "-ar",
            str(SAMPLE_RATE),
            "-f",
            "s16le",
            "-",
        ],
        capture_output=True,
    )
    if proc.returncode != 0:
        return 0.0
    return len(proc.stdout) / 2 / SAMPLE_RATE


def measure(utterances: list[Utterance], *, cache_path: Path | None = None) -> None:
    """Fill in `seconds` for each utterance, caching ffprobe results."""
    cache: dict[str, float] = {}
    if cache_path and cache_path.is_file():
        try:
            cache = json.loads(cache_path.read_text())
        except json.JSONDecodeError:
            cache = {}

    fresh = 0
    for index, utt in enumerate(utterances, start=1):
        hit = cache.get(utt.stem)
        if hit is not None:
            utt.seconds = float(hit)
            continue
        utt.seconds = probe_seconds(utt.path)
        cache[utt.stem] = utt.seconds
        fresh += 1
        if fresh % 100 == 0:
            print(f"  probed {index}/{len(utterances)}…", file=sys.stderr)

    if cache_path and fresh:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, indent=0, sort_keys=True))


def decode_to_array(path: Path) -> np.ndarray:
    """Decode any ffmpeg-readable file to 24 kHz mono float32 in [-1, 1]."""
    proc = subprocess.run(
        [
            "ffmpeg",
            "-v",
            "error",
            "-i",
            str(path),
            "-ac",
            "1",
            "-ar",
            str(SAMPLE_RATE),
            "-f",
            "f32le",
            "-",
        ],
        capture_output=True,
    )
    if proc.returncode != 0:
        raise SystemExit(
            f"ffmpeg failed on {path}: {proc.stderr.decode('utf-8', 'replace')[:400]}"
        )
    return np.frombuffer(proc.stdout, dtype=np.float32).copy()


def _raised_cosine(length: int, *, fade_out: bool) -> np.ndarray:
    if length <= 0:
        return np.ones(0, dtype=np.float32)
    ramp = np.linspace(0.0, np.pi, length, dtype=np.float32)
    curve = (1.0 - np.cos(ramp)) * 0.5
    return (curve[::-1] if fade_out else curve).astype(np.float32)


def trim_quiet_edges(
    audio: np.ndarray, *, rms_floor_db: float = -42.0, pad_ms: float = 40.0
) -> np.ndarray:
    """RMS-gated edge trim.

    Gentler than an absolute-amplitude gate: a soft sentence onset or a quiet
    expressive tail survives, which matters for an emotive reference.
    """
    if audio.size == 0:
        return audio
    win = max(1, int(SAMPLE_RATE * 0.010))
    trimmed = audio.astype(np.float32, copy=True)
    frames = np.pad(trimmed, (0, (-trimmed.size) % win)).reshape(-1, win)
    rms = np.sqrt((frames.astype(np.float64) ** 2).mean(axis=1) + 1e-12)
    peak = float(rms.max())
    if peak <= 0.0:
        return trimmed
    threshold = peak * (10.0 ** (rms_floor_db / 20.0))
    active = np.flatnonzero(rms >= threshold)
    if active.size == 0:
        return trimmed
    pad_samples = int(SAMPLE_RATE * pad_ms / 1000)
    start = max(0, int(active[0]) * win - pad_samples)
    end = min(trimmed.size, (int(active[-1]) + 1) * win + pad_samples)
    return trimmed[start:end].copy()


def compact_internal_silence(
    audio: np.ndarray,
    *,
    max_gap_ms: float = 380.0,
    keep_ms: float = 280.0,
    rms_floor_db: float = -42.0,
) -> tuple[np.ndarray, float]:
    """Collapse over-long internal pauses down to `keep_ms`.

    These are remote browser recordings, so the speaker's own hesitations are
    baked in — id=94 carries ~2.5 s of dead air mid-clip. Silence contributes
    nothing to a speaker embedding, so compacting it raises the speech content
    per second of reference without touching pitch, pace or timbre of the
    speech itself.

    Returns the compacted audio and the number of seconds removed.
    """
    if audio.size == 0:
        return audio, 0.0
    win = max(1, int(SAMPLE_RATE * 0.010))
    frames = np.pad(audio, (0, (-audio.size) % win)).reshape(-1, win)
    rms = np.sqrt((frames.astype(np.float64) ** 2).mean(axis=1) + 1e-12)
    peak = float(rms.max())
    if peak <= 0.0:
        return audio, 0.0
    quiet = rms < peak * (10.0 ** (rms_floor_db / 20.0))

    max_gap = int(max_gap_ms / 10)  # in 10 ms frames
    keep = int(keep_ms / 10)
    segments: list[np.ndarray] = []
    removed_frames = 0
    index = 0
    n = quiet.size
    while index < n:
        if not quiet[index]:
            start = index
            while index < n and not quiet[index]:
                index += 1
            segments.append(audio[start * win : min(audio.size, index * win)])
            continue
        start = index
        while index < n and quiet[index]:
            index += 1
        run = index - start
        # Leading/trailing runs are handled by trim_quiet_edges; only squeeze
        # gaps that sit between two stretches of speech.
        interior = start > 0 and index < n
        length = keep if (interior and run > max_gap) else run
        if interior and run > max_gap:
            removed_frames += run - keep
        segments.append(
            np.zeros(length * win, dtype=np.float32)
            if (interior and run > max_gap)
            else audio[start * win : min(audio.size, index * win)]
        )
    out = np.concatenate(segments).astype(np.float32) if segments else audio
    return out, removed_frames * win / SAMPLE_RATE


def normalize_rms(audio: np.ndarray, target_dbfs: float = -20.0) -> np.ndarray:
    """Match perceived loudness across clips before splicing."""
    if audio.size == 0:
        return audio
    rms = float(np.sqrt((audio.astype(np.float64) ** 2).mean()))
    if rms <= 1e-9:
        return audio
    gain = (10.0 ** (target_dbfs / 20.0)) / rms
    out = (audio.astype(np.float32) * gain).astype(np.float32)
    peak = float(np.abs(out).max())
    if peak > 0.99:  # leave headroom, never clip
        out *= 0.99 / peak
    return out


def splice(clips: list[np.ndarray], *, gap_ms: float = SPLICE_GAP_MS) -> np.ndarray:
    """Join clips with a short pause, fading each edge to avoid join clicks."""
    if not clips:
        return np.zeros(0, dtype=np.float32)
    gap = np.zeros(int(SAMPLE_RATE * gap_ms / 1000), dtype=np.float32)
    edge = int(SAMPLE_RATE * EDGE_FADE_MS / 1000)
    parts: list[np.ndarray] = []
    for index, clip in enumerate(clips):
        piece = clip.astype(np.float32, copy=True)
        span = min(edge, max(1, piece.size // 8))
        piece[:span] *= _raised_cosine(span, fade_out=False)
        piece[-span:] *= _raised_cosine(span, fade_out=True)
        parts.append(piece)
        if index < len(clips) - 1:
            parts.append(gap)
    return np.concatenate(parts)


def apply_final_fades(audio: np.ndarray) -> np.ndarray:
    out = audio.astype(np.float32, copy=True)
    fade_in = min(int(SAMPLE_RATE * FINAL_FADE_IN_MS / 1000), max(1, out.size // 8))
    fade_out = min(int(SAMPLE_RATE * FINAL_FADE_OUT_MS / 1000), max(1, out.size // 3))
    out[:fade_in] *= _raised_cosine(fade_in, fade_out=False)
    out[-fade_out:] *= _raised_cosine(fade_out, fade_out=True)
    out[-min(8, out.size) :] = 0.0
    return out


# --------------------------------------------------------------------------- #
# selection
# --------------------------------------------------------------------------- #


@dataclass
class Recipe:
    label: str
    members: list[Utterance] = field(default_factory=list)

    @property
    def seconds(self) -> float:
        base = sum(m.seconds for m in self.members)
        return base + SPLICE_GAP_MS / 1000 * max(0, len(self.members) - 1)


def recipes_from_ids(pool: list[Utterance], ids: list[str]) -> list[Recipe]:
    """Build one single-clip recipe per explicitly requested utterance id.

    Hand-picking beats the greedy grouper once you know which clips you want:
    a single continuous take has no splice seam at all.
    """
    by_id = {u.uid: u for u in pool}
    missing = [i for i in ids if i not in by_id]
    if missing:
        raise SystemExit(f"utterance id(s) not found in corpus: {', '.join(missing)}")
    out: list[Recipe] = []
    for uid in ids:
        utt = by_id[uid]
        out.append(
            Recipe(label=f"{utt.emotion.lower()}-l{utt.level}-{utt.uid}", members=[utt])
        )
    return out


def recipes_from_groups(pool: list[Utterance], groups: list[str]) -> list[Recipe]:
    """Build one spliced ref per comma-separated group of utterance ids.

    Lets you combine clips chosen on measured prosody rather than adjacency,
    which is how you get both a long reference and a wide pitch range: the
    single clips that move the most are only ~6-7 s of speech each.
    """
    by_id = {u.uid: u for u in pool}
    out: list[Recipe] = []
    for group in groups:
        ids = [piece.strip() for piece in group.split(",") if piece.strip()]
        if not ids:
            raise SystemExit(f"empty --splice-group {group!r}")
        missing = [i for i in ids if i not in by_id]
        if missing:
            raise SystemExit(f"utterance id(s) not found: {', '.join(missing)}")
        members = [by_id[i] for i in ids]
        emotions = {m.emotion.lower() for m in members}
        stamp = "-".join(ids)
        prefix = members[0].emotion.lower() if len(emotions) == 1 else "mixed"
        out.append(Recipe(label=f"{prefix}-splice-{stamp}", members=members))
    return out


def build_recipes(
    pool: list[Utterance],
    *,
    target_seconds: float,
    tolerance: float,
    max_members: int,
    count: int,
    min_clip_seconds: float,
    min_final_seconds: float,
) -> list[Recipe]:
    """Greedily group consecutive same-emotion clips up to the target duration.

    Clips are ordered by `date_created` so grouped members come from the same
    recording session — same mic placement, same room, same vocal setup, which
    keeps a spliced reference acoustically coherent.
    """
    usable = [u for u in pool if u.seconds >= min_clip_seconds]
    usable.sort(key=lambda u: (u.created, u.uid))

    recipes: list[Recipe] = []
    index = 0
    while index < len(usable) and len(recipes) < count:
        members: list[Utterance] = []
        total = 0.0
        while index < len(usable) and len(members) < max_members:
            candidate = usable[index]
            projected = total + candidate.seconds + (
                SPLICE_GAP_MS / 1000 if members else 0.0
            )
            if members and projected > target_seconds + tolerance:
                break
            members.append(candidate)
            total = projected
            index += 1
            if total >= target_seconds - tolerance:
                break
        if not members:
            index += 1
            continue
        if total < min_final_seconds:
            # Ran out of adjacent material; only keep a group that still beats
            # the incumbent 4.81 s seed by a clear margin.
            continue
        levels = "-".join(str(m.level) for m in members)
        label = f"{members[0].emotion.lower()}-l{levels}-{members[0].uid}"
        recipes.append(Recipe(label=label, members=members))
    return recipes


# --------------------------------------------------------------------------- #
# reporting
# --------------------------------------------------------------------------- #


def profile_prosody(
    utterances: list[Utterance],
    *,
    cache_path: Path | None,
    compact: bool = True,
) -> dict[str, dict[str, float]]:
    """Measure pitch spread and dynamic range for every clip.

    Emotion labels are a poor proxy for prosodic range: low-arousal classes
    (sadness especially) *flatten* pitch, so "high intensity sad" is monotone.
    Selecting on measured prosody avoids that trap entirely.
    """
    cache: dict[str, dict[str, float]] = {}
    if cache_path and cache_path.is_file():
        try:
            cache = json.loads(cache_path.read_text())
        except json.JSONDecodeError:
            cache = {}

    fresh = 0
    for index, utt in enumerate(utterances, start=1):
        if utt.stem in cache:
            continue
        audio = trim_quiet_edges(decode_to_array(utt.path))
        if compact:
            audio, _ = compact_internal_silence(audio)
        median_hz, pitch_sd, pitch_span = pitch_stats(audio)
        cache[utt.stem] = {
            "wall_seconds": round(audio.size / SAMPLE_RATE, 3),
            "speech_seconds": round(speech_seconds(audio), 3),
            "pitch_median_hz": round(median_hz, 2),
            "pitch_stdev_semitones": round(pitch_sd, 3),
            "pitch_span_semitones": round(pitch_span, 3),
            "dynamic_range_db": round(dynamic_range_db(audio), 2),
        }
        fresh += 1
        if fresh % 100 == 0:
            print(f"  profiled {index}/{len(utterances)}…", file=sys.stderr)

    if cache_path and fresh:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, indent=0, sort_keys=True))
    return cache


def report_prosody(
    utterances: list[Utterance],
    metrics: dict[str, dict[str, float]],
    *,
    baseline: Path | None,
    min_speech: float,
    top: int,
) -> None:
    base: dict[str, float] | None = None
    if baseline and baseline.is_file():
        audio, sr = sf.read(str(baseline), always_2d=False)
        audio = np.asarray(audio, dtype=np.float32)
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        if sr != SAMPLE_RATE:
            print(f"note: baseline is {sr} Hz, metrics assume {SAMPLE_RATE}", file=sys.stderr)
        median_hz, pitch_sd, pitch_span = pitch_stats(audio)
        base = {
            "speech_seconds": speech_seconds(audio),
            "pitch_stdev_semitones": pitch_sd,
            "pitch_span_semitones": pitch_span,
            "dynamic_range_db": dynamic_range_db(audio),
            "pitch_median_hz": median_hz,
        }
        print(
            f"baseline {baseline.name}: speech={base['speech_seconds']:.2f}s "
            f"pitchSD={pitch_sd:.2f} span={pitch_span:.2f} "
            f"dyn={base['dynamic_range_db']:.1f}dB median={median_hz:.0f}Hz\n"
        )

    print("mean prosody by emotion class (clips with enough speech):")
    print(f"{'emotion':12s} {'n':>4s} {'speech_s':>9s} {'pitchSD':>8s} {'span':>7s} {'dynDB':>7s}")
    groups: dict[str, list[dict[str, float]]] = defaultdict(list)
    for utt in utterances:
        m = metrics.get(utt.stem)
        if m and m["speech_seconds"] >= min_speech:
            groups[utt.emotion].append(m)
    ranked_classes = sorted(
        groups.items(),
        key=lambda kv: -sum(m["pitch_span_semitones"] for m in kv[1]) / max(1, len(kv[1])),
    )
    for emotion, group in ranked_classes:
        n = len(group)

        def avg(key: str) -> float:
            return sum(m[key] for m in group) / n

        print(
            f"{emotion:12s} {n:>4d} {avg('speech_seconds'):9.2f} "
            f"{avg('pitch_stdev_semitones'):8.2f} {avg('pitch_span_semitones'):7.2f} "
            f"{avg('dynamic_range_db'):7.1f}"
        )

    eligible = [
        (utt, metrics[utt.stem])
        for utt in utterances
        if utt.stem in metrics and metrics[utt.stem]["speech_seconds"] >= min_speech
    ]
    if base:
        eligible = [
            (u, m)
            for u, m in eligible
            if m["pitch_span_semitones"] > base["pitch_span_semitones"]
            and m["dynamic_range_db"] > base["dynamic_range_db"]
        ]
        print(
            f"\n{len(eligible)} clip(s) beat the baseline on BOTH pitch span and "
            f"dynamic range with >= {min_speech:g}s speech"
        )

    eligible.sort(key=lambda pair: -(pair[1]["pitch_span_semitones"]))
    print(f"\ntop {top} by pitch span:")
    print(
        f"{'id':>5s} {'emotion':11s} {'lvl':>3s} {'speech':>7s} {'pitchSD':>8s} "
        f"{'span':>6s} {'dynDB':>6s}  text"
    )
    for utt, m in eligible[:top]:
        print(
            f"{utt.uid:>5s} {utt.emotion:11s} {utt.level:>3d} "
            f"{m['speech_seconds']:7.2f} {m['pitch_stdev_semitones']:8.2f} "
            f"{m['pitch_span_semitones']:6.2f} {m['dynamic_range_db']:6.1f}  "
            f"{utt.text[:48]}"
        )


def report(utterances: list[Utterance]) -> None:
    print(f"utterances with audio: {len(utterances)}")
    durations = [u.seconds for u in utterances if u.seconds > 0]
    if durations:
        durations.sort()

        def pct(p: float) -> float:
            return durations[min(len(durations) - 1, int(len(durations) * p))]

        print(
            f"duration s: min={durations[0]:.2f} p25={pct(0.25):.2f} "
            f"median={statistics.median(durations):.2f} p75={pct(0.75):.2f} "
            f"p95={pct(0.95):.2f} max={durations[-1]:.2f}"
        )
        print(f"total corpus: {sum(durations)/3600:.2f} h")
        for band in ((0, 5), (5, 8), (8, 11), (11, 99)):
            n = sum(1 for d in durations if band[0] <= d < band[1])
            print(f"  {band[0]:>2d}-{band[1]:<2d} s : {n:>4d}")

    print("\nemotion x level (count) / mean duration")
    by_emotion: dict[str, list[Utterance]] = defaultdict(list)
    for utt in utterances:
        by_emotion[utt.emotion].append(utt)
    header = "emotion         " + "".join(f"{l:>5d}" for l in range(11)) + "    n   mean_s  max_s"
    print(header)
    for emotion in sorted(by_emotion):
        group = by_emotion[emotion]
        levels = Counter(u.level for u in group)
        secs = [u.seconds for u in group if u.seconds > 0]
        mean_s = sum(secs) / len(secs) if secs else 0.0
        max_s = max(secs) if secs else 0.0
        print(
            f"{emotion:16s}"
            + "".join(f"{levels.get(l, 0):>5d}" for l in range(11))
            + f" {len(group):>4d}  {mean_s:6.2f} {max_s:6.2f}"
        )


# --------------------------------------------------------------------------- #
# cli
# --------------------------------------------------------------------------- #


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--corpus",
        type=Path,
        default=Path.home() / ".cache/emns-slr136",
        help="Dir holding metadata.csv and cleaned_webm/",
    )
    parser.add_argument("--report", action="store_true", help="Survey the corpus and exit")
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Measure pitch spread / dynamic range per clip and rank empirically",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        default=None,
        help="Reference WAV to beat (e.g. the incumbent uk-southern-female-03-tight.wav)",
    )
    parser.add_argument("--min-speech", type=float, default=6.0, help="For --profile")
    parser.add_argument("--top", type=int, default=25, help="Rows to show for --profile")
    parser.add_argument("--build", action="store_true", help="Write reference WAVs")
    parser.add_argument(
        "--emotion",
        action="append",
        default=None,
        help="Emotion class to draw from; repeatable (e.g. --emotion Sad)",
    )
    parser.add_argument(
        "--level",
        action="append",
        type=int,
        default=None,
        help="Expressiveness level to keep; repeatable (e.g. --level 6 --level 7)",
    )
    parser.add_argument(
        "--id",
        action="append",
        dest="ids",
        default=None,
        help="Build a single-clip ref from this exact utterance id; repeatable. "
        "Bypasses emotion/level/duration search.",
    )
    parser.add_argument(
        "--splice-group",
        action="append",
        dest="splice_groups",
        default=None,
        help="Comma-separated utterance ids spliced into ONE ref; repeatable "
        "(e.g. --splice-group 599,524)",
    )
    parser.add_argument("--target-seconds", type=float, default=13.0)
    parser.add_argument("--tolerance", type=float, default=2.0)
    parser.add_argument("--max-members", type=int, default=3)
    parser.add_argument("--min-clip-seconds", type=float, default=3.0)
    parser.add_argument(
        "--min-final-seconds",
        type=float,
        default=10.0,
        help="Discard any assembled ref shorter than this",
    )
    parser.add_argument("--count", type=int, default=4, help="How many candidate refs to build")
    parser.add_argument(
        "--keep-internal-silence",
        action="store_true",
        help="Do not collapse long internal pauses (default is to compact them)",
    )
    parser.add_argument("--out-dir", type=Path, default=None)
    parser.add_argument(
        "--manifest",
        type=Path,
        default=None,
        help="Where to write the provenance JSON (defaults inside --out-dir)",
    )
    args = parser.parse_args()

    if not args.report and not args.build and not args.profile:
        parser.error("choose --report, --profile and/or --build")

    require_ffmpeg()
    utterances = load_metadata(args.corpus)
    # v2 = exact decoded duration. v1 trusted the WebM container and was inflated.
    measure(utterances, cache_path=args.corpus / ".duration-cache-v2.json")

    if args.report:
        report(utterances)
        print()

    if args.profile:
        metrics = profile_prosody(
            utterances, cache_path=args.corpus / ".prosody-cache-v1.json"
        )
        report_prosody(
            utterances,
            metrics,
            baseline=args.baseline,
            min_speech=args.min_speech,
            top=args.top,
        )
        print()

    if not args.build:
        return

    if not args.out_dir:
        parser.error("--build requires --out-dir")

    if args.ids or args.splice_groups:
        recipes = []
        if args.ids:
            recipes += recipes_from_ids(utterances, args.ids)
        if args.splice_groups:
            recipes += recipes_from_groups(utterances, args.splice_groups)
        print(f"building {len(recipes)} hand-picked ref(s)")
    else:
        pool = utterances
        if args.emotion:
            wanted = {e.lower() for e in args.emotion}
            pool = [u for u in pool if u.emotion.lower() in wanted]
        if args.level:
            levels = set(args.level)
            pool = [u for u in pool if u.level in levels]
        if not pool:
            raise SystemExit("no utterances matched the emotion/level filters")

        print(f"pool after filters: {len(pool)} utterances")
        recipes = build_recipes(
            pool,
            target_seconds=args.target_seconds,
            tolerance=args.tolerance,
            max_members=args.max_members,
            count=args.count,
            min_clip_seconds=args.min_clip_seconds,
            min_final_seconds=args.min_final_seconds,
        )
    if not recipes:
        raise SystemExit("could not assemble any candidate in the target band")

    out_dir: Path = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    manifest_entries = []

    for recipe in recipes:
        clips = []
        squeezed = 0.0
        for member in recipe.members:
            audio = trim_quiet_edges(decode_to_array(member.path))
            if not args.keep_internal_silence:
                audio, dropped = compact_internal_silence(audio)
                squeezed += dropped
            clips.append(normalize_rms(audio))
        joined = apply_final_fades(splice(clips))
        dest = out_dir / f"emns-{recipe.label}.wav"
        sf.write(str(dest), joined, SAMPLE_RATE, subtype="PCM_16")
        actual = joined.size / SAMPLE_RATE
        voiced = speech_seconds(joined)
        note = f"  (-{squeezed:.2f}s dead air)" if squeezed > 0.01 else ""
        print(
            f"wrote {dest.name}  {actual:5.2f} s wall / {voiced:5.2f} s speech"
            f"  ({len(recipe.members)} clip(s)){note}"
        )
        for member in recipe.members:
            print(f"    [{member.emotion} l{member.level}] {member.text}")
        manifest_entries.append(
            {
                "ref": dest.name,
                "seconds": round(actual, 3),
                "speech_seconds": round(voiced, 3),
                "dead_air_removed_seconds": round(squeezed, 3),
                "sample_rate": SAMPLE_RATE,
                "emotion": recipe.members[0].emotion,
                "levels": [m.level for m in recipe.members],
                "splice_gap_ms": SPLICE_GAP_MS if len(recipe.members) > 1 else 0,
                "members": [
                    {
                        "id": m.uid,
                        "source": m.path.name,
                        "seconds": round(m.seconds, 3),
                        "level": m.level,
                        "text": m.text,
                        "created": m.created,
                    }
                    for m in recipe.members
                ],
            }
        )

    manifest = args.manifest or (out_dir / "emns-refs.json")
    manifest.write_text(
        json.dumps(
            {
                "corpus": "EMNS (Emotive Narrative Storytelling), OpenSLR SLR136",
                "corpus_url": "https://openslr.org/136/",
                "license": "Apache 2.0",
                "attribution": (
                    "Kari Noriy, Xiaosong Yang, Jian Zhang — "
                    "EMNS /Imz/ Corpus: An emotive single-speaker dataset for "
                    "narrative storytelling in games, television and graphic novels (2023)"
                ),
                "speaker": "single female British English speaker, 20s",
                "source_format": "Opus in WebM, 48 kHz mono (lossy)",
                "processing": (
                    "ffmpeg decode to 24 kHz mono f32 -> RMS edge trim -> "
                    + (
                        "internal silence kept as-is -> "
                        if args.keep_internal_silence
                        else "internal pauses >380 ms compacted to 280 ms -> "
                    )
                    + "RMS normalize to -20 dBFS -> splice with "
                    f"{SPLICE_GAP_MS:.0f} ms gap -> raised-cosine fades -> PCM_16"
                ),
                "duration_note": (
                    "Durations are exact decoded sample counts. The source WebM "
                    "containers over-report duration and must not be trusted."
                ),
                "refs": manifest_entries,
            },
            indent=2,
        )
    )
    print(f"\nmanifest: {manifest}")


if __name__ == "__main__":
    main()
