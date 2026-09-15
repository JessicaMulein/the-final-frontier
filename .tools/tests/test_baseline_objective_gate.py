"""The task 8.27 complete-objective-checker gate, re-derived on every run.

Validates: Requirements 1.14, 11.1-11.9, 12.14, and 12.15.

`planning/gate-results.md` records a `baseline-objective` `GateResult` claiming
that global mode is complete, that exits are deterministic, and that the mandatory
suite is green. A hand-written claim drifts, so these tests read that record and
prove each part of it against the repository and the checker as committed.

This gate does not approve the Baseline. Requirement 12.14 also needs the
calibration Editorial_Review, which is human-only, and nothing here judges prose.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Sequence, Tuple

import pytest

import novel_fixtures as nf

GATE_LEDGER = "planning/gate-results.md"
GATE_ID = "GATE-BASELINE-OBJECTIVE-001"

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

# The numbers the gate record's evidence table states. A count that moves without
# the gate being rerun is drift, which is the whole reason this module exists.
EXPECTED_CHAPTERS = 128
EXPECTED_PROSE_WORDS = 89607
EXPECTED_PROPERTY_MODULES = 15
EXPECTED_PROPERTY_EXAMPLES = 100

# The three whole-book documents only the global gate may read. Requirement 10.9
# keeps them out of a Chapter_Local_Gate's reach.
GLOBAL_ONLY_SOURCES = (
    "planning/arc-changes.md",
    "planning/editorial-log.md",
    "planning/gate-results.md",
)


@pytest.fixture(scope="module")
def checker() -> Any:
    return nf.load_checker()


@pytest.fixture(scope="module")
def manuscript_root():
    root = nf.COMMITTED_MANUSCRIPT_ROOT
    assert root.is_dir(), "the committed manuscript root must exist"
    return root


@pytest.fixture(scope="module")
def gate_record(manuscript_root) -> Dict[str, Any]:
    """The one `GateResult` this gate recorded, parsed from the ledger."""

    path = manuscript_root.joinpath(*GATE_LEDGER.split("/"))
    assert path.is_file(), GATE_LEDGER + " must exist"
    matching = [
        item
        for item in _gate_results(path.read_text(encoding="utf-8"))
        if item.get("gate_result_id") == GATE_ID
    ]
    assert len(matching) == 1, "exactly one " + GATE_ID + " record"
    return matching[0]


@pytest.fixture(scope="module")
def synthetic_manuscript(tmp_path_factory) -> Any:
    """A complete 128-chapter workspace, built once for the module."""

    return nf.manuscript_workspace(tmp_path_factory.mktemp("baseline-objective"))


def _gate_results(text: str) -> List[Dict[str, Any]]:
    """Every `GateResult` payload in a fenced planning document."""

    records: List[Dict[str, Any]] = []
    lines = text.splitlines()
    position = 0
    while position < len(lines):
        if lines[position].strip() == "```json record=GateResult schema=1":
            close = position + 1
            while close < len(lines) and lines[close].strip() != "```":
                close += 1
            assert close < len(lines), "an opened record fence must close"
            payload = json.loads("\n".join(lines[position + 1 : close]))
            records.extend(payload if isinstance(payload, list) else [payload])
            position = close
        position += 1
    return records


def _exit_status(checker: Any, diagnostics: Sequence[Any]) -> int:
    return checker.exit_status_for_result(checker.classify_result(diagnostics))


def _codes(diagnostics: Sequence[Any]) -> List[str]:
    return [item.code for item in diagnostics]


# ---------------------------------------------------------------------------
# The record itself
# ---------------------------------------------------------------------------


def test_the_gate_record_is_well_formed(gate_record) -> None:
    """The record carries exactly the `GateResult` schema keys."""

    assert set(gate_record) == set(GATE_RESULT_KEYS), sorted(gate_record)
    assert set(gate_record["scope"]) == set(SCOPE_KEYS), sorted(gate_record["scope"])


def test_the_gate_record_claims_a_passing_baseline_objective_gate(
    checker, gate_record
) -> None:
    """A `baseline-objective` gate, complete, passing, and at exit 0."""

    assert gate_record["gate_type"] == "baseline-objective"
    assert gate_record["gate_type"] in checker.GATE_TYPES
    assert gate_record["prerequisite_state"] == "complete"
    assert gate_record["result"] == "pass"
    assert gate_record["result"] in checker.GATE_RESULTS
    assert gate_record["checker_exit_status"] == 0
    assert gate_record["objective_diagnostic_ids"] == []


def test_the_gate_record_audits_no_chapter_and_no_editorial_finding(
    gate_record,
) -> None:
    """It proves readiness, so it names no chapter and borrows no human finding.

    An objective gate that cited an `EditorialFinding` would be claiming a reading
    it did not perform, which is the confusion the two separate ledgers exist to
    prevent.
    """

    assert gate_record["scope"]["chapter_numbers"] == []
    assert gate_record["editorial_finding_ids"] == []


def test_the_gate_record_is_accepted_by_the_checker(checker, gate_record) -> None:
    """The record validates under the same rules as any other GateResult."""

    index = nf.record_index(supporting=False, GateResult=[gate_record])
    assert checker.check_gate_results(index) == (), _codes(
        checker.check_gate_results(index)
    )


def test_the_gate_record_follows_the_calibration_gate(manuscript_root) -> None:
    """Reruns get new identifiers, so both records stand side by side.

    The calibration gate is not edited or replaced by this one. It recorded what
    was true when exploratory drafting was unlocked, and it stays readable.
    """

    path = manuscript_root.joinpath(*GATE_LEDGER.split("/"))
    ids = [item["gate_result_id"] for item in _gate_results(path.read_text(encoding="utf-8"))]
    assert "GATE-CALIBRATION-OBJECTIVE-001" in ids, ids
    assert GATE_ID in ids, ids
    assert ids.index("GATE-CALIBRATION-OBJECTIVE-001") < ids.index(GATE_ID), ids


# ---------------------------------------------------------------------------
# Complete global mode
# ---------------------------------------------------------------------------


def test_global_mode_passes_a_complete_manuscript(
    checker, synthetic_manuscript
) -> None:
    """Zero diagnostics and exit 0 over 128 chapters, as the record claims."""

    files = sorted(synthetic_manuscript.manuscript_root.rglob("chapters/**/*.md"))
    assert len(files) == EXPECTED_CHAPTERS, len(files)

    run = checker.run_scope(
        (),
        scope=checker.SCOPE_GLOBAL,
        manuscript_root=synthetic_manuscript.manuscript_root,
    )
    assert run.diagnostics == (), _codes(run.diagnostics)
    assert _exit_status(checker, run.diagnostics) == 0


def test_the_recorded_word_total_still_holds(checker, synthetic_manuscript) -> None:
    """The evidence table's 89,607 words are recounted rather than trusted.

    The number is only meaningful if it is the number the checker would count
    today, so it is recomputed from the Prose_Bodies on every run.
    """

    total = 0
    classes: Dict[str, int] = {}
    for path in sorted(
        synthetic_manuscript.manuscript_root.rglob("chapters/**/*.md")
    ):
        relative = str(path.relative_to(synthetic_manuscript.manuscript_root))
        report = checker.chapter_length_report(
            checker.parse_chapter_document(
                path.read_text(encoding="utf-8"), relative_path=relative
            )
        )
        total += report.observed_words
        classes[report.observed_length_class] = (
            classes.get(report.observed_length_class, 0) + 1
        )

    assert total == EXPECTED_PROSE_WORDS, total
    normal = classes.get("normal", 0)
    # Exact integer arithmetic, the same way the checker decides the 80% floor.
    assert normal * 100 >= EXPECTED_CHAPTERS * 80, classes


def test_the_committed_repository_fails_closed_at_global_scope(
    checker, manuscript_root
) -> None:
    """The real manuscript exits 2, and the record says so rather than hiding it.

    128 ArcEntries are planned and no Chapter_File exists. A checker that reported
    a pass here would be treating an unwritten book as a finished one, so exit 2 is
    the correct answer and this gate's claim is scoped to the synthetic run.
    """

    run = checker.run_scope(
        (), scope=checker.SCOPE_GLOBAL, manuscript_root=manuscript_root
    )
    assert _exit_status(checker, run.diagnostics) == 2
    assert "OUTLINE_ENTRY_WITHOUT_FILE" in _codes(run.diagnostics)


def test_the_planning_reference_checks_are_reachable_from_global_scope(
    checker,
) -> None:
    """`check_planning_references` is wired into the global gate.

    This is the defect that motivated the fix: the function existed, its rules had
    tests, and no scope called it. Asserting the call site by name would be
    brittle, so the proof is behavioural -- a broken mechanism state must surface
    in a global run.
    """

    import inspect

    source = inspect.getsource(checker.check_global_scope)
    assert "check_planning_references(index)" in source, source[:400]


# ---------------------------------------------------------------------------
# Deterministic exits
# ---------------------------------------------------------------------------


def test_the_three_exit_statuses_are_deterministic(
    checker, synthetic_manuscript, tmp_path
) -> None:
    """0 for clean, 1 for a violation, 2 for unreadable input, in that order.

    The three runs use one file in one workspace, restored between each, so the
    only thing that changes is the fault. A copy is taken first because the module
    fixture is shared and must not be left mutated.
    """

    target = sorted(
        synthetic_manuscript.manuscript_root.rglob("chapters/**/*.md")
    )[0]
    original = target.read_text(encoding="utf-8")
    root = synthetic_manuscript.manuscript_root

    def _chapter_exit() -> Tuple[int, List[str]]:
        run = checker.run_scope(
            (target,), scope=checker.SCOPE_CHAPTER, manuscript_root=root
        )
        return _exit_status(checker, run.diagnostics), _codes(run.diagnostics)

    try:
        status, codes = _chapter_exit()
        assert status == 0, codes

        declared = original.split("movement: ", 1)[1].split("\n", 1)[0]
        replacement = "mindwars_part" if declared != "mindwars_part" else "discovery_part"
        target.write_text(
            original.replace(
                "movement: " + declared, "movement: " + replacement, 1
            ),
            encoding="utf-8",
        )
        status, codes = _chapter_exit()
        assert status == 1, codes
        assert "CHAPTER_MOVEMENT_DISAGREEMENT" in codes, codes

        target.write_text(original.replace("movement:", "movment:", 1), encoding="utf-8")
        status, codes = _chapter_exit()
        assert status == 2, codes
    finally:
        target.write_text(original, encoding="utf-8")

    status, codes = _chapter_exit()
    assert status == 0, codes


def test_incomplete_input_outranks_an_ordinary_violation(checker) -> None:
    """A run holding both a violation and unreadable input reports 2, never 1."""

    violation = checker._diagnostic(
        "SYNTHETIC_VIOLATION",
        scope=checker.SCOPE_GLOBAL,
        item="synthetic",
        observed="a synthetic objective violation",
        expected="no violation",
    )
    incomplete = checker._diagnostic(
        "SYNTHETIC_INCOMPLETE",
        scope=checker.SCOPE_GLOBAL,
        item="synthetic",
        observed="a synthetic unreadable input",
        expected="readable input",
        disposition=checker.DISPOSITION_INCOMPLETE,
    )
    assert _exit_status(checker, (violation,)) == 1
    assert _exit_status(checker, (incomplete,)) == 2
    assert _exit_status(checker, (violation, incomplete)) == 2
    assert _exit_status(checker, (incomplete, violation)) == 2


# ---------------------------------------------------------------------------
# The mandatory suite
# ---------------------------------------------------------------------------


def test_all_fifteen_principal_property_modules_exist() -> None:
    """One module per design property, numbered 01 through 15."""

    modules = sorted(
        path.name
        for path in nf.Path(__file__).parent.glob("test_property_*.py")
    )
    assert len(modules) == EXPECTED_PROPERTY_MODULES, modules
    for number in range(1, EXPECTED_PROPERTY_MODULES + 1):
        prefix = "test_property_{0:02d}_".format(number)
        assert any(name.startswith(prefix) for name in modules), (prefix, modules)


def test_every_property_module_runs_at_least_one_hundred_examples() -> None:
    """Requirement 1.14: each principal property test generates 100 examples.

    Read from the source rather than from a test run, because a module that
    silently dropped to ten examples would still pass its own assertions.
    """

    for path in sorted(nf.Path(__file__).parent.glob("test_property_*.py")):
        text = path.read_text(encoding="utf-8")
        marker = "max_examples={0},".format(EXPECTED_PROPERTY_EXAMPLES)
        assert marker in text, path.name


def test_the_focused_and_integration_suites_exist() -> None:
    """Tasks 8.25 and 8.26 contribute their own modules, not just properties."""

    names = sorted(
        path.name for path in nf.Path(__file__).parent.glob("test_*.py")
    )
    for required in (
        "test_focused_decisions_and_canon.py",
        "test_focused_mechanism_and_motifs.py",
        "test_focused_scope_roster_and_restraint.py",
        "test_integration_scopes_and_process.py",
    ):
        assert required in names, (required, names)


def test_no_diagnostic_code_names_a_craft_judgment(checker) -> None:
    """Requirement 12.15: the checker has no vocabulary for craft.

    The forbidden fragments come from the checker's own `CRAFT_JUDGMENT_TERMS`
    rather than from a list retyped here, so the guard and the test cannot drift
    apart. Only the codes actually passed to a diagnostic constructor are scanned,
    which is what makes a new offending code fail the moment it is written.
    """

    import inspect
    import re

    source = inspect.getsource(checker)
    codes = set(
        re.findall(
            r'(?:_diagnostic|\.violation|\.malformed)\(\s*"([A-Z][A-Z0-9_]+)"',
            source,
        )
    )
    assert len(codes) > 100, len(codes)
    for code in sorted(codes):
        for term in checker.CRAFT_JUDGMENT_TERMS:
            assert term not in code, (code, term)


def test_the_craft_term_guard_would_catch_a_new_offender(checker) -> None:
    """The guard is only worth something if it rejects something.

    Without this the previous test passes on an empty or misspelled term list, and
    the strongest-looking assertion in the file would be proving nothing.
    """

    assert "HOOK_QUALITY" in checker.CRAFT_JUDGMENT_TERMS
    invented = "CHAPTER_HOOK_QUALITY_WEAK"
    assert any(term in invented for term in checker.CRAFT_JUDGMENT_TERMS), invented
    # And a legitimate code that merely mentions the same subject is allowed.
    allowed = "CHAPTER_HOOK_DISAGREEMENT"
    assert not any(term in allowed for term in checker.CRAFT_JUDGMENT_TERMS), allowed


# ---------------------------------------------------------------------------
# Scope separation, which this gate must not blur
# ---------------------------------------------------------------------------


def test_the_whole_book_documents_stay_out_of_chapter_scope(checker) -> None:
    """Requirement 10.9: a Chapter_Local_Gate cannot read the whole-book records.

    The separation is structural rather than conditional: the global source list is
    the default list plus exactly these three documents, so a chapter run has no
    way to reach them.
    """

    extra = frozenset(checker.GLOBAL_RECORD_SOURCES) - frozenset(
        checker.DEFAULT_RECORD_SOURCES
    )
    # Compared as a set: the order the global list happens to be written in is not
    # part of the contract, but its membership is.
    assert extra == frozenset(GLOBAL_ONLY_SOURCES), sorted(extra)
    for source in GLOBAL_ONLY_SOURCES:
        assert source not in checker.DEFAULT_RECORD_SOURCES, source


def test_this_gate_does_not_claim_an_approved_baseline(checker, gate_record) -> None:
    """The record is evidence for approval, not approval itself.

    An approved Baseline needs an author approval, a revision pass, final targets,
    and the calibration Editorial_Review. A Baseline citing only this gate is still
    incomplete, and proving that is what keeps the gate honest about its own reach.
    """

    baseline = nf.baseline(
        baseline_id="BASELINE-GATE-CHECK",
        state="approved",
        full_suite_gate_result_id=GATE_ID,
    )
    index = nf.record_index(
        supporting=False, Baseline=[baseline], GateResult=[gate_record]
    )
    _state, diagnostics = checker.check_baseline(index)
    assert diagnostics != (), "an approved Baseline needs more than this gate"
    assert "BASELINE_AUTHOR_APPROVAL_MISSING" in _codes(diagnostics), _codes(
        diagnostics
    )


# ---------------------------------------------------------------------------
# Task 11: the approved Baseline as committed
# ---------------------------------------------------------------------------

CHECKPOINT_GATE_ID = "GATE-APPROVED-BASELINE-001"
CALIBRATION_CHAPTERS = (1, 2, 3, 4, 5, 73, 118, 124)


@pytest.fixture(scope="module")
def committed_global_index(checker, manuscript_root):
    """All planning records visible to global mode, with no load failures."""

    index, diagnostics = checker.load_reference_index(
        manuscript_root, sources=checker.GLOBAL_RECORD_SOURCES
    )
    assert diagnostics == (), _codes(diagnostics)
    return index


def test_committed_global_mode_reads_the_author_approved_final_targets(
    checker, committed_global_index
) -> None:
    """Validates: Requirements 1.14, 1.15, 2.2, 11.5, and 12.7."""

    baseline, diagnostics = checker.check_baseline(committed_global_index)
    assert diagnostics == (), _codes(diagnostics)
    assert baseline.approved is True
    assert baseline.record is not None
    assert baseline.record.payload["author_approval"] == {
        "approved_by": "Jessica Mulein",
        "approved_at": "2026-09-16T22:00:00Z",
        "approval_record": "planning/arc-outline.md#author-approval--task-102",
    }
    assert baseline.final_targets == checker.FinalTargets(
        chapter_count=128,
        minimum_words=130000,
        maximum_words=150000,
    )


def test_committed_baseline_contains_exactly_one_complete_revision_pass(
    checker, committed_global_index
) -> None:
    """Validates: Requirements 1.12, 1.13, 1.14, and 1.18."""

    current = [
        record
        for record in committed_global_index.of_type("Baseline")
        if record.payload.get("state") != "superseded"
    ]
    assert len(current) == 1
    payload = current[0].payload
    revision_pass = payload["baseline_revision_pass"]
    dispositions = revision_pass["dispositions"]
    assert revision_pass["performed_at"] < payload["author_approval"]["approved_at"]
    assert len(dispositions) == len(payload["calibration_finding_ids"]) == 18
    assert {item["editorial_finding_id"] for item in dispositions} == set(
        payload["calibration_finding_ids"]
    )
    assert {item["outcome"] for item in dispositions} == {"no-change-rationale"}
    assert {item["arc_change_id"] for item in dispositions} == {None}
    assert checker.check_arc_changes(committed_global_index) == ()


def test_all_eight_committed_calibration_chapters_track_current_status(
    checker, committed_global_index, manuscript_root
) -> None:
    """Validates fixed calibration identity and current status synchronization."""

    current_baselines = [
        record
        for record in committed_global_index.of_type("Baseline")
        if record.payload.get("state") != "superseded"
    ]
    assert len(current_baselines) == 1
    baseline_chapters = tuple(
        current_baselines[0].payload["calibration_chapters"]
    )
    assert baseline_chapters == CALIBRATION_CHAPTERS

    entries = {
        int(record.payload["chapter"]): record.payload
        for record in committed_global_index.of_type("ArcEntry")
    }
    selected = tuple(
        sorted(
            chapter
            for chapter, entry in entries.items()
            if entry["calibration_selected"] is True
        )
    )
    assert selected == baseline_chapters
    for chapter in baseline_chapters:
        entry = entries[chapter]
        assert entry["status"] != "planned"
        path = manuscript_root.joinpath(*entry["filename"].split("/"))
        document = checker.parse_chapter_document(
            path.read_text(encoding="utf-8"),
            relative_path=entry["filename"],
        )
        assert document.header["status"] == entry["status"]


def test_task_11_checkpoint_gate_is_readable_and_passing(
    checker, committed_global_index
) -> None:
    """The post-approval rerun is a new gate record, never rewritten history."""

    matching = [
        record
        for record in committed_global_index.of_type("GateResult")
        if record.payload.get("gate_result_id") == CHECKPOINT_GATE_ID
    ]
    assert len(matching) == 1
    gate = matching[0].payload
    assert gate["gate_type"] == "baseline-objective"
    assert gate["prerequisite_state"] == "complete"
    assert gate["objective_diagnostic_ids"] == []
    assert gate["editorial_finding_ids"] == []
    assert gate["result"] == "pass"
    assert gate["checker_exit_status"] == 0
    assert gate["scope"]["chapter_numbers"] == []
    assert "702 tests" in gate["scope"]["description"]
    assert gate["timestamp"] > "2026-09-16T22:00:00Z"
    assert checker.check_gate_results(committed_global_index) == ()
