"""Focused tests for task 7.3 of the `The-Final-Frontier-novel` spec.

Covered surface: typed fenced record parsing for the allowlisted record sources,
stable-ID indexing with duplicate identity rejected before reference resolution,
Timeline_ID / POV_ID / Character_ID / VoiceBrief / Motif_Event resolution, the
closed four-mode `technical_state` invariant table with `CancelState`,
`PairState`, and `PairingEvidence`, the Requirement 12.5 local
filename/header/outline agreements, and Cross_Cut integrity gated on the
requested batch scope.

Validates: Requirements 10.1-10.5, 12.4, 12.5, 14.1, 14.3-14.12.

Not covered here, deliberately: the Motif_Ledger's own assignment and progression
rules and literal-string scanning (task 7.4), the `--scope chapter`/`--scope
batch` CLI and its changed-reference inputs (task 7.5), the text and JSON
diagnostic surface (task 7.6), and every whole-manuscript total. `Reveal` and
`CanonFact` records are parsed but not indexed, because their reference rules
belong to later tasks.

Nothing here judges whether a scene succeeds dramatically. For chapter 73 this
module validates the objective `CANCEL` bounded-consent state and the `PAIR`
metadata and references only; whether the fluent scene or the consent conflict
works on the page is Editorial_Review's alone.

Fixtures are synthetic and live in pytest `tmp_path`, except for three tests that
read the committed planning documents to confirm the checks report nothing on
real, audited data. No test writes into the real manuscript tree.
"""

from __future__ import annotations

import pytest

import novel_fixtures as nf

DEFAULT_CHAPTER_PATH = (
    "chapters/discovery-part/discovery-part-001-synthetic-fixture.md"
)
DEFAULT_MOTIFS = ["MOT-FIXTURE-01"]


# ---------------------------------------------------------------------------
# Helpers
#
# These compose the shared builders and never restate a checker rule. Expected
# codes are written literally in each test so nothing is compared against a
# second implementation of the specification.
# ---------------------------------------------------------------------------


def _chapter(**options):
    """A Chapter_File fixture whose header agrees with the default ArcEntry."""

    options.setdefault("motif_events", DEFAULT_MOTIFS)
    return nf.chapter_fixture(**options)


def _workspace(tmp_path, *, chapters=None, **planning_options):
    if chapters is None:
        chapters = (_chapter(),)
    return nf.build_workspace(
        tmp_path / "workspace",
        planning=nf.reference_planning_documents(**planning_options),
        chapters=chapters,
    )


def _index(checker, workspace, **options):
    return checker.load_reference_index(workspace.manuscript_root, **options)


def _dedupe(diagnostics):
    """Order-preserving dedupe: two loaders may report one document fault once."""

    return tuple(dict.fromkeys(diagnostics))


def _codes(diagnostics):
    return sorted({diagnostic.code for diagnostic in diagnostics})


def _planning(checker, workspace, *, batch_scope=None):
    """Every planning-side task 7.3 diagnostic for one workspace."""

    index, load_diagnostics = _index(checker, workspace)
    return index, _dedupe(
        tuple(load_diagnostics)
        + checker.check_planning_references(index, batch_scope=batch_scope)
    )


def _gate(checker, workspace, chapters=None):
    """The whole chapter-and-planning gate, as task 7.5 will compose it."""

    index, load_diagnostics = _index(checker, workspace)
    fixtures = workspace.chapters if chapters is None else chapters
    result = checker.check_chapter_scope(
        [workspace.chapter_path(fixture) for fixture in fixtures],
        manuscript_root=workspace.manuscript_root,
        reference_index=index,
    )
    diagnostics = _dedupe(
        tuple(load_diagnostics)
        + tuple(result.diagnostics)
        + checker.check_planning_references(index)
    )
    return diagnostics, checker.classify_result(diagnostics)


def _timeline(checker, index, timeline_id):
    """The one indexed TimelineEntry record claiming `timeline_id`."""

    record = index.unique("TimelineEntry", timeline_id)
    assert record is not None, "fixture must index exactly one " + timeline_id
    return record


def _mindwars_entry(chapter=73, slug="counterphase-consent", **options):
    options.setdefault("timeline_id", "TL-FIXTURE-CANCEL")
    options.setdefault("pov_id", "POV-MARA")
    options.setdefault("motif_events", DEFAULT_MOTIFS)
    return nf.arc_entry(
        chapter=chapter, movement="mindwars_part", slug=slug, **options
    )


def _state_workspace(tmp_path, state, *, chapter=73, movement="mindwars_part"):
    """A workspace whose single Timeline entry carries `state`, in `movement`."""

    entry = nf.arc_entry(
        chapter=chapter,
        movement=movement,
        slug="mechanism-fixture",
        timeline_id="TL-FIXTURE-CANCEL",
        motif_events=DEFAULT_MOTIFS,
    )
    return nf.build_workspace(
        tmp_path / "workspace",
        planning=nf.reference_planning_documents(
            arc_entries=[entry],
            timeline_entries=[
                nf.timeline_entry(
                    timeline_id="TL-FIXTURE-CANCEL",
                    chapter_numbers=[chapter],
                    participants=["CHAR-001", "CHAR-002"],
                    state=state,
                )
            ],
            motif_events=[
                nf.motif_event(motif_event_id="MOT-FIXTURE-01", planned_chapter=chapter)
            ],
            pov_profiles=[nf.pov_profile(), nf.pov_profile(**_SECOND_PROFILE)],
            voice_briefs=[
                nf.voice_brief(),
                nf.voice_brief(
                    voice_brief_id="VOICE-FIXTURE-TWO", pov_id="POV-FIXTURE-TWO"
                ),
            ],
        ),
    )


_SECOND_PROFILE = {
    "character_id": "CHAR-002",
    "pov_id": "POV-FIXTURE-TWO",
    "selected_name": "Fixture Two",
    "anchor": False,
    "voice_brief_id": "VOICE-FIXTURE-TWO",
}


# ---------------------------------------------------------------------------
# Record parsing and the record-source allowlist
# ---------------------------------------------------------------------------


def test_records_parse_from_single_fences_and_from_json_arrays(checker):
    """Records live in typed fences holding one object or an array of objects."""

    single = nf.render_json_fence("MotifEvent", nf.motif_event())
    array = nf.render_json_fence(
        "TimelineEntry",
        [
            nf.timeline_entry(timeline_id="TL-FIXTURE-001"),
            nf.timeline_entry(timeline_id="TL-FIXTURE-002"),
        ],
    )
    grouped, diagnostics = checker.parse_planning_records(
        single + "\n" + array, source="planning/canon-bible.md"
    )

    assert diagnostics == ()
    assert len(grouped["MotifEvent"]) == 1
    assert len(grouped["TimelineEntry"]) == 2
    # An array member is located by its index so a duplicate names the record.
    assert [record.array_index for record in grouped["TimelineEntry"]] == [0, 1]
    assert grouped["MotifEvent"][0].array_index is None
    assert grouped["TimelineEntry"][1].identity.endswith("#2[1]")


