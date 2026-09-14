"""Offline production resume inspection and explicit manual resolution.

Transaction ledgers and retained local artifacts are the only inputs.  This module
has no identity, pricing, network, child-process, AWS, narration, or model-call
integration.  Inspection is read-only; resolution only appends immutable ledger
evidence and never moves or rewrites attempt/runtime artifacts.
"""

from __future__ import annotations

import os
import re
import stat
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any, ClassVar

from .errors import InputError
from .nova import _mid_sentence_partial_turn_count, replay_output_events
from .production import load_production_plan
from .production_models import (
    RECORD_SCHEMA_VERSION,
    AttemptResult,
    FrozenBatchPlan,
    FrozenTrackPlan,
    PaidAuthorization,
    StrictRecordCodec,
    TransactionState,
    canonical_sha256,
    seal_record,
)
from .production_preflight import (
    _load_event_journal,
    _current_segments,
    _wav_lpcm,
)
from .production_transactions import TransactionSnapshot, TransactionSpec, TransactionStore
from .production_worker import (
    _load_authorization_artifact,
    _load_current_config,
    _load_narration_runtime,
    _runtime_fingerprint,
    _selected_catalog_track,
)
from .util import (
    read_bytes_nofollow,
    read_json,
    resolve_inside,
    sha256_bytes,
    utc_now,
    workspace_relative,
)
from .verify import compare_transcript, normalized_tokens

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
_FUTURE_REQUIREMENTS = (
    "new-transaction",
    "new-plan",
    "new-preflight",
    "new-authorization",
)


class ResumeClassification(StrEnum):
    """The complete, closed set of resume inspection outcomes."""

    NOTHING_TO_RESUME = "nothing-to-resume"
    LOCAL_VALIDATION_AVAILABLE = "local-validation-available"
    COMPLETE_ARTIFACTS_RECOVERABLE = "complete-artifacts-recoverable"
    CHARGE_UNCERTAIN_REVIEW_REQUIRED = "charge-uncertain-review-required"
    BLOCKED_NEW_PLAN_REQUIRED = "blocked-new-plan-required"


class ManualResolutionDisposition(StrEnum):
    """Nonbillable operator dispositions for uncertain local evidence."""

    ACCEPT_COMPLETE_LOCAL_ARTIFACTS = "accept-complete-local-artifacts"
    QUARANTINE_INVALID_ARTIFACTS = "quarantine-invalid-artifacts"
    ABANDON_UNCERTAIN_ATTEMPT = "abandon-uncertain-attempt"


class DuplicateChargeDecision(StrEnum):
    """The only decision accepted as duplicate-charge acknowledgement."""

    ACKNOWLEDGE_EXACT_RETAINED_ATTEMPT = "acknowledge-exact-retained-attempt"


@dataclass(frozen=True, slots=True)
class ResumeInspection:
    schema_version: int
    classification: ResumeClassification
    plan_id: str
    plan_sha256: str
    transaction_id: str
    track_id: str
    transaction_state: TransactionState | None
    ledger_head_sha256: str | None
    preflight_sha256: str | None
    authorization_sha256: str | None
    attempt_evidence_sha256: str
    runtime_evidence_sha256: str
    finding_categories: tuple[str, ...]
    future_paid_attempt_requirements: tuple[str, ...]
    duplicate_charge_acknowledgement_required: bool
    duplicate_charge_binding_sha256: str | None
    canonical_sha256: str

    SCHEMA_VERSION: ClassVar[int] = RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != RECORD_SCHEMA_VERSION:
            raise InputError("resume inspection schema_version is unsupported")
        if not isinstance(self.classification, ResumeClassification):
            raise InputError("resume inspection classification is not enumerated")
        for name in ("plan_sha256", "attempt_evidence_sha256", "runtime_evidence_sha256"):
            if not _is_sha256(getattr(self, name)):
                raise InputError(f"resume inspection {name} is malformed")
        for value in (
            self.ledger_head_sha256,
            self.preflight_sha256,
            self.authorization_sha256,
            self.duplicate_charge_binding_sha256,
        ):
            if value is not None and not _is_sha256(value):
                raise InputError("resume inspection contains a malformed optional digest")
        if tuple(sorted(set(self.finding_categories))) != self.finding_categories:
            raise InputError("resume inspection findings must be unique and sorted")
        if self.future_paid_attempt_requirements not in ((), _FUTURE_REQUIREMENTS):
            raise InputError("resume inspection future-attempt requirements are incomplete")
        if self.duplicate_charge_acknowledgement_required != (
            self.duplicate_charge_binding_sha256 is not None
        ):
            raise InputError("resume inspection duplicate-charge binding is inconsistent")
        if self.canonical_sha256 and not _is_sha256(self.canonical_sha256):
            raise InputError("resume inspection canonical_sha256 is malformed")


@dataclass(frozen=True, slots=True)
class ManualResolutionResult:
    schema_version: int
    disposition: ManualResolutionDisposition
    plan_id: str
    plan_sha256: str
    transaction_id: str
    track_id: str
    preflight_sha256: str | None
    authorization_sha256: str | None
    inspection_sha256: str
    attempt_evidence_sha256: str
    runtime_evidence_sha256: str
    state_after: TransactionState
    resolved_at_utc: str
    evidence_retained: bool
    future_paid_attempt_requirements: tuple[str, ...]
    duplicate_charge_acknowledgement_required: bool
    duplicate_charge_binding_sha256: str | None
    canonical_sha256: str

    SCHEMA_VERSION: ClassVar[int] = RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != RECORD_SCHEMA_VERSION:
            raise InputError("manual resolution schema_version is unsupported")
        if not isinstance(self.disposition, ManualResolutionDisposition):
            raise InputError("manual resolution disposition is invalid")
        for value in (
            self.plan_sha256,
            self.inspection_sha256,
            self.attempt_evidence_sha256,
            self.runtime_evidence_sha256,
        ):
            if not _is_sha256(value):
                raise InputError("manual resolution contains a malformed digest")
        for value in (
            self.preflight_sha256,
            self.authorization_sha256,
            self.duplicate_charge_binding_sha256,
        ):
            if value is not None and not _is_sha256(value):
                raise InputError("manual resolution contains a malformed optional digest")
        _require_utc(self.resolved_at_utc, "manual resolution timestamp")
        if not self.evidence_retained:
            raise InputError("manual resolution must retain original evidence")
        if self.state_after is TransactionState.RENDERED:
            if self.future_paid_attempt_requirements:
                raise InputError("accepted local artifacts cannot authorize another attempt")
        elif self.state_after is TransactionState.BLOCKED:
            if self.future_paid_attempt_requirements != _FUTURE_REQUIREMENTS:
                raise InputError("blocked resolution must require a complete fresh paid scope")
        else:
            raise InputError("manual resolution may end only rendered or blocked")
        if self.duplicate_charge_acknowledgement_required != (
            self.duplicate_charge_binding_sha256 is not None
        ):
            raise InputError("manual resolution duplicate-charge binding is inconsistent")
        if self.canonical_sha256 and not _is_sha256(self.canonical_sha256):
            raise InputError("manual resolution canonical_sha256 is malformed")


