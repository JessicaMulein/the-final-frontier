"""Segmented chapter narration.

Amazon Nova 2 Sonic reliably narrates only a short passage per turn, so a chapter
is split into small verbatim segments, rendered one at a time, verified against
the source, and concatenated. Every rendered segment is journalled so an
interrupted run resumes without paying for the same segment twice.
"""

from __future__ import annotations

import io
import re
import wave
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import json

from .audition import fidelity_accepted
from .config import AuditionConfig
from .errors import FidelityMismatch, InputError
from .manuscript import ChapterSource, discover_chapter, markdown_to_spoken, read_chapter
from .nova import render_text, replay_output_events
from .util import (
    atomic_write_bytes,
    atomic_write_json,
    atomic_write_text,
    read_bytes_nofollow,
    read_json,
    resolve_inside,
    sha256_bytes,
    sha256_text,
    utc_now,
    workspace_relative,
)
from .verify import compare_transcript, normalized_tokens

MAX_SEGMENT_WORDS = 35
NOVA_SAFE_MAX_CHARACTERS = 180
NOVA_SAFE_MAX_WORDS = 32
SEGMENT_GAP_SECONDS = 0.28
PARAGRAPH_GAP_SECONDS = 0.62

SENTENCE_BOUNDARY = re.compile(r'(?<=[.!?])["\u201d\u2019\')\]]*\s+')
SEGMENT_BOUNDARY_POLICY = "safe-narration-punctuation-v3"


@dataclass(frozen=True)
class Segment:
    index: int
    paragraph_index: int
    text: str
    narration_only_punctuation: bool = False

    @property
    def segment_id(self) -> str:
        return f"{self.index:04d}"

    @property
    def word_count(self) -> int:
        return len(normalized_tokens(self.text))


def _fits_safe_turn(text: str) -> bool:
    return (
        len(text) <= NOVA_SAFE_MAX_CHARACTERS
        and len(normalized_tokens(text)) <= NOVA_SAFE_MAX_WORDS
    )


def _narration_sentence_fragment(source: str, *, final: bool) -> str:
    text = source.strip()
    if not final:
        text = re.sub(r"[,;:]$", ".", text)
        if not text.endswith((".", "!", "?")):
            text += "."
    for index, character in enumerate(text):
        if character.isalpha():
            return text[:index] + character.upper() + text[index + 1 :]
    return text


def _split_for_narration(
    sentence: str,
    paragraph_index: int,
    sentence_index: int,
) -> tuple[str, ...]:
    """Add narration-only sentence punctuation while preserving every word."""

    def solve(boundaries: list[int]) -> tuple[str, ...] | None:
        positions = sorted({0, *boundaries, len(sentence)})
        memo: dict[int, tuple[str, ...] | None] = {}

        def visit(position_index: int) -> tuple[str, ...] | None:
            if position_index == len(positions) - 1:
                return ()
            if position_index in memo:
                return memo[position_index]
            best: tuple[str, ...] | None = None
            for next_index in range(len(positions) - 1, position_index, -1):
                fragment = _narration_sentence_fragment(
                    sentence[positions[position_index] : positions[next_index]],
                    final=next_index == len(positions) - 1,
                )
                if not _fits_safe_turn(fragment):
                    continue
                remainder = visit(next_index)
                if remainder is None:
                    continue
                candidate = (fragment, *remainder)
                if best is None or len(candidate) < len(best):
                    best = candidate
            memo[position_index] = best
            return best

        return visit(0)

    comma_boundaries = [match.start() + 1 for match in re.finditer(r",\s+", sentence)]
    result = solve(comma_boundaries)
    if result is None:
        conjunction_boundaries = [
            match.start()
            for match in re.finditer(
                r"\s+(?=(?:and|but|with|because|while|when)\s)",
                sentence,
                flags=re.IGNORECASE,
            )
        ]
        result = solve([*comma_boundaries, *conjunction_boundaries])
    if result is None:
        raise InputError(
            "Narration sentence cannot be partitioned into safe turns using approved "
            f"punctuation at paragraph {paragraph_index + 1}, sentence {sentence_index + 1}: "
            f"characters={len(sentence)}, words={len(normalized_tokens(sentence))}. "
            "Split the sentence in the manuscript or use a synthesizer without turn boundaries."
        )
    actual = tuple(token for fragment in result for token in normalized_tokens(fragment))
    if actual != normalized_tokens(sentence):
        raise InputError("Narration-only punctuation changed the sentence word sequence")
    return result


