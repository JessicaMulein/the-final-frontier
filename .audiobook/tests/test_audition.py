from __future__ import annotations

import asyncio
import base64
import concurrent.futures
import copy
import json
import os
import re
import shutil
import socket
import subprocess
import tempfile
import threading
import time
import uuid
import venv
import zipfile
from pathlib import Path
from types import SimpleNamespace

import pytest

import frontier_audiobook.audition as audition
import frontier_audiobook.nova as nova
from frontier_audiobook.config import load_audition_config
from frontier_audiobook.errors import FidelityMismatch, InputError
from frontier_audiobook.nova import (
    NovaRenderResult,
    _invoke_session,
    _receive_events,
    _run_worker_process,
    render_text,
    replay_output_events,
)
from frontier_audiobook.util import atomic_write_json, read_json, resolve_inside, sha256_file
from frontier_audiobook.verify import compare_transcript


WORKSPACE = Path(__file__).resolve().parents[2]
AUDIOBOOK_ROOT = WORKSPACE / ".audiobook"
CONFIG_PATH = AUDIOBOOK_ROOT / "config" / "audition.toml"


def _hanging_process_worker(connection):
    try:
        time.sleep(60)
    finally:
        connection.close()


def _result_process_worker(connection, value):
    try:
        connection.send(("result", value))
    finally:
        connection.close()


@pytest.fixture(autouse=True)
def deny_python_network(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("offline tests must not open a network connection")

    async def blocked_native_render(*_args, **_kwargs):
        raise AssertionError("offline tests must not construct the AWS CRT transport")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(nova, "_render_async", blocked_native_render)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    for name in (
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AWS_SESSION_TOKEN",
        "AWS_PROFILE",
        "AWS_DEFAULT_PROFILE",
    ):
        monkeypatch.delenv(name, raising=False)


@pytest.fixture
def isolated_config():
    parent = AUDIOBOOK_ROOT / "build" / "pytest"
    parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=parent) as temporary:
        root = Path(temporary)
        config_path = root / "audition.toml"
        raw = CONFIG_PATH.read_text(encoding="utf-8")
        output_relative = (root / "build").relative_to(WORKSPACE).as_posix()
        package_relative = (root / "dist").relative_to(WORKSPACE).as_posix()
        raw = raw.replace(
            'output_root = ".audiobook/build/auditions"',
            f'output_root = "{output_relative}"',
        ).replace(
            'package_root = ".audiobook/dist/auditions"',
            f'package_root = "{package_relative}"',
        )
        config_path.write_text(raw, encoding="utf-8")
        yield load_audition_config(config_path, WORKSPACE)


def _plan(isolated_config) -> Path:
    return audition.create_plan(isolated_config, "test-" + uuid.uuid4().hex[:12])


def _ids(prompt_name: str = "prompt-1") -> dict[str, str]:
    return {
        "sessionId": "session-1",
        "promptName": prompt_name,
        "completionId": "completion-1",
    }


def _output_events(
    transcript: str,
    audio: bytes = b"\0\0" * 2400,
    *,
    text_chunks: tuple[str, ...] | None = None,
    prompt_name: str = "prompt-1",
) -> tuple[dict[str, object], ...]:
    identity = _ids(prompt_name)
    chunks = text_chunks or (transcript,)
    events: list[dict[str, object]] = [
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
                "content": base64.b64encode(audio).decode("ascii"),
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
    ]
    events.extend(
        {
            "textOutput": {
                **identity,
                "contentId": "text-1",
                "content": chunk,
            }
        }
        for chunk in chunks
    )
    events.extend(
        [
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
        ]
    )
    return tuple(events)


def _render_result(
    text: str,
    audio: bytes = b"\0\0" * 2400,
    *,
    prompt_name: str = "prompt-1",
) -> NovaRenderResult:
    return NovaRenderResult(
        audio_lpcm=audio,
        final_transcript=text,
        events=_output_events(text, audio, prompt_name=prompt_name),
        completion_stop_reason="END_TURN",
    )


def _render_all(plan_path: Path, monkeypatch) -> None:
    def fake_render(
        text,
        voice_id,
        settings,
        *,
        prompt_name=None,
        paid_render_authorized=False,
    ):
        assert paid_render_authorized is True
        assert voice_id in {"tiffany", "amy", "olivia", "kiara"}
        assert isinstance(prompt_name, str)
        return _render_result(text, prompt_name=prompt_name)

    monkeypatch.setattr(audition, "render_text", fake_render)
    assert audition.render_plan(WORKSPACE, plan_path, paid_render_authorized=True) == 16