@dataclass(frozen=True, slots=True)
class ExactDuplicateChargeAcknowledgement:
    schema_version: int
    prior_transaction_id: str
    retained_attempt_sha256: str
    binding_sha256: str
    decision: DuplicateChargeDecision
    acknowledged_at_utc: str
    canonical_sha256: str

    SCHEMA_VERSION: ClassVar[int] = RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if self.schema_version != RECORD_SCHEMA_VERSION:
            raise InputError("duplicate-charge acknowledgement schema_version is unsupported")
        for value in (self.retained_attempt_sha256, self.binding_sha256):
            if not _is_sha256(value):
                raise InputError("duplicate-charge acknowledgement digest is malformed")
        if self.binding_sha256 != _duplicate_charge_binding(
            self.prior_transaction_id, self.retained_attempt_sha256
        ):
            raise InputError("duplicate-charge acknowledgement binding is not exact")
        if self.decision is not DuplicateChargeDecision.ACKNOWLEDGE_EXACT_RETAINED_ATTEMPT:
            raise InputError("duplicate-charge acknowledgement decision is insufficient")
        _require_utc(self.acknowledged_at_utc, "duplicate-charge acknowledgement timestamp")
        if self.canonical_sha256 and not _is_sha256(self.canonical_sha256):
            raise InputError("duplicate-charge acknowledgement canonical_sha256 is malformed")


@dataclass(frozen=True, slots=True)
class _TreeInventory:
    exists: bool
    safe: bool
    files: tuple[tuple[str, str, int, str | None], ...]
    sha256: str


