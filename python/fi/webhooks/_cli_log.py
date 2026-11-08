"""``futureagi-py webhooks`` handlers for the delivery log, redelivery, the event catalog and offline ``verify``."""

from __future__ import annotations

import json
import os
import sys
from typing import Dict, Optional

from fi.webhooks import _cli_io as io
from fi.webhooks._cli_io import EXIT_OK, UsageError


# ---- deliveries and events ------------------------------------------------------------------------------------------


def _seq(value: Optional[str]) -> Dict[str, int]:
    if not value:
        return {}
    lo, sep, hi = value.partition("-")
    try:
        a, b = int(lo), int(hi) if sep else int(lo)
    except ValueError:
        raise UsageError(f"--seq takes N or N-M, not {io.inert(repr(value))}") from None
    if a < 1 or b < a:
        raise UsageError(f"--seq {io.inert(value)}: need 1 <= N <= M")
    return {"seq_from": a, "seq_to": b}


def _deliveries(wh, args) -> int:
    page = wh.deliveries.list(endpoint=args.id, status=args.status, event_type=args.event, since=args.since,
                              until=args.until, limit=args.limit, cursor=args.cursor, **_seq(args.seq))
    if args.json:
        io.print_json(page)
        return EXIT_OK
    rows = []
    for d in page["results"]:
        last = d.get("last_attempt") or {}
        rows.append([d["id"], d["event_type"], d.get("seq") or ("test" if d.get("is_test") else "-"), d["status"],
                     d["attempts_count"], last.get("response_status") or last.get("outcome") or "-"])
    if rows:
        io.table(rows, ["delivery", "event", "seq", "status", "attempts", "last"])
    else:
        print("No deliveries match.", file=sys.stderr)
    if page.get("next_cursor"):
        print(f"more: --cursor {io.inert(page['next_cursor'])}", file=sys.stderr)
    return EXIT_OK


def _delivery(wh, args) -> int:
    d = wh.deliveries.get(args.id)
    if args.json:
        io.print_json(d if args.attempts else {k: v for k, v in d.items() if k != "attempts"})
        return EXIT_OK
    i = io.inert
    print(f"{i(d['id'])}  {i(d['event_type'])}  event {i(d['event_id'])}  {i(d['status'])}  "
          f"attempts {i(d['attempts_count'])}"
          + (f"  seq {i(d['seq'])}" if d.get("seq") else "  (test)" if d.get("is_test") else ""))
    if args.attempts:
        for a in d.get("attempts") or []:
            fields = [str(a.get(k)) for k in ("n", "started_at", "trigger", "outcome", "response_status")
                      if a.get(k) is not None]
            if a.get("duration_ms") is not None:
                fields.append(f"{a['duration_ms']} ms")
            print("  " + "  ".join(io.inert(f, 60) for f in fields))
            if a.get("response_body_excerpt"):
                print(f"     response: {io.inert(a['response_body_excerpt'], 300)}")
            if a.get("error_detail"):
                print(f"     detail: {io.inert(a['error_detail'], 300)}")
    return EXIT_OK


def _redeliver(wh, args) -> int:
    if args.ids and args.endpoint:
        raise UsageError("pass delivery ids, or --endpoint with filters for a bulk redelivery, not both")
    stray = [f for f in ("status", "event", "since", "until", "dry_run", "yes") if getattr(args, f, None)]
    if args.ids and stray:  # with ids they would be silently ignored: refuse them, as events refuses --list's flags
        raise UsageError(f"--{stray[0].replace('_', '-')} goes with --endpoint (bulk redelivery), not with delivery "
                         "ids. Nothing was queued.")
    if args.ids:
        out = []
        for delivery_id in args.ids:  # one request each; a line per queued id, so a later refusal leaves them shown
            r = wh.deliveries.redeliver(delivery_id)
            out.append(r)
            if not args.json:
                print(f"Queued {io.inert(r['delivery_id'])} (attempt {io.inert(r['attempt'])})", flush=True)
        if args.json:
            io.print_json({"results": out})
        return EXIT_OK
    if not args.endpoint or not args.status:
        raise UsageError("bulk redelivery needs --endpoint ID and --status (or pass delivery ids)")
    query = dict(endpoint=args.endpoint, status=args.status, event_type=args.event, since=args.since, until=args.until)
    count = wh.deliveries.redeliver_many(dry_run=True, **query)
    if args.dry_run:
        if args.json:
            io.print_json(count)
        else:
            print(f"{io.inert(count['count'])} deliveries match ({io.inert(count['expired'])} without a kept body); "
                  "nothing queued")
        return EXIT_OK
    if count["count"] == 0:
        print("No deliveries match; nothing queued.", file=sys.stderr)
        if args.json:
            io.print_json(count)
        return EXIT_OK
    if not io.confirm(f"Redeliver {io.inert(count['count'])} deliveries of {io.inert(args.endpoint)}?", yes=args.yes):
        print("Nothing queued.", file=sys.stderr)
        return io.EXIT_INTERRUPTED
    out = wh.deliveries.redeliver_many(dry_run=False, **query)
    if args.json:
        io.print_json(out)
    else:
        print(f"Queued {io.inert(out['queued'])} of {io.inert(out['count'])} ({io.inert(out['expired'])} without a "
              "kept body)")
    return EXIT_OK


