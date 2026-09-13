"""Strict TOML configuration for the blind voice audition."""

from __future__ import annotations

import math
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .errors import InputError
from .util import read_bytes_nofollow, resolve_inside, sha256_bytes

MODEL_ID = "amazon.nova-2-sonic-v1:0"
REGION = "us-east-1"
NORMALIZATION_ID = "frontier-word-sequence-v1"
FEMININE_ENGLISH_VOICES = frozenset({"tiffany", "amy", "olivia", "kiara"})
EXPECTED_EXCERPT_SCOPE = (
    (
        "technical-authority",
        5,
        "Anything built to send information carries concessions to a receiver.",
        "My apparatus was the only thing in the arrangement behaving as a receiver.",
    ),
    (
        "consent-and-dialogue",
        73,
        "My conditions were four.",
        "That was the consent. Not my badge, not the three signatures, not the channel.",
    ),
    (
        "private-grief",
        118,
        "Forgetting has friction.",
        "What I cannot access in this head has no surviving copy elsewhere.",
    ),
    (
        "quiet-refusal",
        124,
        "The relay stood on the bench under the window, lit and on standby.",
        "It was not absolution and it was not repair.",
    ),
)
ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class NovaSettings:
    model_id: str
    region: str
    sample_rate_hz: int
    sample_size_bits: int
    channels: int
    max_tokens: int
    top_p: float
    temperature: float
    stream_timeout_seconds: int
    system_prompt: str


@dataclass(frozen=True)
class ExcerptSpec:
    id: str
    chapter: int
    start_anchor: str
    end_anchor: str
    purpose: str


@dataclass(frozen=True)
class AuditionConfig:
    path: Path
    sha256: str
    workspace_root: Path
    manuscript_root: Path
    output_root: Path
    package_root: Path
    voices: tuple[str, ...]
    nova: NovaSettings
    normalization: str
    excerpts: tuple[ExcerptSpec, ...]


def _mapping(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise InputError(f"{label} must be a TOML table")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], label: str) -> None:
    actual = set(value)
    if actual != expected:
        missing = sorted(expected - actual)
        unknown = sorted(actual - expected)
        raise InputError(f"{label} keys are invalid; missing={missing}, unknown={unknown}")


def _text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{label} must be a nonblank string")
    return value.strip()


def _integer(value: Any, label: str, minimum: int = 1) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise InputError(f"{label} must be an integer >= {minimum}")
    return value


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{label} must be numeric")
    result = float(value)
    if not math.isfinite(result):
        raise InputError(f"{label} must be finite")
    return result


