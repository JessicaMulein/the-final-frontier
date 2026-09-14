from __future__ import annotations

import base64
import json
import socket
import subprocess
import wave
from dataclasses import replace
from io import BytesIO
from pathlib import Path

import pytest

from frontier_audiobook import narrate
from frontier_audiobook.errors import InputError
from frontier_audiobook.production import (
    ProductionSelectors,
    create_production_plan,
    load_production_plan,
)
from frontier_audiobook.production_models import (
    AuthorizationDecision,
    FrozenBatchPlan,
    PaidAuthorization,
    StrictRecordCodec,
    TransactionState,
    authorization_confirmation_sha256,
    seal_record,
)
from frontier_audiobook.production_resume import (
    DuplicateChargeDecision,
    ManualResolutionDisposition,
    ResumeClassification,
    create_exact_duplicate_charge_acknowledgement,
    inspect_resume,
    resolve_resume,
    validate_replacement_paid_attempt_requirements,
)
from frontier_audiobook.production_transactions import TransactionStore
from frontier_audiobook.util import sha256_bytes

AUDITION_CONFIG = Path(__file__).parents[1] / "config" / "audition.toml"
CHAPTER_TEXT = "Alpha one two three."


@pytest.fixture(autouse=True)
def deny_every_external_or_paid_boundary(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("resume and manual resolution must remain offline and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(subprocess, "Popen", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")


def _tree_bytes(root: Path) -> dict[str, bytes]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def _write_workspace(workspace: Path) -> Path:
    chapter = (
        workspace
        / "The Final Frontier Novel"
        / "chapters"
        / "discovery-part"
        / "discovery-part-003-third-signal.md"
    )
    chapter.parent.mkdir(parents=True)
    chapter.write_text(
        "\n".join(
            (
                "---",
                "movement: discovery",
                "chapter: 3",
                "pov_id: test-pov",
                "timeline_id: test-timeline",
                "motif_events: none",
                "hook: test-hook",
                "words: 4",
                "length_class: short",
                "status: draft",
                "---",
                CHAPTER_TEXT,
                "",
            )
        ),
        encoding="utf-8",
    )
    config = workspace / ".audiobook" / "config" / "production.toml"
    config.parent.mkdir(parents=True)
    config.write_text(
        '''schema_version = 1
book_id = "the-final-frontier"
manuscript_root = "The Final Frontier Novel"
build_root = ".audiobook/build/production"
delivery_root = ".audiobook/dist/audiobook"
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
    (workspace / ".audiobook" / "config" / "audition.toml").write_bytes(
        AUDITION_CONFIG.read_bytes()
    )
    return config


def _create_plan(workspace: Path, plan_id: str):
    config = workspace / ".audiobook" / "config" / "production.toml"
    plan_path = create_production_plan(
        config,
        ProductionSelectors.from_cli(chapters=[3]),
        plan_id=plan_id,
        workspace_root=workspace,
        created_at_utc="2026-09-14T12:00:00Z",
    )
    return plan_path, load_production_plan(plan_path)


def _authorization(plan: FrozenBatchPlan, preflight_sha256: str, authorization_id: str):
    track = plan.tracks[0]
    challenge = "a" * 64
    display_sha256 = "b" * 64
    confirmed_at_utc = "2026-09-14T12:00:30Z"
    decision = AuthorizationDecision.AUTHORIZE_EXACT_SCOPE
    return seal_record(
        PaidAuthorization(
            schema_version=1,
            authorization_id=authorization_id,
            plan_sha256=StrictRecordCodec(FrozenBatchPlan).sha256(plan),
            preflight_sha256=preflight_sha256,
            local_preflight_sha256="c" * 64,
            estimate_sha256="d" * 64,
            official_rate_provenance_sha256="e" * 64,
            exact_transaction_ids=tuple(item.transaction_id for item in plan.tracks),
            exact_track_ids=tuple(item.track_id for item in plan.tracks),
            exact_command_sha256s=tuple(item.command_sha256 for item in plan.tracks),
            maximum_new_calls_by_track={
                item.track_id: item.maximum_new_calls for item in plan.tracks
            },
            maximum_new_calls_total=sum(
                item.maximum_new_calls for item in plan.tracks
            ),
            estimated_pre_tax_usd="0.01",
            operator_approved_max_estimated_pre_tax_usd="1.00",
            issued_at_utc="2026-09-14T12:00:00Z",
            expires_at_utc="2026-09-14T13:00:00Z",
            one_shot=True,
            confirmation_challenge=challenge,
            confirmation_display_sha256=display_sha256,
            confirmation_decision=decision,
            confirmed_at_utc=confirmed_at_utc,
            confirmation_sha256=authorization_confirmation_sha256(
                display_sha256=display_sha256,
                challenge=challenge,
                decision=decision,
                confirmed_at_utc=confirmed_at_utc,
            ),
            canonical_sha256="",
        )
    )


def _prepare_transaction(workspace: Path, plan_path: Path, plan: FrozenBatchPlan):
    track = plan.tracks[0]
    preflight_sha256 = "f" * 64
    authorization = _authorization(plan, preflight_sha256, "authorization-resume-test")
    store = TransactionStore(
        workspace / ".audiobook" / "build" / "production" / plan.book_id,
        plan.book_id,
    )
    store.materialize_plan(plan, occurred_at_utc="2026-09-14T12:00:00Z")
    store.append_transition(
        track.track_id,
        track.transaction_id,
        operation_id="preflight-passed",
        event_type="preflight-passed",
        state_after=TransactionState.PREFLIGHT_PASSED,
        details={"preflight_sha256": preflight_sha256},
        occurred_at_utc="2026-09-14T12:00:01Z",
    )
    store.append_transition(
        track.track_id,
        track.transaction_id,
        operation_id="authorization-required",
        event_type="authorization-required",
        state_after=TransactionState.AUTHORIZATION_REQUIRED,
        details={"preflight_sha256": preflight_sha256},
        occurred_at_utc="2026-09-14T12:00:02Z",
    )
    authorization_path = plan_path.parent / "authorizations" / "authorization-resume-test.json"
    StrictRecordCodec(PaidAuthorization).write_atomic(authorization_path, authorization)
    return track, authorization, store


def _consume_uncertain(track, authorization, store):
    authorization_sha256 = StrictRecordCodec(PaidAuthorization).sha256(authorization)
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
        occurred_at_utc="2026-09-14T12:00:03Z",
    )
    attempts = store.transaction_path(track.track_id, track.transaction_id) / "attempts"
    attempts.mkdir()
    (attempts / "attempt-001.ambiguous.json").write_text(
        json.dumps(
            {
                "schema_version": 1,
                "attempt_id": "attempt-001",
                "transaction_id": track.transaction_id,
                "authorization_sha256": authorization_sha256,
                "finding_category": "incomplete-launched-attempt-evidence",
                "child_launch_status": "confirmed",
                "automatic_retry_performed": False,
                "environment_persisted": False,
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        encoding="utf-8",
    )
    store.append_transition(
        track.track_id,
        track.transaction_id,
        operation_id="attempt-001-charge-uncertain",
        event_type="attempt-charge-uncertain",
        state_after=TransactionState.CHARGE_UNCERTAIN,
        details={
            "attempt_id": "attempt-001",
            "authorization_sha256": authorization_sha256,
            "finding_category": "incomplete-launched-attempt-evidence",
            "child_launch_status": "confirmed",
            "automatic_retry_performed": False,
        },
        occurred_at_utc="2026-09-14T12:00:04Z",
    )


def _wav_bytes(lpcm: bytes) -> bytes:
    output = BytesIO()
    with wave.open(output, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(lpcm)
    return output.getvalue()


def _events(transcript: str, lpcm: bytes) -> tuple[dict[str, object], ...]:
    identity = {
        "sessionId": "session-1",
        "promptName": "prompt-1",
        "completionId": "completion-1",
    }
    return (
        {"completionStart": dict(identity)},
        {
            "contentStart": {
                **identity,
                "contentId": "audio-1",
                "role": "ASSISTANT",
                "type": "AUDIO",
                "audioOutputConfiguration": {
                    "mediaType": "audio/lpcm",
                    "sampleRateHertz": 24000,
                    "sampleSizeBits": 16,
                    "encoding": "base64",
                    "channelCount": 1,
                },
            }
        },
        {
            "audioOutput": {
                **identity,
                "contentId": "audio-1",
                "content": base64.b64encode(lpcm).decode("ascii"),
            }
        },
        {
            "contentEnd": {
                **identity,
                "contentId": "audio-1",
                "stopReason": "END_TURN",
                "type": "AUDIO",
            }
        },
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
        {
            "usageEvent": {
                **identity,
                "totalInputTokens": 1,
                "totalOutputTokens": 1,
                "totalTokens": 2,
                "details": {},
            }
        },
        {"completionEnd": {**identity, "stopReason": "END_TURN"}},
    )


def _write_complete_runtime(workspace: Path, track, store):
    transaction = store.transaction_path(track.track_id, track.transaction_id)
    runtime = transaction / "runtime"
    (runtime / "segments").mkdir(parents=True)
    (runtime / "transcripts").mkdir()
    (runtime / "events").mkdir()
    snapshot = track.source.segments[0]
    stem = f"{snapshot.segment_id}-{snapshot.text_sha256}"
    lpcm = b"\xe8\x03" * 2400
    audio = _wav_bytes(lpcm)
    audio_path = runtime / "segments" / f"{stem}.wav"
    transcript_path = runtime / "transcripts" / f"{stem}.txt"
    event_path = runtime / "events" / f"{stem}.jsonl"
    track_path = runtime / Path(track.effective_config.output_path).name
    audio_path.write_bytes(audio)
    transcript_path.write_text(CHAPTER_TEXT + "\n", encoding="utf-8")
    event_path.write_text(
        "".join(json.dumps(item, sort_keys=True) + "\n" for item in _events(CHAPTER_TEXT, lpcm)),
        encoding="utf-8",
    )
    track_path.write_bytes(audio)
    manifest = {
        "track_id": track.track_id,
        "voice_id": track.effective_config.voice,
        "source_path": track.source.source_path,
        "source_sha256": track.source.raw_sha256,
        "spoken_sha256": track.source.spoken_sha256,
        "word_count": track.source.spoken_token_count,
        "segment_count": track.source.segment_count,
        "narration_only_punctuation_segments": 0,
        "target_segment_words": track.effective_config.target_segment_words,
        "segment_boundary_policy": track.source.segmentation_policy,
        "track_kind": track.effective_config.track_kind.value,
        "source_kind": track.source.source_kind.value,
        "source_section": track.source.source_section,
        "sequence": track.sequence,
        "normalized_body_sha256": track.source.normalized_body_sha256,
        "spoken_token_count": track.source.spoken_token_count,
        "render_identity_schema": track.source.render_identity_schema,
        "active_segment_count": 1,
        "maximum_new_calls": track.maximum_new_calls,
        "billable_calls_made": 1,
        "segments": [
            {
                "segment_id": snapshot.segment_id,
                "paragraph_index": snapshot.paragraph_index,
                "text": CHAPTER_TEXT,
                "text_sha256": snapshot.text_sha256,
                "render_identity_sha256": snapshot.render_identity_sha256,
                "word_count": snapshot.spoken_token_count,
                "narration_only_punctuation": False,
                "status": "narrated",
                "audio_path": audio_path.relative_to(workspace).as_posix(),
                "audio_sha256": sha256_bytes(audio),
                "duration_seconds": 0.1,
                "transcript": CHAPTER_TEXT,
                "exact_transcript_match": True,
                "coverage_ratio": 1.0,
                "event_replay_passed": True,
                "mid_sentence_partial_turns": 0,
                "rendered_in_current_attempt": True,
                "call_ordinal": 1,
            }
        ],
        "carried_over_segments": [],
        "track_audio_path": track_path.relative_to(workspace).as_posix(),
        "track_audio_sha256": sha256_bytes(audio),
        "track_duration_seconds": 0.1,
        "stitching": {"profile": "sentence-boundary-partial-turn-v3"},
        "updated_at": "2026-09-14T12:00:05Z",
    }
    (runtime / "manifest.json").write_text(
        json.dumps(manifest, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )
    return runtime


def _uncertain_fixture(tmp_path: Path, *, complete_runtime: bool):
    config = _write_workspace(tmp_path)
    plan_path, plan = _create_plan(tmp_path, "plan-resume-original")
    track, authorization, store = _prepare_transaction(tmp_path, plan_path, plan)
    _consume_uncertain(track, authorization, store)
    runtime = (
        _write_complete_runtime(tmp_path, track, store)
        if complete_runtime
        else store.transaction_path(track.track_id, track.transaction_id) / "runtime"
    )
    protected = tmp_path / ".kiro" / "specs" / "chapter-3-audio-proof" / "sentinel.txt"
    protected.parent.mkdir(parents=True)
    protected.write_bytes(b"protected-historical-evidence")
    return config, plan_path, plan, track, store, runtime, protected


def test_inspection_returns_only_enumerated_nothing_and_recoverable_classifications(tmp_path):
    _write_workspace(tmp_path)
    plan_path, plan = _create_plan(tmp_path, "plan-resume-enumerated")
    track, _authorization_value, _store = _prepare_transaction(tmp_path, plan_path, plan)

    nothing = inspect_resume(tmp_path, plan_path, track.track_id, track.transaction_id)
    assert nothing.classification is ResumeClassification.NOTHING_TO_RESUME
    assert isinstance(nothing.classification, ResumeClassification)

    _config, plan_path, _plan, track, _store, _runtime, _protected = _uncertain_fixture(
        tmp_path / "uncertain", complete_runtime=False
    )
    uncertain = inspect_resume(
        tmp_path / "uncertain", plan_path, track.track_id, track.transaction_id
    )
    assert uncertain.classification is ResumeClassification.CHARGE_UNCERTAIN_REVIEW_REQUIRED
    assert uncertain.duplicate_charge_acknowledgement_required is True
    assert uncertain.future_paid_attempt_requirements == (
        "new-transaction",
        "new-plan",
        "new-preflight",
        "new-authorization",
    )


def test_accept_complete_local_artifacts_is_offline_idempotent_and_preserves_evidence(tmp_path):
    _config, plan_path, _plan, track, store, runtime, protected = _uncertain_fixture(
        tmp_path, complete_runtime=True
    )
    transaction = store.transaction_path(track.track_id, track.transaction_id)
    attempts = transaction / "attempts"
    before_attempts = _tree_bytes(attempts)
    before_runtime = _tree_bytes(runtime)
    before_protected = protected.read_bytes()

    inspection = inspect_resume(tmp_path, plan_path, track.track_id, track.transaction_id)
    assert inspection.classification is ResumeClassification.COMPLETE_ARTIFACTS_RECOVERABLE

    result = resolve_resume(
        tmp_path,
        plan_path,
        track.track_id,
        track.transaction_id,
        ManualResolutionDisposition.ACCEPT_COMPLETE_LOCAL_ARTIFACTS,
        occurred_at_utc="2026-09-14T12:00:06Z",
    )
    assert result.state_after is TransactionState.RENDERED
    assert result.evidence_retained is True
    assert result.future_paid_attempt_requirements == ()
    assert _tree_bytes(attempts) == before_attempts
    assert _tree_bytes(runtime) == before_runtime
    assert protected.read_bytes() == before_protected
    assert store.inspect_transaction(track.track_id, track.transaction_id).state is TransactionState.RENDERED
    assert inspect_resume(
        tmp_path, plan_path, track.track_id, track.transaction_id
    ).classification is ResumeClassification.LOCAL_VALIDATION_AVAILABLE

    event_count = len(store.inspect_transaction(track.track_id, track.transaction_id).events)
    repeated = resolve_resume(
        tmp_path,
        plan_path,
        track.track_id,
        track.transaction_id,
        ManualResolutionDisposition.ACCEPT_COMPLETE_LOCAL_ARTIFACTS,
        occurred_at_utc="2026-09-14T23:59:59Z",
    )
    assert repeated == result
    assert len(store.inspect_transaction(track.track_id, track.transaction_id).events) == event_count


@pytest.mark.parametrize(
    "disposition",
    (
        ManualResolutionDisposition.QUARANTINE_INVALID_ARTIFACTS,
        ManualResolutionDisposition.ABANDON_UNCERTAIN_ATTEMPT,
    ),
)
def test_blocking_manual_actions_retain_attempt_runtime_and_protected_bytes(
    tmp_path, disposition
):
    _config, plan_path, _plan, track, store, runtime, protected = _uncertain_fixture(
        tmp_path, complete_runtime=False
    )
    runtime.mkdir()
    (runtime / "invalid-local-artifact").write_bytes(b"retain-me")
    attempts = store.transaction_path(track.track_id, track.transaction_id) / "attempts"
    before_attempts = _tree_bytes(attempts)
    before_runtime = _tree_bytes(runtime)
    before_protected = protected.read_bytes()

    result = resolve_resume(
        tmp_path,
        plan_path,
        track.track_id,
        track.transaction_id,
        disposition,
        occurred_at_utc="2026-09-14T12:00:06Z",
    )

    assert result.state_after is TransactionState.BLOCKED
    assert result.evidence_retained is True
    assert result.future_paid_attempt_requirements == (
        "new-transaction",
        "new-plan",
        "new-preflight",
        "new-authorization",
    )
    assert result.duplicate_charge_acknowledgement_required is True
    assert _tree_bytes(attempts) == before_attempts
    assert _tree_bytes(runtime) == before_runtime
    assert protected.read_bytes() == before_protected
    assert store.inspect_transaction(track.track_id, track.transaction_id).state is TransactionState.BLOCKED


def test_source_config_authorization_and_ledger_tampering_block_recovery(tmp_path):
    for case in ("source", "config", "authorization", "ledger"):
        workspace = tmp_path / case
        config, plan_path, _plan, track, store, _runtime, _protected = _uncertain_fixture(
            workspace, complete_runtime=True
        )
        if case == "source":
            source = workspace / track.source.source_path
            source.write_text(source.read_text(encoding="utf-8") + "Changed.\n", encoding="utf-8")
        elif case == "config":
            config.write_text(config.read_text(encoding="utf-8") + "\n# drift\n", encoding="utf-8")
        elif case == "authorization":
            authorization_path = plan_path.parent / "authorizations" / "authorization-resume-test.json"
            authorization_path.write_bytes(authorization_path.read_bytes() + b"\n")
        else:
            event = sorted(
                (store.transaction_path(track.track_id, track.transaction_id) / "events").glob("*.json")
            )[-1]
            event.write_bytes(event.read_bytes() + b"\n")

        inspection = inspect_resume(
            workspace, plan_path, track.track_id, track.transaction_id
        )
        assert inspection.classification is ResumeClassification.BLOCKED_NEW_PLAN_REQUIRED
        assert inspection.finding_categories


def test_replacement_attempt_requires_fresh_scope_and_exact_retained_attempt_acknowledgement(
    tmp_path,
):
    _config, plan_path, _plan, track, _store, _runtime, _protected = _uncertain_fixture(
        tmp_path, complete_runtime=False
    )
    resolution = resolve_resume(
        tmp_path,
        plan_path,
        track.track_id,
        track.transaction_id,
        ManualResolutionDisposition.ABANDON_UNCERTAIN_ATTEMPT,
        occurred_at_utc="2026-09-14T12:00:06Z",
    )
    replacement_path, replacement_plan = _create_plan(tmp_path, "plan-resume-replacement")
    assert replacement_path != plan_path
    replacement_preflight = "1" * 64
    replacement_authorization = _authorization(
        replacement_plan,
        replacement_preflight,
        "authorization-resume-replacement",
    )

    with pytest.raises(InputError, match="acknowledgement is required"):
        validate_replacement_paid_attempt_requirements(
            resolution,
            replacement_plan,
            replacement_preflight,
            replacement_authorization,
            None,
        )

    acknowledgement = create_exact_duplicate_charge_acknowledgement(
        resolution,
        DuplicateChargeDecision.ACKNOWLEDGE_EXACT_RETAINED_ATTEMPT,
        acknowledged_at_utc="2026-09-14T12:00:07Z",
    )
    wrong_acknowledgement = seal_record(
        replace(
            acknowledgement,
            retained_attempt_sha256="2" * 64,
            binding_sha256=sha256_bytes(
                json.dumps(
                    {
                        "schema": "frontier-duplicate-charge-acknowledgement-v1",
                        "prior_transaction_id": resolution.transaction_id,
                        "retained_attempt_sha256": "2" * 64,
                    },
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            ),
            canonical_sha256="",
        )
    )
    with pytest.raises(InputError):
        validate_replacement_paid_attempt_requirements(
            resolution,
            replacement_plan,
            replacement_preflight,
            replacement_authorization,
            wrong_acknowledgement,
        )

    with pytest.raises(InputError, match="new transaction"):
        validate_replacement_paid_attempt_requirements(
            resolution,
            _plan,
            replacement_preflight,
            replacement_authorization,
            acknowledgement,
        )

    validate_replacement_paid_attempt_requirements(
        resolution,
        replacement_plan,
        replacement_preflight,
        replacement_authorization,
        acknowledgement,
    )
