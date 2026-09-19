"""Typed, prose-free records and strict canonical JSON codecs for production.

This module defines data contracts only.  State reduction, planning, authorization,
execution, validation algorithms, and delivery behavior live in later production
components.
"""

from __future__ import annotations

import json
import math
import re
from collections.abc import Mapping as MappingABC
from dataclasses import dataclass, fields, is_dataclass, replace
from datetime import datetime
from decimal import Decimal, InvalidOperation
from enum import Enum, StrEnum
from pathlib import Path, PurePosixPath
from types import MappingProxyType, UnionType
from typing import Any, ClassVar, Generic, Mapping, TypeAlias, TypeVar, Union, get_args, get_origin, get_type_hints

from .errors import InputError
from .util import atomic_write_bytes, json_loads_strict, read_bytes_nofollow, sha256_bytes

RECORD_SCHEMA_VERSION = 1
TOKEN_MODALITIES = ("input_speech", "input_text", "output_speech", "output_text")

_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_FIELD_NAME_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]*$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
_DECIMAL_PATTERN = re.compile(r"^(?:0|[1-9]\d*)(?:\.\d+)?$")

JsonPrimitive: TypeAlias = str | int | bool | None
T = TypeVar("T")


class TrackKind(StrEnum):
    """Supported independent audiobook track kinds."""

    OPENING_CREDITS = "opening_credits"
    FRONT_MATTER = "front_matter"
    CHAPTER = "chapter"
    CLOSING_CREDITS = "closing_credits"


class SourceKind(StrEnum):
    """Source adapter category recorded without source text."""

    CHAPTER = "chapter"
    APPROVED_SPECIAL_TRACK = "approved_special_track"


class FidelityPolicy(StrEnum):
    """Supported transcript fidelity policies."""

    EXACT = "exact"


class AuthorizationDecision(StrEnum):
    """Explicit operator response values for a paid authorization display."""

    AUTHORIZE_EXACT_SCOPE = "authorize-exact-paid-scope-once"
    DECLINE = "do-not-authorize"


class AudioEncoding(StrEnum):
    """Supported production audio encoding."""

    PCM_S16LE = "pcm_s16le"


class TransactionState(StrEnum):
    DISCOVERED = "discovered"
    PLANNED = "planned"
    PREFLIGHT_PASSED = "preflight-passed"
    AUTHORIZATION_REQUIRED = "authorization-required"
    RUNNING = "running"
    CHARGE_UNCERTAIN = "charge-uncertain"
    RENDERED = "rendered"
    VALIDATED = "validated"
    DELIVERED = "delivered"
    BLOCKED = "blocked"


class DestinationState(StrEnum):
    ABSENT = "absent"
    ALREADY_IDENTICAL = "already-identical"
    CONFLICTING = "conflicting"


class ValidationStatus(StrEnum):
    PASSED = "passed"
    BLOCKED = "blocked"
    NOT_RUN = "not-run"
    NOT_APPLICABLE = "not-applicable"


class DeliveryStatus(StrEnum):
    NOT_STARTED = "not-started"
    PUBLISHED = "published"
    ALREADY_IDENTICAL = "already-identical"
    CONFLICTING = "conflicting"
    BLOCKED = "blocked"


class BillingStatus(StrEnum):
    PENDING = "pending"
    NOT_PERFORMED = "not-performed"
    CONFIRMED = "confirmed"


class BatchStatus(StrEnum):
    NOT_STARTED = "not-started"
    RUNNING = "running"
    PARTIAL = "partial"
    BLOCKED = "blocked"
    COMPLETE = "complete"


def _require_schema_version(value: object, label: str) -> None:
    if type(value) is not int or value != RECORD_SCHEMA_VERSION:
        raise InputError(f"{label} schema_version must be integer {RECORD_SCHEMA_VERSION}")


def _require_bool(value: object, label: str) -> None:
    if type(value) is not bool:
        raise InputError(f"{label} must be a boolean")


def _require_int(value: object, label: str, *, minimum: int = 0) -> None:
    if type(value) is not int or value < minimum:
        raise InputError(f"{label} must be an integer >= {minimum}")


def _require_text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value:
        raise InputError(f"{label} must be a nonblank canonical string")
    return value


def _require_identifier(value: object, label: str) -> str:
    text = _require_text(value, label)
    if not _ID_PATTERN.fullmatch(text):
        raise InputError(f"{label} must be a lowercase hyphenated identifier")
    return text


def _require_field_name(value: object, label: str) -> str:
    text = _require_text(value, label)
    if not _FIELD_NAME_PATTERN.fullmatch(text):
        raise InputError(f"{label} must be a canonical field identifier")
    return text


def _require_sha256(value: object, label: str, *, allow_unsealed: bool = False) -> str:
    if allow_unsealed and value == "":
        return ""
    if not isinstance(value, str) or not _SHA256_PATTERN.fullmatch(value):
        raise InputError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_optional_sha256(value: object, label: str) -> None:
    if value is not None:
        _require_sha256(value, label)