def test_plan_extracts_only_prose_and_creates_sixteen_calls(isolated_config):
    plan_path = _plan(isolated_config)
    plan = read_json(plan_path)

    assert plan["schema_version"] == 2
    assert len(plan["voices"]) == 4
    assert len(plan["excerpts"]) == 4
    assert len(plan["calls"]) == 16
    assert {call["status"] for call in plan["calls"]} == {"pending"}

    for call in plan["calls"]:
        assert call["attempt_id"] is None
        assert call["reconciliation_history"] == []
    for excerpt in plan["excerpts"]:
        prepared = resolve_inside(WORKSPACE, excerpt["input_path"]).read_text(encoding="utf-8")
        assert "movement:" not in prepared
        assert "pov_id:" not in prepared
        assert "hook:" not in prepared
        assert not prepared.startswith("---")


def test_config_requires_all_four_blind_candidates(isolated_config):
    invalid_path = isolated_config.path.parent / "invalid-voices.toml"
    raw = isolated_config.path.read_text(encoding="utf-8").replace(
        'voices = ["tiffany", "amy", "olivia", "kiara"]',
        'voices = ["tiffany"]',
    )
    invalid_path.write_text(raw, encoding="utf-8")
    with pytest.raises(InputError, match="exactly tiffany, amy, olivia, and kiara"):
        load_audition_config(invalid_path, WORKSPACE)


def test_copied_or_malformed_plan_cannot_reach_billable_boundary(isolated_config, monkeypatch):
    plan_path = _plan(isolated_config)
    copied_path = plan_path.parent.parent / f"copied-{uuid.uuid4().hex}.json"
    copied_path.write_bytes(plan_path.read_bytes())
    invocation_count = 0

    def forbidden_render(*_args, **_kwargs):
        nonlocal invocation_count
        invocation_count += 1
        raise AssertionError("malformed plans must not reach render_text")

    monkeypatch.setattr(audition, "render_text", forbidden_render)
    with pytest.raises(InputError, match="canonical path"):
        audition.render_plan(WORKSPACE, copied_path, paid_render_authorized=True)
    assert invocation_count == 0

    plan = read_json(plan_path)
    plan["calls"][1] = copy.deepcopy(plan["calls"][0])
    atomic_write_json(plan_path, plan)
    with pytest.raises(InputError, match="Call matrix identity"):
        audition.render_plan(WORKSPACE, plan_path, paid_render_authorized=True)
    assert invocation_count == 0


def test_paid_boundaries_fail_closed(isolated_config):
    plan_path = _plan(isolated_config)
    with pytest.raises(InputError, match="paid-render authorization"):
        render_text("Never invoke this", "tiffany", isolated_config.nova)
    with pytest.raises(InputError, match="paid-render authorization"):
        audition.render_plan(WORKSPACE, plan_path)


def test_mock_render_packages_blind_and_revalidates_transcripts(isolated_config, monkeypatch):
    plan_path = _plan(isolated_config)
    _render_all(plan_path, monkeypatch)
    package = audition.package_blind_audition(WORKSPACE, plan_path)

    assert len(list((package / "clips").glob("*/*.wav"))) == 16
    assert len((package / "scorecard.csv").read_text(encoding="utf-8").splitlines()) == 17
    assert not (package / "blind-key.json").exists()
    assert len(audition.reveal_blind_key(WORKSPACE, plan_path)) == 4
    assert audition.package_blind_audition(WORKSPACE, plan_path) == package
    assert audition.render_plan(WORKSPACE, plan_path, paid_render_authorized=True) == 0
    assert read_json(plan_path)["status"] == "packaged"

    plan = read_json(plan_path)
    assert all(call["attempt_id"] and call["events_sha256"] for call in plan["calls"])
    private_binding = resolve_inside(WORKSPACE, plan["blind_key_path"]).parent / "package-binding.json"
    assert private_binding.is_file()
    assert not (package / "package-binding.json").exists()

    transcript = resolve_inside(WORKSPACE, plan["calls"][0]["transcript_path"])
    transcript.write_text("tampered transcript\n", encoding="utf-8")
    with pytest.raises(FidelityMismatch, match="no longer matches source"):
        audition.package_blind_audition(WORKSPACE, plan_path)


