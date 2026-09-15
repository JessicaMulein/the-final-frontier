"""Offline production selection, source snapshots, and immutable plan creation.

Planning is intentionally local-only.  It reads strict configuration and selected
sources, reuses the established manuscript/spoken/segmentation algorithms, and
persists only canonical hashes, counts, boundaries, configuration, and finite call
ceilings.  Identity, pricing, model invocation, artifact reuse classification, and
execution belong to later production phases.
"""

from __future__ import annotations

import os
import re
import secrets
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Iterable, Protocol, Sequence

from .errors import InputError
from .manuscript import discover_chapter, markdown_to_spoken, read_chapter
from .narrate import SEGMENT_BOUNDARY_POLICY, Segment, segment_spoken_text
from .production_config import (
    BookProductionConfig,
    CatalogTrack,
    OrderedTrackCatalog,
    SourceApprovalStatus,
    build_ordered_track_catalog,
    parse_production_toml,
)
from .production_models import (
    RECORD_SCHEMA_VERSION,
    FrozenBatchPlan,
    FrozenTrackPlan,
    SegmentSnapshot,
    SourceKind,
    SourceSnapshot,
    StrictRecordCodec,
    TrackKind,
    canonical_sha256,
    seal_record,
)
from .util import (
    compact_utc_now,
    durable_mkdir,
    durable_replace,
    find_workspace_root,
    fsync_directory,
    normalize_lf_nfc,
    read_bytes_nofollow,
    resolve_inside,
    sha256_bytes,
    sha256_text,
    utc_now,
    workspace_relative,
)
from .verify import normalized_tokens

RENDER_CONFIG_SCHEMA = "frontier-render-config-v1"
RENDER_IDENTITY_SCHEMA = "frontier-render-identity-v1"
RENDER_CONTEXT_POLICY = "bounded-neighbor-v1"
RENDER_CONTEXT_RADIUS = 1
PLAN_PROTECTED_BINDING_SCHEMA = "frontier-plan-protected-binding-v1"
TRANSACTION_ID_SCHEMA = "frontier-track-transaction-id-v1"
WORKER_COMMAND = ("frontier-audiobook", "_production-worker")

_IDENTIFIER = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_CHAPTER_SELECTOR = re.compile(r"^chapter:(\d+)$")
_CHAPTER_RANGE_SELECTOR = re.compile(r"^chapter-range:(\d+):(\d+)$")
_TRACK_SELECTOR = re.compile(r"^track:([a-z0-9]+(?:-[a-z0-9]+)*)$")
_CHAPTER_TRACK_ID = re.compile(r"^chapter-(\d+)$")
_MARKDOWN_HEADING = re.compile(
    r"(?m)^(?P<marks>#{1,6})[ \t]+(?P<title>.*?)[ \t]*#*[ \t]*$"
)


@dataclass(frozen=True, slots=True)
class ProductionSelectors:
    """Canonical selector tokens assembled from repeatable CLI option values."""

    tokens: tuple[str, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.tokens, tuple):
            raise InputError("Production selectors must be a tuple")
        for index, token in enumerate(self.tokens):
            if not isinstance(token, str) or not token or token != token.strip():
                raise InputError(f"Production selector {index} must be a nonblank canonical string")

    @classmethod
    def from_cli(
        cls,
        *,
        chapters: Iterable[int] | None = None,
        chapter_ranges: Iterable[str] | None = None,
        tracks: Iterable[str] | None = None,
    ) -> ProductionSelectors:
        """Convert repeatable ``--chapter``, ``--chapter-range``, and ``--track`` values."""

        tokens: list[str] = []
        for chapter in chapters or ():
            if type(chapter) is not int or chapter < 1:
                raise InputError("--chapter values must be positive integers")
            tokens.append(f"chapter:{chapter}")
        for chapter_range in chapter_ranges or ():
            if not isinstance(chapter_range, str):
                raise InputError("--chapter-range values must use START:END")
            tokens.append(f"chapter-range:{chapter_range}")
        for track_id in tracks or ():
            if not isinstance(track_id, str):
                raise InputError("--track values must be Track IDs")
            tokens.append(f"track:{track_id}")
        return cls(tuple(tokens))


@dataclass(frozen=True, slots=True)
class ResolvedProductionScope:
    selectors: tuple[str, ...]
    tracks: tuple[CatalogTrack, ...]


