from __future__ import annotations

import json
import socket
from dataclasses import replace

import pytest

from frontier_audiobook.errors import InputError
from frontier_audiobook.production_models import (
    AttemptResult,
    AudioEncoding,
    AudioFormat,
    AuthorizationDecision,
    BatchReport,
    BatchStatus,
    BatchTrackReportEntry,
    BillingStatus,
    DeliveryStatus,
    DestinationState,
    EffectiveTrackConfig,
    FidelityPolicy,
    FrozenBatchPlan,
    FrozenTrackPlan,
    LedgerEvent,
    PaidAuthorization,
    PreflightRecord,
    SegmentSnapshot,
    SourceKind,
    SourceSnapshot,
    StrictRecordCodec,
    TrackKind,
    TrackReport,
    TransactionState,
    UsageTotals,
    ValidationCheck,
    ValidationEvidence,
    ValidationStatus,
    authorization_confirmation_sha256,
    canonical_json_text,
    record_to_data,
    seal_record,
)


@pytest.fixture(autouse=True)
def deny_python_network(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("production record tests must remain offline")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")


def _hash(character: str) -> str:
    return character * 64


def _effective_config() -> EffectiveTrackConfig:
    return EffectiveTrackConfig(
        track_id="chapter-003",
        track_kind=TrackKind.CHAPTER,
        sequence=3,
        voice="tiffany",
        model_id="amazon.nova-2-sonic-v1:0",
        region="us-east-1",
        profile_label="frontier-audiobook",
        target_segment_words=5,
        fidelity_policy=FidelityPolicy.EXACT,
        normalization="frontier-word-sequence-v1",
        audio_format=AudioFormat(24000, 16, 1, AudioEncoding.PCM_S16LE),
        output_path="audiobook-studio/dist/audiobook/the-final-frontier/003-chapter-003-tiffany.wav",
        resolution_provenance={
            "voice": "defaults",
            "model_id": "defaults",
            "target_segment_words": "defaults",
        },
    )


def _source_snapshot() -> SourceSnapshot:
    return SourceSnapshot(
        track_id="chapter-003",
        source_path="The Final Frontier Novel/chapters/discovery-part/chapter-003.md",
        source_section=None,
        source_kind=SourceKind.CHAPTER,
        raw_sha256=_hash("a"),
        normalized_body_sha256=_hash("b"),
        spoken_sha256=_hash("c"),
        declared_word_count=5,
        normalized_word_count=5,
        spoken_token_count=5,
        segment_count=2,
        segmentation_policy="safe-narration-punctuation-v3",
        render_identity_schema="frontier-render-identity-v1",
        render_context_radius=1,
        segments=(
            SegmentSnapshot(
                segment_id="segment-001",
                ordinal=1,
                paragraph_index=0,
                start_token_index=0,
                end_token_index=2,
                text_sha256=_hash("d"),
                normalized_tokens_sha256=_hash("2"),
                context_before_sha256=None,
                context_after_sha256=_hash("4"),
                render_config_sha256=_hash("6"),
                render_identity_sha256=_hash("7"),
                spoken_token_count=2,
                narration_only_punctuation=False,
            ),
            SegmentSnapshot(
                segment_id="segment-002",
                ordinal=2,
                paragraph_index=1,
                start_token_index=2,
                end_token_index=5,
                text_sha256=_hash("e"),
                normalized_tokens_sha256=_hash("3"),
                context_before_sha256=_hash("5"),
                context_after_sha256=None,
                render_config_sha256=_hash("6"),
                render_identity_sha256=_hash("8"),
                spoken_token_count=3,
                narration_only_punctuation=True,
            ),
        ),
    )


def _track_plan() -> FrozenTrackPlan:
    return FrozenTrackPlan(
        transaction_id="transaction-003",
        track_id="chapter-003",
        sequence=3,
        effective_config=_effective_config(),
        source=_source_snapshot(),
        command_argv=("python", "-m", "frontier_audiobook", "production-worker"),
        command_sha256=_hash("f"),
        maximum_new_calls=2,
        legacy_candidates=("audiobook-studio/build/narration/chapter-003/manifest.json",),
        protected_inventory_sha256=_hash("0"),
    )


def _plan() -> FrozenBatchPlan:
    return seal_record(
        FrozenBatchPlan(
            schema_version=1,
            plan_id="plan-003",
            created_at_utc="2026-09-12T00:00:00Z",
            book_id="the-final-frontier",
            config_path="audiobook-studio/config/production.toml",
            config_sha256=_hash("1"),
            selectors=("chapter:3",),
            tracks=(_track_plan(),),
            canonical_sha256="",
        )
    )


def _preflight() -> PreflightRecord:
    return seal_record(
        PreflightRecord(
            schema_version=1,
            plan_sha256=_hash("2"),
            checked_at_utc="2026-09-12T00:01:00Z",
            expires_at_utc="2026-09-13T00:01:00Z",
            targeted_checks_sha256=_hash("3"),
            identity_profile_label="frontier-audiobook",
            identity_resolved=True,
            identity_checked_at_utc="2026-09-12T00:01:01Z",
            official_rates={
                "input_speech": "0.0001",
                "input_text": "0.0002",
                "output_speech": "0.0003",
                "output_text": "0.0004",
            },
            official_rate_provenance={
                "source_url": "https://example.invalid/rates",
                "currency": "USD",
                "unit": "tokens-per-1k",
            },
            reusable_segment_ids={"chapter-003": ("segment-001",)},
            maximum_new_calls_by_track={"chapter-003": 1},
            maximum_new_calls_total=1,
            estimated_pre_tax_usd="0.01",
            estimate_inputs={"input_text_tokens": 8192, "conservative": True},
            delivery_collisions={"chapter-003": DestinationState.ABSENT},
            per_file_inventory_sha256=_hash("4"),
            canonical_sha256="",
        )
    )


def _authorization() -> PaidAuthorization:
    challenge = _hash("8")
    display_sha256 = _hash("9")
    confirmed_at_utc = "2026-09-12T00:02:30Z"
    decision = AuthorizationDecision.AUTHORIZE_EXACT_SCOPE
    return seal_record(
        PaidAuthorization(
            schema_version=1,
            authorization_id="authorization-003",
            plan_sha256=_hash("5"),
            preflight_sha256=_hash("6"),
            local_preflight_sha256=_hash("a"),
            estimate_sha256=_hash("b"),
            official_rate_provenance_sha256=_hash("c"),
            exact_transaction_ids=("transaction-003",),
            exact_track_ids=("chapter-003",),
            exact_command_sha256s=(_hash("7"),),
            maximum_new_calls_by_track={"chapter-003": 1},
            maximum_new_calls_total=1,
            estimated_pre_tax_usd="0.01",
            operator_approved_max_estimated_pre_tax_usd="0.02",
            issued_at_utc="2026-09-12T00:02:00Z",
            expires_at_utc="2026-09-12T01:02:00Z",
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


def _ledger_event() -> LedgerEvent:
    return seal_record(
        LedgerEvent(
            schema_version=1,
            transaction_id="transaction-003",
            sequence=1,
            event_type="track-discovered",
            state_before=None,
            state_after=TransactionState.DISCOVERED,
            occurred_at_utc="2026-09-12T00:00:00Z",
            payload_sha256=_hash("8"),
            previous_event_sha256=None,
            event_sha256="",
        )
    )


def _attempt() -> AttemptResult:
    return AttemptResult(
        schema_version=1,
        attempt_id="attempt-001",
        transaction_id="transaction-003",
        authorization_sha256=_hash("9"),
        working_directory="audiobook-studio/build/production/the-final-frontier",
        argv=("python", "-m", "frontier_audiobook", "production-worker"),
        command_sha256=_hash("a"),
        profile_label="frontier-audiobook",
        started_at_utc="2026-09-12T00:03:00Z",
        ended_at_utc="2026-09-12T00:04:00Z",
        child_launched=True,
        native_return_code=0,
        termination_signal=None,
        console_path="audiobook-studio/build/production/attempt-001/render-console.log",
        console_sha256=_hash("b"),
        automatic_retry_performed=False,
        environment_persisted=False,
    )


def _validation() -> ValidationEvidence:
    return seal_record(
        ValidationEvidence(
            schema_version=1,
            transaction_id="transaction-003",
            track_id="chapter-003",
            validated_at_utc="2026-09-12T00:05:00Z",
            plan_sha256=_hash("c"),
            attempt_sha256=_hash("d"),
            manifest_sha256=_hash("e"),
            status=ValidationStatus.PASSED,
            checks=(
                ValidationCheck(
                    check_id="manifest.binding",
                    status=ValidationStatus.PASSED,
                    artifact_path="audiobook-studio/build/production/runtime/manifest.json",
                    artifact_sha256=_hash("f"),
                    finding_category=None,
                    finding_count=0,
                ),
            ),
            delivery_gate_passed=True,
            canonical_sha256="",
        )
    )


def _track_report() -> TrackReport:
    return seal_record(
        TrackReport(
            schema_version=1,
            transaction_id="transaction-003",
            track_id="chapter-003",
            generated_at_utc="2026-09-12T00:06:00Z",
            state=TransactionState.DELIVERED,
            source_sha256=_hash("0"),
            config_sha256=_hash("1"),
            plan_sha256=_hash("2"),
            preflight_sha256=_hash("3"),
            authorization_sha256=_hash("4"),
            attempt_sha256=_hash("5"),
            validation_sha256=_hash("6"),
            native_return_code=0,
            active_artifact_totals=UsageTotals(0, 10, 20, 2),
            current_execution_totals=UsageTotals(0, 10, 20, 2),
            estimated_pre_tax_usd="0.01",
            active_artifact_cost_usd="0.008",
            current_execution_cost_usd="0.008",
            billing_status=BillingStatus.NOT_PERFORMED,
            billing_amount_usd=None,
            billing_confirmed_at_utc=None,
            delivery_status=DeliveryStatus.PUBLISHED,
            isolation_status=ValidationStatus.PASSED,
            targeted_checks_sha256=_hash("7"),
            broader_suite_status=ValidationStatus.NOT_RUN,
            supplemental_listening_sha256=None,
            canonical_sha256="",
        )
    )


def _batch_report() -> BatchReport:
    return seal_record(
        BatchReport(
            schema_version=1,
            plan_id="plan-003",
            plan_sha256=_hash("8"),
            generated_at_utc="2026-09-12T00:07:00Z",
            status=BatchStatus.COMPLETE,
            tracks=(
                BatchTrackReportEntry(
                    transaction_id="transaction-003",
                    track_id="chapter-003",
                    sequence=3,
                    state=TransactionState.DELIVERED,
                    track_report_sha256=_hash("9"),
                ),
            ),
            selected_count=1,
            completed_count=1,
            blocked_count=0,
            unstarted_count=0,
            canonical_sha256="",
        )
    )


def test_all_record_families_round_trip_through_canonical_json():
    records = (
        _effective_config(),
        _source_snapshot(),
        _track_plan(),
        _plan(),
        _preflight(),
        _authorization(),
        _ledger_event(),
        _attempt(),
        _validation(),
        _track_report(),
        _batch_report(),
    )

    for record in records:
        codec = StrictRecordCodec(type(record))
        encoded = codec.dumps(record)
        assert encoded == canonical_json_text(record)
        assert encoded == encoded.strip()
        assert ": " not in encoded
        assert codec.loads(encoded) == record
        assert codec.sha256(record) == codec.sha256(codec.loads(encoded))


def test_strict_record_codec_rejects_duplicate_unknown_nonfinite_enum_and_schema_values():
    codec = StrictRecordCodec(FrozenBatchPlan)
    encoded = codec.dumps(_plan())

    duplicate = encoded.replace('"book_id":', '"book_id":"duplicate","book_id":', 1)
    with pytest.raises(InputError, match="duplicate object name"):
        codec.loads(duplicate)

    unknown = json.loads(encoded)
    unknown["source_text"] = "must not be persisted"
    with pytest.raises(InputError, match=r"unknown=\['source_text'\]"):
        codec.loads(json.dumps(unknown, sort_keys=True, separators=(",", ":")))

    nonfinite = encoded.replace('"schema_version":1', '"schema_version":NaN', 1)
    with pytest.raises(InputError, match="non-finite JSON number"):
        codec.loads(nonfinite)

    unknown_enum = json.loads(encoded)
    unknown_enum["tracks"][0]["effective_config"]["track_kind"] = "appendix"
    with pytest.raises(InputError, match="unknown enum value"):
        codec.loads(json.dumps(unknown_enum, sort_keys=True, separators=(",", ":")))

    wrong_schema = json.loads(encoded)
    wrong_schema["schema_version"] = 2
    with pytest.raises(InputError, match="schema_version must be integer 1"):
        codec.loads(json.dumps(wrong_schema, sort_keys=True, separators=(",", ":")))


def test_codec_enforces_canonical_bytes_and_embedded_digest(tmp_path):
    record = _plan()
    codec = StrictRecordCodec(FrozenBatchPlan)
    encoded = codec.dumps(record)
    pretty = json.dumps(json.loads(encoded), ensure_ascii=False, indent=2, sort_keys=True)

    with pytest.raises(InputError, match="not canonically encoded"):
        codec.loads(pretty)
    assert codec.loads(pretty, require_canonical=False) == record

    tampered = json.loads(encoded)
    tampered["selectors"] = ["chapter:4"]
    with pytest.raises(InputError, match="does not match canonical content"):
        codec.loads(json.dumps(tampered, sort_keys=True, separators=(",", ":")))

    path = tmp_path / "plan.json"
    codec.write_atomic(path, record)
    assert path.read_bytes() == encoded.encode("utf-8")
    assert codec.load(path) == record


def test_records_are_deeply_immutable_and_have_no_body_fields():
    preflight = _preflight()
    with pytest.raises(TypeError):
        preflight.maximum_new_calls_by_track["chapter-003"] = 2  # type: ignore[index]

    forbidden = {
        "prose",
        "source_text",
        "segment_text",
        "transcript",
        "event_payload",
        "environment",
        "credentials",
        "identity_response",
    }

    def names(value):
        if isinstance(value, dict):
            yield from value
            for item in value.values():
                yield from names(item)
        elif isinstance(value, list):
            for item in value:
                yield from names(item)

    persisted_names = set(names(record_to_data((_plan(), preflight, _authorization(), _attempt()))))
    assert forbidden.isdisjoint(persisted_names)


def test_model_invariants_reject_token_loss_and_forbidden_attempt_flags():
    source = _source_snapshot()
    with pytest.raises(InputError, match="token counts"):
        replace(source, spoken_token_count=6)

    with pytest.raises(InputError, match="automatic_retry_performed must be false"):
        replace(_attempt(), automatic_retry_performed=True)

    with pytest.raises(InputError, match="approved maximum must cover"):
        replace(
            _authorization(),
            operator_approved_max_estimated_pre_tax_usd="0.001",
            canonical_sha256="",
        )
