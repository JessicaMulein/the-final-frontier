"""Deterministic generated checks for audiobook production correctness Property 12."""

from __future__ import annotations

import json
import os
import random
import socket
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import pytest

from frontier_audiobook import audition, narrate, nova
from frontier_audiobook import production_delivery as delivery_module
from frontier_audiobook.production_delivery import DeliveryRecord, deliver_validated_track
from frontier_audiobook.production_models import (
    RECORD_SCHEMA_VERSION,
    AudioEncoding,
    AudioFormat,
    DeliveryStatus,
    DestinationState,
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
    ValidationCheck,
    ValidationEvidence,
    ValidationStatus,
    canonical_sha256,
    seal_record,
)
from frontier_audiobook.production_transactions import TransactionStore
from frontier_audiobook.production_validation import validation_evidence_path
from frontier_audiobook.util import read_bytes_nofollow, sha256_bytes


PROPERTY_TAG = (
    "Feature: audiobook-production-workflow, Property 12: "
    "Delivery is collision-safe and idempotent"
)
PROPERTY_SEED = 0xA0D10B0C
GENERATED_CASES = 128

# **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.10**

_DESTINATION_STATES = (
    DestinationState.ABSENT,
    DestinationState.ALREADY_IDENTICAL,
    DestinationState.CONFLICTING,
)
_SOURCE_LENGTHS = (1, 2, 3, 7, 31, 32, 63, 64, 255, 256, 257, 1023, 1024, 4096)
_CONFLICT_LENGTHS = (0, 1, 2, 5, 31, 32, 255, 256, 1024, 3073)
_DELIVERED_AT = "2026-09-20T00:00:09Z"
_REPEATED_AT = "2027-01-01T00:00:00Z"


@dataclass(frozen=True, slots=True)
class _GeneratedCase:
    case_index: int
    destination_state: DestinationState
    source_bytes: bytes
    destination_bytes: bytes | None


@pytest.fixture(autouse=True)
def deny_external_paid_and_child_boundaries(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> dict[str, int]:
    """Fail immediately if delivery crosses an external, child, or paid boundary."""

    calls: dict[str, int] = {}

    def blocked(name: str):
        calls[name] = 0

        def refuse(*_args, **_kwargs):
            calls[name] += 1
            raise AssertionError(
                f"Property 12 delivery must remain local and nonbillable: {name}"
            )

        return refuse

    monkeypatch.setattr(socket, "create_connection", blocked("socket.create_connection"))
    monkeypatch.setattr(socket, "getaddrinfo", blocked("socket.getaddrinfo"))
    monkeypatch.setattr(socket.socket, "connect", blocked("socket.socket.connect"))
    monkeypatch.setattr(socket.socket, "connect_ex", blocked("socket.socket.connect_ex"))
    monkeypatch.setattr(subprocess, "Popen", blocked("subprocess.Popen"))
    monkeypatch.setattr(subprocess, "run", blocked("subprocess.run"))
    monkeypatch.setattr(urllib.request, "urlopen", blocked("urllib.request.urlopen"))
    monkeypatch.setattr(audition, "render_text", blocked("audition.render_text"))
    monkeypatch.setattr(narrate, "render_text", blocked("narrate.render_text"))
    monkeypatch.setattr(nova, "render_text", blocked("nova.render_text"))
    monkeypatch.setattr(
        nova,
        "render_text_sequence",
        blocked("nova.render_text_sequence"),
    )
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(tmp_path / "denied-aws-config"))
    monkeypatch.setenv(
        "AWS_SHARED_CREDENTIALS_FILE",
        str(tmp_path / "denied-aws-credentials"),
    )
    for variable in (
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_SECURITY_TOKEN",
    ):
        monkeypatch.delenv(variable, raising=False)
    return calls


def _digest(label: str) -> str:
    return sha256_bytes(label.encode("utf-8"))


