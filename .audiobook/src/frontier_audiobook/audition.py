"""Audition planning, guarded rendering, and blind listener packaging."""

from __future__ import annotations

import csv
import io
import json
import math
import os
import re
import secrets
import uuid
import wave
from pathlib import Path
from typing import Any, Iterable

from .config import AuditionConfig, load_audition_config
from .errors import FidelityMismatch, InputError
from .manuscript import discover_chapter, extract_anchored_excerpt, markdown_to_spoken, read_chapter
from .nova import render_text, replay_output_events
from .util import (
    atomic_write_bytes,
    atomic_write_json,
    atomic_write_text,
    compact_utc_now,
    durable_mkdir,
    durable_replace,
    exclusive_file_lock,
    json_loads_strict,
    read_bytes_nofollow,
    read_json,
    resolve_inside,
    sha256_bytes,
    sha256_file,
    sha256_text,
    utc_now,
    workspace_relative,
)
from .verify import compare_transcript

PLAN_KIND = "frontier-nova-voice-audition"
PLAN_SCHEMA = 2
BLIND_KEY_SCHEMA = 1
PACKAGE_BINDING_SCHEMA = 1
BLIND_LABELS = ("A", "B", "C", "D")
BLIND_KEY_WARNING = "Keep this file out of the listener package until scoring is complete."
UNCERTAIN_STATUSES = frozenset({"invoking", "charge_uncertain"})
CALL_STATUSES = frozenset(
    {"pending", "invoking", "charge_uncertain", "fidelity_pass", "fidelity_mismatch"}
)
PLAN_FIELDS = frozenset(
    {
        "schema_version",
        "kind",
        "audition_id",
        "created_at",
        "updated_at",
        "status",
        "config_path",
        "config_sha256",
        "model_id",
        "region",
        "audio_format",
        "temperature",
        "system_prompt_sha256",
        "normalization",
        "voices",
        "excerpts",
        "calls",
        "blind_key_path",
        "package_path",
    }
)
EXCERPT_FIELDS = frozenset(
    {
        "id",
        "chapter",
        "movement",
        "pov_id",
        "purpose",
        "source_path",
        "chapter_body_sha256",
        "source_excerpt_sha256",
        "spoken_sha256",
        "word_count",
        "input_path",
    }
)
CALL_FIELDS = frozenset(
    {
        "call_id",
        "voice_id",
        "excerpt_id",
        "status",
        "audio_path",
        "transcript_path",
        "events_path",
        "verification_path",
        "audio_sha256",
        "transcript_sha256",
        "events_sha256",
        "verification_sha256",
        "duration_seconds",
        "rendered_at",
        "attempt_id",
        "prompt_name",
        "request_binding_sha256",
        "invocation_started_at",
        "charge_uncertain_at",
        "last_error",
        "reconciliation_history",
        "reconciliation_in_progress",
        "recovered_without_new_call",
    }
)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
ATTEMPT_PATTERN = re.compile(r"^[0-9a-f]{32}$")
AUDITION_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$")


def _default_audition_id(config: AuditionConfig) -> str:
    identity = sha256_text(
        config.sha256 + "|" + "|".join(config.voices) + "|" + "|".join(item.id for item in config.excerpts)
    )[:8]
    return f"audition-{compact_utc_now()}-{identity}"


def create_plan(config: AuditionConfig, audition_id: str | None = None) -> Path:
    selected_id = audition_id or _default_audition_id(config)
    if not AUDITION_ID.fullmatch(selected_id):
        raise InputError(f"Invalid audition ID: {selected_id!r}")
    run_root = config.output_root / selected_id
    if run_root.exists():
        raise InputError(f"Audition directory already exists; refusing to overwrite: {run_root}")

    excerpt_records: list[dict[str, Any]] = []
    excerpt_text: dict[str, str] = {}
    for spec in config.excerpts:
        chapter = read_chapter(discover_chapter(config.manuscript_root, spec.chapter))
        source = extract_anchored_excerpt(chapter.body, spec.start_anchor, spec.end_anchor, spec.id)
        spoken = markdown_to_spoken(source, spec.id)
        input_path = run_root / "inputs" / f"{spec.id}.txt"
        atomic_write_text(input_path, spoken + "\n")
        excerpt_text[spec.id] = spoken
        excerpt_records.append(
            {
                "id": spec.id,
                "chapter": chapter.chapter,
                "movement": chapter.movement,
                "pov_id": chapter.pov_id,
                "purpose": spec.purpose,
                "source_path": workspace_relative(config.workspace_root, chapter.path),
                "chapter_body_sha256": chapter.body_sha256,
                "source_excerpt_sha256": sha256_text(source),
                "spoken_sha256": sha256_text(spoken),
                "word_count": len(spoken.split()),
                "input_path": workspace_relative(config.workspace_root, input_path),
            }
        )

    calls: list[dict[str, Any]] = []
    for voice in config.voices:
        for excerpt in excerpt_records:
            stem = f"{excerpt['id']}--{voice}"
            calls.append(
                {
                    "call_id": stem,
                    "voice_id": voice,
                    "excerpt_id": excerpt["id"],
                    "status": "pending",
                    "audio_path": workspace_relative(config.workspace_root, run_root / "renders" / voice / f"{excerpt['id']}.wav"),
                    "transcript_path": workspace_relative(config.workspace_root, run_root / "transcripts" / voice / f"{excerpt['id']}.txt"),
                    "events_path": workspace_relative(config.workspace_root, run_root / "events" / voice / f"{excerpt['id']}.jsonl"),
                    "verification_path": workspace_relative(config.workspace_root, run_root / "verification" / voice / f"{excerpt['id']}.json"),
                    "audio_sha256": None,
                    "transcript_sha256": None,
                    "events_sha256": None,
                    "verification_sha256": None,
                    "duration_seconds": None,
                    "rendered_at": None,
                    "attempt_id": None,
                    "prompt_name": None,
                    "request_binding_sha256": None,
                    "invocation_started_at": None,
                    "charge_uncertain_at": None,
                    "last_error": None,
                    "reconciliation_history": [],
                    "reconciliation_in_progress": None,
                    "recovered_without_new_call": False,
                }
            )

    now = utc_now()
    plan = {
        "schema_version": PLAN_SCHEMA,
        "kind": PLAN_KIND,
        "audition_id": selected_id,
        "created_at": now,
        "updated_at": now,
        "status": "planned",
        "config_path": workspace_relative(config.workspace_root, config.path),
        "config_sha256": config.sha256,
        "model_id": config.nova.model_id,
        "region": config.nova.region,
        "audio_format": {
            "media_type": "audio/lpcm",
            "container": "wav",
            "sample_rate_hz": config.nova.sample_rate_hz,
            "sample_size_bits": config.nova.sample_size_bits,
            "channels": config.nova.channels,
        },
        "temperature": config.nova.temperature,
        "system_prompt_sha256": sha256_text(config.nova.system_prompt),
        "normalization": config.normalization,
        "voices": list(config.voices),
        "excerpts": excerpt_records,
        "calls": calls,
        "blind_key_path": workspace_relative(config.workspace_root, run_root / "blind-key.json"),
        "package_path": None,
    }
    plan_path = run_root / "plan.json"
    atomic_write_json(plan_path, plan)
    return plan_path


def _require_exact_keys(value: dict[str, Any], expected: frozenset[str], label: str) -> None:
    actual = set(value)
    if actual != set(expected):
        raise InputError(
            f"{label} keys are invalid; missing={sorted(set(expected) - actual)}, "
            f"unknown={sorted(actual - set(expected))}"
        )


def _is_sha256(value: Any) -> bool:
    return isinstance(value, str) and SHA256_PATTERN.fullmatch(value) is not None


def _derived_plan_status(plan: dict[str, Any]) -> str:
    statuses = [call.get("status") for call in plan.get("calls", [])]
    if any(status in UNCERTAIN_STATUSES for status in statuses):
        return "render_blocked"
    if any(status == "fidelity_mismatch" for status in statuses):
        return "fidelity_mismatch"
    if statuses and all(status == "fidelity_pass" for status in statuses):
        return "packaged" if plan.get("package_path") is not None else "rendered"
    if any(status != "pending" for status in statuses):
        return "rendering"
    return "planned"


def _persist_plan(plan_path: Path, plan: dict[str, Any]) -> None:
    plan["updated_at"] = utc_now()
    plan["status"] = _derived_plan_status(plan)
    atomic_write_json(plan_path, plan)


