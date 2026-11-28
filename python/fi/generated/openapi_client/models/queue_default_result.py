from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.queue_default_result_action import QueueDefaultResultAction

if TYPE_CHECKING:
    from ..models.queue_default_queue import QueueDefaultQueue
    from ..models.queue_label_result import QueueLabelResult


T = TypeVar("T", bound="QueueDefaultResult")


@_attrs_define
class QueueDefaultResult:
    """
    Attributes:
        queue (QueueDefaultQueue):
        labels (list[QueueLabelResult]):
        created (bool):
        action (QueueDefaultResultAction):
    """

    queue: QueueDefaultQueue
    labels: list[QueueLabelResult]
    created: bool
    action: QueueDefaultResultAction
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        queue = self.queue.to_dict()

        labels = []
        for labels_item_data in self.labels:
            labels_item = labels_item_data.to_dict()
            labels.append(labels_item)

        created = self.created

        action = self.action.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "queue": queue,
                "labels": labels,
                "created": created,
                "action": action,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.queue_default_queue import QueueDefaultQueue
        from ..models.queue_label_result import QueueLabelResult

        d = dict(src_dict)
        queue = QueueDefaultQueue.from_dict(d.pop("queue"))

        labels = []
        _labels = d.pop("labels")
        for labels_item_data in _labels:
            labels_item = QueueLabelResult.from_dict(labels_item_data)

            labels.append(labels_item)

        created = d.pop("created")

        action = QueueDefaultResultAction(d.pop("action"))

        queue_default_result = cls(
            queue=queue,
            labels=labels,
            created=created,
            action=action,
        )

        queue_default_result.additional_properties = d
        return queue_default_result

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
