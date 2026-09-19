"""Deterministic generated checks for audiobook production correctness Property 2."""

from __future__ import annotations

import random
import socket
from collections.abc import Mapping
from dataclasses import replace
from decimal import Decimal
from pathlib import Path

import pytest

from frontier_audiobook import narrate
from frontier_audiobook.errors import InputError
from frontier_audiobook.production import (
    ProductionSelectors,
    create_production_plan,
    load_production_plan,
)
from frontier_audiobook.production_config import (
    build_ordered_track_catalog,
    parse_production_toml,
)
from frontier_audiobook.production_models import (
    TOKEN_MODALITIES,
    AuthorizationDecision,
    DestinationState,
    FrozenBatchPlan,
    FrozenTrackPlan,
    PaidAuthorization,
    PreflightRecord,
    StrictRecordCodec,
    authorization_confirmation_sha256,
    canonical_json_bytes,
    canonical_sha256,
    record_to_data,
    seal_record,
)
from frontier_audiobook.production_preflight import (
    TargetedCheckBinding,
    bind_targeted_check_result,
    run_local_preflight,
)
from frontier_audiobook.util import (
    read_bytes_nofollow,
    sha256_bytes,
    sha256_text,
)


PROPERTY_TAG = (
    "Feature: audiobook-production-workflow, Property 2: "
    "Frozen plans and preflight scopes are immutable and bounded"
)
PROPERTY_SEED = 0xA0D10B02
GENERATED_CASES = 128

# **Validates: Requirements 1.8, 3.1, 3.2, 3.3, 3.4, 3.8, 3.9,
# 3.10, 3.11, 3.12, 4.1, 4.12, 4.13, 4.15, 6.3, 6.4, 6.5, 6.6**

_CHAPTER_COUNT = 8
_RENDER_CONTEXT_RADIUS = 1
_MODALITY_ENVELOPES = {
    "input_speech": 3,
    "input_text": 37,
    "output_speech": 41,
    "output_text": 11,
}
_OFFICIAL_RATES = {
    "input_speech": "0.003",
    "input_text": "0.007",
    "output_speech": "0.011",
    "output_text": "0.013",
}
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


