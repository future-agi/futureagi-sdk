"""Account for completed, non-streaming requests carrying an active session id."""
from __future__ import annotations

from typing import Any


class SessionTracker:
    def __init__(self, client: Any) -> None:
        self.client = client

    def on_request_end(self, request: Any, response: Any) -> None:
        session = self.client._active_session
        if session is None:
            return
        headers = {key.lower(): value for key, value in request.headers.items()}
        if headers.get("x-agentcc-session-id") != session.session_id:
            return
        usage = getattr(response, "usage", None)
        metadata = getattr(response, "agentcc", None)
        session.track_request(
            cost=getattr(metadata, "cost", 0.0) or 0.0,
            tokens=getattr(usage, "total_tokens", 0) or 0,
        )
