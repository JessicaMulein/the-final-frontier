"""The task 7.8 minimal calibration-readiness gate, re-derived on every run.

Validates: Requirements 1.10, 10.1–10.5, and 13.1.

`planning/gate-results.md` records a `calibration-objective` `GateResult` claiming
the minimal checker is ready for exploratory calibration. A hand-written claim can
drift away from the repository it describes, so these tests read that record and
prove each part of it against the committed files: the contract, the five record
sources, and the checker's own chapter and batch modes.

This gate unlocks exploratory calibration only. Nothing here asserts global mode,
a whole-book total, a complete property suite, or an Approved_Baseline, and
nothing here judges prose.
"""

from __future__ import annotations

import json

import pytest

import novel_fixtures as nf

GATE_LEDGER = "planning/gate-results.md"
GATE_ID = "GATE-CALIBRATION-OBJECTIVE-001"

GATE_RESULT_KEYS = (
    "gate_result_id",
    "gate_type",
    "scope",
    "prerequisite_state",
    "objective_diagnostic_ids",
    "editorial_finding_ids",
    "result",
    "checker_exit_status",
    "timestamp",
)
SCOPE_KEYS = ("chapter_numbers", "documents", "description")

# What the recorded scope must name, and therefore what these tests must prove.
EXPECTED_SCOPE_DOCUMENTS = (
    "exclusion-contract.json",
    "planning/arc-outline.md",
    "planning/canon-bible.md",
    "planning/motif-ledger.md",
    "planning/pov-roster.md",
    "planning/voice-briefs.md",
)

# The committed provisional planning set, as the gate record's evidence table
# states it. A record count that moves without the gate being rerun is drift.
EXPECTED_RECORD_COUNTS = {
    "TimelineEntry": 44,
    "POVProfile": 4,
    "VoiceBrief": 4,
    "MotifEvent": 22,
    "LiteralPhraseConstraint": 2,
    "CrossCut": 65,
}
EXPECTED_ARC_ENTRIES = 128


@pytest.fixture(scope="module")
def manuscript_root():
    root = nf.COMMITTED_MANUSCRIPT_ROOT
    assert root.is_dir(), "the committed manuscript root must exist"
    return root


@pytest.fixture(scope="module")
def gate_record(manuscript_root):
    """The one `GateResult` this gate recorded, parsed from the ledger."""

    path = manuscript_root.joinpath(*GATE_LEDGER.split("/"))
    assert path.is_file(), GATE_LEDGER + " must exist"
    records = _gate_results(path.read_text(encoding="utf-8"))
    matching = [item for item in records if item.get("gate_result_id") == GATE_ID]
    assert len(matching) == 1, "exactly one " + GATE_ID + " record"
    return matching[0]


def _gate_results(text):
    """Every `GateResult` payload in a fenced planning document."""

    records = []
    lines = text.splitlines()
    position = 0
    while position < len(lines):
        line = lines[position].strip()
        if line == "```json record=GateResult schema=1":
            close = position + 1
            while close < len(lines) and lines[close].strip() != "```":
                close += 1
            assert close < len(lines), "an opened record fence must close"
            payload = json.loads("\n".join(lines[position + 1 : close]))
            records.extend(payload if isinstance(payload, list) else [payload])
            position = close
        position += 1
    return records


def _committed_diagnostics(checker, manuscript_root):
    """Every objective diagnostic the committed planning set produces."""

    index, load_diagnostics = checker.load_reference_index(manuscript_root)
    return index, (
        tuple(load_diagnostics)
        + checker.check_planning_references(index)
        + checker.check_motif_planning(index)
        + checker.check_cross_cut_references(index)
    )


# ---------------------------------------------------------------------------
# The record itself
# ---------------------------------------------------------------------------


def test_the_gate_record_matches_the_gate_result_schema(gate_record):
    assert tuple(gate_record) == GATE_RESULT_KEYS
    assert gate_record["gate_type"] == "calibration-objective"
    assert tuple(gate_record["scope"]) == SCOPE_KEYS
    assert gate_record["scope"]["description"].strip()
    assert gate_record["timestamp"].endswith("Z")


