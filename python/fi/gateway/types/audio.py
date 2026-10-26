"""Audio response types."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Transcription(BaseModel):
    text: str
    model_config = ConfigDict(extra="allow")


class Translation(BaseModel):
    text: str
    model_config = ConfigDict(extra="allow")
