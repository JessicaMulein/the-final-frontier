"""Focused scope, roster, and restraint tests for task 8.25.

Validates: Requirements 1.1, 4.1-4.10, 7.12, 7.17, 9.5-9.7, 12.11, and 15.1-15.5.

Three things share this file because each one is about a *boundary* the checker
has to hold rather than a value it has to compare.

The first is scope: which text a literal-phrase scan is allowed to read. Song
lyrics and planning documents are outside it, so a phrase quoted in a Canon_Source
never counts toward a Chapter_File total.

The second is the POV roster: exactly one Anchor_POV, and a provisional load
vector fixed as a sorted multiset. That last detail decides two tests that look
contradictory until you see the rule -- changing a number is rejected, while
swapping which POV owns which number is not, because Requirement 12.11 keeps that
choice with the author.

The third is restraint, including the case that motivated the checker's most
recent fix: an absent closed motif family. Absence is the strongest form of the
violation, and a check that iterated over the families it happened to find would
have let it pass in silence.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Sequence, Tuple

import pytest

import novel_fixtures as nf

checker = nf.load_checker()

PAIR_A = "CHAR-001"
PAIR_B = "CHAR-002"


# ---------------------------------------------------------------------------
# Probes
# ---------------------------------------------------------------------------


def _two_character_roster() -> List[Dict[str, Any]]:
    """Two POVProfiles, so a two-person pairing has two resolvable participants.

    The default supporting set carries one character, which would make even a
    lawful pairing look like a dangling reference.
    """

    return [
        nf.pov_profile(
            character_id=PAIR_A, pov_id="POV-MARA", voice_brief_id="VOICE-A", anchor=True
        ),
        nf.pov_profile(
            character_id=PAIR_B, pov_id="POV-NIA", voice_brief_id="VOICE-B", anchor=False
        ),
    ]


def _session_reference_codes(*participants: str) -> Tuple[str, ...]:
    """Character-reference diagnostics for a pairing session's participants."""

    entry = nf.timeline_entry(
        timeline_id="TL-SESSION",
        chronology_kind="point",
        participants=list(participants),
        state=nf.technical_state(
            mode="PAIR",
            apparatus_mode="bench-transmit",
            transmit_stage_present=True,
            person_specific_address_state="locked",
            pair_state=nf.pair_state(
                participants=participants, calibration_participants=participants
            ),
            pairing_evidence=nf.pairing_evidence(),
        ),
    )
    index = nf.record_index(
        supporting=False,
        POVProfile=_two_character_roster(),
        VoiceBrief=[
            nf.voice_brief(pov_id="POV-MARA", voice_brief_id="VOICE-A"),
            nf.voice_brief(pov_id="POV-NIA", voice_brief_id="VOICE-B"),
        ],
        TimelineEntry=[entry],
    )
    return tuple(
        sorted({item.code for item in checker.check_character_references(index)})
    )


def _roster_codes(profiles: Sequence[Mapping[str, Any]]) -> Tuple[str, ...]:
    """POV roster diagnostics for a set of POVProfiles."""

    index = nf.record_index(
        supporting=False,
        POVProfile=list(profiles),
        VoiceBrief=[
            nf.voice_brief(
                pov_id=profile["pov_id"], voice_brief_id=profile["voice_brief_id"]
            )
            for profile in profiles
        ],
    )
    return tuple(sorted({item.code for item in checker.check_pov_roster(index)}))


def _plan_of_record_profiles(
    *, loads: Mapping[str, Mapping[str, int]] = None
) -> List[Dict[str, Any]]:
    """The four-POV roster of record, with exactly one Anchor_POV."""

    matrix = loads or nf.MANUSCRIPT_POV_LOAD
    profiles = []
    for position, pov_id in enumerate(nf.MANUSCRIPT_POV_LOAD):
        profiles.append(
            nf.pov_profile(
                character_id="CHAR-{0:03d}".format(position + 1),
                pov_id=pov_id,
                voice_brief_id="VOICE-{0}".format(pov_id),
                anchor=position == 0,
                provisional_load=matrix[pov_id],
            )
        )
    return profiles


