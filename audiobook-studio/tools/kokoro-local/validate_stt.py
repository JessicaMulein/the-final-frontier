#!/usr/bin/env python3
"""Speech-to-text glitch detection for local Chatterbox chapter WAVs.

Transcribes each WAV with mlx-whisper, then compares against the manuscript
spoken text. Fails chapters on high WER, long insert spans (loops), or
suspicious content-word replacements (ignoring number/spelling noise).

Local tooling only — does not touch the Nova production path.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from dataclasses import asdict, dataclass
from difflib import SequenceMatcher
from pathlib import Path

import mlx_whisper

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / ".tools"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from check_novel import (  # noqa: E402
    discover_chapter_files,
    parse_chapter_filename,
    split_chapter_header,
)

TOKEN = re.compile(r"[^\W_]+(?:'[^\W_]+)*", re.UNICODE)
APOSTROPHES = str.maketrans({"’": "'", "‘": "'", "ʼ": "'", "＇": "'"})
EMPHASIS = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
WAV_CHAPTER_RE = re.compile(
    r"^(?P<seq>\d{3})-chapter-(?P<num>\d{3})-(?P<voice>.+)\.wav$",
    re.IGNORECASE,
)

_NUMBER_WORDS = {
    "zero": "0",
    "one": "1",
    "two": "2",
    "three": "3",
    "four": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "nine": "9",
    "ten": "10",
    "eleven": "11",
    "twelve": "12",
    "thirteen": "13",
    "fourteen": "14",
    "fifteen": "15",
    "sixteen": "16",
    "seventeen": "17",
    "eighteen": "18",
    "nineteen": "19",
    "twenty": "20",
    "thirty": "30",
    "forty": "40",
    "fifty": "50",
    "sixty": "60",
    "seventy": "70",
    "eighty": "80",
    "ninety": "90",
    "hundred": "100",
}


@dataclass(frozen=True)
class GlitchReport:
    chapter: int
    wav: str
    source: str
    passed: bool
    wer: float
    coverage_ratio: float
    expected_tokens: int
    transcript_tokens: int
    insert_ops: int
    delete_ops: int
    replace_ops: int
    suspicious_replaces: int
    first_difference: dict | None
    worst_insert: dict | None
    suspicious_examples: list
    transcript_preview: str


def spoken_from_markdown(body: str) -> str:
    text = EMPHASIS.sub(r"\1", body)
    text = text.replace("*", " ")
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text


def normalized_tokens(value: str) -> tuple[str, ...]:
    normalized = unicodedata.normalize("NFC", value).translate(APOSTROPHES).casefold()
    return tuple(TOKEN.findall(normalized))


def token_wer(expected: tuple[str, ...], actual: tuple[str, ...]) -> float:
    if not expected:
        return 0.0 if not actual else 1.0
    matcher = SequenceMatcher(a=expected, b=actual, autojunk=False)
    edits = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        if tag == "replace":
            edits += max(i2 - i1, j2 - j1)
        elif tag == "delete":
            edits += i2 - i1
        elif tag == "insert":
            edits += j2 - j1
    return edits / len(expected)


def _normalize_spelling(token: str) -> str:
    token = token.replace("'", "")
    pairs = (
        ("neighbour", "neighbor"),
        ("neighbours", "neighbors"),
        ("digitiser", "digitizer"),
        ("travelling", "traveling"),
        ("travelled", "traveled"),
        ("organised", "organized"),
        ("recognised", "recognized"),
    )
    for uk, us in pairs:
        if token in {uk, us}:
            return us
    return token


def _numberish(tokens: list[str]) -> str:
    if not tokens:
        return ""
    if all(t.isdigit() for t in tokens):
        return "".join(tokens)
    out: list[str] = []
    ordinals = {
        "first": "1",
        "second": "2",
        "third": "3",
        "fourth": "4",
        "fifth": "5",
        "sixth": "6",
        "seventh": "7",
        "eighth": "8",
        "ninth": "9",
        "tenth": "10",
        "eleventh": "11",
        "twelfth": "12",
    }
    for t in tokens:
        if t in ordinals:
            out.append(ordinals[t])
        elif t.endswith(("st", "nd", "rd", "th")) and t[:-2].isdigit():
            out.append(t[:-2])
        elif t.endswith(("st", "nd", "rd", "th")) and t[:-2] in _NUMBER_WORDS:
            out.append(_NUMBER_WORDS[t[:-2]])
        elif t in _NUMBER_WORDS:
            out.append(_NUMBER_WORDS[t])
        elif t in {"point", "oh"}:
            continue
        elif t.isdigit():
            out.append(t)
        else:
            return ""
    return "".join(out)


def is_benign_replace(expected: list[str], actual: list[str]) -> bool:
    if not expected and not actual:
        return True
    e_num = _numberish(expected)
    a_num = _numberish(actual)
    if e_num and a_num and e_num == a_num:
        return True
    if len(expected) == 1 and len(actual) == 1:
        e = _normalize_spelling(expected[0])
        a = _normalize_spelling(actual[0])
        if e == a:
            return True
        # Weak function-word flips are usually ASR, not audible TTS failure.
        weak = {
            "a",
            "an",
            "the",
            "and",
            "in",
            "on",
            "at",
            "as",
            "to",
            "of",
            "i",
            "it",
            "that",
            "this",
            "than",
            "then",
            "with",
            "for",
            "from",
            "by",
            "or",
            "but",
        }
        if e in weak and a in weak:
            return True
        # Tense / plural micro-flips Whisper often invents.
        if e.rstrip("ds") == a.rstrip("ds") and min(len(e), len(a)) >= 4:
            return True
    # Spoken number phrases vs digits ("hundred and nine" ↔ "109").
    e_num2 = _numberish([t for t in expected if t not in {"and", "a", "the"}])
    a_num2 = _numberish([t for t in actual if t not in {"and", "a", "the"}])
    if e_num2 and a_num2 and e_num2 == a_num2:
        return True
    e_join = "".join(expected).replace("-", "")
    a_join = "".join(actual).replace("-", "")
    if e_join and e_join == a_join:
        return True
    return False


def analyze_opcodes(
    expected: tuple[str, ...], actual: tuple[str, ...]
) -> tuple[dict | None, dict | None, int, int, int, list[dict]]:
    matcher = SequenceMatcher(a=expected, b=actual, autojunk=False)
    first = None
    worst_insert = None
    inserts = deletes = replaces = 0
    suspicious: list[dict] = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            continue
        op = {
            "operation": tag,
            "expected_range": [i1, i2],
            "transcript_range": [j1, j2],
            "expected": list(expected[i1:i2]),
            "transcript": list(actual[j1:j2]),
            "expected_context": list(expected[max(0, i1 - 6) : i2 + 6]),
            "transcript_context": list(actual[max(0, j1 - 6) : j2 + 6]),
        }
        if first is None:
            first = op
        if tag == "insert":
            inserts += 1
            if worst_insert is None or (j2 - j1) > len(worst_insert["transcript"]):
                worst_insert = op
        elif tag == "delete":
            deletes += 1
        elif tag == "replace":
            replaces += 1
            if not is_benign_replace(op["expected"], op["transcript"]):
                suspicious.append(
                    {
                        "expected": op["expected"],
                        "transcript": op["transcript"],
                        "expected_context": op["expected_context"],
                        "transcript_context": op["transcript_context"],
                    }
                )
    return first, worst_insert, inserts, deletes, replaces, suspicious


def expected_text_for_chapter(manuscript_root: Path, chapter_num: int) -> tuple[str, Path]:
    for path in discover_chapter_files(manuscript_root):
        parsed = parse_chapter_filename(path.name)
        if parsed is None:
            continue
        if parsed.sequence == chapter_num:
            _header, body = split_chapter_header(
                path.read_text(encoding="utf-8"),
                item=str(path),
            )
            return spoken_from_markdown(body), path
    raise SystemExit(f"No manuscript chapter {chapter_num:03d} under {manuscript_root}")


def transcribe(wav: Path, *, model: str, language: str) -> str:
    result = mlx_whisper.transcribe(
        str(wav),
        path_or_hf_repo=model,
        language=language,
        word_timestamps=False,
        verbose=False,
        # Whisper's default context conditioning makes it hallucinate runaway
        # repetition on long narration, which this gate then blames on the
        # render. Measured on chapter 12: context on gave 1189 words including
        # 130 tokens of 'and that s what i did not have to do' repeated 13x;
        # context off gave 1051 words against a manuscript of 1049, clean.
        # Never re-enable without re-checking the false-failure rate.
        condition_on_previous_text=False,
    )
    text = (result.get("text") or "").strip()
    if not text:
        raise RuntimeError(f"Empty transcript for {wav}")
    return text


def validate_one(
    wav: Path,
    *,
    manuscript_root: Path,
    model: str,
    language: str,
    wer_fail: float,
    insert_fail: int,
    suspicious_fail: int,
    transcript: str | None = None,
) -> GlitchReport:
    """Gate one chapter WAV against the manuscript.

    `transcript` lets a caller supply an already-computed transcript so a
    chapter is only passed through whisper once when several gates need it.
    """
    match = WAV_CHAPTER_RE.match(wav.name)
    if not match:
        raise SystemExit(f"Unrecognized chapter WAV name: {wav.name}")
    chapter_num = int(match.group("num"))
    expected_raw, source = expected_text_for_chapter(manuscript_root, chapter_num)
    if transcript is None:
        transcript = transcribe(wav, model=model, language=language)
    expected_toks = normalized_tokens(expected_raw)
    actual_toks = normalized_tokens(transcript)
    wer = token_wer(expected_toks, actual_toks)
    first, worst_insert, inserts, deletes, replaces, suspicious = analyze_opcodes(
        expected_toks, actual_toks
    )
    coverage = round(len(actual_toks) / len(expected_toks), 4) if expected_toks else 0.0
    worst_insert_len = len(worst_insert["transcript"]) if worst_insert else 0
    passed = (
        wer <= wer_fail
        and worst_insert_len < insert_fail
        and len(suspicious) < suspicious_fail
    )
    return GlitchReport(
        chapter=chapter_num,
        wav=str(wav),
        source=str(source),
        passed=passed,
        wer=round(wer, 4),
        coverage_ratio=coverage,
        expected_tokens=len(expected_toks),
        transcript_tokens=len(actual_toks),
        insert_ops=inserts,
        delete_ops=deletes,
        replace_ops=replaces,
        suspicious_replaces=len(suspicious),
        first_difference=first,
        worst_insert=worst_insert,
        suspicious_examples=suspicious[:12],
        transcript_preview=transcript[:280],
    )


def discover_wavs(audio_dir: Path, voice_tag: str, chapters: list[int] | None) -> list[Path]:
    wavs: list[Path] = []
    for path in sorted(audio_dir.glob(f"*-chapter-*-{voice_tag}.wav")):
        match = WAV_CHAPTER_RE.match(path.name)
        if not match:
            continue
        num = int(match.group("num"))
        if chapters is not None and num not in chapters:
            continue
        wavs.append(path)
    return wavs


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio-dir", type=Path, default=REPO_ROOT / "audiobook")
    parser.add_argument(
        "--manuscript-root",
        type=Path,
        default=REPO_ROOT / "The Final Frontier Novel",
    )
    parser.add_argument("--voice-tag", default="chatterbox-uk-s03")
    parser.add_argument("--chapter", type=int, action="append", default=None)
    parser.add_argument("--model", default="mlx-community/whisper-large-v3-turbo")
    parser.add_argument("--language", default="en")
    parser.add_argument("--wer-fail", type=float, default=0.12)
    parser.add_argument("--insert-fail", type=int, default=12)
    parser.add_argument(
        "--suspicious-fail",
        type=int,
        default=15,
        help="Fail when suspicious content-word replaces reach this count",
    )
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args()

    wavs = discover_wavs(args.audio_dir, args.voice_tag, args.chapter)
    if not wavs:
        raise SystemExit("No chapter WAVs matched")

    reports: list[GlitchReport] = []
    failures = 0
    for wav in wavs:
        print(f"=== chapter WAV {wav.name}", flush=True)
        report = validate_one(
            wav,
            manuscript_root=args.manuscript_root,
            model=args.model,
            language=args.language,
            wer_fail=args.wer_fail,
            insert_fail=args.insert_fail,
            suspicious_fail=args.suspicious_fail,
        )
        reports.append(report)
        status = "PASS" if report.passed else "FAIL"
        if not report.passed:
            failures += 1
        print(
            f"  {status} wer={report.wer:.3f} coverage={report.coverage_ratio:.3f} "
            f"ins={report.insert_ops} del={report.delete_ops} repl={report.replace_ops} "
            f"suspicious={report.suspicious_replaces}",
            flush=True,
        )
        for ex in report.suspicious_examples[:5]:
            print(f"  ~ {ex['expected']!r} → {ex['transcript']!r}", flush=True)

    report_path = args.report or (
        REPO_ROOT / "audiobook/kokoro-audition/chatterbox-v2/stt-glitch-report.json"
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "model": args.model,
        "voice_tag": args.voice_tag,
        "wer_fail": args.wer_fail,
        "insert_fail": args.insert_fail,
        "suspicious_fail": args.suspicious_fail,
        "failure_count": failures,
        "chapters": [asdict(r) for r in reports],
    }
    report_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {report_path} ({failures} failure(s) / {len(reports)} checked)")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
