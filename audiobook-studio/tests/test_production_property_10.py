"""Deterministic generated checks for audiobook production correctness Property 10."""

from __future__ import annotations

import random
import socket
import subprocess
import wave
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterator

import pytest

from frontier_audiobook import narrate
from frontier_audiobook.production_models import ValidationStatus
from frontier_audiobook.util import sha256_bytes

import test_production_validation as validation_support


PROPERTY_TAG = (
    "Feature: audiobook-production-workflow, "
    "Property 10: Assembly integrity is preserved"
)
PROPERTY_SEED = 0xA0D10B0A
GENERATED_CASES = 128

# **Validates: Requirements 10.10, 10.11, 10.12**

_SCENARIOS = (
    "valid",
    "segment-pcm",
    "manifest-order",
    "assembled-order",
    "stitch-profile-value",
    "stitch-profile-missing",
    "stitch-profile-extra",
    "wav-pcm",
    "wav-sample-rate",
    "wav-sample-size",
    "wav-channels",
    "wav-compressed",
    "wav-byte-count",
    "wav-sha256",
    "wav-duration",
)
_STITCHING_SCENARIOS = frozenset(
    {
        "segment-pcm",
        "manifest-order",
        "assembled-order",
        "stitch-profile-value",
        "stitch-profile-missing",
        "stitch-profile-extra",
        "wav-pcm",
    }
)
_WAV_SCENARIOS = frozenset(_SCENARIOS) - _STITCHING_SCENARIOS - {"valid"}
_ALTERNATIVE_SAMPLE_RATES = (8000, 16000, 22050, 44100, 48000)
_STITCH_PROFILE_KEYS = tuple(narrate.stitch_profile())


@dataclass(frozen=True, slots=True)
class _PcmShape:
    leading_silent_frames: int
    active_frames: int
    trailing_silent_frames: int
    amplitude: int
    half_period_frames: int


@dataclass(frozen=True, slots=True)
class _GeneratedCase:
    case_index: int
    scenario: str
    pcm_shapes: tuple[_PcmShape, _PcmShape]
    stitch_profile_key: str
    alternative_sample_rate_hz: int


@dataclass(frozen=True, slots=True)
class _AssemblyState:
    manifest: dict[str, object]
    parts: tuple[narrate.StitchSegment, ...]
    settings: narrate.StitchAudioSettings
    expected_lpcm: bytes
    expected_wav: bytes


