from __future__ import annotations

import json
import socket
from decimal import Decimal
from pathlib import Path, PurePosixPath

import pytest

from frontier_audiobook import narrate
from frontier_audiobook.errors import InputError
from frontier_audiobook.production_accounting import (
    ActiveAudioStem,
    BillingConfirmation,
    BudgetExceptionStatus,
    CostScopeName,
    JournalAggregation,
    JournalCandidate,
    ResolvedJournalUsage,
    calculate_exact_accounting,
    parse_event_journal_usage,
    resolve_and_aggregate_journals,
)
from frontier_audiobook.production_models import BillingStatus, TOKEN_MODALITIES, UsageTotals
from frontier_audiobook.production_preflight import (
    OfficialModalityRate,
    OfficialRateCard,
    OfficialRateTarget,
)
from frontier_audiobook.util import sha256_bytes

MODEL_ID = "amazon.nova-2-sonic-v1:0"
REGION = "us-east-1"
PURCHASE_OPTION = "on-demand"
RATE_SOURCE_URL = "https://aws.amazon.com/bedrock/pricing/"


@pytest.fixture(autouse=True)
def deny_external_access_and_render(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*_args, **_kwargs):
        raise AssertionError("Task 6.4 accounting tests must remain local and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")


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
    total: tuple[int, int, int, int],
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
        json.dumps(event, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for event in events
    ).encode("utf-8")


def _journal_bytes(
    deltas: tuple[tuple[int, int, int, int], ...],
    *,
    identity: str,
) -> bytes:
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
        running = [current + increment for current, increment in zip(running, delta, strict=True)]
        events.append(
            _usage_event(
                delta,
                tuple(running),
                identity=identity,
            )
        )
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


def _write_active_journal(
    workspace: Path,
    *,
    segment_id: str,
    stem_name: str,
    deltas: tuple[tuple[int, int, int, int], ...],
    rendered_in_current_attempt: bool,
    journal_identity: str | None = None,
) -> ActiveAudioStem:
    audio_path = (
        ".audiobook/build/production/the-final-frontier/transactions/track/transaction/"
        f"runtime/segments/{stem_name}.wav"
    )
    journal_path = _journal_path(audio_path)
    raw = _journal_bytes(deltas, identity=journal_identity or segment_id)
    absolute_journal = workspace / journal_path
    absolute_journal.parent.mkdir(parents=True, exist_ok=True)
    absolute_journal.write_bytes(raw)
    return ActiveAudioStem(
        segment_id=segment_id,
        audio_path=audio_path,
        rendered_in_current_attempt=rendered_in_current_attempt,
        journal_candidates=(JournalCandidate(journal_path, sha256_bytes(raw)),),
    )


def _rate_target(*, region: str = REGION) -> OfficialRateTarget:
    return OfficialRateTarget(MODEL_ID, region, PURCHASE_OPTION)


def _rate_card(
    rates: tuple[str, str, str, str] = ("0.1", "0.2", "0.3", "0.4"),
) -> OfficialRateCard:
    return OfficialRateCard(
        model_id=MODEL_ID,
        region=REGION,
        purchase_option=PURCHASE_OPTION,
        currency="USD",
        unit="per-1k-tokens",
        source_url=RATE_SOURCE_URL,
        offer_publication_date="2026-09-01",
        retrieved_at_utc="2026-09-14T00:00:00Z",
        effective_date="2026-09-01",
        rates=tuple(
            OfficialModalityRate(modality, rate)
            for modality, rate in zip(TOKEN_MODALITIES, rates, strict=True)
        ),
    )


def _sample_aggregation(workspace: Path) -> JournalAggregation:
    current = _write_active_journal(
        workspace,
        segment_id="segment-0001",
        stem_name="0001-current",
        deltas=((1, 2, 3, 4), (5, 6, 7, 8)),
        rendered_in_current_attempt=True,
    )
    reused = _write_active_journal(
        workspace,
        segment_id="segment-0002",
        stem_name="0002-reused",
        deltas=((10, 20, 30, 40),),
        rendered_in_current_attempt=False,
    )
    return resolve_and_aggregate_journals(workspace, (current, reused))


