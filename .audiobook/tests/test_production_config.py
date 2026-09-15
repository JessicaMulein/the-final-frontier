from __future__ import annotations

import socket
from dataclasses import replace
from pathlib import Path

import pytest

from frontier_audiobook.errors import InputError
from frontier_audiobook.production_config import (
    AudioOverride,
    ProductionTomlCodec,
    SourceApprovalStatus,
    TrackDeclaration,
    TrackSettingsOverride,
    build_ordered_track_catalog,
    load_production_config,
    parse_production_toml,
    print_production_toml,
    production_toml_sha256,
    resolve_effective_track_config,
)
from frontier_audiobook.production_models import AudioEncoding, FidelityPolicy, TrackKind
from frontier_audiobook.util import sha256_bytes
from frontier_audiobook.verify import normalized_tokens


VALID_TOML = """\
schema_version = 1
book_id = "the-final-frontier"
manuscript_root = "The Final Frontier Novel"
build_root = ".audiobook/build/production"
delivery_root = ".audiobook/dist/audiobook"
max_tracks_per_plan = 16

[defaults]
voice = "tiffany"
model_id = "amazon.nova-2-sonic-v1:0"
region = "us-east-1"
profile_label = "frontier-audiobook"
target_segment_words = 5
fidelity_policy = "exact"
normalization = "frontier-word-sequence-v1"
output_template = "{sequence:03d}-{track_slug}-{voice}.wav"

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

[track_kinds.chapter]
target_segment_words = 7

[track_kinds.chapter.audio]
sample_rate_hz = 24000

[[tracks]]
id = "closing-credits"
kind = "closing_credits"
sequence = 132
source_path = ".audiobook/config/tracks/closing-credits.md"
approved_sha256 = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
enabled = true
approval_status = "approved"
render_once = true

[tracks.override]
voice = "amy"

[tracks.override.audio]
channels = 1

[[tracks]]
id = "opening-credits"
kind = "opening_credits"
sequence = 1
source_path = ".audiobook/config/tracks/opening-credits.md"
source_section = "spoken-title"
enabled = true
approval_status = "approved"
render_once = true

[tracks.override]
"""


