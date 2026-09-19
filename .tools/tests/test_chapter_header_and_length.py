"""Focused tests for task 7.2 of the `The-Final-Frontier-novel` spec.

Covered surface: the restricted Chapter_Header parser, the Prose_Word count, the
Length_Class bands and the Hard_Chapter_Maximum, the outlier planned-purpose
rule, and the four-way filename/directory/header/ArcEntry movement and
global-sequence agreement rule. Also covered is the exit-status model those
checks feed, because a diagnostic that reports the wrong status is worse than no
diagnostic at all.

Validates: Requirements 2.8-2.11, 9.5-9.7, 12.1-12.3, 12.10.

Not covered here, deliberately: Timeline_ID/POV_ID/Motif_Event resolution and
Hook/status outline agreement (task 7.3), motif and literal-phrase scanning
(task 7.4), the `--scope chapter`/`--scope batch` CLI (task 7.5), the text and
JSON diagnostic surface (task 7.6), and every whole-manuscript total such as the
80 percent normal share. Asserting those now would mean asserting against code
that does not exist.

Every fixture is synthetic and lives in pytest `tmp_path`. Nothing here writes
into the real manuscript tree, and no test contains novel prose.
"""

from __future__ import annotations

import pytest

import novel_fixtures as nf

DEFAULT_RELATIVE_PATH = (
    "chapters/discovery-part/discovery-part-001-synthetic-fixture.md"
)


# ---------------------------------------------------------------------------
# Helpers
#
# These compose the shared builders; they never restate a checker rule. Expected
# counts and classes are written literally in each test so nothing is compared
# against a second implementation of the specification.
# ---------------------------------------------------------------------------


def _chapter(
    words,
    *,
    declared_words=None,
    declared_class=None,
    **fixture_options,
):
    """A `ChapterFixture` whose Prose_Body holds exactly `words` tokens.

    Pass `prose=` to supply the body text directly; `words` then states how many
    tokens that body is expected to contain, which is also what the header
    declares. A test that needs a declared/observed disagreement passes
    `declared_words`.
    """

    if declared_class is None:
        declared_class = (
            nf.derive_length_class(words)
            if words <= nf.HARD_CHAPTER_MAXIMUM
            else "long-outlier"
        )
    prose = fixture_options.pop("prose", None)
    if prose is None:
        prose = nf.prose_of_length(words)
    return nf.chapter_fixture(
        prose=prose,
        words=words if declared_words is None else declared_words,
        length_class=declared_class,
        **fixture_options
    )


def _entry_for(fixture, **overrides):
    """A conforming `ArcEntry` for one fixture, before any injected violation."""

    observed = nf.count_prose_words(fixture.prose)
    fields = {
        "chapter": fixture.chapter,
        "movement": fixture.movement,
        "slug": fixture.slug,
    }
    if observed <= nf.HARD_CHAPTER_MAXIMUM:
        length_class = nf.derive_length_class(observed)
        fields["estimated_words"] = observed
        fields["estimated_length_class"] = length_class
        if length_class != "normal":
            fields["outlier_purpose"] = "A synthetic planned outlier purpose."
    fields.update(overrides)
    return nf.arc_entry(**fields)


def _outline(entries):
    return nf.planning_document(
        "planning/arc-outline.md",
        title="Arc Outline",
        blocks=tuple(("ArcEntry", entry) for entry in entries),
    )


def _scope(checker, tmp_path, fixtures, entries, *, name="workspace"):
    """Build a workspace and run the chapter/batch scope over its chapters."""

    workspace = nf.build_workspace(
        tmp_path / name, planning=(_outline(entries),), chapters=tuple(fixtures)
    )
    return workspace, checker.check_chapter_scope(
        [workspace.chapter_path(fixture) for fixture in fixtures],
        manuscript_root=workspace.manuscript_root,
    )


