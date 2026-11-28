"""``SandboxEval``: what one trial does inside its own sandbox, and the records it writes.

A frozen dataclass, checked when it is made, so a wrong field fails before any sandbox exists.
Timeouts have no upper bound here: the workspace's own maximum (``caps.exec.maxTimeoutSeconds``)
is read from the sandbox settings when the run starts.
"""

from __future__ import annotations

import json
import posixpath
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Final, Mapping, Optional, Tuple, Union

from fi.experiments.errors import UsageError

if TYPE_CHECKING:  # pragma: no cover
    from fi.experiments._context import TaskContext
    from fi.sandbox import AsyncSandbox

#: The sandbox's writable folder: commands run here, or in a folder under it.
WORKSPACE: Final = "/workspace"
#: The folder each trial's own files live in: ``row.json`` and the default reward file.
EVAL_DIR: Final = WORKSPACE + "/.fi-eval"

Files = Mapping[str, Union[str, bytes]]
Text = Union[str, Callable[[Any], str]]


@dataclass(frozen=True)
class SandboxEval:
    """One trial: create a sandbox, write the row and ``files``, run the agent, run the verifier,
    read the reward, delete the sandbox.

    Exactly one of ``agent_command`` (a command run inside the sandbox) and ``agent`` (an async
    function ``agent(row, sbx, ctx)`` run in this process, acting on the sandbox through its
    handle) is set. ``agent_command``, ``verifier`` and ``files`` may be functions of the row;
    ``env`` may be a function of ``(row, ctx)``. ``env`` holds plain, non-secret variables only.
    ``cwd`` is the commands' folder: ``/workspace``, a folder under it, or a path relative to it
    (``app`` is ``/workspace/app``). The keys of ``files`` and ``reward_path`` are absolute paths of
    files under ``/workspace`` (the sandbox's files API reaches only that folder).
    """

    agent_command: Optional[Text] = None
    agent: Optional[Callable[[Any, "AsyncSandbox", "TaskContext"], Awaitable[Any]]] = None
    verifier: Optional[Text] = None
    files: Union[Files, Callable[[Any], Files], None] = None
    env: Union[Mapping[str, str], Callable[[Any, "TaskContext"], Mapping[str, str]], None] = None
    template: Optional[str] = None
    size: Optional[str] = None
    image: Optional[str] = None
    cwd: str = "/workspace"
    agent_timeout_s: int = 900
    verifier_timeout_s: int = 300
    reward_path: str = EVAL_DIR + "/reward"
    reward_from_exit: bool = True
    trace_env: bool = True
    name_prefix: str = "fi-eval"
    max_output_chars: int = 20_000

    def __post_init__(self) -> None:
        if (self.agent_command is None) == (self.agent is None):
            raise UsageError("SandboxEval takes exactly one of agent_command= (a command run inside the "
                             "sandbox) and agent= (an async function agent(row, sbx, ctx))")
        if self.agent is not None and not callable(self.agent):
            raise UsageError("agent= takes an async function agent(row, sbx, ctx)")
        for name in ("agent_command", "verifier"):
            value = getattr(self, name)
            if value is not None and not callable(value) and not (isinstance(value, str) and value.strip()):
                raise UsageError(f"{name}= takes a command (a non-empty string) or a function of the row")
        if self.files is not None and not callable(self.files):
            if not isinstance(self.files, Mapping):
                raise UsageError("files= takes a mapping of absolute path under /workspace to text or bytes, "
                                 "or a function of the row")
            checked_files(self.files)
        if self.env is not None and not callable(self.env) and not isinstance(self.env, Mapping):
            raise UsageError("env= takes a mapping of plain, non-secret variables, or a function of (row, ctx)")
        for name in ("agent_timeout_s", "verifier_timeout_s"):
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, int) or value < 1:
                raise UsageError(f"{name} must be a whole number of seconds, at least 1")
        if isinstance(self.max_output_chars, bool) or not isinstance(self.max_output_chars, int) \
                or self.max_output_chars < 0:
            raise UsageError("max_output_chars must be a whole number, 0 or more")
        exec_cwd(self.cwd)
        workspace_file(self.reward_path, "reward_path")
        prefix = self.name_prefix
        if not isinstance(prefix, str) or not 1 <= len(prefix) <= 32 or not prefix.isprintable() \
                or prefix != prefix.strip():
            raise UsageError("name_prefix must be 1 to 32 printable characters with no leading or "
                             "trailing space")

    @property
    def mode(self) -> str:
        """``"command"`` (the agent runs inside the sandbox) or ``"callable"`` (it runs here)."""
        return "command" if self.agent_command is not None else "callable"

    @property
    def command_cwd(self) -> Optional[str]:
        """``cwd`` as the exec API takes it: relative to ``/workspace``, None for ``/workspace``."""
        return exec_cwd(self.cwd)


def exec_cwd(path: Any) -> Optional[str]:
    """A command's folder as the exec API takes it. The API takes a folder relative to ``/workspace``
    and refuses an absolute one, so ``/workspace/app`` is sent as ``app`` and ``/workspace`` itself as
    no cwd (None). A relative ``path`` is relative to ``/workspace``. A folder outside ``/workspace``,
    or one that leaves it through ``..``, raises ``UsageError``."""
    if not isinstance(path, str):
        raise UsageError(f"cwd must be a folder path, not {path!r}")
    joined = path if path.startswith("/") else f"{WORKSPACE}/{path}"
    full = posixpath.normpath("/" + joined.lstrip("/"))
    if full == WORKSPACE:
        return None
    if full.startswith(WORKSPACE + "/"):
        return full[len(WORKSPACE) + 1:]
    raise UsageError(f"cwd {path!r} is outside {WORKSPACE}: sandbox commands run in {WORKSPACE} or a folder "
                     f"under it, so pass one of those (or a path relative to {WORKSPACE})")


