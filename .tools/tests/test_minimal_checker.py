"""Focused tests for the minimal checker's implemented surface.

Created by task 7.1. Today `.tools/check_novel.py` implements exactly one scope:
the Manuscript_Exclusion_Contract reference collector, its visibility-plan
loading, its in-memory reference artifacts, and the CLI around them. These tests
cover that surface and nothing else.

Header parsing, word counting, Length_Class derivation, direct-reference
integrity, motif/literal rules, and the JSON diagnostic format arrive with tasks
7.2 through 7.6, and their focused tests belong to task 7.7. Writing them now
would mean asserting against code that does not exist.

`test_site_exclusion.py` already covers the happy path, the resolved-alias case,
the committed contract, a missing and a malformed contract, missing root
evidence, and two CLI paths. This module deliberately does not repeat any of
them. What it adds is the uncovered implemented behaviour: three further
contract-drift codes, the whole visibility-plan surface, the one implemented
exit-1 violation path, source-eligibility rules, artifact determinism and
escaping, and the refusal of unimplemented CLI scopes.
"""

from __future__ import annotations

import json

import pytest

import novel_fixtures as nf

MANUSCRIPT_PREFIX = nf.MANUSCRIPT_ROOT_NAME + "/"


def _sources(result):
    return [source.relative_path for source in result.sources]


def _run(checker, workspace, **kwargs):
    return checker.run_site_exclusion(
        workspace.root, contract_path=workspace.contract_path, **kwargs
    )


# ---------------------------------------------------------------------------
# The contract's own `must_remain_collectible` conformance assertion
# ---------------------------------------------------------------------------


def test_title_sharing_song_stays_collectible_while_manuscript_is_excluded(
    checker, tmp_path
):
    """`songs/The Final Frontier.md` shares the novel's title and must survive.

    This is the contract's declared `must_remain_collectible` row and the reason
    substring matching is a forbidden heuristic. No existing test exercises it.
    """

    workspace = nf.build_workspace(
        tmp_path / "workspace",
        planning=nf.default_planning_documents(),
        chapters=(nf.chapter_fixture(chapter=1),),
        songs={
            "songs/The Final Frontier.md": "[Verse]\nThe source song shares the title.\n",
            "songs/control-song.md": "[Verse]\nA control song.\n",
        },
    )

    result = _run(checker, workspace)

    assert _sources(result) == [
        "songs/The Final Frontier.md",
        "songs/control-song.md",
    ]
    assert all(
        not song.source_path.startswith(MANUSCRIPT_PREFIX) for song in result.songs
    )
    assert nf.MANUSCRIPT_ROOT_NAME not in result.scanned_direct_children


# ---------------------------------------------------------------------------
# Contract drift codes not covered by test_site_exclusion.py
# ---------------------------------------------------------------------------


def _drift_workspace(tmp_path, name, mutate):
    return nf.build_workspace(
        tmp_path / name,
        contract=nf.contract_document(mutate=mutate),
        planning=nf.default_planning_documents(),
    )


def test_unsupported_contract_schema_fails_closed(checker, tmp_path):
    def mutate(document):
        document["schema"] = "manuscript-exclusion-contract/v2"

    workspace = _drift_workspace(tmp_path, "schema", mutate)

    with pytest.raises(checker.SiteExclusionError) as raised:
        _run(checker, workspace)

    assert raised.value.code == "CONTRACT_UNSUPPORTED_SCHEMA"
    assert raised.value.exit_status == 2


def test_declared_at_pointing_at_another_file_fails_closed(checker, tmp_path):
    def mutate(document):
        document["declared_at"] = "{0}/front-matter.md".format(nf.MANUSCRIPT_ROOT_NAME)

    workspace = _drift_workspace(tmp_path, "declared-at", mutate)

    with pytest.raises(checker.SiteExclusionError) as raised:
        _run(checker, workspace)

    assert raised.value.code == "CONTRACT_STALE"
    assert raised.value.exit_status == 2


def test_exclusion_path_below_the_workspace_root_is_rejected(checker, tmp_path):
    def mutate(document):
        document["exclusions"][0]["path"] = "{0}/chapters".format(
            nf.MANUSCRIPT_ROOT_NAME
        )

    workspace = _drift_workspace(tmp_path, "nested-exclusion", mutate)

    with pytest.raises(checker.SiteExclusionError) as raised:
        _run(checker, workspace)

    # The matching rule resolves direct workspace children only, so a deeper
    # path is malformed rather than a narrower exclusion.
    assert raised.value.code == "CONTRACT_MALFORMED"
    assert raised.value.exit_status == 2


# ---------------------------------------------------------------------------
# Visibility plan loading, entirely uncovered until now
# ---------------------------------------------------------------------------


def test_missing_visibility_plan_fails_closed(checker, workspace):
    with pytest.raises(checker.SiteExclusionError) as raised:
        _run(
            checker,
            workspace,
            visibility_plan_path=workspace.root / "absent-visibility.json",
        )

    assert raised.value.code == "VISIBILITY_PLAN_MISSING"
    assert raised.value.exit_status == 2