def test_uncertain_call_never_retries_without_explicit_reconciliation(isolated_config, monkeypatch):
    plan_path = _plan(isolated_config)
    initial = read_json(plan_path)
    target = initial["calls"][0]
    invocation_count = 0

    def uncertain_render(
        text,
        voice_id,
        settings,
        *,
        prompt_name=None,
        paid_render_authorized=False,
    ):
        nonlocal invocation_count
        invocation_count += 1
        persisted = read_json(plan_path)
        persisted_target = next(call for call in persisted["calls"] if call["call_id"] == target["call_id"])
        assert persisted_target["status"] == "invoking"
        assert persisted_target["attempt_id"]
        assert persisted_target["prompt_name"] == prompt_name
        assert persisted_target["request_binding_sha256"]
        raise InputError("simulated transport failure after invocation began")

    monkeypatch.setattr(audition, "render_text", uncertain_render)
    with pytest.raises(InputError, match="simulated transport failure"):
        audition.render_plan(
            WORKSPACE,
            plan_path,
            [target["voice_id"]],
            [target["excerpt_id"]],
            paid_render_authorized=True,
        )

    persisted = read_json(plan_path)
    persisted_target = next(call for call in persisted["calls"] if call["call_id"] == target["call_id"])
    assert persisted_target["status"] == "charge_uncertain"
    assert invocation_count == 1

    with pytest.raises(InputError, match="Charge is uncertain"):
        audition.render_plan(
            WORKSPACE,
            plan_path,
            [target["voice_id"]],
            [target["excerpt_id"]],
            paid_render_authorized=True,
        )
    assert invocation_count == 1

    with pytest.raises(InputError, match="confirm-possible-duplicate-charge"):
        audition.reconcile_uncertain_call(WORKSPACE, plan_path, target["call_id"])
    outcome = audition.reconcile_uncertain_call(
        WORKSPACE,
        plan_path,
        target["call_id"],
        duplicate_charge_acknowledged=True,
    )
    assert outcome["action"] == "reset_to_pending"
    reset_target = next(call for call in read_json(plan_path)["calls"] if call["call_id"] == target["call_id"])
    assert reset_target["status"] == "pending"
    assert reset_target["reconciliation_history"][-1]["prior_status"] == "charge_uncertain"


def test_reconciliation_journal_survives_crash_after_evidence_move(isolated_config, monkeypatch):
    plan_path = _plan(isolated_config)
    plan = read_json(plan_path)
    target = plan["calls"][0]
    partial = resolve_inside(WORKSPACE, target["transcript_path"])

    def partial_render(
        text,
        voice_id,
        settings,
        *,
        prompt_name=None,
        paid_render_authorized=False,
    ):
        partial.parent.mkdir(parents=True, exist_ok=True)
        partial.write_text("partial evidence\n", encoding="utf-8")
        raise InputError("simulated interruption with partial evidence")

    monkeypatch.setattr(audition, "render_text", partial_render)
    with pytest.raises(InputError, match="partial evidence"):
        audition.render_plan(
            WORKSPACE,
            plan_path,
            [target["voice_id"]],
            [target["excerpt_id"]],
            paid_render_authorized=True,
        )

    original_persist = audition._persist_plan
    persist_count = 0

    def crash_before_finalize(path, value):
        nonlocal persist_count
        persist_count += 1
        if persist_count == 2:
            raise RuntimeError("simulated crash after evidence move")
        original_persist(path, value)

    monkeypatch.setattr(audition, "_persist_plan", crash_before_finalize)
    with pytest.raises(RuntimeError, match="after evidence move"):
        audition.reconcile_uncertain_call(
            WORKSPACE,
            plan_path,
            target["call_id"],
            duplicate_charge_acknowledged=True,
        )
    assert not partial.exists()
    journaled_target = next(
        call for call in read_json(plan_path)["calls"] if call["call_id"] == target["call_id"]
    )
    journal = journaled_target["reconciliation_in_progress"]
    assert journal is not None
    assert resolve_inside(WORKSPACE, journal["evidence"][0]["quarantined_path"]).is_file()

    monkeypatch.setattr(audition, "_persist_plan", original_persist)
    outcome = audition.reconcile_uncertain_call(
        WORKSPACE,
        plan_path,
        target["call_id"],
        duplicate_charge_acknowledged=True,
    )
    assert outcome["quarantined_artifacts"] == 1
    reset_target = next(call for call in read_json(plan_path)["calls"] if call["call_id"] == target["call_id"])
    assert reset_target["reconciliation_in_progress"] is None
    evidence = reset_target["reconciliation_history"][-1]["quarantined_evidence"]
    assert len(evidence) == 1
    assert resolve_inside(WORKSPACE, evidence[0]["quarantined_path"]).is_file()


