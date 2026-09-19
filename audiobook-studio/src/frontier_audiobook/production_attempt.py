"""Atomic direct-child capture for one authorized production Track attempt.

This module is the paid-process boundary, but it contains no AWS, narration, or
model integration.  It validates an already-confirmed exact authorization scope,
durably consumes that authorization in the independent Track ledger, launches the
frozen argv directly, and commits sanitized process evidence atomically.
"""

from __future__ import annotations

import os
import re
import secrets
import subprocess
import sys
from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import TextIO

from .errors import InputError
from .production_authorization import (
    AuthorizationStartRequest,
    build_authorization_start_request,
)
from .production_models import (
    RECORD_SCHEMA_VERSION,
    AttemptResult,
    FrozenBatchPlan,
    FrozenTrackPlan,
    PaidAuthorization,
    StrictRecordCodec,
    TransactionState,
    canonical_json_bytes,
    canonical_sha256,
)
from .production_transactions import TransactionSpec, TransactionStore
from .util import (
    atomic_write_bytes,
    durable_mkdir,
    durable_replace,
    fsync_directory,
    sha256_file,
    utc_now,
    workspace_relative,
)

Clock = Callable[[], datetime]

_ATTEMPT_ID = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SAFE_CHILD_ENVIRONMENT = (
    "PATH",
    "HOME",
    "USERPROFILE",
    "SYSTEMROOT",
    "SystemRoot",
    "WINDIR",
    "COMSPEC",
    "PATHEXT",
    "TEMP",
    "TMP",
    "TMPDIR",
    "LANG",
    "LC_ALL",
    "LC_CTYPE",
    "VIRTUAL_ENV",
    "SSL_CERT_FILE",
    "SSL_CERT_DIR",
)
_CONSOLE_CHUNK_SIZE = 64 * 1024


class AttemptChargeUncertain(InputError):
    """A child launched but complete committed evidence could not be proven."""


def _system_clock() -> datetime:
    return datetime.now(UTC)


def _clock_now(clock: Clock) -> datetime:
    try:
        value = clock()
    except Exception as exc:
        raise InputError("Attempt clock failed") from exc
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise InputError("Attempt clock must return a timezone-aware datetime")
    return value.astimezone(UTC)


def _format_utc(value: datetime) -> str:
    rendered = value.astimezone(UTC).isoformat(timespec="microseconds")
    if rendered.endswith(".000000+00:00"):
        rendered = rendered.replace(".000000+00:00", "Z")
    else:
        rendered = rendered.replace("+00:00", "Z")
    return rendered


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.removesuffix("Z") + "+00:00")


def _require_attempt_id(value: str) -> str:
    if not isinstance(value, str) or not _ATTEMPT_ID.fullmatch(value):
        raise InputError("attempt_id must be a lowercase hyphenated identifier")
    return value