@dataclass(frozen=True, slots=True)
class _PreparedSource:
    """Selected source text held in memory only while a prose-free snapshot is built."""

    source_path: str
    source_section: str | None
    source_kind: SourceKind
    raw_bytes: bytes
    normalized_body: str
    spoken: str
    declared_word_count: int | None


class TrackSourceAdapter(Protocol):
    """Read one catalog Track into an in-memory source suitable for snapshotting."""

    def read(
        self,
        config: BookProductionConfig,
        track: CatalogTrack,
        workspace_root: Path,
    ) -> _PreparedSource: ...


class ChapterSourceAdapter:
    """Adapter over the existing restricted chapter parser and spoken transform."""

    def read(
        self,
        config: BookProductionConfig,
        track: CatalogTrack,
        workspace_root: Path,
    ) -> _PreparedSource:
        if track.kind is not TrackKind.CHAPTER:
            raise InputError("ChapterSourceAdapter requires a Chapter Track")
        match = _CHAPTER_TRACK_ID.fullmatch(track.id)
        if match is None:
            raise InputError(f"Chapter Track has a noncanonical ID: {track.id!r}")
        chapter_number = int(match.group(1))
        manuscript_root = resolve_inside(workspace_root, config.manuscript_root)
        discovered = discover_chapter(manuscript_root, chapter_number)
        configured = resolve_inside(workspace_root, track.source_path)
        if discovered.resolve() != configured:
            raise InputError(
                f"Chapter Track {track.id!r} no longer resolves to its catalog source"
            )

        before = read_bytes_nofollow(configured)
        source = read_chapter(configured, enforce_declared_words=False)
        after = read_bytes_nofollow(configured)
        if before != after:
            raise InputError(f"Chapter source changed while planning {track.id!r}")
        if source.chapter != chapter_number:
            raise InputError(f"Chapter source identity changed while planning {track.id!r}")
        spoken, _applied = config.pronunciations.apply(
            markdown_to_spoken(source.body, track.id)
        )
        return _PreparedSource(
            source_path=track.source_path,
            source_section=None,
            source_kind=SourceKind.CHAPTER,
            raw_bytes=before,
            normalized_body=source.body,
            spoken=spoken,
            declared_word_count=None,
        )


class ApprovedSpecialTrackSourceAdapter:
    """Adapter for an enabled, approved, Render_Once publishing handoff."""

    def read(
        self,
        config: BookProductionConfig,
        track: CatalogTrack,
        workspace_root: Path,
    ) -> _PreparedSource:
        if track.kind is TrackKind.CHAPTER:
            raise InputError("ApprovedSpecialTrackSourceAdapter requires a Special Track")
        if not track.enabled or track.approval_status is not SourceApprovalStatus.APPROVED:
            raise InputError(f"Special Track {track.id!r} does not have an approved source")
        if not track.render_once:
            raise InputError(f"Special Track {track.id!r} must remain Render_Once")

        source_path = resolve_inside(workspace_root, track.source_path)
        before = read_bytes_nofollow(source_path)
        raw_sha256 = sha256_bytes(before)
        if track.verified_source_sha256 != raw_sha256:
            raise InputError(f"Approved source changed while planning {track.id!r}")
        if track.approved_sha256 is not None and track.approved_sha256 != raw_sha256:
            raise InputError(f"Approved source hash mismatch while planning {track.id!r}")
        try:
            decoded = before.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InputError(
                f"Cannot decode approved source as strict UTF-8, {source_path}: {exc}"
            ) from exc
        normalized = normalize_lf_nfc(decoded)
        selected = (
            normalized
            if track.source_section is None
            else _extract_named_markdown_section(normalized, track.source_section, track.id)
        )
        spoken, _applied = config.pronunciations.apply(
            markdown_to_spoken(selected, track.id)
        )
        after = read_bytes_nofollow(source_path)
        if before != after:
            raise InputError(f"Approved source changed while planning {track.id!r}")
        return _PreparedSource(
            source_path=track.source_path,
            source_section=track.source_section,
            source_kind=SourceKind.APPROVED_SPECIAL_TRACK,
            raw_bytes=before,
            normalized_body=selected,
            spoken=spoken,
            declared_word_count=None,
        )


def _section_slug(value: str) -> str:
    plain = re.sub(r"[*_`]", "", normalize_lf_nfc(value).casefold())
    return re.sub(r"[^a-z0-9]+", "-", plain).strip("-")


