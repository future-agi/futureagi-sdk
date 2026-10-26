"""Files API types — file management for batches and other features."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict


class FileObject(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    object: str = "file"
    bytes: int | None = None
    created_at: int | None = None
    filename: str | None = None
    purpose: str | None = None
    status: str | None = None
    status_details: str | Any | None = None


class FileList(BaseModel):
    model_config = ConfigDict(extra="allow")

    data: list[FileObject] = []
    object: str = "list"


class FileDeleted(BaseModel):
    model_config = ConfigDict(extra="allow")

    id: str
    object: str = "file"
    deleted: bool = False