def _validate_attempt_bindings(
    plan: FrozenBatchPlan,
    transaction: FrozenTrackPlan,
    authorization: PaidAuthorization,
    authorization_start: AuthorizationStartRequest,
    store: TransactionStore,
    now: datetime,
) -> str:
    """Recheck immutable execution bindings without expanding authorized scope.

    ``authorization_start`` must be the exact request already accepted by Task 4.1's
    complete preflight-aware validator.  The wrapper repeats all facts it can verify
    from immutable local inputs immediately before consumption.
    """

    plan_codec = StrictRecordCodec(FrozenBatchPlan)
    authorization_codec = StrictRecordCodec(PaidAuthorization)
    plan_codec.dump_bytes(plan)
    authorization_codec.dump_bytes(authorization)
    if not isinstance(transaction, FrozenTrackPlan):
        raise InputError("Atomic attempt requires FrozenTrackPlan")
    if not isinstance(authorization_start, AuthorizationStartRequest):
        raise InputError("Atomic attempt requires AuthorizationStartRequest")
    if not isinstance(store, TransactionStore):
        raise InputError("Atomic attempt requires TransactionStore")
    if store.book_id != plan.book_id:
        raise InputError("Transaction store book identity differs from the frozen plan")

    matches = tuple(item for item in plan.tracks if item.track_id == transaction.track_id)
    if len(matches) != 1 or matches[0] != transaction:
        raise InputError("Attempt Track is not the exact frozen Track plan")
    if transaction.command_sha256 != canonical_sha256(transaction.command_argv):
        raise InputError("Frozen direct-child argv hash is inconsistent")

    plan_sha256 = plan_codec.sha256(plan)
    authorization_sha256 = authorization_codec.sha256(authorization)
    if authorization.plan_sha256 != plan_sha256:
        raise InputError("Paid authorization is not bound to the exact frozen plan")
    if authorization_start != build_authorization_start_request(authorization):
        raise InputError("Authorization start scope is altered, incomplete, or unlisted")

    expected_transactions = tuple(item.transaction_id for item in plan.tracks)
    expected_tracks = tuple(item.track_id for item in plan.tracks)
    expected_commands = tuple(item.command_sha256 for item in plan.tracks)
    if authorization.exact_transaction_ids != expected_transactions:
        raise InputError("Paid authorization transaction scope differs from the plan")
    if authorization.exact_track_ids != expected_tracks:
        raise InputError("Paid authorization Track scope differs from the plan")
    if authorization.exact_command_sha256s != expected_commands:
        raise InputError("Paid authorization command scope differs from the plan")
    if authorization.maximum_new_calls_by_track[transaction.track_id] > transaction.maximum_new_calls:
        raise InputError("Paid authorization call ceiling exceeds the frozen Track bound")

    issued = _parse_utc(authorization.issued_at_utc)
    expires = _parse_utc(authorization.expires_at_utc)
    if now < issued:
        raise InputError("Paid authorization is not yet valid")
    if now >= expires:
        raise InputError("Paid authorization is expired")
    if not authorization.one_shot:
        raise InputError("Paid authorization must be one-shot")
    return authorization_sha256


def _child_environment(
    profile_label: str,
    exact_environment: Mapping[str, str] | None,
) -> dict[str, str]:
    """Build a minimal child environment and discard all credential variables."""

    source: Mapping[str, str] = os.environ if exact_environment is None else exact_environment
    if not isinstance(source, Mapping):
        raise InputError("exact_environment must be a string mapping")
    child: dict[str, str] = {}
    for name in _SAFE_CHILD_ENVIRONMENT:
        if name not in source:
            continue
        value = source[name]
        if not isinstance(value, str) or "\x00" in value:
            raise InputError(f"Child environment {name} must be a NUL-free string")
        child[name] = value
    child.setdefault("PATH", os.defpath)
    child["PYTHONUNBUFFERED"] = "1"
    child["AWS_PROFILE"] = profile_label
    return child


def _attempt_entries(attempts_root: Path, attempt_id: str) -> tuple[Path, ...]:
    if not os.path.lexists(attempts_root):
        return ()
    if attempts_root.is_symlink() or not attempts_root.is_dir():
        raise InputError("Attempt root is missing, unsafe, or ambiguous")
    try:
        entries = tuple(attempts_root.iterdir())
    except OSError as exc:
        raise InputError("Attempt root cannot be inspected safely") from exc
    return entries


def _write_marker(path: Path, value: Mapping[str, object]) -> None:
    """Write one sanitized marker without replacing prior evidence."""

    if os.path.lexists(path):
        return
    try:
        from .production_evidence import EvidenceArtifactKind, assert_evidence_safe

        assert_evidence_safe(
            EvidenceArtifactKind.ATTEMPT_RESULT,
            value,
            artifact_path=path.name,
        )
        atomic_write_bytes(path, canonical_json_bytes(value))
    except BaseException:
        # The immutable ledger transition remains the primary truth.  Marker write
        # failure must never trigger a second launch or obscure the original error.
        return


