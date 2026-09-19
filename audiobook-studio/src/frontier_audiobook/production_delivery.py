"""Collision-safe, nonbillable publication of validated production Tracks.

The Proof_Deliverer consumes only local, digest-bound validation evidence.  It
copies a validated WAV to a same-directory temporary file, verifies the complete
copy, and publishes without replacing an existing destination.  Every outcome is
an immutable canonical record and every successful repeat returns that record.
"""

from __future__ import annotations

import ctypes
import errno
import os
import re
import secrets
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePosixPath
from typing import Callable

from .errors import InputError
from .production import load_production_plan
from .production_models import (
    RECORD_SCHEMA_VERSION,
    DeliveryStatus,
    DestinationState,
    FrozenBatchPlan,
    FrozenTrackPlan,
    StrictRecordCodec,
    TransactionState,
    ValidationEvidence,
    seal_record,
)
from .production_evidence import resolve_private_runtime_path
from .production_transactions import TransactionStore
from .production_validation import load_passing_validation_evidence
from .util import (
    durable_mkdir,
    fsync_directory,
    json_loads_strict,
    read_bytes_nofollow,
    resolve_inside,
    resolve_inside_approved_root,
    sha256_bytes,
    utc_now,
    workspace_relative,
)

Clock = Callable[[], datetime]

_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_UTC = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")


@dataclass(frozen=True, slots=True)
class ProductionTrackScope:
    """One exact Track and its canonical production paths."""

    workspace_root: Path
    plan_path: Path
    plan: FrozenBatchPlan
    track: FrozenTrackPlan
    book_root: Path
    transaction_root: Path
    store: TransactionStore


@dataclass(frozen=True, slots=True)
class DeliveryRecord:
    """Sanitized immutable evidence for one Proof_Deliverer decision."""

    schema_version: int
    transaction_id: str
    track_id: str
    recorded_at_utc: str
    validation_sha256: str
    source_path: str
    destination_path: str
    destination_state: DestinationState
    status: DeliveryStatus
    source_byte_count: int
    source_sha256: str
    destination_byte_count: int | None
    destination_sha256: str | None
    complete_byte_sequence_verified: bool
    temporary_copy_verified: bool
    atomic_publish_performed: bool
    destination_preserved: bool
    nonbillable: bool
    canonical_sha256: str

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != RECORD_SCHEMA_VERSION:
            raise InputError(
                f"delivery record schema_version must be integer {RECORD_SCHEMA_VERSION}"
            )
        _require_identifier(self.transaction_id, "delivery transaction_id")
        _require_identifier(self.track_id, "delivery track_id")
        _require_utc(self.recorded_at_utc, "delivery recorded_at_utc")
        _require_sha256(self.validation_sha256, "delivery validation_sha256")
        _require_relative_path(self.source_path, "delivery source_path")
        _require_relative_path(self.destination_path, "delivery destination_path")
        if self.source_path == self.destination_path:
            raise InputError("delivery source and destination paths must differ")
        if not isinstance(self.destination_state, DestinationState):
            raise InputError("delivery destination_state must be a DestinationState")
        if not isinstance(self.status, DeliveryStatus):
            raise InputError("delivery status must be a DeliveryStatus")
        if type(self.source_byte_count) is not int or self.source_byte_count < 1:
            raise InputError("delivery source_byte_count must be a positive integer")
        _require_sha256(self.source_sha256, "delivery source_sha256")
        if (self.destination_byte_count is None) != (self.destination_sha256 is None):
            raise InputError("delivery destination byte count and digest must appear together")
        if self.destination_byte_count is not None:
            if type(self.destination_byte_count) is not int or self.destination_byte_count < 0:
                raise InputError(
                    "delivery destination_byte_count must be a nonnegative integer"
                )
            _require_sha256(self.destination_sha256, "delivery destination_sha256")
        for name in (
            "complete_byte_sequence_verified",
            "temporary_copy_verified",
            "atomic_publish_performed",
            "destination_preserved",
            "nonbillable",
        ):
            if type(getattr(self, name)) is not bool:
                raise InputError(f"delivery {name} must be a boolean")
        if not self.nonbillable:
            raise InputError("delivery records must declare nonbillable=true")

        successful = self.status in {
            DeliveryStatus.PUBLISHED,
            DeliveryStatus.ALREADY_IDENTICAL,
        }
        if successful:
            if self.destination_byte_count != self.source_byte_count:
                raise InputError("successful delivery byte counts must match")
            if self.destination_sha256 != self.source_sha256:
                raise InputError("successful delivery digests must match")
            if not self.complete_byte_sequence_verified:
                raise InputError("successful delivery requires complete byte verification")
        elif self.status is DeliveryStatus.CONFLICTING:
            if self.destination_state is not DestinationState.CONFLICTING:
                raise InputError("conflicting delivery must record a conflicting destination")
            if self.complete_byte_sequence_verified or self.atomic_publish_performed:
                raise InputError("conflicting delivery cannot claim publication or byte identity")
            if not self.destination_preserved:
                raise InputError("conflicting delivery must preserve the destination")
        else:
            raise InputError("delivery record status must be published, identical, or conflicting")

        if self.status is DeliveryStatus.PUBLISHED:
            if self.destination_state is not DestinationState.ABSENT:
                raise InputError("published delivery must originate from an absent destination")
            if not (
                self.temporary_copy_verified
                and self.atomic_publish_performed
                and not self.destination_preserved
            ):
                raise InputError(
                    "published delivery requires verified temporary atomic publication"
                )
        elif self.status is DeliveryStatus.ALREADY_IDENTICAL:
            if self.destination_state is not DestinationState.ALREADY_IDENTICAL:
                raise InputError("identical delivery must record already-identical")
            if self.atomic_publish_performed or not self.destination_preserved:
                raise InputError("identical delivery must retain the existing destination")

        _require_sha256(
            self.canonical_sha256,
            "delivery canonical_sha256",
            allow_empty=True,
        )


