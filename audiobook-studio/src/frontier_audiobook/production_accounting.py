"""Strict Event_Journal aggregation and exact production cost accounting.

The accounting boundary is intentionally offline.  Callers supply validated active
segment bindings and a preflight ``OfficialRateCard``; this module never retrieves
rates, resolves identity, launches a child, or invokes a model.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation, localcontext
from enum import StrEnum
from pathlib import Path, PurePosixPath

from .errors import InputError
from .production_models import BillingStatus, TOKEN_MODALITIES, UsageTotals
from .production_preflight import OfficialRateCard, OfficialRateTarget
from .util import json_loads_strict, read_bytes_nofollow, resolve_inside, sha256_bytes

_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_DECIMAL_PATTERN = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d+)?$")
_UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
_USAGE_EVENT_FIELDS = {
    "completionId",
    "promptName",
    "sessionId",
    "details",
    "totalInputTokens",
    "totalOutputTokens",
    "totalTokens",
}
_TOKEN_DIRECTIONS = ("input", "output")
_TOKEN_KINDS = ("speechTokens", "textTokens")
_MODALITY_LOCATIONS = (
    ("input_speech", "input", "speechTokens"),
    ("input_text", "input", "textTokens"),
    ("output_speech", "output", "speechTokens"),
    ("output_text", "output", "textTokens"),
)


class CostScopeName(StrEnum):
    """The two non-interchangeable exact usage/cost scopes."""

    ACTIVE_ARTIFACT = "active-artifact"
    CURRENT_EXECUTION = "current-execution"


class BudgetExceptionStatus(StrEnum):
    """Whether current-execution exact service cost exceeded authorization."""

    WITHIN_APPROVED_MAXIMUM = "within-approved-maximum"
    BLOCKING = "blocking-exceeds-approved-maximum"


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value:
        raise InputError(f"{label} must be a nonblank canonical string")
    return value


def _require_relative_path(value: object, label: str, *, suffix: str) -> str:
    text = _require_text(value, label)
    if "\\" in text:
        raise InputError(f"{label} must use workspace-relative POSIX separators")
    candidate = PurePosixPath(text)
    if (
        candidate.is_absolute()
        or text == "."
        or any(part in {"", ".", ".."} for part in candidate.parts)
        or candidate.as_posix() != text
    ):
        raise InputError(f"{label} must be a traversal-free canonical relative path")
    if candidate.suffix != suffix:
        raise InputError(f"{label} must end in {suffix}")
    return text


def _require_sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_PATTERN.fullmatch(value):
        raise InputError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_nonnegative_int(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise InputError(f"{label} must be a nonnegative integer")
    return value


def _require_decimal(value: object, label: str, *, positive: bool = False) -> Decimal:
    text = _require_text(value, label)
    if not _DECIMAL_PATTERN.fullmatch(text):
        raise InputError(f"{label} must be a nonnegative plain decimal string")
    try:
        parsed = Decimal(text)
    except InvalidOperation as exc:  # pragma: no cover - guarded by the pattern
        raise InputError(f"{label} must be a valid decimal string") from exc
    if not parsed.is_finite() or parsed < 0 or (positive and parsed == 0):
        qualifier = "positive" if positive else "nonnegative"
        raise InputError(f"{label} must be finite and {qualifier}")
    return parsed


def _require_utc(value: object, label: str) -> str:
    text = _require_text(value, label)
    if not _UTC_PATTERN.fullmatch(text):
        raise InputError(f"{label} must be an ISO-8601 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(text.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise InputError(f"{label} is not a valid UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.astimezone(UTC).utcoffset() is None:
        raise InputError(f"{label} must be UTC")
    return text


def _require_exact_keys(value: object, expected: set[str], label: str) -> Mapping[str, object]:
    if not isinstance(value, dict):
        raise InputError(f"{label} must be an object")
    actual = set(value)
    if actual != expected:
        raise InputError(
            f"{label} fields are invalid; missing={sorted(expected - actual)}, "
            f"unknown={sorted(actual - expected)}"
        )
    return value


def _canonical_decimal(value: Decimal) -> str:
    if not value.is_finite() or value < 0:
        raise InputError("Cost values must be finite and nonnegative")
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _exact_subtotal(tokens: int, rate: Decimal) -> Decimal:
    precision = max(28, len(str(tokens)) + len(rate.as_tuple().digits) + 8)
    with localcontext() as context:
        context.prec = precision
        return Decimal(tokens) * rate / Decimal(1000)


def _exact_sum(values: Iterable[Decimal]) -> Decimal:
    """Add finite nonnegative decimals without context-dependent rounding."""

    items = tuple(values)
    if not items:
        return Decimal("0")
    if any(not item.is_finite() or item < 0 for item in items):
        raise InputError("Exact cost subtotals must be finite and nonnegative")

    # Decimal addition obeys the active context and can otherwise discard a very
    # small subtotal when it is combined with a much larger one.  Align the
    # integer coefficients explicitly so every represented decimal place is kept.
    common_exponent = min(int(item.as_tuple().exponent) for item in items)
    total_coefficient = 0
    for item in items:
        parts = item.as_tuple()
        coefficient = 0
        for digit in parts.digits:
            coefficient = (coefficient * 10) + digit
        total_coefficient += coefficient * (10 ** (int(parts.exponent) - common_exponent))

    if total_coefficient == 0:
        return Decimal("0")
    digits = tuple(int(character) for character in str(total_coefficient))
    return Decimal((0, digits, common_exponent))


def _usage_totals(values: Mapping[str, int]) -> UsageTotals:
    return UsageTotals(**{modality: values[modality] for modality in TOKEN_MODALITIES})


def _sum_usage_totals(values: Iterable[UsageTotals]) -> UsageTotals:
    materialized = tuple(values)
    totals = {
        modality: sum(getattr(value, modality) for value in materialized)
        for modality in TOKEN_MODALITIES
    }
    return _usage_totals(totals)


@dataclass(frozen=True, slots=True)
class JournalCandidate:
    """One mandatory path/hash binding for an active audio stem's Event_Journal."""

    path: str
    expected_sha256: str

    def __post_init__(self) -> None:
        _require_relative_path(self.path, "Event_Journal candidate path", suffix=".jsonl")
        _require_sha256(self.expected_sha256, "Event_Journal expected_sha256")


