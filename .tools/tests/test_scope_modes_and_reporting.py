"""Focused tests for tasks 7.5 and 7.6 of the novel specification.

Validates: Requirements 10.1–10.5, 10.9, 12.9–12.15, and 13.3.

Covers the two requested scopes, the delivered-batch size rules, the changed
cross-document reference audit, one total order over diagnostics, the text and
JSON report surfaces, and the `0`/`1`/`2` exit contract. Global mode, whole-book
totals, and every craft judgment stay out of scope by design.
"""

from __future__ import annotations

import ast
import json
import pathlib

import pytest

import novel_fixtures as nf

CALIBRATION = nf.CALIBRATION_CHAPTERS


def _codes(diagnostics):
    return [diagnostic.code for diagnostic in diagnostics]


def _batch(checker, workspace, **options):
    return checker.run_scope(
        [workspace.chapter_path(fixture) for fixture in workspace.chapters],
        scope="batch",
        manuscript_root=workspace.manuscript_root,
        **options
    )


def _chapter(checker, workspace, index=0):
    return checker.run_scope(
        [workspace.chapter_path(workspace.chapters[index])],
        scope="chapter",
        manuscript_root=workspace.manuscript_root,
    )


# ---------------------------------------------------------------------------
# Batch composition
# ---------------------------------------------------------------------------


def test_complete_calibration_batch_passes_with_exit_zero(checker, tmp_path):
    workspace = nf.calibration_workspace(tmp_path / "workspace")

    run = _batch(checker, workspace)

    assert run.diagnostics == ()
    assert run.batch_kind == "calibration"
    assert run.chapter_numbers == CALIBRATION
    assert run.result == checker.RESULT_PASS
    assert run.exit_status == 0


def test_calibration_batch_is_accepted_while_nonconsecutive(checker, tmp_path):
    """Chapters 1–5, 73, 118, and 124 are three separate movement blocks."""

    workspace = nf.calibration_workspace(tmp_path / "workspace")

    run = _batch(checker, workspace)

    movements = {fixture.movement for fixture in workspace.chapters}
    assert movements == {"discovery_part", "mindwars_part", "aftermath_coda"}
    assert "BATCH_SIZE_OUT_OF_RANGE" not in _codes(run.diagnostics)
    assert "BATCH_CALIBRATION_CHAPTER_UNEXPECTED" not in _codes(run.diagnostics)


@pytest.mark.parametrize(
    "kind,size,expected",
    [
        ("calibration", 5, "BATCH_SIZE_OUT_OF_RANGE"),
        ("calibration", 6, None),
        ("calibration", 8, None),
        ("drafting", 3, "BATCH_SIZE_OUT_OF_RANGE"),
        ("drafting", 4, None),
        ("drafting", 8, None),
        ("drafting", 9, "BATCH_SIZE_OUT_OF_RANGE"),
    ],
)
def test_each_batch_kind_enforces_its_own_size_range(checker, kind, size, expected):
    """Requirement 13.1 sizes calibration at 6–8; 13.2 sizes drafting at 4–8."""

    # A calibration case must draw from the fixed eight so only size is at issue.
    chapters = (
        list(CALIBRATION[:size])
        if kind == "calibration"
        else list(range(30, 30 + size))
    )

    diagnostics = checker.check_batch_composition(chapters, batch_kind=kind)

    assert _codes(diagnostics) == ([] if expected is None else [expected])


def test_declared_calibration_batch_rejects_a_chapter_outside_the_fixed_eight(
    checker,
):
    diagnostics = checker.check_batch_composition(
        [1, 2, 3, 4, 5, 42, 118, 124], batch_kind="calibration"
    )

    assert _codes(diagnostics) == ["BATCH_CALIBRATION_CHAPTER_UNEXPECTED"]
    assert "42" in diagnostics[0].observed


def test_batch_kind_inference_needs_the_calibration_minimum(checker):
    assert checker.classify_batch_kind(CALIBRATION) == "calibration"
    assert checker.classify_batch_kind([1, 2, 3, 4, 5, 73]) == "calibration"
    # Too small to be the Calibration_Batch, so it reads as an ordinary
    # Drafting_Batch whose own 4–8 range it satisfies.
    assert checker.classify_batch_kind([1, 2, 3, 4]) == "drafting"
    assert checker.classify_batch_kind([30, 31, 32, 33]) == "drafting"
    assert checker.check_batch_composition([1, 2, 3, 4], batch_kind="drafting") == ()


