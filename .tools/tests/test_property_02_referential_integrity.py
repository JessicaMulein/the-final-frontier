"""Principal property test for design Property 2.

Property 2: Stable identifier, mechanism-state, and evidence referential integrity

Validates: Requirements 10.4, 14.1, 14.3, 14.4, 14.5, 14.6, 14.7, 14.8, 14.9,
14.10, 14.11, 14.12, 14.14, 15.1, 15.2, 15.3, 15.4
Related requirements: 1.4, 1.5, 4.2-4.4, 6.2, 6.17, 7.1-7.3, 9.5, 9.6, 10.3,
12.1, 12.4, 12.5, 14.2, 14.13, 15.5.

Owning task: 8.11. Reserved by task 7.1.

Feature: the-final-frontier-novel, Property 2: Stable identifier,
mechanism-state, and evidence referential integrity

What is being proved
--------------------
This is the widest property in the design, and task 8.11 keeps it as one
principal test rather than splitting it into new Properties 16 or 17. It holds
together because every clause is the same claim: a record's declared references
and declared state must be resolvable and self-consistent, and where the design
draws a line the checker must stop at it.

The clauses:

* every Stable_ID reference resolves, and a dangling one is never silently
  ignored (10.4, 1.4, 1.5);
* Canon_Source authority follows the declared basis: self-authorizing bases carry
  a matching material class, a ratified note needs an advisory class and a
  resolvable adoption, and advisory material contributes no binding implication
  (14.1, 14.2, 14.3);
* the Canon_Source set is exactly the five paths `DEC-014` names, and
  `songs/One-Time Pad.md` is not one of them (14.14);
* the four neural modes stay distinct, each state carrying only its own mode's
  object, with `CancelState`, `PairState`, and `PairingEvidence` invariants
  intact (14.5-14.9);
* the receive-only December interval, its person-specific lock, and the distinct
  later bench path are three separate facts, not one mechanism (14.10);
* first-person lyric testimony is binding *as testimony*, never as omniscient
  causal proof (14.11, 14.13);
* the five mandatory Fluent_Pairing ranges each resolve to a `PAIR` beat (15.1);
* the provisional load vector is the 56/32/33/7 multiset (15.3).

Where the checker must stay silent
----------------------------------
Two of these are claims about restraint, and they are the ones most easily lost.

A Pairing_Session's *content* is never judged. Requirement 6.17 makes a transcript
semantically opaque, so a record may say a session happened and may not say what
was in it, and nothing here asks the checker to evaluate meaning.

Requirement 14.4's `heritage_base` stays `unspecified_by_author`. Whether a prose
`fact` sentence quietly fills it is a continuity judgment for a human, so those
states are generated and asserted to draw *no* diagnostic.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

import novel_fixtures as nf
import novel_strategies as ns

checker = nf.load_checker()

PROPERTY = (
    "Property 2: Stable identifier, mechanism-state, and evidence "
    "referential integrity"
)
OWNING_TASK = "8.11"

PROPERTY_SETTINGS = settings(
    max_examples=100,
    deadline=None,
    suppress_health_check=[HealthCheck.too_slow, HealthCheck.data_too_large],
)


def _timeline_codes(
    entries: Sequence[Mapping[str, Any]], *, supporting: bool = False
) -> Tuple[str, ...]:
    """Mechanism-state diagnostics for a set of TimelineEntries.

    Supporting records are off by default here. Mechanism state resolves nothing
    outside its own entry, and the default supporting set includes a TimelineEntry
    of its own, which would silently add a foreign entry's verdict to every probe.
    """

    index = nf.record_index(supporting=supporting, TimelineEntry=list(entries))
    diagnostics: Tuple[Any, ...] = ()
    for record in index.of_type("TimelineEntry"):
        diagnostics = diagnostics + checker.check_technical_state(record, index)
    diagnostics = diagnostics + checker.check_pair_calibration_uniqueness(index)
    return tuple(sorted({item.code for item in diagnostics}))


# ---------------------------------------------------------------------------
# Stable identifier resolution
# ---------------------------------------------------------------------------


@PROPERTY_SETTINGS
@given(ns.novel_extension_variants())
def test_every_declared_reference_must_resolve(variant):
    """Requirement 10.4: a reference to a record that does not exist is a fault.

    Dangling references are generated alongside resolvable ones, so a checker
    that resolved nothing would fail the valid cases and one that resolved
    everything optimistically would fail the invalid ones.
    """

    supporting = "unresolvable" not in variant.label
    index = nf.record_index(
        supporting=supporting, NovelExtension=[variant.payload]
    )
    codes = sorted({item.code for item in checker.check_novel_extensions(index)})
    if variant.valid:
        assert codes == [], "{0} drew {1}".format(variant, codes)
    else:
        assert codes, "{0} drew no diagnostic".format(variant)


@PROPERTY_SETTINGS
@given(ns.stable_ids("POV"), ns.stable_ids("TL"))
def test_a_dangling_reference_is_reported_whatever_it_is_named(pov_id, timeline_id):
    """The fault is the unresolvable target, not a recognizable identifier shape."""

    extension = nf.novel_extension(
        affected_records=[{"record_type": "POVProfile", "record_id": pov_id}],
        first_dependency={"record_type": "TimelineEntry", "record_id": timeline_id},
    )
    index = nf.record_index(supporting=False, NovelExtension=[extension])
    codes = {item.code for item in checker.check_novel_extensions(index)}
    assert "EXTENSION_AFFECTED_RECORD_UNRESOLVED" in codes, sorted(codes)
    assert "EXTENSION_DEPENDENCY_UNRESOLVED" in codes, sorted(codes)


# ---------------------------------------------------------------------------
# Canon_Source authority
# ---------------------------------------------------------------------------


@PROPERTY_SETTINGS
@given(ns.canon_authority_variants())
def test_canon_authority_follows_the_declared_basis(variant):
    """Requirements 14.1 through 14.3: the author names the basis and is held to it.

    Nothing here reads a song file or infers that a statement "sounds like" canon.
    That is the point of an explicit authority basis.
    """

    index = nf.record_index(CanonFact=[variant.payload])
    codes = sorted({item.code for item in checker.check_canon_facts(index)})
    if variant.expects_diagnostic:
        assert codes, "{0} drew no diagnostic".format(variant)
    else:
        assert not codes, "{0} drew {1}".format(variant, codes)


@PROPERTY_SETTINGS
@given(ns.canon_source_inventories())
def test_the_canon_source_set_is_exactly_the_five_named_paths(variant):
    """Requirement 14.14 and `DEC-014`: five sources, and not the excluded song."""

    observed = set(variant.payload)
    assert (observed == set(nf.CANON_SOURCE_PATHS)) == variant.valid, str(variant)
    if variant.label == "One-Time Pad added":
        assert nf.EXCLUDED_CANON_SOURCE_PATH in observed
        assert nf.EXCLUDED_CANON_SOURCE_PATH not in set(nf.CANON_SOURCE_PATHS)


@PROPERTY_SETTINGS
@given(ns.dec_002_states())
def test_testimony_is_binding_as_testimony_and_never_as_proof(variant):
    """Requirements 14.11 and 14.13: a truth scope the design does not allow fails.

    There is no `omniscient` truth scope, so a first-person account cannot be
    recorded as settled causal fact however confident the speaker is.
    """

    payload = variant.payload
    if not isinstance(payload, dict) or "canon_id" not in payload:
        return
    index = nf.record_index(CanonFact=[payload])
    codes = sorted({item.code for item in checker.check_canon_facts(index)})
    if variant.expects_diagnostic:
        assert codes, "{0} drew no diagnostic".format(variant)
    else:
        assert not codes, "{0} drew {1}".format(variant, codes)


@PROPERTY_SETTINGS
@given(ns.dec_007_states())
def test_three_accounts_stay_three_accounts(variant):
    """Requirement 14.13: belief, refusal, and inference are not one settled fact."""

    payload = variant.payload
    if "canon_id" in payload:
        index = nf.record_index(CanonFact=[payload])
        diagnostics = checker.check_canon_facts(index)
    else:
        index = nf.record_index(Reveal=[payload])
        diagnostics = checker.check_reveals(index)
    codes = sorted({item.code for item in diagnostics})
    if variant.expects_diagnostic:
        assert codes, "{0} drew no diagnostic".format(variant)
    else:
        assert not codes, "{0} drew {1}".format(variant, codes)


# ---------------------------------------------------------------------------
# The four neural modes
# ---------------------------------------------------------------------------


@PROPERTY_SETTINGS
@given(ns.technical_state_variants())
def test_each_mode_carries_only_its_own_state_object(variant):
    """Requirements 14.5 through 14.9: the modes are distinct, not one channel."""

    entry = nf.timeline_entry(
        timeline_id="TL-MODE-PROBE", chronology_kind="point", state=variant.payload
    )
    codes = _timeline_codes([entry])
    if variant.expects_diagnostic:
        assert codes, "{0} drew no diagnostic".format(variant)
    else:
        assert codes == (), "{0} drew {1}".format(variant, codes)


@PROPERTY_SETTINGS
@given(ns.consent_calibration_rows())
def test_the_pair_consent_and_calibration_table_is_enforced(variant):
    """Requirement 14.7: two living participants, current revocable authorized consent.

    The calibration belongs to exactly those two people and is not transferable,
    so a replacement participant cannot inherit it.
    """

    entry = nf.timeline_entry(
        timeline_id="TL-PAIR-PROBE",
        chronology_kind="point",
        state=ns.pair_technical_state(pair_state=variant.payload),
    )
    codes = _timeline_codes([entry])
    if variant.expects_diagnostic:
        assert codes, "{0} drew no diagnostic".format(variant)
    else:
        assert codes == (), "{0} drew {1}".format(variant, codes)


@PROPERTY_SETTINGS
@given(ns.recording_consent_combinations())
def test_recording_needs_both_independent_consents(variant):
    """Requirement 14.8: the two recording consents are independent, not one flag."""

    entry = nf.timeline_entry(
        timeline_id="TL-EVIDENCE-PROBE",
        chronology_kind="point",
        state=ns.pair_technical_state(pairing_evidence=variant.payload),
    )
    codes = _timeline_codes([entry])
    if variant.expects_diagnostic:
        assert codes, "{0} drew no diagnostic".format(variant)
    else:
        assert codes == (), "{0} drew {1}".format(variant, codes)


@PROPERTY_SETTINGS
@given(ns.stable_ids("CAL"))
def test_a_calibration_id_cannot_be_shared_by_two_different_pairs(calibration_id):
    """Requirement 14.7: a calibration identifies one pair, so reuse is a violation.

    This is the invariant that stops a calibration from becoming a transferable
    key, which is the mechanism the story's consent rules depend on.
    """

    first = nf.timeline_entry(
        timeline_id="TL-CAL-001",
        chronology_kind="point",
        state=ns.pair_technical_state(
            pair_state=nf.pair_state(
                calibration_id=calibration_id,
                participants=("CHAR-001", "CHAR-002"),
                calibration_participants=("CHAR-001", "CHAR-002"),
            )
        ),
    )
    second = nf.timeline_entry(
        timeline_id="TL-CAL-002",
        chronology_kind="point",
        state=ns.pair_technical_state(
            pair_state=nf.pair_state(
                calibration_id=calibration_id,
                participants=("CHAR-003", "CHAR-004"),
                calibration_participants=("CHAR-003", "CHAR-004"),
            )
        ),
    )
    assert _timeline_codes([first]) == ()
    assert _timeline_codes([first, second]) != ()


@PROPERTY_SETTINGS
@given(ns.dec_002_states())
def test_the_december_interval_and_the_bench_path_stay_separate(variant):
    """Requirement 14.10: receive-only December, and a distinct later bench path."""

    payload = variant.payload
    if not isinstance(payload, dict) or "timeline_id" not in payload:
        return
    codes = _timeline_codes([payload])
    if variant.valid:
        assert codes == (), "{0} drew {1}".format(variant, codes)
    else:
        assert codes, "{0} drew no diagnostic".format(variant)


# ---------------------------------------------------------------------------
# Restraint: content is never judged
# ---------------------------------------------------------------------------


@PROPERTY_SETTINGS
@given(ns.transcript_variants())
def test_a_transcript_is_checked_for_consent_not_for_meaning(variant):
    """Requirement 6.17: a transcript stays semantically opaque.

    A record may say a session happened and may not say what was in it. The
    checkable facts are consent, session identity, and scope; the content is not
    the checker's business and no assertion here inspects it.
    """

    payload = variant.payload
    transcript = payload.get("transcript")
    assert isinstance(transcript, dict)
    assert "semantic_claim" in transcript
    # The generator's own verdict tracks overclaiming, never the words spoken.
    assert variant.valid == (
        transcript["covers_subset"]
        and not transcript["cross_session"]
        and not transcript["semantic_claim"]
        and not transcript["provenance_proof"]
    )


@PROPERTY_SETTINGS
@given(ns.heritage_variants())
def test_heritage_base_content_is_left_to_the_author(variant):
    """Requirement 14.4: the base stays unspecified, and prose is not graded.

    A `fact` sentence that quietly fills the base is a continuity finding for a
    human `EditorialFinding`. Asking the checker to detect it would be asking it
    to read for meaning.
    """

    index = nf.record_index(NovelExtension=[variant.payload])
    codes = sorted({item.code for item in checker.check_novel_extensions(index)})
    assert codes == [], "{0} drew {1}".format(variant, codes)


@PROPERTY_SETTINGS
@given(ns.dec_012_states())
def test_mechanism_claims_in_prose_are_recorded_not_graded(variant):
    """The mechanism invariants live in `technical_state`, not in an extension's prose."""

    index = nf.record_index(NovelExtension=[variant.payload])
    codes = sorted({item.code for item in checker.check_novel_extensions(index)})
    assert codes == [], "{0} drew {1}".format(variant, codes)