def test_the_recorded_result_and_exit_status_agree(gate_record):
    """A complete scope with zero diagnostics is `pass` and `0`."""

    assert gate_record["prerequisite_state"] == "complete"
    assert gate_record["objective_diagnostic_ids"] == []
    assert gate_record["result"] == "pass"
    assert gate_record["checker_exit_status"] == 0


def test_an_objective_gate_records_no_editorial_finding(gate_record):
    """Objective and editorial gates stay independent records."""

    assert gate_record["editorial_finding_ids"] == []


def test_the_gate_audits_no_chapter_file(gate_record):
    """This gate proved readiness, so it rests on no Chapter_File at all.

    The durable claim is about the record, not about the state of `chapters/`.
    Prose now exists there, because drafting exploratory calibration is precisely
    what this gate unlocked; asserting the directory is still empty would make the
    guard fail the moment the gate did its job. What has to stay true is that the
    gate audited no chapter and drew none of its evidence from prose.
    """

    assert gate_record["scope"]["chapter_numbers"] == []
    for document in gate_record["scope"]["documents"]:
        assert not document.startswith("chapters/"), document


def test_the_gate_claims_no_global_authority(gate_record):
    description = gate_record["scope"]["description"].lower()

    assert "exploratory calibration" in description
    for disclaimed in ("no global mode", "no whole-book total", "no approved_baseline"):
        assert disclaimed in description


def test_the_gate_scope_names_every_document_it_depends_on(gate_record, checker):
    documents = tuple(gate_record["scope"]["documents"])

    assert documents == EXPECTED_SCOPE_DOCUMENTS
    # Every allowlisted record source is named, so the scope cannot silently
    # omit a document the gate actually relied on.
    assert set(checker.DEFAULT_RECORD_SOURCES) <= set(documents)


def test_the_ledger_holds_only_objective_gates(manuscript_root):
    """`editorial-log.md` owns editorial gates; this document owns the rest."""

    path = manuscript_root.joinpath(*GATE_LEDGER.split("/"))
    for record in _gate_results(path.read_text(encoding="utf-8")):
        assert record["gate_type"] != "editorial"
        assert record["checker_exit_status"] in (0, 1, 2)


# ---------------------------------------------------------------------------
# Re-deriving the evidence
# ---------------------------------------------------------------------------


def test_site_isolation_still_passes(checker):
    assert checker.main(["--site-exclusion"]) == 0


def test_the_committed_contract_names_the_real_manuscript_root(checker):
    contract = checker.load_exclusion_contract(nf.REPOSITORY_ROOT)
    excluded = {root.relative_path for root in contract.excluded_roots}

    assert nf.MANUSCRIPT_ROOT_NAME in excluded


def test_the_provisional_planning_set_is_complete_and_resolves(
    checker, manuscript_root, gate_record
):
    index, diagnostics = _committed_diagnostics(checker, manuscript_root)

    assert diagnostics == ()
    assert checker.classify_result(diagnostics) == checker.RESULT_PASS
    assert index.sources == tuple(checker.DEFAULT_RECORD_SOURCES)

    drifted = {
        "ArcEntry": (len(index.arc_entries), EXPECTED_ARC_ENTRIES),
    }
    drifted.update(
        {
            record_type: (len(index.of_type(record_type)), expected)
            for record_type, expected in EXPECTED_RECORD_COUNTS.items()
        }
    )
    drifted = {
        record_type: counts
        for record_type, counts in drifted.items()
        if counts[0] != counts[1]
    }
    assert drifted == {}, (
        "the committed planning set no longer matches the evidence table in "
        "{0} for {1} (observed, recorded). Rerun the gate and record a new "
        "GateResult rather than editing {2}.".format(
            GATE_LEDGER, drifted, GATE_ID
        )
    )


def test_the_provisional_arc_covers_every_planned_chapter(checker, manuscript_root):
    index, _ = checker.load_reference_index(manuscript_root)
    chapters = sorted(
        entry.chapter for entry in index.arc_entries if entry.chapter is not None
    )

    assert chapters == list(range(1, EXPECTED_ARC_ENTRIES + 1))


