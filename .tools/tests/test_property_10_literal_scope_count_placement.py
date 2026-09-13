"""Principal property test for design Property 10.

Property 10: Ledger-driven literal scope, count, and placement

Validates: Requirements 7.16
Related requirements: 7.7, 7.14, 7.15, 11.8, 12.6.

Owning task: 8.19. Reserved by task 7.1.

Feature: the-final-frontier-novel, Property 10: Ledger-driven literal scope,
count, and placement

What is being proved
--------------------
A phrase is only evaluated because the Motif_Ledger constrains it. There is no
list of interesting phrases inside the checker; the ledger's
Literal_Phrase_Constraint records are the whole authority (7.16, 11.8).

Given a rule, three things hold:

* scanning stays inside Chapter_File Prose_Bodies. Song files, including all five
  Canon_Sources, planning documents, headers, and editorial notes are out of
  scope, so text there can never trigger or satisfy a rule (7.14, 12.6);
* comparison is literal after Unicode NFC and LF normalization only, so case,
  punctuation, and word order are all significant (7.15);
* an in-scope total is counted inside the ledger's *machine-declared* span. The
  Final_Passage is located from the declared marker, never guessed from
  typography, and an unresolvable span makes the gate incomplete rather than
  letting the checker scan a span it inferred (7.7).

A phrase the ledger says nothing about must draw nothing, however evocative it
looks. That is the half of the property that fails if someone hard-codes a phrase.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import novel_fixtures as nf
import novel_strategies as ns

checker = nf.load_checker()

PROPERTY = "Property 10: Ledger-driven literal scope, count, and placement"
OWNING_TASK = "8.19"

PROPERTY_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)

MINDWARS = "mindwars_part"
CODA = "aftermath_coda"
FINAL_CHAPTER = 128


def _chapter_result(
    chapter: int, movement: str, prose: str, *, slug: Optional[str] = None
) -> Any:
    """One parsed Chapter_File, as the literal checks see it."""

    name = slug if slug is not None else "chapter-{0:03d}".format(chapter)
    header = nf.chapter_header(
        chapter=chapter, movement=movement, prose=prose, status="final"
    )
    document = checker.parse_chapter_document(
        nf.render_chapter_file(header, prose),
        relative_path=nf.chapter_relative_path(movement, chapter, name),
    )
    return checker.ChapterCheckResult(
        relative_path=document.relative_path,
        document=document,
        length_report=checker.chapter_length_report(document),
        arc_entry=None,
        diagnostics=(),
    )


def _local_codes(
    result: Any, constraints: Sequence[Mapping[str, Any]]
) -> Tuple[str, ...]:
    """Chapter-local outside-scope diagnostics for one file."""

    index = nf.record_index(
        supporting=False, LiteralPhraseConstraint=list(constraints)
    )
    return tuple(
        sorted(
            {
                item.code
                for item in checker.check_literal_phrase_constraints(
                    result.document, index
                )
            }
        )
    )


def _whole_book_codes(
    results: Sequence[Any], constraints: Sequence[Mapping[str, Any]]
) -> Tuple[str, ...]:
    """Whole-book in-scope-total and span diagnostics."""

    index = nf.record_index(
        supporting=False, LiteralPhraseConstraint=list(constraints)
    )
    return tuple(
        sorted(
            {
                item.code
                for item in checker.check_whole_book_literal_constraints(
                    tuple(results), index
                )
            }
        )
    )


# ---------------------------------------------------------------------------
# Only the ledger decides what is evaluated
# ---------------------------------------------------------------------------


@PROPERTY_SETTINGS
@given(st.integers(min_value=1, max_value=6))
def test_an_unledgered_phrase_is_never_evaluated(repeats):
    """Requirement 7.16: no phrase is interesting unless a record says so.

    The prose repeats a memorable line that no Literal_Phrase_Constraint mentions.
    With an empty ledger nothing can be reported, which is what makes the rules
    data and not code.
    """

    prose = ("Whose was that?\n" * repeats) + nf.prose_of_length(800)
    result = _chapter_result(1, "discovery_part", prose)
    assert _local_codes(result, ()) == ()
    assert _whole_book_codes((result,), ()) == ()


@PROPERTY_SETTINGS
@given(st.sampled_from([m for m in nf.MOVEMENTS if m != MINDWARS]))
def test_a_ledgered_phrase_outside_its_allowed_movement_is_reported(movement):
    """Requirement 7.16: the rule names where the phrase may appear."""

    prose = nf.DID_I_SAY_YES + "\n" + nf.prose_of_length(800)
    result = _chapter_result(20, movement, prose)
    codes = _local_codes(result, (nf.did_i_say_yes_constraint(),))
    assert codes != (), (movement, codes)


@PROPERTY_SETTINGS
@given(st.integers(min_value=1, max_value=5))
def test_a_ledgered_phrase_inside_its_allowed_movement_is_accepted(repeats):
    """The same phrase in its own movement draws nothing, at any count.

    `Did I say yes?` deliberately fixes no in-scope total, so repetition inside
    the allowed movement is a craft matter and not a countable violation.
    """

    prose = (nf.DID_I_SAY_YES + "\n") * repeats + nf.prose_of_length(800)
    result = _chapter_result(73, MINDWARS, prose)
    assert _local_codes(result, (nf.did_i_say_yes_constraint(),)) == ()


# ---------------------------------------------------------------------------
# Literal comparison after NFC and LF normalization only
# ---------------------------------------------------------------------------

NEAR_MISSES: Tuple[str, ...] = (
    "did i say yes?",
    "DID I SAY YES?",
    "Did I say yes",
    "Did I say yes!",
    "Did I  say yes?",
    "Yes, did I say?",
    "Did I say Yes?",
)


@PROPERTY_SETTINGS
@given(st.sampled_from(NEAR_MISSES))
def test_case_punctuation_and_word_order_are_all_significant(near_miss):
    """Requirement 7.15: a near miss is a different phrase, not the same one.

    Each variant here differs from the ledgered phrase only in case, punctuation,
    spacing, or word order, and none of them is the constrained phrase. Placed
    outside the allowed movement they must still draw nothing.
    """

    prose = near_miss + "\n" + nf.prose_of_length(800)
    result = _chapter_result(20, "discovery_part", prose)
    assert _local_codes(result, (nf.did_i_say_yes_constraint(),)) == (), near_miss


@PROPERTY_SETTINGS
@given(st.sampled_from(["\n", "\r\n", "\r"]))
def test_line_endings_do_not_change_a_match(separator):
    """Normalization folds CRLF and CR to LF, so the same prose matches the same."""

    prose = separator.join([nf.DID_I_SAY_YES, "and then nothing."]) + separator
    result = _chapter_result(20, "discovery_part", prose)
    assert _local_codes(result, (nf.did_i_say_yes_constraint(),)) != (), separator


@PROPERTY_SETTINGS
@given(st.sampled_from(["\u0065\u0301", "\u00e9"]))
def test_nfc_equivalent_spellings_match_each_other(spelling):
    """Requirement 7.15: NFC is applied, so composed and decomposed text agree."""

    phrase = "Caf" + spelling + " light?"
    constraint = nf.literal_phrase_constraint(
        constraint_id="LPC-NFC-PROBE",
        exact_phrase="Caf\u00e9 light?",
        allowed_movements=(MINDWARS,),
        diagnostic_code="LITERAL_NFC_PROBE",
    )
    prose = phrase + "\n" + nf.prose_of_length(800)
    result = _chapter_result(20, "discovery_part", prose)
    assert _local_codes(result, (constraint,)) != (), spelling


# ---------------------------------------------------------------------------
# Scanning stays inside Chapter_File Prose_Bodies
# ---------------------------------------------------------------------------


@PROPERTY_SETTINGS
@given(st.integers(min_value=1, max_value=4))
def test_a_phrase_in_a_header_is_out_of_scope(repeats):
    """Requirement 12.6: metadata is not prose, so a hook cannot trigger a rule."""

    prose = nf.prose_of_length(800)
    header = nf.chapter_header(
        chapter=20,
        movement="discovery_part",
        prose=prose,
        hook=(nf.DID_I_SAY_YES + " ") * repeats,
        status="final",
    )
    document = checker.parse_chapter_document(
        nf.render_chapter_file(header, prose),
        relative_path=nf.chapter_relative_path("discovery_part", 20, "probe"),
    )
    index = nf.record_index(
        supporting=False,
        LiteralPhraseConstraint=[nf.did_i_say_yes_constraint()],
    )
    codes = {
        item.code
        for item in checker.check_literal_phrase_constraints(document, index)
    }
    assert codes == set(), sorted(codes)


@PROPERTY_SETTINGS
@given(st.sampled_from(list(nf.CANON_SOURCE_PATHS) + [nf.EXCLUDED_CANON_SOURCE_PATH]))
def test_song_files_are_never_scanned(song_path):
    """Requirement 7.14: the Canon_Sources are read for authority, never scanned.

    A Canon_Source may contain the phrase — it is where the phrase comes from.
    Scanning song text as if it were Chapter_File prose would report the source
    material for quoting itself.
    """

    prose = nf.prose_of_length(800)
    result = _chapter_result(20, "discovery_part", prose)
    constraint = nf.did_i_say_yes_constraint()
    assert song_path in constraint["scope_exclusions"] or song_path.startswith(
        "songs/"
    ), song_path
    assert constraint["scan_scope"] == "chapter-prose-body-only"
    assert _local_codes(result, (constraint,)) == ()


# ---------------------------------------------------------------------------
# In-scope totals inside the machine-declared span
# ---------------------------------------------------------------------------


@PROPERTY_SETTINGS
@given(ns.literal_phrase_placements())
def test_the_in_scope_total_is_counted_inside_the_declared_span(variant):
    """Requirement 7.7: the count is taken from the declared Final_Passage."""

    result = _chapter_result(FINAL_CHAPTER, CODA, variant.payload)
    codes = _whole_book_codes((result,), (nf.whose_was_that_constraint(),))
    if variant.valid:
        assert codes == (), "{0} drew {1}".format(variant, codes)
    else:
        assert codes, "{0} drew no diagnostic".format(variant)


@PROPERTY_SETTINGS
@given(st.integers(min_value=0, max_value=5))
def test_only_exactly_two_occurrences_satisfy_the_terminal_rule(occurrences):
    """The rule fixes an exact total, so one is as wrong as three."""

    prose = nf.final_passage_prose(words=700, occurrences=occurrences)
    result = _chapter_result(FINAL_CHAPTER, CODA, prose)
    codes = _whole_book_codes((result,), (nf.whose_was_that_constraint(),))
    assert (codes == ()) == (occurrences == 2), (occurrences, codes)


@PROPERTY_SETTINGS
@given(st.integers(min_value=1, max_value=3))
def test_an_unresolvable_span_makes_the_gate_incomplete_not_passing(markers):
    """Requirement 7.7: never scan a guessed span.

    A marker that appears zero times or more than once leaves the span
    ambiguous. The checker must report incomplete input rather than pick one
    occurrence and count inside it.
    """

    body = nf.prose_of_length(200)
    prose = (
        body
        + (nf.FINAL_PASSAGE_MARKER + "\n") * markers
        + nf.WHOSE_WAS_THAT
        + " "
        + nf.WHOSE_WAS_THAT
        + "\n"
    )
    result = _chapter_result(FINAL_CHAPTER, CODA, prose)
    index = nf.record_index(
        supporting=False,
        LiteralPhraseConstraint=[nf.whose_was_that_constraint()],
    )
    diagnostics = checker.check_whole_book_literal_constraints((result,), index)
    if markers == 1:
        assert diagnostics == (), [item.code for item in diagnostics]
        return
    assert diagnostics, markers
    assert all(
        item.disposition == checker.DISPOSITION_INCOMPLETE for item in diagnostics
    ), [(item.code, item.disposition) for item in diagnostics]


@PROPERTY_SETTINGS
@given(st.integers(min_value=1, max_value=127))
def test_an_absent_declared_chapter_makes_the_gate_incomplete(other_chapter):
    """A rule scoped to a chapter that is not present cannot be evaluated.

    The gate reports scope-incomplete instead of concluding zero occurrences,
    because "the chapter is missing" and "the phrase is missing" are different
    findings with different repairs.
    """

    movement = nf.manuscript_movement_for_chapter(other_chapter)
    result = _chapter_result(
        other_chapter, movement, nf.prose_of_length(800)
    )
    index = nf.record_index(
        supporting=False,
        LiteralPhraseConstraint=[nf.whose_was_that_constraint()],
    )
    diagnostics = checker.check_whole_book_literal_constraints((result,), index)
    assert diagnostics, other_chapter
    assert all(
        item.disposition == checker.DISPOSITION_INCOMPLETE for item in diagnostics
    ), [(item.code, item.disposition) for item in diagnostics]
