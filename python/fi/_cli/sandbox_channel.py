"""The ``sandbox`` commands that ride the exec channel: ``rsh``, ``ssh``, ``rsync`` and ``scp``.

``sandbox.py`` registers them and imports this module only when one runs, so ``--help`` stays fast.

- ``rsh SANDBOX_ID [--] COMMAND...`` runs the command with local standard input, output and error
  joined to it byte for byte, and exits with the command's code. It is the transport rsync and scp
  run: a leading host word (rsync sends an empty one, or the sandbox id for ``ID:path``) is dropped.
- ``ssh SANDBOX_ID`` is an interactive shell.
- ``rsync SANDBOX_ID ARGS...`` and ``scp SANDBOX_ID ARGS...`` run the system tool with this CLI as
  its transport; the sandbox side of a path is written ``:path``.

Close codes of the channel end the command with a message and exit 1 (see ``CLOSE_MESSAGES``).
"""

from __future__ import annotations

import os
import select
import shlex
import shutil
import sys
import threading
import time
from typing import Any, Callable, Optional

#: The CLI's words for each channel close code: what happened, and what to do next (``{rsh}`` is
#: the command that runs the same thing again).
CLOSE_MESSAGES = {
    4401: ("your access to this sandbox ended: you left the workspace, lost the role, or access was "
           "revoked", "check FI_WORKSPACE_ID and your role, then run it again"),
    4404: ("the sandbox was deleted or is no longer in this workspace",
           "check the id with: {list}"),
    4409: ("the workspace's sandboxes were stopped (emergency stop, paused or halted)",
           "run it again when sandboxes are running"),
    4410: ("the sandbox hibernated while the command ran", "run it again to resume it: {rsh}"),
    4411: ("the sandbox was frozen", "run it again when it is active"),
    1001: ("the server is shutting down", "run it again shortly"),
}
_STOPPED = "The command was stopped and whether it finished is unknown"


def closed_text(error: BaseException, sandbox_id: Optional[str], command: Callable[..., str]) -> str:
    """The CLI's message for a ``ChannelClosedError``: the words for its close code, that the command
    was stopped, and the next step."""
    code = getattr(error, "close_code", None)
    said, step = CLOSE_MESSAGES.get(code, (str(error), ""))
    step = step.format(list=command("list"), rsh=command("rsh", sandbox_id or "SANDBOX_ID", "--", "COMMAND..."))
    return f"{said}. {_STOPPED}" + (f"; {step}" if step else "")


# ---------------------------------------------------------------------------------------------
# rsh: the words of the command


#: ssh's options that take a value (``-p 22``, ``-oFoo=1``, ``-i key``): ``--ssh-style`` skips them.
_SSH_VALUED = frozenset("bcDEeFIiJLlmOopQRSWw")


def command_words(words: list, sandbox_id: str, *, ssh_style: bool) -> list:
    """The argv to run from what followed the id: a leading ``--`` is dropped; with ``ssh_style``
    ssh's options, its ``--`` and its host word come off first and the rest is one command line for
    a shell, as ssh takes it (scp runs its transport this way); otherwise a host word, empty or the
    sandbox id, is dropped (rsync names a host even for ``:path``) and the rest is the argv."""
    words = list(words)
    if words[:1] == ["--"]:
        words = words[1:]
    if ssh_style:
        index = 0
        while index < len(words):
            word = words[index]
            if word == "--":
                index += 1
                break
            if not word.startswith("-") or word == "-":
                break
            index += 2 if len(word) == 2 and word[1] in _SSH_VALUED else 1
        words = words[index + 1:]  # the host word, whatever it is, comes after the options
        return ["sh", "-c", " ".join(words)] if words else []
    if words[:1] in ([""], [sandbox_id]):
        words = words[1:]
    return words


# ---------------------------------------------------------------------------------------------
# Joining the local streams to a running command

_WRITE = threading.Lock()  # one writer at a time on the local output (typed echo and remote output)


def _emit(target: Any, data: bytes) -> None:
    """Write all of ``data`` and flush it. rsync and scp set their end of the pipe non-blocking, so
    this function waits for room when the pipe is full rather than failing partway through."""
    with _WRITE:
        view = memoryview(data)
        while view:
            try:
                written = target.write(view)
            except BlockingIOError as error:
                written = getattr(error, "characters_written", 0)
                _wait_writable(target)
            if written is None:  # a raw non-blocking writer says "would block" this way
                _wait_writable(target)
            view = view[written or 0 :]
        while True:
            try:
                target.flush()
                return
            except BlockingIOError:
                _wait_writable(target)


