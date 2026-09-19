"""Independent production transaction ledgers and derived status.

Transaction directories are the authority.  The book status index is only a
rebuildable cache and is never consulted without first reconstructing current
transaction truth from canonical metadata, payloads, and hash-chained events.
This module performs local filesystem work only; it has no AWS, network, audio,
or paid-execution integration.
"""

from __future__ import annotations

import errno
import os
import re
import secrets
import threading
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime
from enum import StrEnum
from pathlib import Path, PurePosixPath
from types import MappingProxyType
from typing import ClassVar, TypeAlias

try:  # POSIX advisory locks
    import fcntl
except ImportError:  # pragma: no cover - exercised on Windows
    fcntl = None  # type: ignore[assignment]

try:  # Windows advisory locks
    import msvcrt
except ImportError:  # pragma: no cover - exercised on POSIX
    msvcrt = None  # type: ignore[assignment]

from .errors import InputError
from .production_models import (
    RECORD_SCHEMA_VERSION,
    BatchStatus,
    FrozenBatchPlan,
    FrozenTrackPlan,
    LedgerEvent,
    StrictRecordCodec,
    TransactionState,
    canonical_json_bytes,
    canonical_sha256,
    seal_record,
)
from .util import (
    _open_directory_fd,
    atomic_write_bytes,
    durable_mkdir,
    durable_replace,
    fsync_directory,
    read_bytes_nofollow,
    sha256_bytes,
    utc_now,
)

LedgerScalar: TypeAlias = str | int | bool | None

_ID_PATTERN = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
_FIELD_PATTERN = re.compile(r"^[a-z][a-z0-9_.-]*$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_UTC_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$")
_EVENT_FILE_PATTERN = re.compile(
    r"^(?P<sequence>\d{6})-(?P<event_type>[a-z0-9]+(?:-[a-z0-9]+)*)\.json$"
)

_EARLY_STATES = frozenset(
    {
        TransactionState.DISCOVERED,
        TransactionState.PLANNED,
        TransactionState.PREFLIGHT_PASSED,
        TransactionState.AUTHORIZATION_REQUIRED,
    }
)
_BLOCKING_STATES = frozenset(
    {TransactionState.BLOCKED, TransactionState.CHARGE_UNCERTAIN}
)
_PROGRESS_STATES = frozenset(
    {
        TransactionState.RUNNING,
        TransactionState.RENDERED,
        TransactionState.VALIDATED,
        TransactionState.DELIVERED,
    }
)

# A blocked transaction is terminal.  The documented blocked -> planned recovery
# is represented by a new immutable plan and transaction, never by reusing a ledger.
ALLOWED_TRANSITIONS: Mapping[TransactionState, frozenset[TransactionState]] = MappingProxyType(
    {
        TransactionState.DISCOVERED: frozenset({TransactionState.PLANNED}),
        TransactionState.PLANNED: frozenset(
            {TransactionState.PREFLIGHT_PASSED, TransactionState.BLOCKED}
        ),
        TransactionState.PREFLIGHT_PASSED: frozenset(
            {TransactionState.AUTHORIZATION_REQUIRED}
        ),
        TransactionState.AUTHORIZATION_REQUIRED: frozenset(
            {TransactionState.RUNNING, TransactionState.BLOCKED}
        ),
        TransactionState.RUNNING: frozenset(
            {
                TransactionState.RENDERED,
                TransactionState.CHARGE_UNCERTAIN,
                TransactionState.BLOCKED,
            }
        ),
        TransactionState.CHARGE_UNCERTAIN: frozenset(
            {TransactionState.RENDERED, TransactionState.BLOCKED}
        ),
        TransactionState.RENDERED: frozenset(
            {TransactionState.VALIDATED, TransactionState.BLOCKED}
        ),
        TransactionState.VALIDATED: frozenset(
            {TransactionState.DELIVERED, TransactionState.BLOCKED}
        ),
        TransactionState.DELIVERED: frozenset(),
        TransactionState.BLOCKED: frozenset(),
    }
)


class TransactionHealth(StrEnum):
    """Whether a selected transaction has independently usable truth."""

    VALID = "valid"
    MISSING = "missing"
    CORRUPT = "corrupt"


class StatusCacheDisposition(StrEnum):
    """How a status read treated the non-authoritative global cache."""

    CURRENT = "current"
    MISSING_REBUILT = "missing-rebuilt"
    STALE_REBUILT = "stale-rebuilt"
    CORRUPT_REBUILT = "corrupt-rebuilt"


class TransactionLockUnavailable(InputError):
    """A cooperating writer already owns the book/Track mutation lock."""


class TransactionCorruption(InputError):
    """One transaction cannot be reduced without weakening its evidence."""

    def __init__(self, category: str, message: str):
        super().__init__(message)
        self.category = category


def _require_identifier(value: object, label: str) -> str:
    if not isinstance(value, str) or not _ID_PATTERN.fullmatch(value):
        raise InputError(f"{label} must be a lowercase hyphenated identifier")
    return value


def _require_field_name(value: object, label: str) -> str:
    if not isinstance(value, str) or not _FIELD_PATTERN.fullmatch(value):
        raise InputError(f"{label} must be a canonical field identifier")
    return value


def _require_sha256(value: object, label: str, *, allow_empty: bool = False) -> str:
    if allow_empty and value == "":
        return ""
    if not isinstance(value, str) or not _SHA256_PATTERN.fullmatch(value):
        raise InputError(f"{label} must be a lowercase SHA-256 digest")
    return value