def test_example_records_outside_the_allowlist_are_never_indexed(checker, tmp_path):
    """`record-schemas.md` carries illustrative records with no authority.

    Its example records would manufacture phantom duplicate identities if the
    loader globbed `planning/*.md`. The allowlist is explicit rather than an
    `EXAMPLE` name heuristic, so this proves the exclusion by pointing the loader
    at the document rather than by trusting a naming habit: the same records are
    ignored by default and reported as duplicates when explicitly requested.
    """

    workspace = _workspace(tmp_path)
    nf.write_text(
        workspace.manuscript_root,
        "planning/record-schemas.md",
        nf.planning_document(
            "planning/record-schemas.md",
            title="Record Schemas",
            preamble="Illustrative fixtures. They carry no continuity authority.",
            blocks=(
                (
                    "TimelineEntry",
                    nf.timeline_entry(timeline_id="TL-FIXTURE-001"),
                ),
            ),
        ).text(),
    )

    default_index, default_diagnostics = _index(checker, workspace)
    assert "planning/record-schemas.md" not in default_index.sources
    assert default_diagnostics == ()
    assert len(default_index.lookup("TimelineEntry", "TL-FIXTURE-001")) == 1

    widened, widened_diagnostics = _index(
        checker,
        workspace,
        sources=checker.DEFAULT_RECORD_SOURCES + ("planning/record-schemas.md",),
    )
    assert "RECORD_DUPLICATE_IDENTITY" in _codes(widened_diagnostics)
    assert widened.unique("TimelineEntry", "TL-FIXTURE-001") is None


@pytest.mark.parametrize(
    "information_string, expected_code",
    [
        ("json record=TimelineEntry schema=2", "PLANNING_FENCE_UNSUPPORTED_SCHEMA"),
        ("json record=NotARecordType schema=1", "PLANNING_RECORD_TYPE_UNKNOWN"),
        ("json record=TimelineEntry", "PLANNING_FENCE_MALFORMED"),
    ],
)
def test_unusable_fence_information_strings_report_incomplete_input(
    checker, information_string, expected_code
):
    text = nf.render_json_fence(
        "TimelineEntry", nf.timeline_entry(), information_string=information_string
    )
    grouped, diagnostics = checker.parse_planning_records(
        text, source="planning/canon-bible.md"
    )

    assert grouped == {}
    assert _codes(diagnostics) == [expected_code]
    assert checker.classify_result(diagnostics) == checker.RESULT_INCOMPLETE


@pytest.mark.parametrize(
    "payload, observed_fragment",
    [([], "empty record array"), ("TL-FIXTURE-001", "record has type str")],
)
def test_malformed_record_shape_reports_incomplete_without_inferring(
    checker, payload, observed_fragment
):
    """A malformed record is reported; no value is inferred from around it."""

    text = "Prose commentary naming TL-FIXTURE-001 and mode CANCEL.\n\n"
    text += nf.render_json_fence("TimelineEntry", payload)
    grouped, diagnostics = checker.parse_planning_records(
        text, source="planning/canon-bible.md"
    )

    assert grouped == {}
    assert _codes(diagnostics) == ["PLANNING_RECORD_MALFORMED"]
    assert observed_fragment in diagnostics[0].observed


def test_missing_record_source_document_fails_closed(checker, tmp_path):
    workspace = nf.build_workspace(
        tmp_path / "workspace",
        planning=nf.reference_planning_documents()[:-1],
    )
    index, diagnostics = _index(checker, workspace)

    assert "planning/motif-ledger.md" not in index.sources
    assert _codes(diagnostics) == ["PLANNING_DOCUMENT_MISSING"]
    assert checker.classify_result(diagnostics) == checker.RESULT_INCOMPLETE
    assert checker.exit_status_for_result(checker.RESULT_INCOMPLETE) == 2


def test_arc_entry_parsing_still_reads_only_arc_entries(checker, tmp_path):
    """Task 7.2's loader stays restricted to its own record type."""

    workspace = _workspace(tmp_path)
    entries, diagnostics = checker.load_arc_entries(
        workspace.manuscript_root / "planning" / "canon-bible.md",
        relative_path="planning/canon-bible.md",
    )

    assert entries == ()
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# Duplicate identity, resolved before any reference resolves
# ---------------------------------------------------------------------------


def test_duplicate_stable_id_is_reported_instead_of_a_dangling_reference(
    checker, tmp_path
):
    """Validation order steps 4 and 5: duplicates are rejected before resolution.

    A chapter referencing a duplicated Timeline_ID must not also be told the
    reference dangles. One fault, one diagnostic, and the duplicate outranks it.
    """

    workspace = _workspace(
        tmp_path,
        timeline_entries=[
            nf.timeline_entry(timeline_id="TL-FIXTURE-001"),
            nf.timeline_entry(
                timeline_id="TL-FIXTURE-001", relative_chronology="A second claim."
            ),
        ],
    )
    diagnostics, result = _gate(checker, workspace)

    assert _codes(diagnostics) == ["RECORD_DUPLICATE_IDENTITY"]
    assert result == checker.RESULT_INCOMPLETE


@pytest.mark.parametrize(
    "second_entry_options, expected_item",
    [
        ({"slug": "second-fixture"}, "chapter 1"),
        ({"chapter": 2, "filename": DEFAULT_CHAPTER_PATH}, DEFAULT_CHAPTER_PATH),
    ],
)
def test_arc_entry_chapter_and_filename_are_independently_unique(
    checker, tmp_path, second_entry_options, expected_item
):
    """The outline's own identity keys, checked across the whole document.

    A duplicate is caught even when no Chapter_File exists for it yet, which is
    the state the manuscript is in while the outline is still provisional.
    """

    second = dict(second_entry_options)
    second.setdefault("chapter", 1)
    workspace = _workspace(
        tmp_path,
        arc_entries=[
            nf.arc_entry(chapter=1, motif_events=DEFAULT_MOTIFS),
            nf.arc_entry(motif_events=DEFAULT_MOTIFS, **second),
        ],
    )
    _index_, diagnostics = _planning(checker, workspace)

    assert _codes(diagnostics) == ["ARC_ENTRY_DUPLICATE_IDENTITY"]
    assert diagnostics[0].item == expected_item
    assert checker.classify_result(diagnostics) == checker.RESULT_INCOMPLETE


