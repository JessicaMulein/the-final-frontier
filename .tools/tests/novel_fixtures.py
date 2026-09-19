"""Shared synthetic-fixture builders for the objective manuscript checker suite.

Created by task 7.1 of the `The-Final-Frontier-novel` spec. Every later focused
test (task 7.7) and every principal property test (tasks 8.10 through 8.24)
builds its inputs from this module, so the fifteen properties all describe the
same synthetic world instead of fifteen private ones.

Scope and honesty boundaries
----------------------------
* The builders are **deterministic**. Nothing here randomizes. Hypothesis
  supplies variation later by choosing the arguments passed in.
* The builders construct *conforming* records by default and let a caller
  override any individual field, so a test injects exactly one violation
  instead of hand-writing a whole malformed tree.
* `count_prose_words` and `derive_length_class` exist so a builder can emit a
  self-consistent header. They are fixture-side conveniences that restate
  Requirement 9.7 and the Length_Class bands, **not** the checker. Property 4
  (task 8.13) and Property 5 (task 8.14) must assert the checker's own results
  against the specification, never against these helpers, or the test proves
  nothing.
* Nothing here writes into the real manuscript tree. Callers pass a pytest
  `tmp_path` (or any scratch directory) as the workspace base.

Authority: `The Final Frontier Novel/planning/record-schemas.md` for the
restricted ten-key Chapter_Header and the typed JSON fence contract,
`planning/file-conventions.md` for directory and filename shape, and
`The Final Frontier Novel/exclusion-contract.json` for the exclusion document.
"""

from __future__ import annotations

import copy
import importlib.util
import json
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

TESTS_ROOT = Path(__file__).resolve().parent
TOOLS_ROOT = TESTS_ROOT.parent
REPOSITORY_ROOT = TOOLS_ROOT.parent

CHECKER_PATH = TOOLS_ROOT / "check_novel.py"
# `.tools/` is not a package, so the checker is loaded from its file path. The
# module name matches the one `test_site_exclusion.py` already registers, so
# both entry points share a single module instance rather than executing
# `check_novel.py` twice under two names.
CHECKER_MODULE_NAME = "novel_site_exclusion"

MANUSCRIPT_ROOT_NAME = "The Final Frontier Novel"
COMMITTED_MANUSCRIPT_ROOT = REPOSITORY_ROOT / MANUSCRIPT_ROOT_NAME
COMMITTED_CONTRACT = COMMITTED_MANUSCRIPT_ROOT / "exclusion-contract.json"

MOVEMENTS: Tuple[str, ...] = (
    "discovery_part",
    "private_defense_part",
    "mindwars_part",
    "aftermath_coda",
)

# The ten restricted Chapter_Header keys, in the canonical order
# `record-schemas.md` defines. The key set is closed: no schema key or discriminator.
CHAPTER_HEADER_KEYS: Tuple[str, ...] = (
    "movement",
    "chapter",
    "title",
    "pov_id",
    "timeline_id",
    "motif_events",
    "hook",
    "words",
    "length_class",
    "status",
)

HEADER_DELIMITER = "---"
LENGTH_CLASSES = ("microchapter", "normal", "long-outlier")
CHAPTER_STATUSES = (
    "planned",
    "exploratory",
    "draft",
    "revised",
    "approved",
    "final",
)
HARD_CHAPTER_MAXIMUM = 2500
RECORD_SCHEMA_VERSION = 1
LITERAL_SCOPE_EXCLUSIONS: Tuple[str, ...] = (
    "canon-source-songs",
    "other-song-files",
    "planning-documents",
    "chapter-headers",
    "front-matter",
    "editorial-records",
    "checker-output",
)


class FixtureError(AssertionError):
    """A fixture was asked for something the schema cannot represent."""


# ---------------------------------------------------------------------------
# Checker loading
# ---------------------------------------------------------------------------


