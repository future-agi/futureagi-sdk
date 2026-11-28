"""How a sandbox command ended, as one shell-style exit code, for the integrations.

The numbers come from the SDK's one exit-code table, :mod:`fi.sandbox.types`, which the ``sandbox exec``
command reads too, so an integration and the command line give the same code for the same ending. The
first row that applies wins, in this order:

=====================================================  ================  ==========================================
How the command ended                                  Code              :func:`ending_note`
=====================================================  ================  ==========================================
it was cancelled                                       130               ``Command was cancelled``
it ran past its time limit                             124               ``Command timed out after {t} seconds``
it could not start (``error``)                         1                 ``The command could not start: {error}``
it exited (``exit_code`` is not None)                  that code         None
signal N ended it, N its Linux number                  128 + N           ``Command was ended by signal {signal}``
a signal with no known number, or no code and no       None              ``Command ended without an exit code``
signal                                                                   (with the signal in brackets, if any)
=====================================================  ================  ==========================================

Signal numbers are Linux's, because sandboxes run Linux, whatever this computer numbers them.
:func:`shell_exit_code` returns None for the last row so that each integration decides what an
ending without a number means to its framework (the command line exits 1 there). Records are read by
attribute: ``cancelled``, ``timed_out``, ``error``, ``exit_code`` and ``signal``, as a
:class:`fi.sandbox.CommandResult` or an :class:`fi.sandbox.ExitFrame` carries them.
"""

from __future__ import annotations

from typing import Any, Optional

from fi.sandbox.types import (
    EXIT_CANCELLED,
    EXIT_REFUSED,
    EXIT_SIGNAL_BASE,
    EXIT_TIMED_OUT,
    LINUX_SIGNALS,
    exit_status,
    signal_number,
)

#: The command could not start (its exit record has an ``error``).
EXIT_FAILED = EXIT_REFUSED


def shell_exit_code(result: Any) -> Optional[int]:
    """The exit code for how a command ended, by the table above; None when the record has no code,
    no known signal, and was not cancelled, timed out or refused to start."""
    if not (result.cancelled or result.timed_out or result.error):
        if result.exit_code is None and signal_number(result.signal) is None:
            return None
    return exit_status(result)


def ending_note(result: Any, timeout_s: Optional[int] = None) -> Optional[str]:
    """One line that says how a command ended, for an integration to append to its output; None when
    the command exited with its own code. ``timeout_s`` is the time limit the command ran with."""
    if result.cancelled:
        return "Command was cancelled"
    if result.timed_out:
        if timeout_s is None:
            return "Command timed out"
        return f"Command timed out after {timeout_s} seconds"
    if result.error:
        return f"The command could not start: {result.error}"
    if result.exit_code is not None:
        return None
    if result.signal and signal_number(result.signal) is not None:
        return f"Command was ended by signal {result.signal}"
    if result.signal:
        return f"Command ended without an exit code ({result.signal})"
    return "Command ended without an exit code"


__all__ = [
    "EXIT_FAILED",
    "EXIT_TIMED_OUT",
    "EXIT_SIGNAL_BASE",
    "EXIT_CANCELLED",
    "LINUX_SIGNALS",
    "signal_number",
    "shell_exit_code",
    "ending_note",
]