def _one(checker, tmp_path, fixture, entry=None, *, name="workspace"):
    entry = _entry_for(fixture) if entry is None else entry
    _workspace, result = _scope(checker, tmp_path, (fixture,), (entry,), name=name)
    return result


def _codes(result):
    return sorted(diagnostic.code for diagnostic in result.diagnostics)


def _parse(checker, fixture=None, text=None, relative_path=DEFAULT_RELATIVE_PATH):
    if text is None:
        text = fixture.text()
        relative_path = fixture.relative_path
    return checker.parse_chapter_document(text, relative_path=relative_path)


def _text_diagnostics(checker, document):
    """Header diagnostics plus the length diagnostics, with no outline."""

    report = checker.chapter_length_report(document)
    return tuple(document.diagnostics) + checker.check_chapter_length(report)


# ---------------------------------------------------------------------------
# The diagnostic model and the exit-status model
# ---------------------------------------------------------------------------


def test_diagnostic_renders_the_line_shape_the_design_specifies(checker):
    diagnostic = checker.CheckerDiagnostic(
        code="CHAPTER_WORD_COUNT",
        scope=checker.SCOPE_CHAPTER,
        item="aftermath-coda-124-the-relay.md",
        observed="1018",
        expected="equal",
        details=(("declared", "1008"),),
    )

    assert diagnostic.format_text() == (
        "ERROR CHAPTER_WORD_COUNT aftermath-coda-124-the-relay.md "
        "observed=1018 declared=1008 expected=equal"
    )


def test_diagnostic_code_must_be_a_stable_uppercase_identifier(checker):
    with pytest.raises(ValueError):
        checker.CheckerDiagnostic(
            code="chapter word count",
            scope=checker.SCOPE_CHAPTER,
            item="x.md",
            observed="a",
            expected="b",
        )


def test_incomplete_input_outranks_an_objective_violation(checker):
    """Exit 2 takes precedence over exit 1 (Requirements 12.9, 12.14, 12.15)."""

    violation = checker.CheckerDiagnostic(
        code="CHAPTER_WORD_COUNT",
        scope=checker.SCOPE_CHAPTER,
        item="x.md",
        observed="1",
        expected="2",
        disposition=checker.DISPOSITION_VIOLATION,
    )
    incomplete = checker.CheckerDiagnostic(
        code="CHAPTER_HEADER_KEY_MISSING",
        scope=checker.SCOPE_CHAPTER,
        item="x.md",
        observed="absent",
        expected="present",
        disposition=checker.DISPOSITION_INCOMPLETE,
    )
    warning = checker.CheckerDiagnostic(
        code="PROVISIONAL_DATA",
        scope=checker.SCOPE_CHAPTER,
        item="x.md",
        observed="provisional",
        expected="provisional",
        severity=checker.SEVERITY_WARNING,
        disposition=checker.DISPOSITION_INCOMPLETE,
    )

    assert checker.classify_result(()) == checker.RESULT_PASS
    assert checker.classify_result((violation,)) == checker.RESULT_REVISION
    assert checker.classify_result((incomplete,)) == checker.RESULT_INCOMPLETE
    # Order must not matter, and a warning must never mask or create a failure.
    assert checker.classify_result((violation, incomplete)) == checker.RESULT_INCOMPLETE
    assert checker.classify_result((incomplete, violation)) == checker.RESULT_INCOMPLETE
    assert checker.classify_result((warning,)) == checker.RESULT_PASS

    assert checker.exit_status_for_result(checker.RESULT_PASS) == 0
    assert checker.exit_status_for_result(checker.RESULT_REVISION) == 1
    assert checker.exit_status_for_result(checker.RESULT_INCOMPLETE) == 2


