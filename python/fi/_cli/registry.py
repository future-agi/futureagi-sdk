"""The command-group registry for the one ``futureagi-py`` binary.

A command group is a module with ``register(subparsers) -> None`` that imports only ``argparse``
at module level. Groups are listed under the entry-point group ``futureagi.cli`` in a
distribution's ``pyproject.toml``::

    [tool.poetry.plugins."futureagi.cli"]
    example = "example_commands"

A group that fails to load prints one warning naming it; every other command still works.

In a source checkout (``fi`` on ``PYTHONPATH``, no installed metadata) the same table is read from
``python/pyproject.toml``, so nothing here names a group.

Hooks: a group's ``register()`` may add

- ``add_pre_parse(fn)``: ``fn(argv) -> int | None`` sees the raw argv before argparse; an int
  ends the command with that exit code;
- ``add_on_interrupt(fn)``: ``fn(exc, argv) -> str | None`` is the message Ctrl-C prints (the
  first hook that answers wins; the default is ``Interrupted.``);
- ``add_on_exit(fn)``: ``fn(code)`` runs after the command, in the console script only.

A hook that raises is skipped with one warning, like a broken group.

Sections: ``futureagi-py --help`` lists registered commands under **Evaluate**, **Platform**
and **Setup** (``doctor``, ``login``). Only installed groups appear. A group puts each of its
commands in one with ``set_section(name, "evaluate" | "platform" | "setup")``; a command without
one is listed under "Other".
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Optional, Sequence

GROUP = "futureagi.cli"
_TABLE_HEADERS = (
    '[tool.poetry.plugins."futureagi.cli"]',
    "[tool.poetry.plugins.'futureagi.cli']",
    '[project.entry-points."futureagi.cli"]',
    "[project.entry-points.'futureagi.cli']",
)

PreParseHook = Callable[[list], Optional[int]]
InterruptHook = Callable[[BaseException, Sequence[str]], Optional[str]]
ExitHook = Callable[[int], None]

SECTIONS = (("evaluate", "Evaluate"), ("platform", "Platform"), ("setup", "Setup"))
_SECTION_OF: dict[str, str] = {}

_PRE_PARSE: list[PreParseHook] = []
_ON_INTERRUPT: list[InterruptHook] = []
_ON_EXIT: list[ExitHook] = []


def _warn_default(msg: str) -> None:
    print(msg, file=sys.stderr)


class _EP:
    def __init__(self, name: str, value: str) -> None:
        self.name = name
        self.value = value

    def load(self) -> Any:
        return importlib.import_module(self.value)


def source_tree_groups(pyproject: Optional[Path] = None) -> dict[str, str]:
    """The ``futureagi.cli`` table of ``python/pyproject.toml`` next to this package (a source
    checkout), or ``{}`` when there is none (an installed wheel). Only that one table is read."""
    path = pyproject or Path(__file__).resolve().parents[2] / "pyproject.toml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return {}
    groups: dict[str, str] = {}
    inside = False
    for raw in text.splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("["):
            inside = line.replace(" ", "") in _TABLE_HEADERS
            continue
        if inside and "=" in line:
            name, value = (part.strip().strip("\"'") for part in line.split("=", 1))
            if name and value:
                groups[name] = value
    return groups


def entry_points() -> list[Any]:
    try:
        from importlib.metadata import entry_points as eps

        found = list(eps(group=GROUP))
    except Exception:
        found = []
    names = {ep.name for ep in found}
    found += [_EP(name, value) for name, value in source_tree_groups().items() if name not in names]
    return sorted(found, key=lambda ep: ep.name)


def load_groups(
    subparsers: Any,
    *,
    eps: Optional[Iterable[Any]] = None,
    warn: Callable[[str], None] = _warn_default,
) -> list[str]:
    loaded: list[str] = []
    for ep in eps if eps is not None else entry_points():
        try:
            module = ep.load()
            register = getattr(module, "register")
            register(subparsers)
        except Exception as exc:  # one broken group never takes the CLI down
            warn(f"futureagi-py: command group {ep.name!r} could not be loaded ({type(exc).__name__}: {exc}); "
                 "the other commands still work")
            continue
        loaded.append(ep.name)
    return loaded


def add_pre_parse(fn: PreParseHook) -> None:
    if fn not in _PRE_PARSE:
        _PRE_PARSE.append(fn)


def add_on_interrupt(fn: InterruptHook) -> None:
    if fn not in _ON_INTERRUPT:
        _ON_INTERRUPT.append(fn)


def add_on_exit(fn: ExitHook) -> None:
    if fn not in _ON_EXIT:
        _ON_EXIT.append(fn)


def _hook_failed(kind: str, fn: Any, exc: BaseException, warn: Callable[[str], None]) -> None:
    name = getattr(fn, "__qualname__", repr(fn))
    warn(f"futureagi-py: {kind} hook {name} failed ({type(exc).__name__}: {exc}); ignored")


def run_pre_parse(argv: Sequence[str], warn: Callable[[str], None] = _warn_default) -> Optional[int]:
    for fn in list(_PRE_PARSE):
        try:
            code = fn(list(argv))
        except Exception as exc:
            _hook_failed("pre-parse", fn, exc, warn)
            continue
        if code is not None:
            return int(code)
    return None


def interrupt_message(
    exc: BaseException, argv: Sequence[str], warn: Callable[[str], None] = _warn_default
) -> Optional[str]:
    for fn in list(_ON_INTERRUPT):
        try:
            message = fn(exc, argv)
        except Exception as err:
            _hook_failed("interrupt", fn, err, warn)
            continue
        if message:
            return message
    return None


def run_on_exit(code: int, warn: Callable[[str], None] = _warn_default) -> None:
    for fn in list(_ON_EXIT):
        try:
            fn(code)
        except Exception as exc:
            _hook_failed("exit", fn, exc, warn)


def set_section(command: str, section: str) -> None:
    """List ``command`` under ``section`` (``evaluate``, ``platform`` or ``setup``) in ``--help``."""
    if section not in dict(SECTIONS):
        raise ValueError(f"unknown help section {section!r}; one of {[key for key, _ in SECTIONS]}")
    _SECTION_OF[command] = section


def command_rows(subparsers: Any) -> list[tuple[str, str, str]]:
    """``(name, label, help)`` for each top-level command, in registration order.

    It reads ``subparsers.choices``, not only argparse's help rows: a command added without
    ``help=`` has no help row, and would otherwise be missing from ``futureagi-py --help`` (S4).
    Aliases are shown in the label (``name (alias)``). ``help=argparse.SUPPRESS`` hides a command."""
    import argparse

    helps = {a.dest: a.help for a in getattr(subparsers, "_choices_actions", [])}
    names_of: dict[int, list[str]] = {}
    parsers: list[Any] = []
    for name, parser in getattr(subparsers, "choices", {}).items():
        if id(parser) not in names_of:
            names_of[id(parser)] = []
            parsers.append(parser)
        names_of[id(parser)].append(name)
    rows = []
    for parser in parsers:
        name, *aliases = names_of[id(parser)]
        text = helps.get(name) or ""
        if text == argparse.SUPPRESS:
            continue
        rows.append((name, name + (f" ({', '.join(aliases)})" if aliases else ""), text))
    return rows


def commands_help(subparsers: Any) -> str:
    """The top-level command list, one block per section, in the order of :data:`SECTIONS`."""
    rows = command_rows(subparsers)
    if not rows:
        return ""
    width = max(len(label) for _, label, _ in rows) + 2
    buckets: dict[str, list[str]] = {key: [] for key, _ in SECTIONS}
    other: list[str] = []
    for name, label, text in rows:
        buckets.get(_SECTION_OF.get(name, ""), other).append(f"  {label:<{width}}{text}".rstrip())
    blocks = [f"{title}:\n" + "\n".join(buckets[key]) for key, title in SECTIONS if buckets[key]]
    if other:
        blocks.append("Other:\n" + "\n".join(other))
    return "\n\n".join(blocks)