def _track(case_index: int) -> FrozenTrackPlan:
    number = case_index + 1
    track_id = f"chapter-{number:03d}"
    transaction_id = f"transaction-{number:03d}"
    render_config_sha256 = _digest(f"render-config-{number}")
    segment = SegmentSnapshot(
        segment_id="segment-001",
        ordinal=1,
        paragraph_index=0,
        start_token_index=0,
        end_token_index=1,
        text_sha256=_digest(f"segment-text-{number}"),
        normalized_tokens_sha256=_digest(f"segment-tokens-{number}"),
        context_before_sha256=None,
        context_after_sha256=None,
        render_config_sha256=render_config_sha256,
        render_identity_sha256=_digest(f"render-identity-{number}"),
        spoken_token_count=1,
        narration_only_punctuation=False,
    )
    source = SourceSnapshot(
        track_id=track_id,
        source_path=f"The Final Frontier Novel/chapters/chapter-{number:03d}.md",
        source_section=None,
        source_kind=SourceKind.CHAPTER,
        raw_sha256=_digest(f"raw-source-{number}"),
        normalized_body_sha256=_digest(f"normalized-body-{number}"),
        spoken_sha256=_digest(f"spoken-source-{number}"),
        declared_word_count=None,
        normalized_word_count=1,
        spoken_token_count=1,
        segment_count=1,
        segmentation_policy="frontier-safe-segments-v1",
        render_identity_schema="frontier-render-identity-v1",
        render_context_radius=0,
        segments=(segment,),
    )
    effective_config = EffectiveTrackConfig(
        track_id=track_id,
        track_kind=TrackKind.CHAPTER,
        sequence=number,
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
            f"{number:03d}-{track_id}-tiffany.wav"
        ),
        resolution_provenance={
            "voice": "defaults",
            "model_id": "defaults",
            "output_path": "catalog",
        },
    )
    argv = (
        "frontier-audiobook",
        "_production-worker",
        "--transaction-id",
        transaction_id,
    )
    return FrozenTrackPlan(
        transaction_id=transaction_id,
        track_id=track_id,
        sequence=number,
        effective_config=effective_config,
        source=source,
        command_argv=argv,
        command_sha256=canonical_sha256(argv),
        maximum_new_calls=1,
        legacy_candidates=(),
        protected_inventory_sha256=_digest(f"protected-inventory-{number}"),
    )


def _plan(case_index: int) -> FrozenBatchPlan:
    track = _track(case_index)
    return seal_record(
        FrozenBatchPlan(
            schema_version=RECORD_SCHEMA_VERSION,
            plan_id="plan-property-12-delivery",
            created_at_utc="2026-09-20T00:00:00Z",
            book_id="the-final-frontier",
            config_path="audiobook-studio/config/production.toml",
            config_sha256=_digest("property-12-config"),
            selectors=(f"chapter:{case_index + 1}",),
            tracks=(track,),
            canonical_sha256="",
        )
    )


def _write_plan(
    workspace: Path,
    plan: FrozenBatchPlan,
) -> tuple[Path, TransactionStore]:
    book_root = workspace / "audiobook-studio/build/production" / plan.book_id
    plan_path = book_root / "plans" / plan.plan_id / "plan.json"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_bytes(StrictRecordCodec(FrozenBatchPlan).dump_bytes(plan))
    store = TransactionStore(book_root, plan.book_id)
    store.materialize_plan(plan, occurred_at_utc="2026-09-20T00:00:01Z")
    return plan_path, store


def _advance_to_validated(store: TransactionStore, track: FrozenTrackPlan) -> None:
    for offset, state in enumerate(
        (
            TransactionState.PREFLIGHT_PASSED,
            TransactionState.AUTHORIZATION_REQUIRED,
            TransactionState.RUNNING,
            TransactionState.RENDERED,
            TransactionState.VALIDATED,
        ),
        start=2,
    ):
        store.append_transition(
            track.track_id,
            track.transaction_id,
            operation_id=f"fixture-{state.value}",
            event_type=f"fixture-{state.value}",
            state_after=state,
            details={"fixture-step": offset},
            occurred_at_utc=f"2026-09-20T00:00:{offset:02d}Z",
        )


