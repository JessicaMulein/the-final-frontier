"""Focused mechanism-chronology tests for task 7.7 of the novel specification.

Validates: Requirements 6.2, 9.6, 9.7, and 14.1–14.14.

Two groups of synthetic records. The first proves the December chronology stays
separable: a continuous source interval, an eight-second offset carried only on
the receiving side, a receive-only apparatus with no transmit stage, a distinct
later bench `INTRUDE` over the locked person-specific address, page nine as
broader capability rather than December evidence, and Trust formation kept apart
from record composition and later deposit. The second adds the `DEC-015` pairing
cases task 7.3 did not already cover.

Every record here is synthetic. No test reads novel prose, and no test asks
whether any of this is dramatically successful.
"""

from __future__ import annotations

import pytest

import novel_fixtures as nf

MARA = "CHAR-001"
NIA = "CHAR-002"

# The December event: Mara receives, the source side stays continuous, and the
# eight seconds are a reception offset rather than a source-side discontinuity.
DECEMBER_RECEIVE = dict(
    mode="RECEIVE",
    source_side_continuity="continuous",
    receiver_offset_seconds=8,
    apparatus_mode="receive-only",
    transmit_stage_present=False,
    person_specific_address_state="locked",
    evidence_scope=(
        "The receiver observes an offset and an address lock. This entry proves "
        "no transmission and no causal link to the source's wanting."
    ),
)

# The later bench path Mara deliberately adds. A separate entry, a separate mode.
BENCH_INTRUDE = dict(
    mode="INTRUDE",
    source_side_continuity="unknown",
    receiver_offset_seconds=None,
    apparatus_mode="bench-transmit",
    transmit_stage_present=True,
    person_specific_address_state="locked",
    evidence_scope=(
        "A nonsemantic write to a locked person-specific address. This entry "
        "supplies no December transmit stage and confirms no provenance."
    ),
)

# Page nine describes what the architecture can do, not what December did.
PAGE_NINE_CAPABILITY = dict(
    mode="not-applicable",
    source_side_continuity="not-applicable",
    receiver_offset_seconds=None,
    apparatus_mode="bidirectional-architecture",
    transmit_stage_present=None,
    person_specific_address_state="not-applicable",
    evidence_scope=(
        "Page nine records a broader architectural capability. It is not "
        "evidence of a December transmit event and cannot supply one."
    ),
)


def _codes(diagnostics):
    return [diagnostic.code for diagnostic in diagnostics]


def _chronology_workspace(base, timelines, *, chapters=(1,)):
    """A workspace whose Canon_Bible carries exactly `timelines`.

    Registers two people, because a `PAIR` participant and a December
    source/receiver pair must both resolve to real Character_IDs.
    """

    entries = [
        nf.arc_entry(
            chapter=chapter,
            slug="chronology-{0:03d}".format(chapter),
            timeline_id=timelines[0]["timeline_id"],
            motif_events=[],
        )
        for chapter in chapters
    ]
    return nf.build_workspace(
        base,
        planning=nf.reference_planning_documents(
            arc_entries=entries,
            timeline_entries=list(timelines),
            motif_events=[],
            pov_profiles=[
                nf.pov_profile(character_id=MARA),
                nf.pov_profile(
                    character_id=NIA,
                    pov_id="POV-NIA",
                    selected_name="Fixture Two",
                    anchor=False,
                    voice_brief_id="VOICE-FIXTURE-TWO",
                ),
            ],
            voice_briefs=[
                nf.voice_brief(),
                nf.voice_brief(
                    voice_brief_id="VOICE-FIXTURE-TWO", pov_id="POV-NIA"
                ),
            ],
        ),
    )


def _entry_diagnostics(checker, workspace, timeline_id):
    """Every planning diagnostic attributable to one Timeline entry."""

    index, load_diagnostics = checker.load_reference_index(
        workspace.manuscript_root
    )
    record = index.unique("TimelineEntry", timeline_id)
    assert record is not None, "fixture must index exactly one " + timeline_id
    return (
        tuple(load_diagnostics)
        + checker.check_technical_state(record, index)
        + checker.check_planning_references(index)
    )


