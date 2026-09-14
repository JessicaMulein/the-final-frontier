"""Deterministic generated checks for audiobook production correctness Property 6."""

from __future__ import annotations

import json
import random
import socket
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

import pytest

import frontier_audiobook.narrate as narrate
import frontier_audiobook.production_attempt as attempt_module
from frontier_audiobook.errors import InputError
from frontier_audiobook.production_attempt import AttemptChargeUncertain
from frontier_audiobook.production_authorization import build_authorization_start_request
from frontier_audiobook.production_batch import execute_authorized_batch
from frontier_audiobook.production_models import (
    AttemptResult,
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
from frontier_audiobook.production_transactions import TransactionStore
from frontier_audiobook.util import sha256_file


PROPERTY_TAG = "Feature: audiobook-production-workflow, Property 6: Batch execution is fail-fast with independent transactions"
PROPERTY_SEED = 0xA0D10B06
MAX_BATCH_SIZE = 5
_FAILURE_TYPES = (
    "nonzero-status",
    "charge-uncertain",
    "source-drift",
    "protected-runtime-drift",
    "authorization-mismatch",
    "call-bound-exhaustion",
    "exact-fidelity-failure",
    "partial-turn-failure",
)
GENERATED_CASES = len(_FAILURE_TYPES) * sum(range(1, MAX_BATCH_SIZE + 1))
_PRECALL_FAILURES = frozenset(
    {
        "source-drift",
        "protected-runtime-drift",
        "authorization-mismatch",
        "call-bound-exhaustion",
    }
)
_FAILURES_WITHOUT_ACCEPTED_RESULT = frozenset(
    {"charge-uncertain", "authorization-mismatch"}
)

# **Validates: Requirements 6.13, 8.1, 8.2, 8.3, 8.7, 8.8, 8.9**


@dataclass(frozen=True, slots=True)
class _GeneratedCase:
    batch_size: int
    failure_position: int
    failure_type: str
    nonzero_status: int
    nonce: int


@pytest.fixture(autouse=True)
def deny_network_model_narration_and_child_launch(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Fail if Property 6 crosses any external or paid execution boundary."""

    def blocked(*_args, **_kwargs):
        raise AssertionError("Property 6 must remain synthetic, local, and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setattr(attempt_module.subprocess, "Popen", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.delenv("AWS_ACCESS_KEY_ID", raising=False)
    monkeypatch.delenv("AWS_SECRET_ACCESS_KEY", raising=False)
    monkeypatch.delenv("AWS_SESSION_TOKEN", raising=False)


def _fixed_clock() -> datetime:
    return datetime(2026, 9, 14, 12, 3, tzinfo=UTC)


def _digest(label: str) -> str:
    return canonical_sha256({"property-6-fixture": label})


def _generated_cases(rng: random.Random) -> Iterator[_GeneratedCase]:
    coverage = [
        (batch_size, failure_position, failure_type)
        for batch_size in range(1, MAX_BATCH_SIZE + 1)
        for failure_position in range(batch_size)
        for failure_type in _FAILURE_TYPES
    ]
    rng.shuffle(coverage)
    for batch_size, failure_position, failure_type in coverage:
        yield _GeneratedCase(
            batch_size=batch_size,
            failure_position=failure_position,
            failure_type=failure_type,
            nonzero_status=1 + rng.randrange(125),
            nonce=rng.getrandbits(64),
        )


def _track_plan(number: int, *, case_nonce: int) -> FrozenTrackPlan:
    track_id = f"chapter-{number:03d}"
    render_config_sha256 = _digest(f"render-config-{case_nonce}-{number}")
    segment = SegmentSnapshot(
        segment_id="segment-001",
        ordinal=1,
        paragraph_index=0,
        start_token_index=0,
        end_token_index=1,
        text_sha256=_digest(f"text-{case_nonce}-{number}"),
        normalized_tokens_sha256=_digest(f"tokens-{case_nonce}-{number}"),
        context_before_sha256=None,
        context_after_sha256=None,
        render_config_sha256=render_config_sha256,
        render_identity_sha256=_digest(f"render-identity-{case_nonce}-{number}"),
        spoken_token_count=1,
        narration_only_punctuation=False,
    )
    source = SourceSnapshot(
        track_id=track_id,
        source_path=f"The Final Frontier Novel/chapters/chapter-{number:03d}.md",
        source_section=None,
        source_kind=SourceKind.CHAPTER,
        raw_sha256=_digest(f"raw-{case_nonce}-{number}"),
        normalized_body_sha256=_digest(f"body-{case_nonce}-{number}"),
        spoken_sha256=_digest(f"spoken-{case_nonce}-{number}"),
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
            f".audiobook/dist/audiobook/{number:03d}-{track_id}-tiffany.wav"
        ),
        resolution_provenance={"voice": "defaults", "model_id": "defaults"},
    )
    command_argv = (
        "synthetic-local-batch-worker",
        "--track-id",
        track_id,
        "--case",
        f"{case_nonce:016x}",
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
        protected_inventory_sha256=_digest(f"inventory-{case_nonce}-{number}"),
    )


def _plan(case: _GeneratedCase) -> FrozenBatchPlan:
    tracks = tuple(
        _track_plan(number, case_nonce=case.nonce)
        for number in range(1, case.batch_size + 1)
    )
    return seal_record(
        FrozenBatchPlan(
            schema_version=1,
            plan_id="plan-property-six",
            created_at_utc="2026-09-14T12:00:00Z",
            book_id="the-final-frontier",
            config_path=".audiobook/config/production.toml",
            config_sha256=_digest(f"config-{case.nonce}"),
            selectors=tuple(
                f"chapter:{number}" for number in range(1, case.batch_size + 1)
            ),
            tracks=tracks,
            canonical_sha256="",
        )
    )


def _authorization(plan: FrozenBatchPlan, *, case_nonce: int) -> PaidAuthorization:
    challenge = _digest(f"challenge-{case_nonce}")
    display_sha256 = _digest(f"display-{case_nonce}")
    confirmed_at_utc = "2026-09-14T12:00:30Z"
    decision = AuthorizationDecision.AUTHORIZE_EXACT_SCOPE
    return seal_record(
        PaidAuthorization(
            schema_version=1,
            authorization_id="authorization-property-six",
            plan_sha256=StrictRecordCodec(FrozenBatchPlan).sha256(plan),
            preflight_sha256=_digest(f"preflight-{case_nonce}"),
            local_preflight_sha256=_digest(f"local-preflight-{case_nonce}"),
            estimate_sha256=_digest(f"estimate-{case_nonce}"),
            official_rate_provenance_sha256=_digest(f"rates-{case_nonce}"),
            exact_transaction_ids=tuple(
                track.transaction_id for track in plan.tracks
            ),
            exact_track_ids=tuple(track.track_id for track in plan.tracks),
            exact_command_sha256s=tuple(
                track.command_sha256 for track in plan.tracks
            ),
            maximum_new_calls_by_track={
                track.track_id: track.maximum_new_calls for track in plan.tracks
            },
            maximum_new_calls_total=sum(
                track.maximum_new_calls for track in plan.tracks
            ),
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


def _ready_batch(
    workspace: Path,
    plan: FrozenBatchPlan,
    authorization: PaidAuthorization,
) -> TransactionStore:
    store = TransactionStore(
        workspace / ".audiobook" / "build" / "production" / plan.book_id,
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
    return store


class _SyntheticFailFastRunner:
    """Local attempt fixture that records real independent ledger/evidence roots."""

    def __init__(
        self,
        *,
        case: _GeneratedCase,
        plan: FrozenBatchPlan,
        workspace: Path,
        store: TransactionStore,
        authorization_sha256: str,
    ) -> None:
        self.case = case
        self.plan = plan
        self.workspace = workspace
        self.store = store
        self.authorization_sha256 = authorization_sha256
        self.invocations: list[str] = []
        self.synthetic_call_counts: dict[str, int] = {}
        self.evidence_paths: dict[str, Path] = {}
        self._active = 0
        self.max_active = 0

    def __call__(
        self,
        track: FrozenTrackPlan,
        _authorization: PaidAuthorization,
        **_kwargs,
    ) -> AttemptResult:
        invocation_index = len(self.invocations)
        assert track is self.plan.tracks[invocation_index]
        self.invocations.append(track.track_id)
        self._active += 1
        self.max_active = max(self.max_active, self._active)
        assert self._active == 1, "batch attempts must never overlap"
        try:
            return self._run_track(track, invocation_index)
        finally:
            self._active -= 1

    def _run_track(
        self,
        track: FrozenTrackPlan,
        invocation_index: int,
    ) -> AttemptResult:
        is_failure = invocation_index == self.case.failure_position
        failure_type = self.case.failure_type if is_failure else None
        synthetic_calls = (
            0 if failure_type in _PRECALL_FAILURES else 1
        )
        self.synthetic_call_counts[track.track_id] = synthetic_calls
        self.store.append_transition(
            track.track_id,
            track.transaction_id,
            operation_id="synthetic-authorization-consumed",
            event_type="authorization-consumed",
            state_after=TransactionState.RUNNING,
            details={
                "attempt_id": "attempt-001",
                "authorization_sha256": self.authorization_sha256,
                "command_sha256": track.command_sha256,
                "maximum_new_calls": track.maximum_new_calls,
                "automatic_retry_performed": False,
                "synthetic_call_count": synthetic_calls,
            },
            occurred_at_utc="2026-09-14T12:03:00Z",
        )

        transaction_root = self.store.transaction_path(
            track.track_id, track.transaction_id
        )
        attempts_root = transaction_root / "attempts"
        attempts_root.mkdir(parents=True, exist_ok=False)

        if failure_type == "charge-uncertain":
            marker = attempts_root / "attempt-001.ambiguous.json"
            marker.write_bytes(
                json.dumps(
                    {
                        "attempt_id": "attempt-001",
                        "failure_type": failure_type,
                        "synthetic_call_count": synthetic_calls,
                        "track_id": track.track_id,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            self.evidence_paths[track.track_id] = marker
            self.store.append_transition(
                track.track_id,
                track.transaction_id,
                operation_id="synthetic-charge-uncertain",
                event_type="attempt-charge-uncertain",
                state_after=TransactionState.CHARGE_UNCERTAIN,
                details={
                    "attempt_id": "attempt-001",
                    "evidence_sha256": sha256_file(marker),
                    "failure_type": failure_type,
                    "automatic_retry_performed": False,
                    "synthetic_call_count": synthetic_calls,
                },
                occurred_at_utc="2026-09-14T12:03:01Z",
            )
            raise AttemptChargeUncertain(
                "synthetic launched attempt has explicitly uncertain evidence"
            )

        bundle_root = attempts_root / "attempt-001"
        bundle_root.mkdir()
        console_path = bundle_root / "render-console.log"
        console_path.write_text(
            (
                f"track_id={track.track_id};case={self.case.nonce:016x};"
                f"result={failure_type or 'rendered'};"
                f"synthetic_calls={synthetic_calls}\n"
            ),
            encoding="utf-8",
        )
        result_authorization_sha256 = (
            _digest(f"mismatched-authorization-{self.case.nonce}")
            if failure_type == "authorization-mismatch"
            else self.authorization_sha256
        )
        result = AttemptResult(
            schema_version=1,
            attempt_id="attempt-001",
            transaction_id=track.transaction_id,
            authorization_sha256=result_authorization_sha256,
            working_directory=".",
            argv=track.command_argv,
            command_sha256=track.command_sha256,
            profile_label=track.effective_config.profile_label,
            started_at_utc="2026-09-14T12:03:00Z",
            ended_at_utc="2026-09-14T12:03:01Z",
            child_launched=True,
            native_return_code=(self.case.nonzero_status if is_failure else 0),
            termination_signal=None,
            console_path=console_path.relative_to(self.workspace).as_posix(),
            console_sha256=sha256_file(console_path),
            automatic_retry_performed=False,
            environment_persisted=False,
        )
        result_codec = StrictRecordCodec(AttemptResult)
        result_path = bundle_root / "attempt.json"
        result_codec.write_atomic(result_path, result)
        self.evidence_paths[track.track_id] = result_path

        state_after = (
            TransactionState.BLOCKED if is_failure else TransactionState.RENDERED
        )
        details: dict[str, str | int | bool] = {
            "attempt_id": "attempt-001",
            "attempt_result_sha256": result_codec.sha256(result),
            "automatic_retry_performed": False,
            "native_return_code": result.native_return_code,
            "synthetic_call_count": synthetic_calls,
        }
        if failure_type is not None:
            details["failure_type"] = failure_type
        self.store.append_transition(
            track.track_id,
            track.transaction_id,
            operation_id=(
                "synthetic-attempt-blocked" if is_failure else "synthetic-rendered"
            ),
            event_type=(
                "attempt-blocked" if is_failure else "attempt-rendered"
            ),
            state_after=state_after,
            details=details,
            occurred_at_utc="2026-09-14T12:03:01Z",
        )
        return result


def _assert_case(
    case: _GeneratedCase,
    plan: FrozenBatchPlan,
    store: TransactionStore,
    runner: _SyntheticFailFastRunner,
    result,
) -> None:
    expected_started_tracks = plan.tracks[: case.failure_position + 1]
    expected_suffix = plan.tracks[case.failure_position + 1 :]
    expected_started_ids = tuple(
        track.transaction_id for track in expected_started_tracks
    )
    expected_completed_ids = tuple(
        track.transaction_id for track in plan.tracks[: case.failure_position]
    )

    assert tuple(runner.invocations) == tuple(
        track.track_id for track in expected_started_tracks
    )
    assert runner.max_active == 1
    assert result.started_transaction_ids == expected_started_ids
    assert result.completed_prefix_transaction_ids == expected_completed_ids
    assert result.stopped_transaction_id == plan.tracks[
        case.failure_position
    ].transaction_id
    assert result.fresh_preflight_required
    assert result.fresh_authorization_required

    accepted_result_count = len(expected_started_tracks) - (
        1 if case.failure_type in _FAILURES_WITHOUT_ACCEPTED_RESULT else 0
    )
    assert tuple(item.transaction_id for item in result.attempt_results) == tuple(
        track.transaction_id for track in expected_started_tracks[:accepted_result_count]
    )
    assert all(
        not item.automatic_retry_performed and not item.environment_persisted
        for item in result.attempt_results
    )

    for track in plan.tracks[: case.failure_position]:
        snapshot = store.inspect_transaction(track.track_id, track.transaction_id)
        assert snapshot.state is TransactionState.RENDERED
        assert runner.synthetic_call_counts[track.track_id] == 1
        assert sum(
            event.state_after is TransactionState.RUNNING
            for event in snapshot.events
        ) == 1

    failed_track = plan.tracks[case.failure_position]
    failed_snapshot = store.inspect_transaction(
        failed_track.track_id, failed_track.transaction_id
    )
    expected_failed_state = (
        TransactionState.CHARGE_UNCERTAIN
        if case.failure_type == "charge-uncertain"
        else TransactionState.BLOCKED
    )
    assert failed_snapshot.state is expected_failed_state
    assert failed_snapshot.payloads[-1].details["failure_type"] == case.failure_type
    assert sum(
        event.state_after is TransactionState.RUNNING
        for event in failed_snapshot.events
    ) == 1
    expected_failed_calls = 0 if case.failure_type in _PRECALL_FAILURES else 1
    assert runner.synthetic_call_counts[failed_track.track_id] == expected_failed_calls

    evidence_paths = tuple(
        runner.evidence_paths[track.track_id] for track in expected_started_tracks
    )
    assert len(set(evidence_paths)) == len(expected_started_tracks)
    assert len({sha256_file(path) for path in evidence_paths}) == len(
        expected_started_tracks
    )
    for track, evidence_path in zip(
        expected_started_tracks, evidence_paths, strict=True
    ):
        assert evidence_path.is_file()
        transaction_root = store.transaction_path(
            track.track_id, track.transaction_id
        )
        assert evidence_path.is_relative_to(transaction_root / "attempts")
    started_head_hashes = tuple(
        store.inspect_transaction(track.track_id, track.transaction_id).head_event_sha256
        for track in expected_started_tracks
    )
    assert len(set(started_head_hashes)) == len(expected_started_tracks)

    for track in expected_suffix:
        snapshot = store.inspect_transaction(track.track_id, track.transaction_id)
        assert snapshot.state is TransactionState.AUTHORIZATION_REQUIRED
        assert all(
            event.state_after is not TransactionState.RUNNING
            for event in snapshot.events
        )
        assert not (
            store.transaction_path(track.track_id, track.transaction_id) / "attempts"
        ).exists()
        assert runner.synthetic_call_counts.get(track.track_id, 0) == 0
        assert track.track_id not in runner.evidence_paths

    ledger_status = store.inspect_plan_status(plan)
    assert result.plan_status == ledger_status
    assert ledger_status.status is (
        BatchStatus.BLOCKED
        if case.failure_position == 0
        else BatchStatus.PARTIAL
    )
    assert ledger_status.selected_count == case.batch_size
    assert ledger_status.completed_count == 0
    assert ledger_status.blocked_count == 1
    assert ledger_status.unstarted_count == len(expected_suffix)


def test_batch_execution_is_fail_fast_with_independent_transactions(
    tmp_path: Path,
) -> None:
    """Feature: audiobook-production-workflow, Property 6: Batch execution is fail-fast with independent transactions"""

    assert GENERATED_CASES == 120
    print(f"{PROPERTY_TAG}; seed={PROPERTY_SEED:#x}; cases={GENERATED_CASES}")
    generated = tuple(_generated_cases(random.Random(PROPERTY_SEED)))
    assert len(generated) == GENERATED_CASES

    observed_coverage: set[tuple[int, int, str]] = set()
    for case_index, case in enumerate(generated):
        context = (
            f"{PROPERTY_TAG}; seed={PROPERTY_SEED:#x}; case={case_index}; "
            f"input={case!r}"
        )
        try:
            workspace = tmp_path / f"case-{case_index:03d}"
            workspace.mkdir()
            plan = _plan(case)
            authorization = _authorization(plan, case_nonce=case.nonce)
            authorization_start = build_authorization_start_request(authorization)
            store = _ready_batch(workspace, plan, authorization)

            # A forged aggregate cache must not influence coordinator truth.
            store.index_path.parent.mkdir(parents=True, exist_ok=True)
            store.index_path.write_text(
                '{"forged":"non-authoritative"}', encoding="utf-8"
            )
            runner = _SyntheticFailFastRunner(
                case=case,
                plan=plan,
                workspace=workspace,
                store=store,
                authorization_sha256=authorization_start.authorization_sha256,
            )
            result = execute_authorized_batch(
                plan,
                authorization,
                authorization_start,
                workspace_root=workspace,
                store=store,
                attempt_runner=runner,
                clock=_fixed_clock,
            )
            _assert_case(case, plan, store, runner, result)
            observed_coverage.add(
                (case.batch_size, case.failure_position, case.failure_type)
            )
        except Exception as exc:
            raise AssertionError(context) from exc

    expected_coverage = {
        (batch_size, failure_position, failure_type)
        for batch_size in range(1, MAX_BATCH_SIZE + 1)
        for failure_position in range(batch_size)
        for failure_type in _FAILURE_TYPES
    }
    assert observed_coverage == expected_coverage
