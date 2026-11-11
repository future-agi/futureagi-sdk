"""``futureagi-py sandbox``: hosted sandboxes from the command line (contract v1 section 5, v2 item 6).

Registered by one line of ``python/pyproject.toml`` (``[tool.poetry.plugins."futureagi.cli"]``:
``sandbox = "fi._cli.sandbox"``), so it is ``futureagi-py sandbox`` today. The owner's name,
``futureagi sandbox``, needs the console-script rename (``scripts/packaging/rename-cli.py
futureagi``) with ``sandbox`` in that script's ``COMMANDS`` and the group's sub-commands (``exec``,
``cp``, ``cat``, ``mv``, ``mkdir``, ``snapshot``, ``restore``, ``hibernate``, ``settings``,
``network-policy``, ``set``) in its ``RESERVED_NAMES``; without that the rename drops this group.
The group lives here rather than in ``fi/sandbox/`` because
importing that package loads the HTTP client: this module imports only ``argparse`` when it is
loaded, and a command imports ``fi.sandbox`` when it runs, so ``--help`` stays fast and a broken
install costs only this group (``fi/_cli/README.md``).

Every command calls the ``Sandbox`` handle (``fi.sandbox``) or the generated layer under it
(``client.sandboxes``); none builds a request itself, and none retries what the handle does not.

Settings come from the environment, as for ``Sandbox.create`` (contract section 2, v2 items 1-2):
``--base-url`` or ``OMEGA_BASE_URL`` (no default host); ``FI_API_KEY`` + ``FI_SECRET_KEY`` (hosted)
or ``FUTUREAGI_OMEGA_API_KEY`` (self-hosted EE), never both; ``FI_WORKSPACE_ID`` /
``FI_ORGANIZATION_ID`` sent as the mode's scope headers. A saved ``login`` is not used (the
refusal for a missing credential says so). The key pair goes only to a Future AGI host (HTTPS in
the ``futureagi.com`` zone) or to loopback, and a self-host token only to loopback, unless
``--allow-custom-base-url`` (the command-line form of ``allow_custom_base_url``) is passed: a
``--base-url`` copied from a document cannot send the exported keys anywhere else. For an
``OMEGA_BASE_URL`` from the environment, ``FI_ALLOW_CUSTOM_PLATFORM_URL=1`` also lets the key pair
go to another host, as for ``Sandbox.create``; it never applies to ``--base-url``. Either prints the
core's one-time notice.

Output: ``--format text`` (the default) is for people. ``--format json`` (or ``--json``) prints the
API record: the list response for ``list``; the sandbox record for ``create``, ``get``,
``hibernate``, ``resume``, ``delete`` and ``snapshot restore``; the file, entry, snapshot,
settings and policy records for the others (``network-policy`` adds the ``etag``); ``cp`` out of a
sandbox prints ``{"from", "to", "bytes"}``. ``exec --format json`` prints each output frame
(``{"event", "id", "data"}``) as one JSON line as it arrives, the exit frame last.

Exit codes: ``exec`` exits with the command's own code; 124 when it ran out of time; 128+N when
signal N ended it (Linux numbering: the sandbox runs Linux); 130 when it was cancelled, including by
Ctrl-C, which cancels it (``commands.cancel``); 1 when the server failed after it started, it could
not start, or the stream ended or broke without an exit record (the message says whether it
finished is unknown). Every other command: 0 done, 1 refused (``code: message`` on stderr), 2 a
usage or configuration problem (no base URL, both credentials, a bad flag). These codes are the one
table in ``fi.sandbox.types`` (``exit_status``, ``LINUX_SIGNALS``), imported when a command runs.

Every next step a message suggests is a command to type, built by :func:`_command` from the
program name (the root parser's prog) and this group's words: ``futureagi-py sandbox resume ID``.
"""

from __future__ import annotations

import argparse

GROUP = "sandbox"
SIZES = ("small", "medium", "large", "xl")

_DESCRIPTION = """\
Run commands and keep files in hosted sandboxes: isolated computers in your workspace.

Settings come from the environment:
  OMEGA_BASE_URL             where the sandbox API is (or pass --base-url). Hosted:
                             https://<gateway-host>/omega/api. Self-hosted: your EE's
                             address with its port. There is no default. Your keys go
                             only to Future AGI hosts (futureagi.com, HTTPS) or loopback
                             unless you pass --allow-custom-base-url.
  FI_API_KEY, FI_SECRET_KEY  your Future AGI API key pair (hosted), or
  FUTUREAGI_OMEGA_API_KEY    an EE account key (self-hosted). Set one, not both.
  FI_WORKSPACE_ID            optional: the workspace to use.
  FI_ORGANIZATION_ID         optional: the organization to use.
A saved `login` is not used here: export the variables."""

_EPILOG = """\
examples:
  %(prog)s create --name scratch
  %(prog)s exec SANDBOX_ID -- python3 -c "print('hello')"
  %(prog)s cp ./data.csv SANDBOX_ID:data.csv
  %(prog)s cp SANDBOX_ID:results.json ./results.json
  %(prog)s delete SANDBOX_ID

exit codes: 0 done; 1 refused by the server (it prints "code: message"); 2 a usage or
configuration problem. exec exits with the command's own code: 124 when it ran out of
time, 128+N when signal N ended it, 130 when it was cancelled (Ctrl-C cancels it), and 1
when the server failed or it is unknown whether the command finished."""

