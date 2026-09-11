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
restricted nine-key Chapter_Header and the typed JSON fence contract,
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

# The nine restricted Chapter_Header keys, in the order `record-schemas.md`
# defines them. The key set is closed: no schema key, title, or discriminator.
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
    """Build the logical nine-key Chapter_Header object.

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
    if key == "hook":
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
    for exclusion in document.get("exclusions", []):
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
