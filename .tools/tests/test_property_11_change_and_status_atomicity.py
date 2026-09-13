"""Principal property test for design Property 11.

Property 11: Post-baseline change and status atomicity

Validates: Requirements 1.16
Related requirements: 1.17, 1.18, 7.3, 10.7, 10.8, 13.7-13.10.

Owning task: 8.20. Reserved by task 7.1.

Feature: the-final-frontier-novel, Property 11: Post-baseline change and status
atomicity

What is being proved
--------------------
Once a Baseline is approved, changing anything is a recorded event rather than an
edit. Two rules, both all-or-nothing:

* every changed arc, continuity, motif, POV, or voice state carries a `complete`
  ArcChange, and `complete` means every affected document has a satisfied
  synchronization obligation with evidence, plus an approval and a completion
  time (1.16-1.18, 13.7-13.10);
* a Substantive_Prose_Change demotes both the Chapter_Header and its ArcEntry to
  `revised` until the affected gates pass again (10.7, 10.8).

Atomicity is what makes this a property rather than a checklist. A change that is
half-recorded is not a smaller change, it is an inconsistent manuscript: the
outline says one thing and the timeline says another, and no reader can tell which
is current. So the generated ArcChanges leave exactly one obligation short at a
time, and every one of those must fail.

The demotion rule runs the other way round from most checks here. It does not ask
whether the prose is good, only that a manuscript claiming `approved` or `final`
status has actually passed a gate since it last changed. Requirement 12.12 keeps
the question of whether the change *improved* anything with a human.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import novel_fixtures as nf
import novel_strategies as ns

checker = nf.load_checker()

PROPERTY = "Property 11: Post-baseline change and status atomicity"
OWNING_TASK = "8.20"

PROPERTY_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

SYNCHRONIZED_DOCUMENTS: Tuple[str, ...] = (
    "planning/arc-outline.md",
    "planning/timeline.md",
    "planning/motif-ledger.md",
    "planning/canon-bible.md",
    "planning/pov-roster.md",
    "planning/voice-briefs.md",
)

# Requirement 10.7's two statuses that assert a passed gate, and the one status a
# Substantive_Prose_Change demotes them to. Transcribed from the requirement.
APPROVED_STATUSES: Tuple[str, ...] = ("approved", "final")
REVISED_STATUS = "revised"


def _change_codes(records: Sequence[Mapping[str, Any]]) -> Tuple[str, ...]:
    """ArcChange diagnostics through the checker's own gate."""

    index = nf.record_index(ArcChange=list(records))
    return tuple(sorted({item.code for item in checker.check_arc_changes(index)}))


@PROPERTY_SETTINGS
@given(ns.status_changes())
def test_a_change_is_complete_only_when_every_obligation_is_satisfied(variant):
    """Requirements 1.16 and 13.7 through 13.10, one shortfall at a time."""

    codes = _change_codes([variant.payload])
    if variant.valid:
        assert codes == (), "{0} drew {1}".format(variant, codes)
    else:
        assert codes, "{0} drew no diagnostic".format(variant)


@PROPERTY_SETTINGS
@given(
    st.lists(
        st.sampled_from(list(SYNCHRONIZED_DOCUMENTS)),
        min_size=2,
        max_size=6,
        unique=True,
    ),
    st.integers(min_value=0, max_value=5),
)
def test_one_pending_obligation_out_of_many_still_fails(documents, position):
    """Atomicity: five satisfied obligations do not carry a sixth.

    A partially synchronized change leaves the planning documents disagreeing
    with each other, which is worse than an unmade change, so "mostly done" is
    not a state the gate accepts.
    """

    record = nf.completed_arc_change(affected_documents=documents)
    obligations = [dict(item) for item in record["synchronization_obligations"]]
    index = position % len(obligations)
    obligations[index] = dict(
        obligations[index], status="pending", evidence_ref=None
    )
    codes = _change_codes(
        [dict(record, synchronization_obligations=obligations)]
    )
    assert "ARC_CHANGE_INCOMPLETE_SYNCHRONIZATION" in codes, (documents, codes)


@PROPERTY_SETTINGS
@given(
    st.lists(
        st.sampled_from(list(SYNCHRONIZED_DOCUMENTS)),
        min_size=1,
        max_size=6,
        unique=True,
    )
)
def test_a_fully_evidenced_change_of_any_size_is_accepted(documents):
    """The positive direction: atomicity is satisfiable, not merely demanding."""

    assert _change_codes([nf.completed_arc_change(affected_documents=documents)]) == ()


@PROPERTY_SETTINGS
@given(
    st.lists(
        st.sampled_from(list(SYNCHRONIZED_DOCUMENTS)),
        min_size=1,
        max_size=6,
        unique=True,
    )
)
def test_an_affected_document_with_no_obligation_at_all_is_reported(documents):
    """A document named as affected but never synchronized is the same fault.

    Dropping the obligation record entirely must not be a way around the rule
    that dropping its evidence would trip.
    """

    record = nf.completed_arc_change(affected_documents=documents)
    obligations = [dict(item) for item in record["synchronization_obligations"]][1:]
    codes = _change_codes(
        [dict(record, synchronization_obligations=obligations)]
    )
    assert codes != (), documents


@PROPERTY_SETTINGS
@given(st.sampled_from(["approval", "completed_at"]))
def test_a_complete_change_needs_both_its_approval_and_its_time(field):
    """Requirement 13.9: who approved it and when it finished are both required."""

    record = dict(nf.completed_arc_change(), **{field: None})
    assert _change_codes([record]) != (), field


