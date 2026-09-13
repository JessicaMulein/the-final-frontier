"""Principal property test for design Property 3.

Property 3: Cross-cut graph symmetry

Validates: Requirements 1.6
Related requirements: 1.7.

Owning task: 8.12. Reserved by task 7.1.

Feature: the-final-frontier-novel, Property 3: Cross-cut graph symmetry

What is being proved
--------------------
A Cross_Cut is an undirected edge that both endpoints must declare. The literal
string `none` is the only way an ArcEntry says "no cross-cuts here"; an empty
list, a null, or an omitted key is missing input rather than a declaration of
absence, because those three are what a partially written record looks like and
the checker must not read them as a decision.

One-sided edges and edges naming a chapter that does not exist always fail. The
generated graphs vary in size and in which endpoint is dropped, so a reciprocity
check that only ever looked at the lower-numbered chapter would be caught.
"""

from __future__ import annotations

from typing import Any, Dict, List, Sequence, Tuple

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import novel_fixtures as nf
import novel_strategies as ns

checker = nf.load_checker()

PROPERTY = "Property 3: Cross-cut graph symmetry"
OWNING_TASK = "8.12"

PROPERTY_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

CHAPTER_COUNT = 12


def _codes(
    cuts: Sequence[Dict[str, Any]],
    declarations: Dict[int, Any],
    *,
    scope: Sequence[int] = tuple(range(1, CHAPTER_COUNT + 1)),
) -> Tuple[str, ...]:
    """Cross_Cut diagnostics for one generated graph, through the checker's gate.

    `declarations` maps a chapter to whatever its ArcEntry puts in `cross_cuts`,
    so a test can supply `none`, a list of IDs, or a malformed value without the
    builder normalizing it away.
    """

    entries = [
        nf.arc_entry(
            chapter=chapter,
            movement="discovery_part",
            slug="chapter-{0:03d}".format(chapter),
            cross_cuts=declarations.get(chapter, "none"),
        )
        for chapter in range(1, CHAPTER_COUNT + 1)
    ]
    index = nf.record_index(CrossCut=list(cuts), arc_entries=entries)
    diagnostics = checker.check_cross_cut_references(index, batch_scope=tuple(scope))
    return tuple(sorted({item.code for item in diagnostics}))


@PROPERTY_SETTINGS
@given(ns.cross_cut_graphs(chapters=CHAPTER_COUNT))
def test_a_reciprocal_graph_draws_no_diagnostic(cuts):
    """Requirement 1.6: every endpoint declares the edge, so the graph is silent."""

    declarations: Dict[int, List[str]] = {}
    for cut in cuts:
        for chapter in cut["chapters"]:
            declarations.setdefault(chapter, []).append(cut["cross_cut_id"])
    assert _codes(cuts, declarations) == ()


@PROPERTY_SETTINGS
@given(ns.cross_cut_graphs(chapters=CHAPTER_COUNT), st.integers(min_value=0, max_value=5))
def test_a_one_sided_edge_always_fails(cuts, dropped):
    """Requirement 1.6: an edge one endpoint never declared is not an edge."""

    target = cuts[dropped % len(cuts)]
    declarations: Dict[int, List[str]] = {}
    for cut in cuts:
        for chapter in cut["chapters"]:
            declarations.setdefault(chapter, []).append(cut["cross_cut_id"])
    # Remove the declaration from the *higher*-numbered endpoint as well as the
    # lower one across examples, so a check that only inspected one side fails.
    endpoint = target["chapters"][dropped % len(target["chapters"])]
    declarations[endpoint] = [
        value
        for value in declarations[endpoint]
        if value != target["cross_cut_id"]
    ]
    if not declarations[endpoint]:
        declarations[endpoint] = "none"
    assert _codes(cuts, declarations) != ()


@PROPERTY_SETTINGS
@given(ns.cross_cut_graphs(chapters=CHAPTER_COUNT))
def test_a_declaration_naming_no_record_is_a_dangling_reference(cuts):
    """Requirement 1.7: an ArcEntry cannot cite a Cross_Cut that does not exist.

    This is decidable from the declaring chapter alone, so it is reported whenever
    that chapter is in scope, without waiting for the other endpoint.
    """

    declarations = {1: ["CUT-NOT-RECORDED"]}
    for cut in cuts:
        for chapter in cut["chapters"]:
            declarations.setdefault(chapter, []).append(cut["cross_cut_id"])
    codes = _codes(cuts, declarations)
    assert "CROSS_CUT_REFERENCE_DANGLING" in codes, codes


@PROPERTY_SETTINGS
@given(ns.cross_cut_graphs(chapters=CHAPTER_COUNT))
def test_an_edge_naming_a_chapter_outside_the_plan_fails_at_whole_book_scope(cuts):
    """Requirement 1.6: a chapter that does not exist cannot declare its half.

    A nonexistent endpoint can never reciprocate, so at whole-book scope the edge
    is one-sided by construction. Scoped to the chapters that *do* exist the
    checker stays silent instead, because reciprocity is then undecidable, and
    that restraint is what the next test pins down.
    """

    declarations = {1: ["CUT-OUTSIDE-PLAN"]}
    for cut in cuts:
        for chapter in cut["chapters"]:
            declarations.setdefault(chapter, []).append(cut["cross_cut_id"])
    outside = nf.cross_cut(
        cross_cut_id="CUT-OUTSIDE-PLAN", chapters=(1, CHAPTER_COUNT + 500)
    )
    entries = [
        nf.arc_entry(
            chapter=chapter,
            movement="discovery_part",
            slug="chapter-{0:03d}".format(chapter),
            cross_cuts=declarations.get(chapter, "none"),
        )
        for chapter in range(1, CHAPTER_COUNT + 1)
    ]
    index = nf.record_index(
        CrossCut=list(cuts) + [outside], arc_entries=entries
    )
    whole_book = {
        item.code for item in checker.check_cross_cut_references(index)
    }
    assert "CROSS_CUT_ONE_SIDED" in whole_book, sorted(whole_book)


@PROPERTY_SETTINGS
@given(st.sampled_from([[], None, "", "None", "NONE", ["none"]]))
def test_none_is_the_only_declaration_of_absence(empty_value):
    """Requirement 1.6: an empty list or a null is missing input, not a decision.

    `none` alone means "considered, and there are none". Everything else here is
    what a half-written record looks like, and reading any of them as absence
    would let an unfinished entry pass as a finished one.
    """

    codes = _codes((), {1: empty_value})
    assert codes != (), "{0!r} was accepted as a declaration of absence".format(
        empty_value
    )


@PROPERTY_SETTINGS
@given(ns.cross_cut_graphs(chapters=CHAPTER_COUNT))
def test_reciprocity_is_not_judged_outside_the_requested_scope(cuts):
    """Requirement 1.6 needs every participant, so a partial scope stays quiet.

    Reciprocity is undecidable when one endpoint is out of scope. Reporting it
    anyway would make a chapter gate fail for a fact it cannot see, which is the
    separation Property 12 protects.
    """

    declarations: Dict[int, List[str]] = {}
    for cut in cuts:
        for chapter in cut["chapters"]:
            declarations.setdefault(chapter, []).append(cut["cross_cut_id"])
    partner = max(chapter for cut in cuts for chapter in cut["chapters"])
    codes = _codes(cuts, declarations, scope=(partner,))
    assert "CROSS_CUT_ONE_SIDED" not in codes, codes