# ---------------------------------------------------------------------------
# Failing safely on an unresolvable Prose_Body boundary
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "label, render_options, expected_code",
    [
        (
            "missing opening delimiter",
            {"open_delimiter": "==="},
            "CHAPTER_HEADER_OPEN_DELIMITER_MISSING",
        ),
        (
            "missing closing delimiter",
            {"close_delimiter": "==="},
            "CHAPTER_HEADER_CLOSE_DELIMITER_MISSING",
        ),
    ],
)
def test_a_missing_delimiter_stops_counting_with_incomplete_input(
    checker, tmp_path, label, render_options, expected_code
):
    fixture = _chapter(900, render_options=render_options)

    result = _one(checker, tmp_path, fixture)

    assert _codes(result) == [expected_code], label
    assert result.result == checker.RESULT_INCOMPLETE
    assert result.exit_status == 2
    # Fail safely: no boundary, so no count, no class, and no semantic check.
    chapter = result.chapters[0]
    assert chapter.document.boundary_resolved is False
    assert chapter.document.prose_body is None
    assert chapter.length_report is None
    assert chapter.arc_entry is None


def test_a_second_header_block_is_an_ambiguous_boundary(checker, tmp_path):
    fixture = _chapter(900)
    doubled = nf.render_chapter_header(fixture.header) + fixture.text()

    document = _parse(checker, text=doubled)
    diagnostics = _text_diagnostics(checker, document)

    assert [diagnostic.code for diagnostic in diagnostics] == [
        "CHAPTER_HEADER_SECOND_BLOCK"
    ]
    assert document.boundary_resolved is False
    assert checker.classify_result(diagnostics) == checker.RESULT_INCOMPLETE


def test_a_scene_break_in_the_prose_body_is_not_a_second_header(checker):
    """A bare `---` only reads as a header when a restricted key follows it.

    The scene-break line is itself a whitespace-separated token, so it counts
    like any other punctuation-only token.
    """

    fixture = _chapter(7, prose="one two three\n\n---\n\nfour five six\n")
    document = _parse(checker, fixture)

    assert document.boundary_resolved is True
    assert document.diagnostics == ()
    assert checker.count_prose_words(document.prose_body) == 7
    assert checker.check_chapter_length(checker.chapter_length_report(document)) == ()


# ---------------------------------------------------------------------------
# The restricted ten-key header block
# ---------------------------------------------------------------------------


def test_a_conforming_header_parses_into_the_ten_logical_keys(checker):
    fixture = _chapter(900)
    document = _parse(checker, fixture)

    assert document.diagnostics == ()
    assert document.header_complete is True
    assert sorted(document.header) == sorted(checker.CHAPTER_HEADER_KEYS)
    assert document.header["movement"] == "discovery_part"
    assert document.header["chapter"] == 1
    assert document.header["title"] == "A Synthetic Chapter"
    assert document.header["words"] == 900
    assert document.header["length_class"] == "normal"
    assert document.header["motif_events"] == []
    assert document.header["hook"] == "A synthetic fixture hook line."


def test_duplicate_unknown_missing_and_null_keys_are_incomplete_input(checker):
    cases = (
        (
            "duplicate key",
            nf.render_chapter_file(
                nf.chapter_header(prose=nf.prose_of_length(900)),
                nf.prose_of_length(900),
                duplicate_key="words",
            ),
            "CHAPTER_HEADER_KEY_DUPLICATE",
        ),
        (
            "unknown key",
            _chapter(900, overrides={"unexpected": "Not a header key"}).text(),
            "CHAPTER_HEADER_KEY_UNKNOWN",
        ),
        (
            "missing required key",
            _chapter(900, drop_keys=["status"]).text(),
            "CHAPTER_HEADER_KEY_MISSING",
        ),
        (
            "null value",
            _chapter(900, overrides={"timeline_id": None}).text(),
            "CHAPTER_HEADER_VALUE_NULL",
        ),
    )

    for label, text, expected_code in cases:
        document = _parse(checker, text=text)
        codes = [diagnostic.code for diagnostic in document.diagnostics]
        assert codes == [expected_code], label
        disposition = document.diagnostics[0].disposition
        assert disposition == checker.DISPOSITION_INCOMPLETE, label
        assert document.boundary_resolved is True, label


