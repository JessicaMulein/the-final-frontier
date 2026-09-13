"""Focused mechanism-state and closed-motif tests for task 8.25.

Validates: Requirements 6.2-6.19, 7.12, 7.17, 14.1-14.14, and 15.1-15.5.

Two subjects share this file because they share a shape. `DEC-015` fixes four
neural-communication modes and the state each one may carry; the motif ledger
fixes closed families whose membership and placement are equally settled. In both
cases the design has already made the decision, so the checker's whole job is to
notice when a record disagrees with it.

What is being proved
--------------------
That the accepted state is accepted exactly, and that each forbidden state is
rejected *individually*. The consent, cancellation, and evidence invariants are
tested one field at a time rather than as a lump, because a single check that
flipped every field at once would still pass if only one of them were enforced.

These tests read structured records only. No test here scores pairing prose, and
no test asks whether a motif event is moving on the page -- a motif's dramatic
force is an `EditorialFinding`, while its family, movement, chapter, and
representation mode are bookkeeping.
"""

from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence, Tuple

import pytest

import novel_fixtures as nf
import novel_strategies as ns

checker = nf.load_checker()

CHAIN_FAMILY = "spectrum / wire / voice"
COPPER_FAMILY = "copper / quiet"


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------


def _state_codes(state: Mapping[str, Any], *, timeline_id: str = "TL-MODE") -> Tuple[str, ...]:
    """Mechanism diagnostics for one `technical_state`.

    Supporting records are off deliberately: mechanism state resolves nothing
    outside its own entry, and the default supporting set contains a TimelineEntry
    whose verdict would be mixed into every result here.
    """

    entry = nf.timeline_entry(
        timeline_id=timeline_id, chronology_kind="point", state=state
    )
    index = nf.record_index(supporting=False, TimelineEntry=[entry])
    diagnostics: Tuple[Any, ...] = ()
    for record in index.of_type("TimelineEntry"):
        diagnostics = diagnostics + checker.check_technical_state(record, index)
    return tuple(sorted({item.code for item in diagnostics}))


def _calibration_codes(*entries: Mapping[str, Any]) -> Tuple[str, ...]:
    """Pair_Calibration uniqueness diagnostics across several sessions."""

    index = nf.record_index(supporting=False, TimelineEntry=list(entries))
    return tuple(
        sorted(
            {item.code for item in checker.check_pair_calibration_uniqueness(index)}
        )
    )


def _motif_codes(*events: Mapping[str, Any]) -> Tuple[str, ...]:
    """Motif planning diagnostics for a set of MotifEvents."""

    index = nf.record_index(supporting=False, MotifEvent=list(events))
    return tuple(sorted({item.code for item in checker.check_motif_planning(index)}))


def _cancel(**options: Any) -> Dict[str, Any]:
    """A `CANCEL` state carrying a CancelState built from `options`."""

    return nf.technical_state(
        mode="CANCEL",
        apparatus_mode="bidirectional-architecture",
        transmit_stage_present=True,
        person_specific_address_state="not-applicable",
        cancel_state=nf.cancel_state(**options),
    )


def _pair_session(timeline_id: str, *participants: str, **pair_options: Any) -> Dict[str, Any]:
    """A conforming pairing session between the named participants."""

    options: Dict[str, Any] = {
        "participants": participants,
        "calibration_participants": participants,
    }
    options.update(pair_options)
    return nf.timeline_entry(
        timeline_id=timeline_id,
        chronology_kind="point",
        state=ns.pair_technical_state(pair_state=nf.pair_state(**options)),
    )


# ---------------------------------------------------------------------------
# DEC-015: one of four modes per event
# ---------------------------------------------------------------------------


def test_a_passive_live_receive_is_accepted() -> None:
    """`RECEIVE` is passive and live: a continuous source, no transmit stage."""

    assert (
        _state_codes(
            nf.technical_state(
                mode="RECEIVE",
                source_side_continuity="continuous",
                apparatus_mode="receive-only",
                transmit_stage_present=False,
                person_specific_address_state="locked",
            )
        )
        == ()
    )


@pytest.mark.parametrize(
    "continuity", ("discontinuous", "unknown", "not-applicable")
)
def test_a_receive_from_a_broken_source_side_is_rejected(continuity: str) -> None:
    """A live reception has a continuous source side; a recording is not reception."""

    codes = _state_codes(
        nf.technical_state(
            mode="RECEIVE",
            source_side_continuity=continuity,
            apparatus_mode="receive-only",
            transmit_stage_present=False,
            person_specific_address_state="locked",
        )
    )
    assert codes != (), continuity