def test_an_explicit_batch_kind_overrides_the_inference(checker, tmp_path):
    workspace = nf.calibration_workspace(
        tmp_path / "workspace", chapters=(1, 2, 3, 4, 5)
    )

    inferred = _batch(checker, workspace)
    declared = _batch(checker, workspace, batch_kind="calibration")

    assert inferred.batch_kind == "drafting"
    assert inferred.diagnostics == ()
    assert declared.batch_kind == "calibration"
    assert _codes(declared.diagnostics) == ["BATCH_SIZE_OUT_OF_RANGE"]
    assert declared.exit_status == 1


def test_batch_composition_rejects_an_unknown_batch_kind(checker):
    with pytest.raises(ValueError):
        checker.check_batch_composition([1, 2, 3, 4], batch_kind="baseline")


# ---------------------------------------------------------------------------
# Changed cross-document references
# ---------------------------------------------------------------------------


def test_a_changed_reference_the_batch_reaches_is_audited_without_complaint(
    checker, tmp_path
):
    workspace = nf.calibration_workspace(tmp_path / "workspace")

    run = _batch(
        checker,
        workspace,
        changed_references=("planning/motif-ledger.md", "planning/arc-outline.md"),
    )

    assert run.diagnostics == ()
    assert run.exit_status == 0
    assert run.changed_references == (
        "planning/motif-ledger.md",
        "planning/arc-outline.md",
    )


def test_a_changed_reference_no_scope_chapter_reaches_is_stale(checker, tmp_path):
    """Chapters 1–5 carry no Motif_Event, so a changed ledger is out of scope."""

    workspace = nf.calibration_workspace(
        tmp_path / "workspace", chapters=(1, 2, 3, 4, 5)
    )

    run = _batch(
        checker, workspace, changed_references=("planning/motif-ledger.md",)
    )

    assert _codes(run.diagnostics) == ["CHANGED_REFERENCE_STALE"]
    diagnostic = run.diagnostics[0]
    assert diagnostic.item == "planning/motif-ledger.md"
    assert diagnostic.scope == checker.SCOPE_BATCH
    assert diagnostic.disposition == checker.DISPOSITION_VIOLATION
    assert run.result == checker.RESULT_REVISION
    assert run.exit_status == 1


def test_widening_the_batch_scope_makes_the_same_reference_current(
    checker, tmp_path
):
    """The stale finding is about scope, not about the document itself."""

    narrow = nf.calibration_workspace(
        tmp_path / "narrow", chapters=(1, 2, 3, 4, 5)
    )
    wide = nf.calibration_workspace(tmp_path / "wide")
    changed = ("planning/motif-ledger.md",)

    assert _codes(
        _batch(checker, narrow, changed_references=changed).diagnostics
    ) == ["CHANGED_REFERENCE_STALE"]
    assert _batch(checker, wide, changed_references=changed).diagnostics == ()


def test_a_changed_reference_outside_the_allowlist_is_incomplete_input(
    checker, tmp_path
):
    workspace = nf.calibration_workspace(tmp_path / "workspace")

    run = _batch(
        checker, workspace, changed_references=("planning/record-schemas.md",)
    )

    assert _codes(run.diagnostics) == ["CHANGED_REFERENCE_UNKNOWN"]
    assert run.diagnostics[0].disposition == checker.DISPOSITION_INCOMPLETE
    assert run.result == checker.RESULT_INCOMPLETE
    assert run.exit_status == 2


def test_a_declared_but_missing_record_source_fails_closed(checker, tmp_path):
    workspace = nf.calibration_workspace(tmp_path / "workspace")
    workspace.manuscript_root.joinpath("planning", "voice-briefs.md").unlink()

    run = _batch(
        checker, workspace, changed_references=("planning/voice-briefs.md",)
    )

    codes = _codes(run.diagnostics)
    assert "PLANNING_DOCUMENT_MISSING" in codes
    assert "CHANGED_REFERENCE_UNREADABLE" in codes
    assert run.result == checker.RESULT_INCOMPLETE
    assert run.exit_status == 2