def _family_total_codes(events: Sequence[Mapping[str, Any]]) -> Tuple[str, ...]:
    """Closed-family total diagnostics for a motif ledger."""

    index = nf.record_index(supporting=False, MotifEvent=list(events))
    return tuple(
        sorted({item.code for item in checker.check_motif_family_totals(index)})
    )


# ---------------------------------------------------------------------------
# Literal scan scope: Chapter_File prose only
# ---------------------------------------------------------------------------


def test_song_text_is_never_scanned_for_literal_phrases(tmp_path) -> None:
    """A protected phrase inside a Canon_Source does not count as an occurrence.

    The songs are the source of the protected wording, so of course they contain
    it. Counting those occurrences would make every constraint fail on arrival and
    would also mean the checker was reading files outside the manuscript.
    """

    workspace = nf.manuscript_workspace(tmp_path)
    songs = workspace.root / "songs"
    songs.mkdir(parents=True, exist_ok=True)
    # Far more occurrences than any constraint allows, so if the scan reached this
    # file at all the count would be unmistakably wrong.
    nf.write_text(songs, "Case Zero.md", "Did I say yes?\n" * 12)

    result = checker.run_scope(
        (), scope=checker.SCOPE_GLOBAL, manuscript_root=workspace.manuscript_root
    )
    codes = [item.code for item in result.diagnostics]
    assert "LITERAL_DID_I_SAY_YES_SCOPE" not in codes, codes
    assert checker.exit_status_for_result(
        checker.classify_result(result.diagnostics)
    ) == 0, codes


def test_planning_documents_are_never_scanned_for_literal_phrases(
    tmp_path,
) -> None:
    """The ledger that *declares* a phrase constraint also quotes the phrase.

    A scan that read planning documents would count the declaration itself, so
    the constraint would be violated by the act of recording it.
    """

    workspace = nf.calibration_workspace(tmp_path)
    ledger = workspace.manuscript_root / "planning" / "motif-ledger.md"
    assert ledger.exists(), ledger
    assert "Did I say yes?" in ledger.read_text(encoding="utf-8")

    result = checker.run_scope(
        (), scope=checker.SCOPE_GLOBAL, manuscript_root=workspace.manuscript_root
    )
    codes = [item.code for item in result.diagnostics]
    assert "LITERAL_DID_I_SAY_YES_SCOPE" not in codes, codes


# ---------------------------------------------------------------------------
# POV roster, load vector, and session ownership
# ---------------------------------------------------------------------------


def test_the_plan_of_record_roster_is_clean() -> None:
    """Four POVs, one anchor, and the provisional load vector as recorded."""

    assert _roster_codes(_plan_of_record_profiles()) == ()


def test_exactly_one_anchor_pov_is_required() -> None:
    """Requirement 4.2: one Anchor_POV, so neither none nor two will do."""

    profiles = _plan_of_record_profiles()

    none_anchored = [dict(profile, anchor=False) for profile in profiles]
    assert "POV_ANCHOR_COUNT" in _roster_codes(none_anchored)

    two_anchored = [dict(profile) for profile in profiles]
    two_anchored[1]["anchor"] = True
    assert "POV_ANCHOR_COUNT" in _roster_codes(two_anchored)


def test_changing_a_load_number_is_rejected() -> None:
    """Requirement 15.3: the provisional load vector is fixed."""

    matrix = {key: dict(value) for key, value in nf.MANUSCRIPT_POV_LOAD.items()}
    first = list(matrix)[0]
    movement = list(matrix[first])[0]
    matrix[first][movement] = matrix[first][movement] + 5

    codes = _roster_codes(_plan_of_record_profiles(loads=matrix))
    assert "POV_PROVISIONAL_LOAD_VECTOR" in codes, codes


