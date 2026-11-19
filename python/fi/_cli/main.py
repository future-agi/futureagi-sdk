"""The ``futureagi-py`` entry point and its exit-code table.

Exit codes (stable; the same table backs ``get_error_code()`` and the ``--json`` error object):
0 success · 1 a gate failed (``--fail-under``) · 2 usage error · 3 setup / server / a missing
extra · 4 interrupted · 5 the trial error rate is above ``--max-error-rate`` (default 0 under
``CI=true``).

The core imports no command group. Groups arrive through the registry (``registry.py``), and what
only a group knows reaches the core as a registry hook the group adds in its ``register()``:
a pre-parse hook (sees the raw argv first), an interrupt hook (the lines Ctrl-C prints) and an
exit hook (runs after the command in the console script). A missing optional dependency (a
``ModuleNotFoundError``) prints its fix: an exception's explicit ``install_hint``, else the
missing root's unique extra, else the dispatched command's ``install_hint``, else the module name.
The local-evals Python-version guard also reports a missing extra, without changing its library
exception. Other ``ImportError`` failures say an installed package failed, with no install line.
Never a traceback.

Nothing optional is imported at module level. The library keeps a ``NullHandler``; the CLI adds
the stderr handler.
"""

from __future__ import annotations

import argparse
import logging
import re
import sys
from contextlib import contextmanager
from typing import Iterator, Optional, Sequence

EXIT_OK, EXIT_GATE, EXIT_USAGE, EXIT_SETUP, EXIT_INTERRUPTED, EXIT_CI_ERRORS = 0, 1, 2, 3, 4, 5

logging.getLogger("fi").addHandler(logging.NullHandler())


def build_parser(*, warn=None) -> argparse.ArgumentParser:
    from fi._cli import auth, doctor, registry

    parser = argparse.ArgumentParser(
        prog="futureagi-py",
        usage="futureagi-py [-h] [--version] COMMAND ...",
        description="Future AGI from the command line. `futureagi-py COMMAND --help` shows a command's options.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    import fi

    # Legacy distributions overwrite or remove fi/__init__.py. Doctor must still
    # start in that broken environment so it can describe the ordered repair.
    from importlib.metadata import PackageNotFoundError, version

    try:
        installed_version = version("futureagi")
    except PackageNotFoundError:
        installed_version = getattr(fi, "__version__", "unknown")
    parser.add_argument("--version", action="version", version=f"futureagi-py {installed_version}")
    # the commands are listed by section (Evaluate, Platform, Setup) in the epilog, not by argparse
    sub = parser.add_subparsers(dest="command", metavar="COMMAND", help=argparse.SUPPRESS)
    doctor.register(sub)
    auth.register(sub)
    for name in ("doctor", "login", "logout"):
        registry.set_section(name, "setup")
    kwargs = {"warn": warn} if warn is not None else {}
    registry.load_groups(sub, **kwargs)
    parser.epilog = registry.commands_help(sub)
    return parser


@contextmanager
def _setup_logging(verbose: bool, quiet: bool) -> Iterator[None]:
    """Configure this invocation only; embedded callers keep their logging policy."""
    root = logging.getLogger("fi")
    previous_level = root.level
    handler = None
    if not any(getattr(h, "_futureagi_cli", False) for h in root.handlers):
        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))
        handler._futureagi_cli = True  # type: ignore[attr-defined]
        root.addHandler(handler)
    try:
        root.setLevel(logging.DEBUG if verbose else logging.WARNING if quiet else logging.INFO)
        yield
    finally:
        root.setLevel(previous_level)
        if handler is not None:
            root.removeHandler(handler)
            handler.close()


def main(argv: Optional[Sequence[str]] = None) -> int:
    from fi._cli import registry

    console = argv is None
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = build_parser()  # loads the groups, which add their hooks
    early = registry.run_pre_parse(argv)
    if early is not None:
        return early
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:  # argparse: 0 for --help, 2 for a usage error
        return int(exc.code or 0)
    if not getattr(args, "command", None):
        parser.print_help(sys.stderr)
        return EXIT_USAGE
    with _setup_logging(getattr(args, "verbose", False), getattr(args, "quiet", False)):
        code = _dispatch(args, argv)
        if console:
            registry.run_on_exit(code)
        return code


