"""Integrity, path, atomic-write, and local-lock helpers."""

from __future__ import annotations

import hashlib
import json
import os
import secrets
import stat
import tempfile
import threading
import unicodedata
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterator

try:  # POSIX advisory locks
    import fcntl
except ImportError:  # pragma: no cover - exercised on Windows
    fcntl = None  # type: ignore[assignment]

try:  # Windows advisory locks
    import msvcrt
except ImportError:  # pragma: no cover - exercised on POSIX
    msvcrt = None  # type: ignore[assignment]

from .errors import InputError


def _absolute_lexical(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path.expanduser())))


def _open_directory_fd(path: Path, *, create: bool = False) -> int:
    """Open a directory through pinned, no-follow parent descriptors on POSIX."""

    if os.name != "posix":  # pragma: no cover - POSIX is the paid-render platform
        raise InputError("Descriptor-rooted directory operations require POSIX")
    nofollow = getattr(os, "O_NOFOLLOW", None)
    directory = getattr(os, "O_DIRECTORY", None)
    if nofollow is None or directory is None:  # pragma: no cover - unsupported POSIX variant
        raise InputError("This POSIX platform lacks required no-follow directory operations")

    absolute = _absolute_lexical(path)
    parts = absolute.parts
    if not parts or not absolute.is_absolute():
        raise InputError(f"Directory path must be absolute: {path}")
    flags = os.O_RDONLY | directory | nofollow | getattr(os, "O_CLOEXEC", 0)
    try:
        current = os.open(parts[0], flags)
    except OSError as exc:
        raise InputError(f"Cannot open directory anchor for {path}: {exc}") from exc

    try:
        for component in parts[1:]:
            if component in {"", ".", ".."}:
                raise InputError(f"Directory path contains an unsafe component: {path}")
            try:
                child = os.open(component, flags, dir_fd=current)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(component, 0o755, dir_fd=current)
                except FileExistsError:
                    pass
                os.fsync(current)
                child = os.open(component, flags, dir_fd=current)
                os.fsync(child)
            os.close(current)
            current = child
        return current
    except BaseException as exc:
        os.close(current)
        if isinstance(exc, InputError):
            raise
        if isinstance(exc, OSError):
            raise InputError(f"Cannot open no-follow directory path {path}: {exc}") from exc
        raise


def _open_regular_file_fd(path: Path) -> int:
    if os.name != "posix":  # pragma: no cover - handled by the caller
        raise InputError("Descriptor-rooted file operations require POSIX")
    absolute = _absolute_lexical(path)
    parent_fd = _open_directory_fd(absolute.parent)
    try:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
        descriptor = os.open(absolute.name, flags, dir_fd=parent_fd)
    except OSError as exc:
        raise InputError(f"Cannot open required no-follow file {path}: {exc}") from exc
    finally:
        os.close(parent_fd)
    if not stat.S_ISREG(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise InputError(f"Required path is not a regular file: {path}")
    return descriptor


def read_bytes_nofollow(path: Path) -> bytes:
    if os.name != "posix":  # pragma: no cover - Windows offline support
        try:
            return path.read_bytes()
        except OSError as exc:
            raise InputError(f"Cannot read required file {path}: {exc}") from exc
    descriptor = _open_regular_file_fd(path)
    chunks: list[bytes] = []
    try:
        while chunk := os.read(descriptor, 1024 * 1024):
            chunks.append(chunk)
    except OSError as exc:
        raise InputError(f"Cannot read required file {path}: {exc}") from exc
    finally:
        os.close(descriptor)
    return b"".join(chunks)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def sha256_file(path: Path) -> str:
    return sha256_bytes(read_bytes_nofollow(path))


def normalize_lf_nfc(value: str) -> str:
    return unicodedata.normalize("NFC", value.replace("\r\n", "\n").replace("\r", "\n"))


def utc_now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")


def compact_utc_now() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def fsync_directory(path: Path) -> None:
    """Persist a directory through a no-follow descriptor where supported."""

    if os.name == "nt":  # Windows does not expose POSIX directory fsync.
        return
    descriptor = _open_directory_fd(path)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def durable_mkdir(path: Path) -> None:
    """Create and fsync a directory chain without following swapped symlinks."""

    if os.name == "posix":
        descriptor = _open_directory_fd(path, create=True)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
        parent_descriptor = _open_directory_fd(_absolute_lexical(path).parent)
        try:
            os.fsync(parent_descriptor)
        finally:
            os.close(parent_descriptor)
        return

    target = _absolute_lexical(path)  # pragma: no cover - Windows offline support
    try:
        target.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        raise InputError(f"Cannot create directory {target}: {exc}") from exc
    if target.is_symlink() or not target.is_dir():
        raise InputError(f"Expected a real directory at {target}")


def atomic_write_bytes(path: Path, content: bytes) -> None:
    absolute = _absolute_lexical(path)
    if not absolute.name or absolute.name in {".", ".."}:
        raise InputError(f"Cannot atomically write an unsafe path: {path}")

    if os.name != "posix":  # pragma: no cover - Windows offline support
        durable_mkdir(absolute.parent)
        descriptor, temporary_name = tempfile.mkstemp(prefix=f".{absolute.name}.", dir=absolute.parent)
        temporary = Path(temporary_name)
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temporary, absolute)
        except BaseException:
            temporary.unlink(missing_ok=True)
            raise
        return

    parent_fd = _open_directory_fd(absolute.parent, create=True)
    temporary_name = f".{absolute.name}.{secrets.token_hex(12)}.tmp"
    descriptor: int | None = None
    try:
        flags = (
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_CLOEXEC", 0)
        )
        descriptor = os.open(temporary_name, flags, 0o600, dir_fd=parent_fd)
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(
            temporary_name,
            absolute.name,
            src_dir_fd=parent_fd,
            dst_dir_fd=parent_fd,
        )
        os.fsync(parent_fd)
    except BaseException:
        if descriptor is not None:
            os.close(descriptor)
        try:
            os.unlink(temporary_name, dir_fd=parent_fd)
        except FileNotFoundError:
            pass
        raise
    finally:
        os.close(parent_fd)


