"""Deterministic generated checks for audiobook production correctness Property 1."""

from __future__ import annotations

import random
import socket
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from frontier_audiobook import narrate
from frontier_audiobook.errors import InputError
from frontier_audiobook.manuscript import markdown_to_spoken, read_chapter
from frontier_audiobook.narrate import segment_spoken_text
from frontier_audiobook.production import (
    ProductionSelectors,
    create_production_plan,
    load_production_plan,
    snapshot_track_source,
)
from frontier_audiobook.production_config import (
    SourceApprovalStatus,
    build_ordered_track_catalog,
    parse_production_toml,
    print_production_toml,
    resolve_effective_track_config,
)
from frontier_audiobook.production_models import (
    SourceKind,
    TrackKind,
    canonical_sha256,
)
from frontier_audiobook.util import (
    normalize_lf_nfc,
    read_bytes_nofollow,
    sha256_bytes,
    sha256_text,
)
from frontier_audiobook.verify import normalized_tokens


PROPERTY_TAG = (
    "Feature: audiobook-production-workflow, Property 1: "
    "Effective configuration and source planning are deterministic"
)
PROPERTY_SEED = 0xA0D10B00
GENERATED_CASES = 128

# **Validates: Requirements 2.1, 2.3, 2.4, 2.12, 2.13, 2.14, 2.16,
# 2.17, 3.5, 3.6, 3.7, 17.2**

_WORDS = (
    "amber",
    "bravo",
    "cinder",
    "delta",
    "ember",
    "fable",
    "glimmer",
    "harbor",
    "island",
    "jovial",
    "kindle",
    "lumen",
    "meadow",
    "nectar",
    "orbit",
    "prairie",
    "quartz",
    "raven",
    "silver",
    "timber",
    "umber",
    "velvet",
    "willow",
    "xenon",
    "yonder",
    "zephyr",
)


@dataclass(frozen=True, slots=True)
class _GeneratedCase:
    default_voice: str
    default_region: str
    default_target: int
    kind_voice: str | None
    kind_region: str | None
    kind_target: int | None
    exact_voice: str | None
    exact_region: str | None
    exact_target: int | None
    exact_channels: int
    special_profile: str
    word_shift: int
    mutation: str
    mutation_index: int

    @property
    def effective_target(self) -> int:
        if self.exact_target is not None:
            return self.exact_target
        if self.kind_target is not None:
            return self.kind_target
        return self.default_target


@pytest.fixture(autouse=True)
def deny_network_aws_and_render(monkeypatch):
    """Make every Property 1 case fail if planning crosses a paid/external boundary."""

    def blocked(*_args, **_kwargs):
        raise AssertionError("Property 1 planning must remain offline and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")


def _generated_case(rng: random.Random, case_index: int) -> _GeneratedCase:
    return _GeneratedCase(
        default_voice=f"default-voice-{case_index}",
        default_region=f"default-region-{rng.randrange(4)}",
        default_target=rng.randint(5, 9),
        kind_voice=(f"kind-voice-{case_index}" if rng.getrandbits(1) else None),
        kind_region=(f"kind-region-{rng.randrange(4)}" if rng.getrandbits(1) else None),
        kind_target=(rng.randint(5, 9) if rng.getrandbits(1) else None),
        exact_voice=(f"exact-voice-{case_index}" if rng.getrandbits(1) else None),
        exact_region=(f"exact-region-{rng.randrange(4)}" if rng.getrandbits(1) else None),
        exact_target=(rng.randint(5, 9) if rng.getrandbits(1) else None),
        exact_channels=rng.randint(1, 2),
        special_profile=f"special-profile-{case_index}",
        word_shift=rng.randrange(len(_WORDS)),
        mutation="insert" if rng.getrandbits(1) else "edit",
        mutation_index=rng.randint(2, 5),
    )


def _sentence(lead_index: int, word_count: int, shift: int) -> str:
    words = [_WORDS[lead_index % len(_WORDS)]]
    words.extend(
        _WORDS[(shift + lead_index + offset) % len(_WORDS)]
        for offset in range(1, word_count)
    )
    return f"{' '.join(words)}."


def _chapter_relative(chapter: int) -> str:
    return (
        "manuscript/chapters/discovery/"
        f"discovery-{chapter:03d}-generated-chapter.md"
    )