_EXEC_USAGE = "%(prog)s [options] SANDBOX_ID -- COMMAND..."
_EXEC_EPILOG = """\
examples:
  %(prog)s SANDBOX_ID -- ls -la
  %(prog)s --cwd src SANDBOX_ID -- python3 app.py
  %(prog)s SANDBOX_ID -- "echo $HOME | wc -c"

Put the command after --: words after it are the command's, not this tool's options."""
#: exec's own options that take a value (the pre-parse check skips them and their value).
_EXEC_VALUED = ("--cwd", "--env", "--timeout", "--base-url", "--format")
#: exec's own options that take none (the pre-parse check skips them).
_EXEC_FLAGS = ("--json", "--allow-custom-base-url")
_SETTING = "OMEGA_BASE_URL (or --base-url)"
_NO_LOGIN = " (a saved login is not read by sandbox commands: export the variables)"
#: The program name and this group as typed, set by register() from the root parser's prog.
_PROG = ["futureagi-py sandbox"]


def _command(*words: str) -> str:
    """A command to type: the program name, ``sandbox`` and ``words``. Every next step any
    message here names is built with this, so none can show argparse's usage text."""
    return " ".join((_PROG[0],) + words)


_CLI_HINT = (
    "pass --allow-custom-base-url if this is your EE, or reach it on a loopback address (for "
    "example through an SSH tunnel to http://127.0.0.1:PORT); in Python: "
    "FutureAGIClient(platform_token=..., platform_base_url=..., allow_custom_base_url=True)"
)
#: What a refusal of the key pair to another host says, for an address typed here and for
#: OMEGA_BASE_URL.
_KEYS_HINT = ("pass --allow-custom-base-url to send them to that host. A self-hosted server takes "
              "FUTUREAGI_OMEGA_API_KEY instead")
_ENV_KEYS_HINT = ("pass --allow-custom-base-url (or set FI_ALLOW_CUSTOM_PLATFORM_URL=1) to send them "
                  "to that host. A self-hosted server takes FUTUREAGI_OMEGA_API_KEY instead")


