"""Deterministic generated checks for audiobook production correctness Property 7."""

from __future__ import annotations

import base64
import json
import random
import socket
import subprocess
import urllib.request
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path
from types import SimpleNamespace

import pytest

import frontier_audiobook.production_worker as worker_module
from frontier_audiobook import narrate
from frontier_audiobook.config import NovaSettings
from frontier_audiobook.errors import InputError
from frontier_audiobook.narrate import (
    NarrationSegmentIdentity,
    TrackSourceSnapshot,
    narrate_track,
    segment_spoken_text,
)
from frontier_audiobook.nova import NovaRenderResult
from frontier_audiobook.production_models import (
    PaidAuthorization,
    StrictRecordCodec,
    canonical_sha256,
    seal_record,
)
from frontier_audiobook.production_resume import (
    DuplicateChargeDecision,
    ExactDuplicateChargeAcknowledgement,
    ManualResolutionDisposition,
    ManualResolutionResult,
    ResumeClassification,
    create_exact_duplicate_charge_acknowledgement,
    inspect_resume,
    resolve_resume,
    validate_replacement_paid_attempt_requirements,
)
from frontier_audiobook.util import read_json, sha256_bytes, sha256_text

import test_production_resume as resume_support


PROPERTY_TAG = "Feature: audiobook-production-workflow, Property 7: Reuse and resume never create unapproved calls"
PROPERTY_SEED = 0xA0D10B07
GENERATED_CASES = 100
OFFLINE_RECOVERY_CASES = 15

# **Validates: Requirements 4.5, 8.4, 8.5, 8.6, 9.1, 9.2, 9.3,
# 9.4, 9.5, 9.6, 9.7, 9.8, 9.9, 9.10, 9.11**