def test_a_duplicated_key_keeps_no_trusted_value(checker):
    """Neither the first nor the last duplicate may be silently preferred."""

    text = nf.render_chapter_file(
        nf.chapter_header(prose=nf.prose_of_length(900)),
        nf.prose_of_length(900),
        duplicate_key="words",
    )
    document = _parse(checker, text=text)

    assert "words" not in document.header
    assert document.header_complete is False
    # The declared value is untrustworthy, so no word-count comparison is made.
    report = checker.chapter_length_report(document)
    assert report.declared_words is None
    assert checker.check_chapter_length(report) == ()


@pytest.mark.parametrize(
    "overrides",
    [
        {"movement": "prologue_part"},
        {"chapter": "one"},
        {"chapter": -1},
        {"words": -5},
        {"length_class": "very-long"},
        {"status": "polished"},
        {"pov_id": "pov-mara"},
        {"timeline_id": "TLFIXTURE001"},
        {"hook": "   "},
        {"title": "   "},
        {"motif_events": "MOT-A"},
    ],
    ids=[
        "unknown movement",
        "non-integer chapter",
        "negative chapter",
        "negative words",
        "unknown length class",
        "unknown status",
        "lowercase pov id",
        "pov id without a hyphen",
        "blank hook",
        "blank title",
        "unbracketed motif list",
    ],
)
def test_a_malformed_header_value_is_incomplete_input(checker, overrides):
    document = _parse(checker, text=_chapter(900, overrides=overrides).text())

    assert [diagnostic.code for diagnostic in document.diagnostics] == [
        "CHAPTER_HEADER_VALUE_MALFORMED"
    ]
    assert document.diagnostics[0].disposition == checker.DISPOSITION_INCOMPLETE
    assert list(overrides)[0] not in document.header


def test_a_yaml_anchor_or_continuation_line_is_rejected(checker):
    anchored = _chapter(900, overrides={"hook": "*shared"}).text()
    unquoted = anchored.replace('hook: "*shared"', "hook: *shared")
    document = _parse(checker, text=unquoted)
    assert "CHAPTER_HEADER_VALUE_MALFORMED" in [
        diagnostic.code for diagnostic in document.diagnostics
    ]

    continued = _chapter(900).text().replace(
        "status: draft", "status: draft\n  and a second line"
    )
    document = _parse(checker, text=continued)
    assert "CHAPTER_HEADER_LINE_MALFORMED" in [
        diagnostic.code for diagnostic in document.diagnostics
    ]


# ---------------------------------------------------------------------------
# Prose_Word counting
# ---------------------------------------------------------------------------


def test_only_the_prose_body_is_counted(checker):
    fixture = _chapter(
        3,
        prose="one two three\n",
        hook="A hook line carrying many separate metadata words here.",
    )
    document = _parse(checker, fixture)
    report = checker.chapter_length_report(document)

    assert report.observed_words == 3
    assert document.prose_body.strip() == "one two three"
    assert "movement" not in document.prose_body


def test_empty_prose_is_a_legal_zero(checker, tmp_path):
    fixture = _chapter(0, prose="")
    result = _one(checker, tmp_path, fixture)

    report = result.chapters[0].length_report
    assert report.observed_words == 0
    assert report.observed_length_class == "microchapter"
    assert result.result == checker.RESULT_PASS
    assert result.exit_status == 0


@pytest.mark.parametrize(
    "label, prose, expected",
    [
        ("punctuation-only tokens", ". , ? ! ;\n", 5),
        (
            "mixed scripts",
            "\u03a9 \u65e5\u672c\u8a9e \u0442\u0435\u043a\u0441\u0442\n",
            3,
        ),
        ("collapsed whitespace runs", "one   two\t\tthree\n\n\nfour\n", 4),
        ("emoji and dashes", "\u2014 \U0001f6f0 next\n", 3),
    ],
)
def test_whitespace_separated_tokens_count_across_unicode(
    checker, label, prose, expected
):
    fixture = _chapter(expected, prose=prose)
    report = checker.chapter_length_report(_parse(checker, fixture))

    assert report.observed_words == expected, label


