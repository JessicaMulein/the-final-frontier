"""Deterministic generated checks for audiobook production correctness Property 8."""

from __future__ import annotations

import random
import socket
import subprocess
import urllib.request
from dataclasses import dataclass
from pathlib import Path

import pytest

from frontier_audiobook import narrate
from frontier_audiobook.production_models import ValidationStatus
from frontier_audiobook.util import sha256_text

import test_production_validation as validation_support


PROPERTY_TAG = (
    "Feature: audiobook-production-workflow, "
    "Property 8: Active manifests are complete and unambiguous"
)
PROPERTY_SEED = 0xA0D10B08
GENERATED_CASES = 100

# **Validates: Requirements 10.2, 10.3, 10.4, 10.5, 10.9**

_FIXED_PLAN_FIELDS = (
    "track_id",
    "transaction_id",
    "track_plan_sha256",
    "effective_config_sha256",
    "source_snapshot_sha256",
    "track_kind",
    "sequence",
    "voice_id",
    "model_id",
    "region",
    "profile_label",
    "fidelity_policy",
    "normalization",
    "audio_sample_rate_hz",
    "audio_sample_size_bits",
    "audio_channels",
    "audio_encoding",
    "output_path",
    "source_path",
    "source_kind",
    "source_section",
    "source_sha256",
    "normalized_body_sha256",
    "spoken_sha256",
    "declared_word_count",
    "normalized_word_count",
    "word_count",
    "spoken_token_count",
    "segment_count",
    "narration_only_punctuation_segments",
    "target_segment_words",
    "segment_boundary_policy",
    "render_identity_schema",
    "render_context_radius",
)
_ACTIVE_PLAN_FIELDS = (
    "paragraph_index",
    "text_sha256",
    "render_identity_sha256",
    "word_count",
    "narration_only_punctuation",
)
_EXPECTED_SCENARIO_COUNTS = {
    "fixed-field-mutation": len(_FIXED_PLAN_FIELDS),
    "active-field-mutation": len(_ACTIVE_PLAN_FIELDS),
    "track-path-mutation": 1,
    "valid": 7,
    "active-count": 8,
    "gap": 8,
    "duplicate": 8,
    "reordering": 8,
    "token-loss": 8,
    "token-addition": 8,
    "historical-records": 5,
}
_TARGET_CHECKS = (
    "manifest.frozen-plan-binding",
    "manifest.active-set",
    "manifest.token-conservation",
    "manifest.path-confinement",
    "manifest.history-exclusion",
)
_NON_ACTIVE_BUCKETS = (
    "carried_over_segments",
    "historical_segments",
    "rejected_segments",
)


@dataclass(frozen=True, slots=True)
class _GeneratedCase:
    case_index: int
    scenario: str
    field_name: str | None
    active_index: int
    nonce: int
    historical_records_per_bucket: int


