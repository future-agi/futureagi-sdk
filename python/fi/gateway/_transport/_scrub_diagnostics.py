"""Transport diagnostic text and exchange-boundary adapters."""
from __future__ import annotations
import re
import types
from typing import Any
import httpx
from fi.gateway._constants import CREDENTIAL_HEADER_NAMES
from fi.gateway.callbacks.base import REDACTED

def composed_credential_values(
    headers: httpx.Headers | dict[str, str], composed_names: frozenset[str],
) -> tuple[bytes, ...]:
    """Snapshot this attempt's private values before retained headers are masked."""
    names = CREDENTIAL_HEADER_NAMES | composed_names
    values = {
        value for name, value in httpx.Headers(headers).raw
        if name.decode("ascii").lower() in names and value and value != REDACTED.encode()
    }
    # A transport may report the token alone, or quote the entire header value.
    values.update(value[7:] for value in tuple(values) if value.lower().startswith(b"bearer ") and value[7:])
    return tuple(values)


def scrub_error_text(error: BaseException, credentials: tuple[bytes, ...]) -> None:
    """Redact mutable diagnostics in place, retaining exception and HTTP identities.

    Inspect only standard exception links, diagnostic fields and their built-in
    containers. Copy containers so aliases in caller-owned data stay untouched.
    Do not traverse arbitrary caller objects or traceback locals.
    Byte/str repr forms matter: h11 quotes invalid headers, escaping newlines.
    """
    from fi.gateway._exceptions import StreamError
    from fi.gateway._transport import _scrub
    from fi.gateway._transport._scrub import _is, _class_dicts, _EXCEPTION_GROUP

    # Short synthetic keys are not meaningful substring secrets: replacing them
    # can corrupt ordinary words. Header masking remains unconditional.
    credentials = tuple(value for value in credentials if len(value) >= 8)
    if not credentials:
        return
    text_values: set[str] = set()
    for value in credentials:
        try:
            text = value.decode("utf-8")
        except UnicodeDecodeError:
            text = value.decode("latin-1")
        text_values.update((text, repr(text)[1:-1], repr(value)[2:-1]))
    byte_values = set(credentials) | {value.encode("utf-8") for value in text_values}
    # One substitution avoids reprocessing the replacement or shorter tokens
    # inside an already-redacted longer credential.
    text_pattern = re.compile("|".join(re.escape(v) for v in sorted(text_values, key=len, reverse=True)))
    byte_pattern = re.compile(b"|".join(re.escape(v) for v in sorted(byte_values, key=len, reverse=True)))
    pending = [error]
    seen: set[int] = set()
    memo: dict[int, Any] = {}
    text_nodes = 0

    def hash_safe(value: Any, depth: int = 0) -> bool:
        if depth > _scrub.TEXT_DEPTH_CAP:
            return False
        if type(value) in (str, bytes, int, float, bool, complex, type(None)):
            return True
        if type(value) in (tuple, frozenset):
            return len(value) <= _scrub.TEXT_NODE_CAP and all(hash_safe(item, depth + 1) for item in value)
        if type(value) is memoryview:
            return value.readonly and value.format in ("B", "b", "c")
        return False

    def redact(value: Any, depth: int = 0) -> Any:
        nonlocal text_nodes
        if _is(value, (httpx.Request, httpx.Response, httpx.Headers)):
            # Exchange identities are protected independently by the header mask.
            return value
        text_nodes += 1
        if text_nodes > _scrub.TEXT_NODE_CAP or depth > _scrub.TEXT_DEPTH_CAP:
            return REDACTED
        if _is(value, str):
            return text_pattern.sub(REDACTED, value)
        if _is(value, bytes):
            return byte_pattern.sub(REDACTED.encode(), value)
        if _is(value, BaseException):
            pending.append(value)
            return value
        if id(value) in memo:
            return memo[id(value)]
        if type(value) in (list, tuple, dict, set, frozenset) and len(value) > _scrub.TEXT_NODE_CAP - text_nodes:
            return REDACTED
        if type(value) is dict and not all(hash_safe(key) for key in dict.__iter__(value)):
            return REDACTED
        if type(value) in (set, frozenset) and not all(hash_safe(item) for item in value):
            return REDACTED
        if type(value) is list:
            cleaned_list: list[Any] = []
            memo[id(value)] = cleaned_list
            cleaned_list.extend(redact(item, depth + 1) for item in value)
            return cleaned_list
        elif type(value) is dict:
            cleaned_dict: dict[Any, Any] = {}
            memo[id(value)] = cleaned_dict
            cleaned_dict.update((redact(key, depth + 1), redact(item, depth + 1)) for key, item in dict.items(value))
            return cleaned_dict
        elif type(value) is tuple:
            items = tuple(redact(item, depth + 1) for item in value)
            # A tuple/list cycle may already have memoized this tuple below us.
            if id(value) not in memo:
                memo[id(value)] = items
            return memo[id(value)]
        elif type(value) in (set, frozenset):
            memo[id(value)] = type(value)(redact(item, depth + 1) for item in value)
            return memo[id(value)]
        elif type(value) is bytearray:
            memo[id(value)] = bytearray(byte_pattern.sub(REDACTED.encode(), value))
            return memo[id(value)]
        elif type(value) is memoryview:
            try:
                raw = value.tobytes()
            except ValueError:
                # A released view has no readable diagnostic contents.
                return value
            cleaned = byte_pattern.sub(REDACTED.encode(), raw)
            # Never write through the view into a caller's backing buffer. A
            # readonly copy also stays hashable when used in a set or dict key.
            memo[id(value)] = memoryview(cleaned if value.readonly else bytearray(cleaned))
            return memo[id(value)]
        return value

    def clean_field(name: str, original: Any) -> Any:
        try:
            cleaned = redact(original)
        except BaseException:
            cleaned = REDACTED
        # BaseException.args requires a tuple even when its entire diagnostic
        # payload has been replaced after a budget/inspection failure.
        return (cleaned,) if name == "args" and type(cleaned) is not tuple else cleaned

    while pending:
        current = pending.pop()
        if id(current) in seen:
            continue
        seen.add(id(current))
        for name in ("__cause__", "__context__"):
            link = BaseException.__dict__[name].__get__(current, type(current))
            if link is not None:
                pending.append(link)
        if _is(current, _EXCEPTION_GROUP):
            pending.extend(_EXCEPTION_GROUP.__dict__["exceptions"].__get__(current, type(current)))
        # Use native exception storage, never a subclass's attribute hooks,
        # properties or __dict__ override. Normal exception dictionaries have
        # exact string keys; injected collision keys are outside that layout.
        stored = BaseException.__dict__["__dict__"].__get__(current, type(current))
        protocol_fields = {"code", "type", "param", "gateway_evidence", "request_id"}
        if _is(current, StreamError):
            # Stream fields are parsed protocol data, or a wrapper around an
            # already-scrubbed transport cause. Do not rewrite their semantics.
            protocol_fields.update(("body", "message", "args"))
        if all(type(name) is str for name in dict.__iter__(stored)):
            for name, original in tuple(dict.items(stored)):
                if name in protocol_fields:
                    continue
                cleaned = clean_field(name, original)
                if cleaned is not original:
                    dict.__setitem__(stored, name, cleaned)
        # Built-in exceptions can render native cached fields instead of args.
        # Read only native slot/getset descriptors, skipping caller properties.
        fields = {"args", "message", "msg", "reason", "strerror", "filename", "filename2", "text", "object", "__notes__"}
        for namespace in _class_dicts(current):
            for name, descriptor in types.MappingProxyType.items(namespace):
                if type(name) is not str or name not in fields or name in protocol_fields:
                    continue
                if type(descriptor) not in (types.MemberDescriptorType, types.GetSetDescriptorType):
                    continue
                try:
                    original = descriptor.__get__(current, type(current))
                    cleaned = clean_field(name, original)
                    if cleaned is not original:
                        descriptor.__set__(current, cleaned)
                except (AttributeError, TypeError):
                    # Immutable diagnostic descriptors remain best effort.
                    pass


def bind_stream_scrubber(
    response: httpx.Response, credentials: tuple[bytes, ...], composed_names: frozenset[str],
) -> None:
    """Keep late diagnostic redaction in a closure, not public exchange data.

    No client or mutable header container is captured. The interpreter closure
    boundary is the same one used by HTTPX's stream machinery.
    """
    def scrub(error: BaseException) -> None:
        from fi.gateway._transport._scrub import scrub_reachable

        scrub_error_text(error, credentials)
        scrub_reachable((error,), composed_names)

    response._gateway_error_scrubber = scrub  # type: ignore[attr-defined]


def scrub_sent_request(
    request: httpx.Request | None,
    response: httpx.Response | None,
    error: BaseException | None,
    composed_names: frozenset[str] = frozenset(),
) -> None:
    """Mask known exchanges directly, then inspect optional diagnostic graphs."""
    from fi.gateway._transport._exchange_mask import mask_known_exchange
    from fi.gateway._transport._scrub import scrub_reachable

    mask_known_exchange(request, response, composed_names, error)
    scrub_reachable((request, response, error), composed_names)
