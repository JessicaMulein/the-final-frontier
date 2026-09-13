"""Focused synthetic tests for task 7.4 of the novel specification.

Validates: Requirements 7.2, 7.3, 7.7, 7.12, 7.14, 7.15, and 12.6.

These tests exercise only objective calibration-scope behavior. They do not
implement the task-7.5 CLI, task-7.6 rendering, the reserved principal property
modules, whole-book literal totals, or any editorial judgment.
"""

from __future__ import annotations

from typing import Mapping, Optional, Sequence

import pytest

import novel_fixtures as nf

DID_QUESTION = "Did I say yes?"
DID_CONSTRAINT_ID = "LPC-DID-I-SAY-YES"
DID_DIAGNOSTIC = "LITERAL_DID_I_SAY_YES_SCOPE"
CALIBRATION_CHAPTERS = (1, 2, 3, 4, 5, 73, 118, 124)


def _codes(diagnostics):
    return [diagnostic.code for diagnostic in diagnostics]


def _normal_prose(prefix: str = "") -> str:
    """Return normal-length neutral prose, optionally prefixed by test text."""

    separator = "" if not prefix or prefix.endswith(("\n", "\r")) else "\n"
    return prefix + separator + nf.prose_of_length(880)


def _did_event(**options):
    values = {
        "motif_event_id": "MOT-YES-01",
        "family": "authorization question",
        "movement": "mindwars_part",
        "planned_chapter": 73,
        "participating_chapters": [73],
        "representation_mode": "literal",
        "literal_constraint_id": DID_CONSTRAINT_ID,
    }
    values.update(options)
    return nf.motif_event(**values)


def _did_constraint(**options):
    values = {
        "constraint_id": DID_CONSTRAINT_ID,
        "motif_event_id": "MOT-YES-01",
        "exact_phrase": DID_QUESTION,
        "allowed_movements": ["mindwars_part"],
        "diagnostic_code": DID_DIAGNOSTIC,
    }
    values.update(options)
    return nf.literal_phrase_constraint(**values)


def _single_workspace(
    tmp_path,
    *,
    chapter: int = 1,
    movement: str = "discovery_part",
    slug: str = "literal-scope",
    prose: Optional[str] = None,
    header_motifs: Sequence[str] = (),
    arc_motifs: Optional[Sequence[str]] = None,
    motif_events: Sequence[Mapping[str, object]] = (),
    constraints: Sequence[Mapping[str, object]] = (),
    hook: str = "A synthetic fixture hook line.",
    songs: Optional[Mapping[str, str]] = None,
):
    body = _normal_prose() if prose is None else prose
    outline_motifs = header_motifs if arc_motifs is None else arc_motifs
    fixture = nf.chapter_fixture(
        chapter=chapter,
        movement=movement,
        slug=slug,
        prose=body,
        motif_events=header_motifs,
        hook=hook,
    )
    entry = nf.arc_entry(
        chapter=chapter,
        movement=movement,
        slug=slug,
        motif_events=outline_motifs,
        hook=hook,
        estimated_words=nf.count_prose_words(body),
    )
    planning = nf.reference_planning_documents(
        arc_entries=[entry],
        timeline_entries=[
            nf.timeline_entry(chapter_numbers=[chapter])
        ],
        motif_events=list(motif_events),
        literal_phrase_constraints=list(constraints),
    )
    return nf.build_workspace(
        tmp_path / "workspace",
        planning=planning,
        chapters=[fixture],
        songs=songs,
    )


def _gate(checker, workspace):
    index, load_diagnostics = checker.load_reference_index(
        workspace.manuscript_root
    )
    result = checker.check_chapter_scope(
        [workspace.chapter_path(fixture) for fixture in workspace.chapters],
        manuscript_root=workspace.manuscript_root,
        reference_index=index,
    )
    diagnostics = tuple(load_diagnostics) + tuple(result.diagnostics)
    return index, diagnostics, checker.classify_result(diagnostics)