@dataclass(frozen=True, slots=True)
class ActiveAudioStem:
    """Minimal active-manifest projection needed for usage accounting."""

    segment_id: str
    audio_path: str
    rendered_in_current_attempt: bool
    journal_candidates: tuple[JournalCandidate, ...]

    def __post_init__(self) -> None:
        _require_text(self.segment_id, "active segment_id")
        _require_relative_path(self.audio_path, "active audio_path", suffix=".wav")
        if type(self.rendered_in_current_attempt) is not bool:
            raise InputError("rendered_in_current_attempt must be a boolean")
        if not isinstance(self.journal_candidates, tuple) or not all(
            isinstance(candidate, JournalCandidate) for candidate in self.journal_candidates
        ):
            raise InputError("journal_candidates must be a tuple of JournalCandidate records")


@dataclass(frozen=True, slots=True)
class ResolvedJournalUsage:
    segment_id: str
    audio_path: str
    journal_path: str
    journal_sha256: str
    rendered_in_current_attempt: bool
    usage_event_count: int
    totals: UsageTotals

    def __post_init__(self) -> None:
        _require_text(self.segment_id, "resolved journal segment_id")
        _require_relative_path(self.audio_path, "resolved journal audio_path", suffix=".wav")
        _require_relative_path(
            self.journal_path,
            "resolved Event_Journal path",
            suffix=".jsonl",
        )
        _require_sha256(self.journal_sha256, "resolved Event_Journal SHA-256")
        if type(self.rendered_in_current_attempt) is not bool:
            raise InputError("resolved journal current-attempt marker must be a boolean")
        _require_nonnegative_int(self.usage_event_count, "usage_event_count")
        if self.usage_event_count == 0:
            raise InputError("resolved Event_Journal must contain a usageEvent")
        if not isinstance(self.totals, UsageTotals):
            raise InputError("resolved Event_Journal totals must be UsageTotals")


@dataclass(frozen=True, slots=True)
class JournalAggregation:
    """Exactly-once usage totals for all active and current-execution journals."""

    journals: tuple[ResolvedJournalUsage, ...]
    active_artifact_totals: UsageTotals
    current_execution_totals: UsageTotals

    def __post_init__(self) -> None:
        if not isinstance(self.journals, tuple) or not self.journals or not all(
            isinstance(journal, ResolvedJournalUsage) for journal in self.journals
        ):
            raise InputError("journal aggregation requires active resolved journals")
        for label, values in (
            ("segment IDs", (item.segment_id for item in self.journals)),
            ("audio paths", (item.audio_path for item in self.journals)),
            ("Event_Journal paths", (item.journal_path for item in self.journals)),
            ("Event_Journal SHA-256 digests", (item.journal_sha256 for item in self.journals)),
        ):
            materialized = tuple(values)
            if len(set(materialized)) != len(materialized):
                raise InputError(f"journal aggregation contains duplicate {label}")
        expected_active = _sum_usage_totals(item.totals for item in self.journals)
        expected_current = _sum_usage_totals(
            item.totals for item in self.journals if item.rendered_in_current_attempt
        )
        if self.active_artifact_totals != expected_active:
            raise InputError("Active_Artifact_Totals do not equal active journals exactly once")
        if self.current_execution_totals != expected_current:
            raise InputError(
                "Current_Execution_Totals do not equal current-attempt journals exactly once"
            )