def _require_utc(value: object, label: str) -> str:
    if not isinstance(value, str) or not _UTC_PATTERN.fullmatch(value):
        raise InputError(f"{label} must be an ISO-8601 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value.removesuffix("Z") + "+00:00")
    except ValueError as exc:
        raise InputError(f"{label} is not a valid UTC timestamp") from exc
    if parsed.utcoffset() is None or parsed.utcoffset().total_seconds() != 0:
        raise InputError(f"{label} must be UTC")
    return value


def _parse_utc(value: str) -> datetime:
    return datetime.fromisoformat(value.removesuffix("Z") + "+00:00")


def _require_relative_path(value: object, label: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise InputError(f"{label} must be a workspace-relative POSIX path")
    candidate = PurePosixPath(value)
    if (
        candidate.is_absolute()
        or value == "."
        or candidate.as_posix() != value
        or any(part in {"", ".", ".."} for part in candidate.parts)
    ):
        raise InputError(f"{label} must be a canonical traversal-free relative path")
    return value


def _freeze_details(
    value: Mapping[str, LedgerScalar], label: str = "ledger payload details"
) -> Mapping[str, LedgerScalar]:
    if not isinstance(value, Mapping):
        raise InputError(f"{label} must be a mapping")
    result: dict[str, LedgerScalar] = {}
    for key, item in value.items():
        checked_key = _require_field_name(key, f"{label} key")
        if item is not None and type(item) not in {str, int, bool}:
            raise InputError(f"{label}[{checked_key!r}] must be a JSON scalar")
        if isinstance(item, str) and (not item or item != item.strip() or "\x00" in item):
            raise InputError(f"{label}[{checked_key!r}] must be a canonical string")
        result[checked_key] = item
    return MappingProxyType(result)


@dataclass(frozen=True, slots=True)
class TransactionSpec:
    """The immutable plan facts needed to materialize one Track transaction."""

    book_id: str
    plan_id: str
    plan_sha256: str
    transaction_id: str
    track_id: str
    sequence: int
    track_plan_sha256: str

    def __post_init__(self) -> None:
        for name in ("book_id", "plan_id", "transaction_id", "track_id"):
            _require_identifier(getattr(self, name), f"transaction spec {name}")
        _require_sha256(self.plan_sha256, "transaction spec plan_sha256")
        _require_sha256(self.track_plan_sha256, "transaction spec track_plan_sha256")
        if type(self.sequence) is not int or self.sequence < 1:
            raise InputError("transaction spec sequence must be an integer >= 1")

    @classmethod
    def from_plan(
        cls, plan: FrozenBatchPlan, track: FrozenTrackPlan | str
    ) -> TransactionSpec:
        """Bind a transaction spec to a digest-valid frozen plan and Track plan."""

        StrictRecordCodec(FrozenBatchPlan).dump_bytes(plan)
        if isinstance(track, str):
            matches = tuple(item for item in plan.tracks if item.track_id == track)
            if len(matches) != 1:
                raise InputError(f"Frozen plan does not contain exactly one Track {track!r}")
            selected = matches[0]
        elif isinstance(track, FrozenTrackPlan) and track in plan.tracks:
            selected = track
        else:
            raise InputError("Track plan does not belong to the frozen plan")
        return cls(
            book_id=plan.book_id,
            plan_id=plan.plan_id,
            plan_sha256=plan.canonical_sha256,
            transaction_id=selected.transaction_id,
            track_id=selected.track_id,
            sequence=selected.sequence,
            track_plan_sha256=canonical_sha256(selected),
        )


@dataclass(frozen=True, slots=True)
class TransactionMetadata:
    """Immutable identity record at the root of one independent transaction."""

    schema_version: int
    book_id: str
    plan_id: str
    plan_sha256: str
    transaction_id: str
    track_id: str
    sequence: int
    track_plan_sha256: str
    created_at_utc: str
    canonical_sha256: str

    SCHEMA_VERSION: ClassVar[int] = RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != RECORD_SCHEMA_VERSION:
            raise InputError(
                f"transaction metadata schema_version must be integer {RECORD_SCHEMA_VERSION}"
            )
        for name in ("book_id", "plan_id", "transaction_id", "track_id"):
            _require_identifier(getattr(self, name), f"transaction metadata {name}")
        _require_sha256(self.plan_sha256, "transaction metadata plan_sha256")
        _require_sha256(self.track_plan_sha256, "transaction metadata track_plan_sha256")
        if type(self.sequence) is not int or self.sequence < 1:
            raise InputError("transaction metadata sequence must be an integer >= 1")
        _require_utc(self.created_at_utc, "transaction metadata created_at_utc")
        _require_sha256(
            self.canonical_sha256,
            "transaction metadata canonical_sha256",
            allow_empty=True,
        )

    def matches(self, spec: TransactionSpec) -> bool:
        return (
            self.book_id == spec.book_id
            and self.plan_id == spec.plan_id
            and self.plan_sha256 == spec.plan_sha256
            and self.transaction_id == spec.transaction_id
            and self.track_id == spec.track_id
            and self.sequence == spec.sequence
            and self.track_plan_sha256 == spec.track_plan_sha256
        )


@dataclass(frozen=True, slots=True)
class LedgerPayload:
    """Sanitized immutable payload bound by one ledger event digest."""

    schema_version: int
    transaction_id: str
    operation_id: str
    event_type: str
    state_after: TransactionState
    details: Mapping[str, LedgerScalar]

    SCHEMA_VERSION: ClassVar[int] = RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != RECORD_SCHEMA_VERSION:
            raise InputError(
                f"ledger payload schema_version must be integer {RECORD_SCHEMA_VERSION}"
            )
        _require_identifier(self.transaction_id, "ledger payload transaction_id")
        _require_identifier(self.operation_id, "ledger payload operation_id")
        _require_identifier(self.event_type, "ledger payload event_type")
        if not isinstance(self.state_after, TransactionState):
            raise InputError("ledger payload state_after must be a TransactionState")
        object.__setattr__(self, "details", _freeze_details(self.details))


@dataclass(frozen=True, slots=True)
class TransactionSnapshot:
    """Reduced transaction truth; runtime/audio directories are never inspected."""

    metadata: TransactionMetadata
    state: TransactionState
    events: tuple[LedgerEvent, ...]
    payloads: tuple[LedgerPayload, ...]

    def __post_init__(self) -> None:
        if not self.events or len(self.events) != len(self.payloads):
            raise InputError("transaction snapshot events and payloads must be nonempty and aligned")
        if self.state is not self.events[-1].state_after:
            raise InputError("transaction snapshot state must equal the ledger head state")

    @property
    def head_event_sha256(self) -> str:
        return self.events[-1].event_sha256


@dataclass(frozen=True, slots=True)
class TransactionStatus:
    """One transaction's independently reconstructed status."""

    book_id: str
    plan_id: str
    plan_sha256: str
    transaction_id: str
    track_id: str
    sequence: int
    transaction_path: str
    health: TransactionHealth
    state: TransactionState | None
    event_count: int
    head_event_sha256: str | None
    corruption_category: str | None

    def __post_init__(self) -> None:
        for name in ("book_id", "plan_id", "transaction_id", "track_id"):
            _require_identifier(getattr(self, name), f"transaction status {name}")
        _require_sha256(self.plan_sha256, "transaction status plan_sha256")
        if type(self.sequence) is not int or self.sequence < 1:
            raise InputError("transaction status sequence must be an integer >= 1")
        _require_relative_path(self.transaction_path, "transaction status transaction_path")
        if not isinstance(self.health, TransactionHealth):
            raise InputError("transaction status health must be a TransactionHealth")
        if type(self.event_count) is not int or self.event_count < 0:
            raise InputError("transaction status event_count must be an integer >= 0")
        if self.health is TransactionHealth.VALID:
            if not isinstance(self.state, TransactionState) or self.event_count < 1:
                raise InputError("valid transaction status requires reduced state and events")
            _require_sha256(
                self.head_event_sha256, "transaction status head_event_sha256"
            )
            if self.corruption_category is not None:
                raise InputError("valid transaction status cannot contain corruption")
        elif self.health is TransactionHealth.MISSING:
            if (
                self.state is not None
                or self.event_count != 0
                or self.head_event_sha256 is not None
                or self.corruption_category is not None
            ):
                raise InputError("missing transaction status cannot contain ledger evidence")
        else:
            if self.state is not None or self.head_event_sha256 is not None:
                raise InputError("corrupt transaction status cannot assert ledger truth")
            _require_field_name(
                self.corruption_category, "transaction status corruption_category"
            )


@dataclass(frozen=True, slots=True)
class PlanStatus:
    """Derived status for every selected transaction in one plan/batch."""

    plan_id: str
    plan_sha256: str
    status: BatchStatus
    tracks: tuple[TransactionStatus, ...]
    selected_count: int
    completed_count: int
    blocked_count: int
    unstarted_count: int

    def __post_init__(self) -> None:
        _require_identifier(self.plan_id, "plan status plan_id")
        _require_sha256(self.plan_sha256, "plan status plan_sha256")
        if not isinstance(self.status, BatchStatus):
            raise InputError("plan status status must be a BatchStatus")
        if not isinstance(self.tracks, tuple):
            raise InputError("plan status tracks must be a tuple")
        if any(
            item.plan_id != self.plan_id or item.plan_sha256 != self.plan_sha256
            for item in self.tracks
        ):
            raise InputError("plan status Track scope must match its plan binding")
        if tuple(item.sequence for item in self.tracks) != tuple(
            sorted(item.sequence for item in self.tracks)
        ):
            raise InputError("plan status Tracks must be in sequence order")
        for name in (
            "selected_count",
            "completed_count",
            "blocked_count",
            "unstarted_count",
        ):
            value = getattr(self, name)
            if type(value) is not int or value < 0:
                raise InputError(f"plan status {name} must be an integer >= 0")
        if self.selected_count != len(self.tracks):
            raise InputError("plan status selected_count must equal Track count")
        if self.completed_count + self.blocked_count + self.unstarted_count > len(
            self.tracks
        ):
            raise InputError("plan status counts cannot exceed selected_count")


@dataclass(frozen=True, slots=True)
class CorruptTransactionPath:
    """A malformed path that cannot safely supply transaction identity."""

    path: str
    category: str

    def __post_init__(self) -> None:
        _require_relative_path(self.path, "corrupt transaction path")
        _require_field_name(self.category, "corrupt transaction category")


@dataclass(frozen=True, slots=True)
class DerivedStatusIndex:
    """Canonical cache reconstructed from independent transaction directories."""

    schema_version: int
    book_id: str
    rebuilt_at_utc: str
    transactions: tuple[TransactionStatus, ...]
    plans: tuple[PlanStatus, ...]
    corrupt_paths: tuple[CorruptTransactionPath, ...]
    source_fingerprint: str
    canonical_sha256: str

    SCHEMA_VERSION: ClassVar[int] = RECORD_SCHEMA_VERSION

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != RECORD_SCHEMA_VERSION:
            raise InputError(
                f"derived status schema_version must be integer {RECORD_SCHEMA_VERSION}"
            )
        _require_identifier(self.book_id, "derived status book_id")
        _require_utc(self.rebuilt_at_utc, "derived status rebuilt_at_utc")
        if not isinstance(self.transactions, tuple) or not all(
            isinstance(item, TransactionStatus) for item in self.transactions
        ):
            raise InputError("derived status transactions must contain TransactionStatus values")
        if not isinstance(self.plans, tuple) or not all(
            isinstance(item, PlanStatus) for item in self.plans
        ):
            raise InputError("derived status plans must contain PlanStatus values")
        if not isinstance(self.corrupt_paths, tuple) or not all(
            isinstance(item, CorruptTransactionPath) for item in self.corrupt_paths
        ):
            raise InputError(
                "derived status corrupt_paths must contain CorruptTransactionPath values"
            )
        transaction_order = tuple(
            (item.plan_id, item.sequence, item.track_id, item.transaction_id)
            for item in self.transactions
        )
        if transaction_order != tuple(sorted(transaction_order)):
            raise InputError("derived status transactions must be in canonical order")
        plan_order = tuple((item.plan_id, item.plan_sha256) for item in self.plans)
        if plan_order != tuple(sorted(plan_order)):
            raise InputError("derived status plans must be in canonical order")
        corrupt_order = tuple((item.path, item.category) for item in self.corrupt_paths)
        if corrupt_order != tuple(sorted(corrupt_order)):
            raise InputError("derived status corrupt paths must be in canonical order")
        expected_fingerprint = _status_source_fingerprint(
            self.book_id, self.transactions, self.plans, self.corrupt_paths
        )
        if self.source_fingerprint != expected_fingerprint:
            raise InputError("derived status source_fingerprint does not match status content")
        _require_sha256(
            self.canonical_sha256,
            "derived status canonical_sha256",
            allow_empty=True,
        )


@dataclass(frozen=True, slots=True)
class StatusReadResult:
    """Status plus an explicit report of cache repair/currentness."""

    index: DerivedStatusIndex
    cache_disposition: StatusCacheDisposition
    cache_path: str

    def __post_init__(self) -> None:
        if not isinstance(self.index, DerivedStatusIndex):
            raise InputError("status result index must be a DerivedStatusIndex")
        if not isinstance(self.cache_disposition, StatusCacheDisposition):
            raise InputError("status result cache_disposition is invalid")
        _require_relative_path(self.cache_path, "status result cache_path")


_LOCAL_LOCKS_GUARD = threading.Lock()
_LOCAL_LOCKS: dict[str, threading.Lock] = {}


@contextmanager
def _nonblocking_file_lock(path: Path) -> Iterator[None]:
    """Acquire a local and process lock without waiting for another writer."""

    absolute = Path(os.path.abspath(os.fspath(path.expanduser())))
    durable_mkdir(absolute.parent)
    key = str(absolute)
    with _LOCAL_LOCKS_GUARD:
        local_lock = _LOCAL_LOCKS.setdefault(key, threading.Lock())
    if not local_lock.acquire(blocking=False):
        raise TransactionLockUnavailable(f"Transaction lock is already held: {path}")

    handle = None
    process_locked = False
    try:
        if os.name == "posix":
            parent_fd = _open_directory_fd(absolute.parent)
            try:
                flags = (
                    os.O_RDWR
                    | os.O_CREAT
                    | getattr(os, "O_NOFOLLOW", 0)
                    | getattr(os, "O_CLOEXEC", 0)
                )
                descriptor = os.open(absolute.name, flags, 0o600, dir_fd=parent_fd)
                os.fsync(parent_fd)
            finally:
                os.close(parent_fd)
            handle = os.fdopen(descriptor, "a+b")
        else:  # pragma: no cover - Windows offline support
            handle = absolute.open("a+b")

        if fcntl is not None:
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise TransactionLockUnavailable(
                    f"Transaction lock is already held: {path}"
                ) from exc
            process_locked = True
        elif msvcrt is not None:  # pragma: no cover - Windows
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
                os.fsync(handle.fileno())
            handle.seek(0)
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            except OSError as exc:
                if exc.errno in {errno.EACCES, errno.EAGAIN, errno.EDEADLK}:
                    raise TransactionLockUnavailable(
                        f"Transaction lock is already held: {path}"
                    ) from exc
                raise
            process_locked = True
        else:  # pragma: no cover - unsupported interpreter platform
            raise InputError("No supported cross-process file-lock API is available")

        yield
    except OSError as exc:
        raise InputError(f"Cannot acquire transaction lock {path}: {exc}") from exc
    finally:
        if handle is not None:
            if process_locked and fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            elif process_locked and msvcrt is not None:  # pragma: no cover - Windows
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            handle.close()
        local_lock.release()


def _write_exclusive_atomic(path: Path, content: bytes) -> None:
    """Publish one immutable file atomically without replacing existing evidence."""

    durable_mkdir(path.parent)
    temporary = path.parent / f".{path.name}.{secrets.token_hex(12)}.tmp"
    if os.name == "posix":
        parent_fd = _open_directory_fd(path.parent)
        descriptor: int | None = None
        try:
            flags = (
                os.O_WRONLY
                | os.O_CREAT
                | os.O_EXCL
                | getattr(os, "O_NOFOLLOW", 0)
                | getattr(os, "O_CLOEXEC", 0)
            )
            descriptor = os.open(temporary.name, flags, 0o600, dir_fd=parent_fd)
            with os.fdopen(descriptor, "wb") as handle:
                descriptor = None
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.fsync(parent_fd)
        finally:
            if descriptor is not None:
                os.close(descriptor)
            os.close(parent_fd)
    else:  # pragma: no cover - Windows offline support
        with temporary.open("xb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
    durable_replace(temporary, path, source_kind="file")


def _write_immutable_or_verify(path: Path, content: bytes) -> None:
    if os.path.lexists(path):
        if path.is_symlink() or not path.is_file():
            raise TransactionCorruption(
                "immutable-path-invalid", f"Immutable record path is unsafe: {path}"
            )
        if read_bytes_nofollow(path) != content:
            raise TransactionCorruption(
                "immutable-collision", f"Immutable record collision at {path}"
            )
        return
    try:
        _write_exclusive_atomic(path, content)
    except InputError:
        # A cooperating race can only be accepted if it published identical bytes.
        if os.path.lexists(path) and not path.is_symlink() and path.is_file():
            if read_bytes_nofollow(path) == content:
                return
        raise


def _event_file_name(sequence: int, event_type: str) -> str:
    if sequence > 999_999:
        raise InputError("Transaction ledger exceeds the supported sequence bound")
    return f"{sequence:06d}-{event_type}.json"


def _validate_transition(
    state_before: TransactionState | None, state_after: TransactionState
) -> None:
    if state_before is None:
        if state_after is not TransactionState.DISCOVERED:
            raise InputError("A transaction ledger must begin in discovered state")
        return
    if state_after not in ALLOWED_TRANSITIONS[state_before]:
        raise InputError(
            f"Invalid transaction transition: {state_before.value} -> {state_after.value}"
        )


def reduce_ledger_events(
    events: Sequence[LedgerEvent], *, transaction_id: str | None = None
) -> TransactionState:
    """Strictly reduce a canonical event sequence to one authoritative state."""

    if not events:
        raise TransactionCorruption("event-chain-invalid", "Transaction ledger is empty")
    expected_transaction = transaction_id or events[0].transaction_id
    _require_identifier(expected_transaction, "ledger transaction_id")
    previous_hash: str | None = None
    previous_state: TransactionState | None = None
    previous_time: datetime | None = None
    seen_sequences: set[int] = set()

    for expected_sequence, event in enumerate(events, start=1):
        try:
            StrictRecordCodec(LedgerEvent).dump_bytes(event)
        except InputError as exc:
            raise TransactionCorruption(
                "event-chain-invalid", "Ledger event digest or schema is invalid"
            ) from exc
        if event.transaction_id != expected_transaction:
            raise TransactionCorruption(
                "event-chain-invalid", "Ledger event transaction identity changed"
            )
        if event.sequence in seen_sequences or event.sequence != expected_sequence:
            raise TransactionCorruption(
                "event-chain-invalid", "Ledger sequence is duplicate, missing, or reordered"
            )
        if event.previous_event_sha256 != previous_hash:
            raise TransactionCorruption(
                "event-chain-invalid", "Ledger previous-event digest is broken"
            )
        if event.state_before is not previous_state:
            raise TransactionCorruption(
                "event-chain-invalid", "Ledger state_before does not match reduced state"
            )
        try:
            _validate_transition(previous_state, event.state_after)
        except InputError as exc:
            raise TransactionCorruption(
                "event-chain-invalid", "Ledger contains an invalid state transition"
            ) from exc
        occurred = _parse_utc(event.occurred_at_utc)
        if previous_time is not None and occurred < previous_time:
            raise TransactionCorruption(
                "event-chain-invalid", "Ledger timestamps move backwards"
            )
        seen_sequences.add(event.sequence)
        previous_hash = event.event_sha256
        previous_state = event.state_after
        previous_time = occurred

    assert previous_state is not None
    return previous_state


def _status_source_fingerprint(
    book_id: str,
    transactions: tuple[TransactionStatus, ...],
    plans: tuple[PlanStatus, ...],
    corrupt_paths: tuple[CorruptTransactionPath, ...],
) -> str:
    return canonical_sha256(
        {
            "schema": "frontier-derived-status-source-v1",
            "book_id": book_id,
            "transactions": transactions,
            "plans": plans,
            "corrupt_paths": corrupt_paths,
        }
    )


def _derive_batch_status(tracks: Sequence[TransactionStatus]) -> BatchStatus:
    if not tracks:
        return BatchStatus.NOT_STARTED
    valid_states = tuple(
        item.state
        for item in tracks
        if item.health is TransactionHealth.VALID and item.state is not None
    )
    completed = sum(state is TransactionState.DELIVERED for state in valid_states)
    blocked = sum(
        item.health is TransactionHealth.CORRUPT
        or (
            item.health is TransactionHealth.VALID
            and item.state in _BLOCKING_STATES
        )
        for item in tracks
    )
    progressed = any(state in _PROGRESS_STATES for state in valid_states)
    running = any(state is TransactionState.RUNNING for state in valid_states)

    if completed == len(tracks):
        return BatchStatus.COMPLETE
    if blocked:
        return BatchStatus.PARTIAL if completed or progressed else BatchStatus.BLOCKED
    if completed or any(
        state in {TransactionState.RENDERED, TransactionState.VALIDATED}
        for state in valid_states
    ):
        return BatchStatus.PARTIAL
    if running:
        return BatchStatus.RUNNING
    return BatchStatus.NOT_STARTED


def _make_plan_status(
    plan_id: str, plan_sha256: str, tracks: Sequence[TransactionStatus]
) -> PlanStatus:
    ordered = tuple(
        sorted(tracks, key=lambda item: (item.sequence, item.track_id, item.transaction_id))
    )
    completed = sum(
        item.health is TransactionHealth.VALID
        and item.state is TransactionState.DELIVERED
        for item in ordered
    )
    blocked = sum(
        item.health is TransactionHealth.CORRUPT
        or (
            item.health is TransactionHealth.VALID
            and item.state in _BLOCKING_STATES
        )
        for item in ordered
    )
    unstarted = sum(
        item.health is TransactionHealth.MISSING
        or (
            item.health is TransactionHealth.VALID and item.state in _EARLY_STATES
        )
        for item in ordered
    )
    return PlanStatus(
        plan_id=plan_id,
        plan_sha256=plan_sha256,
        status=_derive_batch_status(ordered),
        tracks=ordered,
        selected_count=len(ordered),
        completed_count=completed,
        blocked_count=blocked,
        unstarted_count=unstarted,
    )


class TransactionStore:
    """Own independent Track transaction roots for one configured book."""

    def __init__(self, book_root: Path, book_id: str):
        self.book_root = Path(os.path.abspath(os.fspath(book_root.expanduser())))
        self.book_id = _require_identifier(book_id, "transaction store book_id")
        self.transactions_root = self.book_root / "transactions"
        self.locks_root = self.book_root / "locks" / self.book_id
        self.index_path = self.book_root / "indexes" / "status.json"

    def _relative(self, path: Path) -> str:
        try:
            return path.relative_to(self.book_root).as_posix()
        except ValueError as exc:
            raise InputError(f"Path is outside the transaction book root: {path}") from exc

    def transaction_path(self, track_id: str, transaction_id: str) -> Path:
        checked_track = _require_identifier(track_id, "track_id")
        checked_transaction = _require_identifier(transaction_id, "transaction_id")
        return self.transactions_root / checked_track / checked_transaction

    @contextmanager
    def book_lock(self) -> Iterator[None]:
        """Acquire the exclusive book-level mutation lock without blocking.

        Paid batch coordination holds this lock for the complete sequential run,
        while each attempt continues to use its independent Track lock.  The
        private filename cannot collide with a valid Track identifier.
        """

        with _nonblocking_file_lock(self.locks_root / ".book.lock"):
            yield

    @contextmanager
    def track_lock(self, track_id: str) -> Iterator[None]:
        """Acquire the exclusive book/Track lock without blocking another writer."""

        checked_track = _require_identifier(track_id, "track_id")
        with _nonblocking_file_lock(self.locks_root / f"{checked_track}.lock"):
            yield

    def _load_metadata(self, transaction_root: Path) -> TransactionMetadata:
        if (
            not os.path.lexists(transaction_root)
            or transaction_root.is_symlink()
            or not transaction_root.is_dir()
        ):
            raise TransactionCorruption(
                "metadata-invalid", f"Transaction root is missing or unsafe: {transaction_root}"
            )
        try:
            metadata = StrictRecordCodec(TransactionMetadata).load(
                transaction_root / "transaction.json"
            )
        except InputError as exc:
            raise TransactionCorruption(
                "metadata-invalid", "Transaction metadata is missing or malformed"
            ) from exc
        if metadata.book_id != self.book_id:
            raise TransactionCorruption(
                "metadata-invalid", "Transaction metadata book identity does not match store"
            )
        if (
            transaction_root.parent.name != metadata.track_id
            or transaction_root.name != metadata.transaction_id
        ):
            raise TransactionCorruption(
                "metadata-invalid", "Transaction metadata does not match its path"
            )
        return metadata

    def _read_chain(
        self, transaction_root: Path, metadata: TransactionMetadata
    ) -> TransactionSnapshot:
        events_root = transaction_root / "events"
        payloads_root = transaction_root / "payloads"
        if (
            events_root.is_symlink()
            or payloads_root.is_symlink()
            or not events_root.is_dir()
            or not payloads_root.is_dir()
        ):
            raise TransactionCorruption(
                "event-chain-invalid", "Transaction event or payload directory is unsafe"
            )
        try:
            event_paths = sorted(events_root.iterdir(), key=lambda item: item.name)
        except OSError as exc:
            raise TransactionCorruption(
                "event-chain-invalid", "Transaction events cannot be listed"
            ) from exc
        if not event_paths:
            raise TransactionCorruption("event-chain-invalid", "Transaction ledger is empty")

        events: list[LedgerEvent] = []
        for path in event_paths:
            match = _EVENT_FILE_PATTERN.fullmatch(path.name)
            if match is None or path.is_symlink() or not path.is_file():
                raise TransactionCorruption(
                    "event-chain-invalid", "Transaction event directory is ambiguous"
                )
            try:
                event = StrictRecordCodec(LedgerEvent).load(path)
            except InputError as exc:
                raise TransactionCorruption(
                    "event-chain-invalid", "Transaction event is malformed"
                ) from exc
            if (
                event.sequence != int(match.group("sequence"))
                or event.event_type != match.group("event_type")
            ):
                raise TransactionCorruption(
                    "event-chain-invalid", "Transaction event filename binding is invalid"
                )
            events.append(event)

        state = reduce_ledger_events(events, transaction_id=metadata.transaction_id)
        payloads: list[LedgerPayload] = []
        seen_operations: set[str] = set()
        for event in events:
            payload_path = payloads_root / f"{event.payload_sha256}.json"
            try:
                raw = read_bytes_nofollow(payload_path)
            except InputError as exc:
                raise TransactionCorruption(
                    "payload-invalid", "A bound transaction payload is missing or unsafe"
                ) from exc
            if sha256_bytes(raw) != event.payload_sha256:
                raise TransactionCorruption(
                    "payload-invalid", "A bound transaction payload digest is invalid"
                )
            try:
                payload = StrictRecordCodec(LedgerPayload).loads(
                    raw, label=str(payload_path)
                )
            except InputError as exc:
                raise TransactionCorruption(
                    "payload-invalid", "A bound transaction payload is malformed"
                ) from exc
            if (
                payload.transaction_id != metadata.transaction_id
                or payload.event_type != event.event_type
                or payload.state_after is not event.state_after
            ):
                raise TransactionCorruption(
                    "payload-invalid", "A transaction payload does not match its event"
                )
            if payload.operation_id in seen_operations:
                raise TransactionCorruption(
                    "payload-invalid", "Transaction operation IDs must be unique"
                )
            seen_operations.add(payload.operation_id)
            payloads.append(payload)

        return TransactionSnapshot(metadata, state, tuple(events), tuple(payloads))

    def inspect_transaction(
        self, track_id: str, transaction_id: str
    ) -> TransactionSnapshot:
        """Reduce metadata and ledger evidence without traversing runtime/audio files."""

        root = self.transaction_path(track_id, transaction_id)
        metadata = self._load_metadata(root)
        return self._read_chain(root, metadata)

    def _commit_event(
        self,
        transaction_root: Path,
        metadata: TransactionMetadata,
        events: Sequence[LedgerEvent],
        *,
        operation_id: str,
        event_type: str,
        state_after: TransactionState,
        details: Mapping[str, LedgerScalar],
        occurred_at_utc: str,
    ) -> LedgerEvent:
        checked_operation = _require_identifier(operation_id, "ledger operation_id")
        checked_event_type = _require_identifier(event_type, "ledger event_type")
        checked_time = _require_utc(occurred_at_utc, "ledger occurred_at_utc")
        frozen_details = _freeze_details(details)
        state_before = events[-1].state_after if events else None
        _validate_transition(state_before, state_after)
        if events and _parse_utc(checked_time) < _parse_utc(events[-1].occurred_at_utc):
            raise InputError("Ledger event timestamp cannot precede the current ledger head")

        payload = LedgerPayload(
            schema_version=RECORD_SCHEMA_VERSION,
            transaction_id=metadata.transaction_id,
            operation_id=checked_operation,
            event_type=checked_event_type,
            state_after=state_after,
            details=frozen_details,
        )
        payload_bytes = StrictRecordCodec(LedgerPayload).dump_bytes(payload)
        payload_sha256 = sha256_bytes(payload_bytes)
        payload_path = transaction_root / "payloads" / f"{payload_sha256}.json"
        _write_immutable_or_verify(payload_path, payload_bytes)

        sequence = len(events) + 1
        event = seal_record(
            LedgerEvent(
                schema_version=RECORD_SCHEMA_VERSION,
                transaction_id=metadata.transaction_id,
                sequence=sequence,
                event_type=checked_event_type,
                state_before=state_before,
                state_after=state_after,
                occurred_at_utc=checked_time,
                payload_sha256=payload_sha256,
                previous_event_sha256=(events[-1].event_sha256 if events else None),
                event_sha256="",
            )
        )
        event_path = transaction_root / "events" / _event_file_name(
            sequence, checked_event_type
        )
        _write_exclusive_atomic(
            event_path, StrictRecordCodec(LedgerEvent).dump_bytes(event)
        )
        fsync_directory(transaction_root / "payloads")
        fsync_directory(transaction_root / "events")
        fsync_directory(transaction_root)
        return event

    def materialize_transaction(
        self,
        spec: TransactionSpec,
        *,
        occurred_at_utc: str | None = None,
    ) -> TransactionSnapshot:
        """Atomically create one independent planned transaction, idempotently."""

        if spec.book_id != self.book_id:
            raise InputError("Transaction spec book_id does not match the transaction store")
        timestamp = occurred_at_utc or utc_now()
        _require_utc(timestamp, "transaction materialization timestamp")
        final_root = self.transaction_path(spec.track_id, spec.transaction_id)

        with self.track_lock(spec.track_id):
            if os.path.lexists(final_root):
                snapshot = self.inspect_transaction(spec.track_id, spec.transaction_id)
                if not snapshot.metadata.matches(spec):
                    raise InputError(
                        "Existing transaction identity differs from the requested Track plan"
                    )
                return snapshot

            track_root = final_root.parent
            durable_mkdir(track_root)
            staging_prefix = f".{spec.transaction_id}.staging-"
            for entry in track_root.iterdir():
                if entry.name.startswith(staging_prefix):
                    raise TransactionCorruption(
                        "incomplete-transaction-staging",
                        "An incomplete transaction staging directory requires inspection",
                    )
            staging = track_root / f"{staging_prefix}{secrets.token_hex(8)}"
            try:
                staging.mkdir(mode=0o700)
                fsync_directory(track_root)
                durable_mkdir(staging / "events")
                durable_mkdir(staging / "payloads")
                metadata = seal_record(
                    TransactionMetadata(
                        schema_version=RECORD_SCHEMA_VERSION,
                        book_id=spec.book_id,
                        plan_id=spec.plan_id,
                        plan_sha256=spec.plan_sha256,
                        transaction_id=spec.transaction_id,
                        track_id=spec.track_id,
                        sequence=spec.sequence,
                        track_plan_sha256=spec.track_plan_sha256,
                        created_at_utc=timestamp,
                        canonical_sha256="",
                    )
                )
                _write_exclusive_atomic(
                    staging / "transaction.json",
                    StrictRecordCodec(TransactionMetadata).dump_bytes(metadata),
                )
                discovered = self._commit_event(
                    staging,
                    metadata,
                    (),
                    operation_id="materialize-discovered",
                    event_type="track-discovered",
                    state_after=TransactionState.DISCOVERED,
                    details={
                        "plan_sha256": spec.plan_sha256,
                        "track_plan_sha256": spec.track_plan_sha256,
                    },
                    occurred_at_utc=timestamp,
                )
                self._commit_event(
                    staging,
                    metadata,
                    (discovered,),
                    operation_id="materialize-planned",
                    event_type="track-planned",
                    state_after=TransactionState.PLANNED,
                    details={
                        "plan_sha256": spec.plan_sha256,
                        "track_plan_sha256": spec.track_plan_sha256,
                    },
                    occurred_at_utc=timestamp,
                )
                fsync_directory(staging)
                durable_replace(staging, final_root, source_kind="directory")
            except BaseException:
                # Retain incomplete staging evidence.  A later mutation fails closed
                # rather than deleting or guessing about an interrupted commit.
                raise

            return self.inspect_transaction(spec.track_id, spec.transaction_id)

    def materialize_plan(
        self,
        plan: FrozenBatchPlan,
        *,
        occurred_at_utc: str | None = None,
    ) -> tuple[TransactionSnapshot, ...]:
        """Materialize one independent transaction for every Track in plan order."""

        StrictRecordCodec(FrozenBatchPlan).dump_bytes(plan)
        if plan.book_id != self.book_id:
            raise InputError("Frozen plan book_id does not match the transaction store")
        return tuple(
            self.materialize_transaction(
                TransactionSpec.from_plan(plan, track),
                occurred_at_utc=occurred_at_utc,
            )
            for track in plan.tracks
        )

    def append_transition(
        self,
        track_id: str,
        transaction_id: str,
        *,
        operation_id: str,
        event_type: str,
        state_after: TransactionState,
        details: Mapping[str, LedgerScalar],
        occurred_at_utc: str | None = None,
    ) -> LedgerEvent:
        """Append one local transition or return its prior identical result.

        ``operation_id`` is unique within the transaction.  Repeating the same
        operation with unchanged event type, state, and details returns the original
        event without writing another sequence.  Reusing the key for different input
        is an immutable idempotency collision.
        """

        checked_track = _require_identifier(track_id, "track_id")
        checked_transaction = _require_identifier(transaction_id, "transaction_id")
        checked_operation = _require_identifier(operation_id, "operation_id")
        checked_event_type = _require_identifier(event_type, "event_type")
        if not isinstance(state_after, TransactionState):
            raise InputError("state_after must be a TransactionState")
        requested_details = _freeze_details(details)

        with self.track_lock(checked_track):
            snapshot = self.inspect_transaction(checked_track, checked_transaction)
            requested_payload = LedgerPayload(
                schema_version=RECORD_SCHEMA_VERSION,
                transaction_id=checked_transaction,
                operation_id=checked_operation,
                event_type=checked_event_type,
                state_after=state_after,
                details=requested_details,
            )
            for event, payload in zip(snapshot.events, snapshot.payloads, strict=True):
                if payload.operation_id != checked_operation:
                    continue
                if payload == requested_payload:
                    return event
                raise InputError(
                    f"Idempotency key {checked_operation!r} already binds different input"
                )

            timestamp = occurred_at_utc or utc_now()
            return self._commit_event(
                self.transaction_path(checked_track, checked_transaction),
                snapshot.metadata,
                snapshot.events,
                operation_id=checked_operation,
                event_type=checked_event_type,
                state_after=state_after,
                details=requested_details,
                occurred_at_utc=timestamp,
            )

    def _status_for_spec(self, spec: TransactionSpec) -> TransactionStatus:
        root = self.transaction_path(spec.track_id, spec.transaction_id)
        relative = self._relative(root)
        if not os.path.lexists(root):
            return TransactionStatus(
                book_id=spec.book_id,
                plan_id=spec.plan_id,
                plan_sha256=spec.plan_sha256,
                transaction_id=spec.transaction_id,
                track_id=spec.track_id,
                sequence=spec.sequence,
                transaction_path=relative,
                health=TransactionHealth.MISSING,
                state=None,
                event_count=0,
                head_event_sha256=None,
                corruption_category=None,
            )
        try:
            snapshot = self.inspect_transaction(spec.track_id, spec.transaction_id)
            if not snapshot.metadata.matches(spec):
                raise TransactionCorruption(
                    "metadata-invalid", "Transaction metadata differs from frozen plan"
                )
        except TransactionCorruption as exc:
            return TransactionStatus(
                book_id=spec.book_id,
                plan_id=spec.plan_id,
                plan_sha256=spec.plan_sha256,
                transaction_id=spec.transaction_id,
                track_id=spec.track_id,
                sequence=spec.sequence,
                transaction_path=relative,
                health=TransactionHealth.CORRUPT,
                state=None,
                event_count=0,
                head_event_sha256=None,
                corruption_category=exc.category,
            )
        return self._valid_status(snapshot, relative)

    @staticmethod
    def _valid_status(snapshot: TransactionSnapshot, relative: str) -> TransactionStatus:
        metadata = snapshot.metadata
        return TransactionStatus(
            book_id=metadata.book_id,
            plan_id=metadata.plan_id,
            plan_sha256=metadata.plan_sha256,
            transaction_id=metadata.transaction_id,
            track_id=metadata.track_id,
            sequence=metadata.sequence,
            transaction_path=relative,
            health=TransactionHealth.VALID,
            state=snapshot.state,
            event_count=len(snapshot.events),
            head_event_sha256=snapshot.head_event_sha256,
            corruption_category=None,
        )

    def _status_from_observed_root(
        self, root: Path
    ) -> tuple[TransactionStatus | None, CorruptTransactionPath | None]:
        relative = self._relative(root)
        try:
            metadata = self._load_metadata(root)
        except TransactionCorruption as exc:
            return None, CorruptTransactionPath(relative, exc.category)
        try:
            snapshot = self._read_chain(root, metadata)
        except TransactionCorruption as exc:
            return (
                TransactionStatus(
                    book_id=metadata.book_id,
                    plan_id=metadata.plan_id,
                    plan_sha256=metadata.plan_sha256,
                    transaction_id=metadata.transaction_id,
                    track_id=metadata.track_id,
                    sequence=metadata.sequence,
                    transaction_path=relative,
                    health=TransactionHealth.CORRUPT,
                    state=None,
                    event_count=0,
                    head_event_sha256=None,
                    corruption_category=exc.category,
                ),
                None,
            )
        return self._valid_status(snapshot, relative), None

    def inspect_plan_status(self, plan: FrozenBatchPlan) -> PlanStatus:
        """List every selected Track using ledger truth, including missing/corrupt ones."""

        StrictRecordCodec(FrozenBatchPlan).dump_bytes(plan)
        if plan.book_id != self.book_id:
            raise InputError("Frozen plan book_id does not match the transaction store")
        tracks = tuple(
            self._status_for_spec(TransactionSpec.from_plan(plan, track))
            for track in plan.tracks
        )
        return _make_plan_status(plan.plan_id, plan.canonical_sha256, tracks)

    @staticmethod
    def _mark_duplicate_plan_scope(
        statuses: Sequence[TransactionStatus],
    ) -> tuple[TransactionStatus, ...]:
        duplicate_indexes: set[int] = set()
        groups: dict[tuple[str, str], list[tuple[int, TransactionStatus]]] = {}
        for index, item in enumerate(statuses):
            groups.setdefault((item.plan_id, item.plan_sha256), []).append((index, item))
        for members in groups.values():
            by_sequence: dict[int, list[int]] = {}
            by_track: dict[str, list[int]] = {}
            by_transaction: dict[str, list[int]] = {}
            for index, item in members:
                by_sequence.setdefault(item.sequence, []).append(index)
                by_track.setdefault(item.track_id, []).append(index)
                by_transaction.setdefault(item.transaction_id, []).append(index)
            for buckets in (by_sequence, by_track, by_transaction):
                for indexes in buckets.values():
                    if len(indexes) > 1:
                        duplicate_indexes.update(indexes)
        return tuple(
            replace(
                item,
                health=TransactionHealth.CORRUPT,
                state=None,
                event_count=0,
                head_event_sha256=None,
                corruption_category="duplicate-plan-scope",
            )
            if index in duplicate_indexes
            else item
            for index, item in enumerate(statuses)
        )

    def rebuild_status_index(
        self,
        *,
        plans: Sequence[FrozenBatchPlan] = (),
        rebuilt_at_utc: str | None = None,
    ) -> DerivedStatusIndex:
        """Reconstruct all supplied plan and observed book status from transactions."""

        timestamp = rebuilt_at_utc or utc_now()
        _require_utc(timestamp, "status rebuild timestamp")
        expected: dict[tuple[str, str], TransactionSpec] = {}
        supplied_plan_keys: set[tuple[str, str]] = set()
        for plan in plans:
            StrictRecordCodec(FrozenBatchPlan).dump_bytes(plan)
            if plan.book_id != self.book_id:
                raise InputError("Frozen plan book_id does not match the transaction store")
            supplied_plan_keys.add((plan.plan_id, plan.canonical_sha256))
            for track in plan.tracks:
                spec = TransactionSpec.from_plan(plan, track)
                key = (spec.track_id, spec.transaction_id)
                prior = expected.get(key)
                if prior is not None and prior != spec:
                    raise InputError("Supplied plans bind one transaction path differently")
                expected[key] = spec

        statuses: list[TransactionStatus] = [
            self._status_for_spec(spec)
            for _, spec in sorted(
                expected.items(), key=lambda item: (item[1].plan_id, item[1].sequence)
            )
        ]
        seen_paths = set(expected)
        corrupt_paths: list[CorruptTransactionPath] = []

        if os.path.lexists(self.transactions_root):
            if self.transactions_root.is_symlink() or not self.transactions_root.is_dir():
                corrupt_paths.append(
                    CorruptTransactionPath("transactions", "transactions-root-invalid")
                )
            else:
                for track_root in sorted(
                    self.transactions_root.iterdir(), key=lambda item: item.name
                ):
                    track_relative = self._relative(track_root)
                    if track_root.is_symlink() or not track_root.is_dir():
                        corrupt_paths.append(
                            CorruptTransactionPath(track_relative, "track-root-invalid")
                        )
                        continue
                    for transaction_root in sorted(
                        track_root.iterdir(), key=lambda item: item.name
                    ):
                        relative = self._relative(transaction_root)
                        if transaction_root.name.startswith("."):
                            corrupt_paths.append(
                                CorruptTransactionPath(
                                    relative, "incomplete-transaction-staging"
                                )
                            )
                            continue
                        key = (track_root.name, transaction_root.name)
                        if key in seen_paths:
                            continue
                        if transaction_root.is_symlink() or not transaction_root.is_dir():
                            corrupt_paths.append(
                                CorruptTransactionPath(relative, "transaction-root-invalid")
                            )
                            continue
                        status, corruption = self._status_from_observed_root(
                            transaction_root
                        )
                        if status is not None:
                            statuses.append(status)
                        if corruption is not None:
                            corrupt_paths.append(corruption)

        statuses = list(self._mark_duplicate_plan_scope(statuses))
        ordered_statuses = tuple(
            sorted(
                statuses,
                key=lambda item: (
                    item.plan_id,
                    item.sequence,
                    item.track_id,
                    item.transaction_id,
                ),
            )
        )
        grouped: dict[tuple[str, str], list[TransactionStatus]] = {}
        for item in ordered_statuses:
            grouped.setdefault((item.plan_id, item.plan_sha256), []).append(item)
        # Supplied empty plans cannot exist because FrozenBatchPlan requires Tracks, but
        # preserve their key explicitly so the implementation never relies on scanning.
        for key in supplied_plan_keys:
            grouped.setdefault(key, [])
        plan_statuses = tuple(
            _make_plan_status(plan_id, plan_sha256, grouped[(plan_id, plan_sha256)])
            for plan_id, plan_sha256 in sorted(grouped)
        )
        ordered_corruptions = tuple(
            sorted(corrupt_paths, key=lambda item: (item.path, item.category))
        )
        fingerprint = _status_source_fingerprint(
            self.book_id, ordered_statuses, plan_statuses, ordered_corruptions
        )
        return seal_record(
            DerivedStatusIndex(
                schema_version=RECORD_SCHEMA_VERSION,
                book_id=self.book_id,
                rebuilt_at_utc=timestamp,
                transactions=ordered_statuses,
                plans=plan_statuses,
                corrupt_paths=ordered_corruptions,
                source_fingerprint=fingerprint,
                canonical_sha256="",
            )
        )

    @staticmethod
    def _same_truth(left: DerivedStatusIndex, right: DerivedStatusIndex) -> bool:
        return (
            left.book_id == right.book_id
            and left.source_fingerprint == right.source_fingerprint
            and left.transactions == right.transactions
            and left.plans == right.plans
            and left.corrupt_paths == right.corrupt_paths
        )

    def read_status(
        self,
        *,
        plans: Sequence[FrozenBatchPlan] = (),
        rebuilt_at_utc: str | None = None,
    ) -> StatusReadResult:
        """Read status from transaction truth, then retain or repair the cache."""

        rebuilt = self.rebuild_status_index(
            plans=plans, rebuilt_at_utc=rebuilt_at_utc
        )
        cache_relative = self._relative(self.index_path)
        codec = StrictRecordCodec(DerivedStatusIndex)
        if not os.path.lexists(self.index_path):
            durable_mkdir(self.index_path.parent)
            atomic_write_bytes(self.index_path, codec.dump_bytes(rebuilt))
            return StatusReadResult(
                rebuilt, StatusCacheDisposition.MISSING_REBUILT, cache_relative
            )

        try:
            cached = codec.load(self.index_path)
        except InputError:
            atomic_write_bytes(self.index_path, codec.dump_bytes(rebuilt))
            return StatusReadResult(
                rebuilt, StatusCacheDisposition.CORRUPT_REBUILT, cache_relative
            )

        if self._same_truth(cached, rebuilt):
            return StatusReadResult(
                cached, StatusCacheDisposition.CURRENT, cache_relative
            )

        atomic_write_bytes(self.index_path, codec.dump_bytes(rebuilt))
        return StatusReadResult(
            rebuilt, StatusCacheDisposition.STALE_REBUILT, cache_relative
        )


__all__ = [
    "ALLOWED_TRANSITIONS",
    "CorruptTransactionPath",
    "DerivedStatusIndex",
    "LedgerPayload",
    "PlanStatus",
    "StatusCacheDisposition",
    "StatusReadResult",
    "TransactionCorruption",
    "TransactionHealth",
    "TransactionLockUnavailable",
    "TransactionMetadata",
    "TransactionSnapshot",
    "TransactionSpec",
    "TransactionStatus",
    "TransactionStore",
    "reduce_ledger_events",
]