def _december(**overrides):
    state = dict(DECEMBER_RECEIVE)
    state.update(overrides)
    return nf.timeline_entry(
        timeline_id="TL-DECEMBER-RECEIVE",
        chronology_kind="interval",
        relative_chronology="A continuous December source-side morning.",
        duration="twenty minutes in the attributed account",
        participants=[MARA, NIA],
        chapter_numbers=[1],
        state=nf.technical_state(**state),
    )


# ---------------------------------------------------------------------------
# December reception, the later bench path, and page nine
# ---------------------------------------------------------------------------


def test_december_reception_validates_as_a_continuous_source_with_an_offset(
    checker, tmp_path
):
    workspace = _chronology_workspace(tmp_path / "workspace", [_december()])

    assert _entry_diagnostics(checker, workspace, "TL-DECEMBER-RECEIVE") == ()


@pytest.mark.parametrize(
    "overrides,reason",
    [
        ({"source_side_continuity": "discontinuous"}, "a source-side gap"),
        ({"transmit_stage_present": True}, "a December transmit stage"),
    ],
)
def test_december_cannot_gain_a_source_gap_or_a_transmit_stage(
    checker, tmp_path, overrides, reason
):
    """`RECEIVE` fixes a continuous source and no transmit stage."""

    workspace = _chronology_workspace(
        tmp_path / "workspace", [_december(**overrides)]
    )

    diagnostics = _entry_diagnostics(checker, workspace, "TL-DECEMBER-RECEIVE")

    assert "TIMELINE_MODE_INVARIANT" in _codes(diagnostics), reason
    assert checker.classify_result(diagnostics) == checker.RESULT_REVISION


def test_the_eight_second_offset_lives_only_on_the_receiving_record(
    checker, tmp_path
):
    """Nia's source-side morning carries no offset; Mara's reception does."""

    source_side = nf.timeline_entry(
        timeline_id="TL-DECEMBER-SOURCE",
        chronology_kind="interval",
        relative_chronology="The same morning, lived continuously by the source.",
        participants=[NIA],
        chapter_numbers=[2],
        state=nf.technical_state(
            mode="not-applicable",
            source_side_continuity="continuous",
            receiver_offset_seconds=None,
            evidence_scope=(
                "An ordinary continuous morning. No reception, no offset, and "
                "no anomaly experienced by the source."
            ),
        ),
    )
    workspace = _chronology_workspace(
        tmp_path / "workspace", [_december(), source_side], chapters=(1, 2)
    )
    index, load_diagnostics = checker.load_reference_index(
        workspace.manuscript_root
    )

    receiving = index.unique("TimelineEntry", "TL-DECEMBER-RECEIVE")
    source = index.unique("TimelineEntry", "TL-DECEMBER-SOURCE")

    assert load_diagnostics == ()
    assert receiving.payload["technical_state"]["receiver_offset_seconds"] == 8
    assert source.payload["technical_state"]["receiver_offset_seconds"] is None
    assert (
        source.payload["technical_state"]["source_side_continuity"] == "continuous"
    )
    assert checker.check_technical_state(source, index) == ()
    assert checker.check_technical_state(receiving, index) == ()


def test_the_later_bench_handshake_is_a_distinct_intrude_record(
    checker, tmp_path
):
    """One address, two entries: December receives, the bench path writes."""

    bench = nf.timeline_entry(
        timeline_id="TL-BENCH-INTRUDE",
        relative_chronology="The later bench transmit path over the same address.",
        participants=[MARA, NIA],
        chapter_numbers=[18],
        state=nf.technical_state(**BENCH_INTRUDE),
    )
    workspace = _chronology_workspace(
        tmp_path / "workspace", [_december(), bench], chapters=(1,)
    )
    index, load_diagnostics = checker.load_reference_index(
        workspace.manuscript_root
    )
    december = index.unique("TimelineEntry", "TL-DECEMBER-RECEIVE")
    later = index.unique("TimelineEntry", "TL-BENCH-INTRUDE")

    assert load_diagnostics == ()
    assert checker.check_technical_state(december, index) == ()
    assert checker.check_technical_state(later, index) == ()
    # Same locked address, opposite transmit state, different modes and entries.
    for record in (december, later):
        assert record.payload["technical_state"][
            "person_specific_address_state"
        ] == "locked"
    assert december.payload["technical_state"]["transmit_stage_present"] is False
    assert later.payload["technical_state"]["transmit_stage_present"] is True
    assert december.payload["timeline_id"] != later.payload["timeline_id"]


