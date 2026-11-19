"""Handlers of ``futureagi-py webhooks``. Each command calls the SDK client; output is a short
human form, or the API's JSON with ``--json``. Receiver-supplied text (response excerpts) prints as inert text."""

from __future__ import annotations

import sys
import time
from typing import Any, Dict

from fi._extra_headers import ExtraHeadersError
from fi.webhooks import _cli_io as io
from fi.webhooks._cli_io import EXIT_OK, UsageError

_TERMINAL = ("succeeded", "failed", "skipped", "cancelled")


def _client(args: Any):
    from fi.webhooks import Webhooks

    return Webhooks()


def dispatch(args: Any) -> int:
    name = {"ls": "list", "show": "get", "rm": "delete"}.get(args.webhooks_command, args.webhooks_command)
    from fi.webhooks import _cli_log

    if name == "verify":
        return _cli_log._verify(args)
    handler = globals().get("_" + name.replace("-", "_")) or getattr(_cli_log, "_" + name)
    with _client(args) as wh:
        try:
            return handler(wh, args)
        except ExtraHeadersError:  # FI_EXTRA_HEADERS is malformed: a setup error (exit 3), not a usage error
            raise
        except ValueError as exc:  # the client's own argument checks, before any request: a usage error, not a trace
            raise UsageError(str(exc)) from exc


def _endpoint_line(ep: Dict[str, Any]) -> str:
    events = ",".join(s["event_type"] for s in ep.get("subscriptions") or [])
    return f"{ep['id']}  {ep['name']}  {ep.get('url') or ep.get('url_host')}  {events}  {ep['status']}"


def _describe(ep: Dict[str, Any]) -> None:
    health = ep.get("health") or {}
    lines = [
        ("id", ep["id"]),
        ("name", ep["name"]),
        ("url", ep.get("url") or f"{ep.get('url_host')} (the full URL is shown to workspace admins)"),
        ("status", ep["status"] + (f" ({ep['disabled_reason']})" if ep.get("disabled_reason") else "")),
        ("scope", "org-wide" if ep.get("org_wide") else f"workspace {ep.get('workspace_id')}"),
        ("events", ", ".join(s["event_type"] for s in ep.get("subscriptions") or [])),
        ("payload", ep.get("payload_mode")),
        ("last answer", f"{health.get('last_status_code')} {health.get('last_outcome') or ''}".strip()
         if health else "none yet"),
    ]
    if ep.get("header_names"):
        lines.append(("headers", ", ".join(ep["header_names"])))
    for s in ep.get("secrets") or []:
        expiry = f", stops working {s['expires_at']}" if s.get("expires_at") else ""
        lines.append(("secret", f"…{s['tail']} {s['state']}{expiry}"))
    width = max(len(k) for k, _ in lines)
    for key, value in lines:
        print(f"{key.ljust(width)}  {io.inert(value, 300)}")


# ---- endpoints ------------------------------------------------------------------------------------------------------


def _list(wh, args) -> int:
    eps = wh.endpoints.list(workspace=args.workspace, event_type=args.event, status=args.status, kind=args.kind)
    if args.json:
        io.print_json({"results": eps})
        return EXIT_OK
    if not eps:
        print("No webhook endpoints.", file=sys.stderr)
        return EXIT_OK
    rows = []
    for ep in eps:
        health = ep.get("health") or {}
        last = health.get("last_status_code") or health.get("last_outcome") or "-"
        rows.append([ep["id"], ep["name"], ep.get("url_host"), ",".join(s["event_type"] for s in ep["subscriptions"]),
                     ep["status"], last])
    io.table(rows, ["id", "name", "host", "events", "status", "last answer"])
    return EXIT_OK


def _get(wh, args) -> int:
    ep = wh.endpoints.get(args.id)
    if args.json:
        io.print_json(ep)
    else:
        _describe(ep)
    return EXIT_OK