def test_swapping_which_pov_owns_which_load_is_not_rejected() -> None:
    """Requirement 12.11: the vector is a sorted multiset, not an assignment.

    This is the deliberate seam between the two requirements. Requirement 15.3
    fixes *which numbers* the book carries; deciding which POV carries which of
    them is an authorial choice, and a checker that enforced the pairing would be
    making that choice instead.
    """

    matrix = {key: dict(value) for key, value in nf.MANUSCRIPT_POV_LOAD.items()}
    names = list(matrix)
    matrix[names[0]], matrix[names[1]] = matrix[names[1]], matrix[names[0]]

    assert _roster_codes(_plan_of_record_profiles(loads=matrix)) == ()


def test_a_fifth_pov_is_rejected_by_the_load_vector() -> None:
    """A fifth POV cannot be admitted, and the rule that stops it is the vector.

    The roster size rule permits three to five POVs generally, so nothing there
    objects. What objects is Requirement 15.3: a five-element multiset of loads
    cannot equal the four-element vector the design fixed.
    """

    profiles = _plan_of_record_profiles()
    smallest = dict(profiles[-1]["provisional_load"])
    movement = [key for key, value in smallest.items() if value > 0][0]
    smallest[movement] = smallest[movement] - 1
    profiles[-1] = dict(profiles[-1], provisional_load=smallest)
    profiles.append(
        nf.pov_profile(
            character_id="CHAR-005",
            pov_id="POV-005",
            voice_brief_id="VOICE-POV-005",
            anchor=False,
            provisional_load={
                key: (1 if key == movement else 0) for key in smallest
            },
        )
    )

    codes = _roster_codes(profiles)
    assert "POV_PROVISIONAL_LOAD_VECTOR" in codes, codes


def test_a_session_between_two_roster_characters_is_accepted() -> None:
    """A pairing session is owned by characters the roster actually knows."""

    assert _session_reference_codes(PAIR_A, PAIR_B) == ()


@pytest.mark.parametrize(
    "stand_in",
    (
        "ARCHIVE-001",
        "MODEL-001",
        "RECON-001",
        "SIM-001",
        "GROUP-001",
        "CHAR-999",
    ),
)
def test_a_stand_in_cannot_own_a_pairing_session(stand_in: str) -> None:
    """An archive, a model, a reconstruction, a simulation, a group mind, an absence.

    None of them resolve to a roster character, and that is the objective handle:
    the checker does not need to understand what a reconstruction *is* to refuse a
    participant who is not a person on the roster.
    """

    codes = _session_reference_codes(PAIR_A, stand_in)
    assert "CHARACTER_REFERENCE_DANGLING" in codes, (stand_in, codes)


def test_a_dead_roster_character_draws_no_diagnostic() -> None:
    """The remaining half of the living-participant rule is not machine-checkable.

    No record schema carries a living-or-dead state, so a session with a character
    who has died reads exactly like a session with one who has not. The checker
    stays silent, and the pairing is an `EditorialFinding`. Asserting otherwise
    would be claiming a guarantee the records cannot support.
    """

    assert _session_reference_codes(PAIR_A, PAIR_B) == ()


# ---------------------------------------------------------------------------
# Closed motif family totals, including the absent-family case
# ---------------------------------------------------------------------------


def test_the_ledger_of_record_satisfies_every_closed_family() -> None:
    """The whole-book ledger carries each closed family at its exact total."""

    assert _family_total_codes(nf.manuscript_motif_events()) == ()