@pytest.mark.parametrize("address_state", ("identified", "locked", "reused"))
def test_a_nonsemantic_addressed_intrude_is_accepted(address_state: str) -> None:
    """`INTRUDE` reaches a specific address; it does not read meaning.

    All three addressed states are accepted because addressing is what the mode
    requires. What it must not do -- read semantic content -- has no field to be
    recorded in, and a prose claim that it did is an `EditorialFinding`.
    """

    assert (
        _state_codes(
            nf.technical_state(
                mode="INTRUDE",
                apparatus_mode="bench-transmit",
                transmit_stage_present=True,
                person_specific_address_state=address_state,
            )
        )
        == ()
    )


@pytest.mark.parametrize("address_state", ("unidentified", "not-applicable"))
def test_an_unaddressed_intrude_is_rejected(address_state: str) -> None:
    """An intrusion with no address is not this mode."""

    codes = _state_codes(
        nf.technical_state(
            mode="INTRUDE",
            apparatus_mode="bench-transmit",
            transmit_stage_present=True,
            person_specific_address_state=address_state,
        )
    )
    assert codes != (), address_state


@pytest.mark.parametrize("scope", ("bounded-local", "area-scale"))
def test_an_unaddressed_subtractive_cancel_is_accepted(scope: str) -> None:
    """`CANCEL` subtracts across a field volume, in either declared scope."""

    assert _state_codes(_cancel(scope=scope)) == (), scope


def test_a_cancel_scope_outside_the_two_is_rejected() -> None:
    """There are two scopes, so a third is malformed rather than merely unusual."""

    codes = _state_codes(_cancel(scope="global"))
    assert "CANCEL_STATE_MALFORMED" in codes, codes


def test_an_addressed_cancellation_is_rejected() -> None:
    """Cancellation acts on a volume, not on a person, so it has no address."""

    state = _cancel()
    state["person_specific_address_state"] = "locked"
    assert _state_codes(state) != ()


@pytest.mark.parametrize(
    "field,value",
    (
        ("additive_inverse_exists", True),
        ("affected_set_predictable_before", True),
        ("affected_set_enumerable_during", True),
        ("affected_set_fully_mapped_after", True),
        ("inserted_content", "A sentence placed into the field."),
        ("provenance_yield", "The field names who sent it."),
    ),
)
def test_each_forbidden_cancel_property_is_rejected_on_its_own(
    field: str, value: Any
) -> None:
    """Requirement 14.9: six separate prohibitions, enforced separately.

    A reversible cancellation, a predictable or enumerable or fully mapped
    affected set, inserted content, and a provenance yield are each independently
    fatal. Testing them one at a time is what proves all six are live, rather than
    one of them standing in for the rest.
    """

    codes = _state_codes(_cancel(overrides={field: value}))
    assert "CANCEL_STATE_INVARIANT" in codes, (field, codes)


def test_the_null_event_is_not_classified_as_intrude() -> None:
    """`not-applicable` means no neural event; it is not a quiet intrusion."""

    assert _state_codes(nf.technical_state()) == ()
    codes = _state_codes(
        nf.technical_state(
            mode="INTRUDE",
            apparatus_mode="not-applicable",
            transmit_stage_present=False,
            person_specific_address_state="not-applicable",
        )
    )
    assert codes != ()


def test_a_two_participant_pair_session_is_accepted() -> None:
    """`PAIR` is a deliberate, consented, calibrated session between two people."""

    assert _state_codes(ns.pair_technical_state()) == ()


def test_a_mode_outside_the_fixed_five_is_rejected() -> None:
    """Four modes plus the no-event value; nothing else is a mode."""

    codes = _state_codes(nf.technical_state(mode="TRANSMIT"))
    assert "TIMELINE_TECHNICAL_STATE_MALFORMED" in codes, codes


def test_a_state_carrying_two_mode_objects_is_rejected() -> None:
    """One event is in one mode, so it carries one mode object.

    Holding a CancelState and a PairState together would let a record be read as
    whichever mode suited the moment.
    """

    codes = _state_codes(
        ns.pair_technical_state(cancel_state=nf.cancel_state())
    )
    assert "TIMELINE_MODE_INVARIANT" in codes, codes