@dataclass(frozen=True, slots=True)
class BillingConfirmation:
    """Invoice/Cost Explorer evidence, deliberately separate from service cost."""

    status: BillingStatus
    amount_usd: str | None = None
    confirmed_at_utc: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, BillingStatus):
            raise InputError("billing confirmation status must be a BillingStatus")
        if self.status is BillingStatus.CONFIRMED:
            if self.amount_usd is None or self.confirmed_at_utc is None:
                raise InputError("confirmed billing requires an amount and confirmation timestamp")
            _require_decimal(self.amount_usd, "billing confirmation amount_usd")
            _require_utc(self.confirmed_at_utc, "billing confirmation confirmed_at_utc")
        elif self.amount_usd is not None or self.confirmed_at_utc is not None:
            raise InputError("pending/not-performed billing must not include confirmation values")


@dataclass(frozen=True, slots=True)
class ModalityCostLine:
    modality: str
    tokens: int
    rate_per_1k_tokens: str
    formula: str
    unrounded_subtotal_usd: str

    def __post_init__(self) -> None:
        if self.modality not in TOKEN_MODALITIES:
            raise InputError(f"Unknown exact-cost modality: {self.modality!r}")
        tokens = _require_nonnegative_int(self.tokens, f"{self.modality} exact-cost tokens")
        rate = _require_decimal(
            self.rate_per_1k_tokens,
            f"{self.modality} exact official rate",
            positive=True,
        )
        expected_formula = (
            f'Decimal("{tokens}") * Decimal("{self.rate_per_1k_tokens}") '
            '/ Decimal("1000")'
        )
        if self.formula != expected_formula:
            raise InputError(f"{self.modality} exact-cost formula is not canonical")
        expected_subtotal = _exact_subtotal(tokens, rate)
        if _require_decimal(
            self.unrounded_subtotal_usd,
            f"{self.modality} unrounded subtotal",
        ) != expected_subtotal:
            raise InputError(f"{self.modality} subtotal does not equal tokens × rate ÷ 1000")


@dataclass(frozen=True, slots=True)
class ExactCostScope:
    scope: CostScopeName
    token_totals: UsageTotals
    modality_lines: tuple[ModalityCostLine, ...]
    computed_pre_tax_service_cost_usd: str

    def __post_init__(self) -> None:
        if not isinstance(self.scope, CostScopeName):
            raise InputError("exact cost scope must be a CostScopeName")
        if not isinstance(self.token_totals, UsageTotals):
            raise InputError("exact cost scope token_totals must be UsageTotals")
        if tuple(line.modality for line in self.modality_lines) != TOKEN_MODALITIES:
            raise InputError("exact cost lines must contain all four modalities in canonical order")
        for line in self.modality_lines:
            if line.tokens != getattr(self.token_totals, line.modality):
                raise InputError("exact cost line token count differs from its usage scope")
        expected = _exact_sum(
            _require_decimal(line.unrounded_subtotal_usd, "exact cost line subtotal")
            for line in self.modality_lines
        )
        if _require_decimal(
            self.computed_pre_tax_service_cost_usd,
            "Computed_Pre_Tax_Service_Cost",
        ) != expected:
            raise InputError("Computed_Pre_Tax_Service_Cost must equal exact modality subtotals")


