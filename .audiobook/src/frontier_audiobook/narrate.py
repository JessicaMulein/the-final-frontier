"""Segmented chapter narration.

Amazon Nova 2 Sonic reliably narrates only a short passage per turn, so a chapter
is split into small verbatim segments, rendered one at a time, verified against
the source, and concatenated. Every rendered segment is journalled so an
interrupted run resumes without paying for the same segment twice.
"""

from __future__ import annotations

import io
import json
import re
import wave
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Protocol

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


@dataclass(frozen=True)
class TrackSourceSnapshot:
    """One in-memory source read; prose remains confined to the runtime caller."""

    track_id: str
    source_path: str
    source_sha256: str
    revision_sha256: str
    spoken_text: str
    manifest_metadata: Mapping[str, object]

    def __post_init__(self) -> None:
        if not isinstance(self.track_id, str) or not self.track_id.strip():
            raise InputError("Track source track_id must be nonblank text")
        if not isinstance(self.source_path, str) or not self.source_path.strip():
            raise InputError("Track source path must be nonblank text")
        for field_name in ("source_sha256", "revision_sha256"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
                raise InputError(f"Track source {field_name} must be a lowercase SHA-256")
        if not isinstance(self.spoken_text, str) or not self.spoken_text.strip():
            raise InputError("Track source spoken text must be nonblank")
        if not isinstance(self.manifest_metadata, Mapping):
            raise InputError("Track source manifest metadata must be a mapping")
        object.__setattr__(
            self,
            "manifest_metadata",
            MappingProxyType(dict(self.manifest_metadata)),
        )


class TrackSource(Protocol):
    """Re-readable narration source shared by chapters and approved Special Tracks."""

    @property
    def track_id(self) -> str: ...

    def read(self) -> TrackSourceSnapshot: ...


@dataclass(frozen=True)
class NarrationSegmentIdentity:
    """Frozen segment identity used for content-addressed runtime artifacts."""

    segment_id: str
    text_sha256: str
    render_identity_sha256: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.segment_id, str) or not self.segment_id.strip():
            raise InputError("Narration segment identity must have a nonblank ID")
        for field_name in ("text_sha256", "render_identity_sha256"):
            value = getattr(self, field_name)
            if value is not None and (
                not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value)
            ):
                raise InputError(
                    f"Narration segment identity {field_name} must be a lowercase SHA-256"
                )


@dataclass(frozen=True)
class ChapterTrackSource:
    """Compatibility adapter that places existing chapter reads behind TrackSource."""

    config: AuditionConfig
    chapter: int

    @property
    def track_id(self) -> str:
        return f"chapter-{self.chapter:03d}"

    def read(self) -> TrackSourceSnapshot:
        source, spoken = chapter_spoken_text(self.config, self.chapter)
        spoken_sha256 = sha256_text(spoken)
        chapter_path = workspace_relative(self.config.workspace_root, source.path)
        return TrackSourceSnapshot(
            track_id=self.track_id,
            source_path=chapter_path,
            source_sha256=source.body_sha256,
            # Existing audition narration intentionally treats restricted-header edits
            # as non-narrative; only the spoken revision gates its legacy behavior.
            revision_sha256=spoken_sha256,
            spoken_text=spoken,
            manifest_metadata={
                "chapter": self.chapter,
                "chapter_path": chapter_path,
            },
        )


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


def _segment_paths(
    root: Path,
    segment: Segment,
    *,
    segment_id: str | None = None,
    text_sha256: str | None = None,
) -> dict[str, Path]:
    """Return immutable content-addressed paths for a newly rendered segment."""

    stem = f"{segment_id or segment.segment_id}-{text_sha256 or sha256_text(segment.text)}"
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


def _replay_event_journal(events_path: Path):
    """Strictly load and replay one existing Nova event journal."""

    try:
        lines = read_bytes_nofollow(events_path).decode("utf-8").splitlines()
        events = tuple(json.loads(line) for line in lines if line)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise InputError(f"Malformed narration event log {events_path}: {exc}") from exc
    return events, replay_output_events(events)


def _event_audio_blocks(
    events_path: Path,
    expected_lpcm: bytes,
) -> tuple[tuple[bytes, bool], ...]:
    """Recover audio blocks and mark only non-semantic PARTIAL_TURN joins."""

    import base64

    events, replayed = _replay_event_journal(events_path)
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