def _wait_writable(target: Any) -> None:
    try:
        select.select([], [target.fileno()], [])
    except (AttributeError, OSError, ValueError):
        time.sleep(0.01)


def _read_fd(source: Any) -> Optional[Callable[[int], bytes]]:
    """A blocking read of local standard input as raw bytes: the descriptor itself when there is
    one (a thread blocked in it holds no buffer lock when the interpreter ends), else the buffer."""
    try:
        fd = source.fileno()
    except (AttributeError, OSError, ValueError):
        fd = None
    if fd is not None:
        return lambda n: os.read(fd, n)
    buffer = getattr(source, "buffer", source)
    read = getattr(buffer, "read1", None) or getattr(buffer, "read", None)
    return None if read is None else read


def pump_stdin(stream: Any, source: Any, editor: Any = None) -> None:
    """Send local standard input to the command from a thread that stops at EOF. ``editor`` is the
    terminal's line editor (``ssh``); without one the bytes go as they are."""
    from fi.sandbox import ChannelStreamEndedError, SandboxError

    read = _read_fd(source)
    try:
        while read is not None:
            data = read(65536)
            if not data:
                break
            if editor is None:
                stream.write(data)
                continue
            send, echo, event = editor.push(data)
            if echo:
                _emit(sys.stdout.buffer, echo)
            if send:
                stream.write(send)
            if event == "interrupt":
                stream.cancel()
                return
            if event == "eof":
                break
    except (ChannelStreamEndedError, SandboxError, OSError, ValueError):
        return  # the command ended, or input is gone: the main thread reports how it ended
    try:
        stream.close_stdin()
    except (SandboxError, OSError):
        pass


def run_stream(stream: Any, out: Any, *, editor: Any = None, source: Any = None) -> int:
    """Copy the command's output to local standard output and error as it arrives, send local
    standard input to it, and return the exit status (the command's own code; 130 on Ctrl-C)."""
    from fi.sandbox.types import EXIT_CANCELLED

    from fi._cli.sandbox import _exit_status

    stdin = sys.stdin if source is None else source
    threading.Thread(target=pump_stdin, args=(stream, stdin, editor), daemon=True,
                     name="fi-sandbox-stdin").start()
    try:
        for chunk in stream:
            _emit(sys.stdout.buffer if chunk.stream == "stdout" else sys.stderr.buffer, chunk.data)
        return _exit_status(stream.wait(), out)
    except KeyboardInterrupt:
        stream.cancel()
        try:
            stream.wait(5)
        except (KeyboardInterrupt, Exception):
            pass
        return EXIT_CANCELLED
    except BrokenPipeError:
        stream.cancel()
        return 1


# ---------------------------------------------------------------------------------------------
# ssh: the terminal

_ESC, _CTRL_C, _CTRL_D, _CTRL_U, _BACKSPACE, _DELETE = 0x1B, 0x03, 0x04, 0x15, 0x08, 0x7F


class LineEditor:
    """Provide local terminal editing for a remote shell that runs as an exec stream
    with no pty behind it, so typed text is echoed and edited here and sent a line at a time.
    Backspace and Ctrl-U edit the line, Ctrl-D ends input (at the start of a line), Ctrl-C stops the
    command, and escape sequences (arrow keys) are dropped."""

    def __init__(self) -> None:
        self._line = bytearray()
        self._escape = False

    def push(self, data: bytes) -> tuple:
        """``(bytes to send, bytes to echo, event)`` for typed ``data``; ``event`` is ``"interrupt"``
        or ``"eof"`` once one is typed (the rest of ``data`` is dropped)."""
        send, echo = bytearray(), bytearray()
        for byte in data:
            if self._escape:
                self._escape = not (0x40 <= byte <= 0x7E and byte != ord("["))
                continue
            if byte == _ESC:
                self._escape = True
            elif byte == _CTRL_C:
                self._line.clear()
                echo += b"^C\r\n"
                return bytes(send), bytes(echo), "interrupt"
            elif byte == _CTRL_D:
                if self._line:
                    send += self._line
                    self._line.clear()
                else:
                    return bytes(send), bytes(echo), "eof"
            elif byte in (0x0D, 0x0A):
                send += self._line + b"\n"
                self._line.clear()
                echo += b"\r\n"
            elif byte in (_BACKSPACE, _DELETE):
                if self._line:
                    while self._line and (self._line[-1] & 0xC0) == 0x80:  # a UTF-8 continuation
                        self._line.pop()
                    if self._line:
                        self._line.pop()
                    echo += b"\b \b"
            elif byte == _CTRL_U:
                echo += b"\b \b" * len(self._line.decode("utf-8", "ignore"))
                self._line.clear()
            elif byte >= 0x20 or byte == 0x09:
                self._line.append(byte)
                echo.append(byte)
        return bytes(send), bytes(echo), None


