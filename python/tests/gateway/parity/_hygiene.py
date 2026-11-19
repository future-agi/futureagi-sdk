"""Refuse a golden that carries a local path.

The twin of ``gateway-client/tests/parity/harness/hygiene.mjs``; both pass
``tests/fixtures/gateway/hygiene-cases.json``.

A recording holds what the SDK does. A path of the checkout, an install or a
temp directory says where it was recorded: the golden then reproduces from
that one directory only, and a machine's layout lands in the repository. Two
rules find one:

- the static rule, which needs no context (a committed golden's recording
  place is unknown): any ``file://`` URL, and an absolute path under a home,
  volume or temp root that does not continue a word or URL path;
- the recorder's own roots (its checkout, the interpreter prefix, the working,
  home, temp and output directories), passed in. Any absolute directory other
  than the filesystem root is usable, including a single-component checkout.

Text after a ``<path>`` placeholder is relative to it and is never checked.
"""

from __future__ import annotations

import os
import re
import sys
import tempfile
from collections.abc import Iterable
from pathlib import Path
from typing import Any

from ._fixtures import REPO
from ._observe import dump

_PLACEHOLDER = re.compile(r"<path>[^\s\"'()]*")
_STATIC = re.compile(
    r"file://|(?<![\w.@+~-])/(?:Users|Volumes|home|tmp|private|root|var/folders)/"
)
_USABLE = re.compile(r"^/[^/]")


class LocalPathError(ValueError):
    pass


def _variants(roots: Iterable[str]) -> list[str]:
    out = set()
    for root in roots:
        if not isinstance(root, str) or not _USABLE.match(root):
            continue
        out.add(root.rstrip("/"))
        out.add(os.path.realpath(root).rstrip("/"))
    return sorted(r for r in out if _USABLE.match(r))


def leaks(text: str, roots: Iterable[str] = ()) -> list[str]:
    """The local paths in one string: each static token, then each root it contains."""
    body = _PLACEHOLDER.sub("<path>", text)
    found = [m.group(0) for m in _STATIC.finditer(body)]
    found += [root for root in _variants(roots) if root in body]
    return found


def leaks_in(
    value: Any, roots: Iterable[str] = (), at: str = ""
) -> list[dict[str, str]]:
    """Every string in a JSON-able value, keys included, with its JSON path."""
    roots = tuple(roots)
    out: list[dict[str, str]] = []

    def visit(v: Any, path: str) -> None:
        if isinstance(v, str):
            out.extend({"at": path, "token": t} for t in leaks(v, roots))
        elif isinstance(v, (list, tuple)):
            for i, item in enumerate(v):
                visit(item, f"{path}/{i}")
        elif isinstance(v, dict):
            for key in sorted(v, key=str):
                sub = f"{path}/{key}"
                out.extend({"at": sub, "token": t} for t in leaks(str(key), roots))
                visit(v[key], sub)

    visit(value, at)
    return out


def recorder_roots(*extra: Path | str) -> list[str]:
    """The directories a recorder process knows it runs from."""
    base = [REPO, Path.cwd(), Path.home(), tempfile.gettempdir(), sys.prefix]
    return [os.path.abspath(p) for p in (*base, *extra)]  # leaks() adds realpaths


def write_checked(file: Path, data: Any, roots: Iterable[str]) -> str:
    """Write ``dump(data)`` to ``file``, or refuse (nothing written) if any string leaks."""
    found = leaks_in(data, roots)
    if found:
        shown = "; ".join(f"{f['at'] or '/'}: {f['token']}" for f in found[:5])
        raise LocalPathError(
            f"refusing to write {file}: {len(found)} local path(s) ({shown})"
        )
    text = dump(data)
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(text)
    return text
