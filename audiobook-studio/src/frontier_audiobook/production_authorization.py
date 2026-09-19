"""Exact, finite, local-only paid authorization creation and validation.

This module never consumes an authorization and never launches a child. It binds
one immutable production plan to Task 2.1's exact cache-miss ceilings and Task
2.2's sealed Decimal estimate/rate evidence, requires a fresh exact display
confirmation, and validates first-start eligibility from authoritative transaction
ledgers before the later atomic attempt wrapper consumes anything.
"""

from __future__ import annotations

import os
import re
import secrets
from collections.abc import Callable, Mapping
from dataclasses import dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from typing import Any

from .errors import InputError
from .production_config import BookProductionConfig
from .production_models import (
    RECORD_SCHEMA_VERSION,
    TOKEN_MODALITIES,
    AuthorizationDecision,
    FrozenBatchPlan,
    PaidAuthorization,
    StrictRecordCodec,
    TransactionState,
    authorization_confirmation_sha256,
    canonical_sha256,
    seal_record,
)
from .production_preflight import (
    BoundedPreflightEstimateResult,
    LocalPreflightResult,
    OfficialRateTarget,
)
from .production_transactions import TransactionSpec, TransactionStore
from .util import (
    atomic_write_bytes,
    durable_mkdir,
    fsync_directory,
    read_bytes_nofollow,
    resolve_inside,
)

AUTHORIZATION_CONFIRMATION_PROMPT = (
    "Authorize this exact paid production scope once under the displayed plan and "
    "preflight digests, ordered Tracks and commands, call ceilings, expiration, and "
    "approved maximum estimated pre-tax amount?"
)

_IDENTIFIER_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_UTC_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)
_DECIMAL_PATTERN = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d+)?$")
Clock = Callable[[], datetime]


def _system_clock() -> datetime:
    return datetime.now(UTC)


def _clock_now(clock: Clock, label: str) -> datetime:
    if not callable(clock):
        raise InputError("authorization clock must be callable")
    value = clock()
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise InputError(f"{label} clock must return a timezone-aware datetime")
    if value.utcoffset() != timedelta(0):
        raise InputError(f"{label} clock must return UTC")
    return value.astimezone(UTC)


def _format_utc(value: datetime) -> str:
    timespec = "microseconds" if value.microsecond else "seconds"
    return value.isoformat(timespec=timespec).replace("+00:00", "Z")


def _require_identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER_PATTERN.fullmatch(value):
        raise InputError(f"{label} must be a lowercase hyphenated identifier")
    return value


