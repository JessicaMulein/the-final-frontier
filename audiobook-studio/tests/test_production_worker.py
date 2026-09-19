from __future__ import annotations

import base64
import json
import socket
from datetime import UTC, datetime
from pathlib import Path

import pytest

from frontier_audiobook import narrate
from frontier_audiobook.errors import InputError
from frontier_audiobook.nova import NovaRenderResult
from frontier_audiobook.production import (
    ProductionSelectors,
    create_production_plan,
    load_production_plan,
)
from frontier_audiobook.production_models import (
    AuthorizationDecision,
    FrozenBatchPlan,
    PaidAuthorization,
    StrictRecordCodec,
    TransactionState,
    authorization_confirmation_sha256,
    seal_record,
)
from frontier_audiobook.production_transactions import TransactionStore
from frontier_audiobook.production_worker import run_production_worker
from frontier_audiobook.util import read_json, sha256_bytes

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
AUDITION_CONFIG = REPOSITORY_ROOT / "audiobook-studio" / "config" / "audition.toml"
SENTENCES = (
    "Alpha one two three four.",
    "Bravo one two three four.",
)


@pytest.fixture(autouse=True)
def deny_external_access(monkeypatch):
    def blocked(*_args, **_kwargs):
        raise AssertionError("production worker tests must remain local and nonbillable")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(narrate, "render_text", blocked)
    monkeypatch.setenv("FRONTIER_AUDIOBOOK_DISABLE_AWS", "1")
    monkeypatch.setenv("AWS_EC2_METADATA_DISABLED", "true")
    monkeypatch.setenv("AWS_PROFILE", "frontier-audiobook")
    for name in ("AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_SESSION_TOKEN"):
        monkeypatch.delenv(name, raising=False)


