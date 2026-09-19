"""Offline local preflight, reuse inspection, and read-only legacy observation.

This module intentionally has no AWS, pricing, identity, rendering, or network
imports.  It binds current local bytes to a frozen production plan, inventories
protected files individually, validates reusable segment artifacts using the
existing transcript/event algorithms, and computes exact cache-miss call bounds.
"""

from __future__ import annotations

import io
import os
import shutil
import stat
import subprocess
import wave
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path, PurePosixPath
from typing import Any

from .errors import InputError
from .narrate import Segment, segment_spoken_text
from .nova import _mid_sentence_partial_turn_count, replay_output_events
from .production import (
    ApprovedSpecialTrackSourceAdapter,
    ChapterSourceAdapter,
    TrackSourceAdapter,
    _build_source_snapshot,
    snapshot_track_source,
)
from .production_config import BookProductionConfig, CatalogTrack, OrderedTrackCatalog
from .production_models import (
    DestinationState,
    FrozenBatchPlan,
    FrozenTrackPlan,
    SegmentSnapshot,
    SourceKind,
    StrictRecordCodec,
    canonical_sha256,
)
from .util import (
    json_loads_strict,
    read_bytes_nofollow,
    read_json,
    resolve_inside,
    sha256_bytes,
    workspace_relative,
)
from .verify import compare_transcript, normalized_tokens

_HISTORICAL_SPEC_ROOTS = (
    ".kiro/specs/chapter-2-audio-proof",
    ".kiro/specs/chapter-3-audio-proof",
)
_GOVERNING_SPEC_ROOT = ".kiro/specs/The-Final-Frontier-novel"
_RUNTIME_ROOT = "audiobook-studio/src/frontier_audiobook"
_DEPENDENCY_PATHS = (
    "audiobook-studio/pyproject.toml",
    "audiobook-studio/uv.lock",
    "audiobook-studio/requirements/dev.txt",
    "audiobook-studio/requirements/runtime.txt",
)
_SHA256_LENGTH = 64


class InventoryKind(StrEnum):
    SELECTED_SOURCE = "selected-source"
    SELECTED_PUBLISHING_HANDOFF = "selected-publishing-handoff"
    PRODUCTION_CONFIG = "production-config"
    RUNTIME = "runtime"
    DEPENDENCY = "dependency"
    PRIOR_AUDIO = "prior-audio"
    LEGACY_MANIFEST = "legacy-manifest"
    LEGACY_TRANSCRIPT = "legacy-transcript"
    LEGACY_EVENT_JOURNAL = "legacy-event-journal"
    LEGACY_EVIDENCE = "legacy-evidence"
    HISTORICAL_SPEC = "historical-spec"
    GOVERNING_SPEC = "governing-spec"
    UNSELECTED_MANUSCRIPT = "unselected-manuscript"


class FileAttribution(StrEnum):
    BASELINE = "baseline"
    PREEXISTING = "pre-existing"
    WORKFLOW_OWNED = "workflow-owned"
    CONCURRENT_OR_UNATTRIBUTED = "concurrent-or-unattributed"
    UNEXPECTED_WORKFLOW_WRITE = "unexpected-workflow-write"


class PriorArtifactState(StrEnum):
    ABSENT = "absent"
    REUSABLE = "reusable"
    REJECTED = "rejected"
    CHARGE_UNCERTAIN = "charge-uncertain"


class ReuseDisposition(StrEnum):
    CURRENT_REUSABLE = "current-reusable"
    STALE_RERENDER_REQUIRED = "stale-rerender-required"
    REASSEMBLY_REQUIRED = "reassembly-required"


@dataclass(frozen=True, slots=True)
class FileObservation:
    path: str
    kind: InventoryKind
    exists: bool
    byte_count: int | None
    sha256: str | None
    git_status: str
    attribution: FileAttribution


@dataclass(frozen=True, slots=True)
class ProtectedInventory:
    files: tuple[FileObservation, ...]
    unselected_manuscript_files: tuple[FileObservation, ...]
    inventory_sha256: str


@dataclass(frozen=True, slots=True)
class WorkflowWriteAllowlist:
    recursive_roots: tuple[str, ...]
    exact_paths: tuple[str, ...]
    canonical_sha256: str

    def contains(self, path: str) -> bool:
        checked = _relative_path(path, "workflow write path")
        candidate = PurePosixPath(checked)
        if checked in self.exact_paths:
            return True
        return any(
            candidate == PurePosixPath(root) or PurePosixPath(root) in candidate.parents
            for root in self.recursive_roots
        )


@dataclass(frozen=True, slots=True)
class TargetedCheckBinding:
    result_path: str
    result_byte_count: int
    result_sha256: str
    command_sha256: str
    return_code: int
    aws_access_disabled: bool
    model_access_disabled: bool
    passed: bool
    binding_sha256: str


@dataclass(frozen=True, slots=True)
class FilesystemCheck:
    required_free_bytes: int
    minimum_available_bytes: int
    disk_space_sufficient: bool
    same_filesystem_atomic_scopes: bool
    checked_devices: tuple[tuple[str, int], ...]
    blocking_categories: tuple[str, ...]
    canonical_sha256: str


@dataclass(frozen=True, slots=True)
class LegacyArtifactObservation:
    chapter: int
    path: str
    kind: InventoryKind
    byte_count: int
    sha256: str


@dataclass(frozen=True, slots=True)
class ValidatedArtifactBinding:
    path: str
    byte_count: int
    sha256: str


@dataclass(frozen=True, slots=True)
class SegmentReuseAssessment:
    segment_id: str
    render_identity_sha256: str
    disposition: ReuseDisposition
    candidate_audio: ValidatedArtifactBinding | None
    transcript_sha256: str | None
    event_journal_sha256: str | None
    finding_categories: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class TrackReuseAssessment:
    track_id: str
    prior_state: PriorArtifactState
    disposition: ReuseDisposition
    segments: tuple[SegmentReuseAssessment, ...]
    reusable_segment_ids: tuple[str, ...]
    rerender_segment_ids: tuple[str, ...]
    maximum_new_calls: int
    planned_call_ceiling: int
    comparison_call_ceiling: int
    invalidation_fan_out_blocked: bool
    source_revision_changed: bool
    assembled_audio: ValidatedArtifactBinding | None
    blocking_categories: tuple[str, ...]
    canonical_sha256: str


@dataclass(frozen=True, slots=True)
class DestinationAssessment:
    track_id: str
    path: str
    state: DestinationState
    destination_byte_count: int | None
    destination_sha256: str | None
    expected_sha256: str | None
    canonical_sha256: str


@dataclass(frozen=True, slots=True)
class IsolationAssessment:
    hard_protected_drift_paths: tuple[str, ...]
    concurrent_manuscript_change_paths: tuple[str, ...]
    workflow_writes_outside_allowlist: tuple[str, ...]
    passed: bool
    canonical_sha256: str


@dataclass(frozen=True, slots=True)
class LocalPreflightResult:
    plan_sha256: str
    config_sha256: str
    targeted_checks: TargetedCheckBinding
    inventory: ProtectedInventory
    write_allowlist: WorkflowWriteAllowlist
    filesystem: FilesystemCheck
    track_reuse: tuple[TrackReuseAssessment, ...]
    destinations: tuple[DestinationAssessment, ...]
    maximum_new_calls_by_track: tuple[tuple[str, int], ...]
    maximum_new_calls_total: int
    blocking_categories: tuple[str, ...]
    passed: bool
    canonical_sha256: str


@dataclass(frozen=True, slots=True)
class _ValidatedCandidate:
    audio: ValidatedArtifactBinding
    transcript_sha256: str
    event_journal_sha256: str


def _relative_path(value: str, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\\" in value:
        raise InputError(f"{label} must be a nonblank workspace-relative POSIX path")
    candidate = PurePosixPath(value)
    if candidate.is_absolute() or value == "." or any(part in {"", ".", ".."} for part in candidate.parts):
        raise InputError(f"{label} must be traversal-free and workspace-relative")
    if candidate.as_posix() != value:
        raise InputError(f"{label} must be canonical")
    return value


def _sha256(value: str, label: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) != _SHA256_LENGTH
        or any(character not in "0123456789abcdef" for character in value)
    ):
        raise InputError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _seal(value: Any, field_name: str = "canonical_sha256"):
    sealed = replace(
        value,
        **{field_name: canonical_sha256(value, omit_fields=(field_name,))},
    )
    from .production_evidence import assert_typed_evidence_safe

    assert_typed_evidence_safe(sealed)
    return sealed


def _nearest_existing_ancestor(path: Path) -> Path:
    current = path
    while not os.path.lexists(current):
        if current == current.parent:
            raise InputError(f"No existing ancestor for local path {path}")
        current = current.parent
    if current.is_symlink():
        raise InputError(f"Local path traverses a symlink: {path}")
    if current.is_file():
        current = current.parent
    if not current.is_dir() or current.is_symlink():
        raise InputError(f"Local path has no safe directory ancestor: {path}")
    return current


def _walk_regular_files(workspace_root: Path, relative_root: str) -> tuple[str, ...]:
    """List files under one root without following symlinks or special files."""

    checked = _relative_path(relative_root, "inventory root")
    absolute = resolve_inside(workspace_root, checked)
    if not os.path.lexists(absolute):
        return (checked,)
    if absolute.is_symlink():
        raise InputError(f"Inventory root must not be a symlink: {checked}")
    if absolute.is_file():
        return (checked,)
    if not absolute.is_dir():
        raise InputError(f"Inventory root has an unsupported file type: {checked}")

    found: list[str] = []
    pending = [absolute]
    while pending:
        directory = pending.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda item: item.name)
        except OSError as exc:
            raise InputError(f"Cannot enumerate protected directory {directory}: {exc}") from exc
        for entry in entries:
            path = Path(entry.path)
            relative = workspace_relative(workspace_root, path)
            if entry.is_symlink():
                raise InputError(f"Protected inventory must not follow symlink {relative}")
            if entry.is_dir(follow_symlinks=False):
                if entry.name in {"__pycache__", ".pytest_cache", ".venv"}:
                    continue
                pending.append(path)
            elif entry.is_file(follow_symlinks=False):
                if path.suffix == ".pyc":
                    continue
                found.append(relative)
            else:
                raise InputError(f"Protected inventory contains special file {relative}")
    return tuple(sorted(found))