def _quarantine_destination(
    workspace_root: Path,
    run_root: Path,
    artifact: str,
    source: Path,
    value: Any,
) -> Path:
    if not isinstance(value, str) or not value:
        raise InputError("Reconciliation quarantine path must be nonblank text")
    destination = resolve_inside(workspace_root, value)
    uncertain_root = resolve_inside(run_root, "uncertain-evidence")
    evidence_root = destination.parent
    if evidence_root.parent != uncertain_root or not evidence_root.name:
        raise InputError("Reconciliation destination must remain inside this audition's evidence root")
    expected = resolve_inside(evidence_root, f"{artifact}{source.suffix}")
    if destination != expected:
        raise InputError("Reconciliation destination filename is not canonical")
    return destination


def _validate_reconciliation_history(
    workspace_root: Path,
    run_root: Path,
    paths: dict[str, Path],
    call_id: str,
    history: Any,
) -> None:
    if not isinstance(history, list):
        raise InputError(f"Call {call_id} has malformed reconciliation_history")
    for index, entry in enumerate(history):
        expected_fields = {
            "reconciled_at",
            "prior_status",
            "prior_attempt_id",
            "decision",
            "quarantined_evidence",
        }
        if not isinstance(entry, dict) or set(entry) != expected_fields:
            raise InputError(f"Call {call_id} has malformed reconciliation history entry {index}")
        if not isinstance(entry["reconciled_at"], str) or not entry["reconciled_at"]:
            raise InputError(f"Call {call_id} has invalid reconciliation timestamp")
        if entry["prior_status"] not in UNCERTAIN_STATUSES:
            raise InputError(f"Call {call_id} has invalid reconciliation prior_status")
        prior_attempt = entry["prior_attempt_id"]
        if not isinstance(prior_attempt, str) or ATTEMPT_PATTERN.fullmatch(prior_attempt) is None:
            raise InputError(f"Call {call_id} has invalid reconciliation prior_attempt_id")
        if entry["decision"] != "operator_acknowledged_possible_duplicate_charge_and_reset":
            raise InputError(f"Call {call_id} has invalid reconciliation decision")
        evidence = entry["quarantined_evidence"]
        if not isinstance(evidence, list):
            raise InputError(f"Call {call_id} has malformed reconciliation history evidence")
        seen: set[str] = set()
        evidence_roots: set[Path] = set()
        for record in evidence:
            if (
                not isinstance(record, dict)
                or set(record) != {"artifact", "sha256", "quarantined_path"}
                or record.get("artifact") not in paths
                or record["artifact"] in seen
                or not _is_sha256(record.get("sha256"))
            ):
                raise InputError(f"Call {call_id} has malformed reconciliation history evidence")
            artifact = record["artifact"]
            seen.add(artifact)
            destination = _quarantine_destination(
                workspace_root,
                run_root,
                artifact,
                paths[artifact],
                record.get("quarantined_path"),
            )
            evidence_roots.add(destination.parent)
            if not destination.is_file() or sha256_file(destination) != record["sha256"]:
                raise InputError(f"Call {call_id} has missing or altered reconciliation evidence")
        if len(evidence_roots) > 1:
            raise InputError(f"Call {call_id} reconciliation history spans multiple evidence roots")


def _validate_reconciliation_journal(
    workspace_root: Path,
    run_root: Path,
    paths: dict[str, Path],
    call_id: str,
    status: str,
    attempt_id: str | None,
    journal: Any,
) -> None:
    expected_fields = {
        "schema_version",
        "started_at",
        "prior_status",
        "prior_attempt_id",
        "evidence_root",
        "evidence",
    }
    if not isinstance(journal, dict) or set(journal) != expected_fields:
        raise InputError(f"Call {call_id} has a malformed reconciliation journal")
    if type(journal["schema_version"]) is not int or journal["schema_version"] != 1:
        raise InputError(f"Call {call_id} has an unsupported reconciliation journal")
    if not isinstance(journal["started_at"], str) or not journal["started_at"]:
        raise InputError(f"Call {call_id} has an invalid reconciliation journal timestamp")
    if journal["prior_status"] != status or status not in UNCERTAIN_STATUSES:
        raise InputError(f"Call {call_id} reconciliation journal status is inconsistent")
    if journal["prior_attempt_id"] != attempt_id:
        raise InputError(f"Call {call_id} reconciliation journal attempt is inconsistent")
    if not isinstance(journal["evidence_root"], str) or not journal["evidence_root"]:
        raise InputError(f"Call {call_id} reconciliation journal has no evidence root")
    evidence_root = resolve_inside(workspace_root, journal["evidence_root"])
    uncertain_root = resolve_inside(run_root, "uncertain-evidence")
    if evidence_root.parent != uncertain_root or not evidence_root.name:
        raise InputError(f"Call {call_id} reconciliation journal escapes its evidence root")

    evidence = journal["evidence"]
    if not isinstance(evidence, list):
        raise InputError(f"Call {call_id} has malformed reconciliation evidence")
    seen: set[str] = set()
    for record in evidence:
        if (
            not isinstance(record, dict)
            or set(record) != {"artifact", "sha256", "source_path", "quarantined_path"}
            or record.get("artifact") not in paths
            or record["artifact"] in seen
            or not _is_sha256(record.get("sha256"))
            or not isinstance(record.get("source_path"), str)
        ):
            raise InputError(f"Call {call_id} has malformed reconciliation evidence")
        artifact = record["artifact"]
        seen.add(artifact)
        source = resolve_inside(workspace_root, record["source_path"])
        if source != paths[artifact]:
            raise InputError(f"Call {call_id} reconciliation source is not canonical")
        destination = _quarantine_destination(
            workspace_root,
            run_root,
            artifact,
            source,
            record.get("quarantined_path"),
        )
        if destination.parent != evidence_root:
            raise InputError(f"Call {call_id} reconciliation destination uses the wrong evidence root")
        source_exists = source.exists()
        destination_exists = destination.exists()
        if source_exists == destination_exists:
            raise InputError(f"Call {call_id} has missing or ambiguous reconciliation evidence")
        current = source if source_exists else destination
        if not current.is_file() or sha256_file(current) != record["sha256"]:
            raise InputError(f"Call {call_id} reconciliation evidence hash changed")

    untracked = [name for name, path in paths.items() if path.exists() and name not in seen]
    if untracked:
        raise InputError(f"Call {call_id} has unjournaled reconciliation evidence: {untracked}")


