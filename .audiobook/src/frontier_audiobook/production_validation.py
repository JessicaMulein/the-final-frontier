"""Fail-closed frozen-plan, manifest, and exact-fidelity validation.

The validator reads one immutable Frozen Track plan, one committed direct-child
attempt, and private runtime artifacts.  Transcript and event bodies are consumed
only in memory from the transaction runtime root.  Persisted evidence contains
only artifact digests, counts, statuses, and sanitized finding categories.  This
module never imports an AWS adapter, launches a child, or performs usage/cost
accounting.
"""

from __future__ import annotations

import math
import os
import re
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Any

from .errors import InputError
from .narrate import (
    Segment,
    StitchAudioSettings,
    StitchSegment,
    assembled_lpcm_duration_seconds,
    stitch_profile,
    stitch_track_lpcm,
)
from .nova import _mid_sentence_partial_turn_count, replay_output_events
from .production import load_production_plan
from .production_models import (
    RECORD_SCHEMA_VERSION,
    AttemptResult,
    FrozenBatchPlan,
    FrozenTrackPlan,
    StrictRecordCodec,
    TransactionState,
    ValidationCheck,
    ValidationEvidence,
    ValidationStatus,
    canonical_sha256,
    seal_record,
)
from .production_preflight import _load_event_journal, _wav_lpcm
from .production_transactions import TransactionSpec, TransactionStore
from .util import (
    durable_mkdir,
    json_loads_strict,
    normalize_lf_nfc,
    read_bytes_nofollow,
    resolve_inside,
    sha256_bytes,
    sha256_text,
    utc_now,
    workspace_relative,
)
from .verify import compare_transcript, normalized_tokens

Clock = Callable[[], datetime]

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_SEGMENT_ID = re.compile(r"^segment-(\d+)$")
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
_CONTENT_ADDRESSED_VALIDATION = re.compile(
    r"^frozen-manifest-([0-9a-f]{64})\.json$"
)

_ACCEPTED_ACTIVE_STATUSES = frozenset({"accepted", "narrated", "reused"})
_NON_ACTIVE_BUCKETS = (
    "carried_over_segments",
    "historical_segments",
    "rejected_segments",
)

_REQUIRED_MANIFEST_FIELDS = frozenset(
    {
        "track_id",
        "transaction_id",
        "track_plan_sha256",
        "effective_config_sha256",
        "source_snapshot_sha256",
        "track_kind",
        "sequence",
        "voice_id",
        "model_id",
        "region",
        "profile_label",
        "fidelity_policy",
        "normalization",
        "audio_sample_rate_hz",
        "audio_sample_size_bits",
        "audio_channels",
        "audio_encoding",
        "output_path",
        "source_path",
        "source_kind",
        "source_section",
        "source_sha256",
        "normalized_body_sha256",
        "spoken_sha256",
        "declared_word_count",
        "normalized_word_count",
        "word_count",
        "spoken_token_count",
        "segment_count",
        "active_segment_count",
        "narration_only_punctuation_segments",
        "target_segment_words",
        "safe_request_max_characters",
        "safe_request_max_words",
        "segment_boundary_policy",
        "render_identity_schema",
        "render_context_radius",
        "maximum_new_calls",
        "billable_calls_made",
        "segments",
        "carried_over_segments",
        "track_audio_path",
        "track_audio_sha256",
        "track_audio_byte_count",
        "track_duration_seconds",
        "stitching",
        "updated_at",
    }
)
_ALLOWED_MANIFEST_FIELDS = _REQUIRED_MANIFEST_FIELDS | frozenset(
    {"historical_segments", "rejected_segments"}
)

_REQUIRED_ACTIVE_FIELDS = frozenset(
    {
        "segment_id",
        "paragraph_index",
        "text",
        "text_sha256",
        "render_identity_sha256",
        "word_count",
        "narration_only_punctuation",
        "status",
        "audio_path",
        "audio_sha256",
        "transcript_path",
        "transcript_sha256",
        "event_journal_path",
        "event_journal_sha256",
        "duration_seconds",
        "transcript",
        "exact_transcript_match",
        "coverage_ratio",
        "event_replay_passed",
        "mid_sentence_partial_turns",
        "rendered_in_current_attempt",
    }
)
_ALLOWED_ACTIVE_FIELDS = _REQUIRED_ACTIVE_FIELDS | frozenset(
    {"call_ordinal", "narrated_at"}
)

_CHECKS = (
    ("attempt.committed-native-zero", "attempt-evidence-invalid"),
    ("manifest.schema", "manifest-schema-invalid"),
    ("manifest.frozen-plan-binding", "manifest-plan-binding-invalid"),
    ("manifest.active-set", "manifest-active-set-invalid"),
    ("manifest.token-conservation", "manifest-token-conservation-invalid"),
    ("manifest.path-confinement", "manifest-path-confinement-invalid"),
    ("manifest.history-exclusion", "manifest-history-exclusion-invalid"),
    ("fidelity.hash-bindings", "runtime-artifact-digest-invalid"),
    ("fidelity.exact-transcript", "exact-transcript-invalid"),
    ("fidelity.event-replay", "event-replay-invalid"),
    ("fidelity.lpcm-equality", "reconstructed-lpcm-invalid"),
    ("fidelity.partial-turns", "partial-turn-invalid"),
    ("assembly.source-current", "assembly-source-invalid"),
    ("assembly.stitching", "assembly-stitching-invalid"),
    ("assembly.wav-integrity", "assembled-wav-integrity-invalid"),
    ("evidence.sanitization", "evidence-sanitization-invalid"),
)


def _format_utc(value: datetime) -> str:
    rendered = value.astimezone(UTC).isoformat(timespec="microseconds")
    if rendered.endswith(".000000+00:00"):
        return rendered.replace(".000000+00:00", "Z")
    return rendered.replace("+00:00", "Z")


def _validated_at(value: str | None, clock: Clock | None) -> str:
    if value is not None and clock is not None:
        raise InputError("Specify validated_at_utc or clock, not both")
    if value is None:
        if clock is None:
            value = utc_now()
        else:
            try:
                current = clock()
            except Exception as exc:
                raise InputError("Validation clock failed") from exc
            if not isinstance(current, datetime) or current.tzinfo is None:
                raise InputError("Validation clock must return an aware datetime")
            value = _format_utc(current)
    if not isinstance(value, str) or not _UTC.fullmatch(value):
        raise InputError("Validation timestamp must be canonical UTC")
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise InputError("Validation timestamp is invalid") from exc
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise InputError("Validation timestamp must be UTC")
    return value


def _sentinel_digest(artifact: str, state: str) -> str:
    return canonical_sha256(
        {
            "schema": "frontier-structural-validation-unavailable-v1",
            "artifact": artifact,
            "state": state,
        }
    )


def _resolve_plan_path(workspace_root: Path, plan_path: Path) -> Path:
    candidate = plan_path.expanduser()
    if candidate.is_absolute():
        relative = workspace_relative(workspace_root, candidate)
    else:
        relative = candidate.as_posix()
    return resolve_inside(workspace_root, relative)


