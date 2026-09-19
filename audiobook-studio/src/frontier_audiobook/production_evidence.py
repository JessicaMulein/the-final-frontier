"""Explicit privacy, schema, and path boundaries for production evidence.

Evidence is intentionally smaller than private runtime state.  This module owns the
shared allowlists used by plans, preflight, authorization, ledgers, attempts,
validation, indexes, and reports.  Findings contain only a category, an artifact
path, and a count; prohibited values are never copied into a finding or exception.

The module performs local deterministic checks only.  It has no AWS, network,
model, narration, child-process, or delivery side effects.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum, StrEnum
from pathlib import Path, PurePosixPath
from typing import Any, ClassVar

from .errors import InputError
from .util import (
    _open_directory_fd,
    durable_mkdir,
    fsync_directory,
    json_loads_strict,
    read_bytes_nofollow,
    resolve_inside_approved_root,
    sha256_bytes,
    workspace_relative,
)

_RECORD_SCHEMA_VERSION = 1
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_FIELD_NAME = re.compile(r"^[a-z][a-z0-9.-]*(?:_[a-z0-9.-]+)*$")
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
_ARN_VALUE = re.compile(r"(?<![A-Za-z0-9])arn:(?:aws|aws-us-gov|aws-cn):[^\s\"']+")
_ACCOUNT_ID_VALUE = re.compile(r"(?<!\d)\d{12}(?!\d)")
_ACCESS_KEY_VALUE = re.compile(r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])")
_ENVIRONMENT_ASSIGNMENT = re.compile(
    r"(?:^|[\s,{;])(?:AWS_[A-Z0-9_]+|AZURE_[A-Z0-9_]+|GOOGLE_[A-Z0-9_]+|"
    r"[A-Z][A-Z0-9_]*(?:SECRET|TOKEN|PASSWORD|CREDENTIAL)[A-Z0-9_]*)="
    r"[^\s,;}]+",
    re.IGNORECASE,
)
_PRIVATE_KEY_VALUE = re.compile(r"-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----")
_RAW_EVENT_VALUE = re.compile(
    r"[\"'](?:audioOutput|textOutput|usageEvent|completionStart|completionEnd)[\"']\s*:",
)


class EvidenceArtifactKind(StrEnum):
    PLAN = "plan"
    PREFLIGHT = "preflight"
    AUTHORIZATION = "authorization"
    LEDGER = "ledger"
    ATTEMPT_LOG = "attempt-log"
    ATTEMPT_RESULT = "attempt-result"
    VALIDATION = "validation"
    DELIVERY = "delivery"
    INDEX = "index"
    REPORT = "report"
    RESOLUTION = "resolution"


@dataclass(frozen=True, slots=True)
class SanitizationFinding:
    """A value-safe finding: no offending key or value is retained."""

    category: str
    path: str
    count: int

    def __post_init__(self) -> None:
        if not isinstance(self.category, str) or not _FIELD_NAME.fullmatch(self.category):
            raise InputError("Sanitization finding category is invalid")
        _require_evidence_path(self.path)
        if type(self.count) is not int or self.count < 1:
            raise InputError("Sanitization finding count must be an integer >= 1")


@dataclass(frozen=True, slots=True)
class ScannedEvidenceArtifact:
    kind: EvidenceArtifactKind
    path: str
    byte_count: int
    sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.kind, EvidenceArtifactKind):
            raise InputError("Scanned evidence kind is invalid")
        _require_evidence_path(self.path)
        if type(self.byte_count) is not int or self.byte_count < 0:
            raise InputError("Scanned evidence byte_count must be an integer >= 0")
        if not isinstance(self.sha256, str) or not _SHA256.fullmatch(self.sha256):
            raise InputError("Scanned evidence SHA-256 is invalid")


@dataclass(frozen=True, slots=True)
class EvidenceScanReport:
    """Immutable summary used as the sanitization input to a successful gate."""

    schema_version: int
    scope: str
    scanned_at_utc: str
    artifacts: tuple[ScannedEvidenceArtifact, ...]
    findings: tuple[SanitizationFinding, ...]
    passed: bool
    canonical_sha256: str

    SCHEMA_VERSION: ClassVar[int] = _RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != self.SCHEMA_VERSION:
            raise InputError("Evidence scan schema_version is unsupported")
        if not isinstance(self.scope, str) or not _FIELD_NAME.fullmatch(self.scope):
            raise InputError("Evidence scan scope is invalid")
        if not isinstance(self.scanned_at_utc, str) or not _UTC.fullmatch(self.scanned_at_utc):
            raise InputError("Evidence scan timestamp must be canonical UTC")
        if not isinstance(self.artifacts, tuple) or not all(
            isinstance(item, ScannedEvidenceArtifact) for item in self.artifacts
        ):
            raise InputError("Evidence scan artifacts must be typed records")
        artifact_order = tuple((item.path, item.kind.value) for item in self.artifacts)
        if artifact_order != tuple(sorted(artifact_order)) or len(set(artifact_order)) != len(
            artifact_order
        ):
            raise InputError("Evidence scan artifacts must be unique and canonically ordered")
        if not isinstance(self.findings, tuple) or not all(
            isinstance(item, SanitizationFinding) for item in self.findings
        ):
            raise InputError("Evidence scan findings must be typed records")
        finding_order = tuple((item.path, item.category) for item in self.findings)
        if finding_order != tuple(sorted(finding_order)) or len(set(finding_order)) != len(
            finding_order
        ):
            raise InputError("Evidence scan findings must be unique and canonically ordered")
        if type(self.passed) is not bool or self.passed != (not self.findings):
            raise InputError("Evidence scan passed must reflect an empty finding set")
        if self.canonical_sha256 and not _SHA256.fullmatch(self.canonical_sha256):
            raise InputError("Evidence scan canonical SHA-256 is invalid")


class EvidenceSanitizationError(InputError):
    """Raised without retaining or displaying a prohibited value."""

    def __init__(self, findings: Sequence[SanitizationFinding]):
        checked = tuple(findings)
        if not checked:
            raise ValueError("EvidenceSanitizationError requires at least one finding")
        self.findings = checked
        summary = ", ".join(
            f"category={item.category},path={item.path},count={item.count}"
            for item in checked
        )
        super().__init__(f"Evidence sanitization blocked: {summary}")


# Every accepted evidence root has an exact schema.  Nested typed records are
# validated by StrictRecordCodec; dynamic mappings are still scanned recursively.
_ROOT_SCHEMAS: dict[EvidenceArtifactKind, tuple[frozenset[str], ...]] = {
    EvidenceArtifactKind.PLAN: (
        frozenset(
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
        ),
    ),
    EvidenceArtifactKind.PREFLIGHT: (
        frozenset(
            {
                "schema_version",
                "plan_sha256",
                "checked_at_utc",
                "expires_at_utc",
                "targeted_checks_sha256",
                "identity_profile_label",
                "identity_resolved",
                "identity_checked_at_utc",
                "official_rates",
                "official_rate_provenance",
                "reusable_segment_ids",
                "maximum_new_calls_by_track",
                "maximum_new_calls_total",
                "estimated_pre_tax_usd",
                "estimate_inputs",
                "delivery_collisions",
                "per_file_inventory_sha256",
                "canonical_sha256",
            }
        ),
        frozenset(
            {
                "plan_sha256",
                "config_sha256",
                "targeted_checks",
                "inventory",
                "write_allowlist",
                "filesystem",
                "track_reuse",
                "destinations",
                "maximum_new_calls_by_track",
                "maximum_new_calls_total",
                "blocking_categories",
                "passed",
                "canonical_sha256",
            }
        ),
        frozenset(
            {
                "plan_sha256",
                "local_preflight_sha256",
                "checked_at_utc",
                "identity_evidence",
                "official_rate_cards",
                "estimate",
                "blocking_categories",
                "passed",
                "canonical_sha256",
            }
        ),
    ),
    EvidenceArtifactKind.AUTHORIZATION: (
        frozenset(
            {
                "schema_version",
                "authorization_id",
                "plan_sha256",
                "preflight_sha256",
                "local_preflight_sha256",
                "estimate_sha256",
                "official_rate_provenance_sha256",
                "exact_transaction_ids",
                "exact_track_ids",
                "exact_command_sha256s",
                "maximum_new_calls_by_track",
                "maximum_new_calls_total",
                "estimated_pre_tax_usd",
                "operator_approved_max_estimated_pre_tax_usd",
                "issued_at_utc",
                "expires_at_utc",
                "one_shot",
                "confirmation_challenge",
                "confirmation_display_sha256",
                "confirmation_decision",
                "confirmed_at_utc",
                "confirmation_sha256",
                "canonical_sha256",
            }
        ),
    ),
    EvidenceArtifactKind.LEDGER: (
        frozenset(
            {
                "schema_version",
                "book_id",
                "plan_id",
                "plan_sha256",
                "transaction_id",
                "track_id",
                "sequence",
                "track_plan_sha256",
                "created_at_utc",
                "canonical_sha256",
            }
        ),
        frozenset(
            {
                "schema_version",
                "transaction_id",
                "operation_id",
                "event_type",
                "state_after",
                "details",
            }
        ),
        frozenset(
            {
                "schema_version",
                "transaction_id",
                "sequence",
                "event_type",
                "state_before",
                "state_after",
                "occurred_at_utc",
                "payload_sha256",
                "previous_event_sha256",
                "event_sha256",
            }
        ),
    ),
    EvidenceArtifactKind.ATTEMPT_RESULT: (
        frozenset(
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
        ),
        frozenset(
            {
                "schema_version",
                "attempt_id",
                "transaction_id",
                "authorization_sha256",
                "finding_category",
                "child_launch_status",
                "automatic_retry_performed",
                "environment_persisted",
            }
        ),
        frozenset(
            {
                "schema_version",
                "attempt_id",
                "transaction_id",
                "authorization_sha256",
                "finding_category",
                "child_launched",
                "automatic_retry_performed",
                "environment_persisted",
            }
        ),
    ),
    EvidenceArtifactKind.VALIDATION: (
        frozenset(
            {
                "schema_version",
                "transaction_id",
                "track_id",
                "validated_at_utc",
                "plan_sha256",
                "attempt_sha256",
                "manifest_sha256",
                "status",
                "checks",
                "delivery_gate_passed",
                "canonical_sha256",
            }
        ),
        frozenset(
            {
                "schema_version",
                "scope",
                "scanned_at_utc",
                "artifacts",
                "findings",
                "passed",
                "canonical_sha256",
            }
        ),
    ),
    EvidenceArtifactKind.DELIVERY: (
        frozenset(
            {
                "schema_version",
                "transaction_id",
                "track_id",
                "recorded_at_utc",
                "validation_sha256",
                "source_path",
                "destination_path",
                "destination_state",
                "status",
                "source_byte_count",
                "source_sha256",
                "destination_byte_count",
                "destination_sha256",
                "complete_byte_sequence_verified",
                "temporary_copy_verified",
                "atomic_publish_performed",
                "destination_preserved",
                "nonbillable",
                "canonical_sha256",
            }
        ),
    ),
    EvidenceArtifactKind.INDEX: (
        frozenset(
            {
                "schema_version",
                "book_id",
                "rebuilt_at_utc",
                "transactions",
                "plans",
                "corrupt_paths",
                "source_fingerprint",
                "canonical_sha256",
            }
        ),
    ),
    EvidenceArtifactKind.REPORT: (
        frozenset(
            {
                "schema_version",
                "transaction_id",
                "track_id",
                "generated_at_utc",
                "state",
                "source_sha256",
                "config_sha256",
                "plan_sha256",
                "preflight_sha256",
                "authorization_sha256",
                "attempt_sha256",
                "validation_sha256",
                "native_return_code",
                "active_artifact_totals",
                "current_execution_totals",
                "estimated_pre_tax_usd",
                "active_artifact_cost_usd",
                "current_execution_cost_usd",
                "billing_status",
                "billing_amount_usd",
                "billing_confirmed_at_utc",
                "delivery_status",
                "isolation_status",
                "targeted_checks_sha256",
                "broader_suite_status",
                "supplemental_listening_sha256",
                "canonical_sha256",
            }
        ),
        frozenset(
            {
                "schema_version",
                "plan_id",
                "plan_sha256",
                "generated_at_utc",
                "status",
                "tracks",
                "selected_count",
                "completed_count",
                "blocked_count",
                "unstarted_count",
                "canonical_sha256",
            }
        ),
    ),
    EvidenceArtifactKind.RESOLUTION: (
        frozenset(
            {
                "schema_version",
                "classification",
                "plan_id",
                "plan_sha256",
                "transaction_id",
                "track_id",
                "transaction_state",
                "ledger_head_sha256",
                "preflight_sha256",
                "authorization_sha256",
                "attempt_evidence_sha256",
                "runtime_evidence_sha256",
                "finding_categories",
                "future_paid_attempt_requirements",
                "duplicate_charge_acknowledgement_required",
                "duplicate_charge_binding_sha256",
                "canonical_sha256",
            }
        ),
        frozenset(
            {
                "schema_version",
                "disposition",
                "plan_id",
                "plan_sha256",
                "transaction_id",
                "track_id",
                "preflight_sha256",
                "authorization_sha256",
                "inspection_sha256",
                "attempt_evidence_sha256",
                "runtime_evidence_sha256",
                "state_after",
                "resolved_at_utc",
                "evidence_retained",
                "future_paid_attempt_requirements",
                "duplicate_charge_acknowledgement_required",
                "duplicate_charge_binding_sha256",
                "canonical_sha256",
            }
        ),
        frozenset(
            {
                "schema_version",
                "prior_transaction_id",
                "retained_attempt_sha256",
                "binding_sha256",
                "decision",
                "acknowledged_at_utc",
                "canonical_sha256",
            }
        ),
    ),
}

_TYPED_KINDS: dict[str, EvidenceArtifactKind] = {
    "FrozenBatchPlan": EvidenceArtifactKind.PLAN,
    "PreflightRecord": EvidenceArtifactKind.PREFLIGHT,
    "LocalPreflightResult": EvidenceArtifactKind.PREFLIGHT,
    "BoundedPreflightEstimateResult": EvidenceArtifactKind.PREFLIGHT,
    "PaidAuthorization": EvidenceArtifactKind.AUTHORIZATION,
    "TransactionMetadata": EvidenceArtifactKind.LEDGER,
    "LedgerPayload": EvidenceArtifactKind.LEDGER,
    "LedgerEvent": EvidenceArtifactKind.LEDGER,
    "AttemptResult": EvidenceArtifactKind.ATTEMPT_RESULT,
    "ValidationEvidence": EvidenceArtifactKind.VALIDATION,
    "EvidenceScanReport": EvidenceArtifactKind.VALIDATION,
    "DeliveryRecord": EvidenceArtifactKind.DELIVERY,
    "DerivedStatusIndex": EvidenceArtifactKind.INDEX,
    "TrackReport": EvidenceArtifactKind.REPORT,
    "BatchReport": EvidenceArtifactKind.REPORT,
    "ResumeInspection": EvidenceArtifactKind.RESOLUTION,
    "ManualResolutionResult": EvidenceArtifactKind.RESOLUTION,
    "ExactDuplicateChargeAcknowledgement": EvidenceArtifactKind.RESOLUTION,
}

_SAFE_PRIVATE_METADATA_NAMES = frozenset(
    {
        "identity_profile_label",
        "identity_resolved",
        "identity_checked_at_utc",
        "profile_label",
        "environment_persisted",
    }
)
_METADATA_SUFFIXES = (
    "_sha256",
    "_path",
    "_count",
    "_status",
    "_type",
    "_schema",
    "_id",
    "_ids",
    "_at_utc",
)


def _require_evidence_path(value: object) -> str:
    if not isinstance(value, str) or not value or "\x00" in value or "\n" in value:
        raise InputError("Evidence path must be a nonblank value-safe relative path")
    candidate = PurePosixPath(value)
    if (
        candidate.is_absolute()
        or value == "."
        or candidate.as_posix() != value
        or any(part in {"", ".", ".."} for part in candidate.parts)
    ):
        raise InputError("Evidence path must be canonical, relative, and traversal-free")
    return value


def _to_json_data(value: Any) -> Any:
    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: _to_json_data(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise InputError("Evidence object names must be strings")
            result[key] = _to_json_data(item)
        return result
    if isinstance(value, (tuple, list)):
        return [_to_json_data(item) for item in value]
    if value is None or type(value) in {str, int, bool, float}:
        return value
    raise InputError(f"Unsupported evidence value type: {type(value).__name__}")


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise InputError("Evidence cannot be canonically encoded") from exc


def _key_category(name: str) -> str | None:
    normalized = re.sub(r"[^a-z0-9]+", "_", name.casefold()).strip("_")
    if normalized in _SAFE_PRIVATE_METADATA_NAMES:
        return None
    if (
        "credential" in normalized
        or normalized in {"access_key", "secret_key", "session_token", "password", "token_value"}
        or normalized.endswith("_access_key")
        or normalized.endswith("_secret_access_key")
    ):
        return "credential-field"
    if normalized in {
        "account",
        "account_id",
        "arn",
        "role_arn",
        "role_id",
        "user_id",
        "principal_id",
        "caller_identity",
        "identity_response",
    }:
        return "identity-detail-field"
    if normalized in {"environment", "environment_dump", "env", "process_environment"}:
        return "environment-field"
    if normalized in {
        "body",
        "prose",
        "source_text",
        "segment_text",
        "text",
        "transcript",
        "transcript_body",
        "content",
        "prompt_body",
    }:
        return "prose-or-transcript-field"
    if normalized in {
        "events",
        "event_payload",
        "raw_event",
        "raw_events",
        "event_journal",
        "raw_event_journal",
        "audio_output",
        "text_output",
        "usage_event",
    }:
        return "raw-event-field"
    if any(normalized.endswith(suffix) for suffix in _METADATA_SUFFIXES):
        return None
    return None


def _value_categories(value: str) -> set[str]:
    categories: set[str] = set()
    if _ARN_VALUE.search(value):
        categories.add("identity-detail-value")
    if _ACCOUNT_ID_VALUE.fullmatch(value.strip()):
        categories.add("identity-detail-value")
    if _ACCESS_KEY_VALUE.search(value) or _PRIVATE_KEY_VALUE.search(value):
        categories.add("credential-value")
    if _ENVIRONMENT_ASSIGNMENT.search(value):
        categories.add("environment-value")
    if _RAW_EVENT_VALUE.search(value):
        categories.add("raw-event-value")
    return categories


def sensitive_strings(value: object) -> tuple[str, ...]:
    """Extract private response values for in-memory non-echo comparisons."""

    values: set[str] = set()

    def visit(item: object) -> None:
        if isinstance(item, str):
            if len(item) >= 4:
                values.add(item)
            return
        if isinstance(item, Mapping):
            for child in item.values():
                visit(child)
            return
        if isinstance(item, (tuple, list, set, frozenset)):
            for child in item:
                visit(child)

    visit(value)
    return tuple(sorted(values, key=lambda item: (len(item), item)))


def forbidden_field_values(value: object) -> tuple[str, ...]:
    """Extract values beneath forbidden evidence fields without persisting them.

    This is used when rendering non-JSON evidence such as Markdown: the generated
    bytes can be compared in memory with private runtime values while findings
    retain only category, path, and count.
    """

    data = _to_json_data(value)
    values: set[str] = set()

    def visit(item: object) -> None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                if isinstance(key, str) and _key_category(key) is not None:
                    values.update(sensitive_strings(child))
                visit(child)
        elif isinstance(item, (tuple, list)):
            for child in item:
                visit(child)

    visit(data)
    return tuple(sorted(values, key=lambda item: (len(item), item)))


def private_environment_values(
    environment: Mapping[str, str] | None,
    *,
    allowed_names: Iterable[str],
) -> tuple[str, ...]:
    """Return only values excluded from the child-environment allowlist."""

    if environment is None:
        return ()
    allowed = frozenset(allowed_names)
    return tuple(
        sorted(
            {
                value
                for name, value in environment.items()
                if name not in allowed
                and isinstance(value, str)
                and len(value) >= 4
            },
            key=lambda item: (len(item), item),
        )
    )


def _scan_data(
    data: object,
    *,
    artifact_path: str,
    sensitive_values: Iterable[str],
) -> tuple[SanitizationFinding, ...]:
    counts: dict[str, int] = {}
    private_values = tuple(
        value for value in dict.fromkeys(sensitive_values) if isinstance(value, str) and len(value) >= 4
    )

    def add(category: str, count: int = 1) -> None:
        counts[category] = counts.get(category, 0) + count

    def visit(item: object, parent_name: str | None = None) -> None:
        if isinstance(item, Mapping):
            for key, child in item.items():
                if type(key) is not str:
                    add("non-string-object-name")
                    child_name = None
                else:
                    category = _key_category(key)
                    if category is not None:
                        add(category)
                    child_name = key
                visit(child, child_name)
            return
        if isinstance(item, (list, tuple)):
            for child in item:
                visit(child, parent_name)
            return
        if isinstance(item, str):
            normalized_parent = (
                re.sub(r"[^a-z0-9]+", "_", parent_name.casefold()).strip("_")
                if isinstance(parent_name, str)
                else ""
            )
            metadata_value = normalized_parent.endswith(_METADATA_SUFFIXES) or normalized_parent in {
                "canonical_sha256",
                "confirmation_challenge",
                "source_fingerprint",
            }
            if not metadata_value:
                for category in _value_categories(item):
                    add(category)
            for private in private_values:
                if private in item:
                    add("private-value")

    visit(data)
    return tuple(
        SanitizationFinding(category, artifact_path, count)
        for category, count in sorted(counts.items())
    )


def scan_evidence_value(
    kind: EvidenceArtifactKind,
    value: object,
    *,
    artifact_path: str,
    sensitive_values: Iterable[str] = (),
) -> tuple[SanitizationFinding, ...]:
    """Scan one typed/untyped evidence value against its exact root allowlist."""

    if not isinstance(kind, EvidenceArtifactKind):
        raise InputError("Evidence kind is invalid")
    checked_path = _require_evidence_path(artifact_path)
    data = _to_json_data(value)
    findings = list(
        _scan_data(data, artifact_path=checked_path, sensitive_values=sensitive_values)
    )
    schemas = _ROOT_SCHEMAS.get(kind)
    if schemas is not None:
        if not isinstance(data, dict) or not any(set(data) == schema for schema in schemas):
            findings.append(SanitizationFinding("schema-not-allowlisted", checked_path, 1))
    return _merge_findings(findings)


def assert_evidence_safe(
    kind: EvidenceArtifactKind,
    value: object,
    *,
    artifact_path: str,
    sensitive_values: Iterable[str] = (),
) -> None:
    findings = scan_evidence_value(
        kind,
        value,
        artifact_path=artifact_path,
        sensitive_values=sensitive_values,
    )
    if findings:
        raise EvidenceSanitizationError(findings)


def scan_identity_projection(
    value: object,
    *,
    artifact_path: str = "preflight/identity-evidence.json",
    raw_response: object | None = None,
) -> tuple[SanitizationFinding, ...]:
    """Enforce the only three fields permitted from an identity response."""

    checked_path = _require_evidence_path(artifact_path)
    data = _to_json_data(value)
    findings: list[SanitizationFinding] = []
    if not isinstance(data, dict) or set(data) != {
        "profile_label",
        "resolved",
        "checked_at_utc",
    }:
        findings.append(SanitizationFinding("identity-projection-not-allowlisted", checked_path, 1))
    allowed_values = tuple(data.values()) if isinstance(data, dict) else ()
    private_values = tuple(
        item for item in sensitive_strings(raw_response) if item not in allowed_values
    )
    findings.extend(
        _scan_data(data, artifact_path=checked_path, sensitive_values=private_values)
    )
    return _merge_findings(findings)


def assert_identity_projection(
    value: object,
    *,
    artifact_path: str = "preflight/identity-evidence.json",
    raw_response: object | None = None,
) -> None:
    findings = scan_identity_projection(
        value,
        artifact_path=artifact_path,
        raw_response=raw_response,
    )
    if findings:
        raise EvidenceSanitizationError(findings)


def scan_typed_evidence_if_applicable(
    value: object,
    *,
    artifact_path: str | None = None,
    sensitive_values: Iterable[str] = (),
) -> tuple[SanitizationFinding, ...]:
    """Apply an explicit allowlist when ``value`` is a known evidence record."""

    name = type(value).__name__
    if name == "IdentityEvidence":
        return scan_identity_projection(
            value,
            artifact_path=artifact_path or "preflight/identity-evidence.json",
        )
    kind = _TYPED_KINDS.get(name)
    if kind is None:
        return ()
    return scan_evidence_value(
        kind,
        value,
        artifact_path=artifact_path or f"evidence/{name}.json",
        sensitive_values=sensitive_values,
    )


def assert_typed_evidence_safe(
    value: object,
    *,
    artifact_path: str | None = None,
    sensitive_values: Iterable[str] = (),
) -> None:
    findings = scan_typed_evidence_if_applicable(
        value,
        artifact_path=artifact_path,
        sensitive_values=sensitive_values,
    )
    if findings:
        raise EvidenceSanitizationError(findings)


def _merge_findings(
    findings: Iterable[SanitizationFinding],
) -> tuple[SanitizationFinding, ...]:
    counts: dict[tuple[str, str], int] = {}
    for finding in findings:
        key = (finding.path, finding.category)
        counts[key] = counts.get(key, 0) + finding.count
    return tuple(
        SanitizationFinding(category, path, count)
        for (path, category), count in sorted(counts.items())
    )


def scan_sanitized_console(
    raw: bytes,
    *,
    artifact_path: str,
    sensitive_values: Iterable[str] = (),
) -> tuple[SanitizationFinding, ...]:
    """Validate the prose-free child-output chunk log schema and values."""

    checked_path = _require_evidence_path(artifact_path)
    findings: list[SanitizationFinding] = []
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return (SanitizationFinding("console-encoding-invalid", checked_path, 1),)
    if text and not text.endswith("\n"):
        findings.append(SanitizationFinding("console-framing-invalid", checked_path, 1))
    expected_sequence = 1
    for line in text.splitlines():
        if not line:
            findings.append(SanitizationFinding("console-framing-invalid", checked_path, 1))
            continue
        try:
            data = json_loads_strict(line, "sanitized attempt console")
        except InputError:
            findings.append(SanitizationFinding("console-schema-invalid", checked_path, 1))
            continue
        if not isinstance(data, dict) or set(data) != {
            "schema_version",
            "event",
            "sequence",
            "byte_count",
            "sha256",
        }:
            findings.append(SanitizationFinding("console-schema-invalid", checked_path, 1))
        else:
            if (
                data["schema_version"] != _RECORD_SCHEMA_VERSION
                or data["event"] != "child-output-chunk"
                or type(data["sequence"]) is not int
                or data["sequence"] != expected_sequence
                or type(data["byte_count"]) is not int
                or data["byte_count"] < 1
                or not isinstance(data["sha256"], str)
                or not _SHA256.fullmatch(data["sha256"])
            ):
                findings.append(SanitizationFinding("console-schema-invalid", checked_path, 1))
            if _canonical_json_bytes(data).decode("utf-8") != line:
                findings.append(SanitizationFinding("console-canonical-encoding-invalid", checked_path, 1))
        findings.extend(
            _scan_data(data, artifact_path=checked_path, sensitive_values=sensitive_values)
        )
        expected_sequence += 1
    return _merge_findings(findings)


def assert_sanitized_console(
    raw: bytes,
    *,
    artifact_path: str,
    sensitive_values: Iterable[str] = (),
) -> None:
    findings = scan_sanitized_console(
        raw,
        artifact_path=artifact_path,
        sensitive_values=sensitive_values,
    )
    if findings:
        raise EvidenceSanitizationError(findings)


def scan_evidence_bytes(
    kind: EvidenceArtifactKind,
    raw: bytes,
    *,
    artifact_path: str,
    sensitive_values: Iterable[str] = (),
) -> tuple[SanitizationFinding, ...]:
    """Strictly decode and scan one persisted evidence artifact."""

    checked_path = _require_evidence_path(artifact_path)
    if kind is EvidenceArtifactKind.ATTEMPT_LOG:
        return scan_sanitized_console(
            raw,
            artifact_path=checked_path,
            sensitive_values=sensitive_values,
        )
    if kind is EvidenceArtifactKind.REPORT and checked_path.endswith(".md"):
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            return (SanitizationFinding("report-encoding-invalid", checked_path, 1),)
        return _scan_data(
            text,
            artifact_path=checked_path,
            sensitive_values=sensitive_values,
        )
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return (SanitizationFinding("evidence-encoding-invalid", checked_path, 1),)
    try:
        data = json_loads_strict(text, "evidence artifact")
    except InputError:
        return (SanitizationFinding("evidence-json-invalid", checked_path, 1),)
    findings = list(
        scan_evidence_value(
            kind,
            data,
            artifact_path=checked_path,
            sensitive_values=sensitive_values,
        )
    )
    if _canonical_json_bytes(data) != raw:
        findings.append(SanitizationFinding("evidence-canonical-encoding-invalid", checked_path, 1))
    return _merge_findings(findings)


def assert_evidence_bytes_safe(
    kind: EvidenceArtifactKind,
    raw: bytes,
    *,
    artifact_path: str,
    sensitive_values: Iterable[str] = (),
) -> None:
    """Reject unsafe encoded evidence without copying prohibited values."""

    findings = scan_evidence_bytes(
        kind,
        raw,
        artifact_path=artifact_path,
        sensitive_values=sensitive_values,
    )
    if findings:
        raise EvidenceSanitizationError(findings)


def _artifact_relative(workspace_root: Path, path: Path) -> str:
    root = Path(os.path.abspath(os.fspath(workspace_root.expanduser())))
    absolute = Path(os.path.abspath(os.fspath(path.expanduser())))
    try:
        relative = absolute.relative_to(root).as_posix()
    except ValueError:
        return "evidence/outside-approved-root"
    try:
        return _require_evidence_path(relative)
    except InputError:
        return "evidence/unsafe-path"


def _classify_json_path(path: Path) -> EvidenceArtifactKind | None:
    name = path.name
    parent = path.parent.name
    if name == "plan.json":
        return EvidenceArtifactKind.PLAN
    if name == "transaction.json" or parent in {"events", "payloads"}:
        return EvidenceArtifactKind.LEDGER
    if "preflight" in name and path.suffix == ".json":
        return EvidenceArtifactKind.PREFLIGHT
    if parent == "authorizations" and path.suffix == ".json":
        return EvidenceArtifactKind.AUTHORIZATION
    if name == "attempt.json" or name.endswith(".ambiguous.json") or name == "launch-failure.json":
        return EvidenceArtifactKind.ATTEMPT_RESULT
    if name == "render-console.log":
        return EvidenceArtifactKind.ATTEMPT_LOG
    if parent == "validation" and path.suffix == ".json":
        return EvidenceArtifactKind.VALIDATION
    if name == "delivery.json" and parent == "delivery":
        return EvidenceArtifactKind.DELIVERY
    if name == "status.json" and parent == "indexes":
        return EvidenceArtifactKind.INDEX
    if name in {"report.json", "report.md"}:
        return EvidenceArtifactKind.REPORT
    return None


def _safe_directory_files(
    workspace_root: Path,
    directory: Path,
    *,
    recurse: bool,
) -> tuple[tuple[Path, ...], tuple[SanitizationFinding, ...]]:
    if not os.path.lexists(directory):
        return (), ()
    relative = _artifact_relative(workspace_root, directory)
    if directory.is_symlink() or not directory.is_dir():
        return (), (SanitizationFinding("unsafe-evidence-path", relative, 1),)
    files: list[Path] = []
    findings: list[SanitizationFinding] = []
    try:
        entries = tuple(sorted(directory.iterdir(), key=lambda item: item.name))
    except OSError:
        return (), (SanitizationFinding("unreadable-evidence-path", relative, 1),)
    for entry in entries:
        entry_relative = _artifact_relative(workspace_root, entry)
        if entry.is_symlink():
            findings.append(SanitizationFinding("unsafe-evidence-path", entry_relative, 1))
        elif entry.is_file():
            files.append(entry)
        elif entry.is_dir():
            if recurse:
                child_files, child_findings = _safe_directory_files(
                    workspace_root,
                    entry,
                    recurse=True,
                )
                files.extend(child_files)
                findings.extend(child_findings)
            # Known child evidence roots are scanned explicitly by the caller when
            # recursion is disabled; a directory entry is not itself evidence.
        else:
            findings.append(SanitizationFinding("ambiguous-evidence-path", entry_relative, 1))
    return tuple(files), _merge_findings(findings)


def scan_validation_gate_evidence(
    workspace_root: Path,
    plan_path: Path,
    transaction_root: Path,
    *,
    scanned_at_utc: str,
    sensitive_values: Iterable[str] = (),
) -> EvidenceScanReport:
    """Scan every available evidence class before a Delivery_Gate can pass.

    Private ``runtime/`` bytes are deliberately not treated as Evidence_Artifacts;
    their confinement and fidelity are validated by the postflight validator.
    """

    root = workspace_root.expanduser().resolve()
    workspace_relative(root, plan_path)
    relative_transaction = workspace_relative(root, transaction_root)
    if not relative_transaction:
        raise InputError("Transaction evidence root is invalid")
    candidates: set[Path] = {plan_path, transaction_root / "transaction.json"}
    initial_findings: list[SanitizationFinding] = []

    directories = (
        (plan_path.parent, False),
        (plan_path.parent / "authorizations", False),
        (transaction_root / "events", False),
        (transaction_root / "payloads", False),
        (transaction_root / "attempts", True),
        (transaction_root / "validation", False),
        (transaction_root / "delivery", False),
    )
    for directory, recurse in directories:
        files, findings = _safe_directory_files(root, directory, recurse=recurse)
        candidates.update(files)
        initial_findings.extend(findings)

    try:
        book_root = transaction_root.parents[2]
    except IndexError:
        book_root = transaction_root
        initial_findings.append(
            SanitizationFinding("unsafe-evidence-path", relative_transaction, 1)
        )
    for optional in (
        book_root / "indexes" / "status.json",
        transaction_root / "report.json",
        transaction_root / "report.md",
    ):
        if os.path.lexists(optional):
            candidates.add(optional)
    batch_files, batch_findings = _safe_directory_files(
        root,
        book_root / "batches",
        recurse=True,
    )
    candidates.update(batch_files)
    initial_findings.extend(batch_findings)

    artifacts: list[ScannedEvidenceArtifact] = []
    findings = list(initial_findings)
    for path in sorted(candidates, key=lambda item: _artifact_relative(root, item)):
        kind = _classify_json_path(path)
        if kind is None:
            continue
        relative = _artifact_relative(root, path)
        try:
            raw = read_bytes_nofollow(path)
        except InputError:
            findings.append(SanitizationFinding("unreadable-evidence-path", relative, 1))
            continue
        artifacts.append(
            ScannedEvidenceArtifact(kind, relative, len(raw), sha256_bytes(raw))
        )
        findings.extend(
            scan_evidence_bytes(
                kind,
                raw,
                artifact_path=relative,
                sensitive_values=sensitive_values,
            )
        )

    merged = _merge_findings(findings)
    from .production_models import seal_record

    return seal_record(
        EvidenceScanReport(
            schema_version=_RECORD_SCHEMA_VERSION,
            scope="delivery-gate-evidence",
            scanned_at_utc=scanned_at_utc,
            artifacts=tuple(sorted(artifacts, key=lambda item: (item.path, item.kind.value))),
            findings=merged,
            passed=not merged,
            canonical_sha256="",
        )
    )


def write_immutable_bytes(path: Path, content: bytes) -> Path:
    """Durably publish immutable evidence or accept only identical existing bytes."""

    absolute = Path(os.path.abspath(os.fspath(path.expanduser())))
    if not absolute.name or absolute.name in {".", ".."}:
        raise InputError("Immutable evidence path is unsafe")
    if os.path.lexists(absolute):
        if absolute.is_symlink() or not absolute.is_file():
            raise InputError("Immutable evidence collision is not a regular file")
        if read_bytes_nofollow(absolute) != content:
            raise InputError("Immutable evidence collision has different bytes")
        return absolute

    durable_mkdir(absolute.parent)
    if os.name == "posix":
        parent_fd = _open_directory_fd(absolute.parent)
        descriptor: int | None = None
        try:
            flags = (
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0)
            )
            try:
                descriptor = os.open(absolute.name, flags, 0o600, dir_fd=parent_fd)
            except FileExistsError:
                if read_bytes_nofollow(absolute) != content:
                    raise InputError("Immutable evidence race published different bytes")
                return absolute
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = None
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.fsync(parent_fd)
        finally:
            if descriptor is not None:
                os.close(descriptor)
            os.close(parent_fd)
    else:  # pragma: no cover - Windows offline support
        try:
            with absolute.open("xb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        except FileExistsError:
            if read_bytes_nofollow(absolute) != content:
                raise InputError("Immutable evidence race published different bytes")
    fsync_directory(absolute.parent)
    return absolute


def write_immutable_evidence(path: Path, value: object) -> Path:
    """Scan, strictly encode, and immutably publish one typed evidence record."""

    assert_typed_evidence_safe(value, artifact_path=f"evidence/{type(value).__name__}.json")
    from .production_models import StrictRecordCodec

    content = StrictRecordCodec(type(value)).dump_bytes(value)
    return write_immutable_bytes(path, content)


def resolve_private_runtime_path(
    workspace_root: Path,
    transaction_root: Path,
    value: str,
    *,
    require_exists: bool = False,
    expected_kind: str | None = None,
) -> Path:
    """Resolve a path only inside one ignored Track transaction ``runtime/`` root."""

    runtime_root = transaction_root / "runtime"
    return resolve_inside_approved_root(
        workspace_root,
        runtime_root,
        value,
        require_exists=require_exists,
        expected_kind=expected_kind,
    )


__all__ = [
    "EvidenceArtifactKind",
    "EvidenceSanitizationError",
    "EvidenceScanReport",
    "SanitizationFinding",
    "ScannedEvidenceArtifact",
    "assert_evidence_bytes_safe",
    "assert_evidence_safe",
    "assert_identity_projection",
    "assert_sanitized_console",
    "assert_typed_evidence_safe",
    "forbidden_field_values",
    "private_environment_values",
    "resolve_private_runtime_path",
    "scan_evidence_bytes",
    "scan_evidence_value",
    "scan_identity_projection",
    "scan_sanitized_console",
    "scan_typed_evidence_if_applicable",
    "scan_validation_gate_evidence",
    "sensitive_strings",
    "write_immutable_bytes",
    "write_immutable_evidence",
]
