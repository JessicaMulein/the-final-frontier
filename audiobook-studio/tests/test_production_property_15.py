"""Deterministic generated checks for audiobook production correctness Property 15."""

from __future__ import annotations

import base64
import json
import random
import socket
import wave
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path

import pytest

from frontier_audiobook import narrate, nova
from frontier_audiobook.production import (
    ProductionSelectors,
    create_production_plan,
    load_production_plan,
)
from frontier_audiobook.production_config import (
    build_ordered_track_catalog,
    parse_production_toml,
)
from frontier_audiobook.production_models import FrozenTrackPlan
from frontier_audiobook.production_preflight import (
    InventoryKind,
    PriorArtifactState,
    ReadOnlyLegacyAdapter,
    ReuseDisposition,
)
from frontier_audiobook.util import (
    read_bytes_nofollow,
    sha256_bytes,
    workspace_relative,
)


PROPERTY_TAG = (
    "Feature: audiobook-production-workflow, Property 15: Legacy import is "
    "observational and byte-preserving"
)
PROPERTY_SEED = 0xA0D10B0F
GENERATED_CASES = 128

# **Validates: Requirements 13.5, 14.1, 14.2, 14.3, 14.4, 14.5,
# 14.6, 14.7**

_FIXTURE_KINDS = (
    "complete",
    "incomplete",
    "ambiguous",
    "tampered",
    "cross-source-revision",
)
_INCOMPLETE_PARTS = (
    "manifest-entry",
    "segment-audio",
    "transcript",
    "event-journal",
)
_TAMPER_MODES = (
    "render-identity",
    "render-config",
    "audio-hash",
    "transcript-body",
    "event-audio",
    "event-transcript",
    "event-partial-turn",
    "fidelity-record",
    "partial-turn-record",
)
_WORDS = (
    "amber",
    "beacon",
    "cinder",
    "delta",
    "ember",
    "fable",
    "glimmer",
    "harbor",
    "island",
    "jovial",
    "kindle",
    "lumen",
    "meadow",
    "nectar",
    "orbit",
    "prairie",
    "quartz",
    "raven",
    "silver",
    "timber",
    "umber",
    "velvet",
    "willow",
    "xenon",
    "yonder",
    "zephyr",
)


@dataclass(frozen=True, slots=True)
class _GeneratedCase:
    case_index: int
    chapter: int
    fixture_kind: str
    target_ordinal: int
    mutation_index: int
    incomplete_part: str
    tamper_mode: str
    frame_variation: int


@dataclass(frozen=True, slots=True)
class _LegacyFixture:
    manifest_paths: tuple[Path, ...]
    target_render_identity_sha256: str
    audio_paths_by_segment_id: dict[str, Path]


@pytest.fixture(autouse=True)
def deny_network_aws_model_and_render(monkeypatch):
    """Fail immediately if Property 15 crosses any external or paid boundary."""

    def blocked(*_args, **_kwargs):
        raise AssertionError(
            "Property 15 legacy observation must remain offline and nonbillable"
        )

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setattr(nova, "render_text", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)