def _write_chapter(workspace: Path, sentences: tuple[str, ...] = SENTENCES) -> Path:
    path = (
        workspace
        / "The Final Frontier Novel"
        / "chapters"
        / "discovery-part"
        / "discovery-part-001-test.md"
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    body = " ".join(sentences)
    path.write_text(
        "\n".join(
            (
                "---",
                "movement: discovery",
                "chapter: 1",
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


def _write_workspace(
    workspace: Path,
    track_kind: str,
    *,
    sentences: tuple[str, ...] = SENTENCES,
) -> tuple[Path, Path]:
    runtime_config = workspace / "audiobook-studio" / "config" / "audition.toml"
    runtime_config.parent.mkdir(parents=True, exist_ok=True)
    runtime_config.write_bytes(AUDITION_CONFIG.read_bytes())
    chapter_root = workspace / "The Final Frontier Novel" / "chapters" / "discovery-part"
    chapter_root.mkdir(parents=True, exist_ok=True)

    selected_source: Path
    track_declaration = "tracks = []\n"
    if track_kind == "chapter":
        selected_source = _write_chapter(workspace, sentences)
    else:
        selected_source = workspace / "audiobook-studio" / "config" / "tracks" / "opening.md"
        selected_source.parent.mkdir(parents=True, exist_ok=True)
        source_text = (
            "# Publishing Handoff\n\n"
            "## Spoken Opening\n\n"
            + " ".join(sentences)
            + "\n\n## Written Only\n\nDo not narrate this section.\n"
        )
        selected_source.write_text(source_text, encoding="utf-8")
        track_declaration = ""

    config_path = workspace / "audiobook-studio" / "config" / "production.toml"
    special = ""
    if track_kind == "special":
        special = f'''
[[tracks]]
id = "opening-credits"
kind = "opening_credits"
sequence = 1
source_path = "audiobook-studio/config/tracks/opening.md"
source_section = "spoken-opening"
approved_sha256 = "{sha256_bytes(selected_source.read_bytes())}"
enabled = true
approval_status = "approved"
render_once = true

[tracks.override]
'''
    config_path.write_text(
        f'''schema_version = 1
book_id = "the-final-frontier"
manuscript_root = "The Final Frontier Novel"
build_root = "audiobook-studio/build/production"
delivery_root = "audiobook-studio/dist/audiobook"
max_tracks_per_plan = 4
{track_declaration}
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
input_speech_tokens_per_call = 0
input_text_tokens_per_call = 8192
output_speech_tokens_per_call = 8192
output_text_tokens_per_call = 8192
{special}''',
        encoding="utf-8",
    )
    return config_path, selected_source


def _create_plan(workspace: Path, track_kind: str, *, sentences=SENTENCES):
    config_path, source_path = _write_workspace(
        workspace,
        track_kind,
        sentences=sentences,
    )
    selectors = (
        ProductionSelectors.from_cli(chapters=[1])
        if track_kind == "chapter"
        else ProductionSelectors.from_cli(tracks=["opening-credits"])
    )
    plan_path = create_production_plan(
        config_path,
        selectors,
        plan_id=f"plan-worker-{track_kind}",
        workspace_root=workspace,
        created_at_utc="2026-09-14T12:00:00Z",
    )
    return plan_path, load_production_plan(plan_path), source_path


def _authorization(plan: FrozenBatchPlan, maximum_new_calls: int) -> PaidAuthorization:
    track = plan.tracks[0]
    challenge = "a" * 64
    display_sha256 = "b" * 64
    confirmed_at_utc = "2020-01-01T00:00:01Z"
    decision = AuthorizationDecision.AUTHORIZE_EXACT_SCOPE
    return seal_record(
        PaidAuthorization(
            schema_version=1,
            authorization_id="authorization-worker-test",
            plan_sha256=StrictRecordCodec(FrozenBatchPlan).sha256(plan),
            preflight_sha256="c" * 64,
            local_preflight_sha256="d" * 64,
            estimate_sha256="e" * 64,
            official_rate_provenance_sha256="f" * 64,
            exact_transaction_ids=(track.transaction_id,),
            exact_track_ids=(track.track_id,),
            exact_command_sha256s=(track.command_sha256,),
            maximum_new_calls_by_track={track.track_id: maximum_new_calls},
            maximum_new_calls_total=maximum_new_calls,
            estimated_pre_tax_usd="0.01",
            operator_approved_max_estimated_pre_tax_usd="1.00",
            issued_at_utc="2020-01-01T00:00:00Z",
            expires_at_utc="2099-01-01T00:00:00Z",
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


def _ready_worker(
    workspace: Path,
    plan_path: Path,
    plan: FrozenBatchPlan,
    *,
    maximum_new_calls: int,
):
    track = plan.tracks[0]
    authorization = _authorization(plan, maximum_new_calls)
    store = TransactionStore(
        workspace / "audiobook-studio" / "build" / "production" / plan.book_id,
        plan.book_id,
    )
    store.materialize_plan(plan, occurred_at_utc="2026-09-14T12:00:00Z")
    store.append_transition(
        track.track_id,
        track.transaction_id,
        operation_id="preflight-passed",
        event_type="preflight-passed",
        state_after=TransactionState.PREFLIGHT_PASSED,
        details={"preflight_sha256": authorization.preflight_sha256},
        occurred_at_utc="2026-09-14T12:00:01Z",
    )
    store.append_transition(
        track.track_id,
        track.transaction_id,
        operation_id="authorization-required",
        event_type="authorization-required",
        state_after=TransactionState.AUTHORIZATION_REQUIRED,
        details={"preflight_sha256": authorization.preflight_sha256},
        occurred_at_utc="2026-09-14T12:00:02Z",
    )
    authorization_codec = StrictRecordCodec(PaidAuthorization)
    authorization_sha256 = authorization_codec.sha256(authorization)
    authorization_path = plan_path.parent / "authorizations" / "authorization-worker-test.json"
    authorization_codec.write_atomic(authorization_path, authorization)
    store.append_transition(
        track.track_id,
        track.transaction_id,
        operation_id="attempt-001-authorization-consumed",
        event_type="authorization-consumed",
        state_after=TransactionState.RUNNING,
        details={
            "attempt_id": "attempt-001",
            "authorization_sha256": authorization_sha256,
            "command_sha256": track.command_sha256,
            "maximum_new_calls": maximum_new_calls,
            "one_shot": True,
            "automatic_retry_performed": False,
        },
        occurred_at_utc="2026-09-14T12:00:03Z",
    )
    transaction_root = store.transaction_path(track.track_id, track.transaction_id)
    return track, authorization_path, transaction_root


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


def _render_result(text: str) -> NovaRenderResult:
    lpcm = b"\xe8\x03" * 2400
    return NovaRenderResult(
        audio_lpcm=lpcm,
        final_transcript=text,
        events=_output_events(text, lpcm),
        completion_stop_reason="END_TURN",
    )


@pytest.mark.parametrize("track_kind", ("chapter", "special"))
def test_hidden_worker_uses_one_generic_engine_for_chapter_and_approved_special_track(
    tmp_path,
    monkeypatch,
    capsys,
    track_kind,
):
    plan_path, plan, _source_path = _create_plan(tmp_path, track_kind)
    track, _authorization_path, transaction_root = _ready_worker(
        tmp_path,
        plan_path,
        plan,
        maximum_new_calls=plan.tracks[0].source.segment_count,
    )
    calls: list[str] = []

    def render(text, voice_id, _settings, *, paid_render_authorized=False, **_kwargs):
        assert paid_render_authorized is True
        assert voice_id == "tiffany"
        calls.append(text)
        return _render_result(text)

    monkeypatch.setattr(narrate, "render_text", render)
    status = run_production_worker(
        tmp_path,
        plan_path,
        track.transaction_id,
        track.track_id,
    )

    assert status == 0
    assert len(calls) == track.source.segment_count
    runtime_root = transaction_root / "runtime"
    manifest = read_json(runtime_root / "manifest.json")
    assert manifest["track_id"] == track.track_id
    assert manifest["source_kind"] == track.source.source_kind.value
    assert manifest["active_segment_count"] == track.source.segment_count
    assert manifest["billable_calls_made"] == track.source.segment_count
    assert tuple(item["segment_id"] for item in manifest["segments"]) == tuple(
        item.segment_id for item in track.source.segments
    )
    assert all(item["event_replay_passed"] is True for item in manifest["segments"])
    assert all(
        item["render_identity_sha256"] == planned.render_identity_sha256
        for item, planned in zip(manifest["segments"], track.source.segments, strict=True)
    )
    assert (runtime_root / Path(manifest["track_audio_path"]).name).is_file()
    assert not tuple(runtime_root.parent.glob("*.staging-*"))
    output = capsys.readouterr().out
    assert '"event":"production-track-complete"' in output
    assert "Alpha one two" not in output
    for item in manifest["segments"]:
        assert Path(item["audio_path"]).stem.startswith(item["segment_id"] + "-")
        for path_field, digest_field in (
            ("audio_path", "audio_sha256"),
            ("transcript_path", "transcript_sha256"),
            ("event_journal_path", "event_journal_sha256"),
        ):
            artifact = tmp_path / item[path_field]
            assert artifact.is_file()
            assert sha256_bytes(artifact.read_bytes()) == item[digest_field]


@pytest.mark.parametrize(
    ("drift", "message"),
    (
        ("source", "source or frozen segmentation changed"),
        ("config", "configuration differs from the frozen plan"),
        ("runtime", "Protected production runtime changed"),
        ("authorization", "authorization artifact is missing or ambiguous"),
        ("call-bound", "authorized new-call ceiling"),
    ),
)
def test_worker_stops_before_second_possible_call_when_a_frozen_gate_changes(
    tmp_path,
    monkeypatch,
    drift,
    message,
):
    plan_path, plan, source_path = _create_plan(tmp_path, "chapter")
    maximum_new_calls = 1 if drift == "call-bound" else plan.tracks[0].source.segment_count
    track, authorization_path, transaction_root = _ready_worker(
        tmp_path,
        plan_path,
        plan,
        maximum_new_calls=maximum_new_calls,
    )
    calls = 0

    def render(text, _voice_id, _settings, *, paid_render_authorized=False, **_kwargs):
        nonlocal calls
        assert paid_render_authorized is True
        calls += 1
        if calls == 1:
            if drift == "source":
                source_path.write_text(
                    source_path.read_text(encoding="utf-8") + "Changed afterward.\n",
                    encoding="utf-8",
                )
            elif drift == "config":
                config_path = tmp_path / "audiobook-studio" / "config" / "production.toml"
                config_path.write_text(
                    config_path.read_text(encoding="utf-8") + "\n# changed\n",
                    encoding="utf-8",
                )
            elif drift == "runtime":
                runtime_path = tmp_path / "audiobook-studio" / "config" / "audition.toml"
                runtime_path.write_text(
                    runtime_path.read_text(encoding="utf-8") + "\n# changed\n",
                    encoding="utf-8",
                )
            elif drift == "authorization":
                authorization_path.write_bytes(authorization_path.read_bytes() + b"\n")
        return _render_result(text)

    monkeypatch.setattr(narrate, "render_text", render)
    with pytest.raises(InputError, match=message):
        run_production_worker(
            tmp_path,
            plan_path,
            track.transaction_id,
            track.track_id,
        )

    assert calls == 1
    manifest = read_json(transaction_root / "runtime" / "manifest.json")
    assert manifest["billable_calls_made"] == 1
    assert manifest["active_segment_count"] == 1
    assert not (transaction_root / "runtime" / Path(track.effective_config.output_path).name).exists()


def test_worker_revalidates_production_source_before_final_assembly(
    tmp_path,
    monkeypatch,
):
    plan_path, plan, source_path = _create_plan(
        tmp_path,
        "chapter",
        sentences=("One short paid segment.",),
    )
    track, _authorization_path, transaction_root = _ready_worker(
        tmp_path,
        plan_path,
        plan,
        maximum_new_calls=1,
    )
    calls = 0

    def render(text, _voice_id, _settings, *, paid_render_authorized=False, **_kwargs):
        nonlocal calls
        assert paid_render_authorized is True
        calls += 1
        source_path.write_text(
            source_path.read_text(encoding="utf-8") + "Changed after the call.\n",
            encoding="utf-8",
        )
        return _render_result(text)

    monkeypatch.setattr(narrate, "render_text", render)
    with pytest.raises(InputError, match="source or frozen segmentation changed"):
        run_production_worker(
            tmp_path,
            plan_path,
            track.transaction_id,
            track.track_id,
        )

    assert calls == 1
    manifest = read_json(transaction_root / "runtime" / "manifest.json")
    assert manifest["billable_calls_made"] == 1
    assert not (transaction_root / "runtime" / Path(track.effective_config.output_path).name).exists()