@pytest.mark.parametrize(
    "label, document",
    [
        (
            "unsupported schema",
            nf.visibility_plan_document(overrides={"schema": "song-visibility/v9"}),
        ),
        (
            "non-boolean default",
            nf.visibility_plan_document(overrides={"default_visible": "yes"}),
        ),
        (
            "rows not an array",
            nf.visibility_plan_document(overrides={"rows": {}}),
        ),
        (
            "duplicate row for one source",
            nf.visibility_plan_document(
                [
                    nf.visibility_row("songs/control-song.md"),
                    nf.visibility_row("songs/control-song.md", visible=False),
                ]
            ),
        ),
        (
            "non-boolean visible",
            nf.visibility_plan_document(
                [{"source": "songs/control-song.md", "visible": "true"}]
            ),
        ),
        (
            "slug that is not kebab-case",
            nf.visibility_plan_document(
                [nf.visibility_row("songs/control-song.md", slug="Control Song")]
            ),
        ),
        (
            "source that is not markdown",
            nf.visibility_plan_document([nf.visibility_row("songs/control-song.txt")]),
        ),
    ],
)
def test_malformed_visibility_plan_fails_closed(checker, tmp_path, label, document):
    workspace = nf.build_workspace(
        tmp_path / "workspace", visibility=document
    )

    with pytest.raises(checker.SiteExclusionError) as raised:
        _run(checker, workspace, visibility_plan_path=workspace.visibility_plan_path)

    assert raised.value.code == "VISIBILITY_PLAN_MALFORMED", label
    assert raised.value.exit_status == 2


@pytest.mark.parametrize(
    "default_visible, rows, expected_slugs",
    [
        (True, [], ["control-song"]),
        (False, [], []),
        (True, [{"source": "songs/control-song.md", "visible": False}], []),
        (
            False,
            [{"source": "songs/control-song.md", "visible": True}],
            ["control-song"],
        ),
    ],
)
def test_visibility_rows_and_default_decide_song_collection(
    checker, tmp_path, default_visible, rows, expected_slugs
):
    workspace = nf.build_workspace(
        tmp_path / "workspace",
        visibility=nf.visibility_plan_document(rows, default_visible=default_visible),
    )

    result = _run(
        checker, workspace, visibility_plan_path=workspace.visibility_plan_path
    )

    # Discovery is unchanged; visibility only decides what becomes a Song.
    assert _sources(result) == ["songs/control-song.md"]
    assert [song.slug for song in result.songs] == expected_slugs


def test_slug_collision_is_a_violation_rather_than_incomplete_input(checker, tmp_path):
    """The only implemented exit-1 path, and it must not read as exit 2.

    Requirements 12.9, 12.14, and 12.15 separate an objective violation from an
    unreadable or incomplete input. Nothing else in the current checker
    distinguishes the two statuses.
    """

    workspace = nf.build_workspace(
        tmp_path / "workspace",
        songs={
            "songs/first/Control Song.md": "[Verse]\nOne.\n",
            "songs/second/control-song.md": "[Verse]\nTwo.\n",
        },
    )

    with pytest.raises(checker.SiteExclusionError) as raised:
        _run(checker, workspace)

    assert raised.value.code == "SONG_SLUG_COLLISION"
    assert raised.value.exit_status == 1


# ---------------------------------------------------------------------------
# Source eligibility after exclusion filtering
# ---------------------------------------------------------------------------


def test_hidden_roots_and_non_markdown_files_are_not_sources(checker, tmp_path):
    workspace = nf.build_workspace(
        tmp_path / "workspace",
        extra_files={
            ".hidden-tooling/looks-like-a-song.md": "[Verse]\nHidden.\n",
            "songs/reading-notes.txt": "not markdown\n",
            "notes.md": "# Root-level markdown outside the manuscript\n",
        },
    )

    result = _run(checker, workspace)

    assert _sources(result) == ["notes.md", "songs/control-song.md"]
    assert ".hidden-tooling" not in result.scanned_direct_children
    assert sorted(result.scanned_direct_children) == ["notes.md", "songs"]


# ---------------------------------------------------------------------------
# Reference artifacts
# ---------------------------------------------------------------------------


def test_reference_artifacts_are_deterministic_and_escape_metadata(checker, tmp_path):
    workspace = nf.build_workspace(
        tmp_path / "workspace",
        visibility=nf.visibility_plan_document(
            [nf.visibility_row("songs/control-song.md", title="Ampersand & <Angle>")]
        ),
    )

    first = _run(
        checker, workspace, visibility_plan_path=workspace.visibility_plan_path
    )
    second = _run(
        checker, workspace, visibility_plan_path=workspace.visibility_plan_path
    )

    assert first.artifacts == second.artifacts

    by_kind = {artifact.kind: artifact for artifact in first.artifacts}
    assert "Ampersand &amp; &lt;Angle&gt;" in by_kind["lyrics"].content
    assert "<Angle>" not in by_kind["lyrics"].content
    assert by_kind["lyrics"].output_path == "lyrics/ampersand-angle.html"
    assert json.loads(by_kind["index"].content) == [
        {
            "slug": "ampersand-angle",
            "source": "songs/control-song.md",
            "title": "Ampersand & <Angle>",
        }
    ]


def test_no_songs_still_yields_empty_search_and_index_artifacts(checker, tmp_path):
    workspace = nf.build_workspace(
        tmp_path / "workspace",
        visibility=nf.visibility_plan_document(default_visible=False),
    )

    result = _run(
        checker, workspace, visibility_plan_path=workspace.visibility_plan_path
    )

    assert result.songs == ()
    assert {artifact.kind for artifact in result.artifacts} == {"search", "index"}
    for artifact in result.artifacts:
        assert json.loads(artifact.content) == []
        assert artifact.source_paths == ()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def test_cli_refuses_an_unimplemented_scope_instead_of_passing_silently(
    checker, capsys
):
    with pytest.raises(SystemExit) as raised:
        checker.main([])

    assert raised.value.code == 2
    assert "only --site-exclusion is implemented" in capsys.readouterr().err