def _validate_call_record(
    workspace_root: Path,
    run_root: Path,
    call: Any,
    voice: str,
    excerpt_id: str,
) -> None:
    if not isinstance(call, dict):
        raise InputError("Audition plan contains a non-object call record")
    _require_exact_keys(call, CALL_FIELDS, f"call {voice}/{excerpt_id}")
    call_id = f"{excerpt_id}--{voice}"
    if (call.get("call_id"), call.get("voice_id"), call.get("excerpt_id")) != (
        call_id,
        voice,
        excerpt_id,
    ):
        raise InputError(f"Call matrix identity is invalid for {voice}/{excerpt_id}")
    expected_paths = {
        "audio_path": run_root / "renders" / voice / f"{excerpt_id}.wav",
        "transcript_path": run_root / "transcripts" / voice / f"{excerpt_id}.txt",
        "events_path": run_root / "events" / voice / f"{excerpt_id}.jsonl",
        "verification_path": run_root / "verification" / voice / f"{excerpt_id}.json",
    }
    for field, expected in expected_paths.items():
        if call.get(field) != workspace_relative(workspace_root, expected):
            raise InputError(f"Call {call_id} has a noncanonical {field}")
    paths = {
        name: resolve_inside(workspace_root, str(call[f"{name}_path"]))
        for name in ("audio", "transcript", "events", "verification")
    }

    status = call.get("status")
    if status not in CALL_STATUSES:
        raise InputError(f"Call {call_id} has unsupported status {status!r}")
    for field in ("audio_sha256", "transcript_sha256", "events_sha256", "verification_sha256"):
        value = call.get(field)
        if value is not None and not _is_sha256(value):
            raise InputError(f"Call {call_id} has invalid {field}")
    duration = call.get("duration_seconds")
    if duration is not None and (
        isinstance(duration, bool)
        or not isinstance(duration, (int, float))
        or not math.isfinite(float(duration))
        or duration < 0
    ):
        raise InputError(f"Call {call_id} has invalid duration_seconds")
    for field in ("rendered_at", "invocation_started_at", "charge_uncertain_at"):
        value = call.get(field)
        if value is not None and (not isinstance(value, str) or not value):
            raise InputError(f"Call {call_id} has invalid {field}")
    attempt_id = call.get("attempt_id")
    if attempt_id is not None and (
        not isinstance(attempt_id, str) or ATTEMPT_PATTERN.fullmatch(attempt_id) is None
    ):
        raise InputError(f"Call {call_id} has invalid attempt_id")
    prompt_name = call.get("prompt_name")
    if prompt_name is not None:
        if not isinstance(prompt_name, str):
            raise InputError(f"Call {call_id} has invalid prompt_name")
        try:
            if str(uuid.UUID(prompt_name)) != prompt_name:
                raise ValueError
        except ValueError as exc:
            raise InputError(f"Call {call_id} has invalid prompt_name") from exc
    request_binding = call.get("request_binding_sha256")
    if request_binding is not None and not _is_sha256(request_binding):
        raise InputError(f"Call {call_id} has invalid request_binding_sha256")
    last_error = call.get("last_error")
    if last_error is not None and (
        not isinstance(last_error, dict)
        or set(last_error) != {"type", "message"}
        or any(not isinstance(last_error[field], str) or not last_error[field] for field in ("type", "message"))
    ):
        raise InputError(f"Call {call_id} has malformed last_error")
    if not isinstance(call.get("recovered_without_new_call"), bool):
        raise InputError(f"Call {call_id} has invalid recovered_without_new_call")

    _validate_reconciliation_history(
        workspace_root,
        run_root,
        paths,
        call_id,
        call.get("reconciliation_history"),
    )
    journal = call.get("reconciliation_in_progress")
    if journal is not None:
        _validate_reconciliation_journal(
            workspace_root,
            run_root,
            paths,
            call_id,
            status,
            attempt_id,
            journal,
        )

    invocation_fields = (attempt_id, prompt_name, request_binding, call.get("invocation_started_at"))
    hash_fields = tuple(
        call.get(field)
        for field in ("audio_sha256", "transcript_sha256", "events_sha256", "verification_sha256")
    )
    if status == "pending":
        if (
            any(value is not None for value in invocation_fields + hash_fields)
            or duration is not None
            or call.get("rendered_at") is not None
            or call.get("charge_uncertain_at") is not None
            or last_error is not None
            or journal is not None
            or call["recovered_without_new_call"]
        ):
            raise InputError(f"Pending call {call_id} contains invocation or artifact state")
    elif status == "invoking":
        if (
            any(value is None for value in invocation_fields)
            or any(value is not None for value in hash_fields)
            or duration is not None
            or call.get("rendered_at") is not None
            or call.get("charge_uncertain_at") is not None
            or last_error is not None
            or call["recovered_without_new_call"]
        ):
            raise InputError(f"Invoking call {call_id} has inconsistent state")
    elif status == "charge_uncertain":
        if (
            any(value is None for value in invocation_fields)
            or any(value is not None for value in hash_fields)
            or duration is not None
            or call.get("rendered_at") is not None
            or call.get("charge_uncertain_at") is None
            or last_error is None
            or call["recovered_without_new_call"]
        ):
            raise InputError(f"Charge-uncertain call {call_id} has inconsistent state")
    else:
        if (
            any(value is None for value in invocation_fields + hash_fields)
            or duration is None
            or duration <= 0
            or call.get("rendered_at") is None
            or call.get("charge_uncertain_at") is not None
            or last_error is not None
            or journal is not None
            or (status == "fidelity_mismatch" and call["recovered_without_new_call"])
        ):
            raise InputError(f"Completed call {call_id} has inconsistent integrity state")


def load_plan(workspace_root: Path, plan_path: Path) -> tuple[dict[str, Any], AuditionConfig]:
    value = read_json(plan_path)
    if not isinstance(value, dict):
        raise InputError(f"Not a supported audition plan: {plan_path}")
    _require_exact_keys(value, PLAN_FIELDS, "audition plan")
    if (
        type(value.get("schema_version")) is not int
        or value.get("schema_version") != PLAN_SCHEMA
        or value.get("kind") != PLAN_KIND
    ):
        raise InputError(f"Not a supported audition plan: {plan_path}")
    audition_id = value.get("audition_id")
    if not isinstance(audition_id, str) or AUDITION_ID.fullmatch(audition_id) is None:
        raise InputError("Audition plan has an invalid audition_id")
    for field in ("created_at", "updated_at"):
        if not isinstance(value.get(field), str) or not value[field]:
            raise InputError(f"Audition plan has invalid {field}")

    config_path_value = value.get("config_path")
    if not isinstance(config_path_value, str):
        raise InputError("Audition plan has no valid config_path")
    config_path = resolve_inside(workspace_root, config_path_value)
    config = load_audition_config(config_path, workspace_root)
    if value.get("config_path") != workspace_relative(workspace_root, config.path):
        raise InputError("Audition plan config_path is not canonical")
    if value.get("config_sha256") != config.sha256:
        raise InputError("Audition config changed after planning; create a new plan")

    run_root = resolve_inside(config.output_root, audition_id)
    canonical_plan_path = resolve_inside(run_root, "plan.json")
    if plan_path.expanduser().resolve() != canonical_plan_path:
        raise InputError(
            f"Audition plan must be loaded from its canonical path: {canonical_plan_path}"
        )
    if value.get("model_id") != config.nova.model_id or value.get("region") != config.nova.region:
        raise InputError("Audition plan model or region does not match the pinned config")
    audio_format = value.get("audio_format")
    expected_audio_fields = {
        "media_type",
        "container",
        "sample_rate_hz",
        "sample_size_bits",
        "channels",
    }
    if not isinstance(audio_format, dict) or set(audio_format) != expected_audio_fields:
        raise InputError("Audition plan audio format schema is invalid")
    if (
        audio_format.get("media_type") != "audio/lpcm"
        or audio_format.get("container") != "wav"
        or type(audio_format.get("sample_rate_hz")) is not int
        or audio_format["sample_rate_hz"] != config.nova.sample_rate_hz
        or type(audio_format.get("sample_size_bits")) is not int
        or audio_format["sample_size_bits"] != config.nova.sample_size_bits
        or type(audio_format.get("channels")) is not int
        or audio_format["channels"] != config.nova.channels
    ):
        raise InputError("Audition plan audio format does not match the pinned config")
    temperature = value.get("temperature")
    if (
        type(temperature) is not float
        or not math.isfinite(temperature)
        or temperature != config.nova.temperature
    ):
        raise InputError("Audition plan temperature does not match the pinned config")
    if value.get("system_prompt_sha256") != sha256_text(config.nova.system_prompt):
        raise InputError("Audition plan system prompt does not match the pinned config")
    if value.get("normalization") != config.normalization:
        raise InputError("Audition plan normalization does not match the pinned config")
    if value.get("voices") != list(config.voices):
        raise InputError("Audition plan voices do not exactly match the pinned config")
    expected_blind_key = workspace_relative(workspace_root, run_root / "blind-key.json")
    if value.get("blind_key_path") != expected_blind_key:
        raise InputError("Audition plan blind_key_path is not canonical")
    package_path = value.get("package_path")
    expected_package_path = workspace_relative(workspace_root, config.package_root / audition_id)
    if package_path is not None and (
        not isinstance(package_path, str) or package_path != expected_package_path
    ):
        raise InputError("Audition plan package_path is not canonical")

    excerpts = value.get("excerpts")
    if not isinstance(excerpts, list) or len(excerpts) != len(config.excerpts):
        raise InputError("Audition plan excerpt matrix is incomplete")
    for record, spec in zip(excerpts, config.excerpts, strict=True):
        if not isinstance(record, dict):
            raise InputError("Audition plan contains a non-object excerpt")
        _require_exact_keys(record, EXCERPT_FIELDS, f"excerpt {spec.id}")
        chapter_path = discover_chapter(config.manuscript_root, spec.chapter)
        if (
            record.get("id") != spec.id
            or type(record.get("chapter")) is not int
            or record["chapter"] != spec.chapter
            or record.get("purpose") != spec.purpose
            or record.get("source_path") != workspace_relative(workspace_root, chapter_path)
            or record.get("input_path")
            != workspace_relative(workspace_root, run_root / "inputs" / f"{spec.id}.txt")
        ):
            raise InputError(f"Excerpt record {spec.id!r} is not canonical")
        if (
            not isinstance(record.get("movement"), str)
            or not record["movement"]
            or not isinstance(record.get("pov_id"), str)
            or not record["pov_id"]
            or isinstance(record.get("word_count"), bool)
            or not isinstance(record.get("word_count"), int)
            or record["word_count"] < 1
        ):
            raise InputError(f"Excerpt record {spec.id!r} has invalid metadata")
        for field in ("chapter_body_sha256", "source_excerpt_sha256", "spoken_sha256"):
            if not _is_sha256(record.get(field)):
                raise InputError(f"Excerpt record {spec.id!r} has invalid {field}")

    calls = value.get("calls")
    expected_pairs = [
        (voice, spec.id)
        for voice in config.voices
        for spec in config.excerpts
    ]
    if not isinstance(calls, list) or len(calls) != len(expected_pairs):
        raise InputError("Audition plan call matrix is incomplete")
    for call, (voice, excerpt_id) in zip(calls, expected_pairs, strict=True):
        _validate_call_record(workspace_root, run_root, call, voice, excerpt_id)

    if package_path is not None:
        if not all(call.get("status") == "fidelity_pass" for call in calls):
            raise InputError("Audition plan declares a package before every call passed fidelity")
        _validate_declared_package(workspace_root, value, config)

    expected_status = _derived_plan_status(value)
    if value.get("status") != expected_status:
        raise InputError(
            f"Audition plan status is inconsistent; expected {expected_status!r}, got {value.get('status')!r}"
        )
    return value, config