def test_an_intrude_record_still_needs_its_person_specific_address(
    checker, tmp_path
):
    bench = nf.timeline_entry(
        timeline_id="TL-BENCH-INTRUDE",
        participants=[MARA, NIA],
        chapter_numbers=[18],
        state=nf.technical_state(
            **dict(BENCH_INTRUDE, person_specific_address_state="unidentified")
        ),
    )
    workspace = _chronology_workspace(tmp_path / "workspace", [bench])

    diagnostics = _entry_diagnostics(checker, workspace, "TL-BENCH-INTRUDE")

    assert "TIMELINE_MODE_INVARIANT" in _codes(diagnostics)


def test_page_nine_is_capability_and_supplies_no_december_transmit_event(
    checker, tmp_path
):
    """A bidirectional architecture record declares no mode and no transmission."""

    page_nine = nf.timeline_entry(
        timeline_id="TL-PAGE-NINE",
        relative_chronology="Page nine, read later as architectural capability.",
        participants=[MARA],
        chapter_numbers=[45],
        state=nf.technical_state(**PAGE_NINE_CAPABILITY),
    )
    workspace = _chronology_workspace(
        tmp_path / "workspace", [_december(), page_nine]
    )
    index, _ = checker.load_reference_index(workspace.manuscript_root)
    record = index.unique("TimelineEntry", "TL-PAGE-NINE")
    state = record.payload["technical_state"]

    assert checker.check_technical_state(record, index) == ()
    assert state["mode"] == "not-applicable"
    assert state["transmit_stage_present"] is None
    assert state["apparatus_mode"] == "bidirectional-architecture"
    # The December entry keeps its own receive-only apparatus regardless.
    december = index.unique("TimelineEntry", "TL-DECEMBER-RECEIVE")
    assert december.payload["technical_state"]["apparatus_mode"] == "receive-only"


def test_page_nine_cannot_be_written_as_a_december_receive_event(
    checker, tmp_path
):
    """Claiming RECEIVE on the bidirectional record forces a transmit contradiction."""

    overclaim = nf.timeline_entry(
        timeline_id="TL-PAGE-NINE",
        participants=[MARA],
        chapter_numbers=[45],
        state=nf.technical_state(
            **dict(PAGE_NINE_CAPABILITY, mode="RECEIVE", transmit_stage_present=True)
        ),
    )
    workspace = _chronology_workspace(tmp_path / "workspace", [overclaim])

    diagnostics = _entry_diagnostics(checker, workspace, "TL-PAGE-NINE")

    assert "TIMELINE_MODE_INVARIANT" in _codes(diagnostics)


# ---------------------------------------------------------------------------
# Trust formation, record composition, and later deposit
# ---------------------------------------------------------------------------


def _trust_workspace(base, *, chronology):
    """April alteration, Trust formation, composition, deposit, and release."""

    supporting = [
        nf.timeline_entry(
            timeline_id=timeline_id,
            relative_chronology=description,
            participants=[MARA],
            chapter_numbers=[chapter],
        )
        for timeline_id, description, chapter in (
            ("TL-APRIL-ALTERED", "The April record is altered.", 8),
            ("TL-RECORD-COMPOSED", "The record is composed, before the Trust.", 9),
            ("TL-RECORD-DEPOSITED", "The same record is deposited later.", 40),
            ("TL-RECORD-RELEASED", "The deposited record is released.", 60),
        )
    ]
    trust = nf.timeline_entry(
        timeline_id="TL-TRUST-FORMED",
        relative_chronology="The Civic Record Trust forms after the alteration.",
        participants=[MARA],
        chapter_numbers=[10],
        record_chronology=chronology,
    )
    return _chronology_workspace(base, [trust] + supporting)


