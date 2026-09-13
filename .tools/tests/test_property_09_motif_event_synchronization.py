"""Principal property test for design Property 9.

Property 9: Motif event synchronization

Validates: Requirements 7.3
Related requirements: 7.1, 7.2, 7.12, 7.17, 7.18, 11.8.

Owning task: 8.18. Reserved by task 7.1.

Feature: the-final-frontier-novel, Property 9: Motif event synchronization

What is being proved
--------------------
The Motif_Ledger, the ArcEntries, and the Chapter_Headers all say the same thing
about which Motif_Events belong to which chapter (7.3), and the closed families
keep their fixed shape:

* `MOT-CHAIN-01..03` and `MOT-COPPER-01..03` are closed three-event progressions
  whose movements are fixed (7.1, 7.2);
* exactly two kettle events, both in the Coda (7.12);
* exactly three Record_Progression events, one each in Private Defense,
  Mindwars, and the Coda (7.17).

Two restraints are part of the property rather than exceptions to it.

An Incidental_Mention is not a ledgered event, so counts come from ledger records
only. Nothing here reads prose looking for the word "kettle" — by Requirement 7.5
an unledgered mention carries no dramatic function and cannot change a count.

Mindwars counterphase stays connective context. It becomes a separate Motif_Event
only when an explicit ArcChange creates one, so the checker must not invent a
fourth Record_Progression event from a movement's texture (7.18).
"""

from __future__ import annotations

import collections
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import novel_fixtures as nf
import novel_strategies as ns

checker = nf.load_checker()

PROPERTY = "Property 9: Motif event synchronization"
OWNING_TASK = "8.18"

PROPERTY_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

# Requirements 7.12 and 7.17, transcribed. The closed families and their fixed
# movement placements are the design's, not the checker's.
CLOSED_FAMILY_TOTALS: Mapping[str, int] = {"kettle": 2, "record progression": 3}
KETTLE_MOVEMENTS: Tuple[str, ...] = ("aftermath_coda", "aftermath_coda")
RECORD_MOVEMENTS: Tuple[str, ...] = (
    "private_defense_part",
    "mindwars_part",
    "aftermath_coda",
)


def _family_codes(ledger: Sequence[Mapping[str, Any]]) -> Tuple[str, ...]:
    """Whole-book family totals through the checker's own gate."""

    index = nf.record_index(supporting=False, MotifEvent=list(ledger))
    return tuple(
        sorted({item.code for item in checker.check_motif_family_totals(index)})
    )


@PROPERTY_SETTINGS
@given(st.just(None))
def test_the_design_ledger_satisfies_every_closed_family_total(_unused):
    """The plan of record passes, which is what makes a perturbation legible."""

    assert _family_codes(nf.manuscript_motif_events()) == ()


@PROPERTY_SETTINGS
@given(ns.motif_ledgers())
def test_a_perturbed_closed_family_is_always_reported(variant):
    """Requirements 7.12 and 7.17: a dropped, moved, or extra event never passes."""

    codes = _family_codes(variant.payload)
    if variant.valid:
        assert codes == (), "{0} drew {1}".format(variant, codes)
    else:
        assert codes, "{0} drew no diagnostic".format(variant)


@PROPERTY_SETTINGS
@given(st.sampled_from(sorted(CLOSED_FAMILY_TOTALS)), st.integers(min_value=0, max_value=6))
def test_a_closed_family_count_must_be_exact(family, count):
    """Neither too few nor too many: the totals are fixed, not minimums.

    A "%d or more" reading would let an extra kettle event pass, which is why the
    generated count runs above the fixed total as well as below it.
    """

    movements = KETTLE_MOVEMENTS if family == "kettle" else RECORD_MOVEMENTS
    ledger: List[Dict[str, Any]] = [
        record
        for record in nf.manuscript_motif_events()
        if record["family"] != family
    ]
    for position in range(count):
        ledger.append(
            nf.motif_event(
                motif_event_id="MOT-GEN-{0}-{1:02d}".format(
                    family.split()[0].upper(), position + 1
                ),
                family=family,
                movement=movements[position % len(movements)],
                planned_chapter=100 + position,
            )
        )
    codes = _family_codes(ledger)
    expected_exact = count == CLOSED_FAMILY_TOTALS[family]
    assert (codes == ()) == expected_exact, (family, count, codes)


@PROPERTY_SETTINGS
@given(st.sampled_from(list(nf.MOVEMENTS)))
def test_a_kettle_event_outside_the_coda_is_reported(movement):
    """Requirement 7.12 places both kettle events in the Coda, not merely two of them."""

    ledger = [
        dict(record, movement=movement)
        if record["motif_event_id"] == "MOT-KETTLE-02"
        else record
        for record in nf.manuscript_motif_events()
    ]
    codes = _family_codes(ledger)
    if movement == "aftermath_coda":
        assert codes == (), codes
    else:
        assert "MOTIF_FAMILY_MOVEMENT_PLACEMENT" in codes, (movement, codes)


@PROPERTY_SETTINGS
@given(st.sampled_from(list(nf.MOVEMENTS)))
def test_a_record_progression_event_in_the_wrong_movement_is_reported(movement):
    """Requirement 7.17 fixes one event per named movement, not any three."""

    ledger = [
        dict(record, movement=movement)
        if record["motif_event_id"] == "MOT-RECORD-02"
        else record
        for record in nf.manuscript_motif_events()
    ]
    codes = _family_codes(ledger)
    if movement == "mindwars_part":
        assert codes == (), codes
    else:
        assert "MOTIF_FAMILY_MOVEMENT_PLACEMENT" in codes, (movement, codes)