# ---------------------------------------------------------------------------
# Pairing consent, calibration, and evidence
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "field,value",
    (
        ("current", False),
        ("revocable", False),
        ("authorized_a", False),
        ("authorized_b", False),
    ),
)
def test_each_consent_field_is_required_on_its_own(field: str, value: Any) -> None:
    """Requirement 6.4: current, revocable, and separately authorized by both.

    `authorized_a` and `authorized_b` are checked separately because one flag
    standing for both is precisely the shortcut the design refuses.
    """

    consent = dict(nf.pair_state()["consent"])
    consent[field] = value
    codes = _state_codes(
        ns.pair_technical_state(pair_state=nf.pair_state(consent=consent))
    )
    assert "PAIR_STATE_INVARIANT" in codes, (field, codes)


def test_a_deliberate_send_act_is_required() -> None:
    """Requirement 6.6: sending is an act, so the send state says `required`."""

    assert (
        _state_codes(
            ns.pair_technical_state(
                pair_state=nf.pair_state(deliberate_send_state="required")
            )
        )
        == ()
    )
    codes = _state_codes(
        ns.pair_technical_state(
            pair_state=nf.pair_state(deliberate_send_state="optional")
        )
    )
    assert "PAIR_STATE_MALFORMED" in codes, codes


@pytest.mark.parametrize("send_state", ("paused", "revoked", "integrity-failed"))
def test_a_stopped_session_is_recorded_rather_than_continued(
    send_state: str,
) -> None:
    """A pause, a revocation, and an integrity failure are declarable states.

    Each one is a legitimate thing to record. What the design forbids is a session
    that continues as though the channel were clean, and the way to forbid it is
    to require the state be named -- which is why these are accepted values and
    an invented one is not.
    """

    codes = _state_codes(
        ns.pair_technical_state(
            pair_state=nf.pair_state(deliberate_send_state=send_state)
        )
    )
    assert "PAIR_STATE_MALFORMED" not in codes, (send_state, codes)


def test_a_calibration_is_not_transferable() -> None:
    """Requirement 6.5: a calibration belongs to its pair and cannot be lent."""

    codes = _state_codes(
        ns.pair_technical_state(
            pair_state=nf.pair_state(calibration_transferable=True)
        )
    )
    assert "PAIR_STATE_INVARIANT" in codes, codes


def test_a_replacement_participant_cannot_inherit_the_calibration() -> None:
    """The calibrated pair and the sending pair are the same two people."""

    codes = _state_codes(
        ns.pair_technical_state(
            pair_state=nf.pair_state(
                participants=("CHAR-001", "CHAR-004"),
                calibration_participants=("CHAR-001", "CHAR-002"),
            )
        )
    )
    assert "PAIR_STATE_INVARIANT" in codes, codes


def test_one_calibration_cannot_serve_two_pairs() -> None:
    """A shared calibration would make it a transferable key."""

    shared = "CAL-SHARED-001"
    first = _pair_session(
        "TL-CAL-001", "CHAR-001", "CHAR-002", calibration_id=shared
    )
    second = _pair_session(
        "TL-CAL-002", "CHAR-003", "CHAR-004", calibration_id=shared
    )
    assert _calibration_codes(first) == ()
    assert _calibration_codes(first, second) != ()


def test_the_same_pair_may_hold_its_calibration_across_sessions() -> None:
    """Reuse by the *same* pair is the calibration working as designed.

    Without this the previous test would be satisfied by a checker that simply
    banned every repeated calibration ID, which would make a continuing
    relationship unrecordable.
    """

    shared = "CAL-SAME-001"
    first = _pair_session(
        "TL-SAME-001", "CHAR-001", "CHAR-002", calibration_id=shared
    )
    second = _pair_session(
        "TL-SAME-002", "CHAR-001", "CHAR-002", calibration_id=shared
    )
    assert _calibration_codes(first, second) == ()


@pytest.mark.parametrize(
    "field",
    (
        "consent_state_metadata_present",
        "transport_metadata_present",
        "metadata_semantically_opaque",
    ),
)
def test_mandatory_evidence_metadata_is_required(field: str) -> None:
    """Consent and transport metadata are mandatory, and stay meaning-free.

    Opacity is the load-bearing one: transport metadata proves a session happened
    without disclosing what passed through it.
    """

    codes = _state_codes(
        ns.pair_technical_state(
            pairing_evidence=nf.pairing_evidence(overrides={field: False})
        )
    )
    assert "PAIRING_EVIDENCE_INVARIANT" in codes, (field, codes)