def _require_identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise InputError(f"{label} must be a lowercase hyphenated identifier")
    return value


def _require_sha256(value: object, label: str, *, allow_empty: bool = False) -> str:
    if allow_empty and value == "":
        return ""
    if not isinstance(value, str) or not _SHA256.fullmatch(value):
        raise InputError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_utc(value: object, label: str) -> str:
    if not isinstance(value, str) or not _UTC.fullmatch(value):
        raise InputError(f"{label} must be an ISO-8601 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise InputError(f"{label} is not a valid UTC timestamp") from exc
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise InputError(f"{label} must be UTC")
    return value


def _require_relative_path(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\\" in value:
        raise InputError(f"{label} must be a canonical workspace-relative POSIX path")
    candidate = PurePosixPath(value)
    if (
        candidate.is_absolute()
        or value == "."
        or any(part in {"", ".", ".."} for part in candidate.parts)
        or candidate.as_posix() != value
    ):
        raise InputError(f"{label} must be traversal-free and workspace-relative")
    return value


def _timestamp(value: str | None, clock: Clock | None) -> str:
    if value is not None and clock is not None:
        raise InputError("Pass delivered_at_utc or clock, not both")
    if value is not None:
        return _require_utc(value, "delivery timestamp")
    if clock is None:
        return utc_now()
    now = clock()
    if not isinstance(now, datetime) or now.tzinfo is None or now.utcoffset() != UTC.utcoffset(now):
        raise InputError("delivery clock must return an aware UTC datetime")
    return now.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def _resolve_plan_path(workspace_root: Path, plan_path: Path) -> Path:
    candidate = plan_path.expanduser()
    relative = (
        workspace_relative(workspace_root, candidate)
        if candidate.is_absolute()
        else candidate.as_posix()
    )
    return resolve_inside(workspace_root, relative)


def load_production_track_scope(
    workspace_root: Path,
    plan_path: Path,
    track_id: str,
    transaction_id: str,
) -> ProductionTrackScope:
    """Load one exact digest-valid Track scope from the production layout."""

    root = workspace_root.expanduser().resolve()
    checked_track = _require_identifier(track_id, "delivery track_id")
    checked_transaction = _require_identifier(transaction_id, "delivery transaction_id")
    absolute_plan = _resolve_plan_path(root, plan_path)
    plan = load_production_plan(absolute_plan)
    if (
        absolute_plan.name != "plan.json"
        or absolute_plan.parent.name != plan.plan_id
        or absolute_plan.parent.parent.name != "plans"
        or absolute_plan.parent.parent.parent.name != plan.book_id
    ):
        raise InputError("Frozen plan path does not match the production plan layout")
    matches = tuple(
        track
        for track in plan.tracks
        if track.track_id == checked_track
        and track.transaction_id == checked_transaction
    )
    if len(matches) != 1:
        raise InputError("Delivery scope is not one exact Frozen Track plan")
    book_root = absolute_plan.parent.parent.parent
    store = TransactionStore(book_root, plan.book_id)
    transaction_root = store.transaction_path(checked_track, checked_transaction)
    try:
        transaction_root.relative_to(book_root)
    except ValueError as exc:  # pragma: no cover - identifiers make this defensive
        raise InputError("Transaction path escapes the production book root") from exc
    return ProductionTrackScope(
        workspace_root=root,
        plan_path=absolute_plan,
        plan=plan,
        track=matches[0],
        book_root=book_root,
        transaction_root=transaction_root,
        store=store,
    )


def _load_validated_wav(
    scope: ProductionTrackScope,
) -> tuple[ValidationEvidence, str, Path, bytes, str]:
    manifest_value = workspace_relative(
        scope.workspace_root,
        scope.transaction_root / "runtime" / "manifest.json",
    )
    manifest_path = resolve_private_runtime_path(
        scope.workspace_root,
        scope.transaction_root,
        manifest_value,
        require_exists=True,
        expected_kind="file",
    )
    manifest_raw = read_bytes_nofollow(manifest_path)
    manifest_sha256 = sha256_bytes(manifest_raw)
    plan_sha256 = StrictRecordCodec(FrozenBatchPlan).sha256(scope.plan)
    validation, _validation_path = load_passing_validation_evidence(
        scope.transaction_root,
        transaction_id=scope.track.transaction_id,
        track_id=scope.track.track_id,
        plan_sha256=plan_sha256,
        manifest_sha256=manifest_sha256,
    )
    validation_sha256 = StrictRecordCodec(ValidationEvidence).sha256(validation)

    try:
        manifest_text = manifest_raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError("Runtime manifest is not valid UTF-8") from exc
    manifest = json_loads_strict(manifest_text, str(manifest_path))
    if not isinstance(manifest, dict):
        raise InputError("Runtime manifest must be a JSON object")

    required = {
        "track_id",
        "transaction_id",
        "track_audio_path",
        "track_audio_sha256",
        "track_audio_byte_count",
    }
    if not required.issubset(manifest):
        raise InputError("Runtime manifest lacks required validated WAV bindings")
    if (
        manifest["track_id"] != scope.track.track_id
        or manifest["transaction_id"] != scope.track.transaction_id
    ):
        raise InputError("Runtime manifest identity differs from the Frozen Track")
    source_value = _require_relative_path(
        manifest["track_audio_path"], "runtime manifest track_audio_path"
    )
    expected_sha256 = _require_sha256(
        manifest["track_audio_sha256"], "runtime manifest track_audio_sha256"
    )
    expected_count = manifest["track_audio_byte_count"]
    if type(expected_count) is not int or expected_count < 1:
        raise InputError("runtime manifest track_audio_byte_count must be positive")

    source_path = resolve_private_runtime_path(
        scope.workspace_root,
        scope.transaction_root,
        source_value,
        require_exists=True,
        expected_kind="file",
    )
    if source_path.name != PurePosixPath(scope.track.effective_config.output_path).name:
        raise InputError("Validated Track WAV name differs from the frozen destination name")
    source_content = read_bytes_nofollow(source_path)
    if len(source_content) != expected_count or sha256_bytes(source_content) != expected_sha256:
        raise InputError("Validated Track WAV bytes differ from the runtime manifest")
    return validation, validation_sha256, source_path, source_content, expected_sha256


def _configured_delivery_root(scope: ProductionTrackScope) -> Path:
    """Derive the one frozen configured root shared by every planned destination."""

    roots: set[str] = set()
    for track in scope.plan.tracks:
        output_value = _require_relative_path(
            track.effective_config.output_path,
            "frozen delivery output_path",
        )
        output = PurePosixPath(output_value)
        if output.parent.name != scope.plan.book_id or output.parent.parent == PurePosixPath("."):
            raise InputError("Frozen delivery path is outside its configured book root")
        roots.add(output.parent.parent.as_posix())
    if len(roots) != 1:
        raise InputError("Frozen plan spans multiple configured delivery roots")
    return resolve_inside(scope.workspace_root, roots.pop())


def _classify_destination(
    destination: Path,
    source_content: bytes,
) -> tuple[DestinationState, int | None, str | None]:
    if not os.path.lexists(destination):
        return DestinationState.ABSENT, None, None
    if destination.is_symlink() or not destination.is_file():
        return DestinationState.CONFLICTING, None, None
    destination_content = read_bytes_nofollow(destination)
    destination_count = len(destination_content)
    destination_sha256 = sha256_bytes(destination_content)
    if (
        destination_count == len(source_content)
        and destination_sha256 == sha256_bytes(source_content)
        and destination_content == source_content
    ):
        return (
            DestinationState.ALREADY_IDENTICAL,
            destination_count,
            destination_sha256,
        )
    return DestinationState.CONFLICTING, destination_count, destination_sha256


def _platform_rename_noreplace(source: Path, destination: Path) -> bool | None:
    """Use the host's atomic no-replace rename, or return None if unavailable."""

    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(source)
    destination_bytes = os.fsencode(destination)
    function = None
    arguments: tuple[object, ...]

    if sys.platform == "darwin":
        function = getattr(libc, "renamex_np", None)
        if function is None:
            return None
        function.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint]
        function.restype = ctypes.c_int
        arguments = (source_bytes, destination_bytes, 0x00000004)  # RENAME_EXCL
    elif sys.platform.startswith("linux"):
        function = getattr(libc, "renameat2", None)
        if function is None:
            return None
        function.argtypes = [
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        ]
        function.restype = ctypes.c_int
        arguments = (-100, source_bytes, -100, destination_bytes, 1)  # RENAME_NOREPLACE
    else:
        return None

    ctypes.set_errno(0)
    result = function(*arguments)
    if result == 0:
        return True
    error = ctypes.get_errno()
    if error in {errno.EEXIST, errno.ENOTEMPTY}:
        return False
    if error in {errno.ENOSYS, errno.ENOTSUP, errno.EINVAL}:
        return None
    raise InputError(
        f"Cannot atomically publish delivery destination: {os.strerror(error)}"
    )


def _atomic_publish_noreplace(source: Path, destination: Path) -> bool:
    """Atomically publish source, returning False when destination already exists."""

    if source.parent != destination.parent:
        raise InputError("Atomic delivery publication requires a same-directory temporary")
    try:
        platform_result = _platform_rename_noreplace(source, destination)
        if platform_result is not None:
            if platform_result:
                fsync_directory(destination.parent)
            return platform_result

        # Portable POSIX fallback: linking the verified same-filesystem temporary is
        # an atomic create-if-absent publication.  The temporary name is then removed.
        try:
            os.link(source, destination, follow_symlinks=False)
        except TypeError:  # pragma: no cover - older Windows/Python fallback
            os.link(source, destination)
        except FileExistsError:
            return False
        source.unlink()
        fsync_directory(destination.parent)
        return True
    except FileExistsError:
        return False
    except OSError as exc:
        raise InputError(f"Cannot atomically publish {destination}: {exc}") from exc


def _write_temporary(path: Path, content: bytes) -> None:
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0)
        | getattr(os, "O_CLOEXEC", 0)
    )
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags, 0o600)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise InputError(f"Cannot write delivery temporary {path}: {exc}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _publish_verified_temporary(
    source_path: Path,
    source_content: bytes,
    destination: Path,
) -> tuple[bool, bool]:
    """Verify a same-directory temporary and atomically publish it if still absent."""

    durable_mkdir(destination.parent)
    temporary = destination.parent / (
        f".{destination.name}.delivery-{secrets.token_hex(12)}.tmp"
    )
    _write_temporary(temporary, source_content)
    try:
        temporary_content = read_bytes_nofollow(temporary)
        if (
            len(temporary_content) != len(source_content)
            or sha256_bytes(temporary_content) != sha256_bytes(source_content)
            or temporary_content != source_content
        ):
            raise InputError("Delivery temporary copy failed complete byte verification")
        if read_bytes_nofollow(source_path) != source_content:
            raise InputError("Validated Track WAV changed during delivery")
        published = _atomic_publish_noreplace(temporary, destination)
        return published, True
    finally:
        if os.path.lexists(temporary):
            if temporary.is_symlink() or not temporary.is_file():
                raise InputError("Delivery temporary path became unsafe")
            temporary.unlink()
            fsync_directory(destination.parent)


