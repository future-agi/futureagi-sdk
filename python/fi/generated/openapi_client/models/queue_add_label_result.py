from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.queue_label_result import QueueLabelResult


T = TypeVar("T", bound="QueueAddLabelResult")


@_attrs_define
class QueueAddLabelResult:
    """
    Attributes:
        label (QueueLabelResult):
        created (bool):
        reopened_items (int):
        queue_status (str):
    """

    label: QueueLabelResult
    created: bool
    reopened_items: int
    queue_status: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        label = self.label.to_dict()

        created = self.created

        reopened_items = self.reopened_items

        queue_status = self.queue_status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "label": label,
                "created": created,
                "reopened_items": reopened_items,
                "queue_status": queue_status,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_label_result import QueueLabelResult

        d = dict(src_dict)
        label = QueueLabelResult.from_dict(d.pop("label"))

        created = d.pop("created")

        reopened_items = d.pop("reopened_items")

        queue_status = d.pop("queue_status")

        queue_add_label_result = cls(
            label=label,
            created=created,
            reopened_items=reopened_items,
            queue_status=queue_status,
        )

        queue_add_label_result.additional_properties = d
        return queue_add_label_result

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
