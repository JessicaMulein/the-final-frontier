"""Deterministic generated checks for audiobook production correctness Property 5."""

from __future__ import annotations

import io
import json
import os
import random
import signal
import socket
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Iterator

import pytest

import frontier_audiobook.production_attempt as attempt_module
from frontier_audiobook.errors import InputError
from frontier_audiobook.production_attempt import (
    AttemptChargeUncertain,
    run_atomic_paid_attempt,
)
from frontier_audiobook.production_authorization import (
    build_authorization_start_request,
)
from frontier_audiobook.production_models import (
    AttemptResult,
    AudioEncoding,
    AudioFormat,
    AuthorizationDecision,
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


PROPERTY_TAG = "Feature: audiobook-production-workflow, Property 5: Paid attempt state is definitive or explicitly uncertain"
PROPERTY_SEED = 0xA0D10B05
GENERATED_CASES = 100

# **Validates: Requirements 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7,
# 7.8, 7.9, 7.10**

_SCENARIOS = (
    "exit-zero",
    "nonzero-status",
    "signal",
    "prelaunch-interruption",
    "output-interruption",
    "commit-interruption",
    "missing-file",
    "inconsistent-console-hash",
    "status-less-wait",
    "stale-staging",
    "duplicate-attempt-id",
    "ambiguous-attempt-id",
)
_TERMINATING_SIGNALS = tuple(
    int(candidate)
    for candidate in (
        getattr(signal, "SIGTERM", None),
        getattr(signal, "SIGKILL", None),
        getattr(signal, "SIGHUP", None),
    )
    if candidate is not None
)


@dataclass(frozen=True, slots=True)
class _GeneratedCase:
    scenario: str
    attempt_id: str
    exit_status: int
    signal_number: int
    stdout_payload: bytes
    stderr_payload: bytes
    missing_file: str


@pytest.fixture(autouse=True)
def deny_network_and_external_services(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail if this local process crosses a network or credential boundary."""

    def blocked(*_args, **_kwargs):
        raise AssertionError("Property 5 must remain offline and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "parent-access-value-must-not-persist")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "parent-secret-value-must-not-persist")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "parent-session-value-must-not-persist")


def _fixed_clock() -> datetime:
    return datetime(2026, 9, 14, 12, 3, tzinfo=UTC)


def _hash(character: str) -> str:
    return character * 64


def _shuffled_cycle(rng: random.Random, values: tuple[object, ...]) -> Iterator[object]:
    while True:
        batch = list(values)
        rng.shuffle(batch)
        yield from batch


def _generated_cases(rng: random.Random) -> Iterator[_GeneratedCase]:
    scenarios = _shuffled_cycle(rng, _SCENARIOS)
    signals = _shuffled_cycle(rng, _TERMINATING_SIGNALS)
    missing_files = _shuffled_cycle(rng, ("attempt.json", "render-console.log"))
    for case_index in range(GENERATED_CASES):
        scenario = next(scenarios)
        nonce = rng.getrandbits(64)
        yield _GeneratedCase(
            scenario=str(scenario),
            attempt_id=f"attempt-{case_index:03d}",
            exit_status=1 + ((case_index * 37 + rng.randrange(31)) % 120),
            signal_number=(
                int(next(signals)) if scenario == "signal" else _TERMINATING_SIGNALS[0]
            ),
            stdout_payload=(
                f"private-stdout-{case_index:03d}-{nonce:016x}".encode("ascii")
            ),
            stderr_payload=(
                f"private-stderr-{case_index:03d}-{nonce ^ 0x55AA55AA55AA55AA:016x}".encode(
                    "ascii"
                )
            ),
            missing_file=str(next(missing_files)),
        )


def _track_plan(argv: tuple[str, ...]) -> FrozenTrackPlan:
    track_id = "chapter-001"
    render_config_sha256 = _hash("1")
    segment = SegmentSnapshot(
        segment_id="segment-001",
        ordinal=1,
        paragraph_index=0,
        start_token_index=0,
        end_token_index=1,
        text_sha256=_hash("2"),
        normalized_tokens_sha256=_hash("3"),
        context_before_sha256=None,
        context_after_sha256=None,
        render_config_sha256=render_config_sha256,
        render_identity_sha256=_hash("4"),
        spoken_token_count=1,
        narration_only_punctuation=False,
    )
    source = SourceSnapshot(
        track_id=track_id,
        source_path="The Final Frontier Novel/chapters/chapter-001.md",
        source_section=None,
        source_kind=SourceKind.CHAPTER,
        raw_sha256=_hash("5"),
        normalized_body_sha256=_hash("6"),
        spoken_sha256=_hash("7"),
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
        sequence=1,
        voice="tiffany",
        model_id="amazon.nova-2-sonic-v1:0",
        region="us-east-1",
        profile_label="frontier-audiobook",
        target_segment_words=5,
        fidelity_policy=FidelityPolicy.EXACT,
        normalization="frontier-word-sequence-v1",
        audio_format=AudioFormat(24000, 16, 1, AudioEncoding.PCM_S16LE),
        output_path=".audiobook/dist/audiobook/001-chapter-001-tiffany.wav",
        resolution_provenance={"voice": "defaults", "model_id": "defaults"},
    )
    return FrozenTrackPlan(
        transaction_id="transaction-001",
        track_id=track_id,
        sequence=1,
        effective_config=effective,
        source=source,
        command_argv=argv,
        command_sha256=canonical_sha256(argv),
        maximum_new_calls=1,
        legacy_candidates=(),
        protected_inventory_sha256=_hash("8"),
    )


def _plan(argv: tuple[str, ...]) -> FrozenBatchPlan:
    return seal_record(
        FrozenBatchPlan(
            schema_version=1,
            plan_id="property-five-plan",
            created_at_utc="2026-09-14T12:00:00Z",
            book_id="the-final-frontier",
            config_path=".audiobook/config/production.toml",
            config_sha256=_hash("9"),
            selectors=("chapter:1",),
            tracks=(_track_plan(argv),),
            canonical_sha256="",
        )
    )


def _authorization(plan: FrozenBatchPlan) -> PaidAuthorization:
    track = plan.tracks[0]
    challenge = _hash("a")
    display_sha256 = _hash("b")
    confirmed_at_utc = "2026-09-14T12:00:30Z"
    decision = AuthorizationDecision.AUTHORIZE_EXACT_SCOPE
    return seal_record(
        PaidAuthorization(
            schema_version=1,
            authorization_id="property-five-authorization",
            plan_sha256=StrictRecordCodec(FrozenBatchPlan).sha256(plan),
            preflight_sha256=_hash("c"),
            local_preflight_sha256=_hash("d"),
            estimate_sha256=_hash("e"),
            official_rate_provenance_sha256=_hash("f"),
            exact_transaction_ids=(track.transaction_id,),
            exact_track_ids=(track.track_id,),
            exact_command_sha256s=(track.command_sha256,),
            maximum_new_calls_by_track={track.track_id: 1},
            maximum_new_calls_total=1,
            estimated_pre_tax_usd="0.250",
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


def _ready_attempt(workspace: Path, argv: tuple[str, ...]):
    plan = _plan(argv)
    track = plan.tracks[0]
    authorization = _authorization(plan)
    store = TransactionStore(
        workspace / ".audiobook" / "build" / "production" / plan.book_id,
        plan.book_id,
    )
    store.materialize_plan(plan, occurred_at_utc="2026-09-14T12:00:00Z")
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
    return (
        plan,
        track,
        authorization,
        build_authorization_start_request(authorization),
        store,
    )


def _transaction_root(workspace: Path) -> Path:
    return (
        workspace
        / ".audiobook"
        / "build"
        / "production"
        / "the-final-frontier"
        / "transactions"
        / "chapter-001"
        / "transaction-001"
    )


def _secret_values(case_index: int) -> tuple[str, ...]:
    return (
        f"access-value-{case_index:03d}-must-not-persist",
        f"secret-value-{case_index:03d}-must-not-persist",
        f"session-value-{case_index:03d}-must-not-persist",
        f"unrelated-value-{case_index:03d}-must-not-persist",
    )


def _run(
    workspace: Path,
    fixture,
    case: _GeneratedCase,
    case_index: int,
    output_stream: io.StringIO,
):
    plan, track, authorization, request, store = fixture
    access, secret, session, unrelated = _secret_values(case_index)
    return run_atomic_paid_attempt(
        track,
        authorization,
        plan=plan,
        authorization_start=request,
        workspace_root=workspace,
        store=store,
        exact_environment={
            "PATH": os.environ.get("PATH", os.defpath),
            "HOME": str(workspace),
            "AWS_ACCESS_KEY_ID": access,
            "AWS_SECRET_ACCESS_KEY": secret,
            "AWS_SESSION_TOKEN": session,
            "UNRELATED_SECRET": unrelated,
        },
        output_stream=output_stream,
        attempt_id=case.attempt_id,
        clock=_fixed_clock,
    )


def _synthetic_argv(
    case: _GeneratedCase,
    launch_counter: Path,
    environment_result: Path,
    shell_sentinel: Path,
) -> tuple[str, ...]:
    if case.scenario == "signal":
        ending = f"os.kill(os.getpid(),{case.signal_number});sys.exit(125)"
    elif case.scenario == "nonzero-status":
        ending = f"sys.exit({case.exit_status})"
    else:
        ending = "sys.exit(0)"
    script = (
        "import os,sys;from pathlib import Path;"
        "counter=Path(sys.argv[1]);"
        "count=int(counter.read_text()) if counter.exists() else 0;"
        "counter.write_text(str(count+1));"
        "safe=os.environ.get('AWS_PROFILE')=='frontier-audiobook' and "
        "'AWS_ACCESS_KEY_ID' not in os.environ and "
        "'AWS_SECRET_ACCESS_KEY' not in os.environ and "
        "'AWS_SESSION_TOKEN' not in os.environ and "
        "'UNRELATED_SECRET' not in os.environ;"
        "Path(sys.argv[2]).write_text('ok' if safe else 'bad');"
        "safe or sys.exit(121);"
        f"sys.stdout.buffer.write(bytes.fromhex('{case.stdout_payload.hex()}'));"
        "sys.stdout.buffer.flush();"
        f"sys.stderr.buffer.write(bytes.fromhex('{case.stderr_payload.hex()}'));"
        "sys.stderr.buffer.flush();"
        f"{ending}"
    )
    return (
        sys.executable,
        "-c",
        script,
        str(launch_counter),
        str(environment_result),
        f"literal=; touch {shell_sentinel}",
    )


def _tree_snapshot(root: Path) -> dict[str, bytes | None]:
    if not root.exists():
        return {}
    snapshot: dict[str, bytes | None] = {}
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        snapshot[relative] = None if path.is_dir() else path.read_bytes()
    return snapshot


def _assert_no_private_values(
    transaction_root: Path,
    case: _GeneratedCase,
    case_index: int,
    output: io.StringIO,
) -> None:
    evidence = b"\n".join(
        path.read_bytes() for path in transaction_root.rglob("*") if path.is_file()
    )
    for prohibited in (
        case.stdout_payload,
        case.stderr_payload,
        *[value.encode("utf-8") for value in _secret_values(case_index)],
    ):
        assert prohibited not in evidence
        assert prohibited.decode("utf-8") not in output.getvalue()


def _assert_console_metadata(
    console: Path,
    case: _GeneratedCase,
) -> None:
    lines = console.read_text(encoding="utf-8").splitlines()
    assert lines
    events = tuple(json.loads(line) for line in lines)
    assert sum(event["byte_count"] for event in events) == (
        len(case.stdout_payload) + len(case.stderr_payload)
    )
    for sequence, event in enumerate(events, start=1):
        assert set(event) == {
            "byte_count",
            "event",
            "schema_version",
            "sequence",
            "sha256",
        }
        assert event["event"] == "child-output-chunk"
        assert event["sequence"] == sequence
        assert event["byte_count"] > 0


def _assert_definitive(
    workspace: Path,
    fixture,
    case: _GeneratedCase,
    case_index: int,
    result: AttemptResult,
    output: io.StringIO,
    launch_counter: Path,
    environment_result: Path,
    shell_sentinel: Path,
) -> None:
    _plan_value, track, authorization, _request, store = fixture
    if case.scenario == "exit-zero":
        expected_status = 0
        expected_signal = None
        expected_state = TransactionState.RENDERED
    elif case.scenario == "nonzero-status":
        expected_status = case.exit_status
        expected_signal = None
        expected_state = TransactionState.BLOCKED
    else:
        expected_status = -case.signal_number
        expected_signal = case.signal_number
        expected_state = TransactionState.BLOCKED

    assert type(result.native_return_code) is int
    assert result.native_return_code == expected_status
    assert result.termination_signal == expected_signal
    assert result.child_launched is True
    assert result.argv == track.command_argv
    assert result.command_sha256 == track.command_sha256
    assert result.authorization_sha256 == StrictRecordCodec(PaidAuthorization).sha256(
        authorization
    )
    assert result.profile_label == "frontier-audiobook"
    assert result.working_directory == "."
    assert result.automatic_retry_performed is False
    assert result.environment_persisted is False
    assert launch_counter.read_text(encoding="utf-8") == "1"
    assert environment_result.read_text(encoding="utf-8") == "ok"
    assert not shell_sentinel.exists()

    attempts_root = _transaction_root(workspace) / "attempts"
    final = attempts_root / case.attempt_id
    assert final.is_dir()
    assert not tuple(attempts_root.glob(f"{case.attempt_id}.staging-*"))
    assert not (attempts_root / f"{case.attempt_id}.ambiguous.json").exists()
    assert os.stat(final, follow_symlinks=False).st_dev == os.stat(
        attempts_root, follow_symlinks=False
    ).st_dev
    persisted = StrictRecordCodec(AttemptResult).load(final / "attempt.json")
    assert persisted == result
    console = final / "render-console.log"
    assert sha256_file(console) == result.console_sha256
    _assert_console_metadata(console, case)
    _assert_no_private_values(_transaction_root(workspace), case, case_index, output)

    snapshot = store.inspect_transaction(track.track_id, track.transaction_id)
    assert snapshot.state is expected_state
    terminal = snapshot.payloads[-1]
    assert terminal.details["native_return_code"] == expected_status
    assert terminal.details["termination_signal"] == expected_signal
    assert terminal.details["automatic_retry_performed"] is False

    with pytest.raises(InputError):
        _run(workspace, fixture, case, case_index, io.StringIO())
    assert launch_counter.read_text(encoding="utf-8") == "1"
    assert store.inspect_transaction(track.track_id, track.transaction_id).state is expected_state


def _assert_uncertain(
    workspace: Path,
    fixture,
    case: _GeneratedCase,
    case_index: int,
    output: io.StringIO,
    launch_counter: Path,
    environment_result: Path,
    shell_sentinel: Path,
) -> None:
    _plan_value, track, _authorization, _request, store = fixture
    attempts_root = _transaction_root(workspace) / "attempts"
    staging = tuple(attempts_root.glob(f"{case.attempt_id}.staging-*"))
    assert len(staging) == 1
    assert os.stat(staging[0], follow_symlinks=False).st_dev == os.stat(
        attempts_root, follow_symlinks=False
    ).st_dev
    assert (attempts_root / f"{case.attempt_id}.ambiguous.json").is_file()
    assert not (attempts_root / case.attempt_id).exists()
    assert launch_counter.read_text(encoding="utf-8") == "1"
    assert environment_result.read_text(encoding="utf-8") == "ok"
    assert not shell_sentinel.exists()
    _assert_no_private_values(_transaction_root(workspace), case, case_index, output)

    if case.scenario == "missing-file":
        assert not (staging[0] / case.missing_file).exists()
    snapshot = store.inspect_transaction(track.track_id, track.transaction_id)
    assert snapshot.state is TransactionState.CHARGE_UNCERTAIN
    uncertain = tuple(
        payload
        for payload in snapshot.payloads
        if payload.event_type == "attempt-charge-uncertain"
    )
    assert len(uncertain) == 1
    assert uncertain[0].details["child_launch_status"] == "confirmed"
    assert uncertain[0].details["automatic_retry_performed"] is False

    with pytest.raises(InputError):
        _run(workspace, fixture, case, case_index, io.StringIO())
    assert launch_counter.read_text(encoding="utf-8") == "1"
    assert store.inspect_transaction(
        track.track_id, track.transaction_id
    ).state is TransactionState.CHARGE_UNCERTAIN


def _assert_prelaunch_blocked(
    workspace: Path,
    fixture,
    case: _GeneratedCase,
    case_index: int,
    launch_counter: Path,
    environment_result: Path,
    shell_sentinel: Path,
) -> None:
    _plan_value, track, _authorization, _request, store = fixture
    assert not launch_counter.exists()
    assert not environment_result.exists()
    assert not shell_sentinel.exists()
    attempts_root = _transaction_root(workspace) / "attempts"
    staging = tuple(attempts_root.glob(f"{case.attempt_id}.staging-*"))
    assert len(staging) == 1
    marker = json.loads((staging[0] / "launch-failure.json").read_text(encoding="utf-8"))
    assert marker["child_launched"] is False
    assert marker["automatic_retry_performed"] is False
    assert not (attempts_root / f"{case.attempt_id}.ambiguous.json").exists()
    assert not (attempts_root / case.attempt_id).exists()
    snapshot = store.inspect_transaction(track.track_id, track.transaction_id)
    assert snapshot.state is TransactionState.BLOCKED
    assert snapshot.payloads[-1].details["child_launched"] is False
    assert snapshot.payloads[-1].details["automatic_retry_performed"] is False

    with pytest.raises(InputError):
        _run(workspace, fixture, case, case_index, io.StringIO())
    assert not launch_counter.exists()


def _prepare_preexisting_evidence(
    attempts_root: Path,
    case: _GeneratedCase,
) -> None:
    attempts_root.mkdir(parents=True)
    if case.scenario == "stale-staging":
        (attempts_root / f"{case.attempt_id}.staging-stale").mkdir()
    elif case.scenario == "duplicate-attempt-id":
        (attempts_root / case.attempt_id).mkdir()
    else:
        (attempts_root / f"{case.attempt_id}.ambiguous.json").write_text(
            "{}", encoding="utf-8"
        )


def test_paid_attempt_state_is_definitive_or_explicitly_uncertain(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Feature: audiobook-production-workflow, Property 5: Paid attempt state is definitive or explicitly uncertain"""

    assert GENERATED_CASES >= 100
    assert _TERMINATING_SIGNALS
    print(f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; cases={GENERATED_CASES}")
    generated = tuple(_generated_cases(random.Random(PROPERTY_SEED)))
    assert len(generated) == GENERATED_CASES

    observed_scenarios: set[str] = set()
    observed_nonzero_statuses: set[int] = set()
    observed_signals: set[int] = set()
    observed_missing_files: set[str] = set()

    for case_index, case in enumerate(generated):
        observed_scenarios.add(case.scenario)
        context = (
            f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; case={case_index}; input={case!r}"
        )
        try:
            workspace = tmp_path / f"case-{case_index:03d}"
            workspace.mkdir()
            launch_counter = workspace / "synthetic-child-launch-count"
            environment_result = workspace / "synthetic-child-environment-result"
            shell_sentinel = workspace / "must-not-be-created-by-shell"
            argv = _synthetic_argv(
                case,
                launch_counter,
                environment_result,
                shell_sentinel,
            )
            fixture = _ready_attempt(workspace, argv)
            attempts_root = _transaction_root(workspace) / "attempts"
            output = io.StringIO()

            if case.scenario in {
                "stale-staging",
                "duplicate-attempt-id",
                "ambiguous-attempt-id",
            }:
                _prepare_preexisting_evidence(attempts_root, case)
                before = _tree_snapshot(_transaction_root(workspace))
                with pytest.raises(
                    InputError, match="Duplicate, staging, or ambiguous"
                ):
                    _run(workspace, fixture, case, case_index, output)
                assert _tree_snapshot(_transaction_root(workspace)) == before
                _plan_value, track, _authorization, _request, store = fixture
                assert store.inspect_transaction(
                    track.track_id, track.transaction_id
                ).state is TransactionState.AUTHORIZATION_REQUIRED
                assert not launch_counter.exists()
                assert not environment_result.exists()
                assert not shell_sentinel.exists()
                continue

            with monkeypatch.context() as patch:
                if case.scenario == "prelaunch-interruption":

                    def refuse_launch(*_args, **_kwargs):
                        raise OSError("injected interruption before direct-child launch")

                    patch.setattr(attempt_module.subprocess, "Popen", refuse_launch)
                elif case.scenario == "output-interruption":
                    original_stream = attempt_module._stream_sanitized_output

                    def interrupt_after_output(pipe, log_handle, output_stream):
                        original_stream(pipe, log_handle, output_stream)
                        raise OSError("injected interruption after direct-child launch")

                    patch.setattr(
                        attempt_module,
                        "_stream_sanitized_output",
                        interrupt_after_output,
                    )
                elif case.scenario == "commit-interruption":

                    def interrupt_commit(*_args, **_kwargs):
                        raise OSError("injected interruption before atomic bundle commit")

                    patch.setattr(attempt_module, "durable_replace", interrupt_commit)
                elif case.scenario == "missing-file":
                    observed_missing_files.add(case.missing_file)
                    original_write = StrictRecordCodec.write_atomic

                    def omit_required_file(codec, path, value):
                        if codec.record_type is AttemptResult:
                            if case.missing_file == "attempt.json":
                                return None
                            original_write(codec, path, value)
                            (path.parent / "render-console.log").unlink()
                            return None
                        return original_write(codec, path, value)

                    patch.setattr(StrictRecordCodec, "write_atomic", omit_required_file)
                elif case.scenario == "inconsistent-console-hash":
                    original_sha256_file = attempt_module.sha256_file

                    def inconsistent_console_hash(path: Path) -> str:
                        digest = original_sha256_file(path)
                        if path.name == "render-console.log":
                            return ("0" if digest[0] != "0" else "1") + digest[1:]
                        return digest

                    patch.setattr(
                        attempt_module, "sha256_file", inconsistent_console_hash
                    )
                elif case.scenario == "status-less-wait":
                    real_popen = attempt_module.subprocess.Popen

                    class _StatuslessProcess:
                        def __init__(self, *args, **kwargs):
                            self._process = real_popen(*args, **kwargs)
                            self.stdout = self._process.stdout

                        def wait(self):
                            self._process.wait()
                            return None

                    patch.setattr(
                        attempt_module.subprocess, "Popen", _StatuslessProcess
                    )

                if case.scenario == "prelaunch-interruption":
                    with pytest.raises(InputError, match="did not launch"):
                        _run(workspace, fixture, case, case_index, output)
                    _assert_prelaunch_blocked(
                        workspace,
                        fixture,
                        case,
                        case_index,
                        launch_counter,
                        environment_result,
                        shell_sentinel,
                    )
                elif case.scenario in {
                    "output-interruption",
                    "commit-interruption",
                    "missing-file",
                    "inconsistent-console-hash",
                    "status-less-wait",
                }:
                    with pytest.raises(
                        AttemptChargeUncertain,
                        match="complete attempt evidence is uncertain",
                    ):
                        _run(workspace, fixture, case, case_index, output)
                    _assert_uncertain(
                        workspace,
                        fixture,
                        case,
                        case_index,
                        output,
                        launch_counter,
                        environment_result,
                        shell_sentinel,
                    )
                else:
                    result = _run(workspace, fixture, case, case_index, output)
                    _assert_definitive(
                        workspace,
                        fixture,
                        case,
                        case_index,
                        result,
                        output,
                        launch_counter,
                        environment_result,
                        shell_sentinel,
                    )
                    if case.scenario == "nonzero-status":
                        observed_nonzero_statuses.add(result.native_return_code)
                    elif case.scenario == "signal":
                        assert result.termination_signal is not None
                        observed_signals.add(result.termination_signal)
        except Exception as exc:
            exc.add_note(context)
            raise

    assert observed_scenarios == set(_SCENARIOS)
    assert len(observed_nonzero_statuses) >= 5
    assert observed_signals == set(_TERMINATING_SIGNALS)
    assert observed_missing_files == {"attempt.json", "render-console.log"}