@dataclass(frozen=True)
class StitchAudioSettings:
    """Exact audio fields consumed by the shared Track stitching algorithm."""

    sample_rate_hz: int
    sample_size_bits: int
    channels: int

    def __post_init__(self) -> None:
        for name in ("sample_rate_hz", "sample_size_bits", "channels"):
            value = getattr(self, name)
            if type(value) is not int or value < 1:
                raise InputError(f"Stitch audio {name} must be a positive integer")
        if self.sample_size_bits % 8:
            raise InputError("Stitch audio sample size must be byte-aligned")


@dataclass(frozen=True)
class StitchSegment:
    """One private in-memory segment supplied to shared deterministic stitching."""

    segment: Segment
    lpcm: bytes
    event_journal_path: Path | None

    def __post_init__(self) -> None:
        if not isinstance(self.segment, Segment):
            raise InputError("Stitch segment metadata must be a Segment")
        if not isinstance(self.lpcm, bytes) or not self.lpcm:
            raise InputError("Stitch segment LPCM must be nonempty bytes")
        if self.event_journal_path is not None and not isinstance(
            self.event_journal_path, Path
        ):
            raise InputError("Stitch event journal path must be a Path or None")


@dataclass(frozen=True)
class _StitchNovaSettings:
    sample_rate_hz: int
    sample_size_bits: int
    channels: int


@dataclass(frozen=True)
class _StitchConfig:
    nova: _StitchNovaSettings


def stitch_profile() -> dict[str, str | float]:
    """Return the complete versioned parameters bound to assembled Track audio."""

    return {
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
    }


def stitch_track_lpcm(
    parts: tuple[StitchSegment, ...],
    settings: StitchAudioSettings,
) -> bytes:
    """Reconstruct Track LPCM with the same smoothing and gap policy as production."""

    if not isinstance(parts, tuple) or not parts:
        raise InputError("Track stitching requires a nonempty ordered segment tuple")
    if not isinstance(settings, StitchAudioSettings):
        raise InputError("Track stitching requires StitchAudioSettings")
    config = _StitchConfig(
        _StitchNovaSettings(
            settings.sample_rate_hz,
            settings.sample_size_bits,
            settings.channels,
        )
    )
    assembled = bytearray()
    previous: Segment | None = None
    for ordinal, part in enumerate(parts, start=1):
        if not isinstance(part, StitchSegment) or part.segment.index != ordinal:
            raise InputError("Track stitching segments must be unique and contiguous in order")
        if previous is not None:
            assembled.extend(_silence(_gap_between(previous, part.segment), config))  # type: ignore[arg-type]
        assembled.extend(
            _smooth_clip_lpcm(  # type: ignore[arg-type]
                part.lpcm,
                config,
                part.event_journal_path,
            )
        )
        previous = part.segment
    return bytes(assembled)