def test_duplicate_character_id_across_two_profiles_is_a_duplicate_identity(
    checker, tmp_path
):
    workspace = _workspace(
        tmp_path,
        pov_profiles=[
            nf.pov_profile(),
            nf.pov_profile(
                character_id="CHAR-001",
                pov_id="POV-FIXTURE-TWO",
                selected_name="Fixture Two",
                anchor=False,
                voice_brief_id="VOICE-FIXTURE-TWO",
            ),
        ],
        voice_briefs=[
            nf.voice_brief(),
            nf.voice_brief(
                voice_brief_id="VOICE-FIXTURE-TWO", pov_id="POV-FIXTURE-TWO"
            ),
        ],
    )
    _index_, diagnostics = _planning(checker, workspace)

    assert "CHARACTER_ID_DUPLICATE_IDENTITY" in _codes(diagnostics)
    assert checker.classify_result(diagnostics) == checker.RESULT_INCOMPLETE


@pytest.mark.parametrize(
    "state, resolves",
    [("approved", True), ("provisional", False), ("retired", False)],
)
def test_character_registry_union_covers_approved_name_extensions(
    checker, tmp_path, state, resolves
):
    """A non-viewpoint Character ID resolves through its approved extension.

    Holding an ID licenses no viewpoint: the profile count, the POV_ID, and the
    Voice_Brief obligation are untouched. A `provisional` extension declares no
    resolvable ID yet and a `retired` one declares none any longer.
    """

    workspace = _workspace(
        tmp_path,
        timeline_entries=[
            nf.timeline_entry(
                timeline_id="TL-FIXTURE-001", participants=["CHAR-001", "CHAR-005"]
            )
        ],
        novel_extensions=[
            nf.character_name_extension(character_id="CHAR-005", state=state)
        ],
    )
    index, diagnostics = _planning(checker, workspace)

    assert ("CHAR-005" in index.character_ids) is resolves
    assert index.lookup("POVProfile", "CHAR-005") == ()
    if resolves:
        assert diagnostics == ()
    else:
        assert _codes(diagnostics) == ["CHARACTER_REFERENCE_DANGLING"]
        assert checker.classify_result(diagnostics) == checker.RESULT_REVISION


def test_character_name_extension_must_agree_with_the_profile_name(
    checker, tmp_path
):
    """One ID declared by both a profile and an extension is one character."""

    workspace = _workspace(
        tmp_path,
        novel_extensions=[
            nf.character_name_extension(
                character_id="CHAR-001",
                fact="CHAR-001 identifies Someone Else entirely.",
            )
        ],
    )
    index, diagnostics = _planning(checker, workspace)

    assert index.character_ids == ("CHAR-001",)
    assert _codes(diagnostics) == ["CHARACTER_NAME_EXTENSION_DISAGREEMENT"]


def test_character_id_is_read_from_the_fact_field_and_never_from_prose(
    checker, tmp_path
):
    """The ID is the first whitespace-delimited token of the record's own `fact`.

    A `character-name` extension whose `fact` opens with prose declares no ID,
    even when the surrounding document names one. Nothing here reads a heading,
    a table, a list, or a sentence of commentary.
    """

    workspace = _workspace(
        tmp_path,
        novel_extensions=[
            nf.character_name_extension(
                character_id="CHAR-005",
                fact="The interpreter CHAR-005 is named Fixture Five.",
            )
        ],
    )
    index, diagnostics = _planning(checker, workspace)

    assert "CHAR-005" not in index.character_ids
    assert _codes(diagnostics) == ["CHARACTER_NAME_EXTENSION_MALFORMED"]
    assert checker.classify_result(diagnostics) == checker.RESULT_INCOMPLETE


def test_two_profiles_naming_one_voice_brief_is_a_many_to_one_reference(
    checker, tmp_path
):
    workspace = _workspace(
        tmp_path,
        pov_profiles=[
            nf.pov_profile(),
            nf.pov_profile(
                character_id="CHAR-002",
                pov_id="POV-FIXTURE-TWO",
                selected_name="Fixture Two",
                anchor=False,
            ),
        ],
    )
    _index_, diagnostics = _planning(checker, workspace)

    assert "VOICE_BRIEF_MANY_TO_ONE" in _codes(diagnostics)


def test_voice_brief_must_point_back_at_the_profile_that_names_it(
    checker, tmp_path
):
    """A one-to-one reference that disagrees in one direction is reported."""

    workspace = _workspace(
        tmp_path,
        voice_briefs=[nf.voice_brief(pov_id="POV-FIXTURE-TWO")],
    )
    _index_, diagnostics = _planning(checker, workspace)

    assert _codes(diagnostics) == ["VOICE_BRIEF_POV_DISAGREEMENT"]


# ---------------------------------------------------------------------------
# Chapter-local direct references
# ---------------------------------------------------------------------------


def test_conforming_chapter_resolves_every_direct_reference(checker, tmp_path):
    workspace = _workspace(tmp_path)
    diagnostics, result = _gate(checker, workspace)

    assert diagnostics == ()
    assert result == checker.RESULT_PASS
    assert checker.exit_status_for_result(result) == 0


@pytest.mark.parametrize(
    "header_options, expected_code",
    [
        ({"timeline_id": "TL-FIXTURE-ABSENT"}, "TIMELINE_REFERENCE_DANGLING"),
        ({"pov_id": "POV-FIXTURE-ABSENT"}, "POV_REFERENCE_DANGLING"),
        ({"motif_events": ["MOT-FIXTURE-ABSENT"]}, "MOTIF_EVENT_REFERENCE_DANGLING"),
    ],
)
def test_dangling_header_references_are_reported(
    checker, tmp_path, header_options, expected_code
):
    """A dangling ID is an objective violation, not incomplete input."""

    workspace = _workspace(tmp_path, chapters=(_chapter(**header_options),))
    diagnostics, result = _gate(checker, workspace)

    assert expected_code in _codes(diagnostics)
    assert result == checker.RESULT_REVISION
    assert checker.exit_status_for_result(result) == 1


def test_dangling_outline_reference_is_reported_for_the_owning_chapter(
    checker, tmp_path
):
    """The ArcEntry is a Direct_Planning_Reference, so its own refs resolve too."""

    workspace = _workspace(
        tmp_path,
        arc_entries=[
            nf.arc_entry(
                chapter=1,
                timeline_id="TL-FIXTURE-001",
                motif_events=DEFAULT_MOTIFS,
                record_horizon={
                    "through_timeline_id": "TL-FIXTURE-ABSENT",
                    "knowledge_limit": "Synthetic fixture knowledge limit.",
                },
            )
        ],
    )
    diagnostics, result = _gate(checker, workspace)

    assert _codes(diagnostics) == ["TIMELINE_REFERENCE_DANGLING"]
    assert result == checker.RESULT_REVISION