def _extract_named_markdown_section(text: str, section: str, track_id: str) -> str:
    headings = tuple(_MARKDOWN_HEADING.finditer(text))
    matches = tuple(item for item in headings if _section_slug(item.group("title")) == section)
    if len(matches) != 1:
        raise InputError(
            f"Approved source section {section!r} for {track_id!r} must match exactly one heading; "
            f"found {len(matches)}"
        )
    selected_heading = matches[0]
    following = next((item for item in headings if item.start() > selected_heading.start()), None)
    end = len(text) if following is None else following.start()
    selected = text[selected_heading.end() : end].strip()
    if not selected:
        raise InputError(f"Approved source section {section!r} for {track_id!r} is empty")
    return selected


def _coerce_selectors(
    selectors: ProductionSelectors | Sequence[str],
) -> ProductionSelectors:
    if isinstance(selectors, ProductionSelectors):
        return selectors
    if isinstance(selectors, (str, bytes)) or not isinstance(selectors, Sequence):
        raise InputError("Production selectors must be a finite sequence")
    return ProductionSelectors(tuple(selectors))


def resolve_production_selectors(
    catalog: OrderedTrackCatalog,
    selectors: ProductionSelectors | Sequence[str],
) -> ResolvedProductionScope:
    """Resolve an exact finite selector scope into immutable catalog order."""

    if not isinstance(catalog, OrderedTrackCatalog):
        raise InputError("resolve_production_selectors requires an OrderedTrackCatalog")
    selector_set = _coerce_selectors(selectors)
    if not selector_set.tokens:
        raise InputError("At least one --chapter, --chapter-range, or --track is required")

    requested_track_ids: list[str] = []
    normalized_selectors: list[str] = []
    seen_track_ids: set[str] = set()

    def add(track_id: str, selector: str) -> None:
        if track_id in seen_track_ids:
            raise InputError(f"Selector scope contains duplicate Track {track_id!r}")
        seen_track_ids.add(track_id)
        requested_track_ids.append(track_id)
        if len(requested_track_ids) > catalog.max_tracks_per_plan:
            raise InputError(
                "Selector scope exceeds max_tracks_per_plan="
                f"{catalog.max_tracks_per_plan}"
            )
        if selector not in normalized_selectors:
            normalized_selectors.append(selector)

    for token in selector_set.tokens:
        chapter_match = _CHAPTER_SELECTOR.fullmatch(token)
        if chapter_match is not None:
            chapter = int(chapter_match.group(1))
            if chapter < 1:
                raise InputError("--chapter values must be positive integers")
            normalized = f"chapter:{chapter}"
            add(f"chapter-{chapter:03d}", normalized)
            continue

        range_match = _CHAPTER_RANGE_SELECTOR.fullmatch(token)
        if range_match is not None:
            start, end = (int(range_match.group(1)), int(range_match.group(2)))
            if start < 1 or end < 1:
                raise InputError("--chapter-range bounds must be positive integers")
            if start > end:
                raise InputError("--chapter-range must be inclusive and not reversed")
            range_size = end - start + 1
            if range_size > catalog.max_tracks_per_plan:
                raise InputError(
                    "Selector scope exceeds max_tracks_per_plan="
                    f"{catalog.max_tracks_per_plan}"
                )
            normalized = f"chapter-range:{start}:{end}"
            for chapter in range(start, end + 1):
                add(f"chapter-{chapter:03d}", normalized)
            continue

        track_match = _TRACK_SELECTOR.fullmatch(token)
        if track_match is not None:
            track_id = track_match.group(1)
            add(track_id, f"track:{track_id}")
            continue

        if token.startswith("chapter-range:"):
            raise InputError("--chapter-range values must use positive START:END bounds")
        if token.startswith("chapter:"):
            raise InputError("--chapter values must be positive integers")
        if token.startswith("track:"):
            raise InputError("--track values must be lowercase hyphenated Track IDs")
        raise InputError(f"Unknown production selector {token!r}")

    selected = catalog.select_track_ids(tuple(requested_track_ids))
    return ResolvedProductionScope(tuple(normalized_selectors), selected)


def _canonical_render_text(value: str) -> str:
    return " ".join(normalize_lf_nfc(value).split())


