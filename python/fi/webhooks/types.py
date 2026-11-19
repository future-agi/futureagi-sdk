"""Result types of the webhooks client: the API's JSON objects, as dicts with attribute access.

Every result is a plain ``dict`` of the wire shape (the REST contract's field names, unchanged), so
``ep["status"]``, ``json.dumps(ep)`` and ``dict(ep)`` work as they do for the rest of the SDK. Fields are also readable
as attributes (``ep.status``), and nested objects are wrapped the same way. ``repr()`` never shows a secret: a
``secret`` field prints as its last four characters.
"""

from __future__ import annotations

from typing import Any, Optional


def _wrap(value: Any) -> Any:
    if isinstance(value, Record):
        return value
    if isinstance(value, dict):
        return Record(value)
    if isinstance(value, list):
        return [_wrap(v) for v in value]
    return value


class Record(dict):
    """A JSON object from the webhooks API: a dict whose keys are also read-only attributes."""

    def __init__(self, data: Optional[dict] = None, **extra: Any) -> None:
        super().__init__()
        for key, value in {**(data or {}), **extra}.items():
            dict.__setitem__(self, key, _wrap(value))

    def __getattr__(self, name: str) -> Any:
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"{type(self).__name__} has no field {name!r}") from None

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"{type(self).__name__} is read-only; use dict(...) for a copy you can change")

    def to_dict(self) -> dict:
        """A deep copy as plain dicts and lists."""

        def plain(v: Any) -> Any:
            if isinstance(v, dict):
                return {k: plain(x) for k, x in v.items()}
            if isinstance(v, list):
                return [plain(x) for x in v]
            return v

        return plain(self)

    def __repr__(self) -> str:
        shown = {k: (_mask(v) if k == "secret" and isinstance(v, str) else v) for k, v in self.items()}
        return f"{type(self).__name__}({shown!r})"

    __str__ = __repr__


def _mask(secret: str) -> str:
    return "…" + secret[-4:] if secret else secret


class Endpoint(Record):
    """A webhook endpoint (``EndpointOut``). ``url`` and ``header_names`` are ``None`` unless the caller is a
    workspace admin. After :meth:`create`, it also has ``secret`` (shown once) and ``warnings``."""


class Rotation(Record):
    """The answer to ``rotate_secret`` (``RotateOut``): the new ``secret`` (shown once), its ``tail``, the
    ``previous`` secret's ``{tail, expires_at}`` (``None`` with an overlap of 0) and any ``revoked_tails``."""

    @property
    def previous_tail(self) -> Optional[str]:
        prev = self.get("previous")
        return prev.get("tail") if prev else None

    @property
    def previous_expires_at(self) -> Optional[str]:
        prev = self.get("previous")
        return prev.get("expires_at") if prev else None


class TestResult(Record):
    """The answer to ``test`` (``TestOut``): ``status_code``, ``outcome``, ``latency_ms`` and ``response_excerpt``
    once the attempt settled; only ``event_id`` and ``delivery_id`` while it is still being sent (``settled``
    False)."""

    __test__ = False  # not a pytest class

    @property
    def settled(self) -> bool:
        return self.get("outcome") is not None

    @property
    def ok(self) -> bool:
        """The receiver answered 2xx."""
        code = self.get("status_code")
        return self.get("outcome") == "success" and isinstance(code, int) and 200 <= code < 300


class Page(Record):
    """One page of a cursor-paged list: ``results`` and ``next_cursor`` (``None`` on the last page). Pass
    ``cursor=page.next_cursor`` for the next one."""

    @property
    def has_more(self) -> bool:
        return bool(self.get("next_cursor"))
