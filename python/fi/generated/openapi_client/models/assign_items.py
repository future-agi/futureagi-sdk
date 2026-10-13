from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.assign_items_action import AssignItemsAction
from ..types import UNSET, Unset

T = TypeVar("T", bound="AssignItems")


@_attrs_define
class AssignItems:
    """
    Attributes:
        item_ids (list[UUID]):
        user_ids (list[UUID] | Unset):
        action (AssignItemsAction | Unset):  Default: AssignItemsAction.ADD.
    """

    item_ids: list[UUID]
    user_ids: list[UUID] | Unset = UNSET
    action: AssignItemsAction | Unset = AssignItemsAction.ADD
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        item_ids = []
        for item_ids_item_data in self.item_ids:
            item_ids_item = str(item_ids_item_data)
            item_ids.append(item_ids_item)

        user_ids: list[str] | Unset = UNSET
        if not isinstance(self.user_ids, Unset):
            user_ids = []
            for user_ids_item_data in self.user_ids:
                user_ids_item = str(user_ids_item_data)
                user_ids.append(user_ids_item)

        action: str | Unset = UNSET
        if not isinstance(self.action, Unset):
            action = self.action.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "item_ids": item_ids,
            }
        )
        if user_ids is not UNSET:
            field_dict["user_ids"] = user_ids
        if action is not UNSET:
            field_dict["action"] = action

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        item_ids = []
        _item_ids = d.pop("item_ids")
        for item_ids_item_data in _item_ids:
            item_ids_item = UUID(item_ids_item_data)

            item_ids.append(item_ids_item)

        _user_ids = d.pop("user_ids", UNSET)
        user_ids: list[UUID] | Unset = UNSET
        if _user_ids is not UNSET:
            user_ids = []
            for user_ids_item_data in _user_ids:
                user_ids_item = UUID(user_ids_item_data)

                user_ids.append(user_ids_item)

        _action = d.pop("action", UNSET)
        action: AssignItemsAction | Unset
        if isinstance(_action, Unset):
            action = UNSET
        else:
            action = AssignItemsAction(_action)

        assign_items = cls(
            item_ids=item_ids,
            user_ids=user_ids,
            action=action,
        )

        assign_items.additional_properties = d
        return assign_items

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