def _mark_charge_uncertain(
    store: TransactionStore,
    transaction: FrozenTrackPlan,
    attempts_root: Path,
    attempt_id: str,
    authorization_sha256: str,
    occurred_at_utc: str,
    *,
    launch_status: str,
) -> None:
    durable_mkdir(attempts_root)
    _write_marker(
        attempts_root / f"{attempt_id}.ambiguous.json",
        {
            "schema_version": RECORD_SCHEMA_VERSION,
            "attempt_id": attempt_id,
            "transaction_id": transaction.transaction_id,
            "authorization_sha256": authorization_sha256,
            "finding_category": "incomplete-launched-attempt-evidence",
            "child_launch_status": launch_status,
            "automatic_retry_performed": False,
            "environment_persisted": False,
        },
    )
    try:
        store.append_transition(
            transaction.track_id,
            transaction.transaction_id,
            operation_id=f"{attempt_id}-charge-uncertain",
            event_type="attempt-charge-uncertain",
            state_after=TransactionState.CHARGE_UNCERTAIN,
            details={
                "attempt_id": attempt_id,
                "authorization_sha256": authorization_sha256,
                "finding_category": "incomplete-launched-attempt-evidence",
                "child_launch_status": launch_status,
                "automatic_retry_performed": False,
            },
            occurred_at_utc=occurred_at_utc,
        )
    except BaseException:
        # Retain the marker and any staging bytes.  A future inspector must treat
        # RUNNING plus those artifacts as uncertain; never retry from this path.
        return


def _mark_prelaunch_blocked(
    store: TransactionStore,
    transaction: FrozenTrackPlan,
    staging: Path,
    attempt_id: str,
    authorization_sha256: str,
    occurred_at_utc: str,
) -> None:
    _write_marker(
        staging / "launch-failure.json",
        {
            "schema_version": RECORD_SCHEMA_VERSION,
            "attempt_id": attempt_id,
            "transaction_id": transaction.transaction_id,
            "authorization_sha256": authorization_sha256,
            "finding_category": "direct-child-not-launched",
            "child_launched": False,
            "automatic_retry_performed": False,
            "environment_persisted": False,
        },
    )
    try:
        fsync_directory(staging)
    except BaseException:
        pass
    try:
        store.append_transition(
            transaction.track_id,
            transaction.transaction_id,
            operation_id=f"{attempt_id}-launch-blocked",
            event_type="attempt-launch-blocked",
            state_after=TransactionState.BLOCKED,
            details={
                "attempt_id": attempt_id,
                "authorization_sha256": authorization_sha256,
                "finding_category": "direct-child-not-launched",
                "child_launched": False,
                "automatic_retry_performed": False,
            },
            occurred_at_utc=occurred_at_utc,
        )
    except BaseException:
        return


def _stream_sanitized_output(
    pipe: object,
    log_handle: object,
    output_stream: TextIO,
) -> None:
    """Stream hash/size metadata only; raw child bytes are never echoed or stored."""

    read = getattr(pipe, "read1", None) or getattr(pipe, "read", None)
    if read is None:
        raise InputError("Direct child stdout pipe is unavailable")
    sequence = 0
    while True:
        chunk = read(_CONSOLE_CHUNK_SIZE)
        if not chunk:
            break
        if not isinstance(chunk, bytes):
            raise InputError("Direct child output pipe must be binary")
        sequence += 1
        sanitized = canonical_json_bytes(
            {
                "schema_version": RECORD_SCHEMA_VERSION,
                "event": "child-output-chunk",
                "sequence": sequence,
                "byte_count": len(chunk),
                "sha256": canonical_sha256(chunk.hex()),
            }
        ) + b"\n"
        log_handle.write(sanitized)
        log_handle.flush()
        output_stream.write(sanitized.decode("utf-8"))
        output_stream.flush()


def _open_console_log(path: Path):
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor = os.open(path, flags, 0o600)
    return os.fdopen(descriptor, "wb")