def _normalize_git_status(code: str) -> str:
    if code == "??":
        return "untracked"
    if code == "!!":
        return "ignored"
    labels = {
        "M": "modified",
        "A": "added",
        "D": "deleted",
        "R": "renamed",
        "C": "copied",
        "U": "unmerged",
        "T": "type-changed",
    }
    values = tuple(dict.fromkeys(labels[item] for item in code if item in labels))
    return "+".join(values) if values else "changed"


def _read_git_statuses(workspace_root: Path) -> Mapping[str, str]:
    environment = {
        "PATH": os.environ.get("PATH", ""),
        "HOME": os.environ.get("HOME", ""),
        "LC_ALL": "C",
        "GIT_OPTIONAL_LOCKS": "0",
    }
    try:
        completed = subprocess.run(
            ["git", "status", "--porcelain=v1", "-z", "--untracked-files=all"],
            cwd=workspace_root,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return {}
    if completed.returncode != 0:
        return {}

    raw_items = completed.stdout.split(b"\0")
    result: dict[str, str] = {}
    index = 0
    while index < len(raw_items):
        item = raw_items[index]
        index += 1
        if not item:
            continue
        try:
            decoded = item.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InputError("Git status returned a non-UTF-8 path") from exc
        if len(decoded) < 4 or decoded[2] != " ":
            raise InputError("Git status returned malformed porcelain output")
        code, path = decoded[:2], decoded[3:]
        result[path] = _normalize_git_status(code)
        if code[0] in {"R", "C"} and index < len(raw_items) and raw_items[index]:
            try:
                original = raw_items[index].decode("utf-8")
            except UnicodeDecodeError as exc:
                raise InputError("Git status returned a non-UTF-8 rename path") from exc
            index += 1
            result[original] = _normalize_git_status(code)
    return result


def _observe_file(
    workspace_root: Path,
    path: str,
    kind: InventoryKind,
    git_statuses: Mapping[str, str],
    *,
    attribution: FileAttribution | None = None,
) -> FileObservation:
    checked = _relative_path(path, "inventory path")
    absolute = resolve_inside(workspace_root, checked)
    status_value = git_statuses.get(checked, "clean" if (workspace_root / ".git").exists() else "not-repository")
    chosen_attribution = attribution or (
        FileAttribution.BASELINE
        if status_value in {"clean", "not-repository"}
        else FileAttribution.PREEXISTING
    )
    if not os.path.lexists(absolute):
        return FileObservation(checked, kind, False, None, None, status_value, chosen_attribution)
    if absolute.is_symlink():
        raise InputError(f"Inventory path must not be a symlink: {checked}")
    before = absolute.stat(follow_symlinks=False)
    if not stat.S_ISREG(before.st_mode):
        raise InputError(f"Inventory path is not a regular file: {checked}")
    content = read_bytes_nofollow(absolute)
    after = absolute.stat(follow_symlinks=False)
    before_identity = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns)
    after_identity = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns)
    if before_identity != after_identity or len(content) != after.st_size:
        raise InputError(f"Inventory path changed while it was being observed: {checked}")
    return FileObservation(
        checked,
        kind,
        True,
        len(content),
        sha256_bytes(content),
        status_value,
        chosen_attribution,
    )


def derive_workflow_write_allowlist(
    config: BookProductionConfig,
    plan: FrozenBatchPlan,
) -> WorkflowWriteAllowlist:
    """Derive exact generated roots and delivery files for one frozen scope."""

    base = PurePosixPath(config.build_root) / config.book_id
    roots = {
        (base / "plans" / plan.plan_id).as_posix(),
        (base / "batches" / plan.plan_id).as_posix(),
    }
    for track in plan.tracks:
        roots.add(
            (base / "transactions" / track.track_id / track.transaction_id).as_posix()
        )
    exact = {(base / "indexes" / "status.json").as_posix()}
    exact.update(track.effective_config.output_path for track in plan.tracks)
    value = WorkflowWriteAllowlist(
        recursive_roots=tuple(sorted(roots)),
        exact_paths=tuple(sorted(exact)),
        canonical_sha256="",
    )
    return _seal(value)


class ReadOnlyLegacyAdapter:
    """Observe Chapter 1/2 conventions without moving, rewriting, or deleting bytes."""

    def __init__(self, workspace_root: Path):
        self.workspace_root = workspace_root.expanduser().resolve()

    def _build_roots(self, chapter: int) -> tuple[str, ...]:
        narration = resolve_inside(self.workspace_root, "audiobook-studio/build/narration")
        if not narration.is_dir() or narration.is_symlink():
            return ()
        prefix = f"chapter-{chapter:03d}-"
        roots: list[str] = []
        for entry in sorted(os.scandir(narration), key=lambda item: item.name):
            if not entry.name.startswith(prefix):
                continue
            if entry.is_symlink():
                raise InputError(f"Legacy build root must not be a symlink: {entry.path}")
            if entry.is_dir(follow_symlinks=False):
                roots.append(workspace_relative(self.workspace_root, Path(entry.path)))
        return tuple(roots)

    def manifest_paths(self, chapter: int) -> tuple[Path, ...]:
        if chapter not in {1, 2}:
            raise InputError("Legacy adapter supports only Chapter 1 and Chapter 2")
        result: list[Path] = []
        for root in self._build_roots(chapter):
            candidate = resolve_inside(self.workspace_root, (PurePosixPath(root) / "manifest.json").as_posix())
            if candidate.is_file() and not candidate.is_symlink():
                result.append(candidate)
        return tuple(result)

    def has_uncertain_evidence(self, chapter: int) -> bool:
        uncertain_names = {
            "charge-uncertain",
            "charge-uncertain.json",
            "ambiguity",
            "ambiguity.json",
        }
        for root in self._build_roots(chapter):
            absolute = resolve_inside(self.workspace_root, root)
            pending = [absolute]
            while pending:
                directory = pending.pop()
                for entry in os.scandir(directory):
                    if entry.is_symlink():
                        raise InputError(f"Legacy evidence must not traverse a symlink: {entry.path}")
                    lowered = entry.name.casefold()
                    if "staging" in lowered or lowered in uncertain_names:
                        return True
                    if entry.is_dir(follow_symlinks=False):
                        pending.append(Path(entry.path))
        return False

    def observe(self, chapters: Iterable[int] = (1, 2)) -> tuple[LegacyArtifactObservation, ...]:
        observations: list[LegacyArtifactObservation] = []
        for chapter in chapters:
            if chapter not in {1, 2}:
                raise InputError("Legacy adapter supports only Chapter 1 and Chapter 2")
            paths: set[str] = set()
            for root in self._build_roots(chapter):
                paths.update(_walk_regular_files(self.workspace_root, root))
            proof_root = resolve_inside(self.workspace_root, "voice-samples")
            if proof_root.is_dir() and not proof_root.is_symlink():
                prefix = f"chapter-{chapter}-"
                for entry in os.scandir(proof_root):
                    if entry.is_symlink() and entry.name.startswith(prefix):
                        raise InputError(f"Legacy proof path must not be a symlink: {entry.path}")
                    if (
                        entry.name.startswith(prefix)
                        and entry.is_file(follow_symlinks=False)
                        and entry.name.casefold().endswith(".wav")
                    ):
                        paths.add(workspace_relative(self.workspace_root, Path(entry.path)))
            for path in sorted(paths):
                absolute = resolve_inside(self.workspace_root, path)
                content = read_bytes_nofollow(absolute)
                observations.append(
                    LegacyArtifactObservation(
                        chapter=chapter,
                        path=path,
                        kind=_legacy_inventory_kind(path),
                        byte_count=len(content),
                        sha256=sha256_bytes(content),
                    )
                )
        return tuple(observations)

    def inspect_track(
        self,
        track_plan: FrozenTrackPlan,
        config: BookProductionConfig,
        catalog_track: CatalogTrack,
        *,
        comparison_call_ceiling: int | None = None,
    ) -> TrackReuseAssessment:
        chapter = _chapter_number(track_plan.track_id)
        if chapter not in {1, 2}:
            raise InputError("Legacy reuse inspection supports only Chapter 1 and Chapter 2")
        return classify_track_reuse(
            self.workspace_root,
            track_plan,
            config,
            catalog_track,
            self.manifest_paths(chapter),
            comparison_call_ceiling=comparison_call_ceiling,
            charge_uncertain=self.has_uncertain_evidence(chapter),
        )


def _legacy_inventory_kind(path: str) -> InventoryKind:
    candidate = PurePosixPath(path)
    name = candidate.name.casefold()
    parts = {part.casefold() for part in candidate.parts}
    if name == "manifest.json":
        return InventoryKind.LEGACY_MANIFEST
    if "transcripts" in parts or candidate.suffix.casefold() == ".txt":
        return InventoryKind.LEGACY_TRANSCRIPT
    if "events" in parts or candidate.suffix.casefold() == ".jsonl":
        return InventoryKind.LEGACY_EVENT_JOURNAL
    if candidate.suffix.casefold() == ".wav":
        return InventoryKind.PRIOR_AUDIO
    return InventoryKind.LEGACY_EVIDENCE


def _chapter_number(track_id: str) -> int:
    prefix = "chapter-"
    if not track_id.startswith(prefix) or not track_id[len(prefix) :].isdigit():
        raise InputError(f"Track is not a canonical Chapter Track: {track_id!r}")
    return int(track_id[len(prefix) :])


