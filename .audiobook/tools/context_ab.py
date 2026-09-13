"""One-shot, fail-closed Tiffany persistent-session A/B experiment."""

from __future__ import annotations

import argparse
import json
import secrets
import sys
import uuid
from pathlib import Path
from typing import Any

from frontier_audiobook.config import load_audition_config
from frontier_audiobook.errors import InputError
from frontier_audiobook.narrate import (
    _event_audio_blocks,
    _lpcm_from_wav,
    _wav_bytes,
    chapter_spoken_text,
)
from frontier_audiobook.nova import (
    NovaRenderResult,
    NovaSequenceIncomplete,
    _mid_sentence_partial_turn_count,
    render_text_sequence,
    replay_output_events,
)
from frontier_audiobook.util import (
    atomic_write_bytes,
    atomic_write_json,
    atomic_write_text,
    durable_mkdir,
    read_bytes_nofollow,
    sha256_bytes,
    sha256_file,
    sha256_text,
    utc_now,
)
from frontier_audiobook.verify import compare_transcript, normalized_tokens

EXPECTED_SPOKEN_SHA256 = "25063f1971ecb03448fa9a4007fa350edcdbe588f2dd126846b9176eb81dd1dc"
EXPERIMENT_ID = "chapter-001-tiffany-persistent-context-v1-retry-1"
PREVIOUS_MANIFEST_RELATIVE = (
    ".audiobook/build/narration/chapter-001-tiffany-context-ab/manifest.json"
)
SEGMENTS = (
    {
        "segment_id": "0011",
        "text_sha256": "126dbcecf8ef8f6066be50ca70b6c40588321107415513fb37dd1dee1ee2ed9d",
        "baseline_audio_sha256": "0c9e44f8a0c7a726a87d92eb5e72efa9a4da34f214d28bf7d8bd8f7a503f4d8c",
        "text": "Northline's noise floor was characterised before I arrived, and the list of it is pinned above the bench in the order I learned it.",
    },
    {
        "segment_id": "0012",
        "text_sha256": "a30dd4e90fb04f950ab0a648892dc5f2deb6d7a5cbefcf8dd8a34267ce74274f",
        "baseline_audio_sha256": "b3b8631f0a42f112dc574618b99d843869fbfc10e78be84c17cc7e645de161ba",
        "text": "Thermal from the amplifiers, a diurnal term that tracks the cooling plant, a sidereal ripple belonging to the sky and not to us.",
    },
    {
        "segment_id": "0013",
        "text_sha256": "0be7badaa1ad8f665844fcf2bac642b97774b8c7c4a0599b1e4e66a2b18f1d01",
        "baseline_audio_sha256": "3482a89e3570bde426d102eadd107e8360596df6db44f22b5e9c165908e6e03d",
        "text": "And underneath all of it the hiss that is simply what matter at a temperature does.",
    },
    {
        "segment_id": "0014",
        "text_sha256": "006b006908032734c82e59c7a7d7af7d0fd0cbd90d126eaa102ef8cfa2df5a36",
        "baseline_audio_sha256": "d7150e02d047972cd2a3a8c7bba53a66a1bc27e207ca2d49475b6b051002a08c",
        "text": "When something surfaces you walk down that list until one of our own machines confesses.",
    },
    {
        "segment_id": "0015",
        "text_sha256": "1136f8fabdb04b5d557b175139b8417ad37d86cd2069fe7311790e3027feedec",
        "baseline_audio_sha256": "244ea5440385d8424f93730ca66bf67f55f48c0dd6c7ae6a9ffeef0247cecc58",
        "text": "I tabulated the fourteen while Ravi read them out, because tabulating is what I do when I am annoyed: date, start, duration, peak excess.",
    },
    {
        "segment_id": "0016",
        "text_sha256": "6785a0e4a9896db554c65e7a2e8be3b22598e64d0775d767aa04bbeedace6af5",
        "baseline_audio_sha256": "356391f925942a2c05c53e29bad2966300141f6cedb4e933c5cb6509aa13aab1",
        "text": "And the small confident lie I had written at the time.",
    },
)


def _workspace() -> Path:
    return Path(__file__).resolve().parents[2]


def _paths() -> dict[str, Path]:
    workspace = _workspace()
    root = workspace / ".audiobook/build/narration/chapter-001-tiffany-context-ab-retry-1"
    return {
        "workspace": workspace,
        "config": workspace / ".audiobook/config/audition.toml",
        "source_manifest": workspace / ".audiobook/build/narration/chapter-001-tiffany/manifest.json",
        "root": root,
        "manifest": root / "manifest.json",
    }


