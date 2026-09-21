#!/usr/bin/env python3
"""Render the whole book with Fish S2 Pro, resumably, and report what to listen to.

Settings are the ones the listener approved on chapter 3: the `hifitts-clean-92`
reference, the interior-memoir direction, 650 ms of shaped room tone between
paragraphs, and `[short pause]` between sentences. They are not exposed as knobs
here on purpose — a book should be one voice, and a flag that drifts mid-run is how
chapter 60 stops matching chapter 3.

Resumability is the point. At the measured RTF of 1.33 this is roughly a 20-hour
job, so it must survive being interrupted, and it must never silently redo work.
A chapter is skipped only if its audio exists AND its manifest records a pass, so a
half-written file from a kill is regenerated rather than trusted.

What this does NOT do is certify the output. A passing chapter here means no
text-level problem was found. The defect class that cost this project a session --
an intra-word stutter that Whisper normalises into the correct token -- is not
detectable by anything in this script, and the acoustic judges are not built yet.
The listen list it emits is therefore a triage aid, not a guarantee.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import soundfile as sf

from render_chapter_fish import MANIFEST_SCHEMA, production_identity

REPO = Path(__file__).resolve().parents[3]
CHAPTERS = REPO / "The Final Frontier Novel/chapters"
HERE = Path(__file__).resolve().parent

# Delivery naming already established in audiobook/: sequence = 4 + chapter.
SEQUENCE_OFFSET = 4
VOICE_TAG = "fish-clean92"

# Narrow, evidence-backed exceptions. Every value is part of production identity, so
# resume cannot confuse an exceptional render with the default pipeline.
CHAPTER_OVERRIDES: dict[int, dict] = {
    13: {
        # 2,166 words exceed this Fish conversation's reliable stamina. One call
        # deterministically fails near the end; two calls re-anchored to the same
        # byte-identical state pass whole-chapter ASR.
        "max_words_per_call": 1100,
    },
    15: {
        # Fish treats the Markdown-emphasized phrase beginning "Open Channel" like an
        # instruction and produces unintelligible audio. Punctuation-only generation
        # spelling preserves the verifier's token sequence; the bad region is then
        # replaced by a separately verified phrase at identical duration.
        "spoken_replacements": (
            "*Open Channel working group*, lower case, in a footnote="
            "Open-Channel working group, lower-case, in a footnote",
        ),
        "patch": {
            "phrase": REPO
            / "audiobook-studio/assets/production-patches/ch015-open-channel-working-group.wav",
            "start": 25.32,
            "end": 28.88,
            "announcement_text": "Chapter Fifteen. Who Will Be Holding It.",
        },
    },
    26: {
        # Eleven words collapse into 1.11 seconds of unintelligible speech. Replace
        # that exact sample-map-bounded region with a normally paced verified phrase;
        # the patcher shifts every later assembly/read-along offset by the delta.
        "patch": {
            "phrase": REPO
            / "audiobook-studio/assets/production-patches/ch026-confidentiality-terms.wav",
            "start": 161.40,
            "end": 162.511497,
            "announcement_text": "Chapter Twenty-Six. Already Outside.",
            "allow_duration_change": True,
        },
    },
    39: {
        # Two tail-of-sentence omissions: (1) "moved one deliberate correction in
        # front of an ordinary delay" dropped from the end of the page-three sentence,
        # and (2) "disabled unless both participants expressly enable it for one
        # identified session" dropped from the end of the definitions paragraph.
        # Re-rendering at seed 70 reproduces both deterministically.
        "patches": [
            {
                "phrase": REPO
                / "audiobook-studio/assets/production-patches/ch039-deliberate-correction.wav",
                "start": 70.64,
                "end": 71.22,
                "announcement_text": "Chapter Thirty-Nine. A Benefit Becomes a Platform.",
                "allow_duration_change": True,
            },
            {
                "phrase": REPO
                / "audiobook-studio/assets/production-patches/ch039-content-recording-session.wav",
                "start": 218.17,
                "end": 218.666,
                "announcement_text": "Chapter Thirty-Nine. A Benefit Becomes a Platform.",
                "allow_duration_change": True,
            },
        ],
    },
    113: {
        # A 10-word clause ("and that nobody had yet written down what it took") is
        # dropped from the end of the chapter's final long sentence: the audio jumps
        # from "give somebody," straight to "I read it back". The verified phrase
        # re-supplies "give somebody, and that nobody ..." from just before "give",
        # inside the speech segment that ends at the paragraph gap.
        "patch": {
            "phrase": REPO
            / "audiobook-studio/assets/production-patches/ch113-nobody-wrote-it-down.wav",
            "start": 274.64,
            "end": 275.584,
            "announcement_text": "Chapter One Hundred Thirteen. What Went Out.",
            "allow_duration_change": True,
        },
    },
    109: {
        # The 14-word tail of subhead five ("external actor remains an inference ...
        # has not been established") is dropped: the audio truncates "actor" to "act"
        # and jumps to the next paragraph. The corrupt "act" is the last word of one
        # speech segment, so the region stays inside that segment (end at the segment
        # boundary) and the phrase re-supplies "external actor ...".
        "patch": {
            "phrase": REPO
            / "audiobook-studio/assets/production-patches/ch109-external-actor-inference.wav",
            "start": 208.10,
            "end": 208.74,
            "announcement_text": "Chapter One Hundred Nine. Into the History.",
            "allow_duration_change": True,
        },
    },
    49: {
        # An 83-word span ("...becomes action on a configuration change ... a lawyer
        # can deliver") collapses into the single fused utterance "becomes actionable".
        # "becomes" and the corrupted syllable share one continuous waveform, so no cut
        # at that boundary preserves "becomes" without leaving an "actionable" stutter.
        # The region is instead opened back to the deep pause after "reception work,"
        # and the verified phrase re-supplies "and it becomes action on a ...".
        "patch": {
            "phrase": REPO
            / "audiobook-studio/assets/production-patches/ch049-position-of-record.wav",
            "start": 132.70,
            "end": 134.14,
            "announcement_text": "Chapter Forty-Nine. Filed as Agreed.",
            "allow_duration_change": True,
        },
    },
}


def inventory() -> list[tuple[int, Path]]:
    """(chapter number, path) for every chapter, ordered by the front matter."""
    found: dict[int, Path] = {}
    for path in sorted(CHAPTERS.glob("*/*.md")):
        head = path.read_text(errors="replace")[:800]
        match = re.search(r"^chapter:\s*(\d+)", head, re.M)
        if not match:
            continue
        number = int(match.group(1))
        if number in found:
            raise SystemExit(f"duplicate chapter {number}: {path} and {found[number]}")
        found[number] = path
    return sorted(found.items())


def output_for(out_dir: Path, number: int) -> Path:
    return out_dir / f"{SEQUENCE_OFFSET + number:03d}-chapter-{number:03d}-{VOICE_TAG}.wav"


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def already_done(
    wav: Path,
    *,
    chapter: Path,
    announcement: Path | None,
    reference: str,
    seed: int,
    anchored: bool,
    overrides: dict | None = None,
) -> dict | None:
    """Return a current, byte-bound production manifest or require a rerender.

    A large WAV beside a passing JSON file is not a resume contract. The previous
    implementation accepted exactly that, so changing prose, title, announcement,
    narrator reference, seed, anchor, gap algorithm, renderer settings, or the WAV
    bytes themselves could silently keep stale audio.
    """
    manifest = wav.with_suffix(".manifest.json")
    if not wav.is_file() or not manifest.is_file():
        return None
    try:
        data = json.loads(manifest.read_text())
        override = overrides or {}
        expected = production_identity(
            chapter,
            announcement=announcement,
            reference_name=reference,
            seed=seed,
            anchored=anchored,
            max_words_per_call=int(override.get("max_words_per_call", 0)),
            spoken_replacements=tuple(override.get("spoken_replacements", ())),
        )
    except (json.JSONDecodeError, OSError, RuntimeError):
        return None

    if data.get("schema_version") != MANIFEST_SCHEMA:
        return None
    recorded_identity = data.get("production_identity") or {}
    if recorded_identity.get("identity_sha256") != expected["identity_sha256"]:
        return None
    if data.get("output") != str(wav.resolve()):
        return None
    if data.get("output_sha256") != _sha256_file(wav):
        return None

    assembly = data.get("assembly") or {}
    quality = assembly.get("chapter_quality") or {}
    if not quality.get("passed"):
        return None
    if assembly.get("gap_algorithm") != "spectral-v6":
        return None
    if assembly.get("gap_fft_size") != 2048:
        return None
    if not assembly.get("segment_offsets_include_gaps"):
        return None
    try:
        info = sf.info(str(wav))
    except (RuntimeError, OSError):
        return None
    if info.samplerate != assembly.get("sample_rate"):
        return None
    if info.frames != assembly.get("sample_count"):
        return None
    if abs(info.duration - float(assembly.get("seconds", 0.0))) > 0.01:
        return None
    assembly_map = assembly.get("assembly_map")
    if not isinstance(assembly_map, list) or not assembly_map:
        return None
    if assembly_map[0].get("start_sample") != 0:
        return None
    if assembly_map[-1].get("end_sample") != info.frames:
        return None
    for left, right in zip(assembly_map, assembly_map[1:]):
        if left.get("end_sample") != right.get("start_sample"):
            return None
    speech_entries = [e for e in assembly_map if e.get("kind") == "speech_segment"]
    segments = data.get("segments") or []
    if len(speech_entries) != len(segments):
        return None
    if any(
        entry.get("start_sample") != segment.get("start_sample")
        or entry.get("end_sample") != segment.get("end_sample")
        for entry, segment in zip(speech_entries, segments)
    ):
        return None
    gaps = [e for e in assembly_map if str(e.get("kind", "")).endswith("_gap")]
    if not gaps or any(e.get("algorithm") != "spectral-v6" for e in gaps):
        return None
    if not quality.get("asr_segments"):
        return None
    override_patches = override.get("patches") or ([override["patch"]] if override.get("patch") else [])
    if override_patches:
        patches = assembly.get("production_patches") or []
        if len(patches) != len(override_patches):
            return None
        if any(p.get("kind") != "verified_unintelligible_replacement" for p in patches):
            return None
    if wav.stat().st_size < 1_000_000:
        return None
    return data


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    # Deliverables belong in the repo's `audiobook/` directory, which is reserved
    # for final output only: the WAVs, the MP3s derived from them, and the M4B.
    # Tooling inputs, provenance and superseded renders live under `audiobook-studio/`.
    p.add_argument("--out-dir", type=Path, default=REPO / "audiobook")
    p.add_argument("--first", type=int, default=1)
    p.add_argument("--last", type=int, default=128)
    p.add_argument("--reference", default="hifitts-clean-92")
    # The settled production spec. Defaults are the decided values rather than
    # opt-ins, so a full run cannot quietly omit them: a book rendered without the
    # anchor, without a fixed seed, or without spoken announcements is a different
    # book, and the last of those removes a blind listener's only way to know where
    # they are without touching the device.
    p.add_argument(
        "--seed",
        type=int,
        default=70,
        help="MLX RNG seed reset before each chapter; Fish exposes no seed argument",
    )
    p.add_argument(
        "--no-anchor",
        action="store_true",
        help="skip the deterministic discarded lead-in. Off by default: anchoring was "
        "chosen blind and measurably narrows chapter-to-chapter pitch drift",
    )
    p.add_argument(
        "--announce-dir",
        type=Path,
        default=HERE / "out/announcements",
        help="rendered chapter announcements, one per chapter",
    )
    p.add_argument(
        "--no-announcements",
        action="store_true",
        help="render without spoken chapter announcements. Off by default: they are "
        "primary navigation for a listener who cannot see a chapter list",
    )
    p.add_argument(
        "--retries",
        type=int,
        default=1,
        help="re-render a chapter this many extra times if QA fails",
    )
    p.add_argument("--dry-run", action="store_true")
    args = p.parse_args()

    chapters = [(n, path) for n, path in inventory() if args.first <= n <= args.last]
    print(f"{len(chapters)} chapters in range {args.first}-{args.last}")
    args.out_dir.mkdir(parents=True, exist_ok=True)

    # Resolve every announcement before rendering anything. Discovering a missing one
    # nineteen hours into a twenty-one hour run, having already written chapters that
    # silently lack navigation, is the failure this prevents.
    announcements: dict[int, Path] = {}
    if not args.no_announcements:
        missing = []
        for number, _ in chapters:
            expected = args.announce_dir / f"chapter-{number:03d}-number-title.wav"
            if expected.is_file():
                announcements[number] = expected
            else:
                missing.append(number)
        if missing:
            raise SystemExit(
                f"no announcement for chapter(s) {_ranges(missing)} in "
                f"{args.announce_dir}\n"
                f"render them first:  python render_announcement.py "
                f"{args.first} .. {args.last} --style number-title\n"
                f"or pass --no-announcements to render prose only."
            )
        print(f"  {len(announcements)} announcements resolved")
    else:
        print("  announcements DISABLED; chapters will carry no spoken navigation")

    print(
        f"  seed {args.seed}, anchor {'off' if args.no_anchor else 'on'}, "
        f"reference {args.reference}"
    )

    pending, skipped = [], []
    for number, path in chapters:
        if already_done(
            output_for(args.out_dir, number),
            chapter=path,
            announcement=announcements.get(number),
            reference=args.reference,
            seed=args.seed,
            anchored=not args.no_anchor,
            overrides=CHAPTER_OVERRIDES.get(number),
        ):
            skipped.append(number)
        else:
            pending.append((number, path))
    print(f"  {len(skipped)} already rendered and passing, {len(pending)} to do")
    if skipped:
        print(f"  skipping: {_ranges(skipped)}")

    if args.dry_run:
        for number, path in pending[:10]:
            print(f"  would render {number:3d}  {path.name}")
        if len(pending) > 10:
            print(f"  ... and {len(pending) - 10} more")
        return

    report_path = args.out_dir / "book-report.json"
    report = json.loads(report_path.read_text()) if report_path.is_file() else {}

    started = time.perf_counter()
    failures = []
    for index, (number, path) in enumerate(pending, start=1):
        wav = output_for(args.out_dir, number)
        elapsed = time.perf_counter() - started
        rate = elapsed / max(1, index - 1) if index > 1 else 0.0
        eta = rate * (len(pending) - index + 1) / 3600 if rate else 0.0
        print(
            f"\n=== [{index}/{len(pending)}] chapter {number} {path.name}"
            + (f"  (eta {eta:.1f} h)" if eta else ""),
            flush=True,
        )

        command = [
            sys.executable,
            str(HERE / "render_chapter_fish.py"),
            str(path),
            "--output",
            str(wav),
            "--reference",
            args.reference,
            "--seed",
            str(args.seed),
        ]
        if not args.no_anchor:
            command.append("--anchor")
        if number in announcements:
            command += ["--announcement", str(announcements[number])]
        override = CHAPTER_OVERRIDES.get(number, {})
        if override.get("max_words_per_call"):
            command += ["--max-words-per-call", str(override["max_words_per_call"])]
        for replacement in override.get("spoken_replacements", ()):
            command += ["--spoken-replace", replacement]

        outcome = None
        for attempt in range(args.retries + 1):
            result = subprocess.run(
                command,
                cwd=HERE,
                capture_output=True,
                text=True,
            )
            tail = [
                line
                for line in result.stdout.splitlines()
                if line.startswith(("wrote", "  WER", "  articulation"))
            ]
            for line in tail:
                print("   ", line.strip(), flush=True)
            if result.returncode != 0:
                print(f"    render exit {result.returncode}", flush=True)
                snippet = (result.stderr or "").strip().splitlines()[-3:]
                for line in snippet:
                    print(f"    {line}", flush=True)

            override_patches = override.get("patches") or (
                [override["patch"]] if override.get("patch") else []
            )
            # Apply later-in-file patches first so earlier region times stay valid.
            for patch in sorted(override_patches, key=lambda p: -p["start"]):
                if result.returncode != 0 or not wav.is_file():
                    break
                patch_command = [
                    sys.executable,
                    str(HERE / "patch_verified_omission.py"),
                    str(wav),
                    str(patch["phrase"]),
                    "--output",
                    str(wav),
                    "--manifest",
                    str(wav.with_suffix(".manifest.json")),
                    "--chapter",
                    str(path),
                    "--announcement-text",
                    str(patch["announcement_text"]),
                    "--start",
                    str(patch["start"]),
                    "--end",
                    str(patch["end"]),
                    "--replace-unintelligible",
                ]
                if patch.get("allow_duration_change"):
                    patch_command.append("--allow-duration-change")
                patch_result = subprocess.run(
                    patch_command,
                    cwd=HERE,
                    capture_output=True,
                    text=True,
                )
                for line in patch_result.stdout.splitlines():
                    if line.startswith(("patched", "  samples", "  wrote")):
                        print(f"    {line.strip()}", flush=True)
                if patch_result.returncode != 0:
                    print(f"    patch exit {patch_result.returncode}", flush=True)
                    for line in (patch_result.stderr or "").strip().splitlines()[-3:]:
                        print(f"    {line}", flush=True)

            outcome = already_done(
                wav,
                chapter=path,
                announcement=announcements.get(number),
                reference=args.reference,
                seed=args.seed,
                anchored=not args.no_anchor,
                overrides=override,
            )
            if outcome:
                break
            if attempt < args.retries:
                print("    QA did not pass; retrying", flush=True)

        if not outcome:
            failures.append(number)
            report[str(number)] = {"chapter": number, "file": wav.name, "passed": False}
        else:
            assembly = outcome["assembly"]
            quality = assembly["chapter_quality"]
            report[str(number)] = {
                "chapter": number,
                "file": wav.name,
                "passed": True,
                "minutes": round(assembly["seconds"] / 60, 2),
                "wer": quality["wer"],
                "coverage": quality["coverage"],
                "articulation_first_third": assembly.get("articulation_first_third"),
                "articulation_last_third": assembly.get("articulation_last_third"),
                "suspicious_spans": quality.get("suspicious_spans", []),
            }
        report_path.write_text(json.dumps(report, indent=2))

    _summarise(report, args.out_dir, failures)


def _ranges(numbers: list[int]) -> str:
    numbers = sorted(numbers)
    out, start, previous = [], numbers[0], numbers[0]
    for n in numbers[1:]:
        if n == previous + 1:
            previous = n
            continue
        out.append(f"{start}" if start == previous else f"{start}-{previous}")
        start = previous = n
    out.append(f"{start}" if start == previous else f"{start}-{previous}")
    return ", ".join(out)


def _summarise(report: dict, out_dir: Path, failures: list[int]) -> None:
    passing = [r for r in report.values() if r.get("passed")]
    minutes = sum(r.get("minutes", 0.0) for r in passing)
    print(
        f"\n{len(passing)} chapters passing, {len(failures)} failed, "
        f"{minutes / 60:.1f} h of audio"
    )

    # Triage, ordered by how much attention each chapter probably needs.
    listen = []
    for r in passing:
        reasons = []
        first = r.get("articulation_first_third")
        last = r.get("articulation_last_third")
        if first and last and first > 0:
            drop = (first - last) / first
            if drop > 0.10:
                reasons.append(f"articulation -{drop * 100:.0f}% across chapter")
        if r.get("wer", 0) > 0.05:
            reasons.append(f"WER {r['wer']:.3f}")
        if r.get("coverage", 1.0) < 0.99:
            reasons.append(f"coverage {r['coverage']:.3f}")
        spans = r.get("suspicious_spans") or []
        if len(spans) > 4:
            reasons.append(f"{len(spans)} suspicious spans")
        if reasons:
            listen.append({"chapter": r["chapter"], "file": r["file"], "reasons": reasons})

    listen.sort(key=lambda x: -len(x["reasons"]))
    path = out_dir / "listen-list.json"
    path.write_text(
        json.dumps(
            {
                "note": "Triage only. Text metrics cannot see intra-word stutters; "
                "the acoustic judges are not built yet.",
                "failed_chapters": failures,
                "listen": listen,
            },
            indent=2,
        )
    )
    print(f"listen list: {len(listen)} chapters flagged -> {path}")
    if failures:
        print(f"FAILED (no passing render): {_ranges(failures)}")
    for item in listen[:10]:
        print(f"  ch {item['chapter']:3d}  {'; '.join(item['reasons'])}")


if __name__ == "__main__":
    main()
