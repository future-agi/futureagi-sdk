"""The webhooks REST contract (the Future AGI API under ``webhooks/``, OpenAPI operations ``webhooks_*``) as request specs.

One source for the sync and the async client: each operation is a :class:`Call` (method, path, query, JSON body, the
status codes that succeed, and the result type). The clients only send it. Nothing here does I/O.

Retry classes (``fi._http``): reads (GET) retry on 429, 502-504 and network errors; writes (POST, PATCH, PUT) retry
only on 429 and when nothing was sent (a 5xx after a write may mean it ran); DELETE is idempotent.
"""

from __future__ import annotations

import datetime as _dt
import re
from dataclasses import dataclass, field
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple, Union
from urllib.parse import quote

from fi.errors import FutureAGIAPIError, api_error
from fi.webhooks import types as t
from fi.webhooks._text import inert

PREFIX = "/webhooks"
EVENT_TYPES = (
    "prompt.version.created",
    "prompt.label.changed",
    "deployment.run.completed",
    "deployment.run.failed",
)
_DURATION = re.compile(r"^\s*(\d+)\s*([smhdw]?)\s*$")  # a bare number is seconds
_ISO_TIME = re.compile(r"\d{4}-\d{2}-\d{2}(?:[T ]\d{2}:\d{2}(?::\d{2}(?:\.\d{1,9})?)?)?(?:Z|[+-]\d{2}:?\d{2})?")
_UNIT_S = {"": 1, "s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}

When = Union[str, int, float, _dt.datetime, _dt.timedelta, None]


@dataclass(frozen=True)
class Call:
    method: str
    path: str
    params: Dict[str, Any] = field(default_factory=dict)
    json: Optional[Any] = None
    ok: Tuple[int, ...] = (200,)
    result: Any = t.Record


def seconds(value: Union[str, int, float, _dt.timedelta]) -> int:
    """``"24h"``, ``"30m"``, ``"7d"``, ``"90s"``, ``"2w"``, a number of seconds or a ``timedelta`` → seconds."""
    if isinstance(value, _dt.timedelta):
        return int(value.total_seconds())
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return int(value)
    m = _DURATION.match(str(value))
    if not m:
        raise ValueError(f"not a duration: {value!r} (use a number of seconds, or 90s, 30m, 24h, 7d, 2w)")
    return int(m.group(1)) * _UNIT_S[m.group(2)]


def check_when(value: str) -> str:
    """``value`` unchanged if it is a duration ago (``"24h"``) or an ISO-8601 date or time, else ``ValueError``."""
    if _DURATION.match(value) or _ISO_TIME.fullmatch(value.strip()):
        return value
    raise ValueError(f"not a time: {value!r} (use a duration ago such as 30m or 24h, or an ISO time such as "
                     "2026-10-23T09:00:00Z)")


def instant(value: When, *, now: Optional[_dt.datetime] = None) -> Optional[str]:
    """An ISO-8601 UTC time for ``since`` / ``until``: a datetime, an ISO string (sent as is), or a duration meaning
    "that long ago" (``"24h"``, ``timedelta(hours=24)``)."""
    if value is None:
        return None
    if isinstance(value, _dt.datetime):
        when = value if value.tzinfo else value.replace(tzinfo=_dt.timezone.utc)
        return when.astimezone(_dt.timezone.utc).isoformat().replace("+00:00", "Z")
    if isinstance(value, str) and not _DURATION.match(value):
        return value
    base = now or _dt.datetime.now(_dt.timezone.utc)
    return instant((base - _dt.timedelta(seconds=seconds(value))).replace(microsecond=0))


def _id(value: Any) -> str:
    text = str(value)
    if not text or "/" in text:
        raise ValueError(f"not an id: {value!r}")
    return quote(text, safe="")


def _clean(data: Mapping[str, Any]) -> Dict[str, Any]:
    return {k: v for k, v in data.items() if v is not None}


def subscriptions(
    events: Optional[Sequence[str]], filters: Optional[Mapping[str, Mapping[str, Any]]] = None
) -> Optional[list]:
    """``events=["prompt.label.changed"]`` and ``filters={"prompt.label.changed": {"label_names": [...]}}`` →
    the contract's ``subscriptions`` list (one entry per type; a type's filters apply to it alone)."""
    if events is None:
        if filters:
            raise ValueError("filters need events: name each event type the filters apply to")
        return None
    if isinstance(events, str):
        events = [events]
    unknown = set(filters or {}) - set(events)
    if unknown:
        raise ValueError(f"filters for event types not in events: {sorted(unknown)}")
    return [{"event_type": e, "filters": dict((filters or {}).get(e) or {})} for e in events]


# ---- endpoints ------------------------------------------------------------------------------------------------------


def list_endpoints(*, workspace=None, event_type=None, status=None, kind=None) -> Call:
    params = _clean({"workspace": workspace, "event_type": event_type, "status": status, "kind": kind})
    return Call("GET", f"{PREFIX}/endpoints/", params=params, result="endpoint_list")


def create_endpoint(body: Mapping[str, Any]) -> Call:
    return Call("POST", f"{PREFIX}/endpoints/", json=dict(body), ok=(201,), result="endpoint_created")


def get_endpoint(endpoint_id) -> Call:
    return Call("GET", f"{PREFIX}/endpoints/{_id(endpoint_id)}/", result=t.Endpoint)


def update_endpoint(endpoint_id, body: Mapping[str, Any]) -> Call:
    return Call("PATCH", f"{PREFIX}/endpoints/{_id(endpoint_id)}/", json=dict(body), result=t.Endpoint)


def delete_endpoint(endpoint_id) -> Call:
    return Call("DELETE", f"{PREFIX}/endpoints/{_id(endpoint_id)}/")


def toggle(endpoint_id, on: bool, reason: Optional[str]) -> Call:
    verb = "enable" if on else "disable"
    body = _clean({"reason": reason})
    return Call("POST", f"{PREFIX}/endpoints/{_id(endpoint_id)}/{verb}/", json=body, result=t.Endpoint)


def resume(endpoint_id, mode: str) -> Call:
    if mode not in ("send", "skip"):
        raise ValueError("resume mode is 'send' or 'skip'")
    return Call("POST", f"{PREFIX}/endpoints/{_id(endpoint_id)}/resume/", json={"mode": mode})


def rotate_secret(endpoint_id, overlap, secret: Optional[str]) -> Call:
    body: Dict[str, Any] = {}
    if overlap is not None:
        overlap_s = seconds(overlap)
        if not 0 <= overlap_s <= 7 * 86400:
            raise ValueError("overlap is 0 to 7 days (0 revokes the old secret at once)")
        body["overlap_seconds"] = overlap_s
    if secret is not None:
        body["secret"] = secret
    return Call("POST", f"{PREFIX}/endpoints/{_id(endpoint_id)}/rotate-secret/", json=body, result=t.Rotation)


def revoke_previous_secret(endpoint_id) -> Call:
    return Call("POST", f"{PREFIX}/endpoints/{_id(endpoint_id)}/revoke-previous-secret/", json={})


def test(endpoint_id, event_type: str) -> Call:
    return Call(
        "POST",
        f"{PREFIX}/endpoints/{_id(endpoint_id)}/test/",
        json={"event_type": event_type},
        ok=(200, 202),
        result=t.TestResult,
    )


test.__test__ = False  # type: ignore[attr-defined]  # not a pytest test


# ---- deliveries, events, catalog, policy ----------------------------------------------------------------------------


def list_deliveries(
    *,
    endpoint=None,
    status=None,
    event_type=None,
    event=None,
    subject=None,
    since: When = None,
    until: When = None,
    seq_from=None,
    seq_to=None,
    include_body=None,
    cursor=None,
    limit=None,
) -> Call:
    params = _clean(
        {
            "status": status,
            "event_type": event_type,
            "event": event,
            "subject": subject,
            "since": instant(since),
            "until": instant(until),
            "seq_from": seq_from,
            "seq_to": seq_to,
            "include_body": None if include_body is None else ("true" if include_body else "false"),
            "cursor": cursor,
            "limit": limit,
        }
    )
    path = f"{PREFIX}/endpoints/{_id(endpoint)}/deliveries/" if endpoint else f"{PREFIX}/deliveries/"
    return Call("GET", path, params=params, result=t.Page)


def get_delivery(delivery_id, *, attempts: bool = True) -> Call:
    return Call("GET", f"{PREFIX}/deliveries/{_id(delivery_id)}/", result=t.Record if attempts else "no_attempts")


def redeliver(delivery_id) -> Call:
    return Call("POST", f"{PREFIX}/deliveries/{_id(delivery_id)}/redeliver/", json={}, ok=(200, 202))


def redeliver_many(*, endpoint, status, event_type=None, since: When = None, until: When = None, dry_run=False) -> Call:
    body = _clean(
        {
            "endpoint": str(endpoint),
            "status": status,
            "event_type": event_type,
            "since": instant(since),
            "until": instant(until),
            "dry_run": bool(dry_run),
        }
    )
    return Call("POST", f"{PREFIX}/deliveries/redeliver/", json=body)


def list_events(*, type=None, subject=None, since: When = None, until: When = None, cursor=None, limit=None) -> Call:
    params = _clean(
        {
            "type": type,
            "subject": subject,
            "since": instant(since),
            "until": instant(until),
            "cursor": cursor,
            "limit": limit,
        }
    )
    return Call("GET", f"{PREFIX}/events/", params=params, result=t.Page)


def event_types() -> Call:
    return Call("GET", f"{PREFIX}/event-types/")


def egress_ips() -> Call:
    return Call("GET", f"{PREFIX}/egress-ips/")


def preview(body: Mapping[str, Any]) -> Call:
    return Call("POST", f"{PREFIX}/preview/", json=dict(body))


def get_policy(workspace=None) -> Call:
    path = f"{PREFIX}/policy/workspace/{_id(workspace)}/" if workspace else f"{PREFIX}/policy/"
    return Call("GET", path)


def put_policy(body: Mapping[str, Any], workspace=None) -> Call:
    path = f"{PREFIX}/policy/workspace/{_id(workspace)}/" if workspace else f"{PREFIX}/policy/"
    return Call("PUT", path, json=dict(body))


# ---- responses ------------------------------------------------------------------------------------------------------


def error(status: int, payload: Any, headers: Optional[Mapping[str, str]] = None) -> FutureAGIAPIError:
    """The SDK error for a refusal: the status class of :func:`fi.errors.api_error` (``NotFoundError``,
    ``PermissionDeniedError``, ``RateLimitError``, ...; all ``FutureAGIAPIError``), with ``code`` (``WEBHOOK_*``),
    ``attr`` (the field) and ``detail`` (the server's message) set, and a one-line ``str()``."""
    err = api_error(status, payload, headers)
    body = payload if isinstance(payload, dict) else {}
    code = body.get("code")
    attr = body.get("attr")
    message = body.get("message") or body.get("detail") or body.get("error")
    if not isinstance(message, str):
        message = str(payload)[:500] if payload not in (None, "") else f"HTTP {status}"
    err.code = code  # type: ignore[attr-defined]
    err.attr = attr  # type: ignore[attr-defined]
    err.detail = message  # type: ignore[attr-defined]
    where = f" ({inert(attr, 100)})" if attr else ""
    # one inert line: a server (or a proxy in front of it) may answer with text that would rewrite a terminal or log
    err.custom_message = f"{inert(code, 100) + ': ' if code else ''}{inert(message, 500)}{where} [HTTP {status}]"
    err.args = (err.custom_message,)
    return err


def unwrap(call: Call, status: int, payload: Any) -> Any:
    """The ``result`` of the API's ``{status, result}`` envelope, as the call's result type."""
    result = payload.get("result") if isinstance(payload, dict) and "result" in payload else payload
    if call.result == "endpoint_list":
        return [t.Endpoint(e) for e in (result or {}).get("results", [])]
    if call.result == "endpoint_created":
        ep = t.Endpoint(result["endpoint"], secret=result.get("secret"), warnings=result.get("warnings") or [])
        return ep
    if call.result == "no_attempts":
        return t.Record({k: v for k, v in (result or {}).items() if k != "attempts"})
    if isinstance(result, dict):
        return call.result(result)
    return result