def load_audition_config(path: Path, workspace_root: Path) -> AuditionConfig:
    raw = read_bytes_nofollow(path)
    try:
        parsed = tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise InputError(f"Malformed UTF-8 TOML in {path}: {exc}") from exc

    _exact_keys(
        parsed,
        {"schema_version", "manuscript_root", "output_root", "package_root", "voices", "nova", "verification", "excerpts"},
        "audition config",
    )
    if type(parsed["schema_version"]) is not int or parsed["schema_version"] != 1:
        raise InputError("audition config schema_version must be integer 1")

    voices_value = parsed["voices"]
    if not isinstance(voices_value, list):
        raise InputError("voices must be an array")
    voices = tuple(_text(item, "voices[]").lower() for item in voices_value)
    if len(voices) != len(set(voices)):
        raise InputError("voices contains duplicates")
    if len(voices) != 4 or set(voices) != FEMININE_ENGLISH_VOICES:
        raise InputError(
            "voices must contain exactly tiffany, amy, olivia, and kiara for the four-label blind audition"
        )

    nova_table = _mapping(parsed["nova"], "nova")
    _exact_keys(
        nova_table,
        {"model_id", "region", "sample_rate_hz", "sample_size_bits", "channels", "max_tokens", "top_p", "temperature", "stream_timeout_seconds", "system_prompt"},
        "nova",
    )
    model_id = _text(nova_table["model_id"], "nova.model_id")
    region = _text(nova_table["region"], "nova.region")
    temperature = _number(nova_table["temperature"], "nova.temperature")
    if model_id != MODEL_ID:
        raise InputError(f"nova.model_id must remain pinned to {MODEL_ID}")
    if region != REGION:
        raise InputError(f"nova.region must remain pinned to {REGION}")
    if temperature != 0.0:
        raise InputError("nova.temperature must be 0.0 for the fidelity audition")

    nova = NovaSettings(
        model_id=model_id,
        region=region,
        sample_rate_hz=_integer(nova_table["sample_rate_hz"], "nova.sample_rate_hz"),
        sample_size_bits=_integer(nova_table["sample_size_bits"], "nova.sample_size_bits"),
        channels=_integer(nova_table["channels"], "nova.channels"),
        max_tokens=_integer(nova_table["max_tokens"], "nova.max_tokens"),
        top_p=_number(nova_table["top_p"], "nova.top_p"),
        temperature=temperature,
        stream_timeout_seconds=_integer(nova_table["stream_timeout_seconds"], "nova.stream_timeout_seconds"),
        system_prompt=_text(nova_table["system_prompt"], "nova.system_prompt"),
    )
    if (nova.sample_rate_hz, nova.sample_size_bits, nova.channels) != (24000, 16, 1):
        raise InputError("Nova output must remain 24 kHz, signed 16-bit, mono LPCM")
    if not 0.0 <= nova.top_p <= 1.0:
        raise InputError("nova.top_p must be between 0 and 1")
    if nova.stream_timeout_seconds >= 480:
        raise InputError("nova.stream_timeout_seconds must leave time below the eight-minute connection limit")

    verification = _mapping(parsed["verification"], "verification")
    _exact_keys(verification, {"normalization"}, "verification")
    normalization = _text(verification["normalization"], "verification.normalization")
    if normalization != NORMALIZATION_ID:
        raise InputError(f"verification.normalization must be {NORMALIZATION_ID}")

    excerpt_values = parsed["excerpts"]
    if not isinstance(excerpt_values, list) or len(excerpt_values) != len(EXPECTED_EXCERPT_SCOPE):
        raise InputError("excerpts must contain exactly the four pinned audition selections")
    excerpts: list[ExcerptSpec] = []
    for index, item in enumerate(excerpt_values):
        table = _mapping(item, f"excerpts[{index}]")
        _exact_keys(table, {"id", "chapter", "start_anchor", "end_anchor", "purpose"}, f"excerpts[{index}]")
        excerpt_id = _text(table["id"], f"excerpts[{index}].id")
        if not ID_PATTERN.fullmatch(excerpt_id):
            raise InputError(f"Invalid excerpt ID: {excerpt_id!r}")
        excerpts.append(
            ExcerptSpec(
                id=excerpt_id,
                chapter=_integer(table["chapter"], f"excerpts[{index}].chapter"),
                start_anchor=_text(table["start_anchor"], f"excerpts[{index}].start_anchor"),
                end_anchor=_text(table["end_anchor"], f"excerpts[{index}].end_anchor"),
                purpose=_text(table["purpose"], f"excerpts[{index}].purpose"),
            )
        )
    scope = tuple((item.id, item.chapter, item.start_anchor, item.end_anchor) for item in excerpts)
    if scope != EXPECTED_EXCERPT_SCOPE:
        raise InputError(
            "excerpts must match the four pinned IDs, chapters, anchors, and ordering for this audition"
        )

    return AuditionConfig(
        path=path.resolve(),
        sha256=sha256_bytes(raw),
        workspace_root=workspace_root.resolve(),
        manuscript_root=resolve_inside(workspace_root, _text(parsed["manuscript_root"], "manuscript_root")),
        output_root=resolve_inside(workspace_root, _text(parsed["output_root"], "output_root")),
        package_root=resolve_inside(workspace_root, _text(parsed["package_root"], "package_root")),
        voices=voices,
        nova=nova,
        normalization=normalization,
        excerpts=tuple(excerpts),
    )
