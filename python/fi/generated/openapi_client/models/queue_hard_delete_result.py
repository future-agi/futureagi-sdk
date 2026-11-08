from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="QueueHardDeleteResult")


@_attrs_define
class QueueHardDeleteResult:
    """
    Attributes:
        deleted (bool):
        queue_id (UUID):
        hard_deleted (bool | Unset):
        archived (bool | Unset):
    """

    deleted: bool
    queue_id: UUID
    hard_deleted: bool | Unset = UNSET
    archived: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        deleted = self.deleted

        queue_id = str(self.queue_id)

        hard_deleted = self.hard_deleted

        archived = self.archived

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "deleted": deleted,
                "queue_id": queue_id,
            }
        )
        if hard_deleted is not UNSET:
            field_dict["hard_deleted"] = hard_deleted
        if archived is not UNSET:
            field_dict["archived"] = archived

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        deleted = d.pop("deleted")

        queue_id = UUID(d.pop("queue_id"))

        hard_deleted = d.pop("hard_deleted", UNSET)

        archived = d.pop("archived", UNSET)

        queue_hard_delete_result = cls(
            deleted=deleted,
            queue_id=queue_id,
            hard_deleted=hard_deleted,
            archived=archived,
        )

        queue_hard_delete_result.additional_properties = d
        return queue_hard_delete_result

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