def test_motif_event_not_assigned_to_this_chapter_is_reported(checker, tmp_path):
    workspace = _workspace(
        tmp_path,
        arc_entries=[
            nf.arc_entry(chapter=1, motif_events=DEFAULT_MOTIFS),
            nf.arc_entry(chapter=2, slug="second-fixture", motif_events=[]),
        ],
        motif_events=[
            nf.motif_event(motif_event_id="MOT-FIXTURE-01", planned_chapter=2)
        ],
    )
    diagnostics, result = _gate(checker, workspace)

    codes = _codes(diagnostics)
    assert "MOTIF_EVENT_CHAPTER_DISAGREEMENT" in codes
    assert "CHAPTER_MOTIF_EVENTS_DISAGREEMENT" not in codes
    assert result == checker.RESULT_REVISION


@pytest.mark.parametrize(
    "header_options, expected_code",
    [
        ({"timeline_id": "TL-FIXTURE-002"}, "CHAPTER_TIMELINE_DISAGREEMENT"),
        ({"pov_id": "POV-FIXTURE-TWO"}, "CHAPTER_POV_DISAGREEMENT"),
        ({"motif_events": []}, "CHAPTER_MOTIF_EVENTS_DISAGREEMENT"),
        ({"hook": "A different hook line."}, "CHAPTER_HOOK_DISAGREEMENT"),
        ({"status": "approved"}, "CHAPTER_STATUS_DISAGREEMENT"),
    ],
)
def test_header_and_outline_must_agree_on_every_local_reference(
    checker, tmp_path, header_options, expected_code
):
    """Requirement 12.5 for one chapter's own outline entry.

    Hook *presence* and textual agreement are objective. Hook quality stays with
    Editorial_Review and is never scored here.
    """

    workspace = _workspace(
        tmp_path,
        chapters=(_chapter(**header_options),),
        timeline_entries=[
            nf.timeline_entry(timeline_id="TL-FIXTURE-001"),
            nf.timeline_entry(timeline_id="TL-FIXTURE-002"),
        ],
        pov_profiles=[nf.pov_profile(), nf.pov_profile(**_SECOND_PROFILE)],
        voice_briefs=[
            nf.voice_brief(),
            nf.voice_brief(
                voice_brief_id="VOICE-FIXTURE-TWO", pov_id="POV-FIXTURE-TWO"
            ),
        ],
    )
    diagnostics, result = _gate(checker, workspace)

    assert expected_code in _codes(diagnostics)
    assert result == checker.RESULT_REVISION


def test_filename_header_and_outline_agreement_survives_reference_checking(
    checker, tmp_path
):
    """The task 7.2 four-way agreement rule keeps reporting alongside 7.3."""

    workspace = _workspace(
        tmp_path,
        chapters=(_chapter(chapter=1, header=None, movement="discovery_part"),),
        arc_entries=[
            nf.arc_entry(
                chapter=1,
                movement="mindwars_part",
                filename=DEFAULT_CHAPTER_PATH,
                motif_events=DEFAULT_MOTIFS,
            )
        ],
    )
    diagnostics, _result = _gate(checker, workspace)

    assert "CHAPTER_MOVEMENT_DISAGREEMENT" in _codes(diagnostics)


# ---------------------------------------------------------------------------
# `technical_state`: key absence versus an explicit null
# ---------------------------------------------------------------------------


def test_present_but_null_technical_state_is_permitted(checker, tmp_path):
    """`technical_state: null` is a conforming record, not incomplete input.

    The schema permits `null` for the whole object. Reporting it as the
    pre-amendment case would be a false positive on committed data, so key
    absence and an explicit null value are deliberately distinguished.
    """

    workspace = _workspace(
        tmp_path,
        timeline_entries=[
            nf.timeline_entry(
                timeline_id="TL-FIXTURE-001", overrides={"technical_state": None}
            )
        ],
    )
    index, diagnostics = _planning(checker, workspace)
    entry = _timeline(checker, index, "TL-FIXTURE-001")

    assert entry.payload["technical_state"] is None
    assert checker.check_technical_state(entry, index) == ()
    assert diagnostics == ()


@pytest.mark.parametrize(
    "dropped",
    ["mode", "cancel_state", "pair_state", "pairing_evidence"],
)
def test_pre_amendment_record_reports_incomplete_rather_than_inferring(
    checker, tmp_path, dropped
):
    """Omitting a mechanism field is the pre-amendment case: no mode is inferred."""

    workspace = _workspace(
        tmp_path,
        timeline_entries=[
            nf.timeline_entry(
                timeline_id="TL-FIXTURE-001",
                state=nf.technical_state(drop_keys=[dropped]),
            )
        ],
    )
    index, diagnostics = _planning(checker, workspace)

    assert _codes(diagnostics) == ["TIMELINE_TECHNICAL_STATE_INCOMPLETE"]
    assert dropped in diagnostics[0].observed
    assert checker.classify_result(diagnostics) == checker.RESULT_INCOMPLETE
    assert index.unique("TimelineEntry", "TL-FIXTURE-001") is not None


def test_absent_technical_state_key_reports_incomplete(checker, tmp_path):
    workspace = _workspace(
        tmp_path,
        timeline_entries=[
            nf.timeline_entry(
                timeline_id="TL-FIXTURE-001", drop_keys=["technical_state"]
            )
        ],
    )
    _index_, diagnostics = _planning(checker, workspace)

    assert _codes(diagnostics) == ["TIMELINE_TECHNICAL_STATE_MALFORMED"]
    assert checker.classify_result(diagnostics) == checker.RESULT_INCOMPLETE


# ---------------------------------------------------------------------------
# The closed four-mode invariant table
# ---------------------------------------------------------------------------

RECEIVE_STATE = dict(
    mode="RECEIVE",
    source_side_continuity="continuous",
    receiver_offset_seconds=8,
    apparatus_mode="receive-only",
    transmit_stage_present=False,
    person_specific_address_state="locked",
)
INTRUDE_STATE = dict(
    mode="INTRUDE",
    source_side_continuity="unknown",
    apparatus_mode="bench-transmit",
    transmit_stage_present=True,
    person_specific_address_state="identified",
)
CANCEL_STATE = dict(
    mode="CANCEL",
    source_side_continuity="not-applicable",
    apparatus_mode="bidirectional-architecture",
    transmit_stage_present=True,
    person_specific_address_state="not-applicable",
)
PAIR_STATE = dict(
    mode="PAIR",
    source_side_continuity="not-applicable",
    apparatus_mode="bidirectional-architecture",
    transmit_stage_present=True,
    person_specific_address_state="not-applicable",
)


