"""POSIX directory-relative, no-follow writes with identity-checked rollback."""

from __future__ import annotations

import os
from pathlib import Path, PurePosixPath
from typing import Iterable, Tuple


class SafePathError(RuntimeError):
    """A path cannot be accessed without following links or replacing work."""


def relative_parts(value: str) -> Tuple[str, ...]:
    path = PurePosixPath(value)
    if (not value or path.is_absolute() or ".." in path.parts
            or "\\" in value or ":" in value or "\x00" in value or not path.parts):
        raise SafePathError(f"unsafe relative path: {value!r}")
    return path.parts


def require_safe_writes() -> None:
    required = (os.open, os.mkdir, os.stat, os.unlink, os.rmdir)
    if (os.name != "posix" or not hasattr(os, "O_NOFOLLOW")
            or not hasattr(os, "O_DIRECTORY")
            or not all(function in os.supports_dir_fd for function in required)):
        raise SafePathError("safe writes require POSIX directory descriptors and O_NOFOLLOW")


def identity(info: os.stat_result) -> Tuple[int, int]:
    return info.st_dev, info.st_ino


def write_exclusive(root: Path, entries: Iterable[Tuple[str, bytes]]) -> None:
    """Never follow directory links; roll back only objects created by this call.

    Ancestors must be real directories. Callers may canonicalize the trusted
    parent once before discovery, but must not resolve target links after it.
    Open descriptors pin directories even when another process renames them.
    This is not a lock against concurrent edits or process termination.
    """
    require_safe_writes()
    root = root.absolute()
    records = []
    descriptors = []
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW

    def directory(parent: int, name: str) -> int:
        try:
            descriptor = os.open(name, flags, dir_fd=parent)
        except FileNotFoundError:
            try:
                os.mkdir(name, 0o755, dir_fd=parent)
            except FileExistsError:
                return directory(parent, name)
            info = os.stat(name, dir_fd=parent, follow_symlinks=False)
            records.append((parent, name, identity(info), True))
            descriptor = os.open(name, flags, dir_fd=parent)
        descriptors.append(descriptor)
        return descriptor

    try:
        descriptor = os.open(root.anchor, flags)
        descriptors.append(descriptor)
        for part in root.parts[1:]:
            descriptor = directory(descriptor, part)
        root_descriptor = descriptor
        for relative, content in entries:
            parts = relative_parts(relative)
            parent = root_descriptor
            for part in parts[:-1]:
                parent = directory(parent, part)
            descriptor = os.open(
                parts[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o644, dir_fd=parent,
            )
            records.append((parent, parts[-1], identity(os.fstat(descriptor)), False))
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(content)
            except BaseException:
                try:
                    os.close(descriptor)
                except OSError:
                    pass
                raise
    except BaseException as exc:
        cleanup_errors = []
        for parent, name, expected, is_directory in reversed(records):
            try:
                actual = os.stat(name, dir_fd=parent, follow_symlinks=False)
                if identity(actual) != expected:
                    raise SafePathError(f"refusing cleanup of replaced object: {name}")
                operation = os.rmdir if is_directory else os.unlink
                operation(name, dir_fd=parent)
            except (OSError, SafePathError) as cleanup:
                cleanup_errors.append(str(cleanup))
        if cleanup_errors:
            raise SafePathError(
                f"write failed: {exc}; incomplete rollback: {'; '.join(cleanup_errors)}"
            ) from exc
        if isinstance(exc, (OSError, SafePathError)):
            raise SafePathError(f"safe write refused or failed: {exc}") from exc
        raise
    finally:
        for descriptor in reversed(descriptors):
            os.close(descriptor)