def write_immutable_evidence(path: Path, content: bytes) -> None:
    """Publish immutable evidence or accept a cooperating identical writer."""

    durable_mkdir(path.parent)
    if os.path.lexists(path):
        if path.is_symlink() or not path.is_file():
            raise InputError(f"Immutable evidence path is unsafe: {path}")
        if read_bytes_nofollow(path) != content:
            raise InputError(f"Immutable evidence collision at {path}")
        return
    temporary = path.parent / f".{path.name}.{secrets.token_hex(12)}.tmp"
    _write_temporary(temporary, content)
    try:
        if read_bytes_nofollow(temporary) != content:
            raise InputError("Immutable evidence temporary failed byte verification")
        published = _atomic_publish_noreplace(temporary, path)
        if not published:
            if path.is_symlink() or not path.is_file() or read_bytes_nofollow(path) != content:
                raise InputError(f"Immutable evidence collision at {path}")
    finally:
        if os.path.lexists(temporary):
            temporary.unlink()
            fsync_directory(path.parent)


def _verify_existing_record(
    scope: ProductionTrackScope,
    record: DeliveryRecord,
    validation_sha256: str,
    source_path: Path,
    source_content: bytes,
    destination: Path,
) -> None:
    if (
        record.transaction_id != scope.track.transaction_id
        or record.track_id != scope.track.track_id
        or record.validation_sha256 != validation_sha256
        or record.source_path != workspace_relative(scope.workspace_root, source_path)
        or record.destination_path != scope.track.effective_config.output_path
        or record.source_byte_count != len(source_content)
        or record.source_sha256 != sha256_bytes(source_content)
    ):
        raise InputError("Existing delivery record differs from current validated evidence")
    if read_bytes_nofollow(source_path) != source_content:
        raise InputError("Validated Track WAV changed after delivery")
    state, count, digest = _classify_destination(destination, source_content)
    if record.status in {DeliveryStatus.PUBLISHED, DeliveryStatus.ALREADY_IDENTICAL}:
        if state is not DestinationState.ALREADY_IDENTICAL:
            raise InputError("Delivered destination no longer matches the validated Track WAV")
    elif state is not DestinationState.CONFLICTING:
        raise InputError("Blocked delivery destination no longer matches retained collision evidence")
    if count != record.destination_byte_count or digest != record.destination_sha256:
        raise InputError("Delivery destination differs from its immutable delivery record")