_REUSE_MUTATIONS = (
    "none",
    "audio-artifact",
    "transcript-artifact",
    "event-journal",
    "config-binding",
    "partial-turn",
)
_CALL_GATE_SCENARIOS = (
    "call-valid",
    "call-plan",
    "call-config",
    "call-source",
    "call-runtime",
    "call-consumption",
    "call-authorization-artifact",
    "call-authorization-binding",
    "call-profile",
    "call-progress",
    "call-segment",
    "call-bound",
    "assembly-valid",
    "assembly-plan",
    "assembly-config",
    "assembly-source",
    "assembly-runtime",
)
_RECOVERY_MUTATIONS = (
    "complete",
    "missing-runtime",
    "audio-artifact",
    "event-journal",
    "config",
    "render-partition",
)
_REPLACEMENT_SCENARIOS = (
    "valid-exact-acknowledgement",
    "missing-acknowledgement",
    "wrong-acknowledgement",
    "old-transaction",
    "old-plan-id",
    "old-preflight",
    "old-authorization",
    "authorization-plan-binding",
    "authorization-preflight-binding",
    "authorization-command-binding",
    "authorization-call-bound",
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
_TOKENS_PER_SYNTHETIC_RENDER = 18
_FRESH_REQUIREMENTS = (
    "new-transaction",
    "new-plan",
    "new-preflight",
    "new-authorization",
)


@dataclass(frozen=True, slots=True)
class _GeneratedCase:
    case_index: int
    segment_count: int
    reuse_mutations: tuple[str, ...]
    gate_scenario: str
    recovery_mutation: str
    replacement_scenario: str
    nonce: int


@dataclass(frozen=True, slots=True)
class _NarrationConfig:
    workspace_root: Path
    nova: NovaSettings
    normalization: str = "frontier-word-sequence-v1"


class _SyntheticSource:
    def __init__(self, snapshot: TrackSourceSnapshot):
        self.snapshot = snapshot
        self.read_count = 0

    @property
    def track_id(self) -> str:
        return self.snapshot.track_id

    def read(self) -> TrackSourceSnapshot:
        self.read_count += 1
        return self.snapshot


class _GateSource:
    def __init__(self, events: list[str], *, fail: bool):
        self.events = events
        self.fail = fail

    def read(self) -> object:
        self.events.append("source")
        if self.fail:
            raise InputError("generated source drift")
        return object()


@pytest.fixture(autouse=True)
def deny_external_paid_and_child_boundaries(monkeypatch: pytest.MonkeyPatch) -> None:
    """Fail immediately if Property 7 crosses any external or paid boundary."""

    def blocked(*_args, **_kwargs):
        raise AssertionError("Property 7 must remain local, offline, and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(subprocess, "Popen", blocked)
    monkeypatch.setattr(urllib.request, "urlopen", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.setenv("AWS_PROFILE", "frontier-audiobook")
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.delenv(name, raising=False)


def _generated_cases() -> tuple[_GeneratedCase, ...]:
    rng = random.Random(PROPERTY_SEED)
    cases: list[_GeneratedCase] = []
    for case_index in range(GENERATED_CASES):
        segment_count = 1 + rng.randrange(5)
        if case_index % 20 == 0:
            mutations = ("none",) * segment_count
        elif case_index % 20 == 1:
            mutations = tuple(
                _REUSE_MUTATIONS[1 + (offset % (len(_REUSE_MUTATIONS) - 1))]
                for offset in range(segment_count)
            )
        else:
            mutations = tuple(
                _REUSE_MUTATIONS[
                    (case_index + offset + rng.randrange(len(_REUSE_MUTATIONS)))
                    % len(_REUSE_MUTATIONS)
                ]
                for offset in range(segment_count)
            )
        cases.append(
            _GeneratedCase(
                case_index=case_index,
                segment_count=segment_count,
                reuse_mutations=mutations,
                gate_scenario=_CALL_GATE_SCENARIOS[
                    case_index % len(_CALL_GATE_SCENARIOS)
                ],
                recovery_mutation=_RECOVERY_MUTATIONS[
                    case_index % len(_RECOVERY_MUTATIONS)
                ],
                replacement_scenario=_REPLACEMENT_SCENARIOS[
                    case_index % len(_REPLACEMENT_SCENARIOS)
                ],
                nonce=rng.getrandbits(64),
            )
        )
    return tuple(cases)


def _sentences(case: _GeneratedCase) -> tuple[str, ...]:
    values: list[str] = []
    for segment_index in range(case.segment_count):
        start = (case.case_index * 7 + segment_index * 11) % len(_WORDS)
        words = tuple(_WORDS[(start + offset) % len(_WORDS)] for offset in range(5))
        values.append(f"{' '.join(words)} {case.case_index} {segment_index}.")
    return tuple(values)


def _narration_config(workspace: Path) -> _NarrationConfig:
    return _NarrationConfig(
        workspace_root=workspace,
        nova=NovaSettings(
            model_id="amazon.nova-2-sonic-v1:0",
            region="us-east-1",
            sample_rate_hz=24000,
            sample_size_bits=16,
            channels=1,
            max_tokens=8192,
            top_p=0.9,
            temperature=0.0,
            stream_timeout_seconds=120,
            system_prompt="local synthetic property fixture",
        ),
    )


def _output_events(transcript: str, lpcm: bytes) -> tuple[dict[str, object], ...]:
    identity = {
        "sessionId": "property-seven-session",
        "promptName": "property-seven-prompt",
        "completionId": "property-seven-completion",
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
                "totalInputTokens": 7,
                "totalOutputTokens": 11,
                "totalTokens": _TOKENS_PER_SYNTHETIC_RENDER,
                "details": {},
            }
        },
        {"completionEnd": {**identity, "stopReason": "END_TURN"}},
    )


def _render_result(text: str, nonce: int) -> NovaRenderResult:
    sample = 1000 + ((sum(text.encode("utf-8")) + nonce) % 2000)
    lpcm = sample.to_bytes(2, "little", signed=True) * 2400
    return NovaRenderResult(
        audio_lpcm=lpcm,
        final_transcript=text,
        events=_output_events(text, lpcm),
        completion_stop_reason="END_TURN",
    )


def _event_path(workspace: Path, entry: dict[str, object]) -> Path:
    audio_path = workspace / str(entry["audio_path"])
    return audio_path.parent.parent / "events" / f"{audio_path.stem}.jsonl"


def _journal_total(path: Path) -> int:
    totals = []
    for line in path.read_text(encoding="utf-8").splitlines():
        value = json.loads(line)
        if "usageEvent" in value:
            totals.append(value["usageEvent"]["totalTokens"])
    assert totals
    assert all(type(value) is int for value in totals)
    return int(totals[-1])


def _write_manifest(path: Path, value: dict[str, object]) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")),
        encoding="utf-8",
    )


