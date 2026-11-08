"""``futureagi-py doctor``: the host and credential source before any request, then each group's
section (groups add one with ``add_section``, and the arguments it reads with ``add_argument``).
``--json`` prints one object: the local checks, ``who`` (the account the keys belong to, one
request; ``--offline`` skips it) and ``sections`` (title to ``lines`` or ``error``, and ``problems``
when the section found any). With ``FI_EXTRA_HEADERS`` set, a ``Headers`` line (and ``extra_headers``
in ``--json``) names its headers, never a value; a malformed setting is shown there and exits 3.

A section reports a problem by returning a :class:`Problem` line (``doctor.Problem("...")``): it is
printed like any line, listed under the section's ``problems`` in ``--json``, and doctor then exits 3
(the setup exit code) instead of 0. A section that raises is "could not check", not a problem.

Doctor's arguments are **one namespace shared by every group**: a flag another group already
added is left alone (and then shared), and only one positional fits (the experiments group's
``TARGET``). A group should add flags named for itself."""

from __future__ import annotations

import platform
import sys
from typing import Any, Callable

_SECTIONS: list[tuple[str, Callable[[Any], list[str]]]] = []
EXIT_PROBLEM = 3  # the CLI's setup exit code (fi._cli.main.EXIT_SETUP)


class Problem(str):
    """A doctor line that reports a problem (doctor prints it and exits 3)."""


def add_section(title: str, fn: Callable[[Any], list[str]]) -> None:
    if all(t != title for t, _ in _SECTIONS):
        _SECTIONS.append((title, fn))


def local_info() -> dict[str, Any]:
    """What doctor checks before any request, as data (never a key value)."""
    from fi._credentials import login_path, resolve
    from fi._extra_headers import describe as describe_extra_headers

    creds = resolve()
    path = login_path()
    return {
        "server": {"base_url": creds.base_url, "source": creds.base_url_source},
        "keys": {"present": creds.complete, "source": creds.keys_source},
        "platform": {"base_url": creds.platform_base_url, "source": creds.platform_base_url_source},
        "login": {"path": str(path), "exists": path.exists()},
        "python": {
            "version": platform.python_version(),
            "system": platform.system(),
            "machine": platform.machine(),
        },
        "note": creds.login_skipped,
        # FI_EXTRA_HEADERS: the header names only, never a value (or the error, which names no value)
        "extra_headers": describe_extra_headers(),
    }


def local_lines(info: dict[str, Any] | None = None) -> list[str]:
    info = info or local_info()
    server, keys, plat, login, py = (info[k] for k in ("server", "keys", "platform", "login", "python"))
    lines = [
        f"Server     {server['base_url']}  (base URL from {server['source']})",
        f"Keys       {'present' if keys['present'] else 'missing'}  (source: {keys['source']})",
        f"Platform   {plat['base_url']}  (from {plat['source']})",
        f"Login      {login['path']}{'' if login['exists'] else ' (not found)'}",
        f"Python     {py['version']} on {py['system']} {py['machine']}",
    ]
    if info.get("note"):
        lines.append(f"Note       {info['note']}")
    extra = info.get("extra_headers") or {}
    if extra.get("error"):
        lines.append(f"Headers    {extra['error']}")
    elif extra.get("names"):
        lines.append(f"Headers    {', '.join(extra['names'])}  (from {extra['source']}; sent to {server['base_url']} only)")
    return lines


def _section(fn: Callable[[Any], list[str]], args: Any) -> dict[str, Any]:
    try:
        lines = list(fn(args))
    except Exception as exc:  # a section never breaks doctor
        return {"error": f"{type(exc).__name__}: {exc}"}
    out: dict[str, Any] = {"lines": [str(line) for line in lines]}
    problems = [str(line) for line in lines if isinstance(line, Problem)]
    if problems:
        out["problems"] = problems
    return out


def run_doctor(args: Any) -> int:
    out = getattr(args, "stdout", None) or sys.stdout
    from fi._cli.auth import who_info

    info = local_info()
    who = who_info(args)  # the server half: after the local lines say where the request goes
    from fi._cli.ownership import section as ownership_section

    # Core diagnosis cannot depend on optional command-group registration.
    sections = [("Package ownership", _section(ownership_section, args))]
    sections.extend((title, _section(fn, args)) for title, fn in _SECTIONS)
    bad_headers = bool((info.get("extra_headers") or {}).get("error"))
    code = EXIT_PROBLEM if bad_headers or any(result.get("problems") for _, result in sections) else 0
    if getattr(args, "json", False):  # one object: the local checks and each group's section (S3)
        import json

        print(json.dumps({**info, "who": who, "sections": dict(sections)}), file=out)
        return code
    for line in local_lines(info):
        print(line, file=out)
    print(f"Who        {who['line']}", file=out)
    for title, result in sections:
        print(f"\n[{title}]", file=out)
        for line in result.get("lines", []):
            print(line, file=out)
        if "error" in result:
            print(f"  could not check: {result['error']}", file=out)
    return code


def add_argument(subparsers: Any, *flags: str, **kwargs: Any) -> None:
    """Add an argument a group's doctor section reads. Call it inside the group's
    ``register(subparsers)`` with the same ``subparsers``. Without a ``doctor`` command there (a
    group registered on its own, as unit tests do) it does nothing; an argument that is already
    there is left alone."""
    parser = getattr(subparsers, "choices", {}).get("doctor")
    if parser is None:
        return
    dest = kwargs.get("dest") or flags[0].lstrip("-").replace("-", "_")
    if any(action.dest == dest for action in parser._actions):
        return
    parser.add_argument(*flags, **kwargs)


def register(subparsers: Any) -> None:
    p = subparsers.add_parser("doctor", help="check the host, the keys and each command group's setup")
    p.add_argument("--json", action="store_true", help="print one JSON object instead of lines")
    p.add_argument("--offline", action="store_true", help="make no request (skip who you are)")
    p.set_defaults(func=run_doctor)