def _pack(pieces: list[str], target_words: int) -> list[str]:
    """Pack safe sentences while preserving established paragraph grouping."""

    packed: list[str] = []
    current: list[str] = []
    current_words = 0
    for piece in pieces:
        words = len(normalized_tokens(piece))
        if current and current_words + words > target_words:
            packed.append(" ".join(current))
            current = []
            current_words = 0
        current.append(piece)
        current_words += words
    if current:
        packed.append(" ".join(current))
    return packed


def segment_spoken_text(spoken: str, max_words: int = MAX_SEGMENT_WORDS) -> tuple[Segment, ...]:
    """Pack safe source sentences, adding approved narration-only punctuation as needed."""

    if max_words < 5:
        raise InputError("Narration segments must target at least five words")
    paragraphs = [block.strip() for block in re.split(r"\n\s*\n", spoken) if block.strip()]
    if not paragraphs:
        raise InputError("Chapter has no narratable paragraphs")

    segments: list[Segment] = []
    for paragraph_index, paragraph in enumerate(paragraphs):
        collapsed = " ".join(paragraph.split())
        sentences = [item.strip() for item in SENTENCE_BOUNDARY.split(collapsed) if item.strip()]
        pending: list[str] = []

        def flush_pending() -> None:
            for text in _pack(pending, max_words):
                segments.append(Segment(len(segments) + 1, paragraph_index, text))
            pending.clear()

        for sentence_index, sentence in enumerate(sentences):
            if _fits_safe_turn(sentence):
                pending.append(sentence)
                continue
            flush_pending()
            for fragment in _split_for_narration(sentence, paragraph_index, sentence_index):
                if not _fits_safe_turn(fragment):
                    raise InputError("Narration punctuation override produced an unsafe Nova turn")
                segments.append(
                    Segment(
                        len(segments) + 1,
                        paragraph_index,
                        fragment,
                        narration_only_punctuation=True,
                    )
                )
        flush_pending()

    expected = normalized_tokens(spoken)
    actual = tuple(token for segment in segments for token in normalized_tokens(segment.text))
    if expected != actual:
        raise InputError("Segmentation changed the chapter word sequence")
    return tuple(segments)


def chapter_spoken_text(config: AuditionConfig, chapter: int) -> tuple[ChapterSource, str]:
    """Read a chapter for narration.

    The declared header word count is metadata that goes stale while drafting, and
    it does not affect what is narrated, so narration does not enforce it. The
    audition path stays strict.
    """

    source = read_chapter(
        discover_chapter(config.manuscript_root, chapter),
        enforce_declared_words=False,
    )
    return source, markdown_to_spoken(source.body, f"chapter-{chapter:03d}")


def _narration_root(config: AuditionConfig, chapter: int, voice_id: str) -> Path:
    return resolve_inside(
        config.output_root.parent / "narration",
        f"chapter-{chapter:03d}-{voice_id}",
    )


def _segment_paths(root: Path, segment: Segment) -> dict[str, Path]:
    """Return immutable content-addressed paths for a newly rendered segment."""

    stem = f"{segment.segment_id}-{sha256_text(segment.text)}"
    return {
        "audio": resolve_inside(root, f"segments/{stem}.wav"),
        "events": resolve_inside(root, f"events/{stem}.jsonl"),
        "transcript": resolve_inside(root, f"transcripts/{stem}.txt"),
    }


