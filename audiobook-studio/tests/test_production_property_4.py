"""Deterministic generated checks for production correctness Property 4."""

from __future__ import annotations

import io
import json
import random
import shutil
import socket
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

import frontier_audiobook.production_attempt as attempt_module
from frontier_audiobook import narrate
from frontier_audiobook.errors import InputError
from frontier_audiobook.production import ProductionSelectors, create_production_plan, load_production_plan
from frontier_audiobook.production_attempt import run_atomic_paid_attempt
from frontier_audiobook.production_authorization import (
    AuthorizationDisplay,
    AuthorizationStartRequest,
    ExactAuthorizationConfirmation,
    build_authorization_start_request,
    create_paid_authorization,
    validate_paid_authorization_start,
)
from frontier_audiobook.production_config import (
    BookProductionConfig,
    build_ordered_track_catalog,
    parse_production_toml,
)
from frontier_audiobook.production_models import (
    AuthorizationDecision,
    FrozenBatchPlan,
    PaidAuthorization,
    StrictRecordCodec,
    TransactionState,
    canonical_sha256,
    seal_record,
)
from frontier_audiobook.production_preflight import (
    BoundedPreflightEstimateResult,
    LocalPreflightResult,
    bind_targeted_check_result,
    run_bounded_identity_rate_preflight,
    run_local_preflight,
)
from frontier_audiobook.production_transactions import TransactionStore
from frontier_audiobook.util import read_bytes_nofollow, sha256_bytes, workspace_relative


PROPERTY_TAG = "Feature: audiobook-production-workflow, Property 4: Authorization is exact, finite, current, and one-shot"
PROPERTY_SEED = 0xA0D10B04
GENERATED_CASES = 128

# **Validates: Requirements 6.1, 6.2, 6.3, 6.4, 6.5, 6.6, 6.7,
# 6.10, 6.11, 6.12, 6.13**

_SENTENCES = (
    "Alpha one two three four.",
    "Bravo one two three four.",
    "Charlie one two three four.",
)
_VALIDATION_TIME = "2026-09-14T12:03:00Z"
_CASE_KINDS = (
    "request-transaction-permutation",
    "request-scope-permutation",
    "request-scope-addition",
    "request-scope-removal",
    "request-command-mutation",
    "request-call-increase",
    "request-call-decrease",
    "request-authorization-digest",
    "request-plan-digest",
    "request-preflight-digest",
    "authorization-scope-permutation",
    "authorization-scope-addition",
    "authorization-scope-removal",
    "authorization-command-mutation",
    "authorization-call-change",
    "authorization-plan-digest",
    "authorization-preflight-digest",
    "authorization-estimate-change",
    "authorization-approved-maximum-change",
    "plan-command-mutation",
    "approved-maximum-below-estimate",
    "approved-maximum-malformed",
    "expiration-not-yet-valid",
    "expiration-exact-boundary",
    "expiration-after-boundary",
    "expiration-at-issue",
    "expiration-beyond-freshness",
    "confirmation-at-expiration",
    "one-shot-false",
    "consumed-ledger",
    "stopped-batch",
    "repeated-consumption",
)
_BATCH_ONLY = {
    "request-transaction-permutation",
    "request-scope-permutation",
    "request-scope-addition",
    "request-scope-removal",
    "authorization-scope-permutation",
    "authorization-scope-addition",
    "authorization-scope-removal",
    "stopped-batch",
}


class _Clock:
    def __init__(self, *values: str):
        self._values = [
            datetime.fromisoformat(value.removesuffix("Z") + "+00:00").astimezone(UTC)
            for value in values
        ]

    def __call__(self) -> datetime:
        if not self._values:
            raise AssertionError("property clock was called more often than expected")
        return self._values.pop(0)


class _SyntheticProcess:
    def __init__(self):
        self.stdout = io.BytesIO(b"")

    def wait(self) -> int:
        return 0


class _LaunchObserver:
    def __init__(self):
        self.count = 0

    def __call__(self, *_args, **kwargs):
        assert kwargs["shell"] is False
        assert kwargs["stdout"] is attempt_module.subprocess.PIPE
        self.count += 1
        return _SyntheticProcess()


@dataclass(frozen=True, slots=True)
class _AuthorizationFixture:
    workspace: Path
    config: BookProductionConfig
    plan: FrozenBatchPlan
    local: LocalPreflightResult
    bounded: BoundedPreflightEstimateResult
    authorization: PaidAuthorization