def test_trust_formation_keeps_composition_and_later_deposit_separate(
    checker, tmp_path
):
    workspace = _trust_workspace(
        tmp_path / "workspace",
        chronology={
            "composition_timeline_id": "TL-RECORD-COMPOSED",
            "deposit_timeline_id": "TL-RECORD-DEPOSITED",
            "release_timeline_ids": ["TL-RECORD-RELEASED"],
        },
    )

    assert _entry_diagnostics(checker, workspace, "TL-TRUST-FORMED") == ()


def test_collapsing_composition_into_deposit_is_reported(checker, tmp_path):
    """Pre-Trust composition and later deposit are separate entries."""

    workspace = _trust_workspace(
        tmp_path / "workspace",
        chronology={
            "composition_timeline_id": "TL-RECORD-COMPOSED",
            "deposit_timeline_id": "TL-RECORD-COMPOSED",
            "release_timeline_ids": [],
        },
    )

    diagnostics = _entry_diagnostics(checker, workspace, "TL-TRUST-FORMED")

    assert "RECORD_CHRONOLOGY_COLLAPSED" in _codes(diagnostics)
    assert checker.classify_result(diagnostics) == checker.RESULT_REVISION


def test_a_dangling_record_chronology_reference_is_reported(checker, tmp_path):
    workspace = _trust_workspace(
        tmp_path / "workspace",
        chronology={
            "composition_timeline_id": "TL-RECORD-COMPOSED",
            "deposit_timeline_id": "TL-RECORD-ABSENT",
            "release_timeline_ids": ["TL-RECORD-RELEASED"],
        },
    )

    diagnostics = _entry_diagnostics(checker, workspace, "TL-TRUST-FORMED")

    assert "RECORD_CHRONOLOGY_REFERENCE_DANGLING" in _codes(diagnostics)


def test_a_repeated_release_reference_is_reported(checker, tmp_path):
    workspace = _trust_workspace(
        tmp_path / "workspace",
        chronology={
            "composition_timeline_id": "TL-RECORD-COMPOSED",
            "deposit_timeline_id": "TL-RECORD-DEPOSITED",
            "release_timeline_ids": ["TL-RECORD-RELEASED", "TL-RECORD-RELEASED"],
        },
    )

    diagnostics = _entry_diagnostics(checker, workspace, "TL-TRUST-FORMED")

    assert "RECORD_CHRONOLOGY_RELEASE_DUPLICATE" in _codes(diagnostics)


def test_an_incomplete_record_chronology_key_set_is_malformed(checker, tmp_path):
    workspace = _trust_workspace(
        tmp_path / "workspace",
        chronology={"composition_timeline_id": "TL-RECORD-COMPOSED"},
    )

    diagnostics = _entry_diagnostics(checker, workspace, "TL-TRUST-FORMED")

    assert "RECORD_CHRONOLOGY_MALFORMED" in _codes(diagnostics)
    assert checker.classify_result(diagnostics) == checker.RESULT_INCOMPLETE


def test_an_absent_record_chronology_is_permitted(checker, tmp_path):
    """Most entries record no Trust chronology at all."""

    workspace = _chronology_workspace(
        tmp_path / "workspace",
        [
            nf.timeline_entry(
                timeline_id="TL-DECEMBER-RECEIVE",
                participants=[MARA],
                record_chronology=None,
            )
        ],
    )

    assert _entry_diagnostics(checker, workspace, "TL-DECEMBER-RECEIVE") == ()


# ---------------------------------------------------------------------------
# DEC-015 fluent pairing
# ---------------------------------------------------------------------------