def workspace_file(path: Any, name: str) -> str:
    """A file a trial writes or reads, as given: an absolute path under ``/workspace``, which is all the
    sandbox's files API reaches. ``/workspace`` itself, a path outside it, and one with a ``.`` or ``..``
    segment, a backslash or a control character raise ``UsageError`` before any file is written."""
    text = path if isinstance(path, str) else ""
    parts = [part for part in text.split("/") if part]
    if text.startswith("/") and parts[:1] == ["workspace"] and len(parts) > 1 and not {".", ".."} & set(parts) \
            and "\\" not in text and not any(ord(char) < 32 or ord(char) == 127 for char in text):
        return text
    raise UsageError(f"{name} {path!r} is not a file under {WORKSPACE}: a trial writes and reads its files "
                     f"through the sandbox's files API, which reaches only {WORKSPACE}, so give an absolute "
                     f'path under it with no "." or ".." part (for example {WORKSPACE}/task.md)')


def checked_files(files: Any) -> Dict[str, Union[str, bytes]]:
    """``files=`` (the mapping, or what its function returned for a row) as it is written: each key a file
    under ``/workspace`` (:func:`workspace_file`) and each value text or bytes, else ``UsageError``."""
    try:
        given = dict(files)
    except (TypeError, ValueError):
        raise UsageError("files= maps an absolute path under /workspace to text or bytes") from None
    for path, data in given.items():
        workspace_file(path, "files= key")
        if not isinstance(data, (str, bytes)):
            raise UsageError(f"files= maps each path to text or bytes, not {type(data).__name__} "
                             f"(for {path!r})")
    return given


# ---- what a trial writes and reads (pure: no sandbox, no loop) ----------------------------------

#: The row as the task sees it, as JSON, at this path (``EVAL_ROW_FILE`` in a command's env).
ROW_FILE: Final = EVAL_DIR + "/row.json"
#: Our own credential names: not passed in a command's env (a refusal list, not a detector).
REFUSED_ENV: Final = frozenset(
    {"FI_API_KEY", "FI_SECRET_KEY", "FUTUREAGI_OMEGA_API_KEY", "FI_PLATFORM_TOKEN", "OMEGA_OS_API_KEY"}
)
NAME_CHARS: Final = 63
NAME_BYTES: Final = 120
REWARD_MAX_BYTES: Final = 64 * 1024


def describe(exc: BaseException) -> str:
    """``"code: message"`` (the handle's error text is already scrubbed of keys)."""
    code = getattr(exc, "code", None)
    text = str(exc) or type(exc).__name__
    return f"{code}: {text}" if isinstance(code, str) and code and not text.startswith(code) else text


def fit_name(text: str) -> str:
    """A sandbox name: printable, at most ``NAME_CHARS`` characters and ``NAME_BYTES`` UTF-8 bytes."""
    text = "".join(c if c.isprintable() else "-" for c in text)[:NAME_CHARS]
    while len(text.encode("utf-8")) > NAME_BYTES:
        text = text[:-1]
    return text


def positive(value: Any) -> Optional[int]:
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 1 else None


def row_json(row: Any) -> str:
    """``row.json``: an ``fi.experiments`` row's id, number, columns, inputs, expected and metadata."""
    from fi.experiments._plan import to_jsonable

    if hasattr(row, "inputs") and hasattr(row, "to_dict"):
        view = {"id": row.id, "number": row.number, "data": row.to_dict(), "inputs": row.inputs,
                "expected": row.expected, "metadata": row.metadata}
    else:
        view = {"data": row}
    return json.dumps(to_jsonable(view), ensure_ascii=False, default=str)


def command_record(result: Any, limit: int) -> dict:
    """A command's exit record for the output: not its env, only the last ``limit`` characters of
    its output. ``shell_exit_code`` is the one exit-code table (``fi.sandbox.types.exit_status``)."""
    from fi.sandbox.types import exit_status

    record = {"exit_code": result.exit_code, "shell_exit_code": exit_status(result),
              "timed_out": result.timed_out, "signal": result.signal, "cancelled": result.cancelled,
              "truncated": result.truncated, "duration_ms": result.duration_ms,
              "stdout_tail": result.stdout[-limit:] if limit else "",
              "stderr_tail": result.stderr[-limit:] if limit else ""}
    if result.error:
        record["error"] = result.error
    return record


def parse_reward(data: Any) -> Tuple[Dict[str, float], Optional[str]]:
    """A reward file: a JSON object of numbers, or one number (``{"reward": n}``); else a problem."""
    text = data.decode("utf-8", errors="replace") if isinstance(data, bytes) else str(data)
    try:
        value = json.loads(text.strip())
    except ValueError:
        value = None
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return {"reward": float(value)}, None
    if isinstance(value, dict) and value and all(
            isinstance(v, (int, float)) and not isinstance(v, bool) for v in value.values()):
        return {str(k): float(v) for k, v in value.items()}, None
    return {}, "the reward file holds neither a number nor a JSON object of numbers"


__all__ = ["EVAL_DIR", "SandboxEval", "ROW_FILE", "REFUSED_ENV", "describe", "parse_reward"]
