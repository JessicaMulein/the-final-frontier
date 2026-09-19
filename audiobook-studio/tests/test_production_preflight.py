from __future__ import annotations

import base64
import json
import random
import socket
import wave
from io import BytesIO
from pathlib import Path

import pytest

from frontier_audiobook import narrate
from frontier_audiobook.production import ProductionSelectors, create_production_plan, load_production_plan
from frontier_audiobook.production_config import build_ordered_track_catalog, parse_production_toml
from frontier_audiobook.production_models import DestinationState
from frontier_audiobook.production_preflight import (
    FileAttribution,
    InventoryKind,
    PriorArtifactState,
    ReadOnlyLegacyAdapter,
    ReuseDisposition,
    ValidatedArtifactBinding,
    bind_targeted_check_result,
    build_protected_inventory,
    classify_destination,
    classify_track_reuse,
    derive_workflow_write_allowlist,
    evaluate_isolation,
    inspect_local_filesystems,
    run_local_preflight,
)
from frontier_audiobook.util import read_bytes_nofollow, sha256_bytes, workspace_relative


SENTENCES = (
    "Alpha one two three four.",
    "Bravo one two three four.",
    "Charlie one two three four.",
    "Delta one two three four.",
    "Echo one two three four.",
)


@pytest.fixture(autouse=True)
def deny_external_access_and_render(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("Task 2.1 tests must stay local and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")


def _chapter_path(workspace: Path, chapter: int) -> Path:
    names = {
        1: "discovery-part-001-first-contact.md",
        2: "discovery-part-002-second-signal.md",
        3: "discovery-part-003-third-signal.md",
    }
    return workspace / "The Final Frontier Novel" / "chapters" / "discovery-part" / names[chapter]


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
                'title: "Test Chapter"',
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


def _write_workspace(workspace: Path, chapters: tuple[int, ...] = (1, 2, 3)) -> Path:
    for chapter in chapters:
        _write_chapter(workspace, chapter, SENTENCES)
    config_path = workspace / "audiobook-studio" / "config" / "production.toml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        '''schema_version = 1
book_id = "the-final-frontier"
manuscript_root = "The Final Frontier Novel"
build_root = "audiobook-studio/build/production"
delivery_root = "audiobook-studio/dist/audiobook"
max_tracks_per_plan = 16
tracks = []

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
''',
        encoding="utf-8",
    )
    return config_path


def _config_catalog(workspace: Path, config_path: Path):
    config = parse_production_toml(read_bytes_nofollow(config_path), label=str(config_path))
    return config, build_ordered_track_catalog(config, workspace)


def _create_plan(workspace: Path, chapter: int, plan_id: str):
    config_path = workspace / "audiobook-studio" / "config" / "production.toml"
    path = create_production_plan(
        config_path,
        ProductionSelectors.from_cli(chapters=[chapter]),
        plan_id=plan_id,
        workspace_root=workspace,
        created_at_utc="2026-09-14T00:00:00Z",
    )
    return load_production_plan(path)


def _wav_bytes(lpcm: bytes) -> bytes:
    output = BytesIO()
    with wave.open(output, "wb") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(24000)
        handle.writeframes(lpcm)
    return output.getvalue()


def _output_events(transcript: str, lpcm: bytes) -> tuple[dict[str, object], ...]:
    identity = {
        "sessionId": "session-1",
        "promptName": "prompt-1",
        "completionId": "completion-1",
    }
    return (
        {"completionStart": dict(identity)},
        {
            "contentStart": {
                **identity,
                "contentId": "audio-1",
                "role": "ASSISTANT",
                "type": "AUDIO",
                "audioOutputConfiguration": {
                    "mediaType": "audio/lpcm",
                    "sampleRateHertz": 24000,
                    "sampleSizeBits": 16,
                    "encoding": "base64",
                    "channelCount": 1,
                },
            }
        },
        {
            "audioOutput": {
                **identity,
                "contentId": "audio-1",
                "content": base64.b64encode(lpcm).decode("ascii"),
            }
        },
        {
            "contentEnd": {
                **identity,
                "contentId": "audio-1",
                "stopReason": "END_TURN",
                "type": "AUDIO",
            }
        },
        {
            "contentStart": {
                **identity,
                "contentId": "text-1",
                "role": "ASSISTANT",
                "type": "TEXT",
                "additionalModelFields": '{"generationStage":"FINAL"}',
                "textOutputConfiguration": {"mediaType": "text/plain"},
            }
        },
        {
            "textOutput": {
                **identity,
                "contentId": "text-1",
                "content": transcript,
            }
        },
        {
            "contentEnd": {
                **identity,
                "contentId": "text-1",
                "stopReason": "END_TURN",
                "type": "TEXT",
            }
        },
        {
            "usageEvent": {
                **identity,
                "totalInputTokens": 1,
                "totalOutputTokens": 1,
                "totalTokens": 2,
                "details": {},
            }
        },
        {"completionEnd": {**identity, "stopReason": "END_TURN"}},
    )


def _write_reuse_manifest(
    workspace: Path,
    track_plan,
    texts: tuple[str, ...],
    *,
    included_ordinals: set[int] | None = None,
) -> tuple[Path, tuple[dict[str, object], ...]]:
    root = workspace / "audiobook-studio" / "build" / "narration" / "chapter-001-tiffany"
    for directory in (root / "segments", root / "transcripts", root / "events"):
        directory.mkdir(parents=True, exist_ok=True)
    included = included_ordinals or set(range(1, len(track_plan.source.segments) + 1))
    entries: list[dict[str, object]] = []
    all_entries: list[dict[str, object]] = []
    for snapshot, text in zip(track_plan.source.segments, texts, strict=True):
        lpcm = b"\0\0" * (1200 + snapshot.ordinal)
        stem = f"{snapshot.ordinal:04d}-{snapshot.text_sha256}"
        audio_path = root / "segments" / f"{stem}.wav"
        transcript_path = root / "transcripts" / f"{stem}.txt"
        event_path = root / "events" / f"{stem}.jsonl"
        audio = _wav_bytes(lpcm)
        transcript = (text + "\n").encode("utf-8")
        event_bytes = "".join(
            json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"
            for event in _output_events(text, lpcm)
        ).encode("utf-8")
        audio_path.write_bytes(audio)
        transcript_path.write_bytes(transcript)
        event_path.write_bytes(event_bytes)
        entry = {
            "segment_id": snapshot.segment_id,
            "status": "narrated",
            "text_sha256": snapshot.text_sha256,
            "render_identity_sha256": snapshot.render_identity_sha256,
            "render_config_sha256": snapshot.render_config_sha256,
            "exact_transcript_match": True,
            "coverage_ratio": 1.0,
            "mid_sentence_partial_turns": 0,
            "audio_path": workspace_relative(workspace, audio_path),
            "audio_sha256": sha256_bytes(audio),
            "transcript_path": workspace_relative(workspace, transcript_path),
            "transcript_sha256": sha256_bytes(transcript),
            "event_journal_path": workspace_relative(workspace, event_path),
            "event_journal_sha256": sha256_bytes(event_bytes),
        }
        all_entries.append(entry)
        if snapshot.ordinal in included:
            entries.append(entry)

    assembled = _wav_bytes(b"\0\0" * 5000)
    assembled_path = root / "chapter-001-tiffany.wav"
    assembled_path.write_bytes(assembled)
    manifest = {
        "chapter": 1,
        "source_sha256": track_plan.source.raw_sha256,
        "spoken_sha256": track_plan.source.spoken_sha256,
        "render_config_sha256": track_plan.source.segments[0].render_config_sha256,
        "active_render_identity_sha256s": [
            item.render_identity_sha256 for item in track_plan.source.segments
        ],
        "chapter_audio_path": workspace_relative(workspace, assembled_path),
        "chapter_audio_sha256": sha256_bytes(assembled),
        "segments": entries,
        "carried_over_segments": [],
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
    return manifest_path, tuple(all_entries)


def test_reuse_uses_bounded_render_identity_and_blocks_invalidation_fan_out(tmp_path):
    config_path = _write_workspace(tmp_path)
    original = _create_plan(tmp_path, 1, "original-plan").tracks[0]
    manifest_path, _entries = _write_reuse_manifest(tmp_path, original, SENTENCES)
    config, catalog = _config_catalog(tmp_path, config_path)
    catalog_track = next(item for item in catalog.tracks if item.id == "chapter-001")

    current = classify_track_reuse(
        tmp_path,
        original,
        config,
        catalog_track,
        (manifest_path,),
        comparison_call_ceiling=0,
    )
    assert current.prior_state is PriorArtifactState.REUSABLE
    assert current.disposition is ReuseDisposition.CURRENT_REUSABLE
    assert current.maximum_new_calls == 0
    assert current.assembled_audio is not None

    inserted = "Inserted one two three four."
    _write_chapter(tmp_path, 1, (*SENTENCES[:2], inserted, *SENTENCES[2:]))
    changed_plan = _create_plan(tmp_path, 1, "changed-plan").tracks[0]
    config, catalog = _config_catalog(tmp_path, config_path)
    changed_catalog_track = next(item for item in catalog.tracks if item.id == "chapter-001")
    changed = classify_track_reuse(
        tmp_path,
        changed_plan,
        config,
        changed_catalog_track,
        (manifest_path,),
        comparison_call_ceiling=2,
    )

    assert changed.source_revision_changed is True
    assert changed.disposition is ReuseDisposition.STALE_RERENDER_REQUIRED
    assert changed.maximum_new_calls == 3
    assert len(changed.reusable_segment_ids) == 3
    assert len(changed.rerender_segment_ids) == 3
    assert changed.invalidation_fan_out_blocked is True
    assert "unexpected-invalidation-fan-out" in changed.blocking_categories
    original_by_hash = {item.text_sha256: item for item in original.source.segments}
    changed_by_hash = {item.text_sha256: item for item in changed_plan.source.segments}
    for sentence in (SENTENCES[0], SENTENCES[3], SENTENCES[4]):
        digest = sha256_bytes(sentence.encode("utf-8"))
        assert original_by_hash[digest].render_identity_sha256 == changed_by_hash[digest].render_identity_sha256


def test_exact_cache_miss_count_over_deterministic_generated_subsets(tmp_path):
    config_path = _write_workspace(tmp_path)
    track_plan = _create_plan(tmp_path, 1, "cache-count-plan").tracks[0]
    manifest_path, all_entries = _write_reuse_manifest(tmp_path, track_plan, SENTENCES)
    config, catalog = _config_catalog(tmp_path, config_path)
    catalog_track = next(item for item in catalog.tracks if item.id == "chapter-001")
    rng = random.Random(2101)

    for _case in range(100):
        included = {
            ordinal
            for ordinal in range(1, len(all_entries) + 1)
            if rng.choice((False, True))
        }
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["segments"] = [
            entry for ordinal, entry in enumerate(all_entries, start=1) if ordinal in included
        ]
        # Without the complete active set the assembled file is deliberately not
        # current, but reusable segments must still reduce paid calls exactly.
        if len(included) != len(all_entries):
            manifest["active_render_identity_sha256s"] = []
        manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")
        assessment = classify_track_reuse(
            tmp_path,
            track_plan,
            config,
            catalog_track,
            (manifest_path,),
        )
        assert assessment.maximum_new_calls == len(all_entries) - len(included)
        assert len(assessment.reusable_segment_ids) == len(included)
        assert assessment.maximum_new_calls <= track_plan.maximum_new_calls


def test_inventory_isolation_allowlist_and_legacy_observation_are_per_file_and_read_only(tmp_path):
    config_path = _write_workspace(tmp_path)
    plan = _create_plan(tmp_path, 1, "inventory-plan")
    config, _catalog = _config_catalog(tmp_path, config_path)
    manifest_path, _entries = _write_reuse_manifest(tmp_path, plan.tracks[0], SENTENCES)
    for relative in (
        ".kiro/specs/chapter-2-audio-proof/design.md",
        ".kiro/specs/chapter-3-audio-proof/design.md",
        ".kiro/specs/The-Final-Frontier-novel/requirements.md",
        "audiobook-studio/src/frontier_audiobook/runtime_marker.py",
        "audiobook-studio/requirements/dev.txt",
        "audiobook-studio/requirements/runtime.txt",
        "audiobook-studio/pyproject.toml",
        "audiobook-studio/uv.lock",
    ):
        path = tmp_path / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(relative, encoding="utf-8")
    proof = tmp_path / "voice-samples" / "chapter-1-tiffany-proof.wav"
    proof.parent.mkdir(parents=True, exist_ok=True)
    proof.write_bytes(b"proof-bytes")

    adapter = ReadOnlyLegacyAdapter(tmp_path)
    before = {
        item.path: read_bytes_nofollow(tmp_path / item.path)
        for item in adapter.observe()
    }
    assert manifest_path in adapter.manifest_paths(1)
    after = {
        item.path: read_bytes_nofollow(tmp_path / item.path)
        for item in adapter.observe()
    }
    assert after == before

    baseline = build_protected_inventory(tmp_path, config, plan, git_statuses={})
    kinds = {item.path: item.kind for item in baseline.files}
    assert kinds[workspace_relative(tmp_path, _chapter_path(tmp_path, 1))] is InventoryKind.SELECTED_SOURCE
    assert kinds[".kiro/specs/chapter-2-audio-proof/design.md"] is InventoryKind.HISTORICAL_SPEC
    assert kinds[".kiro/specs/The-Final-Frontier-novel/requirements.md"] is InventoryKind.GOVERNING_SPEC
    assert kinds["voice-samples/chapter-1-tiffany-proof.wav"] is InventoryKind.PRIOR_AUDIO
    assert all(item.attribution is FileAttribution.BASELINE for item in baseline.files)

    allowlist = derive_workflow_write_allowlist(config, plan)
    transaction_root = (
        f"audiobook-studio/build/production/the-final-frontier/transactions/"
        f"chapter-001/{plan.tracks[0].transaction_id}"
    )
    assert allowlist.contains(f"{transaction_root}/runtime/manifest.json")
    assert not allowlist.contains(workspace_relative(tmp_path, _chapter_path(tmp_path, 2)))

    _write_chapter(tmp_path, 2, (*SENTENCES, "Concurrent one two three four."))
    concurrent_snapshot = build_protected_inventory(tmp_path, config, plan, git_statuses={})
    concurrent = evaluate_isolation(baseline, concurrent_snapshot, allowlist)
    assert concurrent.passed is True
    assert concurrent.concurrent_manuscript_change_paths == (
        workspace_relative(tmp_path, _chapter_path(tmp_path, 2)),
    )
    assert concurrent.hard_protected_drift_paths == ()

    _write_chapter(tmp_path, 1, (*SENTENCES, "Selected one two three four."))
    drifted_snapshot = build_protected_inventory(tmp_path, config, plan, git_statuses={})
    drifted = evaluate_isolation(
        baseline,
        drifted_snapshot,
        allowlist,
        workflow_written_paths=(
            workspace_relative(tmp_path, _chapter_path(tmp_path, 2)),
            f"{transaction_root}/runtime/manifest.json",
        ),
    )
    assert drifted.passed is False
    assert workspace_relative(tmp_path, _chapter_path(tmp_path, 1)) in drifted.hard_protected_drift_paths
    assert drifted.workflow_writes_outside_allowlist == (
        workspace_relative(tmp_path, _chapter_path(tmp_path, 2)),
    )


def test_target_disk_destination_and_complete_local_preflight_are_bound_without_external_calls(tmp_path):
    config_path = _write_workspace(tmp_path)
    plan = _create_plan(tmp_path, 3, "local-preflight-plan")
    config, catalog = _config_catalog(tmp_path, config_path)
    result_path = tmp_path / "audiobook-studio" / "build" / "targeted" / "result.json"
    result_path.parent.mkdir(parents=True, exist_ok=True)
    result_path.write_text('{"passed":true}', encoding="utf-8")
    command_sha256 = sha256_bytes(b"pytest-targeted-command")
    targeted = bind_targeted_check_result(
        tmp_path,
        workspace_relative(tmp_path, result_path),
        command_sha256=command_sha256,
        return_code=0,
        aws_access_disabled=True,
        model_access_disabled=True,
    )
    assert targeted.passed is True
    assert targeted.result_sha256 == sha256_bytes(result_path.read_bytes())

    allowlist = derive_workflow_write_allowlist(config, plan)
    filesystem = inspect_local_filesystems(
        tmp_path,
        allowlist,
        required_free_bytes=0,
    )
    assert filesystem.disk_space_sufficient is True
    assert filesystem.same_filesystem_atomic_scopes is True

    source = tmp_path / "audiobook-studio" / "build" / "validated.wav"
    source.parent.mkdir(parents=True, exist_ok=True)
    source.write_bytes(b"validated-audio")
    expected = ValidatedArtifactBinding(
        path=workspace_relative(tmp_path, source),
        byte_count=source.stat().st_size,
        sha256=sha256_bytes(source.read_bytes()),
    )
    destination = plan.tracks[0].effective_config.output_path
    absent = classify_destination(
        tmp_path,
        plan.tracks[0].track_id,
        destination,
        expected_artifact=expected,
    )
    assert absent.state is DestinationState.ABSENT
    destination_path = tmp_path / destination
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_bytes(source.read_bytes())
    identical = classify_destination(
        tmp_path,
        plan.tracks[0].track_id,
        destination,
        expected_artifact=expected,
    )
    assert identical.state is DestinationState.ALREADY_IDENTICAL
    destination_path.write_bytes(b"conflicting-audio")
    conflicting = classify_destination(
        tmp_path,
        plan.tracks[0].track_id,
        destination,
        expected_artifact=expected,
    )
    assert conflicting.state is DestinationState.CONFLICTING
    destination_path.unlink()

    local = run_local_preflight(
        tmp_path,
        config,
        catalog,
        plan,
        targeted,
        required_free_bytes=0,
        git_statuses={},
    )
    assert local.passed is True
    assert local.blocking_categories == ()
    assert local.maximum_new_calls_by_track == (
        (plan.tracks[0].track_id, plan.tracks[0].source.segment_count),
    )
    assert local.maximum_new_calls_total == plan.tracks[0].source.segment_count
    assert local.track_reuse[0].prior_state is PriorArtifactState.ABSENT
    assert local.destinations[0].state is DestinationState.ABSENT


def _official_rate_fixture(
    *,
    retrieved_at_utc: str = "2026-09-14T11:00:00Z",
) -> dict[str, object]:
    rates = {
        "input_speech": "0.001",
        "input_text": "0.002",
        "output_speech": "0.003",
        "output_text": "0.004",
    }
    return {
        "schema_version": 1,
        "source_url": "https://aws.amazon.com/bedrock/pricing/",
        "offer_publication_date": "2026-09-14",
        "retrieved_at_utc": retrieved_at_utc,
        "effective_date": "2026-09-14",
        "offers": [
            {
                "model_id": "amazon.nova-2-sonic-v1:0",
                "region": "us-east-1",
                "purchase_option": "on-demand",
                "currency": "USD",
                "unit": "per-1k-tokens",
                "modality": modality,
                "rate_per_1k_tokens": rate,
            }
            for modality, rate in rates.items()
        ],
    }


def test_identity_projection_calls_each_unique_profile_once_and_retains_only_three_fields():
    from dataclasses import fields

    from frontier_audiobook.production_preflight import resolve_minimal_identity_evidence

    calls: list[str] = []

    def identity_call(profile: str):
        calls.append(profile)
        if profile == "unresolved-profile":
            raise RuntimeError("secret failure detail must not persist")
        return {
            "Account": "123456789012",
            "Arn": "arn:aws:iam::123456789012:user/private",
            "UserId": "PRIVATE-USER-ID",
        }

    evidence = resolve_minimal_identity_evidence(
        ("frontier-audiobook", "unresolved-profile", "frontier-audiobook"),
        identity_call,
        checked_at_utc="2026-09-14T12:00:00Z",
    )

    assert calls == ["frontier-audiobook", "unresolved-profile"]
    assert tuple(item.profile_label for item in evidence) == (
        "frontier-audiobook",
        "unresolved-profile",
    )
    assert tuple(item.resolved for item in evidence) == (True, False)
    assert {field.name for field in fields(evidence[0])} == {
        "profile_label",
        "resolved",
        "checked_at_utc",
    }
    assert "123456789012" not in repr(evidence)
    assert "PRIVATE-USER-ID" not in repr(evidence)
    assert "secret failure detail" not in repr(evidence)


def test_official_rate_parser_accepts_one_current_complete_exact_match():
    from frontier_audiobook.production_preflight import (
        OfficialRateTarget,
        parse_official_rate_document,
    )

    cards = parse_official_rate_document(
        json.dumps(_official_rate_fixture(), separators=(",", ":")),
        (OfficialRateTarget("amazon.nova-2-sonic-v1:0", "us-east-1"),),
        checked_at_utc="2026-09-14T12:00:00Z",
        max_age_hours=24,
    )

    assert len(cards) == 1
    card = cards[0]
    assert (card.model_id, card.region, card.purchase_option) == (
        "amazon.nova-2-sonic-v1:0",
        "us-east-1",
        "on-demand",
    )
    assert card.currency == "USD"
    assert card.unit == "per-1k-tokens"
    assert card.source_url == "https://aws.amazon.com/bedrock/pricing/"
    assert card.offer_publication_date == "2026-09-14"
    assert card.retrieved_at_utc == "2026-09-14T11:00:00Z"
    assert card.effective_date == "2026-09-14"
    assert tuple((item.modality, item.rate_per_1k_tokens) for item in card.rates) == (
        ("input_speech", "0.001"),
        ("input_text", "0.002"),
        ("output_speech", "0.003"),
        ("output_text", "0.004"),
    )


@pytest.mark.parametrize(
    ("case", "message"),
    (
        ("missing", "Missing official output_text rate"),
        ("duplicate", "Duplicate official input_text rates"),
        ("ambiguous", "Ambiguous official input_text rates"),
        ("stale", "stale"),
        ("wrong-currency", "currency"),
        ("wrong-unit", "unit"),
        ("wrong-model", "Missing official input_speech rate"),
    ),
)
def test_official_rate_parser_rejects_incomplete_ambiguous_or_invalid_matches(case, message):
    from frontier_audiobook.errors import InputError
    from frontier_audiobook.production_preflight import (
        OfficialRateTarget,
        parse_official_rate_document,
    )

    document = _official_rate_fixture()
    offers = document["offers"]
    assert isinstance(offers, list)
    if case == "missing":
        offers.pop()
    elif case in {"duplicate", "ambiguous"}:
        duplicate = dict(offers[1])
        if case == "ambiguous":
            duplicate["rate_per_1k_tokens"] = "0.999"
        offers.append(duplicate)
    elif case == "stale":
        document["retrieved_at_utc"] = "2026-09-13T11:59:59Z"
        document["offer_publication_date"] = "2026-09-13"
        document["effective_date"] = "2026-09-13"
    elif case == "wrong-currency":
        offers[0]["currency"] = "EUR"
    elif case == "wrong-unit":
        offers[0]["unit"] = "per-token"
    elif case == "wrong-model":
        for offer in offers:
            offer["model_id"] = "amazon.other-model-v1:0"

    with pytest.raises(InputError, match=message):
        parse_official_rate_document(
            json.dumps(document, separators=(",", ":")),
            (OfficialRateTarget("amazon.nova-2-sonic-v1:0", "us-east-1"),),
            checked_at_utc="2026-09-14T12:00:00Z",
            max_age_hours=24,
        )


def test_bounded_decimal_estimate_uses_only_task_2_1_cache_misses_and_sanitized_evidence(tmp_path):
    from dataclasses import fields
    from decimal import Decimal

    from frontier_audiobook.production_models import canonical_json_text
    from frontier_audiobook.production_preflight import run_bounded_identity_rate_preflight

    config_path = _write_workspace(tmp_path)
    plan = _create_plan(tmp_path, 1, "bounded-estimate-plan")
    manifest_path, all_entries = _write_reuse_manifest(
        tmp_path,
        plan.tracks[0],
        SENTENCES,
    )
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["segments"] = [all_entries[index] for index in (0, 2, 4)]
    manifest["active_render_identity_sha256s"] = []
    manifest_path.write_text(json.dumps(manifest, sort_keys=True), encoding="utf-8")

    config, catalog = _config_catalog(tmp_path, config_path)
    targeted_path = tmp_path / "audiobook-studio" / "build" / "targeted" / "task-2-2.json"
    targeted_path.parent.mkdir(parents=True, exist_ok=True)
    targeted_path.write_text('{"passed":true}', encoding="utf-8")
    targeted = bind_targeted_check_result(
        tmp_path,
        workspace_relative(tmp_path, targeted_path),
        command_sha256=sha256_bytes(b"task-2-2-targeted-command"),
        return_code=0,
        aws_access_disabled=True,
        model_access_disabled=True,
    )
    local = run_local_preflight(
        tmp_path,
        config,
        catalog,
        plan,
        targeted,
        required_free_bytes=0,
        git_statuses={},
    )
    assert local.passed is True
    assert local.maximum_new_calls_by_track == (("chapter-001", 2),)
    assert local.maximum_new_calls_total == 2

    identity_calls: list[str] = []

    def identity_call(profile: str):
        identity_calls.append(profile)
        return {
            "Account": "123456789012",
            "Arn": "arn:aws:iam::123456789012:role/private-role",
            "UserId": "PRIVATE-USER-ID",
            "Credentials": "DO-NOT-PERSIST",
        }

    completed = run_bounded_identity_rate_preflight(
        config,
        plan,
        local,
        identity_call=identity_call,
        official_rate_document=json.dumps(
            _official_rate_fixture(),
            separators=(",", ":"),
        ),
        checked_at_utc="2026-09-14T12:00:00Z",
    )

    assert completed.passed is True
    assert completed.blocking_categories == ()
    assert identity_calls == ["frontier-audiobook"]
    assert {field.name for field in fields(completed.identity_evidence[0])} == {
        "profile_label",
        "resolved",
        "checked_at_utc",
    }
    assert completed.estimate.maximum_new_calls_by_track == local.maximum_new_calls_by_track
    assert completed.estimate.maximum_new_calls_total == local.maximum_new_calls_total
    assert tuple(
        (item.modality, item.tokens)
        for item in completed.estimate.configured_tokens_per_call
    ) == (
        ("input_speech", 0),
        ("input_text", 8192),
        ("output_speech", 8192),
        ("output_text", 8192),
    )
    assert tuple(
        (item.modality, item.tokens)
        for item in completed.estimate.maximum_tokens_by_modality
    ) == (
        ("input_speech", 0),
        ("input_text", 16384),
        ("output_speech", 16384),
        ("output_text", 16384),
    )
    assert Decimal(completed.estimate.estimated_pre_tax_usd) == Decimal("0.147456")
    assert completed.estimate.tracks[0].estimated_pre_tax_usd == "0.147456"
    assert len(completed.estimate.assumptions) == 6
    assert len(completed.canonical_sha256) == 64

    serialized = canonical_json_text(completed)
    for forbidden in (
        "123456789012",
        "arn:aws",
        "PRIVATE-USER-ID",
        "DO-NOT-PERSIST",
        "Credentials",
    ):
        assert forbidden not in serialized
