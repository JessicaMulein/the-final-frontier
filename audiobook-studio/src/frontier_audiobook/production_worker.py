"""Hidden generic production Track worker entry point.

The parent paid-attempt wrapper establishes one consumed direct-child launch.  This
module resolves either a chapter or approved Special Track through the shared source
adapters, then delegates all segmentation, rendering, verification, event replay,
content-addressed persistence, and assembly to :mod:`frontier_audiobook.narrate`.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Callable

from .config import NovaSettings, load_audition_config
from .errors import InputError
from .narrate import (
    NarrationSegmentIdentity,
    Segment,
    TrackSourceSnapshot,
    narrate_track,
)
from .production import (
    WORKER_COMMAND,
    ApprovedSpecialTrackSourceAdapter,
    ChapterSourceAdapter,
    _build_source_snapshot,
    load_production_plan,
)
from .production_config import (
    BookProductionConfig,
    CatalogTrack,
    SourceApprovalStatus,
    TrackDeclaration,
    _validate_track_semantics,
    parse_production_toml,
    resolve_effective_track_config,
)
from .production_models import (
    AudioEncoding,
    FrozenBatchPlan,
    FrozenTrackPlan,
    PaidAuthorization,
    SourceKind,
    StrictRecordCodec,
    TrackKind,
    TransactionState,
    canonical_sha256,
)
from .production_transactions import TransactionSpec, TransactionStore
from .util import (
    read_bytes_nofollow,
    read_json,
    resolve_inside,
    sha256_bytes,
    workspace_relative,
)

Clock = Callable[[], datetime]
_CHAPTER_TRACK_ID = re.compile(r"^chapter-(\d{3})$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_AUDITION_RUNTIME_CONFIG = "audiobook-studio/config/audition.toml"


@dataclass(frozen=True, slots=True)
class _ProductionNarrationConfig:
    """The structural subset of AuditionConfig consumed by the shared engine."""

    workspace_root: Path
    nova: NovaSettings
    normalization: str


@dataclass(frozen=True, slots=True)
class _FrozenProductionTrackSource:
    """Re-read one selected source and require its complete frozen snapshot."""

    workspace_root: Path
    config: BookProductionConfig
    catalog_track: CatalogTrack
    track_plan: FrozenTrackPlan

    @property
    def track_id(self) -> str:
        return self.track_plan.track_id

    def read(self) -> TrackSourceSnapshot:
        adapter = (
            ChapterSourceAdapter()
            if self.catalog_track.kind is TrackKind.CHAPTER
            else ApprovedSpecialTrackSourceAdapter()
        )
        prepared = adapter.read(
            self.config,
            self.catalog_track,
            self.workspace_root,
        )
        current = _build_source_snapshot(self.catalog_track, prepared)
        if current != self.track_plan.source:
            raise InputError(
                f"Track {self.track_id!r} source or frozen segmentation changed before rendering"
            )
        return TrackSourceSnapshot(
            track_id=self.track_id,
            source_path=current.source_path,
            source_sha256=current.raw_sha256,
            revision_sha256=canonical_sha256(current),
            spoken_text=prepared.spoken,
            manifest_metadata={
                "transaction_id": self.track_plan.transaction_id,
                "track_plan_sha256": canonical_sha256(self.track_plan),
                "effective_config_sha256": canonical_sha256(
                    self.track_plan.effective_config
                ),
                "source_snapshot_sha256": canonical_sha256(current),
                "track_kind": self.catalog_track.kind.value,
                "model_id": self.track_plan.effective_config.model_id,
                "region": self.track_plan.effective_config.region,
                "profile_label": self.track_plan.effective_config.profile_label,
                "fidelity_policy": self.track_plan.effective_config.fidelity_policy.value,
                "normalization": self.track_plan.effective_config.normalization,
                "audio_sample_rate_hz": (
                    self.track_plan.effective_config.audio_format.sample_rate_hz
                ),
                "audio_sample_size_bits": (
                    self.track_plan.effective_config.audio_format.sample_size_bits
                ),
                "audio_channels": self.track_plan.effective_config.audio_format.channels,
                "audio_encoding": (
                    self.track_plan.effective_config.audio_format.encoding.value
                ),
                "output_path": self.track_plan.effective_config.output_path,
                "source_kind": current.source_kind.value,
                "source_section": current.source_section,
                "sequence": self.track_plan.sequence,
                "normalized_body_sha256": current.normalized_body_sha256,
                "declared_word_count": current.declared_word_count,
                "normalized_word_count": current.normalized_word_count,
                "spoken_token_count": current.spoken_token_count,
                "render_identity_schema": current.render_identity_schema,
                "render_context_radius": current.render_context_radius,
            },
        )


def _system_clock() -> datetime:
    return datetime.now(UTC)


def _clock_now(clock: Clock) -> datetime:
    value = clock()
    if not isinstance(value, datetime) or value.tzinfo is None:
        raise InputError("Production worker clock must return an aware datetime")
    return value.astimezone(UTC)


def _parse_utc(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except (TypeError, ValueError) as exc:
        raise InputError(f"{label} must be a UTC timestamp") from exc
    if parsed.tzinfo is None:
        raise InputError(f"{label} must be timezone-aware")
    return parsed.astimezone(UTC)


def _resolve_plan_path(workspace_root: Path, plan_path: Path) -> tuple[str, Path]:
    candidate = plan_path.expanduser()
    if candidate.is_absolute():
        relative = workspace_relative(workspace_root, candidate)
    else:
        relative = candidate.as_posix()
    return relative, resolve_inside(workspace_root, relative)


def _load_current_config(
    workspace_root: Path,
    plan: FrozenBatchPlan,
) -> tuple[Path, BookProductionConfig]:
    config_path = resolve_inside(workspace_root, plan.config_path)
    raw = read_bytes_nofollow(config_path)
    if sha256_bytes(raw) != plan.config_sha256:
        raise InputError("Production configuration differs from the frozen plan")
    config = parse_production_toml(raw, label=str(config_path))
    if config.book_id != plan.book_id:
        raise InputError("Production configuration book identity differs from the frozen plan")
    return config_path, config


def _selected_catalog_track(
    config: BookProductionConfig,
    track_plan: FrozenTrackPlan,
) -> CatalogTrack:
    """Resolve only the selected Track so unrelated publishing sources are not read."""

    matches = tuple(item for item in config.tracks if item.id == track_plan.track_id)
    kind = track_plan.effective_config.track_kind
    if kind is TrackKind.CHAPTER:
        chapter_match = _CHAPTER_TRACK_ID.fullmatch(track_plan.track_id)
        if chapter_match is None:
            raise InputError("Frozen Chapter Track has a noncanonical ID")
        if len(matches) > 1:  # pragma: no cover - strict config rejects duplicates
            raise InputError("Production configuration contains duplicate Track declarations")
        declaration = (
            matches[0]
            if matches
            else TrackDeclaration(
                id=track_plan.track_id,
                kind=TrackKind.CHAPTER,
                sequence=track_plan.sequence,
                source_path=track_plan.source.source_path,
                source_section=None,
                approved_sha256=None,
                render_once=False,
                enabled=True,
                approval_status=SourceApprovalStatus.NOT_REQUIRED,
            )
        )
        if track_plan.source.source_kind is not SourceKind.CHAPTER:
            raise InputError("Frozen Chapter Track source kind is inconsistent")
    else:
        if len(matches) != 1:
            raise InputError(
                f"Approved Special Track {track_plan.track_id!r} is not uniquely configured"
            )
        declaration = matches[0]
        if track_plan.source.source_kind is not SourceKind.APPROVED_SPECIAL_TRACK:
            raise InputError("Frozen Special Track source kind is inconsistent")

    _validate_track_semantics(declaration)
    if (
        declaration.kind is not kind
        or declaration.sequence != track_plan.sequence
        or declaration.source_path != track_plan.source.source_path
        or declaration.source_section != track_plan.source.source_section
    ):
        raise InputError("Current Track declaration differs from the frozen Track plan")
    effective = resolve_effective_track_config(config, declaration)
    if effective != track_plan.effective_config:
        raise InputError("Current effective Track configuration differs from the frozen plan")
    return CatalogTrack(
        id=declaration.id,
        kind=declaration.kind,
        sequence=declaration.sequence,
        source_path=declaration.source_path,
        source_section=declaration.source_section,
        approved_sha256=declaration.approved_sha256,
        verified_source_sha256=(
            None
            if declaration.kind is TrackKind.CHAPTER
            else track_plan.source.raw_sha256
        ),
        render_once=declaration.render_once,
        enabled=declaration.enabled,
        approval_status=declaration.approval_status,
        effective_config=effective,
    )


def _load_narration_runtime(
    workspace_root: Path,
    track_plan: FrozenTrackPlan,
) -> tuple[Path, _ProductionNarrationConfig]:
    runtime_config_path = resolve_inside(workspace_root, _AUDITION_RUNTIME_CONFIG)
    base = load_audition_config(runtime_config_path, workspace_root)
    effective = track_plan.effective_config
    audio = effective.audio_format
    if audio.encoding is not AudioEncoding.PCM_S16LE:
        raise InputError("Production narration requires signed 16-bit little-endian PCM")
    if audio.sample_size_bits != 16 or audio.channels != 1:
        raise InputError("Existing narration assembly requires signed 16-bit mono PCM")
    if effective.normalization != base.normalization:
        raise InputError("Production normalization differs from the verified runtime")
    settings = replace(
        base.nova,
        model_id=effective.model_id,
        region=effective.region,
        sample_rate_hz=audio.sample_rate_hz,
        sample_size_bits=audio.sample_size_bits,
        channels=audio.channels,
    )
    return runtime_config_path, _ProductionNarrationConfig(
        workspace_root=workspace_root,
        nova=settings,
        normalization=effective.normalization,
    )


def _runtime_fingerprint(runtime_config_path: Path) -> str:
    package_root = Path(__file__).resolve().parent
    try:
        module_paths = tuple(
            sorted(
                (
                    path
                    for path in package_root.iterdir()
                    if path.suffix == ".py"
                ),
                key=lambda path: path.name,
            )
        )
    except OSError as exc:
        raise InputError("Production runtime files cannot be enumerated") from exc
    paths = (*module_paths, runtime_config_path)
    observations: list[tuple[str, str]] = []
    for path in paths:
        if path.is_symlink() or not path.is_file():
            raise InputError(f"Production runtime path is missing or unsafe: {path}")
        observations.append((str(path), sha256_bytes(read_bytes_nofollow(path))))
    return canonical_sha256(tuple(observations))


def _authorization_consumption(
    store: TransactionStore,
    plan: FrozenBatchPlan,
    track_plan: FrozenTrackPlan,
) -> tuple[str, int, str]:
    snapshot = store.inspect_transaction(track_plan.track_id, track_plan.transaction_id)
    if not snapshot.metadata.matches(TransactionSpec.from_plan(plan, track_plan)):
        raise InputError("Track transaction identity differs from the frozen plan")
    if snapshot.state is not TransactionState.RUNNING:
        raise InputError("Production worker requires one durably consumed running transaction")
    consumed = tuple(
        payload
        for payload in snapshot.payloads
        if payload.event_type == "authorization-consumed"
    )
    if len(consumed) != 1 or consumed[0] is not snapshot.payloads[-1]:
        raise InputError("Running transaction lacks one exact authorization-consumption head")
    details = consumed[0].details
    authorization_sha256 = details.get("authorization_sha256")
    maximum_new_calls = details.get("maximum_new_calls")
    if not isinstance(authorization_sha256, str) or not _SHA256.fullmatch(
        authorization_sha256
    ):
        raise InputError("Consumed authorization digest is malformed")
    if (
        details.get("command_sha256") != track_plan.command_sha256
        or details.get("one_shot") is not True
        or details.get("automatic_retry_performed") is not False
        or type(maximum_new_calls) is not int
        or maximum_new_calls < 0
        or maximum_new_calls > track_plan.maximum_new_calls
    ):
        raise InputError("Consumed authorization scope differs from the frozen Track")
    required = tuple(
        payload
        for payload in snapshot.payloads
        if payload.event_type == "authorization-required"
    )
    if len(required) != 1:
        raise InputError("Track transaction lacks one authorization-required binding")
    preflight_sha256 = required[0].details.get("preflight_sha256")
    if not isinstance(preflight_sha256, str) or not _SHA256.fullmatch(preflight_sha256):
        raise InputError("Track transaction preflight binding is malformed")
    return authorization_sha256, maximum_new_calls, preflight_sha256


def _load_authorization_artifact(
    plan_path: Path,
    expected_sha256: str,
) -> PaidAuthorization:
    authorization_root = plan_path.parent / "authorizations"
    if (
        authorization_root.is_symlink()
        or not authorization_root.is_dir()
    ):
        raise InputError("Consumed authorization artifact directory is missing or unsafe")
    matches: list[Path] = []
    try:
        entries = tuple(authorization_root.iterdir())
    except OSError as exc:
        raise InputError("Consumed authorization artifacts cannot be inspected") from exc
    for path in entries:
        if path.suffix != ".json" or path.is_symlink() or not path.is_file():
            continue
        raw = read_bytes_nofollow(path)
        if sha256_bytes(raw) == expected_sha256:
            matches.append(path)
    if len(matches) != 1:
        raise InputError("Consumed authorization artifact is missing or ambiguous")
    authorization = StrictRecordCodec(PaidAuthorization).load(matches[0])
    if StrictRecordCodec(PaidAuthorization).sha256(authorization) != expected_sha256:
        raise InputError("Consumed authorization artifact digest is inconsistent")
    return authorization


def _validate_authorization(
    authorization: PaidAuthorization,
    expected_sha256: str,
    maximum_new_calls: int,
    preflight_sha256: str,
    plan: FrozenBatchPlan,
    track_plan: FrozenTrackPlan,
    now: datetime,
) -> None:
    codec = StrictRecordCodec(PaidAuthorization)
    if codec.sha256(authorization) != expected_sha256:
        raise InputError("Paid authorization changed after durable consumption")
    if authorization.plan_sha256 != StrictRecordCodec(FrozenBatchPlan).sha256(plan):
        raise InputError("Paid authorization is not bound to the current frozen plan")
    if authorization.preflight_sha256 != preflight_sha256:
        raise InputError("Paid authorization preflight differs from transaction truth")
    if authorization.exact_transaction_ids != tuple(
        item.transaction_id for item in plan.tracks
    ):
        raise InputError("Paid authorization transaction scope differs from the plan")
    if authorization.exact_track_ids != tuple(item.track_id for item in plan.tracks):
        raise InputError("Paid authorization Track scope differs from the plan")
    if authorization.exact_command_sha256s != tuple(
        item.command_sha256 for item in plan.tracks
    ):
        raise InputError("Paid authorization command scope differs from the plan")
    if (
        authorization.maximum_new_calls_by_track[track_plan.track_id]
        != maximum_new_calls
    ):
        raise InputError("Paid authorization call ceiling differs from consumed scope")
    issued = _parse_utc(authorization.issued_at_utc, "authorization issue time")
    expires = _parse_utc(authorization.expires_at_utc, "authorization expiration")
    if now < issued or now >= expires:
        raise InputError("Paid authorization is not currently valid for another model call")
    if not authorization.one_shot:
        raise InputError("Paid authorization must remain one-shot")


def _validate_runtime_progress(
    manifest_path: Path,
    track_plan: FrozenTrackPlan,
    calls_made: int,
) -> None:
    if not os.path.lexists(manifest_path):
        if calls_made:
            raise InputError("Runtime progress is missing after a completed model call")
        return
    manifest = read_json(manifest_path)
    if not isinstance(manifest, dict):
        raise InputError("Runtime progress manifest is malformed")
    if (
        manifest.get("track_id") != track_plan.track_id
        or manifest.get("spoken_sha256") != track_plan.source.spoken_sha256
    ):
        raise InputError("Runtime progress source binding differs from the frozen Track")
    recorded_calls = manifest.get("billable_calls_made", 0)
    if type(recorded_calls) is not int or recorded_calls != calls_made:
        raise InputError("Runtime progress call count differs from in-process truth")
    entries = manifest.get("segments", [])
    if not isinstance(entries, list) or not all(isinstance(item, dict) for item in entries):
        raise InputError("Runtime progress segment set is malformed")
    ids = tuple(item.get("segment_id") for item in entries)
    frozen_ids = {item.segment_id for item in track_plan.source.segments}
    if len(ids) != len(set(ids)) or any(item not in frozen_ids for item in ids):
        raise InputError("Runtime progress segment identities differ from the frozen Track")
    current_calls = sum(
        item.get("rendered_in_current_attempt") is True for item in entries
    )
    if current_calls != calls_made:
        raise InputError("Runtime progress does not account for every current model call")


@dataclass(frozen=True, slots=True)
class _WorkerGuard:
    workspace_root: Path
    plan_path: Path
    plan: FrozenBatchPlan
    track_plan: FrozenTrackPlan
    catalog_track: CatalogTrack
    source: _FrozenProductionTrackSource
    store: TransactionStore
    runtime_config_path: Path
    runtime_sha256: str
    authorization_sha256: str
    maximum_new_calls: int
    preflight_sha256: str
    clock: Clock

    def _revalidate_common(self) -> PaidAuthorization:
        if load_production_plan(self.plan_path) != self.plan:
            raise InputError("Frozen plan changed during production execution")
        _config_path, current_config = _load_current_config(
            self.workspace_root,
            self.plan,
        )
        if _selected_catalog_track(current_config, self.track_plan) != self.catalog_track:
            raise InputError("Effective production configuration changed during execution")
        self.source.read()
        if _runtime_fingerprint(self.runtime_config_path) != self.runtime_sha256:
            raise InputError("Protected production runtime changed during execution")
        authorization_sha256, maximum_new_calls, preflight_sha256 = (
            _authorization_consumption(self.store, self.plan, self.track_plan)
        )
        if (
            authorization_sha256 != self.authorization_sha256
            or maximum_new_calls != self.maximum_new_calls
            or preflight_sha256 != self.preflight_sha256
        ):
            raise InputError("Authorization consumption changed during execution")
        authorization = _load_authorization_artifact(
            self.plan_path,
            self.authorization_sha256,
        )
        _validate_authorization(
            authorization,
            self.authorization_sha256,
            self.maximum_new_calls,
            self.preflight_sha256,
            self.plan,
            self.track_plan,
            _clock_now(self.clock),
        )
        if os.environ.get("AWS_PROFILE") != self.track_plan.effective_config.profile_label:
            raise InputError("Production worker profile differs from frozen configuration")
        return authorization

    def before_model_call(
        self,
        _segment: Segment,
        identity: NarrationSegmentIdentity,
        calls_made: int,
        manifest_path: Path,
    ) -> None:
        """Revalidate every paid boundary immediately before ``render_text``."""

        self._revalidate_common()
        if identity.segment_id not in {
            item.segment_id for item in self.track_plan.source.segments
        }:
            raise InputError("Possible model call is not for a frozen segment")
        _validate_runtime_progress(manifest_path, self.track_plan, calls_made)
        if calls_made >= self.maximum_new_calls:
            raise InputError("Possible model call exceeds the consumed authorization ceiling")

    def before_assembly(self) -> None:
        """Require current source/config/runtime truth immediately before assembly."""

        if load_production_plan(self.plan_path) != self.plan:
            raise InputError("Frozen plan changed before Track assembly")
        _config_path, current_config = _load_current_config(
            self.workspace_root,
            self.plan,
        )
        if _selected_catalog_track(current_config, self.track_plan) != self.catalog_track:
            raise InputError("Effective production configuration changed before assembly")
        self.source.read()
        if _runtime_fingerprint(self.runtime_config_path) != self.runtime_sha256:
            raise InputError("Protected production runtime changed before assembly")


def run_production_worker(
    workspace_root: Path,
    plan_path: Path,
    transaction_id: str,
    track_id: str,
    *,
    clock: Clock = _system_clock,
) -> int:
    """Execute one exact frozen Track through the hidden direct-child boundary."""

    root = workspace_root.expanduser().resolve()
    relative_plan, absolute_plan = _resolve_plan_path(root, plan_path)
    plan = load_production_plan(absolute_plan)
    matches = tuple(
        track
        for track in plan.tracks
        if track.track_id == track_id and track.transaction_id == transaction_id
    )
    if len(matches) != 1:
        raise InputError("Hidden production worker scope is not one exact frozen Track")
    track_plan = matches[0]
    expected_argv = (
        *WORKER_COMMAND,
        "--plan",
        relative_plan,
        "--transaction",
        transaction_id,
        "--track",
        track_id,
    )
    if track_plan.command_argv != expected_argv:
        raise InputError("Hidden production worker argv differs from the frozen command")
    if track_plan.command_sha256 != canonical_sha256(track_plan.command_argv):
        raise InputError("Hidden production worker command hash is inconsistent")
    if os.environ.get("AWS_PROFILE") != track_plan.effective_config.profile_label:
        raise InputError("Hidden production worker profile differs from frozen configuration")

    _config_path, config = _load_current_config(root, plan)
    catalog_track = _selected_catalog_track(config, track_plan)
    source = _FrozenProductionTrackSource(root, config, catalog_track, track_plan)
    source.read()
    runtime_config_path, runtime = _load_narration_runtime(root, track_plan)
    runtime_sha256 = _runtime_fingerprint(runtime_config_path)
    book_root = resolve_inside(
        root,
        (PurePosixPath(config.build_root) / config.book_id).as_posix(),
    )
    store = TransactionStore(book_root, config.book_id)
    transaction_root = store.transaction_path(track_id, transaction_id)
    runtime_root = transaction_root / "runtime"
    from .production_evidence import resolve_private_runtime_path

    runtime_root = resolve_private_runtime_path(
        root,
        transaction_root,
        workspace_relative(root, runtime_root),
    )

    segment_identities = tuple(
        NarrationSegmentIdentity(
            segment.segment_id,
            segment.text_sha256,
            segment.render_identity_sha256,
        )
        for segment in track_plan.source.segments
    )
    assembly_name = PurePosixPath(track_plan.effective_config.output_path).name
    if not assembly_name:
        raise InputError("Frozen Track output path has no assembly filename")

    with store.track_lock(track_id):
        authorization_sha256, maximum_new_calls, preflight_sha256 = (
            _authorization_consumption(store, plan, track_plan)
        )
        authorization = _load_authorization_artifact(
            absolute_plan,
            authorization_sha256,
        )
        _validate_authorization(
            authorization,
            authorization_sha256,
            maximum_new_calls,
            preflight_sha256,
            plan,
            track_plan,
            _clock_now(clock),
        )
        guard = _WorkerGuard(
            workspace_root=root,
            plan_path=absolute_plan,
            plan=plan,
            track_plan=track_plan,
            catalog_track=catalog_track,
            source=source,
            store=store,
            runtime_config_path=runtime_config_path,
            runtime_sha256=runtime_sha256,
            authorization_sha256=authorization_sha256,
            maximum_new_calls=maximum_new_calls,
            preflight_sha256=preflight_sha256,
            clock=clock,
        )
        result = narrate_track(
            runtime,  # type: ignore[arg-type] - structural narration config
            source,
            track_plan.effective_config.voice,
            runtime_root=runtime_root,
            assembly_name=assembly_name,
            paid_render_authorized=True,
            accept_verbatim_prefix=False,
            max_words=track_plan.effective_config.target_segment_words,
            maximum_new_calls=maximum_new_calls,
            segment_identities=segment_identities,
            require_event_replay=True,
            assembly_manifest_prefix="track",
            before_model_call=guard.before_model_call,
            before_assembly=guard.before_assembly,
        )

    if result["billable_calls_made"] > maximum_new_calls:
        raise InputError("Production worker exceeded its consumed call ceiling")
    print(
        json.dumps(
            {
                "event": "production-track-complete",
                "track_id": track_id,
                "transaction_id": transaction_id,
                "segments_total": result["segments_total"],
                "segments_rendered": result["segments_rendered"],
                "segments_reused": result["segments_reused"],
                "billable_calls_made": result["billable_calls_made"],
                "track_audio_sha256": result["track_audio_sha256"],
            },
            sort_keys=True,
            separators=(",", ":"),
        ),
        flush=True,
    )
    return 0


__all__ = ["run_production_worker"]
