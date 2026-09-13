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
  Cross_Cut integrity gated on the requested batch scope;
* task 7.4 — scoped Motif_Ledger/Header/ArcEntry assignment checks, the fixed
  chain/copper and calibration mappings, reciprocal literal-constraint links,
  and exact NFC/LF Prose_Body-only rejection of ledgered phrases outside their
  allowed scope without inferring an in-scope count or Final_Passage;
* task 7.5 — the `--scope chapter` and `--scope batch` modes, the delivered
  Calibration_Batch and Drafting_Batch size rules, and the changed
  cross-document reference audit;
* task 7.6 — one total order over diagnostics, the text and JSON report
  surfaces, and the `0`/`1`/`2` exit contract;
* task 8.8 — `--scope global` and the Manuscript_Global_Gate: whole-outline
  sequence, four ordered contiguous movement blocks, outline/file bijection,
  both Same_POV_Run bounds, roster size/Anchor coverage/load vector, normal
  share, movement word relationships, Final_Targets, whole-book literal totals
  read from the declared Final_Passage span, fixed motif family totals,
  CanonFact authority under `DEC-011`/`DEC-014`, NovelExtension and Reveal
  reference integrity, ArcChange atomicity, GateResult consistency, the two
  independent finalization gates, mandatory Fluent_Pairing coverage, and
  Front_Matter rights.

The checker is read-only: it never rewrites counts, metadata, IDs, statuses, or
prose, and it never infers a record value from prose commentary. No diagnostic
code may name a craft judgment; see `CRAFT_JUDGMENT_TERMS`.
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
SCOPE_GLOBAL = "global"

DIAGNOSTIC_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]*$")

# Requirements 12.11 and 12.12 remove a fixed list of craft judgments from every
# automated pass/fail evaluation, so the checker's diagnostic vocabulary must not
# be able to name one. These are the forbidden fragments of a diagnostic code.
#
# The terms are deliberately specific rather than single broad words, because
# several objective codes legitimately mention the same subject. `HOOK` and
# `VOICE` appear alone in `CHAPTER_HOOK_DISAGREEMENT` and
# `VOICE_BRIEF_POV_DISAGREEMENT`, which compare declared Hook metadata and
# resolve a Voice_Brief ID; Requirement 12.5 requires both. What may never
# appear is a code that scores the hook or the prose voice itself.
CRAFT_JUDGMENT_TERMS: Tuple[str, ...] = (
    "ARTISTRY",
    "BEAUTY",
    "DISTINCTNESS",
    "ELEGANCE",
    "EMOTIONAL",
    "HOOK_EFFECTIVENESS",
    "HOOK_QUALITY",
    "MOOD",
    "ORIGINALITY",
    "PACING",
    "PROSE_VOICE",
    "QUALITY",
    "RATING",
    "RESTRAINT",
    "RHETORICAL",
    "SCORE",
    "SENTENCE_RHYTHM",
    "TENDERNESS",
    "TONAL",
    "VOICE_FIDELITY",
)


def craft_judgment_term(code: str) -> Optional[str]:
    """The forbidden craft-judgment term in `code`, or `None` when it is clean.

    Returns the term rather than a boolean so both the programming-error backstop
    in `CheckerDiagnostic` and the author-facing ledger diagnostic can name what
    they rejected.
    """

    upper = code.upper()
    for term in CRAFT_JUDGMENT_TERMS:
        if term in upper:
            return term
    return None

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

# The record sources the Manuscript_Global_Gate additionally requires. Kept
# separate from `DEFAULT_RECORD_SOURCES` on purpose: Requirement 10.9 excludes
# Final_Targets, baseline approval, and final-ending acceptance from the
# Chapter_Local_Gate, so a chapter gate must not be able to fail because a
# whole-book document is absent.
GLOBAL_RECORD_SOURCES: Tuple[str, ...] = DEFAULT_RECORD_SOURCES + (
    "planning/arc-changes.md",
    "planning/gate-results.md",
    "planning/editorial-log.md",
)

# The Front_Matter document, which is a Final_Prerequisite but holds no records.
DEFAULT_FRONT_MATTER_PATH = "front-matter.md"

# The stable-ID field of each record type this checker resolves references
# against. Task 7.4 adds `LiteralPhraseConstraint` because motif records and
# their only authorized prose-scan rules must resolve in both directions; task
# 8.8 adds the whole-book authority, change, and gate records.
RECORD_ID_FIELDS: Mapping[str, str] = {
    "TimelineEntry": "timeline_id",
    "POVProfile": "pov_id",
    "VoiceBrief": "voice_brief_id",
    "MotifEvent": "motif_event_id",
    "LiteralPhraseConstraint": "constraint_id",
    "CrossCut": "cross_cut_id",
    "NovelExtension": "extension_id",
    "CanonFact": "canon_id",
    "Reveal": "reveal_id",
    "Baseline": "baseline_id",
    "ArcChange": "arc_change_id",
    "EditorialFinding": "editorial_finding_id",
    "GateResult": "gate_result_id",
}
REFERENCE_DANGLING_CODES: Mapping[str, str] = {
    "TimelineEntry": "TIMELINE_REFERENCE_DANGLING",
    "POVProfile": "POV_REFERENCE_DANGLING",
    "VoiceBrief": "VOICE_BRIEF_REFERENCE_DANGLING",
    "MotifEvent": "MOTIF_EVENT_REFERENCE_DANGLING",
    "LiteralPhraseConstraint": "LITERAL_CONSTRAINT_REFERENCE_DANGLING",
    "CrossCut": "CROSS_CUT_REFERENCE_DANGLING",
}

MOTIF_EVENT_KEYS: Tuple[str, ...] = (
    "motif_event_id",
    "family",
    "dramatic_function",
    "movement",
    "planned_chapter",
    "participating_chapters",
    "representation_mode",
    "literal_constraint_id",
    "scene_scope",
    "arc_change_history",
)
MOTIF_REPRESENTATION_MODES: Tuple[str, ...] = (
    "literal",
    "adapted",
    "image",
    "action",
    "scene-structure",
)
LITERAL_CONSTRAINT_KEYS: Tuple[str, ...] = (
    "constraint_id",
    "motif_event_id",
    "exact_phrase",
    "scan_scope",
    "allowed_movements",
    "allowed_chapters",
    "allowed_files",
    "allowed_span",
    "minimum_in_scope",
    "maximum_in_scope",
    "exact_in_scope",
    "maximum_outside_scope",
    "normalization",
    "scope_exclusions",
    "diagnostic_code",
)
LITERAL_NORMALIZATION: Mapping[str, Any] = {
    "unicode": "NFC",
    "line_endings": "LF",
    "case_sensitive": True,
    "punctuation_sensitive": True,
    "word_order_sensitive": True,
    "match_mode": "non-overlapping-literal",
}
LITERAL_SCOPE_EXCLUSIONS: Tuple[str, ...] = (
    "canon-source-songs",
    "other-song-files",
    "planning-documents",
    "chapter-headers",
    "front-matter",
    "editorial-records",
    "checker-output",
)
LITERAL_SPAN_KEYS: Tuple[str, ...] = (
    "span_id",
    "chapter",
    "start_boundary",
    "end_boundary",
)
LITERAL_BOUNDARY_KINDS: Tuple[str, ...] = (
    "literal-marker",
    "line-number",
    "start-of-prose",
    "end-of-prose",
)