def _exercise_reuse_partition(
    case: _GeneratedCase,
    workspace: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> set[str]:
    workspace.mkdir(parents=True)
    spoken = " ".join(_sentences(case))
    snapshot = TrackSourceSnapshot(
        track_id=f"track-{case.case_index:03d}",
        source_path=f"sources/property-seven-{case.case_index:03d}.md",
        source_sha256=sha256_text(spoken),
        revision_sha256=sha256_text(f"revision:{spoken}"),
        spoken_text=spoken,
        manifest_metadata={"property_case": case.case_index},
    )
    source = _SyntheticSource(snapshot)
    config = _narration_config(workspace)
    segments = segment_spoken_text(spoken, max_words=7)
    assert len(segments) == case.segment_count
    baseline_identities = tuple(
        NarrationSegmentIdentity(
            segment.segment_id,
            sha256_text(segment.text),
            sha256_text(f"config-v1:{case.nonce}:{segment_index}"),
        )
        for segment_index, segment in enumerate(segments)
    )
    runtime_root = workspace / "runtime"
    baseline_calls: list[str] = []

    def baseline_render(text, _voice, _settings, *, paid_render_authorized=False, **_kwargs):
        assert paid_render_authorized is True
        baseline_calls.append(text)
        return _render_result(text, case.nonce)

    with monkeypatch.context() as patch:
        patch.setattr(narrate, "render_text", baseline_render)
        baseline = narrate_track(
            config,  # type: ignore[arg-type] - intentional structural local fixture
            source,
            "tiffany",
            runtime_root=runtime_root,
            assembly_name="property-seven.wav",
            paid_render_authorized=True,
            max_words=7,
            maximum_new_calls=case.segment_count,
            segment_identities=baseline_identities,
            require_event_replay=True,
        )
    assert baseline["billable_calls_made"] == case.segment_count
    assert len(baseline_calls) == case.segment_count

    manifest_path = runtime_root / "manifest.json"
    manifest = read_json(manifest_path)
    assert isinstance(manifest, dict)
    entries = manifest["segments"]
    assert isinstance(entries, list)
    second_identities = list(baseline_identities)
    observed_mutations: set[str] = set()
    for segment_index, (entry, mutation) in enumerate(
        zip(entries, case.reuse_mutations, strict=True)
    ):
        assert isinstance(entry, dict)
        observed_mutations.add(mutation)
        if mutation == "audio-artifact":
            audio_path = workspace / str(entry["audio_path"])
            audio_path.write_bytes(audio_path.read_bytes() + b"artifact-drift")
        elif mutation == "transcript-artifact":
            entry["transcript"] = "mutated transcript candidate"
        elif mutation == "event-journal":
            with _event_path(workspace, entry).open("a", encoding="utf-8") as handle:
                handle.write("{not-valid-json}\n")
        elif mutation == "config-binding":
            prior = baseline_identities[segment_index]
            second_identities[segment_index] = NarrationSegmentIdentity(
                prior.segment_id,
                prior.text_sha256,
                sha256_text(f"config-v2:{case.nonce}:{segment_index}"),
            )
        elif mutation == "partial-turn":
            entry["mid_sentence_partial_turns"] = 1
        else:
            assert mutation == "none"
    _write_manifest(manifest_path, manifest)

    nonreusable = tuple(
        segment.text
        for segment, mutation in zip(segments, case.reuse_mutations, strict=True)
        if mutation != "none"
    )
    reusable = tuple(
        segment.text
        for segment, mutation in zip(segments, case.reuse_mutations, strict=True)
        if mutation == "none"
    )
    calls: list[str] = []
    guarded_calls: list[tuple[str, int]] = []
    assembly_checks = 0
    source.read_count = 0

    def local_render(text, _voice, _settings, *, paid_render_authorized=False, **_kwargs):
        assert paid_render_authorized is True
        calls.append(text)
        return _render_result(text, case.nonce ^ 0x5A5A5A5A)

    def before_model_call(_segment, identity, calls_made, _manifest_path):
        guarded_calls.append((identity.segment_id, calls_made))
        assert calls_made == len(guarded_calls) - 1

    def before_assembly():
        nonlocal assembly_checks
        assembly_checks += 1

    with monkeypatch.context() as patch:
        patch.setattr(narrate, "render_text", local_render)
        result = narrate_track(
            config,  # type: ignore[arg-type] - intentional structural local fixture
            source,
            "tiffany",
            runtime_root=runtime_root,
            assembly_name="property-seven.wav",
            paid_render_authorized=True,
            max_words=7,
            maximum_new_calls=len(nonreusable),
            segment_identities=tuple(second_identities),
            require_event_replay=True,
            before_model_call=before_model_call,
            before_assembly=before_assembly,
        )

    assert Counter(calls) == Counter(nonreusable)
    assert all(count == 1 for count in Counter(calls).values())
    assert not (set(calls) & set(reusable))
    assert len(guarded_calls) == len(nonreusable)
    assert result["billable_calls_made"] == len(nonreusable)
    assert result["segments_rendered"] == len(nonreusable)
    assert result["segments_reused"] == len(reusable)
    assert assembly_checks == 1
    assert source.read_count == 2 + len(nonreusable)

    final_manifest = read_json(manifest_path)
    assert isinstance(final_manifest, dict)
    final_entries = final_manifest["segments"]
    assert isinstance(final_entries, list)
    current_execution_tokens = 0
    reused_current_execution_tokens = 0
    for entry, mutation in zip(final_entries, case.reuse_mutations, strict=True):
        assert isinstance(entry, dict)
        journal_tokens = _journal_total(_event_path(workspace, entry))
        if mutation == "none":
            assert entry["rendered_in_current_attempt"] is False
            assert str(entry["text"]) not in calls
            reused_current_execution_tokens += 0
        else:
            assert entry["rendered_in_current_attempt"] is True
            assert calls.count(str(entry["text"])) == 1
            current_execution_tokens += journal_tokens
    assert final_manifest["billable_calls_made"] == len(nonreusable)
    assert reused_current_execution_tokens == 0
    assert current_execution_tokens == len(nonreusable) * _TOKENS_PER_SYNTHETIC_RENDER
    return observed_mutations


def _exercise_revalidation_gate(
    case: _GeneratedCase,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    scenario = case.gate_scenario
    events: list[str] = []
    plan = object()
    catalog = object()
    config = object()
    authorization = object()
    source = _GateSource(events, fail=scenario in {"call-source", "assembly-source"})
    track_plan = SimpleNamespace(
        track_id="chapter-001",
        source=SimpleNamespace(segments=(SimpleNamespace(segment_id="segment-001"),)),
        effective_config=SimpleNamespace(profile_label="frontier-audiobook"),
    )
    guard = worker_module._WorkerGuard(
        workspace_root=tmp_path,
        plan_path=tmp_path / "plan.json",
        plan=plan,  # type: ignore[arg-type] - gate isolation fixture
        track_plan=track_plan,  # type: ignore[arg-type] - gate isolation fixture
        catalog_track=catalog,  # type: ignore[arg-type] - gate isolation fixture
        source=source,  # type: ignore[arg-type] - gate isolation fixture
        store=object(),  # type: ignore[arg-type] - gate isolation fixture
        runtime_config_path=tmp_path / "audition.toml",
        runtime_sha256="1" * 64,
        authorization_sha256="2" * 64,
        maximum_new_calls=0 if scenario == "call-bound" else 1,
        preflight_sha256="3" * 64,
        clock=lambda: worker_module.datetime(
            2026, 9, 14, 12, 0, tzinfo=worker_module.UTC
        ),
    )
    would_call_or_assemble = 0

    with monkeypatch.context() as patch:
        patch.setenv(
            "AWS_PROFILE",
            "wrong-profile" if scenario == "call-profile" else "frontier-audiobook",
        )

        def load_plan(_path):
            events.append("plan")
            return object() if scenario in {"call-plan", "assembly-plan"} else plan

        def load_config(_root, _plan):
            events.append("config")
            return tmp_path / "production.toml", config

        def select_catalog(_config, _track):
            events.append("catalog")
            return object() if scenario in {"call-config", "assembly-config"} else catalog

        def runtime_fingerprint(_path):
            events.append("runtime")
            return "9" * 64 if scenario in {"call-runtime", "assembly-runtime"} else "1" * 64

        def consumption(_store, _plan, _track):
            events.append("consumption")
            if scenario == "call-consumption":
                return "8" * 64, 1, "3" * 64
            return "2" * 64, guard.maximum_new_calls, "3" * 64

        def load_authorization(_plan_path, _expected):
            events.append("authorization-artifact")
            if scenario == "call-authorization-artifact":
                raise InputError("generated authorization artifact drift")
            return authorization

        def validate_authorization(*_args, **_kwargs):
            events.append("authorization-binding")
            if scenario == "call-authorization-binding":
                raise InputError("generated authorization binding drift")

        def validate_progress(*_args, **_kwargs):
            events.append("progress")
            if scenario == "call-progress":
                raise InputError("generated runtime progress drift")

        patch.setattr(worker_module, "load_production_plan", load_plan)
        patch.setattr(worker_module, "_load_current_config", load_config)
        patch.setattr(worker_module, "_selected_catalog_track", select_catalog)
        patch.setattr(worker_module, "_runtime_fingerprint", runtime_fingerprint)
        patch.setattr(worker_module, "_authorization_consumption", consumption)
        patch.setattr(worker_module, "_load_authorization_artifact", load_authorization)
        patch.setattr(worker_module, "_validate_authorization", validate_authorization)
        patch.setattr(worker_module, "_validate_runtime_progress", validate_progress)

        valid = scenario in {"call-valid", "assembly-valid"}
        try:
            if scenario.startswith("assembly-"):
                guard.before_assembly()
            else:
                identity = NarrationSegmentIdentity(
                    "segment-999" if scenario == "call-segment" else "segment-001",
                    "4" * 64,
                    "5" * 64,
                )
                guard.before_model_call(
                    SimpleNamespace(),  # type: ignore[arg-type] - ignored by guard
                    identity,
                    0,
                    tmp_path / "manifest.json",
                )
        except InputError:
            assert not valid
        else:
            assert valid
            would_call_or_assemble += 1

    assert would_call_or_assemble == (1 if scenario in {"call-valid", "assembly-valid"} else 0)
    if scenario == "call-valid":
        assert events == [
            "plan",
            "config",
            "catalog",
            "source",
            "runtime",
            "consumption",
            "authorization-artifact",
            "authorization-binding",
            "progress",
        ]
    elif scenario == "assembly-valid":
        assert events == ["plan", "config", "catalog", "source", "runtime"]


def _mutate_recovery_fixture(
    mutation: str,
    workspace: Path,
    config_path: Path,
    runtime: Path,
) -> None:
    if mutation in {"complete", "missing-runtime"}:
        return
    manifest_path = runtime / "manifest.json"
    manifest = read_json(manifest_path)
    assert isinstance(manifest, dict)
    entries = manifest["segments"]
    assert isinstance(entries, list) and len(entries) == 1
    entry = entries[0]
    assert isinstance(entry, dict)
    if mutation == "audio-artifact":
        audio_path = workspace / str(entry["audio_path"])
        audio_path.write_bytes(audio_path.read_bytes() + b"mutated")
    elif mutation == "event-journal":
        with _event_path(workspace, entry).open("a", encoding="utf-8") as handle:
            handle.write("{not-valid-json}\n")
    elif mutation == "config":
        config_path.write_text(
            config_path.read_text(encoding="utf-8") + "\n# generated config drift\n",
            encoding="utf-8",
        )
    else:
        assert mutation == "render-partition"
        entry["rendered_in_current_attempt"] = "ambiguous"
        _write_manifest(manifest_path, manifest)


def _exercise_offline_recovery(
    case: _GeneratedCase,
    workspace: Path,
) -> ManualResolutionResult:
    complete_runtime = case.recovery_mutation != "missing-runtime"
    (
        config_path,
        plan_path,
        _plan,
        track,
        store,
        runtime,
        protected,
    ) = resume_support._uncertain_fixture(workspace, complete_runtime=complete_runtime)
    _mutate_recovery_fixture(
        case.recovery_mutation,
        workspace,
        config_path,
        runtime,
    )
    transaction = store.transaction_path(track.track_id, track.transaction_id)
    attempts = transaction / "attempts"
    before_attempts = resume_support._tree_bytes(attempts)
    before_runtime = resume_support._tree_bytes(runtime)
    before_protected = protected.read_bytes()
    before_plan = plan_path.read_bytes()
    before_config = config_path.read_bytes()

    inspection = inspect_resume(
        workspace,
        plan_path,
        track.track_id,
        track.transaction_id,
    )
    if case.recovery_mutation == "complete":
        assert inspection.classification is ResumeClassification.COMPLETE_ARTIFACTS_RECOVERABLE
        disposition = ManualResolutionDisposition.ACCEPT_COMPLETE_LOCAL_ARTIFACTS
    else:
        assert inspection.classification in {
            ResumeClassification.CHARGE_UNCERTAIN_REVIEW_REQUIRED,
            ResumeClassification.BLOCKED_NEW_PLAN_REQUIRED,
        }
        disposition = (
            ManualResolutionDisposition.QUARANTINE_INVALID_ARTIFACTS
            if case.case_index % 2
            else ManualResolutionDisposition.ABANDON_UNCERTAIN_ATTEMPT
        )

    result = resolve_resume(
        workspace,
        plan_path,
        track.track_id,
        track.transaction_id,
        disposition,
        occurred_at_utc="2026-09-14T12:00:06Z",
    )
    event_count = len(store.inspect_transaction(track.track_id, track.transaction_id).events)
    repeated = resolve_resume(
        workspace,
        plan_path,
        track.track_id,
        track.transaction_id,
        disposition,
        occurred_at_utc="2026-09-14T23:59:59Z",
    )
    assert repeated == result
    assert len(store.inspect_transaction(track.track_id, track.transaction_id).events) == event_count
    assert result.evidence_retained is True
    assert resume_support._tree_bytes(attempts) == before_attempts
    assert resume_support._tree_bytes(runtime) == before_runtime
    assert protected.read_bytes() == before_protected
    assert plan_path.read_bytes() == before_plan
    assert config_path.read_bytes() == before_config
    if case.recovery_mutation == "complete":
        assert result.future_paid_attempt_requirements == ()
    else:
        assert result.future_paid_attempt_requirements == _FRESH_REQUIREMENTS
        assert result.duplicate_charge_acknowledgement_required is True
    return result


def _wrong_acknowledgement(
    acknowledgement: ExactDuplicateChargeAcknowledgement,
) -> ExactDuplicateChargeAcknowledgement:
    retained_attempt_sha256 = (
        "6" * 64
        if acknowledgement.retained_attempt_sha256 != "6" * 64
        else "7" * 64
    )
    binding_sha256 = canonical_sha256(
        {
            "schema": "frontier-duplicate-charge-acknowledgement-v1",
            "prior_transaction_id": acknowledgement.prior_transaction_id,
            "retained_attempt_sha256": retained_attempt_sha256,
        }
    )
    return seal_record(
        replace(
            acknowledgement,
            retained_attempt_sha256=retained_attempt_sha256,
            binding_sha256=binding_sha256,
            canonical_sha256="",
        )
    )


def _exercise_replacement_requirements(
    cases: tuple[_GeneratedCase, ...],
    workspace: Path,
    accepted_subject: ManualResolutionResult,
) -> set[str]:
    (
        _config,
        original_plan_path,
        original_plan,
        track,
        _store,
        _runtime,
        _protected,
    ) = resume_support._uncertain_fixture(workspace, complete_runtime=False)
    subject = resolve_resume(
        workspace,
        original_plan_path,
        track.track_id,
        track.transaction_id,
        ManualResolutionDisposition.ABANDON_UNCERTAIN_ATTEMPT,
        occurred_at_utc="2026-09-14T12:00:06Z",
    )
    assert subject.future_paid_attempt_requirements == _FRESH_REQUIREMENTS
    assert subject.duplicate_charge_acknowledgement_required is True

    _replacement_path, replacement_plan = resume_support._create_plan(
        workspace,
        "plan-property-seven-replacement",
    )
    replacement_preflight = "1" * 64
    replacement_authorization = resume_support._authorization(
        replacement_plan,
        replacement_preflight,
        "authorization-property-seven-replacement",
    )
    original_authorization = StrictRecordCodec(PaidAuthorization).load(
        original_plan_path.parent
        / "authorizations"
        / "authorization-resume-test.json"
    )
    acknowledgement = create_exact_duplicate_charge_acknowledgement(
        subject,
        DuplicateChargeDecision.ACKNOWLEDGE_EXACT_RETAINED_ATTEMPT,
        acknowledged_at_utc="2026-09-14T12:00:07Z",
    )
    wrong_acknowledgement = _wrong_acknowledgement(acknowledgement)
    old_id_plan = seal_record(
        replace(
            replacement_plan,
            plan_id=subject.plan_id,
            canonical_sha256="",
        )
    )
    authorization_plan_binding = seal_record(
        replace(
            replacement_authorization,
            plan_sha256=subject.plan_sha256,
            canonical_sha256="",
        )
    )
    authorization_preflight_binding = seal_record(
        replace(
            replacement_authorization,
            preflight_sha256=subject.preflight_sha256 or ("8" * 64),
            canonical_sha256="",
        )
    )
    authorization_command_binding = seal_record(
        replace(
            replacement_authorization,
            exact_command_sha256s=("9" * 64,),
            canonical_sha256="",
        )
    )
    replacement_track = replacement_plan.tracks[0]
    authorization_call_bound = seal_record(
        replace(
            replacement_authorization,
            maximum_new_calls_by_track={
                replacement_track.track_id: replacement_track.maximum_new_calls + 1
            },
            maximum_new_calls_total=replacement_track.maximum_new_calls + 1,
            canonical_sha256="",
        )
    )

    no_charge_subject = seal_record(
        replace(
            subject,
            duplicate_charge_acknowledgement_required=False,
            duplicate_charge_binding_sha256=None,
            canonical_sha256="",
        )
    )
    validate_replacement_paid_attempt_requirements(
        no_charge_subject,
        replacement_plan,
        replacement_preflight,
        replacement_authorization,
        None,
    )
    with pytest.raises(InputError, match="Unexpected duplicate-charge acknowledgement"):
        validate_replacement_paid_attempt_requirements(
            no_charge_subject,
            replacement_plan,
            replacement_preflight,
            replacement_authorization,
            acknowledgement,
        )

    observed: set[str] = set()
    for case in cases:
        scenario = case.replacement_scenario
        observed.add(scenario)
        arguments = [
            subject,
            replacement_plan,
            replacement_preflight,
            replacement_authorization,
            acknowledgement,
        ]
        if scenario == "missing-acknowledgement":
            arguments[4] = None
        elif scenario == "wrong-acknowledgement":
            arguments[4] = wrong_acknowledgement
        elif scenario == "old-transaction":
            arguments[1] = original_plan
        elif scenario == "old-plan-id":
            arguments[1] = old_id_plan
        elif scenario == "old-preflight":
            arguments[2] = subject.preflight_sha256
        elif scenario == "old-authorization":
            arguments[3] = original_authorization
        elif scenario == "authorization-plan-binding":
            arguments[3] = authorization_plan_binding
        elif scenario == "authorization-preflight-binding":
            arguments[3] = authorization_preflight_binding
        elif scenario == "authorization-command-binding":
            arguments[3] = authorization_command_binding
        elif scenario == "authorization-call-bound":
            arguments[3] = authorization_call_bound
        else:
            assert scenario == "valid-exact-acknowledgement"

        if scenario == "valid-exact-acknowledgement":
            validate_replacement_paid_attempt_requirements(*arguments)  # type: ignore[arg-type]
        else:
            with pytest.raises(InputError):
                validate_replacement_paid_attempt_requirements(*arguments)  # type: ignore[arg-type]

    with pytest.raises(InputError, match="does not permit another paid attempt"):
        validate_replacement_paid_attempt_requirements(
            accepted_subject,
            replacement_plan,
            replacement_preflight,
            replacement_authorization,
            None,
        )
    return observed


def test_reuse_and_resume_never_create_unapproved_calls(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Feature: audiobook-production-workflow, Property 7: Reuse and resume never create unapproved calls"""

    assert GENERATED_CASES >= 100
    cases = _generated_cases()
    assert len(cases) == GENERATED_CASES
    print(f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; cases={GENERATED_CASES}")

    observed_mutations: set[str] = set()
    observed_gates: set[str] = set()
    for case in cases:
        context = (
            f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; case={case.case_index}; "
            f"input={case!r}"
        )
        try:
            observed_mutations.update(
                _exercise_reuse_partition(
                    case,
                    tmp_path / f"reuse-{case.case_index:03d}",
                    monkeypatch,
                )
            )
            _exercise_revalidation_gate(case, tmp_path, monkeypatch)
            observed_gates.add(case.gate_scenario)
        except Exception as exc:
            exc.add_note(context)
            raise

    assert observed_mutations == set(_REUSE_MUTATIONS)
    assert observed_gates == set(_CALL_GATE_SCENARIOS)

    observed_recovery_mutations: set[str] = set()
    accepted_subject: ManualResolutionResult | None = None
    for case in cases[:OFFLINE_RECOVERY_CASES]:
        observed_recovery_mutations.add(case.recovery_mutation)
        try:
            recovery_result = _exercise_offline_recovery(
                case,
                tmp_path / f"recovery-{case.case_index:03d}",
            )
            if recovery_result.future_paid_attempt_requirements == ():
                accepted_subject = recovery_result
        except Exception as exc:
            exc.add_note(
                f"{PROPERTY_TAG}; seed={PROPERTY_SEED}; offline-recovery-case="
                f"{case.case_index}; input={case!r}"
            )
            raise
    assert observed_recovery_mutations == set(_RECOVERY_MUTATIONS)
    assert accepted_subject is not None

    observed_replacement_scenarios = _exercise_replacement_requirements(
        cases,
        tmp_path / "replacement-requirements",
        accepted_subject,
    )
    assert observed_replacement_scenarios == set(_REPLACEMENT_SCENARIOS)