class RawTerminal:
    """Local terminal in raw input mode for the length of a session: no echo, no line buffering, no
    signals from the keys. Output processing stays on, so a newline returns the carriage. The
    saved settings are put back on every exit (normal, an error, Ctrl-C, SIGTERM or SIGHUP). When
    standard input is not a terminal nothing changes."""

    def __init__(self, fd: Optional[int] = None) -> None:
        self.fd = 0 if fd is None else fd
        self.active = False
        self._saved: Any = None
        self._handlers: dict = {}

    def __enter__(self) -> "RawTerminal":
        try:
            import termios
        except ImportError:  # no terminal control here
            return self
        try:
            if not os.isatty(self.fd):
                return self
            self._saved = termios.tcgetattr(self.fd)
            mode = termios.tcgetattr(self.fd)
        except (termios.error, OSError, ValueError):
            return self
        mode[0] &= ~(termios.BRKINT | termios.ICRNL | termios.INPCK | termios.ISTRIP | termios.IXON)
        mode[3] &= ~(termios.ECHO | termios.ICANON | termios.IEXTEN | termios.ISIG)
        mode[6][termios.VMIN], mode[6][termios.VTIME] = 1, 0
        self._hang_up_to_exit()
        termios.tcsetattr(self.fd, termios.TCSADRAIN, mode)
        self.active = True
        return self

    def _hang_up_to_exit(self) -> None:
        import signal

        def leave(number: int, frame: Any) -> None:
            raise SystemExit(128 + number)

        if threading.current_thread() is threading.main_thread():
            for name in ("SIGTERM", "SIGHUP"):
                number = getattr(signal, name, None)
                if number is not None:
                    self._handlers[number] = signal.signal(number, leave)

    def __exit__(self, *exc: object) -> None:
        import signal

        if self._saved is not None:
            import termios

            try:
                termios.tcsetattr(self.fd, termios.TCSADRAIN, self._saved)
            except (termios.error, OSError):
                pass
            self._saved = None
        for number, handler in self._handlers.items():
            signal.signal(number, handler)
        self._handlers.clear()
        self.active = False


def open_shell(sbx: Any, shell: str) -> tuple:
    """The one place that decides how an interactive session is attached, and so the one place that
    changes when the server serves pty streams: ``(stream, terminal, editor)``.

    Today the shell runs as an exec stream with no pty behind it, so the local terminal is raw and
    :class:`LineEditor` supplies the terminal's line handling. When the server offers a pty
    (``POST .../pty`` and attach on the channel), open that here instead and return no editor: the
    remote terminal then does the echo and editing, and keys go through untouched."""
    stream = sbx.commands.exec_stream([shell, "-i"])
    return stream, RawTerminal(), LineEditor()


def reported_shell(info: Any) -> str:
    """The shell the sandbox's record reports (``shell``: an absolute path), else ``/bin/sh``."""
    shell = info.get("shell") if isinstance(info, dict) else None
    ok = isinstance(shell, str) and shell.startswith("/") and shell.isprintable() and " " not in shell
    return shell if ok else "/bin/sh"


# ---------------------------------------------------------------------------------------------
# rsync and scp: the system tools


def self_command(prog: str) -> list:
    """How to run this program again: its console script when that is what is running, else
    ``python -I -m fi._cli`` (isolated, so the re-entry does not import from the current directory)."""
    name = prog.split(" ", 1)[0]
    argv0 = sys.argv[0] if sys.argv else ""
    if argv0 and os.path.basename(argv0) == name:
        found = shutil.which(argv0) or os.path.abspath(argv0)
        return [found]
    return [sys.executable, "-I", "-m", "fi._cli"]