def test_aggregates_each_active_journal_once_and_calculates_two_exact_scopes(
    tmp_path: Path,
) -> None:
    aggregation = _sample_aggregation(tmp_path)

    assert tuple(item.usage_event_count for item in aggregation.journals) == (2, 1)
    assert aggregation.active_artifact_totals == UsageTotals(16, 28, 40, 52)
    assert aggregation.current_execution_totals == UsageTotals(6, 8, 10, 12)

    card = _rate_card()
    result = calculate_exact_accounting(
        aggregation,
        card,
        expected_rate_target=_rate_target(),
        cost_estimate_usd="0.02",
        operator_approved_max_estimated_pre_tax_usd="0.02",
        calculated_at_utc="2026-09-14T01:00:00Z",
    )

    assert result.cost_estimate_usd == "0.02"
    assert result.active_artifact_cost.scope is CostScopeName.ACTIVE_ARTIFACT
    assert result.current_execution_cost.scope is CostScopeName.CURRENT_EXECUTION
    assert result.active_artifact_cost.computed_pre_tax_service_cost_usd == "0.04"
    assert result.current_execution_cost.computed_pre_tax_service_cost_usd == "0.01"
    assert result.active_artifact_cost.modality_lines[0].formula == (
        'Decimal("16") * Decimal("0.1") / Decimal("1000")'
    )
    assert tuple(line.tokens for line in result.current_execution_cost.modality_lines) == (
        6,
        8,
        10,
        12,
    )
    assert result.official_rate_card is card
    assert result.official_rate_card.source_url == RATE_SOURCE_URL
    assert result.billing_confirmation == BillingConfirmation(BillingStatus.PENDING)
    assert result.budget_exception_status is BudgetExceptionStatus.WITHIN_APPROVED_MAXIMUM


def test_estimate_exact_cost_billing_and_budget_exception_remain_distinct(tmp_path: Path) -> None:
    billing = BillingConfirmation(
        BillingStatus.CONFIRMED,
        amount_usd="0.009",
        confirmed_at_utc="2026-09-15T00:00:00Z",
    )
    result = calculate_exact_accounting(
        _sample_aggregation(tmp_path),
        _rate_card(),
        expected_rate_target=_rate_target(),
        cost_estimate_usd="0.005",
        operator_approved_max_estimated_pre_tax_usd="0.005",
        calculated_at_utc="2026-09-14T01:00:00Z",
        billing_confirmation=billing,
    )

    assert result.cost_estimate_usd == "0.005"
    assert result.current_execution_cost.computed_pre_tax_service_cost_usd == "0.01"
    assert result.billing_confirmation.amount_usd == "0.009"
    assert result.budget_exception_status is BudgetExceptionStatus.BLOCKING


def test_resolution_rejects_missing_duplicate_ambiguous_unbound_and_tampered_evidence(
    tmp_path: Path,
) -> None:
    valid = _write_active_journal(
        tmp_path,
        segment_id="segment-0001",
        stem_name="0001-valid",
        deltas=((1, 2, 3, 4),),
        rendered_in_current_attempt=True,
    )
    candidate = valid.journal_candidates[0]

    with pytest.raises(InputError, match="expected_sha256"):
        JournalCandidate(candidate.path, None)  # type: ignore[arg-type]

    with pytest.raises(InputError, match="Missing Event_Journal"):
        resolve_and_aggregate_journals(
            tmp_path,
            (
                ActiveAudioStem(
                    "segment-missing-binding",
                    valid.audio_path,
                    True,
                    (),
                ),
            ),
        )

    with pytest.raises(InputError, match="Duplicate Event_Journal"):
        resolve_and_aggregate_journals(
            tmp_path,
            (
                ActiveAudioStem(
                    "segment-duplicate",
                    valid.audio_path,
                    True,
                    (candidate, candidate),
                ),
            ),
        )

    alternate = JournalCandidate(
        candidate.path.replace("0001-valid", "alternate"),
        "1" * 64,
    )
    with pytest.raises(InputError, match="Ambiguous Event_Journal"):
        resolve_and_aggregate_journals(
            tmp_path,
            (
                ActiveAudioStem(
                    "segment-ambiguous",
                    valid.audio_path,
                    True,
                    (candidate, alternate),
                ),
            ),
        )

    missing_audio = valid.audio_path.replace("0001-valid", "0002-missing")
    with pytest.raises(InputError, match="Missing Event_Journal"):
        resolve_and_aggregate_journals(
            tmp_path,
            (
                ActiveAudioStem(
                    "segment-missing-file",
                    missing_audio,
                    True,
                    (JournalCandidate(_journal_path(missing_audio), "2" * 64),),
                ),
            ),
        )

    with pytest.raises(InputError, match="Tampered Event_Journal"):
        resolve_and_aggregate_journals(
            tmp_path,
            (
                ActiveAudioStem(
                    "segment-tampered",
                    valid.audio_path,
                    True,
                    (JournalCandidate(candidate.path, "0" * 64),),
                ),
            ),
        )


