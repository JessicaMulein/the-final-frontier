"""Principal property test for design Property 6.

Property 6: Ordered movement architecture and scale

Validates: Requirements 11.4
Related requirements: 2.1-2.3, 3.1, 3.6-3.8, 11.5, 11.6, 12.7, 15.5.

Owning task: 8.15. Reserved by task 7.1.

Feature: the-final-frontier-novel, Property 6: Ordered movement architecture and
scale

What is being proved
--------------------
Four claims about the shape of the whole book:

* the four movements form contiguous blocks in the required order (11.4, 3.1);
* the approved Final_Targets bind the finished manuscript, with the word range
  read as *inclusive* on both ends (11.5, 12.7);
* Mindwars is strictly the longest movement by Prose_Words (3.7, 11.6);
* the Coda is strictly the shortest (3.8, 11.6).

Both scale relationships are evaluated only when all four movements have a total.
That restraint is itself part of the property: three totals cannot settle a
four-way comparison, so a partially drafted book must come back incomplete rather
than have the checker guess from what happens to exist. A test that only ever
generated complete manuscripts would not notice the difference.

The provisional 29/32/51/16 allocation is generated alongside its boundary
variants, so the property covers the design's actual plan and its neighbours
rather than only convenient small numbers.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st

import novel_fixtures as nf
import novel_strategies as ns

checker = nf.load_checker()

PROPERTY = "Property 6: Ordered movement architecture and scale"
OWNING_TASK = "8.15"

PROPERTY_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

MINDWARS = "mindwars_part"
CODA = "aftermath_coda"

# The design's provisional allocation, and the neighbours a boundary error would
# land on. Transcribed from Requirement 15.5 rather than imported.
PROVISIONAL_ALLOCATION: Mapping[str, int] = {
    "discovery_part": 29,
    "private_defense_part": 32,
    "mindwars_part": 51,
    "aftermath_coda": 16,
}


def _outline(allocation: Mapping[str, int]) -> Tuple[Any, ...]:
    """ArcEntry records realizing one allocation as ordered contiguous blocks."""

    payloads: List[Dict[str, Any]] = []
    chapter = 0
    for movement in nf.MOVEMENTS:
        for _ in range(int(allocation.get(movement, 0))):
            chapter += 1
            payloads.append(
                nf.arc_entry(
                    chapter=chapter,
                    movement=movement,
                    slug="chapter-{0:03d}".format(chapter),
                )
            )
    document = nf.planning_document(
        "planning/arc-outline.md",
        title="Arc Outline",
        blocks=tuple(("ArcEntry", payload) for payload in payloads),
    )
    entries, _diagnostics = checker.parse_arc_entries(
        document.text(), source="planning/arc-outline.md"
    )
    return entries


@PROPERTY_SETTINGS
@given(ns.movement_allocations())
def test_any_contiguous_ordered_allocation_is_accepted(allocation):
    """Requirement 11.4 constrains block order and contiguity, not block size."""

    diagnostics = checker.check_movement_blocks(_outline(allocation))
    assert diagnostics == (), [item.code for item in diagnostics]


@PROPERTY_SETTINGS
@given(st.integers(min_value=-3, max_value=3), st.integers(min_value=-3, max_value=3))
def test_the_provisional_allocation_and_its_neighbours_are_accepted(shift, spread):
    """Requirement 15.5's 29/32/51/16 plan, and the counts just around it."""

    allocation = dict(PROVISIONAL_ALLOCATION)
    allocation[MINDWARS] = allocation[MINDWARS] + shift
    allocation[CODA] = allocation[CODA] + spread
    assume(all(count >= 1 for count in allocation.values()))
    diagnostics = checker.check_movement_blocks(_outline(allocation))
    assert diagnostics == (), [item.code for item in diagnostics]


@PROPERTY_SETTINGS
@given(ns.outline_variants())
def test_a_broken_block_structure_is_always_reported(variant):
    """Requirement 11.4 and 1.2: an out-of-order or split block never passes."""

    entries = _outline_from_payloads(variant.payload)
    diagnostics = checker.check_movement_blocks(
        entries
    ) + checker.check_outline_sequence(entries)
    if variant.valid:
        assert diagnostics == (), [item.code for item in diagnostics]
    else:
        assert diagnostics, "{0} drew no diagnostic".format(variant)


def _outline_from_payloads(payloads: Sequence[Mapping[str, Any]]) -> Tuple[Any, ...]:
    document = nf.planning_document(
        "planning/arc-outline.md",
        title="Arc Outline",
        blocks=tuple(("ArcEntry", payload) for payload in payloads),
    )
    entries, _diagnostics = checker.parse_arc_entries(
        document.text(), source="planning/arc-outline.md"
    )
    return entries


# ---------------------------------------------------------------------------
# Movement scale
# ---------------------------------------------------------------------------


@PROPERTY_SETTINGS
@given(
    st.integers(min_value=2000, max_value=40000),
    st.integers(min_value=2000, max_value=40000),
    st.integers(min_value=2000, max_value=40000),
    st.integers(min_value=2000, max_value=40000),
)
def test_the_scale_relationships_are_strict_and_two_sided(
    discovery, defense, mindwars, coda
):
    """Requirements 3.7 and 3.8: Mindwars strictly longest, Coda strictly shortest.

    The expected verdict is recomputed from the requirement, so this catches a
    comparison that is accidentally non-strict as well as one that is missing.
    """

    totals = {
        "discovery_part": discovery,
        "private_defense_part": defense,
        MINDWARS: mindwars,
        CODA: coda,
    }
    others = [value for key, value in totals.items() if key != MINDWARS]
    not_coda = [value for key, value in totals.items() if key != CODA]
    expected = not (mindwars > max(others) and coda < min(not_coda))
    codes = {item.code for item in checker.check_movement_scale(totals)}
    assert bool(codes) == expected, (totals, sorted(codes))