def _report(args: argparse.Namespace, exc: BaseException, code: int, error_code: str) -> int:
    if getattr(args, "json", False):
        import json

        from fi.errors import MissingExtraError

        error = {"code": error_code, "message": str(exc), "exit_code": code}
        if isinstance(exc, MissingExtraError):
            error.update(getattr(exc, "_cli_error_fields", {}))
        print(json.dumps({"error": error}))
    else:
        print(f"error: {exc}", file=sys.stderr)
    return int(code)


def missing_extra(args: argparse.Namespace, exc: ImportError):
    """Prefer the exception's hint, then a unique extra, then the command's default.

    Without any of those, name the module but never guess a distribution (S2).
    """
    from fi._cli.extra_roots import evals_requirement, extra_for_module, is_evals_requirement
    from fi.errors import MissingExtraError

    module = getattr(exc, "name", None)
    hint = getattr(exc, "install_hint", None)
    python_guard = is_evals_requirement(exc)
    extra = None
    if not hint:
        extra = "evals" if python_guard else extra_for_module(module)
        hint = f'pip install "futureagi[{extra}]"' if extra else getattr(args, "install_hint", None)
    if extra == "evals":
        requirement = evals_requirement()
        message = requirement if str(exc) == requirement else f"{exc}. {requirement}"
    elif hint:
        message = f"{exc}. Run: {hint}"
    elif module:
        message = f"{exc}. Install the package that provides the {module.split('.')[0]!r} module and retry"
    else:
        message = f"{exc}. An optional dependency is missing"
    err = MissingExtraError(message, exc, extra=extra, module=module)
    err.install_hint = hint
    # Keep machine markers separate from the legacy attributes and hint precedence.
    # Only the fixed root table (never an install hint or exc.extra) supplies an extra.
    fields = {}
    if python_guard:
        fields = {
            "reason": "python_version",
            "python": f"{sys.version_info[0]}.{sys.version_info[1]}",
            "required_python": "3.11",
            "extra": "evals",
        }
    elif module:
        fields["reason"] = "missing_module"
        root = module.split(".", 1)[0]
        if re.fullmatch(r"[A-Za-z0-9_.]+", root):
            fields["module"] = root
        mapped_extra = extra_for_module(module)
        if mapped_extra:
            fields["extra"] = mapped_extra
    err._cli_error_fields = fields
    return err


def _dispatch(args: argparse.Namespace, argv: Sequence[str] = ()) -> int:
    import httpx

    from fi._cli import registry
    from fi._sdk_exception import SDKException
    from fi.errors import TransportError

    try:
        return int(args.func(args) or 0)
    except KeyboardInterrupt as exc:
        print(f"\n{registry.interrupt_message(exc, argv) or 'Interrupted.'}", file=sys.stderr)
        return EXIT_INTERRUPTED
    except SDKException as exc:
        return _report(args, exc, getattr(exc, "exit_code", EXIT_SETUP), exc.get_error_code())
    except httpx.TransportError as exc:  # the server did not answer: exit 3, one line, no traceback
        err = TransportError.from_exception(exc)
        return _report(args, err, EXIT_SETUP, err.get_error_code())
    except ModuleNotFoundError as exc:  # a module is absent: a missing extra
        err = missing_extra(args, exc)
        return _report(args, err, EXIT_SETUP, err.get_error_code())
    except ImportError as exc:
        from fi._cli.extra_roots import is_evals_requirement

        if is_evals_requirement(exc):
            err = missing_extra(args, exc)
            return _report(args, err, EXIT_SETUP, err.get_error_code())
        # Installed but broken ("cannot import name X"): not a missing extra (S6).
        err = SDKException(f"{exc}. An installed package failed to import; reinstall or upgrade it", exc)
        return _report(args, err, EXIT_SETUP, "IMPORT_FAILED")


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