def test_prose_is_normalized_to_nfc_before_counting(checker):
    """A combining mark composes and never splits a token in two."""

    decomposed = "cafe\u0301 nai\u0308ve\n"
    document = _parse(checker, _chapter(2, prose=decomposed))

    assert document.prose_body.strip() == "caf\u00e9 na\u00efve"
    assert "cafe\u0301" not in document.prose_body
    assert checker.chapter_length_report(document).observed_words == 2


def test_mixed_line_endings_are_normalized_before_counting(checker):
    header = nf.chapter_header(words=6, length_class="microchapter")
    text = nf.render_chapter_file(header, "one two\r\nthree four\rfive six\n")
    crlf_text = text.replace("\nmovement", "\r\nmovement").replace(
        "chapter: 1\n", "chapter: 1\r\n"
    )

    document = _parse(checker, text=crlf_text)

    assert document.diagnostics == ()
    assert "\r" not in document.prose_body
    report = checker.chapter_length_report(document)
    assert report.observed_words == 6
    assert checker.check_chapter_length(report) == ()


# ---------------------------------------------------------------------------
# Length_Class bands, boundaries, and the Hard_Chapter_Maximum
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "words, expected_class",
    [
        (0, "microchapter"),
        (1, "microchapter"),
        (699, "microchapter"),
        (700, "normal"),
        (1600, "normal"),
        (1601, "long-outlier"),
        (2500, "long-outlier"),
    ],
)
def test_length_class_bands_and_both_boundary_pairs(
    checker, tmp_path, words, expected_class
):
    fixture = _chapter(words)

    result = _one(checker, tmp_path, fixture, name="band-{0}".format(words))

    report = result.chapters[0].length_report
    assert report.observed_words == words
    assert report.observed_length_class == expected_class
    assert report.within_hard_maximum is True
    assert result.result == checker.RESULT_PASS
    assert result.exit_status == 0


def test_two_thousand_five_hundred_and_one_words_is_rejected(checker, tmp_path):
    fixture = _chapter(2501)

    result = _one(checker, tmp_path, fixture)

    assert _codes(result) == ["CHAPTER_HARD_MAXIMUM_EXCEEDED"]
    report = result.chapters[0].length_report
    assert report.observed_words == 2501
    assert report.within_hard_maximum is False
    # Above the maximum no Length_Class is valid, so none is derived.
    assert report.observed_length_class is None
    assert result.result == checker.RESULT_REVISION
    assert result.exit_status == 1


def test_declared_words_must_equal_the_observed_count(checker, tmp_path):
    fixture = _chapter(900, declared_words=1008, declared_class="normal")

    result = _one(checker, tmp_path, fixture)

    assert _codes(result) == ["CHAPTER_WORD_COUNT"]
    diagnostic = result.diagnostics[0]
    assert diagnostic.observed == "900"
    assert diagnostic.details == (("declared", "1008"),)
    assert diagnostic.expected == "equal"
    assert result.exit_status == 1


def test_a_declared_length_class_that_disagrees_is_reported(checker, tmp_path):
    fixture = _chapter(900, declared_class="microchapter")

    result = _one(checker, tmp_path, fixture)

    assert _codes(result) == ["CHAPTER_LENGTH_CLASS_MISMATCH"]
    diagnostic = result.diagnostics[0]
    assert diagnostic.observed == "normal"
    assert dict(diagnostic.details) == {"declared": "microchapter", "words": "900"}
    report = result.chapters[0].length_report
    assert (report.observed_length_class, report.declared_length_class) == (
        "normal",
        "microchapter",
    )
    assert result.exit_status == 1