def atomic_write_text(path: Path, content: str) -> None:
    atomic_write_bytes(path, content.encode("utf-8"))


def atomic_write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def durable_replace(
    source: Path,
    destination: Path,
    *,
    source_kind: str,
) -> None:
    """Rename within pinned parent directories and fsync both sides."""

    if source_kind not in {"file", "directory"}:
        raise InputError(f"Unsupported durable replacement source kind: {source_kind}")
    source_absolute = _absolute_lexical(source)
    destination_absolute = _absolute_lexical(destination)

    if os.name != "posix":  # pragma: no cover - Windows offline support
        if destination_absolute.exists() or destination_absolute.is_symlink():
            raise InputError(f"Refusing to replace an existing destination: {destination}")
        os.replace(source_absolute, destination_absolute)
        return

    source_parent_fd = _open_directory_fd(source_absolute.parent)
    destination_parent_fd = _open_directory_fd(destination_absolute.parent)
    try:
        source_stat = os.stat(source_absolute.name, dir_fd=source_parent_fd, follow_symlinks=False)
        expected_type = stat.S_ISREG if source_kind == "file" else stat.S_ISDIR
        if not expected_type(source_stat.st_mode):
            raise InputError(f"Durable replacement source has the wrong type: {source}")
        try:
            os.stat(destination_absolute.name, dir_fd=destination_parent_fd, follow_symlinks=False)
        except FileNotFoundError:
            pass
        else:
            raise InputError(f"Refusing to replace an existing destination: {destination}")
        os.replace(
            source_absolute.name,
            destination_absolute.name,
            src_dir_fd=source_parent_fd,
            dst_dir_fd=destination_parent_fd,
        )
        os.fsync(source_parent_fd)
        os.fsync(destination_parent_fd)
    except OSError as exc:
        raise InputError(f"Cannot durably replace {source} with {destination}: {exc}") from exc
    finally:
        os.close(source_parent_fd)
        os.close(destination_parent_fd)


_LOCAL_LOCKS_GUARD = threading.Lock()
_LOCAL_LOCKS: dict[str, threading.Lock] = {}


@contextmanager
def exclusive_file_lock(path: Path) -> Iterator[None]:
    """Serialize cooperating render/package threads and processes."""

    absolute = _absolute_lexical(path)
    durable_mkdir(absolute.parent)
    key = str(absolute)
    with _LOCAL_LOCKS_GUARD:
        local_lock = _LOCAL_LOCKS.setdefault(key, threading.Lock())
    with local_lock:
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
                handle_context = os.fdopen(descriptor, "a+b")
            else:  # pragma: no cover - Windows
                handle_context = absolute.open("a+b")

            with handle_context as handle:
                if fcntl is not None:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
                    try:
                        yield
                    finally:
                        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
                elif msvcrt is not None:  # pragma: no cover - Windows
                    handle.seek(0, os.SEEK_END)
                    if handle.tell() == 0:
                        handle.write(b"\0")
                        handle.flush()
                    handle.seek(0)
                    msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
                    try:
                        yield
                    finally:
                        handle.seek(0)
                        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
                else:  # pragma: no cover - unsupported interpreter platform
                    raise InputError("No supported cross-process file-lock API is available")
        except OSError as exc:
            raise InputError(f"Cannot acquire audition lock {path}: {exc}") from exc


