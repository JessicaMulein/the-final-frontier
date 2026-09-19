from __future__ import annotations

import base64
import json
import shutil
import socket
import subprocess
import wave
from dataclasses import dataclass, replace
from io import BytesIO
from pathlib import Path

import pytest

from frontier_audiobook import narrate
from frontier_audiobook.production_models import (
    RECORD_SCHEMA_VERSION,
    AttemptResult,
    AudioEncoding,
    AudioFormat,
    EffectiveTrackConfig,
    FidelityPolicy,
    FrozenBatchPlan,
    FrozenTrackPlan,
    SegmentSnapshot,
    SourceKind,
    SourceSnapshot,
    StrictRecordCodec,
    TrackKind,
    TransactionState,
    ValidationEvidence,
    ValidationStatus,
    canonical_sha256,
    seal_record,
)
from frontier_audiobook.production_transactions import TransactionStore
from frontier_audiobook.production_validation import (
    load_passing_validation_evidence,
    validate_frozen_track_manifest,
    validation_evidence_path,
)
from frontier_audiobook.util import sha256_bytes, sha256_text
from frontier_audiobook.verify import normalized_tokens


@dataclass(frozen=True)
class ValidationFixture:
    workspace: Path
    plan_path: Path
    plan: FrozenBatchPlan
    track: FrozenTrackPlan
    store: TransactionStore
    transaction_root: Path
    attempt_root: Path
    manifest_path: Path
    protected_path: Path