# ---------------------------------------------------------------------------
# The planned purpose a Length_Outlier requires
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("words", [400, 2000])
@pytest.mark.parametrize("purpose", [None, "   "])
def test_an_outlier_without_a_planned_purpose_is_a_violation(
    checker, tmp_path, words, purpose
):
    fixture = _chapter(words)
    entry = _entry_for(fixture, outlier_purpose=purpose)

    name = "outlier-{0}-{1}".format(words, bool(purpose))
    result = _one(checker, tmp_path, fixture, entry, name=name)

    assert _codes(result) == ["CHAPTER_OUTLIER_PURPOSE_MISSING"]
    assert result.exit_status == 1


def test_a_normal_chapter_carries_a_null_outlier_purpose(checker, tmp_path):
    fixture = _chapter(900)
    entry = _entry_for(fixture, outlier_purpose="An unexpected purpose.")

    result = _one(checker, tmp_path, fixture, entry)

    assert _codes(result) == ["CHAPTER_OUTLIER_PURPOSE_UNEXPECTED"]
    assert result.exit_status == 1


def test_a_planned_outlier_with_a_purpose_passes(checker, tmp_path):
    fixture = _chapter(400)

    result = _one(checker, tmp_path, fixture)

    assert result.chapters[0].arc_entry.outlier_purpose
    assert result.result == checker.RESULT_PASS
    assert result.exit_status == 0


# ---------------------------------------------------------------------------
# The four-way filename/directory/header/ArcEntry agreement rule
# ---------------------------------------------------------------------------


def test_a_conforming_chapter_agrees_four_ways(checker, tmp_path):
    fixture = _chapter(900, movement="mindwars_part", chapter=104, slug="null-night")

    result = _one(checker, tmp_path, fixture)

    assert fixture.relative_path == (
        "chapters/mindwars-part/mindwars-part-104-null-night.md"
    )
    assert result.diagnostics == ()
    assert result.exit_status == 0


def test_a_header_sequence_that_disagrees_is_reported(checker, tmp_path):
    fixture = _chapter(900, chapter=1, overrides={"chapter": 2})

    result = _one(checker, tmp_path, fixture)

    assert _codes(result) == ["CHAPTER_SEQUENCE_DISAGREEMENT"]
    observed = result.diagnostics[0].observed
    assert "filename=1" in observed
    assert "header=2" in observed
    assert "arc_entry=1" in observed
    assert result.exit_status == 1


def test_an_outline_sequence_that_disagrees_is_reported(checker, tmp_path):
    fixture = _chapter(900, chapter=1)
    entry = _entry_for(fixture, chapter=7, filename=fixture.relative_path)

    result = _one(checker, tmp_path, fixture, entry)

    assert _codes(result) == ["CHAPTER_SEQUENCE_DISAGREEMENT"]
    assert "arc_entry=7" in result.diagnostics[0].observed


def test_a_header_movement_that_disagrees_is_reported(checker, tmp_path):
    fixture = _chapter(900, overrides={"movement": "mindwars_part"})

    result = _one(checker, tmp_path, fixture)

    assert _codes(result) == ["CHAPTER_MOVEMENT_DISAGREEMENT"]
    observed = result.diagnostics[0].observed
    assert "directory=discovery_part" in observed
    assert "filename=discovery_part" in observed
    assert "header=mindwars_part" in observed
    assert "arc_entry=discovery_part" in observed
    assert result.exit_status == 1


def test_an_outline_movement_that_disagrees_is_reported(checker, tmp_path):
    fixture = _chapter(900)
    entry = _entry_for(
        fixture, movement="aftermath_coda", filename=fixture.relative_path
    )

    result = _one(checker, tmp_path, fixture, entry)

    assert _codes(result) == ["CHAPTER_MOVEMENT_DISAGREEMENT"]
    assert "arc_entry=aftermath_coda" in result.diagnostics[0].observed