def _valid_states():
    """One conforming `technical_state` per row of the four-mode table."""

    return {
        "RECEIVE": nf.technical_state(**RECEIVE_STATE),
        "INTRUDE": nf.technical_state(**INTRUDE_STATE),
        "CANCEL": nf.technical_state(cancel_state=nf.cancel_state(), **CANCEL_STATE),
        "PAIR": nf.technical_state(
            pair_state=nf.pair_state(),
            pairing_evidence=nf.pairing_evidence(),
            **PAIR_STATE
        ),
        "not-applicable": nf.technical_state(),
    }


@pytest.mark.parametrize("mode", list(_valid_states()))
def test_each_row_of_the_four_mode_table_validates(checker, tmp_path, mode):
    workspace = _state_workspace(tmp_path, _valid_states()[mode])
    index, diagnostics = _planning(checker, workspace)
    entry = _timeline(checker, index, "TL-FIXTURE-CANCEL")

    assert entry.payload["technical_state"]["mode"] == mode
    assert checker.check_technical_state(entry, index) == ()
    assert diagnostics == ()


@pytest.mark.parametrize(
    "mode, overrides",
    [
        ("RECEIVE", {"transmit_stage_present": True}),
        ("RECEIVE", {"source_side_continuity": "discontinuous"}),
        ("INTRUDE", {"transmit_stage_present": False}),
        ("INTRUDE", {"person_specific_address_state": "not-applicable"}),
        ("CANCEL", {"person_specific_address_state": "identified"}),
        ("CANCEL", {"cancel_state": None}),
        ("PAIR", {"pair_state": None}),
        ("PAIR", {"pairing_evidence": None}),
    ],
)
def test_four_mode_table_violations_are_reported(checker, tmp_path, mode, overrides):
    """`INTRUDE` requires an address and `CANCEL` forbids one.

    That structural boundary is why an unaddressed subtractive event must never
    be recorded as `INTRUDE`, and it is validated from `mode` and the state
    fields alone.
    """

    state = dict(_valid_states()[mode])
    state.update(overrides)
    workspace = _state_workspace(tmp_path, state)
    index, _diagnostics = _planning(checker, workspace)
    entry = _timeline(checker, index, "TL-FIXTURE-CANCEL")
    diagnostics = checker.check_technical_state(entry, index)

    assert "TIMELINE_MODE_INVARIANT" in _codes(diagnostics)
    assert checker.classify_result(diagnostics) == checker.RESULT_REVISION


def test_not_applicable_fixes_no_transmit_stage(checker, tmp_path):
    """The table constrains only the three mode objects for `not-applicable`.

    A record that establishes no neural communication event is not thereby
    forced to declare an absent transmit stage, so this is not a violation.
    """

    state = nf.technical_state(mode="not-applicable", transmit_stage_present=True)
    workspace = _state_workspace(tmp_path, state)
    index, diagnostics = _planning(checker, workspace)

    assert diagnostics == ()
    assert (
        checker.check_technical_state(
            _timeline(checker, index, "TL-FIXTURE-CANCEL"), index
        )
        == ()
    )


@pytest.mark.parametrize(
    "mode, extra_object",
    [
        ("RECEIVE", "cancel_state"),
        ("INTRUDE", "pair_state"),
        ("CANCEL", "pair_state"),
        ("not-applicable", "pairing_evidence"),
    ],
)
def test_mode_specific_objects_must_be_null_outside_their_mode(
    checker, tmp_path, mode, extra_object
):
    populated = {
        "cancel_state": nf.cancel_state(),
        "pair_state": nf.pair_state(),
        "pairing_evidence": nf.pairing_evidence(),
    }[extra_object]
    state = dict(_valid_states()[mode])
    state[extra_object] = populated
    workspace = _state_workspace(tmp_path, state)
    index, _diagnostics = _planning(checker, workspace)
    diagnostics = checker.check_technical_state(
        _timeline(checker, index, "TL-FIXTURE-CANCEL"), index
    )

    assert "TIMELINE_MODE_INVARIANT" in _codes(diagnostics)


def test_mechanism_state_is_never_inferred_from_prose_commentary(
    checker, tmp_path
):
    """`evidence_scope` and `uncertainty_notes` are commentary, never state.

    A record whose commentary claims a different mode still validates against its
    `technical_state` fields, and only those.
    """

    state = nf.technical_state(
        evidence_scope=(
            "Commentary asserting this event is an addressed INTRUDE with an "
            "enumerated affected set and a recoverable inverse."
        ),
        **RECEIVE_STATE
    )
    workspace = _state_workspace(tmp_path, state)
    index, diagnostics = _planning(checker, workspace)
    entry = _timeline(checker, index, "TL-FIXTURE-CANCEL")

    assert checker.check_technical_state(entry, index) == ()
    assert diagnostics == ()


# ---------------------------------------------------------------------------
# `CancelState`
# ---------------------------------------------------------------------------


def test_bounded_local_cancel_requires_the_exposed_individual_consent(
    checker, tmp_path
):
    """`bounded-local` describes a field volume, not a targeted person."""

    state = nf.technical_state(
        cancel_state=nf.cancel_state(overrides={"individual_consent": None}),
        **CANCEL_STATE
    )
    workspace = _state_workspace(tmp_path, state)
    index, _diagnostics = _planning(checker, workspace)
    diagnostics = checker.check_technical_state(
        _timeline(checker, index, "TL-FIXTURE-CANCEL"), index
    )

    assert _codes(diagnostics) == ["CANCEL_STATE_INVARIANT"]


def test_area_scale_cancel_records_institutional_authorization_only(
    checker, tmp_path
):
    """Area-scale authorization is never individual consent from everyone affected."""

    state = nf.technical_state(
        cancel_state=nf.cancel_state(
            scope="area-scale",
            individual_consent={
                "character_id": "CHAR-002",
                "current": True,
                "specific_act": "An invalid area-scale consent claim.",
                "revocable": True,
            },
        ),
        **CANCEL_STATE
    )
    workspace = _state_workspace(tmp_path, state)
    index, _diagnostics = _planning(checker, workspace)
    diagnostics = checker.check_technical_state(
        _timeline(checker, index, "TL-FIXTURE-CANCEL"), index
    )

    assert _codes(diagnostics) == ["CANCEL_STATE_INVARIANT"]
    valid = nf.technical_state(
        cancel_state=nf.cancel_state(scope="area-scale"), **CANCEL_STATE
    )
    other = _state_workspace(tmp_path / "second", valid)
    other_index, other_diagnostics = _planning(checker, other)
    assert other_diagnostics == ()
    assert (
        checker.check_technical_state(
            _timeline(checker, other_index, "TL-FIXTURE-CANCEL"), other_index
        )
        == ()
    )