def _delivery_record(
    scope: ProductionTrackScope,
    *,
    recorded_at_utc: str,
    validation_sha256: str,
    source_path: Path,
    source_content: bytes,
    destination: Path,
    destination_state: DestinationState,
    destination_byte_count: int | None,
    destination_sha256: str | None,
    temporary_copy_verified: bool,
    atomic_publish_performed: bool,
) -> DeliveryRecord:
    if atomic_publish_performed:
        status = DeliveryStatus.PUBLISHED
    elif destination_state is DestinationState.ALREADY_IDENTICAL:
        status = DeliveryStatus.ALREADY_IDENTICAL
    else:
        status = DeliveryStatus.CONFLICTING
    return seal_record(
        DeliveryRecord(
            schema_version=RECORD_SCHEMA_VERSION,
            transaction_id=scope.track.transaction_id,
            track_id=scope.track.track_id,
            recorded_at_utc=recorded_at_utc,
            validation_sha256=validation_sha256,
            source_path=workspace_relative(scope.workspace_root, source_path),
            destination_path=scope.track.effective_config.output_path,
            destination_state=(
                DestinationState.ABSENT
                if atomic_publish_performed
                else destination_state
            ),
            status=status,
            source_byte_count=len(source_content),
            source_sha256=sha256_bytes(source_content),
            destination_byte_count=destination_byte_count,
            destination_sha256=destination_sha256,
            complete_byte_sequence_verified=(
                status in {DeliveryStatus.PUBLISHED, DeliveryStatus.ALREADY_IDENTICAL}
            ),
            temporary_copy_verified=temporary_copy_verified,
            atomic_publish_performed=atomic_publish_performed,
            destination_preserved=not atomic_publish_performed,
            nonbillable=True,
            canonical_sha256="",
        )
    )