@pytest.fixture(autouse=True)
def deny_python_network(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("production config tests must remain offline")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")


def test_production_toml_parse_print_parse_is_deterministic_and_complete(tmp_path):
    parsed = parse_production_toml(VALID_TOML)

    assert parsed.schema_version == 1
    assert parsed.defaults.voice == "tiffany"
    assert parsed.defaults.fidelity_policy is FidelityPolicy.EXACT
    assert parsed.defaults.audio.sample_rate_hz == 24000
    assert parsed.track_kind_overrides[0].kind is TrackKind.CHAPTER
    assert tuple(track.id for track in parsed.tracks) == ("opening-credits", "closing-credits")
    assert all(track.approval_status is SourceApprovalStatus.APPROVED for track in parsed.tracks)

    printed = print_production_toml(parsed)
    reparsed = parse_production_toml(printed)
    assert reparsed == parsed
    assert print_production_toml(reparsed) == printed
    assert production_toml_sha256(parsed) == production_toml_sha256(reparsed)
    assert printed.endswith("\n")
    assert "\r" not in printed

    path = tmp_path / "production.toml"
    path.write_text(printed, encoding="utf-8")
    assert load_production_config(path) == parsed
    assert ProductionTomlCodec.load(path) == parsed
    assert ProductionTomlCodec.dumps(parsed) == printed
    assert ProductionTomlCodec.loads(printed) == parsed


def test_production_toml_rejects_malformed_utf8_and_duplicate_keys():
    with pytest.raises(InputError, match="Malformed UTF-8 TOML"):
        parse_production_toml(b"schema_version = \xff")

    duplicate = VALID_TOML.replace(
        'book_id = "the-final-frontier"',
        'book_id = "the-final-frontier"\nbook_id = "duplicate"',
        1,
    )
    with pytest.raises(InputError, match="Malformed TOML"):
        parse_production_toml(duplicate)


def test_production_toml_rejects_unknown_fields_enums_nonfinite_and_unsafe_paths():
    unknown = VALID_TOML.replace(
        "max_tracks_per_plan = 16",
        'max_tracks_per_plan = 16\naccount_id = "must-not-persist"',
        1,
    )
    with pytest.raises(InputError, match=r"unknown=\['account_id'\]"):
        parse_production_toml(unknown)

    unknown_nested = VALID_TOML.replace(
        'voice = "tiffany"',
        'voice = "tiffany"\ntranscript = "forbidden"',
        1,
    )
    with pytest.raises(InputError, match=r"unknown=\['transcript'\]"):
        parse_production_toml(unknown_nested)

    unknown_enum = VALID_TOML.replace('fidelity_policy = "exact"', 'fidelity_policy = "fuzzy"', 1)
    with pytest.raises(InputError, match="unknown enum value 'fuzzy'"):
        parse_production_toml(unknown_enum)

    unknown_approval = VALID_TOML.replace('approval_status = "approved"', 'approval_status = "draft"', 1)
    with pytest.raises(InputError, match="unknown enum value 'draft'"):
        parse_production_toml(unknown_approval)

    nonfinite = VALID_TOML.replace("rate_max_age_hours = 24", "rate_max_age_hours = inf", 1)
    with pytest.raises(InputError, match="non-finite number"):
        parse_production_toml(nonfinite)

    unsafe = VALID_TOML.replace(
        'build_root = ".audiobook/build/production"',
        'build_root = "../outside"',
        1,
    )
    with pytest.raises(InputError, match="traversal-free relative path"):
        parse_production_toml(unsafe)


def test_production_toml_rejects_schema_and_duplicate_logical_tracks():
    wrong_schema = VALID_TOML.replace("schema_version = 1", "schema_version = true", 1)
    with pytest.raises(InputError, match="schema_version must be integer 1"):
        parse_production_toml(wrong_schema)

    duplicate_id = VALID_TOML.replace('id = "closing-credits"', 'id = "opening-credits"', 1)
    with pytest.raises(InputError, match="duplicate Track IDs"):
        parse_production_toml(duplicate_id)

    duplicate_sequence = VALID_TOML.replace("sequence = 132", "sequence = 1", 1)
    with pytest.raises(InputError, match="duplicate Track sequence"):
        parse_production_toml(duplicate_sequence)


def test_production_toml_rejects_unknown_track_kind_and_override_keys():
    unknown_kind = VALID_TOML.replace(
        "[track_kinds.chapter]", "[track_kinds.appendix]", 1
    ).replace("[track_kinds.chapter.audio]", "[track_kinds.appendix.audio]", 1)
    with pytest.raises(InputError, match=r"unknown=\['appendix'\]"):
        parse_production_toml(unknown_kind)

    unknown_override = VALID_TOML.replace(
        'voice = "amy"', 'voice = "amy"\nsystem_prompt = "forbidden"', 1
    )
    with pytest.raises(InputError, match=r"unknown=\['system_prompt'\]"):
        parse_production_toml(unknown_override)


def test_override_resolution_uses_global_then_kind_then_exact_with_full_provenance():
    parsed = parse_production_toml(VALID_TOML)
    chapter = TrackDeclaration(
        id="chapter-003",
        kind=TrackKind.CHAPTER,
        sequence=4,
        source_path="The Final Frontier Novel/chapters/discovery-part/discovery-part-003-the-failed-check.md",
        source_section=None,
        approved_sha256=None,
        render_once=False,
        enabled=True,
        approval_status=SourceApprovalStatus.NOT_REQUIRED,
        override=TrackSettingsOverride(
            voice="amy",
            region="us-west-2",
            audio=AudioOverride(channels=2),
        ),
    )

    resolved = resolve_effective_track_config(parsed, chapter)

    assert resolved == resolve_effective_track_config(parsed, chapter)
    assert resolved.voice == "amy"
    assert resolved.region == "us-west-2"
    assert resolved.model_id == "amazon.nova-2-sonic-v1:0"
    assert resolved.target_segment_words == 7
    assert resolved.fidelity_policy is FidelityPolicy.EXACT
    assert resolved.audio_format.sample_rate_hz == 24000
    assert resolved.audio_format.channels == 2
    assert resolved.audio_format.encoding is AudioEncoding.PCM_S16LE
    assert resolved.output_path.endswith("/004-chapter-003-amy.wav")
    assert resolved.resolution_provenance["model_id"] == "global-defaults"
    assert resolved.resolution_provenance["target_segment_words"] == "track-kind:chapter"
    assert resolved.resolution_provenance["voice"] == "exact-track:chapter-003"
    assert resolved.resolution_provenance["audio.channels"] == "exact-track:chapter-003"


def test_output_templates_are_field_limited_and_render_to_one_confined_wav():
    unknown_field = VALID_TOML.replace(
        'output_template = "{sequence:03d}-{track_slug}-{voice}.wav"',
        'output_template = "{track_slug.__class__}.wav"',
        1,
    )
    with pytest.raises(InputError, match="unsupported field"):
        parse_production_toml(unknown_field)

    unsafe_format = VALID_TOML.replace(
        'output_template = "{sequence:03d}-{track_slug}-{voice}.wav"',
        'output_template = "{sequence:0999d}-{track_slug}.wav"',
        1,
    )
    with pytest.raises(InputError, match="unsafe sequence format"):
        parse_production_toml(unsafe_format)

    parsed = parse_production_toml(VALID_TOML)
    track = replace(
        parsed.tracks[0],
        override=TrackSettingsOverride(voice="nested/tiffany"),
    )
    with pytest.raises(InputError, match="one confined WAV filename"):
        resolve_effective_track_config(parsed, track)


def test_tracked_config_has_required_defaults_and_pending_render_once_catalog():
    workspace_root = Path(__file__).resolve().parents[2]
    config_path = workspace_root / ".audiobook" / "config" / "production.toml"
    config = load_production_config(config_path)

    assert config.defaults.voice == "tiffany"
    assert config.defaults.model_id == "amazon.nova-2-sonic-v1:0"
    assert config.defaults.region == "us-east-1"
    assert config.defaults.profile_label == "frontier-audiobook"
    assert config.defaults.target_segment_words == 5
    assert config.defaults.fidelity_policy is FidelityPolicy.EXACT
    assert config.defaults.normalization == "frontier-word-sequence-v1"
    assert (
        config.defaults.audio.sample_rate_hz,
        config.defaults.audio.sample_size_bits,
        config.defaults.audio.channels,
    ) == (24000, 16, 1)
    assert print_production_toml(config) == config_path.read_text(encoding="utf-8")

    # The dedication Special Track has an explicitly approved source; every other
    # Special Track still ships disabled and pending operator approval.
    approved_ids = {"dedication"}
    pending_ids = {
        "opening-credits",
        "epigraph",
        "narratable-front-matter",
        "closing-credits",
    }
    special_ids = approved_ids | pending_ids
    assert {track.id for track in config.tracks} == special_ids
    by_declaration = {track.id: track for track in config.tracks}
    for track_id in pending_ids:
        assert not by_declaration[track_id].enabled
        assert by_declaration[track_id].approval_status is SourceApprovalStatus.PENDING
    for track_id in approved_ids:
        assert by_declaration[track_id].enabled
        assert by_declaration[track_id].approval_status is SourceApprovalStatus.APPROVED
        assert by_declaration[track_id].approved_sha256 is not None
    assert all(track.render_once for track in config.tracks)
    assert [(entry.written, entry.spoken) for entry in config.pronunciations.entries] == [
        ("Hannah", "Haanah"),
        ("waveform", "wave-form"),
        ("waveforms", "wave-forms"),
    ]

    catalog = build_ordered_track_catalog(config, workspace_root)
    by_id = {track.id: track for track in catalog.tracks}
    assert special_ids < set(by_id)
    assert "chapter-003" in by_id
    assert by_id["chapter-003"].sequence == 7
    assert by_id["chapter-003"].enabled
    assert not by_id["opening-credits"].enabled
    assert catalog.tracks[-1].id == "closing-credits"
    assert len({track.id for track in catalog.tracks}) == len(catalog.tracks)
    assert len({track.sequence for track in catalog.tracks}) == len(catalog.tracks)
    assert catalog.select_track_ids(("chapter-003",))[0].id == "chapter-003"


def test_approved_handoff_hash_render_once_and_plan_bound_are_enforced(tmp_path):
    manuscript_chapters = tmp_path / "manuscript" / "chapters" / "part"
    manuscript_chapters.mkdir(parents=True)
    (manuscript_chapters / "part-001-one.md").write_text("placeholder", encoding="utf-8")
    handoff_path = tmp_path / "handoffs" / "opening.md"
    handoff_path.parent.mkdir()
    handoff_bytes = b"approved spoken source"
    handoff_path.write_bytes(handoff_bytes)

    parsed = parse_production_toml(VALID_TOML)
    approved = TrackDeclaration(
        id="opening-credits",
        kind=TrackKind.OPENING_CREDITS,
        sequence=1,
        source_path="handoffs/opening.md",
        source_section="spoken-title",
        approved_sha256=sha256_bytes(handoff_bytes),
        render_once=True,
        enabled=True,
        approval_status=SourceApprovalStatus.APPROVED,
    )
    pending = TrackDeclaration(
        id="closing-credits",
        kind=TrackKind.CLOSING_CREDITS,
        sequence=100,
        source_path="handoffs/closing.md",
        source_section=None,
        approved_sha256=None,
        render_once=True,
        enabled=False,
        approval_status=SourceApprovalStatus.PENDING,
    )
    config = replace(
        parsed,
        manuscript_root="manuscript",
        delivery_root="delivery",
        max_tracks_per_plan=1,
        track_kind_overrides=(),
        tracks=(approved, pending),
    )

    catalog = build_ordered_track_catalog(config, tmp_path)
    by_id = {track.id: track for track in catalog.tracks}
    assert by_id["opening-credits"].source_section == "spoken-title"
    assert by_id["opening-credits"].verified_source_sha256 == sha256_bytes(handoff_bytes)
    assert by_id["chapter-001"].approval_status is SourceApprovalStatus.NOT_REQUIRED

    with pytest.raises(InputError, match="exceeds max_tracks_per_plan"):
        catalog.select_track_ids(("opening-credits", "chapter-001"))
    with pytest.raises(InputError, match="disabled pending"):
        catalog.select_track_ids(("closing-credits",))
    with pytest.raises(InputError, match="duplicate Track IDs"):
        catalog.select_track_ids(("chapter-001", "chapter-001"))

    wrong_hash = replace(approved, approved_sha256="0" * 64)
    with pytest.raises(InputError, match="Approved source hash mismatch"):
        build_ordered_track_catalog(replace(config, tracks=(wrong_hash, pending)), tmp_path)

    pending_but_enabled = replace(pending, enabled=True)
    with pytest.raises(InputError, match="Pending Special Track.*must be disabled"):
        build_ordered_track_catalog(
            replace(config, tracks=(approved, pending_but_enabled)), tmp_path
        )

    not_render_once = replace(approved, render_once=False)
    with pytest.raises(InputError, match="Special Track.*must be Render_Once"):
        build_ordered_track_catalog(
            replace(config, tracks=(not_render_once, pending)), tmp_path
        )


def test_waveform_lexicon_hyphenates_without_touching_neighbor_words():
    workspace_root = Path(__file__).resolve().parents[2]
    config = load_production_config(workspace_root / ".audiobook" / "config" / "production.toml")
    source = (
        "No arbitrary waveform generator had been borrowed from the test building. "
        "The two waveforms had not met cleanly."
    )
    spoken, applied = config.pronunciations.apply(source)

    assert applied == ("waveform", "waveforms")
    assert "waveform" not in spoken
    assert "wave-form generator" in spoken
    assert "wave-forms had" in spoken
    assert normalized_tokens("wave-form") == ("wave", "form")
    assert normalized_tokens("wave-forms") == ("wave", "forms")