def _generated_case(rng: random.Random, case_index: int) -> _GeneratedCase:
    return _GeneratedCase(
        case_index=case_index,
        chapter=1 + ((case_index // len(_FIXTURE_KINDS)) % 2),
        fixture_kind=_FIXTURE_KINDS[case_index % len(_FIXTURE_KINDS)],
        target_ordinal=rng.randint(2, 7),
        mutation_index=rng.randint(2, 4),
        incomplete_part=rng.choice(_INCOMPLETE_PARTS),
        tamper_mode=rng.choice(_TAMPER_MODES),
        frame_variation=rng.randint(0, 31),
    )


def _sentences(case_index: int) -> tuple[str, ...]:
    sentences: list[str] = []
    for ordinal in range(1, 10):
        shift = (case_index * 3 + ordinal * 5) % len(_WORDS)
        words = (
            _WORDS[shift].capitalize(),
            _WORDS[(shift + 1) % len(_WORDS)],
            _WORDS[(shift + 2) % len(_WORDS)],
            f"case{case_index:03d}",
            f"unit{ordinal:02d}",
        )
        sentences.append(f"{' '.join(words)}.")
    return tuple(sentences)


def _inserted_sentence(case_index: int) -> str:
    return f"Inserted revision marker case{case_index:03d} evidence."


def _chapter_path(workspace: Path, chapter: int) -> Path:
    names = {
        1: "discovery-part-001-property-fifteen.md",
        2: "discovery-part-002-property-fifteen.md",
    }
    return (
        workspace
        / "The Final Frontier Novel"
        / "chapters"
        / "discovery-part"
        / names[chapter]
    )


def _write_chapter(workspace: Path, chapter: int, sentences: tuple[str, ...]) -> Path:
    path = _chapter_path(workspace, chapter)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = " ".join(sentences)
    path.write_text(
        "\n".join(
            (
                "---",
                "movement: discovery",
                f"chapter: {chapter}",
                'title: "Property Fifteen Chapter"',
                "pov_id: property-fifteen-pov",
                "timeline_id: property-fifteen-timeline",
                "motif_events: none",
                "hook: property-fifteen-hook",
                f"words: {len(body.split())}",
                "length_class: short",
                "status: draft",
                "---",
                body,
                "",
            )
        ),
        encoding="utf-8",
    )
    return path


def _write_workspace(
    workspace: Path,
    chapter: int,
    sentences: tuple[str, ...],
) -> Path:
    _write_chapter(workspace, chapter, sentences)
    config_path = workspace / "audiobook-studio" / "config" / "production.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        '''schema_version = 1
book_id = "the-final-frontier"
manuscript_root = "The Final Frontier Novel"
build_root = "audiobook-studio/build/production"
delivery_root = "audiobook-studio/dist/audiobook"
max_tracks_per_plan = 16
tracks = []

[defaults]
voice = "tiffany"
model_id = "amazon.nova-2-sonic-v1:0"
region = "us-east-1"
profile_label = "frontier-audiobook"
target_segment_words = 5
fidelity_policy = "exact"
normalization = "frontier-word-sequence-v1"
output_template = "{sequence:03d}-{track_slug}-{voice}.wav"

[defaults.audio]
sample_rate_hz = 24000
sample_size_bits = 16
channels = 1

[estimate]
rate_max_age_hours = 24
preflight_max_age_hours = 24
input_speech_tokens_per_call = 0
input_text_tokens_per_call = 8192
output_speech_tokens_per_call = 8192
output_text_tokens_per_call = 8192
''',
        encoding="utf-8",
    )
    return config_path


def _create_track_plan(
    workspace: Path,
    config_path: Path,
    chapter: int,
    plan_id: str,
) -> tuple[Path, FrozenTrackPlan]:
    plan_path = create_production_plan(
        config_path,
        ProductionSelectors.from_cli(chapters=[chapter]),
        plan_id=plan_id,
        workspace_root=workspace,
        created_at_utc="2026-09-15T00:00:00Z",
    )
    plan = load_production_plan(plan_path)
    assert len(plan.tracks) == 1
    return plan_path, plan.tracks[0]


def _wav_bytes(lpcm: bytes) -> bytes:
    output = BytesIO()
    with wave.open(output, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(lpcm)
    return output.getvalue()


def _content_start(
    identity: dict[str, str],
    content_id: str,
    content_type: str,
    *,
    stage: str | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        **identity,
        "contentId": content_id,
        "role": "ASSISTANT",
        "type": content_type,
    }
    if content_type == "AUDIO":
        payload["audioOutputConfiguration"] = {
            "mediaType": "audio/lpcm",
            "sampleRateHertz": 24000,
            "sampleSizeBits": 16,
            "encoding": "base64",
            "channelCount": 1,
        }
    else:
        payload["textOutputConfiguration"] = {"mediaType": "text/plain"}
        if stage is not None:
            payload["additionalModelFields"] = json.dumps(
                {"generationStage": stage},
                separators=(",", ":"),
            )
    return {"contentStart": payload}


def _output_events(
    transcript: str,
    lpcm: bytes,
    *,
    unsafe_partial_turn: bool = False,
) -> tuple[dict[str, object], ...]:
    identity = {
        "sessionId": "property-fifteen-session",
        "promptName": "property-fifteen-prompt",
        "completionId": "property-fifteen-completion",
    }
    events: list[dict[str, object]] = [{"completionStart": dict(identity)}]

    if unsafe_partial_turn:
        events.extend(
            (
                _content_start(identity, "speculative-1", "TEXT", stage="SPECULATIVE"),
                {
                    "textOutput": {
                        **identity,
                        "contentId": "speculative-1",
                        "content": "unfinished speculative phrase",
                    }
                },
                {
                    "contentEnd": {
                        **identity,
                        "contentId": "speculative-1",
                        "stopReason": "END_TURN",
                        "type": "TEXT",
                    }
                },
            )
        )
        split_at = (len(lpcm) // 4) * 2
        split_at = min(max(split_at, 2), len(lpcm) - 2)
        audio_parts = (
            ("audio-partial", lpcm[:split_at], "PARTIAL_TURN"),
            ("audio-final", lpcm[split_at:], "END_TURN"),
        )
    else:
        audio_parts = (("audio-final", lpcm, "END_TURN"),)

    for content_id, content, stop_reason in audio_parts:
        events.extend(
            (
                _content_start(identity, content_id, "AUDIO"),
                {
                    "audioOutput": {
                        **identity,
                        "contentId": content_id,
                        "content": base64.b64encode(content).decode("ascii"),
                    }
                },
                {
                    "contentEnd": {
                        **identity,
                        "contentId": content_id,
                        "stopReason": stop_reason,
                        "type": "AUDIO",
                    }
                },
            )
        )

    events.extend(
        (
            _content_start(identity, "final-text", "TEXT", stage="FINAL"),
            {
                "textOutput": {
                    **identity,
                    "contentId": "final-text",
                    "content": transcript,
                }
            },
            {
                "contentEnd": {
                    **identity,
                    "contentId": "final-text",
                    "stopReason": "END_TURN",
                    "type": "TEXT",
                }
            },
            {
                "usageEvent": {
                    **identity,
                    "totalInputTokens": 5,
                    "totalOutputTokens": 10,
                    "totalTokens": 15,
                    "details": {
                        "input_speech": {"delta": 0, "total": 0},
                        "input_text": {"delta": 5, "total": 5},
                        "output_speech": {"delta": 5, "total": 5},
                        "output_text": {"delta": 5, "total": 5},
                    },
                }
            },
            {"completionEnd": {**identity, "stopReason": "END_TURN"}},
        )
    )
    return tuple(events)


def _event_bytes(events: tuple[dict[str, object], ...]) -> bytes:
    return "".join(
        json.dumps(event, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
        + "\n"
        for event in events
    ).encode("utf-8")


def _legacy_root(
    workspace: Path,
    case: _GeneratedCase,
    variant: str,
) -> Path:
    return (
        workspace
        / "audiobook-studio"
        / "build"
        / "narration"
        / (
            f"chapter-{case.chapter:03d}-tiffany-property-15-"
            f"{case.case_index:03d}-{variant}"
        )
    )


def _write_manifest_root(
    workspace: Path,
    case: _GeneratedCase,
    track_plan: FrozenTrackPlan,
    sentences: tuple[str, ...],
    *,
    variant: str,
    mutate: bool,
) -> tuple[Path, dict[str, Path], bytes]:
    root = _legacy_root(workspace, case, variant)
    for directory in (root / "segments", root / "transcripts", root / "events"):
        directory.mkdir(parents=True, exist_ok=True)

    assert len(track_plan.source.segments) == len(sentences)
    entries: list[dict[str, object]] = []
    audio_paths_by_segment_id: dict[str, Path] = {}
    lpcm_parts: list[bytes] = []
    target_index = case.target_ordinal - 1

    for snapshot, text in zip(track_plan.source.segments, sentences, strict=True):
        sample_value = (case.case_index + snapshot.ordinal * 17) % 256
        lpcm = bytes((sample_value, 0)) * (
            96 + case.frame_variation + snapshot.ordinal
        )
        lpcm_parts.append(lpcm)
        stem = f"{snapshot.ordinal:04d}-{snapshot.text_sha256}"
        audio_path = root / "segments" / f"{stem}.wav"
        transcript_path = root / "transcripts" / f"{stem}.txt"
        event_path = root / "events" / f"{stem}.jsonl"

        audio = _wav_bytes(lpcm)
        transcript = (text + "\n").encode("utf-8")
        events = _event_bytes(_output_events(text, lpcm))
        audio_path.write_bytes(audio)
        transcript_path.write_bytes(transcript)
        event_path.write_bytes(events)
        audio_paths_by_segment_id[snapshot.segment_id] = audio_path

        entries.append(
            {
                "segment_id": snapshot.segment_id,
                "status": "narrated",
                "text_sha256": snapshot.text_sha256,
                "render_identity_sha256": snapshot.render_identity_sha256,
                "render_config_sha256": snapshot.render_config_sha256,
                "exact_transcript_match": True,
                "coverage_ratio": 1.0,
                "mid_sentence_partial_turns": 0,
                "audio_path": workspace_relative(workspace, audio_path),
                "audio_sha256": sha256_bytes(audio),
                "transcript_path": workspace_relative(workspace, transcript_path),
                "transcript_sha256": sha256_bytes(transcript),
                "event_journal_path": workspace_relative(workspace, event_path),
                "event_journal_sha256": sha256_bytes(events),
            }
        )

    if mutate and case.fixture_kind == "incomplete":
        target = entries[target_index]
        if case.incomplete_part == "manifest-entry":
            entries.pop(target_index)
        elif case.incomplete_part == "segment-audio":
            (workspace / str(target["audio_path"])).unlink()
        elif case.incomplete_part == "transcript":
            (workspace / str(target["transcript_path"])).unlink()
        else:
            (workspace / str(target["event_journal_path"])).unlink()

    if mutate and case.fixture_kind == "tampered":
        target = entries[target_index]
        snapshot = track_plan.source.segments[target_index]
        text = sentences[target_index]
        audio_path = workspace / str(target["audio_path"])
        transcript_path = workspace / str(target["transcript_path"])
        event_path = workspace / str(target["event_journal_path"])
        lpcm = lpcm_parts[target_index]

        if case.tamper_mode == "render-identity":
            target["render_identity_sha256"] = sha256_bytes(
                f"wrong-render-identity-{case.case_index}".encode("utf-8")
            )
        elif case.tamper_mode == "render-config":
            target["render_config_sha256"] = sha256_bytes(
                f"wrong-render-config-{case.case_index}".encode("utf-8")
            )
        elif case.tamper_mode == "audio-hash":
            target["audio_sha256"] = sha256_bytes(
                f"wrong-audio-{case.case_index}".encode("utf-8")
            )
        elif case.tamper_mode == "transcript-body":
            changed = f"Mismatched transcript case {case.case_index}.\n".encode("utf-8")
            transcript_path.write_bytes(changed)
            target["transcript_sha256"] = sha256_bytes(changed)
        elif case.tamper_mode == "event-audio":
            changed_lpcm = bytes((lpcm[0] ^ 0xFF, lpcm[1])) + lpcm[2:]
            changed = _event_bytes(_output_events(text, changed_lpcm))
            event_path.write_bytes(changed)
            target["event_journal_sha256"] = sha256_bytes(changed)
        elif case.tamper_mode == "event-transcript":
            changed = _event_bytes(
                _output_events(f"Mismatched event transcript {case.case_index}.", lpcm)
            )
            event_path.write_bytes(changed)
            target["event_journal_sha256"] = sha256_bytes(changed)
        elif case.tamper_mode == "event-partial-turn":
            changed = _event_bytes(
                _output_events(text, lpcm, unsafe_partial_turn=True)
            )
            event_path.write_bytes(changed)
            target["event_journal_sha256"] = sha256_bytes(changed)
        elif case.tamper_mode == "fidelity-record":
            target["coverage_ratio"] = 0.5
        else:
            target["mid_sentence_partial_turns"] = 1

        assert audio_path.is_file()
        assert snapshot.render_identity_sha256 == track_plan.source.segments[
            target_index
        ].render_identity_sha256

    assembled = _wav_bytes(b"".join(lpcm_parts))
    assembled_path = root / f"chapter-{case.chapter:03d}-tiffany.wav"
    assembled_path.write_bytes(assembled)
    manifest = {
        "chapter": case.chapter,
        "source_sha256": track_plan.source.raw_sha256,
        "spoken_sha256": track_plan.source.spoken_sha256,
        "render_config_sha256": track_plan.source.segments[0].render_config_sha256,
        "active_render_identity_sha256s": [
            item.render_identity_sha256 for item in track_plan.source.segments
        ],
        "chapter_audio_path": workspace_relative(workspace, assembled_path),
        "chapter_audio_sha256": sha256_bytes(assembled),
        "segments": entries,
        "carried_over_segments": [],
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), sort_keys=True),
        encoding="utf-8",
    )
    return manifest_path, audio_paths_by_segment_id, assembled


def _write_legacy_fixture(
    workspace: Path,
    case: _GeneratedCase,
    track_plan: FrozenTrackPlan,
    sentences: tuple[str, ...],
) -> _LegacyFixture:
    first_manifest, audio_paths, assembled = _write_manifest_root(
        workspace,
        case,
        track_plan,
        sentences,
        variant="primary",
        mutate=True,
    )
    manifests = [first_manifest]
    if case.fixture_kind == "ambiguous":
        second_manifest, _second_audio_paths, _second_assembled = _write_manifest_root(
            workspace,
            case,
            track_plan,
            sentences,
            variant="duplicate",
            mutate=False,
        )
        manifests.append(second_manifest)

    proof = (
        workspace
        / "voice-samples"
        / f"chapter-{case.chapter}-tiffany-property-15-{case.case_index:03d}.wav"
    )
    proof.parent.mkdir(parents=True, exist_ok=True)
    proof.write_bytes(assembled)
    target = track_plan.source.segments[case.target_ordinal - 1]
    return _LegacyFixture(
        manifest_paths=tuple(sorted(manifests)),
        target_render_identity_sha256=target.render_identity_sha256,
        audio_paths_by_segment_id=audio_paths,
    )


def _snapshot_legacy_bytes(workspace: Path, chapter: int) -> dict[str, bytes]:
    paths: list[Path] = []
    narration_root = workspace / "audiobook-studio" / "build" / "narration"
    if narration_root.is_dir():
        prefix = f"chapter-{chapter:03d}-"
        for root in narration_root.iterdir():
            if root.name.startswith(prefix) and root.is_dir() and not root.is_symlink():
                paths.extend(
                    path
                    for path in root.rglob("*")
                    if path.is_file() and not path.is_symlink()
                )
    proof_root = workspace / "voice-samples"
    if proof_root.is_dir():
        prefix = f"chapter-{chapter}-"
        paths.extend(
            path
            for path in proof_root.iterdir()
            if path.name.startswith(prefix)
            and path.suffix.casefold() == ".wav"
            and path.is_file()
            and not path.is_symlink()
        )
    return {
        workspace_relative(workspace, path): read_bytes_nofollow(path)
        for path in sorted(paths)
    }


def _assert_observations_bind_exact_bytes(observations, expected: dict[str, bytes]) -> None:
    assert tuple(item.path for item in observations) == tuple(sorted(expected))
    for item in observations:
        content = expected[item.path]
        assert item.byte_count == len(content)
        assert item.sha256 == sha256_bytes(content)

    kinds = {item.kind for item in observations}
    assert InventoryKind.LEGACY_MANIFEST in kinds
    assert InventoryKind.LEGACY_TRANSCRIPT in kinds
    assert InventoryKind.LEGACY_EVENT_JOURNAL in kinds
    assert InventoryKind.PRIOR_AUDIO in kinds


def _valid_fixture_render_identities(
    case: _GeneratedCase,
    original_plan: FrozenTrackPlan,
) -> set[str]:
    identities = {
        item.render_identity_sha256 for item in original_plan.source.segments
    }
    if case.fixture_kind in {"incomplete", "tampered"}:
        identities.remove(
            original_plan.source.segments[
                case.target_ordinal - 1
            ].render_identity_sha256
        )
    if case.fixture_kind == "ambiguous":
        return set()
    return identities


def _run_generated_case(workspace: Path, case: _GeneratedCase) -> None:
    sentences = _sentences(case.case_index)
    config_path = _write_workspace(workspace, case.chapter, sentences)
    original_plan_path, original_plan = _create_track_plan(
        workspace,
        config_path,
        case.chapter,
        f"property-15-{case.case_index:03d}-original",
    )
    fixture = _write_legacy_fixture(
        workspace,
        case,
        original_plan,
        sentences,
    )

    current_plan_path = original_plan_path
    current_plan = original_plan
    if case.fixture_kind == "cross-source-revision":
        revised = (
            *sentences[: case.mutation_index],
            _inserted_sentence(case.case_index),
            *sentences[case.mutation_index :],
        )
        _write_chapter(workspace, case.chapter, revised)
        current_plan_path, current_plan = _create_track_plan(
            workspace,
            config_path,
            case.chapter,
            f"property-15-{case.case_index:03d}-revised",
        )

    for plan_path in {original_plan_path, current_plan_path}:
        relative_plan = workspace_relative(workspace, plan_path)
        assert relative_plan.startswith(
            "audiobook-studio/build/production/the-final-frontier/plans/"
        )
        assert "/narration/" not in relative_plan

    config = parse_production_toml(
        read_bytes_nofollow(config_path),
        label=str(config_path),
    )
    catalog = build_ordered_track_catalog(config, workspace)
    catalog_track = next(
        item for item in catalog.tracks if item.id == current_plan.track_id
    )
    adapter = ReadOnlyLegacyAdapter(workspace)

    bytes_before = _snapshot_legacy_bytes(workspace, case.chapter)
    observations_before = adapter.observe()
    _assert_observations_bind_exact_bytes(observations_before, bytes_before)
    assert adapter.manifest_paths(case.chapter) == fixture.manifest_paths

    assessment = adapter.inspect_track(
        current_plan,
        config,
        catalog_track,
    )
    repeated_assessment = adapter.inspect_track(
        current_plan,
        config,
        catalog_track,
    )
    assert repeated_assessment == assessment

    valid_identities = _valid_fixture_render_identities(case, original_plan)
    expected_reusable = tuple(
        item.segment_id
        for item in current_plan.source.segments
        if item.render_identity_sha256 in valid_identities
    )
    expected_rerender = tuple(
        item.segment_id
        for item in current_plan.source.segments
        if item.render_identity_sha256 not in valid_identities
    )
    assert assessment.reusable_segment_ids == expected_reusable
    assert assessment.rerender_segment_ids == expected_rerender
    assert assessment.maximum_new_calls == len(expected_rerender)

    by_segment_id = {item.segment_id: item for item in assessment.segments}
    for segment_id in expected_reusable:
        segment = by_segment_id[segment_id]
        assert segment.disposition is ReuseDisposition.CURRENT_REUSABLE
        assert segment.candidate_audio is not None
        audio = read_bytes_nofollow(workspace / segment.candidate_audio.path)
        assert segment.candidate_audio.byte_count == len(audio)
        assert segment.candidate_audio.sha256 == sha256_bytes(audio)
        assert segment.transcript_sha256 is not None
        assert segment.event_journal_sha256 is not None
        assert segment.finding_categories == ()
    for segment_id in expected_rerender:
        segment = by_segment_id[segment_id]
        assert segment.disposition is ReuseDisposition.STALE_RERENDER_REQUIRED
        assert segment.candidate_audio is None
        assert segment.finding_categories

    if case.fixture_kind == "complete":
        assert assessment.prior_state is PriorArtifactState.REUSABLE
        assert assessment.disposition is ReuseDisposition.CURRENT_REUSABLE
        assert assessment.assembled_audio is not None
        assert assessment.source_revision_changed is False
    else:
        assert assessment.prior_state is PriorArtifactState.REJECTED
        assert assessment.disposition is ReuseDisposition.STALE_RERENDER_REQUIRED
        assert assessment.assembled_audio is None

    if case.fixture_kind == "cross-source-revision":
        assert assessment.source_revision_changed is True
        original_by_identity = {
            item.render_identity_sha256: item
            for item in original_plan.source.segments
        }
        shifted_matches = tuple(
            item
            for item in current_plan.source.segments
            if item.render_identity_sha256 in original_by_identity
            and item.ordinal
            != original_by_identity[item.render_identity_sha256].ordinal
        )
        assert shifted_matches
        assert all(
            item.segment_id in assessment.reusable_segment_ids
            for item in shifted_matches
        )

        inserted = current_plan.source.segments[case.mutation_index]
        assert inserted.segment_id in fixture.audio_paths_by_segment_id
        assert fixture.audio_paths_by_segment_id[inserted.segment_id].is_file()
        assert inserted.render_identity_sha256 not in original_by_identity
        assert inserted.segment_id not in assessment.reusable_segment_ids
    else:
        assert assessment.source_revision_changed is False

    if case.fixture_kind in {"incomplete", "tampered"}:
        assert fixture.target_render_identity_sha256 not in {
            item.render_identity_sha256
            for item in current_plan.source.segments
            if item.segment_id in assessment.reusable_segment_ids
        }
    if case.fixture_kind == "ambiguous":
        assert all(
            "candidate-ambiguous" in item.finding_categories
            for item in assessment.segments
        )

    observations_after = adapter.observe()
    bytes_after = _snapshot_legacy_bytes(workspace, case.chapter)
    assert observations_after == observations_before
    assert bytes_after == bytes_before
    _assert_observations_bind_exact_bytes(observations_after, bytes_after)


def test_property_15_legacy_import_is_observational_and_byte_preserving(tmp_path):
    """Feature: audiobook-production-workflow, Property 15: Legacy import is observational and byte-preserving"""

    assert GENERATED_CASES >= 100
    print(f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; cases={GENERATED_CASES}")
    rng = random.Random(PROPERTY_SEED)
    coverage: set[tuple[int, str]] = set()
    for case_index in range(GENERATED_CASES):
        case = _generated_case(rng, case_index)
        coverage.add((case.chapter, case.fixture_kind))
        try:
            _run_generated_case(tmp_path / f"case-{case_index:03d}", case)
        except Exception as exc:
            exc.add_note(
                f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; case={case_index}; "
                f"input={case!r}"
            )
            raise

    assert {
        (chapter, fixture_kind)
        for chapter in (1, 2)
        for fixture_kind in _FIXTURE_KINDS
    } <= coverage