def build_protected_inventory(
    workspace_root: Path,
    config: BookProductionConfig,
    plan: FrozenBatchPlan,
    *,
    prior_artifact_paths: Iterable[str] = (),
    extra_runtime_paths: Iterable[str] = (),
    git_statuses: Mapping[str, str] | None = None,
) -> ProtectedInventory:
    """Hash every protected file independently and inventory unselected prose separately."""

    root = workspace_root.expanduser().resolve()
    statuses = dict(git_statuses) if git_statuses is not None else dict(_read_git_statuses(root))
    categories: dict[str, InventoryKind] = {}

    def add(path: str, kind: InventoryKind) -> None:
        checked = _relative_path(path, "protected inventory path")
        existing = categories.get(checked)
        priority = {
            InventoryKind.SELECTED_PUBLISHING_HANDOFF: 100,
            InventoryKind.SELECTED_SOURCE: 90,
            InventoryKind.PRODUCTION_CONFIG: 80,
            InventoryKind.PRIOR_AUDIO: 70,
            InventoryKind.LEGACY_MANIFEST: 65,
            InventoryKind.LEGACY_TRANSCRIPT: 64,
            InventoryKind.LEGACY_EVENT_JOURNAL: 63,
            InventoryKind.LEGACY_EVIDENCE: 62,
            InventoryKind.RUNTIME: 50,
            InventoryKind.DEPENDENCY: 40,
            InventoryKind.HISTORICAL_SPEC: 30,
            InventoryKind.GOVERNING_SPEC: 20,
        }
        if existing is None or priority.get(kind, 0) > priority.get(existing, 0):
            categories[checked] = kind

    add(plan.config_path, InventoryKind.PRODUCTION_CONFIG)
    selected_paths: set[str] = set()
    for track in plan.tracks:
        selected_paths.add(track.source.source_path)
        kind = (
            InventoryKind.SELECTED_PUBLISHING_HANDOFF
            if track.source.source_kind is SourceKind.APPROVED_SPECIAL_TRACK
            else InventoryKind.SELECTED_SOURCE
        )
        add(track.source.source_path, kind)

    for path in _walk_regular_files(root, _RUNTIME_ROOT):
        add(path, InventoryKind.RUNTIME)
    for path in extra_runtime_paths:
        for expanded in _walk_regular_files(root, path):
            add(expanded, InventoryKind.RUNTIME)
    for path in _DEPENDENCY_PATHS:
        add(path, InventoryKind.DEPENDENCY)
    for spec_root in _HISTORICAL_SPEC_ROOTS:
        for path in _walk_regular_files(root, spec_root):
            add(path, InventoryKind.HISTORICAL_SPEC)
    for path in _walk_regular_files(root, _GOVERNING_SPEC_ROOT):
        add(path, InventoryKind.GOVERNING_SPEC)

    legacy = ReadOnlyLegacyAdapter(root)
    for observation in legacy.observe():
        add(observation.path, observation.kind)
    for path in prior_artifact_paths:
        for expanded in _walk_regular_files(root, path):
            add(expanded, _legacy_inventory_kind(expanded))

    files = tuple(
        _observe_file(root, path, categories[path], statuses)
        for path in sorted(categories)
    )

    manuscript_files = _walk_regular_files(root, config.manuscript_root)
    unselected = tuple(
        _observe_file(
            root,
            path,
            InventoryKind.UNSELECTED_MANUSCRIPT,
            statuses,
            attribution=(
                FileAttribution.CONCURRENT_OR_UNATTRIBUTED
                if statuses.get(path, "clean") not in {"clean", "not-repository"}
                else FileAttribution.BASELINE
            ),
        )
        for path in manuscript_files
        if path not in selected_paths
    )
    unsealed = ProtectedInventory(files, unselected, "")
    return replace(
        unsealed,
        inventory_sha256=canonical_sha256(unsealed, omit_fields=("inventory_sha256",)),
    )


def bind_targeted_check_result(
    workspace_root: Path,
    result_path: str,
    *,
    command_sha256: str,
    return_code: int,
    aws_access_disabled: bool,
    model_access_disabled: bool,
) -> TargetedCheckBinding:
    """Bind an already-produced local test result; this function never runs tests."""

    checked = _relative_path(result_path, "targeted-check result path")
    _sha256(command_sha256, "targeted-check command_sha256")
    if type(return_code) is not int:
        raise InputError("targeted-check return_code must be an integer")
    if type(aws_access_disabled) is not bool or type(model_access_disabled) is not bool:
        raise InputError("targeted-check access controls must be booleans")
    absolute = resolve_inside(workspace_root.expanduser().resolve(), checked)
    content = read_bytes_nofollow(absolute)
    unsealed = TargetedCheckBinding(
        result_path=checked,
        result_byte_count=len(content),
        result_sha256=sha256_bytes(content),
        command_sha256=command_sha256,
        return_code=return_code,
        aws_access_disabled=aws_access_disabled,
        model_access_disabled=model_access_disabled,
        passed=(return_code == 0 and aws_access_disabled and model_access_disabled),
        binding_sha256="",
    )
    return _seal(unsealed, "binding_sha256")


def inspect_local_filesystems(
    workspace_root: Path,
    allowlist: WorkflowWriteAllowlist,
    *,
    required_free_bytes: int,
    atomic_pairs: Iterable[tuple[str, str]] = (),
) -> FilesystemCheck:
    """Check free space and device equality for every requested atomic rename pair."""

    if type(required_free_bytes) is not int or required_free_bytes < 0:
        raise InputError("required_free_bytes must be a nonnegative integer")
    root = workspace_root.expanduser().resolve()
    scope_paths = set(allowlist.recursive_roots)
    scope_paths.update(PurePosixPath(path).parent.as_posix() for path in allowlist.exact_paths)
    device_rows: dict[str, int] = {}
    available_by_device: dict[int, int] = {}
    for relative in sorted(scope_paths):
        absolute = resolve_inside(root, relative)
        ancestor = _nearest_existing_ancestor(absolute)
        device = ancestor.stat(follow_symlinks=False).st_dev
        device_rows[relative] = device
        available_by_device[device] = min(
            available_by_device.get(device, shutil.disk_usage(ancestor).free),
            shutil.disk_usage(ancestor).free,
        )

    same_filesystem = True
    for first, second in atomic_pairs:
        first_path = resolve_inside(root, _relative_path(first, "atomic source path"))
        second_path = resolve_inside(root, _relative_path(second, "atomic destination path"))
        first_device = _nearest_existing_ancestor(first_path).stat(follow_symlinks=False).st_dev
        second_device = _nearest_existing_ancestor(second_path).stat(follow_symlinks=False).st_dev
        if first_device != second_device:
            same_filesystem = False

    minimum_available = min(available_by_device.values(), default=shutil.disk_usage(root).free)
    sufficient = minimum_available >= required_free_bytes
    blockers: list[str] = []
    if not sufficient:
        blockers.append("insufficient-local-disk")
    if not same_filesystem:
        blockers.append("cross-filesystem-atomic-scope")
    unsealed = FilesystemCheck(
        required_free_bytes=required_free_bytes,
        minimum_available_bytes=minimum_available,
        disk_space_sufficient=sufficient,
        same_filesystem_atomic_scopes=same_filesystem,
        checked_devices=tuple(sorted(device_rows.items())),
        blocking_categories=tuple(blockers),
        canonical_sha256="",
    )
    return _seal(unsealed)


def _current_segments(
    workspace_root: Path,
    config: BookProductionConfig,
    catalog_track: CatalogTrack,
    track_plan: FrozenTrackPlan,
) -> tuple[tuple[SegmentSnapshot, Segment], ...]:
    current_snapshot = snapshot_track_source(config, catalog_track, workspace_root)
    if current_snapshot != track_plan.source:
        raise InputError(f"Selected source drifted from frozen plan for {track_plan.track_id!r}")
    adapter: TrackSourceAdapter = (
        ChapterSourceAdapter()
        if catalog_track.kind.value == "chapter"
        else ApprovedSpecialTrackSourceAdapter()
    )
    prepared = adapter.read(config, catalog_track, workspace_root)
    second_snapshot = _build_source_snapshot(catalog_track, prepared)
    if second_snapshot != current_snapshot:
        raise InputError(f"Selected source changed during local preflight for {track_plan.track_id!r}")
    segments = segment_spoken_text(
        prepared.spoken,
        max_words=track_plan.effective_config.target_segment_words,
    )
    if len(segments) != len(current_snapshot.segments):
        raise InputError(f"Current segment count changed during local preflight for {track_plan.track_id!r}")
    pairs = tuple(zip(current_snapshot.segments, segments, strict=True))
    for snapshot, segment in pairs:
        if snapshot.text_sha256 != sha256_bytes(" ".join(segment.text.split()).encode("utf-8")):
            raise InputError(f"Current segment text binding changed for {track_plan.track_id!r}")
    return pairs


def _candidate_path(
    workspace_root: Path,
    manifest_root: Path,
    value: object,
    label: str,
) -> Path:
    if not isinstance(value, str):
        raise InputError(f"{label} must be a workspace-relative path")
    absolute = resolve_inside(workspace_root, _relative_path(value, label))
    try:
        absolute.relative_to(manifest_root)
    except ValueError as exc:
        raise InputError(f"{label} must remain inside its legacy/runtime root") from exc
    return absolute


def _load_event_journal(path: Path) -> tuple[dict[str, Any], ...]:
    raw = read_bytes_nofollow(path)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError(f"Event journal is not strict UTF-8: {path}") from exc
    events: list[dict[str, Any]] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line:
            continue
        value = json_loads_strict(line, f"{path}:{line_number}")
        if not isinstance(value, dict):
            raise InputError(f"Event journal line is not an object: {path}:{line_number}")
        events.append(value)
    if not events:
        raise InputError(f"Event journal is empty: {path}")
    return tuple(events)


def _wav_lpcm(content: bytes, track_plan: FrozenTrackPlan) -> bytes:
    expected = track_plan.effective_config.audio_format
    try:
        with wave.open(io.BytesIO(content), "rb") as handle:
            actual = (
                handle.getframerate(),
                handle.getsampwidth() * 8,
                handle.getnchannels(),
                handle.getcomptype(),
            )
            required = (
                expected.sample_rate_hz,
                expected.sample_size_bits,
                expected.channels,
                "NONE",
            )
            if actual != required:
                raise InputError("Reusable segment WAV format does not match EffectiveTrackConfig")
            return handle.readframes(handle.getnframes())
    except (EOFError, wave.Error) as exc:
        raise InputError("Reusable segment WAV is malformed") from exc


