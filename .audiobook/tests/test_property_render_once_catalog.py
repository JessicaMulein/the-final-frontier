from __future__ import annotations

import random
import socket
from collections import Counter
from dataclasses import replace
from pathlib import Path

import pytest

from frontier_audiobook.errors import InputError
from frontier_audiobook.production import (
    ProductionSelectors,
    resolve_production_selectors,
)
from frontier_audiobook.production_config import (
    SourceApprovalStatus,
    TrackDeclaration,
    build_ordered_track_catalog,
    load_production_config,
)
from frontier_audiobook.production_models import TrackKind
from frontier_audiobook.util import sha256_bytes


PROPERTY_SEED = 0x16C0FFEE
GENERATED_CASES = 128
_FRONT_MATTER_IDS = (
    "dedication",
    "epigraph",
    "narratable-front-matter",
    "preface",
)


@pytest.fixture(autouse=True)
def deny_external_access(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("Property 16 must remain offline and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")


def _tracked_base_config():
    workspace_root = Path(__file__).resolve().parents[2]
    return load_production_config(
        workspace_root / ".audiobook" / "config" / "production.toml"
    )


def _approved_special_track(
    *,
    case_root: Path,
    rng: random.Random,
    case_index: int,
    track_id: str,
    kind: TrackKind,
    sequence: int,
    source_section: str | None,
) -> tuple[TrackDeclaration, str]:
    source_path = f"handoffs/{track_id}.source"
    absolute_source = case_root / source_path
    absolute_source.parent.mkdir(parents=True, exist_ok=True)
    source_bytes = (
        case_index.to_bytes(2, "big")
        + sequence.to_bytes(2, "big")
        + rng.randbytes(48)
    )
    absolute_source.write_bytes(source_bytes)
    source_sha256 = sha256_bytes(source_bytes)
    return (
        TrackDeclaration(
            id=track_id,
            kind=kind,
            sequence=sequence,
            source_path=source_path,
            source_section=source_section,
            approved_sha256=source_sha256,
            render_once=True,
            enabled=True,
            approval_status=SourceApprovalStatus.APPROVED,
        ),
        source_sha256,
    )


# Feature: audiobook-production-workflow, Property 16: Render-once book tracks are catalog-unique
# **Validates: Requirements 2.14, 2.15, 2.16, 2.17**
def test_render_once_book_tracks_are_catalog_unique(tmp_path):
    """Feature: audiobook-production-workflow, Property 16: Render-once book tracks are catalog-unique."""

    assert GENERATED_CASES >= 100
    print(f"Property 16 seed={PROPERTY_SEED} cases={GENERATED_CASES}")
    rng = random.Random(PROPERTY_SEED)
    base_config = _tracked_base_config()
    observed_front_matter_combinations: set[tuple[str, ...]] = set()
    observed_chapter_counts: set[int] = set()

    for case_index in range(GENERATED_CASES):
        context = f"seed={PROPERTY_SEED}, case={case_index}"
        case_root = tmp_path / f"case-{case_index:03d}"
        chapter_root = case_root / "manuscript" / "chapters" / "part"
        chapter_root.mkdir(parents=True)

        chapter_count = 1 + case_index % 8
        chapter_numbers = tuple(
            sorted(rng.sample(range(1, 25), chapter_count))
        )
        observed_chapter_counts.add(chapter_count)
        for chapter_number in chapter_numbers:
            chapter_path = chapter_root / f"part-{chapter_number:03d}-fixture.md"
            chapter_path.write_bytes(b"")

        subset_mask = 1 + case_index % ((1 << len(_FRONT_MATTER_IDS)) - 1)
        front_matter_ids = tuple(
            track_id
            for bit, track_id in enumerate(_FRONT_MATTER_IDS)
            if subset_mask & (1 << bit)
        )
        observed_front_matter_combinations.add(front_matter_ids)

        prefix_specs = [
            ("opening-credits", TrackKind.OPENING_CREDITS, "spoken-title"),
            *(
                (track_id, TrackKind.FRONT_MATTER, track_id)
                for track_id in front_matter_ids
            ),
        ]
        declarations: list[TrackDeclaration] = []
        expected_handoff_hashes: dict[str, str] = {}
        for sequence, (track_id, kind, section) in enumerate(prefix_specs, start=1):
            declaration, source_sha256 = _approved_special_track(
                case_root=case_root,
                rng=rng,
                case_index=case_index,
                track_id=track_id,
                kind=kind,
                sequence=sequence,
                source_section=section if (case_index + sequence) % 2 else None,
            )
            declarations.append(declaration)
            expected_handoff_hashes[track_id] = source_sha256

        closing_sequence = len(prefix_specs) + max(chapter_numbers) + 1
        closing, closing_sha256 = _approved_special_track(
            case_root=case_root,
            rng=rng,
            case_index=case_index,
            track_id="closing-credits",
            kind=TrackKind.CLOSING_CREDITS,
            sequence=closing_sequence,
            source_section=None,
        )
        declarations.append(closing)
        expected_handoff_hashes[closing.id] = closing_sha256

        config = replace(
            base_config,
            manuscript_root="manuscript",
            build_root="build",
            delivery_root="delivery",
            max_tracks_per_plan=len(declarations) + len(chapter_numbers),
            track_kind_overrides=(),
            tracks=tuple(declarations),
        )
        catalog = build_ordered_track_catalog(config, case_root)
        catalog_ids = tuple(track.id for track in catalog.tracks)
        catalog_sequences = tuple(track.sequence for track in catalog.tracks)

        assert len(catalog.tracks) == len(declarations) + len(chapter_numbers), context
        assert len(catalog_ids) == len(set(catalog_ids)), context
        assert len(catalog_sequences) == len(set(catalog_sequences)), context
        assert catalog_sequences == tuple(sorted(catalog_sequences)), context

        configured_special_counts = Counter(track.id for track in declarations)
        catalog_special_counts = Counter(
            track.id for track in catalog.tracks if track.kind is not TrackKind.CHAPTER
        )
        assert catalog_special_counts == configured_special_counts, context
        assert all(count == 1 for count in catalog_special_counts.values()), context
        assert all(
            not track.render_once
            for track in catalog.tracks
            if track.kind is TrackKind.CHAPTER
        ), context

        for declaration in declarations:
            matches = [
                track for track in catalog.tracks if track.id == declaration.id
            ]
            assert len(matches) == 1, context
            catalog_track = matches[0]
            assert catalog_track.kind is declaration.kind, context
            assert catalog_track.sequence == declaration.sequence, context
            assert catalog_track.render_once is True, context
            assert catalog_track.source_path == declaration.source_path, context
            assert catalog_track.source_section == declaration.source_section, context
            assert (
                catalog_track.approved_sha256
                == catalog_track.verified_source_sha256
                == expected_handoff_hashes[declaration.id]
            ), context

        assert sum(
            track.kind is TrackKind.OPENING_CREDITS for track in catalog.tracks
        ) == 1, context
        assert sum(
            track.kind is TrackKind.FRONT_MATTER for track in catalog.tracks
        ) == len(front_matter_ids), context
        assert sum(
            track.kind is TrackKind.CLOSING_CREDITS for track in catalog.tracks
        ) == 1, context

        addressed_ids = [track.id for track in declarations]
        addressed_ids.append(f"chapter-{rng.choice(chapter_numbers):03d}")
        rng.shuffle(addressed_ids)
        selectors = ProductionSelectors.from_cli(tracks=addressed_ids)
        resolved = resolve_production_selectors(catalog, selectors)
        addressed_set = set(addressed_ids)
        expected_resolved_ids = tuple(
            track.id for track in catalog.tracks if track.id in addressed_set
        )
        assert tuple(track.id for track in resolved.tracks) == expected_resolved_ids, context
        assert Counter(track.id for track in resolved.tracks) == Counter(addressed_ids), context
        assert resolved.selectors == tuple(
            f"track:{track_id}" for track_id in addressed_ids
        ), context

        tampered_index = case_index % len(declarations)
        bound_track = declarations[tampered_index]
        bound_digest = expected_handoff_hashes[bound_track.id]
        replacement_prefix = "1" if bound_digest[0] == "0" else "0"
        wrong_digest = replacement_prefix + bound_digest[1:]
        tampered_declarations = tuple(
            replace(track, approved_sha256=wrong_digest)
            if track.id == bound_track.id
            else track
            for track in declarations
        )
        with pytest.raises(InputError, match="Approved source hash mismatch"):
            build_ordered_track_catalog(
                replace(config, tracks=tampered_declarations), case_root
            )

    assert observed_chapter_counts == set(range(1, 9))
    assert len(observed_front_matter_combinations) == 15