@dataclass(frozen=True, slots=True)
class ExactAccountingResult:
    """Report-ready accounting with estimate, exact cost, billing, and budget split."""

    calculated_at_utc: str
    journal_aggregation: JournalAggregation
    official_rate_card: OfficialRateCard
    cost_estimate_usd: str
    operator_approved_max_estimated_pre_tax_usd: str
    active_artifact_cost: ExactCostScope
    current_execution_cost: ExactCostScope
    billing_confirmation: BillingConfirmation
    budget_exception_status: BudgetExceptionStatus

    def __post_init__(self) -> None:
        _require_utc(self.calculated_at_utc, "accounting calculated_at_utc")
        if not isinstance(self.journal_aggregation, JournalAggregation):
            raise InputError("accounting journal_aggregation must be a JournalAggregation")
        if not isinstance(self.official_rate_card, OfficialRateCard):
            raise InputError("accounting requires complete OfficialRateCard provenance")
        estimate = _require_decimal(self.cost_estimate_usd, "Cost_Estimate")
        approved = _require_decimal(
            self.operator_approved_max_estimated_pre_tax_usd,
            "operator-approved maximum estimated pre-tax USD",
        )
        if approved < estimate:
            raise InputError("operator-approved maximum must not be lower than Cost_Estimate")
        if self.active_artifact_cost.scope is not CostScopeName.ACTIVE_ARTIFACT:
            raise InputError("active artifact cost has the wrong scope label")
        if self.current_execution_cost.scope is not CostScopeName.CURRENT_EXECUTION:
            raise InputError("current execution cost has the wrong scope label")
        if (
            self.active_artifact_cost.token_totals
            != self.journal_aggregation.active_artifact_totals
            or self.current_execution_cost.token_totals
            != self.journal_aggregation.current_execution_totals
        ):
            raise InputError("exact cost token scopes differ from journal aggregation")
        if not isinstance(self.billing_confirmation, BillingConfirmation):
            raise InputError("billing_confirmation must be a BillingConfirmation")
        current_cost = _require_decimal(
            self.current_execution_cost.computed_pre_tax_service_cost_usd,
            "current execution Computed_Pre_Tax_Service_Cost",
        )
        expected_budget_status = (
            BudgetExceptionStatus.BLOCKING
            if current_cost > approved
            else BudgetExceptionStatus.WITHIN_APPROVED_MAXIMUM
        )
        if self.budget_exception_status is not expected_budget_status:
            raise InputError("budget exception status must reflect current-execution exact cost")


def _token_vector(value: object, label: str) -> dict[str, int]:
    outer = _require_exact_keys(value, set(_TOKEN_DIRECTIONS), label)
    result: dict[str, int] = {}
    for direction in _TOKEN_DIRECTIONS:
        inner = _require_exact_keys(
            outer[direction],
            set(_TOKEN_KINDS),
            f"{label}.{direction}",
        )
        for token_kind in _TOKEN_KINDS:
            result[f"{direction}.{token_kind}"] = _require_nonnegative_int(
                inner[token_kind],
                f"{label}.{direction}.{token_kind}",
            )
    return result


def _modalities_from_vector(value: Mapping[str, int]) -> dict[str, int]:
    return {
        modality: value[f"{direction}.{token_kind}"]
        for modality, direction, token_kind in _MODALITY_LOCATIONS
    }


