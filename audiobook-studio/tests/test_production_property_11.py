"""Deterministic generated checks for audiobook production correctness Property 11."""

from __future__ import annotations

import json
import random
import socket
import subprocess
import urllib.request
from dataclasses import dataclass, replace
from decimal import Decimal, localcontext
from pathlib import Path, PurePosixPath

import pytest

from frontier_audiobook import narrate, nova
from frontier_audiobook.errors import InputError
from frontier_audiobook.production_accounting import (
    ActiveAudioStem,
    BillingConfirmation,
    BudgetExceptionStatus,
    CostScopeName,
    JournalCandidate,
    calculate_exact_accounting,
    resolve_and_aggregate_journals,
)
from frontier_audiobook.production_models import BillingStatus, TOKEN_MODALITIES, UsageTotals
from frontier_audiobook.production_preflight import (
    OfficialModalityRate,
    OfficialRateCard,
    OfficialRateTarget,
)
from frontier_audiobook.util import sha256_bytes


PROPERTY_TAG = (
    "Feature: audiobook-production-workflow, Property 11: "
    "Journal aggregation and exact cost are modality-complete"
)
PROPERTY_SEED = 0xA0D10B11
GENERATED_CASES = 128

# **Validates: Requirements 4.10, 4.11, 4.13, 11.1, 11.2, 11.3, 11.4,
# 11.5, 11.6, 11.7, 11.8, 11.9, 11.10, 11.11, 11.12, 11.13, 11.14**

_MODEL_ID = "amazon.nova-2-sonic-v1:0"
_REGION = "us-east-1"
_PURCHASE_OPTION = "on-demand"
_RATE_SOURCE_URL = "https://aws.amazon.com/bedrock/pricing/"
_JOURNAL_FAILURES = (
    "missing-binding",
    "missing-file",
    "duplicate-binding",
    "ambiguous-binding",
    "unbound-path",
    "tampered-hash",
    "tampered-bytes",
    "malformed-json",
    "noninteger-delta",
    "modality-total",
    "combined-total",
    "mixed-model-call",
    "copied-journal",
)
_PROVENANCE_FAILURES = (
    "missing-model",
    "missing-region",
    "missing-purchase-option",
    "wrong-currency",
    "wrong-unit",
    "missing-source-url",
    "missing-publication-date",
    "missing-retrieval-time",
    "missing-effective-date",
    "missing-modality-rate",
    "duplicate-modality-rate",
    "nonpositive-rate",
    "target-mismatch",
)
_BUDGET_BOUNDARIES = ("below", "equal", "above")

_Delta = tuple[int, int, int, int]
_JournalDeltas = tuple[_Delta, ...]


@dataclass(frozen=True, slots=True)
class _GeneratedCase:
    case_index: int
    deltas_by_segment: tuple[_JournalDeltas, ...]
    rendered_in_current_attempt: tuple[bool, ...]
    rates: tuple[str, str, str, str]
    journal_failure: str
    provenance_failure: str
    budget_boundary: str
    billing_status: BillingStatus


