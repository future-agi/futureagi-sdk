"""Input and output rules of ``futureagi-py webhooks``.

- **Secrets.** ``create`` and ``rotate-secret`` print the signing secret to stdout only when stdout is a terminal (with
  a warning on stderr), or with ``--show-secret``. Otherwise they refuse **before any request** unless
  ``--secret-out FILE`` is given. Its directory is checked before the request (a 0600 temporary file is created
  there); FILE is replaced only once the secret has arrived, so a failed ``rotate-secret`` leaves the old secret in
  place. Only the secret's last 4 characters are printed. A secret that is not ``whsec_`` plus padded base64 is
  neither written nor printed.
- **Headers.** ``--header 'K: V'`` lands in shell history and ``ps``; ``--header-file FILE`` (``Name: value`` lines)
  and ``--header-env NAME=ENVVAR`` keep values out of both. Every value is sent literally, and no error message
  quotes a header line (it may hold the value).
"""

from __future__ import annotations

import json
import os
import re
import stat
import sys
from typing import Any, Dict, Iterable, List, Optional, Sequence

from fi._sdk_exception import SDKException
from fi.webhooks._text import inert

EXIT_OK, EXIT_FAILED, EXIT_USAGE, EXIT_SETUP, EXIT_INTERRUPTED = 0, 1, 2, 3, 4  # fi/_cli/main.py's table


class UsageError(SDKException):
    exit_code = EXIT_USAGE

    def get_error_code(self) -> str:
        return "USAGE"


# ---- secrets --------------------------------------------------------------------------------------------------------


class SecretError(SDKException):
    """The API answered with a signing secret the CLI will not write or print (not ``whsec_`` plus padded base64), or
    a received secret could not be moved into ``--secret-out``. Exit 3, like any other server or setup error."""

    exit_code = EXIT_SETUP

    def get_error_code(self) -> str:
        return "WEBHOOK_SECRET_UNUSABLE"


class SecretSink:
    """Where a new signing secret goes. Built before the request that makes the secret.

    With ``--secret-out FILE``, a temporary file is created next to FILE first (``O_CREAT|O_EXCL|O_NOFOLLOW``, mode
    0600), which proves the directory is writable before anything is sent. FILE itself is not touched until the secret
    has arrived: it is then written to the temporary file, synced, and moved onto FILE with ``os.replace``. A failed or
    interrupted request removes only the temporary file, so an existing FILE (the secret a receiver reads today) keeps
    its content."""

    def __init__(self, args: Any, stdout=None, stderr=None) -> None:
        self.stdout = stdout or sys.stdout
        self.stderr = stderr or sys.stderr
        self.path: Optional[str] = getattr(args, "secret_out", None)
        self.show = bool(getattr(args, "show_secret", False))
        self.tty = _isatty(self.stdout)
        self._fd: Optional[int] = None
        self._tmp: Optional[str] = None
        if self.path and self.show:
            raise UsageError("use --secret-out FILE or --show-secret, not both")
        if not self.path and not self.show and not self.tty:
            raise UsageError(
                "stdout is not a terminal, so the signing secret would land in a log. Pass --secret-out FILE "
                "(written with mode 0600) or --show-secret. Nothing was sent."
            )
        if self.path:
            self._open()

    def _open(self) -> None:
        import tempfile

        path = self.path or ""
        shown = inert(path, 300)
        try:
            if stat.S_ISDIR(os.lstat(path).st_mode):
                raise UsageError(f"--secret-out {shown} is a directory; name a file. Nothing was sent.")
        except FileNotFoundError:
            pass
        except OSError as exc:
            raise UsageError(f"cannot write --secret-out {shown}: {exc.strerror}. Nothing was sent.") from None
        folder, base = os.path.split(os.path.abspath(path))
        try:  # mkstemp: O_RDWR|O_CREAT|O_EXCL|O_NOFOLLOW, mode 0600, a fresh name
            self._fd, self._tmp = tempfile.mkstemp(prefix=f".{base}.", suffix=".tmp", dir=folder)
        except OSError as exc:
            raise UsageError(f"cannot write --secret-out {shown}: {exc.strerror}. Nothing was sent.") from None
        if os.name == "nt":  # pragma: no cover - Windows only
            _user_only_acl(self._tmp)
        else:
            os.fchmod(self._fd, 0o600)

    def abandon(self) -> None:
        """The request failed or was interrupted: remove the temporary file. ``--secret-out`` itself is untouched."""
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None
        if self._tmp is not None:
            try:
                os.unlink(self._tmp)
            except OSError:
                pass
            self._tmp = None

    def deliver(self, secret: Any, endpoint_id: Any) -> Dict[str, Any]:
        """Check, then write or print the secret; returns what ``--json`` may show (``secret`` only when printed).

        A secret that is not ``whsec_`` plus padded standard base64 (``fi.webhooks.verify.secret_key``) is neither
        written nor printed. One that is cannot carry a control or bidi character, so the line that shows it is inert
        by construction."""
        from fi.webhooks.verify import WebhookSecretError, secret_key

        try:
            secret_key(secret)
        except WebhookSecretError as exc:
            self.abandon()
            raise SecretError(
                f"the API's new signing secret for {inert(endpoint_id)} is not whsec_ plus padded base64 "
                f"({exc.reason}), so it was neither written nor printed. Run: futureagi-py webhooks rotate-secret "
                f"{inert(endpoint_id)}"
            ) from None
        tail = secret[-4:]
        if self.path:
            self._commit(secret)
            return {"secret": None, "secret_file": self.path, "secret_tail": tail}
        if not self.tty:
            print("warning: printing the signing secret to a non-terminal (--show-secret)", file=self.stderr)
        else:
            print("warning: this is the only time the signing secret is shown; store it now", file=self.stderr)
        return {"secret": secret, "secret_file": None, "secret_tail": tail}

    def _commit(self, secret: str) -> None:
        assert self._fd is not None and self._tmp is not None and self.path
        data = (secret + "\n").encode("ascii")
        fd, self._fd = self._fd, None
        try:
            while data:
                data = data[os.write(fd, data) :]
            os.fsync(fd)
        finally:
            os.close(fd)
        tmp = self._tmp
        try:
            os.replace(tmp, self.path)
        except OSError as exc:  # the secret exists only in tmp now: keep it, and say where it is
            raise SecretError(
                f"the new signing secret could not be moved into --secret-out {inert(self.path, 300)} "
                f"({exc.strerror}); it is in {inert(tmp, 300)} (mode 0600)"
            ) from None
        self._tmp = None
        _sync_folder(os.path.dirname(os.path.abspath(self.path)))

    def note(self, out: Dict[str, Any]) -> str:
        if out["secret_file"]:
            return f"Signing secret written to {inert(out['secret_file'], 300)} (…{out['secret_tail']}, mode 0600)"
        return f"Signing secret: {out['secret']}"


