"""Deterministic generated checks for audiobook production correctness Property 9."""

from __future__ import annotations

import base64
import random
import socket
import subprocess
import urllib.request
import wave
from collections import Counter
from dataclasses import dataclass
from io import BytesIO

import pytest

from frontier_audiobook import narrate
from frontier_audiobook.production_models import ValidationStatus
from frontier_audiobook.production_validation import validate_frozen_track_manifest
from frontier_audiobook.util import sha256_bytes
from frontier_audiobook.verify import normalized_tokens

import test_production_validation as validation_support


PROPERTY_TAG = (
    "Feature: audiobook-production-workflow, Property 9: "
    "Exact transcript and LPCM replay are preserved"
)
PROPERTY_SEED = 0xA0D10B09
GENERATED_CASES = 120

# **Validates: Requirements 10.6, 10.7, 10.8, 10.12**

_SCENARIOS = (
    "valid",
    "valid-normalized-transcript",
    "valid-multi-audio-block",
    "transcript-token-delete",
    "transcript-token-substitute",
    "transcript-token-add",
    "exact-match-record",
    "coverage-record",
    "transcript-manifest-binding",
    "event-final-token",
    "event-content-correlation",
    "event-prompt-correlation",
    "event-incomplete",
    "audio-block-bytes",
    "audio-block-order",
    "audio-hash",
    "transcript-hash",
    "event-hash",
    "partial-count-record",
    "partial-turn-event",
)
_VALID_SCENARIOS = frozenset(
    {"valid", "valid-normalized-transcript", "valid-multi-audio-block"}
)
_EXPECTED_BLOCKED_CHECK = {
    "transcript-token-delete": "fidelity.exact-transcript",
    "transcript-token-substitute": "fidelity.exact-transcript",
    "transcript-token-add": "fidelity.exact-transcript",
    "exact-match-record": "fidelity.exact-transcript",
    "coverage-record": "fidelity.exact-transcript",
    "transcript-manifest-binding": "fidelity.hash-bindings",
    "event-final-token": "fidelity.event-replay",
    "event-content-correlation": "fidelity.event-replay",
    "event-prompt-correlation": "fidelity.event-replay",
    "event-incomplete": "fidelity.event-replay",
    "audio-block-bytes": "fidelity.lpcm-equality",
    "audio-block-order": "fidelity.lpcm-equality",
    "audio-hash": "fidelity.hash-bindings",
    "transcript-hash": "fidelity.hash-bindings",
    "event-hash": "fidelity.hash-bindings",
    "partial-count-record": "fidelity.partial-turns",
    "partial-turn-event": "fidelity.partial-turns",
}
_FIDELITY_CHECKS = frozenset(
    {
        "fidelity.hash-bindings",
        "fidelity.exact-transcript",
        "fidelity.event-replay",
        "fidelity.lpcm-equality",
        "fidelity.partial-turns",
    }
)
_MUTATION_DOMAINS = {
    "valid": "valid-control",
    "valid-normalized-transcript": "transcript-tokens",
    "valid-multi-audio-block": "audio-blocks",
    "transcript-token-delete": "transcript-tokens",
    "transcript-token-substitute": "transcript-tokens",
    "transcript-token-add": "transcript-tokens",
    "exact-match-record": "transcript-tokens",
    "coverage-record": "coverage",
    "transcript-manifest-binding": "hashes",
    "event-final-token": "correlated-events",
    "event-content-correlation": "correlated-events",
    "event-prompt-correlation": "correlated-events",
    "event-incomplete": "correlated-events",
    "audio-block-bytes": "audio-blocks",
    "audio-block-order": "audio-blocks",
    "audio-hash": "hashes",
    "transcript-hash": "hashes",
    "event-hash": "hashes",
    "partial-count-record": "partial-turn-counts",
    "partial-turn-event": "partial-turn-counts",
}
_REQUIRED_DOMAINS = frozenset(
    {
        "valid-control",
        "transcript-tokens",
        "correlated-events",
        "audio-blocks",
        "hashes",
        "coverage",
        "partial-turn-counts",
    }
)
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
)


@dataclass(frozen=True, slots=True)
class _GeneratedCase:
    case_index: int
    scenario: str
    segment_index: int
    nonce: int