def test_event_replay_requires_complete_correlated_output():
    events = _output_events("cannot", b"\0\0", text_chunks=("can", "not"))
    result = replay_output_events(events)
    assert result.final_transcript == "cannot"
    assert result.audio_lpcm == b"\0\0"

    missing_end = tuple(
        event
        for event in events
        if not (
            "contentEnd" in event
            and event["contentEnd"].get("contentId") == "text-1"
        )
    )
    with pytest.raises(InputError, match="before contentEnd"):
        replay_output_events(missing_end)

    wrong_id = copy.deepcopy(events)
    next(event for event in wrong_id if "audioOutput" in event)["audioOutput"]["contentId"] = "other"
    with pytest.raises(InputError, match="unopened contentId"):
        replay_output_events(wrong_id)

    after_completion = events + ({"usageEvent": {**_ids(), "details": {}}},)
    with pytest.raises(InputError, match="does not end with completionEnd"):
        replay_output_events(after_completion)

    leading_usage = ({"usageEvent": {**_ids(), "details": {}}},) + events
    assert replay_output_events(leading_usage).final_transcript == "cannot"

    without_completion_start = events[1:]
    assert replay_output_events(without_completion_start).final_transcript == "cannot"

    extra_completion_segment = (
        events[0],
        {"completionStart": {**_ids(), "completionId": "completion-0"}},
        {"completionEnd": {**_ids(), "completionId": "completion-0", "stopReason": "END_TURN"}},
    ) + events[1:]
    assert replay_output_events(extra_completion_segment).final_transcript == "cannot"

    foreign_prompt_event = copy.deepcopy(events)
    next(event for event in foreign_prompt_event if "audioOutput" in event)["audioOutput"][
        "promptName"
    ] = "prompt-2"
    with pytest.raises(InputError, match="promptName does not match the rest of the stream"):
        replay_output_events(foreign_prompt_event)
    with pytest.raises(InputError, match="does not match the persisted request"):
        replay_output_events(events, expected_prompt_name="prompt-2")

    with pytest.raises(InputError, match="unsupported event type 'mysteryEvent'"):
        replay_output_events(events + ({"mysteryEvent": dict(_ids())},))
    with pytest.raises(InputError, match="observed Nova output events: completionStart"):
        replay_output_events((events[0], {"mysteryEvent": dict(_ids())}))

    partial_final_text = copy.deepcopy(events)
    next(
        event
        for event in partial_final_text
        if "contentEnd" in event and event["contentEnd"].get("contentId") == "text-1"
    )["contentEnd"]["stopReason"] = "PARTIAL_TURN"
    with pytest.raises(InputError, match="no complete ASSISTANT FINAL transcript turn"):
        replay_output_events(partial_final_text)

    partial_audio = copy.deepcopy(events)
    next(
        event
        for event in partial_audio
        if "contentEnd" in event and event["contentEnd"].get("contentId") == "audio-1"
    )["contentEnd"]["stopReason"] = "PARTIAL_TURN"
    with pytest.raises(InputError, match="no complete ASSISTANT audio turn"):
        replay_output_events(partial_audio)