# These are objective identity/movement/chapter/representation mappings fixed by
# the approved design. The checker does not compare the prose-like
# `dramatic_function` or `scene_scope` text semantically; it only requires those
# fields to be nonblank. A later completed ArcChange validator may supersede a
# mapping, but no such post-baseline state exists in the calibration scope.
RESOLVED_MOTIF_MAPPINGS: Mapping[str, Mapping[str, Any]] = {
    "MOT-CHAIN-01": {
        "family": "spectrum / wire / voice",
        "movement": "discovery_part",
        "planned_chapter": 13,
        "participating_chapters": (13,),
        "representation_mode": "image",
        "literal_constraint_id": None,
    },
    "MOT-CHAIN-02": {
        "family": "spectrum / wire / voice",
        "movement": "private_defense_part",
        "planned_chapter": 45,
        "participating_chapters": (45,),
        "representation_mode": "image",
        "literal_constraint_id": None,
    },
    "MOT-CHAIN-03": {
        "family": "spectrum / wire / voice",
        "movement": "aftermath_coda",
        "planned_chapter": 127,
        "participating_chapters": (127,),
        "representation_mode": "action",
        "literal_constraint_id": None,
    },
    "MOT-COPPER-01": {
        "family": "copper / quiet",
        "movement": "private_defense_part",
        "planned_chapter": 31,
        "participating_chapters": (31,),
        "representation_mode": "image",
        "literal_constraint_id": None,
    },
    "MOT-COPPER-02": {
        "family": "copper / quiet",
        "movement": "mindwars_part",
        "planned_chapter": 70,
        "participating_chapters": (70,),
        "representation_mode": "image",
        "literal_constraint_id": None,
    },
    "MOT-COPPER-03": {
        "family": "copper / quiet",
        "movement": "aftermath_coda",
        "planned_chapter": 124,
        "participating_chapters": (124,),
        "representation_mode": "image",
        "literal_constraint_id": None,
    },
    "MOT-YES-01": {
        "family": "authorization question",
        "movement": "mindwars_part",
        "planned_chapter": 73,
        "participating_chapters": (73,),
        "representation_mode": "literal",
        "literal_constraint_id": "LPC-DID-I-SAY-YES",
    },
    "MOT-KETTLE-01": {
        "family": "kettle",
        "movement": "aftermath_coda",
        "planned_chapter": 118,
        "participating_chapters": (118,),
        "representation_mode": "image",
        "literal_constraint_id": None,
    },
    "MOT-COME-04": {
        "family": "come in",
        "movement": "aftermath_coda",
        "planned_chapter": 124,
        "participating_chapters": (124,),
        "representation_mode": "action",
        "literal_constraint_id": None,
    },
    "MOT-KETTLE-02": {
        "family": "kettle",
        "movement": "aftermath_coda",
        "planned_chapter": 124,
        "participating_chapters": (124,),
        "representation_mode": "action",
        "literal_constraint_id": None,
    },
}
CLOSED_MOTIF_FAMILY_IDS: Mapping[str, Tuple[str, ...]] = {
    "spectrum / wire / voice": (
        "MOT-CHAIN-01",
        "MOT-CHAIN-02",
        "MOT-CHAIN-03",
    ),
    "copper / quiet": (
        "MOT-COPPER-01",
        "MOT-COPPER-02",
        "MOT-COPPER-03",
    ),
}
CALIBRATION_REQUIRED_MOTIFS: Mapping[int, Tuple[str, ...]] = {
    73: ("MOT-YES-01",),
    118: ("MOT-KETTLE-01",),
    124: ("MOT-COME-04", "MOT-KETTLE-02"),
}
RESOLVED_DID_I_SAY_YES_CONSTRAINT: Mapping[str, Any] = {
    "motif_event_id": "MOT-YES-01",
    "exact_phrase": "Did I say yes?",
    "scan_scope": "chapter-prose-body-only",
    "allowed_movements": ("mindwars_part",),
    "allowed_chapters": (),
    "allowed_files": (),
    "allowed_span": None,
    "minimum_in_scope": None,
    "maximum_in_scope": None,
    "exact_in_scope": None,
    "maximum_outside_scope": 0,
    "diagnostic_code": "LITERAL_DID_I_SAY_YES_SCOPE",
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

# The two independent Same_POV_Run bounds. Requirement 2.7 and 11.12 cap the
# Chapter_File count; Requirement 2.15 and 11.12 cap the combined Prose_Words.
# Neither implies the other: a legal three-chapter run can still be too long,
# and a two-chapter run can break the word bound while its length is legal.
POV_RUN_CHAPTER_LIMIT = 3
POV_RUN_WORD_LIMIT = 3600

# Requirement 4.1 and 11.7: the final roster holds 3–5 human POVs, exactly one
# of which is the Anchor_POV.
POV_ROSTER_SIZE_RANGE: Tuple[int, int] = (3, 5)
POV_ENTITY_TYPE_HUMAN = "human"

# Requirement 2.8: at least 80 percent of *all* final Chapter_Files are
# `normal`. Held as a numerator/denominator pair so the comparison stays exact
# integer arithmetic and 79/100 versus 80/100 cannot drift on a float.
NORMAL_SHARE_MINIMUM: Tuple[int, int] = (80, 100)

# Requirement 2.1: provisional planning targets. They are replaced by
# Final_Targets at approval, so exceeding them is a warning about provisional
# data rather than an objective violation.
PROVISIONAL_CHAPTER_RANGE: Tuple[int, int] = (120, 135)
PROVISIONAL_WORD_RANGE: Tuple[int, int] = (130000, 150000)

# Requirement 15.1: every mandatory Fluent_Pairing range must resolve to at
# least one assigned beat in the complete Arc_Outline.
FLUENT_PAIRING_RANGES: Tuple[Tuple[int, int], ...] = (
    (36, 42),
    (56, 61),
    (70, 77),
    (78, 93),
    (94, 108),
)

# Requirement 15.3 and `DEC-016`: the provisional per-POV Chapter_File loads.
# Held as a sorted multiset of totals rather than a POV_ID-keyed mapping, because
# Requirement 12.11 keeps selected names outside pass/fail evaluation and the
# obligation is that the load vector is unchanged, not that a particular name
# owns a particular number.
PROVISIONAL_POV_LOAD_TOTALS: Tuple[int, ...] = (7, 32, 33, 56)

# The exact five Canon_Sources `DEC-014` fixes, and the one path it excludes.
# A `lyric` CanonFact resolves to exactly one of the five; *One-Time Pad* is
# unpublished, noncanonical, and absent from the working tree.
CANON_SOURCE_PATHS: Tuple[str, ...] = (
    "songs/Case Zero.md",
    "songs/Faraday.md",
    "songs/The Final Frontier.md",
    "songs/The Radius.md",
    "songs/The Synaptic Frontier.md",
)
EXCLUDED_CANON_SOURCE_PATH = "songs/One-Time Pad.md"

# `DEC-011` authority precedence, as the closed `CanonFact` enums of
# `record-schemas.md` section 7.
CANON_AUTHORITY_BASES: Tuple[str, ...] = (
    "author-decision",
    "requirement",
    "lyric",
    "ratified-note",
)
CANON_SOURCE_MATERIAL_CLASSES: Tuple[str, ...] = (
    "author-decision",
    "requirement",
    "lyric",
    "production-note",
    "style-prompt",
    "exclude-prompt",
    "generation-workflow",
    "credits",
    "rights-metadata",
)
# The note and metadata classes that carry no authority of their own. A fact on
# one of these is binding only through a resolvable `adopted_by` adoption.
ADVISORY_SOURCE_MATERIAL_CLASSES: Tuple[str, ...] = (
    "production-note",
    "style-prompt",
    "exclude-prompt",
    "generation-workflow",
    "credits",
    "rights-metadata",
)
# The required source class for each self-authorizing basis. `ratified-note` is
# absent because it accepts any advisory class plus an adoption.
CANON_BASIS_SOURCE_CLASS: Mapping[str, str] = {
    "author-decision": "author-decision",
    "requirement": "requirement",
    "lyric": "lyric",
}
CANON_TRUTH_SCOPES: Tuple[str, ...] = (
    "authoritative-proposition",
    "attributed-testimony",
    "ratified-proposition",
)
# There is deliberately no `omniscient` truth scope. First-person testimony is
# binding as an account and never as omniscient causal proof.
TESTIMONY_TRUTH_SCOPE = "attributed-testimony"
TESTIMONY_ATTRIBUTION_KEYS: Tuple[str, ...] = (
    "speaker",
    "attribution",
    "epistemic_limitation",
)
CANON_ADOPTION_KEYS: Tuple[str, ...] = (
    "authority_type",
    "authority_id",
    "source_path",
    "source_location",
)
CANON_ADOPTION_AUTHORITY_TYPES: Tuple[str, ...] = ("author-decision", "requirement")
ADVISORY_CITATION_KEYS: Tuple[str, ...] = (
    "source_path",
    "source_location",
    "material_class",
    "classification",
    "note",
)
ADVISORY_CITATION_CLASSIFICATION = "advisory-non-story"

# `Baseline`, `ArcChange`, and `GateResult` enums, from `record-schemas.md`
# sections 12, 13, and 15.
BASELINE_STATES: Tuple[str, ...] = (
    "provisional",
    "pending-author-approval",
    "approved",
    "superseded",
)
BASELINE_STATE_APPROVED = "approved"
BASELINE_APPROVAL_KEYS: Tuple[str, ...] = (
    "approved_by",
    "approved_at",
    "approval_record",
)
FINAL_TARGET_KEYS: Tuple[str, ...] = (
    "chapter_count",
    "minimum_words",
    "maximum_words",
)
BASELINE_REVISION_PASS_KEYS: Tuple[str, ...] = ("performed_at", "dispositions")
BASELINE_DISPOSITION_KEYS: Tuple[str, ...] = (
    "editorial_finding_id",
    "outcome",
    "arc_change_id",
    "rationale",
)
BASELINE_DISPOSITION_OUTCOMES: Tuple[str, ...] = (
    "arc-change",
    "no-change-rationale",
)

ARC_CHANGE_STATUSES: Tuple[str, ...] = (
    "proposed",
    "approved",
    "in-progress",
    "complete",
    "rejected",
)
ARC_CHANGE_STATUS_COMPLETE = "complete"
ARC_CHANGE_OBLIGATION_KEYS: Tuple[str, ...] = (
    "document",
    "required_change",
    "status",
    "evidence_ref",
)
SYNCHRONIZATION_STATUSES: Tuple[str, ...] = ("pending", "complete")
SYNCHRONIZATION_STATUS_COMPLETE = "complete"

GATE_TYPES: Tuple[str, ...] = (
    "site-isolation",
    "calibration-objective",
    "chapter-local",
    "batch",
    "baseline-objective",
    "manuscript-global",
    "editorial",
)
GATE_TYPE_EDITORIAL = "editorial"
GATE_TYPE_MANUSCRIPT_GLOBAL = "manuscript-global"
GATE_SCOPE_KEYS: Tuple[str, ...] = ("chapter_numbers", "documents", "description")
GATE_PREREQUISITE_STATES: Tuple[str, ...] = ("complete", "incomplete")
GATE_PREREQUISITE_COMPLETE = "complete"
GATE_RESULTS: Tuple[str, ...] = (RESULT_PASS, RESULT_REVISION, RESULT_INCOMPLETE)

# Chapter statuses that assert a passed gate, and the one status a substantive
# Prose_Body change demotes them to.
APPROVED_CHAPTER_STATUSES: Tuple[str, ...] = ("approved", "final")
REVISED_CHAPTER_STATUS = "revised"
# Exploratory work can never satisfy a Final_Prerequisite; the Calibration_Batch
# stays exploratory until its surrounding movement batches reconcile it.
EXPLORATORY_CHAPTER_STATUS = "exploratory"
FINAL_CHAPTER_STATUS = "final"

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
        forbidden = craft_judgment_term(self.code)
        if forbidden is not None:
            # A programming-error backstop, not a data path. A ledgered
            # `diagnostic_code` is screened while its constraint is parsed, so an
            # author document produces a violation instead of reaching this.
            raise ValueError(
                "diagnostic code {0!r} names the craft judgment {1!r}, which "
                "Requirements 12.11 and 12.12 exclude from automated "
                "evaluation".format(self.code, forbidden)
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
        diagnostics.extend(_check_record_chronology(record, index))
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
    if isinstance(pair_state, dict) and isinstance(evidence, dict):
        diagnostics.extend(_check_stopped_session(entry, pair_state, evidence))
    return tuple(diagnostics)


RECORD_CHRONOLOGY_KEYS: Tuple[str, ...] = (
    "composition_timeline_id",
    "deposit_timeline_id",
    "release_timeline_ids",
)


def _check_record_chronology(
    entry: PlanningRecord, index: ReferenceIndex
) -> Tuple[CheckerDiagnostic, ...]:
    """Resolve a record's composition, deposit, and release chronology.

    The Civic Record Trust chronology keeps a record's composition, its later
    deposit, and each release as separate entries, which is what lets Trust
    formation follow alteration of the April record without collapsing the two
    timestamps. Objectively that means the three references resolve, the release
    list holds no duplicate, and composition and deposit are not the same entry.

    Which entry is *earlier* is not decided here. Order lives in the prose
    `relative_chronology` field, and reading it would mean inferring continuity
    from commentary.
    """

    chronology = entry.payload.get("record_chronology")
    if chronology is None:
        return ()
    if not isinstance(chronology, dict):
        return (
            entry.malformed(
                "RECORD_CHRONOLOGY_MALFORMED",
                observed="record_chronology has type {0}".format(
                    type(chronology).__name__
                ),
                expected="an object or null",
            ),
        )

    diagnostics: List[CheckerDiagnostic] = []
    report = _key_set_report(chronology, RECORD_CHRONOLOGY_KEYS)
    if report:
        return (
            entry.malformed(
                "RECORD_CHRONOLOGY_MALFORMED",
                observed=report,
                expected="exactly " + ", ".join(RECORD_CHRONOLOGY_KEYS),
            ),
        )

    def _resolve_entry(value: Any, field_name: str) -> Optional[str]:
        if value is None:
            return None
        timeline_id = _stable_id(value)
        if timeline_id is None:
            diagnostics.append(
                entry.malformed(
                    "RECORD_CHRONOLOGY_MALFORMED",
                    observed="{0}={1!r}".format(field_name, value),
                    expected="a Timeline StableID or null",
                )
            )
            return None
        if index.is_duplicated("TimelineEntry", timeline_id):
            return timeline_id
        if not index.lookup("TimelineEntry", timeline_id):
            diagnostics.append(
                entry.violation(
                    "RECORD_CHRONOLOGY_REFERENCE_DANGLING",
                    observed="{0}={1} resolves to no TimelineEntry".format(
                        field_name, timeline_id
                    ),
                    expected="one existing TimelineEntry",
                )
            )
        return timeline_id

    composition = _resolve_entry(
        chronology.get("composition_timeline_id"), "composition_timeline_id"
    )
    deposit = _resolve_entry(
        chronology.get("deposit_timeline_id"), "deposit_timeline_id"
    )
    if composition is not None and composition == deposit:
        diagnostics.append(
            entry.violation(
                "RECORD_CHRONOLOGY_COLLAPSED",
                observed="composition and deposit are both {0}".format(composition),
                expected="composition and later deposit as separate entries",
            )
        )

    releases = chronology.get("release_timeline_ids")
    if not isinstance(releases, list):
        diagnostics.append(
            entry.malformed(
                "RECORD_CHRONOLOGY_MALFORMED",
                observed="release_timeline_ids={0!r}".format(releases),
                expected="an array of unique Timeline StableIDs",
            )
        )
        return tuple(diagnostics)

    seen: List[str] = []
    for position, value in enumerate(releases):
        timeline_id = _resolve_entry(
            value, "release_timeline_ids[{0}]".format(position)
        )
        if timeline_id is None:
            continue
        if timeline_id in seen:
            diagnostics.append(
                entry.violation(
                    "RECORD_CHRONOLOGY_RELEASE_DUPLICATE",
                    observed="{0} appears more than once".format(timeline_id),
                    expected="unique release references",
                )
            )
        else:
            seen.append(timeline_id)

    return tuple(diagnostics)


def _check_stopped_session(
    entry: PlanningRecord,
    pair_state: Mapping[str, Any],
    evidence: Mapping[str, Any],
) -> Tuple[CheckerDiagnostic, ...]:
    """A paused, revoked, or integrity-failed session transports no content.

    The `PairState` invariant stops semantic transport the moment a participant
    pauses or revokes, and after clipping, latency, or an integrity failure until
    an explicit confirmation, retry, or ordinary-speech fallback. A transcript is
    the only transported content this schema represents, so within one entry the
    objective rule is exact: a stopped send state carries no transcript.

    Recovery is expressed by a later entry returning `deliberate_send_state` to
    `required`. Ordering a recovery marker across an event stream would need
    fields this schema version does not define, so that part of the invariant
    stays a human continuity reading rather than a guessed automated one.
    """

    send_state = pair_state.get("deliberate_send_state")
    if send_state not in ("paused", "revoked", "integrity-failed"):
        return ()
    if evidence.get("transcript") is None:
        return ()
    return (
        entry.violation(
            "PAIR_STOPPED_SESSION_TRANSPORT",
            observed="deliberate_send_state={0!r} with a transcript".format(
                send_state
            ),
            expected=(
                "no transported content while a session is paused, revoked, or "
                "integrity-failed; recovery needs an explicit confirmation, "
                "retry, or ordinary-speech fallback first"
            ),
        ),
    )


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
# Calibration-scope Motif_Event and Literal_Phrase_Constraint checks
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _MotifEventRule:
    record: PlanningRecord
    motif_event_id: str
    family: str
    movement: str
    planned_chapter: int
    participating_chapters: Tuple[int, ...]
    representation_mode: str
    literal_constraint_id: Optional[str]


@dataclass(frozen=True)
class _LiteralConstraintRule:
    record: PlanningRecord
    constraint_id: str
    motif_event_id: str
    exact_phrase: str
    allowed_movements: Tuple[str, ...]
    allowed_chapters: Tuple[int, ...]
    allowed_files: Tuple[str, ...]
    allowed_span: Optional[Mapping[str, Any]]
    maximum_outside_scope: int
    diagnostic_code: str
    # In-scope totals are only decidable when the scope actually contains every
    # file the rule allows, so they are carried here and consumed by the
    # whole-book check rather than by the chapter-local one.
    minimum_in_scope: Optional[int] = None
    maximum_in_scope: Optional[int] = None
    exact_in_scope: Optional[int] = None

    @property
    def has_in_scope_total(self) -> bool:
        return (
            self.minimum_in_scope is not None
            or self.maximum_in_scope is not None
            or self.exact_in_scope is not None
        )


def _is_nonnegative_integer(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value >= 0


def _is_workspace_relative_path(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip() or "\\" in value:
        return False
    normalized = _normalized_text(value.strip())
    path = PurePosixPath(normalized)
    return (
        not path.is_absolute()
        and all(part not in ("", ".", "..") for part in path.parts)
        and path.as_posix() == normalized
    )


def _stable_id_sequence(value: Any) -> Optional[Tuple[str, ...]]:
    if not isinstance(value, list):
        return None
    values: List[str] = []
    for member in value:
        stable_id = _stable_id(member)
        if stable_id is None or stable_id in values:
            return None
        values.append(stable_id)
    return tuple(values)


def _chapter_number_sequence(
    value: Any, *, nonempty: bool = False
) -> Optional[Tuple[int, ...]]:
    if not isinstance(value, list) or (nonempty and not value):
        return None
    if any(not _is_chapter_number(member) for member in value):
        return None
    if len(set(value)) != len(value):
        return None
    return tuple(value)


def _parse_motif_event_rule(
    record: PlanningRecord,
) -> Tuple[Optional[_MotifEventRule], Tuple[CheckerDiagnostic, ...]]:
    """Validate one MotifEvent record without inferring from commentary."""

    payload = record.payload
    if set(payload) != set(MOTIF_EVENT_KEYS):
        return None, (
            record.malformed(
                "MOTIF_EVENT_MALFORMED",
                observed=_key_set_report(payload, MOTIF_EVENT_KEYS),
                expected="exactly the MotifEvent schema keys",
            ),
        )

    diagnostics: List[CheckerDiagnostic] = []
    motif_event_id = _stable_id(payload.get("motif_event_id"))
    if motif_event_id is None:
        diagnostics.append(
            record.malformed(
                "MOTIF_EVENT_MALFORMED",
                observed="motif_event_id={0!r}".format(
                    payload.get("motif_event_id")
                ),
                expected="a StableID matching " + STABLE_ID_PATTERN.pattern,
            )
        )

    family = payload.get("family")
    if not _is_nonblank_string(family):
        diagnostics.append(
            record.malformed(
                "MOTIF_EVENT_MALFORMED",
                observed="family={0!r}".format(family),
                expected="a nonblank family",
            )
        )
    dramatic_function = payload.get("dramatic_function")
    if not _is_nonblank_string(dramatic_function):
        diagnostics.append(
            record.malformed(
                "MOTIF_EVENT_MALFORMED",
                observed="dramatic_function={0!r}".format(dramatic_function),
                expected="a nonblank dramatic function",
            )
        )
    scene_scope = payload.get("scene_scope")
    if not _is_nonblank_string(scene_scope):
        diagnostics.append(
            record.malformed(
                "MOTIF_EVENT_MALFORMED",
                observed="scene_scope={0!r}".format(scene_scope),
                expected="a nonblank sustained scene/function boundary",
            )
        )

    movement = payload.get("movement")
    if movement not in MOVEMENT_ORDER:
        diagnostics.append(
            record.malformed(
                "MOTIF_EVENT_MALFORMED",
                observed="movement={0!r}".format(movement),
                expected="one of " + ", ".join(MOVEMENTS),
            )
        )
    planned_chapter = payload.get("planned_chapter")
    if not _is_chapter_number(planned_chapter):
        diagnostics.append(
            record.malformed(
                "MOTIF_EVENT_MALFORMED",
                observed="planned_chapter={0!r}".format(planned_chapter),
                expected="an integer of at least 1",
            )
        )
    participating = _chapter_number_sequence(
        payload.get("participating_chapters"), nonempty=True
    )
    if participating is None:
        diagnostics.append(
            record.malformed(
                "MOTIF_EVENT_MALFORMED",
                observed="participating_chapters={0!r}".format(
                    payload.get("participating_chapters")
                ),
                expected="a nonempty duplicate-free array of chapter numbers",
            )
        )
    elif _is_chapter_number(planned_chapter) and planned_chapter not in participating:
        diagnostics.append(
            record.malformed(
                "MOTIF_EVENT_MALFORMED",
                observed="planned_chapter {0} is absent from {1}".format(
                    planned_chapter, list(participating)
                ),
                expected="participating_chapters to include the primary owner",
            )
        )

    representation_mode = payload.get("representation_mode")
    if representation_mode not in MOTIF_REPRESENTATION_MODES:
        diagnostics.append(
            record.malformed(
                "MOTIF_EVENT_MALFORMED",
                observed="representation_mode={0!r}".format(representation_mode),
                expected="one of " + ", ".join(MOTIF_REPRESENTATION_MODES),
            )
        )
    raw_constraint_id = payload.get("literal_constraint_id")
    literal_constraint_id = (
        None if raw_constraint_id is None else _stable_id(raw_constraint_id)
    )
    if raw_constraint_id is not None and literal_constraint_id is None:
        diagnostics.append(
            record.malformed(
                "MOTIF_EVENT_MALFORMED",
                observed="literal_constraint_id={0!r}".format(raw_constraint_id),
                expected="null or a StableID",
            )
        )
    history = _stable_id_sequence(payload.get("arc_change_history"))
    if history is None:
        diagnostics.append(
            record.malformed(
                "MOTIF_EVENT_MALFORMED",
                observed="arc_change_history={0!r}".format(
                    payload.get("arc_change_history")
                ),
                expected="a duplicate-free array of ArcChange StableIDs",
            )
        )

    if diagnostics:
        return None, tuple(diagnostics)
    assert motif_event_id is not None
    assert isinstance(family, str)
    assert isinstance(movement, str)
    assert isinstance(planned_chapter, int)
    assert participating is not None
    assert isinstance(representation_mode, str)
    return (
        _MotifEventRule(
            record=record,
            motif_event_id=motif_event_id,
            family=_normalized_text(family).strip(),
            movement=movement,
            planned_chapter=planned_chapter,
            participating_chapters=participating,
            representation_mode=representation_mode,
            literal_constraint_id=literal_constraint_id,
        ),
        (),
    )


def _literal_boundary_is_valid(value: Any) -> bool:
    if not isinstance(value, dict) or set(value) != {"kind", "value"}:
        return False
    kind = value.get("kind")
    boundary_value = value.get("value")
    if kind not in LITERAL_BOUNDARY_KINDS:
        return False
    if kind in ("start-of-prose", "end-of-prose"):
        return boundary_value is None
    if kind == "line-number":
        return _is_chapter_number(boundary_value)
    return _is_nonblank_string(boundary_value)


def _literal_span_is_valid(value: Any) -> bool:
    if value is None:
        return True
    if not isinstance(value, dict) or set(value) != set(LITERAL_SPAN_KEYS):
        return False
    return (
        _stable_id(value.get("span_id")) is not None
        and _is_chapter_number(value.get("chapter"))
        and _literal_boundary_is_valid(value.get("start_boundary"))
        and _literal_boundary_is_valid(value.get("end_boundary"))
    )


def _parse_literal_constraint_rule(
    record: PlanningRecord,
) -> Tuple[Optional[_LiteralConstraintRule], Tuple[CheckerDiagnostic, ...]]:
    """Validate one ledgered literal rule; prose is never consulted here."""

    payload = record.payload
    if set(payload) != set(LITERAL_CONSTRAINT_KEYS):
        return None, (
            record.malformed(
                "LITERAL_CONSTRAINT_MALFORMED",
                observed=_key_set_report(payload, LITERAL_CONSTRAINT_KEYS),
                expected="exactly the LiteralPhraseConstraint schema keys",
            ),
        )

    diagnostics: List[CheckerDiagnostic] = []
    constraint_id = _stable_id(payload.get("constraint_id"))
    motif_event_id = _stable_id(payload.get("motif_event_id"))
    if constraint_id is None:
        diagnostics.append(
            record.malformed(
                "LITERAL_CONSTRAINT_MALFORMED",
                observed="constraint_id={0!r}".format(payload.get("constraint_id")),
                expected="a StableID matching " + STABLE_ID_PATTERN.pattern,
            )
        )
    if motif_event_id is None:
        diagnostics.append(
            record.malformed(
                "LITERAL_CONSTRAINT_MALFORMED",
                observed="motif_event_id={0!r}".format(
                    payload.get("motif_event_id")
                ),
                expected="a MotifEvent StableID",
            )
        )

    exact_phrase = payload.get("exact_phrase")
    if (
        not _is_nonblank_string(exact_phrase)
        or "\r" in str(exact_phrase)
        or "\n" in str(exact_phrase)
    ):
        diagnostics.append(
            record.malformed(
                "LITERAL_CONSTRAINT_MALFORMED",
                observed="exact_phrase={0!r}".format(exact_phrase),
                expected="a nonblank single-line exact phrase",
            )
        )
    if payload.get("scan_scope") != "chapter-prose-body-only":
        diagnostics.append(
            record.malformed(
                "LITERAL_CONSTRAINT_MALFORMED",
                observed="scan_scope={0!r}".format(payload.get("scan_scope")),
                expected="chapter-prose-body-only",
            )
        )

    allowed_movements_value = payload.get("allowed_movements")
    allowed_movements: Optional[Tuple[str, ...]] = None
    if (
        isinstance(allowed_movements_value, list)
        and allowed_movements_value
        and all(member in MOVEMENT_ORDER for member in allowed_movements_value)
        and len(set(allowed_movements_value)) == len(allowed_movements_value)
    ):
        allowed_movements = tuple(allowed_movements_value)
    else:
        diagnostics.append(
            record.malformed(
                "LITERAL_CONSTRAINT_MALFORMED",
                observed="allowed_movements={0!r}".format(allowed_movements_value),
                expected="a nonempty duplicate-free array of Movement values",
            )
        )

    allowed_chapters = _chapter_number_sequence(payload.get("allowed_chapters"))
    if allowed_chapters is None:
        diagnostics.append(
            record.malformed(
                "LITERAL_CONSTRAINT_MALFORMED",
                observed="allowed_chapters={0!r}".format(
                    payload.get("allowed_chapters")
                ),
                expected="a duplicate-free array of chapter numbers",
            )
        )
    allowed_files_value = payload.get("allowed_files")
    allowed_files: Optional[Tuple[str, ...]] = None
    if (
        isinstance(allowed_files_value, list)
        and all(_is_workspace_relative_path(member) for member in allowed_files_value)
        and len(set(allowed_files_value)) == len(allowed_files_value)
    ):
        allowed_files = tuple(
            _normalized_text(member.strip()) for member in allowed_files_value
        )
    else:
        diagnostics.append(
            record.malformed(
                "LITERAL_CONSTRAINT_MALFORMED",
                observed="allowed_files={0!r}".format(allowed_files_value),
                expected="a duplicate-free array of workspace-relative paths",
            )
        )

    allowed_span = payload.get("allowed_span")
    if not _literal_span_is_valid(allowed_span):
        diagnostics.append(
            record.malformed(
                "LITERAL_CONSTRAINT_MALFORMED",
                observed="allowed_span={0!r}".format(allowed_span),
                expected="null or one closed, machine-readable span object",
            )
        )

    count_fields = (
        "minimum_in_scope",
        "maximum_in_scope",
        "exact_in_scope",
    )
    counts: Dict[str, Optional[int]] = {}
    for field_name in count_fields:
        value = payload.get(field_name)
        if value is not None and not _is_nonnegative_integer(value):
            diagnostics.append(
                record.malformed(
                    "LITERAL_CONSTRAINT_MALFORMED",
                    observed="{0}={1!r}".format(field_name, value),
                    expected="null or a nonnegative integer",
                )
            )
        counts[field_name] = value if isinstance(value, int) else None
    if counts["exact_in_scope"] is not None and (
        counts["minimum_in_scope"] is not None
        or counts["maximum_in_scope"] is not None
    ):
        diagnostics.append(
            record.malformed(
                "LITERAL_CONSTRAINT_MALFORMED",
                observed="exact_in_scope is combined with a minimum or maximum",
                expected="exact count alone, or minimum/maximum without exact",
            )
        )
    if (
        counts["minimum_in_scope"] is not None
        and counts["maximum_in_scope"] is not None
        and int(counts["minimum_in_scope"] or 0)
        > int(counts["maximum_in_scope"] or 0)
    ):
        diagnostics.append(
            record.malformed(
                "LITERAL_CONSTRAINT_MALFORMED",
                observed="minimum_in_scope exceeds maximum_in_scope",
                expected="minimum_in_scope <= maximum_in_scope",
            )
        )

    maximum_outside_scope = payload.get("maximum_outside_scope")
    if not _is_nonnegative_integer(maximum_outside_scope):
        diagnostics.append(
            record.malformed(
                "LITERAL_CONSTRAINT_MALFORMED",
                observed="maximum_outside_scope={0!r}".format(
                    maximum_outside_scope
                ),
                expected="a nonnegative integer",
            )
        )
    normalization = payload.get("normalization")
    if normalization != dict(LITERAL_NORMALIZATION):
        diagnostics.append(
            record.malformed(
                "LITERAL_CONSTRAINT_MALFORMED",
                observed="normalization={0!r}".format(normalization),
                expected="the fixed NFC/LF exact-case/order/punctuation policy",
            )
        )
    exclusions = payload.get("scope_exclusions")
    if not (
        isinstance(exclusions, list)
        and len(exclusions) == len(LITERAL_SCOPE_EXCLUSIONS)
        and set(exclusions) == set(LITERAL_SCOPE_EXCLUSIONS)
    ):
        diagnostics.append(
            record.malformed(
                "LITERAL_CONSTRAINT_MALFORMED",
                observed="scope_exclusions={0!r}".format(exclusions),
                expected="exactly the seven non-Prose_Body exclusions",
            )
        )
    diagnostic_code = payload.get("diagnostic_code")
    if not isinstance(diagnostic_code, str) or DIAGNOSTIC_CODE_PATTERN.match(
        diagnostic_code
    ) is None:
        diagnostics.append(
            record.malformed(
                "LITERAL_CONSTRAINT_MALFORMED",
                observed="diagnostic_code={0!r}".format(diagnostic_code),
                expected="a stable uppercase underscore diagnostic code",
            )
        )
    else:
        # The ledger supplies this code, so it is the one place a craft judgment
        # could enter the diagnostic vocabulary from a document. Reject it here.
        forbidden = craft_judgment_term(diagnostic_code)
        if forbidden is not None:
            diagnostics.append(
                record.violation(
                    "LITERAL_CONSTRAINT_CRAFT_JUDGMENT_CODE",
                    observed="diagnostic_code={0!r} names {1!r}".format(
                        diagnostic_code, forbidden
                    ),
                    expected=(
                        "an objective code; Requirements 12.11 and 12.12 keep "
                        "craft judgment out of automated evaluation"
                    ),
                )
            )

    if diagnostics:
        return None, tuple(diagnostics)
    assert constraint_id is not None
    assert motif_event_id is not None
    assert isinstance(exact_phrase, str)
    assert allowed_movements is not None
    assert allowed_chapters is not None
    assert allowed_files is not None
    assert isinstance(maximum_outside_scope, int)
    assert isinstance(diagnostic_code, str)
    return (
        _LiteralConstraintRule(
            record=record,
            constraint_id=constraint_id,
            motif_event_id=motif_event_id,
            exact_phrase=normalize_prose(exact_phrase),
            allowed_movements=allowed_movements,
            allowed_chapters=allowed_chapters,
            allowed_files=allowed_files,
            allowed_span=allowed_span,
            maximum_outside_scope=maximum_outside_scope,
            diagnostic_code=diagnostic_code,
            minimum_in_scope=counts["minimum_in_scope"],
            maximum_in_scope=counts["maximum_in_scope"],
            exact_in_scope=counts["exact_in_scope"],
        ),
        (),
    )


def _resolved_mapping_diagnostics(
    rule: _MotifEventRule,
) -> Tuple[CheckerDiagnostic, ...]:
    expected = RESOLVED_MOTIF_MAPPINGS.get(rule.motif_event_id)
    if expected is None:
        closed_ids: Optional[Tuple[str, ...]] = None
        if rule.motif_event_id.startswith("MOT-CHAIN-"):
            closed_ids = CLOSED_MOTIF_FAMILY_IDS["spectrum / wire / voice"]
        elif rule.motif_event_id.startswith("MOT-COPPER-"):
            closed_ids = CLOSED_MOTIF_FAMILY_IDS["copper / quiet"]
        elif rule.family in CLOSED_MOTIF_FAMILY_IDS:
            closed_ids = CLOSED_MOTIF_FAMILY_IDS[rule.family]
        if closed_ids is None or rule.motif_event_id in closed_ids:
            return ()
        return (
            rule.record.violation(
                "MOTIF_CLOSED_FAMILY_EXTENSION",
                observed="{0} extends a closed chain/copper family".format(
                    rule.motif_event_id
                ),
                expected="only " + ", ".join(closed_ids),
            ),
        )

    actual: Mapping[str, Any] = {
        "family": rule.family,
        "movement": rule.movement,
        "planned_chapter": rule.planned_chapter,
        "participating_chapters": rule.participating_chapters,
        "representation_mode": rule.representation_mode,
        "literal_constraint_id": rule.literal_constraint_id,
    }
    differing = [field_name for field_name in expected if actual[field_name] != expected[field_name]]
    if not differing:
        return ()
    return (
        rule.record.violation(
            "MOTIF_RESOLVED_MAPPING_DISAGREEMENT",
            observed=", ".join(
                "{0}={1!r}".format(field_name, actual[field_name])
                for field_name in differing
            ),
            expected=", ".join(
                "{0}={1!r}".format(field_name, expected[field_name])
                for field_name in differing
            ),
        ),
    )


def _resolved_literal_diagnostics(
    rule: _LiteralConstraintRule,
) -> Tuple[CheckerDiagnostic, ...]:
    if rule.constraint_id != "LPC-DID-I-SAY-YES":
        return ()
    actual: Mapping[str, Any] = {
        "motif_event_id": rule.motif_event_id,
        "exact_phrase": rule.exact_phrase,
        "scan_scope": rule.record.payload.get("scan_scope"),
        "allowed_movements": rule.allowed_movements,
        "allowed_chapters": rule.allowed_chapters,
        "allowed_files": rule.allowed_files,
        "allowed_span": rule.allowed_span,
        "minimum_in_scope": rule.record.payload.get("minimum_in_scope"),
        "maximum_in_scope": rule.record.payload.get("maximum_in_scope"),
        "exact_in_scope": rule.record.payload.get("exact_in_scope"),
        "maximum_outside_scope": rule.maximum_outside_scope,
        "diagnostic_code": rule.diagnostic_code,
    }
    expected = RESOLVED_DID_I_SAY_YES_CONSTRAINT
    differing = [field_name for field_name in expected if actual[field_name] != expected[field_name]]
    if not differing:
        return ()
    return (
        rule.record.violation(
            "LITERAL_CONSTRAINT_RESOLVED_MAPPING_DISAGREEMENT",
            observed=", ".join(
                "{0}={1!r}".format(field_name, actual[field_name])
                for field_name in differing
            ),
            expected=", ".join(
                "{0}={1!r}".format(field_name, expected[field_name])
                for field_name in differing
            ),
        ),
    )


def check_motif_planning(
    index: ReferenceIndex, *, chapter_scope: Optional[Iterable[int]] = None
) -> Tuple[CheckerDiagnostic, ...]:
    """Validate task-7.4 planning records and ledger/Arc assignments.

    With an explicit chapter scope, only MotifEvents assigned to, referenced by,
    or fixed as required for those chapters are direct records. With no scope,
    every existing MotifEvent and LiteralPhraseConstraint is audited. This pure
    planning seam is also usable before any Chapter_File exists.
    """

    scope = (
        None
        if chapter_scope is None
        else frozenset(
            chapter for chapter in chapter_scope if _is_chapter_number(chapter)
        )
    )
    arc_references: set = set()
    for entry in index.arc_entries:
        if entry.chapter is None or (scope is not None and entry.chapter not in scope):
            continue
        values = _stable_id_sequence(entry.payload.get("motif_events"))
        if values is not None:
            arc_references.update(values)
    required_ids = set()
    if scope is not None:
        for chapter in scope:
            required_ids.update(CALIBRATION_REQUIRED_MOTIFS.get(chapter, ()))

    selected_records: List[PlanningRecord] = []
    for record in index.of_type("MotifEvent"):
        record_id = _stable_id(record.payload.get("motif_event_id"))
        participating = _chapter_number_sequence(
            record.payload.get("participating_chapters"), nonempty=True
        )
        if scope is None or record_id in arc_references or record_id in required_ids:
            selected_records.append(record)
        elif participating is not None and any(chapter in scope for chapter in participating):
            selected_records.append(record)

    diagnostics: List[CheckerDiagnostic] = []
    rules: Dict[str, _MotifEventRule] = {}
    for record in selected_records:
        record_id = _stable_id(record.payload.get("motif_event_id"))
        if record_id is not None and index.is_duplicated("MotifEvent", record_id):
            continue
        rule, record_diagnostics = _parse_motif_event_rule(record)
        diagnostics.extend(record_diagnostics)
        if rule is None:
            continue
        rules[rule.motif_event_id] = rule
        diagnostics.extend(_resolved_mapping_diagnostics(rule))

    selected_ids = set(rules) | arc_references | required_ids
    linked_constraint_ids = {
        rule.literal_constraint_id
        for rule in rules.values()
        if rule.literal_constraint_id is not None
    }
    constraint_rules: Dict[str, _LiteralConstraintRule] = {}
    for record in index.of_type("LiteralPhraseConstraint"):
        constraint_id = _stable_id(record.payload.get("constraint_id"))
        motif_event_id = _stable_id(record.payload.get("motif_event_id"))
        if scope is not None and (
            constraint_id not in linked_constraint_ids
            and motif_event_id not in selected_ids
        ):
            continue
        if constraint_id is not None and index.is_duplicated(
            "LiteralPhraseConstraint", constraint_id
        ):
            continue
        rule, record_diagnostics = _parse_literal_constraint_rule(record)
        diagnostics.extend(record_diagnostics)
        if rule is None:
            continue
        constraint_rules[rule.constraint_id] = rule
        diagnostics.extend(_resolved_literal_diagnostics(rule))

    for rule in rules.values():
        if rule.literal_constraint_id is None:
            continue
        target, reference_diagnostics = _resolve_reference(
            index,
            "LiteralPhraseConstraint",
            rule.literal_constraint_id,
            scope=SCOPE_PLANNING,
            item=rule.motif_event_id,
            field_name="literal_constraint_id",
            related=(rule.record.identity,),
        )
        diagnostics.extend(reference_diagnostics)
        if target is not None and _stable_id(
            target.payload.get("motif_event_id")
        ) != rule.motif_event_id:
            diagnostics.append(
                rule.record.violation(
                    "MOTIF_LITERAL_CONSTRAINT_DISAGREEMENT",
                    observed="{0} points back to {1!r}".format(
                        rule.literal_constraint_id,
                        target.payload.get("motif_event_id"),
                    ),
                    expected="a reciprocal constraint for " + rule.motif_event_id,
                    related=(target.identity,),
                )
            )

    for rule in constraint_rules.values():
        target, reference_diagnostics = _resolve_reference(
            index,
            "MotifEvent",
            rule.motif_event_id,
            scope=SCOPE_PLANNING,
            item=rule.constraint_id,
            field_name="motif_event_id",
            related=(rule.record.identity,),
        )
        diagnostics.extend(reference_diagnostics)
        if target is not None and _stable_id(
            target.payload.get("literal_constraint_id")
        ) != rule.constraint_id:
            diagnostics.append(
                rule.record.violation(
                    "LITERAL_CONSTRAINT_MOTIF_DISAGREEMENT",
                    observed="{0} carries literal_constraint_id={1!r}".format(
                        rule.motif_event_id,
                        target.payload.get("literal_constraint_id"),
                    ),
                    expected="a reciprocal link to " + rule.constraint_id,
                    related=(target.identity,),
                )
            )

    ledger_by_chapter: Dict[int, set] = {}
    for rule in rules.values():
        for chapter in rule.participating_chapters:
            ledger_by_chapter.setdefault(chapter, set()).add(rule.motif_event_id)
    chapters = (
        sorted(scope)
        if scope is not None
        else sorted(
            set(ledger_by_chapter)
            | {
                entry.chapter
                for entry in index.arc_entries
                if entry.chapter is not None
            }
        )
    )
    for chapter in chapters:
        entry = index.arc_entry_for_chapter(chapter)
        if entry is None:
            continue
        arc_ids = _stable_id_sequence(entry.payload.get("motif_events"))
        if arc_ids is None:
            diagnostics.append(
                _diagnostic(
                    "MOTIF_ARC_ASSIGNMENT_MALFORMED",
                    scope=SCOPE_PLANNING,
                    item=entry.filename or entry.identity,
                    observed="motif_events={0!r}".format(
                        entry.payload.get("motif_events")
                    ),
                    expected="a duplicate-free array of MotifEvent StableIDs",
                    disposition=DISPOSITION_INCOMPLETE,
                    related=(entry.identity,),
                )
            )
            continue
        expected_ids = set(ledger_by_chapter.get(chapter, set()))
        if set(arc_ids) != expected_ids:
            diagnostics.append(
                _diagnostic(
                    "MOTIF_LEDGER_ARC_DISAGREEMENT",
                    scope=SCOPE_PLANNING,
                    item=entry.filename or entry.identity,
                    observed="arc_entry={0}, ledger={1}".format(
                        sorted(arc_ids), sorted(expected_ids)
                    ),
                    expected="one Motif_Event assignment set",
                    related=(entry.identity,),
                )
            )

    if scope is not None:
        for chapter in sorted(scope):
            for motif_event_id in CALIBRATION_REQUIRED_MOTIFS.get(chapter, ()):
                if index.lookup("MotifEvent", motif_event_id):
                    continue
                diagnostics.append(
                    _diagnostic(
                        "MOTIF_CALIBRATION_ASSIGNMENT_MISSING",
                        scope=SCOPE_PLANNING,
                        item="chapter {0}".format(chapter),
                        observed="no MotifEvent record for " + motif_event_id,
                        expected="{0} assigned to chapter {1}".format(
                            motif_event_id, chapter
                        ),
                    )
                )

    return tuple(diagnostics)


def check_chapter_motif_assignments(
    document: ChapterDocument, index: ReferenceIndex
) -> Tuple[CheckerDiagnostic, ...]:
    """Compare one parsed header with the ledger's assignment for its chapter."""

    chapter = document.header.get("chapter")
    header_ids = document.header.get("motif_events")
    if not _is_chapter_number(chapter) or not isinstance(header_ids, list):
        return ()

    expected_ids = set()
    for record in index.of_type("MotifEvent"):
        record_id = _stable_id(record.payload.get("motif_event_id"))
        if record_id is None or index.is_duplicated("MotifEvent", record_id):
            continue
        rule, _diagnostics = _parse_motif_event_rule(record)
        if rule is not None and chapter in rule.participating_chapters:
            expected_ids.add(rule.motif_event_id)
    observed_ids = {
        stable_id
        for stable_id in (_stable_id(value) for value in header_ids)
        if stable_id is not None
    }
    if observed_ids == expected_ids:
        return ()
    return (
        _diagnostic(
            "MOTIF_LEDGER_HEADER_DISAGREEMENT",
            scope=SCOPE_CHAPTER,
            item=document.relative_path,
            observed="header={0}, ledger={1}".format(
                sorted(observed_ids), sorted(expected_ids)
            ),
            expected="one Motif_Event assignment set",
        ),
    )


def _non_overlapping_occurrence_offsets(text: str, phrase: str) -> Tuple[int, ...]:
    offsets: List[int] = []
    cursor = 0
    while phrase:
        offset = text.find(phrase, cursor)
        if offset < 0:
            break
        offsets.append(offset)
        cursor = offset + len(phrase)
    return tuple(offsets)


def check_literal_phrase_constraints(
    document: ChapterDocument, index: ReferenceIndex
) -> Tuple[CheckerDiagnostic, ...]:
    """Apply ledgered outside-scope literal rules to one Prose_Body only.

    Both phrase and prose are NFC/LF normalized, then compared literally. Case,
    punctuation, and word order are therefore preserved. In-scope totals are not
    inferred from a chapter subset: `Did I say yes?` has no such total, and the
    declared Final_Passage/count owned by Chapter 128 is deliberately left for a
    scope that actually contains that machine-declared span.
    """

    if not document.boundary_resolved or document.prose_body is None:
        return ()
    movement = document.header.get("movement")
    chapter = document.header.get("chapter")
    if movement not in MOVEMENT_ORDER or not _is_chapter_number(chapter):
        return ()

    prose = normalize_prose(document.prose_body)
    diagnostics: List[CheckerDiagnostic] = []
    for record in index.of_type("LiteralPhraseConstraint"):
        constraint_id = _stable_id(record.payload.get("constraint_id"))
        if constraint_id is None or index.is_duplicated(
            "LiteralPhraseConstraint", constraint_id
        ):
            continue
        rule, _record_diagnostics = _parse_literal_constraint_rule(record)
        if rule is None:
            continue
        offsets = _non_overlapping_occurrence_offsets(prose, rule.exact_phrase)
        if not offsets:
            continue
        in_allowed_scope = movement in rule.allowed_movements
        if rule.allowed_chapters:
            in_allowed_scope = in_allowed_scope and chapter in rule.allowed_chapters
        if rule.allowed_files:
            in_allowed_scope = (
                in_allowed_scope and document.relative_path in rule.allowed_files
            )
        if in_allowed_scope:
            # Task 7.4 never turns a partial chapter/batch into a whole-book
            # count, and it never guesses the Chapter-128 Final_Passage.
            continue
        for occurrence_number, offset in enumerate(
            offsets[rule.maximum_outside_scope :],
            start=rule.maximum_outside_scope + 1,
        ):
            diagnostics.append(
                _diagnostic(
                    rule.diagnostic_code,
                    scope=SCOPE_CHAPTER,
                    item=document.relative_path,
                    observed="occurrence {0} at normalized Prose_Body offset {1}".format(
                        occurrence_number, offset
                    ),
                    expected=(
                        "no more than {0} exact occurrences outside the ledgered "
                        "movement/chapter/file scope"
                    ).format(rule.maximum_outside_scope),
                    details=(("protected_phrase", rule.exact_phrase),),
                    related=(rule.record.identity,),
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
    adds task 7.3 direct-reference resolution plus task 7.4 ledger/header and
    Prose_Body-only literal checks. Requirement 12.5 Timeline_ID, POV_ID,
    Motif_Event, Hook, and Chapter_Status agreements remain part of that seam.
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
        diagnostics.extend(
            check_chapter_motif_assignments(document, reference_index)
        )
        diagnostics.extend(
            check_literal_phrase_constraints(document, reference_index)
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

    When `reference_index` is supplied, the batch scope is exactly the set of
    chapters these files claim. Cross_Cut reciprocity is evaluated only when all
    participants are present; task-7.4 motif planning checks likewise inspect
    only records directly assigned/referenced in that set, while each parsed
    Prose_Body is scanned against the ledgered outside-scope literal rules.
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
        diagnostics.extend(
            check_motif_planning(reference_index, chapter_scope=batch_scope)
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


# ---------------------------------------------------------------------------
# Batch composition and changed cross-document references
# ---------------------------------------------------------------------------


# The design fixes the Calibration_Batch as chapters 1–5 plus the three
# nonconsecutive representative chapters. It is a pre-baseline delivery, so it is
# never required to be one contiguous sequence row.
CALIBRATION_BATCH_CHAPTERS: Tuple[int, ...] = (1, 2, 3, 4, 5, 73, 118, 124)
# Requirement 13.1 sizes the Calibration_Batch at 6–8 Chapter_Files; Requirement
# 13.2 sizes each post-baseline Drafting_Batch at 4–8. The ranges differ, which
# is why the two kinds are distinguished rather than sharing one rule.
CALIBRATION_BATCH_SIZE_RANGE: Tuple[int, int] = (6, 8)
DRAFTING_BATCH_SIZE_RANGE: Tuple[int, int] = (4, 8)

BATCH_KIND_CALIBRATION = "calibration"
BATCH_KIND_DRAFTING = "drafting"
BATCH_KINDS: Tuple[str, ...] = (BATCH_KIND_CALIBRATION, BATCH_KIND_DRAFTING)

BATCH_SIZE_RANGES: Mapping[str, Tuple[int, int]] = {
    BATCH_KIND_CALIBRATION: CALIBRATION_BATCH_SIZE_RANGE,
    BATCH_KIND_DRAFTING: DRAFTING_BATCH_SIZE_RANGE,
}

# Which record types a chapter can reach directly, and the one field that makes
# each reachable. `LiteralPhraseConstraint` is absent because a chapter never
# names one: it is reached through the Motif_Event it protects.
_SCOPE_PARTICIPATION_TYPES: Tuple[str, ...] = (
    "ArcEntry",
    "TimelineEntry",
    "POVProfile",
    "VoiceBrief",
    "MotifEvent",
    "LiteralPhraseConstraint",
    "CrossCut",
)


def classify_batch_kind(chapters: Iterable[int]) -> str:
    """Infer whether a chapter set is the Calibration_Batch or a Drafting_Batch.

    A set is the Calibration_Batch when it is drawn entirely from the eight fixed
    calibration chapters *and* is already large enough to be one. Requiring the
    Requirement 13.1 minimum keeps a small delivery like chapters 1–4 from being
    reported against the calibration range it never claimed; that reads as an
    ordinary Drafting_Batch, which its size satisfies.

    An explicit `--batch-kind` overrides this, so the inference only has to be
    right for the common case. Declaring the kind stays available whenever a
    delivery is ambiguous — including a deliberately undersized calibration
    delivery, which then correctly reports its size.
    """

    requested = frozenset(chapters)
    if len(requested) >= CALIBRATION_BATCH_SIZE_RANGE[0] and requested <= frozenset(
        CALIBRATION_BATCH_CHAPTERS
    ):
        return BATCH_KIND_CALIBRATION
    return BATCH_KIND_DRAFTING


def check_batch_composition(
    chapters: Sequence[int], *, batch_kind: str
) -> Tuple[CheckerDiagnostic, ...]:
    """Enforce the delivered batch size rule for the declared batch kind.

    Reports size against the range Requirement 13.1 or 13.2 sets for that kind,
    and reports any chapter a Calibration_Batch claims that the design's fixed
    eight-chapter set does not contain. Contiguity is deliberately not checked:
    the Calibration_Batch is nonconsecutive by design, and a Drafting_Batch is
    only *normally* one sequence row or cross-cut cluster.
    """

    if batch_kind not in BATCH_SIZE_RANGES:
        raise ValueError("unknown batch kind {0!r}".format(batch_kind))

    diagnostics: List[CheckerDiagnostic] = []
    unique = sorted(set(chapters))
    minimum, maximum = BATCH_SIZE_RANGES[batch_kind]

    if unique and not minimum <= len(unique) <= maximum:
        diagnostics.append(
            _diagnostic(
                "BATCH_SIZE_OUT_OF_RANGE",
                scope=SCOPE_BATCH,
                item="{0} batch".format(batch_kind),
                observed="{0} Chapter_Files ({1})".format(
                    len(unique), ", ".join(str(number) for number in unique)
                ),
                expected="{0}–{1} Chapter_Files".format(minimum, maximum),
            )
        )

    if batch_kind == BATCH_KIND_CALIBRATION:
        allowed = frozenset(CALIBRATION_BATCH_CHAPTERS)
        outside = [number for number in unique if number not in allowed]
        if outside:
            diagnostics.append(
                _diagnostic(
                    "BATCH_CALIBRATION_CHAPTER_UNEXPECTED",
                    scope=SCOPE_BATCH,
                    item="calibration batch",
                    observed="chapters outside the Calibration_Batch: {0}".format(
                        ", ".join(str(number) for number in outside)
                    ),
                    expected="chapters drawn from {0}".format(
                        ", ".join(
                            str(number) for number in CALIBRATION_BATCH_CHAPTERS
                        )
                    ),
                )
            )

    return tuple(diagnostics)


def scope_participating_records(
    index: ReferenceIndex,
    *,
    chapter_scope: Iterable[int],
    chapter_results: Sequence["ChapterCheckResult"] = (),
) -> Mapping[str, Tuple[str, ...]]:
    """Map each record source to the stable IDs it holds inside a scope.

    A record participates when the requested chapters reach it directly: an
    ArcEntry for a scope chapter, that entry's or header's Timeline_ID and
    POV_ID, the profile's Voice_Brief, an assigned or participating Motif_Event,
    a Literal_Phrase_Constraint protecting one of those events, and a Cross_Cut
    a scope chapter declares. This is the same Direct_Planning_Reference notion
    the chapter checks resolve, collected by source document so a declared
    changed reference can be compared against it.
    """

    scope = frozenset(chapter_scope)
    wanted: Dict[str, set] = {
        record_type: set() for record_type in _SCOPE_PARTICIPATION_TYPES
    }

    for entry in index.arc_entries:
        if entry.chapter is None or entry.chapter not in scope:
            continue
        for record_type, field_name in (
            ("TimelineEntry", "timeline_id"),
            ("POVProfile", "pov_id"),
        ):
            value = _stable_id(entry.payload.get(field_name))
            if value is not None:
                wanted[record_type].add(value)
        for key in ("motif_events", "cross_cuts"):
            values = entry.payload.get(key)
            if not isinstance(values, list):
                continue
            record_type = "MotifEvent" if key == "motif_events" else "CrossCut"
            for item in values:
                value = _stable_id(item)
                if value is not None:
                    wanted[record_type].add(value)

    # A Chapter_Header can name a Timeline_ID, POV_ID, or Motif_Event that its
    # ArcEntry does not. That disagreement is reported elsewhere; here both sides
    # count as reached, so a changed reference is never called stale merely
    # because the two records disagree about which ID the chapter uses.
    for result in chapter_results:
        if result.chapter is None or result.chapter not in scope:
            continue
        header = result.document.header
        for record_type, field_name in (
            ("TimelineEntry", "timeline_id"),
            ("POVProfile", "pov_id"),
        ):
            value = _stable_id(header.get(field_name))
            if value is not None:
                wanted[record_type].add(value)
        header_motifs = header.get("motif_events")
        if isinstance(header_motifs, list):
            for item in header_motifs:
                value = _stable_id(item)
                if value is not None:
                    wanted["MotifEvent"].add(value)

    for pov_id in sorted(wanted["POVProfile"]):
        for record in index.lookup("POVProfile", pov_id):
            value = _stable_id(record.payload.get("voice_brief_id"))
            if value is not None:
                wanted["VoiceBrief"].add(value)

    for motif_event_id in sorted(wanted["MotifEvent"]):
        for record in index.of_type("LiteralPhraseConstraint"):
            if _stable_id(record.payload.get("motif_event_id")) == motif_event_id:
                value = _stable_id(record.payload.get("constraint_id"))
                if value is not None:
                    wanted["LiteralPhraseConstraint"].add(value)

    participating: Dict[str, set] = {}
    for entry in index.arc_entries:
        if entry.chapter is not None and entry.chapter in scope:
            participating.setdefault(entry.source, set()).add(
                "chapter {0}".format(entry.chapter)
            )

    for record_type in _SCOPE_PARTICIPATION_TYPES:
        if record_type == "ArcEntry":
            continue
        for record_id in wanted[record_type]:
            for record in index.lookup(record_type, record_id):
                participating.setdefault(record.source, set()).add(record_id)

    return {
        source: tuple(sorted(ids)) for source, ids in sorted(participating.items())
    }


def check_changed_references(
    declared: Sequence[str],
    *,
    index: ReferenceIndex,
    chapter_scope: Iterable[int],
    chapter_results: Sequence["ChapterCheckResult"] = (),
    known_sources: Sequence[str] = DEFAULT_RECORD_SOURCES,
) -> Tuple[CheckerDiagnostic, ...]:
    """Audit the changed cross-document references a batch delivers.

    Requirement 13.3 makes a delivered batch audit its files *and* every changed
    cross-document reference the batch affects. The batch declares those
    documents; this reports the ones the declaration cannot support:

    * a path that is not an allowlisted record source, or that the index could
      not load, leaves the requested scope incomplete rather than merely
      violated, because the audit the batch claims never ran;
    * the same document declared twice is a malformed declaration; and
    * a document holding no record the batch's chapters reach is stale — the
      batch cannot audit a change it does not touch, and a partially
      synchronized delivery must not read as an approved one.

    A record source the scope *does* reach but that the batch does not declare is
    not reported. Most references are unchanged by a given batch, and this
    checker reads one snapshot: it cannot see that a document changed, only that
    a declaration does or does not agree with the requested scope.
    """

    diagnostics: List[CheckerDiagnostic] = []
    allowlist = frozenset(known_sources)
    loaded = frozenset(index.sources)
    scope = sorted(set(chapter_scope))
    participating = scope_participating_records(
        index, chapter_scope=scope, chapter_results=chapter_results
    )

    seen: Dict[str, int] = {}
    for raw in declared:
        relative = _normalized_text(str(raw)).replace("\\", "/").strip("/")
        seen[relative] = seen.get(relative, 0) + 1
        if seen[relative] > 1:
            diagnostics.append(
                _diagnostic(
                    "CHANGED_REFERENCE_DUPLICATE",
                    scope=SCOPE_BATCH,
                    item=relative,
                    observed="declared {0} times".format(seen[relative]),
                    expected="each changed reference declared once",
                    disposition=DISPOSITION_INCOMPLETE,
                )
            )
            continue

        if relative not in allowlist:
            diagnostics.append(
                _diagnostic(
                    "CHANGED_REFERENCE_UNKNOWN",
                    scope=SCOPE_BATCH,
                    item=relative,
                    observed="not an allowlisted record source",
                    expected="one of {0}".format(", ".join(sorted(allowlist))),
                    disposition=DISPOSITION_INCOMPLETE,
                )
            )
            continue

        if relative not in loaded:
            diagnostics.append(
                _diagnostic(
                    "CHANGED_REFERENCE_UNREADABLE",
                    scope=SCOPE_BATCH,
                    item=relative,
                    observed="the record source did not load for this scope",
                    expected="a readable record source to audit the change against",
                    disposition=DISPOSITION_INCOMPLETE,
                )
            )
            continue

        reached = participating.get(relative, ())
        if not reached:
            diagnostics.append(
                _diagnostic(
                    "CHANGED_REFERENCE_STALE",
                    scope=SCOPE_BATCH,
                    item=relative,
                    observed="no record in this document is reached by chapters "
                    "{0}".format(
                        ", ".join(str(number) for number in scope) or "(none)"
                    ),
                    expected=(
                        "a changed reference the delivered batch actually "
                        "reaches, or a batch scope containing the changed records"
                    ),
                )
            )

    return tuple(diagnostics)


# ---------------------------------------------------------------------------
# Same_POV_Run: two independent bounds
#
# A Same_POV_Run is a maximal uninterrupted sequence of chapters sharing one
# POV_ID on the *global* sequence, so a Story_Movement boundary counts like any
# other adjacency. Planning evaluates the word bound from `estimated_words` and
# the completed Manuscript from each declared `words`; the run grammar is the
# same either way, so it is computed once here and fed from either source.
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class POVRun:
    """One maximal same-POV run and the word values available for it."""

    pov_id: str
    chapters: Tuple[int, ...]
    words: Tuple[Optional[int], ...]

    @property
    def chapter_count(self) -> int:
        return len(self.chapters)

    @property
    def total_words(self) -> Optional[int]:
        """The combined Prose_Words, or `None` when any member is unknown.

        `None` is not zero and not a pass. A run whose total cannot be computed
        is reported as incomplete input rather than silently treated as short
        enough, which is the whole reason `estimated_words` is required for a run
        of two or more chapters.
        """

        if any(value is None for value in self.words):
            return None
        return sum(int(value) for value in self.words if value is not None)

    @property
    def label(self) -> str:
        return "{0} chapters {1}".format(
            self.pov_id, ",".join(str(number) for number in self.chapters)
        )


def pov_runs(
    assignments: Sequence[Tuple[int, str, Optional[int]]],
) -> Tuple[POVRun, ...]:
    """Group `(chapter, pov_id, words)` triples into maximal same-POV runs.

    Input is sorted by chapter first, so a caller may pass entries in document
    order. Adjacency is decided by consecutive position in the sorted sequence
    rather than by consecutive chapter numbers: a partial scope has gaps, and
    inventing a break at a gap would silently split a run that the complete
    outline holds together. Whole-book contiguity is checked separately.
    """

    ordered = sorted(assignments, key=lambda item: item[0])
    runs: List[POVRun] = []
    current_pov: Optional[str] = None
    chapters: List[int] = []
    words: List[Optional[int]] = []

    for chapter, pov_id, word_count in ordered:
        if pov_id != current_pov:
            if current_pov is not None:
                runs.append(
                    POVRun(
                        pov_id=current_pov,
                        chapters=tuple(chapters),
                        words=tuple(words),
                    )
                )
            current_pov = pov_id
            chapters = []
            words = []
        chapters.append(chapter)
        words.append(word_count)

    if current_pov is not None:
        runs.append(
            POVRun(pov_id=current_pov, chapters=tuple(chapters), words=tuple(words))
        )
    return tuple(runs)


def check_pov_runs(
    runs: Sequence[POVRun], *, scope: str, source: str
) -> Tuple[CheckerDiagnostic, ...]:
    """Report every run over the chapter cap or the combined word limit.

    Both bounds are evaluated for every run, so one run can report both. Per
    Requirement 12.16 each diagnostic names the run's chapters, the observed
    total, and the expected limit. `source` names where the word values came from
    so the reader knows whether an estimate or a declared count was measured.
    """

    diagnostics: List[CheckerDiagnostic] = []
    for run in runs:
        if run.chapter_count > POV_RUN_CHAPTER_LIMIT:
            diagnostics.append(
                _diagnostic(
                    "POV_RUN_CHAPTER_LIMIT",
                    scope=scope,
                    item=run.label,
                    observed="{0} consecutive Chapter_Files".format(run.chapter_count),
                    expected="at most {0} consecutive Chapter_Files under one "
                    "POV_ID".format(POV_RUN_CHAPTER_LIMIT),
                    details=(("source", source),),
                )
            )
        total = run.total_words
        if total is None:
            if run.chapter_count < 2:
                # A single-chapter run needs no estimate: the Hard_Chapter_Maximum
                # already bounds it, and `estimated_words` may be null there.
                continue
            unknown = [
                str(chapter)
                for chapter, value in zip(run.chapters, run.words)
                if value is None
            ]
            diagnostics.append(
                _diagnostic(
                    "POV_RUN_WORDS_UNKNOWN",
                    scope=scope,
                    item=run.label,
                    observed="no word value for chapter {0}".format(
                        ",".join(unknown)
                    ),
                    expected="a word value for every chapter in a run of two or "
                    "more, so the {0}-word run limit can be "
                    "evaluated".format(POV_RUN_WORD_LIMIT),
                    disposition=DISPOSITION_INCOMPLETE,
                    details=(("source", source),),
                )
            )
            continue
        if total > POV_RUN_WORD_LIMIT:
            diagnostics.append(
                _diagnostic(
                    "POV_RUN_WORD_LIMIT",
                    scope=scope,
                    item=run.label,
                    observed="{0} combined Prose_Words".format(total),
                    expected="at most {0} combined Prose_Words in one "
                    "Same_POV_Run".format(POV_RUN_WORD_LIMIT),
                    details=(("source", source),),
                )
            )
    return tuple(diagnostics)


def arc_entry_pov_assignments(
    entries: Sequence[ArcEntryRecord],
) -> Tuple[Tuple[int, str, Optional[int]], ...]:
    """Planning-side `(chapter, pov_id, estimated_words)` triples.

    Entries whose chapter or `pov_id` will not parse are skipped: their own
    structural diagnostics already fired, and guessing a POV would invent a run
    boundary. `estimated_words` stays `None` when absent or malformed so the run
    check reports it as unknown rather than as zero.
    """

    assignments: List[Tuple[int, str, Optional[int]]] = []
    for entry in entries:
        if entry.chapter is None:
            continue
        pov_id = _stable_id(entry.payload.get("pov_id"))
        if pov_id is None:
            continue
        estimated = entry.payload.get("estimated_words")
        words = (
            estimated
            if isinstance(estimated, int) and not isinstance(estimated, bool)
            else None
        )
        assignments.append((entry.chapter, pov_id, words))
    return tuple(assignments)


# ---------------------------------------------------------------------------
# POV_Roster size, one-to-one identity, entity type, and Anchor coverage
# ---------------------------------------------------------------------------


def check_pov_roster(
    index: ReferenceIndex,
    *,
    chapter_movements: Optional[Mapping[str, frozenset]] = None,
) -> Tuple[CheckerDiagnostic, ...]:
    """Roster size, human entity type, single Anchor, and Anchor coverage.

    `chapter_movements` maps POV_ID to the set of movements that POV actually
    holds a chapter in. It is supplied only at global scope, because Requirement
    4.9's coverage obligation is a whole-book fact: a batch legitimately contains
    one movement. When it is `None` the coverage checks are skipped and the
    declared `movement_coverage` is left alone rather than compared against a
    partial view.

    The Character_ID/POV_ID bijection itself is checked in
    `check_pov_voice_brief_pairing`, which owns the one-to-one mapping. This adds
    only the roster-wide obligations of Requirements 4.1, 4.8, 4.10, and 11.7.
    """

    profiles = index.of_type("POVProfile")
    diagnostics: List[CheckerDiagnostic] = []

    minimum, maximum = POV_ROSTER_SIZE_RANGE
    if profiles and not minimum <= len(profiles) <= maximum:
        diagnostics.append(
            _diagnostic(
                "POV_ROSTER_SIZE",
                scope=SCOPE_PLANNING,
                item="planning/pov-roster.md",
                observed="{0} POVProfile records".format(len(profiles)),
                expected="{0}\u2013{1} human POVs".format(minimum, maximum),
            )
        )

    anchors: List[str] = []
    for profile in profiles:
        pov_id = _stable_id(profile.payload.get("pov_id"))
        label = pov_id or profile.identity

        entity_type = profile.payload.get("entity_type")
        if entity_type != POV_ENTITY_TYPE_HUMAN:
            # Requirement 4.10: no POV is reserved for the Foreign_Signal or for
            # any actual, alleged, or hypothesized adversary behind it. The
            # schema expresses that as a closed single-value enum, so anything
            # other than `human` is the prohibited case.
            diagnostics.append(
                profile.violation(
                    "POV_ENTITY_TYPE",
                    item=label,
                    observed="entity_type={0!r}".format(entity_type),
                    expected="exactly {0!r}; a Foreign_Signal or adversary POV is "
                    "prohibited".format(POV_ENTITY_TYPE_HUMAN),
                )
            )

        anchor = profile.payload.get("anchor")
        if not _is_bool(anchor):
            diagnostics.append(
                profile.malformed(
                    "POV_ANCHOR_MALFORMED",
                    observed="anchor={0!r}".format(anchor),
                    expected="a boolean",
                )
            )
        elif anchor and pov_id is not None:
            anchors.append(pov_id)

        declared = profile.payload.get("movement_coverage")
        coverage = _movement_sequence(declared)
        if coverage is None:
            diagnostics.append(
                profile.malformed(
                    "POV_MOVEMENT_COVERAGE_MALFORMED",
                    observed="movement_coverage={0!r}".format(declared),
                    expected="a unique nonempty list of movement names",
                )
            )
        elif chapter_movements is not None and pov_id is not None:
            observed = chapter_movements.get(pov_id, frozenset())
            if frozenset(coverage) != observed:
                diagnostics.append(
                    profile.violation(
                        "POV_MOVEMENT_COVERAGE_DISAGREEMENT",
                        item=label,
                        observed="declared={0} assigned={1}".format(
                            ",".join(coverage) or "(none)",
                            ",".join(sorted(observed)) or "(none)",
                        ),
                        expected="declared movement_coverage equal to the "
                        "movements the Arc_Outline assigns this POV",
                    )
                )

    if profiles and len(anchors) != 1:
        diagnostics.append(
            _diagnostic(
                "POV_ANCHOR_COUNT",
                scope=SCOPE_PLANNING,
                item="planning/pov-roster.md",
                observed="{0} anchor profiles: {1}".format(
                    len(anchors), ",".join(sorted(anchors)) or "(none)"
                ),
                expected="exactly one Anchor_POV",
            )
        )
    elif anchors and chapter_movements is not None:
        anchor_id = anchors[0]
        held = chapter_movements.get(anchor_id, frozenset())
        missing = [movement for movement in MOVEMENTS if movement not in held]
        if missing:
            diagnostics.append(
                _diagnostic(
                    "ANCHOR_MOVEMENT_COVERAGE",
                    scope=SCOPE_GLOBAL,
                    item=anchor_id,
                    observed="no Chapter_File in {0}".format(",".join(missing)),
                    expected="at least one Anchor_POV Chapter_File in every "
                    "Story_Movement",
                )
            )

    diagnostics.extend(_check_provisional_pov_loads(profiles))
    return tuple(diagnostics)


def _movement_sequence(value: Any) -> Optional[Tuple[str, ...]]:
    if not isinstance(value, list) or not value:
        return None
    names: List[str] = []
    for member in value:
        if not isinstance(member, str):
            return None
        name = _normalized_text(member).strip()
        if name not in MOVEMENTS or name in names:
            return None
        names.append(name)
    return tuple(names)


def _check_provisional_pov_loads(
    profiles: Sequence[PlanningRecord],
) -> Tuple[CheckerDiagnostic, ...]:
    """The `provisional_load` object's own arithmetic, then the 56/32/33/7 vector.

    Requirement 15.3 fixes the load vector, so a changed vector is a violation
    even when each individual object is internally consistent. The comparison is
    over the sorted multiset of totals, because Requirement 12.11 keeps which
    selected name owns which number outside automated pass/fail.
    """

    diagnostics: List[CheckerDiagnostic] = []
    totals: List[int] = []
    for profile in profiles:
        label = _stable_id(profile.payload.get("pov_id")) or profile.identity
        load = profile.payload.get("provisional_load")
        expected_keys = MOVEMENTS + ("total",)
        if not isinstance(load, dict) or set(load) != set(expected_keys):
            diagnostics.append(
                profile.malformed(
                    "POV_PROVISIONAL_LOAD_MALFORMED",
                    observed="provisional_load {0}".format(
                        _key_set_report(load, expected_keys)
                        if isinstance(load, dict)
                        else "is not an object"
                    ),
                    expected="exactly {0}".format(", ".join(expected_keys)),
                )
            )
            continue
        if any(
            not isinstance(load[key], int)
            or isinstance(load[key], bool)
            or load[key] < 0
            for key in expected_keys
        ):
            diagnostics.append(
                profile.malformed(
                    "POV_PROVISIONAL_LOAD_MALFORMED",
                    observed="provisional_load={0!r}".format(load),
                    expected="nonnegative integers for every movement and total",
                )
            )
            continue
        movement_sum = sum(int(load[movement]) for movement in MOVEMENTS)
        if movement_sum != int(load["total"]):
            diagnostics.append(
                profile.violation(
                    "POV_PROVISIONAL_LOAD_TOTAL",
                    item=label,
                    observed="movements sum to {0}, total={1}".format(
                        movement_sum, load["total"]
                    ),
                    expected="the four movement counts to sum to total",
                )
            )
            continue
        totals.append(int(load["total"]))

    if totals and tuple(sorted(totals)) != PROVISIONAL_POV_LOAD_TOTALS:
        diagnostics.append(
            _diagnostic(
                "POV_PROVISIONAL_LOAD_VECTOR",
                scope=SCOPE_PLANNING,
                item="planning/pov-roster.md",
                observed="totals {0}".format(
                    "/".join(str(value) for value in sorted(totals, reverse=True))
                ),
                expected="the unchanged {0} load vector".format(
                    "/".join(
                        str(value)
                        for value in sorted(PROVISIONAL_POV_LOAD_TOTALS, reverse=True)
                    )
                ),
            )
        )
    return tuple(diagnostics)


# ---------------------------------------------------------------------------
# Whole-outline sequence, movement blocks, and outline/file bijection
# ---------------------------------------------------------------------------


def check_outline_sequence(
    entries: Sequence[ArcEntryRecord],
) -> Tuple[CheckerDiagnostic, ...]:
    """Requirement 1.3: the complete outline is exactly `1..N`, once each.

    Duplicates and gaps are reported separately because they are different
    authoring mistakes with different repairs, and both are structural: a plan
    with either is incomplete input rather than a continuity violation.
    """

    diagnostics: List[CheckerDiagnostic] = []
    by_chapter: Dict[int, List[str]] = {}
    for entry in entries:
        if entry.chapter is None:
            continue
        by_chapter.setdefault(entry.chapter, []).append(entry.identity)

    for chapter in sorted(by_chapter):
        claimants = sorted(by_chapter[chapter])
        if len(claimants) > 1:
            diagnostics.append(
                _diagnostic(
                    "OUTLINE_CHAPTER_DUPLICATE",
                    scope=SCOPE_GLOBAL,
                    item="chapter {0}".format(chapter),
                    observed=", ".join(claimants),
                    expected="exactly one ArcEntry per planned Chapter_File",
                    disposition=DISPOSITION_INCOMPLETE,
                )
            )

    if not by_chapter:
        return tuple(diagnostics)

    numbers = sorted(by_chapter)
    expected_range = list(range(1, len(numbers) + 1))
    if numbers != expected_range:
        missing = sorted(set(expected_range) - set(numbers))
        unexpected = sorted(set(numbers) - set(expected_range))
        observed = []
        if missing:
            observed.append("missing={0}".format(_compact_numbers(missing)))
        if unexpected:
            observed.append("outside 1..{0}={1}".format(
                len(numbers), _compact_numbers(unexpected)
            ))
        diagnostics.append(
            _diagnostic(
                "OUTLINE_SEQUENCE_RANGE",
                scope=SCOPE_GLOBAL,
                item="planning/arc-outline.md",
                observed="; ".join(observed),
                expected="the uninterrupted integers 1..{0}".format(len(numbers)),
                disposition=DISPOSITION_INCOMPLETE,
            )
        )

    duplicate_filenames: Dict[str, List[int]] = {}
    for entry in entries:
        if entry.chapter is None or entry.filename is None:
            continue
        duplicate_filenames.setdefault(entry.filename, []).append(entry.chapter)
    for filename in sorted(duplicate_filenames):
        chapters = sorted(duplicate_filenames[filename])
        if len(chapters) > 1:
            diagnostics.append(
                _diagnostic(
                    "OUTLINE_FILENAME_DUPLICATE",
                    scope=SCOPE_GLOBAL,
                    item=filename,
                    observed="claimed by chapters {0}".format(
                        ",".join(str(number) for number in chapters)
                    ),
                    expected="one filename per planned Chapter_File",
                    disposition=DISPOSITION_INCOMPLETE,
                )
            )
    return tuple(diagnostics)


def _compact_numbers(numbers: Sequence[int]) -> str:
    """Render a sorted integer list as compact ranges: `1,4-7,12`."""

    ordered = sorted(set(numbers))
    if not ordered:
        return "(none)"
    spans: List[str] = []
    start = previous = ordered[0]
    for number in ordered[1:]:
        if number == previous + 1:
            previous = number
            continue
        spans.append(str(start) if start == previous else "{0}-{1}".format(start, previous))
        start = previous = number
    spans.append(str(start) if start == previous else "{0}-{1}".format(start, previous))
    return ",".join(spans)


def check_movement_blocks(
    entries: Sequence[ArcEntryRecord],
) -> Tuple[CheckerDiagnostic, ...]:
    """Requirement 11.4 and 3.1: four contiguous blocks in the required order.

    Contiguity and order are one fact read two ways, so both come from the same
    walk: the movement of each chapter in sequence must change at most three
    times, and each change must move forward through `MOVEMENTS`. A movement that
    reappears after a different one has begun is a discontiguous block, reported
    at the chapter where it reappears.
    """

    ordered = [
        entry
        for entry in sorted(
            (entry for entry in entries if entry.chapter is not None),
            key=lambda item: int(item.chapter or 0),
        )
        if entry.movement in MOVEMENT_ORDER
    ]
    if not ordered:
        return ()

    diagnostics: List[CheckerDiagnostic] = []
    seen: List[str] = []
    previous: Optional[ArcEntryRecord] = None
    for entry in ordered:
        movement = str(entry.movement)
        if previous is not None and movement == str(previous.movement):
            previous = entry
            continue
        if movement in seen:
            diagnostics.append(
                _diagnostic(
                    "MOVEMENT_BLOCK_DISCONTIGUOUS",
                    scope=SCOPE_GLOBAL,
                    item="chapter {0}".format(entry.chapter),
                    observed="{0} resumes after {1}".format(
                        movement, str(previous.movement) if previous else "(none)"
                    ),
                    expected="one contiguous block of chapters per "
                    "Story_Movement",
                )
            )
        else:
            if previous is not None and MOVEMENT_ORDER[movement] <= MOVEMENT_ORDER[
                str(previous.movement)
            ]:
                diagnostics.append(
                    _diagnostic(
                        "MOVEMENT_BLOCK_ORDER",
                        scope=SCOPE_GLOBAL,
                        item="chapter {0}".format(entry.chapter),
                        observed="{0} begins after {1}".format(
                            movement, str(previous.movement)
                        ),
                        expected="movement blocks in the order {0}".format(
                            ", ".join(MOVEMENTS)
                        ),
                    )
                )
            seen.append(movement)
        previous = entry

    absent = [movement for movement in MOVEMENTS if movement not in seen]
    if absent:
        diagnostics.append(
            _diagnostic(
                "MOVEMENT_BLOCK_MISSING",
                scope=SCOPE_GLOBAL,
                item="planning/arc-outline.md",
                observed="no chapter in {0}".format(",".join(absent)),
                expected="exactly four Story_Movements: {0}".format(
                    ", ".join(MOVEMENTS)
                ),
                disposition=DISPOSITION_INCOMPLETE,
            )
        )
    return tuple(diagnostics)


def check_outline_file_bijection(
    entries: Sequence[ArcEntryRecord],
    results: Sequence["ChapterCheckResult"],
) -> Tuple[CheckerDiagnostic, ...]:
    """Requirement 11.3: one Chapter_File per ArcEntry and one entry per file.

    Matched on the manuscript-relative filename the ArcEntry records, which is
    the only identity both sides independently declare. A chapter-number
    disagreement between a file and its entry is already reported by the
    chapter-local agreement checks; repeating it here as a bijection failure
    would double-report one mistake.
    """

    planned = {
        entry.filename: entry
        for entry in entries
        if entry.filename is not None and entry.chapter is not None
    }
    present = {result.relative_path: result for result in results}

    diagnostics: List[CheckerDiagnostic] = []
    for filename in sorted(set(planned) - set(present)):
        entry = planned[filename]
        diagnostics.append(
            _diagnostic(
                "OUTLINE_ENTRY_WITHOUT_FILE",
                scope=SCOPE_GLOBAL,
                item=filename,
                observed="planned by chapter {0} with no Chapter_File".format(
                    entry.chapter
                ),
                expected="exactly one Chapter_File for every ArcEntry",
                disposition=DISPOSITION_INCOMPLETE,
                related=(entry.identity,),
            )
        )
    for filename in sorted(set(present) - set(planned)):
        diagnostics.append(
            _diagnostic(
                "CHAPTER_FILE_WITHOUT_OUTLINE_ENTRY",
                scope=SCOPE_GLOBAL,
                item=filename,
                observed="present with no ArcEntry claiming this filename",
                expected="exactly one ArcEntry for every Chapter_File",
                disposition=DISPOSITION_INCOMPLETE,
            )
        )
    return tuple(diagnostics)


# ---------------------------------------------------------------------------
# Whole-book length facts: normal share, movement scale, Final_Targets
# ---------------------------------------------------------------------------


def check_normal_share(
    results: Sequence["ChapterCheckResult"],
) -> Tuple[CheckerDiagnostic, ...]:
    """Requirement 2.8: at least 80 percent of all final chapters are `normal`.

    The denominator is every final Chapter_File, including outliers, and the
    comparison is exact integer arithmetic so the 79/100 and 80/100 boundary
    cannot move on a floating-point rounding. Observed classes are derived from
    observed word counts rather than declared `length_class`, because a declared
    class that disagrees with its count is a separate diagnostic and must not be
    able to buy a passing share.
    """

    classes = [
        result.length_report.observed_length_class
        for result in results
        if result.length_report is not None
    ]
    denominator = len(classes)
    if denominator == 0:
        return ()
    normal = sum(1 for value in classes if value == "normal")
    minimum_numerator, minimum_denominator = NORMAL_SHARE_MINIMUM
    if normal * minimum_denominator >= minimum_numerator * denominator:
        return ()
    return (
        _diagnostic(
            "NORMAL_SHARE",
            scope=SCOPE_GLOBAL,
            item="manuscript",
            observed="{0} of {1} final Chapter_Files are normal".format(
                normal, denominator
            ),
            expected="at least {0} percent of all final Chapter_Files within "
            "{1}\u2013{2} Prose_Words".format(
                minimum_numerator, *NORMAL_CHAPTER_RANGE
            ),
        ),
    )


def movement_word_totals(
    results: Sequence["ChapterCheckResult"],
) -> Mapping[str, int]:
    """Observed Prose_Words per Story_Movement, from observed counts only."""

    totals: Dict[str, int] = {}
    for result in results:
        movement = result.movement
        if movement not in MOVEMENT_ORDER or result.length_report is None:
            continue
        totals[str(movement)] = totals.get(str(movement), 0) + int(
            result.length_report.observed_words
        )
    return totals


def check_movement_scale(
    totals: Mapping[str, int],
) -> Tuple[CheckerDiagnostic, ...]:
    """Requirements 3.7, 3.8, and 11.6: Mindwars longest, Coda shortest.

    Both relationships are strict, and both are evaluated only when all four
    movements have a total. A partially drafted manuscript cannot answer the
    question, so a missing movement is reported as incomplete rather than
    letting three totals decide a four-way comparison.
    """

    absent = [movement for movement in MOVEMENTS if movement not in totals]
    if absent:
        return (
            _diagnostic(
                "MOVEMENT_SCALE_INCOMPLETE",
                scope=SCOPE_GLOBAL,
                item="manuscript",
                observed="no Prose_Words counted for {0}".format(",".join(absent)),
                expected="a Prose_Word total for every Story_Movement before "
                "the length relationships are evaluated",
                disposition=DISPOSITION_INCOMPLETE,
            ),
        )

    diagnostics: List[CheckerDiagnostic] = []
    mindwars = totals[MINDWARS_MOVEMENT]
    others = {
        movement: total
        for movement, total in totals.items()
        if movement != MINDWARS_MOVEMENT
    }
    not_shorter = sorted(
        movement for movement, total in others.items() if total >= mindwars
    )
    if not_shorter:
        diagnostics.append(
            _diagnostic(
                "MOVEMENT_SCALE_MINDWARS_NOT_LONGEST",
                scope=SCOPE_GLOBAL,
                item=MINDWARS_MOVEMENT,
                observed="{0} Prose_Words, not more than {1}".format(
                    mindwars,
                    ", ".join(
                        "{0}={1}".format(name, others[name]) for name in not_shorter
                    ),
                ),
                expected="the Mindwars_Part strictly longest by Prose_Words",
            )
        )

    coda = totals["aftermath_coda"]
    main_parts = {
        movement: total
        for movement, total in totals.items()
        if movement != "aftermath_coda"
    }
    not_longer = sorted(
        movement for movement, total in main_parts.items() if total <= coda
    )
    if not_longer:
        diagnostics.append(
            _diagnostic(
                "MOVEMENT_SCALE_CODA_NOT_SHORTEST",
                scope=SCOPE_GLOBAL,
                item="aftermath_coda",
                observed="{0} Prose_Words, not fewer than {1}".format(
                    coda,
                    ", ".join(
                        "{0}={1}".format(name, main_parts[name])
                        for name in not_longer
                    ),
                ),
                expected="the Aftermath_Coda strictly shortest by Prose_Words",
            )
        )
    return tuple(diagnostics)


@dataclass(frozen=True)
class FinalTargets:
    """The approved exact chapter count and inclusive total Prose_Word range."""

    chapter_count: int
    minimum_words: int
    maximum_words: int


def check_final_targets(
    targets: Optional[FinalTargets],
    *,
    chapter_count: int,
    total_words: int,
) -> Tuple[CheckerDiagnostic, ...]:
    """Requirements 11.5 and 12.7: observed totals against the Final_Targets.

    Reports the observed facts against the approved targets. A `None` target set
    is a missing Final_Prerequisite reported by the Baseline check, not here, so
    this stays a pure comparison with nothing to infer.
    """

    if targets is None:
        return ()

    diagnostics: List[CheckerDiagnostic] = []
    if chapter_count != targets.chapter_count:
        diagnostics.append(
            _diagnostic(
                "FINAL_TARGET_CHAPTER_COUNT",
                scope=SCOPE_GLOBAL,
                item="manuscript",
                observed="{0} Chapter_Files".format(chapter_count),
                expected="exactly {0} planned Chapter_Files".format(
                    targets.chapter_count
                ),
            )
        )
    if not targets.minimum_words <= total_words <= targets.maximum_words:
        diagnostics.append(
            _diagnostic(
                "FINAL_TARGET_TOTAL_WORDS",
                scope=SCOPE_GLOBAL,
                item="manuscript",
                observed="{0} total Prose_Words".format(total_words),
                expected="within the inclusive range {0}\u2013{1}".format(
                    targets.minimum_words, targets.maximum_words
                ),
            )
        )
    return tuple(diagnostics)


# ---------------------------------------------------------------------------
# Whole-book literal totals and the declared Final_Passage span
#
# The chapter-local check deliberately refuses to turn a subset into a total.
# This is the scope that may: it holds every Chapter_File, so an in-scope total
# is decidable. The Final_Passage is still never guessed from typography — it is
# read from the machine-declared span the ledger maintains, and a missing or
# unlocatable span makes the gate incomplete instead.
# ---------------------------------------------------------------------------


def locate_literal_span(
    span: Mapping[str, Any], prose: str
) -> Tuple[Optional[Tuple[int, int]], Optional[str]]:
    """Resolve a declared span to `(start, end)` offsets in normalized prose.

    Returns the offsets, or a reason the span could not be located. Only the four
    boundary kinds the schema defines are honored, and a literal marker must occur
    exactly once: two markers would make the span ambiguous, and choosing one
    would be a guess.
    """

    bounds: Dict[str, int] = {}
    for key, default in (("start_boundary", 0), ("end_boundary", len(prose))):
        boundary = span.get(key)
        if not isinstance(boundary, dict):
            return None, "{0} is not a boundary object".format(key)
        kind = boundary.get("kind")
        value = boundary.get("value")
        if kind in ("start-of-prose", "end-of-prose"):
            bounds[key] = default
            continue
        if kind == "line-number":
            if not _is_chapter_number(value):
                return None, "{0} line-number is not a positive integer".format(key)
            lines = prose.split("\n")
            if int(value) > len(lines):
                return None, "{0} line {1} is past the Prose_Body's {2} lines".format(
                    key, value, len(lines)
                )
            offset = sum(len(line) + 1 for line in lines[: int(value) - 1])
            bounds[key] = offset if key == "start_boundary" else min(
                offset + len(lines[int(value) - 1]), len(prose)
            )
            continue
        if kind == "literal-marker":
            if not isinstance(value, str):
                return None, "{0} literal-marker has no marker text".format(key)
            marker = normalize_prose(value)
            offsets = _non_overlapping_occurrence_offsets(prose, marker)
            if len(offsets) != 1:
                return None, "{0} marker {1!r} occurs {2} times".format(
                    key, value, len(offsets)
                )
            bounds[key] = (
                offsets[0] + len(marker) if key == "start_boundary" else offsets[0]
            )
            continue
        return None, "{0} kind={1!r} is not a declared boundary kind".format(key, kind)

    start, end = bounds["start_boundary"], bounds["end_boundary"]
    if start > end:
        return None, "start boundary at {0} is after end boundary at {1}".format(
            start, end
        )
    return (start, end), None


def check_whole_book_literal_constraints(
    results: Sequence["ChapterCheckResult"], index: ReferenceIndex
) -> Tuple[CheckerDiagnostic, ...]:
    """Requirements 7.16 and 11.8: in-scope totals and declared span placement.

    Only rules that declare an in-scope total are evaluated here, because a rule
    without one — `Did I say yes?` — deliberately fixes no count and is fully
    handled by the chapter-local outside-scope check.
    """

    prose_by_path: Dict[str, str] = {}
    chapter_by_path: Dict[str, Optional[int]] = {}
    for result in results:
        if not result.document.boundary_resolved or result.document.prose_body is None:
            continue
        prose_by_path[result.relative_path] = normalize_prose(
            result.document.prose_body
        )
        chapter_by_path[result.relative_path] = result.chapter

    diagnostics: List[CheckerDiagnostic] = []
    for record in index.of_type("LiteralPhraseConstraint"):
        constraint_id = _stable_id(record.payload.get("constraint_id"))
        if constraint_id is None or index.is_duplicated(
            "LiteralPhraseConstraint", constraint_id
        ):
            continue
        rule, _record_diagnostics = _parse_literal_constraint_rule(record)
        if rule is None or not rule.has_in_scope_total:
            continue

        if rule.allowed_span is None:
            # A total with no declared span would have to be counted over a
            # guessed region. Refuse instead.
            diagnostics.append(
                record.malformed(
                    "LITERAL_CONSTRAINT_SPAN_MISSING",
                    observed="an in-scope total with allowed_span=null",
                    expected="a declared machine-readable span for any rule "
                    "fixing an in-scope count",
                )
            )
            continue

        missing = [path for path in rule.allowed_files if path not in prose_by_path]
        if missing or not rule.allowed_files:
            diagnostics.append(
                _diagnostic(
                    "LITERAL_CONSTRAINT_SCOPE_INCOMPLETE",
                    scope=SCOPE_GLOBAL,
                    item=constraint_id,
                    observed="no readable Prose_Body for {0}".format(
                        ", ".join(missing) if missing else "(no allowed_files)"
                    ),
                    expected="every allowed file present before an in-scope total "
                    "is counted",
                    disposition=DISPOSITION_INCOMPLETE,
                    related=(record.identity,),
                )
            )
            continue

        span_chapter = rule.allowed_span.get("chapter")
        span_paths = [
            path
            for path in rule.allowed_files
            if chapter_by_path.get(path) == span_chapter
        ]
        if len(span_paths) != 1:
            diagnostics.append(
                _diagnostic(
                    "LITERAL_CONSTRAINT_SPAN_UNRESOLVED",
                    scope=SCOPE_GLOBAL,
                    item=constraint_id,
                    observed="{0} allowed files claim chapter {1}".format(
                        len(span_paths), span_chapter
                    ),
                    expected="exactly one allowed Chapter_File for the declared "
                    "span chapter",
                    disposition=DISPOSITION_INCOMPLETE,
                    related=(record.identity,),
                )
            )
            continue

        span_path = span_paths[0]
        bounds, reason = locate_literal_span(
            rule.allowed_span, prose_by_path[span_path]
        )
        if bounds is None:
            diagnostics.append(
                _diagnostic(
                    "LITERAL_CONSTRAINT_SPAN_UNRESOLVED",
                    scope=SCOPE_GLOBAL,
                    item=constraint_id,
                    observed=str(reason),
                    expected="a locatable declared span; the checker does not "
                    "guess a literary passage from typography",
                    disposition=DISPOSITION_INCOMPLETE,
                    details=(("file", span_path),),
                    related=(record.identity,),
                )
            )
            continue

        start, end = bounds
        inside = 0
        for offset in _non_overlapping_occurrence_offsets(
            prose_by_path[span_path], rule.exact_phrase
        ):
            if start <= offset and offset + len(rule.exact_phrase) <= end:
                inside += 1
            else:
                diagnostics.append(
                    _diagnostic(
                        rule.diagnostic_code,
                        scope=SCOPE_GLOBAL,
                        item=span_path,
                        observed="occurrence at normalized offset {0}, outside the "
                        "declared span {1}-{2}".format(offset, start, end),
                        expected="every in-scope occurrence inside the declared "
                        "span",
                        details=(("protected_phrase", rule.exact_phrase),),
                        related=(record.identity,),
                    )
                )

        diagnostics.extend(
            _check_in_scope_total(rule, observed=inside, item=span_path)
        )
    return tuple(diagnostics)


def _check_in_scope_total(
    rule: _LiteralConstraintRule, *, observed: int, item: str
) -> Tuple[CheckerDiagnostic, ...]:
    """Compare an observed in-scope count against the ledgered bound."""

    if rule.exact_in_scope is not None and observed != rule.exact_in_scope:
        return (
            _diagnostic(
                rule.diagnostic_code,
                scope=SCOPE_GLOBAL,
                item=item,
                observed="{0} in-scope occurrences".format(observed),
                expected="exactly {0} inside the declared span".format(
                    rule.exact_in_scope
                ),
                details=(("protected_phrase", rule.exact_phrase),),
                related=(rule.record.identity,),
            ),
        )
    diagnostics: List[CheckerDiagnostic] = []
    if rule.minimum_in_scope is not None and observed < rule.minimum_in_scope:
        diagnostics.append(
            _diagnostic(
                rule.diagnostic_code,
                scope=SCOPE_GLOBAL,
                item=item,
                observed="{0} in-scope occurrences".format(observed),
                expected="at least {0} inside the declared span".format(
                    rule.minimum_in_scope
                ),
                details=(("protected_phrase", rule.exact_phrase),),
                related=(rule.record.identity,),
            )
        )
    if rule.maximum_in_scope is not None and observed > rule.maximum_in_scope:
        diagnostics.append(
            _diagnostic(
                rule.diagnostic_code,
                scope=SCOPE_GLOBAL,
                item=item,
                observed="{0} in-scope occurrences".format(observed),
                expected="at most {0} inside the declared span".format(
                    rule.maximum_in_scope
                ),
                details=(("protected_phrase", rule.exact_phrase),),
                related=(rule.record.identity,),
            )
        )
    return tuple(diagnostics)


# ---------------------------------------------------------------------------
# Whole-book Motif_Event family totals
# ---------------------------------------------------------------------------

# The motif families whose whole-book event count and movement placement the
# requirements fix exactly. Each entry is the family name, the required number of
# events, and the movements those events must occupy, in order.
CLOSED_MOTIF_FAMILY_TOTALS: Mapping[str, Mapping[str, Any]] = {
    # Requirement 7.12: exactly two kettle events, both in the Aftermath_Coda.
    "kettle": {
        "count": 2,
        "movements": ("aftermath_coda", "aftermath_coda"),
        "requirement": "7.12",
    },
    # Requirement 7.17: the Record_Progression is exactly three events, one per
    # movement from Private Defense onward.
    "record progression": {
        "count": 3,
        "movements": (
            "private_defense_part",
            MINDWARS_MOVEMENT,
            "aftermath_coda",
        ),
        "requirement": "7.17",
    },
}


def check_motif_family_totals(
    index: ReferenceIndex,
) -> Tuple[CheckerDiagnostic, ...]:
    """Requirements 7.12 and 7.17: the fixed whole-book family event counts.

    Counted from ledger records only. An Incidental_Mention is by definition not
    a ledgered event, so nothing here reads prose looking for the noun "record" or
    a kettle: an unledgered mention adds no dramatic function and is excluded from
    Motif_Event counts by Requirement 7.5.
    """

    by_family: Dict[str, List[Tuple[int, str, str]]] = {}
    for record in index.of_type("MotifEvent"):
        family = record.payload.get("family")
        if not isinstance(family, str):
            continue
        name = _normalized_text(family).strip()
        if name not in CLOSED_MOTIF_FAMILY_TOTALS:
            continue
        chapter = record.payload.get("planned_chapter")
        movement = record.payload.get("movement")
        motif_id = _stable_id(record.payload.get("motif_event_id")) or record.identity
        by_family.setdefault(name, []).append(
            (
                int(chapter) if _is_chapter_number(chapter) else 0,
                str(movement),
                motif_id,
            )
        )

    diagnostics: List[CheckerDiagnostic] = []
    # Every closed family is walked, not only the families the ledger happens to
    # mention. A family with no records at all is the strongest form of the same
    # violation, and iterating over what was found would let it pass silently.
    # This is a whole-book check, so a complete ledger is a precondition here and
    # an absent family cannot be an as-yet-unwritten one.
    for family in sorted(CLOSED_MOTIF_FAMILY_TOTALS):
        rule = CLOSED_MOTIF_FAMILY_TOTALS[family]
        events = sorted(by_family.get(family, ()))
        expected_count = int(rule["count"])
        expected_movements = tuple(rule["movements"])
        if len(events) != expected_count:
            diagnostics.append(
                _diagnostic(
                    "MOTIF_FAMILY_EVENT_COUNT",
                    scope=SCOPE_PLANNING,
                    item=family,
                    observed="{0} ledgered events: {1}".format(
                        len(events),
                        ",".join(motif_id for _, _, motif_id in events),
                    ),
                    expected="exactly {0} Motif_Events in the {1} family "
                    "(Requirement {2})".format(
                        expected_count, family, rule["requirement"]
                    ),
                )
            )
            continue
        observed_movements = tuple(movement for _, movement, _ in events)
        if observed_movements != expected_movements:
            diagnostics.append(
                _diagnostic(
                    "MOTIF_FAMILY_MOVEMENT_PLACEMENT",
                    scope=SCOPE_PLANNING,
                    item=family,
                    observed=", ".join(
                        "{0}={1}".format(motif_id, movement)
                        for _, movement, motif_id in events
                    ),
                    expected="the {0} family in {1} by ascending chapter "
                    "(Requirement {2})".format(
                        family,
                        " then ".join(expected_movements),
                        rule["requirement"],
                    ),
                )
            )
    return tuple(diagnostics)


# ---------------------------------------------------------------------------
# CanonFact authority under `DEC-011` and `DEC-014`
#
# Authority is decided from the record's own declared basis, source class, and
# adoption reference. Nothing here reads a song file, and nothing infers that a
# statement "sounds like" lyric canon: the point of the authority basis is that
# the author names it and the checker holds them to what they named.
# ---------------------------------------------------------------------------


def check_canon_facts(index: ReferenceIndex) -> Tuple[CheckerDiagnostic, ...]:
    """Every `CanonFact` authority, testimony, and advisory-citation rule."""

    diagnostics: List[CheckerDiagnostic] = []
    for record in index.of_type("CanonFact"):
        label = _stable_id(record.payload.get("canon_id")) or record.identity
        basis = record.payload.get("authority_basis")
        if basis not in CANON_AUTHORITY_BASES:
            diagnostics.append(
                record.violation(
                    "CANON_AUTHORITY_BASIS_UNKNOWN",
                    item=label,
                    observed="authority_basis={0!r}".format(basis),
                    expected="one of {0}".format(", ".join(CANON_AUTHORITY_BASES)),
                )
            )
            continue

        material_class = record.payload.get("source_material_class")
        if material_class not in CANON_SOURCE_MATERIAL_CLASSES:
            diagnostics.append(
                record.violation(
                    "CANON_SOURCE_MATERIAL_CLASS_UNKNOWN",
                    item=label,
                    observed="source_material_class={0!r}".format(material_class),
                    expected="one of {0}".format(
                        ", ".join(CANON_SOURCE_MATERIAL_CLASSES)
                    ),
                )
            )
            continue

        diagnostics.extend(
            _check_canon_basis_agreement(
                record, label=label, basis=str(basis), material_class=str(material_class)
            )
        )
        diagnostics.extend(_check_canon_testimony(record, label=label))
        diagnostics.extend(_check_canon_advisory_citations(record, label=label))

    return tuple(diagnostics)


def _check_canon_basis_agreement(
    record: PlanningRecord, *, label: str, basis: str, material_class: str
) -> Tuple[CheckerDiagnostic, ...]:
    """The authority matrix: basis, required source class, path, and adoption."""

    diagnostics: List[CheckerDiagnostic] = []
    source_path = record.payload.get("source_path")

    required_class = CANON_BASIS_SOURCE_CLASS.get(basis)
    if required_class is not None and material_class != required_class:
        diagnostics.append(
            record.violation(
                "CANON_SOURCE_MATERIAL_CLASS_MISMATCH",
                item=label,
                observed="authority_basis={0} source_material_class={1}".format(
                    basis, material_class
                ),
                expected="source_material_class {0!r} for authority_basis "
                "{1!r}".format(required_class, basis),
            )
        )

    if basis == "lyric":
        normalized = (
            _normalized_text(source_path).strip()
            if isinstance(source_path, str)
            else None
        )
        if normalized == EXCLUDED_CANON_SOURCE_PATH:
            diagnostics.append(
                record.violation(
                    "CANON_SOURCE_EXCLUDED",
                    item=label,
                    observed="source_path={0!r}".format(source_path),
                    expected="a Canon_Source; {0} is unpublished, noncanonical, "
                    "and supplies no novel continuity".format(
                        EXCLUDED_CANON_SOURCE_PATH
                    ),
                )
            )
        elif normalized not in CANON_SOURCE_PATHS:
            diagnostics.append(
                record.violation(
                    "CANON_SOURCE_PATH_UNKNOWN",
                    item=label,
                    observed="source_path={0!r}".format(source_path),
                    expected="exactly one of the five DEC-014 Canon_Sources: "
                    "{0}".format(", ".join(CANON_SOURCE_PATHS)),
                )
            )

    adoption = record.payload.get("adopted_by")
    if basis == "ratified-note":
        if material_class not in ADVISORY_SOURCE_MATERIAL_CLASSES:
            diagnostics.append(
                record.violation(
                    "CANON_SOURCE_MATERIAL_CLASS_MISMATCH",
                    item=label,
                    observed="ratified-note over source_material_class={0}".format(
                        material_class
                    ),
                    expected="one of the note or metadata classes: {0}".format(
                        ", ".join(ADVISORY_SOURCE_MATERIAL_CLASSES)
                    ),
                )
            )
        if record.payload.get("truth_scope") == "authoritative-proposition":
            # Requirement 6.17: a ratified note's authority is borrowed from its
            # identified adopter, which is why the vocabulary carries a separate
            # `ratified-proposition` scope. Letting a note claim the
            # `authoritative-proposition` tier would promote advisory metadata into
            # binding continuity by relabelling rather than by ratification, which
            # is the promotion the requirement forbids.
            diagnostics.append(
                record.violation(
                    "CANON_RATIFIED_NOTE_TRUTH_SCOPE",
                    item=label,
                    observed="ratified-note recorded as authoritative-proposition",
                    expected="truth_scope 'ratified-proposition'; a ratified note "
                    "binds on its adopter's authority, not on its own",
                )
            )
        diagnostics.extend(_check_canon_adoption(record, label=label, adoption=adoption))
    elif adoption is not None:
        diagnostics.append(
            record.violation(
                "CANON_ADOPTION_UNEXPECTED",
                item=label,
                observed="authority_basis={0} with adopted_by present".format(basis),
                expected="adopted_by of null unless the basis is ratified-note",
            )
        )

    if (
        basis != "ratified-note"
        and material_class in ADVISORY_SOURCE_MATERIAL_CLASSES
    ):
        # Requirement 6.17: unratified Production_Notes, style prompts, exclude
        # lists, generation workflow, credits, and rights metadata cannot be
        # promoted into binding continuity.
        diagnostics.append(
            record.violation(
                "CANON_ADVISORY_MATERIAL_BINDING",
                item=label,
                observed="{0} material bound as {1}".format(material_class, basis),
                expected="advisory non-story material recorded as a supporting "
                "citation, or ratified by a resolvable author decision or "
                "approved requirement",
            )
        )
    return tuple(diagnostics)


def _check_canon_adoption(
    record: PlanningRecord, *, label: str, adoption: Any
) -> Tuple[CheckerDiagnostic, ...]:
    """A `ratified-note` fact needs an adoption naming who adopted it."""

    if not isinstance(adoption, dict) or set(adoption) != set(CANON_ADOPTION_KEYS):
        return (
            record.malformed(
                "CANON_ADOPTION_MALFORMED",
                observed="adopted_by {0}".format(
                    _key_set_report(adoption, CANON_ADOPTION_KEYS)
                    if isinstance(adoption, dict)
                    else "is {0!r}".format(adoption)
                ),
                expected="exactly {0}".format(", ".join(CANON_ADOPTION_KEYS)),
            ),
        )

    diagnostics: List[CheckerDiagnostic] = []
    authority_type = adoption.get("authority_type")
    if authority_type not in CANON_ADOPTION_AUTHORITY_TYPES:
        diagnostics.append(
            record.violation(
                "CANON_ADOPTION_AUTHORITY_TYPE",
                item=label,
                observed="authority_type={0!r}".format(authority_type),
                expected="one of {0}".format(
                    ", ".join(CANON_ADOPTION_AUTHORITY_TYPES)
                ),
            )
        )
    for key in ("authority_id", "source_path", "source_location"):
        if not _is_nonblank_string(adoption.get(key)):
            diagnostics.append(
                record.violation(
                    "CANON_ADOPTION_REFERENCE_MISSING",
                    item=label,
                    observed="adopted_by.{0}={1!r}".format(key, adoption.get(key)),
                    expected="a nonblank reference identifying the adopting "
                    "author decision or approved requirement",
                )
            )
    return tuple(diagnostics)


def _check_canon_testimony(
    record: PlanningRecord, *, label: str
) -> Tuple[CheckerDiagnostic, ...]:
    """First-person testimony keeps its speaker, attribution, and limitation.

    The schema has no `omniscient` truth scope, so the only way to overclaim is
    to record first-person testimony under a proposition scope. That is exactly
    the *Case Zero* failure mode `DEC-014` and the error-handling table name:
    binding what Nia reports is legitimate; converting it into causal proof is
    not.
    """

    testimony = record.payload.get("first_person_testimony")
    truth_scope = record.payload.get("truth_scope")

    diagnostics: List[CheckerDiagnostic] = []
    if truth_scope not in CANON_TRUTH_SCOPES:
        diagnostics.append(
            record.violation(
                "CANON_TRUTH_SCOPE_UNKNOWN",
                item=label,
                observed="truth_scope={0!r}".format(truth_scope),
                expected="one of {0}".format(", ".join(CANON_TRUTH_SCOPES)),
            )
        )
    if not _is_bool(testimony):
        diagnostics.append(
            record.malformed(
                "CANON_TESTIMONY_MALFORMED",
                observed="first_person_testimony={0!r}".format(testimony),
                expected="a boolean",
            )
        )
        return tuple(diagnostics)

    if not testimony:
        return tuple(diagnostics)

    for key in TESTIMONY_ATTRIBUTION_KEYS:
        if not _is_nonblank_string(record.payload.get(key)):
            diagnostics.append(
                record.violation(
                    "CANON_TESTIMONY_ATTRIBUTION_MISSING",
                    item=label,
                    observed="{0}={1!r}".format(key, record.payload.get(key)),
                    expected="a nonblank {0} for first-person testimony".format(key),
                )
            )
    if truth_scope in CANON_TRUTH_SCOPES and truth_scope != TESTIMONY_TRUTH_SCOPE:
        diagnostics.append(
            record.violation(
                "CANON_TESTIMONY_TRUTH_SCOPE",
                item=label,
                observed="first-person testimony recorded as {0}".format(truth_scope),
                expected="truth_scope {0!r}; a first-person account binds what "
                "the speaker reports and is not omniscient causal "
                "proof".format(TESTIMONY_TRUTH_SCOPE),
            )
        )
    return tuple(diagnostics)


def _check_canon_advisory_citations(
    record: PlanningRecord, *, label: str
) -> Tuple[CheckerDiagnostic, ...]:
    """Supporting advisory citations stay classified `advisory-non-story`."""

    citations = record.payload.get("supporting_advisory_citations")
    if not isinstance(citations, list):
        return (
            record.malformed(
                "CANON_ADVISORY_CITATIONS_MALFORMED",
                observed="supporting_advisory_citations={0!r}".format(citations),
                expected="an array of advisory citation objects, possibly empty",
            ),
        )

    diagnostics: List[CheckerDiagnostic] = []
    for position, citation in enumerate(citations):
        if not isinstance(citation, dict) or set(citation) != set(
            ADVISORY_CITATION_KEYS
        ):
            diagnostics.append(
                record.malformed(
                    "CANON_ADVISORY_CITATIONS_MALFORMED",
                    observed="supporting_advisory_citations[{0}] {1}".format(
                        position,
                        _key_set_report(citation, ADVISORY_CITATION_KEYS)
                        if isinstance(citation, dict)
                        else "is not an object",
                    ),
                    expected="exactly {0}".format(", ".join(ADVISORY_CITATION_KEYS)),
                )
            )
            continue
        if citation.get("classification") != ADVISORY_CITATION_CLASSIFICATION:
            diagnostics.append(
                record.violation(
                    "CANON_ADVISORY_CITATION_CLASSIFICATION",
                    item=label,
                    observed="supporting_advisory_citations[{0}]."
                    "classification={1!r}".format(
                        position, citation.get("classification")
                    ),
                    expected="exactly {0!r}".format(ADVISORY_CITATION_CLASSIFICATION),
                )
            )
    return tuple(diagnostics)


def check_canon_source_inventory(
    index: ReferenceIndex,
) -> Tuple[CheckerDiagnostic, ...]:
    """`DEC-014`: the lyric-cited Canon_Sources are a subset of the exact five.

    This reports which of the five the Canon_Bible actually cites, as an
    informational warning, and never demands that all five be cited: an early
    Canon_Bible legitimately has facts from three songs. What it does enforce is
    that no path outside the five appears, which the per-record check already
    covers, so the only additional objective failure here is the *One-Time Pad*
    inventory error surfaced once for the whole document.
    """

    cited: Dict[str, int] = {}
    for record in index.of_type("CanonFact"):
        if record.payload.get("authority_basis") != "lyric":
            continue
        source_path = record.payload.get("source_path")
        if not isinstance(source_path, str):
            continue
        normalized = _normalized_text(source_path).strip()
        cited[normalized] = cited.get(normalized, 0) + 1

    if not cited:
        return ()
    unknown = sorted(set(cited) - set(CANON_SOURCE_PATHS))
    if not unknown:
        return ()
    return (
        _diagnostic(
            "CANON_SOURCE_INVENTORY",
            scope=SCOPE_PLANNING,
            item="planning/canon-bible.md",
            observed="lyric authority cited from {0}".format(", ".join(unknown)),
            expected="lyric authority only from the exact five DEC-014 "
            "Canon_Sources",
        ),
    )


# ---------------------------------------------------------------------------
# `NovelExtension` and `Reveal` reference integrity
#
# These carry the structured `DEC-005` and provenance obligations. A missing or
# dangling decision or entity reference is a metadata error; the *wording* of a
# selected institution, country, or county name is not, because Requirement 12.11
# keeps name choice and capitalization out of automated pass/fail.
# ---------------------------------------------------------------------------

NOVEL_EXTENSION_STATES: Tuple[str, ...] = ("provisional", "approved", "retired")
NOVEL_EXTENSION_KINDS: Tuple[str, ...] = (
    "character-name",
    "alias",
    "relationship",
    "place",
    "institution",
    "product",
    "mechanism",
    "chronology",
    "profession",
    "document",
    "other-continuity",
)
RECORD_REF_KEYS: Tuple[str, ...] = ("record_type", "record_id")
# `Reveal.truth_status`; every Foreign_Signal provenance record is fixed here.
REVEAL_TRUTH_STATUSES: Tuple[str, ...] = (
    "confirmed",
    "character-belief",
    "unresolved",
)
REVEAL_UNRESOLVED = "unresolved"


def _resolve_record_ref(
    index: ReferenceIndex, value: Any
) -> Tuple[bool, Optional[str]]:
    """Whether a `RecordRef` is well-formed and resolves, plus why it did not.

    A reference into a record type this checker does not index resolves
    vacuously: the reference is structurally valid and there is no index to
    contradict it. Reporting it as dangling would invent a failure from the
    checker's own coverage rather than from the data.
    """

    if not isinstance(value, dict) or set(value) != set(RECORD_REF_KEYS):
        return False, "not exactly {0}".format(", ".join(RECORD_REF_KEYS))
    record_type = value.get("record_type")
    record_id = value.get("record_id")
    if record_type not in RECORD_TYPES:
        return False, "record_type={0!r} is not a defined record type".format(
            record_type
        )
    if not _is_nonblank_string(record_id):
        return False, "record_id={0!r} is blank".format(record_id)
    if record_type not in RECORD_ID_FIELDS:
        return True, None
    normalized = _stable_id(record_id)
    if normalized is None:
        # `ArcEntry` targets are chapter numbers as strings, which are legitimate
        # nonblank references that are not StableIDs.
        return True, None
    matches = index.lookup(str(record_type), normalized)
    if len(matches) == 1:
        return True, None
    if not matches:
        return False, "{0} {1} does not resolve".format(record_type, normalized)
    return False, "{0} {1} resolves to {2} records".format(
        record_type, normalized, len(matches)
    )


def check_novel_extensions(index: ReferenceIndex) -> Tuple[CheckerDiagnostic, ...]:
    """Extension state, authority reference, and dependency resolution."""

    diagnostics: List[CheckerDiagnostic] = []
    for record in index.of_type("NovelExtension"):
        label = _stable_id(record.payload.get("extension_id")) or record.identity

        kind = record.payload.get("extension_kind")
        if kind not in NOVEL_EXTENSION_KINDS:
            diagnostics.append(
                record.violation(
                    "EXTENSION_KIND_UNKNOWN",
                    item=label,
                    observed="extension_kind={0!r}".format(kind),
                    expected="one of {0}".format(", ".join(NOVEL_EXTENSION_KINDS)),
                )
            )
        state = record.payload.get("state")
        if state not in NOVEL_EXTENSION_STATES:
            diagnostics.append(
                record.violation(
                    "EXTENSION_STATE_UNKNOWN",
                    item=label,
                    observed="state={0!r}".format(state),
                    expected="one of {0}".format(", ".join(NOVEL_EXTENSION_STATES)),
                )
            )
        elif state == "approved" and not _is_nonblank_string(
            record.payload.get("authority_ref")
        ):
            diagnostics.append(
                record.violation(
                    "EXTENSION_AUTHORITY_REFERENCE_MISSING",
                    item=label,
                    observed="authority_ref={0!r}".format(
                        record.payload.get("authority_ref")
                    ),
                    expected="an author decision, approved design decision, or "
                    "completed ArcChange reference for an approved extension",
                )
            )

        superseding = record.payload.get("superseding_arc_change_id")
        if state == "retired" and _stable_id(superseding) is None:
            diagnostics.append(
                record.violation(
                    "EXTENSION_SUPERSEDING_CHANGE_MISSING",
                    item=label,
                    observed="superseding_arc_change_id={0!r}".format(superseding),
                    expected="the ArcChange that retired the extension",
                )
            )
        elif state != "retired" and superseding is not None:
            diagnostics.append(
                record.violation(
                    "EXTENSION_SUPERSEDING_CHANGE_UNEXPECTED",
                    item=label,
                    observed="state={0} with superseding_arc_change_id={1!r}".format(
                        state, superseding
                    ),
                    expected="null unless the extension is retired",
                )
            )

        resolved, reason = _resolve_record_ref(
            index, record.payload.get("first_dependency")
        )
        if not resolved:
            diagnostics.append(
                record.violation(
                    "EXTENSION_DEPENDENCY_UNRESOLVED",
                    item=label,
                    observed="first_dependency {0}".format(reason),
                    expected="one resolvable RecordRef naming the first record or "
                    "chapter that depends on the fact",
                )
            )

        affected = record.payload.get("affected_records")
        if not isinstance(affected, list) or not affected:
            diagnostics.append(
                record.malformed(
                    "EXTENSION_AFFECTED_RECORDS_MALFORMED",
                    observed="affected_records={0!r}".format(affected),
                    expected="a nonempty array of RecordRef objects",
                )
            )
        else:
            for position, reference in enumerate(affected):
                resolved, reason = _resolve_record_ref(index, reference)
                if resolved:
                    continue
                diagnostics.append(
                    record.violation(
                        "EXTENSION_AFFECTED_RECORD_UNRESOLVED",
                        item=label,
                        observed="affected_records[{0}] {1}".format(position, reason),
                        expected="every affected record reference to resolve "
                        "uniquely",
                    )
                )

        implications = record.payload.get("consistency_implications")
        if (
            not isinstance(implications, list)
            or not implications
            or any(not _is_nonblank_string(value) for value in implications)
        ):
            diagnostics.append(
                record.malformed(
                    "EXTENSION_IMPLICATIONS_MALFORMED",
                    observed="consistency_implications={0!r}".format(implications),
                    expected="a nonempty array of nonblank consistency "
                    "implications",
                )
            )
    return tuple(diagnostics)


def check_reveals(index: ReferenceIndex) -> Tuple[CheckerDiagnostic, ...]:
    """`Reveal` truth status, and the unresolved-provenance invariant.

    Requirements 3.13 and 4.11 keep every Foreign_Signal origin or sender account
    unconfirmed. A record can only break that by declaring itself `confirmed`, so
    that is what is checked: a `confirmed` provenance reveal, or one that hands an
    unresolved question a reveal owner and reader release chapter, which would
    schedule an answer the novel never gives.
    """

    diagnostics: List[CheckerDiagnostic] = []
    for record in index.of_type("Reveal"):
        label = _stable_id(record.payload.get("reveal_id")) or record.identity
        truth_status = record.payload.get("truth_status")
        if truth_status not in REVEAL_TRUTH_STATUSES:
            diagnostics.append(
                record.violation(
                    "REVEAL_TRUTH_STATUS_UNKNOWN",
                    item=label,
                    observed="truth_status={0!r}".format(truth_status),
                    expected="one of {0}".format(", ".join(REVEAL_TRUTH_STATUSES)),
                )
            )
            continue
        if truth_status != REVEAL_UNRESOLVED:
            continue
        if record.payload.get("reveal_owner") is not None or record.payload.get(
            "reader_release_chapter"
        ) is not None:
            diagnostics.append(
                record.violation(
                    "REVEAL_UNRESOLVED_RELEASE_SCHEDULED",
                    item=label,
                    observed="unresolved with reveal_owner={0!r} "
                    "reader_release_chapter={1!r}".format(
                        record.payload.get("reveal_owner"),
                        record.payload.get("reader_release_chapter"),
                    ),
                    expected="no reveal owner and no reader release chapter for a "
                    "permanently unresolved question",
                )
            )
    return tuple(diagnostics)


# ---------------------------------------------------------------------------
# ArcChange atomicity and Chapter_Status synchronization
# ---------------------------------------------------------------------------


def check_arc_changes(index: ReferenceIndex) -> Tuple[CheckerDiagnostic, ...]:
    """Requirements 1.16 and 1.17: an ArcChange is atomic or it is not complete.

    Partial synchronization is never treated as approval, which is the rule the
    error-handling table states directly. A `complete` record must therefore carry
    every obligation complete with evidence, an approval, and a completion time;
    anything less is reported with the unsynchronized documents named.
    """

    diagnostics: List[CheckerDiagnostic] = []
    for record in index.of_type("ArcChange"):
        label = _stable_id(record.payload.get("arc_change_id")) or record.identity

        for key in ("prior_state", "revised_state"):
            value = record.payload.get(key)
            if not isinstance(value, dict) or not value:
                diagnostics.append(
                    record.violation(
                        "ARC_CHANGE_STATE_MISSING",
                        item=label,
                        observed="{0}={1!r}".format(key, value),
                        expected="a nonempty snapshot object naming the changed "
                        "logical values",
                    )
                )
        if not _is_nonblank_string(record.payload.get("rationale")):
            diagnostics.append(
                record.violation(
                    "ARC_CHANGE_RATIONALE_MISSING",
                    item=label,
                    observed="rationale={0!r}".format(record.payload.get("rationale")),
                    expected="a nonblank narrative or calibration reason",
                )
            )
        if _chapter_number_sequence(record.payload.get("affected_chapters")) is None:
            diagnostics.append(
                record.malformed(
                    "ARC_CHANGE_AFFECTED_CHAPTERS_MALFORMED",
                    observed="affected_chapters={0!r}".format(
                        record.payload.get("affected_chapters")
                    ),
                    expected="a unique list of chapter numbers, possibly empty for "
                    "a reference-only change",
                )
            )

        documents = record.payload.get("affected_documents")
        if (
            not isinstance(documents, list)
            or not documents
            or any(not _is_workspace_relative_path(value) for value in documents)
            or len(set(documents)) != len(documents)
        ):
            diagnostics.append(
                record.malformed(
                    "ARC_CHANGE_AFFECTED_DOCUMENTS_MALFORMED",
                    observed="affected_documents={0!r}".format(documents),
                    expected="a unique nonempty list of workspace-relative paths",
                )
            )
            documents = []

        status = record.payload.get("status")
        if status not in ARC_CHANGE_STATUSES:
            diagnostics.append(
                record.violation(
                    "ARC_CHANGE_STATUS_UNKNOWN",
                    item=label,
                    observed="status={0!r}".format(status),
                    expected="one of {0}".format(", ".join(ARC_CHANGE_STATUSES)),
                )
            )

        obligations, obligation_diagnostics = _arc_change_obligations(record)
        diagnostics.extend(obligation_diagnostics)

        covered = {document for document, _ in obligations}
        uncovered = sorted(set(documents) - covered)
        if uncovered:
            diagnostics.append(
                record.violation(
                    "ARC_CHANGE_SYNCHRONIZATION_MISSING",
                    item=label,
                    observed="no synchronization obligation for {0}".format(
                        ", ".join(uncovered)
                    ),
                    expected="one synchronization obligation per affected "
                    "reference document",
                )
            )

        if status != ARC_CHANGE_STATUS_COMPLETE:
            continue

        pending = sorted(
            document
            for document, obligation_status in obligations
            if obligation_status != SYNCHRONIZATION_STATUS_COMPLETE
        )
        if pending:
            diagnostics.append(
                record.violation(
                    "ARC_CHANGE_INCOMPLETE_SYNCHRONIZATION",
                    item=label,
                    observed="complete with {0} still pending".format(
                        ", ".join(pending)
                    ),
                    expected="every synchronization obligation complete before "
                    "the ArcChange is complete; partial synchronization is not "
                    "approval",
                )
            )
        if not _is_complete_approval(record.payload.get("approval")):
            diagnostics.append(
                record.violation(
                    "ARC_CHANGE_APPROVAL_MISSING",
                    item=label,
                    observed="approval={0!r}".format(record.payload.get("approval")),
                    expected="exactly {0} for a complete ArcChange".format(
                        ", ".join(BASELINE_APPROVAL_KEYS)
                    ),
                )
            )
        if not _is_nonblank_string(record.payload.get("completed_at")):
            diagnostics.append(
                record.violation(
                    "ARC_CHANGE_COMPLETION_TIME_MISSING",
                    item=label,
                    observed="completed_at={0!r}".format(
                        record.payload.get("completed_at")
                    ),
                    expected="a completion timestamp for a complete ArcChange",
                )
            )
    return tuple(diagnostics)


def _arc_change_obligations(
    record: PlanningRecord,
) -> Tuple[Tuple[Tuple[str, str], ...], Tuple[CheckerDiagnostic, ...]]:
    """Parse `synchronization_obligations` into `(document, status)` pairs."""

    value = record.payload.get("synchronization_obligations")
    if not isinstance(value, list) or not value:
        return (
            (),
            (
                record.malformed(
                    "ARC_CHANGE_OBLIGATIONS_MALFORMED",
                    observed="synchronization_obligations={0!r}".format(value),
                    expected="a nonempty array of synchronization obligations",
                ),
            ),
        )

    obligations: List[Tuple[str, str]] = []
    diagnostics: List[CheckerDiagnostic] = []
    label = _stable_id(record.payload.get("arc_change_id")) or record.identity
    for position, obligation in enumerate(value):
        if not isinstance(obligation, dict) or set(obligation) != set(
            ARC_CHANGE_OBLIGATION_KEYS
        ):
            diagnostics.append(
                record.malformed(
                    "ARC_CHANGE_OBLIGATIONS_MALFORMED",
                    observed="synchronization_obligations[{0}] {1}".format(
                        position,
                        _key_set_report(obligation, ARC_CHANGE_OBLIGATION_KEYS)
                        if isinstance(obligation, dict)
                        else "is not an object",
                    ),
                    expected="exactly {0}".format(
                        ", ".join(ARC_CHANGE_OBLIGATION_KEYS)
                    ),
                )
            )
            continue
        document = obligation.get("document")
        status = obligation.get("status")
        if not _is_workspace_relative_path(document) or status not in (
            SYNCHRONIZATION_STATUSES
        ):
            diagnostics.append(
                record.malformed(
                    "ARC_CHANGE_OBLIGATIONS_MALFORMED",
                    observed="synchronization_obligations[{0}] document={1!r} "
                    "status={2!r}".format(position, document, status),
                    expected="a workspace-relative document and a status of {0}".format(
                        " or ".join(SYNCHRONIZATION_STATUSES)
                    ),
                )
            )
            continue
        evidence = obligation.get("evidence_ref")
        if status == SYNCHRONIZATION_STATUS_COMPLETE and not _is_nonblank_string(
            evidence
        ):
            diagnostics.append(
                record.violation(
                    "ARC_CHANGE_OBLIGATION_EVIDENCE_MISSING",
                    item=label,
                    observed="{0} complete with evidence_ref={1!r}".format(
                        document, evidence
                    ),
                    expected="a nonblank record or path reference once the "
                    "obligation is complete",
                )
            )
        elif status != SYNCHRONIZATION_STATUS_COMPLETE and evidence is not None:
            diagnostics.append(
                record.violation(
                    "ARC_CHANGE_OBLIGATION_EVIDENCE_PREMATURE",
                    item=label,
                    observed="{0} {1} with evidence_ref={2!r}".format(
                        document, status, evidence
                    ),
                    expected="evidence_ref of null until the obligation is "
                    "complete",
                )
            )
        obligations.append((str(_normalized_text(document).strip()), str(status)))
    return tuple(obligations), tuple(diagnostics)


def _is_complete_approval(value: Any) -> bool:
    return (
        isinstance(value, dict)
        and set(value) == set(BASELINE_APPROVAL_KEYS)
        and all(_is_nonblank_string(value.get(key)) for key in BASELINE_APPROVAL_KEYS)
    )


def check_status_synchronization(
    results: Sequence["ChapterCheckResult"],
) -> Tuple[CheckerDiagnostic, ...]:
    """Requirement 10.7: an `approved` or `final` chapter agrees with its entry.

    The header-versus-ArcEntry status agreement itself is a Requirement 12.5
    chapter-local check that already runs for every file. What is added here is
    the whole-book obligation that a Final_Prerequisite cannot be satisfied by
    exploratory work: a manuscript presented as complete cannot hold chapters
    still labeled `exploratory` or otherwise short of an approved status.
    """

    diagnostics: List[CheckerDiagnostic] = []
    for result in results:
        status = result.document.header.get("status")
        if not isinstance(status, str) or status in APPROVED_CHAPTER_STATUSES:
            continue
        diagnostics.append(
            _diagnostic(
                "CHAPTER_STATUS_NOT_FINAL",
                scope=SCOPE_GLOBAL,
                item=result.relative_path,
                observed="status={0}".format(status),
                expected="one of {0}; exploratory or in-progress work cannot "
                "satisfy a Final_Prerequisite".format(
                    ", ".join(APPROVED_CHAPTER_STATUSES)
                ),
                disposition=DISPOSITION_INCOMPLETE,
            )
        )
    return tuple(diagnostics)


# ---------------------------------------------------------------------------
# Baseline, Final_Prerequisites, and the two independent final gates
# ---------------------------------------------------------------------------


def parse_final_targets(payload: Any) -> Tuple[Optional[FinalTargets], Optional[str]]:
    """Read a `final_targets` object, returning it or why it was rejected."""

    if payload is None:
        return None, None
    if not isinstance(payload, dict) or set(payload) != set(FINAL_TARGET_KEYS):
        return None, "final_targets {0}".format(
            _key_set_report(payload, FINAL_TARGET_KEYS)
            if isinstance(payload, dict)
            else "is not an object"
        )
    values: Dict[str, int] = {}
    for key in FINAL_TARGET_KEYS:
        value = payload.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 1:
            return None, "final_targets.{0}={1!r}".format(key, value)
        values[key] = value
    if values["minimum_words"] > values["maximum_words"]:
        return None, "final_targets minimum_words {0} exceeds maximum_words {1}".format(
            values["minimum_words"], values["maximum_words"]
        )
    return (
        FinalTargets(
            chapter_count=values["chapter_count"],
            minimum_words=values["minimum_words"],
            maximum_words=values["maximum_words"],
        ),
        None,
    )


@dataclass(frozen=True)
class BaselineState:
    """The approved-baseline facts the global gate needs, plus its record."""

    record: Optional[PlanningRecord]
    state: Optional[str]
    final_targets: Optional[FinalTargets]

    @property
    def approved(self) -> bool:
        return self.state == BASELINE_STATE_APPROVED


def check_baseline(index: ReferenceIndex) -> Tuple[BaselineState, Tuple[CheckerDiagnostic, ...]]:
    """Read the current `Baseline` and check its internal completeness rules.

    Approval is all-or-nothing: `approved` requires a complete provisional arc,
    both Gate Results, one disposition per calibration finding, an author
    approval, and Final_Targets. A `provisional` baseline is not a violation —
    that is the pre-approval state this project is legitimately in — so nothing
    here demands approval. It only refuses to let a record *claim* approval
    without the evidence.
    """

    records = index.of_type("Baseline")
    diagnostics: List[CheckerDiagnostic] = []

    current = [
        record
        for record in records
        if record.payload.get("state") != "superseded"
    ]
    if len(current) > 1:
        diagnostics.append(
            _diagnostic(
                "BASELINE_NOT_UNIQUE",
                scope=SCOPE_PLANNING,
                item="planning/arc-outline.md",
                observed=", ".join(sorted(record.identity for record in current)),
                expected="exactly one current Baseline record",
                disposition=DISPOSITION_INCOMPLETE,
            )
        )
    record = current[0] if len(current) == 1 else None
    if record is None:
        return BaselineState(record=None, state=None, final_targets=None), tuple(
            diagnostics
        )

    label = _stable_id(record.payload.get("baseline_id")) or record.identity
    state = record.payload.get("state")
    if state not in BASELINE_STATES:
        diagnostics.append(
            record.violation(
                "BASELINE_STATE_UNKNOWN",
                item=label,
                observed="state={0!r}".format(state),
                expected="one of {0}".format(", ".join(BASELINE_STATES)),
            )
        )
        state = None

    calibration = _chapter_number_sequence(record.payload.get("calibration_chapters"))
    if calibration is None:
        diagnostics.append(
            record.malformed(
                "BASELINE_CALIBRATION_CHAPTERS_MALFORMED",
                observed="calibration_chapters={0!r}".format(
                    record.payload.get("calibration_chapters")
                ),
                expected="a unique list of chapter numbers",
            )
        )
    else:
        minimum, maximum = CALIBRATION_BATCH_SIZE_RANGE
        if not minimum <= len(calibration) <= maximum:
            diagnostics.append(
                record.violation(
                    "BASELINE_CALIBRATION_SIZE",
                    item=label,
                    observed="{0} calibration chapters".format(len(calibration)),
                    expected="{0}\u2013{1} chapters identified as the "
                    "Calibration_Batch".format(minimum, maximum),
                )
            )

    targets, target_error = parse_final_targets(record.payload.get("final_targets"))
    if target_error is not None:
        diagnostics.append(
            record.malformed(
                "BASELINE_FINAL_TARGETS_MALFORMED",
                observed=target_error,
                expected="exactly {0} with minimum_words at most "
                "maximum_words".format(", ".join(FINAL_TARGET_KEYS)),
            )
        )

    # A declared gate reference must resolve to a *passing* gate of the right
    # type. This is where a stale or mismatched claim of readiness is caught:
    # `calibration-objective` covers the staged minimal checker and
    # `baseline-objective` covers global mode plus the mandatory suite, and
    # neither can stand in for the other.
    for key, gate_type in (
        ("minimal_checker_gate_result_id", "calibration-objective"),
        ("full_suite_gate_result_id", "baseline-objective"),
    ):
        gate_id = record.payload.get(key)
        if gate_id is None:
            continue
        diagnostics.extend(
            _check_baseline_gate_reference(
                record, index, label=label, key=key, gate_type=gate_type
            )
        )

    if state == BASELINE_STATE_APPROVED:
        diagnostics.extend(
            _check_approved_baseline(record, label=label, targets=targets)
        )

    return (
        BaselineState(record=record, state=state, final_targets=targets),
        tuple(diagnostics),
    )


def _check_baseline_gate_reference(
    record: PlanningRecord,
    index: ReferenceIndex,
    *,
    label: str,
    key: str,
    gate_type: str,
) -> Tuple[CheckerDiagnostic, ...]:
    """One declared Baseline gate reference: resolvable, right type, passing."""

    gate_id = _stable_id(record.payload.get(key))
    if gate_id is None:
        return (
            record.malformed(
                "BASELINE_GATE_REFERENCE_MALFORMED",
                observed="{0}={1!r}".format(key, record.payload.get(key)),
                expected="null or a GateResult StableID",
            ),
        )
    gate = index.unique("GateResult", gate_id)
    if gate is None:
        return (
            record.violation(
                "BASELINE_GATE_REFERENCE_DANGLING",
                item=label,
                observed="{0}={1} resolves to {2} GateResult records".format(
                    key, gate_id, len(index.lookup("GateResult", gate_id))
                ),
                expected="exactly one GateResult",
            ),
        )

    diagnostics: List[CheckerDiagnostic] = []
    if gate.payload.get("gate_type") != gate_type:
        diagnostics.append(
            record.violation(
                "BASELINE_GATE_TYPE_MISMATCH",
                item=label,
                observed="{0} names a {1!r} gate".format(
                    key, gate.payload.get("gate_type")
                ),
                expected="a {0!r} GateResult; a local or staged result cannot "
                "claim another gate's authority".format(gate_type),
                related=(gate.identity,),
            )
        )
    if gate.payload.get("result") != RESULT_PASS:
        diagnostics.append(
            record.violation(
                "BASELINE_GATE_NOT_PASSING",
                item=label,
                observed="{0} names a gate with result={1!r}".format(
                    key, gate.payload.get("result")
                ),
                expected="a passing GateResult",
                related=(gate.identity,),
            )
        )
    return tuple(diagnostics)


def _check_approved_baseline(
    record: PlanningRecord, *, label: str, targets: Optional[FinalTargets]
) -> Tuple[CheckerDiagnostic, ...]:
    """The evidence an `approved` Baseline must actually carry."""

    diagnostics: List[CheckerDiagnostic] = []
    if record.payload.get("provisional_arc_complete") is not True:
        diagnostics.append(
            record.violation(
                "BASELINE_PROVISIONAL_ARC_INCOMPLETE",
                item=label,
                observed="provisional_arc_complete={0!r}".format(
                    record.payload.get("provisional_arc_complete")
                ),
                expected="true before approval",
            )
        )
    for key, gate in (
        ("minimal_checker_gate_result_id", "calibration-objective"),
        ("full_suite_gate_result_id", "baseline-objective"),
    ):
        if _stable_id(record.payload.get(key)) is None:
            diagnostics.append(
                record.violation(
                    "BASELINE_GATE_EVIDENCE_MISSING",
                    item=label,
                    observed="{0}={1!r}".format(key, record.payload.get(key)),
                    expected="a passing {0} GateResult reference before "
                    "approval".format(gate),
                )
            )
    if not _is_complete_approval(record.payload.get("author_approval")):
        diagnostics.append(
            record.violation(
                "BASELINE_AUTHOR_APPROVAL_MISSING",
                item=label,
                observed="author_approval={0!r}".format(
                    record.payload.get("author_approval")
                ),
                expected="exactly {0}".format(", ".join(BASELINE_APPROVAL_KEYS)),
            )
        )
    if targets is None:
        diagnostics.append(
            record.violation(
                "BASELINE_FINAL_TARGETS_MISSING",
                item=label,
                observed="final_targets={0!r}".format(
                    record.payload.get("final_targets")
                ),
                expected="one exact planned chapter count and one inclusive "
                "total Prose_Word range",
            )
        )
    else:
        chapter_minimum, chapter_maximum = PROVISIONAL_CHAPTER_RANGE
        word_minimum, word_maximum = PROVISIONAL_WORD_RANGE
        outside = (
            not chapter_minimum <= targets.chapter_count <= chapter_maximum
            or not word_minimum <= targets.minimum_words <= word_maximum
            or not word_minimum <= targets.maximum_words <= word_maximum
        )
        if outside and not _is_nonblank_string(
            record.payload.get("out_of_range_rationale")
        ):
            diagnostics.append(
                record.violation(
                    "BASELINE_OUT_OF_RANGE_RATIONALE_MISSING",
                    item=label,
                    observed="chapter_count={0} words={1}\u2013{2}".format(
                        targets.chapter_count,
                        targets.minimum_words,
                        targets.maximum_words,
                    ),
                    expected="a recorded narrative or calibration rationale when "
                    "Final_Targets fall outside {0}\u2013{1} chapters or "
                    "{2}\u2013{3} Prose_Words".format(
                        chapter_minimum, chapter_maximum, word_minimum, word_maximum
                    ),
                )
            )

    diagnostics.extend(_check_baseline_revision_pass(record, label=label))
    return tuple(diagnostics)


def _check_baseline_revision_pass(
    record: PlanningRecord, *, label: str
) -> Tuple[CheckerDiagnostic, ...]:
    """Requirement 1.13: one disposition per calibration finding, exactly once."""

    findings = _stable_id_sequence(record.payload.get("calibration_finding_ids"))
    if findings is None:
        return (
            record.malformed(
                "BASELINE_CALIBRATION_FINDINGS_MALFORMED",
                observed="calibration_finding_ids={0!r}".format(
                    record.payload.get("calibration_finding_ids")
                ),
                expected="a unique list of EditorialFinding references",
            ),
        )

    revision_pass = record.payload.get("baseline_revision_pass")
    if not isinstance(revision_pass, dict) or set(revision_pass) != set(
        BASELINE_REVISION_PASS_KEYS
    ):
        return (
            record.violation(
                "BASELINE_REVISION_PASS_MISSING",
                item=label,
                observed="baseline_revision_pass {0}".format(
                    _key_set_report(revision_pass, BASELINE_REVISION_PASS_KEYS)
                    if isinstance(revision_pass, dict)
                    else "is {0!r}".format(revision_pass)
                ),
                expected="exactly {0} for the one dedicated "
                "Baseline_Revision_Pass".format(
                    ", ".join(BASELINE_REVISION_PASS_KEYS)
                ),
            ),
        )

    diagnostics: List[CheckerDiagnostic] = []
    dispositions = revision_pass.get("dispositions")
    if not isinstance(dispositions, list):
        return (
            record.malformed(
                "BASELINE_REVISION_PASS_MALFORMED",
                observed="dispositions={0!r}".format(dispositions),
                expected="an array of disposition objects",
            ),
        )

    dispositioned: List[str] = []
    for position, disposition in enumerate(dispositions):
        if not isinstance(disposition, dict) or set(disposition) != set(
            BASELINE_DISPOSITION_KEYS
        ):
            diagnostics.append(
                record.malformed(
                    "BASELINE_REVISION_PASS_MALFORMED",
                    observed="dispositions[{0}] {1}".format(
                        position,
                        _key_set_report(disposition, BASELINE_DISPOSITION_KEYS)
                        if isinstance(disposition, dict)
                        else "is not an object",
                    ),
                    expected="exactly {0}".format(
                        ", ".join(BASELINE_DISPOSITION_KEYS)
                    ),
                )
            )
            continue
        finding_id = _stable_id(disposition.get("editorial_finding_id"))
        outcome = disposition.get("outcome")
        if outcome not in BASELINE_DISPOSITION_OUTCOMES:
            diagnostics.append(
                record.violation(
                    "BASELINE_DISPOSITION_OUTCOME_UNKNOWN",
                    item=label,
                    observed="dispositions[{0}].outcome={1!r}".format(
                        position, outcome
                    ),
                    expected="one of {0}".format(
                        ", ".join(BASELINE_DISPOSITION_OUTCOMES)
                    ),
                )
            )
        elif outcome == "arc-change" and _stable_id(
            disposition.get("arc_change_id")
        ) is None:
            diagnostics.append(
                record.violation(
                    "BASELINE_DISPOSITION_ARC_CHANGE_MISSING",
                    item=label,
                    observed="dispositions[{0}].arc_change_id={1!r}".format(
                        position, disposition.get("arc_change_id")
                    ),
                    expected="an ArcChange reference when the disposition is an "
                    "arc change",
                )
            )
        if not _is_nonblank_string(disposition.get("rationale")):
            diagnostics.append(
                record.violation(
                    "BASELINE_DISPOSITION_RATIONALE_MISSING",
                    item=label,
                    observed="dispositions[{0}].rationale={1!r}".format(
                        position, disposition.get("rationale")
                    ),
                    expected="a nonblank arc change or no-change rationale for "
                    "every calibration finding",
                )
            )
        if finding_id is not None:
            dispositioned.append(finding_id)

    missing = sorted(set(findings) - set(dispositioned))
    if missing:
        diagnostics.append(
            record.violation(
                "BASELINE_FINDING_UNDISPOSITIONED",
                item=label,
                observed="no disposition for {0}".format(", ".join(missing)),
                expected="one Baseline_Revision_Pass disposition per recorded "
                "calibration finding",
            )
        )
    duplicated = sorted(
        {
            finding_id
            for finding_id in dispositioned
            if dispositioned.count(finding_id) > 1
        }
    )
    if duplicated:
        diagnostics.append(
            record.violation(
                "BASELINE_FINDING_DISPOSITIONED_TWICE",
                item=label,
                observed="{0} dispositioned more than once".format(
                    ", ".join(duplicated)
                ),
                expected="exactly one disposition per finding in one dedicated "
                "revision pass",
            )
        )
    unknown = sorted(set(dispositioned) - set(findings))
    if unknown:
        diagnostics.append(
            record.violation(
                "BASELINE_DISPOSITION_UNKNOWN_FINDING",
                item=label,
                observed="dispositions reference {0}".format(", ".join(unknown)),
                expected="only findings listed in calibration_finding_ids",
            )
        )
    return tuple(diagnostics)


def check_gate_results(index: ReferenceIndex) -> Tuple[CheckerDiagnostic, ...]:
    """Each `GateResult`'s own internal consistency, from its declared fields.

    An objective gate's exit status is a function of its prerequisite state and
    diagnostics, so a record claiming a pass with an incomplete prerequisite is a
    violation. Editorial results derive from human findings and carry a null exit
    status; the checker never computes one for them.
    """

    diagnostics: List[CheckerDiagnostic] = []
    for record in index.of_type("GateResult"):
        label = _stable_id(record.payload.get("gate_result_id")) or record.identity
        gate_type = record.payload.get("gate_type")
        if gate_type not in GATE_TYPES:
            diagnostics.append(
                record.violation(
                    "GATE_TYPE_UNKNOWN",
                    item=label,
                    observed="gate_type={0!r}".format(gate_type),
                    expected="one of {0}".format(", ".join(GATE_TYPES)),
                )
            )
            continue

        scope = record.payload.get("scope")
        if not isinstance(scope, dict) or set(scope) != set(GATE_SCOPE_KEYS):
            diagnostics.append(
                record.malformed(
                    "GATE_SCOPE_MALFORMED",
                    observed="scope {0}".format(
                        _key_set_report(scope, GATE_SCOPE_KEYS)
                        if isinstance(scope, dict)
                        else "is not an object"
                    ),
                    expected="exactly {0}".format(", ".join(GATE_SCOPE_KEYS)),
                )
            )

        prerequisite = record.payload.get("prerequisite_state")
        if prerequisite not in GATE_PREREQUISITE_STATES:
            diagnostics.append(
                record.violation(
                    "GATE_PREREQUISITE_STATE_UNKNOWN",
                    item=label,
                    observed="prerequisite_state={0!r}".format(prerequisite),
                    expected="one of {0}".format(", ".join(GATE_PREREQUISITE_STATES)),
                )
            )
        result = record.payload.get("result")
        if result not in GATE_RESULTS:
            diagnostics.append(
                record.violation(
                    "GATE_RESULT_UNKNOWN",
                    item=label,
                    observed="result={0!r}".format(result),
                    expected="one of {0}".format(", ".join(GATE_RESULTS)),
                )
            )
            continue

        exit_status = record.payload.get("checker_exit_status")
        if gate_type == GATE_TYPE_EDITORIAL:
            if exit_status is not None:
                diagnostics.append(
                    record.violation(
                        "GATE_EDITORIAL_EXIT_STATUS",
                        item=label,
                        observed="checker_exit_status={0!r}".format(exit_status),
                        expected="null; an editorial gate derives from human "
                        "findings and has no checker exit status",
                    )
                )
            continue

        if prerequisite == "incomplete" and result != RESULT_INCOMPLETE:
            diagnostics.append(
                record.violation(
                    "GATE_INCOMPLETE_PREREQUISITE_RESULT",
                    item=label,
                    observed="prerequisite_state=incomplete result={0}".format(result),
                    expected="result of {0!r} whenever a prerequisite is "
                    "incomplete".format(RESULT_INCOMPLETE),
                )
            )
        expected_status = RESULT_EXIT_STATUS.get(str(result))
        if expected_status is not None and exit_status != expected_status:
            diagnostics.append(
                record.violation(
                    "GATE_EXIT_STATUS_DISAGREEMENT",
                    item=label,
                    observed="result={0} checker_exit_status={1!r}".format(
                        result, exit_status
                    ),
                    expected="checker_exit_status {0} for result {1!r}".format(
                        expected_status, result
                    ),
                )
            )
        diagnostic_ids = _stable_id_sequence(
            record.payload.get("objective_diagnostic_ids")
        )
        if diagnostic_ids is None:
            diagnostics.append(
                record.malformed(
                    "GATE_DIAGNOSTIC_IDS_MALFORMED",
                    observed="objective_diagnostic_ids={0!r}".format(
                        record.payload.get("objective_diagnostic_ids")
                    ),
                    expected="a unique list of CheckerDiagnostic references",
                )
            )
        elif result == RESULT_PASS and diagnostic_ids:
            diagnostics.append(
                record.violation(
                    "GATE_PASS_WITH_DIAGNOSTICS",
                    item=label,
                    observed="pass with {0} objective diagnostics".format(
                        len(diagnostic_ids)
                    ),
                    expected="zero objective diagnostics for a passing objective "
                    "gate",
                )
            )
    return tuple(diagnostics)


def check_finalization_gates(index: ReferenceIndex) -> Tuple[CheckerDiagnostic, ...]:
    """Requirement 11.11: `final` requires both independent gates to pass.

    The two gates are independent in both directions, which is the whole point:
    an objective pass cannot substitute for editorial approval, and editorial
    approval cannot override an objective violation or an incomplete
    prerequisite. This reports the missing side by name rather than a single
    undifferentiated failure, because the remedy differs completely.
    """

    passing: Dict[str, List[str]] = {}
    for record in index.of_type("GateResult"):
        gate_type = record.payload.get("gate_type")
        if gate_type not in (GATE_TYPE_MANUSCRIPT_GLOBAL, GATE_TYPE_EDITORIAL):
            continue
        if (
            record.payload.get("result") != RESULT_PASS
            or record.payload.get("prerequisite_state") != GATE_PREREQUISITE_COMPLETE
        ):
            continue
        label = _stable_id(record.payload.get("gate_result_id")) or record.identity
        passing.setdefault(str(gate_type), []).append(label)

    missing = [
        gate_type
        for gate_type in (GATE_TYPE_MANUSCRIPT_GLOBAL, GATE_TYPE_EDITORIAL)
        if not passing.get(gate_type)
    ]
    if not missing:
        return ()
    return (
        _diagnostic(
            "FINALIZATION_GATE_MISSING",
            scope=SCOPE_GLOBAL,
            item="manuscript",
            observed="no passing {0} GateResult".format(" or ".join(missing)),
            expected="separate passing manuscript-global and final editorial "
            "GateResults before the Manuscript may be marked final",
            disposition=DISPOSITION_INCOMPLETE,
            related=tuple(
                sorted(label for labels in passing.values() for label in labels)
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Mandatory Fluent_Pairing coverage
# ---------------------------------------------------------------------------


def check_fluent_pairing_coverage(
    index: ReferenceIndex,
) -> Tuple[CheckerDiagnostic, ...]:
    """Requirement 15.1: every mandatory range resolves to at least one beat.

    A beat is a `PAIR` TimelineEntry whose declared chapters intersect the range.
    Read from `technical_state.mode` and the entry's own chapter list only; no
    range is credited from prose commentary, and a `PAIR` entry with no chapters
    yet credits nothing.
    """

    covered: Dict[Tuple[int, int], List[str]] = {}
    for record in index.of_type("TimelineEntry"):
        technical_state = record.payload.get("technical_state")
        if not isinstance(technical_state, dict):
            continue
        if technical_state.get("mode") != "PAIR":
            continue
        chapters = record.payload.get("chapter_numbers")
        if not isinstance(chapters, list):
            continue
        label = _stable_id(record.payload.get("timeline_id")) or record.identity
        for start, end in FLUENT_PAIRING_RANGES:
            if any(
                _is_chapter_number(chapter) and start <= int(chapter) <= end
                for chapter in chapters
            ):
                covered.setdefault((start, end), []).append(label)

    diagnostics: List[CheckerDiagnostic] = []
    for span in FLUENT_PAIRING_RANGES:
        if span in covered:
            continue
        diagnostics.append(
            _diagnostic(
                "FLUENT_PAIRING_RANGE_UNCOVERED",
                scope=SCOPE_GLOBAL,
                item="chapters {0}\u2013{1}".format(*span),
                observed="no PAIR TimelineEntry assigned inside the range",
                expected="at least one mandatory Fluent_Pairing beat in every "
                "range {0}".format(
                    ", ".join(
                        "{0}\u2013{1}".format(*bounds)
                        for bounds in FLUENT_PAIRING_RANGES
                    )
                ),
            )
        )
    return tuple(diagnostics)


# ---------------------------------------------------------------------------
# Front_Matter rights and acknowledgment
#
# Requirements 9.10 to 9.12 are bookkeeping facts about a short document, so they
# are checked by exact-phrase presence and absence, not by reading the prose.
# Deliberately narrow: the checker verifies that the five Canon_Source titles are
# named, that *One-Time Pad* is not, and that the sound-recording and performance
# ownership vocabulary is absent from the notice. It makes no judgment about
# wording quality.
# ---------------------------------------------------------------------------

CANON_SOURCE_TITLES: Tuple[str, ...] = (
    "Case Zero",
    "Faraday",
    "The Final Frontier",
    "The Radius",
    "The Synaptic Frontier",
)
EXCLUDED_CANON_SOURCE_TITLE = "One-Time Pad"
# The ownership vocabulary Requirement 9.11 excludes from the prose notice. These
# are claims of ownership in a recording or a performance, not the ordinary words
# "recording" or "performance", so each phrase is matched whole.
PROHIBITED_RIGHTS_PHRASES: Tuple[str, ...] = (
    "sound recording copyright",
    "sound recording rights",
    "master recording",
    "phonogram rights",
    "performance rights",
    "performer's rights",
    "performers' rights",
    "neighbouring rights",
    "neighboring rights",
    "\u2117",
)
# The prose-rights facts Requirement 9.10 requires the document to state, as the
# accepted markers for each. Several forms are accepted per fact because the
# requirement is that the document identifies the author and the prose copyright
# holder, not that it uses one house phrasing; Requirement 12.11 keeps wording
# outside pass/fail.
REQUIRED_FRONT_MATTER_MARKERS: Mapping[str, Tuple[str, ...]] = {
    "author": ("a novel by", "author:", "written by"),
    "prose copyright holder": ("copyright", "\u00a9"),
}


def check_front_matter(
    path: Path, *, relative_path: Optional[str] = None
) -> Tuple[CheckerDiagnostic, ...]:
    """Requirements 9.10 to 9.12 over the Front_Matter document."""

    item = relative_path or Path(path).name
    try:
        text = Path(path).read_text(encoding="utf-8")
    except FileNotFoundError:
        return (
            _diagnostic(
                "FRONT_MATTER_MISSING",
                scope=SCOPE_GLOBAL,
                item=item,
                observed="no readable file at this path",
                expected="a Front_Matter document naming the author and prose "
                "copyright holder",
                disposition=DISPOSITION_INCOMPLETE,
            ),
        )
    except (OSError, UnicodeError) as exc:
        return (
            _diagnostic(
                "FRONT_MATTER_UNREADABLE",
                scope=SCOPE_GLOBAL,
                item=item,
                observed=str(exc),
                expected="readable UTF-8 text",
                disposition=DISPOSITION_INCOMPLETE,
            ),
        )

    normalized = normalize_prose(text)
    folded = normalized.casefold()
    diagnostics: List[CheckerDiagnostic] = []

    for description, markers in sorted(REQUIRED_FRONT_MATTER_MARKERS.items()):
        if not any(marker.casefold() in folded for marker in markers):
            diagnostics.append(
                _diagnostic(
                    "FRONT_MATTER_RIGHTS_FIELD_MISSING",
                    scope=SCOPE_GLOBAL,
                    item=item,
                    observed="no {0} statement".format(description),
                    expected="a stated {0} for the novel prose".format(description),
                )
            )

    present = [phrase for phrase in PROHIBITED_RIGHTS_PHRASES if phrase in folded]
    if present:
        diagnostics.append(
            _diagnostic(
                "FRONT_MATTER_RECORDING_OWNERSHIP_CLAIM",
                scope=SCOPE_GLOBAL,
                item=item,
                observed="contains {0}".format(", ".join(repr(p) for p in present)),
                expected="prose rights stated independently, with no "
                "sound-recording or performance ownership claim",
            )
        )

    if EXCLUDED_CANON_SOURCE_TITLE.casefold() in folded:
        diagnostics.append(
            _diagnostic(
                "FRONT_MATTER_EXCLUDED_SOURCE_ACKNOWLEDGED",
                scope=SCOPE_GLOBAL,
                item=item,
                observed="acknowledges {0!r}".format(EXCLUDED_CANON_SOURCE_TITLE),
                expected="no {0} acknowledgment; it is not a "
                "Canon_Source".format(EXCLUDED_CANON_SOURCE_TITLE),
            )
        )

    # Requirement 9.12 applies only *where* the author includes an
    # acknowledgment, so absence of every title is absence of the optional
    # section rather than an incomplete one. A partial list is the failure.
    named = [
        title for title in CANON_SOURCE_TITLES if title.casefold() in folded
    ]
    if named and len(named) != len(CANON_SOURCE_TITLES):
        missing = [title for title in CANON_SOURCE_TITLES if title not in named]
        diagnostics.append(
            _diagnostic(
                "FRONT_MATTER_SOURCE_ACKNOWLEDGMENT_INCOMPLETE",
                scope=SCOPE_GLOBAL,
                item=item,
                observed="names {0} of {1} Canon_Sources; missing {2}".format(
                    len(named), len(CANON_SOURCE_TITLES), ", ".join(missing)
                ),
                expected="all five source-song titles when an acknowledgment is "
                "included",
            )
        )
    return tuple(diagnostics)


# ---------------------------------------------------------------------------
# Requested-scope orchestration
# ---------------------------------------------------------------------------


def discover_chapter_files(manuscript_root: Path) -> Tuple[Path, ...]:
    """Every Chapter_File under `chapters/`, in movement then sequence order.

    Discovery is by the fixed filename convention, so a note or scratch file that
    does not parse as a Chapter_File name is not silently treated as a chapter.
    Such a file is reported by the outline/file bijection instead, which is where
    an unexpected manuscript file belongs.
    """

    root = Path(manuscript_root) / CHAPTERS_DIRECTORY
    if not root.is_dir():
        return ()
    found: List[Tuple[int, int, str, Path]] = []
    for path in sorted(root.rglob("*.md")):
        parsed = parse_chapter_filename(path.name)
        if parsed is None:
            continue
        found.append(
            (
                MOVEMENT_ORDER.get(parsed.movement, len(MOVEMENTS)),
                parsed.sequence,
                path.name,
                path,
            )
        )
    return tuple(item[3] for item in sorted(found, key=lambda item: item[:3]))


@dataclass(frozen=True)
class ScopeRun:
    """One completed chapter-or-batch run: what was asked, and what was found."""

    scope: str
    manuscript_root: str
    chapter_paths: Tuple[str, ...]
    chapters: Tuple[ChapterCheckResult, ...]
    diagnostics: Tuple[CheckerDiagnostic, ...]
    batch_kind: Optional[str] = None
    changed_references: Tuple[str, ...] = ()

    @property
    def chapter_numbers(self) -> Tuple[int, ...]:
        return tuple(
            sorted(
                {
                    result.chapter
                    for result in self.chapters
                    if result.chapter is not None
                }
            )
        )

    @property
    def result(self) -> str:
        return classify_result(self.diagnostics)

    @property
    def exit_status(self) -> int:
        return exit_status_for_result(self.result)


def check_global_scope(
    results: Sequence["ChapterCheckResult"],
    *,
    index: ReferenceIndex,
    manuscript_root: Path,
    front_matter_path: Optional[str] = DEFAULT_FRONT_MATTER_PATH,
) -> Tuple[CheckerDiagnostic, ...]:
    """Every whole-book objective check Requirement 11 assigns to global scope.

    Ordered so structure is established before the facts that depend on it: the
    outline's own sequence and movement blocks, then the outline-to-file
    bijection, then the counts and relationships that only mean something once
    both sides agree.

    Every check here is deliberately absent from chapter and batch scope, which
    is the separation Requirement 10.9 and Property 12 require.
    """

    diagnostics: List[CheckerDiagnostic] = []
    entries = index.arc_entries

    diagnostics.extend(check_outline_sequence(entries))
    diagnostics.extend(check_movement_blocks(entries))
    diagnostics.extend(check_outline_file_bijection(entries, results))

    # Whole-book POV facts. The roster's movement coverage and Anchor coverage are
    # read from the outline rather than from the delivered files, so an
    # undrafted-but-planned movement still counts as assigned.
    chapter_movements: Dict[str, set] = {}
    for entry in entries:
        pov_id = _stable_id(entry.payload.get("pov_id"))
        if pov_id is None or entry.movement not in MOVEMENT_ORDER:
            continue
        chapter_movements.setdefault(pov_id, set()).add(str(entry.movement))
    diagnostics.extend(
        check_pov_roster(
            index,
            chapter_movements={
                pov_id: frozenset(movements)
                for pov_id, movements in chapter_movements.items()
            },
        )
    )

    # Requirement 11.12 evaluates the run bounds from each Chapter_File's declared
    # `words`, while Requirement 2.15 evaluates the plan from `estimated_words`.
    # Both are reported, because a plan that already breaks the bound is a
    # planning violation even before the prose exists.
    diagnostics.extend(
        check_pov_runs(
            pov_runs(arc_entry_pov_assignments(entries)),
            scope=SCOPE_PLANNING,
            source="ArcEntry.estimated_words",
        )
    )
    declared: List[Tuple[int, str, Optional[int]]] = []
    for result in results:
        chapter = result.chapter
        pov_id = _stable_id(result.document.header.get("pov_id"))
        if chapter is None or pov_id is None:
            continue
        observed = (
            result.length_report.observed_words
            if result.length_report is not None
            else None
        )
        declared.append((chapter, pov_id, observed))
    diagnostics.extend(
        check_pov_runs(
            pov_runs(declared),
            scope=SCOPE_GLOBAL,
            source="ChapterHeader.words",
        )
    )

    diagnostics.extend(check_normal_share(results))
    totals = movement_word_totals(results)
    diagnostics.extend(check_movement_scale(totals))

    baseline, baseline_diagnostics = check_baseline(index)
    diagnostics.extend(baseline_diagnostics)
    diagnostics.extend(
        check_final_targets(
            baseline.final_targets,
            chapter_count=len(results),
            total_words=sum(totals.values()),
        )
    )

    # The planning-side reference checks run here with no batch scope, which means
    # the whole book is in view: mechanism state on every TimelineEntry, Pair
    # Calibration uniqueness across all of them, the Character_ID/POV_ID
    # bijection, and Cross_Cut reciprocity. They are deliberately *not* run for a
    # chapter scope, because validating every TimelineEntry would let one chapter's
    # gate fail for an unrelated record, which Requirement 10.9 forbids. A chapter
    # gets `check_direct_references` for its own references instead.
    diagnostics.extend(check_planning_references(index))

    diagnostics.extend(check_whole_book_literal_constraints(results, index))
    diagnostics.extend(check_motif_family_totals(index))
    diagnostics.extend(check_canon_facts(index))
    diagnostics.extend(check_canon_source_inventory(index))
    diagnostics.extend(check_novel_extensions(index))
    diagnostics.extend(check_reveals(index))
    diagnostics.extend(check_arc_changes(index))
    diagnostics.extend(check_status_synchronization(results))
    diagnostics.extend(check_gate_results(index))
    diagnostics.extend(check_finalization_gates(index))
    diagnostics.extend(check_fluent_pairing_coverage(index))

    if front_matter_path is not None:
        diagnostics.extend(
            check_front_matter(
                Path(manuscript_root).joinpath(*front_matter_path.split("/")),
                relative_path=front_matter_path,
            )
        )
    return tuple(diagnostics)


def run_scope(
    paths: Sequence[Path],
    *,
    scope: str,
    manuscript_root: Path,
    batch_kind: Optional[str] = None,
    changed_references: Sequence[str] = (),
    record_sources: Optional[Sequence[str]] = None,
) -> ScopeRun:
    """Run one `chapter`, `batch`, or `global` scope.

    Chapter scope evaluates one Chapter_File against its Direct_Planning_
    References only, per Requirement 10.1, and takes no changed references: a
    Chapter_Local_Gate has no batch to synchronize. Batch scope adds the delivered
    batch size rule and the changed cross-document reference audit of Requirement
    13.3 on top of every chapter violation. Global scope discovers every
    Chapter_File under the manuscript root, requires the whole-book record
    sources, and adds the Manuscript_Global_Gate.

    For chapter and batch scope Requirement 10.9 stays satisfied by omission.
    Nothing in those paths reaches for Final_Targets, whole-book POV distribution,
    cross-manuscript motif totals, movement length relationships, or final-ending
    acceptance.
    """

    if scope not in (SCOPE_CHAPTER, SCOPE_BATCH, SCOPE_GLOBAL):
        raise ValueError("unknown scope {0!r}".format(scope))
    if scope != SCOPE_BATCH and changed_references:
        raise ValueError(
            "{0} scope takes no changed references; they belong to a delivered "
            "batch".format(scope)
        )
    if scope != SCOPE_BATCH and batch_kind is not None:
        raise ValueError("batch_kind belongs to batch scope")

    root = Path(manuscript_root)
    if record_sources is None:
        record_sources = (
            GLOBAL_RECORD_SOURCES if scope == SCOPE_GLOBAL else DEFAULT_RECORD_SOURCES
        )
    if scope == SCOPE_GLOBAL:
        paths = discover_chapter_files(root)

    index, index_diagnostics = load_reference_index(root, sources=record_sources)
    scope_result = check_chapter_scope(
        paths, manuscript_root=root, reference_index=index
    )

    diagnostics: List[CheckerDiagnostic] = list(index_diagnostics)
    diagnostics.extend(scope_result.diagnostics)

    if scope == SCOPE_GLOBAL:
        diagnostics.extend(
            check_global_scope(
                scope_result.chapters, index=index, manuscript_root=root
            )
        )

    resolved_kind: Optional[str] = None
    if scope == SCOPE_BATCH:
        numbers = sorted(
            {
                result.chapter
                for result in scope_result.chapters
                if result.chapter is not None
            }
        )
        resolved_kind = (
            batch_kind if batch_kind is not None else classify_batch_kind(numbers)
        )
        diagnostics.extend(
            check_batch_composition(numbers, batch_kind=resolved_kind)
        )
        diagnostics.extend(
            check_changed_references(
                changed_references,
                index=index,
                chapter_scope=numbers,
                chapter_results=scope_result.chapters,
                known_sources=record_sources,
            )
        )

    return ScopeRun(
        scope=scope,
        manuscript_root=str(root),
        chapter_paths=tuple(
            manuscript_relative_path(Path(path), root) for path in paths
        ),
        chapters=scope_result.chapters,
        diagnostics=tuple(diagnostics),
        batch_kind=resolved_kind,
        changed_references=tuple(changed_references),
    )


# ---------------------------------------------------------------------------
# Deterministic diagnostic output
# ---------------------------------------------------------------------------


FORMAT_TEXT = "text"
FORMAT_JSON = "json"
REPORT_FORMATS: Tuple[str, ...] = (FORMAT_TEXT, FORMAT_JSON)

# Reported scope order: the narrowest first, so a chapter's own violations read
# before the batch and planning findings that depend on more than one document.
_SCOPE_REPORT_ORDER: Mapping[str, int] = {
    SCOPE_CHAPTER: 0,
    SCOPE_BATCH: 1,
    SCOPE_PLANNING: 2,
    SCOPE_GLOBAL: 3,
}


def _diagnostic_sort_key(
    diagnostic: CheckerDiagnostic,
) -> Tuple[int, str, str, str, str, str, str]:
    return (
        _SCOPE_REPORT_ORDER.get(diagnostic.scope, len(_SCOPE_REPORT_ORDER)),
        diagnostic.scope,
        diagnostic.item,
        diagnostic.code,
        diagnostic.observed,
        diagnostic.expected,
        diagnostic.severity,
    )


def sort_diagnostics(
    diagnostics: Iterable[CheckerDiagnostic],
) -> Tuple[CheckerDiagnostic, ...]:
    """Impose one total order on a diagnostic list.

    Every check already runs deterministically, but sorting at the output edge
    makes the emitted report independent of the order checks happen to append in,
    so the same normalized inputs always render byte-identically.
    """

    return tuple(sorted(diagnostics, key=_diagnostic_sort_key))


def _count_by(
    diagnostics: Iterable[CheckerDiagnostic], attribute: str
) -> Mapping[str, int]:
    counts: Dict[str, int] = {}
    for diagnostic in diagnostics:
        key = str(getattr(diagnostic, attribute))
        counts[key] = counts.get(key, 0) + 1
    return {key: counts[key] for key in sorted(counts)}


def diagnostic_as_json(diagnostic: CheckerDiagnostic) -> Dict[str, Any]:
    """The design's `CheckerDiagnostic` fields as a JSON-ready mapping."""

    return {
        "severity": diagnostic.severity,
        "code": diagnostic.code,
        "scope": diagnostic.scope,
        "item": diagnostic.item,
        "observed": diagnostic.observed,
        "expected": diagnostic.expected,
        "disposition": diagnostic.disposition,
        "details": {key: value for key, value in diagnostic.details},
        "related": list(diagnostic.related),
    }


def scope_run_as_json(run: ScopeRun) -> Dict[str, Any]:
    """The whole run as structured facts, matching the text report exactly."""

    ordered = sort_diagnostics(run.diagnostics)
    document: Dict[str, Any] = {
        "scope": run.scope,
        "manuscript_root": run.manuscript_root,
        "chapter_paths": list(run.chapter_paths),
        "chapter_numbers": list(run.chapter_numbers),
        "result": run.result,
        "exit_status": run.exit_status,
        "counts": {
            "total": len(ordered),
            "severity": _count_by(ordered, "severity"),
            "scope": _count_by(ordered, "scope"),
        },
        "diagnostics": [diagnostic_as_json(item) for item in ordered],
    }
    if run.scope == SCOPE_BATCH:
        document["batch_kind"] = run.batch_kind
        document["changed_references"] = list(run.changed_references)
    return document


def render_text_report(run: ScopeRun) -> str:
    """The author-facing report: one line per diagnostic, then the counts."""

    ordered = sort_diagnostics(run.diagnostics)
    lines = [diagnostic.format_text() for diagnostic in ordered]

    request = ["SUMMARY scope={0}".format(run.scope)]
    if run.scope == SCOPE_BATCH:
        request.append("batch_kind={0}".format(run.batch_kind))
    request.append(
        "chapters={0}".format(
            ",".join(str(number) for number in run.chapter_numbers) or "(none)"
        )
    )
    if run.scope == SCOPE_BATCH:
        request.append(
            "changed_references={0}".format(
                ",".join(sorted(set(run.changed_references))) or "(none)"
            )
        )
    request.append("result={0}".format(run.result))
    request.append("exit={0}".format(run.exit_status))
    lines.append(" ".join(request))

    severity_counts = _count_by(ordered, "severity")
    lines.append(
        "SEVERITY {0}".format(
            " ".join(
                "{0}={1}".format(name, severity_counts.get(name, 0))
                for name in (SEVERITY_ERROR, SEVERITY_WARNING)
            )
        )
    )
    scope_counts = _count_by(ordered, "scope")
    lines.append(
        "SCOPE {0}".format(
            " ".join(
                "{0}={1}".format(name, scope_counts.get(name, 0))
                for name in sorted(_SCOPE_REPORT_ORDER, key=_SCOPE_REPORT_ORDER.get)
            )
        )
    )
    if run.result == RESULT_PASS:
        lines.append(
            "PASS {0}-scope objective checks found no violation".format(run.scope)
        )
    return "\n".join(lines) + "\n"


def render_report(run: ScopeRun, *, report_format: str = FORMAT_TEXT) -> str:
    """Render a completed run in the requested format."""

    if report_format == FORMAT_TEXT:
        return render_text_report(run)
    if report_format == FORMAT_JSON:
        return (
            json.dumps(
                scope_run_as_json(run),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        )
    raise ValueError("unknown report format {0!r}".format(report_format))


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
    parser.add_argument(
        "--scope",
        choices=(SCOPE_CHAPTER, SCOPE_BATCH, SCOPE_GLOBAL),
        default=None,
        help=(
            "run the Chapter_Local_Gate, the delivered-batch audit, or the "
            "Manuscript_Global_Gate"
        ),
    )
    parser.add_argument(
        "--chapter",
        type=Path,
        default=None,
        help="the one Chapter_File to check with --scope chapter",
    )
    parser.add_argument(
        "--chapters",
        type=Path,
        nargs="+",
        default=None,
        metavar="PATH",
        help="the delivered Chapter_Files to check with --scope batch",
    )
    parser.add_argument(
        "--manuscript-root",
        type=Path,
        default=None,
        help=(
            "manuscript root holding planning/ and chapters/ "
            "(defaults to {0}/ under --workspace-root)".format(
                DEFAULT_MANUSCRIPT_ROOT
            )
        ),
    )
    parser.add_argument(
        "--changed-reference",
        action="append",
        default=None,
        metavar="RELATIVE_PATH",
        help=(
            "a changed cross-document reference this batch delivers, relative to "
            "the manuscript root; repeatable and valid only with --scope batch"
        ),
    )
    parser.add_argument(
        "--batch-kind",
        choices=BATCH_KINDS,
        default=None,
        help=(
            "declare the delivered batch kind; inferred from the chapter set "
            "when omitted"
        ),
    )
    parser.add_argument(
        "--format",
        dest="report_format",
        choices=REPORT_FORMATS,
        default=FORMAT_TEXT,
        help="diagnostic output format (default: text)",
    )
    return parser


def _resolve_chapter_argument(
    path: Path, *, manuscript_root: Path, workspace_root: Path
) -> Path:
    """Accept a Chapter_File path as given, or relative to either root."""

    candidate = Path(path)
    if candidate.is_absolute():
        return candidate
    for base in (Path.cwd(), manuscript_root, workspace_root):
        resolved = base / candidate
        if resolved.is_file():
            return resolved
    # Nothing matched. Return the manuscript-relative form so the fail-closed
    # missing-file diagnostic names the path the checker actually expected.
    return manuscript_root / candidate


def _run_scope_command(
    arguments: argparse.Namespace, parser: argparse.ArgumentParser
) -> int:
    """Validate a `--scope` invocation, run it, and print its report."""

    scope = arguments.scope
    if scope == SCOPE_CHAPTER:
        if arguments.chapter is None:
            parser.error("--scope chapter requires --chapter")
        if arguments.chapters:
            parser.error("--chapters belongs to --scope batch")
        if arguments.batch_kind is not None:
            parser.error("--batch-kind belongs to --scope batch")
        if arguments.changed_reference:
            # Requirement 10.1: the Chapter_Local_Gate evaluates only the current
            # Chapter_File and its Direct_Planning_References.
            parser.error(
                "--changed-reference belongs to --scope batch; the "
                "Chapter_Local_Gate reads only Direct_Planning_References"
            )
        requested: Sequence[Path] = (arguments.chapter,)
    elif scope == SCOPE_GLOBAL:
        if arguments.chapter is not None or arguments.chapters:
            parser.error(
                "--scope global discovers every Chapter_File under the "
                "manuscript root and takes no chapter arguments"
            )
        if arguments.batch_kind is not None:
            parser.error("--batch-kind belongs to --scope batch")
        if arguments.changed_reference:
            parser.error(
                "--changed-reference belongs to --scope batch; the "
                "Manuscript_Global_Gate evaluates the complete Manuscript"
            )
        requested = ()
    else:
        if not arguments.chapters:
            parser.error("--scope batch requires --chapters")
        if arguments.chapter is not None:
            parser.error("--chapter belongs to --scope chapter")
        requested = arguments.chapters

    workspace_root = Path(arguments.workspace_root)
    manuscript_root = (
        Path(arguments.manuscript_root)
        if arguments.manuscript_root is not None
        else workspace_root / DEFAULT_MANUSCRIPT_ROOT
    )

    run = run_scope(
        [
            _resolve_chapter_argument(
                path,
                manuscript_root=manuscript_root,
                workspace_root=workspace_root,
            )
            for path in requested
        ],
        scope=scope,
        manuscript_root=manuscript_root,
        batch_kind=arguments.batch_kind,
        changed_references=tuple(arguments.changed_reference or ()),
    )

    report = render_report(run, report_format=arguments.report_format)
    stream = sys.stdout if run.result == RESULT_PASS else sys.stderr
    print(report, end="", file=stream)
    return run.exit_status


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_argument_parser()
    arguments = parser.parse_args(argv)
    if arguments.site_exclusion and arguments.scope is not None:
        parser.error("--site-exclusion and --scope are separate gates; run one")
    if arguments.scope is not None:
        return _run_scope_command(arguments, parser)
    if not arguments.site_exclusion:
        parser.error(
            "choose a gate: --site-exclusion, or --scope chapter|batch|global"
        )

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
