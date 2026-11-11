"""The options a Future AGI sandbox is created with, and the state a session resumes from.

Both are the Agents SDK's own pydantic types, registered under the type ``"futureagi"`` so that a
serialized run state finds them again.
"""

from __future__ import annotations

from typing import Literal, Optional

from fi.errors import MissingExtraError

try:
    from agents.sandbox.session.sandbox_client import BaseSandboxClientOptions
    from agents.sandbox.session.sandbox_session_state import SandboxSessionState
except ImportError as exc:
    raise MissingExtraError(
        cause=exc, extra="sandbox-openai-agents", module="agents.sandbox"
    ) from exc

#: The sandbox's writable folder, and the only folder the sandbox files API reaches.
WORKSPACE_ROOT = "/workspace"


class FutureAGISandboxClientOptions(BaseSandboxClientOptions):
    """How :class:`FutureAGISandboxClient` creates a sandbox. Every field is optional.

    ``name``, ``template``, ``size``, ``image`` and ``idle_ttl_seconds`` go to the sandbox create
    call as given (None leaves the deployment's default). ``workdir`` is the workspace root when no
    manifest is passed; it must be ``/workspace`` or a folder inside it. ``exec_timeout_s`` is the
    time limit of a command run without one; None, or more than the workspace's exec maximum,
    means that maximum. ``hibernate_on_exit`` hibernates the sandbox at the end of a run instead
    of deleting it: its files are kept, its processes are not."""

    type: Literal["futureagi"] = "futureagi"
    name: Optional[str] = None
    template: Optional[str] = None
    size: Optional[str] = None
    image: Optional[str] = None
    idle_ttl_seconds: Optional[int] = None
    workdir: str = WORKSPACE_ROOT
    exec_timeout_s: Optional[int] = None
    hibernate_on_exit: bool = False


class FutureAGISandboxSessionState(SandboxSessionState):
    """What a session needs to reattach to its sandbox, or to create a replacement like it. The
    workspace root is ``manifest.root``."""

    type: Literal["futureagi"] = "futureagi"
    sandbox_id: str
    name: Optional[str] = None
    template: Optional[str] = None
    size: Optional[str] = None
    image: Optional[str] = None
    idle_ttl_seconds: Optional[int] = None
    exec_timeout_s: Optional[int] = None
    hibernate_on_exit: bool = False


__all__ = ["FutureAGISandboxClientOptions", "FutureAGISandboxSessionState", "WORKSPACE_ROOT"]
