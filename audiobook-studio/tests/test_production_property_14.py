"""Deterministic generated checks for audiobook production correctness Property 14."""

from __future__ import annotations

import hashlib
import json
import os
import random
import socket
import string
from dataclasses import asdict, dataclass, fields
from pathlib import Path

import pytest

from frontier_audiobook import narrate, nova, production_attempt
from frontier_audiobook.errors import InputError
from frontier_audiobook.production_evidence import (
    EvidenceArtifactKind,
    EvidenceSanitizationError,
    SanitizationFinding,
    assert_evidence_safe,
    assert_identity_projection,
    assert_sanitized_console,
    forbidden_field_values,
    private_environment_values,
    resolve_private_runtime_path,
    scan_evidence_bytes,
    scan_evidence_value,
    scan_identity_projection,
    scan_sanitized_console,
    write_immutable_bytes,
)
from frontier_audiobook.production_models import RECORD_SCHEMA_VERSION
from frontier_audiobook.production_preflight import (
    IdentityEvidence,
    resolve_minimal_identity_evidence,
)
from frontier_audiobook.util import resolve_inside_approved_root


PROPERTY_TAG = (
    "Feature: audiobook-production-workflow, Property 14: "
    "Evidence and identity persistence obey explicit allowlists"
)
PROPERTY_SEED = 0xA0D10B0E
GENERATED_CASES = 128

# **Validates: Requirements 3.9, 4.9, 7.4, 7.5, 7.11, 15.1, 15.2,
# 15.3, 15.4, 15.5, 15.6, 15.7, 15.8, 15.9**

_PATH_ATTACKS = ("outside-root", "traversal", "absolute", "symlink")
_APPROVED_ROOT_KINDS = ("source", "evidence", "delivery", "runtime")
_HISTORY_STATES = ("blocked", "charge-uncertain")
_NATIVE_RETURN_CODES = (0, 1, 73, -15)
_UNICODE_MARKERS = ("Ω", "雪", "ñ", "λ", "Ж")

_IDENTITY_FIELDS = frozenset({"profile_label", "resolved", "checked_at_utc"})
_PLAN_FIELDS = frozenset(
    {
        "schema_version",
        "plan_id",
        "created_at_utc",
        "book_id",
        "config_path",
        "config_sha256",
        "selectors",
        "tracks",
        "canonical_sha256",
    }
)
_ATTEMPT_RESULT_FIELDS = frozenset(
    {
        "schema_version",
        "attempt_id",
        "transaction_id",
        "authorization_sha256",
        "working_directory",
        "argv",
        "command_sha256",
        "profile_label",
        "started_at_utc",
        "ended_at_utc",
        "child_launched",
        "native_return_code",
        "termination_signal",
        "console_path",
        "console_sha256",
        "automatic_retry_performed",
        "environment_persisted",
    }
)
_EXPECTED_FORBIDDEN_CATEGORIES = frozenset(
    {
        "credential-field",
        "credential-value",
        "environment-field",
        "environment-value",
        "identity-detail-field",
        "identity-detail-value",
        "private-value",
        "prose-or-transcript-field",
        "raw-event-field",
        "raw-event-value",
        "schema-not-allowlisted",
    }
)


@dataclass(frozen=True, slots=True)
class _GeneratedCase:
    case_index: int
    nonce: str
    identity_succeeds: bool
    path_attack: str
    approved_root_kind: str
    history_state: str
    native_return_code: int
    console_chunks: int


@dataclass(frozen=True, slots=True)
class _PrivateValues:
    account_id: str
    arn: str
    role_id: str
    user_id: str
    access_key: str
    secret_credential: str
    session_token: str
    credential_type: str
    credential_source: str
    credential_age: str
    credential_expiration: str
    source_body: str
    segment_text: str
    transcript_body: str
    raw_event_payload: str
    environment_dump: str
    other_identity_field: str

    def all(self) -> tuple[str, ...]:
        return tuple(
            sorted(
                {getattr(self, field.name) for field in fields(self)},
                key=lambda item: (len(item), item),
            )
        )

    def leaked_fields(self, raw_identity: object) -> dict[str, object]:
        return {
            "account_id": self.account_id,
            "arn": self.arn,
            "role_id": self.role_id,
            "user_id": self.user_id,
            "access_key": self.access_key,
            "credential_value": self.secret_credential,
            "session_token": self.session_token,
            "credential_type": self.credential_type,
            "credential_source": self.credential_source,
            "credential_age": self.credential_age,
            "credential_expiration": self.credential_expiration,
            "body": self.source_body,
            "segment_text": self.segment_text,
            "transcript_body": self.transcript_body,
            "raw_event_journal": self.raw_event_payload,
            "environment_dump": self.environment_dump,
            "identity_response": raw_identity,
        }