def _load_exact_scope(
    workspace_root: Path,
    plan_path: Path,
    track_id: str,
    transaction_id: str,
) -> tuple[Path, FrozenBatchPlan, FrozenTrackPlan, Path, TransactionStore]:
    if not isinstance(track_id, str) or not _IDENTIFIER.fullmatch(track_id):
        raise InputError("Validation track_id is not canonical")
    if not isinstance(transaction_id, str) or not _IDENTIFIER.fullmatch(transaction_id):
        raise InputError("Validation transaction_id is not canonical")
    absolute_plan = _resolve_plan_path(workspace_root, plan_path)
    plan = load_production_plan(absolute_plan)
    if (
        absolute_plan.name != "plan.json"
        or absolute_plan.parent.name != plan.plan_id
        or absolute_plan.parent.parent.name != "plans"
        or absolute_plan.parent.parent.parent.name != plan.book_id
    ):
        raise InputError("Frozen plan path does not match the production plan layout")
    matches = tuple(
        track
        for track in plan.tracks
        if track.track_id == track_id and track.transaction_id == transaction_id
    )
    if len(matches) != 1:
        raise InputError("Validation scope is not one exact Frozen Track plan")
    book_root = absolute_plan.parent.parent.parent
    store = TransactionStore(book_root, plan.book_id)
    transaction_root = store.transaction_path(track_id, transaction_id)
    try:
        transaction_root.relative_to(book_root)
    except ValueError as exc:  # pragma: no cover - identifiers make this defensive
        raise InputError("Transaction path escapes the production book root") from exc
    return absolute_plan, plan, matches[0], transaction_root, store


def _artifact_reference(
    workspace_root: Path,
    path: Path,
) -> tuple[str | None, str | None]:
    try:
        raw = read_bytes_nofollow(path)
        return workspace_relative(workspace_root, path), sha256_bytes(raw)
    except InputError:
        return None, None


def _attempt_issues(
    workspace_root: Path,
    plan: FrozenBatchPlan,
    track: FrozenTrackPlan,
    transaction_root: Path,
    store: TransactionStore,
) -> tuple[list[str], str, str | None, str | None]:
    issues: list[str] = []
    attempt_sha256 = _sentinel_digest("attempt", "unavailable")
    artifact_path: str | None = None
    artifact_sha256: str | None = None
    attempts_root = transaction_root / "attempts"

    if attempts_root.is_symlink() or not attempts_root.is_dir():
        return ["attempt-root-missing-or-unsafe"], attempt_sha256, None, None
    try:
        entries = tuple(sorted(attempts_root.iterdir(), key=lambda item: item.name))
    except OSError:
        return ["attempt-root-unreadable"], attempt_sha256, None, None
    committed = tuple(
        item for item in entries if not item.is_symlink() and item.is_dir()
    )
    if len(entries) != 1 or len(committed) != 1:
        return ["attempt-scope-ambiguous"], attempt_sha256, None, None

    bundle = committed[0]
    try:
        bundle_entries = tuple(sorted(bundle.iterdir(), key=lambda item: item.name))
    except OSError:
        return ["attempt-bundle-unreadable"], attempt_sha256, None, None
    if (
        {item.name for item in bundle_entries}
        != {"attempt.json", "render-console.log"}
        or any(item.is_symlink() or not item.is_file() for item in bundle_entries)
    ):
        issues.append("attempt-bundle-ambiguous")

    result_path = bundle / "attempt.json"
    console_path = bundle / "render-console.log"
    artifact_path, artifact_sha256 = _artifact_reference(workspace_root, result_path)
    if artifact_sha256 is not None:
        attempt_sha256 = artifact_sha256
    try:
        result_raw = read_bytes_nofollow(result_path)
        result = StrictRecordCodec(AttemptResult).loads(
            result_raw,
            label="committed attempt result",
        )
    except InputError:
        issues.append("attempt-result-malformed")
        return issues, attempt_sha256, artifact_path, artifact_sha256

    expected_console = workspace_relative(workspace_root, console_path)
    try:
        console_raw = read_bytes_nofollow(console_path)
    except InputError:
        issues.append("attempt-console-missing-or-unsafe")
        console_raw = None
    if result.native_return_code != 0:
        issues.append("attempt-native-status-nonzero")
    if result.termination_signal is not None:
        issues.append("attempt-termination-signal-present")
    if (
        result.transaction_id != track.transaction_id
        or result.argv != track.command_argv
        or result.command_sha256 != track.command_sha256
        or track.command_sha256 != canonical_sha256(track.command_argv)
        or result.profile_label != track.effective_config.profile_label
        or result.working_directory != "."
        or result.console_path != expected_console
    ):
        issues.append("attempt-frozen-binding-mismatch")
    if console_raw is not None:
        from .production_evidence import scan_sanitized_console

        console_findings = scan_sanitized_console(
            console_raw,
            artifact_path=expected_console,
        )
        for finding in console_findings:
            issues.extend(
                f"attempt-console-sanitization-{finding.category}-{index}"
                for index in range(finding.count)
            )
        if sha256_bytes(console_raw) != result.console_sha256:
            issues.append("attempt-console-digest-mismatch")

    try:
        snapshot = store.inspect_transaction(track.track_id, track.transaction_id)
    except InputError:
        issues.append("attempt-ledger-invalid")
    else:
        if not snapshot.metadata.matches(TransactionSpec.from_plan(plan, track)):
            issues.append("attempt-transaction-plan-mismatch")
        if snapshot.state is not TransactionState.RENDERED:
            issues.append("attempt-transaction-not-rendered")
        consumed = tuple(
            payload
            for payload in snapshot.payloads
            if payload.event_type == "authorization-consumed"
        )
        rendered = tuple(
            payload
            for payload in snapshot.payloads
            if payload.event_type == "attempt-rendered"
        )
        blocking = tuple(
            payload
            for payload in snapshot.payloads
            if payload.event_type in {"attempt-nonzero", "attempt-charge-uncertain"}
        )
        result_digest = StrictRecordCodec(AttemptResult).sha256(result)
        if (
            len(consumed) != 1
            or consumed[0].details.get("attempt_id") != result.attempt_id
            or consumed[0].details.get("authorization_sha256")
            != result.authorization_sha256
            or consumed[0].details.get("command_sha256") != track.command_sha256
            or consumed[0].details.get("one_shot") is not True
            or consumed[0].details.get("automatic_retry_performed") is not False
        ):
            issues.append("attempt-consumption-binding-invalid")
        if (
            len(rendered) != 1
            or rendered[0].details.get("attempt_id") != result.attempt_id
            or rendered[0].details.get("authorization_sha256")
            != result.authorization_sha256
            or rendered[0].details.get("attempt_result_sha256") != result_digest
            or rendered[0].details.get("console_sha256") != result.console_sha256
            or rendered[0].details.get("native_return_code") != 0
            or rendered[0].details.get("termination_signal") is not None
            or rendered[0].details.get("automatic_retry_performed") is not False
            or blocking
        ):
            issues.append("attempt-completion-binding-invalid")

    try:
        if read_bytes_nofollow(result_path) != result_raw:
            issues.append("attempt-result-changed-during-validation")
        if console_raw is not None and read_bytes_nofollow(console_path) != console_raw:
            issues.append("attempt-console-changed-during-validation")
        if tuple(sorted(item.name for item in attempts_root.iterdir())) != (
            bundle.name,
        ):
            issues.append("attempt-scope-changed-during-validation")
    except (InputError, OSError):
        issues.append("attempt-evidence-changed-during-validation")

    return issues, attempt_sha256, artifact_path, artifact_sha256