def rsh_command(prog: str, args: Any, flags: tuple = (), tail: tuple = ()) -> list:
    """This CLI's ``sandbox [address flags] rsh [flags] SANDBOX_ID [tail]`` (the address flags typed
    here are repeated; the environment carries the rest)."""
    words = self_command(prog) + ["sandbox"]
    if getattr(args, "base_url", None) is not None:
        words += ["--base-url", args.base_url]
    if getattr(args, "allow_custom_base_url", False):
        words.append("--allow-custom-base-url")
    return words + ["rsh", *flags, args.id, *tail]


def find_tool(name: str, why: str) -> str:
    """The system tool's path, or a usage problem that names it."""
    from fi._cli.sandbox import _Usage

    found = shutil.which(name)
    if found is None:
        raise _Usage(
            f"{name}_missing",
            f"{name} is not installed on this computer (it is not on PATH), and {why}. Install "
            f"{name} (for example: apt install {name}, or brew install {name}), then run this again.",
        )
    return found


def remote_operands(words: list, sandbox_id: str) -> list:
    """The words that name a path in the sandbox: ``:path`` (or ``ID:path``)."""
    return [w for w in words if w.startswith(":") or w.startswith(sandbox_id + ":")]


def require_remote(tool: str, words: list, sandbox_id: str) -> None:
    from fi._cli.sandbox import _Usage

    if set(words) & {"-h", "--help", "--version"} or remote_operands(words, sandbox_id):
        return
    raise _Usage("invalid_arguments", f"{tool} needs a path in the sandbox: write it as :PATH "
                                      f"(for example {tool} SANDBOX_ID ./file :dest/)")


def run_tool(argv: list, cleanup: Callable[[], None] = lambda: None) -> int:
    import subprocess

    try:
        done = subprocess.run(argv)
    except KeyboardInterrupt:
        return 130
    except OSError as error:
        from fi._cli.sandbox import _Usage

        raise _Usage("tool_failed", f"could not run {argv[0]}: {error}") from None
    finally:
        cleanup()
    code = done.returncode
    return 128 - code if code < 0 else code


_PROTECT = {"-s", "--protect-args", "--secluded-args", "--no-protect-args", "--no-secluded-args"}


def tool_words(args: Any) -> list:
    """What followed the sandbox id, less a leading ``--``."""
    words = list(args.tool_args)
    return words[1:] if words[:1] == ["--"] else words


def rsync_argv(prog: str, args: Any) -> list:
    from fi._cli.sandbox import _Usage

    words = tool_words(args)
    if any(w in ("-e", "--rsh") or w.startswith("--rsh=") for w in words):
        raise _Usage("invalid_arguments", "sandbox rsync sets the remote shell itself; remove -e / --rsh")
    require_remote("rsync", words, args.id)
    tool = find_tool("rsync", "sandbox rsync runs it")
    # No shell runs on the sandbox side, so rsync must not escape the paths it sends for one.
    protect = [] if set(words) & _PROTECT else ["--protect-args"]
    return [tool, "-e", shlex.join(rsh_command(prog, args)), *protect, *words]


def scp_argv(prog: str, args: Any) -> tuple:
    """``(argv, cleanup)`` for the system scp. ``:path`` becomes ``SANDBOX_ID:path`` (scp needs a
    host), ``-O`` selects the classic protocol (it runs ``scp`` in the sandbox over the channel; the
    newer one needs an sftp server there), and ``-S`` names a wrapper that maps scp's ssh command
    line to this CLI's ``rsh``."""
    import stat
    import tempfile

    words = [(args.id + w) if w.startswith(":") else w for w in tool_words(args)]
    require_remote("scp", words, args.id)
    tool = find_tool("scp", "sandbox scp runs it")
    folder = tempfile.mkdtemp(prefix="futureagi-scp-")
    path = os.path.join(folder, "rsh")
    command = shlex.join(rsh_command(prog, args, flags=("--ssh-style",), tail=("--",)))
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(f'#!/bin/sh\nexec {command} "$@"\n')
    os.chmod(path, stat.S_IRWXU)
    return [tool, "-O", "-S", path, *words], lambda: shutil.rmtree(folder, ignore_errors=True)
