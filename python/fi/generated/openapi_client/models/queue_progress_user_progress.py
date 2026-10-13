from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="QueueProgressUserProgress")


@_attrs_define
class QueueProgressUserProgress:
    """
    Attributes:
        total (int):
        completed (int):
        pending (int):
        in_progress (int):
        in_review (int):
        skipped (int):
        progress_pct (float):
    """

    total: int
    completed: int
    pending: int
    in_progress: int
    in_review: int
    skipped: int
    progress_pct: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total = self.total

        completed = self.completed

        pending = self.pending

        in_progress = self.in_progress

        in_review = self.in_review

        skipped = self.skipped

        progress_pct = self.progress_pct

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total": total,
                "completed": completed,
                "pending": pending,
                "in_progress": in_progress,
                "in_review": in_review,
                "skipped": skipped,
                "progress_pct": progress_pct,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        total = d.pop("total")

        completed = d.pop("completed")

        pending = d.pop("pending")

        in_progress = d.pop("in_progress")

        in_review = d.pop("in_review")

        skipped = d.pop("skipped")

        progress_pct = d.pop("progress_pct")

        queue_progress_user_progress = cls(
            total=total,
            completed=completed,
            pending=pending,
            in_progress=in_progress,
            in_review=in_review,
            skipped=skipped,
            progress_pct=progress_pct,
        )

        queue_progress_user_progress.additional_properties = d
        return queue_progress_user_progress

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
