from __future__ import annotations

import socket
from pathlib import Path

import pytest

from frontier_audiobook import narrate
from frontier_audiobook.errors import InputError
from frontier_audiobook.production import (
    ProductionSelectors,
    create_production_plan,
    load_production_plan,
    resolve_production_selectors,
    snapshot_track_source,
)
from frontier_audiobook.production_config import (
    build_ordered_track_catalog,
    parse_production_toml,
)
from frontier_audiobook.production_models import (
    FrozenBatchPlan,
    SourceKind,
    StrictRecordCodec,
    canonical_sha256,
    record_to_data,
)
from frontier_audiobook.util import read_bytes_nofollow, sha256_bytes, sha256_text


SPECIAL_SOURCE = """\
# Written Front Matter

## Spoken Title

Approved spoken opening words only.

## Copyright

This section is not approved for narration.
"""

CHAPTER_SENTENCES = (
    "Alpha one two three four.",
    "Bravo one two three four.",
    "Charlie one two three four.",
    "Delta one two three four.",
    "Echo one two three four.",
)


@pytest.fixture(autouse=True)
def deny_network_and_render(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("production planning must remain offline and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")


def _chapter_path(workspace: Path, chapter: int) -> Path:
    names = {
        1: "discovery-part-001-first-contact.md",
        2: "discovery-part-002-second-signal.md",
        3: "discovery-part-003-the-failed-check.md",
    }
    return (
        workspace
        / "The Final Frontier Novel"
        / "chapters"
        / "discovery-part"
        / names[chapter]
    )


def _write_chapter(workspace: Path, chapter: int, sentences: tuple[str, ...]) -> Path:
    path = _chapter_path(workspace, chapter)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = " ".join(sentences)
    path.write_text(
        "\n".join(
            (
                "---",
                "movement: discovery",
                f"chapter: {chapter}",
                "pov_id: test-pov",
                "timeline_id: test-timeline",
                "motif_events: none",
                "hook: test-hook",
                f"words: {len(body.split())}",
                "length_class: short",
                "status: draft",
                "---",
                body,
                "",
            )
        ),
        encoding="utf-8",
    )
    return path


def _write_workspace(workspace: Path, *, max_tracks_per_plan: int = 4) -> Path:
    for chapter in (1, 2, 3):
        _write_chapter(workspace, chapter, CHAPTER_SENTENCES)
    special_path = workspace / ".audiobook" / "config" / "tracks" / "opening-credits.md"
    special_path.parent.mkdir(parents=True, exist_ok=True)
    special_path.write_text(SPECIAL_SOURCE, encoding="utf-8")
    special_sha256 = sha256_bytes(SPECIAL_SOURCE.encode("utf-8"))

    config_path = workspace / ".audiobook" / "config" / "production.toml"
    config_path.write_text(
        f'''schema_version = 1
book_id = "the-final-frontier"
manuscript_root = "The Final Frontier Novel"
build_root = ".audiobook/build/production"
delivery_root = ".audiobook/dist/audiobook"
max_tracks_per_plan = {max_tracks_per_plan}

[defaults]
voice = "tiffany"
model_id = "amazon.nova-2-sonic-v1:0"
region = "us-east-1"
profile_label = "frontier-audiobook"
target_segment_words = 5
fidelity_policy = "exact"
normalization = "frontier-word-sequence-v1"
output_template = "{{sequence:03d}}-{{track_slug}}-{{voice}}.wav"

[defaults.audio]
sample_rate_hz = 24000
sample_size_bits = 16
channels = 1

[estimate]
rate_max_age_hours = 24
preflight_max_age_hours = 24
input_speech_tokens_per_call = 0
input_text_tokens_per_call = 8192
output_speech_tokens_per_call = 8192
output_text_tokens_per_call = 8192

[[tracks]]
id = "opening-credits"
kind = "opening_credits"
sequence = 1
source_path = ".audiobook/config/tracks/opening-credits.md"
source_section = "spoken-title"
approved_sha256 = "{special_sha256}"
enabled = true
approval_status = "approved"
render_once = true

[tracks.override]
''',
        encoding="utf-8",
    )
    return config_path


def _config_and_catalog(workspace: Path, config_path: Path):
    config = parse_production_toml(read_bytes_nofollow(config_path), label=str(config_path))
    return config, build_ordered_track_catalog(config, workspace)


def _track(catalog, track_id: str):
    return next(item for item in catalog.tracks if item.id == track_id)


def test_repeatable_chapter_range_and_track_selectors_resolve_exact_catalog_scope(tmp_path):
    config_path = _write_workspace(tmp_path)
    _config, catalog = _config_and_catalog(tmp_path, config_path)

    selectors = ProductionSelectors.from_cli(
        chapters=[3, 1],
        chapter_ranges=["2:2"],
        tracks=["opening-credits"],
    )
    scope = resolve_production_selectors(catalog, selectors)

    assert scope.selectors == (
        "chapter:3",
        "chapter:1",
        "chapter-range:2:2",
        "track:opening-credits",
    )
    assert tuple(item.id for item in scope.tracks) == (
        "opening-credits",
        "chapter-001",
        "chapter-002",
        "chapter-003",
    )
    assert scope.tracks[-1].source_path == (
        "The Final Frontier Novel/chapters/discovery-part/"
        "discovery-part-003-the-failed-check.md"
    )


def test_selectors_reject_empty_reversed_duplicate_unresolved_and_oversized_scopes(tmp_path):
    config_path = _write_workspace(tmp_path)
    _config, catalog = _config_and_catalog(tmp_path, config_path)

    with pytest.raises(InputError, match="At least one"):
        resolve_production_selectors(catalog, ProductionSelectors.from_cli())
    with pytest.raises(InputError, match="not reversed"):
        resolve_production_selectors(
            catalog, ProductionSelectors.from_cli(chapter_ranges=["3:2"])
        )
    with pytest.raises(InputError, match="duplicate Track 'chapter-001'"):
        resolve_production_selectors(
            catalog,
            ProductionSelectors.from_cli(chapters=[1], chapter_ranges=["1:2"]),
        )
    with pytest.raises(InputError, match="unresolved IDs"):
        resolve_production_selectors(
            catalog, ProductionSelectors.from_cli(chapters=[99])
        )
    with pytest.raises(InputError, match="unresolved IDs"):
        resolve_production_selectors(
            catalog, ProductionSelectors.from_cli(tracks=["missing-track"])
        )
    with pytest.raises(InputError, match="exceeds max_tracks_per_plan=4"):
        resolve_production_selectors(
            catalog, ProductionSelectors.from_cli(chapter_ranges=["1:5"])
        )
    with pytest.raises(InputError, match="START:END"):
        resolve_production_selectors(
            catalog, ProductionSelectors.from_cli(chapter_ranges=[":2"])
        )


def test_approved_special_track_adapter_hashes_only_the_named_handoff_section(tmp_path):
    config_path = _write_workspace(tmp_path)
    config, catalog = _config_and_catalog(tmp_path, config_path)
    opening = _track(catalog, "opening-credits")

    snapshot = snapshot_track_source(config, opening, tmp_path)

    assert snapshot.source_kind is SourceKind.APPROVED_SPECIAL_TRACK
    assert snapshot.source_section == "spoken-title"
    assert snapshot.raw_sha256 == sha256_bytes(SPECIAL_SOURCE.encode("utf-8"))
    assert snapshot.normalized_body_sha256 == sha256_text(
        "Approved spoken opening words only."
    )
    assert snapshot.spoken_sha256 == snapshot.normalized_body_sha256
    assert snapshot.spoken_token_count == 5
    assert snapshot.segment_count == 1
    persisted = record_to_data(snapshot)
    assert "Approved spoken opening words only." not in repr(persisted)
    assert "This section is not approved for narration." not in repr(persisted)


def test_render_identity_uses_bounded_context_and_survives_distant_ordinal_shift(tmp_path):
    config_path = _write_workspace(tmp_path)
    config, catalog = _config_and_catalog(tmp_path, config_path)
    original = snapshot_track_source(config, _track(catalog, "chapter-003"), tmp_path)

    inserted = "Inserted one two three four."
    _write_chapter(
        tmp_path,
        3,
        (*CHAPTER_SENTENCES[:2], inserted, *CHAPTER_SENTENCES[2:]),
    )
    config, catalog = _config_and_catalog(tmp_path, config_path)
    changed = snapshot_track_source(config, _track(catalog, "chapter-003"), tmp_path)

    assert original.raw_sha256 != changed.raw_sha256
    assert original.spoken_sha256 != changed.spoken_sha256
    assert original.render_context_radius == changed.render_context_radius == 1

    original_by_text = {item.text_sha256: item for item in original.segments}
    changed_by_text = {item.text_sha256: item for item in changed.segments}
    sentence_hashes = {sentence: sha256_text(sentence) for sentence in CHAPTER_SENTENCES}

    # The insertion changes its immediate neighbors' quality context, not the
    # identities of distant unchanged render inputs.
    assert (
        original_by_text[sentence_hashes[CHAPTER_SENTENCES[0]]].render_identity_sha256
        == changed_by_text[sentence_hashes[CHAPTER_SENTENCES[0]]].render_identity_sha256
    )
    for sentence in CHAPTER_SENTENCES[1:3]:
        assert (
            original_by_text[sentence_hashes[sentence]].render_identity_sha256
            != changed_by_text[sentence_hashes[sentence]].render_identity_sha256
        )
    for sentence in CHAPTER_SENTENCES[3:]:
        assert (
            original_by_text[sentence_hashes[sentence]].render_identity_sha256
            == changed_by_text[sentence_hashes[sentence]].render_identity_sha256
        )
    assert original_by_text[sentence_hashes[CHAPTER_SENTENCES[3]]].ordinal == 4
    assert changed_by_text[sentence_hashes[CHAPTER_SENTENCES[3]]].ordinal == 5


def test_plan_creation_is_canonical_idempotent_collision_safe_and_recomputed(tmp_path):
    config_path = _write_workspace(tmp_path)
    selectors = ProductionSelectors.from_cli(chapters=[3], tracks=["opening-credits"])

    plan_path = create_production_plan(
        config_path,
        selectors,
        plan_id="chapter-three-pilot-plan",
        workspace_root=tmp_path,
        created_at_utc="2026-09-12T00:00:00Z",
    )
    original_bytes = read_bytes_nofollow(plan_path)
    plan = load_production_plan(plan_path)

    assert plan.config_sha256 == sha256_bytes(read_bytes_nofollow(config_path))
    assert tuple(item.track_id for item in plan.tracks) == (
        "opening-credits",
        "chapter-003",
    )
    assert original_bytes == StrictRecordCodec(FrozenBatchPlan).dump_bytes(plan)
    assert all(item.maximum_new_calls == item.source.segment_count for item in plan.tracks)
    for item in plan.tracks:
        assert item.command_sha256 == canonical_sha256(item.command_argv)
        assert item.command_argv[:2] == ("frontier-audiobook", "_production-worker")
        assert item.command_argv[item.command_argv.index("--track") + 1] == item.track_id

    encoded = original_bytes.decode("utf-8")
    assert "Approved spoken opening words only." not in encoded
    assert CHAPTER_SENTENCES[0] not in encoded
    assert "source_text" not in encoded
    assert "segment_text" not in encoded
    assert "transcript" not in encoded

    # The existing creation timestamp is retained while every current input is
    # recomputed and compared, making an explicit plan ID genuinely idempotent.
    assert (
        create_production_plan(
            config_path,
            selectors,
            plan_id="chapter-three-pilot-plan",
            workspace_root=tmp_path,
        )
        == plan_path
    )
    assert read_bytes_nofollow(plan_path) == original_bytes

    changed_sentences = (*CHAPTER_SENTENCES, "Foxtrot one two three four.")
    _write_chapter(tmp_path, 3, changed_sentences)
    with pytest.raises(InputError, match="existing canonical bytes differ"):
        create_production_plan(
            config_path,
            selectors,
            plan_id="chapter-three-pilot-plan",
            workspace_root=tmp_path,
        )
    assert read_bytes_nofollow(plan_path) == original_bytes

    recomputed_path = create_production_plan(
        config_path,
        selectors,
        plan_id="chapter-three-pilot-plan-recomputed",
        workspace_root=tmp_path,
        created_at_utc="2026-09-12T00:01:00Z",
    )
    recomputed = load_production_plan(recomputed_path)
    old_chapter = next(item for item in plan.tracks if item.track_id == "chapter-003")
    new_chapter = next(item for item in recomputed.tracks if item.track_id == "chapter-003")
    assert new_chapter.source.raw_sha256 != old_chapter.source.raw_sha256
    assert new_chapter.source.segment_count == old_chapter.source.segment_count + 1
    assert new_chapter.maximum_new_calls == new_chapter.source.segment_count