def test_the_same_changed_reference_declared_twice_is_incomplete(checker, tmp_path):
    workspace = nf.calibration_workspace(tmp_path / "workspace")

    run = _batch(
        checker,
        workspace,
        changed_references=("planning/motif-ledger.md", "planning/motif-ledger.md"),
    )

    assert _codes(run.diagnostics) == ["CHANGED_REFERENCE_DUPLICATE"]
    assert run.exit_status == 2


def test_chapter_scope_takes_no_changed_reference(checker, tmp_path):
    """Requirement 10.1: only the Chapter_File and its direct references."""

    workspace = nf.calibration_workspace(tmp_path / "workspace")

    with pytest.raises(ValueError):
        checker.run_scope(
            [workspace.chapter_path(workspace.chapters[0])],
            scope="chapter",
            manuscript_root=workspace.manuscript_root,
            changed_references=("planning/motif-ledger.md",),
        )


def test_participating_sources_follow_the_direct_reference_chain(
    checker, tmp_path
):
    workspace = nf.calibration_workspace(tmp_path / "workspace", chapters=(73,))
    index, _ = checker.load_reference_index(workspace.manuscript_root)

    reached = checker.scope_participating_records(index, chapter_scope=[73])

    # Chapter 73's ArcEntry, its Timeline entry, its POV profile, that profile's
    # Voice_Brief, its Motif_Event, and the constraint the event protects.
    assert set(reached) == {
        "planning/arc-outline.md",
        "planning/canon-bible.md",
        "planning/pov-roster.md",
        "planning/voice-briefs.md",
        "planning/motif-ledger.md",
    }
    assert "MOT-YES-01" in reached["planning/motif-ledger.md"]
    assert nf.DID_I_SAY_YES_CONSTRAINT_ID in reached["planning/motif-ledger.md"]
    assert "TL-CALIBRATION-073" in reached["planning/canon-bible.md"]


def test_an_out_of_scope_chapter_reaches_nothing(checker, tmp_path):
    workspace = nf.calibration_workspace(tmp_path / "workspace", chapters=(1,))
    index, _ = checker.load_reference_index(workspace.manuscript_root)

    assert checker.scope_participating_records(index, chapter_scope=[]) == {}


# ---------------------------------------------------------------------------
# Deterministic diagnostics and exit behavior
# ---------------------------------------------------------------------------


def test_repeated_runs_render_byte_identical_reports(checker, tmp_path):
    workspace = nf.calibration_workspace(
        tmp_path / "workspace",
        chapter_overrides={118: {"words": 4}, 124: {"pov_id": "POV-ABSENT"}},
    )

    first = _batch(checker, workspace)
    second = _batch(checker, workspace)

    assert first.diagnostics != ()
    for report_format in checker.REPORT_FORMATS:
        assert checker.render_report(
            first, report_format=report_format
        ) == checker.render_report(second, report_format=report_format)


def test_diagnostic_order_is_independent_of_arrival_order(checker, tmp_path):
    workspace = nf.calibration_workspace(
        tmp_path / "workspace", chapter_overrides={5: {"words": 7}}
    )

    run = _batch(checker, workspace)
    forward = checker.sort_diagnostics(run.diagnostics)
    reversed_input = checker.sort_diagnostics(tuple(reversed(run.diagnostics)))

    assert forward == reversed_input
    # Chapter findings read before the batch and planning findings above them.
    ranks = [checker._SCOPE_REPORT_ORDER[item.scope] for item in forward]
    assert ranks == sorted(ranks)


def test_text_report_carries_every_design_field_and_the_trailing_counts(
    checker, tmp_path
):
    # Declared `words` drifts while the declared Length_Class still matches the
    # real prose, which isolates exactly one diagnostic.
    workspace = nf.calibration_workspace(
        tmp_path / "workspace",
        chapter_overrides={124: {"words": 11, "length_class": "normal"}},
    )

    run = _batch(checker, workspace)
    lines = checker.render_text_report(run).splitlines()

    violation = next(line for line in lines if line.startswith("ERROR "))
    assert "CHAPTER_WORD_COUNT" in violation
    assert "observed=" in violation and "expected=" in violation
    assert "declared=11" in violation
    assert lines[-3].startswith("SUMMARY scope=batch batch_kind=calibration")
    assert "result=revision" in lines[-3] and "exit=1" in lines[-3]
    assert lines[-2] == "SEVERITY error=1 warning=0"
    assert lines[-1] == "SCOPE chapter=1 batch=0 planning=0 global=0"