def test_recording_is_off_by_default() -> None:
    """The default evidence state records nothing."""

    evidence = nf.pairing_evidence()
    assert evidence["content_recording_enabled"] is False
    assert evidence["recording_consent_a"] is False
    assert evidence["recording_consent_b"] is False
    assert _state_codes(ns.pair_technical_state()) == ()


@pytest.mark.parametrize(
    "consent_a,consent_b", ((False, False), (True, False), (False, True))
)
def test_recording_needs_both_consents(consent_a: bool, consent_b: bool) -> None:
    """Requirement 6.12: recording is enabled by separate mutual consent."""

    codes = _state_codes(
        ns.pair_technical_state(
            pairing_evidence=nf.pairing_evidence(
                content_recording_enabled=True,
                recording_consent_a=consent_a,
                recording_consent_b=consent_b,
            )
        )
    )
    assert "PAIRING_EVIDENCE_INVARIANT" in codes, (consent_a, consent_b, codes)


def test_recording_with_both_consents_is_accepted() -> None:
    """Mutual consent is the one state in which recording is lawful."""

    assert (
        _state_codes(
            ns.pair_technical_state(
                pairing_evidence=nf.pairing_evidence(
                    content_recording_enabled=True,
                    recording_consent_a=True,
                    recording_consent_b=True,
                )
            )
        )
        == ()
    )


def test_a_transcript_belongs_to_its_own_session() -> None:
    """A transcript is bound to the session that produced it."""

    own = nf.pairing_evidence(
        content_recording_enabled=True,
        recording_consent_a=True,
        recording_consent_b=True,
        transcript={
            "transcript_id": "TR-001",
            "session_timeline_id": "TL-MODE",
            "content_scope": "Only the contributions both participants transported.",
        },
    )
    assert _state_codes(ns.pair_technical_state(pairing_evidence=own)) == ()

    borrowed = nf.pairing_evidence(
        content_recording_enabled=True,
        recording_consent_a=True,
        recording_consent_b=True,
        transcript={
            "transcript_id": "TR-002",
            "session_timeline_id": "TL-SOME-OTHER-SESSION",
            "content_scope": "Only the contributions both participants transported.",
        },
    )
    assert _state_codes(ns.pair_technical_state(pairing_evidence=borrowed)) != ()


def test_a_transcript_cannot_exist_without_recording() -> None:
    """Requirement 6.12: no transcript where recording was never enabled."""

    codes = _state_codes(
        ns.pair_technical_state(
            pairing_evidence=nf.pairing_evidence(
                transcript={
                    "transcript_id": "TR-003",
                    "session_timeline_id": "TL-MODE",
                    "content_scope": "Transported contributions only.",
                }
            )
        )
    )
    assert codes != ()


def test_the_mandatory_fluent_pairing_ranges_are_covered() -> None:
    """Requirement 15.4: five chapter ranges each carry a pairing beat."""

    index = nf.record_index(
        supporting=False, TimelineEntry=list(nf.fluent_pairing_timeline_entries())
    )
    assert checker.check_fluent_pairing_coverage(index) == ()


@pytest.mark.parametrize("dropped", nf.FLUENT_PAIRING_RANGES)
def test_dropping_any_required_range_is_rejected(
    dropped: Sequence[int],
) -> None:
    """Each of the five ranges is required on its own, not four out of five."""

    start, end = dropped
    kept = [
        entry
        for entry in nf.fluent_pairing_timeline_entries()
        if not any(start <= number <= end for number in entry["chapter_numbers"])
    ]
    index = nf.record_index(supporting=False, TimelineEntry=kept)
    assert checker.check_fluent_pairing_coverage(index) != ()


# ---------------------------------------------------------------------------
# Closed motif families: MOT-CHAIN-01..03 and MOT-COPPER-01..03
# ---------------------------------------------------------------------------

CHAIN_EVENTS: Tuple[Tuple[str, str, int, str], ...] = (
    ("MOT-CHAIN-01", "discovery_part", 13, "image"),
    ("MOT-CHAIN-02", "private_defense_part", 45, "image"),
    ("MOT-CHAIN-03", "aftermath_coda", 127, "action"),
)
COPPER_EVENTS: Tuple[Tuple[str, str, int, str], ...] = (
    ("MOT-COPPER-01", "private_defense_part", 31, "image"),
    ("MOT-COPPER-02", "mindwars_part", 70, "image"),
    ("MOT-COPPER-03", "aftermath_coda", 124, "image"),
)