@PROPERTY_SETTINGS
@given(st.sampled_from(list(nf.MOVEMENTS)))
def test_a_missing_movement_total_is_incomplete_not_a_verdict(absent):
    """Requirement 11.6: three totals cannot decide a four-way comparison.

    The checker must decline rather than compare what it has, because an absent
    movement is a manuscript still being written, not a manuscript that failed.
    """

    totals = {
        "discovery_part": 10000,
        "private_defense_part": 12000,
        MINDWARS: 30000,
        CODA: 5000,
    }
    del totals[absent]
    diagnostics = checker.check_movement_scale(totals)
    assert diagnostics, "an absent movement must be reported"
    assert all(
        item.disposition == checker.DISPOSITION_INCOMPLETE for item in diagnostics
    ), [(item.code, item.disposition) for item in diagnostics]


@PROPERTY_SETTINGS
@given(st.integers(min_value=5000, max_value=30000))
def test_a_tie_for_longest_is_not_the_longest(shared):
    """"Strictly the longest" excludes a tie, which a `>=` comparison would allow."""

    totals = {
        "discovery_part": shared,
        "private_defense_part": shared // 2,
        MINDWARS: shared,
        CODA: shared // 4,
    }
    codes = {item.code for item in checker.check_movement_scale(totals)}
    assert "MOVEMENT_SCALE_MINDWARS_NOT_LONGEST" in codes, sorted(codes)


@PROPERTY_SETTINGS
@given(st.integers(min_value=5000, max_value=30000))
def test_a_tie_for_shortest_is_not_the_shortest(shared):
    """The same strictness on the other end of the book."""

    totals = {
        "discovery_part": shared,
        "private_defense_part": shared * 2,
        MINDWARS: shared * 4,
        CODA: shared,
    }
    codes = {item.code for item in checker.check_movement_scale(totals)}
    assert "MOVEMENT_SCALE_CODA_NOT_SHORTEST" in codes, sorted(codes)


# ---------------------------------------------------------------------------
# Final_Targets
# ---------------------------------------------------------------------------


@PROPERTY_SETTINGS
@given(ns.final_targets())
def test_final_targets_bind_the_observed_totals(variant):
    """Requirements 11.5 and 12.7: the approved targets are binding, not advisory."""

    targets, chapters, words = variant.payload
    diagnostics = checker.check_final_targets(
        checker.FinalTargets(
            chapter_count=int(targets["chapter_count"]),
            minimum_words=int(targets["minimum_words"]),
            maximum_words=int(targets["maximum_words"]),
        ),
        chapter_count=chapters,
        total_words=words,
    )
    codes = sorted({item.code for item in diagnostics})
    assert bool(codes) != variant.valid, "{0} drew {1}".format(variant, codes)


@PROPERTY_SETTINGS
@given(
    st.integers(min_value=120, max_value=135),
    st.integers(min_value=130000, max_value=149000),
    st.integers(min_value=0, max_value=1000),
)
def test_the_final_target_word_range_is_inclusive_on_both_ends(
    chapters, floor, span
):
    """Requirement 11.5's range includes both endpoints, and excludes neither.

    An exclusive comparison would reject a manuscript that landed exactly on its
    approved floor or ceiling, which is the one outcome the author aimed for.
    """

    ceiling = floor + span
    targets = checker.FinalTargets(
        chapter_count=chapters, minimum_words=floor, maximum_words=ceiling
    )
    for total in (floor, ceiling):
        diagnostics = checker.check_final_targets(
            targets, chapter_count=chapters, total_words=total
        )
        assert diagnostics == (), (total, [item.code for item in diagnostics])
    for total in (floor - 1, ceiling + 1):
        diagnostics = checker.check_final_targets(
            targets, chapter_count=chapters, total_words=total
        )
        assert diagnostics, total


@PROPERTY_SETTINGS
@given(st.integers(min_value=120, max_value=135), st.sampled_from([-2, -1, 1, 2]))
def test_the_final_target_chapter_count_is_exact(chapters, delta):
    """Requirement 11.5 fixes an exact count, so one chapter either way fails."""

    targets = checker.FinalTargets(
        chapter_count=chapters, minimum_words=130000, maximum_words=150000
    )
    diagnostics = checker.check_final_targets(
        targets, chapter_count=chapters + delta, total_words=140000
    )
    codes = {item.code for item in diagnostics}
    assert "FINAL_TARGET_CHAPTER_COUNT" in codes, sorted(codes)


@PROPERTY_SETTINGS
@given(st.integers(min_value=1, max_value=200), st.integers(min_value=1, max_value=200000))
def test_absent_targets_are_not_this_check_s_business(chapters, words):
    """A `None` target set is the Baseline's missing prerequisite, reported there.

    Reporting it twice would make one missing record look like two problems, and
    would put a Final_Prerequisite failure in the wrong place.
    """

    assert checker.check_final_targets(None, chapter_count=chapters, total_words=words) == ()