def _load_manifest(
    workspace_root: Path,
    manifest_path: Path,
) -> tuple[dict[str, Any] | None, bytes | None, str, str | None, str | None, list[str]]:
    unavailable = _sentinel_digest("manifest", "unavailable")
    artifact_path: str | None = None
    artifact_sha256: str | None = None
    issues: list[str] = []
    try:
        raw = read_bytes_nofollow(manifest_path)
        artifact_path = workspace_relative(workspace_root, manifest_path)
        artifact_sha256 = sha256_bytes(raw)
    except InputError:
        return None, None, unavailable, None, None, ["manifest-missing-or-unsafe"]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        return None, raw, artifact_sha256, artifact_path, artifact_sha256, [
            "manifest-utf8-invalid"
        ]
    try:
        value = json_loads_strict(text, "runtime manifest")
    except InputError:
        return None, raw, artifact_sha256, artifact_path, artifact_sha256, [
            "manifest-json-invalid"
        ]
    if not isinstance(value, dict):
        issues.append("manifest-root-not-object")
        return None, raw, artifact_sha256, artifact_path, artifact_sha256, issues
    return value, raw, artifact_sha256, artifact_path, artifact_sha256, issues


def _is_int(value: object, *, minimum: int = 0) -> bool:
    return type(value) is int and value >= minimum


def _is_number(value: object, *, minimum: float = 0.0) -> bool:
    return type(value) in {int, float} and math.isfinite(float(value)) and value >= minimum


def _is_text(value: object) -> bool:
    return isinstance(value, str) and bool(value) and "\x00" not in value


def _is_sha256(value: object) -> bool:
    return isinstance(value, str) and _SHA256.fullmatch(value) is not None


def _is_utc(value: object) -> bool:
    if not isinstance(value, str) or not _UTC.fullmatch(value):
        return False
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError:
        return False
    return parsed.utcoffset() is not None and parsed.utcoffset().total_seconds() == 0