def _require_sha256(value: object, label: str, *, allow_empty: bool = False) -> str:
    if allow_empty and value == "":
        return ""
    if not isinstance(value, str) or not _SHA256_PATTERN.fullmatch(value):
        raise InputError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _parse_utc(value: object, label: str) -> datetime:
    if not isinstance(value, str) or not _UTC_PATTERN.fullmatch(value):
        raise InputError(f"{label} must be an ISO-8601 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise InputError(f"{label} is not a valid UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise InputError(f"{label} must be UTC")
    return parsed.astimezone(UTC)


def _parse_decimal(value: object, label: str) -> Decimal:
    if not isinstance(value, str) or not _DECIMAL_PATTERN.fullmatch(value):
        raise InputError(f"{label} must be a nonnegative plain decimal string")
    try:
        parsed = Decimal(value)
    except InvalidOperation as exc:  # pragma: no cover - guarded by the pattern
        raise InputError(f"{label} must be a valid decimal string") from exc
    if not parsed.is_finite() or parsed < 0:
        raise InputError(f"{label} must be finite and nonnegative")
    return parsed


def _require_scope_tuple(
    values: object,
    label: str,
    validator: Callable[[object, str], str],
) -> tuple[str, ...]:
    if not isinstance(values, tuple) or not values:
        raise InputError(f"{label} must be a nonempty tuple")
    checked = tuple(validator(item, f"{label}[{index}]") for index, item in enumerate(values))
    if len(set(checked)) != len(checked):
        raise InputError(f"{label} must contain unique values")
    return checked


def _require_call_rows(rows: object, label: str) -> tuple[tuple[str, int], ...]:
    if not isinstance(rows, tuple) or not rows:
        raise InputError(f"{label} must be a nonempty tuple")
    checked: list[tuple[str, int]] = []
    for index, row in enumerate(rows):
        if not isinstance(row, tuple) or len(row) != 2:
            raise InputError(f"{label}[{index}] must be a (Track ID, calls) tuple")
        track_id = _require_identifier(row[0], f"{label}[{index}] Track ID")
        calls = row[1]
        if type(calls) is not int or calls < 0:
            raise InputError(f"{label}[{index}] calls must be an integer >= 0")
        checked.append((track_id, calls))
    if len({track_id for track_id, _calls in checked}) != len(checked):
        raise InputError(f"{label} Track IDs must be unique")
    return tuple(checked)


def _verify_sealed(value: Any, label: str) -> str:
    if not hasattr(value, "canonical_sha256"):
        raise InputError(f"{label} does not contain a canonical digest")
    from .production_evidence import assert_typed_evidence_safe

    assert_typed_evidence_safe(value)
    actual = _require_sha256(getattr(value, "canonical_sha256"), f"{label} canonical_sha256")
    expected = canonical_sha256(value, omit_fields=("canonical_sha256",))
    if actual != expected:
        raise InputError(f"{label} canonical digest does not match its content")
    return actual


@dataclass(frozen=True, slots=True)
class AuthorizationDisplay:
    """The complete non-secret scope shown with a fresh one-use challenge."""

    schema_version: int
    authorization_id: str
    plan_sha256: str
    preflight_sha256: str
    local_preflight_sha256: str
    estimate_sha256: str
    official_rate_provenance_sha256: str
    exact_transaction_ids: tuple[str, ...]
    exact_track_ids: tuple[str, ...]
    exact_command_sha256s: tuple[str, ...]
    maximum_new_calls_by_track: tuple[tuple[str, int], ...]
    maximum_new_calls_total: int
    estimated_pre_tax_usd: str
    operator_approved_max_estimated_pre_tax_usd: str
    issued_at_utc: str
    expires_at_utc: str
    one_shot: bool
    confirmation_challenge: str
    confirmation_prompt: str
    canonical_sha256: str

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != RECORD_SCHEMA_VERSION:
            raise InputError(
                f"authorization display schema_version must be integer {RECORD_SCHEMA_VERSION}"
            )
        _require_identifier(self.authorization_id, "authorization display authorization_id")
        for field_name in (
            "plan_sha256",
            "preflight_sha256",
            "local_preflight_sha256",
            "estimate_sha256",
            "official_rate_provenance_sha256",
            "confirmation_challenge",
        ):
            _require_sha256(getattr(self, field_name), f"authorization display {field_name}")
        transactions = _require_scope_tuple(
            self.exact_transaction_ids,
            "authorization display exact_transaction_ids",
            _require_identifier,
        )
        tracks = _require_scope_tuple(
            self.exact_track_ids,
            "authorization display exact_track_ids",
            _require_identifier,
        )
        commands = _require_scope_tuple(
            self.exact_command_sha256s,
            "authorization display exact_command_sha256s",
            _require_sha256,
        )
        if not len(transactions) == len(tracks) == len(commands):
            raise InputError("authorization display exact scope lists must have equal lengths")
        calls = _require_call_rows(
            self.maximum_new_calls_by_track,
            "authorization display maximum_new_calls_by_track",
        )
        if tuple(track_id for track_id, _calls in calls) != tracks:
            raise InputError("authorization display call rows must follow exact_track_ids")
        if type(self.maximum_new_calls_total) is not int or self.maximum_new_calls_total < 0:
            raise InputError("authorization display maximum_new_calls_total must be an integer >= 0")
        if self.maximum_new_calls_total != sum(value for _track_id, value in calls):
            raise InputError("authorization display total calls must equal per-Track ceilings")
        estimate = _parse_decimal(
            self.estimated_pre_tax_usd,
            "authorization display estimated_pre_tax_usd",
        )
        approved = _parse_decimal(
            self.operator_approved_max_estimated_pre_tax_usd,
            "authorization display operator-approved maximum",
        )
        if approved < estimate:
            raise InputError("operator-approved maximum must cover the exact preflight estimate")
        issued = _parse_utc(self.issued_at_utc, "authorization display issued_at_utc")
        expires = _parse_utc(self.expires_at_utc, "authorization display expires_at_utc")
        if expires <= issued:
            raise InputError("authorization display expiration must be after issue time")
        if type(self.one_shot) is not bool or not self.one_shot:
            raise InputError("authorization display one_shot must be true")
        if self.confirmation_prompt != AUTHORIZATION_CONFIRMATION_PROMPT:
            raise InputError("authorization display must use the exact confirmation prompt")
        _require_sha256(
            self.canonical_sha256,
            "authorization display canonical_sha256",
            allow_empty=True,
        )


@dataclass(frozen=True, slots=True)
class ExactAuthorizationConfirmation:
    """Injected operator response to one exact fresh challenge."""

    schema_version: int
    display_sha256: str
    challenge: str
    decision: AuthorizationDecision

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != RECORD_SCHEMA_VERSION:
            raise InputError(
                f"authorization confirmation schema_version must be integer {RECORD_SCHEMA_VERSION}"
            )
        _require_sha256(self.display_sha256, "authorization confirmation display_sha256")
        _require_sha256(self.challenge, "authorization confirmation challenge")
        if not isinstance(self.decision, AuthorizationDecision):
            raise InputError("authorization confirmation decision is invalid")


@dataclass(frozen=True, slots=True)
class AuthorizationStartRequest:
    """Ephemeral exact start scope; lifecycle truth comes only from ledgers."""

    authorization_sha256: str
    plan_sha256: str
    preflight_sha256: str
    exact_transaction_ids: tuple[str, ...]
    exact_track_ids: tuple[str, ...]
    exact_command_sha256s: tuple[str, ...]
    maximum_new_calls_by_track: tuple[tuple[str, int], ...]
    maximum_new_calls_total: int

    def __post_init__(self) -> None:
        for field_name in ("authorization_sha256", "plan_sha256", "preflight_sha256"):
            _require_sha256(getattr(self, field_name), f"authorization start {field_name}")
        transactions = _require_scope_tuple(
            self.exact_transaction_ids,
            "authorization start exact_transaction_ids",
            _require_identifier,
        )
        tracks = _require_scope_tuple(
            self.exact_track_ids,
            "authorization start exact_track_ids",
            _require_identifier,
        )
        commands = _require_scope_tuple(
            self.exact_command_sha256s,
            "authorization start exact_command_sha256s",
            _require_sha256,
        )
        if not len(transactions) == len(tracks) == len(commands):
            raise InputError("authorization start exact scope lists must have equal lengths")
        calls = _require_call_rows(
            self.maximum_new_calls_by_track,
            "authorization start maximum_new_calls_by_track",
        )
        if tuple(track_id for track_id, _calls in calls) != tracks:
            raise InputError("authorization start call rows must follow exact_track_ids")
        if type(self.maximum_new_calls_total) is not int or self.maximum_new_calls_total < 0:
            raise InputError("authorization start maximum_new_calls_total must be an integer >= 0")
        if self.maximum_new_calls_total != sum(value for _track_id, value in calls):
            raise InputError("authorization start total calls must equal per-Track ceilings")


@dataclass(frozen=True, slots=True)
class _AuthorizationBindings:
    plan_sha256: str
    local_preflight_sha256: str
    preflight_sha256: str
    estimate_sha256: str
    official_rate_provenance_sha256: str
    transaction_ids: tuple[str, ...]
    track_ids: tuple[str, ...]
    command_sha256s: tuple[str, ...]
    call_rows: tuple[tuple[str, int], ...]
    maximum_new_calls_total: int
    estimated_pre_tax_usd: str
    preflight_checked_at: datetime
    preflight_deadline: datetime


def _expected_profile_labels(plan: FrozenBatchPlan) -> tuple[str, ...]:
    return tuple(
        dict.fromkeys(track.effective_config.profile_label for track in plan.tracks)
    )


def _expected_rate_targets(plan: FrozenBatchPlan) -> tuple[OfficialRateTarget, ...]:
    return tuple(
        dict.fromkeys(
            OfficialRateTarget(
                track.effective_config.model_id,
                track.effective_config.region,
            )
            for track in plan.tracks
        )
    )


def _validate_decimal_estimate(
    config: BookProductionConfig,
    plan: FrozenBatchPlan,
    local_preflight: LocalPreflightResult,
    bounded_preflight: BoundedPreflightEstimateResult,
) -> None:
    estimate = bounded_preflight.estimate
    expected_envelopes = tuple(
        (modality, getattr(config.estimate, f"{modality}_tokens_per_call"))
        for modality in TOKEN_MODALITIES
    )
    actual_envelopes = tuple(
        (item.modality, item.tokens) for item in estimate.configured_tokens_per_call
    )
    if actual_envelopes != expected_envelopes:
        raise InputError("Task 2.2 token envelopes differ from current production configuration")

    cards = {card.target: card for card in bounded_preflight.official_rate_cards}
    if tuple(cards) != _expected_rate_targets(plan):
        raise InputError("Task 2.2 official rate targets do not match the exact plan scope")

    call_map = dict(local_preflight.maximum_new_calls_by_track)
    if tuple(item.track_id for item in estimate.tracks) != tuple(call_map):
        raise InputError("Task 2.2 Track estimates do not match Task 2.1 ordered scope")

    expected_aggregate = {modality: Decimal("0") for modality in TOKEN_MODALITIES}
    for track_plan, track_estimate in zip(plan.tracks, estimate.tracks, strict=True):
        if track_estimate.track_id != track_plan.track_id:
            raise InputError("Task 2.2 Track estimate order differs from the plan")
        if track_estimate.maximum_new_calls != call_map[track_plan.track_id]:
            raise InputError("Task 2.2 Track call ceiling differs from Task 2.1")
        target = OfficialRateTarget(
            track_plan.effective_config.model_id,
            track_plan.effective_config.region,
            track_estimate.purchase_option,
        )
        card = cards.get(target)
        if card is None:
            raise InputError("Task 2.2 Track estimate lacks exact official rate provenance")
        if (track_estimate.model_id, track_estimate.region) != (
            track_plan.effective_config.model_id,
            track_plan.effective_config.region,
        ):
            raise InputError("Task 2.2 Track estimate model or region differs from the plan")
        rates = {
            item.modality: _parse_decimal(
                item.rate_per_1k_tokens,
                f"Task 2.2 {item.modality} official rate",
            )
            for item in card.rates
        }
        token_rows = {item.modality: item.tokens for item in track_estimate.maximum_tokens_by_modality}
        subtotal_rows = {
            item.modality: _parse_decimal(
                item.amount_usd,
                f"Task 2.2 {track_plan.track_id}/{item.modality} subtotal",
            )
            for item in track_estimate.subtotals_by_modality_usd
        }
        track_total = Decimal("0")
        for modality, tokens_per_call in expected_envelopes:
            expected_tokens = call_map[track_plan.track_id] * tokens_per_call
            if token_rows.get(modality) != expected_tokens:
                raise InputError("Task 2.2 maximum tokens do not match the finite call envelope")
            expected_subtotal = Decimal(expected_tokens) * rates[modality] / Decimal(1000)
            if subtotal_rows.get(modality) != expected_subtotal:
                raise InputError("Task 2.2 Decimal subtotal does not match tokens and official rate")
            expected_aggregate[modality] += expected_subtotal
            track_total += expected_subtotal
        if _parse_decimal(
            track_estimate.estimated_pre_tax_usd,
            f"Task 2.2 {track_plan.track_id} estimate",
        ) != track_total:
            raise InputError("Task 2.2 Track estimate total is inconsistent")

    aggregate_subtotals = {
        item.modality: _parse_decimal(
            item.amount_usd,
            f"Task 2.2 aggregate {item.modality} subtotal",
        )
        for item in estimate.subtotals_by_modality_usd
    }
    if aggregate_subtotals != expected_aggregate:
        raise InputError("Task 2.2 aggregate Decimal subtotals are inconsistent")
    expected_total = sum(expected_aggregate.values(), start=Decimal("0"))
    if _parse_decimal(estimate.estimated_pre_tax_usd, "Task 2.2 estimate") != expected_total:
        raise InputError("Task 2.2 estimated pre-tax total is inconsistent")


def _validate_bindings(
    config: BookProductionConfig,
    plan: FrozenBatchPlan,
    local_preflight: LocalPreflightResult,
    bounded_preflight: BoundedPreflightEstimateResult,
) -> _AuthorizationBindings:
    if not isinstance(config, BookProductionConfig):
        raise InputError("Authorization requires BookProductionConfig")
    if not isinstance(plan, FrozenBatchPlan):
        raise InputError("Authorization requires FrozenBatchPlan")
    if not isinstance(local_preflight, LocalPreflightResult):
        raise InputError("Authorization requires Task 2.1 LocalPreflightResult")
    if not isinstance(bounded_preflight, BoundedPreflightEstimateResult):
        raise InputError("Authorization requires Task 2.2 BoundedPreflightEstimateResult")

    plan_codec = StrictRecordCodec(FrozenBatchPlan)
    plan_codec.dump_bytes(plan)
    plan_sha256 = plan_codec.sha256(plan)
    local_sha256 = _verify_sealed(local_preflight, "Task 2.1 local preflight")
    estimate_sha256 = _verify_sealed(bounded_preflight.estimate, "Task 2.2 estimate")
    preflight_sha256 = _verify_sealed(bounded_preflight, "Task 2.2 bounded preflight")

    if config.book_id != plan.book_id:
        raise InputError("Production configuration book_id differs from the plan")
    if len(plan.tracks) > config.max_tracks_per_plan:
        raise InputError("Plan exceeds the current maximum Tracks per authorization")
    if not local_preflight.passed or local_preflight.blocking_categories:
        raise InputError("Task 2.1 local preflight did not pass")
    if not local_preflight.targeted_checks.passed:
        raise InputError("Targeted checks did not pass with external access disabled")
    if not (
        local_preflight.targeted_checks.aws_access_disabled
        and local_preflight.targeted_checks.model_access_disabled
    ):
        raise InputError("Targeted checks lack AWS/model denial evidence")
    if not bounded_preflight.passed or bounded_preflight.blocking_categories:
        raise InputError("Task 2.2 bounded preflight did not pass")
    if any(not identity.resolved for identity in bounded_preflight.identity_evidence):
        raise InputError("Task 2.2 identity evidence contains an unresolved profile")

    if local_preflight.plan_sha256 != plan_sha256:
        raise InputError("Task 2.1 local preflight is not bound to the exact plan")
    if local_preflight.config_sha256 != plan.config_sha256:
        raise InputError("Task 2.1 configuration digest differs from the plan")
    if bounded_preflight.plan_sha256 != plan_sha256:
        raise InputError("Task 2.2 bounded preflight is not bound to the exact plan")
    if bounded_preflight.local_preflight_sha256 != local_sha256:
        raise InputError("Task 2.2 bounded preflight is not bound to Task 2.1")

    transaction_ids = tuple(track.transaction_id for track in plan.tracks)
    track_ids = tuple(track.track_id for track in plan.tracks)
    command_sha256s = tuple(track.command_sha256 for track in plan.tracks)
    call_rows = local_preflight.maximum_new_calls_by_track
    if tuple(track_id for track_id, _calls in call_rows) != track_ids:
        raise InputError("Task 2.1 call ceilings do not match exact ordered plan scope")
    if tuple(item.track_id for item in local_preflight.track_reuse) != track_ids:
        raise InputError("Task 2.1 reuse assessments do not match exact ordered plan scope")
    if tuple(item.track_id for item in local_preflight.destinations) != track_ids:
        raise InputError("Task 2.1 destinations do not match exact ordered plan scope")
    if local_preflight.maximum_new_calls_total != sum(calls for _track_id, calls in call_rows):
        raise InputError("Task 2.1 total call ceiling is inconsistent")
    for track, (track_id, calls) in zip(plan.tracks, call_rows, strict=True):
        if track_id != track.track_id or calls > track.maximum_new_calls:
            raise InputError("Task 2.1 call ceiling exceeds the frozen Track bound")

    estimate = bounded_preflight.estimate
    if estimate.maximum_new_calls_by_track != call_rows:
        raise InputError("Task 2.2 call ceilings differ from Task 2.1 exact cache misses")
    if estimate.maximum_new_calls_total != local_preflight.maximum_new_calls_total:
        raise InputError("Task 2.2 total call ceiling differs from Task 2.1")
    if tuple(identity.profile_label for identity in bounded_preflight.identity_evidence) != _expected_profile_labels(plan):
        raise InputError("Task 2.2 identity profiles do not match the exact plan scope")
    _validate_decimal_estimate(config, plan, local_preflight, bounded_preflight)

    checked_at = _parse_utc(
        bounded_preflight.checked_at_utc,
        "Task 2.2 checked_at_utc",
    )
    deadline = checked_at + timedelta(hours=config.estimate.preflight_max_age_hours)
    return _AuthorizationBindings(
        plan_sha256=plan_sha256,
        local_preflight_sha256=local_sha256,
        preflight_sha256=preflight_sha256,
        estimate_sha256=estimate_sha256,
        official_rate_provenance_sha256=canonical_sha256(
            bounded_preflight.official_rate_cards
        ),
        transaction_ids=transaction_ids,
        track_ids=track_ids,
        command_sha256s=command_sha256s,
        call_rows=call_rows,
        maximum_new_calls_total=local_preflight.maximum_new_calls_total,
        estimated_pre_tax_usd=estimate.estimated_pre_tax_usd,
        preflight_checked_at=checked_at,
        preflight_deadline=deadline,
    )


def _transaction_store(
    workspace_root: Path,
    config: BookProductionConfig,
) -> TransactionStore:
    root = workspace_root.expanduser().resolve()
    book_root = resolve_inside(
        root,
        (PurePosixPath(config.build_root) / config.book_id).as_posix(),
    )
    return TransactionStore(book_root, config.book_id)


def _require_authorization_required_state(
    workspace_root: Path,
    config: BookProductionConfig,
    plan: FrozenBatchPlan,
    preflight_sha256: str,
) -> None:
    """Read lifecycle truth from independent ledgers, never caller booleans."""

    store = _transaction_store(workspace_root, config)
    for track in plan.tracks:
        try:
            snapshot = store.inspect_transaction(track.track_id, track.transaction_id)
        except InputError as exc:
            raise InputError(
                f"Transaction truth is missing or corrupt for {track.track_id!r}"
            ) from exc
        spec = TransactionSpec.from_plan(plan, track)
        if not snapshot.metadata.matches(spec):
            raise InputError(f"Transaction identity differs from plan for {track.track_id!r}")
        if snapshot.state is TransactionState.AUTHORIZATION_REQUIRED:
            if snapshot.payloads[-1].details.get("preflight_sha256") != preflight_sha256:
                raise InputError(
                    f"Transaction preflight binding is stale for {track.track_id!r}"
                )
            continue
        if snapshot.state in {
            TransactionState.BLOCKED,
            TransactionState.CHARGE_UNCERTAIN,
        }:
            raise InputError(
                "Stopped batch or uncertain transaction requires fresh preflight and authorization"
            )
        if snapshot.state in {
            TransactionState.RUNNING,
            TransactionState.RENDERED,
            TransactionState.VALIDATED,
            TransactionState.DELIVERED,
        }:
            raise InputError("Paid authorization scope has already been consumed or started")
        raise InputError(
            f"Transaction {track.track_id!r} is not ready for paid authorization"
        )


def _display_from_bindings(
    bindings: _AuthorizationBindings,
    *,
    authorization_id: str,
    operator_approved_max_estimated_pre_tax_usd: str,
    issued_at_utc: str,
    expires_at_utc: str,
    confirmation_challenge: str,
) -> AuthorizationDisplay:
    _require_identifier(authorization_id, "authorization_id")
    _require_sha256(confirmation_challenge, "authorization confirmation challenge")
    estimate = _parse_decimal(bindings.estimated_pre_tax_usd, "preflight estimate")
    approved = _parse_decimal(
        operator_approved_max_estimated_pre_tax_usd,
        "operator-approved maximum estimated pre-tax USD",
    )
    if approved < estimate:
        raise InputError("operator-approved maximum is lower than the preflight estimate")
    issued = _parse_utc(issued_at_utc, "authorization issued_at_utc")
    expires = _parse_utc(expires_at_utc, "authorization expires_at_utc")
    if issued < bindings.preflight_checked_at:
        raise InputError("authorization issue time precedes the bound preflight")
    if issued > bindings.preflight_deadline:
        raise InputError("bound preflight is stale at authorization issue time")
    if expires <= issued:
        raise InputError("authorization expiration must be after issue time")
    if expires > bindings.preflight_deadline:
        raise InputError("authorization expiration exceeds the bound preflight freshness window")

    return seal_record(
        AuthorizationDisplay(
            schema_version=RECORD_SCHEMA_VERSION,
            authorization_id=authorization_id,
            plan_sha256=bindings.plan_sha256,
            preflight_sha256=bindings.preflight_sha256,
            local_preflight_sha256=bindings.local_preflight_sha256,
            estimate_sha256=bindings.estimate_sha256,
            official_rate_provenance_sha256=bindings.official_rate_provenance_sha256,
            exact_transaction_ids=bindings.transaction_ids,
            exact_track_ids=bindings.track_ids,
            exact_command_sha256s=bindings.command_sha256s,
            maximum_new_calls_by_track=bindings.call_rows,
            maximum_new_calls_total=bindings.maximum_new_calls_total,
            estimated_pre_tax_usd=bindings.estimated_pre_tax_usd,
            operator_approved_max_estimated_pre_tax_usd=(
                operator_approved_max_estimated_pre_tax_usd
            ),
            issued_at_utc=issued_at_utc,
            expires_at_utc=expires_at_utc,
            one_shot=True,
            confirmation_challenge=confirmation_challenge,
            confirmation_prompt=AUTHORIZATION_CONFIRMATION_PROMPT,
            canonical_sha256="",
        )
    )


def _display_from_authorization(
    bindings: _AuthorizationBindings,
    authorization: PaidAuthorization,
) -> AuthorizationDisplay:
    return _display_from_bindings(
        bindings,
        authorization_id=authorization.authorization_id,
        operator_approved_max_estimated_pre_tax_usd=(
            authorization.operator_approved_max_estimated_pre_tax_usd
        ),
        issued_at_utc=authorization.issued_at_utc,
        expires_at_utc=authorization.expires_at_utc,
        confirmation_challenge=authorization.confirmation_challenge,
    )


def create_paid_authorization(
    config: BookProductionConfig,
    plan: FrozenBatchPlan,
    local_preflight: LocalPreflightResult,
    bounded_preflight: BoundedPreflightEstimateResult,
    *,
    workspace_root: Path,
    authorization_id: str,
    operator_approved_max_estimated_pre_tax_usd: str,
    expires_at_utc: str,
    confirmation_provider: Callable[[AuthorizationDisplay], object],
    clock: Clock = _system_clock,
) -> PaidAuthorization:
    """Create one authorization after a fresh exact injected confirmation.

    A boolean, free-form string, specification state, completed task, old challenge,
    or generic approval is intentionally not an accepted response type.
    """

    if not callable(confirmation_provider):
        raise InputError("confirmation_provider must display and confirm the exact scope")
    bindings = _validate_bindings(config, plan, local_preflight, bounded_preflight)
    _require_authorization_required_state(
        workspace_root,
        config,
        plan,
        bindings.preflight_sha256,
    )
    issued = _clock_now(clock, "authorization issue")
    issued_at_utc = _format_utc(issued)
    challenge = secrets.token_hex(32)
    display = _display_from_bindings(
        bindings,
        authorization_id=authorization_id,
        operator_approved_max_estimated_pre_tax_usd=(
            operator_approved_max_estimated_pre_tax_usd
        ),
        issued_at_utc=issued_at_utc,
        expires_at_utc=expires_at_utc,
        confirmation_challenge=challenge,
    )
    try:
        confirmation = confirmation_provider(display)
    except Exception as exc:
        raise InputError("Exact paid authorization confirmation was not obtained") from exc
    if not isinstance(confirmation, ExactAuthorizationConfirmation):
        raise InputError(
            "Confirmation must be ExactAuthorizationConfirmation; generic approval is insufficient"
        )
    if confirmation.display_sha256 != display.canonical_sha256:
        raise InputError("Confirmation does not bind the exact displayed authorization scope")
    if confirmation.challenge != challenge:
        raise InputError("Confirmation challenge is stale or belongs to another invocation")
    if confirmation.decision is not AuthorizationDecision.AUTHORIZE_EXACT_SCOPE:
        raise InputError("Exact paid authorization was declined")

    confirmed = _clock_now(clock, "authorization confirmation")
    expires = _parse_utc(expires_at_utc, "authorization expires_at_utc")
    if confirmed < issued or confirmed >= expires:
        raise InputError("Exact confirmation must occur within the displayed authorization window")
    if confirmed > bindings.preflight_deadline:
        raise InputError("Bound preflight became stale before exact confirmation")
    confirmed_at_utc = _format_utc(confirmed)
    confirmation_sha256 = authorization_confirmation_sha256(
        display_sha256=display.canonical_sha256,
        challenge=challenge,
        decision=confirmation.decision,
        confirmed_at_utc=confirmed_at_utc,
    )

    authorization = seal_record(
        PaidAuthorization(
            schema_version=RECORD_SCHEMA_VERSION,
            authorization_id=authorization_id,
            plan_sha256=bindings.plan_sha256,
            preflight_sha256=bindings.preflight_sha256,
            local_preflight_sha256=bindings.local_preflight_sha256,
            estimate_sha256=bindings.estimate_sha256,
            official_rate_provenance_sha256=bindings.official_rate_provenance_sha256,
            exact_transaction_ids=bindings.transaction_ids,
            exact_track_ids=bindings.track_ids,
            exact_command_sha256s=bindings.command_sha256s,
            maximum_new_calls_by_track=dict(bindings.call_rows),
            maximum_new_calls_total=bindings.maximum_new_calls_total,
            estimated_pre_tax_usd=bindings.estimated_pre_tax_usd,
            operator_approved_max_estimated_pre_tax_usd=(
                operator_approved_max_estimated_pre_tax_usd
            ),
            issued_at_utc=issued_at_utc,
            expires_at_utc=expires_at_utc,
            one_shot=True,
            confirmation_challenge=challenge,
            confirmation_display_sha256=display.canonical_sha256,
            confirmation_decision=confirmation.decision,
            confirmed_at_utc=confirmed_at_utc,
            confirmation_sha256=confirmation_sha256,
            canonical_sha256="",
        )
    )
    StrictRecordCodec(PaidAuthorization).dump_bytes(authorization)
    return authorization


def load_paid_authorization(path: Path) -> PaidAuthorization:
    """Load one strict canonical authorization artifact without mutating it."""

    return StrictRecordCodec(PaidAuthorization).load(path.expanduser().resolve())


def write_paid_authorization(path: Path, authorization: PaidAuthorization) -> Path:
    """Publish an immutable authorization file, idempotently and without overwrite."""

    if not isinstance(authorization, PaidAuthorization):
        raise InputError("Authorization artifact must be PaidAuthorization")
    codec = StrictRecordCodec(PaidAuthorization)
    content = codec.dump_bytes(authorization)
    absolute = Path(os.path.abspath(os.fspath(path.expanduser())))
    if not absolute.name or absolute.name in {".", ".."}:
        raise InputError("Authorization artifact path is unsafe")

    def verify_existing() -> Path:
        if absolute.is_symlink() or not absolute.is_file():
            raise InputError("Authorization artifact collision is not a regular file")
        existing = read_bytes_nofollow(absolute)
        if existing != content:
            raise InputError("Authorization artifact collision has different canonical bytes")
        codec.loads(existing, label=str(absolute))
        return absolute

    if os.path.lexists(absolute):
        return verify_existing()

    durable_mkdir(absolute.parent)
    temporary = absolute.parent / f".{absolute.name}.{secrets.token_hex(12)}.staging"
    atomic_write_bytes(temporary, content)
    try:
        try:
            os.link(temporary, absolute, follow_symlinks=False)
            fsync_directory(absolute.parent)
        except FileExistsError:
            return verify_existing()
    finally:
        temporary.unlink(missing_ok=True)
        fsync_directory(absolute.parent)
    return absolute


def create_paid_authorization_file(
    path: Path,
    config: BookProductionConfig,
    plan: FrozenBatchPlan,
    local_preflight: LocalPreflightResult,
    bounded_preflight: BoundedPreflightEstimateResult,
    *,
    workspace_root: Path,
    authorization_id: str,
    operator_approved_max_estimated_pre_tax_usd: str,
    expires_at_utc: str,
    confirmation_provider: Callable[[AuthorizationDisplay], object],
    clock: Clock = _system_clock,
) -> PaidAuthorization:
    """Confirm, create, then exclusively persist one local canonical artifact."""

    absolute = Path(os.path.abspath(os.fspath(path.expanduser())))
    if os.path.lexists(absolute):
        raise InputError("Authorization ID already has an artifact; refusing a second confirmation")
    authorization = create_paid_authorization(
        config,
        plan,
        local_preflight,
        bounded_preflight,
        workspace_root=workspace_root,
        authorization_id=authorization_id,
        operator_approved_max_estimated_pre_tax_usd=(
            operator_approved_max_estimated_pre_tax_usd
        ),
        expires_at_utc=expires_at_utc,
        confirmation_provider=confirmation_provider,
        clock=clock,
    )
    from .util import resolve_inside_approved_root, workspace_relative

    root = workspace_root.expanduser().resolve()
    approved_root = resolve_inside(
        root,
        (
            PurePosixPath(config.build_root)
            / config.book_id
            / "plans"
            / plan.plan_id
            / "authorizations"
        ).as_posix(),
    )
    checked_absolute = resolve_inside_approved_root(
        root,
        approved_root,
        workspace_relative(root, absolute),
    )
    write_paid_authorization(checked_absolute, authorization)
    return authorization


def build_authorization_start_request(
    authorization: PaidAuthorization,
) -> AuthorizationStartRequest:
    """Build the exact ephemeral first-start scope; this performs no consumption."""

    if not isinstance(authorization, PaidAuthorization):
        raise InputError("Start request requires PaidAuthorization")
    codec = StrictRecordCodec(PaidAuthorization)
    authorization_sha256 = codec.sha256(authorization)
    return AuthorizationStartRequest(
        authorization_sha256=authorization_sha256,
        plan_sha256=authorization.plan_sha256,
        preflight_sha256=authorization.preflight_sha256,
        exact_transaction_ids=authorization.exact_transaction_ids,
        exact_track_ids=authorization.exact_track_ids,
        exact_command_sha256s=authorization.exact_command_sha256s,
        maximum_new_calls_by_track=tuple(
            (track_id, authorization.maximum_new_calls_by_track[track_id])
            for track_id in authorization.exact_track_ids
        ),
        maximum_new_calls_total=authorization.maximum_new_calls_total,
    )


def validate_paid_authorization_start(
    authorization: PaidAuthorization,
    config: BookProductionConfig,
    plan: FrozenBatchPlan,
    local_preflight: LocalPreflightResult,
    bounded_preflight: BoundedPreflightEstimateResult,
    request: AuthorizationStartRequest,
    *,
    workspace_root: Path,
    clock: Clock = _system_clock,
) -> PaidAuthorization:
    """Validate one exact first start without consuming or launching anything."""

    if not isinstance(authorization, PaidAuthorization):
        raise InputError("Authorization validation requires PaidAuthorization")
    if not isinstance(request, AuthorizationStartRequest):
        raise InputError("Authorization validation requires AuthorizationStartRequest")
    codec = StrictRecordCodec(PaidAuthorization)
    codec.dump_bytes(authorization)
    bindings = _validate_bindings(config, plan, local_preflight, bounded_preflight)

    expected = {
        "plan_sha256": bindings.plan_sha256,
        "preflight_sha256": bindings.preflight_sha256,
        "local_preflight_sha256": bindings.local_preflight_sha256,
        "estimate_sha256": bindings.estimate_sha256,
        "official_rate_provenance_sha256": bindings.official_rate_provenance_sha256,
        "exact_transaction_ids": bindings.transaction_ids,
        "exact_track_ids": bindings.track_ids,
        "exact_command_sha256s": bindings.command_sha256s,
        "maximum_new_calls_by_track": dict(bindings.call_rows),
        "maximum_new_calls_total": bindings.maximum_new_calls_total,
        "estimated_pre_tax_usd": bindings.estimated_pre_tax_usd,
    }
    for field_name, value in expected.items():
        actual = getattr(authorization, field_name)
        if isinstance(actual, Mapping):
            actual = dict(actual)
        if actual != value:
            raise InputError(f"Paid authorization {field_name} is stale or mismatched")

    display = _display_from_authorization(bindings, authorization)
    if display.canonical_sha256 != authorization.confirmation_display_sha256:
        raise InputError("Paid authorization display/confirmation chain is invalid")
    expected_confirmation_sha256 = authorization_confirmation_sha256(
        display_sha256=display.canonical_sha256,
        challenge=authorization.confirmation_challenge,
        decision=authorization.confirmation_decision,
        confirmed_at_utc=authorization.confirmed_at_utc,
    )
    if authorization.confirmation_sha256 != expected_confirmation_sha256:
        raise InputError("Paid authorization confirmation evidence is invalid")

    now = _clock_now(clock, "authorization validation")
    issued = _parse_utc(authorization.issued_at_utc, "authorization issued_at_utc")
    expires = _parse_utc(authorization.expires_at_utc, "authorization expires_at_utc")
    if now < issued:
        raise InputError("Paid authorization is not yet valid")
    if now >= expires:
        raise InputError("Paid authorization is expired")
    if now > bindings.preflight_deadline:
        raise InputError("Paid authorization is bound to stale preflight evidence")

    _require_authorization_required_state(
        workspace_root,
        config,
        plan,
        bindings.preflight_sha256,
    )
    authorization_sha256 = codec.sha256(authorization)
    exact_request = {
        "authorization_sha256": authorization_sha256,
        "plan_sha256": authorization.plan_sha256,
        "preflight_sha256": authorization.preflight_sha256,
        "exact_transaction_ids": authorization.exact_transaction_ids,
        "exact_track_ids": authorization.exact_track_ids,
        "exact_command_sha256s": authorization.exact_command_sha256s,
        "maximum_new_calls_by_track": tuple(
            (track_id, authorization.maximum_new_calls_by_track[track_id])
            for track_id in authorization.exact_track_ids
        ),
        "maximum_new_calls_total": authorization.maximum_new_calls_total,
    }
    for field_name, value in exact_request.items():
        if getattr(request, field_name) != value:
            raise InputError(f"Authorization start {field_name} is altered, incomplete, or unlisted")
    return authorization


__all__ = [
    "AUTHORIZATION_CONFIRMATION_PROMPT",
    "AuthorizationDecision",
    "AuthorizationDisplay",
    "AuthorizationStartRequest",
    "ExactAuthorizationConfirmation",
    "build_authorization_start_request",
    "create_paid_authorization",
    "create_paid_authorization_file",
    "load_paid_authorization",
    "validate_paid_authorization_start",
    "write_paid_authorization",
]