def _wav_bytes(lpcm: bytes, config: AuditionConfig) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(config.nova.channels)
        handle.setsampwidth(config.nova.sample_size_bits // 8)
        handle.setframerate(config.nova.sample_rate_hz)
        handle.writeframes(lpcm)
    return buffer.getvalue()


def _lpcm_from_wav(path: Path, config: AuditionConfig) -> bytes:
    with wave.open(io.BytesIO(read_bytes_nofollow(path)), "rb") as handle:
        if (
            handle.getframerate(),
            handle.getsampwidth() * 8,
            handle.getnchannels(),
        ) != (config.nova.sample_rate_hz, config.nova.sample_size_bits, config.nova.channels):
            raise InputError(f"Segment WAV format mismatch: {path}")
        return handle.readframes(handle.getnframes())


def _silence(seconds: float, config: AuditionConfig) -> bytes:
    frames = int(round(seconds * config.nova.sample_rate_hz))
    return bytes(frames * config.nova.channels * (config.nova.sample_size_bits // 8))


SILENCE_WINDOW_SECONDS = 0.01
SILENCE_RMS_THRESHOLD = 100.0
EDGE_SILENCE_SECONDS = 0.02
EDGE_FADE_SECONDS = 0.002
CONTINUATION_GAP_SECONDS = 0.08
PARTIAL_TURN_CROSSFADE_SECONDS = 0.012
PARTIAL_TURN_POLICY = "crossfade-mid-sentence-v1"
STITCH_PROFILE = "sentence-boundary-partial-turn-v3"


def _event_path_for_audio(audio_path: Path) -> Path | None:
    candidate = audio_path.parent.parent / "events" / f"{audio_path.stem}.jsonl"
    return candidate if candidate.is_file() else None


def _event_audio_blocks(
    events_path: Path,
    expected_lpcm: bytes,
) -> tuple[tuple[bytes, bool], ...]:
    """Recover audio blocks and mark only non-semantic PARTIAL_TURN joins."""

    import base64

    try:
        lines = read_bytes_nofollow(events_path).decode("utf-8").splitlines()
        events = [json.loads(line) for line in lines if line]
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise InputError(f"Malformed narration event log {events_path}: {exc}") from exc
    replayed = replay_output_events(events)
    if replayed.audio_lpcm != expected_lpcm:
        raise InputError(f"Narration event audio does not match segment WAV: {events_path}")

    contexts: dict[str, tuple[str, str, int]] = {}
    text_parts: dict[str, list[str]] = {}
    audio_parts: dict[str, list[bytes]] = {}
    blocks: list[tuple[bytes, str, str]] = []
    for index, event in enumerate(events):
        if "contentStart" in event:
            content = event["contentStart"]
            content_id = content["contentId"]
            additional = content.get("additionalModelFields", "")
            contexts[content_id] = (content.get("type", ""), additional, index)
            text_parts[content_id] = []
            audio_parts[content_id] = []
        elif "textOutput" in event:
            content = event["textOutput"]
            text_parts[content["contentId"]].append(content["content"])
        elif "audioOutput" in event:
            content = event["audioOutput"]
            audio_parts[content["contentId"]].append(
                base64.b64decode(content["content"], validate=True)
            )
        elif "contentEnd" in event and event["contentEnd"].get("type") == "AUDIO":
            content = event["contentEnd"]
            content_id = content["contentId"]
            audio_start = contexts[content_id][2]
            preceding_speculative = [
                (start, "".join(text_parts[candidate_id]))
                for candidate_id, (content_type, additional, start) in contexts.items()
                if content_type == "TEXT"
                and "SPECULATIVE" in additional
                and start < audio_start
            ]
            speculative = max(preceding_speculative, default=(-1, ""))[1]
            blocks.append(
                (
                    b"".join(audio_parts[content_id]),
                    content.get("stopReason", ""),
                    speculative,
                )
            )

    if b"".join(block[0] for block in blocks) != expected_lpcm:
        raise InputError(f"Narration event block order does not match segment WAV: {events_path}")
    result: list[tuple[bytes, bool]] = []
    for index, (audio, stop_reason, speculative) in enumerate(blocks):
        ends_sentence = bool(
            re.search(r"[.!?][\"\u201d\u2019')\]]*\s*$", speculative)
        )
        repair_after = (
            index < len(blocks) - 1
            and stop_reason == "PARTIAL_TURN"
            and bool(speculative.strip())
            and not ends_sentence
        )
        result.append((audio, repair_after))
    return tuple(result)


def _crossfade_partial_turns(
    blocks: tuple[tuple[bytes, bool], ...],
    config: AuditionConfig,
) -> bytes:
    """Remove internal turn padding and blend speech only at mid-sentence joins."""

    from array import array
    import math
    import sys

    if not blocks:
        raise InputError("Narration event log contains no audio blocks")

    def samples_from_bytes(value: bytes) -> array:
        samples = array("h")
        samples.frombytes(value)
        if sys.byteorder != "little":
            samples.byteswap()
        return samples

    def active_bounds(samples: array) -> tuple[int, int]:
        window = max(1, int(round(SILENCE_WINDOW_SECONDS * config.nova.sample_rate_hz)))
        active: list[int] = []
        for index, start in enumerate(range(0, len(samples), window)):
            block = samples[start : start + window]
            rms = math.sqrt(sum(value * value for value in block) / len(block))
            if rms >= SILENCE_RMS_THRESHOLD:
                active.append(index)
        if not active:
            raise InputError("PARTIAL_TURN audio block contains no audible speech")
        return active[0] * window, min(len(samples), (active[-1] + 1) * window)

    result = samples_from_bytes(blocks[0][0])
    for index, (raw, _) in enumerate(blocks[1:], start=1):
        following = samples_from_bytes(raw)
        if blocks[index - 1][1]:
            _, left_end = active_bounds(result)
            right_start, _ = active_bounds(following)
            result = result[:left_end]
            following = following[right_start:]
            overlap = min(
                int(round(PARTIAL_TURN_CROSSFADE_SECONDS * config.nova.sample_rate_hz)),
                len(result),
                len(following),
            )
            if overlap > 1:
                mixed = array("h")
                for offset in range(overlap):
                    right_weight = (offset + 1) / (overlap + 1)
                    mixed.append(
                        round(
                            result[-overlap + offset] * (1.0 - right_weight)
                            + following[offset] * right_weight
                        )
                    )
                result[-overlap:] = mixed
                result.extend(following[overlap:])
            else:
                result.extend(following)
        else:
            result.extend(following)

    if sys.byteorder != "little":
        result.byteswap()
    return result.tobytes()


def _smooth_clip_lpcm(
    lpcm: bytes,
    config: AuditionConfig,
    events_path: Path | None = None,
) -> bytes:
    """Repair internal turn seams, trim edge silence, and suppress edge clicks."""

    from array import array
    import math
    import sys

    if (config.nova.sample_size_bits, config.nova.channels) != (16, 1):
        raise InputError("Smooth stitching requires signed 16-bit mono segment audio")
    if not lpcm or len(lpcm) % 2:
        raise InputError("Segment LPCM is empty or not aligned to 16-bit samples")
    if events_path is not None:
        blocks = _event_audio_blocks(events_path, lpcm)
        if any(repair_after for _, repair_after in blocks):
            lpcm = _crossfade_partial_turns(blocks, config)

    samples = array("h")
    samples.frombytes(lpcm)
    if sys.byteorder != "little":
        samples.byteswap()

    window = max(1, int(round(SILENCE_WINDOW_SECONDS * config.nova.sample_rate_hz)))
    active_windows: list[int] = []
    for index, start in enumerate(range(0, len(samples), window)):
        block = samples[start : start + window]
        rms = math.sqrt(sum(value * value for value in block) / len(block))
        if rms >= SILENCE_RMS_THRESHOLD:
            active_windows.append(index)
    if not active_windows:
        raise InputError("Segment audio contains no audible speech")

    pad = int(round(EDGE_SILENCE_SECONDS * config.nova.sample_rate_hz))
    start = max(0, active_windows[0] * window - pad)
    end = min(len(samples), (active_windows[-1] + 1) * window + pad)
    smoothed = samples[start:end]

    fade = min(
        int(round(EDGE_FADE_SECONDS * config.nova.sample_rate_hz)),
        len(smoothed) // 2,
    )
    if fade > 1:
        for offset in range(fade):
            gain = offset / (fade - 1)
            smoothed[offset] = round(smoothed[offset] * gain)
            smoothed[-(offset + 1)] = round(smoothed[-(offset + 1)] * gain)

    if sys.byteorder != "little":
        smoothed.byteswap()
    return smoothed.tobytes()


def _gap_between(previous: Segment, current: Segment) -> float:
    if previous.paragraph_index != current.paragraph_index:
        return PARAGRAPH_GAP_SECONDS
    if re.search(r"[.!?][\"\u201d\u2019')\]]*$", previous.text.rstrip()):
        return SEGMENT_GAP_SECONDS
    return CONTINUATION_GAP_SECONDS


def _narration_snapshot(
    config: AuditionConfig,
    chapter: int,
    voice_id: str,
    max_words: int,
) -> tuple[dict[str, Any], tuple[Segment, ...]]:
    """Build the outline and segments from one immutable source read."""

    source, spoken = chapter_spoken_text(config, chapter)
    segments = segment_spoken_text(spoken, max_words)
    outline = {
        "chapter": chapter,
        "voice_id": voice_id,
        "chapter_path": workspace_relative(config.workspace_root, source.path),
        "source_sha256": source.body_sha256,
        "spoken_sha256": sha256_text(spoken),
        "word_count": len(normalized_tokens(spoken)),
        "segment_count": len(segments),
        "narration_only_punctuation_segments": sum(
            segment.narration_only_punctuation for segment in segments
        ),
        "target_segment_words": max_words,
        "safe_request_max_characters": NOVA_SAFE_MAX_CHARACTERS,
        "safe_request_max_words": NOVA_SAFE_MAX_WORDS,
        "segment_boundary_policy": SEGMENT_BOUNDARY_POLICY,
        "segments": [
            {
                "segment_id": segment.segment_id,
                "paragraph_index": segment.paragraph_index,
                "word_count": segment.word_count,
                "text": segment.text,
                "narration_only_punctuation": segment.narration_only_punctuation,
            }
            for segment in segments
        ],
    }
    return outline, segments


def plan_narration(
    config: AuditionConfig,
    chapter: int,
    voice_id: str,
    max_words: int = MAX_SEGMENT_WORDS,
) -> dict[str, Any]:
    outline, _ = _narration_snapshot(config, chapter, voice_id, max_words)
    return outline


def _load_manifest(path: Path) -> dict[str, Any]:
    if not path.is_file():
        return {}
    manifest = read_json(path)
    if not isinstance(manifest, dict):
        raise InputError(f"Narration manifest is malformed: {path}")
    return manifest


def _manifest_candidates(
    manifest: dict[str, Any],
) -> tuple[dict[str, list[dict[str, Any]]], list[dict[str, Any]]]:
    """Index every historical candidate, preferring active entries over carried ones."""

    by_text: dict[str, list[dict[str, Any]]] = {}
    history: list[dict[str, Any]] = []
    for bucket_name in ("segments", "carried_over_segments"):
        bucket = manifest.get(bucket_name)
        if not isinstance(bucket, list):
            continue
        for raw in bucket:
            if not isinstance(raw, dict) or not isinstance(raw.get("text_sha256"), str):
                continue
            item = dict(raw)
            history.append(item)
            by_text.setdefault(item["text_sha256"], []).append(item)
    return by_text, history


def _entry_audio_path(config: AuditionConfig, entry: dict[str, Any]) -> Path | None:
    value = entry.get("audio_path")
    if not isinstance(value, str) or not value:
        return None
    try:
        return resolve_inside(config.workspace_root, value)
    except InputError:
        return None


def _normalized_reusable_entry(
    entry: Any,
    segment: Segment,
    config: AuditionConfig,
    accept_verbatim_prefix: bool,
) -> dict[str, Any] | None:
    """Return a current, accepted entry for an intact previously paid render."""

    if not isinstance(entry, dict) or entry.get("text_sha256") != sha256_text(segment.text):
        return None
    if entry.get("mid_sentence_partial_turns", 0):
        return None
    try:
        audio_path = _entry_audio_path(config, entry)
        if audio_path is None or not audio_path.is_file():
            return None
        audio = read_bytes_nofollow(audio_path)
        if sha256_bytes(audio) != entry.get("audio_sha256"):
            return None
        transcript_value = entry.get("transcript")
        if not isinstance(transcript_value, str):
            sibling = audio_path.parent.parent / "transcripts" / f"{audio_path.stem}.txt"
            if not sibling.is_file():
                return None
            transcript_value = read_bytes_nofollow(sibling).decode("utf-8").removesuffix("\n")
        verification = compare_transcript(segment.text, transcript_value, config.normalization)
        lpcm = _lpcm_from_wav(audio_path, config)
    except (InputError, UnicodeError, OSError, EOFError, wave.Error):
        return None

    duration = round(
        len(lpcm)
        / (config.nova.sample_rate_hz * config.nova.channels * (config.nova.sample_size_bits // 8)),
        3,
    )
    if not fidelity_accepted(
        verification,
        duration,
        accept_verbatim_prefix=accept_verbatim_prefix,
    ):
        return None
    return {
        **entry,
        "segment_id": segment.segment_id,
        "paragraph_index": segment.paragraph_index,
        "text": segment.text,
        "text_sha256": sha256_text(segment.text),
        "word_count": segment.word_count,
        "narration_only_punctuation": segment.narration_only_punctuation,
        "status": "narrated",
        "audio_path": workspace_relative(config.workspace_root, audio_path),
        "audio_sha256": sha256_bytes(audio),
        "duration_seconds": duration,
        "transcript": transcript_value,
        "exact_transcript_match": verification.passed,
        "coverage_ratio": verification.coverage_ratio,
    }


def _carried_over_entries(
    history: list[dict[str, Any]],
    current: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Retain distinct historical artifacts not selected for the current snapshot."""

    current_paths = {
        item.get("audio_path") for item in current if isinstance(item.get("audio_path"), str)
    }
    current_keys = {
        (item.get("text_sha256"), item.get("audio_path"), item.get("audio_sha256"))
        for item in current
    }
    carried: list[dict[str, Any]] = []
    seen: set[tuple[Any, Any, Any]] = set()
    for item in history:
        key = (item.get("text_sha256"), item.get("audio_path"), item.get("audio_sha256"))
        if key in current_keys or key in seen or item.get("audio_path") in current_paths:
            continue
        seen.add(key)
        carried.append(item)
    return carried


def _assert_chapter_unchanged(
    config: AuditionConfig,
    chapter: int,
    expected_spoken_sha256: str,
) -> None:
    """Fail before a billable call or stitch if the spoken source moved mid-run."""

    _, spoken = chapter_spoken_text(config, chapter)
    if sha256_text(spoken) != expected_spoken_sha256:
        raise InputError(
            f"Chapter {chapter} spoken text changed during narration; "
            "stopped before another paid render or final stitch"
        )


def narrate_chapter(
    config: AuditionConfig,
    chapter: int,
    voice_id: str,
    *,
    paid_render_authorized: bool = False,
    accept_verbatim_prefix: bool = False,
    max_words: int = MAX_SEGMENT_WORDS,
    progress: Any = None,
) -> dict[str, Any]:
    if not paid_render_authorized:
        raise InputError("Refusing billable narration without explicit paid-render authorization")
    if voice_id not in config.voices:
        raise InputError(f"Voice {voice_id!r} is not one of the configured voices")

    outline, segments = _narration_snapshot(config, chapter, voice_id, max_words)
    baseline_spoken_sha256 = outline["spoken_sha256"]
    root = _narration_root(config, chapter, voice_id)
    manifest_path = resolve_inside(root, "manifest.json")
    manifest = _load_manifest(manifest_path)
    source_changed = bool(manifest) and manifest.get("spoken_sha256") not in (
        None,
        baseline_spoken_sha256,
    )
    candidates_by_text, history = _manifest_candidates(manifest)

    entries: dict[str, dict[str, Any]] = {}
    rendered = 0
    reused = 0
    for segment in segments:
        text_sha256 = sha256_text(segment.text)
        accepted_entry = None
        for candidate in candidates_by_text.get(text_sha256, []):
            accepted_entry = _normalized_reusable_entry(
                candidate,
                segment,
                config,
                accept_verbatim_prefix,
            )
            if accepted_entry is not None:
                break
        if accepted_entry is not None:
            reused += 1
            entries[segment.segment_id] = accepted_entry
            if progress is not None:
                progress(segment, "reused", accepted_entry)
            continue

        _assert_chapter_unchanged(config, chapter, baseline_spoken_sha256)
        paths = _segment_paths(root, segment)
        result = render_text(
            segment.text,
            voice_id,
            config.nova,
            paid_render_authorized=True,
        )
        verification = compare_transcript(segment.text, result.final_transcript, config.normalization)
        audio = _wav_bytes(result.audio_lpcm, config)
        duration = round(
            len(result.audio_lpcm)
            / (config.nova.sample_rate_hz * config.nova.channels * (config.nova.sample_size_bits // 8)),
            3,
        )
        atomic_write_bytes(paths["audio"], audio)
        atomic_write_text(paths["transcript"], result.final_transcript + "\n")
        atomic_write_text(
            paths["events"],
            "".join(
                json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"
                for event in result.events
            ),
        )
        fidelity_passed = fidelity_accepted(
            verification,
            duration,
            accept_verbatim_prefix=accept_verbatim_prefix,
        )
        mid_sentence_partial_turns = 0
        if result.events:
            rendered_blocks = _event_audio_blocks(paths["events"], result.audio_lpcm)
            mid_sentence_partial_turns = sum(
                repair_after for _, repair_after in rendered_blocks
            )
        accepted = fidelity_passed and mid_sentence_partial_turns == 0
        status = (
            "mid_sentence_partial_turn"
            if mid_sentence_partial_turns
            else "narrated" if fidelity_passed else "fidelity_mismatch"
        )
        entries[segment.segment_id] = {
            "segment_id": segment.segment_id,
            "paragraph_index": segment.paragraph_index,
            "text": segment.text,
            "text_sha256": text_sha256,
            "word_count": segment.word_count,
            "narration_only_punctuation": segment.narration_only_punctuation,
            "status": status,
            "audio_path": workspace_relative(config.workspace_root, paths["audio"]),
            "audio_sha256": sha256_bytes(audio),
            "duration_seconds": duration,
            "transcript": result.final_transcript,
            "exact_transcript_match": verification.passed,
            "coverage_ratio": verification.coverage_ratio,
            "mid_sentence_partial_turns": mid_sentence_partial_turns,
            "narrated_at": utc_now(),
        }
        retained = [entries[item.segment_id] for item in segments if item.segment_id in entries]
        manifest = {
            **outline,
            "segments": retained,
            "carried_over_segments": _carried_over_entries(history, retained),
            "updated_at": utc_now(),
        }
        atomic_write_json(manifest_path, manifest)
        rendered += 1
        if progress is not None:
            progress(segment, status, entries[segment.segment_id])
        if mid_sentence_partial_turns:
            raise FidelityMismatch(
                f"Segment {segment.segment_id} of chapter {chapter} crossed a mid-sentence "
                f"Nova PARTIAL_TURN; narration stopped. Review {manifest_path}"
            )
        if not fidelity_passed:
            raise FidelityMismatch(
                f"Segment {segment.segment_id} of chapter {chapter} did not pass fidelity; "
                f"narration stopped. Review {manifest_path}"
            )

    _assert_chapter_unchanged(config, chapter, baseline_spoken_sha256)
    chapter_lpcm = bytearray()
    previous_segment: Segment | None = None
    for segment in segments:
        if previous_segment is not None:
            chapter_lpcm.extend(_silence(_gap_between(previous_segment, segment), config))
        entry = entries[segment.segment_id]
        audio_path = _entry_audio_path(config, entry)
        if audio_path is None:
            raise InputError(f"Segment {segment.segment_id} has no recorded audio path")
        audio = read_bytes_nofollow(audio_path)
        if sha256_bytes(audio) != entry.get("audio_sha256"):
            raise InputError(f"Segment {segment.segment_id} audio changed before stitching")
        chapter_lpcm.extend(
            _smooth_clip_lpcm(
                _lpcm_from_wav(audio_path, config),
                config,
                _event_path_for_audio(audio_path),
            )
        )
        previous_segment = segment

    chapter_path = resolve_inside(root, f"chapter-{chapter:03d}-{voice_id}.wav")
    chapter_audio = _wav_bytes(bytes(chapter_lpcm), config)
    atomic_write_bytes(chapter_path, chapter_audio)

    total_seconds = round(
        len(chapter_lpcm)
        / (config.nova.sample_rate_hz * config.nova.channels * (config.nova.sample_size_bits // 8)),
        2,
    )
    current_entries = [entries[segment.segment_id] for segment in segments]
    manifest = {
        **outline,
        "segments": current_entries,
        "carried_over_segments": _carried_over_entries(history, current_entries),
        "chapter_audio_path": workspace_relative(config.workspace_root, chapter_path),
        "chapter_audio_sha256": sha256_bytes(chapter_audio),
        "chapter_duration_seconds": total_seconds,
        "stitching": {
            "profile": STITCH_PROFILE,
            "silence_window_seconds": SILENCE_WINDOW_SECONDS,
            "silence_rms_threshold": SILENCE_RMS_THRESHOLD,
            "retained_edge_silence_seconds": EDGE_SILENCE_SECONDS,
            "edge_fade_seconds": EDGE_FADE_SECONDS,
            "partial_turn_policy": PARTIAL_TURN_POLICY,
            "partial_turn_crossfade_seconds": PARTIAL_TURN_CROSSFADE_SECONDS,
            "continuation_gap_seconds": CONTINUATION_GAP_SECONDS,
            "sentence_gap_seconds": SEGMENT_GAP_SECONDS,
            "paragraph_gap_seconds": PARAGRAPH_GAP_SECONDS,
        },
        "updated_at": utc_now(),
    }
    atomic_write_json(manifest_path, manifest)
    return {
        "chapter": chapter,
        "voice_id": voice_id,
        "chapter_text_changed_since_last_run": source_changed,
        "segments_total": len(segments),
        "segments_rendered": rendered,
        "segments_reused": reused,
        "billable_calls_made": rendered,
        "chapter_audio": str(chapter_path),
        "chapter_duration_seconds": total_seconds,
        "stitch_profile": STITCH_PROFILE,
        "exact_transcript_segments": sum(
            1 for item in entries.values() if item.get("exact_transcript_match")
        ),
    }
