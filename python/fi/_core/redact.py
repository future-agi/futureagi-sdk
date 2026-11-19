"""Redaction (ported from the Omega SDK runtime).

Credentials, the Bearer token and every field the contract marks secret are redacted in errors,
reprs, raw-response views and cassettes. One redactor for the whole SDK, using only the standard
library.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Mapping
from typing import Any

#: What a redacted value is replaced with.
REDACTED = "[redacted]"

#: Header names whose values are never shown.
SECRET_HEADERS = frozenset(
    {
        "x-api-key",
        "x-secret-key",
        "authorization",
        "proxy-authorization",
        "cookie",
        "set-cookie",
        "sec-websocket-protocol",
    }
)

#: Field names treated as secret wherever they appear in a structured value.
SECRET_FIELD = re.compile(
    r"token|secret|password|passwd|api_?key|private_?key|credential|^code$|^state$|^env$|^envs$", re.I
)
_MAX_DEPTH = 8


def redact_headers(headers: Mapping[str, str] | Iterable[tuple[str, str]]) -> dict[str, str]:
    """A copy of the headers with every secret value replaced."""
    pairs = list(headers.items()) if isinstance(headers, Mapping) else list(headers)
    return {
        str(name).lower(): (REDACTED if str(name).lower() in SECRET_HEADERS else str(value)) for name, value in pairs
    }


def redact_value(value: Any, depth: int = 0) -> Any:
    """A deep copy with every secret-named field replaced. Depth-limited; never raises."""
    if depth > _MAX_DEPTH:
        return REDACTED
    if isinstance(value, list):
        return [redact_value(item, depth + 1) for item in value]
    if isinstance(value, dict):
        return {k: (REDACTED if SECRET_FIELD.search(str(k)) else redact_value(v, depth + 1)) for k, v in value.items()}
    return value


def _copy(value: Any) -> Any:
    if isinstance(value, list):
        return [_copy(v) for v in value]
    if isinstance(value, dict):
        return {k: _copy(v) for k, v in value.items()}
    return value


def _redact_path(value: Any, segments: list[str]) -> Any:
    if not segments:
        return REDACTED
    if isinstance(value, list):
        return [_redact_path(v, segments[1:]) for v in value] if segments[0] == "*" else value
    if isinstance(value, dict):
        head, rest = segments[0], segments[1:]
        for key in list(value):
            if head in ("*", key):
                value[key] = _redact_path(value[key], rest)
    return value


def redact_paths(value: Any, paths: Iterable[str]) -> Any:
    """Redact the fields a contract marks secret. Paths are dotted; ``*`` matches every key or item."""
    out = _copy(value)
    for path in paths:
        out = _redact_path(out, path.split("."))
    return out


def scrub_text(text: str, secrets: Iterable[str | None], *, min_length: int = 4) -> str:
    """Replace known secrets in one longest-first literal pass, never re-scrubbing replacements.
    Use min_length=1 when even short submitted credentials must be scrubbed."""
    known = sorted({s for s in secrets if s and len(s) >= min_length}, key=lambda s: (-len(s), s))
    if not known:
        return text
    return re.sub("|".join(re.escape(s) for s in known), lambda _: REDACTED, text)


def scrub_value(value: Any, secrets: Iterable[str | None], depth: int = 0, *,
                min_length: int = 4, scrub_keys: bool = True) -> Any:
    """A deep copy with known secrets replaced in strings; scrub_keys=False preserves wire field names.
    A secret a server reflected in JSON text with escapes (a quote, a backslash, ``\\uXXXX``) is only
    whole once decoded, so :func:`scrub_text` on the raw text misses it. Depth-limited; never raises."""
    known = secrets if isinstance(secrets, list) else list(secrets)
    if depth > _MAX_DEPTH:
        return REDACTED
    if isinstance(value, str):
        return scrub_text(value, known, min_length=min_length)
    if isinstance(value, list):
        return [scrub_value(item, known, depth + 1, min_length=min_length, scrub_keys=scrub_keys) for item in value]
    if isinstance(value, dict):
        return {
            (scrub_text(str(k), known, min_length=min_length) if scrub_keys else k):
                scrub_value(v, known, depth + 1, min_length=min_length, scrub_keys=scrub_keys)
            for k, v in value.items()
        }
    return value


def request_secret_values(body: Any, marked_paths: Iterable[str] = ()) -> list[str]:
    """The strings a request carries in secret fields: at the contract's marked ``request.`` paths and
    in any secret-named field. Used to scrub a server's reflected error text."""
    out: set[str] = set()

    def collect(value: Any, depth: int = 0) -> None:
        if depth > _MAX_DEPTH:
            return
        if isinstance(value, str):
            out.add(value)
        elif isinstance(value, list):
            for item in value:
                collect(item, depth + 1)
        elif isinstance(value, dict):
            for item in value.values():
                collect(item, depth + 1)

    def named(value: Any, depth: int = 0) -> None:
        if depth > _MAX_DEPTH or not isinstance(value, dict):
            return
        for key, item in value.items():
            if SECRET_FIELD.search(str(key)):
                collect(item)
            else:
                named(item, depth + 1)

    def at(value: Any, segments: list[str]) -> None:
        if not segments:
            collect(value)
            return
        entries = enumerate(value) if isinstance(value, list) else value.items() if isinstance(value, dict) else ()
        for key, item in entries:
            if segments[0] in ("*", str(key)):
                at(item, segments[1:])

    named(body)
    for path in marked_paths:
        if path.startswith("request."):
            at(body, path.split(".", 1)[1].split("."))
    return sorted(out)