def test_calibration_batch_assignments_pass_without_in_scope_literal_count(
    checker, tmp_path
):
    assignments = {
        1: (),
        2: (),
        3: (),
        4: (),
        5: (),
        73: ("MOT-YES-01",),
        118: ("MOT-KETTLE-01",),
        124: ("MOT-COME-04", "MOT-KETTLE-02"),
    }
    movements = {
        1: "discovery_part",
        2: "discovery_part",
        3: "discovery_part",
        4: "discovery_part",
        5: "discovery_part",
        73: "mindwars_part",
        118: "aftermath_coda",
        124: "aftermath_coda",
    }
    events = [
        _did_event(),
        nf.motif_event(
            motif_event_id="MOT-KETTLE-01",
            family="kettle",
            movement="aftermath_coda",
            planned_chapter=118,
            representation_mode="image",
        ),
        nf.motif_event(
            motif_event_id="MOT-COME-04",
            family="come in",
            movement="aftermath_coda",
            planned_chapter=124,
            representation_mode="action",
        ),
        nf.motif_event(
            motif_event_id="MOT-KETTLE-02",
            family="kettle",
            movement="aftermath_coda",
            planned_chapter=124,
            representation_mode="action",
        ),
    ]
    chapters = []
    entries = []
    timelines = []
    for chapter in CALIBRATION_CHAPTERS:
        movement = movements[chapter]
        slug = "calibration-{0:03d}".format(chapter)
        prose = _normal_prose(
            (DID_QUESTION + " " + DID_QUESTION) if chapter == 73 else ""
        )
        timeline_id = "TL-FIXTURE-{0:03d}".format(chapter)
        chapters.append(
            nf.chapter_fixture(
                chapter=chapter,
                movement=movement,
                slug=slug,
                timeline_id=timeline_id,
                motif_events=assignments[chapter],
                prose=prose,
            )
        )
        entries.append(
            nf.arc_entry(
                chapter=chapter,
                movement=movement,
                slug=slug,
                timeline_id=timeline_id,
                motif_events=assignments[chapter],
                estimated_words=nf.count_prose_words(prose),
                calibration_selected=True,
                representative_purpose=(
                    "Synthetic representative calibration purpose."
                    if chapter > 5
                    else None
                ),
            )
        )
        timelines.append(
            nf.timeline_entry(
                timeline_id=timeline_id,
                chapter_numbers=[chapter],
            )
        )

    workspace = nf.build_workspace(
        tmp_path / "workspace",
        planning=nf.reference_planning_documents(
            arc_entries=entries,
            timeline_entries=timelines,
            motif_events=events,
            literal_phrase_constraints=[_did_constraint()],
        ),
        chapters=chapters,
    )
    _index, diagnostics, result = _gate(checker, workspace)

    assert diagnostics == ()
    assert result == checker.RESULT_PASS


def test_ledger_assignment_missing_from_both_header_and_arc_is_reported(
    checker, tmp_path
):
    workspace = _single_workspace(
        tmp_path,
        chapter=73,
        movement="mindwars_part",
        motif_events=[_did_event()],
        constraints=[_did_constraint()],
    )
    _index, diagnostics, result = _gate(checker, workspace)

    assert "MOTIF_LEDGER_HEADER_DISAGREEMENT" in _codes(diagnostics)
    assert "MOTIF_LEDGER_ARC_DISAGREEMENT" in _codes(diagnostics)
    assert result == checker.RESULT_REVISION


def test_required_calibration_event_cannot_disappear_with_all_three_records(
    checker, tmp_path
):
    workspace = _single_workspace(
        tmp_path,
        chapter=118,
        movement="aftermath_coda",
    )
    _index, diagnostics, result = _gate(checker, workspace)

    assert _codes(diagnostics) == ["MOTIF_CALIBRATION_ASSIGNMENT_MISSING"]
    assert result == checker.RESULT_REVISION


def test_consistently_moved_authorization_event_still_violates_resolved_mapping(
    checker, tmp_path
):
    moved = _did_event(
        planned_chapter=74,
        participating_chapters=[74],
    )
    workspace = _single_workspace(
        tmp_path,
        chapter=74,
        movement="mindwars_part",
        header_motifs=["MOT-YES-01"],
        motif_events=[moved],
        constraints=[_did_constraint()],
    )
    _index, diagnostics, result = _gate(checker, workspace)

    assert "MOTIF_RESOLVED_MAPPING_DISAGREEMENT" in _codes(diagnostics)
    assert result == checker.RESULT_REVISION


