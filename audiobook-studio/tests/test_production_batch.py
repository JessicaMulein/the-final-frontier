from __future__ import annotations

import io
import os
import socket
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

from frontier_audiobook import narrate
from frontier_audiobook.errors import InputError
from frontier_audiobook.production_attempt import run_atomic_paid_attempt
from frontier_audiobook.production_authorization import build_authorization_start_request
from frontier_audiobook.production_batch import execute_authorized_batch
from frontier_audiobook.production_models import (
    AudioEncoding,
    AudioFormat,
    AuthorizationDecision,
    BatchStatus,
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
    authorization_confirmation_sha256,
    canonical_sha256,
    seal_record,
)
from frontier_audiobook.production_transactions import (
    TransactionLockUnavailable,
    TransactionStore,
)

_SYNTHETIC_WORKER = """
import pathlib
import sys

path = pathlib.Path(sys.argv[1])
with path.open("a", encoding="utf-8") as handle:
    handle.write(sys.argv[2] + "\\n")
print(sys.argv[2], flush=True)
raise SystemExit(int(sys.argv[3]))
""".strip()


def _fixed_clock() -> datetime:
    return datetime(2026, 9, 14, 12, 3, tzinfo=UTC)


@pytest.fixture(autouse=True)
def deny_external_access_and_narration(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("batch coordinator tests must remain local and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")


def _digest(label: str) -> str:
    return canonical_sha256({"fixture": label})


def _track_plan(
    number: int,
    *,
    launch_log: Path,
    native_return_code: int = 0,
    executable: str | None = None,
) -> FrozenTrackPlan:
    track_id = f"chapter-{number:03d}"
    render_config_sha256 = _digest(f"render-config-{number}")
    segment = SegmentSnapshot(
        segment_id="segment-001",
        ordinal=1,
        paragraph_index=0,
        start_token_index=0,
        end_token_index=1,
        text_sha256=_digest(f"text-{number}"),
        normalized_tokens_sha256=_digest(f"tokens-{number}"),
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
        raw_sha256=_digest(f"raw-{number}"),
        normalized_body_sha256=_digest(f"body-{number}"),
        spoken_sha256=_digest(f"spoken-{number}"),
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
        output_path=f"audiobook-studio/dist/audiobook/{number:03d}-{track_id}-tiffany.wav",
        resolution_provenance={"voice": "defaults", "model_id": "defaults"},
    )
    command_argv = (
        executable or sys.executable,
        "-I",
        "-c",
        _SYNTHETIC_WORKER,
        str(launch_log),
        track_id,
        str(native_return_code),
    )
    return FrozenTrackPlan(
        transaction_id=f"transaction-{number:03d}",
        track_id=track_id,
        sequence=number,
        effective_config=effective,
        source=source,
        command_argv=command_argv,
        command_sha256=canonical_sha256(command_argv),
        maximum_new_calls=1,
        legacy_candidates=(),
        protected_inventory_sha256=_digest(f"inventory-{number}"),
    )


def _plan(
    launch_log: Path,
    return_codes: tuple[int, ...],
    *,
    missing_executable_at: int | None = None,
) -> FrozenBatchPlan:
    tracks = tuple(
        _track_plan(
            number,
            launch_log=launch_log,
            native_return_code=return_code,
            executable=(
                str(launch_log.parent / "missing-synthetic-worker")
                if missing_executable_at == number
                else None
            ),
        )
        for number, return_code in enumerate(return_codes, start=1)
    )
    return seal_record(
        FrozenBatchPlan(
            schema_version=1,
            plan_id="plan-batch-test",
            created_at_utc="2026-09-14T12:00:00Z",
            book_id="the-final-frontier",
            config_path="audiobook-studio/config/production.toml",
            config_sha256=_digest("config"),
            selectors=tuple(f"chapter:{number}" for number in range(1, len(tracks) + 1)),
            tracks=tracks,
            canonical_sha256="",
        )
    )


def _authorization(
    plan: FrozenBatchPlan,
    *,
    authorization_id: str = "authorization-batch-test",
) -> PaidAuthorization:
    challenge = _digest(f"{authorization_id}-challenge")
    display_sha256 = _digest(f"{authorization_id}-display")
    confirmed_at_utc = "2026-09-14T12:00:30Z"
    decision = AuthorizationDecision.AUTHORIZE_EXACT_SCOPE
    return seal_record(
        PaidAuthorization(
            schema_version=1,
            authorization_id=authorization_id,
            plan_sha256=StrictRecordCodec(FrozenBatchPlan).sha256(plan),
            preflight_sha256=_digest("bounded-preflight"),
            local_preflight_sha256=_digest("local-preflight"),
            estimate_sha256=_digest("estimate"),
            official_rate_provenance_sha256=_digest("rates"),
            exact_transaction_ids=tuple(track.transaction_id for track in plan.tracks),
            exact_track_ids=tuple(track.track_id for track in plan.tracks),
            exact_command_sha256s=tuple(track.command_sha256 for track in plan.tracks),
            maximum_new_calls_by_track={track.track_id: 1 for track in plan.tracks},
            maximum_new_calls_total=len(plan.tracks),
            estimated_pre_tax_usd="0.750",
            operator_approved_max_estimated_pre_tax_usd="1.000",
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


def _ready_batch(workspace: Path, plan: FrozenBatchPlan, authorization: PaidAuthorization):
    store = TransactionStore(
        workspace / "audiobook-studio" / "build" / "production" / plan.book_id,
        plan.book_id,
    )
    store.materialize_plan(plan, occurred_at_utc="2026-09-14T12:00:00Z")
    for track in plan.tracks:
        store.append_transition(
            track.track_id,
            track.transaction_id,
            operation_id="preflight-passed",
            event_type="preflight-passed",
            state_after=TransactionState.PREFLIGHT_PASSED,
            details={"preflight_sha256": authorization.preflight_sha256},
            occurred_at_utc="2026-09-14T12:00:01Z",
        )
        store.append_transition(
            track.track_id,
            track.transaction_id,
            operation_id="authorization-required",
            event_type="authorization-required",
            state_after=TransactionState.AUTHORIZATION_REQUIRED,
            details={"preflight_sha256": authorization.preflight_sha256},
            occurred_at_utc="2026-09-14T12:00:02Z",
        )
    return store, build_authorization_start_request(authorization)


def _execute(
    workspace: Path,
    plan: FrozenBatchPlan,
    authorization: PaidAuthorization,
    store: TransactionStore,
    request,
    **kwargs,
):
    return execute_authorized_batch(
        plan,
        authorization,
        request,
        workspace_root=workspace,
        store=store,
        exact_environment={
            "PATH": os.environ.get("PATH", os.defpath),
            "HOME": str(workspace),
        },
        output_stream=kwargs.pop("output_stream", io.StringIO()),
        clock=_fixed_clock,
        **kwargs,
    )


def _launches(path: Path) -> tuple[str, ...]:
    if not path.exists():
        return ()
    return tuple(path.read_text(encoding="utf-8").splitlines())


def test_batch_runs_exact_plan_order_serially_with_independent_attempts(tmp_path):
    launch_log = tmp_path / "synthetic-launches.txt"
    plan = _plan(launch_log, (0, 0, 0))
    authorization = _authorization(plan)
    store, request = _ready_batch(tmp_path, plan, authorization)
    runner_calls: list[str] = []

    def lock_observing_runner(track, authorization_value, **kwargs):
        runner_calls.append(track.track_id)
        with pytest.raises(TransactionLockUnavailable):
            with store.book_lock():
                pass
        return run_atomic_paid_attempt(track, authorization_value, **kwargs)

    result = _execute(
        tmp_path,
        plan,
        authorization,
        store,
        request,
        attempt_runner=lock_observing_runner,
    )

    expected_tracks = tuple(track.track_id for track in plan.tracks)
    expected_transactions = tuple(track.transaction_id for track in plan.tracks)
    assert tuple(runner_calls) == expected_tracks
    assert _launches(launch_log) == expected_tracks
    assert result.started_transaction_ids == expected_transactions
    assert result.completed_prefix_transaction_ids == expected_transactions
    assert result.stopped_transaction_id is None
    assert not result.fresh_preflight_required
    assert not result.fresh_authorization_required
    assert result.plan_status == store.inspect_plan_status(plan)
    assert result.plan_status.status is BatchStatus.PARTIAL

    attempt_roots = []
    for track in plan.tracks:
        snapshot = store.inspect_transaction(track.track_id, track.transaction_id)
        assert snapshot.state is TransactionState.RENDERED
        assert sum(event.state_after is TransactionState.RUNNING for event in snapshot.events) == 1
        attempt_root = (
            store.transaction_path(track.track_id, track.transaction_id)
            / "attempts"
            / "attempt-001"
        )
        assert (attempt_root / "attempt.json").is_file()
        assert (attempt_root / "render-console.log").is_file()
        attempt_roots.append(attempt_root)
    assert len(set(attempt_roots)) == len(plan.tracks)


def test_nonzero_stops_suffix_at_zero_calls_and_old_scope_cannot_continue(tmp_path):
    launch_log = tmp_path / "synthetic-launches.txt"
    plan = _plan(launch_log, (0, 17, 0))
    authorization = _authorization(plan)
    store, request = _ready_batch(tmp_path, plan, authorization)
    store.index_path.parent.mkdir(parents=True, exist_ok=True)
    store.index_path.write_text('{"forged":"non-authoritative"}', encoding="utf-8")

    result = _execute(tmp_path, plan, authorization, store, request)

    assert _launches(launch_log) == ("chapter-001", "chapter-002")
    assert result.started_transaction_ids == (
        "transaction-001",
        "transaction-002",
    )
    assert result.completed_prefix_transaction_ids == ("transaction-001",)
    assert tuple(item.native_return_code for item in result.attempt_results) == (0, 17)
    assert result.stopped_transaction_id == "transaction-002"
    assert result.fresh_preflight_required
    assert result.fresh_authorization_required
    assert result.plan_status == store.inspect_plan_status(plan)
    assert result.plan_status.status is BatchStatus.PARTIAL

    states = tuple(
        store.inspect_transaction(track.track_id, track.transaction_id).state
        for track in plan.tracks
    )
    assert states == (
        TransactionState.RENDERED,
        TransactionState.BLOCKED,
        TransactionState.AUTHORIZATION_REQUIRED,
    )
    suffix = plan.tracks[2]
    suffix_root = store.transaction_path(suffix.track_id, suffix.transaction_id)
    assert not (suffix_root / "attempts").exists()
    suffix_snapshot = store.inspect_transaction(suffix.track_id, suffix.transaction_id)
    assert all(event.state_after is not TransactionState.RUNNING for event in suffix_snapshot.events)

    before = _launches(launch_log)
    with pytest.raises(InputError, match="fresh preflight and fresh authorization"):
        _execute(tmp_path, plan, authorization, store, request)
    assert _launches(launch_log) == before

    replacement_authorization = _authorization(
        plan, authorization_id="authorization-replacement-test"
    )
    with pytest.raises(InputError, match="fresh preflight and fresh authorization"):
        _execute(
            tmp_path,
            plan,
            replacement_authorization,
            store,
            build_authorization_start_request(replacement_authorization),
        )
    assert _launches(launch_log) == before


class _FailOnSecondWrite:
    def __init__(self):
        self.write_count = 0

    def write(self, value: str) -> int:
        self.write_count += 1
        if self.write_count == 2:
            raise OSError("synthetic operator stream interruption")
        return len(value)

    def flush(self) -> None:
        return None


def test_charge_uncertain_stops_before_suffix_and_retains_ambiguous_evidence(tmp_path):
    launch_log = tmp_path / "synthetic-launches.txt"
    plan = _plan(launch_log, (0, 0, 0))
    authorization = _authorization(plan)
    store, request = _ready_batch(tmp_path, plan, authorization)

    result = _execute(
        tmp_path,
        plan,
        authorization,
        store,
        request,
        output_stream=_FailOnSecondWrite(),
    )

    assert _launches(launch_log) == ("chapter-001", "chapter-002")
    assert result.started_transaction_ids == (
        "transaction-001",
        "transaction-002",
    )
    assert result.completed_prefix_transaction_ids == ("transaction-001",)
    assert tuple(item.native_return_code for item in result.attempt_results) == (0,)
    assert result.stopped_transaction_id == "transaction-002"
    assert result.fresh_preflight_required and result.fresh_authorization_required

    first, uncertain, suffix = plan.tracks
    assert store.inspect_transaction(first.track_id, first.transaction_id).state is (
        TransactionState.RENDERED
    )
    assert store.inspect_transaction(uncertain.track_id, uncertain.transaction_id).state is (
        TransactionState.CHARGE_UNCERTAIN
    )
    assert store.inspect_transaction(suffix.track_id, suffix.transaction_id).state is (
        TransactionState.AUTHORIZATION_REQUIRED
    )
    uncertain_attempts = (
        store.transaction_path(uncertain.track_id, uncertain.transaction_id) / "attempts"
    )
    assert (uncertain_attempts / "attempt-001.ambiguous.json").is_file()
    assert tuple(uncertain_attempts.glob("attempt-001.staging-*"))
    assert not (
        store.transaction_path(suffix.track_id, suffix.transaction_id) / "attempts"
    ).exists()


def test_prelaunch_block_is_fail_fast_and_does_not_dispatch_suffix(tmp_path):
    launch_log = tmp_path / "synthetic-launches.txt"
    plan = _plan(launch_log, (0, 0, 0), missing_executable_at=2)
    authorization = _authorization(plan)
    store, request = _ready_batch(tmp_path, plan, authorization)

    result = _execute(tmp_path, plan, authorization, store, request)

    assert _launches(launch_log) == ("chapter-001",)
    assert result.started_transaction_ids == (
        "transaction-001",
        "transaction-002",
    )
    assert result.completed_prefix_transaction_ids == ("transaction-001",)
    assert tuple(item.native_return_code for item in result.attempt_results) == (0,)
    assert result.stopped_transaction_id == "transaction-002"
    states = tuple(
        store.inspect_transaction(track.track_id, track.transaction_id).state
        for track in plan.tracks
    )
    assert states == (
        TransactionState.RENDERED,
        TransactionState.BLOCKED,
        TransactionState.AUTHORIZATION_REQUIRED,
    )
    assert not (
        store.transaction_path(
            plan.tracks[2].track_id, plan.tracks[2].transaction_id
        )
        / "attempts"
    ).exists()