def run_atomic_paid_attempt(
    transaction: FrozenTrackPlan,
    authorization: PaidAuthorization,
    *,
    plan: FrozenBatchPlan,
    authorization_start: AuthorizationStartRequest,
    workspace_root: Path,
    store: TransactionStore,
    exact_environment: Mapping[str, str] | None = None,
    output_stream: TextIO | None = None,
    attempt_id: str = "attempt-001",
    clock: Clock = _system_clock,
) -> AttemptResult:
    """Run exactly one frozen direct child and atomically commit its evidence.

    This function never invokes a shell and never retries.  The caller must first
    pass ``authorization_start`` through Task 4.1's complete authorization validator.
    The independent Track ledger is rechecked and moved to ``running`` durably before
    ``Popen`` is called, which is the one-shot consumption point.
    """

    checked_attempt_id = _require_attempt_id(attempt_id)
    root = workspace_root.expanduser().resolve()
    workspace_relative(root, store.book_root)
    checked_now = _clock_now(clock)
    authorization_sha256 = _validate_attempt_bindings(
        plan,
        transaction,
        authorization,
        authorization_start,
        store,
        checked_now,
    )
    child_environment = _child_environment(
        transaction.effective_config.profile_label,
        exact_environment,
    )
    sink = sys.stdout if output_stream is None else output_stream
    if not hasattr(sink, "write") or not hasattr(sink, "flush"):
        raise InputError("output_stream must be a writable text stream")

    spec = TransactionSpec.from_plan(plan, transaction)
    transaction_root = store.transaction_path(
        transaction.track_id, transaction.transaction_id
    )
    workspace_relative(root, transaction_root)
    attempts_root = transaction_root / "attempts"
    final = attempts_root / checked_attempt_id
    ambiguity_due_to_running = False

    with store.track_lock(transaction.track_id):
        snapshot = store.inspect_transaction(
            transaction.track_id, transaction.transaction_id
        )
        if not snapshot.metadata.matches(spec):
            raise InputError("Transaction identity differs from the frozen Track plan")
        existing = _attempt_entries(attempts_root, checked_attempt_id)
        if snapshot.state is TransactionState.RUNNING:
            ambiguity_due_to_running = True
        elif snapshot.state is not TransactionState.AUTHORIZATION_REQUIRED:
            raise InputError("Track transaction is not ready for a first paid attempt")
        elif existing:
            raise InputError("Duplicate, staging, or ambiguous attempt evidence already exists")
        else:
            if snapshot.payloads[-1].details.get("preflight_sha256") != authorization.preflight_sha256:
                raise InputError("Transaction preflight binding differs from authorization")
            durable_mkdir(attempts_root)
            staging = attempts_root / (
                f"{checked_attempt_id}.staging-{secrets.token_hex(8)}"
            )
            staging.mkdir(mode=0o700)
            fsync_directory(attempts_root)
            if os.stat(staging, follow_symlinks=False).st_dev != os.stat(
                attempts_root, follow_symlinks=False
            ).st_dev:
                raise InputError("Attempt staging is not on the destination filesystem")

    occurred_at_utc = _format_utc(checked_now)
    if ambiguity_due_to_running:
        _mark_charge_uncertain(
            store,
            transaction,
            attempts_root,
            checked_attempt_id,
            authorization_sha256,
            occurred_at_utc,
            launch_status="unknown",
        )
        raise AttemptChargeUncertain(
            "Previously consumed attempt has incomplete evidence; charge is uncertain"
        )

    # ``staging`` is assigned only by the sole AUTHORIZATION_REQUIRED branch above.
    try:
        staging
    except UnboundLocalError as exc:  # pragma: no cover - defensive invariant
        raise InputError("Attempt staging was not reserved") from exc

    store.append_transition(
        transaction.track_id,
        transaction.transaction_id,
        operation_id=f"{checked_attempt_id}-authorization-consumed",
        event_type="authorization-consumed",
        state_after=TransactionState.RUNNING,
        details={
            "attempt_id": checked_attempt_id,
            "authorization_sha256": authorization_sha256,
            "command_sha256": transaction.command_sha256,
            "maximum_new_calls": authorization.maximum_new_calls_by_track[
                transaction.track_id
            ],
            "one_shot": True,
            "automatic_retry_performed": False,
        },
        occurred_at_utc=occurred_at_utc,
    )

    child_launched = False
    bundle_committed = False
    process: subprocess.Popen[bytes] | None = None
    log_handle = None
    console_staging = staging / "render-console.log"
    try:
        log_handle = _open_console_log(console_staging)
        started_at_utc = _format_utc(_clock_now(clock))
        process = subprocess.Popen(
            transaction.command_argv,
            cwd=root,
            env=child_environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=False,
            close_fds=True,
            bufsize=0,
        )
        child_launched = True
        if process.stdout is None:  # pragma: no cover - guaranteed by stdout=PIPE
            raise InputError("Direct child stdout pipe was not created")
        try:
            _stream_sanitized_output(process.stdout, log_handle, sink)
        finally:
            process.stdout.close()
        native_return_code = process.wait()
        if type(native_return_code) is not int:
            raise InputError("Popen.wait() did not return an integer native status")
        ended_at_utc = _format_utc(_clock_now(clock))

        log_handle.flush()
        os.fsync(log_handle.fileno())
        log_handle.close()
        log_handle = None
        from .production_evidence import (
            assert_sanitized_console,
            assert_typed_evidence_safe,
            private_environment_values,
        )
        from .util import read_bytes_nofollow, sha256_bytes

        console_raw = read_bytes_nofollow(console_staging)
        private_values = private_environment_values(
            exact_environment,
            allowed_names=(*_SAFE_CHILD_ENVIRONMENT, "AWS_PROFILE", "PYTHONUNBUFFERED"),
        )
        assert_sanitized_console(
            console_raw,
            artifact_path=workspace_relative(root, console_staging),
            sensitive_values=private_values,
        )
        console_sha256 = sha256_bytes(console_raw)
        console_final = final / "render-console.log"
        result = AttemptResult(
            schema_version=RECORD_SCHEMA_VERSION,
            attempt_id=checked_attempt_id,
            transaction_id=transaction.transaction_id,
            authorization_sha256=authorization_sha256,
            working_directory=workspace_relative(root, root),
            argv=transaction.command_argv,
            command_sha256=transaction.command_sha256,
            profile_label=transaction.effective_config.profile_label,
            started_at_utc=started_at_utc,
            ended_at_utc=ended_at_utc,
            child_launched=True,
            native_return_code=native_return_code,
            termination_signal=(
                -native_return_code if native_return_code < 0 else None
            ),
            console_path=workspace_relative(root, console_final),
            console_sha256=console_sha256,
            automatic_retry_performed=False,
            environment_persisted=False,
        )
        assert_typed_evidence_safe(
            result,
            sensitive_values=private_values,
        )
        result_codec = StrictRecordCodec(AttemptResult)
        result_codec.write_atomic(staging / "attempt.json", result)
        if result_codec.load(staging / "attempt.json") != result:
            raise InputError("Committed attempt result did not round-trip exactly")
        if sha256_file(console_staging) != result.console_sha256:
            raise InputError("Sanitized console digest changed before commit")
        fsync_directory(staging)
        durable_replace(staging, final, source_kind="directory")
        fsync_directory(attempts_root)
        bundle_committed = True

        if native_return_code == 0:
            next_state = TransactionState.RENDERED
            event_type = "attempt-rendered"
            operation_id = f"{checked_attempt_id}-rendered"
        else:
            next_state = TransactionState.BLOCKED
            event_type = "attempt-nonzero"
            operation_id = f"{checked_attempt_id}-blocked"
        store.append_transition(
            transaction.track_id,
            transaction.transaction_id,
            operation_id=operation_id,
            event_type=event_type,
            state_after=next_state,
            details={
                "attempt_id": checked_attempt_id,
                "authorization_sha256": authorization_sha256,
                "attempt_result_sha256": result_codec.sha256(result),
                "console_sha256": result.console_sha256,
                "native_return_code": native_return_code,
                "termination_signal": result.termination_signal,
                "automatic_retry_performed": False,
            },
            occurred_at_utc=ended_at_utc,
        )
        return result
    except BaseException as exc:
        if log_handle is not None:
            try:
                log_handle.flush()
                os.fsync(log_handle.fileno())
            except BaseException:
                pass
            try:
                log_handle.close()
            except BaseException:
                pass
        failure_time = _format_utc(_clock_now(clock))
        if child_launched:
            _mark_charge_uncertain(
                store,
                transaction,
                attempts_root,
                checked_attempt_id,
                authorization_sha256,
                failure_time,
                launch_status="confirmed",
            )
            location = final if bundle_committed else staging
            raise AttemptChargeUncertain(
                f"Direct child launched but complete attempt evidence is uncertain at {workspace_relative(root, location)}"
            ) from exc
        _mark_prelaunch_blocked(
            store,
            transaction,
            staging,
            checked_attempt_id,
            authorization_sha256,
            failure_time,
        )
        raise InputError(
            "Direct child did not launch; authorization was consumed and the transaction is blocked"
        ) from exc


__all__ = [
    "AttemptChargeUncertain",
    "run_atomic_paid_attempt",
]