def _require_utc(value: object, label: str) -> str:
    text = _require_text(value, label)
    if not _UTC_PATTERN.fullmatch(text):
        raise InputError(f"{label} must be an ISO-8601 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(text.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise InputError(f"{label} is not a valid UTC timestamp") from exc
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise InputError(f"{label} must be UTC")
    return text


def _require_decimal(value: object, label: str) -> Decimal:
    text = _require_text(value, label)
    if not _DECIMAL_PATTERN.fullmatch(text):
        raise InputError(f"{label} must be a nonnegative plain decimal string")
    try:
        parsed = Decimal(text)
    except InvalidOperation as exc:  # pragma: no cover - guarded by the pattern
        raise InputError(f"{label} must be a valid decimal string") from exc
    if not parsed.is_finite() or parsed < 0:
        raise InputError(f"{label} must be finite and nonnegative")
    return parsed


def _require_relative_path(value: object, label: str) -> str:
    text = _require_text(value, label)
    if "\\" in text:
        raise InputError(f"{label} must use workspace-relative POSIX separators")
    candidate = PurePosixPath(text)
    if candidate.is_absolute() or text == "." or any(part in {"", ".", ".."} for part in candidate.parts):
        raise InputError(f"{label} must be a traversal-free relative path")
    if candidate.as_posix() != text:
        raise InputError(f"{label} must be a canonical relative path")
    return text


def _require_enum(value: object, expected: type[Enum], label: str) -> None:
    if not isinstance(value, expected):
        raise InputError(f"{label} must be a {expected.__name__} value")


def _freeze_text_mapping(value: Mapping[str, str], label: str) -> Mapping[str, str]:
    if not isinstance(value, MappingABC):
        raise InputError(f"{label} must be a mapping")
    result: dict[str, str] = {}
    for key, item in value.items():
        checked_key = _require_field_name(key, f"{label} key")
        result[checked_key] = _require_text(item, f"{label}[{checked_key!r}]")
    return MappingProxyType(result)


def _freeze_int_mapping(value: Mapping[str, int], label: str) -> Mapping[str, int]:
    if not isinstance(value, MappingABC):
        raise InputError(f"{label} must be a mapping")
    result: dict[str, int] = {}
    for key, item in value.items():
        checked_key = _require_identifier(key, f"{label} key")
        _require_int(item, f"{label}[{checked_key!r}]")
        result[checked_key] = item
    return MappingProxyType(result)


def _freeze_primitive_mapping(
    value: Mapping[str, JsonPrimitive], label: str
) -> Mapping[str, JsonPrimitive]:
    if not isinstance(value, MappingABC):
        raise InputError(f"{label} must be a mapping")
    result: dict[str, JsonPrimitive] = {}
    for key, item in value.items():
        checked_key = _require_field_name(key, f"{label} key")
        if item is not None and type(item) not in {str, int, bool}:
            raise InputError(f"{label}[{checked_key!r}] must be a JSON scalar")
        if isinstance(item, str):
            _require_text(item, f"{label}[{checked_key!r}]")
        result[checked_key] = item
    return MappingProxyType(result)


@dataclass(frozen=True, slots=True)
class AudioFormat:
    sample_rate_hz: int
    sample_size_bits: int
    channels: int
    encoding: AudioEncoding

    def __post_init__(self) -> None:
        _require_int(self.sample_rate_hz, "audio.sample_rate_hz", minimum=1)
        _require_int(self.sample_size_bits, "audio.sample_size_bits", minimum=1)
        _require_int(self.channels, "audio.channels", minimum=1)
        _require_enum(self.encoding, AudioEncoding, "audio.encoding")


@dataclass(frozen=True, slots=True)
class EffectiveTrackConfig:
    track_id: str
    track_kind: TrackKind
    sequence: int
    voice: str
    model_id: str
    region: str
    profile_label: str
    target_segment_words: int
    fidelity_policy: FidelityPolicy
    normalization: str
    audio_format: AudioFormat
    output_path: str
    resolution_provenance: Mapping[str, str]

    def __post_init__(self) -> None:
        _require_identifier(self.track_id, "effective config track_id")
        _require_enum(self.track_kind, TrackKind, "effective config track_kind")
        _require_int(self.sequence, "effective config sequence", minimum=1)
        for field_name in ("voice", "model_id", "region", "profile_label", "normalization"):
            _require_text(getattr(self, field_name), f"effective config {field_name}")
        _require_int(self.target_segment_words, "effective config target_segment_words", minimum=1)
        _require_enum(self.fidelity_policy, FidelityPolicy, "effective config fidelity_policy")
        if not isinstance(self.audio_format, AudioFormat):
            raise InputError("effective config audio_format must be an AudioFormat")
        _require_relative_path(self.output_path, "effective config output_path")
        provenance = _freeze_text_mapping(self.resolution_provenance, "effective config resolution_provenance")
        if not provenance:
            raise InputError("effective config resolution_provenance must not be empty")
        object.__setattr__(self, "resolution_provenance", provenance)


@dataclass(frozen=True, slots=True)
class SegmentSnapshot:
    """Prose-free positional metadata and reusable render identity for one segment."""

    segment_id: str
    ordinal: int
    paragraph_index: int
    start_token_index: int
    end_token_index: int
    text_sha256: str
    normalized_tokens_sha256: str
    context_before_sha256: str | None
    context_after_sha256: str | None
    render_config_sha256: str
    render_identity_sha256: str
    spoken_token_count: int
    narration_only_punctuation: bool

    def __post_init__(self) -> None:
        _require_identifier(self.segment_id, "segment snapshot segment_id")
        _require_int(self.ordinal, "segment snapshot ordinal", minimum=1)
        _require_int(self.paragraph_index, "segment snapshot paragraph_index")
        _require_int(self.start_token_index, "segment snapshot start_token_index")
        _require_int(self.end_token_index, "segment snapshot end_token_index", minimum=1)
        _require_int(self.spoken_token_count, "segment snapshot spoken_token_count", minimum=1)
        if self.end_token_index <= self.start_token_index:
            raise InputError("segment snapshot token boundary must be nonempty")
        if self.end_token_index - self.start_token_index != self.spoken_token_count:
            raise InputError("segment snapshot token boundary must match spoken_token_count")
        for field_name in (
            "text_sha256",
            "normalized_tokens_sha256",
            "render_config_sha256",
            "render_identity_sha256",
        ):
            _require_sha256(getattr(self, field_name), f"segment snapshot {field_name}")
        _require_optional_sha256(
            self.context_before_sha256, "segment snapshot context_before_sha256"
        )
        _require_optional_sha256(
            self.context_after_sha256, "segment snapshot context_after_sha256"
        )
        _require_bool(self.narration_only_punctuation, "segment snapshot narration_only_punctuation")


@dataclass(frozen=True, slots=True)
class SourceSnapshot:
    track_id: str
    source_path: str
    source_section: str | None
    source_kind: SourceKind
    raw_sha256: str
    normalized_body_sha256: str
    spoken_sha256: str
    declared_word_count: int | None
    normalized_word_count: int
    spoken_token_count: int
    segment_count: int
    segmentation_policy: str
    render_identity_schema: str
    render_context_radius: int
    segments: tuple[SegmentSnapshot, ...]

    def __post_init__(self) -> None:
        _require_identifier(self.track_id, "source snapshot track_id")
        _require_relative_path(self.source_path, "source snapshot source_path")
        if self.source_section is not None:
            _require_text(self.source_section, "source snapshot source_section")
        _require_enum(self.source_kind, SourceKind, "source snapshot source_kind")
        for field_name in ("raw_sha256", "normalized_body_sha256", "spoken_sha256"):
            _require_sha256(getattr(self, field_name), f"source snapshot {field_name}")
        if self.declared_word_count is not None:
            _require_int(self.declared_word_count, "source snapshot declared_word_count")
        _require_int(self.normalized_word_count, "source snapshot normalized_word_count")
        _require_int(self.spoken_token_count, "source snapshot spoken_token_count", minimum=1)
        _require_int(self.segment_count, "source snapshot segment_count", minimum=1)
        _require_text(self.segmentation_policy, "source snapshot segmentation_policy")
        _require_text(self.render_identity_schema, "source snapshot render_identity_schema")
        _require_int(self.render_context_radius, "source snapshot render_context_radius")
        if not isinstance(self.segments, tuple) or not all(isinstance(item, SegmentSnapshot) for item in self.segments):
            raise InputError("source snapshot segments must be a tuple of SegmentSnapshot records")
        if self.segment_count != len(self.segments):
            raise InputError("source snapshot segment_count must equal the number of segments")
        if tuple(item.ordinal for item in self.segments) != tuple(range(1, self.segment_count + 1)):
            raise InputError("source snapshot segment ordinals must be contiguous from 1")
        if len({item.segment_id for item in self.segments}) != self.segment_count:
            raise InputError("source snapshot segment IDs must be unique")
        if sum(item.spoken_token_count for item in self.segments) != self.spoken_token_count:
            raise InputError("source snapshot segment token counts must equal spoken_token_count")
        expected_start = 0
        for item in self.segments:
            if item.start_token_index != expected_start:
                raise InputError("source snapshot segment token boundaries must be contiguous")
            expected_start = item.end_token_index
        if expected_start != self.spoken_token_count:
            raise InputError("source snapshot segment boundaries must cover every spoken token")
        if len({item.render_config_sha256 for item in self.segments}) != 1:
            raise InputError("source snapshot segments must share one render configuration digest")
        if self.render_context_radius == 0:
            if any(
                item.context_before_sha256 is not None or item.context_after_sha256 is not None
                for item in self.segments
            ):
                raise InputError("zero-radius render context must not contain context digests")
        else:
            for index, item in enumerate(self.segments):
                if (item.context_before_sha256 is None) != (index == 0):
                    raise InputError("segment before-context must be present exactly off the first boundary")
                if (item.context_after_sha256 is None) != (index == self.segment_count - 1):
                    raise InputError("segment after-context must be present exactly off the last boundary")


@dataclass(frozen=True, slots=True)
class FrozenTrackPlan:
    transaction_id: str
    track_id: str
    sequence: int
    effective_config: EffectiveTrackConfig
    source: SourceSnapshot
    command_argv: tuple[str, ...]
    command_sha256: str
    maximum_new_calls: int
    legacy_candidates: tuple[str, ...]
    protected_inventory_sha256: str

    def __post_init__(self) -> None:
        _require_identifier(self.transaction_id, "track plan transaction_id")
        _require_identifier(self.track_id, "track plan track_id")
        _require_int(self.sequence, "track plan sequence", minimum=1)
        if not isinstance(self.effective_config, EffectiveTrackConfig):
            raise InputError("track plan effective_config must be an EffectiveTrackConfig")
        if not isinstance(self.source, SourceSnapshot):
            raise InputError("track plan source must be a SourceSnapshot")
        if self.track_id != self.effective_config.track_id or self.track_id != self.source.track_id:
            raise InputError("track plan track_id must match effective config and source snapshot")
        if self.sequence != self.effective_config.sequence:
            raise InputError("track plan sequence must match effective config")
        if not isinstance(self.command_argv, tuple) or not self.command_argv:
            raise InputError("track plan command_argv must be a nonempty tuple")
        for index, argument in enumerate(self.command_argv):
            _require_text(argument, f"track plan command_argv[{index}]")
        _require_sha256(self.command_sha256, "track plan command_sha256")
        _require_int(self.maximum_new_calls, "track plan maximum_new_calls")
        if not isinstance(self.legacy_candidates, tuple):
            raise InputError("track plan legacy_candidates must be a tuple")
        for index, path in enumerate(self.legacy_candidates):
            _require_relative_path(path, f"track plan legacy_candidates[{index}]")
        if len(set(self.legacy_candidates)) != len(self.legacy_candidates):
            raise InputError("track plan legacy_candidates must be unique")
        _require_sha256(self.protected_inventory_sha256, "track plan protected_inventory_sha256")


@dataclass(frozen=True, slots=True)
class FrozenBatchPlan:
    schema_version: int
    plan_id: str
    created_at_utc: str
    book_id: str
    config_path: str
    config_sha256: str
    selectors: tuple[str, ...]
    tracks: tuple[FrozenTrackPlan, ...]
    canonical_sha256: str

    SCHEMA_VERSION: ClassVar[int] = RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_schema_version(self.schema_version, "frozen plan")
        _require_identifier(self.plan_id, "frozen plan plan_id")
        _require_utc(self.created_at_utc, "frozen plan created_at_utc")
        _require_identifier(self.book_id, "frozen plan book_id")
        _require_relative_path(self.config_path, "frozen plan config_path")
        _require_sha256(self.config_sha256, "frozen plan config_sha256")
        if not isinstance(self.selectors, tuple) or not self.selectors:
            raise InputError("frozen plan selectors must be a nonempty tuple")
        for index, selector in enumerate(self.selectors):
            _require_text(selector, f"frozen plan selectors[{index}]")
        if len(set(self.selectors)) != len(self.selectors):
            raise InputError("frozen plan selectors must be unique")
        if not isinstance(self.tracks, tuple) or not self.tracks:
            raise InputError("frozen plan tracks must be a nonempty tuple")
        if not all(isinstance(item, FrozenTrackPlan) for item in self.tracks):
            raise InputError("frozen plan tracks must contain FrozenTrackPlan records")
        if len({item.track_id for item in self.tracks}) != len(self.tracks):
            raise InputError("frozen plan track IDs must be unique")
        if len({item.transaction_id for item in self.tracks}) != len(self.tracks):
            raise InputError("frozen plan transaction IDs must be unique")
        if tuple(item.sequence for item in self.tracks) != tuple(sorted(item.sequence for item in self.tracks)):
            raise InputError("frozen plan tracks must be in catalog sequence order")
        _require_sha256(self.canonical_sha256, "frozen plan canonical_sha256", allow_unsealed=True)


@dataclass(frozen=True, slots=True)
class PreflightRecord:
    schema_version: int
    plan_sha256: str
    checked_at_utc: str
    expires_at_utc: str
    targeted_checks_sha256: str
    identity_profile_label: str
    identity_resolved: bool
    identity_checked_at_utc: str
    official_rates: Mapping[str, str]
    official_rate_provenance: Mapping[str, str]
    reusable_segment_ids: Mapping[str, tuple[str, ...]]
    maximum_new_calls_by_track: Mapping[str, int]
    maximum_new_calls_total: int
    estimated_pre_tax_usd: str
    estimate_inputs: Mapping[str, JsonPrimitive]
    delivery_collisions: Mapping[str, DestinationState]
    per_file_inventory_sha256: str
    canonical_sha256: str

    SCHEMA_VERSION: ClassVar[int] = RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_schema_version(self.schema_version, "preflight")
        for field_name in ("plan_sha256", "targeted_checks_sha256", "per_file_inventory_sha256"):
            _require_sha256(getattr(self, field_name), f"preflight {field_name}")
        checked = _require_utc(self.checked_at_utc, "preflight checked_at_utc")
        expires = _require_utc(self.expires_at_utc, "preflight expires_at_utc")
        if datetime.fromisoformat(expires.replace("Z", "+00:00")) <= datetime.fromisoformat(
            checked.replace("Z", "+00:00")
        ):
            raise InputError("preflight expires_at_utc must be after checked_at_utc")
        _require_text(self.identity_profile_label, "preflight identity_profile_label")
        _require_bool(self.identity_resolved, "preflight identity_resolved")
        _require_utc(self.identity_checked_at_utc, "preflight identity_checked_at_utc")
        rates = _freeze_text_mapping(self.official_rates, "preflight official_rates")
        if set(rates) != set(TOKEN_MODALITIES):
            raise InputError(f"preflight official_rates must contain exactly {list(TOKEN_MODALITIES)}")
        for modality, rate in rates.items():
            _require_decimal(rate, f"preflight official_rates[{modality!r}]")
        object.__setattr__(self, "official_rates", rates)
        provenance = _freeze_text_mapping(
            self.official_rate_provenance, "preflight official_rate_provenance"
        )
        if not provenance:
            raise InputError("preflight official_rate_provenance must not be empty")
        object.__setattr__(self, "official_rate_provenance", provenance)
        if not isinstance(self.reusable_segment_ids, MappingABC):
            raise InputError("preflight reusable_segment_ids must be a mapping")
        reusable: dict[str, tuple[str, ...]] = {}
        for track_id, segment_ids in self.reusable_segment_ids.items():
            checked_track = _require_identifier(track_id, "preflight reusable_segment_ids key")
            if not isinstance(segment_ids, tuple):
                raise InputError(f"preflight reusable segments for {checked_track} must be a tuple")
            for segment_id in segment_ids:
                _require_identifier(segment_id, f"preflight reusable segment for {checked_track}")
            if len(set(segment_ids)) != len(segment_ids):
                raise InputError(f"preflight reusable segments for {checked_track} must be unique")
            reusable[checked_track] = segment_ids
        object.__setattr__(self, "reusable_segment_ids", MappingProxyType(reusable))
        calls = _freeze_int_mapping(
            self.maximum_new_calls_by_track, "preflight maximum_new_calls_by_track"
        )
        object.__setattr__(self, "maximum_new_calls_by_track", calls)
        _require_int(self.maximum_new_calls_total, "preflight maximum_new_calls_total")
        if self.maximum_new_calls_total != sum(calls.values()):
            raise InputError("preflight maximum_new_calls_total must equal per-track call bounds")
        if set(reusable) != set(calls):
            raise InputError("preflight reusable and call-bound track scopes must match")
        _require_decimal(self.estimated_pre_tax_usd, "preflight estimated_pre_tax_usd")
        inputs = _freeze_primitive_mapping(self.estimate_inputs, "preflight estimate_inputs")
        if not inputs:
            raise InputError("preflight estimate_inputs must not be empty")
        object.__setattr__(self, "estimate_inputs", inputs)
        if not isinstance(self.delivery_collisions, MappingABC):
            raise InputError("preflight delivery_collisions must be a mapping")
        collisions: dict[str, DestinationState] = {}
        for track_id, state in self.delivery_collisions.items():
            checked_track = _require_identifier(track_id, "preflight delivery_collisions key")
            _require_enum(state, DestinationState, f"preflight delivery state for {checked_track}")
            collisions[checked_track] = state
        if set(collisions) != set(calls):
            raise InputError("preflight delivery and call-bound track scopes must match")
        object.__setattr__(self, "delivery_collisions", MappingProxyType(collisions))
        _require_sha256(self.canonical_sha256, "preflight canonical_sha256", allow_unsealed=True)


@dataclass(frozen=True, slots=True)
class PaidAuthorization:
    schema_version: int
    authorization_id: str
    plan_sha256: str
    preflight_sha256: str
    local_preflight_sha256: str
    estimate_sha256: str
    official_rate_provenance_sha256: str
    exact_transaction_ids: tuple[str, ...]
    exact_track_ids: tuple[str, ...]
    exact_command_sha256s: tuple[str, ...]
    maximum_new_calls_by_track: Mapping[str, int]
    maximum_new_calls_total: int
    estimated_pre_tax_usd: str
    operator_approved_max_estimated_pre_tax_usd: str
    issued_at_utc: str
    expires_at_utc: str
    one_shot: bool
    confirmation_challenge: str
    confirmation_display_sha256: str
    confirmation_decision: AuthorizationDecision
    confirmed_at_utc: str
    confirmation_sha256: str
    canonical_sha256: str

    SCHEMA_VERSION: ClassVar[int] = RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_schema_version(self.schema_version, "paid authorization")
        _require_identifier(self.authorization_id, "paid authorization authorization_id")
        for field_name in (
            "plan_sha256",
            "preflight_sha256",
            "local_preflight_sha256",
            "estimate_sha256",
            "official_rate_provenance_sha256",
        ):
            _require_sha256(getattr(self, field_name), f"paid authorization {field_name}")
        scopes = (
            (self.exact_transaction_ids, "exact_transaction_ids", _require_identifier),
            (self.exact_track_ids, "exact_track_ids", _require_identifier),
            (self.exact_command_sha256s, "exact_command_sha256s", _require_sha256),
        )
        for values, field_name, validator in scopes:
            if not isinstance(values, tuple) or not values:
                raise InputError(f"paid authorization {field_name} must be a nonempty tuple")
            for index, value in enumerate(values):
                validator(value, f"paid authorization {field_name}[{index}]")
            if len(set(values)) != len(values):
                raise InputError(f"paid authorization {field_name} must contain unique values")
        if not (
            len(self.exact_transaction_ids)
            == len(self.exact_track_ids)
            == len(self.exact_command_sha256s)
        ):
            raise InputError("paid authorization exact scope lists must have equal lengths")
        calls = _freeze_int_mapping(
            self.maximum_new_calls_by_track, "paid authorization maximum_new_calls_by_track"
        )
        if set(calls) != set(self.exact_track_ids):
            raise InputError("paid authorization call-bound keys must match exact_track_ids")
        object.__setattr__(self, "maximum_new_calls_by_track", calls)
        _require_int(self.maximum_new_calls_total, "paid authorization maximum_new_calls_total")
        if self.maximum_new_calls_total != sum(calls.values()):
            raise InputError("paid authorization total call bound must equal per-track bounds")
        estimate = _require_decimal(self.estimated_pre_tax_usd, "paid authorization estimated_pre_tax_usd")
        approved = _require_decimal(
            self.operator_approved_max_estimated_pre_tax_usd,
            "paid authorization operator_approved_max_estimated_pre_tax_usd",
        )
        if approved < estimate:
            raise InputError("paid authorization approved maximum must cover the estimate")
        issued = _require_utc(self.issued_at_utc, "paid authorization issued_at_utc")
        expires = _require_utc(self.expires_at_utc, "paid authorization expires_at_utc")
        confirmed = _require_utc(self.confirmed_at_utc, "paid authorization confirmed_at_utc")
        issued_time = datetime.fromisoformat(issued.replace("Z", "+00:00"))
        expires_time = datetime.fromisoformat(expires.replace("Z", "+00:00"))
        confirmed_time = datetime.fromisoformat(confirmed.replace("Z", "+00:00"))
        if expires_time <= issued_time:
            raise InputError("paid authorization expires_at_utc must be after issued_at_utc")
        if confirmed_time < issued_time or confirmed_time >= expires_time:
            raise InputError("paid authorization confirmation must occur inside its validity window")
        _require_bool(self.one_shot, "paid authorization one_shot")
        if not self.one_shot:
            raise InputError("paid authorization one_shot must be true")
        _require_sha256(self.confirmation_challenge, "paid authorization confirmation_challenge")
        _require_sha256(
            self.confirmation_display_sha256,
            "paid authorization confirmation_display_sha256",
        )
        _require_enum(
            self.confirmation_decision,
            AuthorizationDecision,
            "paid authorization confirmation_decision",
        )
        if self.confirmation_decision is not AuthorizationDecision.AUTHORIZE_EXACT_SCOPE:
            raise InputError("paid authorization confirmation decision must authorize exact scope")
        _require_sha256(self.confirmation_sha256, "paid authorization confirmation_sha256")
        expected_confirmation = authorization_confirmation_sha256(
            display_sha256=self.confirmation_display_sha256,
            challenge=self.confirmation_challenge,
            decision=self.confirmation_decision,
            confirmed_at_utc=self.confirmed_at_utc,
        )
        if self.confirmation_sha256 != expected_confirmation:
            raise InputError("paid authorization confirmation_sha256 does not match confirmation evidence")
        _require_sha256(
            self.canonical_sha256, "paid authorization canonical_sha256", allow_unsealed=True
        )


@dataclass(frozen=True, slots=True)
class LedgerEvent:
    schema_version: int
    transaction_id: str
    sequence: int
    event_type: str
    state_before: TransactionState | None
    state_after: TransactionState
    occurred_at_utc: str
    payload_sha256: str
    previous_event_sha256: str | None
    event_sha256: str

    SCHEMA_VERSION: ClassVar[int] = RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_schema_version(self.schema_version, "ledger event")
        _require_identifier(self.transaction_id, "ledger event transaction_id")
        _require_int(self.sequence, "ledger event sequence", minimum=1)
        _require_identifier(self.event_type, "ledger event event_type")
        if self.state_before is not None:
            _require_enum(self.state_before, TransactionState, "ledger event state_before")
        _require_enum(self.state_after, TransactionState, "ledger event state_after")
        _require_utc(self.occurred_at_utc, "ledger event occurred_at_utc")
        _require_sha256(self.payload_sha256, "ledger event payload_sha256")
        _require_optional_sha256(self.previous_event_sha256, "ledger event previous_event_sha256")
        if self.sequence == 1 and self.previous_event_sha256 is not None:
            raise InputError("first ledger event must not have a previous event digest")
        if self.sequence > 1 and self.previous_event_sha256 is None:
            raise InputError("later ledger events must bind the previous event digest")
        _require_sha256(self.event_sha256, "ledger event event_sha256", allow_unsealed=True)


@dataclass(frozen=True, slots=True)
class AttemptResult:
    schema_version: int
    attempt_id: str
    transaction_id: str
    authorization_sha256: str
    working_directory: str
    argv: tuple[str, ...]
    command_sha256: str
    profile_label: str
    started_at_utc: str
    ended_at_utc: str
    child_launched: bool
    native_return_code: int
    termination_signal: int | None
    console_path: str
    console_sha256: str
    automatic_retry_performed: bool
    environment_persisted: bool

    SCHEMA_VERSION: ClassVar[int] = RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_schema_version(self.schema_version, "attempt result")
        _require_identifier(self.attempt_id, "attempt result attempt_id")
        _require_identifier(self.transaction_id, "attempt result transaction_id")
        _require_sha256(self.authorization_sha256, "attempt result authorization_sha256")
        if self.working_directory != ".":
            _require_relative_path(self.working_directory, "attempt result working_directory")
        if not isinstance(self.argv, tuple) or not self.argv:
            raise InputError("attempt result argv must be a nonempty tuple")
        for index, argument in enumerate(self.argv):
            _require_text(argument, f"attempt result argv[{index}]")
        _require_sha256(self.command_sha256, "attempt result command_sha256")
        _require_text(self.profile_label, "attempt result profile_label")
        started = _require_utc(self.started_at_utc, "attempt result started_at_utc")
        ended = _require_utc(self.ended_at_utc, "attempt result ended_at_utc")
        if datetime.fromisoformat(ended.replace("Z", "+00:00")) < datetime.fromisoformat(
            started.replace("Z", "+00:00")
        ):
            raise InputError("attempt result ended_at_utc must not precede started_at_utc")
        _require_bool(self.child_launched, "attempt result child_launched")
        if not self.child_launched:
            raise InputError("a committed attempt result must record child_launched=true")
        if type(self.native_return_code) is not int:
            raise InputError("attempt result native_return_code must be an integer")
        if self.termination_signal is not None:
            _require_int(self.termination_signal, "attempt result termination_signal", minimum=1)
        _require_relative_path(self.console_path, "attempt result console_path")
        _require_sha256(self.console_sha256, "attempt result console_sha256")
        _require_bool(self.automatic_retry_performed, "attempt result automatic_retry_performed")
        _require_bool(self.environment_persisted, "attempt result environment_persisted")
        if self.automatic_retry_performed:
            raise InputError("attempt result automatic_retry_performed must be false")
        if self.environment_persisted:
            raise InputError("attempt result environment_persisted must be false")


@dataclass(frozen=True, slots=True)
class ValidationCheck:
    check_id: str
    status: ValidationStatus
    artifact_path: str | None
    artifact_sha256: str | None
    finding_category: str | None
    finding_count: int

    def __post_init__(self) -> None:
        _require_field_name(self.check_id, "validation check check_id")
        _require_enum(self.status, ValidationStatus, "validation check status")
        if self.artifact_path is not None:
            _require_relative_path(self.artifact_path, "validation check artifact_path")
        _require_optional_sha256(self.artifact_sha256, "validation check artifact_sha256")
        if (self.artifact_path is None) != (self.artifact_sha256 is None):
            raise InputError("validation check artifact path and digest must appear together")
        if self.finding_category is not None:
            _require_field_name(self.finding_category, "validation check finding_category")
        _require_int(self.finding_count, "validation check finding_count")


@dataclass(frozen=True, slots=True)
class ValidationEvidence:
    schema_version: int
    transaction_id: str
    track_id: str
    validated_at_utc: str
    plan_sha256: str
    attempt_sha256: str
    manifest_sha256: str
    status: ValidationStatus
    checks: tuple[ValidationCheck, ...]
    delivery_gate_passed: bool
    canonical_sha256: str

    SCHEMA_VERSION: ClassVar[int] = RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_schema_version(self.schema_version, "validation evidence")
        _require_identifier(self.transaction_id, "validation evidence transaction_id")
        _require_identifier(self.track_id, "validation evidence track_id")
        _require_utc(self.validated_at_utc, "validation evidence validated_at_utc")
        for field_name in ("plan_sha256", "attempt_sha256", "manifest_sha256"):
            _require_sha256(getattr(self, field_name), f"validation evidence {field_name}")
        _require_enum(self.status, ValidationStatus, "validation evidence status")
        if not isinstance(self.checks, tuple) or not self.checks:
            raise InputError("validation evidence checks must be a nonempty tuple")
        if not all(isinstance(item, ValidationCheck) for item in self.checks):
            raise InputError("validation evidence checks must contain ValidationCheck records")
        if len({item.check_id for item in self.checks}) != len(self.checks):
            raise InputError("validation evidence check IDs must be unique")
        _require_bool(self.delivery_gate_passed, "validation evidence delivery_gate_passed")
        if self.delivery_gate_passed and (
            self.status is not ValidationStatus.PASSED
            or any(item.status is not ValidationStatus.PASSED for item in self.checks)
        ):
            raise InputError("delivery_gate_passed requires all validation checks to pass")
        _require_sha256(
            self.canonical_sha256, "validation evidence canonical_sha256", allow_unsealed=True
        )


@dataclass(frozen=True, slots=True)
class UsageTotals:
    input_speech: int
    input_text: int
    output_speech: int
    output_text: int

    def __post_init__(self) -> None:
        for field_name in TOKEN_MODALITIES:
            _require_int(getattr(self, field_name), f"usage totals {field_name}")


@dataclass(frozen=True, slots=True)
class TrackReport:
    schema_version: int
    transaction_id: str
    track_id: str
    generated_at_utc: str
    state: TransactionState
    source_sha256: str
    config_sha256: str
    plan_sha256: str
    preflight_sha256: str
    authorization_sha256: str
    attempt_sha256: str
    validation_sha256: str
    native_return_code: int
    active_artifact_totals: UsageTotals
    current_execution_totals: UsageTotals
    estimated_pre_tax_usd: str
    active_artifact_cost_usd: str
    current_execution_cost_usd: str
    billing_status: BillingStatus
    billing_amount_usd: str | None
    billing_confirmed_at_utc: str | None
    delivery_status: DeliveryStatus
    isolation_status: ValidationStatus
    targeted_checks_sha256: str
    broader_suite_status: ValidationStatus
    supplemental_listening_sha256: str | None
    canonical_sha256: str

    SCHEMA_VERSION: ClassVar[int] = RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_schema_version(self.schema_version, "track report")
        _require_identifier(self.transaction_id, "track report transaction_id")
        _require_identifier(self.track_id, "track report track_id")
        _require_utc(self.generated_at_utc, "track report generated_at_utc")
        _require_enum(self.state, TransactionState, "track report state")
        for field_name in (
            "source_sha256",
            "config_sha256",
            "plan_sha256",
            "preflight_sha256",
            "authorization_sha256",
            "attempt_sha256",
            "validation_sha256",
            "targeted_checks_sha256",
        ):
            _require_sha256(getattr(self, field_name), f"track report {field_name}")
        if type(self.native_return_code) is not int:
            raise InputError("track report native_return_code must be an integer")
        if not isinstance(self.active_artifact_totals, UsageTotals) or not isinstance(
            self.current_execution_totals, UsageTotals
        ):
            raise InputError("track report usage totals must be UsageTotals records")
        for field_name in (
            "estimated_pre_tax_usd",
            "active_artifact_cost_usd",
            "current_execution_cost_usd",
        ):
            _require_decimal(getattr(self, field_name), f"track report {field_name}")
        _require_enum(self.billing_status, BillingStatus, "track report billing_status")
        if self.billing_amount_usd is not None:
            _require_decimal(self.billing_amount_usd, "track report billing_amount_usd")
        if self.billing_confirmed_at_utc is not None:
            _require_utc(self.billing_confirmed_at_utc, "track report billing_confirmed_at_utc")
        if self.billing_status is BillingStatus.CONFIRMED:
            if self.billing_amount_usd is None or self.billing_confirmed_at_utc is None:
                raise InputError("confirmed billing requires amount and confirmation timestamp")
        elif self.billing_amount_usd is not None or self.billing_confirmed_at_utc is not None:
            raise InputError("unconfirmed billing must not include amount or confirmation timestamp")
        _require_enum(self.delivery_status, DeliveryStatus, "track report delivery_status")
        _require_enum(self.isolation_status, ValidationStatus, "track report isolation_status")
        _require_enum(
            self.broader_suite_status, ValidationStatus, "track report broader_suite_status"
        )
        _require_optional_sha256(
            self.supplemental_listening_sha256, "track report supplemental_listening_sha256"
        )
        _require_sha256(self.canonical_sha256, "track report canonical_sha256", allow_unsealed=True)


@dataclass(frozen=True, slots=True)
class BatchTrackReportEntry:
    transaction_id: str
    track_id: str
    sequence: int
    state: TransactionState
    track_report_sha256: str | None

    def __post_init__(self) -> None:
        _require_identifier(self.transaction_id, "batch entry transaction_id")
        _require_identifier(self.track_id, "batch entry track_id")
        _require_int(self.sequence, "batch entry sequence", minimum=1)
        _require_enum(self.state, TransactionState, "batch entry state")
        _require_optional_sha256(self.track_report_sha256, "batch entry track_report_sha256")


@dataclass(frozen=True, slots=True)
class BatchReport:
    schema_version: int
    plan_id: str
    plan_sha256: str
    generated_at_utc: str
    status: BatchStatus
    tracks: tuple[BatchTrackReportEntry, ...]
    selected_count: int
    completed_count: int
    blocked_count: int
    unstarted_count: int
    canonical_sha256: str

    SCHEMA_VERSION: ClassVar[int] = RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        _require_schema_version(self.schema_version, "batch report")
        _require_identifier(self.plan_id, "batch report plan_id")
        _require_sha256(self.plan_sha256, "batch report plan_sha256")
        _require_utc(self.generated_at_utc, "batch report generated_at_utc")
        _require_enum(self.status, BatchStatus, "batch report status")
        if not isinstance(self.tracks, tuple) or not self.tracks:
            raise InputError("batch report tracks must be a nonempty tuple")
        if not all(isinstance(item, BatchTrackReportEntry) for item in self.tracks):
            raise InputError("batch report tracks must contain BatchTrackReportEntry records")
        if tuple(item.sequence for item in self.tracks) != tuple(sorted(item.sequence for item in self.tracks)):
            raise InputError("batch report tracks must be in sequence order")
        if len({item.track_id for item in self.tracks}) != len(self.tracks):
            raise InputError("batch report track IDs must be unique")
        for field_name in ("selected_count", "completed_count", "blocked_count", "unstarted_count"):
            _require_int(getattr(self, field_name), f"batch report {field_name}")
        if self.selected_count != len(self.tracks):
            raise InputError("batch report selected_count must equal the number of tracks")
        if self.completed_count + self.blocked_count + self.unstarted_count > self.selected_count:
            raise InputError("batch report state counts cannot exceed selected_count")
        _require_sha256(self.canonical_sha256, "batch report canonical_sha256", allow_unsealed=True)


FrozenPlan = FrozenBatchPlan
TrackPlan = FrozenTrackPlan


def record_to_data(value: Any) -> Any:
    """Convert a typed record to JSON data without weakening its types."""

    if is_dataclass(value) and not isinstance(value, type):
        return {field.name: record_to_data(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, MappingABC):
        result: dict[str, Any] = {}
        for key, item in value.items():
            if type(key) is not str:
                raise InputError("canonical JSON object names must be strings")
            result[key] = record_to_data(item)
        return result
    if isinstance(value, (tuple, list)):
        return [record_to_data(item) for item in value]
    if value is None or type(value) in {str, int, bool}:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise InputError("canonical JSON numbers must be finite")
        return value
    raise InputError(f"Unsupported canonical JSON value type: {type(value).__name__}")


def canonical_json_bytes(value: Any, *, omit_fields: tuple[str, ...] = ()) -> bytes:
    """Serialize JSON deterministically as compact, sorted UTF-8 bytes."""

    data = record_to_data(value)
    if omit_fields:
        if not isinstance(data, dict):
            raise InputError("canonical JSON fields can only be omitted from an object")
        data = {key: item for key, item in data.items() if key not in set(omit_fields)}
    try:
        return json.dumps(
            data,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except (TypeError, ValueError, UnicodeEncodeError) as exc:
        raise InputError(f"Cannot encode canonical JSON: {exc}") from exc


def canonical_json_text(value: Any, *, omit_fields: tuple[str, ...] = ()) -> str:
    return canonical_json_bytes(value, omit_fields=omit_fields).decode("utf-8")


def canonical_sha256(value: Any, *, omit_fields: tuple[str, ...] = ()) -> str:
    return sha256_bytes(canonical_json_bytes(value, omit_fields=omit_fields))


def authorization_confirmation_sha256(
    *,
    display_sha256: str,
    challenge: str,
    decision: AuthorizationDecision,
    confirmed_at_utc: str,
) -> str:
    """Hash the complete exact-confirmation evidence retained by authorization."""

    _require_sha256(display_sha256, "authorization confirmation display_sha256")
    _require_sha256(challenge, "authorization confirmation challenge")
    _require_enum(decision, AuthorizationDecision, "authorization confirmation decision")
    _require_utc(confirmed_at_utc, "authorization confirmation confirmed_at_utc")
    return canonical_sha256(
        {
            "schema": "frontier-paid-authorization-confirmation-v1",
            "display_sha256": display_sha256,
            "challenge": challenge,
            "decision": decision.value,
            "confirmed_at_utc": confirmed_at_utc,
        }
    )


def _embedded_digest_field(value: Any) -> str | None:
    names = {field.name for field in fields(value)} if is_dataclass(value) else set()
    if "canonical_sha256" in names:
        return "canonical_sha256"
    if "event_sha256" in names:
        return "event_sha256"
    return None


def seal_record(value: T) -> T:
    """Return a record with its embedded digest calculated over that field omitted."""

    digest_field = _embedded_digest_field(value)
    if digest_field is None:
        raise InputError(f"{type(value).__name__} has no embedded digest field")
    digest = canonical_sha256(value, omit_fields=(digest_field,))
    return replace(value, **{digest_field: digest})


def _verify_embedded_digest(value: Any) -> None:
    digest_field = _embedded_digest_field(value)
    if digest_field is None:
        return
    actual = getattr(value, digest_field)
    _require_sha256(actual, f"{type(value).__name__}.{digest_field}")
    expected = canonical_sha256(value, omit_fields=(digest_field,))
    if actual != expected:
        raise InputError(f"{type(value).__name__}.{digest_field} does not match canonical content")


def _decode_value(expected_type: Any, value: Any, label: str) -> Any:
    origin = get_origin(expected_type)
    arguments = get_args(expected_type)

    if origin in {Union, UnionType}:
        failures: list[InputError] = []
        for option in arguments:
            try:
                return _decode_value(option, value, label)
            except InputError as exc:
                failures.append(exc)
        raise InputError(f"{label} has a value incompatible with its declared type") from failures[-1]

    if expected_type is type(None):
        if value is not None:
            raise InputError(f"{label} must be null")
        return None

    if isinstance(expected_type, type) and issubclass(expected_type, Enum):
        if type(value) is not str:
            raise InputError(f"{label} must be a string enum value")
        try:
            return expected_type(value)
        except ValueError as exc:
            allowed = [item.value for item in expected_type]
            raise InputError(f"{label} has unknown enum value {value!r}; allowed={allowed}") from exc

    if isinstance(expected_type, type) and is_dataclass(expected_type):
        if not isinstance(value, dict):
            raise InputError(f"{label} must be a JSON object")
        expected_fields = {field.name: field for field in fields(expected_type)}
        actual_names = set(value)
        expected_names = set(expected_fields)
        if actual_names != expected_names:
            missing = sorted(expected_names - actual_names)
            unknown = sorted(actual_names - expected_names)
            raise InputError(f"{label} fields are invalid; missing={missing}, unknown={unknown}")
        hints = get_type_hints(expected_type)
        decoded = {
            name: _decode_value(hints[name], value[name], f"{label}.{name}")
            for name in expected_fields
        }
        try:
            return expected_type(**decoded)
        except InputError:
            raise
        except (TypeError, ValueError) as exc:
            raise InputError(f"{label} is invalid: {exc}") from exc

    if origin is tuple:
        if not isinstance(value, list):
            raise InputError(f"{label} must be a JSON array")
        if len(arguments) == 2 and arguments[1] is Ellipsis:
            return tuple(_decode_value(arguments[0], item, f"{label}[{index}]") for index, item in enumerate(value))
        if len(value) != len(arguments):
            raise InputError(f"{label} must contain exactly {len(arguments)} items")
        return tuple(
            _decode_value(item_type, item, f"{label}[{index}]")
            for index, (item_type, item) in enumerate(zip(arguments, value, strict=True))
        )

    if origin in {dict, Mapping, MappingABC}:
        if not isinstance(value, dict):
            raise InputError(f"{label} must be a JSON object")
        key_type, item_type = arguments
        return {
            _decode_value(key_type, key, f"{label} object name"): _decode_value(
                item_type, item, f"{label}[{key!r}]"
            )
            for key, item in value.items()
        }

    if expected_type is str:
        if type(value) is not str:
            raise InputError(f"{label} must be a string")
        return value
    if expected_type is int:
        if type(value) is not int:
            raise InputError(f"{label} must be an integer")
        return value
    if expected_type is bool:
        if type(value) is not bool:
            raise InputError(f"{label} must be a boolean")
        return value
    if expected_type is float:
        if type(value) is not float or not math.isfinite(value):
            raise InputError(f"{label} must be a finite JSON float")
        return value

    raise InputError(f"{label} uses unsupported record type {expected_type!r}")


class StrictRecordCodec(Generic[T]):
    """Strict schema-aware codec for one expected record type.

    Known Evidence_Artifact records additionally pass the central explicit
    allowlist before bytes are emitted or accepted.  The import is deliberately
    local so the evidence module can use this codec without an import cycle.
    """

    def __init__(self, record_type: type[T]):
        if not is_dataclass(record_type):
            raise TypeError("StrictRecordCodec requires a dataclass record type")
        self.record_type = record_type

    def _assert_evidence_safe(self, value: T) -> None:
        from .production_evidence import assert_typed_evidence_safe

        assert_typed_evidence_safe(
            value,
            artifact_path=f"evidence/{self.record_type.__name__}.json",
        )

    def dump_bytes(self, value: T) -> bytes:
        if not isinstance(value, self.record_type):
            raise InputError(f"Expected {self.record_type.__name__}, got {type(value).__name__}")
        self._assert_evidence_safe(value)
        _verify_embedded_digest(value)
        return canonical_json_bytes(value)

    def dumps(self, value: T) -> str:
        return self.dump_bytes(value).decode("utf-8")

    def sha256(self, value: T) -> str:
        return sha256_bytes(self.dump_bytes(value))

    def loads(
        self,
        raw: str | bytes,
        *,
        label: str | None = None,
        require_canonical: bool = True,
    ) -> T:
        source_label = label or self.record_type.__name__
        if isinstance(raw, bytes):
            raw_bytes = raw
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise InputError(f"Malformed UTF-8 JSON in {source_label}: {exc}") from exc
        elif isinstance(raw, str):
            text = raw
            try:
                raw_bytes = raw.encode("utf-8")
            except UnicodeEncodeError as exc:
                raise InputError(f"Malformed Unicode JSON in {source_label}: {exc}") from exc
        else:
            raise InputError(f"{source_label} must be UTF-8 JSON text or bytes")

        data = json_loads_strict(text, source_label)
        decoded = _decode_value(self.record_type, data, source_label)
        self._assert_evidence_safe(decoded)
        _verify_embedded_digest(decoded)
        canonical = canonical_json_bytes(decoded)
        if require_canonical and raw_bytes != canonical:
            raise InputError(f"JSON in {source_label} is valid but not canonically encoded")
        return decoded

    def load(self, path: Path, *, require_canonical: bool = True) -> T:
        return self.loads(
            read_bytes_nofollow(path), label=str(path), require_canonical=require_canonical
        )

    def write_atomic(self, path: Path, value: T) -> None:
        """Atomically write canonical bytes; callers retain collision policy ownership."""

        atomic_write_bytes(path, self.dump_bytes(value))