def _events(wh, args) -> int:
    if args.list:
        page = wh.events.list(type=args.type, since=args.since, until=args.until, limit=args.limit,
                              cursor=args.cursor)
        if args.json:
            io.print_json(page)
            return EXIT_OK
        if page["results"]:
            io.table([[e["id"], e["type"], e["timestamp"], e.get("subject") or "-", e["delivery_count"]]
                      for e in page["results"]], ["event", "type", "time", "subject", "deliveries"])
        else:
            print("No events match.", file=sys.stderr)
        if page.get("next_cursor"):
            print(f"more: --cursor {io.inert(page['next_cursor'])}", file=sys.stderr)
        return EXIT_OK
    stray = [f for f in ("type", "since", "until", "cursor") if getattr(args, f, None)]
    if stray:
        raise UsageError(f"--{stray[0]} goes with --list")
    catalog = wh.event_types()
    if args.schema:
        found = [t for t in catalog["results"] if t["type"] == args.schema]
        if not found:
            raise UsageError(f"unknown event type {io.inert(repr(args.schema))}; one of "
                             f"{io.inert(', '.join(str(t['type']) for t in catalog['results']), 500)}")
        io.print_json(found[0]["schema"])
        return EXIT_OK
    if args.json:
        io.print_json(catalog)
    else:
        io.table([[t["type"], t["group"], ",".join(t["filters"]), t["description"]] for t in catalog["results"]],
                 ["type", "group", "filters", "description"])
    return EXIT_OK


# ---- verify (offline) -----------------------------------------------------------------------------------------------


def _read_headers(path: str) -> Dict[str, str]:
    try:
        with open(path, "rb") as fh:
            raw = fh.read().decode("utf-8", "replace")
    except OSError as exc:
        raise UsageError(f"cannot read --headers-file {io.inert(path, 300)}: {exc.strerror}") from None
    text = raw.strip()
    if text.startswith("{"):
        try:
            data = json.loads(text)
        except ValueError as exc:
            raise UsageError(f"--headers-file {io.inert(path, 300)} is not valid JSON: {io.inert(exc)}") from None
        return {str(k): str(v) for k, v in data.items()}
    out: Dict[str, str] = {}
    for line in raw.splitlines():
        if not line.strip() or line.startswith(("HTTP/", "POST ", "PUT ", "GET ")):
            continue
        name, sep, value = line.partition(":")
        if sep:
            out.setdefault(name.strip(), value.strip())
    return out


def _verify(args) -> int:
    from fi.webhooks.verify import WebhookSecretError, WebhookVerificationError, verify

    if args.secret_file:
        try:
            with open(args.secret_file, encoding="utf-8") as fh:
                secret = fh.read().strip()
        except OSError as exc:
            raise UsageError(f"cannot read --secret-file {io.inert(args.secret_file, 300)}: {exc.strerror}") from None
    else:
        secret = os.environ.get("FI_WEBHOOK_SECRET", "").strip()
        if not secret:
            raise UsageError("pass --secret-file FILE or set FI_WEBHOOK_SECRET (never the secret itself on the "
                             "command line)")
    try:
        with open(args.body_file, "rb") as fh:
            body = fh.read()
    except OSError as exc:
        raise UsageError(f"cannot read --body-file {io.inert(args.body_file, 300)}: {exc.strerror}") from None
    headers = _read_headers(args.headers_file)
    try:
        event = verify(body=body, headers=headers, secret=secret, tolerance_s=args.tolerance_s, now=args.now)
    except WebhookSecretError as exc:
        raise UsageError(f"the secret is malformed: {exc}") from None
    except WebhookVerificationError as exc:
        if args.json:
            io.print_json({"verified": False, "reason": exc.reason, "message": str(exc)})
        else:
            print(f"not verified: {exc.reason}: {exc}", file=sys.stderr)
        return io.EXIT_FAILED
    if args.json:
        io.print_json({"verified": True, "id": event.get("id"), "type": event.get("type"),
                       "test": bool(event.get("test"))})
    else:
        print(f"verified: {io.inert(event.get('id'))}  {io.inert(event.get('type'))}"
              + ("  (test)" if event.get("test") else ""))
    return EXIT_OK