def assembled_lpcm_duration_seconds(
    lpcm: bytes,
    settings: StitchAudioSettings,
) -> float:
    """Return the two-decimal manifest duration from exact complete PCM frames."""

    if not isinstance(lpcm, bytes) or not lpcm:
        raise InputError("Assembled Track LPCM must be nonempty bytes")
    frame_width = settings.channels * (settings.sample_size_bits // 8)
    if frame_width < 1 or len(lpcm) % frame_width:
        raise InputError("Assembled Track LPCM is not aligned to complete frames")
    frame_count = len(lpcm) // frame_width
    return round(frame_count / settings.sample_rate_hz, 2)


def _track_narration_snapshot(
    source: TrackSource,
    voice_id: str,
    max_words: int,
) -> tuple[TrackSourceSnapshot, dict[str, Any], tuple[Segment, ...]]:
    """Build an outline and segments from one immutable generic source read."""

    source_snapshot = source.read()
    if source_snapshot.track_id != source.track_id:
        raise InputError("Track source identity changed while it was read")
    spoken = source_snapshot.spoken_text
    segments = segment_spoken_text(spoken, max_words)
    outline = {
        "track_id": source_snapshot.track_id,
        "voice_id": voice_id,
        "source_path": source_snapshot.source_path,
        "source_sha256": source_snapshot.source_sha256,
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
        **source_snapshot.manifest_metadata,
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
    return source_snapshot, outline, segments


def _narration_snapshot(
    config: AuditionConfig,
    chapter: int,
    voice_id: str,
    max_words: int,
) -> tuple[dict[str, Any], tuple[Segment, ...]]:
    """Build the legacy chapter outline through the generic TrackSource path."""

    _source_snapshot, outline, segments = _track_narration_snapshot(
        ChapterTrackSource(config, chapter),
        voice_id,
        max_words,
    )
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
    *,
    identity: NarrationSegmentIdentity | None = None,
    require_event_replay: bool = False,
) -> dict[str, Any] | None:
    """Return a current, accepted entry for an intact previously paid render."""

    expected_identity = identity or NarrationSegmentIdentity(
        segment.segment_id,
        sha256_text(segment.text),
    )
    if not isinstance(entry, dict) or entry.get("text_sha256") != expected_identity.text_sha256:
        return None
    if (
        expected_identity.render_identity_sha256 is not None
        and entry.get("render_identity_sha256")
        != expected_identity.render_identity_sha256
    ):
        return None
    if entry.get("mid_sentence_partial_turns", 0):
        return None
    events_path: Path | None = None
    event_bytes: bytes | None = None
    try:
        audio_path = _entry_audio_path(config, entry)
        if audio_path is None or not audio_path.is_file():
            return None
        audio = read_bytes_nofollow(audio_path)
        if sha256_bytes(audio) != entry.get("audio_sha256"):
            return None
        transcript_path = (
            audio_path.parent.parent / "transcripts" / f"{audio_path.stem}.txt"
        )
        if not transcript_path.is_file():
            return None
        transcript_bytes = read_bytes_nofollow(transcript_path)
        transcript_value = transcript_bytes.decode("utf-8").removesuffix("\n")
        recorded_transcript = entry.get("transcript")
        if isinstance(recorded_transcript, str) and recorded_transcript != transcript_value:
            return None
        verification = compare_transcript(segment.text, transcript_value, config.normalization)
        lpcm = _lpcm_from_wav(audio_path, config)
        if require_event_replay:
            events_path = _event_path_for_audio(audio_path)
            if events_path is None:
                return None
            event_bytes = read_bytes_nofollow(events_path)
            _events, replayed = _replay_event_journal(events_path)
            if replayed.audio_lpcm != lpcm:
                return None
            replay_verification = compare_transcript(
                segment.text,
                replayed.final_transcript,
                config.normalization,
            )
            if not replay_verification.passed or normalized_tokens(
                transcript_value,
                config.normalization,
            ) != normalized_tokens(replayed.final_transcript, config.normalization):
                return None
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
    normalized = {
        **entry,
        "segment_id": expected_identity.segment_id,
        "paragraph_index": segment.paragraph_index,
        "text": segment.text,
        "text_sha256": expected_identity.text_sha256,
        "word_count": segment.word_count,
        "narration_only_punctuation": segment.narration_only_punctuation,
        "status": "narrated",
        "audio_path": workspace_relative(config.workspace_root, audio_path),
        "audio_sha256": sha256_bytes(audio),
        "transcript_path": workspace_relative(config.workspace_root, transcript_path),
        "transcript_sha256": sha256_bytes(transcript_bytes),
        "duration_seconds": duration,
        "transcript": transcript_value,
        "exact_transcript_match": verification.passed,
        "coverage_ratio": verification.coverage_ratio,
        "event_replay_passed": True,
        "mid_sentence_partial_turns": 0,
        "rendered_in_current_attempt": False,
    }
    if events_path is not None and event_bytes is not None:
        normalized["event_journal_path"] = workspace_relative(
            config.workspace_root, events_path
        )
        normalized["event_journal_sha256"] = sha256_bytes(event_bytes)
    if expected_identity.render_identity_sha256 is not None:
        normalized["render_identity_sha256"] = expected_identity.render_identity_sha256
    return normalized


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


def _assert_track_source_unchanged(
    source: TrackSource,
    expected_revision_sha256: str,
) -> TrackSourceSnapshot:
    """Fail before a billable call or assembly if a Track source moved mid-run."""

    current = source.read()
    if current.track_id != source.track_id:
        raise InputError("Track source identity changed during narration")
    if current.revision_sha256 != expected_revision_sha256:
        raise InputError(
            f"Track {source.track_id} source changed during narration; "
            "stopped before another paid render or final stitch"
        )
    return current


def _assert_chapter_unchanged(
    config: AuditionConfig,
    chapter: int,
    expected_spoken_sha256: str,
) -> None:
    """Compatibility wrapper for the legacy chapter source-drift check."""

    _assert_track_source_unchanged(
        ChapterTrackSource(config, chapter),
        expected_spoken_sha256,
    )


def _resolved_segment_identities(
    segments: tuple[Segment, ...],
    supplied: tuple[NarrationSegmentIdentity, ...] | None,
) -> tuple[NarrationSegmentIdentity, ...]:
    identities = supplied or tuple(
        NarrationSegmentIdentity(segment.segment_id, sha256_text(segment.text))
        for segment in segments
    )
    if len(identities) != len(segments):
        raise InputError("Frozen narration segment identities do not match segment count")
    if len({item.segment_id for item in identities}) != len(identities):
        raise InputError("Frozen narration segment identities contain duplicate IDs")
    for segment, identity in zip(segments, identities, strict=True):
        if identity.text_sha256 != sha256_text(segment.text):
            raise InputError(
                f"Frozen narration segment text differs for {identity.segment_id}"
            )
    return identities


def narrate_track(
    config: AuditionConfig,
    source: TrackSource,
    voice_id: str,
    *,
    runtime_root: Path,
    assembly_name: str,
    paid_render_authorized: bool = False,
    accept_verbatim_prefix: bool = False,
    max_words: int = MAX_SEGMENT_WORDS,
    maximum_new_calls: int | None = None,
    segment_identities: tuple[NarrationSegmentIdentity, ...] | None = None,
    require_event_replay: bool = False,
    assembly_manifest_prefix: str = "track",
    before_model_call: Callable[
        [Segment, NarrationSegmentIdentity, int, Path], None
    ]
    | None = None,
    before_assembly: Callable[[], None] | None = None,
    progress: Any = None,
) -> dict[str, Any]:
    """Render one generic Track through the established narration algorithms.

    A nonreusable segment reaches ``render_text`` at most once.  The optional guard
    is the final operation before that possible model call, allowing production to
    revalidate frozen source/config/runtime/authorization/call evidence without
    changing audition behavior.
    """

    if not paid_render_authorized:
        raise InputError("Refusing billable narration without explicit paid-render authorization")
    if not isinstance(assembly_name, str) or not assembly_name.strip():
        raise InputError("Track assembly name must be nonblank text")
    if not re.fullmatch(r"[a-z][a-z0-9_]*", assembly_manifest_prefix):
        raise InputError("Track assembly manifest prefix is invalid")

    source_snapshot, outline, segments = _track_narration_snapshot(
        source,
        voice_id,
        max_words,
    )
    identities = _resolved_segment_identities(segments, segment_identities)
    outline = {
        **outline,
        "segments": [
            {
                "segment_id": identity.segment_id,
                "paragraph_index": segment.paragraph_index,
                "word_count": segment.word_count,
                "text": segment.text,
                "text_sha256": identity.text_sha256,
                "render_identity_sha256": identity.render_identity_sha256,
                "narration_only_punctuation": segment.narration_only_punctuation,
            }
            for segment, identity in zip(segments, identities, strict=True)
        ],
    }
    baseline_revision_sha256 = source_snapshot.revision_sha256
    baseline_spoken_sha256 = outline["spoken_sha256"]
    checked_maximum_new_calls = (
        len(segments) if maximum_new_calls is None else maximum_new_calls
    )
    if (
        type(checked_maximum_new_calls) is not int
        or checked_maximum_new_calls < 0
        or checked_maximum_new_calls > len(segments)
    ):
        raise InputError("Track maximum new calls must be within the frozen segment count")

    relative_root = workspace_relative(config.workspace_root, runtime_root)
    root = resolve_inside(config.workspace_root, relative_root)
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

    def persist_progress() -> dict[str, Any]:
        current = [
            entries[identity.segment_id]
            for identity in identities
            if identity.segment_id in entries
        ]
        progress_manifest = {
            **outline,
            "active_segment_count": len(current),
            "segments": current,
            "carried_over_segments": _carried_over_entries(history, current),
            "maximum_new_calls": checked_maximum_new_calls,
            "billable_calls_made": rendered,
            "updated_at": utc_now(),
        }
        atomic_write_json(manifest_path, progress_manifest)
        return progress_manifest

    for segment, identity in zip(segments, identities, strict=True):
        accepted_entry = None
        for candidate in candidates_by_text.get(identity.text_sha256, []):
            accepted_entry = _normalized_reusable_entry(
                candidate,
                segment,
                config,
                accept_verbatim_prefix,
                identity=identity,
                require_event_replay=require_event_replay,
            )
            if accepted_entry is not None:
                break
        if accepted_entry is not None:
            reused += 1
            entries[identity.segment_id] = accepted_entry
            persist_progress()
            if progress is not None:
                progress(segment, "reused", accepted_entry)
            continue

        _assert_track_source_unchanged(source, baseline_revision_sha256)
        if rendered >= checked_maximum_new_calls:
            raise InputError(
                f"Track {source.track_id} reached its authorized new-call ceiling "
                "before a nonreusable segment"
            )
        if before_model_call is not None:
            before_model_call(segment, identity, rendered, manifest_path)

        paths = _segment_paths(
            root,
            segment,
            segment_id=identity.segment_id,
            text_sha256=identity.text_sha256,
        )
        # Deliberately one invocation with no retry loop for this nonreusable segment.
        result = render_text(
            segment.text,
            voice_id,
            config.nova,
            paid_render_authorized=True,
        )
        verification = compare_transcript(
            segment.text,
            result.final_transcript,
            config.normalization,
        )
        audio = _wav_bytes(result.audio_lpcm, config)
        duration = round(
            len(result.audio_lpcm)
            / (
                config.nova.sample_rate_hz
                * config.nova.channels
                * (config.nova.sample_size_bits // 8)
            ),
            3,
        )
        transcript_document = result.final_transcript + "\n"
        event_document = "".join(
            json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"
            for event in result.events
        )
        atomic_write_bytes(paths["audio"], audio)
        atomic_write_text(paths["transcript"], transcript_document)
        atomic_write_text(paths["events"], event_document)

        fidelity_passed = fidelity_accepted(
            verification,
            duration,
            accept_verbatim_prefix=accept_verbatim_prefix,
        )
        event_replay_passed = not require_event_replay
        mid_sentence_partial_turns = 0
        if result.events:
            try:
                _events, replayed = _replay_event_journal(paths["events"])
                replay_verification = compare_transcript(
                    segment.text,
                    replayed.final_transcript,
                    config.normalization,
                )
                rendered_blocks = _event_audio_blocks(paths["events"], result.audio_lpcm)
                mid_sentence_partial_turns = sum(
                    repair_after for _, repair_after in rendered_blocks
                )
                event_replay_passed = (
                    replayed.audio_lpcm == result.audio_lpcm
                    and replay_verification.passed
                    and normalized_tokens(
                        replayed.final_transcript,
                        config.normalization,
                    )
                    == normalized_tokens(result.final_transcript, config.normalization)
                )
            except InputError:
                event_replay_passed = False

        status = (
            "mid_sentence_partial_turn"
            if mid_sentence_partial_turns
            else "event_replay_mismatch"
            if not event_replay_passed
            else "narrated"
            if fidelity_passed
            else "fidelity_mismatch"
        )
        entry = {
            "segment_id": identity.segment_id,
            "paragraph_index": segment.paragraph_index,
            "text": segment.text,
            "text_sha256": identity.text_sha256,
            "word_count": segment.word_count,
            "narration_only_punctuation": segment.narration_only_punctuation,
            "status": status,
            "audio_path": workspace_relative(config.workspace_root, paths["audio"]),
            "audio_sha256": sha256_bytes(audio),
            "transcript_path": workspace_relative(
                config.workspace_root, paths["transcript"]
            ),
            "transcript_sha256": sha256_bytes(transcript_document.encode("utf-8")),
            "event_journal_path": workspace_relative(
                config.workspace_root, paths["events"]
            ),
            "event_journal_sha256": sha256_bytes(event_document.encode("utf-8")),
            "duration_seconds": duration,
            "transcript": result.final_transcript,
            "exact_transcript_match": verification.passed,
            "coverage_ratio": verification.coverage_ratio,
            "event_replay_passed": event_replay_passed,
            "mid_sentence_partial_turns": mid_sentence_partial_turns,
            "rendered_in_current_attempt": True,
            "call_ordinal": rendered + 1,
            "narrated_at": utc_now(),
        }
        if identity.render_identity_sha256 is not None:
            entry["render_identity_sha256"] = identity.render_identity_sha256
        entries[identity.segment_id] = entry
        rendered += 1
        persist_progress()
        if progress is not None:
            progress(segment, status, entry)
        if mid_sentence_partial_turns:
            raise FidelityMismatch(
                f"Segment {identity.segment_id} of Track {source.track_id} crossed a "
                f"mid-sentence Nova PARTIAL_TURN; narration stopped. Review {manifest_path}"
            )
        if not event_replay_passed:
            raise FidelityMismatch(
                f"Segment {identity.segment_id} of Track {source.track_id} did not pass "
                f"complete event replay; narration stopped. Review {manifest_path}"
            )
        if not fidelity_passed:
            raise FidelityMismatch(
                f"Segment {identity.segment_id} of Track {source.track_id} did not pass "
                f"fidelity; narration stopped. Review {manifest_path}"
            )

    _assert_track_source_unchanged(source, baseline_revision_sha256)
    if before_assembly is not None:
        before_assembly()

    stitch_settings = StitchAudioSettings(
        config.nova.sample_rate_hz,
        config.nova.sample_size_bits,
        config.nova.channels,
    )
    stitch_parts: list[StitchSegment] = []
    for ordinal, (segment, identity) in enumerate(
        zip(segments, identities, strict=True),
        start=1,
    ):
        entry = entries[identity.segment_id]
        audio_path = _entry_audio_path(config, entry)
        if audio_path is None:
            raise InputError(f"Segment {identity.segment_id} has no recorded audio path")
        audio = read_bytes_nofollow(audio_path)
        if sha256_bytes(audio) != entry.get("audio_sha256"):
            raise InputError(f"Segment {identity.segment_id} audio changed before stitching")
        stitch_parts.append(
            StitchSegment(
                Segment(
                    ordinal,
                    segment.paragraph_index,
                    segment.text,
                    segment.narration_only_punctuation,
                ),
                _lpcm_from_wav(audio_path, config),
                _event_path_for_audio(audio_path),
            )
        )

    track_lpcm = stitch_track_lpcm(tuple(stitch_parts), stitch_settings)
    track_path = resolve_inside(root, assembly_name)
    track_audio = _wav_bytes(track_lpcm, config)
    atomic_write_bytes(track_path, track_audio)
    total_seconds = assembled_lpcm_duration_seconds(track_lpcm, stitch_settings)
    current_entries = [entries[identity.segment_id] for identity in identities]
    manifest = {
        **outline,
        "active_segment_count": len(current_entries),
        "segments": current_entries,
        "carried_over_segments": _carried_over_entries(history, current_entries),
        "maximum_new_calls": checked_maximum_new_calls,
        "billable_calls_made": rendered,
        f"{assembly_manifest_prefix}_audio_path": workspace_relative(
            config.workspace_root,
            track_path,
        ),
        f"{assembly_manifest_prefix}_audio_sha256": sha256_bytes(track_audio),
        f"{assembly_manifest_prefix}_audio_byte_count": len(track_audio),
        f"{assembly_manifest_prefix}_duration_seconds": total_seconds,
        "stitching": stitch_profile(),
        "updated_at": utc_now(),
    }
    atomic_write_json(manifest_path, manifest)
    return {
        "track_id": source.track_id,
        "voice_id": voice_id,
        "source_changed_since_last_run": source_changed,
        "segments_total": len(segments),
        "segments_rendered": rendered,
        "segments_reused": reused,
        "billable_calls_made": rendered,
        "track_audio": str(track_path),
        "track_audio_sha256": sha256_bytes(track_audio),
        "track_duration_seconds": total_seconds,
        "stitch_profile": STITCH_PROFILE,
        "exact_transcript_segments": sum(
            1 for item in entries.values() if item.get("exact_transcript_match")
        ),
    }


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
    """Preserve the existing audition chapter contract over the generic engine."""

    if not paid_render_authorized:
        raise InputError("Refusing billable narration without explicit paid-render authorization")
    if voice_id not in config.voices:
        raise InputError(f"Voice {voice_id!r} is not one of the configured voices")

    result = narrate_track(
        config,
        ChapterTrackSource(config, chapter),
        voice_id,
        runtime_root=_narration_root(config, chapter, voice_id),
        assembly_name=f"chapter-{chapter:03d}-{voice_id}.wav",
        paid_render_authorized=True,
        accept_verbatim_prefix=accept_verbatim_prefix,
        max_words=max_words,
        assembly_manifest_prefix="chapter",
        progress=progress,
    )
    return {
        "chapter": chapter,
        "voice_id": voice_id,
        "chapter_text_changed_since_last_run": result[
            "source_changed_since_last_run"
        ],
        "segments_total": result["segments_total"],
        "segments_rendered": result["segments_rendered"],
        "segments_reused": result["segments_reused"],
        "billable_calls_made": result["billable_calls_made"],
        "chapter_audio": result["track_audio"],
        "chapter_duration_seconds": result["track_duration_seconds"],
        "stitch_profile": result["stitch_profile"],
        "exact_transcript_segments": result["exact_transcript_segments"],
    }