def _manifest_schema_issues(manifest: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    names = set(manifest)
    if names - _ALLOWED_MANIFEST_FIELDS:
        issues.append("manifest-unknown-fields")
    if _REQUIRED_MANIFEST_FIELDS - names:
        issues.append("manifest-required-fields-missing")

    text_fields = (
        "track_id",
        "transaction_id",
        "track_kind",
        "voice_id",
        "model_id",
        "region",
        "profile_label",
        "fidelity_policy",
        "normalization",
        "audio_encoding",
        "output_path",
        "source_path",
        "source_kind",
        "source_sha256",
        "normalized_body_sha256",
        "spoken_sha256",
        "segment_boundary_policy",
        "render_identity_schema",
        "track_audio_path",
        "track_audio_sha256",
    )
    for name in text_fields:
        if name in manifest and not _is_text(manifest[name]):
            issues.append(f"manifest-{name}-type")
    for name in (
        "track_plan_sha256",
        "effective_config_sha256",
        "source_snapshot_sha256",
        "source_sha256",
        "normalized_body_sha256",
        "spoken_sha256",
        "track_audio_sha256",
    ):
        if name in manifest and not _is_sha256(manifest[name]):
            issues.append(f"manifest-{name}-digest")
    if "source_section" in manifest and manifest["source_section"] is not None and not _is_text(
        manifest["source_section"]
    ):
        issues.append("manifest-source-section-type")
    if "declared_word_count" in manifest and manifest["declared_word_count"] is not None and not _is_int(
        manifest["declared_word_count"]
    ):
        issues.append("manifest-declared-word-count-type")
    for name in (
        "sequence",
        "audio_sample_rate_hz",
        "audio_sample_size_bits",
        "audio_channels",
        "normalized_word_count",
        "word_count",
        "spoken_token_count",
        "segment_count",
        "active_segment_count",
        "narration_only_punctuation_segments",
        "target_segment_words",
        "safe_request_max_characters",
        "safe_request_max_words",
        "render_context_radius",
        "maximum_new_calls",
        "billable_calls_made",
        "track_audio_byte_count",
    ):
        minimum = 1 if name in {
            "sequence",
            "audio_sample_rate_hz",
            "audio_sample_size_bits",
            "audio_channels",
            "word_count",
            "spoken_token_count",
            "segment_count",
            "active_segment_count",
            "target_segment_words",
            "safe_request_max_characters",
            "safe_request_max_words",
            "track_audio_byte_count",
        } else 0
        if name in manifest and not _is_int(manifest[name], minimum=minimum):
            issues.append(f"manifest-{name}-type")
    if "track_duration_seconds" in manifest and not _is_number(
        manifest["track_duration_seconds"]
    ):
        issues.append("manifest-track-duration-type")
    if "stitching" in manifest and not isinstance(manifest["stitching"], dict):
        issues.append("manifest-stitching-type")
    if "updated_at" in manifest and not _is_utc(manifest["updated_at"]):
        issues.append("manifest-updated-at-type")

    segments = manifest.get("segments")
    if not isinstance(segments, list):
        issues.append("manifest-segments-type")
    else:
        for index, entry in enumerate(segments):
            if not isinstance(entry, dict):
                issues.append(f"manifest-active-{index}-type")
                continue
            fields = set(entry)
            if fields - _ALLOWED_ACTIVE_FIELDS:
                issues.append(f"manifest-active-{index}-unknown-fields")
            if _REQUIRED_ACTIVE_FIELDS - fields:
                issues.append(f"manifest-active-{index}-missing-fields")
            for name in (
                "segment_id",
                "text",
                "text_sha256",
                "render_identity_sha256",
                "status",
                "audio_path",
                "audio_sha256",
                "transcript_path",
                "transcript_sha256",
                "event_journal_path",
                "event_journal_sha256",
            ):
                if name in entry and not _is_text(entry[name]):
                    issues.append(f"manifest-active-{index}-{name}-type")
            for name in (
                "text_sha256",
                "render_identity_sha256",
                "audio_sha256",
                "transcript_sha256",
                "event_journal_sha256",
            ):
                if name in entry and not _is_sha256(entry[name]):
                    issues.append(f"manifest-active-{index}-{name}-digest")
            for name in (
                "paragraph_index",
                "word_count",
                "mid_sentence_partial_turns",
            ):
                minimum = 1 if name == "word_count" else 0
                if name in entry and not _is_int(entry[name], minimum=minimum):
                    issues.append(f"manifest-active-{index}-{name}-type")
            for name in (
                "narration_only_punctuation",
                "exact_transcript_match",
                "event_replay_passed",
                "rendered_in_current_attempt",
            ):
                if name in entry and type(entry[name]) is not bool:
                    issues.append(f"manifest-active-{index}-{name}-type")
            if "duration_seconds" in entry and not _is_number(entry["duration_seconds"]):
                issues.append(f"manifest-active-{index}-duration-type")
            if "coverage_ratio" in entry and not _is_number(entry["coverage_ratio"]):
                issues.append(f"manifest-active-{index}-coverage-type")
            if "transcript" in entry and not isinstance(entry["transcript"], str):
                issues.append(f"manifest-active-{index}-transcript-type")
            if "call_ordinal" in entry and not _is_int(entry["call_ordinal"], minimum=1):
                issues.append(f"manifest-active-{index}-call-ordinal-type")
            if "narrated_at" in entry and not _is_utc(entry["narrated_at"]):
                issues.append(f"manifest-active-{index}-narrated-at-type")

    for bucket in _NON_ACTIVE_BUCKETS:
        if bucket not in manifest:
            continue
        records = manifest[bucket]
        if not isinstance(records, list) or any(not isinstance(item, dict) for item in records):
            issues.append(f"manifest-{bucket}-type")
    return issues


def _frozen_binding_issues(
    plan: FrozenBatchPlan,
    track: FrozenTrackPlan,
    manifest: Mapping[str, Any],
) -> list[str]:
    source = track.source
    effective = track.effective_config
    audio = effective.audio_format
    expected: Mapping[str, object] = {
        "track_id": track.track_id,
        "transaction_id": track.transaction_id,
        "track_plan_sha256": canonical_sha256(track),
        "effective_config_sha256": canonical_sha256(effective),
        "source_snapshot_sha256": canonical_sha256(source),
        "track_kind": effective.track_kind.value,
        "sequence": track.sequence,
        "voice_id": effective.voice,
        "model_id": effective.model_id,
        "region": effective.region,
        "profile_label": effective.profile_label,
        "fidelity_policy": effective.fidelity_policy.value,
        "normalization": effective.normalization,
        "audio_sample_rate_hz": audio.sample_rate_hz,
        "audio_sample_size_bits": audio.sample_size_bits,
        "audio_channels": audio.channels,
        "audio_encoding": audio.encoding.value,
        "output_path": effective.output_path,
        "source_path": source.source_path,
        "source_kind": source.source_kind.value,
        "source_section": source.source_section,
        "source_sha256": source.raw_sha256,
        "normalized_body_sha256": source.normalized_body_sha256,
        "spoken_sha256": source.spoken_sha256,
        "declared_word_count": source.declared_word_count,
        "normalized_word_count": source.normalized_word_count,
        "word_count": source.spoken_token_count,
        "spoken_token_count": source.spoken_token_count,
        "segment_count": source.segment_count,
        "narration_only_punctuation_segments": sum(
            item.narration_only_punctuation for item in source.segments
        ),
        "target_segment_words": effective.target_segment_words,
        "segment_boundary_policy": source.segmentation_policy,
        "render_identity_schema": source.render_identity_schema,
        "render_context_radius": source.render_context_radius,
    }
    issues = [
        f"manifest-{name}-mismatch"
        for name, value in expected.items()
        if manifest.get(name) != value
    ]
    maximum = manifest.get("maximum_new_calls")
    calls = manifest.get("billable_calls_made")
    if type(maximum) is int and maximum > track.maximum_new_calls:
        issues.append("manifest-maximum-calls-exceeds-plan")
    if type(maximum) is int and type(calls) is int and calls > maximum:
        issues.append("manifest-billable-calls-exceed-maximum")
    return issues


def _active_set_issues(
    track: FrozenTrackPlan,
    manifest: Mapping[str, Any],
) -> list[str]:
    entries = manifest["segments"]
    planned = track.source.segments
    issues: list[str] = []
    if manifest["active_segment_count"] != len(entries):
        issues.append("manifest-active-count-mismatch")
    if len(entries) != track.source.segment_count:
        issues.append("manifest-active-set-incomplete")
    ids = tuple(entry["segment_id"] for entry in entries)
    planned_ids = tuple(item.segment_id for item in planned)
    if len(set(ids)) != len(ids):
        issues.append("manifest-active-ids-duplicate")
    if ids != planned_ids:
        issues.append("manifest-active-order-mismatch")
    for ordinal, segment_id in enumerate(ids, start=1):
        match = _SEGMENT_ID.fullmatch(segment_id)
        if match is None or int(match.group(1)) != ordinal:
            issues.append("manifest-active-ids-not-contiguous")
            break
    if len(entries) == len(planned):
        for entry, snapshot in zip(entries, planned, strict=True):
            if (
                entry["paragraph_index"] != snapshot.paragraph_index
                or entry["text_sha256"] != snapshot.text_sha256
                or entry["render_identity_sha256"] != snapshot.render_identity_sha256
                or entry["word_count"] != snapshot.spoken_token_count
                or entry["narration_only_punctuation"]
                is not snapshot.narration_only_punctuation
            ):
                issues.append("manifest-active-segment-plan-mismatch")
    rendered = sum(entry["rendered_in_current_attempt"] is True for entry in entries)
    if manifest["billable_calls_made"] != rendered:
        issues.append("manifest-active-call-partition-mismatch")
    return issues


def _token_conservation_issues(
    track: FrozenTrackPlan,
    manifest: Mapping[str, Any],
) -> list[str]:
    entries = manifest["segments"]
    planned = track.source.segments
    if len(entries) != len(planned):
        return ["manifest-token-scope-incomplete"]
    issues: list[str] = []
    total = 0
    for entry, snapshot in zip(entries, planned, strict=True):
        text = entry["text"]
        canonical_text = " ".join(normalize_lf_nfc(text).split())
        try:
            tokens = tuple(normalized_tokens(text, track.effective_config.normalization))
        except InputError:
            issues.append("manifest-active-normalization-invalid")
            continue
        if (
            sha256_text(canonical_text) != snapshot.text_sha256
            or canonical_sha256(tokens) != snapshot.normalized_tokens_sha256
            or len(tokens) != snapshot.spoken_token_count
            or entry["word_count"] != len(tokens)
        ):
            issues.append("manifest-active-token-binding-mismatch")
        total += len(tokens)
    if total != track.source.spoken_token_count:
        issues.append("manifest-full-token-conservation-failed")
    return issues


def _confined_runtime_path(
    workspace_root: Path,
    runtime_root: Path,
    value: object,
    *,
    require_file: bool,
) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        from .util import resolve_inside_approved_root

        return resolve_inside_approved_root(
            workspace_root,
            runtime_root,
            value,
            require_exists=require_file,
            expected_kind="file" if require_file else None,
        )
    except InputError:
        return None


def _path_confinement_issues(
    workspace_root: Path,
    transaction_root: Path,
    track: FrozenTrackPlan,
    manifest: Mapping[str, Any],
) -> list[str]:
    runtime_root = transaction_root / "runtime"
    issues: list[str] = []
    if runtime_root.is_symlink() or not runtime_root.is_dir():
        return ["manifest-runtime-root-missing-or-unsafe"]
    try:
        source_path = resolve_inside(workspace_root, manifest["source_path"])
        output_path = resolve_inside(workspace_root, manifest["output_path"])
    except InputError:
        issues.append("manifest-source-or-output-path-unsafe")
    else:
        if manifest["source_path"] != track.source.source_path:
            issues.append("manifest-source-path-mismatch")
        if manifest["output_path"] != track.effective_config.output_path:
            issues.append("manifest-output-path-mismatch")
        if source_path.is_symlink() or not source_path.is_file():
            issues.append("manifest-source-path-missing-or-unsafe")
        # Delivery can legitimately be absent at validation time; resolving it is
        # sufficient here.  Collision-safe publication is a later operation.
        del output_path

    active_paths: set[str] = set()
    for entry, snapshot in zip(
        manifest["segments"], track.source.segments, strict=False
    ):
        stem = f"{snapshot.segment_id}-{snapshot.text_sha256}"
        expected_artifacts = (
            ("audio", "audio_path", runtime_root / "segments" / f"{stem}.wav"),
            (
                "transcript",
                "transcript_path",
                runtime_root / "transcripts" / f"{stem}.txt",
            ),
            (
                "event-journal",
                "event_journal_path",
                runtime_root / "events" / f"{stem}.jsonl",
            ),
        )
        for label, field_name, expected in expected_artifacts:
            artifact = _confined_runtime_path(
                workspace_root,
                runtime_root,
                entry.get(field_name),
                require_file=True,
            )
            if artifact is None:
                issues.append(
                    f"manifest-active-{label}-path-missing-or-unsafe"
                )
                continue
            if artifact != expected:
                issues.append(f"manifest-active-{label}-path-mismatch")
            relative = workspace_relative(workspace_root, artifact)
            if relative in active_paths:
                issues.append(f"manifest-active-{label}-path-duplicate")
            active_paths.add(relative)

    track_audio = _confined_runtime_path(
        workspace_root,
        runtime_root,
        manifest["track_audio_path"],
        require_file=True,
    )
    expected_track_audio = runtime_root / PurePosixPath(
        track.effective_config.output_path
    ).name
    if track_audio is None:
        issues.append("manifest-track-audio-path-missing-or-unsafe")
    elif track_audio != expected_track_audio:
        issues.append("manifest-track-audio-path-mismatch")

    for bucket in _NON_ACTIVE_BUCKETS:
        for entry in manifest.get(bucket, []):
            if "audio_path" not in entry:
                continue
            historical = _confined_runtime_path(
                workspace_root,
                runtime_root,
                entry["audio_path"],
                require_file=False,
            )
            if historical is None:
                issues.append("manifest-nonactive-audio-path-unsafe")
    return issues


def _history_exclusion_issues(manifest: Mapping[str, Any]) -> list[str]:
    issues: list[str] = []
    active = manifest["segments"]
    active_artifacts = {
        (entry.get("text_sha256"), entry.get("audio_path"), entry.get("audio_sha256"))
        for entry in active
    }
    active_paths = {entry.get("audio_path") for entry in active}
    if any(entry["status"] not in _ACCEPTED_ACTIVE_STATUSES for entry in active):
        issues.append("manifest-nonaccepted-record-in-active-set")
    for bucket in _NON_ACTIVE_BUCKETS:
        for entry in manifest.get(bucket, []):
            artifact = (
                entry.get("text_sha256"),
                entry.get("audio_path"),
                entry.get("audio_sha256"),
            )
            if artifact in active_artifacts or (
                entry.get("audio_path") is not None
                and entry.get("audio_path") in active_paths
            ):
                issues.append("manifest-active-nonactive-artifact-overlap")
    return issues


def _exact_fidelity_issue_sets(
    workspace_root: Path,
    transaction_root: Path,
    track: FrozenTrackPlan,
    manifest: Mapping[str, Any],
) -> tuple[list[str], list[str], list[str], list[str], list[str]]:
    """Validate private segment artifacts while returning only sanitized findings."""

    hash_issues: list[str] = []
    transcript_issues: list[str] = []
    event_issues: list[str] = []
    lpcm_issues: list[str] = []
    partial_issues: list[str] = []
    issue_sets = (
        hash_issues,
        transcript_issues,
        event_issues,
        lpcm_issues,
        partial_issues,
    )
    entries = manifest["segments"]
    if len(entries) != len(track.source.segments):
        for issues in issue_sets:
            issues.append("fidelity-active-scope-incomplete")
        return issue_sets

    runtime_root = transaction_root / "runtime"
    if runtime_root.is_symlink() or not runtime_root.is_dir():
        for issues in issue_sets:
            issues.append("fidelity-runtime-root-missing-or-unsafe")
        return issue_sets

    for entry, snapshot in zip(entries, track.source.segments, strict=True):
        canonical_text = " ".join(normalize_lf_nfc(entry["text"]).split())
        if (
            entry["text_sha256"] != snapshot.text_sha256
            or sha256_text(canonical_text) != snapshot.text_sha256
        ):
            hash_issues.append("segment-text-digest-mismatch")

        stem = f"{snapshot.segment_id}-{snapshot.text_sha256}"
        expected = {
            "audio": runtime_root / "segments" / f"{stem}.wav",
            "transcript": runtime_root / "transcripts" / f"{stem}.txt",
            "event": runtime_root / "events" / f"{stem}.jsonl",
        }
        field_names = {
            "audio": ("audio_path", "audio_sha256"),
            "transcript": ("transcript_path", "transcript_sha256"),
            "event": ("event_journal_path", "event_journal_sha256"),
        }
        paths: dict[str, Path] = {}
        content: dict[str, bytes] = {}
        for artifact, (path_field, digest_field) in field_names.items():
            path = _confined_runtime_path(
                workspace_root,
                runtime_root,
                entry[path_field],
                require_file=True,
            )
            if path is None or path != expected[artifact]:
                hash_issues.append(f"{artifact}-path-binding-invalid")
                continue
            paths[artifact] = path
            try:
                raw = read_bytes_nofollow(path)
            except InputError:
                hash_issues.append(f"{artifact}-unreadable")
                continue
            content[artifact] = raw
            if sha256_bytes(raw) != entry[digest_field]:
                hash_issues.append(f"{artifact}-digest-mismatch")

        transcript: str | None = None
        transcript_raw = content.get("transcript")
        if transcript_raw is None:
            transcript_issues.append("transcript-artifact-unavailable")
        else:
            try:
                decoded = transcript_raw.decode("utf-8")
            except UnicodeDecodeError:
                transcript_issues.append("transcript-utf8-invalid")
            else:
                if not decoded.endswith("\n"):
                    transcript_issues.append("transcript-framing-invalid")
                transcript = decoded.removesuffix("\n")
                if transcript != entry["transcript"]:
                    hash_issues.append("transcript-manifest-binding-mismatch")
                try:
                    verification = compare_transcript(
                        entry["text"],
                        transcript,
                        track.effective_config.normalization,
                    )
                except InputError:
                    transcript_issues.append("transcript-comparison-invalid")
                else:
                    if (
                        not verification.passed
                        or verification.coverage_ratio != 1.0
                        or entry["exact_transcript_match"] is not True
                        or entry["coverage_ratio"] != 1.0
                    ):
                        transcript_issues.append("transcript-exactness-failed")

        events: tuple[dict[str, Any], ...] | None = None
        replayed = None
        event_path = paths.get("event")
        if event_path is None or "event" not in content:
            event_issues.append("event-journal-unavailable")
        else:
            try:
                events = _load_event_journal(event_path)
                replayed = replay_output_events(events)
            except InputError:
                event_issues.append("event-replay-failed")
            else:
                try:
                    replay_verification = compare_transcript(
                        entry["text"],
                        replayed.final_transcript,
                        track.effective_config.normalization,
                    )
                    transcript_tokens = (
                        normalized_tokens(
                            transcript,
                            track.effective_config.normalization,
                        )
                        if transcript is not None
                        else ()
                    )
                    replay_tokens = normalized_tokens(
                        replayed.final_transcript,
                        track.effective_config.normalization,
                    )
                except InputError:
                    event_issues.append("event-transcript-comparison-invalid")
                else:
                    if (
                        not replay_verification.passed
                        or replay_verification.coverage_ratio != 1.0
                        or transcript is None
                        or transcript_tokens != replay_tokens
                        or entry["event_replay_passed"] is not True
                    ):
                        event_issues.append("event-transcript-binding-failed")
        if entry["event_replay_passed"] is not True:
            event_issues.append("event-replay-record-not-passed")

        lpcm: bytes | None = None
        audio_raw = content.get("audio")
        if audio_raw is None:
            lpcm_issues.append("segment-audio-unavailable")
        else:
            try:
                lpcm = _wav_lpcm(audio_raw, track)
            except InputError:
                lpcm_issues.append("segment-wav-lpcm-invalid")
        if replayed is None or lpcm is None:
            lpcm_issues.append("event-lpcm-prerequisite-invalid")
        elif replayed.audio_lpcm != lpcm:
            lpcm_issues.append("event-lpcm-mismatch")

        if entry["mid_sentence_partial_turns"] != 0:
            partial_issues.append("partial-turn-record-nonzero")
        if events is None:
            partial_issues.append("partial-turn-prerequisite-invalid")
        else:
            try:
                partial_count = _mid_sentence_partial_turn_count(events)
            except InputError:
                partial_issues.append("partial-turn-classification-invalid")
            else:
                if partial_count != 0:
                    partial_issues.append("mid-sentence-partial-turn-detected")

        for artifact, raw in content.items():
            try:
                if read_bytes_nofollow(paths[artifact]) != raw:
                    hash_issues.append(f"{artifact}-changed-during-validation")
            except InputError:
                hash_issues.append(f"{artifact}-changed-during-validation")

    return issue_sets


def _assembly_issue_sets(
    workspace_root: Path,
    transaction_root: Path,
    track: FrozenTrackPlan,
    manifest: Mapping[str, Any],
) -> tuple[list[str], list[str], list[str]]:
    """Reconstruct assembled LPCM and return only sanitized failure categories."""

    source_issues: list[str] = []
    stitching_issues: list[str] = []
    wav_issues: list[str] = []
    runtime_root = transaction_root / "runtime"

    source_raw: bytes | None = None
    try:
        source_path = resolve_inside(workspace_root, track.source.source_path)
        if source_path.is_symlink() or not source_path.is_file():
            raise InputError("Frozen source is missing or unsafe")
        source_raw = read_bytes_nofollow(source_path)
    except InputError:
        source_issues.append("assembly-source-unavailable")
    else:
        if sha256_bytes(source_raw) != track.source.raw_sha256:
            source_issues.append("assembly-source-digest-mismatch")

    if manifest.get("stitching") != stitch_profile():
        stitching_issues.append("assembly-stitch-profile-mismatch")

    entries = manifest["segments"]
    expected_ids = tuple(item.segment_id for item in track.source.segments)
    actual_ids = tuple(entry["segment_id"] for entry in entries)
    parts: list[StitchSegment] = []
    stable_artifacts: list[tuple[Path, bytes, str]] = []
    reconstruction_blocked = bool(source_issues)
    if source_issues:
        stitching_issues.append("assembly-source-prerequisite-invalid")
    if actual_ids != expected_ids or len(entries) != len(track.source.segments):
        stitching_issues.append("assembly-active-order-mismatch")
        reconstruction_blocked = True
    else:
        for ordinal, (entry, snapshot) in enumerate(
            zip(entries, track.source.segments, strict=True),
            start=1,
        ):
            stem = f"{snapshot.segment_id}-{snapshot.text_sha256}"
            expected_audio = runtime_root / "segments" / f"{stem}.wav"
            expected_event = runtime_root / "events" / f"{stem}.jsonl"
            audio_path = _confined_runtime_path(
                workspace_root,
                runtime_root,
                entry["audio_path"],
                require_file=True,
            )
            event_path = _confined_runtime_path(
                workspace_root,
                runtime_root,
                entry["event_journal_path"],
                require_file=True,
            )
            if audio_path != expected_audio or event_path != expected_event:
                stitching_issues.append("assembly-segment-artifact-binding-invalid")
                reconstruction_blocked = True
                continue
            try:
                audio_raw = read_bytes_nofollow(audio_path)
                event_raw = read_bytes_nofollow(event_path)
                segment_lpcm = _wav_lpcm(audio_raw, track)
            except InputError:
                stitching_issues.append("assembly-segment-artifact-invalid")
                reconstruction_blocked = True
                continue
            if (
                sha256_bytes(audio_raw) != entry["audio_sha256"]
                or sha256_bytes(event_raw) != entry["event_journal_sha256"]
            ):
                stitching_issues.append("assembly-segment-artifact-digest-mismatch")
                reconstruction_blocked = True
                continue
            stable_artifacts.extend(
                (
                    (audio_path, audio_raw, "audio"),
                    (event_path, event_raw, "event"),
                )
            )
            parts.append(
                StitchSegment(
                    Segment(
                        ordinal,
                        snapshot.paragraph_index,
                        entry["text"],
                        snapshot.narration_only_punctuation,
                    ),
                    segment_lpcm,
                    event_path,
                )
            )

    expected_lpcm: bytes | None = None
    if not reconstruction_blocked and len(parts) == len(entries):
        settings = StitchAudioSettings(
            track.effective_config.audio_format.sample_rate_hz,
            track.effective_config.audio_format.sample_size_bits,
            track.effective_config.audio_format.channels,
        )
        try:
            expected_lpcm = stitch_track_lpcm(tuple(parts), settings)
        except InputError:
            stitching_issues.append("assembly-reconstruction-failed")

    track_audio_path = _confined_runtime_path(
        workspace_root,
        runtime_root,
        manifest["track_audio_path"],
        require_file=True,
    )
    track_audio_raw: bytes | None = None
    actual_lpcm: bytes | None = None
    if track_audio_path is None:
        wav_issues.append("assembled-wav-unavailable")
    else:
        try:
            track_audio_raw = read_bytes_nofollow(track_audio_path)
            actual_lpcm = _wav_lpcm(track_audio_raw, track)
        except InputError:
            wav_issues.append("assembled-wav-format-invalid")
        else:
            if len(track_audio_raw) != manifest["track_audio_byte_count"]:
                wav_issues.append("assembled-wav-byte-count-mismatch")
            if sha256_bytes(track_audio_raw) != manifest["track_audio_sha256"]:
                wav_issues.append("assembled-wav-digest-mismatch")
            settings = StitchAudioSettings(
                track.effective_config.audio_format.sample_rate_hz,
                track.effective_config.audio_format.sample_size_bits,
                track.effective_config.audio_format.channels,
            )
            try:
                duration = assembled_lpcm_duration_seconds(actual_lpcm, settings)
            except InputError:
                wav_issues.append("assembled-wav-frame-count-invalid")
            else:
                if duration != manifest["track_duration_seconds"]:
                    wav_issues.append("assembled-wav-duration-mismatch")
            if expected_lpcm is not None and actual_lpcm != expected_lpcm:
                stitching_issues.append("assembled-lpcm-mismatch")

    for path, raw, artifact in stable_artifacts:
        try:
            if read_bytes_nofollow(path) != raw:
                stitching_issues.append(f"assembly-{artifact}-changed-during-validation")
        except InputError:
            stitching_issues.append(f"assembly-{artifact}-changed-during-validation")
    if source_raw is not None:
        try:
            if read_bytes_nofollow(source_path) != source_raw:
                source_issues.append("assembly-source-changed-during-validation")
        except InputError:
            source_issues.append("assembly-source-changed-during-validation")
    if track_audio_path is not None and track_audio_raw is not None:
        try:
            if read_bytes_nofollow(track_audio_path) != track_audio_raw:
                wav_issues.append("assembled-wav-changed-during-validation")
        except InputError:
            wav_issues.append("assembled-wav-changed-during-validation")

    return source_issues, stitching_issues, wav_issues


def _make_check(
    check_id: str,
    category: str,
    issues: Sequence[str],
    artifact_path: str | None,
    artifact_sha256: str | None,
) -> ValidationCheck:
    failed = bool(issues)
    return ValidationCheck(
        check_id=check_id,
        status=ValidationStatus.BLOCKED if failed else ValidationStatus.PASSED,
        artifact_path=artifact_path,
        artifact_sha256=artifact_sha256,
        finding_category=category if failed else None,
        finding_count=len(set(issues)),
    )


def validate_frozen_track_manifest(
    workspace_root: Path,
    plan_path: Path,
    track_id: str,
    transaction_id: str,
    *,
    validated_at_utc: str | None = None,
    clock: Clock | None = None,
    persist: bool = True,
) -> ValidationEvidence:
    """Validate one native-zero attempt and active manifest against its Track plan.

    Failed local evidence is represented by sanitized categories and counts.  No
    source, segment, transcript, event, console, identity, or credential value is
    copied into the returned or persisted ValidationEvidence.
    """

    root = workspace_root.expanduser().resolve()
    timestamp = _validated_at(validated_at_utc, clock)
    absolute_plan, plan, track, transaction_root, store = _load_exact_scope(
        root,
        plan_path,
        track_id,
        transaction_id,
    )
    plan_sha256 = StrictRecordCodec(FrozenBatchPlan).sha256(plan)

    (
        attempt_issues,
        attempt_sha256,
        attempt_artifact_path,
        attempt_artifact_sha256,
    ) = _attempt_issues(root, plan, track, transaction_root, store)

    manifest_path = transaction_root / "runtime" / "manifest.json"
    (
        manifest,
        manifest_raw,
        manifest_sha256,
        manifest_artifact_path,
        manifest_artifact_sha256,
        schema_issues,
    ) = _load_manifest(root, manifest_path)

    binding_issues: list[str] = []
    active_issues: list[str] = []
    token_issues: list[str] = []
    path_issues: list[str] = []
    history_issues: list[str] = []
    hash_issues: list[str] = []
    transcript_issues: list[str] = []
    event_issues: list[str] = []
    lpcm_issues: list[str] = []
    partial_issues: list[str] = []
    assembly_source_issues: list[str] = []
    assembly_stitching_issues: list[str] = []
    assembly_wav_issues: list[str] = []
    if manifest is not None:
        schema_issues.extend(_manifest_schema_issues(manifest))
    if manifest is not None and not schema_issues:
        binding_issues = _frozen_binding_issues(plan, track, manifest)
        active_issues = _active_set_issues(track, manifest)
        token_issues = _token_conservation_issues(track, manifest)
        path_issues = _path_confinement_issues(
            root,
            transaction_root,
            track,
            manifest,
        )
        history_issues = _history_exclusion_issues(manifest)
        (
            hash_issues,
            transcript_issues,
            event_issues,
            lpcm_issues,
            partial_issues,
        ) = _exact_fidelity_issue_sets(
            root,
            transaction_root,
            track,
            manifest,
        )
        (
            assembly_source_issues,
            assembly_stitching_issues,
            assembly_wav_issues,
        ) = _assembly_issue_sets(
            root,
            transaction_root,
            track,
            manifest,
        )
    else:
        prerequisite = ["manifest-schema-prerequisite-invalid"]
        binding_issues = list(prerequisite)
        active_issues = list(prerequisite)
        token_issues = list(prerequisite)
        path_issues = list(prerequisite)
        history_issues = list(prerequisite)
        hash_issues = list(prerequisite)
        transcript_issues = list(prerequisite)
        event_issues = list(prerequisite)
        lpcm_issues = list(prerequisite)
        partial_issues = list(prerequisite)
        assembly_source_issues = list(prerequisite)
        assembly_stitching_issues = list(prerequisite)
        assembly_wav_issues = list(prerequisite)

    if manifest_raw is not None:
        try:
            if read_bytes_nofollow(manifest_path) != manifest_raw:
                schema_issues.append("manifest-changed-during-validation")
        except InputError:
            schema_issues.append("manifest-changed-during-validation")

    private_values: list[str] = []
    if manifest is not None:
        for bucket in ("segments", *_NON_ACTIVE_BUCKETS):
            entries = manifest.get(bucket, [])
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, Mapping):
                    continue
                for name in ("text", "transcript"):
                    value = entry.get(name)
                    if isinstance(value, str) and len(value) >= 4:
                        private_values.append(value)

    from .production_evidence import (
        EvidenceScanReport,
        scan_validation_gate_evidence,
        write_immutable_evidence,
    )

    sanitization_report = scan_validation_gate_evidence(
        root,
        absolute_plan,
        transaction_root,
        scanned_at_utc=timestamp,
        sensitive_values=private_values,
    )
    sanitization_issues = [
        f"{finding.category}-{index}"
        for finding in sanitization_report.findings
        for index in range(finding.count)
    ]
    sanitization_artifact_path: str | None = None
    sanitization_artifact_sha256: str | None = None
    validation_root = transaction_root / "validation"
    if persist:
        durable_mkdir(validation_root)
        sanitization_path = validation_root / (
            f"sanitization-{sanitization_report.canonical_sha256}.json"
        )
        write_immutable_evidence(sanitization_path, sanitization_report)
        sanitization_artifact_path = workspace_relative(root, sanitization_path)
        sanitization_artifact_sha256 = StrictRecordCodec(EvidenceScanReport).sha256(
            sanitization_report
        )

    issue_sets = (
        attempt_issues,
        schema_issues,
        binding_issues,
        active_issues,
        token_issues,
        path_issues,
        history_issues,
        hash_issues,
        transcript_issues,
        event_issues,
        lpcm_issues,
        partial_issues,
        assembly_source_issues,
        assembly_stitching_issues,
        assembly_wav_issues,
        sanitization_issues,
    )
    checks: list[ValidationCheck] = []
    for (check_id, category), issues in zip(_CHECKS, issue_sets, strict=True):
        if check_id.startswith("attempt."):
            path = attempt_artifact_path
            digest = attempt_artifact_sha256
        elif check_id == "evidence.sanitization":
            path = sanitization_artifact_path
            digest = sanitization_artifact_sha256
        else:
            path = manifest_artifact_path
            digest = manifest_artifact_sha256
        checks.append(_make_check(check_id, category, issues, path, digest))

    passed = all(check.status is ValidationStatus.PASSED for check in checks)
    evidence = seal_record(
        ValidationEvidence(
            schema_version=RECORD_SCHEMA_VERSION,
            transaction_id=track.transaction_id,
            track_id=track.track_id,
            validated_at_utc=timestamp,
            plan_sha256=plan_sha256,
            attempt_sha256=attempt_sha256,
            manifest_sha256=manifest_sha256,
            status=ValidationStatus.PASSED if passed else ValidationStatus.BLOCKED,
            checks=tuple(checks),
            delivery_gate_passed=passed,
            canonical_sha256="",
        )
    )
    # The candidate itself is an Evidence_Artifact and must pass its explicit
    # schema/privacy allowlist even when the caller requests a non-persisted check.
    StrictRecordCodec(ValidationEvidence).dump_bytes(evidence)
    # Ensure the exact immutable plan remained stable while local evidence was read
    # before committing a result that claims to bind it.
    if StrictRecordCodec(FrozenBatchPlan).load(absolute_plan) != plan:
        raise InputError("Frozen plan changed during manifest validation")
    if persist:
        write_immutable_evidence(
            validation_evidence_path(transaction_root, evidence),
            evidence,
        )
    return evidence