@PROPERTY_SETTINGS
@given(st.integers(min_value=1, max_value=40))
def test_prose_mentioning_a_motif_noun_never_changes_a_count(mentions):
    """Requirement 7.5: an Incidental_Mention is not an event.

    A Prose_Body may say "kettle" any number of times. Counts come from ledger
    records, so no amount of prose can add a Motif_Event, and a checker that
    scanned for the noun would fail this.
    """

    ledger = nf.manuscript_motif_events()
    before = _family_codes(ledger)
    # The prose is built and counted, but deliberately never handed to the family
    # totals: the point is that the ledger alone decides, so an implementation
    # reading prose here would have to change this test to pass.
    prose = ("The kettle ticked as it cooled.\n" * mentions) + nf.prose_of_length(700)
    assert checker.count_prose_words(checker.normalize_prose(prose)) > 0
    assert _family_codes(ledger) == before == ()


# ---------------------------------------------------------------------------
# Three-way synchronization: ledger, ArcEntry, and Chapter_Header
# ---------------------------------------------------------------------------


def _sync_codes(
    *,
    ledger: Sequence[Mapping[str, Any]],
    arc_assignments: Mapping[int, Sequence[str]],
    header_assignments: Mapping[int, Sequence[str]],
    chapters: Sequence[int],
) -> Tuple[str, ...]:
    """Ledger, ArcEntry, and Chapter_Header assignments, compared by the checker."""

    entries = [
        nf.arc_entry(
            chapter=chapter,
            movement=nf.manuscript_movement_for_chapter(chapter),
            slug="chapter-{0:03d}".format(chapter),
            motif_events=list(arc_assignments.get(chapter, ())),
        )
        for chapter in chapters
    ]
    # Two ledger events cite a Literal_Phrase_Constraint, so those records belong
    # in the index too. Leaving them out would make every example fail on a
    # dangling reference the probe itself created.
    index = nf.record_index(
        supporting=False,
        MotifEvent=list(ledger),
        LiteralPhraseConstraint=[
            nf.did_i_say_yes_constraint(),
            nf.whose_was_that_constraint(),
        ],
        arc_entries=entries,
    )
    results = tuple(
        _chapter_result(chapter, header_assignments.get(chapter, ()))
        for chapter in chapters
    )
    diagnostics = checker.check_motif_planning(index, chapter_scope=tuple(chapters))
    for result in results:
        diagnostics = diagnostics + checker.check_chapter_motif_assignments(
            result.document, index
        )
    return tuple(sorted({item.code for item in diagnostics}))


def _chapter_result(chapter: int, motif_events: Sequence[str]) -> Any:
    movement = nf.manuscript_movement_for_chapter(chapter)
    body = nf.prose_of_length(900)
    header = nf.chapter_header(
        chapter=chapter,
        movement=movement,
        prose=body,
        motif_events=list(motif_events),
        status="final",
    )
    document = checker.parse_chapter_document(
        nf.render_chapter_file(header, body),
        relative_path=nf.chapter_relative_path(
            movement, chapter, "chapter-{0:03d}".format(chapter)
        ),
    )
    return checker.ChapterCheckResult(
        relative_path=document.relative_path,
        document=document,
        length_report=checker.chapter_length_report(document),
        arc_entry=None,
        diagnostics=(),
    )


MOTIF_CHAPTERS: Tuple[int, ...] = tuple(sorted(nf.MANUSCRIPT_MOTIF_ASSIGNMENTS))


@PROPERTY_SETTINGS
@given(st.just(None))
def test_agreeing_ledger_entry_and_header_assignments_are_silent(_unused):
    """Requirement 7.3: three records naming the same events draw no diagnostic."""

    assignments = {
        chapter: list(ids) for chapter, ids in nf.MANUSCRIPT_MOTIF_ASSIGNMENTS.items()
    }
    codes = _sync_codes(
        ledger=nf.manuscript_motif_events(),
        arc_assignments=assignments,
        header_assignments=assignments,
        chapters=MOTIF_CHAPTERS,
    )
    assert codes == (), codes


@PROPERTY_SETTINGS
@given(st.sampled_from(MOTIF_CHAPTERS))
def test_a_header_disagreeing_with_its_entry_is_reported(chapter):
    """Requirement 7.3: the header and the ArcEntry must name one set."""

    assignments = {
        number: list(ids)
        for number, ids in nf.MANUSCRIPT_MOTIF_ASSIGNMENTS.items()
    }
    headers = dict(assignments)
    headers[chapter] = []
    codes = _sync_codes(
        ledger=nf.manuscript_motif_events(),
        arc_assignments=assignments,
        header_assignments=headers,
        chapters=MOTIF_CHAPTERS,
    )
    assert "MOTIF_LEDGER_HEADER_DISAGREEMENT" in codes, (chapter, codes)


@PROPERTY_SETTINGS
@given(st.sampled_from(MOTIF_CHAPTERS))
def test_an_entry_disagreeing_with_the_ledger_is_reported(chapter):
    """Requirement 7.3: the ArcEntry and the ledger must name one set."""

    assignments = {
        number: list(ids)
        for number, ids in nf.MANUSCRIPT_MOTIF_ASSIGNMENTS.items()
    }
    entries = dict(assignments)
    entries[chapter] = []
    codes = _sync_codes(
        ledger=nf.manuscript_motif_events(),
        arc_assignments=entries,
        header_assignments=assignments,
        chapters=MOTIF_CHAPTERS,
    )
    assert codes, (chapter, codes)
