from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.add_queue_item import AddQueueItem
    from ..models.selection import Selection


T = TypeVar("T", bound="AddItems")


@_attrs_define
class AddItems:
    """
    Attributes:
        items (list[AddQueueItem] | Unset):
        selection (Selection | Unset):
    """

    items: list[AddQueueItem] | Unset = UNSET
    selection: Selection | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        items: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.items, Unset):
            items = []
            for items_item_data in self.items:
                items_item = items_item_data.to_dict()
                items.append(items_item)

        selection: dict[str, Any] | Unset = UNSET
        if not isinstance(self.selection, Unset):
            selection = self.selection.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if items is not UNSET:
            field_dict["items"] = items
        if selection is not UNSET:
            field_dict["selection"] = selection

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.add_queue_item import AddQueueItem
        from ..models.selection import Selection

        d = dict(src_dict)
        _items = d.pop("items", UNSET)
        items: list[AddQueueItem] | Unset = UNSET
        if _items is not UNSET:
            items = []
            for items_item_data in _items:
                items_item = AddQueueItem.from_dict(items_item_data)

                items.append(items_item)

        _selection = d.pop("selection", UNSET)
        selection: Selection | Unset
        if isinstance(_selection, Unset):
            selection = UNSET
        else:
            selection = Selection.from_dict(_selection)

        add_items = cls(
            items=items,
            selection=selection,
        )

        add_items.additional_properties = d
        return add_items

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