@pytest.fixture(autouse=True)
def deny_every_external_or_paid_boundary(monkeypatch: pytest.MonkeyPatch) -> None:
    def blocked(*_args, **_kwargs):
        raise AssertionError("Property 9 must remain local and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(subprocess, "Popen", blocked)
    monkeypatch.setattr(urllib.request, "urlopen", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.delenv(name, raising=False)


def _generated_cases(rng: random.Random) -> tuple[_GeneratedCase, ...]:
    assert GENERATED_CASES % len(_SCENARIOS) == 0
    scenarios = list(_SCENARIOS) * (GENERATED_CASES // len(_SCENARIOS))
    rng.shuffle(scenarios)
    return tuple(
        _GeneratedCase(
            case_index=index,
            scenario=scenario,
            segment_index=rng.randrange(2),
            nonce=rng.getrandbits(64),
        )
        for index, scenario in enumerate(scenarios)
    )


def _lpcm_from_wav(raw: bytes) -> bytes:
    with wave.open(BytesIO(raw), "rb") as handle:
        assert handle.getnchannels() == 1
        assert handle.getsampwidth() == 2
        assert handle.getframerate() == 24000
        return handle.readframes(handle.getnframes())


def _split_lpcm(lpcm: bytes, count: int) -> tuple[bytes, ...]:
    assert len(lpcm) % 2 == 0
    frame_count = len(lpcm) // 2
    assert 1 < count <= frame_count
    blocks = tuple(
        lpcm[(frame_count * index // count) * 2 : (frame_count * (index + 1) // count) * 2]
        for index in range(count)
    )
    assert all(blocks)
    assert b"".join(blocks) == lpcm
    return blocks


def _events_for_audio_blocks(
    transcript: str,
    blocks: tuple[bytes, ...],
) -> tuple[dict[str, object], ...]:
    assert blocks and all(blocks)
    baseline = list(validation_support._output_events(transcript, b"".join(blocks)))
    audio_start_index = next(
        index
        for index, event in enumerate(baseline)
        if isinstance(event.get("contentStart"), dict)
        and event["contentStart"].get("type") == "AUDIO"
    )
    final_text_index = next(
        index
        for index, event in enumerate(baseline)
        if isinstance(event.get("contentStart"), dict)
        and event["contentStart"].get("type") == "TEXT"
    )
    start_template = baseline[audio_start_index]["contentStart"]
    output_template = baseline[audio_start_index + 1]["audioOutput"]
    end_template = baseline[audio_start_index + 2]["contentEnd"]
    assert isinstance(start_template, dict)
    assert isinstance(output_template, dict)
    assert isinstance(end_template, dict)

    generated: list[dict[str, object]] = list(baseline[:audio_start_index])
    for ordinal, block in enumerate(blocks, start=1):
        content_id = f"audio-{ordinal}"
        start = dict(start_template)
        start["contentId"] = content_id
        output = dict(output_template)
        output["contentId"] = content_id
        output["content"] = base64.b64encode(block).decode("ascii")
        end = dict(end_template)
        end["contentId"] = content_id
        generated.extend(
            (
                {"contentStart": start},
                {"audioOutput": output},
                {"contentEnd": end},
            )
        )
    generated.extend(baseline[final_text_index:])
    return tuple(generated)


def _event_payload(
    events: tuple[dict[str, object], ...],
    event_name: str,
) -> dict[str, object]:
    for event in events:
        payload = event.get(event_name)
        if isinstance(payload, dict):
            return payload
    raise AssertionError(f"generated journal has no {event_name}")


def _token_mutation(text: str, scenario: str, nonce: int) -> str:
    tokens = list(normalized_tokens(text, "frontier-word-sequence-v1"))
    assert len(tokens) >= 2
    index = nonce % len(tokens)
    replacement = _WORDS[(nonce >> 8) % len(_WORDS)]
    if replacement == tokens[index]:
        replacement = _WORDS[(_WORDS.index(replacement) + 1) % len(_WORDS)]
    if scenario == "transcript-token-delete":
        del tokens[index]
    elif scenario in {"transcript-token-substitute", "event-final-token"}:
        tokens[index] = replacement
    else:
        assert scenario == "transcript-token-add"
        tokens.insert(index, replacement)
    return " ".join(tokens) + "."


def _normalized_equivalent(text: str, nonce: int) -> str:
    tokens = normalized_tokens(text, "frontier-word-sequence-v1")
    rendered = [
        token.upper() if (nonce >> index) & 1 else token.title()
        for index, token in enumerate(tokens)
    ]
    equivalent = " — ".join(rendered) + "!!!"
    assert normalized_tokens(equivalent) == tokens
    return equivalent


def _rewrite_transcript(
    fixture: validation_support.ValidationFixture,
    entry: dict[str, object],
    transcript: str,
) -> None:
    path = fixture.workspace / str(entry["transcript_path"])
    raw = (transcript + "\n").encode("utf-8")
    path.write_bytes(raw)
    entry["transcript"] = transcript
    entry["transcript_sha256"] = sha256_bytes(raw)


def _rewrite_events(
    fixture: validation_support.ValidationFixture,
    entry: dict[str, object],
    events: tuple[dict[str, object], ...],
) -> None:
    path = fixture.workspace / str(entry["event_journal_path"])
    raw = validation_support._event_bytes(events)
    path.write_bytes(raw)
    entry["event_journal_sha256"] = sha256_bytes(raw)


def _wrong_digest(current: object) -> str:
    candidate = "0" * 64
    return "f" * 64 if current == candidate else candidate


def _apply_case(
    fixture: validation_support.ValidationFixture,
    manifest: dict[str, object],
    case: _GeneratedCase,
) -> None:
    entries = manifest["segments"]
    assert isinstance(entries, list) and len(entries) == 2
    entry = entries[case.segment_index]
    assert isinstance(entry, dict)
    expected_text = str(entry["text"])
    audio_path = fixture.workspace / str(entry["audio_path"])
    lpcm = _lpcm_from_wav(audio_path.read_bytes())
    scenario = case.scenario

    if scenario == "valid":
        return
    if scenario == "valid-normalized-transcript":
        transcript = _normalized_equivalent(expected_text, case.nonce)
        _rewrite_transcript(fixture, entry, transcript)
        _rewrite_events(
            fixture,
            entry,
            _events_for_audio_blocks(transcript, (lpcm,)),
        )
        return
    if scenario == "valid-multi-audio-block":
        blocks = _split_lpcm(lpcm, 2 + case.nonce % 3)
        _rewrite_events(
            fixture,
            entry,
            _events_for_audio_blocks(expected_text, blocks),
        )
        return
    if scenario.startswith("transcript-token-"):
        _rewrite_transcript(
            fixture,
            entry,
            _token_mutation(expected_text, scenario, case.nonce),
        )
        return
    if scenario == "exact-match-record":
        entry["exact_transcript_match"] = False
        return
    if scenario == "coverage-record":
        entry["coverage_ratio"] = (1, 2, 3)[case.nonce % 3] / 4
        return
    if scenario == "transcript-manifest-binding":
        entry["transcript"] = _token_mutation(
            expected_text,
            "transcript-token-substitute",
            case.nonce,
        )
        return

    events = _events_for_audio_blocks(expected_text, (lpcm,))
    if scenario == "event-final-token":
        payload = _event_payload(events, "textOutput")
        payload["content"] = _token_mutation(expected_text, scenario, case.nonce)
        _rewrite_events(fixture, entry, events)
    elif scenario == "event-content-correlation":
        payload = _event_payload(events, "audioOutput")
        payload["contentId"] = f"unopened-{case.nonce:x}"
        _rewrite_events(fixture, entry, events)
    elif scenario == "event-prompt-correlation":
        payload = _event_payload(events, "audioOutput")
        payload["promptName"] = f"foreign-prompt-{case.nonce:x}"
        _rewrite_events(fixture, entry, events)
    elif scenario == "event-incomplete":
        assert "completionEnd" in events[-1]
        _rewrite_events(fixture, entry, events[:-1])
    elif scenario == "audio-block-bytes":
        changed = bytearray(lpcm)
        changed[case.nonce % len(changed)] ^= 0x01
        _rewrite_events(
            fixture,
            entry,
            _events_for_audio_blocks(expected_text, (bytes(changed),)),
        )
    elif scenario == "audio-block-order":
        split = 1 + 2 * (case.nonce % ((len(lpcm) - 2) // 2))
        blocks = (lpcm[:split], lpcm[split:])
        assert b"".join(reversed(blocks)) != lpcm
        _rewrite_events(
            fixture,
            entry,
            _events_for_audio_blocks(expected_text, tuple(reversed(blocks))),
        )
    elif scenario == "audio-hash":
        entry["audio_sha256"] = _wrong_digest(entry["audio_sha256"])
    elif scenario == "transcript-hash":
        entry["transcript_sha256"] = _wrong_digest(entry["transcript_sha256"])
    elif scenario == "event-hash":
        entry["event_journal_sha256"] = _wrong_digest(entry["event_journal_sha256"])
    elif scenario == "partial-count-record":
        entry["mid_sentence_partial_turns"] = 1 + case.nonce % 5
    else:
        assert scenario == "partial-turn-event"
        _rewrite_events(
            fixture,
            entry,
            validation_support._output_events(
                expected_text,
                lpcm,
                unsafe_partial_turn=True,
            ),
        )


def _check(evidence, check_id: str):
    return next(check for check in evidence.checks if check.check_id == check_id)


def test_property_9_exact_transcript_and_lpcm_replay_are_preserved(tmp_path) -> None:
    """Feature: audiobook-production-workflow, Property 9: Exact transcript and LPCM replay are preserved"""

    assert GENERATED_CASES >= 100
    print(f"{PROPERTY_TAG}; seed={PROPERTY_SEED:#x}; cases={GENERATED_CASES}")
    generated = _generated_cases(random.Random(PROPERTY_SEED))
    assert len(generated) == GENERATED_CASES

    observed_scenarios: Counter[str] = Counter()
    observed_domains: set[str] = set()
    observed_segments: set[int] = set()
    observed_blocked_checks: set[str] = set()
    for case in generated:
        context = (
            f"{PROPERTY_TAG}; seed={PROPERTY_SEED:#x}; case={case.case_index}; "
            f"input={case!r}"
        )
        try:
            fixture = validation_support._fixture(
                tmp_path / f"case-{case.case_index:03d}"
            )
            protected_before = fixture.protected_path.read_bytes()
            manifest = validation_support._manifest(fixture)
            _apply_case(fixture, manifest, case)
            validation_support._write_json(fixture.manifest_path, manifest)

            evidence = validate_frozen_track_manifest(
                fixture.workspace,
                fixture.plan_path,
                fixture.track.track_id,
                fixture.track.transaction_id,
                validated_at_utc="2026-09-15T12:00:08Z",
                persist=False,
            )

            observed_scenarios[case.scenario] += 1
            observed_domains.add(_MUTATION_DOMAINS[case.scenario])
            observed_segments.add(case.segment_index)
            assert fixture.protected_path.read_bytes() == protected_before, context
            assert _check(evidence, "manifest.schema").status is ValidationStatus.PASSED, context
            if case.scenario in _VALID_SCENARIOS:
                assert evidence.status is ValidationStatus.PASSED, context
                assert evidence.delivery_gate_passed is True, context
                assert all(
                    _check(evidence, check_id).status is ValidationStatus.PASSED
                    for check_id in _FIDELITY_CHECKS
                ), context
            else:
                expected_check = _EXPECTED_BLOCKED_CHECK[case.scenario]
                observed_blocked_checks.add(expected_check)
                assert _check(evidence, expected_check).status is ValidationStatus.BLOCKED, context
                assert evidence.status is ValidationStatus.BLOCKED, context
                assert evidence.delivery_gate_passed is False, context
        except Exception as exc:
            exc.add_note(context)
            raise

    expected_per_scenario = GENERATED_CASES // len(_SCENARIOS)
    assert set(observed_scenarios) == set(_SCENARIOS)
    assert set(observed_scenarios.values()) == {expected_per_scenario}
    assert observed_domains == _REQUIRED_DOMAINS
    assert observed_segments == {0, 1}
    assert observed_blocked_checks == _FIDELITY_CHECKS
