#!/usr/bin/env python3
"""Objective manuscript checker for *The Final Frontier*.

Implemented so far:

* task 3.2 — the Manuscript_Exclusion_Contract reference collector and its
  small reference artifact model;
* task 7.2 — Chapter_File header parsing, Prose_Word counting, Length_Class
  validation, and the four-way filename/directory/header/ArcEntry movement and
  global-sequence agreement rule;
* task 7.3 — typed fenced record parsing for the allowlisted record sources,
  stable-ID indexing with duplicate identity rejected before reference
  resolution, Timeline_ID/POV_ID/Character_ID/VoiceBrief/Motif_Event resolution,
  the closed four-mode `technical_state` invariant table with `CancelState`,
  `PairState`, and `PairingEvidence`, the Requirement 12.5 local agreements, and
  Cross_Cut integrity gated on the requested batch scope.

Motif-ledger rules and literal-phrase scanning (task 7.4), the `--scope
chapter`/`--scope batch` CLI (task 7.5), the text/JSON diagnostic surface (task
7.6), and every whole-manuscript total belong to later specification tasks. The
checker is read-only: it never rewrites counts, metadata, IDs, statuses, or
prose, and it never infers a record value from prose commentary.
"""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

SUPPORTED_CONTRACT_SCHEMA = "manuscript-exclusion-contract/v1"
SUPPORTED_VISIBILITY_SCHEMA = "reference-song-visibility/v1"
DEFAULT_MANUSCRIPT_ROOT = "The Final Frontier Novel"
DEFAULT_CONTRACT_PATH = PurePosixPath(
    DEFAULT_MANUSCRIPT_ROOT, "exclusion-contract.json"
)
EXTERNAL_ADOPTION_LIMIT = (
    "Passing this local reference check does not prove that the external "
    "Site_Build has adopted the Manuscript_Exclusion_Contract."
)


class SiteExclusionError(RuntimeError):
    """A deterministic, fail-closed site-exclusion failure."""

    def __init__(
        self,
        code: str,
        *,
        path: Path,
        observed: str,
        expected: str,
        exit_status: int = 2,
    ) -> None:
        self.code = code
        self.path = path
        self.observed = observed
        self.expected = expected
        self.exit_status = exit_status
        super().__init__(
            f"{code} path={path} observed={observed!r} expected={expected!r}"
        )


@dataclass(frozen=True)
class ExcludedRoot:
    """One validated exclusion resolved from the contract."""

    exclusion_id: str
    relative_path: str
    resolved_path: Path


@dataclass(frozen=True)
class LoadedContract:
    """The validated contract and its resolved exclusion roots."""

    workspace_root: Path
    contract_path: Path
    raw: Mapping[str, Any]
    excluded_roots: Tuple[ExcludedRoot, ...]


@dataclass(frozen=True)
class MarkdownSource:
    """An eligible Markdown source found after exclusion filtering."""

    relative_path: str
    resolved_path: Path


@dataclass(frozen=True)
class VisibilityRow:
    """A reference visibility row used by the synthetic site fixture."""

    source: str
    visible: bool
    title: Optional[str] = None
    slug: Optional[str] = None


@dataclass(frozen=True)
class VisibilityPlan:
    """A minimal reference visibility plan, not an external build format."""

    default_visible: bool
    rows: Mapping[str, VisibilityRow]


@dataclass(frozen=True)
class Song:
    """A song admitted by discovery and then by reference visibility rules."""

    source_path: str
    title: str
    slug: str


@dataclass(frozen=True)
class GeneratedArtifact:
    """An in-memory reference artifact carrying explicit source provenance."""

    kind: str
    output_path: str
    source_paths: Tuple[str, ...]
    content: str


@dataclass(frozen=True)
class SiteExclusionResult:
    """Result of one complete local reference-collector run."""

    contract: LoadedContract
    scanned_direct_children: Tuple[str, ...]
    sources: Tuple[MarkdownSource, ...]
    songs: Tuple[Song, ...]
    artifacts: Tuple[GeneratedArtifact, ...]
    external_adoption_verified: bool = False


def _normalized_text(value: str) -> str:
    return unicodedata.normalize("NFC", value)


def _path_is_at_or_below(path: Path, root: Path) -> bool:
    return path == root or root in path.parents


def _relative_posix(path: Path, workspace_root: Path) -> str:
    try:
        return path.relative_to(workspace_root).as_posix()
    except ValueError as exc:
        raise SiteExclusionError(
            "SOURCE_OUTSIDE_WORKSPACE",
            path=path,
            observed=str(path),
            expected=f"a resolved path at or below {workspace_root}",
        ) from exc


def _require_mapping(
    value: Any, *, code: str, path: Path, field: str
) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise SiteExclusionError(
            code,
            path=path,
            observed=f"{field} has type {type(value).__name__}",
            expected=f"{field} to be an object",
        )
    return value


def _safe_relative_parts(
    value: Any,
    *,
    code: str,
    path: Path,
    field: str,
    direct_child: bool,
) -> Tuple[str, ...]:
    if not isinstance(value, str) or not value.strip():
        raise SiteExclusionError(
            code,
            path=path,
            observed=f"{field} is missing or blank",
            expected="a nonblank workspace-relative POSIX path",
        )

    normalized = _normalized_text(value.strip().replace("\\", "/"))
    pure_path = PurePosixPath(normalized)
    parts = pure_path.parts
    invalid = (
        pure_path.is_absolute()
        or not parts
        or any(part in {"", ".", ".."} for part in parts)
        or (direct_child and len(parts) != 1)
    )
    if invalid:
        expected = (
            "one direct workspace-child name"
            if direct_child
            else "a workspace-relative path without traversal"
        )
        raise SiteExclusionError(
            code,
            path=path,
            observed=normalized,
            expected=expected,
        )
    return tuple(parts)


def _resolve_existing(path: Path, *, code: str, expected: str) -> Path:
    try:
        return path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise SiteExclusionError(
            code,
            path=path,
            observed="missing, unreadable, or unresolvable",
            expected=expected,
        ) from exc


def load_exclusion_contract(
    workspace_root: Path | str,
    contract_path: Path | str | None = None,
) -> LoadedContract:
    """Load and validate the exclusion contract, failing closed on drift."""

    workspace_input = Path(workspace_root)
    workspace = _resolve_existing(
        workspace_input,
        code="WORKSPACE_MISSING",
        expected="an existing readable workspace directory",
    )
    if not workspace.is_dir():
        raise SiteExclusionError(
            "WORKSPACE_MALFORMED",
            path=workspace,
            observed="not a directory",
            expected="a workspace directory",
        )

    if contract_path is None:
        contract_input = workspace.joinpath(*DEFAULT_CONTRACT_PATH.parts)
    else:
        contract_input = Path(contract_path)
        if not contract_input.is_absolute():
            contract_input = workspace / contract_input

    if not contract_input.exists():
        raise SiteExclusionError(
            "CONTRACT_MISSING",
            path=contract_input,
            observed="file does not exist",
            expected="the committed Manuscript_Exclusion_Contract",
        )
    if not contract_input.is_file():
        raise SiteExclusionError(
            "CONTRACT_MALFORMED",
            path=contract_input,
            observed="contract path is not a file",
            expected="a readable JSON file",
        )

    try:
        raw_text = contract_input.read_text(encoding="utf-8")
    except OSError as exc:
        raise SiteExclusionError(
            "CONTRACT_UNREADABLE",
            path=contract_input,
            observed=str(exc),
            expected="readable UTF-8 JSON",
        ) from exc

    try:
        parsed = json.loads(raw_text)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise SiteExclusionError(
            "CONTRACT_MALFORMED",
            path=contract_input,
            observed=f"invalid JSON: {exc}",
            expected="valid JSON matching manuscript-exclusion-contract/v1",
        ) from exc

    document = _require_mapping(
        parsed,
        code="CONTRACT_MALFORMED",
        path=contract_input,
        field="contract document",
    )

    if document.get("schema") != SUPPORTED_CONTRACT_SCHEMA:
        raise SiteExclusionError(
            "CONTRACT_UNSUPPORTED_SCHEMA",
            path=contract_input,
            observed=str(document.get("schema")),
            expected=SUPPORTED_CONTRACT_SCHEMA,
        )
    if document.get("contract") != "Manuscript_Exclusion_Contract":
        raise SiteExclusionError(
            "CONTRACT_MALFORMED",
            path=contract_input,
            observed=str(document.get("contract")),
            expected="Manuscript_Exclusion_Contract",
        )

    declared_parts = _safe_relative_parts(
        document.get("declared_at"),
        code="CONTRACT_MALFORMED",
        path=contract_input,
        field="declared_at",
        direct_child=False,
    )
    actual_contract = _resolve_existing(
        contract_input,
        code="CONTRACT_UNREADABLE",
        expected="a resolvable contract file",
    )
    declared_contract = _resolve_existing(
        workspace.joinpath(*declared_parts),
        code="CONTRACT_STALE",
        expected="declared_at to resolve to this contract file",
    )
    if actual_contract != declared_contract:
        raise SiteExclusionError(
            "CONTRACT_STALE",
            path=actual_contract,
            observed=f"declared_at resolves to {declared_contract}",
            expected="declared_at to resolve to the loaded contract",
        )

    exclusions = document.get("exclusions")
    if not isinstance(exclusions, list) or not exclusions:
        raise SiteExclusionError(
            "CONTRACT_MALFORMED",
            path=actual_contract,
            observed="exclusions is missing, empty, or not an array",
            expected="at least one direct-child source-root exclusion",
        )

    excluded_roots = []
    seen_ids = set()
    seen_resolved_paths = set()
    for index, raw_exclusion in enumerate(exclusions):
        exclusion = _require_mapping(
            raw_exclusion,
            code="CONTRACT_MALFORMED",
            path=actual_contract,
            field=f"exclusions[{index}]",
        )
        exclusion_id = exclusion.get("id")
        if not isinstance(exclusion_id, str) or not exclusion_id.strip():
            raise SiteExclusionError(
                "CONTRACT_MALFORMED",
                path=actual_contract,
                observed=f"exclusions[{index}].id is missing or blank",
                expected="a unique nonblank exclusion ID",
            )
        if exclusion_id in seen_ids:
            raise SiteExclusionError(
                "CONTRACT_MALFORMED",
                path=actual_contract,
                observed=f"duplicate exclusion ID {exclusion_id}",
                expected="unique exclusion IDs",
            )
        seen_ids.add(exclusion_id)

        if exclusion.get("resolution") != "direct-workspace-child":
            raise SiteExclusionError(
                "CONTRACT_MALFORMED",
                path=actual_contract,
                observed=str(exclusion.get("resolution")),
                expected="direct-workspace-child",
            )
        if exclusion.get("must_exist") is not True:
            raise SiteExclusionError(
                "CONTRACT_MALFORMED",
                path=actual_contract,
                observed=str(exclusion.get("must_exist")),
                expected="must_exist: true for the manuscript root",
            )

        root_parts = _safe_relative_parts(
            exclusion.get("path"),
            code="CONTRACT_MALFORMED",
            path=actual_contract,
            field=f"exclusions[{index}].path",
            direct_child=True,
        )
        relative_root = PurePosixPath(*root_parts).as_posix()
        unresolved_root = workspace.joinpath(*root_parts)
        resolved_root = _resolve_existing(
            unresolved_root,
            code="CONTRACT_STALE",
            expected="the declared manuscript root to exist",
        )
        if not resolved_root.is_dir():
            raise SiteExclusionError(
                "CONTRACT_STALE",
                path=unresolved_root,
                observed="declared exclusion is not a directory",
                expected="an existing manuscript root directory",
            )
        if resolved_root in seen_resolved_paths:
            raise SiteExclusionError(
                "CONTRACT_MALFORMED",
                path=actual_contract,
                observed=f"duplicate resolved exclusion {resolved_root}",
                expected="unique resolved exclusion roots",
            )
        seen_resolved_paths.add(resolved_root)

        root_evidence = _require_mapping(
            exclusion.get("root_evidence"),
            code="CONTRACT_MALFORMED",
            path=actual_contract,
            field=f"exclusions[{index}].root_evidence",
        )
        required_children = root_evidence.get("required_children")
        if not isinstance(required_children, list) or not required_children:
            raise SiteExclusionError(
                "CONTRACT_MALFORMED",
                path=actual_contract,
                observed="root_evidence.required_children is missing or empty",
                expected="one or more required manuscript-root children",
            )
        for child_index, child in enumerate(required_children):
            child_parts = _safe_relative_parts(
                child,
                code="CONTRACT_MALFORMED",
                path=actual_contract,
                field=(
                    f"exclusions[{index}].root_evidence.required_children"
                    f"[{child_index}]"
                ),
                direct_child=True,
            )
            evidence_path = resolved_root.joinpath(*child_parts)
            if not evidence_path.is_dir():
                raise SiteExclusionError(
                    "CONTRACT_STALE",
                    path=evidence_path,
                    observed="required manuscript-root evidence is absent",
                    expected="an existing directory named by required_children",
                )

        excluded_roots.append(
            ExcludedRoot(
                exclusion_id=exclusion_id,
                relative_path=relative_root,
                resolved_path=resolved_root,
            )
        )

    if actual_contract.parent not in {
        excluded.resolved_path for excluded in excluded_roots
    }:
        raise SiteExclusionError(
            "CONTRACT_STALE",
            path=actual_contract,
            observed="the loaded contract is not inside a declared exclusion root",
            expected="the contract's parent manuscript root to be excluded",
        )

    matching_rule = _require_mapping(
        document.get("matching_rule"),
        code="CONTRACT_MALFORMED",
        path=actual_contract,
        field="matching_rule",
    )
    ordering = _require_mapping(
        matching_rule.get("ordering_constraint"),
        code="CONTRACT_MALFORMED",
        path=actual_contract,
        field="matching_rule.ordering_constraint",
    )
    precedes = ordering.get("exclusion_check_precedes")
    required_later_steps = {"glob-markdown", "visibility-plan-fallback"}
    if not isinstance(precedes, list) or not required_later_steps.issubset(
        set(precedes)
    ):
        raise SiteExclusionError(
            "CONTRACT_MALFORMED",
            path=actual_contract,
            observed=str(precedes),
            expected=(
                "exclusion_check_precedes to include glob-markdown and "
                "visibility-plan-fallback"
            ),
        )

    honest_limit = _require_mapping(
        document.get("honest_limit"),
        code="CONTRACT_MALFORMED",
        path=actual_contract,
        field="honest_limit",
    )
    external_follow_up = _require_mapping(
        honest_limit.get("external_follow_up"),
        code="CONTRACT_MALFORMED",
        path=actual_contract,
        field="honest_limit.external_follow_up",
    )
    if external_follow_up.get("inside_this_project_acceptance") is not False:
        raise SiteExclusionError(
            "CONTRACT_MALFORMED",
            path=actual_contract,
            observed=str(external_follow_up.get("inside_this_project_acceptance")),
            expected="inside_this_project_acceptance: false",
        )

    return LoadedContract(
        workspace_root=workspace,
        contract_path=actual_contract,
        raw=document,
        excluded_roots=tuple(excluded_roots),
    )


def _is_excluded(path: Path, excluded_roots: Iterable[ExcludedRoot]) -> bool:
    return any(
        _path_is_at_or_below(path, excluded.resolved_path)
        for excluded in excluded_roots
    )


def _add_markdown_source(
    candidate: Path,
    *,
    contract: LoadedContract,
    sources_by_resolved_path: Dict[Path, MarkdownSource],
) -> None:
    if candidate.suffix.lower() != ".md":
        return
    resolved = _resolve_existing(
        candidate,
        code="SOURCE_UNREADABLE",
        expected="a readable Markdown source",
    )
    if _is_excluded(resolved, contract.excluded_roots):
        return
    relative_path = _relative_posix(resolved, contract.workspace_root)
    sources_by_resolved_path.setdefault(
        resolved,
        MarkdownSource(relative_path=relative_path, resolved_path=resolved),
    )


def discover_markdown_sources(
    contract: LoadedContract,
) -> Tuple[Tuple[str, ...], Tuple[MarkdownSource, ...]]:
    """Discover Markdown only after direct-child exclusions are resolved.

    The first pass enumerates and resolves every direct child and removes all
    excluded candidates. Only the second pass applies source-root eligibility
    and walks Markdown. This ordering is the central contract invariant.
    """

    try:
        direct_children = sorted(
            contract.workspace_root.iterdir(),
            key=lambda item: _normalized_text(item.name),
        )
    except OSError as exc:
        raise SiteExclusionError(
            "WORKSPACE_UNREADABLE",
            path=contract.workspace_root,
            observed=str(exc),
            expected="readable direct workspace children",
        ) from exc

    surviving_children = []
    for child in direct_children:
        resolved_child = _resolve_existing(
            child,
            code="SOURCE_ROOT_UNREADABLE",
            expected="a resolvable direct workspace child",
        )
        if _is_excluded(resolved_child, contract.excluded_roots):
            continue
        surviving_children.append((child, resolved_child))

    scanned_direct_children = []
    sources_by_resolved_path: Dict[Path, MarkdownSource] = {}
    for lexical_child, resolved_child in surviving_children:
        # Hidden project/tooling directories are not eligible song roots. This
        # eligibility rule intentionally runs only after exclusion filtering.
        if lexical_child.name.startswith("."):
            continue
        _relative_posix(resolved_child, contract.workspace_root)
        scanned_direct_children.append(lexical_child.name)

        if resolved_child.is_file():
            _add_markdown_source(
                resolved_child,
                contract=contract,
                sources_by_resolved_path=sources_by_resolved_path,
            )
            continue
        if not resolved_child.is_dir():
            continue

        for directory, directory_names, file_names in os.walk(
            resolved_child, followlinks=False
        ):
            directory_path = Path(directory)
            safe_directory_names = []
            for directory_name in sorted(
                directory_names, key=_normalized_text
            ):
                nested_directory = directory_path / directory_name
                nested_resolved = _resolve_existing(
                    nested_directory,
                    code="SOURCE_ROOT_UNREADABLE",
                    expected="a resolvable source directory",
                )
                if _is_excluded(nested_resolved, contract.excluded_roots):
                    continue
                _relative_posix(nested_resolved, contract.workspace_root)
                if nested_directory.is_symlink():
                    # Do not follow directory links. Direct-child aliases into
                    # the manuscript were already excluded in the first pass.
                    continue
                safe_directory_names.append(directory_name)
            directory_names[:] = safe_directory_names

            for file_name in sorted(file_names, key=_normalized_text):
                _add_markdown_source(
                    directory_path / file_name,
                    contract=contract,
                    sources_by_resolved_path=sources_by_resolved_path,
                )

    sources = tuple(
        sorted(
            sources_by_resolved_path.values(),
            key=lambda source: _normalized_text(source.relative_path),
        )
    )
    return tuple(scanned_direct_children), sources


def _normalize_visibility_source(value: Any, *, plan_path: Path) -> str:
    parts = _safe_relative_parts(
        value,
        code="VISIBILITY_PLAN_MALFORMED",
        path=plan_path,
        field="visibility row source",
        direct_child=False,
    )
    source = PurePosixPath(*parts).as_posix()
    if PurePosixPath(source).suffix.lower() != ".md":
        raise SiteExclusionError(
            "VISIBILITY_PLAN_MALFORMED",
            path=plan_path,
            observed=source,
            expected="a workspace-relative Markdown source path",
        )
    return source