def parse_event_journal_usage(raw: bytes, *, label: str = "Event_Journal") -> tuple[UsageTotals, int]:
    """Sum only integer modality deltas and reconcile every cumulative total.

    The returned totals are derived exclusively from ``details.delta``.  The
    ``details.total`` vectors and top-level input/output/combined totals are
    reconciliation evidence and are never themselves summed.
    """

    if type(raw) is not bytes:
        raise InputError(f"{label} content must be bytes")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError(f"Malformed UTF-8 in {label}: {exc}") from exc
    lines = text.splitlines()
    if not lines or any(not line for line in lines):
        raise InputError(f"{label} must be nonempty JSONL without blank records")

    accumulated = {modality: 0 for modality in TOKEN_MODALITIES}
    usage_event_count = 0
    bound_identity: tuple[str, str, str] | None = None

    for line_number, line in enumerate(lines, start=1):
        event = json_loads_strict(line, f"{label} line {line_number}")
        if not isinstance(event, dict) or len(event) != 1:
            raise InputError(f"{label} line {line_number} must contain exactly one event type")
        event_name, payload = next(iter(event.items()))
        if not isinstance(event_name, str) or not event_name:
            raise InputError(f"{label} line {line_number} has an invalid event type")
        if not isinstance(payload, dict):
            raise InputError(f"{label} line {line_number} event payload must be an object")
        if event_name != "usageEvent":
            continue

        usage_event_count += 1
        usage = _require_exact_keys(
            payload,
            _USAGE_EVENT_FIELDS,
            f"{label} usageEvent {usage_event_count}",
        )
        identity = tuple(
            _require_text(usage[field], f"{label} usageEvent {usage_event_count}.{field}")
            for field in ("sessionId", "promptName", "completionId")
        )
        if bound_identity is None:
            bound_identity = identity
        elif identity != bound_identity:
            raise InputError(f"{label} contains usageEvents from different model calls")

        details = _require_exact_keys(
            usage["details"],
            {"delta", "total"},
            f"{label} usageEvent {usage_event_count}.details",
        )
        deltas = _modalities_from_vector(
            _token_vector(
                details["delta"],
                f"{label} usageEvent {usage_event_count}.details.delta",
            )
        )
        recorded_modality_totals = _modalities_from_vector(
            _token_vector(
                details["total"],
                f"{label} usageEvent {usage_event_count}.details.total",
            )
        )
        for modality in TOKEN_MODALITIES:
            accumulated[modality] += deltas[modality]
        if recorded_modality_totals != accumulated:
            raise InputError(
                f"{label} usageEvent {usage_event_count} terminal modality totals "
                "do not reconcile with summed deltas"
            )

        recorded_input = _require_nonnegative_int(
            usage["totalInputTokens"],
            f"{label} usageEvent {usage_event_count}.totalInputTokens",
        )
        recorded_output = _require_nonnegative_int(
            usage["totalOutputTokens"],
            f"{label} usageEvent {usage_event_count}.totalOutputTokens",
        )
        recorded_combined = _require_nonnegative_int(
            usage["totalTokens"],
            f"{label} usageEvent {usage_event_count}.totalTokens",
        )
        expected_input = accumulated["input_speech"] + accumulated["input_text"]
        expected_output = accumulated["output_speech"] + accumulated["output_text"]
        if (
            recorded_input != expected_input
            or recorded_output != expected_output
            or recorded_combined != expected_input + expected_output
        ):
            raise InputError(
                f"{label} usageEvent {usage_event_count} combined terminal totals "
                "do not reconcile with modality totals"
            )

    if usage_event_count == 0:
        raise InputError(f"{label} contains no usageEvent evidence")
    return _usage_totals(accumulated), usage_event_count


def _expected_journal_path(audio_path: str) -> str:
    audio = PurePosixPath(audio_path)
    if len(audio.parents) < 2:
        raise InputError("active audio_path cannot bind a sibling events directory")
    return (audio.parent.parent / "events" / f"{audio.stem}.jsonl").as_posix()


def resolve_and_aggregate_journals(
    workspace_root: Path,
    active_audio_stems: Iterable[ActiveAudioStem],
) -> JournalAggregation:
    """Resolve exactly one hash-bound Event_Journal per active audio stem."""

    stems = tuple(active_audio_stems)
    if not stems or not all(isinstance(item, ActiveAudioStem) for item in stems):
        raise InputError("At least one ActiveAudioStem is required")
    for label, values in (
        ("segment IDs", (item.segment_id for item in stems)),
        ("audio paths", (item.audio_path for item in stems)),
    ):
        materialized = tuple(values)
        if len(set(materialized)) != len(materialized):
            raise InputError(f"active usage scope contains duplicate {label}")

    resolved: list[ResolvedJournalUsage] = []
    seen_journal_paths: set[str] = set()
    for stem in stems:
        candidate_paths = tuple(candidate.path for candidate in stem.journal_candidates)
        if not candidate_paths:
            raise InputError(f"Missing Event_Journal for active audio stem {stem.segment_id}")
        if len(set(candidate_paths)) != len(candidate_paths):
            raise InputError(f"Duplicate Event_Journal evidence for active audio stem {stem.segment_id}")
        if len(candidate_paths) != 1:
            raise InputError(f"Ambiguous Event_Journal evidence for active audio stem {stem.segment_id}")

        candidate = stem.journal_candidates[0]
        expected_path = _expected_journal_path(stem.audio_path)
        if candidate.path != expected_path:
            raise InputError(
                f"Event_Journal candidate does not match active audio stem {stem.segment_id}"
            )
        if candidate.path in seen_journal_paths:
            raise InputError("One Event_Journal cannot account for multiple active audio stems")
        seen_journal_paths.add(candidate.path)

        path = resolve_inside(workspace_root, candidate.path)
        if not path.is_file():
            raise InputError(f"Missing Event_Journal for active audio stem {stem.segment_id}")
        raw = read_bytes_nofollow(path)
        digest = sha256_bytes(raw)
        if candidate.expected_sha256 is not None and digest != candidate.expected_sha256:
            raise InputError(f"Tampered Event_Journal for active audio stem {stem.segment_id}")
        totals, event_count = parse_event_journal_usage(raw, label=candidate.path)
        resolved.append(
            ResolvedJournalUsage(
                segment_id=stem.segment_id,
                audio_path=stem.audio_path,
                journal_path=candidate.path,
                journal_sha256=digest,
                rendered_in_current_attempt=stem.rendered_in_current_attempt,
                usage_event_count=event_count,
                totals=totals,
            )
        )

    journals = tuple(resolved)
    return JournalAggregation(
        journals=journals,
        active_artifact_totals=_sum_usage_totals(item.totals for item in journals),
        current_execution_totals=_sum_usage_totals(
            item.totals for item in journals if item.rendered_in_current_attempt
        ),
    )