@pytest.fixture(autouse=True)
def deny_network_aws_model_and_render(monkeypatch):
    """Fail immediately if a generated case crosses a paid or external boundary."""

    def blocked(*_args, **_kwargs):
        raise AssertionError("Property 2 must remain offline and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "offline-denied")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "offline-denied")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "offline-denied")


def _chapter_relative(chapter: int) -> str:
    return (
        "The Final Frontier Novel/chapters/discovery-part/"
        f"discovery-part-{chapter:03d}-generated-{chapter}.md"
    )


def _chapter_path(workspace: Path, chapter: int) -> Path:
    return workspace / _chapter_relative(chapter)


def _sentences(case_index: int, chapter: int, count: int) -> tuple[str, ...]:
    sentences: list[str] = []
    for sentence_index in range(count):
        start = (case_index * 3 + chapter * 7 + sentence_index * 5) % len(_WORDS)
        words = tuple(_WORDS[(start + offset) % len(_WORDS)] for offset in range(5))
        sentences.append(f"{' '.join(words)}.")
    assert len(set(sentences)) == len(sentences)
    return tuple(sentences)


def _write_chapter(
    workspace: Path,
    chapter: int,
    sentences: tuple[str, ...],
) -> Path:
    path = _chapter_path(workspace, chapter)
    path.parent.mkdir(parents=True, exist_ok=True)
    body = " ".join(sentences)
    path.write_text(
        "\n".join(
            (
                "---",
                "movement: discovery",
                f"chapter: {chapter}",
                'title: "Property Two Chapter"',
                "pov_id: property-two-pov",
                "timeline_id: property-two-timeline",
                "motif_events: none",
                "hook: property-two-hook",
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


def _write_config(workspace: Path, max_tracks_per_plan: int) -> Path:
    path = workspace / "audiobook-studio" / "config" / "production.toml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f'''schema_version = 1
book_id = "the-final-frontier"
manuscript_root = "The Final Frontier Novel"
build_root = "audiobook-studio/build/production"
delivery_root = "audiobook-studio/dist/audiobook"
max_tracks_per_plan = {max_tracks_per_plan}
tracks = []

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
input_speech_tokens_per_call = 3
input_text_tokens_per_call = 37
output_speech_tokens_per_call = 41
output_text_tokens_per_call = 11
''',
        encoding="utf-8",
    )
    return path


def _valid_selectors(
    rng: random.Random,
    case_index: int,
    maximum: int,
) -> tuple[ProductionSelectors, tuple[int, ...]]:
    mode = case_index % 4
    if mode == 0:
        chapter = rng.randint(1, _CHAPTER_COUNT)
        return ProductionSelectors.from_cli(chapters=[chapter]), (chapter,)
    if mode == 1:
        length = rng.randint(1, maximum)
        start = rng.randint(1, _CHAPTER_COUNT - length + 1)
        chapters = tuple(range(start, start + length))
        return (
            ProductionSelectors.from_cli(chapter_ranges=[f"{start}:{chapters[-1]}"]),
            chapters,
        )

    count = rng.randint(1, maximum)
    supplied = tuple(rng.sample(range(1, _CHAPTER_COUNT + 1), count))
    if mode == 2:
        return (
            ProductionSelectors.from_cli(
                tracks=[f"chapter-{chapter:03d}" for chapter in supplied]
            ),
            tuple(sorted(supplied)),
        )
    return ProductionSelectors.from_cli(chapters=supplied), tuple(sorted(supplied))


def _invalid_selectors(case_index: int, maximum: int) -> ProductionSelectors:
    mode = case_index % 5
    if mode == 0:
        return ProductionSelectors.from_cli()
    if mode == 1:
        return ProductionSelectors.from_cli(chapter_ranges=["2:1"])
    if mode == 2:
        return ProductionSelectors.from_cli(chapters=[1], tracks=["chapter-001"])
    if mode == 3:
        return ProductionSelectors.from_cli(chapters=[99])
    return ProductionSelectors.from_cli(chapter_ranges=[f"1:{maximum + 1}"])


def _different_digest(value: str) -> str:
    replacement = "0" if value[0] != "0" else "1"
    return replacement + value[1:]


def _canonical_decimal(value: Decimal) -> str:
    assert value.is_finite() and value >= 0
    return format(value, "f")


def _estimate(total_calls: int, rates: Mapping[str, str]) -> str:
    value = sum(
        (
            Decimal(total_calls * _MODALITY_ENVELOPES[modality])
            * Decimal(rates[modality])
            / Decimal(1000)
            for modality in TOKEN_MODALITIES
        ),
        start=Decimal("0"),
    )
    return _canonical_decimal(value)


def _estimate_inputs(
    plan: FrozenBatchPlan,
    calls: Mapping[str, int],
) -> dict[str, str | int | bool]:
    values: dict[str, str | int | bool] = {
        "formula": "tokens-times-rate-divided-by-1000",
        "plan_sha256": StrictRecordCodec(FrozenBatchPlan).sha256(plan),
        "config_sha256": plan.config_sha256,
        "call_bounds_sha256": canonical_sha256(tuple(calls.items())),
        "selected_track_ids_sha256": canonical_sha256(
            tuple(track.track_id for track in plan.tracks)
        ),
        "maximum_new_calls_total": sum(calls.values()),
        "finite_envelopes": True,
    }
    for modality in TOKEN_MODALITIES:
        values[f"{modality}_tokens_per_call"] = _MODALITY_ENVELOPES[modality]
        values[f"{modality}_rate_per_1k"] = _OFFICIAL_RATES[modality]
    return values


def _build_preflight(
    plan: FrozenBatchPlan,
    reusable_segment_ids: Mapping[str, tuple[str, ...]],
    case_index: int,
) -> PreflightRecord:
    calls = {
        track.track_id: track.maximum_new_calls
        - len(reusable_segment_ids[track.track_id])
        for track in plan.tracks
    }
    total_calls = sum(calls.values())
    return seal_record(
        PreflightRecord(
            schema_version=1,
            plan_sha256=StrictRecordCodec(FrozenBatchPlan).sha256(plan),
            checked_at_utc="2026-09-14T00:01:00Z",
            expires_at_utc="2026-09-15T00:01:00Z",
            targeted_checks_sha256=canonical_sha256(
                ("property-2-targeted-checks", case_index)
            ),
            identity_profile_label="frontier-audiobook",
            identity_resolved=True,
            identity_checked_at_utc="2026-09-14T00:01:01Z",
            official_rates=_OFFICIAL_RATES,
            official_rate_provenance={
                "source_url": "https://aws.amazon.com/bedrock/pricing/",
                "offer_publication_date": "2026-09-14",
                "retrieved_at_utc": "2026-09-14T00:00:30Z",
                "effective_date": "2026-09-14",
                "model_id": "amazon.nova-2-sonic-v1:0",
                "region": "us-east-1",
                "purchase_option": "on-demand",
                "currency": "USD",
                "unit": "per-1k-tokens",
            },
            reusable_segment_ids=reusable_segment_ids,
            maximum_new_calls_by_track=calls,
            maximum_new_calls_total=total_calls,
            estimated_pre_tax_usd=_estimate(total_calls, _OFFICIAL_RATES),
            estimate_inputs=_estimate_inputs(plan, calls),
            delivery_collisions={
                track.track_id: DestinationState.ABSENT for track in plan.tracks
            },
            per_file_inventory_sha256=canonical_sha256(
                (
                    "property-2-inventory",
                    plan.config_sha256,
                    tuple(
                        (track.track_id, track.source.raw_sha256)
                        for track in plan.tracks
                    ),
                )
            ),
            canonical_sha256="",
        )
    )


def _build_authorization(
    plan: FrozenBatchPlan,
    preflight: PreflightRecord,
    case_index: int,
) -> PaidAuthorization:
    approved = Decimal(preflight.estimated_pre_tax_usd) + Decimal("1")
    preflight_sha256 = StrictRecordCodec(PreflightRecord).sha256(preflight)
    challenge = canonical_sha256(("property-2-challenge", case_index))
    display_sha256 = canonical_sha256(
        {
            "schema": "property-2-display-v1",
            "plan_sha256": StrictRecordCodec(FrozenBatchPlan).sha256(plan),
            "preflight_sha256": preflight_sha256,
            "challenge": challenge,
        }
    )
    confirmed_at_utc = "2026-09-14T00:02:30Z"
    decision = AuthorizationDecision.AUTHORIZE_EXACT_SCOPE
    return seal_record(
        PaidAuthorization(
            schema_version=1,
            authorization_id=f"authorization-case-{case_index:03d}",
            plan_sha256=StrictRecordCodec(FrozenBatchPlan).sha256(plan),
            preflight_sha256=preflight_sha256,
            local_preflight_sha256=canonical_sha256(
                ("property-2-local-preflight", preflight.canonical_sha256)
            ),
            estimate_sha256=canonical_sha256(
                (preflight.estimate_inputs, preflight.estimated_pre_tax_usd)
            ),
            official_rate_provenance_sha256=canonical_sha256(
                (preflight.official_rates, preflight.official_rate_provenance)
            ),
            exact_transaction_ids=tuple(
                track.transaction_id for track in plan.tracks
            ),
            exact_track_ids=tuple(track.track_id for track in plan.tracks),
            exact_command_sha256s=tuple(
                track.command_sha256 for track in plan.tracks
            ),
            maximum_new_calls_by_track=dict(
                preflight.maximum_new_calls_by_track
            ),
            maximum_new_calls_total=preflight.maximum_new_calls_total,
            estimated_pre_tax_usd=preflight.estimated_pre_tax_usd,
            operator_approved_max_estimated_pre_tax_usd=_canonical_decimal(
                approved
            ),
            issued_at_utc="2026-09-14T00:02:00Z",
            expires_at_utc="2026-09-14T01:02:00Z",
            one_shot=True,
            confirmation_challenge=challenge,
            confirmation_display_sha256=display_sha256,
            confirmation_decision=decision,
            confirmed_at_utc=confirmed_at_utc,
            confirmation_sha256=authorization_confirmation_sha256(
                display_sha256=display_sha256,
                challenge=challenge,
                decision=decision,
                confirmed_at_utc=confirmed_at_utc,
            ),
            canonical_sha256="",
        )
    )


def _plan_bindings_are_complete(
    plan: FrozenBatchPlan,
    *,
    maximum_tracks: int,
) -> bool:
    if not 1 <= len(plan.tracks) <= maximum_tracks:
        return False
    track_ids = tuple(track.track_id for track in plan.tracks)
    if len(set(track_ids)) != len(track_ids):
        return False
    if tuple(track.sequence for track in plan.tracks) != tuple(
        sorted(track.sequence for track in plan.tracks)
    ):
        return False

    for track in plan.tracks:
        if track.command_sha256 != canonical_sha256(track.command_argv):
            return False
        if track.maximum_new_calls != track.source.segment_count:
            return False
        if track.source.render_context_radius != _RENDER_CONTEXT_RADIUS:
            return False
        if track.command_argv[:2] != (
            "frontier-audiobook",
            "_production-worker",
        ):
            return False
        if track.command_argv[track.command_argv.index("--track") + 1] != track.track_id:
            return False
        if (
            track.command_argv[track.command_argv.index("--transaction") + 1]
            != track.transaction_id
        ):
            return False
        protected_binding = canonical_sha256(
            {
                "schema": "frontier-plan-protected-binding-v1",
                "config_path": plan.config_path,
                "config_sha256": plan.config_sha256,
                "source_path": track.source.source_path,
                "source_raw_sha256": track.source.raw_sha256,
            }
        )
        if track.protected_inventory_sha256 != protected_binding:
            return False
    return True


def _preflight_bindings_are_complete(
    plan: FrozenBatchPlan,
    preflight: PreflightRecord,
) -> bool:
    track_ids = tuple(track.track_id for track in plan.tracks)
    if preflight.plan_sha256 != StrictRecordCodec(FrozenBatchPlan).sha256(plan):
        return False
    if tuple(preflight.reusable_segment_ids) != track_ids:
        return False
    if tuple(preflight.maximum_new_calls_by_track) != track_ids:
        return False
    if tuple(preflight.delivery_collisions) != track_ids:
        return False

    for track in plan.tracks:
        active_segment_ids = tuple(item.segment_id for item in track.source.segments)
        reusable = preflight.reusable_segment_ids[track.track_id]
        if any(segment_id not in active_segment_ids for segment_id in reusable):
            return False
        if (
            preflight.maximum_new_calls_by_track[track.track_id]
            != track.maximum_new_calls - len(reusable)
        ):
            return False
        if not (
            0
            <= preflight.maximum_new_calls_by_track[track.track_id]
            <= track.maximum_new_calls
        ):
            return False

    calls = dict(preflight.maximum_new_calls_by_track)
    if preflight.maximum_new_calls_total != sum(calls.values()):
        return False
    expected_inputs = _estimate_inputs(plan, calls)
    if dict(preflight.estimate_inputs) != expected_inputs:
        return False
    return preflight.estimated_pre_tax_usd == _estimate(
        preflight.maximum_new_calls_total,
        preflight.official_rates,
    )


def _authorization_bindings_are_current(
    authorization: PaidAuthorization,
    plan: FrozenBatchPlan,
    preflight: PreflightRecord,
) -> bool:
    if not _preflight_bindings_are_complete(plan, preflight):
        return False
    return (
        authorization.plan_sha256
        == StrictRecordCodec(FrozenBatchPlan).sha256(plan)
        and authorization.preflight_sha256
        == StrictRecordCodec(PreflightRecord).sha256(preflight)
        and authorization.exact_transaction_ids
        == tuple(track.transaction_id for track in plan.tracks)
        and authorization.exact_track_ids
        == tuple(track.track_id for track in plan.tracks)
        and authorization.exact_command_sha256s
        == tuple(track.command_sha256 for track in plan.tracks)
        and dict(authorization.maximum_new_calls_by_track)
        == dict(preflight.maximum_new_calls_by_track)
        and authorization.maximum_new_calls_total
        == preflight.maximum_new_calls_total
        and authorization.estimated_pre_tax_usd
        == preflight.estimated_pre_tax_usd
        and authorization.one_shot
    )


def _replace_first_track(
    plan: FrozenBatchPlan,
    replacement: FrozenTrackPlan,
) -> FrozenBatchPlan:
    return seal_record(
        replace(
            plan,
            tracks=(replacement, *plan.tracks[1:]),
            canonical_sha256="",
        )
    )


def _resealed_plan_mutations(plan: FrozenBatchPlan) -> tuple[FrozenBatchPlan, ...]:
    first = plan.tracks[0]
    source_mutation = _replace_first_track(
        plan,
        replace(
            first,
            source=replace(
                first.source,
                raw_sha256=_different_digest(first.source.raw_sha256),
            ),
        ),
    )
    config_mutation = seal_record(
        replace(
            plan,
            config_sha256=_different_digest(plan.config_sha256),
            canonical_sha256="",
        )
    )
    changed_argv = (*first.command_argv, "--tampered-command")
    command_mutation = _replace_first_track(
        plan,
        replace(
            first,
            command_argv=changed_argv,
            command_sha256=canonical_sha256(changed_argv),
        ),
    )
    plan_mutation = seal_record(
        replace(plan, plan_id=f"{plan.plan_id}-mutated", canonical_sha256="")
    )
    return source_mutation, config_mutation, command_mutation, plan_mutation


def _coherent_call_bound_mutation(
    plan: FrozenBatchPlan,
    preflight: PreflightRecord,
    case_index: int,
) -> PreflightRecord:
    first = plan.tracks[0]
    old_calls = preflight.maximum_new_calls_by_track[first.track_id]
    new_calls = (old_calls + 1) % (first.maximum_new_calls + 1)
    assert new_calls != old_calls
    changed_reuse = dict(preflight.reusable_segment_ids)
    reusable_count = first.maximum_new_calls - new_calls
    changed_reuse[first.track_id] = tuple(
        item.segment_id for item in first.source.segments[:reusable_count]
    )
    return _build_preflight(plan, changed_reuse, case_index)


def _mutated_source_sentences(
    original: tuple[str, ...],
    *,
    mutation_kind: str,
    mutation_index: int,
) -> tuple[str, ...]:
    if mutation_kind == "insert":
        inserted = "Inserted signal enters quiet orbit."
        return (*original[:mutation_index], inserted, *original[mutation_index:])
    words = original[mutation_index].removesuffix(".").split()
    words[0] = "mutated"
    replacement = f"{' '.join(words)}."
    return (
        *original[:mutation_index],
        replacement,
        *original[mutation_index + 1 :],
    )


def _assert_bounded_context_change(
    original,
    changed,
    original_sentences: tuple[str, ...],
    *,
    mutation_kind: str,
    mutation_index: int,
) -> None:
    assert original.raw_sha256 != changed.raw_sha256
    assert original.spoken_sha256 != changed.spoken_sha256
    assert (
        original.render_context_radius
        == changed.render_context_radius
        == _RENDER_CONTEXT_RADIUS
    )

    original_by_text = {item.text_sha256: item for item in original.segments}
    changed_by_text = {item.text_sha256: item for item in changed.segments}
    if mutation_kind == "insert":
        locally_affected = {mutation_index - 1, mutation_index}
        absent: set[int] = set()
    else:
        locally_affected = {mutation_index - 1, mutation_index + 1}
        absent = {mutation_index}

    for index, sentence in enumerate(original_sentences):
        text_sha256 = sha256_text(sentence)
        if index in absent:
            assert text_sha256 not in changed_by_text
            continue
        before = original_by_text[text_sha256]
        after = changed_by_text[text_sha256]
        if index in locally_affected:
            assert before.render_identity_sha256 != after.render_identity_sha256
        else:
            assert before.render_identity_sha256 == after.render_identity_sha256


def _targeted_check_binding(workspace: Path) -> TargetedCheckBinding:
    relative = "audiobook-studio/build/test-results/property-2-offline.txt"
    result = workspace / relative
    result.parent.mkdir(parents=True, exist_ok=True)
    result.write_text("offline targeted checks passed\n", encoding="utf-8")
    return bind_targeted_check_result(
        workspace,
        relative,
        command_sha256=canonical_sha256(
            ("pytest", "tests/test_production_property_2.py")
        ),
        return_code=0,
        aws_access_disabled=True,
        model_access_disabled=True,
    )


def test_property_2_frozen_plans_and_preflight_scopes_are_immutable_and_bounded(
    tmp_path,
):
    """Feature: audiobook-production-workflow, Property 2: Frozen plans and preflight scopes are immutable and bounded"""

    assert GENERATED_CASES >= 100
    print(f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; cases={GENERATED_CASES}")
    rng = random.Random(PROPERTY_SEED)
    for chapter in range(1, _CHAPTER_COUNT + 1):
        _write_chapter(tmp_path, chapter, _sentences(0, chapter, 6))
    targeted_checks = _targeted_check_binding(tmp_path)

    plan_codec = StrictRecordCodec(FrozenBatchPlan)
    preflight_codec = StrictRecordCodec(PreflightRecord)
    authorization_codec = StrictRecordCodec(PaidAuthorization)

    for case_index in range(GENERATED_CASES):
        maximum = rng.randint(2, 6)
        config_path = _write_config(tmp_path, maximum)
        config_bytes = read_bytes_nofollow(config_path)
        selectors, expected_chapters = _valid_selectors(
            rng,
            case_index,
            maximum,
        )
        sentence_count = rng.randint(5, 8)
        source_sentences: dict[int, tuple[str, ...]] = {}
        for chapter in expected_chapters:
            generated = _sentences(case_index + 1, chapter, sentence_count)
            source_sentences[chapter] = generated
            _write_chapter(tmp_path, chapter, generated)

        plan_id = f"property-two-case-{case_index:03d}"
        plan_path = create_production_plan(
            config_path,
            selectors,
            plan_id=plan_id,
            workspace_root=tmp_path,
            created_at_utc="2026-09-14T00:00:00Z",
        )
        original_plan_bytes = read_bytes_nofollow(plan_path)
        plan = load_production_plan(plan_path)
        config = parse_production_toml(config_bytes, label=str(config_path))
        catalog = build_ordered_track_catalog(config, tmp_path)

        try:
            expected_track_ids = tuple(
                f"chapter-{chapter:03d}" for chapter in expected_chapters
            )
            assert tuple(track.track_id for track in plan.tracks) == expected_track_ids
            assert _plan_bindings_are_complete(plan, maximum_tracks=maximum)
            assert plan.config_sha256 == sha256_bytes(config_bytes)
            assert original_plan_bytes == plan_codec.dump_bytes(plan)
            assert plan_codec.loads(original_plan_bytes) == plan
            assert plan_codec.dump_bytes(plan_codec.loads(original_plan_bytes)) == original_plan_bytes
            assert plan_codec.sha256(plan) == sha256_bytes(original_plan_bytes)
            assert plan.canonical_sha256 == canonical_sha256(
                plan,
                omit_fields=("canonical_sha256",),
            )
            for track in plan.tracks:
                current = read_bytes_nofollow(tmp_path / track.source.source_path)
                assert track.source.raw_sha256 == sha256_bytes(current)
                assert track.maximum_new_calls == track.source.segment_count
                assert source_sentences[int(track.track_id.removeprefix("chapter-"))][0] not in original_plan_bytes.decode("utf-8")

            invalid_id = f"property-two-invalid-{case_index:03d}"
            invalid_path = (
                tmp_path
                / "audiobook-studio/build/production/the-final-frontier/plans"
                / invalid_id
            )
            with pytest.raises(InputError):
                create_production_plan(
                    config_path,
                    _invalid_selectors(case_index, maximum),
                    plan_id=invalid_id,
                    workspace_root=tmp_path,
                    created_at_utc="2026-09-14T00:00:00Z",
                )
            assert not invalid_path.exists()

            reusable: dict[str, tuple[str, ...]] = {}
            for track in plan.tracks:
                reusable_count = rng.randint(0, track.maximum_new_calls)
                selected = rng.sample(
                    list(track.source.segments),
                    reusable_count,
                )
                reusable[track.track_id] = tuple(
                    item.segment_id
                    for item in sorted(selected, key=lambda item: item.ordinal)
                )
            preflight = _build_preflight(plan, reusable, case_index)
            preflight_bytes = preflight_codec.dump_bytes(preflight)
            assert _preflight_bindings_are_complete(plan, preflight)
            assert preflight_codec.loads(preflight_bytes) == preflight
            assert preflight_codec.dump_bytes(preflight_codec.loads(preflight_bytes)) == preflight_bytes
            assert preflight_codec.sha256(preflight) == sha256_bytes(preflight_bytes)
            assert preflight.canonical_sha256 == canonical_sha256(
                preflight,
                omit_fields=("canonical_sha256",),
            )

            authorization = _build_authorization(plan, preflight, case_index)
            authorization_bytes = authorization_codec.dump_bytes(authorization)
            assert authorization_codec.loads(authorization_bytes) == authorization
            assert _authorization_bindings_are_current(
                authorization,
                plan,
                preflight,
            )

            raw_plan_tamper = record_to_data(plan)
            raw_plan_tamper["tracks"][0]["source"]["raw_sha256"] = _different_digest(
                plan.tracks[0].source.raw_sha256
            )
            with pytest.raises(InputError, match="does not match canonical content"):
                plan_codec.loads(canonical_json_bytes(raw_plan_tamper))

            raw_preflight_tamper = record_to_data(preflight)
            raw_preflight_tamper["estimated_pre_tax_usd"] = _canonical_decimal(
                Decimal(preflight.estimated_pre_tax_usd) + Decimal("0.001")
            )
            with pytest.raises(InputError, match="does not match canonical content"):
                preflight_codec.loads(canonical_json_bytes(raw_preflight_tamper))

            for changed_plan in _resealed_plan_mutations(plan):
                assert plan_codec.loads(plan_codec.dump_bytes(changed_plan)) == changed_plan
                assert changed_plan.canonical_sha256 != plan.canonical_sha256
                assert not _authorization_bindings_are_current(
                    authorization,
                    changed_plan,
                    preflight,
                )

            changed_preflight = _coherent_call_bound_mutation(
                plan,
                preflight,
                case_index,
            )
            assert _preflight_bindings_are_complete(plan, changed_preflight)
            assert changed_preflight.canonical_sha256 != preflight.canonical_sha256
            assert not _authorization_bindings_are_current(
                authorization,
                plan,
                changed_preflight,
            )
            inventory_mutation = seal_record(
                replace(
                    preflight,
                    per_file_inventory_sha256=_different_digest(
                        preflight.per_file_inventory_sha256
                    ),
                    canonical_sha256="",
                )
            )
            assert not _authorization_bindings_are_current(
                authorization,
                plan,
                inventory_mutation,
            )
            estimate_mutation = seal_record(
                replace(
                    preflight,
                    estimated_pre_tax_usd=_canonical_decimal(
                        Decimal(preflight.estimated_pre_tax_usd) + Decimal("0.001")
                    ),
                    canonical_sha256="",
                )
            )
            assert not _preflight_bindings_are_complete(plan, estimate_mutation)
            assert not _authorization_bindings_are_current(
                authorization,
                plan,
                estimate_mutation,
            )

            first_track = plan.tracks[0]
            stale_command_plan = _replace_first_track(
                plan,
                replace(
                    first_track,
                    command_argv=(*first_track.command_argv, "--stale-command"),
                ),
            )
            with pytest.raises(InputError, match="Worker command hash mismatch"):
                run_local_preflight(
                    tmp_path,
                    config,
                    catalog,
                    stale_command_plan,
                    targeted_checks,
                )
            expanded_call_plan = _replace_first_track(
                plan,
                replace(
                    first_track,
                    maximum_new_calls=first_track.maximum_new_calls + 1,
                ),
            )
            with pytest.raises(InputError, match="call ceiling is inconsistent"):
                run_local_preflight(
                    tmp_path,
                    config,
                    catalog,
                    expanded_call_plan,
                    targeted_checks,
                )

            config_path.write_bytes(config_bytes + b"\n# byte-level drift\n")
            try:
                with pytest.raises(InputError, match="configuration drifted"):
                    run_local_preflight(
                        tmp_path,
                        config,
                        catalog,
                        plan,
                        targeted_checks,
                    )
            finally:
                config_path.write_bytes(config_bytes)

            target = plan.tracks[0]
            target_chapter = int(target.track_id.removeprefix("chapter-"))
            original_sentences = source_sentences[target_chapter]
            mutation_kind = "insert" if rng.getrandbits(1) else "edit"
            mutation_index = rng.randint(1, len(original_sentences) - 2)
            changed_sentences = _mutated_source_sentences(
                original_sentences,
                mutation_kind=mutation_kind,
                mutation_index=mutation_index,
            )
            _write_chapter(tmp_path, target_chapter, changed_sentences)

            with pytest.raises(InputError, match="source drifted"):
                run_local_preflight(
                    tmp_path,
                    config,
                    catalog,
                    plan,
                    targeted_checks,
                )
            with pytest.raises(InputError, match="existing canonical bytes differ"):
                create_production_plan(
                    config_path,
                    selectors,
                    plan_id=plan_id,
                    workspace_root=tmp_path,
                )
            assert read_bytes_nofollow(plan_path) == original_plan_bytes

            recomputed_path = create_production_plan(
                config_path,
                selectors,
                plan_id=f"{plan_id}-recomputed",
                workspace_root=tmp_path,
                created_at_utc="2026-09-14T00:03:00Z",
            )
            recomputed = load_production_plan(recomputed_path)
            old_target = plan.tracks[0]
            new_target = recomputed.tracks[0]
            assert new_target.source.raw_sha256 == sha256_bytes(
                read_bytes_nofollow(_chapter_path(tmp_path, target_chapter))
            )
            assert new_target.maximum_new_calls == new_target.source.segment_count
            expected_delta = 1 if mutation_kind == "insert" else 0
            assert (
                new_target.maximum_new_calls
                == old_target.maximum_new_calls + expected_delta
            )
            _assert_bounded_context_change(
                old_target.source,
                new_target.source,
                original_sentences,
                mutation_kind=mutation_kind,
                mutation_index=mutation_index,
            )
            assert not _authorization_bindings_are_current(
                authorization,
                recomputed,
                preflight,
            )
        except Exception as exc:
            exc.add_note(
                f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; case={case_index}; "
                f"maximum={maximum}; selectors={selectors.tokens!r}"
            )
            raise