def test_resolution_rejects_copied_journal_content_before_double_counting(tmp_path: Path) -> None:
    first = _write_active_journal(
        tmp_path,
        segment_id="segment-0001",
        stem_name="0001-copy",
        deltas=((1, 2, 3, 4),),
        rendered_in_current_attempt=True,
        journal_identity="copied-call",
    )
    second = _write_active_journal(
        tmp_path,
        segment_id="segment-0002",
        stem_name="0002-copy",
        deltas=((1, 2, 3, 4),),
        rendered_in_current_attempt=True,
        journal_identity="copied-call",
    )

    with pytest.raises(InputError, match="duplicate Event_Journal SHA-256 digests"):
        resolve_and_aggregate_journals(tmp_path, (first, second))


@pytest.mark.parametrize(
    ("raw", "message"),
    (
        (b'{"usageEvent":\n', "Malformed JSON"),
        (_jsonl({"completionStart": {}}), "contains no usageEvent"),
        (
            _jsonl(_usage_event((True, 2, 3, 4), (1, 2, 3, 4), identity="bool")),
            "must be a nonnegative integer",
        ),
        (
            _jsonl(_usage_event((1, 2, 3, 4), (1, 99, 3, 4), identity="modality")),
            "terminal modality totals do not reconcile",
        ),
        (
            _jsonl(
                {
                    "usageEvent": {
                        **_usage_event(
                            (1, 2, 3, 4),
                            (1, 2, 3, 4),
                            identity="combined",
                        )["usageEvent"],
                        "totalTokens": 999,
                    }
                }
            ),
            "combined terminal totals do not reconcile",
        ),
        (
            _jsonl(
                _usage_event((1, 1, 1, 1), (1, 1, 1, 1), identity="first"),
                _usage_event((1, 1, 1, 1), (2, 2, 2, 2), identity="second"),
            ),
            "different model calls",
        ),
    ),
)
def test_journal_parser_rejects_malformed_or_inconsistent_usage(
    raw: bytes,
    message: str,
) -> None:
    with pytest.raises(InputError, match=message):
        parse_event_journal_usage(raw)


def test_decimal_cost_sum_preserves_subtotals_across_distant_scales() -> None:
    totals = UsageTotals(1, 1, 0, 0)
    resolved = ResolvedJournalUsage(
        segment_id="segment-0001",
        audio_path="runtime/segments/0001.wav",
        journal_path="runtime/events/0001.jsonl",
        journal_sha256="a" * 64,
        rendered_in_current_attempt=True,
        usage_event_count=1,
        totals=totals,
    )
    aggregation = JournalAggregation((resolved,), totals, totals)
    tiny_rate = "0." + ("0" * 29) + "1"

    result = calculate_exact_accounting(
        aggregation,
        _rate_card(("1", tiny_rate, "0.1", "0.1")),
        expected_rate_target=_rate_target(),
        cost_estimate_usd="0",
        operator_approved_max_estimated_pre_tax_usd="1",
        calculated_at_utc="2026-09-14T01:00:00Z",
    )

    expected = Decimal((0, (1,) + ((0,) * 29) + (1,), -33))
    assert result.current_execution_cost.computed_pre_tax_service_cost_usd == format(
        expected,
        "f",
    )


def test_exact_accounting_rejects_rate_provenance_for_another_target(tmp_path: Path) -> None:
    with pytest.raises(InputError, match="does not match the rendered model/region/option"):
        calculate_exact_accounting(
            _sample_aggregation(tmp_path),
            _rate_card(),
            expected_rate_target=_rate_target(region="us-west-2"),
            cost_estimate_usd="0.02",
            operator_approved_max_estimated_pre_tax_usd="0.02",
            calculated_at_utc="2026-09-14T01:00:00Z",
        )