def test_receiver_uses_the_same_complete_event_replay(isolated_config):
    timeline: list[tuple[str, str, str | None]] = []

    class Chunk:
        def __init__(self, event):
            self.event = event
            encoded = json.dumps({"event": event}).encode("utf-8")
            self.value = SimpleNamespace(bytes_=encoded)

    class Unknown:
        pass

    enough_silence = asyncio.Event()

    class Output:
        def __init__(self, values):
            self.values = values
            self.started = False

        def __aiter__(self):
            self.iterator = iter(self.values)
            return self

        async def __anext__(self):
            if not self.started:
                self.started = True
                await enough_silence.wait()
            try:
                chunk = next(self.iterator)
            except StopIteration as exc:
                raise StopAsyncIteration from exc
            event_name, content = next(iter(chunk.event.items()))
            timeline.append(("output", event_name, content.get("contentId")))
            return chunk

    class InputStream:
        def __init__(self):
            self.events = []
            self.audio_input_count = 0
            self.closed = False

        async def send(self, value):
            document = json.loads(value.value.bytes_.decode("utf-8"))
            assert set(document) == {"event"}
            event = document["event"]
            self.events.append(event)
            event_name, content = next(iter(event.items()))
            timeline.append(("input", event_name, content.get("contentName")))
            if "audioInput" in event:
                self.audio_input_count += 1
                if self.audio_input_count >= 3:
                    enough_silence.set()

        async def close(self):
            self.closed = True

    prompt_name = "00000000-0000-4000-8000-000000000001"

    class Stream:
        def __init__(self):
            self.input_stream = InputStream()
            self.entered = False
            self.exited = False

        async def __aenter__(self):
            self.entered = True
            return self

        async def __aexit__(self, *_args):
            self.exited = True

        async def await_output(self):
            identity = _ids(prompt_name)
            response_events = list(
                _output_events(
                    "not",
                    b"\0\0",
                    text_chunks=("not",),
                    prompt_name=prompt_name,
                )
            )
            response_events[1:1] = [
                {
                    "completionEnd": {
                        **identity,
                        "completionId": "completion-0",
                        "stopReason": "END_TURN",
                    }
                },
            ]
            response_events[5:5] = [
                {
                    "contentStart": {
                        **identity,
                        "contentId": "text-partial",
                        "role": "ASSISTANT",
                        "type": "TEXT",
                        "additionalModelFields": '{"generationStage":"FINAL"}',
                        "textOutputConfiguration": {"mediaType": "text/plain"},
                    }
                },
                {
                    "textOutput": {
                        **identity,
                        "contentId": "text-partial",
                        "content": "can",
                    }
                },
                {
                    "contentEnd": {
                        **identity,
                        "contentId": "text-partial",
                        "stopReason": "PARTIAL_TURN",
                        "type": "TEXT",
                    }
                },
            ]
            return None, Output([Chunk(event) for event in response_events])

    stream = Stream()

    class Client:
        def __init__(self):
            self.model_ids = []

        async def invoke_model_with_bidirectional_stream(self, operation):
            self.model_ids.append(operation.model_id)
            return stream

    client = Client()

    class Config:
        @staticmethod
        async def resolve(**_kwargs):
            return object()

    sdk = {
        "config": Config,
        "transport": object,
        "client": lambda **_kwargs: client,
        "operation_input": lambda **kwargs: SimpleNamespace(**kwargs),
        "input_chunk": lambda **kwargs: SimpleNamespace(**kwargs),
        "payload": lambda **kwargs: SimpleNamespace(**kwargs),
    }

    result = asyncio.run(
        _invoke_session(
            "cannot",
            "tiffany",
            isolated_config.nova,
            prompt_name,
            sdk,
            {"chunk": Chunk, "errors": (), "unknown": Unknown},
        )
    )
    assert result.final_transcript == "cannot"
    assert result.audio_lpcm == b"\0\0"
    assert client.model_ids == [isolated_config.nova.model_id]
    assert stream.entered is True
    assert stream.input_stream.closed is True
    assert stream.exited is True

    events = stream.input_stream.events
    event_names = [next(iter(event)) for event in events]
    assert event_names[:10] == [
        "sessionStart",
        "promptStart",
        "contentStart",
        "textInput",
        "contentEnd",
        "contentStart",
        "audioInput",
        "contentStart",
        "textInput",
        "contentEnd",
    ]
    assert len(event_names[10:-3]) >= 2
    assert set(event_names[10:-3]) == {"audioInput"}
    assert event_names[-3:] == ["contentEnd", "promptEnd", "sessionEnd"]
    assert events[1]["promptStart"]["audioOutputConfiguration"]["sampleRateHertz"] == 24000

    audio_start = events[5]["contentStart"]
    assert audio_start["type"] == "AUDIO"
    assert audio_start["interactive"] is True
    assert audio_start["role"] == "USER"
    assert audio_start["audioInputConfiguration"] == {
        "mediaType": "audio/lpcm",
        "sampleRateHertz": 16000,
        "sampleSizeBits": 16,
        "channelCount": 1,
        "audioType": "SPEECH",
        "encoding": "base64",
    }
    audio_name = audio_start["contentName"]
    audio_inputs = [event["audioInput"] for event in events if "audioInput" in event]
    assert len(audio_inputs) >= 3
    for audio_input in audio_inputs:
        assert audio_input["contentName"] == audio_name
        silent_frame = base64.b64decode(audio_input["content"], validate=True)
        assert len(silent_frame) == 1024
        assert silent_frame == bytes(1024)

    user_start = events[7]["contentStart"]
    assert user_start["type"] == "TEXT"
    assert user_start["interactive"] is True
    assert user_start["role"] == "USER"
    assert events[-3]["contentEnd"]["contentName"] == audio_name

    final_text_end = timeline.index(("output", "contentEnd", "text-1"))
    audio_input_end = timeline.index(("input", "contentEnd", audio_name))
    prompt_end = timeline.index(("input", "promptEnd", None))
    session_end = timeline.index(("input", "sessionEnd", None))
    completion_ends = [
        position
        for position, entry in enumerate(timeline)
        if entry[0] == "output" and entry[1] == "completionEnd"
    ]
    assert len(completion_ends) == 2
    early_completion_end, completion_end = completion_ends
    assert early_completion_end < final_text_end
    assert final_text_end < audio_input_end < prompt_end < session_end < completion_end
    assert all(entry[1] != "audioInput" for entry in timeline[final_text_end + 1 :])