@dataclass(frozen=True, slots=True)
class _GeneratedCase:
    kind: str
    nonce: int
    use_batch: bool


@pytest.fixture(autouse=True)
def deny_external_access_and_render(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("Property 4 must remain local, synthetic, and nonbillable")

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
        / f"discovery-part-{chapter:03d}-property-four.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    body = " ".join(_SENTENCES)
    path.write_text(
        "\n".join(
            (
                "---",
                "movement: discovery",
                f"chapter: {chapter}",
                'title: "Property Four Chapter"',
                "pov_id: property-four-pov",
                "timeline_id: property-four-timeline",
                "motif_events: none",
                "hook: property-four",
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
    path = workspace / "audiobook-studio" / "config" / "production.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '''schema_version = 1
book_id = "the-final-frontier"
manuscript_root = "The Final Frontier Novel"
build_root = "audiobook-studio/build/production"
delivery_root = "audiobook-studio/dist/audiobook"
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


def _store(fixture: _AuthorizationFixture) -> TransactionStore:
    return TransactionStore(
        fixture.workspace / fixture.config.build_root / fixture.config.book_id,
        fixture.config.book_id,
    )


def _exact_confirmation(display: AuthorizationDisplay) -> ExactAuthorizationConfirmation:
    return ExactAuthorizationConfirmation(
        schema_version=1,
        display_sha256=display.canonical_sha256,
        challenge=display.confirmation_challenge,
        decision=AuthorizationDecision.AUTHORIZE_EXACT_SCOPE,
    )


def _approved_maximum(bounded: BoundedPreflightEstimateResult) -> str:
    return format(Decimal(bounded.estimate.estimated_pre_tax_usd) + Decimal("1"), "f")


def _build_fixture(workspace: Path, chapters: tuple[int, ...]) -> _AuthorizationFixture:
    for chapter in chapters:
        _write_chapter(workspace, chapter)
    config_path = _write_config(workspace)
    plan_path = create_production_plan(
        config_path,
        ProductionSelectors.from_cli(chapters=chapters),
        plan_id=f"property-four-{'batch' if len(chapters) > 1 else 'single'}-plan",
        workspace_root=workspace,
        created_at_utc="2026-09-14T10:00:00Z",
    )
    plan = load_production_plan(plan_path)
    config = parse_production_toml(read_bytes_nofollow(config_path), label=str(config_path))
    catalog = build_ordered_track_catalog(config, workspace)

    targeted_path = workspace / "audiobook-studio" / "build" / "targeted" / "property-four.json"
    targeted_path.parent.mkdir(parents=True, exist_ok=True)
    targeted_path.write_text('{"passed":true,"external_access":false}', encoding="utf-8")
    targeted = bind_targeted_check_result(
        workspace,
        workspace_relative(workspace, targeted_path),
        command_sha256=canonical_sha256(
            ("pytest", "tests/test_production_property_4.py")
        ),
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

    store = TransactionStore(
        workspace / config.build_root / config.book_id,
        config.book_id,
    )
    store.materialize_plan(plan, occurred_at_utc="2026-09-14T10:00:00Z")
    for track in plan.tracks:
        store.append_transition(
            track.track_id,
            track.transaction_id,
            operation_id="property-four-preflight-passed",
            event_type="preflight-passed",
            state_after=TransactionState.PREFLIGHT_PASSED,
            details={"preflight_sha256": bounded.canonical_sha256},
            occurred_at_utc="2026-09-14T12:00:01Z",
        )
        store.append_transition(
            track.track_id,
            track.transaction_id,
            operation_id="property-four-authorization-required",
            event_type="authorization-required",
            state_after=TransactionState.AUTHORIZATION_REQUIRED,
            details={"preflight_sha256": bounded.canonical_sha256},
            occurred_at_utc="2026-09-14T12:00:02Z",
        )

    authorization = create_paid_authorization(
        config,
        plan,
        local,
        bounded,
        workspace_root=workspace,
        authorization_id="property-four-authorization",
        operator_approved_max_estimated_pre_tax_usd=_approved_maximum(bounded),
        expires_at_utc="2026-09-14T13:00:00Z",
        confirmation_provider=_exact_confirmation,
        clock=_Clock("2026-09-14T12:01:00Z", "2026-09-14T12:02:00Z"),
    )
    return _AuthorizationFixture(workspace, config, plan, local, bounded, authorization)


def _copy_fixture(
    fixture: _AuthorizationFixture,
    destination: Path,
) -> _AuthorizationFixture:
    shutil.copytree(fixture.workspace, destination)
    return replace(fixture, workspace=destination)


def _create_authorization(
    fixture: _AuthorizationFixture,
    *,
    authorization_id: str,
    approved_maximum: str,
    expires_at_utc: str,
    issued_at_utc: str = "2026-09-14T12:01:00Z",
    confirmed_at_utc: str = "2026-09-14T12:02:00Z",
) -> PaidAuthorization:
    return create_paid_authorization(
        fixture.config,
        fixture.plan,
        fixture.local,
        fixture.bounded,
        workspace_root=fixture.workspace,
        authorization_id=authorization_id,
        operator_approved_max_estimated_pre_tax_usd=approved_maximum,
        expires_at_utc=expires_at_utc,
        confirmation_provider=_exact_confirmation,
        clock=_Clock(issued_at_utc, confirmed_at_utc),
    )


def _validate(
    fixture: _AuthorizationFixture,
    authorization: PaidAuthorization,
    request: AuthorizationStartRequest,
    *,
    plan: FrozenBatchPlan | None = None,
    now: str = _VALIDATION_TIME,
) -> PaidAuthorization:
    return validate_paid_authorization_start(
        authorization,
        fixture.config,
        fixture.plan if plan is None else plan,
        fixture.local,
        fixture.bounded,
        request,
        workspace_root=fixture.workspace,
        clock=_Clock(now),
    )


def _validate_then_attempt(
    fixture: _AuthorizationFixture,
    authorization: PaidAuthorization,
    request: AuthorizationStartRequest,
    *,
    plan: FrozenBatchPlan | None = None,
    now: str = _VALIDATION_TIME,
):
    selected_plan = fixture.plan if plan is None else plan
    assert _validate(fixture, authorization, request, plan=selected_plan, now=now) == authorization
    track = selected_plan.tracks[0]
    return run_atomic_paid_attempt(
        track,
        authorization,
        plan=selected_plan,
        authorization_start=request,
        workspace_root=fixture.workspace,
        store=_store(fixture),
        exact_environment={"PATH": "/usr/bin:/bin", "HOME": str(fixture.workspace)},
        output_stream=io.StringIO(),
        clock=lambda: datetime(2026, 9, 14, 12, 3, tzinfo=UTC),
    )


def _different_digest(current: str, nonce: int) -> str:
    candidate = sha256_bytes(f"property-four-{nonce}".encode("utf-8"))
    if candidate == current:
        candidate = sha256_bytes(f"property-four-{nonce}-different".encode("utf-8"))
    return candidate


def _reseal_authorization(
    authorization: PaidAuthorization,
    **changes,
) -> PaidAuthorization:
    return seal_record(replace(authorization, **changes, canonical_sha256=""))


def _generated_cases(rng: random.Random) -> tuple[_GeneratedCase, ...]:
    cases = []
    for index in range(GENERATED_CASES):
        kind = _CASE_KINDS[index % len(_CASE_KINDS)]
        cases.append(
            _GeneratedCase(
                kind=kind,
                nonce=rng.getrandbits(64),
                use_batch=kind in _BATCH_ONLY or bool(rng.getrandbits(1)),
            )
        )
    return tuple(cases)


def _assert_invalid_case(
    case: _GeneratedCase,
    fixture: _AuthorizationFixture,
    case_root: Path,
    observer: _LaunchObserver,
) -> int:
    authorization = fixture.authorization
    request = build_authorization_start_request(authorization)
    plan = fixture.plan
    now = _VALIDATION_TIME
    kind = case.kind

    if kind == "approved-maximum-below-estimate":
        estimate = Decimal(fixture.bounded.estimate.estimated_pre_tax_usd)
        assert estimate > 0
        with pytest.raises(InputError):
            _create_authorization(
                fixture,
                authorization_id=f"property-four-below-{case.nonce:x}",
                approved_maximum=format(estimate / Decimal(2), "f"),
                expires_at_utc="2026-09-14T13:00:00Z",
            )
        return 0

    if kind == "approved-maximum-malformed":
        malformed = ("NaN", "Infinity", "-0.01", "1e3", "")[case.nonce % 5]
        with pytest.raises(InputError):
            _create_authorization(
                fixture,
                authorization_id=f"property-four-malformed-{case.nonce:x}",
                approved_maximum=malformed,
                expires_at_utc="2026-09-14T13:00:00Z",
            )
        return 0

    if kind == "expiration-at-issue":
        with pytest.raises(InputError):
            _create_authorization(
                fixture,
                authorization_id=f"property-four-expiry-at-issue-{case.nonce:x}",
                approved_maximum=_approved_maximum(fixture.bounded),
                expires_at_utc="2026-09-14T12:01:00Z",
            )
        return 0

    if kind == "expiration-beyond-freshness":
        with pytest.raises(InputError):
            _create_authorization(
                fixture,
                authorization_id=f"property-four-stale-{case.nonce:x}",
                approved_maximum=_approved_maximum(fixture.bounded),
                expires_at_utc="2026-09-15T12:00:00.000001Z",
            )
        return 0

    if kind == "confirmation-at-expiration":
        with pytest.raises(InputError):
            _create_authorization(
                fixture,
                authorization_id=f"property-four-confirm-expired-{case.nonce:x}",
                approved_maximum=_approved_maximum(fixture.bounded),
                expires_at_utc="2026-09-14T12:02:00Z",
            )
        return 0

    if kind == "one-shot-false":
        with pytest.raises(InputError):
            replace(authorization, one_shot=False, canonical_sha256="")
        return 0

    if kind in {"consumed-ledger", "stopped-batch", "repeated-consumption"}:
        fixture = _copy_fixture(fixture, case_root)
        authorization = fixture.authorization
        request = build_authorization_start_request(authorization)
        store = _store(fixture)
        first = fixture.plan.tracks[0]
        authorization_sha256 = StrictRecordCodec(PaidAuthorization).sha256(authorization)

        if kind == "consumed-ledger":
            store.append_transition(
                first.track_id,
                first.transaction_id,
                operation_id=f"property-four-consumed-{case.nonce:x}",
                event_type="authorization-consumed",
                state_after=TransactionState.RUNNING,
                details={"authorization_sha256": authorization_sha256},
                occurred_at_utc="2026-09-14T12:02:30Z",
            )
        elif kind == "stopped-batch":
            store.append_transition(
                first.track_id,
                first.transaction_id,
                operation_id=f"property-four-stopped-{case.nonce:x}",
                event_type="batch-stopped",
                state_after=TransactionState.BLOCKED,
                details={"authorization_sha256": authorization_sha256},
                occurred_at_utc="2026-09-14T12:02:30Z",
            )
        else:
            result = _validate_then_attempt(fixture, authorization, request)
            assert result.native_return_code == 0
            before_retry = observer.count
            with pytest.raises(InputError):
                _validate_then_attempt(fixture, authorization, request)
            assert observer.count == before_retry
            return 1

        with pytest.raises(InputError):
            _validate_then_attempt(fixture, authorization, request)
        return 0

    if kind == "request-transaction-permutation":
        request = replace(
            request,
            exact_transaction_ids=tuple(reversed(request.exact_transaction_ids)),
        )
    elif kind == "request-scope-permutation":
        request = replace(
            request,
            exact_transaction_ids=tuple(reversed(request.exact_transaction_ids)),
            exact_track_ids=tuple(reversed(request.exact_track_ids)),
            exact_command_sha256s=tuple(reversed(request.exact_command_sha256s)),
            maximum_new_calls_by_track=tuple(reversed(request.maximum_new_calls_by_track)),
        )
    elif kind == "request-scope-addition":
        extra_track = f"extra-track-{case.nonce:x}"
        request = AuthorizationStartRequest(
            authorization_sha256=request.authorization_sha256,
            plan_sha256=request.plan_sha256,
            preflight_sha256=request.preflight_sha256,
            exact_transaction_ids=(*request.exact_transaction_ids, f"extra-transaction-{case.nonce:x}"),
            exact_track_ids=(*request.exact_track_ids, extra_track),
            exact_command_sha256s=(
                *request.exact_command_sha256s,
                _different_digest(request.exact_command_sha256s[0], case.nonce),
            ),
            maximum_new_calls_by_track=(*request.maximum_new_calls_by_track, (extra_track, 1)),
            maximum_new_calls_total=request.maximum_new_calls_total + 1,
        )
    elif kind == "request-scope-removal":
        removed_calls = request.maximum_new_calls_by_track[-1][1]
        request = AuthorizationStartRequest(
            authorization_sha256=request.authorization_sha256,
            plan_sha256=request.plan_sha256,
            preflight_sha256=request.preflight_sha256,
            exact_transaction_ids=request.exact_transaction_ids[:-1],
            exact_track_ids=request.exact_track_ids[:-1],
            exact_command_sha256s=request.exact_command_sha256s[:-1],
            maximum_new_calls_by_track=request.maximum_new_calls_by_track[:-1],
            maximum_new_calls_total=request.maximum_new_calls_total - removed_calls,
        )
    elif kind == "request-command-mutation":
        commands = list(request.exact_command_sha256s)
        commands[0] = _different_digest(commands[0], case.nonce)
        request = replace(request, exact_command_sha256s=tuple(commands))
    elif kind in {"request-call-increase", "request-call-decrease"}:
        rows = list(request.maximum_new_calls_by_track)
        track_id, old_calls = rows[0]
        delta = 1 if kind.endswith("increase") else -1
        assert old_calls + delta >= 0
        rows[0] = (track_id, old_calls + delta)
        request = replace(
            request,
            maximum_new_calls_by_track=tuple(rows),
            maximum_new_calls_total=request.maximum_new_calls_total + delta,
        )
    elif kind == "request-authorization-digest":
        request = replace(
            request,
            authorization_sha256=_different_digest(request.authorization_sha256, case.nonce),
        )
    elif kind == "request-plan-digest":
        request = replace(
            request,
            plan_sha256=_different_digest(request.plan_sha256, case.nonce),
        )
    elif kind == "request-preflight-digest":
        request = replace(
            request,
            preflight_sha256=_different_digest(request.preflight_sha256, case.nonce),
        )
    elif kind == "authorization-scope-permutation":
        authorization = _reseal_authorization(
            authorization,
            exact_transaction_ids=tuple(reversed(authorization.exact_transaction_ids)),
            exact_track_ids=tuple(reversed(authorization.exact_track_ids)),
            exact_command_sha256s=tuple(reversed(authorization.exact_command_sha256s)),
        )
        request = build_authorization_start_request(authorization)
    elif kind == "authorization-scope-addition":
        extra_track = f"extra-track-{case.nonce:x}"
        calls = dict(authorization.maximum_new_calls_by_track)
        calls[extra_track] = 1
        authorization = _reseal_authorization(
            authorization,
            exact_transaction_ids=(
                *authorization.exact_transaction_ids,
                f"extra-transaction-{case.nonce:x}",
            ),
            exact_track_ids=(*authorization.exact_track_ids, extra_track),
            exact_command_sha256s=(
                *authorization.exact_command_sha256s,
                _different_digest(authorization.exact_command_sha256s[0], case.nonce),
            ),
            maximum_new_calls_by_track=calls,
            maximum_new_calls_total=authorization.maximum_new_calls_total + 1,
        )
        request = build_authorization_start_request(authorization)
    elif kind == "authorization-scope-removal":
        removed_track = authorization.exact_track_ids[-1]
        calls = dict(authorization.maximum_new_calls_by_track)
        removed_calls = calls.pop(removed_track)
        authorization = _reseal_authorization(
            authorization,
            exact_transaction_ids=authorization.exact_transaction_ids[:-1],
            exact_track_ids=authorization.exact_track_ids[:-1],
            exact_command_sha256s=authorization.exact_command_sha256s[:-1],
            maximum_new_calls_by_track=calls,
            maximum_new_calls_total=authorization.maximum_new_calls_total - removed_calls,
        )
        request = build_authorization_start_request(authorization)
    elif kind == "authorization-command-mutation":
        commands = list(authorization.exact_command_sha256s)
        commands[0] = _different_digest(commands[0], case.nonce)
        authorization = _reseal_authorization(
            authorization,
            exact_command_sha256s=tuple(commands),
        )
        request = build_authorization_start_request(authorization)
    elif kind == "authorization-call-change":
        calls = dict(authorization.maximum_new_calls_by_track)
        calls[authorization.exact_track_ids[0]] += 1
        authorization = _reseal_authorization(
            authorization,
            maximum_new_calls_by_track=calls,
            maximum_new_calls_total=authorization.maximum_new_calls_total + 1,
        )
        request = build_authorization_start_request(authorization)
    elif kind == "authorization-plan-digest":
        authorization = _reseal_authorization(
            authorization,
            plan_sha256=_different_digest(authorization.plan_sha256, case.nonce),
        )
        request = build_authorization_start_request(authorization)
    elif kind == "authorization-preflight-digest":
        authorization = _reseal_authorization(
            authorization,
            preflight_sha256=_different_digest(authorization.preflight_sha256, case.nonce),
        )
        request = build_authorization_start_request(authorization)
    elif kind == "authorization-estimate-change":
        changed = Decimal(authorization.estimated_pre_tax_usd) + Decimal(
            (case.nonce % 100) + 1
        ) / Decimal(10000)
        authorization = _reseal_authorization(
            authorization,
            estimated_pre_tax_usd=format(changed, "f"),
        )
        request = build_authorization_start_request(authorization)
    elif kind == "authorization-approved-maximum-change":
        changed = Decimal(authorization.operator_approved_max_estimated_pre_tax_usd) + Decimal(
            (case.nonce % 100) + 1
        ) / Decimal(10000)
        authorization = _reseal_authorization(
            authorization,
            operator_approved_max_estimated_pre_tax_usd=format(changed, "f"),
        )
        request = build_authorization_start_request(authorization)
    elif kind == "plan-command-mutation":
        tracks = list(plan.tracks)
        changed_argv = (*tracks[0].command_argv, f"--property-four-{case.nonce:x}")
        tracks[0] = replace(
            tracks[0],
            command_argv=changed_argv,
            command_sha256=canonical_sha256(changed_argv),
        )
        plan = seal_record(replace(plan, tracks=tuple(tracks), canonical_sha256=""))
    elif kind == "expiration-not-yet-valid":
        now = "2026-09-14T12:00:59.999999Z"
    elif kind == "expiration-exact-boundary":
        now = authorization.expires_at_utc
    elif kind == "expiration-after-boundary":
        now = "2026-09-14T13:00:00.000001Z"
    else:  # pragma: no cover - the generated-kind coverage assertion guards this
        raise AssertionError(f"unhandled Property 4 case kind: {kind}")

    with pytest.raises(InputError):
        _validate_then_attempt(
            fixture,
            authorization,
            request,
            plan=plan,
            now=now,
        )
    return 0


def test_property_4_authorization_is_exact_finite_current_and_one_shot(
    tmp_path,
    monkeypatch,
):
    """Feature: audiobook-production-workflow, Property 4: Authorization is exact, finite, current, and one-shot"""

    assert GENERATED_CASES >= 100
    assert GENERATED_CASES % len(_CASE_KINDS) == 0
    print(f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; cases={GENERATED_CASES}")
    rng = random.Random(PROPERTY_SEED)
    single = _build_fixture(tmp_path / "single", (1,))
    batch = _build_fixture(tmp_path / "batch", (1, 2, 3))

    observer = _LaunchObserver()
    monkeypatch.setattr(attempt_module.subprocess, "Popen", observer)

    # Requirements 6.1/6.2: the same exact validator accepts single-Track and
    # finite ordered batch authorizations without consuming or launching either.
    for fixture in (single, batch):
        request = build_authorization_start_request(fixture.authorization)
        assert _validate(fixture, fixture.authorization, request) == fixture.authorization
    assert observer.count == 0

    # Decimal equality is sufficient (6.6/6.7), and expiration may reach the
    # exact preflight deadline while validation remains valid immediately before it.
    exact_estimate = batch.bounded.estimate.estimated_pre_tax_usd
    exact_maximum = _create_authorization(
        batch,
        authorization_id="property-four-exact-decimal-boundary",
        approved_maximum=exact_estimate,
        expires_at_utc="2026-09-14T13:00:00Z",
    )
    assert _validate(
        batch,
        exact_maximum,
        build_authorization_start_request(exact_maximum),
    ) == exact_maximum
    deadline = _create_authorization(
        batch,
        authorization_id="property-four-exact-expiration-deadline",
        approved_maximum=_approved_maximum(batch.bounded),
        expires_at_utc="2026-09-15T12:00:00Z",
    )
    assert _validate(
        batch,
        deadline,
        build_authorization_start_request(deadline),
        now="2026-09-15T11:59:59.999999Z",
    ) == deadline
    assert observer.count == 0

    cases = _generated_cases(rng)
    assert len(cases) == GENERATED_CASES
    coverage: set[str] = set()
    for case_index, case in enumerate(cases):
        coverage.add(case.kind)
        fixture = batch if case.use_batch else single
        before = observer.count
        context = (
            f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; case={case_index}; "
            f"kind={case.kind}; nonce={case.nonce}; batch={case.use_batch}"
        )
        try:
            expected_synthetic_launches = _assert_invalid_case(
                case,
                fixture,
                tmp_path / "generated" / f"case-{case_index:03d}",
                observer,
            )
            assert observer.count == before + expected_synthetic_launches
        except Exception as exc:
            exc.add_note(context)
            raise

    assert coverage == set(_CASE_KINDS)
