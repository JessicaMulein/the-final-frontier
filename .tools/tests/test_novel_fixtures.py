"""Guard tests for the shared synthetic-fixture builders.

Created by task 7.1. All fifteen principal property tests will build their
inputs from `novel_fixtures`, so a silent drift in the builders would weaken
every one of them at once. These tests check the builders against the recorded
contracts in `planning/record-schemas.md`, `planning/file-conventions.md`, and
the design's Chapter_Header metadata example.

They assert nothing about `check_novel.py`. `derive_length_class` and
`count_prose_words` are fixture-side conveniences; the checker's own derivations
are the subject of tasks 7.2, 8.13, and 8.14.
"""

from __future__ import annotations

import json

import pytest

import novel_fixtures as nf

# The order the design's metadata-only example uses.
EXPECTED_HEADER_KEY_ORDER = (
    "movement",
    "chapter",
    "title",
    "pov_id",
    "timeline_id",
    "motif_events",
    "hook",
    "words",
    "length_class",
    "status",
)


def test_chapter_header_has_exactly_the_ten_restricted_keys_in_order():
    header = nf.chapter_header()

    assert tuple(header) == EXPECTED_HEADER_KEY_ORDER
    assert tuple(header) == nf.CHAPTER_HEADER_KEYS
    assert all(value is not None for value in header.values())


def test_rendered_header_is_one_key_per_line_between_bare_delimiters():
    prose = nf.prose_of_length(1200)
    header = nf.chapter_header(
        movement="aftermath_coda",
        chapter=124,
        motif_events=["MOT-COME-04", "MOT-KETTLE-02"],
        prose=prose,
    )

    text = nf.render_chapter_file(header, prose)
    lines = text.split("\n")

    assert lines[0] == "---"
    assert lines[11] == "---"
    assert [line.split(":", 1)[0] for line in lines[1:11]] == list(
        EXPECTED_HEADER_KEY_ORDER
    )
    assert "motif_events: [MOT-COME-04, MOT-KETTLE-02]" in lines
    assert 'title: "A Synthetic Chapter"' in lines
    assert 'hook: "A synthetic fixture hook line."' in lines
    # Prose Body begins after the closing delimiter and is unmodified.
    assert text.split("---\n", 2)[2].lstrip("\n") == prose


def test_declared_words_and_length_class_agree_with_the_generated_prose():
    prose = nf.prose_of_length(1601)
    header = nf.chapter_header(prose=prose)

    assert header["words"] == 1601 == nf.count_prose_words(prose)
    assert header["length_class"] == "long-outlier"


@pytest.mark.parametrize(
    "words, expected",
    [
        (0, "microchapter"),
        (699, "microchapter"),
        (700, "normal"),
        (1600, "normal"),
        (1601, "long-outlier"),
        (2500, "long-outlier"),
    ],
)
def test_fixture_length_bands_match_the_recorded_boundaries(words, expected):
    assert nf.derive_length_class(words) == expected


def test_fixture_refuses_to_classify_above_the_hard_chapter_maximum():
    with pytest.raises(nf.FixtureError):
        nf.derive_length_class(nf.HARD_CHAPTER_MAXIMUM + 1)


@pytest.mark.parametrize(
    "movement, chapter, expected",
    [
        ("discovery_part", 1, "chapters/discovery-part/discovery-part-001-slug.md"),
        (
            "private_defense_part",
            30,
            "chapters/private-defense-part/private-defense-part-030-slug.md",
        ),
        ("mindwars_part", 104, "chapters/mindwars-part/mindwars-part-104-slug.md"),
        (
            "aftermath_coda",
            128,
            "chapters/aftermath-coda/aftermath-coda-128-slug.md",
        ),
    ],
)
def test_chapter_paths_follow_the_global_non_resetting_convention(
    movement, chapter, expected
):
    assert nf.chapter_relative_path(movement, chapter, "slug") == expected


def test_json_fence_uses_the_required_information_string_and_round_trips():
    payload = nf.arc_entry(chapter=7, slug="seventh-fixture")

    block = nf.render_json_fence("ArcEntry", payload)
    lines = block.split("\n")

    assert lines[0] == "```json record=ArcEntry schema=1"
    assert lines[-2] == "```"
    assert json.loads("\n".join(lines[1:-2])) == payload


def test_overrides_and_drop_keys_can_inject_a_single_violation():
    unknown = nf.chapter_header(overrides={"unexpected": "not a permitted key"})
    missing = nf.chapter_header(drop_keys=["words"])
    duplicated = nf.render_chapter_header(nf.chapter_header(), duplicate_key="status")

    assert "unexpected" in unknown and len(unknown) == len(nf.CHAPTER_HEADER_KEYS) + 1
    assert "words" not in missing
    assert duplicated.count("status:") == 2


def test_builders_are_deterministic_across_two_identical_workspaces(tmp_path):
    def build(name):
        return nf.build_workspace(
            tmp_path / name,
            planning=nf.default_planning_documents(),
            chapters=(nf.chapter_fixture(chapter=1),),
        )

    first, second = build("one"), build("two")

    def snapshot(workspace):
        return {
            path.relative_to(workspace.root).as_posix(): path.read_text(
                encoding="utf-8"
            )
            for path in sorted(workspace.root.rglob("*"))
            if path.is_file()
        }

    assert snapshot(first) == snapshot(second)


def test_default_workspace_supplies_real_manuscript_markdown_to_exclude(workspace):
    manuscript_markdown = sorted(
        path.relative_to(workspace.manuscript_root).as_posix()
        for path in workspace.manuscript_root.rglob("*.md")
    )

    assert "front-matter.md" in manuscript_markdown
    assert "planning/arc-outline.md" in manuscript_markdown
    assert any(name.startswith("chapters/") for name in manuscript_markdown)
    assert workspace.contract_path.is_file()
    # Typed fenced records are present and parseable where the tests expect them.
    outline = workspace.read(
        "{0}/planning/arc-outline.md".format(workspace.manuscript_root.name)
    )
    assert "```json record=ArcEntry schema=1" in outline
    assert "```json record=CrossCut schema=1" in outline