def test_event_and_wav_tampering_are_bound_together(isolated_config, monkeypatch):
    plan_path = _plan(isolated_config)
    _render_all(plan_path, monkeypatch)
    plan = read_json(plan_path)
    target = plan["calls"][0]
    events_path = resolve_inside(WORKSPACE, target["events_path"])
    original_events = events_path.read_text(encoding="utf-8")
    events = [json.loads(line) for line in original_events.splitlines()]
    next(event for event in events if "textOutput" in event)["textOutput"]["content"] = "tampered"
    events_path.write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )
    with pytest.raises(InputError, match="Event log transcript"):
        audition.package_blind_audition(WORKSPACE, plan_path)

    events_path.write_text(original_events, encoding="utf-8")
    audio_path = resolve_inside(WORKSPACE, target["audio_path"])
    audio_path.write_bytes(audition._wav_bytes(b"\1\0" * 2400, isolated_config))
    plan = read_json(plan_path)
    next(call for call in plan["calls"] if call["call_id"] == target["call_id"])["audio_sha256"] = sha256_file(audio_path)
    atomic_write_json(plan_path, plan)
    with pytest.raises(InputError, match="Event log audio"):
        audition.package_blind_audition(WORKSPACE, plan_path)


def test_output_prompt_identity_is_bound_to_the_persisted_attempt(isolated_config, monkeypatch):
    plan_path = _plan(isolated_config)
    _render_all(plan_path, monkeypatch)
    plan = read_json(plan_path)
    target = plan["calls"][0]
    events_path = resolve_inside(WORKSPACE, target["events_path"])
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines()]
    wrong_prompt = "00000000-0000-4000-8000-000000000099"
    for event in events:
        payload = next(iter(event.values()))
        if "promptName" in payload:
            payload["promptName"] = wrong_prompt
    events_path.write_text(
        "".join(json.dumps(event, sort_keys=True) + "\n" for event in events),
        encoding="utf-8",
    )
    target["events_sha256"] = sha256_file(events_path)
    atomic_write_json(plan_path, plan)

    with pytest.raises(InputError, match="promptName does not match"):
        audition.package_blind_audition(WORKSPACE, plan_path)


def test_blind_key_rejects_traversal_unknown_fields_and_duplicates(isolated_config, monkeypatch):
    plan_path = _plan(isolated_config)
    _render_all(plan_path, monkeypatch)
    plan = read_json(plan_path)
    key_path = resolve_inside(WORKSPACE, plan["blind_key_path"])
    voices = plan["voices"]
    base = {
        "schema_version": 1,
        "audition_id": plan["audition_id"],
        "created_at": "2026-09-12T00:00:00Z",
        "voice_by_label": dict(zip(audition.BLIND_LABELS, voices, strict=True)),
        "warning": audition.BLIND_KEY_WARNING,
    }

    duplicate_names = json.dumps(base).replace(
        '"schema_version": 1',
        '"schema_version": 1, "schema_version": true',
        1,
    )
    key_path.write_text(duplicate_names, encoding="utf-8")
    with pytest.raises(InputError, match="duplicate object name"):
        audition.reveal_blind_key(WORKSPACE, plan_path)

    traversal = copy.deepcopy(base)
    traversal["voice_by_label"] = {
        "../../voice-identity": voices[0],
        "B": voices[1],
        "C": voices[2],
        "D": voices[3],
    }
    atomic_write_json(key_path, traversal)
    with pytest.raises(InputError, match="labels must be exactly"):
        audition.package_blind_audition(WORKSPACE, plan_path)
    assert not (isolated_config.package_root / plan["audition_id"]).exists()

    unknown = copy.deepcopy(base)
    unknown["voice_id_hint"] = voices[0]
    atomic_write_json(key_path, unknown)
    with pytest.raises(InputError, match="unknown"):
        audition.reveal_blind_key(WORKSPACE, plan_path)

    duplicate = copy.deepcopy(base)
    duplicate["voice_by_label"]["D"] = voices[0]
    atomic_write_json(key_path, duplicate)
    with pytest.raises(InputError, match="unique permutation"):
        audition.reveal_blind_key(WORKSPACE, plan_path)