@pytest.fixture(autouse=True)
def deny_every_external_or_paid_boundary(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("structural validation must remain local and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(subprocess, "Popen", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.delenv(name, raising=False)


def _hash(character: str) -> str:
    return character * 64


def _write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )


def _wav_bytes(
    lpcm: bytes,
    *,
    sample_rate_hz: int = 24000,
    sample_size_bytes: int = 2,
    channels: int = 1,
) -> bytes:
    output = BytesIO()
    with wave.open(output, "wb") as handle:
        handle.setnchannels(channels)
        handle.setsampwidth(sample_size_bytes)
        handle.setframerate(sample_rate_hz)
        handle.writeframes(lpcm)
    return output.getvalue()


def _output_events(
    transcript: str,
    lpcm: bytes,
    *,
    unsafe_partial_turn: bool = False,
) -> tuple[dict[str, object], ...]:
    identity = {
        "sessionId": "validation-session",
        "promptName": "validation-prompt",
        "completionId": "validation-completion",
    }
    audio_configuration = {
        "mediaType": "audio/lpcm",
        "sampleRateHertz": 24000,
        "sampleSizeBits": 16,
        "encoding": "base64",
        "channelCount": 1,
    }
    events: list[dict[str, object]] = [{"completionStart": dict(identity)}]
    audio_blocks = (("audio-1", lpcm, "END_TURN"),)
    if unsafe_partial_turn:
        events.extend(
            (
                {
                    "contentStart": {
                        **identity,
                        "contentId": "speculative-1",
                        "role": "ASSISTANT",
                        "type": "TEXT",
                        "additionalModelFields": '{"generationStage":"SPECULATIVE"}',
                        "textOutputConfiguration": {"mediaType": "text/plain"},
                    }
                },
                {
                    "textOutput": {
                        **identity,
                        "contentId": "speculative-1",
                        "content": "unfinished clause",
                    }
                },
                {
                    "contentEnd": {
                        **identity,
                        "contentId": "speculative-1",
                        "stopReason": "PARTIAL_TURN",
                        "type": "TEXT",
                    }
                },
            )
        )
        split = max(2, (len(lpcm) // 4) * 2)
        audio_blocks = (
            ("audio-1", lpcm[:split], "PARTIAL_TURN"),
            ("audio-2", lpcm[split:], "END_TURN"),
        )
    for content_id, block, stop_reason in audio_blocks:
        events.extend(
            (
                {
                    "contentStart": {
                        **identity,
                        "contentId": content_id,
                        "role": "ASSISTANT",
                        "type": "AUDIO",
                        "audioOutputConfiguration": audio_configuration,
                    }
                },
                {
                    "audioOutput": {
                        **identity,
                        "contentId": content_id,
                        "content": base64.b64encode(block).decode("ascii"),
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
            {
                "contentStart": {
                    **identity,
                    "contentId": "text-1",
                    "role": "ASSISTANT",
                    "type": "TEXT",
                    "additionalModelFields": '{"generationStage":"FINAL"}',
                    "textOutputConfiguration": {"mediaType": "text/plain"},
                }
            },
            {
                "textOutput": {
                    **identity,
                    "contentId": "text-1",
                    "content": transcript,
                }
            },
            {
                "contentEnd": {
                    **identity,
                    "contentId": "text-1",
                    "stopReason": "END_TURN",
                    "type": "TEXT",
                }
            },
            {"usageEvent": {**identity, "details": {}}},
            {"completionEnd": {**identity, "stopReason": "END_TURN"}},
        )
    )
    return tuple(events)


def _event_bytes(events: tuple[dict[str, object], ...]) -> bytes:
    return "".join(
        json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"
        for event in events
    ).encode("utf-8")


def _segment_snapshot(
    segment_id: str,
    ordinal: int,
    start: int,
    text: str,
) -> SegmentSnapshot:
    tokens = tuple(normalized_tokens(text, "frontier-word-sequence-v1"))
    return SegmentSnapshot(
        segment_id=segment_id,
        ordinal=ordinal,
        paragraph_index=ordinal - 1,
        start_token_index=start,
        end_token_index=start + len(tokens),
        text_sha256=sha256_text(" ".join(text.split())),
        normalized_tokens_sha256=canonical_sha256(tokens),
        context_before_sha256=None,
        context_after_sha256=None,
        render_config_sha256=_hash("6"),
        render_identity_sha256=canonical_sha256(
            {"segment_id": segment_id, "text": text}
        ),
        spoken_token_count=len(tokens),
        narration_only_punctuation=False,
    )


def _fixture(tmp_path: Path) -> ValidationFixture:
    workspace = tmp_path
    source_path = (
        workspace
        / "The Final Frontier Novel"
        / "chapters"
        / "discovery-part"
        / "discovery-part-001-validation.md"
    )
    source_path.parent.mkdir(parents=True)
    source_bytes = b"frozen local source fixture\n"
    source_path.write_bytes(source_bytes)

    texts = ("Alpha one two.", "Bravo three four.")
    first = _segment_snapshot("segment-001", 1, 0, texts[0])
    second = _segment_snapshot(
        "segment-002", 2, first.end_token_index, texts[1]
    )
    segments = (first, second)
    spoken = " ".join(texts)
    source = SourceSnapshot(
        track_id="chapter-001",
        source_path=source_path.relative_to(workspace).as_posix(),
        source_section=None,
        source_kind=SourceKind.CHAPTER,
        raw_sha256=sha256_bytes(source_bytes),
        normalized_body_sha256=sha256_text(spoken),
        spoken_sha256=sha256_text(spoken),
        declared_word_count=sum(item.spoken_token_count for item in segments),
        normalized_word_count=sum(item.spoken_token_count for item in segments),
        spoken_token_count=sum(item.spoken_token_count for item in segments),
        segment_count=len(segments),
        segmentation_policy="safe-narration-punctuation-v3",
        render_identity_schema="frontier-render-identity-v1",
        render_context_radius=0,
        segments=segments,
    )
    effective = EffectiveTrackConfig(
        track_id="chapter-001",
        track_kind=TrackKind.CHAPTER,
        sequence=1,
        voice="tiffany",
        model_id="amazon.nova-2-sonic-v1:0",
        region="us-east-1",
        profile_label="frontier-audiobook",
        target_segment_words=5,
        fidelity_policy=FidelityPolicy.EXACT,
        normalization="frontier-word-sequence-v1",
        audio_format=AudioFormat(24000, 16, 1, AudioEncoding.PCM_S16LE),
        output_path=(
            "audiobook-studio/dist/audiobook/the-final-frontier/"
            "001-chapter-001-tiffany.wav"
        ),
        resolution_provenance={
            "voice": "global-defaults",
            "model_id": "global-defaults",
            "region": "global-defaults",
        },
    )
    command = (
        "python",
        "-m",
        "frontier_audiobook",
        "production-worker",
        "--track",
        "chapter-001",
    )
    track = FrozenTrackPlan(
        transaction_id="plan-validation-chapter-001",
        track_id="chapter-001",
        sequence=1,
        effective_config=effective,
        source=source,
        command_argv=command,
        command_sha256=canonical_sha256(command),
        maximum_new_calls=2,
        legacy_candidates=(),
        protected_inventory_sha256=_hash("7"),
    )
    plan = seal_record(
        FrozenBatchPlan(
            schema_version=RECORD_SCHEMA_VERSION,
            plan_id="plan-validation",
            created_at_utc="2026-09-15T12:00:00Z",
            book_id="the-final-frontier",
            config_path="audiobook-studio/config/production.toml",
            config_sha256=_hash("8"),
            selectors=("chapter:1",),
            tracks=(track,),
            canonical_sha256="",
        )
    )
    plan_path = (
        workspace
        / "audiobook-studio"
        / "build"
        / "production"
        / plan.book_id
        / "plans"
        / plan.plan_id
        / "plan.json"
    )
    plan_path.parent.mkdir(parents=True)
    StrictRecordCodec(FrozenBatchPlan).write_atomic(plan_path, plan)

    store = TransactionStore(plan_path.parents[2], plan.book_id)
    store.materialize_plan(plan, occurred_at_utc="2026-09-15T12:00:00Z")
    store.append_transition(
        track.track_id,
        track.transaction_id,
        operation_id="preflight-passed",
        event_type="preflight-passed",
        state_after=TransactionState.PREFLIGHT_PASSED,
        details={"preflight_sha256": _hash("9")},
        occurred_at_utc="2026-09-15T12:00:01Z",
    )
    store.append_transition(
        track.track_id,
        track.transaction_id,
        operation_id="authorization-required",
        event_type="authorization-required",
        state_after=TransactionState.AUTHORIZATION_REQUIRED,
        details={"preflight_sha256": _hash("9")},
        occurred_at_utc="2026-09-15T12:00:02Z",
    )
    authorization_sha256 = _hash("a")
    store.append_transition(
        track.track_id,
        track.transaction_id,
        operation_id="attempt-001-authorization-consumed",
        event_type="authorization-consumed",
        state_after=TransactionState.RUNNING,
        details={
            "attempt_id": "attempt-001",
            "authorization_sha256": authorization_sha256,
            "command_sha256": track.command_sha256,
            "maximum_new_calls": track.maximum_new_calls,
            "one_shot": True,
            "automatic_retry_performed": False,
        },
        occurred_at_utc="2026-09-15T12:00:03Z",
    )

    transaction_root = store.transaction_path(track.track_id, track.transaction_id)
    attempt_root = transaction_root / "attempts" / "attempt-001"
    attempt_root.mkdir(parents=True)
    console_path = attempt_root / "render-console.log"
    console = (
        json.dumps(
            {
                "schema_version": RECORD_SCHEMA_VERSION,
                "event": "child-output-chunk",
                "sequence": 1,
                "byte_count": 1,
                "sha256": _hash("9"),
            },
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        + b"\n"
    )
    console_path.write_bytes(console)
    result = AttemptResult(
        schema_version=RECORD_SCHEMA_VERSION,
        attempt_id="attempt-001",
        transaction_id=track.transaction_id,
        authorization_sha256=authorization_sha256,
        working_directory=".",
        argv=track.command_argv,
        command_sha256=track.command_sha256,
        profile_label=track.effective_config.profile_label,
        started_at_utc="2026-09-15T12:00:03Z",
        ended_at_utc="2026-09-15T12:00:04Z",
        child_launched=True,
        native_return_code=0,
        termination_signal=None,
        console_path=console_path.relative_to(workspace).as_posix(),
        console_sha256=sha256_bytes(console),
        automatic_retry_performed=False,
        environment_persisted=False,
    )
    result_codec = StrictRecordCodec(AttemptResult)
    result_codec.write_atomic(attempt_root / "attempt.json", result)
    store.append_transition(
        track.track_id,
        track.transaction_id,
        operation_id="attempt-001-rendered",
        event_type="attempt-rendered",
        state_after=TransactionState.RENDERED,
        details={
            "attempt_id": result.attempt_id,
            "authorization_sha256": result.authorization_sha256,
            "attempt_result_sha256": result_codec.sha256(result),
            "console_sha256": result.console_sha256,
            "native_return_code": 0,
            "termination_signal": None,
            "automatic_retry_performed": False,
        },
        occurred_at_utc="2026-09-15T12:00:04Z",
    )

    runtime = transaction_root / "runtime"
    for directory in (runtime / "segments", runtime / "transcripts", runtime / "events"):
        directory.mkdir(parents=True)
    active: list[dict[str, object]] = []
    stitch_parts: list[narrate.StitchSegment] = []
    for ordinal, (snapshot, text) in enumerate(zip(segments, texts, strict=True), start=1):
        stem = f"{snapshot.segment_id}-{snapshot.text_sha256}"
        audio_path = runtime / "segments" / f"{stem}.wav"
        transcript_path = runtime / "transcripts" / f"{stem}.txt"
        event_path = runtime / "events" / f"{stem}.jsonl"
        lpcm = (ordinal * 1000).to_bytes(2, "little", signed=True) * 2400
        audio = _wav_bytes(lpcm)
        transcript = (text + "\n").encode("utf-8")
        events = _event_bytes(_output_events(text, lpcm))
        audio_path.write_bytes(audio)
        transcript_path.write_bytes(transcript)
        event_path.write_bytes(events)
        stitch_parts.append(
            narrate.StitchSegment(
                narrate.Segment(
                    ordinal,
                    snapshot.paragraph_index,
                    text,
                    snapshot.narration_only_punctuation,
                ),
                lpcm,
                event_path,
            )
        )
        active.append(
            {
                "segment_id": snapshot.segment_id,
                "paragraph_index": snapshot.paragraph_index,
                "text": text,
                "text_sha256": snapshot.text_sha256,
                "render_identity_sha256": snapshot.render_identity_sha256,
                "word_count": snapshot.spoken_token_count,
                "narration_only_punctuation": False,
                "status": "narrated",
                "audio_path": audio_path.relative_to(workspace).as_posix(),
                "audio_sha256": sha256_bytes(audio),
                "transcript_path": transcript_path.relative_to(workspace).as_posix(),
                "transcript_sha256": sha256_bytes(transcript),
                "event_journal_path": event_path.relative_to(workspace).as_posix(),
                "event_journal_sha256": sha256_bytes(events),
                "duration_seconds": 0.1,
                "transcript": text,
                "exact_transcript_match": True,
                "coverage_ratio": 1.0,
                "event_replay_passed": True,
                "mid_sentence_partial_turns": 0,
                "rendered_in_current_attempt": True,
                "call_ordinal": ordinal,
                "narrated_at": f"2026-09-15T12:00:0{4 + ordinal}Z",
            }
        )
    stitch_settings = narrate.StitchAudioSettings(24000, 16, 1)
    track_lpcm = narrate.stitch_track_lpcm(tuple(stitch_parts), stitch_settings)
    track_audio_path = runtime / Path(effective.output_path).name
    track_audio = _wav_bytes(track_lpcm)
    track_audio_path.write_bytes(track_audio)
    manifest = {
        "track_id": track.track_id,
        "transaction_id": track.transaction_id,
        "track_plan_sha256": canonical_sha256(track),
        "effective_config_sha256": canonical_sha256(effective),
        "source_snapshot_sha256": canonical_sha256(source),
        "track_kind": effective.track_kind.value,
        "sequence": track.sequence,
        "voice_id": effective.voice,
        "model_id": effective.model_id,
        "region": effective.region,
        "profile_label": effective.profile_label,
        "fidelity_policy": effective.fidelity_policy.value,
        "normalization": effective.normalization,
        "audio_sample_rate_hz": effective.audio_format.sample_rate_hz,
        "audio_sample_size_bits": effective.audio_format.sample_size_bits,
        "audio_channels": effective.audio_format.channels,
        "audio_encoding": effective.audio_format.encoding.value,
        "output_path": effective.output_path,
        "source_path": source.source_path,
        "source_kind": source.source_kind.value,
        "source_section": source.source_section,
        "source_sha256": source.raw_sha256,
        "normalized_body_sha256": source.normalized_body_sha256,
        "spoken_sha256": source.spoken_sha256,
        "declared_word_count": source.declared_word_count,
        "normalized_word_count": source.normalized_word_count,
        "word_count": source.spoken_token_count,
        "spoken_token_count": source.spoken_token_count,
        "segment_count": source.segment_count,
        "active_segment_count": source.segment_count,
        "narration_only_punctuation_segments": 0,
        "target_segment_words": effective.target_segment_words,
        "safe_request_max_characters": 1000,
        "safe_request_max_words": 100,
        "segment_boundary_policy": source.segmentation_policy,
        "render_identity_schema": source.render_identity_schema,
        "render_context_radius": source.render_context_radius,
        "maximum_new_calls": track.maximum_new_calls,
        "billable_calls_made": 2,
        "segments": active,
        "carried_over_segments": [],
        "track_audio_path": track_audio_path.relative_to(workspace).as_posix(),
        "track_audio_sha256": sha256_bytes(track_audio),
        "track_audio_byte_count": len(track_audio),
        "track_duration_seconds": narrate.assembled_lpcm_duration_seconds(
            track_lpcm,
            stitch_settings,
        ),
        "stitching": narrate.stitch_profile(),
        "updated_at": "2026-09-15T12:00:07Z",
    }
    manifest_path = runtime / "manifest.json"
    _write_json(manifest_path, manifest)

    protected_path = (
        workspace
        / ".kiro"
        / "specs"
        / "chapter-3-audio-proof"
        / "protected-sentinel"
    )
    protected_path.parent.mkdir(parents=True)
    protected_path.write_bytes(b"protected-historical-evidence")
    return ValidationFixture(
        workspace,
        plan_path,
        plan,
        track,
        store,
        transaction_root,
        attempt_root,
        manifest_path,
        protected_path,
    )


def _validate(fixture: ValidationFixture) -> ValidationEvidence:
    return validate_frozen_track_manifest(
        fixture.workspace,
        fixture.plan_path,
        fixture.track.track_id,
        fixture.track.transaction_id,
        validated_at_utc="2026-09-15T12:00:08Z",
    )


def _manifest(fixture: ValidationFixture) -> dict[str, object]:
    return json.loads(fixture.manifest_path.read_text(encoding="utf-8"))


def _check(evidence: ValidationEvidence, check_id: str):
    return next(item for item in evidence.checks if item.check_id == check_id)


def test_native_zero_exact_fidelity_produces_only_sanitized_evidence(tmp_path):
    fixture = _fixture(tmp_path)
    protected_before = fixture.protected_path.read_bytes()

    evidence = _validate(fixture)

    assert evidence.status is ValidationStatus.PASSED
    assert evidence.delivery_gate_passed is True
    assert all(item.status is ValidationStatus.PASSED for item in evidence.checks)
    assert _check(evidence, "assembly.source-current").status is ValidationStatus.PASSED
    assert _check(evidence, "assembly.stitching").status is ValidationStatus.PASSED
    assert _check(evidence, "assembly.wav-integrity").status is ValidationStatus.PASSED
    sanitization = _check(evidence, "evidence.sanitization")
    assert sanitization.status is ValidationStatus.PASSED
    assert sanitization.artifact_path is not None
    evidence_path = validation_evidence_path(fixture.transaction_root, evidence)
    persisted = StrictRecordCodec(ValidationEvidence).load(evidence_path)
    assert persisted == evidence
    encoded = StrictRecordCodec(ValidationEvidence).dump_bytes(evidence)
    assert b"Alpha one two" not in encoded
    assert b"Bravo three four" not in encoded
    assert b"audioOutput" not in encoded
    assert b"/transcripts/" not in encoded
    assert b"/events/" not in encoded
    assert fixture.protected_path.read_bytes() == protected_before


def test_failed_validation_evidence_remains_immutable_when_later_validation_passes(
    tmp_path,
):
    fixture = _fixture(tmp_path)
    original_manifest = fixture.manifest_path.read_bytes()
    malformed = _manifest(fixture)
    malformed["private_prose_copy"] = "failed private value must not enter evidence"
    _write_json(fixture.manifest_path, malformed)

    failed = _validate(fixture)
    assert failed.status is ValidationStatus.BLOCKED
    failed_path = validation_evidence_path(fixture.transaction_root, failed)
    failed_bytes = failed_path.read_bytes()
    assert b"failed private value" not in failed_bytes

    fixture.manifest_path.write_bytes(original_manifest)
    passed = _validate(fixture)
    assert passed.status is ValidationStatus.PASSED
    passed_path = validation_evidence_path(fixture.transaction_root, passed)

    assert passed_path != failed_path
    assert failed_path.read_bytes() == failed_bytes
    assert StrictRecordCodec(ValidationEvidence).load(failed_path) == failed
    assert StrictRecordCodec(ValidationEvidence).load(passed_path) == passed

    selected, selected_path = load_passing_validation_evidence(
        fixture.transaction_root,
        transaction_id=fixture.track.transaction_id,
        track_id=fixture.track.track_id,
        plan_sha256=StrictRecordCodec(FrozenBatchPlan).sha256(fixture.plan),
        manifest_sha256=passed.manifest_sha256,
    )
    assert selected == passed
    assert selected_path == passed_path
    assert failed_path.read_bytes() == failed_bytes


@pytest.mark.parametrize("case", ("missing", "malformed", "ambiguous", "nonzero"))
def test_missing_malformed_ambiguous_or_nonzero_attempt_blocks_delivery_gate(
    tmp_path,
    case,
):
    fixture = _fixture(tmp_path)
    result_path = fixture.attempt_root / "attempt.json"
    if case == "missing":
        shutil.rmtree(fixture.attempt_root)
    elif case == "malformed":
        result_path.write_bytes(b"{")
    elif case == "ambiguous":
        (fixture.attempt_root.parent / "attempt-002.staging-local").mkdir()
    else:
        result = StrictRecordCodec(AttemptResult).load(result_path)
        StrictRecordCodec(AttemptResult).write_atomic(
            result_path,
            replace(result, native_return_code=7),
        )

    evidence = _validate(fixture)

    attempt = _check(evidence, "attempt.committed-native-zero")
    assert attempt.status is ValidationStatus.BLOCKED
    assert attempt.finding_category == "attempt-evidence-invalid"
    assert attempt.finding_count >= 1
    assert evidence.status is ValidationStatus.BLOCKED
    assert evidence.delivery_gate_passed is False


@pytest.mark.parametrize(
    ("field", "replacement"),
    (
        ("track_id", "chapter-099"),
        ("model_id", "different-model"),
        ("source_sha256", _hash("f")),
        ("target_segment_words", 6),
        ("source_snapshot_sha256", _hash("e")),
    ),
)
def test_every_frozen_manifest_binding_must_match_the_exact_track_plan(
    tmp_path,
    field,
    replacement,
):
    fixture = _fixture(tmp_path)
    manifest = _manifest(fixture)
    manifest[field] = replacement
    _write_json(fixture.manifest_path, manifest)

    evidence = _validate(fixture)

    binding = _check(evidence, "manifest.frozen-plan-binding")
    assert binding.status is ValidationStatus.BLOCKED
    assert binding.finding_category == "manifest-plan-binding-invalid"
    assert evidence.delivery_gate_passed is False


@pytest.mark.parametrize(
    ("case", "check_id"),
    (
        ("count", "manifest.active-set"),
        ("duplicate", "manifest.active-set"),
        ("reordered", "manifest.active-set"),
        ("token", "manifest.token-conservation"),
        ("rejected-active", "manifest.history-exclusion"),
    ),
)
def test_active_count_identity_order_tokens_and_status_are_fail_closed(
    tmp_path,
    case,
    check_id,
):
    fixture = _fixture(tmp_path)
    manifest = _manifest(fixture)
    segments = manifest["segments"]
    assert isinstance(segments, list)
    if case == "count":
        manifest["active_segment_count"] = 1
    elif case == "duplicate":
        segments[1]["segment_id"] = segments[0]["segment_id"]
    elif case == "reordered":
        manifest["segments"] = list(reversed(segments))
    elif case == "token":
        segments[0]["text"] = "Different token sequence."
    else:
        segments[0]["status"] = "rejected"
    _write_json(fixture.manifest_path, manifest)

    evidence = _validate(fixture)

    assert _check(evidence, check_id).status is ValidationStatus.BLOCKED
    if case == "reordered":
        assert _check(evidence, "assembly.stitching").status is ValidationStatus.BLOCKED
    assert evidence.delivery_gate_passed is False


@pytest.mark.parametrize("case", ("missing", "malformed", "unknown", "escape", "symlink"))
def test_manifest_schema_and_runtime_paths_block_missing_malformed_or_unsafe_input(
    tmp_path,
    case,
):
    fixture = _fixture(tmp_path)
    if case == "missing":
        fixture.manifest_path.unlink()
        expected = "manifest.schema"
    elif case == "malformed":
        fixture.manifest_path.write_bytes(b'{"track_id":')
        expected = "manifest.schema"
    else:
        manifest = _manifest(fixture)
        if case == "unknown":
            manifest["private_prose_copy"] = "must not be accepted"
            expected = "manifest.schema"
        elif case == "escape":
            manifest["segments"][0]["audio_path"] = "outside-runtime.wav"
            (fixture.workspace / "outside-runtime.wav").write_bytes(b"outside")
            expected = "manifest.path-confinement"
        else:
            active_path = fixture.workspace / manifest["segments"][0]["audio_path"]
            active_path.unlink()
            outside = fixture.workspace / "outside-audio.wav"
            outside.write_bytes(b"outside")
            active_path.symlink_to(outside)
            expected = "manifest.path-confinement"
        _write_json(fixture.manifest_path, manifest)

    evidence = _validate(fixture)

    assert _check(evidence, expected).status is ValidationStatus.BLOCKED
    assert evidence.delivery_gate_passed is False
    encoded = StrictRecordCodec(ValidationEvidence).dump_bytes(evidence)
    assert b"must not be accepted" not in encoded


def test_explicit_historical_rejected_and_carried_buckets_are_excluded_from_active_totals(
    tmp_path,
):
    fixture = _fixture(tmp_path)
    manifest = _manifest(fixture)
    runtime_relative = (
        fixture.transaction_root / "runtime" / "segments" / "old-rejected.wav"
    ).relative_to(fixture.workspace).as_posix()
    nonactive = {
        "segment_id": "segment-999",
        "status": "rejected",
        "word_count": 999999,
        "text": "Historical private body must not enter evidence or active totals.",
        "text_sha256": _hash("b"),
        "audio_path": runtime_relative,
        "audio_sha256": _hash("c"),
    }
    manifest["carried_over_segments"] = [dict(nonactive)]
    manifest["historical_segments"] = [dict(nonactive, segment_id="segment-998")]
    manifest["rejected_segments"] = [dict(nonactive, segment_id="segment-997")]
    _write_json(fixture.manifest_path, manifest)

    evidence = _validate(fixture)

    assert evidence.status is ValidationStatus.PASSED
    assert evidence.delivery_gate_passed is True
    assert _check(evidence, "manifest.active-set").status is ValidationStatus.PASSED
    assert _check(evidence, "manifest.token-conservation").status is ValidationStatus.PASSED
    encoded = StrictRecordCodec(ValidationEvidence).dump_bytes(evidence)
    assert b"Historical private body" not in encoded


@pytest.mark.parametrize(
    ("case", "check_id"),
    (
        ("audio-hash", "fidelity.hash-bindings"),
        ("transcript-hash", "fidelity.hash-bindings"),
        ("event-hash", "fidelity.hash-bindings"),
        ("transcript-content", "fidelity.exact-transcript"),
        ("coverage-record", "fidelity.exact-transcript"),
        ("event-structure", "fidelity.event-replay"),
        ("event-transcript", "fidelity.event-replay"),
        ("event-lpcm", "fidelity.lpcm-equality"),
        ("partial-turn", "fidelity.partial-turns"),
    ),
)
def test_exact_transcript_replay_lpcm_hash_and_partial_turn_failures_block_delivery(
    tmp_path,
    case,
    check_id,
):
    fixture = _fixture(tmp_path)
    manifest = _manifest(fixture)
    entries = manifest["segments"]
    assert isinstance(entries, list)
    entry = entries[0]
    assert isinstance(entry, dict)
    transcript_path = fixture.workspace / str(entry["transcript_path"])
    event_path = fixture.workspace / str(entry["event_journal_path"])
    original_lpcm = (1000).to_bytes(2, "little", signed=True) * 2400

    if case == "audio-hash":
        entry["audio_sha256"] = _hash("f")
    elif case == "transcript-hash":
        entry["transcript_sha256"] = _hash("f")
    elif case == "event-hash":
        entry["event_journal_sha256"] = _hash("f")
    elif case == "transcript-content":
        changed = b"Private altered transcript body.\n"
        transcript_path.write_bytes(changed)
        entry["transcript_sha256"] = sha256_bytes(changed)
    elif case == "coverage-record":
        entry["coverage_ratio"] = 0.5
    elif case == "event-structure":
        changed = b'{"completionStart":{}}\n'
        event_path.write_bytes(changed)
        entry["event_journal_sha256"] = sha256_bytes(changed)
    else:
        expected_text = str(entry["text"])
        event_text = (
            "Private altered event transcript."
            if case == "event-transcript"
            else expected_text
        )
        event_lpcm = (
            b"\x09\x00" * 2400 if case == "event-lpcm" else original_lpcm
        )
        changed = _event_bytes(
            _output_events(
                event_text,
                event_lpcm,
                unsafe_partial_turn=case == "partial-turn",
            )
        )
        event_path.write_bytes(changed)
        entry["event_journal_sha256"] = sha256_bytes(changed)
    _write_json(fixture.manifest_path, manifest)

    evidence = _validate(fixture)

    check = _check(evidence, check_id)
    assert check.status is ValidationStatus.BLOCKED
    assert check.finding_count >= 1
    assert evidence.status is ValidationStatus.BLOCKED
    assert evidence.delivery_gate_passed is False
    encoded = StrictRecordCodec(ValidationEvidence).dump_bytes(evidence)
    assert b"Private altered" not in encoded


def test_current_source_hash_is_revalidated_before_assembly_validation(tmp_path):
    fixture = _fixture(tmp_path)
    source_path = fixture.workspace / fixture.track.source.source_path
    source_path.write_text("Private changed source must not enter evidence.\n", encoding="utf-8")

    evidence = _validate(fixture)

    source_check = _check(evidence, "assembly.source-current")
    assert source_check.status is ValidationStatus.BLOCKED
    assert source_check.finding_category == "assembly-source-invalid"
    assert _check(evidence, "assembly.stitching").status is ValidationStatus.BLOCKED
    assert evidence.delivery_gate_passed is False
    encoded = StrictRecordCodec(ValidationEvidence).dump_bytes(evidence)
    assert b"Private changed source" not in encoded


def test_complete_stitch_profile_is_required_for_delivery(tmp_path):
    fixture = _fixture(tmp_path)
    manifest = _manifest(fixture)
    stitching = manifest["stitching"]
    assert isinstance(stitching, dict)
    stitching["paragraph_gap_seconds"] = 9.0
    _write_json(fixture.manifest_path, manifest)

    evidence = _validate(fixture)

    check = _check(evidence, "assembly.stitching")
    assert check.status is ValidationStatus.BLOCKED
    assert check.finding_category == "assembly-stitching-invalid"
    assert evidence.delivery_gate_passed is False


@pytest.mark.parametrize(
    ("case", "check_id"),
    (
        ("lpcm", "assembly.stitching"),
        ("byte-count", "assembly.wav-integrity"),
        ("sha256", "assembly.wav-integrity"),
        ("duration", "assembly.wav-integrity"),
        ("sample-rate", "assembly.wav-integrity"),
        ("compressed", "assembly.wav-integrity"),
    ),
)
def test_assembled_lpcm_wav_format_size_digest_and_duration_are_exact(
    tmp_path,
    case,
    check_id,
):
    fixture = _fixture(tmp_path)
    manifest = _manifest(fixture)
    track_audio_path = fixture.workspace / str(manifest["track_audio_path"])
    track_audio = track_audio_path.read_bytes()
    with wave.open(BytesIO(track_audio), "rb") as handle:
        lpcm = handle.readframes(handle.getnframes())

    if case == "lpcm":
        changed_lpcm = bytearray(lpcm)
        midpoint = (len(changed_lpcm) // 4) * 2
        changed_lpcm[midpoint : midpoint + 2] = (3000).to_bytes(
            2,
            "little",
            signed=True,
        )
        changed = _wav_bytes(bytes(changed_lpcm))
        track_audio_path.write_bytes(changed)
        manifest["track_audio_sha256"] = sha256_bytes(changed)
        manifest["track_audio_byte_count"] = len(changed)
    elif case == "byte-count":
        manifest["track_audio_byte_count"] = len(track_audio) + 1
    elif case == "sha256":
        manifest["track_audio_sha256"] = _hash("f")
    elif case == "duration":
        manifest["track_duration_seconds"] = float(
            manifest["track_duration_seconds"]
        ) + 0.01
    elif case == "sample-rate":
        changed = _wav_bytes(lpcm, sample_rate_hz=16000)
        track_audio_path.write_bytes(changed)
        manifest["track_audio_sha256"] = sha256_bytes(changed)
        manifest["track_audio_byte_count"] = len(changed)
    else:
        changed_header = bytearray(track_audio)
        changed_header[20:22] = (3).to_bytes(2, "little")
        changed = bytes(changed_header)
        track_audio_path.write_bytes(changed)
        manifest["track_audio_sha256"] = sha256_bytes(changed)
        manifest["track_audio_byte_count"] = len(changed)
    _write_json(fixture.manifest_path, manifest)

    evidence = _validate(fixture)

    check = _check(evidence, check_id)
    assert check.status is ValidationStatus.BLOCKED
    assert check.finding_count >= 1
    assert evidence.status is ValidationStatus.BLOCKED
    assert evidence.delivery_gate_passed is False