@pytest.mark.parametrize(
    "event, chapter, movement",
    [
        (
            nf.motif_event(
                motif_event_id="MOT-CHAIN-01",
                family="spectrum / wire / voice",
                movement="mindwars_part",
                planned_chapter=13,
                representation_mode="image",
            ),
            13,
            "mindwars_part",
        ),
        (
            nf.motif_event(
                motif_event_id="MOT-COPPER-02",
                family="copper / quiet",
                movement="private_defense_part",
                planned_chapter=70,
                representation_mode="image",
            ),
            70,
            "private_defense_part",
        ),
    ],
)
def test_direct_chain_and_copper_records_enforce_resolved_mapping(
    checker, tmp_path, event, chapter, movement
):
    workspace = _single_workspace(
        tmp_path,
        chapter=chapter,
        movement=movement,
        header_motifs=[event["motif_event_id"]],
        motif_events=[event],
    )
    _index, diagnostics, result = _gate(checker, workspace)

    assert "MOTIF_RESOLVED_MAPPING_DISAGREEMENT" in _codes(diagnostics)
    assert result == checker.RESULT_REVISION


def test_unapproved_fourth_chain_event_is_rejected_for_a_direct_record(
    checker, tmp_path
):
    event = nf.motif_event(
        motif_event_id="MOT-CHAIN-04",
        family="spectrum / wire / voice",
        movement="discovery_part",
        planned_chapter=14,
    )
    workspace = _single_workspace(
        tmp_path,
        chapter=14,
        movement="discovery_part",
        header_motifs=["MOT-CHAIN-04"],
        motif_events=[event],
    )
    _index, diagnostics, result = _gate(checker, workspace)

    assert "MOTIF_CLOSED_FAMILY_EXTENSION" in _codes(diagnostics)
    assert result == checker.RESULT_REVISION


def test_every_exact_occurrence_outside_mindwars_is_reported(checker, tmp_path):
    prose = _normal_prose(DID_QUESTION + "\r\n" + DID_QUESTION + "\r\n")
    prose = prose.replace("\n", "\r\n")
    workspace = _single_workspace(
        tmp_path,
        prose=prose,
        motif_events=[_did_event()],
        constraints=[_did_constraint()],
    )
    _index, diagnostics, result = _gate(checker, workspace)

    literal_diagnostics = [
        diagnostic for diagnostic in diagnostics if diagnostic.code == DID_DIAGNOSTIC
    ]
    assert len(literal_diagnostics) == 2
    assert all(
        diagnostic.details == (("protected_phrase", DID_QUESTION),)
        for diagnostic in literal_diagnostics
    )
    assert result == checker.RESULT_REVISION


@pytest.mark.parametrize("occurrences", [0, 1, 3])
def test_mindwars_occurrences_have_no_in_scope_count_rule(
    checker, tmp_path, occurrences
):
    prose = _normal_prose(" ".join([DID_QUESTION] * occurrences))
    workspace = _single_workspace(
        tmp_path,
        chapter=73,
        movement="mindwars_part",
        prose=prose,
        header_motifs=["MOT-YES-01"],
        motif_events=[_did_event()],
        constraints=[_did_constraint()],
    )
    _index, diagnostics, result = _gate(checker, workspace)

    assert DID_DIAGNOSTIC not in _codes(diagnostics)
    assert diagnostics == ()
    assert result == checker.RESULT_PASS


@pytest.mark.parametrize(
    "near_match",
    [
        "did I say yes?",
        "Did I say yes!",
        "Did I yes say?",
    ],
)
def test_literal_matching_preserves_case_punctuation_and_order(
    checker, tmp_path, near_match
):
    workspace = _single_workspace(
        tmp_path,
        prose=_normal_prose(near_match),
        motif_events=[_did_event()],
        constraints=[_did_constraint()],
    )
    _index, diagnostics, result = _gate(checker, workspace)

    assert DID_DIAGNOSTIC not in _codes(diagnostics)
    assert diagnostics == ()
    assert result == checker.RESULT_PASS


def test_literal_matching_normalizes_unicode_nfc(checker, tmp_path):
    event = nf.motif_event(
        motif_event_id="MOT-CAFE-01",
        planned_chapter=73,
        movement="mindwars_part",
        representation_mode="literal",
        literal_constraint_id="LPC-CAFE-01",
    )
    constraint = nf.literal_phrase_constraint(
        constraint_id="LPC-CAFE-01",
        motif_event_id="MOT-CAFE-01",
        exact_phrase="Caf\u00e9?",
        allowed_movements=["mindwars_part"],
        diagnostic_code="LITERAL_CAFE_SCOPE",
    )
    workspace = _single_workspace(
        tmp_path,
        prose=_normal_prose("Cafe\u0301?"),
        motif_events=[event],
        constraints=[constraint],
    )
    _index, diagnostics, result = _gate(checker, workspace)

    assert _codes(diagnostics) == ["LITERAL_CAFE_SCOPE"]
    assert result == checker.RESULT_REVISION


