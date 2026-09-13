"""Principal property test for design Property 8.

Property 8: POV run cap and run word limit

Validates: Requirements 2.7, 2.15, 11.12
Related requirements: 11.4. The Mindwars turnover cadence formerly cited here is
now Editorial_Review criterion 15.6, because Requirement 12.12 excludes pacing
from automated evaluation.

Owning task: 8.17. Reserved by task 7.1.

Feature: the-final-frontier-novel, Property 8: POV run cap and run word limit

What is being proved
--------------------
A Same_POV_Run is bounded twice, and the two bounds are independent:

* at most three consecutive Chapter_Files may share a POV_ID (Requirement 2.7);
* those chapters may total at most 3,600 Prose_Words (Requirement 2.15).

Independence is the whole point. A three-chapter run of 1,201-word chapters
satisfies the chapter bound and breaks the word bound. A four-chapter run of
300-word chapters does the reverse. A checker that enforced only one of them, or
that folded them into a single average, would pass a test that generated only
comfortable cases, so both extremes are generated explicitly.

Requirement 11.12 supplies the third rule: a run of two or more chapters whose
word total cannot be computed is incomplete input, not a silent pass. An
uncomputable run must never be treated as a short one.

No pacing or turnover judgment belongs here. How often a POV *should* change is
Editorial_Review criterion 15.6, and Requirement 12.12 keeps it out of the
checker entirely.
"""

from __future__ import annotations

from typing import Any, List, Optional, Sequence, Tuple

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import novel_fixtures as nf
import novel_strategies as ns

checker = nf.load_checker()

PROPERTY = "Property 8: POV run cap and run word limit"
OWNING_TASK = "8.17"

PROPERTY_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

# The two bounds, transcribed from Requirements 2.7 and 2.15 rather than imported
# from the checker, so this test measures the checker against the requirement.
CHAPTER_LIMIT = 3
WORD_LIMIT = 3600


def _codes(assignments: Sequence[Tuple[int, str, Optional[int]]]) -> Tuple[str, ...]:
    """Run diagnostics for one `(chapter, pov_id, words)` sequence."""

    runs = checker.pov_runs(tuple(assignments))
    diagnostics = checker.check_pov_runs(
        runs, scope=checker.SCOPE_PLANNING, source="planning/arc-outline.md"
    )
    return tuple(sorted({item.code for item in diagnostics}))


def _expected_faults(
    assignments: Sequence[Tuple[int, str, Optional[int]]]
) -> Tuple[bool, bool, bool]:
    """Whether the sequence breaks the chapter bound, the word bound, or is unknown.

    Runs are grouped by adjacency in the given order, which is how the design
    defines a Same_POV_Run: consecutive Chapter_Files, not consecutive numbers.
    """

    over_chapters = False
    over_words = False
    unknown = False
    run: List[Tuple[int, str, Optional[int]]] = []

    def close(group: Sequence[Tuple[int, str, Optional[int]]]) -> None:
        nonlocal over_chapters, over_words, unknown
        if not group:
            return
        if len(group) > CHAPTER_LIMIT:
            over_chapters = True
        words = [item[2] for item in group]
        if len(group) >= 2 and any(value is None for value in words):
            unknown = True
        elif all(value is not None for value in words):
            if sum(value for value in words if value is not None) > WORD_LIMIT:
                over_words = True

    for item in assignments:
        if run and item[1] != run[-1][1]:
            close(run)
            run = []
        run.append(item)
    close(run)
    return over_chapters, over_words, unknown


@PROPERTY_SETTINGS
@given(ns.pov_assignments(words=(400, 1100)))
def test_a_sequence_inside_both_bounds_is_silent(assignments):
    """Requirements 2.7 and 2.15: a conforming sequence draws no diagnostic."""

    assert _codes(assignments) == ()


@PROPERTY_SETTINGS
@given(ns.pov_run_variants())
def test_each_named_bound_is_enforced_on_its_own(variant):
    """One bound crossed per draw, so a diagnostic names a single cause."""

    codes = _codes(variant.payload)
    if variant.valid:
        assert codes == (), "{0} drew {1}".format(variant, codes)
    else:
        assert codes, "{0} drew no diagnostic".format(variant)


@PROPERTY_SETTINGS
@given(st.integers(min_value=CHAPTER_LIMIT + 1, max_value=8), ns.stable_ids("POV"))
def test_a_run_longer_than_three_chapters_fails_even_when_short(length, pov_id):
    """Requirement 2.7 counts chapters, so tiny chapters do not buy a fourth one."""

    # Every chapter is small enough that the whole run is far under the word
    # bound, which isolates the chapter-count bound completely.
    per_chapter = WORD_LIMIT // (length + 2)
    assignments = tuple(
        (chapter, pov_id, per_chapter) for chapter in range(1, length + 1)
    )
    assert sum(item[2] for item in assignments) <= WORD_LIMIT
    assert _codes(assignments) != ()