@pytest.mark.parametrize(
    "overrides",
    [
        {"additive_inverse_exists": True},
        {"affected_set_predictable_before": True},
        {"affected_set_enumerable_during": True},
        {"affected_set_fully_mapped_after": True},
        {"inserted_content": "a spoken order"},
        {"provenance_yield": "the sender's identity"},
    ],
)
def test_cancel_state_fixed_values_cannot_be_relaxed(checker, tmp_path, overrides):
    """No reversal, no enumerated set, no inserted payload, no provenance."""

    state = nf.technical_state(
        cancel_state=nf.cancel_state(overrides=overrides), **CANCEL_STATE
    )
    workspace = _state_workspace(tmp_path, state)
    index, _diagnostics = _planning(checker, workspace)
    diagnostics = checker.check_technical_state(
        _timeline(checker, index, "TL-FIXTURE-CANCEL"), index
    )

    assert _codes(diagnostics) == ["CANCEL_STATE_INVARIANT"]


def test_cancel_event_outside_the_mindwars_block_is_reported(checker, tmp_path):
    state = nf.technical_state(cancel_state=nf.cancel_state(), **CANCEL_STATE)
    workspace = _state_workspace(
        tmp_path, state, chapter=5, movement="discovery_part"
    )
    index, _diagnostics = _planning(checker, workspace)
    diagnostics = checker.check_technical_state(
        _timeline(checker, index, "TL-FIXTURE-CANCEL"), index
    )

    assert _codes(diagnostics) == ["CANCEL_CHAPTER_OUTSIDE_MINDWARS"]
    assert "5" in diagnostics[0].observed


# ---------------------------------------------------------------------------
# `PairState` and `PairingEvidence`
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "pair_overrides, expected_code",
    [
        ({"participants": ["CHAR-001"]}, "PAIR_STATE_MALFORMED"),
        (
            {"participants": ["CHAR-001", "CHAR-002", "CHAR-003"]},
            "PAIR_STATE_MALFORMED",
        ),
        ({"calibration_transferable": True}, "PAIR_STATE_INVARIANT"),
        ({"deliberate_send_state": "always-on"}, "PAIR_STATE_MALFORMED"),
    ],
)
def test_pair_state_shape_and_invariants(
    checker, tmp_path, pair_overrides, expected_code
):
    state = nf.technical_state(
        pair_state=nf.pair_state(overrides=pair_overrides),
        pairing_evidence=nf.pairing_evidence(),
        **PAIR_STATE
    )
    workspace = _state_workspace(tmp_path, state)
    index, _diagnostics = _planning(checker, workspace)
    diagnostics = checker.check_technical_state(
        _timeline(checker, index, "TL-FIXTURE-CANCEL"), index
    )

    assert expected_code in _codes(diagnostics)


def test_calibration_participants_must_equal_participants_as_a_set(
    checker, tmp_path
):
    state = nf.technical_state(
        pair_state=nf.pair_state(calibration_participants=["CHAR-001", "CHAR-003"]),
        pairing_evidence=nf.pairing_evidence(),
        **PAIR_STATE
    )
    workspace = _state_workspace(tmp_path, state)
    index, _diagnostics = _planning(checker, workspace)
    diagnostics = checker.check_technical_state(
        _timeline(checker, index, "TL-FIXTURE-CANCEL"), index
    )

    assert _codes(diagnostics) == ["PAIR_STATE_INVARIANT"]


def test_one_calibration_shared_by_two_pairs_is_many_to_one(checker, tmp_path):
    """A Pair_Calibration is unique to one pair and never transfers."""

    entry = _mindwars_entry(chapter=73)
    workspace = nf.build_workspace(
        tmp_path / "workspace",
        planning=nf.reference_planning_documents(
            arc_entries=[entry],
            motif_events=[
                nf.motif_event(motif_event_id="MOT-FIXTURE-01", planned_chapter=73)
            ],
            timeline_entries=[
                nf.timeline_entry(
                    timeline_id="TL-FIXTURE-CANCEL",
                    chapter_numbers=[73],
                    participants=["CHAR-001", "CHAR-002"],
                    state=nf.technical_state(
                        pair_state=nf.pair_state(),
                        pairing_evidence=nf.pairing_evidence(),
                        **PAIR_STATE
                    ),
                ),
                nf.timeline_entry(
                    timeline_id="TL-FIXTURE-PAIR-TWO",
                    chapter_numbers=[73],
                    participants=["CHAR-001", "CHAR-003"],
                    state=nf.technical_state(
                        pair_state=nf.pair_state(
                            participants=["CHAR-001", "CHAR-003"]
                        ),
                        pairing_evidence=nf.pairing_evidence(),
                        **PAIR_STATE
                    ),
                ),
            ],
            novel_extensions=[
                nf.character_name_extension(character_id="CHAR-002"),
                nf.character_name_extension(character_id="CHAR-003"),
            ],
        ),
    )
    _index_, diagnostics = _planning(checker, workspace)

    assert _codes(diagnostics) == ["PAIR_CALIBRATION_MANY_TO_ONE"]


@pytest.mark.parametrize(
    "evidence_options, expected_code",
    [
        (
            {"content_recording_enabled": True, "recording_consent_a": True},
            "PAIRING_EVIDENCE_INVARIANT",
        ),
        (
            {
                "transcript": {
                    "transcript_id": "TR-FIXTURE-001",
                    "session_timeline_id": "TL-FIXTURE-CANCEL",
                    "content_scope": "Contributions transported during the session.",
                }
            },
            "PAIRING_EVIDENCE_INVARIANT",
        ),
        (
            {
                "content_recording_enabled": True,
                "recording_consent_a": True,
                "recording_consent_b": True,
                "transcript": {
                    "transcript_id": "TR-FIXTURE-001",
                    "session_timeline_id": "TL-FIXTURE-OTHER",
                    "content_scope": "Contributions transported during the session.",
                },
            },
            "PAIRING_EVIDENCE_INVARIANT",
        ),
    ],
)
def test_content_recording_and_transcript_scope_are_enforced(
    checker, tmp_path, evidence_options, expected_code
):
    """Recording is off until both partners consent, separately from `PAIR`."""

    state = nf.technical_state(
        pair_state=nf.pair_state(),
        pairing_evidence=nf.pairing_evidence(**evidence_options),
        **PAIR_STATE
    )
    workspace = _state_workspace(tmp_path, state)
    index, _diagnostics = _planning(checker, workspace)
    diagnostics = checker.check_technical_state(
        _timeline(checker, index, "TL-FIXTURE-CANCEL"), index
    )

    assert expected_code in _codes(diagnostics)


