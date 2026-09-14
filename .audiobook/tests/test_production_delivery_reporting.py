from __future__ import annotations

import json
import os
import socket
import subprocess
from dataclasses import replace
from pathlib import Path

import pytest

from frontier_audiobook import narrate
from frontier_audiobook.errors import InputError
from frontier_audiobook.production_accounting import (
    JournalAggregation,
    ResolvedJournalUsage,
    calculate_exact_accounting,
)
from frontier_audiobook.production_delivery import (
    DeliveryRecord,
    deliver_validated_track,
)
from frontier_audiobook.production_models import (
    RECORD_SCHEMA_VERSION,
    AttemptResult,
    AudioEncoding,
    AudioFormat,
    AuthorizationDecision,
    BatchStatus,
    BillingStatus,
    DeliveryStatus,
    DestinationState,
    EffectiveTrackConfig,
    FidelityPolicy,
    FrozenBatchPlan,
    FrozenTrackPlan,
    PaidAuthorization,
    SegmentSnapshot,
    SourceKind,
    SourceSnapshot,
    StrictRecordCodec,
    TrackKind,
    TransactionState,
    UsageTotals,
    ValidationCheck,
    ValidationEvidence,
    ValidationStatus,
    authorization_confirmation_sha256,
    canonical_sha256,
    seal_record,
)
from frontier_audiobook.production_preflight import (
    BoundedCostEstimate,
    BoundedPreflightEstimateResult,
    DestinationAssessment,
    FileObservation,
    FilesystemCheck,
    IdentityEvidence,
    IsolationAssessment,
    LocalPreflightResult,
    ModalityDecimalAmount,
    ModalityTokenAmount,
    OFFICIAL_RATE_CURRENCY,
    OFFICIAL_RATE_UNIT,
    ON_DEMAND_PURCHASE_OPTION,
    OfficialModalityRate,
    OfficialRateCard,
    PriorArtifactState,
    ProtectedInventory,
    ReuseDisposition,
    TargetedCheckBinding,
    TrackCostEstimate,
    TrackReuseAssessment,
    WorkflowWriteAllowlist,
)
from frontier_audiobook.production_reporting import (
    deliver_and_write_track_report,
    write_batch_report,
)
from frontier_audiobook.production_transactions import TransactionStore
from frontier_audiobook.production_validation import validation_evidence_path
from frontier_audiobook.util import sha256_bytes