def _validate_candidate(
    workspace_root: Path,
    manifest_path: Path,
    manifest: Mapping[str, Any],
    entry: Mapping[str, Any],
    track_plan: FrozenTrackPlan,
    snapshot: SegmentSnapshot,
    segment: Segment,
) -> _ValidatedCandidate:
    if entry.get("status") not in {"narrated", "reused", "accepted"}:
        raise InputError("candidate-status")
    if entry.get("text_sha256") != snapshot.text_sha256:
        raise InputError("candidate-text-binding")
    render_identity = entry.get("render_identity_sha256")
    if render_identity != snapshot.render_identity_sha256:
        raise InputError("candidate-render-identity")
    render_config = entry.get("render_config_sha256", manifest.get("render_config_sha256"))
    if render_config != snapshot.render_config_sha256:
        raise InputError("candidate-config-binding")
    if entry.get("exact_transcript_match") is not True or entry.get("coverage_ratio") != 1.0:
        raise InputError("candidate-fidelity-record")
    if type(entry.get("mid_sentence_partial_turns", 0)) is not int or entry.get(
        "mid_sentence_partial_turns", 0
    ) != 0:
        raise InputError("candidate-partial-turn-record")

    manifest_root = manifest_path.parent
    audio_path = _candidate_path(
        workspace_root,
        manifest_root,
        entry.get("audio_path"),
        "candidate audio_path",
    )
    audio = read_bytes_nofollow(audio_path)
    audio_sha256 = sha256_bytes(audio)
    if entry.get("audio_sha256") != audio_sha256:
        raise InputError("candidate-audio-hash")
    lpcm = _wav_lpcm(audio, track_plan)

    transcript_value = entry.get("transcript_path")
    transcript_path = (
        _candidate_path(
            workspace_root,
            manifest_root,
            transcript_value,
            "candidate transcript_path",
        )
        if transcript_value is not None
        else manifest_root / "transcripts" / f"{audio_path.stem}.txt"
    )
    transcript_bytes = read_bytes_nofollow(transcript_path)
    transcript_sha256 = sha256_bytes(transcript_bytes)
    recorded_transcript_sha = entry.get("transcript_sha256")
    if recorded_transcript_sha is not None and recorded_transcript_sha != transcript_sha256:
        raise InputError("candidate-transcript-hash")
    try:
        transcript = transcript_bytes.decode("utf-8").removesuffix("\n")
    except UnicodeDecodeError as exc:
        raise InputError("candidate-transcript-encoding") from exc
    verification = compare_transcript(
        segment.text,
        transcript,
        track_plan.effective_config.normalization,
    )
    if not verification.passed or verification.coverage_ratio != 1.0:
        raise InputError("candidate-transcript-fidelity")

    event_value = entry.get("event_journal_path")
    event_path = (
        _candidate_path(
            workspace_root,
            manifest_root,
            event_value,
            "candidate event_journal_path",
        )
        if event_value is not None
        else manifest_root / "events" / f"{audio_path.stem}.jsonl"
    )
    event_bytes = read_bytes_nofollow(event_path)
    event_sha256 = sha256_bytes(event_bytes)
    recorded_event_sha = entry.get("event_journal_sha256")
    if recorded_event_sha is not None and recorded_event_sha != event_sha256:
        raise InputError("candidate-event-hash")
    events = _load_event_journal(event_path)
    replayed = replay_output_events(events)
    if replayed.audio_lpcm != lpcm:
        raise InputError("candidate-event-lpcm")
    replay_verification = compare_transcript(
        segment.text,
        replayed.final_transcript,
        track_plan.effective_config.normalization,
    )
    if not replay_verification.passed:
        raise InputError("candidate-event-transcript")
    if normalized_tokens(transcript, track_plan.effective_config.normalization) != normalized_tokens(
        replayed.final_transcript,
        track_plan.effective_config.normalization,
    ):
        raise InputError("candidate-transcript-event-binding")
    if _mid_sentence_partial_turn_count(events):
        raise InputError("candidate-event-partial-turn")

    return _ValidatedCandidate(
        audio=ValidatedArtifactBinding(
            path=workspace_relative(workspace_root, audio_path),
            byte_count=len(audio),
            sha256=audio_sha256,
        ),
        transcript_sha256=transcript_sha256,
        event_journal_sha256=event_sha256,
    )


def _load_manifests(
    workspace_root: Path,
    manifest_paths: Sequence[Path],
) -> tuple[tuple[Path, Mapping[str, Any]], ...]:
    loaded: list[tuple[Path, Mapping[str, Any]]] = []
    seen: set[str] = set()
    for supplied in manifest_paths:
        absolute = (
            supplied.expanduser().resolve()
            if supplied.is_absolute()
            else resolve_inside(workspace_root, supplied.as_posix())
        )
        relative = workspace_relative(workspace_root, absolute)
        if relative in seen:
            raise InputError(f"Duplicate reuse manifest path: {relative}")
        seen.add(relative)
        value = read_json(absolute)
        if not isinstance(value, dict):
            raise InputError(f"Reuse manifest must be an object: {relative}")
        loaded.append((absolute, value))
    return tuple(loaded)


def _manifest_entries(manifest: Mapping[str, Any]) -> tuple[Mapping[str, Any], ...]:
    result: list[Mapping[str, Any]] = []
    for field in ("segments", "carried_over_segments"):
        value = manifest.get(field, [])
        if not isinstance(value, list):
            raise InputError(f"Reuse manifest {field} must be an array")
        for item in value:
            if not isinstance(item, dict):
                raise InputError(f"Reuse manifest {field} entries must be objects")
            result.append(item)
    return tuple(result)


def _source_revision_changed(
    manifests: Sequence[tuple[Path, Mapping[str, Any]]],
    track_plan: FrozenTrackPlan,
) -> bool:
    current = {
        track_plan.source.raw_sha256,
        track_plan.source.normalized_body_sha256,
        track_plan.source.spoken_sha256,
    }
    recorded: list[str] = []
    for _path, manifest in manifests:
        for field in ("raw_sha256", "source_sha256", "spoken_sha256"):
            value = manifest.get(field)
            if isinstance(value, str):
                recorded.append(value)
    return bool(recorded) and any(value not in current for value in recorded)


def _assembled_candidate(
    workspace_root: Path,
    manifests: Sequence[tuple[Path, Mapping[str, Any]]],
    track_plan: FrozenTrackPlan,
) -> tuple[ValidatedArtifactBinding | None, bool]:
    expected_identities = [item.render_identity_sha256 for item in track_plan.source.segments]
    valid: list[ValidatedArtifactBinding] = []
    for manifest_path, manifest in manifests:
        identities = manifest.get("active_render_identity_sha256s")
        if identities is None:
            raw_segments = manifest.get("segments")
            if isinstance(raw_segments, list) and all(isinstance(item, dict) for item in raw_segments):
                identities = [item.get("render_identity_sha256") for item in raw_segments]
        if identities != expected_identities:
            continue
        render_config = manifest.get("render_config_sha256")
        if render_config != track_plan.source.segments[0].render_config_sha256:
            continue
        path_value = manifest.get("track_audio_path", manifest.get("chapter_audio_path"))
        hash_value = manifest.get("track_audio_sha256", manifest.get("chapter_audio_sha256"))
        try:
            audio_path = _candidate_path(
                workspace_root,
                manifest_path.parent,
                path_value,
                "assembled audio path",
            )
            content = read_bytes_nofollow(audio_path)
        except (InputError, OSError):
            continue
        digest = sha256_bytes(content)
        if hash_value != digest:
            continue
        valid.append(
            ValidatedArtifactBinding(
                path=workspace_relative(workspace_root, audio_path),
                byte_count=len(content),
                sha256=digest,
            )
        )
    if len(valid) == 1:
        return valid[0], False
    return None, len(valid) > 1


def classify_track_reuse(
    workspace_root: Path,
    track_plan: FrozenTrackPlan,
    config: BookProductionConfig,
    catalog_track: CatalogTrack,
    manifest_paths: Sequence[Path],
    *,
    comparison_call_ceiling: int | None = None,
    charge_uncertain: bool = False,
) -> TrackReuseAssessment:
    """Apply current per-segment reuse checks and calculate an exact call bound."""

    root = workspace_root.expanduser().resolve()
    if track_plan.track_id != catalog_track.id:
        raise InputError("Reuse catalog Track does not match FrozenTrackPlan")
    if track_plan.effective_config != catalog_track.effective_config:
        raise InputError(f"Effective configuration drifted for {track_plan.track_id!r}")
    current = _current_segments(root, config, catalog_track, track_plan)
    manifests = _load_manifests(root, manifest_paths)
    all_entries: list[tuple[Path, Mapping[str, Any], Mapping[str, Any]]] = []
    for manifest_path, manifest in manifests:
        for entry in _manifest_entries(manifest):
            all_entries.append((manifest_path, manifest, entry))

    segment_results: list[SegmentReuseAssessment] = []
    for snapshot, segment in current:
        candidates: list[_ValidatedCandidate] = []
        findings: set[str] = set()
        matching_identity_seen = False
        for manifest_path, manifest, entry in all_entries:
            if entry.get("text_sha256") != snapshot.text_sha256:
                continue
            if entry.get("render_identity_sha256") == snapshot.render_identity_sha256:
                matching_identity_seen = True
            try:
                candidates.append(
                    _validate_candidate(
                        root,
                        manifest_path,
                        manifest,
                        entry,
                        track_plan,
                        snapshot,
                        segment,
                    )
                )
            except (InputError, OSError, EOFError, wave.Error) as exc:
                category = str(exc)
                findings.add(category if category.startswith("candidate-") else "candidate-invalid")

        if len(candidates) == 1:
            candidate = candidates[0]
            segment_results.append(
                SegmentReuseAssessment(
                    segment_id=snapshot.segment_id,
                    render_identity_sha256=snapshot.render_identity_sha256,
                    disposition=ReuseDisposition.CURRENT_REUSABLE,
                    candidate_audio=candidate.audio,
                    transcript_sha256=candidate.transcript_sha256,
                    event_journal_sha256=candidate.event_journal_sha256,
                    finding_categories=(),
                )
            )
        else:
            if len(candidates) > 1:
                findings.add("candidate-ambiguous")
            elif not matching_identity_seen:
                findings.add("cache-miss")
            segment_results.append(
                SegmentReuseAssessment(
                    segment_id=snapshot.segment_id,
                    render_identity_sha256=snapshot.render_identity_sha256,
                    disposition=ReuseDisposition.STALE_RERENDER_REQUIRED,
                    candidate_audio=None,
                    transcript_sha256=None,
                    event_journal_sha256=None,
                    finding_categories=tuple(sorted(findings)),
                )
            )

    reusable = tuple(
        item.segment_id
        for item in segment_results
        if item.disposition is ReuseDisposition.CURRENT_REUSABLE
    )
    rerender = tuple(
        item.segment_id
        for item in segment_results
        if item.disposition is ReuseDisposition.STALE_RERENDER_REQUIRED
    )
    maximum_new_calls = len(rerender)
    if maximum_new_calls > track_plan.maximum_new_calls:
        raise InputError("Calculated cache misses exceed FrozenTrackPlan call ceiling")
    comparison_ceiling = (
        track_plan.maximum_new_calls
        if comparison_call_ceiling is None
        else comparison_call_ceiling
    )
    if type(comparison_ceiling) is not int or comparison_ceiling < 0:
        raise InputError("comparison_call_ceiling must be a nonnegative integer")
    fan_out = maximum_new_calls > comparison_ceiling

    assembled: ValidatedArtifactBinding | None = None
    ambiguous_assembly = False
    if not rerender:
        assembled, ambiguous_assembly = _assembled_candidate(root, manifests, track_plan)
    if rerender:
        disposition = ReuseDisposition.STALE_RERENDER_REQUIRED
    elif assembled is None:
        disposition = ReuseDisposition.REASSEMBLY_REQUIRED
    else:
        disposition = ReuseDisposition.CURRENT_REUSABLE

    blockers: set[str] = set()
    if fan_out:
        blockers.add("unexpected-invalidation-fan-out")
    if charge_uncertain:
        blockers.add("charge-uncertain-prior-state")
    if ambiguous_assembly:
        blockers.add("assembled-candidate-ambiguous")

    if charge_uncertain:
        prior_state = PriorArtifactState.CHARGE_UNCERTAIN
    elif not manifests:
        prior_state = PriorArtifactState.ABSENT
    elif disposition is ReuseDisposition.CURRENT_REUSABLE:
        prior_state = PriorArtifactState.REUSABLE
    else:
        prior_state = PriorArtifactState.REJECTED

    unsealed = TrackReuseAssessment(
        track_id=track_plan.track_id,
        prior_state=prior_state,
        disposition=disposition,
        segments=tuple(segment_results),
        reusable_segment_ids=reusable,
        rerender_segment_ids=rerender,
        maximum_new_calls=maximum_new_calls,
        planned_call_ceiling=track_plan.maximum_new_calls,
        comparison_call_ceiling=comparison_ceiling,
        invalidation_fan_out_blocked=fan_out,
        source_revision_changed=_source_revision_changed(manifests, track_plan),
        assembled_audio=assembled,
        blocking_categories=tuple(sorted(blockers)),
        canonical_sha256="",
    )
    return _seal(unsealed)


