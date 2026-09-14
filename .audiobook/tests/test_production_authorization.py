from __future__ import annotations

import json
import socket
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from frontier_audiobook import narrate
from frontier_audiobook.errors import InputError
from frontier_audiobook.production import (
    ProductionSelectors,
    create_production_plan,
    load_production_plan,
)
from frontier_audiobook.production_authorization import (
    AUTHORIZATION_CONFIRMATION_PROMPT,
    AuthorizationDecision,
    AuthorizationDisplay,
    AuthorizationStartRequest,
    ExactAuthorizationConfirmation,
    build_authorization_start_request,
    create_paid_authorization,
    create_paid_authorization_file,
    load_paid_authorization,
    validate_paid_authorization_start,
    write_paid_authorization,
)
from frontier_audiobook.production_config import (
    build_ordered_track_catalog,
    parse_production_toml,
)
from frontier_audiobook.production_models import (
    PaidAuthorization,
    StrictRecordCodec,
    TOKEN_MODALITIES,
    TransactionState,
    authorization_confirmation_sha256,
    canonical_sha256,
    seal_record,
)
from frontier_audiobook.production_preflight import (
    bind_targeted_check_result,
    run_bounded_identity_rate_preflight,
    run_local_preflight,
)
from frontier_audiobook.production_transactions import TransactionStore
from frontier_audiobook.util import read_bytes_nofollow, sha256_bytes, workspace_relative


_SENTENCES = (
    "Alpha one two three four.",
    "Bravo one two three four.",
    "Charlie one two three four.",
)


class _Clock:
    def __init__(self, *values: str):
        self._values = [
            datetime.fromisoformat(value.removesuffix("Z") + "+00:00").astimezone(UTC)
            for value in values
        ]

    def __call__(self) -> datetime:
        if not self._values:
            raise AssertionError("authorization clock was called more often than expected")
        return self._values.pop(0)