def _render_config_sha256(track: CatalogTrack) -> str:
    effective = track.effective_config
    return canonical_sha256(
        {
            "schema": RENDER_CONFIG_SCHEMA,
            "track_kind": effective.track_kind.value,
            "voice": effective.voice,
            "model_id": effective.model_id,
            "region": effective.region,
            "profile_label": effective.profile_label,
            "target_segment_words": effective.target_segment_words,
            "fidelity_policy": effective.fidelity_policy.value,
            "normalization": effective.normalization,
            "audio": {
                "sample_rate_hz": effective.audio_format.sample_rate_hz,
                "sample_size_bits": effective.audio_format.sample_size_bits,
                "channels": effective.audio_format.channels,
                "encoding": effective.audio_format.encoding.value,
            },
            "segmentation_policy": SEGMENT_BOUNDARY_POLICY,
        }
    )


def _context_sha256(
    segment_components: tuple[dict[str, object], ...],
    start: int,
    end: int,
) -> str | None:
    bounded = segment_components[start:end]
    if not bounded:
        return None
    return canonical_sha256(
        {
            "schema": RENDER_CONTEXT_POLICY,
            "radius": RENDER_CONTEXT_RADIUS,
            "segments": bounded,
        }
    )


def _segment_components(
    segments: tuple[Segment, ...],
    normalization: str,
) -> tuple[dict[str, object], ...]:
    components: list[dict[str, object]] = []
    for segment in segments:
        tokens = normalized_tokens(segment.text, normalization)
        if not tokens:
            raise InputError(f"Narration segment {segment.segment_id} has no normalized tokens")
        canonical_text = _canonical_render_text(segment.text)
        components.append(
            {
                "text_sha256": sha256_text(canonical_text),
                "normalized_tokens_sha256": canonical_sha256(tokens),
                "spoken_token_count": len(tokens),
                "narration_only_punctuation": segment.narration_only_punctuation,
            }
        )
    return tuple(components)


def _build_source_snapshot(track: CatalogTrack, prepared: _PreparedSource) -> SourceSnapshot:
    effective = track.effective_config
    spoken_tokens = normalized_tokens(prepared.spoken, effective.normalization)
    if not spoken_tokens:
        raise InputError(f"Track {track.id!r} has no normalized spoken tokens")
    segments = segment_spoken_text(
        prepared.spoken,
        max_words=effective.target_segment_words,
    )
    reproduced = tuple(
        token
        for segment in segments
        for token in normalized_tokens(segment.text, effective.normalization)
    )
    if reproduced != spoken_tokens:
        raise InputError(f"Segmentation changed the spoken token sequence for {track.id!r}")

    render_config_sha256 = _render_config_sha256(track)
    components = _segment_components(segments, effective.normalization)
    snapshots: list[SegmentSnapshot] = []
    token_cursor = 0
    for index, (segment, component) in enumerate(zip(segments, components, strict=True)):
        context_before = _context_sha256(
            components,
            max(0, index - RENDER_CONTEXT_RADIUS),
            index,
        )
        context_after = _context_sha256(
            components,
            index + 1,
            min(len(components), index + 1 + RENDER_CONTEXT_RADIUS),
        )
        token_count = int(component["spoken_token_count"])
        render_identity_sha256 = canonical_sha256(
            {
                "schema": RENDER_IDENTITY_SCHEMA,
                "segmentation_policy": SEGMENT_BOUNDARY_POLICY,
                "normalization": effective.normalization,
                "context_policy": RENDER_CONTEXT_POLICY,
                "context_radius": RENDER_CONTEXT_RADIUS,
                "text_sha256": component["text_sha256"],
                "normalized_tokens_sha256": component["normalized_tokens_sha256"],
                "spoken_token_count": token_count,
                "narration_only_punctuation": component["narration_only_punctuation"],
                "context_before_sha256": context_before,
                "context_after_sha256": context_after,
                "render_config_sha256": render_config_sha256,
            }
        )
        snapshots.append(
            SegmentSnapshot(
                segment_id=f"segment-{index + 1:04d}",
                ordinal=index + 1,
                paragraph_index=segment.paragraph_index,
                start_token_index=token_cursor,
                end_token_index=token_cursor + token_count,
                text_sha256=str(component["text_sha256"]),
                normalized_tokens_sha256=str(component["normalized_tokens_sha256"]),
                context_before_sha256=context_before,
                context_after_sha256=context_after,
                render_config_sha256=render_config_sha256,
                render_identity_sha256=render_identity_sha256,
                spoken_token_count=token_count,
                narration_only_punctuation=segment.narration_only_punctuation,
            )
        )
        token_cursor += token_count

    return SourceSnapshot(
        track_id=track.id,
        source_path=prepared.source_path,
        source_section=prepared.source_section,
        source_kind=prepared.source_kind,
        raw_sha256=sha256_bytes(prepared.raw_bytes),
        normalized_body_sha256=sha256_text(normalize_lf_nfc(prepared.normalized_body)),
        spoken_sha256=sha256_text(normalize_lf_nfc(prepared.spoken)),
        declared_word_count=prepared.declared_word_count,
        normalized_word_count=len(prepared.normalized_body.split()),
        spoken_token_count=len(spoken_tokens),
        segment_count=len(snapshots),
        segmentation_policy=SEGMENT_BOUNDARY_POLICY,
        render_identity_schema=RENDER_IDENTITY_SCHEMA,
        render_context_radius=RENDER_CONTEXT_RADIUS,
        segments=tuple(snapshots),
    )