def load_checker() -> Any:
    """Return the `check_novel.py` module, loaded once and shared.

    Uses the same `importlib.util.spec_from_file_location` mechanism and the
    same module name as `test_site_exclusion.py`, so whichever module imports
    first wins and the other reuses it.
    """

    existing = sys.modules.get(CHECKER_MODULE_NAME)
    if existing is not None:
        return existing

    spec = importlib.util.spec_from_file_location(CHECKER_MODULE_NAME, CHECKER_PATH)
    if spec is None or spec.loader is None:  # pragma: no cover - import guard
        raise FixtureError(f"Unable to load checker module from {CHECKER_PATH}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


# ---------------------------------------------------------------------------
# Text, path, and count helpers
# ---------------------------------------------------------------------------


def normalize_text(value: str) -> str:
    """Normalize to Unicode NFC and to LF line endings."""

    return unicodedata.normalize("NFC", value).replace("\r\n", "\n").replace("\r", "\n")


def count_prose_words(prose: str) -> int:
    """Whitespace-token count of a Prose_Body (fixture-side expectation)."""

    return len(normalize_text(prose).split())


def derive_length_class(words: int) -> str:
    """Map an observed count onto a Length_Class band.

    Bands: below 700 `microchapter`, 700-1,600 `normal`, 1,601-2,500
    `long-outlier`. Above the Hard_Chapter_Maximum there is no valid class, so
    this raises rather than inventing one.
    """

    if words < 0:
        raise FixtureError(f"negative word count {words}")
    if words > HARD_CHAPTER_MAXIMUM:
        raise FixtureError(
            f"{words} words exceeds the Hard_Chapter_Maximum of "
            f"{HARD_CHAPTER_MAXIMUM}; no Length_Class applies"
        )
    if words < 700:
        return "microchapter"
    if words <= 1600:
        return "normal"
    return "long-outlier"


def movement_directory(movement: str) -> str:
    """Translate a header `movement` value to its directory/filename slug."""

    if movement not in MOVEMENTS:
        raise FixtureError(f"unknown movement {movement!r}")
    return movement.replace("_", "-")


def chapter_filename(movement: str, chapter: int, slug: str) -> str:
    """`<movement>-<three-digit-global-sequence>-<slug>.md`."""

    return "{0}-{1:03d}-{2}.md".format(movement_directory(movement), chapter, slug)


def chapter_relative_path(movement: str, chapter: int, slug: str) -> str:
    """Manuscript-relative chapter path, as an ArcEntry `filename` carries it."""

    return "chapters/{0}/{1}".format(
        movement_directory(movement), chapter_filename(movement, chapter, slug)
    )


def prose_of_length(words: int, *, per_line: int = 12) -> str:
    """Deterministic placeholder Prose_Body with exactly `words` tokens.

    Deliberately neutral filler, never novel prose, and it contains no phrase
    under a Literal_Phrase_Constraint.
    """

    if words < 0:
        raise FixtureError(f"negative word count {words}")
    if words == 0:
        return ""
    if per_line < 1:
        raise FixtureError("per_line must be at least 1")
    tokens = ["token{0:04d}".format(index) for index in range(1, words + 1)]
    lines = [
        " ".join(tokens[start : start + per_line])
        for start in range(0, len(tokens), per_line)
    ]
    return "\n".join(lines) + "\n"


DEFAULT_PROSE = prose_of_length(900)


# ---------------------------------------------------------------------------
# Chapter_Header and Chapter_File
# ---------------------------------------------------------------------------


def chapter_header(
    *,
    movement: str = "discovery_part",
    chapter: int = 1,
    title: str = "A Synthetic Chapter",
    pov_id: str = "POV-MARA",
    timeline_id: str = "TL-FIXTURE-001",
    motif_events: Optional[Sequence[str]] = None,
    hook: str = "A synthetic fixture hook line.",
    words: Optional[int] = None,
    length_class: Optional[str] = None,
    status: str = "draft",
    prose: Optional[str] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build the logical ten-key Chapter_Header object.

    `words` and `length_class` default to values consistent with `prose`, so a
    conforming header needs no bookkeeping from the caller. `overrides` sets any
    key, including an unknown one, and `drop_keys` removes required keys; both
    exist so a test can inject exactly one malformed-header violation.
    """

    body = DEFAULT_PROSE if prose is None else prose
    observed = count_prose_words(body) if words is None else words
    if length_class is None:
        length_class = derive_length_class(observed)

    header: Dict[str, Any] = {
        "movement": movement,
        "chapter": chapter,
        "title": title,
        "pov_id": pov_id,
        "timeline_id": timeline_id,
        "motif_events": list(motif_events or []),
        "hook": hook,
        "words": observed,
        "length_class": length_class,
        "status": status,
    }
    for key in drop_keys:
        header.pop(key, None)
    if overrides:
        header.update(overrides)
    return header


def _render_header_value(key: str, value: Any) -> str:
    if key in ("hook", "title"):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, list):
        return "[" + ", ".join(str(item) for item in value) + "]"
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return "null"
    return str(value)


def render_chapter_header(
    header: Mapping[str, Any],
    *,
    open_delimiter: str = HEADER_DELIMITER,
    close_delimiter: str = HEADER_DELIMITER,
    duplicate_key: Optional[str] = None,
) -> str:
    """Render the restricted delimited header block, one key per line.

    Follows the design's metadata example: bare enums, integers, and IDs, a
    quoted `hook`, and `motif_events` as a bracketed inline list. The delimiter
    arguments and `duplicate_key` let a test produce the malformed-delimiter and
    duplicate-key cases without rebuilding the renderer.
    """

    lines: List[str] = [open_delimiter]
    for key, value in header.items():
        lines.append("{0}: {1}".format(key, _render_header_value(key, value)))
        if duplicate_key is not None and key == duplicate_key:
            lines.append("{0}: {1}".format(key, _render_header_value(key, value)))
    lines.append(close_delimiter)
    return "\n".join(lines) + "\n"


def render_chapter_file(
    header: Mapping[str, Any],
    prose: Optional[str] = None,
    *,
    separator: str = "\n",
    **render_options: Any,
) -> str:
    """Render a complete Chapter_File: header block, then the Prose_Body."""

    body = DEFAULT_PROSE if prose is None else prose
    return render_chapter_header(header, **render_options) + separator + body


@dataclass(frozen=True)
class ChapterFixture:
    """One synthetic Chapter_File: where it lives and what it contains."""

    movement: str
    chapter: int
    slug: str
    header: Mapping[str, Any]
    prose: str
    render_options: Mapping[str, Any] = field(default_factory=dict)

    @property
    def filename(self) -> str:
        return chapter_filename(self.movement, self.chapter, self.slug)

    @property
    def relative_path(self) -> str:
        return chapter_relative_path(self.movement, self.chapter, self.slug)

    def text(self) -> str:
        return render_chapter_file(self.header, self.prose, **dict(self.render_options))


def chapter_fixture(
    *,
    movement: str = "discovery_part",
    chapter: int = 1,
    slug: str = "synthetic-fixture",
    prose: Optional[str] = None,
    header: Optional[Mapping[str, Any]] = None,
    render_options: Optional[Mapping[str, Any]] = None,
    **header_options: Any,
) -> ChapterFixture:
    """Build a `ChapterFixture` whose header agrees with its path and prose.

    Pass `header` to supply a fully hand-built header, or any
    `chapter_header` keyword to adjust the generated one.
    """

    body = DEFAULT_PROSE if prose is None else prose
    if header is None:
        header = chapter_header(
            movement=movement, chapter=chapter, prose=body, **header_options
        )
    elif header_options:
        raise FixtureError("pass either `header` or header keyword options, not both")
    return ChapterFixture(
        movement=movement,
        chapter=chapter,
        slug=slug,
        header=header,
        prose=body,
        render_options=dict(render_options or {}),
    )


# ---------------------------------------------------------------------------
# Typed JSON fences and planning documents
# ---------------------------------------------------------------------------


def render_json_fence(
    record_type: str,
    payload: Any,
    *,
    schema: int = RECORD_SCHEMA_VERSION,
    information_string: Optional[str] = None,
) -> str:
    """Render one typed fenced JSON record block.

    The opening fence sits at column zero with the exact information string
    `json record=<RecordType> schema=<n>`; the closing fence is three backticks
    at column zero. `information_string` overrides the whole thing so a test can
    produce an unknown record type or unsupported schema version.
    """

    if information_string is None:
        information_string = "json record={0} schema={1}".format(record_type, schema)
    body = json.dumps(payload, ensure_ascii=False, indent=2)
    return "```{0}\n{1}\n```\n".format(information_string, body)


@dataclass(frozen=True)
class PlanningDocument:
    """One synthetic planning document and its typed fenced records."""

    relative_path: str
    title: str
    blocks: Sequence[Tuple[str, Any]] = ()
    preamble: Optional[str] = None

    def text(self) -> str:
        parts = ["# {0}\n".format(self.title)]
        if self.preamble:
            parts.append(self.preamble.rstrip("\n") + "\n")
        else:
            parts.append(
                "Synthetic fixture document. It carries no continuity authority.\n"
            )
        for record_type, payload in self.blocks:
            parts.append(render_json_fence(record_type, payload))
        return "\n".join(parts)


def planning_document(
    relative_path: str,
    *,
    title: Optional[str] = None,
    blocks: Sequence[Tuple[str, Any]] = (),
    preamble: Optional[str] = None,
) -> PlanningDocument:
    """Build a planning document; `relative_path` is manuscript-root relative."""

    if title is None:
        title = Path(relative_path).stem.replace("-", " ").title()
    return PlanningDocument(
        relative_path=relative_path,
        title=title,
        blocks=tuple(blocks),
        preamble=preamble,
    )


# ---------------------------------------------------------------------------
# Planning record builders
# ---------------------------------------------------------------------------


def arc_entry(
    *,
    chapter: int = 1,
    movement: str = "discovery_part",
    slug: str = "synthetic-fixture",
    filename: Optional[str] = None,
    timeline_id: str = "TL-FIXTURE-001",
    pov_id: str = "POV-MARA",
    purpose: str = "A synthetic outline purpose sentence.",
    hook: str = "A synthetic fixture hook line.",
    cross_cuts: Any = "none",
    motif_events: Optional[Sequence[str]] = None,
    estimated_length_class: Optional[str] = None,
    estimated_words: Optional[int] = 900,
    outlier_purpose: Optional[str] = None,
    status: str = "draft",
    calibration_selected: bool = False,
    representative_purpose: Optional[str] = None,
    record_horizon: Optional[Mapping[str, Any]] = None,
    reveal_ids: Optional[Sequence[str]] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build one conforming `ArcEntry` record."""

    if estimated_length_class is None:
        estimated_length_class = (
            derive_length_class(estimated_words)
            if estimated_words is not None
            else "normal"
        )
    record: Dict[str, Any] = {
        "chapter": chapter,
        "filename": filename
        if filename is not None
        else chapter_relative_path(movement, chapter, slug),
        "movement": movement,
        "timeline_id": timeline_id,
        "pov_id": pov_id,
        "purpose": purpose,
        "hook": hook,
        "cross_cuts": cross_cuts,
        "motif_events": list(motif_events or []),
        "estimated_length_class": estimated_length_class,
        "estimated_words": estimated_words,
        "outlier_purpose": outlier_purpose,
        "status": status,
        "calibration_selected": calibration_selected,
        "representative_purpose": representative_purpose,
        "record_horizon": dict(record_horizon)
        if record_horizon is not None
        else {
            "through_timeline_id": timeline_id,
            "knowledge_limit": "Synthetic fixture knowledge limit.",
        },
        "reveal_ids": list(reveal_ids or []),
    }
    return _finish_record(record, overrides, drop_keys)


def pov_profile(
    *,
    character_id: str = "CHAR-001",
    pov_id: str = "POV-MARA",
    selected_name: str = "Fixture One",
    aliases: Optional[Sequence[str]] = None,
    anchor: bool = True,
    movement_coverage: Optional[Sequence[str]] = None,
    provisional_load: Optional[Mapping[str, int]] = None,
    voice_brief_id: str = "VOICE-FIXTURE-ONE",
    relationships: Optional[Sequence[Mapping[str, str]]] = None,
    blind_spots: Optional[Sequence[str]] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build one conforming human `POVProfile` record.

    `entity_type` is always `human` by default; a test that needs the invalid
    signal/adversary case sets it through `overrides`, which keeps the
    prohibition visible at the call site.
    """

    coverage = list(movement_coverage) if movement_coverage is not None else list(MOVEMENTS)
    if provisional_load is None:
        provisional_load = {movement: 1 for movement in MOVEMENTS}
        provisional_load["total"] = len(MOVEMENTS)
    record: Dict[str, Any] = {
        "character_id": character_id,
        "pov_id": pov_id,
        "selected_name": selected_name,
        "aliases": list(aliases or []),
        "entity_type": "human",
        "anchor": anchor,
        "knowledge_position": "Synthetic fixture knowledge position.",
        "moral_pressure": "Synthetic fixture moral pressure.",
        "plot_function": "Synthetic fixture plot function.",
        "relationships": [dict(item) for item in (relationships or [])],
        "blind_spots": list(blind_spots or ["Synthetic fixture blind spot."]),
        "reason_to_narrate": "Synthetic fixture reason to narrate.",
        "movement_coverage": coverage,
        "provisional_load": dict(provisional_load),
        "voice_brief_id": voice_brief_id,
    }
    return _finish_record(record, overrides, drop_keys)


def technical_state(
    *,
    mode: str = "not-applicable",
    source_side_continuity: str = "not-applicable",
    receiver_offset_seconds: Optional[int] = None,
    apparatus_mode: str = "not-applicable",
    transmit_stage_present: Optional[bool] = None,
    person_specific_address_state: str = "not-applicable",
    cancel_state: Optional[Mapping[str, Any]] = None,
    pair_state: Optional[Mapping[str, Any]] = None,
    pairing_evidence: Optional[Mapping[str, Any]] = None,
    evidence_scope: str = "Synthetic fixture evidence scope.",
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build a `TimelineEntry.technical_state` object.

    Defaults to `not-applicable`: no neural-communication event and all three
    mode-specific objects null. A mode-specific fixture passes `mode` plus the
    matching object, which keeps the four-mode invariants visible in the test
    rather than hidden in a default.
    """

    record: Dict[str, Any] = {
        "mode": mode,
        "source_side_continuity": source_side_continuity,
        "receiver_offset_seconds": receiver_offset_seconds,
        "apparatus_mode": apparatus_mode,
        "transmit_stage_present": transmit_stage_present,
        "person_specific_address_state": person_specific_address_state,
        "cancel_state": dict(cancel_state) if cancel_state is not None else None,
        "pair_state": dict(pair_state) if pair_state is not None else None,
        "pairing_evidence": dict(pairing_evidence)
        if pairing_evidence is not None
        else None,
        "evidence_scope": evidence_scope,
    }
    return _finish_record(record, overrides, drop_keys)


def timeline_entry(
    *,
    timeline_id: str = "TL-FIXTURE-001",
    chronology_kind: str = "point",
    canon_status: str = "novel-extension",
    relative_chronology: str = "A synthetic fixture chronology point.",
    exact_time: Optional[str] = None,
    duration: Optional[str] = None,
    location: Optional[str] = None,
    participants: Optional[Sequence[str]] = None,
    chapter_numbers: Optional[Sequence[int]] = None,
    fact_refs: Optional[Sequence[Mapping[str, str]]] = None,
    uncertainty_notes: Optional[Sequence[str]] = None,
    record_chronology: Optional[Mapping[str, Any]] = None,
    state: Optional[Mapping[str, Any]] = None,
    cross_cut_ids: Optional[Sequence[str]] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build one conforming `TimelineEntry` record.

    `state` populates `technical_state`; it defaults to the `not-applicable`
    object so an ordinary chronology fixture asserts no mechanism claim.
    """

    record: Dict[str, Any] = {
        "timeline_id": timeline_id,
        "chronology_kind": chronology_kind,
        "canon_status": canon_status,
        "relative_chronology": relative_chronology,
        "exact_time": exact_time,
        "duration": duration,
        "location": location,
        "participants": list(participants or ["CHAR-001"]),
        "chapter_numbers": sorted(chapter_numbers or [1]),
        "fact_refs": [dict(item) for item in (fact_refs or [])],
        "uncertainty_notes": list(uncertainty_notes or []),
        "record_chronology": dict(record_chronology)
        if record_chronology is not None
        else None,
        "technical_state": dict(state) if state is not None else technical_state(),
        "cross_cut_ids": list(cross_cut_ids or []),
    }
    return _finish_record(record, overrides, drop_keys)


def cross_cut(
    *,
    cross_cut_id: str = "CUT-FIXTURE-001",
    chapters: Sequence[int] = (1, 2),
    shared_timeline_id: Optional[str] = "TL-FIXTURE-001",
    shared_reveal_id: Optional[str] = None,
    shared_consequence: Optional[str] = None,
    handoff_mode: str = "sensory-match",
    material_narrative_value: Optional[Sequence[Mapping[str, Any]]] = None,
    replay_boundary: str = "Synthetic fixture replay boundary.",
    declared_by_chapters: Optional[Sequence[int]] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build one conforming, reciprocal `CrossCut` record."""

    ordered = sorted(chapters)
    if material_narrative_value is None:
        material_narrative_value = [
            {
                "chapter": number,
                "value": "Synthetic distinct value for chapter {0}.".format(number),
            }
            for number in ordered
        ]
    record: Dict[str, Any] = {
        "cross_cut_id": cross_cut_id,
        "chapters": ordered,
        "shared_timeline_id": shared_timeline_id,
        "shared_reveal_id": shared_reveal_id,
        "shared_consequence": shared_consequence,
        "handoff_mode": handoff_mode,
        "material_narrative_value": [dict(item) for item in material_narrative_value],
        "replay_boundary": replay_boundary,
        "declared_by_chapters": sorted(declared_by_chapters)
        if declared_by_chapters is not None
        else list(ordered),
    }
    return _finish_record(record, overrides, drop_keys)


def motif_event(
    *,
    motif_event_id: str = "MOT-FIXTURE-01",
    family: str = "fixture",
    dramatic_function: str = "Synthetic fixture dramatic function.",
    movement: str = "discovery_part",
    planned_chapter: int = 1,
    participating_chapters: Optional[Sequence[int]] = None,
    representation_mode: str = "image",
    literal_constraint_id: Optional[str] = None,
    scene_scope: str = "Synthetic fixture scene scope.",
    arc_change_history: Optional[Sequence[str]] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build one conforming `MotifEvent` record."""

    participating = (
        sorted(participating_chapters)
        if participating_chapters is not None
        else [planned_chapter]
    )
    record: Dict[str, Any] = {
        "motif_event_id": motif_event_id,
        "family": family,
        "dramatic_function": dramatic_function,
        "movement": movement,
        "planned_chapter": planned_chapter,
        "participating_chapters": participating,
        "representation_mode": representation_mode,
        "literal_constraint_id": literal_constraint_id,
        "scene_scope": scene_scope,
        "arc_change_history": list(arc_change_history or []),
    }
    return _finish_record(record, overrides, drop_keys)


def literal_phrase_constraint(
    *,
    constraint_id: str = "LPC-FIXTURE-001",
    motif_event_id: str = "MOT-FIXTURE-01",
    exact_phrase: str = "Fixture phrase?",
    allowed_movements: Sequence[str] = ("discovery_part",),
    allowed_chapters: Sequence[int] = (),
    allowed_files: Sequence[str] = (),
    allowed_span: Optional[Mapping[str, Any]] = None,
    minimum_in_scope: Optional[int] = None,
    maximum_in_scope: Optional[int] = None,
    exact_in_scope: Optional[int] = None,
    maximum_outside_scope: int = 0,
    diagnostic_code: str = "LITERAL_FIXTURE_SCOPE",
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build one conforming `LiteralPhraseConstraint` record."""

    record: Dict[str, Any] = {
        "constraint_id": constraint_id,
        "motif_event_id": motif_event_id,
        "exact_phrase": exact_phrase,
        "scan_scope": "chapter-prose-body-only",
        "allowed_movements": list(allowed_movements),
        "allowed_chapters": list(allowed_chapters),
        "allowed_files": list(allowed_files),
        "allowed_span": copy.deepcopy(allowed_span),
        "minimum_in_scope": minimum_in_scope,
        "maximum_in_scope": maximum_in_scope,
        "exact_in_scope": exact_in_scope,
        "maximum_outside_scope": maximum_outside_scope,
        "normalization": {
            "unicode": "NFC",
            "line_endings": "LF",
            "case_sensitive": True,
            "punctuation_sensitive": True,
            "word_order_sensitive": True,
            "match_mode": "non-overlapping-literal",
        },
        "scope_exclusions": list(LITERAL_SCOPE_EXCLUSIONS),
        "diagnostic_code": diagnostic_code,
    }
    return _finish_record(record, overrides, drop_keys)


def voice_brief(
    *,
    voice_brief_id: str = "VOICE-FIXTURE-ONE",
    pov_id: str = "POV-MARA",
    syntax_rhythm: str = "Synthetic fixture qualitative rhythm tendency.",
    image_sensory_families: Optional[Sequence[str]] = None,
    emotional_distance: str = "Synthetic fixture emotional distance.",
    omission_evasion_delayed_notice: Optional[Sequence[str]] = None,
    reverb_profile: Optional[Mapping[str, str]] = None,
    movement_evolution: Optional[Sequence[Mapping[str, str]]] = None,
    coda_turn: Optional[Mapping[str, Any]] = None,
    calibration_evidence: Optional[Sequence[Mapping[str, Any]]] = None,
    first_appearance_review: Optional[Mapping[str, Any]] = None,
    movements: Sequence[str] = MOVEMENTS,
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build one conforming `VoiceBrief` record.

    Every field is qualitative by construction. The schema forbids a numeric
    sentence-length target, vocabulary quota, style score, or quality threshold,
    so no builder default supplies one.
    """

    record: Dict[str, Any] = {
        "voice_brief_id": voice_brief_id,
        "pov_id": pov_id,
        "syntax_rhythm": syntax_rhythm,
        "image_sensory_families": list(
            image_sensory_families or ["synthetic fixture image family"]
        ),
        "emotional_distance": emotional_distance,
        "omission_evasion_delayed_notice": list(
            omission_evasion_delayed_notice or ["Synthetic fixture delayed notice."]
        ),
        "reverb_profile": dict(reverb_profile)
        if reverb_profile is not None
        else {
            "name": "Synthetic-fixture-reverb",
            "expectations": "Synthetic fixture reverb expectations.",
        },
        "movement_evolution": [dict(item) for item in movement_evolution]
        if movement_evolution is not None
        else [
            {
                "movement": movement,
                "evolution": "Synthetic fixture evolution in {0}.".format(movement),
            }
            for movement in movements
        ],
        "coda_turn": dict(coda_turn) if coda_turn is not None else None,
        "calibration_evidence": [dict(item) for item in (calibration_evidence or [])],
        "first_appearance_review": dict(first_appearance_review)
        if first_appearance_review is not None
        else None,
    }
    return _finish_record(record, overrides, drop_keys)


def novel_extension(
    *,
    extension_id: str = "EXT-FIXTURE-001",
    extension_kind: str = "other-continuity",
    fact: str = "A synthetic fixture continuity proposition.",
    rationale: str = "Synthetic fixture rationale.",
    authority_ref: Optional[str] = "DEC-FIXTURE",
    first_dependency: Optional[Mapping[str, str]] = None,
    affected_records: Optional[Sequence[Mapping[str, str]]] = None,
    consistency_implications: Optional[Sequence[str]] = None,
    state: str = "approved",
    superseding_arc_change_id: Optional[str] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build one conforming `NovelExtension` record."""

    record: Dict[str, Any] = {
        "extension_id": extension_id,
        "extension_kind": extension_kind,
        "fact": fact,
        "rationale": rationale,
        "authority_ref": authority_ref,
        "first_dependency": dict(first_dependency)
        if first_dependency is not None
        else {"record_type": "ArcEntry", "record_id": "1"},
        "affected_records": [dict(item) for item in affected_records]
        if affected_records is not None
        else [{"record_type": "POVProfile", "record_id": "POV-MARA"}],
        "consistency_implications": list(
            consistency_implications or ["Synthetic fixture consistency implication."]
        ),
        "state": state,
        "superseding_arc_change_id": superseding_arc_change_id,
    }
    return _finish_record(record, overrides, drop_keys)


def character_name_extension(
    *,
    character_id: str = "CHAR-005",
    selected_name: str = "Fixture Five",
    extension_id: Optional[str] = None,
    state: str = "approved",
    fact: Optional[str] = None,
    **extension_options: Any,
) -> Dict[str, Any]:
    """Build the `character-name` extension that declares one Character ID.

    The registry rule is machine-readable from the record itself: the Character
    ID is the first whitespace-delimited token of `fact`. The default `fact`
    therefore begins with the ID and then states the `selected_name`, which is
    also what the profile-agreement rule needs.
    """

    if fact is None:
        fact = "{0} identifies {1}, a synthetic fixture person.".format(
            character_id, selected_name
        )
    if extension_id is None:
        extension_id = "EXT-{0}-NAME".format(character_id)
    return novel_extension(
        extension_id=extension_id,
        extension_kind="character-name",
        fact=fact,
        state=state,
        **extension_options,
    )


def cancel_state(
    *,
    scope: str = "bounded-local",
    individual_consent: Optional[Mapping[str, Any]] = None,
    institutional_authorization: Optional[str] = None,
    subtraction: str = (
        "Removal of access to some mental content within the field volume."
    ),
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build a conforming `CancelState` object.

    Defaults to `bounded-local` with one deliberately exposed consenting
    individual. The four booleans are `false` and both enums are `none` because
    the schema fixes them: a `CANCEL` has no additive inverse, no predictable or
    enumerable affected set, no complete post-hoc map, no inserted payload, and
    no provenance yield. A test that needs one of those wrong passes `overrides`,
    which keeps the violation visible at the call site.
    """

    if scope == "bounded-local" and individual_consent is None:
        individual_consent = {
            "character_id": "CHAR-002",
            "current": True,
            "specific_act": "Synthetic fixture consent to this bounded exposure.",
            "revocable": True,
        }
    if scope == "area-scale" and institutional_authorization is None:
        institutional_authorization = (
            "Synthetic fixture emergency authorization issued by a civil "
            "authority; not individual consent from affected persons."
        )
    record: Dict[str, Any] = {
        "scope": scope,
        "individual_consent": dict(individual_consent)
        if individual_consent is not None
        else None,
        "institutional_authorization": institutional_authorization,
        "subtraction": subtraction,
        "inserted_content": "none",
        "affected_set_predictable_before": False,
        "affected_set_enumerable_during": False,
        "affected_set_fully_mapped_after": False,
        "additive_inverse_exists": False,
        "provenance_yield": "none",
    }
    return _finish_record(record, overrides, drop_keys)


def pair_state(
    *,
    participants: Sequence[str] = ("CHAR-001", "CHAR-002"),
    consent: Optional[Mapping[str, Any]] = None,
    calibration_id: str = "CAL-FIXTURE-001",
    calibration_participants: Optional[Sequence[str]] = None,
    calibration_transferable: bool = False,
    deliberate_send_state: str = "required",
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build a conforming `PairState` object: two living consenting participants."""

    record: Dict[str, Any] = {
        "participants": list(participants),
        "consent": dict(consent)
        if consent is not None
        else {
            "current": True,
            "specific_act": "Synthetic fixture consent to this pairing session.",
            "revocable": True,
            "authorized_a": True,
            "authorized_b": True,
        },
        "calibration_id": calibration_id,
        "calibration_participants": list(
            calibration_participants
            if calibration_participants is not None
            else participants
        ),
        "calibration_transferable": calibration_transferable,
        "deliberate_send_state": deliberate_send_state,
    }
    return _finish_record(record, overrides, drop_keys)


def pairing_evidence(
    *,
    content_recording_enabled: bool = False,
    recording_consent_a: bool = False,
    recording_consent_b: bool = False,
    transcript: Optional[Mapping[str, Any]] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build a conforming `PairingEvidence` object.

    Consent-state and transport metadata are present and semantically opaque
    because the schema fixes all three to `true`. Content recording starts
    disabled with no transcript, which is the schema's initial value.
    """

    record: Dict[str, Any] = {
        "consent_state_metadata_present": True,
        "transport_metadata_present": True,
        "metadata_semantically_opaque": True,
        "content_recording_enabled": content_recording_enabled,
        "recording_consent_a": recording_consent_a,
        "recording_consent_b": recording_consent_b,
        "transcript": dict(transcript) if transcript is not None else None,
    }
    return _finish_record(record, overrides, drop_keys)


def _finish_record(
    record: Dict[str, Any],
    overrides: Optional[Mapping[str, Any]],
    drop_keys: Sequence[str],
) -> Dict[str, Any]:
    for key in drop_keys:
        record.pop(key, None)
    if overrides:
        record.update(overrides)
    return record


# ---------------------------------------------------------------------------
# Exclusion contract and reference visibility plan
# ---------------------------------------------------------------------------


def committed_contract_document() -> Dict[str, Any]:
    """Return a deep copy of the committed exclusion contract document.

    Deriving fixtures from the committed file keeps them honest: a real schema
    change breaks the fixtures instead of leaving them agreeing with a stale
    private copy.
    """

    with COMMITTED_CONTRACT.open(encoding="utf-8") as handle:
        return json.load(handle)


def contract_document(
    *,
    manuscript_root_name: str = MANUSCRIPT_ROOT_NAME,
    contract_filename: str = "exclusion-contract.json",
    overrides: Optional[Mapping[str, Any]] = None,
    mutate: Optional[Callable[[Dict[str, Any]], None]] = None,
) -> Dict[str, Any]:
    """Build a contract document for a synthetic workspace.

    `declared_at` and the declared exclusion path are rewritten from
    `manuscript_root_name`, so a fixture may rename its manuscript root and stay
    self-consistent. `overrides` replaces top-level keys and `mutate` receives
    the document for nested edits, which is how a test produces stale, malformed,
    or unsupported-schema contracts.
    """

    document = committed_contract_document()
    document["declared_at"] = "{0}/{1}".format(manuscript_root_name, contract_filename)
    # Synthetic workspaces declare the manuscript exclusion only.
    #
    # The committed contract also excludes the audiobook subproject root, which
    # exists in this repository but not in a temporary fixture tree. Every
    # exclusion carries `must_exist: true`, so keeping that second entry would
    # make each synthetic workspace fail as a stale contract unless it also
    # created that directory and its required children. Dropping it keeps these
    # fixtures aimed at the rule under test -- manuscript isolation -- while the
    # committed contract is verified separately against the real workspace.
    document["exclusions"] = [
        exclusion
        for exclusion in document.get("exclusions", [])
        if not isinstance(exclusion, dict)
        or exclusion.get("id") == "EXCL-MANUSCRIPT-ROOT"
    ]
    for exclusion in document["exclusions"]:
        if isinstance(exclusion, dict) and exclusion.get("kind") == "source-root":
            exclusion["path"] = manuscript_root_name
    if overrides:
        document.update(copy.deepcopy(dict(overrides)))
    if mutate is not None:
        mutate(document)
    return document


def visibility_plan_document(
    rows: Optional[Sequence[Mapping[str, Any]]] = None,
    *,
    default_visible: bool = True,
    schema: str = "reference-song-visibility/v1",
    overrides: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Build a `reference-song-visibility/v1` plan document."""

    document: Dict[str, Any] = {
        "schema": schema,
        "default_visible": default_visible,
        "rows": [dict(row) for row in (rows or [])],
    }
    if overrides:
        document.update(dict(overrides))
    return document


def visibility_row(
    source: str,
    *,
    visible: bool = True,
    title: Optional[str] = None,
    slug: Optional[str] = None,
) -> Dict[str, Any]:
    """Build one visibility row, omitting optional keys left as `None`."""

    row: Dict[str, Any] = {"source": source, "visible": visible}
    if title is not None:
        row["title"] = title
    if slug is not None:
        row["slug"] = slug
    return row


# ---------------------------------------------------------------------------
# Workspace composition
# ---------------------------------------------------------------------------

DEFAULT_FRONT_MATTER = "# Synthetic Front Matter\n\nManuscript root markdown.\n"
DEFAULT_SONGS: Mapping[str, str] = {
    "songs/control-song.md": "[Verse]\nA valid control song remains collectible.\n",
}


@dataclass(frozen=True)
class SyntheticWorkspace:
    """A synthetic workspace tree and the paths a checker run needs."""

    root: Path
    manuscript_root: Path
    contract_path: Path
    visibility_plan_path: Optional[Path]
    chapters: Tuple[ChapterFixture, ...] = ()
    planning: Tuple[PlanningDocument, ...] = ()

    def path(self, relative_path: str) -> Path:
        return self.root.joinpath(*relative_path.split("/"))

    def chapter_path(self, fixture: ChapterFixture) -> Path:
        return self.manuscript_root.joinpath(*fixture.relative_path.split("/"))

    def read(self, relative_path: str) -> str:
        return self.path(relative_path).read_text(encoding="utf-8")


def write_text(base: Path, relative_path: str, content: str) -> Path:
    """Write UTF-8 text at `relative_path` under `base`, creating parents."""

    path = base.joinpath(*relative_path.split("/"))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def write_json(base: Path, relative_path: str, document: Any) -> Path:
    """Write a JSON document at `relative_path` under `base`."""

    return write_text(
        base, relative_path, json.dumps(document, ensure_ascii=False, indent=2) + "\n"
    )


def build_workspace(
    base: Path,
    *,
    manuscript_root_name: str = MANUSCRIPT_ROOT_NAME,
    contract: Optional[Mapping[str, Any]] = None,
    contract_filename: Optional[str] = "exclusion-contract.json",
    movements: Sequence[str] = MOVEMENTS,
    chapters: Sequence[ChapterFixture] = (),
    planning: Sequence[PlanningDocument] = (),
    front_matter: Optional[str] = DEFAULT_FRONT_MATTER,
    songs: Optional[Mapping[str, str]] = None,
    visibility: Optional[Mapping[str, Any]] = None,
    visibility_filename: str = "reference-visibility.json",
    extra_files: Optional[Mapping[str, str]] = None,
) -> SyntheticWorkspace:
    """Compose a synthetic workspace from the small builders above.

    This is a thin composer, not a second implementation: every piece comes from
    a builder a test can call directly. Defaults produce the tree the exclusion
    collector needs (a contract, a manuscript root with `planning/` and
    `chapters/<movement>/`, root and nested manuscript markdown, and one eligible
    control song outside the manuscript). Pass `contract_filename=None` to omit
    the contract entirely for a fail-closed case.
    """

    base = Path(base)
    base.mkdir(parents=True, exist_ok=True)
    manuscript_root = base / manuscript_root_name
    (manuscript_root / "planning").mkdir(parents=True, exist_ok=True)
    for movement in movements:
        (manuscript_root / "chapters" / movement_directory(movement)).mkdir(
            parents=True, exist_ok=True
        )

    contract_path = manuscript_root / (contract_filename or "exclusion-contract.json")
    if contract_filename is not None:
        document = (
            dict(contract)
            if contract is not None
            else contract_document(
                manuscript_root_name=manuscript_root_name,
                contract_filename=contract_filename,
            )
        )
        write_json(
            manuscript_root, contract_filename, document
        )

    if front_matter is not None:
        write_text(manuscript_root, "front-matter.md", front_matter)

    for document in planning:
        write_text(manuscript_root, document.relative_path, document.text())

    for fixture in chapters:
        write_text(manuscript_root, fixture.relative_path, fixture.text())

    for relative_path, content in (
        DEFAULT_SONGS if songs is None else songs
    ).items():
        write_text(base, relative_path, content)

    for relative_path, content in (extra_files or {}).items():
        write_text(base, relative_path, content)

    visibility_plan_path: Optional[Path] = None
    if visibility is not None:
        visibility_plan_path = write_json(base, visibility_filename, visibility)

    return SyntheticWorkspace(
        root=base,
        manuscript_root=manuscript_root,
        contract_path=contract_path,
        visibility_plan_path=visibility_plan_path,
        chapters=tuple(chapters),
        planning=tuple(planning),
    )


def default_planning_documents() -> Tuple[PlanningDocument, ...]:
    """A small conforming planning set: outline, roster, and ledger records.

    Deliberately minimal. Later tasks add the documents their own records need;
    this exists so a workspace has real typed fenced JSON to parse and real
    manuscript markdown for the exclusion collector to skip.
    """

    return (
        planning_document(
            "planning/arc-outline.md",
            title="Arc Outline",
            blocks=(
                ("ArcEntry", arc_entry(chapter=1, cross_cuts=["CUT-FIXTURE-001"])),
                (
                    "ArcEntry",
                    arc_entry(
                        chapter=2,
                        pov_id="POV-TWO",
                        slug="second-fixture",
                        cross_cuts=["CUT-FIXTURE-001"],
                    ),
                ),
                ("CrossCut", cross_cut()),
            ),
        ),
        planning_document(
            "planning/pov-roster.md",
            title="POV Roster",
            blocks=(
                ("POVProfile", pov_profile()),
                (
                    "POVProfile",
                    pov_profile(
                        character_id="CHAR-002",
                        pov_id="POV-TWO",
                        selected_name="Fixture Two",
                        anchor=False,
                        voice_brief_id="VOICE-FIXTURE-TWO",
                        movement_coverage=["discovery_part"],
                        provisional_load={
                            "discovery_part": 1,
                            "private_defense_part": 0,
                            "mindwars_part": 0,
                            "aftermath_coda": 0,
                            "total": 1,
                        },
                    ),
                ),
            ),
        ),
        planning_document(
            "planning/motif-ledger.md",
            title="Motif Ledger",
            blocks=(("MotifEvent", motif_event()),),
        ),
        planning_document(
            "planning/canon-bible.md",
            title="Canon Bible",
            blocks=(("TimelineEntry", timeline_entry(chapter_numbers=[1, 2])),),
        ),
    )


# The allowlisted record sources, mirroring the checker's own constant. Kept here
# so a fixture can compose a complete, conforming reference set without a test
# restating the list.
RECORD_SOURCE_TITLES: Mapping[str, str] = {
    "planning/arc-outline.md": "Arc Outline",
    "planning/canon-bible.md": "Canon Bible",
    "planning/pov-roster.md": "POV Roster",
    "planning/voice-briefs.md": "Voice Briefs",
    "planning/motif-ledger.md": "Motif Ledger",
}


def reference_planning_documents(
    *,
    arc_entries: Optional[Sequence[Mapping[str, Any]]] = None,
    timeline_entries: Optional[Sequence[Mapping[str, Any]]] = None,
    pov_profiles: Optional[Sequence[Mapping[str, Any]]] = None,
    voice_briefs: Optional[Sequence[Mapping[str, Any]]] = None,
    motif_events: Optional[Sequence[Mapping[str, Any]]] = None,
    literal_phrase_constraints: Optional[Sequence[Mapping[str, Any]]] = None,
    cross_cuts: Optional[Sequence[Mapping[str, Any]]] = None,
    novel_extensions: Optional[Sequence[Mapping[str, Any]]] = None,
    extra_blocks: Optional[Mapping[str, Sequence[Tuple[str, Any]]]] = None,
    as_arrays: bool = False,
) -> Tuple[PlanningDocument, ...]:
    """Compose all five allowlisted record sources as a conforming reference set.

    Every argument defaults to a minimal set that resolves cleanly: one chapter,
    one Timeline entry, one POV profile with its one-to-one Voice Brief, and one
    Motif Event assigned to that chapter. Pass `as_arrays=True` to emit each
    record type as one JSON array inside a single fence, which is how the real
    planning documents store most of their records.

    This is a thin composer over the record builders, not a second
    implementation, and it deliberately omits `record-schemas.md`: that document
    holds illustrative example records with no continuity authority.
    """

    if arc_entries is None:
        arc_entries = [
            arc_entry(
                chapter=1,
                timeline_id="TL-FIXTURE-001",
                pov_id="POV-MARA",
                motif_events=["MOT-FIXTURE-01"],
            )
        ]
    if timeline_entries is None:
        timeline_entries = [timeline_entry(timeline_id="TL-FIXTURE-001")]
    if pov_profiles is None:
        pov_profiles = [pov_profile()]
    if voice_briefs is None:
        voice_briefs = [voice_brief()]
    if motif_events is None:
        motif_events = [motif_event(motif_event_id="MOT-FIXTURE-01", planned_chapter=1)]

    grouped: Dict[str, List[Tuple[str, Any]]] = {}

    def _add(relative_path: str, record_type: str, records: Sequence[Any]) -> None:
        if not records:
            return
        blocks = grouped.setdefault(relative_path, [])
        if as_arrays:
            blocks.append((record_type, [dict(record) for record in records]))
        else:
            blocks.extend((record_type, dict(record)) for record in records)

    _add("planning/arc-outline.md", "ArcEntry", arc_entries)
    _add("planning/arc-outline.md", "CrossCut", cross_cuts or ())
    _add("planning/canon-bible.md", "TimelineEntry", timeline_entries)
    _add("planning/canon-bible.md", "NovelExtension", novel_extensions or ())
    _add("planning/pov-roster.md", "POVProfile", pov_profiles)
    _add("planning/voice-briefs.md", "VoiceBrief", voice_briefs)
    _add("planning/motif-ledger.md", "MotifEvent", motif_events)
    _add(
        "planning/motif-ledger.md",
        "LiteralPhraseConstraint",
        literal_phrase_constraints or (),
    )

    for relative_path, blocks in (extra_blocks or {}).items():
        grouped.setdefault(relative_path, []).extend(blocks)

    return tuple(
        planning_document(
            relative_path,
            title=RECORD_SOURCE_TITLES.get(relative_path),
            blocks=tuple(grouped.get(relative_path, ())),
        )
        for relative_path in RECORD_SOURCE_TITLES
    )


# ---------------------------------------------------------------------------
# The eight-chapter Calibration_Batch
# ---------------------------------------------------------------------------

# The design fixes the Calibration_Batch as chapters 1–5 plus three
# nonconsecutive representative chapters, and fixes which Motif_Events three of
# them carry.
CALIBRATION_CHAPTERS: Tuple[int, ...] = (1, 2, 3, 4, 5, 73, 118, 124)
CALIBRATION_MOVEMENTS: Mapping[int, str] = {
    1: "discovery_part",
    2: "discovery_part",
    3: "discovery_part",
    4: "discovery_part",
    5: "discovery_part",
    73: "mindwars_part",
    118: "aftermath_coda",
    124: "aftermath_coda",
}
CALIBRATION_MOTIFS: Mapping[int, Tuple[str, ...]] = {
    73: ("MOT-YES-01",),
    118: ("MOT-KETTLE-01",),
    124: ("MOT-COME-04", "MOT-KETTLE-02"),
}
DID_I_SAY_YES = "Did I say yes?"
DID_I_SAY_YES_CONSTRAINT_ID = "LPC-DID-I-SAY-YES"
DID_I_SAY_YES_DIAGNOSTIC = "LITERAL_DID_I_SAY_YES_SCOPE"

# `RESOLVED_MOTIF_MAPPINGS` in the checker fixes each calibration Motif_Event's
# family, movement, chapter, and representation mode, so the fixture must match
# it exactly rather than reusing one generic default.
_CALIBRATION_MOTIF_RECORDS: Mapping[str, Mapping[str, Any]] = {
    "MOT-YES-01": {
        "family": "authorization question",
        "movement": "mindwars_part",
        "planned_chapter": 73,
        "representation_mode": "literal",
        "literal_constraint_id": DID_I_SAY_YES_CONSTRAINT_ID,
    },
    "MOT-KETTLE-01": {
        "family": "kettle",
        "movement": "aftermath_coda",
        "planned_chapter": 118,
        "representation_mode": "image",
    },
    "MOT-COME-04": {
        "family": "come in",
        "movement": "aftermath_coda",
        "planned_chapter": 124,
        "representation_mode": "action",
    },
    "MOT-KETTLE-02": {
        "family": "kettle",
        "movement": "aftermath_coda",
        "planned_chapter": 124,
        "representation_mode": "action",
    },
}


def calibration_motif_events(
    chapters: Sequence[int] = CALIBRATION_CHAPTERS,
) -> Tuple[Dict[str, Any], ...]:
    """The `MotifEvent` records the requested calibration chapters require."""

    wanted: List[str] = []
    for chapter in chapters:
        for motif_event_id in CALIBRATION_MOTIFS.get(chapter, ()):
            if motif_event_id not in wanted:
                wanted.append(motif_event_id)
    return tuple(
        motif_event(
            motif_event_id=motif_event_id,
            **_CALIBRATION_MOTIF_RECORDS[motif_event_id]
        )
        for motif_event_id in wanted
    )


def did_i_say_yes_constraint(**options: Any) -> Dict[str, Any]:
    """The ledgered `Did I say yes?` Literal_Phrase_Constraint."""

    values: Dict[str, Any] = {
        "constraint_id": DID_I_SAY_YES_CONSTRAINT_ID,
        "motif_event_id": "MOT-YES-01",
        "exact_phrase": DID_I_SAY_YES,
        "allowed_movements": ["mindwars_part"],
        "diagnostic_code": DID_I_SAY_YES_DIAGNOSTIC,
    }
    values.update(options)
    return literal_phrase_constraint(**values)


def calibration_workspace(
    base: Path,
    *,
    chapters: Sequence[int] = CALIBRATION_CHAPTERS,
    prose_words: int = 880,
    chapter_overrides: Optional[Mapping[int, Mapping[str, Any]]] = None,
    entry_overrides: Optional[Mapping[int, Mapping[str, Any]]] = None,
    extra_planning: Optional[Mapping[str, Sequence[Tuple[str, Any]]]] = None,
    **workspace_options: Any,
) -> SyntheticWorkspace:
    """Build the complete pre-baseline Calibration_Batch workspace.

    Every requested chapter gets a conforming Chapter_File, a matching ArcEntry,
    and its own TimelineEntry, and chapters 73, 118, and 124 carry the fixed
    Motif_Events the design assigns them. Chapter 73's Prose_Body contains the
    ledgered `Did I say yes?` phrase, which is legal inside the Mindwars movement.

    `chapter_overrides` and `entry_overrides` pass keyword options through to
    `chapter_fixture` and `arc_entry` for one chapter, so a test can inject
    exactly one violation into an otherwise clean batch.
    """

    chapter_overrides = chapter_overrides or {}
    entry_overrides = entry_overrides or {}

    fixtures: List[ChapterFixture] = []
    entries: List[Dict[str, Any]] = []
    timelines: List[Dict[str, Any]] = []

    for chapter in chapters:
        movement = CALIBRATION_MOVEMENTS[chapter]
        slug = "calibration-{0:03d}".format(chapter)
        motifs = CALIBRATION_MOTIFS.get(chapter, ())
        prefix = DID_I_SAY_YES + "\n" if chapter == 73 else ""
        prose = prefix + prose_of_length(prose_words)
        timeline_id = "TL-CALIBRATION-{0:03d}".format(chapter)

        fixtures.append(
            chapter_fixture(
                chapter=chapter,
                movement=movement,
                slug=slug,
                prose=prose,
                timeline_id=timeline_id,
                motif_events=motifs,
                **dict(chapter_overrides.get(chapter, {}))
            )
        )
        entries.append(
            arc_entry(
                chapter=chapter,
                movement=movement,
                slug=slug,
                timeline_id=timeline_id,
                motif_events=motifs,
                estimated_words=count_prose_words(prose),
                calibration_selected=True,
                representative_purpose=(
                    "Synthetic representative calibration purpose."
                    if chapter > 5
                    else None
                ),
                **dict(entry_overrides.get(chapter, {}))
            )
        )
        timelines.append(
            timeline_entry(timeline_id=timeline_id, chapter_numbers=[chapter])
        )

    planning = reference_planning_documents(
        arc_entries=entries,
        timeline_entries=timelines,
        motif_events=list(calibration_motif_events(chapters)),
        literal_phrase_constraints=(
            [did_i_say_yes_constraint()] if 73 in tuple(chapters) else []
        ),
        extra_blocks=extra_planning,
    )
    return build_workspace(
        base, planning=planning, chapters=fixtures, **workspace_options
    )


# ---------------------------------------------------------------------------
# Whole-book record builders (task 8.9)
# ---------------------------------------------------------------------------

CANON_SOURCE_PATHS: Tuple[str, ...] = (
    "songs/Case Zero.md",
    "songs/Faraday.md",
    "songs/The Final Frontier.md",
    "songs/The Radius.md",
    "songs/The Synaptic Frontier.md",
)
EXCLUDED_CANON_SOURCE_PATH = "songs/One-Time Pad.md"


def canon_fact(
    *,
    canon_id: str = "CF-FIXTURE-001",
    authority_basis: str = "author-decision",
    source_path: str = "planning/decisions.md",
    source_location: str = "DEC-FIXTURE",
    source_material_class: Optional[str] = None,
    adopted_by: Optional[Mapping[str, Any]] = None,
    statement: str = "A synthetic fixture canon proposition.",
    first_person_testimony: bool = False,
    speaker: Optional[str] = None,
    attribution: Optional[str] = None,
    epistemic_limitation: Optional[str] = None,
    truth_scope: Optional[str] = None,
    binding_implications: Optional[Sequence[str]] = None,
    protected_ambiguities: Optional[Sequence[str]] = None,
    protected_wording: Optional[str] = None,
    affected_timeline_ids: Optional[Sequence[str]] = None,
    affected_chapters: Optional[Sequence[int]] = None,
    supporting_advisory_citations: Optional[Sequence[Mapping[str, Any]]] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build one conforming `CanonFact` record.

    `source_material_class` and `truth_scope` default to the values the declared
    authority basis and testimony flag require, so a conforming record needs no
    bookkeeping from the caller. A test that wants an authority-matrix violation
    sets them explicitly, which keeps the violation visible at the call site.
    """

    if source_material_class is None:
        source_material_class = (
            authority_basis if authority_basis != "ratified-note" else "production-note"
        )
    if truth_scope is None:
        if first_person_testimony:
            truth_scope = "attributed-testimony"
        elif authority_basis == "ratified-note":
            truth_scope = "ratified-proposition"
        else:
            truth_scope = "authoritative-proposition"
    if first_person_testimony:
        speaker = speaker if speaker is not None else "CHAR-002"
        attribution = (
            attribution
            if attribution is not None
            else "Binding as the speaker's own first-person account."
        )
        epistemic_limitation = (
            epistemic_limitation
            if epistemic_limitation is not None
            else "The account does not prove causation and is not omniscient."
        )
    if authority_basis == "ratified-note" and adopted_by is None:
        adopted_by = {
            "authority_type": "author-decision",
            "authority_id": "DEC-FIXTURE",
            "source_path": "planning/decisions.md",
            "source_location": "DEC-FIXTURE adoption clause",
        }

    record: Dict[str, Any] = {
        "canon_id": canon_id,
        "authority_basis": authority_basis,
        "source_path": source_path,
        "source_location": source_location,
        "source_material_class": source_material_class,
        "adopted_by": dict(adopted_by) if adopted_by is not None else None,
        "statement": statement,
        "first_person_testimony": first_person_testimony,
        "speaker": speaker,
        "attribution": attribution,
        "epistemic_limitation": epistemic_limitation,
        "truth_scope": truth_scope,
        "binding_implications": list(
            binding_implications or ["A synthetic fixture binding implication."]
        ),
        "protected_ambiguities": list(protected_ambiguities or []),
        "protected_wording": protected_wording,
        "affected_timeline_ids": list(affected_timeline_ids or []),
        "affected_chapters": list(affected_chapters or []),
        "supporting_advisory_citations": [
            dict(item) for item in (supporting_advisory_citations or [])
        ],
    }
    return _finish_record(record, overrides, drop_keys)


def advisory_citation(
    *,
    source_path: str = "songs/Case Zero.md",
    source_location: str = "Production Notes: carried-motif analysis",
    material_class: str = "production-note",
    classification: str = "advisory-non-story",
    note: str = "Advisory only; contributes no binding implication.",
) -> Dict[str, Any]:
    """One conforming `supporting_advisory_citations` member."""

    return {
        "source_path": source_path,
        "source_location": source_location,
        "material_class": material_class,
        "classification": classification,
        "note": note,
    }


def reveal(
    *,
    reveal_id: str = "REV-FIXTURE-001",
    fact_id: str = "FACT-FIXTURE-001",
    truth_status: str = "unresolved",
    knowers: Optional[Sequence[str]] = None,
    reveal_owner: Optional[str] = None,
    reader_release_chapter: Optional[int] = None,
    withholding_basis: str = "A synthetic fixture withholding basis.",
    payoff_window: Optional[Sequence[int]] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build one `Reveal` record, defaulting to the unresolved provenance shape."""

    record: Dict[str, Any] = {
        "reveal_id": reveal_id,
        "fact_id": fact_id,
        "truth_status": truth_status,
        "knowers": list(knowers or []),
        "reveal_owner": reveal_owner,
        "reader_release_chapter": reader_release_chapter,
        "withholding_basis": withholding_basis,
        "payoff_window": list(payoff_window) if payoff_window is not None else None,
    }
    return _finish_record(record, overrides, drop_keys)


def gate_result(
    *,
    gate_result_id: str = "GATE-FIXTURE-001",
    gate_type: str = "chapter-local",
    chapter_numbers: Optional[Sequence[int]] = None,
    documents: Optional[Sequence[str]] = None,
    description: str = "A synthetic fixture gate scope.",
    prerequisite_state: str = "complete",
    objective_diagnostic_ids: Optional[Sequence[str]] = None,
    editorial_finding_ids: Optional[Sequence[str]] = None,
    result: str = "pass",
    checker_exit_status: Optional[int] = 0,
    timestamp: str = "2026-09-12T00:00:00Z",
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build one conforming `GateResult` record.

    `checker_exit_status` is passed through exactly as given, including `None`,
    so a test can build both the editorial null and a disagreeing objective
    status. It is not derived from `result`, because the disagreement between the
    two is itself one of the things the checker reports.
    """

    record: Dict[str, Any] = {
        "gate_result_id": gate_result_id,
        "gate_type": gate_type,
        "scope": {
            "chapter_numbers": list(chapter_numbers or []),
            "documents": list(documents or []),
            "description": description,
        },
        "prerequisite_state": prerequisite_state,
        "objective_diagnostic_ids": list(objective_diagnostic_ids or []),
        "editorial_finding_ids": list(editorial_finding_ids or []),
        "result": result,
        "checker_exit_status": checker_exit_status,
        "timestamp": timestamp,
    }
    return _finish_record(record, overrides, drop_keys)


def editorial_gate_result(**options: Any) -> Dict[str, Any]:
    """A passing final editorial `GateResult`, whose exit status is null."""

    options.setdefault("gate_result_id", "GATE-FIXTURE-EDITORIAL")
    options.setdefault("gate_type", "editorial")
    options.setdefault("checker_exit_status", None)
    return gate_result(**options)


def editorial_finding(
    *,
    editorial_finding_id: str = "FIND-FIXTURE-001",
    scope: str = "chapter",
    chapter_numbers: Optional[Sequence[int]] = None,
    batch_id: Optional[str] = None,
    criterion: str = "Voice_Brief fidelity",
    prose_locations: Optional[Sequence[Mapping[str, Any]]] = None,
    finding: str = "pass",
    rationale: str = "A synthetic fixture human rationale.",
    requested_action: Optional[str] = None,
    reviewer: str = "Fixture Reviewer",
    reviewed_at: str = "2026-09-12T00:00:00Z",
    resolution: Optional[Mapping[str, Any]] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build one conforming `EditorialFinding` record.

    Human craft judgment lives only here. No checker check consumes `finding`,
    `rationale`, or `criterion` as a craft verdict; the record exists so gate
    references resolve and so the two independent final gates can be exercised.
    """

    record: Dict[str, Any] = {
        "editorial_finding_id": editorial_finding_id,
        "scope": scope,
        "chapter_numbers": list(chapter_numbers or [1]),
        "batch_id": batch_id,
        "criterion": criterion,
        "prose_locations": [dict(item) for item in (prose_locations or [])]
        or [
            {
                "path": chapter_relative_path("discovery_part", 1, "synthetic-fixture"),
                "start_line": 1,
                "end_line": 2,
                "note": "Representative synthetic location.",
            }
        ],
        "finding": finding,
        "rationale": rationale,
        "requested_action": requested_action,
        "reviewer": reviewer,
        "reviewed_at": reviewed_at,
        "resolution": dict(resolution) if resolution is not None else None,
    }
    return _finish_record(record, overrides, drop_keys)


def baseline(
    *,
    baseline_id: str = "BASELINE-FIXTURE-001",
    state: str = "provisional",
    provisional_arc_complete: bool = True,
    resolved_decision_refs: Optional[Sequence[str]] = None,
    calibration_chapters: Optional[Sequence[int]] = None,
    minimal_checker_gate_result_id: Optional[str] = None,
    calibration_finding_ids: Optional[Sequence[str]] = None,
    baseline_revision_pass: Optional[Mapping[str, Any]] = None,
    full_suite_gate_result_id: Optional[str] = None,
    author_approval: Optional[Mapping[str, Any]] = None,
    final_targets: Optional[Mapping[str, int]] = None,
    out_of_range_rationale: Optional[str] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build one `Baseline` record, provisional by default."""

    record: Dict[str, Any] = {
        "baseline_id": baseline_id,
        "state": state,
        "provisional_arc_complete": provisional_arc_complete,
        "resolved_decision_refs": list(resolved_decision_refs or ["DEC-FIXTURE"]),
        "calibration_chapters": list(
            calibration_chapters if calibration_chapters is not None
            else CALIBRATION_CHAPTERS
        ),
        "minimal_checker_gate_result_id": minimal_checker_gate_result_id,
        "calibration_finding_ids": list(calibration_finding_ids or []),
        "baseline_revision_pass": copy.deepcopy(baseline_revision_pass),
        "full_suite_gate_result_id": full_suite_gate_result_id,
        "author_approval": dict(author_approval)
        if author_approval is not None
        else None,
        "final_targets": dict(final_targets) if final_targets is not None else None,
        "out_of_range_rationale": out_of_range_rationale,
    }
    return _finish_record(record, overrides, drop_keys)


def author_approval(
    *,
    approved_by: str = "Fixture Author",
    approved_at: str = "2026-09-12T00:00:00Z",
    approval_record: str = "planning/arc-outline.md#baseline-approval",
) -> Dict[str, Any]:
    """One conforming `author_approval` / `approval` object."""

    return {
        "approved_by": approved_by,
        "approved_at": approved_at,
        "approval_record": approval_record,
    }


def revision_disposition(
    *,
    editorial_finding_id: str = "FIND-FIXTURE-001",
    outcome: str = "no-change-rationale",
    arc_change_id: Optional[str] = None,
    rationale: str = "A synthetic fixture no-change rationale.",
) -> Dict[str, Any]:
    """One `baseline_revision_pass.dispositions` member."""

    return {
        "editorial_finding_id": editorial_finding_id,
        "outcome": outcome,
        "arc_change_id": arc_change_id,
        "rationale": rationale,
    }


def baseline_revision_pass(
    *,
    performed_at: str = "2026-09-12T00:00:00Z",
    dispositions: Optional[Sequence[Mapping[str, Any]]] = None,
) -> Dict[str, Any]:
    """One conforming `baseline_revision_pass` object."""

    return {
        "performed_at": performed_at,
        "dispositions": [dict(item) for item in (dispositions or [])],
    }


def synchronization_obligation(
    *,
    document: str = "planning/arc-outline.md",
    required_change: str = "A synthetic fixture required change.",
    status: str = "pending",
    evidence_ref: Optional[str] = None,
) -> Dict[str, Any]:
    """One `synchronization_obligations` member."""

    return {
        "document": document,
        "required_change": required_change,
        "status": status,
        "evidence_ref": evidence_ref,
    }


def arc_change(
    *,
    arc_change_id: str = "ARC-CHANGE-FIXTURE-001",
    date: str = "2026-09-12",
    prior_state: Optional[Mapping[str, Any]] = None,
    revised_state: Optional[Mapping[str, Any]] = None,
    rationale: str = "A synthetic fixture change rationale.",
    affected_chapters: Optional[Sequence[int]] = None,
    affected_documents: Optional[Sequence[str]] = None,
    synchronization_obligations: Optional[Sequence[Mapping[str, Any]]] = None,
    approval: Optional[Mapping[str, Any]] = None,
    status: str = "proposed",
    completed_at: Optional[str] = None,
    overrides: Optional[Mapping[str, Any]] = None,
    drop_keys: Sequence[str] = (),
) -> Dict[str, Any]:
    """Build one `ArcChange` record.

    Defaults to a `proposed` change with one pending obligation covering its one
    affected document, which is the atomic shape a complete change must reach.
    A caller building a `complete` change supplies completed obligations with
    evidence, an approval, and a completion time.
    """

    documents = list(affected_documents or ["planning/arc-outline.md"])
    if synchronization_obligations is None:
        synchronization_obligations = [
            synchronization_obligation(document=document) for document in documents
        ]
    record: Dict[str, Any] = {
        "arc_change_id": arc_change_id,
        "date": date,
        "prior_state": dict(prior_state) if prior_state is not None
        else {"chapter": 1, "status": "approved"},
        "revised_state": dict(revised_state) if revised_state is not None
        else {"chapter": 1, "status": "revised"},
        "rationale": rationale,
        "affected_chapters": list(affected_chapters if affected_chapters is not None
                                  else [1]),
        "affected_documents": documents,
        "synchronization_obligations": [
            dict(item) for item in synchronization_obligations
        ],
        "approval": dict(approval) if approval is not None else None,
        "status": status,
        "completed_at": completed_at,
    }
    return _finish_record(record, overrides, drop_keys)


def completed_arc_change(**options: Any) -> Dict[str, Any]:
    """An atomic `complete` ArcChange: every obligation done, with evidence."""

    documents = list(options.pop("affected_documents", ["planning/arc-outline.md"]))
    options.setdefault(
        "synchronization_obligations",
        [
            synchronization_obligation(
                document=document,
                status="complete",
                evidence_ref="{0}#synchronized".format(document),
            )
            for document in documents
        ],
    )
    options.setdefault("approval", author_approval())
    options.setdefault("status", "complete")
    options.setdefault("completed_at", "2026-09-12T00:00:00Z")
    return arc_change(affected_documents=documents, **options)


# ---------------------------------------------------------------------------
# The complete 128-chapter manuscript fixture (task 8.9)
# ---------------------------------------------------------------------------

# The design's provisional allocation: 29/32/51/16 chapters, and the per-POV
# per-movement load matrix summing to the 56/32/33/7 vector.
MANUSCRIPT_MOVEMENT_CHAPTERS: Mapping[str, int] = {
    "discovery_part": 29,
    "private_defense_part": 32,
    "mindwars_part": 51,
    "aftermath_coda": 16,
}
MANUSCRIPT_POV_LOAD: Mapping[str, Mapping[str, int]] = {
    "POV-MARA": {
        "discovery_part": 14,
        "private_defense_part": 14,
        "mindwars_part": 21,
        "aftermath_coda": 7,
        "total": 56,
    },
    "POV-NIA": {
        "discovery_part": 9,
        "private_defense_part": 8,
        "mindwars_part": 14,
        "aftermath_coda": 1,
        "total": 32,
    },
    "POV-JULIAN": {
        "discovery_part": 6,
        "private_defense_part": 10,
        "mindwars_part": 16,
        "aftermath_coda": 1,
        "total": 33,
    },
    "POV-SAFIYA": {
        "discovery_part": 0,
        "private_defense_part": 0,
        "mindwars_part": 0,
        "aftermath_coda": 7,
        "total": 7,
    },
}
MANUSCRIPT_POV_CHARACTERS: Mapping[str, str] = {
    "POV-MARA": "CHAR-001",
    "POV-NIA": "CHAR-002",
    "POV-JULIAN": "CHAR-003",
    "POV-SAFIYA": "CHAR-004",
}
MANUSCRIPT_ANCHOR_POV = "POV-MARA"

# Requirement 15.1's mandatory Fluent_Pairing ranges, and the chapter each
# synthetic beat is assigned to.
FLUENT_PAIRING_RANGES: Tuple[Tuple[int, int], ...] = (
    (36, 42),
    (56, 61),
    (70, 77),
    (78, 93),
    (94, 108),
)

WHOSE_WAS_THAT = "Whose was that?"
FINAL_PASSAGE_MARKER = "<!-- final-passage:start -->"
WHOSE_WAS_THAT_CONSTRAINT_ID = "LPC-WHOSE-WAS-THAT"
WHOSE_WAS_THAT_DIAGNOSTIC = "LITERAL_WHOSE_WAS_THAT_PLACEMENT"

CONFORMING_FRONT_MATTER = """# Synthetic Manuscript

A novel by Fixture Author

Novel prose copyright 2026 Fixture Author. All rights reserved.

## Source acknowledgment

This novel grows from five source songs: *The Synaptic Frontier*, *Faraday*,
*The Final Frontier*, *The Radius*, and *Case Zero*.
"""


def manuscript_movement_for_chapter(
    chapter: int, *, allocation: Optional[Mapping[str, int]] = None
) -> str:
    """The movement a chapter belongs to under a contiguous block allocation."""

    counts = allocation or MANUSCRIPT_MOVEMENT_CHAPTERS
    upper = 0
    for movement in MOVEMENTS:
        upper += int(counts.get(movement, 0))
        if chapter <= upper:
            return movement
    raise FixtureError(
        "chapter {0} is past the {1}-chapter allocation".format(chapter, upper)
    )


def manuscript_pov_sequence(
    *,
    allocation: Optional[Mapping[str, int]] = None,
    load: Optional[Mapping[str, Mapping[str, int]]] = None,
) -> Tuple[str, ...]:
    """Assign a POV_ID to every chapter, honoring the load matrix and run caps.

    Greedy anti-clustering: at each position take the POV with the most chapters
    still owed in this movement that is not the previous chapter's POV. That
    yields runs of length one wherever the counts allow, which keeps the fixture
    inside both Same_POV_Run bounds without the fixture having to know them.
    Property 8 generates its own run sequences; this only needs to be valid.
    """

    counts = allocation or MANUSCRIPT_MOVEMENT_CHAPTERS
    matrix = load or MANUSCRIPT_POV_LOAD
    sequence: List[str] = []
    previous: Optional[str] = None

    for movement in MOVEMENTS:
        remaining = {
            pov_id: int(values.get(movement, 0))
            for pov_id, values in matrix.items()
            if int(values.get(movement, 0)) > 0
        }
        planned = int(counts.get(movement, 0))
        if sum(remaining.values()) != planned:
            raise FixtureError(
                "{0} load sums to {1}, not the planned {2}".format(
                    movement, sum(remaining.values()), planned
                )
            )
        for _ in range(planned):
            candidates = sorted(
                (owed, pov_id)
                for pov_id, owed in remaining.items()
                if owed > 0 and pov_id != previous
            )
            if not candidates:
                # Only reachable when one POV owns every remaining chapter in the
                # movement. Taking it is still correct; the run cap is asserted by
                # the checker, not assumed by the fixture.
                candidates = sorted(
                    (owed, pov_id) for pov_id, owed in remaining.items() if owed > 0
                )
            _owed, chosen = candidates[-1]
            remaining[chosen] -= 1
            sequence.append(chosen)
            previous = chosen

    return tuple(sequence)


def manuscript_motif_events() -> Tuple[Dict[str, Any], ...]:
    """The design's whole-book Motif_Ledger, transcribed record by record.

    Seven closed families, each landing where the design places it: the two
    kettle events in the Coda (Requirement 7.12), the three Record_Progression
    events across Private Defense, Mindwars, and the Coda (Requirement 7.17),
    the three-part chain and copper progressions, and the two literal questions
    carrying their Literal_Phrase_Constraints. Transcribed from
    `planning/motif-ledger.md` rather than imported from the checker, so a
    property test measures the checker against the design and not against
    itself.
    """

    return (
        motif_event(
            motif_event_id="MOT-CHAIN-01",
            family="spectrum / wire / voice",
            movement="discovery_part",
            planned_chapter=13,
            representation_mode="image",
        ),
        motif_event(
            motif_event_id="MOT-CHAIN-02",
            family="spectrum / wire / voice",
            movement="private_defense_part",
            planned_chapter=45,
            representation_mode="image",
        ),
        motif_event(
            motif_event_id="MOT-CHAIN-03",
            family="spectrum / wire / voice",
            movement="aftermath_coda",
            planned_chapter=127,
            representation_mode="action",
        ),
        motif_event(
            motif_event_id="MOT-COPPER-01",
            family="copper / quiet",
            movement="private_defense_part",
            planned_chapter=31,
            representation_mode="image",
        ),
        motif_event(
            motif_event_id="MOT-COPPER-02",
            family="copper / quiet",
            movement="mindwars_part",
            planned_chapter=70,
            representation_mode="image",
        ),
        motif_event(
            motif_event_id="MOT-COPPER-03",
            family="copper / quiet",
            movement="aftermath_coda",
            planned_chapter=124,
            representation_mode="image",
        ),
        motif_event(
            motif_event_id="MOT-COME-01",
            family="come in",
            movement="discovery_part",
            planned_chapter=16,
            representation_mode="adapted",
        ),
        motif_event(
            motif_event_id="MOT-COME-02",
            family="come in",
            movement="private_defense_part",
            planned_chapter=61,
            representation_mode="scene-structure",
        ),
        motif_event(
            motif_event_id="MOT-COME-03",
            family="come in",
            movement="mindwars_part",
            planned_chapter=74,
            representation_mode="action",
        ),
        motif_event(
            motif_event_id="MOT-COME-04",
            family="come in",
            movement="aftermath_coda",
            planned_chapter=124,
            representation_mode="action",
        ),
        motif_event(
            motif_event_id="MOT-KNOCK-01",
            family="knock / wait",
            movement="mindwars_part",
            planned_chapter=73,
            representation_mode="action",
        ),
        motif_event(
            motif_event_id="MOT-KNOCK-02",
            family="knock / wait",
            movement="aftermath_coda",
            planned_chapter=116,
            representation_mode="action",
        ),
        motif_event(
            motif_event_id="MOT-KNOCK-03",
            family="knock / wait",
            movement="aftermath_coda",
            planned_chapter=128,
            representation_mode="action",
        ),
        motif_event(
            motif_event_id="MOT-KETTLE-01",
            family="kettle",
            movement="aftermath_coda",
            planned_chapter=118,
            representation_mode="image",
        ),
        motif_event(
            motif_event_id="MOT-KETTLE-02",
            family="kettle",
            movement="aftermath_coda",
            planned_chapter=124,
            representation_mode="action",
        ),
        motif_event(
            motif_event_id="MOT-RADIUS-01",
            family="silence has a radius",
            movement="mindwars_part",
            planned_chapter=101,
            representation_mode="adapted",
        ),
        motif_event(
            motif_event_id="MOT-RADIUS-02",
            family="silence has a radius",
            movement="aftermath_coda",
            planned_chapter=120,
            representation_mode="adapted",
        ),
        motif_event(
            motif_event_id="MOT-RECORD-01",
            family="record progression",
            movement="private_defense_part",
            planned_chapter=51,
            representation_mode="literal",
        ),
        motif_event(
            motif_event_id="MOT-RECORD-02",
            family="record progression",
            movement="mindwars_part",
            planned_chapter=109,
            representation_mode="adapted",
        ),
        motif_event(
            motif_event_id="MOT-RECORD-03",
            family="record progression",
            movement="aftermath_coda",
            planned_chapter=128,
            representation_mode="adapted",
        ),
        motif_event(
            motif_event_id="MOT-YES-01",
            family="authorization question",
            movement="mindwars_part",
            planned_chapter=73,
            representation_mode="literal",
            literal_constraint_id=DID_I_SAY_YES_CONSTRAINT_ID,
        ),
        motif_event(
            motif_event_id="MOT-WHOSE-01",
            family="provenance question",
            movement="aftermath_coda",
            planned_chapter=128,
            representation_mode="literal",
            literal_constraint_id=WHOSE_WAS_THAT_CONSTRAINT_ID,
        ),
    )


MANUSCRIPT_MOTIF_ASSIGNMENTS: Mapping[int, Tuple[str, ...]] = {
    13: ("MOT-CHAIN-01",),
    16: ("MOT-COME-01",),
    31: ("MOT-COPPER-01",),
    45: ("MOT-CHAIN-02",),
    51: ("MOT-RECORD-01",),
    61: ("MOT-COME-02",),
    70: ("MOT-COPPER-02",),
    73: ("MOT-KNOCK-01", "MOT-YES-01"),
    74: ("MOT-COME-03",),
    101: ("MOT-RADIUS-01",),
    109: ("MOT-RECORD-02",),
    116: ("MOT-KNOCK-02",),
    118: ("MOT-KETTLE-01",),
    120: ("MOT-RADIUS-02",),
    124: ("MOT-COPPER-03", "MOT-COME-04", "MOT-KETTLE-02"),
    127: ("MOT-CHAIN-03",),
    128: ("MOT-KNOCK-03", "MOT-RECORD-03", "MOT-WHOSE-01"),
}

def whose_was_that_constraint(
    *, final_chapter: int = 128, filename: Optional[str] = None, **options: Any
) -> Dict[str, Any]:
    """The terminal `Whose was that?` rule: exactly twice inside the span."""

    path = (
        filename
        if filename is not None
        else chapter_relative_path(
            "aftermath_coda", final_chapter, "chapter-{0:03d}".format(final_chapter)
        )
    )
    options.setdefault("constraint_id", WHOSE_WAS_THAT_CONSTRAINT_ID)
    options.setdefault("motif_event_id", "MOT-WHOSE-01")
    options.setdefault("exact_phrase", WHOSE_WAS_THAT)
    options.setdefault("allowed_movements", ("aftermath_coda",))
    options.setdefault("allowed_chapters", (final_chapter,))
    options.setdefault("allowed_files", (path,))
    options.setdefault("exact_in_scope", 2)
    options.setdefault("maximum_outside_scope", 0)
    options.setdefault("diagnostic_code", WHOSE_WAS_THAT_DIAGNOSTIC)
    options.setdefault(
        "allowed_span",
        {
            "span_id": "SPAN-FINAL-PASSAGE",
            "chapter": final_chapter,
            "start_boundary": {"kind": "literal-marker", "value": FINAL_PASSAGE_MARKER},
            "end_boundary": {"kind": "end-of-prose", "value": None},
        },
    )
    return literal_phrase_constraint(**options)


def final_passage_prose(
    *, words: int = 700, occurrences: int = 2, marker: str = FINAL_PASSAGE_MARKER
) -> str:
    """A final-chapter Prose_Body whose declared Final_Passage holds the phrase.

    The marker is emitted once, then `occurrences` copies of the protected phrase
    follow it. The leading filler stays outside the span, which is what lets a
    test move an occurrence out of scope by changing only `occurrences`.
    """

    lead = max(words - occurrences * len(WHOSE_WAS_THAT.split()), 1)
    tail = " ".join([WHOSE_WAS_THAT] * occurrences)
    return prose_of_length(lead) + marker + "\n" + tail + "\n"


def fluent_pairing_timeline_entries(
    *, ranges: Sequence[Tuple[int, int]] = FLUENT_PAIRING_RANGES
) -> Tuple[Dict[str, Any], ...]:
    """One `PAIR` TimelineEntry per mandatory Fluent_Pairing range."""

    entries: List[Dict[str, Any]] = []
    for start, end in ranges:
        entries.append(
            timeline_entry(
                timeline_id="TL-PAIR-RANGE-{0:03d}".format(start),
                chapter_numbers=[start],
                state=technical_state(
                    mode="PAIR",
                    # `bench-transmit` and `locked` are the design's vocabulary for
                    # a deliberate paired send to a person-specific address.
                    # Inventing readable-looking values would make the fixture
                    # describe a mechanism the checker does not recognize.
                    apparatus_mode="bench-transmit",
                    transmit_stage_present=True,
                    person_specific_address_state="locked",
                    pair_state=pair_state(),
                    pairing_evidence=pairing_evidence(),
                ),
            )
        )
    return tuple(entries)


def manuscript_workspace(
    base: Path,
    *,
    prose_words: int = 700,
    allocation: Optional[Mapping[str, int]] = None,
    load: Optional[Mapping[str, Mapping[str, int]]] = None,
    status: str = "final",
    approve_baseline: bool = True,
    final_targets: Optional[Mapping[str, int]] = None,
    chapter_overrides: Optional[Mapping[int, Mapping[str, Any]]] = None,
    entry_overrides: Optional[Mapping[int, Mapping[str, Any]]] = None,
    arc_changes: Optional[Sequence[Mapping[str, Any]]] = None,
    gate_results: Optional[Sequence[Mapping[str, Any]]] = None,
    editorial_findings: Optional[Sequence[Mapping[str, Any]]] = None,
    extra_planning: Optional[Mapping[str, Sequence[Tuple[str, Any]]]] = None,
    **workspace_options: Any,
) -> SyntheticWorkspace:
    """Build a complete manuscript that passes the Manuscript_Global_Gate.

    Every planned chapter gets a Chapter_File and a matching ArcEntry, the four
    movements form contiguous blocks in order, the POV loads and run caps hold,
    every chapter is `normal` so the normal share is 100 percent, the final
    chapter carries the declared Final_Passage with exactly two protected
    occurrences, and the Baseline plus both independent final gates are recorded.

    Final_Targets default to the totals this fixture actually produces, with an
    out-of-range rationale supplied automatically when those totals fall outside
    the provisional planning bands. That keeps the fixture self-consistent at any
    `prose_words`, so a test can build a fast small manuscript or the real
    provisional allocation from the same builder.

    `chapter_overrides` and `entry_overrides` inject exactly one violation into
    an otherwise clean whole book, which is how the global invariants are
    exercised one at a time.
    """

    chapter_overrides = dict(chapter_overrides or {})
    entry_overrides = dict(entry_overrides or {})
    counts = allocation or MANUSCRIPT_MOVEMENT_CHAPTERS
    total_chapters = sum(int(counts.get(movement, 0)) for movement in MOVEMENTS)
    povs = manuscript_pov_sequence(allocation=counts, load=load)
    final_chapter = total_chapters

    fixtures: List[ChapterFixture] = []
    entries: List[Dict[str, Any]] = []
    timelines: List[Dict[str, Any]] = list(fluent_pairing_timeline_entries())
    observed_total = 0

    for chapter in range(1, total_chapters + 1):
        movement = manuscript_movement_for_chapter(chapter, allocation=counts)
        slug = "chapter-{0:03d}".format(chapter)
        pov_id = povs[chapter - 1]
        motifs = MANUSCRIPT_MOTIF_ASSIGNMENTS.get(chapter, ())
        timeline_id = "TL-CHAPTER-{0:03d}".format(chapter)
        if chapter == final_chapter:
            prose = final_passage_prose(words=prose_words)
        elif chapter == 73:
            prose = DID_I_SAY_YES + "\n" + prose_of_length(prose_words)
        else:
            prose = prose_of_length(prose_words)
        observed = count_prose_words(prose)
        observed_total += observed

        # Overrides are merged rather than splatted so a test can replace a
        # keyword the builder already supplies, which is the usual way to inject
        # one violation: a wrong movement, POV_ID, or status on one chapter.
        chapter_options: Dict[str, Any] = {
            "chapter": chapter,
            "movement": movement,
            "slug": slug,
            "prose": prose,
            "pov_id": pov_id,
            "timeline_id": timeline_id,
            "motif_events": motifs,
            "status": status,
        }
        chapter_options.update(chapter_overrides.get(chapter, {}))
        fixtures.append(chapter_fixture(**chapter_options))

        entry_options: Dict[str, Any] = {
            "chapter": chapter,
            "movement": movement,
            "slug": slug,
            "pov_id": pov_id,
            "timeline_id": timeline_id,
            "motif_events": motifs,
            "estimated_words": observed,
            "status": status,
            "calibration_selected": chapter in CALIBRATION_CHAPTERS,
            "representative_purpose": (
                "Synthetic representative calibration purpose."
                if chapter in CALIBRATION_CHAPTERS and chapter > 5
                else None
            ),
        }
        entry_options.update(entry_overrides.get(chapter, {}))
        entries.append(arc_entry(**entry_options))
        timelines.append(
            timeline_entry(timeline_id=timeline_id, chapter_numbers=[chapter])
        )

    profiles = [
        pov_profile(
            character_id=MANUSCRIPT_POV_CHARACTERS[pov_id],
            pov_id=pov_id,
            selected_name="Fixture {0}".format(pov_id.split("-")[-1].title()),
            anchor=pov_id == MANUSCRIPT_ANCHOR_POV,
            voice_brief_id="VOICE-{0}".format(pov_id.split("-")[-1]),
            movement_coverage=[
                movement
                for movement in MOVEMENTS
                if int(MANUSCRIPT_POV_LOAD[pov_id].get(movement, 0)) > 0
            ],
            provisional_load=MANUSCRIPT_POV_LOAD[pov_id],
        )
        for pov_id in MANUSCRIPT_POV_LOAD
    ]
    briefs = [
        voice_brief(
            voice_brief_id="VOICE-{0}".format(pov_id.split("-")[-1]),
            pov_id=pov_id,
            movements=[
                movement
                for movement in MOVEMENTS
                if int(MANUSCRIPT_POV_LOAD[pov_id].get(movement, 0)) > 0
            ],
        )
        for pov_id in MANUSCRIPT_POV_LOAD
    ]

    if final_targets is None:
        final_targets = {
            "chapter_count": total_chapters,
            "minimum_words": observed_total,
            "maximum_words": observed_total,
        }
    outside_provisional = not (
        120 <= int(final_targets["chapter_count"]) <= 135
        and 130000 <= int(final_targets["minimum_words"]) <= 150000
        and 130000 <= int(final_targets["maximum_words"]) <= 150000
    )

    if gate_results is None:
        gate_results = [
            gate_result(
                gate_result_id="GATE-FIXTURE-CALIBRATION",
                gate_type="calibration-objective",
            ),
            gate_result(
                gate_result_id="GATE-FIXTURE-BASELINE",
                gate_type="baseline-objective",
            ),
            gate_result(
                gate_result_id="GATE-FIXTURE-GLOBAL",
                gate_type="manuscript-global",
            ),
            editorial_gate_result(
                editorial_finding_ids=["FIND-FIXTURE-001"],
            ),
        ]
    if editorial_findings is None:
        editorial_findings = [editorial_finding(scope="manuscript")]

    baseline_record = baseline(
        state="approved" if approve_baseline else "provisional",
        minimal_checker_gate_result_id="GATE-FIXTURE-CALIBRATION"
        if approve_baseline
        else None,
        full_suite_gate_result_id="GATE-FIXTURE-BASELINE"
        if approve_baseline
        else None,
        calibration_finding_ids=["FIND-FIXTURE-001"] if approve_baseline else [],
        baseline_revision_pass=baseline_revision_pass(
            dispositions=[revision_disposition()]
        )
        if approve_baseline
        else None,
        author_approval=author_approval() if approve_baseline else None,
        final_targets=dict(final_targets) if approve_baseline else None,
        out_of_range_rationale=(
            "Synthetic fixture scale differs from the provisional planning bands."
            if approve_baseline and outside_provisional
            else None
        ),
    )

    blocks: Dict[str, List[Tuple[str, Any]]] = {
        "planning/arc-outline.md": [("Baseline", baseline_record)],
        "planning/gate-results.md": [
            ("GateResult", dict(record)) for record in gate_results
        ],
        "planning/editorial-log.md": [
            ("EditorialFinding", dict(record)) for record in editorial_findings
        ],
        "planning/arc-changes.md": [
            ("ArcChange", dict(record)) for record in (arc_changes or ())
        ],
    }
    for relative_path, extra in (extra_planning or {}).items():
        blocks.setdefault(relative_path, []).extend(extra)

    planning = list(
        reference_planning_documents(
            arc_entries=entries,
            timeline_entries=timelines,
            pov_profiles=profiles,
            voice_briefs=briefs,
            motif_events=list(manuscript_motif_events()),
            literal_phrase_constraints=[
                did_i_say_yes_constraint(),
                whose_was_that_constraint(
                    final_chapter=final_chapter,
                    filename=chapter_relative_path(
                        manuscript_movement_for_chapter(
                            final_chapter, allocation=counts
                        ),
                        final_chapter,
                        "chapter-{0:03d}".format(final_chapter),
                    ),
                ),
            ],
            extra_blocks={
                path: tuple(items)
                for path, items in blocks.items()
                if path in RECORD_SOURCE_TITLES
            },
        )
    )
    for relative_path, items in blocks.items():
        if relative_path in RECORD_SOURCE_TITLES:
            continue
        planning.append(
            planning_document(
                relative_path,
                title=relative_path.rsplit("/", 1)[-1][:-3].replace("-", " ").title(),
                blocks=tuple(items),
            )
        )

    workspace_options.setdefault("front_matter", CONFORMING_FRONT_MATTER)
    return build_workspace(
        base, planning=planning, chapters=fixtures, **workspace_options
    )


# ---------------------------------------------------------------------------
# In-memory record indexes (task 8.9)
# ---------------------------------------------------------------------------

# Records a reference in a probe is allowed to point at. Without these, a
# single-record probe reports every outbound reference as dangling and the
# property under test is drowned by the probe's own missing context.
SUPPORTING_RECORD_TYPES: Tuple[str, ...] = (
    "POVProfile",
    "VoiceBrief",
    "TimelineEntry",
    "ArcChange",
)


def supporting_records() -> Dict[str, List[Dict[str, Any]]]:
    """The minimal record set that makes an ordinary reference resolvable."""

    return {
        "POVProfile": [pov_profile()],
        "VoiceBrief": [voice_brief()],
        "TimelineEntry": [timeline_entry()],
        "ArcChange": [arc_change()],
    }


def record_index(
    *,
    supporting: bool = True,
    arc_entries: Optional[Sequence[Mapping[str, Any]]] = None,
    source: str = "planning/probe.md",
    **records: Sequence[Mapping[str, Any]]
) -> Any:
    """Build a checker `ReferenceIndex` from record payloads, without touching disk.

    Records are rendered into one synthetic planning document and read back
    through the checker's own fence parser, so a probe exercises the same parse
    path a real run does rather than a shortcut around it.

    `supporting` seeds the resolvable records an ordinary outbound reference
    points at. Pass `supporting=False` when the property under test *is* a
    dangling reference and the probe must not accidentally satisfy it.

    Returns the index only. A caller that needs the parse and index diagnostics
    should use `record_index_with_diagnostics`.
    """

    index, _diagnostics = record_index_with_diagnostics(
        supporting=supporting, arc_entries=arc_entries, source=source, **records
    )
    return index


def record_index_with_diagnostics(
    *,
    supporting: bool = True,
    arc_entries: Optional[Sequence[Mapping[str, Any]]] = None,
    source: str = "planning/probe.md",
    **records: Sequence[Mapping[str, Any]]
) -> Tuple[Any, Tuple[Any, ...]]:
    """`record_index`, plus the diagnostics parsing and indexing produced."""

    checker = load_checker()
    collected: Dict[str, List[Mapping[str, Any]]] = {}
    if supporting:
        for record_type, defaults in supporting_records().items():
            collected[record_type] = list(defaults)
    for record_type, payloads in records.items():
        collected.setdefault(record_type, [])
        collected[record_type].extend(payloads)

    blocks: List[Tuple[str, Any]] = []
    for record_type in sorted(collected):
        for payload in collected[record_type]:
            blocks.append((record_type, payload))
    document = planning_document(source, title="Probe", blocks=tuple(blocks))

    parsed, parse_diagnostics = checker.parse_planning_records(
        document.text(), source=source
    )
    grouped: Dict[str, List[Any]] = {}
    for record_type, items in parsed.items():
        grouped.setdefault(record_type, []).extend(items)

    entry_records: Tuple[Any, ...] = ()
    if arc_entries is not None:
        entry_document = planning_document(
            "planning/probe-arc.md",
            title="Probe Arc",
            blocks=tuple(("ArcEntry", entry) for entry in arc_entries),
        )
        entry_records, entry_diagnostics = checker.parse_arc_entries(
            entry_document.text(), source="planning/probe-arc.md"
        )
        parse_diagnostics = tuple(parse_diagnostics) + tuple(entry_diagnostics)
        entry_parsed, _ = checker.parse_planning_records(
            entry_document.text(),
            source="planning/probe-arc.md",
            record_types=("ArcEntry",),
        )
        grouped.setdefault("ArcEntry", []).extend(entry_parsed.get("ArcEntry", ()))

    index, index_diagnostics = checker.build_reference_index(
        grouped, sources=(source,), arc_entries=entry_records
    )
    return index, tuple(parse_diagnostics) + tuple(index_diagnostics)
