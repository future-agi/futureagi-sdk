"""The blocking WebSocket connect class that refuses a redirect on the channel's upgrade."""

from __future__ import annotations

from typing import Any

from websockets.sync import client as sync_client


def no_redirect_class(module: Any) -> Any:
    """The blocking connect class that answers a 3xx to the upgrade as a refusal, or ``None`` when the websockets
    version has no redirecting class (websockets 16.x, and 17.0, do not follow a redirect; the plain ``connect``
    is used).

    From websockets 17.1 the blocking connect follows a redirect through ``reconnect``, a class it does not
    document, and its ``process_redirect`` hook; the sandbox channel does not follow a redirect, so it overrides the
    hook. ``process_redirect`` exists from 17.1 (17.1 and 17.4 were checked; 16.1.1 has neither
    ``reconnect`` nor the hook). A version that has the class but not the hook is refused with this ImportError
    instead of being used: the override would not run and the redirect would be followed. The error is raised
    when this module, and so the sync channel module, is imported; ``fi.sandbox`` loads the sync channel module on
    first use, so a user of the async client alone does not meet it. pyproject pins websockets below 18 for the
    same reason."""
    redirecting = getattr(module, "reconnect", None)
    if redirecting is None:
        return None
    if not callable(getattr(redirecting, "process_redirect", None)):
        raise ImportError(
            "this websockets version's blocking connect (websockets.sync.client.reconnect) has no process_redirect "
            "hook, so the sandbox channel cannot refuse a redirect on it; install websockets 16.x or 17.1 and later below 18"
        )

    class NoRedirectConnect(redirecting):  # type: ignore[misc, valid-type]
        """The sync connect of websockets 17.1 and later, which follows a 3xx to the upgrade by
        default: here a 3xx is answered as the refusal it is."""

        def process_redirect(self, exc: Exception) -> Exception:
            return exc

    return NoRedirectConnect


NoRedirectConnect = no_redirect_class(sync_client)
