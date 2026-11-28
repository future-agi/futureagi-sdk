"""The channel's two operations on ``client.sandboxes.commands`` (async): mint a data token, and
open an exec stream with one. ``AsyncSandboxCommands`` gets them from ``AsyncChannelCommands``,
which calls these with itself as ``part``."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Any, Optional

from .._wire import NO_RETRY
from ..channel_errors import reworded
from ..errors import ConflictError, NotFoundError
from . import connect
from .constants import KILL_SWITCH_ENV, TOKEN_SUFFIX

if TYPE_CHECKING:
    from ._async.stream import AsyncExecStream


async def channel_token(part: Any, sandbox_id: str) -> dict:
    """``POST .../channel/token`` through ``part`` (a ``commands`` part: its ``_call``, origin
    rule and error mapping). The operation is not in the generated table, so it is derived from
    the table's ``sandboxes.hibernate`` row (a POST on the sandbox with a JSON body). A 404 is
    explained (the operator may have switched the channel off), and so is a 409 for a sandbox on
    a sandbox host."""
    name = connect.MINT_OPERATION
    base = part._core.operation("sandboxes.hibernate")
    operation = replace(
        base,
        name=name,
        path=base.path.rsplit("/", 1)[0]
        + TOKEN_SUFFIX,  # .../sandboxes/{id} + /channel/token
        content_type="application/json",
        operation_id="mintWorkspaceSandboxChannelToken",
    )
    try:
        return await part._call(
            name,
            path={"id": sandbox_id},
            body={},
            retries=NO_RETRY,
            _operation=operation,
        )
    except NotFoundError as error:
        raise reworded(
            error,
            f"{name} failed with status 404 ({error.code}): the channel is switched off by the "
            f"operator ({KILL_SWITCH_ENV}=0), or there is no sandbox {sandbox_id} in this workspace",
        ) from None
    except ConflictError as error:
        reason = error.detail.get("reason") if isinstance(error.detail, dict) else None
        if reason != "channel_remote_unsupported":
            raise
        raise reworded(
            error,
            f"{name} failed with status 409 ({reason}): this sandbox runs on a sandbox host, which "
            "the channel does not reach yet; run commands with commands.run (the sandbox exec "
            "command) instead",
        ) from None


async def exec_stream(
    part: Any,
    sandbox_id: str,
    argv: Any,
    *,
    stdin: Any = None,
    cwd: Optional[str] = None,
    env: Optional[dict] = None,
    timeout_seconds: Optional[int] = None,
) -> AsyncExecStream:
    """Check the arguments, mint a token for this one connection, and open the stream: the socket
    goes to the reply's URL, offering exactly the reply's subprotocols, with ``Origin`` set to the
    API base URL's origin and no cookie."""
    argv = connect.check_argv(argv)
    connect.check_options(cwd, env, timeout_seconds)
    shared = part._core.shared
    # The mint reply holds the token: it is not bound to a name here, so no frame of a later
    # error's traceback has it in its locals.
    plan = connect.plan(await channel_token(part, sandbox_id), shared.origin().url)
    # Imported here: the stream module of the sync twin checks the installed websockets when it is
    # imported, and a user of the other client must not meet that check.
    from ._async.stream import AsyncExecStream

    return await AsyncExecStream.open(
        plan,
        argv,
        cwd=cwd,
        env=dict(env) if env is not None else None,
        timeout_seconds=timeout_seconds,
        stdin=stdin,
        scrub=connect.scrubber(shared, plan.token),
    )


class AsyncChannelCommands:
    """The channel's methods on ``client.sandboxes.commands`` (async), mixed into
    ``AsyncSandboxCommands``: it supplies ``_call`` and ``_core``."""

    async def channel_token(self, sandbox_id: str) -> dict[str, Any]:
        """Mint a channel data token (60 seconds, single use); ``exec_stream`` mints its own."""
        return await channel_token(self, sandbox_id)

    async def exec_stream(
        self,
        sandbox_id: str,
        argv: list[str],
        *,
        stdin: Any = None,
        cwd: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
        timeout_seconds: Optional[int] = None,
    ) -> AsyncExecStream:
        """Run ``argv`` (a list, run with no shell) on the sandbox's channel: an
        ``AsyncExecStream`` with binary-safe stdin, stdout, stderr and an exit record. Not retried."""
        return await exec_stream(
            self,
            sandbox_id,
            argv,
            stdin=stdin,
            cwd=cwd,
            env=env,
            timeout_seconds=timeout_seconds,
        )