PAIR_FIELDS = dict(
    mode="PAIR",
    source_side_continuity="not-applicable",
    apparatus_mode="bidirectional-architecture",
    transmit_stage_present=True,
    person_specific_address_state="not-applicable",
    evidence_scope=(
        "Consent state and transport metadata only. This entry supports no "
        "claim about truth, intent, memory provenance, or a mental state."
    ),
)


def _pair_workspace(base, *, pair=None, evidence=None, participants=(MARA, NIA)):
    entry = nf.timeline_entry(
        timeline_id="TL-PAIRING-SESSION",
        relative_chronology="An authorized fluent pairing session.",
        participants=list(participants),
        chapter_numbers=[58],
        state=nf.technical_state(
            pair_state=pair if pair is not None else nf.pair_state(),
            pairing_evidence=evidence if evidence is not None else nf.pairing_evidence(),
            **PAIR_FIELDS
        ),
    )
    return _chronology_workspace(base, [entry])


def _transcript(**overrides):
    values = {
        "transcript_id": "PT-FIXTURE-001",
        "session_timeline_id": "TL-PAIRING-SESSION",
        "content_scope": (
            "Only the contributions the protocol transported during this "
            "recorded session."
        ),
    }
    values.update(overrides)
    return values


def test_an_authorized_pairing_session_validates(checker, tmp_path):
    workspace = _pair_workspace(tmp_path / "workspace")

    assert _entry_diagnostics(checker, workspace, "TL-PAIRING-SESSION") == ()


def test_a_deliberate_send_state_outside_the_enum_is_malformed(checker, tmp_path):
    workspace = _pair_workspace(
        tmp_path / "workspace",
        pair=nf.pair_state(deliberate_send_state="assumed"),
    )

    diagnostics = _entry_diagnostics(checker, workspace, "TL-PAIRING-SESSION")

    assert "PAIR_STATE_MALFORMED" in _codes(diagnostics)
    assert checker.classify_result(diagnostics) == checker.RESULT_INCOMPLETE


@pytest.mark.parametrize("send_state", ["paused", "revoked", "integrity-failed"])
def test_a_stopped_session_transports_no_recorded_content(
    checker, tmp_path, send_state
):
    """Pause, revocation, and integrity failure all stop semantic transport."""

    workspace = _pair_workspace(
        tmp_path / "workspace",
        pair=nf.pair_state(deliberate_send_state=send_state),
        evidence=nf.pairing_evidence(
            content_recording_enabled=True,
            recording_consent_a=True,
            recording_consent_b=True,
            transcript=_transcript(),
        ),
    )

    diagnostics = _entry_diagnostics(checker, workspace, "TL-PAIRING-SESSION")

    assert "PAIR_STOPPED_SESSION_TRANSPORT" in _codes(diagnostics)
    assert checker.classify_result(diagnostics) == checker.RESULT_REVISION


@pytest.mark.parametrize("send_state", ["paused", "revoked", "integrity-failed"])
def test_a_stopped_session_with_no_transcript_is_not_a_violation(
    checker, tmp_path, send_state
):
    """Stopping is legal. Only transporting content while stopped is not."""

    workspace = _pair_workspace(
        tmp_path / "workspace",
        pair=nf.pair_state(deliberate_send_state=send_state),
    )

    assert _entry_diagnostics(checker, workspace, "TL-PAIRING-SESSION") == ()