def _write_chapter(workspace: Path, chapter: int, sentences: tuple[str, ...]) -> Path:
    path = workspace / _chapter_relative(chapter)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = " ".join(sentences)
    path.write_text(
        "\n".join(
            (
                "---",
                "movement: discovery",
                f"chapter: {chapter}",
                'title: "Generated Chapter"',
                "pov_id: generated-pov",
                "timeline_id: generated-timeline",
                "motif_events: none",
                "hook: generated-hook",
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


def _write_handoff(workspace: Path, approved_body: str) -> Path:
    path = workspace / "handoffs" / "opening.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(
        (
            "# Written Front Matter\n\n"
            "## Approved Spoken\n\n"
            f"{approved_body}\n\n"
            "## Written Layout Only\n\n"
            "This private layout section is not approved for narration.\n"
        ).encode("utf-8")
    )
    return path


def _append_optional_assignment(lines: list[str], name: str, value: object | None) -> None:
    if value is None:
        return
    if isinstance(value, str):
        lines.append(f'{name} = "{value}"')
    else:
        lines.append(f"{name} = {value}")


def _write_config(workspace: Path, case: _GeneratedCase) -> Path:
    handoff_sha256 = sha256_bytes(read_bytes_nofollow(workspace / "handoffs" / "opening.md"))
    lines = [
        "schema_version = 1",
        'book_id = "generated-book"',
        'manuscript_root = "manuscript"',
        'build_root = "audiobook-studio/build/production"',
        'delivery_root = "audiobook-studio/dist/audiobook"',
        "max_tracks_per_plan = 8",
        "",
        "[defaults]",
        f'voice = "{case.default_voice}"',
        'model_id = "amazon.nova-2-sonic-v1:0"',
        f'region = "{case.default_region}"',
        'profile_label = "generated-profile"',
        f"target_segment_words = {case.default_target}",
        'fidelity_policy = "exact"',
        'normalization = "frontier-word-sequence-v1"',
        'output_template = "{sequence:03d}-{track_slug}-{voice}.wav"',
        "",
        "[defaults.audio]",
        "sample_rate_hz = 24000",
        "sample_size_bits = 16",
        "channels = 1",
        "",
        "[estimate]",
        "rate_max_age_hours = 24",
        "preflight_max_age_hours = 24",
        "input_speech_tokens_per_call = 0",
        "input_text_tokens_per_call = 8192",
        "output_speech_tokens_per_call = 8192",
        "output_text_tokens_per_call = 8192",
        "",
        "[track_kinds.chapter]",
    ]
    _append_optional_assignment(lines, "voice", case.kind_voice)
    _append_optional_assignment(lines, "region", case.kind_region)
    _append_optional_assignment(lines, "target_segment_words", case.kind_target)
    lines.extend(
        (
            "",
            "[[tracks]]",
            'id = "opening-credits"',
            'kind = "opening_credits"',
            "sequence = 1",
            'source_path = "handoffs/opening.md"',
            'source_section = "approved-spoken"',
            f'approved_sha256 = "{handoff_sha256}"',
            "enabled = true",
            'approval_status = "approved"',
            "render_once = true",
            "",
            "[tracks.override]",
            f'profile_label = "{case.special_profile}"',
            "",
            "[[tracks]]",
            'id = "chapter-001"',
            'kind = "chapter"',
            "sequence = 2",
            f'source_path = "{_chapter_relative(1)}"',
            "enabled = true",
            'approval_status = "not-required"',
            "render_once = false",
            "",
            "[tracks.override]",
        )
    )
    _append_optional_assignment(lines, "voice", case.exact_voice)
    _append_optional_assignment(lines, "region", case.exact_region)
    _append_optional_assignment(lines, "target_segment_words", case.exact_target)
    lines.extend(
        (
            "",
            "[tracks.override.audio]",
            f"channels = {case.exact_channels}",
            "",
            "[[tracks]]",
            'id = "closing-credits"',
            'kind = "closing_credits"',
            "sequence = 100",
            'source_path = "handoffs/closing.md"',
            "enabled = false",
            'approval_status = "pending"',
            "render_once = true",
            "",
            "[tracks.override]",
        )
    )
    config_path = workspace / "audiobook-studio" / "config" / "production.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return config_path


def _write_workspace(
    workspace: Path,
    case: _GeneratedCase,
) -> tuple[Path, dict[int, tuple[str, ...]], str]:
    chapter_sentences: dict[int, tuple[str, ...]] = {}
    for chapter in (1, 2, 3):
        sentences = tuple(
            _sentence(chapter * 8 + ordinal, case.effective_target, case.word_shift)
            for ordinal in range(8)
        )
        chapter_sentences[chapter] = sentences
        _write_chapter(workspace, chapter, sentences)
    special_body = " ".join(
        _sentence(ordinal + 20, case.default_target, case.word_shift)
        for ordinal in range(2)
    )
    _write_handoff(workspace, special_body)
    return _write_config(workspace, case), chapter_sentences, special_body


def _winning_value_and_layer(
    default: object,
    kind: object | None,
    exact: object | None,
    *,
    kind_layer: str = "track-kind:chapter",
    exact_layer: str = "exact-track:chapter-001",
) -> tuple[object, str]:
    if exact is not None:
        return exact, exact_layer
    if kind is not None:
        return kind, kind_layer
    return default, "global-defaults"


def _assert_snapshot_derivation(
    snapshot,
    *,
    source_path: Path,
    normalized_body: str,
    track,
    expected_source_kind: SourceKind,
) -> None:
    effective = track.effective_config
    spoken = markdown_to_spoken(normalized_body, track.id)
    spoken_tokens = normalized_tokens(spoken, effective.normalization)
    expected_segments = segment_spoken_text(
        spoken,
        max_words=effective.target_segment_words,
    )
    reproduced_tokens = tuple(
        token
        for segment in expected_segments
        for token in normalized_tokens(segment.text, effective.normalization)
    )

    assert reproduced_tokens == spoken_tokens
    assert snapshot.track_id == track.id
    assert snapshot.source_kind is expected_source_kind
    assert snapshot.raw_sha256 == sha256_bytes(read_bytes_nofollow(source_path))
    assert snapshot.normalized_body_sha256 == sha256_text(normalize_lf_nfc(normalized_body))
    assert snapshot.spoken_sha256 == sha256_text(normalize_lf_nfc(spoken))
    assert snapshot.normalized_word_count == len(normalized_body.split())
    assert snapshot.spoken_token_count == len(spoken_tokens)
    assert snapshot.segment_count == len(expected_segments)
    assert sum(item.spoken_token_count for item in snapshot.segments) == len(spoken_tokens)

    token_cursor = 0
    for ordinal, (actual, expected) in enumerate(
        zip(snapshot.segments, expected_segments, strict=True),
        start=1,
    ):
        expected_tokens = normalized_tokens(expected.text, effective.normalization)
        canonical_text = " ".join(normalize_lf_nfc(expected.text).split())
        assert actual.segment_id == f"segment-{ordinal:04d}"
        assert actual.ordinal == ordinal
        assert actual.paragraph_index == expected.paragraph_index
        assert actual.start_token_index == token_cursor
        assert actual.end_token_index == token_cursor + len(expected_tokens)
        assert actual.text_sha256 == sha256_text(canonical_text)
        assert actual.normalized_tokens_sha256 == canonical_sha256(expected_tokens)
        assert actual.spoken_token_count == len(expected_tokens)
        assert actual.narration_only_punctuation is expected.narration_only_punctuation
        assert len(actual.render_config_sha256) == 64
        assert len(actual.render_identity_sha256) == 64
        token_cursor += len(expected_tokens)
    assert token_cursor == len(spoken_tokens)


def _assert_local_mutation_uses_bounded_context(
    original,
    changed,
    original_sentences: tuple[str, ...],
    *,
    mutation: str,
    mutation_index: int,
) -> None:
    assert original.raw_sha256 != changed.raw_sha256
    assert original.spoken_sha256 != changed.spoken_sha256
    assert original.render_context_radius == changed.render_context_radius == 1

    original_by_text = {item.text_sha256: item for item in original.segments}
    changed_by_text = {item.text_sha256: item for item in changed.segments}
    sentence_hashes = tuple(sha256_text(sentence) for sentence in original_sentences)

    if mutation == "insert":
        locally_affected = {mutation_index - 1, mutation_index}
        absent = set()
    else:
        locally_affected = {mutation_index - 1, mutation_index + 1}
        absent = {mutation_index}

    for index, sentence_hash in enumerate(sentence_hashes):
        if index in absent:
            assert sentence_hash not in changed_by_text
            continue
        before = original_by_text[sentence_hash]
        after = changed_by_text[sentence_hash]
        if index in locally_affected:
            assert before.render_identity_sha256 != after.render_identity_sha256
        else:
            assert before.render_identity_sha256 == after.render_identity_sha256

    if mutation == "insert":
        # This segment is two positions from the insertion. Its ordinal and source
        # binding change, but its bounded render inputs remain exactly reusable.
        distant_shifted_hash = sentence_hashes[mutation_index + 1]
        before = original_by_text[distant_shifted_hash]
        after = changed_by_text[distant_shifted_hash]
        assert after.ordinal == before.ordinal + 1
        assert after.render_identity_sha256 == before.render_identity_sha256


def _run_generated_case(workspace: Path, case: _GeneratedCase) -> None:
    config_path, chapters, special_body = _write_workspace(workspace, case)
    raw_config = read_bytes_nofollow(config_path)
    config = parse_production_toml(raw_config, label=str(config_path))
    printed = print_production_toml(config)
    reparsed = parse_production_toml(printed, label="canonical generated production TOML")

    assert reparsed == config
    assert print_production_toml(reparsed) == printed

    catalog = build_ordered_track_catalog(config, workspace)
    assert build_ordered_track_catalog(reparsed, workspace) == catalog
    assert len({item.id for item in catalog.tracks}) == len(catalog.tracks)
    assert len({item.sequence for item in catalog.tracks}) == len(catalog.tracks)
    assert len({item.effective_config.output_path for item in catalog.tracks}) == len(
        catalog.tracks
    )

    by_id = {item.id: item for item in catalog.tracks}
    chapter = by_id["chapter-001"]
    opening = by_id["opening-credits"]
    special_tracks = tuple(item for item in catalog.tracks if item.kind is not TrackKind.CHAPTER)
    assert all(item.render_once for item in special_tracks)
    assert opening.enabled
    assert opening.approval_status is SourceApprovalStatus.APPROVED
    assert opening.verified_source_sha256 == sha256_bytes(
        read_bytes_nofollow(workspace / opening.source_path)
    )
    assert opening.approved_sha256 == opening.verified_source_sha256

    declaration = next(item for item in config.tracks if item.id == "chapter-001")
    resolved = resolve_effective_track_config(config, declaration)
    assert resolve_effective_track_config(config, declaration) == resolved
    assert chapter.effective_config == resolved

    expected_voice, voice_layer = _winning_value_and_layer(
        case.default_voice,
        case.kind_voice,
        case.exact_voice,
    )
    expected_region, region_layer = _winning_value_and_layer(
        case.default_region,
        case.kind_region,
        case.exact_region,
    )
    expected_target, target_layer = _winning_value_and_layer(
        case.default_target,
        case.kind_target,
        case.exact_target,
    )
    assert resolved.voice == expected_voice
    assert resolved.region == expected_region
    assert resolved.target_segment_words == expected_target
    assert resolved.audio_format.channels == case.exact_channels
    assert resolved.resolution_provenance["voice"] == voice_layer
    assert resolved.resolution_provenance["region"] == region_layer
    assert resolved.resolution_provenance["target_segment_words"] == target_layer
    assert resolved.resolution_provenance["audio.channels"] == "exact-track:chapter-001"
    assert resolved.resolution_provenance["model_id"] == "global-defaults"
    assert resolved.resolution_provenance["audio.sample_rate_hz"] == "global-defaults"
    assert opening.effective_config.profile_label == case.special_profile
    assert (
        opening.effective_config.resolution_provenance["profile_label"]
        == "exact-track:opening-credits"
    )

    wrong_digest = "0" * 64 if opening.approved_sha256 != "0" * 64 else "1" * 64
    bad_config = replace(
        config,
        tracks=tuple(
            replace(item, approved_sha256=wrong_digest)
            if item.id == "opening-credits"
            else item
            for item in config.tracks
        ),
    )
    with pytest.raises(InputError, match="Approved source hash mismatch"):
        build_ordered_track_catalog(bad_config, workspace)

    chapter_snapshot = snapshot_track_source(config, chapter, workspace)
    assert chapter_snapshot == snapshot_track_source(config, chapter, workspace)
    chapter_source = read_chapter(workspace / chapter.source_path, enforce_declared_words=False)
    _assert_snapshot_derivation(
        chapter_snapshot,
        source_path=workspace / chapter.source_path,
        normalized_body=chapter_source.body,
        track=chapter,
        expected_source_kind=SourceKind.CHAPTER,
    )

    opening_snapshot = snapshot_track_source(config, opening, workspace)
    assert opening_snapshot == snapshot_track_source(config, opening, workspace)
    _assert_snapshot_derivation(
        opening_snapshot,
        source_path=workspace / opening.source_path,
        normalized_body=special_body,
        track=opening,
        expected_source_kind=SourceKind.APPROVED_SPECIAL_TRACK,
    )

    mutation_sentence = _sentence(24, case.effective_target, case.word_shift + 7)
    if case.mutation == "insert":
        changed_sentences = (
            *chapters[1][: case.mutation_index],
            mutation_sentence,
            *chapters[1][case.mutation_index :],
        )
    else:
        changed_sentences = (
            *chapters[1][: case.mutation_index],
            mutation_sentence,
            *chapters[1][case.mutation_index + 1 :],
        )
    _write_chapter(workspace, 1, changed_sentences)
    changed_catalog = build_ordered_track_catalog(config, workspace)
    changed_chapter = next(item for item in changed_catalog.tracks if item.id == "chapter-001")
    changed_snapshot = snapshot_track_source(config, changed_chapter, workspace)
    _assert_local_mutation_uses_bounded_context(
        chapter_snapshot,
        changed_snapshot,
        chapters[1],
        mutation=case.mutation,
        mutation_index=case.mutation_index,
    )


def test_property_1_generated_configuration_catalog_and_source_planning(tmp_path):
    """Feature: audiobook-production-workflow, Property 1: Effective configuration and source planning are deterministic"""

    print(f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; cases={GENERATED_CASES}")
    rng = random.Random(PROPERTY_SEED)
    for case_index in range(GENERATED_CASES):
        case = _generated_case(rng, case_index)
        try:
            _run_generated_case(tmp_path / f"case-{case_index:03d}", case)
        except Exception as exc:
            exc.add_note(
                f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; case={case_index}; input={case!r}"
            )
            raise


_SELECTOR_CASES = (
    ("chapter", {"chapters": [2]}, "chapter-002", 2),
    ("chapter-list", {"chapters": [3, 1]}, "chapter-003", 3),
    ("chapter-range", {"chapter_ranges": ["1:3"]}, "chapter-002", 2),
    ("special-track", {"tracks": ["opening-credits"]}, "opening-credits", None),
)


@pytest.mark.parametrize(
    ("selector_kind", "selector_kwargs", "changed_track_id", "changed_chapter"),
    _SELECTOR_CASES,
    ids=tuple(item[0] for item in _SELECTOR_CASES),
)
def test_property_1_generic_selector_plans_recompute_current_hashes(
    tmp_path,
    selector_kind,
    selector_kwargs,
    changed_track_id,
    changed_chapter,
):
    """Feature: audiobook-production-workflow, Property 1: Effective configuration and source planning are deterministic"""

    case = _generated_case(random.Random(PROPERTY_SEED ^ 0x51EC70), 999)
    config_path, chapters, special_body = _write_workspace(tmp_path, case)
    selectors = ProductionSelectors.from_cli(**selector_kwargs)
    before_path = create_production_plan(
        config_path,
        selectors,
        plan_id=f"{selector_kind}-before-plan",
        workspace_root=tmp_path,
        created_at_utc="2026-09-12T00:00:00Z",
    )
    before = load_production_plan(before_path)

    if changed_chapter is None:
        updated_special_body = " ".join(
            (
                special_body,
                _sentence(25, case.default_target, case.word_shift + 11),
            )
        )
        _write_handoff(tmp_path, updated_special_body)
        config_path = _write_config(tmp_path, case)
    else:
        _write_chapter(
            tmp_path,
            changed_chapter,
            (
                *chapters[changed_chapter],
                _sentence(25, case.effective_target, case.word_shift + 11),
            ),
        )

    after_path = create_production_plan(
        config_path,
        selectors,
        plan_id=f"{selector_kind}-after-plan",
        workspace_root=tmp_path,
        created_at_utc="2026-09-12T00:01:00Z",
    )
    after = load_production_plan(after_path)

    assert tuple(item.track_id for item in after.tracks) == tuple(
        item.track_id for item in before.tracks
    )
    before_by_id = {item.track_id: item for item in before.tracks}
    after_by_id = {item.track_id: item for item in after.tracks}
    assert before_by_id[changed_track_id].source.raw_sha256 != after_by_id[
        changed_track_id
    ].source.raw_sha256

    for track_plan in after.tracks:
        current_source = read_bytes_nofollow(tmp_path / track_plan.source.source_path)
        assert track_plan.source.raw_sha256 == sha256_bytes(current_source)
        if track_plan.track_id != changed_track_id:
            assert (
                track_plan.source.raw_sha256
                == before_by_id[track_plan.track_id].source.raw_sha256
            )