def _current_excerpt_text(config: AuditionConfig, excerpt_record: dict[str, Any]) -> str:
    excerpt_id = excerpt_record.get("id")
    spec = next((item for item in config.excerpts if item.id == excerpt_id), None)
    if spec is None:
        raise InputError(f"Plan references unknown excerpt {excerpt_id!r}")
    chapter = read_chapter(discover_chapter(config.manuscript_root, spec.chapter))
    source = extract_anchored_excerpt(chapter.body, spec.start_anchor, spec.end_anchor, spec.id)
    spoken = markdown_to_spoken(source, spec.id)
    if chapter.body_sha256 != excerpt_record.get("chapter_body_sha256"):
        raise InputError(f"Chapter {spec.chapter} changed after the audition was planned")
    if sha256_text(source) != excerpt_record.get("source_excerpt_sha256"):
        raise InputError(f"Source excerpt {spec.id!r} changed after planning")
    if sha256_text(spoken) != excerpt_record.get("spoken_sha256"):
        raise InputError(f"Spoken excerpt {spec.id!r} changed after planning")
    input_path = resolve_inside(config.workspace_root, str(excerpt_record.get("input_path", "")))
    try:
        prepared = read_bytes_nofollow(input_path).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError(f"Cannot decode planned excerpt input {input_path}: {exc}") from exc
    if prepared != spoken + "\n":
        raise InputError(f"Prepared input for {spec.id!r} is missing or stale")
    return spoken


def selected_calls(
    plan: dict[str, Any], voices: Iterable[str] | None = None, excerpts: Iterable[str] | None = None
) -> list[dict[str, Any]]:
    voice_filter = set(voices or [])
    excerpt_filter = set(excerpts or [])
    known_voices = set(plan.get("voices", []))
    known_excerpts = {item.get("id") for item in plan.get("excerpts", [])}
    if voice_filter - known_voices:
        raise InputError(f"Unknown selected voices: {sorted(voice_filter - known_voices)}")
    if excerpt_filter - known_excerpts:
        raise InputError(f"Unknown selected excerpts: {sorted(excerpt_filter - known_excerpts)}")
    selected = [
        item
        for item in plan["calls"]
        if (not voice_filter or item.get("voice_id") in voice_filter)
        and (not excerpt_filter or item.get("excerpt_id") in excerpt_filter)
    ]
    if not selected:
        raise InputError("No audition calls match the requested filters")
    return selected


def dry_run_render(
    plan: dict[str, Any], config: AuditionConfig, voices: Iterable[str] | None, excerpts: Iterable[str] | None
) -> list[dict[str, str]]:
    excerpt_by_id = {item["id"]: item for item in plan["excerpts"]}
    result: list[dict[str, str]] = []
    for call in selected_calls(plan, voices, excerpts):
        excerpt = excerpt_by_id[call["excerpt_id"]]
        _current_excerpt_text(config, excerpt)
        result.append(
            {
                "call_id": call["call_id"],
                "voice_id": call["voice_id"],
                "excerpt_id": call["excerpt_id"],
                "current_status": call["status"],
            }
        )
    return result