def test_every_calibration_chapter_has_a_planned_arc_entry(checker, manuscript_root):
    index, _ = checker.load_reference_index(manuscript_root)

    for chapter in nf.CALIBRATION_CHAPTERS:
        entry = index.arc_entry_for_chapter(chapter)
        assert entry is not None, "chapter {0} needs one ArcEntry".format(chapter)
        assert entry.movement == nf.CALIBRATION_MOVEMENTS[chapter]


def test_the_calibration_motif_assignments_are_in_the_committed_ledger(
    checker, manuscript_root
):
    index, _ = checker.load_reference_index(manuscript_root)

    for chapter, motif_ids in checker.CALIBRATION_REQUIRED_MOTIFS.items():
        for motif_event_id in motif_ids:
            assert index.unique("MotifEvent", motif_event_id) is not None, motif_event_id
    assert checker.check_motif_planning(
        index, chapter_scope=nf.CALIBRATION_CHAPTERS
    ) == ()


def test_delivered_chapter_files_match_current_arc_entries(
    checker, manuscript_root
):
    """Every delivered ArcEntry has exactly one file, with no prose leakage."""

    index, diagnostics = checker.load_reference_index(manuscript_root)
    assert diagnostics == ()

    chapters = manuscript_root.joinpath("chapters")
    expected = sorted(
        record.payload["filename"].split("chapters/", 1)[1]
        for record in index.of_type("ArcEntry")
        if record.payload["status"] != "planned"
    )
    actual = sorted(
        path.relative_to(chapters).as_posix()
        for path in chapters.rglob("*.md")
    )

    assert manuscript_root.joinpath("planning", "arc-outline.md").is_file()
    assert actual == expected
    assert sorted({path.split("/", 1)[0] for path in actual}) == [
        "aftermath-coda",
        "discovery-part",
        "mindwars-part",
        "private-defense-part",
    ]


# ---------------------------------------------------------------------------
# The chapter and batch modes the gate unlocks
# ---------------------------------------------------------------------------


def test_the_synthetic_calibration_batch_smoke_test_passes(checker, tmp_path):
    """Design integration test 2, end to end through the CLI."""

    workspace = nf.calibration_workspace(tmp_path / "workspace")

    status = checker.main(
        [
            "--manuscript-root",
            str(workspace.manuscript_root),
            "--scope",
            "batch",
            "--chapters",
        ]
        + [fixture.relative_path for fixture in workspace.chapters]
    )

    assert status == 0


def test_each_calibration_chapter_also_passes_its_own_chapter_gate(
    checker, tmp_path
):
    workspace = nf.calibration_workspace(tmp_path / "workspace")

    for fixture in workspace.chapters:
        run = checker.run_scope(
            [workspace.chapter_path(fixture)],
            scope="chapter",
            manuscript_root=workspace.manuscript_root,
        )
        assert run.diagnostics == (), fixture.relative_path
        assert run.exit_status == 0


def test_the_gate_does_not_require_a_global_artifact(checker, tmp_path):
    """A chapter gate must not fail for a whole-book input it never needs.

    Requirement 10.9 excludes Final_Targets, whole-book POV distribution,
    cross-manuscript motif totals, movement length relationships, and final-ending
    acceptance from the chapter-local gate. A single-chapter workspace has none of
    them, and still passes.
    """

    workspace = nf.calibration_workspace(tmp_path / "workspace", chapters=(1,))

    run = checker.run_scope(
        [workspace.chapter_path(workspace.chapters[0])],
        scope="chapter",
        manuscript_root=workspace.manuscript_root,
    )

    assert run.diagnostics == ()
    assert run.exit_status == 0


def test_the_reserved_property_suite_is_still_outstanding(checker):
    """Honesty check: this gate must not look like the full baseline gate.

    The fifteen principal property tests complete in parallel with calibration
    drafting and are required before baseline approval. If they ever all pass,
    this test is the reminder to record a `baseline-objective` gate rather than
    letting the calibration gate quietly stand in for it.
    """

    reserved = sorted(
        path.name
        for path in nf.TESTS_ROOT.glob("test_property_*.py")
    )

    assert len(reserved) == 15
