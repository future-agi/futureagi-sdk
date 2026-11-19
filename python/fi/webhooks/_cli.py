"""``futureagi-py webhooks``: the command group, registered through the ``futureagi.cli`` entry point.

Only ``argparse`` is imported at module level (a broken group prints one warning and every other command still works);
the handlers live in ``fi.webhooks._cli_run`` and load when a command runs.
"""

import argparse

_EVENTS_HELP = "event type (repeatable): prompt.version.created, prompt.label.changed, deployment.run.completed, " \
    "deployment.run.failed, or a group wildcard prompt.* / deployment.run.*"


def _duration(text: str) -> str:
    """A duration (90s, 30m, 24h, 7d, 2w, or a number of seconds); anything else is a usage error before any request."""
    from fi.webhooks._api import seconds

    try:
        seconds(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None
    return text


def _overlap(text: str) -> str:
    from fi.webhooks._api import seconds

    if not 0 <= seconds(_duration(text)) <= 7 * 86400:
        raise argparse.ArgumentTypeError(f"{text!r} is outside 0 to 7d (0 revokes the old secret at once)")
    return text


def _when(text: str) -> str:
    """A duration ago (24h) or an ISO-8601 time."""
    from fi.webhooks._api import check_when

    try:
        return check_when(text)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from None


def _seconds_float(text: str) -> float:
    import math

    try:
        value = float(text)
    except ValueError:
        value = math.nan
    if not math.isfinite(value) or value <= 0:
        raise argparse.ArgumentTypeError(f"not a number of seconds: {text!r}")
    return value


_ENDPOINT_ID = "the endpoint's id (whep_...; see futureagi-py webhooks list)"


def _add_id(p: argparse.ArgumentParser) -> None:
    p.add_argument("id", metavar="ID", help=_ENDPOINT_ID)


def _add_json(p: argparse.ArgumentParser) -> None:
    p.add_argument("--json", action="store_true", help="print the API's JSON (stable, for CI)")


def _add_secret_output(p: argparse.ArgumentParser) -> None:
    p.add_argument("--secret-out", metavar="FILE",
                   help="write the new signing secret to FILE (mode 0600) and print only its last 4 characters")
    p.add_argument("--show-secret", action="store_true",
                   help="print the signing secret even when stdout is not a terminal (it then lands in logs)")


def _add_endpoint_fields(p: argparse.ArgumentParser, *, create: bool) -> None:
    p.add_argument("--url", required=create, help="the HTTPS URL that receives the events")
    p.add_argument("--event", dest="events", action="append", metavar="TYPE", required=create, help=_EVENTS_HELP)
    p.add_argument("--name", help="a name, unique in the workspace (default: the URL's host)")
    p.add_argument("--description")
    f = p.add_argument_group("filters (applied to every --event they fit)")
    f.add_argument("--prompt", dest="prompt_ids", action="append", metavar="ID", help="only these prompts")
    f.add_argument("--exclude-prompt", dest="exclude_prompt_ids", action="append", metavar="ID")
    f.add_argument("--label", dest="label_names", action="append", metavar="NAME", help="only these labels")
    f.add_argument("--action", dest="actions", action="append", choices=("assigned", "moved", "removed"))
    f.add_argument("--deployment", dest="deployment_ids", action="append", metavar="ID")
    f.add_argument("--environment", dest="environments", action="append", metavar="NAME")
    f.add_argument("--trigger", dest="trigger_kinds", action="append", choices=("api", "cron", "studio", "batch"))
    f.add_argument("--status", dest="statuses", action="append", choices=("failed", "interrupted", "cancelled"),
                   help="deployment.run.failed only")
    h = p.add_argument_group("headers (sent literally; never expanded)")
    h.add_argument("--header", dest="header_args", action="append", metavar="'NAME: VALUE'",
                   help="a static header (visible in shell history and ps; prefer --header-file / --header-env)")
    h.add_argument("--header-file", metavar="FILE", help="read 'Name: value' lines from FILE")
    h.add_argument("--header-env", dest="header_envs", action="append", metavar="NAME=ENVVAR",
                   help="header NAME takes the value of this shell's ENVVAR")
    if not create:
        h.add_argument("--clear-headers", action="store_true", help="remove every static header")
    o = p.add_argument_group("delivery")
    o.add_argument("--payload", choices=("thin", "full"), help="thin (ids, default) or full (prompt text; admins)")
    o.add_argument("--no-names", dest="include_people_names", action="store_false", default=None,
                   help="never put people's display names in bodies")
    if not create:
        o.add_argument("--names", dest="include_people_names", action="store_true",
                       help="put people's display names in bodies again (the default)")
    if create:
        o.add_argument("--accept-run-targeting", action="store_true", default=None,
                       help="let deployment runs target this endpoint by id (admins)")
    else:
        o.add_argument("--accept-run-targeting", dest="accept_run_targeting", action="store_true", default=None)
        o.add_argument("--no-run-targeting", dest="accept_run_targeting", action="store_false")
    o.add_argument("--timeout-s", type=_seconds_float, help="per-attempt deadline, 5-30 s (default 15)")
    o.add_argument("--rate-limit", type=int, metavar="PER_S", help="requests per second, 1-100")
    o.add_argument("--max-in-flight", type=int, help="concurrent requests, 1-16")
    o.add_argument("--max-age", type=_duration, metavar="DURATION",
                   help="give up on a delivery after this long (1h-72h)")
    if create:
        o.add_argument("--workspace", metavar="ID", help="the workspace (default: the key's current workspace)")
        o.add_argument("--org-wide", action="store_true", help="receive events from every workspace (org admins)")


def register(subparsers) -> None:
    from fi._cli import registry

    p = subparsers.add_parser(
        "webhooks",
        prog="futureagi-py webhooks",  # not the root's whole usage line: "usage: futureagi-py webhooks create ..."
        help="signed webhooks: endpoints, test, deliveries, redeliver, secrets, verify",
        description="Manage Future AGI webhook endpoints and their delivery log, and verify signed requests offline. "
        "Exit codes: 0 ok, 1 a test or verification failed, 2 usage, 3 setup or server error, 4 interrupted "
        "(Ctrl-C, or 'no' to a confirmation).",
    )
    sub = p.add_subparsers(dest="webhooks_command", metavar="COMMAND", required=True)

    ls = sub.add_parser("list", aliases=["ls"], help="list endpoints")
    ls.add_argument("--workspace", metavar="ID")
    ls.add_argument("--event", metavar="TYPE")
    ls.add_argument("--status", choices=("enabled", "disabled_manual", "disabled_auto", "blocked_by_policy"))
    ls.add_argument("--kind", choices=("http", "github_dispatch"))
    _add_json(ls)

    get = sub.add_parser("get", aliases=["show"], help="show one endpoint (never its secret)")
    _add_id(get)
    _add_json(get)

    create = sub.add_parser("create", help="create an endpoint; prints its signing secret once")
    _add_endpoint_fields(create, create=True)
    _add_secret_output(create)
    _add_json(create)

    update = sub.add_parser("update", help="change an endpoint (the create flags)")
    _add_id(update)
    _add_endpoint_fields(update, create=False)
    _add_json(update)

    enable = sub.add_parser("enable", help="turn an endpoint on")
    _add_id(enable)
    enable.add_argument("--reason")
    enable.add_argument("--resume", choices=("send", "skip"), help="then deliver or skip its paused deliveries")
    _add_json(enable)

    disable = sub.add_parser("disable", help="turn an endpoint off (new events wait, paused)")
    _add_id(disable)
    disable.add_argument("--reason")
    _add_json(disable)

    test = sub.add_parser("test", help="send a signed test event; exits 1 unless the receiver answers 2xx")
    _add_id(test)
    test.add_argument("--event", metavar="TYPE", help="the event type (default: the endpoint's only subscribed type)")
    test.add_argument("--wait", default="60s", type=_duration, metavar="DURATION",
                      help="how long to wait for the answer (60s)")
    _add_json(test)

    dl = sub.add_parser("deliveries", help="an endpoint's delivery log, newest first")
    _add_id(dl)
    dl.add_argument("--status", choices=("pending", "sending", "retrying", "succeeded", "failed", "paused", "skipped",
                                         "cancelled"))
    dl.add_argument("--event", metavar="TYPE")
    dl.add_argument("--since", type=_when, metavar="DURATION|TIME", help="24h, 30m, 7d or an ISO time")
    dl.add_argument("--until", type=_when, metavar="DURATION|TIME")
    dl.add_argument("--seq", metavar="N|N-M", help="one sequence number or a range (recover a gap)")
    dl.add_argument("--limit", type=int, default=20, help="1-100 (20)")
    dl.add_argument("--cursor", help="the next_cursor of a previous page")
    _add_json(dl)

    one = sub.add_parser("delivery", help="one delivery")
    one.add_argument("id", metavar="DLV", help="the delivery's id (dlv_...; see futureagi-py webhooks deliveries ID)")
    one.add_argument("--attempts", action="store_true", help="with its attempt timeline")
    _add_json(one)

    rd = sub.add_parser("redeliver", help="send deliveries again (same event id, fresh signature)")
    rd.add_argument("ids", nargs="*", metavar="DLV",
                    help="delivery ids to send again, one request each (the bulk flags go with --endpoint instead)")
    rd.add_argument("--endpoint", metavar="ID", help="bulk: every matching delivery of this endpoint")
    rd.add_argument("--status", choices=("failed", "succeeded", "skipped"), help="bulk filter")
    rd.add_argument("--event", metavar="TYPE", help="bulk filter")
    rd.add_argument("--since", type=_when, metavar="DURATION|TIME")
    rd.add_argument("--until", type=_when, metavar="DURATION|TIME")
    rd.add_argument("--dry-run", action="store_true", help="bulk: only count")
    rd.add_argument("--yes", action="store_true", help="bulk: do not ask for confirmation")
    _add_json(rd)

    rot = sub.add_parser("rotate-secret", help="a new signing secret; the old one keeps working for --overlap")
    _add_id(rot)
    rot.add_argument("--overlap", default=None, type=_overlap, metavar="DURATION",
                     help="0 to 7d (24h); 0 revokes the old one now")
    _add_secret_output(rot)
    _add_json(rot)

    rp = sub.add_parser("revoke-previous-secret", help="end a rotation overlap now")
    _add_id(rp)
    _add_json(rp)

    rm = sub.add_parser("delete", aliases=["rm"], help="delete an endpoint (asks first)")
    _add_id(rm)
    rm.add_argument("--yes", action="store_true", help="do not ask for confirmation")
    _add_json(rm)

    ev = sub.add_parser("events", help="the event catalog, one type's JSON Schema, or the events list")
    ev.add_argument("--schema", metavar="TYPE", help="print this type's JSON Schema")
    ev.add_argument("--list", action="store_true", help="the events list (reconciliation)")
    ev.add_argument("--type", metavar="TYPE", help="with --list")
    ev.add_argument("--since", type=_when, metavar="DURATION|TIME", help="with --list")
    ev.add_argument("--until", type=_when, metavar="DURATION|TIME", help="with --list")
    ev.add_argument("--limit", type=int, default=20, help="with --list: 1-100 (20)")
    ev.add_argument("--cursor", help="with --list: the next_cursor of a previous page")
    _add_json(ev)

    vf = sub.add_parser("verify", help="check a recorded request offline (no network)")
    vf.add_argument("--secret-file", metavar="FILE",
                    help="a file holding the whsec_ secret (default: the FI_WEBHOOK_SECRET environment variable)")
    vf.add_argument("--headers-file", metavar="FILE", required=True,
                    help="the request headers: a JSON object, or 'Name: value' lines (an HTTP dump works)")
    vf.add_argument("--body-file", metavar="FILE", required=True, help="the raw request body, byte for byte")
    vf.add_argument("--tolerance-s", type=int, default=300, help="accepted clock difference (300)")
    vf.add_argument("--now", type=int, metavar="UNIX_S", help="judge the timestamp as of this time (recorded requests)")
    _add_json(vf)

    for parser in sub.choices.values():
        parser.set_defaults(func=_run)
    registry.set_section("webhooks", "platform")


def _run(args) -> int:
    from fi.webhooks import _cli_run

    return _cli_run.dispatch(args)