def test_a_filename_outside_the_convention_is_reported(checker, tmp_path):
    fixture = _chapter(900)
    workspace = nf.build_workspace(
        tmp_path / "workspace",
        planning=(_outline((_entry_for(fixture),)),),
    )
    stray = nf.write_text(
        workspace.manuscript_root,
        "chapters/discovery-part/Discovery_Part_1.md",
        fixture.text(),
    )

    result = checker.check_chapter_scope(
        [stray], manuscript_root=workspace.manuscript_root
    )

    assert "CHAPTER_FILENAME_MALFORMED" in _codes(result)
    assert result.chapters[0].document.filename is None


def test_a_chapter_outside_a_movement_directory_is_reported(checker, tmp_path):
    fixture = _chapter(900)
    workspace = nf.build_workspace(
        tmp_path / "workspace",
        planning=(_outline((_entry_for(fixture),)),),
    )
    misplaced = nf.write_text(
        workspace.manuscript_root,
        "chapters/discovery-part-001-synthetic-fixture.md",
        fixture.text(),
    )

    result = checker.check_chapter_scope(
        [misplaced], manuscript_root=workspace.manuscript_root
    )

    assert "CHAPTER_DIRECTORY_MISMATCH" in _codes(result)
    assert result.exit_status == 1


def test_the_global_sequence_never_resets_at_a_movement_boundary(checker, tmp_path):
    early = _chapter(900, movement="discovery_part", chapter=100, slug="late-discovery")
    later = _chapter(900, movement="mindwars_part", chapter=5, slug="early-mindwars")

    _workspace, result = _scope(
        checker,
        tmp_path,
        (early, later),
        (_entry_for(early), _entry_for(later)),
    )

    assert _codes(result) == ["CHAPTER_MOVEMENT_SEQUENCE_ORDER"]
    assert result.exit_status == 1


def test_two_files_claiming_one_global_number_is_a_duplicate_identity(
    checker, tmp_path
):
    first = _chapter(900, chapter=1, slug="first-fixture")
    second = _chapter(900, chapter=2, slug="second-fixture", overrides={"chapter": 1})

    _workspace, result = _scope(
        checker,
        tmp_path,
        (first, second),
        (_entry_for(first), _entry_for(second)),
    )

    assert "CHAPTER_SEQUENCE_DUPLICATE" in _codes(result)
    assert result.result == checker.RESULT_INCOMPLETE
    assert result.exit_status == 2


# ---------------------------------------------------------------------------
# ArcEntry availability, which is a required input rather than a violation
# ---------------------------------------------------------------------------


def test_a_chapter_with_no_matching_arc_entry_is_incomplete_input(checker, tmp_path):
    fixture = _chapter(900, chapter=3, slug="unplanned-fixture")
    other = _chapter(900, chapter=1)

    workspace = nf.build_workspace(
        tmp_path / "workspace",
        planning=(_outline((_entry_for(other),)),),
        chapters=(fixture,),
    )
    result = checker.check_chapter_scope(
        [workspace.chapter_path(fixture)], manuscript_root=workspace.manuscript_root
    )

    assert _codes(result) == ["CHAPTER_ARC_ENTRY_MISSING"]
    assert result.exit_status == 2


def test_two_arc_entries_for_one_file_is_a_duplicate_identity(checker, tmp_path):
    fixture = _chapter(900)
    entry = _entry_for(fixture)

    result = _one(checker, tmp_path, fixture, entry)
    assert result.exit_status == 0

    workspace = nf.build_workspace(
        tmp_path / "duplicate",
        planning=(_outline((entry, dict(entry))),),
        chapters=(fixture,),
    )
    duplicated = checker.check_chapter_scope(
        [workspace.chapter_path(fixture)], manuscript_root=workspace.manuscript_root
    )

    assert _codes(duplicated) == ["ARC_ENTRY_DUPLICATE_IDENTITY"]
    assert duplicated.exit_status == 2


