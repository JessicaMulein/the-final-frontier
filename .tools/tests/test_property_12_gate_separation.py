"""Principal property test for design Property 12.

Property 12: Chapter-local and manuscript-global gate separation

Validates: Requirements 10.9
Related requirements: 10.1-10.5.

Owning task: 8.21. Reserved by task 7.1.

Feature: the-final-frontier-novel, Property 12: Chapter-local and
manuscript-global gate separation

What is being proved
--------------------
The Chapter_Local_Gate cannot see the whole book. Specifically, none of these can
change a chapter's local result:

* the approved Final_Targets;
* any other chapter, however broken;
* the whole-book POV distribution;
* cross-manuscript motif family totals;
* movement length relationships;
* final-ending acceptance and baseline approval.

This is a property about *absence*, which makes it the easiest one to fake and the
most important one to get right. A test that only checked "the local gate passes a
good chapter" would pass against a gate that read every whole-book document. So
the shape here is a differential: run the local gate on one unchanged chapter,
mutate the whole-book context arbitrarily, run it again, and require the two
results to be identical — not merely both passing.

The other direction is asserted too. A local defect must always fail the local
gate, or "the local gate ignores global facts" would be satisfied trivially by a
gate that ignored everything.

The mechanism that makes this true is structural rather than defensive:
`GLOBAL_RECORD_SOURCES` is a separate list, so the documents carrying
Final_Targets, gate results, and the editorial log are not even loaded for a
chapter scope. A chapter gate therefore cannot fail because a whole-book document
is missing, which is checked here directly.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import novel_fixtures as nf
import novel_strategies as ns

checker = nf.load_checker()

PROPERTY = "Property 12: Chapter-local and manuscript-global gate separation"
OWNING_TASK = "8.21"

PROPERTY_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[
        HealthCheck.too_slow,
        HealthCheck.data_too_large,
        HealthCheck.function_scoped_fixture,
    ],
)

# The chapter whose local result must stay fixed under every global mutation.
SUBJECT = 40

# The whole-book documents Requirement 10.9 keeps out of the Chapter_Local_Gate.
GLOBAL_ONLY_DOCUMENTS: Tuple[str, ...] = (
    "planning/arc-changes.md",
    "planning/gate-results.md",
    "planning/editorial-log.md",
)


@pytest.fixture(scope="module")
def manuscript(tmp_path_factory):
    """One complete clean manuscript, rebuilt per module rather than per example."""

    base = tmp_path_factory.mktemp("property-12")
    workspace = nf.manuscript_workspace(base)
    run = checker.run_scope(
        (), scope=checker.SCOPE_GLOBAL, manuscript_root=workspace.manuscript_root
    )
    assert run.diagnostics == (), [item.code for item in run.diagnostics]
    return workspace


def _local_codes(workspace: Any, chapter: int = SUBJECT) -> Tuple[str, ...]:
    """The Chapter_Local_Gate result for one chapter, as codes."""

    movement = nf.manuscript_movement_for_chapter(chapter)
    path = workspace.manuscript_root / nf.chapter_relative_path(
        movement, chapter, "chapter-{0:03d}".format(chapter)
    )
    run = checker.run_scope(
        (path,),
        scope=checker.SCOPE_CHAPTER,
        manuscript_root=workspace.manuscript_root,
    )
    return tuple(sorted(item.code for item in run.diagnostics))


def _chapter_path(workspace: Any, chapter: int) -> Path:
    return workspace.manuscript_root / nf.chapter_relative_path(
        nf.manuscript_movement_for_chapter(chapter),
        chapter,
        "chapter-{0:03d}".format(chapter),
    )


# ---------------------------------------------------------------------------
# Global facts never change a local result
# ---------------------------------------------------------------------------


@PROPERTY_SETTINGS
@given(st.sampled_from(GLOBAL_ONLY_DOCUMENTS))
def test_removing_a_whole_book_document_does_not_change_the_local_result(
    manuscript, document
):
    """Requirement 10.9: a chapter gate cannot fail for an absent global document.

    This is the structural guarantee behind the property. The documents holding
    Final_Targets, gate results, and the editorial log are in
    `GLOBAL_RECORD_SOURCES` only, so a chapter scope never loads them and cannot
    notice they are gone.
    """

    baseline = _local_codes(manuscript)
    path = manuscript.manuscript_root / document
    original = path.read_text(encoding="utf-8")
    path.unlink()
    try:
        after = _local_codes(manuscript)
    finally:
        path.write_text(original, encoding="utf-8")
    assert after == baseline, (document, baseline, after)


@PROPERTY_SETTINGS
@given(ns.chapter_numbers(minimum=1, maximum=128))
def test_breaking_an_unrelated_chapter_does_not_change_the_local_result(
    manuscript, other
):
    """Requirements 10.1 through 10.4: a chapter is judged on its own contents."""

    if other == SUBJECT:
        return
    baseline = _local_codes(manuscript)
    path = _chapter_path(manuscript, other)
    original = path.read_text(encoding="utf-8")
    # Corrupted past parsing: no header delimiters, no declared counts, nothing.
    path.write_text("not a chapter file at all\n", encoding="utf-8")
    try:
        after = _local_codes(manuscript)
    finally:
        path.write_text(original, encoding="utf-8")
    assert after == baseline, (other, baseline, after)


@PROPERTY_SETTINGS
@given(ns.chapter_numbers(minimum=1, maximum=128))
def test_deleting_an_unrelated_chapter_does_not_change_the_local_result(
    manuscript, other
):
    """A plan/file bijection failure is a whole-book finding, not a local one."""

    if other == SUBJECT:
        return
    baseline = _local_codes(manuscript)
    path = _chapter_path(manuscript, other)
    original = path.read_text(encoding="utf-8")
    path.unlink()
    try:
        after = _local_codes(manuscript)
    finally:
        path.write_text(original, encoding="utf-8")
    assert after == baseline, (other, baseline, after)


@PROPERTY_SETTINGS
@given(ns.final_targets())
def test_rewriting_the_final_targets_does_not_change_the_local_result(
    manuscript, variant
):
    """Requirement 10.9 names Final_Targets first: a chapter cannot see them."""

    baseline = _local_codes(manuscript)
    targets, chapters, words = variant.payload
    path = manuscript.manuscript_root / "planning" / "arc-outline.md"
    original = path.read_text(encoding="utf-8")
    rewritten = original.replace(
        '"chapter_count": 128', '"chapter_count": {0}'.format(targets["chapter_count"])
    )
    path.write_text(rewritten, encoding="utf-8")
    try:
        after = _local_codes(manuscript)
    finally:
        path.write_text(original, encoding="utf-8")
    assert after == baseline, (variant.label, baseline, after)


@PROPERTY_SETTINGS
@given(ns.scope_isolation_cases())
def test_every_named_global_fact_is_absent_from_the_chapter_gate(variant):
    """Requirement 10.9's list, checked against the checker's own scope wiring.

    Rather than restate the list in prose, this asserts the mechanism: the record
    sources a chapter scope loads are exactly the default set, and every
    additional whole-book document belongs to the global set alone.
    """

    assert set(checker.GLOBAL_RECORD_SOURCES) > set(checker.DEFAULT_RECORD_SOURCES)
    extra = set(checker.GLOBAL_RECORD_SOURCES) - set(checker.DEFAULT_RECORD_SOURCES)
    assert extra == set(GLOBAL_ONLY_DOCUMENTS), sorted(extra)
    assert variant.valid


# ---------------------------------------------------------------------------
# Local defects always fail locally
# ---------------------------------------------------------------------------

LOCAL_DEFECTS: Tuple[str, ...] = (
    "declared word count disagrees",
    "declared length class disagrees",
    "header key missing",
    "header delimiter broken",
    "unknown status",
    "motif assignment disagrees with the ledger",
)


@PROPERTY_SETTINGS
@given(st.sampled_from(LOCAL_DEFECTS))
def test_any_local_defect_always_fails_the_local_gate(manuscript, defect):
    """The other direction: a gate that ignored everything would be useless.

    Each defect is injected into the subject chapter alone, leaving the rest of
    the book untouched, so a diagnostic here can only come from the chapter's own
    contents.
    """

    path = _chapter_path(manuscript, SUBJECT)
    original = path.read_text(encoding="utf-8")
    header_lines, prose = checker.split_chapter_header(original, item="subject")
    header, _diagnostics = checker.parse_chapter_header_lines(
        header_lines, item="subject"
    )

    options: Dict[str, Any] = {}
    broken = dict(header)
    if defect == "declared word count disagrees":
        broken["words"] = int(broken["words"]) - 1
    elif defect == "declared length class disagrees":
        broken["length_class"] = "microchapter"
    elif defect == "header key missing":
        del broken["hook"]
    elif defect == "header delimiter broken":
        options = {"close_delimiter": "***"}
    elif defect == "unknown status":
        broken["status"] = "nearly-there"
    else:
        broken["motif_events"] = ["MOT-CHAIN-01"]

    path.write_text(
        nf.render_chapter_file(broken, prose, **options), encoding="utf-8"
    )
    try:
        codes = _local_codes(manuscript)
    finally:
        path.write_text(original, encoding="utf-8")
    assert codes != (), defect


@PROPERTY_SETTINGS
@given(ns.chapter_numbers(minimum=1, maximum=128))
def test_a_clean_chapter_passes_locally_wherever_it_sits(manuscript, chapter):
    """Every chapter of the clean manuscript passes its own local gate.

    Including chapter 73, which carries `Did I say yes?`, and chapter 128, whose
    terminal in-scope total is deliberately left to a scope containing the
    declared span.
    """

    assert _local_codes(manuscript, chapter) == ()
