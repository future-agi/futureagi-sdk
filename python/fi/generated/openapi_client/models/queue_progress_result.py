from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.queue_progress_annotator_stat import QueueProgressAnnotatorStat
    from ..models.queue_progress_user_progress import QueueProgressUserProgress


T = TypeVar("T", bound="QueueProgressResult")


@_attrs_define
class QueueProgressResult:
    """
    Attributes:
        total (int):
        pending (int):
        in_progress (int):
        in_review (int):
        completed (int):
        skipped (int):
        progress_pct (float):
        annotator_stats (list[QueueProgressAnnotatorStat]):
        user_progress (QueueProgressUserProgress):
    """

    total: int
    pending: int
    in_progress: int
    in_review: int
    completed: int
    skipped: int
    progress_pct: float
    annotator_stats: list[QueueProgressAnnotatorStat]
    user_progress: QueueProgressUserProgress
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total = self.total

        pending = self.pending

        in_progress = self.in_progress

        in_review = self.in_review

        completed = self.completed

        skipped = self.skipped

        progress_pct = self.progress_pct

        annotator_stats = []
        for annotator_stats_item_data in self.annotator_stats:
            annotator_stats_item = annotator_stats_item_data.to_dict()
            annotator_stats.append(annotator_stats_item)

        user_progress = self.user_progress.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "total": total,
                "pending": pending,
                "in_progress": in_progress,
                "in_review": in_review,
                "completed": completed,
                "skipped": skipped,
                "progress_pct": progress_pct,
                "annotator_stats": annotator_stats,
                "user_progress": user_progress,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_progress_annotator_stat import QueueProgressAnnotatorStat
        from ..models.queue_progress_user_progress import QueueProgressUserProgress

        d = dict(src_dict)
        total = d.pop("total")

        pending = d.pop("pending")

        in_progress = d.pop("in_progress")

        in_review = d.pop("in_review")

        completed = d.pop("completed")

        skipped = d.pop("skipped")

        progress_pct = d.pop("progress_pct")

        annotator_stats = []
        _annotator_stats = d.pop("annotator_stats")
        for annotator_stats_item_data in _annotator_stats:
            annotator_stats_item = QueueProgressAnnotatorStat.from_dict(
                annotator_stats_item_data
            )

            annotator_stats.append(annotator_stats_item)

        user_progress = QueueProgressUserProgress.from_dict(d.pop("user_progress"))

        queue_progress_result = cls(
            total=total,
            pending=pending,
            in_progress=in_progress,
            in_review=in_review,
            completed=completed,
            skipped=skipped,
            progress_pct=progress_pct,
            annotator_stats=annotator_stats,
            user_progress=user_progress,
        )

        queue_progress_result.additional_properties = d
        return queue_progress_result

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