@PROPERTY_SETTINGS
@given(
    st.lists(
        st.sampled_from(list(SYNCHRONIZED_DOCUMENTS)),
        min_size=1,
        max_size=6,
        unique=True,
    )
)
def test_evidence_recorded_against_a_pending_obligation_is_reported(documents):
    """Requirement 13.8: evidence means the work is done, so it cannot be pending.

    An obligation that is `pending` but already cites its evidence is a record
    contradicting itself, and reading either half as authoritative would be the
    checker guessing.
    """

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
    codes = _change_codes([record])
    assert "ARC_CHANGE_OBLIGATION_EVIDENCE_PREMATURE" in codes, codes


# ---------------------------------------------------------------------------
# Substantive_Prose_Change demotion
# ---------------------------------------------------------------------------


def _status_codes(statuses: Mapping[int, str]) -> Tuple[str, ...]:
    """Whole-book status synchronization for a set of chapter statuses."""

    results = []
    for chapter, status in sorted(statuses.items()):
        movement = nf.manuscript_movement_for_chapter(chapter)
        prose = nf.prose_of_length(900)
        header = nf.chapter_header(
            chapter=chapter, movement=movement, prose=prose, status=status
        )
        document = checker.parse_chapter_document(
            nf.render_chapter_file(header, prose),
            relative_path=nf.chapter_relative_path(
                movement, chapter, "chapter-{0:03d}".format(chapter)
            ),
        )
        results.append(
            checker.ChapterCheckResult(
                relative_path=document.relative_path,
                document=document,
                length_report=checker.chapter_length_report(document),
                arc_entry=None,
                diagnostics=(),
            )
        )
    return tuple(
        sorted({item.code for item in checker.check_status_synchronization(results)})
    )


@PROPERTY_SETTINGS
@given(st.sampled_from(list(APPROVED_STATUSES)), ns.chapter_numbers(maximum=40))
def test_an_approved_or_final_chapter_satisfies_the_prerequisite(status, chapter):
    """Requirement 10.7: `approved` and `final` are the statuses that assert a gate."""

    assert _status_codes({chapter: status}) == ()


@PROPERTY_SETTINGS
@given(
    st.sampled_from(["draft", "exploratory", REVISED_STATUS]),
    ns.chapter_numbers(maximum=40),
)
def test_any_pre_gate_status_blocks_the_final_prerequisite(status, chapter):
    """Requirement 10.8: a complete manuscript holds no ungated chapter.

    `revised` is included deliberately. Demotion is not a punishment, it is a
    statement that the chapter changed and has not been re-gated, so a book
    presented as finished cannot contain one.
    """

    codes = _status_codes({chapter: status})
    assert "CHAPTER_STATUS_NOT_FINAL" in codes, (status, codes)


@PROPERTY_SETTINGS
@given(
    st.lists(ns.chapter_numbers(maximum=40), min_size=1, max_size=8, unique=True),
    st.sampled_from(["draft", "exploratory", REVISED_STATUS]),
)
def test_one_ungated_chapter_among_many_is_enough_to_report(chapters, status):
    """A single demoted chapter blocks finalization, however finished the rest is."""

    statuses = {chapter: "final" for chapter in chapters}
    statuses[chapters[0]] = status
    codes = _status_codes(statuses)
    assert "CHAPTER_STATUS_NOT_FINAL" in codes, (chapters, status, codes)


@PROPERTY_SETTINGS
@given(
    st.lists(ns.chapter_numbers(maximum=40), min_size=1, max_size=8, unique=True),
    st.sampled_from(list(APPROVED_STATUSES)),
)
def test_a_wholly_gated_manuscript_is_silent(chapters, status):
    """The positive direction, so the rule is not vacuously satisfied."""

    assert _status_codes({chapter: status for chapter in chapters}) == ()


@PROPERTY_SETTINGS
@given(ns.chapter_numbers(maximum=40))
def test_a_header_and_entry_disagreeing_on_status_is_reported(chapter):
    """Requirement 12.5: a chapter cannot be `final` in one record and not another.

    The demotion rule is only enforceable if the two records agree on where the
    chapter stands, so the disagreement itself is the reported fault.
    """

    movement = nf.manuscript_movement_for_chapter(chapter)
    prose = nf.prose_of_length(900)
    header = nf.chapter_header(
        chapter=chapter, movement=movement, prose=prose, status="final"
    )
    document = checker.parse_chapter_document(
        nf.render_chapter_file(header, prose),
        relative_path=nf.chapter_relative_path(
            movement, chapter, "chapter-{0:03d}".format(chapter)
        ),
    )
    entries = [
        nf.arc_entry(
            chapter=chapter,
            movement=movement,
            slug="chapter-{0:03d}".format(chapter),
            estimated_words=900,
            status=REVISED_STATUS,
        )
    ]
    parsed = _arc_entries(entries)
    # Movement and sequence agreement live in `check_chapter_agreement`; the
    # Requirement 12.5 status, hook, Timeline_ID, and POV_ID agreements live in
    # `check_direct_references`, which is the one that owns this rule.
    diagnostics = checker.check_direct_references(
        document, parsed[0], nf.record_index()
    )
    codes = {item.code for item in diagnostics}
    assert "CHAPTER_STATUS_DISAGREEMENT" in codes, sorted(codes)


def _arc_entries(payloads: Sequence[Mapping[str, Any]]) -> Tuple[Any, ...]:
    document = nf.planning_document(
        "planning/arc-outline.md",
        title="Arc Outline",
        blocks=tuple(("ArcEntry", payload) for payload in payloads),
    )
    entries, _diagnostics = checker.parse_arc_entries(
        document.text(), source="planning/arc-outline.md"
    )
    return entries
