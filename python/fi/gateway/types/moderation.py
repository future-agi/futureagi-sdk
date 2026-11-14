"""Moderation response types."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class CategoryScores(BaseModel):
    model_config = ConfigDict(extra="allow")


class ModerationResult(BaseModel):
    flagged: bool
    categories: dict[str, bool] = {}
    category_scores: dict[str, float] = {}
    model_config = ConfigDict(extra="allow")


class ModerationResponse(BaseModel):
    id: str
    model: str
    results: list[ModerationResult]
    model_config = ConfigDict(extra="allow")