def _record_transition(scope: ProductionTrackScope, record: DeliveryRecord) -> None:
    succeeded = record.status in {
        DeliveryStatus.PUBLISHED,
        DeliveryStatus.ALREADY_IDENTICAL,
    }
    scope.store.append_transition(
        scope.track.track_id,
        scope.track.transaction_id,
        operation_id="deliver-v1",
        event_type="delivery-succeeded" if succeeded else "delivery-blocked",
        state_after=TransactionState.DELIVERED if succeeded else TransactionState.BLOCKED,
        details={
            "delivery-record-sha256": StrictRecordCodec(DeliveryRecord).sha256(record),
            "delivery-status": record.status.value,
            "destination-sha256": record.destination_sha256,
            "model-calls-started": 0,
        },
        occurred_at_utc=record.recorded_at_utc,
    )


def deliver_validated_track(
    workspace_root: Path,
    plan_path: Path,
    track_id: str,
    transaction_id: str,
    *,
    delivered_at_utc: str | None = None,
    clock: Clock | None = None,
) -> DeliveryRecord:
    """Publish one validated Track locally without overwrite, child, AWS, or model calls.

    A successful repeat verifies and returns the immutable prior DeliveryRecord.
    A different existing destination is retained, recorded as ``conflicting``, and
    transitions only this transaction to ``blocked``.
    """

    scope = load_production_track_scope(
        workspace_root,
        plan_path,
        track_id,
        transaction_id,
    )
    (
        _validation,
        validation_sha256,
        source_path,
        source_content,
        _source_sha256,
    ) = _load_validated_wav(scope)
    destination = resolve_inside_approved_root(
        scope.workspace_root,
        _configured_delivery_root(scope),
        scope.track.effective_config.output_path,
    )
    if destination == source_path:
        raise InputError("Delivery destination must differ from the private runtime WAV")

    record_path = scope.transaction_root / "delivery" / "delivery.json"
    codec = StrictRecordCodec(DeliveryRecord)
    record: DeliveryRecord
    with scope.store.track_lock(scope.track.track_id):
        snapshot = scope.store.inspect_transaction(
            scope.track.track_id,
            scope.track.transaction_id,
        )
        if os.path.lexists(record_path):
            record = codec.load(record_path)
            _verify_existing_record(
                scope,
                record,
                validation_sha256,
                source_path,
                source_content,
                destination,
            )
        else:
            if snapshot.state is not TransactionState.VALIDATED:
                raise InputError("Delivery requires independently reconstructed validated state")
            state, destination_count, destination_sha256 = _classify_destination(
                destination,
                source_content,
            )
            temporary_verified = False
            published = False
            if state is DestinationState.ABSENT:
                published, temporary_verified = _publish_verified_temporary(
                    source_path,
                    source_content,
                    destination,
                )
                state, destination_count, destination_sha256 = _classify_destination(
                    destination,
                    source_content,
                )
                if published and state is not DestinationState.ALREADY_IDENTICAL:
                    raise InputError("Published destination failed post-rename byte verification")
            record = _delivery_record(
                scope,
                recorded_at_utc=_timestamp(delivered_at_utc, clock),
                validation_sha256=validation_sha256,
                source_path=source_path,
                source_content=source_content,
                destination=destination,
                destination_state=state,
                destination_byte_count=destination_count,
                destination_sha256=destination_sha256,
                temporary_copy_verified=temporary_verified,
                atomic_publish_performed=published,
            )
            write_immutable_evidence(record_path, codec.dump_bytes(record))
            if codec.load(record_path) != record:
                raise InputError("Delivery record failed canonical round-trip verification")

    # append_transition owns the canonical Track lock.  If publication committed but
    # this append was interrupted, a repeat reuses the immutable record and completes
    # this exact idempotent operation without touching destination bytes.
    _record_transition(scope, record)
    return record


__all__ = [
    "DeliveryRecord",
    "ProductionTrackScope",
    "deliver_validated_track",
    "load_production_track_scope",
    "write_immutable_evidence",
]