def _event(
    motif_event_id: str,
    family: str,
    movement: str,
    chapter: int,
    representation_mode: str,
) -> Dict[str, Any]:
    return nf.motif_event(
        motif_event_id=motif_event_id,
        family=family,
        movement=movement,
        planned_chapter=chapter,
        participating_chapters=(chapter,),
        representation_mode=representation_mode,
    )


@pytest.mark.parametrize(
    "family,events", ((CHAIN_FAMILY, CHAIN_EVENTS), (COPPER_FAMILY, COPPER_EVENTS))
)
def test_the_closed_family_mapping_is_accepted_exactly(
    family: str, events: Sequence[Tuple[str, str, int, str]]
) -> None:
    """Three events each, in the movements and chapters the ledger fixes."""

    records = [
        _event(motif_id, family, movement, chapter, mode)
        for motif_id, movement, chapter, mode in events
    ]
    assert _motif_codes(*records) == ()


@pytest.mark.parametrize(
    "family,events", ((CHAIN_FAMILY, CHAIN_EVENTS), (COPPER_FAMILY, COPPER_EVENTS))
)
def test_a_fourth_event_extends_a_closed_family(
    family: str, events: Sequence[Tuple[str, str, int, str]]
) -> None:
    """A closed family has no fourth member, whatever it is called.

    The chain family's Mindwars counterphase and the copper family's Discovery
    references are connective context and unledgered foreshadowing. Admitting them
    as events is the specific mistake the closure rule prevents.
    """

    extra_id = "{0}-04".format(family.split()[0].upper())
    records = [
        _event(motif_id, family, movement, chapter, mode)
        for motif_id, movement, chapter, mode in events
    ]
    records.append(_event(extra_id, family, "mindwars_part", 70, "image"))
    codes = _motif_codes(*records)
    assert "MOTIF_CLOSED_FAMILY_EXTENSION" in codes, codes


@pytest.mark.parametrize(
    "motif_id,family,movement,chapter,mode",
    (
        # Each row moves exactly one field off the ledger's mapping.
        ("MOT-CHAIN-01", CHAIN_FAMILY, "private_defense_part", 13, "image"),
        ("MOT-CHAIN-02", CHAIN_FAMILY, "private_defense_part", 46, "image"),
        ("MOT-CHAIN-03", CHAIN_FAMILY, "aftermath_coda", 127, "image"),
        ("MOT-COPPER-01", COPPER_FAMILY, "discovery_part", 31, "image"),
        ("MOT-COPPER-02", COPPER_FAMILY, "mindwars_part", 71, "image"),
        ("MOT-COPPER-03", COPPER_FAMILY, "aftermath_coda", 124, "literal"),
    ),
)
def test_a_single_field_off_the_mapping_is_rejected(
    motif_id: str, family: str, movement: str, chapter: int, mode: str
) -> None:
    """The mapping fixes family, movement, chapter, and representation together.

    One wrong field is enough. Checking them a row at a time is what shows the
    mapping is compared field by field rather than by identifier alone.
    """

    codes = _motif_codes(_event(motif_id, family, movement, chapter, mode))
    assert "MOTIF_RESOLVED_MAPPING_DISAGREEMENT" in codes, (motif_id, codes)


@pytest.mark.parametrize(
    "family,events", ((CHAIN_FAMILY, CHAIN_EVENTS), (COPPER_FAMILY, COPPER_EVENTS))
)
def test_a_family_name_off_the_mapping_is_rejected(
    family: str, events: Sequence[Tuple[str, str, int, str]]
) -> None:
    """A ledgered event cannot be refiled under another family."""

    motif_id, movement, chapter, mode = events[0]
    other = COPPER_FAMILY if family == CHAIN_FAMILY else CHAIN_FAMILY
    codes = _motif_codes(_event(motif_id, other, movement, chapter, mode))
    assert codes != (), (motif_id, other)


def test_motif_prose_wording_is_not_judged() -> None:
    """The `dramatic_function` text must exist; it is never read for quality.

    A blank function is missing bookkeeping. A weak one is an `EditorialFinding`,
    and the difference is the whole boundary this checker is built on.
    """

    flat = nf.motif_event(
        motif_event_id="MOT-CHAIN-01",
        family=CHAIN_FAMILY,
        movement="discovery_part",
        planned_chapter=13,
        participating_chapters=(13,),
        representation_mode="image",
        dramatic_function="It happens.",
    )
    assert _motif_codes(flat) == ()

    blank = dict(flat)
    blank["dramatic_function"] = ""
    assert _motif_codes(blank) != ()
