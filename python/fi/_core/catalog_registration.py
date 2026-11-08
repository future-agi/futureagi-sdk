"""Bind admitted FA resources to the single root client's existing transport."""
from __future__ import annotations

from typing import Any

from fi.generated.platform.catalog.models import AsyncModels, Models
from fi.generated.platform.catalog.optimizations import AsyncOptimizations, Optimizations
from fi.generated.platform.catalog.workspaces import AsyncWorkspaces, Workspaces


def register(client: Any, *, asynchronous: bool = False) -> None:
    if asynchronous:
        client.workspaces = AsyncWorkspaces(client)
        client.optimizations = AsyncOptimizations(client)
        client.models = AsyncModels(client)
    else:
        client.workspaces = Workspaces(client)
        client.optimizations = Optimizations(client)
        client.models = Models(client)
