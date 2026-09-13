"""Principal property test for design Property 13.

Property 13: Fail-closed incomplete inputs and exit status

Validates: Requirements 12.9
Related requirements: 11.1, 11.2, 12.10, 12.14, 12.15.

Owning task: 8.22. Reserved by task 7.1.

Feature: the-final-frontier-novel, Property 13: Fail-closed incomplete inputs and
exit status

What is being proved
--------------------
The three-way exit mapping, in every scope:

* `2` for incomplete or unreadable input;
* `1` for one or more objective violations with nothing unreadable;
* `0` only for a complete, readable scope with zero violations.

Fail-closed is the whole idea, and it has a precise meaning here: `2` outranks `1`
outranks `0`. When the checker cannot read something, it must say so rather than
report the violations it happened to find in the parts it could read, because a
partial reading looks exactly like a clean one from the outside.

That is why `disposition` is separate from `severity` in the diagnostic record. An
unreadable input is not a severe violation, it is a different kind of thing, and
collapsing the two would let a missing document be "downgraded" to an ordinary
finding and then averaged away.

The exit status is always derived through `classify_result` and
`exit_status_for_result`, never compared against a literal, so the mapping has one
definition and this test checks that one.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import novel_fixtures as nf
import novel_strategies as ns

checker = nf.load_checker()

PROPERTY = "Property 13: Fail-closed incomplete inputs and exit status"
OWNING_TASK = "8.22"

PROPERTY_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[
        HealthCheck.too_slow,
        HealthCheck.data_too_large,
        HealthCheck.function_scoped_fixture,
    ],
)

# The scopes a run can be requested in. `SCOPE_PLANNING` is a diagnostic *label*
# for a finding about a planning document rather than a runnable scope, so it
# belongs in the classification tests below and not in the run tests.
RUNNABLE_SCOPES: Tuple[str, ...] = (
    checker.SCOPE_CHAPTER,
    checker.SCOPE_BATCH,
    checker.SCOPE_GLOBAL,
)
DIAGNOSTIC_SCOPES: Tuple[str, ...] = RUNNABLE_SCOPES + (checker.SCOPE_PLANNING,)

# Ways to make an input unreadable that have nothing to do with its content.
CORRUPTIONS: Tuple[str, ...] = (
    "removed",
    "emptied",
    "no header delimiters",
    "unclosed header",
    "two header blocks",
    "truncated mid-header",
    "binary bytes",
)


@pytest.fixture(scope="module")
def manuscript(tmp_path_factory):
    """One complete clean manuscript at exit 0, shared across examples."""

    base = tmp_path_factory.mktemp("property-13")
    workspace = nf.manuscript_workspace(base)
    run = checker.run_scope(
        (), scope=checker.SCOPE_GLOBAL, manuscript_root=workspace.manuscript_root
    )
    assert checker.exit_status_for_result(
        checker.classify_result(run.diagnostics)
    ) == 0
    return workspace


def _status(diagnostics: Sequence[Any]) -> int:
    """The one definition of the mapping, used everywhere in this module."""

    return checker.exit_status_for_result(checker.classify_result(diagnostics))


# ---------------------------------------------------------------------------
# The mapping itself
# ---------------------------------------------------------------------------


@PROPERTY_SETTINGS
@given(
    st.integers(min_value=0, max_value=4),
    st.integers(min_value=0, max_value=4),
    st.sampled_from(list(DIAGNOSTIC_SCOPES)),
)
def test_incomplete_outranks_violation_outranks_clean(violations, incompletes, scope):
    """Requirement 12.9: `2` outranks `1` outranks `0`, at any mixture.

    Generated as counts rather than as a fixed pair, so a mapping that only
    happened to work for one violation and one incomplete would fail.
    """

    diagnostics = [
        checker._diagnostic(
            "PROBE_VIOLATION",
            scope=scope,
            item="probe-{0}".format(index),
            observed="a synthetic objective violation",
            expected="no violation",
        )
        for index in range(violations)
    ] + [
        checker._diagnostic(
            "PROBE_INCOMPLETE",
            scope=scope,
            item="probe-{0}".format(index),
            observed="a synthetic unreadable input",
            expected="readable input",
            disposition=checker.DISPOSITION_INCOMPLETE,
        )
        for index in range(incompletes)
    ]
    expected = 2 if incompletes else (1 if violations else 0)
    assert _status(diagnostics) == expected, (violations, incompletes, scope)


@PROPERTY_SETTINGS
@given(st.integers(min_value=1, max_value=6), st.integers(min_value=1, max_value=6))
def test_an_unreadable_input_is_never_downgraded_to_a_violation(violations, incompletes):
    """Requirement 12.10: disposition is not severity, so `2` cannot be averaged away.

    However many ordinary violations accompany it, one unreadable input still
    produces `2`. A checker that ranked by count, or that treated incompleteness
    as merely another finding, would report `1` here and hide the fact that it
    never finished reading.
    """

    diagnostics = [
        checker._diagnostic(
            "PROBE_VIOLATION",
            scope=checker.SCOPE_GLOBAL,
            item="probe-{0}".format(index),
            observed="a synthetic objective violation",
            expected="no violation",
        )
        for index in range(violations)
    ] + [
        checker._diagnostic(
            "PROBE_INCOMPLETE",
            scope=checker.SCOPE_GLOBAL,
            item="probe",
            observed="a synthetic unreadable input",
            expected="readable input",
            disposition=checker.DISPOSITION_INCOMPLETE,
        )
        for _ in range(incompletes)
    ]
    assert _status(diagnostics) == 2


@PROPERTY_SETTINGS
@given(st.just(None))
def test_zero_diagnostics_is_the_only_route_to_zero(_unused):
    """`0` means complete, readable, and with nothing wrong; nothing else earns it."""

    assert _status(()) == 0


# ---------------------------------------------------------------------------
# Corrupted inputs in real scopes
# ---------------------------------------------------------------------------


def _corrupt(path: Path, corruption: str) -> None:
    """Damage one file in a way that has nothing to do with its content."""

    if corruption == "removed":
        path.unlink()
        return
    original = path.read_text(encoding="utf-8")
    header_lines, prose = checker.split_chapter_header(original, item=path.name)
    block = "\n".join(header_lines)
    if corruption == "emptied":
        path.write_text("", encoding="utf-8")
    elif corruption == "no header delimiters":
        path.write_text(block + "\n\n" + prose, encoding="utf-8")
    elif corruption == "unclosed header":
        path.write_text("---\n" + block + "\n\n" + prose, encoding="utf-8")
    elif corruption == "two header blocks":
        path.write_text(
            "---\n" + block + "\n---\n\n---\n" + block + "\n---\n\n" + prose,
            encoding="utf-8",
        )
    elif corruption == "truncated mid-header":
        path.write_text("---\n" + block[: len(block) // 2], encoding="utf-8")
    else:
        path.write_bytes(b"\x00\x01\x02 not text at all \xff\xfe")


@PROPERTY_SETTINGS
@given(st.sampled_from(CORRUPTIONS), ns.chapter_numbers(minimum=1, maximum=128))
def test_a_corrupted_chapter_yields_two_at_chapter_scope(manuscript, corruption, chapter):
    """Requirement 12.9: an unreadable Chapter_File is incomplete input, not a pass."""

    movement = nf.manuscript_movement_for_chapter(chapter)
    path = manuscript.manuscript_root / nf.chapter_relative_path(
        movement, chapter, "chapter-{0:03d}".format(chapter)
    )
    original = path.read_bytes()
    _corrupt(path, corruption)
    try:
        run = checker.run_scope(
            (path,),
            scope=checker.SCOPE_CHAPTER,
            manuscript_root=manuscript.manuscript_root,
        )
        status = _status(run.diagnostics)
    finally:
        path.write_bytes(original)
    assert status == 2, (corruption, chapter, [d.code for d in run.diagnostics])


@PROPERTY_SETTINGS
@given(st.sampled_from(CORRUPTIONS), ns.chapter_numbers(minimum=1, maximum=128))
def test_a_corrupted_chapter_yields_two_at_global_scope(manuscript, corruption, chapter):
    """One unreadable file makes the whole-book verdict incomplete, not failing.

    This is the case that matters most: the global gate has 127 readable chapters
    and could easily report a violation count instead of admitting it could not
    read the manuscript.
    """

    movement = nf.manuscript_movement_for_chapter(chapter)
    path = manuscript.manuscript_root / nf.chapter_relative_path(
        movement, chapter, "chapter-{0:03d}".format(chapter)
    )
    original = path.read_bytes()
    _corrupt(path, corruption)
    try:
        run = checker.run_scope(
            (),
            scope=checker.SCOPE_GLOBAL,
            manuscript_root=manuscript.manuscript_root,
        )
        status = _status(run.diagnostics)
    finally:
        path.write_bytes(original)
    assert status == 2, (corruption, chapter)


@PROPERTY_SETTINGS
@given(st.sampled_from(list(checker.GLOBAL_RECORD_SOURCES)))
def test_a_missing_record_source_yields_two_at_global_scope(manuscript, document):
    """Requirements 11.1 and 11.2: a required document that is absent is not a pass.

    Every record source the global gate requires is generated, so a check that
    only guarded the Arc_Outline would fail here.
    """

    path = manuscript.manuscript_root / document
    original = path.read_text(encoding="utf-8")
    path.unlink()
    try:
        run = checker.run_scope(
            (),
            scope=checker.SCOPE_GLOBAL,
            manuscript_root=manuscript.manuscript_root,
        )
        status = _status(run.diagnostics)
    finally:
        path.write_text(original, encoding="utf-8")
    assert status == 2, (document, [d.code for d in run.diagnostics])


@PROPERTY_SETTINGS
@given(st.sampled_from(list(checker.GLOBAL_RECORD_SOURCES)))
def test_a_malformed_record_fence_yields_two(manuscript, document):
    """Unparseable JSON in a required document is unreadable input.

    A record the checker cannot parse is not an absent record and not a wrong
    one; guessing which would be the checker inventing content.
    """

    path = manuscript.manuscript_root / document
    original = path.read_text(encoding="utf-8")
    path.write_text(
        original + "\n```json record=ArcEntry schema=1\n{not valid json,,,}\n```\n",
        encoding="utf-8",
    )
    try:
        run = checker.run_scope(
            (),
            scope=checker.SCOPE_GLOBAL,
            manuscript_root=manuscript.manuscript_root,
        )
        status = _status(run.diagnostics)
    finally:
        path.write_text(original, encoding="utf-8")
    assert status == 2, (document, [d.code for d in run.diagnostics])


@PROPERTY_SETTINGS
@given(ns.chapter_numbers(minimum=2, maximum=128))
def test_a_pure_violation_yields_one_not_two(manuscript, chapter):
    """Requirement 12.9: a readable manuscript with a real violation exits `1`.

    The injected fault is a declared word count that disagrees with the observed
    one: fully readable, unambiguously wrong. If this returned `2`, the checker
    would be treating every violation as unreadable input and the three-way
    mapping would collapse to two.
    """

    movement = nf.manuscript_movement_for_chapter(chapter)
    path = manuscript.manuscript_root / nf.chapter_relative_path(
        movement, chapter, "chapter-{0:03d}".format(chapter)
    )
    original = path.read_text(encoding="utf-8")
    header_lines, prose = checker.split_chapter_header(original, item="probe")
    header, _diagnostics = checker.parse_chapter_header_lines(
        header_lines, item="probe"
    )
    lying = dict(header, words=int(header["words"]) - 1)
    path.write_text(nf.render_chapter_file(lying, prose), encoding="utf-8")
    try:
        run = checker.run_scope(
            (path,),
            scope=checker.SCOPE_CHAPTER,
            manuscript_root=manuscript.manuscript_root,
        )
        status = _status(run.diagnostics)
        codes = [d.code for d in run.diagnostics]
    finally:
        path.write_text(original, encoding="utf-8")
    assert status == 1, (chapter, codes)
    assert all(
        d.disposition == checker.DISPOSITION_VIOLATION for d in run.diagnostics
    ), codes


@PROPERTY_SETTINGS
@given(st.sampled_from(list(RUNNABLE_SCOPES)))
def test_an_absent_manuscript_root_yields_two_in_every_scope(tmp_path, scope):
    """A scope pointed at nothing must not report success.

    The easiest way for a checker to be silently useless is to be aimed at an
    empty directory and say nothing, so every scope is generated here.
    """

    run = checker.run_scope(
        (), scope=scope, manuscript_root=tmp_path / "not-a-manuscript"
    )
    assert _status(run.diagnostics) == 2, scope
