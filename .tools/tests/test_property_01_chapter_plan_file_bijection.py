"""Principal property test for design Property 1.

Property 1: Chapter plan and file bijection

Validates: Requirements 11.3
Related requirements: 1.2, 1.3, 9.4, 12.2.

Owning task: 8.10. Reserved by task 7.1 so the property has exactly one principal
test and so an unimplemented property reads as an honest skip instead of as
coverage.

Feature: the-final-frontier-novel, Property 1: Chapter plan and file bijection

What is being proved
--------------------
The complete outline is exactly `1..N`, once each, in four ordered contiguous
movement blocks, and it maps one-to-one onto the Chapter_Files on disk. The
assertions run against the checker's own outline and bijection gates rather than
against a fixture helper, because a fixture that restated the rule would only
prove the fixture agrees with itself.

Both directions matter. A generated outline that conforms must draw no
diagnostic, and each named structural fault must be caught. The second half is
the part that fails if a check is quietly removed.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

import pytest
from hypothesis import HealthCheck, given, settings

import novel_fixtures as nf
import novel_strategies as ns

checker = nf.load_checker()

PROPERTY = "Property 1: Chapter plan and file bijection"
OWNING_TASK = "8.10"

PROPERTY_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def _arc_entries(payloads: Any) -> Tuple[Any, ...]:
    """Read generated ArcEntry payloads through the checker's own parser.

    Going through `parse_arc_entries` rather than constructing records directly
    means a generated entry reaches the gate the same way an authored one does,
    including any structural rejection the parser performs first.
    """

    document = nf.planning_document(
        "planning/arc-outline.md",
        title="Arc Outline",
        blocks=tuple(("ArcEntry", payload) for payload in payloads),
    )
    entries, _diagnostics = checker.parse_arc_entries(
        document.text(), source="planning/arc-outline.md"
    )
    return entries


def _plan_diagnostics(payloads: Any) -> Tuple[str, ...]:
    """Every code the outline-integrity gates report for one generated plan."""

    entries = _arc_entries(payloads)
    diagnostics = checker.check_outline_sequence(entries) + checker.check_movement_blocks(
        entries
    )
    return tuple(sorted({item.code for item in diagnostics}))


@PROPERTY_SETTINGS
@given(ns.conforming_outlines())
def test_a_conforming_outline_draws_no_structural_diagnostic(entries):
    """Requirement 1.3: a clean `1..N` plan in ordered blocks is silent."""

    assert _plan_diagnostics(entries) == ()


@PROPERTY_SETTINGS
@given(ns.outline_variants())
def test_every_named_outline_fault_is_caught(variant):
    """Requirement 11.3 and 1.2, one injected structural fault at a time."""

    codes = _plan_diagnostics(variant.payload)
    if variant.valid:
        assert codes == (), "{0} drew {1}".format(variant, codes)
    else:
        assert codes, "{0} drew no diagnostic".format(variant)


@PROPERTY_SETTINGS
@given(ns.movement_allocations())
def test_a_contiguous_allocation_is_accepted_at_any_block_size(allocation):
    """Requirement 11.4 fixes the block *order*, not the block sizes."""

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
    assert _plan_diagnostics(entries) == ()


# The bijection halves need real Chapter_Files, because the gate matches a plan
# entry against a file that exists on disk. Building the whole 128-chapter
# manuscript once and moving a single file per example keeps the property honest
# without writing the book a hundred times.
@pytest.fixture(scope="module")
def whole_manuscript(tmp_path_factory):
    """One complete, clean manuscript shared by the bijection tests."""

    base = tmp_path_factory.mktemp("property-01-manuscript")
    workspace = nf.manuscript_workspace(base)
    run = checker.run_scope(
        (), scope=checker.SCOPE_GLOBAL, manuscript_root=workspace.manuscript_root
    )
    assert run.diagnostics == (), "the baseline manuscript must start clean"
    return workspace


def _global_codes(workspace: Any) -> Tuple[str, ...]:
    run = checker.run_scope(
        (), scope=checker.SCOPE_GLOBAL, manuscript_root=workspace.manuscript_root
    )
    return tuple(sorted({item.code for item in run.diagnostics}))


@PROPERTY_SETTINGS
@given(ns.chapter_numbers(minimum=1, maximum=128))
def test_a_plan_entry_without_a_chapter_file_is_reported(whole_manuscript, missing):
    """Requirement 11.3, one half of the bijection: a plan entry with no file."""

    path = whole_manuscript.manuscript_root / nf.chapter_relative_path(
        nf.manuscript_movement_for_chapter(missing),
        missing,
        "chapter-{0:03d}".format(missing),
    )
    original = path.read_text(encoding="utf-8")
    path.unlink()
    try:
        codes = _global_codes(whole_manuscript)
    finally:
        path.write_text(original, encoding="utf-8")
    assert "OUTLINE_ENTRY_WITHOUT_FILE" in codes, codes


@PROPERTY_SETTINGS
@given(ns.chapter_numbers(minimum=1, maximum=128))
def test_a_chapter_file_without_a_plan_entry_is_reported(whole_manuscript, source):
    """Requirement 11.3, the other half: a file the plan never declared."""

    movement = nf.manuscript_movement_for_chapter(source)
    original = whole_manuscript.manuscript_root / nf.chapter_relative_path(
        movement, source, "chapter-{0:03d}".format(source)
    )
    # Sequence 900 is outside the planned 1..128 range, so no ArcEntry claims it.
    unplanned = whole_manuscript.manuscript_root / nf.chapter_relative_path(
        movement, 900, "unplanned-chapter"
    )
    unplanned.write_text(original.read_text(encoding="utf-8"), encoding="utf-8")
    try:
        codes = _global_codes(whole_manuscript)
    finally:
        unplanned.unlink()
    assert "CHAPTER_FILE_WITHOUT_OUTLINE_ENTRY" in codes, codes
