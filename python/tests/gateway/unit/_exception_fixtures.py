"""Shared HTTP error response fixture."""
from typing import Any
from unittest.mock import MagicMock


def _make_mock_response(
    status_code: int,
    body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> MagicMock:
    """Create a mock httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.headers = headers or {}
    if body is not None:
        resp.json.return_value = body
    else:
        resp.json.side_effect = Exception("No JSON body")
    return resp