def _fields(args, *, create: bool) -> Dict[str, Any]:
    events = args.events
    fields: Dict[str, Any] = {
        "url": args.url,
        "events": events,
        "name": args.name,
        "description": args.description,
        "headers": io.headers_from_args(args),
        "payload": args.payload,
        "include_people_names": args.include_people_names,
        "accepts_run_targeting": args.accept_run_targeting,
        "timeout_s": args.timeout_s,
        "rate_limit_per_s": args.rate_limit,
        "max_in_flight": args.max_in_flight,
        "max_age": args.max_age,
    }
    if not events and any(getattr(args, f, None) for f in io.FILTER_FLAGS):
        raise UsageError("filter flags need --event (they replace the endpoint's subscriptions)")
    fields["filters"] = io.filters_from_args(args, events or [])
    return {k: v for k, v in fields.items() if v is not None}


def _create(wh, args) -> int:
    fields = _fields(args, create=True)
    if args.org_wide and args.workspace:
        raise UsageError("use --workspace ID or --org-wide, not both")
    sink = io.SecretSink(args)  # refuses before any request when the secret has nowhere safe to go
    try:
        ep = wh.endpoints.create(org_wide=args.org_wide, **({"workspace_id": args.workspace} if args.workspace else {}),
                                 **fields)
    except BaseException:
        sink.abandon()
        raise
    shown = sink.deliver(ep.get("secret"), ep.get("id"))
    data = {k: v for k, v in ep.items() if k != "secret"}
    if args.json:
        io.print_json({"endpoint": {k: v for k, v in data.items() if k != "warnings"}, "warnings": ep["warnings"],
                       **shown})
        return EXIT_OK
    print(f"Created {io.inert(ep['id'])} ({io.inert(ep['name'])}) for {io.inert(', '.join(fields['events']), 500)}",
          file=sys.stderr)
    for w in ep.get("warnings") or []:
        print(f"warning: {io.inert(w.get('message'), 500)}", file=sys.stderr)
    print(sink.note(shown) if shown["secret_file"] else shown["secret"])  # deliver() checked it: whsec_ + base64
    return EXIT_OK


def _update(wh, args) -> int:
    fields = _fields(args, create=False)
    if args.clear_headers and "headers" in fields:
        raise UsageError("use --clear-headers or header flags, not both")
    if not fields and not args.clear_headers:
        raise UsageError("nothing to update: pass the flags to change (see futureagi-py webhooks update --help)")
    ep = wh.endpoints.update(args.id, clear_headers=args.clear_headers, **fields)
    if args.json:
        io.print_json(ep)
    else:
        print(f"Updated {io.inert(ep['id'])}", file=sys.stderr)
        _describe(ep)
    return EXIT_OK


def _enable(wh, args) -> int:
    out = wh.endpoints.enable(args.id, reason=args.reason, resume=args.resume)
    if args.json:
        io.print_json(out)
    elif args.resume:
        print(f"Enabled {io.inert(args.id)}; paused deliveries: {io.inert(out['sent'])} sent, "
              f"{io.inert(out['skipped'])} skipped, {io.inert(out['past_max_age'])} past their max age")
    else:
        print(f"Enabled {io.inert(out['id'])} ({io.inert(out['status'])})")
    return EXIT_OK


def _disable(wh, args) -> int:
    ep = wh.endpoints.disable(args.id, reason=args.reason)
    if args.json:
        io.print_json(ep)
    else:
        print(f"Disabled {io.inert(ep['id'])} ({io.inert(ep['status'])}); new events wait as paused deliveries")
    return EXIT_OK


def _pick_event(wh, endpoint_id: str) -> str:
    ep = wh.endpoints.get(endpoint_id)
    concrete = [s["event_type"] for s in ep.get("subscriptions") or [] if "*" not in s["event_type"]]
    if len(concrete) == 1:
        return concrete[0]
    names = ", ".join(s["event_type"] for s in ep.get("subscriptions") or []) or "none"
    raise UsageError(f"pass --event TYPE (this endpoint subscribes to: {io.inert(names, 500)})")