def _write_validated_runtime(
    workspace: Path,
    plan: FrozenBatchPlan,
    store: TransactionStore,
    track: FrozenTrackPlan,
    source_bytes: bytes,
) -> Path:
    transaction_root = store.transaction_path(track.track_id, track.transaction_id)
    runtime_root = transaction_root / "runtime"
    runtime_root.mkdir(parents=True, exist_ok=True)
    source_path = runtime_root / Path(track.effective_config.output_path).name
    source_path.write_bytes(source_bytes)
    manifest = {
        "track_id": track.track_id,
        "transaction_id": track.transaction_id,
        "track_audio_path": source_path.relative_to(workspace).as_posix(),
        "track_audio_sha256": sha256_bytes(source_bytes),
        "track_audio_byte_count": len(source_bytes),
    }
    manifest_bytes = json.dumps(
        manifest,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    manifest_path = runtime_root / "manifest.json"
    manifest_path.write_bytes(manifest_bytes)
    evidence = seal_record(
        ValidationEvidence(
            schema_version=RECORD_SCHEMA_VERSION,
            transaction_id=track.transaction_id,
            track_id=track.track_id,
            validated_at_utc="2026-09-20T00:00:08Z",
            plan_sha256=StrictRecordCodec(FrozenBatchPlan).sha256(plan),
            attempt_sha256=_digest(f"attempt-{track.transaction_id}"),
            manifest_sha256=sha256_bytes(manifest_bytes),
            status=ValidationStatus.PASSED,
            checks=(
                ValidationCheck(
                    check_id="delivery.gate",
                    status=ValidationStatus.PASSED,
                    artifact_path=manifest_path.relative_to(workspace).as_posix(),
                    artifact_sha256=sha256_bytes(manifest_bytes),
                    finding_category=None,
                    finding_count=0,
                ),
            ),
            delivery_gate_passed=True,
            canonical_sha256="",
        )
    )
    validation_path = validation_evidence_path(transaction_root, evidence)
    validation_path.parent.mkdir(parents=True)
    validation_path.write_bytes(StrictRecordCodec(ValidationEvidence).dump_bytes(evidence))
    return source_path


def _payload(rng: random.Random, length: int, case_index: int) -> bytes:
    payload = bytearray(rng.randbytes(length))
    if length >= 256:
        payload[:256] = bytes((value + case_index) % 256 for value in range(256))
    return bytes(payload)


def _different_payload(
    rng: random.Random,
    source_bytes: bytes,
    length: int,
    case_index: int,
) -> bytes:
    candidate = _payload(rng, length, case_index ^ 0x5A)
    discriminator = 0
    while sha256_bytes(candidate) == sha256_bytes(source_bytes):
        candidate += bytes((discriminator,))
        discriminator = (discriminator + 1) % 256
    return candidate


def _generated_cases(rng: random.Random) -> tuple[_GeneratedCase, ...]:
    cases: list[_GeneratedCase] = []
    for case_index in range(GENERATED_CASES):
        state = _DESTINATION_STATES[case_index % len(_DESTINATION_STATES)]
        source_length = _SOURCE_LENGTHS[case_index % len(_SOURCE_LENGTHS)]
        source_bytes = _payload(rng, source_length, case_index)
        if state is DestinationState.ABSENT:
            destination_bytes = None
        elif state is DestinationState.ALREADY_IDENTICAL:
            destination_bytes = source_bytes
        else:
            destination_bytes = _different_payload(
                rng,
                source_bytes,
                _CONFLICT_LENGTHS[case_index % len(_CONFLICT_LENGTHS)],
                case_index,
            )
        cases.append(
            _GeneratedCase(
                case_index=case_index,
                destination_state=state,
                source_bytes=source_bytes,
                destination_bytes=destination_bytes,
            )
        )
    return tuple(cases)


def _file_identity(path: Path) -> tuple[int, int, int, int]:
    stat = path.stat()
    return stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns


def _case_context(case: _GeneratedCase) -> str:
    destination = case.destination_bytes
    return (
        f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; case={case.case_index}; "
        f"state={case.destination_state.value}; "
        f"source_len={len(case.source_bytes)}; "
        f"source_sha256={sha256_bytes(case.source_bytes)}; "
        f"destination_len={None if destination is None else len(destination)}; "
        f"destination_sha256={None if destination is None else sha256_bytes(destination)}"
    )


# Feature: audiobook-production-workflow, Property 12: Delivery is collision-safe and idempotent
# **Validates: Requirements 12.1, 12.2, 12.3, 12.4, 12.10**
def test_property_12_delivery_is_collision_safe_and_idempotent(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    deny_external_paid_and_child_boundaries: dict[str, int],
) -> None:
    """Feature: audiobook-production-workflow, Property 12: Delivery is collision-safe and idempotent"""

    assert GENERATED_CASES >= 100
    print(f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; cases={GENERATED_CASES}")
    cases = _generated_cases(random.Random(PROPERTY_SEED))
    assert len(cases) == GENERATED_CASES

    active_case: list[tuple[_GeneratedCase, Path] | None] = [None]
    atomic_wav_calls = {case.case_index: 0 for case in cases}
    real_atomic_publish = delivery_module._atomic_publish_noreplace

    def observe_atomic_publish(source: Path, destination: Path) -> bool:
        active = active_case[0]
        if active is not None and destination == active[1]:
            case, expected_destination = active
            context = _case_context(case)
            assert source.parent == expected_destination.parent, context
            assert source.name.startswith(
                f".{expected_destination.name}.delivery-"
            ), context
            assert source.name.endswith(".tmp"), context
            assert not os.path.lexists(expected_destination), context
            temporary_bytes = read_bytes_nofollow(source)
            assert temporary_bytes == case.source_bytes, context
            assert len(temporary_bytes) == len(case.source_bytes), context
            assert sha256_bytes(temporary_bytes) == sha256_bytes(case.source_bytes), context
            atomic_wav_calls[case.case_index] += 1
            published = real_atomic_publish(source, destination)
            assert published is True, context
            assert read_bytes_nofollow(destination) == case.source_bytes, context
            return published
        return real_atomic_publish(source, destination)

    monkeypatch.setattr(
        delivery_module,
        "_atomic_publish_noreplace",
        observe_atomic_publish,
    )

    observed_states: set[DestinationState] = set()
    observed_source_lengths: set[int] = set()
    observed_conflict_lengths: set[int] = set()
    observed_source_octets: set[int] = set()
    state_counts = {state: 0 for state in _DESTINATION_STATES}

    for case in cases:
        context = _case_context(case)
        try:
            observed_states.add(case.destination_state)
            observed_source_lengths.add(len(case.source_bytes))
            observed_source_octets.update(case.source_bytes)
            state_counts[case.destination_state] += 1

            workspace = tmp_path / f"case-{case.case_index:03d}" / "workspace"
            workspace.mkdir(parents=True)
            plan = _plan(case.case_index)
            plan_path, store = _write_plan(workspace, plan)
            track = plan.tracks[0]
            _advance_to_validated(store, track)
            source_path = _write_validated_runtime(
                workspace,
                plan,
                store,
                track,
                case.source_bytes,
            )
            destination = workspace / track.effective_config.output_path
            active_case[0] = (case, destination)

            existing_identity: tuple[int, int, int, int] | None = None
            if case.destination_bytes is not None:
                destination.parent.mkdir(parents=True)
                destination.write_bytes(case.destination_bytes)
                existing_identity = _file_identity(destination)
                if case.destination_state is DestinationState.CONFLICTING:
                    observed_conflict_lengths.add(len(case.destination_bytes))
                    assert sha256_bytes(case.destination_bytes) != sha256_bytes(
                        case.source_bytes
                    ), context
            else:
                assert not os.path.lexists(destination), context

            source_identity = _file_identity(source_path)
            first = deliver_validated_track(
                workspace,
                plan_path,
                track.track_id,
                track.transaction_id,
                delivered_at_utc=_DELIVERED_AT,
            )

            successful = case.destination_state is not DestinationState.CONFLICTING
            expected_status = {
                DestinationState.ABSENT: DeliveryStatus.PUBLISHED,
                DestinationState.ALREADY_IDENTICAL: DeliveryStatus.ALREADY_IDENTICAL,
                DestinationState.CONFLICTING: DeliveryStatus.CONFLICTING,
            }[case.destination_state]
            expected_destination_bytes = (
                case.source_bytes if successful else case.destination_bytes
            )
            assert expected_destination_bytes is not None, context
            assert first.status is expected_status, context
            assert first.destination_state is case.destination_state, context
            assert first.source_byte_count == len(case.source_bytes), context
            assert first.source_sha256 == sha256_bytes(case.source_bytes), context
            assert first.destination_byte_count == len(expected_destination_bytes), context
            assert first.destination_sha256 == sha256_bytes(
                expected_destination_bytes
            ), context
            assert first.complete_byte_sequence_verified is successful, context
            assert first.temporary_copy_verified is (
                case.destination_state is DestinationState.ABSENT
            ), context
            assert first.atomic_publish_performed is (
                case.destination_state is DestinationState.ABSENT
            ), context
            assert first.destination_preserved is (
                case.destination_state is not DestinationState.ABSENT
            ), context
            assert first.nonbillable is True, context
            assert first.canonical_sha256 == canonical_sha256(
                first,
                omit_fields=("canonical_sha256",),
            ), context
            assert read_bytes_nofollow(source_path) == case.source_bytes, context
            assert _file_identity(source_path) == source_identity, context
            assert read_bytes_nofollow(destination) == expected_destination_bytes, context
            assert len(read_bytes_nofollow(destination)) == len(
                expected_destination_bytes
            ), context
            assert sha256_bytes(read_bytes_nofollow(destination)) == sha256_bytes(
                expected_destination_bytes
            ), context
            if existing_identity is not None:
                assert _file_identity(destination) == existing_identity, context

            expected_transaction_state = (
                TransactionState.DELIVERED if successful else TransactionState.BLOCKED
            )
            first_snapshot = store.inspect_transaction(
                track.track_id,
                track.transaction_id,
            )
            assert first_snapshot.state is expected_transaction_state, context
            first_event_count = len(first_snapshot.events)
            record_path = (
                store.transaction_path(track.track_id, track.transaction_id)
                / "delivery/delivery.json"
            )
            record_bytes = read_bytes_nofollow(record_path)
            assert StrictRecordCodec(DeliveryRecord).loads(
                record_bytes,
                label=str(record_path),
            ) == first, context
            delivered_identity = _file_identity(destination)
            atomic_calls_after_first = atomic_wav_calls[case.case_index]

            second = deliver_validated_track(
                workspace,
                plan_path,
                track.track_id,
                track.transaction_id,
                delivered_at_utc=_REPEATED_AT,
            )

            assert second == first, context
            assert read_bytes_nofollow(record_path) == record_bytes, context
            assert read_bytes_nofollow(source_path) == case.source_bytes, context
            assert _file_identity(source_path) == source_identity, context
            assert read_bytes_nofollow(destination) == expected_destination_bytes, context
            assert _file_identity(destination) == delivered_identity, context
            assert sha256_bytes(read_bytes_nofollow(destination)) == sha256_bytes(
                expected_destination_bytes
            ), context
            repeated_snapshot = store.inspect_transaction(
                track.track_id,
                track.transaction_id,
            )
            assert repeated_snapshot.state is expected_transaction_state, context
            assert len(repeated_snapshot.events) == first_event_count, context
            assert atomic_wav_calls[case.case_index] == atomic_calls_after_first, context
            assert not tuple(
                destination.parent.glob(f".{destination.name}.delivery-*.tmp")
            ), context

            expected_atomic_calls = (
                1 if case.destination_state is DestinationState.ABSENT else 0
            )
            assert atomic_wav_calls[case.case_index] == expected_atomic_calls, context
        except Exception as exc:
            exc.add_note(context)
            raise

    active_case[0] = None
    assert observed_states == set(_DESTINATION_STATES)
    assert observed_source_lengths == set(_SOURCE_LENGTHS)
    assert 0 in observed_conflict_lengths
    assert observed_source_octets == set(range(256))
    assert all(state_counts[state] >= GENERATED_CASES // 3 for state in _DESTINATION_STATES)
    assert sum(atomic_wav_calls.values()) == state_counts[DestinationState.ABSENT]
    assert all(count == 0 for count in deny_external_paid_and_child_boundaries.values())
