from __future__ import annotations

import io
import json
import os
import socket
import sys
from datetime import UTC, datetime
from pathlib import Path

import pytest

import frontier_audiobook.production_attempt as attempt_module
from frontier_audiobook import narrate
from frontier_audiobook.cli import main
from frontier_audiobook.errors import InputError
from frontier_audiobook.production_attempt import (
    AttemptChargeUncertain,
    run_atomic_paid_attempt,
)
from frontier_audiobook.production_authorization import (
    build_authorization_start_request,
)
from frontier_audiobook.production_models import (
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


def _fixed_clock() -> datetime:
    return datetime(2026, 9, 14, 12, 3, tzinfo=UTC)


@pytest.fixture(autouse=True)
def deny_external_access_and_render(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("attempt tests must remain local and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")


def _hash(character: str) -> str:
    return character * 64


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
            plan_id="plan-attempt-test",
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
            authorization_id="authorization-attempt-test",
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


def _run(workspace: Path, fixture, **kwargs):
    plan, track, authorization, request, store = fixture
    return run_atomic_paid_attempt(
        track,
        authorization,
        plan=plan,
        authorization_start=request,
        workspace_root=workspace,
        store=store,
        clock=_fixed_clock,
        **kwargs,
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


def test_atomic_attempt_consumes_before_direct_child_and_commits_sanitized_result(
    tmp_path,
    monkeypatch,
):
    events_root = _transaction_root(tmp_path) / "events"
    shell_sentinel = tmp_path / "must-not-be-created-by-a-shell"
    raw_stdout = "private-child-output"
    raw_stderr = "transcript-body-must-not-persist"
    script = (
        "import os,sys;from pathlib import Path;"
        "events=Path(next(x[7:] for x in sys.argv if x.startswith('events=')));"
        "literal=next(x for x in sys.argv if x.startswith('literal='));"
        "ok=any(events.glob('*-authorization-consumed.json'));"
        "ok=ok and os.environ.get('AWS_PROFILE')=='frontier-audiobook';"
        "ok=ok and 'AWS_SECRET_ACCESS_KEY' not in os.environ;"
        "ok=ok and 'UNRELATED_SECRET' not in os.environ;"
        "ok=ok and literal.startswith('literal=; touch ');"
        f"sys.stdout.buffer.write(bytes.fromhex('{raw_stdout.encode().hex()}'));"
        f"sys.stderr.buffer.write(bytes.fromhex('{raw_stderr.encode().hex()}'));"
        "sys.exit(0 if ok else 19)"
    )
    argv = (
        sys.executable,
        "-c",
        script,
        f"events={events_root}",
        f"literal=; touch {shell_sentinel}",
    )
    fixture = _ready_attempt(tmp_path, argv)
    captured_replace: dict[str, bool] = {}
    real_replace = attempt_module.durable_replace

    def checked_replace(source, destination, *, source_kind):
        captured_replace["same_filesystem"] = (
            os.stat(source, follow_symlinks=False).st_dev
            == os.stat(destination.parent, follow_symlinks=False).st_dev
        )
        return real_replace(source, destination, source_kind=source_kind)

    monkeypatch.setattr(attempt_module, "durable_replace", checked_replace)
    operator_output = io.StringIO()
    result = _run(
        tmp_path,
        fixture,
        exact_environment={
            "PATH": os.environ.get("PATH", os.defpath),
            "HOME": str(tmp_path),
            "AWS_SECRET_ACCESS_KEY": "credential-value-must-not-persist",
            "UNRELATED_SECRET": "environment-value-must-not-persist",
        },
        output_stream=operator_output,
    )

    plan, track, authorization, _request, store = fixture
    assert result.native_return_code == 0
    assert result.termination_signal is None
    assert result.argv == track.command_argv
    assert result.command_sha256 == track.command_sha256
    assert result.authorization_sha256 == StrictRecordCodec(PaidAuthorization).sha256(
        authorization
    )
    assert result.working_directory == "."
    assert result.profile_label == "frontier-audiobook"
    assert result.automatic_retry_performed is False
    assert result.environment_persisted is False
    assert captured_replace == {"same_filesystem": True}
    assert not shell_sentinel.exists()

    attempt_root = _transaction_root(tmp_path) / "attempts" / "attempt-001"
    assert attempt_root.is_dir()
    assert not tuple(attempt_root.parent.glob("attempt-001.staging-*"))
    persisted = StrictRecordCodec(type(result)).load(attempt_root / "attempt.json")
    assert persisted == result
    console = attempt_root / "render-console.log"
    assert sha256_file(console) == result.console_sha256
    console_text = console.read_text(encoding="utf-8")
    assert raw_stdout not in console_text
    assert raw_stderr not in console_text
    assert raw_stdout not in operator_output.getvalue()
    assert raw_stderr not in operator_output.getvalue()
    for line in console_text.splitlines():
        event = json.loads(line)
        assert set(event) == {
            "byte_count",
            "event",
            "schema_version",
            "sequence",
            "sha256",
        }
        assert event["event"] == "child-output-chunk"
        assert event["byte_count"] > 0

    evidence = b"".join(
        path.read_bytes()
        for path in _transaction_root(tmp_path).rglob("*")
        if path.is_file()
    )
    assert b"credential-value-must-not-persist" not in evidence
    assert b"environment-value-must-not-persist" not in evidence
    assert raw_stdout.encode() not in evidence
    assert raw_stderr.encode() not in evidence

    snapshot = store.inspect_transaction(track.track_id, track.transaction_id)
    assert snapshot.state is TransactionState.RENDERED
    consumed = next(
        payload for payload in snapshot.payloads if payload.event_type == "authorization-consumed"
    )
    assert consumed.details["authorization_sha256"] == result.authorization_sha256
    assert consumed.details["one_shot"] is True
    assert consumed.details["automatic_retry_performed"] is False


def test_known_nonzero_status_is_committed_blocked_and_never_retried(tmp_path):
    counter = tmp_path / "synthetic-child-count"
    script = (
        "import sys;from pathlib import Path;"
        "p=Path(sys.argv[-1]);"
        "n=int(p.read_text()) if p.exists() else 0;"
        "p.write_text(str(n+1));"
        "sys.exit(9)"
    )
    fixture = _ready_attempt(tmp_path, (sys.executable, "-c", script, str(counter)))
    result = _run(tmp_path, fixture, output_stream=io.StringIO())
    assert result.native_return_code == 9
    assert result.automatic_retry_performed is False
    assert counter.read_text(encoding="utf-8") == "1"

    _plan_value, track, _authorization_value, _request, store = fixture
    assert store.inspect_transaction(
        track.track_id, track.transaction_id
    ).state is TransactionState.BLOCKED
    with pytest.raises(InputError, match="not ready"):
        _run(tmp_path, fixture, output_stream=io.StringIO())
    assert counter.read_text(encoding="utf-8") == "1"
    assert len(tuple((_transaction_root(tmp_path) / "attempts").glob("attempt-*"))) == 1


class _FailingOperatorStream:
    def write(self, _value: str) -> int:
        raise OSError("synthetic operator stream interruption")

    def flush(self) -> None:
        return None


def test_incomplete_launched_evidence_becomes_charge_uncertain_without_retry(tmp_path):
    fixture = _ready_attempt(
        tmp_path,
        (sys.executable, "-c", "import sys;sys.stdout.write('x')"),
    )
    with pytest.raises(AttemptChargeUncertain, match="complete attempt evidence"):
        _run(tmp_path, fixture, output_stream=_FailingOperatorStream())

    _plan_value, track, _authorization_value, _request, store = fixture
    snapshot = store.inspect_transaction(track.track_id, track.transaction_id)
    assert snapshot.state is TransactionState.CHARGE_UNCERTAIN
    attempts_root = _transaction_root(tmp_path) / "attempts"
    assert (attempts_root / "attempt-001.ambiguous.json").is_file()
    assert tuple(attempts_root.glob("attempt-001.staging-*"))
    assert not (attempts_root / "attempt-001").exists()
    with pytest.raises(InputError, match="not ready"):
        _run(tmp_path, fixture, output_stream=io.StringIO())


@pytest.mark.parametrize("existing_kind", ("committed", "staging", "ambiguous"))
def test_duplicate_staging_and_ambiguous_attempts_are_refused_before_launch(
    tmp_path,
    existing_kind,
):
    sentinel = tmp_path / "synthetic-child-launched"
    script = "import sys;from pathlib import Path;Path(sys.argv[-1]).write_text('launched')"
    fixture = _ready_attempt(tmp_path, (sys.executable, "-c", script, str(sentinel)))
    attempts_root = _transaction_root(tmp_path) / "attempts"
    attempts_root.mkdir()
    if existing_kind == "committed":
        (attempts_root / "attempt-001").mkdir()
    elif existing_kind == "staging":
        (attempts_root / "attempt-001.staging-existing").mkdir()
    else:
        (attempts_root / "attempt-001.ambiguous.json").write_text("{}", encoding="utf-8")

    with pytest.raises(InputError, match="Duplicate, staging, or ambiguous"):
        _run(tmp_path, fixture, output_stream=io.StringIO())
    assert not sentinel.exists()
    _plan_value, track, _authorization_value, _request, store = fixture
    assert store.inspect_transaction(
        track.track_id, track.transaction_id
    ).state is TransactionState.AUTHORIZATION_REQUIRED


def test_known_prelaunch_failure_consumes_once_and_blocks_without_uncertain_claim(tmp_path):
    missing = tmp_path / "definitely-missing-executable"
    fixture = _ready_attempt(tmp_path, (str(missing), "synthetic-argument"))
    with pytest.raises(InputError, match="did not launch"):
        _run(tmp_path, fixture, output_stream=io.StringIO())

    _plan_value, track, _authorization_value, _request, store = fixture
    assert store.inspect_transaction(
        track.track_id, track.transaction_id
    ).state is TransactionState.BLOCKED
    attempts_root = _transaction_root(tmp_path) / "attempts"
    staging = tuple(attempts_root.glob("attempt-001.staging-*"))
    assert len(staging) == 1
    assert (staging[0] / "launch-failure.json").is_file()
    assert not (attempts_root / "attempt-001.ambiguous.json").exists()
    assert not (attempts_root / "attempt-001").exists()


def test_hidden_generic_worker_entry_is_bound_and_rejects_changed_config_without_rendering(
    tmp_path,
    monkeypatch,
    capsys,
):
    config_path = tmp_path / ".audiobook" / "config" / "production.toml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("# local hidden-worker fixture\n", encoding="utf-8")
    plan_path = tmp_path / "plan.json"
    argv = (
        "frontier-audiobook",
        "_production-worker",
        "--plan",
        "plan.json",
        "--transaction",
        "transaction-001",
        "--track",
        "chapter-001",
    )
    plan = _plan(argv)
    StrictRecordCodec(FrozenBatchPlan).write_atomic(plan_path, plan)
    monkeypatch.setenv("AWS_PROFILE", "frontier-audiobook")

    status = main(
        (
            "--workspace-root",
            str(tmp_path),
            "_production-worker",
            "--plan",
            str(plan_path),
            "--transaction",
            "transaction-001",
            "--track",
            "chapter-001",
        )
    )
    assert status == 2
    assert "configuration differs from the frozen plan" in capsys.readouterr().err