class _Usage(Exception):
    """A usage problem found after argparse (exit 2), printed as ``code: message``."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


# ---------------------------------------------------------------------------------------------
# Arguments


def _positive(text: str) -> int:
    try:
        value = int(text)
    except ValueError:
        value = 0
    if value <= 0:
        raise argparse.ArgumentTypeError(f"expected a whole number above 0, got {text!r}")
    return value


def _env_pair(text: str) -> tuple:
    name, sep, value = text.partition("=")
    if not sep or not name:
        raise argparse.ArgumentTypeError(f"expected NAME=VALUE, got {text!r}")
    return name, value


def _add_globals(parser: argparse.ArgumentParser, *, nested: bool) -> None:
    """``--base-url`` and ``--format`` before or after the command (a nested copy sets nothing
    unless given, so it never undoes the group-level value)."""
    parser.add_argument(
        "--base-url", metavar="URL", default=argparse.SUPPRESS if nested else None,
        help="where the sandbox API is (default: $OMEGA_BASE_URL); your keys go only to Future "
             "AGI hosts (futureagi.com, HTTPS) or loopback unless --allow-custom-base-url is given",
    )
    parser.add_argument(
        "--allow-custom-base-url", action="store_true",
        default=argparse.SUPPRESS if nested else False,
        help="send the credentials to a host outside Future AGI's and loopback: a self-hosted "
             "EE, or a host you trust (prints a notice)",
    )
    parser.add_argument(
        "--format", choices=("text", "json"), default=argparse.SUPPRESS if nested else "text",
        help="text for people (the default) or json: the API's record",
    )
    parser.add_argument(
        "--json", dest="format", action="store_const", const="json", default=argparse.SUPPRESS,
        help="the same as --format json",
    )


def _add_id(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("id", metavar="SANDBOX_ID", help="the sandbox's id (see the list command)")


def _exec_needs_dashes(argv: list):
    """Pre-parse: ``sandbox exec ID ls -la`` without ``--`` would fail with the top-level usage;
    say where the command goes instead (exit 2). Anything else is left to argparse."""
    import sys

    words = [word for word in argv if not word.startswith("-")]
    if words[:1] != [GROUP] or "--" in argv:
        return None
    rest = argv[argv.index(GROUP) + 1:]
    if "exec" not in rest:
        return None
    rest, seen, index = rest[rest.index("exec") + 1:], [], 0
    while index < len(rest):
        word = rest[index]
        if word in _EXEC_VALUED:
            index += 2
            continue
        if word.split("=", 1)[0] in _EXEC_VALUED or word in _EXEC_FLAGS:
            index += 1
            continue
        if word in ("-h", "--help"):
            return None
        if word.startswith("-") and seen:
            from fi.sandbox.types import EXIT_USAGE  # only now: this hook runs for every command

            example = _command("exec", seen[0], "--", *(seen[1:] + rest[index:]))
            print(f"usage: {_command('exec', '[options]', 'SANDBOX_ID', '--', 'COMMAND...')}\n"
                  f"exec_usage: put the command after --, for example: {example}", file=sys.stderr)
            return EXIT_USAGE
        if not word.startswith("-"):
            seen.append(word)
        index += 1
    return None


def register(subparsers) -> None:
    from fi._cli import registry

    group = subparsers.add_parser(
        GROUP,
        help="Hosted sandboxes: run commands, copy files, take snapshots",
        description=_DESCRIPTION,
        epilog=_EPILOG,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    # argparse names a sub-parser after the root's whole usage line ("futureagi-py [-h] [--version]
    # COMMAND ... sandbox"), whose first word is the root parser's prog (an executable name has no
    # space: scripts/packaging/rename-cli.py). Every prog below, every "usage:" line, the %(prog)s
    # examples and every next step use "<prog> sandbox", set before any sub-parser is added.
    group.prog = _PROG[0] = f"{group.prog.split(' ', 1)[0]} {GROUP}"
    _add_globals(group, nested=False)
    common = argparse.ArgumentParser(add_help=False)
    _add_globals(common, nested=True)
    commands = group.add_subparsers(dest="sandbox_command", metavar="COMMAND", title="commands")
    commands.required = True
    registry.add_pre_parse(_exec_needs_dashes)

    def add(parent, name: str, text: str, run=None, **kw) -> argparse.ArgumentParser:
        parser = parent.add_parser(
            name, help=text, description=text[0].upper() + text[1:] + ".", parents=[common], **kw
        )
        if run is not None:
            parser.set_defaults(func=_main, sandbox_run=run)
        return parser

    add(commands, "list", "list the sandboxes in your workspace", _list)

    p = add(commands, "create", "create a sandbox and print its id", _create)
    p.add_argument("--name", help="a name to recognise it by")
    p.add_argument("--template", help="start from this template id (the settings command lists them)")
    p.add_argument("--size", choices=SIZES, help="how much CPU and memory it gets")
    p.add_argument("--idle-ttl", type=_positive, metavar="SECONDS",
                   help="hibernate it after this many seconds without activity")

    _add_id(add(commands, "get", "show one sandbox", _get))

    p = add(commands, "exec", "run a command in a sandbox and stream its output", _exec,
            usage=_EXEC_USAGE, epilog=_EXEC_EPILOG, formatter_class=argparse.RawDescriptionHelpFormatter)
    _add_id(p)
    p.add_argument("--cwd", metavar="DIR", help="the folder to run in (relative to the sandbox's files)")
    p.add_argument("--env", action="append", type=_env_pair, metavar="NAME=VALUE",
                   help="set a variable for the command (repeatable; plain values, never secrets)")
    p.add_argument("--timeout", type=_positive, metavar="SECONDS",
                   help="stop the command after this many seconds (it then exits 124)")
    # dest "words", not "command": the core parser keeps the top-level command name in args.command
    p.add_argument("words", nargs="+", metavar="COMMAND",
                   help="the command, after --. One quoted string runs as written (pipes and && "
                        "work); several words are each quoted for you")

    p = add(commands, "cp", "copy a file into or out of a sandbox", _cp)
    p.add_argument("source", metavar="FROM", help="a local file, or SANDBOX_ID:PATH in a sandbox")
    p.add_argument("destination", metavar="TO",
                   help="SANDBOX_ID:PATH in a sandbox (a PATH ending in / keeps the file's name), "
                        "or a local file or folder")

    p = add(commands, "ls", "list a folder in a sandbox", _ls)
    _add_id(p)
    p.add_argument("path", nargs="?", default=".", help="the folder (default: the top folder)")

    p = add(commands, "cat", "print a file from a sandbox", _cat)
    _add_id(p)
    p.add_argument("path", help="the file")
    p.add_argument("--max-bytes", type=_positive, metavar="N", help="print at most N bytes")

    p = add(commands, "rm", "delete a file (or, with -r, a folder) in a sandbox", _rm)
    _add_id(p)
    p.add_argument("path", help="the file or folder")
    p.add_argument("-r", "--recursive", action="store_true", help="delete a folder and everything in it")

    p = add(commands, "mv", "move or rename a file or folder in a sandbox", _mv)
    _add_id(p)
    p.add_argument("src", metavar="FROM", help="the current path")
    p.add_argument("dst", metavar="TO", help="the new path")

    p = add(commands, "mkdir", "create a folder (and any missing parents) in a sandbox", _mkdir)
    _add_id(p)
    p.add_argument("path", help="the folder")

    snapshot = add(commands, "snapshot", "save a sandbox's files, list the saves, or restore one")
    snapshots = snapshot.add_subparsers(dest="snapshot_command", metavar="COMMAND", title="commands")
    snapshots.required = True
    _add_id(add(snapshots, "create", "save the sandbox's files now and print the snapshot's id",
                _snapshot_create))
    _add_id(add(snapshots, "list", "list the sandbox's snapshots", _snapshot_list))
    p = add(snapshots, "restore",
            "make a NEW sandbox from a snapshot and print its id (the original is unchanged)",
            _snapshot_restore)
    _add_id(p)
    p.add_argument("snapshot_id", metavar="SNAPSHOT_ID", help="the snapshot (see snapshot list)")

    _add_id(add(commands, "hibernate",
                "stop a sandbox's computer but keep its files (resume starts it again)", _hibernate))
    _add_id(add(commands, "resume", "start a hibernated sandbox again", _resume))
    _add_id(add(commands, "delete", "delete a sandbox and its files for good", _delete))
    add(commands, "settings", "show the workspace's sandbox templates, sizes and limits", _settings)

    policy = add(commands, "network-policy", "show or replace a sandbox's network policy")
    policies = policy.add_subparsers(dest="policy_command", metavar="COMMAND", title="commands")
    policies.required = True
    _add_id(add(policies, "get", "show the sandbox's network policy and its ETag", _policy_get))
    p = add(policies, "set", "replace the sandbox's network policy with the JSON in a file", _policy_set)
    _add_id(p)
    p.add_argument("--file", required=True, metavar="FILE",
                   help="the policy as a JSON object (- reads it from standard input)")
    p.add_argument("--if-match", metavar="ETAG",
                   help="change it only if it is still at this ETag (default: read the current "
                        "one first)")

    registry.set_section(GROUP, "platform")


# ---------------------------------------------------------------------------------------------
# Running a command


class _Output:
    def __init__(self, args: argparse.Namespace) -> None:
        self.json = getattr(args, "format", "text") == "json"

    def record(self, value) -> None:
        import json

        print(json.dumps(value, indent=2, ensure_ascii=False, default=str))

    def json_line(self, value) -> None:
        import json
        import sys

        sys.stdout.write(json.dumps(value, ensure_ascii=False, default=str) + "\n")
        sys.stdout.flush()

    def line(self, text: str = "") -> None:
        print(text)

    def note(self, text: str) -> None:
        import sys

        print(text, file=sys.stderr)

    def refusal(self, code: str, message: str) -> None:
        import sys

        print(f"{code}: {message}", file=sys.stderr)

    def table(self, rows: list) -> None:
        cells = [[_show(cell) for cell in row] for row in rows]
        widths = [max(len(row[i]) for row in cells) for i in range(len(cells[0]))]
        for row in cells:
            print("  ".join(cell.ljust(width) for cell, width in zip(row, widths)).rstrip())


def _show(value) -> str:
    """One value as plain text: scalars as they are, lists of names joined, objects as JSON."""
    import json

    if value is None:
        return "-"
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (str, int, float)):
        return str(value)
    if isinstance(value, list):
        names = [item.get("name") or item.get("id") if isinstance(item, dict) else item for item in value]
        if all(isinstance(name, (str, int, float)) for name in names):
            return ", ".join(str(name) for name in names) or "-"
    return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)


def _code(error: BaseException) -> str:
    code = getattr(error, "code", None)
    if isinstance(code, str) and code:
        return code
    get = getattr(error, "get_error_code", None)
    return get().lower() if callable(get) else type(error).__name__


def _main(args: argparse.Namespace) -> int:
    from fi.sandbox.types import EXIT_USAGE

    out = _Output(args)
    try:
        return int(_dispatch(args, out))
    except _Usage as problem:
        out.refusal(problem.code, problem.message)
        return EXIT_USAGE


def _open(args: argparse.Namespace):
    """``client.sandboxes`` for the environment's settings, with ``--base-url`` in place of
    ``OMEGA_BASE_URL``; the environment itself is never changed."""
    import os

    from fi.sandbox import Sandboxes
    from fi.sandbox._connection import BASE_URL_ENV, OriginRule, SandboxConnection

    env = dict(os.environ)
    typed = getattr(args, "base_url", None) is not None
    base = args.base_url if typed else env.get(BASE_URL_ENV, "")
    if not base.strip():
        raise _Usage(
            "missing_base_url",
            f"no sandbox address: pass --base-url URL or set {BASE_URL_ENV} (hosted: "
            "https://<gateway-host>/omega/api; self-hosted: your EE's address with its port). "
            "There is no default.",
        )
    env[BASE_URL_ENV] = base
    flag = bool(getattr(args, "allow_custom_base_url", False))
    # A typed address takes the keys off Future AGI's hosts only with the flag: the variable that
    # allows it for OMEGA_BASE_URL never applies to a --base-url copied from a document.
    allow = True if flag else (False if typed else None)
    hint = _KEYS_HINT if typed else _ENV_KEYS_HINT
    core = SandboxConnection(environ=env, allow_custom_base_url=allow, keys_hint=hint).core()
    rule = OriginRule(allow_custom_base_url=flag, hint=_CLI_HINT, setting=_SETTING)
    return Sandboxes(core, rule=rule), core


def _dispatch(args: argparse.Namespace, out: _Output) -> int:
    from fi import errors
    from fi.sandbox.types import EXIT_REFUSED, EXIT_USAGE

    try:
        api, core = _open(args)
    except errors.ConfigurationError as error:
        out.refusal(_code(error), _configuration(error))
        return EXIT_USAGE
    try:
        return args.sandbox_run(args, api, out)
    except errors.ConfigurationError as error:
        out.refusal(_code(error), _configuration(error))
        return EXIT_USAGE
    except errors.FutureAGIError as error:
        code = _code(error)
        out.refusal(code, _said(error) + _next_step(error, code, args, core))
        return EXIT_REFUSED
    finally:
        core.shared.close()


def _configuration(error: BaseException) -> str:
    text = str(error)
    return text + _NO_LOGIN if getattr(error, "code", None) == "missing_credentials" else text


def _said(error: BaseException) -> str:
    """The server's words without the SDK's ``<operation> failed with status N (code):``."""
    import re

    text = str(error)
    found = re.match(r"[\w.]+ failed with status (\d+) \([^)]*\)(?:: )?", text)
    if found:
        text = text[found.end():] or f"refused with status {found.group(1)}"
    return text.rstrip(". ")


def _next_step(error: BaseException, code: str, args, core) -> str:
    """One short clause saying what to do next, by class (empty when there is nothing to add)."""
    from fi import sandbox as sb

    sandbox_id = getattr(args, "id", None)
    if isinstance(error, sb.SandboxHibernatedError) and sandbox_id:
        return f". It is hibernated; start it first with: {_command('resume', sandbox_id)}"
    if code == "network_policy_revision_mismatch" and sandbox_id:
        return (f". The policy changed since it was read; see it with: "
                f"{_command('network-policy', 'get', sandbox_id)}, then try again")
    if isinstance(error, sb.RateLimitError):
        wait = error.retry_after_seconds
        return f". Try again in {wait:g} s" if wait is not None else ". Try again shortly"
    if isinstance(error, sb.AuthenticationError):
        bearer = core.shared.origin().mode == "bearer"
        sent = "FUTUREAGI_OMEGA_API_KEY" if bearer else "FI_API_KEY and FI_SECRET_KEY"
        return (f". The server did not accept {sent}: check them, and that OMEGA_BASE_URL (or "
                "--base-url) is the deployment they belong to")
    if isinstance(error, sb.PermissionDeniedError):
        return ". Check FI_WORKSPACE_ID (the workspace you act in) and your role there"
    if isinstance(error, sb.NotFoundError) and sandbox_id:
        if getattr(args, "sandbox_command", None) in ("ls", "cat", "rm", "mv", "mkdir", "cp"):
            return f". Check the path, and the sandbox id with: {_command('list')}"
        if getattr(args, "snapshot_id", None):
            return f". Check the snapshot id with: {_command('snapshot', 'list', sandbox_id)}"
        return (f". No sandbox {sandbox_id} here (one in another workspace also answers 404): "
                f"check the id with: {_command('list')}, and FI_WORKSPACE_ID")
    if isinstance(error, sb.InsufficientStorageError):
        return ". Free some space: delete files (rm) or sandboxes you no longer need"
    if code == "download_too_large":
        return " (cp keeps this limit; copy a larger file from Python with that argument)"
    return ""


def _handle(api, sandbox_id: str):
    """The ``Sandbox`` handle on ``sandbox_id`` (no read first: the call itself says 404)."""
    from fi.sandbox import Sandbox

    return Sandbox(api, {"id": sandbox_id})


# ---------------------------------------------------------------------------------------------
# Sandboxes


def _list(args, api, out: _Output) -> int:
    from fi.sandbox.types import EXIT_OK

    raw = api.list()
    if out.json:
        out.record(raw)
        return EXIT_OK
    rows = raw.get("sandboxes") or []
    if not rows:
        out.note(f"No sandboxes yet. Create one with: {_command('create', '--name', 'NAME')}")
        return EXIT_OK
    header = ("ID", "NAME", "STATE", "SIZE", "LAST ACTIVE")
    out.table([header] + [
        (row.get("id"), row.get("name"), row.get("state"), row.get("size"), row.get("lastActivityAt"))
        for row in rows
    ])
    return EXIT_OK


def _create(args, api, out: _Output) -> int:
    from fi.sandbox.types import EXIT_OK

    fields = {"name": args.name, "template": args.template, "size": args.size,
              "idleTtlSeconds": args.idle_ttl}
    sbx = api.create(body={key: value for key, value in fields.items() if value is not None})
    if out.json:
        out.record(sbx.info)
    else:
        out.line(sbx.id)
    return EXIT_OK


_FIELDS = (
    ("id", "ID"), ("name", "Name"), ("state", "State"), ("template", "Template"), ("size", "Size"),
    ("image", "Image"), ("network", "Network"), ("idleTtlSeconds", "Idle timeout (seconds)"),
    ("createdAt", "Created"), ("lastActivityAt", "Last active"), ("hibernatesAt", "Hibernates at"),
    ("restoredFrom", "Restored from"),
)


def _get(args, api, out: _Output) -> int:
    from fi.sandbox.types import EXIT_OK

    info = api.connect(args.id).info
    if out.json:
        out.record(info)
        return EXIT_OK
    width = max(len(label) for _, label in _FIELDS) + 1
    for key, label in _FIELDS:
        if key in info and info[key] is not None:
            out.line(f"{label + ':':<{width}} {_show(info[key])}")
    return EXIT_OK


def _state_change(name: str):
    def run(args, api, out: _Output) -> int:
        from fi.sandbox.types import EXIT_OK

        record = getattr(_handle(api, args.id), name)()
        if out.json:
            out.record(record)
        elif name == "delete":
            out.line(f"Deleted {args.id}.")
        else:
            out.line(f"{record.get('id', args.id)}: {record.get('state', '-')}")
        return EXIT_OK

    run.__name__ = f"_{name}"
    return run


_hibernate = _state_change("hibernate")
_resume = _state_change("resume")


def _delete(args, api, out: _Output) -> int:
    """Delete through the generated layer: a 404 on the first attempt is a refusal (no such
    sandbox here), and only a 404 on a retry (the first attempt deleted it) counts as done."""
    from fi.sandbox.types import EXIT_OK

    raw = api.kill(args.id)
    record = (raw or {}).get("sandbox") or {"id": args.id, "state": "destroyed"}
    if out.json:
        out.record(record)
    else:
        out.line(f"Deleted {args.id}.")
    return EXIT_OK


def _ids(items):
    """The values a flag takes (``--template``, ``--size``): each item's id, with its name after
    it when that differs (``python-data (Python data)``)."""
    if not isinstance(items, list):
        return items
    shown = []
    for item in items:
        if isinstance(item, dict) and item.get("id") is not None:
            ident, name = str(item["id"]), item.get("name")
            shown.append(f"{ident} ({name})" if name and name != ident else ident)
        else:
            shown.append(item)
    return shown


def _settings(args, api, out: _Output) -> int:
    from fi.sandbox.types import EXIT_OK

    raw = api.settings.get()
    if out.json:
        out.record(raw)
        return EXIT_OK
    caps = raw.get("caps") or {}
    rows = (
        ("Templates", _ids(caps.get("templates"))), ("Default template", caps.get("defaultTemplate")),
        ("Sizes", _ids(caps.get("sizes"))), ("Default size", caps.get("defaultSize")),
        ("Network modes", _ids(caps.get("networkModes"))), ("Default network", caps.get("defaultNetwork")),
        ("Most active sandboxes", caps.get("maxActiveSandboxes")),
        ("Idle timeout (seconds)", caps.get("idleTtlSeconds")),
    )
    width = max(len(label) for label, _ in rows) + 1
    for label, value in rows:
        out.line(f"{label + ':':<{width}} {_show(value)}")
    out.note("These are changed in the Console, signed in as an owner or admin.")
    return EXIT_OK


# ---------------------------------------------------------------------------------------------
# exec


def _command_text(words: list) -> str:
    import shlex

    words = list(words)
    if words and words[0] == "--":
        words = words[1:]
    if not words:
        raise _Usage("invalid_arguments", "give the command to run after --, for example: "
                                          "exec SANDBOX_ID -- ls -la")
    return words[0] if len(words) == 1 else shlex.join(words)


def _exit_status(frame, out: _Output) -> int:
    """The exit code for an ``exit`` frame (v2 item 6): the number is ``fi.sandbox.types``'s
    table; this only says why."""
    from fi.sandbox.types import exit_status, signal_number

    if frame.truncated and not out.json:
        out.note("note: the server dropped some of the output (it was longer than the server keeps)")
    if frame.cancelled:
        if not out.json:
            out.note("cancelled: the command was cancelled")
    elif frame.timed_out:
        if not out.json:
            out.note("timed out: the command ran past its time limit and was stopped")
    elif frame.error:
        out.refusal("spawn_failed", f"the command could not start: {frame.error}")
    elif frame.exit_code is not None:
        pass
    elif frame.signal and signal_number(frame.signal) is None:
        out.refusal("unknown_signal", f"the command was ended by signal {frame.signal}, "
                                      "whose number is not known here")
    elif frame.signal:
        if not out.json:
            out.note(f"the command was ended by signal {frame.signal}")
    else:
        out.refusal("invalid_exit_record", "the exit record has neither an exit code nor a signal")
    return exit_status(frame)


def _cancel(sbx, stream, out: _Output) -> int:
    """Ctrl-C: cancel the running command, then the stream closes; exit 130."""
    from fi import errors
    from fi.sandbox.types import EXIT_CANCELLED

    exec_id = stream.exec_id
    if exec_id is None:
        out.note("\nStopped before the command started. If it did start, closing the connection "
                 "stops it.")
        return EXIT_CANCELLED
    out.note(f"\nCancelling the command ({exec_id})...")
    try:
        sbx.commands.cancel(exec_id)
    except KeyboardInterrupt:
        out.note("Stopped waiting for the cancel; closing the connection stops the command too.")
    except errors.FutureAGIError as error:
        out.note(f"The cancel request failed ({_code(error)}: {error}); closing the connection "
                 "stops the command too.")
    else:
        out.note("Cancelled.")
    return EXIT_CANCELLED


def _exec(args, api, out: _Output) -> int:
    import sys

    from fi.sandbox import ErrorFrame, ExitFrame, StderrFrame, StdoutFrame
    from fi.sandbox.types import EXIT_REFUSED

    command = _command_text(args.words)
    sbx = _handle(api, args.id)
    env = dict(args.env) if args.env else None
    stream = sbx.commands.stream(command, cwd=args.cwd, env=env, timeout_seconds=args.timeout)
    with stream:
        try:
            for frame in stream:
                if out.json:
                    out.json_line(frame.raw)
                elif isinstance(frame, (StdoutFrame, StderrFrame)):
                    target = sys.stdout if isinstance(frame, StdoutFrame) else sys.stderr
                    target.write(frame.data)
                    target.flush()
                if isinstance(frame, ExitFrame):
                    return _exit_status(frame, out)
                if isinstance(frame, ErrorFrame):
                    out.refusal("command_failed", f"the server failed while the command ran "
                                                  f"({frame.message}); whether it finished is unknown")
                    return EXIT_REFUSED
        except KeyboardInterrupt:
            return _cancel(sbx, stream, out)
    out.refusal("command_incomplete", "the output ended without an exit record; whether the "
                                      "command finished is unknown")
    return EXIT_REFUSED


# ---------------------------------------------------------------------------------------------
# Files


def _remote(text: str):
    """``(sandbox_id, path)`` for ``SANDBOX_ID:PATH``, or None for a local path (a one-letter
    prefix is a Windows drive, and a prefix with a slash is a local folder)."""
    head, sep, tail = text.partition(":")
    if not sep or len(head) < 2 or "/" in head or "\\" in head:
        return None
    return head, tail


def _inside(folder: str, sandbox_id: str, path: str) -> str:
    """Where ``SANDBOX_ID:PATH`` lands in the local ``folder``: the last part of ``path``, with
    both ``/`` and ``\\`` as separators on every system. A name that is empty, ``.`` or ``..``,
    names a drive or is absolute, or resolves outside ``folder`` (a link there pointing out) is
    refused before anything is sent or written: a script may copy names a sandbox listed."""
    import ntpath
    import os
    import re

    name = os.path.normpath(re.split(r"[\\/]", path)[-1] or ".")
    target = os.path.join(folder, name)
    unsafe = name in (".", "..") or bool(ntpath.splitdrive(name)[0])
    unsafe = unsafe or os.path.isabs(name) or ntpath.isabs(name)
    if not unsafe:
        base, real = os.path.realpath(folder), os.path.realpath(target)
        try:
            unsafe = real == base or os.path.commonpath([base, real]) != base
        except ValueError:  # another drive, or a device name
            unsafe = True
    if unsafe:
        raise _Usage("unsafe_file_name", f"{sandbox_id}:{path} has no file name that can be written "
                                         f"inside {folder}; name the local file: "
                                         f"{_command('cp', f'{sandbox_id}:{path}', 'LOCAL_FILE')}")
    return target


def _cp(args, api, out: _Output) -> int:
    import os
    from pathlib import Path

    from fi.sandbox.types import EXIT_OK, EXIT_REFUSED

    source, destination = _remote(args.source), _remote(args.destination)
    if (source is None) == (destination is None):
        raise _Usage("invalid_arguments", "cp copies between this computer and a sandbox: write "
                                          "the sandbox side as SANDBOX_ID:PATH and the other as a "
                                          "local path")
    args.id = (destination or source)[0]  # for the refusal's next step (resume, list)
    if destination is not None:
        sandbox_id, path = destination
        local = args.source
        if not os.path.isfile(local):
            raise _Usage("local_file_not_found", f"{local} is not a file on this computer (cp "
                                                 "copies one file at a time)")
        if not path or path.endswith("/"):
            path += os.path.basename(local)
        try:
            raw = _handle(api, sandbox_id).files.upload(path, Path(local))
        except OSError as error:
            out.refusal("local_file_error", f"cannot read {local}: {error.strerror or error}")
            return EXIT_REFUSED
        record = raw.get("file", raw) if isinstance(raw, dict) else raw
        if out.json:
            out.record(record)
        else:
            size = record.get("bytes", os.path.getsize(local)) if isinstance(record, dict) else "?"
            out.line(f"Copied {local} to {sandbox_id}:{path} ({size} bytes).")
        return EXIT_OK
    sandbox_id, path = source
    if not path or path.endswith("/"):
        raise _Usage("invalid_arguments", f"name the file to copy after the colon, for example "
                                          f"{sandbox_id}:results.json")
    local = args.destination
    if os.path.isdir(local):
        local = _inside(local, sandbox_id, path)
    try:
        target = _handle(api, sandbox_id).files.download_to(path, local)
    except OSError as error:
        out.refusal("local_file_error", f"cannot write {local}: {error.strerror or error}")
        return EXIT_REFUSED
    size = os.path.getsize(target)
    if out.json:
        out.record({"from": f"{sandbox_id}:{path}", "to": target, "bytes": size})
    else:
        out.line(f"Copied {sandbox_id}:{path} to {target} ({size} bytes).")
    return EXIT_OK


def _ls(args, api, out: _Output) -> int:
    from fi.sandbox.types import EXIT_OK

    entries = _handle(api, args.id).files.list(args.path)
    if out.json:
        out.record(entries)
        return EXIT_OK
    for entry in entries:
        name = str(entry.get("name", "?")) + ("/" if entry.get("directory") else "")
        size = "-" if entry.get("directory") else _show(entry.get("size"))
        out.line(f"{size:>12}  {name}")
    return EXIT_OK


def _cat(args, api, out: _Output) -> int:
    import base64
    import sys

    from fi.sandbox.types import EXIT_OK

    raw = api.files.read(args.id, args.path, max_bytes=args.max_bytes)
    file = raw.get("file") or {}
    if out.json:
        out.record(file)
        return EXIT_OK
    content = file.get("content") or ""
    if file.get("encoding") == "base64":
        data = base64.b64decode(content)
        sys.stdout.flush()
        buffer = getattr(sys.stdout, "buffer", None)
        if buffer is not None:
            buffer.write(data)
            buffer.flush()
        else:
            sys.stdout.write(data.decode("utf-8", "replace"))
    else:
        sys.stdout.write(content)
        sys.stdout.flush()
    if file.get("truncated"):
        out.note(f"\nnote: the file is longer than what was printed. Copy all of it with: "
                 f"{_command('cp', f'{args.id}:{args.path}', 'LOCAL_FILE')}")
    return EXIT_OK


def _rm(args, api, out: _Output) -> int:
    from fi.sandbox.types import EXIT_OK

    raw = _handle(api, args.id).files.remove(args.path, recursive=args.recursive)
    if out.json:
        out.record(raw.get("deleted", raw))
    else:
        out.line(f"Deleted {args.id}:{args.path}.")
    return EXIT_OK


def _mv(args, api, out: _Output) -> int:
    from fi.sandbox.types import EXIT_OK

    raw = _handle(api, args.id).files.move(args.src, args.dst)
    if out.json:
        out.record(raw.get("moved", raw))
    else:
        out.line(f"Moved {args.src} to {args.dst} in {args.id}.")
    return EXIT_OK


def _mkdir(args, api, out: _Output) -> int:
    from fi.sandbox.types import EXIT_OK

    raw = _handle(api, args.id).files.make_dir(args.path)
    if out.json:
        out.record(raw.get("folder", raw))
    else:
        out.line(f"Created the folder {args.id}:{args.path}.")
    return EXIT_OK


# ---------------------------------------------------------------------------------------------
# Snapshots


def _snapshot_create(args, api, out: _Output) -> int:
    from fi.sandbox.types import EXIT_OK

    record = _handle(api, args.id).snapshots.create()
    if out.json:
        out.record(record)
    else:
        out.line(_show(record.get("id")))
    return EXIT_OK


def _snapshot_list(args, api, out: _Output) -> int:
    from fi.sandbox.types import EXIT_OK

    records = _handle(api, args.id).snapshots.list()
    if out.json:
        out.record(records)
        return EXIT_OK
    if not records:
        out.note(f"No snapshots yet. Save one with: {_command('snapshot', 'create', args.id)}")
        return EXIT_OK
    out.table([("ID", "CREATED", "KIND")] + [
        (record.get("id"), record.get("createdAt"), record.get("kind")) for record in records
    ])
    return EXIT_OK


def _snapshot_restore(args, api, out: _Output) -> int:
    from fi.sandbox.types import EXIT_OK

    restored = _handle(api, args.id).snapshots.restore(args.snapshot_id)
    if out.json:
        out.record(restored.info)
    else:
        out.line(restored.id)
    return EXIT_OK


# ---------------------------------------------------------------------------------------------
# Network policy


def _policy_record(info) -> dict:
    return {"etag": info.etag, "policy": info.policy}


def _policy_get(args, api, out: _Output) -> int:
    import json

    from fi.sandbox.types import EXIT_OK

    info = _handle(api, args.id).network_policy.get()
    if out.json:
        out.record(_policy_record(info))
        return EXIT_OK
    policy = info.policy
    out.line(f"ETag: {info.etag or '-'}  (pass it to network-policy set --if-match)")
    out.line(f"Apply status: {_show(policy.get('applyStatus'))} (desired revision "
             f"{_show(policy.get('desiredRevision'))}, applied revision "
             f"{_show(policy.get('appliedRevision'))})")
    if policy.get("reason"):
        out.line(f"Reason: {_show(policy.get('reason'))}")
    out.line("Policy:")
    out.line(json.dumps(policy.get("desired"), indent=2, ensure_ascii=False, sort_keys=True))
    return EXIT_OK


def _read_policy(name: str) -> dict:
    import json
    import sys

    try:
        if name == "-":
            text = sys.stdin.read()
        else:
            with open(name, encoding="utf-8") as handle:
                text = handle.read()
    except OSError as error:
        raise _Usage("local_file_not_found", f"cannot read {name}: {error.strerror or error}") from None
    try:
        policy = json.loads(text)
    except ValueError as error:
        raise _Usage("invalid_policy_file", f"{name} is not valid JSON ({error})") from None
    if not isinstance(policy, dict):
        raise _Usage("invalid_policy_file", f"{name} must hold one JSON object, for example "
                                            '{"mode": "allow-list", "allow": [...]}')
    return policy


def _policy_set(args, api, out: _Output) -> int:
    from fi.sandbox.types import EXIT_OK

    policy = _read_policy(args.file)
    info = _handle(api, args.id).network_policy.set(policy, if_match=args.if_match)
    if out.json:
        out.record(_policy_record(info))
    else:
        out.line(f"Saved the network policy. ETag: {info.etag or '-'}; apply status: "
                 f"{_show(info.policy.get('applyStatus'))}.")
    return EXIT_OK