@pytest.mark.parametrize(
    "key", ["consent_state_metadata_present", "metadata_semantically_opaque"]
)
def test_consent_and_transport_metadata_stay_present_and_opaque(
    checker, tmp_path, key
):
    state = nf.technical_state(
        pair_state=nf.pair_state(),
        pairing_evidence=nf.pairing_evidence(overrides={key: False}),
        **PAIR_STATE
    )
    workspace = _state_workspace(tmp_path, state)
    index, _diagnostics = _planning(checker, workspace)
    diagnostics = checker.check_technical_state(
        _timeline(checker, index, "TL-FIXTURE-CANCEL"), index
    )

    assert _codes(diagnostics) == ["PAIRING_EVIDENCE_INVARIANT"]


# ---------------------------------------------------------------------------
# Chapter 73: the objective state only
# ---------------------------------------------------------------------------

CHAPTER_73_CANCEL = "TL-MINDWARS-COUNTERPHASE"
CHAPTER_73_PAIR = "TL-PAIR-MARA-NIA-COUNTERPHASE"


def test_chapter_73_objective_cancel_and_pair_state_validate(checker, tmp_path):
    """The bounded consent state and the pairing metadata, and nothing else.

    Whether the fluent scene or the consent conflict succeeds dramatically is not
    judged here and never will be: this asserts the objective `CANCEL` scope and
    consent fields and the `PAIR` metadata and references.
    """

    workspace = nf.build_workspace(
        tmp_path / "workspace",
        planning=nf.reference_planning_documents(
            arc_entries=[
                _mindwars_entry(
                    chapter=73,
                    estimated_words=None,
                    estimated_length_class="long-outlier",
                    outlier_purpose="Synthetic fixture outlier purpose.",
                )
            ],
            motif_events=[
                nf.motif_event(motif_event_id="MOT-FIXTURE-01", planned_chapter=73)
            ],
            timeline_entries=[
                nf.timeline_entry(
                    timeline_id=CHAPTER_73_CANCEL,
                    chronology_kind="interval",
                    chapter_numbers=[70, 71, 72, 73, 74, 75, 76, 77],
                    participants=["CHAR-001", "CHAR-002"],
                    state=nf.technical_state(
                        cancel_state=nf.cancel_state(scope="bounded-local"),
                        **CANCEL_STATE
                    ),
                ),
                nf.timeline_entry(
                    timeline_id=CHAPTER_73_PAIR,
                    chronology_kind="interval",
                    chapter_numbers=[73, 74, 75],
                    participants=["CHAR-001", "CHAR-002"],
                    state=nf.technical_state(
                        pair_state=nf.pair_state(
                            participants=["CHAR-001", "CHAR-002"]
                        ),
                        pairing_evidence=nf.pairing_evidence(),
                        **PAIR_STATE
                    ),
                ),
                nf.timeline_entry(timeline_id="TL-FIXTURE-CANCEL", chapter_numbers=[73]),
            ],
            pov_profiles=[nf.pov_profile(), nf.pov_profile(**_SECOND_PROFILE)],
            voice_briefs=[
                nf.voice_brief(),
                nf.voice_brief(
                    voice_brief_id="VOICE-FIXTURE-TWO", pov_id="POV-FIXTURE-TWO"
                ),
            ],
        ),
    )
    index, diagnostics = _planning(checker, workspace)
    cancel = _timeline(checker, index, CHAPTER_73_CANCEL)
    pair = _timeline(checker, index, CHAPTER_73_PAIR)

    assert diagnostics == ()
    cancel_state = cancel.payload["technical_state"]["cancel_state"]
    assert cancel_state["scope"] == "bounded-local"
    assert cancel_state["individual_consent"]["character_id"] == "CHAR-002"
    assert cancel_state["institutional_authorization"] is None
    pair_state = pair.payload["technical_state"]["pair_state"]
    assert set(pair_state["participants"]) == {"CHAR-001", "CHAR-002"}
    assert pair_state["calibration_transferable"] is False
    evidence = pair.payload["technical_state"]["pairing_evidence"]
    assert evidence["content_recording_enabled"] is False
    assert evidence["transcript"] is None


# ---------------------------------------------------------------------------
# Cross_Cut references, gated on the requested batch scope
# ---------------------------------------------------------------------------


def _cross_cut_workspace(tmp_path, *, declaring_chapters=(1, 2), chapters=(1, 2)):
    entries = []
    for chapter in (1, 2, 3):
        entries.append(
            nf.arc_entry(
                chapter=chapter,
                slug="fixture-{0}".format(chapter),
                motif_events=[],
                cross_cuts=["CUT-FIXTURE-001"]
                if chapter in declaring_chapters
                else "none",
            )
        )
    return nf.build_workspace(
        tmp_path / "workspace",
        planning=nf.reference_planning_documents(
            arc_entries=entries,
            cross_cuts=[nf.cross_cut(chapters=list(chapters))],
            motif_events=[nf.motif_event()],
        ),
    )


def test_reciprocal_cross_cut_inside_the_scope_validates(checker, tmp_path):
    workspace = _cross_cut_workspace(tmp_path)
    index, diagnostics = _planning(checker, workspace, batch_scope={1, 2})

    assert diagnostics == ()
    assert index.declared_cross_cuts() == {"CUT-FIXTURE-001": (1, 2)}


def test_one_sided_cross_cut_is_reported_when_the_scope_holds_both_chapters(
    checker, tmp_path
):
    workspace = _cross_cut_workspace(tmp_path, declaring_chapters=(1,))
    _index_, diagnostics = _planning(checker, workspace, batch_scope={1, 2})

    assert "CROSS_CUT_ONE_SIDED" in _codes(diagnostics)


def test_cross_cut_reciprocity_is_not_judged_from_a_partial_batch_scope(
    checker, tmp_path
):
    """A scope missing a participant cannot decide reciprocity, so it stays quiet.

    Only Cross_Cut references whose requested batch scope contains every
    participating changed record are evaluated. Chapter 2 is outside this scope,
    so its missing declaration is not yet knowable and is not reported.
    """

    workspace = _cross_cut_workspace(tmp_path, declaring_chapters=(1,))
    _index_, narrow = _planning(checker, workspace, batch_scope={1})
    _index_two, wide = _planning(checker, workspace, batch_scope=None)

    assert narrow == ()
    assert "CROSS_CUT_ONE_SIDED" in _codes(wide)