@pytest.fixture(autouse=True)
def deny_network_aws_model_narration_and_child_process(monkeypatch, tmp_path):
    """Fail immediately if this local property crosses an external or paid boundary."""

    def blocked(*_args, **_kwargs):
        raise AssertionError("Property 10 must remain local and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(subprocess, "Popen", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.setenv("AWS_CONFIG_FILE", str(tmp_path / "denied-aws-config"))
    monkeypatch.setenv(
        "AWS_SHARED_CREDENTIALS_FILE",
        str(tmp_path / "denied-aws-credentials"),
    )
    for variable in (
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_SECURITY_TOKEN",
    ):
        monkeypatch.delenv(variable, raising=False)


def _shuffled_cycle(rng: random.Random, values: tuple[str, ...]) -> Iterator[str]:
    while True:
        batch = list(values)
        rng.shuffle(batch)
        yield from batch


def _pcm_shape(rng: random.Random, segment_index: int) -> _PcmShape:
    # Disjoint amplitude ranges guarantee that reversing the two generated clips
    # changes the assembled byte sequence rather than relying on probability.
    return _PcmShape(
        leading_silent_frames=2 * rng.randrange(0, 121),
        active_frames=2 * rng.randrange(360, 1201),
        trailing_silent_frames=2 * rng.randrange(0, 121),
        amplitude=rng.randrange(1000, 9000) + segment_index * 10000,
        half_period_frames=rng.randrange(1, 98),
    )


def _generated_cases(rng: random.Random) -> tuple[_GeneratedCase, ...]:
    scenarios = _shuffled_cycle(rng, _SCENARIOS)
    return tuple(
        _GeneratedCase(
            case_index=case_index,
            scenario=next(scenarios),
            pcm_shapes=(_pcm_shape(rng, 0), _pcm_shape(rng, 1)),
            stitch_profile_key=rng.choice(_STITCH_PROFILE_KEYS),
            alternative_sample_rate_hz=rng.choice(_ALTERNATIVE_SAMPLE_RATES),
        )
        for case_index in range(GENERATED_CASES)
    )


def _lpcm(shape: _PcmShape) -> bytes:
    active = bytearray()
    for frame in range(shape.active_frames):
        sign = 1 if (frame // shape.half_period_frames) % 2 == 0 else -1
        active.extend(
            (sign * shape.amplitude).to_bytes(2, "little", signed=True)
        )
    return (
        b"\x00\x00" * shape.leading_silent_frames
        + bytes(active)
        + b"\x00\x00" * shape.trailing_silent_frames
    )


def _segments(manifest: dict[str, object]) -> list[dict[str, object]]:
    raw = manifest["segments"]
    assert isinstance(raw, list)
    assert all(isinstance(item, dict) for item in raw)
    return raw  # type: ignore[return-value]


def _prepare_valid_assembly(
    fixture: validation_support.ValidationFixture,
    case: _GeneratedCase,
) -> _AssemblyState:
    manifest = validation_support._manifest(fixture)
    entries = _segments(manifest)
    settings = narrate.StitchAudioSettings(24000, 16, 1)
    parts: list[narrate.StitchSegment] = []

    for ordinal, (entry, snapshot, shape) in enumerate(
        zip(entries, fixture.track.source.segments, case.pcm_shapes, strict=True),
        start=1,
    ):
        segment_lpcm = _lpcm(shape)
        audio_path = fixture.workspace / str(entry["audio_path"])
        event_path = fixture.workspace / str(entry["event_journal_path"])
        audio = validation_support._wav_bytes(segment_lpcm)
        events = validation_support._event_bytes(
            validation_support._output_events(str(entry["text"]), segment_lpcm)
        )
        audio_path.write_bytes(audio)
        event_path.write_bytes(events)
        entry["audio_sha256"] = sha256_bytes(audio)
        entry["event_journal_sha256"] = sha256_bytes(events)
        entry["duration_seconds"] = round(
            (len(segment_lpcm) // 2) / settings.sample_rate_hz,
            3,
        )
        parts.append(
            narrate.StitchSegment(
                narrate.Segment(
                    ordinal,
                    snapshot.paragraph_index,
                    str(entry["text"]),
                    snapshot.narration_only_punctuation,
                ),
                segment_lpcm,
                event_path,
            )
        )

    expected_lpcm = narrate.stitch_track_lpcm(tuple(parts), settings)
    expected_wav = validation_support._wav_bytes(expected_lpcm)
    track_audio_path = fixture.workspace / str(manifest["track_audio_path"])
    track_audio_path.write_bytes(expected_wav)
    manifest["track_audio_sha256"] = sha256_bytes(expected_wav)
    manifest["track_audio_byte_count"] = len(expected_wav)
    manifest["track_duration_seconds"] = narrate.assembled_lpcm_duration_seconds(
        expected_lpcm,
        settings,
    )
    manifest["stitching"] = narrate.stitch_profile()
    validation_support._write_json(fixture.manifest_path, manifest)
    return _AssemblyState(
        manifest=manifest,
        parts=tuple(parts),
        settings=settings,
        expected_lpcm=expected_lpcm,
        expected_wav=expected_wav,
    )


def _write_track_wav(
    fixture: validation_support.ValidationFixture,
    manifest: dict[str, object],
    content: bytes,
) -> None:
    path = fixture.workspace / str(manifest["track_audio_path"])
    path.write_bytes(content)
    manifest["track_audio_sha256"] = sha256_bytes(content)
    manifest["track_audio_byte_count"] = len(content)


def _negate_s16le(content: bytes) -> bytes:
    result = bytearray()
    for offset in range(0, len(content), 2):
        sample = int.from_bytes(content[offset : offset + 2], "little", signed=True)
        result.extend((-sample).to_bytes(2, "little", signed=True))
    return bytes(result)


def _reversed_assembly(state: _AssemblyState) -> bytes:
    reordered: list[narrate.StitchSegment] = []
    for ordinal, part in enumerate(reversed(state.parts), start=1):
        reordered.append(
            narrate.StitchSegment(
                narrate.Segment(
                    ordinal,
                    part.segment.paragraph_index,
                    part.segment.text,
                    part.segment.narration_only_punctuation,
                ),
                part.lpcm,
                part.event_journal_path,
            )
        )
    return narrate.stitch_track_lpcm(tuple(reordered), state.settings)


def _stereo_lpcm(mono_lpcm: bytes) -> bytes:
    return b"".join(
        mono_lpcm[offset : offset + 2] * 2
        for offset in range(0, len(mono_lpcm), 2)
    )


def _mutate_case(
    fixture: validation_support.ValidationFixture,
    state: _AssemblyState,
    case: _GeneratedCase,
) -> str | None:
    manifest = state.manifest
    entries = _segments(manifest)
    scenario = case.scenario

    if scenario == "valid":
        return None
    if scenario == "segment-pcm":
        index = case.case_index % len(entries)
        entry = entries[index]
        changed_lpcm = _negate_s16le(state.parts[index].lpcm)
        audio_path = fixture.workspace / str(entry["audio_path"])
        event_path = fixture.workspace / str(entry["event_journal_path"])
        audio = validation_support._wav_bytes(changed_lpcm)
        events = validation_support._event_bytes(
            validation_support._output_events(str(entry["text"]), changed_lpcm)
        )
        audio_path.write_bytes(audio)
        event_path.write_bytes(events)
        entry["audio_sha256"] = sha256_bytes(audio)
        entry["event_journal_sha256"] = sha256_bytes(events)
    elif scenario == "manifest-order":
        manifest["segments"] = list(reversed(entries))
    elif scenario == "assembled-order":
        changed_lpcm = _reversed_assembly(state)
        changed_wav = validation_support._wav_bytes(changed_lpcm)
        _write_track_wav(fixture, manifest, changed_wav)
        manifest["track_duration_seconds"] = narrate.assembled_lpcm_duration_seconds(
            changed_lpcm,
            state.settings,
        )
    elif scenario == "stitch-profile-value":
        profile = manifest["stitching"]
        assert isinstance(profile, dict)
        current = profile[case.stitch_profile_key]
        profile[case.stitch_profile_key] = (
            current + 0.125 if isinstance(current, float) else f"{current}-changed"
        )
    elif scenario == "stitch-profile-missing":
        profile = manifest["stitching"]
        assert isinstance(profile, dict)
        profile.pop(case.stitch_profile_key)
    elif scenario == "stitch-profile-extra":
        profile = manifest["stitching"]
        assert isinstance(profile, dict)
        profile["unrecorded-policy"] = "not-approved"
    elif scenario == "wav-pcm":
        changed_lpcm = bytearray(state.expected_lpcm)
        offset = (len(changed_lpcm) // 4) * 2
        sample = int.from_bytes(
            changed_lpcm[offset : offset + 2],
            "little",
            signed=True,
        )
        replacement = -sample if sample else 1234
        changed_lpcm[offset : offset + 2] = replacement.to_bytes(
            2,
            "little",
            signed=True,
        )
        _write_track_wav(
            fixture,
            manifest,
            validation_support._wav_bytes(bytes(changed_lpcm)),
        )
    elif scenario == "wav-sample-rate":
        _write_track_wav(
            fixture,
            manifest,
            validation_support._wav_bytes(
                state.expected_lpcm,
                sample_rate_hz=case.alternative_sample_rate_hz,
            ),
        )
    elif scenario == "wav-sample-size":
        _write_track_wav(
            fixture,
            manifest,
            validation_support._wav_bytes(
                state.expected_lpcm,
                sample_size_bytes=1,
            ),
        )
    elif scenario == "wav-channels":
        _write_track_wav(
            fixture,
            manifest,
            validation_support._wav_bytes(
                _stereo_lpcm(state.expected_lpcm),
                channels=2,
            ),
        )
    elif scenario == "wav-compressed":
        changed = bytearray(state.expected_wav)
        changed[20:22] = (3).to_bytes(2, "little")
        _write_track_wav(fixture, manifest, bytes(changed))
    elif scenario == "wav-byte-count":
        manifest["track_audio_byte_count"] = len(state.expected_wav) + 1
    elif scenario == "wav-sha256":
        manifest["track_audio_sha256"] = "f" * 64
    elif scenario == "wav-duration":
        manifest["track_duration_seconds"] = round(
            float(manifest["track_duration_seconds"]) + 0.01,
            2,
        )
    else:  # pragma: no cover - generated scenarios are closed above
        raise AssertionError(f"Unhandled generated scenario: {scenario}")

    validation_support._write_json(fixture.manifest_path, manifest)
    return (
        "assembly.stitching"
        if scenario in _STITCHING_SCENARIOS
        else "assembly.wav-integrity"
    )


def _assert_exact_recorded_wav(
    fixture: validation_support.ValidationFixture,
    state: _AssemblyState,
) -> None:
    manifest = state.manifest
    current = (
        fixture.workspace / str(manifest["track_audio_path"])
    ).read_bytes()
    assert current == state.expected_wav
    assert len(current) == manifest["track_audio_byte_count"]
    assert sha256_bytes(current) == manifest["track_audio_sha256"]

    with wave.open(BytesIO(current), "rb") as handle:
        assert (
            handle.getframerate(),
            handle.getsampwidth() * 8,
            handle.getnchannels(),
            handle.getcomptype(),
        ) == (24000, 16, 1, "NONE")
        frame_count = handle.getnframes()
        assert handle.readframes(frame_count) == state.expected_lpcm

    assert len(state.expected_lpcm) == frame_count * 2
    assert manifest["track_duration_seconds"] == round(frame_count / 24000, 2)


def test_property_10_assembly_integrity_is_preserved(tmp_path):
    """Feature: audiobook-production-workflow, Property 10: Assembly integrity is preserved.

    **Validates: Requirements 10.10, 10.11, 10.12**
    """

    assert GENERATED_CASES >= 100
    cases = _generated_cases(random.Random(PROPERTY_SEED))
    assert len(cases) == GENERATED_CASES
    print(f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; cases={GENERATED_CASES}")

    observed_scenarios: set[str] = set()
    for case in cases:
        observed_scenarios.add(case.scenario)
        context = (
            f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; case={case.case_index}; "
            f"input={case!r}"
        )
        try:
            fixture = validation_support._fixture(
                tmp_path / f"case-{case.case_index:03d}"
            )
            state = _prepare_valid_assembly(fixture, case)
            _assert_exact_recorded_wav(fixture, state)
            expected_blocked_check = _mutate_case(fixture, state, case)

            evidence = validation_support._validate(fixture)
            stitching = validation_support._check(evidence, "assembly.stitching")
            wav_integrity = validation_support._check(
                evidence,
                "assembly.wav-integrity",
            )
            if expected_blocked_check is None:
                assert stitching.status is ValidationStatus.PASSED
                assert wav_integrity.status is ValidationStatus.PASSED
                assert evidence.status is ValidationStatus.PASSED
                assert evidence.delivery_gate_passed is True
            else:
                blocked = validation_support._check(evidence, expected_blocked_check)
                other = (
                    wav_integrity
                    if expected_blocked_check == "assembly.stitching"
                    else stitching
                )
                assert blocked.status is ValidationStatus.BLOCKED
                assert blocked.finding_count >= 1
                assert other.status is ValidationStatus.PASSED
                assert evidence.status is ValidationStatus.BLOCKED
                assert evidence.delivery_gate_passed is False
        except Exception as exc:
            exc.add_note(context)
            raise

    assert observed_scenarios == set(_SCENARIOS)
    assert observed_scenarios == _STITCHING_SCENARIOS | _WAV_SCENARIOS | {"valid"}
