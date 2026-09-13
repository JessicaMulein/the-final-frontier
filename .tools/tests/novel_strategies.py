"""Shared Hypothesis strategies for the objective manuscript checker suite.

Created by task 8.9 of the `The-Final-Frontier-novel` spec. `novel_fixtures`
builds one deterministic world; this module chooses which world to build, so the
fifteen principal property tests (tasks 8.10 through 8.24) all draw from the same
generator vocabulary instead of fifteen private ones.

Scope and honesty boundaries
----------------------------
* Every strategy composes `novel_fixtures` builders. Nothing here hand-writes a
  record shape, so a schema change lands in one place.
* A strategy named `conforming_*` yields only valid values. A strategy named
  `*_variants` yields a `Variant` carrying its own `valid` flag, which is what
  lets one property test assert both directions of a rule from a single draw.
* `Variant.valid` is the *design's* verdict, transcribed from the requirement,
  never read back from the checker. A property test that took its expectation
  from `check_novel.py` would pass no matter what the checker did.
* Nothing here imports `check_novel`. Diagnostic codes are the property test's
  business, not the generator's.

Authority: the design's "Objective Test Stack" and Correctness Properties, the
Requirements document sections cited on each strategy, and
`The Final Frontier Novel/planning/record-schemas.md` for record shape.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from hypothesis import strategies as st

import novel_fixtures as nf

# ---------------------------------------------------------------------------
# Labelled variants
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class Variant:
    """One generated world plus the design's verdict on it.

    `label` names the state the way the requirement names it, so a shrunk
    counterexample reads as a sentence rather than as a diff. `valid` is the
    design's verdict. `requirement` cites where that verdict comes from, which is
    what makes a failure actionable instead of merely red.

    `objective` is the more important field. Some states the design calls wrong
    are wrong in a way no program can see: a record that quietly contradicts the
    unnamed-geography decision, or that reads as omniscient causal proof in its
    prose, is a craft and continuity judgment belonging to a human
    `EditorialFinding`. Those variants carry `objective=False`, and the property
    they support is that the checker stays **silent** about them. Marking such a
    state `valid=False, objective=True` would ask the checker to grade prose,
    which is the one thing it must never do.
    """

    label: str
    valid: bool
    payload: Any
    requirement: str = ""
    objective: bool = True

    @property
    def expects_diagnostic(self) -> bool:
        """True only when the checker must report this state.

        An invalid-but-editorial state expects no diagnostic, because the fault
        is not machine-visible. This is the predicate a property test asserts on.
        """

        return self.objective and not self.valid

    def __str__(self) -> str:
        state = "valid" if self.valid else "malformed"
        if not self.objective:
            state += ", editorial"
        return "{0} [{1}{2}]".format(
            self.label, state, " " + self.requirement if self.requirement else ""
        )


# ---------------------------------------------------------------------------
# Identifiers, numbers, and enums
# ---------------------------------------------------------------------------

STABLE_ID_PREFIXES: Tuple[str, ...] = (
    "TL",
    "POV",
    "VOICE",
    "MOT",
    "LPC",
    "CUT",
    "EXT",
    "CF",
    "REV",
    "BASELINE",
    "ARC-CHANGE",
    "FIND",
    "GATE",
)


def stable_ids(prefix: str = "TL") -> "st.SearchStrategy[str]":
    """Stable_IDs of the documented shape: a type prefix and a stable suffix.

    Requirement 9.9 fixes only that the identifier is stable and unique, not its
    spelling, so the generator varies the suffix and never the meaning.
    """

    return st.builds(
        "{0}-GEN-{1:04d}".format,
        st.just(prefix),
        st.integers(min_value=1, max_value=9999),
    )


def chapter_numbers(
    *, minimum: int = 1, maximum: int = 128
) -> "st.SearchStrategy[int]":
    """A chapter number inside the planned sequence."""

    return st.integers(min_value=minimum, max_value=maximum)


def movements() -> "st.SearchStrategy[str]":
    """One of the four movements, in no particular order."""

    return st.sampled_from(list(nf.MOVEMENTS))


def length_classes() -> "st.SearchStrategy[str]":
    """One of the four Length_Classes."""

    return st.sampled_from(list(nf.LENGTH_CLASSES))


def chapter_statuses() -> "st.SearchStrategy[str]":
    """One of the documented Chapter_Header statuses."""

    return st.sampled_from(list(nf.CHAPTER_STATUSES))


def prose_word_counts(
    *, minimum: int = 1, maximum: int = nf.HARD_CHAPTER_MAXIMUM
) -> "st.SearchStrategy[int]":
    """A Prose_Word count anywhere inside the permitted range.

    Bounded by the hard chapter maximum rather than by a Length_Class band, so a
    draw can land on a band boundary. Property 5 (task 8.14) needs those.
    """

    return st.integers(min_value=minimum, max_value=maximum)


# The design's three Length_Class bands, by observed Prose_Word count. Below 700
# is `microchapter`, 700 through 1,600 inclusive is `normal`, and 1,601 through
# the Hard_Chapter_Maximum is `long-outlier`. Above that maximum there is no valid
# class at all, which is why no band extends past it.
#
# Transcribed from the design's Length_Class table rather than read back from
# `derive_length_class`, so a property test comparing the checker against this
# strategy is comparing it against the specification and not against itself.
LENGTH_CLASS_BANDS: Mapping[str, Tuple[int, int]] = {
    "microchapter": (1, 699),
    "normal": (700, 1600),
    "long-outlier": (1601, nf.HARD_CHAPTER_MAXIMUM),
}


def words_in_length_class(length_class: str) -> "st.SearchStrategy[int]":
    """A Prose_Word count that the design assigns to exactly `length_class`."""

    low, high = LENGTH_CLASS_BANDS[length_class]
    return st.integers(min_value=low, max_value=high)


def band_boundary_word_counts() -> "st.SearchStrategy[int]":
    """A count sitting exactly on a band edge, where an off-by-one would hide.

    Property 5 (task 8.14) needs these: the interesting counts are 699/700 and
    1600/1601, plus the Hard_Chapter_Maximum and the first count past it.
    """

    edges: List[int] = [1]
    for low, high in LENGTH_CLASS_BANDS.values():
        edges.extend((low - 1, low, high, high + 1))
    return st.sampled_from(sorted({edge for edge in edges if edge >= 0}))


# ---------------------------------------------------------------------------
# Chapter_Headers and Prose_Bodies
# ---------------------------------------------------------------------------


@st.composite
def conforming_headers(
    draw: Any,
    *,
    chapter: Optional[int] = None,
    movement: Optional[str] = None,
    length_class: Optional[str] = None,
) -> Dict[str, Any]:
    """A Chapter_Header whose nine keys agree with each other.

    The declared `words` and `length_class` match the body the header is built
    for, so any disagreement a property test observes was injected on purpose.
    """

    chosen_class = length_class or draw(length_classes())
    words = draw(words_in_length_class(chosen_class))
    return nf.chapter_header(
        chapter=chapter if chapter is not None else draw(chapter_numbers()),
        movement=movement or draw(movements()),
        prose=nf.prose_of_length(words),
        status=draw(chapter_statuses()),
    )


@st.composite
def header_body_pairs(draw: Any) -> Tuple[Dict[str, Any], str]:
    """A header and the Prose_Body it describes, consistent by construction."""

    chosen_class = draw(length_classes())
    words = draw(words_in_length_class(chosen_class))
    body = nf.prose_of_length(words)
    return nf.chapter_header(prose=body), body


HEADER_MALFORMATIONS: Tuple[str, ...] = (
    "missing-key",
    "unknown-key",
    "duplicate-key",
    "unopened-delimiter",
    "unclosed-delimiter",
    "declared-words-disagree",
    "declared-length-class-disagree",
    "unknown-movement",
    "unknown-status",
)


@st.composite
def header_variants(draw: Any) -> Variant:
    """A rendered Chapter_File header, conforming or malformed one way.

    Requirement 9.6 fixes the nine keys and the delimiters; Requirement 9.7 fixes
    the agreement between declared and observed counts. Exactly one fault is
    injected per draw so a counterexample names a single cause.
    """

    words = draw(words_in_length_class("normal"))
    body = nf.prose_of_length(words)
    if draw(st.booleans()):
        return Variant(
            label="conforming nine-key header",
            valid=True,
            payload=nf.render_chapter_file(nf.chapter_header(prose=body), body),
            requirement="9.6",
        )

    fault = draw(st.sampled_from(list(HEADER_MALFORMATIONS)))
    header = nf.chapter_header(prose=body)
    options: Dict[str, Any] = {}
    requirement = "9.6"

    if fault == "missing-key":
        header = nf.chapter_header(
            prose=body, drop_keys=[draw(st.sampled_from(list(nf.CHAPTER_HEADER_KEYS)))]
        )
    elif fault == "unknown-key":
        header = nf.chapter_header(
            prose=body, overrides={"unbudgeted_key": "not in the restricted set"}
        )
    elif fault == "duplicate-key":
        options = {"duplicate_key": "chapter"}
    elif fault == "unopened-delimiter":
        options = {"open_delimiter": "***"}
    elif fault == "unclosed-delimiter":
        options = {"close_delimiter": "***"}
    elif fault == "declared-words-disagree":
        header = nf.chapter_header(prose=body, words=words + 1)
        requirement = "9.7"
    elif fault == "declared-length-class-disagree":
        header = nf.chapter_header(
            prose=body,
            length_class=draw(
                st.sampled_from([c for c in nf.LENGTH_CLASSES if c != "normal"])
            ),
        )
        requirement = "9.7"
    elif fault == "unknown-movement":
        header = nf.chapter_header(prose=body, movement="interlude")
    elif fault == "unknown-status":
        header = nf.chapter_header(prose=body, status="nearly-there")

    return Variant(
        label=fault,
        valid=False,
        payload=nf.render_chapter_file(header, body, **options),
        requirement=requirement,
    )


# ---------------------------------------------------------------------------
# Movement allocations and outline plans
# ---------------------------------------------------------------------------


@st.composite
def movement_allocations(
    draw: Any, *, total: Optional[int] = None
) -> Dict[str, int]:
    """Four positive per-movement chapter counts forming contiguous blocks.

    Only the block sizes vary. Which movement comes first is fixed by the design
    and is not a degree of freedom, so the generator never permutes the order.
    """

    planned = total if total is not None else draw(st.integers(min_value=8, max_value=60))
    counts: List[int] = []
    remaining = planned
    for index in range(len(nf.MOVEMENTS) - 1):
        headroom = remaining - (len(nf.MOVEMENTS) - 1 - index)
        take = draw(st.integers(min_value=1, max_value=max(1, headroom)))
        counts.append(take)
        remaining -= take
    counts.append(remaining)
    return dict(zip(nf.MOVEMENTS, counts))


@st.composite
def conforming_outlines(draw: Any) -> Tuple[Dict[str, Any], ...]:
    """A whole ArcEntry sequence numbered 1..N in ordered contiguous blocks."""

    allocation = draw(movement_allocations())
    entries: List[Dict[str, Any]] = []
    chapter = 0
    for movement in nf.MOVEMENTS:
        for _ in range(allocation[movement]):
            chapter += 1
            entries.append(
                nf.arc_entry(
                    chapter=chapter,
                    movement=movement,
                    slug="chapter-{0:03d}".format(chapter),
                )
            )
    return tuple(entries)


OUTLINE_MALFORMATIONS: Tuple[str, ...] = (
    "duplicate-chapter-number",
    "gap-in-sequence",
    "does-not-start-at-one",
    "duplicate-filename",
    "movement-block-discontiguous",
    "movement-blocks-out-of-order",
    "movement-block-missing",
)


@st.composite
def outline_variants(draw: Any) -> Variant:
    """A whole outline, conforming or broken in exactly one structural way.

    Requirement 11.3 fixes the 1..N sequence and the plan/file bijection;
    Requirement 1.2 fixes the four ordered contiguous movement blocks.
    """

    entries = list(draw(conforming_outlines()))
    if draw(st.booleans()):
        return Variant(
            label="ordered contiguous outline numbered 1..N",
            valid=True,
            payload=tuple(entries),
            requirement="11.3",
        )

    fault = draw(st.sampled_from(list(OUTLINE_MALFORMATIONS)))
    index = draw(st.integers(min_value=1, max_value=len(entries) - 1))
    requirement = "11.3"

    if fault == "duplicate-chapter-number":
        entries[index] = dict(entries[index], chapter=entries[index - 1]["chapter"])
    elif fault == "gap-in-sequence":
        entries[index] = dict(entries[index], chapter=entries[index]["chapter"] + 1000)
    elif fault == "does-not-start-at-one":
        entries = [dict(entry, chapter=entry["chapter"] + 1) for entry in entries]
    elif fault == "duplicate-filename":
        entries[index] = dict(entries[index], filename=entries[index - 1]["filename"])
    elif fault == "movement-block-discontiguous":
        # Reassigning an arbitrary entry can silently *extend* its neighbour's
        # block instead of breaking anything. Sending the final chapter back to
        # the first movement always produces a backwards transition, so the fault
        # this case claims to inject is the fault it actually injects.
        entries[-1] = dict(entries[-1], movement=nf.MOVEMENTS[0])
        requirement = "1.2"
    elif fault == "movement-blocks-out-of-order":
        entries = [
            dict(
                entry,
                movement=nf.MOVEMENTS[
                    len(nf.MOVEMENTS) - 1 - nf.MOVEMENTS.index(entry["movement"])
                ],
            )
            for entry in entries
        ]
        requirement = "1.2"
    elif fault == "movement-block-missing":
        dropped = entries[-1]["movement"]
        entries = [
            dict(entry, movement=nf.MOVEMENTS[0])
            if entry["movement"] == dropped
            else entry
            for entry in entries
        ]
        requirement = "1.2"

    return Variant(
        label=fault, valid=False, payload=tuple(entries), requirement=requirement
    )


# ---------------------------------------------------------------------------
# POV assignment, Same_POV_Run, and the load vector
# ---------------------------------------------------------------------------

POV_IDS: Tuple[str, ...] = tuple(nf.MANUSCRIPT_POV_LOAD)

# Requirement 2.7 and 2.15 set two independent Same_POV_Run bounds. Transcribed
# here so a property test measures the checker against the requirement.
RUN_CHAPTER_LIMIT = 3
RUN_WORD_LIMIT = 3600


@st.composite
def pov_assignments(
    draw: Any,
    *,
    chapters: Optional[int] = None,
    max_run: int = RUN_CHAPTER_LIMIT,
    words: Optional[Tuple[int, int]] = None,
) -> Tuple[Tuple[int, str, Optional[int]], ...]:
    """A `(chapter, pov_id, words)` sequence whose runs stay within `max_run`.

    `max_run` above the limit is how a property test asks for a violating run
    without hand-building one, and the per-chapter word range is separate so the
    chapter-count bound and the word bound can be crossed independently.
    """

    count = chapters if chapters is not None else draw(st.integers(2, 24))
    low, high = words if words is not None else (400, 1400)
    assignments: List[Tuple[int, str, Optional[int]]] = []
    current = draw(st.sampled_from(list(POV_IDS)))
    run = 0
    for chapter in range(1, count + 1):
        if run >= max_run:
            current = draw(
                st.sampled_from([pov for pov in POV_IDS if pov != current])
            )
            run = 0
        elif run > 0 and draw(st.booleans()):
            current = draw(
                st.sampled_from([pov for pov in POV_IDS if pov != current])
            )
            run = 0
        run += 1
        assignments.append(
            (chapter, current, draw(st.integers(min_value=low, max_value=high)))
        )
    return tuple(assignments)


@st.composite
def pov_run_variants(draw: Any) -> Variant:
    """A POV assignment sequence, conforming or over exactly one bound.

    The two bounds are independent: a three-chapter run of long chapters breaks
    the word bound while satisfying the chapter bound, and a four-chapter run of
    short chapters does the reverse. Both directions matter, so both are drawn.
    """

    fault = draw(
        st.sampled_from(
            [
                "within both bounds",
                "over the chapter bound",
                "over the word bound",
                "unknown words in a multi-chapter run",
            ]
        )
    )
    if fault == "within both bounds":
        return Variant(
            label=fault,
            valid=True,
            payload=draw(pov_assignments(words=(400, 1100))),
            requirement="2.7, 2.15",
        )
    if fault == "over the chapter bound":
        run = draw(st.integers(min_value=RUN_CHAPTER_LIMIT + 1, max_value=6))
        pov = draw(st.sampled_from(list(POV_IDS)))
        return Variant(
            label=fault,
            valid=False,
            payload=tuple(
                (chapter, pov, draw(st.integers(min_value=300, max_value=700)))
                for chapter in range(1, run + 1)
            ),
            requirement="2.7",
        )
    if fault == "over the word bound":
        pov = draw(st.sampled_from(list(POV_IDS)))
        per_chapter = draw(
            st.integers(min_value=RUN_WORD_LIMIT // RUN_CHAPTER_LIMIT + 1,
                        max_value=2500)
        )
        return Variant(
            label=fault,
            valid=False,
            payload=tuple(
                (chapter, pov, per_chapter)
                for chapter in range(1, RUN_CHAPTER_LIMIT + 1)
            ),
            requirement="2.15",
        )
    pov = draw(st.sampled_from(list(POV_IDS)))
    return Variant(
        label=fault,
        valid=False,
        payload=((1, pov, None), (2, pov, 900)),
        requirement="11.12",
    )


@st.composite
def load_vector_variants(draw: Any) -> Variant:
    """The provisional per-POV load vector, exact or changed.

    Requirement 15.3 fixes the 56/32/33/7 multiset. Requirement 12.11 keeps which
    selected name owns which number outside pass/fail, so the valid cases include
    a permutation of the numbers across POV_IDs.
    """

    exact = {pov: dict(load) for pov, load in nf.MANUSCRIPT_POV_LOAD.items()}
    fault = draw(
        st.sampled_from(
            [
                "exact 56/32/33/7 vector",
                "totals permuted across POV_IDs",
                "one total changed",
                "a POV dropped from the roster",
                "movement counts disagree with the total",
            ]
        )
    )
    if fault == "exact 56/32/33/7 vector":
        return Variant(label=fault, valid=True, payload=exact, requirement="15.3")
    if fault == "totals permuted across POV_IDs":
        ordered = list(exact)
        rotated = ordered[1:] + ordered[:1]
        return Variant(
            label=fault,
            valid=True,
            payload={
                pov: dict(exact[source]) for pov, source in zip(ordered, rotated)
            },
            requirement="12.11",
        )
    if fault == "one total changed":
        pov = draw(st.sampled_from(list(exact)))
        delta = draw(st.sampled_from([-2, -1, 1, 2]))
        changed = {name: dict(load) for name, load in exact.items()}
        changed[pov]["total"] = int(changed[pov]["total"]) + delta
        return Variant(label=fault, valid=False, payload=changed, requirement="15.3")
    if fault == "a POV dropped from the roster":
        pov = draw(st.sampled_from(list(exact)))
        return Variant(
            label=fault,
            valid=False,
            payload={name: dict(load) for name, load in exact.items() if name != pov},
            requirement="15.3",
        )
    pov = draw(st.sampled_from(list(exact)))
    changed = {name: dict(load) for name, load in exact.items()}
    movement = draw(st.sampled_from(list(nf.MOVEMENTS)))
    changed[pov][movement] = int(changed[pov].get(movement, 0)) + 3
    return Variant(label=fault, valid=False, payload=changed, requirement="15.3")


NAME_VARIANT_SPELLINGS: Tuple[str, ...] = (
    "Mara Kessler",
    "mara kessler",
    "MARA KESSLER",
    "Mara K.",
    "M\u00e1ra Kessler",
)


@st.composite
def name_variants(draw: Any) -> Variant:
    """A selected name that varies while the Stable_ID does not.

    Requirement 12.11 makes name choice and capitalization a non-violation. Every
    case here is valid; the property is that the checker stays silent about all
    of them, which is a claim about what it must *not* do.
    """

    return Variant(
        label="selected name spelling varies, Stable_ID fixed",
        valid=True,
        payload=nf.pov_profile(
            pov_id="POV-MARA",
            selected_name=draw(st.sampled_from(list(NAME_VARIANT_SPELLINGS))),
            aliases=draw(
                st.lists(st.sampled_from(list(NAME_VARIANT_SPELLINGS)), max_size=3)
            ),
        ),
        requirement="12.11",
    )


# ---------------------------------------------------------------------------
# Cross_Cuts and chronology
# ---------------------------------------------------------------------------


@st.composite
def cross_cut_graphs(draw: Any, *, chapters: int = 24) -> Tuple[Dict[str, Any], ...]:
    """A set of Cross_Cuts over distinct chapter pairs in the same movement."""

    count = draw(st.integers(min_value=1, max_value=6))
    cuts: List[Dict[str, Any]] = []
    for index in range(count):
        first = draw(st.integers(min_value=1, max_value=max(1, chapters - 1)))
        cuts.append(
            nf.cross_cut(
                cross_cut_id="CUT-GEN-{0:03d}".format(index + 1),
                chapters=(first, first + 1),
            )
        )
    return tuple(cuts)


@st.composite
def chronologies(draw: Any, *, chapters: int = 24) -> Tuple[Dict[str, Any], ...]:
    """A TimelineEntry set covering a chapter range, one entry per chapter."""

    count = draw(st.integers(min_value=1, max_value=chapters))
    return tuple(
        nf.timeline_entry(
            timeline_id="TL-GEN-{0:03d}".format(chapter),
            chronology_kind=draw(st.sampled_from(["point", "interval"])),
            chapter_numbers=[chapter],
        )
        for chapter in range(1, count + 1)
    )


# ---------------------------------------------------------------------------
# Mode states: the consent and calibration truth table
# ---------------------------------------------------------------------------

# The design's four neural-communication modes plus the no-event value, and the
# vocabularies each mode-bearing field draws from. Transcribed from the design's
# mechanism tables rather than imported, so a property test measures the checker
# against the specification.
TECHNICAL_MODES: Tuple[str, ...] = (
    "RECEIVE",
    "INTRUDE",
    "CANCEL",
    "PAIR",
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
SOURCE_SIDE_CONTINUITY_VALUES: Tuple[str, ...] = (
    "continuous",
    "discontinuous",
    "unknown",
    "not-applicable",
)
DELIBERATE_SEND_STATES: Tuple[str, ...] = (
    "required",
    "paused",
    "revoked",
    "integrity-failed",
)

# The conforming shape of a `PAIR` state: a deliberate bench send to a
# person-specific address that is locked to the pair.
PAIR_APPARATUS_MODE = "bench-transmit"
PAIR_ADDRESS_STATE = "locked"


def pair_technical_state(**pair_options: Any) -> Dict[str, Any]:
    """A conforming `PAIR` `technical_state`, with the pair object substitutable.

    Every `PAIR` probe in the suite needs the same five surrounding fields set
    correctly, so they live here once. A test varying only the consent or the
    evidence passes `pair_state=` or `pairing_evidence=` and inherits the rest.
    """

    options: Dict[str, Any] = {
        "mode": "PAIR",
        "apparatus_mode": PAIR_APPARATUS_MODE,
        "transmit_stage_present": True,
        "person_specific_address_state": PAIR_ADDRESS_STATE,
        "pair_state": nf.pair_state(),
        "pairing_evidence": nf.pairing_evidence(),
    }
    options.update(pair_options)
    return nf.technical_state(**options)


@st.composite
def consent_calibration_rows(draw: Any) -> Variant:
    """The `PAIR` consent and calibration truth table, row by row.

    Requirement 6.x makes a Pairing_Session lawful only with two living
    participants, current revocable consent authorized on both sides, a
    calibration belonging to exactly those participants, a non-transferable
    calibration, and a required deliberate send. Each malformed row negates
    exactly one of those, which is what lets one property test cover the table.
    """

    row = draw(
        st.sampled_from(
            [
                "two living consenting participants",
                "consent not current",
                "consent not revocable",
                "one side unauthorized",
                "calibration participants differ",
                "calibration marked transferable",
                "deliberate send not required",
                "a replacement participant reuses the calibration",
                "a nonliving participant",
            ]
        )
    )
    if row == "two living consenting participants":
        return Variant(label=row, valid=True, payload=nf.pair_state(), requirement="6.4")
    if row == "consent not current":
        return Variant(
            label=row,
            valid=False,
            payload=nf.pair_state(
                consent={
                    "current": False,
                    "specific_act": "Consent given for an earlier session.",
                    "revocable": True,
                    "authorized_a": True,
                    "authorized_b": True,
                }
            ),
            requirement="6.4",
        )
    if row == "consent not revocable":
        return Variant(
            label=row,
            valid=False,
            payload=nf.pair_state(
                consent={
                    "current": True,
                    "specific_act": "Consent declared irrevocable.",
                    "revocable": False,
                    "authorized_a": True,
                    "authorized_b": True,
                }
            ),
            requirement="6.4",
        )
    if row == "one side unauthorized":
        side = draw(st.sampled_from(["authorized_a", "authorized_b"]))
        consent = {
            "current": True,
            "specific_act": "Consent recorded on one side only.",
            "revocable": True,
            "authorized_a": True,
            "authorized_b": True,
        }
        consent[side] = False
        return Variant(
            label=row + " (" + side + ")",
            valid=False,
            payload=nf.pair_state(consent=consent),
            requirement="6.4",
        )
    if row == "calibration participants differ":
        return Variant(
            label=row,
            valid=False,
            payload=nf.pair_state(calibration_participants=("CHAR-001", "CHAR-003")),
            requirement="6.5",
        )
    if row == "calibration marked transferable":
        return Variant(
            label=row,
            valid=False,
            payload=nf.pair_state(calibration_transferable=True),
            requirement="6.5",
        )
    if row == "deliberate send not required":
        return Variant(
            label=row,
            valid=False,
            payload=nf.pair_state(deliberate_send_state="optional"),
            requirement="6.6",
        )
    if row == "a replacement participant reuses the calibration":
        return Variant(
            label=row,
            valid=False,
            payload=nf.pair_state(
                participants=("CHAR-001", "CHAR-004"),
                calibration_participants=("CHAR-001", "CHAR-002"),
            ),
            requirement="6.5",
        )
    # Requirement 6.4 wants two *living* participants. A stand-in written as a
    # non-Character identifier is caught elsewhere, by reference resolution
    # against the roster, which is why this case is labelled invalid. What no
    # program can see is the remaining half: a participant who *is* on the roster
    # but is dead by the time of the session, because no schema carries a
    # living-or-dead state. So the mechanism check is expected to stay silent
    # here, and the pairing itself is an `EditorialFinding`.
    return Variant(
        label=row,
        valid=False,
        objective=False,
        payload=nf.pair_state(participants=("CHAR-001", "ARCHIVE-001")),
        requirement="6.4",
    )


PAUSE_REVOCATION_EVENTS: Tuple[str, ...] = (
    "pause",
    "resume",
    "revoke",
    "clipping",
    "latency",
    "integrity-failure",
    "recovery",
)


@st.composite
def pause_revocation_streams(draw: Any) -> Variant:
    """A session event stream, lawful or ending in an unhandled fault.

    A pause must be resumable and a revocation must end the session; a clipping,
    latency, or integrity failure must be either recovered or left declared as a
    failure, never silently continued as if the channel were clean.
    """

    stream = draw(
        st.lists(
            st.sampled_from(list(PAUSE_REVOCATION_EVENTS)),
            min_size=1,
            max_size=8,
        )
    )
    faults = {"clipping", "latency", "integrity-failure"}
    if "revoke" in stream and stream.index("revoke") != len(stream) - 1:
        return Variant(
            label="session continues after revocation",
            valid=False,
            payload=tuple(stream),
            requirement="6.9",
        )
    last_fault = max(
        (index for index, event in enumerate(stream) if event in faults), default=-1
    )
    if last_fault >= 0 and "recovery" not in stream[last_fault + 1 :]:
        return Variant(
            label="unrecovered channel fault",
            valid=False,
            payload=tuple(stream),
            requirement="6.10",
        )
    return Variant(
        label="lawful pause, resume, and recovery stream",
        valid=True,
        payload=tuple(stream),
        requirement="6.9, 6.10",
    )


@st.composite
def recording_consent_combinations(draw: Any) -> Variant:
    """Content recording against the two independent recording consents.

    Requirement 6.12 makes the two consents independent: recording is lawful only
    when both are given, so three of the four combinations are violations when
    recording is enabled, and all four are lawful when it is not.
    """

    enabled = draw(st.booleans())
    consent_a = draw(st.booleans())
    consent_b = draw(st.booleans())
    lawful = (not enabled) or (consent_a and consent_b)
    return Variant(
        label="recording={0} consent_a={1} consent_b={2}".format(
            enabled, consent_a, consent_b
        ),
        valid=lawful,
        payload=nf.pairing_evidence(
            content_recording_enabled=enabled,
            recording_consent_a=consent_a,
            recording_consent_b=consent_b,
        ),
        requirement="6.12",
    )


@st.composite
def transcript_variants(draw: Any) -> Variant:
    """A session transcript, honest or overclaiming.

    A transcript may cover a subset of one consented session and must stay
    semantically opaque. Overclaiming means spanning sessions, asserting meaning,
    or presenting itself as provenance proof.
    """

    case = draw(
        st.sampled_from(
            [
                "subset of one consented session",
                "spans two sessions",
                "claims semantic content",
                "presented as provenance proof",
            ]
        )
    )
    base: Dict[str, Any] = {
        "session_id": "SESSION-GEN-001",
        "covers_subset": True,
        "cross_session": False,
        "semantic_claim": False,
        "provenance_proof": False,
    }
    if case == "subset of one consented session":
        return Variant(
            label=case,
            valid=True,
            payload=nf.pairing_evidence(
                content_recording_enabled=True,
                recording_consent_a=True,
                recording_consent_b=True,
                transcript=base,
            ),
            requirement="6.13",
        )
    key = {
        "spans two sessions": "cross_session",
        "claims semantic content": "semantic_claim",
        "presented as provenance proof": "provenance_proof",
    }[case]
    return Variant(
        label=case,
        valid=False,
        payload=nf.pairing_evidence(
            content_recording_enabled=True,
            recording_consent_a=True,
            recording_consent_b=True,
            transcript=dict(base, **{key: True}),
        ),
        requirement="6.13",
    )


@st.composite
def technical_state_variants(draw: Any) -> Variant:
    """A `technical_state`, one mode at a time, valid or mode-collapsed.

    The design keeps the four modes distinct: a state declares one mode and
    carries only that mode's object. Declaring `PAIR` while holding a
    `cancel_state`, carrying both objects at once, or naming a mode outside the
    fixed five is the malformed direction.

    `INTRUDE` is a real mode, so it is generated as a *valid* state. What the
    design forbids is a semantic reading, and that is expressed by the address
    state and the mode's own invariants rather than by the mode's existence.
    """

    case = draw(
        st.sampled_from(
            [
                "not-applicable with no mode object",
                "RECEIVE with no mode object",
                "RECEIVE with a discontinuous source side",
                "INTRUDE with no mode object",
                "CANCEL with a cancel object",
                "PAIR with a pair object",
                "PAIR and CANCEL objects together",
                "PAIR declared with only a cancel object",
                "CANCEL declared with a pair object",
                "a mode outside the fixed five",
                "an apparatus mode outside the fixed four",
                "an address state outside the fixed five",
            ]
        )
    )
    if case == "not-applicable with no mode object":
        return Variant(
            label=case, valid=True, payload=nf.technical_state(), requirement="14.5"
        )
    if case == "RECEIVE with no mode object":
        return Variant(
            label=case,
            valid=True,
            payload=nf.technical_state(
                mode="RECEIVE",
                # A received signal has a continuous source side by definition, so
                # this is pinned rather than drawn. The discontinuous reading is
                # generated as its own case below.
                source_side_continuity="continuous",
                apparatus_mode="receive-only",
                transmit_stage_present=False,
                person_specific_address_state="locked",
            ),
            requirement="14.5",
        )
    if case == "RECEIVE with a discontinuous source side":
        return Variant(
            label=case,
            valid=False,
            payload=nf.technical_state(
                mode="RECEIVE",
                source_side_continuity=draw(
                    st.sampled_from(
                        [
                            value
                            for value in SOURCE_SIDE_CONTINUITY_VALUES
                            if value != "continuous"
                        ]
                    )
                ),
                apparatus_mode="receive-only",
                transmit_stage_present=False,
                person_specific_address_state="locked",
            ),
            requirement="14.5",
        )
    if case == "INTRUDE with no mode object":
        return Variant(
            label=case,
            valid=True,
            payload=nf.technical_state(
                mode="INTRUDE",
                apparatus_mode="bench-transmit",
                transmit_stage_present=True,
                person_specific_address_state="identified",
            ),
            requirement="14.6",
        )
    if case == "CANCEL with a cancel object":
        return Variant(
            label=case,
            valid=True,
            payload=nf.technical_state(
                mode="CANCEL",
                apparatus_mode="bidirectional-architecture",
                transmit_stage_present=True,
                person_specific_address_state="not-applicable",
                cancel_state=nf.cancel_state(),
            ),
            requirement="14.9",
        )
    if case == "PAIR with a pair object":
        return Variant(
            label=case, valid=True, payload=pair_technical_state(), requirement="14.7"
        )
    if case == "PAIR and CANCEL objects together":
        return Variant(
            label=case,
            valid=False,
            payload=pair_technical_state(cancel_state=nf.cancel_state()),
            requirement="14.5",
        )
    if case == "PAIR declared with only a cancel object":
        return Variant(
            label=case,
            valid=False,
            payload=pair_technical_state(
                pair_state=None, cancel_state=nf.cancel_state()
            ),
            requirement="14.5",
        )
    if case == "CANCEL declared with a pair object":
        return Variant(
            label=case,
            valid=False,
            payload=nf.technical_state(
                mode="CANCEL",
                apparatus_mode="bidirectional-architecture",
                transmit_stage_present=True,
                pair_state=nf.pair_state(),
            ),
            requirement="14.5",
        )
    if case == "a mode outside the fixed five":
        return Variant(
            label=case,
            valid=False,
            payload=nf.technical_state(mode="TRANSMIT"),
            requirement="14.5",
        )
    if case == "an apparatus mode outside the fixed four":
        return Variant(
            label=case,
            valid=False,
            payload=nf.technical_state(apparatus_mode="single-channel"),
            requirement="14.5",
        )
    return Variant(
        label=case,
        valid=False,
        payload=nf.technical_state(
            person_specific_address_state="reads-arbitrary-memory"
        ),
        requirement="14.6",
    )


# ---------------------------------------------------------------------------
# Role-decision states: DEC-002, DEC-005, DEC-007, DEC-012, DEC-014, DEC-015
# ---------------------------------------------------------------------------


@st.composite
def dec_002_states(draw: Any) -> Variant:
    """The `DEC-002` mapping and the separate `DEC-014` same-speaker testimony.

    The lawful state keeps three things apart: the receive-only December interval
    with its person-specific lock, the distinct later bench path and handshake,
    and the *Case Zero* first-person testimony that is binding *as testimony*.
    The malformed states each erase one of those distinctions.
    """

    case = draw(
        st.sampled_from(
            [
                "receive-only December interval with person-specific lock",
                "distinct later bench path and handshake",
                "same-speaker lyric testimony as attributed testimony",
                "whole mechanism collapsed into one lyric fact",
                "Case Zero testimony demoted to advisory",
                "causal-linkage record with a reveal owner and release window",
                "a December transmit stage",
                "page nine treated as proof of December transmission",
            ]
        )
    )
    if case == "receive-only December interval with person-specific lock":
        return Variant(
            label=case,
            valid=True,
            payload=nf.timeline_entry(
                timeline_id="TL-DEC-002-DECEMBER",
                chronology_kind="interval",
                state=nf.technical_state(
                    mode="RECEIVE",
                    source_side_continuity="continuous",
                    apparatus_mode="receive-only",
                    transmit_stage_present=False,
                    person_specific_address_state="locked",
                ),
            ),
            requirement="14.10",
        )
    if case == "distinct later bench path and handshake":
        return Variant(
            label=case,
            valid=True,
            payload=nf.timeline_entry(
                timeline_id="TL-DEC-002-BENCH",
                chronology_kind="point",
                state=pair_technical_state(),
            ),
            requirement="14.10",
        )
    if case == "same-speaker lyric testimony as attributed testimony":
        return Variant(
            label=case,
            valid=True,
            payload=nf.canon_fact(
                canon_id="CF-DEC-014-TESTIMONY",
                authority_basis="lyric",
                source_path="songs/Case Zero.md",
                source_location="Verse 2",
                first_person_testimony=True,
            ),
            requirement="14.11",
        )
    if case == "whole mechanism collapsed into one lyric fact":
        return Variant(
            label=case,
            valid=False,
            payload=nf.canon_fact(
                canon_id="CF-DEC-002-COLLAPSED",
                authority_basis="lyric",
                source_path="songs/Case Zero.md",
                source_location="Verse 2",
                statement="December reception, the bench handshake, and the "
                "person-specific lock are one undifferentiated mechanism.",
                first_person_testimony=True,
                truth_scope="authoritative-proposition",
            ),
            requirement="14.11",
        )
    if case == "Case Zero testimony demoted to advisory":
        return Variant(
            label=case,
            valid=False,
            payload=nf.canon_fact(
                canon_id="CF-DEC-014-DEMOTED",
                authority_basis="lyric",
                source_path="songs/Case Zero.md",
                source_location="Verse 2",
                source_material_class="production-note",
                first_person_testimony=True,
            ),
            requirement="14.11",
        )
    if case == "causal-linkage record with a reveal owner and release window":
        return Variant(
            label=case,
            valid=False,
            payload=nf.reveal(
                reveal_id="REV-DEC-002-CAUSAL",
                fact_id="FACT-DEC-002-CAUSAL-LINKAGE",
                truth_status="unresolved",
                reveal_owner="POV-NIA",
                reader_release_chapter=draw(chapter_numbers()),
                payoff_window=[70, 80],
            ),
            requirement="14.12",
        )
    if case == "a December transmit stage":
        return Variant(
            label=case,
            valid=False,
            payload=nf.timeline_entry(
                timeline_id="TL-DEC-002-TRANSMIT",
                chronology_kind="interval",
                state=nf.technical_state(
                    mode="RECEIVE",
                    apparatus_mode="receive-only",
                    # A receive-only interval with a transmit stage is the
                    # mechanism contradiction `DEC-002` exists to prevent.
                    transmit_stage_present=True,
                    person_specific_address_state="locked",
                ),
            ),
            requirement="14.10",
        )
    return Variant(
        label=case,
        valid=False,
        payload=nf.canon_fact(
            canon_id="CF-DEC-002-PAGE-NINE",
            authority_basis="lyric",
            source_path="songs/Case Zero.md",
            source_location="Page nine",
            statement="Page nine proves a December transmission occurred.",
            first_person_testimony=True,
            truth_scope="authoritative-proposition",
        ),
        requirement="14.11",
    )


@st.composite
def dec_007_states(draw: Any) -> Variant:
    """`DEC-007`: three accounts held apart, both records `unverified`.

    Mara's high but non-authoritative belief, Nia's refusal and later release,
    and Julian's professional inference are three distinct epistemic positions.
    The malformed direction promotes any one of them to settled truth.
    """

    case = draw(
        st.sampled_from(
            [
                "Mara's high non-authoritative belief",
                "Nia's refusal then release",
                "Julian's professional inference",
                "both accounts left unresolved",
                "a belief promoted to authoritative proposition",
                "an inference recorded as omniscient causal proof",
                "an account given a truth status outside the fixed three",
            ]
        )
    )
    valid_cases = {
        "Mara's high non-authoritative belief": nf.canon_fact(
            canon_id="CF-DEC-007-MARA",
            authority_basis="author-decision",
            source_location="DEC-007",
            statement="Mara holds a high-confidence belief that is not "
            "authoritative about what happened.",
            first_person_testimony=True,
            speaker="CHAR-001",
        ),
        "Nia's refusal then release": nf.canon_fact(
            canon_id="CF-DEC-007-NIA",
            authority_basis="author-decision",
            source_location="DEC-007",
            statement="Nia refuses to say, and releases the account later.",
            first_person_testimony=True,
            speaker="CHAR-002",
        ),
        "Julian's professional inference": nf.canon_fact(
            canon_id="CF-DEC-007-JULIAN",
            authority_basis="author-decision",
            source_location="DEC-007",
            statement="Julian infers a mechanism from professional experience.",
            first_person_testimony=True,
            speaker="CHAR-003",
        ),
        "both accounts left unresolved": nf.reveal(
            reveal_id="REV-DEC-007-ACCOUNTS",
            fact_id="FACT-DEC-007-ACCOUNTS",
            truth_status="unresolved",
        ),
    }
    if case in valid_cases:
        return Variant(label=case, valid=True, payload=valid_cases[case],
                       requirement="14.13")
    if case == "a belief promoted to authoritative proposition":
        return Variant(
            label=case,
            valid=False,
            payload=nf.canon_fact(
                canon_id="CF-DEC-007-PROMOTED",
                authority_basis="author-decision",
                source_location="DEC-007",
                first_person_testimony=True,
                speaker="CHAR-001",
                truth_scope="authoritative-proposition",
            ),
            requirement="14.13",
        )
    if case == "an inference recorded as omniscient causal proof":
        return Variant(
            label=case,
            valid=False,
            payload=nf.canon_fact(
                canon_id="CF-DEC-007-OMNISCIENT",
                authority_basis="author-decision",
                source_location="DEC-007",
                first_person_testimony=True,
                speaker="CHAR-003",
                truth_scope="omniscient",
            ),
            requirement="14.13",
        )
    return Variant(
        label=case,
        valid=False,
        payload=nf.reveal(
            reveal_id="REV-DEC-007-VERIFIED",
            fact_id="FACT-DEC-007-ACCOUNTS",
            truth_status="verified",
        ),
        requirement="14.13",
    )

    # `confirmed`, `character-belief`, and `unresolved` are the only statuses the
    # design allows. `verified` is not one of them, which is what makes an
    # account "proved" by assertion a structural violation rather than a reading.


HERITAGE_BASE_UNSPECIFIED = "unspecified_by_author"


@st.composite
def heritage_variants(draw: Any) -> Variant:
    """`heritage_base` left unspecified, or filled in against the decision.

    The author's decision is that the base stays unspecified. Whether a `fact`
    sentence quietly fills it, or infers a real-world particular from it, is a
    reading of prose, so those states are editorial rather than objective: the
    checker must record the extension and say nothing about its content.
    """

    case = draw(
        st.sampled_from(
            [
                "heritage_base unspecified_by_author",
                "heritage_base filled with a particular",
                "a real-world particular inferred from the base",
            ]
        )
    )
    if case == "heritage_base unspecified_by_author":
        return Variant(
            label=case,
            valid=True,
            payload=nf.character_name_extension(
                character_id="CHAR-005",
                fact="CHAR-005 identifies Fixture Five. Heritage base: {0}.".format(
                    HERITAGE_BASE_UNSPECIFIED
                ),
            ),
            requirement="14.4",
        )
    if case == "heritage_base filled with a particular":
        return Variant(
            label=case,
            valid=False,
            objective=False,
            payload=nf.character_name_extension(
                character_id="CHAR-005",
                fact="CHAR-005 identifies Fixture Five. Heritage base: a named "
                "real-world region.",
            ),
            requirement="14.4",
        )
    return Variant(
        label=case,
        valid=False,
        objective=False,
        payload=nf.character_name_extension(
            character_id="CHAR-005",
            fact="CHAR-005 identifies Fixture Five. Heritage base: {0}.".format(
                HERITAGE_BASE_UNSPECIFIED
            ),
            consistency_implications=[
                "A real-world particular inferred from the unspecified base."
            ],
        ),
        requirement="14.4",
    )


@st.composite
def canon_authority_variants(draw: Any) -> Variant:
    """Every CanonFact authority basis, plus the states the matrix rejects.

    Self-authorizing bases carry a matching `source_material_class`. A ratified
    note needs an advisory class and a resolvable adoption. An unratified note is
    not canon at all, and advisory material contributes no binding implication.
    """

    case = draw(
        st.sampled_from(
            [
                "author-decision basis",
                "requirement basis",
                "lyric basis",
                "ratified note with an adoption reference",
                "advisory citation supporting an authorized fact",
                "unratified note treated as canon",
                "ratified note with no adoption reference",
                "self-authorizing basis with a mismatched material class",
                "advisory material marked binding",
            ]
        )
    )
    if case == "author-decision basis":
        return Variant(label=case, valid=True,
                       payload=nf.canon_fact(authority_basis="author-decision"),
                       requirement="14.1")
    if case == "requirement basis":
        return Variant(
            label=case,
            valid=True,
            payload=nf.canon_fact(
                authority_basis="requirement",
                source_path="planning/requirements.md",
                source_location="Requirement 14.1",
            ),
            requirement="14.1",
        )
    if case == "lyric basis":
        return Variant(
            label=case,
            valid=True,
            payload=nf.canon_fact(
                authority_basis="lyric",
                source_path=draw(st.sampled_from(list(nf.CANON_SOURCE_PATHS))),
                source_location="Verse 1",
            ),
            requirement="14.1",
        )
    if case == "ratified note with an adoption reference":
        return Variant(label=case, valid=True,
                       payload=nf.canon_fact(authority_basis="ratified-note"),
                       requirement="14.2")
    if case == "advisory citation supporting an authorized fact":
        return Variant(
            label=case,
            valid=True,
            payload=nf.canon_fact(
                supporting_advisory_citations=[nf.advisory_citation()]
            ),
            requirement="14.3",
        )
    if case == "unratified note treated as canon":
        return Variant(
            label=case,
            valid=False,
            payload=nf.canon_fact(
                authority_basis="production-note",
                source_path="songs/Case Zero.md",
                source_location="Production Notes",
                source_material_class="production-note",
            ),
            requirement="14.2",
        )
    if case == "ratified note with no adoption reference":
        return Variant(
            label=case,
            valid=False,
            payload=nf.canon_fact(
                authority_basis="ratified-note", overrides={"adopted_by": None}
            ),
            requirement="14.2",
        )
    if case == "self-authorizing basis with a mismatched material class":
        basis = draw(st.sampled_from(["author-decision", "requirement", "lyric"]))
        return Variant(
            label=case + " (" + basis + ")",
            valid=False,
            payload=nf.canon_fact(
                authority_basis=basis, source_material_class="style-note"
            ),
            requirement="14.1",
        )
    return Variant(
        label=case,
        valid=False,
        payload=nf.canon_fact(
            supporting_advisory_citations=[
                nf.advisory_citation(classification="binding")
            ]
        ),
        requirement="14.3",
    )


@st.composite
def canon_source_inventories(draw: Any) -> Variant:
    """`DEC-014`: the Canon_Source set is exactly five named paths.

    *One-Time Pad* is excluded by the decision, so adding it is a violation, and
    dropping *Case Zero* removes the source the testimony depends on.
    """

    case = draw(
        st.sampled_from(
            [
                "the exact five Canon_Source paths",
                "Case Zero missing",
                "One-Time Pad added",
                "a path outside the decision",
            ]
        )
    )
    exact = list(nf.CANON_SOURCE_PATHS)
    if case == "the exact five Canon_Source paths":
        return Variant(label=case, valid=True, payload=tuple(exact),
                       requirement="14.14")
    if case == "Case Zero missing":
        return Variant(
            label=case,
            valid=False,
            payload=tuple(p for p in exact if p != "songs/Case Zero.md"),
            requirement="14.14",
        )
    if case == "One-Time Pad added":
        return Variant(
            label=case,
            valid=False,
            payload=tuple(exact + [nf.EXCLUDED_CANON_SOURCE_PATH]),
            requirement="14.14",
        )
    return Variant(
        label=case,
        valid=False,
        payload=tuple(exact + ["songs/an-unlisted-song.md"]),
        requirement="14.14",
    )


@st.composite
def dec_005_states(draw: Any) -> Variant:
    """`DEC-005`, split into what a program can see and what only a human can.

    The lawful state names three selected institutions, leaves geography
    intentionally unnamed, and has conditioned public Trust releases competing
    with official summaries. Of the malformed states the design lists, only the
    reference faults are machine-visible: a missing or dangling decision or entity
    reference. Contradicting the geography decision, adjudicating complete
    holdings, collapsing the release model, or treating provenance as truth are
    all claims made in prose, so they are editorial and the checker must stay
    silent about them.
    """

    case = draw(
        st.sampled_from(
            [
                "three institutions, unnamed geography, conditioned releases",
                "post-alteration Trust formation with later deposits",
                "post-formation rolling deposits",
                "missing decision reference",
                "dangling entity reference",
                "dangling first dependency",
                "contradictory geography state",
                "complete-holdings adjudication",
                "hidden-only one-time release model",
                "provenance treated as truth",
            ]
        )
    )
    lawful_facts = {
        "three institutions, unnamed geography, conditioned releases": (
            "Three selected institutions hold deposits. The geography stays "
            "intentionally unnamed. Public Trust releases are conditioned and "
            "compete with official summaries."
        ),
        "post-alteration Trust formation with later deposits": (
            "The Trust forms after the alteration, and pre-Trust sources are "
            "deposited later."
        ),
        "post-formation rolling deposits": (
            "After formation the Trust accepts rolling deposits."
        ),
    }
    if case in lawful_facts:
        return Variant(
            label=case,
            valid=True,
            payload=nf.novel_extension(
                extension_id="EXT-DEC-005-LAWFUL",
                extension_kind="institution",
                fact=lawful_facts[case],
                authority_ref="DEC-005",
                affected_records=[
                    {"record_type": "POVProfile", "record_id": "POV-MARA"}
                ],
            ),
            requirement="14.2",
        )

    if case == "missing decision reference":
        return Variant(
            label=case,
            valid=False,
            payload=nf.novel_extension(
                extension_id="EXT-DEC-005-NO-AUTHORITY",
                extension_kind="institution",
                authority_ref=None,
            ),
            requirement="14.2",
        )
    if case == "dangling entity reference":
        return Variant(
            label=case,
            valid=False,
            payload=nf.novel_extension(
                extension_id="EXT-DEC-005-DANGLING-ENTITY",
                extension_kind="institution",
                authority_ref="DEC-005",
                affected_records=[
                    {"record_type": "POVProfile", "record_id": "POV-NOT-RECORDED"}
                ],
            ),
            requirement="14.2",
        )
    if case == "dangling first dependency":
        return Variant(
            label=case,
            valid=False,
            payload=nf.novel_extension(
                extension_id="EXT-DEC-005-DANGLING-DEPENDENCY",
                extension_kind="institution",
                authority_ref="DEC-005",
                first_dependency={
                    "record_type": "TimelineEntry",
                    "record_id": "TL-NOT-RECORDED",
                },
            ),
            requirement="14.2",
        )

    editorial_facts = {
        "contradictory geography state": (
            "The geography stays intentionally unnamed, and the deposit sits in a "
            "named real-world city."
        ),
        "complete-holdings adjudication": (
            "The Trust adjudicates its holdings as complete."
        ),
        "hidden-only one-time release model": (
            "The Trust releases once, to no one, and never again."
        ),
        "provenance treated as truth": (
            "A deposit's provenance settles whether its contents are true."
        ),
    }
    return Variant(
        label=case,
        valid=False,
        objective=False,
        payload=nf.novel_extension(
            extension_id="EXT-DEC-005-EDITORIAL",
            extension_kind="institution",
            fact=editorial_facts[case],
            authority_ref="DEC-005",
        ),
        requirement="14.2",
    )


@st.composite
def novel_extension_variants(draw: Any) -> Variant:
    """A NovelExtension's reference integrity and lifecycle state.

    These are the extension faults a program can see without reading meaning: an
    unknown kind or state, an unresolvable authority, dependency, or affected
    record, and a superseded extension with no superseding change.
    """

    case = draw(
        st.sampled_from(
            [
                "approved extension with resolvable references",
                "retired extension naming its superseding change",
                "unknown extension kind",
                "unknown extension state",
                "missing authority reference",
                "unresolvable dependency",
                "unresolvable affected record",
                "retired with no superseding change",
                "approved with a superseding change",
            ]
        )
    )
    table: Mapping[str, Tuple[bool, Dict[str, Any]]] = {
        "approved extension with resolvable references": (
            True,
            nf.novel_extension(),
        ),
        "retired extension naming its superseding change": (
            True,
            nf.novel_extension(
                state="retired",
                superseding_arc_change_id="ARC-CHANGE-FIXTURE-001",
            ),
        ),
        "unknown extension kind": (
            False,
            nf.novel_extension(extension_kind="an-unbudgeted-kind"),
        ),
        "unknown extension state": (
            False,
            nf.novel_extension(state="nearly-approved"),
        ),
        "missing authority reference": (
            False,
            nf.novel_extension(authority_ref=None),
        ),
        "unresolvable dependency": (
            False,
            nf.novel_extension(
                first_dependency={
                    "record_type": "TimelineEntry",
                    "record_id": "TL-NOT-RECORDED",
                }
            ),
        ),
        "unresolvable affected record": (
            False,
            nf.novel_extension(
                affected_records=[
                    {"record_type": "POVProfile", "record_id": "POV-NOT-RECORDED"}
                ]
            ),
        ),
        "retired with no superseding change": (
            False,
            nf.novel_extension(state="retired"),
        ),
        "approved with a superseding change": (
            False,
            nf.novel_extension(
                state="approved",
                superseding_arc_change_id="ARC-CHANGE-FIXTURE-001",
            ),
        ),
    }
    valid, payload = table[case]
    return Variant(label=case, valid=valid, payload=payload, requirement="14.2")


@st.composite
def dec_012_states(draw: Any) -> Variant:
    """`DEC-012`/`DEC-015`: coinage timing and the mechanism's limits.

    Every state here is a claim the extension's `fact` makes in prose. Whether the
    term is coined before Discovery, whether December carried a transmission,
    whether the modes are collapsed, whether `INTRUDE` is semantic, and whether
    arbitrary memory is read are all continuity judgments a human makes; the
    mechanism invariants the checker *can* enforce live in `technical_state`, and
    `technical_state_variants` covers those. So the malformed states here are
    editorial, and the property is that the checker records the extension without
    grading it.
    """

    case = draw(
        st.sampled_from(
            [
                "coinage after Discovery",
                "pre-Discovery coinage",
                "December transmission claimed",
                "modes collapsed",
                "semantic INTRUDE",
                "arbitrary memory reading",
            ]
        )
    )
    facts = {
        "coinage after Discovery": (
            True,
            "The term is coined during Private Defense, after Discovery.",
            "DEC-012",
        ),
        "pre-Discovery coinage": (
            False,
            "The term is already in use before Discovery begins.",
            "DEC-012",
        ),
        "December transmission claimed": (
            False,
            "December carried a transmission, not only reception.",
            "DEC-012",
        ),
        "modes collapsed": (
            False,
            "RECEIVE, INTRUDE, CANCEL, and PAIR are one channel.",
            "DEC-015",
        ),
        "semantic INTRUDE": (
            False,
            "INTRUDE reads the semantic content of a thought.",
            "DEC-015",
        ),
        "arbitrary memory reading": (
            False,
            "The apparatus reads arbitrary memory on demand.",
            "DEC-015",
        ),
    }
    valid, fact, authority = facts[case]
    return Variant(
        label=case,
        valid=valid,
        objective=valid,
        payload=nf.novel_extension(
            extension_id="EXT-DEC-012-{0}".format(
                "LAWFUL" if valid else "EDITORIAL"
            ),
            extension_kind="mechanism",
            fact=fact,
            authority_ref=authority,
        ),
        requirement="14.4",
    )


# ---------------------------------------------------------------------------
# Status changes, gates, and source trees
# ---------------------------------------------------------------------------


@st.composite
def status_changes(draw: Any) -> Variant:
    """An ArcChange, atomic or partially synchronized.

    Requirement 13.x makes a `complete` change atomic: every affected document
    has a completed obligation with evidence, plus an approval and a completion
    time. A `proposed` change with pending obligations is lawful; a `complete`
    change with a pending one is not.
    """

    documents = draw(
        st.lists(
            st.sampled_from(
                [
                    "planning/arc-outline.md",
                    "planning/timeline.md",
                    "planning/motif-ledger.md",
                    "planning/canon-bible.md",
                ]
            ),
            min_size=1,
            max_size=4,
            unique=True,
        )
    )
    case = draw(
        st.sampled_from(
            [
                "proposed change with pending obligations",
                "complete change with every obligation evidenced",
                "complete change with a pending obligation",
                "complete change with no approval",
                "complete change with no completion time",
                "obligation evidence recorded while still pending",
            ]
        )
    )
    if case == "proposed change with pending obligations":
        return Variant(label=case, valid=True,
                       payload=nf.arc_change(affected_documents=documents),
                       requirement="13.4")
    if case == "complete change with every obligation evidenced":
        return Variant(label=case, valid=True,
                       payload=nf.completed_arc_change(affected_documents=documents),
                       requirement="13.4")
    record = nf.completed_arc_change(affected_documents=documents)
    if case == "complete change with a pending obligation":
        obligations = [dict(item) for item in record["synchronization_obligations"]]
        target = draw(st.integers(min_value=0, max_value=len(obligations) - 1))
        obligations[target] = dict(obligations[target], status="pending",
                                  evidence_ref=None)
        record = dict(record, synchronization_obligations=obligations)
    elif case == "complete change with no approval":
        record = dict(record, approval=None)
    elif case == "complete change with no completion time":
        record = dict(record, completed_at=None)
    else:
        record = nf.arc_change(
            affected_documents=documents,
            synchronization_obligations=[
                nf.synchronization_obligation(
                    document=document,
                    status="pending",
                    evidence_ref="{0}#synchronized".format(document),
                )
                for document in documents
            ],
        )
    return Variant(label=case, valid=False, payload=record, requirement="13.4")


@st.composite
def gates(draw: Any) -> Variant:
    """A GateResult, consistent or contradicting its own exit status.

    An objective gate's `result` must agree with its recorded checker exit
    status; an editorial gate records no exit status at all, because no checker
    produced it.
    """

    case = draw(
        st.sampled_from(
            [
                "passing objective gate with exit 0",
                "revision-requiring objective gate with exit 1",
                "incomplete objective gate with exit 2",
                "passing editorial gate with a null exit status",
                "passing objective gate with a failing exit status",
                "revision-requiring objective gate with exit 0",
                "editorial gate claiming a checker exit status",
            ]
        )
    )
    table: Mapping[str, Tuple[bool, Dict[str, Any]]] = {
        "passing objective gate with exit 0": (
            True,
            nf.gate_result(result="pass", checker_exit_status=0),
        ),
        "revision-requiring objective gate with exit 1": (
            True,
            nf.gate_result(result="revision", checker_exit_status=1),
        ),
        "incomplete objective gate with exit 2": (
            True,
            nf.gate_result(result="incomplete", checker_exit_status=2),
        ),
        "passing editorial gate with a null exit status": (
            True,
            nf.editorial_gate_result(),
        ),
        "passing objective gate with a failing exit status": (
            False,
            nf.gate_result(result="pass", checker_exit_status=1),
        ),
        "revision-requiring objective gate with exit 0": (
            False,
            nf.gate_result(result="revision", checker_exit_status=0),
        ),
        "editorial gate claiming a checker exit status": (
            False,
            nf.editorial_gate_result(checker_exit_status=0),
        ),
    }
    valid, payload = table[case]
    return Variant(label=case, valid=valid, payload=payload, requirement="13.7")


@st.composite
def source_trees(draw: Any) -> Variant:
    """A source tree, with the excluded document present or absent.

    The excluded song may exist on disk; what matters is that it is never
    collected, published, or scanned. A tree that collects it is the malformed
    direction, and Chapter_File-only phrase scanning is the lawful one.
    """

    case = draw(
        st.sampled_from(
            [
                "five Canon_Sources collected, excluded song absent",
                "five Canon_Sources collected, excluded song present but uncollected",
                "excluded song collected",
                "Canon_Source song text scanned as Chapter_File prose",
            ]
        )
    )
    songs = {path: "[Verse]\nSynthetic source line.\n" for path in nf.CANON_SOURCE_PATHS}
    if case == "five Canon_Sources collected, excluded song absent":
        return Variant(label=case, valid=True, payload=dict(songs),
                       requirement="14.14")
    if case == "five Canon_Sources collected, excluded song present but uncollected":
        return Variant(
            label=case,
            valid=True,
            payload=dict(
                songs,
                **{nf.EXCLUDED_CANON_SOURCE_PATH: "[Verse]\nExcluded, not collected.\n"}
            ),
            requirement="14.14",
        )
    if case == "excluded song collected":
        return Variant(
            label=case,
            valid=False,
            payload=dict(
                songs,
                **{nf.EXCLUDED_CANON_SOURCE_PATH: "[Verse]\nCollected in error.\n"}
            ),
            requirement="14.14",
        )
    return Variant(
        label=case,
        valid=False,
        payload=dict(
            songs,
            **{"songs/Case Zero.md": "[Verse]\n" + nf.DID_I_SAY_YES + "\n"}
        ),
        requirement="14.14",
    )


# ---------------------------------------------------------------------------
# Whole-workspace strategies
# ---------------------------------------------------------------------------


@st.composite
def motif_ledgers(draw: Any) -> Variant:
    """The whole-book Motif_Ledger, complete or short one fixed event.

    Requirement 7.12 fixes two kettle events in the Coda and Requirement 7.17
    fixes three Record_Progression events across three movements. Dropping one,
    or moving one out of its movement, is the malformed direction.
    """

    ledger = list(nf.manuscript_motif_events())
    case = draw(
        st.sampled_from(
            [
                "the complete ledger",
                "a closed-family event dropped",
                "a closed-family event moved out of its movement",
                "an extra event added to a closed family",
            ]
        )
    )
    if case == "the complete ledger":
        return Variant(label=case, valid=True, payload=tuple(ledger),
                       requirement="7.12, 7.17")
    closed = [
        record
        for record in ledger
        if record["family"] in ("kettle", "record progression")
    ]
    target = draw(st.sampled_from(closed))
    if case == "a closed-family event dropped":
        return Variant(
            label=case + " (" + target["motif_event_id"] + ")",
            valid=False,
            payload=tuple(r for r in ledger if r is not target),
            requirement="7.12, 7.17",
        )
    if case == "a closed-family event moved out of its movement":
        moved = dict(
            target,
            movement=draw(
                st.sampled_from(
                    [m for m in nf.MOVEMENTS if m != target["movement"]]
                )
            ),
        )
        return Variant(
            label=case + " (" + target["motif_event_id"] + ")",
            valid=False,
            payload=tuple(moved if r is target else r for r in ledger),
            requirement="7.12, 7.17",
        )
    return Variant(
        label=case + " (" + target["family"] + ")",
        valid=False,
        payload=tuple(
            ledger
            + [
                nf.motif_event(
                    motif_event_id="MOT-EXTRA-01",
                    family=target["family"],
                    movement=target["movement"],
                    planned_chapter=target["planned_chapter"],
                )
            ]
        ),
        requirement="7.12, 7.17",
    )


@st.composite
def fluent_pairing_coverage(draw: Any) -> Variant:
    """Coverage of the five mandatory Fluent_Pairing ranges.

    Requirement 15.1 fixes the five ranges. Every range needs at least one `PAIR`
    session in it; leaving one uncovered is the malformed direction.
    """

    if draw(st.booleans()):
        return Variant(
            label="all five mandatory ranges covered",
            valid=True,
            payload=nf.fluent_pairing_timeline_entries(),
            requirement="15.1",
        )
    dropped = draw(st.sampled_from(list(nf.FLUENT_PAIRING_RANGES)))
    return Variant(
        label="range {0}-{1} uncovered".format(*dropped),
        valid=False,
        payload=nf.fluent_pairing_timeline_entries(
            ranges=[r for r in nf.FLUENT_PAIRING_RANGES if r != dropped]
        ),
        requirement="15.1",
    )


@st.composite
def final_targets(draw: Any) -> Variant:
    """Final_Targets against the observed manuscript, agreeing or not.

    Requirement 11.x makes the approved Final_Targets binding on the completed
    manuscript, so a target that the observed totals miss is a violation.
    """

    chapters = draw(st.integers(min_value=8, max_value=48))
    words = draw(st.integers(min_value=chapters * 700, max_value=chapters * 2500))
    case = draw(
        st.sampled_from(
            [
                "targets match the observed totals",
                "chapter count target missed",
                "word floor above the observed total",
                "word ceiling below the observed total",
            ]
        )
    )
    if case == "targets match the observed totals":
        return Variant(
            label=case,
            valid=True,
            payload=(
                {
                    "chapter_count": chapters,
                    "minimum_words": words,
                    "maximum_words": words,
                },
                chapters,
                words,
            ),
            requirement="11.9",
        )
    targets = {
        "chapter_count": chapters,
        "minimum_words": words,
        "maximum_words": words,
    }
    if case == "chapter count target missed":
        targets["chapter_count"] = chapters + draw(st.sampled_from([-2, -1, 1, 2]))
    elif case == "word floor above the observed total":
        targets["minimum_words"] = words + 1
        targets["maximum_words"] = words + 2
    else:
        targets["minimum_words"] = max(1, words - 2)
        targets["maximum_words"] = max(1, words - 1)
    return Variant(
        label=case, valid=False, payload=(targets, chapters, words), requirement="11.9"
    )


@st.composite
def normal_share_allocations(draw: Any) -> Variant:
    """A whole-book Length_Class allocation against the 80 percent normal floor.

    Requirement 3.x sets the floor. The verdict is computed with exact integer
    arithmetic from the design's rule, never from the checker, so a property test
    comparing the two is a real comparison.
    """

    total = draw(st.integers(min_value=5, max_value=60))
    normal = draw(st.integers(min_value=0, max_value=total))
    others = [c for c in nf.LENGTH_CLASSES if c != "normal"]
    allocation = ["normal"] * normal + [
        draw(st.sampled_from(others)) for _ in range(total - normal)
    ]
    return Variant(
        label="{0} of {1} chapters normal".format(normal, total),
        valid=normal * 100 >= total * 80,
        payload=tuple(allocation),
        requirement="3.6",
    )


@st.composite
def literal_phrase_placements(draw: Any) -> Variant:
    """The terminal protected phrase, in or out of its declared span.

    The rule fixes exactly two occurrences inside the declared Final_Passage and
    none outside it. Both the count and the span boundary matter, so both are
    varied independently.
    """

    case = draw(
        st.sampled_from(
            [
                "exactly two occurrences inside the span",
                "one occurrence inside the span",
                "three occurrences inside the span",
                "an occurrence before the span marker",
                "the span marker missing",
                "the span marker duplicated",
            ]
        )
    )
    filler = nf.prose_of_length(draw(st.integers(min_value=40, max_value=200)))
    marker = nf.FINAL_PASSAGE_MARKER
    phrase = nf.WHOSE_WAS_THAT
    bodies: Mapping[str, Tuple[bool, str]] = {
        "exactly two occurrences inside the span": (
            True,
            filler + marker + "\n" + phrase + " " + phrase + "\n",
        ),
        "one occurrence inside the span": (
            False,
            filler + marker + "\n" + phrase + "\n",
        ),
        "three occurrences inside the span": (
            False,
            filler + marker + "\n" + " ".join([phrase] * 3) + "\n",
        ),
        "an occurrence before the span marker": (
            False,
            filler + phrase + "\n" + marker + "\n" + phrase + " " + phrase + "\n",
        ),
        "the span marker missing": (False, filler + phrase + " " + phrase + "\n"),
        "the span marker duplicated": (
            False,
            filler + marker + "\n" + marker + "\n" + phrase + " " + phrase + "\n",
        ),
    }
    valid, body = bodies[case]
    return Variant(label=case, valid=valid, payload=body, requirement="7.20")


@st.composite
def scope_isolation_cases(draw: Any) -> Variant:
    """A whole-book fact a Chapter_Local_Gate must not be able to see.

    Requirement 10.9 makes this a claim about absence: the local gate has no
    access to Final_Targets, the whole-book POV distribution, cross-manuscript
    motif totals, movement length relationships, or final-ending acceptance.
    Every case here is a fact the local gate must stay silent about.
    """

    return Variant(
        label=draw(
            st.sampled_from(
                [
                    "Final_Targets",
                    "whole-book POV distribution",
                    "cross-manuscript motif family totals",
                    "movement length relationships",
                    "final-ending acceptance",
                ]
            )
        ),
        valid=True,
        payload=None,
        requirement="10.9",
    )