def test_json_report_carries_the_same_structured_facts(checker, tmp_path):
    workspace = nf.calibration_workspace(
        tmp_path / "workspace",
        chapter_overrides={124: {"words": 11, "length_class": "normal"}},
    )

    run = _batch(
        checker, workspace, changed_references=("planning/motif-ledger.md",)
    )
    document = json.loads(checker.render_report(run, report_format="json"))

    assert document["scope"] == "batch"
    assert document["batch_kind"] == "calibration"
    assert document["chapter_numbers"] == list(CALIBRATION)
    assert document["changed_references"] == ["planning/motif-ledger.md"]
    assert document["result"] == "revision"
    assert document["exit_status"] == 1
    assert document["counts"] == {
        "total": 1,
        "severity": {"error": 1},
        "scope": {"chapter": 1},
    }
    entry = document["diagnostics"][0]
    assert set(entry) == {
        "severity",
        "code",
        "scope",
        "item",
        "observed",
        "expected",
        "disposition",
        "details",
        "related",
    }
    assert entry["code"] == "CHAPTER_WORD_COUNT"
    assert entry["details"]["declared"] == "11"


def test_a_passing_chapter_scope_reports_no_batch_only_field(checker, tmp_path):
    workspace = nf.calibration_workspace(tmp_path / "workspace")

    run = _chapter(checker, workspace)
    document = json.loads(checker.render_report(run, report_format="json"))

    assert run.exit_status == 0
    assert "batch_kind" not in document
    assert "changed_references" not in document
    assert "PASS chapter-scope" in checker.render_text_report(run)


def test_an_unknown_report_format_is_refused(checker, tmp_path):
    workspace = nf.calibration_workspace(tmp_path / "workspace")

    with pytest.raises(ValueError):
        checker.render_report(_chapter(checker, workspace), report_format="yaml")


@pytest.mark.parametrize(
    "overrides,expected_status,expected_result",
    [
        ({}, 0, "pass"),
        ({124: {"words": 11}}, 1, "revision"),
        ({124: {"drop_keys": ("pov_id",)}}, 2, "incomplete"),
    ],
)
def test_exit_status_follows_the_worst_finding(
    checker, tmp_path, overrides, expected_status, expected_result
):
    """`2` outranks `1` outranks `0`, per Requirements 12.9, 12.14, and 12.15."""

    workspace = nf.calibration_workspace(
        tmp_path / "workspace", chapter_overrides=overrides
    )

    run = _batch(checker, workspace)

    assert run.result == expected_result
    assert run.exit_status == expected_status


def test_an_incomplete_input_outranks_an_ordinary_violation(checker, tmp_path):
    workspace = nf.calibration_workspace(
        tmp_path / "workspace",
        chapter_overrides={5: {"words": 3}, 118: {"drop_keys": ("hook",)}},
    )

    run = _batch(checker, workspace)
    dispositions = {item.disposition for item in run.diagnostics}

    assert dispositions == {
        checker.DISPOSITION_VIOLATION,
        checker.DISPOSITION_INCOMPLETE,
    }
    assert run.exit_status == 2


def test_an_unknown_scope_is_refused(checker, tmp_path):
    workspace = nf.calibration_workspace(tmp_path / "workspace")

    with pytest.raises(ValueError):
        checker.run_scope(
            [workspace.chapter_path(workspace.chapters[0])],
            scope="movement",
            manuscript_root=workspace.manuscript_root,
        )


# ---------------------------------------------------------------------------
# The command line
# ---------------------------------------------------------------------------


def _cli(checker, workspace, *arguments):
    return checker.main(
        ["--manuscript-root", str(workspace.manuscript_root)] + list(arguments)
    )


def _cli_batch_arguments(workspace):
    return ["--scope", "batch", "--chapters"] + [
        fixture.relative_path for fixture in workspace.chapters
    ]