def _reject_duplicate_json_names(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for name, value in pairs:
        if name in result:
            raise ValueError(f"duplicate object name {name!r}")
        result[name] = value
    return result


def _reject_nonfinite_json_constant(value: str) -> None:
    raise ValueError(f"non-finite JSON number {value!r}")


def json_loads_strict(value: str, label: str) -> Any:
    try:
        return json.loads(
            value,
            object_pairs_hook=_reject_duplicate_json_names,
            parse_constant=_reject_nonfinite_json_constant,
        )
    except (json.JSONDecodeError, ValueError) as exc:
        raise InputError(f"Malformed JSON in {label}: {exc}") from exc


def read_json(path: Path) -> Any:
    raw = read_bytes_nofollow(path)
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise InputError(f"Malformed UTF-8 JSON in {path}: {exc}") from exc
    return json_loads_strict(text, str(path))


def resolve_inside(workspace_root: Path, value: str) -> Path:
    candidate = Path(value)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise InputError(f"Path must be workspace-relative and traversal-free: {value!r}")

    root = workspace_root.expanduser().resolve()
    lexical = root.joinpath(*candidate.parts)
    cursor = root
    for part in candidate.parts:
        cursor = cursor / part
        if os.path.lexists(cursor) and cursor.is_symlink():
            raise InputError(f"Path must not traverse a symlink: {value!r}")

    resolved = lexical.resolve()
    try:
        resolved.relative_to(root)
    except ValueError as exc:
        raise InputError(f"Path escapes the workspace: {value!r}") from exc
    return resolved


def resolve_inside_approved_root(
    workspace_root: Path,
    approved_root: Path | str,
    value: str,
    *,
    require_exists: bool = False,
    expected_kind: str | None = None,
) -> Path:
    """Resolve a no-follow workspace path inside one narrower approved root.

    ``value`` remains workspace-relative so persisted paths have one canonical trust
    anchor.  Existing components in both the approved root and candidate are checked
    for symlinks by :func:`resolve_inside`; non-existing destinations are accepted
    only when every existing ancestor is safe.
    """

    root = workspace_root.expanduser().resolve()
    if isinstance(approved_root, Path):
        approved_lexical = _absolute_lexical(approved_root)
        try:
            approved_relative = approved_lexical.relative_to(root).as_posix()
        except ValueError as exc:
            raise InputError("Approved path root is outside the workspace") from exc
    elif isinstance(approved_root, str):
        approved_relative = approved_root
    else:
        raise InputError("Approved path root must be a path or workspace-relative string")

    approved = resolve_inside(root, approved_relative)
    candidate = resolve_inside(root, value)
    try:
        candidate.relative_to(approved)
    except ValueError as exc:
        raise InputError("Path is outside its approved root") from exc

    if expected_kind not in {None, "file", "directory"}:
        raise InputError("Expected path kind must be file or directory")
    exists = os.path.lexists(candidate)
    if require_exists and not exists:
        raise InputError("Required approved path does not exist")
    if exists:
        try:
            metadata = os.stat(candidate, follow_symlinks=False)
        except OSError as exc:
            raise InputError("Approved path cannot be inspected safely") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise InputError("Approved path must not be a symlink")
        if expected_kind == "file" and not stat.S_ISREG(metadata.st_mode):
            raise InputError("Approved path is not a regular file")
        if expected_kind == "directory" and not stat.S_ISDIR(metadata.st_mode):
            raise InputError("Approved path is not a directory")
    return candidate


def workspace_relative(workspace_root: Path, path: Path) -> str:
    root = workspace_root.expanduser().resolve()
    try:
        relative = path.expanduser().resolve().relative_to(root)
    except ValueError as exc:
        raise InputError(f"Path is outside the workspace: {path}") from exc
    checked = resolve_inside(root, relative.as_posix())
    if checked != path.expanduser().resolve():
        raise InputError(f"Path is not canonical inside the workspace: {path}")
    return relative.as_posix()


def find_workspace_root(start: Path) -> Path:
    current = start.resolve()
    for candidate in (current, *current.parents):
        if (candidate / "audiobook-studio" / "config" / "audition.toml").is_file():
            return candidate
    raise InputError(
        "Cannot locate the workspace root containing audiobook-studio/config/audition.toml; "
        "pass --workspace-root explicitly"
    )
