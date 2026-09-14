"""Sanitized, evidence-bound Track and batch reporting.

Reports are deterministic views over immutable local evidence and independent
transaction ledgers.  This module has no child-process, AWS, network, pricing, or
model integration.  A successful repeat reuses the original Track report timestamp
and bytes; a batch report changes only when its independently reconstructed inputs
change.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Sequence

from .errors import InputError
from .production_accounting import ExactAccountingResult
from .production_evidence import (
    EvidenceArtifactKind,
    assert_evidence_bytes_safe,
    assert_typed_evidence_safe,
    forbidden_field_values,
    resolve_private_runtime_path,
)
from .production_delivery import (
    DeliveryRecord,
    ProductionTrackScope,
    deliver_validated_track,
    load_production_track_scope,
    write_immutable_evidence,
)
from .production_models import (
    RECORD_SCHEMA_VERSION,
    BatchReport,
    BatchTrackReportEntry,
    DeliveryStatus,
    FrozenBatchPlan,
    PaidAuthorization,
    StrictRecordCodec,
    TrackReport,
    TransactionState,
    ValidationEvidence,
    ValidationStatus,
    canonical_sha256,
    seal_record,
)
from .production_preflight import (
    BoundedPreflightEstimateResult,
    DestinationAssessment,
    IsolationAssessment,
    LocalPreflightResult,
    OfficialRateCard,
    TrackCostEstimate,
    TrackReuseAssessment,
)
from .production_transactions import TransactionHealth
from .production_validation import load_passing_validation_evidence
from .util import (
    atomic_write_bytes,
    json_loads_strict,
    read_bytes_nofollow,
    sha256_bytes,
    utc_now,
    workspace_relative,
)

Clock = Callable[[], datetime]


@dataclass(frozen=True, slots=True)
class DeliveryAndReportResult:
    """Result of the complete nonbillable deliver operation."""

    delivery: DeliveryRecord
    track_report: TrackReport | None

    def __post_init__(self) -> None:
        if not isinstance(self.delivery, DeliveryRecord):
            raise InputError("deliver/report result requires DeliveryRecord")
        succeeded = self.delivery.status in {
            DeliveryStatus.PUBLISHED,
            DeliveryStatus.ALREADY_IDENTICAL,
        }
        if succeeded != isinstance(self.track_report, TrackReport):
            raise InputError("successful delivery requires one TrackReport")


def _timestamp(value: str | None, clock: Clock | None, label: str) -> str:
    if value is not None and clock is not None:
        raise InputError(f"Pass {label}_at_utc or clock, not both")
    if value is None and clock is None:
        value = utc_now()
    elif value is None:
        now = clock()
        if (
            not isinstance(now, datetime)
            or now.tzinfo is None
            or now.utcoffset() != UTC.utcoffset(now)
        ):
            raise InputError(f"{label} clock must return an aware UTC datetime")
        value = now.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    assert value is not None
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except (AttributeError, ValueError) as exc:
        raise InputError(f"{label}_at_utc must be a valid UTC timestamp") from exc
    if not value.endswith("Z") or parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise InputError(f"{label}_at_utc must be a valid UTC timestamp ending in Z")
    return value


def _verify_sealed(value: Any, label: str) -> str:
    assert_typed_evidence_safe(value)
    digest = getattr(value, "canonical_sha256", None)
    if not isinstance(digest, str) or len(digest) != 64:
        raise InputError(f"{label} lacks a sealed canonical digest")
    expected = canonical_sha256(value, omit_fields=("canonical_sha256",))
    if digest != expected:
        raise InputError(f"{label} canonical digest does not match its content")
    return digest


def _exact_member(values: Sequence[Any], predicate: Callable[[Any], bool], label: str) -> Any:
    matches = tuple(value for value in values if predicate(value))
    if len(matches) != 1:
        raise InputError(f"Expected exactly one {label}")
    return matches[0]


def _load_transaction_evidence(
    scope: ProductionTrackScope,
) -> tuple[ValidationEvidence, DeliveryRecord]:
    delivery = StrictRecordCodec(DeliveryRecord).load(
        scope.transaction_root / "delivery" / "delivery.json"
    )
    validation, _validation_path = load_passing_validation_evidence(
        scope.transaction_root,
        transaction_id=scope.track.transaction_id,
        track_id=scope.track.track_id,
        plan_sha256=StrictRecordCodec(FrozenBatchPlan).sha256(scope.plan),
        validation_sha256=delivery.validation_sha256,
    )
    return validation, delivery


def _private_runtime_values(
    scope: ProductionTrackScope,
    validation: ValidationEvidence,
) -> tuple[str, ...]:
    """Read private fields only in memory for non-echo report comparisons."""

    manifest_value = workspace_relative(
        scope.workspace_root,
        scope.transaction_root / "runtime" / "manifest.json",
    )
    manifest_path = resolve_private_runtime_path(
        scope.workspace_root,
        scope.transaction_root,
        manifest_value,
        require_exists=True,
        expected_kind="file",
    )
    raw = read_bytes_nofollow(manifest_path)
    if sha256_bytes(raw) != validation.manifest_sha256:
        raise InputError("Runtime manifest differs from report validation evidence")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError("Runtime manifest is not valid UTF-8") from exc
    value = json_loads_strict(text, str(manifest_path))
    if not isinstance(value, dict):
        raise InputError("Runtime manifest must be a JSON object")
    return forbidden_field_values(value)


def _assert_report_markdown_safe(
    scope: ProductionTrackScope,
    report_path: Path,
    content: bytes,
    *,
    validation: ValidationEvidence | None = None,
) -> None:
    sensitive_values = (
        _private_runtime_values(scope, validation)
        if validation is not None
        else ()
    )
    assert_evidence_bytes_safe(
        EvidenceArtifactKind.REPORT,
        content,
        artifact_path=workspace_relative(scope.workspace_root, report_path),
        sensitive_values=sensitive_values,
    )


def _validate_track_report_inputs(
    scope: ProductionTrackScope,
    local_preflight: LocalPreflightResult,
    bounded_preflight: BoundedPreflightEstimateResult,
    authorization: PaidAuthorization,
    attempt: Any,
    validation: ValidationEvidence,
    accounting: ExactAccountingResult,
    delivery: DeliveryRecord,
    isolation: IsolationAssessment,
    broader_suite_status: ValidationStatus,
) -> tuple[
    TrackReuseAssessment,
    DestinationAssessment,
    TrackCostEstimate,
    OfficialRateCard,
]:
    from .production_models import AttemptResult  # avoid widening public module imports

    if not isinstance(local_preflight, LocalPreflightResult):
        raise InputError("Track report requires LocalPreflightResult")
    if not isinstance(bounded_preflight, BoundedPreflightEstimateResult):
        raise InputError("Track report requires BoundedPreflightEstimateResult")
    if not isinstance(authorization, PaidAuthorization):
        raise InputError("Track report requires PaidAuthorization")
    if not isinstance(attempt, AttemptResult):
        raise InputError("Track report requires AttemptResult")
    if not isinstance(accounting, ExactAccountingResult):
        raise InputError("Track report requires ExactAccountingResult")
    if not isinstance(isolation, IsolationAssessment):
        raise InputError("Track report requires IsolationAssessment")
    if not isinstance(broader_suite_status, ValidationStatus):
        raise InputError("broader suite status must be a ValidationStatus")

    plan_codec = StrictRecordCodec(FrozenBatchPlan)
    authorization_codec = StrictRecordCodec(PaidAuthorization)
    attempt_codec = StrictRecordCodec(AttemptResult)
    validation_codec = StrictRecordCodec(ValidationEvidence)
    delivery_codec = StrictRecordCodec(DeliveryRecord)
    plan_sha256 = plan_codec.sha256(scope.plan)
    authorization_sha256 = authorization_codec.sha256(authorization)
    attempt_sha256 = attempt_codec.sha256(attempt)
    validation_sha256 = validation_codec.sha256(validation)
    delivery_codec.dump_bytes(delivery)

    local_sha256 = _verify_sealed(local_preflight, "local preflight")
    bounded_sha256 = _verify_sealed(bounded_preflight, "bounded preflight")
    _verify_sealed(bounded_preflight.estimate, "bounded cost estimate")
    _verify_sealed(isolation, "isolation assessment")

    if not local_preflight.passed or local_preflight.blocking_categories:
        raise InputError("Track report requires passing local preflight evidence")
    if not bounded_preflight.passed or bounded_preflight.blocking_categories:
        raise InputError("Track report requires passing bounded preflight evidence")
    if local_preflight.plan_sha256 != plan_sha256 or local_preflight.config_sha256 != scope.plan.config_sha256:
        raise InputError("Local preflight differs from the exact plan/configuration")
    if (
        bounded_preflight.plan_sha256 != plan_sha256
        or bounded_preflight.local_preflight_sha256 != local_sha256
    ):
        raise InputError("Bounded preflight differs from the exact local scope")
    if (
        authorization.plan_sha256 != plan_sha256
        or authorization.local_preflight_sha256 != local_sha256
        or authorization.preflight_sha256 != bounded_sha256
    ):
        raise InputError("Paid authorization differs from the exact report scope")

    scope_index = tuple(authorization.exact_transaction_ids).index(
        scope.track.transaction_id
    ) if scope.track.transaction_id in authorization.exact_transaction_ids else -1
    if (
        scope_index < 0
        or authorization.exact_track_ids[scope_index] != scope.track.track_id
        or authorization.exact_command_sha256s[scope_index] != scope.track.command_sha256
    ):
        raise InputError("Paid authorization does not contain this exact Track scope")
    if (
        attempt.transaction_id != scope.track.transaction_id
        or attempt.authorization_sha256 != authorization_sha256
        or attempt.command_sha256 != scope.track.command_sha256
        or attempt.native_return_code != 0
    ):
        raise InputError("Attempt result is not the native-zero attempt for this Track")
    if (
        validation.transaction_id != scope.track.transaction_id
        or validation.track_id != scope.track.track_id
        or validation.plan_sha256 != plan_sha256
        or validation.attempt_sha256 != attempt_sha256
        or validation.status is not ValidationStatus.PASSED
        or not validation.delivery_gate_passed
        or any(check.status is not ValidationStatus.PASSED for check in validation.checks)
    ):
        raise InputError("Validation evidence does not pass the exact Delivery_Gate")
    if (
        delivery.transaction_id != scope.track.transaction_id
        or delivery.track_id != scope.track.track_id
        or delivery.validation_sha256 != validation_sha256
        or delivery.status
        not in {DeliveryStatus.PUBLISHED, DeliveryStatus.ALREADY_IDENTICAL}
        or not delivery.complete_byte_sequence_verified
    ):
        raise InputError("Delivery evidence is not a successful verified Track delivery")

    snapshot = scope.store.inspect_transaction(
        scope.track.track_id,
        scope.track.transaction_id,
    )
    if snapshot.state is not TransactionState.DELIVERED:
        raise InputError("Track report requires independently reconstructed delivered state")

    reuse = _exact_member(
        local_preflight.track_reuse,
        lambda item: item.track_id == scope.track.track_id,
        "Track reuse assessment",
    )
    destination = _exact_member(
        local_preflight.destinations,
        lambda item: item.track_id == scope.track.track_id,
        "Track destination assessment",
    )
    estimate = _exact_member(
        bounded_preflight.estimate.tracks,
        lambda item: item.track_id == scope.track.track_id,
        "Track cost estimate",
    )
    rate_card = _exact_member(
        bounded_preflight.official_rate_cards,
        lambda item: item.target == accounting.official_rate_card.target,
        "official rate card",
    )
    if rate_card != accounting.official_rate_card:
        raise InputError("Exact accounting uses different official rate provenance")
    if accounting.cost_estimate_usd != estimate.estimated_pre_tax_usd:
        raise InputError("Exact accounting Cost_Estimate differs from the Track estimate")
    if Decimal(accounting.operator_approved_max_estimated_pre_tax_usd) != Decimal(
        authorization.operator_approved_max_estimated_pre_tax_usd
    ):
        raise InputError("Exact accounting approved maximum differs from authorization")
    if not isolation.passed:
        raise InputError("Track report requires passing postflight isolation")
    if not (
        local_preflight.targeted_checks.passed
        and local_preflight.targeted_checks.aws_access_disabled
        and local_preflight.targeted_checks.model_access_disabled
    ):
        raise InputError("Track report requires passing nonbillable Targeted_Checks")
    return reuse, destination, estimate, rate_card


def _build_track_record(
    scope: ProductionTrackScope,
    *,
    generated_at_utc: str,
    bounded_preflight: BoundedPreflightEstimateResult,
    authorization: PaidAuthorization,
    attempt: Any,
    validation: ValidationEvidence,
    accounting: ExactAccountingResult,
    delivery: DeliveryRecord,
    isolation: IsolationAssessment,
    targeted_checks_sha256: str,
    broader_suite_status: ValidationStatus,
    supplemental_listening_sha256: str | None,
) -> TrackReport:
    from .production_models import AttemptResult

    return seal_record(
        TrackReport(
            schema_version=RECORD_SCHEMA_VERSION,
            transaction_id=scope.track.transaction_id,
            track_id=scope.track.track_id,
            generated_at_utc=generated_at_utc,
            state=TransactionState.DELIVERED,
            source_sha256=scope.track.source.raw_sha256,
            config_sha256=scope.plan.config_sha256,
            plan_sha256=StrictRecordCodec(FrozenBatchPlan).sha256(scope.plan),
            preflight_sha256=bounded_preflight.canonical_sha256,
            authorization_sha256=StrictRecordCodec(PaidAuthorization).sha256(authorization),
            attempt_sha256=StrictRecordCodec(AttemptResult).sha256(attempt),
            validation_sha256=StrictRecordCodec(ValidationEvidence).sha256(validation),
            native_return_code=attempt.native_return_code,
            active_artifact_totals=accounting.journal_aggregation.active_artifact_totals,
            current_execution_totals=accounting.journal_aggregation.current_execution_totals,
            estimated_pre_tax_usd=accounting.cost_estimate_usd,
            active_artifact_cost_usd=(
                accounting.active_artifact_cost.computed_pre_tax_service_cost_usd
            ),
            current_execution_cost_usd=(
                accounting.current_execution_cost.computed_pre_tax_service_cost_usd
            ),
            billing_status=accounting.billing_confirmation.status,
            billing_amount_usd=accounting.billing_confirmation.amount_usd,
            billing_confirmed_at_utc=accounting.billing_confirmation.confirmed_at_utc,
            delivery_status=delivery.status,
            isolation_status=(
                ValidationStatus.PASSED if isolation.passed else ValidationStatus.BLOCKED
            ),
            targeted_checks_sha256=targeted_checks_sha256,
            broader_suite_status=broader_suite_status,
            supplemental_listening_sha256=supplemental_listening_sha256,
            canonical_sha256="",
        )
    )


def _cell(value: object) -> str:
    if value is None:
        return "not-applicable"
    if isinstance(value, Enum):
        value = value.value
    text = str(value)
    return (
        text.replace("\\", "\\\\")
        .replace("|", "\\|")
        .replace("\r", " ")
        .replace("\n", " ")
    )


def _usage_value(totals: Any, modality: str) -> int:
    return int(getattr(totals, modality))


def _render_track_markdown(
    report: TrackReport,
    scope: ProductionTrackScope,
    local_preflight: LocalPreflightResult,
    bounded_preflight: BoundedPreflightEstimateResult,
    authorization: PaidAuthorization,
    attempt: Any,
    validation: ValidationEvidence,
    accounting: ExactAccountingResult,
    delivery: DeliveryRecord,
    isolation: IsolationAssessment,
    reuse: TrackReuseAssessment,
    preflight_destination: DestinationAssessment,
    estimate: TrackCostEstimate,
    rate_card: OfficialRateCard,
) -> bytes:
    track = scope.track
    lines = [
        f"# Track Report: {_cell(track.track_id)}",
        "",
        "> Sanitized evidence only. Prose, transcript bodies, raw event payloads, environment data, and identity responses are excluded.",
        "",
        "## State",
        "",
        f"- Transaction: `{_cell(track.transaction_id)}`",
        f"- Catalog sequence: `{track.sequence}`",
        f"- Derived ledger state: `{report.state.value}`",
        f"- Native child return code: `{report.native_return_code}`",
        f"- Generated at (UTC): `{report.generated_at_utc}`",
        f"- Nonbillable deliver/report operation: `true`",
        "",
        "## Evidence digests",
        "",
        "| Evidence | SHA-256 |",
        "|---|---|",
        f"| Source bytes | `{report.source_sha256}` |",
        f"| Production configuration | `{report.config_sha256}` |",
        f"| Frozen plan | `{report.plan_sha256}` |",
        f"| Local preflight | `{local_preflight.canonical_sha256}` |",
        f"| Bounded preflight | `{report.preflight_sha256}` |",
        f"| Paid authorization | `{report.authorization_sha256}` |",
        f"| Native attempt | `{report.attempt_sha256}` |",
        f"| Runtime manifest | `{validation.manifest_sha256}` |",
        f"| Validation evidence | `{report.validation_sha256}` |",
        f"| Delivery evidence | `{StrictRecordCodec(DeliveryRecord).sha256(delivery)}` |",
        f"| Track report canonical content | `{report.canonical_sha256}` |",
        "",
        "## Source and effective configuration",
        "",
        f"- Source path: `{_cell(track.source.source_path)}`",
        f"- Source kind: `{track.source.source_kind.value}`",
        f"- Source section: `{_cell(track.source.source_section)}`",
        f"- Normalized word count: `{track.source.normalized_word_count}`",
        f"- Spoken token count: `{track.source.spoken_token_count}`",
        f"- Segment count: `{track.source.segment_count}`",
        f"- Voice: `{_cell(track.effective_config.voice)}`",
        f"- Model: `{_cell(track.effective_config.model_id)}`",
        f"- Region: `{_cell(track.effective_config.region)}`",
        f"- Profile label: `{_cell(track.effective_config.profile_label)}`",
        f"- Fidelity policy: `{track.effective_config.fidelity_policy.value}`",
        f"- Normalization: `{_cell(track.effective_config.normalization)}`",
        f"- Audio: `{track.effective_config.audio_format.sample_rate_hz} Hz / {track.effective_config.audio_format.sample_size_bits}-bit / {track.effective_config.audio_format.channels} channel(s) / {track.effective_config.audio_format.encoding.value}`",
        "",
        "### Resolution provenance",
        "",
        "| Setting | Layer |",
        "|---|---|",
    ]
    lines.extend(
        f"| {_cell(name)} | {_cell(layer)} |"
        for name, layer in sorted(track.effective_config.resolution_provenance.items())
    )
    lines.extend(
        [
            "",
            "## Deterministic validation",
            "",
            f"- Delivery_Gate: `{'passed' if validation.delivery_gate_passed else 'blocked'}`",
            f"- Validation status: `{validation.status.value}`",
            "",
            "| Check | Status | Finding category | Count | Artifact SHA-256 |",
            "|---|---|---|---:|---|",
        ]
    )
    lines.extend(
        "| "
        + " | ".join(
            (
                _cell(check.check_id),
                _cell(check.status),
                _cell(check.finding_category),
                str(check.finding_count),
                f"`{_cell(check.artifact_sha256)}`",
            )
        )
        + " |"
        for check in validation.checks
    )
    lines.extend(
        [
            "",
            "## Reuse",
            "",
            f"- Prior artifact state: `{reuse.prior_state.value}`",
            f"- Reuse disposition: `{reuse.disposition.value}`",
            f"- Reused segments: `{len(reuse.reusable_segment_ids)}`",
            f"- Newly rendered segment ceiling: `{reuse.maximum_new_calls}`",
            f"- Reuse assessment digest: `{reuse.canonical_sha256}`",
            "",
            "## Usage",
            "",
            "| Modality | Active Artifact Totals | Current Execution Totals |",
            "|---|---:|---:|",
        ]
    )
    for modality in ("input_speech", "input_text", "output_speech", "output_text"):
        lines.append(
            f"| `{modality}` | {_usage_value(report.active_artifact_totals, modality)} | {_usage_value(report.current_execution_totals, modality)} |"
        )
    lines.extend(
        [
            "",
            "## Cost estimate and exact service cost",
            "",
            f"- Track Cost_Estimate (pre-tax USD): `{estimate.estimated_pre_tax_usd}`",
            f"- Active Artifact Computed_Pre_Tax_Service_Cost (USD): `{report.active_artifact_cost_usd}`",
            f"- Current Execution Computed_Pre_Tax_Service_Cost (USD): `{report.current_execution_cost_usd}`",
            f"- Operator-approved maximum estimated pre-tax USD: `{authorization.operator_approved_max_estimated_pre_tax_usd}`",
            f"- Budget exception status: `{accounting.budget_exception_status.value}`",
            f"- Accounting calculated at (UTC): `{accounting.calculated_at_utc}`",
            "",
            "### Exact modality calculations",
            "",
            "| Scope | Modality | Tokens | Rate / 1k | Formula | Unrounded USD |",
            "|---|---|---:|---:|---|---:|",
        ]
    )
    for cost_scope in (accounting.active_artifact_cost, accounting.current_execution_cost):
        for item in cost_scope.modality_lines:
            lines.append(
                "| "
                + " | ".join(
                    (
                        _cell(cost_scope.scope),
                        _cell(item.modality),
                        str(item.tokens),
                        _cell(item.rate_per_1k_tokens),
                        f"`{_cell(item.formula)}`",
                        _cell(item.unrounded_subtotal_usd),
                    )
                )
                + " |"
            )
    lines.extend(
        [
            "",
            "### Official rate provenance",
            "",
            f"- Model / region / purchase option: `{_cell(rate_card.model_id)}` / `{_cell(rate_card.region)}` / `{_cell(rate_card.purchase_option)}`",
            f"- Currency / unit: `{_cell(rate_card.currency)}` / `{_cell(rate_card.unit)}`",
            f"- Source URL: `{_cell(rate_card.source_url)}`",
            f"- Offer publication / effective date: `{rate_card.offer_publication_date}` / `{rate_card.effective_date}`",
            f"- Retrieved at (UTC): `{rate_card.retrieved_at_utc}`",
            f"- Rate provenance digest: `{canonical_sha256(rate_card)}`",
            "",
            "## Billing confirmation (separate from service cost)",
            "",
            f"- Status: `{report.billing_status.value}`",
            f"- Confirmed amount (USD): `{_cell(report.billing_amount_usd)}`",
            f"- Confirmation date/time: `{_cell(report.billing_confirmed_at_utc)}`",
            "",
            "## Delivery and collision",
            "",
            f"- Preflight destination state: `{preflight_destination.state.value}`",
            f"- Delivery decision: `{delivery.status.value}`",
            f"- Destination state at delivery: `{delivery.destination_state.value}`",
            f"- Runtime source path: `{_cell(delivery.source_path)}`",
            f"- Destination path: `{_cell(delivery.destination_path)}`",
            f"- Source bytes / SHA-256: `{delivery.source_byte_count}` / `{delivery.source_sha256}`",
            f"- Destination bytes / SHA-256: `{_cell(delivery.destination_byte_count)}` / `{_cell(delivery.destination_sha256)}`",
            f"- Complete byte sequence verified: `{str(delivery.complete_byte_sequence_verified).lower()}`",
            f"- Verified temporary copy: `{str(delivery.temporary_copy_verified).lower()}`",
            f"- Atomic publication performed: `{str(delivery.atomic_publish_performed).lower()}`",
            f"- Existing destination preserved: `{str(delivery.destination_preserved).lower()}`",
            "",
            "## Isolation",
            "",
            f"- Status: `{'passed' if isolation.passed else 'blocked'}`",
            f"- Hard protected drift paths: `{len(isolation.hard_protected_drift_paths)}`",
            f"- Concurrent/unattributed manuscript changes: `{len(isolation.concurrent_manuscript_change_paths)}`",
            f"- Workflow writes outside allowlist: `{len(isolation.workflow_writes_outside_allowlist)}`",
            f"- Isolation digest: `{isolation.canonical_sha256}`",
            "",
            "## Tests",
            "",
            f"- Targeted_Checks: `{'passed' if local_preflight.targeted_checks.passed else 'blocked'}`",
            f"- Targeted_Checks result SHA-256: `{local_preflight.targeted_checks.result_sha256}`",
            f"- Targeted_Checks binding SHA-256: `{report.targeted_checks_sha256}`",
            f"- Targeted_Checks return code: `{local_preflight.targeted_checks.return_code}`",
            f"- AWS access disabled: `{str(local_preflight.targeted_checks.aws_access_disabled).lower()}`",
            f"- Model access disabled: `{str(local_preflight.targeted_checks.model_access_disabled).lower()}`",
            f"- Broader_Suite_Result (separate): `{report.broader_suite_status.value}`",
            "",
            "## Supplemental listening",
            "",
        ]
    )
    if report.supplemental_listening_sha256 is None:
        lines.append("No listening feedback was supplied.")
    else:
        lines.extend(
            [
                f"- Listening feedback SHA-256: `{report.supplemental_listening_sha256}`",
                "- Classification: `supplemental-only`; this feedback does not replace or alter deterministic Delivery_Gate results.",
            ]
        )
    lines.append("")
    return "\n".join(lines).encode("utf-8")


def write_track_report(
    workspace_root: Path,
    plan_path: Path,
    track_id: str,
    transaction_id: str,
    *,
    local_preflight: LocalPreflightResult,
    bounded_preflight: BoundedPreflightEstimateResult,
    authorization: PaidAuthorization,
    attempt: Any,
    accounting: ExactAccountingResult,
    isolation: IsolationAssessment,
    broader_suite_status: ValidationStatus = ValidationStatus.NOT_RUN,
    supplemental_listening_sha256: str | None = None,
    generated_at_utc: str | None = None,
    clock: Clock | None = None,
) -> TrackReport:
    """Create or return one immutable sanitized report for a delivered Track."""

    scope = load_production_track_scope(
        workspace_root,
        plan_path,
        track_id,
        transaction_id,
    )
    validation, delivery = _load_transaction_evidence(scope)
    reuse, destination, estimate, rate_card = _validate_track_report_inputs(
        scope,
        local_preflight,
        bounded_preflight,
        authorization,
        attempt,
        validation,
        accounting,
        delivery,
        isolation,
        broader_suite_status,
    )
    if supplemental_listening_sha256 is not None and (
        len(supplemental_listening_sha256) != 64
        or any(character not in "0123456789abcdef" for character in supplemental_listening_sha256)
    ):
        raise InputError("supplemental listening evidence must be a lowercase SHA-256 digest")

    report_json = scope.transaction_root / "report.json"
    report_markdown = scope.transaction_root / "report.md"
    codec = StrictRecordCodec(TrackReport)
    if os.path.lexists(report_json):
        existing = codec.load(report_json)
        expected = _build_track_record(
            scope,
            generated_at_utc=existing.generated_at_utc,
            bounded_preflight=bounded_preflight,
            authorization=authorization,
            attempt=attempt,
            validation=validation,
            accounting=accounting,
            delivery=delivery,
            isolation=isolation,
            targeted_checks_sha256=local_preflight.targeted_checks.binding_sha256,
            broader_suite_status=broader_suite_status,
            supplemental_listening_sha256=supplemental_listening_sha256,
        )
        if existing != expected:
            raise InputError("Existing Track_Report binds different evidence")
        markdown = _render_track_markdown(
            existing,
            scope,
            local_preflight,
            bounded_preflight,
            authorization,
            attempt,
            validation,
            accounting,
            delivery,
            isolation,
            reuse,
            destination,
            estimate,
            rate_card,
        )
        _assert_report_markdown_safe(
            scope,
            report_markdown,
            markdown,
            validation=validation,
        )
        write_immutable_evidence(report_markdown, markdown)
        return existing
    if os.path.lexists(report_markdown):
        raise InputError("Track_Report Markdown exists without its canonical record")

    report = _build_track_record(
        scope,
        generated_at_utc=_timestamp(generated_at_utc, clock, "generated"),
        bounded_preflight=bounded_preflight,
        authorization=authorization,
        attempt=attempt,
        validation=validation,
        accounting=accounting,
        delivery=delivery,
        isolation=isolation,
        targeted_checks_sha256=local_preflight.targeted_checks.binding_sha256,
        broader_suite_status=broader_suite_status,
        supplemental_listening_sha256=supplemental_listening_sha256,
    )
    markdown = _render_track_markdown(
        report,
        scope,
        local_preflight,
        bounded_preflight,
        authorization,
        attempt,
        validation,
        accounting,
        delivery,
        isolation,
        reuse,
        destination,
        estimate,
        rate_card,
    )
    _assert_report_markdown_safe(
        scope,
        report_markdown,
        markdown,
        validation=validation,
    )
    write_immutable_evidence(report_json, codec.dump_bytes(report))
    write_immutable_evidence(report_markdown, markdown)
    if codec.load(report_json) != report or read_bytes_nofollow(report_markdown) != markdown:
        raise InputError("Track_Report failed durable round-trip verification")
    return report


def deliver_and_write_track_report(
    workspace_root: Path,
    plan_path: Path,
    track_id: str,
    transaction_id: str,
    *,
    local_preflight: LocalPreflightResult,
    bounded_preflight: BoundedPreflightEstimateResult,
    authorization: PaidAuthorization,
    attempt: Any,
    accounting: ExactAccountingResult,
    isolation: IsolationAssessment,
    broader_suite_status: ValidationStatus = ValidationStatus.NOT_RUN,
    supplemental_listening_sha256: str | None = None,
    delivered_at_utc: str | None = None,
    generated_at_utc: str | None = None,
) -> DeliveryAndReportResult:
    """Run the complete idempotent nonbillable deliver operation.

    Conflicts retain and block the destination without creating a success report.
    Every successful publication/retention creates or reuses its Track_Report.
    """

    delivery = deliver_validated_track(
        workspace_root,
        plan_path,
        track_id,
        transaction_id,
        delivered_at_utc=delivered_at_utc,
    )
    if delivery.status is DeliveryStatus.CONFLICTING:
        return DeliveryAndReportResult(delivery, None)
    report = write_track_report(
        workspace_root,
        plan_path,
        track_id,
        transaction_id,
        local_preflight=local_preflight,
        bounded_preflight=bounded_preflight,
        authorization=authorization,
        attempt=attempt,
        accounting=accounting,
        isolation=isolation,
        broader_suite_status=broader_suite_status,
        supplemental_listening_sha256=supplemental_listening_sha256,
        generated_at_utc=generated_at_utc,
    )
    return DeliveryAndReportResult(delivery, report)


def _batch_report_inputs(
    scope: ProductionTrackScope,
) -> tuple[
    tuple[BatchTrackReportEntry, ...],
    tuple[tuple[TrackReport | None, DeliveryRecord | None], ...],
    Any,
]:
    plan_status = scope.store.inspect_plan_status(scope.plan)
    entries: list[BatchTrackReportEntry] = []
    details: list[tuple[TrackReport | None, DeliveryRecord | None]] = []
    track_report_codec = StrictRecordCodec(TrackReport)
    delivery_codec = StrictRecordCodec(DeliveryRecord)
    for status in plan_status.tracks:
        if status.health is not TransactionHealth.VALID or status.state is None:
            raise InputError(
                "Batch_Report requires independently valid transaction truth for every Track"
            )
        transaction_root = scope.store.transaction_path(
            status.track_id,
            status.transaction_id,
        )
        report_path = transaction_root / "report.json"
        report: TrackReport | None = None
        delivery: DeliveryRecord | None = None
        report_sha256: str | None = None
        if os.path.lexists(report_path):
            report = track_report_codec.load(report_path)
            if (
                report.transaction_id != status.transaction_id
                or report.track_id != status.track_id
                or report.state is not status.state
            ):
                raise InputError("Track_Report differs from independent ledger truth")
            report_sha256 = track_report_codec.sha256(report)
            delivery_path = transaction_root / "delivery" / "delivery.json"
            delivery = delivery_codec.load(delivery_path)
        elif status.state is TransactionState.DELIVERED:
            raise InputError("Delivered Track is missing its required Track_Report")
        entries.append(
            BatchTrackReportEntry(
                transaction_id=status.transaction_id,
                track_id=status.track_id,
                sequence=status.sequence,
                state=status.state,
                track_report_sha256=report_sha256,
            )
        )
        details.append((report, delivery))
    return tuple(entries), tuple(details), plan_status


def _build_batch_record(
    scope: ProductionTrackScope,
    entries: tuple[BatchTrackReportEntry, ...],
    plan_status: Any,
    generated_at_utc: str,
) -> BatchReport:
    return seal_record(
        BatchReport(
            schema_version=RECORD_SCHEMA_VERSION,
            plan_id=scope.plan.plan_id,
            plan_sha256=scope.plan.canonical_sha256,
            generated_at_utc=generated_at_utc,
            status=plan_status.status,
            tracks=entries,
            selected_count=plan_status.selected_count,
            completed_count=plan_status.completed_count,
            blocked_count=plan_status.blocked_count,
            unstarted_count=plan_status.unstarted_count,
            canonical_sha256="",
        )
    )


def _render_batch_markdown(
    report: BatchReport,
    details: tuple[tuple[TrackReport | None, DeliveryRecord | None], ...],
) -> bytes:
    lines = [
        f"# Batch Report: {_cell(report.plan_id)}",
        "",
        "> Sanitized aggregate derived from independent Track transaction ledgers and Track_Report digests.",
        "",
        "## Batch state",
        "",
        f"- Frozen plan SHA-256: `{report.plan_sha256}`",
        f"- Batch report canonical content SHA-256: `{report.canonical_sha256}`",
        f"- Derived status: `{report.status.value}`",
        f"- Generated at (UTC): `{report.generated_at_utc}`",
        f"- Selected / completed / blocked / unstarted: `{report.selected_count}` / `{report.completed_count}` / `{report.blocked_count}` / `{report.unstarted_count}`",
        f"- Nonbillable report operation: `true`",
        "",
        "## Selected Track transactions",
        "",
        "| Seq | Track | Transaction | State | Track_Report SHA-256 | Validation SHA-256 | Usage active/current | Estimate USD | Exact current USD | Billing | Isolation | Tests targeted/broader | Delivery / collision | Supplemental listening |",
        "|---:|---|---|---|---|---|---|---:|---:|---|---|---|---|---|",
    ]
    for entry, (track_report, delivery) in zip(report.tracks, details, strict=True):
        if track_report is None:
            row = (
                entry.sequence,
                entry.track_id,
                entry.transaction_id,
                entry.state.value,
                "not-available",
                "not-available",
                "not-available",
                "not-available",
                "not-available",
                "not-available",
                "not-available",
                "not-available",
                "not-available",
                "not-available",
            )
        else:
            active = sum(
                _usage_value(track_report.active_artifact_totals, modality)
                for modality in ("input_speech", "input_text", "output_speech", "output_text")
            )
            current = sum(
                _usage_value(track_report.current_execution_totals, modality)
                for modality in ("input_speech", "input_text", "output_speech", "output_text")
            )
            row = (
                entry.sequence,
                entry.track_id,
                entry.transaction_id,
                entry.state.value,
                entry.track_report_sha256,
                track_report.validation_sha256,
                f"{active}/{current}",
                track_report.estimated_pre_tax_usd,
                track_report.current_execution_cost_usd,
                track_report.billing_status.value,
                track_report.isolation_status.value,
                f"{track_report.targeted_checks_sha256}/{track_report.broader_suite_status.value}",
                (
                    f"{track_report.delivery_status.value}/{delivery.destination_state.value}"
                    if delivery is not None
                    else track_report.delivery_status.value
                ),
                track_report.supplemental_listening_sha256 or "not-supplied",
            )
        lines.append("| " + " | ".join(_cell(value) for value in row) + " |")
    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "- Validation, usage, estimate/exact cost, billing, isolation, tests, collision, and optional listening details remain independently reconstructable from each bound Track_Report.",
            "- Listening feedback is supplemental and never replaces deterministic Delivery_Gate results.",
            "",
        ]
    )
    return "\n".join(lines).encode("utf-8")


def write_batch_report(
    workspace_root: Path,
    plan_path: Path,
    *,
    generated_at_utc: str | None = None,
    clock: Clock | None = None,
) -> BatchReport:
    """Create an idempotent derived Batch_Report listing every selected Track."""

    root = workspace_root.expanduser().resolve()
    # Every valid plan has at least one Track.  Reuse the exact scope loader to bind
    # the plan path and production book root before deriving aggregate truth.
    candidate_plan = load_production_track_scope_from_plan(root, plan_path)
    scope = load_production_track_scope(
        root,
        candidate_plan[0],
        candidate_plan[1].track_id,
        candidate_plan[1].transaction_id,
    )
    entries, details, plan_status = _batch_report_inputs(scope)
    report_root = scope.book_root / "batches" / scope.plan.plan_id
    report_json = report_root / "report.json"
    report_markdown = report_root / "report.md"
    codec = StrictRecordCodec(BatchReport)

    existing: BatchReport | None = None
    if os.path.lexists(report_json):
        existing = codec.load(report_json)
        expected = _build_batch_record(
            scope,
            entries,
            plan_status,
            existing.generated_at_utc,
        )
        if existing == expected:
            markdown = _render_batch_markdown(existing, details)
            _assert_report_markdown_safe(scope, report_markdown, markdown)
            write_immutable_evidence(report_markdown, markdown)
            return existing

    generated = _timestamp(generated_at_utc, clock, "generated")
    report = _build_batch_record(scope, entries, plan_status, generated)
    markdown = _render_batch_markdown(report, details)
    _assert_report_markdown_safe(scope, report_markdown, markdown)
    # Batch reports are explicitly derived caches.  Changed transaction truth may
    # replace the prior aggregate, while unchanged truth above retains exact bytes.
    atomic_write_bytes(report_json, codec.dump_bytes(report))
    atomic_write_bytes(report_markdown, markdown)
    if codec.load(report_json) != report or read_bytes_nofollow(report_markdown) != markdown:
        raise InputError("Batch_Report failed durable round-trip verification")
    if scope.store.inspect_plan_status(scope.plan) != plan_status:
        raise InputError("Transaction truth changed while Batch_Report was generated")
    return report


def load_production_track_scope_from_plan(
    workspace_root: Path,
    plan_path: Path,
) -> tuple[Path, Any]:
    """Load a plan once to select a representative Track for exact layout binding."""

    candidate = plan_path.expanduser()
    if not candidate.is_absolute():
        candidate = workspace_root / candidate
    plan = StrictRecordCodec(FrozenBatchPlan).load(candidate)
    if not plan.tracks:
        raise InputError("Batch_Report requires a nonempty Frozen_Plan")
    return candidate, plan.tracks[0]


__all__ = [
    "DeliveryAndReportResult",
    "deliver_and_write_track_report",
    "write_batch_report",
    "write_track_report",
]