def load_visibility_plan(plan_path: Path | str) -> VisibilityPlan:
    """Load the small, fixture-facing reference visibility format."""

    path = Path(plan_path)
    if not path.exists() or not path.is_file():
        raise SiteExclusionError(
            "VISIBILITY_PLAN_MISSING",
            path=path,
            observed="file does not exist or is not a file",
            expected="a readable reference visibility JSON file",
        )
    try:
        parsed = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise SiteExclusionError(
            "VISIBILITY_PLAN_MALFORMED",
            path=path,
            observed=str(exc),
            expected=f"valid JSON matching {SUPPORTED_VISIBILITY_SCHEMA}",
        ) from exc

    document = _require_mapping(
        parsed,
        code="VISIBILITY_PLAN_MALFORMED",
        path=path,
        field="visibility plan",
    )
    if document.get("schema") != SUPPORTED_VISIBILITY_SCHEMA:
        raise SiteExclusionError(
            "VISIBILITY_PLAN_MALFORMED",
            path=path,
            observed=str(document.get("schema")),
            expected=SUPPORTED_VISIBILITY_SCHEMA,
        )
    default_visible = document.get("default_visible")
    if not isinstance(default_visible, bool):
        raise SiteExclusionError(
            "VISIBILITY_PLAN_MALFORMED",
            path=path,
            observed=str(default_visible),
            expected="a boolean default_visible value",
        )
    raw_rows = document.get("rows")
    if not isinstance(raw_rows, list):
        raise SiteExclusionError(
            "VISIBILITY_PLAN_MALFORMED",
            path=path,
            observed="rows is missing or not an array",
            expected="an array of visibility rows",
        )

    rows: Dict[str, VisibilityRow] = {}
    for index, raw_row in enumerate(raw_rows):
        row = _require_mapping(
            raw_row,
            code="VISIBILITY_PLAN_MALFORMED",
            path=path,
            field=f"rows[{index}]",
        )
        source = _normalize_visibility_source(row.get("source"), plan_path=path)
        if source in rows:
            raise SiteExclusionError(
                "VISIBILITY_PLAN_MALFORMED",
                path=path,
                observed=f"duplicate row for {source}",
                expected="one visibility row per source",
            )
        visible = row.get("visible")
        if not isinstance(visible, bool):
            raise SiteExclusionError(
                "VISIBILITY_PLAN_MALFORMED",
                path=path,
                observed=f"rows[{index}].visible={visible!r}",
                expected="a boolean visible value",
            )
        title = row.get("title")
        slug = row.get("slug")
        if title is not None and (
            not isinstance(title, str) or not title.strip()
        ):
            raise SiteExclusionError(
                "VISIBILITY_PLAN_MALFORMED",
                path=path,
                observed=f"rows[{index}].title={title!r}",
                expected="a nonblank string when title is present",
            )
        if slug is not None and (
            not isinstance(slug, str)
            or re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) is None
        ):
            raise SiteExclusionError(
                "VISIBILITY_PLAN_MALFORMED",
                path=path,
                observed=f"rows[{index}].slug={slug!r}",
                expected="a lowercase kebab-case slug when slug is present",
            )
        rows[source] = VisibilityRow(
            source=source,
            visible=visible,
            title=title.strip() if isinstance(title, str) else None,
            slug=slug,
        )

    return VisibilityPlan(default_visible=default_visible, rows=rows)


def _slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", ascii_text.lower()).strip("-")
    return slug or "song"


def collect_songs(
    sources: Sequence[MarkdownSource],
    visibility_plan: VisibilityPlan | None = None,
) -> Tuple[Song, ...]:
    """Create Songs only from sources that survived exclusion discovery."""

    plan = visibility_plan or VisibilityPlan(default_visible=True, rows={})
    songs = []
    seen_slugs = set()
    for source in sources:
        row = plan.rows.get(source.relative_path)
        if row is not None:
            visible = row.visible
        else:
            visible = plan.default_visible
        if not visible:
            continue

        title = (
            row.title
            if row is not None and row.title is not None
            else Path(source.relative_path).stem
        )
        slug = (
            row.slug
            if row is not None and row.slug is not None
            else _slugify(title)
        )
        if slug in seen_slugs:
            raise SiteExclusionError(
                "SONG_SLUG_COLLISION",
                path=source.resolved_path,
                observed=f"duplicate slug {slug}",
                expected="one unique slug per discovered Song",
                exit_status=1,
            )
        seen_slugs.add(slug)
        songs.append(
            Song(source_path=source.relative_path, title=title, slug=slug)
        )
    return tuple(songs)