@dataclass(frozen=True, slots=True)
class _AuthorizationAssessment:
    valid: bool
    preflight_sha256: str | None
    authorization_sha256: str | None
    maximum_new_calls: int | None
    findings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _AttemptAssessment:
    evidence_sha256: str
    has_evidence: bool
    valid_committed_result: bool
    native_return_code: int | None
    possible_charge: bool
    findings: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class _RuntimeAssessment:
    evidence_sha256: str
    complete: bool
    findings: tuple[str, ...]


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _require_utc(value: object, label: str) -> str:
    if not isinstance(value, str) or _UTC.fullmatch(value) is None:
        raise InputError(f"{label} must be a UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise InputError(f"{label} is invalid") from exc
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise InputError(f"{label} must be UTC")
    return value


def _clock_value(value: str | None) -> str:
    return _require_utc(value or utc_now(), "manual resolution timestamp")


def _duplicate_charge_binding(transaction_id: str, attempt_sha256: str) -> str:
    if not _is_sha256(attempt_sha256):
        raise InputError("retained attempt digest is malformed")
    return canonical_sha256(
        {
            "schema": "frontier-duplicate-charge-acknowledgement-v1",
            "prior_transaction_id": transaction_id,
            "retained_attempt_sha256": attempt_sha256,
        }
    )


def _tree_inventory(root: Path) -> _TreeInventory:
    absolute = Path(os.path.abspath(os.fspath(root.expanduser())))
    if not os.path.lexists(absolute):
        payload = {"exists": False, "files": ()}
        return _TreeInventory(False, True, (), canonical_sha256(payload))

    records: list[tuple[str, str, int, str | None]] = []
    safe = True

    def visit(path: Path, relative: str) -> None:
        nonlocal safe
        try:
            metadata = os.lstat(path)
        except OSError:
            safe = False
            records.append((relative, "unreadable", 0, None))
            return
        if stat.S_ISLNK(metadata.st_mode):
            safe = False
            records.append((relative, "symlink", metadata.st_size, None))
            return
        if stat.S_ISREG(metadata.st_mode):
            try:
                content = read_bytes_nofollow(path)
            except InputError:
                safe = False
                records.append((relative, "unreadable-file", metadata.st_size, None))
                return
            records.append((relative, "file", len(content), sha256_bytes(content)))
            return
        if stat.S_ISDIR(metadata.st_mode):
            records.append((relative, "directory", 0, None))
            try:
                children = tuple(sorted(path.iterdir(), key=lambda item: item.name))
            except OSError:
                safe = False
                return
            for child in children:
                child_relative = child.name if relative == "." else f"{relative}/{child.name}"
                visit(child, child_relative)
            return
        safe = False
        records.append((relative, "special", metadata.st_size, None))

    visit(absolute, ".")
    frozen = tuple(records)
    return _TreeInventory(
        True,
        safe,
        frozen,
        canonical_sha256({"exists": True, "files": frozen}),
    )


def _load_scope(
    workspace_root: Path,
    plan_path: Path,
    track_id: str,
    transaction_id: str,
) -> tuple[Path, Path, FrozenBatchPlan, FrozenTrackPlan, TransactionStore]:
    root = workspace_root.expanduser().resolve()
    absolute_plan = Path(os.path.abspath(os.fspath(plan_path.expanduser())))
    workspace_relative(root, absolute_plan)
    plan = load_production_plan(absolute_plan)
    matches = tuple(
        item
        for item in plan.tracks
        if item.track_id == track_id and item.transaction_id == transaction_id
    )
    if len(matches) != 1:
        raise InputError("Resume scope must identify one exact frozen Track transaction")
    if (
        absolute_plan.name != "plan.json"
        or absolute_plan.parent.name != plan.plan_id
        or absolute_plan.parent.parent.name != "plans"
        or absolute_plan.parent.parent.parent.name != plan.book_id
    ):
        raise InputError("Frozen plan path does not match the production plan layout")
    book_root = absolute_plan.parent.parent.parent
    store = TransactionStore(book_root, plan.book_id)
    return root, absolute_plan, plan, matches[0], store


def _authorization_assessment(
    plan_path: Path,
    plan: FrozenBatchPlan,
    track: FrozenTrackPlan,
    snapshot: TransactionSnapshot,
) -> _AuthorizationAssessment:
    required = tuple(
        payload for payload in snapshot.payloads if payload.event_type == "authorization-required"
    )
    preflight_sha256 = (
        required[0].details.get("preflight_sha256") if len(required) == 1 else None
    )
    findings: set[str] = set()
    if preflight_sha256 is not None and not _is_sha256(preflight_sha256):
        findings.add("authorization-preflight-binding-invalid")
        preflight_sha256 = None

    consumed = tuple(
        payload for payload in snapshot.payloads if payload.event_type == "authorization-consumed"
    )
    if not consumed:
        return _AuthorizationAssessment(False, preflight_sha256, None, None, tuple(sorted(findings)))
    if len(consumed) != 1 or len(required) != 1:
        findings.add("authorization-consumption-ambiguous")
        return _AuthorizationAssessment(False, preflight_sha256, None, None, tuple(sorted(findings)))

    details = consumed[0].details
    authorization_sha256 = details.get("authorization_sha256")
    maximum_new_calls = details.get("maximum_new_calls")
    if not _is_sha256(authorization_sha256):
        findings.add("authorization-consumption-digest-invalid")
        authorization_sha256 = None
    if type(maximum_new_calls) is not int or not (0 <= maximum_new_calls <= track.maximum_new_calls):
        findings.add("authorization-consumption-call-bound-invalid")
        maximum_new_calls = None
    if (
        details.get("command_sha256") != track.command_sha256
        or details.get("one_shot") is not True
        or details.get("automatic_retry_performed") is not False
    ):
        findings.add("authorization-consumption-scope-invalid")

    authorization: PaidAuthorization | None = None
    if authorization_sha256 is not None:
        try:
            authorization = _load_authorization_artifact(plan_path, authorization_sha256)
        except InputError:
            findings.add("authorization-artifact-invalid")
    if authorization is not None:
        expected_plan_sha256 = StrictRecordCodec(FrozenBatchPlan).sha256(plan)
        if (
            StrictRecordCodec(PaidAuthorization).sha256(authorization) != authorization_sha256
            or authorization.plan_sha256 != expected_plan_sha256
            or authorization.preflight_sha256 != preflight_sha256
            or authorization.exact_transaction_ids
            != tuple(item.transaction_id for item in plan.tracks)
            or authorization.exact_track_ids != tuple(item.track_id for item in plan.tracks)
            or authorization.exact_command_sha256s
            != tuple(item.command_sha256 for item in plan.tracks)
            or maximum_new_calls is None
            or authorization.maximum_new_calls_by_track.get(track.track_id)
            != maximum_new_calls
            or not authorization.one_shot
        ):
            findings.add("authorization-artifact-binding-invalid")

    return _AuthorizationAssessment(
        not findings and authorization is not None,
        preflight_sha256,
        authorization_sha256,
        maximum_new_calls,
        tuple(sorted(findings)),
    )


def _attempt_assessment(
    workspace_root: Path,
    transaction_root: Path,
    track: FrozenTrackPlan,
    snapshot: TransactionSnapshot,
    authorization: _AuthorizationAssessment,
) -> _AttemptAssessment:
    attempts_root = transaction_root / "attempts"
    inventory = _tree_inventory(attempts_root)
    findings: set[str] = set()
    if not inventory.safe:
        findings.add("attempt-evidence-unsafe")

    consumed = tuple(
        payload for payload in snapshot.payloads if payload.event_type == "authorization-consumed"
    )
    attempt_id = consumed[0].details.get("attempt_id") if len(consumed) == 1 else None
    if not isinstance(attempt_id, str) or not attempt_id:
        if consumed:
            findings.add("attempt-identity-invalid")
        return _AttemptAssessment(
            inventory.sha256,
            inventory.exists and len(inventory.files) > 1,
            False,
            None,
            bool(consumed),
            tuple(sorted(findings)),
        )

    final = attempts_root / attempt_id
    ambiguous = attempts_root / f"{attempt_id}.ambiguous.json"
    staging_prefix = f"{attempt_id}.staging-"
    try:
        top_entries = (
            tuple(sorted(attempts_root.iterdir(), key=lambda item: item.name))
            if inventory.exists and attempts_root.is_dir() and not attempts_root.is_symlink()
            else ()
        )
    except OSError:
        top_entries = ()
        findings.add("attempt-root-unreadable")
    allowed = {attempt_id, f"{attempt_id}.ambiguous.json"}
    if any(not (item.name in allowed or item.name.startswith(staging_prefix)) for item in top_entries):
        findings.add("attempt-evidence-ambiguous")
    staging = tuple(item for item in top_entries if item.name.startswith(staging_prefix))
    if staging:
        findings.add("attempt-staging-retained")

    possible_charge = bool(consumed)
    prelaunch = any(payload.event_type == "attempt-launch-blocked" for payload in snapshot.payloads)
    if prelaunch:
        possible_charge = False

    if os.path.lexists(ambiguous):
        try:
            marker = read_json(ambiguous)
            if not isinstance(marker, dict) or (
                marker.get("attempt_id") != attempt_id
                or marker.get("transaction_id") != track.transaction_id
                or marker.get("authorization_sha256") != authorization.authorization_sha256
                or marker.get("automatic_retry_performed") is not False
                or marker.get("environment_persisted") is not False
            ):
                raise InputError("ambiguous marker binding invalid")
            possible_charge = marker.get("child_launch_status") in {"confirmed", "unknown"}
        except InputError:
            findings.add("attempt-ambiguity-marker-invalid")
            possible_charge = True

    result: AttemptResult | None = None
    if os.path.lexists(final):
        if final.is_symlink() or not final.is_dir():
            findings.add("attempt-committed-bundle-unsafe")
        else:
            try:
                names = {item.name for item in final.iterdir()}
            except OSError:
                names = set()
            if names != {"attempt.json", "render-console.log"}:
                findings.add("attempt-committed-bundle-ambiguous")
            try:
                result = StrictRecordCodec(AttemptResult).load(final / "attempt.json")
                console = final / "render-console.log"
                expected_console = workspace_relative(workspace_root, console)
                if (
                    result.attempt_id != attempt_id
                    or result.transaction_id != track.transaction_id
                    or result.authorization_sha256 != authorization.authorization_sha256
                    or result.argv != track.command_argv
                    or result.command_sha256 != track.command_sha256
                    or result.profile_label != track.effective_config.profile_label
                    or result.console_path != expected_console
                    or sha256_bytes(read_bytes_nofollow(console)) != result.console_sha256
                    or result.automatic_retry_performed
                    or result.environment_persisted
                    or (
                        result.termination_signal
                        != (-result.native_return_code if result.native_return_code < 0 else None)
                    )
                ):
                    raise InputError("committed attempt binding invalid")
            except InputError:
                findings.add("attempt-committed-result-invalid")
                result = None
    elif consumed and not prelaunch:
        findings.add("attempt-committed-result-missing")

    if result is not None:
        possible_charge = True
        completion = tuple(
            payload
            for payload in snapshot.payloads
            if payload.event_type in {"attempt-rendered", "attempt-nonzero"}
        )
        if completion:
            if len(completion) != 1 or (
                completion[0].details.get("attempt_result_sha256")
                != StrictRecordCodec(AttemptResult).sha256(result)
                or completion[0].details.get("console_sha256") != result.console_sha256
                or completion[0].details.get("native_return_code") != result.native_return_code
            ):
                findings.add("attempt-ledger-result-binding-invalid")

    if os.path.lexists(ambiguous) or staging:
        findings.add("attempt-evidence-incomplete")
    return _AttemptAssessment(
        inventory.sha256,
        inventory.exists and len(inventory.files) > 1,
        result is not None and not any(
            item.startswith("attempt-committed") or item == "attempt-ledger-result-binding-invalid"
            for item in findings
        ),
        result.native_return_code if result is not None else None,
        possible_charge,
        tuple(sorted(findings)),
    )


def _runtime_artifact_path(
    workspace_root: Path,
    runtime_root: Path,
    value: object,
    label: str,
) -> Path:
    if not isinstance(value, str) or not value:
        raise InputError(f"{label} is not a workspace-relative path")
    from .util import resolve_inside_approved_root

    try:
        return resolve_inside_approved_root(
            workspace_root,
            runtime_root,
            value,
            require_exists=True,
            expected_kind="file",
        )
    except InputError as exc:
        raise InputError(f"{label} escapes or violates the private runtime boundary") from exc


def _validate_runtime_manifest(
    workspace_root: Path,
    runtime_root: Path,
    track: FrozenTrackPlan,
    segment_pairs: Sequence[tuple[Any, Any]],
    maximum_new_calls: int,
) -> None:
    manifest = read_json(runtime_root / "manifest.json")
    if not isinstance(manifest, dict):
        raise InputError("runtime manifest is not an object")
    source = track.source
    required = {
        "track_id": track.track_id,
        "voice_id": track.effective_config.voice,
        "source_path": source.source_path,
        "source_sha256": source.raw_sha256,
        "spoken_sha256": source.spoken_sha256,
        "word_count": source.spoken_token_count,
        "segment_count": source.segment_count,
        "active_segment_count": source.segment_count,
        "target_segment_words": track.effective_config.target_segment_words,
        "segment_boundary_policy": source.segmentation_policy,
        "track_kind": track.effective_config.track_kind.value,
        "source_kind": source.source_kind.value,
        "source_section": source.source_section,
        "sequence": track.sequence,
        "normalized_body_sha256": source.normalized_body_sha256,
        "spoken_token_count": source.spoken_token_count,
        "render_identity_schema": source.render_identity_schema,
        "maximum_new_calls": maximum_new_calls,
    }
    if any(manifest.get(name) != value for name, value in required.items()):
        raise InputError("runtime manifest fixed binding differs from frozen Track")

    entries = manifest.get("segments")
    if not isinstance(entries, list) or len(entries) != len(segment_pairs):
        raise InputError("runtime manifest active segment set is incomplete")
    if [item.get("segment_id") for item in entries if isinstance(item, dict)] != [
        snapshot.segment_id for snapshot, _segment in segment_pairs
    ]:
        raise InputError("runtime manifest segment order or identity is invalid")

    rendered_calls = 0
    for raw, (snapshot, segment) in zip(entries, segment_pairs, strict=True):
        if not isinstance(raw, dict):
            raise InputError("runtime manifest segment entry is malformed")
        if (
            raw.get("segment_id") != snapshot.segment_id
            or raw.get("paragraph_index") != segment.paragraph_index
            or raw.get("text") != segment.text
            or raw.get("text_sha256") != snapshot.text_sha256
            or raw.get("render_identity_sha256") != snapshot.render_identity_sha256
            or raw.get("word_count") != segment.word_count
            or raw.get("narration_only_punctuation")
            is not segment.narration_only_punctuation
            or raw.get("status") not in {"narrated", "reused", "accepted"}
            or raw.get("exact_transcript_match") is not True
            or raw.get("coverage_ratio") != 1.0
            or raw.get("event_replay_passed") is not True
            or raw.get("mid_sentence_partial_turns") != 0
        ):
            raise InputError("runtime segment binding or fidelity evidence is invalid")

        audio_path = _runtime_artifact_path(
            workspace_root, runtime_root, raw.get("audio_path"), "runtime audio_path"
        )
        audio = read_bytes_nofollow(audio_path)
        if sha256_bytes(audio) != raw.get("audio_sha256"):
            raise InputError("runtime segment audio digest is invalid")
        lpcm = _wav_lpcm(audio, track)

        transcript_path = runtime_root / "transcripts" / f"{audio_path.stem}.txt"
        transcript_bytes = read_bytes_nofollow(transcript_path)
        try:
            transcript = transcript_bytes.decode("utf-8").removesuffix("\n")
        except UnicodeDecodeError as exc:
            raise InputError("runtime transcript is not strict UTF-8") from exc
        if raw.get("transcript") != transcript:
            raise InputError("runtime transcript body differs from its private artifact")
        verification = compare_transcript(
            segment.text, transcript, track.effective_config.normalization
        )
        if not verification.passed or verification.coverage_ratio != 1.0:
            raise InputError("runtime transcript does not exactly match frozen spoken text")

        event_path = runtime_root / "events" / f"{audio_path.stem}.jsonl"
        events = _load_event_journal(event_path)
        replayed = replay_output_events(events)
        if replayed.audio_lpcm != lpcm:
            raise InputError("runtime event replay LPCM differs from segment audio")
        replay_check = compare_transcript(
            segment.text,
            replayed.final_transcript,
            track.effective_config.normalization,
        )
        if not replay_check.passed or normalized_tokens(
            transcript, track.effective_config.normalization
        ) != normalized_tokens(
            replayed.final_transcript, track.effective_config.normalization
        ):
            raise InputError("runtime event replay transcript binding is invalid")
        if _mid_sentence_partial_turn_count(events) != 0:
            raise InputError("runtime event replay contains a mid-sentence partial turn")
        if raw.get("rendered_in_current_attempt") is True:
            rendered_calls += 1
        elif raw.get("rendered_in_current_attempt") is not False:
            raise InputError("runtime segment render/reuse partition is invalid")

    if manifest.get("billable_calls_made") != rendered_calls:
        raise InputError("runtime manifest billable call accounting is invalid")
    if rendered_calls > maximum_new_calls:
        raise InputError("runtime manifest exceeds consumed authorization call bound")

    output_name = PurePosixPath(track.effective_config.output_path).name
    track_path = _runtime_artifact_path(
        workspace_root, runtime_root, manifest.get("track_audio_path"), "track_audio_path"
    )
    if track_path.name != output_name:
        raise InputError("runtime assembled Track path differs from frozen output naming")
    track_audio = read_bytes_nofollow(track_path)
    if sha256_bytes(track_audio) != manifest.get("track_audio_sha256"):
        raise InputError("runtime assembled Track digest is invalid")
    _wav_lpcm(track_audio, track)
    stitching = manifest.get("stitching")
    if not isinstance(stitching, dict) or stitching.get("profile") != "sentence-boundary-partial-turn-v3":
        raise InputError("runtime stitching profile is missing or changed")


def _runtime_assessment(
    workspace_root: Path,
    plan: FrozenBatchPlan,
    track: FrozenTrackPlan,
    transaction_root: Path,
    authorization: _AuthorizationAssessment,
) -> _RuntimeAssessment:
    runtime_root = transaction_root / "runtime"
    before = _tree_inventory(runtime_root)
    findings: set[str] = set()
    if not before.safe:
        findings.add("runtime-evidence-unsafe")
    if not before.exists:
        findings.add("runtime-evidence-missing")
        return _RuntimeAssessment(before.sha256, False, tuple(sorted(findings)))
    if authorization.maximum_new_calls is None:
        findings.add("runtime-authorization-bound-missing")
        return _RuntimeAssessment(before.sha256, False, tuple(sorted(findings)))

    try:
        _config_path, config = _load_current_config(workspace_root, plan)
        catalog_track = _selected_catalog_track(config, track)
        pairs = _current_segments(workspace_root, config, catalog_track, track)
        runtime_config_path, _runtime_config = _load_narration_runtime(workspace_root, track)
        protected_runtime_sha256 = _runtime_fingerprint(runtime_config_path)
        _validate_runtime_manifest(
            workspace_root,
            runtime_root,
            track,
            pairs,
            authorization.maximum_new_calls,
        )
        # Re-read every mutable binding after artifact validation to reject races.
        _config_path_after, config_after = _load_current_config(workspace_root, plan)
        if config_after != config:
            raise InputError("production config changed during resume inspection")
        catalog_after = _selected_catalog_track(config_after, track)
        if catalog_after != catalog_track:
            raise InputError("effective Track config changed during resume inspection")
        if _current_segments(workspace_root, config_after, catalog_after, track) != pairs:
            raise InputError("selected source changed during resume inspection")
        if _runtime_fingerprint(runtime_config_path) != protected_runtime_sha256:
            raise InputError("protected runtime changed during resume inspection")
    except InputError:
        findings.add("runtime-evidence-invalid")

    after = _tree_inventory(runtime_root)
    if after.sha256 != before.sha256 or not after.safe:
        findings.add("runtime-evidence-changed-during-inspection")
    return _RuntimeAssessment(
        after.sha256,
        not findings,
        tuple(sorted(findings)),
    )


def _context_findings(
    workspace_root: Path,
    plan: FrozenBatchPlan,
    track: FrozenTrackPlan,
    book_root: Path,
) -> tuple[str, ...]:
    findings: set[str] = set()
    try:
        _config_path, config = _load_current_config(workspace_root, plan)
        expected_book_root = resolve_inside(
            workspace_root,
            (PurePosixPath(config.build_root) / config.book_id).as_posix(),
        )
        if expected_book_root != book_root:
            raise InputError("configured production root differs from plan layout")
        catalog_track = _selected_catalog_track(config, track)
        _current_segments(workspace_root, config, catalog_track, track)
        runtime_config_path, _runtime = _load_narration_runtime(workspace_root, track)
        _runtime_fingerprint(runtime_config_path)
    except InputError:
        findings.add("source-config-runtime-binding-invalid")
    return tuple(sorted(findings))


def _sealed_inspection(**values: Any) -> ResumeInspection:
    return seal_record(
        ResumeInspection(
            schema_version=RECORD_SCHEMA_VERSION,
            canonical_sha256="",
            **values,
        )
    )


def inspect_resume(
    workspace_root: Path,
    plan_path: Path,
    track_id: str,
    transaction_id: str,
) -> ResumeInspection:
    """Classify one transaction from local immutable evidence only.

    The returned classification is always one of :class:`ResumeClassification`.
    Evidence failures are represented as sanitized finding categories and a blocked
    classification rather than guessed recovery state.
    """

    root, absolute_plan, plan, track, store = _load_scope(
        workspace_root, plan_path, track_id, transaction_id
    )
    transaction_root = store.transaction_path(track_id, transaction_id)
    empty_runtime = _tree_inventory(transaction_root / "runtime")
    empty_attempt = _tree_inventory(transaction_root / "attempts")
    try:
        snapshot = store.inspect_transaction(track_id, transaction_id)
        if not snapshot.metadata.matches(TransactionSpec.from_plan(plan, track)):
            raise InputError("transaction metadata differs from frozen plan")
    except InputError:
        return _sealed_inspection(
            classification=ResumeClassification.BLOCKED_NEW_PLAN_REQUIRED,
            plan_id=plan.plan_id,
            plan_sha256=StrictRecordCodec(FrozenBatchPlan).sha256(plan),
            transaction_id=track.transaction_id,
            track_id=track.track_id,
            transaction_state=None,
            ledger_head_sha256=None,
            preflight_sha256=None,
            authorization_sha256=None,
            attempt_evidence_sha256=empty_attempt.sha256,
            runtime_evidence_sha256=empty_runtime.sha256,
            finding_categories=("ledger-evidence-invalid",),
            future_paid_attempt_requirements=_FUTURE_REQUIREMENTS,
            duplicate_charge_acknowledgement_required=False,
            duplicate_charge_binding_sha256=None,
        )

    context_findings = _context_findings(root, plan, track, store.book_root)
    authorization = _authorization_assessment(absolute_plan, plan, track, snapshot)
    attempt = _attempt_assessment(
        root, transaction_root, track, snapshot, authorization
    )
    runtime = _runtime_assessment(root, plan, track, transaction_root, authorization)
    findings = set((*context_findings, *authorization.findings, *attempt.findings))
    state = snapshot.state
    consumed = any(
        payload.event_type == "authorization-consumed" for payload in snapshot.payloads
    )

    early = {
        TransactionState.DISCOVERED,
        TransactionState.PLANNED,
        TransactionState.PREFLIGHT_PASSED,
        TransactionState.AUTHORIZATION_REQUIRED,
    }
    if state in early:
        if consumed or attempt.has_evidence or context_findings:
            classification = ResumeClassification.BLOCKED_NEW_PLAN_REQUIRED
        else:
            classification = ResumeClassification.NOTHING_TO_RESUME
            findings.discard("runtime-evidence-missing")
    elif state in {TransactionState.RUNNING, TransactionState.CHARGE_UNCERTAIN}:
        findings.update(runtime.findings)
        if context_findings or not authorization.valid:
            classification = ResumeClassification.BLOCKED_NEW_PLAN_REQUIRED
        elif attempt.valid_committed_result and attempt.native_return_code not in {None, 0}:
            classification = ResumeClassification.BLOCKED_NEW_PLAN_REQUIRED
        elif runtime.complete:
            classification = ResumeClassification.COMPLETE_ARTIFACTS_RECOVERABLE
        else:
            classification = ResumeClassification.CHARGE_UNCERTAIN_REVIEW_REQUIRED
    elif state is TransactionState.RENDERED:
        findings.update(runtime.findings)
        accepted_manually = snapshot.payloads[-1].event_type == "manual-artifacts-accepted"
        if (
            not context_findings
            and authorization.valid
            and runtime.complete
            and (
                accepted_manually
                or (
                    attempt.valid_committed_result
                    and attempt.native_return_code == 0
                )
            )
        ):
            classification = ResumeClassification.LOCAL_VALIDATION_AVAILABLE
        else:
            classification = ResumeClassification.BLOCKED_NEW_PLAN_REQUIRED
    elif state in {TransactionState.VALIDATED, TransactionState.DELIVERED}:
        findings.update(runtime.findings)
        classification = (
            ResumeClassification.NOTHING_TO_RESUME
            if not context_findings and authorization.valid and runtime.complete
            else ResumeClassification.BLOCKED_NEW_PLAN_REQUIRED
        )
    else:
        findings.update(runtime.findings)
        classification = ResumeClassification.BLOCKED_NEW_PLAN_REQUIRED

    requires_fresh_scope = classification is ResumeClassification.BLOCKED_NEW_PLAN_REQUIRED or (
        classification
        in {
            ResumeClassification.COMPLETE_ARTIFACTS_RECOVERABLE,
            ResumeClassification.CHARGE_UNCERTAIN_REVIEW_REQUIRED,
        }
        and consumed
    )
    duplicate_binding = (
        _duplicate_charge_binding(track.transaction_id, attempt.evidence_sha256)
        if attempt.possible_charge
        and classification
        in {
            ResumeClassification.BLOCKED_NEW_PLAN_REQUIRED,
            ResumeClassification.COMPLETE_ARTIFACTS_RECOVERABLE,
            ResumeClassification.CHARGE_UNCERTAIN_REVIEW_REQUIRED,
        }
        else None
    )
    return _sealed_inspection(
        classification=classification,
        plan_id=plan.plan_id,
        plan_sha256=StrictRecordCodec(FrozenBatchPlan).sha256(plan),
        transaction_id=track.transaction_id,
        track_id=track.track_id,
        transaction_state=state,
        ledger_head_sha256=snapshot.head_event_sha256,
        preflight_sha256=authorization.preflight_sha256,
        authorization_sha256=authorization.authorization_sha256,
        attempt_evidence_sha256=attempt.evidence_sha256,
        runtime_evidence_sha256=runtime.evidence_sha256,
        finding_categories=tuple(sorted(findings)),
        future_paid_attempt_requirements=(
            _FUTURE_REQUIREMENTS if requires_fresh_scope else ()
        ),
        duplicate_charge_acknowledgement_required=duplicate_binding is not None,
        duplicate_charge_binding_sha256=duplicate_binding,
    )


def _resolution_operation(disposition: ManualResolutionDisposition) -> tuple[str, str]:
    return {
        ManualResolutionDisposition.ACCEPT_COMPLETE_LOCAL_ARTIFACTS: (
            "manual-accept-complete-local-artifacts",
            "manual-artifacts-accepted",
        ),
        ManualResolutionDisposition.QUARANTINE_INVALID_ARTIFACTS: (
            "manual-quarantine-invalid-artifacts",
            "manual-artifacts-quarantined",
        ),
        ManualResolutionDisposition.ABANDON_UNCERTAIN_ATTEMPT: (
            "manual-abandon-uncertain-attempt",
            "manual-attempt-abandoned",
        ),
    }[disposition]


def _resolution_result_from_event(
    plan: FrozenBatchPlan,
    track: FrozenTrackPlan,
    disposition: ManualResolutionDisposition,
    snapshot: TransactionSnapshot,
) -> ManualResolutionResult | None:
    operation_id, _event_type = _resolution_operation(disposition)
    matches = tuple(
        (event, payload)
        for event, payload in zip(snapshot.events, snapshot.payloads, strict=True)
        if payload.operation_id == operation_id
    )
    if not matches:
        return None
    if len(matches) != 1:
        raise InputError("Manual resolution evidence is ambiguous")
    event, payload = matches[0]
    details = payload.details
    required_future = (
        _FUTURE_REQUIREMENTS if event.state_after is TransactionState.BLOCKED else ()
    )
    result = ManualResolutionResult(
        schema_version=RECORD_SCHEMA_VERSION,
        disposition=disposition,
        plan_id=plan.plan_id,
        plan_sha256=str(details.get("plan_sha256")),
        transaction_id=track.transaction_id,
        track_id=track.track_id,
        preflight_sha256=details.get("preflight_sha256"),  # type: ignore[arg-type]
        authorization_sha256=details.get("authorization_sha256"),  # type: ignore[arg-type]
        inspection_sha256=str(details.get("inspection_sha256")),
        attempt_evidence_sha256=str(details.get("attempt_evidence_sha256")),
        runtime_evidence_sha256=str(details.get("runtime_evidence_sha256")),
        state_after=event.state_after,
        resolved_at_utc=event.occurred_at_utc,
        evidence_retained=details.get("evidence_retained") is True,
        future_paid_attempt_requirements=required_future,
        duplicate_charge_acknowledgement_required=(
            details.get("duplicate_charge_acknowledgement_required") is True
        ),
        duplicate_charge_binding_sha256=details.get("duplicate_charge_binding_sha256"),  # type: ignore[arg-type]
        canonical_sha256="",
    )
    return seal_record(result)


def resolve_resume(
    workspace_root: Path,
    plan_path: Path,
    track_id: str,
    transaction_id: str,
    disposition: ManualResolutionDisposition,
    *,
    occurred_at_utc: str | None = None,
) -> ManualResolutionResult:
    """Apply one explicit nonbillable disposition while retaining all evidence."""

    if not isinstance(disposition, ManualResolutionDisposition):
        raise InputError("Manual resolution requires an enumerated disposition")
    root, absolute_plan, plan, track, store = _load_scope(
        workspace_root, plan_path, track_id, transaction_id
    )
    del root  # Scope validation is intentional; resolution performs no external work.
    snapshot = store.inspect_transaction(track_id, transaction_id)
    if not snapshot.metadata.matches(TransactionSpec.from_plan(plan, track)):
        raise InputError("Transaction identity differs from frozen plan")
    existing = _resolution_result_from_event(plan, track, disposition, snapshot)
    if existing is not None:
        return existing

    inspection = inspect_resume(
        workspace_root, absolute_plan, track_id, transaction_id
    )
    if snapshot.state not in {TransactionState.RUNNING, TransactionState.CHARGE_UNCERTAIN}:
        raise InputError("Manual resolution requires running or charge-uncertain transaction truth")
    if disposition is ManualResolutionDisposition.ACCEPT_COMPLETE_LOCAL_ARTIFACTS:
        if inspection.classification is not ResumeClassification.COMPLETE_ARTIFACTS_RECOVERABLE:
            raise InputError("Complete local artifacts did not pass offline recovery validation")
        state_after = TransactionState.RENDERED
    elif disposition is ManualResolutionDisposition.QUARANTINE_INVALID_ARTIFACTS:
        if inspection.classification is ResumeClassification.COMPLETE_ARTIFACTS_RECOVERABLE:
            raise InputError("Validated complete artifacts are not invalid quarantine candidates")
        state_after = TransactionState.BLOCKED
    else:
        state_after = TransactionState.BLOCKED

    timestamp = _clock_value(occurred_at_utc)
    common_details: dict[str, str | int | bool | None] = {
        "plan_sha256": inspection.plan_sha256,
        "preflight_sha256": inspection.preflight_sha256,
        "authorization_sha256": inspection.authorization_sha256,
        "inspection_sha256": inspection.canonical_sha256,
        "attempt_evidence_sha256": inspection.attempt_evidence_sha256,
        "runtime_evidence_sha256": inspection.runtime_evidence_sha256,
        "evidence_retained": True,
        "automatic_retry_performed": False,
        "external_calls_performed": 0,
        "duplicate_charge_acknowledgement_required": (
            inspection.duplicate_charge_acknowledgement_required
        ),
        "duplicate_charge_binding_sha256": inspection.duplicate_charge_binding_sha256,
    }
    if snapshot.state is TransactionState.RUNNING:
        store.append_transition(
            track_id,
            transaction_id,
            operation_id="manual-normalize-charge-uncertain",
            event_type="manual-charge-uncertain",
            state_after=TransactionState.CHARGE_UNCERTAIN,
            details=common_details,
            occurred_at_utc=timestamp,
        )

    operation_id, event_type = _resolution_operation(disposition)
    event = store.append_transition(
        track_id,
        transaction_id,
        operation_id=operation_id,
        event_type=event_type,
        state_after=state_after,
        details=common_details,
        occurred_at_utc=timestamp,
    )
    result = ManualResolutionResult(
        schema_version=RECORD_SCHEMA_VERSION,
        disposition=disposition,
        plan_id=plan.plan_id,
        plan_sha256=inspection.plan_sha256,
        transaction_id=transaction_id,
        track_id=track_id,
        preflight_sha256=inspection.preflight_sha256,
        authorization_sha256=inspection.authorization_sha256,
        inspection_sha256=inspection.canonical_sha256,
        attempt_evidence_sha256=inspection.attempt_evidence_sha256,
        runtime_evidence_sha256=inspection.runtime_evidence_sha256,
        state_after=state_after,
        resolved_at_utc=event.occurred_at_utc,
        evidence_retained=True,
        future_paid_attempt_requirements=(
            _FUTURE_REQUIREMENTS if state_after is TransactionState.BLOCKED else ()
        ),
        duplicate_charge_acknowledgement_required=(
            inspection.duplicate_charge_acknowledgement_required
        ),
        duplicate_charge_binding_sha256=inspection.duplicate_charge_binding_sha256,
        canonical_sha256="",
    )
    return seal_record(result)


def create_exact_duplicate_charge_acknowledgement(
    subject: ResumeInspection | ManualResolutionResult,
    decision: DuplicateChargeDecision,
    *,
    acknowledged_at_utc: str | None = None,
) -> ExactDuplicateChargeAcknowledgement:
    """Create an explicit acknowledgement bound to one retained attempt tree."""

    if not isinstance(subject, (ResumeInspection, ManualResolutionResult)):
        raise InputError("Duplicate-charge acknowledgement subject is invalid")
    if not subject.duplicate_charge_acknowledgement_required:
        raise InputError("Subject does not contain a possible duplicate-charge condition")
    if decision is not DuplicateChargeDecision.ACKNOWLEDGE_EXACT_RETAINED_ATTEMPT:
        raise InputError("Explicit exact duplicate-charge acknowledgement was not supplied")
    acknowledgement = ExactDuplicateChargeAcknowledgement(
        schema_version=RECORD_SCHEMA_VERSION,
        prior_transaction_id=subject.transaction_id,
        retained_attempt_sha256=subject.attempt_evidence_sha256,
        binding_sha256=_duplicate_charge_binding(
            subject.transaction_id, subject.attempt_evidence_sha256
        ),
        decision=decision,
        acknowledged_at_utc=_require_utc(
            acknowledged_at_utc or utc_now(),
            "duplicate-charge acknowledgement timestamp",
        ),
        canonical_sha256="",
    )
    return seal_record(acknowledgement)


def validate_replacement_paid_attempt_requirements(
    subject: ResumeInspection | ManualResolutionResult,
    replacement_plan: FrozenBatchPlan,
    replacement_preflight_sha256: str,
    replacement_authorization: PaidAuthorization,
    acknowledgement: ExactDuplicateChargeAcknowledgement | None,
) -> None:
    """Enforce the complete fresh scope before any possible later paid attempt.

    This is a pure local validation gate.  It does not create or consume an
    authorization and cannot launch a child or make an external call.
    """

    if not isinstance(subject, (ResumeInspection, ManualResolutionResult)):
        raise InputError("Replacement-attempt subject is invalid")
    if subject.future_paid_attempt_requirements != _FUTURE_REQUIREMENTS:
        raise InputError("This recovery outcome does not permit another paid attempt")
    StrictRecordCodec(FrozenBatchPlan).dump_bytes(replacement_plan)
    StrictRecordCodec(PaidAuthorization).dump_bytes(replacement_authorization)
    if not _is_sha256(replacement_preflight_sha256):
        raise InputError("Replacement preflight digest is malformed")
    matches = tuple(
        item for item in replacement_plan.tracks if item.track_id == subject.track_id
    )
    if len(matches) != 1:
        raise InputError("Replacement plan must contain the exact affected Track once")
    replacement_track = matches[0]
    if replacement_track.transaction_id == subject.transaction_id:
        raise InputError("A later paid attempt requires a new transaction")
    replacement_plan_sha256 = StrictRecordCodec(FrozenBatchPlan).sha256(replacement_plan)
    if replacement_plan_sha256 == subject.plan_sha256 or replacement_plan.plan_id == subject.plan_id:
        raise InputError("A later paid attempt requires a new immutable plan")
    if replacement_preflight_sha256 == subject.preflight_sha256:
        raise InputError("A later paid attempt requires a new preflight")
    if (
        replacement_authorization.plan_sha256 != replacement_plan_sha256
        or replacement_authorization.preflight_sha256 != replacement_preflight_sha256
        or replacement_authorization.exact_transaction_ids
        != tuple(item.transaction_id for item in replacement_plan.tracks)
        or replacement_authorization.exact_track_ids
        != tuple(item.track_id for item in replacement_plan.tracks)
        or replacement_authorization.exact_command_sha256s
        != tuple(item.command_sha256 for item in replacement_plan.tracks)
        or replacement_authorization.authorization_id == ""
        or replacement_authorization.canonical_sha256 == subject.authorization_sha256
    ):
        raise InputError("A later paid attempt requires a new exact authorization")
    for item in replacement_plan.tracks:
        bound = replacement_authorization.maximum_new_calls_by_track.get(item.track_id)
        if type(bound) is not int or not (0 <= bound <= item.maximum_new_calls):
            raise InputError("Replacement authorization call bounds exceed the new plan")

    if subject.duplicate_charge_acknowledgement_required:
        if acknowledgement is None:
            raise InputError("Exact duplicate-charge acknowledgement is required")
        StrictRecordCodec(ExactDuplicateChargeAcknowledgement).dump_bytes(acknowledgement)
        if (
            acknowledgement.prior_transaction_id != subject.transaction_id
            or acknowledgement.retained_attempt_sha256
            != subject.attempt_evidence_sha256
            or acknowledgement.binding_sha256
            != subject.duplicate_charge_binding_sha256
            or acknowledgement.decision
            is not DuplicateChargeDecision.ACKNOWLEDGE_EXACT_RETAINED_ATTEMPT
        ):
            raise InputError("Duplicate-charge acknowledgement does not bind retained evidence")
    elif acknowledgement is not None:
        raise InputError("Unexpected duplicate-charge acknowledgement for definitive prelaunch evidence")


__all__ = [
    "DuplicateChargeDecision",
    "ExactDuplicateChargeAcknowledgement",
    "ManualResolutionDisposition",
    "ManualResolutionResult",
    "ResumeClassification",
    "ResumeInspection",
    "create_exact_duplicate_charge_acknowledgement",
    "inspect_resume",
    "resolve_resume",
    "validate_replacement_paid_attempt_requirements",
]
