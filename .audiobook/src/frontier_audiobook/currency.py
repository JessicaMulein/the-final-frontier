"""Standing source-currency audit for chapter audio.

Every rendering pipeline records the digest of the source text it actually spoke.
This module re-reads those recorded digests and compares them against the live
manuscript, so a text edit that lands after a render is reported as stale audio
instead of silently shipping.

Two pipelines record the source digest under different conventions, and each is
compared under its own convention:

* ``production`` records ``source_sha256`` as the SHA-256 of the whole source
  file (``raw_sha256``).
* ``legacy-narration`` records ``source_sha256`` as the SHA-256 of the prose body
  only, deliberately excluding restricted-header edits.

Comparing a recorded digest under the wrong convention produces false staleness,
so the convention is bound to the pipeline rather than guessed.

The audit is read-only: it never calls a model, never contacts AWS, and never
writes to the delivered artifacts it inspects.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping, Sequence

from .errors import InputError
from .manuscript import read_chapter
from .util import (
    json_loads_strict,
    read_bytes_nofollow,
    resolve_inside,
    sha256_bytes,
    utc_now,
    workspace_relative,
)


class Pipeline(StrEnum):
    """Which workflow produced an audio artifact."""

    PRODUCTION = "production"
    LEGACY_NARRATION = "legacy-narration"


class SourceDigestConvention(StrEnum):
    """What bytes a pipeline hashed into its recorded source digest."""

    RAW_BYTES = "raw-bytes"
    PROSE_BODY = "prose-body"


_PIPELINE_CONVENTIONS: Mapping[Pipeline, SourceDigestConvention] = {
    Pipeline.PRODUCTION: SourceDigestConvention.RAW_BYTES,
    Pipeline.LEGACY_NARRATION: SourceDigestConvention.PROSE_BODY,
}


class CurrencyStatus(StrEnum):
    """Derived audit verdict for one audio artifact."""

    CURRENT = "current"
    STALE_SOURCE_CHANGED = "stale-source-changed"
    AUDIO_MODIFIED = "audio-modified"
    AUDIO_MISSING = "audio-missing"
    SOURCE_MISSING = "source-missing"
    SOURCE_UNREADABLE = "source-unreadable"


#: Verdicts that mean the delivered audio must not be shipped as-is.
FAILING_STATUSES = frozenset(
    {
        CurrencyStatus.STALE_SOURCE_CHANGED,
        CurrencyStatus.AUDIO_MODIFIED,
        CurrencyStatus.AUDIO_MISSING,
        CurrencyStatus.SOURCE_MISSING,
        CurrencyStatus.SOURCE_UNREADABLE,
    }
)


@dataclass(frozen=True, slots=True)
class AudioBinding:
    """One recorded claim that a specific audio file speaks a specific source."""

    pipeline: Pipeline
    track_id: str
    chapter: int | None
    voice: str | None
    evidence_path: str
    source_path: str
    recorded_source_sha256: str
    audio_path: str
    recorded_audio_sha256: str


@dataclass(frozen=True, slots=True)
class CurrencyResult:
    """Audit outcome for one :class:`AudioBinding`."""

    binding: AudioBinding
    status: CurrencyStatus
    convention: SourceDigestConvention
    current_source_sha256: str | None
    current_audio_sha256: str | None
    source_current: bool
    audio_intact: bool
    detail: str | None = None

    def as_json(self) -> dict[str, Any]:
        return {
            "pipeline": self.binding.pipeline.value,
            "track_id": self.binding.track_id,
            "chapter": self.binding.chapter,
            "voice": self.binding.voice,
            "status": self.status.value,
            "source_digest_convention": self.convention.value,
            "source_path": self.binding.source_path,
            "recorded_source_sha256": self.binding.recorded_source_sha256,
            "current_source_sha256": self.current_source_sha256,
            "source_current": self.source_current,
            "audio_path": self.binding.audio_path,
            "recorded_audio_sha256": self.binding.recorded_audio_sha256,
            "current_audio_sha256": self.current_audio_sha256,
            "audio_intact": self.audio_intact,
            "evidence_path": self.binding.evidence_path,
            "detail": self.detail,
        }


def _load_manifest(path: Path, label: str) -> dict[str, Any]:
    raw = read_bytes_nofollow(path)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError(f"{label} is not strict UTF-8") from exc
    value = json_loads_strict(text, label)
    if not isinstance(value, dict):
        raise InputError(f"{label} must be a JSON object")
    return value


def _text(value: Any) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def _digest(value: Any) -> str | None:
    if isinstance(value, str) and len(value) == 64:
        lowered = value.lower()
        if all(character in "0123456789abcdef" for character in lowered):
            return lowered
    return None


def _chapter_number(track_id: str) -> int | None:
    prefix = "chapter-"
    if not track_id.startswith(prefix):
        return None
    tail = track_id[len(prefix) :]
    return int(tail) if tail.isdigit() else None


def _file_digest(workspace_root: Path, relative: str) -> str | None:
    try:
        path = resolve_inside(workspace_root, relative)
    except InputError:
        return None
    if not path.is_file():
        return None
    try:
        return sha256_bytes(read_bytes_nofollow(path))
    except (InputError, OSError):
        return None


def discover_production_bindings(
    workspace_root: Path,
    *,
    build_root: str = ".audiobook/build/production",
) -> tuple[AudioBinding, ...]:
    """Collect delivered production artifacts from their own delivery evidence."""

    root = resolve_inside(workspace_root, build_root)
    if not root.is_dir():
        return ()

    latest: dict[str, tuple[str, AudioBinding]] = {}
    for delivery_path in sorted(root.glob("*/transactions/*/*/delivery/delivery.json")):
        transaction_root = delivery_path.parent.parent
        manifest_path = transaction_root / "runtime" / "manifest.json"
        if not manifest_path.is_file():
            continue
        delivery = _load_manifest(delivery_path, "delivery record")
        manifest = _load_manifest(manifest_path, "runtime manifest")

        if _text(delivery.get("status")) != "published":
            continue
        track_id = _text(manifest.get("track_id")) or transaction_root.parent.name
        source_path = _text(manifest.get("source_path"))
        recorded_source = _digest(manifest.get("source_sha256"))
        audio_path = _text(delivery.get("destination_path"))
        recorded_audio = _digest(delivery.get("destination_sha256"))
        if not (source_path and recorded_source and audio_path and recorded_audio):
            continue

        binding = AudioBinding(
            pipeline=Pipeline.PRODUCTION,
            track_id=track_id,
            chapter=_chapter_number(track_id),
            voice=_text(manifest.get("voice_id")),
            evidence_path=workspace_relative(workspace_root, delivery_path),
            source_path=source_path,
            recorded_source_sha256=recorded_source,
            audio_path=audio_path,
            recorded_audio_sha256=recorded_audio,
        )
        stamp = _text(delivery.get("recorded_at_utc")) or ""
        previous = latest.get(track_id)
        if previous is None or stamp >= previous[0]:
            latest[track_id] = (stamp, binding)

    return tuple(binding for _, binding in sorted(latest.values(), key=lambda item: item[1].track_id))


def discover_legacy_bindings(
    workspace_root: Path,
    *,
    narration_root: str = ".audiobook/build/narration",
) -> tuple[AudioBinding, ...]:
    """Collect legacy narrate artifacts from their per-chapter manifests."""

    root = resolve_inside(workspace_root, narration_root)
    if not root.is_dir():
        return ()

    bindings: list[AudioBinding] = []
    for manifest_path in sorted(root.glob("*/manifest.json")):
        manifest = _load_manifest(manifest_path, "narration manifest")
        source_path = _text(manifest.get("chapter_path"))
        recorded_source = _digest(manifest.get("source_sha256"))
        audio_path = _text(manifest.get("chapter_audio_path"))
        recorded_audio = _digest(manifest.get("chapter_audio_sha256"))
        if not (source_path and recorded_source and audio_path and recorded_audio):
            continue

        chapter = manifest.get("chapter")
        chapter_number = chapter if isinstance(chapter, int) else None
        bindings.append(
            AudioBinding(
                pipeline=Pipeline.LEGACY_NARRATION,
                track_id=manifest_path.parent.name,
                chapter=chapter_number,
                voice=_text(manifest.get("voice_id")),
                evidence_path=workspace_relative(workspace_root, manifest_path),
                source_path=source_path,
                recorded_source_sha256=recorded_source,
                audio_path=audio_path,
                recorded_audio_sha256=recorded_audio,
            )
        )
    return tuple(bindings)


def current_source_digest(
    workspace_root: Path,
    source_path: str,
    convention: SourceDigestConvention,
) -> tuple[str | None, str | None]:
    """Digest the live source under ``convention``; return ``(digest, error)``."""

    try:
        path = resolve_inside(workspace_root, source_path)
    except InputError as exc:
        return None, str(exc)
    if not path.is_file():
        return None, None

    if convention is SourceDigestConvention.RAW_BYTES:
        try:
            return sha256_bytes(read_bytes_nofollow(path)), None
        except (InputError, OSError) as exc:
            return None, str(exc)

    try:
        return read_chapter(path, enforce_declared_words=False).body_sha256, None
    except (InputError, OSError, UnicodeDecodeError) as exc:
        return None, str(exc)


def evaluate_binding(workspace_root: Path, binding: AudioBinding) -> CurrencyResult:
    """Compare one recorded binding against the live manuscript and audio."""

    convention = _PIPELINE_CONVENTIONS[binding.pipeline]
    current_source, error = current_source_digest(
        workspace_root, binding.source_path, convention
    )
    current_audio = _file_digest(workspace_root, binding.audio_path)

    source_current = current_source is not None and current_source == binding.recorded_source_sha256
    audio_intact = current_audio is not None and current_audio == binding.recorded_audio_sha256

    if error is not None:
        status = CurrencyStatus.SOURCE_UNREADABLE
        detail: str | None = error
    elif current_source is None:
        status = CurrencyStatus.SOURCE_MISSING
        detail = "recorded source path is absent from the workspace"
    elif current_audio is None:
        status = CurrencyStatus.AUDIO_MISSING
        detail = "recorded audio path is absent from the workspace"
    elif not source_current:
        status = CurrencyStatus.STALE_SOURCE_CHANGED
        detail = "source text changed after this audio was rendered; re-render required"
    elif not audio_intact:
        status = CurrencyStatus.AUDIO_MODIFIED
        detail = "audio bytes differ from the digest recorded at render time"
    else:
        status = CurrencyStatus.CURRENT
        detail = None

    return CurrencyResult(
        binding=binding,
        status=status,
        convention=convention,
        current_source_sha256=current_source,
        current_audio_sha256=current_audio,
        source_current=source_current,
        audio_intact=audio_intact,
        detail=detail,
    )


def find_unbound_audio(
    workspace_root: Path,
    results: Sequence[CurrencyResult],
    *,
    search_roots: Sequence[str] = ("voice-samples",),
) -> tuple[dict[str, Any], ...]:
    """Report loose WAVs, flagging any that duplicate a known bound artifact."""

    bound: dict[str, CurrencyResult] = {}
    bound_paths: set[str] = set()
    for result in results:
        bound.setdefault(result.binding.recorded_audio_sha256, result)
        bound_paths.add(result.binding.audio_path)

    found: list[dict[str, Any]] = []
    for relative_root in search_roots:
        try:
            root = resolve_inside(workspace_root, relative_root)
        except InputError:
            continue
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*.wav")):
            if path.is_symlink() or not path.is_file():
                continue
            relative = workspace_relative(workspace_root, path)
            if relative in bound_paths:
                continue
            digest = sha256_bytes(read_bytes_nofollow(path))
            match = bound.get(digest)
            found.append(
                {
                    "path": relative,
                    "sha256": digest,
                    "byte_count": path.stat().st_size,
                    "identical_to_track": match.binding.track_id if match else None,
                    "inherited_status": match.status.value if match else None,
                    "bound_to_evidence": match is not None,
                }
            )
    return tuple(found)


def audit_currency(
    workspace_root: Path,
    *,
    include_unbound: bool = True,
    audited_at_utc: str | None = None,
) -> dict[str, Any]:
    """Audit every recorded chapter-audio binding in the workspace."""

    bindings = (
        *discover_production_bindings(workspace_root),
        *discover_legacy_bindings(workspace_root),
    )
    results = tuple(evaluate_binding(workspace_root, binding) for binding in bindings)
    ordered = sorted(
        results,
        key=lambda item: (
            item.binding.chapter if item.binding.chapter is not None else 1 << 30,
            item.binding.pipeline.value,
            item.binding.track_id,
        ),
    )

    counts: dict[str, int] = {}
    for result in ordered:
        counts[result.status.value] = counts.get(result.status.value, 0) + 1

    stale = tuple(result for result in ordered if result.status in FAILING_STATUSES)
    payload: dict[str, Any] = {
        "schema_version": 1,
        "operation": "audit-currency",
        "billable_calls_made": 0,
        "model_calls_made": 0,
        "audited_at_utc": audited_at_utc or utc_now(),
        "audited_binding_count": len(ordered),
        "status_counts": counts,
        "all_current": not stale,
        "action_required": [
            {
                "chapter": result.binding.chapter,
                "track_id": result.binding.track_id,
                "status": result.status.value,
                "detail": result.detail,
            }
            for result in stale
        ],
        "bindings": [result.as_json() for result in ordered],
    }
    if include_unbound:
        payload["unbound_audio"] = list(find_unbound_audio(workspace_root, ordered))
    return payload


def format_currency_table(payload: Mapping[str, Any]) -> str:
    """Render a compact operator-readable summary of :func:`audit_currency`."""

    lines = [
        "Chapter audio source-currency audit",
        f"  audited at (UTC): {payload.get('audited_at_utc')}",
        f"  bindings audited: {payload.get('audited_binding_count')}",
        "",
        f"{'Ch':>3}  {'Pipeline':<17} {'Status':<22} {'Src':<4} {'Audio':<5} Artifact",
    ]
    for entry in payload.get("bindings", ()):
        chapter = entry.get("chapter")
        lines.append(
            f"{(chapter if chapter is not None else '-'):>3}  "
            f"{entry.get('pipeline', ''):<17} "
            f"{entry.get('status', ''):<22} "
            f"{('ok' if entry.get('source_current') else 'DIFF'):<4} "
            f"{('ok' if entry.get('audio_intact') else 'DIFF'):<5} "
            f"{entry.get('audio_path', '')}"
        )

    unbound = payload.get("unbound_audio") or ()
    if unbound:
        lines.extend(["", "Unbound WAVs (no render evidence of their own):"])
        for entry in unbound:
            match = entry.get("identical_to_track")
            note = (
                f"byte-identical to {match} ({entry.get('inherited_status')})"
                if match
                else "no matching recorded artifact"
            )
            lines.append(f"  {entry.get('path')}  -  {note}")

    actions = payload.get("action_required") or ()
    lines.append("")
    if actions:
        lines.append(f"Action required for {len(actions)} binding(s):")
        for entry in actions:
            lines.append(
                f"  chapter {entry.get('chapter')} ({entry.get('track_id')}): "
                f"{entry.get('status')} - {entry.get('detail')}"
            )
    else:
        lines.append("All audited audio is current with the manuscript.")
    return "\n".join(lines)