@pytest.fixture(autouse=True)
def deny_external_access_and_render(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("authorization tests must remain local and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")


def _write_chapter(workspace: Path, chapter: int) -> None:
    path = (
        workspace
        / "The Final Frontier Novel"
        / "chapters"
        / "discovery-part"
        / f"discovery-part-{chapter:03d}-authorization-fixture.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    body = " ".join(_SENTENCES)
    path.write_text(
        "\n".join(
            (
                "---",
                "movement: discovery",
                f"chapter: {chapter}",
                "pov_id: test-pov",
                "timeline_id: test-timeline",
                "motif_events: none",
                "hook: authorization-test",
                f"words: {len(body.split())}",
                "length_class: short",
                "status: draft",
                "---",
                body,
                "",
            )
        ),
        encoding="utf-8",
    )


def _write_config(workspace: Path) -> Path:
    path = workspace / ".audiobook" / "config" / "production.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '''schema_version = 1
book_id = "the-final-frontier"
manuscript_root = "The Final Frontier Novel"
build_root = ".audiobook/build/production"
delivery_root = ".audiobook/dist/audiobook"
max_tracks_per_plan = 16
tracks = []

[defaults]
voice = "tiffany"
model_id = "amazon.nova-2-sonic-v1:0"
region = "us-east-1"
profile_label = "frontier-audiobook"
target_segment_words = 5
fidelity_policy = "exact"
normalization = "frontier-word-sequence-v1"
output_template = "{sequence:03d}-{track_slug}-{voice}.wav"

[defaults.audio]
sample_rate_hz = 24000
sample_size_bits = 16
channels = 1

[estimate]
rate_max_age_hours = 24
preflight_max_age_hours = 24
input_speech_tokens_per_call = 0
input_text_tokens_per_call = 8192
output_speech_tokens_per_call = 8192
output_text_tokens_per_call = 8192
''',
        encoding="utf-8",
    )
    return path


def _official_rate_document() -> str:
    rates = {
        "input_speech": "0.001",
        "input_text": "0.002",
        "output_speech": "0.003",
        "output_text": "0.004",
    }
    return json.dumps(
        {
            "schema_version": 1,
            "source_url": "https://aws.amazon.com/bedrock/pricing/",
            "offer_publication_date": "2026-09-14",
            "retrieved_at_utc": "2026-09-14T11:00:00Z",
            "effective_date": "2026-09-14",
            "offers": [
                {
                    "model_id": "amazon.nova-2-sonic-v1:0",
                    "region": "us-east-1",
                    "purchase_option": "on-demand",
                    "currency": "USD",
                    "unit": "per-1k-tokens",
                    "modality": modality,
                    "rate_per_1k_tokens": rate,
                }
                for modality, rate in rates.items()
            ],
        },
        separators=(",", ":"),
    )


def _store(workspace: Path, config) -> TransactionStore:
    return TransactionStore(
        workspace / config.build_root / config.book_id,
        config.book_id,
    )


def _authorization_inputs(workspace: Path, chapters: tuple[int, ...]):
    for chapter in chapters:
        _write_chapter(workspace, chapter)
    config_path = _write_config(workspace)
    plan_path = create_production_plan(
        config_path,
        ProductionSelectors.from_cli(chapters=chapters),
        plan_id="authorization-test-plan",
        workspace_root=workspace,
        created_at_utc="2026-09-14T10:00:00Z",
    )
    plan = load_production_plan(plan_path)
    config = parse_production_toml(read_bytes_nofollow(config_path), label=str(config_path))
    catalog = build_ordered_track_catalog(config, workspace)

    targeted_path = workspace / ".audiobook" / "build" / "targeted" / "authorization.json"
    targeted_path.parent.mkdir(parents=True, exist_ok=True)
    targeted_path.write_text('{"passed":true,"external_access":false}', encoding="utf-8")
    targeted = bind_targeted_check_result(
        workspace,
        workspace_relative(workspace, targeted_path),
        command_sha256=sha256_bytes(b"pytest tests/test_production_authorization.py"),
        return_code=0,
        aws_access_disabled=True,
        model_access_disabled=True,
    )
    local = run_local_preflight(
        workspace,
        config,
        catalog,
        plan,
        targeted,
        required_free_bytes=0,
        git_statuses={},
    )
    bounded = run_bounded_identity_rate_preflight(
        config,
        plan,
        local,
        identity_call=lambda profile: {"resolved_profile": profile},
        official_rate_document=_official_rate_document(),
        checked_at_utc="2026-09-14T12:00:00Z",
    )
    assert local.passed and bounded.passed

    store = _store(workspace, config)
    store.materialize_plan(plan, occurred_at_utc="2026-09-14T10:00:00Z")
    for track in plan.tracks:
        store.append_transition(
            track.track_id,
            track.transaction_id,
            operation_id="preflight-passed",
            event_type="preflight-passed",
            state_after=TransactionState.PREFLIGHT_PASSED,
            details={"preflight_sha256": bounded.canonical_sha256},
            occurred_at_utc="2026-09-14T12:00:01Z",
        )
        store.append_transition(
            track.track_id,
            track.transaction_id,
            operation_id="authorization-required",
            event_type="authorization-required",
            state_after=TransactionState.AUTHORIZATION_REQUIRED,
            details={"preflight_sha256": bounded.canonical_sha256},
            occurred_at_utc="2026-09-14T12:00:02Z",
        )
    return config, plan, local, bounded


def _approved_maximum(bounded) -> str:
    return format(Decimal(bounded.estimate.estimated_pre_tax_usd) + Decimal("1"), "f")


def _exact_provider(captured: list[object]):
    def provider(display: AuthorizationDisplay):
        confirmation = ExactAuthorizationConfirmation(
            schema_version=1,
            display_sha256=display.canonical_sha256,
            challenge=display.confirmation_challenge,
            decision=AuthorizationDecision.AUTHORIZE_EXACT_SCOPE,
        )
        captured.extend((display, confirmation))
        return confirmation

    return provider


def _create_authorization(workspace: Path, chapters: tuple[int, ...] = (1,)):
    config, plan, local, bounded = _authorization_inputs(workspace, chapters)
    captured: list[object] = []
    authorization = create_paid_authorization(
        config,
        plan,
        local,
        bounded,
        workspace_root=workspace,
        authorization_id="authorization-local-fixture",
        operator_approved_max_estimated_pre_tax_usd=_approved_maximum(bounded),
        expires_at_utc="2026-09-14T13:00:00Z",
        confirmation_provider=_exact_provider(captured),
        clock=_Clock("2026-09-14T12:01:00Z", "2026-09-14T12:02:00Z"),
    )
    return config, plan, local, bounded, authorization, captured


@pytest.mark.parametrize("chapters", ((1,), (1, 2)))
def test_exact_single_or_batch_confirmation_creates_one_canonical_bound_artifact(
    tmp_path,
    chapters,
):
    config, plan, local, bounded, authorization, captured = _create_authorization(
        tmp_path,
        chapters,
    )
    display, confirmation = captured
    assert isinstance(display, AuthorizationDisplay)
    assert isinstance(confirmation, ExactAuthorizationConfirmation)
    assert display.confirmation_prompt == AUTHORIZATION_CONFIRMATION_PROMPT
    assert display.exact_track_ids == tuple(track.track_id for track in plan.tracks)
    assert display.exact_transaction_ids == tuple(track.transaction_id for track in plan.tracks)
    assert display.exact_command_sha256s == tuple(track.command_sha256 for track in plan.tracks)
    assert display.maximum_new_calls_by_track == local.maximum_new_calls_by_track
    assert display.local_preflight_sha256 == local.canonical_sha256
    assert display.preflight_sha256 == bounded.canonical_sha256
    assert display.estimate_sha256 == bounded.estimate.canonical_sha256
    assert display.official_rate_provenance_sha256 == canonical_sha256(
        bounded.official_rate_cards
    )
    assert tuple(item.modality for item in bounded.official_rate_cards[0].rates) == TOKEN_MODALITIES

    assert authorization.plan_sha256 == StrictRecordCodec(type(plan)).sha256(plan)
    assert authorization.preflight_sha256 == bounded.canonical_sha256
    assert authorization.local_preflight_sha256 == local.canonical_sha256
    assert authorization.estimate_sha256 == bounded.estimate.canonical_sha256
    assert authorization.exact_track_ids == display.exact_track_ids
    assert dict(authorization.maximum_new_calls_by_track) == dict(
        local.maximum_new_calls_by_track
    )
    assert authorization.maximum_new_calls_total == local.maximum_new_calls_total
    assert authorization.estimated_pre_tax_usd == bounded.estimate.estimated_pre_tax_usd
    assert authorization.one_shot is True
    assert authorization.confirmation_challenge == display.confirmation_challenge
    assert authorization.confirmation_display_sha256 == display.canonical_sha256
    assert authorization.confirmation_sha256 == authorization_confirmation_sha256(
        display_sha256=display.canonical_sha256,
        challenge=display.confirmation_challenge,
        decision=AuthorizationDecision.AUTHORIZE_EXACT_SCOPE,
        confirmed_at_utc="2026-09-14T12:02:00Z",
    )

    display_codec = StrictRecordCodec(AuthorizationDisplay)
    authorization_codec = StrictRecordCodec(PaidAuthorization)
    assert display_codec.loads(display_codec.dump_bytes(display)) == display
    assert authorization_codec.loads(authorization_codec.dump_bytes(authorization)) == authorization

    path = tmp_path / ".audiobook" / "build" / "authorizations" / "authorization.json"
    assert write_paid_authorization(path, authorization) == path
    before = path.read_bytes()
    assert write_paid_authorization(path, authorization) == path
    assert path.read_bytes() == before
    assert load_paid_authorization(path) == authorization

    collision = seal_record(
        replace(
            authorization,
            authorization_id="authorization-collision",
            canonical_sha256="",
        )
    )
    with pytest.raises(InputError, match="different canonical bytes"):
        write_paid_authorization(path, collision)
    assert path.read_bytes() == before


def test_generic_or_replayed_approval_cannot_create_authorization(tmp_path):
    config, plan, local, bounded = _authorization_inputs(tmp_path, (1,))
    path = tmp_path / "authorizations" / "authorization.json"
    arguments = dict(
        workspace_root=tmp_path,
        authorization_id="authorization-generic-rejected",
        operator_approved_max_estimated_pre_tax_usd=_approved_maximum(bounded),
        expires_at_utc="2026-09-14T13:00:00Z",
    )
    for response in (
        True,
        "yes",
        "spec-approved",
        "task-4-1-complete",
        {"approved": True},
        None,
    ):
        with pytest.raises(InputError, match="generic approval is insufficient"):
            create_paid_authorization_file(
                path,
                config,
                plan,
                local,
                bounded,
                **arguments,
                confirmation_provider=lambda _display, value=response: value,
                clock=_Clock("2026-09-14T12:01:00Z"),
            )
        assert not path.exists()

    with pytest.raises(InputError, match="declined"):
        create_paid_authorization_file(
            path,
            config,
            plan,
            local,
            bounded,
            **arguments,
            confirmation_provider=lambda display: ExactAuthorizationConfirmation(
                1,
                display.canonical_sha256,
                display.confirmation_challenge,
                AuthorizationDecision.DECLINE,
            ),
            clock=_Clock("2026-09-14T12:01:00Z"),
        )

    captured: list[object] = []
    create_paid_authorization(
        config,
        plan,
        local,
        bounded,
        **arguments,
        confirmation_provider=_exact_provider(captured),
        clock=_Clock("2026-09-14T12:01:00Z", "2026-09-14T12:02:00Z"),
    )
    old_confirmation = captured[1]
    with pytest.raises(InputError, match="exact displayed|stale"):
        create_paid_authorization(
            config,
            plan,
            local,
            bounded,
            **arguments,
            confirmation_provider=lambda _display: old_confirmation,
            clock=_Clock("2026-09-14T12:03:00Z"),
        )
    assert not path.exists()


def test_creation_uses_trusted_clock_and_rejects_invalid_scope_before_confirmation(tmp_path):
    config, plan, local, bounded = _authorization_inputs(tmp_path, (1,))
    calls = 0

    def must_not_confirm(_display):
        nonlocal calls
        calls += 1
        raise AssertionError("invalid scope must fail before confirmation")

    common = dict(
        workspace_root=tmp_path,
        authorization_id="authorization-invalid",
        operator_approved_max_estimated_pre_tax_usd=_approved_maximum(bounded),
        expires_at_utc="2026-09-14T13:00:00Z",
        confirmation_provider=must_not_confirm,
    )
    with pytest.raises(InputError, match="lower than"):
        create_paid_authorization(
            config,
            plan,
            local,
            bounded,
            **{**common, "operator_approved_max_estimated_pre_tax_usd": "0"},
            clock=_Clock("2026-09-14T12:01:00Z"),
        )
    with pytest.raises(InputError, match="stale"):
        create_paid_authorization(
            config,
            plan,
            local,
            bounded,
            **{**common, "expires_at_utc": "2026-09-15T13:00:00Z"},
            clock=_Clock("2026-09-15T12:00:01Z"),
        )
    with pytest.raises(InputError, match="freshness window"):
        create_paid_authorization(
            config,
            plan,
            local,
            bounded,
            **{**common, "expires_at_utc": "2026-09-15T12:00:01Z"},
            clock=_Clock("2026-09-14T12:01:00Z"),
        )

    mismatched = seal_record(
        replace(
            bounded,
            local_preflight_sha256="f" * 64,
            canonical_sha256="",
        )
    )
    with pytest.raises(InputError, match="not bound to Task 2.1"):
        create_paid_authorization(
            config,
            plan,
            local,
            mismatched,
            **common,
            clock=_Clock("2026-09-14T12:01:00Z"),
        )
    assert calls == 0


def test_start_validation_rejects_altered_unlisted_and_unverifiable_evidence(tmp_path):
    config, plan, local, bounded, authorization, _captured = _create_authorization(
        tmp_path,
        (1, 2),
    )
    request = build_authorization_start_request(authorization)
    assert (
        validate_paid_authorization_start(
            authorization,
            config,
            plan,
            local,
            bounded,
            request,
            workspace_root=tmp_path,
            clock=_Clock("2026-09-14T12:03:00Z"),
        )
        == authorization
    )

    first_track, first_calls = request.maximum_new_calls_by_track[0]
    changed_calls = (
        (first_track, first_calls + 1),
        *request.maximum_new_calls_by_track[1:],
    )
    expanded_calls = replace(
        request,
        maximum_new_calls_by_track=changed_calls,
        maximum_new_calls_total=request.maximum_new_calls_total + 1,
    )
    with pytest.raises(InputError, match="altered, incomplete, or unlisted"):
        validate_paid_authorization_start(
            authorization,
            config,
            plan,
            local,
            bounded,
            expanded_calls,
            workspace_root=tmp_path,
            clock=_Clock("2026-09-14T12:03:00Z"),
        )

    unlisted_track = "chapter-999"
    unlisted = AuthorizationStartRequest(
        authorization_sha256=request.authorization_sha256,
        plan_sha256=request.plan_sha256,
        preflight_sha256=request.preflight_sha256,
        exact_transaction_ids=(*request.exact_transaction_ids, "transaction-999"),
        exact_track_ids=(*request.exact_track_ids, unlisted_track),
        exact_command_sha256s=(*request.exact_command_sha256s, "f" * 64),
        maximum_new_calls_by_track=(
            *request.maximum_new_calls_by_track,
            (unlisted_track, 1),
        ),
        maximum_new_calls_total=request.maximum_new_calls_total + 1,
    )
    with pytest.raises(InputError, match="altered, incomplete, or unlisted"):
        validate_paid_authorization_start(
            authorization,
            config,
            plan,
            local,
            bounded,
            unlisted,
            workspace_root=tmp_path,
            clock=_Clock("2026-09-14T12:03:00Z"),
        )

    forged_display = "e" * 64
    forged = seal_record(
        replace(
            authorization,
            confirmation_display_sha256=forged_display,
            confirmation_sha256=authorization_confirmation_sha256(
                display_sha256=forged_display,
                challenge=authorization.confirmation_challenge,
                decision=authorization.confirmation_decision,
                confirmed_at_utc=authorization.confirmed_at_utc,
            ),
            canonical_sha256="",
        )
    )
    forged_request = build_authorization_start_request(forged)
    with pytest.raises(InputError, match="display/confirmation chain"):
        validate_paid_authorization_start(
            forged,
            config,
            plan,
            local,
            bounded,
            forged_request,
            workspace_root=tmp_path,
            clock=_Clock("2026-09-14T12:03:00Z"),
        )

    with pytest.raises(InputError, match="expired"):
        validate_paid_authorization_start(
            authorization,
            config,
            plan,
            local,
            bounded,
            request,
            workspace_root=tmp_path,
            clock=_Clock("2026-09-14T13:00:00Z"),
        )


def test_ledger_truth_rejects_consumed_retry_and_old_batch_authorization(tmp_path):
    config, plan, local, bounded, authorization, _captured = _create_authorization(
        tmp_path,
        (1, 2),
    )
    request = build_authorization_start_request(authorization)
    store = _store(tmp_path, config)
    first = plan.tracks[0]
    store.append_transition(
        first.track_id,
        first.transaction_id,
        operation_id="authorization-consumed",
        event_type="authorization-consumed",
        state_after=TransactionState.RUNNING,
        details={
            "authorization_sha256": StrictRecordCodec(PaidAuthorization).sha256(
                authorization
            )
        },
        occurred_at_utc="2026-09-14T12:03:00Z",
    )

    with pytest.raises(InputError, match="already been consumed"):
        validate_paid_authorization_start(
            authorization,
            config,
            plan,
            local,
            bounded,
            build_authorization_start_request(authorization),
            workspace_root=tmp_path,
            clock=_Clock("2026-09-14T12:04:00Z"),
        )

    store.append_transition(
        first.track_id,
        first.transaction_id,
        operation_id="batch-stopped",
        event_type="batch-stopped",
        state_after=TransactionState.BLOCKED,
        details={"authorization_sha256": request.authorization_sha256},
        occurred_at_utc="2026-09-14T12:05:00Z",
    )
    for message in ("fresh preflight", "fresh preflight"):
        with pytest.raises(InputError, match=message):
            validate_paid_authorization_start(
                authorization,
                config,
                plan,
                local,
                bounded,
                build_authorization_start_request(authorization),
                workspace_root=tmp_path,
                clock=_Clock("2026-09-14T12:06:00Z"),
            )