def test_concurrent_packagers_share_one_key_and_hash_binding(isolated_config, monkeypatch):
    plan_path = _plan(isolated_config)
    _render_all(plan_path, monkeypatch)
    barrier = threading.Barrier(2)

    def package_once() -> Path:
        barrier.wait(timeout=5)
        return audition.package_blind_audition(WORKSPACE, plan_path)

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        results = list(executor.map(lambda _index: package_once(), range(2)))
    assert results[0] == results[1]

    plan = read_json(plan_path)
    key_path = resolve_inside(WORKSPACE, plan["blind_key_path"])
    mapping = read_json(key_path)["voice_by_label"]
    binding = read_json(key_path.parent / "package-binding.json")
    calls = {call["call_id"]: call for call in plan["calls"]}
    assert len(binding["clips"]) == 16
    for clip in binding["clips"]:
        source = resolve_inside(WORKSPACE, calls[clip["source_call_id"]]["audio_path"])
        published = resolve_inside(results[0], clip["relative_path"])
        assert sha256_file(source) == clip["wav_sha256"] == sha256_file(published)
        assert all(voice not in clip["relative_path"] for voice in mapping.values())

    binding["schema_version"] = True
    atomic_write_json(key_path.parent / "package-binding.json", binding)
    with pytest.raises(InputError, match="schema_version"):
        audition.package_blind_audition(WORKSPACE, plan_path)


def test_cancellation_and_context_teardown_have_short_bounds(isolated_config, monkeypatch):
    flags: list[str] = []
    output_started = asyncio.Event()

    class HangingOutput:
        def __aiter__(self):
            return self

        async def __anext__(self):
            output_started.set()
            try:
                await asyncio.sleep(60)
            except asyncio.CancelledError:
                try:
                    await asyncio.sleep(60)
                except asyncio.CancelledError:
                    raise
            raise StopAsyncIteration

    class InputStream:
        async def send(self, _value):
            return None

        async def close(self):
            flags.append("input-close")
            await asyncio.sleep(60)

    class Stream:
        def __init__(self):
            self.input_stream = InputStream()

        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            flags.append("stream-exit")
            await asyncio.sleep(60)

        async def await_output(self):
            return None, HangingOutput()

    stream = Stream()

    class Client:
        async def invoke_model_with_bidirectional_stream(self, _operation):
            return stream

    class Config:
        @staticmethod
        async def resolve(**_kwargs):
            return object()

    sdk = {
        "config": Config,
        "transport": object,
        "client": lambda **_kwargs: Client(),
        "operation_input": lambda **kwargs: SimpleNamespace(**kwargs),
        "input_chunk": lambda **kwargs: SimpleNamespace(**kwargs),
        "payload": lambda **kwargs: SimpleNamespace(**kwargs),
    }

    class Chunk:
        pass

    class Unknown:
        pass

    monkeypatch.setattr(nova, "_CLEANUP_TIMEOUT_SECONDS", 0.02)

    async def scenario() -> float:
        task = asyncio.create_task(
            _invoke_session(
                "text",
                "tiffany",
                isolated_config.nova,
                "00000000-0000-4000-8000-000000000001",
                sdk,
                {"chunk": Chunk, "errors": (), "unknown": Unknown},
            )
        )
        await asyncio.wait_for(output_started.wait(), timeout=1)
        started = time.monotonic()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        return time.monotonic() - started

    elapsed = asyncio.run(scenario())
    assert elapsed < 0.25
    assert flags == ["input-close", "stream-exit"]


def test_hard_process_deadline_kills_cancellation_resistant_worker():
    assert _run_worker_process(_result_process_worker, ("ok",), 2, "unused") == "ok"
    started = time.monotonic()
    with pytest.raises(InputError, match="hard test deadline"):
        _run_worker_process(
            _hanging_process_worker,
            (),
            0.05,
            "hard test deadline",
        )
    assert time.monotonic() - started < 2.5