def test_an_outline_filename_that_disagrees_is_reported(checker, tmp_path):
    fixture = _chapter(900, chapter=1)
    entry = _entry_for(
        fixture, filename="chapters/discovery-part/discovery-part-001-other-slug.md"
    )

    result = _one(checker, tmp_path, fixture, entry)

    assert _codes(result) == ["CHAPTER_ARC_ENTRY_FILENAME_DISAGREEMENT"]
    assert result.exit_status == 1


def test_a_missing_arc_outline_document_is_incomplete_input(checker, tmp_path):
    fixture = _chapter(900)
    workspace = nf.build_workspace(tmp_path / "workspace", chapters=(fixture,))

    result = checker.check_chapter_scope(
        [workspace.chapter_path(fixture)], manuscript_root=workspace.manuscript_root
    )

    assert "ARC_OUTLINE_MISSING" in _codes(result)
    assert result.exit_status == 2


def test_a_missing_chapter_file_is_incomplete_input(checker, tmp_path):
    fixture = _chapter(900)
    workspace = nf.build_workspace(
        tmp_path / "workspace", planning=(_outline((_entry_for(fixture),)),)
    )

    result = checker.check_chapter_scope(
        [workspace.chapter_path(fixture)], manuscript_root=workspace.manuscript_root
    )

    assert _codes(result) == ["CHAPTER_FILE_MISSING"]
    assert result.exit_status == 2


def test_a_duplicate_json_key_in_an_arc_entry_fence_is_incomplete_input(
    checker, tmp_path
):
    fixture = _chapter(900)
    outline = nf.planning_document(
        "planning/arc-outline.md",
        title="Arc Outline",
        preamble=(
            "```json record=ArcEntry schema=1\n"
            '{"chapter": 1, "chapter": 2}\n'
            "```\n"
        ),
    )
    workspace = nf.build_workspace(
        tmp_path / "workspace", planning=(outline,), chapters=(fixture,)
    )

    result = checker.check_chapter_scope(
        [workspace.chapter_path(fixture)], manuscript_root=workspace.manuscript_root
    )

    assert "PLANNING_FENCE_MALFORMED" in _codes(result)
    assert result.exit_status == 2


# ---------------------------------------------------------------------------
# Determinism and the read-only contract
# ---------------------------------------------------------------------------


def test_repeated_runs_are_deterministic_and_never_rewrite_a_chapter(
    checker, tmp_path
):
    fixture = _chapter(900, declared_words=901, declared_class="microchapter")
    workspace = nf.build_workspace(
        tmp_path / "workspace",
        planning=(_outline((_entry_for(fixture),)),),
        chapters=(fixture,),
    )
    chapter_path = workspace.chapter_path(fixture)
    before = chapter_path.read_bytes()

    first = checker.check_chapter_scope(
        [chapter_path], manuscript_root=workspace.manuscript_root
    )
    second = checker.check_chapter_scope(
        [chapter_path], manuscript_root=workspace.manuscript_root
    )

    assert first.diagnostics == second.diagnostics
    assert _codes(first) == ["CHAPTER_LENGTH_CLASS_MISMATCH", "CHAPTER_WORD_COUNT"]
    assert first.exit_status == 1
    assert chapter_path.read_bytes() == before


def test_every_emitted_code_is_a_stable_uppercase_identifier(checker, tmp_path):
    fixture = _chapter(2501, chapter=1, overrides={"movement": "mindwars_part"})
    entry = _entry_for(fixture, chapter=9, filename=fixture.relative_path)

    result = _one(checker, tmp_path, fixture, entry)

    assert result.diagnostics
    for diagnostic in result.diagnostics:
        assert checker.DIAGNOSTIC_CODE_PATTERN.match(diagnostic.code)
        assert diagnostic.item
        assert diagnostic.observed
        assert diagnostic.expected