@pytest.fixture(autouse=True)
def deny_external_paid_and_child_boundaries(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Fail immediately if Property 11 crosses an external or billable boundary."""

    def blocked(*_args, **_kwargs):
        raise AssertionError("Property 11 must remain local, offline, and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(subprocess, "Popen", blocked)
    monkeypatch.setattr(subprocess, "run", blocked)
    monkeypatch.setattr(urllib.request, "urlopen", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setattr(nova, "render_text", blocked)
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


def _decimal_text(value: Decimal) -> str:
    text = format(value, "f")
    if "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def _generated_rate(rng: random.Random) -> str:
    coefficient = 1 + rng.randrange(9_999_999)
    scale = 1 + rng.randrange(8)
    return _decimal_text(Decimal(coefficient).scaleb(-scale))


def _generated_cases() -> tuple[_GeneratedCase, ...]:
    rng = random.Random(PROPERTY_SEED)
    billing_statuses = tuple(BillingStatus)
    cases: list[_GeneratedCase] = []
    for case_index in range(GENERATED_CASES):
        journal_failure = _JOURNAL_FAILURES[case_index % len(_JOURNAL_FAILURES)]
        budget_boundary = _BUDGET_BOUNDARIES[(case_index * 5 + 1) % 3]
        segment_count = 1 + rng.randrange(5)
        partition_mode = case_index % 4
        if journal_failure == "copied-journal" or partition_mode >= 2:
            segment_count = max(segment_count, 2)

        if partition_mode == 0:
            current_partition = [True] * segment_count
        elif partition_mode == 1:
            current_partition = [False] * segment_count
        elif partition_mode == 2:
            current_partition = [index % 2 == 0 for index in range(segment_count)]
        else:
            current_partition = [bool(rng.getrandbits(1)) for _ in range(segment_count)]
            current_partition[0] = True
            current_partition[-1] = False
        if budget_boundary == "below" and not any(current_partition):
            current_partition[0] = True

        deltas_by_segment: list[_JournalDeltas] = []
        for segment_index in range(segment_count):
            event_count = (
                2 + rng.randrange(2)
                if segment_index == 0
                else 1 + rng.randrange(3)
            )
            deltas: list[_Delta] = []
            for event_index in range(event_count):
                minimum = 1 if event_index == 0 else 0
                deltas.append(
                    tuple(
                        minimum + rng.randrange(10_000)
                        for _modality in TOKEN_MODALITIES
                    )
                )
            deltas_by_segment.append(tuple(deltas))

        cases.append(
            _GeneratedCase(
                case_index=case_index,
                deltas_by_segment=tuple(deltas_by_segment),
                rendered_in_current_attempt=tuple(current_partition),
                rates=tuple(_generated_rate(rng) for _ in TOKEN_MODALITIES),
                journal_failure=journal_failure,
                provenance_failure=_PROVENANCE_FAILURES[
                    (case_index * 7) % len(_PROVENANCE_FAILURES)
                ],
                budget_boundary=budget_boundary,
                billing_status=billing_statuses[case_index % len(billing_statuses)],
            )
        )
    return tuple(cases)


def _vector(values: tuple[object, object, object, object]) -> dict[str, object]:
    return {
        "input": {
            "speechTokens": values[0],
            "textTokens": values[1],
        },
        "output": {
            "speechTokens": values[2],
            "textTokens": values[3],
        },
    }


def _usage_event(
    delta: tuple[object, object, object, object],
    total: _Delta,
    *,
    identity: str,
) -> dict[str, object]:
    return {
        "usageEvent": {
            "sessionId": f"session-{identity}",
            "promptName": f"prompt-{identity}",
            "completionId": f"completion-{identity}",
            "details": {
                "delta": _vector(delta),
                "total": _vector(total),
            },
            "totalInputTokens": total[0] + total[1],
            "totalOutputTokens": total[2] + total[3],
            "totalTokens": sum(total),
        }
    }


def _jsonl(*events: dict[str, object]) -> bytes:
    return "".join(
        json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
        for event in events
    ).encode("utf-8")


def _journal_bytes(deltas: _JournalDeltas, *, identity: str) -> bytes:
    running = [0, 0, 0, 0]
    events: list[dict[str, object]] = [
        {
            "completionStart": {
                "sessionId": f"session-{identity}",
                "promptName": f"prompt-{identity}",
                "completionId": f"completion-{identity}",
            }
        }
    ]
    for delta in deltas:
        running = [
            current + increment
            for current, increment in zip(running, delta, strict=True)
        ]
        events.append(_usage_event(delta, tuple(running), identity=identity))
    events.append(
        {
            "completionEnd": {
                "sessionId": f"session-{identity}",
                "promptName": f"prompt-{identity}",
                "completionId": f"completion-{identity}",
                "stopReason": "END_TURN",
            }
        }
    )
    return _jsonl(*events)


def _journal_path(audio_path: str) -> str:
    audio = PurePosixPath(audio_path)
    return (audio.parent.parent / "events" / f"{audio.stem}.jsonl").as_posix()


def _write_valid_journals(
    workspace: Path,
    case: _GeneratedCase,
) -> tuple[tuple[ActiveAudioStem, ...], dict[str, bytes]]:
    stems: list[ActiveAudioStem] = []
    raw_by_path: dict[str, bytes] = {}
    for segment_index, (deltas, rendered) in enumerate(
        zip(
            case.deltas_by_segment,
            case.rendered_in_current_attempt,
            strict=True,
        ),
        start=1,
    ):
        stem_name = f"{segment_index:04d}-case-{case.case_index:03d}"
        audio_path = f"runtime/segments/{stem_name}.wav"
        journal_path = _journal_path(audio_path)
        raw = _journal_bytes(
            deltas,
            identity=f"case-{case.case_index:03d}-segment-{segment_index:04d}",
        )
        absolute_path = workspace / journal_path
        absolute_path.parent.mkdir(parents=True, exist_ok=True)
        absolute_path.write_bytes(raw)
        raw_by_path[journal_path] = raw
        stems.append(
            ActiveAudioStem(
                segment_id=f"segment-{segment_index:04d}",
                audio_path=audio_path,
                rendered_in_current_attempt=rendered,
                journal_candidates=(
                    JournalCandidate(journal_path, sha256_bytes(raw)),
                ),
            )
        )
    return tuple(stems), raw_by_path


def _totals_from_case(case: _GeneratedCase, *, current_only: bool) -> UsageTotals:
    selected = tuple(
        deltas
        for deltas, rendered in zip(
            case.deltas_by_segment,
            case.rendered_in_current_attempt,
            strict=True,
        )
        if not current_only or rendered
    )
    values = tuple(
        sum(
            delta[modality_index]
            for journal_deltas in selected
            for delta in journal_deltas
        )
        for modality_index in range(len(TOKEN_MODALITIES))
    )
    return UsageTotals(*values)


def _rate_card(rates: tuple[str, str, str, str]) -> OfficialRateCard:
    return OfficialRateCard(
        model_id=_MODEL_ID,
        region=_REGION,
        purchase_option=_PURCHASE_OPTION,
        currency="USD",
        unit="per-1k-tokens",
        source_url=_RATE_SOURCE_URL,
        offer_publication_date="2026-09-01",
        retrieved_at_utc="2026-09-14T00:00:00Z",
        effective_date="2026-09-01",
        rates=tuple(
            OfficialModalityRate(modality, rate)
            for modality, rate in zip(TOKEN_MODALITIES, rates, strict=True)
        ),
    )


def _exact_cost(
    totals: UsageTotals,
    rates: tuple[str, str, str, str],
) -> tuple[tuple[Decimal, ...], Decimal]:
    with localcontext() as context:
        context.prec = 120
        subtotals = tuple(
            Decimal(getattr(totals, modality)) * Decimal(rate) / Decimal(1000)
            for modality, rate in zip(TOKEN_MODALITIES, rates, strict=True)
        )
        return subtotals, sum(subtotals, start=Decimal("0"))


def _budget_inputs(
    current_cost: Decimal,
    boundary: str,
    case_index: int,
) -> tuple[str, str, BudgetExceptionStatus]:
    if boundary == "below":
        assert current_cost > 0
        approved = current_cost / Decimal(2)
        expected_status = BudgetExceptionStatus.BLOCKING
    elif boundary == "equal":
        approved = current_cost
        expected_status = BudgetExceptionStatus.WITHIN_APPROVED_MAXIMUM
    else:
        assert boundary == "above"
        approved = current_cost + Decimal(case_index + 1).scaleb(-9)
        expected_status = BudgetExceptionStatus.WITHIN_APPROVED_MAXIMUM
    estimate = approved / Decimal(2)
    return _decimal_text(estimate), _decimal_text(approved), expected_status


def _billing_confirmation(
    case: _GeneratedCase,
    current_cost: Decimal,
) -> BillingConfirmation:
    if case.billing_status is BillingStatus.CONFIRMED:
        return BillingConfirmation(
            BillingStatus.CONFIRMED,
            amount_usd=_decimal_text(
                current_cost + Decimal(case.case_index + 1).scaleb(-8)
            ),
            confirmed_at_utc="2026-09-15T00:00:00Z",
        )
    return BillingConfirmation(case.billing_status)


def _assert_cost_scope(
    scope,
    expected_scope: CostScopeName,
    totals: UsageTotals,
    rates: tuple[str, str, str, str],
) -> None:
    expected_subtotals, expected_total = _exact_cost(totals, rates)
    assert scope.scope is expected_scope
    assert scope.token_totals == totals
    assert tuple(line.modality for line in scope.modality_lines) == TOKEN_MODALITIES
    for line, modality, rate, subtotal in zip(
        scope.modality_lines,
        TOKEN_MODALITIES,
        rates,
        expected_subtotals,
        strict=True,
    ):
        tokens = getattr(totals, modality)
        assert line.tokens == tokens
        assert line.rate_per_1k_tokens == rate
        assert line.formula == (
            f'Decimal("{tokens}") * Decimal("{rate}") / Decimal("1000")'
        )
        assert Decimal(line.unrounded_subtotal_usd) == subtotal
    assert Decimal(scope.computed_pre_tax_service_cost_usd) == expected_total


def _rate_card_arguments(
    rates: tuple[str, str, str, str],
) -> dict[str, object]:
    return {
        "model_id": _MODEL_ID,
        "region": _REGION,
        "purchase_option": _PURCHASE_OPTION,
        "currency": "USD",
        "unit": "per-1k-tokens",
        "source_url": _RATE_SOURCE_URL,
        "offer_publication_date": "2026-09-01",
        "retrieved_at_utc": "2026-09-14T00:00:00Z",
        "effective_date": "2026-09-01",
        "rates": tuple(
            OfficialModalityRate(modality, rate)
            for modality, rate in zip(TOKEN_MODALITIES, rates, strict=True)
        ),
    }


def _assert_incomplete_provenance_blocks_exact_cost(
    case: _GeneratedCase,
    aggregation,
    valid_card: OfficialRateCard,
    estimate: str,
    approved: str,
) -> None:
    scenario = case.provenance_failure
    if scenario == "target-mismatch":
        with pytest.raises(InputError, match="provenance does not match"):
            calculate_exact_accounting(
                aggregation,
                valid_card,
                expected_rate_target=OfficialRateTarget(
                    _MODEL_ID,
                    "us-west-2",
                    _PURCHASE_OPTION,
                ),
                cost_estimate_usd=estimate,
                operator_approved_max_estimated_pre_tax_usd=approved,
                calculated_at_utc="2026-09-14T01:00:00Z",
            )
        return

    arguments = _rate_card_arguments(case.rates)
    if scenario == "missing-model":
        arguments["model_id"] = ""
    elif scenario == "missing-region":
        arguments["region"] = ""
    elif scenario == "missing-purchase-option":
        arguments["purchase_option"] = ""
    elif scenario == "wrong-currency":
        arguments["currency"] = ""
    elif scenario == "wrong-unit":
        arguments["unit"] = ""
    elif scenario == "missing-source-url":
        arguments["source_url"] = ""
    elif scenario == "missing-publication-date":
        arguments["offer_publication_date"] = ""
    elif scenario == "missing-retrieval-time":
        arguments["retrieved_at_utc"] = ""
    elif scenario == "missing-effective-date":
        arguments["effective_date"] = ""
    elif scenario == "missing-modality-rate":
        arguments["rates"] = arguments["rates"][:-1]
    elif scenario == "duplicate-modality-rate":
        rates = arguments["rates"]
        arguments["rates"] = (*rates[:-1], rates[0])
    else:
        assert scenario == "nonpositive-rate"
        with pytest.raises(InputError):
            OfficialModalityRate(TOKEN_MODALITIES[0], "0")
        return

    with pytest.raises(InputError):
        OfficialRateCard(**arguments)


def _rewrite_bound_journal(
    workspace: Path,
    stem: ActiveAudioStem,
    raw: bytes,
) -> ActiveAudioStem:
    path = stem.journal_candidates[0].path
    (workspace / path).write_bytes(raw)
    return replace(
        stem,
        journal_candidates=(JournalCandidate(path, sha256_bytes(raw)),),
    )


def _mutate_usage_journal(
    raw: bytes,
    mutation: str,
) -> bytes:
    records = [json.loads(line) for line in raw.decode("utf-8").splitlines()]
    usage_events = [record["usageEvent"] for record in records if "usageEvent" in record]
    assert len(usage_events) >= 2
    if mutation == "noninteger-delta":
        usage_events[0]["details"]["delta"]["input"]["speechTokens"] = True
    elif mutation == "modality-total":
        usage_events[0]["details"]["total"]["output"]["textTokens"] += 1
    elif mutation == "combined-total":
        usage_events[0]["totalTokens"] += 1
    else:
        assert mutation == "mixed-model-call"
        usage_events[1]["completionId"] += "-tampered"
    return _jsonl(*records)


def _assert_journal_failure_blocks(
    workspace: Path,
    case: _GeneratedCase,
    stems: tuple[ActiveAudioStem, ...],
    raw_by_path: dict[str, bytes],
) -> None:
    scenario = case.journal_failure
    first = stems[0]
    candidate = first.journal_candidates[0]
    mutated_stems = stems

    if scenario == "missing-binding":
        mutated_stems = (replace(first, journal_candidates=()), *stems[1:])
    elif scenario == "missing-file":
        (workspace / candidate.path).unlink()
    elif scenario == "duplicate-binding":
        mutated_stems = (
            replace(first, journal_candidates=(candidate, candidate)),
            *stems[1:],
        )
    elif scenario == "ambiguous-binding":
        alternate = JournalCandidate(
            "runtime/events/alternate.jsonl",
            "a" * 64,
        )
        mutated_stems = (
            replace(first, journal_candidates=(candidate, alternate)),
            *stems[1:],
        )
    elif scenario == "unbound-path":
        mutated_stems = (
            replace(
                first,
                journal_candidates=(
                    JournalCandidate("runtime/events/unbound.jsonl", "b" * 64),
                ),
            ),
            *stems[1:],
        )
    elif scenario == "tampered-hash":
        mutated_stems = (
            replace(
                first,
                journal_candidates=(JournalCandidate(candidate.path, "0" * 64),),
            ),
            *stems[1:],
        )
    elif scenario == "tampered-bytes":
        (workspace / candidate.path).write_bytes(raw_by_path[candidate.path] + b"tampered")
    elif scenario == "malformed-json":
        malformed = b'{"usageEvent":\n'
        mutated_stems = (
            _rewrite_bound_journal(workspace, first, malformed),
            *stems[1:],
        )
    elif scenario in {
        "noninteger-delta",
        "modality-total",
        "combined-total",
        "mixed-model-call",
    }:
        raw = _mutate_usage_journal(raw_by_path[candidate.path], scenario)
        mutated_stems = (
            _rewrite_bound_journal(workspace, first, raw),
            *stems[1:],
        )
    else:
        assert scenario == "copied-journal"
        assert len(stems) >= 2
        second = stems[1]
        copied_raw = raw_by_path[candidate.path]
        second = _rewrite_bound_journal(workspace, second, copied_raw)
        mutated_stems = (first, second, *stems[2:])

    with pytest.raises(InputError):
        resolve_and_aggregate_journals(workspace, mutated_stems)


def _partition_name(values: tuple[bool, ...]) -> str:
    if all(values):
        return "all-new"
    if not any(values):
        return "all-reused"
    return "mixed"


# Feature: audiobook-production-workflow, Property 11: Journal aggregation and exact cost are modality-complete
# **Validates: Requirements 4.10, 4.11, 4.13, 11.1-11.14**
def test_property_11_journal_aggregation_and_exact_cost_are_modality_complete(
    tmp_path: Path,
) -> None:
    """Feature: audiobook-production-workflow, Property 11: Journal aggregation and exact cost are modality-complete"""

    assert GENERATED_CASES >= 100
    cases = _generated_cases()
    assert len(cases) == GENERATED_CASES
    print(f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; cases={GENERATED_CASES}")

    observed_journal_failures: set[str] = set()
    observed_provenance_failures: set[str] = set()
    observed_budget_boundaries: set[str] = set()
    observed_partitions: set[str] = set()
    observed_billing_statuses: set[BillingStatus] = set()
    observed_modalities: set[str] = set()

    for case in cases:
        context = (
            f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; case={case.case_index}; "
            f"input={case!r}"
        )
        try:
            workspace = tmp_path / f"case-{case.case_index:03d}"
            stems, raw_by_path = _write_valid_journals(workspace, case)
            aggregation = resolve_and_aggregate_journals(workspace, stems)
            expected_active = _totals_from_case(case, current_only=False)
            expected_current = _totals_from_case(case, current_only=True)

            assert len(aggregation.journals) == len(stems)
            assert tuple(item.segment_id for item in aggregation.journals) == tuple(
                stem.segment_id for stem in stems
            )
            assert tuple(item.usage_event_count for item in aggregation.journals) == tuple(
                len(deltas) for deltas in case.deltas_by_segment
            )
            assert tuple(item.rendered_in_current_attempt for item in aggregation.journals) == (
                case.rendered_in_current_attempt
            )
            assert aggregation.active_artifact_totals == expected_active
            assert aggregation.current_execution_totals == expected_current
            assert aggregation.journals[0].usage_event_count >= 2

            card = _rate_card(case.rates)
            assert card.target == OfficialRateTarget(
                _MODEL_ID,
                _REGION,
                _PURCHASE_OPTION,
            )
            assert tuple(item.modality for item in card.rates) == TOKEN_MODALITIES
            assert tuple(item.rate_per_1k_tokens for item in card.rates) == case.rates
            assert card.currency == "USD"
            assert card.unit == "per-1k-tokens"
            assert card.source_url == _RATE_SOURCE_URL
            assert card.offer_publication_date == "2026-09-01"
            assert card.retrieved_at_utc == "2026-09-14T00:00:00Z"
            assert card.effective_date == "2026-09-01"

            _, current_cost = _exact_cost(expected_current, case.rates)
            estimate, approved, expected_budget_status = _budget_inputs(
                current_cost,
                case.budget_boundary,
                case.case_index,
            )
            billing = _billing_confirmation(case, current_cost)
            result = calculate_exact_accounting(
                aggregation,
                card,
                expected_rate_target=card.target,
                cost_estimate_usd=estimate,
                operator_approved_max_estimated_pre_tax_usd=approved,
                calculated_at_utc="2026-09-14T01:00:00Z",
                billing_confirmation=billing,
            )

            assert result.journal_aggregation is aggregation
            assert result.official_rate_card is card
            assert result.cost_estimate_usd == estimate
            assert result.operator_approved_max_estimated_pre_tax_usd == approved
            _assert_cost_scope(
                result.active_artifact_cost,
                CostScopeName.ACTIVE_ARTIFACT,
                expected_active,
                case.rates,
            )
            _assert_cost_scope(
                result.current_execution_cost,
                CostScopeName.CURRENT_EXECUTION,
                expected_current,
                case.rates,
            )
            assert result.billing_confirmation == billing
            assert result.budget_exception_status is expected_budget_status
            if billing.status is BillingStatus.CONFIRMED:
                assert billing.amount_usd is not None
                assert Decimal(billing.amount_usd) != current_cost
                assert billing.confirmed_at_utc == "2026-09-15T00:00:00Z"
            else:
                assert billing.amount_usd is None
                assert billing.confirmed_at_utc is None

            _assert_incomplete_provenance_blocks_exact_cost(
                case,
                aggregation,
                card,
                estimate,
                approved,
            )
            _assert_journal_failure_blocks(
                workspace,
                case,
                stems,
                raw_by_path,
            )

            observed_journal_failures.add(case.journal_failure)
            observed_provenance_failures.add(case.provenance_failure)
            observed_budget_boundaries.add(case.budget_boundary)
            observed_partitions.add(_partition_name(case.rendered_in_current_attempt))
            observed_billing_statuses.add(case.billing_status)
            observed_modalities.update(
                line.modality for line in result.active_artifact_cost.modality_lines
            )
        except Exception as exc:
            exc.add_note(context)
            raise

    assert observed_journal_failures == set(_JOURNAL_FAILURES)
    assert observed_provenance_failures == set(_PROVENANCE_FAILURES)
    assert observed_budget_boundaries == set(_BUDGET_BOUNDARIES)
    assert observed_partitions == {"all-new", "all-reused", "mixed"}
    assert observed_billing_statuses == set(BillingStatus)
    assert observed_modalities == set(TOKEN_MODALITIES)
