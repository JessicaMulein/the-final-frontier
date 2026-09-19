"""Sequential fail-fast coordination for exact authorized production batches.

The coordinator is intentionally small: immutable plan/authorization validation
stays in their owning modules, each paid attempt stays in its independent Track
transaction, and aggregate status is always reconstructed from those transaction
ledgers.  This module performs no AWS, model, narration, or network work itself.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from .errors import InputError
from .production_attempt import AttemptChargeUncertain, run_atomic_paid_attempt
from .production_authorization import (
    AuthorizationStartRequest,
    build_authorization_start_request,
)
from .production_models import (
    AttemptResult,
    FrozenBatchPlan,
    FrozenTrackPlan,
    PaidAuthorization,
    StrictRecordCodec,
    TransactionState,
)
from .production_transactions import (
    PlanStatus,
    TransactionHealth,
    TransactionStore,
)
from .util import workspace_relative

Clock = Callable[[], datetime]
AttemptRunner = Callable[..., AttemptResult]

_SUCCESSFUL_EXECUTION_STATES = frozenset(
    {
        TransactionState.RENDERED,
        TransactionState.VALIDATED,
        TransactionState.DELIVERED,
    }
)
_STOPPED_STATES = frozenset(
    {
        TransactionState.RUNNING,
        TransactionState.CHARGE_UNCERTAIN,
        TransactionState.BLOCKED,
    }
)
_FRESH_SCOPE_MESSAGE = (
    "Batch continuation after a start or stop requires fresh preflight and fresh "
    "authorization for a new exact scope"
)


def _system_clock() -> datetime:
    return datetime.now(UTC)


def _clock_now(clock: Clock) -> datetime:
    try:
        value = clock()
    except Exception as exc:
        raise InputError("Batch coordinator clock failed") from exc
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise InputError("Batch coordinator clock must return a timezone-aware datetime")
    return value.astimezone(UTC)


def _format_utc(value: datetime) -> str:
    rendered = value.astimezone(UTC).isoformat(timespec="microseconds")
    if rendered.endswith(".000000+00:00"):
        return rendered.replace(".000000+00:00", "Z")
    return rendered.replace("+00:00", "Z")


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.removesuffix("Z") + "+00:00")


def _completed_prefix(status: PlanStatus) -> tuple[str, ...]:
    completed: list[str] = []
    for track in status.tracks:
        if (
            track.health is TransactionHealth.VALID
            and track.state in _SUCCESSFUL_EXECUTION_STATES
        ):
            completed.append(track.transaction_id)
            continue
        break
    return tuple(completed)


@dataclass(frozen=True, slots=True)
class BatchExecutionResult:
    """One fail-fast invocation, with aggregate state taken only from ledgers."""

    plan_status: PlanStatus
    started_transaction_ids: tuple[str, ...]
    completed_prefix_transaction_ids: tuple[str, ...]
    attempt_results: tuple[AttemptResult, ...]
    stopped_transaction_id: str | None
    fresh_preflight_required: bool
    fresh_authorization_required: bool

    def __post_init__(self) -> None:
        if not isinstance(self.plan_status, PlanStatus):
            raise InputError("Batch execution result requires PlanStatus ledger truth")
        scope = tuple(item.transaction_id for item in self.plan_status.tracks)
        if not isinstance(self.started_transaction_ids, tuple) or (
            self.started_transaction_ids != scope[: len(self.started_transaction_ids)]
        ):
            raise InputError("Started batch transactions must be an ordered plan prefix")
        if len(set(self.started_transaction_ids)) != len(self.started_transaction_ids):
            raise InputError("Started batch transactions must be unique")
        if self.completed_prefix_transaction_ids != _completed_prefix(self.plan_status):
            raise InputError("Completed prefix must be derived from independent ledgers")
        if not isinstance(self.attempt_results, tuple) or not all(
            isinstance(item, AttemptResult) for item in self.attempt_results
        ):
            raise InputError("Batch attempt results must contain AttemptResult records")
        result_ids = tuple(item.transaction_id for item in self.attempt_results)
        if result_ids != self.started_transaction_ids[: len(result_ids)]:
            raise InputError("Attempt results must follow the started transaction prefix")
        if len(self.started_transaction_ids) - len(result_ids) not in {0, 1}:
            raise InputError("At most one started Track may lack definitive attempt evidence")
        if self.stopped_transaction_id is None:
            if self.fresh_preflight_required or self.fresh_authorization_required:
                raise InputError("A completed coordinator invocation cannot require fresh scope")
            if self.started_transaction_ids != scope:
                raise InputError("A non-stopped coordinator invocation must cover the full scope")
        else:
            if (
                not self.started_transaction_ids
                or self.stopped_transaction_id != self.started_transaction_ids[-1]
            ):
                raise InputError("Stopped transaction must be the final started Track")
            if not (
                self.fresh_preflight_required and self.fresh_authorization_required
            ):
                raise InputError("A stopped batch requires fresh preflight and authorization")


def _validate_exact_start_scope(
    plan: FrozenBatchPlan,
    authorization: PaidAuthorization,
    authorization_start: AuthorizationStartRequest,
    *,
    workspace_root: Path,
    store: TransactionStore,
    now: datetime,
) -> PlanStatus:
    plan_codec = StrictRecordCodec(FrozenBatchPlan)
    authorization_codec = StrictRecordCodec(PaidAuthorization)
    plan_codec.dump_bytes(plan)
    authorization_codec.dump_bytes(authorization)
    if not isinstance(authorization_start, AuthorizationStartRequest):
        raise InputError("Batch execution requires AuthorizationStartRequest")
    if not isinstance(store, TransactionStore):
        raise InputError("Batch execution requires TransactionStore")

    root = workspace_root.expanduser().resolve()
    workspace_relative(root, store.book_root)
    if store.book_id != plan.book_id:
        raise InputError("Transaction store book identity differs from the frozen plan")
    if authorization.plan_sha256 != plan_codec.sha256(plan):
        raise InputError("Paid authorization is not bound to the exact frozen plan")
    if authorization_start != build_authorization_start_request(authorization):
        raise InputError("Authorization start scope is altered, incomplete, or unlisted")

    expected_transactions = tuple(track.transaction_id for track in plan.tracks)
    expected_tracks = tuple(track.track_id for track in plan.tracks)
    expected_commands = tuple(track.command_sha256 for track in plan.tracks)
    expected_calls = {
        track.track_id: authorization.maximum_new_calls_by_track[track.track_id]
        for track in plan.tracks
    }
    if authorization.exact_transaction_ids != expected_transactions:
        raise InputError("Paid authorization transaction order differs from the frozen plan")
    if authorization.exact_track_ids != expected_tracks:
        raise InputError("Paid authorization Track order differs from the frozen plan")
    if authorization.exact_command_sha256s != expected_commands:
        raise InputError("Paid authorization command order differs from the frozen plan")
    if dict(authorization.maximum_new_calls_by_track) != expected_calls:
        raise InputError("Paid authorization call scope differs from the frozen plan")
    for track in plan.tracks:
        if authorization.maximum_new_calls_by_track[track.track_id] > track.maximum_new_calls:
            raise InputError("Paid authorization call ceiling exceeds a frozen Track bound")

    issued = _parse_utc(authorization.issued_at_utc)
    expires = _parse_utc(authorization.expires_at_utc)
    if now < issued:
        raise InputError("Paid authorization is not yet valid")
    if now >= expires:
        raise InputError("Paid authorization is expired")
    if not authorization.one_shot:
        raise InputError("Paid authorization must be one-shot")

    status = store.inspect_plan_status(plan)
    for track, track_status in zip(plan.tracks, status.tracks, strict=True):
        if track_status.health is not TransactionHealth.VALID:
            raise InputError(
                f"Independent transaction truth is missing or corrupt for {track.track_id!r}"
            )
        snapshot = store.inspect_transaction(track.track_id, track.transaction_id)
        if snapshot.state is not TransactionState.AUTHORIZATION_REQUIRED:
            raise InputError(_FRESH_SCOPE_MESSAGE)
        if snapshot.payloads[-1].details.get("preflight_sha256") != (
            authorization.preflight_sha256
        ):
            raise InputError(_FRESH_SCOPE_MESSAGE)
    return status


def _record_runner_block(
    store: TransactionStore,
    track: FrozenTrackPlan,
    authorization_start: AuthorizationStartRequest,
    *,
    finding_category: str,
    occurred_at_utc: str,
) -> TransactionState:
    snapshot = store.inspect_transaction(track.track_id, track.transaction_id)
    if snapshot.state in {
        TransactionState.AUTHORIZATION_REQUIRED,
        TransactionState.RUNNING,
    }:
        store.append_transition(
            track.track_id,
            track.transaction_id,
            operation_id="batch-coordinator-stop",
            event_type="batch-coordinator-blocked",
            state_after=TransactionState.BLOCKED,
            details={
                "authorization_sha256": authorization_start.authorization_sha256,
                "finding_category": finding_category,
                "automatic_retry_performed": False,
                "fresh_preflight_required": True,
                "fresh_authorization_required": True,
            },
            occurred_at_utc=occurred_at_utc,
        )
        return TransactionState.BLOCKED
    return snapshot.state


def _validate_attempt_result(
    result: AttemptResult,
    track: FrozenTrackPlan,
    authorization_start: AuthorizationStartRequest,
) -> None:
    if not isinstance(result, AttemptResult):
        raise InputError("Attempt runner did not return AttemptResult")
    if result.transaction_id != track.transaction_id:
        raise InputError("Attempt result transaction differs from the started Track")
    if result.authorization_sha256 != authorization_start.authorization_sha256:
        raise InputError("Attempt result authorization differs from the exact batch scope")
    if result.argv != track.command_argv or result.command_sha256 != track.command_sha256:
        raise InputError("Attempt result command differs from the frozen Track command")


def _result_from_truth(
    store: TransactionStore,
    plan: FrozenBatchPlan,
    *,
    started: tuple[str, ...],
    attempts: tuple[AttemptResult, ...],
    stopped_transaction_id: str | None,
) -> BatchExecutionResult:
    status = store.inspect_plan_status(plan)
    if stopped_transaction_id is not None:
        scope = tuple(item.transaction_id for item in status.tracks)
        stopped_index = scope.index(stopped_transaction_id)
        stopped = status.tracks[stopped_index]
        if (
            stopped.health is not TransactionHealth.VALID
            or stopped.state not in _STOPPED_STATES
        ):
            raise InputError("Stopped Track lacks independent blocking transaction truth")
        for suffix in status.tracks[stopped_index + 1 :]:
            if not (
                suffix.health is TransactionHealth.VALID
                and suffix.state is TransactionState.AUTHORIZATION_REQUIRED
            ):
                raise InputError(
                    "Unstarted suffix transaction truth changed after the fail-fast stop"
                )
    else:
        if any(
            item.health is not TransactionHealth.VALID
            or item.state not in _SUCCESSFUL_EXECUTION_STATES
            for item in status.tracks
        ):
            raise InputError("Batch ended without a stop but not every Track rendered")

    return BatchExecutionResult(
        plan_status=status,
        started_transaction_ids=started,
        completed_prefix_transaction_ids=_completed_prefix(status),
        attempt_results=attempts,
        stopped_transaction_id=stopped_transaction_id,
        fresh_preflight_required=stopped_transaction_id is not None,
        fresh_authorization_required=stopped_transaction_id is not None,
    )


def execute_authorized_batch(
    plan: FrozenBatchPlan,
    authorization: PaidAuthorization,
    authorization_start: AuthorizationStartRequest,
    *,
    workspace_root: Path,
    store: TransactionStore,
    exact_environment: Mapping[str, str] | None = None,
    output_stream: TextIO | None = None,
    attempt_runner: AttemptRunner = run_atomic_paid_attempt,
    clock: Clock = _system_clock,
) -> BatchExecutionResult:
    """Execute one exact batch sequentially and stop after the first bad Track.

    ``authorization_start`` must already have passed Task 4.1's complete,
    preflight-aware validator.  This boundary rechecks immutable scope, current
    ledger/preflight bindings, and expiration before dispatch.  Once any Track
    blocks, returns nonzero, or becomes charge-uncertain, no suffix runner is
    invoked; a later invocation is rejected until a new exact plan scope receives
    fresh preflight and fresh authorization.
    """

    if not callable(attempt_runner):
        raise InputError("attempt_runner must be callable")
    now = _clock_now(clock)
    started: list[str] = []
    attempts: list[AttemptResult] = []

    # One paid Track at a time for this book, including across cooperating batch
    # coordinators.  Track-level locks remain independent transaction protection.
    with store.book_lock():
        _validate_exact_start_scope(
            plan,
            authorization,
            authorization_start,
            workspace_root=workspace_root,
            store=store,
            now=now,
        )

        for track in plan.tracks:
            started.append(track.transaction_id)
            try:
                result = attempt_runner(
                    track,
                    authorization,
                    plan=plan,
                    authorization_start=authorization_start,
                    workspace_root=workspace_root,
                    store=store,
                    exact_environment=exact_environment,
                    output_stream=output_stream,
                    clock=clock,
                )
                _validate_attempt_result(result, track, authorization_start)
            except AttemptChargeUncertain:
                state = store.inspect_transaction(
                    track.track_id, track.transaction_id
                ).state
                if state not in {
                    TransactionState.RUNNING,
                    TransactionState.CHARGE_UNCERTAIN,
                }:
                    _record_runner_block(
                        store,
                        track,
                        authorization_start,
                        finding_category="attempt-charge-uncertain",
                        occurred_at_utc=_format_utc(_clock_now(clock)),
                    )
                return _result_from_truth(
                    store,
                    plan,
                    started=tuple(started),
                    attempts=tuple(attempts),
                    stopped_transaction_id=track.transaction_id,
                )
            except InputError:
                _record_runner_block(
                    store,
                    track,
                    authorization_start,
                    finding_category="attempt-runner-blocked",
                    occurred_at_utc=_format_utc(_clock_now(clock)),
                )
                return _result_from_truth(
                    store,
                    plan,
                    started=tuple(started),
                    attempts=tuple(attempts),
                    stopped_transaction_id=track.transaction_id,
                )

            attempts.append(result)
            state = store.inspect_transaction(track.track_id, track.transaction_id).state
            if (
                result.native_return_code != 0
                or state in _STOPPED_STATES
            ):
                if state not in _STOPPED_STATES:
                    state = _record_runner_block(
                        store,
                        track,
                        authorization_start,
                        finding_category="nonzero-attempt-result",
                        occurred_at_utc=_format_utc(_clock_now(clock)),
                    )
                return _result_from_truth(
                    store,
                    plan,
                    started=tuple(started),
                    attempts=tuple(attempts),
                    stopped_transaction_id=track.transaction_id,
                )
            if state not in _SUCCESSFUL_EXECUTION_STATES:
                _record_runner_block(
                    store,
                    track,
                    authorization_start,
                    finding_category="attempt-state-mismatch",
                    occurred_at_utc=_format_utc(_clock_now(clock)),
                )
                return _result_from_truth(
                    store,
                    plan,
                    started=tuple(started),
                    attempts=tuple(attempts),
                    stopped_transaction_id=track.transaction_id,
                )

        return _result_from_truth(
            store,
            plan,
            started=tuple(started),
            attempts=tuple(attempts),
            stopped_transaction_id=None,
        )


__all__ = [
    "BatchExecutionResult",
    "execute_authorized_batch",
]