def test_recovery_is_expressed_by_a_later_required_send_state(checker, tmp_path):
    """A failure entry and its recovery are separate records, not one guess."""

    failed = nf.timeline_entry(
        timeline_id="TL-PAIRING-FAILED",
        relative_chronology="Clipping and latency break the session.",
        participants=[MARA, NIA],
        chapter_numbers=[58],
        state=nf.technical_state(
            pair_state=nf.pair_state(deliberate_send_state="integrity-failed"),
            pairing_evidence=nf.pairing_evidence(),
            **PAIR_FIELDS
        ),
    )
    recovered = nf.timeline_entry(
        timeline_id="TL-PAIRING-RECOVERED",
        relative_chronology="An explicit retry restores deliberate sending.",
        participants=[MARA, NIA],
        chapter_numbers=[59],
        state=nf.technical_state(
            pair_state=nf.pair_state(deliberate_send_state="required"),
            pairing_evidence=nf.pairing_evidence(
                content_recording_enabled=True,
                recording_consent_a=True,
                recording_consent_b=True,
                transcript=_transcript(
                    session_timeline_id="TL-PAIRING-RECOVERED"
                ),
            ),
            **PAIR_FIELDS
        ),
    )
    workspace = _chronology_workspace(tmp_path / "workspace", [failed, recovered])
    index, load_diagnostics = checker.load_reference_index(
        workspace.manuscript_root
    )

    assert load_diagnostics == ()
    for timeline_id in ("TL-PAIRING-FAILED", "TL-PAIRING-RECOVERED"):
        record = index.unique("TimelineEntry", timeline_id)
        assert checker.check_technical_state(record, index) == ()


@pytest.mark.parametrize(
    "stand_in",
    [
        "CHAR-DEAD-001",
        "CHAR-ABSENT-001",
        "CHAR-REPLACEMENT-001",
        "CHAR-SIMULATION-001",
        "CHAR-ARCHIVE-001",
        "CHAR-MODEL-001",
        "CHAR-RECONSTRUCTION-001",
    ],
)
def test_a_pairing_partner_who_is_not_a_registered_person_is_rejected(
    checker, tmp_path, stand_in
):
    """`PAIR` joins two living people, so each partner must resolve to a person.

    The objective test is registration: a partner resolves to a POVProfile
    character or an approved character-name extension, or it resolves to nothing.
    A dead, absent, replacement, simulated, archived, modelled, or reconstructed
    stand-in has no such record, so it is reported rather than interpreted.
    """

    workspace = _pair_workspace(
        tmp_path / "workspace",
        pair=nf.pair_state(participants=[MARA, stand_in]),
        participants=[MARA, stand_in],
    )

    diagnostics = _entry_diagnostics(checker, workspace, "TL-PAIRING-SESSION")

    assert "CHARACTER_REFERENCE_DANGLING" in _codes(diagnostics)
    assert stand_in in " ".join(item.observed for item in diagnostics)


def test_transferable_calibration_is_rejected(checker, tmp_path):
    workspace = _pair_workspace(
        tmp_path / "workspace",
        pair=nf.pair_state(calibration_transferable=True),
    )

    diagnostics = _entry_diagnostics(checker, workspace, "TL-PAIRING-SESSION")

    assert "PAIR_STATE_INVARIANT" in _codes(diagnostics)


def test_calibration_must_resolve_to_the_same_two_participants(checker, tmp_path):
    workspace = _pair_workspace(
        tmp_path / "workspace",
        pair=nf.pair_state(calibration_participants=[MARA, MARA]),
    )

    diagnostics = _entry_diagnostics(checker, workspace, "TL-PAIRING-SESSION")

    assert "PAIR_STATE_INVARIANT" in _codes(diagnostics)


@pytest.mark.parametrize(
    "consent_key", ["current", "revocable", "authorized_a", "authorized_b"]
)
def test_every_consent_flag_is_required_for_an_authorized_session(
    checker, tmp_path, consent_key
):
    consent = {
        "current": True,
        "specific_act": "Synthetic fixture consent to this pairing session.",
        "revocable": True,
        "authorized_a": True,
        "authorized_b": True,
    }
    consent[consent_key] = False
    workspace = _pair_workspace(
        tmp_path / "workspace", pair=nf.pair_state(consent=consent)
    )

    diagnostics = _entry_diagnostics(checker, workspace, "TL-PAIRING-SESSION")

    assert "PAIR_STATE_INVARIANT" in _codes(diagnostics)