def test_nonparticipant_declaration_is_reported(checker, tmp_path):
    workspace = _cross_cut_workspace(tmp_path, declaring_chapters=(1, 2, 3))
    _index_, diagnostics = _planning(checker, workspace)

    assert _codes(diagnostics) == ["CROSS_CUT_UNDECLARED_PARTICIPANT"]
    assert "chapters 3" in diagnostics[0].observed


def test_dangling_cross_cut_declaration_is_reported_from_its_own_chapter(
    checker, tmp_path
):
    """A declaration with no target is decidable from the declaring chapter alone."""

    workspace = _workspace(
        tmp_path,
        arc_entries=[
            nf.arc_entry(
                chapter=1, motif_events=DEFAULT_MOTIFS, cross_cuts=["CUT-FIXTURE-ABSENT"]
            )
        ],
    )
    _index_, diagnostics = _planning(checker, workspace, batch_scope={1})

    assert _codes(diagnostics) == ["CROSS_CUT_REFERENCE_DANGLING"]


@pytest.mark.parametrize(
    "cross_cut_options, expected_code",
    [
        ({"chapters": [1]}, "CROSS_CUT_MALFORMED"),
        ({"handoff_mode": "vibe-cut"}, "CROSS_CUT_MALFORMED"),
        ({"declared_by_chapters": [1]}, "CROSS_CUT_INVARIANT"),
        (
            {
                "material_narrative_value": [
                    {"chapter": 1, "value": "One participating value."}
                ]
            },
            "CROSS_CUT_INVARIANT",
        ),
        (
            {"shared_timeline_id": None, "shared_consequence": None},
            "CROSS_CUT_INVARIANT",
        ),
    ],
)
def test_cross_cut_record_shape_and_invariants(
    checker, tmp_path, cross_cut_options, expected_code
):
    entries = [
        nf.arc_entry(
            chapter=chapter,
            slug="fixture-{0}".format(chapter),
            motif_events=[],
            cross_cuts=["CUT-FIXTURE-001"],
        )
        for chapter in (1, 2)
    ]
    workspace = nf.build_workspace(
        tmp_path / "workspace",
        planning=nf.reference_planning_documents(
            arc_entries=entries,
            cross_cuts=[nf.cross_cut(**cross_cut_options)],
            motif_events=[nf.motif_event()],
        ),
    )
    _index_, diagnostics = _planning(checker, workspace)

    assert expected_code in _codes(diagnostics)


def test_arc_entry_with_no_cross_cut_uses_the_exact_string_none(checker, tmp_path):
    """`"none"` is the Arc_Outline's only absence marker for this field."""

    workspace = _workspace(
        tmp_path,
        arc_entries=[
            nf.arc_entry(chapter=1, motif_events=DEFAULT_MOTIFS, cross_cuts=[])
        ],
    )
    _index_, diagnostics = _planning(checker, workspace)

    assert _codes(diagnostics) == ["CROSS_CUT_DECLARATION_MALFORMED"]
    assert checker.classify_result(diagnostics) == checker.RESULT_INCOMPLETE


# ---------------------------------------------------------------------------
# The committed planning documents
#
# The real records were audited before this task ran. These three tests assert
# that the implemented checks report nothing on them, so a future edit that
# breaks referential integrity fails here rather than silently.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def committed(checker):
    return checker.load_reference_index(nf.COMMITTED_MANUSCRIPT_ROOT)


def test_committed_records_load_and_index_without_diagnostics(checker, committed):
    index, diagnostics = committed

    assert diagnostics == ()
    assert index.sources == checker.DEFAULT_RECORD_SOURCES
    assert len(index.arc_entries) == 128
    assert len(index.of_type("TimelineEntry")) == 44
    assert len(index.of_type("POVProfile")) == 4
    assert len(index.of_type("VoiceBrief")) == 4
    assert len(index.of_type("MotifEvent")) == 22
    assert len(index.of_type("CrossCut")) == 65
    # Four viewpoints plus twelve approved non-viewpoint character-name
    # extensions. DEC-018 added CHAR-015 Joss Calder and CHAR-016 Ruth Venn as
    # the clause 9 warmth relationships for Nia and Mara; neither creates a
    # POVProfile, so the profile count above is unchanged.
    assert len(index.character_ids) == 16


def test_committed_records_report_no_objective_violations(checker, committed):
    index, load_diagnostics = committed
    diagnostics = _dedupe(
        tuple(load_diagnostics) + checker.check_planning_references(index)
    )

    assert [diagnostic.format_text() for diagnostic in diagnostics] == []
    assert checker.classify_result(diagnostics) == checker.RESULT_PASS


def test_committed_chapter_73_records_carry_the_expected_objective_state(
    checker, committed
):
    """The real records behind the calibration chapter, read as state not prose."""

    index, _load_diagnostics = committed
    cancel = index.unique("TimelineEntry", CHAPTER_73_CANCEL)
    pair = index.unique("TimelineEntry", CHAPTER_73_PAIR)
    assert cancel is not None and pair is not None

    cancel_state = cancel.payload["technical_state"]
    assert cancel_state["mode"] == "CANCEL"
    assert cancel_state["transmit_stage_present"] is True
    assert cancel_state["person_specific_address_state"] == "not-applicable"
    assert cancel_state["cancel_state"]["scope"] == "bounded-local"
    assert (
        cancel_state["cancel_state"]["individual_consent"]["character_id"] == "CHAR-002"
    )
    assert cancel_state["cancel_state"]["institutional_authorization"] is None
    assert all(
        index.movement_for_chapter(number) == "mindwars_part"
        for number in cancel.payload["chapter_numbers"]
    )

    pair_technical = pair.payload["technical_state"]
    assert pair_technical["mode"] == "PAIR"
    assert set(pair_technical["pair_state"]["participants"]) == {
        "CHAR-001",
        "CHAR-002",
    }
    assert pair_technical["pair_state"]["calibration_transferable"] is False
    assert pair_technical["pair_state"]["deliberate_send_state"] == "required"
    assert pair_technical["pairing_evidence"]["content_recording_enabled"] is False
    assert pair_technical["pairing_evidence"]["transcript"] is None
    assert 73 in pair.payload["chapter_numbers"]

    assert checker.check_technical_state(cancel, index) == ()
    assert checker.check_technical_state(pair, index) == ()