def test_headers_planning_docs_and_songs_are_never_literal_scan_surfaces(
    checker, tmp_path
):
    event = _did_event(
        dramatic_function="Planning may quote Did I say yes? without a scan.",
    )
    workspace = _single_workspace(
        tmp_path,
        prose=_normal_prose(),
        hook=DID_QUESTION,
        motif_events=[event],
        constraints=[_did_constraint()],
        songs={"songs/quoted-source.md": DID_QUESTION + "\n"},
    )
    _index, diagnostics, result = _gate(checker, workspace)

    assert DID_DIAGNOSTIC not in _codes(diagnostics)
    assert diagnostics == ()
    assert result == checker.RESULT_PASS


def test_calibration_scope_does_not_guess_or_require_final_passage(
    checker, tmp_path
):
    events = [
        nf.motif_event(
            motif_event_id="MOT-COME-04",
            family="come in",
            movement="aftermath_coda",
            planned_chapter=124,
            representation_mode="action",
        ),
        nf.motif_event(
            motif_event_id="MOT-KETTLE-02",
            family="kettle",
            movement="aftermath_coda",
            planned_chapter=124,
            representation_mode="action",
        ),
        nf.motif_event(
            motif_event_id="MOT-WHOSE-01",
            family="provenance question",
            movement="aftermath_coda",
            planned_chapter=128,
            representation_mode="literal",
            literal_constraint_id="LPC-WHOSE-WAS-THAT",
        ),
    ]
    final_constraint = nf.literal_phrase_constraint(
        constraint_id="LPC-WHOSE-WAS-THAT",
        motif_event_id="MOT-WHOSE-01",
        exact_phrase="Whose was that?",
        allowed_movements=["aftermath_coda"],
        allowed_chapters=[128],
        allowed_files=[
            "chapters/aftermath-coda/aftermath-coda-128-knock-and-wait.md"
        ],
        allowed_span={
            "span_id": "SPAN-FINAL-PASSAGE",
            "chapter": 128,
            "start_boundary": {
                "kind": "literal-marker",
                "value": "<!-- final-passage:start -->",
            },
            "end_boundary": {"kind": "end-of-prose", "value": None},
        },
        exact_in_scope=2,
        diagnostic_code="LITERAL_WHOSE_WAS_THAT_PLACEMENT",
    )
    workspace = _single_workspace(
        tmp_path,
        chapter=124,
        movement="aftermath_coda",
        header_motifs=["MOT-COME-04", "MOT-KETTLE-02"],
        motif_events=events,
        constraints=[final_constraint],
    )
    _index, diagnostics, result = _gate(checker, workspace)

    assert "LITERAL_WHOSE_WAS_THAT_PLACEMENT" not in _codes(diagnostics)
    assert diagnostics == ()
    assert result == checker.RESULT_PASS


def test_malformed_direct_literal_constraint_fails_closed(checker, tmp_path):
    malformed = _did_constraint(
        overrides={"normalization": {"unicode": "NFD"}},
    )
    workspace = _single_workspace(
        tmp_path,
        chapter=73,
        movement="mindwars_part",
        header_motifs=["MOT-YES-01"],
        motif_events=[_did_event()],
        constraints=[malformed],
    )
    _index, diagnostics, result = _gate(checker, workspace)

    assert "LITERAL_CONSTRAINT_MALFORMED" in _codes(diagnostics)
    assert result == checker.RESULT_INCOMPLETE


def test_committed_task_74_planning_records_are_clean(checker):
    index, load_diagnostics = checker.load_reference_index(
        nf.COMMITTED_MANUSCRIPT_ROOT
    )
    global_diagnostics = checker.check_motif_planning(index)
    calibration_diagnostics = checker.check_motif_planning(
        index, chapter_scope=CALIBRATION_CHAPTERS
    )

    assert load_diagnostics == ()
    assert len(index.of_type("LiteralPhraseConstraint")) == 2
    assert global_diagnostics == ()
    assert calibration_diagnostics == ()