def _calculate_scope(
    scope: CostScopeName,
    totals: UsageTotals,
    rate_card: OfficialRateCard,
) -> ExactCostScope:
    rate_by_modality = {item.modality: item.rate_per_1k_tokens for item in rate_card.rates}
    lines: list[ModalityCostLine] = []
    for modality in TOKEN_MODALITIES:
        tokens = getattr(totals, modality)
        rate_text = rate_by_modality[modality]
        subtotal = _exact_subtotal(tokens, _require_decimal(rate_text, modality, positive=True))
        lines.append(
            ModalityCostLine(
                modality=modality,
                tokens=tokens,
                rate_per_1k_tokens=rate_text,
                formula=(
                    f'Decimal("{tokens}") * Decimal("{rate_text}") / Decimal("1000")'
                ),
                unrounded_subtotal_usd=_canonical_decimal(subtotal),
            )
        )
    modality_lines = tuple(lines)
    total = _exact_sum(
        _require_decimal(line.unrounded_subtotal_usd, "exact subtotal")
        for line in modality_lines
    )
    return ExactCostScope(
        scope=scope,
        token_totals=totals,
        modality_lines=modality_lines,
        computed_pre_tax_service_cost_usd=_canonical_decimal(total),
    )


def calculate_exact_accounting(
    aggregation: JournalAggregation,
    official_rate_card: OfficialRateCard,
    *,
    expected_rate_target: OfficialRateTarget,
    cost_estimate_usd: str,
    operator_approved_max_estimated_pre_tax_usd: str,
    calculated_at_utc: str,
    billing_confirmation: BillingConfirmation | None = None,
) -> ExactAccountingResult:
    """Calculate both exact scopes while retaining complete official provenance."""

    if not isinstance(aggregation, JournalAggregation):
        raise InputError("aggregation must be a JournalAggregation")
    if not isinstance(official_rate_card, OfficialRateCard):
        raise InputError("official_rate_card must contain complete official provenance")
    if not isinstance(expected_rate_target, OfficialRateTarget):
        raise InputError("expected_rate_target must be an OfficialRateTarget")
    if official_rate_card.target != expected_rate_target:
        raise InputError("Official rate provenance does not match the rendered model/region/option")
    _require_utc(calculated_at_utc, "accounting calculated_at_utc")
    estimate = _require_decimal(cost_estimate_usd, "Cost_Estimate")
    approved = _require_decimal(
        operator_approved_max_estimated_pre_tax_usd,
        "operator-approved maximum estimated pre-tax USD",
    )
    if approved < estimate:
        raise InputError("operator-approved maximum must not be lower than Cost_Estimate")

    active = _calculate_scope(
        CostScopeName.ACTIVE_ARTIFACT,
        aggregation.active_artifact_totals,
        official_rate_card,
    )
    current = _calculate_scope(
        CostScopeName.CURRENT_EXECUTION,
        aggregation.current_execution_totals,
        official_rate_card,
    )
    current_total = _require_decimal(
        current.computed_pre_tax_service_cost_usd,
        "current-execution exact service cost",
    )
    budget_status = (
        BudgetExceptionStatus.BLOCKING
        if current_total > approved
        else BudgetExceptionStatus.WITHIN_APPROVED_MAXIMUM
    )
    return ExactAccountingResult(
        calculated_at_utc=calculated_at_utc,
        journal_aggregation=aggregation,
        official_rate_card=official_rate_card,
        cost_estimate_usd=_canonical_decimal(estimate),
        operator_approved_max_estimated_pre_tax_usd=_canonical_decimal(approved),
        active_artifact_cost=active,
        current_execution_cost=current,
        billing_confirmation=billing_confirmation
        or BillingConfirmation(BillingStatus.PENDING),
        budget_exception_status=budget_status,
    )