@pytest.fixture(autouse=True)
def deny_external_paid_and_child_boundaries(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("delivery/report tests must remain local and nonbillable")

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


def _sealed(value):
    return replace(
        value,
        canonical_sha256=canonical_sha256(
            value,
            omit_fields=("canonical_sha256",),
        ),
    )


def _track(number: int) -> FrozenTrackPlan:
    track_id = f"chapter-{number:03d}"
    render_config = _hash(str((number + 1) % 10))
    segment = SegmentSnapshot(
        segment_id="segment-001",
        ordinal=1,
        paragraph_index=0,
        start_token_index=0,
        end_token_index=1,
        text_sha256=_hash(str((number + 2) % 10)),
        normalized_tokens_sha256=_hash(str((number + 3) % 10)),
        context_before_sha256=None,
        context_after_sha256=None,
        render_config_sha256=render_config,
        render_identity_sha256=_hash(str((number + 4) % 10)),
        spoken_token_count=1,
        narration_only_punctuation=False,
    )
    source = SourceSnapshot(
        track_id=track_id,
        source_path=f"The Final Frontier Novel/chapters/chapter-{number:03d}.md",
        source_section=None,
        source_kind=SourceKind.CHAPTER,
        raw_sha256=_hash(str((number + 5) % 10)),
        normalized_body_sha256=_hash(str((number + 6) % 10)),
        spoken_sha256=_hash(str((number + 7) % 10)),
        declared_word_count=None,
        normalized_word_count=1,
        spoken_token_count=1,
        segment_count=1,
        segmentation_policy="frontier-safe-segments-v1",
        render_identity_schema="frontier-render-identity-v1",
        render_context_radius=0,
        segments=(segment,),
    )
    effective = EffectiveTrackConfig(
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
            ".audiobook/dist/audiobook/the-final-frontier/"
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
        f"transaction-{number:03d}",
    )
    return FrozenTrackPlan(
        transaction_id=f"transaction-{number:03d}",
        track_id=track_id,
        sequence=number,
        effective_config=effective,
        source=source,
        command_argv=argv,
        command_sha256=canonical_sha256(argv),
        maximum_new_calls=1,
        legacy_candidates=(),
        protected_inventory_sha256=_hash(str((number + 8) % 10)),
    )


def _plan(*numbers: int) -> FrozenBatchPlan:
    return seal_record(
        FrozenBatchPlan(
            schema_version=RECORD_SCHEMA_VERSION,
            plan_id="plan-delivery",
            created_at_utc="2026-09-20T00:00:00Z",
            book_id="the-final-frontier",
            config_path=".audiobook/config/production.toml",
            config_sha256=_hash("f"),
            selectors=tuple(f"chapter:{number}" for number in numbers),
            tracks=tuple(_track(number) for number in numbers),
            canonical_sha256="",
        )
    )


def _write_plan(workspace: Path, plan: FrozenBatchPlan) -> tuple[Path, TransactionStore]:
    book_root = workspace / ".audiobook/build/production" / plan.book_id
    plan_path = book_root / "plans" / plan.plan_id / "plan.json"
    plan_path.parent.mkdir(parents=True)
    plan_path.write_bytes(StrictRecordCodec(FrozenBatchPlan).dump_bytes(plan))
    store = TransactionStore(book_root, plan.book_id)
    store.materialize_plan(plan, occurred_at_utc="2026-09-20T00:00:01Z")
    return plan_path, store


def _advance_to_validated(
    store: TransactionStore,
    track: FrozenTrackPlan,
    *,
    start_second: int = 2,
) -> None:
    for offset, state in enumerate(
        (
            TransactionState.PREFLIGHT_PASSED,
            TransactionState.AUTHORIZATION_REQUIRED,
            TransactionState.RUNNING,
            TransactionState.RENDERED,
            TransactionState.VALIDATED,
        )
    ):
        store.append_transition(
            track.track_id,
            track.transaction_id,
            operation_id=f"fixture-{state.value}",
            event_type=f"fixture-{state.value}",
            state_after=state,
            details={"fixture-step": offset},
            occurred_at_utc=f"2026-09-20T00:00:{start_second + offset:02d}Z",
        )


def _write_validated_runtime(
    workspace: Path,
    plan: FrozenBatchPlan,
    store: TransactionStore,
    track: FrozenTrackPlan,
    *,
    attempt_sha256: str = _hash("a"),
    gate_passed: bool = True,
) -> bytes:
    transaction_root = store.transaction_path(track.track_id, track.transaction_id)
    runtime = transaction_root / "runtime"
    runtime.mkdir(parents=True, exist_ok=True)
    track_audio = b"RIFF-validated-track-" + track.track_id.encode("ascii")
    track_path = runtime / Path(track.effective_config.output_path).name
    track_path.write_bytes(track_audio)
    manifest = {
        "track_id": track.track_id,
        "transaction_id": track.transaction_id,
        "track_audio_path": track_path.relative_to(workspace).as_posix(),
        "track_audio_sha256": sha256_bytes(track_audio),
        "track_audio_byte_count": len(track_audio),
    }
    manifest_raw = json.dumps(
        manifest,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    (runtime / "manifest.json").write_bytes(manifest_raw)
    status = ValidationStatus.PASSED if gate_passed else ValidationStatus.BLOCKED
    check = ValidationCheck(
        check_id="delivery.gate",
        status=status,
        artifact_path=(runtime / "manifest.json").relative_to(workspace).as_posix(),
        artifact_sha256=sha256_bytes(manifest_raw),
        finding_category=None if gate_passed else "delivery-gate-blocked",
        finding_count=0 if gate_passed else 1,
    )
    evidence = seal_record(
        ValidationEvidence(
            schema_version=RECORD_SCHEMA_VERSION,
            transaction_id=track.transaction_id,
            track_id=track.track_id,
            validated_at_utc="2026-09-20T00:00:08Z",
            plan_sha256=StrictRecordCodec(FrozenBatchPlan).sha256(plan),
            attempt_sha256=attempt_sha256,
            manifest_sha256=sha256_bytes(manifest_raw),
            status=status,
            checks=(check,),
            delivery_gate_passed=gate_passed,
            canonical_sha256="",
        )
    )
    validation_root = transaction_root / "validation"
    validation_root.mkdir(parents=True)
    validation_evidence_path(transaction_root, evidence).write_bytes(
        StrictRecordCodec(ValidationEvidence).dump_bytes(evidence)
    )
    return track_audio


def _delivery_fixture(tmp_path: Path):
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    plan = _plan(1)
    plan_path, store = _write_plan(workspace, plan)
    track = plan.tracks[0]
    _advance_to_validated(store, track)
    track_audio = _write_validated_runtime(workspace, plan, store, track)
    destination = workspace / track.effective_config.output_path
    return workspace, plan, plan_path, store, track, track_audio, destination


def test_absent_delivery_uses_verified_atomic_publish_and_is_idempotent(tmp_path: Path) -> None:
    workspace, _plan_value, plan_path, store, track, track_audio, destination = (
        _delivery_fixture(tmp_path)
    )

    first = deliver_validated_track(
        workspace,
        plan_path,
        track.track_id,
        track.transaction_id,
        delivered_at_utc="2026-09-20T00:00:09Z",
    )

    assert first.status is DeliveryStatus.PUBLISHED
    assert first.destination_state is DestinationState.ABSENT
    assert first.temporary_copy_verified is True
    assert first.atomic_publish_performed is True
    assert first.complete_byte_sequence_verified is True
    assert destination.read_bytes() == track_audio
    assert not tuple(destination.parent.glob(".*.delivery-*.tmp"))
    assert store.inspect_transaction(track.track_id, track.transaction_id).state is TransactionState.DELIVERED
    destination_stat = destination.stat()
    record_path = store.transaction_path(track.track_id, track.transaction_id) / "delivery/delivery.json"
    record_bytes = record_path.read_bytes()

    second = deliver_validated_track(
        workspace,
        plan_path,
        track.track_id,
        track.transaction_id,
        delivered_at_utc="2027-01-01T00:00:00Z",
    )

    assert second == first
    assert record_path.read_bytes() == record_bytes
    assert destination.read_bytes() == track_audio
    assert destination.stat().st_ino == destination_stat.st_ino
    assert destination.stat().st_mtime_ns == destination_stat.st_mtime_ns
    assert len(store.inspect_transaction(track.track_id, track.transaction_id).events) == 8


def test_identical_delivery_retains_destination_and_conflict_preserves_and_blocks(tmp_path: Path) -> None:
    identical_root = tmp_path / "identical"
    identical_root.mkdir()
    workspace, _plan_value, plan_path, store, track, track_audio, destination = (
        _delivery_fixture(identical_root)
    )
    destination.parent.mkdir(parents=True)
    destination.write_bytes(track_audio)
    before = destination.stat()

    identical = deliver_validated_track(
        workspace,
        plan_path,
        track.track_id,
        track.transaction_id,
        delivered_at_utc="2026-09-20T00:00:09Z",
    )

    assert identical.status is DeliveryStatus.ALREADY_IDENTICAL
    assert identical.destination_preserved is True
    assert identical.atomic_publish_performed is False
    assert destination.stat().st_ino == before.st_ino
    assert destination.stat().st_mtime_ns == before.st_mtime_ns
    assert store.inspect_transaction(track.track_id, track.transaction_id).state is TransactionState.DELIVERED

    conflict_root = tmp_path / "conflict"
    conflict_root.mkdir()
    workspace, _plan_value, plan_path, store, track, _track_audio, destination = (
        _delivery_fixture(conflict_root)
    )
    conflicting_bytes = b"existing-different-proof"
    destination.parent.mkdir(parents=True)
    destination.write_bytes(conflicting_bytes)
    conflict_before = destination.stat()

    conflict = deliver_validated_track(
        workspace,
        plan_path,
        track.track_id,
        track.transaction_id,
        delivered_at_utc="2026-09-20T00:00:09Z",
    )

    assert conflict.status is DeliveryStatus.CONFLICTING
    assert conflict.destination_state is DestinationState.CONFLICTING
    assert conflict.destination_preserved is True
    assert conflict.complete_byte_sequence_verified is False
    assert destination.read_bytes() == conflicting_bytes
    assert destination.stat().st_ino == conflict_before.st_ino
    assert destination.stat().st_mtime_ns == conflict_before.st_mtime_ns
    assert store.inspect_transaction(track.track_id, track.transaction_id).state is TransactionState.BLOCKED


def test_delivery_refuses_failed_gate_without_destination_or_state_mutation(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    plan = _plan(1)
    plan_path, store = _write_plan(workspace, plan)
    track = plan.tracks[0]
    _advance_to_validated(store, track)
    _write_validated_runtime(
        workspace,
        plan,
        store,
        track,
        gate_passed=False,
    )

    with pytest.raises(InputError, match="Delivery_Gate has not passed"):
        deliver_validated_track(
            workspace,
            plan_path,
            track.track_id,
            track.transaction_id,
        )

    assert not (workspace / track.effective_config.output_path).exists()
    assert store.inspect_transaction(track.track_id, track.transaction_id).state is TransactionState.VALIDATED


def _report_preflight(plan: FrozenBatchPlan):
    targeted = TargetedCheckBinding(
        result_path=".audiobook/build/targeted-checks.json",
        result_byte_count=2,
        result_sha256=sha256_bytes(b"{}"),
        command_sha256=_hash("1"),
        return_code=0,
        aws_access_disabled=True,
        model_access_disabled=True,
        passed=True,
        binding_sha256="",
    )
    targeted = replace(
        targeted,
        binding_sha256=canonical_sha256(
            targeted,
            omit_fields=("binding_sha256",),
        ),
    )
    allowlist = _sealed(
        WorkflowWriteAllowlist(
            recursive_roots=(
                f".audiobook/build/production/{plan.book_id}",
            ),
            exact_paths=tuple(track.effective_config.output_path for track in plan.tracks),
            canonical_sha256="",
        )
    )
    filesystem = _sealed(
        FilesystemCheck(
            required_free_bytes=1,
            minimum_available_bytes=1_000_000,
            disk_space_sufficient=True,
            same_filesystem_atomic_scopes=True,
            checked_devices=((".audiobook", 1),),
            blocking_categories=(),
            canonical_sha256="",
        )
    )
    reuse = tuple(
        _sealed(
            TrackReuseAssessment(
                track_id=track.track_id,
                prior_state=PriorArtifactState.ABSENT,
                disposition=ReuseDisposition.STALE_RERENDER_REQUIRED,
                segments=(),
                reusable_segment_ids=(),
                rerender_segment_ids=tuple(
                    segment.segment_id for segment in track.source.segments
                ),
                maximum_new_calls=1,
                planned_call_ceiling=1,
                comparison_call_ceiling=1,
                invalidation_fan_out_blocked=False,
                source_revision_changed=False,
                assembled_audio=None,
                blocking_categories=(),
                canonical_sha256="",
            )
        )
        for track in plan.tracks
    )
    destinations = tuple(
        _sealed(
            DestinationAssessment(
                track_id=track.track_id,
                path=track.effective_config.output_path,
                state=DestinationState.ABSENT,
                destination_byte_count=None,
                destination_sha256=None,
                expected_sha256=None,
                canonical_sha256="",
            )
        )
        for track in plan.tracks
    )
    inventory = ProtectedInventory(
        files=(),
        unselected_manuscript_files=(),
        inventory_sha256=_hash("2"),
    )
    calls = tuple((track.track_id, 1) for track in plan.tracks)
    local = _sealed(
        LocalPreflightResult(
            plan_sha256=StrictRecordCodec(FrozenBatchPlan).sha256(plan),
            config_sha256=plan.config_sha256,
            targeted_checks=targeted,
            inventory=inventory,
            write_allowlist=allowlist,
            filesystem=filesystem,
            track_reuse=reuse,
            destinations=destinations,
            maximum_new_calls_by_track=calls,
            maximum_new_calls_total=len(plan.tracks),
            blocking_categories=(),
            passed=True,
            canonical_sha256="",
        )
    )

    modalities = ("input_speech", "input_text", "output_speech", "output_text")
    rates = tuple(OfficialModalityRate(modality, "1") for modality in modalities)
    rate_card = OfficialRateCard(
        model_id="amazon.nova-2-sonic-v1:0",
        region="us-east-1",
        purchase_option=ON_DEMAND_PURCHASE_OPTION,
        currency=OFFICIAL_RATE_CURRENCY,
        unit=OFFICIAL_RATE_UNIT,
        source_url="https://aws.amazon.com/bedrock/pricing/",
        offer_publication_date="2026-09-01",
        retrieved_at_utc="2026-09-20T00:00:00Z",
        effective_date="2026-09-01",
        rates=rates,
    )
    token_per_call = tuple(ModalityTokenAmount(modality, 1) for modality in modalities)
    track_estimates = tuple(
        TrackCostEstimate(
            track_id=track.track_id,
            model_id=track.effective_config.model_id,
            region=track.effective_config.region,
            purchase_option=ON_DEMAND_PURCHASE_OPTION,
            maximum_new_calls=1,
            maximum_tokens_by_modality=token_per_call,
            subtotals_by_modality_usd=tuple(
                ModalityDecimalAmount(modality, "0.001") for modality in modalities
            ),
            estimated_pre_tax_usd="0.004",
        )
        for track in plan.tracks
    )
    aggregate_tokens = tuple(
        ModalityTokenAmount(modality, len(plan.tracks)) for modality in modalities
    )
    aggregate_costs = tuple(
        ModalityDecimalAmount(modality, f"0.00{len(plan.tracks)}")
        for modality in modalities
    )
    estimate = _sealed(
        BoundedCostEstimate(
            maximum_new_calls_by_track=calls,
            maximum_new_calls_total=len(plan.tracks),
            configured_tokens_per_call=token_per_call,
            maximum_tokens_by_modality=aggregate_tokens,
            subtotals_by_modality_usd=aggregate_costs,
            tracks=track_estimates,
            estimated_pre_tax_usd=f"0.0{4 * len(plan.tracks):02d}",
            assumptions=("finite configured envelopes",),
            canonical_sha256="",
        )
    )
    bounded = _sealed(
        BoundedPreflightEstimateResult(
            plan_sha256=local.plan_sha256,
            local_preflight_sha256=local.canonical_sha256,
            checked_at_utc="2026-09-20T00:00:00Z",
            identity_evidence=(
                IdentityEvidence(
                    profile_label="frontier-audiobook",
                    resolved=True,
                    checked_at_utc="2026-09-20T00:00:00Z",
                ),
            ),
            official_rate_cards=(rate_card,),
            estimate=estimate,
            blocking_categories=(),
            passed=True,
            canonical_sha256="",
        )
    )
    return local, bounded, rate_card


def _authorization(
    plan: FrozenBatchPlan,
    local: LocalPreflightResult,
    bounded: BoundedPreflightEstimateResult,
) -> PaidAuthorization:
    display = _hash("3")
    challenge = _hash("4")
    confirmed_at = "2026-09-20T00:00:01Z"
    confirmation = authorization_confirmation_sha256(
        display_sha256=display,
        challenge=challenge,
        decision=AuthorizationDecision.AUTHORIZE_EXACT_SCOPE,
        confirmed_at_utc=confirmed_at,
    )
    return seal_record(
        PaidAuthorization(
            schema_version=RECORD_SCHEMA_VERSION,
            authorization_id="authorization-delivery",
            plan_sha256=StrictRecordCodec(FrozenBatchPlan).sha256(plan),
            preflight_sha256=bounded.canonical_sha256,
            local_preflight_sha256=local.canonical_sha256,
            estimate_sha256=bounded.estimate.canonical_sha256,
            official_rate_provenance_sha256=canonical_sha256(
                bounded.official_rate_cards
            ),
            exact_transaction_ids=tuple(track.transaction_id for track in plan.tracks),
            exact_track_ids=tuple(track.track_id for track in plan.tracks),
            exact_command_sha256s=tuple(track.command_sha256 for track in plan.tracks),
            maximum_new_calls_by_track={track.track_id: 1 for track in plan.tracks},
            maximum_new_calls_total=len(plan.tracks),
            estimated_pre_tax_usd=bounded.estimate.estimated_pre_tax_usd,
            operator_approved_max_estimated_pre_tax_usd="1.000",
            issued_at_utc="2026-09-20T00:00:00Z",
            expires_at_utc="2026-09-21T00:00:00Z",
            one_shot=True,
            confirmation_challenge=challenge,
            confirmation_display_sha256=display,
            confirmation_decision=AuthorizationDecision.AUTHORIZE_EXACT_SCOPE,
            confirmed_at_utc=confirmed_at,
            confirmation_sha256=confirmation,
            canonical_sha256="",
        )
    )


def _attempt(track: FrozenTrackPlan, authorization: PaidAuthorization) -> AttemptResult:
    return AttemptResult(
        schema_version=RECORD_SCHEMA_VERSION,
        attempt_id="attempt-001",
        transaction_id=track.transaction_id,
        authorization_sha256=StrictRecordCodec(PaidAuthorization).sha256(authorization),
        working_directory=".",
        argv=track.command_argv,
        command_sha256=track.command_sha256,
        profile_label=track.effective_config.profile_label,
        started_at_utc="2026-09-20T00:00:04Z",
        ended_at_utc="2026-09-20T00:00:05Z",
        child_launched=True,
        native_return_code=0,
        termination_signal=None,
        console_path=(
            f".audiobook/build/production/the-final-frontier/transactions/"
            f"{track.track_id}/{track.transaction_id}/attempts/attempt-001/render-console.log"
        ),
        console_sha256=_hash("5"),
        automatic_retry_performed=False,
        environment_persisted=False,
    )


def _accounting(rate_card: OfficialRateCard):
    totals = UsageTotals(1, 1, 1, 1)
    aggregation = JournalAggregation(
        journals=(
            ResolvedJournalUsage(
                segment_id="segment-001",
                audio_path=".audiobook/build/runtime/segment-001.wav",
                journal_path=".audiobook/build/runtime/segment-001.events.jsonl",
                journal_sha256=_hash("6"),
                rendered_in_current_attempt=True,
                usage_event_count=1,
                totals=totals,
            ),
        ),
        active_artifact_totals=totals,
        current_execution_totals=totals,
    )
    return calculate_exact_accounting(
        aggregation,
        rate_card,
        expected_rate_target=rate_card.target,
        cost_estimate_usd="0.004",
        operator_approved_max_estimated_pre_tax_usd="1.000",
        calculated_at_utc="2026-09-20T00:00:10Z",
    )


def test_deliver_operation_creates_complete_sanitized_idempotent_track_and_batch_reports(
    tmp_path: Path,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    plan = _plan(1, 2)
    plan_path, store = _write_plan(workspace, plan)
    delivered_track = plan.tracks[0]
    _advance_to_validated(store, delivered_track)
    local, bounded, rate_card = _report_preflight(plan)
    authorization = _authorization(plan, local, bounded)
    attempt = _attempt(delivered_track, authorization)
    _write_validated_runtime(
        workspace,
        plan,
        store,
        delivered_track,
        attempt_sha256=StrictRecordCodec(AttemptResult).sha256(attempt),
    )
    isolation = _sealed(
        IsolationAssessment(
            hard_protected_drift_paths=(),
            concurrent_manuscript_change_paths=(),
            workflow_writes_outside_allowlist=(),
            passed=True,
            canonical_sha256="",
        )
    )

    result = deliver_and_write_track_report(
        workspace,
        plan_path,
        delivered_track.track_id,
        delivered_track.transaction_id,
        local_preflight=local,
        bounded_preflight=bounded,
        authorization=authorization,
        attempt=attempt,
        accounting=_accounting(rate_card),
        isolation=isolation,
        broader_suite_status=ValidationStatus.NOT_RUN,
        supplemental_listening_sha256=_hash("7"),
        delivered_at_utc="2026-09-20T00:00:11Z",
        generated_at_utc="2026-09-20T00:00:12Z",
    )

    assert result.delivery.status is DeliveryStatus.PUBLISHED
    assert result.track_report is not None
    report = result.track_report
    assert report.state is TransactionState.DELIVERED
    assert report.native_return_code == 0
    assert report.active_artifact_totals == UsageTotals(1, 1, 1, 1)
    assert report.current_execution_totals == UsageTotals(1, 1, 1, 1)
    assert report.estimated_pre_tax_usd == "0.004"
    assert report.current_execution_cost_usd == "0.004"
    assert report.billing_status is BillingStatus.PENDING
    assert report.isolation_status is ValidationStatus.PASSED
    assert report.delivery_status is DeliveryStatus.PUBLISHED
    transaction_root = store.transaction_path(
        delivered_track.track_id,
        delivered_track.transaction_id,
    )
    report_json = transaction_root / "report.json"
    report_markdown = transaction_root / "report.md"
    first_json = report_json.read_bytes()
    first_markdown = report_markdown.read_text(encoding="utf-8")
    for heading in (
        "## Evidence digests",
        "## Deterministic validation",
        "## Reuse",
        "## Usage",
        "## Cost estimate and exact service cost",
        "## Billing confirmation",
        "## Delivery and collision",
        "## Isolation",
        "## Tests",
        "## Supplemental listening",
    ):
        assert heading in first_markdown
    assert "supplemental-only" in first_markdown
    assert "raw event payloads" in first_markdown
    assert "model-calls-started" not in first_markdown

    repeated = deliver_and_write_track_report(
        workspace,
        plan_path,
        delivered_track.track_id,
        delivered_track.transaction_id,
        local_preflight=local,
        bounded_preflight=bounded,
        authorization=authorization,
        attempt=attempt,
        accounting=_accounting(rate_card),
        isolation=isolation,
        broader_suite_status=ValidationStatus.NOT_RUN,
        supplemental_listening_sha256=_hash("7"),
        delivered_at_utc="2027-01-01T00:00:00Z",
        generated_at_utc="2027-01-01T00:00:01Z",
    )
    assert repeated == result
    assert report_json.read_bytes() == first_json
    assert report_markdown.read_text(encoding="utf-8") == first_markdown

    batch = write_batch_report(
        workspace,
        plan_path,
        generated_at_utc="2026-09-20T00:00:13Z",
    )
    assert batch.status is BatchStatus.PARTIAL
    assert batch.selected_count == 2
    assert batch.completed_count == 1
    assert batch.unstarted_count == 1
    assert tuple(entry.track_id for entry in batch.tracks) == (
        "chapter-001",
        "chapter-002",
    )
    assert batch.tracks[0].track_report_sha256 is not None
    assert batch.tracks[1].track_report_sha256 is None
    batch_path = (
        workspace
        / ".audiobook/build/production/the-final-frontier/batches/plan-delivery/report.md"
    )
    batch_bytes = batch_path.read_bytes()
    assert b"chapter-001" in batch_bytes
    assert b"chapter-002" in batch_bytes
    assert b"Validation SHA-256" in batch_bytes
    assert b"Delivery / collision" in batch_bytes

    repeated_batch = write_batch_report(
        workspace,
        plan_path,
        generated_at_utc="2027-01-01T00:00:02Z",
    )
    assert repeated_batch == batch
    assert batch_path.read_bytes() == batch_bytes
