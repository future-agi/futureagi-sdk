"""Records the sandbox handle returns (``CommandResult``, ``SandboxList``, ``NetworkPolicyInfo``)
and the one exit-code table for how a command ended (:func:`exit_status`).

The table, for a process (the ``sandbox exec`` command, an integration) that exits as the command
did: the command's own ``exit_code``; :data:`EXIT_TIMED_OUT` (124) when it ran past its time
limit; :data:`EXIT_SIGNAL_BASE` + N (128+N) when signal N ended it, numbered as on Linux
(:data:`LINUX_SIGNALS`: the sandbox runs Linux, whatever this computer numbers them);
:data:`EXIT_CANCELLED` (130) when it was cancelled; :data:`EXIT_REFUSED` (1) when it could not
start, the server failed after it started, its signal has no known number, or whether it finished
is unknown; :data:`EXIT_USAGE` (2) for a usage or configuration problem found before anything
ran. This module imports the standard library only (the platform import rule; its ``.frames``
import is for type checkers), and the ``sandbox`` command and the integrations read the codes here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:  # annotations only: this module stays standard library only
    from .frames import ExitFrame

#: Done (a command's own 0 is its own code, not this).
EXIT_OK = 0
#: Refused by the server; or the command could not start, failed after starting, ended by a
#: signal with no known number, or it is unknown whether it finished.
EXIT_REFUSED = 1
#: A usage or configuration problem, found before anything ran.
EXIT_USAGE = 2
#: The command ran past its time limit and was stopped.
EXIT_TIMED_OUT = 124
#: A signal ended the command: this plus the signal's Linux number.
EXIT_SIGNAL_BASE = 128
#: The command was cancelled (``commands.cancel``, or Ctrl-C in the command line).
EXIT_CANCELLED = 130

#: Signal numbers on Linux, where sandboxes run (this computer's own numbering may differ).
LINUX_SIGNALS = {
    "SIGHUP": 1,
    "SIGINT": 2,
    "SIGQUIT": 3,
    "SIGILL": 4,
    "SIGTRAP": 5,
    "SIGABRT": 6,
    "SIGIOT": 6,
    "SIGBUS": 7,
    "SIGFPE": 8,
    "SIGKILL": 9,
    "SIGUSR1": 10,
    "SIGSEGV": 11,
    "SIGUSR2": 12,
    "SIGPIPE": 13,
    "SIGALRM": 14,
    "SIGTERM": 15,
    "SIGSTKFLT": 16,
    "SIGCHLD": 17,
    "SIGCONT": 18,
    "SIGSTOP": 19,
    "SIGTSTP": 20,
    "SIGTTIN": 21,
    "SIGTTOU": 22,
    "SIGURG": 23,
    "SIGXCPU": 24,
    "SIGXFSZ": 25,
    "SIGVTALRM": 26,
    "SIGPROF": 27,
    "SIGWINCH": 28,
    "SIGIO": 29,
    "SIGPOLL": 29,
    "SIGPWR": 30,
    "SIGSYS": 31,
}


def signal_number(name: Optional[str]) -> Optional[int]:
    """The Linux number of a signal named ``SIGTERM``, ``TERM`` or ``15``; None when unknown."""
    text = (name or "").strip().upper()
    if text.isdigit():
        return int(text)
    if not text:
        return None
    return LINUX_SIGNALS.get(text if text.startswith("SIG") else "SIG" + text)


def exit_status(end: Any) -> int:
    """The exit code for how a command ended: an ``ExitFrame`` or a :class:`CommandResult`
    (anything with ``cancelled``, ``timed_out``, ``error``, ``exit_code`` and ``signal``), by the
    table above. A cancel wins over a timeout, and both over the signal that carried them out."""
    if end.cancelled:
        return EXIT_CANCELLED
    if end.timed_out:
        return EXIT_TIMED_OUT
    if end.error:
        return EXIT_REFUSED
    if end.exit_code is not None:
        return int(end.exit_code)
    number = signal_number(end.signal)
    return EXIT_REFUSED if number is None else EXIT_SIGNAL_BASE + number


@dataclass(frozen=True)
class CommandResult:
    """How a command ended: the whole ``exit`` record, plus the output and the ``exec_id``.

    A non-zero ``exit_code``, a timeout, a signal and a cancel are results, not errors.
    ``exit_code`` is None when a signal ended the command (``signal`` names it) or it did not
    start (``error`` says why, for example a spawn failure). ``truncated`` means output beyond
    the server's cap was dropped; ``stdout_bytes`` / ``stderr_bytes`` count what the command
    wrote, ``duration_ms`` how long it ran."""

    exit_code: Optional[int]
    stdout: str
    stderr: str
    exec_id: Optional[str]
    signal: Optional[str] = None
    timed_out: bool = False
    cancelled: bool = False
    truncated: bool = False
    duration_ms: Optional[int] = None
    stdout_bytes: Optional[int] = None
    stderr_bytes: Optional[int] = None
    error: Optional[str] = None
    exit: Optional[ExitFrame] = field(default=None, repr=False, compare=False)

    @classmethod
    def from_exit(
        cls, frame: ExitFrame, stdout: str, stderr: str, exec_id: Optional[str]
    ) -> CommandResult:
        """The result for an ``exit`` frame and the output read before it."""
        return cls(
            exit_code=frame.exit_code,
            stdout=stdout,
            stderr=stderr,
            exec_id=exec_id,
            signal=frame.signal,
            timed_out=frame.timed_out,
            cancelled=frame.cancelled,
            truncated=frame.truncated,
            duration_ms=frame.duration_ms,
            stdout_bytes=frame.stdout_bytes,
            stderr_bytes=frame.stderr_bytes,
            error=frame.error,
            exit=frame,
        )


@dataclass(frozen=True)
class SandboxList:
    """``Sandbox.list()``: one handle per sandbox (its ``info`` is the listed record, no further
    request) and the workspace's ``caps`` (images, sizes, templates, limits)."""

    sandboxes: List[Any]
    caps: Dict[str, Any]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)


@dataclass(frozen=True)
class NetworkPolicyInfo:
    """``sbx.network_policy.get()`` / ``.set()``: the policy and its ``etag``.

    ``etag`` is the response's ``ETag`` header, the quoted desired revision (``"4"``): pass it as
    ``set(..., if_match=etag)``. ``policy`` holds ``desired``, ``desiredRevision``,
    ``appliedRevision`` and ``applyStatus``; ``raw`` is the whole response."""

    etag: Optional[str]
    policy: Dict[str, Any]
    raw: Dict[str, Any] = field(default_factory=dict, repr=False, compare=False)


__all__ = [
    "CommandResult",
    "SandboxList",
    "NetworkPolicyInfo",
    "EXIT_OK",
    "EXIT_REFUSED",
    "EXIT_USAGE",
    "EXIT_TIMED_OUT",
    "EXIT_SIGNAL_BASE",
    "EXIT_CANCELLED",
    "LINUX_SIGNALS",
    "signal_number",
    "exit_status",
]