def test_built_wheel_runs_outside_source_tree_without_private_paths(tmp_path):
    uv = shutil.which("uv")
    assert uv is not None, "uv is required by this project's validated build workflow"
    wheelhouse = tmp_path / "wheelhouse"
    environment = os.environ.copy()
    environment["UV_OFFLINE"] = "1"
    environment.pop("PYTHONPATH", None)
    environment["PYTHONNOUSERSITE"] = "1"

    subprocess.run(
        [
            uv,
            "build",
            "--wheel",
            "--offline",
            "--out-dir",
            str(wheelhouse),
        ],
        cwd=AUDIOBOOK_ROOT,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=120,
    )
    wheels = list(wheelhouse.glob("*.whl"))
    assert len(wheels) == 1

    installed = tmp_path / "installed"
    venv.EnvBuilder(with_pip=False, symlinks=os.name != "nt").create(installed)
    scripts = installed / ("Scripts" if os.name == "nt" else "bin")
    python = scripts / ("python.exe" if os.name == "nt" else "python")
    console = scripts / ("frontier-audiobook.exe" if os.name == "nt" else "frontier-audiobook")
    install_result = subprocess.run(
        [uv, "pip", "install", "--python", str(python), "--no-deps", str(wheels[0])],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=120,
    )
    assert install_result.returncode == 0, install_result.stderr
    help_result = subprocess.run(
        [str(console), "--help"],
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert "Guarded Amazon Nova 2 Sonic" in help_result.stdout
    import_result = subprocess.run(
        [str(python), "-c", "import frontier_audiobook; print(frontier_audiobook.__file__)"],
        cwd=tmp_path,
        env=environment,
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert str(AUDIOBOOK_ROOT / "src") not in import_result.stdout
    assert str(installed) in import_result.stdout

    with zipfile.ZipFile(wheels[0]) as archive:
        metadata_name = next(name for name in archive.namelist() if name.endswith(".dist-info/METADATA"))
        metadata = archive.read(metadata_name).decode("utf-8")
    assert str(Path.home()) not in metadata
    assert not re.search(r"/(?:Users|home)/[^/\s]+/", metadata)


def test_verbatim_prefix_acceptance_requires_opt_in_prefix_and_plausible_duration():
    expected = "The relay stood on the bench under the window, lit and on standby."
    exact = compare_transcript(expected, expected)
    assert exact.passed is True
    assert exact.transcript_is_verbatim_prefix is True
    assert exact.coverage_ratio == 1.0
    # An exact transcript never needs the opt-in and never depends on duration.
    assert audition.fidelity_accepted(exact, 0.0) is True

    prefix = compare_transcript(expected, "The relay stood on the bench")
    assert prefix.passed is False
    assert prefix.transcript_is_verbatim_prefix is True
    assert prefix.expected_token_count == 13
    assert prefix.coverage_ratio < audition.MIN_TRANSCRIPT_COVERAGE
    required = audition.MIN_SECONDS_PER_EXPECTED_WORD * prefix.expected_token_count

    # Strict mode remains the default and still rejects incomplete coverage.
    assert audition.fidelity_accepted(prefix, required) is False
    # Low coverage is accepted only when the audio is long enough for the whole excerpt.
    assert audition.fidelity_accepted(prefix, required, accept_verbatim_prefix=True) is True
    assert (
        audition.fidelity_accepted(prefix, required - 0.001, accept_verbatim_prefix=True) is False
    )

    # High coverage is independent evidence that the audio was not truncated, so a
    # fast but complete reading is accepted even when it is shorter than the
    # duration floor.
    nearly_complete = compare_transcript(
        expected, "The relay stood on the bench under the window, lit and on"
    )
    assert nearly_complete.transcript_is_verbatim_prefix is True
    assert nearly_complete.coverage_ratio >= audition.MIN_TRANSCRIPT_COVERAGE
    assert audition.fidelity_accepted(nearly_complete, 0.1, accept_verbatim_prefix=True) is True
    assert audition.fidelity_accepted(nearly_complete, 0.1) is False

    reordered = compare_transcript(expected, "stood The relay on the bench")
    assert reordered.transcript_is_verbatim_prefix is False
    assert audition.fidelity_accepted(reordered, 600.0, accept_verbatim_prefix=True) is False

    invented = compare_transcript(expected, "The relay rested on the bench")
    assert invented.transcript_is_verbatim_prefix is False
    assert audition.fidelity_accepted(invented, 600.0, accept_verbatim_prefix=True) is False

    longer = compare_transcript(expected, expected + " and then it stopped")
    assert longer.transcript_is_verbatim_prefix is False
    assert audition.fidelity_accepted(longer, 600.0, accept_verbatim_prefix=True) is False