def _test(wh, args) -> int:
    from fi.webhooks._api import seconds

    wait_s = seconds(args.wait)
    event_type = args.event or _pick_event(wh, args.id)
    started = time.monotonic()
    result = dict(wh.endpoints.test(args.id, event_type=event_type))
    while result.get("outcome") is None and time.monotonic() - started < wait_s:
        time.sleep(1.0)
        if not result.get("delivery_id"):  # the worker had not fanned the test out yet: find it by its event
            found = wh.deliveries.list(endpoint=args.id, event=result.get("event_id"), limit=1)["results"]
            result["delivery_id"] = found[0]["id"] if found else None
            if not found:
                continue
        d = wh.deliveries.get(result["delivery_id"])
        if d["status"] in _TERMINAL:
            last = (d.get("attempts") or [None])[-1] or {}
            result.update(status_code=last.get("response_status"), outcome=last.get("outcome") or d["status"],
                          latency_ms=last.get("duration_ms"), response_excerpt=last.get("response_body_excerpt"))
    code, outcome = result.get("status_code"), result.get("outcome")
    passed = outcome == "success" and isinstance(code, int) and 200 <= code < 300
    if args.json:
        io.print_json({**result, "event_type": event_type, "passed": passed})
    elif outcome is None:
        print(f"Test {io.inert(result.get('event_id'))} still sending after {io.inert(args.wait)} "
              f"(delivery {io.inert(result.get('delivery_id'))})")
    else:
        print(f"{io.inert(event_type)}  -> {io.inert(code if code is not None else '-')} {io.inert(outcome)} in "
              f"{io.inert(result.get('latency_ms'))} ms  {io.inert(result.get('delivery_id'))}")
        if result.get("response_excerpt"):
            print(f"response: {io.inert(result['response_excerpt'], 500)}")
    if outcome is None:
        print(f"error: the test delivery did not settle within {io.inert(args.wait)}", file=sys.stderr)
        return io.EXIT_FAILED
    if not passed:
        print(f"error: the receiver answered {io.inert(code if code is not None else outcome)}, not 2xx",
              file=sys.stderr)
        return io.EXIT_FAILED
    return EXIT_OK


_test.__test__ = False  # type: ignore[attr-defined]


def _rotate_secret(wh, args) -> int:
    sink = io.SecretSink(args)
    try:
        rot = wh.endpoints.rotate_secret(args.id, overlap=args.overlap)
    except BaseException:
        sink.abandon()
        raise
    shown = sink.deliver(rot.get("secret"), args.id)
    prev = rot.get("previous") or None
    if args.json:
        io.print_json({**{k: v for k, v in rot.items() if k != "secret"}, **shown})
        return EXIT_OK
    if prev:
        print(f"The previous secret (…{io.inert(prev.get('tail'))}) keeps working until "
              f"{io.inert(prev.get('expires_at'))}", file=sys.stderr)
    for tail in rot.get("revoked_tails") or []:
        print(f"The secret …{io.inert(tail)} stopped working now", file=sys.stderr)
    print(sink.note(shown) if shown["secret_file"] else shown["secret"])  # deliver() checked it: whsec_ + base64
    return EXIT_OK


def _revoke_previous_secret(wh, args) -> int:
    out = wh.endpoints.revoke_previous_secret(args.id)
    if args.json:
        io.print_json(out)
    else:
        tails = ", ".join("…" + t for t in out.get("revoked_tails") or []) or "none (no overlap was running)"
        print(f"Revoked: {io.inert(tails, 500)}")
    return EXIT_OK


def _delete(wh, args) -> int:
    if not args.yes:
        if not io._isatty(sys.stdin):
            raise UsageError("delete needs confirmation: pass --yes (stdin is not a terminal). Nothing was deleted.")
        ep = wh.endpoints.get(args.id)
        if not io.confirm(f"Delete webhook endpoint {io.inert(ep['name'])} ({io.inert(ep['id'])})?", yes=False):
            print("Not deleted.", file=sys.stderr)
            return io.EXIT_INTERRUPTED
    out = wh.endpoints.delete(args.id)
    if args.json:
        io.print_json(out)
    else:
        print(f"Deleted {io.inert(args.id)}; {io.inert(out.get('cancelled_deliveries', 0))} waiting deliveries "
              "cancelled")
    return EXIT_OK