@pytest.fixture(autouse=True)
def deny_external_paid_and_child_boundaries(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Keep every generated manifest check local, offline, and nonbillable."""

    def blocked(*_args, **_kwargs):
        raise AssertionError("Property 8 must remain local and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(urllib.request, "urlopen", blocked)
    monkeypatch.setattr(subprocess, "Popen", blocked)
    monkeypatch.setattr(subprocess, "run", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.delenv(name, raising=False)


def _generated_cases() -> tuple[_GeneratedCase, ...]:
    rng = random.Random(PROPERTY_SEED)
    specifications: list[tuple[str, str | None]] = [
        ("fixed-field-mutation", field_name)
        for field_name in _FIXED_PLAN_FIELDS
    ]
    specifications.extend(
        ("active-field-mutation", field_name)
        for field_name in _ACTIVE_PLAN_FIELDS
    )
    specifications.append(("track-path-mutation", "track_audio_path"))
    for scenario, count in _EXPECTED_SCENARIO_COUNTS.items():
        if scenario in {
            "fixed-field-mutation",
            "active-field-mutation",
            "track-path-mutation",
        }:
            continue
        specifications.extend((scenario, None) for _ in range(count))

    assert len(specifications) == GENERATED_CASES
    rng.shuffle(specifications)
    return tuple(
        _GeneratedCase(
            case_index=case_index,
            scenario=scenario,
            field_name=field_name,
            active_index=rng.randrange(2),
            nonce=rng.getrandbits(64),
            historical_records_per_bucket=1 + rng.randrange(4),
        )
        for case_index, (scenario, field_name) in enumerate(specifications)
    )


def _mutated_value(field_name: str, current: object, nonce: int) -> object:
    if current is None:
        return f"mutated-section-{nonce:016x}"
    if type(current) is bool:
        return not current
    if type(current) is int:
        return current + 1 + nonce % 7
    if isinstance(current, str):
        if len(current) == 64 and set(current) <= set("0123456789abcdef"):
            return sha256_text(f"{field_name}:{nonce:016x}")
        return f"{current}-mutated-{nonce:016x}"
    raise AssertionError(f"No deterministic mutation for {field_name}: {current!r}")


def _historical_record(
    fixture: validation_support.ValidationFixture,
    case: _GeneratedCase,
    bucket: str,
    ordinal: int,
) -> dict[str, object]:
    stem = f"history-{case.case_index:03d}-{bucket}-{ordinal:02d}"
    audio_path = (
        fixture.transaction_root / "runtime" / "segments" / f"{stem}.wav"
    ).relative_to(fixture.workspace).as_posix()
    return {
        "segment_id": f"segment-{900 + ordinal:03d}",
        "status": bucket.removesuffix("_segments").replace("_", "-"),
        "word_count": 100_000 + ordinal,
        "text": f"non-active-history-{case.nonce:016x}-{ordinal}",
        "text_sha256": sha256_text(f"{stem}:text"),
        "audio_path": audio_path,
        "audio_sha256": sha256_text(f"{stem}:audio"),
    }


def _apply_case(
    case: _GeneratedCase,
    fixture: validation_support.ValidationFixture,
    manifest: dict[str, object],
) -> None:
    entries = manifest["segments"]
    assert isinstance(entries, list)
    assert len(entries) == 2
    active = entries[case.active_index]
    assert isinstance(active, dict)

    if case.scenario == "fixed-field-mutation":
        assert case.field_name is not None
        manifest[case.field_name] = _mutated_value(
            case.field_name,
            manifest[case.field_name],
            case.nonce,
        )
    elif case.scenario == "active-field-mutation":
        assert case.field_name is not None
        active[case.field_name] = _mutated_value(
            case.field_name,
            active[case.field_name],
            case.nonce,
        )
    elif case.scenario == "track-path-mutation":
        manifest["track_audio_path"] = (
            fixture.transaction_root / "runtime" / "unexpected-track.wav"
        ).relative_to(fixture.workspace).as_posix()
    elif case.scenario == "active-count":
        manifest["active_segment_count"] = 1 if case.nonce % 2 else 3
    elif case.scenario == "gap":
        entries[1]["segment_id"] = f"segment-{3 + case.nonce % 97:03d}"
    elif case.scenario == "duplicate":
        entries[1]["segment_id"] = entries[0]["segment_id"]
    elif case.scenario == "reordering":
        manifest["segments"] = list(reversed(entries))
    elif case.scenario == "token-loss":
        text = active["text"]
        assert isinstance(text, str)
        words = text.split()
        assert len(words) >= 2
        active["text"] = " ".join(words[:-1])
    elif case.scenario == "token-addition":
        text = active["text"]
        assert isinstance(text, str)
        active["text"] = f"{text} addedtoken{case.nonce % 1009}"
    elif case.scenario == "historical-records":
        for bucket in _NON_ACTIVE_BUCKETS:
            manifest[bucket] = [
                _historical_record(fixture, case, bucket, ordinal)
                for ordinal in range(1, case.historical_records_per_bucket + 1)
            ]
    else:
        assert case.scenario == "valid"


def _assert_expected_result(
    case: _GeneratedCase,
    manifest: dict[str, object],
    evidence,
) -> None:
    checks = {
        check_id: validation_support._check(evidence, check_id)
        for check_id in _TARGET_CHECKS
    }
    if case.scenario in {"valid", "historical-records"}:
        assert evidence.status is ValidationStatus.PASSED
        assert evidence.delivery_gate_passed is True
        assert all(check.status is ValidationStatus.PASSED for check in checks.values())
        if case.scenario == "historical-records":
            entries = manifest["segments"]
            assert isinstance(entries, list)
            assert manifest["active_segment_count"] == len(entries)
            assert sum(len(manifest[bucket]) for bucket in _NON_ACTIVE_BUCKETS) > 0
        return

    assert evidence.status is ValidationStatus.BLOCKED
    assert evidence.delivery_gate_passed is False
    if case.scenario == "fixed-field-mutation":
        expected_check = "manifest.frozen-plan-binding"
    elif case.scenario == "track-path-mutation":
        expected_check = "manifest.path-confinement"
    elif case.scenario in {"token-loss", "token-addition"}:
        expected_check = "manifest.token-conservation"
    else:
        expected_check = "manifest.active-set"
    assert checks[expected_check].status is ValidationStatus.BLOCKED


def test_active_manifests_are_complete_and_unambiguous(
    tmp_path: Path,
) -> None:
    """Feature: audiobook-production-workflow, Property 8: Active manifests are complete and unambiguous"""

    assert GENERATED_CASES >= 100
    cases = _generated_cases()
    assert len(cases) == GENERATED_CASES
    print(f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; cases={GENERATED_CASES}")

    observed_counts = {scenario: 0 for scenario in _EXPECTED_SCENARIO_COUNTS}
    observed_fixed_fields: set[str] = set()
    observed_active_fields: set[str] = set()
    for case in cases:
        context = (
            f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; case={case.case_index}; "
            f"input={case!r}"
        )
        try:
            fixture = validation_support._fixture(
                tmp_path / f"case-{case.case_index:03d}"
            )
            manifest = validation_support._manifest(fixture)
            _apply_case(case, fixture, manifest)
            validation_support._write_json(fixture.manifest_path, manifest)
            evidence = validation_support._validate(fixture)
            _assert_expected_result(case, manifest, evidence)
            observed_counts[case.scenario] += 1
            if case.scenario == "fixed-field-mutation":
                assert case.field_name is not None
                observed_fixed_fields.add(case.field_name)
            elif case.scenario == "active-field-mutation":
                assert case.field_name is not None
                observed_active_fields.add(case.field_name)
        except Exception as exc:
            exc.add_note(context)
            raise

    assert observed_counts == _EXPECTED_SCENARIO_COUNTS
    assert observed_fixed_fields == set(_FIXED_PLAN_FIELDS)
    assert observed_active_fields == set(_ACTIVE_PLAN_FIELDS)
