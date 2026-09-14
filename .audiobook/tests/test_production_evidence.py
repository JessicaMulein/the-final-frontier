"""Focused unit coverage for Task 7.2 evidence trust boundaries."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from frontier_audiobook.errors import InputError
from frontier_audiobook.production_evidence import (
    EvidenceArtifactKind,
    EvidenceSanitizationError,
    assert_sanitized_console,
    scan_evidence_bytes,
    scan_identity_projection,
    scan_sanitized_console,
    write_immutable_bytes,
)
from frontier_audiobook.production_models import (
    RECORD_SCHEMA_VERSION,
    StrictRecordCodec,
    TransactionState,
)
from frontier_audiobook.production_preflight import IdentityEvidence
from frontier_audiobook.production_transactions import LedgerPayload
from frontier_audiobook.util import resolve_inside_approved_root


def _canonical_line(value: object) -> bytes:
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
        + "\n"
    ).encode("utf-8")


def test_identity_projection_is_exact_and_findings_never_echo_private_values():
    evidence = IdentityEvidence(
        "frontier-audiobook",
        True,
        "2026-09-14T12:00:00Z",
    )
    raw = {
        "Account": "123456789012",
        "Arn": "arn:aws:iam::123456789012:role/private-role",
        "UserId": "PRIVATE-CALLER-ID",
        "Credentials": "PRIVATE-CREDENTIAL-VALUE",
    }

    assert scan_identity_projection(evidence, raw_response=raw) == ()

    nested_unknown = {
        "profile_label": "frontier-audiobook",
        "resolved": True,
        "checked_at_utc": "2026-09-14T12:00:00Z",
        "unexpected": {"nested": "value"},
    }
    nested_findings = scan_identity_projection(nested_unknown, raw_response=raw)
    assert "identity-projection-not-allowlisted" in {
        item.category for item in nested_findings
    }

    leaked = {
        "profile_label": "frontier-audiobook",
        "resolved": True,
        "checked_at_utc": "2026-09-14T12:00:00Z",
        "Account": raw["Account"],
        "credential_value": raw["Credentials"],
    }
    findings = scan_identity_projection(leaked, raw_response=raw)
    assert {(item.category, item.path) for item in findings} >= {
        ("identity-projection-not-allowlisted", "preflight/identity-evidence.json"),
        ("identity-detail-field", "preflight/identity-evidence.json"),
        ("credential-field", "preflight/identity-evidence.json"),
    }
    rendered = repr(findings)
    assert raw["Account"] not in rendered
    assert raw["Arn"] not in rendered
    assert raw["Credentials"] not in rendered


def test_typed_ledger_allowlist_rejects_private_values_without_echoing_them():
    private_arn = "arn:aws:iam::123456789012:role/private-role"
    payload = LedgerPayload(
        schema_version=RECORD_SCHEMA_VERSION,
        transaction_id="transaction-001",
        operation_id="unsafe-diagnostic",
        event_type="diagnostic-recorded",
        state_after=TransactionState.BLOCKED,
        details={"diagnostic": private_arn},
    )

    with pytest.raises(EvidenceSanitizationError) as caught:
        StrictRecordCodec(LedgerPayload).dump_bytes(payload)

    message = str(caught.value)
    assert "identity-detail-value" in message
    assert "evidence/LedgerPayload.json" in message
    assert private_arn not in message
    assert "123456789012" not in message


def test_console_schema_is_canonical_prose_free_and_value_safe():
    valid = _canonical_line(
        {
            "schema_version": RECORD_SCHEMA_VERSION,
            "event": "child-output-chunk",
            "sequence": 1,
            "byte_count": 37,
            "sha256": "a" * 64,
        }
    )
    assert scan_sanitized_console(
        valid,
        artifact_path="attempts/attempt-001/render-console.log",
    ) == ()

    private_transcript = "private transcript body must not persist"
    invalid = _canonical_line(
        {
            "schema_version": RECORD_SCHEMA_VERSION,
            "event": "child-output-chunk",
            "sequence": 1,
            "byte_count": len(private_transcript),
            "sha256": "b" * 64,
            "transcript": private_transcript,
        }
    )
    findings = scan_sanitized_console(
        invalid,
        artifact_path="attempts/attempt-001/render-console.log",
        sensitive_values=(private_transcript,),
    )
    assert {item.category for item in findings} >= {
        "console-schema-invalid",
        "prose-or-transcript-field",
        "private-value",
    }
    with pytest.raises(EvidenceSanitizationError) as caught:
        assert_sanitized_console(
            invalid,
            artifact_path="attempts/attempt-001/render-console.log",
            sensitive_values=(private_transcript,),
        )
    assert private_transcript not in str(caught.value)


def test_report_scan_detects_private_body_without_reproducing_it():
    private_body = "A manuscript sentence that belongs only in private runtime."
    raw = f"# Track report\n\n{private_body}\n".encode("utf-8")

    findings = scan_evidence_bytes(
        EvidenceArtifactKind.REPORT,
        raw,
        artifact_path="transactions/chapter-001/report.md",
        sensitive_values=(private_body,),
    )

    assert [(item.category, item.count) for item in findings] == [("private-value", 1)]
    assert private_body not in repr(findings)
    with pytest.raises(InputError, match="canonical, relative"):
        scan_evidence_bytes(
            EvidenceArtifactKind.REPORT,
            b"# Report\n",
            artifact_path=".",
        )


def test_approved_root_resolution_rejects_escape_and_every_symlink(tmp_path: Path):
    workspace = tmp_path
    runtime = workspace / ".audiobook" / "build" / "production" / "book" / "runtime"
    runtime.mkdir(parents=True)
    inside = runtime / "artifact.json"
    inside.write_text("{}", encoding="utf-8")
    outside = workspace / "outside.json"
    outside.write_text("{}", encoding="utf-8")

    relative_inside = inside.relative_to(workspace).as_posix()
    assert resolve_inside_approved_root(
        workspace,
        runtime,
        relative_inside,
        require_exists=True,
        expected_kind="file",
    ) == inside
    future = runtime / "future.json"
    assert resolve_inside_approved_root(
        workspace,
        runtime,
        future.relative_to(workspace).as_posix(),
    ) == future

    with pytest.raises(InputError, match="approved root"):
        resolve_inside_approved_root(
            workspace,
            runtime,
            outside.relative_to(workspace).as_posix(),
        )
    with pytest.raises(InputError, match="traversal-free"):
        resolve_inside_approved_root(workspace, runtime, "../outside.json")

    link = runtime / "linked.json"
    try:
        link.symlink_to(outside)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks are unavailable on this platform")
    with pytest.raises(InputError, match="symlink"):
        resolve_inside_approved_root(
            workspace,
            runtime,
            link.relative_to(workspace).as_posix(),
            require_exists=True,
            expected_kind="file",
        )


def test_immutable_evidence_never_rewrites_failed_or_uncertain_bytes(tmp_path: Path):
    path = tmp_path / "validation" / "failed-evidence.json"
    original = b'{"status":"blocked"}'
    replacement = b'{"status":"passed"}'

    assert write_immutable_bytes(path, original) == path
    assert write_immutable_bytes(path, original) == path
    with pytest.raises(InputError, match="different bytes"):
        write_immutable_bytes(path, replacement)
    assert path.read_bytes() == original