def load_passing_validation_evidence(
    transaction_root: Path,
    *,
    transaction_id: str,
    track_id: str,
    plan_sha256: str,
    manifest_sha256: str | None = None,
    validation_sha256: str | None = None,
) -> tuple[ValidationEvidence, Path]:
    """Load one immutable passing Delivery_Gate record for an exact Track.

    Content-addressed records are preferred, while the former fixed filename is
    accepted as a read-only compatibility input.  Every validation candidate is
    strictly decoded and scope checked; malformed, misnamed, or cross-scope
    evidence fails closed rather than being skipped.  Blocked historical records
    remain untouched and are never selected as proof of success.
    """

    if not isinstance(transaction_id, str) or not _IDENTIFIER.fullmatch(transaction_id):
        raise InputError("Validation transaction_id is not canonical")
    if not isinstance(track_id, str) or not _IDENTIFIER.fullmatch(track_id):
        raise InputError("Validation track_id is not canonical")
    for value, label in (
        (plan_sha256, "plan"),
        (manifest_sha256, "manifest"),
        (validation_sha256, "validation"),
    ):
        if value is not None and (not isinstance(value, str) or not _SHA256.fullmatch(value)):
            raise InputError(f"Expected {label} SHA-256 is invalid")

    validation_root = transaction_root / "validation"
    if (
        not os.path.lexists(validation_root)
        or validation_root.is_symlink()
        or not validation_root.is_dir()
    ):
        raise InputError("Validation evidence root is missing or unsafe")
    try:
        entries = tuple(sorted(validation_root.iterdir(), key=lambda item: item.name))
    except OSError as exc:
        raise InputError("Validation evidence root cannot be read safely") from exc

    candidates: list[tuple[Path, re.Match[str] | None]] = []
    for entry in entries:
        match = _CONTENT_ADDRESSED_VALIDATION.fullmatch(entry.name)
        if entry.name == "frozen-manifest.json":
            candidates.append((entry, None))
        elif match is not None:
            candidates.append((entry, match))
        elif entry.name.startswith("frozen-manifest-"):
            raise InputError("Validation evidence filename is not content-addressed")

    codec = StrictRecordCodec(ValidationEvidence)
    passing: list[tuple[ValidationEvidence, Path, str, bool]] = []
    for path, filename_match in candidates:
        if path.is_symlink() or not path.is_file():
            raise InputError("Validation evidence path is not a regular no-follow file")
        evidence = codec.load(path)
        content_sha256 = codec.sha256(evidence)
        if (
            filename_match is not None
            and filename_match.group(1) != evidence.canonical_sha256
        ):
            raise InputError("Validation evidence filename does not match canonical content")
        if (
            evidence.transaction_id != transaction_id
            or evidence.track_id != track_id
            or evidence.plan_sha256 != plan_sha256
        ):
            raise InputError("Validation evidence is not bound to the exact Track scope")
        if validation_sha256 is not None and content_sha256 != validation_sha256:
            continue
        if manifest_sha256 is not None and evidence.manifest_sha256 != manifest_sha256:
            continue
        if (
            evidence.status is ValidationStatus.PASSED
            and evidence.delivery_gate_passed
            and all(check.status is ValidationStatus.PASSED for check in evidence.checks)
        ):
            passing.append((evidence, path, content_sha256, filename_match is not None))

    if not passing:
        raise InputError("Delivery_Gate has not passed for this Track")
    content_addressed = tuple(item for item in passing if item[3])
    eligible = content_addressed or tuple(passing)
    selected = min(
        eligible,
        key=lambda item: (item[0].validated_at_utc, item[2], item[1].name),
    )
    return selected[0], selected[1]


def validation_evidence_path(
    transaction_root: Path,
    evidence: ValidationEvidence,
) -> Path:
    """Return the content-addressed immutable path for one validation result."""

    if not isinstance(evidence, ValidationEvidence):
        raise InputError("Validation evidence path requires ValidationEvidence")
    StrictRecordCodec(ValidationEvidence).dump_bytes(evidence)
    return transaction_root / "validation" / (
        f"frozen-manifest-{evidence.canonical_sha256}.json"
    )


__all__ = [
    "load_passing_validation_evidence",
    "validate_frozen_track_manifest",
    "validation_evidence_path",
]