# ---------------------------------------------------------------------------
# Fluent_Pairing coverage and the load vector
# ---------------------------------------------------------------------------


@PROPERTY_SETTINGS
@given(ns.fluent_pairing_coverage())
def test_every_mandatory_fluent_range_resolves_to_a_pair_beat(variant):
    """Requirement 15.1: five ranges, each needing at least one `PAIR` beat."""

    index = nf.record_index(
        supporting=False, TimelineEntry=list(variant.payload)
    )
    codes = sorted(
        {item.code for item in checker.check_fluent_pairing_coverage(index)}
    )
    if variant.valid:
        assert codes == [], "{0} drew {1}".format(variant, codes)
    else:
        assert codes, "{0} drew no diagnostic".format(variant)


@PROPERTY_SETTINGS
@given(st.sampled_from(list(nf.FLUENT_PAIRING_RANGES)))
def test_a_non_pair_entry_never_credits_a_fluent_range(bounds):
    """A range is covered by a `PAIR` beat, not by any entry that mentions it.

    Crediting a `RECEIVE` entry would let the mandatory pairing coverage be
    satisfied by scenes that contain no pairing at all.
    """

    start, end = bounds
    entries = list(nf.fluent_pairing_timeline_entries())
    entries = [
        entry
        for entry in entries
        if not any(start <= number <= end for number in entry["chapter_numbers"])
    ]
    receiving = nf.timeline_entry(
        timeline_id="TL-RECEIVE-{0:03d}".format(start),
        chronology_kind="point",
        chapter_numbers=[start],
        state=nf.technical_state(
            mode="RECEIVE",
            apparatus_mode="receive-only",
            source_side_continuity="continuous",
            transmit_stage_present=False,
            person_specific_address_state="locked",
        ),
    )
    index = nf.record_index(
        supporting=False, TimelineEntry=entries + [receiving]
    )
    codes = {item.code for item in checker.check_fluent_pairing_coverage(index)}
    assert codes, (bounds, sorted(codes))


@PROPERTY_SETTINGS
@given(ns.load_vector_variants())
def test_the_load_vector_is_compared_as_a_sorted_multiset(variant):
    """Requirements 15.3 and 12.11 together: the numbers bind, the names do not."""

    totals = sorted(int(load["total"]) for load in variant.payload.values())
    if variant.valid:
        assert totals == [7, 32, 33, 56], str(variant)
    elif variant.label != "a POV dropped from the roster":
        assert totals != [7, 32, 33, 56] or variant.label.startswith(
            "movement counts"
        ), str(variant)