def test_cli_runs_the_calibration_batch_and_exits_zero(checker, tmp_path, capsys):
    """Integration: the whole delivered Calibration_Batch through the CLI."""

    workspace = nf.calibration_workspace(tmp_path / "workspace")

    status = _cli(checker, workspace, *_cli_batch_arguments(workspace))
    captured = capsys.readouterr()

    assert status == 0
    assert "result=pass" in captured.out
    assert "PASS batch-scope" in captured.out
    assert captured.err == ""


def test_cli_runs_one_chapter_and_exits_zero(checker, tmp_path, capsys):
    workspace = nf.calibration_workspace(tmp_path / "workspace")

    status = _cli(
        checker,
        workspace,
        "--scope",
        "chapter",
        "--chapter",
        workspace.chapters[0].relative_path,
    )

    assert status == 0
    assert "SUMMARY scope=chapter chapters=1" in capsys.readouterr().out


def test_cli_reports_a_violation_on_stderr_and_exits_one(checker, tmp_path, capsys):
    workspace = nf.calibration_workspace(
        tmp_path / "workspace",
        chapter_overrides={73: {"words": 9, "length_class": "normal"}},
    )

    status = _cli(checker, workspace, *_cli_batch_arguments(workspace))
    captured = capsys.readouterr()

    assert status == 1
    assert "ERROR CHAPTER_WORD_COUNT" in captured.err
    assert "exit=1" in captured.err
    assert captured.out == ""


def test_cli_exits_two_for_a_chapter_file_that_is_not_there(
    checker, tmp_path, capsys
):
    workspace = nf.calibration_workspace(tmp_path / "workspace")

    status = _cli(
        checker,
        workspace,
        "--scope",
        "chapter",
        "--chapter",
        "chapters/discovery-part/discovery-part-001-absent.md",
    )
    captured = capsys.readouterr()

    assert status == 2
    assert "CHAPTER_FILE_MISSING" in captured.err
    assert "discovery-part-001-absent.md" in captured.err


def test_cli_emits_json_when_asked(checker, tmp_path, capsys):
    workspace = nf.calibration_workspace(tmp_path / "workspace")

    status = _cli(
        checker, workspace, *(_cli_batch_arguments(workspace) + ["--format", "json"])
    )
    document = json.loads(capsys.readouterr().out)

    assert status == 0
    assert document["scope"] == "batch"
    assert document["batch_kind"] == "calibration"
    assert document["diagnostics"] == []


def test_cli_passes_changed_references_through_to_the_batch_audit(
    checker, tmp_path, capsys
):
    workspace = nf.calibration_workspace(
        tmp_path / "workspace", chapters=(1, 2, 3, 4, 5)
    )

    status = _cli(
        checker,
        workspace,
        *(
            _cli_batch_arguments(workspace)
            + ["--changed-reference", "planning/motif-ledger.md"]
        )
    )

    assert status == 1
    assert "CHANGED_REFERENCE_STALE" in capsys.readouterr().err


@pytest.mark.parametrize(
    "arguments",
    [
        ["--scope", "chapter"],
        ["--scope", "batch"],
        ["--scope", "chapter", "--chapters", "a.md", "b.md"],
        ["--scope", "batch", "--chapter", "a.md"],
        ["--scope", "chapter", "--chapter", "a.md", "--batch-kind", "calibration"],
        [
            "--scope",
            "chapter",
            "--chapter",
            "a.md",
            "--changed-reference",
            "planning/motif-ledger.md",
        ],
        ["--site-exclusion", "--scope", "chapter", "--chapter", "a.md"],
    ],
)
def test_cli_refuses_a_contradictory_request_with_exit_two(
    checker, tmp_path, arguments
):
    """Fail closed on misuse rather than silently checking something narrower."""

    workspace = nf.calibration_workspace(tmp_path / "workspace")

    with pytest.raises(SystemExit) as raised:
        _cli(checker, workspace, *arguments)

    assert raised.value.code == 2


def test_cli_accepts_a_workspace_relative_chapter_path(checker, tmp_path, capsys):
    workspace = nf.calibration_workspace(tmp_path / "workspace")
    fixture = workspace.chapters[0]

    status = checker.main(
        [
            "--workspace-root",
            str(workspace.root),
            "--scope",
            "chapter",
            "--chapter",
            str(workspace.chapter_path(fixture)),
        ]
    )

    assert status == 0
    assert "result=pass" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# The diagnostic vocabulary excludes craft judgment