def snapshot_track_source(
    config: BookProductionConfig,
    track: CatalogTrack,
    workspace_root: Path,
) -> SourceSnapshot:
    """Create one current, prose-free snapshot through the appropriate generic adapter."""

    workspace_root = workspace_root.expanduser().resolve()
    adapter: TrackSourceAdapter
    if track.kind is TrackKind.CHAPTER:
        adapter = ChapterSourceAdapter()
    else:
        adapter = ApprovedSpecialTrackSourceAdapter()
    return _build_source_snapshot(track, adapter.read(config, track, workspace_root))


def _validate_plan_id(value: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise InputError("plan_id must be a lowercase hyphenated identifier")
    return value


def _new_plan_id(plans_root: Path) -> str:
    for _ in range(16):
        candidate = f"plan-{compact_utc_now().lower()}-{secrets.token_hex(4)}"
        if not os.path.lexists(plans_root / candidate):
            return candidate
    raise InputError("Could not allocate a unique production plan ID")


def _transaction_id(plan_id: str, track_id: str) -> str:
    digest = canonical_sha256(
        {"schema": TRANSACTION_ID_SCHEMA, "plan_id": plan_id, "track_id": track_id}
    )
    return f"transaction-{digest[:24]}"


def _worker_argv(plan_path: str, transaction_id: str, track_id: str) -> tuple[str, ...]:
    return (
        *WORKER_COMMAND,
        "--plan",
        plan_path,
        "--transaction",
        transaction_id,
        "--track",
        track_id,
    )


def _existing_plan(path: Path, expected_plan_id: str) -> FrozenBatchPlan:
    if path.parent.is_symlink() or not path.parent.is_dir():
        raise InputError(f"Plan ID collision at non-directory path: {path.parent}")
    if not path.is_file() or path.is_symlink():
        raise InputError(f"Plan ID collision lacks one canonical plan.json: {path.parent}")
    existing = StrictRecordCodec(FrozenBatchPlan).load(path)
    if existing.plan_id != expected_plan_id:
        raise InputError(f"Plan directory identity mismatch at {path.parent}")
    return existing


def _remove_private_staging(staging: Path) -> None:
    """Remove only the staging directory created by this invocation."""

    if not staging.exists() or staging.is_symlink():
        return
    plan_path = staging / "plan.json"
    if plan_path.exists() and not plan_path.is_symlink():
        plan_path.unlink()
    try:
        staging.rmdir()
    except OSError:
        # Retain unexpected residue rather than recursively deleting unknown evidence.
        pass


def _commit_plan_exclusively(path: Path, plan: FrozenBatchPlan) -> None:
    plans_root = path.parent.parent
    durable_mkdir(plans_root)
    staging = plans_root / f".{plan.plan_id}.staging-{secrets.token_hex(8)}"
    try:
        staging.mkdir(mode=0o700)
        StrictRecordCodec(FrozenBatchPlan).write_atomic(staging / "plan.json", plan)
        fsync_directory(staging)
        durable_replace(staging, path.parent, source_kind="directory")
    except BaseException:
        _remove_private_staging(staging)
        raise


def load_production_plan(path: Path) -> FrozenBatchPlan:
    """Load one strictly canonical, digest-valid production plan."""

    return StrictRecordCodec(FrozenBatchPlan).load(path.expanduser().resolve())


def create_production_plan(
    config_path: Path,
    selectors: ProductionSelectors | Sequence[str],
    *,
    plan_id: str | None = None,
    workspace_root: Path | None = None,
    created_at_utc: str | None = None,
) -> Path:
    """Create one immutable prose-free plan without identity, pricing, or model calls.

    Reusing an explicit ``plan_id`` is idempotent only when the newly recomputed
    configuration, sources, segment identities, scope, and canonical bytes match the
    existing plan.  Any drift is a collision and never overwrites prior evidence.
    """

    root = (
        workspace_root.expanduser().resolve()
        if workspace_root is not None
        else find_workspace_root(config_path.expanduser().resolve())
    )
    config_absolute = (
        config_path.expanduser().resolve()
        if config_path.is_absolute()
        else resolve_inside(root, config_path.as_posix())
    )
    config_relative = workspace_relative(root, config_absolute)
    config_bytes = read_bytes_nofollow(config_absolute)
    config = parse_production_toml(config_bytes, label=str(config_absolute))
    catalog = build_ordered_track_catalog(config, root)
    scope = resolve_production_selectors(catalog, selectors)

    plans_root_relative = (
        PurePosixPath(config.build_root) / config.book_id / "plans"
    ).as_posix()
    plans_root = resolve_inside(root, plans_root_relative)
    explicit_plan_id = plan_id is not None
    selected_plan_id = (
        _validate_plan_id(plan_id) if plan_id is not None else _new_plan_id(plans_root)
    )
    plan_relative = (
        PurePosixPath(plans_root_relative) / selected_plan_id / "plan.json"
    ).as_posix()
    plan_path = resolve_inside(root, plan_relative)

    existing: FrozenBatchPlan | None = None
    if os.path.lexists(plan_path.parent):
        if not explicit_plan_id:
            raise InputError(f"Generated production plan ID collided at {plan_path.parent}")
        existing = _existing_plan(plan_path, selected_plan_id)
    plan_created_at = existing.created_at_utc if existing is not None else created_at_utc or utc_now()

    config_sha256 = sha256_bytes(config_bytes)
    track_plans: list[FrozenTrackPlan] = []
    for track in scope.tracks:
        source = snapshot_track_source(config, track, root)
        transaction_id = _transaction_id(selected_plan_id, track.id)
        argv = _worker_argv(plan_relative, transaction_id, track.id)
        protected_binding = canonical_sha256(
            {
                "schema": PLAN_PROTECTED_BINDING_SCHEMA,
                "config_path": config_relative,
                "config_sha256": config_sha256,
                "source_path": source.source_path,
                "source_raw_sha256": source.raw_sha256,
            }
        )
        track_plans.append(
            FrozenTrackPlan(
                transaction_id=transaction_id,
                track_id=track.id,
                sequence=track.sequence,
                effective_config=track.effective_config,
                source=source,
                command_argv=argv,
                command_sha256=canonical_sha256(argv),
                maximum_new_calls=source.segment_count,
                legacy_candidates=(),
                protected_inventory_sha256=protected_binding,
            )
        )

    plan = seal_record(
        FrozenBatchPlan(
            schema_version=RECORD_SCHEMA_VERSION,
            plan_id=selected_plan_id,
            created_at_utc=plan_created_at,
            book_id=config.book_id,
            config_path=config_relative,
            config_sha256=config_sha256,
            selectors=scope.selectors,
            tracks=tuple(track_plans),
            canonical_sha256="",
        )
    )

    # Freeze only a self-consistent view.  A concurrent source/config edit blocks the
    # write rather than creating a plan that was stale at its first durable instant.
    if read_bytes_nofollow(config_absolute) != config_bytes:
        raise InputError("Production configuration changed while planning")
    for track_plan in plan.tracks:
        current = read_bytes_nofollow(resolve_inside(root, track_plan.source.source_path))
        if sha256_bytes(current) != track_plan.source.raw_sha256:
            raise InputError(f"Selected source changed while planning {track_plan.track_id!r}")

    codec = StrictRecordCodec(FrozenBatchPlan)
    if existing is not None:
        if codec.dump_bytes(existing) != codec.dump_bytes(plan):
            raise InputError(
                f"Plan ID collision for {selected_plan_id!r}: existing canonical bytes differ"
            )
        return plan_path

    try:
        _commit_plan_exclusively(plan_path, plan)
    except InputError:
        if explicit_plan_id and os.path.lexists(plan_path.parent):
            raced = _existing_plan(plan_path, selected_plan_id)
            if codec.dump_bytes(raced) == codec.dump_bytes(plan):
                return plan_path
        raise
    return plan_path
