"""Shared transport test fixtures (no test collection)."""
from __future__ import annotations
from typing import Any
from pydantic import BaseModel, ConfigDict
from fi.gateway._base_client import SyncBaseClient


class _MockResponse(BaseModel):
    """Simple Pydantic model for testing _process_response_body."""

    model_config = ConfigDict(extra="allow")
    id: str
    content: str


def _make_sync_client(**kwargs: Any) -> SyncBaseClient:
    # The transport has no default base URL (no hosted fallback).
    defaults: dict[str, Any] = {
        "api_key": "sk-test-key-12345",
        "base_url": "http://gateway.test",
    }
    defaults.update(kwargs)
    return SyncBaseClient(**defaults)