def _read_json(path: Path) -> Any:
    try:
        return json.loads(read_bytes_nofollow(path).decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise InputError(f"Cannot read strict JSON from {path}: {exc}") from exc


def _read_events(path: Path) -> tuple[dict[str, Any], ...]:
    try:
        return tuple(
            json.loads(line)
            for line in read_bytes_nofollow(path).decode("utf-8").splitlines()
            if line
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise InputError(f"Cannot read Nova events from {path}: {exc}") from exc


def _relative(path: Path) -> str:
    return path.relative_to(_workspace()).as_posix()


def _request_binding(turns: list[dict[str, Any]], config: Any) -> str:
    payload = {
        "experiment_id": EXPERIMENT_ID,
        "spoken_sha256": EXPECTED_SPOKEN_SHA256,
        "model_id": config.nova.model_id,
        "region": config.nova.region,
        "voice_id": "tiffany",
        "turns": [
            {
                "segment_id": turn["segment_id"],
                "text": turn["text"],
                "text_sha256": turn["text_sha256"],
                "baseline_audio_sha256": turn["baseline_audio_sha256"],
            }
            for turn in turns
        ],
    }
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256_text(encoded)


def _preflight() -> tuple[Any, list[dict[str, Any]]]:
    paths = _paths()
    config = load_audition_config(paths["config"], paths["workspace"])
    previous_manifest_path = paths["workspace"] / PREVIOUS_MANIFEST_RELATIVE
    previous_manifest = _read_json(previous_manifest_path)
    if (
        previous_manifest.get("status") != "charge_uncertain"
        or previous_manifest.get("completed_context_turns") != 0
        or not previous_manifest.get("attempt_id")
    ):
        raise InputError("The preserved first attempt is not the expected zero-turn uncertain charge")
    source_manifest = _read_json(paths["source_manifest"])
    if source_manifest.get("spoken_sha256") != EXPECTED_SPOKEN_SHA256:
        raise InputError("Revised chapter narration manifest no longer matches the pinned spoken source")
    if source_manifest.get("voice_id") != "tiffany":
        raise InputError("Baseline narration manifest is not Tiffany")

    _, spoken = chapter_spoken_text(config, 1)
    if sha256_text(spoken) != EXPECTED_SPOKEN_SHA256:
        raise InputError("Chapter 1 spoken source changed before the context experiment")

    source_entries = {
        (entry.get("segment_id"), entry.get("text_sha256")): entry
        for entry in source_manifest.get("segments", [])
    }
    turns: list[dict[str, Any]] = []
    for expected in SEGMENTS:
        entry = source_entries.get((expected["segment_id"], expected["text_sha256"]))
        if entry is None:
            raise InputError(f"Missing pinned baseline segment {expected['segment_id']}")
        for field in ("text", "text_sha256", "audio_sha256"):
            expected_value = (
                expected["baseline_audio_sha256"] if field == "audio_sha256" else expected[field]
            )
            if entry.get(field) != expected_value:
                raise InputError(f"Baseline segment {expected['segment_id']} changed field {field}")
        if (
            entry.get("status") != "narrated"
            or entry.get("exact_transcript_match") is not True
            or entry.get("coverage_ratio") != 1.0
            or entry.get("mid_sentence_partial_turns") != 0
        ):
            raise InputError(f"Baseline segment {expected['segment_id']} is not safely reusable")

        audio_path = paths["workspace"] / entry["audio_path"]
        if sha256_file(audio_path) != expected["baseline_audio_sha256"]:
            raise InputError(f"Baseline WAV hash changed for segment {expected['segment_id']}")
        stem = audio_path.stem
        events_path = audio_path.parent.parent / "events" / f"{stem}.jsonl"
        transcript_path = audio_path.parent.parent / "transcripts" / f"{stem}.txt"
        transcript = read_bytes_nofollow(transcript_path).decode("utf-8").removesuffix("\n")
        verification = compare_transcript(expected["text"], transcript, config.normalization)
        if not verification.passed:
            raise InputError(f"Baseline transcript changed for segment {expected['segment_id']}")
        lpcm = _lpcm_from_wav(audio_path, config)
        if any(repair for _, repair in _event_audio_blocks(events_path, lpcm)):
            raise InputError(f"Baseline segment {expected['segment_id']} has an unsafe partial turn")
        events = _read_events(events_path)
        if _mid_sentence_partial_turn_count(events):
            raise InputError(f"Baseline event evidence is unsafe for segment {expected['segment_id']}")

        turns.append(
            {
                **expected,
                "baseline_audio_path": _relative(audio_path),
                "baseline_events_path": _relative(events_path),
                "baseline_transcript_path": _relative(transcript_path),
                "baseline_duration_seconds": entry["duration_seconds"],
                "baseline_status": "verified_reuse",
                "context_status": "pending",
            }
        )

    chapter_tokens = normalized_tokens(spoken, config.normalization)
    target_tokens = tuple(
        token
        for expected in SEGMENTS
        for token in normalized_tokens(expected["text"], config.normalization)
    )
    starts = [
        index
        for index in range(len(chapter_tokens) - len(target_tokens) + 1)
        if chapter_tokens[index : index + len(target_tokens)] == target_tokens
    ]
    if len(starts) != 1:
        raise InputError("Pinned A/B paragraph is not one unique contiguous word sequence in chapter 1")

    failed_entry = next(
        (
            entry
            for entry in source_manifest.get("segments", [])
            if entry.get("segment_id") == "0024"
            and entry.get("status") == "mid_sentence_partial_turn"
        ),
        None,
    )
    if failed_entry is None:
        raise InputError("Cannot calibrate the partial-turn guard against rejected segment 0024")
    failed_audio = paths["workspace"] / failed_entry["audio_path"]
    failed_events = failed_audio.parent.parent / "events" / f"{failed_audio.stem}.jsonl"
    if _mid_sentence_partial_turn_count(_read_events(failed_events)) < 1:
        raise InputError("Persistent-session partial-turn guard failed its paid-artifact calibration")

    return config, turns


def _new_manifest(config: Any, turns: list[dict[str, Any]]) -> dict[str, Any]:
    previous = _read_json(_workspace() / PREVIOUS_MANIFEST_RELATIVE)
    return {
        "schema_version": 1,
        "experiment_id": EXPERIMENT_ID,
        "retry_of_manifest": PREVIOUS_MANIFEST_RELATIVE,
        "retry_of_attempt_id": previous["attempt_id"],
        "retry_authorized_by_user": True,
        "status": "planned",
        "planned_at": utc_now(),
        "source_spoken_sha256": EXPECTED_SPOKEN_SHA256,
        "request_binding_sha256": _request_binding(turns, config),
        "prompt_name": str(uuid.uuid4()),
        "attempt_id": None,
        "model_id": config.nova.model_id,
        "region": config.nova.region,
        "voice_id": "tiffany",
        "sample_rate_hz": config.nova.sample_rate_hz,
        "sample_size_bits": config.nova.sample_size_bits,
        "channels": config.nova.channels,
        "baseline_billable_calls": 0,
        "persistent_sessions_planned": 1,
        "context_turns_planned": len(turns),
        "word_count": sum(len(normalized_tokens(turn["text"], config.normalization)) for turn in turns),
        "turns": turns,
        "invocation_started_at": None,
        "rendered_at": None,
        "last_error": None,
    }


def prepare() -> int:
    paths = _paths()
    config, turns = _preflight()
    durable_mkdir(paths["root"])
    if paths["manifest"].exists():
        existing = _read_json(paths["manifest"])
        if (
            existing.get("status") == "planned"
            and existing.get("request_binding_sha256") == _request_binding(turns, config)
        ):
            print(json.dumps({"status": "planned", "manifest": str(paths["manifest"]), "turns": len(turns), "billable_sessions": 1, "baseline_calls": 0}))
            return 0
        raise InputError("Context experiment already exists; refusing to replace or retry it")
    manifest = _new_manifest(config, turns)
    atomic_write_json(paths["manifest"], manifest)
    print(json.dumps({"status": "planned", "manifest": str(paths["manifest"]), "turns": len(turns), "words": manifest["word_count"], "billable_sessions": 1, "baseline_calls": 0}))
    return 0


def _artifact_paths(segment_id: str) -> dict[str, Path]:
    root = _paths()["root"] / "context"
    return {
        "audio": root / "segments" / f"{segment_id}.wav",
        "events": root / "events" / f"{segment_id}.jsonl",
        "transcript": root / "transcripts" / f"{segment_id}.txt",
        "verification": root / "verification" / f"{segment_id}.json",
    }


def _persist_results(
    config: Any,
    manifest: dict[str, Any],
    results: tuple[NovaRenderResult, ...],
) -> list[dict[str, Any]]:
    outcomes: list[dict[str, Any]] = []
    for index, result in enumerate(results):
        turn = manifest["turns"][index]
        replayed = replay_output_events(
            result.events,
            expected_prompt_name=manifest["prompt_name"],
        )
        if (
            replayed.audio_lpcm != result.audio_lpcm
            or replayed.final_transcript != result.final_transcript
            or replayed.completion_stop_reason != result.completion_stop_reason
        ):
            raise InputError(f"Sequence result replay mismatch for segment {turn['segment_id']}")
        verification = compare_transcript(
            turn["text"],
            result.final_transcript,
            config.normalization,
        )
        unsafe_partial_turns = _mid_sentence_partial_turn_count(result.events)
        paths = _artifact_paths(turn["segment_id"])
        events_content = "".join(
            json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"
            for event in result.events
        )
        atomic_write_bytes(paths["audio"], _wav_bytes(result.audio_lpcm, config))
        atomic_write_text(paths["events"], events_content)
        atomic_write_text(paths["transcript"], result.final_transcript + "\n")
        atomic_write_json(paths["verification"], verification.to_dict())

        status = "accepted"
        if unsafe_partial_turns:
            status = "mid_sentence_partial_turn"
        elif not verification.passed:
            status = "fidelity_mismatch"
        outcome = {
            "context_status": status,
            "context_audio_path": _relative(paths["audio"]),
            "context_events_path": _relative(paths["events"]),
            "context_transcript_path": _relative(paths["transcript"]),
            "context_verification_path": _relative(paths["verification"]),
            "context_audio_sha256": sha256_file(paths["audio"]),
            "context_events_sha256": sha256_file(paths["events"]),
            "context_transcript_sha256": sha256_file(paths["transcript"]),
            "context_verification_sha256": sha256_file(paths["verification"]),
            "context_lpcm_sha256": sha256_bytes(result.audio_lpcm),
            "context_duration_seconds": round(
                len(result.audio_lpcm)
                / config.nova.sample_rate_hz
                / config.nova.channels
                / (config.nova.sample_size_bits // 8),
                3,
            ),
            "context_transcript": result.final_transcript,
            "exact_word_sequence": verification.passed,
            "coverage_ratio": verification.coverage_ratio,
            "mid_sentence_partial_turns": unsafe_partial_turns,
            "completion_stop_reason": result.completion_stop_reason,
        }
        turn.update(outcome)
        outcomes.append(outcome)
    return outcomes


def render() -> int:
    paths = _paths()
    config, turns = _preflight()
    if not paths["manifest"].is_file():
        raise InputError("Run --prepare before the paid context experiment")
    manifest = _read_json(paths["manifest"])
    if manifest.get("status") != "planned":
        raise InputError("Context experiment is not pending; refusing a duplicate paid session")
    if manifest.get("request_binding_sha256") != _request_binding(turns, config):
        raise InputError("Context experiment request binding changed after preparation")
    if manifest.get("source_spoken_sha256") != EXPECTED_SPOKEN_SHA256:
        raise InputError("Context experiment source binding changed after preparation")
    for turn in manifest["turns"]:
        if any(path.exists() for path in _artifact_paths(turn["segment_id"]).values()):
            raise InputError("Context artifacts already exist; refusing a duplicate paid session")

    manifest.update(
        {
            "status": "invoking",
            "attempt_id": secrets.token_hex(16),
            "invocation_started_at": utc_now(),
            "last_error": None,
        }
    )
    atomic_write_json(paths["manifest"], manifest)

    results: tuple[NovaRenderResult, ...] = ()
    error: BaseException | None = None
    try:
        results = render_text_sequence(
            tuple(turn["text"] for turn in manifest["turns"]),
            "tiffany",
            config.nova,
            prompt_name=manifest["prompt_name"],
            paid_render_authorized=True,
        )
    except NovaSequenceIncomplete as exc:
        results = exc.completed_results
        error = exc
    except BaseException as exc:
        error = exc

    try:
        outcomes = _persist_results(config, manifest, results)
        manifest["completed_context_turns"] = len(results)
        manifest["rendered_at"] = utc_now()
        if error is not None:
            manifest["status"] = "charge_uncertain"
            manifest["last_error"] = {
                "type": type(error).__name__,
                "message": (str(error) or type(error).__name__)[:1000],
            }
        elif len(outcomes) != len(manifest["turns"]):
            manifest["status"] = "charge_uncertain"
            manifest["last_error"] = {
                "type": "IncompleteSequence",
                "message": "Nova returned fewer context turns than requested",
            }
        elif any(outcome["context_status"] != "accepted" for outcome in outcomes):
            manifest["status"] = "rejected"
        else:
            manifest["status"] = "rendered"
        atomic_write_json(paths["manifest"], manifest)
    except BaseException as persistence_error:
        manifest["status"] = "charge_uncertain"
        manifest["last_error"] = {
            "type": type(persistence_error).__name__,
            "message": (str(persistence_error) or type(persistence_error).__name__)[:1000],
        }
        try:
            atomic_write_json(paths["manifest"], manifest)
        finally:
            raise

    print(json.dumps({"status": manifest["status"], "manifest": str(paths["manifest"]), "completed_context_turns": len(results), "requested_context_turns": len(manifest["turns"])}))
    if error is not None:
        raise error
    if manifest["status"] != "rendered":
        raise InputError(f"Context experiment finished with status {manifest['status']}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--prepare", action="store_true", help="Validate and persist the no-AWS experiment plan")
    mode.add_argument("--confirm-paid-render", action="store_true", help="Run the one prepared billable Nova session")
    args = parser.parse_args()
    try:
        return prepare() if args.prepare else render()
    except BaseException as exc:
        print(f"error: {str(exc) or type(exc).__name__}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
