"""Request/response recorder for integration testing."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from fi.gateway.callbacks.base import CallbackHandler, CallbackRequest, CallbackResponse, redact_credentials


def _response_record(response: Any) -> dict[str, Any]:
    """Record release wrappers, parsed current values or raw bytes without gateway metadata."""
    if isinstance(response, CallbackResponse):
        parsed = response._parsed
        if isinstance(parsed, (bytes, bytearray)):
            body = {"bytes": len(parsed)}
        elif hasattr(parsed, "model_dump"):
            body = parsed.model_dump(mode="json", exclude={"agentcc"})
        else:
            body = response.body
        return {"status_code": response.status_code, "body": body}
    meta = getattr(response, "agentcc", None)
    http = getattr(meta, "http_response", None)
    status = getattr(http, "status_code", None)
    if hasattr(response, "model_dump"):
        body = response.model_dump(mode="json", exclude={"agentcc"})
    elif isinstance(response, (bytes, bytearray)):
        body = {"bytes": len(response)}
    else:
        body = response
    return {"status_code": status if isinstance(status, int) else None, "body": body}


@dataclass
class Interaction:
    """A recorded request/response pair."""
    request: dict[str, Any]
    response: dict[str, Any]


class RequestRecorder(CallbackHandler):
    """Records all API calls to a JSON file for replay in tests.

    Usage::

        from fi.gateway.testing import RequestRecorder

        with RequestRecorder("recordings.json") as recorder:
            client = AgentCC(api_key="sk-...", base_url="...", callbacks=[recorder])
            client.chat.completions.create(...)
        # recordings.json now contains all request/response pairs
    """

    def __init__(self, file_path: str, *, format: str = "published") -> None:
        """Use ``format='compact'`` for JSON snapshots and raw-byte summaries."""
        if format not in {"published", "compact"}:
            raise ValueError("format must be 'published' or 'compact'")
        self._format = format
        self._file_path = file_path
        self._recordings: list[dict[str, Any]] = []

    def on_request_end(self, request: CallbackRequest, response: Any) -> None:
        self._recordings.append(
            {
                "request": {
                    "method": request.method,
                    "url": request.url,
                    "body": redact_credentials(request.body),
                },
                "response": (_response_record(response) if self._format == "compact" else {
                    "status_code": getattr(response, "status_code", None),
                    "body": getattr(response, "body", None),
                }),
            }
        )

    @property
    def recordings(self) -> list[dict[str, Any]]:
        """Return a copy of all recorded interactions."""
        return list(self._recordings)

    def save(self) -> None:
        """Write recordings to file."""
        with open(self._file_path, "w") as f:
            json.dump(self._recordings, f, indent=2, default=str)

    def __enter__(self) -> RequestRecorder:
        return self

    def __exit__(self, *args: Any) -> None:
        self.save()


class RecordingAgentCC:
    """Wraps a AgentCC client and records all chat completion interactions.

    Usage::

        from fi.gateway import AgentCC
        from fi.gateway.testing import RecordingAgentCC

        client = AgentCC(api_key="sk-...", base_url="...")
        recorder = RecordingAgentCC(client)
        result = recorder.chat.completions.create(model="gpt-4o", messages=[...])
        recorder.save("interactions.json")
    """

    def __init__(self, client: Any) -> None:
        self._client = client
        self._interactions: list[Interaction] = []
        self._chat = _RecordingChat(self)

    @property
    def chat(self) -> _RecordingChat:
        return self._chat

    @property
    def interactions(self) -> list[Interaction]:
        return list(self._interactions)

    def save(self, path: str | Path) -> None:
        """Save all recorded interactions to a JSON file."""
        data = [asdict(i) for i in self._interactions]
        Path(path).write_text(json.dumps(data, indent=2, default=str))

    @classmethod
    def load(cls, path: str | Path) -> list[Interaction]:
        """Load interactions from a JSON file."""
        data = json.loads(Path(path).read_text())
        return [Interaction(request=d["request"], response=d["response"]) for d in data]

    def close(self) -> None:
        self._client.close()


class _RecordingChatCompletions:
    def __init__(self, recorder: RecordingAgentCC) -> None:
        self._recorder = recorder

    def create(self, **kwargs: Any) -> Any:
        result = self._recorder._client.chat.completions.create(**kwargs)
        req_data = {k: v for k, v in kwargs.items() if k != "extra_headers"}
        resp_data = result.model_dump() if hasattr(result, "model_dump") else {}
        self._recorder._interactions.append(
            Interaction(request=req_data, response=resp_data)
        )
        return result


class _RecordingChat:
    def __init__(self, recorder: RecordingAgentCC) -> None:
        self._completions = _RecordingChatCompletions(recorder)

    @property
    def completions(self) -> _RecordingChatCompletions:
        return self._completions
