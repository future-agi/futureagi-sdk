"""Bounded JSON input and atomic, private agent state files."""
from __future__ import annotations

import contextlib
import json
import os
import stat
from pathlib import Path
import tempfile

from .definition import LIMIT, canonical, invalid

# JSON null is data, not evidence that a file is absent.
MISSING = object()


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            invalid("Duplicate JSON object keys are not allowed.")
        result[key] = value
    return result


def read_json(path: str | Path, *, missing: bool = False):
    try:
        # Refuse symlinks, including lockfiles pointing at unrelated files.
        fd = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0),
        )
        with os.fdopen(fd, "rb") as handle:
            if not stat.S_ISREG(os.fstat(handle.fileno()).st_mode):
                invalid("Agent input must be a regular file.", "agent_file_error")
            raw = handle.read(LIMIT + 1)
        if len(raw) > LIMIT:
            invalid("Agent file exceeds 1 MiB.")
        return json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_pairs,
            parse_constant=lambda _: invalid(
                "Non-finite JSON numbers are not allowed."
            ),
        )
    except FileNotFoundError:
        if missing:
            return MISSING
        invalid("Agent file does not exist.", "agent_file_error")
    except (OSError, UnicodeError, ValueError, RecursionError):
        invalid(
            "Agent file could not be read as bounded UTF-8 JSON.", "agent_file_error"
        )


def write_json(path: str | Path, value, *, replace: bool = False):
    path = Path(path)
    data = (canonical(value) + "\n").encode("utf-8")
    if len(data) > LIMIT:
        invalid("Agent state exceeds 1 MiB.")
    temporary = None
    try:
        fd, temporary = tempfile.mkstemp(prefix=".futureagi-", dir=path.parent)
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if replace:
            if path.is_symlink():
                invalid("Refusing a symlink state file.", "agent_file_error")
            os.replace(temporary, path)
        else:
            # Atomic no-clobber: exported definitions never overwrite another file.
            os.link(temporary, path)
        directory = os.open(path.parent, os.O_RDONLY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    except OSError:
        invalid(
            "Agent state could not be saved; output must be new and its directory writable.",
            "agent_file_error",
        )
    finally:
        if temporary is not None:
            with contextlib.suppress(FileNotFoundError):
                os.unlink(temporary)


@contextlib.contextmanager
def locked(path: str | Path):
    """One process per lock path. A crash releases flock, but keeps any pending-write journal."""
    try:
        import fcntl
    except ImportError:
        invalid(
            "Agent apply currently requires a POSIX file-locking host.",
            "agent_file_error",
        )
    handle = None
    try:
        fd = os.open(
            str(Path(path).absolute()) + ".guard",
            os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        handle = os.fdopen(fd, "r+")
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        if handle is not None:
            handle.close()
        invalid(
            "Another apply holds this lockfile, or its directory is not writable.",
            "agent_file_busy",
        )
    try:
        yield
    finally:
        handle.close()