# ---------------------------------------------------------------------------


def _source_diagnostic_codes(checker):
    """Every diagnostic code the checker can emit.

    Two sources, because a code reaches `_diagnostic` two ways: as a literal at
    the call site, and through a mapping the call site looks it up in. The AST
    walk finds the first; the module's own resolved constants supply the second.
    """

    tree = ast.parse(pathlib.Path(nf.CHECKER_PATH).read_text(encoding="utf-8"))
    codes = set(checker.REFERENCE_DANGLING_CODES.values())
    codes.add(checker.RESOLVED_DID_I_SAY_YES_CONSTRAINT["diagnostic_code"])
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
        if name not in ("_diagnostic", "malformed", "violation", "CheckerDiagnostic"):
            continue
        keywords = {keyword.arg: keyword.value for keyword in node.keywords}
        target = node.args[0] if node.args else keywords.get("code")
        if isinstance(target, ast.Constant) and isinstance(target.value, str):
            codes.add(target.value)
        elif isinstance(target, ast.Constant):
            raise AssertionError(
                "non-string diagnostic code at line {0}".format(node.lineno)
            )
    return codes


def test_no_diagnostic_code_in_the_checker_names_a_craft_judgment(checker):
    """Requirements 12.11 and 12.12 keep craft judgment out of the vocabulary."""

    codes = _source_diagnostic_codes(checker)

    assert len(codes) > 60, "the code scan found suspiciously few codes"
    offenders = {
        code: checker.craft_judgment_term(code)
        for code in codes
        if checker.craft_judgment_term(code) is not None
    }
    assert offenders == {}


def test_objective_codes_that_merely_mention_a_subject_stay_allowed(checker):
    """Requirement 12.5 requires Hook metadata and Voice_Brief ID agreement."""

    for code in (
        "CHAPTER_HOOK_DISAGREEMENT",
        "VOICE_BRIEF_POV_DISAGREEMENT",
        "VOICE_BRIEF_REFERENCE_DANGLING",
    ):
        assert checker.craft_judgment_term(code) is None
        assert code in _source_diagnostic_codes(checker)


@pytest.mark.parametrize(
    "code,term",
    [
        ("CHAPTER_HOOK_QUALITY", "HOOK_QUALITY"),
        ("PROSE_VOICE_DRIFT", "PROSE_VOICE"),
        ("CHAPTER_PACING_UNEVEN", "PACING"),
        ("EMOTIONAL_TRUTH_MISSING", "EMOTIONAL"),
        ("VOICE_SCORE", "SCORE"),
        ("TENDERNESS_ABSENT", "TENDERNESS"),
        ("RESTRAINT_LOST", "RESTRAINT"),
        ("ORIGINALITY_LOW", "ORIGINALITY"),
        ("RHETORICAL_FORCE_WEAK", "RHETORICAL"),
    ],
)
def test_a_craft_judgment_code_cannot_be_constructed(checker, code, term):
    assert checker.craft_judgment_term(code) == term
    with pytest.raises(ValueError) as raised:
        checker.CheckerDiagnostic(
            code=code,
            scope=checker.SCOPE_CHAPTER,
            item="discovery-part-001-x.md",
            observed="anything",
            expected="anything",
        )
    assert term in str(raised.value)


def test_a_ledgered_craft_judgment_code_is_a_violation_not_a_crash(
    checker, tmp_path
):
    """An author document can never smuggle a craft judgment into the vocabulary."""

    workspace = nf.calibration_workspace(
        tmp_path / "workspace",
        chapters=(73,),
        extra_planning={
            "planning/motif-ledger.md": (
                (
                    "LiteralPhraseConstraint",
                    nf.did_i_say_yes_constraint(
                        constraint_id="LPC-CRAFT-JUDGMENT",
                        diagnostic_code="LITERAL_PROSE_VOICE_QUALITY",
                    ),
                ),
            )
        },
    )

    run = _batch(checker, workspace)

    assert "LITERAL_CONSTRAINT_CRAFT_JUDGMENT_CODE" in _codes(run.diagnostics)
    assert run.exit_status == 1