def _sync_folder(folder: str) -> None:
    """Make the rename durable (POSIX); a file system that cannot sync a directory is not an error."""
    if os.name == "nt":  # pragma: no cover - Windows only
        return
    try:
        fd = os.open(folder, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _isatty(stream: Any) -> bool:
    try:
        return bool(stream.isatty())
    except (AttributeError, ValueError):
        return False


def _user_only_acl(path: str) -> None:  # pragma: no cover - Windows only
    import getpass
    import subprocess

    user = os.environ.get("USERNAME") or getpass.getuser()
    done = subprocess.run(
        ["icacls", path, "/inheritance:r", "/grant:r", f"{user}:F"], capture_output=True, text=True, check=False
    )
    if done.returncode != 0:
        raise UsageError(
            f"cannot restrict --secret-out {inert(path, 300)} to your user (icacls exit {done.returncode})"
        )


# ---- headers --------------------------------------------------------------------------------------------------------


def _split_header(line: str, where: str) -> tuple:
    """``Name: value``. A malformed line is refused by its place only: the line may be a secret header written
    without its colon (``Authorization Bearer sk-...``), and stderr ends up in CI logs (K3)."""
    name, sep, value = line.partition(":")
    if not sep or not name.strip():
        raise UsageError(f"{where}: expected 'Name: value' (a header name, a colon, then the value)")
    return name.strip(), value.strip()


_ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def headers_from_args(args: Any, environ: Optional[Dict[str, str]] = None) -> Optional[Dict[str, str]]:
    """``--header``, ``--header-file`` and ``--header-env`` merged (later wins); ``None`` when none was given."""
    env = os.environ if environ is None else environ
    out: Dict[str, str] = {}
    given = False
    for n, raw in enumerate(getattr(args, "header_args", None) or [], 1):
        given = True
        name, value = _split_header(raw, f"--header #{n}")
        out[name] = value
    path = getattr(args, "header_file", None)
    if path:
        given = True
        try:
            with open(path, encoding="utf-8") as fh:
                lines = fh.read().splitlines()
        except OSError as exc:
            raise UsageError(f"cannot read --header-file {inert(path, 300)}: {exc.strerror}") from None
        for n, line in enumerate(lines, 1):
            if line.strip() and not line.lstrip().startswith("#"):
                name, value = _split_header(line, f"--header-file line {n}")
                out[name] = value
    for n, spec in enumerate(getattr(args, "header_envs", None) or [], 1):
        given = True
        name, sep, var = (part.strip() for part in spec.partition("="))
        if not sep or not name or not _ENV_NAME.fullmatch(var):
            # not echoed: a value pasted here by mistake ("Authorization=Bearer sk-...") would reach CI logs
            raise UsageError(f"--header-env #{n}: expected NAME=ENVVAR, ENVVAR being the name of an environment "
                             "variable that holds the value")
        if var not in env:
            raise UsageError(f"--header-env {inert(name)}: the environment variable {var} is not set")
        out[name] = env[var]
    return out if given else None


FILTER_FLAGS = (
    "prompt_ids",
    "exclude_prompt_ids",
    "label_names",
    "actions",
    "deployment_ids",
    "environments",
    "trigger_kinds",
    "statuses",
)
_FILTERS_OF = {
    "prompt": {"prompt_ids", "exclude_prompt_ids", "label_names", "actions"},
    "prompt.version.created": {"prompt_ids", "exclude_prompt_ids"},
    "deployment.run.failed": {"deployment_ids", "environments", "trigger_kinds", "statuses"},
    "deployment.run": {"deployment_ids", "environments", "trigger_kinds", "statuses"},
    "deployment.run.completed": {"deployment_ids", "environments", "trigger_kinds"},
}


def _allowed(event_type: str) -> set:
    if event_type in _FILTERS_OF:
        return _FILTERS_OF[event_type]
    return _FILTERS_OF["prompt"] if event_type.startswith("prompt.") else _FILTERS_OF["deployment.run"]


def filters_from_args(args: Any, events: Sequence[str]) -> Optional[Dict[str, Dict[str, List[str]]]]:
    """The filter flags as per-type filters: each flag goes to every event type it applies to. A flag that fits none
    of the types is a usage error, so nothing is silently ignored."""
    given = {f: list(getattr(args, f, None) or []) for f in FILTER_FLAGS if getattr(args, f, None)}
    if not given:
        return None
    out: Dict[str, Dict[str, List[str]]] = {}
    for flag, values in given.items():
        fits = [e for e in events if flag in _allowed(e)]
        if not fits:
            raise UsageError(f"--{_flag_name(flag)} does not apply to {inert(', '.join(events), 500)}")
        for e in fits:
            out.setdefault(e, {})[flag] = values
    return out


def _flag_name(dest: str) -> str:
    return {
        "prompt_ids": "prompt",
        "exclude_prompt_ids": "exclude-prompt",
        "label_names": "label",
        "actions": "action",
        "deployment_ids": "deployment",
        "environments": "environment",
        "trigger_kinds": "trigger",
        "statuses": "status",
    }[dest]


# ---- output ---------------------------------------------------------------------------------------------------------


def print_json(value: Any, stream=None) -> None:
    print(json.dumps(value, indent=2, sort_keys=True, default=str), file=stream or sys.stdout)


def table(rows: Iterable[Sequence[Any]], header: Sequence[str], stream=None) -> None:
    rows = [[inert(c, 80) for c in r] for r in rows]
    widths = [max([len(h)] + [len(r[i]) for r in rows]) for i, h in enumerate(header)]
    stream = stream or sys.stdout
    print("  ".join(h.upper().ljust(w) for h, w in zip(header, widths)).rstrip(), file=stream)
    for r in rows:
        print("  ".join(c.ljust(w) for c, w in zip(r, widths)).rstrip(), file=stream)


def confirm(question: str, *, yes: bool, stdin=None, stderr=None) -> bool:
    """``--yes``, else ask on a terminal; without a terminal, refuse (exit 2) rather than guess. A ``False`` answer
    is the caller's exit 4 (:data:`EXIT_INTERRUPTED`, as Ctrl-C at the same question)."""
    if yes:
        return True
    stdin = stdin or sys.stdin
    if not _isatty(stdin):
        raise UsageError(f"{question} needs confirmation: pass --yes (stdin is not a terminal)")
    print(f"{question} [y/N] ", end="", file=stderr or sys.stderr, flush=True)
    return stdin.readline().strip().lower() in ("y", "yes")