@PROPERTY_SETTINGS
@given(st.integers(min_value=WORD_LIMIT + 1, max_value=WORD_LIMIT + 2000), ns.stable_ids("POV"))
def test_a_two_chapter_run_over_the_word_bound_fails(total, pov_id):
    """Requirement 2.15 counts words, so a legal-length run can still be too long.

    Two chapters is well inside the chapter bound, which isolates the word bound.
    """

    first = total // 2
    assignments = ((1, pov_id, first), (2, pov_id, total - first))
    assert len(assignments) <= CHAPTER_LIMIT
    assert _codes(assignments) != ()


@PROPERTY_SETTINGS
@given(st.integers(min_value=WORD_LIMIT // CHAPTER_LIMIT + 1, max_value=2500), ns.stable_ids("POV"))
def test_a_three_chapter_run_over_the_word_bound_fails(per_chapter, pov_id):
    """The exact case the design calls out: three chapters totalling over 3,600."""

    assignments = tuple((chapter, pov_id, per_chapter) for chapter in range(1, 4))
    assert len(assignments) == CHAPTER_LIMIT
    assert sum(item[2] for item in assignments) > WORD_LIMIT
    assert _codes(assignments) != ()


@PROPERTY_SETTINGS
@given(ns.stable_ids("POV"))
def test_the_word_bound_is_inclusive_at_exactly_three_thousand_six_hundred(pov_id):
    """"At most 3,600" includes 3,600, and excludes 3,601."""

    at_limit = ((1, pov_id, 1200), (2, pov_id, 1200), (3, pov_id, 1200))
    over_limit = ((1, pov_id, 1200), (2, pov_id, 1200), (3, pov_id, 1201))
    assert _codes(at_limit) == ()
    assert _codes(over_limit) != ()


@PROPERTY_SETTINGS
@given(st.integers(min_value=2, max_value=CHAPTER_LIMIT), ns.stable_ids("POV"))
def test_an_uncomputable_multi_chapter_run_is_incomplete_not_passing(length, pov_id):
    """Requirement 11.12: an unknown word total is missing input, never a pass.

    Treating an uncomputable run as zero words would let an unfinished plan slip
    through the bound it exists to enforce.
    """

    assignments = tuple(
        (chapter, pov_id, None if chapter == 1 else 900)
        for chapter in range(1, length + 1)
    )
    diagnostics = checker.check_pov_runs(
        checker.pov_runs(assignments),
        scope=checker.SCOPE_PLANNING,
        source="planning/arc-outline.md",
    )
    assert diagnostics, "an unknown total must be reported"
    assert all(
        item.disposition == checker.DISPOSITION_INCOMPLETE for item in diagnostics
    ), [(item.code, item.disposition) for item in diagnostics]


@PROPERTY_SETTINGS
@given(ns.stable_ids("POV"))
def test_a_single_chapter_run_may_omit_its_word_count(pov_id):
    """A one-chapter run has nothing to sum, so a null count is not yet a fault.

    Requirement 11.12 asks for the total of a *run*; a lone chapter's estimate is
    still owed elsewhere, but it is not this rule's business.
    """

    assert _codes(((1, pov_id, None),)) == ()


@PROPERTY_SETTINGS
@given(ns.pov_assignments(chapters=24, max_run=6, words=(200, 2000)))
def test_the_checker_agrees_with_the_requirement_on_arbitrary_sequences(assignments):
    """The general claim: the checker reports exactly when a bound is broken.

    The expected verdict is recomputed here from Requirements 2.7, 2.15, and
    11.12, so this is the one assertion that would catch a bound the checker
    enforces *too* eagerly as well as one it misses.
    """

    over_chapters, over_words, unknown = _expected_faults(assignments)
    codes = _codes(assignments)
    assert bool(codes) == (over_chapters or over_words or unknown), (
        assignments,
        codes,
    )


@PROPERTY_SETTINGS
@given(ns.conforming_outlines())
def test_runs_are_read_from_arc_entry_estimates_at_planning_time(entries):
    """Requirement 11.12: before prose exists, the bound is read from estimates.

    A planning-time run is assembled from `ArcEntry.estimated_words`, which is why
    those estimates are required for a run of two or more.
    """

    document = nf.planning_document(
        "planning/arc-outline.md",
        title="Arc Outline",
        blocks=tuple(("ArcEntry", entry) for entry in entries),
    )
    parsed, _diagnostics = checker.parse_arc_entries(
        document.text(), source="planning/arc-outline.md"
    )
    assignments = checker.arc_entry_pov_assignments(parsed)
    assert len(assignments) == len(entries)
    assert all(item[2] is not None for item in assignments)