def classify_destination(
    workspace_root: Path,
    track_id: str,
    destination_path: str,
    *,
    expected_artifact: ValidatedArtifactBinding | None,
) -> DestinationAssessment:
    """Classify a destination without writing or replacing either artifact."""

    destination = _relative_path(destination_path, "delivery destination")
    absolute = resolve_inside(workspace_root.expanduser().resolve(), destination)
    if not os.path.lexists(absolute):
        state = DestinationState.ABSENT
        byte_count = None
        digest = None
    else:
        if absolute.is_symlink() or not absolute.is_file():
            state = DestinationState.CONFLICTING
            byte_count = None
            digest = None
        else:
            content = read_bytes_nofollow(absolute)
            byte_count = len(content)
            digest = sha256_bytes(content)
            if expected_artifact is None:
                state = DestinationState.CONFLICTING
            else:
                expected_path = resolve_inside(workspace_root, expected_artifact.path)
                expected_bytes = read_bytes_nofollow(expected_path)
                if (
                    len(expected_bytes) == expected_artifact.byte_count
                    and sha256_bytes(expected_bytes) == expected_artifact.sha256
                    and content == expected_bytes
                ):
                    state = DestinationState.ALREADY_IDENTICAL
                else:
                    state = DestinationState.CONFLICTING
    unsealed = DestinationAssessment(
        track_id=track_id,
        path=destination,
        state=state,
        destination_byte_count=byte_count,
        destination_sha256=digest,
        expected_sha256=(expected_artifact.sha256 if expected_artifact is not None else None),
        canonical_sha256="",
    )
    return _seal(unsealed)


def _observation_changed(
    before: FileObservation | None,
    after: FileObservation | None,
) -> bool:
    if before is None or after is None:
        return True
    return (
        before.exists,
        before.byte_count,
        before.sha256,
    ) != (
        after.exists,
        after.byte_count,
        after.sha256,
    )


def evaluate_isolation(
    baseline: ProtectedInventory,
    current: ProtectedInventory,
    allowlist: WorkflowWriteAllowlist,
    *,
    workflow_written_paths: Iterable[str] = (),
) -> IsolationAssessment:
    """Compare per-file snapshots; concurrent unselected edits are not hard drift."""

    before_protected = {item.path: item for item in baseline.files}
    after_protected = {item.path: item for item in current.files}
    hard = tuple(
        sorted(
            path
            for path in set(before_protected) | set(after_protected)
            if _observation_changed(before_protected.get(path), after_protected.get(path))
        )
    )
    before_unselected = {item.path: item for item in baseline.unselected_manuscript_files}
    after_unselected = {item.path: item for item in current.unselected_manuscript_files}
    concurrent = tuple(
        sorted(
            path
            for path in set(before_unselected) | set(after_unselected)
            if _observation_changed(before_unselected.get(path), after_unselected.get(path))
        )
    )
    outside = tuple(
        sorted(
            {
                _relative_path(path, "workflow-written path")
                for path in workflow_written_paths
                if not allowlist.contains(path)
            }
        )
    )
    passed = not hard and not outside
    unsealed = IsolationAssessment(hard, concurrent, outside, passed, "")
    return _seal(unsealed)


def _default_required_free_bytes(plan: FrozenBatchPlan) -> int:
    # A local-only conservative workspace envelope.  It is deliberately independent
    # of pricing/token estimates, which belong to the next task.
    return 64 * 1024 * 1024 + sum(
        track.maximum_new_calls * 16 * 1024 * 1024 for track in plan.tracks
    )


def run_local_preflight(
    workspace_root: Path,
    config: BookProductionConfig,
    catalog: OrderedTrackCatalog,
    plan: FrozenBatchPlan,
    targeted_checks: TargetedCheckBinding,
    *,
    manifest_paths_by_track: Mapping[str, Sequence[Path]] | None = None,
    comparison_call_ceilings: Mapping[str, int] | None = None,
    required_free_bytes: int | None = None,
    git_statuses: Mapping[str, str] | None = None,
) -> LocalPreflightResult:
    """Run Task 2.1's complete local-only preflight and return immutable evidence."""

    root = workspace_root.expanduser().resolve()
    config_path = resolve_inside(root, plan.config_path)
    config_bytes = read_bytes_nofollow(config_path)
    config_sha256 = sha256_bytes(config_bytes)
    if config_sha256 != plan.config_sha256:
        raise InputError("Production configuration drifted from FrozenBatchPlan")
    if plan.book_id != config.book_id:
        raise InputError("Production configuration book_id does not match FrozenBatchPlan")
    if len(plan.tracks) > config.max_tracks_per_plan:
        raise InputError("FrozenBatchPlan exceeds current max_tracks_per_plan")

    catalog_by_id = {item.id: item for item in catalog.tracks}
    legacy = ReadOnlyLegacyAdapter(root)
    explicit = manifest_paths_by_track or {}
    ceilings = comparison_call_ceilings or {}
    reuse: list[TrackReuseAssessment] = []
    prior_paths: set[str] = set()
    for track_plan in plan.tracks:
        catalog_track = catalog_by_id.get(track_plan.track_id)
        if catalog_track is None:
            raise InputError(f"Frozen Track no longer exists in catalog: {track_plan.track_id!r}")
        if canonical_sha256(track_plan.command_argv) != track_plan.command_sha256:
            raise InputError(f"Worker command hash mismatch for {track_plan.track_id!r}")
        if track_plan.maximum_new_calls != track_plan.source.segment_count:
            raise InputError(f"Frozen call ceiling is inconsistent for {track_plan.track_id!r}")
        if track_plan.track_id in explicit:
            manifests = tuple(explicit[track_plan.track_id])
            uncertain = False
        elif track_plan.track_id in {"chapter-001", "chapter-002"}:
            chapter = _chapter_number(track_plan.track_id)
            manifests = legacy.manifest_paths(chapter)
            uncertain = legacy.has_uncertain_evidence(chapter)
        else:
            manifests = ()
            uncertain = False
        for manifest in manifests:
            absolute = manifest if manifest.is_absolute() else resolve_inside(root, manifest.as_posix())
            prior_paths.add(workspace_relative(root, absolute.parent))
        reuse.append(
            classify_track_reuse(
                root,
                track_plan,
                config,
                catalog_track,
                manifests,
                comparison_call_ceiling=ceilings.get(
                    track_plan.track_id,
                    track_plan.maximum_new_calls,
                ),
                charge_uncertain=uncertain,
            )
        )

    allowlist = derive_workflow_write_allowlist(config, plan)
    inventory = build_protected_inventory(
        root,
        config,
        plan,
        prior_artifact_paths=tuple(sorted(prior_paths)),
        git_statuses=git_statuses,
    )
    required = (
        _default_required_free_bytes(plan)
        if required_free_bytes is None
        else required_free_bytes
    )
    atomic_pairs: list[tuple[str, str]] = []
    for write_root in allowlist.recursive_roots:
        atomic_pairs.append(
            (
                (PurePosixPath(write_root) / ".preflight-staging").as_posix(),
                (PurePosixPath(write_root) / "committed").as_posix(),
            )
        )
    for exact_path in allowlist.exact_paths:
        parent = PurePosixPath(exact_path).parent
        atomic_pairs.append(
            (
                (parent / f".{PurePosixPath(exact_path).name}.tmp").as_posix(),
                exact_path,
            )
        )
    filesystem = inspect_local_filesystems(
        root,
        allowlist,
        required_free_bytes=required,
        atomic_pairs=atomic_pairs,
    )

    destinations = tuple(
        classify_destination(
            root,
            track_plan.track_id,
            track_plan.effective_config.output_path,
            expected_artifact=assessment.assembled_audio,
        )
        for track_plan, assessment in zip(plan.tracks, reuse, strict=True)
    )
    call_rows = tuple((item.track_id, item.maximum_new_calls) for item in reuse)
    blockers: set[str] = set(filesystem.blocking_categories)
    if not targeted_checks.passed:
        blockers.add("targeted-checks-failed-or-unbounded")
    for assessment in reuse:
        blockers.update(assessment.blocking_categories)
    if any(item.state is DestinationState.CONFLICTING for item in destinations):
        blockers.add("delivery-destination-conflict")

    unsealed = LocalPreflightResult(
        plan_sha256=StrictRecordCodec(FrozenBatchPlan).sha256(plan),
        config_sha256=config_sha256,
        targeted_checks=targeted_checks,
        inventory=inventory,
        write_allowlist=allowlist,
        filesystem=filesystem,
        track_reuse=tuple(reuse),
        destinations=destinations,
        maximum_new_calls_by_track=call_rows,
        maximum_new_calls_total=sum(value for _track_id, value in call_rows),
        blocking_categories=tuple(sorted(blockers)),
        passed=not blockers,
        canonical_sha256="",
    )
    return _seal(unsealed)