@pytest.mark.parametrize("family", ("kettle", "record progression"))
def test_an_entirely_absent_closed_family_is_rejected(family: str) -> None:
    """A family with no events at all is the strongest form of a wrong total.

    This is a regression test. The count check used to walk the families it found
    in the ledger, so removing every event of a family removed the check along
    with it, and the global gate passed a manuscript whose kettle motif was never
    ledgered. At whole-book scope a complete ledger is a precondition, so an
    absent family cannot be excused as not-yet-written.
    """

    remaining = [
        event
        for event in nf.manuscript_motif_events()
        if event["family"] != family
    ]
    assert len(remaining) < len(nf.manuscript_motif_events()), family
    codes = _family_total_codes(remaining)
    assert "MOTIF_FAMILY_EVENT_COUNT" in codes, (family, codes)


@pytest.mark.parametrize("family", ("kettle", "record progression"))
def test_dropping_one_event_from_a_closed_family_is_rejected(
    family: str,
) -> None:
    """One short is a wrong total too, which is what the old check did catch."""

    events = list(nf.manuscript_motif_events())
    for position, event in enumerate(events):
        if event["family"] == family:
            del events[position]
            break
    else:  # pragma: no cover - the ledger always carries both families
        pytest.fail("no {0} event to drop".format(family))

    codes = _family_total_codes(events)
    assert "MOTIF_FAMILY_EVENT_COUNT" in codes, (family, codes)


# ---------------------------------------------------------------------------
# Restraint: protected wording and open questions
# ---------------------------------------------------------------------------


def test_protected_wording_is_carried_but_never_scored() -> None:
    """The canonical extent is recorded as wording, not as a derivable quantity.

    `protected_wording` tells an author which phrasing to preserve. The checker
    carries it and does not read it, which is why a record may describe the fact in
    its own words while still protecting the phrase. Comparing the two would be
    semantic reading.
    """

    fact = nf.canon_fact(
        canon_id="CF-EXTENT-001",
        protected_wording="three counties wide",
        statement="Mara describes the defensive quiet as three counties wide.",
    )
    assert fact["protected_wording"] == "three counties wide"

    paraphrased = nf.canon_fact(
        canon_id="CF-EXTENT-002",
        protected_wording="three counties wide",
        statement="Mara gives the extent of the defensive quiet without naming a county.",
    )
    index = nf.record_index(supporting=False, CanonFact=[fact, paraphrased])
    assert checker.check_canon_facts(index) == ()


def test_a_derived_radius_draws_no_automated_diagnostic() -> None:
    """Turning the canonical extent into a radius is a reading, so it stays human.

    There is no ledgered constraint on this wording and no field for a radius, so
    a record asserting one is structurally ordinary. Rejecting it would require
    interpreting the sentence, which is the boundary this checker does not cross;
    the reading is recorded as an `EditorialFinding` instead.
    """

    radial = nf.novel_extension(
        extension_id="EXT-RADIUS-001",
        fact="The affected area had a radius of roughly eleven miles.",
    )
    index = nf.record_index(NovelExtension=[radial])
    assert checker.check_novel_extensions(index) == ()


def test_open_questions_stay_open_without_complaint() -> None:
    """The rights-footer follow-up and the inward-frontier premise stay unresolved.

    An open question is a legitimate recorded state, not missing work. The checker
    accepts an unresolved reveal with no owner and no scheduled release, and it
    would reject an attempt to quietly close one -- which is the direction that
    actually needs guarding.
    """

    open_items = [
        nf.reveal(
            reveal_id="REV-RIGHTS-FOOTER",
            fact_id="FACT-RIGHTS-FOOTER",
            truth_status="unresolved",
        ),
        nf.reveal(
            reveal_id="REV-INWARD-FRONTIER",
            fact_id="FACT-INWARD-FRONTIER",
            truth_status="unresolved",
        ),
    ]
    index = nf.record_index(supporting=False, Reveal=open_items)
    assert checker.check_reveals(index) == ()

    closed = nf.reveal(
        reveal_id="REV-RIGHTS-FOOTER",
        fact_id="FACT-RIGHTS-FOOTER",
        truth_status="unresolved",
        reader_release_chapter=128,
    )
    index = nf.record_index(supporting=False, Reveal=[closed])
    assert checker.check_reveals(index) != ()