def render_reference_artifacts(
    songs: Sequence[Song],
) -> Tuple[GeneratedArtifact, ...]:
    """Render deterministic in-memory lyrics, search, and index artifacts."""

    artifacts = []
    for song in songs:
        artifacts.append(
            GeneratedArtifact(
                kind="lyrics",
                output_path=f"lyrics/{song.slug}.html",
                source_paths=(song.source_path,),
                content=(
                    "<!doctype html><title>"
                    f"{html.escape(song.title)}"
                    "</title><main data-source=\""
                    f"{html.escape(song.source_path, quote=True)}\"></main>"
                ),
            )
        )

    search_payload = [
        {
            "title": song.title,
            "url": f"/lyrics/{song.slug}.html",
            "source": song.source_path,
        }
        for song in songs
    ]
    index_payload = [
        {
            "slug": song.slug,
            "title": song.title,
            "source": song.source_path,
        }
        for song in songs
    ]
    all_sources = tuple(song.source_path for song in songs)
    artifacts.extend(
        (
            GeneratedArtifact(
                kind="search",
                output_path="search-index.json",
                source_paths=all_sources,
                content=json.dumps(
                    search_payload,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            ),
            GeneratedArtifact(
                kind="index",
                output_path="song-index.json",
                source_paths=all_sources,
                content=json.dumps(
                    index_payload,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            ),
        )
    )
    return tuple(artifacts)


def _verify_zero_excluded_entries(
    contract: LoadedContract,
    songs: Sequence[Song],
    artifacts: Sequence[GeneratedArtifact],
) -> None:
    referenced_sources = [song.source_path for song in songs]
    for artifact in artifacts:
        referenced_sources.extend(artifact.source_paths)

    for relative_source in referenced_sources:
        parts = _safe_relative_parts(
            relative_source,
            code="EXCLUSION_REACHED_DISCOVERY",
            path=contract.workspace_root,
            field="generated artifact source",
            direct_child=False,
        )
        resolved_source = (contract.workspace_root.joinpath(*parts)).resolve(
            strict=False
        )
        if _is_excluded(resolved_source, contract.excluded_roots):
            raise SiteExclusionError(
                "EXCLUSION_REACHED_DISCOVERY",
                path=resolved_source,
                observed="excluded manuscript source reached a generated artifact",
                expected="zero manuscript-derived lyrics, search, or index entries",
                exit_status=1,
            )


def run_site_exclusion(
    workspace_root: Path | str,
    *,
    contract_path: Path | str | None = None,
    visibility_plan_path: Path | str | None = None,
) -> SiteExclusionResult:
    """Run the complete local contract reference check."""

    contract = load_exclusion_contract(workspace_root, contract_path)
    scanned_direct_children, sources = discover_markdown_sources(contract)
    visibility_plan = (
        load_visibility_plan(visibility_plan_path)
        if visibility_plan_path is not None
        else None
    )
    songs = collect_songs(sources, visibility_plan)
    artifacts = render_reference_artifacts(songs)
    _verify_zero_excluded_entries(contract, songs, artifacts)
    return SiteExclusionResult(
        contract=contract,
        scanned_direct_children=scanned_direct_children,
        sources=sources,
        songs=songs,
        artifacts=artifacts,
    )


# ---------------------------------------------------------------------------
# Task 7.2 — Chapter_File parsing, Prose_Word counting, Length_Class validation
#
# Authority: Requirements 2.8-2.11, 9.5-9.7, 12.1-12.3, 12.10-12.12; the
# design's Lightweight Checker section; `planning/record-schemas.md` sections 1
# and 2 with the Chapter Header storage exception, the null/absence rules, and
# the identity/validation-order contract; and `planning/file-conventions.md` for
# the four-way agreement rule.
#
# Requirements 12.11 and 12.12 are prohibitions and are honoured by omission:
# nothing below scores or pass/fails a name choice, capitalization, prose voice,
# sentence artistry, emotional tone, Hook quality, POV distinctness, rhetorical
# force, or emotional truth. Hook *presence* and non-blankness are objective and
# are checked; Hook quality is Editorial_Review's alone.
# ---------------------------------------------------------------------------

SEVERITY_ERROR = "error"
SEVERITY_WARNING = "warning"

# A diagnostic's disposition decides which gate result it forces. It is kept
# separate from `severity` so the exit-status model cannot blur: an unreadable
# or malformed required input is never downgraded into an ordinary violation.
DISPOSITION_INCOMPLETE = "incomplete"
DISPOSITION_VIOLATION = "violation"

RESULT_PASS = "pass"
RESULT_REVISION = "revision"
RESULT_INCOMPLETE = "incomplete"

RESULT_EXIT_STATUS: Mapping[str, int] = {
    RESULT_PASS: 0,
    RESULT_REVISION: 1,
    RESULT_INCOMPLETE: 2,
}

SCOPE_CHAPTER = "chapter"
SCOPE_BATCH = "batch"
SCOPE_PLANNING = "planning"

DIAGNOSTIC_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")

MOVEMENTS: Tuple[str, ...] = (
    "discovery_part",
    "private_defense_part",
    "mindwars_part",
    "aftermath_coda",
)
MOVEMENT_ORDER: Mapping[str, int] = {
    movement: index for index, movement in enumerate(MOVEMENTS)
}
LENGTH_CLASSES: Tuple[str, ...] = ("microchapter", "normal", "long-outlier")
OUTLIER_LENGTH_CLASSES: Tuple[str, ...] = ("microchapter", "long-outlier")
CHAPTER_STATUSES: Tuple[str, ...] = (
    "planned",
    "exploratory",
    "draft",
    "revised",
    "approved",
    "final",
)

# The restricted Chapter_Header key set is closed and ordered by
# `record-schemas.md` section 1. No discriminator, schema key, or title.
CHAPTER_HEADER_KEYS: Tuple[str, ...] = (
    "movement",
    "chapter",
    "pov_id",
    "timeline_id",
    "motif_events",
    "hook",
    "words",
    "length_class",
    "status",
)

HEADER_DELIMITER = "---"
HARD_CHAPTER_MAXIMUM = 2500
MICROCHAPTER_MAXIMUM = 699
NORMAL_CHAPTER_RANGE = (700, 1600)
LONG_OUTLIER_RANGE = (1601, HARD_CHAPTER_MAXIMUM)
CHAPTERS_DIRECTORY = "chapters"
DEFAULT_ARC_OUTLINE_PATH = "planning/arc-outline.md"

# The closed set of record type names `record-schemas.md` defines. A fence
# naming anything else is malformed input, not a record to ignore.
RECORD_TYPES: Tuple[str, ...] = (
    "ChapterHeader",
    "ArcEntry",
    "POVProfile",
    "VoiceBrief",
    "TimelineEntry",
    "CrossCut",
    "CanonFact",
    "NovelExtension",
    "Reveal",
    "MotifEvent",
    "LiteralPhraseConstraint",
    "Baseline",
    "ArcChange",
    "EditorialFinding",
    "GateResult",
    "CheckerDiagnostic",
)

# The authoritative record sources, as an explicit allowlist. `record-schemas.md`
# is deliberately absent: it carries sixteen illustrative `EXAMPLE` records that
# the document itself gives no continuity authority, and globbing `planning/*.md`
# would turn them into phantom duplicate identities and dangling IDs. The
# allowlist is explicit rather than a name heuristic so that a prose naming habit
# never becomes load-bearing for referential integrity.
DEFAULT_RECORD_SOURCES: Tuple[str, ...] = (
    "planning/arc-outline.md",
    "planning/canon-bible.md",
    "planning/pov-roster.md",
    "planning/voice-briefs.md",
    "planning/motif-ledger.md",
)

# The stable-ID field of each record type this task resolves references against.
# `CanonFact`, `Reveal`, `Baseline`, and `LiteralPhraseConstraint` are parsed but
# deliberately unindexed: their reference rules belong to later tasks.
RECORD_ID_FIELDS: Mapping[str, str] = {
    "TimelineEntry": "timeline_id",
    "POVProfile": "pov_id",
    "VoiceBrief": "voice_brief_id",
    "MotifEvent": "motif_event_id",
    "CrossCut": "cross_cut_id",
    "NovelExtension": "extension_id",
}
REFERENCE_DANGLING_CODES: Mapping[str, str] = {
    "TimelineEntry": "TIMELINE_REFERENCE_DANGLING",
    "POVProfile": "POV_REFERENCE_DANGLING",
    "VoiceBrief": "VOICE_BRIEF_REFERENCE_DANGLING",
    "MotifEvent": "MOTIF_EVENT_REFERENCE_DANGLING",
    "CrossCut": "CROSS_CUT_REFERENCE_DANGLING",
}

# `technical_state` and its three mode-specific objects. Each key set is closed:
# `record-schemas.md` says the object "contains exactly" these keys.
TECHNICAL_STATE_KEYS: Tuple[str, ...] = (
    "mode",
    "source_side_continuity",
    "receiver_offset_seconds",
    "apparatus_mode",
    "transmit_stage_present",
    "person_specific_address_state",
    "cancel_state",
    "pair_state",
    "pairing_evidence",
    "evidence_scope",
)
# The four keys the 2026-09-11 mechanism amendment added. A pre-amendment record
# omits them, which is structurally incomplete input rather than a record whose
# mode may be inferred. Absence is the test; an explicit `null` value is not,
# because the schema permits `null` for all three mode-specific objects and for
# `technical_state` itself.
MECHANISM_AMENDMENT_KEYS: Tuple[str, ...] = (
    "mode",
    "cancel_state",
    "pair_state",
    "pairing_evidence",
)
NEURAL_COMMUNICATION_MODES: Tuple[str, ...] = (
    "RECEIVE",
    "INTRUDE",
    "CANCEL",
    "PAIR",
    "not-applicable",
)
SOURCE_SIDE_CONTINUITY_VALUES: Tuple[str, ...] = (
    "continuous",
    "discontinuous",
    "unknown",
    "not-applicable",
)
APPARATUS_MODES: Tuple[str, ...] = (
    "receive-only",
    "bench-transmit",
    "bidirectional-architecture",
    "not-applicable",
)
PERSON_SPECIFIC_ADDRESS_STATES: Tuple[str, ...] = (
    "unidentified",
    "identified",
    "locked",
    "reused",
    "not-applicable",
)
ADDRESSED_STATES: Tuple[str, ...] = ("identified", "locked", "reused")
CANCEL_STATE_KEYS: Tuple[str, ...] = (
    "scope",
    "individual_consent",
    "institutional_authorization",
    "subtraction",
    "inserted_content",
    "affected_set_predictable_before",
    "affected_set_enumerable_during",
    "affected_set_fully_mapped_after",
    "additive_inverse_exists",
    "provenance_yield",
)
CANCEL_SCOPES: Tuple[str, ...] = ("bounded-local", "area-scale")
INDIVIDUAL_CONSENT_KEYS: Tuple[str, ...] = (
    "character_id",
    "current",
    "specific_act",
    "revocable",
)
# The four `CancelState` booleans that MUST be exactly `false`: no reversal, no
# predictable set, no enumerable set, no complete post-hoc map.
CANCEL_FALSE_KEYS: Tuple[str, ...] = (
    "affected_set_predictable_before",
    "affected_set_enumerable_during",
    "affected_set_fully_mapped_after",
    "additive_inverse_exists",
)
CANCEL_NONE_KEYS: Tuple[str, ...] = ("inserted_content", "provenance_yield")
PAIR_STATE_KEYS: Tuple[str, ...] = (
    "participants",
    "consent",
    "calibration_id",
    "calibration_participants",
    "calibration_transferable",
    "deliberate_send_state",
)
PAIR_CONSENT_KEYS: Tuple[str, ...] = (
    "current",
    "specific_act",
    "revocable",
    "authorized_a",
    "authorized_b",
)
DELIBERATE_SEND_STATES: Tuple[str, ...] = (
    "required",
    "paused",
    "revoked",
    "integrity-failed",
)
PAIRING_EVIDENCE_KEYS: Tuple[str, ...] = (
    "consent_state_metadata_present",
    "transport_metadata_present",
    "metadata_semantically_opaque",
    "content_recording_enabled",
    "recording_consent_a",
    "recording_consent_b",
    "transcript",
)
PAIRING_EVIDENCE_TRUE_KEYS: Tuple[str, ...] = (
    "consent_state_metadata_present",
    "transport_metadata_present",
    "metadata_semantically_opaque",
)
TRANSCRIPT_KEYS: Tuple[str, ...] = (
    "transcript_id",
    "session_timeline_id",
    "content_scope",
)
MINDWARS_MOVEMENT = "mindwars_part"
CROSS_CUT_HANDOFF_MODES: Tuple[str, ...] = (
    "sensory-match",
    "causal-cut",
    "contradiction-cut",
    "threshold-cut",
    "temporal-braid",
    "delayed-return",
)
ARC_ENTRY_NO_CROSS_CUT = "none"

STABLE_ID_PATTERN = re.compile(r"^[A-Z][A-Z0-9]*(?:-[A-Z0-9]+)+$")
NON_NEGATIVE_INTEGER_PATTERN = re.compile(r"^(?:0|[1-9][0-9]*)$")
CHAPTER_SLUG_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
HEADER_LINE_PATTERN = re.compile(
    r"^(?P<key>[A-Za-z_][A-Za-z0-9_]*):(?:[ \t]+(?P<value>.*))?$"
)
MOTIF_EVENT_LIST_PATTERN = re.compile(r"^\[(?P<items>.*)\]$")
JSON_FENCE_OPEN_PATTERN = re.compile(
    r"^json record=(?P<record_type>[A-Za-z][A-Za-z0-9]*) schema=(?P<schema>[0-9]+)$"
)
JSON_FENCE_PREFIX = "json record="
JSON_FENCE_MARKER = "```"

_MOVEMENT_BY_DIRECTORY_SLUG: Mapping[str, str] = {
    movement.replace("_", "-"): movement for movement in MOVEMENTS
}
_CHAPTER_FILENAME_PATTERN = re.compile(
    r"^(?P<movement_slug>{0})-(?P<sequence>[0-9]{{3}})-(?P<slug>.+)\.md$".format(
        "|".join(re.escape(slug) for slug in sorted(_MOVEMENT_BY_DIRECTORY_SLUG))
    )
)
# A `---` line in the Prose_Body is an ordinary scene break. It only makes the
# prose boundary ambiguous when a restricted header key line immediately
# follows it, which is a mechanical test rather than a reading of the prose.
_SECOND_HEADER_LINE_PATTERN = re.compile(
    r"^(?:{0}):".format("|".join(CHAPTER_HEADER_KEYS))
)

_NULL_LITERAL = "null"
# The restricted header is not YAML, so an anchor, alias, tag, or block marker
# has no meaning here and is rejected rather than read as text. `[` is absent
# because `motif_events` legitimately carries a bracketed inline list, and `"`
# is absent because a quoted `hook` is the design's own form.
_YAML_STRUCTURE_PREFIXES = ("&", "*", "!", "|", ">", "?", "%", "@", "`", "{", "- ")


@dataclass(frozen=True)
class CheckerDiagnostic:
    """One deterministic objective diagnostic.

    Carries the design's `CheckerDiagnostic` fields: severity, stable code,
    scope, affected path or ID, observed condition, expected condition, and
    optional related references. `details` holds extra observed facts, such as
    the declared `words` value beside the observed count, so Requirement 12.3
    can report all four length facts in one line.
    """

    code: str
    scope: str
    item: str
    observed: str
    expected: str
    severity: str = SEVERITY_ERROR
    disposition: str = DISPOSITION_VIOLATION
    details: Tuple[Tuple[str, str], ...] = ()
    related: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if DIAGNOSTIC_CODE_PATTERN.match(self.code) is None:
            raise ValueError(
                "diagnostic code {0!r} must match {1}".format(
                    self.code, DIAGNOSTIC_CODE_PATTERN.pattern
                )
            )
        if self.severity not in (SEVERITY_ERROR, SEVERITY_WARNING):
            raise ValueError("unknown severity {0!r}".format(self.severity))
        if self.disposition not in (DISPOSITION_INCOMPLETE, DISPOSITION_VIOLATION):
            raise ValueError("unknown disposition {0!r}".format(self.disposition))

    def format_text(self) -> str:
        """Render the author-facing single line described by the design."""

        parts = [self.severity.upper(), self.code, self.item]
        parts.append("observed={0}".format(self.observed))
        parts.extend("{0}={1}".format(key, value) for key, value in self.details)
        parts.append("expected={0}".format(self.expected))
        return " ".join(parts)


def _diagnostic(
    code: str,
    *,
    scope: str,
    item: str,
    observed: Any,
    expected: str,
    disposition: str = DISPOSITION_VIOLATION,
    severity: str = SEVERITY_ERROR,
    details: Sequence[Tuple[str, Any]] = (),
    related: Sequence[str] = (),
) -> CheckerDiagnostic:
    return CheckerDiagnostic(
        code=code,
        scope=scope,
        item=item,
        observed=str(observed),
        expected=expected,
        severity=severity,
        disposition=disposition,
        details=tuple((key, str(value)) for key, value in details),
        related=tuple(related),
    )


def classify_result(diagnostics: Iterable[CheckerDiagnostic]) -> str:
    """Map diagnostics onto `pass`, `revision`, or `incomplete`.

    `incomplete` is tested first and unconditionally, so a missing, unreadable,
    malformed, duplicate-identity, or structurally incomplete required input
    always outranks an ordinary objective violation. Warnings may describe
    provisional data but never change the result.
    """

    saw_violation = False
    for diagnostic in diagnostics:
        if diagnostic.severity != SEVERITY_ERROR:
            continue
        if diagnostic.disposition == DISPOSITION_INCOMPLETE:
            return RESULT_INCOMPLETE
        saw_violation = True
    return RESULT_REVISION if saw_violation else RESULT_PASS


def exit_status_for_result(result: str) -> int:
    """Exit status for a gate result; `2` outranks `1` outranks `0`."""

    try:
        return RESULT_EXIT_STATUS[result]
    except KeyError:
        raise ValueError("unknown gate result {0!r}".format(result))


# ---------------------------------------------------------------------------
# Normalization, counting, and Length_Class derivation
# ---------------------------------------------------------------------------


def normalize_prose(value: str) -> str:
    """Normalize to Unicode NFC and to LF line endings."""

    return _normalized_text(value).replace("\r\n", "\n").replace("\r", "\n")


def count_prose_words(prose: str) -> int:
    """Prose_Word count: whitespace-separated tokens in a Prose_Body.

    Chapter_Header content is excluded by construction, because the caller
    passes only the text after the closing delimiter. Empty prose is a legal
    `0`, and a punctuation-only token still counts as a token.
    """

    return len(normalize_prose(prose).split())


def derive_length_class(words: int) -> Optional[str]:
    """Length_Class for an observed count, or `None` above the hard maximum.

    Below 700 is `microchapter`, 700 through 1,600 inclusive is `normal`, and
    1,601 through 2,500 inclusive is `long-outlier`. Above the
    Hard_Chapter_Maximum there is no valid class, so this returns `None` rather
    than inventing one.
    """

    if words < 0:
        raise ValueError("negative Prose_Word count {0}".format(words))
    if words > HARD_CHAPTER_MAXIMUM:
        return None
    if words <= MICROCHAPTER_MAXIMUM:
        return "microchapter"
    if words <= NORMAL_CHAPTER_RANGE[1]:
        return "normal"
    return "long-outlier"


def movement_directory_slug(movement: str) -> str:
    """Header `movement` value to its directory and filename slug."""

    if movement not in MOVEMENT_ORDER:
        raise ValueError("unknown movement {0!r}".format(movement))
    return movement.replace("_", "-")


def movement_from_directory_slug(slug: str) -> Optional[str]:
    """Directory or filename slug to its header `movement` value."""

    return _MOVEMENT_BY_DIRECTORY_SLUG.get(slug)


# ---------------------------------------------------------------------------
# Chapter filename
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChapterFileName:
    """The three parts a conforming Chapter_File basename encodes."""

    movement: str
    sequence: int
    slug: str

    @property
    def movement_slug(self) -> str:
        return movement_directory_slug(self.movement)


def parse_chapter_filename(basename: str) -> Optional[ChapterFileName]:
    """Parse `<movement>-<NNN>-<slug>.md`, or `None` when it does not conform.

    The movement slug is matched against the closed four-value set, so the
    hyphens inside `private-defense-part` never make the split ambiguous. Only
    the mechanical shape of the descriptive slug is checked: lowercase ASCII
    words joined by single hyphens. Which words the author chose is a name
    choice and is outside automated evaluation (Requirement 12.11).
    """

    match = _CHAPTER_FILENAME_PATTERN.match(basename)
    if match is None:
        return None
    slug = match.group("slug")
    if CHAPTER_SLUG_PATTERN.match(slug) is None:
        return None
    movement = movement_from_directory_slug(match.group("movement_slug"))
    if movement is None:  # pragma: no cover - the pattern is built from the map
        return None
    return ChapterFileName(
        movement=movement, sequence=int(match.group("sequence")), slug=slug
    )


# ---------------------------------------------------------------------------
# Chapter_Header parsing
# ---------------------------------------------------------------------------


class ChapterBoundaryError(RuntimeError):
    """The Prose_Body boundary is missing or ambiguous, so parsing stops."""

    def __init__(self, diagnostic: CheckerDiagnostic) -> None:
        self.diagnostic = diagnostic
        super().__init__(diagnostic.format_text())


def split_chapter_header(text: str, *, item: str) -> Tuple[Tuple[str, ...], str]:
    """Split a Chapter_File into its header lines and its Prose_Body.

    Fails safely: if the opening delimiter is absent, the closing delimiter is
    absent, or a second header block makes the boundary ambiguous, this raises
    `ChapterBoundaryError` carrying an incomplete-input diagnostic. It never
    guesses a boundary, so no word count or semantic validation can run on a
    file whose Prose_Body cannot be identified.
    """

    # A leading UTF-8 BOM is an encoding artifact rather than content, so it is
    # removed before the first physical line is compared.
    normalized = normalize_prose(text).lstrip("\ufeff")
    lines = normalized.split("\n")

    if not lines or lines[0] != HEADER_DELIMITER:
        observed = lines[0] if lines else ""
        raise ChapterBoundaryError(
            _diagnostic(
                "CHAPTER_HEADER_OPEN_DELIMITER_MISSING",
                scope=SCOPE_CHAPTER,
                item=item,
                observed="first physical line is {0!r}".format(observed),
                expected="first physical line to be exactly ---",
                disposition=DISPOSITION_INCOMPLETE,
            )
        )

    close_index: Optional[int] = None
    for index in range(1, len(lines)):
        if lines[index] == HEADER_DELIMITER:
            close_index = index
            break
    if close_index is None:
        raise ChapterBoundaryError(
            _diagnostic(
                "CHAPTER_HEADER_CLOSE_DELIMITER_MISSING",
                scope=SCOPE_CHAPTER,
                item=item,
                observed="no line containing only --- after the opening delimiter",
                expected="a closing --- line ending the Chapter_Header",
                disposition=DISPOSITION_INCOMPLETE,
            )
        )

    header_lines = tuple(lines[1:close_index])
    body_lines = lines[close_index + 1 :]
    for offset in range(len(body_lines) - 1):
        if body_lines[offset] != HEADER_DELIMITER:
            continue
        if _SECOND_HEADER_LINE_PATTERN.match(body_lines[offset + 1]) is None:
            continue
        raise ChapterBoundaryError(
            _diagnostic(
                "CHAPTER_HEADER_SECOND_BLOCK",
                scope=SCOPE_CHAPTER,
                item=item,
                observed="a second header block opens at line {0}".format(
                    close_index + offset + 2
                ),
                expected="exactly one Chapter_Header block per Chapter_File",
                disposition=DISPOSITION_INCOMPLETE,
            )
        )

    return header_lines, "\n".join(body_lines)


def _malformed_value(
    key: str, *, item: str, observed: Any, expected: str
) -> CheckerDiagnostic:
    return _diagnostic(
        "CHAPTER_HEADER_VALUE_MALFORMED",
        scope=SCOPE_CHAPTER,
        item=item,
        observed="{0}={1!r}".format(key, observed),
        expected=expected,
        disposition=DISPOSITION_INCOMPLETE,
        related=(key,),
    )


def _parse_header_scalar(
    key: str, raw: str, *, item: str
) -> Tuple[Any, Optional[CheckerDiagnostic]]:
    """Type and validate one restricted header value.

    Returns `(value, None)` on success and `(None, diagnostic)` otherwise. The
    grammar is the restricted one the design's metadata example shows: bare
    enums, integers, and stable IDs, a quoted single-line `hook`, and
    `motif_events` as a bracketed inline list. It is deliberately not YAML.
    """

    if raw == _NULL_LITERAL:
        return None, _diagnostic(
            "CHAPTER_HEADER_VALUE_NULL",
            scope=SCOPE_CHAPTER,
            item=item,
            observed="{0}=null".format(key),
            expected="a non-null value for every required Chapter_Header key",
            disposition=DISPOSITION_INCOMPLETE,
            related=(key,),
        )

    if raw.startswith(_YAML_STRUCTURE_PREFIXES):
        return None, _malformed_value(
            key,
            item=item,
            observed=raw,
            expected=(
                "a plain restricted-header value with no YAML anchor, alias, "
                "tag, or block marker; quote a Hook that begins with one"
            ),
        )

    if key == "hook":
        if raw.startswith('"'):
            try:
                value = json.loads(raw)
            except (json.JSONDecodeError, ValueError):
                return None, _malformed_value(
                    key,
                    item=item,
                    observed=raw,
                    expected="one complete double-quoted single-line string",
                )
            if not isinstance(value, str):
                return None, _malformed_value(
                    key, item=item, observed=raw, expected="a quoted string"
                )
        else:
            value = raw
        if not value.strip():
            return None, _malformed_value(
                key,
                item=item,
                observed=raw,
                expected="a nonblank single-line Hook description",
            )
        return value, None

    if key in ("chapter", "words"):
        if NON_NEGATIVE_INTEGER_PATTERN.match(raw) is None:
            return None, _malformed_value(
                key,
                item=item,
                observed=raw,
                expected="a non-negative decimal integer",
            )
        number = int(raw)
        if key == "chapter" and number < 1:
            return None, _malformed_value(
                key, item=item, observed=raw, expected="an integer of at least 1"
            )
        return number, None

    if key == "movement":
        if raw not in MOVEMENT_ORDER:
            return None, _malformed_value(
                key,
                item=item,
                observed=raw,
                expected="one of " + ", ".join(MOVEMENTS),
            )
        return raw, None

    if key == "length_class":
        if raw not in LENGTH_CLASSES:
            return None, _malformed_value(
                key,
                item=item,
                observed=raw,
                expected="one of " + ", ".join(LENGTH_CLASSES),
            )
        return raw, None

    if key == "status":
        if raw not in CHAPTER_STATUSES:
            return None, _malformed_value(
                key,
                item=item,
                observed=raw,
                expected="one of " + ", ".join(CHAPTER_STATUSES),
            )
        return raw, None

    if key in ("pov_id", "timeline_id"):
        if STABLE_ID_PATTERN.match(raw) is None:
            return None, _malformed_value(
                key,
                item=item,
                observed=raw,
                expected="a StableID matching " + STABLE_ID_PATTERN.pattern,
            )
        return raw, None

    if key == "motif_events":
        match = MOTIF_EVENT_LIST_PATTERN.match(raw)
        if match is None:
            return None, _malformed_value(
                key,
                item=item,
                observed=raw,
                expected="a bracketed inline list, [] when the chapter has no motifs",
            )
        inner = match.group("items").strip()
        if not inner:
            return [], None
        items = [part.strip() for part in inner.split(",")]
        if any(STABLE_ID_PATTERN.match(part) is None for part in items):
            return None, _malformed_value(
                key,
                item=item,
                observed=raw,
                expected="every item to be a StableID with no empty or trailing entry",
            )
        if len(set(items)) != len(items):
            return None, _malformed_value(
                key, item=item, observed=raw, expected="unique Motif_Event IDs"
            )
        return items, None

    raise AssertionError("unreachable restricted header key {0!r}".format(key))


def parse_chapter_header_lines(
    header_lines: Sequence[str], *, item: str
) -> Tuple[Dict[str, Any], Tuple[CheckerDiagnostic, ...]]:
    """Validate the restricted header block into the logical nine-key object.

    Only keys that parse cleanly appear in the returned mapping, so a caller
    can tell which declared values are trustworthy enough to compare. Every
    missing, duplicate, unknown, null, or malformed key yields an
    incomplete-input diagnostic (Requirement 12.1).
    """

    diagnostics: List[CheckerDiagnostic] = []
    values: Dict[str, Any] = {}
    seen: Dict[str, int] = {}

    for offset, line in enumerate(header_lines):
        match = HEADER_LINE_PATTERN.match(line)
        if match is None:
            diagnostics.append(
                _diagnostic(
                    "CHAPTER_HEADER_LINE_MALFORMED",
                    scope=SCOPE_CHAPTER,
                    item=item,
                    observed="header line {0} is {1!r}".format(offset + 2, line),
                    expected=(
                        "one `key: value` pair per line with no blank line, "
                        "continuation, or multiline value"
                    ),
                    disposition=DISPOSITION_INCOMPLETE,
                )
            )
            continue

        key = match.group("key")
        raw = match.group("value")
        if raw is None or not raw.strip():
            diagnostics.append(
                _malformed_value(
                    key,
                    item=item,
                    observed="" if raw is None else raw,
                    expected="a nonblank value on the same physical line",
                )
            )
            seen[key] = seen.get(key, 0) + 1
            continue
        raw = raw.strip()

        if key not in CHAPTER_HEADER_KEYS:
            diagnostics.append(
                _diagnostic(
                    "CHAPTER_HEADER_KEY_UNKNOWN",
                    scope=SCOPE_CHAPTER,
                    item=item,
                    observed=key,
                    expected="exactly the nine keys " + ", ".join(CHAPTER_HEADER_KEYS),
                    disposition=DISPOSITION_INCOMPLETE,
                    related=(key,),
                )
            )
            continue

        seen[key] = seen.get(key, 0) + 1
        if seen[key] > 1:
            diagnostics.append(
                _diagnostic(
                    "CHAPTER_HEADER_KEY_DUPLICATE",
                    scope=SCOPE_CHAPTER,
                    item=item,
                    observed="{0} occurs {1} times".format(key, seen[key]),
                    expected="exactly one occurrence of every required key",
                    disposition=DISPOSITION_INCOMPLETE,
                    related=(key,),
                )
            )
            # A duplicated key has no single trustworthy value, so the first
            # parse is discarded rather than silently preferred.
            values.pop(key, None)
            continue

        value, diagnostic = _parse_header_scalar(key, raw, item=item)
        if diagnostic is not None:
            diagnostics.append(diagnostic)
            continue
        values[key] = value

    for key in CHAPTER_HEADER_KEYS:
        if seen.get(key, 0) == 0:
            diagnostics.append(
                _diagnostic(
                    "CHAPTER_HEADER_KEY_MISSING",
                    scope=SCOPE_CHAPTER,
                    item=item,
                    observed="absent",
                    expected="a required {0} key".format(key),
                    disposition=DISPOSITION_INCOMPLETE,
                    related=(key,),
                )
            )
        elif seen.get(key, 0) > 1:
            values.pop(key, None)

    return values, tuple(diagnostics)


@dataclass(frozen=True)
class ChapterDocument:
    """One parsed Chapter_File.

    `header` holds only the keys that parsed cleanly, `prose_body` is the
    normalized text after the closing delimiter, and `boundary_resolved` records
    whether the Prose_Body boundary was identified at all. When it is `False`,
    `prose_body` is `None` and no count or semantic validation ran.
    """

    relative_path: str
    filename: Optional[ChapterFileName]
    header: Mapping[str, Any] = field(default_factory=dict)
    prose_body: Optional[str] = None
    boundary_resolved: bool = False
    diagnostics: Tuple[CheckerDiagnostic, ...] = ()

    @property
    def basename(self) -> str:
        return PurePosixPath(self.relative_path).name

    @property
    def directory(self) -> str:
        return PurePosixPath(self.relative_path).parent.as_posix()

    @property
    def header_complete(self) -> bool:
        return all(key in self.header for key in CHAPTER_HEADER_KEYS)


def parse_chapter_document(
    text: str, *, relative_path: str
) -> ChapterDocument:
    """Parse one Chapter_File's text into a `ChapterDocument`."""

    filename = parse_chapter_filename(PurePosixPath(relative_path).name)
    try:
        header_lines, prose_body = split_chapter_header(text, item=relative_path)
    except ChapterBoundaryError as boundary_error:
        return ChapterDocument(
            relative_path=relative_path,
            filename=filename,
            diagnostics=(boundary_error.diagnostic,),
        )

    values, diagnostics = parse_chapter_header_lines(
        header_lines, item=relative_path
    )
    return ChapterDocument(
        relative_path=relative_path,
        filename=filename,
        header=values,
        prose_body=prose_body,
        boundary_resolved=True,
        diagnostics=diagnostics,
    )


def read_chapter_document(
    path: Path, *, relative_path: Optional[str] = None
) -> ChapterDocument:
    """Read and parse one Chapter_File, failing closed on unreadable input."""

    item = relative_path if relative_path is not None else Path(path).name
    if not Path(path).is_file():
        return ChapterDocument(
            relative_path=item,
            filename=parse_chapter_filename(PurePosixPath(item).name),
            diagnostics=(
                _diagnostic(
                    "CHAPTER_FILE_MISSING",
                    scope=SCOPE_CHAPTER,
                    item=item,
                    observed="no readable file at this path",
                    expected="an existing Chapter_File",
                    disposition=DISPOSITION_INCOMPLETE,
                ),
            ),
        )
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return ChapterDocument(
            relative_path=item,
            filename=parse_chapter_filename(PurePosixPath(item).name),
            diagnostics=(
                _diagnostic(
                    "CHAPTER_FILE_UNREADABLE",
                    scope=SCOPE_CHAPTER,
                    item=item,
                    observed=str(exc),
                    expected="readable UTF-8 text",
                    disposition=DISPOSITION_INCOMPLETE,
                ),
            ),
        )
    return parse_chapter_document(text, relative_path=item)


# ---------------------------------------------------------------------------
# Prose_Word count and Length_Class validation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChapterLengthReport:
    """The four length facts Requirement 12.3 reports for one Chapter_File."""

    relative_path: str
    observed_words: int
    declared_words: Optional[int]
    observed_length_class: Optional[str]
    declared_length_class: Optional[str]

    @property
    def within_hard_maximum(self) -> bool:
        return self.observed_words <= HARD_CHAPTER_MAXIMUM


def chapter_length_report(document: ChapterDocument) -> Optional[ChapterLengthReport]:
    """Observed and declared length facts, or `None` if the boundary failed.

    Counting is only possible once the Prose_Body boundary is unambiguous, so a
    file that stopped at an incomplete-input diagnostic yields no report rather
    than a guessed one.
    """

    if not document.boundary_resolved or document.prose_body is None:
        return None
    observed = count_prose_words(document.prose_body)
    declared_words = document.header.get("words")
    return ChapterLengthReport(
        relative_path=document.relative_path,
        observed_words=observed,
        declared_words=declared_words if isinstance(declared_words, int) else None,
        observed_length_class=derive_length_class(observed),
        declared_length_class=document.header.get("length_class"),
    )


def check_chapter_length(
    report: Optional[ChapterLengthReport],
    *,
    arc_entry: Optional["ArcEntryRecord"] = None,
) -> Tuple[CheckerDiagnostic, ...]:
    """Validate the declared count, the Length_Class, and the outlier purpose.

    Requirement 9.7 requires the declared `words` value to equal the observed
    count. Requirement 2.9 caps a Chapter_File at the Hard_Chapter_Maximum, and
    above that cap no Length_Class is valid, so the class comparison is not
    attempted. Requirements 2.10 and 2.11 require a nonblank planned purpose for
    either outlier class and `null` for a `normal` entry.
    """

    if report is None:
        return ()

    diagnostics: List[CheckerDiagnostic] = []
    item = report.relative_path

    if (
        report.declared_words is not None
        and report.declared_words != report.observed_words
    ):
        diagnostics.append(
            _diagnostic(
                "CHAPTER_WORD_COUNT",
                scope=SCOPE_CHAPTER,
                item=item,
                observed=report.observed_words,
                expected="equal",
                details=(("declared", report.declared_words),),
            )
        )

    if not report.within_hard_maximum:
        diagnostics.append(
            _diagnostic(
                "CHAPTER_HARD_MAXIMUM_EXCEEDED",
                scope=SCOPE_CHAPTER,
                item=item,
                observed=report.observed_words,
                expected=(
                    "at most {0} Prose_Words, above which no Length_Class "
                    "is valid".format(HARD_CHAPTER_MAXIMUM)
                ),
                details=(
                    ("declared_length_class", report.declared_length_class or "absent"),
                ),
            )
        )
    elif (
        report.declared_length_class is not None
        and report.declared_length_class != report.observed_length_class
    ):
        diagnostics.append(
            _diagnostic(
                "CHAPTER_LENGTH_CLASS_MISMATCH",
                scope=SCOPE_CHAPTER,
                item=item,
                observed=report.observed_length_class,
                expected="the class derived from the observed count",
                details=(
                    ("declared", report.declared_length_class),
                    ("words", report.observed_words),
                ),
            )
        )

    diagnostics.extend(_check_outlier_purpose(report, arc_entry))
    return tuple(diagnostics)


def _check_outlier_purpose(
    report: ChapterLengthReport, arc_entry: Optional["ArcEntryRecord"]
) -> Tuple[CheckerDiagnostic, ...]:
    if arc_entry is None:
        return ()

    classes = {
        value
        for value in (report.observed_length_class, arc_entry.estimated_length_class)
        if value is not None
    }
    outliers = sorted(classes.intersection(OUTLIER_LENGTH_CLASSES))
    purpose = arc_entry.outlier_purpose

    if outliers:
        if not isinstance(purpose, str) or not purpose.strip():
            return (
                _diagnostic(
                    "CHAPTER_OUTLIER_PURPOSE_MISSING",
                    scope=SCOPE_CHAPTER,
                    item=report.relative_path,
                    observed="outlier_purpose={0!r}".format(purpose),
                    expected="a nonblank planned purpose for a {0} chapter".format(
                        "/".join(outliers)
                    ),
                    related=(arc_entry.identity,),
                ),
            )
        return ()

    if purpose is not None:
        return (
            _diagnostic(
                "CHAPTER_OUTLIER_PURPOSE_UNEXPECTED",
                scope=SCOPE_CHAPTER,
                item=report.relative_path,
                observed="outlier_purpose={0!r}".format(purpose),
                expected="null outlier_purpose for a normal chapter",
                related=(arc_entry.identity,),
            ),
        )
    return ()


# ---------------------------------------------------------------------------
# ArcEntry records, read from typed JSON fences
#
# Only the fields the four-way agreement rule and the outlier-purpose rule need
# are typed here. The complete closed-key ArcEntry contract, the other fifteen
# record types, and every ID resolution belong to task 7.3, which can build on
# `iter_json_fences` and on `ArcEntryRecord.payload`.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class JsonFence:
    """One typed fenced JSON block located in a planning document."""

    source: str
    ordinal: int
    record_type: str
    schema: int
    start_line: int
    end_line: int
    payload: Any = None
    error: Optional[str] = None


def _reject_json_constant(literal: str) -> Any:
    raise ValueError("JSON constant {0} is not permitted".format(literal))


def _reject_duplicate_json_keys(
    pairs: Sequence[Tuple[str, Any]]
) -> Dict[str, Any]:
    seen = set()
    for key, _value in pairs:
        if key in seen:
            raise ValueError("duplicate object key {0!r}".format(key))
        seen.add(key)
    return dict(pairs)


def _strict_json_loads(body: str) -> Any:
    return json.loads(
        body,
        object_pairs_hook=_reject_duplicate_json_keys,
        parse_constant=_reject_json_constant,
    )


def iter_json_fences(text: str, *, source: str) -> Iterable[JsonFence]:
    """Yield every typed fenced JSON record block in a planning document.

    The opening fence sits at column zero with the exact information string
    `json record=<RecordType> schema=<n>` and the closing fence is three
    backticks at column zero. Blocks with any other information string are
    ordinary Markdown and are skipped; a block that opens with
    `json record=` but does not match the exact shape is reported as malformed
    rather than silently ignored.
    """

    lines = normalize_prose(text).split("\n")
    ordinal = 0
    index = 0
    while index < len(lines):
        line = lines[index]
        if not line.startswith(JSON_FENCE_MARKER):
            index += 1
            continue
        information = line[len(JSON_FENCE_MARKER) :].strip()
        if not information.startswith(JSON_FENCE_PREFIX):
            index += 1
            continue

        ordinal += 1
        start_line = index + 1
        close_index: Optional[int] = None
        for scan in range(index + 1, len(lines)):
            if lines[scan] == JSON_FENCE_MARKER:
                close_index = scan
                break
        end_line = (close_index + 1) if close_index is not None else len(lines)
        match = JSON_FENCE_OPEN_PATTERN.match(information)
        record_type = match.group("record_type") if match else ""
        schema = int(match.group("schema")) if match else 0

        if close_index is None:
            yield JsonFence(
                source=source,
                ordinal=ordinal,
                record_type=record_type,
                schema=schema,
                start_line=start_line,
                end_line=end_line,
                error="unterminated fenced record block",
            )
            return
        if match is None:
            yield JsonFence(
                source=source,
                ordinal=ordinal,
                record_type=record_type,
                schema=schema,
                start_line=start_line,
                end_line=end_line,
                error=(
                    "information string {0!r} is not "
                    "`json record=<RecordType> schema=<n>`".format(information)
                ),
            )
            index = close_index + 1
            continue

        body = "\n".join(lines[index + 1 : close_index])
        try:
            payload = _strict_json_loads(body)
        except (json.JSONDecodeError, ValueError) as exc:
            yield JsonFence(
                source=source,
                ordinal=ordinal,
                record_type=record_type,
                schema=schema,
                start_line=start_line,
                end_line=end_line,
                error=str(exc),
            )
            index = close_index + 1
            continue

        yield JsonFence(
            source=source,
            ordinal=ordinal,
            record_type=record_type,
            schema=schema,
            start_line=start_line,
            end_line=end_line,
            payload=payload,
        )
        index = close_index + 1


@dataclass(frozen=True)
class ArcEntryRecord:
    """The ArcEntry fields the task 7.2 checks need, plus the raw record."""

    source: str
    ordinal: int
    array_index: Optional[int]
    chapter: Optional[int]
    filename: Optional[str]
    movement: Optional[str]
    estimated_length_class: Optional[str]
    outlier_purpose: Optional[str]
    payload: Mapping[str, Any] = field(default_factory=dict)

    @property
    def identity(self) -> str:
        location = "{0}#{1}".format(self.source, self.ordinal)
        if self.array_index is not None:
            location += "[{0}]".format(self.array_index)
        return location


@dataclass(frozen=True)
class PlanningRecord:
    """One structurally located fenced record payload from a planning document.

    Records live in typed fences that hold either one object or an array of
    objects, so a record's location is its document, its fence ordinal, and its
    index inside that fence's array when there is one.
    """

    source: str
    ordinal: int
    array_index: Optional[int]
    record_type: str
    start_line: int
    end_line: int
    payload: Mapping[str, Any] = field(default_factory=dict)

    @property
    def identity(self) -> str:
        location = "{0}#{1}".format(self.source, self.ordinal)
        if self.array_index is not None:
            location += "[{0}]".format(self.array_index)
        return location

    @property
    def lines(self) -> str:
        return "{0}-{1}".format(self.start_line, self.end_line)

    def record_id(self) -> Optional[str]:
        """The record's own stable ID, when its type declares one and it parses."""

        id_field = RECORD_ID_FIELDS.get(self.record_type)
        if id_field is None:
            return None
        value = self.payload.get(id_field)
        if isinstance(value, str) and STABLE_ID_PATTERN.match(value.strip()):
            return _normalized_text(value.strip())
        return None

    def malformed(
        self, code: str, *, observed: Any, expected: str
    ) -> CheckerDiagnostic:
        """A structurally incomplete-input diagnostic located at this record."""

        return _diagnostic(
            code,
            scope=SCOPE_PLANNING,
            item=self.identity,
            observed=observed,
            expected=expected,
            disposition=DISPOSITION_INCOMPLETE,
            details=(("lines", self.lines),),
        )

    def violation(
        self,
        code: str,
        *,
        observed: Any,
        expected: str,
        item: Optional[str] = None,
        details: Sequence[Tuple[str, Any]] = (),
        related: Sequence[str] = (),
    ) -> CheckerDiagnostic:
        """An objective semantic violation located at this record."""

        return _diagnostic(
            code,
            scope=SCOPE_PLANNING,
            item=item if item is not None else (self.record_id() or self.identity),
            observed=observed,
            expected=expected,
            details=tuple(details) + (("lines", self.lines),),
            related=tuple(related) or (self.identity,),
        )


def parse_planning_records(
    text: str, *, source: str, record_types: Optional[Sequence[str]] = None
) -> Tuple[Mapping[str, Tuple[PlanningRecord, ...]], Tuple[CheckerDiagnostic, ...]]:
    """Read every typed fenced record from one planning document, by type.

    One pass over `iter_json_fences` dispatching on `record_type`. A fence holds
    either one object or a nonempty array of objects; both forms are located
    precisely so a duplicate identity can name the exact record. Only structural
    shape is decided here: nothing is inferred from prose around the fence, and
    per-type field validation belongs to the individual checks below.

    `record_types` restricts the pass to the named types and suppresses type and
    schema diagnostics for the rest, which is what a caller wanting a single type
    out of a mixed document needs.
    """

    wanted = None if record_types is None else frozenset(record_types)
    grouped: Dict[str, List[PlanningRecord]] = {}
    diagnostics: List[CheckerDiagnostic] = []

    for fence in iter_json_fences(text, source=source):
        location = "{0}#{1}".format(fence.source, fence.ordinal)
        lines = (("lines", "{0}-{1}".format(fence.start_line, fence.end_line)),)
        if fence.error is not None:
            diagnostics.append(
                _diagnostic(
                    "PLANNING_FENCE_MALFORMED",
                    scope=SCOPE_PLANNING,
                    item=location,
                    observed=fence.error,
                    expected="one strict typed fenced JSON record",
                    disposition=DISPOSITION_INCOMPLETE,
                    details=lines,
                )
            )
            continue
        if wanted is not None and fence.record_type not in wanted:
            continue
        if fence.record_type not in RECORD_TYPES:
            diagnostics.append(
                _diagnostic(
                    "PLANNING_RECORD_TYPE_UNKNOWN",
                    scope=SCOPE_PLANNING,
                    item=location,
                    observed="record={0}".format(fence.record_type),
                    expected="one record type defined by record-schemas.md",
                    disposition=DISPOSITION_INCOMPLETE,
                    details=lines,
                )
            )
            continue
        if fence.schema != 1:
            diagnostics.append(
                _diagnostic(
                    "PLANNING_FENCE_UNSUPPORTED_SCHEMA",
                    scope=SCOPE_PLANNING,
                    item=location,
                    observed="schema={0}".format(fence.schema),
                    expected="schema=1",
                    disposition=DISPOSITION_INCOMPLETE,
                    details=lines,
                )
            )
            continue

        payloads: Sequence[Tuple[Optional[int], Any]]
        if isinstance(fence.payload, list):
            if not fence.payload:
                diagnostics.append(
                    _diagnostic(
                        "PLANNING_RECORD_MALFORMED",
                        scope=SCOPE_PLANNING,
                        item=location,
                        observed="empty record array",
                        expected="one object or a nonempty array of objects",
                        disposition=DISPOSITION_INCOMPLETE,
                        details=lines,
                    )
                )
                continue
            payloads = [(index, member) for index, member in enumerate(fence.payload)]
        else:
            payloads = [(None, fence.payload)]

        for array_index, payload in payloads:
            record = PlanningRecord(
                source=fence.source,
                ordinal=fence.ordinal,
                array_index=array_index,
                record_type=fence.record_type,
                start_line=fence.start_line,
                end_line=fence.end_line,
                payload=payload if isinstance(payload, dict) else {},
            )
            if not isinstance(payload, dict):
                diagnostics.append(
                    record.malformed(
                        "PLANNING_RECORD_MALFORMED",
                        observed="record has type {0}".format(type(payload).__name__),
                        expected="a JSON object",
                    )
                )
                continue
            grouped.setdefault(fence.record_type, []).append(record)

    return (
        {record_type: tuple(items) for record_type, items in grouped.items()},
        tuple(diagnostics),
    )


def _arc_entry_malformed(
    record: PlanningRecord, *, observed: str, expected: str
) -> CheckerDiagnostic:
    return record.malformed(
        "ARC_ENTRY_MALFORMED", observed=observed, expected=expected
    )


def _build_arc_entry(
    record: PlanningRecord,
) -> Tuple[Optional[ArcEntryRecord], Tuple[CheckerDiagnostic, ...]]:
    payload = record.payload
    diagnostics: List[CheckerDiagnostic] = []

    chapter = payload.get("chapter")
    if isinstance(chapter, bool) or not isinstance(chapter, int) or chapter < 1:
        diagnostics.append(
            _arc_entry_malformed(
                record,
                observed="chapter={0!r}".format(chapter),
                expected="an integer of at least 1",
            )
        )
        chapter = None

    filename = payload.get("filename")
    if not isinstance(filename, str) or not filename.strip():
        diagnostics.append(
            _arc_entry_malformed(
                record,
                observed="filename={0!r}".format(filename),
                expected="a nonblank workspace-relative POSIX path",
            )
        )
        filename = None
    else:
        filename = _normalized_text(filename.strip())

    movement = payload.get("movement")
    if movement not in MOVEMENT_ORDER:
        diagnostics.append(
            _arc_entry_malformed(
                record,
                observed="movement={0!r}".format(movement),
                expected="one of " + ", ".join(MOVEMENTS),
            )
        )
        movement = None

    estimated_length_class = payload.get("estimated_length_class")
    if estimated_length_class not in LENGTH_CLASSES:
        diagnostics.append(
            _arc_entry_malformed(
                record,
                observed="estimated_length_class={0!r}".format(estimated_length_class),
                expected="one of " + ", ".join(LENGTH_CLASSES),
            )
        )
        estimated_length_class = None

    outlier_purpose = payload.get("outlier_purpose")
    if "outlier_purpose" not in payload or not (
        outlier_purpose is None or isinstance(outlier_purpose, str)
    ):
        diagnostics.append(
            _arc_entry_malformed(
                record,
                observed="outlier_purpose={0!r}".format(outlier_purpose),
                expected="a required single-line string or null",
            )
        )
        outlier_purpose = None

    entry = ArcEntryRecord(
        source=record.source,
        ordinal=record.ordinal,
        array_index=record.array_index,
        chapter=chapter,
        filename=filename,
        movement=movement,
        estimated_length_class=estimated_length_class,
        outlier_purpose=outlier_purpose if isinstance(outlier_purpose, str) else None,
        payload=payload,
    )
    return entry, tuple(diagnostics)


def parse_arc_entries(
    text: str, *, source: str
) -> Tuple[Tuple[ArcEntryRecord, ...], Tuple[CheckerDiagnostic, ...]]:
    """Read every `ArcEntry` fence from one planning document.

    Restricted to `ArcEntry` so a document mixing record types reports only this
    type's faults. `load_reference_index` reads every allowlisted type instead.
    """

    grouped, diagnostics = parse_planning_records(
        text, source=source, record_types=("ArcEntry",)
    )
    entries: List[ArcEntryRecord] = []
    collected: List[CheckerDiagnostic] = list(diagnostics)
    for record in grouped.get("ArcEntry", ()):
        entry, entry_diagnostics = _build_arc_entry(record)
        collected.extend(entry_diagnostics)
        if entry is not None:
            entries.append(entry)
    return tuple(entries), tuple(collected)


def load_arc_entries(
    path: Path, *, relative_path: Optional[str] = None
) -> Tuple[Tuple[ArcEntryRecord, ...], Tuple[CheckerDiagnostic, ...]]:
    """Read the Arc_Outline document, failing closed when it is unavailable."""

    item = relative_path if relative_path is not None else Path(path).name
    if not Path(path).is_file():
        return (), (
            _diagnostic(
                "ARC_OUTLINE_MISSING",
                scope=SCOPE_PLANNING,
                item=item,
                observed="no readable file at this path",
                expected="the Arc_Outline document",
                disposition=DISPOSITION_INCOMPLETE,
            ),
        )
    try:
        text = Path(path).read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return (), (
            _diagnostic(
                "ARC_OUTLINE_UNREADABLE",
                scope=SCOPE_PLANNING,
                item=item,
                observed=str(exc),
                expected="readable UTF-8 text",
                disposition=DISPOSITION_INCOMPLETE,
            ),
        )
    return parse_arc_entries(text, source=item)


def match_arc_entry(
    entries: Sequence[ArcEntryRecord],
    *,
    relative_path: str,
    chapter: Optional[int],
) -> Tuple[Optional[ArcEntryRecord], Tuple[CheckerDiagnostic, ...]]:
    """Resolve the one ArcEntry that owns a Chapter_File.

    The stored path is the ground truth for a file that exists, so matching
    prefers `ArcEntry.filename` and falls back to the chapter number, which lets
    a filename disagreement be reported instead of collapsing into a missing
    entry. Duplicate identities are rejected before any reference resolves.
    """

    by_filename = [
        entry for entry in entries if entry.filename == relative_path
    ]
    if len(by_filename) > 1:
        return None, (
            _diagnostic(
                "ARC_ENTRY_DUPLICATE_IDENTITY",
                scope=SCOPE_PLANNING,
                item=relative_path,
                observed="{0} ArcEntry records name this filename".format(
                    len(by_filename)
                ),
                expected="exactly one ArcEntry per Chapter_File",
                disposition=DISPOSITION_INCOMPLETE,
                related=tuple(entry.identity for entry in by_filename),
            ),
        )
    if by_filename:
        return by_filename[0], ()

    if chapter is None:
        return None, (
            _diagnostic(
                "CHAPTER_ARC_ENTRY_MISSING",
                scope=SCOPE_CHAPTER,
                item=relative_path,
                observed=(
                    "no ArcEntry names this filename and no chapter "
                    "number resolved"
                ),
                expected="exactly one matching ArcEntry",
                disposition=DISPOSITION_INCOMPLETE,
            ),
        )

    by_chapter = [entry for entry in entries if entry.chapter == chapter]
    if len(by_chapter) > 1:
        return None, (
            _diagnostic(
                "ARC_ENTRY_DUPLICATE_IDENTITY",
                scope=SCOPE_PLANNING,
                item=relative_path,
                observed="{0} ArcEntry records claim chapter {1}".format(
                    len(by_chapter), chapter
                ),
                expected="exactly one ArcEntry per chapter number",
                disposition=DISPOSITION_INCOMPLETE,
                related=tuple(entry.identity for entry in by_chapter),
            ),
        )
    if not by_chapter:
        return None, (
            _diagnostic(
                "CHAPTER_ARC_ENTRY_MISSING",
                scope=SCOPE_CHAPTER,
                item=relative_path,
                observed="no ArcEntry names this filename or claims chapter {0}".format(
                    chapter
                ),
                expected="exactly one matching ArcEntry",
                disposition=DISPOSITION_INCOMPLETE,
            ),
        )

    entry = by_chapter[0]
    return entry, (
        _diagnostic(
            "CHAPTER_ARC_ENTRY_FILENAME_DISAGREEMENT",
            scope=SCOPE_CHAPTER,
            item=relative_path,
            observed="ArcEntry filename={0!r}".format(entry.filename),
            expected="the Chapter_File's manuscript-relative path",
            related=(entry.identity,),
        ),
    )


# ---------------------------------------------------------------------------
# The four-way filename/directory/header/ArcEntry agreement rule
# ---------------------------------------------------------------------------


def check_chapter_agreement(
    document: ChapterDocument, arc_entry: Optional[ArcEntryRecord] = None
) -> Tuple[CheckerDiagnostic, ...]:
    """Validate movement and global-sequence agreement across all four sources.

    The four sources are the containing directory, the filename, the
    Chapter_Header, and the matching ArcEntry. Any disagreement is an objective
    violation. The global sequence never resets at a movement boundary, so the
    filename's three digits are compared directly with the header and outline
    chapter numbers. Hook, status, Timeline_ID, and POV_ID agreement is
    Requirement 12.5's and belongs to task 7.3.
    """

    diagnostics: List[CheckerDiagnostic] = []
    item = document.relative_path
    directory = document.directory
    directory_movement: Optional[str] = None

    directory_path = PurePosixPath(directory)
    if directory_path.parent.name == CHAPTERS_DIRECTORY:
        directory_movement = movement_from_directory_slug(directory_path.name)
    if directory_movement is None:
        diagnostics.append(
            _diagnostic(
                "CHAPTER_DIRECTORY_MISMATCH",
                scope=SCOPE_CHAPTER,
                item=item,
                observed=directory or ".",
                expected="chapters/<movement-slug> for one of the four movements",
            )
        )

    if document.filename is None:
        diagnostics.append(
            _diagnostic(
                "CHAPTER_FILENAME_MALFORMED",
                scope=SCOPE_CHAPTER,
                item=item,
                observed=document.basename,
                expected="<movement>-<three-digit-global-sequence>-<slug>.md",
            )
        )

    movement_claims: List[Tuple[str, str]] = []
    if directory_movement is not None:
        movement_claims.append(("directory", directory_movement))
    if document.filename is not None:
        movement_claims.append(("filename", document.filename.movement))
    if "movement" in document.header:
        movement_claims.append(("header", document.header["movement"]))
    if arc_entry is not None and arc_entry.movement is not None:
        movement_claims.append(("arc_entry", arc_entry.movement))

    if len({value for _source, value in movement_claims}) > 1:
        diagnostics.append(
            _diagnostic(
                "CHAPTER_MOVEMENT_DISAGREEMENT",
                scope=SCOPE_CHAPTER,
                item=item,
                observed=", ".join(
                    "{0}={1}".format(source, value) for source, value in movement_claims
                ),
                expected=(
                    "one movement agreed by directory, filename, header, "
                    "and ArcEntry"
                ),
            )
        )

    sequence_claims: List[Tuple[str, int]] = []
    if document.filename is not None:
        sequence_claims.append(("filename", document.filename.sequence))
    if "chapter" in document.header:
        sequence_claims.append(("header", document.header["chapter"]))
    if arc_entry is not None and arc_entry.chapter is not None:
        sequence_claims.append(("arc_entry", arc_entry.chapter))

    if len({value for _source, value in sequence_claims}) > 1:
        diagnostics.append(
            _diagnostic(
                "CHAPTER_SEQUENCE_DISAGREEMENT",
                scope=SCOPE_CHAPTER,
                item=item,
                observed=", ".join(
                    "{0}={1}".format(source, value) for source, value in sequence_claims
                ),
                expected=(
                    "one global chapter number agreed by filename, header, and "
                    "ArcEntry, never reset at a movement boundary"
                ),
            )
        )

    return tuple(diagnostics)


# ---------------------------------------------------------------------------
# Direct-reference index (task 7.3)
#
# Validation order follows `record-schemas.md`: parse without inference, check
# each record structurally, build the ID indexes, reject duplicate identities,
# and only then resolve references. Duplicate identity is therefore detected
# before any reference resolves, and a reference into a duplicated ID reports the
# duplicate rather than a second, misleading dangling error.
# ---------------------------------------------------------------------------


def _is_nonblank_string(value: Any) -> bool:
    return isinstance(value, str) and bool(_normalized_text(value).strip())


def _stable_id(value: Any) -> Optional[str]:
    """The normalized `StableID` a value carries, or `None` when it is not one."""

    if not isinstance(value, str):
        return None
    candidate = _normalized_text(value).strip()
    if STABLE_ID_PATTERN.match(candidate) is None:
        return None
    return candidate


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _is_chapter_number(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value >= 1


def _key_set_report(payload: Mapping[str, Any], expected: Sequence[str]) -> str:
    missing = [key for key in expected if key not in payload]
    unexpected = sorted(key for key in payload if key not in expected)
    parts = []
    if missing:
        parts.append("missing={0}".format(", ".join(missing)))
    if unexpected:
        parts.append("unexpected={0}".format(", ".join(unexpected)))
    return "; ".join(parts)


@dataclass(frozen=True)
class ReferenceIndex:
    """Every stable ID a chapter's direct references can resolve against.

    `records` holds every parsed record by type, including the types this task
    does not resolve, so a later task can index them without reparsing.
    `by_id` maps each indexed record type's ID to *every* record claiming it, so
    a duplicate identity stays visible instead of being silently collapsed.
    """

    sources: Tuple[str, ...] = ()
    records: Mapping[str, Tuple[PlanningRecord, ...]] = field(default_factory=dict)
    by_id: Mapping[str, Mapping[str, Tuple[PlanningRecord, ...]]] = field(
        default_factory=dict
    )
    arc_entries: Tuple[ArcEntryRecord, ...] = ()
    arc_entry_by_chapter: Mapping[int, Tuple[ArcEntryRecord, ...]] = field(
        default_factory=dict
    )
    character_ids: Tuple[str, ...] = ()
    duplicate_character_ids: Tuple[str, ...] = ()

    def of_type(self, record_type: str) -> Tuple[PlanningRecord, ...]:
        return tuple(self.records.get(record_type, ()))

    def lookup(self, record_type: str, record_id: str) -> Tuple[PlanningRecord, ...]:
        return tuple(self.by_id.get(record_type, {}).get(record_id, ()))

    def unique(self, record_type: str, record_id: str) -> Optional[PlanningRecord]:
        """The one record claiming `record_id`, or `None` when it is not unique."""

        matches = self.lookup(record_type, record_id)
        return matches[0] if len(matches) == 1 else None

    def is_duplicated(self, record_type: str, record_id: str) -> bool:
        return len(self.lookup(record_type, record_id)) > 1

    def is_known_character(self, character_id: str) -> bool:
        return character_id in self.character_ids

    def arc_entry_for_chapter(self, chapter: int) -> Optional[ArcEntryRecord]:
        matches = self.arc_entry_by_chapter.get(chapter, ())
        return matches[0] if len(matches) == 1 else None

    def movement_for_chapter(self, chapter: int) -> Optional[str]:
        entry = self.arc_entry_for_chapter(chapter)
        return None if entry is None else entry.movement

    def declared_cross_cuts(self) -> Mapping[str, Tuple[int, ...]]:
        """Cross_Cut ID to the sorted chapters whose ArcEntry declares it."""

        declared: Dict[str, List[int]] = {}
        for entry in self.arc_entries:
            if entry.chapter is None:
                continue
            value = entry.payload.get("cross_cuts")
            if not isinstance(value, list):
                continue
            for item in value:
                cross_cut_id = _stable_id(item)
                if cross_cut_id is not None:
                    declared.setdefault(cross_cut_id, []).append(entry.chapter)
        return {
            cross_cut_id: tuple(sorted(set(chapters)))
            for cross_cut_id, chapters in declared.items()
        }


def _character_name_extension_id(record: PlanningRecord) -> Optional[str]:
    """The Character ID a `character-name` extension declares, read from `fact`.

    The registry rule is explicit: the ID is the first whitespace-delimited token
    of the record's own `fact` field and must satisfy `StableID`. It is never
    taken from a heading, table, list, or sentence of commentary.
    """

    fact = record.payload.get("fact")
    if not isinstance(fact, str):
        return None
    tokens = _normalized_text(fact).split()
    if not tokens:
        return None
    return _stable_id(tokens[0])


def build_reference_index(
    grouped: Mapping[str, Sequence[PlanningRecord]],
    *,
    sources: Sequence[str] = (),
    arc_entries: Sequence[ArcEntryRecord] = (),
) -> Tuple[ReferenceIndex, Tuple[CheckerDiagnostic, ...]]:
    """Index stable IDs and reject duplicate identities before resolution."""

    diagnostics: List[CheckerDiagnostic] = []
    by_id: Dict[str, Dict[str, Tuple[PlanningRecord, ...]]] = {}

    for record_type, id_field in sorted(RECORD_ID_FIELDS.items()):
        collected: Dict[str, List[PlanningRecord]] = {}
        for record in grouped.get(record_type, ()):
            record_id = _stable_id(record.payload.get(id_field))
            if record_id is None:
                diagnostics.append(
                    record.malformed(
                        "RECORD_ID_MALFORMED",
                        observed="{0}={1!r}".format(
                            id_field, record.payload.get(id_field)
                        ),
                        expected="a StableID matching " + STABLE_ID_PATTERN.pattern,
                    )
                )
                continue
            collected.setdefault(record_id, []).append(record)
        for record_id in sorted(collected):
            claimants = collected[record_id]
            if len(claimants) > 1:
                diagnostics.append(
                    _diagnostic(
                        "RECORD_DUPLICATE_IDENTITY",
                        scope=SCOPE_PLANNING,
                        item=record_id,
                        observed="{0} {1} records claim this ID".format(
                            len(claimants), record_type
                        ),
                        expected="exactly one {0} per stable ID".format(record_type),
                        disposition=DISPOSITION_INCOMPLETE,
                        related=tuple(record.identity for record in claimants),
                    )
                )
        by_id[record_type] = {
            record_id: tuple(claimants)
            for record_id, claimants in collected.items()
        }

    # --- Character ID registry: POVProfile IDs union approved character-name
    # extension IDs. A single ID declared by both is one character.
    profile_characters: Dict[str, List[PlanningRecord]] = {}
    for record in grouped.get("POVProfile", ()):
        character_id = _stable_id(record.payload.get("character_id"))
        if character_id is None:
            diagnostics.append(
                record.malformed(
                    "RECORD_ID_MALFORMED",
                    observed="character_id={0!r}".format(
                        record.payload.get("character_id")
                    ),
                    expected="a StableID matching " + STABLE_ID_PATTERN.pattern,
                )
            )
            continue
        profile_characters.setdefault(character_id, []).append(record)

    extension_characters: Dict[str, List[PlanningRecord]] = {}
    for record in grouped.get("NovelExtension", ()):
        if record.payload.get("extension_kind") != "character-name":
            continue
        if record.payload.get("state") != "approved":
            # A `provisional` extension declares no resolvable ID yet and a
            # `retired` one declares none any longer.
            continue
        character_id = _character_name_extension_id(record)
        if character_id is None:
            diagnostics.append(
                record.malformed(
                    "CHARACTER_NAME_EXTENSION_MALFORMED",
                    observed="fact={0!r}".format(record.payload.get("fact")),
                    expected=(
                        "a fact whose first whitespace-delimited token is the "
                        "declared Character StableID"
                    ),
                )
            )
            continue
        extension_characters.setdefault(character_id, []).append(record)

    duplicate_character_ids: List[str] = []
    for character_id in sorted(set(profile_characters) | set(extension_characters)):
        profiles = profile_characters.get(character_id, [])
        extensions = extension_characters.get(character_id, [])
        if len(profiles) > 1 or len(extensions) > 1:
            duplicate_character_ids.append(character_id)
            diagnostics.append(
                _diagnostic(
                    "CHARACTER_ID_DUPLICATE_IDENTITY",
                    scope=SCOPE_PLANNING,
                    item=character_id,
                    observed="{0} POVProfile and {1} character-name records "
                    "declare this Character ID".format(len(profiles), len(extensions)),
                    expected=(
                        "at most one POVProfile and at most one approved "
                        "character-name extension per Character ID"
                    ),
                    disposition=DISPOSITION_INCOMPLETE,
                    related=tuple(
                        record.identity for record in list(profiles) + list(extensions)
                    ),
                )
            )
            continue
        if profiles and extensions:
            selected_name = profiles[0].payload.get("selected_name")
            fact = extensions[0].payload.get("fact")
            if _is_nonblank_string(selected_name) and isinstance(fact, str):
                if _normalized_text(selected_name) not in _normalized_text(fact):
                    diagnostics.append(
                        extensions[0].violation(
                            "CHARACTER_NAME_EXTENSION_DISAGREEMENT",
                            item=character_id,
                            observed="fact does not state selected_name "
                            "{0!r}".format(selected_name),
                            expected=(
                                "the extension agrees with the POVProfile's "
                                "selected_name"
                            ),
                            related=(
                                extensions[0].identity,
                                profiles[0].identity,
                            ),
                        )
                    )

    character_ids = tuple(sorted(set(profile_characters) | set(extension_characters)))

    # --- POVProfile bijection and the one-to-one VoiceBrief obligation. Both are
    # rules about profiles, never about the registry as a whole: a non-viewpoint
    # Character ID with no profile violates neither.
    voice_brief_claims: Dict[str, List[PlanningRecord]] = {}
    for record in grouped.get("POVProfile", ()):
        voice_brief_id = _stable_id(record.payload.get("voice_brief_id"))
        if voice_brief_id is not None:
            voice_brief_claims.setdefault(voice_brief_id, []).append(record)
    for voice_brief_id in sorted(voice_brief_claims):
        claimants = voice_brief_claims[voice_brief_id]
        if len(claimants) > 1:
            diagnostics.append(
                _diagnostic(
                    "VOICE_BRIEF_MANY_TO_ONE",
                    scope=SCOPE_PLANNING,
                    item=voice_brief_id,
                    observed="{0} POVProfile records name this VoiceBrief".format(
                        len(claimants)
                    ),
                    expected="one VoiceBrief per POVProfile, one-to-one",
                    related=tuple(record.identity for record in claimants),
                )
            )

    # --- ArcEntry identity. `chapter` and `filename` are independently unique.
    # `match_arc_entry` also rejects a duplicate for a Chapter_File it is asked
    # about; this catches the same fault across the whole outline, including
    # entries whose file does not exist yet. Both report `incomplete`, so a
    # duplicate can never be mistaken for an ordinary violation either way.
    arc_entry_by_chapter: Dict[int, List[ArcEntryRecord]] = {}
    arc_entry_by_filename: Dict[str, List[ArcEntryRecord]] = {}
    for entry in arc_entries:
        if entry.chapter is not None:
            arc_entry_by_chapter.setdefault(entry.chapter, []).append(entry)
        if entry.filename is not None:
            arc_entry_by_filename.setdefault(entry.filename, []).append(entry)
    for chapter in sorted(arc_entry_by_chapter):
        claimants = arc_entry_by_chapter[chapter]
        if len(claimants) > 1:
            diagnostics.append(
                _diagnostic(
                    "ARC_ENTRY_DUPLICATE_IDENTITY",
                    scope=SCOPE_PLANNING,
                    item="chapter {0}".format(chapter),
                    observed="{0} ArcEntry records claim this chapter".format(
                        len(claimants)
                    ),
                    expected="exactly one ArcEntry per chapter number",
                    disposition=DISPOSITION_INCOMPLETE,
                    related=tuple(entry.identity for entry in claimants),
                )
            )
    for filename in sorted(arc_entry_by_filename):
        claimants = arc_entry_by_filename[filename]
        if len(claimants) > 1:
            diagnostics.append(
                _diagnostic(
                    "ARC_ENTRY_DUPLICATE_IDENTITY",
                    scope=SCOPE_PLANNING,
                    item=filename,
                    observed="{0} ArcEntry records name this filename".format(
                        len(claimants)
                    ),
                    expected="exactly one ArcEntry per Chapter_File",
                    disposition=DISPOSITION_INCOMPLETE,
                    related=tuple(entry.identity for entry in claimants),
                )
            )

    index = ReferenceIndex(
        sources=tuple(sources),
        records={
            record_type: tuple(items) for record_type, items in grouped.items()
        },
        by_id=by_id,
        arc_entries=tuple(arc_entries),
        arc_entry_by_chapter={
            chapter: tuple(items) for chapter, items in arc_entry_by_chapter.items()
        },
        character_ids=character_ids,
        duplicate_character_ids=tuple(duplicate_character_ids),
    )
    return index, tuple(diagnostics)


def load_reference_index(
    manuscript_root: Path, *, sources: Sequence[str] = DEFAULT_RECORD_SOURCES
) -> Tuple[ReferenceIndex, Tuple[CheckerDiagnostic, ...]]:
    """Read the allowlisted record sources and index their stable IDs.

    `sources` is an explicit allowlist rather than a directory glob. Scoping by
    glob would ingest the illustrative `EXAMPLE` records in `record-schemas.md`,
    which that document gives no continuity authority, and manufacture phantom
    duplicate identities and dangling IDs from them.
    """

    root = Path(manuscript_root)
    grouped: Dict[str, List[PlanningRecord]] = {}
    diagnostics: List[CheckerDiagnostic] = []
    loaded: List[str] = []

    for relative in sources:
        path = root.joinpath(*relative.split("/"))
        if not path.is_file():
            diagnostics.append(
                _diagnostic(
                    "PLANNING_DOCUMENT_MISSING",
                    scope=SCOPE_PLANNING,
                    item=relative,
                    observed="no readable file at this path",
                    expected="an allowlisted record source document",
                    disposition=DISPOSITION_INCOMPLETE,
                )
            )
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as exc:
            diagnostics.append(
                _diagnostic(
                    "PLANNING_DOCUMENT_UNREADABLE",
                    scope=SCOPE_PLANNING,
                    item=relative,
                    observed=str(exc),
                    expected="readable UTF-8 text",
                    disposition=DISPOSITION_INCOMPLETE,
                )
            )
            continue
        loaded.append(relative)
        document_records, document_diagnostics = parse_planning_records(
            text, source=relative
        )
        diagnostics.extend(document_diagnostics)
        for record_type, items in document_records.items():
            grouped.setdefault(record_type, []).extend(items)

    arc_entries: List[ArcEntryRecord] = []
    for record in grouped.get("ArcEntry", ()):
        entry, entry_diagnostics = _build_arc_entry(record)
        diagnostics.extend(entry_diagnostics)
        if entry is not None:
            arc_entries.append(entry)

    index, index_diagnostics = build_reference_index(
        grouped, sources=loaded, arc_entries=arc_entries
    )
    return index, tuple(diagnostics) + index_diagnostics


# ---------------------------------------------------------------------------
# Reference resolution
# ---------------------------------------------------------------------------


def _resolve_reference(
    index: ReferenceIndex,
    record_type: str,
    value: Any,
    *,
    scope: str,
    item: str,
    field_name: str,
    related: Sequence[str] = (),
) -> Tuple[Optional[PlanningRecord], Tuple[CheckerDiagnostic, ...]]:
    """Resolve one stable-ID reference to exactly one target of the right type.

    A malformed ID is reported as incomplete input. A duplicated target was
    already reported at index build time, so this reports nothing further and
    resolves to nothing. Everything else that fails to resolve is a dangling
    reference and an ordinary objective violation.
    """

    record_id = _stable_id(value)
    if record_id is None:
        return None, (
            _diagnostic(
                "REFERENCE_MALFORMED",
                scope=scope,
                item=item,
                observed="{0}={1!r}".format(field_name, value),
                expected="a StableID matching " + STABLE_ID_PATTERN.pattern,
                disposition=DISPOSITION_INCOMPLETE,
                related=related,
            ),
        )
    if index.is_duplicated(record_type, record_id):
        return None, ()
    target = index.unique(record_type, record_id)
    if target is None:
        return None, (
            _diagnostic(
                REFERENCE_DANGLING_CODES.get(
                    record_type, "REFERENCE_DANGLING"
                ),
                scope=scope,
                item=item,
                observed="{0}={1} resolves to no {2}".format(
                    field_name, record_id, record_type
                ),
                expected="exactly one {0} with this stable ID".format(record_type),
                related=related,
            ),
        )
    return target, ()


def check_character_references(
    index: ReferenceIndex,
) -> Tuple[CheckerDiagnostic, ...]:
    """Resolve every Character ID reference against the registry union.

    The union is `POVProfile.character_id` plus the ID declared by every approved
    `character-name` extension, so a reference to a non-viewpoint character
    resolves instead of dangling. Reveal knowledge arrays are deliberately left
    to the task that indexes `Reveal` records.
    """

    diagnostics: List[CheckerDiagnostic] = []

    def _resolve(record: PlanningRecord, value: Any, field_name: str) -> None:
        character_id = _stable_id(value)
        if character_id is None:
            diagnostics.append(
                record.malformed(
                    "REFERENCE_MALFORMED",
                    observed="{0}={1!r}".format(field_name, value),
                    expected="a Character StableID",
                )
            )
            return
        if character_id in index.duplicate_character_ids:
            return
        if not index.is_known_character(character_id):
            diagnostics.append(
                record.violation(
                    "CHARACTER_REFERENCE_DANGLING",
                    observed="{0}={1} resolves to no Character ID".format(
                        field_name, character_id
                    ),
                    expected=(
                        "one POVProfile character_id or one approved "
                        "character-name extension"
                    ),
                )
            )

    for record in index.of_type("TimelineEntry"):
        participants = record.payload.get("participants")
        if not isinstance(participants, list):
            diagnostics.append(
                record.malformed(
                    "TIMELINE_ENTRY_MALFORMED",
                    observed="participants={0!r}".format(participants),
                    expected="an array of unique Character StableIDs",
                )
            )
            continue
        for value in participants:
            _resolve(record, value, "participants[]")
        state = record.payload.get("technical_state")
        if not isinstance(state, dict):
            continue
        pair_state = state.get("pair_state")
        if isinstance(pair_state, dict):
            for key in ("participants", "calibration_participants"):
                members = pair_state.get(key)
                if isinstance(members, list):
                    for value in members:
                        _resolve(record, value, "pair_state.{0}[]".format(key))
        cancel_state = state.get("cancel_state")
        if isinstance(cancel_state, dict):
            consent = cancel_state.get("individual_consent")
            if isinstance(consent, dict):
                _resolve(
                    record,
                    consent.get("character_id"),
                    "cancel_state.individual_consent.character_id",
                )

    for record in index.of_type("POVProfile"):
        relationships = record.payload.get("relationships")
        if not isinstance(relationships, list):
            continue
        for member in relationships:
            if isinstance(member, dict):
                _resolve(record, member.get("character_id"), "relationships[]")

    return tuple(diagnostics)


def check_pov_voice_brief_pairing(
    index: ReferenceIndex,
) -> Tuple[CheckerDiagnostic, ...]:
    """Resolve each profile's VoiceBrief and require the reciprocal `pov_id`."""

    diagnostics: List[CheckerDiagnostic] = []
    for record in index.of_type("POVProfile"):
        pov_id = _stable_id(record.payload.get("pov_id"))
        brief, reference_diagnostics = _resolve_reference(
            index,
            "VoiceBrief",
            record.payload.get("voice_brief_id"),
            scope=SCOPE_PLANNING,
            item=pov_id or record.identity,
            field_name="voice_brief_id",
            related=(record.identity,),
        )
        diagnostics.extend(reference_diagnostics)
        if brief is None or pov_id is None:
            continue
        back_reference = _stable_id(brief.payload.get("pov_id"))
        if back_reference != pov_id:
            diagnostics.append(
                brief.violation(
                    "VOICE_BRIEF_POV_DISAGREEMENT",
                    observed="VoiceBrief pov_id={0!r}".format(
                        brief.payload.get("pov_id")
                    ),
                    expected="the same POV_ID as the profile naming this brief",
                    related=(brief.identity, record.identity),
                )
            )
    return tuple(diagnostics)


# ---------------------------------------------------------------------------
# `TimelineEntry.technical_state`: the closed four-mode invariant table
#
# Mechanism state is read from `technical_state` fields alone. `evidence_scope`
# and `uncertainty_notes` are prose commentary and are never read as mechanism
# state, and no mode is ever inferred from `apparatus_mode` or from a nearby
# heading. For a bounded-consent `CANCEL` entry this checker validates the
# objective consent and scope state only; whether the scene works dramatically
# is Editorial_Review's alone.
# ---------------------------------------------------------------------------

_MODE_TRANSMIT_STAGE: Mapping[str, bool] = {
    "RECEIVE": False,
    "INTRUDE": True,
    "CANCEL": True,
    "PAIR": True,
}
_MODE_REQUIRED_OBJECTS: Mapping[str, Tuple[str, ...]] = {
    "RECEIVE": (),
    "INTRUDE": (),
    "CANCEL": ("cancel_state",),
    "PAIR": ("pair_state", "pairing_evidence"),
    "not-applicable": (),
}
_MODE_NULL_OBJECTS: Mapping[str, Tuple[str, ...]] = {
    "RECEIVE": ("cancel_state", "pair_state", "pairing_evidence"),
    "INTRUDE": ("cancel_state", "pair_state", "pairing_evidence"),
    "CANCEL": ("pair_state", "pairing_evidence"),
    "PAIR": ("cancel_state",),
    "not-applicable": ("cancel_state", "pair_state", "pairing_evidence"),
}


def _check_cancel_state(
    entry: PlanningRecord,
    cancel_state: Mapping[str, Any],
    *,
    index: Optional[ReferenceIndex],
) -> Tuple[CheckerDiagnostic, ...]:
    diagnostics: List[CheckerDiagnostic] = []
    report = _key_set_report(cancel_state, CANCEL_STATE_KEYS)
    if report:
        diagnostics.append(
            entry.malformed(
                "CANCEL_STATE_MALFORMED",
                observed=report,
                expected="exactly " + ", ".join(CANCEL_STATE_KEYS),
            )
        )
        return tuple(diagnostics)

    scope_value = cancel_state.get("scope")
    if scope_value not in CANCEL_SCOPES:
        diagnostics.append(
            entry.malformed(
                "CANCEL_STATE_MALFORMED",
                observed="scope={0!r}".format(scope_value),
                expected="one of " + ", ".join(CANCEL_SCOPES),
            )
        )
        scope_value = None

    consent = cancel_state.get("individual_consent")
    authorization = cancel_state.get("institutional_authorization")

    if consent is not None:
        if not isinstance(consent, dict):
            diagnostics.append(
                entry.malformed(
                    "CANCEL_STATE_MALFORMED",
                    observed="individual_consent has type {0}".format(
                        type(consent).__name__
                    ),
                    expected="an object or null",
                )
            )
            consent = None
        else:
            consent_report = _key_set_report(consent, INDIVIDUAL_CONSENT_KEYS)
            if consent_report:
                diagnostics.append(
                    entry.malformed(
                        "CANCEL_STATE_MALFORMED",
                        observed="individual_consent " + consent_report,
                        expected="exactly " + ", ".join(INDIVIDUAL_CONSENT_KEYS),
                    )
                )
            else:
                for key in ("current", "revocable"):
                    if consent.get(key) is not True:
                        diagnostics.append(
                            entry.violation(
                                "CANCEL_STATE_INVARIANT",
                                observed="individual_consent.{0}={1!r}".format(
                                    key, consent.get(key)
                                ),
                                expected="current specific revocable consent",
                            )
                        )
                if not _is_nonblank_string(consent.get("specific_act")):
                    diagnostics.append(
                        entry.violation(
                            "CANCEL_STATE_INVARIANT",
                            observed="individual_consent.specific_act={0!r}".format(
                                consent.get("specific_act")
                            ),
                            expected="a nonblank specific consented act",
                        )
                    )

    if authorization is not None and not _is_nonblank_string(authorization):
        diagnostics.append(
            entry.malformed(
                "CANCEL_STATE_MALFORMED",
                observed="institutional_authorization={0!r}".format(authorization),
                expected="a nonblank authorizing body and instrument, or null",
            )
        )

    if scope_value == "bounded-local":
        if consent is None:
            diagnostics.append(
                entry.violation(
                    "CANCEL_STATE_INVARIANT",
                    observed="bounded-local scope with individual_consent=null",
                    expected=(
                        "the deliberately exposed individual's current specific "
                        "revocable consent"
                    ),
                )
            )
        if authorization is not None:
            diagnostics.append(
                entry.violation(
                    "CANCEL_STATE_INVARIANT",
                    observed="bounded-local scope with institutional_authorization",
                    expected="institutional_authorization null at bounded-local scope",
                )
            )
    elif scope_value == "area-scale":
        if consent is not None:
            diagnostics.append(
                entry.violation(
                    "CANCEL_STATE_INVARIANT",
                    observed="area-scale scope with individual_consent",
                    expected=(
                        "institutional authorization, never individual consent "
                        "collected from every affected person"
                    ),
                )
            )
        if authorization is None:
            diagnostics.append(
                entry.violation(
                    "CANCEL_STATE_INVARIANT",
                    observed="area-scale scope with institutional_authorization=null",
                    expected="the authorizing body and instrument",
                )
            )

    if not _is_nonblank_string(cancel_state.get("subtraction")):
        diagnostics.append(
            entry.malformed(
                "CANCEL_STATE_MALFORMED",
                observed="subtraction={0!r}".format(cancel_state.get("subtraction")),
                expected="a nonblank description of the removal or degradation",
            )
        )

    for key in CANCEL_NONE_KEYS:
        if cancel_state.get(key) != "none":
            diagnostics.append(
                entry.violation(
                    "CANCEL_STATE_INVARIANT",
                    observed="{0}={1!r}".format(key, cancel_state.get(key)),
                    expected="exactly none",
                )
            )
    for key in CANCEL_FALSE_KEYS:
        if cancel_state.get(key) is not False:
            diagnostics.append(
                entry.violation(
                    "CANCEL_STATE_INVARIANT",
                    observed="{0}={1!r}".format(key, cancel_state.get(key)),
                    expected="exactly false",
                )
            )

    # Requirement 14.5: a `CANCEL` event is placed within the Mindwars_Part. The
    # movement comes from each chapter's ArcEntry, so the rule is only evaluated
    # where the outline actually resolves the chapter.
    if index is not None:
        chapters = entry.payload.get("chapter_numbers")
        if isinstance(chapters, list):
            outside = [
                number
                for number in chapters
                if _is_chapter_number(number)
                and index.movement_for_chapter(number) not in (None, MINDWARS_MOVEMENT)
            ]
            if outside:
                diagnostics.append(
                    entry.violation(
                        "CANCEL_CHAPTER_OUTSIDE_MINDWARS",
                        observed="chapters {0} lie outside the Mindwars block".format(
                            ", ".join(str(number) for number in sorted(outside))
                        ),
                        expected="every chapter_numbers member inside mindwars_part",
                    )
                )
    return tuple(diagnostics)


def _check_pair_state(
    entry: PlanningRecord, pair_state: Mapping[str, Any]
) -> Tuple[CheckerDiagnostic, ...]:
    diagnostics: List[CheckerDiagnostic] = []
    report = _key_set_report(pair_state, PAIR_STATE_KEYS)
    if report:
        diagnostics.append(
            entry.malformed(
                "PAIR_STATE_MALFORMED",
                observed=report,
                expected="exactly " + ", ".join(PAIR_STATE_KEYS),
            )
        )
        return tuple(diagnostics)

    participants = pair_state.get("participants")
    calibration_participants = pair_state.get("calibration_participants")
    for key, members in (
        ("participants", participants),
        ("calibration_participants", calibration_participants),
    ):
        if (
            not isinstance(members, list)
            or len(members) != 2
            or any(_stable_id(member) is None for member in members)
            or len({_stable_id(member) for member in members}) != 2
        ):
            diagnostics.append(
                entry.malformed(
                    "PAIR_STATE_MALFORMED",
                    observed="{0}={1!r}".format(key, members),
                    expected="exactly two distinct Character StableIDs",
                )
            )
    if isinstance(participants, list) and isinstance(calibration_participants, list):
        if {_stable_id(member) for member in participants} != {
            _stable_id(member) for member in calibration_participants
        }:
            diagnostics.append(
                entry.violation(
                    "PAIR_STATE_INVARIANT",
                    observed="calibration_participants={0!r} participants={1!r}".format(
                        calibration_participants, participants
                    ),
                    expected="calibration_participants equals participants as a set",
                )
            )

    consent = pair_state.get("consent")
    if not isinstance(consent, dict):
        diagnostics.append(
            entry.malformed(
                "PAIR_STATE_MALFORMED",
                observed="consent has type {0}".format(type(consent).__name__),
                expected="an object with exactly " + ", ".join(PAIR_CONSENT_KEYS),
            )
        )
    else:
        consent_report = _key_set_report(consent, PAIR_CONSENT_KEYS)
        if consent_report:
            diagnostics.append(
                entry.malformed(
                    "PAIR_STATE_MALFORMED",
                    observed="consent " + consent_report,
                    expected="exactly " + ", ".join(PAIR_CONSENT_KEYS),
                )
            )
        else:
            for key in ("current", "revocable", "authorized_a", "authorized_b"):
                if consent.get(key) is not True:
                    diagnostics.append(
                        entry.violation(
                            "PAIR_STATE_INVARIANT",
                            observed="consent.{0}={1!r}".format(key, consent.get(key)),
                            expected=(
                                "current specific revocable mutual consent for an "
                                "authorized session"
                            ),
                        )
                    )
            if not _is_nonblank_string(consent.get("specific_act")):
                diagnostics.append(
                    entry.violation(
                        "PAIR_STATE_INVARIANT",
                        observed="consent.specific_act={0!r}".format(
                            consent.get("specific_act")
                        ),
                        expected="a nonblank specific consented act",
                    )
                )

    if _stable_id(pair_state.get("calibration_id")) is None:
        diagnostics.append(
            entry.malformed(
                "PAIR_STATE_MALFORMED",
                observed="calibration_id={0!r}".format(pair_state.get("calibration_id")),
                expected="a StableID unique to this pair",
            )
        )
    if pair_state.get("calibration_transferable") is not False:
        diagnostics.append(
            entry.violation(
                "PAIR_STATE_INVARIANT",
                observed="calibration_transferable={0!r}".format(
                    pair_state.get("calibration_transferable")
                ),
                expected="exactly false",
            )
        )
    if pair_state.get("deliberate_send_state") not in DELIBERATE_SEND_STATES:
        diagnostics.append(
            entry.malformed(
                "PAIR_STATE_MALFORMED",
                observed="deliberate_send_state={0!r}".format(
                    pair_state.get("deliberate_send_state")
                ),
                expected="one of " + ", ".join(DELIBERATE_SEND_STATES),
            )
        )
    return tuple(diagnostics)


def _check_pairing_evidence(
    entry: PlanningRecord, evidence: Mapping[str, Any]
) -> Tuple[CheckerDiagnostic, ...]:
    diagnostics: List[CheckerDiagnostic] = []
    report = _key_set_report(evidence, PAIRING_EVIDENCE_KEYS)
    if report:
        diagnostics.append(
            entry.malformed(
                "PAIRING_EVIDENCE_MALFORMED",
                observed=report,
                expected="exactly " + ", ".join(PAIRING_EVIDENCE_KEYS),
            )
        )
        return tuple(diagnostics)

    for key in PAIRING_EVIDENCE_TRUE_KEYS:
        if evidence.get(key) is not True:
            diagnostics.append(
                entry.violation(
                    "PAIRING_EVIDENCE_INVARIANT",
                    observed="{0}={1!r}".format(key, evidence.get(key)),
                    expected="exactly true",
                )
            )
    for key in (
        "content_recording_enabled",
        "recording_consent_a",
        "recording_consent_b",
    ):
        if not _is_bool(evidence.get(key)):
            diagnostics.append(
                entry.malformed(
                    "PAIRING_EVIDENCE_MALFORMED",
                    observed="{0}={1!r}".format(key, evidence.get(key)),
                    expected="a boolean",
                )
            )

    recording = evidence.get("content_recording_enabled")
    both_consented = (
        evidence.get("recording_consent_a") is True
        and evidence.get("recording_consent_b") is True
    )
    if recording is True and not both_consented:
        diagnostics.append(
            entry.violation(
                "PAIRING_EVIDENCE_INVARIANT",
                observed="content_recording_enabled=True with "
                "recording_consent_a={0!r} recording_consent_b={1!r}".format(
                    evidence.get("recording_consent_a"),
                    evidence.get("recording_consent_b"),
                ),
                expected=(
                    "explicit mutual recording consent, separate from consent "
                    "to PAIR, before recording is enabled"
                ),
            )
        )

    transcript = evidence.get("transcript")
    if transcript is None:
        return tuple(diagnostics)
    if not isinstance(transcript, dict):
        diagnostics.append(
            entry.malformed(
                "PAIRING_EVIDENCE_MALFORMED",
                observed="transcript has type {0}".format(type(transcript).__name__),
                expected="an object or null",
            )
        )
        return tuple(diagnostics)
    transcript_report = _key_set_report(transcript, TRANSCRIPT_KEYS)
    if transcript_report:
        diagnostics.append(
            entry.malformed(
                "PAIRING_EVIDENCE_MALFORMED",
                observed="transcript " + transcript_report,
                expected="exactly " + ", ".join(TRANSCRIPT_KEYS),
            )
        )
        return tuple(diagnostics)
    if recording is not True:
        diagnostics.append(
            entry.violation(
                "PAIRING_EVIDENCE_INVARIANT",
                observed="transcript present with content_recording_enabled={0!r}".format(
                    recording
                ),
                expected="a transcript only while content recording is enabled",
            )
        )
    session_id = _stable_id(transcript.get("session_timeline_id"))
    own_id = _stable_id(entry.payload.get("timeline_id"))
    if session_id is None or own_id is None or session_id != own_id:
        diagnostics.append(
            entry.violation(
                "PAIRING_EVIDENCE_INVARIANT",
                observed="transcript.session_timeline_id={0!r}".format(
                    transcript.get("session_timeline_id")
                ),
                expected="the owning entry's timeline_id",
            )
        )
    if not _is_nonblank_string(transcript.get("content_scope")):
        diagnostics.append(
            entry.malformed(
                "PAIRING_EVIDENCE_MALFORMED",
                observed="transcript.content_scope={0!r}".format(
                    transcript.get("content_scope")
                ),
                expected=(
                    "a nonblank scope limited to contributions transported by "
                    "the protocol during that recorded session"
                ),
            )
        )
    return tuple(diagnostics)


def check_technical_state(
    entry: PlanningRecord, index: Optional[ReferenceIndex] = None
) -> Tuple[CheckerDiagnostic, ...]:
    """Validate one `TimelineEntry`'s mechanism and pairing state.

    Mechanism and pairing state are fields of the entry, not separate record
    types, so this reads `entry.payload["technical_state"]` and nothing else. A
    present-but-`null` `technical_state` is permitted by the schema and is not
    the pre-amendment case; that case is defined by *omitting* `mode`,
    `cancel_state`, `pair_state`, and `pairing_evidence`, and it reports
    incomplete input rather than inferring a mode.
    """

    payload = entry.payload
    if "technical_state" not in payload:
        return (
            entry.malformed(
                "TIMELINE_TECHNICAL_STATE_MALFORMED",
                observed="required key technical_state is absent",
                expected="the technical-state object or null",
            ),
        )
    state = payload["technical_state"]
    if state is None:
        return ()
    if not isinstance(state, dict):
        return (
            entry.malformed(
                "TIMELINE_TECHNICAL_STATE_MALFORMED",
                observed="technical_state has type {0}".format(type(state).__name__),
                expected="an object or null",
            ),
        )

    absent = [key for key in MECHANISM_AMENDMENT_KEYS if key not in state]
    if absent:
        return (
            entry.malformed(
                "TIMELINE_TECHNICAL_STATE_INCOMPLETE",
                observed="pre-amendment record omits {0}".format(", ".join(absent)),
                expected=(
                    "the 2026-09-11 mechanism fields; a checker reports "
                    "incomplete input rather than inferring a mode"
                ),
            ),
        )

    diagnostics: List[CheckerDiagnostic] = []
    report = _key_set_report(state, TECHNICAL_STATE_KEYS)
    if report:
        diagnostics.append(
            entry.malformed(
                "TIMELINE_TECHNICAL_STATE_MALFORMED",
                observed=report,
                expected="exactly " + ", ".join(TECHNICAL_STATE_KEYS),
            )
        )
        return tuple(diagnostics)

    mode = state.get("mode")
    if mode not in NEURAL_COMMUNICATION_MODES:
        diagnostics.append(
            entry.malformed(
                "TIMELINE_TECHNICAL_STATE_MALFORMED",
                observed="mode={0!r}".format(mode),
                expected="one of " + ", ".join(NEURAL_COMMUNICATION_MODES),
            )
        )
        mode = None

    for key, allowed in (
        ("source_side_continuity", SOURCE_SIDE_CONTINUITY_VALUES),
        ("apparatus_mode", APPARATUS_MODES),
        ("person_specific_address_state", PERSON_SPECIFIC_ADDRESS_STATES),
    ):
        if state.get(key) not in allowed:
            diagnostics.append(
                entry.malformed(
                    "TIMELINE_TECHNICAL_STATE_MALFORMED",
                    observed="{0}={1!r}".format(key, state.get(key)),
                    expected="one of " + ", ".join(allowed),
                )
            )
    offset = state.get("receiver_offset_seconds")
    if offset is not None and (isinstance(offset, bool) or not isinstance(offset, int) or offset < 0):
        diagnostics.append(
            entry.malformed(
                "TIMELINE_TECHNICAL_STATE_MALFORMED",
                observed="receiver_offset_seconds={0!r}".format(offset),
                expected="a nonnegative integer or null",
            )
        )
    transmit = state.get("transmit_stage_present")
    if transmit is not None and not _is_bool(transmit):
        diagnostics.append(
            entry.malformed(
                "TIMELINE_TECHNICAL_STATE_MALFORMED",
                observed="transmit_stage_present={0!r}".format(transmit),
                expected="a boolean or null",
            )
        )
    if not _is_nonblank_string(state.get("evidence_scope")):
        diagnostics.append(
            entry.malformed(
                "TIMELINE_TECHNICAL_STATE_MALFORMED",
                observed="evidence_scope={0!r}".format(state.get("evidence_scope")),
                expected="a nonblank statement of what the entry does not prove",
            )
        )

    if mode is None:
        return tuple(diagnostics)

    # --- the closed four-mode invariant table
    required_transmit = _MODE_TRANSMIT_STAGE.get(mode)
    if required_transmit is not None and transmit is not required_transmit:
        diagnostics.append(
            entry.violation(
                "TIMELINE_MODE_INVARIANT",
                observed="mode={0} transmit_stage_present={1!r}".format(mode, transmit),
                expected="transmit_stage_present is {0}".format(
                    "true" if required_transmit else "false"
                ),
            )
        )
    if mode == "RECEIVE" and state.get("source_side_continuity") != "continuous":
        diagnostics.append(
            entry.violation(
                "TIMELINE_MODE_INVARIANT",
                observed="mode=RECEIVE source_side_continuity={0!r}".format(
                    state.get("source_side_continuity")
                ),
                expected="source_side_continuity is continuous",
            )
        )
    if mode == "INTRUDE" and state.get("person_specific_address_state") not in ADDRESSED_STATES:
        diagnostics.append(
            entry.violation(
                "TIMELINE_MODE_INVARIANT",
                observed="mode=INTRUDE person_specific_address_state={0!r}".format(
                    state.get("person_specific_address_state")
                ),
                expected="one of " + ", ".join(ADDRESSED_STATES),
            )
        )
    if mode == "CANCEL" and state.get("person_specific_address_state") != "not-applicable":
        diagnostics.append(
            entry.violation(
                "TIMELINE_MODE_INVARIANT",
                observed="mode=CANCEL person_specific_address_state={0!r}".format(
                    state.get("person_specific_address_state")
                ),
                expected=(
                    "exactly not-applicable; CANCEL forbids the person-specific "
                    "address that INTRUDE requires"
                ),
            )
        )
    for key in _MODE_NULL_OBJECTS.get(mode, ()):
        if state.get(key) is not None:
            diagnostics.append(
                entry.violation(
                    "TIMELINE_MODE_INVARIANT",
                    observed="mode={0} with a non-null {1}".format(mode, key),
                    expected="{0} is null for mode {1}".format(key, mode),
                )
            )
    for key in _MODE_REQUIRED_OBJECTS.get(mode, ()):
        if state.get(key) is None:
            diagnostics.append(
                entry.violation(
                    "TIMELINE_MODE_INVARIANT",
                    observed="mode={0} with {1}=null".format(mode, key),
                    expected="a populated {0} for mode {1}".format(key, mode),
                )
            )

    cancel_state = state.get("cancel_state")
    if isinstance(cancel_state, dict):
        diagnostics.extend(_check_cancel_state(entry, cancel_state, index=index))
    elif cancel_state is not None:
        diagnostics.append(
            entry.malformed(
                "CANCEL_STATE_MALFORMED",
                observed="cancel_state has type {0}".format(type(cancel_state).__name__),
                expected="an object or null",
            )
        )
    pair_state = state.get("pair_state")
    if isinstance(pair_state, dict):
        diagnostics.extend(_check_pair_state(entry, pair_state))
    elif pair_state is not None:
        diagnostics.append(
            entry.malformed(
                "PAIR_STATE_MALFORMED",
                observed="pair_state has type {0}".format(type(pair_state).__name__),
                expected="an object or null",
            )
        )
    evidence = state.get("pairing_evidence")
    if isinstance(evidence, dict):
        diagnostics.extend(_check_pairing_evidence(entry, evidence))
    elif evidence is not None:
        diagnostics.append(
            entry.malformed(
                "PAIRING_EVIDENCE_MALFORMED",
                observed="pairing_evidence has type {0}".format(type(evidence).__name__),
                expected="an object or null",
            )
        )
    return tuple(diagnostics)


def check_pair_calibration_uniqueness(
    index: ReferenceIndex,
) -> Tuple[CheckerDiagnostic, ...]:
    """A Pair_Calibration ID stays unique to one pair of living participants."""

    claims: Dict[str, Dict[Tuple[str, ...], List[PlanningRecord]]] = {}
    for entry in index.of_type("TimelineEntry"):
        state = entry.payload.get("technical_state")
        if not isinstance(state, dict):
            continue
        pair_state = state.get("pair_state")
        if not isinstance(pair_state, dict):
            continue
        calibration_id = _stable_id(pair_state.get("calibration_id"))
        participants = pair_state.get("participants")
        if calibration_id is None or not isinstance(participants, list):
            continue
        pair = tuple(sorted(str(member) for member in participants))
        claims.setdefault(calibration_id, {}).setdefault(pair, []).append(entry)

    diagnostics: List[CheckerDiagnostic] = []
    for calibration_id in sorted(claims):
        pairs = claims[calibration_id]
        if len(pairs) > 1:
            related = [
                entry.identity for entries in pairs.values() for entry in entries
            ]
            diagnostics.append(
                _diagnostic(
                    "PAIR_CALIBRATION_MANY_TO_ONE",
                    scope=SCOPE_PLANNING,
                    item=calibration_id,
                    observed="{0} distinct participant pairs share this "
                    "calibration".format(len(pairs)),
                    expected="one Pair_Calibration per pair of living participants",
                    related=tuple(sorted(related)),
                )
            )
    return tuple(diagnostics)


# ---------------------------------------------------------------------------
# Chapter-local direct references and Requirement 12.5 agreement
# ---------------------------------------------------------------------------


def check_arc_entry_references(
    entry: ArcEntryRecord, index: ReferenceIndex
) -> Tuple[CheckerDiagnostic, ...]:
    """Resolve one ArcEntry's own direct planning references.

    `reveal_ids` resolution waits for the task that indexes `Reveal` records.
    """

    diagnostics: List[CheckerDiagnostic] = []
    item = entry.filename or entry.identity
    payload = entry.payload

    for field_name, record_type in (
        ("timeline_id", "TimelineEntry"),
        ("pov_id", "POVProfile"),
    ):
        _target, reference_diagnostics = _resolve_reference(
            index,
            record_type,
            payload.get(field_name),
            scope=SCOPE_CHAPTER,
            item=item,
            field_name=field_name,
            related=(entry.identity,),
        )
        diagnostics.extend(reference_diagnostics)

    horizon = payload.get("record_horizon")
    if isinstance(horizon, dict):
        _target, reference_diagnostics = _resolve_reference(
            index,
            "TimelineEntry",
            horizon.get("through_timeline_id"),
            scope=SCOPE_CHAPTER,
            item=item,
            field_name="record_horizon.through_timeline_id",
            related=(entry.identity,),
        )
        diagnostics.extend(reference_diagnostics)

    motif_events = payload.get("motif_events")
    if isinstance(motif_events, list):
        for value in motif_events:
            _target, reference_diagnostics = _resolve_reference(
                index,
                "MotifEvent",
                value,
                scope=SCOPE_CHAPTER,
                item=item,
                field_name="motif_events[]",
                related=(entry.identity,),
            )
            diagnostics.extend(reference_diagnostics)
    return tuple(diagnostics)


def check_direct_references(
    document: ChapterDocument,
    arc_entry: Optional[ArcEntryRecord],
    index: ReferenceIndex,
) -> Tuple[CheckerDiagnostic, ...]:
    """Resolve a Chapter_File's direct references and check local agreement.

    Covers Requirement 10.3 and 10.4 for one chapter and the Requirement 12.5
    Timeline_ID, POV_ID, Motif_Event, Hook, and Chapter_Status agreements task
    7.2 deferred. Movement and global-sequence agreement stay in
    `check_chapter_agreement`, which already owns them.
    """

    diagnostics: List[CheckerDiagnostic] = []
    item = document.relative_path
    header = document.header

    if "timeline_id" in header:
        _target, reference_diagnostics = _resolve_reference(
            index,
            "TimelineEntry",
            header["timeline_id"],
            scope=SCOPE_CHAPTER,
            item=item,
            field_name="timeline_id",
        )
        diagnostics.extend(reference_diagnostics)

    profile: Optional[PlanningRecord] = None
    if "pov_id" in header:
        profile, reference_diagnostics = _resolve_reference(
            index,
            "POVProfile",
            header["pov_id"],
            scope=SCOPE_CHAPTER,
            item=item,
            field_name="pov_id",
        )
        diagnostics.extend(reference_diagnostics)
    if profile is not None:
        brief, reference_diagnostics = _resolve_reference(
            index,
            "VoiceBrief",
            profile.payload.get("voice_brief_id"),
            scope=SCOPE_CHAPTER,
            item=item,
            field_name="voice_brief_id",
            related=(profile.identity,),
        )
        diagnostics.extend(reference_diagnostics)
        if brief is not None and _stable_id(
            brief.payload.get("pov_id")
        ) != _stable_id(profile.payload.get("pov_id")):
            diagnostics.append(
                _diagnostic(
                    "VOICE_BRIEF_POV_DISAGREEMENT",
                    scope=SCOPE_CHAPTER,
                    item=item,
                    observed="VoiceBrief pov_id={0!r}".format(
                        brief.payload.get("pov_id")
                    ),
                    expected="the same POV_ID as this chapter's profile",
                    related=(brief.identity, profile.identity),
                )
            )

    header_chapter = header.get("chapter")
    header_motifs = header.get("motif_events")
    if isinstance(header_motifs, list):
        for value in header_motifs:
            target, reference_diagnostics = _resolve_reference(
                index,
                "MotifEvent",
                value,
                scope=SCOPE_CHAPTER,
                item=item,
                field_name="motif_events[]",
            )
            diagnostics.extend(reference_diagnostics)
            if target is None or not _is_chapter_number(header_chapter):
                continue
            participating = target.payload.get("participating_chapters")
            if isinstance(participating, list) and header_chapter not in participating:
                diagnostics.append(
                    _diagnostic(
                        "MOTIF_EVENT_CHAPTER_DISAGREEMENT",
                        scope=SCOPE_CHAPTER,
                        item=item,
                        observed="{0} does not list chapter {1} among its "
                        "participating chapters".format(
                            _stable_id(value), header_chapter
                        ),
                        expected="a Motif_Event assigned to this chapter",
                        related=(target.identity,),
                    )
                )

    if arc_entry is None:
        return tuple(diagnostics)

    diagnostics.extend(check_arc_entry_references(arc_entry, index))

    for key, code in (
        ("timeline_id", "CHAPTER_TIMELINE_DISAGREEMENT"),
        ("pov_id", "CHAPTER_POV_DISAGREEMENT"),
    ):
        if key not in header:
            continue
        header_value = _stable_id(header[key])
        outline_value = _stable_id(arc_entry.payload.get(key))
        if header_value != outline_value:
            diagnostics.append(
                _diagnostic(
                    code,
                    scope=SCOPE_CHAPTER,
                    item=item,
                    observed="header={0!r}, arc_entry={1!r}".format(
                        header[key], arc_entry.payload.get(key)
                    ),
                    expected="one {0} agreed by header and Arc_Outline".format(key),
                    related=(arc_entry.identity,),
                )
            )

    if isinstance(header_motifs, list):
        outline_motifs = arc_entry.payload.get("motif_events")
        if isinstance(outline_motifs, list):
            header_set = {_stable_id(value) for value in header_motifs}
            outline_set = {_stable_id(value) for value in outline_motifs}
            if header_set != outline_set:
                diagnostics.append(
                    _diagnostic(
                        "CHAPTER_MOTIF_EVENTS_DISAGREEMENT",
                        scope=SCOPE_CHAPTER,
                        item=item,
                        observed="header={0}, arc_entry={1}".format(
                            sorted(str(value) for value in header_set),
                            sorted(str(value) for value in outline_set),
                        ),
                        expected="one Motif_Event set agreed by header and Arc_Outline",
                        related=(arc_entry.identity,),
                    )
                )

    if "hook" in header:
        header_hook = _normalized_text(str(header["hook"])).strip()
        outline_hook = arc_entry.payload.get("hook")
        outline_hook_text = (
            _normalized_text(outline_hook).strip()
            if isinstance(outline_hook, str)
            else None
        )
        if header_hook != outline_hook_text:
            # Hook *presence* and textual agreement are objective. Hook quality
            # is Editorial_Review's alone and is never scored here.
            diagnostics.append(
                _diagnostic(
                    "CHAPTER_HOOK_DISAGREEMENT",
                    scope=SCOPE_CHAPTER,
                    item=item,
                    observed="header={0!r}, arc_entry={1!r}".format(
                        header["hook"], outline_hook
                    ),
                    expected="Hook metadata agreed textually by header and outline",
                    related=(arc_entry.identity,),
                )
            )

    if "status" in header:
        outline_status = arc_entry.payload.get("status")
        if header["status"] != outline_status:
            diagnostics.append(
                _diagnostic(
                    "CHAPTER_STATUS_DISAGREEMENT",
                    scope=SCOPE_CHAPTER,
                    item=item,
                    observed="header={0!r}, arc_entry={1!r}".format(
                        header["status"], outline_status
                    ),
                    expected="one Chapter_Status agreed by header and Arc_Outline",
                    related=(arc_entry.identity,),
                )
            )

    return tuple(diagnostics)


# ---------------------------------------------------------------------------
# Cross_Cut references, gated on the requested batch scope
# ---------------------------------------------------------------------------


def _scope_contains(
    chapters: Sequence[int], batch_scope: Optional[Iterable[int]]
) -> bool:
    """Whether the requested batch scope contains every participating chapter.

    `None` means an unrestricted scope. A partial scope cannot decide reciprocity
    for a relationship whose other participant it does not contain, so the
    relationship is left unevaluated rather than reported as one-sided.
    """

    if batch_scope is None:
        return True
    scope = frozenset(batch_scope)
    return all(chapter in scope for chapter in chapters)


def check_cross_cut_references(
    index: ReferenceIndex, *, batch_scope: Optional[Iterable[int]] = None
) -> Tuple[CheckerDiagnostic, ...]:
    """Validate Cross_Cut declarations whose participants lie inside the scope.

    Two rules with different scope needs. A declaration whose target does not
    exist is decidable from the declaring chapter alone, so it is reported
    whenever that chapter is in scope. Reciprocity needs every participant, so it
    is evaluated only when the requested batch scope contains all of them.
    """

    diagnostics: List[CheckerDiagnostic] = []
    declared = index.declared_cross_cuts()

    for entry in index.arc_entries:
        if entry.chapter is None or not _scope_contains([entry.chapter], batch_scope):
            continue
        value = entry.payload.get("cross_cuts")
        item = entry.filename or entry.identity
        if value == ARC_ENTRY_NO_CROSS_CUT:
            continue
        if not isinstance(value, list) or not value:
            diagnostics.append(
                _diagnostic(
                    "CROSS_CUT_DECLARATION_MALFORMED",
                    scope=SCOPE_CHAPTER,
                    item=item,
                    observed="cross_cuts={0!r}".format(value),
                    expected='the exact string "none" or a nonempty array of StableIDs',
                    disposition=DISPOSITION_INCOMPLETE,
                    related=(entry.identity,),
                )
            )
            continue
        seen: List[str] = []
        for member in value:
            cross_cut_id = _stable_id(member)
            if cross_cut_id is None:
                diagnostics.append(
                    _diagnostic(
                        "CROSS_CUT_DECLARATION_MALFORMED",
                        scope=SCOPE_CHAPTER,
                        item=item,
                        observed="cross_cuts[]={0!r}".format(member),
                        expected="a StableID matching " + STABLE_ID_PATTERN.pattern,
                        disposition=DISPOSITION_INCOMPLETE,
                        related=(entry.identity,),
                    )
                )
                continue
            if cross_cut_id in seen:
                diagnostics.append(
                    _diagnostic(
                        "CROSS_CUT_DECLARATION_MALFORMED",
                        scope=SCOPE_CHAPTER,
                        item=item,
                        observed="cross_cuts declares {0} twice".format(cross_cut_id),
                        expected="a duplicate-free array",
                        disposition=DISPOSITION_INCOMPLETE,
                        related=(entry.identity,),
                    )
                )
                continue
            seen.append(cross_cut_id)
            _target, reference_diagnostics = _resolve_reference(
                index,
                "CrossCut",
                cross_cut_id,
                scope=SCOPE_CHAPTER,
                item=item,
                field_name="cross_cuts[]",
                related=(entry.identity,),
            )
            diagnostics.extend(reference_diagnostics)

    for record in index.of_type("CrossCut"):
        cross_cut_id = record.record_id()
        if cross_cut_id is None:
            continue
        chapters = record.payload.get("chapters")
        if (
            not isinstance(chapters, list)
            or len(chapters) < 2
            or any(not _is_chapter_number(number) for number in chapters)
            or len(set(chapters)) != len(chapters)
            or list(chapters) != sorted(chapters)
        ):
            diagnostics.append(
                record.malformed(
                    "CROSS_CUT_MALFORMED",
                    observed="chapters={0!r}".format(chapters),
                    expected="at least two unique chapter numbers sorted ascending",
                )
            )
            continue
        if not _scope_contains(chapters, batch_scope):
            continue

        if record.payload.get("handoff_mode") not in CROSS_CUT_HANDOFF_MODES:
            diagnostics.append(
                record.malformed(
                    "CROSS_CUT_MALFORMED",
                    observed="handoff_mode={0!r}".format(
                        record.payload.get("handoff_mode")
                    ),
                    expected="one of " + ", ".join(CROSS_CUT_HANDOFF_MODES),
                )
            )
        if not _is_nonblank_string(record.payload.get("replay_boundary")):
            diagnostics.append(
                record.malformed(
                    "CROSS_CUT_MALFORMED",
                    observed="replay_boundary={0!r}".format(
                        record.payload.get("replay_boundary")
                    ),
                    expected="a nonblank replay boundary statement",
                )
            )
        if all(
            record.payload.get(key) is None
            for key in ("shared_timeline_id", "shared_reveal_id", "shared_consequence")
        ):
            diagnostics.append(
                record.violation(
                    "CROSS_CUT_INVARIANT",
                    observed="no shared timeline, reveal, or consequence",
                    expected="at least one non-null shared basis",
                )
            )
        if record.payload.get("shared_timeline_id") is not None:
            _target, reference_diagnostics = _resolve_reference(
                index,
                "TimelineEntry",
                record.payload.get("shared_timeline_id"),
                scope=SCOPE_PLANNING,
                item=cross_cut_id,
                field_name="shared_timeline_id",
                related=(record.identity,),
            )
            diagnostics.extend(reference_diagnostics)

        values = record.payload.get("material_narrative_value")
        covered: List[Any] = []
        if not isinstance(values, list):
            diagnostics.append(
                record.malformed(
                    "CROSS_CUT_MALFORMED",
                    observed="material_narrative_value={0!r}".format(values),
                    expected="exactly one object per participating chapter",
                )
            )
        else:
            for member in values:
                if (
                    not isinstance(member, dict)
                    or set(member) != {"chapter", "value"}
                    or not _is_nonblank_string(member.get("value"))
                ):
                    diagnostics.append(
                        record.malformed(
                            "CROSS_CUT_MALFORMED",
                            observed="material_narrative_value member "
                            "{0!r}".format(member),
                            expected="exactly chapter plus a nonblank value",
                        )
                    )
                    continue
                covered.append(member["chapter"])
            if sorted(covered) != sorted(chapters) or len(set(covered)) != len(covered):
                diagnostics.append(
                    record.violation(
                        "CROSS_CUT_INVARIANT",
                        observed="material_narrative_value covers {0}".format(
                            sorted(str(number) for number in covered)
                        ),
                        expected="exactly one distinct value per participating chapter",
                    )
                )

        declared_by = record.payload.get("declared_by_chapters")
        if not isinstance(declared_by, list) or set(declared_by) != set(chapters):
            diagnostics.append(
                record.violation(
                    "CROSS_CUT_INVARIANT",
                    observed="declared_by_chapters={0!r}".format(declared_by),
                    expected="the same chapter set as chapters",
                )
            )

        declaring = set(declared.get(cross_cut_id, ()))
        missing = sorted(set(chapters) - declaring)
        if missing:
            diagnostics.append(
                record.violation(
                    "CROSS_CUT_ONE_SIDED",
                    observed="chapters {0} do not declare this Cross_Cut".format(
                        ", ".join(str(number) for number in missing)
                    ),
                    expected="every participating chapter's ArcEntry declares it",
                )
            )
        extra = sorted(declaring - set(chapters))
        if extra:
            diagnostics.append(
                record.violation(
                    "CROSS_CUT_UNDECLARED_PARTICIPANT",
                    observed="chapters {0} declare this Cross_Cut without "
                    "participating".format(", ".join(str(number) for number in extra)),
                    expected="only participating chapters declare it",
                )
            )

    return tuple(diagnostics)


def check_planning_references(
    index: ReferenceIndex, *, batch_scope: Optional[Iterable[int]] = None
) -> Tuple[CheckerDiagnostic, ...]:
    """Every planning-side task 7.3 check over one loaded reference index."""

    diagnostics: List[CheckerDiagnostic] = []
    for entry in index.of_type("TimelineEntry"):
        diagnostics.extend(check_technical_state(entry, index))
    diagnostics.extend(check_pair_calibration_uniqueness(index))
    diagnostics.extend(check_character_references(index))
    diagnostics.extend(check_pov_voice_brief_pairing(index))
    diagnostics.extend(check_cross_cut_references(index, batch_scope=batch_scope))
    return tuple(diagnostics)


# ---------------------------------------------------------------------------
# Chapter and multi-chapter entry points
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ChapterCheckResult:
    """Everything task 7.2 established about one Chapter_File."""

    relative_path: str
    document: ChapterDocument
    length_report: Optional[ChapterLengthReport]
    arc_entry: Optional[ArcEntryRecord]
    diagnostics: Tuple[CheckerDiagnostic, ...]

    @property
    def chapter(self) -> Optional[int]:
        header_chapter = self.document.header.get("chapter")
        if isinstance(header_chapter, int):
            return header_chapter
        if self.document.filename is not None:
            return self.document.filename.sequence
        return None

    @property
    def movement(self) -> Optional[str]:
        header_movement = self.document.header.get("movement")
        if isinstance(header_movement, str):
            return header_movement
        if self.document.filename is not None:
            return self.document.filename.movement
        return None


@dataclass(frozen=True)
class ChapterScopeResult:
    """One requested chapter-or-batch scope, its diagnostics, and its status."""

    chapters: Tuple[ChapterCheckResult, ...]
    diagnostics: Tuple[CheckerDiagnostic, ...]

    @property
    def result(self) -> str:
        return classify_result(self.diagnostics)

    @property
    def exit_status(self) -> int:
        return exit_status_for_result(self.result)


def manuscript_relative_path(path: Path, manuscript_root: Path) -> str:
    """Manuscript-root-relative POSIX path, as an ArcEntry stores it."""

    resolved = Path(path)
    root = Path(manuscript_root)
    try:
        return resolved.relative_to(root).as_posix()
    except ValueError:
        try:
            return resolved.resolve().relative_to(root.resolve()).as_posix()
        except (ValueError, OSError):
            return resolved.name


def check_chapter_file(
    path: Path,
    *,
    manuscript_root: Path,
    arc_entries: Sequence[ArcEntryRecord] = (),
    reference_index: Optional[ReferenceIndex] = None,
) -> ChapterCheckResult:
    """Run every chapter-local check for one Chapter_File.

    `reference_index` is optional and defaults to `None`, in which case only the
    task 7.2 filename, header, length, and agreement checks run. Supplying one
    adds the task 7.3 direct-reference resolution and the Requirement 12.5
    Timeline_ID, POV_ID, Motif_Event, Hook, and Chapter_Status agreements.
    """

    relative_path = manuscript_relative_path(path, manuscript_root)
    document = read_chapter_document(path, relative_path=relative_path)
    diagnostics: List[CheckerDiagnostic] = list(document.diagnostics)

    if not document.boundary_resolved:
        # Fail safely: no count and no semantic validation for a file whose
        # Prose_Body boundary could not be identified.
        return ChapterCheckResult(
            relative_path=relative_path,
            document=document,
            length_report=None,
            arc_entry=None,
            diagnostics=tuple(diagnostics),
        )

    header_chapter = document.header.get("chapter")
    arc_entry, match_diagnostics = match_arc_entry(
        arc_entries,
        relative_path=relative_path,
        chapter=header_chapter
        if isinstance(header_chapter, int)
        else (document.filename.sequence if document.filename is not None else None),
    )
    diagnostics.extend(match_diagnostics)

    report = chapter_length_report(document)
    diagnostics.extend(check_chapter_length(report, arc_entry=arc_entry))
    diagnostics.extend(check_chapter_agreement(document, arc_entry))
    if reference_index is not None:
        diagnostics.extend(
            check_direct_references(document, arc_entry, reference_index)
        )

    return ChapterCheckResult(
        relative_path=relative_path,
        document=document,
        length_report=report,
        arc_entry=arc_entry,
        diagnostics=tuple(diagnostics),
    )


def check_chapter_sequence_agreement(
    results: Sequence[ChapterCheckResult],
) -> Tuple[CheckerDiagnostic, ...]:
    """Report duplicate global chapter numbers and movement/sequence inversions.

    Both checks hold at any scope. Two files claiming one global number is a
    duplicate identity, and because the movements are contiguous blocks in a
    fixed order with a sequence that never resets, a later movement can never
    carry a lower chapter number. Gaps, whole-book contiguity, and the
    outline/file bijection need the complete planned set and belong to the
    Manuscript_Global_Gate.
    """

    diagnostics: List[CheckerDiagnostic] = []
    by_chapter: Dict[int, List[str]] = {}
    for result in results:
        number = result.chapter
        if number is None:
            continue
        by_chapter.setdefault(number, []).append(result.relative_path)

    for number in sorted(by_chapter):
        paths = sorted(by_chapter[number])
        if len(paths) > 1:
            diagnostics.append(
                _diagnostic(
                    "CHAPTER_SEQUENCE_DUPLICATE",
                    scope=SCOPE_BATCH,
                    item="chapter {0}".format(number),
                    observed=", ".join(paths),
                    expected="one Chapter_File per global chapter number",
                    disposition=DISPOSITION_INCOMPLETE,
                )
            )

    ordered = [
        result
        for result in results
        if result.chapter is not None
        and result.movement is not None
        and result.movement in MOVEMENT_ORDER
    ]
    for index, earlier in enumerate(ordered):
        for later in ordered[index + 1 :]:
            earlier_rank = MOVEMENT_ORDER[str(earlier.movement)]
            later_rank = MOVEMENT_ORDER[str(later.movement)]
            if earlier_rank == later_rank:
                continue
            low, high = (
                (earlier, later) if earlier_rank < later_rank else (later, earlier)
            )
            if int(low.chapter or 0) < int(high.chapter or 0):
                continue
            diagnostics.append(
                _diagnostic(
                    "CHAPTER_MOVEMENT_SEQUENCE_ORDER",
                    scope=SCOPE_BATCH,
                    item=high.relative_path,
                    observed="{0} chapter {1} is not after {2} chapter {3}".format(
                        high.movement, high.chapter, low.movement, low.chapter
                    ),
                    expected=(
                        "movement blocks in order with an ascending "
                        "global sequence"
                    ),
                    related=(low.relative_path,),
                )
            )

    return tuple(diagnostics)


def check_chapter_files(
    paths: Sequence[Path],
    *,
    manuscript_root: Path,
    arc_entries: Sequence[ArcEntryRecord] = (),
    extra_diagnostics: Sequence[CheckerDiagnostic] = (),
    reference_index: Optional[ReferenceIndex] = None,
) -> ChapterScopeResult:
    """Run the chapter-local checks over one or more Chapter_Files.

    When `reference_index` is supplied, the batch scope for the Cross_Cut rules
    is exactly the set of chapters these files claim: a relationship whose other
    participant is outside the requested batch is left unevaluated rather than
    reported as one-sided.
    """

    results = tuple(
        check_chapter_file(
            path,
            manuscript_root=manuscript_root,
            arc_entries=arc_entries,
            reference_index=reference_index,
        )
        for path in paths
    )
    diagnostics: List[CheckerDiagnostic] = list(extra_diagnostics)
    for result in results:
        diagnostics.extend(result.diagnostics)
    diagnostics.extend(check_chapter_sequence_agreement(results))
    if reference_index is not None:
        batch_scope = frozenset(
            result.chapter for result in results if result.chapter is not None
        )
        diagnostics.extend(
            check_cross_cut_references(reference_index, batch_scope=batch_scope)
        )
    return ChapterScopeResult(chapters=results, diagnostics=tuple(diagnostics))


def check_chapter_scope(
    paths: Sequence[Path],
    *,
    manuscript_root: Path,
    arc_outline_path: Optional[Path] = None,
    reference_index: Optional[ReferenceIndex] = None,
) -> ChapterScopeResult:
    """Load the Arc_Outline and check the requested Chapter_Files.

    This is the seam the `--scope chapter` and `--scope batch` CLI of task 7.5
    calls and the text/JSON emitter of task 7.6 formats. It performs no output
    and no exit; the caller reads `result` and `exit_status`.

    `reference_index` is not built here. Which record sources a requested scope
    requires, and which changed references a batch carries, are task 7.5's
    inputs; a caller that has an index passes it and receives the task 7.3
    direct-reference checks as well.
    """

    root = Path(manuscript_root)
    outline_path = (
        Path(arc_outline_path)
        if arc_outline_path is not None
        else root.joinpath(*DEFAULT_ARC_OUTLINE_PATH.split("/"))
    )
    arc_entries, outline_diagnostics = load_arc_entries(
        outline_path, relative_path=manuscript_relative_path(outline_path, root)
    )
    return check_chapter_files(
        paths,
        manuscript_root=root,
        arc_entries=arc_entries,
        extra_diagnostics=outline_diagnostics,
        reference_index=reference_index,
    )


def _project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def build_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run objective checks for The Final Frontier novel project."
    )
    parser.add_argument(
        "--site-exclusion",
        action="store_true",
        help="exercise the Manuscript_Exclusion_Contract reference collector",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=_project_root(),
        help="workspace root to scan (defaults to this repository root)",
    )
    parser.add_argument(
        "--contract",
        type=Path,
        default=None,
        help=(
            "contract path, absolute or relative to --workspace-root "
            "(defaults to The Final Frontier Novel/exclusion-contract.json)"
        ),
    )
    parser.add_argument(
        "--visibility-plan",
        type=Path,
        default=None,
        help="optional reference-song-visibility/v1 JSON fixture plan",
    )
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)
    if not arguments.site_exclusion:
        parser.error("only --site-exclusion is implemented by task 3.2")

    try:
        result = run_site_exclusion(
            arguments.workspace_root,
            contract_path=arguments.contract,
            visibility_plan_path=arguments.visibility_plan,
        )
    except SiteExclusionError as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        print(f"LIMIT {EXTERNAL_ADOPTION_LIMIT}", file=sys.stderr)
        return exc.exit_status

    excluded = ",".join(
        root.relative_path for root in result.contract.excluded_roots
    )
    print(
        "PASS site-exclusion "
        f"excluded_roots={excluded} "
        f"scanned_children={len(result.scanned_direct_children)} "
        f"sources={len(result.sources)} "
        f"songs={len(result.songs)} "
        "manuscript_entries=0"
    )
    print(f"LIMIT {EXTERNAL_ADOPTION_LIMIT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
