"""Strict production TOML, deterministic overrides, and ordered Track catalog.

The configuration owns production behavior and source declarations, not manuscript or
written-edition content.  Pending Special Tracks therefore remain disabled catalog
entries until publishing supplies and approves a narratable source handoff.
"""

from __future__ import annotations

import json
import math
import re
import string
import tomllib
from dataclasses import dataclass, field
from enum import Enum, StrEnum
from pathlib import Path, PurePosixPath
from typing import Iterable

from .errors import InputError
from .manuscript import FILENAME_CHAPTER
from .pronunciation import (
    EMPTY_LEXICON,
    PronunciationLexicon,
    parse_pronunciation_entries,
)
from .production_models import (
    RECORD_SCHEMA_VERSION,
    AudioEncoding,
    AudioFormat,
    EffectiveTrackConfig,
    FidelityPolicy,
    TrackKind,
)
from .util import (
    read_bytes_nofollow,
    resolve_inside,
    sha256_bytes,
    workspace_relative,
)

_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_CHAPTER_ID_PATTERN = re.compile(r"^chapter-(\d{3})$")
_SECTION_PATTERN = re.compile(r"^[a-z0-9]+(?:[-_.][a-z0-9]+)*$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_SEQUENCE_FORMAT_PATTERN = re.compile(r"^(?:d|0?[1-6]d)?$")

_OVERRIDE_SCALARS = (
    "voice",
    "model_id",
    "region",
    "profile_label",
    "target_segment_words",
    "fidelity_policy",
    "normalization",
    "output_template",
)
_AUDIO_FIELDS = ("sample_rate_hz", "sample_size_bits", "channels")
_OUTPUT_TEMPLATE_FIELDS = frozenset(
    {"book_id", "sequence", "track_id", "track_slug", "track_kind", "voice"}
)


class SourceApprovalStatus(StrEnum):
    """Publishing handoff state for one configured Track source."""

    NOT_REQUIRED = "not-required"
    PENDING = "pending"
    APPROVED = "approved"


def _text(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value:
        raise InputError(f"{label} must be a nonblank canonical string")
    return value


def _identifier(value: object, label: str) -> str:
    text = _text(value, label)
    if not _ID_PATTERN.fullmatch(text):
        raise InputError(f"{label} must be a lowercase hyphenated identifier")
    return text


def _section(value: object, label: str) -> str:
    text = _text(value, label)
    if not _SECTION_PATTERN.fullmatch(text):
        raise InputError(f"{label} must be a lowercase section identifier")
    return text


def _integer(value: object, label: str, *, minimum: int) -> int:
    if type(value) is not int or value < minimum:
        raise InputError(f"{label} must be an integer >= {minimum}")
    return value


def _boolean(value: object, label: str) -> bool:
    if type(value) is not bool:
        raise InputError(f"{label} must be a boolean")
    return value


def _relative_path(value: object, label: str) -> str:
    text = _text(value, label)
    if "\\" in text:
        raise InputError(f"{label} must use workspace-relative POSIX separators")
    candidate = PurePosixPath(text)
    if candidate.is_absolute() or text == "." or any(
        part in {"", ".", ".."} for part in candidate.parts
    ):
        raise InputError(f"{label} must be a traversal-free relative path")
    if candidate.as_posix() != text:
        raise InputError(f"{label} must be a canonical relative path")
    return text


def _sha256(value: object, label: str) -> str:
    if not isinstance(value, str) or not _SHA256_PATTERN.fullmatch(value):
        raise InputError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _enum(value: object, expected: type[Enum], label: str):
    if not isinstance(value, expected):
        raise InputError(f"{label} must be a {expected.__name__} value")
    return value


def _parse_enum(value: object, expected: type[Enum], label: str):
    if type(value) is not str:
        raise InputError(f"{label} must be a string enum value")
    try:
        return expected(value)
    except ValueError as exc:
        allowed = [item.value for item in expected]
        raise InputError(f"{label} has unknown enum value {value!r}; allowed={allowed}") from exc


def _table(value: object, label: str) -> dict[str, object]:
    if not isinstance(value, dict):
        raise InputError(f"{label} must be a TOML table")
    return value


def _exact_keys(
    value: dict[str, object],
    *,
    required: set[str],
    optional: set[str] = frozenset(),
    label: str,
) -> None:
    actual = set(value)
    allowed = required | optional
    missing = sorted(required - actual)
    unknown = sorted(actual - allowed)
    if missing or unknown:
        raise InputError(f"{label} keys are invalid; missing={missing}, unknown={unknown}")


def _reject_nonfinite(value: object, label: str) -> None:
    if type(value) is float and not math.isfinite(value):
        raise InputError(f"{label} contains a non-finite number")
    if isinstance(value, dict):
        for key, item in value.items():
            _reject_nonfinite(item, f"{label}.{key}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _reject_nonfinite(item, f"{label}[{index}]")


def _format_output_name(
    template: str,
    *,
    book_id: str,
    sequence: int,
    track_id: str,
    track_kind: TrackKind,
    voice: str,
    label: str,
) -> str:
    try:
        rendered = template.format(
            book_id=book_id,
            sequence=sequence,
            track_id=track_id,
            track_slug=track_id,
            track_kind=track_kind.value,
            voice=voice,
        )
    except (IndexError, KeyError, ValueError) as exc:
        raise InputError(f"{label} cannot be rendered safely: {exc}") from exc
    rendered = _relative_path(rendered, f"{label} rendered name")
    candidate = PurePosixPath(rendered)
    if len(candidate.parts) != 1:
        raise InputError(f"{label} must render one confined WAV filename")
    if candidate.suffix != ".wav":
        raise InputError(f"{label} must render a lowercase .wav filename")
    return rendered


def _validate_output_template(value: object, label: str) -> str:
    template = _relative_path(value, label)
    try:
        parsed = tuple(string.Formatter().parse(template))
    except ValueError as exc:
        raise InputError(f"{label} is malformed: {exc}") from exc
    for _literal, field_name, format_spec, conversion in parsed:
        if field_name is None:
            continue
        if field_name not in _OUTPUT_TEMPLATE_FIELDS:
            raise InputError(
                f"{label} uses unsupported field {field_name!r}; "
                f"allowed={sorted(_OUTPUT_TEMPLATE_FIELDS)}"
            )
        if conversion is not None:
            raise InputError(f"{label} must not use conversions")
        if "{" in format_spec or "}" in format_spec:
            raise InputError(f"{label} must not use nested format fields")
        if field_name == "sequence":
            if not _SEQUENCE_FORMAT_PATTERN.fullmatch(format_spec):
                raise InputError(f"{label} has an unsafe sequence format")
        elif format_spec:
            raise InputError(f"{label} must not format string field {field_name!r}")
    _format_output_name(
        template,
        book_id="book",
        sequence=1,
        track_id="track",
        track_kind=TrackKind.CHAPTER,
        voice="voice",
        label=label,
    )
    return template


@dataclass(frozen=True, slots=True)
class AudioOverride:
    sample_rate_hz: int | None = None
    sample_size_bits: int | None = None
    channels: int | None = None

    def __post_init__(self) -> None:
        for field_name in _AUDIO_FIELDS:
            value = getattr(self, field_name)
            if value is not None:
                _integer(value, f"audio override {field_name}", minimum=1)

    @property
    def is_empty(self) -> bool:
        return all(getattr(self, name) is None for name in _AUDIO_FIELDS)


@dataclass(frozen=True, slots=True)
class TrackSettingsOverride:
    voice: str | None = None
    model_id: str | None = None
    region: str | None = None
    profile_label: str | None = None
    target_segment_words: int | None = None
    fidelity_policy: FidelityPolicy | None = None
    normalization: str | None = None
    output_template: str | None = None
    audio: AudioOverride = field(default_factory=AudioOverride)

    def __post_init__(self) -> None:
        for field_name in ("voice", "model_id", "region", "profile_label", "normalization"):
            value = getattr(self, field_name)
            if value is not None:
                _text(value, f"track override {field_name}")
        if self.target_segment_words is not None:
            _integer(
                self.target_segment_words,
                "track override target_segment_words",
                minimum=1,
            )
        if self.fidelity_policy is not None:
            _enum(self.fidelity_policy, FidelityPolicy, "track override fidelity_policy")
        if self.output_template is not None:
            _validate_output_template(self.output_template, "track override output_template")
        if not isinstance(self.audio, AudioOverride):
            raise InputError("track override audio must be an AudioOverride")


@dataclass(frozen=True, slots=True)
class ProductionDefaults:
    voice: str
    model_id: str
    region: str
    profile_label: str
    target_segment_words: int
    fidelity_policy: FidelityPolicy
    normalization: str
    output_template: str
    audio: AudioFormat

    def __post_init__(self) -> None:
        for field_name in ("voice", "model_id", "region", "profile_label", "normalization"):
            _text(getattr(self, field_name), f"defaults.{field_name}")
        _integer(self.target_segment_words, "defaults.target_segment_words", minimum=1)
        _enum(self.fidelity_policy, FidelityPolicy, "defaults.fidelity_policy")
        if self.fidelity_policy is not FidelityPolicy.EXACT:
            raise InputError("defaults.fidelity_policy must remain exact")
        _validate_output_template(self.output_template, "defaults.output_template")
        if not isinstance(self.audio, AudioFormat):
            raise InputError("defaults.audio must be an AudioFormat")


@dataclass(frozen=True, slots=True)
class EstimateConfig:
    rate_max_age_hours: int
    preflight_max_age_hours: int
    input_speech_tokens_per_call: int
    input_text_tokens_per_call: int
    output_speech_tokens_per_call: int
    output_text_tokens_per_call: int

    def __post_init__(self) -> None:
        _integer(self.rate_max_age_hours, "estimate.rate_max_age_hours", minimum=1)
        _integer(self.preflight_max_age_hours, "estimate.preflight_max_age_hours", minimum=1)
        for field_name in (
            "input_speech_tokens_per_call",
            "input_text_tokens_per_call",
            "output_speech_tokens_per_call",
            "output_text_tokens_per_call",
        ):
            _integer(getattr(self, field_name), f"estimate.{field_name}", minimum=0)


@dataclass(frozen=True, slots=True)
class TrackKindOverride:
    kind: TrackKind
    settings: TrackSettingsOverride

    def __post_init__(self) -> None:
        _enum(self.kind, TrackKind, "track kind override kind")
        if not isinstance(self.settings, TrackSettingsOverride):
            raise InputError("track kind override settings must be TrackSettingsOverride")


@dataclass(frozen=True, slots=True)
class TrackDeclaration:
    id: str
    kind: TrackKind
    sequence: int
    source_path: str
    source_section: str | None
    approved_sha256: str | None
    render_once: bool
    enabled: bool = True
    approval_status: SourceApprovalStatus = SourceApprovalStatus.NOT_REQUIRED
    override: TrackSettingsOverride = field(default_factory=TrackSettingsOverride)

    def __post_init__(self) -> None:
        _identifier(self.id, "track.id")
        _enum(self.kind, TrackKind, "track.kind")
        _integer(self.sequence, "track.sequence", minimum=1)
        _relative_path(self.source_path, "track.source_path")
        if self.source_section is not None:
            _section(self.source_section, "track.source_section")
        if self.approved_sha256 is not None:
            _sha256(self.approved_sha256, "track.approved_sha256")
        _boolean(self.render_once, "track.render_once")
        _boolean(self.enabled, "track.enabled")
        _enum(self.approval_status, SourceApprovalStatus, "track.approval_status")
        if not isinstance(self.override, TrackSettingsOverride):
            raise InputError("track.override must be TrackSettingsOverride")


@dataclass(frozen=True, slots=True)
class BookProductionConfig:
    schema_version: int
    book_id: str
    manuscript_root: str
    build_root: str
    delivery_root: str
    max_tracks_per_plan: int
    defaults: ProductionDefaults
    estimate: EstimateConfig
    track_kind_overrides: tuple[TrackKindOverride, ...]
    tracks: tuple[TrackDeclaration, ...]
    pronunciations: PronunciationLexicon = EMPTY_LEXICON

    SCHEMA_VERSION = RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != RECORD_SCHEMA_VERSION:
            raise InputError(
                f"production config schema_version must be integer {RECORD_SCHEMA_VERSION}"
            )
        _identifier(self.book_id, "production config book_id")
        for field_name in ("manuscript_root", "build_root", "delivery_root"):
            _relative_path(getattr(self, field_name), f"production config {field_name}")
        _integer(self.max_tracks_per_plan, "production config max_tracks_per_plan", minimum=1)
        if not isinstance(self.defaults, ProductionDefaults):
            raise InputError("production config defaults must be ProductionDefaults")
        if not isinstance(self.estimate, EstimateConfig):
            raise InputError("production config estimate must be EstimateConfig")
        if not isinstance(self.track_kind_overrides, tuple) or not all(
            isinstance(item, TrackKindOverride) for item in self.track_kind_overrides
        ):
            raise InputError("production config track_kind_overrides must be a tuple")
        if len({item.kind for item in self.track_kind_overrides}) != len(
            self.track_kind_overrides
        ):
            raise InputError("production config contains duplicate Track-kind overrides")
        object.__setattr__(
            self,
            "track_kind_overrides",
            tuple(sorted(self.track_kind_overrides, key=lambda item: item.kind.value)),
        )
        if not isinstance(self.tracks, tuple) or not all(
            isinstance(item, TrackDeclaration) for item in self.tracks
        ):
            raise InputError("production config tracks must be a tuple")
        if len({item.id for item in self.tracks}) != len(self.tracks):
            raise InputError("production config contains duplicate Track IDs")
        if len({item.sequence for item in self.tracks}) != len(self.tracks):
            raise InputError("production config contains duplicate Track sequence positions")
        object.__setattr__(self, "tracks", tuple(sorted(self.tracks, key=lambda item: item.sequence)))
        if not isinstance(self.pronunciations, PronunciationLexicon):
            raise InputError("production config pronunciations must be a PronunciationLexicon")


ProductionConfig = BookProductionConfig


@dataclass(frozen=True, slots=True)
class CatalogTrack:
    """One deterministic catalog item, including disabled publishing placeholders."""

    id: str
    kind: TrackKind
    sequence: int
    source_path: str
    source_section: str | None
    approved_sha256: str | None
    verified_source_sha256: str | None
    render_once: bool
    enabled: bool
    approval_status: SourceApprovalStatus
    effective_config: EffectiveTrackConfig

    def __post_init__(self) -> None:
        _identifier(self.id, "catalog track id")
        _enum(self.kind, TrackKind, "catalog track kind")
        _integer(self.sequence, "catalog track sequence", minimum=1)
        _relative_path(self.source_path, "catalog track source_path")
        if self.source_section is not None:
            _section(self.source_section, "catalog track source_section")
        if self.approved_sha256 is not None:
            _sha256(self.approved_sha256, "catalog track approved_sha256")
        if self.verified_source_sha256 is not None:
            _sha256(self.verified_source_sha256, "catalog track verified_source_sha256")
        _boolean(self.render_once, "catalog track render_once")
        _boolean(self.enabled, "catalog track enabled")
        _enum(self.approval_status, SourceApprovalStatus, "catalog track approval_status")
        if not isinstance(self.effective_config, EffectiveTrackConfig):
            raise InputError("catalog track effective_config must be EffectiveTrackConfig")
        if (
            self.effective_config.track_id != self.id
            or self.effective_config.track_kind is not self.kind
            or self.effective_config.sequence != self.sequence
        ):
            raise InputError("catalog track and effective configuration identity must match")


@dataclass(frozen=True, slots=True)
class OrderedTrackCatalog:
    """Unique catalog order plus the finite plan-scope bound."""

    book_id: str
    max_tracks_per_plan: int
    tracks: tuple[CatalogTrack, ...]

    def __post_init__(self) -> None:
        _identifier(self.book_id, "catalog book_id")
        _integer(self.max_tracks_per_plan, "catalog max_tracks_per_plan", minimum=1)
        if not isinstance(self.tracks, tuple) or not all(
            isinstance(item, CatalogTrack) for item in self.tracks
        ):
            raise InputError("catalog tracks must be a tuple of CatalogTrack values")
        ordered = tuple(sorted(self.tracks, key=lambda item: item.sequence))
        if len({item.id for item in ordered}) != len(ordered):
            raise InputError("ordered Track catalog contains duplicate Track IDs")
        if len({item.sequence for item in ordered}) != len(ordered):
            raise InputError("ordered Track catalog contains duplicate sequence positions")
        output_paths = [item.effective_config.output_path for item in ordered]
        if len(set(output_paths)) != len(output_paths):
            raise InputError("ordered Track catalog contains duplicate output paths")
        object.__setattr__(self, "tracks", ordered)

    def select_track_ids(self, track_ids: Iterable[str]) -> tuple[CatalogTrack, ...]:
        """Resolve exact IDs in catalog order while enforcing the configured plan bound."""

        if isinstance(track_ids, (str, bytes)):
            raise InputError("Track selection must be an iterable of Track IDs")
        requested = tuple(_identifier(item, "selected Track ID") for item in track_ids)
        if not requested:
            raise InputError("Track selection must not be empty")
        if len(set(requested)) != len(requested):
            raise InputError("Track selection contains duplicate Track IDs")
        if len(requested) > self.max_tracks_per_plan:
            raise InputError(
                "Track selection exceeds max_tracks_per_plan="
                f"{self.max_tracks_per_plan}"
            )
        by_id = {item.id: item for item in self.tracks}
        unresolved = sorted(set(requested) - set(by_id))
        if unresolved:
            raise InputError(f"Track selection contains unresolved IDs: {unresolved}")
        disabled = sorted(track_id for track_id in requested if not by_id[track_id].enabled)
        if disabled:
            raise InputError(f"Track selection contains disabled pending IDs: {disabled}")
        requested_set = set(requested)
        return tuple(item for item in self.tracks if item.id in requested_set)


def _parse_audio_defaults(value: object, label: str) -> AudioFormat:
    table = _table(value, label)
    _exact_keys(table, required=set(_AUDIO_FIELDS), label=label)
    return AudioFormat(
        sample_rate_hz=_integer(table["sample_rate_hz"], f"{label}.sample_rate_hz", minimum=1),
        sample_size_bits=_integer(
            table["sample_size_bits"], f"{label}.sample_size_bits", minimum=1
        ),
        channels=_integer(table["channels"], f"{label}.channels", minimum=1),
        encoding=AudioEncoding.PCM_S16LE,
    )


def _parse_audio_override(value: object, label: str) -> AudioOverride:
    table = _table(value, label)
    _exact_keys(table, required=set(), optional=set(_AUDIO_FIELDS), label=label)
    parsed: dict[str, int | None] = {}
    for field_name in _AUDIO_FIELDS:
        parsed[field_name] = (
            None
            if field_name not in table
            else _integer(table[field_name], f"{label}.{field_name}", minimum=1)
        )
    return AudioOverride(**parsed)


def _parse_override(value: object, label: str) -> TrackSettingsOverride:
    table = _table(value, label)
    _exact_keys(
        table,
        required=set(),
        optional=set(_OVERRIDE_SCALARS) | {"audio"},
        label=label,
    )
    values: dict[str, object] = {}
    for field_name in ("voice", "model_id", "region", "profile_label", "normalization"):
        values[field_name] = (
            None if field_name not in table else _text(table[field_name], f"{label}.{field_name}")
        )
    values["target_segment_words"] = (
        None
        if "target_segment_words" not in table
        else _integer(table["target_segment_words"], f"{label}.target_segment_words", minimum=1)
    )
    values["fidelity_policy"] = (
        None
        if "fidelity_policy" not in table
        else _parse_enum(table["fidelity_policy"], FidelityPolicy, f"{label}.fidelity_policy")
    )
    values["output_template"] = (
        None
        if "output_template" not in table
        else _validate_output_template(table["output_template"], f"{label}.output_template")
    )
    values["audio"] = (
        AudioOverride()
        if "audio" not in table
        else _parse_audio_override(table["audio"], f"{label}.audio")
    )
    return TrackSettingsOverride(**values)


def parse_production_toml(
    raw: str | bytes, *, label: str = "production TOML"
) -> BookProductionConfig:
    """Parse untrusted production TOML with exact schemas and typed values."""

    if isinstance(raw, bytes):
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise InputError(f"Malformed UTF-8 TOML in {label}: {exc}") from exc
    elif isinstance(raw, str):
        text = raw
    else:
        raise InputError(f"{label} must be UTF-8 TOML text or bytes")

    try:
        parsed = tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        raise InputError(f"Malformed TOML in {label}: {exc}") from exc
    _reject_nonfinite(parsed, label)
    _exact_keys(
        parsed,
        required={
            "schema_version",
            "book_id",
            "manuscript_root",
            "build_root",
            "delivery_root",
            "max_tracks_per_plan",
            "defaults",
            "estimate",
            "tracks",
        },
        optional={"track_kinds", "pronunciations"},
        label="production config",
    )
    if type(parsed["schema_version"]) is not int or parsed["schema_version"] != RECORD_SCHEMA_VERSION:
        raise InputError(
            f"production config schema_version must be integer {RECORD_SCHEMA_VERSION}"
        )

    defaults_table = _table(parsed["defaults"], "defaults")
    _exact_keys(
        defaults_table,
        required=set(_OVERRIDE_SCALARS) | {"audio"},
        label="defaults",
    )
    defaults = ProductionDefaults(
        voice=_text(defaults_table["voice"], "defaults.voice"),
        model_id=_text(defaults_table["model_id"], "defaults.model_id"),
        region=_text(defaults_table["region"], "defaults.region"),
        profile_label=_text(defaults_table["profile_label"], "defaults.profile_label"),
        target_segment_words=_integer(
            defaults_table["target_segment_words"], "defaults.target_segment_words", minimum=1
        ),
        fidelity_policy=_parse_enum(
            defaults_table["fidelity_policy"], FidelityPolicy, "defaults.fidelity_policy"
        ),
        normalization=_text(defaults_table["normalization"], "defaults.normalization"),
        output_template=_validate_output_template(
            defaults_table["output_template"], "defaults.output_template"
        ),
        audio=_parse_audio_defaults(defaults_table["audio"], "defaults.audio"),
    )

    estimate_table = _table(parsed["estimate"], "estimate")
    estimate_fields = {
        "rate_max_age_hours",
        "preflight_max_age_hours",
        "input_speech_tokens_per_call",
        "input_text_tokens_per_call",
        "output_speech_tokens_per_call",
        "output_text_tokens_per_call",
    }
    _exact_keys(estimate_table, required=estimate_fields, label="estimate")
    estimate = EstimateConfig(
        rate_max_age_hours=_integer(
            estimate_table["rate_max_age_hours"], "estimate.rate_max_age_hours", minimum=1
        ),
        preflight_max_age_hours=_integer(
            estimate_table["preflight_max_age_hours"],
            "estimate.preflight_max_age_hours",
            minimum=1,
        ),
        input_speech_tokens_per_call=_integer(
            estimate_table["input_speech_tokens_per_call"],
            "estimate.input_speech_tokens_per_call",
            minimum=0,
        ),
        input_text_tokens_per_call=_integer(
            estimate_table["input_text_tokens_per_call"],
            "estimate.input_text_tokens_per_call",
            minimum=0,
        ),
        output_speech_tokens_per_call=_integer(
            estimate_table["output_speech_tokens_per_call"],
            "estimate.output_speech_tokens_per_call",
            minimum=0,
        ),
        output_text_tokens_per_call=_integer(
            estimate_table["output_text_tokens_per_call"],
            "estimate.output_text_tokens_per_call",
            minimum=0,
        ),
    )

    kind_overrides: list[TrackKindOverride] = []
    if "track_kinds" in parsed:
        kinds_table = _table(parsed["track_kinds"], "track_kinds")
        allowed_kinds = {kind.value for kind in TrackKind}
        _exact_keys(
            kinds_table,
            required=set(),
            optional=allowed_kinds,
            label="track_kinds",
        )
        for kind in TrackKind:
            if kind.value in kinds_table:
                kind_overrides.append(
                    TrackKindOverride(
                        kind=kind,
                        settings=_parse_override(
                            kinds_table[kind.value], f"track_kinds.{kind.value}"
                        ),
                    )
                )

    track_values = parsed["tracks"]
    if not isinstance(track_values, list):
        raise InputError("tracks must be an array of TOML tables")
    tracks: list[TrackDeclaration] = []
    for index, item in enumerate(track_values):
        track = _table(item, f"tracks[{index}]")
        _exact_keys(
            track,
            required={"id", "kind", "sequence", "source_path", "render_once"},
            optional={
                "source_section",
                "approved_sha256",
                "enabled",
                "approval_status",
                "override",
            },
            label=f"tracks[{index}]",
        )
        kind = _parse_enum(track["kind"], TrackKind, f"tracks[{index}].kind")
        tracks.append(
            TrackDeclaration(
                id=_identifier(track["id"], f"tracks[{index}].id"),
                kind=kind,
                sequence=_integer(track["sequence"], f"tracks[{index}].sequence", minimum=1),
                source_path=_relative_path(
                    track["source_path"], f"tracks[{index}].source_path"
                ),
                source_section=(
                    None
                    if "source_section" not in track
                    else _section(track["source_section"], f"tracks[{index}].source_section")
                ),
                approved_sha256=(
                    None
                    if "approved_sha256" not in track
                    else _sha256(track["approved_sha256"], f"tracks[{index}].approved_sha256")
                ),
                render_once=_boolean(track["render_once"], f"tracks[{index}].render_once"),
                enabled=(
                    True
                    if "enabled" not in track
                    else _boolean(track["enabled"], f"tracks[{index}].enabled")
                ),
                approval_status=(
                    SourceApprovalStatus.NOT_REQUIRED
                    if "approval_status" not in track and kind is TrackKind.CHAPTER
                    else SourceApprovalStatus.APPROVED
                    if "approval_status" not in track
                    else _parse_enum(
                        track["approval_status"],
                        SourceApprovalStatus,
                        f"tracks[{index}].approval_status",
                    )
                ),
                override=(
                    TrackSettingsOverride()
                    if "override" not in track
                    else _parse_override(track["override"], f"tracks[{index}].override")
                ),
            )
        )

    return BookProductionConfig(
        schema_version=parsed["schema_version"],
        book_id=_identifier(parsed["book_id"], "production config book_id"),
        manuscript_root=_relative_path(
            parsed["manuscript_root"], "production config manuscript_root"
        ),
        build_root=_relative_path(parsed["build_root"], "production config build_root"),
        delivery_root=_relative_path(
            parsed["delivery_root"], "production config delivery_root"
        ),
        max_tracks_per_plan=_integer(
            parsed["max_tracks_per_plan"],
            "production config max_tracks_per_plan",
            minimum=1,
        ),
        defaults=defaults,
        estimate=estimate,
        track_kind_overrides=tuple(kind_overrides),
        tracks=tuple(tracks),
        pronunciations=(
            EMPTY_LEXICON
            if "pronunciations" not in parsed
            else parse_pronunciation_entries(
                parsed["pronunciations"], "production config pronunciations"
            )
        ),
    )


def _quote(value: str) -> str:
    try:
        return json.dumps(value, ensure_ascii=False).encode("utf-8").decode("utf-8")
    except UnicodeEncodeError as exc:
        raise InputError(f"Cannot encode production TOML string: {exc}") from exc


def _toml_scalar(value: object) -> str:
    if isinstance(value, Enum):
        return _quote(str(value.value))
    if type(value) is str:
        return _quote(value)
    if type(value) is bool:
        return "true" if value else "false"
    if type(value) is int:
        return str(value)
    raise InputError(f"Unsupported production TOML scalar: {type(value).__name__}")


def _append_assignment(lines: list[str], name: str, value: object) -> None:
    lines.append(f"{name} = {_toml_scalar(value)}")


def _append_override(lines: list[str], header: str, settings: TrackSettingsOverride) -> None:
    lines.append(f"[{header}]")
    for field_name in _OVERRIDE_SCALARS:
        value = getattr(settings, field_name)
        if value is not None:
            _append_assignment(lines, field_name, value)
    lines.append("")
    if not settings.audio.is_empty:
        lines.append(f"[{header}.audio]")
        for field_name in _AUDIO_FIELDS:
            value = getattr(settings.audio, field_name)
            if value is not None:
                _append_assignment(lines, field_name, value)
        lines.append("")


def print_production_toml(config: BookProductionConfig) -> str:
    """Format every present supported value as deterministic valid TOML."""

    if not isinstance(config, BookProductionConfig):
        raise InputError("print_production_toml requires BookProductionConfig")
    lines: list[str] = []
    for field_name in (
        "schema_version",
        "book_id",
        "manuscript_root",
        "build_root",
        "delivery_root",
        "max_tracks_per_plan",
    ):
        _append_assignment(lines, field_name, getattr(config, field_name))
    lines.append("")

    lines.append("[defaults]")
    for field_name in _OVERRIDE_SCALARS:
        _append_assignment(lines, field_name, getattr(config.defaults, field_name))
    lines.append("")
    lines.append("[defaults.audio]")
    for field_name in _AUDIO_FIELDS:
        _append_assignment(lines, field_name, getattr(config.defaults.audio, field_name))
    lines.append("")

    lines.append("[estimate]")
    for field_name in (
        "rate_max_age_hours",
        "preflight_max_age_hours",
        "input_speech_tokens_per_call",
        "input_text_tokens_per_call",
        "output_speech_tokens_per_call",
        "output_text_tokens_per_call",
    ):
        _append_assignment(lines, field_name, getattr(config.estimate, field_name))
    lines.append("")

    for item in config.track_kind_overrides:
        _append_override(lines, f"track_kinds.{item.kind.value}", item.settings)

    for entry in config.pronunciations.entries:
        lines.append("[[pronunciations]]")
        _append_assignment(lines, "written", entry.written)
        _append_assignment(lines, "spoken", entry.spoken)
        if entry.note is not None:
            _append_assignment(lines, "note", entry.note)
        lines.append("")

    for track in config.tracks:
        lines.append("[[tracks]]")
        _append_assignment(lines, "id", track.id)
        _append_assignment(lines, "kind", track.kind)
        _append_assignment(lines, "sequence", track.sequence)
        _append_assignment(lines, "source_path", track.source_path)
        if track.source_section is not None:
            _append_assignment(lines, "source_section", track.source_section)
        if track.approved_sha256 is not None:
            _append_assignment(lines, "approved_sha256", track.approved_sha256)
        _append_assignment(lines, "enabled", track.enabled)
        _append_assignment(lines, "approval_status", track.approval_status)
        _append_assignment(lines, "render_once", track.render_once)
        lines.append("")
        _append_override(lines, "tracks.override", track.override)

    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines) + "\n"


def load_production_config(path: Path) -> BookProductionConfig:
    return parse_production_toml(read_bytes_nofollow(path), label=str(path))


def production_toml_sha256(config: BookProductionConfig) -> str:
    return sha256_bytes(print_production_toml(config).encode("utf-8"))


class ProductionTomlCodec:
    """Small codec facade matching the strict record codec shape."""

    @staticmethod
    def loads(raw: str | bytes, *, label: str = "production TOML") -> BookProductionConfig:
        return parse_production_toml(raw, label=label)

    @staticmethod
    def dumps(config: BookProductionConfig) -> str:
        return print_production_toml(config)

    @staticmethod
    def load(path: Path) -> BookProductionConfig:
        return load_production_config(path)

    @staticmethod
    def sha256(config: BookProductionConfig) -> str:
        return production_toml_sha256(config)


def _apply_override(
    values: dict[str, object],
    audio_values: dict[str, int],
    provenance: dict[str, str],
    settings: TrackSettingsOverride,
    layer: str,
) -> None:
    for field_name in _OVERRIDE_SCALARS:
        value = getattr(settings, field_name)
        if value is not None:
            values[field_name] = value
            provenance[field_name] = layer
    for field_name in _AUDIO_FIELDS:
        value = getattr(settings.audio, field_name)
        if value is not None:
            audio_values[field_name] = value
            provenance[f"audio.{field_name}"] = layer


def resolve_effective_track_config(
    config: BookProductionConfig,
    track: TrackDeclaration,
) -> EffectiveTrackConfig:
    """Resolve global defaults < Track-kind override < exact-Track override."""

    if not isinstance(config, BookProductionConfig):
        raise InputError("resolve_effective_track_config requires BookProductionConfig")
    if not isinstance(track, TrackDeclaration):
        raise InputError("resolve_effective_track_config requires TrackDeclaration")

    values: dict[str, object] = {
        field_name: getattr(config.defaults, field_name) for field_name in _OVERRIDE_SCALARS
    }
    audio_values = {
        field_name: getattr(config.defaults.audio, field_name) for field_name in _AUDIO_FIELDS
    }
    provenance = {field_name: "global-defaults" for field_name in _OVERRIDE_SCALARS}
    provenance.update(
        {f"audio.{field_name}": "global-defaults" for field_name in _AUDIO_FIELDS}
    )

    kind_overrides = {item.kind: item.settings for item in config.track_kind_overrides}
    if track.kind in kind_overrides:
        _apply_override(
            values,
            audio_values,
            provenance,
            kind_overrides[track.kind],
            f"track-kind:{track.kind.value}",
        )
    _apply_override(
        values,
        audio_values,
        provenance,
        track.override,
        f"exact-track:{track.id}",
    )

    fidelity_policy = values["fidelity_policy"]
    if fidelity_policy is not FidelityPolicy.EXACT:
        raise InputError("effective fidelity_policy must remain exact")
    output_template = values["output_template"]
    if not isinstance(output_template, str):  # pragma: no cover - dataclass validation guards this
        raise InputError("effective output_template must be text")
    voice = values["voice"]
    if not isinstance(voice, str):  # pragma: no cover - dataclass validation guards this
        raise InputError("effective voice must be text")
    output_name = _format_output_name(
        output_template,
        book_id=config.book_id,
        sequence=track.sequence,
        track_id=track.id,
        track_kind=track.kind,
        voice=voice,
        label=f"effective output template for {track.id}",
    )
    output_path = _relative_path(
        (PurePosixPath(config.delivery_root) / config.book_id / output_name).as_posix(),
        f"effective output path for {track.id}",
    )
    provenance.update(
        {
            "track_id": "catalog",
            "track_kind": "catalog",
            "sequence": "catalog",
            "output_path": provenance["output_template"],
        }
    )

    return EffectiveTrackConfig(
        track_id=track.id,
        track_kind=track.kind,
        sequence=track.sequence,
        voice=voice,
        model_id=str(values["model_id"]),
        region=str(values["region"]),
        profile_label=str(values["profile_label"]),
        target_segment_words=int(values["target_segment_words"]),
        fidelity_policy=fidelity_policy,
        normalization=str(values["normalization"]),
        audio_format=AudioFormat(
            sample_rate_hz=audio_values["sample_rate_hz"],
            sample_size_bits=audio_values["sample_size_bits"],
            channels=audio_values["channels"],
            encoding=AudioEncoding.PCM_S16LE,
        ),
        output_path=output_path,
        resolution_provenance=provenance,
    )


def _validate_track_semantics(track: TrackDeclaration) -> None:
    if track.kind is TrackKind.CHAPTER:
        if track.render_once:
            raise InputError(f"Chapter Track {track.id!r} must not be Render_Once")
        if not track.enabled:
            raise InputError(f"Chapter Track {track.id!r} must remain enabled")
        if track.approval_status is not SourceApprovalStatus.NOT_REQUIRED:
            raise InputError(
                f"Chapter Track {track.id!r} must use approval_status='not-required'"
            )
        if track.source_section is not None or track.approved_sha256 is not None:
            raise InputError(f"Chapter Track {track.id!r} must not declare a publishing handoff")
        return

    if not track.render_once:
        raise InputError(f"Special Track {track.id!r} must be Render_Once")
    if track.approval_status is SourceApprovalStatus.NOT_REQUIRED:
        raise InputError(f"Special Track {track.id!r} must declare approved or pending status")
    if track.approval_status is SourceApprovalStatus.PENDING:
        if track.enabled:
            raise InputError(f"Pending Special Track {track.id!r} must be disabled")
        if track.approved_sha256 is not None:
            raise InputError(
                f"Pending Special Track {track.id!r} must not claim an approved hash"
            )
    elif track.enabled and track.approval_status is not SourceApprovalStatus.APPROVED:
        raise InputError(f"Enabled Special Track {track.id!r} requires approved source status")


def validate_approved_source_handoff(
    track: TrackDeclaration,
    workspace_root: Path,
) -> str | None:
    """Validate an enabled Special Track path/hash without persisting source text."""

    _validate_track_semantics(track)
    source_path = resolve_inside(workspace_root, track.source_path)
    if track.kind is TrackKind.CHAPTER or not track.enabled:
        return None
    source_sha256 = sha256_bytes(read_bytes_nofollow(source_path))
    if track.approved_sha256 is not None and source_sha256 != track.approved_sha256:
        raise InputError(
            f"Approved source hash mismatch for Special Track {track.id!r}: "
            f"expected {track.approved_sha256}, got {source_sha256}"
        )
    return source_sha256


def _discover_chapter_paths(
    config: BookProductionConfig,
    workspace_root: Path,
) -> dict[int, str]:
    chapter_root = resolve_inside(
        workspace_root,
        (PurePosixPath(config.manuscript_root) / "chapters").as_posix(),
    )
    if not chapter_root.is_dir():
        raise InputError(f"Configured manuscript chapter root is not a directory: {chapter_root}")

    discovered: dict[int, str] = {}
    for movement_path in sorted(chapter_root.iterdir(), key=lambda path: path.name):
        if movement_path.is_symlink():
            raise InputError(f"Chapter catalog must not traverse symlink: {movement_path}")
        if not movement_path.is_dir():
            continue
        for chapter_path in sorted(movement_path.iterdir(), key=lambda path: path.name):
            if chapter_path.is_symlink():
                raise InputError(f"Chapter catalog must not include symlink: {chapter_path}")
            match = FILENAME_CHAPTER.search(chapter_path.name)
            if match is None:
                continue
            if not chapter_path.is_file():
                raise InputError(f"Chapter catalog path is not a regular file: {chapter_path}")
            chapter_number = int(match.group(1))
            relative_path = workspace_relative(workspace_root, chapter_path)
            if chapter_number in discovered:
                raise InputError(
                    f"Chapter {chapter_number} resolves to multiple catalog sources: "
                    f"{discovered[chapter_number]!r}, {relative_path!r}"
                )
            discovered[chapter_number] = relative_path
    return discovered


def build_ordered_track_catalog(
    config: BookProductionConfig,
    workspace_root: Path,
) -> OrderedTrackCatalog:
    """Build all configured Special Tracks and discovered chapters deterministically."""

    if not isinstance(config, BookProductionConfig):
        raise InputError("build_ordered_track_catalog requires BookProductionConfig")
    workspace_root = workspace_root.expanduser().resolve()
    resolve_inside(workspace_root, config.manuscript_root)
    resolve_inside(workspace_root, config.delivery_root)

    explicit_chapters: dict[str, TrackDeclaration] = {}
    special_tracks: list[TrackDeclaration] = []
    for track in config.tracks:
        _validate_track_semantics(track)
        if track.kind is TrackKind.CHAPTER:
            match = _CHAPTER_ID_PATTERN.fullmatch(track.id)
            if match is None:
                raise InputError(
                    f"Explicit Chapter Track ID must use chapter-NNN form: {track.id!r}"
                )
            explicit_chapters[track.id] = track
        else:
            special_tracks.append(track)

    prefix_sequence = max(
        (
            track.sequence
            for track in special_tracks
            if track.kind in {TrackKind.OPENING_CREDITS, TrackKind.FRONT_MATTER}
        ),
        default=0,
    )
    chapter_paths = _discover_chapter_paths(config, workspace_root)
    chapter_tracks: list[TrackDeclaration] = []
    for chapter_number, source_path in sorted(chapter_paths.items()):
        track_id = f"chapter-{chapter_number:03d}"
        sequence = prefix_sequence + chapter_number
        explicit = explicit_chapters.pop(track_id, None)
        if explicit is not None:
            if explicit.source_path != source_path:
                raise InputError(
                    f"Explicit Chapter Track {track_id!r} source does not match discovery: "
                    f"{explicit.source_path!r} != {source_path!r}"
                )
            if explicit.sequence != sequence:
                raise InputError(
                    f"Explicit Chapter Track {track_id!r} sequence must be {sequence}"
                )
            chapter_tracks.append(explicit)
        else:
            chapter_tracks.append(
                TrackDeclaration(
                    id=track_id,
                    kind=TrackKind.CHAPTER,
                    sequence=sequence,
                    source_path=source_path,
                    source_section=None,
                    approved_sha256=None,
                    render_once=False,
                    enabled=True,
                    approval_status=SourceApprovalStatus.NOT_REQUIRED,
                )
            )
    if explicit_chapters:
        raise InputError(
            "Explicit Chapter Tracks do not resolve to discovered sources: "
            f"{sorted(explicit_chapters)}"
        )

    if chapter_tracks:
        last_chapter_sequence = max(track.sequence for track in chapter_tracks)
        misplaced_closing = sorted(
            track.id
            for track in special_tracks
            if track.kind is TrackKind.CLOSING_CREDITS
            and track.sequence <= last_chapter_sequence
        )
        if misplaced_closing:
            raise InputError(
                "Closing-credit Track sequence must follow every chapter: "
                f"{misplaced_closing}"
            )

    declarations = tuple(sorted((*special_tracks, *chapter_tracks), key=lambda item: item.sequence))
    catalog_tracks: list[CatalogTrack] = []
    for track in declarations:
        verified_source_sha256 = validate_approved_source_handoff(track, workspace_root)
        catalog_tracks.append(
            CatalogTrack(
                id=track.id,
                kind=track.kind,
                sequence=track.sequence,
                source_path=track.source_path,
                source_section=track.source_section,
                approved_sha256=track.approved_sha256,
                verified_source_sha256=verified_source_sha256,
                render_once=track.render_once,
                enabled=track.enabled,
                approval_status=track.approval_status,
                effective_config=resolve_effective_track_config(config, track),
            )
        )
    return OrderedTrackCatalog(
        book_id=config.book_id,
        max_tracks_per_plan=config.max_tracks_per_plan,
        tracks=tuple(catalog_tracks),
    )