def _wav_bytes(lpcm: bytes, config: AuditionConfig) -> bytes:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as output:
        output.setnchannels(config.nova.channels)
        output.setsampwidth(config.nova.sample_size_bits // 8)
        output.setframerate(config.nova.sample_rate_hz)
        output.writeframes(lpcm)
    return buffer.getvalue()


def _artifact_paths(workspace_root: Path, call: dict[str, Any]) -> dict[str, Path]:
    return {
        name: resolve_inside(workspace_root, str(call[f"{name}_path"]))
        for name in ("audio", "transcript", "events", "verification")
    }


def _request_binding_sha256(call: dict[str, Any], spoken: str, config: AuditionConfig) -> str:
    request = {
        "schema_version": 1,
        "model_id": config.nova.model_id,
        "region": config.nova.region,
        "voice_id": call["voice_id"],
        "excerpt_id": call["excerpt_id"],
        "spoken_sha256": sha256_text(spoken),
        "system_prompt_sha256": sha256_text(config.nova.system_prompt),
        "audio": {
            "sample_rate_hz": config.nova.sample_rate_hz,
            "sample_size_bits": config.nova.sample_size_bits,
            "channels": config.nova.channels,
        },
        "inference": {
            "max_tokens": config.nova.max_tokens,
            "top_p": config.nova.top_p,
            "temperature": config.nova.temperature,
        },
    }
    return sha256_text(json.dumps(request, ensure_ascii=False, separators=(",", ":"), sort_keys=True))


MIN_SECONDS_PER_EXPECTED_WORD = 0.25
MIN_TRANSCRIPT_COVERAGE = 0.85


def fidelity_accepted(
    verification: Any,
    duration_seconds: float,
    *,
    accept_verbatim_prefix: bool = False,
) -> bool:
    """Decide whether a render may be kept.

    Exact verbatim transcripts always pass. When the operator explicitly opts in,
    a render is also accepted if every transcribed word is a verbatim in-order
    prefix of the source and there is positive evidence the audio is not
    truncated. Nova's FINAL transcript stream lags its audio, so a shortfall in
    transcript coverage alone does not prove truncation. Two independent kinds of
    evidence are accepted:

    * transcript coverage, when Nova confirmed nearly every word was spoken, or
    * audio duration, when the clip is long enough to contain the whole excerpt.
    """

    if verification.passed:
        return True
    if not accept_verbatim_prefix or not verification.transcript_is_verbatim_prefix:
        return False
    if verification.coverage_ratio >= MIN_TRANSCRIPT_COVERAGE:
        return True
    return duration_seconds >= MIN_SECONDS_PER_EXPECTED_WORD * verification.expected_token_count


def _validate_call_artifacts(
    workspace_root: Path,
    call: dict[str, Any],
    spoken: str,
    config: AuditionConfig,
    *,
    allow_fidelity_mismatch: bool = False,
    accept_verbatim_prefix: bool = False,
) -> dict[str, Any]:
    paths = _artifact_paths(workspace_root, call)
    expected_request_binding = _request_binding_sha256(call, spoken, config)
    if call.get("request_binding_sha256") != expected_request_binding:
        raise InputError(f"Stored request binding is missing or stale for {call['call_id']}")
    prompt_name = call.get("prompt_name")
    if not isinstance(prompt_name, str) or not prompt_name:
        raise InputError(f"Stored prompt identity is missing for {call['call_id']}")
    missing = [name for name, path in paths.items() if not path.is_file()]
    if missing:
        raise InputError(f"Render artifacts are incomplete for {call['call_id']}: missing={missing}")

    try:
        transcript_file = read_bytes_nofollow(paths["transcript"]).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError(f"Cannot decode transcript for {call['call_id']}: {exc}") from exc
    if not transcript_file.endswith("\n"):
        raise InputError(f"Transcript file is not in the canonical newline-terminated form: {call['call_id']}")
    transcript = transcript_file[:-1]

    try:
        event_lines = read_bytes_nofollow(paths["events"]).decode("utf-8").splitlines()
        if not event_lines:
            raise InputError(f"Event log is empty for {call['call_id']}")
        events: list[dict[str, Any]] = []
        for line_number, line in enumerate(event_lines, start=1):
            event = json_loads_strict(line, f"event log line {line_number} for {call['call_id']}")
            if not isinstance(event, dict):
                raise InputError(
                    f"Event log line {line_number} contains a non-object for {call['call_id']}"
                )
            events.append(event)
    except UnicodeDecodeError as exc:
        raise InputError(f"Malformed event log for {call['call_id']}: {exc}") from exc

    verification = compare_transcript(spoken, transcript, config.normalization)
    if not verification.passed and not allow_fidelity_mismatch and not accept_verbatim_prefix:
        raise FidelityMismatch(f"Stored transcript no longer matches source for {call['call_id']}")
    if read_json(paths["verification"]) != verification.to_dict():
        raise InputError(f"Verification record is missing, stale, or tampered: {call['call_id']}")

    replayed = replay_output_events(events, expected_prompt_name=prompt_name)
    if replayed.final_transcript != transcript:
        raise InputError(f"Event log transcript does not match stored transcript for {call['call_id']}")

    try:
        audio_bytes = read_bytes_nofollow(paths["audio"])
        with wave.open(io.BytesIO(audio_bytes), "rb") as audio:
            if (
                audio.getframerate(),
                audio.getsampwidth() * 8,
                audio.getnchannels(),
                audio.getcomptype(),
            ) != (
                config.nova.sample_rate_hz,
                config.nova.sample_size_bits,
                config.nova.channels,
                "NONE",
            ):
                raise InputError(f"WAV format mismatch for {call['call_id']}")
            frame_count = audio.getnframes()
            frames = audio.readframes(frame_count)
    except (OSError, wave.Error) as exc:
        raise InputError(f"Malformed WAV for {call['call_id']}: {exc}") from exc
    if frame_count <= 0:
        raise InputError(f"WAV has no audio frames for {call['call_id']}")
    if frames != replayed.audio_lpcm:
        raise InputError(f"Event log audio does not match stored WAV for {call['call_id']}")
    if audio_bytes != _wav_bytes(replayed.audio_lpcm, config):
        raise InputError(f"WAV is not in canonical artifact form for {call['call_id']}")

    artifact_hashes = {
        "audio_sha256": sha256_bytes(audio_bytes),
        "transcript_sha256": sha256_text(transcript),
        "events_sha256": sha256_file(paths["events"]),
        "verification_sha256": sha256_file(paths["verification"]),
    }
    for field, actual in artifact_hashes.items():
        if call.get(field) not in (None, actual):
            raise InputError(f"{field.removesuffix('_sha256').capitalize()} hash mismatch for {call['call_id']}")

    duration_seconds = round(frame_count / config.nova.sample_rate_hz, 3)
    if not allow_fidelity_mismatch and not fidelity_accepted(
        verification,
        duration_seconds,
        accept_verbatim_prefix=accept_verbatim_prefix,
    ):
        raise FidelityMismatch(f"Stored transcript no longer matches source for {call['call_id']}")

    return {
        **artifact_hashes,
        "duration_seconds": duration_seconds,
    }


def _validate_render_result(result: Any, prompt_name: str) -> Any:
    replayed = replay_output_events(result.events, expected_prompt_name=prompt_name)
    if replayed.final_transcript != result.final_transcript:
        raise InputError("Nova event transcript does not match the adapter render result")
    if replayed.audio_lpcm != result.audio_lpcm:
        raise InputError("Nova event audio does not match the adapter render result")
    if replayed.completion_stop_reason != result.completion_stop_reason:
        raise InputError("Nova event completion does not match the adapter render result")
    return replayed


def _lexical_absolute(path: Path) -> Path:
    """Make a path absolute without following a component changed after validation."""

    return Path(os.path.abspath(os.fspath(path.expanduser())))


def _audition_lock_path(plan_path: Path) -> Path:
    return plan_path.parent / ".audition.lock"


def render_plan(
    workspace_root: Path,
    plan_path: Path,
    voices: Iterable[str] | None = None,
    excerpts: Iterable[str] | None = None,
    *,
    paid_render_authorized: bool = False,
    accept_verbatim_prefix: bool = False,
) -> int:
    if not paid_render_authorized:
        raise InputError("Refusing billable render plan without explicit paid-render authorization")
    if os.name != "posix" or os.uname().sysname not in {"Darwin", "Linux"}:
        raise InputError("Paid Nova rendering is supported only on macOS and Linux")

    # Validate the canonical manifest before choosing the lock. A copied plan
    # cannot obtain an alternate lock for the same billing run.
    load_plan(workspace_root, plan_path)
    canonical_plan_path = _lexical_absolute(plan_path)
    plan_path = canonical_plan_path
    with exclusive_file_lock(_audition_lock_path(canonical_plan_path)):
        plan, config = load_plan(workspace_root, canonical_plan_path)
        excerpt_by_id = {item["id"]: item for item in plan["excerpts"]}
        rendered = 0
        for call in selected_calls(plan, voices, excerpts):
            excerpt = excerpt_by_id[call["excerpt_id"]]
            spoken = _current_excerpt_text(config, excerpt)
            paths = _artifact_paths(workspace_root, call)
            status = call.get("status")

            if status == "fidelity_pass":
                _validate_call_artifacts(
                    workspace_root,
                    call,
                    spoken,
                    config,
                    accept_verbatim_prefix=accept_verbatim_prefix,
                )
                continue
            if status == "fidelity_mismatch":
                raise FidelityMismatch(
                    f"Refusing to bill for an automatic retry of {call['call_id']}; create a new plan after review"
                )

            existing = [name for name, path in paths.items() if path.exists()]
            complete_artifacts = len(existing) == len(paths)
            if status in UNCERTAIN_STATUSES:
                if complete_artifacts:
                    recovered = _validate_call_artifacts(
                        workspace_root,
                        call,
                        spoken,
                        config,
                        accept_verbatim_prefix=accept_verbatim_prefix,
                    )
                    call.update(
                        {
                            "status": "fidelity_pass",
                            **recovered,
                            "rendered_at": call.get("rendered_at") or utc_now(),
                            "recovered_without_new_call": True,
                            "charge_uncertain_at": None,
                            "last_error": None,
                        }
                    )
                    _persist_plan(plan_path, plan)
                    continue
                raise InputError(
                    f"Charge is uncertain for {call['call_id']}; refusing another model call. "
                    "Inspect any evidence, then use `audition reconcile --call-id "
                    f"{call['call_id']} --confirm-possible-duplicate-charge` before a deliberate retry"
                )
            if status != "pending":
                raise InputError(f"Unexpected render status for {call['call_id']}: {status!r}")

            if existing:
                if not complete_artifacts:
                    raise InputError(
                        f"Partial paid render artifacts exist for {call['call_id']}; refusing overwrite: {existing}"
                    )
                recovered = _validate_call_artifacts(
                    workspace_root,
                    call,
                    spoken,
                    config,
                    accept_verbatim_prefix=accept_verbatim_prefix,
                )
                call.update(
                    {
                        "status": "fidelity_pass",
                        **recovered,
                        "rendered_at": call.get("rendered_at") or utc_now(),
                        "recovered_without_new_call": True,
                        "last_error": None,
                    }
                )
                _persist_plan(plan_path, plan)
                continue

            attempt_id = secrets.token_hex(16)
            prompt_name = str(uuid.uuid4())
            call.update(
                {
                    "status": "invoking",
                    "attempt_id": attempt_id,
                    "prompt_name": prompt_name,
                    "request_binding_sha256": _request_binding_sha256(call, spoken, config),
                    "invocation_started_at": utc_now(),
                    "charge_uncertain_at": None,
                    "last_error": None,
                    "reconciliation_in_progress": None,
                    "recovered_without_new_call": False,
                }
            )
            _persist_plan(plan_path, plan)

            verification = None
            try:
                result = render_text(
                    spoken,
                    call["voice_id"],
                    config.nova,
                    prompt_name=prompt_name,
                    paid_render_authorized=paid_render_authorized,
                )
                result = _validate_render_result(result, prompt_name)
                wav_content = _wav_bytes(result.audio_lpcm, config)
                events_content = "".join(
                    json.dumps(event, ensure_ascii=False, sort_keys=True) + "\n"
                    for event in result.events
                )
                atomic_write_bytes(paths["audio"], wav_content)
                atomic_write_text(paths["transcript"], result.final_transcript + "\n")
                atomic_write_text(paths["events"], events_content)

                verification = compare_transcript(spoken, result.final_transcript, config.normalization)
                atomic_write_json(paths["verification"], verification.to_dict())
                persisted = _validate_call_artifacts(
                    workspace_root,
                    call,
                    spoken,
                    config,
                    allow_fidelity_mismatch=True,
                )
                accepted = fidelity_accepted(
                    verification,
                    persisted["duration_seconds"],
                    accept_verbatim_prefix=accept_verbatim_prefix,
                )
                call.update(
                    {
                        "status": "fidelity_pass" if accepted else "fidelity_mismatch",
                        **persisted,
                        "rendered_at": utc_now(),
                        "charge_uncertain_at": None,
                        "last_error": None,
                    }
                )
                _persist_plan(plan_path, plan)
            except BaseException as exc:
                if call.get("status") == "invoking":
                    call.update(
                        {
                            "status": "charge_uncertain",
                            "charge_uncertain_at": utc_now(),
                            "last_error": {
                                "type": type(exc).__name__,
                                "message": (str(exc) or type(exc).__name__)[:500],
                            },
                        }
                    )
                    try:
                        _persist_plan(plan_path, plan)
                    except BaseException:
                        # The durable on-disk state remains `invoking`, which is
                        # treated as equally uncertain on the next invocation.
                        pass
                raise

            rendered += 1
            if not accepted:
                raise FidelityMismatch(
                    f"Fidelity mismatch for {call['call_id']}; audio remains quarantined in the build directory"
                )

        if all(item.get("status") == "fidelity_pass" for item in plan["calls"]):
            _persist_plan(plan_path, plan)
        return rendered


def revalidate_plan(
    workspace_root: Path,
    plan_path: Path,
    voices: Iterable[str] | None = None,
    excerpts: Iterable[str] | None = None,
    *,
    accept_verbatim_prefix: bool = False,
) -> list[dict[str, Any]]:
    """Re-apply the fidelity policy to already paid-for artifacts. Makes no model call."""

    load_plan(workspace_root, plan_path)
    plan_path = _lexical_absolute(plan_path)
    with exclusive_file_lock(_audition_lock_path(plan_path)):
        plan, config = load_plan(workspace_root, plan_path)
        excerpt_by_id = {item["id"]: item for item in plan["excerpts"]}
        outcomes: list[dict[str, Any]] = []
        for call in selected_calls(plan, voices, excerpts):
            status = call.get("status")
            if status in UNCERTAIN_STATUSES or status == "pending":
                continue
            spoken = _current_excerpt_text(config, excerpt_by_id[call["excerpt_id"]])
            paths = _artifact_paths(workspace_root, call)
            if any(not path.is_file() for path in paths.values()):
                continue

            transcript = read_bytes_nofollow(paths["transcript"]).decode("utf-8").removesuffix("\n")
            verification = compare_transcript(spoken, transcript, config.normalization)
            atomic_write_json(paths["verification"], verification.to_dict())
            call["verification_sha256"] = None
            try:
                persisted = _validate_call_artifacts(
                    workspace_root,
                    call,
                    spoken,
                    config,
                    accept_verbatim_prefix=accept_verbatim_prefix,
                )
            except FidelityMismatch:
                call["status"] = "fidelity_mismatch"
                outcomes.append(
                    {
                        "call_id": call["call_id"],
                        "status": "fidelity_mismatch",
                        "coverage_ratio": verification.coverage_ratio,
                        "verbatim_prefix": verification.transcript_is_verbatim_prefix,
                    }
                )
                continue
            call.update({"status": "fidelity_pass", **persisted})
            outcomes.append(
                {
                    "call_id": call["call_id"],
                    "status": "fidelity_pass",
                    "exact_transcript_match": verification.passed,
                    "coverage_ratio": verification.coverage_ratio,
                    "duration_seconds": persisted["duration_seconds"],
                }
            )
        _persist_plan(plan_path, plan)
        return outcomes


def reconcile_uncertain_call(
    workspace_root: Path,
    plan_path: Path,
    call_id: str,
    *,
    duplicate_charge_acknowledged: bool = False,
) -> dict[str, Any]:
    if not duplicate_charge_acknowledged:
        raise InputError(
            "Refusing to reset uncertain billing state without --confirm-possible-duplicate-charge"
        )

    load_plan(workspace_root, plan_path)
    plan_path = _lexical_absolute(plan_path)
    with exclusive_file_lock(_audition_lock_path(plan_path)):
        plan, config = load_plan(workspace_root, plan_path)
        matching = [call for call in plan["calls"] if call.get("call_id") == call_id]
        if len(matching) != 1:
            raise InputError(f"Plan does not contain exactly one call named {call_id!r}")
        call = matching[0]
        prior_status = call.get("status")
        if prior_status not in UNCERTAIN_STATUSES:
            raise InputError(
                f"Call {call_id!r} is not charge-uncertain; current status is {prior_status!r}"
            )

        excerpt_by_id = {item["id"]: item for item in plan["excerpts"]}
        excerpt = excerpt_by_id.get(call.get("excerpt_id"))
        if excerpt is None:
            raise InputError(f"Call {call_id!r} references an unknown excerpt")
        spoken = _current_excerpt_text(config, excerpt)
        paths = _artifact_paths(workspace_root, call)
        in_progress = call.get("reconciliation_in_progress")

        run_root = resolve_inside(workspace_root, str(plan["blind_key_path"])).parent
        uncertain_root = resolve_inside(run_root, "uncertain-evidence")
        if in_progress is None:
            existing = {name: path for name, path in paths.items() if path.exists()}
            if len(existing) == len(paths):
                try:
                    recovered = _validate_call_artifacts(workspace_root, call, spoken, config)
                except (InputError, FidelityMismatch):
                    pass
                else:
                    call.update(
                        {
                            "status": "fidelity_pass",
                            **recovered,
                            "rendered_at": call.get("rendered_at") or utc_now(),
                            "recovered_without_new_call": True,
                            "charge_uncertain_at": None,
                            "last_error": None,
                            "reconciliation_in_progress": None,
                        }
                    )
                    _persist_plan(plan_path, plan)
                    return {"call_id": call_id, "action": "recovered", "status": "fidelity_pass"}

            evidence_root = resolve_inside(
                uncertain_root,
                f"{compact_utc_now()}-{sha256_text(call_id)[:12]}-{secrets.token_hex(4)}",
            )
            evidence_records: list[dict[str, str]] = []
            for name, source in sorted(existing.items()):
                if not source.is_file():
                    raise InputError(f"Uncertain artifact is not a regular file: {source}")
                destination = resolve_inside(evidence_root, f"{name}{source.suffix}")
                evidence_records.append(
                    {
                        "artifact": name,
                        "sha256": sha256_file(source),
                        "source_path": workspace_relative(workspace_root, source),
                        "quarantined_path": workspace_relative(workspace_root, destination),
                    }
                )
            in_progress = {
                "schema_version": 1,
                "started_at": utc_now(),
                "prior_status": prior_status,
                "prior_attempt_id": call.get("attempt_id"),
                "evidence_root": workspace_relative(workspace_root, evidence_root),
                "evidence": evidence_records,
            }
            call["reconciliation_in_progress"] = in_progress
            _persist_plan(plan_path, plan)

        _validate_reconciliation_journal(
            workspace_root,
            run_root,
            paths,
            call_id,
            str(call.get("status")),
            call.get("attempt_id"),
            in_progress,
        )
        evidence_root = resolve_inside(workspace_root, in_progress["evidence_root"])
        journal_evidence = in_progress["evidence"]
        for record in journal_evidence:
            artifact = record["artifact"]
            source = resolve_inside(workspace_root, record["source_path"])
            destination = _quarantine_destination(
                workspace_root,
                run_root,
                artifact,
                source,
                record["quarantined_path"],
            )
            if destination.parent != evidence_root:
                raise InputError(f"Call {call_id!r} reconciliation destination uses the wrong evidence root")
            if source.exists() and destination.exists():
                raise InputError(f"Call {call_id!r} has ambiguous duplicate reconciliation evidence")
            if source.is_file():
                if sha256_file(source) != record["sha256"]:
                    raise InputError(f"Call {call_id!r} reconciliation source hash changed")
                durable_mkdir(destination.parent)
                durable_replace(source, destination, source_kind="file")
            elif not destination.is_file():
                raise InputError(f"Call {call_id!r} reconciliation evidence is missing")
            if sha256_file(destination) != record["sha256"]:
                raise InputError(f"Call {call_id!r} quarantined evidence hash mismatch")

        history = call["reconciliation_history"]
        history.append(
            {
                "reconciled_at": utc_now(),
                "prior_status": in_progress["prior_status"],
                "prior_attempt_id": in_progress.get("prior_attempt_id"),
                "decision": "operator_acknowledged_possible_duplicate_charge_and_reset",
                "quarantined_evidence": [
                    {
                        "artifact": record["artifact"],
                        "sha256": record["sha256"],
                        "quarantined_path": record["quarantined_path"],
                    }
                    for record in journal_evidence
                ],
            }
        )
        call.update(
            {
                "status": "pending",
                "audio_sha256": None,
                "transcript_sha256": None,
                "events_sha256": None,
                "verification_sha256": None,
                "duration_seconds": None,
                "rendered_at": None,
                "attempt_id": None,
                "prompt_name": None,
                "request_binding_sha256": None,
                "invocation_started_at": None,
                "charge_uncertain_at": None,
                "last_error": None,
                "reconciliation_history": history,
                "reconciliation_in_progress": None,
                "recovered_without_new_call": False,
            }
        )
        _persist_plan(plan_path, plan)
        return {
            "call_id": call_id,
            "action": "reset_to_pending",
            "status": "pending",
            "quarantined_artifacts": len(journal_evidence),
        }


def _strict_blind_mapping(plan: dict[str, Any], key: Any) -> dict[str, str]:
    expected_fields = {
        "schema_version",
        "audition_id",
        "created_at",
        "voice_by_label",
        "warning",
    }
    if not isinstance(key, dict) or set(key) != expected_fields:
        actual = set(key) if isinstance(key, dict) else set()
        raise InputError(
            "Blind key schema is invalid; "
            f"missing={sorted(expected_fields - actual)}, unknown={sorted(actual - expected_fields)}"
        )
    if type(key["schema_version"]) is not int or key["schema_version"] != BLIND_KEY_SCHEMA:
        raise InputError("Blind key schema_version must be 1")
    if key["audition_id"] != plan.get("audition_id"):
        raise InputError("Blind key audition_id does not match the plan")
    if not isinstance(key["created_at"], str) or not key["created_at"].strip():
        raise InputError("Blind key created_at must be nonblank text")
    if key["warning"] != BLIND_KEY_WARNING:
        raise InputError("Blind key warning is missing or altered")

    voices = plan.get("voices")
    if (
        not isinstance(voices, list)
        or len(voices) != len(BLIND_LABELS)
        or any(not isinstance(voice, str) or not voice for voice in voices)
        or len(set(voices)) != len(voices)
    ):
        raise InputError("Blind packaging requires exactly four unique configured voices")
    mapping = key["voice_by_label"]
    if not isinstance(mapping, dict) or set(mapping) != set(BLIND_LABELS):
        raise InputError("Blind key labels must be exactly A, B, C, and D")
    if any(not isinstance(label, str) or not isinstance(voice, str) for label, voice in mapping.items()):
        raise InputError("Blind key labels and voices must be text")
    ordered = {label: mapping[label] for label in BLIND_LABELS}
    if list(sorted(ordered.values())) != list(sorted(voices)) or len(set(ordered.values())) != len(voices):
        raise InputError("Blind key voices must be a unique permutation of the plan voices")
    return ordered


def _load_or_create_blind_mapping(
    plan: dict[str, Any],
    blind_key_path: Path,
) -> dict[str, str]:
    if not blind_key_path.exists():
        voices = plan.get("voices")
        if not isinstance(voices, list) or len(voices) != len(BLIND_LABELS):
            raise InputError("Blind packaging requires exactly four configured voices")
        shuffled = list(voices)
        secrets.SystemRandom().shuffle(shuffled)
        atomic_write_json(
            blind_key_path,
            {
                "schema_version": BLIND_KEY_SCHEMA,
                "audition_id": plan["audition_id"],
                "created_at": utc_now(),
                "voice_by_label": dict(zip(BLIND_LABELS, shuffled, strict=True)),
                "warning": BLIND_KEY_WARNING,
            },
        )
    return _strict_blind_mapping(plan, read_json(blind_key_path))


def _blind_mapping_sha256(mapping: dict[str, str]) -> str:
    canonical = json.dumps(mapping, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return sha256_text(canonical)


def _clip_specifications(
    workspace_root: Path,
    plan: dict[str, Any],
    mapping: dict[str, str],
) -> list[dict[str, Any]]:
    calls = plan["calls"]
    call_by_pair = {(item.get("voice_id"), item.get("excerpt_id")): item for item in calls}
    if len(call_by_pair) != len(calls):
        raise InputError("Plan contains duplicate voice/excerpt calls")
    excerpt_order = [item.get("id") for item in plan["excerpts"]]
    specifications: list[dict[str, Any]] = []
    for label in BLIND_LABELS:
        voice = mapping[label]
        for index, excerpt_id in enumerate(excerpt_order, start=1):
            call = call_by_pair.get((voice, excerpt_id))
            if call is None:
                raise InputError(f"Plan has no call for voice={voice!r}, excerpt={excerpt_id!r}")
            source = resolve_inside(workspace_root, str(call["audio_path"]))
            expected_hash = call.get("audio_sha256")
            if not _is_sha256(expected_hash):
                raise InputError(f"Plan has no validated audio hash for {call['call_id']}")
            specifications.append(
                {
                    "relative_path": f"clips/voice-{label.lower()}/{index:02d}-{excerpt_id}.wav",
                    "source": source,
                    "source_call_id": call["call_id"],
                    "wav_sha256": expected_hash,
                }
            )
    return specifications


def _expected_binding(
    plan: dict[str, Any],
    mapping: dict[str, str],
    specifications: list[dict[str, Any]],
    created_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": PACKAGE_BINDING_SCHEMA,
        "audition_id": plan["audition_id"],
        "created_at": created_at,
        "blind_mapping_sha256": _blind_mapping_sha256(mapping),
        "clips": [
            {
                "relative_path": spec["relative_path"],
                "source_call_id": spec["source_call_id"],
                "wav_sha256": spec["wav_sha256"],
            }
            for spec in specifications
        ],
    }


def _validate_binding(
    binding_path: Path,
    plan: dict[str, Any],
    mapping: dict[str, str],
    specifications: list[dict[str, Any]],
) -> None:
    if not binding_path.is_file():
        raise InputError("Private blind-package binding is missing")
    binding = read_json(binding_path)
    expected_fields = {
        "schema_version",
        "audition_id",
        "created_at",
        "blind_mapping_sha256",
        "clips",
    }
    if not isinstance(binding, dict) or set(binding) != expected_fields:
        raise InputError("Private blind-package binding has an invalid schema")
    if type(binding.get("schema_version")) is not int or binding["schema_version"] != PACKAGE_BINDING_SCHEMA:
        raise InputError("Private blind-package binding has an invalid schema_version")
    if binding.get("audition_id") != plan.get("audition_id"):
        raise InputError("Private blind-package binding has the wrong audition_id")
    created_at = binding.get("created_at")
    if not isinstance(created_at, str) or not created_at.strip():
        raise InputError("Private blind-package binding has no valid created_at")
    if not _is_sha256(binding.get("blind_mapping_sha256")):
        raise InputError("Private blind-package binding has an invalid mapping hash")
    clips = binding.get("clips")
    if not isinstance(clips, list):
        raise InputError("Private blind-package binding clips must be an array")
    for clip in clips:
        if (
            not isinstance(clip, dict)
            or set(clip) != {"relative_path", "source_call_id", "wav_sha256"}
            or not isinstance(clip.get("relative_path"), str)
            or not isinstance(clip.get("source_call_id"), str)
            or not _is_sha256(clip.get("wav_sha256"))
        ):
            raise InputError("Private blind-package binding contains a malformed clip")
    if binding != _expected_binding(plan, mapping, specifications, created_at):
        raise InputError("Private blind-package binding does not match the key and clips")


def _write_or_validate_binding(
    binding_path: Path,
    plan: dict[str, Any],
    mapping: dict[str, str],
    specifications: list[dict[str, Any]],
) -> None:
    if not binding_path.exists():
        atomic_write_json(binding_path, _expected_binding(plan, mapping, specifications, utc_now()))
    _validate_binding(binding_path, plan, mapping, specifications)


def _validate_published_package(
    package_root: Path,
    binding_path: Path,
    plan: dict[str, Any],
    mapping: dict[str, str],
    specifications: list[dict[str, Any]],
) -> None:
    if not package_root.is_dir():
        raise InputError(f"A partial blind package already exists: {package_root}")

    expected_files = {"scorecard.csv", "LISTENER-GUIDE.txt"}
    expected_files.update(spec["relative_path"] for spec in specifications)
    expected_directories: set[str] = set()
    for relative_value in expected_files:
        relative = Path(relative_value)
        expected_directories.update(
            parent.as_posix()
            for parent in relative.parents
            if parent.as_posix() != "."
        )

    actual_files: set[str] = set()
    actual_directories: set[str] = set()
    for entry in package_root.rglob("*"):
        relative = entry.relative_to(package_root).as_posix()
        if entry.is_symlink():
            raise InputError(f"Published blind package contains a symlink: {relative}")
        if entry.is_dir():
            actual_directories.add(relative)
        elif entry.is_file():
            actual_files.add(relative)
        else:
            raise InputError(f"Published blind package contains an unsupported entry: {relative}")
    if actual_files != expected_files or actual_directories != expected_directories:
        raise InputError("Published blind package tree is incomplete or contains unexpected entries")

    for spec in specifications:
        destination = resolve_inside(package_root, spec["relative_path"])
        if sha256_file(destination) != spec["wav_sha256"]:
            raise InputError(f"Published blind clip does not match its winning key: {spec['relative_path']}")
    _validate_binding(binding_path, plan, mapping, specifications)


def _validate_declared_package(
    workspace_root: Path,
    plan: dict[str, Any],
    config: AuditionConfig,
) -> None:
    package_root = resolve_inside(workspace_root, str(plan["package_path"]))
    expected_package_root = resolve_inside(config.package_root, str(plan["audition_id"]))
    if package_root != expected_package_root:
        raise InputError("Audition plan package evidence is not canonical")
    blind_key_path = resolve_inside(workspace_root, str(plan["blind_key_path"]))
    if not blind_key_path.is_file():
        raise InputError("Packaged audition is missing its private blind key")
    mapping = _strict_blind_mapping(plan, read_json(blind_key_path))
    specifications = _clip_specifications(workspace_root, plan, mapping)
    binding_path = resolve_inside(blind_key_path.parent, "package-binding.json")
    _validate_published_package(
        package_root,
        binding_path,
        plan,
        mapping,
        specifications,
    )


def _copy_validated_clip(source: Path, destination: Path, expected_sha256: str) -> None:
    content = read_bytes_nofollow(source)
    if sha256_bytes(content) != expected_sha256:
        raise InputError(f"Blind clip source changed after validation: {source}")
    atomic_write_bytes(destination, content)
    if sha256_file(destination) != expected_sha256:
        raise InputError(f"Copied blind clip failed hash verification: {destination}")


def package_blind_audition(
    workspace_root: Path,
    plan_path: Path,
    *,
    accept_verbatim_prefix: bool = False,
) -> Path:
    load_plan(workspace_root, plan_path)
    plan_path = _lexical_absolute(plan_path)
    with exclusive_file_lock(_audition_lock_path(plan_path)):
        plan, config = load_plan(workspace_root, plan_path)
        audition_id = plan.get("audition_id")
        if not isinstance(audition_id, str) or not AUDITION_ID.fullmatch(audition_id):
            raise InputError("Plan has an invalid audition_id")
        incomplete = [item["call_id"] for item in plan["calls"] if item.get("status") != "fidelity_pass"]
        if incomplete:
            raise InputError(f"Cannot package until every clip passes fidelity; incomplete={incomplete}")

        excerpt_by_id = {item["id"]: item for item in plan["excerpts"]}
        spoken_by_id = {
            excerpt_id: _current_excerpt_text(config, excerpt)
            for excerpt_id, excerpt in excerpt_by_id.items()
        }
        for call in plan["calls"]:
            _validate_call_artifacts(
                workspace_root,
                call,
                spoken_by_id[call["excerpt_id"]],
                config,
                accept_verbatim_prefix=accept_verbatim_prefix,
            )

        blind_key_path = resolve_inside(workspace_root, str(plan["blind_key_path"]))
        mapping = _load_or_create_blind_mapping(plan, blind_key_path)
        specifications = _clip_specifications(workspace_root, plan, mapping)
        binding_path = resolve_inside(blind_key_path.parent, "package-binding.json")
        package_root = resolve_inside(config.package_root, audition_id)
        _write_or_validate_binding(binding_path, plan, mapping, specifications)

        if package_root.exists():
            _validate_published_package(
                package_root,
                binding_path,
                plan,
                mapping,
                specifications,
            )
            plan["package_path"] = workspace_relative(workspace_root, package_root)
            _persist_plan(plan_path, plan)
            return package_root

        durable_mkdir(package_root.parent)
        staging = package_root.parent / f".{audition_id}.staging-{secrets.token_hex(6)}"
        try:
            for spec in specifications:
                destination = resolve_inside(staging, spec["relative_path"])
                _copy_validated_clip(spec["source"], destination, spec["wav_sha256"])

            score_buffer = io.StringIO(newline="")
            writer = csv.writer(score_buffer)
            writer.writerow(
                [
                    "blind_voice",
                    "excerpt",
                    "comfort_1_5",
                    "authority_1_5",
                    "restraint_1_5",
                    "cadence_1_5",
                    "dialogue_1_5",
                    "pronunciation_1_5",
                    "artifacts_1_5",
                    "notes",
                ]
            )
            excerpt_order = [item["id"] for item in plan["excerpts"]]
            for label in BLIND_LABELS:
                for excerpt_id in excerpt_order:
                    writer.writerow([f"Voice {label}", excerpt_id, "", "", "", "", "", "", "", ""])
            atomic_write_text(resolve_inside(staging, "scorecard.csv"), score_buffer.getvalue())

            guide = f"""THE FINAL FRONTIER — BLIND NOVA 2 SONIC VOICE AUDITION

Audition: {audition_id}
Voices: {len(mapping)} anonymous candidates
Excerpts per voice: {len(excerpt_order)}

Listen without opening the build directory or blind-key.json. Every included clip
already passed exact normalized word-sequence comparison against its current source.

Score each clip from 1 (poor) to 5 (excellent). Treat artifacts_1_5 as 5 when
artifact-free and 1 when severe. Suggested final weighting:
  comfort/fatigue 25%; authority 20%; emotional restraint 20%; cadence 15%;
  dialogue 10%; pronunciation 5%; artifact freedom 5%.

Use headphones and ordinary speakers, then repeat the ranking the following day.
After completing scorecard.csv, reveal the identities with:
  frontier-audiobook audition reveal --plan <plan.json> --confirm-scoring-complete

The winning short-form voice should still complete a longer stamina audition
before production rendering begins.
"""
            atomic_write_text(resolve_inside(staging, "LISTENER-GUIDE.txt"), guide)
            durable_replace(staging, package_root, source_kind="directory")
        except BaseException:
            # Keep an unpublished random staging tree for manual inspection. A
            # pathname-based recursive cleanup would reintroduce an ancestor
            # symlink race after descriptor-rooted publication failed.
            raise

        _validate_published_package(
            package_root,
            binding_path,
            plan,
            mapping,
            specifications,
        )
        plan["package_path"] = workspace_relative(workspace_root, package_root)
        _persist_plan(plan_path, plan)
        return package_root


def reveal_blind_key(workspace_root: Path, plan_path: Path) -> dict[str, str]:
    load_plan(workspace_root, plan_path)
    plan_path = _lexical_absolute(plan_path)
    with exclusive_file_lock(_audition_lock_path(plan_path)):
        plan, _ = load_plan(workspace_root, plan_path)
        key_path = resolve_inside(workspace_root, str(plan["blind_key_path"]))
        if not key_path.is_file():
            raise InputError("No valid blind key exists; package the complete audition first")
        mapping = _strict_blind_mapping(plan, read_json(key_path))
        return {f"Voice {label}": mapping[label] for label in BLIND_LABELS}


def plan_status(plan: dict[str, Any]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for call in plan["calls"]:
        status = str(call.get("status", "unknown"))
        counts[status] = counts.get(status, 0) + 1
    return {
        "audition_id": plan["audition_id"],
        "status": plan["status"],
        "model_id": plan["model_id"],
        "region": plan["region"],
        "voice_count": len(plan["voices"]),
        "excerpt_count": len(plan["excerpts"]),
        "call_counts": counts,
        "package_path": plan.get("package_path"),
    }