@pytest.fixture(autouse=True)
def deny_network_aws_model_narration_and_children(monkeypatch, tmp_path):
    """Fail immediately if Property 14 crosses a forbidden execution boundary."""

    def blocked(*_args, **_kwargs):
        raise AssertionError("Property 14 must remain local, offline, and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setattr(nova, "render_text", blocked)
    monkeypatch.setattr(production_attempt.subprocess, "Popen", blocked)
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


def _generated_case(rng: random.Random, case_index: int) -> _GeneratedCase:
    return _GeneratedCase(
        case_index=case_index,
        nonce="".join(rng.choice(string.ascii_letters + string.digits) for _ in range(18)),
        identity_succeeds=case_index % 3 != 0,
        path_attack=_PATH_ATTACKS[case_index % len(_PATH_ATTACKS)],
        approved_root_kind=_APPROVED_ROOT_KINDS[
            case_index % len(_APPROVED_ROOT_KINDS)
        ],
        history_state=_HISTORY_STATES[case_index % len(_HISTORY_STATES)],
        native_return_code=_NATIVE_RETURN_CODES[
            case_index % len(_NATIVE_RETURN_CODES)
        ],
        console_chunks=1 + rng.randrange(4),
    )


def _private_values(rng: random.Random, case: _GeneratedCase) -> _PrivateValues:
    account_id = "".join(str(rng.randrange(10)) for _ in range(12))
    access_key = "AKIA" + "".join(
        rng.choice(string.ascii_uppercase + string.digits) for _ in range(16)
    )
    marker = _UNICODE_MARKERS[case.case_index % len(_UNICODE_MARKERS)]
    secret_credential = f"credential-{case.nonce}-{rng.getrandbits(48):012x}"
    return _PrivateValues(
        account_id=account_id,
        arn=f"arn:aws:iam::{account_id}:role/private-{case.nonce}",
        role_id=f"private-role-id-{case.nonce}",
        user_id=f"AIDA{case.nonce.upper()}PRIVATE",
        access_key=access_key,
        secret_credential=secret_credential,
        session_token=f"session-token-{case.nonce}-{rng.getrandbits(40):010x}",
        credential_type=f"temporary-{case.nonce}",
        credential_source=f"provider-chain-{case.nonce}",
        credential_age=f"age-seconds-{rng.randrange(1, 100_000)}-{case.nonce}",
        credential_expiration=(
            f"2027-{1 + case.case_index % 12:02d}-"
            f"{1 + case.case_index % 28:02d}T23:59:59Z-{case.nonce}"
        ),
        source_body=f"Source prose {marker} belongs only to case {case.nonce}.",
        segment_text=f"Segment text {marker} remains private for {case.nonce}.",
        transcript_body=f"FINAL transcript {marker} remains private for {case.nonce}.",
        raw_event_payload=(
            '{"audioOutput":{"content":"private-'
            f"{case.nonce}" + '"},"usageEvent":{"totalTokens":17}}'
        ),
        environment_dump=(
            f"AWS_ACCESS_KEY_ID={access_key} "
            f"AWS_SECRET_ACCESS_KEY={secret_credential}"
        ),
        other_identity_field=f"identity-extension-{marker}-{case.nonce}",
    )


def _raw_identity_response(
    profile_label: str,
    values: _PrivateValues,
) -> dict[str, object]:
    return {
        "ResolvedProfile": profile_label,
        "Account": values.account_id,
        "Arn": values.arn,
        "RoleId": values.role_id,
        "UserId": values.user_id,
        "Credentials": {
            "AccessKeyId": values.access_key,
            "SecretAccessKey": values.secret_credential,
            "SessionToken": values.session_token,
            "Type": values.credential_type,
            "Source": values.credential_source,
            "Age": values.credential_age,
            "Expiration": values.credential_expiration,
        },
        "SourceBody": values.source_body,
        "Transcript": values.transcript_body,
        "Events": values.raw_event_payload,
        "Environment": values.environment_dump,
        "FutureIdentityField": values.other_identity_field,
    }


def _sha256(label: str, case: _GeneratedCase) -> str:
    return hashlib.sha256(f"{label}:{case.case_index}:{case.nonce}".encode()).hexdigest()


def _canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _canonical_line(value: object) -> bytes:
    return _canonical_bytes(value) + b"\n"


def _assert_no_private_echo(rendered: object, private_values: tuple[str, ...]) -> None:
    text = str(rendered)
    for private in private_values:
        assert private not in text


def _safe_plan(case: _GeneratedCase) -> dict[str, object]:
    track_id = f"property-14-track-{case.case_index:03d}"
    return {
        "schema_version": RECORD_SCHEMA_VERSION,
        "plan_id": f"property-14-plan-{case.case_index:03d}",
        "created_at_utc": "2026-09-14T12:00:00Z",
        "book_id": "property-14-book",
        "config_path": "audiobook-studio/config/production.toml",
        "config_sha256": _sha256("config", case),
        "selectors": [f"track:{track_id}"],
        "tracks": [
            {
                "transaction_id": f"property-14-transaction-{case.case_index:03d}",
                "track_id": track_id,
                "source_path": f"manuscript/property-14/source-{case.case_index:03d}.md",
                "source_sha256": _sha256("source", case),
                "segment_count": 1 + case.case_index % 19,
                "command_sha256": _sha256("command", case),
            }
        ],
        "canonical_sha256": _sha256("plan", case),
    }


def _safe_attempt_result(
    case: _GeneratedCase,
    profile_label: str,
) -> dict[str, object]:
    return {
        "schema_version": RECORD_SCHEMA_VERSION,
        "attempt_id": f"attempt-{case.case_index:03d}",
        "transaction_id": f"property-14-transaction-{case.case_index:03d}",
        "authorization_sha256": _sha256("authorization", case),
        "working_directory": "audiobook-studio/build/production/property-14-book",
        "argv": [
            "python",
            "-m",
            "frontier_audiobook.production_worker",
            "--transaction",
            f"property-14-transaction-{case.case_index:03d}",
        ],
        "command_sha256": _sha256("command", case),
        "profile_label": profile_label,
        "started_at_utc": "2026-09-14T12:00:00Z",
        "ended_at_utc": "2026-09-14T12:00:01Z",
        "child_launched": True,
        "native_return_code": case.native_return_code,
        "termination_signal": (
            -case.native_return_code if case.native_return_code < 0 else None
        ),
        "console_path": (
            "audiobook-studio/build/production/property-14-book/transactions/"
            f"property-14-track-{case.case_index:03d}/attempts/attempt-001/"
            "render-console.log"
        ),
        "console_sha256": _sha256("console", case),
        "automatic_retry_performed": False,
        "environment_persisted": False,
    }


def _safe_console(case: _GeneratedCase) -> bytes:
    return b"".join(
        _canonical_line(
            {
                "schema_version": RECORD_SCHEMA_VERSION,
                "event": "child-output-chunk",
                "sequence": sequence,
                "byte_count": 1 + (case.case_index + sequence) % 65_536,
                "sha256": _sha256(f"console-chunk-{sequence}", case),
            }
        )
        for sequence in range(1, case.console_chunks + 1)
    )


def _exercise_identity_projection(
    case: _GeneratedCase,
    profile_label: str,
    raw_identity: dict[str, object],
    values: _PrivateValues,
) -> None:
    calls: list[str] = []

    def identity_call(requested_profile: str) -> object:
        calls.append(requested_profile)
        if case.identity_succeeds:
            return raw_identity
        raise RuntimeError(f"synthetic identity failure {values.secret_credential}")

    checked_at_utc = (
        f"2026-09-{1 + case.case_index % 28:02d}T"
        f"{case.case_index % 24:02d}:{case.case_index % 60:02d}:00Z"
    )
    projected = resolve_minimal_identity_evidence(
        (profile_label, profile_label),
        identity_call,
        checked_at_utc=checked_at_utc,
    )
    assert calls == [profile_label]
    assert len(projected) == 1
    identity = projected[0]
    identity_data = asdict(identity)
    assert set(identity_data) == _IDENTITY_FIELDS
    assert identity_data == {
        "profile_label": profile_label,
        "resolved": case.identity_succeeds,
        "checked_at_utc": checked_at_utc,
    }
    assert scan_identity_projection(identity, raw_response=raw_identity) == ()
    assert_identity_projection(identity, raw_response=raw_identity)
    _assert_no_private_echo(identity, values.all())

    leaked_identity = {
        **identity_data,
        "identity_response": raw_identity,
        "credential_value": values.secret_credential,
    }
    findings = scan_identity_projection(leaked_identity, raw_response=raw_identity)
    categories = {finding.category for finding in findings}
    assert {
        "identity-projection-not-allowlisted",
        "identity-detail-field",
        "credential-field",
        "private-value",
    } <= categories
    _assert_no_private_echo(findings, values.all())
    with pytest.raises(EvidenceSanitizationError) as caught:
        assert_identity_projection(leaked_identity, raw_response=raw_identity)
    _assert_no_private_echo(caught.value, values.all())


def _exercise_environment_and_console(
    case: _GeneratedCase,
    profile_label: str,
    values: _PrivateValues,
) -> bytes:
    exact_environment = {
        "PATH": f"/safe/property-14/{case.case_index:03d}",
        "LANG": "C.UTF-8",
        "AWS_PROFILE": values.other_identity_field,
        "PYTHONUNBUFFERED": values.session_token,
        "AWS_ACCESS_KEY_ID": values.access_key,
        "AWS_SECRET_ACCESS_KEY": values.secret_credential,
        "AWS_SESSION_TOKEN": values.session_token,
        "PROPERTY_14_CREDENTIAL": values.environment_dump,
    }
    child_environment = production_attempt._child_environment(  # noqa: SLF001
        profile_label,
        exact_environment,
    )
    assert child_environment == {
        "PATH": exact_environment["PATH"],
        "LANG": exact_environment["LANG"],
        "PYTHONUNBUFFERED": "1",
        "AWS_PROFILE": profile_label,
    }
    for private in values.all():
        assert private not in child_environment.values()

    excluded_environment_values = private_environment_values(
        exact_environment,
        allowed_names=("PATH", "LANG", "AWS_PROFILE", "PYTHONUNBUFFERED"),
    )
    assert excluded_environment_values == tuple(
        sorted(
            {
                values.access_key,
                values.secret_credential,
                values.session_token,
                values.environment_dump,
            },
            key=lambda item: (len(item), item),
        )
    )

    safe_console = _safe_console(case)
    assert (
        scan_sanitized_console(
            safe_console,
            artifact_path=(
                f"transactions/property-14-{case.case_index:03d}/"
                "attempts/attempt-001/render-console.log"
            ),
            sensitive_values=excluded_environment_values,
        )
        == ()
    )

    unsafe_console = _canonical_line(
        {
            "schema_version": RECORD_SCHEMA_VERSION,
            "event": "child-output-chunk",
            "sequence": 1,
            "byte_count": len(values.transcript_body.encode("utf-8")),
            "sha256": _sha256("unsafe-console", case),
            "transcript_body": values.transcript_body,
            "environment_dump": values.environment_dump,
        }
    )
    unsafe_path = (
        f"transactions/property-14-{case.case_index:03d}/"
        "attempts/attempt-unsafe/render-console.log"
    )
    findings = scan_sanitized_console(
        unsafe_console,
        artifact_path=unsafe_path,
        sensitive_values=values.all(),
    )
    assert {
        "console-schema-invalid",
        "credential-value",
        "environment-field",
        "environment-value",
        "private-value",
        "prose-or-transcript-field",
    } <= {finding.category for finding in findings}
    _assert_no_private_echo(findings, values.all())
    with pytest.raises(EvidenceSanitizationError) as caught:
        assert_sanitized_console(
            unsafe_console,
            artifact_path=unsafe_path,
            sensitive_values=values.all(),
        )
    _assert_no_private_echo(caught.value, values.all())
    return safe_console


def _exercise_evidence_allowlists(
    case: _GeneratedCase,
    profile_label: str,
    raw_identity: dict[str, object],
    values: _PrivateValues,
    safe_console: bytes,
) -> tuple[bytes, bytes, set[str]]:
    plan = _safe_plan(case)
    assert set(plan) == _PLAN_FIELDS
    plan_path = f"plans/property-14-{case.case_index:03d}/plan.json"
    plan_bytes = _canonical_bytes(plan)
    assert scan_evidence_value(
        EvidenceArtifactKind.PLAN,
        plan,
        artifact_path=plan_path,
        sensitive_values=values.all(),
    ) == ()
    assert scan_evidence_bytes(
        EvidenceArtifactKind.PLAN,
        plan_bytes,
        artifact_path=plan_path,
        sensitive_values=values.all(),
    ) == ()

    unknown_only = {
        **plan,
        f"unexpected_{case.nonce.casefold()}": False,
    }
    unknown_findings = scan_evidence_value(
        EvidenceArtifactKind.PLAN,
        unknown_only,
        artifact_path=plan_path,
    )
    assert {finding.category for finding in unknown_findings} == {
        "schema-not-allowlisted"
    }

    leaked_fields = values.leaked_fields(raw_identity)
    extracted = forbidden_field_values(leaked_fields)
    assert set(values.all()) <= set(extracted)
    leaked_plan = {**plan, **leaked_fields}
    findings = scan_evidence_value(
        EvidenceArtifactKind.PLAN,
        leaked_plan,
        artifact_path=plan_path,
        sensitive_values=values.all(),
    )
    categories = {finding.category for finding in findings}
    assert _EXPECTED_FORBIDDEN_CATEGORIES <= categories
    _assert_no_private_echo(findings, values.all())
    with pytest.raises(EvidenceSanitizationError) as caught:
        assert_evidence_safe(
            EvidenceArtifactKind.PLAN,
            leaked_plan,
            artifact_path=plan_path,
            sensitive_values=values.all(),
        )
    _assert_no_private_echo(caught.value, values.all())

    attempt = _safe_attempt_result(case, profile_label)
    assert set(attempt) == _ATTEMPT_RESULT_FIELDS
    assert attempt["profile_label"] == profile_label
    assert attempt["environment_persisted"] is False
    assert "environment" not in attempt and "environment_dump" not in attempt
    attempt_path = (
        f"transactions/property-14-{case.case_index:03d}/"
        "attempts/attempt-001/attempt.json"
    )
    attempt_bytes = _canonical_bytes(attempt)
    assert scan_evidence_value(
        EvidenceArtifactKind.ATTEMPT_RESULT,
        attempt,
        artifact_path=attempt_path,
        sensitive_values=values.all(),
    ) == ()
    assert scan_evidence_bytes(
        EvidenceArtifactKind.ATTEMPT_RESULT,
        attempt_bytes,
        artifact_path=attempt_path,
        sensitive_values=values.all(),
    ) == ()

    persisted_evidence = plan_bytes + attempt_bytes + safe_console
    for private in values.all():
        assert private.encode("utf-8") not in persisted_evidence

    unsafe_artifact_paths = {
        "outside-root": "../outside.json",
        "traversal": f"evidence/../{case.nonce}.json",
        "absolute": f"/tmp/property-14-{case.nonce}.json",
        "symlink": ".",
    }
    with pytest.raises(InputError):
        scan_evidence_value(
            EvidenceArtifactKind.PLAN,
            plan,
            artifact_path=unsafe_artifact_paths[case.path_attack],
        )
    return plan_bytes, attempt_bytes, categories


def _write_file(path: Path, content: bytes) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def _unsafe_approved_path(
    workspace: Path,
    approved_root: Path,
    outside: Path,
    case: _GeneratedCase,
) -> tuple[str, str]:
    if case.path_attack == "outside-root":
        return outside.relative_to(workspace).as_posix(), "outside-root"
    if case.path_attack == "traversal":
        return f"../outside-{case.nonce}.json", "traversal"
    if case.path_attack == "absolute":
        return str(outside), "absolute"

    link = approved_root / f"linked-{case.nonce}.json"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        return outside.relative_to(workspace).as_posix(), "symlink-unavailable"
    return link.relative_to(workspace).as_posix(), "symlink"


def _exercise_confinement_and_immutable_history(
    workspace: Path,
    case: _GeneratedCase,
    values: _PrivateValues,
    plan_bytes: bytes,
    attempt_bytes: bytes,
) -> str:
    source_root = workspace / "manuscript"
    evidence_root = workspace / "audiobook-studio" / "build" / "production" / "property-14-book"
    delivery_root = workspace / "audiobook-studio" / "dist" / "audiobook" / "property-14-book"
    transaction_root = (
        evidence_root
        / "transactions"
        / f"property-14-track-{case.case_index:03d}"
        / f"property-14-transaction-{case.case_index:03d}"
    )
    runtime_root = transaction_root / "runtime"

    source_path = _write_file(
        source_root / f"source-{case.case_index:03d}.md",
        values.source_body.encode("utf-8"),
    )
    transcript_path = _write_file(
        runtime_root / "transcripts" / f"segment-{case.case_index:03d}.txt",
        values.transcript_body.encode("utf-8"),
    )
    event_path = _write_file(
        runtime_root / "events" / f"segment-{case.case_index:03d}.jsonl",
        values.raw_event_payload.encode("utf-8"),
    )
    evidence_path = _write_file(
        evidence_root / "plans" / f"property-14-{case.case_index:03d}" / "plan.json",
        plan_bytes,
    )
    attempt_path = _write_file(
        transaction_root / "attempts" / "attempt-001" / "attempt.json",
        attempt_bytes,
    )
    delivery_path = _write_file(
        delivery_root / f"property-14-{case.case_index:03d}.wav",
        hashlib.sha256(case.nonce.encode()).digest(),
    )

    approved_artifacts = (
        (source_root, source_path),
        (runtime_root, transcript_path),
        (runtime_root, event_path),
        (evidence_root, evidence_path),
        (evidence_root, attempt_path),
        (delivery_root, delivery_path),
    )
    for approved_root, path in approved_artifacts:
        relative = path.relative_to(workspace).as_posix()
        assert resolve_inside_approved_root(
            workspace,
            approved_root,
            relative,
            require_exists=True,
            expected_kind="file",
        ) == path

    assert resolve_private_runtime_path(
        workspace,
        transaction_root,
        transcript_path.relative_to(workspace).as_posix(),
        require_exists=True,
        expected_kind="file",
    ) == transcript_path
    assert resolve_private_runtime_path(
        workspace,
        transaction_root,
        event_path.relative_to(workspace).as_posix(),
        require_exists=True,
        expected_kind="file",
    ) == event_path

    outside = _write_file(
        workspace / "outside-approved-roots" / f"outside-{case.nonce}.json",
        b"outside",
    )
    approved_roots = {
        "source": source_root,
        "runtime": runtime_root,
        "evidence": evidence_root,
        "delivery": delivery_root,
    }
    approved_root = approved_roots[case.approved_root_kind]
    unsafe_value, effective_attack = _unsafe_approved_path(
        workspace,
        approved_root,
        outside,
        case,
    )
    with pytest.raises(InputError):
        resolve_inside_approved_root(
            workspace,
            approved_root,
            unsafe_value,
            require_exists=case.path_attack != "traversal",
            expected_kind="file",
        )
    with pytest.raises(InputError):
        resolve_private_runtime_path(
            workspace,
            transaction_root,
            unsafe_value,
            require_exists=case.path_attack != "traversal",
            expected_kind="file",
        )

    history_path = (
        transaction_root
        / "retained-evidence"
        / f"prior-{case.history_state}-{case.case_index:03d}.json"
    )
    original = _canonical_bytes(
        {
            "finding_category": "prior-attempt-not-successful",
            "status": case.history_state,
            "attempt_sha256": _sha256("prior-attempt", case),
        }
    )
    replacement = _canonical_bytes(
        {
            "finding_category": "none",
            "status": "passed",
            "attempt_sha256": _sha256("replacement-attempt", case),
        }
    )
    assert write_immutable_bytes(history_path, original) == history_path
    assert write_immutable_bytes(history_path, original) == history_path
    before_replacement = history_path.read_bytes()
    with pytest.raises(InputError, match="different bytes"):
        write_immutable_bytes(history_path, replacement)
    assert history_path.read_bytes() == before_replacement == original
    return effective_attack


def _run_generated_case(workspace: Path, case: _GeneratedCase) -> tuple[set[str], str]:
    rng = random.Random(f"{PROPERTY_SEED}:{case.case_index}:{case.nonce}")
    values = _private_values(rng, case)
    profile_label = f"property-14-profile-{case.case_index:03d}"
    raw_identity = _raw_identity_response(profile_label, values)

    _exercise_identity_projection(case, profile_label, raw_identity, values)
    safe_console = _exercise_environment_and_console(
        case,
        profile_label,
        values,
    )
    plan_bytes, attempt_bytes, categories = _exercise_evidence_allowlists(
        case,
        profile_label,
        raw_identity,
        values,
        safe_console,
    )
    effective_attack = _exercise_confinement_and_immutable_history(
        workspace,
        case,
        values,
        plan_bytes,
        attempt_bytes,
    )
    return categories, effective_attack


# Feature: audiobook-production-workflow, Property 14: Evidence and identity persistence obey explicit allowlists
# **Validates: Requirements 3.9, 4.9, 7.4, 7.5, 7.11, 15.1-15.9**
def test_property_14_evidence_and_identity_persistence_obey_explicit_allowlists(
    tmp_path: Path,
):
    """Feature: audiobook-production-workflow, Property 14: Evidence and identity persistence obey explicit allowlists"""

    assert GENERATED_CASES >= 100
    assert GENERATED_CASES % len(_PATH_ATTACKS) == 0
    assert {field.name for field in fields(SanitizationFinding)} == {
        "category",
        "path",
        "count",
    }
    print(f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; cases={GENERATED_CASES}")

    rng = random.Random(PROPERTY_SEED)
    generated = tuple(_generated_case(rng, index) for index in range(GENERATED_CASES))
    assert len(generated) == GENERATED_CASES
    observed_identity_outcomes: set[bool] = set()
    observed_path_attacks: set[str] = set()
    observed_effective_attacks: set[str] = set()
    observed_roots: set[str] = set()
    observed_history_states: set[str] = set()
    observed_native_status_classes: set[str] = set()
    observed_forbidden_categories: set[str] = set()

    for case in generated:
        observed_identity_outcomes.add(case.identity_succeeds)
        observed_path_attacks.add(case.path_attack)
        observed_roots.add(case.approved_root_kind)
        observed_history_states.add(case.history_state)
        observed_native_status_classes.add(
            "zero"
            if case.native_return_code == 0
            else "signal"
            if case.native_return_code < 0
            else "nonzero"
        )
        try:
            categories, effective_attack = _run_generated_case(
                tmp_path / f"case-{case.case_index:03d}",
                case,
            )
            observed_forbidden_categories.update(categories)
            observed_effective_attacks.add(effective_attack)
        except Exception as exc:
            exc.add_note(
                f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; case={case.case_index}; "
                f"input={case!r}"
            )
            raise

    assert observed_identity_outcomes == {False, True}
    assert observed_path_attacks == set(_PATH_ATTACKS)
    assert observed_roots == set(_APPROVED_ROOT_KINDS)
    assert observed_history_states == set(_HISTORY_STATES)
    assert observed_native_status_classes == {"zero", "nonzero", "signal"}
    assert _EXPECTED_FORBIDDEN_CATEGORIES <= observed_forbidden_categories
    assert {"outside-root", "traversal", "absolute"} <= observed_effective_attacks
    if os.name == "posix":
        assert "symlink" in observed_effective_attacks