# Task 2.2: injected non-model identity, strict normalized official rates, and
# bounded Decimal estimates.  The adapters below accept local/injected inputs;
# this module deliberately provides no live AWS, HTTP, or Bedrock client.
from collections.abc import Callable
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal, InvalidOperation
import re
from urllib.parse import urlsplit


ON_DEMAND_PURCHASE_OPTION = "on-demand"
OFFICIAL_RATE_CURRENCY = "USD"
OFFICIAL_RATE_UNIT = "per-1k-tokens"
_RATE_SOURCE_SCHEMA_VERSION = 1
_RATE_MODALITIES = (
    "input_speech",
    "input_text",
    "output_speech",
    "output_text",
)
_DECIMAL_TEXT_PATTERN = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d+)?$")
_DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_UTC_TIMESTAMP_PATTERN = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$"
)


def _preflight_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value:
        raise InputError(f"{label} must be a nonblank canonical string")
    return value


def _preflight_nonnegative_int(value: object, label: str) -> int:
    if type(value) is not int or value < 0:
        raise InputError(f"{label} must be a nonnegative integer")
    return value


def _preflight_utc(value: object, label: str) -> datetime:
    text = _preflight_text(value, label)
    if not _UTC_TIMESTAMP_PATTERN.fullmatch(text):
        raise InputError(f"{label} must be an ISO-8601 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(text.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise InputError(f"{label} is not a valid UTC timestamp") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timedelta(0):
        raise InputError(f"{label} must be UTC")
    return parsed.astimezone(UTC)


def _preflight_date(value: object, label: str) -> date:
    text = _preflight_text(value, label)
    if not _DATE_PATTERN.fullmatch(text):
        raise InputError(f"{label} must be an ISO-8601 calendar date")
    try:
        return date.fromisoformat(text)
    except ValueError as exc:
        raise InputError(f"{label} is not a valid calendar date") from exc


def _preflight_decimal(
    value: object,
    label: str,
    *,
    positive: bool = False,
) -> Decimal:
    text = _preflight_text(value, label)
    if not _DECIMAL_TEXT_PATTERN.fullmatch(text):
        raise InputError(f"{label} must be a nonnegative plain decimal string")
    try:
        parsed = Decimal(text)
    except InvalidOperation as exc:  # pragma: no cover - guarded by the pattern
        raise InputError(f"{label} must be a valid decimal string") from exc
    if not parsed.is_finite() or parsed < 0 or (positive and parsed == 0):
        qualifier = "positive" if positive else "nonnegative"
        raise InputError(f"{label} must be finite and {qualifier}")
    return parsed


def _canonical_decimal(value: Decimal) -> str:
    if not value.is_finite() or value < 0:
        raise InputError("Estimated Decimal values must be finite and nonnegative")
    if value == 0:
        return "0"
    return format(value.normalize(), "f")


def _official_source_url(value: object) -> str:
    text = _preflight_text(value, "official rate source_url")
    parsed = urlsplit(text)
    hostname = parsed.hostname.casefold() if parsed.hostname is not None else ""
    official_host = (
        hostname == "aws.amazon.com"
        or hostname.endswith(".aws.amazon.com")
        or hostname.endswith(".amazonaws.com")
    )
    if (
        parsed.scheme != "https"
        or not official_host
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        raise InputError("official rate source_url must be an uncredentialed official AWS HTTPS URL")
    return text


def _exact_object_keys(
    value: object,
    *,
    required: set[str],
    label: str,
) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise InputError(f"{label} must be an object")
    actual = set(value)
    if actual != required:
        raise InputError(
            f"{label} fields are invalid; missing={sorted(required - actual)}, "
            f"unknown={sorted(actual - required)}"
        )
    return value


@dataclass(frozen=True, slots=True)
class IdentityEvidence:
    """The complete and only persisted projection of one identity response."""

    profile_label: str
    resolved: bool
    checked_at_utc: str

    def __post_init__(self) -> None:
        _preflight_text(self.profile_label, "identity profile_label")
        if type(self.resolved) is not bool:
            raise InputError("identity resolved must be a boolean")
        _preflight_utc(self.checked_at_utc, "identity checked_at_utc")


@dataclass(frozen=True, slots=True)
class OfficialRateTarget:
    model_id: str
    region: str
    purchase_option: str = ON_DEMAND_PURCHASE_OPTION

    def __post_init__(self) -> None:
        _preflight_text(self.model_id, "official rate target model_id")
        _preflight_text(self.region, "official rate target region")
        _preflight_text(self.purchase_option, "official rate target purchase_option")
        if self.purchase_option != ON_DEMAND_PURCHASE_OPTION:
            raise InputError("Only the on-demand purchase option is supported")


@dataclass(frozen=True, slots=True)
class OfficialModalityRate:
    modality: str
    rate_per_1k_tokens: str

    def __post_init__(self) -> None:
        if self.modality not in _RATE_MODALITIES:
            raise InputError(f"Unknown official rate modality: {self.modality!r}")
        _preflight_decimal(
            self.rate_per_1k_tokens,
            f"official rate {self.modality}",
            positive=True,
        )


@dataclass(frozen=True, slots=True)
class OfficialRateCard:
    """Four rates plus every allowed provenance field needed for review."""

    model_id: str
    region: str
    purchase_option: str
    currency: str
    unit: str
    source_url: str
    offer_publication_date: str
    retrieved_at_utc: str
    effective_date: str
    rates: tuple[OfficialModalityRate, ...]

    def __post_init__(self) -> None:
        OfficialRateTarget(self.model_id, self.region, self.purchase_option)
        if self.currency != OFFICIAL_RATE_CURRENCY:
            raise InputError(f"Official rates must use {OFFICIAL_RATE_CURRENCY}")
        if self.unit != OFFICIAL_RATE_UNIT:
            raise InputError(f"Official rates must use {OFFICIAL_RATE_UNIT}")
        _official_source_url(self.source_url)
        _preflight_date(self.offer_publication_date, "official rate offer_publication_date")
        _preflight_utc(self.retrieved_at_utc, "official rate retrieved_at_utc")
        _preflight_date(self.effective_date, "official rate effective_date")
        if not isinstance(self.rates, tuple) or not all(
            isinstance(item, OfficialModalityRate) for item in self.rates
        ):
            raise InputError("Official rate card rates must be a tuple of OfficialModalityRate")
        if tuple(item.modality for item in self.rates) != _RATE_MODALITIES:
            raise InputError("Official rate card must contain each modality exactly once in canonical order")

    @property
    def target(self) -> OfficialRateTarget:
        return OfficialRateTarget(self.model_id, self.region, self.purchase_option)


@dataclass(frozen=True, slots=True)
class ModalityTokenAmount:
    modality: str
    tokens: int

    def __post_init__(self) -> None:
        if self.modality not in _RATE_MODALITIES:
            raise InputError(f"Unknown token modality: {self.modality!r}")
        _preflight_nonnegative_int(self.tokens, f"{self.modality} token amount")


@dataclass(frozen=True, slots=True)
class ModalityDecimalAmount:
    modality: str
    amount_usd: str

    def __post_init__(self) -> None:
        if self.modality not in _RATE_MODALITIES:
            raise InputError(f"Unknown cost modality: {self.modality!r}")
        _preflight_decimal(self.amount_usd, f"{self.modality} amount_usd")


@dataclass(frozen=True, slots=True)
class TrackCostEstimate:
    track_id: str
    model_id: str
    region: str
    purchase_option: str
    maximum_new_calls: int
    maximum_tokens_by_modality: tuple[ModalityTokenAmount, ...]
    subtotals_by_modality_usd: tuple[ModalityDecimalAmount, ...]
    estimated_pre_tax_usd: str

    def __post_init__(self) -> None:
        _preflight_text(self.track_id, "Track estimate track_id")
        OfficialRateTarget(self.model_id, self.region, self.purchase_option)
        _preflight_nonnegative_int(self.maximum_new_calls, "Track estimate maximum_new_calls")
        if tuple(item.modality for item in self.maximum_tokens_by_modality) != _RATE_MODALITIES:
            raise InputError("Track estimate token modalities must be complete and canonical")
        if tuple(item.modality for item in self.subtotals_by_modality_usd) != _RATE_MODALITIES:
            raise InputError("Track estimate cost modalities must be complete and canonical")
        expected = sum(
            (_preflight_decimal(item.amount_usd, f"Track estimate {item.modality}") for item in self.subtotals_by_modality_usd),
            start=Decimal("0"),
        )
        if _preflight_decimal(self.estimated_pre_tax_usd, "Track estimated_pre_tax_usd") != expected:
            raise InputError("Track estimated_pre_tax_usd must equal its exact modality subtotals")


@dataclass(frozen=True, slots=True)
class BoundedCostEstimate:
    maximum_new_calls_by_track: tuple[tuple[str, int], ...]
    maximum_new_calls_total: int
    configured_tokens_per_call: tuple[ModalityTokenAmount, ...]
    maximum_tokens_by_modality: tuple[ModalityTokenAmount, ...]
    subtotals_by_modality_usd: tuple[ModalityDecimalAmount, ...]
    tracks: tuple[TrackCostEstimate, ...]
    estimated_pre_tax_usd: str
    assumptions: tuple[str, ...]
    canonical_sha256: str

    def __post_init__(self) -> None:
        if not isinstance(self.maximum_new_calls_by_track, tuple) or not self.maximum_new_calls_by_track:
            raise InputError("Cost estimate call bounds must be a nonempty tuple")
        track_ids: list[str] = []
        for track_id, calls in self.maximum_new_calls_by_track:
            _preflight_text(track_id, "Cost estimate track_id")
            _preflight_nonnegative_int(calls, f"Cost estimate calls for {track_id}")
            track_ids.append(track_id)
        if len(set(track_ids)) != len(track_ids):
            raise InputError("Cost estimate Track IDs must be unique")
        _preflight_nonnegative_int(self.maximum_new_calls_total, "Cost estimate total calls")
        if self.maximum_new_calls_total != sum(value for _track_id, value in self.maximum_new_calls_by_track):
            raise InputError("Cost estimate total calls must equal per-Track call bounds")
        if tuple(item.modality for item in self.configured_tokens_per_call) != _RATE_MODALITIES:
            raise InputError("Configured token envelopes must be complete and canonical")
        if tuple(item.modality for item in self.maximum_tokens_by_modality) != _RATE_MODALITIES:
            raise InputError("Maximum token totals must be complete and canonical")
        if tuple(item.modality for item in self.subtotals_by_modality_usd) != _RATE_MODALITIES:
            raise InputError("Cost subtotals must be complete and canonical")
        if tuple(item.track_id for item in self.tracks) != tuple(track_ids):
            raise InputError("Track estimates must match the exact ordered call-bound scope")
        aggregate_tokens = {
            modality: sum(
                next(item.tokens for item in track.maximum_tokens_by_modality if item.modality == modality)
                for track in self.tracks
            )
            for modality in _RATE_MODALITIES
        }
        if aggregate_tokens != {item.modality: item.tokens for item in self.maximum_tokens_by_modality}:
            raise InputError("Maximum token totals must equal the sum of Track envelopes")
        aggregate_subtotals = {
            modality: sum(
                (
                    _preflight_decimal(
                        next(
                            item.amount_usd
                            for item in track.subtotals_by_modality_usd
                            if item.modality == modality
                        ),
                        f"Track subtotal {track.track_id}/{modality}",
                    )
                    for track in self.tracks
                ),
                start=Decimal("0"),
            )
            for modality in _RATE_MODALITIES
        }
        if aggregate_subtotals != {
            item.modality: _preflight_decimal(item.amount_usd, f"Aggregate subtotal {item.modality}")
            for item in self.subtotals_by_modality_usd
        }:
            raise InputError("Cost subtotals must equal the sum of Track subtotals")
        total = sum(aggregate_subtotals.values(), start=Decimal("0"))
        if _preflight_decimal(self.estimated_pre_tax_usd, "estimated_pre_tax_usd") != total:
            raise InputError("estimated_pre_tax_usd must equal exact modality subtotals")
        if not isinstance(self.assumptions, tuple) or not self.assumptions:
            raise InputError("Cost estimate assumptions must be a nonempty tuple")
        for assumption in self.assumptions:
            _preflight_text(assumption, "Cost estimate assumption")
        if len(set(self.assumptions)) != len(self.assumptions):
            raise InputError("Cost estimate assumptions must be unique")
        _sha256(self.canonical_sha256, "Cost estimate canonical_sha256") if self.canonical_sha256 else None


@dataclass(frozen=True, slots=True)
class BoundedPreflightEstimateResult:
    plan_sha256: str
    local_preflight_sha256: str
    checked_at_utc: str
    identity_evidence: tuple[IdentityEvidence, ...]
    official_rate_cards: tuple[OfficialRateCard, ...]
    estimate: BoundedCostEstimate
    blocking_categories: tuple[str, ...]
    passed: bool
    canonical_sha256: str

    def __post_init__(self) -> None:
        _sha256(self.plan_sha256, "bounded preflight plan_sha256")
        _sha256(self.local_preflight_sha256, "bounded preflight local_preflight_sha256")
        _preflight_utc(self.checked_at_utc, "bounded preflight checked_at_utc")
        if not self.identity_evidence or not all(
            isinstance(item, IdentityEvidence) for item in self.identity_evidence
        ):
            raise InputError("Bounded preflight identity_evidence must not be empty")
        if len({item.profile_label for item in self.identity_evidence}) != len(self.identity_evidence):
            raise InputError("Bounded preflight identity profiles must be unique")
        if not self.official_rate_cards or not all(
            isinstance(item, OfficialRateCard) for item in self.official_rate_cards
        ):
            raise InputError("Bounded preflight official_rate_cards must not be empty")
        if len({item.target for item in self.official_rate_cards}) != len(self.official_rate_cards):
            raise InputError("Bounded preflight official rate targets must be unique")
        if not isinstance(self.estimate, BoundedCostEstimate):
            raise InputError("Bounded preflight estimate must be a BoundedCostEstimate")
        if not isinstance(self.blocking_categories, tuple):
            raise InputError("Bounded preflight blocking_categories must be a tuple")
        for category in self.blocking_categories:
            _preflight_text(category, "Bounded preflight blocking category")
        if tuple(sorted(set(self.blocking_categories))) != self.blocking_categories:
            raise InputError("Bounded preflight blocking categories must be sorted and unique")
        if type(self.passed) is not bool:
            raise InputError("Bounded preflight passed must be a boolean")
        if self.passed != (not self.blocking_categories):
            raise InputError("Bounded preflight passed must reflect blocking_categories")
        _sha256(self.canonical_sha256, "Bounded preflight canonical_sha256") if self.canonical_sha256 else None


def resolve_minimal_identity_evidence(
    profile_labels: Iterable[str],
    identity_call: Callable[[str], object],
    *,
    checked_at_utc: str,
) -> tuple[IdentityEvidence, ...]:
    """Call an injected non-model resolver once per unique profile and discard responses.

    A successful resolver returns a nonempty mapping.  Exceptions and malformed
    responses become a minimal ``resolved=False`` projection; error text and raw
    identity fields are intentionally neither returned nor persisted.
    """

    _preflight_utc(checked_at_utc, "identity checked_at_utc")
    if not callable(identity_call):
        raise InputError("identity_call must be callable")
    ordered_profiles: list[str] = []
    seen: set[str] = set()
    for supplied in profile_labels:
        profile = _preflight_text(supplied, "configured profile label")
        if profile not in seen:
            seen.add(profile)
            ordered_profiles.append(profile)
    if not ordered_profiles:
        raise InputError("At least one configured profile label is required")

    evidence: list[IdentityEvidence] = []
    for profile in ordered_profiles:
        raw_response: object | None = None
        try:
            raw_response = identity_call(profile)
            resolved = isinstance(raw_response, Mapping) and len(raw_response) > 0
        except Exception:
            resolved = False
        projected = IdentityEvidence(profile, resolved, checked_at_utc)
        try:
            from .production_evidence import assert_identity_projection

            assert_identity_projection(projected, raw_response=raw_response)
        finally:
            # Drop the only reference held by this boundary regardless of outcome.
            # No account identifier, ARN, caller identifier, credential, error text,
            # or other raw response field enters the returned evidence.
            raw_response = None
        evidence.append(projected)
    return tuple(evidence)


def _decode_rate_document(raw: str | bytes) -> Mapping[str, Any]:
    if isinstance(raw, bytes):
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InputError(f"Official rate document is not strict UTF-8: {exc}") from exc
    elif isinstance(raw, str):
        text = raw
    else:
        raise InputError("Official rate document must be UTF-8 JSON text or bytes")
    value = json_loads_strict(text, "official rate document")
    return _exact_object_keys(
        value,
        required={
            "schema_version",
            "source_url",
            "offer_publication_date",
            "retrieved_at_utc",
            "effective_date",
            "offers",
        },
        label="official rate document",
    )


def parse_official_rate_document(
    raw: str | bytes,
    targets: Iterable[OfficialRateTarget],
    *,
    checked_at_utc: str,
    max_age_hours: int,
) -> tuple[OfficialRateCard, ...]:
    """Parse a strict locally supplied normalized official AWS rate document."""

    checked_at = _preflight_utc(checked_at_utc, "official rate checked_at_utc")
    if type(max_age_hours) is not int or max_age_hours < 1:
        raise InputError("official rate max_age_hours must be a positive integer")
    document = _decode_rate_document(raw)
    if type(document["schema_version"]) is not int or document["schema_version"] != _RATE_SOURCE_SCHEMA_VERSION:
        raise InputError(
            f"official rate document schema_version must be integer {_RATE_SOURCE_SCHEMA_VERSION}"
        )
    source_url = _official_source_url(document["source_url"])
    publication = _preflight_date(
        document["offer_publication_date"],
        "official rate offer_publication_date",
    )
    retrieved = _preflight_utc(document["retrieved_at_utc"], "official rate retrieved_at_utc")
    effective = _preflight_date(document["effective_date"], "official rate effective_date")
    if retrieved > checked_at:
        raise InputError("Official rate retrieval timestamp is in the future")
    if checked_at - retrieved > timedelta(hours=max_age_hours):
        raise InputError("Official rate document is stale")
    if publication > retrieved.date() or effective > retrieved.date():
        raise InputError("Official rate publication/effective date is later than retrieval")

    supplied_targets: list[OfficialRateTarget] = []
    seen_targets: set[OfficialRateTarget] = set()
    for target in targets:
        if not isinstance(target, OfficialRateTarget):
            raise InputError("Official rate targets must contain OfficialRateTarget records")
        if target in seen_targets:
            raise InputError("Official rate targets must be unique")
        seen_targets.add(target)
        supplied_targets.append(target)
    if not supplied_targets:
        raise InputError("At least one official rate target is required")

    raw_offers = document["offers"]
    if not isinstance(raw_offers, list) or not raw_offers:
        raise InputError("official rate document offers must be a nonempty array")
    parsed_offers: list[tuple[OfficialRateTarget, str, str]] = []
    offer_fields = {
        "model_id",
        "region",
        "purchase_option",
        "currency",
        "unit",
        "modality",
        "rate_per_1k_tokens",
    }
    for index, supplied in enumerate(raw_offers):
        offer = _exact_object_keys(
            supplied,
            required=offer_fields,
            label=f"official rate offers[{index}]",
        )
        target = OfficialRateTarget(
            _preflight_text(offer["model_id"], f"official rate offers[{index}].model_id"),
            _preflight_text(offer["region"], f"official rate offers[{index}].region"),
            _preflight_text(
                offer["purchase_option"],
                f"official rate offers[{index}].purchase_option",
            ),
        )
        currency = _preflight_text(offer["currency"], f"official rate offers[{index}].currency")
        if currency != OFFICIAL_RATE_CURRENCY:
            raise InputError(f"Official rate currency must be {OFFICIAL_RATE_CURRENCY}")
        unit = _preflight_text(offer["unit"], f"official rate offers[{index}].unit")
        if unit != OFFICIAL_RATE_UNIT:
            raise InputError(f"Official rate unit must be {OFFICIAL_RATE_UNIT}")
        modality = _preflight_text(offer["modality"], f"official rate offers[{index}].modality")
        if modality not in _RATE_MODALITIES:
            raise InputError(f"Unknown official rate modality: {modality!r}")
        rate_text = _preflight_text(
            offer["rate_per_1k_tokens"],
            f"official rate offers[{index}].rate_per_1k_tokens",
        )
        _preflight_decimal(rate_text, f"official rate offers[{index}].rate", positive=True)
        parsed_offers.append((target, modality, rate_text))

    cards: list[OfficialRateCard] = []
    for target in supplied_targets:
        matching = [row for row in parsed_offers if row[0] == target]
        rates: list[OfficialModalityRate] = []
        for modality in _RATE_MODALITIES:
            modality_rows = [row[2] for row in matching if row[1] == modality]
            if not modality_rows:
                raise InputError(
                    f"Missing official {modality} rate for {target.model_id}/{target.region}/{target.purchase_option}"
                )
            if len(modality_rows) > 1:
                distinct = {_preflight_decimal(item, f"duplicate {modality} rate") for item in modality_rows}
                category = "duplicate" if len(distinct) == 1 else "ambiguous"
                raise InputError(
                    f"{category.capitalize()} official {modality} rates for "
                    f"{target.model_id}/{target.region}/{target.purchase_option}"
                )
            rates.append(OfficialModalityRate(modality, modality_rows[0]))
        cards.append(
            OfficialRateCard(
                model_id=target.model_id,
                region=target.region,
                purchase_option=target.purchase_option,
                currency=OFFICIAL_RATE_CURRENCY,
                unit=OFFICIAL_RATE_UNIT,
                source_url=source_url,
                offer_publication_date=document["offer_publication_date"],
                retrieved_at_utc=document["retrieved_at_utc"],
                effective_date=document["effective_date"],
                rates=tuple(rates),
            )
        )
    return tuple(cards)


def _configured_token_envelopes(config: BookProductionConfig) -> tuple[ModalityTokenAmount, ...]:
    estimate = config.estimate
    return tuple(
        ModalityTokenAmount(modality, getattr(estimate, f"{modality}_tokens_per_call"))
        for modality in _RATE_MODALITIES
    )


def calculate_bounded_decimal_estimate(
    config: BookProductionConfig,
    plan: FrozenBatchPlan,
    local_preflight: LocalPreflightResult,
    rate_cards: Sequence[OfficialRateCard],
    *,
    purchase_option: str = ON_DEMAND_PURCHASE_OPTION,
) -> BoundedCostEstimate:
    """Price exactly Task 2.1's selected nonreusable render identities."""

    if not isinstance(config, BookProductionConfig):
        raise InputError("Decimal estimate requires BookProductionConfig")
    if not isinstance(plan, FrozenBatchPlan):
        raise InputError("Decimal estimate requires FrozenBatchPlan")
    if not isinstance(local_preflight, LocalPreflightResult):
        raise InputError("Decimal estimate requires LocalPreflightResult")
    _preflight_text(purchase_option, "estimate purchase_option")
    if purchase_option != ON_DEMAND_PURCHASE_OPTION:
        raise InputError("Only on-demand estimates are supported")
    plan_sha256 = StrictRecordCodec(FrozenBatchPlan).sha256(plan)
    if local_preflight.plan_sha256 != plan_sha256:
        raise InputError("Local preflight is not bound to the supplied FrozenBatchPlan")
    if local_preflight.config_sha256 != plan.config_sha256:
        raise InputError("Local preflight configuration digest differs from FrozenBatchPlan")

    expected_track_ids = tuple(track.track_id for track in plan.tracks)
    call_rows = local_preflight.maximum_new_calls_by_track
    if tuple(track_id for track_id, _calls in call_rows) != expected_track_ids:
        raise InputError("Local preflight call bounds do not match exact ordered Track scope")
    if len({track_id for track_id, _calls in call_rows}) != len(call_rows):
        raise InputError("Local preflight call-bound Track IDs must be unique")
    if local_preflight.maximum_new_calls_total != sum(calls for _track_id, calls in call_rows):
        raise InputError("Local preflight total call ceiling is inconsistent")
    reuse_rows = tuple(
        (item.track_id, item.maximum_new_calls) for item in local_preflight.track_reuse
    )
    if reuse_rows != call_rows:
        raise InputError("Local preflight call ceilings must equal exact cache-miss assessments")
    plan_by_id = {item.track_id: item for item in plan.tracks}
    for track_id, calls in call_rows:
        _preflight_nonnegative_int(calls, f"maximum new calls for {track_id}")
        if calls > plan_by_id[track_id].maximum_new_calls:
            raise InputError("Local cache misses exceed the frozen Track call ceiling")

    cards_by_target: dict[OfficialRateTarget, OfficialRateCard] = {}
    for card in rate_cards:
        if not isinstance(card, OfficialRateCard):
            raise InputError("rate_cards must contain OfficialRateCard records")
        if card.target in cards_by_target:
            raise InputError("Duplicate OfficialRateCard target")
        cards_by_target[card.target] = card
    envelopes = _configured_token_envelopes(config)
    envelope_map = {item.modality: item.tokens for item in envelopes}

    tracks: list[TrackCostEstimate] = []
    aggregate_tokens = {modality: 0 for modality in _RATE_MODALITIES}
    aggregate_subtotals = {modality: Decimal("0") for modality in _RATE_MODALITIES}
    for track_plan, (track_id, maximum_calls) in zip(plan.tracks, call_rows, strict=True):
        effective = track_plan.effective_config
        target = OfficialRateTarget(effective.model_id, effective.region, purchase_option)
        card = cards_by_target.get(target)
        if card is None:
            raise InputError(
                f"Missing OfficialRateCard for {target.model_id}/{target.region}/{target.purchase_option}"
            )
        rate_map = {
            item.modality: _preflight_decimal(
                item.rate_per_1k_tokens,
                f"official rate {target.model_id}/{item.modality}",
                positive=True,
            )
            for item in card.rates
        }
        token_rows: list[ModalityTokenAmount] = []
        subtotal_rows: list[ModalityDecimalAmount] = []
        track_total = Decimal("0")
        for modality in _RATE_MODALITIES:
            maximum_tokens = maximum_calls * envelope_map[modality]
            subtotal = Decimal(maximum_tokens) * rate_map[modality] / Decimal(1000)
            token_rows.append(ModalityTokenAmount(modality, maximum_tokens))
            subtotal_rows.append(ModalityDecimalAmount(modality, _canonical_decimal(subtotal)))
            aggregate_tokens[modality] += maximum_tokens
            aggregate_subtotals[modality] += subtotal
            track_total += subtotal
        tracks.append(
            TrackCostEstimate(
                track_id=track_id,
                model_id=target.model_id,
                region=target.region,
                purchase_option=target.purchase_option,
                maximum_new_calls=maximum_calls,
                maximum_tokens_by_modality=tuple(token_rows),
                subtotals_by_modality_usd=tuple(subtotal_rows),
                estimated_pre_tax_usd=_canonical_decimal(track_total),
            )
        )

    total = sum(aggregate_subtotals.values(), start=Decimal("0"))
    unsealed = BoundedCostEstimate(
        maximum_new_calls_by_track=tuple(call_rows),
        maximum_new_calls_total=local_preflight.maximum_new_calls_total,
        configured_tokens_per_call=envelopes,
        maximum_tokens_by_modality=tuple(
            ModalityTokenAmount(modality, aggregate_tokens[modality])
            for modality in _RATE_MODALITIES
        ),
        subtotals_by_modality_usd=tuple(
            ModalityDecimalAmount(modality, _canonical_decimal(aggregate_subtotals[modality]))
            for modality in _RATE_MODALITIES
        ),
        tracks=tuple(tracks),
        estimated_pre_tax_usd=_canonical_decimal(total),
        assumptions=(
            "selected-nonreusable-render-identities-only",
            "validated-reuse-contributes-zero-new-calls",
            "at-most-one-call-per-nonreusable-render-identity",
            "configured-finite-token-envelopes-per-call",
            "official-on-demand-usd-rates-per-1k-tokens",
            "exact-decimal-arithmetic-without-intermediate-rounding",
        ),
        canonical_sha256="",
    )
    return _seal(unsealed)


def run_bounded_identity_rate_preflight(
    config: BookProductionConfig,
    plan: FrozenBatchPlan,
    local_preflight: LocalPreflightResult,
    *,
    identity_call: Callable[[str], object],
    official_rate_document: str | bytes,
    checked_at_utc: str,
    purchase_option: str = ON_DEMAND_PURCHASE_OPTION,
) -> BoundedPreflightEstimateResult:
    """Complete Task 2.2 through injected boundaries without any model call."""

    if not local_preflight.passed:
        raise InputError("Local preflight must pass before identity or rate resolution")
    profiles = tuple(track.effective_config.profile_label for track in plan.tracks)
    identities = resolve_minimal_identity_evidence(
        profiles,
        identity_call,
        checked_at_utc=checked_at_utc,
    )
    targets: list[OfficialRateTarget] = []
    seen_targets: set[OfficialRateTarget] = set()
    for track in plan.tracks:
        target = OfficialRateTarget(
            track.effective_config.model_id,
            track.effective_config.region,
            purchase_option,
        )
        if target not in seen_targets:
            seen_targets.add(target)
            targets.append(target)
    cards = parse_official_rate_document(
        official_rate_document,
        targets,
        checked_at_utc=checked_at_utc,
        max_age_hours=config.estimate.rate_max_age_hours,
    )
    estimate = calculate_bounded_decimal_estimate(
        config,
        plan,
        local_preflight,
        cards,
        purchase_option=purchase_option,
    )
    blockers = tuple(
        sorted(
            {
                "identity-resolution-failed"
                for item in identities
                if not item.resolved
            }
        )
    )
    unsealed = BoundedPreflightEstimateResult(
        plan_sha256=local_preflight.plan_sha256,
        local_preflight_sha256=local_preflight.canonical_sha256,
        checked_at_utc=checked_at_utc,
        identity_evidence=identities,
        official_rate_cards=cards,
        estimate=estimate,
        blocking_categories=blockers,
        passed=not blockers,
        canonical_sha256="",
    )
    return _seal(unsealed)