def test_content_recording_needs_both_participants_and_starts_off(
    checker, tmp_path
):
    default = nf.pairing_evidence()
    assert default["content_recording_enabled"] is False
    assert default["transcript"] is None

    workspace = _pair_workspace(
        tmp_path / "workspace",
        evidence=nf.pairing_evidence(
            content_recording_enabled=True,
            recording_consent_a=True,
            recording_consent_b=False,
            transcript=_transcript(),
        ),
    )

    diagnostics = _entry_diagnostics(checker, workspace, "TL-PAIRING-SESSION")

    assert "PAIRING_EVIDENCE_INVARIANT" in _codes(diagnostics)


def test_a_transcript_cannot_reach_outside_its_recorded_session(
    checker, tmp_path
):
    workspace = _pair_workspace(
        tmp_path / "workspace",
        evidence=nf.pairing_evidence(
            content_recording_enabled=True,
            recording_consent_a=True,
            recording_consent_b=True,
            transcript=_transcript(session_timeline_id="TL-PAIRING-OTHER"),
        ),
    )

    diagnostics = _entry_diagnostics(checker, workspace, "TL-PAIRING-SESSION")

    assert "PAIRING_EVIDENCE_INVARIANT" in _codes(diagnostics)


@pytest.mark.parametrize(
    "metadata_key",
    [
        "consent_state_metadata_present",
        "transport_metadata_present",
        "metadata_semantically_opaque",
    ],
)
def test_consent_and_transport_metadata_stay_mandatory_and_opaque(
    checker, tmp_path, metadata_key
):
    """Opaque metadata is what forbids semantic reconstruction from logs."""

    workspace = _pair_workspace(
        tmp_path / "workspace",
        evidence=nf.pairing_evidence(overrides={metadata_key: False}),
    )

    diagnostics = _entry_diagnostics(checker, workspace, "TL-PAIRING-SESSION")

    assert "PAIRING_EVIDENCE_INVARIANT" in _codes(diagnostics)


def test_exactly_one_mode_is_declared_per_record(checker, tmp_path):
    """A `PAIR` entry carrying a `cancel_state` is claiming two modes at once."""

    entry = nf.timeline_entry(
        timeline_id="TL-PAIRING-SESSION",
        participants=[MARA, NIA],
        chapter_numbers=[58],
        state=nf.technical_state(
            pair_state=nf.pair_state(),
            pairing_evidence=nf.pairing_evidence(),
            cancel_state=nf.cancel_state(),
            **PAIR_FIELDS
        ),
    )
    workspace = _chronology_workspace(tmp_path / "workspace", [entry])

    diagnostics = _entry_diagnostics(checker, workspace, "TL-PAIRING-SESSION")

    assert "TIMELINE_MODE_INVARIANT" in _codes(diagnostics)


def test_no_pairing_record_confirms_the_provenance_question(checker, tmp_path):
    """`evidence_scope` is required text, and no field can yield provenance.

    The checker enforces that the limit is stated and that pairing evidence stays
    opaque. Whether a scene honors that limit is an editorial judgment.
    """

    workspace = _pair_workspace(tmp_path / "workspace")
    index, _ = checker.load_reference_index(workspace.manuscript_root)
    record = index.unique("TimelineEntry", "TL-PAIRING-SESSION")
    state = record.payload["technical_state"]

    assert state["evidence_scope"].strip()
    assert state["pairing_evidence"]["metadata_semantically_opaque"] is True
    assert checker.check_technical_state(record, index) == ()

    blank_entry = nf.timeline_entry(
        timeline_id="TL-PAIRING-SESSION",
        participants=[MARA, NIA],
        chapter_numbers=[58],
        state=nf.technical_state(
            pair_state=nf.pair_state(),
            pairing_evidence=nf.pairing_evidence(),
            **dict(PAIR_FIELDS, evidence_scope="   ")
        ),
    )
    blank = _chronology_workspace(tmp_path / "blank", [blank_entry])
    diagnostics = _entry_diagnostics(checker, blank, "TL-PAIRING-SESSION")
    assert "TIMELINE_TECHNICAL_STATE_MALFORMED" in _codes(diagnostics)
