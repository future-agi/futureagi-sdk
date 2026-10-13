from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="QueueProgressAnnotatorStat")


@_attrs_define
class QueueProgressAnnotatorStat:
    """
    Attributes:
        user_id (UUID):
        completed (int):
        pending (int):
        in_progress (int):
        in_review (int):
        annotations_count (int):
        name (None | str | Unset):
    """

    user_id: UUID
    completed: int
    pending: int
    in_progress: int
    in_review: int
    annotations_count: int
    name: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = str(self.user_id)

        completed = self.completed

        pending = self.pending

        in_progress = self.in_progress

        in_review = self.in_review

        annotations_count = self.annotations_count

        name: None | str | Unset
        if isinstance(self.name, Unset):
            name = UNSET
        else:
            name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "user_id": user_id,
                "completed": completed,
                "pending": pending,
                "in_progress": in_progress,
                "in_review": in_review,
                "annotations_count": annotations_count,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_id = UUID(d.pop("user_id"))

        completed = d.pop("completed")

        pending = d.pop("pending")

        in_progress = d.pop("in_progress")

        in_review = d.pop("in_review")

        annotations_count = d.pop("annotations_count")

        def _parse_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        name = _parse_name(d.pop("name", UNSET))

        queue_progress_annotator_stat = cls(
            user_id=user_id,
            completed=completed,
            pending=pending,
            in_progress=in_progress,
            in_review=in_review,
            annotations_count=annotations_count,
            name=name,
        )

        queue_progress_annotator_stat.additional_properties = d
        return queue_progress_annotator_stat

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
